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

import datetime as _dt

import base64
import binascii
import json
import hashlib
import logging
import re
import time
from datetime import date, datetime, timezone
from typing import Any, Callable

from sqlalchemy import func, select, update as sa_update
from sqlalchemy.orm import Session

from .extraction_client import build_extractor, extract_many, extraction_contract_fingerprint
from .extraction_fields import UNMAPPED, is_mapped
from .extraction_merge import (
    assembly_report, document_as_of, emit_observations, select_signal_inputs,
)
from .field_registry import IDENTITY_FIELDS
from .jdrive_tree import (
    CLASS_ANALYSED, CLASS_FILED, CLASS_REFERENCE, FILING_CLASS_LABELS, needs_review,
    reference_kind, resolve_destination,
)
from .facade import err, now_iso
from .models import Project
from .project_data import apply_to_signal_inputs
from .simulation.models_cat10 import B4_7_ANY_METHOD_CLASS
from .simulation.fusion import governed_status_semantics
from .simulation.qualification import qualification_for_stored_result
from .research_identity import audit, resolve_caller
from .research_membership import (
    ROLE_PM,
    project_decision_state,
    recommendation_visible,
    reveal_gate_applies,
    require_member,
)
from .research_models import (
    AuditEvent,
    ComputedResult, Decision, Document, DocumentUpload, Observation, ProjectNotice,
    ProjectRisk,
    ScheduleActivity,
    UploadAttempt, new_ulid,
)
from .document_evidence import document_evidence
from .evm_consistency import consistency_findings
from .decision_brief import compose_decision_brief
from .recommendation_basis import recommendation_basis
from . import spec_projection
from .risk_exposure import register_exposure
from .risk_register import risk_rows_from_document
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
        # THE CALENDAR PATH. No number was stated, so derive one from the ending date if one
        # was picked. Same function the picker previewed with, so the period a person was shown
        # before uploading is the period the upload actually writes to. An unparseable date is
        # not silently treated as "no date": it falls through to 1 exactly as an absent date
        # does, and `period_end` is stored as NULL, which is what the old behaviour was.
        chosen = _parse_iso_date(payload.get("period_end") or payload.get("periodEnd"))
        if chosen is not None:
            return period_for_end_date(session, project, chosen)["period"], None
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


def _stated_period_ends(session: Session, project: Project) -> list[tuple[int, date]]:
    """
    Every period this project holds a STATED ending date for, ascending by period.

    One date per period: the latest stated for it, because the same period can be uploaded to
    more than once and the ending date is restated each time. Periods uploaded without a date
    are absent from this list entirely rather than carrying a guessed boundary.
    """
    rows = session.execute(
        select(DocumentUpload.period, func.max(DocumentUpload.period_end))
        .where(DocumentUpload.project_id == project.id,
               DocumentUpload.period_end.is_not(None))
        .group_by(DocumentUpload.period)
        .order_by(DocumentUpload.period)
    ).all()
    return [(int(p), e) for p, e in rows if e is not None]


def _highest_period(session: Session, project: Project) -> int:
    """The largest period number this project holds any document for, or 0 when it holds none."""
    return int(session.scalar(
        select(func.max(DocumentUpload.period)).where(DocumentUpload.project_id == project.id)
    ) or 0)


def period_for_end_date(session: Session, project: Project, chosen: date) -> dict[str, Any]:
    """
    Which reporting period a chosen ending DATE names, and whether that period already exists.

    THE CALENDAR IS THE CONTROL. A person picks the date the reporting period ends; the number
    is derived here rather than typed, because the number is bookkeeping and the date is the
    thing they actually know. One rule, stated once, used by both callers: the preview the
    picker shows before an upload, and `_resolve_period` at the upload itself. Two
    implementations of this would drift, and a preview that disagrees with what the upload does
    is worse than no preview.

    THE RULE. The period is the earliest one whose stated ending date falls on or after the
    chosen date; if the chosen date is later than every stated ending date, it opens the next
    period. An exact match on a stated ending date is the same rule's first case and is called
    out separately only so the caller can say "this period already exists" rather than implying
    a new one.

    Returns `{period, period_end, existing, basis}` where `basis` names, in words, which arm
    decided -- the picker prints it, so a derived number is never unexplained.
    """
    ends = _stated_period_ends(session, project)

    for period, end in ends:
        if end == chosen:
            return {"period": period, "period_end": chosen, "existing": True,
                    "basis": f"period {period} is the period stated as ending {end.isoformat()}"}

    covering = [(p, e) for p, e in ends if e >= chosen]
    if covering:
        period, end = min(covering, key=lambda t: (t[1], t[0]))
        return {"period": period, "period_end": end, "existing": True,
                "basis": (f"period {period} ends {end.isoformat()}, the first period ending on "
                          f"or after {chosen.isoformat()}")}

    nxt = _highest_period(session, project) + 1
    if ends:
        latest = max(e for _p, e in ends)
        basis = (f"period {nxt} is new: {chosen.isoformat()} is later than "
                 f"{latest.isoformat()}, the last period's stated ending date")
    else:
        basis = (f"period {nxt} is new: this project has no period with a stated ending date yet")
    return {"period": nxt, "period_end": chosen, "existing": False, "basis": basis}


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


