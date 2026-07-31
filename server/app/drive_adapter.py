"""
Google Drive read adapter.

One-way, read-only. This module has no write path at all: it does not import the Drive write
scopes and exposes no create, update or delete. The Apps Script backend remains the authoritative
writer until M7, and the failure this guards against is a split brain in which both stores accept
writes and neither is authoritative. A read-only adapter cannot cause that even if a caller asks
it to.

Credentials come from an environment variable holding the service account JSON, never from a file
in the repository. A committed key is a key that leaks, and the repository is public.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any, Iterator

CREDENTIAL_ENV = "GOOGLE_SERVICE_ACCOUNT_JSON"
PARENT_FOLDER_ENV = "DRIVE_PARENT_FOLDER_ID"
DEFAULT_PARENT_FOLDER_ID = "14u6LT8E1xKBLbHwq90SySmfou0oVlSqR"

# Read-only. Deliberately the narrowest scope that can list and read metadata; drive.readonly
# cannot be escalated by this process into a write.
SCOPES = ("https://www.googleapis.com/auth/drive.readonly",)

ARCHIVE_FOLDER_NAME = "00_Archive"
SUBFOLDERS = ("_history", "_corpus", "_audits", "_signals")

FOLDER_MIME = "application/vnd.google-apps.folder"


class DriveError(RuntimeError):
    """Raised for any condition that prevents a faithful read."""


@dataclass
class DriveFile:
    file_id: str
    name: str
    mime_type: str
    size: int | None = None
    modified_time: str | None = None
    md5_checksum: str | None = None
    parent_folder: str | None = None


@dataclass
class DriveProject:
    legacy_id: str
    folder_id: str
    archived: bool
    doc: dict[str, Any] | None = None
    parse_error: str | None = None
    history: list[DriveFile] = field(default_factory=list)
    corpus: list[DriveFile] = field(default_factory=list)
    audits: list[DriveFile] = field(default_factory=list)
    signals: list[DriveFile] = field(default_factory=list)

    @property
    def all_files(self) -> list[DriveFile]:
        return self.history + self.corpus + self.audits + self.signals


def load_credentials():
    """
    Build read-only credentials from the environment.

    Fails fast and by name. A missing credential that surfaces later as an empty project list
    would look exactly like an empty Drive folder, and the import would then report a successful
    reconciliation of nothing against nothing.
    """
    raw = (os.environ.get(CREDENTIAL_ENV) or "").strip()
    if not raw:
        raise DriveError(
            f"{CREDENTIAL_ENV} is not set. Provide the Google service account JSON in that "
            f"environment variable. It must never be committed to the repository."
        )

    # Accept either the JSON itself or a path to it, because a long JSON blob in a shell variable
    # is easy to truncate. A path is resolved here and its contents are still never committed.
    if raw.startswith("{"):
        try:
            info = json.loads(raw)
        except ValueError as exc:
            raise DriveError(f"{CREDENTIAL_ENV} is not valid JSON: {exc}") from exc
    else:
        if not os.path.exists(raw):
            raise DriveError(
                f"{CREDENTIAL_ENV} is neither JSON nor a path to an existing file: {raw[:60]!r}"
            )
        with open(raw, "r", encoding="utf-8") as handle:
            info = json.load(handle)

    for required in ("client_email", "private_key", "token_uri"):
        if required not in info:
            raise DriveError(
                f"{CREDENTIAL_ENV} does not look like a service account key: missing {required!r}"
            )

    try:
        from google.oauth2 import service_account  # noqa: PLC0415
    except ImportError as exc:
        raise DriveError(
            "google-auth is not installed. Install the pinned requirements: "
            "pip install -r requirements.txt"
        ) from exc

    return service_account.Credentials.from_service_account_info(info, scopes=list(SCOPES))


def build_service(credentials=None):
    try:
        from googleapiclient.discovery import build  # noqa: PLC0415
    except ImportError as exc:
        raise DriveError(
            "google-api-python-client is not installed. Install the pinned requirements."
        ) from exc
    creds = credentials or load_credentials()
    # cache_discovery=False: the file cache warns and is useless in a short-lived script.
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def parent_folder_id() -> str:
    return (os.environ.get(PARENT_FOLDER_ENV) or DEFAULT_PARENT_FOLDER_ID).strip()


def _list_children(service, folder_id: str, only_folders: bool = False) -> Iterator[dict]:
    """
    Page through the children of a folder.

    Paging is not optional: the API returns 100 items by default and silently omits the rest, so
    a single-page read would under-report a large corpus and the reconciliation would call the
    shortfall a discrepancy in Postgres.
    """
    query = f"'{folder_id}' in parents and trashed = false"
    if only_folders:
        query += f" and mimeType = '{FOLDER_MIME}'"

    page_token = None
    while True:
        response = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, md5Checksum)",
            pageSize=1000,
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()
        for item in response.get("files", []):
            yield item
        page_token = response.get("nextPageToken")
        if not page_token:
            return


def _to_file(item: dict, parent_label: str) -> DriveFile:
    size = item.get("size")
    return DriveFile(
        file_id=item["id"],
        name=item.get("name", ""),
        mime_type=item.get("mimeType", ""),
        size=int(size) if size is not None else None,
        modified_time=item.get("modifiedTime"),
        # Drive's own md5, when it has one. Recorded rather than recomputed: computing a sha256
        # would mean downloading bytes, and this phase reads metadata only.
        md5_checksum=item.get("md5Checksum"),
        parent_folder=parent_label,
    )


def read_json_file(service, file_id: str) -> tuple[dict | None, str | None]:
    """Download and parse one JSON file. Returns (doc, error)."""
    try:
        raw = service.files().get_media(fileId=file_id, supportsAllDrives=True).execute()
    except Exception as exc:  # noqa: BLE001 - a failed read must be named, never skipped
        return None, f"download failed: {type(exc).__name__}: {exc}"
    try:
        text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
        return json.loads(text), None
    except (ValueError, UnicodeDecodeError) as exc:
        return None, f"parse failed: {exc}"


def sha256_of(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def enumerate_projects(service, parent_id: str | None = None) -> list[DriveProject]:
    """
    Walk the parent folder and the archive, returning one DriveProject per project folder.

    A project folder whose project.json is missing or unparseable is still returned, carrying a
    parse_error. Dropping it would make the reconciliation report a clean run over a subset, which
    is the single most misleading outcome this import could produce.
    """
    parent_id = parent_id or parent_folder_id()
    projects: list[DriveProject] = []

    roots: list[tuple[str, bool]] = [(parent_id, False)]
    for item in _list_children(service, parent_id, only_folders=True):
        if item.get("name") == ARCHIVE_FOLDER_NAME:
            roots.append((item["id"], True))

    for root_id, archived in roots:
        for folder in _list_children(service, root_id, only_folders=True):
            name = folder.get("name", "")
            if name == ARCHIVE_FOLDER_NAME or name.startswith("_"):
                continue

            project = DriveProject(legacy_id=name, folder_id=folder["id"], archived=archived)

            subfolder_ids: dict[str, str] = {}
            for child in _list_children(service, folder["id"]):
                if child.get("mimeType") == FOLDER_MIME:
                    if child.get("name") in SUBFOLDERS:
                        subfolder_ids[child["name"]] = child["id"]
                elif child.get("name") == "project.json":
                    doc, problem = read_json_file(service, child["id"])
                    project.doc = doc
                    project.parse_error = problem

            if project.doc is None and project.parse_error is None:
                project.parse_error = "project.json not found in the project folder"

            for label, bucket in (("_history", project.history), ("_corpus", project.corpus),
                                  ("_audits", project.audits), ("_signals", project.signals)):
                folder_id = subfolder_ids.get(label)
                if not folder_id:
                    continue
                for child in _list_children(service, folder_id):
                    if child.get("mimeType") == FOLDER_MIME:
                        continue
                    bucket.append(_to_file(child, label))

            projects.append(project)

    projects.sort(key=lambda p: (p.archived, p.legacy_id))
    return projects


def period_from_filename(name: str) -> str | None:
    """
    Derive a history period from a filename such as history_2026-07.json or 2026-07.json.

    Returns None rather than guessing when no period is recognisable, so an unexpected filename
    surfaces in the reconciliation instead of being stored under a fabricated period.
    """
    import re

    stem = name.rsplit(".", 1)[0]
    match = re.search(r"(\d{4}-\d{2}(?:-\d{2})?)", stem)
    if match:
        return match.group(1)
    match = re.search(r"\bP(\d+)\b", stem, re.IGNORECASE)
    if match:
        return f"P{int(match.group(1))}"
    return None
