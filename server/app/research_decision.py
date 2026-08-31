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

from .facade import err, now_iso
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
        return None, err("not authorized: only the current assignment may be acted on")

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
    from .research_membership import refuse_unless_pm_for_assignment
    problem = refuse_unless_pm_for_assignment(session, caller, assignment, "researchprejudgment")
    if problem:
        return problem

    # T4: the intake questionnaire must be complete before any judgment is recorded.
    #
    # The intake instrument captures the study's moderator variables — experience, industry,
    # certifications, AI familiarity, organisational role, risk attitude. A decision recorded
    # before they exist cannot be entered into the model that needs them, and asking for them
    # afterwards means asking a participant to describe their own background AFTER they have
    # seen how the system behaved, which is exactly the contamination the instrument exists to
    # measure around.
    #
    # T7/T8 built the questionnaire but deliberately did not add this guard, because B4's
    # fixtures predate the profile table and the guard would have failed B4's suite for
    # behaviour B4 never claimed. Those fixtures now complete intake (one line in each
    # enrolment helper), so the guard holds without weakening anything.
    #
    # Placed AFTER the PM check on purpose: test_membership.py asserts that an observer
    # attempting a preliminary judgment is refused with the PM message specifically, and an
    # observer has no reason to have completed intake either. Checking intake first would
    # answer a question about role with a message about questionnaires.
    from .questionnaires import intake_completed
    if not intake_completed(session, caller.participant_id):
        audit(session, "pre_judgment_denied_no_intake", participant_id=caller.participant_id,
              scenario_id=assignment.scenario_id)
        session.commit()
        return err("the intake questionnaire must be completed before a preliminary judgment "
                   "can be recorded")

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
        # T4. The participant's reasoning BEFORE the package was shown — the only record of it
        # there will ever be. Written in this same INSERT, so it is locked from creation.
        pre_assessment=(str(payload.get("pre_assessment")).strip()
                        if payload.get("pre_assessment") else None),
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
    from .research_membership import recommendation_visible, refuse_unless_pm_for_assignment
    problem = refuse_unless_pm_for_assignment(session, caller, assignment, "researchreveal")
    if problem:
        return problem

    scenario = session.get(Scenario, assignment.scenario_id)
    period = current_period(session, assignment, scenario)
    decision = _decision_for(session, assignment.assignment_id, period)

    # Guarantee 1, through THE reveal predicate (research_membership.recommendation_visible,
    # shared with every member read path). The refusal names only the state, never any package
    # content: a refusal that leaked the recommendation would defeat the gate it is enforcing.
    if not recommendation_visible(decision):
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


# T4 extended this from five to eight. The three additions — accept_with_conditions, escalate,
# transfer_authority — are dispositions the research design names but B4 had no value for, so a
# participant who wanted to express them had to flatten their answer into one of the five that
# existed. Purely additive: every previously valid value is still valid, so nothing recorded
# under B4 changes meaning.
#
# escalate appears here AND in the action vocabulary below, and that is deliberate rather than a
# duplication: the action is what to do about the project, the disposition is what the
# participant did with the recommendation. "I escalated, but that is not what the system advised"
# is a distinguishable and analytically important answer.
#
# RUN 98. THE NINTH VALUE, AND WHY THE OTHER EIGHT ARE UNTOUCHED.
#
# The owner's ruling for Run 98 is that everything must record, even agreement, and that a
# fifth disposition -- "record no action within current authority" -- is a real answer a
# participant can give and must be distinguishable from "I judged and declined". No value in
# the eight above says that: `defer` postpones, `reject` refuses, `accept` agrees, and none of
# them states that the participant's own position holds no action to take.
#
# So the list is RECONCILED, NOT OVERWRITTEN. Nothing was removed, renamed or re-meant: all
# eight T4 values are still valid, still validated by `a_researchdecision` below, and every
# stored row keeps exactly the meaning it was written with. One value is APPENDED.
#
# THE STRING NAMES NO AUTHORITY, deliberately. "within current authority" is the participant's
# statement about their own position. The platform records the answer; it does not model, hold
# or assert who has what. There is no authority table behind this value and none is implied.
#
# The column is `Text`, nullable, and carries no constraint or enum, so appending a value needs
# no migration and none was added.
DISPOSITIONS = ("accept", "accept_with_conditions", "modify", "reject", "defer",
                "request_evidence", "escalate", "transfer_authority",
                "no_action_within_current_authority")

