"""
The expert reference standard (T6).

WHAT THIS IS FOR

Every participant decision is scored against an expert reference. The reference is what "correct"
means for a scenario period, and the study's central comparison — did decision support move the
participant toward or away from expert judgment — is only as good as the reference's independence.

ONE RULE CARRIES THE WHOLE THING

The reference must be committed before the expert sees any AI package. An expert who has read the
recommendation cannot afterwards produce an independent reference: whatever they write is
contaminated by the thing the reference exists to evaluate, and the contamination is invisible in
the stored row. There is no way to detect it after the fact, so it has to be made impossible
beforehand.

Four properties enforce that, mirroring the four B4 built for the participant's preliminary
judgment. This is deliberate reuse, not resemblance — the same argument applies, so the same
mechanism is used rather than a second one:

  Evidence is package-free by construction. a_expertevidenceget reads the scenario's evidence
  package and never consults assignments.package_id. It cannot leak a recommendation because it
  never loads one, in any branch, at any stage.

  The lock is server-assigned and atomic. The reference row is INSERTed with locked_at already
  set, in one statement. There is no path that writes a reference and locks it afterwards, because
  that would leave a window in which an unlocked reference exists.

  Package access is gated on the lock, not on the interface. a_expertpackageview refuses unless
  locked_at is already set, and the refusal carries no package content — a refusal that leaked the
  recommendation would defeat the gate it enforces.

  Immutability is enforced by the database. Migration 0012 installs a trigger that rejects any
  UPDATE to the seven reference fields once locked_at is set, and rejects moving locked_at itself.
  The application refuses first; the trigger is the last line, so the guarantee does not rest on
  the application being correct.

WHAT THE EXPERT MAY DO AFTER LOCKING

Exactly one thing: record a realism review of the package — whether it is plausible as a real
system output. That is a judgment ABOUT the package, not a revision OF the reference, and
realism_review is deliberately outside the trigger's protected field list so the two cannot be
confused at the storage layer.

MIGRATION: 0012_expert_reference_lock. /readyz reports 503 until `alembic upgrade head` is run.
"""

from __future__ import annotations

from typing import Any, Callable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .facade import err
from .models import Project
from .research_identity import ROLE_EXPERT, audit, resolve_caller
from .research_models import Assignment, ExpertReference, Scenario

# The reference's own vocabulary. Kept alongside the participant vocabulary in research_decision
# rather than imported from it, because an expert names actions from the same closed set the
# participant chooses from — if these ever diverge the comparison stops meaning anything, so the
# T6 suite asserts they are identical.
from .research_decision import PARTICIPANT_ACTIONS, _package_view, _period_number


