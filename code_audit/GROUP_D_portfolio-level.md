# Group D: Portfolio Level -- module source export

Regenerated from the registry (Run 5, post-freeze; see code_audit/REPORT_2026-08-11_run5-export.md). Every section below carries its activation state. Headings are canonical module names; no module id appears as a heading, per NAMING_AUTHORITY.md.

**5 modules in this group.**

---

## Portfolio computation (all five Group D modules)

Activation state: not a single module. This section holds the shared source only; each of the five modules below carries its own activation state.

All five Group D modules are produced by one function, `compute_portfolio`, in `server/app/simulation/portfolio.py`. There is no per-module function to excerpt; the full function is transcribed once and each subsection below states which returned keys and status fields belong to which module.

```python
def compute_portfolio(portfolio: list[dict], current_id, history: list[dict] | None,
                      period_cutoff) -> dict[str, Any]:
    """Port of portfolioAnalyze_({id, portfolio, history}); period_cutoff replaces the clock."""
    if not current_id:
        return {"ok": False, "error": "id is required"}
    portfolio = portfolio or []
    if len(portfolio) < 2:
        return _insufficient(current_id,
                             "Portfolio too small for anomaly detection — need at least 3 "
                             "projects with signal data")

    def vec(p):
        return [p.get("cpi") or 1.0, p.get("spi") or 1.0,
                p.get("docRiskScore") or 0.0, (p.get("actualPctComplete") or 50) / 100]

    vectors = [{"id": p.get("id"), "v": vec(p)} for p in portfolio
               if p.get("cpi") is not None and p.get("spi") is not None]
    current = next((p for p in portfolio if p.get("id") == current_id), None)
    if current is None or not current.get("cpi"):
        return _insufficient(current_id,
                             "Current project has no signal data — upload EVM documents first")
    current_vec = vec(current)
    n = len(vectors)
    if n < 2:
        return _insufficient(current_id, "Insufficient projects with signal data in portfolio")

    centroid = [0.0, 0.0, 0.0, 0.0]
    for v in vectors:
        for i, x in enumerate(v["v"]):
            centroid[i] += x / n
    variance = [0.0, 0.0, 0.0, 0.0]
    for v in vectors:
        for i, x in enumerate(v["v"]):
            variance[i] += (x - centroid[i]) ** 2 / n
    stddev = [math.sqrt(v) or 0.001 for v in variance]

    def mahalanobis(vector):
        return math.sqrt(sum(((x - centroid[i]) / stddev[i]) ** 2
                             for i, x in enumerate(vector)))

    all_dists = [mahalanobis(v["v"]) for v in vectors]
    current_dist = mahalanobis(current_vec)
    max_dist = max(all_dists)
    mean_dist = sum(all_dists) / len(all_dists)
    threshold = mean_dist + 1.5 * sum(stddev)
    anomaly_score = min(1, current_dist / (max_dist or 1))
    iso_status = ("Red" if current_dist > threshold
                  else "Amber" if current_dist > threshold * 0.7
                  else "Yellow" if current_dist > threshold * 0.4 else "Green")
    isolation_forest = {
        "method_class": "Isolation_Forest", "status_color": iso_status,
        "anomaly_score": round2(anomaly_score), "distance": round2(current_dist),
        "threshold": round2(threshold), "portfolio_size": n,
        "is_anomaly": current_dist > threshold,
        "evidence_metric": f"Isolation Forest: anomaly score {int(js_round(anomaly_score * 100))}%",
    }

    cpi_rank = sum(1 for v in vectors if v["v"][0] <= current_vec[0]) / n
    spi_rank = sum(1 for v in vectors if v["v"][1] <= current_vec[1]) / n
    composite_rank = (cpi_rank + spi_rank) / 2
    outlier_status = ("Red" if composite_rank <= 0.15 else "Amber" if composite_rank <= 0.30
                      else "Yellow" if composite_rank <= 0.45 else "Green")
    portfolio_outlier = {
        "method_class": "Portfolio_Outlier", "status_color": outlier_status,
        "cpi_percentile": int(js_round(cpi_rank * 100)),
        "spi_percentile": int(js_round(spi_rank * 100)),
        "composite_percentile": int(js_round(composite_rank * 100)),
        "evidence_metric": f"Portfolio percentile: {int(js_round(composite_rank * 100))}%",
    }

    # D1.3 abstains by ABSENCE when there is no usable history, matching the project-level
    # contract: an abstaining module is absent from module_results entirely, never present with
    # a colour. The Apps Script emitted status_color "Green" beside insufficient_data: true here,
    # and every display renders the colour without reading the flag — a green dot over "No
    # history available". Diverges from the validated JavaScript deliberately, in the same way
    # and for the same reason as the D1 divergences recorded in VALIDATION.md.
    history = history or []
    trend = 0.0
    trajectory_classifier = None
    if len(history) >= 2:
        recent = history[-3:]
        cpi_values = [h.get("signal_inputs", {}).get("cpi") for h in recent
                      if h.get("signal_inputs")]
        cpi_values = [v for v in cpi_values if v is not None]
        if len(cpi_values) >= 2:
            # THE FIFTEEN DEFECTS, defect 6. The change per period is a slope, so it divides by
            # the number of INTERVALS between the observations, not by the number of
            # observations. Cost performance of 0.9, 1.0 and 1.1 is two intervals of one tenth
            # each: the trend is 0.1 per period, and this returned 0.066667 because it divided
            # the same rise by three. It understated every trajectory it classified, by a factor
            # that grew with the length of the history, and the band ladder below reads the
            # number directly, so a project improving or deteriorating fast enough to change
            # band was reported in a calmer one.
            trend = (cpi_values[-1] - cpi_values[0]) / (len(cpi_values) - 1)
            trajectory_status = ("Green" if trend >= 0.01 else "Yellow" if trend >= -0.01
                                 else "Amber" if trend >= -0.03 else "Red")
            trajectory_desc = (f"CPI trend: {'+' if trend >= 0 else ''}"
                               f"{_num_str(js_round(trend * 1000) / 10)}% per period")
            trajectory_classifier = {
                "method_class": "Trajectory_Classifier", "status_color": trajectory_status,
                "trend": _round3(trend), "periods_analyzed": len(history),
                "insufficient_data": False,
                "evidence_metric": trajectory_desc,
            }

    similar = [v for v in vectors if v["id"] != current_id
               and math.sqrt(sum((v["v"][i] - current_vec[i]) ** 2 for i in range(3))) < 0.15]
    pattern_status = "Green"
    pattern_desc = "No similar distress pattern found in portfolio"
    if similar:
        # THE FIFTEEN DEFECTS, defect 7. The ladder ended at Yellow, so the moment ANY project
        # in the portfolio resembled this one the answer could never be Green again, however
        # well every one of them was performing. A cluster of healthy projects is not a distress
        # pattern; it is the portfolio behaving. The band now continues past Yellow, so a
        # matched cluster whose cost performance is at or above plan reads Green, and the
        # question the computation is named for ("do similar projects show distress?") can be
        # answered no rather than only "less badly".
        avg_cpi = sum(v["v"][0] for v in similar) / len(similar)
        pattern_status = ("Red" if avg_cpi < 0.90 else "Amber" if avg_cpi < 0.95
                          else "Yellow" if avg_cpi < 1.00 else "Green")
        pattern_desc = f"{len(similar)} project(s) show similar signal pattern"
    cross_project = {
        "method_class": "Cross_Project_Pattern", "status_color": pattern_status,
        "similar_project_count": len(similar), "evidence_metric": pattern_desc,
    }

    # THE FIFTEEN DEFECTS, defect 8. The third element of this list was the literal 0.5. It was
    # not a measurement of anything: it was a placeholder that entered the mean on every project
    # in every portfolio and pulled every composite score toward the middle. A project that is
    # the least anomalous in its portfolio and ranks best on both indices scored 0.166667 where
    # the honest answer is zero, and the ladder below reads it directly. The mean is now taken
    # over the terms that were actually measured.
    scores = [anomaly_score, 1 - composite_rank]
    if len(history) >= 2 and trend != 0:
        scores.append(min(1, abs(trend) * 20))
    composite_anomaly = round2(sum(scores) / len(scores))
    anomaly_final = ("Red" if composite_anomaly >= 0.70 else "Amber" if composite_anomaly >= 0.50
                     else "Yellow" if composite_anomaly >= 0.30 else "Green")
    anomaly_result = {
        "method_class": "Anomaly_Score", "status_color": anomaly_final,
        "composite_score": composite_anomaly,
        "evidence_metric": f"Composite anomaly score: {int(js_round(composite_anomaly * 100))}%",
    }

    results = {
        "cat8_1_isolation_forest": isolation_forest,
        "cat8_2_portfolio_outlier": portfolio_outlier,
    }
    if trajectory_classifier is not None:
        results["cat8_3_trajectory_classifier"] = trajectory_classifier
    results["cat8_4_cross_project_pattern"] = cross_project
    results["cat8_5_anomaly_score"] = anomaly_result

    return {
        "ok": True,
        "id": current_id,
        "portfolio_size": n,
        "results": results,
        # The Apps Script stamps new Date().toISOString() here; no module reads the clock.
        "period_cutoff": str(period_cutoff),
    }
```

---

## Isolation Forest

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class `Isolation_Forest`, produced within `compute_portfolio` above (search the function for `"method_class": "Isolation_Forest"`).

---

## Portfolio Outlier

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module. RELABELLED AS PROXY: an empirical CPI and SPI percentile rank; small-n behaviour and bands unvalidated

Method class `Portfolio_Outlier`, produced within `compute_portfolio` above (search the function for `"method_class": "Portfolio_Outlier"`).

---

## Trajectory Classifier

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class `Trajectory_Classifier`, produced within `compute_portfolio` above (search the function for `"method_class": "Trajectory_Classifier"`).

---

## Cross Project Pattern

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class `Cross_Project_Pattern`, produced within `compute_portfolio` above (search the function for `"method_class": "Cross_Project_Pattern"`).

---

## Anomaly Score

Activation state: ADVISORY, NON-VOTING. Computes and shows its finding; excluded from category rollup, project status fusion, recommendation text, courses of action and the decision card, on the footing of every non-CORE module.

Method class `Anomaly_Score`, produced within `compute_portfolio` above (search the function for `"method_class": "Anomaly_Score"`).

---
