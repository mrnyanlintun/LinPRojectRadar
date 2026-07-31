#!/usr/bin/env python3
"""
A2 verification without Google credentials.

Drives the real import and reconciliation code against a stub that mimics the Drive v3 responses
this adapter uses, so the logic that will run against production is the logic under test here.
What this cannot prove is the live API contract itself: field names, paging behaviour and
permissions are only confirmed by a real run with the service account.

Proven here:
  - dry run writes nothing
  - --apply imports projects, history and file metadata
  - a second run is idempotent: same rows, no duplicates
  - reconciliation reports zero discrepancies on a clean import
  - an unparseable project.json is named and explained, never silently dropped
  - a history file with no recognisable period is explained, not stored under a made-up period
  - an orphaned drive_file_id is detected
  - a project in Postgres but not in Drive is detected
  - the adapter has no Drive write path

Run:
    DATABASE_URL=... python tools/test_drive_import.py
"""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from sqlalchemy import func, select  # noqa: E402

import app.drive_adapter as adapter  # noqa: E402
from app.db import build_engine, build_session_factory  # noqa: E402
from app.models import File, Project, ProjectSnapshot  # noqa: E402
from app.settings import load_settings  # noqa: E402

import tools.import_from_drive as importer  # noqa: E402

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((ok, label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))


# ---------------------------------------------------------------- stub Drive

FOLDER = adapter.FOLDER_MIME
PARENT = "PARENT-ID"

TREE = {
    PARENT: [
        {"id": "F-01", "name": "01", "mimeType": FOLDER},
        {"id": "F-02", "name": "02", "mimeType": FOLDER},
        {"id": "F-BAD", "name": "03", "mimeType": FOLDER},
        {"id": "F-ARCH", "name": "00_Archive", "mimeType": FOLDER},
        {"id": "F-LIB", "name": "_lib", "mimeType": FOLDER},
    ],
    "F-ARCH": [{"id": "F-09", "name": "09", "mimeType": FOLDER}],
    "F-01": [
        {"id": "J-01", "name": "project.json", "mimeType": "application/json"},
        {"id": "H-01", "name": "_history", "mimeType": FOLDER},
        {"id": "C-01", "name": "_corpus", "mimeType": FOLDER},
        {"id": "A-01", "name": "_audits", "mimeType": FOLDER},
    ],
    "H-01": [
        {"id": "h1", "name": "history_2026-06.json", "mimeType": "application/json"},
        {"id": "h2", "name": "history_2026-07.json", "mimeType": "application/json"},
        {"id": "h3", "name": "notes.json", "mimeType": "application/json"},  # no period
    ],
    "C-01": [
        {"id": "c1", "name": "01_OPR.pdf", "mimeType": "application/pdf", "size": "1200",
         "md5Checksum": "abc"},
        {"id": "c2", "name": "02_spec.pdf", "mimeType": "application/pdf", "size": "900"},
    ],
    "A-01": [{"id": "a1", "name": "audit_2026-06.csv", "mimeType": "text/csv"}],
    "F-02": [{"id": "J-02", "name": "project.json", "mimeType": "application/json"}],
    "F-BAD": [{"id": "J-BAD", "name": "project.json", "mimeType": "application/json"}],
    "F-09": [{"id": "J-09", "name": "project.json", "mimeType": "application/json"}],
}

DOCS = {
    "J-01": {"id": "01", "name": "Alpha", "sector": "construction", "signals": {}},
    "J-02": {"id": "02", "name": "Beta", "sector": "design", "signals": {}},
    "J-09": {"id": "09", "name": "Archived One", "sector": "design", "signals": {}},
    "h1": {"period": "2026-06", "cpi": 0.98},
    "h2": {"period": "2026-07", "cpi": 1.01},
    "h3": {"note": "no period in the filename"},
}


