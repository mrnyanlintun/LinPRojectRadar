# Run 27 — the remediation matrix for every scientific target that is not a pass, the evidence contract behind each one, and the parsimony verdicts

**This run wrote no production code, changed no operational state, activated nothing, removed nothing and consolidated nothing.** It is planning, evidence-contract design and parsimony, exactly as commissioned. Its whole value is making Runs 28 to 33 precise.

## The headline, and the one number that came back different

| Figure | Value | Derived from |
|---|---|---|
| Scientific targets | 100 | row count of `code_audit/run20_cycle12_100_reaudit.csv` |
| Unique target identities | 100 | distinct `code_id` in the same file |
| Current `SCIENTIFIC_PASS` | **3** | rows of that file whose disposition is `SCIENTIFIC_PASS` |
| Requiring further work | **97** | the identity, not a literal |
| Matrix rows written | **97** | row count of the matrix CSV |

**The run was commissioned to build a 98-module matrix. Mechanically derived, the answer is 97.** The prompt's section 1 instructs that the 98 be derived rather than copied from a narrative, and that if the re-audit does not yield exactly two passes the real number be reported rather than forced. It yields three:

- **A1.7 TCPI** — ENABLED_QUALIFIED, voting, lineage `SAME_SOURCE_TRANSFORM`
- **A1.8 Variance at Completion** — ENABLED_QUALIFIED, voting, lineage `SAME_SOURCE_TRANSFORM`
- **B1.1 Conservative Dominance** — ADVISORY_ONLY, non-voting, lineage `UNDECLARED`

The third is **B1.1 Conservative Dominance**, raised to `SCIENTIFIC_PASS` by Run 20 Cycle 9, which found that a module named for a dominance rule was applying a counting rule and replaced it with a genuine maximum over the signal bands. The Run 20 report records the transition explicitly (`| SCIENTIFIC_PASS | 2 | 3 |`). The number 98 in the commissioning prompt is the pre-Cycle-9 figure. Nothing was adjusted to reach 98 and no row was invented to pad the matrix.

**The artifact keeps the commissioned path** `code_audit/run27_98_module_remediation_matrix.csv` so the owner's file reference resolves, and it holds 97 rows. The guard asserts the identity `targets - passes == rows` and never the literal 97 or 98, so a later run that raises a fourth target to pass moves the matrix without breaking the suite.

### Distribution by remediation type

A row carries one or more types. Counts are rows carrying each type, so they exceed 97.

| Type | Rows | What it means here |
|---|---|---|
| `LINEAGE` | 95 | qualification, dependence, source ancestry or double-counting control is required |
| `CAL` | 91 | a parameter, threshold, membership, prior, weight or boundary lacks defensible provenance |
| `DATA` | 88 | a real missing evidence source or canonical data structure |
| `VALIDATE` | 88 | intended-use performance requires a genuine reference or labelled dataset |
| `METHOD` | 60 | the shipped computation is not the required canonical method |
| `PARSIMONY` | 53 | the module may be redundant, misleadingly named, or not justify a separate presence |
| `RESEARCH` | 10 | the method can be implemented scientifically but operational value is unestablished |
| `REG` | 6 | an authoritative rule, version, applicability and evidence object is required |

**`LINEAGE` at 95 of 97 and `CAL` at 91 are near-universal, and that is the finding rather than an inflation of it.** The Category-9 qualification gate is unimplemented platform-wide and production itself discloses it, so almost every module consumes unqualified signals; and no labelled corpus or expert reference standard exists in this repository, so almost no boundary can be calibrated. Two absent structures account for most of the population's exposure. They are not 97 separate problems.

### Evidence posture

| Question | Answer |
|---|---|
| Require a new evidence or data structure | 67 |
| Can be served from evidence the platform already has or already extracts | 29 |
| Rename or truthful-proxy candidates | 40 |
| Consolidation or removal candidates | 16 |
| Research-only candidates | 10 |
| Rows whose remaining work is calibration and validation only | 9 |

Corpus status, per section 6: `ABSENT` 63, `PARTIALLY_PRESENT` 17, `PRESENT` 9, `PRESENT_NOT_EXTRACTED` 8.

---

## 1. The exact list requiring further work

Derived, not copied. Every identity checked against the registry by the guard.

| id | registered name | cat | disposition | primary | pri | run |
|---|---|---|---|---|---|---|
| A1.1 | Monte Carlo EAC | A1 | METHOD_PASS_CALIBRATION_PENDING | DATA | P2 | Run 33 |
| A1.2 | CUSUM Anomaly Monitor | A1 | CORRECT_PROXY_ONLY | DATA | P1 | Run 28 |
| A1.3 | Bayesian EAC | A1 | CORRECT_PROXY_ONLY | DATA | P1 | Run 28 |
| A1.4 | Kalman Filter SPI Smoother | A1 | CORRECT_PROXY_ONLY | DATA | P1 | Run 28 |
| A1.5 | ARIMA CPI Forecast | A1 | CORRECT_PROXY_ONLY | DATA | P1 | Run 28 |
| A1.6 | Earned Schedule | A1 | CORRECT_PROXY_ONLY | DATA | P1 | Run 28 |
| A1.9 | Budget Execution Rate | A1 | CORRECT_PROXY_ONLY | DATA | P2 | Run 28 |
| A1.10 | Regression to Mean CPI | A1 | CORRECT_PROXY_ONLY | DATA | P1 | Run 28 |
| A1.11 | ICE Ratio | A1 | CORRECT_PROXY_ONLY | DATA | P1 | Run 28 |
| A2.1 | PERT Network Criticality | A2 | CORRECT_ABSTENTION | DATA | P1 | Run 28 |
| A2.2 | Line of Balance | A2 | CORRECT_ABSTENTION | DATA | P1 | Run 28 |
| A2.3 | CCPM Buffer Health | A2 | CORRECT_ABSTENTION | DATA | P1 | Run 28 |
| A2.4 | Schedule Compression Index | A2 | CORRECT_PROXY_ONLY | DATA | P1 | Run 28 |
| A2.5 | Float Consumption Rate | A2 | METHOD_PASS_CALIBRATION_PENDING | LINEAGE | P2 | Run 33 |
| A2.6 | S-Curve Deviation | A2 | CORRECT_PROXY_ONLY | DATA | P1 | Run 28 |
| A2.7 | Milestone Trend Analysis | A2 | CORRECT_PROXY_ONLY | DATA | P1 | Run 28 |
| A2.8 | Look-Ahead Schedule Health | A2 | CORRECT_ABSTENTION | LINEAGE | P2 | Run 33 |
| A2.9 | Resource Loading Index | A2 | METHOD_PASS_CALIBRATION_PENDING | LINEAGE | P2 | Run 33 |
| A2.10 | Schedule Risk Analysis P80 | A2 | CORRECT_PROXY_ONLY | DATA | P0 | Run 28 |
| A2.11 | Critical Path Index | A2 | CORRECT_PROXY_ONLY | DATA | P0 | Run 28 |
| A3.1 | Reference Class Forecasting | A3 | CORRECT_ABSTENTION | DATA | P1 | Run 28 |
| A3.2 | Contingency Burn Rate | A3 | CORRECT_ABSTENTION | DATA | P1 | Run 28 |
| A3.3 | Labor Productivity Index | A3 | CORRECT_PROXY_ONLY | DATA | P1 | Run 28 |
| A3.5 | Overhead Absorption Rate | A3 | CORRECT_PROXY_ONLY | DATA | P1 | Run 28 |
| A3.6 | Cost Risk Analysis P80 | A3 | CORRECT_PROXY_ONLY | DATA | P0 | Run 28 |
| A3.7 | Analogous Estimating Ratio | A3 | CORRECT_PROXY_ONLY | DATA | P1 | Run 28 |
| A3.8 | Parametric Cost Index | A3 | FUTURE_RESEARCH_ONLY | DATA | P3 | Run 28 |
| A3.9 | Inflation Adjustment Index | A3 | CORRECT_PROXY_ONLY | DATA | P1 | Run 28 |
| A4.1 | Document Risk Score | A4 | EMPIRICAL_VALIDATION_BLOCKED | DATA | P0 | Run 29 |
| A4.2 | RFI Velocity | A4 | METHOD_PASS_CALIBRATION_PENDING | LINEAGE | P2 | Run 33 |
| A4.3 | Submittal Rejection Rate | A4 | METHOD_PASS_CALIBRATION_PENDING | LINEAGE | P2 | Run 33 |
| A4.4 | NCR Rate | A4 | CORRECT_ABSTENTION | DATA | P1 | Run 29 |
| A4.5 | Weather Day Impact | A4 | CORRECT_PROXY_ONLY | METHOD | P2 | Run 33 |
| A4.6 | Change Order Frequency | A4 | CORRECT_PROXY_ONLY | DATA | P1 | Run 29 |
| A4.7 | Dispute Escalation Index | A4 | CORRECT_PROXY_ONLY | DATA | P1 | Run 29 |
| A4.8 | Subcontractor Performance | A4 | CORRECT_PROXY_ONLY | DATA | P1 | Run 29 |
| A4.9 | Procurement Lead Time Monitor | A4 | METHOD_PASS_CALIBRATION_PENDING | LINEAGE | P2 | Run 33 |
| A4.10 | Specification Conflict Density | A4 | CORRECT_PROXY_ONLY | DATA | P1 | Run 29 |
| A5.1 | DSM Rework Propagation | A5 | CORRECT_ABSTENTION | DATA | P1 | Run 29 |
| A5.2 | Sensitivity Analysis | A5 | CORRECT_PROXY_ONLY | DATA | P1 | Run 29 |
| A5.3 | Tornado Risk Ranking | A5 | CORRECT_PROXY_ONLY | DATA | P1 | Run 29 |
| A5.4 | Scenario Modeling | A5 | CORRECT_ABSTENTION | DATA | P1 | Run 29 |
| A5.5 | Rework Feedback Loop | A5 | CORRECT_PROXY_ONLY | DATA | P1 | Run 29 |
| A5.6 | Queueing Theory Bottleneck | A5 | CORRECT_ABSTENTION | DATA | P1 | Run 29 |
| A5.7 | Agent-Based Supply Chain | A5 | CORRECT_ABSTENTION | DATA | P3 | Run 29 |
| A5.8 | Discrete Event Simulation | A5 | CORRECT_PROXY_ONLY | DATA | P1 | Run 29 |
| A6.1 | Quality Compliance Index | A6 | CORRECT_ABSTENTION | DATA | P0 | Run 31 |
| A6.2 | Safety Performance Index | A6 | CORRECT_ABSTENTION | DATA | P0 | Run 31 |
| A6.3 | Environmental Compliance Rate | A6 | REGULATORY_VERSION_BLOCKED | DATA | P0 | Run 31 |
| A6.4 | Contractor Performance Score | A6 | CORRECT_PROXY_ONLY | DATA | P1 | Run 31 |
| B1.2 | Weighted Voting | B1 | CORRECT_PROXY_ONLY | DATA | P0 | Run 30 |
| B1.3 | Majority Rules | B1 | METHOD_PASS_CALIBRATION_PENDING | DATA | P0 | Run 30 |
| B1.4 | Worst-N-of-M | B1 | PARAMETER_PROVENANCE_BLOCKED | DATA | P0 | Run 30 |
| B2.1 | Dempster-Shafer | B2 | METHOD_PASS_CALIBRATION_PENDING | DATA | P1 | Run 30 |
| B2.2 | Rough Sets | B2 | CORRECT_PROXY_ONLY | DATA | P1 | Run 30 |
| B2.3 | Neutrosophic Logic | B2 | METHOD_PASS_CALIBRATION_PENDING | DATA | P1 | Run 30 |
| B2.4 | Interval Fuzzy Sets | B2 | METHOD_PASS_CALIBRATION_PENDING | DATA | P1 | Run 30 |
| B2.5 | Z-numbers | B2 | METHOD_PASS_CALIBRATION_PENDING | DATA | P1 | Run 30 |
| B2.6 | PLTS | B2 | METHOD_PASS_CALIBRATION_PENDING | DATA | P1 | Run 30 |
| B2.7 | Plithogenic Sets | B2 | FUTURE_RESEARCH_ONLY | DATA | P3 | Run 30 |
| B2.8 | Belief Rule Base | B2 | METHOD_PASS_CALIBRATION_PENDING | DATA | P1 | Run 30 |
| B2.9 | Quantum Probability | B2 | FUTURE_RESEARCH_ONLY | DATA | P3 | Run 30 |
| B2.10 | Pythagorean Fuzzy Sets | B2 | CORRECT_PROXY_ONLY | DATA | P1 | Run 30 |
| B2.11 | Picture Fuzzy Sets | B2 | CORRECT_PROXY_ONLY | DATA | P1 | Run 30 |
| B2.12 | Hesitant Fuzzy Sets | B2 | CORRECT_PROXY_ONLY | DATA | P1 | Run 30 |
| B2.13 | Type-2 Fuzzy Sets | B2 | CORRECT_PROXY_ONLY | DATA | P1 | Run 30 |
| B2.14 | Maximum Entropy | B2 | CORRECT_PROXY_ONLY | DATA | P1 | Run 30 |
| B2.15 | Possibility Theory | B2 | CORRECT_PROXY_ONLY | DATA | P1 | Run 30 |
| B2.16 | Spherical Fuzzy Sets | B2 | CORRECT_PROXY_ONLY | DATA | P1 | Run 30 |
| B2.17 | Fermatean Fuzzy Sets | B2 | CORRECT_PROXY_ONLY | DATA | P1 | Run 30 |
| B2.18 | MARCOS Ranking | B2 | OWNER_DECISION_REQUIRED | DATA | P1 | Run 30 |
| B2.19 | CRITIC-TOPSIS | B2 | CORRECT_ABSTENTION | DATA | P1 | Run 30 |
| B2.20 | Hypersoft Sets | B2 | FUTURE_RESEARCH_ONLY | DATA | P3 | Run 30 |
| B3.1 | ABM Governance Layer | B3 | CORRECT_PROXY_ONLY | DATA | P0 | Run 31 |
| B3.2 | FAR Threshold Monitor | B3 | METHOD_PASS_CALIBRATION_PENDING | DATA | P1 | Run 31 |
| B3.3 | OMB A-11 Check | B3 | METHOD_PASS_CALIBRATION_PENDING | DATA | P1 | Run 31 |
| B3.4 | EVM Reporting Threshold | B3 | METHOD_PASS_CALIBRATION_PENDING | DATA | P1 | Run 31 |
| B3.5 | Contract Modification Frequency | B3 | CORRECT_PROXY_ONLY | DATA | P1 | Run 31 |
| B4.1 | Multi-Objective Optimization | B4 | FUTURE_RESEARCH_ONLY | DATA | P3 | Run 32 |
| B4.2 | Linear Programming | B4 | FUTURE_RESEARCH_ONLY | DATA | P3 | Run 32 |
| B4.3 | Constraint Satisfaction Analysis | B4 | CORRECT_PROXY_ONLY | DATA | P1 | Run 32 |
| B4.4 | What-If Scenario Matrix | B4 | CORRECT_PROXY_ONLY | DATA | P1 | Run 32 |
| B4.5 | Decision Sensitivity Matrix | B4 | FUTURE_RESEARCH_ONLY | DATA | P3 | Run 32 |
| B4.6 | Pareto Frontier Analysis | B4 | FUTURE_RESEARCH_ONLY | DATA | P3 | Run 32 |
| B4.7 | Regret Minimization Index | B4 | CORRECT_ABSTENTION | DATA | P1 | Run 32 |
| C1.1 | Missing Data Index | C1 | METHOD_PASS_CALIBRATION_PENDING | LINEAGE | P2 | Run 33 |
| C1.2 | Data Timeliness Score | C1 | METHOD_PASS_CALIBRATION_PENDING | DATA | P1 | Run 31 |
| C1.3 | Source Reliability Weighting | C1 | METHOD_PASS_CALIBRATION_PENDING | DATA | P1 | Run 31 |
| C1.4 | Audit Trail Completeness | C1 | OWNER_DECISION_REQUIRED | DATA | P1 | Run 31 |
| C1.5 | Information Completeness Ratio | C1 | METHOD_PASS_CALIBRATION_PENDING | LINEAGE | P2 | Run 33 |
| C1.6 | Cross-document Consistency Score | C1 | CORRECT_PROXY_ONLY | DATA | P0 | Run 31 |
| C1.7 | Reporting Frequency Index | C1 | CORRECT_ABSTENTION | DATA | P1 | Run 31 |
| D1.1 | Isolation Forest | D1 | METHOD_PASS_CALIBRATION_PENDING | DATA | P2 | Run 32 |
| D1.2 | Portfolio Outlier Detection | D1 | CORRECT_PROXY_ONLY | DATA | P1 | Run 32 |
| D1.3 | Signal Trajectory Classifier | D1 | METHOD_PASS_CALIBRATION_PENDING | DATA | P2 | Run 32 |
| D1.4 | Cross-project Pattern Detector | D1 | METHOD_PASS_CALIBRATION_PENDING | DATA | P2 | Run 32 |
| D1.5 | Anomaly Score | D1 | THRESHOLD_CALIBRATION_BLOCKED | DATA | P0 | Run 32 |

