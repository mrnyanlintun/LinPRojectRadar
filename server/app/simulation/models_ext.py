"""
A-group extension models: the remaining A2 (schedule) and A3 (cost) modules.

Ported from assets/js/simulations.js Stage-2 ("Cat 2 — Schedule extensions", "Cat 3 — Cost
extensions" and the derived-field / dormant-module sections), validated numerically against the
JavaScript executed in a browser. See VALIDATION.md for the per-module comparison.

All sixteen are deterministic: signalInputs in, a result dict out. None draws from the generator;
`rand` is accepted only so every module keeps the registry's one call signature.

Porting hazards that shaped this file:

- `new Date('YYYY-MM-DD')` in JavaScript parses as UTC midnight. `_js_date_ms` reproduces that
  for date-only and ISO datetime strings and returns None for anything else, which is where the
  JavaScript's NaN-date paths land.
- `si.spi || 1.0` is JavaScript truthiness: 0, null and undefined all fall back. `_or_default`
  reproduces it; `num(..., default)` would keep a literal 0 and diverge.
- Math.round is half-up (ties toward +Infinity); Python's round() is banker's. Everything here
  rounds through js_round/round1/round2 from rng.py.
- `x.toLocaleString()` on an en-US browser groups thousands with commas; evidence strings use
  Python's f"{...:,}" which matches for the integers produced by Math.round.
"""

from __future__ import annotations

import math
import re
from typing import Any, Callable

from .models import (
    ABSTAIN_INVALID_DENOMINATOR, ABSTAIN_MALFORMED_INPUT, ABSTAIN_MISSING_INPUT,
    ABSTAIN_NOT_APPLICABLE,
    check_inputs, eligible, insufficient, refuse,
)
from .rng import clamp, js_round, num, round1, round2

_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")

# Days from the epoch to the start of each month (non-leap); used for the UTC millisecond
# arithmetic below rather than the datetime module, keeping this file free of any object that
# could tempt a later edit toward the system clock.
_CUM_DAYS = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)


def _days_from_epoch(y: int, m: int, d: int) -> int:
    days = 0
    yy = 1970
    while yy < y:
        days += 366 if _is_leap(yy) else 365
        yy += 1
    days += _CUM_DAYS[m - 1]
    if m > 2 and _is_leap(y):
        days += 1
    return days + (d - 1)


def _is_leap(y: int) -> bool:
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def _js_date_ms(value) -> float | None:
    """
    Milliseconds since the epoch as `new Date(value).getTime()` would produce, or None where the
    JavaScript would produce NaN. Date-only strings are UTC midnight, exactly as JavaScript
    parses them. Datetime strings are out of scope on purpose: the instrument's signalInputs
    carry date-only strings, and a 'T' form without a zone parses as LOCAL time in JavaScript,
    which is precisely the hazard VALIDATION.md flags — refuse it rather than guess.
    """
    if value is None:
        return None
    s = str(value)
    m = _DATE_RE.match(s)
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= mo <= 12 and 1 <= d <= 31):
        return None
    return float(_days_from_epoch(y, mo, d) * 86400000)


def _or_default(value, default):
    """JavaScript `value || default`: 0, NaN, null and undefined all fall back."""
    n = num(value, None)
    return default if n is None or n == 0 else n


def _js_str(n) -> str:
    """A number as JavaScript string-concatenation renders it: integers without a decimal."""
    if isinstance(n, float) and n.is_integer():
        return str(int(n))
    return str(n)


def _grouped(v) -> str:
    """Math.round(v).toLocaleString() on an en-US browser."""
    return f"{int(js_round(v)):,}"


def _money(v) -> str:
    return "$" + _grouped(v)


def _round3(v: float) -> float:
    return js_round(v * 1000) / 1000


def _derived(si: dict, *fields: str) -> bool:
    """The JavaScript `si.sources && sources[f].docType === 'derived'` guard, over any field."""
    sources = si.get("sources")
    if not sources:
        return False
    for f in fields:
        src = sources.get(f)
        if src and src.get("docType") == "derived":
            return True
    return False


# ------------------------------------------------------------ A2.4 Schedule Compression Index


