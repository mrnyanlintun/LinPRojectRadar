"""
B7b — upload, hash-cached extraction, compute, and stored results.

THE PATH

    PM uploads a file
      -> sha256 of the bytes
      -> hash already in `documents`?
           YES -> reuse the stored extraction. No model call.
           NO  -> extract once, store bytes and extraction keyed by hash
      -> when the period's document set is complete, run the analytical layer
      -> store ONE computed_results row
      -> every surface afterwards READS that row

WHY THE CACHE IS ON THE HASH AND NOT ON THE UPLOAD

Two PMs who upload the identical file get byte-identical `signalInputs` because they read the
SAME extraction row — not because a verification step compared two extractions and found them
equal. The identity of the research stimulus is established by construction. That is the single
most important property in this module and every other decision here defers to it.

UNKNOWN DOCUMENTS ARE NOT REFUSED

A hash never seen before simply extracts fresh. The platform runs real projects as well as
research sessions, and refusing unrecognised files would break operational use.

A document whose type is not one the extraction layer maps is stored, classified `unmapped`,
contributes NOTHING to signalInputs, and is REPORTED BACK to the PM explicitly. It is never
silently relabelled `monthly_report` — the legacy did that, which fabricated project-controls
inputs out of documents that were never that type.

COMPUTE IS EVENT-DRIVEN

It runs on upload completion, on an explicit `projectcompute`, and on `adminrecompute`. Never
on page load, navigation, or render. `projectresults` READS; it never computes.

RECOMPUTE IS APPEND-ONLY

A recompute writes a NEW row and sets `superseded_by` on the old one. The old row stays
readable forever, because a decision that referenced it must still resolve. A result referenced
by a SUBMITTED decision cannot be modified at all — refused here, and refused again by a
database trigger (migration 0009), because an application-only guarantee is one careless
`session.execute(update(...))` away from being no guarantee.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import logging
import re
import time
from datetime import date, datetime, timezone
from typing import Any, Callable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .extraction_client import build_extractor, extract_many
from .extraction_fields import UNMAPPED, is_mapped
from .extraction_merge import (
    assembly_report, document_as_of, emit_observations, select_signal_inputs,
)
from .jdrive_tree import (
    CLASS_ANALYSED, CLASS_FILED, CLASS_REFERENCE, FILING_CLASS_LABELS, needs_review,
    reference_kind, resolve_destination,
)
from .facade import err, now_iso
from .models import Project
from .research_identity import audit, resolve_caller
from .research_membership import (
    ROLE_PM,
    project_decision_state,
    recommendation_visible,
    reveal_gate_applies,
    require_member,
)
from .research_models import (
    ComputedResult, Decision, Document, DocumentUpload, Observation, ScheduleActivity,
    UploadAttempt, new_ulid,
)
from .recommendation_basis import recommendation_basis
from .schedule_activities import read_activity_table, select_for_display
from .schedule_table import activity_rows_from_document, activity_table_from_document

log = logging.getLogger("opus-gubernatio-server")

# Mirrors the limits the frontend already enforces (assets/js/signals.js:1373, :1382). Enforced
# again here because a client-side limit is a courtesy, not a control.
MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_BASE64_CHARS = 5_000_000

# `compute_portfolio` needs at least two projects with signal data (simulation/portfolio.py:56).
# Below that the snapshot is stored as NULL — distinct from "computed and came back empty".
PORTFOLIO_MIN_PROJECTS = 2


# Test seam for the extractor. A MODULE-level override, deliberately not a payload key: a
# request body must never be able to choose which extractor runs, or a caller could select the
# stub in production and write recorded output into the research record.
_EXTRACTOR_OVERRIDE = None


def set_extractor_override(extractor) -> None:
    """Install an extractor for verification. Pass None to restore normal resolution."""
    global _EXTRACTOR_OVERRIDE
    _EXTRACTOR_OVERRIDE = extractor


# --------------------------------------------------------------------------- helpers


def _refuse_unless_pm(session: Session, caller, member, project, action: str) -> dict | None:
    """
    Only the project's PM may upload or trigger compute.

    This reads the membership row `require_member` already resolved, rather than reimplementing
    the lookup. It is deliberately NOT `refuse_unless_pm_for_assignment`: that helper resolves a
    PM through a research assignment and returns None (permitting the action) for a project with
    no assignment, which is right for the decision flow but would leave an operational project's
    uploads unguarded.
    """
    if member is None or member.project_role != ROLE_PM:
        audit(session, "pm_only_action_denied", participant_id=caller.participant_id,
              action=action, project_id=project.legacy_id,
              project_role=member.project_role if member else None)
        session.commit()
        return err("not authorized: only the project's PM may perform this action")
    return None


def _period_number(period: Any) -> int | None:
    """"P2" -> 2, 2 -> 2, "2" -> 2. None when it cannot be read."""
    if period is None:
        return None
    if isinstance(period, int):
        return period
    text = str(period).strip().upper().lstrip("P")
    return int(text) if text.isdigit() else None


def _resolve_period(session: Session, project: Project, payload: dict) -> tuple[int | None, dict | None]:
    """
    The period is SERVER-DERIVED whenever the project is part of the research chain.

    A client-supplied period would let a participant write into a period they have not reached
    — the same reasoning `research_decision.a_researchprejudgment` applies at :281-283. Where a
    research assignment exists it is authoritative and the payload is ignored entirely.

    An operational project has no assignment and therefore no derived period, so the payload is
    consulted, defaulting to 1. That is not a weakening of the rule: there is no research
    sequence to write into.
    """
    assignment, _decision, _package = project_decision_state(session, project)
    if assignment is not None:
        from .research_decision import current_period
        derived = _period_number(current_period(session, assignment))
        if derived is not None:
            return derived, None
    supplied = _period_number(payload.get("period"))
    if supplied is None:
        return 1, None
    if supplied < 1:
        return None, err("period must be 1 or greater")
    return supplied, None


def _decode(entry: dict) -> tuple[bytes | None, dict | None]:
    """base64 over JSON, matching the wire format assets/js/store.js already speaks."""
    b64 = str(entry.get("dataBase64") or entry.get("data_base64") or "")
    if not b64:
        return None, err("dataBase64 is required for each document")
    if len(b64) > MAX_BASE64_CHARS:
        return None, err("File too large. The maximum is about 3 MB, so please compress the PDF.")
    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        return None, err("dataBase64 is not valid base64")
    if not raw:
        return None, err("decoded file is empty")
    if len(raw) > MAX_FILE_BYTES:
        return None, err("File too large. The maximum is 20 MB")
    return raw, None


def _parse_iso_date(raw: Any) -> date | None:
    """An ISO date, or None. Never raises, never guesses at another format."""
    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw).strip())
    except (TypeError, ValueError):
        return None


def _previous_period_end(session: Session, project: Project, period: int) -> date | None:
    """
    The latest stated ending date among this project's EARLIER periods, or None.

    Read rather than inferred: it is a date somebody stated on an earlier upload. When no
    earlier period carries one, the lower bound of the window is simply unknown and the
    out-of-period check says nothing about it rather than inventing a boundary.
    """
    return session.scalar(
        select(func.max(DocumentUpload.period_end)).where(
            DocumentUpload.project_id == project.id,
            DocumentUpload.period < period,
            DocumentUpload.period_end.is_not(None),
        )
    )


def _out_of_period(doc_date: date | None, period_end: date | None,
                   previous_end: date | None) -> str | None:
    """
    Is this document's own date outside the reporting period it was filed to?

    Returns the reason, in the words the person is shown, or None when it is inside the window
    or when there is nothing to compare against.

    THE DOCUMENT IS NEVER MOVED AND NEVER REFUSED. A date outside the stated period is usually
    a filing mistake, and it is also sometimes correct: a document produced late can belong to
    an earlier period, which is exactly why the person states the period and the platform does
    not infer it. So this reports, and the upload proceeds.

    Both bounds are dates somebody stated. Where a bound is unknown it is not enforced, because
    a guessed boundary would produce a warning the person cannot act on.
    """
    if doc_date is None or period_end is None:
        return None
    if doc_date > period_end:
        return (f"dated {doc_date.isoformat()}, which is after the "
                f"{period_end.isoformat()} end of the reporting period it was filed to")
    if previous_end is not None and doc_date <= previous_end:
        return (f"dated {doc_date.isoformat()}, which is on or before the "
                f"{previous_end.isoformat()} end of an earlier reporting period")
    return None


def _superseded_document_ids(session: Session, project: Project, period: int) -> set[str]:
    """
    The documents that some other upload in this project and period has replaced.

    A reverse lookup, because the pointer runs new -> old (see migration 0013): superseding is
    an insert carrying `supersedes_document_id`, never an update of the row being replaced.
    Scoped to (project, period) deliberately — the same document may be current evidence in
    another project, and `documents` is shared content, not per-project state.
    """
    rows = session.scalars(
        select(DocumentUpload.supersedes_document_id).where(
            DocumentUpload.project_id == project.id,
            DocumentUpload.period == period,
            DocumentUpload.supersedes_document_id.is_not(None),
        )
    ).all()
    return {r for r in rows if r}


def _period_documents(session: Session, project: Project, period: int) -> list[dict]:
    """
    The period's LIVE document SET, in the shape `assemble_signal_inputs` expects.

    One entry per distinct document. The unique index on (project, period, document) already
    makes a re-upload a no-op, so this is a set by construction — which is what makes assembly
    idempotent and therefore a recompute reproducible.

    SUPERSEDED DOCUMENTS ARE EXCLUDED FROM COMPUTATION AND ARE NOT DELETED. Before 0013 both
    versions of a revised document reached assembly, and which one's figures survived was
    decided by `_ordered_docs`'s sha256 tiebreak: a content hash. First-wins fields took the
    lower hash, last-wins fields the higher, additive fields counted BOTH (an RFI log revised
    from 10 to 12 assembled to 22), and a downward correction to a keep_max field was discarded
    entirely. A single revision could therefore produce a signalInputs mixing both versions.

    Excluding them here rather than inside the merge is deliberate: `assemble_signal_inputs` is
    pure and knows nothing of projects or periods, and supersession is a per-project fact. The
    merge continues to receive a set it can treat as authoritative.

    The superseded rows stay readable through `a_projectuploadstatus`, which is what keeps a
    decision that referenced them reproducible.
    """
    superseded = _superseded_document_ids(session, project, period)
    rows = session.execute(
        select(Document, DocumentUpload.supersedes_document_id)
        .join(DocumentUpload, DocumentUpload.document_id == Document.document_id)
        .where(DocumentUpload.project_id == project.id, DocumentUpload.period == period)
    ).all()
    seen: set[str] = set()
    out: list[dict] = []
    for d, supersedes in rows:
        if d.document_id in superseded:
            continue
        if d.sha256 in seen:
            continue
        seen.add(d.sha256)
        out.append({"sha256": d.sha256, "doc_type": d.doc_type or UNMAPPED,
                    "filename": d.filename, "extraction": d.extraction or {},
                    # Carried so the caller can record provenance on the computed result.
                    # `assemble_signal_inputs` ignores keys it does not know.
                    "document_id": d.document_id,
                    # 0014. The declared document-level revision edge, promoted onto every
                    # observation this document emits (`revision_of`).
                    "supersedes": supersedes})
    return out


_IDENTIFIER_RE = re.compile(
    r"(?:claim|change[ _-]?order|co|site[ _-]?obs(?:ervation)?|obs)[ _\-#]*(\d+)", re.IGNORECASE)


def _identifier_from_filename(filename: str) -> str | None:
    """
    A claim or site-observation number read off the filename, or None.

    THE EXTRACTION VOCABULARY HAS NEITHER NUMBER. The Arora template wants
    `8_CLAIMS/CLAIM #/...` and `7_FIELD-SITE VISITS/YYYY-MM-DD SITE OBS #`, and nothing in
    `extraction_fields.py` asks a document for its claim number or its observation number, so
    there is no extracted field to read. The filename is the only evidence available, and when
    it carries none the folder is created without the identifier rather than with an invented
    one. A PM supplies it by moving the document, which is why moving exists.
    """
    match = _IDENTIFIER_RE.search(str(filename or ""))
    return match.group(1) if match else None


def _decide_filing(doc_type: str, extraction: Any, filename: str,
                   confidence: float | None) -> dict:
    """
    Where this document is filed, what it counts as, and whether the placement needs review.

    Pure: no clock and no database. The date comes from the document, never from now.
    """
    reference = reference_kind(filename)
    if reference is not None:
        filing_class = CLASS_REFERENCE
    elif is_mapped(doc_type or ""):
        filing_class = CLASS_ANALYSED
    else:
        # Stored and never analysed, and that is the EXPECTED outcome for most of the tree:
        # discipline calculations, Revit files, LEED credits, survey photos. It is not a
        # failed extraction and must never read as one.
        filing_class = CLASS_FILED

    as_of = document_as_of(doc_type, extraction)
    review = needs_review(doc_type or "", confidence, filing_class, filename)
    folder = resolve_destination(
        doc_type or "", filing_class=filing_class, as_of=as_of,
        identifier=_identifier_from_filename(filename), reference=reference,
        filename=filename, confidence=confidence,
    )
    return {"folder_path": folder, "filing_class": filing_class,
            "needs_filing_review": review, "reference_kind": reference}


def _persist_observations(session: Session, project: Project, period: int) -> int:
    """
    0014. Project the period's stored extractions into the append-only observation store.

    EVERY upload in the period is projected, superseded ones included — the earlier revision's
    rows are retained and never deleted; selection is what excludes them, not storage. Rows are
    keyed by (project, period, document, field, entity), so re-deriving is an insert of what is
    missing and never an update: the same document always projects to the same rows, because
    the extraction it projects from is content-addressed and immutable.

    A document whose extraction is refused (doc risk out of range) projects nothing — the same
    refusal the selection path raises, kept symmetrical so the store can never hold figures
    the merge refused.

    Returns the number of rows inserted.
    """
    rows = session.execute(
        select(Document, DocumentUpload.supersedes_document_id)
        .join(DocumentUpload, DocumentUpload.document_id == Document.document_id)
        .where(DocumentUpload.project_id == project.id, DocumentUpload.period == period)
    ).all()
    existing = {
        (r[0], r[1], r[2]) for r in session.execute(
            select(Observation.document_id, Observation.field, Observation.entity_key)
            .where(Observation.project_id == project.id, Observation.period == period)
        ).all()
    }
    inserted = 0
    for d, supersedes in rows:
        try:
            emitted = emit_observations({
                "sha256": d.sha256, "doc_type": d.doc_type or UNMAPPED,
                "filename": d.filename, "extraction": d.extraction or {},
                "document_id": d.document_id, "supersedes": supersedes,
            })
        except Exception:
            continue
        for o in emitted:
            key = (d.document_id, o["field"], o["entity_key"] or "")
            if key in existing:
                continue
            existing.add(key)
            session.add(Observation(
                project_id=project.id, period=period,
                field=o["field"], value=o["value"], kind=o["kind"],
                entity_key=o["entity_key"] or "", entity_state=o["entity_state"],
                as_of=o["as_of"], document_id=d.document_id,
                revision_of=o["revision_of"], source_doc_type=o["doc_type"],
            ))
            inserted += 1
    return inserted


def _persist_schedule_activities(session: Session, project: Project, period: int) -> int:
    """
    0021. Project this period's stored activity tables into the schedule store.

    The same shape as `_persist_observations`, for the same reasons: every upload in the period
    is projected (superseded ones included, because storage retains and selection excludes),
    rows are keyed by (project, period, document, activity) so re-deriving inserts only what is
    missing, and nothing is ever updated in place. A document's activity table is
    content-addressed and immutable, so the same document always projects to the same rows.

    A ROW THAT WOULD NOT PARSE IS STILL STORED, with its refusals and `usable_for_trend` false.
    Dropping it would leave the store unable to say why a schedule of nine activities yielded
    six comparable ones, and "loud refusal over quiet approximation" means the refusal has to be
    readable, not merely absent.

    Returns the number of rows inserted.
    """
    rows = session.execute(
        select(Document, DocumentUpload.supersedes_document_id)
        .join(DocumentUpload, DocumentUpload.document_id == Document.document_id)
        .where(DocumentUpload.project_id == project.id, DocumentUpload.period == period)
    ).all()
    existing = {
        (r[0], r[1]) for r in session.execute(
            select(ScheduleActivity.document_id, ScheduleActivity.activity_key)
            .where(ScheduleActivity.project_id == project.id,
                   ScheduleActivity.period == period)
        ).all()
    }
    inserted = 0
    for d, _supersedes in rows:
        ex = d.extraction or {}
        if not isinstance(ex, dict):
            continue
        # THE READER TAKES THE ROWS. The document's own bytes are stored, so the activity table
        # is re-read from the source rather than from anything a model retyped: a hundred rows
        # and a thousand rows cost the same here, and no row can be silently mistyped on the way.
        # `milestones_json` remains as the fallback for a document this reader cannot open (a
        # PDF, whose tables are not available on this side of the model boundary) and for any
        # extraction stored before the reader existed.
        activities = activity_rows_from_document(
            d.content or b"", d.mime_type or "", d.filename or "")
        if not activities:
            activities = read_activity_table(ex.get("milestones_json"))
        if not activities:
            continue
        doc_type = d.doc_type or UNMAPPED
        as_of = document_as_of(doc_type, ex)
        for a in activities:
            key = (d.document_id, a["activity_key"])
            if key in existing:
                continue
            existing.add(key)
            session.add(ScheduleActivity(
                project_id=project.id, period=period, document_id=d.document_id,
                activity_key=a["activity_key"], description=a["description"],
                baseline_start=a["baseline_start"],
                baseline_start_kind=a["baseline_start_kind"],
                baseline_finish=a["baseline_finish"],
                baseline_finish_kind=a["baseline_finish_kind"],
                current_finish=a["current_finish"],
                current_finish_kind=a["current_finish_kind"],
                percent_complete=a["percent_complete"],
                unparsed=a["unparsed"], usable_for_trend=bool(a["usable_for_trend"]),
                as_of=as_of, source_doc_type=doc_type,
            ))
            inserted += 1
    return inserted


def _schedule_snapshot(session: Session, project: Project, period: int) -> dict | None:
    """
    ONE period's schedule, as one snapshot, or None where that period read no schedule.

    WHICH DOCUMENT'S TABLE, when a period carries more than one. Superseded documents are
    excluded exactly as they are from computation. Among the rest, the document with the latest
    `as_of` wins, a dated document always beats an undated one, and ties fall back to the
    document id — the same precedence rule `select_signal_inputs` applies to a SNAPSHOT field,
    stated once more here because a schedule is a snapshot: two schedule updates in one period
    are two accounts of the same activities, not two populations to merge. Merging them would
    let one document's `D100` and another's `D200` describe a schedule that never existed.
    """
    superseded = _superseded_document_ids(session, project, period)
    rows = [
        r for r in session.scalars(
            select(ScheduleActivity).where(
                ScheduleActivity.project_id == project.id,
                ScheduleActivity.period == period,
            )
        ).all()
        if r.document_id not in superseded
    ]
    if not rows:
        return None
    by_doc: dict[str, list[ScheduleActivity]] = {}
    for r in rows:
        by_doc.setdefault(r.document_id, []).append(r)
    doc_id = max(by_doc, key=lambda d: (by_doc[d][0].as_of is not None,
                                        str(by_doc[d][0].as_of or ""), d))
    chosen = sorted(by_doc[doc_id], key=lambda r: r.activity_key)
    at = str(chosen[0].as_of or "")
    return {
        "period": period,
        "at": at,
        "milestones": [
            {
                # `name` and `forecast` are the keys Milestone Trend Analysis reads. The rest
                # are additional facts the module ignores and a reader does not: the module's
                # arithmetic is unchanged and nothing was reshaped to fit a key name.
                "name": r.activity_key,
                "forecast": r.current_finish,
                "forecast_kind": r.current_finish_kind,
                "description": r.description,
                "baseline_start": r.baseline_start,
                "baseline_finish": r.baseline_finish,
                "percent_complete": r.percent_complete,
            }
            for r in chosen if r.usable_for_trend
        ],
        "unusable": [
            {"name": r.activity_key, "unparsed": r.unparsed or []}
            for r in chosen if not r.usable_for_trend
        ],
    }


def _schedule_display(session: Session, project: Project, period: int) -> dict | None:
    """
    The period's schedule, reduced to the rows worth drawing. Reads the per-activity store.

    NOT EVERY ROW IS DRAWN, and the rule that decides is `schedule_activities.DISPLAY_RULE`,
    stated in the response beside the selection so a reader can see what was left out and why
    rather than assuming a short list means a short schedule. `total` and `not_shown` are
    returned for the same reason.

    The previous period's rows are read only to decide what MOVED, and only from periods
    strictly earlier than this one, which is the same bound `_milestone_history` keeps.
    """
    superseded = _superseded_document_ids(session, project, period)

    def rows_for(p: int) -> list[dict]:
        return [
            {"activity_key": r.activity_key, "description": r.description,
             "baseline_finish": r.baseline_finish, "current_finish": r.current_finish,
             "current_finish_kind": r.current_finish_kind,
             "percent_complete": r.percent_complete,
             "usable_for_trend": r.usable_for_trend}
            for r in session.scalars(
                select(ScheduleActivity).where(ScheduleActivity.project_id == project.id,
                                               ScheduleActivity.period == p)
            ).all()
            if r.document_id not in superseded or p != period
        ]

    current = rows_for(period)
    if not current:
        return None
    earlier = sorted({
        int(p) for p in session.scalars(
            select(ScheduleActivity.period).where(
                ScheduleActivity.project_id == project.id,
                ScheduleActivity.period < period,
            )
        ).all()
    })
    previous = rows_for(earlier[-1]) if earlier else []
    out = select_for_display(current, previous)
    out["period"] = period
    out["compared_with_period"] = earlier[-1] if earlier else None
    return out


def _milestone_history(session: Session, project: Project,
                       period: int) -> list[dict]:
    """
    `milestoneHistory`: one snapshot per reporting period, oldest first, ending with this one.

    STRICTLY EARLIER PERIODS PLUS THIS ONE, which is the `_earlier_live_results` rule applied to
    the schedule store: a period's snapshot is assembled from rows whose own period is <= the
    period being computed, so recomputing period 1 while periods 2, 3 and 4 exist reads none of
    them and reproduces what period 1 was computed from. The schedule store makes that
    structural rather than careful — a period's rows are written once, for that period, and no
    later period's upload ever rewrites them.

    A period that read no schedule contributes NO snapshot rather than an empty one. An empty
    snapshot would make every activity look absent, and absence read as movement is precisely
    the error this task forbids.

    Fewer than two snapshots is not a trend, and the key is then omitted entirely so the module
    abstains on its own `len(mh) < 2` guard rather than on a fabricated series.
    """
    periods = sorted({
        int(p) for p in session.scalars(
            select(ScheduleActivity.period).where(
                ScheduleActivity.project_id == project.id,
                ScheduleActivity.period <= period,
            )
        ).all()
    })
    out: list[dict] = []
    for p in periods:
        snap = _schedule_snapshot(session, project, p)
        if snap is not None:
            out.append(snap)
    return out


def _live_result(session: Session, project: Project, period: int) -> ComputedResult | None:
    return session.scalars(
        select(ComputedResult).where(
            ComputedResult.project_id == project.id,
            ComputedResult.period == period,
            ComputedResult.superseded_by.is_(None),
        )
    ).first()


def _document_fingerprint(documents: list[dict]) -> set[tuple[str, str]]:
    """The identity of a period's document set: {(document_id, sha256)} from the live set."""
    return {(d["document_id"], d["sha256"]) for d in documents}


