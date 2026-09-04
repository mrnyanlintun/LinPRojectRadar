"""
A1 extension models: the EVM and statistical forecasters (A1.3–A1.11).

Ported from assets/js/simulations.js "Cat 1 — EVM extensions", validated numerically against the
JavaScript executed in a browser. See VALIDATION.md for the per-module comparison.

All nine are deterministic and none draws from the generator; `rand` is accepted only for the
registry's one call signature.

Porting hazards specific to this file:

- The history fallback `si.spiHistory || (si.spi ? [si.spi] : null)` is JavaScript truthiness
  twice over: a missing history falls back, but an EMPTY history array is truthy and is used
  (then abstains on the length check), and an spi of exactly 0 falls through to null.
  `_history` reproduces all three arms.
- `if (!SPI_t)` and `if (!executionRate)` treat a computed 0 as insufficient, not as a value.
  Reproduced: a project at 0% actual progress abstains from Earned Schedule rather than
  reporting SPI(t) = 0.
- Bayesian EAC divides by `(bac·(1−cpi)/cpi)²`, which is zero at cpi = 1: the JavaScript then
  produces NaN, which falls through every status comparison and lands on Red with a null
  posterior. The port abstains instead — the refusing direction, recorded in VALIDATION.md.
  cpi = 0 (Infinity arithmetic in Bayesian and VAC) is refused the same way.
"""

from __future__ import annotations

from datetime import date as _date
from typing import Any, Callable

from .canonical import StructureAbsent
from .canonical_v3 import (
    bayesian_eac_model, budget_execution, cpi_reference_class, cpi_shrinkage,
    earned_schedule, expenditure_baseline_to_date, forecast_arima, identify_arima,
    independent_eac_reconciliation, kalman_state_space_model, pending_change_exposure,
    require_v3_structure,
    time_phased_baseline,
)
from . import owner_bands as _OB
from .models import (
    ABSTAIN_INSUFFICIENT_HISTORY, ABSTAIN_MALFORMED_INPUT, ABSTAIN_MISSING_INPUT,
    ABSTAIN_STRUCTURE_ABSENT, PROVENANCE_CODIFIED, PROVENANCE_CONVENTION,
    PROVENANCE_OWNER_CALIBRATED, THRESHOLD_SOURCE_EXTERNAL, THRESHOLD_SOURCE_OWNER,
    band_abstained, banded, calibration_pending, check_inputs, insufficient,
)

#: RUN 107. The one basis sentence the owner's order attaches to every band in it, composed
#: once so four modules cannot each write a slightly different one. The module names its own
#: section; the tolerance identifier and the provenance claim are the same in all four.
_RUN107_BASIS_ID = "owner_configured_construction_control_tolerance"


def _run107_basis(section: str, numbers: str) -> str:
    return (f"the owner's Run 107 order, {section}. The band basis identifier is "
            f"`{_RUN107_BASIS_ID}`. OWNER-CALIBRATED: no published standard fixes {numbers}. "
            f"They are a documented owner tolerance, stated as the owner's own decision and "
            f"not presented as a construction standard. A stricter figure stated in a project "
            f"document would take precedence, and none is stated by any document this project "
            f"has uploaded")
from .models_ext import _js_date_ms, _js_str, _money
from .rng import clamp, js_round, num, round1

_round3 = lambda v: js_round(v * 1000) / 1000  # noqa: E731


def _history(si: dict, key: str, scalar_key: str):
    """`si[key] || (si[scalar] ? [si[scalar]] : null)`, truthiness intact."""
    h = si.get(key)
    if h is not None and h is not False:
        # JS: any non-falsy value short-circuits; an empty list is truthy and passes through.
        if isinstance(h, list):
            return h
    s = si.get(scalar_key)
    if s:  # JS truthiness: 0, null, undefined all fail
        return [s]
    return None


# ------------------------------------------------------------ A1.3 Bayesian EAC