def run_schedule_compression(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 7. Three substitutions, all removed.

    1. The schedule index came through `_or_default(..., 1.0)`, JavaScript truthiness, so an
       index of exactly zero and an index never reported both became an index of one, the value
       of a project running exactly to plan. It is now required and must be above zero: at zero
       there is no rate of progress for remaining work to be delivered at, so no compression
       ratio exists.
    2. The available days were floored at one day, `max(available_days, 1)`. That floor is why
       the same index gave a different ratio on a long baseline and a short one, which the
       known-answer run recorded as a failure of scale invariance: a year-long baseline at an
       index of 0.50 read 2.0 and Red, a two-day baseline at the SAME index read 1.0 and Green.
       With the floor removed the ratio is required over available, which is one over the index,
       and it is invariant under scaling the duration, as the stated ratio always should have
       been. This is an arithmetic correction to the stated proxy, not a new method.
    3. A project with no remaining work returned a ratio of one, which banded Green. There is no
       compression to measure when there is nothing left to compress: that is not applicable
       rather than comfortable, and it abstains.
    """
    if not check_inputs(si, ("baselineEnd", "baselineStart", "actualPctComplete")):
        return insufficient("Schedule_Compression",
                            "Insufficient data: the baseline dates and the reported percent "
                            "complete are needed to measure compression, and at least one of "
                            "them has not been reported for this period.",
                            ABSTAIN_MISSING_INPUT)
    verdict = eligible(si, positive=(("spi", "the schedule performance index"),))
    if verdict:
        return refuse("Schedule_Compression", verdict)
    end_ms = _js_date_ms(si.get("baselineEnd"))
    start_ms = _js_date_ms(si.get("baselineStart"))
    if end_ms is None or start_ms is None:
        return insufficient("Schedule_Compression",
                            "Insufficient data: a baseline date was reported in a form that is "
                            "not a date.",
                            ABSTAIN_MALFORMED_INPUT)
    total_days = (end_ms - start_ms) / 86400000
    if total_days <= 0:
        return insufficient("Schedule_Compression",
                            "Insufficient data: the baseline finish is not after the baseline "
                            "start, so the baseline has no duration to compress.",
                            ABSTAIN_MALFORMED_INPUT)
    remaining_pct = (100 - si["actualPctComplete"]) / 100
    remaining_days = total_days * remaining_pct
    if remaining_days <= 0:
        return insufficient("Schedule_Compression",
                            "No remaining work is reported for this project, so there is no "
                            "remaining duration to compress and no ratio to report.",
                            ABSTAIN_NOT_APPLICABLE)
    spi = num(si.get("spi"), None)
    required_days = remaining_days
    available_days = remaining_days * spi
    ratio = required_days / available_days
    ratio = round2(ratio)
    color = ("Green" if ratio <= 1.05 else "Yellow" if ratio <= 1.15
             else "Amber" if ratio <= 1.30 else "Red")
    return {
        "method_class": "Schedule_Compression",
        "status_color": color,
        "compression_ratio": ratio,
        "remaining_days": int(js_round(remaining_days)),
        "evidence_metric": (
            f"Schedule compression: {_js_str(ratio)}x, "
            f"{int(js_round(remaining_days))} days of work remaining"
        ),
    }


# ------------------------------------------------------------ A2.5 Float Consumption Rate


def run_float_consumption(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    THE FIFTEEN DEFECTS, defect 10, and it is one of the permanent abstentions.

    The whole computation is a comparison of float consumed against work completed: consuming
    forty per cent of the float by forty per cent completion is on plan, and consuming it by ten
    per cent completion is not. When completion was absent, `_or_default(..., 50)` supplied FIFTY
    PER CENT, so the comparison was made against a completion figure nobody had reported. Every
    project without a pay application or a monthly report was measured against an invented
    halfway point, and the stress ratio, which is the only thing this computation outputs and the
    only thing its bands read, was that invention divided into a real number.

    The fallback is removed and completion is required. Note what that means honestly: this
    computation reads total and consumed float from a schedule update, which is float derived
    from an activity network with logic and durations. The document corpus does not carry one,
    and the programme's deferred list records building one as a second corpus programme rather
    than a fix. So this computation is expected to abstain on the real corpus for the
    foreseeable future, and abstaining is the correct outcome, not a failure of this run.
    """
    if not check_inputs(si, ("totalFloat", "consumedFloat")):
        return insufficient("Float_Consumption")
    float_remaining = si["totalFloat"] - si["consumedFloat"]
    if not si["totalFloat"] > 0:
        return insufficient(
            "Float_Consumption",
            "No positive total float is recorded, so no consumption rate is measurable")
    consumption_rate = si["consumedFloat"] / si["totalFloat"]
    pct_complete = num(si.get("actualPctComplete"), None)
    if pct_complete is None or not pct_complete > 0:
        return insufficient(
            "Float_Consumption",
            "Awaiting a reported completion percentage: float consumption is only meaningful "
            "against the work actually completed")
    expected = pct_complete / 100
    stress = round2(consumption_rate / max(expected, 0.01))
    color = ("Green" if stress <= 1.0 else "Yellow" if stress <= 1.3
             else "Amber" if stress <= 1.6 else "Red")
    return {
        "method_class": "Float_Consumption",
        "status_color": color,
        "float_remaining_days": int(js_round(float_remaining)),
        "consumption_rate": int(js_round(consumption_rate * 100)),
        "float_stress": stress,
        "evidence_metric": (
            f"Float: {int(js_round(float_remaining))} days remaining, "
            f"{int(js_round(consumption_rate * 100))}% consumed"
        ),
    }


# ------------------------------------------------------------ A2.6 S-Curve Deviation


def run_scurve_deviation(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("actualPctComplete", "plannedPctComplete", "ev", "pv")):
        return insufficient("SCurve_Deviation")
    pct_dev = si["actualPctComplete"] - si["plannedPctComplete"]
    if not si["pv"] > 0:
        return insufficient("SCurve_Deviation")
    value_dev = ((si["ev"] - si["pv"]) / si["pv"]) * 100
    combined = (pct_dev + value_dev) / 2
    color = ("Green" if combined >= -2 else "Yellow" if combined >= -5
             else "Amber" if combined >= -10 else "Red")
    return {
        "method_class": "SCurve_Deviation",
        "status_color": color,
        "pct_deviation": round1(pct_dev),
        "value_deviation": round1(value_dev),
        "evidence_metric": (
            f"S-curve: {_js_str(round1(pct_dev))}% behind planned progress, "
            f"{_js_str(round1(value_dev))}% EV vs PV deviation"
        ),
    }


# ------------------------------------------------------------ A2.7 Milestone Trend Analysis


def run_milestone_trend(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    mh = si.get("milestoneHistory")
    if not isinstance(mh, list) or len(mh) < 2:
        return insufficient("Milestone_Trend",
                            "Awaiting a second schedule update (2 snapshots needed)")
    latest, prev = mh[-1], mh[-2]
    prev_by_name: dict[str, float] = {}
    for m in (prev or {}).get("milestones") or []:
        if m and m.get("name"):
            ms = _js_date_ms(m.get("forecast"))
            if ms is not None:
                prev_by_name[m["name"]] = ms
    matched = []
    worst_slip = -math.inf
    worst_name = None
    sum_slip = 0.0
    for m in (latest or {}).get("milestones") or []:
        if not m or not m.get("name"):
            continue
        lf = _js_date_ms(m.get("forecast"))
        pf = prev_by_name.get(m["name"])
        if lf is None or pf is None:
            continue
        slip = int(js_round((lf - pf) / 86400000))
        matched.append({"name": m["name"], "slip": slip})
        sum_slip += slip
        if slip > worst_slip:
            worst_slip = slip
            worst_name = m["name"]
    if not matched:
        return insufficient("Milestone_Trend", "Milestone names not comparable across periods")
    mean_slip = sum_slip / len(matched)
    color = ("Green" if mean_slip <= 0 else "Yellow" if mean_slip <= 7
             else "Amber" if mean_slip <= 14 else "Red")
    # One badly slipping milestone must not hide inside the average.
    if worst_slip > 21 and color in ("Green", "Yellow"):
        color = "Amber"

    def slip_str(d: float) -> str:
        d = round1(d)
        return ("+" if d >= 0 else "") + _js_str(d) + "d"

    def period_of(s) -> str:
        return str((s or {}).get("at") or "")[:7] or "?"

    n = len(matched)
    return {
        "method_class": "Milestone_Trend",
        "status_color": color,
        "mean_slip_days": round1(mean_slip),
        "worst_slip_days": int(worst_slip),
        "worst_milestone": worst_name,
        "matched_count": n,
        "evidence_metric": (
            f"{n} milestone{'' if n == 1 else 's'} matched "
            f"{period_of(prev)}→{period_of(latest)}; mean slip {slip_str(mean_slip)}; "
            f"worst '{worst_name}' {slip_str(worst_slip)}"
        ),
    }


# ------------------------------------------------------------ A2.8 Look-Ahead Schedule Health


def run_lookahead_health(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("activitiesPlanned", "activitiesConstrained")):
        return insufficient("Lookahead_Health")
    planned = si["activitiesPlanned"]
    constrained = si["activitiesConstrained"]
    # THE ABSTENTION GUARDS. Run 4 (validate the seven). `planned` is the denominator, and a
    # look-ahead window with no activities planned in it used to substitute a rate of zero,
    # which is the best band this module has: a project reporting nothing to do was reported as
    # having nothing constrained. A count of constrained activities larger than the count
    # planned, or a negative count, is outside the domain of a ratio of one to the other and is
    # a reading error in the document rather than a condition of the project.
    if not planned > 0:
        return insufficient(
            "Lookahead_Health",
            "Awaiting a look-ahead window with activities planned in it: a constraint rate has "
            "no denominator without one",
        )
    if constrained < 0 or constrained > planned:
        return insufficient(
            "Lookahead_Health",
            "Awaiting a constrained count that lies within the planned count: the figures read "
            "from the look-ahead schedule cannot both be right",
        )
    rate = constrained / planned
    is_derived = _derived(si, "activitiesPlanned")
    # THE BAND, AND WHAT IT IS SOURCED TO: NOTHING. Run 4 (validate the seven) looked for a
    # source that specifies these numbers for a constraint rate and did not find one. The lean
    # construction literature does publish numeric benchmarks for plan reliability -- Ballard,
    # H. G., "The Last Planner System of Production Control", PhD thesis, University of
    # Birmingham, 2000, reports percent plan complete rising from around half to around seventy
    # per cent -- but percent plan complete is the share of committed tasks actually finished,
    # which is a different measurement from the share of look-ahead activities carrying an open
    # constraint. Citing it here would attach a number to a quantity it was not measured on.
    # The boundaries are therefore left exactly as they were, uncited, and this module DOES NOT
    # VOTE on category or project status. See registry.CORE_VOTING_MODULES.
    color = ("Green" if rate <= 0.10 else "Yellow" if rate <= 0.25
             else "Amber" if rate <= 0.40 else "Red")
    return {
        "method_class": "Lookahead_Health",
        "status_color": color,
        "constraint_rate": int(js_round(rate * 100)),
        "constrained": constrained,
        "planned": planned,
        "evidence_metric": (
            f"{_js_str(constrained)} of {_js_str(planned)} planned activities constrained "
            f"({int(js_round(rate * 100))}%)"
            + (" (estimated; upload Look-Ahead Schedule for precise figures)" if is_derived else "")
        ),
    }


# ------------------------------------------------------------ A2.9 Resource Loading Index


def run_resource_loading(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("plannedLaborHours", "actualLaborHours")):
        return insufficient("Resource_Loading")
    planned = num(si.get("plannedLaborHours"), 0)
    actual = num(si.get("actualLaborHours"), 0)
    if planned <= 0:
        return insufficient("Resource_Loading", "Planned labor hours not available")
    ratio = actual / planned
    if 0.90 <= ratio <= 1.10:
        color = "Green"
    elif 0.80 <= ratio < 0.90 or 1.10 < ratio <= 1.20:
        color = "Yellow"
    elif 0.70 <= ratio < 0.80 or 1.20 < ratio <= 1.35:
        color = "Amber"
    else:
        color = "Red"
    return {
        "method_class": "Resource_Loading",
        "status_color": color,
        "load_ratio": round2(ratio),
        "evidence_metric": (
            f"Actual {_grouped(actual)}h vs planned {_grouped(planned)}h "
            f"(ratio {_js_str(round2(ratio))})"
        ),
    }


# ------------------------------------------------------------ A2.10 Schedule Risk Analysis P80


def run_schedule_risk(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("spi", "baselineEnd", "baselineStart", "actualPctComplete")):
        return insufficient("Schedule_Risk_Analysis")
    end_ms = _js_date_ms(si.get("baselineEnd"))
    start_ms = _js_date_ms(si.get("baselineStart"))
    if end_ms is None or start_ms is None:
        return insufficient("Schedule_Risk_Analysis")
    total_days = (end_ms - start_ms) / 86400000
    if total_days <= 0:
        return insufficient("Schedule_Risk_Analysis")
    remaining_days = total_days * (100 - si["actualPctComplete"]) / 100
    p50_days = remaining_days / si["spi"]
    uncertainty = max(0.05, 1 - si["spi"]) * 0.5
    p80_days = p50_days * (1 + uncertainty * 1.28)
    delay_days = int(js_round(p80_days - remaining_days))
    color = ("Green" if delay_days <= 0 else "Yellow" if delay_days <= 14
             else "Amber" if delay_days <= 30 else "Red")
    return {
        "method_class": "Schedule_Risk_Analysis",
        "status_color": color,
        "p50_delay_days": int(js_round(p50_days - remaining_days)),
        "p80_delay_days": delay_days,
        "evidence_metric": f"SRA P80 delay: {delay_days} days beyond baseline",
    }


# ------------------------------------------------------------ A2.11 Critical Path Index


def run_critical_path_index(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 7. The index is the average of two things: progress against plan, and the schedule
    index. Where no planned progress had been reported the first of the two was replaced by the
    second, so the average became the schedule index averaged with itself and the module reported
    a two-input measure it had one input for. On a project with no planned progress that produced
    Amber. Planned progress is now required to be above zero, because it is the denominator of
    the ratio, and the module abstains rather than quietly reporting a different measure under
    the same name.
    """
    if not check_inputs(si, ("spi", "plannedPctComplete", "actualPctComplete")):
        return insufficient("Critical_Path_Index",
                            "Insufficient data: the schedule performance index and both the "
                            "planned and reported percent complete are needed, and at least one "
                            "of them has not been reported for this period.",
                            ABSTAIN_MISSING_INPUT)
    verdict = eligible(si, positive=(("plannedPctComplete", "the planned percent complete"),))
    if verdict:
        return refuse("Critical_Path_Index", verdict)
    progress_ratio = si["actualPctComplete"] / si["plannedPctComplete"]
    cpi_schedule = si["spi"]
    index = _round3((progress_ratio + cpi_schedule) / 2)
    color = ("Green" if index >= 0.95 else "Yellow" if index >= 0.92
             else "Amber" if index >= 0.88 else "Red")
    return {
        "method_class": "Critical_Path_Index",
        "status_color": color,
        "critical_path_index": index,
        "evidence_metric": f"Critical Path Index: {_js_str(index)}",
    }


# ------------------------------------------------------------ A3.2 Contingency Burn Rate


def run_contingency_burn(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("originalContingency", "remainingContingency", "actualPctComplete")):
        return insufficient("Contingency_Burn_Rate")
    burned = si["originalContingency"] - si["remainingContingency"]
    if not si["originalContingency"] > 0:
        return insufficient(
            "Contingency_Burn_Rate",
            "Awaiting an original contingency amount above zero: the share consumed has no "
            "denominator without one",
        )
    # THE ABSTENTION GUARDS. Run 4 (validate the seven). Two denominators and one domain.
    # Percent complete is the second denominator, and at zero per cent complete the code
    # substituted the raw burn share for the ratio of burn to progress, which is a different
    # quantity reported under the same name and lands in the calmest band whenever nothing has
    # been burned yet. A remaining contingency above the original, or below zero, is outside the
    # domain: it makes the consumed share negative or greater than one.
    if si["remainingContingency"] < 0 or si["remainingContingency"] > si["originalContingency"]:
        return insufficient(
            "Contingency_Burn_Rate",
            "Awaiting a remaining contingency that lies between zero and the original amount: "
            "the figures read from the pay application cannot both be right",
        )
    burn_rate = burned / si["originalContingency"]
    expected = si["actualPctComplete"] / 100
    if not expected > 0:
        return insufficient(
            "Contingency_Burn_Rate",
            "Awaiting reported progress above zero: contingency consumption is compared against "
            "how much of the work is complete, and there is nothing to compare it against yet",
        )
    stress = round2(burn_rate / expected)
    # THE BAND, AND WHAT IT IS SOURCED TO: NOTHING. Run 4 looked and did not find a source
    # specifying 1.0, 1.3 and 1.6 for contingency consumption against progress. AACE
    # International's contingency recommended practices treat contingency as an amount
    # determined by risk analysis, and the risk exposure a contingency covers is not spread
    # evenly across a project's duration, so the premise the 1.0 boundary rests on -- that
    # contingency should be consumed in proportion to progress -- is not only uncited, it is
    # not what the literature describes. The boundaries are left as they were, uncited, and
    # this module DOES NOT VOTE. See registry.CORE_VOTING_MODULES.
    color = ("Green" if stress <= 1.0 else "Yellow" if stress <= 1.3
             else "Amber" if stress <= 1.6 else "Red")
    is_derived = _derived(si, "originalContingency", "remainingContingency")
    return {
        "method_class": "Contingency_Burn_Rate",
        "status_color": color,
        "burn_rate_pct": int(js_round(burn_rate * 100)),
        "remaining_pct": int(js_round((1 - burn_rate) * 100)),
        "burn_stress": stress,
        "evidence_metric": (
            f"Contingency: {int(js_round(burn_rate * 100))}% burned at "
            f"{int(js_round(si['actualPctComplete']))}% complete"
            + (" (estimated; upload Pay Application contingency detail for precise figures)"
               if is_derived else "")
        ),
    }


# ------------------------------------------------------------ A3.3 Labor Productivity Index


def run_labor_productivity(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("plannedLaborHours", "actualLaborHours", "actualPctComplete")):
        return insufficient("Labor_Productivity")
    planned = num(si.get("plannedLaborHours"), 0)
    actual = num(si.get("actualLaborHours"), 0)
    pct = num(si.get("actualPctComplete"), 0)
    if actual <= 0:
        return insufficient("Labor_Productivity", "Actual labor hours not available")
    rate = round2(((pct / 100) * planned) / actual)
    color = ("Green" if rate >= 0.95 else "Yellow" if rate >= 0.85
             else "Amber" if rate >= 0.75 else "Red")
    return {
        "method_class": "Labor_Productivity",
        "status_color": color,
        "earned_hours_rate": rate,
        "evidence_metric": (
            f"Earned-hours rate {_js_str(rate)} ({_js_str(round1(pct))}% × "
            f"{_grouped(planned)}h planned ÷ {_grouped(actual)}h actual)"
        ),
    }


# ------------------------------------------------------------ A3.4 Material Cost Variance


def run_material_cost_variance(si: dict, rand: Callable[[], float],
                               period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("materialCostBaseline", "materialCostCurrent")):
        return insufficient("Material_Cost_Variance")
    # THE ABSTENTION GUARDS. Run 4 (validate the seven). The comparison is material cost to
    # date against the share of the material baseline the project's progress has earned, so
    # percent complete is part of the arithmetic and not an optional refinement. When it was
    # absent the code compared cost to date against the WHOLE baseline, which is the same as
    # assuming the project is finished: every project mid-way through then reads as a large
    # underrun. That is a substituted input, not a missing one, and it abstains now. The
    # expected amount is also the denominator, so it must be above zero.
    if si.get("actualPctComplete") is None:
        return insufficient(
            "Material_Cost_Variance",
            "Awaiting reported progress: material cost to date is compared against the share of "
            "the material baseline the work completed has earned, and that share is not known",
        )
    pct = si["actualPctComplete"] / 100
    expected = si["materialCostBaseline"] * pct
    if not expected > 0:
        return insufficient(
            "Material_Cost_Variance",
            "Awaiting a material baseline and reported progress above zero: there is no expected "
            "material cost at this point to compare the cost to date against",
        )
    variance = (si["materialCostCurrent"] - expected) / expected
    variance = _round3(variance)
    is_derived = _derived(si, "materialCostBaseline")
    a = abs(variance)
    # THE BAND, AND WHAT IT IS SOURCED TO: NOTHING. Run 4 looked. AACE International's cost
    # estimate classification recommended practice (18R-97) does publish numeric accuracy ranges
    # by estimate class, and it is tempting to read five and twenty per cent off them, but those
    # ranges describe how far an ESTIMATE may sit from the eventual cost at the point it is
    # prepared. They are not control limits for a variance measured mid-execution against a
    # progress-adjusted baseline, and using them as such would attach a published number to a
    # quantity it was not measured on. The boundaries are left as they were, uncited, and this
    # module DOES NOT VOTE. See registry.CORE_VOTING_MODULES.
    color = ("Green" if a <= 0.05 else "Yellow" if a <= 0.12
             else "Amber" if a <= 0.20 else "Red")
    return {
        "method_class": "Material_Cost_Variance",
        "status_color": color,
        "variance_pct": int(js_round(variance * 100)),
        "evidence_metric": (
            f"Material cost variance: {'+' if variance >= 0 else ''}"
            f"{int(js_round(variance * 100))}% vs expected at current progress"
            + (" (estimated at 40% of BAC/AC; upload Cost Report for precise figures)"
               if is_derived else "")
        ),
    }


# ------------------------------------------------------------ A3.5 Overhead Absorption Rate


def run_overhead_absorption(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 7. An indirect plan of zero, or a plan scaled by a reported completion of zero, made the
    denominator zero and the absorption ratio was substituted as exactly 1, which is the value of
    a project absorbing overhead precisely as planned, and which banded Green. There is no
    planned indirect cost to absorb against in that state, so no absorption ratio exists and the
    module refuses. The proxy itself is unchanged: it remains a ratio of actual indirect cost to
    a progress-scaled indirect plan, with the qualifier it already carries about whether the plan
    is a total or a period figure.
    """
    if not check_inputs(si, ("indirectCostPlan", "indirectCostActual")):
        return insufficient("Overhead_Absorption",
                            "Insufficient data: the planned and actual indirect cost figures "
                            "are needed, and at least one of them has not been reported for "
                            "this period.",
                            ABSTAIN_MISSING_INPUT)
    pct = si["actualPctComplete"] / 100 if si.get("actualPctComplete") is not None else None
    planned = si["indirectCostPlan"] * pct if pct is not None else si["indirectCostPlan"]
    if not (planned > 0):
        return insufficient("Overhead_Absorption",
                            "Insufficient data: the planned indirect cost at this project's "
                            "reported progress is zero or below, so there is nothing to absorb "
                            "against and no absorption ratio can be formed. No substitute "
                            "figure is used in its place.",
                            ABSTAIN_INVALID_DENOMINATOR)
    absorption = si["indirectCostActual"] / planned
    absorption = _round3(absorption)
    is_derived = _derived(si, "indirectCostPlan")
    color = ("Green" if absorption <= 1.05 else "Yellow" if absorption <= 1.15
             else "Amber" if absorption <= 1.30 else "Red")
    return {
        "method_class": "Overhead_Absorption",
        "status_color": color,
        "absorption_ratio": absorption,
        "evidence_metric": (
            f"Overhead absorption: {int(js_round(absorption * 100))}% of planned indirect cost "
            f"at current progress"
            + (" (estimated at 12% overhead; upload Cost Report for precise figures)"
               if is_derived else "")
        ),
    }


# ------------------------------------------------------------ A3.6 Cost Risk Analysis P80


def run_cost_risk(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    THE FIFTEEN DEFECTS, defect 5, and STRICTLY the domain crash.

    `bac / cpi` had no guard at all, so a cost performance index of exactly zero raised inside
    the computation rather than abstaining, and every project-level result of that run was lost
    to an exception rather than to one module's stated abstention. A zero index abstains now,
    as it already did in the four other computations that divide by it, and a zero or negative
    budget abstains with it because the delta below is a percentage OF that budget.

    THE METHOD IS NOT REBUILT AND MUST NOT BE. The eightieth percentile here is a deterministic
    inflation of the current index, not a cost risk analysis over a risk register, and the
    owner's open items already record that this computation cannot consume register data without
    changing its arithmetic. That is a different piece of work with a different owner. Fixing the
    crash is in scope; making this a real analysis is not.
    """
    if not check_inputs(si, ("bac", "cpi", "ac", "ev")):
        return insufficient("Cost_Risk_Analysis")
    if si["cpi"] <= 0:
        return insufficient(
            "Cost_Risk_Analysis",
            "Cost performance is recorded as zero or below, which no forecast can be scaled by")
    if si["bac"] <= 0:
        return insufficient(
            "Cost_Risk_Analysis",
            "No positive budget at completion is recorded to measure an overrun against")
    eac = si["bac"] / si["cpi"]
    uncertainty = max(0.03, abs(1 - si["cpi"])) * 0.5
    p80_eac = eac * (1 + uncertainty * 1.28)
    p80_delta_pct = ((p80_eac - si["bac"]) / si["bac"]) * 100
    color = ("Green" if p80_delta_pct <= 5 else "Yellow" if p80_delta_pct <= 10
             else "Amber" if p80_delta_pct <= 20 else "Red")
    return {
        "method_class": "Cost_Risk_Analysis",
        "status_color": color,
        "p80_eac": int(js_round(p80_eac)),
        "p80_delta_pct": round1(p80_delta_pct),
        "evidence_metric": (
            f"CRA P80 EAC: {_money(p80_eac)} (+{_js_str(round1(p80_delta_pct))}% BAC)"
        ),
    }


# ------------------------------------------------------------ A3.7 Analogous Estimating Ratio


def run_analogous_estimating(si: dict, rand: Callable[[], float],
                             period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("analogousOverrunPct", "bac")):
        return insufficient("Analogous_Estimating")
    pct = num(si.get("analogousOverrunPct"), 0)
    bac = num(si.get("bac"), 0)
    exposure = bac * pct / 100
    color = ("Green" if pct < 3 else "Yellow" if pct < 7 else "Amber" if pct < 12 else "Red")
    return {
        "method_class": "Analogous_Estimating",
        "status_color": color,
        "analogous_overrun_pct": round1(pct),
        "bac_exposure": int(js_round(exposure)),
        "evidence_metric": (
            f"Analogous overrun {_js_str(round1(pct))}% → {_money(exposure)} BAC exposure"
        ),
    }


# ------------------------------------------------------------ A3.8 Parametric Cost Index


def run_parametric_cost(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("bac", "ev", "ac", "actualPctComplete")):
        return insufficient("Parametric_Cost")
    # The JavaScript divides by si.cpi without listing it as required: a missing cpi produces a
    # NaN index, which its falsy-check then routes to insufficient. Reproduced explicitly.
    cpi = num(si.get("cpi"), None)
    if cpi is None or cpi == 0:
        return insufficient("Parametric_Cost")
    eac_cpi = si["bac"] / cpi
    eac_parametric = si["ac"] + (si["bac"] - si["ev"])
    if not eac_parametric > 0:
        return insufficient("Parametric_Cost")
    index = _round3(eac_cpi / eac_parametric)
    if index == 0:
        return insufficient("Parametric_Cost")
    a = abs(index - 1)
    color = ("Green" if a <= 0.03 else "Yellow" if a <= 0.08
             else "Amber" if a <= 0.15 else "Red")
    return {
        "method_class": "Parametric_Cost",
        "status_color": color,
        "parametric_index": index,
        "evidence_metric": f"Parametric index: {_js_str(index)} (CPI-EAC vs BAC-EAC divergence)",
    }


# ------------------------------------------------------------ A3.9 Inflation Adjustment Index


def run_inflation_adjustment(si: dict, rand: Callable[[], float],
                             period_cutoff) -> dict[str, Any]:
    """
    RUN 7. A material baseline of zero, or a baseline scaled by a reported completion of zero,
    made the denominator zero and the escalation was substituted as exactly 0, which is the value
    of a project with no material escalation at all, and which banded Green. There is no
    progress-adjusted baseline to measure escalation above in that state, so the module refuses.
    The proxy is unchanged: still a ratio above a progress-adjusted baseline with no external
    price index, time base or geography, exactly as its qualifier says.
    """
    if not check_inputs(si, ("materialCostBaseline", "materialCostCurrent")):
        return insufficient("Inflation_Adjustment",
                            "Insufficient data: the baseline and current material cost figures "
                            "are needed, and at least one of them has not been reported for "
                            "this period.",
                            ABSTAIN_MISSING_INPUT)
    pct = si["actualPctComplete"] / 100 if si.get("actualPctComplete") is not None else None
    expected = si["materialCostBaseline"] * pct if pct is not None else si["materialCostBaseline"]
    if not (expected > 0):
        return insufficient("Inflation_Adjustment",
                            "Insufficient data: the material cost baseline at this project's "
                            "reported progress is zero or below, so there is no baseline for "
                            "current costs to have escalated above. No substitute figure is "
                            "used in its place.",
                            ABSTAIN_INVALID_DENOMINATOR)
    escalation = max(0, (si["materialCostCurrent"] - expected) / expected)
    escalation = _round3(escalation)
    is_derived = _derived(si, "materialCostBaseline")
    color = ("Green" if escalation <= 0.04 else "Yellow" if escalation <= 0.08
             else "Amber" if escalation <= 0.15 else "Red")
    return {
        "method_class": "Inflation_Adjustment",
        "status_color": color,
        "escalation_pct": int(js_round(escalation * 100)),
        "evidence_metric": (
            f"Material escalation proxy: +{int(js_round(escalation * 100))}% above "
            f"progress-adjusted baseline"
            + (" (estimated; upload Cost Report / price index for precise figures)"
               if is_derived else "")
        ),
    }


A2_EXTENSIONS: dict[str, tuple[str, Callable]] = {
    "A2.4": ("Schedule_Compression", run_schedule_compression),
    "A2.5": ("Float_Consumption", run_float_consumption),
    "A2.6": ("SCurve_Deviation", run_scurve_deviation),
    "A2.7": ("Milestone_Trend", run_milestone_trend),
    "A2.8": ("Lookahead_Health", run_lookahead_health),
    "A2.9": ("Resource_Loading", run_resource_loading),
    "A2.10": ("Schedule_Risk_Analysis", run_schedule_risk),
    "A2.11": ("Critical_Path_Index", run_critical_path_index),
}

A3_EXTENSIONS: dict[str, tuple[str, Callable]] = {
    "A3.2": ("Contingency_Burn_Rate", run_contingency_burn),
    "A3.3": ("Labor_Productivity", run_labor_productivity),
    "A3.4": ("Material_Cost_Variance", run_material_cost_variance),
    "A3.5": ("Overhead_Absorption", run_overhead_absorption),
    "A3.6": ("Cost_Risk_Analysis", run_cost_risk),
    "A3.7": ("Analogous_Estimating", run_analogous_estimating),
    "A3.8": ("Parametric_Cost", run_parametric_cost),
    "A3.9": ("Inflation_Adjustment", run_inflation_adjustment),
}
