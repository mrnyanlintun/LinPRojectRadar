"""
A4/A5/A6 extension models: document-derived signals, system dynamics, delivery quality.

Ported from assets/js/simulations.js (Cat 4 doc/risk extensions, Cat 5 system dynamics,
the derived-field modules and the dormant-module section), validated numerically against the
JavaScript executed in a browser. See VALIDATION.md for the per-module comparison.

All twenty are deterministic; `rand` is accepted only for the registry's one call signature.

Porting hazards specific to this file:

- Truthiness contributions: Rework Feedback still weights `si.rfiCount ? ... : 0`, so a reported
  zero contributes nothing there via JS falsiness, reproduced with explicit checks. RUN 7 REMOVED
  THAT FROM DISPUTE ESCALATION, because it made an absent log and a log that recorded nothing
  indistinguishable and let a project improve its reading by withholding evidence. Rework Feedback
  carries the identical construct and was NOT in the Run 6 defect list, so it is unchanged and
  recorded in the Run 7 report as the clearest candidate for the next run.
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

from .models import (
    ABSTAIN_INVALID_DENOMINATOR, ABSTAIN_MALFORMED_INPUT, ABSTAIN_MISSING_INPUT,
    ABSTAIN_NO_EXPOSURE, check_inputs, eligible, insufficient, refuse,
)
from .models_ext import _derived, _js_str
from .rng import js_round, num, round1, round2

_RANK = {"Green": 0, "Yellow": 1, "Amber": 2, "Red": 3}


def _and_list(items: list[str]) -> str:
    """A list of things in prose. The word "and", never an ampersand, per the naming rules."""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


# ------------------------------------------------------------ A4.2 RFI Velocity


def run_rfi_velocity(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    count = si.get("rfiCount") if si.get("rfiCount") is not None else si.get("rfiNumber")
    days = si.get("rfiPeriodDays")
    if count is None:
        return insufficient("RFI_Velocity")
    # THE ABSTENTION GUARDS. Run 4 (validate the seven). The elapsed days are the denominator of
    # a velocity, and the module's own declared input contract names them, yet an absent figure
    # was replaced by thirty and the finding then stated "over 30 days" as though the document
    # had said so. The note that would have marked it as assumed rides on a derived-source flag
    # that nothing on the server ever sets, so on the real path the substitution was silent. A
    # count of requests or a span of days below zero, and an overdue count larger than the total,
    # are outside the domain of the two ratios this module forms.
    if days is None:
        return insufficient(
            "RFI_Velocity",
            "Awaiting the number of days the request log covers: a rate of requests over time "
            "cannot be formed without the span of time it was measured over",
        )
    if not days > 0 or count < 0:
        return insufficient(
            "RFI_Velocity",
            "Awaiting a request count and a log period that can form a rate: the figures read "
            "from the request log cannot both be right",
        )
    overdue_raw = si.get("rfiOverdue")
    if overdue_raw is not None and (overdue_raw < 0 or overdue_raw > count):
        return insufficient(
            "RFI_Velocity",
            "Awaiting an overdue count that lies within the total: the figures read from the "
            "request log cannot both be right",
        )
    is_derived = _derived(si, "rfiPeriodDays")
    per30 = js_round((count / days) * 300) / 10
    per_week = js_round((count / days) * 70) / 10
    # THE BAND, AND WHAT IT IS SOURCED TO: NOTHING. Run 4 looked for a source specifying two,
    # four and eight requests per week, and for one specifying ten, twenty and thirty-five per
    # cent overdue, and found neither. Industry studies of requests for information do publish
    # numbers -- counts per project and average response times -- but a count per project or a
    # response time is not a per-week rate threshold, and a normalisation this module does not
    # perform (by contract value, by trade, by phase) sits between them. The boundaries are left
    # as they were, uncited, and this module DOES NOT VOTE. See registry.CORE_VOTING_MODULES.
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
        return insufficient(
            "Submittal_Rejection",
            "Awaiting a submittal register with entries in it: a rejection share has no "
            "denominator without one",
        )
    # THE ABSTENTION GUARD. Run 4 (validate the seven). A rejected count outside the total is
    # outside the domain of a share of one in the other, and produced a rate above one, which
    # every band above the top boundary silently absorbs into Red.
    if rejected < 0 or rejected > total:
        return insufficient(
            "Submittal_Rejection",
            "Awaiting a rejected count that lies within the total: the figures read from the "
            "register cannot both be right",
        )
    rate = js_round((rejected / total) * 1000) / 1000
    # THE BAND, AND WHAT IT IS SOURCED TO: NOTHING. Run 4 looked for a source specifying five,
    # fifteen and twenty-five per cent for a submittal rejection share and found none. Rejection
    # depends on what the specification requires a submittal to contain and on the reviewer's
    # own practice, and no recommended practice or peer-reviewed study located here states a
    # numeric threshold for it. The boundaries are left as they were, uncited, and this module
    # DOES NOT VOTE. See registry.CORE_VOTING_MODULES.
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
    """
    THE FIFTEEN DEFECTS, defect 11, and it is one of the permanent abstentions.

    The ratio was open nonconformances over nonconformances ISSUED THIS PERIOD, which are not
    one set. The open figure is a backlog, a stock carried from every period since the project
    began; the issued figure is this period's flow. Dividing one by the other is not a rate of
    anything, and it is unbounded above: a project that closed its intake but still carries
    twelve open nonconformances and issued two this period scored six. `max(issued, 1)` then
    invented a denominator of one whenever the intake was empty, so a backlog of twelve against
    no intake at all scored twelve, and the ladder below read every one of those as Red.

    The zero-intake arm was worse than unbounded, it was backwards: it returned GREEN, with the
    finding "No NCRs issued this period", on a project that could be carrying an unresolved
    backlog of any size. Issuing nothing new is not evidence of quality.

    A backlog needs a cohort to be a rate of: the audited population of nonconformances the
    backlog is drawn from. That is what the Quality Audit Report carries as its findings total,
    and it is required now. No cohort, no rate: this abstains, and states that it is waiting for
    the audited cohort rather than reporting a number built from two different sets.

    The Quality Audit Report type exists for one project in the corpus today, so this
    computation abstains on the rest until the corpus lands (remediation_decisions_answered.md
    2.3). That is the expected outcome of this fix, not a shortfall in it.
    """
    if not check_inputs(si, ("ncrIssued", "ncrClosed", "ncrOpen")):
        return insufficient("NCR_Rate")
    issued = num(si.get("ncrIssued"), 0)
    open_ = num(si.get("ncrOpen"), 0)
    cohort = num(si.get("totalFindings"), None)
    if cohort is None or cohort <= 0:
        return insufficient(
            "NCR_Rate",
            "Awaiting an audited nonconformance cohort: the open backlog is carried across "
            "periods and cannot be measured against one period's intake")
    if open_ < 0:
        return insufficient(
            "NCR_Rate", "A negative count of open nonconformances is not a measurable backlog")
    if open_ > cohort:
        return insufficient(
            "NCR_Rate",
            f"More nonconformances are recorded open ({_js_str(open_)}) than the audited "
            f"cohort contains ({_js_str(cohort)}), so no proportion is measurable from this pair")
    open_ratio = open_ / cohort
    color = ("Green" if open_ratio < 0.15 else "Yellow" if open_ratio < 0.30
             else "Amber" if open_ratio < 0.50 else "Red")
    return {
        "method_class": "NCR_Rate",
        "status_color": color,
        "open_ratio": round2(open_ratio),
        "audited_cohort": cohort,
        "evidence_metric": (
            f"{_js_str(open_)} open of an audited cohort of {_js_str(cohort)} "
            f"nonconformances, {_js_str(issued)} issued this period "
            f"(open ratio {_js_str(round2(open_ratio))})"
        ),
    }


# ------------------------------------------------------------ A4.5 Weather Day Impact


def run_weather_impact(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    THE FIFTEEN DEFECTS, defect 12, and it is one of the permanent abstentions.

    This computation reports lost days as a proportion of the float available to absorb them, and
    it fabricated that proportion in two ways.

    When no float figure existed at all, the ratio was set to 1.0 whenever any day had been lost.
    That is not an unknown reported as an unknown, it is the WORST case asserted as a
    measurement: one lost day on a project with a year of float scored identically to one that
    had none, and the ladder read it Red either way. When float was recorded as zero or negative,
    the same line fired, so a project already behind was assigned a ratio rather than refused.

    The days themselves were also allowed to be a derivation rather than a count. The field
    report's own weather-day figure is a verified count; anything the pipeline inferred is not,
    and the module carried the inference into the same arithmetic and appended a parenthetical
    to the sentence. A qualifier in a display string is not a substitute for refusing.

    Both are removed. Verified lost days and a positive float figure are required, and the ratio
    is computed only from the two of them. Note the honest consequence: the float here is
    network-derived, and the corpus does not carry an activity network, so this computation is
    expected to abstain until it does. Abstaining is the correct outcome.
    """
    if not check_inputs(si, ("weatherDaysLost",)):
        return insufficient("Weather_Impact")
    if _derived(si, "weatherDaysLost"):
        return insufficient(
            "Weather_Impact",
            "Awaiting verified lost days: the weather days available were inferred rather "
            "than counted in a field report")
    lost = si["weatherDaysLost"]
    if lost < 0:
        return insufficient(
            "Weather_Impact", "A negative count of lost days is not a measurable weather impact")
    if si.get("floatRemaining") is not None:
        flt = si["floatRemaining"]
    elif si.get("totalFloat") is not None and si.get("consumedFloat") is not None:
        flt = si["totalFloat"] - si["consumedFloat"]
    else:
        flt = None
    if flt is None:
        return insufficient(
            "Weather_Impact",
            "Awaiting the schedule float available to absorb the lost days: without it there "
            "is nothing to measure the impact against")
    if not flt > 0:
        return insufficient(
            "Weather_Impact",
            "No positive float remains to absorb lost days, so no proportion of it is "
            "measurable")
    ratio = lost / flt
    color = ("Green" if lost == 0 else "Yellow" if ratio <= 0.20
             else "Amber" if ratio <= 0.50 else "Red")
    evidence = (f"{_js_str(lost)} weather days lost, "
                f"{int(js_round(ratio * 100))}% of available float consumed")
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
    """
    RUN 7. THE SIGNAL IMPROVED WHEN EVIDENCE WAS WITHHELD, AND THAT IS WHAT IS CORRECTED.

    The weights are 0.3 for the request term, 0.3 for the change term and 0.4 for the document
    risk, and only the document risk was required. An absent request log and an absent change
    order log each contributed zero to the sum rather than being absent from it, so the identical
    project read 0.8 when it reported both logs and 0.2 when it reported neither: three bands
    better for withholding the evidence. A composite whose missing terms score zero rewards
    silence, and silence is the one thing a project condition must never reward.

    The correction is to the missingness semantics, not to the weights and not to the method.
    All three inputs are now required. A project that reports every source is measured on the
    same ad hoc weighted sum it always was, with the same weights and the same bands. A project
    that reports fewer abstains and says which source is missing, because there is no defensible
    reading of a three-source composite from one source: renormalising the present terms would
    still let removing a high term improve the reading, which is the same fault in a subtler
    form.

    A reported count of zero is evidence and is treated as one. The previous code tested the
    counts for JavaScript truthiness, so a log that had been read and recorded no entries was
    indistinguishable from a log that had never been read.

    The finding text named two quantities the module does not compute. It said "RFI velocity"
    where the term is a raw request count capped at twenty, and "CO frequency" where the term is
    a raw change order count capped at ten. Neither has a time or exposure denominator, so
    neither is a velocity or a frequency, and the text now names the counts it actually uses.

    No dispute document, claim register or new corpus is introduced by this run, and no formal
    dispute is inferred from this activity: the module stays the advisory, non-voting proxy its
    qualifier describes.
    """
    required = (
        ("docRiskScore", "a document risk score"),
        ("rfiCount", "a count of requests for information"),
        ("changeOrderCount", "a count of change orders"),
    )
    missing = [words for key, words in required if si.get(key) is None]
    if missing:
        return insufficient(
            "Dispute_Escalation",
            "Insufficient data: this reading combines a document risk score, a count of "
            "requests for information and a count of change orders, and it is missing "
            + _and_list(missing)
            + ". A reading is not offered from the remaining sources, because a source that is "
            "absent would otherwise count as a source that is quiet.",
            ABSTAIN_MISSING_INPUT)
    for key, words in required:
        if num(si.get(key), None) is None or si[key] < 0:
            return insufficient(
                "Dispute_Escalation",
                f"Insufficient data: {words} was reported as a negative figure or in a form "
                f"that is not a number.",
                ABSTAIN_MALFORMED_INPUT)
    rfi_w = min(si["rfiCount"] / 20, 1) * 0.3
    co_w = min(si["changeOrderCount"] / 10, 1) * 0.3
    doc_w = si["docRiskScore"] * 0.4
    index = round2(rfi_w + co_w + doc_w)
    color = ("Green" if index <= 0.20 else "Yellow" if index <= 0.40
             else "Amber" if index <= 0.65 else "Red")
    return {
        "method_class": "Dispute_Escalation",
        "status_color": color,
        "escalation_index": index,
        # The trace: every source this reading rests on, so which evidence is behind the number
        # is visible rather than inferred from the number. All three are present or the module
        # has already abstained above, and the qualification says so either way.
        "sources_used": ["document risk score", "count of requests for information",
                         "count of change orders"],
        "sources_missing": [],
        "evidence_metric": (
            f"Dispute escalation index: {_js_str(index)} "
            f"(document risk, request count and change order count combined)"
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
    """
    THE FIFTEEN DEFECTS, defect 4. The weighted ratio was `(at_risk + 2 * delayed) / total`, and
    a procurement log recording ten long-lead items of which eight are at risk and five are
    already delayed produced 1.8: a proportion of a set, reported as one hundred and eighty per
    cent of it.

    Two errors compounded. A delayed item is an at-risk item that has already slipped, so it was
    counted twice, once in each term. And the doubling of the delayed term put the numerator
    above the denominator without anything noticing, because nothing bounded the result.

    Delayed items are now treated as the subset of at-risk items they are: each delayed item
    carries full weight, each remaining at-risk item carries half, and the ratio is a genuine
    proportion of the long-lead set. On the audit's own figures it is 0.65 rather than 1.8.

    The domain is enforced rather than assumed. `max(total, 1)` silently invented a denominator
    of one for an empty procurement log, so a single delayed item out of no items scored 2.0;
    an empty log now abstains. Counts that cannot describe one set (more at risk than exist, more
    delayed than are at risk, a negative count) abstain and say which pair disagreed.
    """
    if not check_inputs(si, ("longLeadItemsTotal", "longLeadAtRisk", "longLeadDelayed")):
        return insufficient("Procurement_Lead_Time")
    total = num(si.get("longLeadItemsTotal"), 0)
    at_risk = num(si.get("longLeadAtRisk"), 0)
    delayed = num(si.get("longLeadDelayed"), 0)
    if total <= 0:
        return insufficient(
            "Procurement_Lead_Time",
            "No long-lead items are recorded, so there is no set to measure disruption against")
    if at_risk < 0 or delayed < 0:
        return insufficient(
            "Procurement_Lead_Time",
            "A negative count of long-lead items is not a measurable procurement state")
    if at_risk > total:
        return insufficient(
            "Procurement_Lead_Time",
            f"More long-lead items are recorded at risk ({_js_str(at_risk)}) than exist "
            f"({_js_str(total)}), so no proportion is measurable from this pair")
    if delayed > at_risk:
        return insufficient(
            "Procurement_Lead_Time",
            f"More long-lead items are recorded delayed ({_js_str(delayed)}) than at risk "
            f"({_js_str(at_risk)}), and a delayed item is an at-risk item that has slipped")
    risk_ratio = (delayed + 0.5 * (at_risk - delayed)) / total
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
    """
    RUN 7. The density is the document risk weighted by request volume: risk times the count over
    the square root of the count. With no requests there is no volume to weight by, and the code
    substituted the unweighted document risk, so a project with an empty request log was assigned
    a conflict density it had reported nothing to support and read Yellow. The substitution is
    removed: with no requests the module abstains on no exposure rather than reporting the
    document risk under a different name. A negative count is refused as malformed.
    """
    if not check_inputs(si, ("docRiskScore", "rfiCount")):
        return insufficient("Spec_Conflict_Density",
                            "Insufficient data: a document risk score and a count of requests "
                            "for information are needed, and at least one of them has not been "
                            "reported for this period.",
                            ABSTAIN_MISSING_INPUT)
    if num(si.get("rfiCount"), None) is None or si["rfiCount"] < 0:
        return insufficient("Spec_Conflict_Density",
                            "Insufficient data: the count of requests for information was "
                            "reported in a form that is not a count.",
                            ABSTAIN_MALFORMED_INPUT)
    if si["rfiCount"] == 0:
        return insufficient("Spec_Conflict_Density",
                            "No requests for information are recorded for this project, so "
                            "there is no request volume for a conflict density to be measured "
                            "over. The document risk score is not reported in its place.",
                            ABSTAIN_NO_EXPOSURE)
    density = (si["docRiskScore"] * si["rfiCount"]) / math.sqrt(si["rfiCount"])
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
    """
    THE FIFTEEN DEFECTS, defect 13. The earned value domains here were guarded only at exactly
    zero, and the guard at zero is the least of what can go wrong.

    A NEGATIVE cost or schedule index passed every check and then divided the remaining work,
    turning a forecast into a number below the money already spent: the pessimistic case came
    out cheaper than the optimistic one, the range went negative, and the ladder read the whole
    thing Green because a negative pessimistic forecast is comfortably under the budget. A
    negative budget did the same to the range, which is a percentage of it. Earned value above
    the budget at completion made the remaining work negative, so every scenario forecast a
    project finishing below what it had already spent.

    None of these is a project condition. Each is an input pair that cannot be reconciled, and
    each abstains and says which one it was.
    """
    if not check_inputs(si, ("bac", "ev", "ac", "cpi", "spi")):
        return insufficient("Scenario_Modeling")
    if si["cpi"] <= 0 or si["spi"] <= 0:
        return insufficient(
            "Scenario_Modeling",
            "Cost or schedule performance is recorded as zero or below, which no remaining "
            "work can be divided by")
    if si["bac"] <= 0:
        return insufficient(
            "Scenario_Modeling",
            "No positive budget at completion is recorded to scale the scenarios against")
    if si["ev"] < 0 or si["ac"] < 0:
        return insufficient(
            "Scenario_Modeling",
            "Negative earned value or actual cost is not a measurable position to forecast from")
    if si["ev"] > si["bac"]:
        return insufficient(
            "Scenario_Modeling",
            "More value is recorded as earned than the budget at completion contains, so there "
            "is no remaining work to forecast")
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
    """
    RUN 7. `max(planned, 1)` invented a denominator of one activity for a project that planned
    none, so an empty look-ahead window produced a queue ratio of zero and read Green. This is
    the same fabricated denominator the fifteen-defects run removed from the look-ahead measure
    and the procurement measure, still standing in a module that reads the identical two fields.
    The known-answer run put it plainly: two modules read the same window and one abstained on it
    while the other read Green. They now agree, through the shared eligibility layer.

    A constrained count above the planned count is malformed rather than missing, and refused on
    the same footing the look-ahead measure refuses it.

    The module remains what its qualifier says it is. A queueing model needs arrival rates,
    service rates, capacity and a queue discipline, none of which are in the corpus, and this run
    does not invent them.
    """
    if not check_inputs(si, ("activitiesPlanned", "activitiesConstrained")):
        return insufficient("Queueing_Bottleneck",
                            "Insufficient data: the planned and constrained activity counts are "
                            "needed, and at least one of them has not been reported for this "
                            "period.",
                            ABSTAIN_MISSING_INPUT)
    verdict = eligible(si, positive=(("activitiesPlanned", "the count of planned activities"),))
    if verdict:
        return refuse("Queueing_Bottleneck", verdict)
    planned = num(si.get("activitiesPlanned"), 0)
    constrained = num(si.get("activitiesConstrained"), 0)
    if constrained < 0 or constrained > planned:
        return insufficient("Queueing_Bottleneck",
                            "Insufficient data: the number of constrained activities reported "
                            "is negative or larger than the number planned, so the two figures "
                            "do not describe the same window.",
                            ABSTAIN_MALFORMED_INPUT)
    ratio = constrained / planned
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
    """
    RUN 7. `max(total, 1)` invented one long-lead item for a project whose long-lead log is
    empty, so an at-risk share of zero was reported and read Green. An empty log is not evidence
    that nothing is at risk; it is the absence of the population the share is a share OF. The
    module abstains on no exposure, and a count of items at risk exceeding the total is refused
    as malformed.

    Agents, states, rules and interactions are not in the corpus. The module is a share of a
    procurement log and this run does not turn it into anything else.
    """
    if not check_inputs(si, ("longLeadItemsTotal", "longLeadAtRisk")):
        return insufficient("Agent_Supply_Chain",
                            "Insufficient data: the total and at-risk long-lead item counts are "
                            "needed, and at least one of them has not been reported for this "
                            "period.",
                            ABSTAIN_MISSING_INPUT)
    total = num(si.get("longLeadItemsTotal"), 0)
    at_risk = num(si.get("longLeadAtRisk"), 0)
    if total <= 0:
        return insufficient("Agent_Supply_Chain",
                            "No long-lead items are recorded for this project, so there is no "
                            "set of items for a share of them to be at risk. No share is "
                            "reported in place of one.",
                            ABSTAIN_NO_EXPOSURE)
    if at_risk < 0 or at_risk > total:
        return insufficient("Agent_Supply_Chain",
                            "Insufficient data: the number of long-lead items reported at risk "
                            "is negative or larger than the number recorded, so the two figures "
                            "do not describe the same log.",
                            ABSTAIN_MALFORMED_INPUT)
    ratio = at_risk / total
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
    """
    RUN 7. Where no planned progress had been reported the progress ratio was substituted as
    exactly 1, the value of a project running precisely to plan, which drove the interruption
    term to zero and read Green. Planned progress is the denominator of that ratio and is now
    required to be above zero.

    Events, entities, resources, queues and a clock are not in the corpus. This module is a
    throughput index computed from two indices and a progress ratio, and the correction is to its
    refusal behaviour only.
    """
    if not check_inputs(si, ("spi", "actualPctComplete", "plannedPctComplete", "cpi")):
        return insufficient("Discrete_Event_Sim",
                            "Insufficient data: both performance indices and both the planned "
                            "and reported percent complete are needed, and at least one of them "
                            "has not been reported for this period.",
                            ABSTAIN_MISSING_INPUT)
    verdict = eligible(si, positive=(("plannedPctComplete", "the planned percent complete"),))
    if verdict:
        return refuse("Discrete_Event_Sim", verdict)
    progress_ratio = si["actualPctComplete"] / si["plannedPctComplete"]
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
    """
    THE FIFTEEN DEFECTS, defect 3. This returned quality scores outside the domain a percentage
    can occupy: five items inspected and eight failed gave a pass rate of minus sixty per cent
    and a score of minus sixty out of a hundred, which the band ladder then read as Red. Red is
    the right colour for the wrong reason, and the number beside it was not a quantity.

    Three fabrications are removed and one refusal added.

    The inspected count no longer defaults to TWENTY. There is no inspection of twenty items; it
    was a placeholder, and it silently set the denominator of every project that never uploaded
    an inspection report.

    The failed count no longer falls back to the deficiency count. Those are two different
    quantities counted by two different documents: a deficiency noted in a field report is not an
    inspection lot that failed, and substituting one for the other is the class of error the
    extraction prompt was rewritten to forbid.

    A pass rate is therefore computed only from a real inspected and failed pair, and an audit
    score only from a real audited score. With neither, the computation abstains.

    And the refusal: more failures than inspections is not a project condition, it is an
    inconsistent input pair. Returning a number outside the domain for it is worse than saying
    so, so it abstains and states what it saw.
    """
    if not check_inputs(si, ("qualityDeficienciesNoted",)):
        return insufficient("Quality_Compliance")
    is_derived = _derived(si, "qualityDeficienciesNoted")
    inspected = si.get("itemsInspected")
    failed = si.get("itemsFailed")
    audit = si.get("qualityAuditScore")
    pass_rate = None
    if inspected is not None and failed is not None:
        if inspected <= 0:
            return insufficient(
                "Quality_Compliance",
                "No items were recorded as inspected, so no pass rate can be measured")
        if failed > inspected:
            return insufficient(
                "Quality_Compliance",
                f"More items are recorded as failed ({_js_str(failed)}) than as inspected "
                f"({_js_str(inspected)}), so no pass rate is measurable from this pair")
        if failed < 0:
            return insufficient(
                "Quality_Compliance",
                "A negative number of failed items is not a measurable inspection result")
        pass_rate = (inspected - failed) / inspected
    if audit is None:
        if pass_rate is None:
            return insufficient(
                "Quality_Compliance",
                "Awaiting an audited quality score, or a recorded inspected and failed pair")
        audit = pass_rate * 100
    color = ("Green" if audit >= 85 else "Yellow" if audit >= 70
             else "Amber" if audit >= 55 else "Red")
    return {
        "method_class": "Quality_Compliance",
        "status_color": color,
        "quality_score": int(js_round(audit)),
        # None, not a substituted figure, when no inspected/failed pair was recorded: the score
        # came from the audit and there is no pass rate to report beside it.
        "pass_rate": (int(js_round(pass_rate * 100)) if pass_rate is not None else None),
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
    """
    RUN 7, AND THIS ONE KEEPS COMPUTING, WHICH IS THE POINT OF CLASSIFYING RATHER THAN REFUSING
    EVERYWHERE.

    A reported zero incidents is a measurement, not an absence: the safety records were read and
    they recorded nothing. The band is therefore left standing on a reported zero, which is the
    disposition the owner's instruction calls a true zero.

    What was wrong is the index beside it. The safety index is the benchmark over the reported
    rate, capped by the module's own `min(2, ...)`. At a rate of zero that ratio is unbounded and
    the cap is the module's own answer to an unbounded ratio, which is 2. The code substituted 1
    instead, a number the formula never produces at a zero rate and which reads as performance
    exactly at benchmark. The cap is now used, so the index is derived from the module's own
    stated formula in every case rather than from a literal in one of them.

    A negative rate is refused: it is outside the domain a rate can occupy, and left alone it
    banded Green because a negative number is below the benchmark.
    """
    if not check_inputs(si, ("safetyIncidentsDiscussed",)):
        return insufficient("Safety_Performance",
                            "Insufficient data: no safety record has been reported for this "
                            "period.",
                            ABSTAIN_MISSING_INPUT)
    is_derived = _derived(si, "safetyIncidentsDiscussed")
    rate = (si.get("oshaIncidentRate") if si.get("oshaIncidentRate") is not None
            else si["safetyIncidentsDiscussed"] * 10)
    if num(rate, None) is None or rate < 0:
        return insufficient("Safety_Performance",
                            "Insufficient data: the safety incident rate was reported as a "
                            "negative figure or in a form that is not a number, and a rate "
                            "cannot be either.",
                            ABSTAIN_MALFORMED_INPUT)
    benchmark = 3.0
    # The module's own cap is its own answer to a ratio without an upper bound, and a rate of
    # zero is exactly that case. No literal is substituted here.
    index = min(2, round2(benchmark / rate)) if rate > 0 else 2
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
    """
    THE FIFTEEN DEFECTS, defect 15, and it is one of the permanent abstentions.

    When no compliance rate had been reported, this computed one: `max(50, 100 - issues * 5)`.
    That formula is not a measurement and does not derive from one. It converts a count of times
    the environment came up in a meeting into a percentage, at five points per mention, floored
    so it can never fall below fifty however many times it was raised. A project where the
    subject was never discussed scored one hundred per cent compliant, which is the opposite of
    what silence means. The band ladder then read that number, so a project's environmental
    status was set by how talkative its minutes were.

    An environmental compliance rate is a proportion of audited permit conditions met, and only
    an environmental compliance report carries it. It is required now, and a rate outside nought
    to a hundred is refused rather than clipped, because clipping a figure into the domain hides
    that the figure was wrong.

    The Environmental Compliance Report type exists for one project in the corpus today, so this
    computation abstains on the rest until the corpus lands (remediation_decisions_answered.md
    2.3). That is the expected outcome of this fix.
    """
    if not check_inputs(si, ("environmentalIssuesDiscussed",)):
        return insufficient("Environmental_Compliance")
    rate = si.get("environmentalComplianceRate")
    if rate is None:
        return insufficient(
            "Environmental_Compliance",
            "Awaiting audited permit compliance data: how often the subject was raised in a "
            "meeting is not a measure of compliance")
    if rate < 0 or rate > 100:
        return insufficient(
            "Environmental_Compliance",
            f"A compliance rate of {_js_str(round1(rate))} per cent is outside the range a "
            f"proportion of permit conditions can take")
    rate = round1(rate)
    color = ("Green" if rate >= 95 else "Yellow" if rate >= 85
             else "Amber" if rate >= 70 else "Red")
    violations = si.get("environmentalViolations") or 0
    evidence = f"Environmental compliance: {_js_str(rate)}%"
    if violations:
        evidence += f", {_js_str(violations)} violations recorded"
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
    """
    THE FIFTEEN DEFECTS, defect 14. A performance evaluation carries four ratings and this read
    three of them. `qualityRating` is a declared field, the extraction pipeline emits it from the
    same performance evaluation as the other three, it arrives in the same dictionary, and the
    computation stepped over it: the worst rating was taken across overall, schedule and cost
    only. So a contractor rated well on cost and schedule and badly on QUALITY reported its
    schedule or cost figure as its worst, and the band ladder read the evaluation as satisfactory
    on the strength of the three questions the assessor was less worried about.

    The quality rating now enters on the same footing as the other three, and is not required:
    an evaluation that did not rate quality is scored on what it did rate, and the finding names
    exactly which ratings were read.
    """
    if not check_inputs(si, ("overallRating", "scheduleRating", "costRating")):
        return insufficient("Contractor_Performance")
    overall = num(si.get("overallRating"), 0)
    sched = num(si.get("scheduleRating"), 0)
    cost = num(si.get("costRating"), 0)
    quality = num(si.get("qualityRating"), None)
    rated = [overall, sched, cost] + ([quality] if quality is not None else [])
    worst = min(rated)
    color = ("Green" if worst >= 4.0 else "Yellow" if worst >= 3.5
             else "Amber" if worst >= 3.0 else "Red")
    return {
        "method_class": "Contractor_Performance",
        "status_color": color,
        "min_rating": round1(worst),
        "quality_rating": (round1(quality) if quality is not None else None),
        "ratings_read": len(rated),
        "evidence_metric": (
            f"Ratings: overall {_js_str(round1(overall))}, schedule {_js_str(round1(sched))}, "
            f"cost {_js_str(round1(cost))}"
            + (f", quality {_js_str(round1(quality))}" if quality is not None else "")
            + f" (worst {_js_str(round1(worst))}/5)"
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
