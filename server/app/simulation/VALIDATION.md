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

> ## D1: TWELVE MODULES NOW DIVERGE FROM THE JAVASCRIPT, DELIBERATELY
>
> **For A1.2, B2.1, B2.2, B2.3, B2.4, B2.5, B2.6, B2.7, B2.8, B2.9, C1.4 and C1.7 the rows below
> record a comparison that no longer describes what this server does.** The rows are kept, not
> corrected in place: what was matched is part of the record, and deleting it would hide that the
> divergence was chosen rather than drifted into. Each row carries a `D1:` note saying what
> changed, and the section "D1 divergence: the fabricated no-evidence verdicts" below says why.
>
> **A matched row does not establish that a module is correct.** It establishes that this server
> computes what the JavaScript computed. These twelve matched exactly on their no-signal cases,
> and that is precisely the problem: the behaviour they matched was a browser edge case which,
> server-side, was the only path any of them ever took.

| new id | name | source | validated | max rel. divergence | notes |
|---|---|---|---|---|---|
| A1.1 | Monte Carlo EAC | sim.js | **yes** | 0.0e+00 | exact match; batch 1 |
| A1.2 | CUSUM Anomaly Monitor | sim.js | **yes** | 0.0e+00 | exact match; batch 1 — **D1: DIVERGES.** Was: synthesised a 12-point series from the current SPI whenever `spiHistory` was absent, which server-side was every project, and drew a control chart over it. Is: abstains below 2 real periods, and reads the `spiHistory` documents.py now assembles from earlier periods. `derive_series` and `hash_seed` are deleted. |
| A2.1 | PERT Network Criticality | simulations.js | **yes** | 0.0e+00 | exact match |
| A2.2 | Line of Balance | simulations.js | **yes** | 0.0e+00 | exact match |
| A2.3 | CCPM Buffer Health | simulations.js | **yes** | 0.0e+00 | exact match |
| A3.1 | Reference Class Forecasting | simulations.js | **yes** | 0.0e+00 | exact match |
| A5.1 | DSM Rework Propagation | simulations.js | **yes** | 0.0e+00 | exact match |
| A1.3 | Bayesian EAC | simulations.js | **yes** | 0.0e+00 | exact match; batch 3; cpi exactly 1 or 0 abstains where the JS NaN/Infinity fallthrough conjures a Red — see the divergence note below |
| A1.4 | Kalman Filter SPI Smoother | simulations.js | **yes** | 0.0e+00 | exact match; batch 3; abstains below 2 periods of spiHistory, validated including the `[si.spi]` single-period fallback and the empty-array arm |
| A1.5 | ARIMA CPI Forecast | simulations.js | **yes** | 0.0e+00 | exact match; batch 3; abstains below 3 periods of cpiHistory |
| A1.6 | Earned Schedule | simulations.js | **yes** | 0.0e+00 | exact match; batch 3; JS `!SPI_t` treats 0% actual progress as insufficient, reproduced |
| A1.7 | TCPI | simulations.js | **yes** | 0.0e+00 | exact match; batch 3; includes the budget-exhausted Red with `tcpi: null` |
| A1.8 | Variance at Completion | simulations.js | **yes** | 0.0e+00 | exact match; batch 3; cpi 0 abstains (JS Infinity) |
| A1.9 | Budget Execution Rate | simulations.js | **yes** | 0.0e+00 | exact match; batch 3; JS `!executionRate` treats ac=0 as insufficient, reproduced |
| A1.10 | Regression to Mean CPI | simulations.js | **yes** | 0.0e+00 | exact match; batch 3; abstains below 2 periods of cpiHistory |
| A1.11 | ICE Ratio | simulations.js | **yes** | 0.0e+00 | exact match; batch 3; cpi 0 abstains (JS Infinity) |
| A2.4 | Schedule Compression Index | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A2.5 | Float Consumption Rate | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A2.6 | S-Curve Deviation | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A2.7 | Milestone Trend Analysis | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A2.8 | Look-Ahead Schedule Health | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A2.9 | Resource Loading Index | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A2.10 | Schedule Risk Analysis P80 | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A2.11 | Critical Path Index | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A3.2 | Contingency Burn Rate | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A3.3 | Labor Productivity Index | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A3.4 | Material Cost Variance | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A3.5 | Overhead Absorption Rate | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A3.6 | Cost Risk Analysis P80 | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A3.7 | Analogous Estimating Ratio | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A3.8 | Parametric Cost Index | simulations.js | **yes** | 0.0e+00 | exact match; batch 2; the JS divides by an unlisted `si.cpi` — a missing/zero cpi yields NaN there and routes to insufficient; the port refuses those explicitly |
| A3.9 | Inflation Adjustment Index | simulations.js | **yes** | 0.0e+00 | exact match; batch 2 |
| A4.1 | Document Risk Score | signals.js | no | - | not ported: produced by the extraction pipeline, not a model |
| A4.2 | RFI Velocity | simulations.js | **yes** | 0.0e+00 | exact match; batch 4; both the RFI-log path and the rfiNumber fallback validated, worst-of velocity/overdue banding |
| A4.3 | Submittal Rejection Rate | simulations.js | **yes** | 0.0e+00 | exact match; batch 4; RFA-log path and submittal-register fallback both validated |
| A4.4 | NCR Rate | simulations.js | **yes** | 0.0e+00 | exact match; batch 4; includes the zero-issued Green special case |
| A4.5 | Weather Day Impact | simulations.js | **yes** | 0.0e+00 | exact match; batch 4; Green iff exactly 0 days lost, reproduced |
| A4.6 | Change Order Frequency | simulations.js | **yes** | 0.0e+00 | exact match; batch 4 |
| A4.7 | Dispute Escalation Index | simulations.js | **yes** | 0.0e+00 | exact match; batch 4; JS-truthy rfiCount/changeOrderCount contributions reproduced |
| A4.8 | Subcontractor Performance | simulations.js | **yes** | 0.0e+00 | exact match; batch 4; the browser's lazy deriveExtendedFields safety net is NOT ported — the extraction pipeline supplies subcontractorComplianceScore or the module abstains; compared against the JS with signals.js absent, i.e. identical semantics |
| A4.9 | Procurement Lead Time Monitor | simulations.js | **yes** | 0.0e+00 | exact match; batch 4 |
| A4.10 | Specification Conflict Density | simulations.js | **yes** | 0.0e+00 | exact match; batch 4 |
| A5.2 | Sensitivity Analysis | simulations.js | **yes** | 0.0e+00 | exact match; batch 5; cpi exactly 0 or ±0.05 abstains (JS division-by-zero fallthrough); descending sort of drivers is stable in both languages |
| A5.3 | Tornado Risk Ranking | simulations.js | **yes** | 0.0e+00 | exact match; batch 5; stable descending sort of the four risks |
| A5.4 | Scenario Modeling | simulations.js | **yes** | 0.0e+00 | exact match on every case except the edge case, where the port abstains and the JS emits a Red with `pessimistic_eac: null` and "worst $Infinityk" — the min(cpi, spi)=0 Infinity fallthrough, refused per the standing rule; recorded in the batch-3 divergence note |
| A5.5 | Rework Feedback Loop | simulations.js | **yes** | 0.0e+00 | exact match; batch 5; JS-truthy rfiCount/changeOrderCount contributions reproduced |
| A5.6 | Queueing Theory Bottleneck | simulations.js | **yes** | 0.0e+00 | exact match; batch 5 |
| A5.7 | Agent-Based Supply Chain | simulations.js | **yes** | 0.0e+00 | exact match; batch 5 |
| A5.8 | Discrete Event Simulation | simulations.js | **yes** | 0.0e+00 | exact match; batch 5 |
| A6.1 | Quality Compliance Index | simulations.js | **yes** | 0.0e+00 | exact match; batch 5; audit-score fallback to pass rate and the default 20-inspected validated |
| A6.2 | Safety Performance Index | simulations.js | **yes** | 0.0e+00 | exact match; batch 5; OSHA-rate fallback to incidents×10 validated |
| A6.3 | Environmental Compliance Rate | simulations.js | **yes** | 0.0e+00 | exact match; batch 5; max(50, …) fallback floor validated |
| A6.4 | Contractor Performance Score | simulations.js | **yes** | 0.0e+00 | exact match; batch 5; worst-of-three rating |
| B1.1 | Conservative Dominance | decision.js | **yes** | 0.0e+00 | exact match; batch 10; a projection of deriveDecision(project) — records {state, conflict} (the instrument's m09_conservative); consumes the ASSEMBLED PROJECT (signals.{evm,mc,cusum,doc}.status + cusum.breached + fairnessSensitive); classifyConflict compares statuses in LOWERCASE, so capitalized statuses do not count — reproduced and case-covered; the browser getProjectFusion primary path is signals.js-only, so the server (like the harness) uses the signal-class fallback rule; a project with no cusum signal THROWS in JS — the port abstains instead (refusing direction) |
| B1.2 | Weighted Voting | simulations.js | **yes** | 0.0e+00 | exact match; batch 6; consumes the ASSEMBLED PROJECT (see input-contract note below); Object.keys reduce in insertion order, later key wins ties |
| B1.3 | Majority Rules | simulations.js | **yes** | 0.0e+00 | exact match; batch 6; project input; voteBucket quirks validated (light-amber→Green, Red-Review→Red, Complete→Green) |
| B1.4 | Worst-N-of-M | simulations.js | **yes** | 0.0e+00 | exact match; batch 6; project input; null statuses from present signals count toward M |
| B2.1 | Dempster-Shafer | simulations.js | **yes** | 0.0e+00 | exact match; batch 6; runDST is defined but not wired into runAll in the JS — validated by calling it directly, per the browser harness; consumes assembled signal keys (evm/mc/cusum/doc/decision) from si; the present-doc-with-undefined-score → Red-branch quirk and the JS empty-object-truthiness of mc/cusum/doc are both reproduced and covered by the edge case — **D1: DIVERGES.** Was: with no signal present, combined three vacuous {0.25×4} masses with the doc arm's absent-doc-reads-as-score-0 Green and returned Green on every project. Is: abstains when evm, mc, cusum and doc are all absent. |
| B2.2 | Rough Sets | simulations.js | **yes** | 0.0e+00 | exact match; batch 7; assembled-signal input (evm/mc/cusum/doc) — **D1: DIVERGES.** Was: `total = len(classes) or 1` divided an empty evidence set by a fictitious one and returned Indeterminate Amber. Is: abstains when no signal classifies. |
| B2.3 | Neutrosophic Logic | simulations.js | **yes** | 0.0e+00 | exact match; batch 7; no-signal case emits the AMBER stub the JS emits, not an abstention — **D1: DIVERGES.** Was: the AMBER "Insufficient signal data" stub, carrying a status colour. Is: abstains. |
| B2.4 | Interval Fuzzy Sets | simulations.js | **yes** | 0.0e+00 | exact match; batch 7; AMBER stub on no signal — **D1: DIVERGES.** Was: the AMBER "Insufficient signal data" stub. Is: abstains. |
| B2.5 | Z-numbers | simulations.js | **yes** | 0.0e+00 | exact match; batch 7; AMBER stub on no signal — **D1: DIVERGES.** Was: the AMBER "Insufficient signal data" stub. Is: abstains. |
| B2.6 | PLTS | simulations.js | **yes** | 0.0e+00 | exact match; batch 7; AMBER stub on no signal — **D1: DIVERGES.** Was: the AMBER "Insufficient signal data" stub. Is: abstains. |
| B2.7 | Plithogenic Sets | simulations.js | **yes** | 0.0e+00 | exact match; batch 7; AMBER stub on no signal — **D1: DIVERGES.** Was: the AMBER "Insufficient signal data" stub. Is: abstains. |
| B2.8 | Belief Rule Base | simulations.js | **yes** | 0.0e+00 | exact match; batch 7; always computes (fallback rule R0 when nothing matches) — **D1: DIVERGES.** Was: fallback rule R0 fired when no EVM state existed, supplying a near-uniform belief mass and a colour drawn from it. Is: abstains when no rule activates; R0 is deleted. |
| B2.9 | Quantum Probability | simulations.js | **yes** | 0.0e+00 | exact match; batch 7; always computes (default amplitudes when signals missing) — **D1: DIVERGES.** Was: defaulted to evm_min 1.0, no breach and doc score 0 (three pieces of good news) and returned Green. Is: abstains when evm, cusum and doc are all absent. |
| B2.10 | Pythagorean Fuzzy Sets | simulations.js | **yes** | 0.0e+00 | exact match; batch 8 |
| B2.11 | Picture Fuzzy Sets | simulations.js | **yes** | 0.0e+00 | exact match; batch 8 |
| B2.12 | Hesitant Fuzzy Sets | simulations.js | **yes** | 0.0e+00 | exact match; batch 8 |
| B2.13 | Type-2 Fuzzy Sets | simulations.js | **yes** | 0.0e+00 | exact match; batch 8 |
| B2.14 | Maximum Entropy | simulations.js | **yes** | 0.0e+00 | exact match; batch 8 |
| B2.15 | Possibility Theory | simulations.js | **yes** | 0.0e+00 | exact match; batch 8 |
| B2.16 | Spherical Fuzzy Sets | simulations.js | **yes** | 0.0e+00 | exact match; batch 8 |
| B2.17 | Fermatean Fuzzy Sets | simulations.js | **yes** | 0.0e+00 | exact match; batch 8 |
| B2.18 | MARCOS Ranking | simulations.js | **yes** | 0.0e+00 | exact match; batch 8 |
| B2.19 | CRITIC-TOPSIS | simulations.js | **yes** | 0.0e+00 | exact match; batch 8 |
| B2.20 | Hypersoft Sets | simulations.js | **yes** | 0.0e+00 | exact match; batch 8 |
| B3.1 | ABM Governance Layer | decision.js | **yes** | 0.0e+00 | exact match; batch 10; the second projection of the same deriveDecision — records {state, authority, action, fairness_gate} (m19_abm); all six deriveDecision fields compared on 8 project cases including the fairness-gate escalation and the capitalized-status quirk |
| B3.2 | FAR Threshold Monitor | simulations.js | **yes** | 0.0e+00 | exact match; batch 6; cpi/bac exactly 0 abstains (JS Infinity/NaN fallthrough) |
| B3.3 | OMB A-11 Check | simulations.js | **yes** | 0.0e+00 | exact match; batch 6; cpi exactly 0 abstains |
| B3.4 | EVM Reporting Threshold | simulations.js | **yes** | 0.0e+00 | exact match; batch 6; cpi/bac exactly 0 abstains |
| B3.5 | Contract Modification Frequency | simulations.js | **yes** | 0.0e+00 | exact match; batch 6 |
| B4.1 | Multi-Objective Optimization | simulations.js | **yes** | 0.0e+00 | exact match; batch 7; stable ascending sort of objectives |
| B4.2 | Linear Programming | simulations.js | **yes** | 0.0e+00 | exact match; batch 7; budget-exhausted Red special case; required-CPI of exactly 0 yields lp_score 1 via the JS Infinity limit, reproduced not refused |
| B4.3 | Constraint Satisfaction Analysis | simulations.js | **yes** | 0.0e+00 | exact match; batch 7 |
| B4.4 | What-If Scenario Matrix | simulations.js | **yes** | 0.0e+00 | exact match; batch 7; cpi/bac exactly 0 abstains (JS Infinity/NaN fallthrough) |
| B4.5 | Decision Sensitivity Matrix | simulations.js | **yes** | 0.0e+00 | exact match; batch 7; `total || 1` zero-impact fallback reproduced |
| B4.6 | Pareto Frontier Analysis | simulations.js | **yes** | 0.0e+00 | exact match; batch 7 |
| B4.7 | Minimax Regret Decision Rule | simulations.js | **yes** | 0.0e+00 | exact match; batch 7; expected-regret Object.keys order preserved (monitor, investigate, escalate) |
| C1.1 | Missing Data Index | simulations.js | **yes** | 0.0e+00 | exact match; batch 9; always computes (a completeness meter, not a signal) |
| C1.2 | Data Timeliness Score | simulations.js | **yes** | 0.0e+00 | exact match; batch 9; the known wall-clock offender — the port takes period_cutoff as its reference date instead of `new Date()`; validated against the JS with the browser Date constructor frozen to the cutoff (see the clock note below) |
| C1.3 | Source Reliability Weighting | simulations.js | **yes** | 0.0e+00 | exact match; batch 9; array-form sources use the LAST entry's docType; unknown types weight 0.50 |
| C1.4 | Audit Trail Completeness | simulations.js | **yes** | 0.0e+00 | exact match; batch 9; events ride on si["events"]; simulation_run counts as extraction evidence — **D1: DIVERGES, and is now WIRED.** Was: `si["events"]` was never supplied, so it reported "0 events recorded" and a Red band on every project. Is: documents.py supplies the project's event log truncated at the period cutoff; an ABSENT log abstains, an EMPTY log is evidence and is reported. |
| C1.5 | Information Completeness Ratio | simulations.js | **yes** | 0.0e+00 | exact match; batch 9 |
| C1.6 | Cross-document Consistency Score | simulations.js | **yes** | 0.0e+00 | exact match; batch 9; three derivation checks at thresholds 0.005/0.005/5 |
| C1.7 | Reporting Frequency Index | simulations.js | **yes** | 0.0e+00 | exact match; batch 9; below 2 extraction events emits the Yellow stub the JS emits, not an abstention — **D1: DIVERGES, and is now WIRED.** Was: the Yellow "upload more documents" stub below 2 extraction events, on every project. Is: computes the real interval from the supplied log and abstains below 2 events. `at` is narrowed to its date part at the boundary, because `_js_date_ms` refuses datetime strings by design. |
| D1.1 | Isolation Forest | Apps Script portfolioanalyze | **yes** | 0.0e+00 | exact match vs the LIVE deployment; batch 11; computed only via compute_portfolio — the single-project path still raises PortfolioModuleError |
| D1.2 | Portfolio Outlier Detection | Apps Script portfolioanalyze | **yes** | 0.0e+00 | exact match vs live; batch 11 |
| D1.3 | Signal Trajectory Classifier | Apps Script portfolioanalyze | **yes** | 0.0e+00 | exact match vs live; batch 11; carries its own insufficient_data flag below 2 history periods while still emitting a status, as the Apps Script does |
| D1.4 | Cross-project Pattern Detector | Apps Script portfolioanalyze | **yes** | 0.0e+00 | exact match vs live; batch 11; similarity over the first three vector dimensions, self excluded by id |
| D1.5 | Anomaly Score | Apps Script portfolioanalyze | **yes** | 0.0e+00 | exact match vs live; batch 11; the trend term joins the composite only with 2+ history periods and a nonzero trend |

## Summary

- validated and shipped: **100** (batch 1 added A1.1 and A1.2 from sim.js; batch 2 added
  A2.4–A2.11 and A3.2–A3.9; batch 3 added A1.3–A1.11; batch 4 added A4.2–A4.10, the
  document-derived condition signals; batch 5 added A5.2–A5.8 and A6.1–A6.4; batch 6 added
  B2.1, B1.2–B1.4 and B3.2–B3.5; batch 7 added B4.1–B4.7 and B2.2–B2.9; batch 8 added
  B2.10–B2.20, completing Group B's simulations.js modules; batch 9 added C1.1–C1.7 — Group C
  computes but does not contribute to project status, an exclusion asserted by Guarantee 4 of
  the test suite). Group A is complete except A4.1, which is produced by the extraction
  pipeline, not a model. Batch 10 added B1.1 and B3.1 from decision.js, validated by loading
  decision.js alone in the browser and comparing deriveDecision field-for-field. Batch 11
  added Group D (D1.1–D1.5) via the separate `compute_portfolio` entry point.
- declared but not ported: **1** — A4.1 Document Risk Score, which is produced by the
  document-extraction pipeline (signals.js / backend extraction), not computed by a model.
  It stays refused: asking the analytical layer for it raises MissingModuleError.

## Group D: no longer refused by design (batch 11)

An earlier revision of this file recorded Group D as "refused on a single-project path" as if
that were permanent. That was wrong as a design statement and is corrected here: participants
create projects one at a time — six is a target, not a constraint — so Portfolio Health
computes over whatever projects a participant has created at that moment and is relevant to
the study. What remains true is the ROUTING rule: `compute_project`/`run_module` never reach
Group D (PortfolioModuleError, asserted by Guarantee 5); the entry point is
`compute_portfolio(projects, current_id, history, period_cutoff)`. Fewer than 3 projects with
signal data returns `insufficient_data: true` with an empty result set — correct behaviour,
not an error and not an abstention. One recorded quirk: the Apps Script guard is
`portfolio.length < 2` while its message says "need at least 3 projects", so a 2-project
portfolio DOES compute (confirmed against the live deployment); the port reproduces both the
guard and the message verbatim.

Validation method: Code.gs cannot run in a browser, so the port was compared against the LIVE
Apps Script deployment's read-only `portfolioanalyze` POST action on seven cases (1 project,
2 projects, exactly 3, a clear outlier, a clear non-outlier, a no-signal current project, and
a 3-period history for the trajectory classifier): every compared field exact at 0.0e+00. The
live deployment is v10.29-geocode; the reference source read for the port is
Code_v10.36_editor_head.gs — no behavioural difference between the two was observed for
portfolioAnalyze_ on any case. The Apps Script stamps `timestamp: new Date().toISOString()`;
the port stamps `period_cutoff` instead (no module reads the system clock), and the timestamp
was the one field excluded from comparison.

