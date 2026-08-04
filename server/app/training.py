"""
Training mode: the flag and the gate, run 1.

Training mode is a product feature, not part of the study: an operational user works a
generated project, decides, and the next period changes in response. NOTHING IN THIS RUN
GENERATES A TRAINING PROJECT OR ADVANCES A PERIOD. Later runs build that. This module builds
only the two things that must exist before any of it: the flag that turns the feature on, and
the refusal that keeps a research account off it wherever the flag is set.

WHY THIS IS ENFORCED ON THE SERVER, THE SAME WAY THEME AND THE TECHNICAL REVIEWER ARE

A previous session found an anonymous `getportfoliohealth` bypassing a flag that a signed-in
user with it off was held to (`gate_action` leaves a sessionless caller alone, because most
gated actions have nothing to check without a session). A hidden nav item is not a gate for the
same reason: hiding the "Train" tab stops a browser from showing the control, and says nothing
about a caller who posts the action directly. So `a_trainingstatus` below resolves the caller
itself, the same defence-in-depth `a_themeset` uses for the research refusal it is already
covered by upstream — refusing an ABSENT session on its own, before it ever asks what the flag
says, closes exactly the gap the previous session found.

RESEARCH IS REFUSED UNCONDITIONALLY, NOT BY THE FLAG DEFAULTING OFF. `default_for_account`
already defaults a research account's flags to disabled, so an admin who never touches the
`training` key gets the right answer by accident. That is not enough: an admin CAN set
`training: true` on a research participant's row (nothing today stops them, and archiving or
reassigning an account does not clear stored features), and the moment that happens the
default-off protection is gone. `training` is listed in `RESEARCH_FORBIDDEN_ACTIONS` for exactly
the reason `themeset` and `projectcreate` are: the refusal must not depend on nobody having
flipped the flag by mistake.
"""

from __future__ import annotations

from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from .facade import err
from .features import feature_enabled
from .models import Project
from .research_identity import audit, resolve_caller
from .research_models import ComputedResult, TrainingRun, new_ulid
from .training_engine import (
    CONDITION_PROFILES, CONTRACT_FORMS, DECISIONS, DEFAULT_CONTRACT_VALUE, DEFAULT_FACILITY,
    LD_RATES_BY_FACILITY, MAX_CONTRACT_VALUE, MIN_CONTRACT_VALUE, PERIODS_TOTAL, RESPONSES,
    advance, allowed_decisions, build_brief, dsc_position, initial_state, notice_position,
    signal_inputs_from_state,
)

__all__ = ["TRAINING_ACTIONS"]

# Test seam for narration, mirroring documents.set_extractor_override: a module-level override,
# deliberately not a payload key. None means normal resolution (training_narration.narrate,
# which itself degrades to None without a key). The tests install a stub to prove the layer is
# carried when present and that the engine is byte-identical with and without it.
_NARRATOR_OVERRIDE = None


def set_narrator_override(narrator) -> None:
    global _NARRATOR_OVERRIDE
    _NARRATOR_OVERRIDE = narrator


def _narrate(view: dict) -> str | None:
    """Never raises: narration is a layer, not a dependency."""
    try:
        if _NARRATOR_OVERRIDE is not None:
            return _NARRATOR_OVERRIDE(view)
        from .training_narration import narrate
        return narrate(view)
    except Exception:  # noqa: BLE001 - a narration fault must never stop the run
        return None