def _result_fingerprint(result: ComputedResult) -> set[tuple[str, str]] | None:
    """The document set recorded on a stored result, or None when no record exists."""
    src = result.source_documents
    if not src:
        return None
    return {(d["document_id"], d["sha256"]) for d in src}


def _period_is_stale(session: Session, project: Project, period: int,
                     result: ComputedResult) -> tuple[bool, str]:
    """
    A period is stale when the documents it was computed from differ from the period's current
    live document set. Compared by the set of (document_id, sha256) pairs, which is stronger
    than a timestamp: it names the exact inputs the result was built from, and the exact inputs
    the period holds now.

    Returns (is_stale, reason). The reason is a human-readable sentence for the per-period
    message.
    """
    current_docs = _period_documents(session, project, period)
    current_fp = _document_fingerprint(current_docs)
    stored_fp = _result_fingerprint(result)
    if stored_fp is None:
        return False, "no source_documents record on the stored result; left untouched"
    if current_fp == stored_fp:
        return False, ""
    added = current_fp - stored_fp
    removed = stored_fp - current_fp
    parts: list[str] = []
    if added:
        parts.append(f"{len(added)} document(s) added")
    if removed:
        parts.append(f"{len(removed)} document(s) removed or replaced")
    reason = "; ".join(parts) + " since the last computation"
    return True, reason


