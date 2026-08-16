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

from typing import Any, Callable

from .canonical import StructureAbsent
from .canonical_v4 import (
    V4_STRUCTURE_KEYS,
    agent_supply_chain,
    change_frequency,
    des_process_model,
    dispute_escalation,
    ncr_rate,
    procurement_slack,
    queue_model,
    require_v4_structure,
    rework_feedback_loop,
    rfi_velocity,
    scenario_modeling,
    sensitivity_analysis,
    specification_conflict_density,
    subcontractor_performance,
    submittal_rejection,
    tornado_ranking,
    weather_day_impact,
)
from .models import (
    ABSTAIN_MALFORMED_INPUT, ABSTAIN_MISSING_INPUT, ABSTAIN_STRUCTURE_ABSENT,
    calibration_pending, check_inputs, insufficient, refuse,
)
from .models_ext import _derived, _js_str
from .rng import js_round, num, round1, round2

_RANK = {"Green": 0, "Yellow": 1, "Amber": 2, "Red": 3}


def _and_list(items: list[str]) -> str:
    """A list of things in prose. The word "and", never an ampersand, per the naming rules."""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


# =================================================================================================
# RUN 29: CATEGORIES 4 AND 5 AGAINST THE SUPPLIED CANONICAL CONTRACTS.
#
# Every runner from A4.2 to A5.8 below reads its defining structure from `canonical_v4` and
# computes the method the module is named for. Where the structure is absent the runner ABSTAINS.
# Nothing below reconstructs a dispute from a request count, a conflict density from a document
# risk score, a queue from an activity count or an event list from a progress ratio; those were
# the Run-27 findings and they are removed rather than qualified.
#
# THE TWO PLACES WHERE A NON-STRUCTURE PATH SURVIVES, and why they are not proxies. Run 27
# classified A4.2 RFI Velocity and A4.3 Submittal Rejection Rate as METHOD_PASS: each already
# computed exactly the formula the supplied contract states -- requests over exposure time, and
# rejected over the assessed population -- from totals extracted from a real register. Those
# extracted totals are the SAME canonical quantity, not a substitute for it, so they remain a
# supply path and the governed event structure is preferred over them where a project has one.
# For every other module in this run the old computation was a different quantity under the same
# name, and it is gone.
#
# THE BAND. Sixteen of the eighteen now report a quantity the old ladder was not drawn over, so
# they assert NO colour: the figure is reported with calibration pending and Run 33 owns the
# calibration. A4.2 and A4.3 report the identical quantity they always did and keep the ladders
# they always carried, which are recorded as uncalibrated in registry.py and unchanged here.
# =================================================================================================


# ------------------------------------------------------------ A4.2 RFI Velocity


