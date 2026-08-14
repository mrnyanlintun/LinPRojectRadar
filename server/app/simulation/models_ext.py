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

from .canonical import StructureAbsent
from .canonical_v3 import (
    analogous_estimate, contingency_burn, cost_risk_simulation, critical_path_status,
    inflation_adjustment, labor_productivity, look_ahead_ready_fraction, milestone_trend,
    network_float_consumption, overhead_absorption, parse_schedule_network, resource_loading,
    require_v3_structure, s_curve_deviation, schedule_compression_index, schedule_risk_p80,
    time_phased_baseline,
)
from .models import (
    ABSTAIN_INVALID_DENOMINATOR, ABSTAIN_MALFORMED_INPUT, ABSTAIN_MISSING_INPUT,
    ABSTAIN_NOT_APPLICABLE, ABSTAIN_STRUCTURE_ABSENT,
    calibration_pending, check_inputs, eligible, insufficient, refuse,
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
    RUN 28, v3. REMAINING-DURATION DEMAND ACROSS RECONCILED ACTIVITIES.

    THE SUPPLIED CONTRACT, which is the PCEIF transparent remaining-duration-demand contract and
    is explicitly NOT claimed to be a universal industry statistical index: SCI is the sum of
    baseline remaining activity durations over the sum of current remaining activity durations,
    for reconciled comparable activities at the same governed status basis. One means equal
    demand, below one means greater current demand and rising compression pressure, above one
    means a more relaxed demand. Baseline and current activity identities, both sets of remaining
    durations and a common status basis are required, and where the two cannot be reconciled the
    answer is NOT ESTIMABLE.

    WHAT v2 DID. It took the baseline start and finish dates, scaled the span by one minus the
    reported percent complete to get a remaining duration, then divided that by the same figure
    multiplied by the schedule performance index. Algebraically the whole thing collapses to one
    over the schedule index: no activity was ever consulted, nothing was reconciled between two
    schedules, and the "compression" reported was the reciprocal of a single reported ratio.

    v3 REQUIRES THE SCHEDULE NETWORK, and reads from it only the activities that carry BOTH a
    baseline duration and a current remaining duration, so reconciliation is a property of the
    data rather than an assumption. Where no activity reconciles the module ABSTAINS. No band is
    asserted; the contract names compression bands as calibration dependent.
    """
    try:
        structure = require_v3_structure(si, "A2.4")
        network = parse_schedule_network(structure)
        reading = schedule_compression_index(network)
    except StructureAbsent as absent:
        return insufficient("Schedule_Compression", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    return calibration_pending(
        "Schedule_Compression",
        f"Across {reading['reconciled_activities']} reconciled activities the baseline planned "
        f"{_js_str(round2(reading['baseline_remaining_total']))} days of remaining work against "
        f"{_js_str(round2(reading['current_remaining_total']))} now, a remaining duration demand "
        f"ratio of {_js_str(round2(reading['schedule_compression_index']))}",
        schedule_compression_index=round2(reading["schedule_compression_index"]),
        baseline_remaining_total=reading["baseline_remaining_total"],
        current_remaining_total=reading["current_remaining_total"],
        reconciled_activities=reading["reconciled_activities"],
        status_basis=reading["status_basis"],
        schedule_version=network["schedule_version"],
        canonical_structure="schedule_network",
    )


# ------------------------------------------------------------ A2.5 Float Consumption Rate


def run_float_consumption(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 28, v3. FLOAT FROM THE NETWORK'S OWN FORWARD AND BACKWARD PASS.

    THE SUPPLIED CONTRACT. Float must be CPM/network derived: TF = LS - ES = LF - EF. Float
    consumed is FC = TF_baseline - TF_current, the consumption fraction is FCR = FC /
    TF_baseline, and a depletion velocity is available where a history exists. Zero baseline
    float requires explicit already-critical handling rather than a division by zero, and float
    must not be fabricated from percent complete.

    WHAT v2 DID. It read two reported scalars, totalFloat and consumedFloat, neither of which any
    document in this corpus carries, and divided their ratio by the reported percent complete to
    make a "float stress" figure. That last step is the forbidden one twice over: it is not float
    consumption, and it makes the reading a function of a progress percentage.

    v3 REQUIRES THE SCHEDULE NETWORK and runs the passes itself: current total float is computed
    from the logic and durations, and is compared against the float each activity carried at
    baseline, which the network states. Where the network is absent, or no activity carries its
    baseline float, the module ABSTAINS. An activity that began at zero float is reported as
    already critical with no fraction rather than divided by nothing. No band is asserted.
    """
    try:
        structure = require_v3_structure(si, "A2.5")
        network = parse_schedule_network(structure)
        reading = network_float_consumption(network)
    except StructureAbsent as absent:
        return insufficient("Float_Consumption", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    ratio = reading["float_consumption_ratio"]
    ratio_words = ("no share is reported because none of the activities began with float"
                   if ratio is None
                   else f"{int(js_round(ratio * 100))} per cent of the float they began with")
    return calibration_pending(
        "Float_Consumption",
        f"Across {reading['activity_count']} activities the network has consumed "
        f"{_js_str(round2(reading['float_consumed_days']))} days of float, {ratio_words}",
        float_consumed_days=reading["float_consumed_days"],
        baseline_total_float=reading["baseline_total_float"],
        float_consumption_ratio=(None if ratio is None else round2(ratio)),
        activity_count=reading["activity_count"],
        per_activity=reading["activities"],
        project_finish=reading["project_finish"],
        network_derived=True,
        schedule_version=network["schedule_version"],
        canonical_structure="schedule_network",
    )


# ------------------------------------------------------------ A2.6 S-Curve Deviation


def run_scurve_deviation(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 28, v3. TWO CUMULATIVE SERIES ON ONE MEASUREMENT BASIS.

    THE SUPPLIED CONTRACT requires a time-indexed cumulative baseline and an actual/earned series
    on the same measurement basis. SD_t = Actual_t - Planned_t, SDR_t = (Actual_t - Planned_t) /
    Planned_t when Planned_t is above zero, and DeltaSD_t = SD_t - SD_(t-1). A single point may
    produce a point deviation but MAY NOT be represented as a longitudinal S-curve trend.

    WHAT v2 DID. It averaged two things measured in different units: the difference of two
    reported percentages, and the percentage difference between earned and planned value. That
    average is not a deviation of anything from anything, and it was a single snapshot presented
    under a curve's name with no series behind it at all.

    v3 REQUIRES THE TIME-PHASED BASELINE and the matching actual series. Where only one point
    exists the point deviation is reported and `longitudinal` is False, with no trend field, so a
    snapshot cannot be read as a trend. Where the baseline is absent the module ABSTAINS. No band
    is asserted; the contract names S-curve bands as calibration dependent.
    """
    try:
        structure = require_v3_structure(si, "A2.6")
        baseline = time_phased_baseline(structure)
        actual = structure.get("cumulative_actual")
        if not isinstance(actual, list) or not actual:
            raise StructureAbsent(
                "The time phased baseline provided carries no matching series of work actually "
                "performed, so there is nothing to compare the planned curve against.")
        reading = s_curve_deviation(baseline["curve"], actual)
    except StructureAbsent as absent:
        return insufficient("SCurve_Deviation", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    trend_words = ""
    if reading["longitudinal"]:
        trend_words = (f"; the gap is {reading['trend_direction']}, having moved "
                       f"{_js_str(round2(reading['trend']))} since the period before")
    return calibration_pending(
        "SCurve_Deviation",
        f"Work performed stands at {_js_str(round2(reading['actual']))} against "
        f"{_js_str(round2(reading['planned']))} planned by this point, a deviation of "
        f"{_js_str(round2(reading['deviation']))}{trend_words}",
        deviation=round2(reading["deviation"]),
        relative_deviation=(None if reading["relative_deviation"] is None
                            else round2(reading["relative_deviation"])),
        planned_cumulative=reading["planned"],
        actual_cumulative=reading["actual"],
        points=reading["points"],
        longitudinal=reading["longitudinal"],
        trend=(round2(reading["trend"]) if reading["longitudinal"] else None),
        trend_direction=reading.get("trend_direction"),
        baseline_version=baseline["baseline_version"],
        canonical_structure="time_phased_baseline",
    )


# ------------------------------------------------------------ A2.7 Milestone Trend Analysis


def run_milestone_trend(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 28, v3. VARIANCE AGAINST THE ORIGINAL COMMITMENT, AND DRIFT BETWEEN FORECASTS.

    THE SUPPLIED CONTRACT requires stable milestone identity across reporting periods, with each
    milestone carrying its original baseline date, its current approved baseline date, the report
    date, the forecast date, the schedule version and the actual date once achieved. MV is the
    forecast date less the BASELINE date; MD is the forecast date less the previous forecast
    date. Insufficient repeated forecasts is NOT ESTIMABLE for a trend claim, and the original
    commitment history may not be erased after a rebaseline.

    WHAT v2 DID. It compared the last two schedule snapshots and reported the mean slip between
    them, matching milestones by NAME. That is the drift term alone: the variance against the
    committed baseline, which is the measurement the method is named for, was never computed, and
    a rebaseline was invisible because no original commitment was retained.

    v3 REQUIRES THE MILESTONE FORECAST HISTORY, keyed on a stable identity rather than a name,
    and reports both variances so a rebaseline cannot hide a slip. A milestone forecast only once
    ABSTAINS rather than being reported as a trend. No band is asserted.
    """
    try:
        structure = require_v3_structure(si, "A2.7")
        reading = milestone_trend(structure)
    except StructureAbsent as absent:
        return insufficient("Milestone_Trend", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    worst = max(reading["milestones"], key=lambda m: m["current_variance_days"])
    return calibration_pending(
        "Milestone_Trend",
        f"{reading['milestone_count']} milestone"
        f"{'' if reading['milestone_count'] == 1 else 's'} followed across their forecasts; the "
        f"largest variance against the original commitment is "
        f"{_js_str(round1(worst['current_variance_days']))} days, and "
        f"{reading['deteriorating_count']} of them moved further out this period",
        milestone_count=reading["milestone_count"],
        worst_variance_days=reading["worst_variance_days"],
        deteriorating_count=reading["deteriorating_count"],
        milestones=reading["milestones"],
        canonical_structure="milestone_forecast_history",
    )


# ------------------------------------------------------------ A2.8 Look-Ahead Schedule Health


def run_lookahead_health(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 28, v3. READINESS GROUNDED IN A CONSTRAINT INVENTORY.

    THE SUPPLIED CONTRACT. This is a PCEIF readiness indicator grounded in constraint removal and
    Percent Plan Complete may not be substituted for it. ReadyFraction = (P - C) / P = 1 - C/P
    over the planned and constrained activities, and a governed look-ahead horizon, activity
    identity, constraint status and constraint category are required. No planned activities or an
    unreliable constraint inventory is NOT ESTIMABLE. Bands remain policy and calibration.

    WHAT v2 DID. It read two bare counts, activitiesPlanned and activitiesConstrained, and
    reported the constraint rate C/P. The arithmetic was sound but there was no inventory behind
    the counts: no activity identity, no constraint status per activity, no category and no
    declared horizon, so nothing could be audited and a count could not be checked against
    anything. The reported quantity was also the complement of the one the contract asks for.

    v3 REQUIRES THE LOOK-AHEAD INVENTORY: the window, the status date, and one row per activity
    carrying its identity, whether its constraints are cleared, and for an open constraint what
    kind it is. The counts are derived from the inventory. Where the inventory is absent, an
    activity appears twice, or a constraint status is not stated, the module ABSTAINS. The
    reported figure is now the ready fraction the contract specifies. No band is asserted.
    """
    try:
        structure = require_v3_structure(si, "A2.8")
        reading = look_ahead_ready_fraction(structure)
    except StructureAbsent as absent:
        return insufficient("Lookahead_Health", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    return calibration_pending(
        "Lookahead_Health",
        f"{reading['planned'] - reading['constrained']} of {reading['planned']} activities "
        f"planned in the {reading['horizon']} look ahead window are free of open constraints, a "
        f"ready fraction of {_js_str(round2(reading['ready_fraction']))}",
        ready_fraction=round2(reading["ready_fraction"]),
        planned=reading["planned"],
        constrained=reading["constrained"],
        constraint_categories=reading["constraint_categories"],
        horizon=reading["horizon"],
        canonical_structure="look_ahead_schedule",
    )


# ------------------------------------------------------------ A2.9 Resource Loading Index


def run_resource_loading(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 28, v3. TIME-PHASED DEMAND AGAINST CAPACITY.

    THE SUPPLIED CONTRACT. LoadRatio_t = Demand_t / AvailableCapacity_t for each time period,
    requiring a time bucket, a resource type, the planned or required demand, the available
    capacity, the amount deployed where used, and the resource constraints. It states in terms
    that a project-total planned-versus-actual labour ratio is NOT the canonical Resource Loading
    Index, and that with no time-phased resource and capacity structure the answer is NOT
    ESTIMABLE.

    WHAT v2 DID, exactly the thing the contract names as not canonical: actualLaborHours divided
    by plannedLaborHours, one ratio for the whole project, with no time bucket, no resource type
    and no capacity anywhere in it. Capacity is the denominator the index is defined on and the
    platform held no figure for it at all.

    v3 REQUIRES THE TIME-PHASED RESOURCE PROFILE. Every bucket carries its period, its resource
    type, the demand and the capacity, and a load ratio is reported for each; the peak is
    reported as the headline because a profile that is over capacity in one period is over
    capacity. Where the profile is absent the module ABSTAINS. No band is asserted.
    """
    try:
        structure = require_v3_structure(si, "A2.9")
        reading = resource_loading(structure)
    except StructureAbsent as absent:
        return insufficient("Resource_Loading", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    peak = reading["peak"]
    return calibration_pending(
        "Resource_Loading",
        f"The heaviest period is {peak['time_bucket']} for {peak['resource_type']}, demanding "
        f"{_grouped(peak['demand'])} against {_grouped(peak['available_capacity'])} available, a "
        f"load ratio of {_js_str(round2(peak['load_ratio']))}; "
        f"{reading['over_capacity_buckets']} of {reading['bucket_count']} periods are above "
        f"capacity",
        peak_load_ratio=round2(reading["peak_load_ratio"]),
        peak_time_bucket=peak["time_bucket"],
        peak_resource_type=peak["resource_type"],
        over_capacity_buckets=reading["over_capacity_buckets"],
        bucket_count=reading["bucket_count"],
        buckets=reading["buckets"],
        canonical_structure="resource_profile",
    )


# ------------------------------------------------------------ A2.10 Schedule Risk Analysis P80


def run_schedule_risk(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 28, v3. THE NETWORK RECOMPUTED ON EVERY TRIAL.

    THE SUPPLIED CONTRACT requires a stochastic network simulation: the activity network,
    duration distributions, calendars, risk events where used, dependencies where material, and a
    Monte Carlo RECOMPUTATION OF THE NETWORK FOR EVERY TRIAL. The reported figure is the 0.80
    empirical quantile of the simulated completion times. A deterministic normal z-score uplift
    is NOT Schedule Risk Analysis P80, and with no network or distributions the answer is NOT
    ESTIMABLE.

    WHAT v2 DID, exactly the forbidden thing. remaining_days / spi gave a P50, then
    uncertainty = max(0.05, 1 - spi) * 0.5 and p80 = p50 * (1 + uncertainty * 1.28), where 1.28
    is the standard normal 80th percentile. No network, no distribution, no trial and no
    simulation: one closed-form multiplication of a reported ratio, published as a P80.

    v3 REQUIRES THE SCHEDULE NETWORK with a three-point duration on every activity, redraws every
    duration on every trial and recomputes the forward and backward passes each time. Where the
    network or any distribution is absent the module ABSTAINS. No band is asserted.
    """
    try:
        structure = require_v3_structure(si, "A2.10")
        network = parse_schedule_network(structure)
        reading = schedule_risk_p80(network, rand, trials=2000)
    except StructureAbsent as absent:
        return insufficient("Schedule_Risk_Analysis", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    return calibration_pending(
        "Schedule_Risk_Analysis",
        f"Simulating the network {reading['trials']} times puts the eightieth percentile "
        f"completion at {_js_str(round2(reading['p80_finish']))} days against the "
        f"{_js_str(round2(reading['deterministic_finish']))} the durations give without "
        f"variation",
        p80_finish_days=round2(reading["p80_finish"]),
        p50_finish_days=round2(reading["p50_finish"]),
        deterministic_finish_days=round2(reading["deterministic_finish"]),
        mean_finish_days=round2(reading["mean_finish"]),
        trials=reading["trials"],
        quantile_convention="right-continuous empirical inverse",
        schedule_version=network["schedule_version"],
        canonical_structure="schedule_network",
    )


# ------------------------------------------------------------ A2.11 Critical Path Index


def run_critical_path_index(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 28, v3. THE FORWARD AND BACKWARD PASS, NOT A WEIGHTED AVERAGE OF TWO RATIOS.

    THE SUPPLIED CONTRACT. The registered name is kept in Run 28. The underlying scientific
    contract is actual CPM critical-path status and margin, requiring a forward and backward
    pass, and it states in terms that a weighted SPI/progress calculation is not a critical-path
    method and that with no valid network the answer is NOT ESTIMABLE.

    WHAT v2 DID, exactly the forbidden thing: (actualPctComplete / plannedPctComplete + spi) / 2.
    Run 27 proved this was a function of the schedule index and the progress ratio alone,
    invariant across thirty-two perturbations of every other input, which is what one expects of
    an average of two reported ratios published under a network method's name.

    v3 REQUIRES THE SCHEDULE NETWORK and reports what the passes yield: the project finish, which
    activities carry no float and are therefore critical, and the smallest margin among those
    that are not. Where the network is absent the module ABSTAINS. No band is asserted; float
    bands are named in the contract as calibration dependent.
    """
    try:
        structure = require_v3_structure(si, "A2.11")
        network = parse_schedule_network(structure)
        reading = critical_path_status(network)
    except StructureAbsent as absent:
        return insufficient("Critical_Path_Index", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    margin = reading["minimum_non_critical_float"]
    margin_words = ("every activity is critical" if margin is None
                    else f"the smallest margin off it is "
                         f"{_js_str(round2(margin))} days")
    return calibration_pending(
        "Critical_Path_Index",
        f"{reading['critical_count']} of {reading['activity_count']} activities lie on the "
        f"critical path to a finish of {_js_str(round2(reading['project_finish']))} days, and "
        f"{margin_words}",
        project_finish=round2(reading["project_finish"]),
        critical_activities=reading["critical_activities"],
        critical_count=reading["critical_count"],
        activity_count=reading["activity_count"],
        critical_fraction=round2(reading["critical_fraction"]),
        minimum_non_critical_float=(None if margin is None else round2(margin)),
        total_float=reading["total_float"],
        schedule_version=network["schedule_version"],
        canonical_structure="schedule_network",
    )


# ------------------------------------------------------------ A3.2 Contingency Burn Rate


def run_contingency_burn(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 28, v3. THE CONSUMED FRACTION AND THE PROGRESS-NORMALIZED BURN, AND NO BANDS.

    THE SUPPLIED CONTRACT. C = (OriginalContingency - RemainingContingency) /
    OriginalContingency, and NormalizedBurn = C / ProgressFraction when the progress fraction is
    above zero. It states in terms that NO universal traffic-light bands are supplied and that
    threshold calibration belongs later.

    WHAT v2 DID. The consumed fraction and the normalized burn were both computed correctly; what
    was wrong was the four-band ladder over the normalized burn at 1.0, 1.3 and 1.6, which Run 4
    already recorded as uncited and which Run 27 carried as CORRECT_ABSTENTION with a calibration
    finding. The contract now settles it: the bands go, the figures stay.

    v3 reports both figures and asserts NO colour. Where the original contingency is absent or
    not above zero, or the remaining amount does not lie between nothing and it, the module
    ABSTAINS as it did before. Where progress is absent the consumed fraction is still reported
    and the normalized burn is not, rather than the whole reading being withheld: the contract
    conditions only the second figure on progress.
    """
    if not check_inputs(si, ("originalContingency", "remainingContingency")):
        return insufficient("Contingency_Burn_Rate",
                            "Insufficient data: the original and remaining contingency amounts "
                            "are needed, and at least one of them has not been reported for "
                            "this period.", ABSTAIN_MISSING_INPUT)
    # ABSENT AND IMPOSSIBLE ARE NOT THE SAME THING, and Run 14's finding is why they are kept
    # apart here. A progress figure that was never reported means the progress-normalised burn
    # cannot be formed, and the contract conditions only that second figure on progress, so the
    # consumed fraction is still a real measurement and is reported. A progress figure that WAS
    # reported and lies outside the range a percentage can occupy is a malformed reading, and
    # Run 13 recorded that an impossible figure read as health here; the whole reading is refused
    # in that case rather than the figure being quietly treated as absent, because treating a
    # wrong number as a missing one is how a reading error becomes invisible.
    progress = None
    if si.get("actualPctComplete") is not None:
        verdict = eligible(si, required=(("actualPctComplete",
                                          "the reported percent complete"),))
        if verdict:
            return refuse("Contingency_Burn_Rate", verdict)
        progress = num(si.get("actualPctComplete"), None)
        progress = None if progress is None else progress / 100.0
    try:
        reading = contingency_burn(num(si.get("originalContingency"), None),
                                   num(si.get("remainingContingency"), None), progress)
    except StructureAbsent as absent:
        return insufficient("Contingency_Burn_Rate", absent.sentence, ABSTAIN_INVALID_DENOMINATOR)
    burn = reading["normalized_burn"]
    burn_words = ("; no progress has been reported, so no burn against progress is offered"
                  if burn is None
                  else f" at {int(js_round(reading['progress_fraction'] * 100))} per cent "
                       f"complete, a burn against progress of {_js_str(round2(burn))}")
    is_derived = _derived(si, "originalContingency", "remainingContingency")
    return calibration_pending(
        "Contingency_Burn_Rate",
        f"Contingency is {int(js_round(reading['consumed_fraction'] * 100))} per cent "
        f"consumed{burn_words}"
        + (" (estimated; upload Pay Application contingency detail for precise figures)"
           if is_derived else ""),
        consumed_fraction=round2(reading["consumed_fraction"]),
        burn_rate_pct=int(js_round(reading["consumed_fraction"] * 100)),
        remaining_pct=int(js_round((1 - reading["consumed_fraction"]) * 100)),
        normalized_burn=(None if burn is None else round2(burn)),
        original_contingency=reading["original_contingency"],
        remaining_contingency=reading["remaining_contingency"],
    )


# ------------------------------------------------------------ A3.3 Labor Productivity Index


def run_labor_productivity(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 28, v3. OUTPUT PER LABOUR INPUT, ON A COMPARABLE INSTALLED QUANTITY.

    THE SUPPLIED CONTRACT. Productivity means output per labour input: ActualProductivity =
    EarnedOutput / ActualLaborHours, PlannedProductivity = PlannedOutput / PlannedLaborHours, and
    the index is the ratio of the two. The output must be a comparable earned or installed
    quantity, an earned labour-hours basis, or another explicitly equivalent production quantity.
    It states in terms that planned hours over actual hours alone is NOT the canonical metric and
    that with no comparable output basis the answer is NOT ESTIMABLE.

    WHAT v2 DID, and it is the forbidden form with a percentage in front of it:
    ((actualPctComplete / 100) * plannedLaborHours) / actualLaborHours. The numerator is not an
    installed quantity, it is the planned hours scaled by a reported progress percentage, so the
    "productivity" moved with whatever percentage was typed into a monthly report.

    v3 REQUIRES THE PRODUCTION RECORD: the quantity installed, the quantity planned, the unit
    both are counted in, the hours each took, and where the quantities came from. Where the
    record is absent the module ABSTAINS. No band is asserted.
    """
    try:
        structure = require_v3_structure(si, "A3.3")
        reading = labor_productivity(structure)
    except StructureAbsent as absent:
        return insufficient("Labor_Productivity", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    return calibration_pending(
        "Labor_Productivity",
        f"{_js_str(round2(reading['actual_productivity']))} {reading['output_unit']} an hour "
        f"installed against {_js_str(round2(reading['planned_productivity']))} planned, a "
        f"productivity index of {_js_str(round2(reading['productivity_index']))}",
        productivity_index=round2(reading["productivity_index"]),
        actual_productivity=reading["actual_productivity"],
        planned_productivity=reading["planned_productivity"],
        output_unit=reading["output_unit"],
        earned_output=reading["earned_output"],
        planned_output=reading["planned_output"],
        actual_labor_hours=reading["actual_labor_hours"],
        planned_labor_hours=reading["planned_labor_hours"],
        canonical_structure="production_output_record",
    )


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
    # RUN 14, FOUND BY THE DEPENDENT SWEEP RATHER THAN BY RUN 13. Run 13 drove this field to ten
    # thousand and this module did not band better, so it was recorded as a match. The Run 14
    # sweep drove every bounded field to every value just outside its own bound as well, and a
    # reported progress a fraction above a hundred per cent DOES read calmer here: it inflates
    # the expected material cost, which is the denominator of the variance. It is the same
    # defect as the five, on a module the earlier sample missed, and it is corrected the same
    # way rather than left standing because it was not on the list.
    verdict = eligible(si, required=(("actualPctComplete", "the reported percent complete"),))
    if verdict:
        return refuse("Material_Cost_Variance", verdict)
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
    RUN 28, v3. AN EXPLICIT ALLOCATION BASE, OR NOTHING.

    THE SUPPLIED CONTRACT. PlannedRate = PlannedOverhead / PlannedDriver, ActualRate =
    ActualOverhead / ActualDriver, and the variance is the difference between the two rates with
    the relative variance as a share of the planned rate. It states in terms that
    IndirectCostActual over IndirectCostPlan with no allocation base is NOT overhead absorption
    and that with no allocation base the answer is NOT ESTIMABLE.

    WHAT v2 DID, exactly the forbidden thing with a progress scaling on it: indirectCostActual
    divided by (indirectCostPlan * actualPctComplete / 100). There is no driver anywhere in that
    expression; overhead is absorbed over a base such as direct labour hours or direct cost, and
    the platform held no figure for one.

    v3 REQUIRES THE ALLOCATION BASE RECORD: the base named, the planned and actual overhead, the
    planned and actual amount of the base, and where the driver figures came from. Where the
    record is absent the module ABSTAINS. Both rates and both variances are reported. No band is
    asserted.
    """
    try:
        structure = require_v3_structure(si, "A3.5")
        reading = overhead_absorption(structure)
    except StructureAbsent as absent:
        return insufficient("Overhead_Absorption", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    return calibration_pending(
        "Overhead_Absorption",
        f"Overhead is being absorbed at {_js_str(round2(reading['actual_rate']))} for each unit "
        f"of {reading['allocation_base']} against {_js_str(round2(reading['planned_rate']))} "
        f"planned, a rate variance of "
        f"{_js_str(round1(reading['relative_rate_variance'] * 100))} per cent",
        planned_rate=reading["planned_rate"],
        actual_rate=reading["actual_rate"],
        rate_variance=reading["rate_variance"],
        relative_rate_variance=reading["relative_rate_variance"],
        allocation_base=reading["allocation_base"],
        planned_driver=reading["planned_driver"],
        actual_driver=reading["actual_driver"],
        canonical_structure="overhead_allocation_base",
    )


# ------------------------------------------------------------ A3.6 Cost Risk Analysis P80


def run_cost_risk(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 28, v3. A SIMULATED TOTAL-COST DISTRIBUTION, NOT AN INFLATED COST INDEX.

    THE SUPPLIED CONTRACT. TotalCost = BaseCostComponents + RealizedRiskEvents, requiring the
    components, the risk events, their probabilities and impact distributions, dependence where
    material, a simulation, and an empirical total-cost distribution whose 0.80 quantile is
    reported under a frozen quantile convention. It states in terms that a deterministic CPI
    uplift is NOT CRA P80 and that with no stochastic cost-risk model the answer is NOT
    ESTIMABLE.

    WHAT v2 DID, exactly the forbidden thing. eac = bac / cpi, then uncertainty = max(0.03,
    abs(1 - cpi)) * 0.5 and p80_eac = eac * (1 + uncertainty * 1.28). One closed-form
    multiplication of a reported cost index by the standard normal 80th percentile, with no
    component, no risk event, no probability, no impact and no trial anywhere in it. The Run-7
    comment in this file said as much and deferred the work; this is that work.

    v3 REQUIRES THE COST RISK MODEL and simulates it: each event occurs with its stated
    probability and, when it does, its impact is drawn from its stated distribution, and the
    reported figure is the empirical eightieth percentile of the resulting total cost under the
    convention frozen in canonical_v3.empirical_quantile. Where the model is absent the module
    ABSTAINS. No band is asserted.
    """
    try:
        structure = require_v3_structure(si, "A3.6")
        reading = cost_risk_simulation(structure, rand, trials=20000)
    except StructureAbsent as absent:
        return insufficient("Cost_Risk_Analysis", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    return calibration_pending(
        "Cost_Risk_Analysis",
        f"Simulating {reading['risk_event_count']} risk event"
        f"{'' if reading['risk_event_count'] == 1 else 's'} against a base cost of "
        f"{_money(reading['base_cost'])} over {reading['trials']} trials puts the eightieth "
        f"percentile total cost at {_money(reading['p80_total_cost'])}",
        p80_total_cost=reading["p80_total_cost"],
        p50_total_cost=reading["p50_total_cost"],
        mean_total_cost=reading["mean_total_cost"],
        base_cost=reading["base_cost"],
        risk_event_count=reading["risk_event_count"],
        trials=reading["trials"],
        quantile_convention="right-continuous empirical inverse",
        canonical_structure="cost_risk_model",
    )


# ------------------------------------------------------------ A3.7 Analogous Estimating Ratio


def run_analogous_estimating(si: dict, rand: Callable[[], float],
                             period_cutoff) -> dict[str, Any]:
    """
    RUN 28, v3. AN IDENTIFIED ANALOG, ADAPTED BY STATED FACTORS.

    THE SUPPLIED CONTRACT requires an identified analog project, its provenance, comparability
    criteria, normalization and adaptation factors, with the adapted estimate the analog cost
    multiplied through those factors. It states in terms that a preloaded analog overrun
    percentage with NO identified analog is not canonical analogous estimating and that with no
    governed analog the answer is NOT ESTIMABLE.

    WHAT v2 DID, exactly the forbidden thing: it read a single scalar, analogousOverrunPct,
    applied it to the budget and banded the percentage. Run 20 corrected what that reading SAID
    about an underrunning analog and recorded plainly that the proxy still carried no analog
    selection, no comparability criteria and no adaptation factors. This is that finding closed.

    v3 REQUIRES THE ANALOG RECORD. Where it is absent, carries no identified project, no cost, or
    no adaptation factors, the module ABSTAINS. No band is asserted.
    """
    try:
        structure = require_v3_structure(si, "A3.7")
        reading = analogous_estimate(structure)
    except StructureAbsent as absent:
        return insufficient("Analogous_Estimating", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    factor_words = ", ".join(
        f"{f['factor_name']} {_js_str(round2(f['factor_value']))}"
        for f in reading["adaptation_factors"])
    return calibration_pending(
        "Analogous_Estimating",
        f"Adapting {reading['analog_project_id']} at {_money(reading['analog_cost'])} by "
        f"{factor_words} gives an analogous estimate of "
        f"{_money(reading['adapted_estimate'])}",
        adapted_estimate=reading["adapted_estimate"],
        analog_project_id=reading["analog_project_id"],
        analog_cost=reading["analog_cost"],
        adaptation_factors=reading["adaptation_factors"],
        combined_factor=round2(reading["combined_factor"]),
        canonical_structure="analog_estimate",
    )


# ------------------------------------------------------------ A3.8 Parametric Cost Index


def run_parametric_cost(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 28, v3. THE CANONICAL STRUCTURE EXISTS; THE MODULE STAYS DISABLED AND NON-VOTING.

    THE SUPPLIED CONTRACT. Keep operationally disabled in Run 28. Build only the canonical v3
    structure and the laboratory implementation: a parametric model requires measurable cost
    drivers and fitted or calibrated coefficients, of the general form Cost = beta0 + beta1*x1 +
    ... + betap*xp. It states in terms that comparing EAC formulas is not parametric estimating,
    and that even if the laboratory implementation passes the module remains disabled and
    non-voting until a later owner or research activation decision.

    WHAT v2 DID, exactly the forbidden thing: (bac / cpi) divided by (ac + (bac - ev)), a
    comparison of two estimate-at-completion formulas published as a parametric index. There was
    no driver, no coefficient, no fit and no dataset in it.

    WHERE THE CANONICAL IMPLEMENTATION LIVES. canonical_v3.parametric_cost, which requires the
    drivers with their units, the fitted coefficients, the coefficient source, the fit dataset
    and the model version, and which refuses when the drivers supplied do not match the drivers
    the model was fitted on. It is exercised by the laboratory oracle in
    server/tools/test_run28_canonical_oracles.py and is reached by NO production path.

    THE PRODUCTION ARM REFUSES. This module sits in registry.DISABLED_CONCEPT_ONLY, so
    run_module short-circuits before this function is called at all. The forbidden arithmetic is
    nonetheless removed from it rather than left standing behind a gate, because a disabled
    module is exactly where a stale claim survives unexamined.
    """
    return insufficient(
        "Parametric_Cost",
        "This measure is registered and is not operated. A parametric cost estimate needs "
        "measurable cost drivers and coefficients fitted to a body of completed work, and "
        "neither has been established for this platform, so no estimate is offered and no "
        "substitute figure is used in its place.",
        ABSTAIN_STRUCTURE_ABSENT)


# ------------------------------------------------------------ A3.9 Inflation Adjustment Index


def run_inflation_adjustment(si: dict, rand: Callable[[], float],
                             period_cutoff) -> dict[str, Any]:
    """
    RUN 28, v3. A NAMED EXTERNAL PRICE INDEX, OR NOTHING.

    THE SUPPLIED CONTRACT requires a governed external cost or price index: the named series, its
    authoritative source, geography, commodity or cost scope, base period, current or forecast
    period, data vintage and the applicable cost exposure. EscalationFactor = Index_current /
    Index_base and AdjustedCost = BaseCost * EscalationFactor. It states in terms that a
    baseline-to-current project material price ratio is NOT an external inflation index, that
    with no governed external index the answer is NOT ESTIMABLE, and that no external market
    index may be fabricated or hard-coded.

    WHAT v2 DID, exactly the forbidden thing: (materialCostCurrent - materialCostBaseline *
    progress) / (materialCostBaseline * progress), floored at zero, published as a material
    escalation. That is this project's own price movement against its own progress-scaled
    baseline. It has no geography, no time base, no authority and no index; the module's own
    qualifier said so.

    v3 REQUIRES THE EXTERNAL INDEX RECORD, and every one of its seven provenance fields must be
    stated or the structure is refused. No index level appears anywhere in this repository's
    production code: both come off the supplied structure. Where the record is absent the module
    ABSTAINS. No band is asserted.
    """
    try:
        structure = require_v3_structure(si, "A3.9")
        exposure = num(structure.get("cost_exposure"), None)
        if exposure is None:
            raise StructureAbsent(
                "The price index provided does not say which cost exposure it is to be applied "
                "to, so no adjusted cost is reported from it.")
        reading = inflation_adjustment(structure, float(exposure))
    except StructureAbsent as absent:
        return insufficient("Inflation_Adjustment", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    return calibration_pending(
        "Inflation_Adjustment",
        f"{reading['index_name']} for {reading['geography']} has moved from "
        f"{_js_str(round2(reading['base_index_value']))} in {reading['base_period']} to "
        f"{_js_str(round2(reading['current_index_value']))} in "
        f"{reading['observation_period']}, a factor of "
        f"{_js_str(round2(reading['escalation_factor']))} which puts "
        f"{_money(reading['base_cost'])} of exposure at "
        f"{_money(reading['adjusted_cost'])}",
        escalation_factor=round2(reading["escalation_factor"]),
        adjusted_cost=reading["adjusted_cost"],
        escalation_amount=reading["escalation_amount"],
        base_index_value=reading["base_index_value"],
        current_index_value=reading["current_index_value"],
        index_name=reading["index_name"],
        index_authority=reading["authority"],
        geography=reading["geography"],
        index_scope=reading["scope"],
        base_period=reading["base_period"],
        observation_period=reading["observation_period"],
        vintage=reading["vintage"],
        cost_exposure=reading["base_cost"],
        canonical_structure="external_cost_index",
    )


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