## Group B input contracts (batch 6)

Three input shapes share the registry's one signature `fn(si, rand, period_cutoff)`:

- **B1.2–B1.4** consume the ASSEMBLED PROJECT: `si["signals"]` ({mc, cusum, doc} each with
  `.status`, {decision} with `.state`) plus `si["simulationSignals"]["signal_array"]`
  (per-module results with `.status_color`). An empty project abstains.
- **B2.1** (and B2.2–B2.9 when they land) consume the assembled signal keys directly from si:
  `si["evm"]` ({cpi, spi}), `si["mc"]` ({p80DeltaPct}), `si["cusum"]` ({breached}),
  `si["doc"]` ({score}), `si["decision"]` ({state}). A present-but-empty object is a PRESENT
  signal, exactly as a truthy `{}` is in JavaScript.
  **D1 amends this contract: when ALL of those keys are absent the module now ABSTAINS**, where
  it used to take the JavaScript's missing-signal branches. Nothing on the server assembles
  those keys and nothing can: they are the browser's `existingSignals`, and the browser no
  longer computes. The sentence this replaces described a contract no caller could satisfy.
- **B2.10–B2.20, B3.x, B4.x** consume flat signalInputs, as Group A does.

## D1 divergence: the fabricated no-evidence verdicts

**What was wrong.** Twelve keys were read by this layer and written by nothing: `evm`, `mc`,
`cusum`, `doc`, `decision`, `signals`, `simulationSignals` and `fairnessSensitive` (the browser's
assembled blob), plus `events`, `spiHistory`, `cpiHistory` and `milestoneHistory`. In the browser
they arrived and the missing-key branch was a rare edge case. On the server the blob never
arrives, so for twelve modules the missing-key branch was the ONLY path that ever executed. Every
project ever computed carried a verdict from an empty evidence set, and the branch was faithful to
the JavaScript in each case, so the exact-match rows above were true and told nobody anything.