class StubFiles:
    def __init__(self, tree, docs):
        self.tree, self.docs = tree, docs
        self.write_calls = []

    def list(self, q=None, fields=None, pageSize=None, pageToken=None, **kw):
        folder = q.split("'")[1]
        only_folders = "mimeType = '%s'" % FOLDER in q
        items = [dict(i) for i in self.tree.get(folder, [])]
        if only_folders:
            items = [i for i in items if i["mimeType"] == FOLDER]
        # Force paging so the adapter's pagination is exercised, not assumed.
        page = int(pageToken or 0)
        chunk, nxt = items[page:page + 2], page + 2
        response = {"files": chunk}
        if nxt < len(items):
            response["nextPageToken"] = str(nxt)
        return _Exec(response)

    def get_media(self, fileId=None, **kw):
        if fileId == "J-BAD":
            return _Exec(b"{ this is not valid json ")
        return _Exec(json.dumps(self.docs[fileId]).encode("utf-8"))

    # Any write attempt must be loud, not silently absent.
    def create(self, *a, **k):
        self.write_calls.append("create"); raise AssertionError("write attempted")

    def update(self, *a, **k):
        self.write_calls.append("update"); raise AssertionError("write attempted")

    def delete(self, *a, **k):
        self.write_calls.append("delete"); raise AssertionError("write attempted")


class _Exec:
    def __init__(self, value):
        self.value = value

    def execute(self):
        return self.value


class StubService:
    def __init__(self):
        self._files = StubFiles(TREE, DOCS)

    def files(self):
        return self._files


service = StubService()

print("=" * 78)
print("ADAPTER: enumerate, page, and surface a parse failure")
print("=" * 78)

projects = adapter.enumerate_projects(service, PARENT)
by_id = {p.legacy_id: p for p in projects}
check(len(projects) == 4, "four project folders found (paging exercised)", str(len(projects)))
check("_lib" not in by_id, "underscore-prefixed folders are not treated as projects")
check(by_id["09"].archived is True, "archive folder marks its projects archived")
check(by_id["01"].archived is False, "non-archived project is not marked archived")
check(by_id["03"].doc is None and by_id["03"].parse_error,
      "unparseable project.json is surfaced, not dropped", str(by_id["03"].parse_error)[:70])
check(len(by_id["01"].history) == 3, "three history files enumerated")
check(len(by_id["01"].corpus) == 2, "two corpus files enumerated")
check(len(by_id["01"].audits) == 1, "one audit file enumerated")
check(adapter.period_from_filename("history_2026-07.json") == "2026-07", "period parsed from name")
check(adapter.period_from_filename("notes.json") is None, "no period invented for an odd filename")

src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "drive_adapter.py").read_text(
    encoding="utf-8")
for forbidden in ("files().create", "files().update", "files().delete", "drive.file",
                  "auth/drive'", "permissions()"):
    check(forbidden not in src, f"adapter has no {forbidden}")
check("drive.readonly" in src, "adapter requests the read-only scope only")

print()
print("=" * 78)
print("DRY RUN writes nothing")
print("=" * 78)

engine = build_engine(load_settings())
Session = build_session_factory(engine)
with Session() as s:
    report = importer.reconcile(s, projects)
    n = s.scalar(select(func.count()).select_from(Project)) or 0
check(n == 0, "no projects written by a reconcile-only pass", str(n))
check(report["counts"]["drive_project_folders"] == 4, "reconcile counted the Drive folders")
check(any(d["kind"] == "in_drive_not_in_postgres" for d in report["discrepancies"]),
      "a dry run correctly reports the projects as not yet imported")

print()
print("=" * 78)
print("APPLY: import and reconcile")
print("=" * 78)

with Session() as s:
    importer.upsert_projects(s, projects)
    importer.upsert_history(s, projects, service)
    importer.upsert_files(s, projects)
    s.commit()

