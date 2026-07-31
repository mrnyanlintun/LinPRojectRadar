"""
Decision-dependent transitions (B5).

The next period's project state depends on what the participant decided. That makes the branch a
measurement artefact, so it has to be reconstructible years later from the stored row alone.

Three properties carry that.

  Selection is deterministic. The seed is sha256 over (participant_id, scenario_id, period), so
  replaying the same inputs always selects the same branch. There is no call to random(): a
  pseudo-random generator seeded at process start would make a run depend on process history,
  which is not reproducible from the data.

  The transitions row is self-contained. branch_id, branch_version, seed, probability,
  next_state_id and displayed_at are all stored, so the allocation can be re-derived without the
  rules table, and re-derived *against* it to detect drift.

  Rules are versioned and frozen. A rule edited after a participant transitioned cannot change
  what that participant experienced, because the branch_version they were allocated under is on
  their row.

An action with no family mapping is an error. There is deliberately no default family: a fallback
would silently absorb a typo or a newly added action and route a participant down a branch nobody
chose.
"""

from __future__ import annotations

import hashlib
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .facade import err
from .models import Project
from .research_identity import audit, resolve_caller
from .research_models import (
    ActionFamily, Assignment, Decision, Scenario, Transition, TransitionRule,
)

SEED_FIELDS = ("participant_id", "scenario_id", "period")


def derive_seed(participant_id: str, scenario_id: str, period: str) -> str:
    """
    The preregistered seed: sha256 over the three identifiers, joined with a separator that
    cannot occur in a ULID or a period label, so no two different inputs can produce the same
    string to hash.
    """
    material = "|".join((participant_id, scenario_id, period))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def seed_fraction(seed: str) -> Decimal:
    """Map the seed onto [0,1). Uses the first 64 bits, which is far more resolution than any
    preregistered probability set will need."""
    return (Decimal(int(seed[:16], 16)) / Decimal(1 << 64)).quantize(Decimal("0.000000000000000001"))


def select_branch(candidates: list[TransitionRule], seed: str) -> tuple[TransitionRule | None, str | None]:
    """
    Choose one candidate by cumulative probability.

    Candidates are ordered by branch_id, not by insertion order or primary key, so the selection
    cannot change because rows were re-inserted in a different order. With a single candidate the
    seed is irrelevant and that candidate is always chosen, which is what makes an action family
    with one branch fully deterministic across participants.
    """
    if not candidates:
        return None, "no candidate branches"

    ordered = sorted(candidates, key=lambda r: r.branch_id)
    try:
        weights = [Decimal(str(r.probability)) for r in ordered]
    except (InvalidOperation, TypeError):
        return None, "a branch probability is not a valid decimal"

    if any(w < 0 for w in weights):
        return None, "a branch probability is negative"

    total = sum(weights)
    if total <= 0:
        return None, "branch probabilities sum to zero"

    # Normalised rather than required to equal exactly 1, so a preregistered set of thirds is not
    # rejected for summing to 0.999. The stored probability is still the value as written.
    target = seed_fraction(seed) * total
    cumulative = Decimal(0)
    for rule, weight in zip(ordered, weights):
        cumulative += weight
        if target < cumulative:
            return rule, None
    return ordered[-1], None


def resolve_family(session: Session, action: str, version: str | None) -> tuple[str | None, str | None]:
    """Map a literal action to its family. Frozen mappings only."""
    query = select(ActionFamily).where(
        ActionFamily.action == (action or "").strip().lower(),
        ActionFamily.frozen_at.is_not(None),
    )
    if version:
        query = query.where(ActionFamily.version == version)
    rows = session.scalars(query).all()
    if not rows:
        return None, (f"action {action!r} has no frozen family mapping; an unmapped action is an "
                      f"error, not a default")
    if not version:
        latest = sorted({r.version for r in rows})[-1]
        rows = [r for r in rows if r.version == latest]
    return rows[0].family, None


def load_rules(session: Session, scenario_id: str, period: str, family: str,
               version: str | None) -> tuple[list[TransitionRule], str | None]:
    query = select(TransitionRule).where(
        TransitionRule.scenario_id == scenario_id,
        TransitionRule.period == period,
        TransitionRule.action_family == family,
        TransitionRule.frozen_at.is_not(None),
    )
    if version:
        query = query.where(TransitionRule.version == version)
    rows = session.scalars(query).all()
    if not rows:
        return [], (f"no frozen transition rule for scenario {scenario_id} period {period} "
                    f"family {family!r}")
    if not version:
        latest = sorted({r.version for r in rows})[-1]
        rows = [r for r in rows if r.version == latest]
    return rows, None


# ---------------------------------------------------------------- admin


def _require_admin(session: Session, payload: dict, secret: str, action: str):
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return None, problem
    if not caller.is_admin:
        audit(session, "admin_action_denied", participant_id=caller.participant_id,
              action=action, role=caller.role)
        session.commit()
        return None, err("not authorised: ResearchAdmin role required")
    return caller, None


