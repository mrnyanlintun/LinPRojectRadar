# Group A: Project Health -- module source export

Regenerated from the registry (Run 5, post-freeze; see code_audit/REPORT_2026-08-11_run5-export.md). Every section below carries its activation state. Headings are canonical module names; no module id appears as a heading, per NAMING_AUTHORITY.md.

**52 modules in this group.**

---

## Monte Carlo EAC

Purpose: Monte Carlo EAC, category "Cost & EVM Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Monte_Carlo`

```python
def run_monte_carlo_module(si, rand, period_cutoff):
    from .models_sim import run_monte_carlo
    return run_monte_carlo(si, rand, SEED_HOLDER.get("seed", 0))
```

---

## Regression to Mean CPI

Purpose: Regression to Mean CPI, category "Cost & EVM Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: fixed 50 per cent shrinkage toward historical mean; coefficient not estimated

Method class: `Regression_To_Mean`

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

---

## ICE Ratio

Purpose: ICE Ratio, category "Cost & EVM Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `ICE_Ratio`

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

---

## CUSUM Anomaly Monitor

Purpose: CUSUM Anomaly Monitor, category "Cost & EVM Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: hard-coded transformations of two-sided CUSUM on real SPI history; k, H, sigma floor and Amber band uncalibrated

Method class: `CUSUM`

```python
def run_cusum_module(si, rand, period_cutoff):
    from .models_sim import run_cusum
    return run_cusum(si, rand, SEED_HOLDER.get("seed", 0))
```

---

## Bayesian EAC

Purpose: Bayesian EAC, category "Cost & EVM Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: Normal-normal updating with designed constant variances, not a governed Bayesian model

Method class: `Bayesian_EAC`

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

---

## Kalman Filter SPI Smoother

Purpose: Kalman Filter SPI Smoother, category "Cost & EVM Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: Scalar Kalman recursion with fixed Q and R, short history, no calibrated filtering claim

Method class: `Kalman_Filter`

```python
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

---

## ARIMA CPI Forecast

Purpose: ARIMA CPI Forecast, category "Cost & EVM Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `ARIMA_Forecast`

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

---

## Earned Schedule

Purpose: Earned Schedule, category "Cost & EVM Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Earned_Schedule`

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

---

## TCPI

Purpose: TCPI, category "Cost & EVM Performance".

Activation state: ENABLED AND VOTING. One of the two CORE modules with a sourced band boundary, a built abstention guard and passing boundary tests (Run 4). Feeds category rollup, project status fusion, generated recommendation text, courses of action and the decision card. Band boundaries are sourced to published literature. False-positive and false-negative performance is not measured: no labelled holdout corpus and no expert reference standard exist for this platform, so how often a band is right is unknown.

Method class: `TCPI`

```python
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
```

---

## Variance at Completion

Purpose: Variance at Completion, category "Cost & EVM Performance".

Activation state: ENABLED AND VOTING. One of the two CORE modules with a sourced band boundary, a built abstention guard and passing boundary tests (Run 4). Feeds category rollup, project status fusion, generated recommendation text, courses of action and the decision card. Band boundaries are sourced to published literature. False-positive and false-negative performance is not measured: no labelled holdout corpus and no expert reference standard exist for this platform, so how often a band is right is unknown.

Method class: `VAC`

```python
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
```

---

## Budget Execution Rate

Purpose: Budget Execution Rate, category "Cost & EVM Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: an expenditure-versus-progress control ratio, not a standardised statistical test

Method class: `Budget_Execution_Rate`

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

---

## PERT Network Criticality

Purpose: PERT Network Criticality, category "Schedule Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `PERT_Network_Criticality`

```python
def run_pert(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    PERT stochastic network criticality. A then (B parallel C); finish = A + max(B, C).

    The only stochastic model in the ported set. The caller seeds from (scenario_id, period), so
    every participant on that scenario and period draws the identical sample path.

    RUN 7. Handed an empty dictionary this read Green. The schedule index defaulted to 1.0, which
    is the value of a project exactly on plan, so a project about which nothing had been reported
    was modelled as a project performing to plan and banded accordingly. The index is now
    required. The activity durations remain the module's own literals and this run does not
    pretend otherwise: a project-specific activity network is not in the corpus, and building one
    is out of scope. What is corrected is that the module no longer reports on a project it has
    been told nothing about.
    """
    verdict = eligible(si, required=(("spi", "the schedule performance index"),))
    if verdict:
        return refuse("PERT_Network_Criticality", verdict)
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

---

## Schedule Risk Analysis P80

Purpose: Schedule Risk Analysis P80, category "Schedule Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Schedule_Risk_Analysis`

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

