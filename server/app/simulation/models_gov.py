"""
Group B models: signal synthesis, evidence combination, governance thresholds, decision
optimization. Ported from assets/js/simulations.js, validated against the JavaScript executed in
a browser. See VALIDATION.md for the per-module comparison.

INPUT CONTRACTS — three shapes share the registry's one signature fn(si, rand, period_cutoff):

- B1.2–B1.4 (voting ensembles) consume the ASSEMBLED PROJECT: si["signals"] holding the primary
  signal package ({mc, cusum, doc} each with .status and {decision} with .state) and
  si["simulationSignals"]["signal_array"] holding per-module results with .status_color.
- B2.1 (DST) and B2.2–B2.9 consume the assembled signal keys directly from si: si["evm"]
  ({cpi, spi}), si["mc"] ({p80DeltaPct}), si["cusum"] ({breached}), si["doc"] ({score}) and,
  for DST's agreement field, si["decision"] ({state}). In the browser these arrive as
  `existingSignals`; on the server the caller assembles them into the same dict.
- B2.10–B2.20, B3.x and B4.x consume flat signalInputs (cpi/spi/docRiskScore/…), as Group A does.

Quirks reproduced deliberately (all validated):

- DST reads `existingSignals.doc ? doc.score : 0`. A PRESENT doc with an undefined score makes
  both `< 0.30` and `< 0.70` false in JavaScript, landing in the Red-evidence branch; an absent
  doc lands Green. Reproduced exactly. Every other module uses `doc.score || 0`.
- voteBucket maps anything containing "Red" to Red, exactly "Amber"/"Yellow" to themselves, and
  EVERYTHING else — including "light-amber" and "Complete" — to Green. Reproduced, not fixed.
- Tie directions differ by site: dstFuse's band reduce keeps the EARLIER state on ties, runDST's
  max-state reduce and the voting reduces keep the LATER one. Each is reproduced per-site.
- Neutrosophic/IntervalFuzzy/ZNumbers/PLTS/Plithogenic emit an AMBER stub (not an abstention)
  when no signal contributes — that is what the instrument has always done.
- MARCOS and Linear Programming can divide by zero in JavaScript yet still produce a FINITE
  score via Infinity arithmetic; `_jsdiv` reproduces that limit instead of refusing.
- FAR / OMB A-11 / EVM Reporting / What-If divide by cpi with no finite fallback: cpi exactly 0
  abstains per the standing NaN/Infinity rule.
- The Object.keys reductions in the voting modules iterate insertion order. DO NOT SORT.
"""

from __future__ import annotations

import math
from typing import Any, Callable

from .fusion import dst_combine, normalise_status
from .models import ABSTAIN_DECISION_STRUCTURE_ABSENT, check_inputs, insufficient
from .models_ext import _derived, _js_str
from .rng import js_round, round1, round2

_round3 = lambda v: js_round(v * 1000) / 1000  # noqa: E731


def _jsdiv(a: float, b: float) -> float:
    """JavaScript division: x/0 is ±Infinity (NaN for 0/0), never an exception."""
    if b == 0:
        if a == 0:
            return float("nan")
        return math.inf if a > 0 else -math.inf
    return a / b


# ================================================================ B2.1 Dempster-Shafer


