"""
Run 76. The per-category call, and the store for what it read.

WHAT THIS MODULE OWNS. Accepting a press of one category's button, finding that project-period's
stored figures, applying that category's WRITTEN SPECIFICATION to them, and STORING the result.
Section 12.7 of the Run 76 order fails the run for a result computed and not stored, so nothing
here computes and throws away.

WHAT IT DOES NOT OWN, and the boundary is the owner's ruling at section 4:

  - FUSION. `spec_apply` calls `fusion.worst_band`, in Python, and this module never decides a
    status itself.
  - THE RECOMMENDATION CHECKS. Untouched.
  - EXTRACTION, STORAGE OF FIGURES, PERIOD BINDING. Untouched; section 7 says leave them alone.

WHERE THE FIGURES COME FROM. `computed_results.signal_inputs` for the (project, period) -- the
stored, provenance-carrying figures the order's section 1 complains were "correct, and unread by
the layer above". This module reads them and hands them, whole, to the specification. It does not
select, filter or rename a field: a specification names its inputs by their exact `signal_inputs`
field names, so anything the specification can name is in front of it.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .facade import err
from .research_models import SpecificationReading
from .simulation import spec_apply as sa
from .simulation.models import SIMULATION_VERSION


def _live_reading(session: Session, project_id: str, period: int,
                  category_key: str) -> SpecificationReading | None:
    return session.scalars(
        select(SpecificationReading)
        .where(SpecificationReading.project_id == project_id,
               SpecificationReading.period == period,
               SpecificationReading.category_key == category_key,
               SpecificationReading.superseded_by.is_(None))
        .order_by(SpecificationReading.created_at.desc())
    ).first()


def _spec_sha(category_key: str) -> str | None:
    p = sa.specification_path(category_key)
    if p is None or not p.is_file():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


def store_reading(session: Session, project_id: str, period: int, row: dict) -> SpecificationReading:
    """Append the reading and supersede the previous live one. Never updates a stored row."""
    category_key = row["category"]
    previous = _live_reading(session, project_id, period, category_key)
    stored = SpecificationReading(
        project_id=project_id,
        period=period,
        category_key=category_key,
        state=row["state"],
        status=row.get("status"),
        counts=row.get("counts"),
        modules=row.get("modules"),
        reason=row.get("reason"),
        missing_upstream=row.get("missing_upstream") or [],
        # NOT NULL by design. A reading whose origin is unknown is worse than no reading, and
        # "recorded" must never be mistaken for a live model call.
        served_by=row.get("served_by") or "unknown",
        # 0031. Which provider, beside which model. Not optional in meaning: a reading that
        # cannot say which model produced it is unusable for comparison later.
        provider=row.get("provider"),
        model_id=row.get("model_id"),
        specification_sha256=_spec_sha(category_key),
        simulation_version=SIMULATION_VERSION,
    )
    session.add(stored)
    session.flush()
    if previous is not None:
        previous.superseded_by = stored.reading_id
    session.flush()
    return stored


def reading_payload(stored: SpecificationReading) -> dict[str, Any]:
    return {
        "readingId": stored.reading_id,
        "category": stored.category_key,
        "period": stored.period,
        # THE FOUR STATES REACH THE CLIENT AS FOUR DISTINCT WORDS. Not a boolean, not a null.
        "state": stored.state,
        "status": stored.status,
        "counts": stored.counts or {},
        "modules": stored.modules or [],
        "reason": stored.reason,
        "missingUpstream": stored.missing_upstream or [],
        "servedBy": stored.served_by,
        "provider": stored.provider,
        "modelId": stored.model_id,
        "specificationSha256": stored.specification_sha256,
        "simulationVersion": stored.simulation_version,
        "computedAt": stored.created_at.isoformat() if stored.created_at else None,
    }


def _missing_upstream_for(session: Session, project_id: str, period: int,
                          category_key: str) -> list[str]:
    """
    OUT OF ORDER, decided here and not by the model.

    A pass-two category is out of order when NO pass-one category that has a specification has
    produced a finding for this project and period. It names the categories it is waiting on. It
    is a warning on the row, not a failure, and pressing again after they have run computes it.
    """
    if category_key not in sa.PASS_TWO:
        return []
    upstream = [k for k in sa.PASS_ONE if sa.has_specification(k)] or list(sa.PASS_ONE)
    produced = []
    for key in upstream:
        row = _live_reading(session, project_id, period, key)
        if row is not None and row.state == sa.COMPUTED:
            produced.append(key)
    return [] if produced else upstream


def apply_and_store(session: Session, project_id: str, period: int, category_key: str,
                    signal_inputs: dict, applier=None) -> SpecificationReading:
    """One category, applied and stored. Never raises: a failure is a stored FAILED row."""
    upstream_report = None
    if category_key in sa.PASS_TWO:
        pass_one_rows = {}
        for key in sa.PASS_ONE:
            prior = _live_reading(session, project_id, period, key)
            if prior is not None:
                pass_one_rows[key] = {"state": prior.state, "status": prior.status,
                                      "counts": prior.counts}
        upstream_report = sa.upstream_state_report(pass_one_rows)
    row = sa.apply_category(
        category_key, signal_inputs or {}, applier,
        upstream_report=upstream_report,
        missing_upstream=_missing_upstream_for(session, project_id, period, category_key))
    return store_reading(session, project_id, period, row)


# ------------------------------------------------------------------------------- the actions


def a_projectcategoryapply(session: Session, payload: dict, secret: str, ttl: int) -> dict:
    """Press one category, or every category with a specification. Any active member."""
    from .documents import _live_result, _resolve_period, require_member
    from .research_identity import resolve_caller

    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    project, _member, problem = require_member(session, caller, payload,
                                               "projectcategoryapply")
    if problem:
        return problem
    period, problem = _resolve_period(session, project, payload)
    if problem:
        return problem

    result = _live_result(session, project, period)
    if result is None:
        return err(f"no computed result for period {period}; run projectcompute first")
    figures = result.signal_inputs or {}

    wanted = str(payload.get("category") or "").strip().upper()
    if wanted and wanted not in sa.ALL_CATEGORIES:
        return err(f"{wanted} is not one of the eleven project categories")
    keys = [wanted] if wanted else [k for k in sa.ALL_CATEGORIES if sa.has_specification(k)]
    if not keys:
        return err("no category has a written specification yet")

    applier = sa.build_applier(_recorded_answers())
    out = []
    # PASS ONE THEN PASS TWO, in that order, so a pass-two category pressed as part of "call
    # all" sees what pass one produced in the same press.
    for key in [k for k in keys if k in sa.PASS_ONE] + [k for k in keys if k in sa.PASS_TWO]:
        out.append(reading_payload(
            apply_and_store(session, project.id, period, key, figures, applier)))
    session.commit()
    return {"ok": True, "period": period, "readings": out,
            "servedBy": getattr(applier, "served_by", "unknown"),
            "provider": getattr(applier, "provider", None),
            "modelId": getattr(applier, "model_id", None)}


def a_projectcategoryreadings(session: Session, payload: dict, secret: str, ttl: int) -> dict:
    """Read the stored readings for a period. READS ONLY — never applies anything."""
    from .documents import _resolve_period, require_member
    from .research_identity import resolve_caller

    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    project, _member, problem = require_member(session, caller, payload,
                                               "projectcategoryreadings")
    if problem:
        return problem
    period, problem = _resolve_period(session, project, payload)
    if problem:
        return problem

    readings = {}
    for key in sa.ALL_CATEGORIES:
        row = _live_reading(session, project.id, period, key)
        if row is not None:
            readings[key] = reading_payload(row)
    return {"ok": True, "period": period, "readings": readings,
            "specified": [k for k in sa.ALL_CATEGORIES if sa.has_specification(k)],
            "passOne": list(sa.PASS_ONE), "passTwo": list(sa.PASS_TWO)}


def _recorded_answers() -> dict[str, str]:
    """
    The recorded fixture, read only when no API key is present -- `build_applier` ignores it
    entirely the moment `ANTHROPIC_API_KEY` is set. It exists so this path can be exercised in a
    keyless environment, and every row it produces is stamped served_by "recorded".
    """
    p = sa.REPO_ROOT / "research_fixtures" / "run76_recorded_a1_answer.json"
    if not p.is_file():
        return {}
    try:
        return {k: v for k, v in json.loads(p.read_text()).items()
                if not k.startswith("_") and isinstance(v, str)}
    except ValueError:
        return {}


SPEC_ACTIONS = {
    "projectcategoryapply": a_projectcategoryapply,
    "projectcategoryreadings": a_projectcategoryreadings,
}
