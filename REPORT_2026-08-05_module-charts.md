# Per-module charts, rebuilt from the stored result

**Date:** 2026-08-05
**Branch:** `claude/module-charts-s5s90m` (merged to `main`, commit `b8043ea`)
**Method:** source-read of `server/app/simulation/*`; a real computed result dumped from `compute_project()` on a rich signalInputs set (the same code path the upload route stores); `getModuleResult()` added to `taxonomy.js`; charts drawn inline in the Signal Ledger by a new dependency-free `module_charts.js`; verified in headless Chromium against the production ledger builder, with fault injection; server suite (fresh DB per file) 2200/2200, `tests.html` 51/51, `tests_render.html` 117/118 (the 1 is the pre-existing auth-gated production-read check, red on `origin/main` too).

---

## THE SPLIT (the most important deliverable)

Each module stores a full result dict in `ComputedResult.module_results` (a JSON column): `status_color`, an `evidence_metric` one-liner, and whatever structured fields that module computed. `_result_view` (documents.py) returns the whole dict to `projectresults`; the detail page grafts it onto `p.storedResult` via `primeAndRefresh` (PR #215), and the Signal Ledger reads that primed row. So the question for each module is **not** "is the number available" (the whole dict is) but **"does what it stored form an honest chart, or would a chart have to fabricate a series the stored result does not hold."**

Sorted against a real computed row (evidence: every field below was read from `compute_project()` output, not guessed from source):

### Group 1 — chartable from the stored result today

The module stored a **labelled, multi-element breakdown it computed itself** (an array of `{name, value}` objects, or a small distribution over named outcomes). Every bar is a stored value read back verbatim. These are honest charts, no derivation.

**Built this pass** (one uniform primitive: a labelled horizontal bar chart):

| Module (name / purpose) | Stored field read | Chart | Bars |
|---|---|---|---|
| Sensitivity Analysis (which inputs move the forecast) | `drivers[].name` / `.sensitivity` | horizontal bars | one per input driver |
| Tornado Risk Ranking (rank the risk drivers) | `risks[].name` / `.impact` | horizontal bars | one per risk |
| Multi-Objective Optimization (how competing objectives score) | `objectives[].name` / `.score` | horizontal bars | one per objective |
| What-If Scenario Matrix (cost under each scenario) | `scenarios[].name` / `.delta_pct` | horizontal bars | one per scenario |
| Decision Sensitivity Matrix (which drivers weigh most) | `sensitivity_matrix[].driver` / `.pct` | horizontal bars | one per driver |
| Regret Minimization Index (regret of each action) | `expected_regret{action: value}` | horizontal bars | one per candidate action |
| Maximum Entropy (spread across outcome bands) | `probabilities{band: value}` | horizontal bars | one per outcome band |

**Chartable today from the stored result but NOT built this pass**, because each needs its own chart primitive and building three more primitives is gold-plating a one-primitive deliverable. Flagged so the owner can decide, not blocked by data:

| Module | Stored field | Would need |
|---|---|---|
| Reference Class Forecasting | `multipliers` (ordered array of 9 empirical cost multipliers) | an ordered distribution strip with the stored p50/p80 markers |
| DSM Rework Propagation | `matrix` (3x3 dependency-structure matrix) | a small heatmap |
| Possibility Theory | `possibility` + `necessity` (two dicts over 3 bands) | grouped/paired bars |

(Hesitant Fuzzy Sets stores a `memberships` array too, but it is three unlabelled degrees that sit at 0.0 across healthy and distressed inputs alike — degenerate, not worth a chart.)

### Group 2 — chartable only if the server stores more

The module **computes a distribution or a trend and then throws it away, storing only a summary**. A chart here would have to invent the shape between the stored points, which is the exact D1 defect the analytical layer removed. These are genuinely chartable **once the server writes the series**; that is a `server/app/...` change and is out of this task's scope.

| Module | Stores today | Would need stored (server change) |
|---|---|---|
| Monte Carlo EAC | `p50_eac`, `p80_eac`, overrun percentages | the EAC percentile ladder or histogram bins from its 5,000 iterations |
| PERT Network Criticality | `p50`, `p80`, `baseline` days | the finish-time distribution from its 2,000 runs |
| Schedule Risk Analysis P80 | `p50_delay`, `p80_delay` | the delay distribution |
| Cost Risk Analysis P80 | `p80_eac`, delta | the cost distribution |
| CUSUM Anomaly Monitor | `max_stat`, `H`, `breached` | the per-period cumulative-sum series (a control chart) |
| Kalman Filter, ARIMA Forecast, Regression to Mean, Earned Schedule | one smoothed/forecast endpoint | the per-period smoothed/forecast series (a trend line) |

Also here, unchanged from `REPORT_2026-08-05_charts-from-stored.md`: the **cross-period trend / trajectory classifier (D1.3)** abstains correctly because `documents.py` passes `history=None`; closing it needs real history threaded server-side, not a front-end change.

### Group 3 — not chartable

A single scalar, a verdict, or several heterogeneous readouts of **different units** that share no common axis. A one-bar bar chart, or bars mixing a ratio with a day-count with a percentage, would manufacture the appearance of a comparable set. These modules keep their status pill and one-line finding and draw no chart. This is most of the taxonomy, e.g.: TCPI, Variance at Completion, ICE Ratio, Budget Execution Rate, Bayesian EAC, Critical Path Index, Labor Productivity, Parametric Cost, Dispute Escalation, Procurement Lead Time, most fuzzy-set scores (Pythagorean, Spherical, Fermatean, MARCOS, CRITIC-TOPSIS, Hypersoft), the reporting-threshold checks (OMB A-11, EVM Reporting Threshold, FAR Threshold), Pareto Frontier, and the Data & Evidence Health completeness scores. Modules that store several scalars (RFI Velocity's eight counts, CCPM Buffer Health's mixed percentages) are readouts, not plottable sets, and are here too: forcing their differing units onto one axis would mislead.

---

## What Group 1 turned out to be, and how each chart reads the stored row

Group 1, built: **seven modules**, all rendered by one honest primitive. Because the seven differ only in which stored field holds the breakdown, a single labelled-horizontal-bar renderer covers them all, keeping the code small and the behaviour identical across modules.

- **`taxonomy.js`** gains `getModuleResult(methodClass, project)`, the sibling of the existing `getModuleStatus`: it looks the module up in `rowFor(project).module_results` by its stored `module_id` and returns the **whole stored dict**, or `null` when there is no row or no entry for that module (an abstaining or insufficient-data module). It reads the primed row and derives nothing.
- **`module_charts.js`** (new, no dependency, inline SVG like every other chart on the platform) turns one stored dict into a spec of `{label, value}` bars, but **only** for the seven charted method classes and **only** when the labelled field is present with at least two elements. A bar whose value is not finite is dropped, never drawn as zero, so an absent figure never reads as a measured one. It refuses to draw a one-bar chart.
- **`app.js`** `categoryLedgerHtml` appends `LinModuleCharts.chartHtmlFor(m.method_class, p)` beneath each module row, so the chart sits **inline with its module** in the Signal Ledger: a reader sees the module's finding and its working together. An abstaining module returns `""` (no chart); a sector-N/A module is skipped.
- **Awaiting state:** unchanged and honoured. `renderLedger` already replaces the whole ledger with the awaiting panel when `LinResults.hasResult(p)` is false, so an uncomputed project shows the awaiting state and **no chart** rather than an empty frame.
- **Nothing recomputes.** The charts read `module_results` only. `deepdive.js` / `sim.js` / `simulations.js` are not loaded by `index.html` (confirmed), and `module_charts.js` calls no model, only `getModuleResult`.

**Naming.** No module id or number appears in any title, axis, label, or note. Bars are labelled by the descriptive names the module stored (driver names, action names, outcome bands). No em dashes.

---

## Verification

Every check was proven able to fail.

- **`tests_render.html` group 14** (new, 11 checks) renders the **production ledger builder** `LinApp.renderLedger` — the same call `detail.js` makes into its `d-ledger` panel — against a stored-row fixture holding a Regret Minimization result (`expected_regret {monitor:11, investigate:5, escalate:8}`) and a Maximum Entropy result, with Sensitivity Analysis deliberately absent so it abstains. It asserts: the charted module drew a chart; the three rendered bar value texts are **exactly** `11,5,8`; bars are labelled `Escalate|Investigate|Monitor` with no ids; no chart leaf carries a module or category id (anchored `[A-D]\d(\.\d+)?` scan over leaf elements, not `textContent`); the abstaining module drew **no** chart; a second charted module also drew; a project with no stored result renders the awaiting state and **no** chart.
- **Fault injection**, each confirmed red then reverted to green (full headless run each time): (1) `valTxt = round(val*100)/100 + 1` (fabricate values) drove the exact-value check red (`116/118`, got `12,6,9`); reverted to `117/118`. (2) `if (!r) r = { drivers:[…] }` (fabricate a chart for an abstaining module) drove the abstention check red (`116/118`); reverted to `117/118`. Faults target **block** `.mchart-value` / `.mchart` elements and **anchored** matches.
- **Server suite:** 39 suites, **2200/2200**, fresh SQLite DB per file. No server file changed.
- **`tests.html`:** **51/51**.

---

## Files changed

`assets/js/taxonomy.js` (added `getModuleResult`), `assets/js/module_charts.js` (new), `assets/js/app.js` (`categoryLedgerHtml` appends the chart), `assets/css/radar.css` (`.mchart*` styles), `index.html` (loads `module_charts.js`), `tests_render.html` (group 14), `T6_HANDOFF.md`. No `server/` change; nothing under `server/app/simulation/` touched.

---

**Summary of outcome:** Group one was non-empty and cleanly buildable (seven modules, one honest primitive), so per the task I built, verified, and merged it to `main`. The three-way split is the lead finding: 7 built + 3 deferred-by-primitive in group 1; a well-defined group 2 whose closure needs the server to store the distribution/trend series it currently discards; and group 3 (most of the taxonomy) correctly left chartless rather than faked. All suites green on the merged result except the one pre-existing auth-gated `tests_render.html` red that is also red on main.
