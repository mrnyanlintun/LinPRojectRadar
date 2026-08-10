# Group D — Portfolio Level

5 modules. Purpose: "requires more than one project." Source: `server/app/simulation/portfolio.py`.

**Structural note, stated once for the whole group:** unlike Groups A/B/C, these five modules are
not five independent functions — they are five sections of one function, `compute_portfolio()`,
which is the single entry point (`compute_portfolio(projects, current_id, history, period_cutoff)`)
called on a **list of project vectors**, not a single project's `signalInputs`. The single-project
registry path (`registry.run_module`) **hard-refuses** any Group D id with
`PortfolioModuleError` — Group D is not reachable from `run_all`/`run_module` at all; a
single-project caller that reaches one is treated as a routing mistake, not as insufficient data.
`PORTFOLIO_VALIDATED` (in `portfolio.py`) is the id→name map the registry cross-checks against for
counting purposes: `{"D1.1": "Isolation_Forest", "D1.2": "Portfolio_Outlier", "D1.3":
"Trajectory_Classifier", "D1.4": "Cross_Project_Pattern", "D1.5": "Anomaly_Score"}`.

All five modules share:
- the same portfolio-size guard (`portfolio too small`),
- the same centroid/variance/Mahalanobis-distance vector-space construction over `(cpi, spi,
  docRiskScore, actualPctComplete)`,
- the historical Apps Script provenance noted in the file's module docstring: ported from
  `apps_script/reference/Code_v10.36_editor_head.gs`'s `portfolioAnalyze_`, validated against a
  live deployment via read-only POSTs (see `VALIDATION.md`), not against `assets/js/simulations.js`
  like every Group A/B/C module.

Full setup shared by all five (quoted once; individual module sections below reference it and
quote only their own section of the function):

```python
PORTFOLIO_VALIDATED = {
    "D1.1": "Isolation_Forest",
    "D1.2": "Portfolio_Outlier",
    "D1.3": "Trajectory_Classifier",
    "D1.4": "Cross_Project_Pattern",
    "D1.5": "Anomaly_Score",
}


def _insufficient(current_id, message: str) -> dict[str, Any]:
    return {"ok": True, "id": current_id, "insufficient_data": True,
            "message": message, "results": {}}


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
```

**Documented quirks (module-level docstring, applying to all five):**
- The small-portfolio guard is `len(portfolio) < 2` while its own message says "need at least 3
  projects" — reproduced verbatim from the Apps Script, message mismatch and all, plus a second
  `n < 2` guard after the cpi/spi filter.
- Vector building uses JS truthiness: `p.cpi || 1.0` maps a `cpi` of exactly 0 to `1.0`, so a
  current project whose `cpi` is genuinely 0 is treated by the vector-builder as having a perfect
  CPI, though the separate `not current.get("cpi")` guard above (also JS-truthiness-shaped) still
  catches a `cpi` of 0 for the *current* project specifically and reports insufficient data for
  it before the vector-with-1.0 would ever be used for `current_vec`.
- `stddev = math.sqrt(v) or 0.001` floors a zero-variance dimension at `0.001` — a portfolio where
  every project has the identical value on some dimension would otherwise divide by zero in the
  Mahalanobis distance.
- The Apps Script stamps `timestamp: new Date().toISOString()`; the port stamps `period_cutoff`
  instead (no module reads the system clock) and the timestamp field is excluded from the
  numeric comparison in `VALIDATION.md`.

**Inputs common to all five.** `portfolio` — a list of per-project dicts each with `id`, `cpi`,
`spi`, `docRiskScore`, `actualPctComplete` (the same flat signalInputs-style keys Group A modules
read, but supplied here as a list across projects, assembled by the caller of
`compute_portfolio`, not by the single-project `si` merge this audit traced for Groups A/B/C).
`current_id` (required, or the whole call returns `{"ok": False, "error": "id is required"}` — not
an `insufficient_data` shape). `history` (optional, a list of prior periods' stored results, used
only by D1.3).