**Measured, the fabrications were not neutral.** On the test suite's own HEALTHY fixture the
synthesised CUSUM series reported a breach, which took category A1 to Red and the whole project to
Red: a project running ahead of plan reported as distressed. The evidence-combination stubs pulled
category B2 to Amber regardless of the evidence, making a healthy project's combination look worse
and a distressed project's look better. C1.4 reported a permanent Red about a platform that has
recorded its events, in exactly the shape C1.4 reads, since `_append_event` was written.

**What was done.** Where the platform holds the evidence, the key is now supplied and the module
computes: `events`, `spiHistory` and `cpiHistory` are assembled in `documents.py` (see
`_events_as_of` and `_period_history`), which is outside this package because both are properties
of a project across periods and `assemble_signal_inputs` must stay pure. Where nothing can ever
supply the key, the module abstains through `insufficient()`, the same contract Kalman, ARIMA and
Regression to Mean have always used. No fabrication path is retained behind a flag or for tests.

**`milestoneHistory` is still unsupplied and A2.7 still abstains.** `milestones_json` is requested
from the extraction model for two document types but is not in `ALL_FIELDS`, so it is never merged
into `signalInputs` and no stored result carries it. A2.7 abstained correctly before D1 and needed
no change; supplying it is a merge-layer task, not this one.

