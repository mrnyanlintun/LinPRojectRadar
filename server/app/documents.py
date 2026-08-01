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
import time
from datetime import date, datetime, timezone
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from .extraction_client import build_extractor, extract_many
from .extraction_fields import UNMAPPED, is_mapped
from .extraction_merge import assemble_signal_inputs, assembly_report
from .facade import err, now_iso
from .models import Project
from .research_identity import audit, resolve_caller
from .research_membership import (
    ROLE_PM,
    project_decision_state,
    recommendation_visible,
    require_member,
)
from .research_models import ComputedResult, Decision, Document, DocumentUpload, new_ulid

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
        return err("not authorised: only the project's PM may perform this action")
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
        return None, err("File too large — maximum ~3 MB. Please compress the PDF.")
    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        return None, err("dataBase64 is not valid base64")
    if not raw:
        return None, err("decoded file is empty")
    if len(raw) > MAX_FILE_BYTES:
        return None, err("File too large — maximum 20 MB")
    return raw, None


def _period_documents(session: Session, project: Project, period: int) -> list[dict]:
    """
    The period's document SET, in the shape `assemble_signal_inputs` expects.

    One entry per distinct document. The unique index on (project, period, document) already
    makes a re-upload a no-op, so this is a set by construction — which is what makes assembly
    idempotent and therefore a recompute reproducible.
    """
    rows = session.execute(
        select(Document)
        .join(DocumentUpload, DocumentUpload.document_id == Document.document_id)
        .where(DocumentUpload.project_id == project.id, DocumentUpload.period == period)
    ).scalars().all()
    seen: set[str] = set()
    out: list[dict] = []
    for d in rows:
        if d.sha256 in seen:
            continue
        seen.add(d.sha256)
        out.append({"sha256": d.sha256, "doc_type": d.doc_type or UNMAPPED,
                    "filename": d.filename, "extraction": d.extraction or {}})
    return out


def _live_result(session: Session, project: Project, period: int) -> ComputedResult | None:
    return session.scalars(
        select(ComputedResult).where(
            ComputedResult.project_id == project.id,
            ComputedResult.period == period,
            ComputedResult.superseded_by.is_(None),
        )
    ).first()


