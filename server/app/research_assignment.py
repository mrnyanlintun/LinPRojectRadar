"""
Scenario assignment and counterbalancing (B3).

Same contract rules as B2: HTTP 200 with ok:false for application errors, case-insensitive
actions, server-assigned timestamps, role from the session and never the body, every event
audited.

Blinding is the point of this module, so it is enforced here rather than left to the interface.
A participant must not be able to learn which condition they are in, what is coming next, or
anything about another participant, and none of that can depend on the frontend asking politely.
The participant-facing projection is built by a single function, _blind_row, which is the only
place a participant-visible assignment is shaped. Adding a field to it is the only way to leak
one, which makes the leak reviewable in one place instead of scattered across handlers.
"""

from __future__ import annotations

from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from .facade import err
from .models import Project
from .research_identity import ROLE_PARTICIPANT, audit, resolve_caller
from .research_models import (
    Assignment, ConditionSequence, Configuration, Participant, Scenario,
)

# Fields a participant may ever see for one of their own assignments. Deliberately short.
# config_id is absent: it names the condition, which is exactly what must stay hidden.
PARTICIPANT_ASSIGNMENT_FIELDS = ("sequence_number", "scenario_id", "status")


def _blind_row(a: Assignment) -> dict[str, Any]:
    """The only participant-visible shape for an assignment."""
    return {f: getattr(a, f) for f in PARTICIPANT_ASSIGNMENT_FIELDS}


def _admin_row(a: Assignment) -> dict[str, Any]:
    return {
        "assignment_id": a.assignment_id,
        "participant_id": a.participant_id,
        "scenario_id": a.scenario_id,
        "sequence_number": a.sequence_number,
        "config_id": a.config_id,
        "package_id": a.package_id,
        "status": a.status,
    }


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


def current_sequence_number(session: Session, participant_id: str) -> int | None:
    """
    The participant's current position: the lowest sequence_number not yet completed.

    Derived from the assignment rows rather than stored on the participant, so it cannot drift out
    of step with the data it describes. Returns None when every assignment is complete.
    """
    rows = session.scalars(
        select(Assignment).where(Assignment.participant_id == participant_id)
        .order_by(Assignment.sequence_number)
    ).all()
    for a in rows:
        if (a.status or "") != "completed":
            return a.sequence_number
    return None


# ---------------------------------------------------------------- admin: scenarios


