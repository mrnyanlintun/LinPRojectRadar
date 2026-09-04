"""
Training mode run 4: the debrief. What was spent, what closed, and what the alternatives
would have cost.

Everything here is computed by the deterministic engine over the run's own record — no model
call, no estimate, no judgement adjective. The debrief exists because the consequences of a
decision are several periods away from the decision, and it must say WHY something happened,
not only that it did: an incident that followed acceleration is attributed to the acceleration
(the engine recorded the cause when it fired), or the trainee reads it as bad luck, which is
the specific failure mode this design exists to avoid.

THE COUNTERFACTUAL IS A REPLAY, NEVER AN ESTIMATE. "What if you had escalated when the
recommendation first appeared" is answered by running the SAME pure engine from the same
initial state with the first decision replaced and the trainee's remaining decisions replayed
verbatim. Where that replay cannot proceed honestly — the trainee already escalated first, or
a later decision no longer fits the replayed world (a stop work order response with no stop
work order, or the reverse) — the debrief says the counterfactual is unavailable and why,
rather than inventing a figure across the divergence. An estimated counterfactual would be the
narrator judging after all, one layer down.
"""

from __future__ import annotations

from typing import Any

from .simulation.band_display import band_figure
from .training_engine import (
    PERIODS_TOTAL, advance, build_disclaimer, initial_state,
)


def _cpi(state: dict[str, Any]) -> float | None:
    return (state["ev"] / state["ac"]) if state["ac"] else None


def _spi(state: dict[str, Any]) -> float | None:
    return (state["ev"] / state["pv"]) if state["pv"] else None


def _spend_summary(state: dict[str, Any],
                   against: dict[str, Any] | None = None) -> dict[str, Any]:
    """The position, with the two ratios PRINTED rather than decided at three decimals.

    RUN 136, F3. This carried two faults of the H1 family. `round` is half-to-EVEN and every
    other `_round3` on this platform is `js_round`, half-UP, so a CPI of 0.8995 read 0.899 here
    and 0.900 everywhere else -- two algebraically equivalent paths to one ratio, which R1
    forbids. And the debrief exists to set the played position BESIDE the replayed one: two
    ratios that genuinely differ printed as the same figure, so a real difference between the
    run played and the run that might have been read as no difference at all.

    `against` is the other state in that comparison. The ratios are computed at full precision
    and printed through the shared `band_display` rule, treating the other side's ratio as the
    boundary the figure must stay on its own side of -- so the printed figures grow a decimal
    exactly when they would otherwise collapse onto each other, and are unchanged otherwise.
    Nothing here compares with a tolerance and nothing rounds a decision.
    """
    baseline = state["baseline_contract_sum"]
    cpi, spi = _cpi(state), _spi(state)
    other_cpi = _cpi(against) if against is not None else None
    other_spi = _spi(against) if against is not None else None
    return {
        "float_spent_days": state["float_consumed_days"],
        "float_total_days": state["float_total_days"],
        "contingency_spent": round(state["contingency_original"]
                                   - state["contingency_remaining"], 2),
        "contingency_original": state["contingency_original"],
        "cost_over_earned": round(state["ac"] - state["ev"], 2),
        "recovered_by_change_order": round(state["revised_contract_sum"] - baseline, 2),
        "owner_credibility": state["owner_credibility"],
        "liquidated_damages_exposure": state["liquidated_damages_exposure"],
        "cpi": None if cpi is None else band_figure(
            cpi, () if other_cpi is None else (other_cpi,), 3),
        "spi": None if spi is None else band_figure(
            spi, () if other_spi is None else (other_spi,), 3),
    }


def _matter_outcome(matter: dict[str, Any] | None, label: str) -> dict[str, Any] | None:
    if not matter:
        return None
    return {
        "matter": label,
        "status": matter.get("status"),
        "entitlement": matter.get("entitlement"),
        "estimated_cost": matter.get("estimated_cost"),
        "recovered_amount": matter.get("recovered_amount"),
    }


def _quality_outcome(quality: dict[str, Any] | None) -> dict[str, Any] | None:
    """
    The failed inspection's outcome. A shape of its own, not `_matter_outcome`'s: the quality
    thread has no `entitlement`, and `closeout_exposure` is the figure the brief asks the
    debrief to surface -- what accepting nonconforming work left behind at the end.
    """
    if not quality:
        return None
    return {
        "matter": "the failed inspection",
        "status": quality.get("status"),
        "defect_value": quality.get("defect_value"),
        "periods_deferred": quality.get("periods_deferred"),
        "closeout_exposure": quality.get("closeout_exposure") or 0.0,
    }


