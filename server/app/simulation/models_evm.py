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

from .models import ABSTAIN_MALFORMED_INPUT, check_inputs, insufficient
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
    if not check_inputs(si, ("bac", "ev", "ac", "cpi")):
        return insufficient("Bayesian_EAC")
    cpi = si["cpi"]
    if cpi == 1 or cpi == 0:
        # JS: cpi=1 → zero likelihood variance → NaN posterior → a conjured Red;
        # cpi=0 → Infinity arithmetic. Both refused here; see VALIDATION.md.
        return insufficient("Bayesian_EAC")
    bac = si["bac"]
    prior_mean = bac
    prior_var = (bac * 0.15) ** 2
    if prior_var == 0:
        return insufficient("Bayesian_EAC")  # bac=0: JS NaN fallthrough, refused likewise
    likelihood_mean = bac / cpi
    likelihood_var = (bac * (1 - cpi) / cpi) ** 2
    posterior = ((prior_mean / prior_var + likelihood_mean / likelihood_var)
                 / (1 / prior_var + 1 / likelihood_var))
    delta_pct = ((posterior - bac) / bac) * 100
    color = ("Green" if delta_pct <= 5 else "Yellow" if delta_pct <= 10
             else "Amber" if delta_pct <= 20 else "Red")
    return {
        "method_class": "Bayesian_EAC",
        "status_color": color,
        "posterior_eac": int(js_round(posterior)),
        "delta_pct": round1(delta_pct),
        "evidence_metric": (
            f"Bayesian EAC: {_money(posterior)} "
            f"({'+' if delta_pct > 0 else ''}{_js_str(round1(delta_pct))}% BAC)"
        ),
    }


# ------------------------------------------------------------ A1.4 Kalman Filter SPI Smoother


