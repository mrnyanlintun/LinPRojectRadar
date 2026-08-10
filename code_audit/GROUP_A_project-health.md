# Group A — Project Health

52 modules. Purpose per `GROUP_ASSIGNMENT.md` / `NAMING_AUTHORITY.md`: "what condition the project
is in." Source files: `server/app/simulation/models.py`, `models_evm.py`, `models_ext.py`,
`models_doc.py`. Shared helpers (`insufficient`, `check_inputs`, `_js_date_ms`, `_derived`, numeric
helpers) are documented once in `SHARED_MACHINERY.md` and referenced by name below, not repeated.

Field availability below is judged against `server/app/field_registry.py`'s `FIELD_KINDS`
(emittable), `UNEMITTABLE_FIELDS` (`rfiNumber`, `rfiResponseTimeDays`, `docDate` — see that file's
note that `docDate` is in fact derived at selection, not genuinely dead), and `NEEDS` (declared
servable series/event-sets: `cpiHistory`, `spiHistory`, `milestoneHistory`, `changeOrderCount` as
an event set).

---

## Monte Carlo EAC

Purpose (module_name / category): Monte Carlo EAC, category "Cost & EVM Performance".

Source (`models_sim.py`, wrapped for the registry by `run_monte_carlo_module` in `models.py`):

```python
def run_monte_carlo(si: dict, rand, seed: int) -> dict[str, Any]:
    """A1.1. Abstains when bac, cpi or spi is absent, matching the registry's required list."""
    from .models import insufficient
    if any(si.get(k) is None for k in ("bac", "cpi", "spi")):
        return insufficient("Monte_Carlo")

    mc = monte_carlo_eac(
        {"cpi": si.get("cpi"), "spi": si.get("spi"), "bac": si.get("bac"),
         "docScore": si.get("docRiskScore")},
        seed=seed,
    )
    return {
        "method_class": "Monte_Carlo",
        "status_color": mc_status(mc["overrunPctP80"]),
        "p50_eac": mc["p50"],
        "p80_eac": mc["p80"],
        "overrun_pct_p50": mc["overrunPctP50"],
        "overrun_pct_p80": mc["overrunPctP80"],
        "spread_driver": mc["s"],
        "iterations": mc["iterations"],
        "evidence_metric": (
            f"P80 EAC {mc['p80']:.0f} vs BAC {mc['baseline']:.0f} "
            f"(+{mc['overrunPctP80']:.1f}%); {mc['iterations']} iterations"
        ),
    }
```

with `monte_carlo_eac`, its only caller, quoted in full because it is private to this module:

```python
def monte_carlo_eac(inputs: dict, seed: int, iterations: int = 5000) -> dict[str, Any]:
    """Monte Carlo over a Beta-PERT derived from the project's EVM and risk signals."""
    cpi = float(inputs.get("cpi") or 0) or 1.0
    spi = float(inputs.get("spi") or 0) or 1.0
    bac = float(inputs.get("bac") or 0) or DEMO_BAC
    doc_score = clamp(float(inputs.get("docScore") or 0), 0, 1)

    m_eac = bac / cpi

    cusum_penalty = (
        0.15 if inputs.get("cusumBreached")
        else 0.15 * clamp((float(inputs.get("cusumDrift") or 0))
                          / (float(inputs.get("cusumThreshold") or 0) or 1.0), 0, 1)
    )
    s = clamp(0.5 * (1 - cpi) + 0.3 * (1 - spi) + 0.2 * doc_score + cusum_penalty, 0, 1)

    o = m_eac * (1 - 0.10 * s)
    m = m_eac
    p = m_eac * (1 + 0.40 * s)

    rand = make_rng(seed)
    if p - o < 1e-9:
        samples = [m_eac] * iterations
    else:
        alpha = 1 + 4 * (m - o) / (p - o)
        beta_p = 1 + 4 * (p - m) / (p - o)
        samples = [o + _beta(alpha, beta_p, rand) * (p - o) for _ in range(iterations)]

    ordered = sorted(samples)
    p50 = pctile(ordered, 0.50)
    p80 = pctile(ordered, 0.80)
    return {
        "iterations": iterations, "p50": p50, "p80": p80, "o": o, "m": m, "p": p, "s": s,
        "mEAC": m_eac, "baseline": bac,
        "overrunPctP50": (p50 / bac - 1) * 100,
        "overrunPctP80": (p80 / bac - 1) * 100,
    }
```

plus `_normal`, `_gamma`, `_beta` (Box-Muller / Marsaglia-Tsang gamma / beta samplers, private to
this module, used only here) and `mc_status`:

```python
def mc_status(overrun_pct_p80: float) -> str:
    if overrun_pct_p80 >= 10:
        return "red"
    if overrun_pct_p80 >= 5:
        return "amber"
    return "green"
```

**Inputs.** `cpi`, `spi`, `bac` (all required, `FIELD_KINDS` SNAPSHOT — extracted/derived fields
in the merged signalInputs) and `docRiskScore` (SNAPSHOT, optional — defaults to 0 via `or 0`
inside `monte_carlo_eac`). Also reads `cusumBreached`, `cusumDrift`, `cusumThreshold` from the
`inputs` dict it is called with — but the caller (`run_monte_carlo`) never passes these three keys
into the `inputs` dict it builds (only `cpi`, `spi`, `bac`, `docScore` are passed), so
`cusum_penalty` always takes the `else` branch with all three `.get()` calls returning `None` →
`0/1.0` → `0`. **This is dead-parameter code as written today**: the CUSUM-derived penalty
described in the docstring can never be non-zero via this call path.

**Availability.** `cpi`, `spi`, `bac`, `docRiskScore` are all emittable (`FIELD_KINDS`); nothing
here is dead-on-arrival at the field level, but the CUSUM-penalty pathway is unreachable as shown
above regardless of field availability.

