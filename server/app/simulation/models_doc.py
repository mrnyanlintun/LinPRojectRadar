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

from datetime import date as _date
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
    subcontractor_reported_ratings,
    submittal_rejection,
    tornado_ranking,
    weather_day_impact,
)
from . import band_reference as _BR
from . import owner_bands as _OB
from . import pm_review as _PMR
from .models import (
    ABSTAIN_MALFORMED_INPUT, ABSTAIN_MISSING_INPUT, ABSTAIN_STRUCTURE_ABSENT,
    PROVENANCE_CODIFIED, PROVENANCE_CONVENTION, PROVENANCE_OWNER_CALIBRATED,
    THRESHOLD_SOURCE_OWNER, THRESHOLD_SOURCE_PROJECT,
    band_abstained, banded, calibration_pending, check_inputs, insufficient, refuse,
)
from .models_ext import _derived, _js_str
from .rng import js_round, num, round1, round2

_RANK = {"Green": 0, "Yellow": 1, "Amber": 2, "Red": 3}


def _module_review(si: dict, module_id: str) -> dict | None:
    """
    RUN 107. The Project Manager's recorded review of THIS module's reading, if one is on record.

    IT IS READ FROM THE SIGNAL INPUTS, not from the database, because a module reads `si` and
    nothing else -- that is the boundary the whole layer is built on. `documents.run_and_store`
    merges the recorded reviews onto `si` under `moduleReviews` before computation, from the
    append-only `audit_events` table, which is where every participant decision this platform
    holds already lives. Nothing here writes, and a module never records a review.
    """
    reviews = si.get("moduleReviews")
    if not isinstance(reviews, dict):
        return None
    entry = reviews.get(module_id)
    return entry if isinstance(entry, dict) else None


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


# ================================ RUN 101, A4.2: THE BAND IS ON OVERDUE, AGAINST THE CONTRACT
#
# THE OWNER'S RULING, SECTION 4. The module reported RFIs issued per week and banded on it. THE
# PUBLISHED PER-MILLION-DOLLAR BENCHMARK MEASURES A DIFFERENT QUANTITY -- requests per million
# dollars of contract value, not requests per week -- and does not apply. The old per-week ladder
# at 2, 4 and 8, which this file's own comment recorded as sourced to nothing, IS REMOVED. The
# weekly rate and the open count are CONTEXT. THE OVERDUE COUNT IS WHAT BANDS.
#
# THE THRESHOLD IS THE CONTRACT'S OWN RESPONSE PERIOD: seven business days. An RFI unanswered
# beyond it is overdue BY THE CONTRACT'S DEFINITION, so the basis is the contract, not an
# industry average. Where a project's contract states a different period, that figure governs and
# its source is the document.
#
# BUSINESS DAYS, AND WHERE THAT REQUIREMENT LIVES. Section 12.1a fails this run for computing
# overdue in CALENDAR days. THE PLATFORM DOES NO DATE ARITHMETIC HERE AT ALL: `rfiOverdue` and
# the register's own overdue flags arrive as figures the DOCUMENT states
# (`extraction_merge._NUMERIC_EMISSIONS["rfi_log"]` maps `rfi_overdue` straight through), and no
# code path in this repository derives an overdue count from RFI dates. So the business-day
# requirement is a requirement on THE DOCUMENT'S AUTHOR, it is stated in the extraction contract
# and in the specification, and it is restated on every reading this module produces -- because a
# requirement nobody can see is a requirement nobody meets. A calendar-day count marks every RFI
# overdue two days early, and this module says so on its own row rather than silently accepting
# whichever the document did.
#
# THE FOUR BOUNDARIES ARE OWNER-CALIBRATED AND ARE NOT THE CONTRACT'S. The seven-day period IS
# contractual; how many breaches of it constitute Yellow rather than Amber is not stated in any
# contract or publication found. The reasoning, recorded so it can be argued with: GREEN IS
# RESERVED FOR ZERO because the response period is a contractual term rather than an aspiration,
# and a project meeting its own contract has nothing overdue; the two upper boundaries divide
# what remains at a tenth and a quarter of the open log, because one late answer on a large log
# is a lapse and a quarter of the log unanswered past its contractual term is a breakdown of the
# information flow the schedule depends on. No publication supports 0.10 or 0.25.
_RFI_OVERDUE_BOUNDARY = (
    "on the proportion of OPEN requests that are overdue against the contract's own response "
    "period: exactly zero overdue is Green; above zero and at or below 0.10 is Yellow; above "
    "0.10 and at or below 0.25 is Amber; above 0.25 is Red. Zero is a value here and is not "
    "treated as missing. The weekly issue rate and the open count are context and are not what "
    "the band is drawn from")


def _rfi_response_period(si: dict) -> tuple:
    """(period in business days, its source). The project's contract wins; else the configured
    default, which says on its face that it stands in for a contract nobody has read."""
    stated = si.get("rfiResponsePeriodBusinessDays")
    if isinstance(stated, (int, float)) and stated > 0:
        return (stated, "this project's own contract, as its uploaded documents state it")
    return (_BR.configured_value("rfi_contract_response_period_business_days"),
            _BR.source_of("rfi_contract_response_period_business_days"))


def _rfi_band(overdue, open_count, si: dict) -> tuple:
    """The band on overdue, or a reason. Reads no dates and computes no elapsed time.

    RUN 102, SECTION 6. THE PRECEDENCE ORDER IS GENUINELY EXERCISED HERE and is not a label:
    when the project's own uploaded contract states its response period the threshold source is
    `project_specific` -- rung 1 -- and when it does not, the configured stand-in is the owner's
    default -- rung 3. The sixth element of the returned tuple carries that.
    """
    period, source = _rfi_response_period(si)
    _tsrc = (THRESHOLD_SOURCE_PROJECT
             if isinstance(si.get("rfiResponsePeriodBusinessDays"), (int, float))
             and si.get("rfiResponsePeriodBusinessDays") > 0
             else THRESHOLD_SOURCE_OWNER)
    basis = (
        f"the contract's own response period of {period} business days -- an RFI unanswered "
        f"beyond it is overdue by the contract's definition, so the basis is the contract and "
        f"not an industry average. Source: {source}. THE FOUR BOUNDARIES DRAWN FROM IT ARE NOT "
        f"CONTRACTUAL and have no published basis; they are the owner's stated thresholds "
        f"(Run 101, section 4). OVERDUE MUST BE COUNTED IN BUSINESS DAYS, EXCLUDING WEEKENDS AND "
        f"HOLIDAYS: this platform performs no date arithmetic on requests for information and "
        f"takes the overdue count as the source document states it, so that requirement falls on "
        f"the document's author and is stated in the extraction contract. A calendar-day count "
        f"marks every request overdue two days early. CORROBORATION RECORDED, NOT USED AS THE "
        f"SOURCE: Aboseif et al. (2023), Journal of Management in Engineering, derived from "
        f"Construction Industry Institute data by cross-validated CART models at 81 to 85 per "
        f"cent accuracy, gives a high-performing RFI processing time of seven days or fewer. "
        f"That corroborates the period from an empirical direction; THE CONTRACT REMAINS THE "
        f"SOURCE. The same paper's requests-per-million-dollars figure measures a DIFFERENT "
        f"QUANTITY and is applied nowhere")
    # THE BASIS AND THE BOUNDARIES HAVE DIFFERENT PROVENANCE, and the order says so itself:
    # "the 7-day period is contractual, the boundaries drawn from it are not". The response
    # period is a term of a governing instrument -- CODIFIED; the four cutoffs are the owner's
    # with no published basis -- OWNER-CALIBRATED.
    if not isinstance(overdue, (int, float)):
        return (None, None,
                "the request log states no overdue count, so the quantity this module bands on "
                "is not reported for this project. The issue rate and the open count are "
                "displayed and no band is drawn from them: the published per-million-dollar "
                "benchmark measures requests against contract value, which is a different "
                "quantity, and it is not applied here", None, None, None)
    if not isinstance(open_count, (int, float)) or open_count <= 0:
        if overdue > 0:
            return ("Red", _RFI_OVERDUE_BOUNDARY, basis, PROVENANCE_CODIFIED,
                PROVENANCE_OWNER_CALIBRATED, _tsrc)
        return (None, None,
                "the request log reports no open requests, so an overdue proportion has no "
                "denominator. With nothing open there is nothing that can be overdue, and that "
                "is reported rather than banded as though it were compliance", None, None,
                None)
    ratio = overdue / open_count
    colour = ("Green" if ratio == 0 else "Yellow" if ratio <= 0.10
              else "Amber" if ratio <= 0.25 else "Red")
    return (colour, _RFI_OVERDUE_BOUNDARY, basis, PROVENANCE_CODIFIED,
            PROVENANCE_OWNER_CALIBRATED, _tsrc)


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
        ratio = reading["overdue_ratio"]
        _colour, _boundary, _basis, _prov, _bprov, _tsrc = _rfi_band(
            reading["overdue"], reading["open_relevant"], si)
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
        _figs = dict(
            rfi_per_30d=round1(reading["rate_per_30_days"]),
            rfi_per_week=round1(per_week),
            rate_per_day=round2(reading["rate_per_day"]),
            total_rfis=reading["events_counted"],
            period_days=reading["exposure_days"],
            rows_supplied=reading["rows_supplied"],
            duplicate_rows_collapsed=reading["duplicate_rows_collapsed"],
            open_rfis=reading["open_relevant"],
            overdue_rfis=reading["overdue"],
            overdue_ratio=(round(ratio, 3) if ratio is not None else None),
            canonical_structure="rfi_event_log",
            register_id=reading["register_id"],
            source=reading["source"],
            rfi_response_period_business_days=_rfi_response_period(si)[0],
            overdue_counting_basis=(
                "business days, excluding weekends and holidays, as the source document must "
                "state it; this platform performs no date arithmetic on requests for information"),
        )
        if _colour is None:
            return band_abstained("RFI_Velocity", evidence, reason=_basis, **_figs)
        return banded("RFI_Velocity", evidence, status_color=_colour, boundary=_boundary,
                      basis=_basis, provenance=_prov, boundary_provenance=_bprov,
                      threshold_source=_tsrc, **_figs)
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
    # RUN 101. THE PER-WEEK LADDER AT 2, 4 AND 8 IS GONE, and the comment that used to stand
    # here is why: Run 4 looked for a source specifying it and found none. The owner's Run 101
    # order settles it -- the weekly rate is CONTEXT and the OVERDUE COUNT is what bands, against
    # the contract's own response period. The overdue proportion is formed over the OPEN count
    # where the log states one, because an overdue request is by definition still open; where the
    # log states no open count the total is not substituted for it, and the module says so.
    _open = si.get("rfiOpen")
    overdue_ratio = None
    if si.get("rfiOverdue") is not None and isinstance(_open, (int, float)) and _open > 0:
        overdue_ratio = si["rfiOverdue"] / _open
    _colour, _boundary, _basis, _prov, _bprov, _tsrc = _rfi_band(
        si.get("rfiOverdue"), _open, si)
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
    _figs = dict(
        rfi_per_30d=per30,
        rfi_per_week=per_week,
        total_rfis=count,
        period_days=days,
        open_rfis=_open if _open is not None else None,
        overdue_rfis=si.get("rfiOverdue") if si.get("rfiOverdue") is not None else None,
        overdue_ratio=(js_round(overdue_ratio * 1000) / 1000
                       if overdue_ratio is not None else None),
        response_time_days=avg_response if avg_response is not None else None,
        canonical_structure="extracted_register_totals",
        rfi_response_period_business_days=_rfi_response_period(si)[0],
        overdue_counting_basis=(
            "business days, excluding weekends and holidays, as the source document must state "
            "it; this platform performs no date arithmetic on requests for information"),
    )
    if _colour is None:
        return band_abstained("RFI_Velocity", evidence, reason=_basis, **_figs)
    return banded("RFI_Velocity", evidence, status_color=_colour, boundary=_boundary,
                  basis=_basis, provenance=_prov, boundary_provenance=_bprov,
                  threshold_source=_tsrc, **_figs)



