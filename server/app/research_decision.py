"""
The experimental sequence (B4): evidence, locked preliminary judgment, reveal, disposition.

This is the measurement. The claim the study makes is that the preliminary judgment was formed
without sight of the decision support package, and everything here exists to make that claim
verifiable rather than asserted.

Four properties carry that weight:

  The lock is server-assigned and atomic. pre_submitted_at, pre_locked_at and pre_judgment_locked
  are written in one statement, so there is no window in which a judgment is submitted but not yet
  locked. A client cannot supply any of them.

  Reveal is gated on the lock, not on the interface. researchreveal refuses unless
  pre_judgment_locked is already true, and the refusal carries no package content, because a
  refusal that leaked the recommendation would defeat the gate it is enforcing.

  Stage is derived, never asserted. It is computed from the decisions row on every read, so a
  client cannot claim to be at a stage it has not reached, and the stage can never disagree with
  the data it describes.

  Nothing here calls a model. Packages are read from decision_support_packages and returned
  verbatim. This module imports no HTTP client and makes no outbound request; the only source of a
  recommendation is a row that was frozen and hashed before the study began.

NO MIGRATION. Packages attach to an assignment through the existing assignments.package_id.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .facade import err
from .models import Project
from .research_assignment import current_sequence_number
from .research_identity import audit, resolve_caller
from .research_models import (
    Assignment, Decision, DecisionSupportPackage, Scenario,
)

# Stage names, in the order they occur.
STAGE_EVIDENCE = "evidence"
STAGE_AWAITING_REVEAL = "awaiting_reveal"
STAGE_DECIDING = "deciding"
STAGE_COMPLETE = "complete"

# The fields whose values are hashed to freeze a package. Ordered and explicit: adding a field
# here changes every future hash, which is the intended behaviour, and leaving one out would let
# it be edited after freezing without detection.
HASHED_FIELDS = (
    "version", "provider_id", "model_version", "use_case", "output_type",
    "detected_condition", "limitations", "recommended_action", "applicability_boundary",
    "expiration_trigger", "alternatives", "uncertainty", "provenance",
)


def compute_package_hash(row: DecisionSupportPackage) -> str:
    """sha256 over a canonical rendering of the content fields."""
    payload = {f: getattr(row, f) for f in HASHED_FIELDS}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- stage


def derive_stage(decision: Decision | None) -> str:
    """
    Stage from row state, in the order the brief specifies.

    Read on every request rather than stored. A stored stage is a second source of truth that can
    disagree with the decisions row, and in a blinded flow a stage that runs ahead of the data
    would be a disclosure.
    """
    if decision is None:
        return STAGE_EVIDENCE
    if decision.final_submitted_at is not None:
        return STAGE_COMPLETE
    if decision.reveal_at is not None:
        return STAGE_DECIDING
    if decision.pre_submitted_at is not None:
        return STAGE_AWAITING_REVEAL
    return STAGE_EVIDENCE


def _current_assignment(session: Session, participant_id: str) -> tuple[Assignment | None, int | None]:
    current = current_sequence_number(session, participant_id)
    if current is None:
        return None, None
    row = session.scalar(
        select(Assignment).where(Assignment.participant_id == participant_id,
                                 Assignment.sequence_number == current)
    )
    return row, current


def _decision_for(session: Session, assignment_id: str, period: str) -> Decision | None:
    return session.scalar(select(Decision).where(Decision.assignment_id == assignment_id,
                                                 Decision.period == period))


def _period_number(period: str) -> int:
    digits = "".join(c for c in str(period) if c.isdigit())
    return int(digits) if digits else 1


def current_period(session: Session, assignment: Assignment,
                   scenario: Scenario | None = None) -> str:
    """
    The period the participant is currently working in.

    Derived, like the stage and the sequence position, so it cannot drift from the rows it
    describes. A completed period only advances once a transition has actually been executed:
    the participant stays in the completed period until researchadvance runs, which makes
    "decided but not yet advanced" a distinguishable state rather than a gap.
    """
    from .research_models import Transition

    rows = session.scalars(
        select(Decision).where(Decision.assignment_id == assignment.assignment_id)
    ).all()
    if not rows:
        return "P1"

    latest = max(rows, key=lambda d: _period_number(d.period or "P1"))
    if latest.final_submitted_at is None:
        return latest.period or "P1"

    transitioned = session.scalar(
        select(Transition).where(Transition.decision_id == latest.decision_id)
    )
    if transitioned is None:
        return latest.period or "P1"

    nxt = _period_number(latest.period or "P1") + 1
    limit = (scenario.period_count if scenario else None) or nxt
    return "P" + str(min(nxt, limit))


def _resolve_target(session: Session, caller, payload: dict, action: str):
    """
    Find the caller's current assignment, refusing anything that is not it.

    Guarantee 4 lives here. A body-supplied assignment_id is checked against the caller's current
    assignment rather than trusted, and a mismatch is audited: an attempt to act on another
    assignment is exactly the event the audit trail exists to hold.
    """
    assignment, current = _current_assignment(session, caller.participant_id)
    if assignment is None:
        return None, err("no current assignment")

    requested = str(payload.get("assignment_id") or "").strip()
    if requested and requested != assignment.assignment_id:
        audit(session, "out_of_sequence_access_denied", participant_id=caller.participant_id,
              action=action, requested_assignment_id=requested,
              current_assignment_id=assignment.assignment_id)
        session.commit()
        return None, err("not authorised: only the current assignment may be acted on")

    return assignment, None


# ---------------------------------------------------------------- evidence


def a_researchevidenceget(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Base project evidence for the caller's current assignment.

    Identical across conditions by construction: it is read from the scenario's evidence package
    and never consults the assignment's configuration. The package is not returned here at any
    stage, including after reveal, because this action is the one a participant may call while
    still forming their preliminary judgment.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem

    assignment, problem = _resolve_target(session, caller, payload, "researchevidenceget")
    if problem:
        return problem

    scenario = session.get(Scenario, assignment.scenario_id)
    if scenario is None:
        return err(f"scenario not found: {assignment.scenario_id}")

    period = current_period(session, assignment, scenario)
    decision = _decision_for(session, assignment.assignment_id, period)

    # From period 2 onward the state is the one the transition produced, not the scenario
    # opening evidence. Re-reading the opening evidence would hide the consequence of the
    # participant own decision, which is the thing this design exists to measure.
    state_ref = scenario.evidence_package_id
    if _period_number(period) > 1:
        from .research_models import Transition
        prior = _decision_for(session, assignment.assignment_id,
                              "P" + str(_period_number(period) - 1))
        if prior is not None:
            tr = session.scalar(
                select(Transition).where(Transition.decision_id == prior.decision_id))
            if tr is not None:
                state_ref = tr.next_state_id

    evidence: dict[str, Any] | None = None
    if state_ref:
        project = session.scalar(select(Project).where(Project.legacy_id == state_ref))
        evidence = project.doc if project else None
    audit(session, "evidence_viewed", participant_id=caller.participant_id,
          scenario_id=scenario.scenario_id, sequence_number=assignment.sequence_number,
          period=period)
    session.commit()

    return {
        "ok": True,
        "period": period,
        "sequence_number": assignment.sequence_number,
        "scenario_id": scenario.scenario_id,
        "scenario_version": scenario.scenario_version,
        "project_type": scenario.project_type,
        "period_count": scenario.period_count,
        "evidence": evidence,
        "current_stage": derive_stage(decision),
        # No configuration, no package, no condition of any kind.
    }


# ---------------------------------------------------------------- preliminary judgment


def a_researchprejudgment(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Commit and lock the preliminary judgment.

    The row is INSERTed with pre_submitted_at, pre_locked_at and pre_judgment_locked all set in the
    same statement. There is deliberately no path that writes the judgment first and locks it
    afterwards: that would leave a window, however short, in which the judgment exists unlocked.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem

    assignment, problem = _resolve_target(session, caller, payload, "researchprejudgment")
    if problem:
        return problem

    pre_action = str(payload.get("pre_action") or "").strip()
    if not pre_action:
        return err("pre_action is required")
    confidence = payload.get("pre_confidence")
    if confidence is None:
        return err("pre_confidence is required")
    try:
        confidence = int(confidence)
    except (TypeError, ValueError):
        return err("pre_confidence must be an integer")
    if not 0 <= confidence <= 100:
        return err("pre_confidence must be between 0 and 100")

    scenario = session.get(Scenario, assignment.scenario_id)
    period = current_period(session, assignment, scenario)
    existing = _decision_for(session, assignment.assignment_id, period)
    if existing is not None and existing.pre_judgment_locked:
        # Guarantee 2, application layer. The database trigger is the last line, not the first.
        audit(session, "pre_judgment_resubmission_denied", participant_id=caller.participant_id,
              scenario_id=assignment.scenario_id, attempted_pre_action=pre_action)
        session.commit()
        return err("preliminary judgment is already locked and cannot be resubmitted")

    now = func.now()
    decision = Decision(
        assignment_id=assignment.assignment_id,
        # Server-derived. A client-supplied period would let a participant write into a
        # period they have not reached.
        period=period,
        pre_action=pre_action,
        pre_confidence=confidence,
        pre_submitted_at=now,
        pre_locked_at=now,          # same statement, same server clock
        pre_judgment_locked=True,
    )
    session.add(decision)
    audit(session, "pre_judgment_locked", participant_id=caller.participant_id,
          scenario_id=assignment.scenario_id, sequence_number=assignment.sequence_number)
    session.commit()

    session.refresh(decision)
    if decision.pre_locked_at is None or not decision.pre_judgment_locked:
        return err("preliminary judgment could not be verified as locked")

    return {
        "ok": True,
        "decision_id": decision.decision_id,
        "period": period,
        "pre_action": decision.pre_action,
        "pre_confidence": decision.pre_confidence,
        "pre_submitted_at": decision.pre_submitted_at.isoformat(),
        "pre_locked_at": decision.pre_locked_at.isoformat(),
        "pre_judgment_locked": True,
        "current_stage": derive_stage(decision),
    }


# ---------------------------------------------------------------- reveal


def _package_view(pkg: DecisionSupportPackage) -> dict[str, Any]:
    """Stored fields only. Nothing here is computed at request time."""
    return {
        "package_id": pkg.package_id,
        "version": pkg.version,
        "hash": pkg.hash,
        "provider_id": pkg.provider_id,
        "model_version": pkg.model_version,
        "use_case": pkg.use_case,
        "output_type": pkg.output_type,
        "detected_condition": pkg.detected_condition,
        "recommended_action": pkg.recommended_action,
        "alternatives": pkg.alternatives,
        "uncertainty": pkg.uncertainty,
        "limitations": pkg.limitations,
        "applicability_boundary": pkg.applicability_boundary,
        "expiration_trigger": pkg.expiration_trigger,
        "provenance": pkg.provenance,
        "data_cutoff": pkg.data_cutoff.isoformat() if pkg.data_cutoff else None,
        "frozen_at": pkg.frozen_at.isoformat() if pkg.frozen_at else None,
    }


def a_researchreveal(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem

    assignment, problem = _resolve_target(session, caller, payload, "researchreveal")
    if problem:
        return problem

    scenario = session.get(Scenario, assignment.scenario_id)
    period = current_period(session, assignment, scenario)
    decision = _decision_for(session, assignment.assignment_id, period)

    # Guarantee 1. The refusal names only the state, never any package content: a refusal that
    # leaked the recommendation would defeat the gate it is enforcing.
    if decision is None or not decision.pre_judgment_locked:
        audit(session, "reveal_denied_unlocked", participant_id=caller.participant_id,
              scenario_id=assignment.scenario_id, sequence_number=assignment.sequence_number)
        session.commit()
        return err("preliminary judgment must be submitted and locked before the decision "
                   "support package can be revealed")

    if decision.reveal_at is not None:
        # Idempotent: re-reading an already revealed package does not move reveal_at, because
        # reveal_at is a measurement of when the participant first saw it.
        pkg = session.get(DecisionSupportPackage, decision.package_id)
        return {
            "ok": True, "already_revealed": True,
            "reveal_at": decision.reveal_at.isoformat(),
            "package": _package_view(pkg) if pkg else None,
            "current_stage": derive_stage(decision),
        }

    if not assignment.package_id:
        return err("no decision support package is attached to this assignment")

    pkg = session.get(DecisionSupportPackage, assignment.package_id)
    if pkg is None:
        return err(f"package not found: {assignment.package_id}")

    # Guarantee 5.
    if pkg.frozen_at is None or not pkg.hash:
        audit(session, "reveal_denied_unfrozen", participant_id=caller.participant_id,
              scenario_id=assignment.scenario_id, package_id=pkg.package_id)
        session.commit()
        return err("decision support package is not frozen and cannot be revealed")

    # Guarantee 6: the hash travels with the decision, so a later edit to the package is
    # detectable against the decisions that were made under it.
    decision.reveal_at = func.now()
    decision.package_id = pkg.package_id
    decision.package_hash = pkg.hash
    audit(session, "package_revealed", participant_id=caller.participant_id,
          scenario_id=assignment.scenario_id, package_id=pkg.package_id, package_hash=pkg.hash)
    session.commit()

    session.refresh(decision)
    if decision.reveal_at is None:
        return err("reveal could not be verified")

    return {
        "ok": True,
        "reveal_at": decision.reveal_at.isoformat(),
        "package": _package_view(pkg),
        "current_stage": derive_stage(decision),
    }


# ---------------------------------------------------------------- final decision


DISPOSITIONS = ("accept", "modify", "reject", "defer", "request_evidence")


def a_researchdecision(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem

    assignment, problem = _resolve_target(session, caller, payload, "researchdecision")
    if problem:
        return problem

    scenario = session.get(Scenario, assignment.scenario_id)
    period = current_period(session, assignment, scenario)
    decision = _decision_for(session, assignment.assignment_id, period)
    if decision is None or decision.reveal_at is None:
        audit(session, "decision_denied_unrevealed", participant_id=caller.participant_id,
              scenario_id=assignment.scenario_id)
        session.commit()
        return err("the decision support package must be revealed before a final decision "
                   "can be recorded")

    if decision.final_submitted_at is not None:
        return err("a final decision has already been recorded for this assignment")

    final_action = str(payload.get("final_action") or "").strip()
    if not final_action:
        return err("final_action is required")
    disposition = str(payload.get("disposition") or "").strip()
    if disposition not in DISPOSITIONS:
        return err(f"disposition must be one of: {', '.join(DISPOSITIONS)}")

    confidence = payload.get("final_confidence")
    if confidence is not None:
        try:
            confidence = int(confidence)
        except (TypeError, ValueError):
            return err("final_confidence must be an integer")
        if not 0 <= confidence <= 100:
            return err("final_confidence must be between 0 and 100")

    decision.final_action = final_action
    decision.disposition = disposition
    decision.rationale = payload.get("rationale")
    decision.final_confidence = confidence
    decision.escalation_level = payload.get("escalation_level")
    decision.owner_role = payload.get("owner_role")
    decision.authority_role = payload.get("authority_role")
    decision.resource_constraint = payload.get("resource_constraint")
    decision.final_submitted_at = func.now()

    # Only the final period completes the assignment. Marking it complete after period 1
    # would advance the participant to their next scenario with periods outstanding.
    period_count = (scenario.period_count if scenario else None) or 1
    assignment.status = ("completed" if _period_number(period) >= period_count
                         else "in_progress")

    audit(session, "final_decision_submitted", participant_id=caller.participant_id,
          scenario_id=assignment.scenario_id, disposition=disposition,
          sequence_number=assignment.sequence_number)
    session.commit()

    session.refresh(decision)
    return {
        "ok": True,
        "decision_id": decision.decision_id,
        "period": period,
        "final_action": decision.final_action,
        "disposition": decision.disposition,
        "final_confidence": decision.final_confidence,
        "final_submitted_at": decision.final_submitted_at.isoformat(),
        "current_stage": derive_stage(decision),
    }


# ---------------------------------------------------------------- admin: packages


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


def a_adminpackagecreate(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Store a pre-generated decision support package.

    The content arrives already written. Nothing in this service generates it, and freezing is what
    admits it to the study: a package without frozen_at and a hash cannot be revealed.
    """
    caller, problem = _require_admin(session, payload, secret, "adminpackagecreate")
    if problem:
        return problem

    version = str(payload.get("version") or "").strip()
    if not version:
        return err("version is required")

    row = DecisionSupportPackage(
        version=version,
        hash="",  # replaced at freeze
        config_id=payload.get("config_id"),
        provider_id=payload.get("provider_id"),
        model_version=payload.get("model_version"),
        use_case=payload.get("use_case"),
        provenance=payload.get("provenance"),
        output_type=payload.get("output_type"),
        detected_condition=payload.get("detected_condition"),
        uncertainty=payload.get("uncertainty"),
        limitations=payload.get("limitations"),
        recommended_action=payload.get("recommended_action"),
        alternatives=payload.get("alternatives"),
        applicability_boundary=payload.get("applicability_boundary"),
        expiration_trigger=payload.get("expiration_trigger"),
        approval_status=payload.get("approval_status") or "draft",
    )
    session.add(row)
    session.flush()

    if payload.get("freeze"):
        row.hash = compute_package_hash(row)
        row.frozen_at = func.now()
        row.approval_status = payload.get("approval_status") or "approved"
        session.flush()

    audit(session, "package_created", created_by=caller.participant_id,
          package_id=row.package_id, version=version, frozen=bool(payload.get("freeze")))
    session.commit()

    session.refresh(row)
    return {"ok": True, "package_id": row.package_id, "version": row.version,
            "hash": row.hash or None,
            "frozen_at": row.frozen_at.isoformat() if row.frozen_at else None,
            "revealable": row.frozen_at is not None and bool(row.hash)}