def _require_expert(session: Session, payload: dict, secret: str, action: str):
    """
    Resolve the caller and refuse anyone who is not an Expert.

    Role is read from the database row by resolve_caller, never from the request, so a caller
    cannot assert their way into the expert panel.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return None, problem
    if caller.role != ROLE_EXPERT:
        audit(session, "expert_action_denied", participant_id=caller.participant_id,
              action=action, role=caller.role)
        session.commit()
        return None, err("not authorized: this action is for the expert review panel")
    return caller, None


def _resolve_expert_assignment(session: Session, caller, payload: dict, action: str):
    """
    Find the expert's assignment for the requested scenario.

    An expert may hold several assignments at once — unlike a participant, they are not walking a
    counterbalanced sequence — so the scenario is named in the request and checked against an
    assignment row rather than derived from a sequence position. A scenario the expert does not
    hold is refused and audited: an attempt to write a reference for someone else's scenario is
    exactly the event the audit trail exists to hold.
    """
    scenario_id = str(payload.get("scenario_id") or "").strip()
    if not scenario_id:
        return None, None, err("scenario_id is required")

    assignment = session.scalar(
        select(Assignment).where(Assignment.participant_id == caller.participant_id,
                                 Assignment.scenario_id == scenario_id)
    )
    if assignment is None:
        audit(session, "expert_scenario_access_denied", participant_id=caller.participant_id,
              scenario_id=scenario_id, action=action)
        session.commit()
        return None, None, err("not authorized: that scenario is not assigned to you")

    scenario = session.get(Scenario, scenario_id)
    if scenario is None:
        return None, None, err(f"scenario not found: {scenario_id}")
    return assignment, scenario, None


def _resolve_period(payload: dict, scenario: Scenario) -> tuple[str | None, dict | None]:
    """
    Validate the requested period against the scenario's length.

    Defaults to P1 so a single-period scenario needs no period in the request at all.
    """
    raw = str(payload.get("period") or "P1").strip()
    period = raw if raw.upper().startswith("P") else f"P{raw}"
    period = period.upper()
    n = _period_number(period)
    if n < 1 or (scenario.period_count is not None and n > scenario.period_count):
        return None, err(f"period out of range for this scenario: {raw}")
    return period, None


def _reference_for(session: Session, scenario_id: str, expert_id: str, period: str):
    return session.scalar(
        select(ExpertReference).where(ExpertReference.scenario_id == scenario_id,
                                      ExpertReference.expert_id == expert_id,
                                      ExpertReference.period == period)
    )


def _reference_view(ref: ExpertReference) -> dict[str, Any]:
    return {
        "reference_id": ref.reference_id,
        "scenario_id": ref.scenario_id,
        "period": ref.period,
        "preferred_action": ref.preferred_action,
        "acceptable_alternatives": ref.acceptable_alternatives or [],
        "unsupported_actions": ref.unsupported_actions or [],
        "rationale": ref.rationale,
        "required_evidence": ref.required_evidence,
        "escalation_expectation": ref.escalation_expectation,
        "confidence": ref.confidence,
        "locked_at": ref.locked_at.isoformat() if ref.locked_at else None,
        "realism_review": ref.realism_review,
    }


# ---------------------------------------------------------------- stage 1: evidence only


def a_expertevidenceget(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    The base project evidence for one scenario period. No package, ever.

    This is the same evidence a participant sees, read from the scenario's evidence package. It
    never reads assignments.package_id and never touches decision_support_packages — not gated on
    the lock, but structurally incapable of returning a recommendation, which is a stronger
    property than a gate because it cannot be got wrong by a future edit to a condition.
    """
    caller, problem = _require_expert(session, payload, secret, "expertevidenceget")
    if problem:
        return problem

    assignment, scenario, problem = _resolve_expert_assignment(
        session, caller, payload, "expertevidenceget")
    if problem:
        return problem

    period, problem = _resolve_period(payload, scenario)
    if problem:
        return problem

    evidence: dict[str, Any] | None = None
    if scenario.evidence_package_id:
        project = session.scalar(
            select(Project).where(Project.legacy_id == scenario.evidence_package_id))
        evidence = project.doc if project else None

    existing = _reference_for(session, scenario.scenario_id, caller.participant_id, period)
    audit(session, "expert_evidence_viewed", participant_id=caller.participant_id,
          scenario_id=scenario.scenario_id, period=period)
    session.commit()

    return {
        "ok": True,
        "scenario_id": scenario.scenario_id,
        "scenario_version": scenario.scenario_version,
        "project_type": scenario.project_type,
        "period": period,
        "period_count": scenario.period_count,
        "evidence": evidence,
        "reference_locked": bool(existing and existing.locked_at),
        "locked_at": existing.locked_at.isoformat() if existing and existing.locked_at else None,
        # The vocabulary the expert names actions from — the same closed set the participant uses.
        "vocabularies": {"actions": list(PARTICIPANT_ACTIONS)},
        # No package, no recommendation, no configuration, no condition of any kind.
    }


# ---------------------------------------------------------------- stage 2: commit and lock


