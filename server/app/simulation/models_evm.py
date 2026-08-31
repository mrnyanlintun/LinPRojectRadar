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

from typing import Any, Callable

from .canonical import StructureAbsent
from .canonical_v3 import (
    bayesian_eac_model, budget_execution, cpi_reference_class, cpi_shrinkage,
    earned_schedule, expenditure_baseline_to_date, identify_arima,
    independent_eac_reconciliation, kalman_state_space_model, require_v3_structure,
    time_phased_baseline,
)
from .models import (
    ABSTAIN_INSUFFICIENT_HISTORY, ABSTAIN_MALFORMED_INPUT, ABSTAIN_MISSING_INPUT,
    ABSTAIN_STRUCTURE_ABSENT, calibration_pending, check_inputs, insufficient,
)
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
    order = f"({model['p']},{model['d']},{model['q']})"
    interval = ""
    if model.get("interval_low") is not None:
        interval = (f", with a 95 per cent prediction interval from "
                    f"{_js_str(_round3(model['interval_low']))} to "
                    f"{_js_str(_round3(model['interval_high']))}")
    return calibration_pending(
        "ARIMA_Forecast",
        f"Cost performance forecast {_js_str(_round3(model['forecast']))} one period ahead "
        f"from an identified {order} model over {model['history']} readings{interval}",
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
    return calibration_pending(
        "Earned_Schedule",
        f"Earned schedule {_js_str(_round3(reading['earned_schedule']))} periods against "
        f"{_js_str(_round3(reading['actual_time']))} elapsed, a time based schedule index of "
        f"{_js_str(_round3(reading['spi_time']))} and a schedule variance of "
        f"{_js_str(_round3(reading['schedule_variance_time']))} periods",
        earned_schedule=_round3(reading["earned_schedule"]),
        spi_time=_round3(reading["spi_time"]),
        schedule_variance_time=_round3(reading["schedule_variance_time"]),
        actual_time=reading["actual_time"],
        curve_periods=reading["periods"],
        baseline_version=baseline["baseline_version"],
        approval_source=baseline["approval_source"],
        canonical_structure="time_phased_baseline",
    )


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
             else "Amber" if tcpi <= _TCPI_BEYOND_OBSERVED else "Red")
    word = ("within the efficiency already planned" if tcpi <= _TCPI_PLANNED_EFFICIENCY
            else "above the efficiency planned" if tcpi <= _TCPI_BEYOND_OBSERVED
            else "beyond the improvement a cumulative cost index is observed to make")
    tcpi_display = _round3(tcpi)
    return {
        "method_class": "TCPI",
        "status_color": color,
        "tcpi": tcpi,
        "tcpi_display": tcpi_display,
        "evidence_metric": (
            f"TCPI: {_js_str(tcpi_display)}, the cost efficiency the remaining work must achieve "
            f"to finish within budget, {word}"
        ),
    }


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
_VAC_BUDGET_MET_PCT = 0.0
_VAC_BEYOND_OBSERVED_PCT = (1 - 1 / _VAC_STABILITY_CPI) * 100


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
    eac = si["bac"] / si["cpi"]
    vac = si["bac"] - eac
    vac_pct = (vac / si["bac"]) * 100 if si["bac"] != 0 else float("nan")
    if vac_pct != vac_pct:
        return insufficient("VAC")  # bac=0: JS NaN fallthrough, refused likewise
    color = ("Green" if vac_pct >= _VAC_BUDGET_MET_PCT
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
    return {
        "method_class": "VAC",
        "status_color": color,
        "vac": vac,
        "vac_pct": vac_pct,
        "vac_display": int(js_round(vac)),
        "vac_pct_display": round1(vac_pct),
        "evidence_metric": (
            f"VAC: {_money(abs(vac))} {'over' if vac < 0 else 'under'} budget "
            f"({_js_str(round1(abs(vac_pct)))}%)"
        ),
    }


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
    return calibration_pending(
        "Budget_Execution_Rate",
        f"Spending is {_money(reading['actual_cost'])} against the "
        f"{_money(reading['expected_spend'])} the approved expenditure baseline plans by this "
        f"point, an execution ratio of {_js_str(_round3(reading['execution_ratio']))}",
        execution_ratio=_round3(reading["execution_ratio"]),
        execution_deviation=_round3(reading["execution_deviation"]),
        expected_spend=reading["expected_spend"],
        actual_cost=reading["actual_cost"],
        baseline_version=profile["baseline_version"],
        approval_source=profile["approval_source"],
        canonical_structure="expenditure_baseline",
    )


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
    try:
        structure = require_v3_structure(si, "A1.11")
        reading = independent_eac_reconciliation(structure.get("management_eac"),
                                                 structure.get("independent_eac"))
    except StructureAbsent as absent:
        return insufficient("Independent_EAC_Reconciliation", absent.sentence,
                            ABSTAIN_STRUCTURE_ABSENT)
    return calibration_pending(
        "Independent_EAC_Reconciliation",
        f"The independent forecast of {_money(reading['independent_eac'])} stands at "
        f"{_js_str(_round3(reading['ier']))} times the management forecast of "
        f"{_money(reading['management_eac'])}, a divergence of "
        f"{_js_str(round1(reading['divergence'] * 100))} per cent",
        ier=_round3(reading["ier"]),
        divergence=_round3(reading["divergence"]),
        management_eac=reading["management_eac"],
        independent_eac=reading["independent_eac"],
        management_lineage=reading["management_lineage"],
        independent_lineage=reading["independent_lineage"],
        canonical_structure="independent_eac_pair",
    )


A1_EXTENSIONS: dict[str, tuple[str, Callable]] = {
    "A1.5": ("ARIMA_Forecast", run_arima_forecast),
    "A1.6": ("Earned_Schedule", run_earned_schedule),
    "A1.7": ("TCPI", run_tcpi),
    "A1.8": ("VAC", run_vac),
    "A1.9": ("Budget_Execution_Rate", run_budget_execution),
    # RUN 28. The two approved Category 1 to 3 renames, and no others.
    "A1.11": ("Independent_EAC_Reconciliation", run_independent_eac_reconciliation),
}