# RUN 98. THE FIVE THE GOVERNANCE DECISION CARD OFFERS, code and participant-facing label.
#
# This is a SUBSET of DISPOSITIONS, asserted below, so the card and the research decision form
# can never drift onto two different vocabularies. Four of the five reuse a value that already
# existed; the fifth is the one appended above.
#
# TWO RECONCILIATIONS ARE IMPERFECT AND ARE RECORDED HERE RATHER THAN PAPERED OVER:
#
#   "Defer pending evidence" -> `defer`. The tree holds TWO candidate values, `defer` and
#   `request_evidence`, and they are not the same thing: one postpones, the other asks. The
#   card's option states both at once. `defer` is stored because the recorded fact is that the
#   decision was postponed; `request_evidence` is left in DISPOSITIONS, unaltered, for the
#   research decision form which offers the two separately. Whether the card should offer them
#   separately too is NOT decided here.
#
#   "Override finding" -> `reject`. `reject` is the closest existing value and it is NOT
#   identical: overriding a finding is substituting one's own judgment for it, which is not the
#   same act as refusing it. No new value was invented for this. It is reported for a ruling.
PROJECT_DECISION_DISPOSITIONS = (
    ("accept", "Accept finding"),
    ("modify", "Modify finding"),
    ("defer", "Defer pending evidence"),
    ("reject", "Override finding"),
    ("no_action_within_current_authority", "Record no action within current authority"),
)
assert all(code in DISPOSITIONS for code, _ in PROJECT_DECISION_DISPOSITIONS), \
    "the card's dispositions must be a subset of DISPOSITIONS"

# THE ACTION VOCABULARY, AND WHY IT IS OFFERED BUT NOT ENFORCED.
#
# These are the actions the decision form presents for pre_action and final_action. They are the
# three the analytical layer itself can recommend (simulation/models_gov.py's regret matrix keys:
# monitor, investigate, escalate) plus the two the study's own fixtures have always used
# (re-baseline, defer), so a participant can always answer, and a participant's action is drawn
# from the same universe as the recommendation they are being compared against.
#
# The server deliberately does NOT reject an action outside this tuple. B5's transition suite
# submits a literal "invent-a-new-action" to prove that researchadvance refuses an action with no
# frozen family mapping — an important guarantee about the transition layer that a closed enum
# here would make untestable. Validation therefore stays where B5 put it: at advance time,
# against the ActionFamily table, where an unmapped action is an error rather than a default.
# This constant is a UI contract, served to the client so the form and the server agree on one
# list, not a second validation layer.
#
# OPERATIONAL NOTE: every action here needs an ActionFamily mapping registered before a
# participant using it can advance a period. Registering them is an admin action
# (adminactionfamilycreate), not a code change, which is why this tuple does not assert one.
PARTICIPANT_ACTIONS = ("monitor", "investigate", "escalate", "re-baseline", "defer")

# Primary reason codes. New in T4 — nothing equivalent existed. Closed, because the whole point
# is comparability across participants; a free-text "why" is already captured in rationale.
REASON_CODES = (
    "cost_variance",
    "schedule_variance",
    "evidence_quality",
    "risk_exposure",
    "contractual_or_regulatory",
    "stakeholder_or_authority",
    "insufficient_information",
    "disagree_with_analysis",
)