def run_rfi_velocity(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    Requests for information per unit of exposure time.

    SUPPLIED CONTRACT 4.2: RFI Velocity = RFI event count / exposure time, with twelve requests
    over thirty days reading 0.4 per day or twelve per standardised thirty day period, and an
    overdue share of overdue over relevant open where that is separately exposed. Revisions of the
    same cumulative register are not new events.

    WHERE THE GOVERNED EVENT REGISTER IS PRESENT it is used, because only the events themselves
    can be de-duplicated: a cumulative register uploaded every month repeats every earlier row,
    and a total extracted from the latest upload cannot tell a re-reported request from a new one.
    Where it is absent the extracted totals are used, which are the same quantity from a thinner
    record, and where neither is present this abstains.
    """
    structure = si.get(V4_STRUCTURE_KEYS["A4.2"])
    if structure is not None:
        try:
            reading = rfi_velocity(require_v4_structure(si, "A4.2"))
        except StructureAbsent as absent:
            return insufficient("RFI_Velocity", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
        per_week = reading["rate_per_day"] * 7.0
        vel_status = ("Green" if per_week <= 2 else "Yellow" if per_week <= 4
                      else "Amber" if per_week <= 8 else "Red")
        overdue_status = None
        ratio = reading["overdue_ratio"]
        if ratio is not None:
            overdue_status = ("Green" if ratio < 0.10 else "Yellow" if ratio < 0.20
                              else "Amber" if ratio < 0.35 else "Red")
        status = (overdue_status
                  if overdue_status and _RANK[overdue_status] > _RANK[vel_status] else vel_status)
        evidence = (
            f"{_js_str(reading['events_counted'])} requests for information over "
            f"{_js_str(reading['exposure_days'])} days "
            f"({_js_str(round2(reading['rate_per_day']))} a day, "
            f"{_js_str(round1(reading['rate_per_30_days']))} in a standard thirty day period)")
        if reading["duplicate_rows_collapsed"]:
            evidence += (f", from {_js_str(reading['rows_supplied'])} register rows of which "
                         f"{_js_str(reading['duplicate_rows_collapsed'])} repeat a request "
                         f"already counted")
        if ratio is not None:
            evidence += (f", {_js_str(reading['overdue'])} of "
                         f"{_js_str(reading['open_relevant'])} still open are overdue")
        return {
            "method_class": "RFI_Velocity",
            "status_color": status,
            "rfi_per_30d": round1(reading["rate_per_30_days"]),
            "rfi_per_week": round1(per_week),
            "rate_per_day": round2(reading["rate_per_day"]),
            "total_rfis": reading["events_counted"],
            "period_days": reading["exposure_days"],
            "rows_supplied": reading["rows_supplied"],
            "duplicate_rows_collapsed": reading["duplicate_rows_collapsed"],
            "open_rfis": reading["open_relevant"],
            "overdue_rfis": reading["overdue"],
            "overdue_ratio": (round(ratio, 3) if ratio is not None else None),
            "canonical_structure": "rfi_event_log",
            "register_id": reading["register_id"],
            "source": reading["source"],
            "evidence_metric": evidence,
        }
    count = si.get("rfiCount") if si.get("rfiCount") is not None else si.get("rfiNumber")
    days = si.get("rfiPeriodDays")
    if count is None:
        return insufficient("RFI_Velocity")
    # THE ABSTENTION GUARDS. Run 4 (validate the seven). The elapsed days are the denominator of
    # a velocity, and the module's own declared input contract names them, yet an absent figure
    # was replaced by thirty and the finding then stated "over 30 days" as though the document
    # had said so. A count of requests or a span of days below zero, and an overdue count larger
    # than the total, are outside the domain of the two ratios this module forms.
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
    # cent overdue, and found neither. The boundaries are left as they were, uncited, and this
    # module DOES NOT VOTE. See registry.CORE_VOTING_MODULES.
    vel_status = ("Green" if per_week <= 2 else "Yellow" if per_week <= 4
                  else "Amber" if per_week <= 8 else "Red")
    overdue_ratio = None
    overdue_status = None
    if si.get("rfiOverdue") is not None and count > 0:
        overdue_ratio = si["rfiOverdue"] / count
        overdue_status = ("Green" if overdue_ratio < 0.10 else "Yellow" if overdue_ratio < 0.20
                          else "Amber" if overdue_ratio < 0.35 else "Red")
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
        "canonical_structure": "extracted_register_totals",
        "evidence_metric": evidence,
    }


# ------------------------------------------------------------ A4.3 Submittal Rejection Rate


def run_submittal_rejection(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    Rejected submittals as a share of the assessed population.

    SUPPLIED CONTRACT 4.3: RejectionRate = Rejected / AssessedPopulation, three rejected of twenty
    assessed reading 0.15, with 0 <= Rejected <= AssessedPopulation, a governed disposition
    taxonomy that does not silently merge approved-as-noted with revise-and-resubmit with
    rejected, and a denominator that does not mix this period's decisions with a cumulative
    backlog.

    WHERE THE GOVERNED DECISION REGISTER IS PRESENT it is used, because only the decisions
    themselves carry a disposition to be governed and a period to be filtered on. Where it is
    absent the extracted totals are used, which are the same share from a thinner record.
    """
    structure = si.get(V4_STRUCTURE_KEYS["A4.3"])
    if structure is not None:
        try:
            reading = submittal_rejection(require_v4_structure(si, "A4.3"))
        except StructureAbsent as absent:
            return insufficient("Submittal_Rejection", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
        rate = reading["rejection_rate"]
        color = ("Green" if rate <= 0.05 else "Yellow" if rate <= 0.15
                 else "Amber" if rate <= 0.25 else "Red")
        return {
            "method_class": "Submittal_Rejection",
            "status_color": color,
            "rejection_rate": round(rate, 3),
            "rejected": reading["rejected"],
            "total": reading["assessed"],
            "unique_submittals": reading["unique_submittals"],
            "resubmission_cycles": reading["resubmission_cycles"],
            "disposition_counts": reading["disposition_counts"],
            "taxonomy_version": reading["taxonomy_version"],
            "canonical_structure": "submittal_decision_register",
            "source": reading["source"],
            "evidence_metric": (
                f"{_js_str(reading['rejected'])} of {_js_str(reading['assessed'])} assessed "
                f"submittal decisions were rejections "
                f"({int(js_round(rate * 100))} per cent), from "
                f"{_js_str(reading['unique_submittals'])} distinct submittals and "
                f"{_js_str(reading['resubmission_cycles'])} resubmission cycles"
            ),
        }
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
    # outside the domain of a share of one in the other, and produced a rate above one.
    if rejected < 0 or rejected > total:
        return insufficient(
            "Submittal_Rejection",
            "Awaiting a rejected count that lies within the total: the figures read from the "
            "register cannot both be right",
        )
    rate = js_round((rejected / total) * 1000) / 1000
    # THE BAND, AND WHAT IT IS SOURCED TO: NOTHING. Run 4 looked for a source specifying five,
    # fifteen and twenty-five per cent for a submittal rejection share and found none. The
    # boundaries are left as they were, uncited, and this module DOES NOT VOTE.
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
        "canonical_structure": "extracted_register_totals",
        "evidence_metric": evidence,
    }


# ------------------------------------------------------------ A4.4 NCR Rate


def run_ncr_rate(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    Nonconformances per unit of governed exposure.

    SUPPLIED CONTRACT 4.4: NCRRate = NCR events / governed exposure, where the exposure is
    inspections, inspected units, labour hours, work value or another explicit denominator, and
    four nonconformances over one hundred inspections reads 0.04. Open count, age of open,
    severity and closure rate are tracked SEPARATELY. With no exposure, no normalised rate is
    fabricated.

    WHAT v12 DID. It reported open nonconformances as a share of an audited findings cohort. That
    is a backlog share, not a rate: the numerator is a stock carried across periods and the
    denominator is the size of an audit, and the contract's own words are that a ratio whose
    numerator and denominator populations differ is not a universal NCR rate. It is replaced, not
    renamed, and the exposure is now required rather than borrowed from an audit total.
    """
    try:
        reading = ncr_rate(require_v4_structure(si, "A4.4"))
    except StructureAbsent as absent:
        return insufficient("NCR_Rate", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    _open = (f" {_js_str(reading['open_count'])} are still open."
             if reading["open_count"] is not None else "")
    return calibration_pending(
        "NCR_Rate",
        f"{_js_str(reading['ncr_count'])} nonconformances against "
        f"{_js_str(reading['exposure_quantity'])} {reading['exposure_unit']}, a rate of "
        f"{_js_str(round(reading['ncr_rate'], 4))} for each one." + _open,
        ncr_rate=round(reading["ncr_rate"], 6),
        ncr_count_basis=reading["ncr_count_basis"],
        event_detail_available=reading["event_detail_available"],
        ncr_count=reading["ncr_count"],
        exposure_unit=reading["exposure_unit"],
        exposure_quantity=reading["exposure_quantity"],
        open_count=reading["open_count"],
        closed_count=reading["closed_count"],
        reopened_count=reading["reopened_count"],
        closure_rate=(round(reading["closure_rate"], 4)
                      if reading["closure_rate"] is not None else None),
        mean_open_age_days=(round(reading["mean_open_age_days"], 2)
                            if reading["mean_open_age_days"] is not None else None),
        max_open_age_days=reading["max_open_age_days"],
        severity_counts=reading["severity_counts"],
        canonical_structure="ncr_exposure_record",
        source=reading["source"],
    )


# ------------------------------------------------------------ A4.5 Weather Day Impact


def run_weather_impact(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    The modelled schedule consequence of verified weather events.

    SUPPLIED CONTRACT 4.5: weather occurrence is not schedule impact. Full impact requires the
    event, the affected activity, the planned work, the lost time, the governing allowance or
    calendar, the path and its float, causal evidence and a modelled consequence. A verified event
    causing two lost days on a zero-float critical activity with no mitigation has a direct
    modelled path effect, before recovery logic, of two days. With no schedule linkage the answer
    is NOT ESTIMABLE for impact, and the method is not renamed to preserve the old proxy.

    WHAT v12 DID. Lost days divided by a reported float figure, banded. That is a ratio of a count
    to a number, with no activity, no path, no allowance and no causal evidence anywhere in it.
    """
    try:
        reading = weather_day_impact(require_v4_structure(si, "A4.5"))
    except StructureAbsent as absent:
        return insufficient("Weather_Impact", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    paths = reading["path_effect_days"]
    worst = max(paths, key=lambda p: (paths[p], p))
    return calibration_pending(
        "Weather_Impact",
        f"{_js_str(reading['event_count'])} verified weather events lost "
        f"{_js_str(reading['total_lost_days'])} days. After the weather allowance and the float "
        f"on each path, the direct effect on the schedule is "
        f"{_js_str(reading['direct_path_effect_days'])} days, on the path called {worst}.",
        direct_path_effect_days=reading["direct_path_effect_days"],
        path_effect_days=paths,
        worst_path_id=worst,
        event_count=reading["event_count"],
        total_lost_days=reading["total_lost_days"],
        allowance_days_remaining_after=reading["allowance_days_remaining_after"],
        mitigation_days_reported=reading["mitigation_days_reported"],
        events=reading["events"],
        weather_calendar_id=reading["weather_calendar_id"],
        canonical_structure="weather_impact_events",
        source=reading["source"],
    )


# ------------------------------------------------------------ A4.6 Change Order Frequency


def run_co_frequency(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    Governed change events per unit of exposure time, with magnitude reported separately.

    SUPPLIED CONTRACT 4.6: ChangeFrequency = governed change events / time or another declared
    opportunity basis, six changes over one hundred and eighty days reading 0.033333... a day or
    one per standardised thirty day period. Magnitude is a separate quantity, the sum of the
    change values over the baseline contract value. Frequency and magnitude are not combined into
    one unnamed composite, and the change type, cause, direction and contract lineage are kept.

    WHAT v12 DID. It banded a raw count of change orders jointly with the percentage growth of the
    contract sum: exactly the unnamed composite the contract forbids, and with no exposure of any
    kind under the count.
    """
    try:
        reading = change_frequency(require_v4_structure(si, "A4.6"))
    except StructureAbsent as absent:
        return insufficient("CO_Frequency", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    return calibration_pending(
        "CO_Frequency",
        f"{_js_str(reading['change_count'])} governed changes over "
        f"{_js_str(reading['exposure_days'])} days, a frequency of "
        f"{_js_str(round(reading['change_frequency_per_30_days'], 3))} in a standard thirty day "
        f"period. Their net value is "
        f"{_js_str(round(reading['change_magnitude_net'] * 100, 2))} per cent of the baseline "
        f"contract, which is a separate quantity and is not combined with the frequency.",
        change_frequency_per_day=round(reading["change_frequency_per_day"], 6),
        change_frequency_per_30_days=round(reading["change_frequency_per_30_days"], 4),
        change_count=reading["change_count"],
        exposure_days=reading["exposure_days"],
        change_magnitude_net=round(reading["change_magnitude_net"], 6),
        change_magnitude_gross=round(reading["change_magnitude_gross"], 6),
        baseline_contract_value=reading["baseline_contract_value"],
        revised_contract_value=reading["revised_contract_value"],
        additive_count=reading["additive_count"],
        deductive_count=reading["deductive_count"],
        type_counts=reading["type_counts"],
        cause_counts=reading["cause_counts"],
        canonical_structure="change_event_register",
        source=reading["source"],
    )


# ------------------------------------------------------------ A4.7 Dispute Escalation Index


def run_dispute_escalation(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    The state of the project's claims on the project's own governed escalation process.

    SUPPLIED CONTRACT 4.7: a real dispute escalation signal requires actual claim or dispute state
    evidence on the project's governed process. A later governed escalation state cannot look less
    escalated because generic KPI data are missing; missing dispute evidence cannot improve the
    condition; a request count does not prove a dispute; a change order count does not prove a
    dispute; a document risk score does not prove a dispute. With no claim or dispute stage
    evidence the answer is NOT ESTIMABLE. The 0.3 / 0.3 / 0.4 generic KPI composite is not
    preserved as the canonical result.

    WHAT v12 DID. Exactly that composite: a capped request count at 0.3, a capped change order
    count at 0.3 and the document risk score at 0.4. None of the three is dispute evidence, and
    none of the three is read here.
    """
    try:
        reading = dispute_escalation(require_v4_structure(si, "A4.7"))
    except StructureAbsent as absent:
        return insufficient("Dispute_Escalation", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    return calibration_pending(
        "Dispute_Escalation",
        f"Of {_js_str(reading['issue_count'])} issues on the "
        f"{reading['process_id']} process, the furthest has reached the stage called "
        f"{reading['highest_stage_id']}, which is step "
        f"{_js_str(reading['highest_stage_rank'])} of "
        f"{_js_str(reading['stage_count'])} on that process.",
        highest_stage_id=reading["highest_stage_id"],
        highest_stage_rank=reading["highest_stage_rank"],
        escalation_position=round(reading["escalation_position"], 4),
        process_id=reading["process_id"],
        process_version=reading["process_version"],
        stage_count=reading["stage_count"],
        issue_count=reading["issue_count"],
        issues_at_highest=reading["issues_at_highest"],
        total_claim_value=reading["total_claim_value"],
        max_unresolved_age_days=reading["max_unresolved_age_days"],
        issues=reading["issues"],
        canonical_structure="claim_dispute_register",
        source=reading["source"],
    )


# ------------------------------------------------------------ A4.8 Subcontractor Performance


def run_subcontractor_performance(si: dict, rand: Callable[[], float],
                                  period_cutoff) -> dict[str, Any]:
    """
    A traceable multi-criteria subcontractor assessment.

    SUPPLIED CONTRACT 4.8: Score = sum(w_i * r_i) with sum(w_i) = 1, ratings 0.80, 0.90 and 0.70
    under equal weights scoring 0.80. All weights must be versioned and provenanced. Do not
    validate this module by consuming an opaque precomputed compliance score with no component
    evidence.

    WHAT v12 DID. It consumed exactly such a score -- a single `subcontractorComplianceScore` from
    the extraction pipeline -- and banded it, with no criteria, no ratings, no evaluator, no
    weights and no provenance behind it.
    """
    try:
        reading = subcontractor_performance(require_v4_structure(si, "A4.8"))
    except StructureAbsent as absent:
        return insufficient("Subcontractor_Performance", absent.sentence,
                            ABSTAIN_STRUCTURE_ABSENT)
    return calibration_pending(
        "Subcontractor_Performance",
        f"{_js_str(reading['subcontractor_count'])} subcontractors were assessed against "
        f"{_and_list(reading['criteria'])}. The weighted score averages "
        f"{_js_str(round(reading['mean_score'], 3))}, and the lowest is "
        f"{_js_str(round(reading['lowest_score'], 3))}, for "
        f"{reading['lowest_subcontractor']}.",
        assessments=reading["assessments"],
        subcontractor_count=reading["subcontractor_count"],
        mean_score=round(reading["mean_score"], 4),
        lowest_score=round(reading["lowest_score"], 4),
        lowest_subcontractor=reading["lowest_subcontractor"],
        critical_violations=reading["critical_violations"],
        criteria=reading["criteria"],
        weights=reading["weights"],
        weights_version=reading["weights_version"],
        canonical_structure="subcontractor_assessments",
        source=reading["source"],
    )


# ------------------------------------------------------------ A4.9 Procurement Lead Time


def run_procurement_lead_time(si: dict, rand: Callable[[], float],
                              period_cutoff) -> dict[str, Any]:
    """
    Item level procurement slack.

    SUPPLIED CONTRACT 4.9: ProcurementSlack = RequiredOnSiteDate - ForecastDeliveryDate, a
    required day of one hundred against a forecast of one hundred and ten reading minus ten days.
    Delayed items are not double counted inside at-risk, and a count ratio alone is not the
    canonical item-level monitor.

    WHAT v12 DID. A weighted count ratio over the long-lead set: half weight for at-risk items and
    full weight for delayed ones. There is no date in it, so there is no slack in it, and the
    contract's own words are that a count ratio alone is not this method.
    """
    try:
        reading = procurement_slack(require_v4_structure(si, "A4.9"))
    except StructureAbsent as absent:
        return insufficient("Procurement_Lead_Time", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    states = reading["state_counts"]
    return calibration_pending(
        "Procurement_Lead_Time",
        f"Across {_js_str(reading['item_count'])} procurement items the tightest slack is "
        f"{_js_str(reading['minimum_slack_days'])} days, on the item called "
        f"{reading['worst_item_id']}. {_js_str(states['LATE'])} items are forecast to arrive "
        f"after they are required, {_js_str(states['AT_RISK'])} arrive inside the float that "
        f"protects them and {_js_str(states['ON_TIME'])} arrive with room to spare. Every item "
        f"is counted once.",
        items=reading["items"],
        item_count=reading["item_count"],
        minimum_slack_days=reading["minimum_slack_days"],
        worst_item_id=reading["worst_item_id"],
        mean_slack_days=round(reading["mean_slack_days"], 2),
        state_counts=states,
        canonical_structure="procurement_items",
        source=reading["source"],
    )


# ------------------------------------------------------------ A4.10 Spec Conflict Density


def run_spec_conflict_density(si: dict, rand: Callable[[], float],
                              period_cutoff) -> dict[str, Any]:
    """
    Verified specification conflicts per unit of declared specification exposure.

    SUPPLIED CONTRACT 4.10: ConflictDensity = VerifiedConflictCandidates / ExposureUnit, five
    verified conflicts over two hundred and fifty requirements reading 0.02 conflicts a
    requirement, or twenty per thousand. Exposure must be explicit, each conflict must retain the
    conflicting evidence locations, and `docRiskScore * sqrt(RFI count)` is not conflict density.
    With no numerator or denominator the answer is NOT ESTIMABLE.

    WHAT v12 DID. `docRiskScore * rfiCount / sqrt(rfiCount)`, capped at one and banded: the
    expression the contract names as not being this method. Neither field is read here.
    """
    try:
        reading = specification_conflict_density(require_v4_structure(si, "A4.10"))
    except StructureAbsent as absent:
        return insufficient("Spec_Conflict_Density", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    return calibration_pending(
        "Spec_Conflict_Density",
        f"{_js_str(reading['verified_conflicts'])} confirmed conflicts across "
        f"{_js_str(reading['exposure_quantity'])} {reading['exposure_unit']}, a density of "
        f"{_js_str(round(reading['conflicts_per_thousand'], 3))} for every thousand. "
        f"{_js_str(reading['candidate_conflicts'])} further candidates are recorded and are not "
        f"counted in the density.",
        conflict_density=round(reading["conflict_density"], 6),
        conflicts_per_thousand=round(reading["conflicts_per_thousand"], 4),
        verified_conflicts=reading["verified_conflicts"],
        candidate_conflicts=reading["candidate_conflicts"],
        exposure_unit=reading["exposure_unit"],
        exposure_quantity=reading["exposure_quantity"],
        conflicts=reading["conflicts"],
        specification_document_id=reading["specification_document_id"],
        specification_revision=reading["specification_revision"],
        detection_precision_recall=reading["detection_precision_recall"],
        canonical_structure="specification_conflict_register",
        source=reading["source"],
    )


# ------------------------------------------------------------ A5.2 Sensitivity Analysis


def run_sensitivity_analysis(si: dict, rand: Callable[[], float],
                             period_cutoff) -> dict[str, Any]:
    """
    A declared response recomputed with each declared input moved.

    SUPPLIED CONTRACT 5.2: use an explicit response Y, input Xi, base point and perturbation, with
    S_i = (dY/Y) / (dXi/Xi). With Y = x1^2 + x2 at x1 = 2, x2 = 1 the response is 5; raising x1 by
    ten per cent gives 5.84, so the normalised sensitivity is (0.84/5)/(0.2/2) = 1.68. Ranking
    currently bad variables is not sensitivity. The model must perturb the input and recompute the
    response. A one-at-a-time local method is acceptable if declared as such and not called
    global.

    WHAT v12 DID. It perturbed the cost performance index by 0.05 either way and recomputed
    `bac / cpi` -- a genuine elasticity of one hard-coded response to one hard-coded input -- and
    reported the schedule index's distance from one and the document risk score itself beside it
    as levels. There was no declared response function, no declared base state, no declared range
    and no way for a project to name the inputs it wanted moved.
    """
    try:
        reading = sensitivity_analysis(require_v4_structure(si, "A5.2"))
    except StructureAbsent as absent:
        return insufficient("Sensitivity_Analysis", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    top = max(reading["inputs"], key=lambda r: (abs(r["normalised_sensitivity"]), r["input_id"]))
    return calibration_pending(
        "Sensitivity_Analysis",
        f"The response called {reading['response_model_id']} reads "
        f"{_js_str(round(reading['base_response'], 4))} at the state declared for it. Moving "
        f"{top['input_id']} by "
        f"{_js_str(round(top['perturbation_fraction'] * 100, 2))} per cent and recomputing the "
        f"response moves it by {_js_str(round(top['delta_response'], 4))}, a normalised "
        f"sensitivity of {_js_str(round(top['normalised_sensitivity'], 4))}. This is a local one "
        f"at a time sensitivity and is not a global one.",
        method=reading["method"],
        method_scope=reading["method_scope"],
        response_model_id=reading["response_model_id"],
        response_model_version=reading["response_model_version"],
        base_state=reading["base_state"],
        base_response=reading["base_response"],
        inputs=reading["inputs"],
        input_count=reading["input_count"],
        top_input=top["input_id"],
        top_normalised_sensitivity=round(top["normalised_sensitivity"], 6),
        canonical_structure="sensitivity_model",
        source=reading["source"],
    )


# ------------------------------------------------------------ A5.3 Tornado Risk Ranking


def run_tornado_diagram(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    The ranking layer over the sensitivity results, and NOT a second evidence body.

    SUPPLIED CONTRACT 5.3 AND THE RUN-29 PARSIMONY DECISION: Impact_i = Y_i(high) - Y_i(low),
    ranked descending by absolute impact, with impacts of 30, 7 and 30 placing A and C tied above
    B and an explicit tie policy. 5.3 ordinarily consumes the 5.2 sensitivity outputs and does not
    recompute an independent duplicate evidence stream; its lineage must show derivation from the
    sensitivity results.

    HOW THAT IS ENFORCED RATHER THAN ASSERTED. This runner calls `sensitivity_analysis` on the
    SAME structure A5.2 reads, then hands the RESULT to `tornado_ranking`, which takes no other
    argument and therefore cannot reach the structure, the response model or the signal inputs.
    The two modules cannot disagree about the evidence because there is only one computation of
    it, and the result carries `derived_from` so a reader can see that.

    WHAT v12 DID. It ranked four present-state deviations -- the distance of each index from one,
    the document risk score and the progress variance -- and banded their mean. Not one of the
    four was a swing in any output, nothing was recomputed at any range, and none of it came from
    the sensitivity module.
    """
    try:
        structure = require_v4_structure(si, "A5.3")
        sensitivity = sensitivity_analysis(structure)
        reading = tornado_ranking(sensitivity)
    except StructureAbsent as absent:
        return insufficient("Tornado_Diagram", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    if not reading["bars"]:
        return insufficient(
            "Tornado_Diagram",
            "The sensitivity computed for this project moved no inputs, so there are no swings "
            "for this ranking to present.",
            ABSTAIN_STRUCTURE_ABSENT)
    return calibration_pending(
        "Tornado_Diagram",
        f"Across {_js_str(len(reading['bars']))} inputs moved through the response called "
        f"{reading['derived_from_response_model_id']}, the widest swing belongs to "
        f"{reading['top_input']}, at {_js_str(round(reading['top_impact'], 4))}. These swings are "
        f"the ones the sensitivity analysis computed; this ranking presents them and computes "
        f"nothing of its own.",
        bars=reading["bars"],
        ranked_inputs=reading["ranked_inputs"],
        top_input=reading["top_input"],
        top_impact=round(reading["top_impact"], 6),
        distinct_ranks=reading["distinct_ranks"],
        tie_policy=reading["tie_policy"],
        tied_impacts=reading["tied_impacts"],
        derived_from=reading["derived_from"],
        derived_from_response_model_id=reading["derived_from_response_model_id"],
        derived_from_response_model_version=reading["derived_from_response_model_version"],
        derived_from_base_response=reading["derived_from_base_response"],
        independent_evidence=reading["independent_evidence"],
        canonical_structure="sensitivity_model",
    )


# ------------------------------------------------------------ A5.4 Scenario Modeling


def run_scenario_modeling(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    Named coherent multi-variable states evaluated through one governed response model.

    SUPPLIED CONTRACT 5.4: a scenario is a coherent multi-variable state; X(s) = {x1(s), ...,
    xp(s)} and Y(s) = f(X(s)), with a scenario id and version, a rationale, the jointly changed
    inputs, consistency constraints, a governed response model and outputs. With Y = 2*x1 + x2 the
    three states BASE (2, 1), ADVERSE (3, 2) and RECOVERY (1.5, 1) give 5, 8 and 4 exactly. This
    is not Category 10: the question is what happens under this condition, not which intervention
    to choose.

    WHAT v12 DID. It read an actions-by-scenarios payoff matrix and returned a recommended action
    and its expected cost. That is a decision method -- Category 10's question -- and the contract
    for this module says in its own words not to confuse the two. The decision structure is no
    longer this module's defining structure and the recommendation is no longer this module's
    output.
    """
    try:
        reading = scenario_modeling(require_v4_structure(si, "A5.4"))
    except StructureAbsent as absent:
        return insufficient("Scenario_Modeling", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    return calibration_pending(
        "Scenario_Modeling",
        f"{_js_str(reading['scenario_count'])} coherent states were evaluated through the "
        f"response called {reading['response_model_id']}. The response runs from "
        f"{_js_str(round(reading['minimum_response'], 4))} to "
        f"{_js_str(round(reading['maximum_response'], 4))} across them. No state is recommended "
        f"over any other, because choosing between them is a different question.",
        scenarios=reading["scenarios"],
        scenario_count=reading["scenario_count"],
        responses=reading["responses"],
        minimum_response=reading["minimum_response"],
        maximum_response=reading["maximum_response"],
        response_model_id=reading["response_model_id"],
        response_model_version=reading["response_model_version"],
        constraints=reading["constraints"],
        scenario_set_version=reading["scenario_set_version"],
        canonical_structure="scenario_set",
        source=reading["source"],
    )


# ------------------------------------------------------------ A5.5 Rework Feedback Loop


def run_rework_feedback(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    A genuine time-dependent stock and flow rework model.

    SUPPLIED CONTRACT 5.5:
        Backlog(t+1) = Backlog(t) + NewWork(t) + ReworkGenerated(t) - WorkCompleted(t)
        ReworkGenerated(t) = ErrorRate(t) * WorkCompleted(t)
    with Backlog0 = 10, NewWork = 5, WorkCompleted = 8 and ErrorRate = 0.25 giving
    ReworkGenerated = 2 and Backlog1 = 9. A weighted CPI/RFI/change-order score is not a feedback
    loop, and with no stock and flow model the answer is NOT ESTIMABLE.

    WHAT v12 DID. Precisely that weighted score: a capped request count at 0.3, a capped change
    order count at 0.3 and the shortfall of the cost index at 0.4. It has no stock, no flow, no
    time and no feedback, and none of its three inputs is read here.
    """
    try:
        reading = rework_feedback_loop(require_v4_structure(si, "A5.5"))
    except StructureAbsent as absent:
        return insufficient("Rework_Feedback", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    return calibration_pending(
        "Rework_Feedback",
        f"Over {_js_str(reading['steps_run'])} steps the backlog moves from "
        f"{_js_str(reading['initial_backlog'])} to {_js_str(reading['final_backlog'])}. "
        f"{_js_str(round(reading['total_rework_generated'], 3))} of the "
        f"{_js_str(reading['total_work_completed'])} completed came back as rework and returned "
        f"to the backlog.",
        time_step=reading["time_step"],
        initial_backlog=reading["initial_backlog"],
        final_backlog=reading["final_backlog"],
        steps_run=reading["steps_run"],
        trace=reading["trace"],
        total_new_work=reading["total_new_work"],
        total_work_completed=reading["total_work_completed"],
        total_rework_generated=reading["total_rework_generated"],
        rework_share_of_completed=(round(reading["rework_share_of_completed"], 4)
                                   if reading["rework_share_of_completed"] is not None else None),
        accounting_residual=reading["accounting_residual"],
        model_version=reading["model_version"],
        canonical_structure="system_dynamics_model",
        source=reading["source"],
    )


# ------------------------------------------------------------ A5.6 Queueing Theory Bottleneck


def run_queueing_bottleneck(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    A genuine queue model: arrival rate, service rate, servers and discipline.

    SUPPLIED CONTRACT 5.6: rho = lambda / mu, L = rho/(1-rho), W = 1/(mu-lambda),
    Lq = rho^2/(1-rho), Wq = rho/(mu-lambda). With lambda = 2 and mu = 3 that is rho = 2/3, L = 2,
    W = 1, Lq = 4/3 and Wq = 2/3, and Little's Law holds. If lambda >= mu, do not emit a
    reassuring steady-state result. ActivitiesConstrained / ActivitiesPlanned is not queueing
    theory.

    WHAT v12 DID. It read a queue OBSERVATION log -- entities, a horizon and a list of measured
    waiting times -- and reported the share of server time that was occupied. That is a measured
    occupancy, not a queueing model: there is no arrival process, no service process and no
    stability condition in it, and the waiting times were read out of the log rather than derived.
    An unstable queue was banded Red; it is now refused, because there is no steady state to
    report and a colour would imply there is.
    """
    try:
        reading = queue_model(require_v4_structure(si, "A5.6"))
    except StructureAbsent as absent:
        return insufficient("Queueing_Bottleneck", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    worst = reading["bottleneck"]
    return calibration_pending(
        "Queueing_Bottleneck",
        f"The busiest queue is {worst['queue_id']}, where work arrives at "
        f"{_js_str(worst['arrival_rate'])} a day against a service rate of "
        f"{_js_str(worst['service_rate'])} a day across "
        f"{_js_str(worst['servers'])} servers. It runs at "
        f"{_js_str(round(worst['utilisation'], 4))} of capacity, holds "
        f"{_js_str(round(worst['L'], 4))} items on average and takes "
        f"{_js_str(round(worst['W'], 4))} days to pass through.",
        utilisation=round(worst["utilisation"], 6),
        arrival_rate=worst["arrival_rate"],
        service_rate=worst["service_rate"],
        servers=worst["servers"],
        discipline=worst["discipline"],
        L=round(worst["L"], 6),
        W=round(worst["W"], 6),
        Lq=round(worst["Lq"], 6),
        Wq=round(worst["Wq"], 6),
        bottleneck_queue_id=worst["queue_id"],
        queues=reading["queues"],
        queues_observed=reading["queue_count"],
        stability=reading["stability"],
        model=reading["model"],
        model_version=reading["model_version"],
        canonical_structure="queue_model",
        source=reading["source"],
    )


# ------------------------------------------------------------ A5.7 Agent-Based Supply Chain


def run_agent_supply_chain(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    Agents, states, behaviour rules, interaction rules, an environment and time, actually stepped.

    SUPPLIED CONTRACT 5.7: a true agent-based model requires all six. The minimum deterministic
    laboratory model is a supplier that ships one unit when it has stock and a request is pending,
    a carrier that collects a shipped unit and delivers it after a declared travel delay, and a
    project with demand, received quantity and backorder. A long-lead at-risk ratio is not an
    agent-based model, and with no agent or rule structure the answer is NOT ESTIMABLE.

    WHAT v12 DID. It read a supplied state history and counted how many agents were in a state
    other than normal at the last time step. The decision rules were required to be NAMED but were
    never EXECUTED: nothing in the module made an agent do anything, so the states came out
    exactly as they were typed in. That is a table read, not a simulation, and it is replaced.
    """
    try:
        reading = agent_supply_chain(require_v4_structure(si, "A5.7"))
    except StructureAbsent as absent:
        return insufficient("Agent_Supply_Chain", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    return calibration_pending(
        "Agent_Supply_Chain",
        f"Over {_js_str(reading['time_steps'])} steps, "
        f"{_js_str(reading['agent_count'])} agents following "
        f"{_js_str(len(reading['rules']))} rules delivered "
        f"{_js_str(reading['received'])} of the {_js_str(reading['demand'])} units the project "
        f"asked for, leaving {_js_str(reading['backordered'])} outstanding."
        + (f" The run is stochastic and was repeated {_js_str(reading['replications'])} times "
           f"from seed {_js_str(reading['seed'])}." if reading["stochastic"] else ""),
        agents=reading["agents"],
        agent_count=reading["agent_count"],
        agent_types=reading["agent_types"],
        rules=reading["rules"],
        environment=reading["environment"],
        time_steps=reading["time_steps"],
        travel_delay_steps=reading["travel_delay_steps"],
        step_order=reading["step_order"],
        stochastic=reading["stochastic"],
        seed=reading["seed"],
        replications=reading["replications"],
        runs=reading["runs"],
        received=reading["received"],
        backordered=reading["backordered"],
        demand=reading["demand"],
        model_version=reading["model_version"],
        empirical_calibration=reading["empirical_calibration"],
        canonical_structure="agent_supply_chain_model",
        source=reading["source"],
    )


# ------------------------------------------------------------ A5.8 Discrete Event Simulation


def run_discrete_event_sim(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    A real discrete event simulation: entities, events, a clock, resources, queues and routing.

    SUPPLIED CONTRACT 5.8: with one server, job A arriving at 0 with a service of 2 and job B
    arriving at 1 with a service of 2, A starts at 0 and ends at 2 having waited 0, B starts at 2
    and ends at 4 having waited 1, and the mean wait is 0.5. A progress or schedule index
    algebraic index is not DES, and with no event, resource or queue structure the answer is NOT
    ESTIMABLE.

    WHAT v12 DID. It formed an interruption term from the progress shortfall and the schedule
    index shortfall and reported the reciprocal of one plus it as a throughput index. Run 27
    proved it a function of the schedule index and the progress ratio alone. There is no entity,
    no event, no clock, no resource and no queue in it, and none of its inputs is read here.
    """
    try:
        reading = des_process_model(require_v4_structure(si, "A5.8"))
    except StructureAbsent as absent:
        return insufficient("Discrete_Event_Sim", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    return calibration_pending(
        "Discrete_Event_Sim",
        f"{_js_str(reading['entity_count'])} entities were run through "
        f"{_js_str(reading['capacity'])} servers of the resource called "
        f"{reading['resource_id']}, taking their turn in "
        f"{reading['queue_discipline']} order. The average wait before service is "
        f"{_js_str(round(reading['mean_wait'], 4))} and the clock finishes at "
        f"{_js_str(round(reading['clock_end'], 4))}."
        + (f" The run is stochastic and was repeated {_js_str(reading['replications'])} times "
           f"from seed {_js_str(reading['seed'])}." if reading["stochastic"] else ""),
        resource_id=reading["resource_id"],
        capacity=reading["capacity"],
        queue_discipline=reading["queue_discipline"],
        event_order_policy=reading["event_order_policy"],
        termination_condition=reading["termination_condition"],
        entity_count=reading["entity_count"],
        stochastic=reading["stochastic"],
        seed=reading["seed"],
        replications=reading["replications"],
        runs=reading["runs"],
        mean_wait=reading["mean_wait"],
        entities=reading["entities"],
        events=reading["events"],
        clock_end=reading["clock_end"],
        model_version=reading["model_version"],
        canonical_structure="des_process_model",
        source=reading["source"],
    )


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
    # RUN 10, BUCKET 2. The fifteen-defects run guarded the inspected and failed pair and left
    # the audited score itself ungoverned. A score of one hundred and forty, or of minus ten,
    # went straight into the band ladder and out again as a quality figure out of a hundred.
    if audit is not None:
        audit_v = num(audit, None)
        if audit_v is None or audit_v < 0 or audit_v > 100:
            return insufficient(
                "Quality_Compliance",
                "The audited quality score falls outside the range a score out of a hundred can "
                "occupy, so it is not a quality figure",
                ABSTAIN_MALFORMED_INPUT)
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
    # RUN 10, BUCKET 2. Absence of evidence was producing the best safety reading in the module.
    # `safetyIncidentsDiscussed` is DERIVED from how many times safety came up in meeting
    # records when no safety report was uploaded. A meeting that never mentioned safety derived
    # a count of nought, that count became a rate of nought, the rate of nought took the module's
    # own cap of two, and the project read Green with the best safety index the module can
    # produce. Nothing had measured safety on that project at all.
    #
    # Four dispositions are now distinguished rather than collapsed:
    #   - a rate or an incident count read from an uploaded safety record, including a recorded
    #     zero over a valid exposure: a measurement, and it bands;
    #   - a derived count of nought, which is meeting SILENCE: not a measurement, and it abstains;
    #   - no safety field at all: missing evidence, and it abstains, as it already did;
    #   - a negative rate: malformed, and it abstains, as it already did.
    #
    # RUN 20, P0B. The zero case above was closed by Run 10 and the NON-ZERO case was left open,
    # which is where the remaining defect lived. Two mentions of safety in meeting minutes were
    # multiplied by ten into an incident rate of 20.0 and the project banded Red on it. That
    # multiplier has no source anywhere, and specification 8.7 forbids using incidents discussed
    # in meeting minutes as an OSHA incidence-rate substitute in those exact terms. Disclosing in
    # the sentence that the figure was estimated did not make the fabricated rate any less of a
    # rate once it reached the band.
    #
    # So the derived count no longer becomes a rate in EITHER direction. Meeting minutes are a
    # record of what was discussed; the OSHA incidence rate is recordable cases times two hundred
    # thousand over employee hours worked, and neither term of that identity is present in a set
    # of minutes. With no uploaded rate the module abstains and says which document would carry
    # one. An uploaded rate, including a recorded zero, is unaffected and still bands.
    if is_derived and si.get("oshaIncidentRate") is None:
        if not si["safetyIncidentsDiscussed"] > 0:
            return insufficient(
                "Safety_Performance",
                "No safety record has been uploaded for this project and the meeting records do "
                "not mention safety. Silence in a meeting is not a measurement of safety "
                "performance, and it is not reported here as a record of no incidents.",
                ABSTAIN_MISSING_INPUT)
        return insufficient(
            "Safety_Performance",
            "Safety was raised in the meeting records but no safety report has been uploaded. "
            "How often a subject is discussed is not an incident rate, and no rate is estimated "
            "from it here. Upload a Safety Report to report an incidence rate.",
            ABSTAIN_MISSING_INPUT)
    # RUN 20, P0B, ROOT CAUSE. The multiplication by ten is removed outright rather than fenced
    # off in the derived case only. A count of times safety was mentioned is not a rate whatever
    # document it was counted in, the multiplier has no source in the specification or anywhere
    # else, and the OSHA identity needs an exposure denominator this module does not carry. Only
    # a reported incidence rate produces a rate now.
    if si.get("oshaIncidentRate") is None:
        return insufficient(
            "Safety_Performance",
            "Safety incidents have been recorded for this project but no incidence rate has "
            "been reported. A count of incidents is not a rate without the hours worked behind "
            "it, and none is estimated here. Upload a Safety Report carrying the OSHA incidence "
            "rate.",
            ABSTAIN_MISSING_INPUT)
    rate = si.get("oshaIncidentRate")
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
    # RUN 10B. The canonical structure is audited permit condition compliance, which the
    # fifteen-defects run already required, so what this module computes does not change. Added
    # here is the structured form of the same audit: where the assessed permit conditions arrive
    # as records rather than as one extracted percentage, the rate is formed as the share of
    # applicable conditions assessed compliant, which is the definition the extracted figure
    # carries. With neither form present the module abstains exactly as it did before.
    audit = si.get("auditedPermitCompliance")
    if isinstance(audit, dict):
        si = dict(si)
        assessments = audit.get("assessments")
        if not isinstance(assessments, list) or not assessments:
            return insufficient(
                "Environmental_Compliance",
                "Awaiting audited permit compliance data: the record provided carries no "
                "assessed permit condition for this period.",
                ABSTAIN_STRUCTURE_ABSENT)
        compliant = sum(1 for a in assessments
                        if str(a.get("result") or "").upper() == "COMPLIANT")
        si["environmentalComplianceRate"] = compliant / len(assessments) * 100.0
        si.setdefault("environmentalIssuesDiscussed", 0)
        si.setdefault("environmentalViolations", audit.get("violations") or 0)
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
    # RUN 10, BUCKET 2. The rating scale was ungoverned. An out-of-scale HIGH rating cannot lower
    # the minimum and so was harmless; an out-of-scale LOW one sets it, and a rating of minus two
    # on a five-point evaluation drove the band to Red on a figure that is not a rating.
    for name, v in (("overall", overall), ("schedule", sched), ("cost", cost),
                    ("quality", quality)):
        if v is not None and (v < 0 or v > 5):
            return insufficient(
                "Contractor_Performance",
                "A performance rating falls outside the five-point scale the evaluation uses, "
                "so it is not a rating this score can be taken from",
                ABSTAIN_MALFORMED_INPUT)
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