# =================================================================================================
# RUN 106, GOAL THREE. THE OWNER'S TWO CONSTRUCTION DOCUMENT-CONTROL AND QUALITY-CONTROL BANDS.
#
# Both are OWNER-CALIBRATED and neither is presented as a construction standard. The owner's
# order states in terms that the informally reported 30-40 per cent first-submission rejection
# figure is DESCRIPTIVE, NOT NORMATIVE, and is not to be cited as the source; it is recorded in
# `band_reference_data.json` as a non-source for exactly that reason.
#
# THEY MEASURE DIFFERENT THINGS FROM A6.1 QUALITY COMPLIANCE, and the specifications say so.
# Quality Compliance measures first-pass INSPECTION acceptance and sits in Delivery Quality. A
# project can inspect well and submit badly, and the two must not be read as one another.
#
# A ZERO DENOMINATOR IS NOT ASSESSED. Never a division by zero, and never a raw count banded as
# though it were a rate.
#
# THE OVERRIDES ARE RED REGARDLESS OF RATE, AND WHERE THE DOCUMENT DOES NOT CARRY THE FIELDS TO
# EVALUATE THEM THE ROW SAYS SO. A high inspection count must not dilute an open critical NCR;
# the override takes precedence over the rate, and a rate-derived band that could not be tested
# against the overrides is published carrying `band_overrides_evaluated: False` and a sentence
# naming which fields were absent. That is a disclosure, not a threshold.
# =================================================================================================

#: The owner's Run 106 first-review submittal rejection ladder, in PER CENT, worst cut first.
#: Each cut is read as "at or above this figure", and the Green arm is the open bottom.
SUBMITTAL_REJECTION_CUTS: tuple[tuple[float, str], ...] = (
    (35.0, "Red"), (20.0, "Amber"), (10.0, "Yellow"))

SUBMITTAL_REJECTION_BOUNDARY = (
    "on the FIRST-REVIEW rejection rate -- submittals rejected or returned for revision on first "
    "review, divided by submittals receiving a first review, as a percentage. Later resubmittal "
    "outcomes are NOT in the denominator: this measures first-pass document quality, not eventual "
    "cycles. Below 10 per cent is Green; at or above 10 and below 20 is Yellow; at or above 20 "
    "and below 35 is Amber; at or above 35 is Red. Each boundary is INCLUSIVE ON ITS LOWER SIDE. "
    "RED REGARDLESS OF RATE where any of three conditions holds: a rejected critical-path or "
    "long-lead submittal whose forecast approval falls after its need-by date; a rejected "
    "submittal unresolved beyond the project-defined review deadline and blocking planned work; "
    "or two or more rejected resubmittals for a critical work package.")

SUBMITTAL_REJECTION_BASIS = (
    "the owner's Run 106 order, section 3, recorded as "
    "`owner_configured_construction_document_control_tolerance`. OWNER-CALIBRATED: a documented "
    "owner tolerance, not a published construction standard. Informal sources report "
    "first-submission rejection around 30 to 40 per cent; that is DESCRIPTIVE and is not the "
    "source for these boundaries and is not cited as one. A stricter figure stated in a project "
    "document -- a submittal plan's acceptance target -- overrides them under the threshold "
    "precedence order")

#: The owner's Run 106 NCR ladder, in PER CENT, worst cut first.
NCR_RATE_CUTS: tuple[tuple[float, str], ...] = (
    (10.0, "Red"), (5.0, "Amber"), (2.0, "Yellow"))

#: The two denominators the owner's NCR percentage ladder is drawn over, and NOTHING ELSE. The
#: ladder is a share of inspections (or, where inspections cannot be reliably identified, of
#: active work packages). It is NOT drawn over labour hours, work value or inspected units, and
#: a rate over one of those is a different quantity that this ladder cannot band.
NCR_DENOMINATOR_TYPES: dict[str, str] = {
    "inspections": "inspections performed in the period",
    "active_work_packages": "active work packages in the period",
}

NCR_RATE_BOUNDARY = (
    "on the NCR rate -- new NCRs opened in the period divided by inspections performed in the "
    "period, as a percentage; where inspections cannot be reliably identified the FALLBACK "
    "denominator is active work packages in the period. Below 2 per cent is Green; at or above 2 "
    "and below 5 is Yellow; at or above 5 and below 10 is Amber; at or above 10 is Red. Each "
    "boundary is INCLUSIVE ON ITS LOWER SIDE. THE DENOMINATOR TYPE IS STORED WITH EVERY RESULT "
    "and must be consistent across periods: the two denominators are not mixed within one "
    "project's trend. RED REGARDLESS OF RATE where any of four conditions holds: an open "
    "critical, life-safety, structural or code-compliance NCR; an NCR on a hold point, a failed "
    "commissioning test or a required inspection blocking turnover; three or more repeat NCRs "
    "for one root cause or trade in the period; or an NCR open beyond a documented contractual "
    "closure date. A high inspection count does not dilute an open critical NCR -- the override "
    "takes precedence over the rate.")

NCR_RATE_BASIS = (
    "the owner's Run 106 order, section 3, recorded as "
    "`owner_configured_construction_quality_control_tolerance`. OWNER-CALIBRATED: a documented "
    "owner tolerance, not a published construction standard. It measures a DIFFERENT quantity "
    "from A6.1 Quality Compliance, which measures first-pass inspection acceptance in Delivery "
    "Quality: a project can inspect well and raise many nonconformances, or the reverse")


def _pct_band(pct: float, cuts: tuple[tuple[float, str], ...]) -> str:
    """Band a percentage on a worst-first ladder of inclusive-lower cuts. Green is the bottom."""
    for cut, band in cuts:
        if pct >= cut:
            return band
    return "Green"