def a_expertreferencecommit(session: Session, payload: dict, secret: str,
                            ttl: int) -> dict[str, Any]:
    """
    Commit and lock the expert reference in one statement.

    locked_at is set in the same INSERT as the content, from the server clock. A client cannot
    supply it, and there is no window in which the reference exists unlocked.
    """
    caller, problem = _require_expert(session, payload, secret, "expertreferencecommit")
    if problem:
        return problem

    assignment, scenario, problem = _resolve_expert_assignment(
        session, caller, payload, "expertreferencecommit")
    if problem:
        return problem

    period, problem = _resolve_period(payload, scenario)
    if problem:
        return problem

    existing = _reference_for(session, scenario.scenario_id, caller.participant_id, period)
    if existing is not None and existing.locked_at is not None:
        # Refused at the application layer, and refused again by the trigger if anything ever
        # reaches an UPDATE. This is the first line, not the only one.
        audit(session, "expert_reference_resubmission_denied",
              participant_id=caller.participant_id, scenario_id=scenario.scenario_id,
              period=period)
        session.commit()
        return err("your reference for this period is already locked and cannot be changed")

    preferred = str(payload.get("preferred_action") or "").strip()
    if not preferred:
        return err("a preferred action is required")
    if preferred not in PARTICIPANT_ACTIONS:
        return err(f"preferred_action must be one of: {', '.join(PARTICIPANT_ACTIONS)}")

    rationale = str(payload.get("rationale") or "").strip()
    if not rationale:
        return err("a rationale is required")

    required_evidence = str(payload.get("required_evidence") or "").strip()
    if not required_evidence:
        return err("the evidence you relied on is required")

    escalation = str(payload.get("escalation_expectation") or "").strip()
    if not escalation:
        return err("an escalation expectation is required")

    confidence = payload.get("confidence")
    if confidence is None:
        return err("confidence is required")
    try:
        confidence = int(confidence)
    except (TypeError, ValueError):
        return err("confidence must be an integer")
    if not 0 <= confidence <= 100:
        return err("confidence must be between 0 and 100")

    def _action_list(key: str) -> tuple[list[str] | None, dict | None]:
        raw = payload.get(key) or []
        if not isinstance(raw, list):
            return None, err(f"{key} must be a list of actions")
        cleaned = [str(a).strip() for a in raw if str(a).strip()]
        unknown = [a for a in cleaned if a not in PARTICIPANT_ACTIONS]
        if unknown:
            return None, err(f"{key} contains unrecognized actions: {', '.join(unknown)}")
        if preferred in cleaned:
            return None, err(f"{key} cannot repeat the preferred action")
        return cleaned, None

    acceptable, problem = _action_list("acceptable_alternatives")
    if problem:
        return problem
    unsupported, problem = _action_list("unsupported_actions")
    if problem:
        return problem
    overlap = sorted(set(acceptable) & set(unsupported))
    if overlap:
        return err("an action cannot be both acceptable and unsupported: " + ", ".join(overlap))

    reference = ExpertReference(
        scenario_id=scenario.scenario_id,
        expert_id=caller.participant_id,
        period=period,
        preferred_action=preferred,
        acceptable_alternatives=acceptable,
        unsupported_actions=unsupported,
        rationale=rationale,
        required_evidence=required_evidence,
        escalation_expectation=escalation,
        confidence=confidence,
        locked_at=func.now(),   # same statement, same server clock
    )
    session.add(reference)
    audit(session, "expert_reference_locked", participant_id=caller.participant_id,
          scenario_id=scenario.scenario_id, period=period)
    session.commit()

    session.refresh(reference)
    if reference.locked_at is None:
        return err("the reference could not be verified as locked")

    return {"ok": True, "reference": _reference_view(reference), "package_available": True}


# ---------------------------------------------------------------- stage 3: package, post-lock


