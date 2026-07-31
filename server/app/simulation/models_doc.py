"""
A4/A5/A6 extension models: document-derived signals, system dynamics, delivery quality.

Ported from assets/js/simulations.js (Cat 4 doc/risk extensions, Cat 5 system dynamics,
the derived-field modules and the dormant-module section), validated numerically against the
JavaScript executed in a browser. See VALIDATION.md for the per-module comparison.

All twenty are deterministic; `rand` is accepted only for the registry's one call signature.

Porting hazards specific to this file:

- Truthiness contributions: Dispute Escalation and Rework Feedback weight `si.rfiCount ? ... : 0`
  — an rfiCount of 0 contributes nothing via JS falsiness, reproduced with explicit checks.
- Weather Day Impact is Green iff `weatherDaysLost === 0` exactly; the ratio ladder starts at
  Yellow. `(si.consumedFloat || 0)` is JS truthiness again.
- Subcontractor Performance in the browser can lazily derive `subcontractorComplianceScore`
  via `window.LinSignals.deriveExtendedFields`. That safety net is NOT ported: on the server the
  extraction pipeline supplies the score or the module abstains. The browser comparison ran
  without signals.js loaded, so the two sides were validated on identical semantics.
- Scenario Modeling divides by `min(cpi, spi)` and Sensitivity Analysis by `cpi ± 0.05`; at the
  zero points JavaScript's Infinity falls through onto a conjured status. The port abstains at
  exactly those values — the standing refusing-direction rule.
"""

from __future__ import annotations

import math
from typing import Any, Callable

from .models import check_inputs, insufficient
from .models_ext import _derived, _js_str
from .rng import js_round, num, round1, round2

_RANK = {"Green": 0, "Yellow": 1, "Amber": 2, "Red": 3}


# ------------------------------------------------------------ A4.2 RFI Velocity