#: The submittal override fields a document must state before the three Red overrides can be
#: evaluated, and the NCR override fields. Named here so the row can say WHICH were absent
#: instead of implying the overrides were tested and did not fire.
SUBMITTAL_OVERRIDE_FIELDS: tuple[str, ...] = (
    "rejected_critical_or_long_lead_forecast_after_need_by",
    "rejected_unresolved_past_review_deadline_blocking_work",
    "critical_package_rejected_resubmittals",
)
NCR_OVERRIDE_FIELDS: tuple[str, ...] = (
    "open_critical_life_safety_structural_or_code_ncr",
    "hold_point_or_commissioning_or_required_inspection_blocking_turnover",
    "max_repeat_ncrs_one_root_cause_or_trade",
    "ncr_open_past_contractual_closure_date",
)


def _override_state(structure: Any, fields: tuple[str, ...]) -> tuple[bool, list[str], list[str]]:
    """
    Which override fields the record actually carries, and which of them FIRED.

    Returns (fired, fired_names, absent_names). A field the record does not carry is ABSENT and
    is never read as False: absent means the condition was not tested, which is a different fact
    from having been tested and found not to hold.
    """
    rec = structure if isinstance(structure, dict) else {}
    fired: list[str] = []
    absent: list[str] = []
    for name in fields:
        value = rec.get(name)
        if value is None:
            absent.append(name)
            continue
        if name.endswith("resubmittals") or name.startswith("max_repeat"):
            try:
                if float(value) >= 2 if name.endswith("resubmittals") else float(value) >= 3:
                    fired.append(name)
            except (TypeError, ValueError):
                absent.append(name)
            continue
        if bool(value):
            fired.append(name)
    return (bool(fired), fired, absent)


def _override_words(fired: list[str], absent: list[str], total: int) -> str:
    if fired:
        return ("A RED OVERRIDE FIRED and it takes precedence over the rate: "
                + ", ".join(fired) + ".")
    if len(absent) == total:
        return ("None of the Red overrides could be evaluated: this project's record states none "
                "of " + ", ".join(absent) + ". The band above rests on the rate alone, and an "
                "override may hold without this reading being able to see it.")
    if absent:
        return ("Overrides evaluated on the fields the record carries; these were not stated and "
                "were therefore NOT tested rather than treated as absent conditions: "
                + ", ".join(absent) + ".")
    return "Every Red override was evaluated against the record and none holds."


# ------------------------------------------------------------ A4.3 Submittal Rejection Rate