def _archived_document_ids(session: Session, project: Project, period: int) -> set[str]:
    """
    The documents WITHDRAWN from this project's period by the document control.

    Scoped to (project, period) for the same reason `_superseded_document_ids` is: `documents`
    is shared content-addressed storage, so the same bytes may be live evidence in another
    project or in another period of this one. The mark is read here and nowhere else decides
    membership of the live set.
    """
    rows = session.scalars(
        select(DocumentUpload.document_id).where(
            DocumentUpload.project_id == project.id,
            DocumentUpload.period == period,
            DocumentUpload.archived_at.is_not(None),
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
    # 0027. ARCHIVED DOCUMENTS ARE EXCLUDED HERE, beside superseded ones and for the same
    # written reason: `assemble_signal_inputs` is pure and knows nothing of projects or
    # periods, and archival is a per-(project, period) fact. Excluding at this one seam is what
    # makes the two rules of the document control structural rather than swept for — no module
    # can hold a value that came only from an archived document, because the observations were
    # never emitted; and no other document's fields are touched, because nothing else is
    # filtered. `_identity_observations_before` reuses this helper per earlier period, so an
    # archived contract stops being carried forward too. The rows stay readable through
    # `a_projectuploadstatus`, exactly as superseded rows do.
    archived = _archived_document_ids(session, project, period)
    rows = session.execute(
        select(Document, DocumentUpload.supersedes_document_id)
        .join(DocumentUpload, DocumentUpload.document_id == Document.document_id)
        .where(DocumentUpload.project_id == project.id, DocumentUpload.period == period)
    ).all()
    seen: set[str] = set()
    out: list[dict] = []
    for d, supersedes in rows:
        if d.document_id in superseded or d.document_id in archived:
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


def _identity_observations_before(session: Session, project: Project,
                                  period: int) -> list[dict]:
    """
    The IDENTITY-field observations this project's EARLIER periods carry.

    RUN 45. `_period_documents` scopes retrieval to the upload period, which is right for a fact
    about one reporting period and wrong for a fact about the project: a contract uploaded at
    period 1 was invisible from period 2 on, and the contract sum fell through to whatever
    weaker writer the later period happened to hold. This supplies what the later period is
    entitled to see, and `select_signal_inputs` decides what to do with it.

    WHY IT REUSES `_period_documents` PER EARLIER PERIOD rather than widening its query: that
    helper already excludes documents a later upload superseded, deduplicates by content hash,
    and is the shape every determinism guarantee since B7b was written against. Supersession is
    a per-(project, period) fact, so asking it per period is what keeps a revision in period 2
    from resurrecting the document it replaced.

    ONLY EARLIER PERIODS. The period being computed is never re-read here — its own documents
    reach selection by the ordinary route, and reading them twice would put two copies of every
    observation into one group. Filtering to IDENTITY_FIELDS happens in `select_signal_inputs`,
    which is the one place the classification is applied, but it is applied here too so a period
    field is never even carried into the pure layer.
    """
    earlier = session.scalars(
        select(DocumentUpload.period)
        .where(DocumentUpload.project_id == project.id, DocumentUpload.period < period)
        .distinct()
    ).all()
    carried: list[dict] = []
    for p in sorted({int(x) for x in earlier if x is not None}):
        for d in _period_documents(session, project, p):
            carried.extend(o for o in emit_observations(d)
                           if str(o.get("field")) in IDENTITY_FIELDS)
    return carried


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


def _persist_observations(session: Session, project: Project, period: int,
                          refusals: dict[str, str] | None = None,
                          stored_fields: dict[str, list[str]] | None = None) -> int:
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

    RUN 74. `refusals` and `stored_fields`, when passed, are FILLED IN, keyed by document_id:
    `refusals` with the verbatim reason a document projected nothing, `stored_fields` with the
    field names that actually reached the observation store for that document.

    Before this run the `except` below was a bare `except Exception: continue`. EVERY refusal —
    an out-of-range figure replayed from the content cache without re-validation, a field with
    no kind declared in field_registry, anything at all — was swallowed here, the document
    contributed no observation, and the upload still reported it as extracted and contributing.
    That is the silent-drop path: a failure indistinguishable from a success. The exception is
    still caught, because one refusing document must not sink the other twenty-six, but the
    reason is now carried out to the caller instead of discarded.
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
        except Exception as exc:  # noqa: BLE001 — one document must not sink the batch
            log.warning("observation projection refused for %s (%s): %s",
                        d.filename, d.document_id, exc)
            if refusals is not None:
                refusals[d.document_id] = str(exc)
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
        if stored_fields is not None:
            seen = stored_fields.setdefault(d.document_id, [])
            for o in emitted:
                if o["field"] not in seen:
                    seen.append(o["field"])
    return inserted


def _period_risks(session: Session, project: Project, period: int) -> list[dict]:
    """
    This period's risks, as dicts, for the card and for the exposure input.

    BOUNDED BY THE PERIOD BEING ASKED ABOUT, exactly as the schedule readers are: rows are
    selected on their own period, so a later period's register can never change what an earlier
    period reports. That bound is what makes recomputing an earlier period reproduce it.
    """
    rows = session.scalars(
        select(ProjectRisk)
        .where(ProjectRisk.project_id == project.id, ProjectRisk.period == period)
        .order_by(ProjectRisk.document_id, ProjectRisk.project_risk_id)
    ).all()
    return [{
        "risk_key": r.risk_key, "keyed_by_position": r.keyed_by_position,
        "description": r.description, "category": r.category,
        "probability": r.probability, "probability_band": r.probability_band,
        "cost_impact": r.cost_impact, "time_impact_days": r.time_impact_days,
        "score": r.score, "owner": r.owner, "response_strategy": r.response_strategy,
        "mitigation_status": r.mitigation_status, "residual_position": r.residual_position,
        "is_open": r.is_open, "unparsed": r.unparsed,
        "usable_for_exposure": r.usable_for_exposure,
    } for r in rows]


def _period_notices(session: Session, project: Project, period: int) -> list[dict]:
    """This period's served notices, as dicts. Same period bound, same reason."""
    rows = session.scalars(
        select(ProjectNotice)
        .where(ProjectNotice.project_id == project.id, ProjectNotice.period == period)
        .order_by(ProjectNotice.project_notice_id)
    ).all()
    return [{
        "filename": n.filename, "served_by": n.served_by, "served_on": n.served_on,
        "claim": n.claim,
        "date_served": n.date_served.isoformat() if n.date_served else None,
        "date_served_refusal": n.date_served_refusal,
        "contract_form": n.contract_form, "notice_kind": n.notice_kind,
        "references_text": n.references_text,
        "deadline_date": n.deadline_date.isoformat() if n.deadline_date else None,
        "deadline_days": n.deadline_days, "deadline_kind": n.deadline_kind,
        "deadline_citation": n.deadline_citation, "deadline_basis": n.deadline_basis,
        "second_step": n.second_step,
    } for n in rows]


def _persist_project_notices(session: Session, project: Project, period: int) -> int:
    """
    0025. Project this period's notices into the notice ledger, deadline derived.

    Same rules as the other two stores: every upload in the period is projected, rows are keyed
    so re-deriving inserts only what is missing, nothing is updated in place, and a period's
    notices are never rewritten by a later period.

    THE DEADLINE IS DERIVED HERE, IN CODE, from the form the DOCUMENT named. The model is asked
    what the notice says; it is never asked when the deadline is, because a model-stated deadline
    is a date with no rule behind it. `contract_notices.deadline_for` applies the form's own
    published period and says plainly when it cannot.

    THE DATE THAT STARTS THE CLOCK USES THE REFUSING PARSER. `_parse_as_of` accepts strict ISO
    only and returns None on anything else with no reason recorded, which is tolerable for an
    as-of and not for a date a deadline is measured from. `parse_schedule_date` refuses loudly,
    never infers a year, and its refusal is stored.
    """
    from .contract_notices import deadline_for, identify_form, identify_notice_type, second_step_for
    from .schedule_dates import DateRefusal, parse_schedule_date

    rows = session.execute(
        select(Document, DocumentUpload.supersedes_document_id)
        .join(DocumentUpload, DocumentUpload.document_id == Document.document_id)
        .where(DocumentUpload.project_id == project.id, DocumentUpload.period == period)
    ).all()
    existing = {
        r[0] for r in session.execute(
            select(ProjectNotice.document_id)
            .where(ProjectNotice.project_id == project.id, ProjectNotice.period == period)
        ).all()
    }
    inserted = 0
    for d, _supersedes in rows:
        if (d.doc_type or "") != "correspondence_notice" or d.document_id in existing:
            continue
        ex = d.extraction if isinstance(d.extraction, dict) else {}
        existing.add(d.document_id)

        raw_served = ex.get("notice_date_served") or ex.get("document_date")
        parsed = parse_schedule_date(raw_served)
        served = getattr(parsed, "value", None)
        refusal = parsed.reason if isinstance(parsed, DateRefusal) else None

        # The form and the kind come from what the document SAID, preferring the model's own
        # reading of the prose and falling back to a phrase match over the same text. Neither
        # consults a project default, because this platform holds none and inventing one would
        # put a confident deadline on a notice from a regime nobody named.
        stated_form = str(ex.get("notice_contract_form") or "")
        form = identify_form(stated_form) or identify_form(
            " ".join(str(ex.get(k) or "") for k in ("notice_kind", "notice_claim",
                                                    "notice_references")))
        kind = identify_notice_type(
            " ".join(str(ex.get(k) or "") for k in ("notice_kind", "notice_claim")))

        derived = deadline_for(form, kind, served)
        step = second_step_for(form, kind, served)

        session.add(ProjectNotice(
            project_id=project.id, period=period, document_id=d.document_id,
            filename=d.filename,
            served_by=_text_or_none(ex.get("notice_served_by")),
            served_on=_text_or_none(ex.get("notice_served_on")),
            claim=_text_or_none(ex.get("notice_claim")),
            date_served=served,
            date_served_raw=_text_or_none(raw_served),
            date_served_refusal=refusal,
            contract_form=form, notice_kind=kind,
            references_text=_text_or_none(ex.get("notice_references")),
            deadline_date=(date.fromisoformat(derived["date"]) if derived.get("date") else None),
            deadline_days=derived.get("days"),
            deadline_kind=derived.get("kind"),
            deadline_citation=derived.get("citation"),
            deadline_basis=derived.get("basis") or "",
            second_step=step,
            as_of=document_as_of(d.doc_type or UNMAPPED, ex),
            source_doc_type=d.doc_type or UNMAPPED,
        ))
        inserted += 1
    return inserted


def _text_or_none(value: Any) -> str | None:
    """A trimmed string, or None where the value says nothing."""
    cleaned = " ".join(str(value if value is not None else "").split()).strip()
    return cleaned or None


def _persist_project_risks(session: Session, project: Project, period: int) -> int:
    """
    0024. Project this period's stored risk registers into the risk store.

    The same shape as `_persist_observations` and `_persist_schedule_activities`, for the same
    reasons: every upload in the period is projected (superseded ones included, because storage
    retains and selection excludes), rows are keyed by (project, period, document, risk) so
    re-deriving inserts only what is missing, and nothing is ever updated in place. A document's
    register is content-addressed and immutable, so the same document always projects the same
    rows, and recomputing an earlier period after later ones exist reproduces it exactly.

    A ROW THAT WOULD NOT PARSE IS STILL STORED, with its refusals and `usable_for_exposure`
    false. A register of two hundred risks that yielded ninety usable probabilities has to be
    able to say which hundred and ten refused and why, and a dropped row cannot.

    Returns the number of rows inserted.
    """
    rows = session.execute(
        select(Document, DocumentUpload.supersedes_document_id)
        .join(DocumentUpload, DocumentUpload.document_id == Document.document_id)
        .where(DocumentUpload.project_id == project.id, DocumentUpload.period == period)
    ).all()
    existing = {
        (r[0], r[1]) for r in session.execute(
            select(ProjectRisk.document_id, ProjectRisk.risk_key)
            .where(ProjectRisk.project_id == project.id, ProjectRisk.period == period)
        ).all()
    }
    inserted = 0
    for d, _supersedes in rows:
        ex = d.extraction if isinstance(d.extraction, dict) else {}
        # THE READER TAKES THE ROWS, from the document's own stored bytes. Twenty risks and five
        # hundred cost the same, and no row can be silently mistyped on the way. There is
        # deliberately NO model-returned fallback here: a register was never asked for as a
        # JSON field, and adding one would reintroduce exactly the unbounded-output failure this
        # treatment exists to avoid. A register in a PDF yields no rows and says so.
        risks = risk_rows_from_document(d.content or b"", d.mime_type or "", d.filename or "")
        if not risks:
            continue
        doc_type = d.doc_type or UNMAPPED
        as_of = document_as_of(doc_type, ex)
        for r in risks:
            key = (d.document_id, r["risk_key"])
            if key in existing:
                continue
            existing.add(key)
            session.add(ProjectRisk(
                project_id=project.id, period=period, document_id=d.document_id,
                risk_key=r["risk_key"], keyed_by_position=bool(r["keyed_by_position"]),
                description=r["description"], category=r["category"],
                probability=r["probability"], probability_band=r["probability_band"],
                probability_raw=r["probability_raw"], cost_impact=r["cost_impact"],
                time_impact_days=r["time_impact_days"], score=r["score"], owner=r["owner"],
                response_strategy=r["response_strategy"],
                mitigation_status=r["mitigation_status"],
                residual_position=r["residual_position"], is_open=r["is_open"],
                unparsed=r["unparsed"],
                usable_for_exposure=bool(r["usable_for_exposure"]),
                as_of=as_of, source_doc_type=doc_type,
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


def _milestone_forecast_history(snapshots: list[dict]) -> dict | None:
    """
    RUN 28. `milestoneForecastHistory`: the structure the canonical Milestone Trend Analysis is
    defined on, assembled from the schedule snapshots this platform already stores.

    WHY THIS EXISTS. The supplied Run-28 contract measures milestone variance against the
    COMMITTED BASELINE DATE -- MV = ForecastDate - BaselineDate -- and separately measures the
    drift between successive forecasts. The v10 module computed only the drift, because the
    baseline date was never assembled into anything a module could read. It IS in the corpus:
    `schedule_activities.py` extracts each activity's baseline finish and the schedule store
    keeps it per period, so this is a wiring gap rather than an absent fact, and closing it is
    exactly the supply path Run 28 exists to build.

    WHAT IS AND IS NOT INVENTED. The original commitment is the baseline finish recorded in the
    EARLIEST period the milestone appears in, and the current approved baseline is the one
    recorded in the LATEST. Where an activity carries no parseable baseline finish it is left
    out entirely rather than given a substitute, because a variance measured against a date
    nobody committed to is the fabrication this run is forbidden to make. Dates become day
    numbers on a fixed epoch so the arithmetic is in days; nothing about a project reaches the
    epoch, and no clock is read.

    Fewer than two forecasts for every milestone leaves the structure absent and the module
    abstains on its own guard, which is what the contract requires of a trend claim.
    """
    epoch = _dt.date(2000, 1, 1)

    def day(value) -> float | None:
        text = str(value or "")[:10]
        try:
            return float((_dt.date.fromisoformat(text) - epoch).days)
        except (TypeError, ValueError):
            return None

    baselines: dict[str, list[tuple[int, float]]] = {}
    forecasts: dict[str, list[tuple[int, float]]] = {}
    for snap in snapshots:
        p = int(snap.get("period") or 0)
        for m in snap.get("milestones") or []:
            key = str(m.get("name") or "")
            if not key:
                continue
            b = day(m.get("baseline_finish"))
            f = day(m.get("forecast"))
            if b is not None:
                baselines.setdefault(key, []).append((p, b))
            if f is not None:
                forecasts.setdefault(key, []).append((p, f))

    rows = []
    for key in sorted(set(baselines) & set(forecasts)):
        series = sorted(forecasts[key])
        if len(series) < 2:
            continue
        committed = sorted(baselines[key])
        rows.append({
            "milestone_id": key,
            "original_baseline_day": committed[0][1],
            "approved_baseline_day": committed[-1][1],
            "forecasts": [{"report_index": p, "forecast_day": d} for p, d in series],
        })
    if not rows:
        return None
    return {"schedule_version": f"schedule store, periods "
                               f"{snapshots[0].get('period')} to {snapshots[-1].get('period')}",
            "milestones": rows}


def _computed_periods(session: Session, project: Project) -> list[int]:
    """
    Every period of this project that HOLDS A LIVE COMPUTED RESULT, ascending.

    RUN 48, RULING 1. Read from the result table itself, never inferred from the document
    table and never generated as a range. A period with documents and no computed result does
    not appear here, because it has not been computed; a superseded result does not appear
    here, because `superseded_by` is not null and the row is no longer the live one. The list
    is therefore whatever the database holds -- it may have gaps, it may start above 1, and it
    is not bounded by any assumed maximum. A project may run to sixty periods.

    RUN 75, THE OWNER'S RULING: A ROW EXISTING IS NOT THE SAME AS A RESULT EXISTING.

    Run 48's rule was "the latest period for which computed results exist", and it was read as
    "a live row is present". It is too weak. The owner uploaded 27 documents to period 1 of one
    project, computed it to an Amber status over 8 modules, and every surface showed nothing:
    a live row also stood for period 2, which had never held a document, carrying no status and
    no module results. The page opened on the latest period holding a row, found nothing in it,
    and drew nothing -- while a complete period 1 sat one row below.

    So the predicate is now what the caller actually needs: the row must HOLD A RESULT. That is
    `module_results` being non-empty, which is the same measure the owner counted by and the one
    every surface reads -- the ledger, the brief, the charts and the category rollup all resolve
    through module results, and a row with none of them has nothing any of them can show.
    `project_status` is deliberately NOT part of the test: a period whose modules all abstained
    legitimately carries no rolled-up status and still has abstention reasons to show.

    This is the second half of the fix and it is the half that does not depend on the first.
    Compute no longer writes such a row (see `_period_holds_evidence`), but this function is
    what makes the page robust to one arriving by ANY other path -- a hand-written row, a
    partial restore, a migration -- which is the failure that cost the owner several runs.
    """
    rows = session.execute(
        select(ComputedResult.period, ComputedResult.module_results).where(
            ComputedResult.project_id == project.id,
            ComputedResult.superseded_by.is_(None),
        ).order_by(ComputedResult.period)
    ).all()
    return sorted({int(p) for p, modules in rows if p is not None and (modules or [])})


def _withdraw_live_result(session: Session, existing: ComputedResult) -> str:
    """
    Mark a live result superseded WITHOUT writing a replacement, and return the id used.

    RUN 75. A period whose documents have all been withdrawn has no evidence, and a result
    derived from no evidence is not a result. The row cannot be edited and must not be deleted
    -- `computed_results` is append-only and a submitted decision that references this row must
    still resolve years from now -- so it is superseded, which migration 0009 permits on a
    referenced row and nothing else does.

    `superseded_by` carries a FRESH IDENTIFIER THAT NO ROW BEARS, because nothing replaced this
    result: its evidence was withdrawn. That is not new machinery; it is exactly the seam
    `writes.py`'s signals reset already uses and states, at :417-421. Every surface filters on
    `superseded_by IS NULL`, so this one write moves all of them at once and the period stops
    being offered as computed.
    """
    marker = new_ulid()
    existing.superseded_by = marker
    session.flush()
    return marker


def _period_holds_evidence(session: Session, project: Project, period: int) -> bool:
    """
    Does this period hold any document that computation would actually read?

    RUN 75, THE OWNER'S RULING: "A period with no documents must not produce a computed row."

    THE LIVE SET, NOT THE UPLOAD TABLE. `_period_documents` is the one function computation
    itself consumes, and it already excludes superseded and ARCHIVED documents. Asking it -- and
    not `DocumentUpload` -- is what makes one predicate cover both directions of the same shape:
    a period that never held a document, and a period whose documents have since been withdrawn
    through the document control. Both are periods with no evidence, and neither may stand as a
    computed result.
    """
    return bool(_period_documents(session, project, period))


def _latest_computed_period(session: Session, project: Project) -> int | None:
    """
    The latest period for which a computed result exists, or None when none does.

    DERIVED, NOT ASSUMED. It is the maximum of `_computed_periods`, which is read out of the
    stored rows. It is NOT `_highest_period` (that is the highest period holding a DOCUMENT,
    which may never have been computed), it is not a count, and it makes no contiguity
    assumption: a project computed at 1 and 4 with 2 and 3 absent returns 4.

    None is the honest answer for a project that has never been computed. The caller renders
    its existing empty state; it does not substitute 1.
    """
    periods = _computed_periods(session, project)
    return periods[-1] if periods else None


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

    # RUN 78. A SECOND STALENESS CONDITION, and it is why Run 67's fix never reached a
    # deployment that had already computed.
    #
    # Comparing document sets answers "have the inputs changed" and CANNOT answer "has what
    # this platform derives from those inputs changed". Run 67 began writing the period's
    # Category-9 assessment onto `signal_inputs`; a result computed before that code shipped
    # carries the same documents it always did, so it was NOT stale, so
    # `projectcomputeall` SKIPPED it, so the key never appeared -- and every module behind the
    # qualification boundary went on refusing with "carries no Category-9 assessment", which is
    # exactly what the boundary produces when the key is absent (measured: 16 of 16 gated
    # modules in service refuse on an otherwise identical signal_inputs with the key removed,
    # and 0 of 16 with it present).
    #
    # NARROW ON PURPOSE. This does not compare code versions or hash the derivation -- either
    # would recompute every period on every deploy. It asks one question with one honest
    # answer: this period holds live documents, so `_compute_and_store` WOULD write the
    # assessment, and the stored row does not have it. That can only be true of a row computed
    # by older code, and recomputing is precisely the repair.
    if current_docs and isinstance(result.signal_inputs, dict) \
            and "evidenceQualification" not in result.signal_inputs:
        return True, ("this result was computed before the period's Category-9 evidence "
                      "assessment was recorded, so every measure requiring qualified evidence "
                      "refused on it")

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


# ---------------------------------------------------------------- RUN 68, THE TIME-PHASED CURVE
#
# THREE MODULES ABSTAINED ON A CURVE THE BASELINE DOCUMENT PRINTS. A1.6 Earned Schedule, A2.6
# S-Curve Deviation and A1.9 Budget Execution Rate are each defined on a period-by-period
# baseline, and each printed the curve's name in its abstention: "a time phased baseline: the
# cumulative value of work planned to be complete at the end of each period", and for A1.9 "an
# approved time phased expenditure baseline: the amount planned to be spent by the end of each
# period". The single figure the platform already extracted from that document
# (`planned_value_to_date`) is ONE POINT ON THAT CURVE, and one point is not a curve --
# `earned_schedule` refuses fewer than two periods in its own words.
#
# So `baseline_curve_json` now asks the document for the table, `baseline_curve.read_baseline_curve`
# maps its headings onto the two quantities, and this assembles the two governed structures. It
# runs on the DOCUMENT PATH ONLY, for the same reason the Category-9 record above does: a training
# period's signal inputs are projected from a deterministic state, and no baseline document was
# uploaded to it.
#
# WHAT IS READ OFF THE DOCUMENT AND WHAT IS READ OFF THE PLATFORM, stated separately because the
# difference is the whole safety argument.
#
#   FROM THE DOCUMENT, and from nothing else: every figure on both curves, the period each row
#   states, the baseline version and the approval source. `_provenance` in canonical_v3 REFUSES to
#   default the last two ("a blank source silently reads as an unsourced number"), so where the
#   document does not state them the structure is not assembled at all and the three modules go on
#   abstaining. That is the correct outcome and it is not a gap to be filled.
#
#   FROM THE PLATFORM, and only facts it already holds: the reporting period being computed, and
#   this project's own earned value as each earlier period stored it. Neither is a judgement.
#
# THE ACTUAL SERIES IS ALIGNED TO THE CURVE'S ROWS, NOT APPENDED TO THEM. `s_curve_deviation`
# pairs the two series BY POSITION (`a[i] - p[i]`) and truncates to the shorter, so an actual
# series merely appended in period order would silently pair period 3's earned value against
# period 1's plan the moment the baseline began at period 0 or skipped a period. It is therefore
# built by walking the curve's own rows in order and looking up the earned value for each row's
# stated period, STOPPING at the first row the project has no earned value for. The pairing is
# then positional by construction and the series ends where the project's record ends.
#
# THE ELAPSED TIME IS THE REPORTING PERIOD'S POSITION ON THE CURVE. `earned_schedule` measures
# earned schedule in curve POSITIONS -- its own oracle runs PV = [0, 20, 40, 60] "indexed from
# period 0" -- so the actual time it is compared against has to be on that same axis or the index
# is an off-by-one. It is taken as the zero-based position, in the ordered curve, of the row whose
# period the platform is reporting: a baseline printing periods 1..12 puts period 2 at position 1,
# and a baseline printing 0..12 puts it at position 2, which is the oracle's own convention. Where
# the curve does not reach the reporting period there is no position, none is invented, and the
# module abstains.
def _baseline_structures(session: Session, project: Project, period: int, documents: list[dict],
                         si: dict) -> dict:
    """The Run-68 governed curves this period's baseline documents support. See above."""
    from .baseline_curve import read_baseline_curve

    rows: list[dict] = []
    version = approval = None
    for d in documents:
        if d.get("doc_type") != "time_phased_schedule":
            continue
        ex = d.get("extraction") or {}
        if not isinstance(ex, dict):
            continue
        read = read_baseline_curve(ex.get("baseline_curve_json"))
        if not read:
            continue
        # ONE DOCUMENT SUPPLIES THE CURVE. Two baseline documents in one period state two
        # baselines, and stitching their rows together would produce a curve neither of them
        # printed. The longest is taken and the other is left alone; where they tie the first
        # the period's document ordering yields wins, which is the same deterministic rule the
        # rest of assembly uses rather than a judgement about which baseline is better.
        if len(read) > len(rows):
            rows = read
            version = str(ex.get("baseline_version") or "").strip() or None
            approval = str(ex.get("baseline_approval_source") or "").strip() or None
    if len(rows) < 2 or not version or not approval:
        # FEWER THAN TWO PRINTED PERIODS IS NOT A CURVE, and an unsourced curve is one no reading
        # could be interpreted from later. Either way the key is ABSENT rather than partial, so
        # each module abstains on its own guard with its own sentence.
        return {}

    ordered = sorted(rows, key=lambda r: r["period_index"])
    out: dict = {}

    pv_rows = [r for r in ordered if "cumulative_pv" in r]
    if len(pv_rows) >= 2:
        # THIS PROJECT'S OWN EARNED VALUE, AS EACH PERIOD STORED IT. `_earlier_live_results` is
        # the one read every cross-period series here is built from: strictly earlier live rows,
        # so recomputing an earlier period cannot see a later one.
        ev_by_period: dict[int, float] = {}
        for r in _earlier_live_results(session, project, period):
            v = (r.signal_inputs or {}).get("ev")
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                ev_by_period[int(r.period)] = float(v)
        current_ev = si.get("ev")
        if isinstance(current_ev, (int, float)) and not isinstance(current_ev, bool):
            ev_by_period[int(period)] = float(current_ev)

        # A2.6 IS NOT IN SERVICE. It was retired by Run 43 and `service_index` excludes it, so the
        # series below reaches no module today and this run's measured gain is A1.6 and A1.9. It
        # is assembled anyway because it is a fact about this project that the structure is
        # defined to carry, and because leaving the structure half-built would make returning A2.6
        # to service look like a wiring gap when it is a retirement decision.
        actual: list[float] = []
        for r in pv_rows:
            got = ev_by_period.get(int(r["period_index"]))
            if got is None:
                break
            actual.append(got)

        # THE ELAPSED TIME IS ONLY SUPPLIED WHERE THE CURVE'S AXIS IS ANCHORED AT ZERO, and this
        # guard is the whole of the off-by-one argument. `earned_schedule` returns a curve
        # POSITION, and SPI(t) is that position divided by the elapsed time, so the two are a
        # ratio only when position and elapsed periods share an origin. A baseline printed from
        # period 1 does not: its position 0 is the END of period 1, so at the end of period 2 the
        # position is 1 while two periods have elapsed, and EITHER figure fed in as the elapsed
        # time yields an index that is wrong in a stated direction -- 1 makes a project ahead of
        # schedule look further ahead than it is, 2 makes the same project look behind.
        #
        # This was worked through rather than assumed, on the fixture's own numbers: earned value
        # 2,000,000 against a curve of 1,020,000 and 1,500,000 at periods 1 and 2 sits at position
        # 1.625, which is period 2.625 -- genuinely AHEAD at the end of period 2 -- and dividing
        # 1.625 by an elapsed 2 reports 0.81, a project behind schedule. The module's own oracle
        # settles it: PV = [0, 20, 40, 60] is "indexed from period 0", so position equals periods
        # elapsed exactly when the baseline prints its zero origin.
        #
        # So where the curve carries that origin row the elapsed time is the reporting period
        # itself, and where it does not the key is OMITTED and A1.6 abstains on its own guard.
        # An index that is quietly wrong is worse than a measure that declines to report.
        at_position = None
        if float(pv_rows[0]["period_index"]) == 0.0:
            for i, r in enumerate(pv_rows):
                if float(r["period_index"]) == float(period):
                    if float(i) == float(period):
                        at_position = float(period)
                    break

        structure: dict = {
            "periods": [{"period_index": r["period_index"], "period": r["period"],
                         "cumulative_pv": r["cumulative_pv"]} for r in pv_rows],
            "baseline_version": version,
            "approval_source": approval,
            "period_index_basis": pv_rows[0]["index_basis"],
            "assembled_by": "document extraction",
            "source_document_type": "time_phased_schedule",
        }
        if at_position is not None:
            structure["actual_time_periods"] = at_position
        if actual:
            structure["cumulative_actual"] = actual
            structure["cumulative_actual_basis"] = (
                "this project's own earned value as each reporting period stored it, taken at "
                "the periods the baseline itself prints and stopping where the record stops")
        out["timePhasedBaseline"] = structure

    spend_rows = [r for r in ordered if "expected_spend" in r]
    if len(spend_rows) >= 2:
        out["expenditureBaseline"] = {
            "periods": [{"period_index": r["period_index"], "period": r["period"],
                         "expected_spend": r["expected_spend"]} for r in spend_rows],
            "baseline_version": version,
            "approval_source": approval,
            "status_period_index": float(period),
            "period_index_basis": spend_rows[0]["index_basis"],
            "assembled_by": "document extraction",
            "source_document_type": "time_phased_schedule",
        }
    return out


# ------------------------------------------------------- RUN 69, FOUR MORE DOCUMENT STRUCTURES
#
# THE SAME FINDING RUN 68 MADE, APPLIED FOUR MORE TIMES: the module did not lack a calculation,
# it lacked a FACT its own document prints, and the platform was asking that document only for
# scalars. Each of the four below names its structure in its own abstention sentence.
#
#   A2.9 Resource Loading      "a time phased resource profile: for each period and each kind of
#                               resource, the amount of work demanded and the amount available"
#   A3.3 Labor Productivity    "a record of production: the quantity of work installed, the
#                               quantity planned, and the labour hours each of those took"
#   A3.5 Overhead Absorption   "an overhead allocation base: the planned and actual overhead and
#                               the planned and actual amount of the base it is absorbed over"
#   B3.5 Modification Governance  "a governed contract modification register"
#
# and B3.2 EVMS Applicability, whose evidence is what a contract states about its own regime.
#
# WHAT IS READ OFF THE DOCUMENT: every figure and every name. WHAT IS READ OFF THE PLATFORM:
# nothing at all -- unlike the Run-68 curves, none of these structures needs a cross-period
# series, so each is a pure function of one period's own extractions.
#
# WHAT IS REFUSED: `canonical_v3._provenance` and `canonical_v6` both refuse to default a source,
# so where a document states the figures but not where they came from the structure is NOT
# assembled and the module goes on abstaining. That is the correct outcome and not a gap.
#
# DOCUMENT PATH ONLY, for the same reason the Category-9 record and the Run-68 curves are: a
# training period's signal inputs are projected from a deterministic state, and no document was
# uploaded to it.
def _text_or_none(value) -> str | None:
    """RUN 87. A printed cell as a stripped string, or None where the document stated nothing."""
    if value is None:
        return None
    out = " ".join(str(value).split()).strip()
    return out or None


def _run69_structures(session: Session, project: Project, period: int,
                      documents: list[dict]) -> dict:
    """
    The Run-69 governed structures this period's documents support. See above.

    ONE EXCEPTION TO "THIS PERIOD'S DOCUMENTS", AND IT IS RUN 45'S OWN RULE. What a contract
    states about its own regulatory regime -- the agency, the acquisition, the clause -- is a
    fact about the PROJECT, not about a reporting period, and Run 45 established exactly this:
    "a contract uploaded at period 1 was invisible from period 2 on". So the contract documents
    at or before the period being computed are read for B3.2, latest period first, and the other
    three structures stay strictly period-scoped because a resource histogram, an overhead
    schedule and a modification register each describe one reporting period.
    """
    from .contract_modifications import read_modification_register
    from .resource_tables import (
        overhead_allocation_base, production_output_record, read_resource_profile,
    )

    out: dict = {}
    for d in documents:
        ex = d.get("extraction")
        if not isinstance(ex, dict):
            continue
        doc_type = d.get("doc_type")

        if doc_type == "resource_report":
            # A2.9. ONE DOCUMENT SUPPLIES THE PROFILE, the longest of them, on the same
            # deterministic rule `_baseline_structures` states: stitching two resource reports'
            # rows together would produce a histogram neither of them printed.
            buckets = read_resource_profile(ex.get("resource_profile_json"))
            version = str(ex.get("resource_plan_version") or "").strip()
            if buckets and version:
                existing = out.get("resourceProfile")
                if existing is None or len(buckets) > len(existing["buckets"]):
                    out["resourceProfile"] = {
                        "buckets": buckets,
                        "resource_plan_version": version,
                        "assembled_by": "document extraction",
                        "source_document_type": "resource_report",
                    }
            # A3.3. The two hours figures are the ones this same document type already states.
            record = production_output_record(
                ex, planned_hours=ex.get("planned_labor_hours"),
                actual_hours=ex.get("actual_labor_hours"))
            if record is not None:
                out.setdefault("productionOutputRecord", record)

        elif doc_type in ("inspection_report", "quality_audit_report"):
            # RUN 87, A6.1. THE QUALITY REQUIREMENT REGISTER, from the document that prints it.
            # `canonical_v6.quality_compliance` takes the GOVERNED path the moment the structure
            # carries a `requirements` list, so nothing in `server/app/simulation/` changes: the
            # corpus assembly that produced `recorded_audit_evidence` and NOT_ESTIMABLE is still
            # there, still correct, and is simply no longer the only thing on offer. Longest
            # register wins between two quality documents in one period, on the deterministic
            # rule `resourceProfile` states above. Where the document printed no readable table,
            # nothing is assembled and A6.1 goes on reaching NOT_ESTIMABLE, honestly.
            from .compliance_register import read_requirement_rows
            requirements = read_requirement_rows(ex.get("quality_requirements_json"))
            if requirements:
                existing = out.get("qualityRequirementRegister")
                if existing is None or len(requirements) > len(existing["requirements"]):
                    out["qualityRequirementRegister"] = {
                        "requirements": requirements,
                        "register_id": _text_or_none(ex.get("quality_register_id")),
                        "register_version": _text_or_none(ex.get("quality_register_period")),
                        "assembled_by": "document extraction",
                        "source_document_type": doc_type,
                    }

        elif doc_type == "environmental_report":
            # RUN 87, A6.3. APPLICABILITY FIRST, AND IT IS READ, NEVER ASSUMED.
            # `canonical_v6.environmental_compliance` refuses to assess conformance without BOTH
            # a jurisdiction and a permitting authority, and it has "no branch that could
            # hard-code" EPA. Both are now asked of the document that states them. Where the
            # document states neither, or only one, NOTHING IS ASSEMBLED HERE and the corpus
            # path's APPLICABILITY_NOT_ESTABLISHED stands -- a half-established applicability is
            # not an applicability, and supplying one half would be inventing the other.
            from .compliance_register import read_requirement_rows
            jurisdiction = _text_or_none(ex.get("environmental_jurisdiction"))
            authority = _text_or_none(ex.get("permitting_authority"))
            if jurisdiction and authority:
                requirements = read_requirement_rows(
                    ex.get("environmental_requirements_json"))
                existing = out.get("environmentalRequirementRegister")
                if existing is None or len(requirements) > len(existing["requirements"]):
                    out["environmentalRequirementRegister"] = {
                        "jurisdiction": jurisdiction,
                        "permitting_authority": authority,
                        "permit_id": _text_or_none(ex.get("permit_id")),
                        "permit_version": _text_or_none(ex.get("permit_version")),
                        "site_id": _text_or_none(ex.get("permit_site_id")),
                        "operator_status": _text_or_none(ex.get("operator_status")),
                        "requirements": requirements,
                        "assembled_by": "document extraction",
                        "source_document_type": "environmental_report",
                    }

        elif doc_type == "lookahead_schedule":
            # RUN 86, A2.8. The look-ahead ACTIVITY INVENTORY, where this period's look-ahead
            # document printed one. `canonical_v3.look_ahead_ready_fraction` derives its counts
            # from rows and refuses to default `horizon` or `status_date`, so the structure is
            # assembled only where the document states all three: at least one activity row, the
            # window, and the date it stands at. The rows are passed through as printed (see
            # `lookahead_table` for what is refused there and why); a row the canonical function
            # cannot accept makes the MODULE abstain in its own words, never this assembler
            # repair it. Longest inventory wins between two look-aheads in one period, on the
            # same deterministic rule `resourceProfile` states above.
            from .lookahead_table import read_lookahead_activities
            activities = read_lookahead_activities(ex.get("lookahead_activities_json"))
            horizon = str(ex.get("lookahead_horizon") or "").strip()
            status_date = str(ex.get("lookahead_status_date") or "").strip()
            if activities and horizon and status_date:
                existing = out.get("lookAheadSchedule")
                if existing is None or len(activities) > len(existing["activities"]):
                    out["lookAheadSchedule"] = {
                        "activities": activities,
                        "horizon": horizon,
                        "status_date": status_date,
                        "assembled_by": "document extraction",
                        "source_document_type": "lookahead_schedule",
                    }

        elif doc_type == "cost_report":
            base = overhead_allocation_base(ex)
            if base is not None:
                out.setdefault("overheadAllocationBase", base)

        elif doc_type == "change_order":
            mods = read_modification_register(ex.get("modifications_json"))
            if mods:
                existing = out.get("contractModificationRegister")
                if existing is None or len(mods) > len(existing["modifications"]):
                    out["contractModificationRegister"] = {
                        "modifications": mods,
                        "evidence_id": "contract-modification-register",
                        "source_type": "contract modification register uploaded for this period",
                        "provenance": "read from the register printed by the change-order "
                                      "document uploaded for this period",
                        "assembled_by": "document extraction",
                        "source_document_type": "change_order",
                    }

    contracts: list[dict] = [d for d in documents if d.get("doc_type") == "contract_value"]
    if not contracts:
        earlier = session.scalars(
            select(DocumentUpload.period)
            .where(DocumentUpload.project_id == project.id, DocumentUpload.period < period)
            .distinct()
        ).all()
        for p in sorted({int(x) for x in earlier if x is not None}, reverse=True):
            contracts = [d for d in _period_documents(session, project, p)
                         if d.get("doc_type") == "contract_value"]
            if contracts:
                break
    for d in contracts:
        ex = d.get("extraction")
        if isinstance(ex, dict):
            # B3.2. EVERY KEY IS OMITTED WHERE THE CONTRACT DID NOT STATE IT, and the canonical
            # function's own precedence then reaches INSUFFICIENT_EVIDENCE rather than a
            # determination. A missing designation is not a determination of non-applicability.
            evidence: dict = {}
            federal = ex.get("federal_acquisition")
            if isinstance(federal, bool):
                evidence["federal_context"] = federal
            elif isinstance(federal, str) and federal.strip().lower() in ("yes", "no",
                                                                          "true", "false"):
                evidence["federal_context"] = federal.strip().lower() in ("yes", "true")
            procedure = ex.get("agency_procedure_requires_evms")
            if isinstance(procedure, bool):
                evidence["agency_procedure_requires_evms"] = procedure
            major = ex.get("major_acquisition")
            if isinstance(major, bool):
                evidence["major_acquisition"] = major
            for key, field in (("agency", "contracting_agency"),
                               ("acquisition_designation", "acquisition_designation"),
                               ("clause_id", "evms_clause_id"),
                               ("award_date", "award_date"),
                               ("acquisition_id", "acquisition_id")):
                value = str(ex.get(field) or "").strip()
                if value:
                    evidence[key] = value
            if evidence:
                evidence.update({
                    "evidence_id": "contract-regulatory-evidence",
                    "source_type": "contract or award document uploaded for this project",
                    "evidence_source": "the contract document uploaded for this project",
                    "assembled_by": "document extraction",
                    "source_document_type": "contract_value",
                })
                out.setdefault("evmsApplicabilityEvidence", evidence)

    # ----------------------------------------------------- RUN 80, THE THREE A3 STRUCTURES
    #
    # A3.1, A3.7 and A3.9 each abstained on a structure their documents were carrying. See the
    # note beside `historical_data` in `extraction_fields._EXTRACTION_FIELDS` for what broke and
    # where. This is the assembler half; the extraction half is that note and the shape hint in
    # `extraction_client.build_prompt`.
    #
    # ALL OR NOTHING, PER STRUCTURE. `canonical_v3._provenance` refuses a structure whose source
    # is blank, and it is right to: "a blank source silently reads as an unsourced number". So a
    # structure is assembled only where the document states EVERY part of it, and where it does
    # not, the key is absent, the module abstains on its own guard, and the sentence it prints
    # names what is missing. Nothing here defaults, substitutes or derives a provenance field.
    for d in documents:
        ex = d.get("extraction")
        if not isinstance(ex, dict) or d.get("doc_type") != "historical_data":
            continue
        for key, structure in _run80_a3_structures(ex).items():
            out.setdefault(key, structure)
    return out


def _text(ex: dict, key: str) -> str:
    return " ".join(str(ex.get(key) or "").split()).strip()


def _pos(ex: dict, key: str) -> float | None:
    """A stated figure above zero, or None. Never a default and never a zero standing in for an
    absent number: every consumer of these three structures refuses a non-positive figure."""
    from .extraction_merge import _coerce_numeric
    v = _coerce_numeric(ex.get(key))
    return float(v) if isinstance(v, (int, float)) and float(v) > 0 else None


def _run80_a3_structures(ex: dict) -> dict:
    """The A3.1 / A3.7 / A3.9 structures this ONE historical-data document supports."""
    out: dict = {}

    # ---- A3.7 analogEstimate. The analogue is identified BY NAME, which is the whole of what
    # Run 20 recorded the old proxy as lacking: "no analog selection, no comparability criteria
    # and no adaptation factors". `analog_cost` is the analogue's FINAL cost -- what it actually
    # came to -- because that is the figure an adaptation factor is applied to; its award value
    # is a different number and is not used here.
    name = _text(ex, "analogous_project_name")
    cost = _pos(ex, "similar_project_final_cost")
    factor = _pos(ex, "analogous_adjustment_factor")
    source = _text(ex, "analogous_source")
    criteria = _text(ex, "analogous_comparability_basis")
    normalization = _text(ex, "analogous_normalization_basis")
    if name and cost and factor and source and criteria and normalization:
        out["analogEstimate"] = {
            "analog_project_id": name,
            "analog_cost": cost,
            "source": source,
            "comparability_criteria": criteria,
            "normalization": normalization,
            # ONE FACTOR, NAMED BY THE DOCUMENT'S OWN WORD FOR IT. The document states one
            # adjustment factor; it is carried as one adaptation factor and not decomposed into
            # factors the document does not print.
            "adaptation_factors": [{"factor_name": "stated adjustment factor",
                                    "factor_value": factor}],
            "assembled_by": "document extraction",
            "source_document_type": "historical_data",
        }

    # ---- A3.9 externalCostIndex. Nine stated parts, no defaults. A published index that does
    # not say which geography or which cost scope it covers is the wrong index applied
    # confidently, so absence refuses here rather than being filled in.
    index = {k: _text(ex, f"cost_index_{k}") for k in
             ("name", "authority", "geography", "scope", "base_period",
              "observation_period", "vintage")}
    base_value = _pos(ex, "cost_index_base_value")
    current_value = _pos(ex, "cost_index_current_value")
    if all(index.values()) and base_value and current_value:
        out["externalCostIndex"] = {
            "index_name": index["name"], "authority": index["authority"],
            "geography": index["geography"], "scope": index["scope"],
            "base_period": index["base_period"],
            "observation_period": index["observation_period"],
            "vintage": index["vintage"],
            "base_index_value": base_value, "current_index_value": current_value,
            "assembled_by": "document extraction",
            "source_document_type": "historical_data",
        }
        # THE COST EXPOSURE THE INDEX IS APPLIED TO, where the document names it. It is NOT part
        # of the index's provenance and `inflation_adjustment` does not refuse the structure
        # without it -- the MODULE refuses, in its own words ("does not say which cost exposure
        # it is to be applied to"), which is the more precise sentence. It is not defaulted to
        # the budget at completion: which part of the cost an index escalates is a judgement the
        # document has to make, and applying a building-materials index to the whole contract
        # sum would be that judgement made silently by this platform.
        _exposure = _pos(ex, "cost_index_cost_exposure")
        if _exposure:
            out["externalCostIndex"]["cost_exposure"] = _exposure

    # ---- A3.1 referenceClassPopulation, from the printed table.
    members = _reference_class_members(ex.get("reference_class_json"))
    meta = {k: _text(ex, f"reference_class_{k}") for k in
            ("inclusion_criteria", "exclusion_criteria", "outcome_definition",
             "normalization", "vintage")}
    if len(members) >= 3 and all(meta.values()):
        out["referenceClassPopulation"] = {
            "members": members,
            "inclusion_criteria": meta["inclusion_criteria"],
            "exclusion_criteria": meta["exclusion_criteria"],
            "outcome_definition": meta["outcome_definition"],
            "normalization": meta["normalization"],
            "data_vintage": meta["vintage"],
            "assembled_by": "document extraction",
            "source_document_type": "historical_data",
        }
        # WHICH PERCENTILE GOVERNS, stated by the document and never chosen here. The module
        # refuses without it and it is right to: an uplift read at the median and an uplift read
        # at the eightieth percentile are different forecasts, and picking one for the owner
        # would be this platform asserting a risk appetite nobody set.
        _pct = _pos(ex, "reference_class_governed_percentile")
        if _pct:
            # A percentile stated as 80 is the same instruction as one stated as 0.80.
            out["referenceClassPopulation"]["governed_percentile"] = (
                _pct / 100.0 if _pct > 1.0 else _pct)
    return out


# THE COLUMN HEADINGS A REFERENCE-CLASS TABLE PRINTS. The rows arrive keyed by the TABLE'S OWN
# headings (that is what the shape hint asks for), so the headings are resolved here, once,
# rather than the model being asked to rename the document's columns -- the same decision
# `risk_register.map_headings` and `schedule_activities` already make for their tables.
_RC_ID_HEADINGS = ("project", "project name", "project id", "reference project",
                   "name", "id", "reference", "comparable project")
_RC_AWARD_HEADINGS = ("award", "award value", "awarded", "award amount", "original value",
                      "budget", "baseline", "original contract sum", "contract award")
_RC_FINAL_HEADINGS = ("final", "final value", "final cost", "actual", "actual cost",
                      "outturn", "final contract sum", "completion cost")
_RC_OVERRUN_HEADINGS = ("overrun", "proportional overrun", "cost overrun", "overrun ratio",
                        "overrun fraction")


def _reference_class_members(raw) -> list[dict]:
    """
    The reference class's rows, or [] where the table supports none.

    THE OVERRUN IS DERIVED HERE, IN CODE, and never asked of the model: the shape hint forbids
    the model computing one. Where the table prints award and final values, the proportional
    overrun is (final - award) / award, which is the outcome definition
    `canonical_v3.reference_class_forecast` reads. Where the table prints the overrun itself as
    a share, it is read as printed. A row supporting neither is DROPPED rather than defaulted --
    a project counted at zero overrun is a project claimed to have finished on budget.
    """
    import re as _re
    from .extraction_merge import _coerce_numeric

    if not isinstance(raw, list):
        return []

    def pick(row: dict, headings) -> object:
        norm = {" ".join(_re.sub(r"[^a-z0-9]+", " ", str(k).lower()).split()): v
                for k, v in row.items()}
        for h in headings:
            if h in norm:
                return norm[h]
        return None

    out: list[dict] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        pid = " ".join(str(pick(row, _RC_ID_HEADINGS) or "").split()).strip()
        if not pid:
            continue
        overrun = _coerce_numeric(pick(row, _RC_OVERRUN_HEADINGS))
        if overrun is None:
            award = _coerce_numeric(pick(row, _RC_AWARD_HEADINGS))
            final = _coerce_numeric(pick(row, _RC_FINAL_HEADINGS))
            if award is None or final is None or float(award) <= 0:
                continue
            overrun = (float(final) - float(award)) / float(award)
        out.append({"reference_project_id": pid,
                    "proportional_overrun": float(overrun)})
    return out


# ------------------------------------------------------------------- RUN 67, THE CATEGORY-9 GAP
#
# WHAT WAS FOUND, AND IT IS NOT WHAT THE PREVIOUS RUN CONCLUDED. Run 66 measured seventeen
# modules across five categories refusing on ONE identical sentence -- "The evidence offered to
# this measure carries no Category-9 assessment, so it is unassessed and not eligible for this
# use" -- and recorded that `evidenceQualification` has no writer anywhere in production. That
# measurement was right. The conclusion drawn beside it, that supplying one would mean inventing
# a judgement about the evidence, is WRONG, and it was tested rather than reasoned about:
# `qualification_boundary.declared_evidence` hands the declaration to
# `qualified_evidence.assess`, which DERIVES the verdict from properties of the evidence record
# and refuses to honour a state more favourable than those properties support. Handed a record
# carrying nothing but the facts this platform already holds -- an identity, the kind of source,
# the period, the date the period's evidence speaks as of, and the fields two documents
# disagreed about -- `assess` returns QUALIFIED_WITH_LIMITATIONS and records the one honest
# limitation: no governed reliability mapping is established, so no numeric reliability weight
# is asserted.
#
# SO NOTHING IS INVENTED HERE, AND THE OMISSIONS ARE THE POINT.
#
#   * NO `verification_status`. Nobody verified these documents. Claiming "verified" would be
#     the invented value section 8 forbids, and the field is therefore ABSENT rather than filled.
#   * NO `source_authority`. A participant's upload is not a system of record and is not
#     asserted to be one.
#   * NO `reliability_weight`. There is no governed rubric in this repository to map a source
#     onto a number, so no number is asserted; `assess` records the absence as a limitation.
#   * NO `timeliness_status`. A freshness verdict needs a governed freshness rule for the use,
#     and none is established, so the field stays UNASSESSED rather than being called TIMELY.
#   * NO `qualification_state`. The record does not declare its own verdict. `assess` computes
#     it. A package may declare itself unassessed and may never declare itself qualified.
#
# WHAT IS STATED IS STATED BECAUSE THE PLATFORM ALREADY HOLDS IT:
#
#   * `effective_date` is the latest as-of among THIS PERIOD'S OWN observations, which is the
#     date the period's evidence speaks as of. It is what makes the future-dating rule live.
#   * `material_conflicts` names every field for which two of this period's documents state
#     DIFFERENT values. That is a fact about the uploads, computed here from the observations
#     themselves, and it makes the gate able to REFUSE: a project whose documents contradict
#     each other on a field reaches REVIEW_REQUIRED and its gated modules stay dark, which is
#     the behaviour the Category-9 architecture exists to produce. A record that reported no
#     conflicts because it never looked would be worse than no record at all.
#   * `required_inputs` is empty ON PURPOSE and is not a claim that nothing is required. What
#     each module requires is decided by that module's own `check_inputs`, which is where this
#     programme has repeatedly established it belongs; restating those field lists here would be
#     a hand-maintained copy of production logic checked against production logic.
#
# The record describes the PERIOD'S EVIDENCE BASE, not one module's inputs, so it is written
# flat: `declared_evidence` applies a flat declaration to every module that asks.
def _evidence_qualification(period: int, observations: list[dict]) -> dict | None:
    """This period's Category-9 assessment, built from the period's own observations. See above
    for what is deliberately NOT stated in it."""
    if not observations:
        return None
    dates = sorted(str(o["as_of"]) for o in observations if o.get("as_of") is not None)
    # WHAT COUNTS AS AN UNRESOLVED CONFLICT, AND WHY IT IS NOT SIMPLY "TWO DOCUMENTS DISAGREE".
    # Two documents stating different values for one field is the NORMAL case and is exactly what
    # `select_signal_inputs` exists to resolve: the lowest declared writer tier wins, and within
    # a tier the latest as-of wins. Calling that a conflict would put nearly every real project
    # into REVIEW_REQUIRED and would block the gated modules for a disagreement the platform had
    # already settled by a declared rule -- a false refusal is as much a defect as a false pass.
    # A conflict is therefore recorded only where the DECLARED PRECEDENCE HAS NOTHING LEFT TO
    # DECIDE WITH: same field, same lowest tier, same latest as-of, and still two different
    # values. At that point selection falls through to the document ROLE rank, which is a
    # deterministic tiebreak and not a statement that one figure is right.
    per_field: dict[str, list[dict]] = {}
    for o in observations:
        if o.get("field") is None:
            continue
        per_field.setdefault(str(o["field"]), []).append(o)

    def _v(o):
        val = o.get("value")
        return val if isinstance(val, (str, int, float, bool, type(None))) \
            else json.dumps(val, sort_keys=True, default=str)

    conflicts: list[dict] = []
    for field, obs in sorted(per_field.items()):
        tiers = [o.get("tier") for o in obs if o.get("tier") is not None]
        if not tiers:
            continue
        top = min(tiers)
        same_tier = [o for o in obs if o.get("tier") == top]
        dated = [o for o in same_tier if o.get("as_of") is not None]
        if dated:
            latest = max(str(o["as_of"]) for o in dated)
            same_tier = [o for o in dated if str(o["as_of"]) == latest]
        values = {_v(o) for o in same_tier}
        if len(values) > 1:
            conflicts.append({
                "field": field,
                "writer_tier": top,
                "distinct_values": len(values),
                "documents": sorted({str(o.get("doc_type")) for o in same_tier}),
                "reason": "two documents of equal declared writer precedence, dated the same, "
                          "state different values for this field, so the declared precedence "
                          "rule cannot decide between them",
            })
    return {
        # THE RECORD IS A PURE FUNCTION OF THE PERIOD'S OWN EVIDENCE and carries no project
        # identity. Two projects that uploaded the same bytes into the same period must reach
        # the same Category-9 assessment, and the byte-identity guarantee several suites hold
        # over extracted signal inputs is not something a new key is entitled to break.
        "evidence_id": f"P{period}-evidence-base",
        "source_type": "project documents uploaded and extracted for this period",
        "period": str(period),
        "effective_date": dates[-1] if dates else None,
        "material_conflicts": conflicts,
    }


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
    # 0024. The register, same rule: written once for this period, never rewritten by a later
    # one, which is what keeps a recompute of an earlier period byte-identical.
    _persist_project_risks(session, project, period)
    _persist_project_notices(session, project, period)
    observations: list[dict] = []
    for d in documents:
        observations.extend(emit_observations(d))
    # RUN 45. Identity fields resolve at or before the period being computed; period fields
    # resolve exactly as before. `documents` — and therefore `source_documents`, the staleness
    # fingerprint and the evidence table — remains the PERIOD's own set, unchanged.
    si = select_signal_inputs(observations, cutoff,
                              carried=_identity_observations_before(session, project, period))

    # D1. One input the analytical layer reads that the pure merge cannot produce, because it is
    # not a property of this period's documents: the project's event log. It is added here rather
    # than inside `assemble_signal_inputs`, which must stay pure, deterministic and order
    # independent — it knows nothing of projects, periods or the session. It is stored on the row
    # as part of `signal_inputs`, so the result records what the modules actually saw and not a
    # subset of it. The cross-period series are assembled in `run_and_store`, which is the one
    # place both assembly paths pass through.
    si["events"] = _events_as_of(project, cutoff)

    # RUN 67. THE PERIOD'S CATEGORY-9 ASSESSMENT, written for the first time. See
    # `_evidence_qualification` above for what it states, what it deliberately omits, and why
    # supplying it invents nothing. Attached here, on the DOCUMENT path only: a training period's
    # signal inputs are projected from a deterministic state rather than selected from uploaded
    # documents, so there is no evidence base to assess and none is asserted for it.
    _eq = _evidence_qualification(period, observations)
    if _eq is not None:
        si["evidenceQualification"] = _eq

    # RUN 68. THE TWO GOVERNED CURVES, where this period's baseline document printed a table to
    # build them from. See `_baseline_structures` above for what each figure is read off and for
    # why the key is absent rather than partial when the document states less than a curve.
    # `setdefault`, so a structure a project supplied through the governed intake is never
    # displaced -- the same precedence rule `project_data.py` states, applied here.
    for _key, _structure in _baseline_structures(session, project, period, documents, si).items():
        si.setdefault(_key, _structure)

    # RUN 69. Four more governed structures, same precedence rule: a structure supplied through
    # the governed intake is never displaced by one assembled from a document.
    for _key, _structure in _run69_structures(session, project, period, documents).items():
        si.setdefault(_key, _structure)

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
    from .simulation import compute_project
    from .simulation.portfolio_health import compute_portfolio_health_snapshot

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

    # RUN 28 CLOSURE. THE GOVERNED PROJECT DATA OBJECTS, MERGED HERE AND NOWHERE ELSE.
    #
    # Run 28 left twenty of the twenty-eight Category 1 to 3 modules abstaining because the
    # structure their canonical method is defined on is absent from the corpus. Twenty-one of the
    # twenty-three v3 structure keys were, at that point, written by NO production code: they
    # existed in test fixtures only, so the abstention rested on a supply path that had been
    # described rather than built. `project_data.py` is that path and this is the one place it
    # reaches a computation.
    #
    # AFTER the document merge and the cross-period series, and never overwriting either: a key
    # the period's own documents produced always wins, so a typed-in structure cannot displace
    # evidence read from the project's documents. PERIOD-EFFECTIVE, so a structure supplied for a
    # later period is invisible to this one and recomputing an earlier period stays byte
    # identical, which is the same acceptance condition the schedule snapshots are held to.
    # THE KEY IS ABSENT WHERE NOTHING WAS SUPPLIED, so a project with no governed data object
    # stores exactly the record it stored before this existed and no module sees a new empty key.
    # RUN 29 CLOSURE, THE ONE REAL CORPUS-TO-STRUCTURE WIRING GAP.
    #
    # Run 29 reported `real_corpus_populated = no` for all seventeen Category-4 and -5
    # structures. The closure decomposed that single sentence, which was covering two very
    # different cases: a structure whose defining fields are genuinely ABSENT from the corpus,
    # and a structure whose defining fields ARE present, already extracted, and simply never
    # wired to a module. Sixteen are the first case. THIS ONE IS THE SECOND, and it is the same
    # class of gap Run 28 found for A2.7, where baseline finish dates were already extracted and
    # reached no module.
    #
    # WHAT IS ALREADY IN THE CORPUS. `ncr_log` yields `ncr_issued`, a COUNT of nonconformances
    # raised in the reporting period, and `inspection_report` yields `items_inspected`, which is
    # a governed exposure in the supplied contract's own words -- its worked example is four
    # nonconformances over one hundred inspections. Both are extracted today and both reach these
    # signal inputs. Nothing is inferred: the numerator is a count that was extracted as a count
    # and the denominator is an inspection total that was extracted as an inspection total.
    #
    # WHAT IS NOT INVENTED. No per-nonconformance identity, date or severity is fabricated to
    # make a list out of a number. The assembled record uses the COUNT form, which reports the
    # quantities that need events as absent and says so on the result. The open and closed counts
    # are carried where they were extracted, beside the rate and never divided into it.
    #
    # ASSEMBLED BEFORE the governed project-data merge, so a structure a project typed in never
    # displaces evidence read from the project's own documents. That is rule 5 of project_data.py
    # applied here rather than restated.
    _ncr_issued = si.get("ncrIssued")
    _inspected = si.get("itemsInspected")
    if (_ncr_issued is not None and _inspected is not None
            and si.get("ncrExposureRecord") is None):
        try:
            _n = float(_ncr_issued)
            _x = float(_inspected)
        except (TypeError, ValueError):
            _n = _x = -1.0
        if _n >= 0 and _x > 0 and _n == int(_n):
            si["ncrExposureRecord"] = {
                "source": ("the nonconformance log and the inspection report for this "
                           "reporting period"),
                "exposure_unit": "inspections",
                "exposure_quantity": _x,
                "ncr_count": int(_n),
                "ncr_count_basis": "nonconformances raised in the reporting period",
                "open_count": si.get("ncrOpen"),
                "closed_count": si.get("ncrClosed"),
                "assembled_by": "document extraction",
            }
            si["ncrExposureRecordDerivation"] = {
                "derived": True,
                "numerator_field": "ncrIssued",
                "numerator_document_type": "ncr_log",
                "denominator_field": "itemsInspected",
                "denominator_document_type": "inspection_report",
                "event_detail_available": False,
                "not_fabricated":
                    "no nonconformance identity, date or severity was invented; the count form "
                    "reports the quantities that need events as absent",
            }

    _supplied = apply_to_signal_inputs(si, project.doc, period)
    if _supplied:
        si["projectDataStructures"] = _supplied

    # RUN 29, A4.1 DOCUMENT RISK SCORE: THE GOVERNED EVIDENCE OUTRANKS THE OPAQUE SCALAR.
    #
    # The supplied contract for A4.1 states that there is no universal scalar document risk score
    # and that a defensible implementation needs a governed risk taxonomy, the source document
    # type, the evidence span, the candidate finding, a severity, a confidence, the evidence
    # coverage, a transparent aggregation rule, the model or rule version and the source
    # provenance. What the extraction pipeline supplies is a single number per document with none
    # of those, and no amount of correct arithmetic downstream can make an unsourced number
    # traceable.
    #
    # So where a project supplies the governed document risk evidence, the score every downstream
    # module reads is RE-DERIVED from it by the canonical aggregation, the derivation is recorded
    # on the row, and the evidence travels with it. Where no such evidence exists the extraction
    # scalar is left exactly as it was and NOTHING here changes: this run does not fabricate
    # provenance for a number that has none, and section 9 of the contract leaves the empirical
    # precision and recall of the extraction itself as Run 33's work.
    _dre = si.get("documentRiskEvidence")
    if isinstance(_dre, dict):
        from .simulation.canonical import StructureAbsent
        from .simulation.canonical_v4 import document_risk_evidence
        try:
            _reading = document_risk_evidence(_dre)
        except StructureAbsent as _absent:
            si["docRiskScoreDerivation"] = {
                "derived": False, "reason": _absent.sentence,
                "empirical_validation": "PENDING_RUN_33"}
        else:
            si["docRiskScore"] = _reading["risk_score"]
            si["docRiskScoreDerivation"] = {
                "derived": True,
                "aggregation_rule": _reading["aggregation_rule"],
                "classifier_version": _reading["classifier_version"],
                "taxonomy_id": _reading["taxonomy_id"],
                "coverage": _reading["coverage"],
                "finding_count": _reading["finding_count"],
                "documents_cited": _reading["documents_cited"],
                "risk_classes": _reading["risk_classes"],
                "source": _reading["source"],
                "empirical_validation": _reading["empirical_validation"],
            }

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
        # RUN 28. The same snapshots, in the shape the canonical method is defined on: each
        # milestone's committed baseline date alongside the run of forecasts made for it. The
        # older key stays because the stored row records what the modules were given and other
        # readers already consume it; the new key is what A2.7 reads.
        forecast_history = _milestone_forecast_history(milestone_history)
        if forecast_history is not None:
            si["milestoneForecastHistory"] = forecast_history

    # 0024. THE REGISTER'S EXPOSURE, SERVED TO THE MODULES THAT WOULD NEED IT.
    #
    # Part 2 of the change that added this asked that the cost-forecasting modules be given a
    # real input rather than generating from literals. This is that input, in the same shape
    # and by the same route as `milestoneHistory` above: read from this period's own store,
    # bounded to this period, attached after selection, ignored by every module that does not
    # want it.
    #
    # NO MODULE CONSUMES IT TODAY, and that is reported rather than quietly true. Cost Risk
    # Analysis computes its whole spread as `max(0.03, abs(1 - cpi)) * 0.5` times a literal
    # 1.28, which has no slot for a list of probability and impact pairs; Reference Class
    # Forecasting is an OUTSIDE-view method whose meaning would invert if fed this project's own
    # inside view. Both would need their arithmetic changed, which was explicitly out of scope,
    # so the data is put where they can reach it and the change to reach for it is left to be
    # authorised. See REPORT_2026-08-10_risk-register-and-notices.md.
    #
    # THE KEY IS ABSENT WHERE THE REGISTER SUPPORTS NOTHING, so a module guarding on it abstains
    # on its own guard rather than on an exposure of zero, which is a different claim.
    exposure = register_exposure(_period_risks(session, project, period))
    if exposure["usable_count"]:
        si["registerExposure"] = exposure
        # RUN 28. THE CHANGE THE COMMENT ABOVE SAID WAS "LEFT TO BE AUTHORISED" IS AUTHORISED
        # AND MADE. Cost Risk Analysis P80's arithmetic was a deterministic uplift on the cost
        # index with no slot for a list of probability and impact pairs, and the register was
        # therefore served to a module that could not read it. The owner's Run-28 supplied
        # contract replaces that arithmetic with a simulated total-cost distribution over
        # exactly such a list, so the register is now assembled into the shape the canonical
        # method is defined on and the module consumes it.
        #
        # WHAT IS AND IS NOT INVENTED. Each usable register row becomes one risk event with the
        # probability and the cost impact the register itself states, and nothing else: a row
        # the register could not give both figures for is REFUSED by register_exposure above and
        # never reaches here, rather than being given a substituted probability. The base cost
        # is the project's own budget at completion. No distribution shape is invented for an
        # impact: a register states one impact figure, so the event's impact is that figure and
        # the declared family is POINT, which says so rather than implying a spread nobody
        # elicited. Where the budget is absent or not positive the key is omitted entirely and
        # the module abstains on its own guard.
        _bac = si.get("bac")
        if isinstance(_bac, (int, float)) and _bac > 0 and exposure.get("contributors"):
            si["costRiskModel"] = {
                "model_version": f"risk register, period {period}",
                "estimate_source": "the project's reported budget at completion and the risk "
                                   "register rows carrying both a probability and a cost impact",
                # RUN 28 CLOSURE. THE DEPENDENCE POLICY, STATED BY THE SOURCE RATHER THAN
                # ASSUMED BY THE SIMULATOR. The register records one probability and one cost
                # impact per row and NO relationship between rows: it has no correlation column,
                # no common-cause grouping and no joint distribution anywhere in it. Independence
                # is therefore what the source supports, and saying so is a declaration about the
                # register rather than an assumption smuggled into the arithmetic. Where a
                # project later supplies a governed cost risk model of its own through
                # `saveprojectdata`, that model states its own policy and this one is not used.
                "dependence_policy":
                    "INDEPENDENT. The risk register states a probability and a cost impact per "
                    "row and records no relationship between rows, so the events are simulated "
                    "independently; no correlation was elicited and none is assumed beyond what "
                    "the register itself supports.",
                "cost_components": [{"component_id": "BUDGET_AT_COMPLETION",
                                     "base_amount": float(_bac)}],
                "risk_events": [
                    {"risk_id": c["risk_key"], "probability": c["probability"],
                     "impact_distribution": "POINT", "impact": c["cost_impact"]}
                    for c in exposure["contributors"]],
            }

    run = compute_project(si, project.legacy_id, f"P{period}", cutoff,
                          project_id=project.legacy_id)

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
                        "actualPctComplete": s.get("actualPctComplete"),
                        # RUN 33. The other projects' GOVERNED PORTFOLIO STRUCTURES, carried
                        # from their own stored signal inputs -- which is where
                        # `project_data.apply_to_signal_inputs` put them when that project was
                        # computed. Nothing is re-derived here and nothing is invented for a
                        # project that supplied none.
                        "signal_inputs": s})
    # Include this project's freshly computed vector, which is not yet stored.
    vectors = [v for v in vectors if v["id"] != project.legacy_id]
    vectors.append({"id": project.legacy_id, "cpi": si.get("cpi"), "spi": si.get("spi"),
                    "docRiskScore": si.get("docRiskScore"),
                    "actualPctComplete": si.get("actualPctComplete"),
                    "signal_inputs": si})
    # Always call, and store whatever it returns — including the abstention shape. Collapsing
    # an abstention to a bare NULL (the behaviour before Run 2) discarded its reason, and T5's
    # portfolio view is required to render the reason verbatim rather than reconstruct one.
    #
    # AT v20 the message rendered here was "Portfolio too small for anomaly detection — need at
    # least 3 projects with signal data", reproducing a legacy off-by-one between that guard and
    # its own wording. At v21 the reason is the governed one the canonical layer states, and the
    # legacy sentence travels with the legacy implementation it belongs to.
    #
    # RUN 33. `history`, this project's per-period snapshots, no longer reaches Portfolio Health.
    # PH.3 is defined on a GOVERNED SIGNAL HISTORY with a stable signal identity, real reporting
    # dates, declared units, declared orientation and a per-observation qualification state; a
    # list of result snapshots carries none of those, and list position is not time. The
    # snapshots remain assembled and stored for the project-level series that already read them.
    # RUN 33, THE CANONICAL v21 PORTFOLIO HEALTH ROUTE. The five Portfolio Health readings are
    # produced by `canonical_v8` over ONE governed cohort, through the dispatcher in
    # `portfolio_health.py`. The superseded v20 implementation, `portfolio.compute_portfolio`,
    # is PRESERVED for the Run-2/6/13/14/15/17/20 findings recorded about it and is NOT called
    # from here or from anywhere else in production; `portfolio_health.assert_not_reachable`
    # proves that from this function's own source rather than from a list.
    #
    # WHY THE COHORT IS NOT `vectors`. A portfolio comparison needs a declared population, a
    # declared period, a declared feature schema and a declared model version before it means
    # anything, and "the rows this query returned" is none of those. Where no governed cohort has
    # been supplied through `saveprojectdata`, all five modules abstain and say so -- which is
    # the correct reading, not a regression from the populated one v20 produced.
    snapshot = compute_portfolio_health_snapshot(
        project.legacy_id, si,
        [(v["id"], v.get("signal_inputs") or {}) for v in vectors
         if v["id"] != project.legacy_id],
        cutoff)

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
                 package=None, project_legacy_id: str | None = None,
                 spec: dict | None = None) -> dict:
    """
    The stored result as returned to a member.

    The recommendation package is spliced in ONLY when `recommendation_visible` says so, and
    when it says no, action-bearing MODULE fields are redacted too — see `_ACTION_KEYS`.

    RUN 79. `spec` IS THE SPECIFICATION READING PROJECTION AND IT IS THE SOURCE.
    When it is supplied -- `a_projectresults` always supplies it -- `module_results`,
    `abstained`, `category_statuses` and `project_status` are taken from
    `spec_projection.projection()`, built from `specification_readings` alone, and the values
    on `row` are NOT consulted for them. There is no fallback: where the specification layer
    has no reading for a category the fields are empty and the page says the category has not
    been called, rather than showing a figure from the retired Python layer.

    `row` IS STILL READ, for `signal_inputs`, the period, the provenance columns and the
    derivations below that are Python and stay Python -- the evidence qualification, the
    recommendation basis, the EVM consistency check and the reveal-gate redaction. Those are
    the recommendation checks and the freeze architecture, which the order's section 6 puts out
    of scope. `computed_results` is history for the three fields above and remains the record
    of what the Python layer produced; nothing here deletes or writes it.
    """
    _spec_modules = spec["module_results"] if spec is not None else row.module_results
    _spec_abstained = spec["abstained"] if spec is not None else row.abstained
    _spec_cats = spec["category_statuses"] if spec is not None else row.category_statuses
    _spec_status = spec["project_status"] if spec is not None else row.project_status
    # RUN 89, GOAL THREE. The required-core verdict rides beside the status, so the Indeterminate
    # brief can render the reason without re-deriving the gate on the client. A row computed
    # before Run 89 carries None here, and the client reads None as "the gate did not run".
    # No stored field is invented for it: on a Python-layer row it is DERIVED from that row's
    # own `category_statuses` by the same pure function, so a stored row and a fresh projection
    # can never disagree about which required categories are missing.
    _spec_basis = (spec.get("project_status_basis") if spec is not None
                   else spec_projection.project_status_basis(_spec_cats or {}))
    view = {
        "result_id": row.result_id,
        "period": row.period,
        "signal_inputs": row.signal_inputs,
        "module_results": (_spec_modules if include_recommendation
                           else _redact_module_actions(_spec_modules)),
        # 0020. Which modules abstained on this row and why, verbatim (module_id + reason, never
        # an action field, so nothing here is gated by `recommendation_visible`). NULL on rows
        # computed before the column existed.
        "abstained": _spec_abstained,
        "category_statuses": _spec_cats,
        "project_status": _spec_status,
        "project_status_basis": _spec_basis,
        # RUN 11, GATES 5 AND 6. Derived at read time from the category statuses this row already
        # holds, by the same function the compute path uses. No column is added, so a row stored
        # before this run answers exactly as one stored after it, and migrations 0020 through
        # 0025 stay where they are.
        **governed_status_semantics(_spec_cats),
        # RUN 12, GATE 2. The evidence qualification, derived at read time from what this row
        # already holds, by the same function the compute path uses. Metadata only: it carries
        # no score, casts no vote and cannot change `project_status`, which is read from the
        # stored row above and never revised here. Its unanswerable dimensions stay PARTIAL and
        # NOT_ESTIMABLE on the read path exactly as they are on the compute path.
        "evidence_qualification": qualification_for_stored_result(
            signal_inputs=row.signal_inputs,
            module_results=row.module_results,
            abstained=row.abstained,
            # RUN 42. The project's identity, so the read path's record names the same
            # project the compute path's does. This was hard-coded None while the caller held
            # the project, which is the same identity loss compute.py carried.
            project_id=project_legacy_id,
            period=(f"P{row.period}" if row.period is not None else None),
            period_cutoff=row.period_cutoff,
        ),
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
    # RUN 32 FINAL CLOSURE. This matched the literal "Regret_Minimization", which B4.7 stopped
    # emitting when the section-3 rename landed. The lookup did not fail -- it silently found
    # nothing, so the recommendation basis quietly went absent on every project. It matches the
    # current class and the historical one, because stored rows written before the rename still
    # carry the old identifier.
    _regret = next((m for m in (_mods or [])
                    if isinstance(m, dict)
                    and m.get("method_class") in B4_7_ANY_METHOD_CLASS),
                   None)
    view["recommendation_basis"] = recommendation_basis(row.signal_inputs, _regret)
    # RUN 47. THE EVM CONSISTENCY CHECK. Where one document states both a value and the
    # percentage that determines it against a known budget at completion, the implied value is
    # computed and the two are compared; a relative difference above the tolerance is reported.
    # DERIVED AT READ TIME from the row this response already carries, by a pure function, for
    # the same reason `recommendation_basis` is: no column is added, no migration is needed, a
    # row stored before this run answers exactly as one stored after it, AND NO STORED FIGURE
    # CAN CHANGE, because nothing on this path writes. It carries no band, no colour and no
    # severity, it casts no vote, and `project_status` and `category_statuses` above are read
    # from the stored row and are not revised here. It is NOT gated by the reveal: a
    # disagreement between two figures a document itself stated is evidence, in the same class
    # as `signal_inputs`, and carries no action.
    view["consistency_findings"] = consistency_findings(row.signal_inputs, row.period)
    # RUN 96. THE GOVERNANCE DECISION CARD, COMPOSED FROM THIS ROW AT READ TIME.
    #
    # Same class as `recommendation_basis` and `consistency_findings` immediately above, and for
    # the same reasons: a PURE FUNCTION of the row this response already carries, so no column is
    # added, no migration is needed, and a row stored before this run answers exactly as one
    # stored after it. NOTHING ON THIS PATH WRITES, so no stored figure can change.
    #
    # It carries NO band of its own, casts no vote, and does not revise `project_status` or
    # `category_statuses`, which are read from the stored row above. It states a FINDING and a
    # QUESTION and never an action, a deadline, an authority or a remedy.
    #
    # It is NOT gated by the reveal. The card is composed from the project's own computed
    # readings, which the project manager is already shown; the researcher-authored
    # recommendation package above is the thing the reveal gate withholds, and it is separate.
    view["decision_brief"] = compose_decision_brief(
        category_statuses=_spec_cats or {},
        module_results=_spec_modules or [],
        status_basis=_spec_basis or {},
        row={
            "simulation_version": row.simulation_version,
            "seed": row.seed,
            "period": row.period,
            # RUN 97, GOAL ZERO, THE FIRST OF TWO BREAKS. This was `row.period_cutoff`, a
            # `datetime.date`, which `json.dumps` cannot encode. `decision_brief` copies it
            # through to the response, so EVERY `projectresults` call raised TypeError and
            # returned a 500 -- measured in a real browser: the detail page's served result
            # never arrived at all, `rowFor(p).period` was null, and the Governance Decision
            # card fell back to its awaiting state. Line 2664 already stringifies the same
            # column for the same response; this now matches it.
            "period_cutoff": str(row.period_cutoff) if row.period_cutoff else None,
            "computed_at": row.computed_at.isoformat() if row.computed_at else None,
        },
        source_documents=row.source_documents,
    )
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

    # THE NUMBER-ONLY PATH. The period picker now offers a NUMBER (the periods this project
    # already holds, plus the next one) rather than a calendar — see period_number_options and
    # ws-upload-period-select. A caller that states only the number sends no date at all, so
    # this reproduces the same derivation `period_for_end_date` used to do for a MATCHED
    # existing period: it returns the period's own previously STATED ending date, not a guess.
    # A brand-new period (never uploaded to before) has no stated date to reuse, so this stays
    # NULL exactly as an unstated date always has — the out-of-period check below then has
    # nothing to measure against and correctly says nothing, which is the pre-existing behaviour
    # for any period with no known ending date, not a new gap.
    if period_end is None:
        period_end = dict(_stated_period_ends(session, project)).get(period)

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
    # 0030. THE CACHE HAS TWO KEYS: the bytes, and the extraction contract. A stored extraction
    # is served only while the fingerprint it was made under equals the CURRENT fingerprint for
    # its stored type -- `extraction_contract_fingerprint` derives that from the same functions
    # that build the real prompt. NULL (every pre-0030 row) or unequal means the contract has
    # grown since the row was extracted, and the bytes are re-extracted once and the row updated
    # in place, which keeps 0009's identity-by-construction: two PMs uploading identical bytes
    # still read the SAME row. An upload with no contract change still costs no model call.
    jobs: list[dict] = []
    queued: set[str] = set()
    stale: set[str] = set()
    for d in decoded:
        if d["reference"] is not None:
            continue
        if d["sha256"] in queued:
            continue
        held = existing.get(d["sha256"])
        if held is not None:
            current = extraction_contract_fingerprint(held.doc_type or "")
            if held.extraction_contract == current:
                continue
            stale.add(d["sha256"])
        queued.add(d["sha256"])
        jobs.append({"sha256": d["sha256"], "content": d["raw"], "mime_type": d["mime_type"],
                     "filename": d["filename"], "doc_type": d["doc_type"]})

    extractor = _EXTRACTOR_OVERRIDE or build_extractor()
    started = time.monotonic()
    results = extract_many(extractor, jobs) if jobs else []
    elapsed = round(time.monotonic() - started, 3)
    by_hash = {r["sha256"]: r for r in results}

    model_id = getattr(extractor, "model_id", None) or getattr(extractor, "model", "unknown")
    # 0031. WHICH PROVIDER served those weights. A model identifier alone does not say, and the
    # provider is a setting from Run 93 onward, so two stored extractions may come from two
    # different providers with nothing else in the row to tell them apart.
    provider_id = getattr(extractor, "provider", None) or "unknown"
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
        # 0030. A STALE ROW IS REFRESHED IN PLACE, never duplicated: the sha256 is unique by
        # construction and identity of the stimulus is the row, so the re-extraction replaces
        # what the row says the document states. The filename stays as first uploaded, per the
        # column's own rule; everything the model call produced is restamped, fingerprint
        # included, so the next upload of these bytes is a cache hit again.
        if r["sha256"] in stale:
            held = existing[r["sha256"]]
            held.doc_type = r["doc_type"]
            held.extraction = extraction
            held.extraction_model = model_id
            held.extraction_provider = provider_id
            held.classification_confidence = r.get("confidence")
            held.extraction_contract = extraction_contract_fingerprint(r["doc_type"] or "")
            held.extracted_at = func.now()
            continue
        session.add(Document(
            sha256=r["sha256"],
            filename=d["filename"],
            mime_type=d["mime_type"] or None,
            size_bytes=len(d["raw"]),
            content=d["raw"],
            doc_type=r["doc_type"],
            extraction=extraction,
            extraction_model=model_id,
            extraction_provider=provider_id,
            # 0030. The contract this extraction was just made under. What the cache compares.
            extraction_contract=extraction_contract_fingerprint(r["doc_type"] or ""),
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
            extraction_provider=None,
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
        # 0030. A refreshed document PAID for a model call this upload, so it is not "cached":
        # the PM is told it was re-read, and `document_uploads.was_cached` records the cost.
        was_cached = d["sha256"] in existing and d["sha256"] not in stale
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
            # RUN 80, FIX TWO. The fields this document stated but that could not be read --
            # an unrecognised CPARS rating word, a "TBD" where a figure belongs. The document
            # is STORED and everything else in it contributes; these fields are absent, and
            # the PM is told which and why rather than being left to wonder why one measure
            # abstained. Empty for every document that read cleanly.
            "unreadable_fields": [u.get("reason") for u in
                                  (by_hash.get(d["sha256"], {}).get("unreadable") or [])],
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
    # RUN 74. The refusals and the per-document field lists come back rather than being
    # discarded, because the response below has to be able to say what was STORED and not only
    # what was extracted. See `_persist_observations` and the summary block at the end.
    obs_refusals: dict[str, str] = {}
    obs_stored: dict[str, list[str]] = {}
    observations_written = _persist_observations(session, project, period,
                                                 refusals=obs_refusals,
                                                 stored_fields=obs_stored)
    # 0021. The same moment, for the same reason: the schedule is structured data the store
    # holds from the instant the evidence arrives, not something derived at compute time.
    _persist_schedule_activities(session, project, period)
    # 0024/0025. And the risk register and any notice, for the same reason again.
    _persist_project_risks(session, project, period)
    _persist_project_notices(session, project, period)

    # RUN 74. WHAT EACH FILE ACTUALLY STORED, attached to the row the PM reads.
    #
    # Until this run the response asserted `status: "extracted"` and `contributes: true` on the
    # strength of the model having returned SOMETHING, and said nothing whatever about whether a
    # figure reached the observation store. An upload that stored nothing was reported in exactly
    # the same words as one that stored everything, which is the defect the owner named: a
    # success message that cannot fail. `fields_stored` is the field names read back out of the
    # projection that just ran, and `storage_refusal` is the verbatim reason when a document that
    # extracted cleanly nevertheless projected nothing.
    for f, d in zip(files, decoded):
        doc = stored.get(d["sha256"])
        did = doc.document_id if doc is not None else None
        fs = obs_stored.get(did) or []
        f["document_id"] = did
        f["fields_stored"] = list(fs)
        f["fields_stored_count"] = len(fs)
        f["storage_refusal"] = obs_refusals.get(did)
        # An analytical document that was accepted and yet put nothing in the store is NOT a
        # success, whatever the extractor reported. Saying so here is what makes the summary
        # below capable of failing.
        f["stored"] = bool(fs)
        if f["status"] != "failed" and f.get("contributes") and not fs:
            f["note"] = (f.get("note") or "") or (
                "this document was read but no figure from it reached the observation store"
                + (": " + obs_refusals[did] if obs_refusals.get(did) else
                   "; no field it carries is one the analysis stores"))

    stored_nothing = [f["filename"] for f in files
                      if f["status"] != "failed" and f.get("contributes") and not f["stored"]]

    audit(session, "documents_uploaded", participant_id=caller.participant_id,
          project_id=project.legacy_id, period=period, files=len(decoded),
          cached=cached_count, extracted=extracted_count, failed=failed_count,
          extraction_model=model_id, extraction_provider=provider_id)

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
            # RUN 74. `appliedFields` and `documentId` are recorded ON THE EVENT, from the
            # projection that just ran.
            #
            # The Uploaded Documents panel could not previously say which DOCUMENT a figure came
            # from. The event carried no field list, so the panel fell back to inverting
            # `signal_inputs.sources` by doc TYPE — which meant two documents of the same type
            # showed the same field list or both showed none, and, when no computed row existed
            # yet, `sources` was absent and EVERY row rendered blank while the observation store
            # held the figures. The attribution is per document here because `observations` is
            # keyed per document; the panel now has the honest answer instead of a type-level
            # approximation of it.
            fresh = _append_event(fresh, "signals_extracted",
                                  docType=f["doc_type"], fileName=f["filename"],
                                  period=period, wasCached=f["was_cached"],
                                  documentId=f.get("document_id"),
                                  appliedFields=list(f.get("fields_stored") or []))
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
            # RUN 74. THE FIGURES THAT REACHED STORAGE. `extracted` above counts model calls,
            # not stored evidence, and reporting it alone is what let an upload that stored
            # nothing read as a complete success. These three can all be zero on an upload
            # whose every other count is healthy, which is the point of them.
            "observations_written": observations_written,
            "documents_that_stored_a_figure": sum(1 for f in files if f["stored"]),
            "documents_that_stored_nothing": len(stored_nothing),
        },
        # Named, not just counted: "3 documents stored nothing" is not actionable, "these three
        # stored nothing" is.
        "stored_nothing_filenames": stored_nothing,
        # False when an analytical document was accepted and stored no figure. The caller must
        # not read `ok` as "the evidence landed" — `ok` means the request was served.
        "all_accepted_documents_stored": not stored_nothing,
        "date_mismatches": date_mismatches,
        "unmapped_filenames": unmapped,
        "extraction_seconds": elapsed,
        "extraction_model": model_id,
        "extraction_provider": provider_id,
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
        signal_inputs = select_signal_inputs(
            observations, _derive_cutoff(period_docs, None),
            # RUN 45. The same retrieval the compute path runs, so this display cannot show a
            # figure the computation would not have used.
            carried=_identity_observations_before(session, project, resp["period"]))
    except Exception as exc:  # noqa: BLE001 — display only; the document is already stored
        log.warning("extractsignals could not assemble signalInputs for display: %s", exc)

    return {
        "ok": True,
        "project_id": resp.get("project_id"),
        "period": resp.get("period"),
        "docType": first.get("doc_type"),
        "applied": applied,
        # RUN 80. The fields this document stated that could not be read. Carried onto the
        # legacy single-document response for the same reason it is carried onto the upload
        # response: the document is stored and contributes, and the person who uploaded it is
        # told which of its figures were not taken and why, rather than being left to infer it
        # from a measure that abstained. Empty for a document that read cleanly.
        "unreadable_fields": first.get("unreadable_fields") or [],
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
        "extraction_provider": resp.get("extraction_provider"),
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
              DocumentUpload.supersedes_document_id,
              DocumentUpload.archived_at, DocumentUpload.archived_by)
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

    # 0027. ARCHIVED DOCUMENTS ARE STILL READABLE, on the same argument 0013 made for
    # superseded ones and written into `document_uploads.archived_at`: the document control
    # withdraws evidence from the live figures, it does not destroy it. `contributes` is false
    # because they no longer reach assembly; `document_id` is carried so the reader can fetch
    # the retained bytes from `/documents/{document_id}/content`, which is the proof that
    # archiving kept them. This list is what the document control dialog reads to show the
    # archive back.
    archived_ids = _archived_document_ids(session, project, period)
    archived_docs = [
        {"document_id": r[1], "filename": r[4], "doc_type": r[5] or UNMAPPED,
         "contributes": False,
         "uploaded_at": r[2].isoformat() if r[2] else None,
         "was_cached": r[3],
         "archived_at": r[7].isoformat() if r[7] else None,
         "archived_by": r[8]}
        for r in upload_rows if r[1] in archived_ids
    ]
    archived_docs.sort(key=lambda a: (a["archived_at"] or "", a["filename"]))

    have = {d["doc_type"] for d in documents}

    # 0014. THE BASELINE AND ITS AMENDMENTS, BOTH READABLE. The original contract baseline
    # persists as PERMANENT observations (a change order can no longer destroy it), and every
    # executed change order is an amendment layered on it. Read from the observation store,
    # across all periods up to this one, because the baseline is a fact about the project,
    # not about one period's uploads.
    #
    # RUN 78. `withdrawn_at IS NULL`. This query is the one LIVE surface in this repository that
    # reads the observation store directly, and until this run it read it UNFILTERED: an
    # archived contract award still supplied "the original contract baseline" on the documents
    # panel, and an archived change order still appeared in the amendments list, after the
    # document control had withdrawn both and after a recompute had correctly removed them from
    # every module. The computation path was clean; this reader was not. Filtering on the 0029
    # mark rather than re-deriving archived ids per period is deliberate -- the mark is scoped
    # to (project, period, document) already, and this query deliberately spans periods.
    baseline_rows = session.scalars(
        select(Observation).where(
            Observation.project_id == project.id,
            Observation.period <= period,
            Observation.withdrawn_at.is_(None),
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
        # 0027. Withdrawn by the document control, kept out of computation and kept readable.
        # Empty on every period where nothing has been archived, which is the ordinary case.
        "archived": archived_docs,
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

    # RUN 75, RULING 1: "Compute over a period that holds no documents produces nothing. Not an
    # empty row, not a null status. Nothing."
    #
    # `_resolve_period` above accepts a period NUMBER from the caller for an operational
    # project, and the period picker offers the periods the project holds PLUS THE NEXT ONE, so
    # pressing compute on that next period reached here with a period holding no document at
    # all. Nothing checked. `_compute_and_store` ran over an empty document set and wrote a live
    # row with no status and no module results -- and because that row was live, it became the
    # project's latest computed period and the detail page opened on it and showed nothing.
    #
    # THE SAME PREDICATE COVERS THE OTHER DIRECTION. `_period_holds_evidence` asks the LIVE
    # document set, so a period whose documents have all been archived through the document
    # control is equally without evidence. There the answer is not a refusal -- a result is
    # standing that no longer has anything behind it -- so the standing row is WITHDRAWN and no
    # replacement is written, and the project falls back to the latest period that still holds
    # something.
    if not _period_holds_evidence(session, project, period):
        if existing is None:
            return err(f"period {period} holds no documents, so there is nothing to compute. "
                       f"Upload this period's documents first.")
        withdrawn_id = _withdraw_live_result(session, existing)
        audit(session, "period_result_withdrawn", participant_id=caller.participant_id,
              project_id=project.legacy_id, period=period,
              superseded_result_id=existing.result_id, superseded_by=withdrawn_id,
              reason="every document in this period has been withdrawn, so the result it was "
                     "derived from no longer has evidence behind it",
              via="projectcompute")
        session.commit()
        return {
            "ok": True,
            "project_id": project.legacy_id,
            "period": period,
            "recomputed": False,
            "withdrawn": True,
            "superseded_result_id": existing.result_id,
            "documents": 0,
            "note": f"period {period} no longer holds any document, so its result has been "
                    f"withdrawn rather than recomputed. Nothing was written in its place.",
            "server_time": now_iso(),
        }

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
        # RUN 75, RULING 1, applied on this path too. `periods` above is read from
        # `DocumentUpload`, which still carries a row for a period whose documents have all been
        # ARCHIVED -- so this loop could reach `_compute_and_store` with an empty live document
        # set and write exactly the row the ruling forbids. `_period_holds_evidence` asks the
        # live set instead. No evidence, no row: a standing result is withdrawn, and a period
        # that never had one is skipped.
        if not _period_holds_evidence(session, project, period):
            if existing is None:
                outcomes.append({"period": period, "computed": False, "skipped": True,
                                 "note": "this period holds no documents, so nothing was "
                                         "computed for it"})
                continue
            withdrawn_id = _withdraw_live_result(session, existing)
            audit(session, "period_result_withdrawn", participant_id=caller.participant_id,
                  project_id=project.legacy_id, period=period,
                  superseded_result_id=existing.result_id, superseded_by=withdrawn_id,
                  reason="every document in this period has been withdrawn, so the result it "
                         "was derived from no longer has evidence behind it",
                  via="projectcomputeall")
            outcomes.append({"period": period, "computed": False, "skipped": False,
                             "withdrawn": True,
                             "superseded_result_id": existing.result_id,
                             "note": "this period no longer holds any document, so its result "
                                     "was withdrawn and nothing was written in its place"})
            earlier_recomputed = True
            continue
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
    # RUN 79. THE READINGS ARE THE SOURCE. Built for the period this row states, so the
    # projection and the row can never describe two different periods.
    view = _result_view(row, include_recommendation=visible, package=package,
                        project_legacy_id=project.legacy_id,
                        spec=spec_projection.projection(session, project.id, row.period))

    # WHAT THE PERIOD'S DOCUMENTS ESTABLISH, read at display time and not frozen into the row.
    # Read from the period's LIVE documents (superseded revisions already excluded), so a
    # replaced document stops speaking the moment it is replaced, which a value copied onto the
    # stored result at compute time would not do.
    #
    # NOT GATED BY THE REVEAL. This is evidence, in the same class as `signal_inputs`, which a
    # participant is shown BEFORE their preliminary judgment because forming one is the point.
    # It carries counts read out of documents and names the documents; it carries no
    # recommendation, no course, no action and no ranking -- `document_evidence.ranking` is a
    # refusal with its reason, never a preference.
    #
    # THAT CLAIM IS CHECKED, and not by the T4 prose scanner: that scanner runs over the
    # decision-state endpoint and was measured NOT to reach this block (a planted "escalate to
    # management review" in a findings sentence left it green). The check that does hold this
    # to account is `test_period_picker_and_evidence.py` section 6, which scans every sentence
    # this table can generate against the same leak vocabulary and is proven able to fail.
    view["document_evidence"] = document_evidence(
        _period_documents(session, project, row.period),
        risks=_period_risks(session, project, row.period),
        notices=_period_notices(session, project, row.period))

    return {
        "ok": True,
        "project_id": project.legacy_id,
        "result": view,
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

    # RUN 75, RULING 1, applied on the admin path too, so no route can leave an evidence-free
    # row live. Recomputing a period whose documents have all been withdrawn would write a row
    # with no status and no module results; the standing row is withdrawn instead and nothing is
    # written in its place.
    if not _period_holds_evidence(session, project, period):
        withdrawn_id = _withdraw_live_result(session, old)
        audit(session, "period_result_withdrawn", participant_id=caller.participant_id,
              project_id=project.legacy_id, period=period, reason=reason,
              superseded_result_id=old.result_id, superseded_by=withdrawn_id,
              via="adminrecompute")
        session.commit()
        return {"ok": True, "project_id": project.legacy_id, "period": period,
                "recomputed": False, "withdrawn": True, "reason": reason,
                "superseded_result_id": old.result_id,
                "note": f"period {period} holds no documents, so its result was withdrawn "
                        f"rather than recomputed. Nothing was written in its place.",
                "server_time": now_iso()}

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


def a_projectperiodfordate(session: Session, payload: dict, secret: str,
                           ttl: int) -> dict[str, Any]:
    """
    Any active member. Which period a chosen ending DATE names on this project. READS ONLY.

    This exists so the calendar picker can show the person which period their date lands in
    BEFORE they upload, using the same `period_for_end_date` the upload itself calls rather
    than a second copy of the rule in JavaScript. A preview that can disagree with the write it
    previews is a defect waiting to happen, so there is one function and two callers.

    Nothing is written and nothing is audited as an evidence view: this answers a question about
    the project's own period boundaries, not about any document's contents.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    project, member, problem = require_member(session, caller, payload, "projectperiodfordate")
    if problem:
        return problem
    chosen = _parse_iso_date(payload.get("period_end") or payload.get("periodEnd"))
    if chosen is None:
        return err("period_end must be a date in YYYY-MM-DD form")

    resolved = period_for_end_date(session, project, chosen)

    # A research project's period is the study's to advance, not the picker's. Say so rather
    # than previewing a number the upload would then override: `_resolve_period` ignores the
    # payload entirely where an assignment exists, and a preview that hid that would be a lie.
    assignment, _decision, _package = project_decision_state(session, project)
    if assignment is not None:
        from .research_decision import current_period
        derived = _period_number(current_period(session, assignment))
        if derived is not None:
            return {
                "ok": True, "project_id": project.legacy_id,
                "period": derived, "period_end": chosen.isoformat(), "existing": True,
                "server_derived": True,
                "basis": (f"period {derived} is set by this project's study sequence, not by "
                          f"the date picked here"),
                "server_time": now_iso(),
            }

    return {
        "ok": True,
        "project_id": project.legacy_id,
        "period": resolved["period"],
        "period_end": resolved["period_end"].isoformat(),
        "existing": resolved["existing"],
        "server_derived": False,
        "basis": resolved["basis"],
        "server_time": now_iso(),
    }


def a_projectperiods(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Any active member. READS ONLY. Which periods this project already holds, and the next
    number the picker should offer for a new one.

    THE PICKER OFFERS A NUMBER, BOUNDED TO WHAT EXISTS PLUS ONE NEW ONE. Periods are
    sequential bookkeeping the platform assigns in order (`_highest_period` + 1 is always the
    next one a new upload opens); a free-text number field would let a person open period 9
    while periods 2-8 stay forever empty, which is a gap nothing here is built to explain. So
    this lists every period the project already holds evidence for, each with its stated ending
    date where one is on file, plus the one new period a person can open next. A research
    project's period is set by its study sequence, not by this list, and that is called out
    rather than silently offered as a choice.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    project, member, problem = require_member(session, caller, payload, "projectperiods")
    if problem:
        return problem

    ends = dict(_stated_period_ends(session, project))
    highest = _highest_period(session, project)
    # RUN 48, RULING 1. Which periods hold a LIVE COMPUTED RESULT, read from the result table.
    # Reported as its own list rather than as a key on each period row: the row shape here is
    # the picker's contract and `test_period_number_picker.py` asserts it exactly, so adding a
    # key to it would have changed a contract this run has no order to change.
    computed = set(_computed_periods(session, project))
    periods = [{"period": p, "period_end": ends.get(p).isoformat() if ends.get(p) else None}
               for p in range(1, highest + 1)]

    assignment, _decision, _package = project_decision_state(session, project)
    server_derived = None
    if assignment is not None:
        from .research_decision import current_period
        server_derived = _period_number(current_period(session, assignment))

    return {
        "ok": True,
        "project_id": project.legacy_id,
        "periods": periods,
        "next_period": highest + 1,
        # RUN 48, RULING 1. The latest period for which computed results exist, or null when
        # this project has never been computed. READ ONLY, derived, and never a substitute for
        # a period the caller stated.
        "computed_periods": sorted(computed),
        "latest_computed_period": _latest_computed_period(session, project),
        "server_derived": server_derived,
        "server_time": now_iso(),
    }


def a_projectdocumentarchive(session: Session, payload: dict, secret: str,
                             ttl: int) -> dict[str, Any]:
    """
    PM only. THE DOCUMENT CONTROL: withdraw a named set of documents from one reporting period.

    WHAT THIS DOES AND DOES NOT DO. It marks `document_uploads.archived_at/archived_by` for the
    (project, period, document) rows named, and writes ONE append-only `documents_archived`
    audit row naming what was archived, from which period, when, by whom, which fields each
    document was withdrawing, and the exact confirmation sentence the person was shown.

    IT DOES NOT RECOMPUTE. Archiving STAGES the withdrawal; recalculating applies it. The live
    `computed_results` row is left exactly as it stands, which is why the response reports
    `recomputed: false` and names the control that applies it. A separate press of "Generate
    signals for every period" (`projectcomputeall` -> `projectcompute`) finds the period stale —
    `_period_is_stale` compares the stored result's (document_id, sha256) set against the
    period's CURRENT live set from `_period_documents`, and the archived rows have just left
    that set — so it recomputes rather than skipping. Nothing here has to tell it to.

    NOTHING IS DESTROYED. `documents.content` is untouched, `/documents/{id}/content` keeps
    serving the bytes, and `a_projectuploadstatus` lists the archived rows under `archived`.

    ONLY THE NAMED DOCUMENTS. Every id is checked against a live upload row in THIS project and
    THIS period before anything is written, and the whole request is refused if any one of them
    fails. A partially-applied withdrawal would leave the audit row describing something other
    than what happened.

    THE FIELDS WITHDRAWN are read by running `emit_observations` over the document exactly as
    `_compute_and_store` does, so what the record names is what computation would actually have
    lost — not a guess assembled from `doc_type`.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    project, member, problem = require_member(session, caller, payload, "projectdocumentarchive")
    if problem:
        return problem
    problem = _refuse_unless_pm(session, caller, member, project, "projectdocumentarchive")
    if problem:
        return problem
    # THE PERIOD IS THE ONE THE PERSON PICKED, and this deliberately does NOT go through
    # `_resolve_period`. That helper derives the period from the research assignment and
    # IGNORES the payload, which is right for an UPLOAD — a participant must not write new
    # evidence into a period they have not reached — and wrong here. This action withdraws
    # evidence that is ALREADY in a stated period, the owner's specification is a dropdown from
    # which the person chooses that period, and an earlier period is exactly the case the
    # control exists for. Nothing new can be reached by choosing a period: every named document
    # is checked against an existing upload row in THIS project and THAT period below, so the
    # only thing the number selects is which of the project's own rows may be marked.
    period = _period_number(payload.get("period"))
    if period is None or period < 1:
        return err("choose the reporting period the documents were uploaded to")

    raw_ids = payload.get("document_ids")
    if not isinstance(raw_ids, list) or not raw_ids:
        return err("name at least one document to archive")
    wanted = [str(x) for x in raw_ids if str(x or "").strip()]
    if not wanted:
        return err("name at least one document to archive")
    if len(set(wanted)) != len(wanted):
        return err("the same document was named more than once")

    confirmation = str(payload.get("confirmation") or "").strip()
    if not confirmation:
        # RULING 4 of the order: the confirmation is RECORDED. A request that carries no
        # confirmation sentence cannot produce an audit row that answers "what did the
        # confirmation say", so it is refused rather than audited with a blank.
        return err("the confirmation shown to the person must be supplied and recorded")

    rows = session.scalars(
        select(DocumentUpload).where(
            DocumentUpload.project_id == project.id,
            DocumentUpload.period == period,
            DocumentUpload.document_id.in_(wanted),
        )
    ).all()
    by_id = {r.document_id: r for r in rows}
    missing = [d for d in wanted if d not in by_id]
    if missing:
        return err(f"{len(missing)} document(s) are not uploaded to period {period} of this "
                   f"project and were not archived")
    already = [d for d in wanted if by_id[d].archived_at is not None]
    if already:
        return err(f"{len(already)} document(s) are already archived; nothing was changed")

    # The fields each named document is withdrawing, read the way computation reads them.
    live_before = {d["document_id"]: d for d in _period_documents(session, project, period)}
    now = datetime.now(timezone.utc)
    withdrawn: list[dict] = []
    for doc_id in wanted:
        row = by_id[doc_id]
        entry = live_before.get(doc_id)
        fields: list[str] = []
        if entry is not None:
            fields = sorted({str(o.get("field")) for o in emit_observations(entry)
                             if o.get("field")})
        doc = session.get(Document, doc_id)
        withdrawn.append({
            "document_id": doc_id,
            "filename": doc.filename if doc else None,
            "sha256": doc.sha256 if doc else None,
            "doc_type": (doc.doc_type if doc else None) or UNMAPPED,
            # Empty where the document was not in the live set to begin with (superseded), or
            # where it contributes no mapped observation. Stated, never inferred.
            "fields_withdrawn": fields,
            "was_live": entry is not None,
        })
        row.archived_at = now
        row.archived_by = caller.participant_id

    result = _live_result(session, project, period)

    # RUN 78. THE AUDIT ROW IS BUILT HERE RATHER THAN THROUGH `audit`, for one reason: the
    # observations this action withdraws must name WHICH archive action withdrew them, and
    # `audit` does not hand back the event it appended. Nothing else about the row differs --
    # same event_type, same metadata, same append-only table, same server-side timestamp.
    archive_event = AuditEvent(
        participant_id=caller.participant_id,
        event_type="documents_archived",
        event_metadata={
            "project_id": project.legacy_id, "period": period,
            "archived_by": caller.participant_id,
            "archived_at": now.isoformat(),
            "document_count": len(withdrawn),
            "documents": withdrawn,
            "fields_withdrawn": sorted({f for w in withdrawn for f in w["fields_withdrawn"]}),
            "confirmation": confirmation,
            "live_result_id": result.result_id if result else None,
            "recomputed": False,
            "note": ("the withdrawal is staged; the live figures do not change until the "
                     "project is recalculated"),
        },
    )
    session.add(archive_event)
    session.flush()

    # RUN 78. THE OBSERVATION STORE IS TOLD, AND NOTHING IS DELETED.
    #
    # `observations` is append-only and `_persist_observations` projects every upload in the
    # period, archived ones included -- correct for an audit store, and the reason the
    # computation path's exclusion at `_period_documents` was never enough to make the TABLE
    # truthful. The rows for the documents just archived are MARKED withdrawn, in place, with
    # the archive's own timestamp, the participant who ran it, and the id of the audit row
    # above. Their values are untouched and they stay readable, which is what section 3 of the
    # order requires and what makes "was this figure withdrawn, and by which action" answerable
    # without a join.
    #
    # SCOPED TO (project, period, document), the same scope the archive mark itself has: the
    # same bytes may be live evidence in another project or another period of this one.
    marked = session.execute(
        sa_update(Observation)
        .where(Observation.project_id == project.id,
               Observation.period == period,
               Observation.document_id.in_(wanted),
               Observation.withdrawn_at.is_(None))
        .values(withdrawn_at=now, withdrawn_by=caller.participant_id,
                withdrawn_by_event_id=archive_event.event_id)
    ).rowcount
    archive_event.event_metadata = dict(archive_event.event_metadata or {},
                                        observations_withdrawn=marked)
    session.commit()
    return {
        "ok": True,
        "project_id": project.legacy_id,
        "period": period,
        "archived": withdrawn,
        "archived_at": now.isoformat(),
        "archived_by": caller.participant_id,
        "confirmation": confirmation,
        "recomputed": False,
        "note": ("Archived. The extracted fields are withdrawn from this period's live "
                 "document set. The stored figures do not change until you recalculate."),
        "server_time": now_iso(),
    }


def a_projectdocumentcontrol(session: Session, payload: dict, secret: str,
                             ttl: int) -> dict[str, Any]:
    """
    Any active member. READS ONLY. Everything the document control dialog shows, in one call.

    THREE THINGS, and no fourth:
      1. `periods` — every reporting period this project holds uploads for, each with its LIVE
         documents (the ones the dialog offers to archive, with the fields each one is
         currently supplying) and the ones already archived.
      2. `record` — the append-only `documents_archived` audit rows for this project, newest
         first. This is how the archive record is read back.

    IT DOES NOT GO THROUGH `_resolve_period`, for the reason written at
    `a_projectdocumentarchive`: that helper derives one period from the research assignment and
    ignores the payload, which would leave the owner's period dropdown with exactly one usable
    entry. This lists them all and writes nothing, so nothing is reachable that the project does
    not already hold.

    The audit rows are filtered in Python on the JSON metadata rather than in SQL because
    `event_metadata` is a portable JSON column and this platform runs on both SQLite (dev) and
    Postgres; a JSON path predicate would be one more thing that behaves differently between
    them. The `event_type` filter does the real narrowing.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    project, member, problem = require_member(session, caller, payload, "projectdocumentcontrol")
    if problem:
        return problem

    upload_rows = session.execute(
        select(DocumentUpload.period, DocumentUpload.document_id, DocumentUpload.uploaded_at,
               DocumentUpload.archived_at, DocumentUpload.archived_by,
               Document.filename, Document.doc_type)
        .join(Document, Document.document_id == DocumentUpload.document_id)
        .where(DocumentUpload.project_id == project.id)
    ).all()
    meta = {r[1]: r for r in upload_rows}
    periods_held = sorted({int(r[0]) for r in upload_rows if r[0] is not None})

    periods: list[dict] = []
    for p in periods_held:
        live = _period_documents(session, project, p)
        documents = []
        for d in live:
            row = meta.get(d["document_id"])
            documents.append({
                "document_id": d["document_id"],
                "filename": d["filename"],
                "doc_type": d["doc_type"],
                "contributes": is_mapped(d["doc_type"]),
                "uploaded_at": (row[2].isoformat() if row and row[2] else None),
                # What computation would lose if this one were archived — read by running the
                # same emitter `_compute_and_store` runs, not guessed from the doc_type.
                "fields": sorted({str(o.get("field")) for o in emit_observations(d)
                                  if o.get("field")}),
            })
        documents.sort(key=lambda x: (x["filename"] or "", x["document_id"]))
        archived = [
            {"document_id": r[1], "filename": r[5], "doc_type": r[6] or UNMAPPED,
             "archived_at": r[3].isoformat() if r[3] else None, "archived_by": r[4]}
            for r in upload_rows
            if int(r[0] or 0) == p and r[3] is not None
        ]
        archived.sort(key=lambda x: (x["archived_at"] or "", x["filename"] or ""))
        periods.append({"period": p, "documents": documents, "archived": archived})

    rows = session.scalars(
        select(AuditEvent).where(AuditEvent.event_type == "documents_archived")
        .order_by(AuditEvent.server_ts.desc())
    ).all()
    record = []
    for r in rows:
        m = r.event_metadata or {}
        if str(m.get("project_id")) != str(project.legacy_id):
            continue
        record.append({
            "event_id": r.event_id,
            "server_ts": r.server_ts.isoformat() if r.server_ts else None,
            "participant_id": r.participant_id,
            "period": m.get("period"),
            "archived_at": m.get("archived_at"),
            "archived_by": m.get("archived_by"),
            "document_count": m.get("document_count"),
            "documents": m.get("documents"),
            "fields_withdrawn": m.get("fields_withdrawn"),
            "confirmation": m.get("confirmation"),
        })

    return {
        "ok": True,
        "project_id": project.legacy_id,
        "periods": periods,
        "record": record,
        "server_time": now_iso(),
    }


DOCUMENT_ACTIONS: dict[str, Callable[[Session, dict, str, int], dict]] = {
    "projectupload": a_projectupload,
    # The calendar picker's read-only preview: a date in, the period it names out. Same rule the
    # upload applies, so the number shown is the number written. Kept for callers still keyed on
    # a date (workspace.js's Period documents panel offers a date field of its own).
    "projectperiodfordate": a_projectperiodfordate,
    # The upload modal's period picker: which periods this project already holds, and the next
    # number it can open. READ ONLY.
    "projectperiods": a_projectperiods,
    # The legacy one-document ingest, adapted onto projectupload. See a_extractsignals for why
    # it is an adapter and not a second extraction path.
    "extractsignals": a_extractsignals,
    "projectuploadstatus": a_projectuploadstatus,
    "projectcompute": a_projectcompute,
    # Part 5. Every period the project holds documents for, computed in order, oldest first.
    "projectcomputeall": a_projectcomputeall,
    "projectresults": a_projectresults,
    "adminrecompute": a_adminrecompute,
    # RUN 71. The document control: withdraw named documents of one period from the live
    # figures, retaining the bytes and recording the withdrawal. Does NOT recompute — that is
    # "Generate signals for every period" (projectcomputeall), pressed separately.
    "projectdocumentarchive": a_projectdocumentarchive,
    # RUN 71. What the document control dialog reads: the periods that hold documents, each
    # period's live and archived documents, and the archive record read back out of the
    # append-only audit table. READ ONLY.
    "projectdocumentcontrol": a_projectdocumentcontrol,
}