def _derive_cutoff(documents: list[dict], reuse: ComputedResult | None) -> date:
    """
    `period_cutoff` replaces the wall clock inside the analytical layer (only C1.2 Data
    Timeliness reads it, simulation/models_dq.py:60).

    A RECOMPUTE REUSES THE SUPERSEDED ROW'S CUTOFF. That is what makes "recomputing on identical
    inputs produces identical module_results" true rather than nearly true: derive it from the
    clock instead and C1.2 drifts by however many days elapsed between the two runs, and the
    guarantee quietly becomes false.

    On a first compute it is the latest document date in the period — the as-of date the
    evidence itself establishes — falling back to the server date when no document carries one.
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
    return latest or datetime.now(timezone.utc).date()


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
    from .simulation import compute_project, compute_portfolio

    documents = _period_documents(session, project, period)
    si = assemble_signal_inputs(documents)
    cutoff = _derive_cutoff(documents, reuse_cutoff_from)

    run = compute_project(si, project.legacy_id, f"P{period}", cutoff)

    # Portfolio snapshot: every other project's most recent live result.
    others = session.scalars(
        select(ComputedResult).where(ComputedResult.superseded_by.is_(None))
    ).all()
    vectors: list[dict] = []
    by_project: dict[Any, ComputedResult] = {}
    for r in others:
        prev = by_project.get(r.project_id)
        if prev is None or (r.period or 0) > (prev.period or 0):
            by_project[r.project_id] = r
    for pid, r in by_project.items():
        legacy = session.get(Project, pid)
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
    snapshot = compute_portfolio(vectors, project.legacy_id, None, cutoff)

    row = ComputedResult(
        result_id=result_id or new_ulid(),
        project_id=project.id,
        period=period,
        signal_inputs=si,
        module_results=run.get("modules"),
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
    return {"row": row, "run": run, "documents": documents}


# Keys inside a MODULE result that name or rank a course of action. Found by grepping the
# analytical layer, which emits them from two modules:
#   models_gov.py:633-634   B4.4 Regret Minimization -> "recommended_action", "expected_regret"
#   models_decision.py:115,150  B1.1 / B3.1           -> "action"
#
# These are recommendations. Returning them to a member before their PM has locked the period's
# preliminary judgment would defeat the reveal gate just as surely as returning the package
# itself — "the model says investigate" is the treatment, whatever field it arrives in. B8's
# gate covers the package; nothing covered the module output, because until B7b nothing read
# the analytical layer at all.
_ACTION_KEYS = frozenset({"recommended_action", "expected_regret", "action"})


def _redact_module_actions(modules) -> list:
    """
    Strip action-bearing keys from module results for a withheld read.

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
        "category_statuses": row.category_statuses,
        "project_status": row.project_status,
        "portfolio_snapshot": row.portfolio_snapshot,
        "simulation_version": row.simulation_version,
        "seed": row.seed,
        "period_cutoff": str(row.period_cutoff) if row.period_cutoff else None,
        "computed_at": row.computed_at.isoformat() if row.computed_at else None,
        "superseded_by": row.superseded_by,
    }
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
        })

    # Which hashes do we already hold? This is the cache, and it is a single query.
    hashes = {d["sha256"] for d in decoded}
    existing = {
        d.sha256: d for d in session.scalars(
            select(Document).where(Document.sha256.in_(hashes))
        ).all()
    }

    # Extract only what is genuinely new, and only ONCE per distinct hash within this batch.
    jobs: list[dict] = []
    queued: set[str] = set()
    for d in decoded:
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
        session.add(Document(
            sha256=r["sha256"],
            filename=d["filename"],
            mime_type=d["mime_type"] or None,
            size_bytes=len(d["raw"]),
            content=d["raw"],
            doc_type=r["doc_type"],
            extraction=r["extraction"],
            extraction_model=model_id,
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
    cached_count = extracted_count = failed_count = 0
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
        if was_cached:
            cached_count += 1
        else:
            extracted_count += 1
        if doc.document_id not in already:
            session.add(DocumentUpload(project_id=project.id, period=period,
                                       document_id=doc.document_id,
                                       uploaded_by=caller.participant_id,
                                       was_cached=was_cached))
            already.add(doc.document_id)
        mapped = is_mapped(doc.doc_type or "")
        files.append({
            "filename": d["filename"],
            "status": "matched" if was_cached else "extracted",
            "doc_type": doc.doc_type,
            "was_cached": was_cached,
            # Reported explicitly so the PM can see which documents did not contribute rather
            # than assuming a successful upload meant a contributing one.
            "contributes": mapped,
            "note": None if mapped else
                    "document type not mapped to any signal input; stored, but contributes "
                    "nothing to the analysis",
        })

    audit(session, "documents_uploaded", participant_id=caller.participant_id,
          project_id=project.legacy_id, period=period, files=len(decoded),
          cached=cached_count, extracted=extracted_count, failed=failed_count,
          extraction_model=model_id)
    session.commit()

    unmapped = [f["filename"] for f in files if f["doc_type"] == UNMAPPED]
    return {
        "ok": True,
        "project_id": project.legacy_id,
        "period": period,
        "files": files,
        "summary": {
            "total": len(decoded),
            "recognised": cached_count,
            "extracted": extracted_count,
            "failed": failed_count,
            "unmapped": len(unmapped),
        },
        "unmapped_filenames": unmapped,
        "extraction_seconds": elapsed,
        "extraction_model": model_id,
        "server_time": now_iso(),
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
              DocumentUpload.was_cached)
        .join(DocumentUpload, DocumentUpload.document_id == Document.document_id)
        .where(DocumentUpload.project_id == project.id, DocumentUpload.period == period)
    ).all()
    by_sha = {sha: (doc_id, uploaded_at, was_cached)
             for sha, doc_id, uploaded_at, was_cached in upload_rows}

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
    have = {d["doc_type"] for d in documents}

    audit(session, "project_read", participant_id=caller.participant_id,
          action="projectuploadstatus", project_id=project.legacy_id,
          project_role=member.project_role)
    session.commit()
    return {
        "ok": True,
        "project_id": project.legacy_id,
        "period": period,
        "documents": present,
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

    Refuses to overwrite: if a live result already exists, this returns it untouched and points
    the caller at `adminrecompute`. Replacing a result is an append-only, audited, reason-bearing
    operation and must not be reachable by calling compute twice.
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
        return {"ok": True, "project_id": project.legacy_id, "period": period,
                "result_id": existing.result_id, "recomputed": False,
                "note": "a computed result already exists for this period; use adminrecompute "
                        "to replace it"}

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
    visible = recommendation_visible(decision)

    audit(session, "project_read", participant_id=caller.participant_id,
          action="projectresults", project_id=project.legacy_id,
          project_role=member.project_role, result_id=row.result_id,
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
    "projectuploadstatus": a_projectuploadstatus,
    "projectcompute": a_projectcompute,
    "projectresults": a_projectresults,
    "adminrecompute": a_adminrecompute,
}