def run_rfi_velocity(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    count = si.get("rfiCount") if si.get("rfiCount") is not None else si.get("rfiNumber")
    days = si.get("rfiPeriodDays") if si.get("rfiPeriodDays") is not None else 30
    if count is None:
        return insufficient("RFI_Velocity")
    is_derived = _derived(si, "rfiPeriodDays")
    per30 = js_round((count / days) * 300) / 10 if days > 0 else 0
    per_week = js_round((count / days) * 70) / 10 if days > 0 else 0
    vel_status = ("Green" if per_week <= 2 else "Yellow" if per_week <= 4
                  else "Amber" if per_week <= 8 else "Red")
    overdue_ratio = None
    overdue_status = None
    if si.get("rfiOverdue") is not None and count > 0:
        overdue_ratio = si["rfiOverdue"] / count
        overdue_status = ("Green" if overdue_ratio < 0.10 else "Yellow" if overdue_ratio < 0.20
                          else "Amber" if overdue_ratio < 0.35 else "Red")
    # Worst of the velocity band and the overdue band.
    status = (overdue_status if overdue_status and _RANK[overdue_status] > _RANK[vel_status]
              else vel_status)
    avg_response = (si.get("rfiAvgResponseDays") if si.get("rfiAvgResponseDays") is not None
                    else si.get("rfiResponseTimeDays"))
    evidence = (f"{_js_str(count)} RFIs over {_js_str(days)} days "
                f"({_js_str(per30)}/30d, {_js_str(per_week)}/week)")
    if overdue_ratio is not None:
        evidence += (f", {_js_str(si['rfiOverdue'])} overdue "
                     f"({int(js_round(overdue_ratio * 100))}%)")
    if avg_response is not None:
        evidence += f", avg response {_js_str(avg_response)} days"
        if avg_response > 14:
            evidence += " (slow response indicates dispute risk)"
    if si.get("rfiOldestOpenDays") is not None:
        evidence += f", oldest open {_js_str(si['rfiOldestOpenDays'])} days"
    if is_derived:
        evidence += " (assumed 30-day period; upload RFI log for precise velocity)"
    return {
        "method_class": "RFI_Velocity",
        "status_color": status,
        "rfi_per_30d": per30,
        "rfi_per_week": per_week,
        "total_rfis": count,
        "period_days": days,
        "open_rfis": si.get("rfiOpen") if si.get("rfiOpen") is not None else None,
        "overdue_rfis": si.get("rfiOverdue") if si.get("rfiOverdue") is not None else None,
        "overdue_ratio": (js_round(overdue_ratio * 1000) / 1000
                          if overdue_ratio is not None else None),
        "response_time_days": avg_response if avg_response is not None else None,
        "evidence_metric": evidence,
    }


# ------------------------------------------------------------ A4.3 Submittal Rejection Rate


def run_submittal_rejection(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    use_rfa = (si.get("rfaTotal") is not None and si.get("rfaRejected") is not None
               and si["rfaTotal"] > 0)
    total = si.get("rfaTotal") if use_rfa else si.get("submittalsTotal")
    rejected = si.get("rfaRejected") if use_rfa else si.get("submittalsRejected")
    if total is None or rejected is None:
        return insufficient("Submittal_Rejection")
    if not total > 0:
        return insufficient("Submittal_Rejection")
    rate = js_round((rejected / total) * 1000) / 1000
    color = ("Green" if rate <= 0.05 else "Yellow" if rate <= 0.15
             else "Amber" if rate <= 0.25 else "Red")
    is_derived = not use_rfa and _derived(si, "submittalsTotal")
    evidence = (f"{_js_str(rejected)} of {_js_str(total)} "
                + ("RFAs rejected (" if use_rfa else "submittals rejected (")
                + f"{int(js_round(rate * 100))}%)")
    if use_rfa:
        if si.get("rfaResubmit") is not None:
            evidence += f", {_js_str(si['rfaResubmit'])} revise-and-resubmit"
        if si.get("rfaOpen") is not None:
            evidence += f", {_js_str(si['rfaOpen'])} open"
        if si.get("rfaAvgReviewDays") is not None:
            evidence += f", avg review {_js_str(si['rfaAvgReviewDays'])} days"
    if is_derived:
        evidence += " (estimated from doc risk; upload Submittal Register for precise figures)"
    return {
        "method_class": "Submittal_Rejection",
        "status_color": color,
        "rejection_rate": rate,
        "rejected": rejected,
        "total": total,
        "source": "rfa_log" if use_rfa else "submittals",
        "evidence_metric": evidence,
    }


# ------------------------------------------------------------ A4.4 NCR Rate


def run_ncr_rate(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("ncrIssued", "ncrClosed", "ncrOpen")):
        return insufficient("NCR_Rate")
    issued = num(si.get("ncrIssued"), 0)
    open_ = num(si.get("ncrOpen"), 0)
    if issued == 0:
        return {
            "method_class": "NCR_Rate",
            "status_color": "Green",
            "open_ratio": 0,
            "evidence_metric": "No NCRs issued this period",
        }
    open_ratio = open_ / max(issued, 1)
    color = ("Green" if open_ratio < 0.15 else "Yellow" if open_ratio < 0.30
             else "Amber" if open_ratio < 0.50 else "Red")
    return {
        "method_class": "NCR_Rate",
        "status_color": color,
        "open_ratio": round2(open_ratio),
        "evidence_metric": (
            f"{_js_str(open_)} open of {_js_str(issued)} NCRs issued "
            f"(open ratio {_js_str(round2(open_ratio))})"
        ),
    }


# ------------------------------------------------------------ A4.5 Weather Day Impact


def run_weather_impact(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("weatherDaysLost",)):
        return insufficient("Weather_Impact")
    is_derived = _derived(si, "weatherDaysLost")
    lost = si["weatherDaysLost"]
    if si.get("floatRemaining") is not None:
        flt = si["floatRemaining"]
    elif si.get("totalFloat") is not None:
        flt = si["totalFloat"] - (si.get("consumedFloat") or 0)
    else:
        flt = None
    if flt is not None and flt > 0:
        ratio = lost / flt
    else:
        ratio = 1.0 if lost > 0 else 0
    color = ("Green" if lost == 0 else "Yellow" if ratio <= 0.20
             else "Amber" if ratio <= 0.50 else "Red")
    evidence = f"{_js_str(lost)} weather days lost"
    if flt is not None:
        evidence += f", {int(js_round(ratio * 100))}% of available float consumed"
    if is_derived:
        evidence += " (estimated; upload Field Report for precise figures)"
    return {
        "method_class": "Weather_Impact",
        "status_color": color,
        "weather_days_lost": lost,
        "float_remaining": flt,
        "weather_ratio": int(js_round(ratio * 100)),
        "evidence_metric": evidence,
    }


# ------------------------------------------------------------ A4.6 Change Order Frequency


def run_co_frequency(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("changeOrderCount", "baselineContractSum", "revisedContractSum")):
        return insufficient("CO_Frequency")
    growth = (((si["revisedContractSum"] - si["baselineContractSum"])
               / si["baselineContractSum"]) * 100 if si["baselineContractSum"] > 0 else 0)
    co_rate = si["changeOrderCount"]
    if growth <= 5 and co_rate <= 3:
        color = "Green"
    elif growth <= 10 and co_rate <= 6:
        color = "Yellow"
    elif growth <= 20 and co_rate <= 10:
        color = "Amber"
    else:
        color = "Red"
    is_derived = _derived(si, "changeOrderCount", "baselineContractSum")
    return {
        "method_class": "CO_Frequency",
        "status_color": color,
        "co_count": co_rate,
        "scope_growth_pct": round1(growth),
        "evidence_metric": (
            f"{_js_str(co_rate)} change orders, scope growth: +{_js_str(round1(growth))}%"
            + (" (estimated; upload Change Order log for precise figures)" if is_derived else "")
        ),
    }


# ------------------------------------------------------------ A4.7 Dispute Escalation Index


def run_dispute_escalation(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("docRiskScore",)):
        return insufficient("Dispute_Escalation")
    rfi_w = min(si["rfiCount"] / 20, 1) * 0.3 if si.get("rfiCount") else 0
    co_w = min(si["changeOrderCount"] / 10, 1) * 0.3 if si.get("changeOrderCount") else 0
    doc_w = si["docRiskScore"] * 0.4
    index = round2(rfi_w + co_w + doc_w)
    color = ("Green" if index <= 0.20 else "Yellow" if index <= 0.40
             else "Amber" if index <= 0.65 else "Red")
    return {
        "method_class": "Dispute_Escalation",
        "status_color": color,
        "escalation_index": index,
        "evidence_metric": (
            f"Dispute escalation index: {_js_str(index)} "
            f"(doc risk + RFI velocity + CO frequency combined)"
        ),
    }


# ------------------------------------------------------------ A4.8 Subcontractor Performance


def run_subcontractor_performance(si: dict, rand: Callable[[], float],
                                  period_cutoff) -> dict[str, Any]:
    if (si.get("subcontractorComplianceScore") is None
            and si.get("subcontractorIssuesDiscussed") is None
            and si.get("docRiskScore") is None):
        return insufficient("Subcontractor_Performance")
    # The browser's deriveExtendedFields safety net is not ported; the extraction pipeline
    # supplies the score or this module abstains. See the module docstring.
    score = si.get("subcontractorComplianceScore")
    if score is None:
        return insufficient("Subcontractor_Performance")
    is_derived = _derived(si, "subcontractorComplianceScore")
    score_pct = int(js_round(score * 100))
    color = ("Green" if score_pct >= 85 else "Yellow" if score_pct >= 70
             else "Amber" if score_pct >= 55 else "Red")
    signals = []
    if (si.get("subcontractorIssuesDiscussed") or 0) > 0:
        signals.append(f"{_js_str(si['subcontractorIssuesDiscussed'])} issues in OAC minutes")
    if (si.get("outstandingActionItems") or 0) > 0:
        signals.append(f"{_js_str(si['outstandingActionItems'])} outstanding action items")
    if (si.get("ncrOpen") or 0) > 0:
        signals.append(f"{_js_str(si['ncrOpen'])} open NCRs")
    if (si.get("docRiskScore") or 0) > 0.30:
        signals.append(f"elevated document risk ({int(js_round(si['docRiskScore'] * 100))}%)")
    return {
        "method_class": "Subcontractor_Performance",
        "status_color": color,
        "compliance_score": score_pct,
        "signals_contributing": signals,
        "evidence_metric": (
            f"Subcontractor compliance: {score_pct}%"
            + (f" ({', '.join(signals)})" if signals else "")
            + (", derived from meeting records and correspondence" if is_derived
               else ", from subcontractor performance report")
        ),
    }


# ------------------------------------------------------------ A4.9 Procurement Lead Time


def run_procurement_lead_time(si: dict, rand: Callable[[], float],
                              period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("longLeadItemsTotal", "longLeadAtRisk", "longLeadDelayed")):
        return insufficient("Procurement_Lead_Time")
    total = num(si.get("longLeadItemsTotal"), 0)
    at_risk = num(si.get("longLeadAtRisk"), 0)
    delayed = num(si.get("longLeadDelayed"), 0)
    risk_ratio = (at_risk + 2 * delayed) / max(total, 1)
    color = ("Green" if risk_ratio < 0.15 else "Yellow" if risk_ratio < 0.30
             else "Amber" if risk_ratio < 0.50 else "Red")
    return {
        "method_class": "Procurement_Lead_Time",
        "status_color": color,
        "risk_ratio": round2(risk_ratio),
        "evidence_metric": (
            f"{_js_str(at_risk)} at-risk + {_js_str(delayed)} delayed of {_js_str(total)} "
            f"long-lead items (weighted disruption {_js_str(round2(risk_ratio))})"
        ),
    }


# ------------------------------------------------------------ A4.10 Spec Conflict Density


def run_spec_conflict_density(si: dict, rand: Callable[[], float],
                              period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("docRiskScore", "rfiCount")):
        return insufficient("Spec_Conflict_Density")
    if si["rfiCount"] > 0:
        density = (si["docRiskScore"] * si["rfiCount"]) / math.sqrt(si["rfiCount"])
    else:
        density = si["docRiskScore"]
    density = min(1, round2(density))
    color = ("Green" if density <= 0.15 else "Yellow" if density <= 0.35
             else "Amber" if density <= 0.60 else "Red")
    return {
        "method_class": "Spec_Conflict_Density",
        "status_color": color,
        "conflict_density": density,
        "evidence_metric": (
            f"Spec conflict density: {_js_str(density)} (doc risk weighted by RFI volume)"
        ),
    }


# ------------------------------------------------------------ A5.2 Sensitivity Analysis


def run_sensitivity_analysis(si: dict, rand: Callable[[], float],
                             period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("bac", "ev", "ac", "pv", "cpi", "spi")):
        return insufficient("Sensitivity_Analysis")
    cpi = si["cpi"]
    if cpi == 0 or cpi == 0.05 or cpi == -0.05:
        # JS: division by zero at these exact values → Infinity/NaN fallthrough. Refused.
        return insufficient("Sensitivity_Analysis")
    eac_base = si["bac"] / cpi
    if eac_base == 0:
        return insufficient("Sensitivity_Analysis")  # bac=0: JS NaN fallthrough, refused
    cpi_sens = abs(si["bac"] / (cpi - 0.05) - si["bac"] / (cpi + 0.05)) / eac_base
    spi_sens = abs(si["spi"] - 1.0) * 0.5
    doc_sens = si.get("docRiskScore") or 0
    drivers = sorted(
        [
            {"name": "CPI", "sensitivity": cpi_sens},
            {"name": "SPI", "sensitivity": spi_sens},
            {"name": "DocRisk", "sensitivity": doc_sens},
        ],
        key=lambda d: -d["sensitivity"],
    )
    top = drivers[0]
    mx = top["sensitivity"]
    color = ("Green" if mx <= 0.10 else "Yellow" if mx <= 0.20
             else "Amber" if mx <= 0.35 else "Red")
    return {
        "method_class": "Sensitivity_Analysis",
        "status_color": color,
        "top_driver": top["name"],
        "top_sensitivity": int(js_round(mx * 100)),
        "drivers": drivers,
        "evidence_metric": (
            f"Top risk driver: {top['name']} (sensitivity: {int(js_round(mx * 100))}%)"
        ),
    }


# ------------------------------------------------------------ A5.3 Tornado Risk Ranking


def run_tornado_diagram(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore",
                             "actualPctComplete", "plannedPctComplete")):
        return insufficient("Tornado_Diagram")
    risks = sorted(
        [
            {"name": "Cost Performance", "impact": abs(1 - si["cpi"]) * 100},
            {"name": "Schedule Performance", "impact": abs(1 - si["spi"]) * 100},
            {"name": "Document Risk", "impact": si["docRiskScore"] * 100},
            {"name": "Progress Variance",
             "impact": abs(si["actualPctComplete"] - si["plannedPctComplete"])},
        ],
        key=lambda r: -r["impact"],
    )
    top = risks[0]
    composite = sum(r["impact"] for r in risks) / len(risks)
    color = ("Green" if composite <= 5 else "Yellow" if composite <= 10
             else "Amber" if composite <= 20 else "Red")
    return {
        "method_class": "Tornado_Diagram",
        "status_color": color,
        "top_risk": top["name"],
        "top_impact": round1(top["impact"]),
        "composite_score": round1(composite),
        "risks": risks,
        "evidence_metric": (
            f"Top risk: {top['name']} ({_js_str(round1(top['impact']))}% impact)"
        ),
    }


# ------------------------------------------------------------ A5.4 Scenario Modeling


def run_scenario_modeling(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("bac", "ev", "ac", "cpi", "spi")):
        return insufficient("Scenario_Modeling")
    if si["cpi"] == 0 or min(si["cpi"], si["spi"]) == 0 or si["bac"] == 0:
        # JS: Infinity/NaN fallthrough onto a conjured status. Refused; see VALIDATION.md.
        return insufficient("Scenario_Modeling")
    remaining = si["bac"] - si["ev"]
    optimistic = si["ac"] + remaining * 1.00
    realistic = si["ac"] + remaining / si["cpi"]
    pessimistic = si["ac"] + remaining / min(si["cpi"], si["spi"])
    scenario_range = (pessimistic - optimistic) / si["bac"] * 100
    color = ("Green" if pessimistic <= si["bac"] * 1.05
             else "Yellow" if pessimistic <= si["bac"] * 1.10
             else "Amber" if pessimistic <= si["bac"] * 1.20 else "Red")
    return {
        "method_class": "Scenario_Modeling",
        "status_color": color,
        "optimistic_eac": int(js_round(optimistic)),
        "realistic_eac": int(js_round(realistic)),
        "pessimistic_eac": int(js_round(pessimistic)),
        "scenario_range_pct": round1(scenario_range),
        "evidence_metric": (
            f"Scenarios: best ${int(js_round(optimistic / 1000))}k / "
            f"likely ${int(js_round(realistic / 1000))}k / "
            f"worst ${int(js_round(pessimistic / 1000))}k"
        ),
    }


# ------------------------------------------------------------ A5.5 Rework Feedback Loop


def run_rework_feedback(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi",)):
        return insufficient("Rework_Feedback")
    rfi_c = min(si["rfiCount"] / 30, 1) * 0.3 if si.get("rfiCount") else 0
    co_c = min(si["changeOrderCount"] / 15, 1) * 0.3 if si.get("changeOrderCount") else 0
    cpi_c = max(0, 1 - si["cpi"]) * 0.4
    index = round2(rfi_c + co_c + cpi_c)
    color = ("Green" if index <= 0.10 else "Yellow" if index <= 0.25
             else "Amber" if index <= 0.45 else "Red")
    return {
        "method_class": "Rework_Feedback",
        "status_color": color,
        "rework_index": index,
        "evidence_metric": (
            f"Rework feedback index: {_js_str(index)} (CPI degradation + RFI + CO combined)"
        ),
    }


# ------------------------------------------------------------ A5.6 Queueing Theory Bottleneck


def run_queueing_bottleneck(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("activitiesPlanned", "activitiesConstrained")):
        return insufficient("Queueing_Bottleneck")
    planned = num(si.get("activitiesPlanned"), 0)
    constrained = num(si.get("activitiesConstrained"), 0)
    ratio = constrained / max(planned, 1)
    color = ("Green" if ratio < 0.15 else "Yellow" if ratio < 0.25
             else "Amber" if ratio < 0.40 else "Red")
    return {
        "method_class": "Queueing_Bottleneck",
        "status_color": color,
        "constraint_ratio": round2(ratio),
        "evidence_metric": (
            f"{_js_str(constrained)} of {_js_str(planned)} planned activities constrained "
            f"(queue ratio {_js_str(round2(ratio))})"
        ),
    }


# ------------------------------------------------------------ A5.7 Agent-Based Supply Chain


def run_agent_supply_chain(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("longLeadItemsTotal", "longLeadAtRisk")):
        return insufficient("Agent_Supply_Chain")
    total = num(si.get("longLeadItemsTotal"), 0)
    at_risk = num(si.get("longLeadAtRisk"), 0)
    ratio = at_risk / max(total, 1)
    color = ("Green" if ratio < 0.10 else "Yellow" if ratio < 0.20
             else "Amber" if ratio < 0.35 else "Red")
    return {
        "method_class": "Agent_Supply_Chain",
        "status_color": color,
        "at_risk_ratio": round2(ratio),
        "evidence_metric": (
            f"{_js_str(at_risk)} of {_js_str(total)} long-lead items at risk "
            f"(at-risk share {_js_str(round2(ratio))})"
        ),
    }


# ------------------------------------------------------------ A5.8 Discrete Event Simulation


def run_discrete_event_sim(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("spi", "actualPctComplete", "plannedPctComplete", "cpi")):
        return insufficient("Discrete_Event_Sim")
    progress_ratio = (si["actualPctComplete"] / si["plannedPctComplete"]
                      if si["plannedPctComplete"] > 0 else 1)
    interruption = max(0, 1 - progress_ratio) + max(0, 1 - si["spi"]) * 0.5
    throughput = js_round((1 / (1 + interruption)) * 1000) / 1000
    color = ("Green" if throughput >= 0.92 else "Yellow" if throughput >= 0.85
             else "Amber" if throughput >= 0.75 else "Red")
    return {
        "method_class": "Discrete_Event_Sim",
        "status_color": color,
        "throughput_index": throughput,
        "interruption_rate": int(js_round(interruption * 100)),
        "evidence_metric": (
            f"DES throughput: {_js_str(throughput)} "
            f"({int(js_round(interruption * 100))}% interruption rate)"
        ),
    }


# ------------------------------------------------------------ A6.1 Quality Compliance Index


def run_quality_compliance(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("qualityDeficienciesNoted",)):
        return insufficient("Quality_Compliance")
    is_derived = _derived(si, "qualityDeficienciesNoted")
    inspected = si.get("itemsInspected") if si.get("itemsInspected") is not None else 20
    failed = (si.get("itemsFailed") if si.get("itemsFailed") is not None
              else si["qualityDeficienciesNoted"])
    pass_rate = (inspected - failed) / inspected if inspected > 0 else 1
    audit = (si.get("qualityAuditScore") if si.get("qualityAuditScore") is not None
             else pass_rate * 100)
    color = ("Green" if audit >= 85 else "Yellow" if audit >= 70
             else "Amber" if audit >= 55 else "Red")
    return {
        "method_class": "Quality_Compliance",
        "status_color": color,
        "quality_score": int(js_round(audit)),
        "pass_rate": int(js_round(pass_rate * 100)),
        "deficiencies": si["qualityDeficienciesNoted"],
        "evidence_metric": (
            f"Quality compliance: {int(js_round(audit))}/100, "
            f"{_js_str(si['qualityDeficienciesNoted'])} deficiencies noted"
            + (" (estimated from field observations; upload Quality Audit for precise score)"
               if is_derived else "")
        ),
    }


# ------------------------------------------------------------ A6.2 Safety Performance Index


def run_safety_performance(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("safetyIncidentsDiscussed",)):
        return insufficient("Safety_Performance")
    is_derived = _derived(si, "safetyIncidentsDiscussed")
    rate = (si.get("oshaIncidentRate") if si.get("oshaIncidentRate") is not None
            else si["safetyIncidentsDiscussed"] * 10)
    benchmark = 3.0
    index = benchmark / rate if rate > 0 else 1
    index = min(2, round2(index))
    color = ("Green" if rate <= benchmark else "Yellow" if rate <= benchmark * 2
             else "Amber" if rate <= benchmark * 5 else "Red")
    evidence = f"Safety: {_js_str(si['safetyIncidentsDiscussed'])} incidents in OAC records"
    if si.get("oshaIncidentRate") is not None:
        evidence += f", OSHA rate {_js_str(round1(si['oshaIncidentRate']))}"
    if is_derived:
        evidence += " (estimated from meeting records; upload Safety Report for OSHA rate)"
    return {
        "method_class": "Safety_Performance",
        "status_color": color,
        "incident_rate": round1(rate),
        "industry_benchmark": benchmark,
        "safety_index": index,
        "incidents_discussed": si["safetyIncidentsDiscussed"],
        "evidence_metric": evidence,
    }


# ------------------------------------------------------------ A6.3 Environmental Compliance


def run_environmental_compliance(si: dict, rand: Callable[[], float],
                                 period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("environmentalIssuesDiscussed",)):
        return insufficient("Environmental_Compliance")
    is_derived = _derived(si, "environmentalIssuesDiscussed")
    rate = (si.get("environmentalComplianceRate")
            if si.get("environmentalComplianceRate") is not None
            else max(50, 100 - si["environmentalIssuesDiscussed"] * 5))
    rate = min(100, round1(rate))
    color = ("Green" if rate >= 95 else "Yellow" if rate >= 85
             else "Amber" if rate >= 70 else "Red")
    violations = si.get("environmentalViolations") or 0
    evidence = f"Environmental compliance: {_js_str(rate)}%"
    if violations:
        evidence += f", {_js_str(violations)} violations recorded"
    if is_derived:
        evidence += " (estimated from meeting records; upload Environmental Report for permit data)"
    return {
        "method_class": "Environmental_Compliance",
        "status_color": color,
        "compliance_rate": rate,
        "issues_discussed": si["environmentalIssuesDiscussed"],
        "violations": violations,
        "evidence_metric": evidence,
    }


# ------------------------------------------------------------ A6.4 Contractor Performance


def run_contractor_performance(si: dict, rand: Callable[[], float],
                               period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("overallRating", "scheduleRating", "costRating")):
        return insufficient("Contractor_Performance")
    overall = num(si.get("overallRating"), 0)
    sched = num(si.get("scheduleRating"), 0)
    cost = num(si.get("costRating"), 0)
    worst = min(overall, sched, cost)
    color = ("Green" if worst >= 4.0 else "Yellow" if worst >= 3.5
             else "Amber" if worst >= 3.0 else "Red")
    return {
        "method_class": "Contractor_Performance",
        "status_color": color,
        "min_rating": round1(worst),
        "evidence_metric": (
            f"Ratings: overall {_js_str(round1(overall))}, schedule {_js_str(round1(sched))}, "
            f"cost {_js_str(round1(cost))} (worst {_js_str(round1(worst))}/5)"
        ),
    }


A4_EXTENSIONS: dict[str, tuple[str, Callable]] = {
    "A4.2": ("RFI_Velocity", run_rfi_velocity),
    "A4.3": ("Submittal_Rejection", run_submittal_rejection),
    "A4.4": ("NCR_Rate", run_ncr_rate),
    "A4.5": ("Weather_Impact", run_weather_impact),
    "A4.6": ("CO_Frequency", run_co_frequency),
    "A4.7": ("Dispute_Escalation", run_dispute_escalation),
    "A4.8": ("Subcontractor_Performance", run_subcontractor_performance),
    "A4.9": ("Procurement_Lead_Time", run_procurement_lead_time),
    "A4.10": ("Spec_Conflict_Density", run_spec_conflict_density),
}

A5_EXTENSIONS: dict[str, tuple[str, Callable]] = {
    "A5.2": ("Sensitivity_Analysis", run_sensitivity_analysis),
    "A5.3": ("Tornado_Diagram", run_tornado_diagram),
    "A5.4": ("Scenario_Modeling", run_scenario_modeling),
    "A5.5": ("Rework_Feedback", run_rework_feedback),
    "A5.6": ("Queueing_Bottleneck", run_queueing_bottleneck),
    "A5.7": ("Agent_Supply_Chain", run_agent_supply_chain),
    "A5.8": ("Discrete_Event_Sim", run_discrete_event_sim),
}

A6_EXTENSIONS: dict[str, tuple[str, Callable]] = {
    "A6.1": ("Quality_Compliance", run_quality_compliance),
    "A6.2": ("Safety_Performance", run_safety_performance),
    "A6.3": ("Environmental_Compliance", run_environmental_compliance),
    "A6.4": ("Contractor_Performance", run_contractor_performance),
}