_SUBMITTAL_NO_BAND = (
    "no universal basis exists for a submittal rejection share. The owner's Run 101 order, section 4, rules that this module computes and displays its figure and asserts no band unless a project document -- a submittal plan's acceptance target -- states one, and no such target is stated by any document this project has uploaded. The five, fifteen and twenty-five per cent ladder this module used to carry was sourced to nothing and is removed")


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
        # RUN 106, GOAL THREE. THE OWNER SUPPLIED THE BOUNDARY, SO THE BAND IS ASSERTED -- and
        # it is asserted over the FIRST-REVIEW population, which is the quantity he defined.
        # `rejection_rate` (contract 4.3, all assessed decisions) is still reported beside it and
        # is NOT the banded figure: banding it would band a different quantity under his words.
        _fr_n = reading["first_review_assessed"]
        _fr_r = reading["first_review_rejected"]
        _figs = dict(
            rejection_rate=round(rate, 3),
            rejected=reading["rejected"],
            total=reading["assessed"],
            first_review_rate=(round(reading["first_review_rate"], 4)
                               if reading["first_review_rate"] is not None else None),
            first_review_rejected=_fr_r,
            first_review_assessed=_fr_n,
            denominator_type="submittals_receiving_a_first_review",
            denominator_type_words=("submittals receiving a first review in the reporting "
                                    "period; later resubmittal outcomes are excluded"),
            reporting_period=reading["reporting_period"],
            unique_submittals=reading["unique_submittals"],
            resubmission_cycles=reading["resubmission_cycles"],
            disposition_counts=reading["disposition_counts"],
            taxonomy_version=reading["taxonomy_version"],
            canonical_structure="submittal_decision_register",
            source=reading["source"],
        )
        if not _fr_n:
            # A ZERO DENOMINATOR IS NOT ASSESSED. Never a division by zero and never a count
            # banded as though it were a rate.
            return insufficient(
                "Submittal_Rejection",
                "No submittal in this register received a first review in the reporting period, "
                "so the first-review rejection rate has no denominator and none is formed.")
        _pct = 100.0 * _fr_r / _fr_n
        _fired, _fire_names, _absent = _override_state(structure, SUBMITTAL_OVERRIDE_FIELDS)
        _colour = "Red" if _fired else _pct_band(_pct, SUBMITTAL_REJECTION_CUTS)
        _ov = _override_words(_fire_names, _absent, len(SUBMITTAL_OVERRIDE_FIELDS))
        return banded(
            "Submittal_Rejection",
            (f"{_js_str(_fr_r)} of {_js_str(_fr_n)} submittals receiving a first review were "
             f"rejected or returned for revision ({round(_pct, 1)} per cent), from "
             f"{_js_str(reading['assessed'])} assessed decisions in all and "
             f"{_js_str(reading['resubmission_cycles'])} resubmission cycles. " + _ov),
            status_color=_colour,
            boundary=SUBMITTAL_REJECTION_BOUNDARY,
            basis=SUBMITTAL_REJECTION_BASIS,
            provenance=PROVENANCE_OWNER_CALIBRATED,
            threshold_source=THRESHOLD_SOURCE_OWNER,
            band_basis_id="owner_configured_construction_document_control_tolerance",
            band_first_review_pct=round(_pct, 3),
            band_override_fired=_fired,
            band_override_conditions=_fire_names,
            band_overrides_evaluated=(len(_absent) < len(SUBMITTAL_OVERRIDE_FIELDS)),
            band_override_fields_absent=_absent,
            band_override_words=_ov,
            **_figs,
        )
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
    # RUN 106, GOAL THREE. THE EXTRACTED-TOTALS PATH CANNOT SEPARATE FIRST REVIEWS FROM
    # RESUBMITTALS, AND SO IT DOES NOT BAND.
    #
    # The owner's measure is explicit that later resubmittal outcomes are NOT in the denominator.
    # These totals are a rejected count and a register total with no revision structure behind
    # them, so the first-review population cannot be identified from them and the share formed
    # here is a DIFFERENT quantity from the one the owner banded. Banding it under his ladder
    # would attach his boundary to a measure he did not define, which is the same defect as
    # inventing a threshold, arrived at from the other end. The figure is displayed and the
    # reason is stated; the governed register path above bands.
    return band_abstained(
        "Submittal_Rejection", evidence,
        reason=("the owner's Run 106 first-review rejection ladder is drawn over submittals "
                "RECEIVING A FIRST REVIEW, excluding later resubmittal outcomes from the "
                "denominator. This project supplied extracted register totals -- a rejected "
                "count and a population total with no revision or decision-date structure -- "
                "from which the first-review population cannot be identified, so the share "
                "computed here is a different quantity and his boundary is not attached to it. "
                "Upload a submittal decision register carrying each decision's submittal "
                "identifier, revision identifier and decision date and this module bands"),
        rejection_rate=rate,
        rejected=rejected,
        total=total,
        denominator_type="all_assessed_decisions",
        denominator_type_words=("every submittal decision the extracted totals report, first "
                                "reviews and resubmittals together and indistinguishable"),
        reporting_period=si.get("period"),
        source="rfa_log" if use_rfa else "submittals",
        canonical_structure="extracted_register_totals",
    )


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
        structure = require_v4_structure(si, "A4.4")
        reading = ncr_rate(structure)
    except StructureAbsent as absent:
        return insufficient("NCR_Rate", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    _open = (f" {_js_str(reading['open_count'])} are still open."
             if reading["open_count"] is not None else "")
    _figs = dict(
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
        reporting_period=(structure.get("reporting_period")
                          if isinstance(structure, dict) else None),
    )
    _msg = (f"{_js_str(reading['ncr_count'])} nonconformances against "
            f"{_js_str(reading['exposure_quantity'])} {reading['exposure_unit']}, a rate of "
            f"{_js_str(round(reading['ncr_rate'], 4))} for each one." + _open)
    # RUN 106, GOAL THREE. THE OWNER SUPPLIED A PERCENTAGE LADDER, AND IT IS DRAWN OVER TWO
    # DENOMINATORS AND NO OTHERS.
    #
    # His measure is new NCRs opened in the period over INSPECTIONS PERFORMED in the period, with
    # ACTIVE WORK PACKAGES as the fallback where inspections cannot be reliably identified. A
    # nonconformance rate per labour hour, per unit of work value or per inspected item is a
    # DIFFERENT quantity, and 2/5/10 per cent means nothing over it. So the exposure unit the
    # record states decides whether the ladder applies at all: where it is neither of the two,
    # the figure is displayed with calibration pending and the reason names the unit. Widening
    # the ladder to cover it would be inventing a threshold.
    #
    # THE DENOMINATOR TYPE IS STORED WITH EVERY RESULT, because the owner requires the
    # denominator to be consistent across periods and a trend that silently switched denominator
    # would be a fabricated trend. The two are not mixed within one project's trend; this module
    # stores which was used and the trend surfaces read it.
    _unit_key = str(reading["exposure_unit"] or "").strip().lower().replace(" ", "_")
    _denominator = NCR_DENOMINATOR_TYPES.get(_unit_key)
    if reading["exposure_quantity"] in (0, None) or not reading["exposure_quantity"]:
        # A ZERO DENOMINATOR IS NOT ASSESSED. `canonical_v4.ncr_rate` already refuses one, so
        # this arm is unreachable today; it is written because the owner requires the rule to be
        # stated here and a future supply path must not be able to reach a division by zero.
        return insufficient(
            "NCR_Rate",
            "The nonconformance record for this project reports no exposure in the period, so "
            "the NCR rate has no denominator and none is formed.")
    if _denominator is None:
        return calibration_pending(
            "NCR_Rate",
            _msg + (" No band is asserted: the owner's Run 106 NCR ladder is a percentage of "
                    "INSPECTIONS PERFORMED in the period, or of ACTIVE WORK PACKAGES where "
                    "inspections cannot be reliably identified. This record measures exposure "
                    "in " + str(reading["exposure_unit"]) + ", which is a different quantity, "
                    "and his boundaries are not stretched to cover it."),
            denominator_type=_unit_key or None,
            denominator_type_words=("the exposure unit this record states, which is not one of "
                                    "the two the owner's ladder is drawn over"),
            **_figs)
    _pct = 100.0 * reading["ncr_count"] / reading["exposure_quantity"]
    _fired, _fire_names, _absent = _override_state(structure, NCR_OVERRIDE_FIELDS)
    # THE OVERRIDE ALSO FIRES ON THE SEVERITY MIX THE RECORD ALREADY CARRIES. An open critical
    # or life-safety nonconformance is a Red condition whether or not the dedicated override
    # field was stated, and the severity counts are a field this platform already extracts.
    _sev = reading.get("severity_counts") or {}
    _crit = [k for k, v in _sev.items()
             if str(k).strip().lower() in ("critical", "life_safety", "life-safety", "major")
             and v]
    if _crit and reading.get("open_count"):
        _fired = True
        _fire_names = _fire_names + ["open_nonconformances_with_" + ",".join(sorted(_crit))
                                     + "_severity_recorded"]
    _colour = "Red" if _fired else _pct_band(_pct, NCR_RATE_CUTS)
    _ov = _override_words(_fire_names, _absent, len(NCR_OVERRIDE_FIELDS))
    return banded(
        "NCR_Rate",
        _msg + f" That is {round(_pct, 1)} per cent of {NCR_DENOMINATOR_TYPES[_unit_key]}. " + _ov,
        status_color=_colour,
        boundary=NCR_RATE_BOUNDARY,
        basis=NCR_RATE_BASIS,
        provenance=PROVENANCE_OWNER_CALIBRATED,
        threshold_source=THRESHOLD_SOURCE_OWNER,
        band_basis_id="owner_configured_construction_quality_control_tolerance",
        band_rate_pct=round(_pct, 3),
        band_override_fired=_fired,
        band_override_conditions=_fire_names,
        band_overrides_evaluated=(len(_absent) < len(NCR_OVERRIDE_FIELDS) or bool(_crit)),
        band_override_fields_absent=_absent,
        band_override_words=_ov,
        denominator_type=_unit_key,
        denominator_type_words=NCR_DENOMINATOR_TYPES[_unit_key],
        denominator_consistency_rule=(
            "the denominator type is stored with every result and must not change between "
            "periods within one project's trend: inspections and active work packages are two "
            "populations and a trend that mixes them is not a trend"),
        **_figs)


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
    # ------------------------------------------------- RUN 107, THE OWNER'S TWO COMPONENTS
    # "Use any component whose denominator exists; worst-of the available." A component whose
    # denominator is absent is NOT ASSESSED and is not counted as favourable.
    _comps = []
    _allow_total = reading.get("weather_allowance_days")
    _approved = reading.get("weather_days_approved")
    if _allow_total is not None and _allow_total > 0 and _approved is not None:
        _consumed = _approved / _allow_total
        _comps.append(_OB.component(
            "allowance consumed", value=round2(_consumed),
            band=_OB.ascending(_consumed, 0.80, 1.00, 1.20),
            boundary=("weather-delay days used divided by weather allowance days: at or below "
                      "0.80 is Green; above 0.80 and at or below 1.00 is Yellow; above 1.00 and "
                      "at or below 1.20 is Amber; above 1.20 is Red. Each boundary is INCLUSIVE "
                      "ON ITS UPPER SIDE. The numerator is the days the OWNER APPROVED, "
                      "recorded in the OAC meeting minutes; a figure the contractor claimed is "
                      "never substituted for it, and a weather log alone is not an approval")))
    else:
        _comps.append(_OB.component(
            "allowance consumed",
            absent_reason=(
                "This project's weather record does not state both the weather allowance the "
                "contract calendar grants and the weather days the owner APPROVED in the OAC "
                "meeting minutes, so the share of the allowance consumed has no denominator or "
                "no numerator and is Not Assessed. Neither figure is inferred and the days "
                "claimed are not read in place of the days approved.")))
    # THE FLOAT DENOMINATOR, AND WHERE IT COMES FROM. It is the float the WEATHER RECORD ITSELF
    # states for the affected path. A2.12 Critical Path Analysis computes total float, but no
    # path exists from one module's reading to another module's runner -- `registry.run_all`
    # dispatches every flat-input module from `signal_inputs` alone, and the only cross-module
    # channel, `signal_package.array_entry`, carries a module id, a method class and a status
    # colour and no figures at all. So this arm bands on the record's own stated float or not
    # at all; it never reaches into A2.12, and it never infers a float figure.
    _float = None
    for _e in reading["events"]:
        if _e.get("schedule_path_id") == worst:
            _float = _e.get("available_float_days")
            break
    # RUN 108, GOAL 2. THE TWO SIDES OF THIS RATIO MUST BE THE SAME KIND OF DAY. Total float is
    # a working-day quantity on the project's approved calendar. Run 107 divided the delay by it
    # without either side stating its basis, so a record counting CALENDAR days was silently
    # divided by working-day float. This run makes the record state its basis and recounts the
    # delay on the project's own calendar, using the one conversion function -- and where it
    # cannot, the component says so instead of dividing two different units.
    from .working_calendar import (CALENDAR_ABSENT_WORDS, read_project_calendar,
                                   working_days_between)
    _w_basis = reading.get("day_basis")
    _w_delay = reading["direct_path_effect_days"]
    _w_cal = None
    _w_absent = None
    _w_recount = None
    if _w_basis == "calendar_days":
        _w_cal = read_project_calendar(si, reading.get("weather_calendar_id"))
        if _w_cal is None:
            _w_cal = read_project_calendar(si)
        if _w_cal is None:
            _w_absent = ("this project's weather record counts CALENDAR days while total float "
                         "is a working-day quantity, and " + CALENDAR_ABSENT_WORDS)
        else:
            _spans = []
            for _e in reading["events"]:
                if _e.get("schedule_path_id") != worst:
                    continue
                try:
                    _a = _date.fromisoformat(str(_e.get("event_start_date") or "")).toordinal()
                    _b = _date.fromisoformat(str(_e.get("event_end_date") or "")).toordinal()
                except ValueError:
                    _spans = None
                    break
                _spans.append((_a, _b, _e.get("actual_lost_days") or 0.0))
            if not _spans:
                _w_absent = (
                    "this project's weather record counts CALENDAR days and states no start "
                    "and end date for the events on the affected path, so the delay cannot be "
                    "recounted in working days on this project's calendar and is not divided "
                    "by a working-day float. WHAT IS NEEDED: event_start_date and "
                    "event_end_date on each weather event, as calendar dates")
            else:
                _cal_lost = sum(l for _, _, l in _spans)
                _work_lost = sum(working_days_between(_w_cal, a - 1, b) for a, b, _ in _spans)
                if _cal_lost > 0:
                    _w_recount = {"calendar_days_lost": _cal_lost,
                                  "working_days_lost": _work_lost,
                                  "working_calendar_id": _w_cal.get("calendar_id")}
                    _w_delay = _w_delay * (_work_lost / _cal_lost)
    elif _w_basis is None:
        _w_absent = None  # basis unstated: the ratio forms as before and the reading says so.
    if _w_absent is not None:
        _comps.append(_OB.component("float consumed", absent_reason=_w_absent))
    elif _float is not None and _float > 0:
        _fc = _w_delay / _float
        _comps.append(_OB.component(
            "float consumed", value=round2(_fc),
            band=_OB.ascending(_fc, 0.50, 0.75, 1.00),
            boundary=("weather-caused forecast delay days divided by remaining total float "
                      "days on the affected path: at or below 0.50 is Green; above 0.50 and at "
                      "or below 0.75 is Yellow; above 0.75 and at or below 1.00 is Amber; above "
                      "1.00 is Red. Each boundary is INCLUSIVE ON ITS UPPER SIDE. The float is "
                      "the figure the weather record itself states for the affected path; it is "
                      "NOT read from Critical Path Analysis, which no path connects to this "
                      "module")))
    else:
        _comps.append(_OB.component(
            "float consumed",
            absent_reason=(
                "This project's weather record states no remaining total float above zero on "
                "the affected path, so the share of float consumed has no denominator and is "
                "Not Assessed. Critical Path Analysis computes total float but its reading does "
                "not reach this module: no path exists in this platform for one module's "
                "reading to reach another module's runner, so no float figure is taken from it "
                "and none is inferred.")))
    _agg = _OB.aggregate(_comps)
    _posture = _agg["band_posture_before_override"]
    # THE HARD OVERRIDE, APPLIED AFTER COMPONENT BANDING AND ABLE ONLY TO WORSEN.
    _late = reading.get("milestone_forecast_late")
    _te_in = reading.get("time_extension_incorporated_in_baseline")
    _mclass = (reading.get("milestone_class") or "").strip().lower()
    _override = bool(_late) and _mclass in ("contractual", "owner_committed", "owner-committed") \
        and not _te_in
    _override_words = (
        "HARD OVERRIDE: Red if a documented weather event causes a contractual or "
        "owner-committed milestone to forecast late and no approved time extension has been "
        "incorporated into the baseline. All three facts must be STATED by the weather record: "
        "that a milestone forecasts late, which class of milestone it is, and whether a granted "
        "extension is in the baseline. ")
    if _late is None:
        _override_words += ("This project's weather record states nothing about a milestone "
                            "forecasting late, so the override was NOT EVALUABLE and silence "
                            "was not read as the condition being absent.")
    elif _override:
        _override_words += "It fired: the record states all three."
    else:
        _override_words += "It did not fire on this record."
    if _override:
        _posture = _OB.at_least_as_adverse_as(_posture, "Red")
    _fields = {
        "direct_path_effect_days": reading["direct_path_effect_days"],
        "path_effect_days": paths,
        "worst_path_id": worst,
        "event_count": reading["event_count"],
        "total_lost_days": reading["total_lost_days"],
        "allowance_days_remaining_after": reading["allowance_days_remaining_after"],
        "mitigation_days_reported": reading["mitigation_days_reported"],
        "events": reading["events"],
        "weather_calendar_id": reading["weather_calendar_id"],
        "weather_day_basis": _w_basis,
        "weather_day_basis_stated": _w_basis is not None,
        "weather_delay_days_used_in_float_share": _w_delay,
        "weather_working_day_recount": _w_recount,
        "weather_allowance_days": _allow_total,
        "weather_days_claimed": reading.get("weather_days_claimed"),
        "weather_days_approved": _approved,
        "approval_period": reading.get("approval_period"),
        "approval_source": reading.get("approval_source"),
        "time_extension_granted": reading.get("time_extension_granted"),
        "time_extension_days_granted": reading.get("time_extension_days_granted"),
        "time_extension_incorporated_in_baseline": _te_in,
        "milestone_forecast_late": _late,
        "milestone_class": reading.get("milestone_class") or None,
        "band_hard_override_fired": _override,
        "band_hard_override_evaluable": _late is not None,
        "canonical_structure": "weather_impact_events",
        "source": reading["source"],
        **_agg,
    }
    _msg = (
        f"{_js_str(reading['event_count'])} verified weather events lost "
        f"{_js_str(reading['total_lost_days'])} days. After the weather allowance and the float "
        f"on each path, the direct effect on the schedule is "
        f"{_js_str(reading['direct_path_effect_days'])} days, on the path called {worst}.")
    if _posture is None:
        return band_abstained(
            "Weather_Impact", _msg,
            reason=("Not Assessed. Neither of the two components the owner's ladder is defined "
                    "on could be formed from this project's weather record: "
                    + " ".join(c["not_assessed_reason"] for c in _comps
                               if c.get("not_assessed_reason"))),
            band_basis_id="owner_configured_construction_control_tolerance",
            **_fields)
    return banded(
        "Weather_Impact", _msg,
        status_color=_posture,
        boundary=(" ".join(c["boundary"] for c in _comps if c["boundary"])
                  + " " + _agg["band_aggregation_words"] + " " + _override_words),
        basis=("the owner's Run 107 order, section 2, A4.5. The band basis identifier is "
               "`owner_configured_construction_control_tolerance`. OWNER-CALIBRATED: no "
               "published standard fixes 0.80, 1.00 and 1.20 on allowance consumption, nor "
               "0.50, 0.75 and 1.00 on float consumption. They are a documented owner tolerance "
               "and are not presented as a construction standard"),
        provenance=PROVENANCE_OWNER_CALIBRATED,
        threshold_source=THRESHOLD_SOURCE_OWNER,
        band_basis_id="owner_configured_construction_control_tolerance",
        **_fields)


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
    # ========================= RUN 101, THE REBUILD: A COUNT IS NOT THE MEASURE, IMPACT IS
    # THE OWNER'S RULING, SECTION 4. What bands is COST IMPACT and SCHEDULE IMPACT, both against
    # the ORIGINAL contract. The frequency is kept and displayed -- it was never wrong, it was
    # simply not the measure -- and it is not what the colour is drawn from.
    #
    # COST IMPACT. Additions and omissions stated SEPARATELY, plus the net change as a proportion
    # of the original contract value. AN OMISSION IS NEVER ADVERSE: a reduction is Green, and
    # section 12.1b fails the run for treating one as adverse. So the ladder is climbed by the
    # ADDITIONS fraction, and a net change of zero or below is Green outright whatever the
    # additions were, because the money set aside has not been passed.
    #
    #   Green  -- net change zero or negative, OR additions strictly under 5 per cent
    #   Yellow -- additions at or above 5 per cent and at or below 10 per cent
    #   Amber  -- additions above 10 per cent and at or below 20 per cent
    #   Red    -- additions above 20 per cent
    #
    # THE BASIS, AND IT IS RECORDED HERE AND IN THE STORED READING: a contingency reserve is
    # conventionally around twenty per cent of contract value, so change exposure beyond twenty
    # per cent has passed the money set aside to absorb it. AMBER BEGINS AT HALF THE RESERVE.
    # CONVENTION, on the owner's stated authority.
    #
    # SCHEDULE IMPACT. Change-related delay days against the ORIGINAL contract duration, and the
    # float consumption ratio -- change-related delay days over available total float on the
    # affected path. IF FLOAT IS UNAVAILABLE THE SCHEDULE HALF ABSTAINS AND SAYS SO rather than
    # assuming zero: assuming zero float would turn every unmeasured project Red.
    _add_f = reading.get("additions_fraction")
    _om_f = reading.get("omissions_fraction")
    _net_f = reading["change_magnitude_net"]
    _reserve = _BR.configured_value("change_order_contingency_reserve_fraction")
    _cost_band = ("Green" if (_net_f <= 0 or _add_f < 0.05)
                  else "Yellow" if _add_f <= 0.10
                  else "Amber" if _add_f <= 0.20 else "Red")
    _sched = _schedule_impact(require_v4_structure(si, "A4.6"), reading)
    _bands = [_cost_band] + ([_sched["band"]] if _sched.get("band") else [])
    _worst = max(_bands, key=lambda b: _RANK[b])
    _message = (
        f"Change orders have added "
        f"{_js_str(round(_add_f * 100, 2))} per cent and omitted "
        f"{_js_str(round(_om_f * 100, 2))} per cent of the original contract, a net change of "
        f"{_js_str(round(_net_f * 100, 2))} per cent. {_sched['sentence']} "
        f"{_js_str(reading['change_count'])} governed changes over "
        f"{_js_str(reading['exposure_days'])} days is the frequency, which is context and is "
        f"not what the band is drawn from.")
    return banded(
        "CO_Frequency", _message,
        status_color=_worst,
        boundary=(
            "COST IMPACT, on the ADDITIONS as a proportion of the ORIGINAL contract value: a net "
            "change of zero or below, or additions strictly under 5 per cent, is Green; "
            "additions at or above 5 per cent and at or below 10 per cent is Yellow; above 10 "
            "per cent and at or below 20 per cent is Amber; above 20 per cent is Red. AN "
            "OMISSION IS NEVER ADVERSE -- a reduction is Green and is never added to the "
            "additions. SCHEDULE IMPACT: " + _sched["boundary"] + " Where both halves band, the "
            "WORSE of the two is what the module asserts, and the other is reported beside it."),
        basis=(
            "the owner's Run 101 order, section 4, on the owner's stated authority. THE COST "
            "LADDER'S BASIS: a contingency reserve is conventionally around "
            f"{_js_str(round((_reserve or 0) * 100))} per cent of contract value, so change "
            "exposure beyond that has passed the money set aside to absorb it, and Amber begins "
            "at half the reserve. No standards clause fixes 5, 10 or 20 per cent. THE SCHEDULE "
            "LADDER has no published basis at all and is the owner's stated threshold."),
        provenance=PROVENANCE_CONVENTION,
        # RUN 102, SECTION 6, RUNG 3. The contingency-reserve fraction the cost ladder is drawn
        # from is a convention the owner configured; no project document and no published
        # instrument fixes these boundaries.
        threshold_source=THRESHOLD_SOURCE_OWNER,
        boundary_provenance=(PROVENANCE_OWNER_CALIBRATED if _sched.get("band") == _worst
                             else PROVENANCE_CONVENTION),
        cost_impact_band=_cost_band,
        schedule_impact_band=_sched.get("band"),
        schedule_impact_reason=_sched.get("reason"),
        additions_fraction=round(_add_f, 6),
        omissions_fraction=round(_om_f, 6),
        additions_value=reading.get("additions_value"),
        omissions_value=reading.get("omissions_value"),
        contingency_reserve_fraction=_reserve,
        change_related_delay_days=_sched.get("delay_days"),
        available_total_float_days=_sched.get("total_float"),
        float_consumption_ratio=_sched.get("float_ratio"),
        original_contract_duration_days=_sched.get("original_duration"),
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


def _schedule_impact(structure: dict, reading: dict) -> dict[str, Any]:
    """
    A4.6's SCHEDULE HALF. Change-related delay days against the original contract duration, and
    the float consumption ratio on the affected path.

    OWNER-CALIBRATED, on the owner's stated authority: no published basis exists for any of these
    four conditions and none is claimed.

        Green  -- no material float consumption or forecast completion movement, or the effect
                  FULLY RESOLVED through an approved extension or rebaseline
        Yellow -- float consumed without a current threat to contractual or key milestone
                  completion
        Amber  -- material erosion of float on a critical or near-critical path, unresolved time
                  extension exposure, or a threatened milestone without confirmed completion
                  movement
        Red    -- forecast or contract completion movement, negative float, or documented
                  unresolved critical-path time extension exposure

    IF FLOAT IS UNAVAILABLE THIS HALF ABSTAINS AND SAYS SO. It does not assume zero. Assuming
    zero float would make every project whose schedule was never measured read as Red, which is
    manufacturing a finding out of an absence.
    """
    boundary = (
        "forecast or contract completion movement, negative float, or documented unresolved "
        "critical-path time extension exposure is Red; material erosion of float on a critical "
        "or near-critical path, unresolved time extension exposure, or a threatened milestone "
        "without confirmed completion movement is Amber; float consumed without a current threat "
        "to contractual or key milestone completion is Yellow; no material float consumption or "
        "forecast completion movement, or the effect fully resolved through an approved "
        "extension or rebaseline, is Green.")
    delay = structure.get("change_related_delay_days")
    total_float = structure.get("available_total_float_days")
    duration = structure.get("original_contract_duration_days")
    resolved = bool(structure.get("time_extension_approved"))
    moved = structure.get("forecast_completion_moved")
    out: dict[str, Any] = {"boundary": boundary, "delay_days": delay,
                           "total_float": total_float, "original_duration": duration,
                           "float_ratio": None, "band": None}
    if not isinstance(delay, (int, float)):
        out["reason"] = ("the change register states no change-related delay days, so the "
                         "schedule half of change impact is not measured and no band is drawn "
                         "for it")
        out["sentence"] = ("No change-related delay days are stated, so the schedule half of "
                           "change impact abstains.")
        return out
    if not isinstance(total_float, (int, float)):
        out["reason"] = ("the change register states no available total float on the affected "
                         "path, so the float consumption ratio cannot be formed. It is NOT "
                         "assumed to be zero: assuming zero float would report a threatened "
                         "completion on a project whose schedule was simply never measured")
        out["sentence"] = (f"{delay} change-related delay days are stated, but no available "
                           f"total float on the affected path is, so the float consumption "
                           f"ratio is not formed and is not assumed to be zero.")
        return out
    ratio = (delay / total_float) if total_float > 0 else None
    out["float_ratio"] = ratio
    if total_float < 0 or moved is True:
        out["band"] = "Red"
    elif resolved or delay <= 0:
        out["band"] = "Green"
    elif ratio is not None and ratio >= 1.0:
        out["band"] = "Amber"
    elif ratio is not None:
        out["band"] = "Yellow"
    else:
        # total_float is zero and delay is positive: the path has no float left to consume and
        # a delay has been recorded against it. That is negative float in all but name.
        out["band"] = "Red"
    out["sentence"] = (
        f"{delay} change-related delay days stand against "
        f"{total_float} days of available total float on the affected path"
        + (f", a float consumption ratio of {round(ratio, 2)}" if ratio is not None else "")
        + (", resolved through an approved time extension" if resolved else "") + ".")
    return out


#: RUN 107, A4.7. The basis, stated once because two call sites print it.
_BASIS_A47 = (
    "the owner's Run 107 order, section 2, A4.7. The band basis identifier is "
    "`owner_configured_construction_control_tolerance`. OWNER-CALIBRATED: the four stages are "
    "the owner's own description of dispute escalation and no published standard fixes which "
    "posture each carries. The ladder is ORDINAL: a count of disputes is not a position on it, "
    "and no arithmetic is performed on the events")


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
    # -------------------------------------------- RUN 107, THE ORDINAL LADDER. NOT A COUNT.
    # "Ordinal. Never average event counts. The posture is the highest documented open stage."
    from .canonical_v4 import DISPUTE_ESCALATION_CLASSES as _DEC
    _open = [i for i in reading["issues"] if not i.get("resolved")]
    _classed = [(i, _DEC[i["escalation_class"]][0]) for i in _open if i.get("escalation_class")]
    _unclassed = [i["issue_id"] for i in _open if not i.get("escalation_class")]
    _msg = (
        f"Of {_js_str(reading['issue_count'])} issues on the "
        f"{reading['process_id']} process, {_js_str(len(_open))} "
        f"{'is' if len(_open) == 1 else 'are'} open, and the furthest has reached the stage "
        f"called {reading['highest_stage_id']}, which is step "
        f"{_js_str(reading['highest_stage_rank'])} of "
        f"{_js_str(reading['stage_count'])} on that process.")
    _fields = {
        "highest_stage_id": reading["highest_stage_id"],
        "highest_stage_rank": reading["highest_stage_rank"],
        "escalation_position": round(reading["escalation_position"], 4),
        "process_id": reading["process_id"],
        "process_version": reading["process_version"],
        "stage_count": reading["stage_count"],
        "issue_count": reading["issue_count"],
        "issues_at_highest": reading["issues_at_highest"],
        "open_issue_count": len(_open),
        "open_issues": reading["open_issues"],
        "stage_escalation_classes": reading["stage_escalation_classes"],
        "issues_without_escalation_class": _unclassed,
        "total_claim_value": reading["total_claim_value"],
        "max_unresolved_age_days": reading["max_unresolved_age_days"],
        "issues": reading["issues"],
        "canonical_structure": "claim_dispute_register",
        "source": reading["source"],
    }
    _override_issues = [i["issue_id"] for i in _open
                        if i.get("prevents_controlling_or_near_critical_progress")]
    _override_stated = any(
        i.get("prevents_controlling_or_near_critical_progress") is not None for i in _open)
    _override_words = (
        "HARD OVERRIDE: Red if any documented dispute prevents progress on a controlling or "
        "near-critical activity. The register must STATE that it does. ")
    if _override_issues:
        _override_words += (f"It fired: {_and_list(_override_issues)} "
                            f"{'states' if len(_override_issues) == 1 else 'state'} it.")
    elif _override_stated:
        _override_words += "No open issue states it, so it did not fire."
    else:
        _override_words += ("No open issue states the fact either way, so the override was NOT "
                            "EVALUABLE on this register and silence was not read as the "
                            "condition being absent.")
    _ladder = ("the posture is the HIGHEST DOCUMENTED OPEN STAGE on the owner's ordinal ladder, "
               "and event counts are NEVER averaged: "
               + "; ".join(f"{band} -- {words}" for _k, (band, words) in _DEC.items())
               + ". Which of these four a project's own stage is must be DECLARED by the "
                 "process record. A stage is never read from its name, from sentiment or from "
                 "narrative tone, and only source-record language is used. " + _override_words)
    if not _classed:
        _reason = (
            "Not Assessed. This project's dispute process does not place its stages in the "
            "owner's four escalation classes, so no open issue can be placed on the ordinal "
            "ladder. A stage is never inferred from its name or from narrative tone."
            if not reading["escalation_classes_declared"] else
            ("Not Assessed. No open issue on this register sits at a stage the process places "
             "in one of the owner's four escalation classes."
             if _open else
             "Not Assessed. This register records no OPEN issue, and the owner's ladder is "
             "defined on the highest documented OPEN stage. A closed register is not read as "
             "Green, because Green is a statement that items were resolved through normal "
             "project administration and this register was not asked that question."))
        if _override_issues:
            return banded(
                "Dispute_Escalation", _msg, status_color="Red",
                boundary=_ladder, basis=_BASIS_A47,
                provenance=PROVENANCE_OWNER_CALIBRATED,
                threshold_source=THRESHOLD_SOURCE_OWNER,
                band_basis_id="owner_configured_construction_control_tolerance",
                band_hard_override_fired=True,
                band_posture_before_override=None, **_fields)
        return band_abstained(
            "Dispute_Escalation", _msg, reason=_reason,
            band_basis_id="owner_configured_construction_control_tolerance",
            band_hard_override_fired=bool(_override_issues), **_fields)
    _posture = _OB.worst([b for _i, b in _classed])
    _before = _posture
    if _override_issues:
        _posture = _OB.at_least_as_adverse_as(_posture, "Red")
    _governing = max(_classed, key=lambda pair: (_OB.BAND_ORDER.index(pair[1]),
                                                 pair[0]["issue_id"]))[0]
    return banded(
        "Dispute_Escalation", _msg,
        status_color=_posture,
        boundary=_ladder + (f" The highest documented open stage is "
                            f"{_governing['current_stage_id']}, on issue "
                            f"{_governing['issue_id']}."),
        basis=_BASIS_A47,
        provenance=PROVENANCE_OWNER_CALIBRATED,
        threshold_source=THRESHOLD_SOURCE_OWNER,
        band_basis_id="owner_configured_construction_control_tolerance",
        band_posture_before_override=_before,
        band_hard_override_fired=bool(_override_issues),
        governing_issue_id=_governing["issue_id"],
        governing_stage_id=_governing["current_stage_id"],
        governing_escalation_class=_governing["escalation_class"],
        band_aggregation_rule="highest documented open stage",
        **_fields)


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
    # ------------------------------------------------ RUN 107. THE MVP, AND IT IS THE BAND.
    # The owner's Run 107 order rules the four-factor composite OUT OF SCOPE. The composite
    # below still COMPUTES where a project supplies the weighted assessment -- it is not
    # removed, and this run adds nothing to it: no per-firm factor extraction, no
    # critical-path adjustment, no trade-level scoring, no "two Ambers make a Red", no
    # automatic default or termination reading. WHAT THIS RUN ADDS is one narrow reading:
    # the rating the Subcontractor Performance Report already states, normalised onto the
    # owner's ladder, with the most adverse valid reported posture governing across firms.
    #
    # AND THE BAND IS HELD. An Amber or Red normalised posture is not a finding until a
    # Project Manager has reviewed it: `pm_review.resolve` decides, `status_color` stays
    # None while it is held, and the held state lives in `module_state`, which is NOT a
    # project status. See `pm_review.py` for why that is structural rather than a promise.
    try:
        structure = require_v4_structure(si, "A4.8")
    except StructureAbsent as absent:
        return insufficient("Subcontractor_Performance", absent.sentence,
                            ABSTAIN_STRUCTURE_ABSENT)
    _mvp = None
    _mvp_absent = None
    try:
        _mvp = subcontractor_reported_ratings(structure)
    except StructureAbsent as absent:
        _mvp_absent = absent.sentence
    if _mvp is not None:
        _norm = _mvp["normalised_posture"]
        _review = _module_review(si, "A4.8")
        _res = _PMR.resolve(_norm, _review)
        _audit = _PMR.audit_record(
            normalised_posture=_norm,
            source_rating=_mvp["governing_reported_rating"],
            source_document_id=_mvp["source"],
            source_document_version=_mvp["report_version"],
            period=next((f["assessment_period"] for f in _mvp["firms"]
                         if f["subcontractor_id"] == _mvp["governing_subcontractor_id"]), None),
            normalisation_rule=_mvp["governing_normalisation_rule"],
            normalisation_rule_version=_mvp["normalisation_rule_version"],
            resolution=_res)
        _fields = {
            "firms": _mvp["firms"],
            "firm_count": _mvp["firm_count"],
            "normalised_posture": _norm,
            "governing_subcontractor_id": _mvp["governing_subcontractor_id"],
            "governing_reported_rating": _mvp["governing_reported_rating"],
            "normalisation_rule": _mvp["governing_normalisation_rule"],
            "normalisation_rule_version": _mvp["normalisation_rule_version"],
            "rating_scale": _mvp["rating_scale"],
            "report_date": _mvp["report_date"],
            "report_version": _mvp["report_version"],
            "module_state": _res["module_state"],
            "module_state_words": _res["module_state_words"],
            "pm_review_required": _res["review_required"],
            "pm_review_audit_record": _audit,
            "canonical_structure": "subcontractor_reported_ratings",
            "source": _mvp["source"],
            "scope_note": (
                "MVP scope, and it is deliberately narrow. This reading normalises the rating "
                "the report already states. It performs no per-firm schedule, quality, safety "
                "or commercial factor extraction, no critical-path or near-critical "
                "adjustment, no trade-level scoring, no two-Ambers-make-a-Red policy and no "
                "automatic default or termination reading."),
        }
        _msg = (
            f"{_js_str(_mvp['firm_count'])} subcontractor"
            f"{'' if _mvp['firm_count'] == 1 else 's'} carry a reported performance rating. "
            f"The most adverse is {_mvp['governing_subcontractor_id']}, rated "
            f"{_mvp['governing_reported_rating']}, which normalises to {_norm}.")
        _boundary = (
            "on the rating the Subcontractor Performance Report states, normalised by "
            "the owner's Run 107 ladder: Exceptional or Very Good, or 90 to 100, is Green; "
            "Satisfactory, or 80 to 89, is Yellow; Marginal, or 70 to 79, is Amber; "
            "Unsatisfactory, or below 70, is Red. Each numeric boundary is INCLUSIVE ON ITS "
            "LOWER SIDE. Where the report states its own scale, that scale's documented "
            "mapping is used in its place. Where no mappable rating or score is present the "
            "reading is Not Assessed and a rating is NEVER inferred from narrative text or "
            "from another document. Across firms the MOST ADVERSE valid reported posture "
            "governs. HELD FOR REVIEW: an Amber or Red normalised posture is not a finding "
            "until a Project Manager records a disposition; the module asserts no band while "
            "it is held and the category is formed from the modules that are available. "
            f"Here the rule applied was {_mvp['governing_normalisation_rule']}.")
        _basis = (
            "the owner's Run 107 order, section 2, A4.8. The band basis identifier the owner "
            "named for it is `source_report_rating_normalization`. OWNER-CALIBRATED: the "
            "report's own rating is the measure and the platform does not re-rate it, but no "
            "published standard fixes which of the four postures each label or score band "
            "maps onto. That mapping is the owner's stated decision. Where the report states "
            "its own documented scale mapping, that mapping is rung 1 and wins.")
        if _res["posture"] is None:
            return band_abstained(
                "Subcontractor_Performance", _msg,
                reason=_res.get("not_assessed_reason") or _res["module_state_words"],
                band_basis_id="source_report_rating_normalization",
                band_boundary_if_reviewed=_boundary,
                **_fields)
        return banded(
            "Subcontractor_Performance", _msg,
            status_color=_res["posture"],
            boundary=_boundary,
            basis=_basis,
            provenance=PROVENANCE_OWNER_CALIBRATED,
            threshold_source=THRESHOLD_SOURCE_OWNER,
            band_basis_id="source_report_rating_normalization",
            **_fields)
    try:
        reading = subcontractor_performance(structure)
    except StructureAbsent as absent:
        return insufficient(
            "Subcontractor_Performance",
            (_mvp_absent or absent.sentence), ABSTAIN_STRUCTURE_ABSENT)
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


#: RUN 108. TELLING A CALENDAR DATE FROM A SCHEDULE-AXIS DAY NUMBER, without asking either
#: document to declare which it printed. `canonical_v4._day` turns an ISO date into a day
#: ORDINAL -- `date.toordinal()` -- and 1 January 1900 is ordinal 693,596 while a schedule axis
#: counts from 0 or 1. The two ranges do not overlap for any project this platform can hold, so
#: a figure inside the ordinal range is a real calendar date and one below it is an axis number
#: that has no calendar day behind it and is never converted.
_ORD_MIN = 693596      # 1900-01-01
_ORD_MAX = 766644      # 2099-12-31


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
    # --------------------------------------- RUN 107. PER ITEM, MOST ADVERSE ITEM GOVERNS.
    from .canonical_v4 import (PROCUREMENT_CRITICALITY_CONTROLLING,
                               PROCUREMENT_CRITICALITY_NOT)
    # RUN 108, GOAL 2. THE REGISTER THAT COUNTS CALENDAR DAYS IS NOW CONVERTED, ON THE
    # PROJECT'S OWN CALENDAR, BY THE ONE CONVERSION FUNCTION -- not by a rule of thumb and not
    # by this module counting days its own way. Run 107 left such a register Not Assessed
    # because no calendar reached the analytical layer.
    #
    # WHAT IS CONVERTIBLE AND WHAT IS NOT, stated rather than blurred. Conversion counts the
    # working days between the required-on-site DATE and the forecast delivery DATE. An item
    # whose dates were printed as calendar dates carries day ORDINALS here -- that is what
    # `canonical_v4._day` produces from an ISO date -- and those ordinals are real days on a
    # calendar, so they convert. An item that printed a day NUMBER on the schedule's own axis
    # while declaring a calendar-day basis carries no anchor date, and NOTHING CONVERTS IT: a
    # guess at which axis day is which calendar day would be an invented conversion.
    from .working_calendar import (CALENDAR_ABSENT_WORDS, read_project_calendar,
                                   working_days_between)
    _day_basis = reading.get("day_basis")
    _basis_ok = _day_basis == "approved_calendar_working_days"
    _cal = None if _basis_ok else read_project_calendar(si)
    _converted = []
    _convert_absent = None
    if not _basis_ok:
        if _day_basis is None:
            _convert_absent = (
                "the register does not state which kind of day it counts, so its dates cannot "
                "be read as working days and are not converted. WHAT IS NEEDED: a procurement "
                "register stating `day_basis` as either approved_calendar_working_days or "
                "calendar_days")
        elif _cal is None:
            _convert_absent = ("the register counts calendar days and " +
                               CALENDAR_ABSENT_WORDS)
    _items = []
    _worst_band = None
    _worst_item = None
    _uneval = []
    for it in reading["items"]:
        late = max(0.0, -it["slack_days"])
        crit = str(it.get("criticality") or "").strip().lower().replace(" ", "_")
        on_controlling = (True if crit in PROCUREMENT_CRITICALITY_CONTROLLING
                          else False if crit in PROCUREMENT_CRITICALITY_NOT else None)
        band = None
        why = None
        if not _basis_ok:
            # THE CONVERSION, ITEM BY ITEM. The dates are day ordinals where the register
            # printed dates. `required_on_site_day` is the start of travel and
            # `forecast_delivery_day` the end, so the working days between them, negated, is
            # the working-day slack -- the same sign convention the calendar-day slack above
            # already carries.
            if _convert_absent:
                why = _convert_absent
            elif not (_ORD_MIN <= it["required_on_site_day"] <= _ORD_MAX
                      and _ORD_MIN <= it["forecast_delivery_day"] <= _ORD_MAX):
                why = ("this item states its dates as day numbers on the schedule's own axis "
                       "while the register counts calendar days, so there is no calendar date "
                       "to count working days between and nothing is converted. WHAT IS "
                       "NEEDED: the required-on-site and forecast-delivery dates as calendar "
                       "dates")
            else:
                _wd_slack = -working_days_between(
                    _cal, it["required_on_site_day"], it["forecast_delivery_day"])
                late = max(0.0, -_wd_slack)
                _converted.append({"item_id": it["item_id"],
                                   "calendar_day_slack": it["slack_days"],
                                   "working_day_slack": _wd_slack})
        if why:
            pass
        elif late <= 0:
            band = "Green"
        elif late > 10:
            band = "Red"
        elif late >= 6:
            band = "Amber"
        elif on_controlling is None:
            why = ("this item is 1 to 5 working days late and the register does not state "
                   "whether it sits on controlling or near-critical work, so Yellow cannot be "
                   "told from Amber. Criticality is never guessed")
        else:
            band = "Amber" if on_controlling else "Yellow"
        # THE MILESTONE ARM OF RED. Stated by the item, never inferred.
        if it.get("causes_required_milestone_late") and late > 0:
            band = _OB.at_least_as_adverse_as(band, "Red")
        _items.append({"item_id": it["item_id"], "days_late": late,
                       "on_controlling_or_near_critical": on_controlling,
                       "band": band, "not_assessed_reason": why})
        if why:
            _uneval.append(it["item_id"])
        if band and (_worst_band is None
                     or _OB.BAND_ORDER.index(band) > _OB.BAND_ORDER.index(_worst_band)):
            _worst_band, _worst_item = band, it["item_id"]
    # THE HARD OVERRIDE, after item banding, able only to worsen.
    _override_items = [it["item_id"] for it in reading["items"]
                       if it.get("long_lead")
                       and it.get("protection_date_missed") is True]
    _override_stated = any(it.get("protection_date_missed") is not None
                           for it in reading["items"])
    _before = _worst_band
    if _override_items:
        _worst_band = _OB.at_least_as_adverse_as(_worst_band, "Red")
    _override_words = (
        "HARD OVERRIDE: Red when a long-lead item is not approved, released, fabricated or "
        "shipped by the latest date required to protect a contractual milestone, on the "
        "project's own schedule logic. The register must STATE that the protecting date was "
        "missed, because that date is a product of the project's schedule logic and this "
        "module holds no schedule. ")
    _override_words += (
        f"It fired on {_and_list(_override_items)}." if _override_items
        else "No item states it was missed, so it did not fire." if _override_stated
        else "No item states the fact either way, so the override was NOT EVALUABLE on this "
             "register and silence was not read as the condition being absent.")
    _boundary = (
        "per item, in approved-calendar working days, forecast delivery date less required-on-"
        "site date, with the MOST ADVERSE ITEM governing: Green where every item is on or "
        "before required-on-site; Yellow where an item is 1 to 5 working days late and NOT on "
        "controlling or near-critical work; Amber where an item is 6 to 10 days late, or 1 to 5 "
        "days late ON controlling or near-critical work; Red where an item is more than 10 "
        "working days late, or a late item causes a contractual or required milestone to "
        "forecast late. WHICH ITEMS SIT ON CONTROLLING OR NEAR-CRITICAL WORK IS STATED BY THE "
        "REGISTER ITSELF. WHERE THE REGISTER COUNTS CALENDAR DAYS the lateness is CONVERTED to "
        "working days on this project's own stated calendar, by the one conversion function "
        "every arm in this platform uses; where the project states no calendar, or an item "
        "printed a schedule-axis day number rather than a calendar date, that item is NOT "
        "ASSESSED and nothing is converted. Critical Path Analysis identifies those activities, but no path "
        "exists in this platform for one module's reading to reach another module's runner -- "
        "the only cross-module channel carries a module id, a method class and a status colour "
        "and no figures -- so criticality is read from the register or the arm that needs it is "
        "not evaluated. Criticality is never guessed. " + _override_words)
    _fields = {
        "items": reading["items"],
        "item_count": reading["item_count"],
        "minimum_slack_days": reading["minimum_slack_days"],
        "worst_item_id": reading["worst_item_id"],
        "mean_slack_days": round(reading["mean_slack_days"], 2),
        "state_counts": states,
        "day_basis": reading.get("day_basis"),
        "day_basis_converted_on_calendar": bool(_converted),
        "working_calendar_id": (_cal or {}).get("calendar_id"),
        "converted_item_slacks": _converted,
        "band_item_postures": _items,
        "band_items_not_assessed": _uneval,
        "band_governing_item_id": _worst_item,
        "band_posture_before_override": _before,
        "band_hard_override_fired": bool(_override_items),
        "band_hard_override_evaluable": _override_stated,
        "band_aggregation_rule": "most adverse item",
        "canonical_structure": "procurement_items",
        "source": reading["source"],
    }
    _msg = (
        f"Across {_js_str(reading['item_count'])} procurement items the tightest slack is "
        f"{_js_str(reading['minimum_slack_days'])} days, on the item called "
        f"{reading['worst_item_id']}. {_js_str(states['LATE'])} items are forecast to arrive "
        f"after they are required, {_js_str(states['AT_RISK'])} arrive inside the float that "
        f"protects them and {_js_str(states['ON_TIME'])} arrive with room to spare. Every item "
        f"is counted once.")
    _a49_basis = (
        "the owner's Run 107 order, section 2, A4.9. The band basis identifier is "
        "`owner_configured_construction_control_tolerance`. OWNER-CALIBRATED: no published "
        "standard fixes 5 and 10 working days, nor the criticality split between Yellow and "
        "Amber. They are a documented owner tolerance")
    if _worst_band is None:
        return band_abstained(
            "Procurement_Lead_Time", _msg,
            reason=("Not Assessed. No item on this register could be banded on the owner's "
                    "ladder: "
                    + "; ".join(sorted({i["not_assessed_reason"] for i in _items
                                        if i["not_assessed_reason"]}))
                    + ". No day count is converted between bases and no criticality is "
                      "guessed."),
            band_basis_id="owner_configured_construction_control_tolerance",
            **_fields)
    return banded(
        "Procurement_Lead_Time", _msg,
        status_color=_worst_band,
        boundary=_boundary
        + (f" {len(_uneval)} of {reading['item_count']} items could not be banded and are "
           f"absent from the aggregation rather than counted as favourable."
           if _uneval else ""),
        basis=_a49_basis,
        provenance=PROVENANCE_OWNER_CALIBRATED,
        threshold_source=THRESHOLD_SOURCE_OWNER,
        band_basis_id="owner_configured_construction_control_tolerance",
        **_fields)




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
}

A5_EXTENSIONS: dict[str, tuple[str, Callable]] = {
}

A6_EXTENSIONS: dict[str, tuple[str, Callable]] = {
    "A6.1": ("Quality_Compliance", run_quality_compliance),
    "A6.2": ("Safety_Performance", run_safety_performance),
    "A6.3": ("Environmental_Compliance", run_environmental_compliance),
    "A6.4": ("Contractor_Performance", run_contractor_performance),
}