def a_adminscenariocreate(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Define a scenario. EVIDENCE IS REQUIRED, and named as a project that exists.

    WHY THIS REFUSES. A scenario with no `evidence_package_id` used to be accepted here and
    assignable below, and the participant it was assigned to reached the decision sequence,
    saw "No evidence project is attached to this period" on the evidence panel, and could still
    commit the PRELIMINARY JUDGMENT against it. That step is irreversible by design. Reveal then
    refused permanently, so the participant was left with the one unrepeatable act of the study
    already spent on an empty panel, and the dead instance still appeared in the export. Found by
    the 2026-08-02 audit, walked end to end.

    Refusing at creation is the earliest point at which the mistake is still cheap: nothing has
    been assigned and no participant has seen anything. `a_adminassign` refuses again for the
    scenarios that already exist, on the same terms, because this guard cannot reach them.

    THE PROJECT MUST EXIST, not merely be a non-empty string. `a_researchevidenceget` resolves
    evidence by `Project.legacy_id == scenario.evidence_package_id` and renders an empty panel
    when that lookup misses, so a typo'd id fails exactly as an absent one does.
    """
    caller, problem = _require_admin(session, payload, secret, "adminscenariocreate")
    if problem:
        return problem

    version = str(payload.get("scenario_version") or "").strip()
    if not version:
        return err("scenario_version is required")

    evidence_id = str(payload.get("evidence_package_id") or "").strip()
    if not evidence_id:
        return err("evidence_package_id is required: a scenario with no evidence would let a "
                   "participant commit an irreversible preliminary judgment against an empty "
                   "evidence panel")
    evidence_project = session.scalars(
        select(Project).where(Project.legacy_id == evidence_id)
    ).first()
    if evidence_project is None:
        return err(f"evidence project not found: {evidence_id}")
    # Training data isolation: a training project must never enter the research chain by any
    # door, including as evidence a research participant is shown. Refused here rather than
    # only at export time, because by export time a participant would already have committed a
    # preliminary judgment against it.
    if evidence_project.is_training:
        return err(f"evidence project {evidence_id} is a training project and cannot be used "
                   f"as research evidence")

    row = Scenario(
        scenario_version=version,
        project_type=payload.get("project_type"),
        period_count=payload.get("period_count"),
        evidence_package_id=evidence_id,
        reference_standard_version=payload.get("reference_standard_version"),
        status=payload.get("status") or "draft",
    )
    session.add(row)
    session.flush()
    audit(session, "scenario_created", scenario_id=row.scenario_id,
          created_by=caller.participant_id, scenario_version=version)
    session.commit()
    return {"ok": True, "scenario_id": row.scenario_id, "scenario_version": version,
            "status": row.status}


def a_adminscenariolist(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = _require_admin(session, payload, secret, "adminscenariolist")
    if problem:
        return problem
    rows = session.scalars(select(Scenario).order_by(Scenario.scenario_id)).all()
    return {"ok": True, "scenarios": [
        {"scenario_id": s.scenario_id, "scenario_version": s.scenario_version,
         "project_type": s.project_type, "period_count": s.period_count,
         "evidence_package_id": s.evidence_package_id,
         "reference_standard_version": s.reference_standard_version, "status": s.status}
        for s in rows
    ]}


# ---------------------------------------------------------------- admin: configurations


def a_adminconfigurationcreate(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = _require_admin(session, payload, secret, "adminconfigurationcreate")
    if problem:
        return problem

    code = str(payload.get("code") or "").strip()
    if code not in ("C0", "C1", "C2"):
        return err("code must be one of C0, C1, C2")
    version = str(payload.get("version") or "").strip()
    if not version:
        return err("version is required")

    row = Configuration(
        code=code, version=version, label=payload.get("label"),
        description=payload.get("description"),
        presentation_spec=payload.get("presentation_spec"),
        elements_included=payload.get("elements_included"),
        active=bool(payload.get("active", False)),
    )
    session.add(row)
    session.flush()

    # Freezing is explicit and one-way in practice: an unfrozen configuration cannot be assigned,
    # so freezing is the act that admits it to the study.
    if payload.get("freeze"):
        row.frozen_at = _server_now_column()
        session.flush()

    audit(session, "configuration_created", created_by=caller.participant_id,
          config_id=row.config_id, code=code, version=version, frozen=bool(payload.get("freeze")))
    session.commit()
    session.refresh(row)
    return {"ok": True, "config_id": row.config_id, "code": code, "version": version,
            "frozen_at": row.frozen_at.isoformat() if row.frozen_at else None}


def _server_now_column():
    from sqlalchemy import func
    return func.now()


def a_adminconfigurationlist(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = _require_admin(session, payload, secret, "adminconfigurationlist")
    if problem:
        return problem
    rows = session.scalars(select(Configuration).order_by(Configuration.code,
                                                          Configuration.version)).all()
    return {"ok": True, "configurations": [
        {"config_id": c.config_id, "code": c.code, "version": c.version, "label": c.label,
         "active": bool(c.active),
         "frozen_at": c.frozen_at.isoformat() if c.frozen_at else None,
         "assignable": c.frozen_at is not None}
        for c in rows
    ]}


# ---------------------------------------------------------------- admin: sequences


def a_adminsequencecreate(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Define one preregistered condition sequence, as data.

    positions is an ordered list of config codes, for example ["C0","C1","C2"]. Stored one row per
    position so the design can be revised without a code change and each version stays queryable.
    """
    caller, problem = _require_admin(session, payload, secret, "adminsequencecreate")
    if problem:
        return problem

    group = str(payload.get("order_group") or "").strip()
    scenario_set = str(payload.get("scenario_set") or "").strip()
    version = str(payload.get("version") or "").strip()
    positions = payload.get("positions")
    if not group or not scenario_set or not version:
        return err("order_group, scenario_set and version are required")
    if not isinstance(positions, list) or not positions:
        return err("positions must be a non-empty list of configuration codes")
    bad = [c for c in positions if c not in ("C0", "C1", "C2")]
    if bad:
        return err(f"positions contains unknown configuration codes: {', '.join(map(str, bad))}")

    existing = session.scalars(
        select(ConditionSequence).where(
            ConditionSequence.order_group == group,
            ConditionSequence.scenario_set == scenario_set,
            ConditionSequence.version == version,
        )
    ).all()
    if existing:
        return err(f"sequence already exists for {group}/{scenario_set} version {version}")

    for index, code in enumerate(positions, start=1):
        session.add(ConditionSequence(
            order_group=group, scenario_set=scenario_set, position=index,
            config_code=code, version=version,
        ))
    session.flush()

    if payload.get("freeze"):
        for row in session.scalars(
            select(ConditionSequence).where(
                ConditionSequence.order_group == group,
                ConditionSequence.scenario_set == scenario_set,
                ConditionSequence.version == version,
            )
        ).all():
            row.frozen_at = _server_now_column()

    audit(session, "condition_sequence_created", created_by=caller.participant_id,
          order_group=group, scenario_set=scenario_set, version=version,
          positions=list(positions), frozen=bool(payload.get("freeze")))
    session.commit()
    return {"ok": True, "order_group": group, "scenario_set": scenario_set, "version": version,
            "positions": list(positions), "frozen": bool(payload.get("freeze"))}


def a_adminsequencelist(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = _require_admin(session, payload, secret, "adminsequencelist")
    if problem:
        return problem
    rows = session.scalars(
        select(ConditionSequence).order_by(
            ConditionSequence.order_group, ConditionSequence.scenario_set,
            ConditionSequence.version, ConditionSequence.position)
    ).all()
    return {"ok": True, "sequences": [
        {"order_group": r.order_group, "scenario_set": r.scenario_set, "version": r.version,
         "position": r.position, "config_code": r.config_code,
         "frozen_at": r.frozen_at.isoformat() if r.frozen_at else None}
        for r in rows
    ]}


# ---------------------------------------------------------------- admin: assign


def resolve_sequence(session: Session, group: str, scenario_set: str,
                     version: str | None) -> tuple[list[ConditionSequence], str | None]:
    """
    Load the ordered, frozen sequence for a group.

    When no version is named the latest frozen one is used, so an allocation never silently picks
    up a draft revision that the committee has not approved.
    """
    query = select(ConditionSequence).where(
        ConditionSequence.order_group == group,
        ConditionSequence.scenario_set == scenario_set,
        ConditionSequence.frozen_at.is_not(None),
    )
    if version:
        query = query.where(ConditionSequence.version == version)

    rows = session.scalars(query).all()
    if not rows:
        return [], (f"no frozen condition sequence for order_group {group!r} and scenario_set "
                    f"{scenario_set!r}" + (f" at version {version!r}" if version else ""))

    if not version:
        version = sorted({r.version for r in rows})[-1]
        rows = [r for r in rows if r.version == version]

    rows.sort(key=lambda r: r.position)
    return rows, None


def a_adminassign(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Allocate a participant's scenario set under a preregistered condition sequence.

    Deterministic given (participant, order_group, scenario_set): the scenario list is sorted, the
    frozen sequence supplies the condition at each position, and the sequence version used is
    recorded on the participant and in the audit trail. Re-running with the same inputs is refused
    rather than silently producing a second allocation.
    """
    caller, problem = _require_admin(session, payload, secret, "adminassign")
    if problem:
        return problem

    target_id = str(payload.get("participant_id") or "").strip()
    if not target_id:
        return err("participant_id is required")
    target = session.get(Participant, target_id)
    if target is None:
        return err(f"participant not found: {target_id}")

    group = str(payload.get("order_group") or "").strip()
    scenario_set = str(payload.get("scenario_set") or "").strip()
    if not group or not scenario_set:
        return err("order_group and scenario_set are required")

    scenario_ids = payload.get("scenario_ids")
    if not isinstance(scenario_ids, list) or not scenario_ids:
        return err("scenario_ids must be a non-empty list")

    # Sorted, so the same inputs always produce the same pairing regardless of request order.
    ordered_scenarios = sorted(str(s) for s in scenario_ids)

    missing = [s for s in ordered_scenarios if session.get(Scenario, s) is None]
    if missing:
        return err(f"unknown scenario_ids: {', '.join(missing)}")

    # EVERY SCENARIO MUST CARRY RESOLVABLE EVIDENCE, checked again here and not only at creation.
    # `a_adminscenariocreate` now refuses to make one without it, but scenarios created before
    # that guard existed are still in the database and still assignable, and the project a
    # scenario names can be renumbered or removed after the scenario was made. This is the guard
    # that stands between an evidence-less scenario and a participant, so it is checked against
    # the projects table at the moment of assignment rather than trusted from creation time.
    #
    # Named per scenario. An allocation is several scenarios at once and "one of them has no
    # evidence" is not something an admin can act on without being told which.
    evidenceless: list[str] = []
    for scenario_id in ordered_scenarios:
        scenario = session.get(Scenario, scenario_id)
        ref = (scenario.evidence_package_id or "").strip()
        evidence_project = session.scalars(
            select(Project).where(Project.legacy_id == ref)
        ).first() if ref else None
        # Re-checked here too, not just at scenario creation: a scenario naming a training
        # project as evidence must not reach a participant, for the same reason a missing
        # project must not.
        if not ref or evidence_project is None or evidence_project.is_training:
            evidenceless.append(f"{scenario.scenario_version or scenario_id}"
                                f"{'' if ref else ' (no evidence project named)'}"
                                f"{f' (names training project {ref})' if evidence_project and evidence_project.is_training else ''}"
                                f"{f' (names missing project {ref})' if ref and evidence_project is None else ''}")
    if evidenceless:
        audit(session, "assignment_denied_no_evidence", participant_id=target_id,
              denied_by=caller.participant_id, scenarios=list(evidenceless))
        session.commit()
        return err("cannot assign: no evidence is attached to " + "; ".join(evidenceless)
                   + ". A participant would reach the preliminary judgment, which cannot be "
                     "undone, with nothing to judge.")

    if session.scalars(select(Assignment).where(Assignment.participant_id == target_id)).first():
        return err(f"participant {target.pseudonymous_code} already has assignments")

    sequence, problem_text = resolve_sequence(session, group, scenario_set,
                                              payload.get("sequence_version"))
    if problem_text:
        return err(problem_text)
    if len(sequence) < len(ordered_scenarios):
        return err(f"condition sequence has {len(sequence)} positions but "
                   f"{len(ordered_scenarios)} scenarios were supplied")

    # Blinding rule 4: only a frozen configuration may be assigned. Resolved per position, so an
    # unfrozen configuration fails the whole allocation rather than half of it.
    resolved: list[tuple[int, str, Configuration]] = []
    for index, scenario_id in enumerate(ordered_scenarios, start=1):
        code = sequence[index - 1].config_code
        config = session.scalar(
            select(Configuration).where(Configuration.code == code,
                                        Configuration.frozen_at.is_not(None))
            .order_by(Configuration.version.desc())
        )
        if config is None:
            unfrozen = session.scalar(select(Configuration).where(Configuration.code == code))
            return err(
                f"configuration {code} is not frozen and cannot be assigned"
                if unfrozen is not None else
                f"no configuration exists for code {code}"
            )
        resolved.append((index, scenario_id, config))

    for index, scenario_id, config in resolved:
        session.add(Assignment(
            participant_id=target_id, scenario_id=scenario_id, sequence_number=index,
            config_id=config.config_id, status="pending",
        ))

    sequence_version = sequence[0].version
    target.order_group = group
    target.scenario_set = scenario_set
    target.condition_sequence = ",".join(s.config_code for s in sequence[:len(ordered_scenarios)])
    target.completion_status = "assigned"

    audit(session, "participant_assigned", participant_id=target_id,
          assigned_by=caller.participant_id, order_group=group, scenario_set=scenario_set,
          sequence_version=sequence_version,
          allocation=[{"sequence_number": i, "scenario_id": s, "config_code": c.code,
                       "config_id": c.config_id} for i, s, c in resolved])
    session.commit()

    return {
        "ok": True,
        "participant_id": target_id,
        "pseudonymous_code": target.pseudonymous_code,
        "order_group": group,
        "scenario_set": scenario_set,
        "sequence_version": sequence_version,
        "condition_sequence": target.condition_sequence,
        "assignments": [{"sequence_number": i, "scenario_id": s, "config_id": c.config_id}
                        for i, s, c in resolved],
    }


def a_adminassignmentlist(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = _require_admin(session, payload, secret, "adminassignmentlist")
    if problem:
        return problem

    query = select(Assignment).order_by(Assignment.participant_id, Assignment.sequence_number)
    target_id = str(payload.get("participant_id") or "").strip()
    if target_id:
        query = query.where(Assignment.participant_id == target_id)

    return {"ok": True, "assignments": [_admin_row(a) for a in session.scalars(query).all()]}


# ---------------------------------------------------------------- participant


def a_researchmyassignments(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    A participant's own assignments, up to and including their current position.

    Blinding rules 1 to 3 all land here. The participant_id comes from the session, so a body
    value cannot redirect it; future rows are filtered out, so the length of the response does not
    reveal how many scenarios remain; and the projection is _blind_row, so no condition-bearing
    field can appear.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem

    # Rule 1: an explicit attempt to read someone else is refused and audited rather than quietly
    # ignored, because the attempt is itself something the audit trail should hold.
    requested = str(payload.get("participant_id") or "").strip()
    if requested and requested != caller.participant_id and not caller.is_admin:
        audit(session, "cross_participant_assignment_read_denied",
              participant_id=caller.participant_id, target_participant_id=requested,
              role=caller.role)
        session.commit()
        return err("not authorized: a participant may only read their own assignments")

    current = current_sequence_number(session, caller.participant_id)
    rows = session.scalars(
        select(Assignment).where(Assignment.participant_id == caller.participant_id)
        .order_by(Assignment.sequence_number)
    ).all()

    # Rule 2: nothing beyond the current position. When everything is complete, current is None
    # and all rows are past, so all are visible.
    visible = [a for a in rows if current is None or a.sequence_number <= current]

    return {"ok": True, "current_sequence_number": current,
            "assignments": [_blind_row(a) for a in visible]}


def a_researchcurrent(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """The single assignment at the participant's current position, and nothing beyond it."""
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem

    requested = str(payload.get("participant_id") or "").strip()
    if requested and requested != caller.participant_id and not caller.is_admin:
        audit(session, "cross_participant_assignment_read_denied",
              participant_id=caller.participant_id, target_participant_id=requested,
              role=caller.role)
        session.commit()
        return err("not authorized: a participant may only read their own assignments")

    current = current_sequence_number(session, caller.participant_id)
    if current is None:
        return {"ok": True, "current_sequence_number": None, "assignment": None,
                "detail": "no outstanding assignment"}

    row = session.scalar(
        select(Assignment).where(Assignment.participant_id == caller.participant_id,
                                 Assignment.sequence_number == current)
    )
    # Stage is derived from the decisions row, never read from participants.current_stage and
    # never taken from the request. A stored stage is a second source of truth that can disagree
    # with the data, and in a blinded flow a stage running ahead of the data is a disclosure.
    from .research_decision import current_period, derive_stage
    from .research_models import Decision

    period = None
    decision = None
    if row is not None:
        scenario = session.get(Scenario, row.scenario_id)
        period = current_period(session, row, scenario)
        decision = session.scalar(
            select(Decision).where(Decision.assignment_id == row.assignment_id,
                                   Decision.period == period)
        )

    return {"ok": True, "current_sequence_number": current,
            "period": period,
            "assignment": _blind_row(row) if row else None,
            "current_stage": derive_stage(decision)}


ASSIGNMENT_ACTIONS: dict[str, Callable[[Session, dict, str, int], dict]] = {
    "adminscenariocreate": a_adminscenariocreate,
    "adminscenariolist": a_adminscenariolist,
    "adminconfigurationcreate": a_adminconfigurationcreate,
    "adminconfigurationlist": a_adminconfigurationlist,
    "adminsequencecreate": a_adminsequencecreate,
    "adminsequencelist": a_adminsequencelist,
    "adminassign": a_adminassign,
    "adminassignmentlist": a_adminassignmentlist,
    "researchmyassignments": a_researchmyassignments,
    "researchcurrent": a_researchcurrent,
}