def a_adminactionfamilycreate(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """Define the action taxonomy as data. mappings is {action: family}."""
    caller, problem = _require_admin(session, payload, secret, "adminactionfamilycreate")
    if problem:
        return problem

    version = str(payload.get("version") or "").strip()
    mappings = payload.get("mappings")
    if not version:
        return err("version is required")
    if not isinstance(mappings, dict) or not mappings:
        return err("mappings must be a non-empty object of action -> family")

    for action_name, family in mappings.items():
        session.add(ActionFamily(action=str(action_name).strip().lower(),
                                 family=str(family).strip().lower(), version=version))
    session.flush()

    if payload.get("freeze"):
        for row in session.scalars(
            select(ActionFamily).where(ActionFamily.version == version)
        ).all():
            row.frozen_at = func.now()

    audit(session, "action_families_created", created_by=caller.participant_id,
          version=version, count=len(mappings), frozen=bool(payload.get("freeze")))
    session.commit()
    return {"ok": True, "version": version, "mappings": {str(k).lower(): str(v).lower()
                                                         for k, v in mappings.items()},
            "frozen": bool(payload.get("freeze"))}


def a_admintransitionrulecreate(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Define the candidate branches for one (scenario, period, action_family).

    branches is a list of {branch_id, branch_version, probability, next_state_id}.
    """
    caller, problem = _require_admin(session, payload, secret, "admintransitionrulecreate")
    if problem:
        return problem

    scenario_id = str(payload.get("scenario_id") or "").strip()
    period = str(payload.get("period") or "").strip()
    family = str(payload.get("action_family") or "").strip().lower()
    version = str(payload.get("version") or "").strip()
    branches = payload.get("branches")

    if not scenario_id or not period or not family or not version:
        return err("scenario_id, period, action_family and version are required")
    if session.get(Scenario, scenario_id) is None:
        return err(f"scenario not found: {scenario_id}")
    if not isinstance(branches, list) or not branches:
        return err("branches must be a non-empty list")

    for b in branches:
        if not isinstance(b, dict):
            return err("each branch must be an object")
        for required in ("branch_id", "branch_version", "probability", "next_state_id"):
            if b.get(required) in (None, ""):
                return err(f"branch is missing {required}")
        try:
            if Decimal(str(b["probability"])) < 0:
                return err("branch probability may not be negative")
        except (InvalidOperation, TypeError):
            return err(f"branch probability {b.get('probability')!r} is not a valid decimal")

    for b in branches:
        session.add(TransitionRule(
            scenario_id=scenario_id, period=period, action_family=family,
            branch_id=str(b["branch_id"]), branch_version=str(b["branch_version"]),
            probability=str(b["probability"]), next_state_id=str(b["next_state_id"]),
            version=version,
        ))
    session.flush()

    if payload.get("freeze"):
        for row in session.scalars(
            select(TransitionRule).where(
                TransitionRule.scenario_id == scenario_id, TransitionRule.period == period,
                TransitionRule.action_family == family, TransitionRule.version == version)
        ).all():
            row.frozen_at = func.now()

    audit(session, "transition_rule_created", created_by=caller.participant_id,
          scenario_id=scenario_id, period=period, action_family=family, version=version,
          branch_count=len(branches), frozen=bool(payload.get("freeze")))
    session.commit()
    return {"ok": True, "scenario_id": scenario_id, "period": period, "action_family": family,
            "version": version, "branches": len(branches), "frozen": bool(payload.get("freeze"))}


def a_admintransitionrulelist(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = _require_admin(session, payload, secret, "admintransitionrulelist")
    if problem:
        return problem
    rows = session.scalars(select(TransitionRule).order_by(
        TransitionRule.scenario_id, TransitionRule.period,
        TransitionRule.action_family, TransitionRule.version, TransitionRule.branch_id)).all()
    return {"ok": True, "rules": [
        {"scenario_id": r.scenario_id, "period": r.period, "action_family": r.action_family,
         "branch_id": r.branch_id, "branch_version": r.branch_version,
         "probability": r.probability, "next_state_id": r.next_state_id,
         "version": r.version, "frozen_at": r.frozen_at.isoformat() if r.frozen_at else None,
         "usable": r.frozen_at is not None}
        for r in rows
    ]}


def a_adminactionfamilylist(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = _require_admin(session, payload, secret, "adminactionfamilylist")
    if problem:
        return problem
    rows = session.scalars(select(ActionFamily).order_by(ActionFamily.version,
                                                         ActionFamily.action)).all()
    return {"ok": True, "action_families": [
        {"action": r.action, "family": r.family, "version": r.version,
         "frozen_at": r.frozen_at.isoformat() if r.frozen_at else None,
         "usable": r.frozen_at is not None}
        for r in rows
    ]}


# ---------------------------------------------------------------- participant


def _resolve_advance_target(session: Session, caller, payload: dict):
    """
    The assignment to advance.

    Normally the caller's current assignment. When every assignment is complete there is no
    "current" one, but advancing must still answer coherently rather than claim the participant
    has no assignment at all, so the highest-numbered assignment is used. A body-supplied
    assignment_id is still checked against the resolved one and a mismatch is audited: guarantee 2
    must hold in both states.
    """
    from .research_decision import _current_assignment

    assignment, _ = _current_assignment(session, caller.participant_id)
    if assignment is None:
        assignment = session.scalars(
            select(Assignment).where(Assignment.participant_id == caller.participant_id)
            .order_by(Assignment.sequence_number.desc())
        ).first()
    if assignment is None:
        return None, err("no assignment")

    requested = str(payload.get("assignment_id") or "").strip()
    if requested and requested != assignment.assignment_id:
        audit(session, "out_of_sequence_access_denied", participant_id=caller.participant_id,
              action="researchadvance", requested_assignment_id=requested,
              current_assignment_id=assignment.assignment_id)
        session.commit()
        return None, err("not authorised: only the current assignment may be acted on")

    return assignment, None


def a_researchadvance(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Execute the branch for the decision just submitted and return the next period's state.

    Refuses unless the current period's decision is complete, and writes nothing on refusal: a
    half-written transition would leave a participant in a period that no rule produced.
    """
    from .research_decision import _period_number, _resolve_target

    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem

    assignment, problem = _resolve_advance_target(session, caller, payload)
    if problem:
        return problem

    scenario = session.get(Scenario, assignment.scenario_id)
    if scenario is None:
        return err(f"scenario not found: {assignment.scenario_id}")

    # Advance FROM the latest period that has a decision, not from the current period. Once a
    # transition has executed the current period is already the next one, so asking about the
    # current period would report the new period as incomplete and make the idempotent re-advance
    # unreachable.
    rows = session.scalars(
        select(Decision).where(Decision.assignment_id == assignment.assignment_id)
    ).all()
    decision = max(rows, key=lambda d: _period_number(d.period or "P1")) if rows else None
    period = (decision.period if decision else "P1") or "P1"

    # Guarantee 1.
    if decision is None or decision.final_submitted_at is None:
        audit(session, "advance_denied_incomplete", participant_id=caller.participant_id,
              scenario_id=scenario.scenario_id, period=period)
        session.commit()
        return err("the current period's decision must be complete before advancing")

    existing = session.scalar(select(Transition).where(Transition.decision_id == decision.decision_id))
    if existing is not None:
        # Idempotent. displayed_at measures when the next state was first shown.
        return _advance_view(session, scenario, existing, period, already=True)

    period_count = scenario.period_count or 1
    if _period_number(period) >= period_count:
        return err(f"scenario has {period_count} period(s); there is nothing to advance to")

    family, problem_text = resolve_family(session, decision.final_action,
                                          payload.get("family_version"))
    if problem_text:
        audit(session, "advance_denied_unmapped_action", participant_id=caller.participant_id,
              scenario_id=scenario.scenario_id, period=period, action=decision.final_action)
        session.commit()
        return err(problem_text)

    candidates, problem_text = load_rules(session, scenario.scenario_id, period, family,
                                          payload.get("rule_version"))
    if problem_text:
        return err(problem_text)

    seed = derive_seed(caller.participant_id, scenario.scenario_id, period)
    branch, problem_text = select_branch(candidates, seed)
    if problem_text:
        return err(problem_text)

    row = Transition(
        decision_id=decision.decision_id,
        branch_id=branch.branch_id,
        branch_version=branch.branch_version,
        seed=seed,
        probability=branch.probability,
        next_state_id=branch.next_state_id,
        displayed_at=func.now(),
    )
    session.add(row)
    audit(session, "transition_executed", participant_id=caller.participant_id,
          scenario_id=scenario.scenario_id, period=period, action_family=family,
          branch_id=branch.branch_id, branch_version=branch.branch_version,
          seed=seed, probability=branch.probability, next_state_id=branch.next_state_id)
    session.commit()

    session.refresh(row)
    if row.displayed_at is None:
        return err("transition could not be verified")
    return _advance_view(session, scenario, row, period, already=False)


def _period_number(period: str) -> int:
    digits = "".join(c for c in str(period) if c.isdigit())
    return int(digits) if digits else 1


def _advance_view(session: Session, scenario: Scenario, row: Transition, from_period: str,
                  already: bool) -> dict[str, Any]:
    project = session.scalar(select(Project).where(Project.legacy_id == row.next_state_id))
    next_period = f"P{_period_number(from_period) + 1}"
    return {
        "ok": True,
        "already_advanced": already,
        "from_period": from_period,
        "period": next_period,
        # branch_id and seed are deliberately included: they identify the state the participant is
        # now in, and reveal nothing about the condition they are in or which branch others got.
        "branch_id": row.branch_id,
        "branch_version": row.branch_version,
        "next_state_id": row.next_state_id,
        "displayed_at": row.displayed_at.isoformat() if row.displayed_at else None,
        "state": project.doc if project else None,
        "current_stage": "evidence",
    }


TRANSITION_ACTIONS: dict[str, Callable[[Session, dict, str, int], dict]] = {
    "adminactionfamilycreate": a_adminactionfamilycreate,
    "adminactionfamilylist": a_adminactionfamilylist,
    "admintransitionrulecreate": a_admintransitionrulecreate,
    "admintransitionrulelist": a_admintransitionrulelist,
    "researchadvance": a_researchadvance,
}