def run_kalman_filter(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    history = _history(si, "spiHistory", "spi")
    if not history or len(history) < 2:
        return insufficient("Kalman_Filter", "Awaiting history (2 periods needed)")
    q, r = 0.01, 0.1
    x, p = history[0], 1.0
    for i in range(1, len(history)):
        p = p + q
        k = p / (p + r)
        x = x + k * (history[i] - x)
        p = (1 - k) * p
    smoothed = _round3(x)
    trend = (history[-1] - history[-3]) / 2 if len(history) >= 3 else 0
    color = ("Green" if smoothed >= 0.95 else "Yellow" if smoothed >= 0.92
             else "Amber" if smoothed >= 0.88 else "Red")
    return {
        "method_class": "Kalman_Filter",
        "status_color": color,
        "smoothed_spi": smoothed,
        "trend": _round3(trend),
        "evidence_metric": (
            f"Kalman SPI: {_js_str(smoothed)} "
            f"(trend: {'+' if trend >= 0 else ''}{_js_str(_round3(trend))}/period)"
        ),
    }


# ------------------------------------------------------------ A1.5 ARIMA CPI Forecast


def run_arima_forecast(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    history = _history(si, "cpiHistory", "cpi")
    if not history or len(history) < 3:
        return insufficient("ARIMA_Forecast", "Awaiting history (3 periods needed)")
    # RUN 10, BUCKET 2. The history domain was unguarded: a series carrying a zero or a negative
    # entry was differenced and forecast as though those were performance readings. A cost
    # performance index is earned value over actual cost and cannot be zero or below, so such a
    # series is a malformed reading rather than a poor project, and it abstains.
    if any(not (v > 0) for v in history):
        return insufficient(
            "ARIMA_Forecast",
            "The cost performance history contains a reading of zero or below, which no cost "
            "performance index can be, so the series is not forecastable",
            ABSTAIN_MALFORMED_INPUT)
    diffs = [history[i] - history[i - 1] for i in range(1, len(history))]
    phi = 0.0
    if len(diffs) >= 2:
        acc_num = sum(diffs[j] * diffs[j - 1] for j in range(1, len(diffs)))
        acc_den = sum(diffs[j - 1] * diffs[j - 1] for j in range(1, len(diffs)))
        phi = clamp(acc_num / acc_den, -0.9, 0.9) if acc_den != 0 else 0.0
    last_diff = diffs[-1] or 0
    forecast_diff = phi * last_diff
    forecast = _round3(history[-1] + forecast_diff)
    color = ("Green" if forecast >= 0.95 else "Yellow" if forecast >= 0.92
             else "Amber" if forecast >= 0.88 else "Red")
    return {
        "method_class": "ARIMA_Forecast",
        "status_color": color,
        "forecast_cpi": forecast,
        "phi": js_round(phi * 100) / 100,
        "evidence_metric": (
            f"ARIMA CPI forecast: {_js_str(forecast)} "
            f"({'recovering' if forecast_diff >= 0 else 'declining'})"
        ),
    }


# ------------------------------------------------------------ A1.6 Earned Schedule


def run_earned_schedule(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    # RUN 10, BUCKET 2. Two faults. First, earned value, planned value and budget were required
    # and never read, so the module abstained on the absence of three figures its arithmetic does
    # not use. They are dropped from the requirement, which is what the arithmetic actually needs.
    # Second, the completion domain was unguarded: a percentage below zero or above one hundred
    # was divided straight into a schedule index, so a reported completion outside the domain a
    # percentage occupies produced a schedule index and a delay figure from a reading that is not
    # a percentage.
    if not check_inputs(si, ("actualPctComplete", "plannedPctComplete")):
        return insufficient("Earned_Schedule")
    for key in ("actualPctComplete", "plannedPctComplete"):
        v = num(si.get(key), None)
        if v is None or v < 0 or v > 100:
            return insufficient(
                "Earned_Schedule",
                "A reported completion percentage falls outside the range a percentage can "
                "occupy, so no schedule index is measurable from it",
                ABSTAIN_MALFORMED_INPUT)
    actual_pct = si["actualPctComplete"] / 100
    planned_pct = si["plannedPctComplete"] / 100
    spi_t = actual_pct / planned_pct if planned_pct > 0 else None
    if not spi_t:  # JS !SPI_t: 0% actual progress abstains rather than reporting SPI(t)=0
        return insufficient("Earned_Schedule")
    baseline_days = None
    if si.get("baselineStart") and si.get("baselineEnd"):
        start_ms = _js_date_ms(si["baselineStart"])
        end_ms = _js_date_ms(si["baselineEnd"])
        if start_ms is not None and end_ms is not None:
            baseline_days = (end_ms - start_ms) / 86400000
    delay_days = int(js_round(baseline_days * (1 - spi_t))) if baseline_days else None
    color = ("Green" if spi_t >= 0.95 else "Yellow" if spi_t >= 0.92
             else "Amber" if spi_t >= 0.88 else "Red")
    return {
        "method_class": "Earned_Schedule",
        "status_color": color,
        "spi_time": _round3(spi_t),
        "delay_days": delay_days,
        "evidence_metric": (
            f"ES SPI(t): {_js_str(_round3(spi_t))}"
            + (f" ({delay_days} day delay implied)" if delay_days else "")
        ),
    }


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
    tcpi = _round3(remaining_work / remaining_budget)
    color = ("Green" if tcpi <= _TCPI_PLANNED_EFFICIENCY
             else "Amber" if tcpi <= _TCPI_BEYOND_OBSERVED else "Red")
    word = ("within the efficiency already planned" if tcpi <= _TCPI_PLANNED_EFFICIENCY
            else "above the efficiency planned" if tcpi <= _TCPI_BEYOND_OBSERVED
            else "beyond the improvement a cumulative cost index is observed to make")
    return {
        "method_class": "TCPI",
        "status_color": color,
        "tcpi": tcpi,
        "evidence_metric": (
            f"TCPI: {_js_str(tcpi)}, the cost efficiency the remaining work must achieve to "
            f"finish within budget, {word}"
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
    return {
        "method_class": "VAC",
        "status_color": color,
        "vac": int(js_round(vac)),
        "vac_pct": round1(vac_pct),
        "evidence_metric": (
            f"VAC: {_money(abs(vac))} {'over' if vac < 0 else 'under'} budget "
            f"({_js_str(round1(abs(vac_pct)))}%)"
        ),
    }


# ------------------------------------------------------------ A1.9 Budget Execution Rate


def run_budget_execution(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("ac", "bac", "actualPctComplete")):
        return insufficient("Budget_Execution_Rate")
    expected = si["bac"] * (si["actualPctComplete"] / 100)
    if not expected > 0:
        return insufficient("Budget_Execution_Rate")
    rate = si["ac"] / expected
    if not rate:  # JS !executionRate: ac=0 abstains rather than reporting a 0 rate
        return insufficient("Budget_Execution_Rate")
    rate = _round3(rate)
    color = ("Green" if rate <= 1.05 else "Yellow" if rate <= 1.10
             else "Amber" if rate <= 1.20 else "Red")
    return {
        "method_class": "Budget_Execution_Rate",
        "status_color": color,
        "execution_rate": rate,
        "evidence_metric": (
            f"Budget execution rate: {_js_str(rate)} (spending "
            + (f"{int(js_round((rate - 1) * 100))}% faster" if rate > 1 else "on plan") + ")"
        ),
    }


# ------------------------------------------------------------ A1.10 Regression to Mean CPI


def run_regression_to_mean(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    history = _history(si, "cpiHistory", "cpi")
    if not history or len(history) < 2:
        return insufficient("Regression_To_Mean", "Awaiting history (2 periods needed)")
    mean = sum(history) / len(history)
    current = history[-1]
    regressed = _round3(mean + (current - mean) * 0.5)
    color = ("Green" if regressed >= 0.95 else "Yellow" if regressed >= 0.92
             else "Amber" if regressed >= 0.88 else "Red")
    return {
        "method_class": "Regression_To_Mean",
        "status_color": color,
        "regressed_cpi": regressed,
        "historical_mean": _round3(mean),
        "evidence_metric": (
            f"Regressed CPI: {_js_str(regressed)} (mean: {_js_str(_round3(mean))})"
        ),
    }


# ------------------------------------------------------------ A1.11 ICE Ratio


def run_ice_ratio(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("bac", "cpi", "ev", "ac")):
        return insufficient("ICE_Ratio")
    # RUN 10, BUCKET 2. A zero index was refused and a NEGATIVE one was not, so a negative index
    # produced a negative completion forecast that the finding then printed as a currency figure.
    # A cost performance index is earned value over actual cost and cannot be at or below zero.
    if not si["cpi"] > 0:
        return insufficient(
            "ICE_Ratio",
            "Cost performance is recorded as zero or below, which no completion forecast can "
            "be scaled by",
            ABSTAIN_MALFORMED_INPUT)
    eac_cpi = si["bac"] / si["cpi"]
    eac_parametric = si["ac"] + (si["bac"] - si["ev"])
    ice = eac_cpi / eac_parametric if eac_parametric > 0 else None
    if not ice:  # JS !iceRatio
        return insufficient("ICE_Ratio")
    ice = _round3(ice)
    a = abs(ice - 1)
    color = ("Green" if a <= 0.05 else "Yellow" if a <= 0.10
             else "Amber" if a <= 0.20 else "Red")
    return {
        "method_class": "ICE_Ratio",
        "status_color": color,
        "ice_ratio": ice,
        "eac_cpi": int(js_round(eac_cpi)),
        "eac_parametric": int(js_round(eac_parametric)),
        "evidence_metric": (
            f"ICE ratio: {_js_str(ice)} (CPI-EAC {_money(eac_cpi)} "
            f"vs parametric {_money(eac_parametric)})"
        ),
    }


A1_EXTENSIONS: dict[str, tuple[str, Callable]] = {
    "A1.3": ("Bayesian_EAC", run_bayesian_eac),
    "A1.4": ("Kalman_Filter", run_kalman_filter),
    "A1.5": ("ARIMA_Forecast", run_arima_forecast),
    "A1.6": ("Earned_Schedule", run_earned_schedule),
    "A1.7": ("TCPI", run_tcpi),
    "A1.8": ("VAC", run_vac),
    "A1.9": ("Budget_Execution_Rate", run_budget_execution),
    "A1.10": ("Regression_To_Mean", run_regression_to_mean),
    "A1.11": ("ICE_Ratio", run_ice_ratio),
}