def run_dst(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    ex = si
    sources: list[dict] = []

    # Presence checks are `is not None`, not Python truthiness: a JS empty object {} is truthy,
    # so an empty mc/cusum/doc still takes the signal-present branch there.
    evm = ex.get("evm")
    cpi = evm.get("cpi") if evm is not None else None
    spi = evm.get("spi") if evm is not None else None

    # D1. With none of the four signals present, the three vacuous {0.25 × 4} masses below
    # combined to nothing while the doc arm's `absent -> score 0 -> Green` branch supplied a
    # real Green mass, so the fusion returned Green on every project the server computed. This
    # is Dempster-Shafer: the honest representation of no evidence is no combination, not a
    # combination of ignorance with one asserted belief.
    if not (cpi and spi) and ex.get("mc") is None and ex.get("cusum") is None \
            and ex.get("doc") is None:
        return insufficient("DST_Evidence_Combination")

    if cpi and spi:
        evm_min = min(cpi, spi)
        if evm_min >= 0.95:
            sources.append({"Green": 0.80, "Amber": 0.10, "Red": 0.05, "Unknown": 0.05})
        elif evm_min >= 0.90:
            sources.append({"Green": 0.10, "Amber": 0.70, "Red": 0.15, "Unknown": 0.05})
        else:
            sources.append({"Green": 0.05, "Amber": 0.15, "Red": 0.75, "Unknown": 0.05})
    else:
        sources.append({"Green": 0.25, "Amber": 0.25, "Red": 0.25, "Unknown": 0.25})

    mc = ex.get("mc")
    if mc is not None:
        p80 = mc.get("p80DeltaPct") or 0
        if p80 <= 5:
            sources.append({"Green": 0.75, "Amber": 0.15, "Red": 0.05, "Unknown": 0.05})
        elif p80 <= 10:
            sources.append({"Green": 0.10, "Amber": 0.65, "Red": 0.20, "Unknown": 0.05})
        else:
            sources.append({"Green": 0.05, "Amber": 0.10, "Red": 0.80, "Unknown": 0.05})
    else:
        sources.append({"Green": 0.25, "Amber": 0.25, "Red": 0.25, "Unknown": 0.25})

    cusum = ex.get("cusum")
    if cusum is not None:
        if not cusum.get("breached"):
            sources.append({"Green": 0.75, "Amber": 0.15, "Red": 0.05, "Unknown": 0.05})
        else:
            sources.append({"Green": 0.05, "Amber": 0.15, "Red": 0.75, "Unknown": 0.05})
    else:
        sources.append({"Green": 0.25, "Amber": 0.25, "Red": 0.25, "Unknown": 0.25})

    doc = ex.get("doc")
    # JS: `doc ? doc.score : 0` — a present doc with an undefined score makes both comparisons
    # below false and lands in the Red branch. Absent doc -> 0 -> Green.
    doc_score = (doc.get("score") if doc is not None else 0)
    if doc_score is not None and doc_score < 0.30:
        sources.append({"Green": 0.75, "Amber": 0.15, "Red": 0.05, "Unknown": 0.05})
    elif doc_score is not None and doc_score < 0.70:
        sources.append({"Green": 0.10, "Amber": 0.70, "Red": 0.15, "Unknown": 0.05})
    else:
        sources.append({"Green": 0.05, "Amber": 0.15, "Red": 0.75, "Unknown": 0.05})

    result = dict(sources[0])
    for s in sources[1:]:
        result = dst_combine(result, s)

    # JS reduce with `>` keeps the LATER state on ties.
    max_state = "Green"
    for b in ("Amber", "Red"):
        max_state = max_state if result[max_state] > result[b] else b

    decision = ex.get("decision")
    conservative = decision.get("state") if decision is not None else None
    # JS `a && expr`: null when conservative is null/'' — not False.
    agrees = (max_state.lower() == conservative.lower()) if conservative else conservative
    conflict = result.get("conflict", 0.0)
    conflict_level = "High" if conflict > 0.3 else ("Moderate" if conflict > 0.1 else "Low")
    status = "Red" if max_state == "Red" else ("Amber" if max_state == "Amber" else "Green")

    return {
        "method_class": "DST_Evidence_Combination",
        "status_color": status,
        "belief_green": round2(result["Green"]),
        "belief_amber": round2(result["Amber"]),
        "belief_red": round2(result["Red"]),
        "belief_unknown": round2(result["Unknown"]),
        "conflict_mass": round2(conflict),
        "conflict_level": conflict_level,
        "agrees_with_conservative": agrees,
        "conservative_state": conservative,
        "evidence_metric": (
            f"Belief: Green {int(js_round(result['Green'] * 100))}% · "
            f"Amber {int(js_round(result['Amber'] * 100))}% · "
            f"Red {int(js_round(result['Red'] * 100))}% · "
            f"Conflict mass {int(js_round(conflict * 100))}%"
        ),
    }


# ================================================================ B1 voting ensembles


def _vote_bucket(status) -> str | None:
    """
    Bucket one status onto a band, or None to cast no vote at all.

    THE FIFTEEN DEFECTS, defect 1, extended to the three voting ensembles per the adapter run's
    incidental finding 2. This function used to match `"Red" in status` and then EXACTLY "Amber"
    or EXACTLY "Yellow", with a final `else Green`. Every one of those tests is case-sensitive
    and capitalised, while the assembled primary signals these three ensembles read arrive in
    LOWERCASE from the instrument's own assembler. So `red` was not Red, `light-amber` was not
    Amber, and an unrecognised value was not refused: all three landed in the final else and
    voted GREEN. The forecast, the control chart and the document risk signals therefore voted
    green on every project regardless of what they said.

    Two changes, and they are separate. Matching now runs through the shared vocabulary, so
    casing cannot decide a vote. And an unrecognised value now casts NO VOTE rather than a Green
    one, because a value this platform does not recognise is not evidence that a project is well.
    """
    return normalise_status(status)


def run_weighted_voting(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    project = si or {}
    s = project.get("signals") or {}
    sim = (project.get("simulationSignals") or {}).get("signal_array") or []
    votes = {"Green": 0, "Yellow": 0, "Amber": 0, "Red": 0}
    weights = {"cat1": 1.5, "cat4": 1.0, "cat7": 0.6, "cat9": 1.5}

    def add_vote(status, w):
        b = _vote_bucket(status)
        if not b:
            return
        votes[b] += w

    if s.get("mc") is not None:
        add_vote(s["mc"].get("status"), weights["cat1"])
    if s.get("cusum") is not None:
        add_vote(s["cusum"].get("status"), weights["cat1"])
    if s.get("doc") is not None:
        add_vote(s["doc"].get("status"), weights["cat4"])
    for m in sim:
        add_vote(m.get("status_color"), weights["cat7"])
    if s.get("decision") is not None:
        add_vote(s["decision"].get("state"), weights["cat9"])

    total = sum(votes[k] for k in votes)  # insertion order; do not sort
    if total == 0:
        return insufficient("Weighted_Voting")
    dominant = "Green"
    for b in list(votes)[1:]:  # JS reduce with `>` keeps the LATER key on ties
        dominant = dominant if votes[dominant] > votes[b] else b
    pct = int(js_round((votes[dominant] / total) * 100))
    return {
        "method_class": "Weighted_Voting",
        "status_color": dominant,
        "votes": votes,
        "dominant_pct": pct,
        "evidence_metric": f"Weighted vote: {dominant} ({pct}% of weighted signals)",
    }


def run_majority_rules(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    project = si or {}
    s = project.get("signals") or {}
    sim = (project.get("simulationSignals") or {}).get("signal_array") or []
    counts = {"Green": 0, "Yellow": 0, "Amber": 0, "Red": 0}

    def count(status):
        b = _vote_bucket(status)
        if not b:
            return
        counts[b] += 1

    if s.get("mc") is not None:
        count(s["mc"].get("status"))
    if s.get("cusum") is not None:
        count(s["cusum"].get("status"))
    if s.get("doc") is not None:
        count(s["doc"].get("status"))
    for m in sim:
        count(m.get("status_color"))

    total = sum(counts[k] for k in counts)
    if total == 0:
        return insufficient("Majority_Rules")
    majority = "Green"
    for b in list(counts)[1:]:
        majority = majority if counts[majority] > counts[b] else b
    pct = int(js_round((counts[majority] / total) * 100))
    return {
        "method_class": "Majority_Rules",
        "status_color": majority,
        "counts": counts,
        "majority_pct": pct,
        "total_votes": total,
        "evidence_metric": (
            f"{majority} by majority ({counts[majority]} of {total} modules, {pct}%)"
        ),
    }


def run_worst_n_of_m(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    project = si or {}
    s = project.get("signals") or {}
    sim = (project.get("simulationSignals") or {}).get("signal_array") or []
    all_statuses: list = []
    if s.get("mc") is not None:
        all_statuses.append(s["mc"].get("status"))
    if s.get("cusum") is not None:
        all_statuses.append(s["cusum"].get("status"))
    if s.get("doc") is not None:
        all_statuses.append(s["doc"].get("status"))
    for m in sim:
        if m.get("status_color"):
            all_statuses.append(m["status_color"])
    # Defect 1 again, third of the three ensembles. `"Red" in st` and `st == "Amber"` are the
    # same capitalised comparisons _vote_bucket carried, applied directly here: the lowercase
    # primary signals counted as neither red nor amber and simply vanished from both tallies
    # while still inflating the denominator. Every status is banded first, and one outside the
    # vocabulary is dropped from the denominator too rather than diluting the red fraction.
    bands = [b for b in (normalise_status(st) for st in all_statuses) if b]
    if not bands:
        return insufficient("Worst_N_of_M")
    red_count = sum(1 for b in bands if b == "Red")
    amber_count = sum(1 for b in bands if b == "Amber")
    m_total = len(bands)
    if red_count >= math.ceil(m_total * 0.3):
        status = "Red"
    elif amber_count >= math.ceil(m_total * 0.4):
        status = "Amber"
    elif red_count >= 1:
        status = "Yellow"
    else:
        status = "Green"
    return {
        "method_class": "Worst_N_of_M",
        "status_color": status,
        "red_count": red_count,
        "amber_count": amber_count,
        "total_modules": m_total,
        "evidence_metric": f"{red_count} Red + {amber_count} Amber of {m_total} total modules",
    }


# ================================================================ B3 governance thresholds


def run_far_threshold(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("bac", "cpi", "ev", "ac")):
        return insufficient("FAR_Threshold")
    if si["cpi"] == 0 or si["bac"] == 0:
        return insufficient("FAR_Threshold")  # JS Infinity/NaN fallthrough; refused
    eac = si["bac"] / si["cpi"]
    overrun = ((eac - si["bac"]) / si["bac"]) * 100
    threshold = 25
    headroom = threshold - overrun
    color = ("Green" if overrun <= 5 else "Yellow" if overrun <= 15
             else "Amber" if overrun <= 25 else "Red")
    return {
        "method_class": "FAR_Threshold",
        "status_color": color,
        "overrun_pct": round1(overrun),
        "far34_threshold_pct": threshold,
        "distance_to_threshold": round1(headroom),
        "far_reporting_required": overrun >= threshold,
        "evidence_metric": (
            f"FAR Part 34: {_js_str(round1(overrun))}% overrun, threshold {threshold}% ("
            + ("REPORTING REQUIRED" if overrun >= threshold
               else f"{_js_str(round1(headroom))}% headroom") + ")"
        ),
    }


def run_omb_a11_check(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("bac", "cpi", "actualPctComplete")):
        return insufficient("OMB_A11_Check")
    if si["cpi"] == 0:
        return insufficient("OMB_A11_Check")  # JS Infinity; refused
    cpi_below = si["cpi"] < 0.90
    major = si["bac"] >= 10000000
    triggered = cpi_below and major
    eac = si["bac"] / si["cpi"]
    overrun = eac - si["bac"]
    color = ("Green" if not cpi_below else "Yellow" if si["cpi"] >= 0.92
             else "Amber" if si["cpi"] >= 0.88 else "Red")
    return {
        "method_class": "OMB_A11_Check",
        "status_color": color,
        "cpi_below_90": cpi_below,
        "major_program": major,
        "reporting_triggered": triggered,
        "projected_overrun": int(js_round(overrun)),
        "evidence_metric": (
            f"OMB A-11: CPI {_js_str(si['cpi'])}"
            + (": MANDATORY REPORTING TRIGGERED" if triggered
               else ": below threshold, monitor" if cpi_below else ": within threshold")
        ),
    }


def run_evm_reporting_threshold(si: dict, rand: Callable[[], float],
                                period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("bac", "cpi", "spi")):
        return insufficient("EVM_Reporting_Threshold")
    if si["cpi"] == 0 or si["bac"] == 0:
        return insufficient("EVM_Reporting_Threshold")  # JS Infinity/NaN; refused
    cpi_b = si["cpi"] < 0.90
    spi_b = si["spi"] < 0.90
    both = cpi_b and spi_b
    eac = si["bac"] / si["cpi"]
    delta = ((eac - si["bac"]) / si["bac"]) * 100
    if not cpi_b and not spi_b:
        color = "Green"
    elif cpi_b != spi_b:
        color = "Yellow"
    elif both and delta <= 15:
        color = "Amber"
    else:
        color = "Red"
    return {
        "method_class": "EVM_Reporting_Threshold",
        "status_color": color,
        "cpi_breached": cpi_b,
        "spi_breached": spi_b,
        "both_breached": both,
        "eac_delta_pct": round1(delta),
        "evidence_metric": (
            f"EVM threshold: CPI {'BREACHED' if cpi_b else 'ok'}, "
            f"SPI {'BREACHED' if spi_b else 'ok'}, EAC +{_js_str(round1(delta))}%"
        ),
    }


def run_contract_mod_frequency(si: dict, rand: Callable[[], float],
                               period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("changeOrderCount", "baselineContractSum", "revisedContractSum")):
        return insufficient("Contract_Mod_Frequency")
    growth = (((si["revisedContractSum"] - si["baselineContractSum"])
               / si["baselineContractSum"]) * 100 if si["baselineContractSum"] > 0 else 0)
    co = si["changeOrderCount"]
    if co >= 10 or growth >= 20:
        risk = "Red"
    elif co >= 6 or growth >= 10:
        risk = "Amber"
    elif co >= 3 or growth >= 5:
        risk = "Yellow"
    else:
        risk = "Green"
    is_derived = _derived(si, "changeOrderCount", "baselineContractSum")
    word = ("contracting officer review merits consideration" if risk == "Red"
            else "elevated modification frequency" if risk == "Amber"
            else "within normal range")
    return {
        "method_class": "Contract_Mod_Frequency",
        "status_color": risk,
        "co_count": co,
        "scope_growth_pct": round1(growth),
        "evidence_metric": (
            f"{_js_str(co)} contract modifications, {_js_str(round1(growth))}% scope growth, "
            + word
            + (" (estimated; upload Change Order log for precise figures)" if is_derived else "")
        ),
    }


# ================================================================ B4 decision optimization


def run_multi_objective(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("Multi_Objective_Optimization")
    norm_cpi = min(1, max(0, (si["cpi"] - 0.80) / 0.25))
    norm_spi = min(1, max(0, (si["spi"] - 0.80) / 0.25))
    norm_risk = 1 - (si.get("docRiskScore") or 0)
    pareto = round2((norm_cpi + norm_spi + norm_risk) / 3)
    objectives = sorted(
        [
            {"name": "Cost performance", "score": norm_cpi},
            {"name": "Schedule performance", "score": norm_spi},
            {"name": "Document risk", "score": norm_risk},
        ],
        key=lambda o: o["score"],
    )
    binding = objectives[0]
    color = ("Green" if pareto >= 0.75 else "Yellow" if pareto >= 0.55
             else "Amber" if pareto >= 0.35 else "Red")
    return {
        "method_class": "Multi_Objective_Optimization",
        "status_color": color,
        "pareto_score": pareto,
        "binding_constraint": binding["name"],
        "objectives": objectives,
        "evidence_metric": (
            f"Multi-objective score: {int(js_round(pareto * 100))}%, "
            f"binding constraint: {binding['name']} "
            f"(score {int(js_round(binding['score'] * 100))}%)"
        ),
    }


def run_linear_programming(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("bac", "ev", "ac", "cpi")):
        return insufficient("Linear_Programming")
    remaining_work = si["bac"] - si["ev"]
    remaining_budget = si["bac"] - si["ac"]
    if remaining_budget <= 0:
        return {
            "method_class": "Linear_Programming",
            "status_color": "Red",
            "feasible": False,
            "evidence_metric": "No feasible solution: budget exhausted before project completion",
        }
    required = remaining_work / remaining_budget
    feasible = required <= 1.20
    optimal = required <= 1.00
    lp_score = min(1, _jsdiv(1.0, required)) if feasible else 0
    color = ("Green" if optimal else "Yellow" if required <= 1.05
             else "Amber" if required <= 1.15 else "Red")
    word = ("achievable at current performance" if optimal
            else "requires productivity improvement" if feasible
            else "budget infeasible, recovery plan needed")
    return {
        "method_class": "Linear_Programming",
        "status_color": color,
        "required_cpi_to_complete": _round3(required),
        "feasible": feasible,
        "optimal": optimal,
        "lp_score": round2(lp_score),
        "evidence_metric": (
            f"LP: requires CPI {_js_str(_round3(required))} to complete within budget, {word}"
        ),
    }


def run_constraint_satisfaction(si: dict, rand: Callable[[], float],
                                period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "bac")):
        return insufficient("Constraint_Satisfaction")
    doc = si.get("docRiskScore") or 0
    constraints = [
        {"name": "Cost constraint (CPI ≥ 0.90)", "satisfied": si["cpi"] >= 0.90},
        {"name": "Schedule constraint (SPI ≥ 0.90)", "satisfied": si["spi"] >= 0.90},
        {"name": "Document risk (score < 0.70)", "satisfied": doc < 0.70},
        {"name": "FAR threshold (overrun < 25%)", "satisfied": si["cpi"] > 0.80},
    ]
    satisfied = sum(1 for c in constraints if c["satisfied"])
    violated = [c["name"] for c in constraints if not c["satisfied"]]
    rate = satisfied / len(constraints)
    color = ("Green" if rate >= 1.0 else "Yellow" if rate >= 0.75
             else "Amber" if rate >= 0.50 else "Red")
    return {
        "method_class": "Constraint_Satisfaction",
        "status_color": color,
        "satisfied": satisfied,
        "total": len(constraints),
        "violated_constraints": violated,
        "satisfaction_rate": int(js_round(rate * 100)),
        "evidence_metric": (
            f"{satisfied} of {len(constraints)} constraints satisfied"
            + (f"; violated: {', '.join(violated)}" if violated else "; all constraints met")
        ),
    }


def run_whatif_matrix(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    THE FIFTEEN DEFECTS, defect 13, applied to the second of the two computations it can name.

    The defect list identifies this one by code and by the name of its sibling, so both were
    read and both carried the same unguarded earned value domains: a guard at exactly zero, and
    nothing at all for a negative index, a negative budget, or earned value exceeding the budget
    at completion. The guards below are the same as the sibling's and refuse for the same
    reasons. Which of the two the audit meant does not change what either needed.
    """
    if not check_inputs(si, ("bac", "ev", "ac", "cpi", "spi")):
        return insufficient("WhatIf_Scenario_Matrix")
    if si["cpi"] <= 0 or si["spi"] <= 0:
        return insufficient(
            "WhatIf_Scenario_Matrix",
            "Cost or schedule performance is recorded as zero or below, which no remaining "
            "work can be divided by")
    if si["bac"] <= 0:
        return insufficient(
            "WhatIf_Scenario_Matrix",
            "No positive budget at completion is recorded to scale the scenarios against")
    if si["ev"] < 0 or si["ac"] < 0:
        return insufficient(
            "WhatIf_Scenario_Matrix",
            "Negative earned value or actual cost is not a measurable position to forecast from")
    if si["ev"] > si["bac"]:
        return insufficient(
            "WhatIf_Scenario_Matrix",
            "More value is recorded as earned than the budget at completion contains, so there "
            "is no remaining work to forecast")
    remaining = si["bac"] - si["ev"]
    scenarios = [
        {"name": "Optimistic (CPI recovers to 1.0)", "eac": si["ac"] + remaining * 1.00},
        {"name": "Base (current CPI continues)", "eac": si["bac"] / si["cpi"]},
        {"name": "Pessimistic (CPI degrades 5%)", "eac": si["bac"] / (si["cpi"] * 0.95)},
        {"name": "Recovery (CPI improves 5%)", "eac": si["bac"] / (si["cpi"] * 1.05)},
    ]
    base_eac = scenarios[1]["eac"]
    range_pct = int(js_round(((scenarios[2]["eac"] - scenarios[0]["eac"]) / si["bac"]) * 100))
    color = ("Green" if range_pct <= 5 else "Yellow" if range_pct <= 10
             else "Amber" if range_pct <= 20 else "Red")
    return {
        "method_class": "WhatIf_Scenario_Matrix",
        "status_color": color,
        "scenarios": [
            {"name": s["name"], "eac": int(js_round(s["eac"])),
             "delta_pct": round1(((s["eac"] - si["bac"]) / si["bac"]) * 100)}
            for s in scenarios
        ],
        "scenario_range_pct": range_pct,
        "base_eac": int(js_round(base_eac)),
        "evidence_metric": (
            f"Scenario range: {range_pct}% of BAC, "
            f"base EAC ${int(js_round(base_eac / 1000))}k, "
            f"worst ${int(js_round(scenarios[2]['eac'] / 1000))}k, "
            f"best ${int(js_round(scenarios[0]['eac'] / 1000))}k"
        ),
    }


def run_decision_sensitivity(si: dict, rand: Callable[[], float],
                             period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("Decision_Sensitivity_Matrix")
    cpi_i = abs(1 - si["cpi"]) * 100
    spi_i = abs(1 - si["spi"]) * 100
    risk_i = (si.get("docRiskScore") or 0) * 50
    total = (cpi_i + spi_i + risk_i) or 1
    sensitivity = sorted(
        [
            {"driver": "Cost performance (CPI)", "impact": cpi_i,
             "pct": int(js_round(cpi_i / total * 100))},
            {"driver": "Schedule performance (SPI)", "impact": spi_i,
             "pct": int(js_round(spi_i / total * 100))},
            {"driver": "Document risk", "impact": risk_i,
             "pct": int(js_round(risk_i / total * 100))},
        ],
        key=lambda d: -d["impact"],
    )
    top = sensitivity[0]
    mx = top["impact"]
    color = ("Green" if mx <= 3 else "Yellow" if mx <= 7 else "Amber" if mx <= 12 else "Red")
    return {
        "method_class": "Decision_Sensitivity_Matrix",
        "status_color": color,
        "top_driver": top["driver"],
        "top_driver_pct": top["pct"],
        "sensitivity_matrix": sensitivity,
        "evidence_metric": (
            f"Decision most sensitive to: {top['driver']} ({top['pct']}% of decision weight); "
            f"a small change here most changes the governance recommendation"
        ),
    }


def run_pareto_frontier(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("Pareto_Frontier")
    doc = si.get("docRiskScore") or 0
    cost_ok = si["cpi"] >= 0.95
    sched_ok = si["spi"] >= 0.95
    risk_ok = doc < 0.30
    dominated = not cost_ok and not sched_ok
    efficient = cost_ok and sched_ok and risk_ok
    tradeoff = (cost_ok != sched_ok) or (not risk_ok and (cost_ok or sched_ok))
    score = ((1 if cost_ok else si["cpi"] / 0.95)
             + (1 if sched_ok else si["spi"] / 0.95)
             + (1 if risk_ok else (1 - doc / 0.30))) / 3
    score = round2(min(1, score))
    color = ("Green" if efficient else "Yellow" if tradeoff
             else "Amber" if not dominated else "Red")
    evidence = ("Project is Pareto-efficient: all objectives met simultaneously" if efficient
                else "Project is Pareto-dominated: multiple objectives failing simultaneously"
                if dominated
                else "Trade-off required: improving one objective may affect another" if tradeoff
                else "Partial Pareto efficiency: some objectives met")
    return {
        "method_class": "Pareto_Frontier",
        "status_color": color,
        "pareto_efficient": efficient,
        "dominated": dominated,
        "tradeoff_required": tradeoff,
        "pareto_score": score,
        "evidence_metric": evidence,
    }


def run_regret_minimization(si: dict, rand: Callable[[], float],
                            period_cutoff) -> dict[str, Any]:
    """
    RUN 7, AND THIS ONE ABSTAINS UNCONDITIONALLY.

    Minimax regret is defined by an action-by-scenario payoff matrix: what each course of action
    costs under each future state, for the decision actually in front of the reader. This
    platform holds no such matrix. The one below was nine literals and three literal state
    probabilities, so the three expected regrets were 11, 5 and 8 on every project and in every
    period, the minimum was always to investigate, and the two overrides could only move that to
    escalate. The known-answer run exhausted 3,721 cost and schedule index pairs from 0.70 to
    1.30 and found no pair that produced a healthy reading: a project twenty per cent ahead on
    both indices was still told to investigate, because the only branch that reads healthy was
    unreachable from any input.

    The corpus was searched for a governed payoff matrix before this was written, and there is
    none: no action-by-scenario structure exists anywhere in the repository outside these
    literals. Substituting different literals would repeat the fault at a different set of
    numbers, and building a real minimax-regret engine needs owner approval and a matrix that
    does not exist. So the module refuses and states which structure is missing.

    What this does NOT do is decide anything for a participant. The courses of action a
    participant chooses among were already outside this module's reach: a non-voting module is
    excluded from the recommendation text and the courses of action by the owner's settled
    decision, which this module has been subject to since Run 1, and it stays non-voting here.
    No new decision policy is introduced by this run.
    """
    return insufficient(
        "Regret_Minimization",
        "Insufficient data: no set of courses of action scored against defined future states is "
        "held for this project, so there is no worst case per course to compare and no course "
        "can be identified as carrying the smallest one. No ranking is offered in its place.",
        ABSTAIN_DECISION_STRUCTURE_ABSENT)


GOV_BATCH_A: dict[str, tuple[str, Callable]] = {
    "B2.1": ("DST_Evidence_Combination", run_dst),
    "B1.2": ("Weighted_Voting", run_weighted_voting),
    "B1.3": ("Majority_Rules", run_majority_rules),
    "B1.4": ("Worst_N_of_M", run_worst_n_of_m),
    "B3.2": ("FAR_Threshold", run_far_threshold),
    "B3.3": ("OMB_A11_Check", run_omb_a11_check),
    "B3.4": ("EVM_Reporting_Threshold", run_evm_reporting_threshold),
    "B3.5": ("Contract_Mod_Frequency", run_contract_mod_frequency),
}

GOV_BATCH_B: dict[str, tuple[str, Callable]] = {
    "B4.1": ("Multi_Objective_Optimization", run_multi_objective),
    "B4.2": ("Linear_Programming", run_linear_programming),
    "B4.3": ("Constraint_Satisfaction", run_constraint_satisfaction),
    "B4.4": ("WhatIf_Scenario_Matrix", run_whatif_matrix),
    "B4.5": ("Decision_Sensitivity_Matrix", run_decision_sensitivity),
    "B4.6": ("Pareto_Frontier", run_pareto_frontier),
    "B4.7": ("Regret_Minimization", run_regret_minimization),
}