def a_expertpackageview(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    The AI package, and only once the reference is locked.

    The refusal path returns no package content whatsoever. A refusal that named the recommended
    action, or carried the package's prose, would leak precisely what the lock exists to withhold.
    """
    caller, problem = _require_expert(session, payload, secret, "expertpackageview")
    if problem:
        return problem

    assignment, scenario, problem = _resolve_expert_assignment(
        session, caller, payload, "expertpackageview")
    if problem:
        return problem

    period, problem = _resolve_period(payload, scenario)
    if problem:
        return problem

    reference = _reference_for(session, scenario.scenario_id, caller.participant_id, period)
    if reference is None or reference.locked_at is None:
        audit(session, "expert_package_denied_before_lock",
              participant_id=caller.participant_id, scenario_id=scenario.scenario_id,
              period=period)
        session.commit()
        # No package field at all — not null, not empty, absent.
        return err("your reference for this period must be locked before the package can be shown")

    if not assignment.package_id:
        return err("no package is attached to this scenario")

    from .research_models import DecisionSupportPackage
    pkg = session.get(DecisionSupportPackage, assignment.package_id)
    if pkg is None:
        return err(f"package not found: {assignment.package_id}")

    audit(session, "expert_package_viewed", participant_id=caller.participant_id,
          scenario_id=scenario.scenario_id, period=period)
    session.commit()

    return {"ok": True, "scenario_id": scenario.scenario_id, "period": period,
            "locked_at": reference.locked_at.isoformat(), "package": _package_view(pkg)}


def a_expertrealismreview(session: Session, payload: dict, secret: str,
                          ttl: int) -> dict[str, Any]:
    """
    Record whether the package is plausible as a real system output.

    This writes realism_review only. Every field that constitutes the reference is left untouched,
    and the trigger from 0012 would reject this UPDATE if it were not.
    """
    caller, problem = _require_expert(session, payload, secret, "expertrealismreview")
    if problem:
        return problem

    assignment, scenario, problem = _resolve_expert_assignment(
        session, caller, payload, "expertrealismreview")
    if problem:
        return problem

    period, problem = _resolve_period(payload, scenario)
    if problem:
        return problem

    reference = _reference_for(session, scenario.scenario_id, caller.participant_id, period)
    if reference is None or reference.locked_at is None:
        return err("your reference for this period must be locked before a realism review")

    plausible = payload.get("plausible")
    if plausible is None:
        return err("a plausibility judgment is required")
    comment = str(payload.get("comment") or "").strip()

    reference.realism_review = {"plausible": bool(plausible), "comment": comment or None}
    audit(session, "expert_realism_review_recorded", participant_id=caller.participant_id,
          scenario_id=scenario.scenario_id, period=period)
    session.commit()

    return {"ok": True, "reference": _reference_view(reference)}


# ---------------------------------------------------------------- read


def a_expertreferencelist(session: Session, payload: dict, secret: str,
                          ttl: int) -> dict[str, Any]:
    """
    The expert's own assigned scenarios and the state of each reference.

    Carries no package content in any branch: this is the screen the expert lands on, so it is on
    the pre-lock side of the guarantee for every row that is not yet locked.
    """
    caller, problem = _require_expert(session, payload, secret, "expertreferencelist")
    if problem:
        return problem

    assignments = session.scalars(
        select(Assignment).where(Assignment.participant_id == caller.participant_id)).all()

    rows: list[dict[str, Any]] = []
    for a in assignments:
        scenario = session.get(Scenario, a.scenario_id)
        if scenario is None:
            continue
        count = scenario.period_count or 1
        for n in range(1, count + 1):
            period = f"P{n}"
            ref = _reference_for(session, a.scenario_id, caller.participant_id, period)
            rows.append({
                "scenario_id": a.scenario_id,
                "scenario_version": scenario.scenario_version,
                "project_type": scenario.project_type,
                "period": period,
                "period_count": count,
                "locked": bool(ref and ref.locked_at),
                "locked_at": ref.locked_at.isoformat() if ref and ref.locked_at else None,
                "realism_reviewed": bool(ref and ref.realism_review),
            })

    return {"ok": True, "references": rows}


EXPERT_ACTIONS: dict[str, Callable[[Session, dict, str, int], dict]] = {
    "expertreferencelist": a_expertreferencelist,
    "expertevidenceget": a_expertevidenceget,
    "expertreferencecommit": a_expertreferencecommit,
    "expertpackageview": a_expertpackageview,
    "expertrealismreview": a_expertrealismreview,
}