---

## Critical Path Index

Purpose: Critical Path Index, category "Schedule Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Critical_Path_Index`

```python
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
```

---

## Line of Balance

Purpose: Line of Balance, category "Schedule Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Line_of_Balance_Velocity`

```python
def run_lob(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    Line of balance: leader (grading) against follower (paving), buffer eroding per unit.

    RUN 7. Same defect as the network model above and the same correction: an empty dictionary
    defaulted the schedule index to 1.0 and read Green. The unit count, the two production rates
    and the buffer stay the module's own literals, because locations, crews and production rates
    are not in the corpus and inventing them is out of scope.
    """
    verdict = eligible(si, required=(("spi", "the schedule performance index"),))
    if verdict:
        return refuse("Line_of_Balance_Velocity", verdict)
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

---

## CCPM Buffer Health

Purpose: CCPM Buffer Health, category "Schedule Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `CCPM_Buffer_Health`

```python
def run_ccpm(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    CCPM buffer-health fever chart: buffer consumption against chain completion.

    RUN 7. Handed an empty dictionary this read Amber: chain completion fell back to zero per
    cent and the schedule index to 1.0, and the fever chart placed a project nobody had reported
    on in the warning zone. Both figures are now required, chain completion from either the
    reported or the planned completion, and the module abstains without them. The buffer itself
    remains derived from the schedule index rather than from a governed critical-chain buffer,
    which is out of scope, and the qualifier says so.
    """
    verdict = eligible(si, required=(("spi", "the schedule performance index"),))
    if verdict:
        return refuse("CCPM_Buffer_Health", verdict)
    raw = si.get("actualPctComplete")
    if raw is None:
        raw = si.get("plannedPctComplete")
    if raw is None:
        return insufficient(
            "CCPM_Buffer_Health",
            "Insufficient data: neither a reported nor a planned percent complete has been "
            "reported for this period, so there is no chain completion to place the buffer "
            "against.",
            ABSTAIN_MISSING_INPUT)
    if num(raw, None) is None:
        return insufficient(
            "CCPM_Buffer_Health",
            "Insufficient data: percent complete was reported in a form that is not a number.",
            ABSTAIN_MALFORMED_INPUT)
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

---

## Schedule Compression Index

Purpose: Schedule Compression Index, category "Schedule Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: a custom compression ratio; no network-based crashing model or calibrated bands

Method class: `Schedule_Compression`

```python
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
```

---

## Float Consumption Rate

Purpose: Float Consumption Rate, category "Schedule Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Float_Consumption`

```python
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
```

---

## S-Curve Deviation

Purpose: S-Curve Deviation, category "Schedule Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: a single planned versus actual snapshot, not a longitudinal S-curve analysis

Method class: `SCurve_Deviation`

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

---

## Milestone Trend Analysis

Purpose: Milestone Trend Analysis, category "Schedule Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: a simplified shift summary on real milestone history, bands uncalibrated

Method class: `Milestone_Trend`

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
```

---

## Look-Ahead Schedule Health

Purpose: Look-Ahead Schedule Health, category "Schedule Performance".

Activation state: ADVISORY, NON-VOTING. One of the seven CORE candidates; computes and shows its finding on the ledger, but held out of voting because no source specifies a constraint-rate threshold; the published plan-reliability benchmarks measure a different quantity.

Method class: `Lookahead_Health`

```python
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
```

---

## Resource Loading Index

Purpose: Resource Loading Index, category "Schedule Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Resource_Loading`

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

---

## Reference Class Forecasting

Purpose: Reference Class Forecasting, category "Cost Risk".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Reference_Class_Forecasting`

```python
def run_rcf(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    Reference class forecasting: empirical overrun multipliers as a cost prior.

    RUN 7, AND THIS ONE ABSTAINS UNCONDITIONALLY.

    The method is defined by its reference class: a population of comparable completed projects
    whose realised overruns give the distribution the forecast is drawn from. This platform holds
    no such population. The nine multipliers below are literals, so the percentile, the debiasing
    factor and therefore the band are the same numbers on every project and in every period, and
    handed an empty dictionary the module read Red about a project nobody had reported anything
    for. It read the budget only to scale a figure it displayed; nothing about a project could
    move the band.

    There is no input that would make it eligible, so there is no preflight to write: the missing
    thing is the reference class itself. Building one is out of scope, and a proxy that keeps
    emitting a constant band is the fault this run exists to remove. The module therefore refuses
    and states that the reference class is absent. The arithmetic it used to perform is not kept
    here as dead code: the suite reads it out of the pinned baseline commit, which is how every
    remediation run on this repository has proved what the shipped code did.
    """
    return insufficient(
        "Reference_Class_Forecasting",
        "Insufficient data: no reference class of comparable completed projects is held, so "
        "there is no distribution of realised overruns to place this project against. No "
        "forecast is offered in its place.",
        ABSTAIN_STRUCTURE_ABSENT)
```

---

## Contingency Burn Rate

Purpose: Contingency Burn Rate, category "Cost Risk".

Activation state: ADVISORY, NON-VOTING. One of the seven CORE candidates; computes and shows its finding on the ledger, but held out of voting because no source specifies a burn-against-progress threshold, and the proportional-drawdown premise the band rests on is not what the contingency literature describes.

Method class: `Contingency_Burn_Rate`

```python
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
```

---

## Labor Productivity Index

Purpose: Labor Productivity Index, category "Cost Risk".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: a labour-hours ratio, not an earned-output productivity model

Method class: `Labor_Productivity`

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

---

## Material Cost Variance

Purpose: Material Cost Variance, category "Cost Risk".

Activation state: ADVISORY, NON-VOTING. One of the seven CORE candidates; computes and shows its finding on the ledger, but held out of voting because no source specifies a control limit for a mid-execution variance against a progress-adjusted baseline; the published accuracy ranges describe estimate accuracy at preparation.

Method class: `Material_Cost_Variance`

```python
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
```

---

## Overhead Absorption Rate

Purpose: Overhead Absorption Rate, category "Cost Risk".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: a transparent ratio; validity depends on whether the indirect plan is total or period-to-date

Method class: `Overhead_Absorption`

```python
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
```

---

## Cost Risk Analysis P80

Purpose: Cost Risk Analysis P80, category "Cost Risk".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Cost_Risk_Analysis`

```python
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
```

---

## Analogous Estimating Ratio

Purpose: Analogous Estimating Ratio, category "Cost Risk".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: an analogous-cost ratio; project selection, normalisation and adaptation ungoverned

Method class: `Analogous_Estimating`

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

---

## Parametric Cost Index

Purpose: Parametric Cost Index, category "Cost Risk".

Activation state: DISABLED. Concept-only: implements no defensible version of the analytical structure its name claims. Non-executable in production, non-voting, excluded from every fusion input and every rollup.

Method class: `Parametric_Cost`

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

---

## Inflation Adjustment Index

Purpose: Inflation Adjustment Index, category "Cost Risk".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: a material-escalation ratio with no external price index, time base or geography

Method class: `Inflation_Adjustment`

```python
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
```

---

## Specification Conflict Density

Purpose: Specification Conflict Density, category "Document-Derived Condition Signals".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Spec_Conflict_Density`

```python
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
```

---

## RFI Velocity

Purpose: RFI Velocity, category "Document-Derived Condition Signals".

Activation state: ADVISORY, NON-VOTING. One of the seven CORE candidates; computes and shows its finding on the ledger, but held out of voting because no source specifies a per-week request rate or an overdue-share threshold.

Method class: `RFI_Velocity`

```python
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
```

---

## Submittal Rejection Rate

Purpose: Submittal Rejection Rate, category "Document-Derived Condition Signals".

Activation state: ADVISORY, NON-VOTING. One of the seven CORE candidates; computes and shows its finding on the ledger, but held out of voting because no source specifies a rejection-share threshold.

Method class: `Submittal_Rejection`

```python
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
```

---

## NCR Rate

Purpose: NCR Rate, category "Document-Derived Condition Signals".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `NCR_Rate`

```python
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
```

---

## Weather Day Impact

Purpose: Weather Day Impact, category "Document-Derived Condition Signals".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: a lost-days over available-float ratio with ungoverned bands, computed only from verified lost days and a reported float figure

Method class: `Weather_Impact`

```python
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
```

---

## Change Order Frequency

Purpose: Change Order Frequency, category "Document-Derived Condition Signals".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: contract growth plus a raw count; no time or exposure denominator

Method class: `CO_Frequency`

```python
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
```

---

## Dispute Escalation Index

Purpose: Dispute Escalation Index, category "Document-Derived Condition Signals".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: an ad hoc 0.3 / 0.3 / 0.4 weighted sum; weights and dependence uncalibrated

Method class: `Dispute_Escalation`

```python
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
```

---

## Subcontractor Performance

Purpose: Subcontractor Performance, category "Document-Derived Condition Signals".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: a precomputed compliance score; provenance and construction unvalidated

Method class: `Subcontractor_Performance`

```python
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
```

---

## Procurement Lead Time Monitor

Purpose: Procurement Lead Time Monitor, category "Document-Derived Condition Signals".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Procurement_Lead_Time`

```python
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
```

---

## DSM Rework Propagation

Purpose: DSM Rework Propagation, category "System Dynamics & Complexity".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `DSM_Rework_Cat5`

```python
def run_dsm(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    Design structure matrix rework propagation across Arch, Structural and MEP.

    RUN 7, AND THIS ONE ABSTAINS UNCONDITIONALLY.

    The method is defined by its dependency matrix: which parts of a project's design depend on
    which others, and how strongly, for the project being analysed. The nine coefficients below
    were literals, the initiating wave was a literal, and no project input was read anywhere in
    the computation. Handed an empty dictionary the module read Amber, and handed a complete
    project it read the same Amber, because nothing about a project could reach the arithmetic.
    The result had the shape of an analysis of a project and was a property of the file.

    No dependency matrix is in the corpus and building one is out of scope, so there is no input
    that would make the module eligible. It refuses and says which structure is missing. The
    suite reads the previous arithmetic out of the pinned baseline commit rather than this file
    keeping it as dead code.
    """
    return insufficient(
        "DSM_Rework_Cat5",
        "Insufficient data: no dependency matrix has been established for this project, so "
        "there is no record of which parts of the design depend on which others and a rework "
        "wave cannot be traced through them. No multiplier is offered in its place.",
        ABSTAIN_STRUCTURE_ABSENT)
```

---

## Sensitivity Analysis

Purpose: Sensitivity Analysis, category "System Dynamics & Complexity".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: local CPI perturbation plus deviations, not calibrated multivariate sensitivity

Method class: `Sensitivity_Analysis`

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

---

## Tornado Risk Ranking

Purpose: Tornado Risk Ranking, category "System Dynamics & Complexity".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: a ranking of four present-state deviations; no outcome-response ranges estimated

Method class: `Tornado_Diagram`

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

---

## Scenario Modeling

Purpose: Scenario Modeling, category "System Dynamics & Complexity".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Scenario_Modeling`

```python
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
```

---

## Rework Feedback Loop

Purpose: Rework Feedback Loop, category "System Dynamics & Complexity".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Rework_Feedback`

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

---

## Queueing Theory Bottleneck

Purpose: Queueing Theory Bottleneck, category "System Dynamics & Complexity".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Queueing_Bottleneck`

```python
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
```

---

## Agent-Based Supply Chain

Purpose: Agent-Based Supply Chain, category "System Dynamics & Complexity".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Agent_Supply_Chain`

```python
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
```

---

## Discrete Event Simulation

Purpose: Discrete Event Simulation, category "System Dynamics & Complexity".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Discrete_Event_Sim`

```python
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
```

---

## Quality Compliance Index

Purpose: Quality Compliance Index, category "Delivery Quality Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Quality_Compliance`

```python
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
```

---

## Safety Performance Index

Purpose: Safety Performance Index, category "Delivery Quality Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Safety_Performance`

```python
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
```

---

## Environmental Compliance Rate

Purpose: Environmental Compliance Rate, category "Delivery Quality Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Environmental_Compliance`

```python
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
```

---

## Contractor Performance Score

Purpose: Contractor Performance Score, category "Delivery Quality Performance".

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class: `Contractor_Performance`

```python
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
```

---

## Document Risk Score (supplied, not computed)

Activation state: SUPPLIED, NOT COMPUTED. `A4.1` is declared in `p0-baseline/module_renumbering_map.csv` but implemented by no formula function anywhere under `server/app/simulation/`. It is a value the extraction model supplies and the server carries through unmodified -- not a computation this platform performs. Not part of the group's registry-computed count, and not one of the 100 registry-computed modules across the four groups. See GROUP_ASSIGNMENT.md and REPORT_2026-08-11_run4-validate-seven.md.

No source to export: no formula function exists.

---