**Availability.** The four vector fields (`cpi`, `spi`, `docRiskScore`, `actualPctComplete`) are
each individually emittable per `field_registry.FIELD_KINDS`, on a per-project basis; whether the
portfolio list itself (multiple projects' assembled signal dicts) is correctly built and passed to
`compute_portfolio` is a concern of the caller outside `server/app/simulation/`, not audited
further here.

**Abstention shape common to all five.** Group D uses a **different** abstention contract than
Groups A/B/C's `insufficient()`: `_insufficient()` returns `{"ok": True, "id": ...,
"insufficient_data": True, "message": ..., "results": {}}` — no `status_color`/`method_class` key
at the top level at all (those exist only nested inside `results` for whichever sub-modules did
compute). All five modules share the same three top-level entry gates: `current_id` missing → hard
error (not abstention); `len(portfolio) < 2` → abstain with message "Portfolio too small...";
current project not found or has no `cpi` → abstain "Current project has no signal data..."; fewer
than 2 vectorizable projects → abstain "Insufficient projects with signal data in portfolio."

---

## Isolation Forest

Purpose: Isolation Forest, category "Portfolio Health". Registry CSV notes: "parked on portfolio
page; requires 3+ projects."

Source (`portfolio.py`, continuing from the shared setup above):

```python
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
```

**Inputs.** The shared portfolio vectors (see group-level note above): `cpi`, `spi`,
`docRiskScore`, `actualPctComplete` across all projects with signal data, plus the current
project's own vector.

**Literals — despite the "Isolation Forest" name, this is a plain Mahalanobis-distance-from-centroid
anomaly score, not an actual isolation-forest ensemble of random partitioning trees:**
`threshold = mean_dist + 1.5 * sum(stddev)` — the `1.5` multiplier on the summed per-dimension
standard deviations has no comment or citation. Banding fractions of `threshold`: `>threshold` Red,
`>0.7×threshold` Amber, `>0.4×threshold` Yellow, else Green — the `0.7`/`0.4` fractions are
uncommented.

**Output / banding.** `anomaly_score` (current distance ÷ max distance in the portfolio, capped at
1), `distance` (raw Mahalanobis distance), `threshold`, `portfolio_size`, `is_anomaly` boolean.

**Abstains** per the group-level shared entry gates only (no module-specific additional guard).

---

## Portfolio Outlier Detection

Purpose: Portfolio Outlier Detection, category "Portfolio Health". Same registry note.

Source (`portfolio.py`, continuing):

```python
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
```

**Inputs.** Same shared vectors; specifically uses only the CPI and SPI components (index 0, 1) of
each project's vector.

**Literals:** `composite_rank = (cpi_rank + spi_rank) / 2` — equal-weight average, no comment.
Banding `<=0.15/0.30/0.45` (percentile rank, low percentile is worse) — no comment.

**Output / banding.** `cpi_percentile`, `spi_percentile`, `composite_percentile` (empirical rank
within the current portfolio, i.e. genuinely data-derived, not a fixed literal — unlike most
Group B fuzzy-set modules, this module's percentile ranking is computed directly from the actual
portfolio's CPI/SPI distribution).

**Abstains** per the shared entry gates only.

---

## Signal Trajectory Classifier

Purpose: Signal Trajectory Classifier, category "Portfolio Health". Same registry note. **The one
module in this group with its own additional abstention rule and a documented deliberate
divergence from the validated JavaScript.**

Source (`portfolio.py`, continuing):

```python
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
            trend = (cpi_values[-1] - cpi_values[0]) / len(cpi_values)
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
```

**Inputs.** `history` — a list of prior periods' stored results, each expected to carry
`signal_inputs.cpi`; up to the three most recent periods (`history[-3:]`) are used, of which at
least 2 must actually have a non-`None` `cpi` value.

**Availability.** Depends on prior-period history being supplied to `compute_portfolio` by its
caller — not covered by `field_registry.py` (that registry governs single-project `signalInputs`
series like `cpiHistory`, not this portfolio-level `history` parameter, which is a distinct
mechanism traced only as far as this function's own parameter).

**Literals:** `trend = (cpi_values[-1] - cpi_values[0]) / len(cpi_values)` — dividing the CPI
change by the *count* of values used (2 or 3), not by the number of intervals between them — this
is an averaging convention, not commented as deliberate vs. incidental. Banding `>=0.01/−0.01/−0.03`
(CPI trend per period) — no comment.

**Output / banding.** `trend` (per-period CPI slope), `periods_analyzed` (note: this is
`len(history)`, the full history length, **not** the count actually used in the trend calculation,
which could differ if some periods lacked a `cpi` value). Explicitly carries `insufficient_data:
False` inside its own result dict, distinguishing "this sub-module computed" from the parent
call's own `insufficient_data` flag.

**Abstains — this module alone, by omission** — when fewer than 2 history points exist, or fewer
than 2 of the most recent 3 have a usable `cpi`, `trajectory_classifier` stays `None` and the key
`cat8_3_trajectory_classifier` is simply **absent** from the `results` dict returned by
`compute_portfolio` (see the code comment above, which documents this as a deliberate departure
from the original Apps Script, which instead emitted a Green-colored stub next to
`insufficient_data: true` — a "green dot over 'No history available'" that every display rendered
as a real Green regardless of the flag).

---

## Cross-project Pattern Detector

Purpose: Cross-project Pattern Detector, category "Portfolio Health". Same registry note.

Source (`portfolio.py`, continuing):

```python
    similar = [v for v in vectors if v["id"] != current_id
               and math.sqrt(sum((v["v"][i] - current_vec[i]) ** 2 for i in range(3))) < 0.15]
    pattern_status = "Green"
    pattern_desc = "No similar distress pattern found in portfolio"
    if similar:
        avg_cpi = sum(v["v"][0] for v in similar) / len(similar)
        pattern_status = "Red" if avg_cpi < 0.90 else "Amber" if avg_cpi < 0.95 else "Yellow"
        pattern_desc = f"{len(similar)} project(s) show similar signal pattern"
    cross_project = {
        "method_class": "Cross_Project_Pattern", "status_color": pattern_status,
        "similar_project_count": len(similar), "evidence_metric": pattern_desc,
    }