**A3.4 Material Cost Variance is deliberately absent.** It is registered and disabled pending an evidence-design decision, and the scientific-audit population excluded it, so it is not one of the hundred targets and cannot be one of the ninety-seven. The contract and procurement baseline package below is nevertheless the evidence design it was disabled pending, and the owner's deferred retain-or-remove decision on it depends on that package.

## 2. The complete remediation matrix

`code_audit/run27_98_module_remediation_matrix.csv`, 97 rows, 42 columns. Every mechanical column is read at build time from the registry, the Cycle-12 re-audit, `method_labels.py`, `parameters.py`, `registry.py` and the authoritative edge list; only the evidence contract is authored, in `server/tools/run27_curation.py`. A rename in the registry or a disposition change in the re-audit moves the matrix without anyone editing it.

Columns: `canonical_id`, `current_registered_name`, `category`, `category_name`, `group`, `scope`, `current_operational_status`, `voting_status`, `current_scientific_disposition`, `actual_computation_currently_implemented`, `canonical_method_required`, `primary_remediation_type`, `secondary_remediation_types`, `exact_missing_evidence`, `exact_missing_data_structure`, `existing_source_document_availability`, `existing_structured_fields_available`, `new_document_or_form_needed`, `new_structured_form_needed`, `new_database_or_data_contract_structure_needed`, `historical_series_needed`, `external_or_reference_dataset_needed`, `regulatory_authority_needed`, `calibration_needed`, `empirical_validation_needed`, `lineage_or_qualification_requirement`, `canonical_implementation_work`, `truthful_rename_candidate`, `redundancy_candidate`, `research_only_candidate`, `owner_decision_required`, `proposed_operational_destination`, `supply_mechanism`, `proposed_artifact`, `corpus_status`, `parsimony_class`, `work_package`, `priority`, `recommended_future_run`, `secondary_future_runs`, `authority_source`, `notes`.

## 3. DATA requirements, module by module

88 rows carry `DATA`. The guard rejects any of them whose missing-evidence cell is empty, is one of a set of generic phrases, or is shorter than twelve words, because section 4 forbids stopping at "more data required". The specifications below are the full cells from the matrix.

**A1.1 Monte Carlo EAC** — canonical method: Monte Carlo simulation of cost at completion over declared input distributions, reporting a distribution and stated percentiles of it.

- Missing: cost-driver input distributions with a declared family and parameters (the module samples designed distributions rather than elicited or fitted ones); the elicitation or fitting record behind each distribution; the dependence structure between drivers; and a convergence criterion tied to the reported percentile
- Structure: Cost Driver Distribution Set (driver id, distribution family, parameters, source of the parameters, correlation matrix between drivers)
- Supply: `NEW_STRUCTURED_FORM` via Cost Driver Distribution Set
- Corpus: `ABSENT`. Already reaching it: bac

**A1.2 CUSUM Anomaly Monitor** — canonical method: two-sided cumulative sum control chart with a reference value k and a decision interval H derived from the in-control process standard deviation and a stated shift to detect.

- Missing: an in-control reference period declared as such; an estimate of the process standard deviation from that period rather than a floored constant; the shift size the chart is designed to detect; and the average-run-length target the pair (k, H) is chosen to meet
- Structure: Control Chart Design Record (series id, in-control window, sigma estimate and its n, target shift, k, H, resulting in-control and out-of-control ARL)
- Supply: `DERIVED_FROM_EXISTING_QUALIFIED_DATA` via Control Chart Design Record
- Corpus: `PARTIALLY_PRESENT`. Already reaching it: none on the authoritative edge list

**A1.3 Bayesian EAC** — canonical method: Bayesian updating of a completion-cost posterior from a stated prior and a stated likelihood, reporting a posterior with a credible interval.

- Missing: a prior distribution with its source (currently a designed constant variance); a likelihood whose variance is estimated from observed reporting error rather than designed; and the observation series the update runs over
- Structure: Bayesian Model Record (prior family and parameters with source, likelihood variance and the residual series it was estimated from, posterior summary and credible interval)
- Supply: `DERIVED_FROM_EXISTING_QUALIFIED_DATA` via Bayesian Model Record
- Corpus: `PARTIALLY_PRESENT`. Already reaching it: ac, bac, ev

**A1.4 Kalman Filter SPI Smoother** — canonical method: Kalman filtering of the schedule performance index with process noise Q and measurement noise R estimated from data, reporting a filtered state and its variance.

- Missing: an estimate of measurement noise R from repeated readings of the same period (the disagreement between documents reporting one period); an estimate of process noise Q from the period-to-period movement of the index; and a history long enough for both
- Structure: Filter Noise Estimation Record (series id, R estimate with the repeated-reading pairs it came from, Q estimate with the differenced series, filtered state and variance)
- Supply: `DERIVED_FROM_EXISTING_QUALIFIED_DATA` via Filter Noise Estimation Record
- Corpus: `PARTIALLY_PRESENT`. Already reaching it: none on the authoritative edge list

**A1.5 ARIMA CPI Forecast** — canonical method: an identified ARIMA model: order selection, stationarity testing, residual diagnostics and a prediction interval on the forecast.

- Missing: a reported cost-index series long enough to identify an order (the platform currently fits one autoregressive coefficient at a fixed lag with no order search); the stationarity test result; residual autocorrelation diagnostics; and the residual variance the prediction interval is built from
- Structure: Reporting History Series (per period: period id, data date, cpi, spi, ev, ac, pv, bac, percent complete, source document version)
- Supply: `DERIVED_FROM_EXISTING_QUALIFIED_DATA` via Reporting History Series
- Corpus: `PARTIALLY_PRESENT`. Already reaching it: none on the authoritative edge list

**A1.6 Earned Schedule** — canonical method: earned schedule: the time at which the earned value now reported would have been planned, read off a time-phased planned value curve.

- Missing: a time-phased planned value curve: period start and end; the planned value planned to be earned in that period; the cumulative planned value at each period end; the budget at completion the curve integrates to; the baseline id and baseline approval date the curve belongs to; the units and currency
- Structure: Time-Phased Baseline Curve
- Supply: `NEW_DOCUMENT_TYPE` via Time-Phased Schedule / Baseline S-Curve (a document type is already declared for this and emits nothing the module reads)
- Corpus: `PARTIALLY_PRESENT`. Already reaching it: actualPctComplete, bac, ev, plannedPctComplete, pv

**A1.9 Budget Execution Rate** — canonical method: a standardised statistical test of expenditure against progress, with a stated null and a reference distribution.

- Missing: the reference distribution the ratio would be tested against, which requires a population of expenditure-versus-progress observations across projects and periods
- Structure: Portfolio Reporting History (the Reporting History Series pooled across projects)
- Supply: `PORTFOLIO_REFERENCE_DATASET` via Portfolio Reporting History
- Corpus: `ABSENT`. Already reaching it: ac, actualPctComplete, bac

**A1.10 Regression to Mean CPI** — canonical method: regression to the mean: shrinkage of a project reading toward a REFERENCE POPULATION mean with a shrinkage weight estimated from the variance components.

