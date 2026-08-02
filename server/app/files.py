"""
The Files tab: the project's Arora directory, what is in each folder, and moving a misfile.

THREE ACTIONS, AND NO FOLDER STORAGE BEHIND THEM

  projectfiles       the tree, and one folder's contents
  projectfilemove    correct a placement the platform got wrong
  projectcorpus      the technical reviewer's reference material

The tree is not stored. `jdrive_tree.TEMPLATE` is the Arora template as code, and a project's
real tree is that template annotated with the distinct `document_uploads.folder_path` values
the project actually holds. See migration 0016 for why there is no `folders` table.

FILING IS VISIBLE AND CORRECTABLE, WHICH IS THE POINT OF `projectfilemove`

The platform chooses the destination and the PM never picks one, so the platform will sometimes
be wrong. A misfile nobody can see is worse than a question, so every file carries the folder it
landed in, the class it was filed as, and whether its placement was flagged for review; and the
PM can move it. Moving is audited and resolves the review flag, because a human has now looked.

THE REFERENCE CORPUS IS GATED ON THE SERVER, NOT BY HIDING A TAB

`projectcorpus` is registered in `features.GATED_ACTIONS` under the existing `auditor` flag,
so `gate_action` refuses it before dispatch for an account whose flag is off. That is the same
mechanism every other optional feature uses, and it is deliberately not a new scheme. It also
closes the shape a previous session found on `getportfoliohealth`, where an anonymous caller
reached a flagged action that a signed-in caller with the flag off was refused: the read guard
authenticates first, and the flag is checked on the authenticated caller.

FILING IS NOT CONDITIONAL ON THE FLAG. With the technical reviewer switched off, a
specification is still filed, still classed `reference`, and still kept out of the analytical
path. The flag governs only whether anything READS the corpus. Nothing about how a document is
stored changes when it is toggled.
"""

from __future__ import annotations

from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from .facade import err, now_iso
from .jdrive_tree import (
    CLASS_ANALYSED, CLASS_FILED, CLASS_REFERENCE, FILING_CLASS_LABELS, is_known_path,
    project_tree,
)
from .models import Project
from .research_identity import audit, resolve_caller
from .research_membership import ROLE_PM, require_member
from .research_models import Document, DocumentUpload

# --------------------------------------------------------------------------- preview
#
# PREVIEW IS BROWSER-FRIENDLY FORMATS ONLY, AND THE REST SAY SO RATHER THAN FAILING.
#
# The browser renders PDFs and images natively. Word, Excel and PowerPoint are listed as
# previewable because the document route serves them with their real content type and the
# platform offers them for download and for whatever handler the viewer's browser has; a CAD or
# Revit file gets neither, and NO RENDERER IS ATTEMPTED for it. `preview` on each row says
# which case a file is, so the tab shows the unsupported message instead of an empty frame that
# looks broken.
PREVIEW_NATIVE: frozenset[str] = frozenset({
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".txt",
})
PREVIEW_DOWNLOAD: frozenset[str] = frozenset({
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".csv",
})

#: Stated verbatim on screen for a format the platform will not try to render.
UNSUPPORTED_PREVIEW_MESSAGE = (
    "Format not supported for preview. Download the file to open it in the application that "
    "reads it."
)


def preview_kind(filename: str) -> str:
    """'native', 'download' or 'unsupported' for this filename."""
    name = str(filename or "").lower()
    dot = name.rfind(".")
    ext = name[dot:] if dot > 0 else ""
    if ext in PREVIEW_NATIVE:
        return "native"
    if ext in PREVIEW_DOWNLOAD:
        return "download"
    return "unsupported"


# --------------------------------------------------------------------------- versions


def _versions(rows: list[tuple[DocumentUpload, Document]]) -> dict[str, dict]:
    """
    The version number and supersession relationship for each upload in a project.

    SURFACED, NOT INVENTED. `supersedes_document_id` already records "this replaces that", and
    migration 0013 made it a chain of inserts precisely so a revision can itself be revised.
    Version number is that chain's depth, counted here rather than stored, because a stored
    counter would be a second source of truth that could disagree with the pointer.

    NOTHING IS REPLACED. A superseded document keeps its row, its bytes and its folder; it is
    marked `superseded` so the file list can show version 1 beside version 2 rather than in
    place of it.
    """
    supersedes: dict[str, str] = {}
    superseded_by: dict[str, str] = {}
    for upload, _doc in rows:
        if upload.supersedes_document_id:
            supersedes[upload.document_id] = upload.supersedes_document_id
            superseded_by[upload.supersedes_document_id] = upload.document_id

    out: dict[str, dict] = {}
    for upload, _doc in rows:
        depth, seen, cursor = 1, set(), upload.document_id
        while cursor in supersedes and cursor not in seen:
            seen.add(cursor)
            cursor = supersedes[cursor]
            depth += 1
        out[upload.document_id] = {
            "version": depth,
            "supersedes_document_id": upload.supersedes_document_id,
            "superseded_by_document_id": superseded_by.get(upload.document_id),
            "superseded": upload.document_id in superseded_by,
        }
    return out


def _file_row(upload: DocumentUpload, doc: Document, version: dict) -> dict:
    return {
        "document_id": upload.document_id,
        "filename": doc.filename,
        "doc_type": doc.doc_type,
        "mime_type": doc.mime_type,
        "size_bytes": doc.size_bytes,
        "period": upload.period,
        "folder_path": upload.folder_path,
        "filing_class": upload.filing_class,
        "filing_label": FILING_CLASS_LABELS.get(upload.filing_class or "", ""),
        "needs_filing_review": bool(upload.needs_filing_review),
        "classification_confidence": doc.classification_confidence,
        "uploaded_at": upload.uploaded_at.isoformat() if upload.uploaded_at else None,
        "preview": preview_kind(doc.filename),
        **version,
    }