**Literals, exhaustively, with provenance as the code states it (or doesn't):**
- `iterations=5000` (default parameter) — no comment.
- `DEMO_BAC = 100.0` (fallback when `bac` is 0/falsy) — named "DEMO", no other provenance comment.
- `cusum_penalty = 0.15` (breached case) and `0.15 * clamp(...)` (else case) — no comment on why
  0.15.
- Spread weights `0.5 * (1 - cpi) + 0.3 * (1 - spi) + 0.2 * doc_score` — no comment on why
  0.5/0.3/0.2.
- Beta-PERT envelope: `o = m_eac * (1 - 0.10 * s)`, `p = m_eac * (1 + 0.40 * s)` — no comment on
  why 0.10 / 0.40 (asymmetric optimistic/pessimistic spread).
- Beta shape parameters `alpha = 1 + 4 * (m - o) / (p - o)`, `beta_p = 1 + 4 * (p - m) / (p - o)`
  — this is the standard PERT-Beta formula (comment says "Beta-PERT derived", so the "4" here is
  documented as the PERT-Beta convention, not an arbitrary literal).
- `1e-9` (near-zero guard on `p - o`) — no comment.
- `mc_status` thresholds `>= 10` red, `>= 5` amber — no comment on why 10%/5%.

**Output / banding.** Returns `p50_eac`, `p80_eac` (5000-sample Beta-PERT percentiles via the
shared index-based `pctile`), `overrun_pct_p50/p80`, `spread_driver` (`s`), `iterations`. Status:
Red if P80 overrun ≥10%, Amber if ≥5%, else Green. `evidence_metric` states the P80 EAC vs BAC and
overrun percentage. **This module stores its own `p80_eac` key** — the handoff (2026-08-10, "risk
register read as data" section) notes the detail-page card no longer prints an eightieth
percentile from *either* Cost Risk Analysis or Monte Carlo, because Monte Carlo's `p80_eac` "would
have re-sourced the sentence if only [Cost Risk Analysis] were silenced" — i.e. this module's P80
figure carries the same invented-parameter concern (arbitrary 0.10/0.40/0.5/0.3/0.2 literals feed
into a P80 that reads as measured) and was deliberately kept off that card even though this module
itself is unchanged.

**Abstains** when any of `bac`, `cpi`, `spi` is `None` (`si.get(k) is None`).

---

## CUSUM Anomaly Monitor

Purpose: CUSUM Anomaly Monitor, category "Cost & EVM Performance".

Source (`models_sim.py`, wrapped by `run_cusum_module`):

```python
def run_cusum(si: dict, rand, seed: int) -> dict[str, Any]:
    """
    A1.2. Runs on the project's real SPI history and abstains without one.
    ...
    """
    from .models import insufficient
    if si.get("spi") is None:
        return insufficient("CUSUM")

    series = si.get("spiHistory")
    if not isinstance(series, list) or len(series) < 2:
        return insufficient("CUSUM", "Awaiting history (2 periods needed)")
    cu = cusum_series(series)
    return {
        "method_class": "CUSUM",
        "status_color": cusum_status(cu),
        "sigma": cu["sigma"],
        "k": cu["k"],
        "H": cu["H"],
        "max_stat": cu["maxStat"],
        "breached": cu["breached"],
        "breach_index": cu["breachIndex"],
        "periods": len(cu["x"]),
        "evidence_metric": (
            f"CUSUM max {cu['maxStat']:.3f} against H {cu['H']:.3f} over {len(cu['x'])} periods"
            + ("; breached" if cu["breached"] else "; no breach")
        ),
    }
```

`cusum_series` and `cusum_status`, private to this module:

```python
def cusum_series(series, target: float = 1.0, sigma=None, h_units: float = 5) -> dict[str, Any]:
    """Standard two-sided tabular CUSUM. Deterministic given the series."""
    x = []
    for v in (series or []):
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if math.isfinite(f):
            x.append(f)

    if sigma is None:
        if len(x) > 1:
            mean = sum(x) / len(x)
            varr = sum((b - mean) ** 2 for b in x) / (len(x) - 1)
            sigma = math.sqrt(varr)
        else:
            sigma = 0.0
    if not (sigma > 0):
        sigma = 0.05  # documented floor so k and H stay meaningful on a short or flat series

    k = 0.5 * sigma
    h = h_units * sigma

    s_hi, s_lo, stat = [], [], []
    hi = lo = 0.0
    breached = False
    breach_index = -1
    for t in range(len(x)):
        hi = max(0.0, hi + (x[t] - target) - k)
        lo = max(0.0, lo + (target - x[t]) - k)
        s_hi.append(hi)
        s_lo.append(lo)
        stat.append(max(hi, lo))
        if not breached and (hi > h or lo > h):
            breached = True
            breach_index = t

    return {"x": x, "target": target, "sigma": sigma, "k": k, "H": h, "hUnits": h_units,
            "sHi": s_hi, "sLo": s_lo, "stat": stat,
            "maxStat": max(stat) if stat else 0.0,
            "breached": breached, "breachIndex": breach_index}


def cusum_status(cu: dict) -> str:
    if cu["breached"]:
        return "red"
    if cu["maxStat"] >= 0.6 * cu["H"]:
        return "amber"
    return "green"
```

**Inputs.** `spi` (SNAPSHOT, required as a presence gate) and `spiHistory` (declared in
`field_registry.NEEDS`: `SERIES`, `min_points: 2`, `servable: True` — "Served by `_period_history`
from earlier periods' stored live results — strictly earlier periods, minimum two points").

**Availability.** `spi` is emittable. `spiHistory` is declared servable since the D1 work referenced
in this file's docstring ("D1. This module used to synthesise a twelve-point series... `spiHistory`
is now assembled from the project's earlier periods"), i.e. it needs at least two prior periods of
computed `spi` to exist — a brand-new project with fewer than two prior periods cannot supply it and
this module abstains, which is documented, expected behaviour rather than a dead field.

**Literals:**
- `target: float = 1.0` (default param) — the CUSUM reference/target value; no comment beyond
  "Standard two-sided tabular CUSUM."
- `h_units: float = 5` (default param, multiplies `sigma` for the decision interval H) — no
  comment on why 5.
- `k = 0.5 * sigma` — the reference-shift constant; 0.5 is the textbook CUSUM `k` convention
  (half a sigma), not commented as such here but is standard tabular-CUSUM practice.
- `sigma` floor `0.05` when computed sigma is 0 or unavailable — commented: "documented floor so k
  and H stay meaningful on a short or flat series."
- `cusum_status` amber threshold `0.6 * cu["H"]` — no comment on why 0.6.

**Output / banding.** Returns `sigma`, `k`, `H`, `max_stat`, `breached`, `breach_index`, `periods`.
Status: Red if breached, Amber if `max_stat >= 0.6*H`, else Green.

**Abstains** when `spi` is `None`, or when `spiHistory` is missing/not a list/has fewer than 2
points (message: "Awaiting history (2 periods needed)").

---

## Bayesian EAC

Purpose: Bayesian EAC, category "Cost & EVM Performance".

Source (`models_evm.py`):

```python
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
```

**Inputs.** `bac`, `ev`, `ac`, `cpi` (all SNAPSHOT, required via `check_inputs`).

**Availability.** All four are emittable per `FIELD_KINDS`.

**Literals:**
- `prior_var = (bac * 0.15) ** 2` — the 0.15 (15% of BAC as prior standard deviation) has no
  comment or provenance.
- Banding thresholds `<=5` Green, `<=10` Yellow, `<=20` Amber, else Red (percent delta from BAC) —
  no comment on why these cut points.

**Output / banding.** `posterior_eac` (Bayesian-updated EAC combining a BAC-centered prior with a
CPI-implied likelihood), `delta_pct` vs BAC. Four-way banding as above (this module uses a
four-color "Yellow" tier, not the three-color Green/Amber/Red most A-group modules use).

**Abstains** when `bac`/`ev`/`ac`/`cpi` missing, or `cpi == 1` or `cpi == 0` (documented as
refusing the JS NaN/Infinity fallthrough at those exact points), or `prior_var == 0` (i.e.
`bac == 0`).

---

## Kalman Filter SPI Smoother

Purpose: Kalman Filter SPI Smoother, category "Cost & EVM Performance".

Source (`models_evm.py`), with its private history helper `_history`:

```python
def _history(si: dict, key: str, scalar_key: str):
    """`si[key] || (si[scalar] ? [si[scalar]] : null)`, truthiness intact."""
    h = si.get(key)
    if h is not None and h is not False:
        if isinstance(h, list):
            return h
    s = si.get(scalar_key)
    if s:
        return [s]
    return None


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
```

**Inputs.** `spiHistory` (series, `NEEDS`-servable) with a fallback to `[spi]` if `spiHistory` is
absent but `spi` is truthy (`_history` reproduces JS truthiness: an *empty* `spiHistory` list is
truthy in JS and is used as-is, then fails the `len < 2` guard below rather than falling back to
the scalar).

**Availability.** `spi` is emittable; `spiHistory` needs ≥2 prior periods (same caveat as A1.2).

**Literals:**
- Process/measurement noise `q, r = 0.01, 0.1` — no comment on the choice of these Kalman filter
  tuning constants beyond the code being "a Kalman Filter SPI Smoother."
- Initial covariance `p = 1.0` — no comment.
- Trend uses `(history[-1] - history[-3]) / 2` (a 2-period-back backward difference divided by 2)
  only when `len(history) >= 3` — no comment on why 2 as the divisor.
- Banding `>=0.95` Green, `>=0.92` Yellow, `>=0.88` Amber, else Red — no comment.

**Output / banding.** `smoothed_spi` (Kalman-filtered SPI to 3 decimals), `trend`. Four-way
banding as listed.

**Abstains** when history is absent or has fewer than 2 points.

---

## ARIMA CPI Forecast

Purpose: ARIMA CPI Forecast, category "Cost & EVM Performance".

Source (`models_evm.py`):

```python
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
```

**Inputs.** `cpiHistory` (series, `NEEDS`-servable, ≥2 prior periods needed to reach 3 total with
the current) with fallback to `[cpi]`.

**Availability.** `cpi` emittable; `cpiHistory` needs ≥3 total points across periods.

**Literals:**
- `phi` clamp bounds `-0.9, 0.9` (AR(1) coefficient stability bound) — this is the standard
  AR(1) stationarity requirement (|phi| < 1), clamped conservatively to 0.9; no comment states
  this reasoning in code.
- Banding `>=0.95/0.92/0.88` — same four-tier scheme as Kalman, no comment.

**Output / banding.** `forecast_cpi` (one-step-ahead AR(1)-style forecast from the differenced
series), `phi` (fitted autocorrelation coefficient, 2-decimal rounded). Same four-tier banding.

**Abstains** when fewer than 3 history points.

---

## Earned Schedule

Purpose: Earned Schedule, category "Cost & EVM Performance".

Source (`models_evm.py`):

```python
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
```

**Inputs.** `ev`, `pv`, `bac`, `actualPctComplete`, `plannedPctComplete` (all required SNAPSHOT),
optionally `baselineStart`/`baselineEnd` (both PERMANENT/SNAPSHOT) for the day-count conversion.
Note `ev`, `pv`, `bac` are checked as required but not otherwise used in the arithmetic shown
(SPI(t) here is computed purely from the two percent-complete fields) — they gate entry but do
not appear in the formula body.

**Availability.** All emittable.

**Literals:**
- Banding `>=0.95/0.92/0.88` — same four-tier scheme, no comment.
- `86400000` (ms per day) is an exact unit conversion constant, not a tunable literal.

**Output / banding.** `spi_time` (SPI(t), actual% ÷ planned%), `delay_days` (baseline duration ×
(1 − SPI(t)), if baseline dates present).

**Abstains** when required fields missing, `plannedPctComplete <= 0`, or SPI(t) computes to a
falsy value (i.e. exactly 0 — "0% actual progress abstains rather than reporting SPI(t)=0",
documented).

---

## TCPI

Purpose: TCPI, category "Cost & EVM Performance".

Source (`models_evm.py`):

```python
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
```

**Inputs.** `bac`, `ev`, `ac` (SNAPSHOT, required).

**Availability.** All emittable.

**Literals:** banding `<=1.05/1.10/1.20` — standard TCPI interpretation bands, no comment on the
specific cut points chosen.

**Output / banding.** `tcpi` (remaining work ÷ remaining budget, the textbook TCPI formula, no
literal beyond the ratio itself); qualitative word ladder plus color.

**Abstains?** Not in the `insufficient()` sense — when `remaining_budget <= 0` it returns a
concrete Red result (`tcpi: None`) rather than an abstention; it only abstains via `insufficient()`
when `bac`/`ev`/`ac` are missing.

---

## Variance at Completion

Purpose: Variance at Completion, category "Cost & EVM Performance".

Source (`models_evm.py`):

```python
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
```

**Inputs.** `bac`, `cpi` (SNAPSHOT, required).

**Availability.** Both emittable.

**Literals:** banding `>=-5/-10/-20` percent — no comment.

**Output / banding.** `vac` (BAC − EAC, dollars), `vac_pct`.

**Abstains** when `bac`/`cpi` missing, `cpi == 0`, or `bac == 0` (NaN vac_pct).

---

## Budget Execution Rate

Purpose: Budget Execution Rate, category "Cost & EVM Performance".

Source (`models_evm.py`):

```python
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
```

**Inputs.** `ac`, `bac`, `actualPctComplete` (SNAPSHOT, required).

**Availability.** All emittable.

**Literals:** banding `<=1.05/1.10/1.20` — same shape as TCPI, no comment.

**Output / banding.** `execution_rate` (AC ÷ expected-spend-to-date).

**Abstains** when required fields missing, `expected <= 0`, or `rate` is falsy (i.e. `ac == 0`
→ abstains rather than reporting a 0 rate, documented).

---

## Regression to Mean CPI

Purpose: Regression to Mean CPI, category "Cost & EVM Performance".

Source (`models_evm.py`):

```python
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
```

**Inputs.** `cpiHistory` (fallback `[cpi]`).

**Availability.** Same as ARIMA/Kalman — needs ≥2 history points.

**Literals:** regression coefficient `0.5` ("halfway back to the mean") — no comment on why 0.5
specifically rather than any other shrinkage factor. Banding `>=0.95/0.92/0.88` — no comment.

**Output / banding.** `regressed_cpi` (mean + half the current deviation from mean),
`historical_mean`.

**Abstains** when fewer than 2 history points.

---

## ICE Ratio

Purpose: ICE Ratio, category "Cost & EVM Performance".

Source (`models_evm.py`):

```python
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
```

**Inputs.** `bac`, `cpi`, `ev`, `ac` (SNAPSHOT, required).

**Availability.** All emittable.

**Literals:** banding on `abs(ice - 1)`: `<=0.05/0.10/0.20` — no comment.

**Output / banding.** `ice_ratio` (CPI-based EAC ÷ parametric EAC — a convergence check between
two EAC conventions), `eac_cpi`, `eac_parametric`.

**Abstains** when required fields missing, `cpi == 0`, `eac_parametric <= 0`, or `ice` computes
falsy (exactly 0).

---

## PERT Network Criticality

Purpose: PERT Network Criticality, category "Schedule Performance". The one **stochastic** module
besides Monte Carlo — draws from the shared seeded generator.

Source (`models.py`), with its private sampler `_sample_triangular`:

```python
def _sample_triangular(a: float, m: float, b: float, rand: Callable[[], float]) -> float:
    """Exact inverse-CDF triangular sampler, matching the JavaScript reference."""
    f = (m - a) / (b - a)
    u = rand()
    if u < f:
        return a + math.sqrt(u * (b - a) * (m - a))
    return b - math.sqrt((1 - u) * (b - a) * (b - m))


def run_pert(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    PERT stochastic network criticality. A then (B parallel C); finish = A + max(B, C).
    """
    spi = num(si.get("spi"), 1.0)
    pess = 1 + max(0.0, 1 - spi) * 0.8
    a_act = (8.0, 10.0, 14.0)
    b_act = (12.0, 15.0, 22.0 * pess)
    c_act = (10.0, 13.0, 18.0 * pess)

    n = 2000
    totals = []
    b_critical = 0
    for _ in range(n):
        a = _sample_triangular(*a_act, rand)
        b = _sample_triangular(*b_act, rand)
        c = _sample_triangular(*c_act, rand)
        totals.append(a + max(b, c))
        if b >= c:
            b_critical += 1

    totals.sort()
    p50 = pctile(totals, 0.50)
    p80 = pctile(totals, 0.80)
    crit = b_critical / n
    baseline = a_act[1] + max(b_act[1], c_act[1])
    ratio = p80 / baseline
    color = "Red" if ratio > 1.30 else ("Amber" if ratio > 1.15 else "Green")

    return {
        "method_class": "PERT_Network_Criticality",
        "status_color": color,
        "p50_duration_days": round1(p50),
        "p80_duration_days": round1(p80),
        "baseline_days": round1(baseline),
        "path_criticality_index": round2(crit),
        "evidence_metric": (
            f"P80 path {round1(p80)}d vs baseline {round1(baseline)}d; "
            f"structural path critical {int(math.floor(crit * 100 + 0.5))}% of runs"
        ),
    }
```

**Inputs.** `spi` (optional, defaults to 1.0 via `num(..., 1.0)` if missing).

**Availability.** `spi` is emittable; module never abstains since it always has a usable default.

**Literals — an entire fixed three-activity PERT network is hardcoded, no project-specific
topology or durations are read from documents:**
- `a_act = (8.0, 10.0, 14.0)`, `b_act = (12.0, 15.0, 22.0*pess)`, `c_act = (10.0, 13.0, 18.0*pess)`
  — the optimistic/most-likely/pessimistic triangular parameters for three fixed "activities" A,
  B, C — no comment tying these to any real schedule data; they are a synthetic demonstration
  network ("A then (B parallel C)").
- `pess = 1 + max(0.0, 1 - spi) * 0.8` — the 0.8 pessimism-scaling coefficient has no comment.
  `pess` only inflates B's and C's pessimistic bound, not their optimistic/likely values.
- `n = 2000` (Monte Carlo sample count) — no comment.
- Banding `ratio > 1.30` Red, `> 1.15` Amber, else Green (P80 path ÷ baseline) — no comment.

**Output / banding.** `p50_duration_days`, `p80_duration_days`, `baseline_days` (fixed
most-likely-case duration `10 + max(15, 13) = 25` when `spi==1`), `path_criticality_index`
(fraction of runs where B ≥ C). Note: **the entire "network" — which activities exist, their
durations, and how they're connected — is invented in code and not read from any project document
or schedule extraction.** Only `spi` (via `pess`) perturbs it.

**Abstains:** never — always has a default for `spi`.

---

## Line of Balance

Purpose: Line of Balance, category "Schedule Performance".

Source (`models.py`):

```python
def run_lob(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """Line of balance: leader (grading) against follower (paving), buffer eroding per unit."""
    spi = num(si.get("spi"), 1.0)
    units = 20
    grading_rate = 2.0
    paving_rate = 1.8 * clamp(spi, 0.3, 1.2)
    initial_buffer = 5.0
    lag = max(0.0, (1 / paving_rate) - (1 / grading_rate))

    min_buffer = initial_buffer
    crit_unit = units
    flagged = False
    for u in range(1, units + 1):
        buf = initial_buffer - u * lag
        if buf < min_buffer:
            min_buffer = buf
        if not flagged and buf <= 1.5:
            crit_unit = u
            flagged = True

    color = "Red" if min_buffer <= 1.5 else ("Amber" if min_buffer <= 3.0 else "Green")
    return {
        "method_class": "Line_of_Balance_Velocity",
        "status_color": color,
        "minimum_buffer_days": round1(min_buffer),
        "critical_unit_index": crit_unit,
        "grading_rate": grading_rate,
        "paving_rate": round2(paving_rate),
        "initial_buffer_days": initial_buffer,
        "units": units,
        "evidence_metric": (
            f"Min crew buffer {round1(min_buffer)}d (paving {round2(paving_rate)} "
            f"vs grading {grading_rate} units/day)"
        ),
    }
```

**Inputs.** `spi` (optional, default 1.0).

**Availability.** Emittable; never abstains.

**Literals — an entirely synthetic two-crew linear schedule:**
- `units = 20` (fixed unit count) — no comment, not read from any document.
- `grading_rate = 2.0` (units/day, fixed) — no comment.
- `paving_rate = 1.8 * clamp(spi, 0.3, 1.2)` — the base rate `1.8` and the `spi` clamp bounds
  `0.3, 1.2` all have no comment.
- `initial_buffer = 5.0` days — no comment.
- Banding `<=1.5` Red, `<=3.0` Amber, else Green — no comment.

**Output / banding.** `minimum_buffer_days`, `critical_unit_index` (first unit where buffer
≤1.5), `grading_rate`/`paving_rate`/`initial_buffer_days`/`units` all echoed back as constants.
**As with PERT, the underlying "project" (20 units, two fixed crew rates) is entirely invented;
only `spi` perturbs the paving rate.**

**Abstains:** never.

---

## CCPM Buffer Health

Purpose: CCPM Buffer Health, category "Schedule Performance".

Source (`models.py`):

```python
def run_ccpm(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """CCPM buffer-health fever chart: buffer consumption against chain completion."""
    raw = si.get("actualPctComplete")
    if raw is None:
        raw = si.get("plannedPctComplete")
    pct_chain = as_percent(raw, 0.0)
    spi = num(si.get("spi"), 1.0)
    pct_buffer = clamp((1 - spi) * 100 * 1.5, 0, 100)
    amber = pct_chain
    red = pct_chain + (100 - pct_chain) / 3
    color = "Red" if pct_buffer >= red else ("Amber" if pct_buffer >= amber else "Green")

    return {
        "method_class": "CCPM_Buffer_Health",
        "status_color": color,
        "pct_chain_complete": round1(pct_chain),
        "pct_buffer_consumed": round1(pct_buffer),
        "zone": color,
        "amber_threshold": round1(amber),
        "red_threshold": round1(red),
        "evidence_metric": (
            f"Buffer {round1(pct_buffer)}% consumed at {round1(pct_chain)}% chain complete"
        ),
    }
```

**Inputs.** `actualPctComplete` (preferred) or `plannedPctComplete` (fallback), `spi` (default
1.0).

**Availability.** All emittable.

**Literals:**
- `pct_buffer = clamp((1 - spi) * 100 * 1.5, 0, 100)` — the `1.5` multiplier converting schedule
  slip into "buffer consumed" has no comment.
- `red = pct_chain + (100 - pct_chain) / 3` — the classic CCPM fever-chart 1/3 rule (buffer zones
  scaled by chain % complete) — not commented in code but matches the textbook CCPM
  one-third-zone convention.

**Output / banding.** `pct_chain_complete`, `pct_buffer_consumed`, moving amber/red thresholds
that scale with chain completion (standard CCPM fever chart shape).

**Abstains:** never (both inputs default).

---

## Schedule Compression Index

Purpose: Schedule Compression Index, category "Schedule Performance".

Source (`models_ext.py`):

```python
def run_schedule_compression(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("baselineEnd", "baselineStart", "actualPctComplete")):
        return insufficient("Schedule_Compression")
    end_ms = _js_date_ms(si.get("baselineEnd"))
    start_ms = _js_date_ms(si.get("baselineStart"))
    if end_ms is None or start_ms is None:
        return insufficient("Schedule_Compression")
    total_days = (end_ms - start_ms) / 86400000
    if total_days <= 0:
        return insufficient("Schedule_Compression")
    remaining_pct = (100 - si["actualPctComplete"]) / 100
    remaining_days = total_days * remaining_pct
    spi = _or_default(si.get("spi"), 1.0)
    required_days = remaining_days
    available_days = remaining_days * spi
    ratio = required_days / max(available_days, 1) if required_days > 0 else 1
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
```

**Inputs.** `baselineEnd`, `baselineStart` (PERMANENT/SNAPSHOT), `actualPctComplete` (SNAPSHOT),
`spi` (optional).

**Availability.** All emittable; date parsing can fail (`_js_date_ms` returns `None`) if the
string isn't a plain `YYYY-MM-DD`, causing abstention even with fields present.

**Literals:** banding `<=1.05/1.15/1.30` — no comment. `max(available_days, 1)` floor of 1 day
— no comment.

**Output / banding.** `compression_ratio` (required ÷ available remaining days, `available_days`
scaled by `spi`), `remaining_days`.

**Abstains** on missing dates/percent, unparseable dates, or `total_days <= 0`.

---

## Float Consumption Rate

Purpose: Float Consumption Rate, category "Schedule Performance".

Source (`models_ext.py`):

```python
def run_float_consumption(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("totalFloat", "consumedFloat")):
        return insufficient("Float_Consumption")
    float_remaining = si["totalFloat"] - si["consumedFloat"]
    if not si["totalFloat"] > 0:
        return insufficient("Float_Consumption")
    consumption_rate = si["consumedFloat"] / si["totalFloat"]
    pct_complete = _or_default(si.get("actualPctComplete"), 50)
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
```

**Inputs.** `totalFloat`, `consumedFloat` (SNAPSHOT, required), `actualPctComplete` (optional,
default 50 if missing/falsy).

**Availability.** All emittable.

**Literals:** default `actualPctComplete` fallback `50` — no comment on why 50% is the assumed
default. `max(expected, 0.01)` floor — no comment. Banding `<=1.0/1.3/1.6` — no comment.

**Output / banding.** `float_remaining_days`, `consumption_rate` (%), `float_stress` (consumption
rate ÷ expected progress).

**Abstains** on missing fields or `totalFloat <= 0`.

---

## S-Curve Deviation

Purpose: S-Curve Deviation, category "Schedule Performance".

Source (`models_ext.py`):

```python
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
```

**Inputs.** `actualPctComplete`, `plannedPctComplete`, `ev`, `pv` (all SNAPSHOT, required).

**Availability.** All emittable.

**Literals:** `combined = (pct_dev + value_dev) / 2` — equal-weight average, no comment on why
50/50. Banding `>=-2/-5/-10` — no comment.

**Output / banding.** `pct_deviation`, `value_deviation`, banded on their unweighted average.

**Abstains** on missing fields or `pv <= 0`.

---

## Milestone Trend Analysis

Purpose: Milestone Trend Analysis, category "Schedule Performance".

Source (`models_ext.py`):

```python
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
```

**Inputs.** `milestoneHistory` — declared in `field_registry.NEEDS` as `SERIES, min_points: 2,
servable: True` since the noted fix ("SERVABLE SINCE 0021... assembled by
`documents._milestone_history` from the `schedule_activities` store").

**Availability.** Now servable (per `field_registry.py` comment), needing ≥2 milestone snapshots
across periods matched by milestone *name* (not id) — a project that renames milestones between
periods will fail to match and abstain with "Milestone names not comparable across periods" even
with history present.

**Literals:** banding `<=0` Green, `<=7` Yellow, `<=14` Amber, else Red (days of mean slip) —
no comment. Override: `worst_slip > 21` forces at least Amber even if the mean is better — the 21
day threshold is uncommented, though the surrounding prose explains the *intent* ("one badly
slipping milestone must not hide inside the average").

**Output / banding.** `mean_slip_days`, `worst_slip_days`, `worst_milestone`, `matched_count`.

**Abstains** when `milestoneHistory` missing/short, or when no milestone names match between the
two most recent snapshots.

---

## Look-Ahead Schedule Health

Purpose: Look-Ahead Schedule Health, category "Schedule Performance".

Source (`models_ext.py`):

```python
def run_lookahead_health(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("activitiesPlanned", "activitiesConstrained")):
        return insufficient("Lookahead_Health")
    planned = si["activitiesPlanned"]
    constrained = si["activitiesConstrained"]
    rate = constrained / planned if planned > 0 else 0
    is_derived = _derived(si, "activitiesPlanned")
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
```

**Inputs.** `activitiesPlanned`, `activitiesConstrained` (SNAPSHOT, required, may arrive derived).

**Availability.** Both emittable; `_derived()` flags when the value came from an estimate rather
than a genuine Look-Ahead Schedule document.

**Literals:** banding `<=0.10/0.25/0.40` — no comment.

**Output / banding.** `constraint_rate` (%), raw counts, evidence text flags estimation.

**Abstains** on missing fields.

---

## Resource Loading Index

Purpose: Resource Loading Index, category "Schedule Performance".

Source (`models_ext.py`):

```python
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
```

**Inputs.** `plannedLaborHours`, `actualLaborHours` (SNAPSHOT, required).

**Availability.** Both emittable.

**Literals:** symmetric banding around 1.0: Green `[0.90, 1.10]`, Yellow `[0.80,0.90)∪(1.10,1.20]`,
Amber `[0.70,0.80)∪(1.20,1.35]`, else Red — no comment on cut points.

**Output / banding.** `load_ratio` (actual ÷ planned labor hours).

**Abstains** on missing fields or `planned <= 0`.

---

## Schedule Risk Analysis P80

Purpose: Schedule Risk Analysis P80, category "Schedule Performance".

Source (`models_ext.py`):

```python
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
```

**Inputs.** `spi`, `baselineEnd`, `baselineStart`, `actualPctComplete` (required).

**Availability.** All emittable; date parsing failure still abstains.

**Literals — the schedule-side twin of Cost Risk Analysis's spread formula:**
- `uncertainty = max(0.05, 1 - si["spi"]) * 0.5` — floor `0.05` and scale `0.5`, both uncommented.
- `p80_days = p50_days * (1 + uncertainty * 1.28)` — the `1.28` is the standard z-score for the
  80th percentile of a normal distribution (documented implicitly by the module name "P80" and
  the shape of the formula, not by an explicit comment), applied here to a hand-built
  `uncertainty` factor rather than to a distribution actually fitted from data. No comment states
  this is a normal-approximation shortcut or that `uncertainty` is not itself a measured standard
  deviation.
- Banding `<=0` Green, `<=14` Yellow, `<=30` Amber, else Red (delay days) — no comment.

**Output / banding.** `p50_delay_days`, `p80_delay_days` (P80 delay beyond the remaining-days
baseline).

**Abstains** on missing fields, unparseable dates, or `total_days <= 0`. **Note the same 1.28
constant and multiplicative-spread shape recurs in Cost Risk Analysis (A3.6) below** — see that
entry and `REPORT_2026-08-10_module-source-export.md` for the cross-reference to the handoff's
"risk register read as data" section, which specifically calls out Cost Risk Analysis's use of
this shape (not this schedule-side module) as reading like measured uncertainty when it is three
literals with no distribution or sample behind them; the same critique applies to this module's
`uncertainty`/`1.28` construction by the same reasoning, though the handoff text names Cost Risk
Analysis specifically.

---

## Critical Path Index

Purpose: Critical Path Index, category "Schedule Performance".

Source (`models_ext.py`):

```python
def run_critical_path_index(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("spi", "plannedPctComplete", "actualPctComplete")):
        return insufficient("Critical_Path_Index")
    progress_ratio = (si["actualPctComplete"] / si["plannedPctComplete"]
                      if si["plannedPctComplete"] > 0 else si["spi"])
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
```

**Inputs.** `spi`, `plannedPctComplete`, `actualPctComplete` (required).

**Availability.** All emittable.

**Literals:** equal-weight average `(progress_ratio + cpi_schedule) / 2` — no comment on 50/50
weighting. Banding `>=0.95/0.92/0.88` — no comment (same four-tier scheme as several A1 modules).

**Output / banding.** `critical_path_index`.

**Abstains** on missing fields (note: `plannedPctComplete <= 0` does not abstain, it falls back
to `spi` alone for `progress_ratio`).

---

## Reference Class Forecasting

Purpose: Reference Class Forecasting, category "Cost Risk". **One of the three cases the task
brief specifically flags.**

Source (`models.py`):

```python
def run_rcf(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """Reference class forecasting: empirical overrun multipliers as a cost prior."""
    bac = num(si.get("bac"), 0.0)
    ordered = sorted([1.00, 1.04, 1.10, 1.14, 1.15, 1.26, 1.38, 1.45, 1.52])
    p50 = pctile(ordered, 0.50)
    p80 = pctile(ordered, 0.80)
    p50_adj = bac * p50
    p80_adj = bac * p80
    over = (p80 - 1) * 100
    color = "Green" if over <= 10 else ("Amber" if over <= 25 else "Red")

    if bac > 0:
        evidence = (f"P80 cost prior ${int(math.floor(p80_adj + 0.5)):,} "
                    f"(+{round1(over)}% vs BAC); debias x{round2(p80)}")
    else:
        evidence = f"Debias x{round2(p80)} (+{round1(over)}% P80 prior; BAC not yet extracted)"

    return {
        "method_class": "Reference_Class_Forecasting",
        "status_color": color,
        "rcf_p50_adjusted": int(math.floor(p50_adj + 0.5)),
        "rcf_p80_adjusted": int(math.floor(p80_adj + 0.5)),
        "debiasing_factor": round2(p80),
        "vs_bac_pct": round1(over),
        "p50_multiplier": round2(p50),
        "p80_multiplier": round2(p80),
        "multipliers": list(ordered),
        "bac": bac,
        "evidence_metric": evidence,
    }
```

**Inputs.** `bac`, read via `num(si.get("bac"), 0.0)` — a **default-to-zero** read, not a
required/abstaining check.

**Availability.** `bac` is emittable, but this module's own arithmetic — not the field
registry — is what stops it abstaining when `bac` is genuinely absent: `num(..., 0.0)` silently
treats "no BAC extracted yet" the same as "BAC is zero," runs the whole computation anyway, and
only changes the wording of `evidence_metric` (branch on `bac > 0`) to say "BAC not yet extracted"
while `rcf_p50_adjusted`/`rcf_p80_adjusted` are still returned as `0` and the status color is
still computed and returned as if it meant something.

**Literals, exhaustively — nine hardcoded historical-overrun multipliers with no cited source,
sample, or study, and an index-based (non-interpolating) percentile function applied to them:**
`[1.00, 1.04, 1.10, 1.14, 1.15, 1.26, 1.38, 1.45, 1.52]` — no comment, docstring, or citation
anywhere in the code as to where these nine numbers come from (what reference class, what study,
what sample size). Banding `over <= 10` Green, `<= 25` Amber, else Red (percent over BAC at P80)
— no comment.

**Mechanically, per `pctile()` (see `SHARED_MACHINERY.md`):** for a 9-element sorted list,
`p50 = pctile(list, 0.50)` picks index `floor(0.50 * 8) = 4` → value `1.15`, and
`p80 = pctile(list, 0.80)` picks index `floor(0.80 * 8) = 6` → value `1.38`. **Because the list of
nine literals never changes and the percentile function is index-based (not interpolated) over a
fixed-length list, P80 is always exactly 1.38 and the P80 overrun (`over`) is always exactly 38.0
percent — for every project, every period, unconditionally.** This is exactly the claim made in
`T6_HANDOFF.md`'s 2026-08-10 "risk register read as data" section (asserted there and reproduced
independently here by walking `pctile`/`ordered` by hand): *"its `pctile` is index-based over
nine literals, so P80 is always 1.38 and its overrun is +38 per cent on every project and every
period, forever (asserted)."* Confirmed against the current code.

**Output / banding.** `rcf_p50_adjusted`/`rcf_p80_adjusted` (BAC × fixed multiplier, i.e. always
BAC×1.15 and BAC×1.38), `debiasing_factor` (always 1.38), `vs_bac_pct` (always 38.0), the raw
multiplier list, and `bac` itself. Status color is likewise fixed at whatever band 38% falls into
— `over <= 25` is false at 38, so **status_color is always "Red"** for any project with a BAC,
and remains "Red" even for BAC=0 (the color computation runs before the BAC-zero branching, which
only changes the evidence string).

**Abstains: never.** This module cannot abstain today — confirmed in code: there is no
`insufficient()` call anywhere in `run_rcf`, and the handoff states directly: *"it cannot abstain
at all today because `num(si.get('bac'), 0.0)` defaults a missing budget to zero."* Verified: the
function has no early return and no `check_inputs`/`insufficient` call of any kind.

---

## Contingency Burn Rate

Purpose: Contingency Burn Rate, category "Cost Risk".

Source (`models_ext.py`):

```python
def run_contingency_burn(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("originalContingency", "remainingContingency", "actualPctComplete")):
        return insufficient("Contingency_Burn_Rate")
    burned = si["originalContingency"] - si["remainingContingency"]
    if not si["originalContingency"] > 0:
        return insufficient("Contingency_Burn_Rate")
    burn_rate = burned / si["originalContingency"]
    expected = si["actualPctComplete"] / 100
    stress = round2(burn_rate / expected if expected > 0 else burn_rate)
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
```

**Inputs.** `originalContingency`, `remainingContingency` (SNAPSHOT, required, may be derived),
`actualPctComplete`.

**Availability.** All emittable.

**Literals:** banding `<=1.0/1.3/1.6` — same shape as Float Consumption, no comment.

**Output / banding.** `burn_rate_pct`, `remaining_pct`, `burn_stress` (burn ÷ expected progress).

**Abstains** on missing fields or `originalContingency <= 0`.

---

## Labor Productivity Index

Purpose: Labor Productivity Index, category "Cost Risk".

Source (`models_ext.py`):

```python
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
```

**Inputs.** `plannedLaborHours`, `actualLaborHours`, `actualPctComplete` (required).

**Availability.** All emittable.

**Literals:** banding `>=0.95/0.85/0.75` — no comment.

**Output / banding.** `earned_hours_rate` (earned hours ÷ actual hours).

**Abstains** on missing fields or `actual <= 0`.

---

## Material Cost Variance

Purpose: Material Cost Variance, category "Cost Risk".

Source (`models_ext.py`):

```python
def run_material_cost_variance(si: dict, rand: Callable[[], float],
                               period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("materialCostBaseline", "materialCostCurrent")):
        return insufficient("Material_Cost_Variance")
    pct = si["actualPctComplete"] / 100 if si.get("actualPctComplete") is not None else None
    expected = si["materialCostBaseline"] * pct if pct is not None else si["materialCostBaseline"]
    variance = (si["materialCostCurrent"] - expected) / expected if expected > 0 else 0
    variance = _round3(variance)
    is_derived = _derived(si, "materialCostBaseline")
    a = abs(variance)
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
```

**Inputs.** `materialCostBaseline`, `materialCostCurrent` (required, may be derived), optionally
`actualPctComplete`.

**Availability.** Both emittable. Evidence string explicitly documents the estimation convention
used upstream when derived: "estimated at 40% of BAC/AC" (that 40% figure lives in the extraction
layer, not in this module — this module only relays the fact that it happened).

**Literals:** banding `<=0.05/0.12/0.20` on absolute variance — no comment.

**Output / banding.** `variance_pct`.

**Abstains** on missing fields (`expected <= 0` falls back to `variance = 0`, not abstention).

---

## Overhead Absorption Rate

Purpose: Overhead Absorption Rate, category "Cost Risk".

Source (`models_ext.py`):

```python
def run_overhead_absorption(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("indirectCostPlan", "indirectCostActual")):
        return insufficient("Overhead_Absorption")
    pct = si["actualPctComplete"] / 100 if si.get("actualPctComplete") is not None else None
    planned = si["indirectCostPlan"] * pct if pct is not None else si["indirectCostPlan"]
    absorption = si["indirectCostActual"] / planned if planned > 0 else 1
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
```

**Inputs.** `indirectCostPlan`, `indirectCostActual` (required, may be derived; note neither
`indirectCostPlan` nor `indirectCostActual` appears in `field_registry.FIELD_KINDS` at all — see
"Availability" below), optionally `actualPctComplete`.

**Availability. DEAD ON ARRIVAL BY FIELD REGISTRY:** `indirectCostPlan` and `indirectCostActual`
are **not present anywhere in `server/app/field_registry.FIELD_KINDS`**, so nothing in the
declared emission layer can write these keys into `signalInputs` today; `check_inputs` will find
them `None` and the module abstains on every real project unless something outside the declared
field registry (not found in this audit) supplies them. The evidence string's "estimated at 12%
overhead" convention implies an intended derivation path exists upstream, but no matching entry
was found in `field_registry.py`.

**Literals:** banding `<=1.05/1.15/1.30` — no comment.

**Output / banding.** `absorption_ratio`.

**Abstains** on missing fields — which, per the above, is effectively always today unless these
two fields are supplied through a path this audit did not locate.

---

## Cost Risk Analysis P80

Purpose: Cost Risk Analysis P80, category "Cost Risk". **The second of the three cases the task
brief specifically flags.**

Source (`models_ext.py`):

```python
def run_cost_risk(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("bac", "cpi", "ac", "ev")):
        return insufficient("Cost_Risk_Analysis")
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
```

**Inputs.** `bac`, `cpi`, `ac`, `ev` — required by `check_inputs`, but **`ac` and `ev` are checked
for presence and then never used anywhere in the formula body.** The entire computation runs off
`bac` and `cpi` alone.

**Availability.** `bac`, `cpi`, `ac`, `ev` all emittable.

**Literals, exhaustively — three literals with no distribution, no sample, and no cited
provenance, exactly as the task brief and the handoff describe:**
- `0.03` — the floor on `abs(1 - cpi)`, i.e. a minimum assumed cost uncertainty of 3% even when
  CPI is exactly on plan. No comment.
- `0.5` — scales the (floored) CPI deviation into an "uncertainty" fraction. No comment.
- `1.28` — the same P80 z-score constant seen in Schedule Risk Analysis (A2.10), applied here to
  scale `eac` up by `uncertainty * 1.28`. No comment.

**Confirmed against `T6_HANDOFF.md` (2026-08-10, "risk register read as data" section), quoted
verbatim there:** *"Cost Risk Analysis computes its whole spread as `max(0.03, abs(1 - cpi)) * 0.5`
times a literal 1.28 and has no slot for probability/impact pairs"* and *"The suite REPRODUCES
the reported 10,555,811 / 79.7 per cent from Cost Risk Analysis exactly, so all of this is
measured."* This audit's read of the current source matches that description exactly: `spread` (as
`uncertainty`) is `max(0.03, abs(1-cpi)) * 0.5`, multiplied by the literal `1.28`, and the module
has no code path that reads a risk register, a probability, or an impact figure of any kind.

**Output / banding.** `p80_eac` (BAC/CPI, inflated by the uncertainty×1.28 factor),
`p80_delta_pct`. Banding `<=5/10/20` percent over BAC — no comment.

**Per the handoff**, this module's `p80_eac` key is one of the two the detail-page card
deliberately stopped printing on 2026-08-10 (the other being Monte Carlo's `p80_eac`) — "the card
no longer prints any eightieth percentile from either Cost Risk Analysis or Monte Carlo... It
prints the exposure the register supports instead." **The module itself is unchanged; only the
card that used to quote it was edited, and that edit lives outside `server/app/simulation/`.**

**Abstains** only when `bac`/`cpi`/`ac`/`ev` are missing — **not** when `cpi == 0`, which this
module does not special-case (unlike Bayesian EAC, VAC, ICE Ratio etc.), so a `cpi` of exactly 0
would raise a `ZeroDivisionError` in `eac = si["bac"] / si["cpi"]` rather than abstaining
gracefully; this audit did not execute the code to confirm the runtime exception, but no
`if si["cpi"] == 0` guard exists in this function, unlike its many siblings that do guard it.

---

## Analogous Estimating Ratio

Purpose: Analogous Estimating Ratio, category "Cost Risk".

Source (`models_ext.py`):

```python
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
```

**Inputs.** `analogousOverrunPct`, `bac` (both emittable per `FIELD_KINDS`; `analogousOverrunPct`
is also one of the `SIGNED_SI_FIELDS` — negative is a legitimate value, "a reference project that
underran is a negative overrun," per that file's comment).

**Availability.** Both emittable.

**Literals:** banding `<3/<7/<12` percent — no comment. Depends entirely on `analogousOverrunPct`
being supplied by an actual analogous/historical-project comparison upstream (not audited further
here — outside `server/app/simulation/`).

**Output / banding.** `analogous_overrun_pct`, `bac_exposure` (dollar exposure = BAC × pct).

**Abstains** on missing fields.

---

## Parametric Cost Index

Purpose: Parametric Cost Index, category "Cost Risk". **Explicitly discussed in the handoff as a
module the same 2026-08-10 review found was mischaracterized in an earlier pass.**

Source (`models_ext.py`):

```python
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
```

**Inputs.** `bac`, `ev`, `ac`, `actualPctComplete` (required, though `actualPctComplete` is
checked but not used in the formula body), `cpi` (read separately with a `None` default, not via
`check_inputs`, so a missing `cpi` is caught by the explicit `cpi is None or cpi == 0` guard
instead).

**Availability.** All emittable.

**Literals:** banding on `abs(index - 1)`: `<=0.03/0.08/0.15` — no comment; **these are the only
literals in this module.** As the handoff states (2026-08-10): *"Parametric Cost invents nothing —
it is a ratio of two EAC conventions over four real extracted figures, only its RAG thresholds are
literals, and including it in the fabricating set was a misdiagnosis; its name oversells it, which
is a naming question."* This audit's read of the source confirms: unlike RCF and Cost Risk
Analysis, this module contains no invented multipliers, spreads, or probability constants — its
only literals are the three RAG (Red/Amber/Green — actually four-tier here, "Yellow" included)
banding cut points on the divergence between two independently-computed EAC figures.

**Output / banding.** `parametric_index` (CPI-based EAC ÷ parametric EAC, i.e. the same ratio
shape as ICE Ratio A1.11 but banded more tightly).

**Abstains** on missing required fields, `cpi` missing/zero, `eac_parametric <= 0`, or
`index == 0`.

---

## Inflation Adjustment Index

Purpose: Inflation Adjustment Index, category "Cost Risk".

Source (`models_ext.py`):

```python
def run_inflation_adjustment(si: dict, rand: Callable[[], float],
                             period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("materialCostBaseline", "materialCostCurrent")):
        return insufficient("Inflation_Adjustment")
    pct = si["actualPctComplete"] / 100 if si.get("actualPctComplete") is not None else None
    expected = si["materialCostBaseline"] * pct if pct is not None else si["materialCostBaseline"]
    escalation = max(0, (si["materialCostCurrent"] - expected) / expected) if expected > 0 else 0
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
```

**Inputs.** `materialCostBaseline`, `materialCostCurrent` (required, may be derived), optionally
`actualPctComplete`. Same source pair as Material Cost Variance (A3.4) — this module is a
one-sided (`max(0, ...)`) escalation-only proxy over the same two fields.

**Availability.** Both emittable.

**Literals:** banding `<=0.04/0.08/0.15` — no comment.

**Output / banding.** `escalation_pct` (only positive deviations counted, unlike A3.4's signed
variance).

**Abstains** on missing fields.

---

## DSM Rework Propagation

Purpose: DSM Rework Propagation, category "System Dynamics & Complexity".

Source (`models.py`):

```python
def run_dsm(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    Design structure matrix rework propagation across Arch, Structural and MEP.

    The 3x3 multiply is written out rather than taken from numpy: the service has been bitten
    twice by compiled-wheel availability and does not need the dependency for nine multiplies.
    The discarded spike also had 0.40 where the instrument has 0.30 at [2][1].
    """
    matrix = [
        [0.0, 0.30, 0.10],
        [0.50, 0.0, 0.20],
        [0.40, 0.30, 0.0],
    ]
    wave = [1.0, 0.0, 0.0]
    cumulative = list(wave)
    for _ in range(4):
        nxt = [0.0, 0.0, 0.0]
        for i in range(3):
            for j in range(3):
                nxt[i] += matrix[i][j] * wave[j]
        for k in range(3):
            cumulative[k] += nxt[k]
        wave = nxt

    total = cumulative[0] + cumulative[1] + cumulative[2]
    color = "Amber" if total > 2.5 else "Green"
    return {
        "method_class": "DSM_Rework_Cat5",
        "status_color": color,
        "rework_multiplier": round2(total),
        "matrix": [list(r) for r in matrix],
        "arch_impact": round2(cumulative[0]),
        "structural_impact": round2(cumulative[1]),
        "mep_impact": round2(cumulative[2]),
        "evidence_metric": (
            f"Architectural change -> x{round2(total)} cumulative rework across "
            f"Arch/Struct/MEP (4 propagation passes)"
        ),
    }
```

**Inputs.** **None from signalInputs at all.** This module reads nothing from `si` — it computes
purely from a hardcoded 3×3 propagation matrix seeded with `wave = [1.0, 0.0, 0.0]` (a fixed
"one unit of architectural change") for a fixed 4 propagation passes.

**Availability.** N/A — no project data is consumed, so the result is **identical for every
project, every period, unconditionally**, regardless of what documents exist.

**Literals, exhaustively — the entire 3×3 coupling matrix, the initial wave vector, and the pass
count are hardcoded:**
- Matrix `[[0, 0.30, 0.10], [0.50, 0, 0.20], [0.40, 0.30, 0]]` — cross-discipline rework
  coupling coefficients between "Arch, Structural and MEP." No comment cites a source study for
  these nine (six nonzero) coefficients; the only provenance note in the docstring is a negative
  one — that a *different, discarded* spike had `0.40` at `[2][1]` where this one has `0.30`,
  i.e. the docstring documents a discrepancy between two uncredited guesses, not the origin of
  either.
- Initial wave `[1.0, 0.0, 0.0]` — "one unit of architectural change" — not tied to any real
  measured change-order magnitude.
- `4` propagation passes — no comment on why 4.
- Banding: `> 2.5` Amber else Green — **only two colors are possible; Red is never reachable by
  this module**, since the matrix, wave, and pass count are fixed and their sum is a deterministic
  constant. No comment on the 2.5 threshold.

**Output / banding.** `rework_multiplier` (deterministic constant, same every run),
`arch_impact`/`structural_impact`/`mep_impact` per-discipline cumulative multipliers, and the
matrix itself echoed back.

**Abstains:** never — cannot, since it reads nothing that could be missing.

---

## Sensitivity Analysis

Purpose: Sensitivity Analysis, category "System Dynamics & Complexity".

Source (`models_doc.py`):

```python
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
```

**Inputs.** `bac`, `ev`, `ac`, `pv`, `cpi`, `spi` (all required — note `ev`/`ac`/`pv` are checked
for presence but never used in the arithmetic body), optionally `docRiskScore`.

**Availability.** All emittable.

**Literals:** the `±0.05` perturbation used for the CPI finite-difference sensitivity — no comment
on why 5 percentage points. `spi_sens = abs(spi - 1.0) * 0.5` — the 0.5 scale factor uncommented.
Banding `<=0.10/0.20/0.35` — no comment.

**Output / banding.** `top_driver`, `top_sensitivity` (%), full `drivers` ranking.

**Abstains** on missing fields, or `cpi` exactly `0`, `0.05`, or `-0.05` (documented refusal of
the JS division-by-zero points), or `eac_base == 0`.

---

## Tornado Risk Ranking

Purpose: Tornado Risk Ranking, category "System Dynamics & Complexity".

Source (`models_doc.py`):

```python
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
```

**Inputs.** `cpi`, `spi`, `docRiskScore`, `actualPctComplete`, `plannedPctComplete` (all required).

**Availability.** All emittable.

**Literals:** composite is an unweighted mean of the four impacts — no comment on equal weighting.
Banding `<=5/10/20` — no comment.

**Output / banding.** `top_risk`, `top_impact`, `composite_score`, full `risks` ranking.

**Abstains** on missing fields.

---

## Scenario Modeling

Purpose: Scenario Modeling, category "System Dynamics & Complexity".

Source (`models_doc.py`):

```python
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
```

**Inputs.** `bac`, `ev`, `ac`, `cpi`, `spi` (required).

**Availability.** All emittable.

**Literals:** the optimistic multiplier `1.00` (i.e. remaining work costs exactly as budgeted) —
no comment. Banding thresholds relative to BAC: `<=1.05/1.10/1.20` — no comment.

**Output / banding.** `optimistic_eac`, `realistic_eac`, `pessimistic_eac`, `scenario_range_pct`.

**Abstains** on missing fields, `cpi == 0`, `min(cpi, spi) == 0`, or `bac == 0`.

---

## Rework Feedback Loop

Purpose: Rework Feedback Loop, category "System Dynamics & Complexity".

Source (`models_doc.py`):

```python
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
```

**Inputs.** `cpi` (required); `rfiCount`, `changeOrderCount` (both optional, contribute 0 when
falsy — JS truthiness, so an RFI count of exactly 0 contributes nothing, documented in the file's
module docstring as a deliberate porting hazard: "Dispute Escalation and Rework Feedback weight
`si.rfiCount ? ... : 0` — an rfiCount of 0 contributes nothing via JS falsiness, reproduced with
explicit checks").

**Availability.** All emittable (`changeOrderCount` is an EVENT-kind field per `field_registry`).

**Literals:** component caps/weights: RFI `min(.../30, 1) * 0.3`, CO `min(.../15, 1) * 0.3`, CPI
`max(0, 1-cpi) * 0.4` — the divisors 30/15 (normalizing scales) and weights 0.3/0.3/0.4 (summing
to 1.0) are all uncommented. Banding `<=0.10/0.25/0.45` — no comment.

**Output / banding.** `rework_index` (weighted composite of RFI rate, CO rate, and CPI shortfall).

**Abstains** only when `cpi` is missing.

---

## Queueing Theory Bottleneck

Purpose: Queueing Theory Bottleneck, category "System Dynamics & Complexity".

Source (`models_doc.py`):

```python
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
```

**Inputs.** `activitiesPlanned`, `activitiesConstrained` — the identical field pair Look-Ahead
Schedule Health (A2.8) uses, banded slightly differently and without the `_derived()` estimation
flag this module lacks (A2.8 marks the estimated case in its evidence text; this module does not).

**Availability.** Both emittable.

**Literals:** banding `<0.15/<0.25/<0.40` — no comment; near-identical thresholds to A2.8's
`<=0.10/<=0.25/<=0.40` but not identical (A2.8's Green cutoff is 0.10, this module's is 0.15) —
no comment explaining why the "queueing theory" framing of the same two fields uses different
thresholds than the "look-ahead health" framing.

**Output / banding.** `constraint_ratio`.

**Abstains** on missing fields.

---

## Agent-Based Supply Chain

Purpose: Agent-Based Supply Chain, category "System Dynamics & Complexity".

Source (`models_doc.py`):

```python
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
```

**Inputs.** `longLeadItemsTotal`, `longLeadAtRisk` (both emittable). Despite the "Agent-Based"
name, the computation is a plain ratio with no agent simulation, population, or interaction model
of any kind.

**Availability.** Both emittable.

**Literals:** banding `<0.10/<0.20/<0.35` — no comment.

**Output / banding.** `at_risk_ratio`.

**Abstains** on missing fields.

---

## Discrete Event Simulation

Purpose: Discrete Event Simulation, category "System Dynamics & Complexity".

Source (`models_doc.py`):

```python
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
```

**Inputs.** `spi`, `actualPctComplete`, `plannedPctComplete`, `cpi` (required — `cpi` is checked
for presence but never used in the formula body). Again, despite the "Discrete Event Simulation"
name, no event queue, arrival process, or simulation clock exists — it is a closed-form ratio.

**Availability.** All emittable.

**Literals:** `0.5` weight on the SPI-shortfall term — no comment. Banding `>=0.92/0.85/0.75` —
no comment.

**Output / banding.** `throughput_index`, `interruption_rate` (%).

**Abstains** on missing fields.

---

## Quality Compliance Index

Purpose: Quality Compliance Index, category "Delivery Quality Performance".

Source (`models_doc.py`):

```python
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
```

**Inputs.** `qualityDeficienciesNoted` (required, emittable, SNAPSHOT), `itemsInspected`
(optional, emittable, default `20` if absent), `itemsFailed` (optional, defaults to
`qualityDeficienciesNoted` if absent), `qualityAuditScore` (optional, emittable).

**Availability.** All fields present in `FIELD_KINDS`.

**Literals:** `itemsInspected` default `20` — no comment on why 20 is the assumed inspection
sample size when no actual inspection count exists. Banding `>=85/70/55` — no comment.

**Output / banding.** `quality_score` (0-100), `pass_rate` (%), raw `deficiencies` count.

**Abstains** only when `qualityDeficienciesNoted` is missing.

---

## Safety Performance Index

Purpose: Safety Performance Index, category "Delivery Quality Performance".

Source (`models_doc.py`):

```python
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
```

**Inputs.** `safetyIncidentsDiscussed` (required), `oshaIncidentRate` (optional, both emittable).

**Availability.** Both emittable.

**Literals:** `safetyIncidentsDiscussed * 10` — the ×10 conversion of a meeting-record incident
mention count into a proxy OSHA-style rate has no comment. `benchmark = 3.0` (an implied
"industry benchmark" OSHA incident rate) — no cited source. `index = min(2, ...)` cap — no
comment. Banding `<=benchmark/<=2×/<=5×` — no comment.

**Output / banding.** `incident_rate`, `industry_benchmark` (fixed 3.0, always echoed back as if
it were a cited figure), `safety_index`, raw `incidents_discussed`.

**Abstains** only when `safetyIncidentsDiscussed` is missing.

---

## Environmental Compliance Rate

Purpose: Environmental Compliance Rate, category "Delivery Quality Performance".

Source (`models_doc.py`):

```python
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
```

**Inputs.** `environmentalIssuesDiscussed` (required), `environmentalComplianceRate` (optional),
`environmentalViolations` (optional) — all present in `FIELD_KINDS`.

**Availability.** All emittable.

**Literals:** derived-rate formula `max(50, 100 - issues*5)` — the floor `50`, base `100`, and
per-issue penalty `5` are all uncommented. Banding `>=95/85/70` — no comment.

**Output / banding.** `compliance_rate` (%, capped at 100), `issues_discussed`, `violations`.

**Abstains** only when `environmentalIssuesDiscussed` is missing.

---

## Contractor Performance Score

Purpose: Contractor Performance Score, category "Delivery Quality Performance".

Source (`models_doc.py`):

```python
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
```

**Inputs.** `overallRating`, `scheduleRating`, `costRating` — **note: `qualityRating` is present
in `field_registry.FIELD_KINDS` as an emittable SNAPSHOT field but is never read by this module**;
only three of the four contractor-rating fields the registry can emit are actually consumed here.

**Availability.** `overallRating`, `scheduleRating`, `costRating` all emittable.

**Literals:** the module takes the *worst* of the three ratings ("weakest-link" logic) — a
deliberate design choice, not a magic number, but the banding thresholds `>=4.0/3.5/3.0` (on a
presumed 1-5 rating scale) are uncommented.

**Output / banding.** `min_rating` (worst of the three ratings, on whatever scale the source
rating fields use — presumed 1-5, not asserted in code).

**Abstains** on missing fields.