- Missing: a governed reference population of projects with their cost indices; the within-project and between-project variance components estimated from it; and the resulting shrinkage weight (the platform uses a fixed one half toward the project's own history)
- Structure: Portfolio Reference Cohort (project id, cohort membership criteria, per-period cost index, cohort mean and variance components, vintage)
- Supply: `PORTFOLIO_REFERENCE_DATASET` via Portfolio Reference Cohort
- Corpus: `ABSENT`. Already reaching it: none on the authoritative edge list

**A1.11 ICE Ratio** — canonical method: an independent cost estimate: an estimate prepared separately, by a different party or a different method, against the same scope, compared with the current forecast.

- Missing: an independently prepared estimate carrying: estimator identity and independence attestation; estimate date; the scope baseline version estimated; the estimating method used; the estimate value with its confidence basis; and the WBS level of detail
- Structure: Independent Cost Estimate Record
- Supply: `NEW_DOCUMENT_TYPE` via Independent Cost Estimate
- Corpus: `ABSENT`. Already reaching it: ac, bac, ev

**A2.1 PERT Network Criticality** — canonical method: PERT: a network with three-point activity duration estimates, from which path criticality is computed.

- Missing: activity id; activity name; deterministic duration; predecessor and successor relationships with relationship type and lag; calendar id and working-day definition; data date / status date; baseline start and finish per activity; actual start and finish per activity; remaining duration; total float and free float per activity; constraint type and date where one is imposed; WBS parent; plus, for a sampling run: a duration distribution family and its parameters per activity (or three-point optimistic / most likely / pessimistic), the correlation or dependence structure between activity durations, and the risk-event-to-activity mapping with probability and impact
- Structure: Schedule Network Data
- Supply: `NEW_DOCUMENT_TYPE` via Schedule Network Export (activity table plus relationship table, from the scheduling tool)
- Corpus: `ABSENT`. Already reaching it: bac

**A2.2 Line of Balance** — canonical method: line of balance: planned and actual production rates per repetitive activity across units, with the buffer between them.

- Missing: repetitive unit ids and their sequence; per activity and per unit, planned start and finish and actual start and finish; the planned production rate per activity; the target buffer between successive activities; and the status date
- Structure: Repetitive Work Production Table
- Supply: `NEW_STRUCTURED_FORM` via Line of Balance Production Schedule
- Corpus: `ABSENT`. Already reaching it: actualPctComplete, plannedPctComplete

**A2.3 CCPM Buffer Health** — canonical method: critical chain buffer health: buffer consumption against chain completion, on a buffered network.

- Missing: the identified critical chain; the project buffer size and its origin; feeding buffers with their sizes and the chains they protect; buffer consumed to date; and the percentage of the protected chain complete
- Structure: Critical Chain Buffer Register
- Supply: `NEW_STRUCTURED_FORM` via CCPM Buffer Register
- Corpus: `ABSENT`. Already reaching it: actualPctComplete, plannedPctComplete

**A2.4 Schedule Compression Index** — canonical method: schedule compression / crashing: a network-based model of which activities can be shortened, at what cost slope, and the resulting duration-cost trade-off.

- Missing: activity id; activity name; deterministic duration; predecessor and successor relationships with relationship type and lag; calendar id and working-day definition; data date / status date; baseline start and finish per activity; actual start and finish per activity; remaining duration; total float and free float per activity; constraint type and date where one is imposed; WBS parent; plus a crash duration and a cost slope per crashable activity
- Structure: Schedule Network Data with Crash Cost Table
- Supply: `NEW_DOCUMENT_TYPE` via Schedule Network Export plus Crash Cost Table
- Corpus: `ABSENT`. Already reaching it: actualPctComplete, baselineEnd, baselineStart

**A2.6 S-Curve Deviation** — canonical method: S-curve deviation: the divergence between the planned and actual cumulative progress CURVES over time.

- Missing: a time-phased planned curve and the matching actual series: period start and end; the planned value planned to be earned in that period; the cumulative planned value at each period end; the budget at completion the curve integrates to; the baseline id and baseline approval date the curve belongs to; the units and currency; plus the actual cumulative earned value at each of the same period ends
- Structure: Time-Phased Baseline Curve plus Reporting History Series
- Supply: `NEW_DOCUMENT_TYPE` via Time-Phased Schedule / Baseline S-Curve
- Corpus: `PARTIALLY_PRESENT`. Already reaching it: actualPctComplete, ev, plannedPctComplete, pv

**A2.7 Milestone Trend Analysis** — canonical method: milestone trend analysis: forecast milestone dates plotted against successive reporting dates, read as a trend against the BASELINE milestone date.

- Missing: the baseline date for each milestone, and at least three dated snapshots of the forecast date for the same milestone with a stable milestone identifier rather than a name match
- Structure: Milestone Forecast History (milestone id, milestone name, baseline date, per snapshot: report date and forecast date, status)
- Supply: `DERIVED_FROM_EXISTING_QUALIFIED_DATA` via Milestone Forecast History
- Corpus: `PARTIALLY_PRESENT`. Already reaching it: none on the authoritative edge list

**A2.10 Schedule Risk Analysis P80** — canonical method: schedule risk analysis: a sampling run over a schedule network with activity duration distributions, reporting the eightieth percentile of the completion date distribution.

- Missing: activity id; activity name; deterministic duration; predecessor and successor relationships with relationship type and lag; calendar id and working-day definition; data date / status date; baseline start and finish per activity; actual start and finish per activity; remaining duration; total float and free float per activity; constraint type and date where one is imposed; WBS parent; plus, for a sampling run: a duration distribution family and its parameters per activity (or three-point optimistic / most likely / pessimistic), the correlation or dependence structure between activity durations, and the risk-event-to-activity mapping with probability and impact
- Structure: Schedule Network Data with duration distributions
- Supply: `NEW_DOCUMENT_TYPE` via Schedule Network Export plus Activity Duration Distribution Set
- Corpus: `ABSENT`. Already reaching it: actualPctComplete, baselineEnd, baselineStart

**A2.11 Critical Path Index** — canonical method: critical path index: the share of simulation runs in which an activity lies on the critical path.

- Missing: activity id; activity name; deterministic duration; predecessor and successor relationships with relationship type and lag; calendar id and working-day definition; data date / status date; baseline start and finish per activity; actual start and finish per activity; remaining duration; total float and free float per activity; constraint type and date where one is imposed; WBS parent; plus, for a sampling run: a duration distribution family and its parameters per activity (or three-point optimistic / most likely / pessimistic), the correlation or dependence structure between activity durations, and the risk-event-to-activity mapping with probability and impact
- Structure: Schedule Network Data with duration distributions
- Supply: `NEW_DOCUMENT_TYPE` via Schedule Network Export plus Activity Duration Distribution Set
- Corpus: `ABSENT`. Already reaching it: actualPctComplete, plannedPctComplete

**A3.1 Reference Class Forecasting** — canonical method: reference class forecasting: an outside-view forecast from an empirical distribution of outcomes in a comparable class of completed projects.

- Missing: a population of completed projects with, per project: project id; project type / asset class; delivery method; region; currency and price base year; approved baseline cost and baseline duration at the decision point the class is anchored to; realised final cost and realised final duration; scope-change indicator; inclusion and exclusion criteria applied; the normalisation and adaptation variables (size, complexity, escalation base) used to make the class comparable; and the data vintage of each record
- Structure: Reference-Class Dataset
- Supply: `HISTORICAL_DATASET` via Reference-Class Dataset
- Corpus: `ABSENT`. Already reaching it: bac

**A3.2 Contingency Burn Rate** — canonical method: contingency burn rate: contingency drawdown against risk retirement.

- Missing: the risk register with, per risk: risk id, the contingency allocated to it, its status (open, realised, retired) and the date of the status change; so that drawdown can be read against risk retirement rather than against percent complete
- Structure: Contingency Drawdown Ledger (risk id, allocation, drawdown transactions with date and amount, risk status history)
- Supply: `NEW_STRUCTURED_FORM` via Contingency Drawdown Ledger
- Corpus: `PARTIALLY_PRESENT`. Already reaching it: actualPctComplete, originalContingency, remainingContingency

**A3.3 Labor Productivity Index** — canonical method: labour productivity: earned output per labour hour against a productivity baseline.

- Missing: an output measure to earn against: quantity installed per work item with its unit of measure, and the budgeted hours per unit of that quantity. Labour hours alone give a ratio of hours to percent complete, not productivity
- Structure: Quantity and Unit Rate Table (work item id, unit of measure, budgeted quantity, quantity installed to date, budgeted hours per unit, actual hours charged)
- Supply: `NEW_STRUCTURED_FORM` via Quantity Installed and Unit Rate Table
- Corpus: `ABSENT`. Already reaching it: actualLaborHours, actualPctComplete, plannedLaborHours

**A3.5 Overhead Absorption Rate** — canonical method: overhead absorption: indirect cost absorbed against an absorption base.

- Missing: the definition of the indirect plan figure: whether indirect_cost_plan is a total-at-completion or a period-to-date figure, and the absorption base (direct labour hours, direct cost or machine hours) the rate is struck on
- Structure: Indirect Cost Basis Declaration (plan basis flag, absorption base, base period, rate)
- Supply: `EXISTING_DOCUMENT_EXTRACTION` via Indirect Cost Basis Declaration on the cost report
- Corpus: `PRESENT_NOT_EXTRACTED`. Already reaching it: indirectCostActual, indirectCostPlan

**A3.6 Cost Risk Analysis P80** — canonical method: cost risk analysis: a sampling run over a risk register with cost impact distributions, reporting the eightieth percentile of the cost outcome distribution.

- Missing: per risk: risk id; probability of occurrence; cost impact distribution family and parameters (or three-point low / likely / high); the correlation between risks; whether the risk is already realised; and the mapping of each risk to the cost account it hits
- Structure: Quantified Risk Register
- Supply: `NEW_STRUCTURED_FORM` via Quantified Risk Register
- Corpus: `ABSENT`. Already reaching it: ac, bac, ev

**A3.7 Analogous Estimating Ratio** — canonical method: analogous estimating: a governed selection of analogous completed projects with a documented normalisation and adaptation to the subject project.

- Missing: the analogue selection rule; per analogue: project id, scope description, final cost, completion year, size and complexity descriptors, region and price base; and the normalisation and adaptation factors applied with their justification
- Structure: Analogue Project Set (a governed subset of the Reference-Class Dataset)
- Supply: `HISTORICAL_DATASET` via Reference-Class Dataset
- Corpus: `PARTIALLY_PRESENT`. Already reaching it: analogousOverrunPct, bac

**A3.8 Parametric Cost Index** — canonical method: parametric cost estimating: an estimating relationship fitted to measurable cost drivers, with calibrated coefficients and their standard errors.

- Missing: measurable cost drivers for the asset class (quantities, capacities, areas, complexity descriptors); a population of completed projects carrying those drivers and their realised costs; the fitted relationship with its functional form; the estimated coefficients with standard errors; and the fit and validation statistics
- Structure: Parametric Estimating Relationship (driver set, project population, functional form, coefficients, standard errors, fit statistics, applicability range)
- Supply: `HISTORICAL_DATASET` via Reference-Class Dataset extended with cost drivers
- Corpus: `ABSENT`. Already reaching it: ac, actualPctComplete, bac, ev

**A3.9 Inflation Adjustment Index** — canonical method: inflation adjustment against a published price index.

- Missing: a governed external price index: publisher; index name and series id; geography; commodity or trade coverage; base period; the index value at the baseline date and at the current date; and the vintage or revision of the series used
- Structure: External Price Index Record
- Supply: `EXTERNAL_OFFICIAL_DATA` via Price Index Reference (for example a published construction cost or producer price series)
- Corpus: `ABSENT`. Already reaching it: materialCostBaseline, materialCostCurrent

**A4.1 Document Risk Score** — canonical method: a document risk score with measured precision and recall against a reference standard.

- Missing: a labelled reference corpus: a labelled reference corpus: document id; document type; the ground-truth condition assigned by a qualified reviewer; the reviewer id; the adjudication rule for disagreements; and a frozen train / calibration / holdout split; plus the score's own construction: which document features enter it, with what weights and from what source
- Structure: Labelled Document Corpus plus Score Construction Record
- Supply: `NEW_PROJECT_DATA_OBJECT` via Labelled Document Corpus
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**A4.4 NCR Rate** — canonical method: nonconformance rate: nonconformances per unit of exposure.

- Missing: an exposure denominator: inspections performed, work quantity placed, or labour hours in the period, so that a count becomes a rate. Only counts (ncr_issued, ncr_open, ncr_closed) are extracted
- Structure: Document Event Denominator (period id, event type, count, exposure unit, exposure quantity)
- Supply: `EXISTING_DOCUMENT_EXTRACTION` via Document Event Denominator Set
- Corpus: `PARTIALLY_PRESENT`. Already reaching it: ncrClosed, ncrIssued, ncrOpen

**A4.6 Change Order Frequency** — canonical method: change order frequency: change orders per unit of exposure time or exposure value.

- Missing: an exposure window: the period over which the counted change orders arose, or the contract value at risk they are counted against. A count with no denominator is not a frequency
- Structure: Document Event Denominator (period start, period end, count in window, contract value exposed)
- Supply: `EXISTING_DOCUMENT_EXTRACTION` via Document Event Denominator Set
- Corpus: `PRESENT_NOT_EXTRACTED`. Already reaching it: baselineContractSum, changeOrderCount

**A4.7 Dispute Escalation Index** — canonical method: dispute escalation: the state of claims and disputes on a governed escalation ladder.

- Missing: per claim or notice: identifier; date raised; the contractual clause invoked; the amount claimed; the current rung of the escalation ladder (notice, claim, negotiation, mediation, arbitration, litigation); the date of the last state change; and the outcome where resolved
- Structure: Claim and Dispute Register
- Supply: `NEW_DOCUMENT_TYPE` via Claim and Notice Register
- Corpus: `ABSENT`. Already reaching it: changeOrderCount, docRiskScore, rfiCount

**A4.8 Subcontractor Performance** — canonical method: subcontractor performance assessment against declared criteria.

- Missing: the construction of the compliance score: which criteria it aggregates, with what weights, assessed by whom, on what date, and against which subcontract scope. The platform reads a precomputed number with no construction record
- Structure: Subcontractor Assessment Record (subcontract id, criterion, score, weight, assessor, assessment date, period covered)
- Supply: `EXISTING_DOCUMENT_EXTRACTION` via Subcontractor Assessment Record
- Corpus: `PARTIALLY_PRESENT`. Already reaching it: subcontractorComplianceScore

**A4.10 Specification Conflict Density** — canonical method: specification conflict density: identified conflicts between specification sections per unit of specification exposure.

- Missing: identified conflicts: conflict id; the two specification references in conflict, each with document id, section and page or clause; who identified it and when; and the exposure unit (specification sections issued, or drawings issued) the density is measured over
- Structure: Specification Conflict Register with evidence locations
- Supply: `NEW_STRUCTURED_FORM` via Specification Conflict Register
- Corpus: `ABSENT`. Already reaching it: docRiskScore, rfiCount

**A5.1 DSM Rework Propagation** — canonical method: design structure matrix rework propagation: rework probability and impact propagated over a dependency matrix.

- Missing: an explicit element set (components, work packages or design tasks) with stable ids; a directed dependency matrix over those elements; a rework probability and a rework impact per dependency edge; a work-transformation or learning coefficient per element; and the iteration or period step over which propagation is evaluated
- Structure: DSM Dependency Matrix
- Supply: `NEW_STRUCTURED_FORM` via DSM Dependency Matrix
- Corpus: `ABSENT`. Already reaching it: none on the authoritative edge list

**A5.2 Sensitivity Analysis** — canonical method: sensitivity analysis: a response re-evaluated as each input is moved across a declared range.

- Missing: declared input ranges: for each input, the low and high value with the basis for each, and the response function the ranges are propagated through
- Structure: Input Range Declaration (input id, low, high, basis, distribution if used)
- Supply: `NEW_STRUCTURED_FORM` via Scenario Assumption Set
- Corpus: `ABSENT`. Already reaching it: ac, bac, ev, pv

**A5.3 Tornado Risk Ranking** — canonical method: tornado analysis: the swing in an output when each input is moved across its declared range, ranked by swing.

- Missing: declared input ranges as for A5.2, plus the output the swing is measured on and its re-evaluation at each low and high
- Structure: Input Range Declaration plus a named response output
- Supply: `NEW_STRUCTURED_FORM` via Scenario Assumption Set
- Corpus: `ABSENT`. Already reaching it: actualPctComplete, docRiskScore, plannedPctComplete

**A5.4 Scenario Modeling** — canonical method: scenario modelling: named scenarios with declared assumption sets, evaluated through the same model.

- Missing: per scenario: scenario id and name; the assumption set (each assumption with the input it sets and the value it sets it to); the probability or weight assigned to the scenario if any; and the author and date of the assumption set
- Structure: Scenario Assumption Set
- Supply: `NEW_STRUCTURED_FORM` via Scenario Assumption Set
- Corpus: `ABSENT`. Already reaching it: ac, bac, ev

**A5.5 Rework Feedback Loop** — canonical method: a system dynamics rework feedback loop: stocks of work done, work discovered defective and work returned, with the rates between them over time.

- Missing: stock and flow definitions: work in each stock at each period; the discovery rate; the rework rate; the delay between execution and discovery; and the loop gain, each estimated from observed period data rather than assumed
- Structure: Rework Stock and Flow Series
- Supply: `NEW_STRUCTURED_FORM` via Rework Stock and Flow Series
- Corpus: `ABSENT`. Already reaching it: changeOrderCount, rfiCount

**A5.6 Queueing Theory Bottleneck** — canonical method: queueing analysis: arrival and service processes, server count and discipline, from which utilisation, queue length and waiting time follow.

- Missing: arrival timestamps (or a fitted arrival process with its parameters); service start and service end timestamps, or observed service-time durations; the number of servers or resource units available per period; the queue discipline; the routing between stations; and the observation window with its start and end
- Structure: Queue Observation Log
- Supply: `NEW_STRUCTURED_FORM` via Queue Observation Log
- Corpus: `ABSENT`. Already reaching it: activitiesConstrained, activitiesPlanned

**A5.7 Agent-Based Supply Chain** — canonical method: agent-based supply chain simulation: agents with decision rules interacting over time.

- Missing: agent types with attributes; a decision rule per agent type; an interaction or network structure between agents; an environment state the agents read and write; a time-step definition; and initialisation and replication policy; plus, for a supply chain: supplier agents with lead-time distributions, order policies, and the disruption events they respond to
- Structure: Agent / Resource Definition
- Supply: `NEW_STRUCTURED_FORM` via Agent and Resource Definition Set
- Corpus: `ABSENT`. Already reaching it: longLeadAtRisk, longLeadItemsTotal

**A5.8 Discrete Event Simulation** — canonical method: discrete event simulation: entities, resources, queues, an event list and a simulation clock.

- Missing: entity types and their generation process; resource definitions with capacity and calendar; an event definition set (event type, trigger condition, state change, duration distribution); queue definitions and disciplines; a run length, warm-up period and replication count; and the random seed policy
- Structure: DES Event Definition
- Supply: `NEW_STRUCTURED_FORM` via DES Event Definition Set
- Corpus: `ABSENT`. Already reaching it: actualPctComplete, plannedPctComplete

**A6.1 Quality Compliance Index** — canonical method: quality compliance: conformance against declared quality criteria.

- Missing: the quality audit findings themselves: audit_score, total_findings, critical_findings and items_inspected / items_failed are ALL extracted from the quality_audit_report and inspection_report document types and NONE of them reaches this module, which reads the meeting-minute proxy qualityDeficienciesNoted instead
- Structure: Quality Evidence Wiring (join the quality_audit_report and inspection_report fields to the module's input contract)
- Supply: `EXISTING_DOCUMENT_EXTRACTION` via Quality Audit Report (already a supported document type)
- Corpus: `PRESENT_NOT_EXTRACTED`. Already reaching it: qualityDeficienciesNoted

**A6.2 Safety Performance Index** — canonical method: safety performance: recordable incidents against exposure hours on the standard basis.

- Missing: osha_recordable_incidents, incident_rate and total_manhours are ALL extracted from the safety_report document type and NONE reaches this module, which reads the meeting-minute proxy safetyIncidentsDiscussed instead. The standard rate requires recordable incident count and total manhours together with the two-hundred-thousand-hour convention
- Structure: Safety Evidence Wiring (join the safety_report fields to the module's input contract)
- Supply: `EXISTING_DOCUMENT_EXTRACTION` via Safety Report (already a supported document type)
- Corpus: `PRESENT_NOT_EXTRACTED`. Already reaching it: safetyIncidentsDiscussed

**A6.3 Environmental Compliance Rate** — canonical method: environmental compliance against a named authority's conditions, at a stated version.

- Missing: environmentalComplianceRate and violations are extracted from the environmental_report and do not reach this module, which reads environmentalIssuesDiscussed from meeting minutes. Separately the regulatory object is absent: the issuing authority; the instrument identifier and its clause or section; the version and its effective date; the jurisdiction; an applicability predicate stating which projects the rule binds; the numeric level the instrument itself states (rather than one chosen here); and an evidence object recording which document proved the condition and where in it
- Structure: Regulatory Applicability Record plus Environmental Evidence Wiring
- Supply: `EXISTING_DOCUMENT_EXTRACTION` via Environmental Report (already supported) plus Regulatory Applicability Record
- Corpus: `PRESENT_NOT_EXTRACTED`. Already reaching it: environmentalIssuesDiscussed

**A6.4 Contractor Performance Score** — canonical method: contractor past performance assessment drawn from official past performance information.

- Missing: a past performance record with: the source system identifier; the assessing agency; the assessment period; the contract it relates to; the rating on each declared factor; the record status; and its review state
- Structure: Past Performance Information Record
- Supply: `EXTERNAL_OFFICIAL_DATA` via Official Past Performance Information
- Corpus: `ABSENT`. Already reaching it: costRating, overallRating, scheduleRating

**B1.2 Weighted Voting** — canonical method: weighted voting over qualified signal states with sourced weights.

- Missing: the qualified-evidence boundary: a signal qualification state per input, which the Category-9 gate would supply and which production itself records as unimplemented (SIGNAL_QUALIFICATION = 'unqualified', CATEGORY_9_DEVIATION)
- Structure: Qualified Signal State (per signal: qualification verdict, the dimensions assessed, the reason where unqualified)
- Supply: `DERIVED_FROM_EXISTING_QUALIFIED_DATA` via Category-9 Qualification Verdict
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B1.3 Majority Rules** — canonical method: majority rule over qualified signal states.

- Missing: the same qualified-evidence boundary as B1.2, plus dependence control: the signals tallied are not independent, and several are readings of one earned-value measurement
- Structure: Qualified Signal State plus a declared dependence structure over signals
- Supply: `DERIVED_FROM_EXISTING_QUALIFIED_DATA` via Category-9 Qualification Verdict
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B1.4 Worst-N-of-M** — canonical method: worst-N-of-M: escalate when N of M signals are adverse, with N and M chosen against a stated error target.

- Missing: the basis for the two proportional thresholds (three tenths of the banded signals for Red, four tenths for Amber), which are design constants; and the qualified-evidence boundary as for B1.2
- Structure: Threshold Design Record (rule, threshold, the error target it meets, the evidence it was chosen against) plus Qualified Signal State
- Supply: `DERIVED_FROM_EXISTING_QUALIFIED_DATA` via Category-9 Qualification Verdict
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B2.1 Dempster-Shafer** — canonical method: Dempster-Shafer combination over independently derived bodies of evidence, with a declared frame of discernment and a stated conflict treatment.

- Missing: elicited or observed assessments to build the memberships from: an elicited assessment set: expert id; the object assessed; the linguistic or interval assessment given; the elicitation protocol and date; the aggregation rule agreed in advance; and the consistency or agreement statistic across experts; plus the qualified-evidence boundary, because the memberships currently consume raw unqualified cost and schedule indices and the document risk score directly
- Structure: Elicited Assessment Set plus Qualified Signal State
- Supply: `NEW_STRUCTURED_FORM` via Expert Elicitation Form plus Category-9 Qualification Verdict
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B2.2 Rough Sets** — canonical method: rough set approximation over an information table of objects described by attributes.

- Missing: elicited or observed assessments to build the memberships from: an elicited assessment set: expert id; the object assessed; the linguistic or interval assessment given; the elicitation protocol and date; the aggregation rule agreed in advance; and the consistency or agreement statistic across experts; plus the qualified-evidence boundary, because the memberships currently consume raw unqualified cost and schedule indices and the document risk score directly
- Structure: Elicited Assessment Set plus Qualified Signal State
- Supply: `NEW_STRUCTURED_FORM` via Expert Elicitation Form plus Category-9 Qualification Verdict
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B2.3 Neutrosophic Logic** — canonical method: neutrosophic logic over independently assessed truth, indeterminacy and falsity degrees.

- Missing: elicited or observed assessments to build the memberships from: an elicited assessment set: expert id; the object assessed; the linguistic or interval assessment given; the elicitation protocol and date; the aggregation rule agreed in advance; and the consistency or agreement statistic across experts; plus the qualified-evidence boundary, because the memberships currently consume raw unqualified cost and schedule indices and the document risk score directly
- Structure: Elicited Assessment Set plus Qualified Signal State
- Supply: `NEW_STRUCTURED_FORM` via Expert Elicitation Form plus Category-9 Qualification Verdict
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B2.4 Interval Fuzzy Sets** — canonical method: interval-valued fuzzy sets whose interval widths come from assessment uncertainty.

- Missing: elicited or observed assessments to build the memberships from: an elicited assessment set: expert id; the object assessed; the linguistic or interval assessment given; the elicitation protocol and date; the aggregation rule agreed in advance; and the consistency or agreement statistic across experts; plus the qualified-evidence boundary, because the memberships currently consume raw unqualified cost and schedule indices and the document risk score directly
- Structure: Elicited Assessment Set plus Qualified Signal State
- Supply: `NEW_STRUCTURED_FORM` via Expert Elicitation Form plus Category-9 Qualification Verdict
- Corpus: `ABSENT`. Already reaching it: none on the authoritative edge list

**B2.5 Z-numbers** — canonical method: Z-numbers: a restriction paired with a reliability measure of that restriction.

- Missing: elicited or observed assessments to build the memberships from: an elicited assessment set: expert id; the object assessed; the linguistic or interval assessment given; the elicitation protocol and date; the aggregation rule agreed in advance; and the consistency or agreement statistic across experts; plus the qualified-evidence boundary, because the memberships currently consume raw unqualified cost and schedule indices and the document risk score directly
- Structure: Elicited Assessment Set plus Qualified Signal State
- Supply: `NEW_STRUCTURED_FORM` via Expert Elicitation Form plus Category-9 Qualification Verdict
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B2.6 PLTS** — canonical method: probabilistic linguistic term sets over elicited linguistic assessments with their probabilities.

- Missing: elicited or observed assessments to build the memberships from: an elicited assessment set: expert id; the object assessed; the linguistic or interval assessment given; the elicitation protocol and date; the aggregation rule agreed in advance; and the consistency or agreement statistic across experts; plus the qualified-evidence boundary, because the memberships currently consume raw unqualified cost and schedule indices and the document risk score directly
- Structure: Elicited Assessment Set plus Qualified Signal State
- Supply: `NEW_STRUCTURED_FORM` via Expert Elicitation Form plus Category-9 Qualification Verdict
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B2.7 Plithogenic Sets** — canonical method: plithogenic set operations over attributes with degrees of appurtenance and a contradiction degree between attribute values.

- Missing: the attribute set with, per attribute: its value range; the dominant value; the degree of appurtenance of each object to each value; and the contradiction degree between each value and the dominant one
- Structure: Plithogenic Attribute Set
- Supply: `NEW_STRUCTURED_FORM` via Expert Elicitation Form
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B2.8 Belief Rule Base** — canonical method: belief rule base inference with rule weights and attribute weights learned or elicited.

- Missing: elicited or observed assessments to build the memberships from: an elicited assessment set: expert id; the object assessed; the linguistic or interval assessment given; the elicitation protocol and date; the aggregation rule agreed in advance; and the consistency or agreement statistic across experts; plus the qualified-evidence boundary, because the memberships currently consume raw unqualified cost and schedule indices and the document risk score directly
- Structure: Elicited Assessment Set plus Qualified Signal State
- Supply: `NEW_STRUCTURED_FORM` via Expert Elicitation Form plus Category-9 Qualification Verdict
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B2.9 Quantum Probability** — canonical method: quantum probability: a state vector in a Hilbert space with projective measurement operators, from which order and interference effects follow.

- Missing: the declared Hilbert space and its basis; the projection operators corresponding to each assessment; the state preparation; and an empirical reason to believe the judgments being modelled violate classical additivity, which is the only thing that motivates the formalism
- Structure: Quantum Judgment Model Specification
- Supply: `NOT_REASONABLY_SUPPLIABLE` via none proposed: the motivating empirical phenomenon would itself have to be demonstrated first
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B2.10 Pythagorean Fuzzy Sets** — canonical method: Pythagorean fuzzy sets over assessed membership and non-membership.

- Missing: elicited or observed assessments to build the memberships from: an elicited assessment set: expert id; the object assessed; the linguistic or interval assessment given; the elicitation protocol and date; the aggregation rule agreed in advance; and the consistency or agreement statistic across experts; plus the qualified-evidence boundary, because the memberships currently consume raw unqualified cost and schedule indices and the document risk score directly
- Structure: Elicited Assessment Set plus Qualified Signal State
- Supply: `NEW_STRUCTURED_FORM` via Expert Elicitation Form plus Category-9 Qualification Verdict
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B2.11 Picture Fuzzy Sets** — canonical method: picture fuzzy sets over assessed positive, neutral, negative and refusal degrees.

- Missing: elicited or observed assessments to build the memberships from: an elicited assessment set: expert id; the object assessed; the linguistic or interval assessment given; the elicitation protocol and date; the aggregation rule agreed in advance; and the consistency or agreement statistic across experts; plus the qualified-evidence boundary, because the memberships currently consume raw unqualified cost and schedule indices and the document risk score directly
- Structure: Elicited Assessment Set plus Qualified Signal State
- Supply: `NEW_STRUCTURED_FORM` via Expert Elicitation Form plus Category-9 Qualification Verdict
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B2.12 Hesitant Fuzzy Sets** — canonical method: hesitant fuzzy sets over MULTIPLE assessments of the same object by different assessors.

- Missing: elicited or observed assessments to build the memberships from: an elicited assessment set: expert id; the object assessed; the linguistic or interval assessment given; the elicitation protocol and date; the aggregation rule agreed in advance; and the consistency or agreement statistic across experts; plus the qualified-evidence boundary, because the memberships currently consume raw unqualified cost and schedule indices and the document risk score directly
- Structure: Elicited Assessment Set plus Qualified Signal State
- Supply: `NEW_STRUCTURED_FORM` via Expert Elicitation Form plus Category-9 Qualification Verdict
- Corpus: `ABSENT`. Already reaching it: none on the authoritative edge list

**B2.13 Type-2 Fuzzy Sets** — canonical method: type-2 fuzzy sets whose footprint of uncertainty comes from disagreement between assessors.

- Missing: elicited or observed assessments to build the memberships from: an elicited assessment set: expert id; the object assessed; the linguistic or interval assessment given; the elicitation protocol and date; the aggregation rule agreed in advance; and the consistency or agreement statistic across experts; plus the qualified-evidence boundary, because the memberships currently consume raw unqualified cost and schedule indices and the document risk score directly
- Structure: Elicited Assessment Set plus Qualified Signal State
- Supply: `NEW_STRUCTURED_FORM` via Expert Elicitation Form plus Category-9 Qualification Verdict
- Corpus: `ABSENT`. Already reaching it: none on the authoritative edge list

**B2.14 Maximum Entropy** — canonical method: maximum entropy: the distribution of greatest entropy subject to stated moment constraints.

- Missing: elicited or observed assessments to build the memberships from: an elicited assessment set: expert id; the object assessed; the linguistic or interval assessment given; the elicitation protocol and date; the aggregation rule agreed in advance; and the consistency or agreement statistic across experts; plus the qualified-evidence boundary, because the memberships currently consume raw unqualified cost and schedule indices and the document risk score directly
- Structure: Elicited Assessment Set plus Qualified Signal State
- Supply: `NEW_STRUCTURED_FORM` via Expert Elicitation Form plus Category-9 Qualification Verdict
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B2.15 Possibility Theory** — canonical method: possibility theory with a governed possibility distribution.

- Missing: elicited or observed assessments to build the memberships from: an elicited assessment set: expert id; the object assessed; the linguistic or interval assessment given; the elicitation protocol and date; the aggregation rule agreed in advance; and the consistency or agreement statistic across experts; plus the qualified-evidence boundary, because the memberships currently consume raw unqualified cost and schedule indices and the document risk score directly
- Structure: Elicited Assessment Set plus Qualified Signal State
- Supply: `NEW_STRUCTURED_FORM` via Expert Elicitation Form plus Category-9 Qualification Verdict
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B2.16 Spherical Fuzzy Sets** — canonical method: spherical fuzzy sets over assessed membership, non-membership and hesitancy.

- Missing: elicited or observed assessments to build the memberships from: an elicited assessment set: expert id; the object assessed; the linguistic or interval assessment given; the elicitation protocol and date; the aggregation rule agreed in advance; and the consistency or agreement statistic across experts; plus the qualified-evidence boundary, because the memberships currently consume raw unqualified cost and schedule indices and the document risk score directly
- Structure: Elicited Assessment Set plus Qualified Signal State
- Supply: `NEW_STRUCTURED_FORM` via Expert Elicitation Form plus Category-9 Qualification Verdict
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B2.17 Fermatean Fuzzy Sets** — canonical method: Fermatean fuzzy sets over assessed membership and non-membership.

- Missing: elicited or observed assessments to build the memberships from: an elicited assessment set: expert id; the object assessed; the linguistic or interval assessment given; the elicitation protocol and date; the aggregation rule agreed in advance; and the consistency or agreement statistic across experts; plus the qualified-evidence boundary, because the memberships currently consume raw unqualified cost and schedule indices and the document risk score directly
- Structure: Elicited Assessment Set plus Qualified Signal State
- Supply: `NEW_STRUCTURED_FORM` via Expert Elicitation Form plus Category-9 Qualification Verdict
- Corpus: `ABSENT`. Already reaching it: none on the authoritative edge list

**B2.18 MARCOS Ranking** — canonical method: MARCOS: ranking of a SET of alternatives against ideal and anti-ideal reference points derived from that set.

- Missing: a real alternative set to rank: a set of candidate actions with stable ids and a description of each; the decision variables each action moves, with type, unit and bounds; the objective functions with coefficients and sense (minimise or maximise); the constraint set with coefficient matrix, relation and right-hand side; and the units of every quantity so the model is dimensionally coherent. The reference points must be derived from the alternative set, which is what makes them ideal and anti-ideal
- Structure: Decision Alternatives Table
- Supply: `NEW_STRUCTURED_FORM` via Decision Alternatives Table
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B2.19 CRITIC-TOPSIS** — canonical method: CRITIC weighting followed by TOPSIS ranking over a decision matrix of alternatives by criteria.

- Missing: a decision matrix: a set of candidate actions with stable ids and a description of each; the decision variables each action moves, with type, unit and bounds; the objective functions with coefficients and sense (minimise or maximise); the constraint set with coefficient matrix, relation and right-hand side; and the units of every quantity so the model is dimensionally coherent. CRITIC weights are derived from the contrast and conflict WITHIN the alternative set, so a single alternative supplies no weights at all
- Structure: Decision Alternatives Table
- Supply: `NEW_STRUCTURED_FORM` via Decision Alternatives Table
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B2.20 Hypersoft Sets** — canonical method: hypersoft sets: a soft set over a Cartesian product of attribute-value sets, with a mapping from each attribute tuple to a subset of the universe.

- Missing: the universe of objects; the attribute set with the value set of each attribute; and the mapping from each tuple of attribute values to its subset of the universe
- Structure: Hypersoft Attribute Mapping
- Supply: `NEW_STRUCTURED_FORM` via Expert Elicitation Form
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B3.1 ABM Governance Layer** — canonical method: agent-based modelling: agents with decision rules, an interaction structure and time steps.

- Missing: agent types with attributes; a decision rule per agent type; an interaction or network structure between agents; an environment state the agents read and write; a time-step definition; and initialisation and replication policy
- Structure: Agent / Resource Definition
- Supply: `NEW_STRUCTURED_FORM` via Agent and Resource Definition Set
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B3.2 FAR Threshold Monitor** — canonical method: a Federal Acquisition Regulation threshold determination at a stated part, version and applicability.

- Missing: the issuing authority; the instrument identifier and its clause or section; the version and its effective date; the jurisdiction; an applicability predicate stating which projects the rule binds; the numeric level the instrument itself states (rather than one chosen here); and an evidence object recording which document proved the condition and where in it
- Structure: Regulatory Applicability Record
- Supply: `NEW_PROJECT_DATA_OBJECT` via Regulatory Applicability Record
- Corpus: `ABSENT`. Already reaching it: ac, bac, ev

**B3.3 OMB A-11 Check** — canonical method: an OMB Circular A-11 reporting determination at a stated version and applicability.

- Missing: the issuing authority; the instrument identifier and its clause or section; the version and its effective date; the jurisdiction; an applicability predicate stating which projects the rule binds; the numeric level the instrument itself states (rather than one chosen here); and an evidence object recording which document proved the condition and where in it
- Structure: Regulatory Applicability Record
- Supply: `NEW_PROJECT_DATA_OBJECT` via Regulatory Applicability Record
- Corpus: `ABSENT`. Already reaching it: actualPctComplete, bac

**B3.4 EVM Reporting Threshold** — canonical method: an earned value management reporting-threshold determination at a stated authority and version.

- Missing: the issuing authority; the instrument identifier and its clause or section; the version and its effective date; the jurisdiction; an applicability predicate stating which projects the rule binds; the numeric level the instrument itself states (rather than one chosen here); and an evidence object recording which document proved the condition and where in it
- Structure: Regulatory Applicability Record
- Supply: `NEW_PROJECT_DATA_OBJECT` via Regulatory Applicability Record
- Corpus: `ABSENT`. Already reaching it: bac

**B3.5 Contract Modification Frequency** — canonical method: contract modification frequency: modifications per unit of exposure time or contract value.

- Missing: an exposure window or exposure value, as for A4.6: the period the counted modifications arose in, or the contract value they are counted against
- Structure: Document Event Denominator
- Supply: `EXISTING_DOCUMENT_EXTRACTION` via Document Event Denominator Set
- Corpus: `PRESENT_NOT_EXTRACTED`. Already reaching it: baselineContractSum, changeOrderCount

**B4.1 Multi-Objective Optimization** — canonical method: multi-objective optimization over declared objectives, decision variables and a feasible set.

- Missing: a set of candidate actions with stable ids and a description of each; the decision variables each action moves, with type, unit and bounds; the objective functions with coefficients and sense (minimise or maximise); the constraint set with coefficient matrix, relation and right-hand side; and the units of every quantity so the model is dimensionally coherent
- Structure: Objective and Constraint Set
- Supply: `NEW_STRUCTURED_FORM` via Decision Alternatives Table plus Objective and Constraint Set
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B4.2 Linear Programming** — canonical method: linear programming: decision variables, a linear objective, a constraint matrix with right-hand sides and bounds.

- Missing: a set of candidate actions with stable ids and a description of each; the decision variables each action moves, with type, unit and bounds; the objective functions with coefficients and sense (minimise or maximise); the constraint set with coefficient matrix, relation and right-hand side; and the units of every quantity so the model is dimensionally coherent
- Structure: Objective and Constraint Set
- Supply: `NEW_STRUCTURED_FORM` via Objective and Constraint Set
- Corpus: `ABSENT`. Already reaching it: ac, bac, ev

**B4.3 Constraint Satisfaction Analysis** — canonical method: constraint satisfaction: a constraint network over declared variables and domains, solved for a satisfying assignment.

- Missing: declared decision variables with domains, and constraints over them that are not simply threshold tests on already-computed indices
- Structure: Objective and Constraint Set
- Supply: `NEW_STRUCTURED_FORM` via Objective and Constraint Set
- Corpus: `ABSENT`. Already reaching it: bac

**B4.4 What-If Scenario Matrix** — canonical method: a what-if matrix: candidate actions as rows, scenarios as columns, an outcome in each cell.

- Missing: candidate actions with identity (none is carried) and scenario definitions: a set of candidate actions with stable ids and a description of each; the decision variables each action moves, with type, unit and bounds; the objective functions with coefficients and sense (minimise or maximise); the constraint set with coefficient matrix, relation and right-hand side; and the units of every quantity so the model is dimensionally coherent
- Structure: Decision Alternatives Table plus Scenario Assumption Set
- Supply: `NEW_STRUCTURED_FORM` via Decision Alternatives Table
- Corpus: `ABSENT`. Already reaching it: ac, bac, ev

**B4.5 Decision Sensitivity Matrix** — canonical method: a decision sensitivity matrix: a decision set with declared input ranges and a response evaluated over them.

- Missing: a decision set and declared input ranges: a set of candidate actions with stable ids and a description of each; the decision variables each action moves, with type, unit and bounds; the objective functions with coefficients and sense (minimise or maximise); the constraint set with coefficient matrix, relation and right-hand side; and the units of every quantity so the model is dimensionally coherent
- Structure: Decision Alternatives Table plus Input Range Declaration
- Supply: `NEW_STRUCTURED_FORM` via Decision Alternatives Table plus Scenario Assumption Set
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B4.6 Pareto Frontier Analysis** — canonical method: Pareto frontier: a set of alternatives evaluated on two or more objectives, over which dominance is assessed.

- Missing: a set of at least two alternatives with their objective values: a set of candidate actions with stable ids and a description of each; the decision variables each action moves, with type, unit and bounds; the objective functions with coefficients and sense (minimise or maximise); the constraint set with coefficient matrix, relation and right-hand side; and the units of every quantity so the model is dimensionally coherent
- Structure: Decision Alternatives Table
- Supply: `NEW_STRUCTURED_FORM` via Decision Alternatives Table
- Corpus: `ABSENT`. Already reaching it: docRiskScore

**B4.7 Regret Minimization Index** — canonical method: regret minimization: maximum regret across states of nature for each candidate action, minimised.

- Missing: candidate actions and states of nature with a payoff for each action-state pair: a set of candidate actions with stable ids and a description of each; the decision variables each action moves, with type, unit and bounds; the objective functions with coefficients and sense (minimise or maximise); the constraint set with coefficient matrix, relation and right-hand side; and the units of every quantity so the model is dimensionally coherent; plus the state set with its definition
- Structure: Decision Alternatives Table plus Scenario Assumption Set
- Supply: `NEW_STRUCTURED_FORM` via Decision Alternatives Table
- Corpus: `ABSENT`. Already reaching it: bac

**C1.2 Data Timeliness Score** — canonical method: data timeliness: the age of each reported figure against a declared freshness requirement.

- Missing: a declared freshness requirement per field: the maximum acceptable age of each figure and the authority for it, so that lateness is measured against a standard rather than a chosen number
- Structure: Freshness Requirement Declaration (field, maximum age, unit, authority)
- Supply: `NEW_PROJECT_DATA_OBJECT` via Reporting Cadence and Freshness Declaration
- Corpus: `ABSENT`. Already reaching it: none on the authoritative edge list

**C1.3 Source Reliability Weighting** — canonical method: source reliability weighting: weights on sources derived from their observed reliability.

- Missing: an observed reliability record per source type: how often figures from that source were later corrected, by how much, over how many observations
- Structure: Source Reliability Record (source type, observations, correction rate, mean correction magnitude, window)
- Supply: `DERIVED_FROM_EXISTING_QUALIFIED_DATA` via Source Reliability Record
- Corpus: `PARTIALLY_PRESENT`. Already reaching it: bac

**C1.4 Audit Trail Completeness** — canonical method: audit trail completeness: assessment of the real signal, judgment and audit objects, their event chronology and the linkage between them, with noncompensatory treatment of critical fields.

- Missing: the audit object graph itself: signal record ids, judgment record ids, audit event ids, their timestamps, and the declared linkage between them; plus the designation of which fields are critical and therefore may not be compensated for by others
- Structure: Audit Object Graph plus Critical Field Designation
- Supply: `DERIVED_FROM_EXISTING_QUALIFIED_DATA` via Audit Object Graph
- Corpus: `PRESENT_NOT_EXTRACTED`. Already reaching it: bac

**C1.6 Cross-document Consistency Score** — canonical method: cross-document consistency: the same fact compared across two or more identified documents.

- Missing: per-field source records: for each extracted figure, the document id, document version, page or location, and extraction timestamp it came from, so that two documents reporting one fact can be compared and the disagreeing document named
- Structure: Field Provenance Record (field, value, document id, document version, location, extracted at)
- Supply: `EXISTING_DOCUMENT_EXTRACTION` via Field-Level Provenance
- Corpus: `PRESENT_NOT_EXTRACTED`. Already reaching it: ac, ev

**C1.7 Reporting Frequency Index** — canonical method: reporting frequency: reports received against a declared reporting cadence.

- Missing: the declared reporting cadence: required reporting interval, the document types required each interval, and the contractual or policy basis for the requirement
- Structure: Reporting Cadence Declaration
- Supply: `NEW_PROJECT_DATA_OBJECT` via Reporting Cadence and Freshness Declaration
- Corpus: `ABSENT`. Already reaching it: none on the authoritative edge list

**D1.1 Isolation Forest** — canonical method: isolation forest anomaly detection with an anomaly-score threshold chosen against a stated error target.

- Missing: a portfolio large enough for the ensemble to mean anything, with a declared cohort definition: which projects are comparable and why
- Structure: Portfolio Cohort Definition plus Portfolio Reporting History
- Supply: `PORTFOLIO_REFERENCE_DATASET` via Portfolio Cohort Definition
- Corpus: `PARTIALLY_PRESENT`. Already reaching it: none on the authoritative edge list

**D1.2 Portfolio Outlier Detection** — canonical method: portfolio outlier detection: a percentile rank of this project within a defined cohort.

- Missing: a declared cohort: inclusion criteria, minimum cohort size for a percentile to be meaningful, and the vintage of the cohort's readings
- Structure: Portfolio Cohort Definition
- Supply: `PORTFOLIO_REFERENCE_DATASET` via Portfolio Cohort Definition
- Corpus: `PARTIALLY_PRESENT`. Already reaching it: none on the authoritative edge list

**D1.3 Signal Trajectory Classifier** — canonical method: trajectory classification: a classified trend over a project's history against defined classes.

- Missing: a governed minimum history length and a class definition with boundaries derived from observed trend distributions rather than chosen
- Structure: Portfolio Reporting History plus Trend Class Definition
- Supply: `PORTFOLIO_REFERENCE_DATASET` via Portfolio Reporting History
- Corpus: `PARTIALLY_PRESENT`. Already reaching it: none on the authoritative edge list

**D1.4 Cross-project Pattern Detector** — canonical method: cross-project pattern detection: recurring signal patterns identified across a portfolio.

- Missing: a declared similarity metric with its threshold justified, and a cohort large enough for a pattern to be distinguishable from coincidence
- Structure: Portfolio Cohort Definition plus Similarity Metric Declaration
- Supply: `PORTFOLIO_REFERENCE_DATASET` via Portfolio Cohort Definition
- Corpus: `PARTIALLY_PRESENT`. Already reaching it: none on the authoritative edge list

**D1.5 Anomaly Score** — canonical method: a composite anomaly score over independent anomaly evidence.

- Missing: independent anomaly evidence to compose. Read from portfolio.py, this score is the mean of (a) a standardised Mahalanobis distance, (b) one minus D1.2's own composite percentile rank, and (c) a term in D1.3's own trend. Two of its at most three terms are other registered modules' outputs
- Structure: Declared composition with a dependence structure, or removal of the duplicated terms
- Supply: `DERIVED_FROM_EXISTING_QUALIFIED_DATA` via Portfolio Cohort Definition
- Corpus: `PARTIALLY_PRESENT`. Already reaching it: none on the authoritative edge list

## 4. Proposed evidence, document and form additions

Supply mechanisms across the 97:

| Mechanism | Rows |
|---|---|
| `NEW_STRUCTURED_FORM` | 42 |
| `DERIVED_FROM_EXISTING_QUALIFIED_DATA` | 11 |
| `(none: no missing evidence)` | 9 |
| `EXISTING_DOCUMENT_EXTRACTION` | 9 |
| `NEW_DOCUMENT_TYPE` | 8 |
| `PORTFOLIO_REFERENCE_DATASET` | 6 |
| `NEW_PROJECT_DATA_OBJECT` | 6 |
| `HISTORICAL_DATASET` | 3 |
| `EXTERNAL_OFFICIAL_DATA` | 2 |
| `NOT_REASONABLY_SUPPLIABLE` | 1 |

Distinct proposed artifacts, with the modules each would unblock:

| Proposed artifact | Modules |
|---|---|
| Expert Elicitation Form plus Category-9 Qualification Verdict | 15: B2.1, B2.2, B2.3, B2.4, B2.5, B2.6, B2.8, B2.10, B2.11, B2.12, B2.13, B2.14, B2.15, B2.16, B2.17 |
| Decision Alternatives Table | 5: B2.18, B2.19, B4.4, B4.6, B4.7 |
| Portfolio Cohort Definition | 4: D1.1, D1.2, D1.4, D1.5 |
| Document Event Denominator Set | 3: A4.4, A4.6, B3.5 |
| Scenario Assumption Set | 3: A5.2, A5.3, A5.4 |
| Category-9 Qualification Verdict | 3: B1.2, B1.3, B1.4 |
| Regulatory Applicability Record | 3: B3.2, B3.3, B3.4 |
| Portfolio Reporting History | 2: A1.9, D1.3 |
| Schedule Network Export plus Activity Duration Distribution Set | 2: A2.10, A2.11 |
| Reference-Class Dataset | 2: A3.1, A3.7 |
| Agent and Resource Definition Set | 2: A5.7, B3.1 |
| Expert Elicitation Form | 2: B2.7, B2.20 |
| Objective and Constraint Set | 2: B4.2, B4.3 |
| Reporting Cadence and Freshness Declaration | 2: C1.2, C1.7 |
| Cost Driver Distribution Set | 1: A1.1 |
| Control Chart Design Record | 1: A1.2 |
| Bayesian Model Record | 1: A1.3 |
| Filter Noise Estimation Record | 1: A1.4 |
| Reporting History Series | 1: A1.5 |
| Time-Phased Schedule / Baseline S-Curve (a document type is already declared for this and emits nothing the module reads) | 1: A1.6 |
| Portfolio Reference Cohort | 1: A1.10 |
| Independent Cost Estimate | 1: A1.11 |
| Schedule Network Export (activity table plus relationship table, from the scheduling tool) | 1: A2.1 |
| Line of Balance Production Schedule | 1: A2.2 |
| CCPM Buffer Register | 1: A2.3 |
| Schedule Network Export plus Crash Cost Table | 1: A2.4 |
| Time-Phased Schedule / Baseline S-Curve | 1: A2.6 |
| Milestone Forecast History | 1: A2.7 |
| Contingency Drawdown Ledger | 1: A3.2 |
| Quantity Installed and Unit Rate Table | 1: A3.3 |
| Indirect Cost Basis Declaration on the cost report | 1: A3.5 |
| Quantified Risk Register | 1: A3.6 |
| Reference-Class Dataset extended with cost drivers | 1: A3.8 |
| Price Index Reference (for example a published construction cost or producer price series) | 1: A3.9 |
| Labelled Document Corpus | 1: A4.1 |
| Claim and Notice Register | 1: A4.7 |
| Subcontractor Assessment Record | 1: A4.8 |
| Specification Conflict Register | 1: A4.10 |
| DSM Dependency Matrix | 1: A5.1 |
| Rework Stock and Flow Series | 1: A5.5 |
| Queue Observation Log | 1: A5.6 |
| DES Event Definition Set | 1: A5.8 |
| Quality Audit Report (already a supported document type) | 1: A6.1 |
| Safety Report (already a supported document type) | 1: A6.2 |
| Environmental Report (already supported) plus Regulatory Applicability Record | 1: A6.3 |
| Official Past Performance Information | 1: A6.4 |
| none proposed: the motivating empirical phenomenon would itself have to be demonstrated first | 1: B2.9 |
| Decision Alternatives Table plus Objective and Constraint Set | 1: B4.1 |
| Decision Alternatives Table plus Scenario Assumption Set | 1: B4.5 |
| Source Reliability Record | 1: C1.3 |
| Audit Object Graph | 1: C1.4 |
| Field-Level Provenance | 1: C1.6 |

## 5. Shared work packages

`code_audit/run27_remediation_work_packages.csv`. The served list and count of every package are derived from the matrix and checked against it, so a package cannot claim a module the matrix does not assign to it.

| Package | Modules | Shared structure | Run |
|---|---|---|---|
| **PKG-ELICIT** Elicitation and evidence-parameter package | 18 | Elicited Assessment Set: expert id, object assessed, linguistic or interval assessment, protocol, date, agreed aggregation rule, agreement statistic… | Run 30 |
| **PKG-CAL-BANDS** Band calibration and empirical validation package | 10 | no new evidence structure: these modules already receive every input their canonical method needs… | Run 33 |
| **PKG-ALTERNATIVES** Alternatives, objectives and constraints package | 9 | Decision Alternatives Table and Objective and Constraint Set: actions, decision variables with bounds and units, objective coefficients and sense, con… | Run 32 |
| **PKG-CAT9** Category-9 qualification and lineage package | 9 | Qualified Signal State per signal, a declared dependence structure over signals, Field Provenance Record, Audit Object Graph, Reporting Cadence and Fr… | Run 31 |
| **PKG-PORTFOLIO-HISTORY** Portfolio cohort and history package | 7 | Portfolio Cohort Definition and Portfolio Reporting History: inclusion criteria, minimum cohort size, per-project per-period readings, vintage… | Run 32 |
| **PKG-SCHEDNET** Schedule network package | 6 | Schedule Network Data: activities, relationships, calendars, float, status date; with activity duration distributions and a risk-event mapping for the… | Run 28 |
| **PKG-HISTORY** Reporting history and time-series package | 5 | Reporting History Series per project, and Milestone Forecast History with stable milestone ids… | Run 28 |
| **PKG-CONTRACT** Contract, procurement and quantity baseline package | 4 | Contract Baseline Data: schedule of values, approved rates and quantities, material baseline, contingency allocations and drawdowns, independent estim… | Run 28 |
| **PKG-DENOM** Document event denominator package | 3 | Document Event Denominator: for every counted document event, the exposure window or exposure quantity it is counted against… | Run 29 |
| **PKG-DOCEVENT** Document event evidence package | 3 | Claim and Notice Register, Specification Conflict Register with evidence locations, Subcontractor Assessment Record… | Run 29 |
| **PKG-ORPHANFIELDS** Orphan extracted-field wiring package | 3 | no new structure at all: join already-extracted safety, quality and environmental fields to the modules named for them… | Run 31 |
| **PKG-QUEUE** Queue, agent and discrete-event package | 3 | Queue Observation Log, Agent and Resource Definition Set, DES Event Definition Set… | Run 29 |
| **PKG-REFCLASS** Reference-class package | 3 | Reference-Class Dataset: completed projects with inclusion criteria, type, baseline, outcome, normalisation variables and vintage… | Run 28 |
| **PKG-REG** Regulatory evidence package | 3 | Regulatory Applicability Record: authority, instrument, clause, version, effective date, jurisdiction, applicability predicate, the level the instrume… | Run 31 |
| **PKG-SCENARIO** Scenario and input-range package | 3 | Scenario Assumption Set and Input Range Declaration… | Run 29 |
| **PKG-DSM** DSM and system model package | 2 | DSM Dependency Matrix and Rework Stock and Flow Series… | Run 29 |
| **PKG-EXTERNAL** External official data package | 2 | External Price Index Record and Past Performance Information Record… | Run 28 |
| **PKG-TIMEPHASED** Time-phased baseline curve package | 2 | Time-Phased Baseline Curve: per-period planned value, cumulative planned value, baseline id and approval date… | Run 28 |
| **PKG-DOCLABEL** Document risk label and validation package | 1 | Labelled Document Corpus with a frozen train, calibration and holdout split… | Run 29 |
| **PKG-RISKQUANT** Quantified risk register package | 1 | Quantified Risk Register: per risk, probability, cost and schedule impact distributions, correlation, realisation status, cost-account mapping… | Run 28 |

**Where one structure enables several modules**, which is the point of the grouping:

- **PKG-ELICIT** (18 modules): B2.1 Dempster-Shafer; B2.2 Rough Sets; B2.3 Neutrosophic Logic; B2.4 Interval Fuzzy Sets; B2.5 Z-numbers; B2.6 PLTS; B2.7 Plithogenic Sets; B2.8 Belief Rule Base; B2.9 Quantum Probability; B2.10 Pythagorean Fuzzy Sets; B2.11 Picture Fuzzy Sets; B2.12 Hesitant Fuzzy Sets; B2.13 Type-2 Fuzzy Sets; B2.14 Maximum Entropy; B2.15 Possibility Theory; B2.16 Spherical Fuzzy Sets; B2.17 Fermatean Fuzzy Sets; B2.20 Hypersoft Sets
- **PKG-CAL-BANDS** (10 modules): A1.1 Monte Carlo EAC; A2.5 Float Consumption Rate; A2.8 Look-Ahead Schedule Health; A2.9 Resource Loading Index; A4.2 RFI Velocity; A4.3 Submittal Rejection Rate; A4.5 Weather Day Impact; A4.9 Procurement Lead Time Monitor; C1.1 Missing Data Index; C1.5 Information Completeness Ratio
- **PKG-ALTERNATIVES** (9 modules): B2.18 MARCOS Ranking; B2.19 CRITIC-TOPSIS; B4.1 Multi-Objective Optimization; B4.2 Linear Programming; B4.3 Constraint Satisfaction Analysis; B4.4 What-If Scenario Matrix; B4.5 Decision Sensitivity Matrix; B4.6 Pareto Frontier Analysis; B4.7 Regret Minimization Index
- **PKG-CAT9** (9 modules): B1.2 Weighted Voting; B1.3 Majority Rules; B1.4 Worst-N-of-M; B3.1 ABM Governance Layer; C1.2 Data Timeliness Score; C1.3 Source Reliability Weighting; C1.4 Audit Trail Completeness; C1.6 Cross-document Consistency Score; C1.7 Reporting Frequency Index
- **PKG-PORTFOLIO-HISTORY** (7 modules): A1.9 Budget Execution Rate; A1.10 Regression to Mean CPI; D1.1 Isolation Forest; D1.2 Portfolio Outlier Detection; D1.3 Signal Trajectory Classifier; D1.4 Cross-project Pattern Detector; D1.5 Anomaly Score
- **PKG-SCHEDNET** (6 modules): A2.1 PERT Network Criticality; A2.2 Line of Balance; A2.3 CCPM Buffer Health; A2.4 Schedule Compression Index; A2.10 Schedule Risk Analysis P80; A2.11 Critical Path Index

Three packages deserve naming in prose.

**PKG-ORPHANFIELDS — Orphan extracted-field wiring package.** THE CHEAPEST PACKAGE IN THE PROGRAMME AND THE ONLY ONE THAT NEEDS NO NEW EVIDENCE. environmentalComplianceRate, qualityAuditScore, totalFindings, criticalFindings, oshaIncidentRate and totalManhours are extracted and consumed by no registered module, while the three modules named for them read meeting-minute proxies.

**PKG-ALTERNATIVES — Alternatives, objectives and constraints package.** ONE STRUCTURE UNBLOCKS THE WHOLE OF CATEGORY 10 PLUS TWO CATEGORY 7 MODULES. It is the highest module-per-structure ratio in the programme after the orphan-field package. The platform already collects courses of action from participants, which is the nearest existing thing to an alternatives table and should be examined before a new form is designed.

**PKG-CAT9 — Category-9 qualification and lineage package.** THIS PACKAGE IS BLOCKED BY THE PLATFORM FREEZE AND RUN 27 RECORDS THAT RATHER THAN WORKING AROUND IT. Production's own disclosure is the finding: 205 of the 397 document-to-module edges land inside the four downstream categories that the gate would qualify.

## 6. Parsimony findings

Classification across the 97: `KEEP_AND_SUPPLY` 52, `CONSOLIDATE_CANDIDATE` 16, `KEEP_AS_TRUTHFUL_PROXY` 12, `KEEP_RESEARCH_ONLY` 10, `KEEP_CONDITIONAL` 3, `OWNER_DECISION_REQUIRED` 2, `RENAME` 2.

Every redundancy claim below is established by property testing over the live production functions or by an argument over the whole input domain, re-derived every time `server/tools/test_run27_parsimony_proofs.py` runs and written to `code_audit/run27_parsimony_property_tests.csv`. **Three of the eight verdicts are negative.**

### Worst-N-of-M vs Conservative Dominance

- Claim tested: *the two are redundant*
- Method: counterexample over the live functions on one assembled project
- **Verdict: REFUTED**
- Evidence: one Red primary signal plus forty Green module signals gives B1.1=Red and B1.4=Green. They read different input sets (B1.1 reads four primary signals, B1.4 reads the primary signals AND the whole simulation signal array) and apply different aggregations (maximum versus a proportional count). Keep both.

### Worst-N-of-M denominator

- Claim tested: *B1.4's verdict is invariant to the size of the module registry*
- Method: same adverse evidence evaluated against two signal-array lengths
- **Verdict: REFUTED**
- Evidence: identical primary signals and three Red module signals give Red when the array holds three modules and Yellow when it holds sixty-three. Registering more modules dilutes the adverse fraction. This is structural, not a calibration gap.

### Constraint Satisfaction Analysis

- Claim tested: *B4.3 is a constraint-satisfaction solver*
- Method: source inspection plus an exhaustive implication check over the cost-index domain
- **Verdict: REFUTED**
- Evidence: Four fixed threshold tests with no variables, no domains and no search. Rule 1 (CPI >= 0.90) implies rule 4 (CPI > 0.80) at every cost index, checked exhaustively at 0.001 resolution over [0, 3] with zero counterexamples, so the satisfaction rate gives cost two of its four items and schedule and document risk one each. The truthful checklist reading is correct and the rename is the remediation; the duplicated cost rule is a separate, provable defect.

### Overlapping fuzzy-set variants

- Claim tested: *the B2 fuzzy variants are mathematically redundant with one another*
- Method: property testing over 5166 admissible (cpi, spi, docRiskScore) points
- **Verdict: NOT ESTABLISHED**
- Evidence: no identical pair among ['B2.10', 'B2.11', 'B2.12', 'B2.13', 'B2.14', 'B2.15', 'B2.16', 'B2.17']; pairwise band agreement ranges 0.3159 to 0.9783. They differ, so none may be deleted on a redundancy proof. What IS established is informational redundancy: all of them read only cpi, spi and docRiskScore, and ['B2.14', 'B2.17'] are functions of min(cpi, spi) alone. They differ in their band boundaries, not in their evidence. CONSOLIDATE_CANDIDATE, owner decision.

### Abstention is not identity

- Claim tested: *B2.3, B2.4, B2.5 and B2.6 are identical to one another*
- Method: re-examination of a first-pass grid result
- **Verdict: REFUTED AS AN ARTEFACT**
- Evidence: All four abstain on this input shape, so their 'identical' band vectors were columns of None. The check above excludes any module that never bands rather than counting it as a match. Recorded because it would have been a false redundancy finding.

### Overlapping anomaly / outlier portfolio methods

- Claim tested: *D1.1, D1.2 and D1.5 are three independent portfolio anomaly readings*
- Method: source inspection of server/app/simulation/portfolio.py
- **Verdict: REFUTED**
- Evidence: D1.5 Anomaly Score is the mean of (a) a standardised Mahalanobis distance that portfolio.py's own comment records as the quantity formerly mislabelled the isolation forest score, (b) one minus D1.2's composite percentile rank, and (c) when history allows, a term in D1.3's trend. Two of its at most three terms are other registered modules' internals, and it does not read D1.1. It is a dependent composite presented beside its own components. CONSOLIDATE_CANDIDATE and a P0 lineage finding.

### Duplicate document-risk indicators

- Claim tested: *A4.10 Specification Conflict Density carries evidence of its own*
- Method: invariance property testing over sixteen perturbations of every other input
- **Verdict: REFUTED**
- Evidence: A4.10's band is unchanged across all sixteen perturbations of budget, actual cost, earned value and percent complete, and moves only with the document risk score and the request count. Both are already registered inputs consumed elsewhere (A4.1 and A4.2), and A4.7 Dispute Escalation Index forms a weighted sum over the same two plus the change order count. Three registered modules over one pair of primitives. CONSOLIDATE_CANDIDATE.

### Duplicate schedule-health indicators

- Claim tested: *A2.11 Critical Path Index and A5.8 Discrete Event Simulation are redundant*
- Method: invariance property testing plus a differing-output check over the shared input pair
- **Verdict: NOT ESTABLISHED**
- Evidence: Both are functions of the schedule performance index and the reported-over-planned progress ratio ALONE, invariant across thirty-two perturbations of every other input, so they share their entire evidence base with each other and with A2.10. They are not the same function of that pair, so neither may be deleted on a redundancy proof. The finding is informational: three registered modules, two primitives, and two of the three names assert a network or a simulation that does not exist.

### ABM Governance versus the Action Boundary / Authority structure

- Claim tested: *B3.1 is an agent-based model*
- Method: source inspection of the live function
- **Verdict: REFUTED**
- Evidence: B3.1 maps the decision-layer state to the action to take and the authority that may take it, and returns exactly those two things plus a fairness gate. There is no agent, no interaction structure and no time step anywhere in it. The mapping IS the action-boundary and authority structure the platform needs and should be kept; only the name is wrong. RENAME, not remove. Separately it declares raw cpi, spi and docRiskScore as required inputs, which specification section 18 forbids in those words, and that is the P0.

### Duplicate change / modification counters

- Claim tested: *A4.6 and B3.5 are the same module twice*
- Method: field-set comparison on the authoritative edge list plus a band comparison
- **Verdict: PARTLY ESTABLISHED**
- Evidence: Both consume exactly the same document-emitted fields (['baselineContractSum', 'changeOrderCount']) and both are counts with no exposure denominator. Their bands are A4.6=['Green', 'Amber', 'Red', 'Red'] and B3.5=['Green', 'Amber', 'Red', 'Red'] over the same change order counts, so they are not the identical function and neither may be deleted on a proof. Two registered modules over one pair of inputs is a CONSOLIDATE_CANDIDATE for the owner.

### Truthful rename candidates

40 of the 97 carry one. The registered name and the truthful name are both already published by production on the interface response, the export and the methods documentation; what a participant reads is unchanged and changing it is an instrument decision for the owner, not a remediation.

| id | registered | truthful |
|---|---|---|
| A1.5 | ARIMA CPI Forecast | Fixed-order one-step cost index projection |
| A1.6 | Earned Schedule | Reported against planned progress ratio |
| A1.9 | Budget Execution Rate | Expenditure against progress control ratio |
| A1.10 | Regression to Mean CPI | Fixed shrinkage toward the project's own history |
| A1.11 | ICE Ratio | Internal completion forecast divergence index |
| A2.4 | Schedule Compression Index | Reported duration compression ratio |
| A2.6 | S-Curve Deviation | Planned versus actual progress snapshot |
| A2.7 | Milestone Trend Analysis | Period-on-period milestone forecast drift |
| A2.10 | Schedule Risk Analysis P80 | Deterministic schedule uplift on the remaining duration |
| A2.11 | Critical Path Index | Mean of the progress ratio and the schedule index |
| A3.3 | Labor Productivity Index | Labour hours against reported progress ratio |
| A3.6 | Cost Risk Analysis P80 | Deterministic cost uplift on the index-based forecast |
| A3.8 | Parametric Cost Index | Disabled: no parametric estimating relationship is implemented |
| A3.9 | Inflation Adjustment Index | Material cost ratio without an external price index |
| A4.5 | Weather Day Impact | Lost days against available float |
| A4.6 | Change Order Frequency | Change order count with contract growth |
| A4.7 | Dispute Escalation Index | Weighted project stress composite |
| A4.10 | Specification Conflict Density | Document risk weighted by request volume |
| A5.2 | Sensitivity Analysis | Local cost index perturbation with present-state deviations |
| A5.3 | Tornado Risk Ranking | Ranked present-state deviations |
| A5.5 | Rework Feedback Loop | Weighted rework pressure composite |
| A5.8 | Discrete Event Simulation | Throughput index from the schedule index and progress ratio |
| A6.4 | Contractor Performance Score | Project-document contractor estimate |
| B1.2 | Weighted Voting | Fixed-weight signal band tally |
| B2.2 | Rough Sets | Supermajority band classification over bodies of evidence |
| B2.7 | Plithogenic Sets | Disabled: no plithogenic structure is implemented |
| B2.9 | Quantum Probability | Disabled: no quantum probability model is implemented |
| B2.14 | Maximum Entropy | Entropy of a designed band lookup |
| B2.18 | MARCOS Ranking | Single-project criterion scoring against designed reference points |
| B2.20 | Hypersoft Sets | Disabled: no hypersoft structure is implemented |
| B3.1 | ABM Governance Layer | Action boundary and authority matrix |
| B3.5 | Contract Modification Frequency | Contract modification count |
| B4.1 | Multi-Objective Optimization | Disabled: no objectives, decision variables or feasible set are implemented |
| B4.2 | Linear Programming | Disabled: no decision variables, objective or constraints are implemented |
| B4.3 | Constraint Satisfaction Analysis | Four-rule project condition check |
| B4.4 | What-If Scenario Matrix | Earned value completion forecast range |
| B4.5 | Decision Sensitivity Matrix | Disabled: no decisions and no sensitivities are implemented |
| B4.6 | Pareto Frontier Analysis | Disabled: no alternative set and no dominance relation are implemented |
| C1.4 | Audit Trail Completeness | Declared audit field presence check |
| C1.6 | Cross-document Consistency Score | Reported index self-consistency check |

### Consolidation and removal candidates

**Run 27 removes nothing and consolidates nothing.** Each of the following is a recommendation to the owner, and the guard asserts that every row marked a redundancy candidate says so in its own owner-decision cell.

- **A4.10 Specification Conflict Density** — No conflict is located in any document, so nothing is counted as a conflict. The computation is a strict function of the document risk score and the request count, both of which are already registered inputs elsewhere, so it adds no evidence of its own.
- **A5.3 Tornado Risk Ranking** — Ranks four present-state deviations by magnitude. Once input ranges exist, A5.2 and A5.3 are two presentations of one computation and consolidation should be considered.
- **B2.3 Neutrosophic Logic** — Reads the same two indices and the document risk score as the rest of the B2 family.
- **B2.4 Interval Fuzzy Sets** — Interval widths are design constants, so the interval measures the design, not the uncertainty.
- **B2.5 Z-numbers** — The reliability component needs an assessed reliability; none is elicited.
- **B2.6 PLTS** — Requires linguistic assessments from people; none are collected.
- **B2.10 Pythagorean Fuzzy Sets** — Hard-coded transformations of raw cost index, schedule index and document risk.
- **B2.11 Picture Fuzzy Sets** — Hard-coded memberships consuming raw metrics.
- **B2.12 Hesitant Fuzzy Sets** — Designed perturbations stand in for hesitant assessments; hesitancy that is manufactured measures the manufacturing rule.
- **B2.13 Type-2 Fuzzy Sets** — Membership intervals are designed constants.
- **B2.15 Possibility Theory** — Fixed mappings from raw metrics; no governed distribution.
- **B2.16 Spherical Fuzzy Sets** — Algebraically bounded but fixed memberships on raw unqualified inputs.
- **B2.17 Fermatean Fuzzy Sets** — Property testing over a 5,166-point grid shows its band is a function of min(cpi, spi) ALONE, so it carries strictly less information than its three-input siblings.
- **B3.5 Contract Modification Frequency** — Reads exactly the same two extracted fields as A4.6 Change Order Frequency (baselineContractSum, changeOrderCount) per the authoritative edge list. Two registered modules over one pair of inputs.
- **C1.5 Information Completeness Ratio** — Measures completeness against a declared set, as C1.1 does. Whether two registered modules are needed for completeness is a parsimony question for the owner.
- **D1.5 Anomaly Score** — This is the portfolio double-counting finding, provable from the source rather than asserted: D1.5 is a strict function of D1.2's and D1.3's internals plus a distance quantity that portfolio.py itself records as the one formerly mislabelled the isolation forest score. It does not read D1.1. P0 on lineage grounds.

## 7. Disabled and research-only methods

Registry status established mechanically from `server/app/simulation/registry.py` rather than from a historical count. `DISABLED_CONCEPT_ONLY` holds eight modules whose formula functions are never called; `DISABLED_EVIDENCE_UNDER_REVIEW` holds one, A3.4, which is outside this population. **No disabled module is activated by this run and none is proposed for activation; the guard checks that every disabled row's operational destination says it remains disabled.**

| id | name | status | structure suppliable? | scientific value shown | operational value shown | recommendation |
|---|---|---|---|---|---|---|
| A3.8 | Parametric Cost Index | DISABLED_UNSAFE | yes, with a cost-driver reference dataset | no | no | leave disabled; revisit when the Reference-Class Dataset exists |
| B2.7 | Plithogenic Sets | DISABLED_UNSAFE | yes in principle, by elicitation | no | no | leave disabled, research-only |
| B2.9 | Quantum Probability | DISABLED_UNSAFE | no: the motivating phenomenon would have to be demonstrated first | no | no | leave disabled; strongest REMOVE_CANDIDATE on parsimony grounds, owner decides |
| B2.20 | Hypersoft Sets | DISABLED_UNSAFE | only if the platform ever ranks a real object set | no | no | leave disabled, research-only |
| B4.1 | Multi-Objective Optimization | DISABLED_UNSAFE | yes, with the Decision Alternatives Table | no | plausible but unshown | leave disabled; revisit in Run 32 once the alternatives structure exists |
| B4.2 | Linear Programming | DISABLED_UNSAFE | yes, with the Objective and Constraint Set | no | plausible but unshown | leave disabled; revisit in Run 32 |
| B4.5 | Decision Sensitivity Matrix | DISABLED_UNSAFE | yes, with alternatives plus input ranges | no | no | leave disabled |
| B4.6 | Pareto Frontier Analysis | DISABLED_UNSAFE | yes, with two or more alternatives on two or more objectives | no | plausible but unshown | leave disabled; revisit in Run 32 |

**Plithogenic Sets, Quantum Probability and Hypersoft Sets are all still disabled**, as the historical statement said, and the registry confirms it rather than the report asserting it. Assessed individually as instructed:

- **B2.7 Plithogenic Sets.** Needs an attribute set with degrees of appurtenance and a contradiction degree between attribute values. That is suppliable by elicitation, so it is not impossible; but no operational question this platform asks is currently expressed in plithogenic terms, and no scientific or operational value has been demonstrated. Leave disabled, research-only.
- **B2.9 Quantum Probability.** Unlike the rest of the family this is *not* merely an elicitation gap. Quantum probability is warranted where judgments violate classical additivity, and no such violation has been observed in this platform's data or could be observed without the elicited assessments that do not exist. Its supply mechanism is recorded as `NOT_REASONABLY_SUPPLIABLE`, the only row in the matrix that carries it. It is the strongest removal candidate in the population. **Removal is the owner's decision and this run does not take it.**
- **B2.20 Hypersoft Sets.** A hypersoft set is a mapping from tuples of attribute values to subsets of a *universe of objects*, and a single project is not a universe. Suppliable only if the platform ever ranks a real alternative or project set, which is the same `PKG-ALTERNATIVES` structure Category 10 needs. Leave disabled, research-only.

Two further modules are `KEEP_RESEARCH_ONLY` while remaining `ADVISORY_ONLY` and therefore live on the ledger: **A5.7 Agent-Based Supply Chain** and **A5.8 Discrete Event Simulation**. A5.8 is P1 rather than P3 despite the research classification, because its registered name asserts a simulation that does not exist and that is a truthfulness problem now, not later.

## 8. Run 28 to 33 assignment

**Zero orphans, checked by the guard.** Every row carries a primary run and a secondary. A row whose remaining work is calibration and validation only is assigned primarily to Run 33 with its category run recorded beside it; every other row terminates in Run 33 because Run 33 carries the complete hundred-target re-audit.

| Run | Scope | Rows (primary) |
|---|---|---|
| Run 28 | Categories 1 to 3: cost, EVM, schedule and cost-risk structures | 24 |
| Run 29 | Categories 4 to 5: document/risk evidence and system-model structures | 14 |
| Run 30 | Categories 6 to 7: signal synthesis and epistemic/evidence methods | 23 |
| Run 31 | Categories 8 to 9: governance, regulatory evidence, data integrity, Category-9 | 14 |
| Run 32 | Category 10 plus Portfolio Health: decision optimization and portfolio methods | 12 |
| Run 33 | Calibration, empirical validation, final parsimony decisions, complete re-audit | 10 |

## 9. Priority distribution

Assigned on evidence, not category number.

| Priority | Rows | Definition |
|---|---|---|
| `P0` | 13 | needed to prevent scientifically unsupported operational output |
| `P1` | 61 | necessary to make an intended operational method actually runnable |
| `P2` | 14 | necessary for calibration and validation after correct execution exists |
| `P3` | 9 | research expansion or optional complexity |

The P0 set, and why each is there:

- **A2.10 Schedule Risk Analysis P80** — Nothing is sampled and the reported figure is not a percentile of anything, so the registered name asserts a quantity that does not exist. P0 because the output is presented as a percentile.
- **A2.11 Critical Path Index** — Neither a network nor a simulation run exists, so no activity is identified as critical at all. P0 for the same reason as A2.10.
- **A3.6 Cost Risk Analysis P80** — A risk_register document type is declared but emits no probability and no impact distribution, so a list of risks is not a quantified register. P0 because a percentile is reported where nothing is sampled.
- **A4.1 Document Risk Score** — Supplied by the extraction model rather than computed by the analytical server, and it is the single most widely consumed input in the system: it reaches at least twenty-eight registered modules on the authoritative edge list. An unvalidated score with that fan-out is a P0.
- **A6.1 Quality Compliance Index** — This is the orphan-field finding: the evidence exists in the corpus, is extracted, and is not consumed. P0 because the module reads a weaker proxy while the real evidence sits unused.
- **A6.2 Safety Performance Index** — Same orphan-field finding as A6.1. A safety rate computed from a count of mentions in minutes, while the recordable count and manhours sit extracted and unread, is the clearest case in the population.
- **A6.3 Environmental Compliance Rate** — Carries BOTH open findings at once: an orphan extracted field and a REGULATORY_VERSION_BLOCKED disposition. The permit authority, jurisdiction and version of the conditions assessed are not carried.
- **B1.2 Weighted Voting** — Four design-constant weights with no source, applied to signals that are not qualified. P0: it is a synthesis feeding presentation.
- **B1.3 Majority Rules** — A counting rule over correlated readings counts one measurement more than once. Run 20 Cycle 9 established exactly this for B1.1 and fixed B1.1 only.
- **B1.4 Worst-N-of-M** — Its denominator is the whole simulation signal array, so the fraction of adverse signals shrinks as more modules are registered. That is a structural defect of a proportional rule over a growing module set and is independent of calibration.
- **B3.1 ABM Governance Layer** — The mapping from decision-layer state to action and authority is sound and is what the platform actually needs; nothing about it is agent based. It ALSO declares raw cpi, spi and docRiskScore as required inputs, which specification section 18 forbids in those words, and that is the P0 rather than the naming.
- **C1.6 Cross-document Consistency Score** — Every figure compared today comes from the same assembled set, so no fact is compared across two documents and no document is identified as the source of any disagreement. The merge layer knows which document won each field; that knowledge is discarded before the module sees it. P0 because the module's name asserts a cross-document check that never happens.
- **D1.5 Anomaly Score** — This is the portfolio double-counting finding, provable from the source rather than asserted: D1.5 is a strict function of D1.2's and D1.3's internals plus a distance quantity that portfolio.py itself records as the one formerly mislabelled the isolation forest score. It does not read D1.1. P0 on lineage grounds.

## 10. Owner decisions required

| id | decision |
|---|---|
| A1.5 ARIMA CPI Forecast | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| A1.6 Earned Schedule | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| A1.9 Budget Execution Rate | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| A1.10 Regression to Mean CPI | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| A1.11 ICE Ratio | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| A2.2 Line of Balance | yes: applicability to this platform's projects is a scoping decision. |
| A2.3 CCPM Buffer Health | yes: applicability to this platform's projects is a scoping decision. |
| A2.4 Schedule Compression Index | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| A2.6 S-Curve Deviation | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| A2.7 Milestone Trend Analysis | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| A2.10 Schedule Risk Analysis P80 | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| A2.11 Critical Path Index | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| A3.3 Labor Productivity Index | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| A3.6 Cost Risk Analysis P80 | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| A3.8 Parametric Cost Index | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| A3.9 Inflation Adjustment Index | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| A4.1 Document Risk Score | yes: applicability to this platform's projects is a scoping decision. |
| A4.5 Weather Day Impact | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| A4.6 Change Order Frequency | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| A4.7 Dispute Escalation Index | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| A4.10 Specification Conflict Density | yes: consolidation or removal is a RECOMMENDATION only. Run 27 removes nothing and consolidates nothing. |
| A5.2 Sensitivity Analysis | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| A5.3 Tornado Risk Ranking | yes: consolidation or removal is a RECOMMENDATION only. Run 27 removes nothing and consolidates nothing. |
| A5.5 Rework Feedback Loop | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| A5.8 Discrete Event Simulation | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| A6.4 Contractor Performance Score | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| B1.2 Weighted Voting | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| B2.2 Rough Sets | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| B2.3 Neutrosophic Logic | yes: consolidation or removal is a RECOMMENDATION only. Run 27 removes nothing and consolidates nothing. |
| B2.4 Interval Fuzzy Sets | yes: consolidation or removal is a RECOMMENDATION only. Run 27 removes nothing and consolidates nothing. |
| B2.5 Z-numbers | yes: consolidation or removal is a RECOMMENDATION only. Run 27 removes nothing and consolidates nothing. |
| B2.6 PLTS | yes: consolidation or removal is a RECOMMENDATION only. Run 27 removes nothing and consolidates nothing. |
| B2.7 Plithogenic Sets | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| B2.9 Quantum Probability | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| B2.10 Pythagorean Fuzzy Sets | yes: consolidation or removal is a RECOMMENDATION only. Run 27 removes nothing and consolidates nothing. |
| B2.11 Picture Fuzzy Sets | yes: consolidation or removal is a RECOMMENDATION only. Run 27 removes nothing and consolidates nothing. |
| B2.12 Hesitant Fuzzy Sets | yes: consolidation or removal is a RECOMMENDATION only. Run 27 removes nothing and consolidates nothing. |
| B2.13 Type-2 Fuzzy Sets | yes: consolidation or removal is a RECOMMENDATION only. Run 27 removes nothing and consolidates nothing. |
| B2.14 Maximum Entropy | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| B2.15 Possibility Theory | yes: consolidation or removal is a RECOMMENDATION only. Run 27 removes nothing and consolidates nothing. |
| B2.16 Spherical Fuzzy Sets | yes: consolidation or removal is a RECOMMENDATION only. Run 27 removes nothing and consolidates nothing. |
| B2.17 Fermatean Fuzzy Sets | yes: consolidation or removal is a RECOMMENDATION only. Run 27 removes nothing and consolidates nothing. |
| B2.18 MARCOS Ranking | yes: A ranking method over one alternative returns that alternative. Either a real alternative set is supplied or the module is not a ranking method; the owner decides which. |
| B2.20 Hypersoft Sets | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| B3.1 ABM Governance Layer | yes: the served participant surface is frozen and checksummed and the study is mid-sequence, so a rename on the participant surface is an instrument decision for the owner, not a remediation. |
| B3.5 Contract Modification Frequency | yes: consolidation or removal is a RECOMMENDATION only. Run 27 removes nothing and consolidates nothing. |
| B4.1 Multi-Objective Optimization | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| B4.2 Linear Programming | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| B4.3 Constraint Satisfaction Analysis | yes: the served participant surface is frozen and checksummed and the study is mid-sequence, so a rename on the participant surface is an instrument decision for the owner, not a remediation. |
| B4.4 What-If Scenario Matrix | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| B4.5 Decision Sensitivity Matrix | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| B4.6 Pareto Frontier Analysis | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| C1.4 Audit Trail Completeness | yes: The objects exist in this platform's own database; the module counts declared field presence instead of assessing them. This is the rare row where the missing structure is already inside the application rather than outside it. |
| C1.5 Information Completeness Ratio | yes: consolidation or removal is a RECOMMENDATION only. Run 27 removes nothing and consolidates nothing. |
| C1.6 Cross-document Consistency Score | yes: whether the truthful name replaces the registered name on the participant surface is an instrument decision. |
| D1.5 Anomaly Score | yes: consolidation or removal is a RECOMMENDATION only. Run 27 removes nothing and consolidates nothing. |

The standing decisions, grouped:

1. **Whether any truthful name replaces a registered name on the participant surface.** 40 modules are affected. The surface is frozen and checksummed and the study is mid-sequence, so this is an instrument decision with protocol consequences.
2. **Whether the fuzzy-set family is consolidated.** Thirteen Category-7 modules are `CONSOLIDATE_CANDIDATE`. Property testing establishes they are *not* mathematically identical, so none may be deleted on a proof; it also establishes they read the same two or three raw inputs and differ only in their band boundaries.
3. **Whether B2.9 Quantum Probability is retained at all.** The only `NOT_REASONABLY_SUPPLIABLE` row in the matrix.
4. **Whether A4.6 and B3.5 remain two modules**, given they consume an identical field set.
5. **Whether D1.5 Anomaly Score is recomposed or withdrawn**, given it is a strict function of D1.2's and D1.3's internals.
6. **Whether line of balance and CCPM buffer health are applicable at all** to this platform's projects, which is scoping rather than data.
7. **A3.4 Material Cost Variance**, retained behind the contract and procurement baseline package or removed. Deferred since Run 16 and unchanged here.
8. **C1.4 Audit Trail Completeness** and **B2.18 MARCOS Ranking**, both recorded `OWNER_DECISION_REQUIRED` by the re-audit itself.

## 11. Non-vacuity proof

Two new suites, both in the runner. `test_run27_remediation_matrix.py` is 47 checks; `test_run27_parsimony_proofs.py` is 25 and re-derives every parsimony claim from the live production functions.

`server/tools/run27_fault_campaign.py` injects the six mandated faults. For each it applies the mutation, **re-reads the file from disk and asserts the specific structural change so an injection that silently failed to apply halts the campaign rather than reporting a clean restore**, runs the guard as a separate process, requires a non-zero exit *and* a canonical RESULT line *and* the named check among the failures, then restores from a byte-exact backup and re-checks the baseline to full green. A run with no RESULT line is recorded `CRASH_NOT_RED` and fails the campaign: a crash is not red.

| Fault | Injection confirmed | Guard exit | Verdict | Detail |
|---|---|---|---|---|
| BASELINE (before any injection) | n/a | 0 | **GREEN** | 47/47 |
| F1 omit one of the non-pass targets (A5.6 Queueing Theory Bottleneck) | YES | 1 | **RED_FOR_THE_INTENDED_REASON** | 44/47; missing non-pass targets = 0 :: ['A5.6'] |
| F1 omit one of the non-pass targets (A5.6 Queueing Theory Bottleneck) :: RESTORED AND BASELINE RE-CHECKED | n/a | 0 | **GREEN** | 47/47 |
| F2 duplicate one module (A1.2 CUSUM Anomaly Monitor appears twice) | YES | 1 | **RED_FOR_THE_INTENDED_REASON** | 44/47; duplicate rows = 0 :: ['A1.2'] |
| F2 duplicate one module (A1.2 CUSUM Anomaly Monitor appears twice) :: RESTORED AND BASELINE RE-CHECKED | n/a | 0 | **GREEN** | 47/47 |
| F3 include a SCIENTIFIC_PASS module (A1.7 TCPI smuggled into the matrix) | YES | 1 | **RED_FOR_THE_INTENDED_REASON** | 44/47; SCIENTIFIC_PASS targets accidentally included = 0 :: ['A1.7'] |
| F3 include a SCIENTIFIC_PASS module (A1.7 TCPI smuggled into the matrix) :: RESTORED AND BASELINE RE-CHECKED | n/a | 0 | **GREEN** | 47/47 |
| F4 remove the DATA requirement from a DATA row (A2.10 missing evidence emptied) | YES | 1 | **RED_FOR_THE_INTENDED_REASON** | 45/47; DATA rows without a stated missing input = 0 :: ['A2.10'] |
| F4 remove the DATA requirement from a DATA row (A2.10 missing evidence emptied) :: RESTORED AND BASELINE RE-CHECKED | n/a | 0 | **GREEN** | 47/47 |
| F5 remove the supply mechanism from that same DATA row (A2.10) | YES | 1 | **RED_FOR_THE_INTENDED_REASON** | 46/47; DATA rows without a proposed supply mechanism = 0 :: ['A2.10'] |
| F5 remove the supply mechanism from that same DATA row (A2.10) :: RESTORED AND BASELINE RE-CHECKED | n/a | 0 | **GREEN** | 47/47 |
| F6 leave one row without a future run (C1.7 Reporting Frequency Index) | YES | 1 | **RED_FOR_THE_INTENDED_REASON** | 45/47; orphan future-run assignments = 0 :: ['C1.7'] |
| F6 leave one row without a future run (C1.7 Reporting Frequency Index) :: RESTORED AND BASELINE RE-CHECKED | n/a | 0 | **GREEN** | 47/47 |

`code_audit/run27_guard_nonvacuity.csv`. All six turned red for the intended reason, all six restored to 47/47, and the baseline was re-checked after every single fault rather than once at the end.

**Two of my own parsimony claims failed their first check and were corrected rather than weakened.** A claimed counterexample for B1.4's growing denominator did not separate the two cases at the point I chose, and a source-string assertion did not match the comment it quoted. Both are recorded here because a suite that only ever confirms the author's expectation is the fourth failure mode.

**One false redundancy finding was caught and is recorded in the suite's own docstring.** A first pass reported B2.3, B2.4, B2.5 and B2.6 as pairwise identical over the grid. They are not: all four abstain on that input shape, so the identical vectors were four columns of `None`. Identity between two abstentions is not redundancy. The check now excludes any module that never produces a band rather than counting it as a match.

## 12. Suite result

SUITE_TOTAL_PLACEHOLDER

## 13. Merged main

MERGE_PLACEHOLDER

## What this run did not do, plainly

- **The Category-9 qualification gate is not closed and could not be.** `server/app/simulation/` is frozen at `sim-2026.08-v2` under a byte-identical guard, and `signal_package.py`, where `SIGNAL_QUALIFICATION = "unqualified"` and `CATEGORY_9_DEVIATION` live, is inside it. `PKG-CAT9` records the block rather than working around it.
- **No production file was changed.** Section 13 permits correcting a mechanically proven registry, name or status inconsistency only where it prevents the matrix being accurate. The one known inconsistency, the registry's `Monte Carlo EAC` against the taxonomy's `Monte Carlo EAC Forecast`, does not: the matrix joins on identity through an explicit alias recorded in the builder. **It therefore remains open and is handed to Run 28.** No freeze record was taken and none was needed.
- **The specification is silent where it is silent, and the silence is reported.** It states no ordering among B1, B2, B3 and B4 and does not say which categories supply the four downstream ones, so no row and no package claims that Categories 6 to 10 form a chain. The authoritative edge list carries five `SILENT` rows for exactly this reason.
- **Three supported document types still emit fields no registered module consumes.** Environmental Report, Quality Audit Report and Safety Report. This is `PKG-ORPHANFIELDS`, the cheapest package in the programme, and it is scheduled rather than fixed because Run 27 is not an implementation run.
- **`VALIDATE` is carried by 88 rows and no row is validated.** No labelled corpus and no expert reference standard exist in this repository. That is not a per-module defect; it is one absent structure, `PKG-DOCLABEL`, and every calibration in the programme waits behind it.

## Artifacts

- `code_audit/run27_98_module_remediation_matrix.csv`
- `code_audit/run27_remediation_work_packages.csv`
- `code_audit/run27_parsimony_property_tests.csv`
- `code_audit/run27_guard_nonvacuity.csv`
- `server/tools/run27_curation.py`
- `server/tools/build_run27_remediation_matrix.py`
- `server/tools/build_run27_report.py`
- `server/tools/run27_fault_campaign.py`
- `server/tools/test_run27_remediation_matrix.py`
- `server/tools/test_run27_parsimony_proofs.py`