def _derive_cutoff(documents: list[dict], reuse: ComputedResult | None) -> date:
    """
    `period_cutoff` replaces the wall clock inside the analytical layer (only C1.2 Data
    Timeliness reads it, simulation/models_dq.py:60).

    A RECOMPUTE REUSES THE SUPERSEDED ROW'S CUTOFF. That is what makes "recomputing on identical
    inputs produces identical module_results" true rather than nearly true: derive it from the
    clock instead and C1.2 drifts by however many days elapsed between the two runs, and the
    guarantee quietly becomes false.

    On a first compute it is the latest date the period's evidence speaks about — the maximum
    of every observation's `as_of` and every document's `document_date` — falling back to the
    server date when nothing carries a parseable date (still D3, unchanged here).

    0014. THE OBSERVATIONS' OWN DATES ARE PART OF THE MAXIMUM, and that is load-bearing:
    selection is `as_of <= cutoff`, so a cutoff derived from `document_date` alone would
    silently exclude a pay application whose `application_date` runs later than the period's
    last `document_date`. Deriving both from the same dates makes "the cutoff" and "the
    evidence's latest date" one number on a first compute — which is also what `docDate` now
    derives from, so the A5 disagreement (two answers to "as of when") is closed rather than
    relocated.
    """
    if reuse is not None and reuse.period_cutoff is not None:
        return reuse.period_cutoff
    latest: date | None = None
    for d in documents:
        raw = (d.get("extraction") or {}).get("document_date")
        try:
            parsed = date.fromisoformat(str(raw)) if raw else None
        except (TypeError, ValueError):
            parsed = None
        if parsed and (latest is None or parsed > latest):
            latest = parsed
        try:
            for o in emit_observations(d):
                if o["as_of"] and (latest is None or o["as_of"] > latest):
                    latest = o["as_of"]
        except Exception:
            # A refused document (e.g. doc risk out of range) contributes no date here; the
            # refusal itself surfaces where the observations are actually consumed.
            pass
    return latest or datetime.now(timezone.utc).date()


def _earlier_live_results(session: Session, project: Project,
                          period: int) -> list[ComputedResult]:
    """
    This project's live stored results for STRICTLY EARLIER reporting periods, in period order.

    THE ONE READ every cross-period series on this platform is assembled from, and the one place
    the period-alignment invariant is enforced. `period < period` is evaluated against the period
    being computed, so recomputing period 1 while periods 2, 3 and 4 exist reads none of them and
    reproduces what period 1 was computed from. This is deliberately NOT the shape of the P1
    defect, where a portfolio vector was chosen by `max(period)` with no alignment to the period
    being computed and a stored period-1 result changed when another project reached period 2.

    Live rows only: a superseded result has been replaced by a recompute of that same period, and
    its figures are no longer the project's account of that period.
    """
    return list(session.scalars(
        select(ComputedResult)
        .where(
            ComputedResult.project_id == project.id,
            ComputedResult.period < period,
            ComputedResult.superseded_by.is_(None),
        )
        .order_by(ComputedResult.period)
    ).all())


def _period_snapshots(session: Session, project: Project, period: int,
                      si: dict) -> list[dict]:
    """
    The project's own per-period snapshots, oldest first, ending with the period being computed.

    `compute_portfolio`'s third argument. Until now every caller passed a literal `None`, so both
    of its `len(history) >= 2` guards were permanently false and the Signal Trajectory Classifier
    abstained on every project ever computed, while the composite anomaly score was always the
    three-term average with no trend term. Nothing was missing from storage: each period already
    stored its own cpi, and nobody had joined them.

    The element shape is the one `portfolio.py` reads and the one the Apps Script wrote,
    `{"period": n, "signal_inputs": {"cpi": ..., "spi": ...}}` — a stored figure read back, never
    a derived one.

    THE CURRENT PERIOD IS THE LAST ELEMENT, for the same reason `_period_history` ends its series
    with the current value: the trend being asked for is the one ending now, and a series that
    stopped at the previous period would report last period's trajectory as this period's. It
    also keeps the two assemblies on one rule — a trajectory becomes available at exactly the
    period cpiHistory does, the second, and never before.

    Assembled from `_earlier_live_results`, so no snapshot is ever taken from a period later than
    the one being computed.
    """
    rows = _earlier_live_results(session, project, period)
    out: list[dict] = []
    for r in rows:
        s = r.signal_inputs or {}
        out.append({"period": r.period,
                    "signal_inputs": {"cpi": s.get("cpi"), "spi": s.get("spi")}})
    out.append({"period": period,
                "signal_inputs": {"cpi": si.get("cpi"), "spi": si.get("spi")}})
    return out


def _period_history(session: Session, project: Project, period: int,
                    si: dict) -> dict[str, list[float]]:
    """
    The project's cpi and spi series across its EARLIER reporting periods, ending with this one.

    D1. Four modules read these series — CUSUM, Kalman, ARIMA and Regression to Mean — and until
    now nothing supplied them. Three abstained on every project; CUSUM synthesised twelve
    observations from the current SPI and drew a control chart over them.

    STRICTLY EARLIER PERIODS ONLY, and that is the whole safety argument. The pipeline audit
    found that the portfolio vector block below reaches every project's most recent live result
    regardless of period, so a later period's figures reach an earlier period's computation
    (defect P1, queued separately). This query cannot do that: `period < period` is evaluated
    against the period being computed, so recomputing period 2 in period 6 reads period 1 and
    nothing else, and the series a stored result was computed from can always be reconstructed.
    That is also why the series is built here and not from the project document, which carries no
    per-period figures.

    Live rows only: a superseded result has been replaced by a recompute of that same period, and
    its figures are no longer the project's account of that period.
    """
    rows = _earlier_live_results(session, project, period)

    out: dict[str, list[float]] = {}
    for key, field in (("cpiHistory", "cpi"), ("spiHistory", "spi")):
        series: list[float] = []
        for r in rows:
            v = (r.signal_inputs or {}).get(field)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                series.append(float(v))
        current = si.get(field)
        if isinstance(current, (int, float)) and not isinstance(current, bool):
            series.append(float(current))
        # A one-element series is what `_history` already synthesises from the scalar; passing it
        # would only restate si[field] under a second name. Supply a series or supply nothing.
        if len(series) >= 2:
            out[key] = series
    return out


def _events_as_of(project: Project, cutoff: date) -> list[dict]:
    """
    The project's event log, truncated at the period's data cutoff.

    D1. `_append_event` in writes.py has always stored `{"event": ..., "at": ...}` on the project
    document, which is exactly the shape C1.4 and C1.7 document reading. Nothing passed it in, so
    Audit Trail Completeness reported "0 events recorded" about a platform that records events.

    TRUNCATED AT THE CUTOFF, for the same reason C1.2 takes its "now" from the cutoff rather than
    the clock: without it, recomputing an early period would see every event logged since, and a
    later period's activity would decide an earlier period's audit-trail verdict. An event whose
    `at` cannot be read as a date is kept rather than dropped, because discarding an event on a
    formatting fault would understate the trail.

    `at` IS NARROWED TO ITS DATE PART, which is the contract models_dq documents and not a
    convenience. `_append_event` stamps a full ISO datetime; `_js_date_ms` refuses datetime
    strings on purpose, because a 'T' form without a zone parses as LOCAL time in JavaScript and
    guessing which zone was meant is the hazard VALIDATION.md flags. Passing the raw stamp would
    have made C1.7 abstain on every real project while appearing wired, so the narrowing happens
    here, at the boundary, rather than by loosening a parser that is strict deliberately.
    """
    events = (project.doc or {}).get("events") or []
    limit = str(cutoff)
    out = []
    for e in events:
        if not isinstance(e, dict):
            continue
        at = e.get("at")
        if isinstance(at, str) and len(at) >= 10:
            if at[:10] > limit:
                continue
            e = {**e, "at": at[:10]}
        out.append(e)
    return out


def _compute_and_store(session: Session, project: Project, period: int,
                       reuse_cutoff_from: ComputedResult | None = None,
                       result_id: str | None = None) -> dict:
    """
    Run the analytical layer and write ONE row. Calls `simulation` entry points; changes nothing
    inside that package.

    `result_id` may be supplied so the caller can mark the outgoing row superseded BEFORE this
    row is inserted. `uq_computed_results_one_live` is a partial unique index over
    (project_id, period) WHERE superseded_by IS NULL, so inserting the new row first would put
    two live rows in the table for the duration of the flush and the index would — correctly —
    refuse it. ULIDs are generated in Python precisely so an id can be known before its row
    exists (see `new_ulid`), which makes supersede-then-insert possible without a deferred
    constraint.
    """
    documents = _period_documents(session, project, period)
    cutoff = _derive_cutoff(documents, reuse_cutoff_from)
    # 0014. signalInputs is the OUTPUT of selection over observations at the cutoff, no longer
    # a stored accumulator. Selection covers the LIVE document set (superseded documents are
    # excluded from computation exactly as before); the store itself keeps every revision's
    # rows. On a recompute the reused cutoff bounds every selection, so evidence dated after
    # it — added later to the period — cannot silently change what the period reports.
    _persist_observations(session, project, period)
    _persist_schedule_activities(session, project, period)
    observations: list[dict] = []
    for d in documents:
        observations.extend(emit_observations(d))
    si = select_signal_inputs(observations, cutoff)

    # D1. One input the analytical layer reads that the pure merge cannot produce, because it is
    # not a property of this period's documents: the project's event log. It is added here rather
    # than inside `assemble_signal_inputs`, which must stay pure, deterministic and order
    # independent — it knows nothing of projects, periods or the session. It is stored on the row
    # as part of `signal_inputs`, so the result records what the modules actually saw and not a
    # subset of it. The cross-period series are assembled in `run_and_store`, which is the one
    # place both assembly paths pass through.
    si["events"] = _events_as_of(project, cutoff)

    result = run_and_store(session, project, period, si, cutoff,
                           source_documents=[
                               {"document_id": d.get("document_id"), "sha256": d.get("sha256"),
                                "doc_type": d.get("doc_type"), "filename": d.get("filename")}
                               for d in documents
                           ],
                           result_id=result_id)
    result["documents"] = documents
    return result