def _project_uploads(session: Session, project: Project
                     ) -> list[tuple[DocumentUpload, Document]]:
    rows = session.execute(
        select(DocumentUpload, Document)
        .join(Document, Document.document_id == DocumentUpload.document_id)
        .where(DocumentUpload.project_id == project.id)
        .order_by(DocumentUpload.uploaded_at, DocumentUpload.upload_id)
    ).all()
    return [(u, d) for u, d in rows]


# --------------------------------------------------------------------------- actions


def a_projectfiles(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Any active member. The project's folder tree, and the contents of one folder.

    Reads only. The tree is computed from the template plus the folders this project actually
    holds documents in, so a project that has filed nothing gets the template with everything
    unoccupied rather than an error or an empty screen.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    project, member, problem = require_member(session, caller, payload, "projectfiles")
    if problem:
        return problem

    rows = _project_uploads(session, project)
    versions = _versions(rows)
    occupied = {u.folder_path for u, _d in rows if u.folder_path}

    wanted = str(payload.get("folder") or "").strip()
    files = [
        _file_row(u, d, versions[u.document_id])
        for u, d in rows
        if u.folder_path and (not wanted or u.folder_path == wanted)
    ]
    # The review queue is a filter over the same rows, never a separate store: a document
    # needing review is in its real folder, flagged, not in a holding pen of its own.
    review_count = sum(1 for u, _d in rows if u.needs_filing_review)

    audit(session, "project_read", participant_id=caller.participant_id,
          action="projectfiles", project_id=project.legacy_id,
          project_role=member.project_role)
    session.commit()
    return {
        "ok": True,
        "project_id": project.legacy_id,
        "tree": project_tree(occupied),
        "folder": wanted or None,
        "files": files,
        "total_files": len(rows),
        "review_count": review_count,
        "unsupported_preview_message": UNSUPPORTED_PREVIEW_MESSAGE,
        "server_time": now_iso(),
    }


def a_projectfilemove(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    PM only. Move a document to a different folder of the Arora structure.

    THE BYTES DO NOT MOVE AND NO VERSION IS CREATED. This corrects where a document is filed,
    which is a statement about this project's copy of it, so only `document_uploads` changes.
    The document row, its extraction and every observation derived from it are untouched: a
    misfile is a filing error, not new evidence, and re-deriving anything from it would make
    correcting a folder silently change a number.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    project, member, problem = require_member(session, caller, payload, "projectfilemove")
    if problem:
        return problem
    if member is None or member.project_role != ROLE_PM:
        audit(session, "pm_only_action_denied", participant_id=caller.participant_id,
              action="projectfilemove", project_id=project.legacy_id,
              project_role=member.project_role if member else None)
        session.commit()
        return err("not authorized: only the project's PM may perform this action")

    document_id = str(payload.get("document_id") or "").strip()
    destination = str(payload.get("folder") or "").strip()
    if not document_id or not destination:
        return err("document_id and folder are required")
    # Refused against the template rather than accepted as free text: a path outside the Arora
    # structure would put a document somewhere the tree can never show it again.
    if not is_known_path(destination):
        return err(f"{destination} is not a folder of the Arora project directory")

    upload = session.scalar(
        select(DocumentUpload).where(DocumentUpload.project_id == project.id,
                                     DocumentUpload.document_id == document_id)
    )
    if upload is None:
        return err(f"this project has no document {document_id}")

    previous = upload.folder_path
    upload.folder_path = destination
    # A human has now decided where this belongs, so the placement no longer needs review.
    upload.needs_filing_review = False
    audit(session, "document_refiled", participant_id=caller.participant_id,
          project_id=project.legacy_id, document_id=document_id,
          from_folder=previous, to_folder=destination)
    session.commit()

    session.expire_all()
    saved = session.scalar(
        select(DocumentUpload).where(DocumentUpload.project_id == project.id,
                                     DocumentUpload.document_id == document_id)
    )
    if saved is None or saved.folder_path != destination:
        return err("the move could not be verified: the document is not in the new folder "
                   "after commit")
    return {"ok": True, "project_id": project.legacy_id, "document_id": document_id,
            "folder_path": destination, "previous_folder_path": previous,
            "needs_filing_review": False, "server_time": now_iso()}


def a_projectcorpus(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Any active member, WHEN the technical reviewer is enabled for their account.

    The reference material a technical reviewer reads: specifications, codes of practice and
    client or user requirements, filed in the Arora tree and never analysed. The flag is
    enforced by `features.gate_action` before this function is reached — it is registered under
    `auditor` in GATED_ACTIONS — so this handler does not re-check it and cannot disagree with
    it. What this action does NOT do is decide whether the documents exist: they are filed
    whether the reviewer is on or off, and only reading them is gated.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    project, member, problem = require_member(session, caller, payload, "projectcorpus")
    if problem:
        return problem

    rows = _project_uploads(session, project)
    versions = _versions(rows)
    corpus = [
        _file_row(u, d, versions[u.document_id])
        for u, d in rows if u.filing_class == CLASS_REFERENCE
    ]
    audit(session, "project_read", participant_id=caller.participant_id,
          action="projectcorpus", project_id=project.legacy_id,
          project_role=member.project_role)
    session.commit()
    return {"ok": True, "project_id": project.legacy_id, "corpus": corpus,
            "count": len(corpus), "server_time": now_iso()}


FILE_ACTIONS: dict[str, Callable[[Session, dict, str, int], dict]] = {
    "projectfiles": a_projectfiles,
    "projectfilemove": a_projectfilemove,
    "projectcorpus": a_projectcorpus,
}