def a_adminpackagelist(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = _require_admin(session, payload, secret, "adminpackagelist")
    if problem:
        return problem
    rows = session.scalars(select(DecisionSupportPackage)
                           .order_by(DecisionSupportPackage.package_id)).all()
    return {"ok": True, "packages": [
        {"package_id": p.package_id, "version": p.version, "hash": p.hash or None,
         "config_id": p.config_id, "approval_status": p.approval_status,
         "frozen_at": p.frozen_at.isoformat() if p.frozen_at else None,
         "revealable": p.frozen_at is not None and bool(p.hash)}
        for p in rows
    ]}


def a_adminpackageattach(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Attach a package to an assignment.

    Separate from adminassign so a package can be prepared after allocation, and so the attachment
    is its own audited event rather than a side effect of allocating.
    """
    caller, problem = _require_admin(session, payload, secret, "adminpackageattach")
    if problem:
        return problem

    assignment_id = str(payload.get("assignment_id") or "").strip()
    package_id = str(payload.get("package_id") or "").strip()
    if not assignment_id or not package_id:
        return err("assignment_id and package_id are required")

    assignment = session.get(Assignment, assignment_id)
    if assignment is None:
        return err(f"assignment not found: {assignment_id}")
    pkg = session.get(DecisionSupportPackage, package_id)
    if pkg is None:
        return err(f"package not found: {package_id}")

    revealed = session.scalar(
        select(Decision).where(Decision.assignment_id == assignment_id,
                               Decision.reveal_at.is_not(None))
    )
    if revealed is not None:
        # Changing the package after the participant has seen it would silently rewrite what they
        # were shown.
        return err("package already revealed for this assignment and cannot be changed")

    assignment.package_id = package_id
    audit(session, "package_attached", assigned_by=caller.participant_id,
          participant_id=assignment.participant_id, package_id=package_id,
          assignment_id=assignment_id)
    session.commit()
    return {"ok": True, "assignment_id": assignment_id, "package_id": package_id}


DECISION_ACTIONS: dict[str, Callable[[Session, dict, str, int], dict]] = {
    "researchevidenceget": a_researchevidenceget,
    "researchprejudgment": a_researchprejudgment,
    "researchreveal": a_researchreveal,
    "researchdecision": a_researchdecision,
    "adminpackagecreate": a_adminpackagecreate,
    "adminpackagelist": a_adminpackagelist,
    "adminpackageattach": a_adminpackageattach,
}