def _require_operational(session: Session, payload: dict, secret: str):
    """
    The shared entry check for every training action: a resolved caller, refused for research
    accounts. Redundant with `gate_action`'s RESEARCH_FORBIDDEN_ACTIONS refusal, which runs
    before dispatch — repeated here for the same reason `a_themeset` repeats its own check: a
    handler that assumes an upstream gate breaks silently the day the gate is refactored.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return None, problem
    if caller.participant.account_type == "research":
        audit(session, "training_denied_research", participant_id=caller.participant_id,
              account_type=caller.participant.account_type)
        session.commit()
        return None, err("not available for this account: training mode is an operational "
                         "feature.")
    return caller, None


def _own_run(session: Session, caller, payload: dict) -> tuple[TrainingRun | None, dict | None]:
    """The caller's run: by run_id when given, else their most recent. Never someone else's."""
    run_id = str(payload.get("run_id") or "").strip()
    if run_id:
        run = session.get(TrainingRun, run_id)
        if run is None or run.participant_id != caller.participant_id:
            # One message for absent and not-yours, the same refusal shape the read guard uses,
            # so an id cannot be probed for existence.
            return None, err(f"training run not found: {run_id}")
        return run, None
    run = session.scalar(
        select(TrainingRun).where(TrainingRun.participant_id == caller.participant_id)
        .order_by(TrainingRun.created_at.desc(), TrainingRun.run_id.desc())
    )
    if run is None:
        return None, err("no training run exists for this account yet; start one")
    return run, None


def _store_period(session: Session, run: TrainingRun, project: Project) -> dict:
    """
    Period generation: project the state into signalInputs and run the platform's NORMAL
    computation path (`documents.run_and_store` — the same function the document path calls
    from `_compute_and_store`). No documents, no extraction, no filing; `source_documents` is
    an empty list because nothing produced this period but the state, and inventing provenance
    would be worse than stating none.
    """
    from .documents import run_and_store
    si, cutoff = signal_inputs_from_state(run.state)
    si["events"] = []
    return run_and_store(session, project, run.state["period"], si, cutoff,
                         source_documents=[])


def _state_view(session: Session, run: TrainingRun, project: Project) -> dict[str, Any]:
    """Everything the screen needs, in one shape. The brief is always included (Part 4)."""
    from .documents import _result_view
    row = session.scalar(
        select(ComputedResult).where(
            ComputedResult.project_id == project.id,
            ComputedResult.period == run.state["period"],
            ComputedResult.superseded_by.is_(None),
        )
    )
    # The hazard accumulator is REDACTED from every response: at the threshold it forecasts
    # the next incident deterministically, and a foreseen near miss teaches nothing. Same
    # reasoning as the run 2 handoff note about never shipping the event schedule.
    visible_state = {k: v for k, v in run.state.items() if k != "hazard"}
    return {
        "ok": True,
        "run_id": run.run_id,
        "project": project.legacy_id,
        "status": run.status,
        "period": run.state["period"],
        "periods_total": PERIODS_TOTAL,
        "brief": build_brief(run.contract_form, run.contract_value, run.conditions,
                             run.state.get("facility") or DEFAULT_FACILITY),
        "state": visible_state,
        "notice": notice_position(run.state),
        # Run 4: the site condition's own clock, on its own clause. None before discovery.
        "dsc_notice": dsc_position(run.state),
        "allowed_decisions": list(allowed_decisions(run.state)),
        "decisions": list(run.state.get("decisions") or []),
        # Module-level recommendations (the analytical layer's own recommended actions) are
        # the recommendation surface in training: there is no researcher-authored package, and
        # a trainee is exactly who they exist for. No reveal gate applies — that gate protects
        # a research pre-judgment, which a training run does not have.
        "result": _result_view(row, include_recommendation=True) if row else None,
    }


def a_trainingstatus(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Whether this caller may use training mode right now.

    Read-only, and safe to call before the "Train" nav item is drawn: the frontend uses this to
    decide whether to show the tab at all, but showing the tab is a convenience, not the
    enforcement. Every action this run does not yet build will register under the same
    `GATED_ACTIONS["training"]` key and go through the identical two checks.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    participant = caller.participant

    if participant.account_type == "research":
        # Redundant with `gate_action`'s RESEARCH_FORBIDDEN_ACTIONS refusal (features.py), which
        # runs before this handler is ever reached. Repeated here for the same reason
        # `a_themeset` repeats its own check: a handler that assumes an upstream gate is a
        # handler that breaks silently the day the gate is refactored.
        audit(session, "training_denied_research", participant_id=caller.participant_id,
              account_type=participant.account_type)
        session.commit()
        return err("not available for this account: training mode is an operational feature.")

    enabled = feature_enabled(session, participant, "training")
    return {
        "ok": True,
        "participant_id": caller.participant_id,
        "account_type": participant.account_type,
        "enabled": enabled,
    }


def a_trainingstart(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Open a run: create the training project (is_training set AT CREATION, run 1's rule), the
    run row, and period one's computed result, in one transaction. The contract form is chosen
    per run and its periods follow from it, not overridable; contract value is clamped, never
    trusted raw, because liquidated damages derive from it.
    """
    caller, problem = _require_operational(session, payload, secret)
    if problem:
        return problem
    if not feature_enabled(session, caller.participant, "training"):
        # gate_action already refused this for /exec callers; repeated for direct calls.
        return err("not available: training mode is disabled for this account")

    contract_form = str(payload.get("contract_form") or "A201-2017").strip()
    if contract_form not in CONTRACT_FORMS:
        return err(f"contract_form must be one of: {', '.join(CONTRACT_FORMS)}")
    conditions = str(payload.get("conditions") or "exacting").strip()
    if conditions not in CONDITION_PROFILES:
        return err(f"conditions must be one of: {', '.join(CONDITION_PROFILES)}")
    facility = str(payload.get("facility") or DEFAULT_FACILITY).strip()
    if facility not in LD_RATES_BY_FACILITY:
        return err(f"facility must be one of: {', '.join(LD_RATES_BY_FACILITY)}")
    raw_value = payload.get("contract_value", DEFAULT_CONTRACT_VALUE)
    try:
        contract_value = float(raw_value)
    except (TypeError, ValueError):
        return err(f"contract_value is not a number: {raw_value!r}")
    if not (MIN_CONTRACT_VALUE <= contract_value <= MAX_CONTRACT_VALUE):
        return err("contract_value must be between 1,000,000 and 500,000,000")

    run_id = new_ulid()
    project = Project(
        legacy_id=f"TRN-{run_id[-8:]}",
        doc={"projectId": f"TRN-{run_id[-8:]}", "name": "Training run",
             "sector": "training", "events": []},
        is_training=True,
    )
    session.add(project)
    session.flush()

    # The trainee is the project's PM, written in the same transaction, matching the rule that
    # a project cannot exist without one (admin-and-membership work, 2026-08-02).
    from .research_models import ProjectMember
    session.add(ProjectMember(project_id=project.id, user_key=caller.participant_id,
                              project_role="PM", added_by=caller.participant_id))

    run = TrainingRun(
        run_id=run_id,
        project_id=project.id,
        participant_id=caller.participant_id,
        contract_form=contract_form,
        contract_value=contract_value,
        conditions=conditions,
        period=1,
        state=initial_state(contract_form, contract_value, conditions, facility),
        history=[],
    )
    session.add(run)
    session.flush()

    _store_period(session, run, project)
    audit(session, "training_run_started", participant_id=caller.participant_id,
          run_id=run_id, project_id=project.legacy_id, contract_form=contract_form,
          conditions=conditions, contract_value=contract_value, facility=facility)
    session.commit()
    session.refresh(run)
    view = _state_view(session, run, project)
    view["narrative"] = _narrate(view)
    return view


