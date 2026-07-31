# Analytical layer validation

One row per module. A module is shipped only if its output was compared against the JavaScript
implementation on at least three input cases (healthy, distressed, insufficient-data) and matched.
Anything not validated is **not computed**: `registry.run_module` raises `MissingModuleError`
rather than returning an unverified number.

Comparison method: the JavaScript was executed in a headless browser against the repository served
locally, with `Math.random` replaced by the same mulberry32 the Python port uses and the stream
reset before every model and case. That makes the stochastic model exactly comparable rather than
only distributionally similar. Node is not installed on this machine.

Tolerance: numeric fields within 1e-6 relative; `status_color` and categorical fields exact.

| new id | name | source | validated | max rel. divergence | notes |
|---|---|---|---|---|---|
| A1.1 | Monte Carlo EAC | sim.js | **yes** | 0.0e+00 | exact match; batch 1 |
| A1.2 | CUSUM Anomaly Monitor | sim.js | **yes** | 0.0e+00 | exact match; batch 1 |
| A2.1 | PERT Network Criticality | simulations.js | **yes** | 0.0e+00 | exact match |
| A2.2 | Line of Balance | simulations.js | **yes** | 0.0e+00 | exact match |
| A2.3 | CCPM Buffer Health | simulations.js | **yes** | 0.0e+00 | exact match |
| A3.1 | Reference Class Forecasting | simulations.js | **yes** | 0.0e+00 | exact match |
| A5.1 | DSM Rework Propagation | simulations.js | **yes** | 0.0e+00 | exact match |
| A1.3 | Bayesian EAC | simulations.js | no | - | not ported in this pass |
| A1.4 | Kalman Filter SPI Smoother | simulations.js | no | - | not ported in this pass |
| A1.5 | ARIMA CPI Forecast | simulations.js | no | - | not ported in this pass |
| A1.6 | Earned Schedule | simulations.js | no | - | not ported in this pass |
| A1.7 | TCPI | simulations.js | no | - | not ported in this pass |
| A1.8 | Variance at Completion | simulations.js | no | - | not ported in this pass |
| A1.9 | Budget Execution Rate | simulations.js | no | - | not ported in this pass |
| A1.10 | Regression to Mean CPI | simulations.js | no | - | not ported in this pass |
| A1.11 | ICE Ratio | simulations.js | no | - | not ported in this pass |
| A2.4 | Schedule Compression Index | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A2.5 | Float Consumption Rate | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A2.6 | S-Curve Deviation | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A2.7 | Milestone Trend Analysis | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A2.8 | Look-Ahead Schedule Health | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A2.9 | Resource Loading Index | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A2.10 | Schedule Risk Analysis P80 | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A2.11 | Critical Path Index | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A3.2 | Contingency Burn Rate | simulations.js | no | - | not ported in this pass |
| A3.3 | Labor Productivity Index | simulations.js | no | - | not ported in this pass |
| A3.4 | Material Cost Variance | simulations.js | no | - | not ported in this pass |
| A3.5 | Overhead Absorption Rate | simulations.js | no | - | not ported in this pass |
| A3.6 | Cost Risk Analysis P80 | simulations.js | no | - | not ported in this pass |
| A3.7 | Analogous Estimating Ratio | simulations.js | no | - | not ported in this pass |
| A3.8 | Parametric Cost Index | simulations.js | no | - | not ported in this pass |
| A3.9 | Inflation Adjustment Index | simulations.js | no | - | not ported in this pass |
| A4.1 | Document Risk Score | signals.js | no | - | not ported: produced by the extraction pipeline, not a model |
| A4.2 | RFI Velocity | simulations.js | no | - | not ported in this pass |
| A4.3 | Submittal Rejection Rate | simulations.js | no | - | not ported in this pass |
| A4.4 | NCR Rate | simulations.js | no | - | not ported in this pass |
| A4.5 | Weather Day Impact | simulations.js | no | - | not ported in this pass |
| A4.6 | Change Order Frequency | simulations.js | no | - | not ported in this pass |
| A4.7 | Dispute Escalation Index | simulations.js | no | - | not ported in this pass |
| A4.8 | Subcontractor Performance | simulations.js | no | - | not ported in this pass |
| A4.9 | Procurement Lead Time Monitor | simulations.js | no | - | not ported in this pass |
| A4.10 | Specification Conflict Density | simulations.js | no | - | not ported in this pass |
| A5.2 | Sensitivity Analysis | simulations.js | no | - | not ported in this pass |
| A5.3 | Tornado Risk Ranking | simulations.js | no | - | not ported in this pass |
| A5.4 | Scenario Modeling | simulations.js | no | - | not ported in this pass |
| A5.5 | Rework Feedback Loop | simulations.js | no | - | not ported in this pass |
| A5.6 | Queueing Theory Bottleneck | simulations.js | no | - | not ported in this pass |
| A5.7 | Agent-Based Supply Chain | simulations.js | no | - | not ported in this pass |
| A5.8 | Discrete Event Simulation | simulations.js | no | - | not ported in this pass |
| A6.1 | Quality Compliance Index | simulations.js | no | - | not ported in this pass |
| A6.2 | Safety Performance Index | simulations.js | no | - | not ported in this pass |
| A6.3 | Environmental Compliance Rate | simulations.js | no | - | not ported in this pass |
| A6.4 | Contractor Performance Score | simulations.js | no | - | not ported in this pass |
| B1.1 | Conservative Dominance | decision.js | no | - | not ported: computed in decision.js |
| B1.2 | Weighted Voting | simulations.js | no | - | not ported in this pass |
| B1.3 | Majority Rules | simulations.js | no | - | not ported in this pass |
| B1.4 | Worst-N-of-M | simulations.js | no | - | not ported in this pass |
| B2.1 | Dempster-Shafer | simulations.js | no | - | not ported: runDST is defined but not wired into runAll |
| B2.2 | Rough Sets | simulations.js | no | - | not ported in this pass |
| B2.3 | Neutrosophic Logic | simulations.js | no | - | not ported in this pass |
| B2.4 | Interval Fuzzy Sets | simulations.js | no | - | not ported in this pass |
| B2.5 | Z-numbers | simulations.js | no | - | not ported in this pass |
| B2.6 | PLTS | simulations.js | no | - | not ported in this pass |
| B2.7 | Plithogenic Sets | simulations.js | no | - | not ported in this pass |
| B2.8 | Belief Rule Base | simulations.js | no | - | not ported in this pass |
| B2.9 | Quantum Probability | simulations.js | no | - | not ported in this pass |
| B2.10 | Pythagorean Fuzzy Sets | simulations.js | no | - | not ported in this pass |
| B2.11 | Picture Fuzzy Sets | simulations.js | no | - | not ported in this pass |
| B2.12 | Hesitant Fuzzy Sets | simulations.js | no | - | not ported in this pass |
| B2.13 | Type-2 Fuzzy Sets | simulations.js | no | - | not ported in this pass |
| B2.14 | Maximum Entropy | simulations.js | no | - | not ported in this pass |
| B2.15 | Possibility Theory | simulations.js | no | - | not ported in this pass |
| B2.16 | Spherical Fuzzy Sets | simulations.js | no | - | not ported in this pass |
| B2.17 | Fermatean Fuzzy Sets | simulations.js | no | - | not ported in this pass |
| B2.18 | MARCOS Ranking | simulations.js | no | - | not ported in this pass |
| B2.19 | CRITIC-TOPSIS | simulations.js | no | - | not ported in this pass |
| B2.20 | Hypersoft Sets | simulations.js | no | - | not ported in this pass |
| B3.1 | ABM Governance Layer | decision.js | no | - | not ported: computed in decision.js |
| B3.2 | FAR Threshold Monitor | simulations.js | no | - | not ported in this pass |
| B3.3 | OMB A-11 Check | simulations.js | no | - | not ported in this pass |
| B3.4 | EVM Reporting Threshold | simulations.js | no | - | not ported in this pass |
| B3.5 | Contract Modification Frequency | simulations.js | no | - | not ported in this pass |
| B4.1 | Multi-Objective Optimization | simulations.js | no | - | not ported in this pass |
| B4.2 | Linear Programming | simulations.js | no | - | not ported in this pass |
| B4.3 | Constraint Satisfaction Analysis | simulations.js | no | - | not ported in this pass |
| B4.4 | What-If Scenario Matrix | simulations.js | no | - | not ported in this pass |
| B4.5 | Decision Sensitivity Matrix | simulations.js | no | - | not ported in this pass |
| B4.6 | Pareto Frontier Analysis | simulations.js | no | - | not ported in this pass |
| B4.7 | Regret Minimization Index | simulations.js | no | - | not ported in this pass |
| C1.1 | Missing Data Index | simulations.js | no | - | not ported in this pass |
| C1.2 | Data Timeliness Score | simulations.js | no | - | not ported in this pass |
| C1.3 | Source Reliability Weighting | simulations.js | no | - | not ported in this pass |
| C1.4 | Audit Trail Completeness | simulations.js | no | - | not ported in this pass |
| C1.5 | Information Completeness Ratio | simulations.js | no | - | not ported in this pass |
| C1.6 | Cross-document Consistency Score | simulations.js | no | - | not ported in this pass |
| C1.7 | Reporting Frequency Index | simulations.js | no | - | not ported in this pass |
| D1.1 | Isolation Forest | Apps Script portfolioanalyze | no | - | Group D: portfolio-level, requires 3+ projects; refused on a single-project path |
| D1.2 | Portfolio Outlier Detection | Apps Script portfolioanalyze | no | - | Group D: portfolio-level, requires 3+ projects; refused on a single-project path |
| D1.3 | Signal Trajectory Classifier | Apps Script portfolioanalyze | no | - | Group D: portfolio-level, requires 3+ projects; refused on a single-project path |
| D1.4 | Cross-project Pattern Detector | Apps Script portfolioanalyze | no | - | Group D: portfolio-level, requires 3+ projects; refused on a single-project path |
| D1.5 | Anomaly Score | Apps Script portfolioanalyze | no | - | Group D: portfolio-level, requires 3+ projects; refused on a single-project path |