def a_researchdecision(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem

    assignment, problem = _resolve_target(session, caller, payload, "researchdecision")
    if problem:
        return problem
    from .research_membership import refuse_unless_pm_for_assignment
    problem = refuse_unless_pm_for_assignment(session, caller, assignment, "researchdecision")
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

    # T4. reason_code is validated against a closed vocabulary because comparability across
    # participants is the entire reason it exists; an unconstrained one would just be a second
    # rationale field. It stays OPTIONAL so that B4/B5/B6's existing fixtures, which predate it,
    # continue to record decisions unchanged.
    reason_code = str(payload.get("reason_code") or "").strip() or None
    if reason_code is not None and reason_code not in REASON_CODES:
        return err(f"reason_code must be one of: {', '.join(REASON_CODES)}")

    # Selected from what the evidence screen displayed. Stored as a list of labels — see
    # migration 0011 for why these are labels rather than foreign keys.
    evidence_items = payload.get("evidence_items")
    if evidence_items is not None and not isinstance(evidence_items, list):
        return err("evidence_items must be a list")

    decision.final_action = final_action
    decision.disposition = disposition
    decision.rationale = payload.get("rationale")
    decision.final_confidence = confidence
    decision.escalation_level = payload.get("escalation_level")
    decision.owner_role = payload.get("owner_role")
    decision.authority_role = payload.get("authority_role")
    decision.resource_constraint = payload.get("resource_constraint")
    decision.evidence_items = evidence_items
    decision.reason_code = reason_code
    decision.deadline = payload.get("deadline")
    decision.residual_risk = payload.get("residual_risk")
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
        return None, err("not authorized: ResearchAdmin role required")
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


def a_researchsequencestate(session: Session, payload: dict, secret: str,
                            ttl: int) -> dict[str, Any]:
    """
    Everything the decision interface needs to decide what to render, derived server-side.

    THE CLIENT MUST NOT COMPUTE A STAGE. This action exists so it does not have to: it returns
    the derived stage, the derived period, whether intake is outstanding, whether every
    assignment is finished, and the vocabularies the form renders. A participant who reloads,
    signs out and back in, or returns days later calls this and lands exactly where the rows say
    they are — because nothing about where they are was ever stored on the client.

    It returns NO package content at any stage, not even after the lock. The reveal is an
    explicit participant action with a server-assigned timestamp, and an action that returned
    package content as a side effect of asking "where am I" would make the reveal happen on page
    load. Deliberation time is measured from reveal_at, so that would corrupt the measure.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem

    from .questionnaires import intake_completed

    seq = current_sequence_number(session, caller.participant_id)
    intake_done = intake_completed(session, caller.participant_id)

    state: dict[str, Any] = {
        "ok": True,
        "current_sequence_number": seq,
        # None means every assignment is complete — the signal to route to the debrief.
        "all_assignments_complete": seq is None,
        "intake_completed": intake_done,
        "vocabularies": {
            "actions": list(PARTICIPANT_ACTIONS),
            "dispositions": list(DISPOSITIONS),
            "reason_codes": list(REASON_CODES),
        },
        "server_time": now_iso(),
    }

    assignment, _current = _current_assignment(session, caller.participant_id)
    if assignment is None:
        state.update({"assignment": None, "period": None, "current_stage": None,
                      "scenario_id": None, "period_count": None, "evidence_project_id": None})
        return state

    scenario = session.get(Scenario, assignment.scenario_id)
    period = current_period(session, assignment, scenario)
    decision = _decision_for(session, assignment.assignment_id, period)

    # Which facade project holds the evidence for THIS period — period 1 is the scenario's
    # opening package, later periods are whatever the participant's own transition produced.
    # Same resolution a_researchevidenceget performs, so the two cannot disagree.
    state_ref = scenario.evidence_package_id if scenario else None
    if _period_number(period) > 1:
        from .research_models import Transition
        prior = _decision_for(session, assignment.assignment_id,
                              "P" + str(_period_number(period) - 1))
        if prior is not None:
            tr = session.scalar(
                select(Transition).where(Transition.decision_id == prior.decision_id))
            if tr is not None:
                state_ref = tr.next_state_id

    state.update({
        "assignment": _blind_assignment(assignment),
        "period": period,
        "period_count": scenario.period_count if scenario else None,
        "scenario_id": assignment.scenario_id,
        "evidence_project_id": state_ref,
        "current_stage": derive_stage(decision),
        # Timestamps only — never pre_action or pre_confidence, which would put the participant's
        # locked judgment back on the client where a form could re-post it.
        "pre_locked_at": decision.pre_locked_at.isoformat()
                         if decision and decision.pre_locked_at else None,
        "reveal_at": decision.reveal_at.isoformat()
                     if decision and decision.reveal_at else None,
        "final_submitted_at": decision.final_submitted_at.isoformat()
                              if decision and decision.final_submitted_at else None,
    })
    return state


def _blind_assignment(assignment) -> dict[str, Any]:
    """
    The same three fields research_assignment._blind_row exposes, for the same reason: config_id
    names the condition. Reimplemented rather than imported only to avoid a circular import at
    module scope; the field list is asserted identical by the T4 suite.
    """
    return {"sequence_number": assignment.sequence_number,
            "scenario_id": assignment.scenario_id,
            "status": assignment.status}


DECISION_ACTIONS: dict[str, Callable[[Session, dict, str, int], dict]] = {
    "researchevidenceget": a_researchevidenceget,
    "researchsequencestate": a_researchsequencestate,
    "researchprejudgment": a_researchprejudgment,
    "researchreveal": a_researchreveal,
    "researchdecision": a_researchdecision,
    "adminpackagecreate": a_adminpackagecreate,
    "adminpackagelist": a_adminpackagelist,
    "adminpackageattach": a_adminpackageattach,
}