**Nothing here reads a later period.** `_period_history` filters on `period < period`, so
recomputing an early period cannot see a later one, and `_events_as_of` truncates the log at the
period cutoff for the same reason C1.2 takes its "now" from the cutoff.

Verified by `server/tools/test_d1_module_inputs.py`: every one of the twelve computes on a
complete input and abstains on the absence of its own key, with nine independent faults injected
to prove those checks can fail.

## Batch 3 divergence note: NaN/Infinity fallthrough refused

Bayesian EAC at cpi exactly 1 divides by a zero likelihood variance; VAC, ICE Ratio and
Bayesian EAC at cpi exactly 0 divide by zero outright. In JavaScript the resulting NaN or
Infinity falls through every status comparison and lands on `Red` with null/NaN metric fields —
a Red conjured from arithmetic breakdown, not from evidence. The port abstains at those exact
values instead, the same refusing direction as the batch-2 malformed-date treatment. A cpi of
exactly 1.0 is a plausible real input, so this divergence is deliberately load-bearing: an
on-budget project must not receive a Red from a division artefact. Every other input, including
the history fallbacks (`spiHistory || [si.spi]`, empty-array truthiness) and the falsy-zero
guards (`!SPI_t`, `!executionRate`), was validated to exact agreement on seven fixture cases.
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

