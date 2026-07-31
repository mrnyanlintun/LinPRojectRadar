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

from .models import check_inputs, insufficient
from .models_ext import _js_date_ms, _js_str, _money
from .rng import clamp, js_round, round1

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
    if not check_inputs(si, ("ev", "pv", "bac", "actualPctComplete", "plannedPctComplete")):
        return insufficient("Earned_Schedule")
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


def run_tcpi(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("bac", "ev", "ac")):
        return insufficient("TCPI")
    remaining_work = si["bac"] - si["ev"]
    remaining_budget = si["bac"] - si["ac"]
    if remaining_budget <= 0:
        return {
            "method_class": "TCPI",
            "status_color": "Red",
            "tcpi": None,
            "evidence_metric": "Budget exhausted: no remaining funds",
        }
    tcpi = _round3(remaining_work / remaining_budget)
    color = ("Green" if tcpi <= 1.05 else "Yellow" if tcpi <= 1.10
             else "Amber" if tcpi <= 1.20 else "Red")
    word = ("achievable" if tcpi <= 1.05 else "challenging" if tcpi <= 1.10
            else "very difficult" if tcpi <= 1.20 else "unrealistic")
    return {
        "method_class": "TCPI",
        "status_color": color,
        "tcpi": tcpi,
        "evidence_metric": f"TCPI: {_js_str(tcpi)}, {word} to finish within budget",
    }


# ------------------------------------------------------------ A1.8 Variance at Completion


def run_vac(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("bac", "cpi")):
        return insufficient("VAC")
    if si["cpi"] == 0:
        return insufficient("VAC")  # JS Infinity arithmetic; refused, see VALIDATION.md
    eac = si["bac"] / si["cpi"]
    vac = si["bac"] - eac
    vac_pct = (vac / si["bac"]) * 100 if si["bac"] != 0 else float("nan")
    if vac_pct != vac_pct:
        return insufficient("VAC")  # bac=0: JS NaN fallthrough, refused likewise
    color = ("Green" if vac_pct >= -5 else "Yellow" if vac_pct >= -10
             else "Amber" if vac_pct >= -20 else "Red")
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
    if si["cpi"] == 0:
        return insufficient("ICE_Ratio")  # JS Infinity arithmetic; refused
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