def run_bayesian_eac(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 28, v3. THE GOVERNED BAYESIAN MODEL, OR NOTHING.

    THE SUPPLIED CONTRACT. posterior is proportional to likelihood times prior, and production
    must explicitly identify the parameter being estimated, the prior and its source, the
    likelihood and its observation model, the provenance of the uncertainty, the posterior
    estimate and a posterior interval.

    WHAT v2 DID. Normal-normal updating whose prior variance was (bac * 0.15) squared and whose
    likelihood variance was (bac * (1 - cpi) / cpi) squared. Both are designed constants: the
    0.15 is a literal in this file and the likelihood variance is a transformation of the cost
    index rather than an estimate of observation error. Nothing stated where either came from,
    and the same two designed variances were used on every project the platform holds, so the
    posterior was a property of this file's constants as much as of the project.

    v3 REQUIRES THE MODEL RECORD. The prior, its source, the observation, the observation
    variance and the basis that variance was estimated from all arrive on the signal inputs, and
    the update is the conjugate normal-normal one. Where the record is absent the module ABSTAINS
    rather than falling back to the designed constants. No band is asserted: the posterior of a
    governed model is not the quantity the old ladder over a percentage of budget was drawn over,
    and designed prior variances verify algebra rather than constituting field calibration.
    """
    try:
        structure = require_v3_structure(si, "A1.3")
        model = bayesian_eac_model(structure)
    except StructureAbsent as absent:
        return insufficient("Bayesian_EAC", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    return calibration_pending(
        "Bayesian_EAC",
        f"Bayesian posterior for {model['parameter']}: {_money(model['posterior_mean'])}, "
        f"with a 95 per cent credible interval from {_money(model['credible_low'])} to "
        f"{_money(model['credible_high'])}",
        posterior_eac=model["posterior_mean"],
        posterior_variance=model["posterior_variance"],
        credible_low=model["credible_low"],
        credible_high=model["credible_high"],
        credible_mass=model["credible_mass"],
        prior_mean=model["prior_mean"],
        prior_variance=model["prior_variance"],
        prior_source=model["prior_source"],
        observation=model["observation"],
        observation_variance=model["observation_variance"],
        observation_model=model["observation_model"],
        variance_basis=model["variance_basis"],
        canonical_structure="bayesian_eac_model",
    )


# ------------------------------------------------------------ A1.4 Kalman Filter SPI Smoother


def run_kalman_filter(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 28, v3. A GENUINE STATE-SPACE RECURSION WITH Q AND R THAT SAY WHERE THEY CAME FROM.

    THE SUPPLIED CONTRACT is the scalar random-walk recursion: x_pred = x_prev, P_pred = P_prev +
    Q, K = P_pred / (P_pred + R), x_post = x_pred + K(z - x_pred), P_post = (1 - K)P_pred. Q and
    R require provenance and calibration, and the filter may not be replaced by a moving average.

    WHAT v2 DID. The recursion itself was right, and it is not the arithmetic that was wrong:
    q = 0.01 and r = 0.1 were literals in this file with no stated origin, the starting state was
    the first reading with a starting variance of 1.0 chosen the same way, and the reported trend
    was a two-period difference divided by two, which is not part of a Kalman filter at all.

    v3 REQUIRES THE STATE-SPACE MODEL RECORD: the starting estimate and its uncertainty, the
    process and measurement variances, the source of each of the two variances, and the readings.
    Run 27 established that the measurement variance IS estimable from evidence this platform
    already holds -- repeated readings of one period do occur, because two document types report
    the same period -- so this is a supply path, not an impossibility. Where the record is absent
    the module ABSTAINS. The filtered state is reported with its final gain and variance and NO
    band, because Q and R are calibration items handed to Run 33.
    """
    try:
        structure = require_v3_structure(si, "A1.4")
        run = kalman_state_space_model(structure)
    except StructureAbsent as absent:
        return insufficient("Kalman_Filter", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    return calibration_pending(
        "Kalman_Filter",
        f"Filtered schedule index {_js_str(_round3(run['x_post']))} after "
        f"{run['observations']} reading{'' if run['observations'] == 1 else 's'}, with a "
        f"filter gain of {_js_str(_round3(run['gains'][-1]))} on the last of them",
        smoothed_spi=_round3(run["x_post"]),
        posterior_variance=run["p_post"],
        final_gain=run["gains"][-1],
        gains=[_round3(g) for g in run["gains"]],
        filtered_path=[_round3(v) for v in run["path"]],
        observations=run["observations"],
        process_variance=run["process_variance"],
        measurement_variance=run["measurement_variance"],
        process_variance_source=run["process_variance_source"],
        measurement_variance_source=run["measurement_variance_source"],
        canonical_structure="kalman_state_space_model",
    )


# ------------------------------------------------------------ A1.5 ARIMA CPI Forecast


def run_arima_forecast(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 28, v3. AN IDENTIFIED ARIMA WORKFLOW, NOT AN AR(1) ON FIRST DIFFERENCES.

    THE SUPPLIED CONTRACT requires an explicit p, d and q, a differencing rule, AR and MA
    coefficients, drift treatment, model identification and selection, estimation, stationarity
    and invertibility handling, residual diagnostics, a short-horizon forecast and a prediction
    interval, with selection parsimonious for short histories by AIC/AICc/BIC plus diagnostics.
    It states in terms that ARIMA must not be hard-coded as an AR(1) on first differences, and
    that a minimum-history failure is NOT ESTIMABLE.

    WHAT v2 DID, exactly the forbidden thing. It differenced once unconditionally, regressed each
    difference on the one before it to get a single phi, clamped that phi to plus or minus 0.9,
    and forecast one step. There was no q, no selection, no intercept, no diagnostics and no
    interval, and d was 1 by assumption rather than by a rule. Three observations were enough to
    run it.

    v3 identifies the model in canonical_v3.identify_arima: d by a stated stationarity rule,
    (p, q) up to (2, 1) estimated by conditional least squares and selected by AICc, which is the
    small-sample criterion and so favours parsimony on a short cost-index history by
    construction; stationarity and invertibility are checked and a model failing either refuses;
    the Ljung-Box statistic and the residual autocorrelation travel with the result. The minimum
    history is eight readings, below which the module ABSTAINS. No band is asserted on the
    forecast: the old ladder was drawn over the output of a different estimator.
    """
    history = _history(si, "cpiHistory", "cpi")
    if not history:
        return insufficient("ARIMA_Forecast", "Awaiting a cost performance history",
                            ABSTAIN_INSUFFICIENT_HISTORY)
    try:
        model = identify_arima(history)
    except StructureAbsent as absent:
        return insufficient("ARIMA_Forecast", absent.sentence, ABSTAIN_INSUFFICIENT_HISTORY)
    # ------------------------------------------------- RUN 107. THREE PERIODS, WORST OF THREE.
    # The owner's order: "Forecast CPI for the next three periods; band the worst of the three.
    # ... A near-term Green does not offset a third-period Red." The three come from the SAME
    # identified model recursed forward -- see `forecast_arima` -- not from three fits.
    _path = forecast_arima(model, 3)
    _bands = [_OB.descending(v, 0.95, 0.90, 0.85) for v in _path]
    _worst = _OB.worst(_bands)
    _worst_i = max(range(3), key=lambda i: _OB.BAND_ORDER.index(_bands[i]))
    order = f"({model['p']},{model['d']},{model['q']})"
    interval = ""
    if model.get("interval_low") is not None:
        interval = (f", with a 95 per cent prediction interval from "
                    f"{_js_str(_round3(model['interval_low']))} to "
                    f"{_js_str(_round3(model['interval_high']))}")
    return banded(
        "ARIMA_Forecast",
        f"Cost performance is forecast at "
        f"{', '.join(_js_str(_round3(v)) for v in _path)} over the next three periods from an "
        f"identified {order} model over {model['history']} readings{interval}. The worst of the "
        f"three is period {_worst_i + 1} at {_js_str(_round3(_path[_worst_i]))}.",
        status_color=_worst,
        boundary=(
            "on the FORECAST cost performance index for each of the next three periods, with "
            "the WORST OF THE THREE governing: at or above 0.95 is Green; at or above 0.90 and "
            "below 0.95 is Yellow; at or above 0.85 and below 0.90 is Amber; below 0.85 is Red. "
            "Each boundary is INCLUSIVE ON ITS LOWER SIDE and the direction is adverse "
            "DOWNWARD. A NEAR-TERM GREEN DOES NOT OFFSET A THIRD-PERIOD RED: the three periods "
            "are never averaged. Here the three forecasts band "
            + ", ".join(f"period {i + 1} {b}" for i, b in enumerate(_bands)) + "."),
        basis=_run107_basis("section 1, A1.5",
                            "0.95, 0.90 and 0.85 on a forecast cost performance index"),
        provenance=PROVENANCE_OWNER_CALIBRATED,
        threshold_source=THRESHOLD_SOURCE_OWNER,
        band_basis_id=_RUN107_BASIS_ID,
        forecast_path=[_round3(v) for v in _path],
        forecast_path_bands=_bands,
        forecast_horizon=3,
        band_governing_period=_worst_i + 1,
        band_aggregation_rule="worst-of the three forecast periods",
        forecast_cpi=_round3(model["forecast"]),
        arima_p=model["p"], arima_d=model["d"], arima_q=model["q"],
        ar_coefficients=[_round3(v) for v in model["phi"]],
        ma_coefficients=[_round3(v) for v in model["theta"]],
        intercept=_round3(model["c"]),
        selection_criterion="AICc",
        aicc=model["aicc"],
        residual_autocorrelation=_round3(model["residual_acf1"]),
        ljung_box_lag1=model["ljung_box_lag1"],
        interval_low=model.get("interval_low"),
        interval_high=model.get("interval_high"),
        interval_mass=model.get("interval_mass"),
        history_periods=model["history"],
        constant_series=model["constant_series"],
    )


# ------------------------------------------------------------ A1.6 Earned Schedule


def run_earned_schedule(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 28, v3. INTERPOLATION ON THE CUMULATIVE PLANNED VALUE CURVE, NOT A PERCENTAGE RATIO.

    THE SUPPLIED CONTRACT. Find C such that PV_C <= EV < PV_(C+1), then ES = C + (EV - PV_C) /
    (PV_(C+1) - PV_C), SV(t) = ES - AT and SPI(t) = ES / AT. It states in terms that actual
    percent over planned percent is not Earned Schedule, and that an absent cumulative PV curve
    is NOT ESTIMABLE.

    WHAT v2 DID, exactly the forbidden thing: actualPctComplete divided by plannedPctComplete,
    reported as "ES SPI(t)". There was no curve, no interpolation and no earned schedule at all;
    the delay figure was that ratio applied to the baseline duration.

    v3 REQUIRES THE TIME-PHASED BASELINE: the cumulative value of work planned complete at the
    end of each period, with its baseline version and approval source. Earned value and the
    actual time elapsed come with it. Where the curve is absent the module ABSTAINS. No band is
    asserted: the old ladder read a ratio of two reported percentages, which is a different
    quantity from a time-based schedule index taken off a planned value curve.
    """
    try:
        structure = require_v3_structure(si, "A1.6")
        baseline = time_phased_baseline(structure)
        ev = num(si.get("ev"), None)
        at = num(structure.get("actual_time_periods"), None)
        if ev is None:
            raise StructureAbsent(
                "The value of work performed has not been reported for this period, so there is "
                "nothing to place on the planned value curve and no schedule position is read.")
        reading = earned_schedule(baseline["curve"], float(ev),
                                  float(at) if at is not None else None)
    except StructureAbsent as absent:
        return insufficient("Earned_Schedule", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    except (TypeError, ValueError):
        return insufficient(
            "Earned_Schedule",
            "The time phased baseline provided carries a figure that is not a number, so no "
            "schedule position is read from it.", ABSTAIN_MALFORMED_INPUT)
    # ------------------------------------------------ RUN 107. TWO COMPONENTS, WORST-OF.
    _comps = []
    _spit = reading["spi_time"]
    _comps.append(_OB.component(
        "SPI(t) = ES / AT", value=_round3(_spit),
        band=_OB.descending(_spit, 0.95, 0.90, 0.85),
        boundary=("earned schedule divided by actual time: at or above 0.95 is Green; at or "
                  "above 0.90 and below 0.95 is Yellow; at or above 0.85 and below 0.90 is "
                  "Amber; below 0.85 is Red. Each boundary is INCLUSIVE ON ITS LOWER SIDE and "
                  "the direction is adverse DOWNWARD.")))
    # THE TIME-VARIANCE COMPONENT IS DEFINED IN WORKING DAYS AND THE CURVE IS IN PERIODS.
    # SV(t) = ES - AT comes off the planned value curve in PERIODS. The owner's ladder divides
    # it, in WORKING DAYS, by the remaining planned working duration. Converting periods to
    # working days needs the approved calendar's working days per period. RUN 107 RECORDED THAT
    # NO CALENDAR REACHED THIS MODULE and left the component Not Assessed on every project.
    # RUN 108, GOAL 2. THE CALENDAR NOW REACHES THIS MODULE, and both figures are counted on
    # it by the ONE conversion function every arm uses -- `working_calendar.working_days_between`
    # and `working_days_per_period` -- so A1.6, A4.9 and A4.5 cannot count a working day three
    # different ways. Nothing here reads a working-day figure a structure asserts: the platform
    # counts the days itself, from the project's stated calendar and the schedule's own printed
    # dates, or it counts none.
    from .working_calendar import (CALENDAR_ABSENT_WORDS, read_project_calendar,
                                   working_days_between, working_days_per_period)
    _cal = read_project_calendar(si)
    _cal_id = (_cal or {}).get("calendar_id")
    _wdpp = None
    _wdpp_detail = None
    _remaining = None
    _tv_absent = None
    if _cal is None:
        _tv_absent = CALENDAR_ABSENT_WORDS
    else:
        _wdpp_detail = working_days_per_period(_cal, baseline.get("period_labels") or [])
        _wdpp = (_wdpp_detail or {}).get("working_days_per_period")
        _refs = si.get("scheduleReferenceDates")
        if isinstance(_refs, dict):
            try:
                _from = _date.fromisoformat(str(_refs.get("data_date") or "").strip())
                _to = _date.fromisoformat(str(_refs.get("baseline_finish_date") or "").strip())
                _remaining = working_days_between(_cal, _from.toordinal(), _to.toordinal())
            except ValueError:
                _remaining = None
        _missing = []
        if not _wdpp:
            _missing.append(
                "the date span each period covers, which is read from the period labels the "
                "approved time-phased baseline itself prints -- an ISO month such as 2026-07 or "
                "an ISO period-ending date -- and which this baseline's labels do not state")
        if _remaining is None or _remaining <= 0:
            _missing.append(
                "the schedule update's own data date and its APPROVED baseline finish DATE, "
                "which the working days remaining are counted between; a baseline finish "
                "stated only as a day number on the schedule's own axis is not converted into "
                "a date")
        if _missing:
            _tv_absent = ("this project states a working calendar" +
                          (f" ({_cal_id})" if _cal_id else "") +
                          ", but the remaining planned working duration and the working days "
                          "per period still cannot both be counted on it. WHAT IS MISSING: " +
                          "; and ".join(_missing) + ". NOT ASSESSED, and no period is assumed "
                          "to be a month, a week or any number of working days.")
    if _tv_absent is None:
        _svt_days = reading["schedule_variance_time"] * float(_wdpp)
        _late = max(0.0, -_svt_days)
        _tv = _late / float(_remaining)
        _comps.append(_OB.component(
            "time variance share", value=round(_tv * 100, 2),
            band=("Green" if _tv <= 0.02 else "Yellow" if _tv <= 0.05
                  else "Amber" if _tv <= 0.10 else "Red"),
            boundary=("the absolute schedule variance in working days -- SV(t) = ES - AT, "
                      "converted on the approved calendar's working days per period -- divided "
                      "by the remaining planned working duration: ON OR AHEAD OF SCHEDULE, or "
                      "late by at or below 2 per cent, is Green; above 2 and at or below 5 per "
                      "cent is Yellow; above 5 and at or below 10 per cent is Amber; above 10 "
                      "per cent is Red. Each boundary is INCLUSIVE ON ITS UPPER SIDE. Being "
                      "AHEAD is Green and is never banded as a variance. THE CALENDAR THE DAYS "
                      f"WERE COUNTED ON is the one this project's own schedule update defines, "
                      f"{_cal_id or 'unnamed'}: a "
                      f"{_cal['working_days_per_week']}-day working week and "
                      f"{_cal['holiday_count']} holiday"
                      f"{'' if _cal['holiday_count'] == 1 else 's'} it states. It is the "
                      f"project's calendar and not the platform's; no working week and no "
                      f"holiday set is assumed anywhere.")))
    else:
        _comps.append(_OB.component("time variance share", absent_reason=_tv_absent))
    _agg = _OB.aggregate(_comps)
    _posture = _agg["band_posture_before_override"]
    # THE HARD OVERRIDE. It needs an approved milestone with the period it is required by. The
    # forecast period for a milestone planned at period m is m / SPI(t), the standard earned
    # schedule projection; the milestone is late when that exceeds the period the milestone is
    # REQUIRED by, as the baseline states it. Where the baseline declares no approved milestone
    # the override is NOT EVALUABLE and this reading says so.
    _milestones = structure.get("approved_milestones")
    _milestones = _milestones if isinstance(_milestones, list) else []
    _late_ms = []
    for _m in _milestones:
        if not isinstance(_m, dict):
            continue
        _pi = num(_m.get("planned_period_index"), None)
        _ri = num(_m.get("required_period_index"), _pi)
        if _pi is None or _ri is None or _spit <= 0:
            continue
        if (_pi / _spit) > _ri + 1e-9:
            _late_ms.append({"milestone_id": str(_m.get("milestone_id") or ""),
                             "milestone_class": str(_m.get("milestone_class") or ""),
                             "planned_period_index": _pi,
                             "required_period_index": _ri,
                             "forecast_period_index": round(_pi / _spit, 3)})
    _override = bool(_late_ms)
    if _override:
        _posture = _OB.at_least_as_adverse_as(_posture, "Red")
    _override_words = (
        "HARD OVERRIDE: Red when the Earned Schedule forecast shows an approved contractual, "
        "turnover, owner-committed or required milestone late. A milestone planned at period m "
        "is forecast at m divided by SPI(t), and it is late when that exceeds the period the "
        "baseline states it is required by. ")
    if not _milestones:
        _override_words += ("This project's time-phased baseline declares no approved "
                            "milestone, so the override was NOT EVALUABLE and its absence was "
                            "not read as no milestone being late.")
    elif _override:
        _override_words += (f"It fired on "
                            f"{', '.join(m['milestone_id'] for m in _late_ms)}.")
    else:
        _override_words += "No approved milestone forecasts late, so it did not fire."
    _fields = dict(
        earned_schedule=_round3(reading["earned_schedule"]),
        spi_time=_round3(reading["spi_time"]),
        schedule_variance_time=_round3(reading["schedule_variance_time"]),
        actual_time=reading["actual_time"],
        curve_periods=reading["periods"],
        baseline_version=baseline["baseline_version"],
        approval_source=baseline["approval_source"],
        working_days_per_period=_wdpp,
        remaining_planned_working_days=_remaining,
        working_calendar_id=_cal_id,
        working_calendar_days_per_week=(_cal or {}).get("working_days_per_week"),
        working_calendar_holidays_stated=(_cal or {}).get("holidays_stated"),
        working_calendar_holiday_count=(_cal or {}).get("holiday_count"),
        working_days_per_period_detail=_wdpp_detail,
        approved_milestones=_milestones,
        milestones_forecast_late=_late_ms,
        band_hard_override_fired=_override,
        band_hard_override_evaluable=bool(_milestones),
        canonical_structure="time_phased_baseline",
        **_agg)
    _msg = (
        f"Earned schedule {_js_str(_round3(reading['earned_schedule']))} periods against "
        f"{_js_str(_round3(reading['actual_time']))} elapsed, a time based schedule index of "
        f"{_js_str(_round3(reading['spi_time']))} and a schedule variance of "
        f"{_js_str(_round3(reading['schedule_variance_time']))} periods")
    if _posture is None:
        return band_abstained("Earned_Schedule", _msg,
                              reason="Not Assessed: no component could be formed.",
                              band_basis_id=_RUN107_BASIS_ID, **_fields)
    return banded(
        "Earned_Schedule", _msg,
        status_color=_posture,
        boundary=(" ".join(c["boundary"] for c in _comps if c["boundary"])
                  + " " + _agg["band_aggregation_words"] + " " + _override_words),
        basis=_run107_basis("section 1, A1.6",
                            "0.95, 0.90 and 0.85 on SPI(t), nor 2, 5 and 10 per cent on the "
                            "time variance share"),
        provenance=PROVENANCE_OWNER_CALIBRATED,
        threshold_source=THRESHOLD_SOURCE_OWNER,
        band_basis_id=_RUN107_BASIS_ID,
        **_fields)





# =============================================================================================
# RUN 107, SECTION 3. THE PROVENANCE GAP ON A1.7 AND A1.8, AND ITS REPAIR.
#
# WHAT RUN 106 FOUND. These two are the only modules in service that BAND while storing no
# `band_provenance_class` and no `threshold_source`. They returned a bare dict with a
# `status_color` on it and never went through `models.banded`, which is the function that makes
# a band and its provenance impossible to store apart. `decision_brief._boundary_and_basis` then
# concealed it, falling back to `registry.BAND_SOURCES` and STAMPING "CODIFIED" onto a row that
# recorded nothing, so the card read complete while the row was not. They carry Cost and EVM,
# the heaviest weighted category.
#
# THE FIX IS TO THE STORAGE, WHICH IS WHAT THE ORDER ASKS FOR. Both now return through `banded`,
# and the citation each already carried -- verbatim, from `registry.BAND_SOURCES`, unchanged --
# is what is stored as the basis. NO BOUNDARY MOVES. NO CITATION IS REWRITTEN. The arithmetic,
# the colours and the rendered sentence are byte-identical.
#
# THE TWO PROVENANCE CLASSES ARE NOT THE SAME, AND THAT IS WHY BOTH ARE WRITTEN. The split
# `models.banded` provides for exactly this case is used rather than flattening it:
#
#   band_basis_provenance_class = CODIFIED. The MEASURE and its ANCHOR are fixed by a standards
#   body: PMI defines TCPI as the efficiency the remaining work must achieve, and defines
#   variance at completion as budget less forecast. 1.00 and 0 per cent are DEFINITIONAL
#   boundaries of the metrics themselves, stated by the source.
#
#   band_boundary_provenance_class = CONVENTION. The SECOND boundary of each -- 1.10, and the
#   -11.11 per cent that restates a cost index of 0.90 -- rests on Christensen and Heise's
#   empirical 0.10 stability finding APPLIED BY INFERENCE. A journal study is a published basis,
#   so this is not OWNER-CALIBRATED; it is not a standards clause fixing a band edge, so it is
#   not CODIFIED. Comparing a required efficiency against the index stability finding is what
#   defence earned-value practice does, which is what CONVENTION means in this vocabulary.
#
#   threshold_source = formal_external_basis, for both: the figures came from published
#   instruments and a journal, not from a project document and not from the owner's default
#   table. `THRESHOLD_SOURCES` is NOT widened; this is one of the three values it already holds.
#
# THIS CLASSIFICATION IS A JUDGEMENT AND IS FLAGGED AS ONE. The order says to record what can be
# recorded; the boundary class above is the honest reading of a sourced-number-applied-by-
# inference, and it is reported to the owner for a ruling rather than presented as settled.
_EVM_BASIS_PROVENANCE = PROVENANCE_CODIFIED
_EVM_BOUNDARY_PROVENANCE = PROVENANCE_CONVENTION
_EVM_BOUNDARY_LIMIT = (
    "The stated limit of this citation: the 0.10 cumulative cost index stability finding is "
    "conditional on the project being past twenty per cent complete, and this measure does not "
    "read percent complete, so that condition is not enforced.")


# RUN 114, GOAL 4. PROVENANCE PER EDGE, BECAUSE THE EDGES NO LONGER SHARE ONE PROVENANCE.
#
# `band_boundary_provenance_class` is a SCALAR and it describes the boundary set as a whole. It
# was accurate while every boundary on these two ladders came from the same place. Run 114
# inserts a rung whose edge is the OWNER'S and neither CODIFIED nor CONVENTION, and the order is
# explicit that it must be "recorded accurately rather than inheriting the existing class for
# it". A scalar cannot say two things, so the scalar is LEFT DESCRIBING THE EDGES IT ALWAYS
# DESCRIBED -- the definitional 1.00 / zero per cent and the inferred 1.10 / minus 11.11 per
# cent, neither of which moves -- and the per-edge record below carries the truth for each edge
# separately, with `band_boundary_provenance_classes` listing every class present so nothing
# reading one field can miss that an OWNER-CALIBRATED edge is in the ladder.
#
# THIS IS A JUDGEMENT AND IS FLAGGED AS ONE, on the same footing as the Run 107 classification
# recorded above it: reported to the owner for a ruling rather than presented as settled.
def _EDGE_CLASSES(table: dict) -> list[str]:
    """Every provenance class present on a ladder, sorted, so one field carries the mix."""
    return sorted({v[1] for v in table.values()})


def _evm_band_source(module_id: str) -> str:
    """The Run 4 citation, read from its single source of truth rather than copied here."""
    from .registry import BAND_SOURCES
    return BAND_SOURCES[module_id]


# ------------------------------------------------------------ A1.7 TCPI

#: THE BAND, AND WHERE EACH BOUNDARY COMES FROM. Run 4 (validate the seven). The formula is
#: untouched; only the boundaries and the abstention guard below are this run's work.
#:
#: 1.00 -- DEFINITIONAL, and the source states it in exactly these terms. Project Management
#: Institute, "A Guide to the Project Management Body of Knowledge (PMBOK Guide)", 6th edition,
#: 2017, section 7.4.2.2, and PMI's "Practice Standard for Earned Value Management", 2nd
#: edition, 2011: TCPI is the cost performance the REMAINING work must achieve to meet the
#: stated financial goal. At or below 1.00 the remaining budget is sufficient at the efficiency
#: already planned; above 1.00 the project must do better than planned for the rest of the work.
#: The source specifies this boundary, not merely the metric.
#:
#: 1.10 -- SOURCED NUMBER, APPLIED BY INFERENCE, and the inference is stated rather than hidden.
#: Christensen, D. S. and Heise, S. R., "Cost Performance Index Stability", National Contract
#: Management Journal, 25(1), 1993, pp. 7-15: on a large defence acquisition sample the
#: CUMULATIVE cost performance index does not change by more than 0.10 from the twenty per cent
#: completion point to the end of the project. The number 0.10 is the source's own. The
#: INFERENCE this run draws from it, and it is an inference: a demand for cost efficiency more
#: than 0.10 above what is currently planned asks for a movement in the cumulative index larger
#: than the one that study observed, so it is not supported by the remaining work. That is the
#: same reasoning defence earned-value practice applies when it compares TCPI against CPI; this
#: module has no CPI term, so the 0.10 is applied to the planned efficiency of 1.00.
#:
#: NO SOURCE was found for the boundaries this module carried before (1.05, 1.10, 1.20). They
#: are removed rather than re-cited. The band has three levels because two boundaries are
#: sourced; a fourth level would need a third boundary and there is not one.
_TCPI_PLANNED_EFFICIENCY = 1.00
_TCPI_STABILITY_MARGIN = 0.10
_TCPI_BEYOND_OBSERVED = _TCPI_PLANNED_EFFICIENCY + _TCPI_STABILITY_MARGIN

# RUN 114, GOAL 4. THE YELLOW RUNG, AND IT IS THE OWNER'S NUMBER AND NOBODY ELSE'S.
#
# WHAT WAS WRONG WITH THREE RUNGS. Cost and EVM is the heaviest weighted category at 0.28 and
# this module votes in it. With Green at or below 1.00 and Amber up to 1.10, a project needing
# 1.05 cost efficiency for the remaining work read IDENTICALLY to one needing 1.10, and both
# stepped straight from Green to Amber with nothing between. Every other ladder in this
# platform has four rungs.
#
# 1.05 IS THE OWNER'S RULING, stated in his Run 114 order in these words: "A1.7 TCPI -- Green
# <= 1.00, Yellow > 1.00 to 1.05, Amber > 1.05 to 1.10, Red > 1.10." It is HALF the Christensen
# and Heise stability margin above the planned efficiency, which is a description of where it
# falls and NOT a citation for it: no source fixes 1.05, and none is claimed. It is recorded as
# OWNER-CALIBRATED and it does not inherit the CONVENTION class the 1.10 carries.
#
# THE EXISTING EDGES DO NOT MOVE. 1.00 is still the Green edge and 1.10 is still the Red edge.
# This inserts a rung; it does not re-band. A project that read Green before still reads Green,
# a project that read Red before still reads Red, and the Amber span is the part that is split.
_TCPI_OWNER_YELLOW = 1.05

#: Each edge of A1.7's ladder -> (what the edge is, which provenance class it belongs to).
_TCPI_EDGE_PROVENANCE: dict[str, tuple[str, str]] = {
    "green_at_or_below": ("1.00", PROVENANCE_CODIFIED),
    "yellow_at_or_below": ("1.05", PROVENANCE_OWNER_CALIBRATED),
    "amber_at_or_below": ("1.10", PROVENANCE_CONVENTION),
}


def run_tcpi(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("bac", "ev", "ac")):
        return insufficient("TCPI")
    # RUN 10B, GATE 1. THE DOMAIN GUARD, AND WHY IT IS THE HIGHEST-SEVERITY ONE IN THE LAYER.
    # This module is one of the two that vote on project status, so an out-of-domain reading here
    # does not merely mis-state one row on the ledger, it moves the project's status. The Run 10
    # neighbour sweep found the reproducer: an actual cost reported below zero enlarges the
    # denominator (BAC - AC) beyond the budget itself, the ratio falls, and the module reads
    # Green. The same shape reaches the numerator from the other side: an earned value above the
    # budget at completion makes the remaining work negative and the ratio negative, which is
    # also Green.
    #
    # NO BOUNDARY MOVES AND NOTHING IS CLAMPED. The three sourced band edges above are untouched,
    # and an out-of-domain figure is NOT pulled back to the nearest admissible value, because
    # clamping would hand the module a number nobody reported and it would land, in every case
    # found, in the favourable direction. The module refuses instead.
    #
    # WHERE EACH DOMAIN COMES FROM, and each is definitional rather than chosen here:
    #   budget at completion  > 0   -- it is the authorised total budget of the work. There is no
    #                                  cost efficiency that finishes remaining work against a
    #                                  budget of nothing or less.
    #   earned value         >= 0   -- it is the budgeted value of work PERFORMED. Negative work
    #                                  has not been performed.
    #   earned value      <= budget -- the same definition bounds it above: the value that can be
    #                                  earned is the value that was budgeted.
    #   actual cost          >= 0   -- it is cost incurred. A negative incurred cost is not a
    #                                  measurement of spending.
    _domains = (
        ("bac", si["bac"], lambda v: v > 0,
         "the budget at completion is reported at or below zero, which is not a budget the "
         "remaining work can be measured against"),
        ("ev", si["ev"], lambda v: v >= 0,
         "the earned value is reported below zero, and the budgeted value of work performed "
         "cannot be negative"),
        ("ac", si["ac"], lambda v: v >= 0,
         "the actual cost is reported below zero, and a cost incurred cannot be negative"),
    )
    for _key, _raw, _ok, _words in _domains:
        _v = num(_raw, None)
        if _v is None or not _ok(_v):
            return insufficient(
                "TCPI",
                f"No cost efficiency is measurable for the remaining work: {_words}. No "
                f"substitute figure is used in its place.",
                ABSTAIN_MALFORMED_INPUT)
    if num(si["ev"], None) > num(si["bac"], None):
        return insufficient(
            "TCPI",
            "No cost efficiency is measurable for the remaining work: the earned value is "
            "reported above the budget at completion, and the budgeted value of work performed "
            "cannot exceed the value that was budgeted. No substitute figure is used in its "
            "place.",
            ABSTAIN_MALFORMED_INPUT)
    remaining_work = si["bac"] - si["ev"]
    remaining_budget = si["bac"] - si["ac"]
    if remaining_budget <= 0:
        # THE ABSTENTION GUARD THE RUN NAMES. (BAC - AC) is the denominator, and it is exactly
        # zero when actual cost has reached the budget, which is the ordinary state of a project
        # at completion rather than an exotic one. This used to return Red with no ratio: a
        # status manufactured from a division that could not be performed, indistinguishable at
        # every downstream surface from a Red that was measured. There is no cost efficiency
        # that finishes the remaining work inside a remaining budget of nothing, so the honest
        # output is no finding, not the worst finding.
        return insufficient(
            "TCPI",
            "Awaiting a remaining budget to measure against: actual cost has reached or passed "
            "the budget at completion, so there is no remaining funding for the efficiency this "
            "measure states",
        )
    # RUN 35 FINAL CLOSURE. ROUNDING IS PRESENTATION, AND IT NO LONGER REACHES THE BAND.
    #
    # THE DEFECT RUN 35 MEASURED AND THIS CLOSURE REPAIRS. This line used to read
    # `tcpi = _round3(remaining_work / remaining_budget)`, and every use below -- the band, the
    # emitted analytical field, the displayed string -- read that one rounded number. Two
    # consequences followed, and the second is the serious one:
    #
    #   1. the emitted analytical value was not the published identity. On the Run-35 governed
    #      corpus it differed from (BAC - EV) / (BAC - AC) by exactly -3/7000, which is why the
    #      Run-35 partial reference standard recorded a genuine FAIL against PMI's definition.
    #
    #   2. THE BAND WAS ASSIGNED FROM THE ROUNDED VALUE, so premature rounding could change a
    #      STATUS and not merely a displayed number. The pre-change measurement pinned at
    #      `code_audit/run35_voter_prechange_measurement.json` found twenty-eight governed
    #      inputs on which this module answered Green while the full-precision index was above
    #      1.00 and implied Amber. This module is one of the two that vote on project status, so
    #      that is a wrong vote, not a cosmetic one.
    #
    # THE SEPARATION IS NOW EXPLICIT AND IS THE WHOLE FIX. `tcpi` is the canonical numeric value
    # at the full precision the application already carries; the band is derived from it; and
    # `tcpi_display` is a presentation value that nothing analytical reads. NO NEW PRECISION IS
    # INTRODUCED -- this is a separation of concerns, not a precision upgrade, and `_round3` is
    # the same presentation helper it always was. No presentation helper mutates the analytical
    # value: `_round3` is called on a copy and its result is never fed back.
    tcpi = remaining_work / remaining_budget
    color = ("Green" if tcpi <= _TCPI_PLANNED_EFFICIENCY
             else "Yellow" if tcpi <= _TCPI_OWNER_YELLOW
             else "Amber" if tcpi <= _TCPI_BEYOND_OBSERVED else "Red")
    word = ("within the efficiency already planned" if tcpi <= _TCPI_PLANNED_EFFICIENCY
            else "above the efficiency planned, inside the owner's tolerance"
            if tcpi <= _TCPI_OWNER_YELLOW
            else "above the efficiency planned" if tcpi <= _TCPI_BEYOND_OBSERVED
            else "beyond the improvement a cumulative cost index is observed to make")
    tcpi_display = _round3(tcpi)
    return banded(
        "TCPI",
        (f"TCPI: {_js_str(tcpi_display)}, the cost efficiency the remaining work must achieve "
         f"to finish within budget, {word}"),
        status_color=color,
        boundary=_evm_band_source("A1.7"),
        basis=_evm_band_source("A1.7") + " " + _EVM_BOUNDARY_LIMIT,
        provenance=_EVM_BASIS_PROVENANCE,
        boundary_provenance=_EVM_BOUNDARY_PROVENANCE,
        threshold_source=THRESHOLD_SOURCE_EXTERNAL,
        band_boundary_provenance_by_edge=_TCPI_EDGE_PROVENANCE,
        band_boundary_provenance_classes=_EDGE_CLASSES(_TCPI_EDGE_PROVENANCE),
        band_owner_inserted_edge="Yellow at or below 1.05",
        tcpi=tcpi,
        tcpi_display=tcpi_display,
    )


# ------------------------------------------------------------ A1.8 Variance at Completion

#: THE BAND, AND WHERE EACH BOUNDARY COMES FROM. Run 4 (validate the seven). The formula is
#: untouched: EAC = BAC / CPI, VAC = BAC - EAC, and the percentage is VAC over BAC. Because the
#: forecast is the index-based one, the percentage is an exact restatement of the index:
#: VAC% = (1 - 1/CPI) x 100. A boundary on the percentage is therefore a boundary on CPI, exactly
#: and not approximately, which is what lets a sourced statement about CPI be cited here honestly.
#:
#: 0 per cent -- DEFINITIONAL. Project Management Institute, "A Guide to the Project Management
#: Body of Knowledge (PMBOK Guide)", 6th edition, 2017, section 7.4.2.2, and PMI's "Practice
#: Standard for Earned Value Management", 2nd edition, 2011: variance at completion is the
#: difference between the approved budget and the forecast final cost, and a negative variance
#: at completion is a forecast overrun. The source specifies the boundary: at zero the forecast
#: meets the budget, below zero it does not. This is the boundary the metric is defined around.
#:
#: -11.11 per cent -- SOURCED NUMBER, APPLIED BY INFERENCE, stated rather than hidden.
#: Christensen, D. S. and Heise, S. R., "Cost Performance Index Stability", National Contract
#: Management Journal, 25(1), 1993, pp. 7-15: the CUMULATIVE cost performance index does not
#: change by more than 0.10 from the twenty per cent completion point to the end. The number is
#: the source's own. The INFERENCE: an index below 0.90 forecasts an overrun the remaining work
#: is not observed to recover, because recovery would require the cumulative index to move
#: further than that study saw it move. The percentage is computed from 0.90 rather than
#: written as a rounded figure, so the boundary is the source's number and not a near one.
#:
#: NO SOURCE was found for the boundaries this module carried before (-5, -10, -20 per cent).
#: They are removed rather than re-cited.
#:
#: THE LIMIT OF THIS CITATION, and it belongs beside the band. The stability finding is
#: conditional on the project being past twenty per cent complete, and this module does not read
#: percent complete, so the condition is not enforced here. Enforcing it would change the
#: module's input contract, which this run is not permitted to do. Recorded as a stated limit of
#: the band rather than left for a reader to discover.
_VAC_STABILITY_CPI = 0.90
# RUN 135, H2, R1. EVERY EDGE IS EXPRESSED IN THE ONE CANONICAL QUANTITY. This was the literal
# 0.0; it is the same number, written the way the Run 114 order names the quantity, so that a
# reader can see all three edges are the same expression evaluated at 1.00, 0.95 and 0.90.
_VAC_BUDGET_MET_CPI = 1.00
_VAC_BUDGET_MET_PCT = (1 - 1 / _VAC_BUDGET_MET_CPI) * 100                       # 0.0
_VAC_BEYOND_OBSERVED_PCT = (1 - 1 / _VAC_STABILITY_CPI) * 100

# RUN 114, GOAL 4. THE YELLOW RUNG ON THIS MODULE'S OWN QUANTITY, AND HOW ITS NUMBER WAS SET.
#
# WHAT THE BOUNDARIES WERE, MEASURED AT THE PARENT COMMIT AND NOT ASSUMED: Green at or above
# zero per cent, Amber at or above minus 11.11 per cent, Red below. Three rungs, the same
# coarse shape A1.7 had.
#
# THE OWNER ORDERED "the same shape on its own quantity", keeping the existing Green and Red
# edges. This module's quantity is the VAC percentage, and because the forecast is the
# index-based one that percentage is an EXACT restatement of the cost performance index:
# VAC% = (1 - 1/CPI) x 100. That identity is what lets the two existing edges be stated on the
# index at all -- zero per cent IS an index of 1.00, and minus 11.11 per cent IS an index of
# 0.90 -- and it is stated in the block above this one, not introduced here.
#
# SO THE ANALOGUE IS EXACT AND IS NOT AN ANALOGY. The owner set A1.7's Yellow edge at 1.05,
# which is the planned efficiency of 1.00 moved by HALF the 0.10 stability margin. The same
# construction on this module's own index, moved in this module's own adverse direction, is
# 1.00 - 0.10/2 = 0.95, and restating it on the percentage by the identity above gives
# (1 - 1/0.95) x 100 = -5.263157894736842 per cent. It lies strictly between the two existing
# edges, and both of them stay exactly where they were.
#
# THIS NUMBER IS THE OWNER'S, NOT CHRISTENSEN AND HEISE'S. The 0.10 is theirs; halving it and
# placing a rung at the half is the owner's Run 114 ruling, made on A1.7 and carried across by
# the identity. It is recorded OWNER-CALIBRATED per edge, and it does not inherit the
# CONVENTION class the minus 11.11 carries.
_VAC_OWNER_YELLOW_CPI = _VAC_STABILITY_CPI + (1.0 - _VAC_STABILITY_CPI) / 2.0   # 0.95
_VAC_OWNER_YELLOW_PCT = (1 - 1 / _VAC_OWNER_YELLOW_CPI) * 100                   # -5.2631578...

#: Each edge of A1.8's ladder -> (what the edge is, which provenance class it belongs to).
_VAC_EDGE_PROVENANCE: dict[str, tuple[str, str]] = {
    "green_at_or_above": ("0.00 per cent (cost performance index 1.00)", PROVENANCE_CODIFIED),
    "yellow_at_or_above": ("-5.263157894736842 per cent (cost performance index 0.95)",
                           PROVENANCE_OWNER_CALIBRATED),
    "amber_at_or_above": ("-11.11111111111111 per cent (cost performance index 0.90)",
                          PROVENANCE_CONVENTION),
}


def run_vac(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("bac", "cpi")):
        return insufficient("VAC")
    if si["cpi"] <= 0:
        # JS Infinity arithmetic at zero (see VALIDATION.md), and a NEGATIVE index is outside
        # the domain of the index-based forecast entirely: it produces a negative estimate at
        # completion, hence a positive variance, hence Green on a project that has recorded no
        # earned value at all. Both refuse.
        return insufficient(
            "VAC",
            "Awaiting a cost performance index above zero: the forecast at completion is the "
            "budget divided by that index, which cannot be formed here",
        )
    if si["bac"] == 0:
        # bac=0: the JS NaN fallthrough this module has always refused. The forecast at
        # completion is the budget divided by the index, and there is no budget to divide.
        return insufficient("VAC")
    eac = si["bac"] / si["cpi"]
    vac = si["bac"] - eac
    # RUN 135, FINDING H2, UNDER RULING R1 -- ONE CANONICAL DECISION QUANTITY, AND THIS IS IT.
    #
    # WHAT THIS LINE WAS: `vac_pct = (vac / si["bac"]) * 100`, that is,
    # ((BAC - BAC/CPI) / BAC) x 100. Algebra says that is (1 - 1/CPI) x 100 and the budget
    # cancels. FLOATING-POINT ARITHMETIC DOES NOT SAY SO. The two expressions differ by 1 to 9
    # units in the last place, and WHICH WAY they differ is decided by the binary representation
    # of the budget at completion. The band edges are themselves written as (1 - 1/x) x 100, so
    # the comparison was between two algebraically equal quantities computed along two different
    # paths, and the answer moved with a number that is not in the quantity at all:
    #
    #   CPI exactly 0.90:  BAC   1,000,000 -> Amber     BAC 330,000,000 -> Red
    #                      BAC   4,400,000 -> Amber     BAC      15,000 -> Red
    #
    # A sweep of $1k to $200M found 5.9 per cent of budgets banding Red at an index that is
    # exactly ON the inclusive Amber edge, and 0.8 per cent reaching the Yellow edge the same
    # way. The project's cost posture depended on the size of its contract.
    #
    # THE FIX IS THE RULING, NOT AN EPSILON. A tolerance would have left both paths in place and
    # added an unauthorised threshold on top of them. Instead there is now ONE quantity, and it
    # is the one the RUN 114 ORDER NAMES -- quoted verbatim in commit `fc9d60c`:
    #
    #       VAC% = (1 - 1/CPI) x 100
    #
    # computed exactly that way, in the same expression every edge above is expressed in. The
    # budget is not in it, so no band on it can move with the budget. `vac` -- the DOLLAR figure
    # the sentence reports -- is still BAC - BAC/CPI, because that is a money amount and money
    # amounts do depend on the budget; it is reported, and it is not what bands.
    vac_pct = (1 - 1 / si["cpi"]) * 100
    color = ("Green" if vac_pct >= _VAC_BUDGET_MET_PCT
             else "Yellow" if vac_pct >= _VAC_OWNER_YELLOW_PCT
             else "Amber" if vac_pct >= _VAC_BEYOND_OBSERVED_PCT else "Red")
    # RUN 35 FINAL CLOSURE. THE SAME SEPARATION, FOR THE SAME REASON.
    #
    # The band here was ALREADY derived from the full-precision percentage, so this module never
    # had A1.7's status defect and none is claimed. What it did have is the first consequence:
    # the emitted analytical field was `int(js_round(vac))`, a whole-dollar presentation value,
    # and on the Run-35 governed corpus that differed from the published identity
    # BAC - BAC/CPI by exactly +10/909. The Run-35 reference comparison read that field, so the
    # FAIL it recorded was real.
    #
    # `vac` and `vac_pct` are now the canonical values at the precision the application already
    # carries; `vac_display` and `vac_pct_display` are presentation only. VAC SEMANTICS AND
    # VOTING DIRECTION ARE UNCHANGED: negative is still a forecast overrun, the band edges are
    # the same two sourced boundaries, and the displayed sentence is byte-identical to what it
    # rendered before, because it was already built from the unrounded value.
    return banded(
        "VAC",
        (f"VAC: {_money(abs(vac))} {'over' if vac < 0 else 'under'} budget "
         f"({_js_str(round1(abs(vac_pct)))}%)"),
        status_color=color,
        boundary=_evm_band_source("A1.8"),
        basis=_evm_band_source("A1.8") + " " + _EVM_BOUNDARY_LIMIT,
        provenance=_EVM_BASIS_PROVENANCE,
        boundary_provenance=_EVM_BOUNDARY_PROVENANCE,
        threshold_source=THRESHOLD_SOURCE_EXTERNAL,
        band_boundary_provenance_by_edge=_VAC_EDGE_PROVENANCE,
        band_boundary_provenance_classes=_EDGE_CLASSES(_VAC_EDGE_PROVENANCE),
        band_owner_inserted_edge=(
            "Yellow at or above -5.26 per cent, the exact restatement of a cost performance "
            "index of 0.95"),
        vac=vac,
        vac_pct=vac_pct,
        vac_display=int(js_round(vac)),
        vac_pct_display=round1(vac_pct),
    )


# ------------------------------------------------------------ A1.9 Budget Execution Rate


def run_budget_execution(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 28, v3. THE APPROVED EXPENDITURE PROFILE, NOT BUDGET TIMES PERCENT COMPLETE.

    THE SUPPLIED CONTRACT. This is a PCEIF transparent expenditure-control indicator and is not
    claimed to be a universal standardised statistical method. ExecutionRatio(t) = AC(t) /
    ExpectedSpend(t) and ExecutionDeviation(t) = ratio - 1, where ExpectedSpend comes from an
    APPROVED time-phased expenditure baseline. The contract states that ExpectedSpend must not be
    manufactured from BAC times a generic percent complete, and that with no approved profile the
    answer is NOT ESTIMABLE. It supplies no status bands.

    WHAT v2 DID, exactly the forbidden thing: expected = bac * (actualPctComplete / 100). That
    treats spending as planned to follow physical progress in a straight line, which no
    expenditure baseline asserts, and it made the ratio a function of the progress figure rather
    than of a plan anybody approved.

    v3 REQUIRES THE EXPENDITURE BASELINE, read at the governed status period, with its version
    and approval source. Where it is absent the module ABSTAINS. Both the ratio and its deviation
    are reported. No band is asserted: the contract supplies none, and the boundaries v2 carried
    were drawn over the progress-scaled figure rather than over this one.
    """
    if not check_inputs(si, ("ac",)):
        return insufficient("Budget_Execution_Rate",
                            "Insufficient data: the actual cost has not been reported for this "
                            "period.", ABSTAIN_MISSING_INPUT)
    try:
        structure = require_v3_structure(si, "A1.9")
        period_index = num(structure.get("status_period_index"), None)
        if period_index is None:
            raise StructureAbsent(
                "The approved expenditure baseline provided does not say which period the "
                "project is being reported at, so no planned amount can be read off it.")
        profile = expenditure_baseline_to_date(structure, float(period_index))
        reading = budget_execution(profile["expected_spend"], num(si.get("ac"), None))
    except StructureAbsent as absent:
        return insufficient("Budget_Execution_Rate", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    # ---------------------------------------------- RUN 107. TWO COMPONENTS, WORST-OF.
    #
    # THE LADDER BANDS OVER-EXECUTION ONLY, AND THIS RUN CORRECTS RUN 106'S CENSUS, WHICH
    # RECORDED THE QUANTITY AS TWO-SIDED. The owner's Run 107 order: "The owner's ladder bands
    # over-execution only. Under-execution is not adverse here." A ratio well BELOW 1.05 is
    # Green -- spending less than the approved profile plans is not banded as a fault by this
    # measure, and the ladder's shape says so by construction rather than by a note.
    _comps = []
    _cum = reading["execution_ratio"]
    _boundary_words = ("at or below 1.05 is Green; above 1.05 and at or below 1.10 is Yellow; "
                       "above 1.10 and at or below 1.15 is Amber; above 1.15 is Red. Each "
                       "boundary is INCLUSIVE ON ITS UPPER SIDE. OVER-EXECUTION ONLY: a ratio "
                       "below 1.05, however far below, is Green, because under-execution is "
                       "not adverse on this measure")
    _comps.append(_OB.component(
        "cumulative actual over cumulative planned", value=_round3(_cum),
        band=_OB.ascending(_cum, 1.05, 1.10, 1.15),
        boundary="cumulative actual divided by cumulative planned: " + _boundary_words + "."))
    _pexp = profile.get("period_expected_spend")
    _pact = num(structure.get("period_actual_cost"), None)
    if _pexp is not None and _pexp > 0 and _pact is not None and _pact >= 0:
        _pr = _pact / _pexp
        _comps.append(_OB.component(
            "this period's actual over this period's planned", value=_round3(_pr),
            band=_OB.ascending(_pr, 1.05, 1.10, 1.15),
            boundary="this period's actual divided by this period's planned: "
                     + _boundary_words + "."))
    else:
        _comps.append(_OB.component(
            "this period's actual over this period's planned",
            absent_reason=(
                "This project's approved expenditure baseline does not state the actual cost "
                "incurred in this period beside the amount planned for it, so the period ratio "
                "has no numerator. NOT ASSESSED. The cumulative actual is not divided by the "
                "period plan and no period figure is inferred from the cumulative one.")))
    _agg = _OB.aggregate(_comps)
    _posture = _agg["band_posture_before_override"]
    _limit = num(structure.get("approved_cumulative_funding_limit"), None)
    if _limit is None:
        _limit = num(structure.get("approved_cash_flow_limit"), None)
    _override = _limit is not None and _limit > 0 and reading["actual_cost"] > _limit
    if _override:
        _posture = _OB.at_least_as_adverse_as(_posture, "Red")
    _override_words = (
        "HARD OVERRIDE: Red if actual expenditure exceeds the approved cumulative funding or "
        "cash-flow limit for the reporting date. ")
    _override_words += (
        "This project's expenditure baseline states no approved cumulative funding or cash-flow "
        "limit, so the override was NOT EVALUABLE and its absence was not read as the limit "
        "being met." if _limit is None
        else "It fired: actual expenditure is above the stated limit." if _override
        else "Actual expenditure is at or below the stated limit, so it did not fire.")
    _fields = dict(
        execution_ratio=_round3(reading["execution_ratio"]),
        execution_deviation=_round3(reading["execution_deviation"]),
        expected_spend=reading["expected_spend"],
        actual_cost=reading["actual_cost"],
        period_expected_spend=_pexp,
        period_actual_cost=_pact,
        approved_cumulative_funding_limit=_limit,
        baseline_version=profile["baseline_version"],
        approval_source=profile["approval_source"],
        band_hard_override_fired=_override,
        band_hard_override_evaluable=_limit is not None,
        band_direction_note=("this ladder bands OVER-execution only; under-execution is not "
                             "adverse on this measure and is Green"),
        canonical_structure="expenditure_baseline",
        **_agg)
    _msg = (
        f"Spending is {_money(reading['actual_cost'])} against the "
        f"{_money(reading['expected_spend'])} the approved expenditure baseline plans by this "
        f"point, an execution ratio of {_js_str(_round3(reading['execution_ratio']))}")
    return banded(
        "Budget_Execution_Rate", _msg,
        status_color=_posture,
        boundary=(" ".join(c["boundary"] for c in _comps if c["boundary"])
                  + " " + _agg["band_aggregation_words"] + " " + _override_words),
        basis=_run107_basis("section 1, A1.9",
                            "1.05, 1.10 and 1.15 on a budget execution ratio"),
        provenance=PROVENANCE_OWNER_CALIBRATED,
        threshold_source=THRESHOLD_SOURCE_OWNER,
        band_basis_id=_RUN107_BASIS_ID,
        **_fields)




# ------------------------------------------------------------ A1.10 CPI Shrinkage Forecast


def run_cpi_shrinkage(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 28, v3. APPROVED RENAME: Regression to Mean CPI becomes CPI SHRINKAGE FORECAST.

    THE SUPPLIED CONTRACT. Do not implement an assumption that cost performance inherently
    regresses toward 1.0. Use statistical partial pooling toward a GOVERNED REFERENCE-CLASS
    expectation: CPI_shrunk = w * CPI_project + (1 - w) * mu_reference with w between nought and
    one. It requires a governed reference population, a reference mean or model, the estimation
    and provenance of the shrinkage weight, and the project stage the estimator is used at, and
    it states in terms that a hard-coded 0.5 weight is not acceptable as a calibrated
    implementation and that with no reference class the answer is NOT ESTIMABLE.

    WHAT v2 DID, and it did both forbidden things at once: mean + (current - mean) * 0.5, where
    the weight was the literal 0.5 and the "mean" was the mean of THIS PROJECT'S OWN history.
    Pooling a reading toward the mean of the same readings is not partial pooling toward an
    outside expectation; it is a smoother, and it carries no reference population at all.

    v3 REQUIRES THE REFERENCE CLASS: the comparable projects, the cost performance each achieved,
    the basis of class membership, the method by which the weight was estimated, and the data
    vintage. The project being assessed may not be a member of the class it is pooled toward, and
    a weight declared as fixed or hard-coded is refused outright. Where the class is absent the
    module ABSTAINS. No band is asserted; the final empirical weight calibration is Run 33.
    """
    try:
        structure = require_v3_structure(si, "A1.10")
        reference = cpi_reference_class(structure)
        cpi = num(si.get("cpi"), None)
        if cpi is None:
            raise StructureAbsent(
                "This project's own cost performance has not been reported for this period, so "
                "there is nothing to pool toward the reference population.")
        reading = cpi_shrinkage(float(cpi), reference["mu_reference"],
                                reference["shrinkage_weight"])
    except StructureAbsent as absent:
        return insufficient("CPI_Shrinkage_Forecast", absent.sentence, ABSTAIN_STRUCTURE_ABSENT)
    return calibration_pending(
        "CPI_Shrinkage_Forecast",
        f"Pooled cost performance {_js_str(_round3(reading['cpi_shrunk']))}: this project's "
        f"{_js_str(_round3(reading['cpi_project']))} carries a weight of "
        f"{_js_str(_round3(reading['weight']))} against "
        f"{_js_str(_round3(reading['mu_reference']))} across "
        f"{reference['members']} comparable projects",
        cpi_shrunk=_round3(reading["cpi_shrunk"]),
        shrinkage_weight=reading["weight"],
        cpi_project=_round3(reading["cpi_project"]),
        mu_reference=_round3(reading["mu_reference"]),
        reference_variance=reference["reference_variance"],
        reference_members=reference["members"],
        class_membership_basis=reference["class_membership_basis"],
        weight_estimation_method=reference["weight_estimation_method"],
        data_vintage=reference["data_vintage"],
        project_stage=reference["project_stage"],
        canonical_structure="cpi_reference_class",
    )


# ------------------------------------------- A1.11 Independent EAC Reconciliation Index


def _pending_change_reconciliation(si: dict, structure: dict) -> dict[str, Any]:
    """
    RUN 115. The owner's redefined A1.11: pending change exposure against the approved budget.

    WHETHER THE RUN 107 LADDER SURVIVES, WHICH THE ORDER REQUIRED BE ESTABLISHED RATHER THAN
    ASSUMED. Run 107 gave this module TWO components on one ladder of 3, 5 and 10 per cent:

      (1) the spread between the two forecasts, over BAC;
      (2) the HIGHER forecast above BAC, over BAC.

    Under the redefinition the two forecasts are the approved budget itself and the approved
    budget plus pending exposure. Component (1) is then
    |(BAC + pending) - BAC| / BAC = |pending| / BAC, and component (2) is
    max(0, (BAC + pending) - BAC) / BAC = max(0, pending) / BAC. THEY ARE THE SAME QUANTITY on
    every project whose pending exposure is additive, and they differ only in sign handling
    where it is net deductive. Reporting them as two components would put one measurement on
    the card twice and let an aggregation rule treat it as corroboration. So component (1) is
    NOT carried, component (2) survives verbatim, and the module reports ONE component.

    NO NEW LADDER IS INVENTED AND NONE IS NEEDED. The surviving component is the owner's own
    Run 107 rung set on the identical quantity it was set on -- a forecast standing above the
    budget, as a percentage of the budget -- so the owner is not asked to supply one.

    A NET DEDUCTIVE PENDING POSITION IS GREEN AND IS NEVER NEGATIVE. Pending credits do not earn
    a project a better posture than nought exposure, and they are not netted into a discount.
    """
    try:
        reading = pending_change_exposure(structure)
    except StructureAbsent as absent:
        return insufficient("Independent_EAC_Reconciliation", absent.sentence,
                            ABSTAIN_STRUCTURE_ABSENT)
    _bac = num(si.get("bac"), None)
    _pending = reading["pending_change_value"]
    _fac = None if _bac is None else float(_bac) + _pending
    _ladder = ("at or below 3 per cent is Green; above 3 and at or below 5 is Yellow; above 5 "
               "and at or below 10 is Amber; above 10 is Red. Each boundary is INCLUSIVE ON "
               "ITS UPPER SIDE")
    _comps = []
    if _bac is not None and _bac > 0:
        _over = max(0.0, _pending / float(_bac))
        _comps.append(_OB.component(
            "pending change exposure above the approved budget", value=round(_over * 100, 2),
            band=_OB.ascending(_over * 100, 3.0, 5.0, 10.0),
            boundary=("the value of the changes the contractor has submitted and the owner has "
                      "not yet approved, divided by the approved budget at completion, on the "
                      "owner's Run 107 ladder: " + _ladder + ". A net deductive pending "
                      "position is nought per cent above the budget and is Green; the quantity "
                      "is never negative and pending credits are never netted into a "
                      "discount.")))
    else:
        _comps.append(_OB.component(
            "pending change exposure above the approved budget",
            absent_reason=("The approved budget at completion has not been reported for this "
                           "period, and the measure is stated as a proportion of it, so it has "
                           "no denominator. NOT ASSESSED. No other figure is used in its "
                           "place.")))
    _agg = _OB.aggregate(_comps)
    _posture = _agg["band_posture_before_override"]
    _cont = num(si.get("remainingContingency"), None)
    _gap = None if _bac is None or _bac <= 0 else max(0.0, _pending)
    _override = (_gap is not None and _gap > 0 and _cont is not None and _cont < _gap)
    if _override:
        _posture = _OB.at_least_as_adverse_as(_posture, "Red")
    _override_words = (
        "HARD OVERRIDE: Red if the pending changes would carry the forecast above the approved "
        "budget and the remaining approved contingency cannot cover the gap. ")
    if _gap is None:
        _override_words += ("No approved budget was reported, so the override was NOT "
                            "EVALUABLE.")
    elif _gap <= 0:
        _override_words += ("The pending position does not carry the forecast above the "
                            "budget, so it did not fire.")
    elif _cont is None:
        _override_words += ("The pending position carries the forecast above the budget but no "
                            "remaining approved contingency was reported, so the override was "
                            "NOT EVALUABLE and an unreported contingency was not treated as "
                            "sufficient.")
    elif _override:
        _override_words += "It fired: the remaining contingency is smaller than the exposure."
    else:
        _override_words += "The remaining contingency covers the exposure, so it did not fire."
    _fields = dict(
        pending_change_value=_pending,
        pending_change_count=reading["pending_change_count"],
        approved_change_count=reading["approved_change_count"],
        change_count=reading["change_count"],
        pending_changes=reading["pending_changes"],
        approved_budget=_bac,
        forecast_at_completion=_fac,
        remaining_contingency=_cont,
        eac_gap_above_bac=_gap,
        band_hard_override_fired=_override,
        band_hard_override_evaluable=(_gap is not None and (_gap <= 0 or _cont is not None)),
        canonical_structure="pending_change_exposure",
        source=reading["source"],
        measure_note=(
            "The forecast at completion on this path is the approved budget plus the changes "
            "submitted and not yet approved. It is not a second, independently prepared "
            "estimate and is never presented as one."),
        **_agg)
    _msg = (
        f"{_js_str(reading['pending_change_count'])} of "
        f"{_js_str(reading['change_count'])} changes on the register "
        f"{'is' if reading['pending_change_count'] == 1 else 'are'} still awaiting approval, "
        f"worth {_money(_pending)}"
        + ("" if _fac is None else
           f", which would carry the forecast at completion to {_money(_fac)} against an "
           f"approved budget of {_money(_bac)}"))
    if _posture is None:
        return band_abstained(
            "Independent_EAC_Reconciliation", _msg,
            reason=("Not Assessed. " + _comps[0]["not_assessed_reason"]),
            band_basis_id=_RUN107_BASIS_ID, **_fields)
    return banded(
        "Independent_EAC_Reconciliation", _msg,
        status_color=_posture,
        boundary=(" ".join(c["boundary"] for c in _comps if c["boundary"])
                  + " " + _override_words),
        basis=_run107_basis("section 1, A1.11",
                            "3, 5 and 10 per cent of the approved budget, on the owner's Run "
                            "115 redefinition of the measure as pending change exposure "
                            "against that budget"),
        provenance=PROVENANCE_OWNER_CALIBRATED,
        threshold_source=THRESHOLD_SOURCE_OWNER,
        band_basis_id=_RUN107_BASIS_ID,
        **_fields)


def run_independent_eac_reconciliation(si: dict, rand: Callable[[], float],
                                       period_cutoff) -> dict[str, Any]:
    """
    RUN 28, v3. APPROVED RENAME: ICE Ratio becomes INDEPENDENT EAC RECONCILIATION INDEX.

    THE SUPPLIED CONTRACT. Two genuinely provenance-distinct forecasts are required, a Management
    EAC and an Independent EAC, and the module reports IER = Independent / Management and
    Divergence = (Independent - Management) / Management. Each estimate must preserve its source,
    method, assumptions, model version, responsible party and lineage, and the contract states in
    terms that two transformations of the same BAC/CPI/EV/AC vector are NOT independent and that
    with no genuinely distinct estimate the answer is NOT ESTIMABLE.

    WHAT v2 DID, exactly the forbidden thing: (bac / cpi) divided by (ac + (bac - ev)). Both
    sides are arithmetic on one vector of four reported figures, prepared by nobody, with no
    method, assumptions or responsible party attached to either. The ratio was published as a
    reconciliation between an independent estimate and a management one when no second estimate
    existed anywhere.

    v3 REQUIRES THE PAIR, and checks independence rather than asserting it: both sides must state
    all five lineage fields, and the two must differ on the method AND on the responsible party.
    Where the pair is absent, incomplete, or not genuinely distinct, the module ABSTAINS. No band
    is asserted: reconciliation bands are named in the contract as calibration dependent.
    """
    # ============================================ RUN 115, GOAL 2. THE OWNER'S REDEFINITION.
    #
    # THE MEASURE HAS CHANGED, and this comment is the record of what it was and what it is.
    #
    # BEFORE: two genuinely provenance-distinct forecasts, IER = Independent / Management, with
    # independence checked on five lineage fields. Run 109 classified the module UNSERVABLE: no
    # document type carries a second estimate at all, and no document can establish that a
    # second estimate was prepared independently of the first. That is a property of documents,
    # not of the implementation, and no assembler could have fixed it.
    #
    # AFTER, in the owner's Run 115 words: the forecast at completion is the approved contract
    # plus the change orders the contractor has submitted and the owner has not yet approved.
    # Once a change order is approved it becomes part of the budget. So the comparison is the
    # budget as it stands against the budget as it will stand if the pending changes go through
    # -- PENDING CHANGE EXPOSURE AGAINST THE APPROVED BUDGET. Both figures are already on the
    # platform: the approved budget is `bac`, and the pending side comes off the change order
    # register's own approval column, which Run 115 added because Run 114's assembler carried
    # identity, issue day, type, cause, value and direction and nothing that distinguished an
    # approved change from a pending one.
    #
    # THE OLD PATH IS NOT DELETED. `independentEacPair` is referenced by name in six suites and
    # a driver in this tree, so the order's condition for retiring it -- "only if nothing else
    # reads it" -- is NOT met, and it also carries strictly more information than the new
    # measure where a project genuinely has two forecasts. A project supplying the pair is read
    # on the pair; every other project is read on its pending exposure.
    _pair = si.get("independentEacPair")
    _exposure_structure = si.get("pendingChangeExposure")
    if _pair is None and isinstance(_exposure_structure, dict):
        return _pending_change_reconciliation(si, _exposure_structure)
    if _pair is None:
        # THE ABSTENTION SENTENCE NAMES BOTH PATHS, because both now serve this module and a
        # sentence naming only the pair would tell a project manager to obtain a document no
        # document type on this platform carries.
        return insufficient(
            "Independent_EAC_Reconciliation",
            "Awaiting the change orders submitted and not yet approved. This measure compares "
            "the approved budget with the budget as it would stand if the pending changes go "
            "through, so it needs a change order register stating, for every change, its value "
            "and whether the owner has approved it. A project that instead holds two "
            "separately prepared forecasts of the cost at completion is read on those. Neither "
            "was provided, and no other figure is used in their place.",
            ABSTAIN_STRUCTURE_ABSENT)
    try:
        structure = require_v3_structure(si, "A1.11")
        reading = independent_eac_reconciliation(structure.get("management_eac"),
                                                 structure.get("independent_eac"))
    except StructureAbsent as absent:
        return insufficient("Independent_EAC_Reconciliation", absent.sentence,
                            ABSTAIN_STRUCTURE_ABSENT)
    # ---------------------------------------------- RUN 107. TWO COMPONENTS, WORST-OF.
    _bac = num(si.get("bac"), None)
    _comps = []
    _ladder = ("at or below 3 per cent is Green; above 3 and at or below 5 is Yellow; above 5 "
               "and at or below 10 is Amber; above 10 is Red. Each boundary is INCLUSIVE ON "
               "ITS UPPER SIDE")
    _higher = max(reading["management_eac"], reading["independent_eac"])
    if _bac is not None and _bac > 0:
        _spread = abs(reading["independent_eac"] - reading["management_eac"]) / float(_bac)
        _comps.append(_OB.component(
            "spread between the two forecasts", value=round(_spread * 100, 2),
            band=_OB.ascending(_spread * 100, 3.0, 5.0, 10.0),
            boundary=("the absolute difference between the independent and the control "
                      "forecast, divided by the budget at completion: " + _ladder + ".")))
        _over = max(0.0, (_higher - float(_bac)) / float(_bac))
        _comps.append(_OB.component(
            "higher forecast above budget at completion", value=round(_over * 100, 2),
            band=_OB.ascending(_over * 100, 3.0, 5.0, 10.0),
            boundary=("the higher of the two forecasts less the budget at completion, divided "
                      "by the budget at completion, on the SAME ladder: " + _ladder + ". A "
                      "higher forecast at or below the budget is nought per cent above it and "
                      "is Green; the quantity is never negative.")))
    else:
        _absent = ("The budget at completion has not been reported for this period, and both of "
                   "the owner's components are measured against it, so neither has a "
                   "denominator. NOT ASSESSED. Neither forecast is used as a denominator in "
                   "its place.")
        _comps.append(_OB.component("spread between the two forecasts", absent_reason=_absent))
        _comps.append(_OB.component("higher forecast above budget at completion",
                                    absent_reason=_absent))
    _agg = _OB.aggregate(_comps)
    _posture = _agg["band_posture_before_override"]
    # THE HARD OVERRIDE: the higher forecast exceeds BAC and remaining approved contingency
    # cannot cover the gap. Both facts must be present; the contingency figure is the project's
    # own reported remaining contingency and is not inferred from the original one.
    _cont = num(si.get("remainingContingency"), None)
    _gap = (_higher - float(_bac)) if _bac is not None and _bac > 0 else None
    _override = (_gap is not None and _gap > 0 and _cont is not None and _cont < _gap)
    if _override:
        _posture = _OB.at_least_as_adverse_as(_posture, "Red")
    _override_words = (
        "HARD OVERRIDE: Red if the higher forecast exceeds the budget at completion and the "
        "remaining approved contingency cannot cover the gap. ")
    if _gap is None:
        _override_words += ("No budget at completion was reported, so the override was NOT "
                            "EVALUABLE.")
    elif _gap <= 0:
        _override_words += "The higher forecast does not exceed the budget, so it did not fire."
    elif _cont is None:
        _override_words += ("The higher forecast exceeds the budget but no remaining approved "
                            "contingency was reported, so the override was NOT EVALUABLE and "
                            "an unreported contingency was not treated as sufficient.")
    elif _override:
        _override_words += "It fired: the remaining contingency is smaller than the gap."
    else:
        _override_words += "The remaining contingency covers the gap, so it did not fire."
    _fields = dict(
        ier=_round3(reading["ier"]),
        divergence=_round3(reading["divergence"]),
        management_eac=reading["management_eac"],
        independent_eac=reading["independent_eac"],
        management_lineage=reading["management_lineage"],
        independent_lineage=reading["independent_lineage"],
        bac=_bac,
        higher_eac=_higher,
        eac_gap_above_bac=_gap,
        remaining_contingency=_cont,
        band_hard_override_fired=_override,
        band_hard_override_evaluable=(_gap is not None and (_gap <= 0 or _cont is not None)),
        canonical_structure="independent_eac_pair",
        **_agg)
    _msg = (
        f"The independent forecast of {_money(reading['independent_eac'])} stands at "
        f"{_js_str(_round3(reading['ier']))} times the management forecast of "
        f"{_money(reading['management_eac'])}, a divergence of "
        f"{_js_str(round1(reading['divergence'] * 100))} per cent")
    if _posture is None:
        return band_abstained(
            "Independent_EAC_Reconciliation", _msg,
            reason=("Not Assessed. " + _comps[0]["not_assessed_reason"]),
            band_basis_id=_RUN107_BASIS_ID, **_fields)
    return banded(
        "Independent_EAC_Reconciliation", _msg,
        status_color=_posture,
        boundary=(" ".join(c["boundary"] for c in _comps if c["boundary"])
                  + " " + _agg["band_aggregation_words"] + " " + _override_words),
        basis=_run107_basis("section 1, A1.11",
                            "3, 5 and 10 per cent on either an estimate spread or a forecast "
                            "overrun above budget"),
        provenance=PROVENANCE_OWNER_CALIBRATED,
        threshold_source=THRESHOLD_SOURCE_OWNER,
        band_basis_id=_RUN107_BASIS_ID,
        **_fields)




A1_EXTENSIONS: dict[str, tuple[str, Callable]] = {
    "A1.5": ("ARIMA_Forecast", run_arima_forecast),
    "A1.6": ("Earned_Schedule", run_earned_schedule),
    "A1.7": ("TCPI", run_tcpi),
    "A1.8": ("VAC", run_vac),
    "A1.9": ("Budget_Execution_Rate", run_budget_execution),
    # RUN 28. The two approved Category 1 to 3 renames, and no others.
    "A1.11": ("Independent_EAC_Reconciliation", run_independent_eac_reconciliation),
}