def run_and_store(session: Session, project: Project, period: int, si: dict,
                  cutoff: date, *, source_documents: list[dict],
                  result_id: str | None = None) -> dict:
    """
    The computation-and-storage tail shared by BOTH assembly paths: the document path above,
    and training period generation (`training.py`), whose `signalInputs` are projected from a
    deterministic state instead of selected from observations. Everything from `compute_project`
    on is identical for both — that is the run 2 brief's requirement that a training project's
    signals compute through the normal path, made structural: there is no second computation
    path to drift.
    """
    from .simulation import compute_project, compute_portfolio

    # THE CROSS-PERIOD SERIES, assembled here because this is the single point BOTH assembly
    # paths pass through: the document path above and training period generation. Every period
    # already stored its own cpi and spi; these two calls are the join nobody had made. Both read
    # `_earlier_live_results` and nothing else, so no series can be assembled from a period later
    # than the one being computed, and a recompute of an earlier period reproduces it exactly.
    #
    # Placed BEFORE `compute_project` and written onto `si`, which is the dict stored on the row,
    # so the stored result records the series the modules were actually given.
    si.update(_period_history(session, project, period, si))
    history = _period_snapshots(session, project, period, si)

    # `milestoneHistory`, served for the first time. Milestone Trend Analysis has never
    # computed: its input was declared UNSERVABLE and was, correctly, because the extraction
    # returned the source table's own headings and its dates parsed with nothing. Both gaps are
    # closed on THIS side of the boundary (`schedule_activities.py`, `schedule_dates.py`), and
    # the schedule is now stored per period, so the series is a read rather than a fabrication.
    #
    # SERVED IN THE SHAPE THE MODULE READS, without changing what it computes: snapshots
    # carrying `name` and `forecast`, oldest first. Nothing was reshaped to fit a key name —
    # the module's `forecast` is the activity's current expected finish, which is exactly what
    # the source table's current-finish column states, and the extra facts each row carries
    # (baseline dates, percent complete, whether the date is actual or forecast) travel beside
    # those keys where a reader can use them and the module simply ignores them.
    #
    # FEWER THAN TWO SNAPSHOTS AND THE KEY IS ABSENT. One period is not a trend, and the module
    # must abstain on its own guard rather than on a series padded to reach a minimum.
    milestone_history = _milestone_history(session, project, period)
    if len(milestone_history) >= 2:
        si["milestoneHistory"] = milestone_history

    run = compute_project(si, project.legacy_id, f"P{period}", cutoff)

    # Portfolio snapshot — CUTOFF-ALIGNED (P1). A portfolio vector for another project is
    # selected by `period_cutoff <= cutoff`, taking that project's latest live result at or
    # before THIS computation's cutoff. NEVER max(period): that let a stored period-1 result
    # change when another project advanced to period 2, and made two projects computed for
    # the same period at different wall-clock moments see different portfolios. With the
    # cutoff bound, recomputing an earlier period after other projects have moved on
    # reproduces the portfolio that period actually saw.
    others = session.scalars(
        select(ComputedResult).where(
            ComputedResult.superseded_by.is_(None),
            ComputedResult.period_cutoff <= cutoff,
        )
    ).all()
    vectors: list[dict] = []
    by_project: dict[Any, ComputedResult] = {}
    for r in others:
        prev = by_project.get(r.project_id)
        if prev is None or (
            (r.period_cutoff, r.period or 0) > (prev.period_cutoff, prev.period or 0)
        ):
            by_project[r.project_id] = r
    for pid, r in by_project.items():
        legacy = session.get(Project, pid)
        # TRAINING ISOLATION, BOTH DIRECTIONS (run 2). A training project's vector must never
        # enter a real project's portfolio snapshot — that snapshot is stored on the result and
        # is exactly "anything the analysis reads". And a training run's own portfolio must not
        # ingest real projects either: a trainee's screen is generated, not an operational
        # surface. So a vector is included only when its project's is_training matches the
        # project being computed. A missing project row contributes nothing rather than
        # defaulting in.
        if legacy is None or bool(legacy.is_training) != bool(project.is_training):
            continue
        s = r.signal_inputs or {}
        vectors.append({"id": legacy.legacy_id if legacy else str(pid),
                        "cpi": s.get("cpi"), "spi": s.get("spi"),
                        "docRiskScore": s.get("docRiskScore"),
                        "actualPctComplete": s.get("actualPctComplete")})
    # Include this project's freshly computed vector, which is not yet stored.
    vectors = [v for v in vectors if v["id"] != project.legacy_id]
    vectors.append({"id": project.legacy_id, "cpi": si.get("cpi"), "spi": si.get("spi"),
                    "docRiskScore": si.get("docRiskScore"),
                    "actualPctComplete": si.get("actualPctComplete")})
    # Always call, and store whatever it returns — including the insufficient_data shape.
    # `vectors` always has at least one entry (this project's own, appended above), so
    # `compute_portfolio`'s own `len(portfolio) < 2` guard is what decides "below threshold",
    # not a check duplicated here. Collapsing that shape to a bare NULL (the prior behaviour)
    # discarded its message — "Portfolio too small for anomaly detection — need at least 3
    # projects with signal data" (portfolio.py, reproducing a legacy off-by-one between the
    # guard and its own wording) — which T5's portfolio view is required to render verbatim,
    # not reconstruct. `PORTFOLIO_MIN_PROJECTS` stays as documentation of that guard's value,
    # not as a second gate here.
    # `history` is this project's own per-period snapshots (see `_period_snapshots`). It was a
    # literal None at every call site, which held D1.3 permanently absent. `compute_portfolio`
    # already accepts and guards it; nothing inside `simulation/` changed to receive it.
    snapshot = compute_portfolio(vectors, project.legacy_id, history, cutoff)

    row = ComputedResult(
        result_id=result_id or new_ulid(),
        project_id=project.id,
        period=period,
        signal_inputs=si,
        # 0013. WHICH DOCUMENT VERSIONS PRODUCED THIS RESULT. Taken from the live set actually
        # assembled, so a result computed before a revision keeps naming the version it used
        # even after that version is superseded. `signal_inputs.sources` records a docType per
        # field and never a document, so without this a result became uninterpretable the
        # moment the period's document set moved on. A training period stores an EMPTY list:
        # no document produced it, and inventing provenance would be worse than stating none.
        source_documents=source_documents,
        module_results=run.get("modules"),
        # 0020. Persist the abstention reasons `run_all()` already produces, so the ledger can
        # read them back after the fact instead of only for the instant of the compute response.
        abstained=run.get("abstained"),
        category_statuses=run.get("category_statuses"),
        project_status=run.get("project_status"),
        portfolio_snapshot=snapshot,
        # NOT NULL in the schema. Taken from the run itself, never defaulted here: a result
        # whose provenance was invented by the caller is worse than no result.
        simulation_version=run["simulation_version"],
        seed=str(run["seed"]),
        period_cutoff=cutoff,
    )
    session.add(row)
    session.flush()
    return {"row": row, "run": run}


# Keys inside a MODULE result that name or rank a course of action, or name who should take it.
# The analytical layer emits them from three modules:
#   models_gov.py:632-634       B4.4 Regret Minimization -> recommended_action, expected_regret
#   models_decision.py:150-151  B3.1 ABM Governance      -> action, authority
#
# These are recommendations. Returning them to a member before their PM has locked the period's
# preliminary judgment would defeat the reveal gate just as surely as returning the package
# itself — "the model says investigate" is the treatment, whatever field it arrives in.
#
# T4: "authority" was added to this set. B3.1 emits `"authority": "Sponsor + Steering committee"`
# alongside its action — naming who must act is part of prescribing the act, and a participant
# who reads it before locking has been told what the model wants done and by whom.
_ACTION_KEYS = frozenset({"recommended_action", "expected_regret", "action", "authority"})

# T4: THE LEAK B7b LEFT OPEN, AND WHY STRIPPING KEYS WAS NEVER ENOUGH.
#
# B7b stripped action-bearing KEYS. It did not touch PROSE. Both action-bearing modules also
# render their recommendation into `evidence_metric`, a free-text field that survived redaction
# untouched and was rendered on the evidence screen:
#
#   models_gov.py:636-640   f"Minimax regret recommends: {recommended} (expected regret score
#                            {min_regret}/30); this decision minimizes worst-case outcome..."
#   models_decision.py:152  f"{d['healthState']}: {d['action']} ({d['authority']})"
#
# So before this change, a participant on the evidence screen — before locking anything — could
# read "Minimax regret recommends: escalate". That is the entire treatment, delivered in the one
# field nobody thought to redact, and it would have silently invalidated every decision made
# through this interface.
#
# The fix is not to sanitise the prose. Scrubbing a substring out of a sentence is a guess about
# wording that a later edit upstream would quietly defeat, and this package must not be edited
# (it is the validated analytical layer). Instead, when a module is identified as action-bearing
# — by carrying any `_ACTION_KEYS` field — its narrative field is REPLACED wholesale. A module
# that recommends nothing keeps its evidence_metric untouched, so the evidence screen still
# explains every non-prescriptive module in full.
_NARRATIVE_KEYS = frozenset({"evidence_metric"})

_WITHHELD_NARRATIVE = ("This module's finding is withheld until the preliminary judgment for "
                       "this period is locked.")


def _redact_module_actions(modules) -> list:
    """
    Strip action-bearing keys AND action-bearing prose from module results for a withheld read.

    Redaction happens in the VIEW, never in storage. The stored row keeps every field, because
    a result that has had values removed from it can no longer be reproduced or compared
    against a later recompute — and the provenance columns would then be describing a row that
    no longer holds what was computed.
    """
    if not isinstance(modules, list):
        return modules
    out = []
    for m in modules:
        if not isinstance(m, dict):
            out.append(m)
            continue
        redacted = {k: v for k, v in m.items() if k not in _ACTION_KEYS}
        if len(redacted) != len(m):
            # Action-bearing. Its narrative restates the recommendation, so replace it rather
            # than ship prose that was written to explain a field we just removed.
            for narrative in _NARRATIVE_KEYS:
                if narrative in redacted:
                    redacted[narrative] = _WITHHELD_NARRATIVE
            redacted["recommendation_withheld"] = True
        out.append(redacted)
    return out