def _resource_outcome(state: dict[str, Any]) -> dict[str, Any] | None:
    """
    The trade shortage's outcome, and the figure that matters after the fact: what the crews
    were still earning at the end. A shortage left open does not appear as a lump sum anywhere,
    because its cost was taken out of every period's earning while it ran -- so the debrief has
    to name it, or a trainee reads the lost EV as bad luck.
    """
    resources = state.get("resources")
    if not resources:
        return None
    adequacy = state.get("crew_adequacy", 1.0)
    return {
        "matter": "the trade shortage",
        "status": resources.get("status"),
        "resolution": resources.get("resolution"),
        "periods_short": resources.get("periods_short"),
        "crew_adequacy": adequacy,
        "productivity_pct": round(adequacy * 100),
    }


def _incident_findings(state: dict[str, Any]) -> list[dict[str, Any]]:
    """
    One finding per incident, with the WHY. The cause was recorded by the engine when the
    incident fired, so the attribution here is a read, not a reconstruction.
    """
    findings = []
    for incident in state.get("incidents") or []:
        cause = incident.get("cause")
        if cause == "acceleration":
            why = ("This stop work order followed the accelerated periods: acceleration "
                   "raises the chance of an incident, and this one is its consequence, not "
                   "bad luck.")
        else:
            why = ("This stop work order followed a near miss that no decision of yours "
                   "caused. What your earlier decisions DID set is what it cost: the days "
                   "it took fell on whatever float remained.")
        findings.append({
            "period": incident.get("period_occurred"),
            "cause": cause,
            "response": incident.get("response"),
            "days_lost": incident.get("days_lost"),
            "why": why,
        })
    return findings


def _replay(contract_form: str, contract_value: float, conditions: str, facility: str,
            decisions: list[str]) -> dict[str, Any]:
    state = initial_state(contract_form, contract_value, conditions, facility)
    for decision in decisions:
        state = advance(state, decision)
    return state


def _counterfactual(run_meta: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """
    The position had the trainee escalated at the first decision, with everything else they
    actually did replayed verbatim. Honest or absent, never estimated.
    """
    decisions = [d["decision"] for d in state.get("decisions") or []]
    if not decisions:
        return {"available": False,
                "reason": "no decisions were made, so there is nothing to compare"}
    if decisions[0] == "escalate":
        return {"available": False,
                "reason": ("you escalated at the first opportunity; the counterfactual is "
                           "the run you played")}
    altered = ["escalate"] + decisions[1:]
    try:
        replayed = _replay(run_meta["contract_form"], run_meta["contract_value"],
                           run_meta["conditions"], run_meta["facility"], altered)
    except ValueError as exc:
        # The replayed world diverged structurally from the played one — typically a stop
        # work order response falling where the replay has no stop work order, or the
        # reverse. A figure carried across that divergence would be an estimate wearing a
        # computation's clothes.
        return {"available": False,
                "reason": ("the replayed run diverges structurally from the one played "
                           f"({exc}), so an honest figure cannot be computed for it")}
    return {
        "available": True,
        "description": ("The engine replayed your run with one change: escalating at the "
                        "first decision, when the recommendation first appeared, with every "
                        "later decision of yours unchanged."),
        "position": _spend_summary(replayed, against=state),
        # The played state's own summary is built in `build_debrief`, which needs this state
        # to print the two positions against each other. Popped there; never served.
        "_replayed_state": replayed,
        "claim": _matter_outcome(replayed.get("dispute"), "the change"),
        "site_condition": _matter_outcome(replayed.get("dsc"), "the site condition"),
        "quality": _quality_outcome(replayed.get("quality")),
        "resources": _resource_outcome(replayed),
    }


def build_debrief(run_meta: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """
    The full debrief for a COMPLETE run. `run_meta` carries contract_form, contract_value,
    conditions, facility. Pure: same run, same debrief, on any machine on any day.
    """
    counterfactual = _counterfactual(run_meta, state)
    replayed = counterfactual.pop("_replayed_state", None)
    return {
        "periods_played": min(state["period"] - 1, PERIODS_TOTAL),
        "spent": _spend_summary(state, against=replayed),
        "closed": [m for m in (
            _matter_outcome(state.get("dispute"), "the change"),
            _matter_outcome(state.get("dsc"), "the site condition"),
        ) if m is not None],
        "quality": _quality_outcome(state.get("quality")),
        "resources": _resource_outcome(state),
        "incidents": _incident_findings(state),
        "decisions": list(state.get("decisions") or []),
        "counterfactual": counterfactual,
        "disclaimer": build_disclaimer(run_meta["contract_form"]),
    }