## Summary

- validated and shipped: **15** (batch 1 added A1.1 and A1.2 from sim.js; batch 2 added
  A2.4–A2.11, the simulations.js schedule extensions)
- declared but not ported: **86**
- maximum relative divergence across every validated module and case: **0.0e+00** (exact match)

## Rule: no module reads the system clock

`compute_project`, `run_all` and `run_module` all take a **required** `period_cutoff`, the
reporting period's data cutoff date. Every model receives it; most ignore it. Where a module needs
a notion of "now", it uses the cutoff and nothing else.

It is required rather than optional on purpose. An optional parameter lets a caller omit it, and a
future module then quietly falls back to the wall clock. `tools/test_simulation.py` asserts both
halves: that omitting it raises, and that no file under `app/simulation/` contains
`datetime.now(`, `time.time(`, `date.today(` or `datetime.utcnow(`.

**If you find another clock read while porting, treat it the same way: pass the cutoff, do not
read the clock, and record the finding in the table below.**

The one known offender is `runDataTimeliness` (C1.2), which computes `days_since_last_doc` from
`new Date()`. It is unported pending batch 4 and must take the cutoff when it lands.

## Known non-determinism found in the JavaScript (Stage 1)

| site | function | affects | treatment |
|---|---|---|---|
| `simulations.js:56` | `sampleTriangular` via `runPERT` | **output value** | seeded from `(scenario_id, period)`; seed recorded on the result |
| `simulations.js:2377` | `runDataTimeliness` | **output value** (`days_since_last_doc` and `status_color` both move with the wall clock) | not ported; needs a reference date rather than `new Date()` |
| `sim.js:230` | derived-series builder | `dataDate` field | not ported |
| `decision.js:395` | export payload | presentation only (`exported_at`) | not ported |
| `simulations.js` x11 | `Object.keys` reductions | float accumulation order | insertion order preserved in both languages. **Do not sort these.** Sorting would look like a determinism fix but would silently change results relative to the instrument's own history; the two languages already agree because both preserve insertion order. |
| `simulations.js:1102,1216,1281,2953` | date parsing from `signalInputs` | value, but deterministic given input | timezone-sensitive parsing is a porting hazard to watch. **Batch 2 treatment**: the port parses date-only `YYYY-MM-DD` strings as UTC midnight, exactly as JavaScript does, and refuses (abstains on) anything else. Two deliberate divergences from the JavaScript, both in the refusing direction: a datetime string with a `T` and no zone, which JavaScript parses as *local* time (the confound itself), and a malformed date, where JavaScript's NaN falls through every comparison and lands on `Red` (A2.4/A2.10) — the port abstains rather than reproducing a Red conjured from an unparseable string. Neither input shape occurs in signalInputs; both are recorded here so a validation case that ever hits one is explained. |
| `sim.js:108,213` | `monteCarloEAC`, `deriveSeries` | deterministic already, but scenario-blind | **ported in batch 1**, reseeded from `(scenario_id, period)`. `deriveSeries` seeds via `hashSeed("series-" + seed)` (FNV-1a); skipping that transform produced a different series, sigma, H and breach index, which is how the first validation attempt failed. |