with Session() as s:
    check((s.scalar(select(func.count()).select_from(Project)) or 0) == 3,
          "three parseable projects imported (the unparseable one skipped)")
    check((s.scalar(select(func.count()).select_from(ProjectSnapshot)) or 0) == 2,
          "two datable history snapshots imported")
    check((s.scalar(select(func.count()).select_from(File)) or 0) == 3,
          "three file metadata rows imported (2 corpus + 1 audit)")
    f = s.scalar(select(File).where(File.name == "01_OPR.pdf"))
    check(f.doc_type == "corpus", "corpus doc_type recorded")
    check(f.sha256 is None, "sha256 left null: no bytes downloaded in this phase")
    a = s.scalar(select(File).where(File.doc_type == "audit_result"))
    check(a is not None and a.name == "audit_2026-06.csv", "audit doc_type recorded")
    arch = s.scalar(select(Project).where(Project.legacy_id == "09"))
    check(bool(arch.archived) is True, "archived flag persisted")
    p1 = s.scalar(select(Project).where(Project.legacy_id == "01"))
    check(p1.doc == DOCS["J-01"], "project doc stored unchanged")

    report = importer.reconcile(s, projects)
check(report["clean"] is True, "reconciliation reports zero discrepancies",
      json.dumps(report["discrepancies"])[:200])
check(any(e["kind"] == "unparseable_project_json" for e in report["explained"]),
      "the unparseable project is EXPLAINED, not counted as clean silence")
check(any(e["kind"] == "history_file_without_period" for e in report["explained"]),
      "the undatable history file is explained")

print()
print("=" * 78)
print("IDEMPOTENCY: a second run changes nothing")
print("=" * 78)

with Session() as s:
    before = (s.scalar(select(func.count()).select_from(Project)),
              s.scalar(select(func.count()).select_from(ProjectSnapshot)),
              s.scalar(select(func.count()).select_from(File)))
    pid_before = s.scalar(select(Project.id).where(Project.legacy_id == "01"))

with Session() as s:
    importer.upsert_projects(s, projects)
    importer.upsert_history(s, projects, service)
    importer.upsert_files(s, projects)
    s.commit()

with Session() as s:
    after = (s.scalar(select(func.count()).select_from(Project)),
             s.scalar(select(func.count()).select_from(ProjectSnapshot)),
             s.scalar(select(func.count()).select_from(File)))
    pid_after = s.scalar(select(Project.id).where(Project.legacy_id == "01"))
check(before == after, "row counts unchanged after a second run", f"{before} -> {after}")
check(pid_before == pid_after, "existing primary key preserved, not deleted and recreated")

print()
print("=" * 78)
print("DISCREPANCY DETECTION")
print("=" * 78)

with Session() as s:
    p = s.scalar(select(Project).where(Project.legacy_id == "01"))
    s.add(File(project_id=p.id, drive_file_id="GHOST-ID", name="ghost.pdf", doc_type="corpus"))
    s.commit()
with Session() as s:
    report = importer.reconcile(s, projects)
check(any(d["kind"] == "orphaned_drive_file_id" for d in report["discrepancies"]),
      "an orphaned drive_file_id is detected")
check(report["clean"] is False, "the report is not clean while a discrepancy stands")

with Session() as s:
    s.delete(s.scalar(select(File).where(File.drive_file_id == "GHOST-ID")))
    s.add(Project(legacy_id="99", doc={"id": "99"}, archived=False))
    s.commit()
with Session() as s:
    report = importer.reconcile(s, projects)
check(any(d["kind"] == "in_postgres_not_in_drive" for d in report["discrepancies"]),
      "a project present only in Postgres is detected")

with Session() as s:
    s.delete(s.scalar(select(Project).where(Project.legacy_id == "99")))
    s.commit()
with Session() as s:
    final = importer.reconcile(s, projects)
check(final["clean"] is True, "clean again once the injected discrepancies are removed")

print()
print("--- sample report ---")
print("\n".join(importer.render_markdown(final, applied=True).splitlines()[:26]))

print()
print("=" * 78)
failed = [x for x in results if not x[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