def _result_view(row: ComputedResult, *, include_recommendation: bool,
                 package=None) -> dict:
    """
    The stored result as returned to a member.

    The recommendation package is spliced in ONLY when `recommendation_visible` says so, and
    when it says no, action-bearing MODULE fields are redacted too — see `_ACTION_KEYS`.
    """
    view = {
        "result_id": row.result_id,
        "period": row.period,
        "signal_inputs": row.signal_inputs,
        "module_results": (row.module_results if include_recommendation
                           else _redact_module_actions(row.module_results)),
        # 0020. Which modules abstained on this row and why, verbatim (module_id + reason, never
        # an action field, so nothing here is gated by `recommendation_visible`). NULL on rows
        # computed before the column existed.
        "abstained": row.abstained,
        "category_statuses": row.category_statuses,
        "project_status": row.project_status,
        "portfolio_snapshot": row.portfolio_snapshot,
        "simulation_version": row.simulation_version,
        "seed": row.seed,
        "period_cutoff": str(row.period_cutoff) if row.period_cutoff else None,
        "computed_at": row.computed_at.isoformat() if row.computed_at else None,
        "superseded_by": row.superseded_by,
        # 0013. Which document versions produced this result. NULL on rows computed before
        # that migration, which is honest rather than backfilled: see the migration's note.
        "source_documents": row.source_documents,
    }
    # WHY THE RECOMMENDED COURSE IS THE ONE RECOMMENDED. Derived from what this row already
    # holds, and served beside it so the card explains the recommendation instead of saying it
    # cannot. Absent when the action-bearing fields were withheld by the reveal gate, which is
    # correct: there is no recommendation on that read to explain.
    _mods = row.module_results if include_recommendation else None
    _regret = next((m for m in (_mods or [])
                    if isinstance(m, dict) and m.get("method_class") == "Regret_Minimization"),
                   None)
    view["recommendation_basis"] = recommendation_basis(row.signal_inputs, _regret)
    if include_recommendation and package is not None:
        view["recommendation"] = {
            "package_id": package.package_id,
            "package_hash": package.hash,
            "recommended_action": package.recommended_action,
            "alternatives": package.alternatives,
            "detected_condition": package.detected_condition,
            "limitations": package.limitations,
        }
    else:
        # Explicit, so a reader of a response can tell "withheld" from "absent".
        view["recommendation"] = None
        # WITHHELD MEANS THE REVEAL GATE REFUSED IT, not merely that there is no package.
        # A project outside the research protocol has no package to withhold: recommendation
        # packages are researcher-authored study artifacts. Flagging those reads as withheld
        # told an operational project manager that something was being kept from them when
        # nothing was, which is the same false statement this task exists to remove from the
        # card.
        if not include_recommendation:
            view["recommendation_withheld"] = True
    return view


# --------------------------------------------------------------------------- actions