def a_trainingstate(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """The current position of a run: brief, state, notice clock, signals. Read-only."""
    caller, problem = _require_operational(session, payload, secret)
    if problem:
        return problem
    run, problem = _own_run(session, caller, payload)
    if problem:
        return problem
    project = session.get(Project, run.project_id)
    if project is None:
        return err("the training project behind this run no longer exists")
    return _state_view(session, run, project)


def a_trainingdecision(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Record a decision and advance: state moves by the effect table (`training_engine.advance`,
    pure and deterministic), the next period's signals compute through the normal path, and
    the next period renders from what was stored. One decision per period, by construction:
    the state's period advances with the decision, so a second post against the same period
    simply decides the NEXT one, which is the loop working, not a replay.
    """
    caller, problem = _require_operational(session, payload, secret)
    if problem:
        return problem
    run, problem = _own_run(session, caller, payload)
    if problem:
        return problem
    if run.status != "active":
        return err("this training run is complete; start a new one")
    project = session.get(Project, run.project_id)
    if project is None:
        return err("the training project behind this run no longer exists")

    decision = str(payload.get("decision") or "").strip().lower()
    if decision not in DECISIONS + RESPONSES:
        return err(f"decision must be one of: {', '.join(DECISIONS + RESPONSES)}")

    before = run.state
    try:
        after = advance(before, decision)
    except ValueError as exc:
        # A response with no stop work order, or a standard decision during one: the engine
        # names the reason and the trainee reads it verbatim.
        return err(str(exc))
    entry = {"period": before["period"], "decision": decision, "state_after": after}
    run.state = after
    run.history = list(run.history or []) + [entry]
    run.period = after["period"]

    if after["period"] > PERIODS_TOTAL:
        run.status = "complete"
    else:
        _store_period(session, run, project)

    audit(session, "training_decision", participant_id=caller.participant_id,
          run_id=run.run_id, period=entry["period"], decision=decision)
    session.commit()
    session.refresh(run)

    view = _state_view(session, run, project)
    view["decided"] = {"period": entry["period"], "decision": decision}
    view["narrative"] = _narrate(view)
    return view


def a_trainingdebrief(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    The debrief, for a COMPLETE run: what was spent, what closed, why the incidents happened,
    and the replayed counterfactual (or the stated reason one cannot be computed). Refused
    while the run is active — mid-run it would be a running commentary, and the consequences
    it exists to connect have not landed yet.
    """
    caller, problem = _require_operational(session, payload, secret)
    if problem:
        return problem
    run, problem = _own_run(session, caller, payload)
    if problem:
        return problem
    if run.status != "complete":
        return err("the debrief is available when the run is complete; "
                   f"the run is at period {run.state.get('period')} of {PERIODS_TOTAL}")
    from .training_debrief import build_debrief
    debrief = build_debrief(
        {"contract_form": run.contract_form, "contract_value": run.contract_value,
         "conditions": run.conditions,
         "facility": run.state.get("facility") or DEFAULT_FACILITY},
        run.state)
    audit(session, "training_debrief_read", participant_id=caller.participant_id,
          run_id=run.run_id)
    session.commit()
    return {"ok": True, "run_id": run.run_id, "debrief": debrief}


TRAINING_ACTIONS: dict[str, Callable[[Session, dict, str, int], dict]] = {
    "trainingstatus": a_trainingstatus,
    "trainingstart": a_trainingstart,
    "trainingstate": a_trainingstate,
    "trainingdecision": a_trainingdecision,
    "trainingdebrief": a_trainingdebrief,
}