```

**Inputs.** Same shared vectors, comparing only the first three components (`cpi`, `spi`,
`docRiskScore` — `range(3)` excludes the fourth component, `actualPctComplete`) of each other
project's vector against the current project's, via plain Euclidean distance (not the
Mahalanobis distance the other modules use).

**Literals:** similarity radius `0.15` (Euclidean distance in the 3-component space) — no comment
on why 0.15, and no comment on why this module switches from Mahalanobis to plain Euclidean
distance while its siblings in the same function use Mahalanobis. Banding on the *average* CPI of
similar projects: `<0.90` Red, `<0.95` Amber, else Yellow (**note: Green is unreachable from this
branch** — the `if similar:` branch can only produce Red/Amber/Yellow; Green is only the
`pattern_status` default when `similar` is empty) — no comment.

**Output / banding.** `similar_project_count`, `status_color` per the above (Green only when no
similar-pattern projects exist at all).

**Abstains** per the shared entry gates only.

---

## Anomaly Score

Purpose: Anomaly Score, category "Portfolio Health". Same registry note.

Source (`portfolio.py`, concluding the function):

```python
    scores = [anomaly_score, 1 - composite_rank, 0.5]
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
```

and the function's assembly of the final `results` dict / return value, which all five modules'
outputs feed into:

```python
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

**Inputs.** Reuses `anomaly_score` (from Isolation Forest, D1.1), `composite_rank` (from Portfolio
Outlier, D1.2), and `trend` (from Signal Trajectory Classifier, D1.3, only if history is
sufficient) — **this module is a composite of the other four modules' intermediate values, not an
independent computation over raw project data.**

**Literals — a fixed three-or-four-element scoring list, with one literal that is not derived
from any project data at all:**
- `0.5` — a constant literal placeholder score, always included regardless of any project's data,
  with no comment on what it represents or why it is fixed at exactly the midpoint.
- `min(1, abs(trend) * 20)` — the ×20 scale converting a CPI-trend-per-period into an anomaly
  contribution, and the `1` cap, both uncommented; this fourth term is included only when history
  is sufficient (`len(history) >= 2 and trend != 0`), so the composite score is computed over
  **either 3 or 4 terms** depending on data availability, with an unweighted mean in both cases
  (no re-weighting to compensate for the varying term count).
- Banding `>=0.70/0.50/0.30` — no comment.

**Output / banding.** `composite_score` (unweighted mean of 3-4 sub-scores, one of which — `0.5`
— is a constant not derived from any project's actual data).

**Abstains** per the shared entry gates only; this module's own arithmetic never abstains
independently once the group-level gates pass (unlike D1.3, which can produce no key at all).