def a_projectupload(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    PM only. Accepts one or more documents for the project's current period.

    Returns per file: filename, whether it was matched or extracted, and its doc_type — enough
    for the UI to show "18 of 27 recognised, 9 extracting".
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    project, member, problem = require_member(session, caller, payload, "projectupload")
    if problem:
        return problem
    problem = _refuse_unless_pm(session, caller, member, project, "projectupload")
    if problem:
        return problem

    period, problem = _resolve_period(session, project, payload)
    if problem:
        return problem

    # 0023. THE PERSON STATES THE REPORTING PERIOD; THE PLATFORM DOES NOT INFER IT.
    #
    # `period` above is the number they chose. `period_end` is that period's ending date, and
    # it is stored so a document whose own date falls outside the period can be reported back
    # to them. It bounds nothing in the analysis: see migration 0023 for why the period cutoff
    # stays derived from the period's own evidence instead.
    #
    # An unparseable or absent date is stored as NULL rather than refused. The upload is the
    # wrong place to argue about a date format, and a NULL simply means the out-of-period check
    # has nothing to measure against and says nothing.
    period_end = _parse_iso_date(payload.get("period_end") or payload.get("periodEnd"))
    previous_end = _previous_period_end(session, project, period)

    entries = payload.get("documents")
    if not isinstance(entries, list) or not entries:
        return err("documents must be a non-empty list")

    decoded: list[dict] = []
    for entry in entries:
        if not isinstance(entry, dict):
            return err("each document must be an object")
        raw, problem = _decode(entry)
        if problem:
            return problem
        decoded.append({
            "raw": raw,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "filename": str(entry.get("filename") or entry.get("name") or "unnamed"),
            "mime_type": str(entry.get("mimeType") or entry.get("mime_type") or ""),
            "doc_type": str(entry.get("docType") or entry.get("doc_type") or "").strip().lower(),
            # 0013. An EXPLICIT claim that this upload replaces an earlier document in this
            # project and period. Never inferred from upload order: two documents of the same
            # type in one period are not necessarily versions of each other (two RFI logs from
            # different weeks are both current), so inferring would silently discard evidence.
            "supersedes": str(entry.get("supersedes")
                              or entry.get("supersedes_document_id") or "").strip() or None,
            # 2026-08-03. Decided HERE, from the filename alone, before anything is extracted.
            # See the job-selection note below for why the order matters.
            "reference": reference_kind(str(entry.get("filename")
                                            or entry.get("name") or "unnamed")),
        })

    # 0013. Validate every supersedes claim BEFORE extracting anything: a bad reference should
    # cost nothing and must refuse by name rather than surfacing later as an integrity error.
    # The condition is stronger than a foreign key could express — the referenced document must
    # exist AND already be part of THIS project and period, because "supersedes" is a statement
    # about this period's evidence, not a pointer into the shared document store.
    claims = [d["supersedes"] for d in decoded if d["supersedes"]]
    if claims:
        held = set(session.scalars(
            select(DocumentUpload.document_id).where(
                DocumentUpload.project_id == project.id,
                DocumentUpload.period == period,
                DocumentUpload.document_id.in_(claims),
            )
        ).all())
        for claim in claims:
            if claim not in held:
                return err(
                    f"cannot supersede {claim}: this project has no such document in period "
                    f"{period}. A document can only supersede one already uploaded to the same "
                    f"project and period."
                )
        for d in decoded:
            if d["supersedes"] and d["supersedes"] == d["sha256"]:
                return err("a document cannot supersede itself")

    # Which hashes do we already hold? This is the cache, and it is a single query.
    hashes = {d["sha256"] for d in decoded}
    existing = {
        d.sha256: d for d in session.scalars(
            select(Document).where(Document.sha256.in_(hashes))
        ).all()
    }

    # Extract only what is genuinely new, and only ONCE per distinct hash within this batch.
    #
    # A REFERENCE DOCUMENT IS NEVER QUEUED. `reference_kind`'s own docstring in jdrive_tree.py
    # says it decides from the filename because "the only content reader on the platform is the
    # analytical extractor and routing a specification through it is precisely what must not
    # happen" — and until 2026-08-03 that is exactly what happened, because filing was decided by
    # `_decide_filing` further down, AFTER extraction had already run. Two consequences, both
    # found by the 2026-08-02 audit: every specification, code and standard was sent to the
    # extraction model, spending a call on a document nothing analyses; and when extraction
    # failed on one — the ordinary outcome for a document the model has no business reading — the
    # upload was reported "failed" and the document was never filed at all, which defeats the
    # whole point of a tree whose bulk is documents that are stored and never analysed.
    #
    # The decision is filename-based and pure, so it is safe to make before any content is read;
    # that is the same property that let `_decide_filing` make it later.
    jobs: list[dict] = []
    queued: set[str] = set()
    for d in decoded:
        if d["reference"] is not None:
            continue
        if d["sha256"] in existing or d["sha256"] in queued:
            continue
        queued.add(d["sha256"])
        jobs.append({"sha256": d["sha256"], "content": d["raw"], "mime_type": d["mime_type"],
                     "filename": d["filename"], "doc_type": d["doc_type"]})

    extractor = _EXTRACTOR_OVERRIDE or build_extractor()
    started = time.monotonic()
    results = extract_many(extractor, jobs) if jobs else []
    elapsed = round(time.monotonic() - started, 3)
    by_hash = {r["sha256"]: r for r in results}

    model_id = getattr(extractor, "model_id", None) or getattr(extractor, "model", "unknown")
    for r in results:
        if not r["ok"]:
            continue
        d = next(x for x in decoded if x["sha256"] == r["sha256"])
        # A BOUNDED RECORD OF THE TABLE, not the table. It names where the table sat, what its
        # columns were taken to mean and how many rows it had, in a few hundred bytes that do
        # not grow with the row count. The rows themselves go to `schedule_activities`, one
        # database row each, which is the only shape a schedule of unknown size can be stored
        # in without a JSON field growing without limit and without being queryable.
        extraction = dict(r["extraction"] or {})
        table = activity_table_from_document(d["raw"], d["mime_type"] or "", d["filename"])
        if table is not None:
            extraction["schedule_table"] = table.descriptor("reader")
        session.add(Document(
            sha256=r["sha256"],
            filename=d["filename"],
            mime_type=d["mime_type"] or None,
            size_bytes=len(d["raw"]),
            content=d["raw"],
            doc_type=r["doc_type"],
            extraction=extraction,
            extraction_model=model_id,
            # 0016. The classifier's own confidence, which the platform used to discard. None
            # when the model's claim was not what decided the type; see extraction_client.
            classification_confidence=r.get("confidence"),
            first_uploaded_by=caller.participant_id,
        ))

    # The reference documents, stored WITHOUT an extraction because none was run for them.
    #
    # `doc_type`, `extraction`, `extraction_model` and `classification_confidence` are all NULL
    # and that is the honest record: nothing read this file. It matters downstream — `is_mapped`
    # is false for a NULL type, so the merge skips it and it cannot reach the analytical inputs,
    # which is the same separation the reference class was built to carry. `_decide_filing`
    # below reads the filename again and files it as reference, so a document arriving here is
    # filed exactly as it would have been, minus the model call that used to precede it.
    seen_ref: set[str] = set()
    for d in decoded:
        if d["reference"] is None or d["sha256"] in existing or d["sha256"] in seen_ref:
            continue
        seen_ref.add(d["sha256"])
        session.add(Document(
            sha256=d["sha256"],
            filename=d["filename"],
            mime_type=d["mime_type"] or None,
            size_bytes=len(d["raw"]),
            content=d["raw"],
            doc_type=None,
            extraction=None,
            extraction_model=None,
            classification_confidence=None,
            first_uploaded_by=caller.participant_id,
        ))
    session.flush()

    stored = {
        d.sha256: d for d in session.scalars(
            select(Document).where(Document.sha256.in_(hashes))
        ).all()
    }

    # Existing upload rows for this period, so a re-upload of the same file is a no-op rather
    # than a second row (the unique index enforces it; this avoids provoking it).
    already = {
        row.document_id for row in session.scalars(
            select(DocumentUpload).where(DocumentUpload.project_id == project.id,
                                         DocumentUpload.period == period)
        ).all()
    }

    files: list[dict] = []
    cached_count = extracted_count = failed_count = filed_count = 0
    for d in decoded:
        doc = stored.get(d["sha256"])
        if doc is None:
            r = by_hash.get(d["sha256"], {})
            failed_count += 1
            files.append({"filename": d["filename"], "status": "failed",
                          "doc_type": None, "was_cached": False,
                          "contributes": False, "error": r.get("error")})
            continue
        was_cached = d["sha256"] in existing
        if d["reference"] is not None:
            # Counted separately: it was neither extracted nor served from an extraction cache.
            filed_count += 1
        elif was_cached:
            cached_count += 1
        else:
            extracted_count += 1
        # 0016. WHERE THIS GOES, decided from the detected type. The PM never chooses a
        # destination; they see the one that was chosen and may move it afterwards.
        filing = _decide_filing(doc.doc_type or "", doc.extraction,
                                d["filename"], doc.classification_confidence)
        if doc.document_id not in already:
            # 0013. A document cannot supersede itself, including via the content cache: if the
            # same bytes are re-uploaded claiming to replace their own row, the claim is
            # dropped rather than stored, because honouring it would exclude the document from
            # its own period and leave the period with nothing.
            supersedes = d["supersedes"] if d["supersedes"] != doc.document_id else None
            session.add(DocumentUpload(project_id=project.id, period=period,
                                       document_id=doc.document_id,
                                       uploaded_by=caller.participant_id,
                                       was_cached=was_cached,
                                       supersedes_document_id=supersedes,
                                       folder_path=filing["folder_path"],
                                       filing_class=filing["filing_class"],
                                       needs_filing_review=filing["needs_filing_review"],
                                       period_end=period_end))
            already.add(doc.document_id)
        mapped = is_mapped(doc.doc_type or "")
        # A FILED DOCUMENT IS NOT A FAILED EXTRACTION, and the note now says which it is.
        # Before this, everything that was not a mapped analytical type carried "contributes
        # nothing to the analysis", so a Revit model, a LEED credit and a specification all
        # read as something that had gone wrong. Most of the Arora tree is documents that are
        # stored and never analysed; that is the expected outcome, not a fault.
        if filing["filing_class"] == CLASS_REFERENCE:
            note = ("filed as reference material for technical review; deliberately kept out "
                    "of the analytical path")
        elif mapped:
            note = None
        else:
            note = "filed and stored; this document type is not one the analysis reads"
        files.append({
            "filename": d["filename"],
            # "filed" is a THIRD outcome and not a flavour of the other two: this document was
            # stored and placed without any extraction being attempted. Reporting it as
            # "extracted" would claim a model call that never happened, and "matched" would
            # claim a cache hit on an extraction that does not exist.
            "status": ("filed" if d["reference"] is not None
                       else ("matched" if was_cached else "extracted")),
            "doc_type": doc.doc_type,
            "was_cached": was_cached,
            # Reported explicitly so the PM can see which documents did not contribute rather
            # than assuming a successful upload meant a contributing one.
            "contributes": mapped,
            # 0016. Where it went, returned on the upload response so the drop animation can
            # name the destination without waiting for anything else.
            "folder_path": filing["folder_path"],
            "filing_class": filing["filing_class"],
            "filing_label": FILING_CLASS_LABELS.get(filing["filing_class"], ""),
            "needs_filing_review": filing["needs_filing_review"],
            "classification_confidence": doc.classification_confidence,
            "note": note,
            # 0023. The document's own date disagrees with the reporting period it was filed
            # to. Reported, never acted on: the document is stored in the period the person
            # stated, because a document produced late can legitimately belong to an earlier
            # period and only they can tell that from a filing mistake. None when the dates
            # agree, or when either date is absent.
            "period_date_mismatch": _out_of_period(
                _parse_iso_date((doc.extraction or {}).get("document_date")),
                period_end, previous_end),
        })

    # 0022. THE DURABLE RECORD OF THIS BATCH, written for every file whether it succeeded or
    # not, and written HERE because it cannot be derived later: a document that failed
    # extraction leaves no row anywhere else, so from storage's point of view it was never
    # offered. The error is stored in the words the refusing code wrote, verbatim.
    batch_id = new_ulid()
    for f, d in zip(files, decoded):
        session.add(UploadAttempt(
            project_id=project.id, period=period, batch_id=batch_id,
            filename=d["filename"], sha256=d["sha256"], size_bytes=len(d["raw"]),
            status=f["status"], doc_type=f.get("doc_type"),
            # The constraint refuses a failure with no reason, so a failure that somehow
            # arrived without one says that, rather than being stored as a silent NULL.
            error=((f.get("error") or "the extractor reported no reason for this failure")
                   if f["status"] == "failed" else None),
            attempted_by=caller.participant_id,
        ))

    # 0014. Project this period's stored extractions into the observation store at the moment
    # the evidence arrives, so the store is current before any compute and the upload-status
    # surface can read the baseline and amendments from it.
    session.flush()
    _persist_observations(session, project, period)
    # 0021. The same moment, for the same reason: the schedule is structured data the store
    # holds from the instant the evidence arrives, not something derived at compute time.
    _persist_schedule_activities(session, project, period)

    audit(session, "documents_uploaded", participant_id=caller.participant_id,
          project_id=project.legacy_id, period=period, files=len(decoded),
          cached=cached_count, extracted=extracted_count, failed=failed_count,
          extraction_model=model_id)

    # THE PROJECT'S OWN EVENT LOG, which is a different store from audit_events and the one C1.4
    # Audit Trail Completeness reads. No current path wrote `signals_extracted`, so C1.4 reported
    # 50% and Amber on every server-created project: it requires project_created AND
    # signals_extracted, and only the first existed. One entry per document that was stored and
    # actually contributes, which is what the name has always meant here and what detail.js's
    # Uploaded Documents table and the slim docCount both count.
    #
    # STAMPED WHEN THE UPLOAD HAPPENED, never at the document's own date. `_append_event` uses the
    # server clock and that is deliberate: `_events_as_of` truncates the log at the period cutoff,
    # so a June report uploaded in August produces an August event that does NOT count toward that
    # period's C1.4. Backdating it to the document date would make it count, and would record an
    # event as having happened when it did not — falsifying the trail to improve the score of the
    # module that measures the trail. The understatement is the honest outcome.
    from .writes import _append_event   # local: writes.py imports facade, which imports this
    logged = [f for f in files if f["status"] != "failed" and f.get("contributes")]
    if logged:
        fresh = dict(project.doc or {})
        for f in logged:
            fresh = _append_event(fresh, "signals_extracted",
                                  docType=f["doc_type"], fileName=f["filename"],
                                  period=period, wasCached=f["was_cached"])
        project.doc = fresh
        project.record_version = (project.record_version or 0) + 1

    session.commit()

    unmapped = [f["filename"] for f in files if f["doc_type"] == UNMAPPED]
    # 0023. The documents whose own date disagrees with the period they were filed to. Every
    # one of them IS stored, in the period that was stated; this is the list the person is
    # shown so a filing mistake is visible instead of silent.
    date_mismatches = [{"filename": f["filename"], "reason": f["period_date_mismatch"]}
                       for f in files if f.get("period_date_mismatch")]
    return {
        "ok": True,
        "project_id": project.legacy_id,
        "period": period,
        # Echoed so the caller can see the period and its ending date the server actually
        # filed to, rather than assuming the one it sent was understood.
        "period_end": period_end.isoformat() if period_end else None,
        "files": files,
        "summary": {
            "total": len(decoded),
            "recognized": cached_count,
            "extracted": extracted_count,
            "failed": failed_count,
            # Stored and placed without an extraction being attempted. Reported so a PM can see
            # that a reference document arriving is a normal outcome, not a silent nothing.
            "filed": filed_count,
            "unmapped": len(unmapped),
            "date_mismatches": len(date_mismatches),
        },
        "date_mismatches": date_mismatches,
        "unmapped_filenames": unmapped,
        "extraction_seconds": elapsed,
        "extraction_model": model_id,
        "server_time": now_iso(),
    }


def a_extractsignals(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    The legacy ONE-DOCUMENT ingest action, adapted onto `a_projectupload`.

    WHY AN ADAPTER AND NOT A SECOND EXTRACTION PATH

    `extractsignals` sat in `DEFERRED_AI_ACTIONS` and returned "Action not implemented in this
    build", so every upload through the project detail page's "Upload a Document" panel
    (`signals.js`, rendered by `ingest.renderScopedIngest`) failed, with its key set. The
    platform meanwhile had a complete, guarded, dispatched upload path in `a_projectupload`,
    used by the workspace period upload and the Files tab.

    Implementing extraction again here would have produced two paths that must agree forever
    about authorisation, the content-hash cache, the malformed-numeric guard, the document risk
    range guard, supersession, filing, observation emission and the project event log. This
    codebase has already paid for that kind of drift more than once. So this reshapes the legacy
    single-document request into the `documents: [...]` request `a_projectupload` accepts, calls
    it, and reshapes the answer back. Every guarantee is inherited rather than restated, and a
    future change to the upload rules cannot apply to one surface and miss the other.

    WHAT THE LEGACY CALLER NEEDS BACK

    `signals.js` reads `docType` and `applied` (see its `processOne`), and passes the whole
    response through `mergeComputed`, which looks for `signalInputs`/`computed`. Everything after
    the `applied` count is wrapped in a non-fatal try/catch there, so the contract that actually
    matters is `ok`, `docType` and `applied`; `signalInputs` is supplied as well so the panel can
    show CPI and SPI rather than a bare field count.
    """
    entry: dict[str, Any] = {
        "filename": payload.get("fileName") or payload.get("filename") or "unnamed",
        "mimeType": payload.get("mimeType") or payload.get("mime_type") or "",
        "docType": payload.get("docType") or payload.get("doc_type") or "",
        "supersedes": payload.get("supersedes") or payload.get("supersedes_document_id") or "",
    }

    # The legacy client sends EITHER `dataBase64` or `text`: `store.js` parses a PDF to plain text
    # with PDF.js and posts that instead of the bytes. `_decode` speaks only base64, so a text
    # submission is encoded here rather than by teaching the shared decoder a second wire format
    # that only this one legacy caller uses.
    #
    # NOTHING IS REFUSED IN THIS FUNCTION BEFORE `a_projectupload` RUNS. An earlier draft returned
    # "needs either dataBase64 or text" up front, which answered an UNAUTHENTICATED caller with a
    # payload critique — the facade's own suite caught it. A body carrying neither simply arrives
    # without `dataBase64`, so `_decode` refuses it with the shared wording, after
    # `resolve_caller` and the PM check have run.
    b64 = payload.get("dataBase64") or payload.get("data_base64")
    text = payload.get("text")
    if b64:
        entry["dataBase64"] = b64
    elif text:
        entry["dataBase64"] = base64.b64encode(str(text).encode("utf-8")).decode("ascii")
        # A text submission has no meaningful browser mime type, and leaving whatever the client
        # claimed would let a PDF-typed text body reach the PDF document block as raw prose.
        entry["mimeType"] = "text/plain"

    upload = dict(payload)
    upload["documents"] = [entry]
    resp = a_projectupload(session, upload, secret, ttl)
    if not resp.get("ok"):
        return resp

    files = resp.get("files") or []
    if not files:
        return err("extractsignals stored nothing for this document")
    first = files[0]
    if first.get("status") == "failed":
        # The per-file reason — the guard that refused and the field it named — is what the
        # uploader's "Extraction failed" dialog shows. Returning ok:True with a failed file
        # would report a refusal as a success with zero fields.
        return err(str(first.get("error") or "extraction failed"))

    # `applied` is the field count the panel prints. Read from the STORED extraction rather than
    # recomputed from the response, so it reports what was actually persisted, and counts only
    # non-null values: a field the model correctly declined to answer was not applied.
    sha = hashlib.sha256(base64.b64decode(entry.get("dataBase64") or "",
                                          validate=True)).hexdigest()
    doc = session.scalars(select(Document).where(Document.sha256 == sha)).first()
    extraction = (doc.extraction if doc is not None else None) or {}
    applied = sorted(k for k, v in extraction.items() if v is not None and v != "")

    # The period's selected signal inputs, by the SAME selection the compute path runs
    # (`_compute_and_store`): observations over the live document set, bounded by the derived
    # cutoff. Nothing is computed and nothing is stored here — the legacy action never ran the
    # analytical layer either, and `projectcompute` remains the only thing that does.
    signal_inputs: dict[str, Any] = {}
    try:
        project = session.scalars(
            select(Project).where(Project.legacy_id == resp["project_id"])
        ).first()
        period_docs = _period_documents(session, project, resp["period"])
        observations: list[dict] = []
        for d in period_docs:
            observations.extend(emit_observations(d))
        signal_inputs = select_signal_inputs(observations, _derive_cutoff(period_docs, None))
    except Exception as exc:  # noqa: BLE001 — display only; the document is already stored
        log.warning("extractsignals could not assemble signalInputs for display: %s", exc)

    return {
        "ok": True,
        "project_id": resp.get("project_id"),
        "period": resp.get("period"),
        "docType": first.get("doc_type"),
        "applied": applied,
        "signalInputs": signal_inputs,
        "contributes": first.get("contributes"),
        "folder_path": first.get("folder_path"),
        "filing_class": first.get("filing_class"),
        "filing_label": first.get("filing_label"),
        "needs_filing_review": first.get("needs_filing_review"),
        "classification_confidence": first.get("classification_confidence"),
        "note": first.get("note"),
        "was_cached": first.get("was_cached"),
        "extraction_model": resp.get("extraction_model"),
        "extraction_seconds": resp.get("extraction_seconds"),
        "server_time": resp.get("server_time"),
    }


def a_projectuploadstatus(session: Session, payload: dict, secret: str,
                          ttl: int) -> dict[str, Any]:
    """Any active member. Which documents are present, and whether the period has been computed."""
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    project, member, problem = require_member(session, caller, payload, "projectuploadstatus")
    if problem:
        return problem
    period, problem = _resolve_period(session, project, payload)
    if problem:
        return problem

    documents = _period_documents(session, project, period)
    report = assembly_report(documents)
    result = _live_result(session, project, period)

    # T3's document viewer needs document_id (to build the content URL), upload time, and
    # whether that upload was a cache hit — none of which `_period_documents` carries, since
    # that helper's shape is fixed by what `assemble_signal_inputs` needs (see its docstring).
    # Queried separately here rather than widening `_period_documents`, which stays the exact
    # shape B7b's determinism guarantees were written against.
    upload_rows = session.execute(
        select(Document.sha256, Document.document_id, DocumentUpload.uploaded_at,
              DocumentUpload.was_cached, Document.filename, Document.doc_type,
              DocumentUpload.supersedes_document_id)
        .join(DocumentUpload, DocumentUpload.document_id == Document.document_id)
        .where(DocumentUpload.project_id == project.id, DocumentUpload.period == period)
    ).all()
    by_sha = {r[0]: (r[1], r[2], r[3]) for r in upload_rows}
    # Which live upload replaced which document, so the reader can follow the chain.
    replaced_by = {r[6]: r[1] for r in upload_rows if r[6]}

    present = []
    for d in documents:
        doc_id, uploaded_at, was_cached = by_sha.get(d["sha256"], (None, None, None))
        present.append({
            "document_id": doc_id,
            "filename": d["filename"], "doc_type": d["doc_type"],
            "contributes": is_mapped(d["doc_type"]),
            "fields": report["fields_by_doc"].get(d["sha256"], []),
            "uploaded_at": uploaded_at.isoformat() if uploaded_at else None,
            "was_cached": was_cached,
        })

    # 0013. SUPERSEDED DOCUMENTS ARE STILL READABLE. `_period_documents` excludes them so they
    # cannot reach computation, which would make them silently vanish from this surface too.
    # They are listed separately instead: a decision recorded against an earlier version must
    # still resolve to the evidence it was actually shown, which is a property the About tab
    # states as reproducibility. `contributes` is false because they no longer feed assembly,
    # and `superseded_by_document_id` names the version that replaced each one.
    superseded_ids = _superseded_document_ids(session, project, period)
    superseded = [
        {"document_id": r[1], "filename": r[4], "doc_type": r[5] or UNMAPPED,
         "contributes": False,
         "uploaded_at": r[2].isoformat() if r[2] else None,
         "was_cached": r[3],
         "superseded_by_document_id": replaced_by.get(r[1])}
        for r in upload_rows if r[1] in superseded_ids
    ]

    have = {d["doc_type"] for d in documents}

    # 0014. THE BASELINE AND ITS AMENDMENTS, BOTH READABLE. The original contract baseline
    # persists as PERMANENT observations (a change order can no longer destroy it), and every
    # executed change order is an amendment layered on it. Read from the observation store,
    # across all periods up to this one, because the baseline is a fact about the project,
    # not about one period's uploads.
    baseline_rows = session.scalars(
        select(Observation).where(
            Observation.project_id == project.id,
            Observation.period <= period,
            Observation.source_doc_type.in_(("contract_value", "change_order")),
        )
    ).all()
    revised_away = {r.revision_of for r in baseline_rows if r.revision_of}
    original: dict[str, Any] = {}
    for want, field in (("contractSum", "baselineContractSum"),
                        ("start", "baselineStart"), ("end", "baselineEnd")):
        cands = [r for r in baseline_rows
                 if r.field == field and r.source_doc_type == "contract_value"
                 and r.document_id not in revised_away]
        if cands:
            first = min(cands, key=lambda r: (r.as_of or date.max, r.document_id))
            original[want] = first.value
    amendments_by_doc: dict[str, dict] = {}
    for r in baseline_rows:
        if r.source_doc_type != "change_order" or r.document_id in revised_away:
            continue
        a = amendments_by_doc.setdefault(r.document_id, {
            "document_id": r.document_id, "period": r.period,
            "as_of": r.as_of.isoformat() if r.as_of else None,
            "state": "executed",
        })
        if r.field == "bac" or r.field == "revisedContractSum":
            a["revisedContractSum"] = r.value
        elif r.field == "baselineEnd":
            a["revisedEnd"] = r.value
    amendments = sorted(amendments_by_doc.values(),
                        key=lambda a: (a["period"], a["as_of"] or "", a["document_id"]))

    # 0022. WHAT WAS ATTEMPTED, INCLUDING WHAT FAILED. Read from `upload_attempts` and not
    # derived from `documents`, because a failed extraction leaves no document row: the files
    # that did not make it are exactly the ones no other query on this surface can see. Newest
    # first, so the most recent account of a filename is the one read first.
    attempt_rows = session.scalars(
        select(UploadAttempt).where(UploadAttempt.project_id == project.id,
                                    UploadAttempt.period == period)
    ).all()
    # ORDERED BY THE ROW ID, NOT ONLY BY THE TIMESTAMP. `attempted_at` comes from the database
    # clock and two attempts a second apart can carry the same value, which would leave "which
    # attempt was the latest" decided by whatever the sort fell back on. The id is a ULID and is
    # monotonic by construction, so it settles the tie by the order the rows were actually
    # written. A retry that succeeded must not be able to lose to the failure it replaced.
    attempts = [
        {"batch_id": a.batch_id, "filename": a.filename, "sha256": a.sha256,
         "status": a.status, "doc_type": a.doc_type, "error": a.error,
         "size_bytes": a.size_bytes,
         "attempted_at": a.attempted_at.isoformat() if a.attempted_at else None}
        for a in sorted(attempt_rows,
                        key=lambda r: (r.attempted_at.isoformat() if r.attempted_at else "",
                                       r.upload_attempt_id),
                        reverse=True)
    ]
    # A filename is OUTSTANDING when its most recent attempt failed. An earlier failure that a
    # later attempt fixed is not outstanding, and both attempts stay in the record: the history
    # of a document is evidence about that document.
    latest_by_name: dict[str, dict] = {}
    for a in attempts:
        latest_by_name.setdefault(a["filename"], a)
    failed_outstanding = [a for a in latest_by_name.values() if a["status"] == "failed"]
    failed_outstanding.sort(key=lambda a: a["filename"])

    audit(session, "project_read", participant_id=caller.participant_id,
          action="projectuploadstatus", project_id=project.legacy_id,
          project_role=member.project_role)
    session.commit()
    return {
        "ok": True,
        "project_id": project.legacy_id,
        "period": period,
        "documents": present,
        # 0022. Every file this period has been offered, and what happened to it. This is the
        # only place a failure is readable after the dialog that first reported it has gone.
        "attempts": attempts,
        "failed": failed_outstanding,
        # The period's schedule, reduced to the rows worth drawing, with the rule that decided
        # and the count of what was left in the store and not drawn. None where this period
        # read no schedule at all.
        "schedule": _schedule_display(session, project, period),
        # Replaced versions, kept readable and kept out of computation. Empty on every period
        # where nothing has been superseded, which is the ordinary case.
        "superseded": superseded,
        # 0014. The original contract baseline and the executed amendments layered on it.
        # `original` survives every change order; `amendments` lists each executed change
        # order's revised figures. Empty objects/lists when no contract or no COs exist.
        "baseline": {"original": original, "amendments": amendments},
        "unmapped": report["unmapped"],
        # Advisory, not a gate: compute never refuses on a missing document type. It reports
        # what is absent so the PM can decide whether the period is complete.
        "expected_missing": sorted(t for t in _EXPECTED_DOC_TYPES if t not in have),
        "computed": result is not None,
        "result_id": result.result_id if result else None,
        "computed_at": result.computed_at.isoformat() if result and result.computed_at else None,
        "server_time": now_iso(),
    }


# The document types a period is normally expected to carry. Advisory only — this is a
# completeness HINT for the PM, never a precondition for compute, because a real project
# routinely lacks one of these in a given month.
_EXPECTED_DOC_TYPES: tuple[str, ...] = (
    "pay_application", "monthly_report", "schedule_update", "contract_value",
)


def a_projectcompute(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    PM only. Runs the analytical layer for a period and stores the result.

    If a live result already exists AND the period's documents have not changed since it was
    stored, the existing result is returned untouched. If the documents have changed (a new
    document was uploaded into the period, one was removed, or a revision replaced one), the
    period is recomputed: the old result is superseded (append-only) and the new one reflects
    the current evidence.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    project, member, problem = require_member(session, caller, payload, "projectcompute")
    if problem:
        return problem
    problem = _refuse_unless_pm(session, caller, member, project, "projectcompute")
    if problem:
        return problem
    period, problem = _resolve_period(session, project, payload)
    if problem:
        return problem

    existing = _live_result(session, project, period)
    if existing is not None:
        stale, stale_reason = _period_is_stale(session, project, period, existing)
        if not stale:
            return {"ok": True, "project_id": project.legacy_id, "period": period,
                    "result_id": existing.result_id, "recomputed": False,
                    "note": "documents unchanged since last computation; result left untouched"}
        new_id = new_ulid()
        existing.superseded_by = new_id
        session.flush()
        outcome = _compute_and_store(session, project, period, result_id=new_id)
        row = outcome["row"]
        audit(session, "period_recomputed", participant_id=caller.participant_id,
              project_id=project.legacy_id, period=period, result_id=row.result_id,
              superseded_result_id=existing.result_id,
              reason=stale_reason,
              simulation_version=row.simulation_version, seed=row.seed,
              period_cutoff=str(row.period_cutoff), documents=len(outcome["documents"]),
              via="projectcompute")
        session.commit()
        return {
            "ok": True,
            "project_id": project.legacy_id,
            "period": period,
            "result_id": row.result_id,
            "recomputed": True,
            "superseded_result_id": existing.result_id,
            "project_status": row.project_status,
            "simulation_version": row.simulation_version,
            "seed": row.seed,
            "period_cutoff": str(row.period_cutoff),
            "documents": len(outcome["documents"]),
            "abstained": outcome["run"].get("abstained"),
            "unported": outcome["run"].get("unported"),
            "reason": stale_reason,
            "server_time": now_iso(),
        }

    outcome = _compute_and_store(session, project, period)
    row = outcome["row"]
    audit(session, "period_computed", participant_id=caller.participant_id,
          project_id=project.legacy_id, period=period, result_id=row.result_id,
          simulation_version=row.simulation_version, seed=row.seed,
          period_cutoff=str(row.period_cutoff), documents=len(outcome["documents"]))
    session.commit()
    return {
        "ok": True,
        "project_id": project.legacy_id,
        "period": period,
        "result_id": row.result_id,
        "recomputed": False,
        "project_status": row.project_status,
        "simulation_version": row.simulation_version,
        "seed": row.seed,
        "period_cutoff": str(row.period_cutoff),
        "documents": len(outcome["documents"]),
        "abstained": outcome["run"].get("abstained"),
        "unported": outcome["run"].get("unported"),
        "server_time": now_iso(),
    }


def a_projectcomputeall(session: Session, payload: dict, secret: str,
                        ttl: int) -> dict[str, Any]:
    """
    PM only, operational accounts only. Generates signals for EVERY period the project holds
    documents for, oldest first.

    WHY THIS EXISTS. Computation is a separate, manual action, and until now it was reachable
    from exactly one control: the Workspace panel's per-period button, which computes period 1
    and nothing else. The project detail upload panel and the Files tab both extract
    successfully and neither offers a compute, which is why a project could read "Awaiting
    analysis" with every one of its documents uploaded and extracted. Nothing was broken; there
    was simply no way to ask.

    PERIODS COMPUTE IN ORDER, AND EACH SEES ONLY ITSELF AND EARLIER PERIODS. This is the
    operation that breaks the byte-identical invariant if done carelessly, and it is held in two
    ways rather than one. The loop runs ascending, so a period is never computed while a later
    one is being written. And the bound is not the loop's to keep: `_earlier_live_results`,
    `_period_history` and `_milestone_history` each select on `period <= the period being
    computed`, so a period computed last would still see only itself and its predecessors. The
    ordering is what makes the results sensible to read; the selection bound is what makes the
    invariant true.

    AN ALREADY-COMPUTED PERIOD IS RECOMPUTED WHEN ITS DOCUMENTS HAVE CHANGED, AND SKIPPED WHEN
    THEY HAVE NOT. Staleness is decided by comparing the stored result's `source_documents`
    (the exact set of document ids and content hashes the result was computed from) against the
    period's current live document set. A match means nothing has changed; any difference means
    a new document was added, one was removed, or a revision replaced one, and the result must
    be rebuilt to reflect the current evidence.

    A CHANGED EARLIER PERIOD INVALIDATES EVERY LATER ONE. The series readers (`_period_history`,
    `_period_snapshots`, `_milestone_history`) take earlier periods' stored results as input, so
    if period 1 is recomputed, every later period's series has changed and must be recomputed
    too. Forward invalidation is tracked by a flag that, once set, forces recomputation of
    every subsequent period regardless of its own document set.

    The recompute is append-only: the old result is superseded and kept readable, and the new
    result gets a new id. When a period is recomputed because its own documents changed, the
    cutoff is re-derived from the new document set. When a period is recomputed only because
    an earlier period changed, the cutoff is preserved from the old result.

    OPERATIONAL ACCOUNTS ONLY, REFUSED HERE AND NOT ONLY IN THE UI. The frozen research package
    depends on WHEN computation happened relative to a participant's judgment; a control that
    computes every period at once is not a thing a participant may do to their own study data.
    `features.RESEARCH_FORBIDDEN_ACTIONS` also carries this action, so a research caller is
    refused at dispatch; this check is what makes the refusal true when it is called directly.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    if caller.participant.account_type == "research":
        audit(session, "compute_all_denied_research", participant_id=caller.participant_id,
              action="projectcomputeall", account_type=caller.participant.account_type)
        session.commit()
        return err(
            "not available for this account: generating signals for every period at once is an "
            "operational feature. In the study, each period is computed on its own."
        )
    project, member, problem = require_member(session, caller, payload, "projectcomputeall")
    if problem:
        return problem
    problem = _refuse_unless_pm(session, caller, member, project, "projectcomputeall")
    if problem:
        return problem

    periods = sorted(session.scalars(
        select(DocumentUpload.period).where(DocumentUpload.project_id == project.id).distinct()
    ).all())
    if not periods:
        return err("this project holds no documents, so there is nothing to compute")

    outcomes: list[dict] = []
    earlier_recomputed = False
    for period in periods:
        existing = _live_result(session, project, period)
        if existing is not None:
            stale, stale_reason = _period_is_stale(session, project, period, existing)
            if not stale and not earlier_recomputed:
                outcomes.append({"period": period, "computed": False, "skipped": True,
                                 "result_id": existing.result_id,
                                 "project_status": existing.project_status,
                                 "note": "documents unchanged since last computation; "
                                         "result left untouched"})
                continue
            recompute_reason = stale_reason if stale else (
                "an earlier period was recomputed, invalidating series inputs")
            new_id = new_ulid()
            existing.superseded_by = new_id
            session.flush()
            outcome = _compute_and_store(session, project, period,
                                         reuse_cutoff_from=existing if not stale else None,
                                         result_id=new_id)
            row = outcome["row"]
            audit(session, "period_recomputed", participant_id=caller.participant_id,
                  project_id=project.legacy_id, period=period, result_id=row.result_id,
                  superseded_result_id=existing.result_id,
                  reason=recompute_reason,
                  simulation_version=row.simulation_version, seed=row.seed,
                  period_cutoff=str(row.period_cutoff), documents=len(outcome["documents"]),
                  via="projectcomputeall")
            outcomes.append({"period": period, "computed": True, "skipped": False,
                             "recomputed": True,
                             "result_id": row.result_id,
                             "superseded_result_id": existing.result_id,
                             "project_status": row.project_status,
                             "period_cutoff": str(row.period_cutoff),
                             "documents": len(outcome["documents"]),
                             "abstained": outcome["run"].get("abstained"),
                             "reason": recompute_reason})
            earlier_recomputed = True
            continue
        outcome = _compute_and_store(session, project, period)
        row = outcome["row"]
        audit(session, "period_computed", participant_id=caller.participant_id,
              project_id=project.legacy_id, period=period, result_id=row.result_id,
              simulation_version=row.simulation_version, seed=row.seed,
              period_cutoff=str(row.period_cutoff), documents=len(outcome["documents"]),
              via="projectcomputeall")
        outcomes.append({"period": period, "computed": True, "skipped": False,
                         "result_id": row.result_id,
                         "project_status": row.project_status,
                         "period_cutoff": str(row.period_cutoff),
                         "documents": len(outcome["documents"]),
                         "abstained": outcome["run"].get("abstained")})
        earlier_recomputed = True

    audit(session, "project_computed_all", participant_id=caller.participant_id,
          project_id=project.legacy_id, periods=len(periods),
          computed=sum(1 for o in outcomes if o["computed"]),
          skipped=sum(1 for o in outcomes if o["skipped"]))
    session.commit()
    return {
        "ok": True,
        "project_id": project.legacy_id,
        "periods": periods,
        "results": outcomes,
        "computed": sum(1 for o in outcomes if o["computed"]),
        "skipped": sum(1 for o in outcomes if o["skipped"]),
        "server_time": now_iso(),
    }


def a_projectresults(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Any active member. Returns the stored row. READS ONLY — never computes.

    The recommendation package is withheld until this project's PM has locked the period's
    preliminary judgment, decided by B8's `recommendation_visible`. That predicate is imported,
    not reimplemented, and this is the only place a package can enter this module's output.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    project, member, problem = require_member(session, caller, payload, "projectresults")
    if problem:
        return problem
    period, problem = _resolve_period(session, project, payload)
    if problem:
        return problem

    # An explicit result_id lets a decision resolve the exact row it referenced, including a
    # superseded one. Scoped to this project so it cannot be used to read across projects.
    wanted = str(payload.get("result_id") or "").strip()
    if wanted:
        row = session.scalars(
            select(ComputedResult).where(ComputedResult.result_id == wanted,
                                         ComputedResult.project_id == project.id)
        ).first()
    else:
        row = _live_result(session, project, period)

    if row is None:
        return err(f"no computed result for period {period}; run projectcompute first")

    _assignment, decision, package = project_decision_state(session, project)
    # THE REVEAL GATE APPLIES TO THE RESEARCH PROTOCOL ONLY.
    #
    # `recommendation_visible` is false until a participant's preliminary judgment is locked,
    # and a `Decision` row exists only inside the instrument. Applied to an ordinary
    # operational project the predicate is false forever, so the scored courses of action were
    # redacted on every read and a project manager could never see them on their own project.
    # There is no judgment to protect there and no participant to blind.
    #
    # `reveal_gate_applies` is the one place that decides, and it is NOT the presence of a
    # decision row: that exists only inside the protocol and only once a participant is
    # assigned, which is what made the predicate false forever out here. It covers both a
    # study project (every member, observers included) and a study participant (wherever they
    # are reading), so the gate lifts for exactly one case: an operational account on a
    # project no scenario is built on. Inside the protocol nothing changes at all.
    gated = reveal_gate_applies(session, project, caller)
    visible = (recommendation_visible(decision) if gated else True)

    audit(session, "project_read", participant_id=caller.participant_id,
          action="projectresults", project_id=project.legacy_id,
          project_role=member.project_role, result_id=row.result_id,
          reveal_gated=gated,
          recommendation_visible=visible)
    session.commit()
    return {
        "ok": True,
        "project_id": project.legacy_id,
        "result": _result_view(row, include_recommendation=visible, package=package),
        "server_time": now_iso(),
    }


def a_adminrecompute(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    ResearchAdmin only, and a stated reason is mandatory.

    Writes a NEW row and sets `superseded_by` on the old one. Never edits in place. If the old
    row is referenced by a SUBMITTED decision it is still superseded — that is permitted — but
    nothing about it changes, which is the distinction the whole append-only design turns on.
    """
    from .research_membership import _require_admin

    caller, problem = _require_admin(session, payload, secret, "adminrecompute")
    if problem:
        return problem

    reason = str(payload.get("reason") or "").strip()
    if not reason:
        return err("reason is required: a recompute without a stated reason is not auditable")

    legacy_id = str(payload.get("id") or payload.get("project_id") or "").strip()
    if not legacy_id:
        return err("id is required")
    project = session.scalars(
        select(Project).where(Project.legacy_id == legacy_id)
    ).first()
    if project is None:
        return err(f"Project not found: {legacy_id}")

    period, problem = _resolve_period(session, project, payload)
    if problem:
        return problem

    old = _live_result(session, project, period)
    if old is None:
        return err(f"no computed result to recompute for period {period}")

    # Mint the new id first, then mark the old row superseded, and only then insert. See the
    # note in `_compute_and_store`: the partial unique index allows exactly one live row per
    # (project, period), so the outgoing row must stop being live before the incoming one
    # starts. Setting superseded_by is also the ONE update the database permits on a row that
    # a submitted decision references.
    new_id = new_ulid()
    old.superseded_by = new_id
    session.flush()

    # The superseded row keeps its cutoff so the new row is comparable to it. Deriving a fresh
    # cutoff would change C1.2 Data Timeliness for reasons unrelated to the recompute.
    outcome = _compute_and_store(session, project, period, reuse_cutoff_from=old,
                                 result_id=new_id)
    new = outcome["row"]

    referencing = session.scalars(
        select(Decision).where(Decision.result_id == old.result_id)
    ).all()
    audit(session, "result_recomputed", participant_id=caller.participant_id,
          project_id=project.legacy_id, period=period, reason=reason,
          superseded_result_id=old.result_id, new_result_id=new.result_id,
          referencing_decisions=len(referencing))
    session.commit()
    return {
        "ok": True,
        "project_id": project.legacy_id,
        "period": period,
        "recomputed": True,
        "reason": reason,
        "superseded_result_id": old.result_id,
        "result_id": new.result_id,
        "referencing_decisions": len(referencing),
        "note": "the superseded row remains readable; a decision referencing it still resolves",
        "server_time": now_iso(),
    }


DOCUMENT_ACTIONS: dict[str, Callable[[Session, dict, str, int], dict]] = {
    "projectupload": a_projectupload,
    # The legacy one-document ingest, adapted onto projectupload. See a_extractsignals for why
    # it is an adapter and not a second extraction path.
    "extractsignals": a_extractsignals,
    "projectuploadstatus": a_projectuploadstatus,
    "projectcompute": a_projectcompute,
    # Part 5. Every period the project holds documents for, computed in order, oldest first.
    "projectcomputeall": a_projectcomputeall,
    "projectresults": a_projectresults,
    "adminrecompute": a_adminrecompute,
}