The one known offender was `runDataTimeliness` (C1.2), which computed `days_since_last_doc`
from `new Date()`. **Ported in batch 9 with `period_cutoff` as its only reference date.** To
validate against a fixed target rather than a moving one, the browser harness patched the Date
constructor before loading simulations.js so a no-argument `new Date()` (and `Date.now()`)
returned UTC midnight of the cutoff, leaving Date parsing and arithmetic untouched. With the
clock frozen, the two implementations agreed exactly on every case.

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


## A4.1 Document Risk Score — a discrepancy between the description and the implementation

Recorded during B7b, when the extraction pipeline that produces A4.1 was built. Documentation
only: nothing in this package changed, and no validated module was touched.

A4.1 stays **declared but not ported** here, and asking the analytical layer for it still raises
`MissingModuleError`. That remains correct — it is produced by the extraction pipeline, not by a
model. What B7b established is *what that pipeline actually does*, and it does not match how A4.1
is described elsewhere in the instrument.

- `assets/js/knowledge.js:2429` describes A4.1 as "a transparent keyword-and-pattern score".
- The shipped legacy implementation contains **no keyword rules and no pattern matching**. The
  extraction prompt asks the model to emit a `document_risk_score` field directly, and
  `extractSignals_` (`apps_script/reference/Code_v10.36_editor_head.gs:910-913`, and again at
  `:1061-1063` for `commissioning_report`) copies that number straight through to
  `signalInputs.docRiskScore`. It is a model judgment, not a computed score.

A second, related defect: the legacy prompt never constrained the value's scale, while `sim.js`
clamps `docScore` to [0,1] and bands it at 0.30 / 0.70, and `assets/js/decision.js:80` carries a
standing comment that the field "carries inconsistent scales — raw counts as well". An
unconstrained emission is therefore silently misread as a band.

B7b's port constrains the prompt to 0..1 explicitly (`server/app/extraction_client.py`,
`build_prompt`). The *description* is deliberately left alone: which of the two is authoritative
is a praxis-document decision, not a porting one. It is recorded here so that a reader comparing
the description against the collected data has the discrepancy in front of them rather than
discovering it in the results.
