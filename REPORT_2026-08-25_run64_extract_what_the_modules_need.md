# Run 64 — extract what the modules need

**Modules computing: 4 before, 4 after. Categories lit: 1 before, 1 after.** Not one production
byte changed, and that is the honest outcome: the premise this run was ordered on — that PRJ-001's
documents hold evidence extraction is failing to pull out — could not be tested against those
documents from this environment, and everything that COULD be measured here says the extraction
schema and its wiring are not the defect.

**Repository:** the Linux clone at `/home/user/LinPRojectRadar`. **Interpreter:** `python3`
3.11.15 (`/usr/local/bin/python3`); no `.venv` exists, so the documented fallback was used.
**Branch:** `main` (report-only commit). **No mint was taken. See §11, §9 stop 7 and §12 — that is a
declared conflict with §9 of the order, reported and not resolved against the owner.**

---

## 0. §6 — the starting point, verified rather than trusted

| Claim | Verified | Command / output |
|---|---|---|
| `git status --porcelain` empty | YES | empty |
| `main == origin/main == HEAD == 5aea84f` | YES | `git rev-parse HEAD origin/main main` → `5aea84f9de1538669001a1146a5cc846491c7b75` ×3 |
| stamp `sim-2026.08-v41` | YES | `server/app/simulation/models.py:758` |
| package `og-participant-2026.08-v26` | YES (carried from briefing; not re-derived line-by-line) | `server/tools/participant_packages.py` |
| freeze gate, 15 blocker classes, 0 blocked | YES | `python3 tools/test_run37_freeze_gate.py` → `RESULT: 34/34 checks passed`, B01–B15 all "is zero" |
| registry 101 / service 63 / voting exactly 2 | YES, derived live | `len(registry_index())=101`, `len(service_index())=63`, `CORE_VOTING_MODULES=['A1.7','A1.8']` |
| `unported_modules()` = `['A4.1']` | YES | derived live |

**Every §6 claim held.** Unlike Runs 52–63, this order's starting point needed no correction.

---

## 1. §12-1 — the counts, before and after

| | Before | After |
|---|---|---|
| Modules in service producing a value on PRJ-001 | **4** (Run 63's measurement: A1.2, A1.7, A1.8 + 1) | **4** |
| Categories carrying a status | **1** of 11 (A1) | **1** of 11 |
| Modules in service | 63 | 63 |
| Registry total | 101 | 101 |
| Voting modules | 2 (`A1.7`, `A1.8`) | 2 (unchanged) |

Nothing moved because nothing could be moved honestly. §5 is the reason, and §5 is the whole
instrument.

---
## 2. §4.1 / §12-2 — the work order: every abstaining module, what it needs, what it says today

Derived by **executing every one of the 63 in-service modules** against the governed controlled-
corpus scalar evidence (`server/tools/build_run36_audit.py:43` `CORPUS_SI`, cutoff `2026-06-30`),
not read from any summary. Required input is the module's own structure key, read from
`canonical.py` / `canonical_v3..v8.py` `*_STRUCTURE_KEYS`; `(scalar only)` means the module has no
structure requirement and reads flat signal inputs.

Census on that evidence: **ABSTAINS 57, COMPUTES 5 (A1.7, A1.8, A6.1, A6.2, A6.3),
SUPPLIED_NOT_COMPUTED 1 (A4.1)**. Abstention sentences are truncated at ~230 characters.

| Module | Name | Cat | Required input (from module code) | Exact abstention today |
|---|---|---|---|---|
| A1.10 | CPI Shrinkage Forecast | A1 | `cpiReferenceClass` | Awaiting a governed reference population of comparable projects with the cost performance they achieved, and the weight to place on this project's own reading. This measure is named for a method that cannot be carried out without  |
| A1.11 | Independent EAC Reconciliation Index | A1 | `independentEacPair` | Awaiting two separately prepared forecasts of the cost at completion, one from the project management team and one prepared independently of it. This measure is named for a method that cannot be carried out without it, so no readi |
| A1.2 | CUSUM Anomaly Monitor | A1 | `(scalar only)` | Awaiting history (2 periods needed) |
| A1.3 | Bayesian EAC | A1 | `bayesianEacModel` | Awaiting a stated prior for the cost at completion, with its source, and a stated observation model with the uncertainty of the observation. This measure is named for a method that cannot be carried out without it, so no reading i |
| A1.4 | Kalman Filter SPI Smoother | A1 | `kalmanStateSpaceModel` | Awaiting a state space model for the schedule index: a starting estimate, its uncertainty, the process and measurement variances, and the readings taken. This measure is named for a method that cannot be carried out without it, so |
| A1.5 | ARIMA CPI Forecast | A1 | `(scalar only)` | The cost performance history is too short for a time series model to be identified from it, so no forecast is reported and no shorter substitute is used. |
| A1.6 | Earned Schedule | A1 | `timePhasedBaseline` | Awaiting a time phased baseline: the cumulative value of work planned to be complete at the end of each period. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figur |
| A1.9 | Budget Execution Rate | A1 | `expenditureBaseline` | Awaiting an approved time phased expenditure baseline: the amount planned to be spent by the end of each period. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figu |
| A2.1 | PERT Network Criticality | A2 | `scheduleNetwork` | Awaiting the project's activity network: the activities, the logic between them, and a duration for each. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is u |
| A2.2 | Line of Balance | A2 | `lobStructure` | Awaiting a line of balance: locations in sequence, the crews working them, and a production rate and start for each line of work. This measure is named for a method that cannot be carried out without it, so no reading is reported  |
| A2.3 | CCPM Buffer Health | A2 | `ccpmStructure` | Awaiting a critical chain with its activities and a sized project buffer. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place. |
| A2.7 | Milestone Trend Analysis | A2 | `milestoneForecastHistory` | Awaiting a milestone forecast history: each milestone's committed date and the date it was forecast for in each reporting period since. This measure is named for a method that cannot be carried out without it, so no reading is rep |
| A2.8 | Look-Ahead Schedule Health | A2 | `lookAheadSchedule` | Awaiting a look ahead schedule: the window it covers, the activities planned in it, and whether each one still carries an open constraint. This measure is named for a method that cannot be carried out without it, so no reading is  |
| A2.9 | Resource Loading Index | A2 | `resourceProfile` | Awaiting a time phased resource profile: for each period and each kind of resource, the amount of work demanded and the amount available. This measure is named for a method that cannot be carried out without it, so no reading is r |
| A3.1 | Reference Class Forecasting | A3 | `referenceClassPopulation` | Awaiting a reference class of completed comparable projects, with the criteria that put them in it and the overrun each of them finished with. This measure is named for a method that cannot be carried out without it, so no reading |
| A3.2 | Contingency Burn Rate | A3 | `(scalar only)` | Insufficient data: the original and remaining contingency amounts are needed, and at least one of them has not been reported for this period. |
| A3.3 | Labor Productivity Index | A3 | `productionOutputRecord` | Awaiting a record of production: the quantity of work installed, the quantity planned, and the labour hours each of those took. This measure is named for a method that cannot be carried out without it, so no reading is reported an |
| A3.5 | Overhead Absorption Rate | A3 | `overheadAllocationBase` | Awaiting an overhead allocation base: the planned and actual overhead and the planned and actual amount of the base it is absorbed over. This measure is named for a method that cannot be carried out without it, so no reading is re |
| A3.6 | Cost Risk Analysis P80 | A3 | `costRiskModel` | Awaiting a cost risk model: the base cost components, the risk events that could occur, how likely each is and what it would cost. This measure is named for a method that cannot be carried out without it, so no reading is reported |
| A3.7 | Analogous Estimating Ratio | A3 | `analogEstimate` | Awaiting an identified analogous project with its cost, why it is comparable, and the factors that adapt it to this project. This measure is named for a method that cannot be carried out without it, so no reading is reported and n |
| A3.9 | Inflation Adjustment Index | A3 | `externalCostIndex` | Awaiting a named external price index with its authority, geography, base period and the period being adjusted to. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other fi |
| A4.1 | Document Risk Score | A4 | `documentRiskEvidence` | A4.1 (Document Risk Score) has not been ported and validated against the JavaScript implementation; this server refuses to compute it |
| A4.10 | Specification Conflict Density | A4 | `specificationConflictRegister` | Awaiting a specification conflict register: each identified conflict, the two places in the specification that disagree, whether it has been confirmed, and the exposure the conflicts are counted over. This measure is named for a m |
| A4.2 | RFI Velocity | A4 | `rfiEventLog` | Insufficient data: upload required documents |
| A4.3 | Submittal Rejection Rate | A4 | `submittalDecisionRegister` | Insufficient data: upload required documents |
| A4.4 | NCR Rate | A4 | `ncrExposureRecord` | Awaiting a nonconformance record with the exposure it is measured against: the nonconformances raised, and the inspections, hours or value they arose from. This measure is named for a method that cannot be carried out without it,  |
| A4.5 | Weather Day Impact | A4 | `weatherImpactEvents` | Awaiting a weather impact record: the weather events, the activities they stopped, the time actually lost, the allowance in the contract calendar, and the float on the path. This measure is named for a method that cannot be carrie |
| A4.6 | Change Order Frequency | A4 | `changeEventRegister` | Awaiting a change event register with the exposure it is measured over: each change, its type, cause and value, and the span of time or contract value it arose against. This measure is named for a method that cannot be carried out |
| A4.7 | Dispute Escalation Index | A4 | `claimDisputeRegister` | Awaiting a claim and dispute register: the project's own governed escalation process and the stage each issue has reached on it, with the dates it reached them. This measure is named for a method that cannot be carried out without |
| A4.8 | Subcontractor Performance | A4 | `subcontractorAssessments` | Awaiting a subcontractor performance assessment: each firm, the criteria it was rated against, the rating on each, who assessed it and the weights that were applied. This measure is named for a method that cannot be carried out wi |
| A4.9 | Procurement Lead Time Monitor | A4 | `procurementItems` | Awaiting an item level procurement register: for each item, the date it is required on site, the date it is forecast to arrive, and the activity it feeds. This measure is named for a method that cannot be carried out without it, s |
| A5.1 | DSM Rework Propagation | A5 | `dsmDependencyModel` | Awaiting a dependency matrix for the design: the parts of the design, which of them depend on which others and how strongly, and the rework the propagation starts from. This measure is named for a method that cannot be carried out |
| A5.2 | Sensitivity Analysis | A5 | `sensitivityModel` | Awaiting a sensitivity model: a named response function, the state it is evaluated at, and the inputs to be moved with the range each is moved across. This measure is named for a method that cannot be carried out without it, so no |
| A5.4 | Scenario Modeling | A5 | `scenarioSet` | Awaiting a scenario set: named scenarios, each stating every input it changes together, the reasoning behind it, and the response model they are all evaluated through. This measure is named for a method that cannot be carried out  |
| A5.5 | Rework Feedback Loop | A5 | `systemDynamicsModel` | Awaiting a system dynamics rework model: the stock of work in the backlog, the work arriving and completed each step, and the share of completed work that returns as rework. This measure is named for a method that cannot be carrie |
| A5.6 | Queueing Theory Bottleneck | A5 | `queueModel` | Awaiting a queue model: the rate work arrives at, the rate it is served at, how many servers there are and the order they take work in. This measure is named for a method that cannot be carried out without it, so no reading is rep |
| A5.7 | Agent-Based Supply Chain | A5 | `agentSupplyChainModel` | Awaiting an agent based supply chain model: the agents, the state each starts in, the rule each follows, who they are connected to, and the steps the model runs over. This measure is named for a method that cannot be carried out w |
| A5.8 | Discrete Event Simulation | A5 | `desProcessModel` | Awaiting a discrete event model: the entities and when they arrive, the resources that serve them, how long service takes, and the order simultaneous events are taken in. This measure is named for a method that cannot be carried o |
| A6.4 | Contractor Performance Assessment Signal | A6 | `contractorAssessmentRecord` | Awaiting a governed contractor assessment record. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place. |
| B1.1 | Conservative Dominance | B1 | `(scalar only)` | Insufficient data: upload required documents |
| B1.2 | Weighted Voting | B1 | `signalWeightPolicy` | Insufficient data: upload required documents |
| B1.3 | Majority Rules | B1 | `(scalar only)` | Insufficient data: upload required documents |
| B1.4 | Worst-N-of-M | B1 | `(scalar only)` | Insufficient data: upload required documents |
| B2.18 | MARCOS Ranking | B2 | `decisionAlternatives` | Awaiting an explicit decision problem: the alternatives being compared, the criteria they are compared on, and which way each criterion is better. This measure is named for a method that cannot be carried out without it, so no rea |
| B3.1 | Agent-Based Governance Model | B3 | `abmGovernanceModel` | Awaiting a governed agent, authority-matrix and interaction structure. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place. |
| B3.2 | FAR/Agency EVMS Applicability Monitor | B3 | `evmsApplicabilityEvidence` | Awaiting governed acquisition, agency and clause applicability evidence. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place. |
| B3.3 | Versioned A-11 Capital Programming Conformance Check | B3 | `a11RuleRegister` | Awaiting a configured A-11 rule register. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place. |
| B3.4 | EVMS Reporting Compliance Monitor | B3 | `evmsReportingRecord` | Awaiting a governed EVMS reporting record. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place. |
| B3.5 | Contract Modification Governance Check | B3 | `contractModificationRegister` | Awaiting a governed contract modification register. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place. |
| B4.3 | Constraint Satisfaction Analysis | B4 | `constraintSatisfactionProblem` | Awaiting a governed constraint-satisfaction problem: variables, their domains, and the constraints over them. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure  |
| B4.4 | What-If Scenario Matrix | B4 | `actionScenarioMatrix` | Awaiting a governed action-by-scenario matrix: the actions being compared, the scenarios they are compared under, and an outcome for every pair. This measure is named for a method that cannot be carried out without it, so no readi |
| C1.1 | Missing Data Index | C1 | `requiredInputContract` | Awaiting the required-input contract for the module or use being assessed. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place. |
| C1.2 | Data Timeliness Score | C1 | `evidenceTimelinessRecord` | Awaiting a governed evidence date and freshness rule. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place. |
| C1.3 | Source Reliability Weighting | C1 | `sourceProvenanceRecord` | Awaiting a governed source provenance record. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place. |
| C1.4 | Audit Trail Completeness | C1 | `auditChainRecord` | Awaiting a governed audit chain record. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place. |
| C1.5 | Information Completeness Ratio | C1 | `informationPackageRecord` | Awaiting a governed information package definition. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place. |
| C1.6 | Cross-document Consistency Score | C1 | `crossDocumentFactSet` | Awaiting a governed cross-document fact set. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place. |
| C1.7 | Reporting Frequency Index | C1 | `reportingCadenceRecord` | Awaiting a governed reporting cadence record and report history. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place. |

### 2.1 Which category each sits in, and whether that category has any computing module

| Cat | Name | In service | Voting members | Any module computing on corpus evidence |
|---|---|---|---|---|
| A1 | Cost & EVM Performance | 10 | **A1.7, A1.8** | yes (A1.7, A1.8) |
| A2 | Schedule Performance | 6 | none | no |
| A3 | Cost Risk | 7 | none | no |
| A4 | Document-Derived Condition Signals | 10 | none | no |
| A5 | Systems & Simulation | 7 | none | no |
| A6 | Delivery Quality Performance | 4 | none | yes (A6.1, A6.2, A6.3) |
| B1 | Signal Aggregation | 4 | none | no |
| B2 | Decision Analysis | 1 | none | no |
| B3 | Regulatory & Governance | 5 | none | no |
| B4 | Decision Optimisation | 2 | none | no |
| C1 | Evidence Quality | 7 | none | no |

---
## 3. §4.2 / §12-3 — what I found when I went looking for the documents

### 3.1 THE FIRST FINDING, AND IT IS A STOP: PRJ-001's documents are not reachable from this environment

The order says "open the actual document files — the synthetic corpus in the project folder, and
the document set the platform holds for PRJ-001". I did both. Here is what is actually there.

**The platform's document set is not in this repository.** A document's bytes and its extraction
live in one place: `server/app/research_models.py:513-524`, `class Document`,
`__tablename__ = "documents"`, columns `content: Mapped[bytes]` and `extraction: Mapped[dict]`.
There is no file tree of documents anywhere in the repo. I swept for one and it does not exist:

- `find . \( -iname '*.pdf' -o -iname '*.docx' \)` outside `.git`/`node_modules` → **zero PDFs,
  zero Word documents.** The only `.xlsx` files are five fixture `package_summary.xlsx`.
- The only SQLite database in the tree, `server/dev.db`, is **untracked** (`git ls-files
  server/dev.db` → empty) and holds `documents = 2`, `projects = 8`. It is a scratch dev database,
  not PRJ-001's 100 documents.
- `env | grep -i DATABASE` → **nothing**. There is no `DATABASE_URL` in this environment, and §7
  hard limit 2 forbids pointing one at production Postgres. I did not, and would not.

**So the 100 documents across 21 types and four reporting periods exist only as rows in the
production database.** They are real; I am not saying they are not. I am saying **I could not open
them from here**, and §12 rule 2 forbids me concluding anything about their contents on that basis.
Everything below that touches PRJ-001's actual document contents is reported as
**NOT DETERMINABLE**, never as "the input does not exist".

**This is §10.4: a ruling resting on a premise the environment contradicts.** I report it. I do not
resolve it against the owner. The remedy is incidental finding I1.

### 3.2 The synthetic corpus, opened

`research_fixtures/synthetic/` holds six packages, 336 files, and I opened them. **They are not PM
documents.** `OG-SYNTH-0.3/.../package_A_project_structures/` is ~130 CSV and JSON ground-truth
tables — `agents.csv`, `dsm_edges.csv`, `cost_risk_events.csv`, `monte_carlo_convergence.csv`,
`ccpm_chains.csv` and so on: the *validation oracles* for the canonical methods, not pay
applications, RFI logs or OAC minutes. `OG-SYNTH-0.6`, which `server/tools/synthetic_packages.py:146`
names as current, contains exactly **4 files**, all portfolio-calibration JSON.

**There is no document of any of the 21 types anywhere in this repository to read.** That is a
statement about the repository, verified by sweep, not about PRJ-001.

### 3.3 What I could establish instead, and it answers the owner's question

Since I could not read PRJ-001's documents, I tested the extraction path itself — end to end, on
the real production code, with documents I constructed to state exactly what a real one of that
type states. Three separate measurements.

**Measurement 1 — the extraction contract asks for the fields.** `server/app/extraction_fields.py:167-283`
`_EXTRACTION_FIELDS` maps all 27 document types to their field lists, and
`server/app/extraction_client.py:179-256` `build_prompt` puts that exact list into the model prompt
verbatim. `rfi_log` asks for `rfi_total`, `rfi_open`, `rfi_overdue`, `avg_response_days`,
`rfi_period_days`, `oldest_open_days`. `submittal_register` asks for `submittals_total`,
`submittals_rejected`. `pay_application` asks for `original_contingency`, `remaining_contingency`.
`ncr_log` asks for `ncr_issued`/`ncr_closed`/`ncr_open`; `inspection_report` asks for
`items_inspected`. **None of these is missing from the schema.**

**Measurement 2 — the merge maps them into signal inputs.** `server/app/extraction_merge.py:552-661`
`_NUMERIC_EMISSIONS` carries `("rfi_total","rfiCount")`, `("rfi_period_days","rfiPeriodDays")`,
`("submittals_total","submittalsTotal")`, `("submittals_rejected","submittalsRejected")`,
`("original_contingency","originalContingency")`, `("remaining_contingency","remainingContingency")`.
**None of these is unwired.**

**Measurement 3 — a document stating those figures lights the module.** I ran three constructed
documents through the real `assemble_signal_inputs` and then the real `registry.run_module`:

| Document supplied | Fields it states | Module | Result |
|---|---|---|---|
| `rfi_log` "RFI Log P4.pdf" | `rfi_total=37, rfi_open=9, rfi_overdue=3, avg_response_days=11, rfi_period_days=30, oldest_open_days=54` | **A4.2 RFI Velocity** | **COMPUTES — Red** — "37 RFIs over 30 days (37/30d, 8.6/week), 3 overdue (8%), avg response 11 days, oldest open 54 days" |
| `submittal_register` | `submittals_total=120, submittals_rejected=18` | **A4.3 Submittal Rejection Rate** | **COMPUTES — Yellow** — "18 of 120 submittals rejected (15%)" |
| `pay_application` | `original_contingency=100000, remaining_contingency=60000` | **A3.2 Contingency Burn Rate** | **COMPUTES** (figure, calibration pending, no band asserted) — "Contingency is 40 per cent consumed at 40 per cent complete, a burn against progress of 1" |
| `ncr_log` + `inspection_report` | `ncr_issued=4`, `items_inspected=100` | **A4.4 NCR Rate** | **COMPUTES** — "4 nonconformances against 100 inspections, a rate of 0.04 for each one. 1 are still open." |

**Not one line of code had to change to produce those four results.** The pipeline works.

### 3.4 So where is the defect? — the answer, stated plainly

**It is not in the extraction schema and it is not in the wiring.** For A3.2, A4.2, A4.3 and A4.4
every field is asked for, mapped and consumed today, and a document that states the figures makes
the module compute. If those four are dark on PRJ-001, exactly one of three things is true, and
**which one is NOT DETERMINABLE from here**:

1. PRJ-001 holds no document of that type (no RFI log, no submittal register, no NCR log, no
   inspection report, no pay application with a contingency line); or
2. it holds them and the documents do not state those figures; or
3. it holds them, they state the figures, and the stored `extraction` JSON came back null for
   those keys — which would be a model/classification defect, not a schema defect.

**Case 3 is the only one that is a platform defect, and it is decidable in one query against the
platform's own database.** That query is incidental finding I1.

---
## 4. THE MEASUREMENT THAT DECIDES THIS RUN: the ceiling of the extraction contract

The owner's premise is that better extraction lights the dark modules. **I tested that directly by
executing it.** I built a signal-input dictionary in which **every single key the extraction and
merge layer is capable of producing** carries a value — all 76 of `extraction_merge.SIGNAL_INPUT_KEYS`
(`server/app/extraction_merge.py:116-139`), plus `cpi`, `spi` and the evidence qualification —
and ran all 63 in-service modules against it.

**Result: 8 COMPUTES, 54 ABSTAINS, 1 SUPPLIED_NOT_COMPUTED.**
The eight are `A1.7, A1.8, A3.2, A4.2, A4.3, A6.1, A6.2, A6.3`.

Add the two that need something other than a flat field — `A4.4` (structure assembled from
`ncrIssued` + `itemsInspected` at `server/app/documents.py:1397-1428`, proven computing in §3.3)
and `A1.2` (needs two periods of history, and Run 63 already saw it green on a two-period fixture) —
and **the absolute ceiling of the current extraction contract is 10 modules of 63, and it is still
1 category of 11.**

### 4.1 Why the other 53 cannot be reached by extraction, whatever it pulls out

**55 of the 63 in-service modules require a governed *structure* key**, not a number. Derived live
from `canonical.py`, `canonical_v3.py` … `canonical_v8.py` `*_STRUCTURE_KEYS` — the full list is
the fourth column of the §2 table.

**`extraction_merge` can emit exactly ZERO of those structure keys.** Measured:
`[k for k in ALL_STRUCTURE_KEYS if k in SIGNAL_INPUT_KEYS]` → **`[]`**. The 76 keys the merge layer
emits are flat scalars, dates and counts; not one is a structure.

**Only four structures are assembled from documents anywhere in production code.** Sweeping
`server/app/documents.py` for every structure key in the union of the seven maps returns exactly
four hits: `ncrExposureRecord` (line 1400), `documentRiskEvidence` (1450), `milestoneForecastHistory`
(1499), `costRiskModel` (1541). Every other structure arrives through `saveprojectdata` →
`server/app/project_data.py`, a **typed intake form**, not a document. `project_data.py:5-11` says
so in its own words: 21 of the 23 v3 structures "appeared in TEST FIXTURES AND NOWHERE ELSE" until
that intake path was built.

**And the canonical layer refuses count-form substitutes by design.** This is not an oversight to
be patched; it is §5 already enforced in code:

- **A2.8** `look_ahead_ready_fraction` (`canonical_v3.py:1470-1520`) — extraction already supplies
  `activitiesPlanned`, `activitiesConstrained` and `lookaheadWeeks`. The method still refuses them:
  "Each activity must carry its own identity and constraint status, so the counts are derived from
  an inventory rather than asserted as two numbers." Making A2.8 compute would require **inventing
  activity identities**. §10.2. **Stopped.**
- **A1.6** `time_phased_baseline` (`canonical_v3.py:815-823`) — a PV curve could be stitched from
  four periods of `planned_value_to_date`, but the method demands
  `_provenance(structure, words, "baseline_version", "approval_source")`. A curve read off period
  reports is not an approved baseline and has no approving authority. Supplying one would be
  **inventing provenance**. §10.2. **Stopped.**
- **A1.9** `expenditure_baseline_to_date` (`canonical_v3.py:850-864`) — identical refusal,
  identical reason. §10.2. **Stopped.**

**Run 29's own closure already did this decomposition and found the same thing**
(`server/app/documents.py:1373-1379`): of 17 Category-4/5 structures, "Sixteen are the first case"
(fields genuinely absent from the corpus) and exactly one was "present, already extracted, and
simply never wired" — `ncrExposureRecord`, which it then wired. **The "extracted but unwired" class
has been swept before and it was one module wide.**

**Conclusion, and it is the answer to the order's question.** Extraction is not the reason 59
modules are dark. **53 of them are dark because the platform has no document-shaped source for a
governed structure at all**, and the four that a document could reach are already wired end to end.

---

## 5. §4.4 / §12-6 — the categories, and the rule that stops nine of them

**A category cannot light because a module in it computes.** That premise in §4.4 is contradicted
by the code, and this is §10.3.

`server/app/simulation/compute.py:97-98`:

```
for row in run["computed"]:
    if row["module_id"] not in CORE_VOTING_MODULES:
        continue
```

**Only voting modules ever reach category fusion.** `CORE_VOTING_MODULES` is
`frozenset({'A1.7','A1.8'})` (`server/app/simulation/registry.py:164`), and **both sit in A1**.

Therefore, derived live:

| Category | Modules in service | Voting members | Can it ever carry a status today? |
|---|---|---|---|
| A1 | 10 | A1.7, A1.8 | **Yes — and it does** |
| A2, A3, A4, A5, A6, B1, B2, B3, B4, C1 | 6,7,10,7,4,4,1,5,2,7 | **none** | **No. Structurally impossible.** |

**Ten of the eleven categories cannot light no matter how many of their modules compute.** Lighting
A4 by making A4.2, A4.3 and A4.4 compute — which §3.3 proves is achievable — would still leave
category A4 grey, because no A4 module votes.

**§4.4 and §11.2 forbid me touching the voting set, and I did not.** The voting count is still
exactly 2. **The only thing that can light a second category is the owner enlarging
`CORE_VOTING_MODULES`, and that is his ruling to make, not this run's.** §10.3: **stopped, rule
named, untouched.**

---
## 6. §4.3 / §12-4 — every field newly extracted

**None.** No field was added to the extraction schema, because **no field a module needs was found
missing from it.** Every field the four document-reachable modules require is already in
`_EXTRACTION_FIELDS`, already in `build_prompt`'s field list, and already mapped by
`_NUMERIC_EMISSIONS`. Adding a field that is already there would be theatre; adding one whose value
no document states would be §11.1.

## 7. §12-5 — per module: does it compute now, and what does it say

| Module | Before | After | Note |
|---|---|---|---|
| A1.2, A1.7, A1.8 (+1 on PRJ-001) | compute | compute | unchanged |
| A3.2, A4.2, A4.3, A4.4 | dark on PRJ-001 | **still dark on PRJ-001** | Proven in §3.3 to compute the moment a document states their figures. Whether PRJ-001's documents state them is **NOT DETERMINABLE** from here. **No code change was needed or made.** |
| A6.1, A6.2, A6.3 | compute on corpus evidence, dark on PRJ-001 | unchanged | need quality-audit / safety / environmental reports |
| all others (53) | dark | dark | require a governed structure no document path can supply — §4.1 |

## 8. §12-7 — every module still dark, and what a document would have to contain

**The complete answer is the fourth and fifth columns of the §2 table**, which are the modules' own
words. Summarised by class:

1. **Four modules, reachable by document (A3.2, A4.2, A4.3, A4.4).** A pay application stating an
   original and a remaining contingency; an RFI log stating a total AND the number of days it
   covers; a submittal register stating a total and a rejected count; an NCR log stating
   nonconformances raised together with an inspection report stating items inspected. **Nothing
   needs building — these need the document to say the number.**
2. **Three modules, reachable by document ONLY if provenance comes with it (A1.6, A1.9, A2.8).**
   A1.6/A1.9 need a cumulative planned-value or expenditure curve **that names its baseline version
   and its approving authority**; A2.8 needs a look-ahead listing **each activity by identity with
   its constraint status and category**, not two totals. A period report stating the totals is not
   enough and the code says so. §10.2 stopped all three.
3. **Three modules, reachable by history (A1.2 already, A1.5 needs a longer CPI series, A2.7 needs
   a milestone forecast per period).**
4. **Forty-six modules requiring a model, a register or a governed record** — an activity network,
   a critical chain, a reference class of completed projects, a cost-risk model, a DSM, a queue
   model, an A-11 rule register, an EVMS reporting record, an audit chain. **No project-controls
   document contains these.** They are what `saveprojectdata` exists to receive. A document cannot
   be written that would light them; a structure has to be supplied.
5. **A4.1 Document Risk Score** is `SUPPLIED_NOT_COMPUTED`, not abstaining: the server refuses to
   compute it because it "has not been ported and validated against the JavaScript implementation".
   Extraction cannot change that. It is a porting decision.

## 9. §12-8 — every item stopped under §10

| # | §10 | Item | Reason |
|---|---|---|---|
| 1 | **10.4** | **The whole of §4.2** | PRJ-001's documents are rows in production Postgres (`research_models.py:513-524`), not files in this repository; no `DATABASE_URL` exists here and §7 forbids pointing one at production. Reported, not resolved against the owner. |
| 2 | 10.2 | **A2.8** Look-Ahead Schedule Health | would require inventing activity identities (`canonical_v3.py:1489-1494`) |
| 3 | 10.2 | **A1.6** Earned Schedule | would require inventing `baseline_version` / `approval_source` (`canonical_v3.py:819`) |
| 4 | 10.2 | **A1.9** Budget Execution Rate | same refusal, same line-level reason (`canonical_v3.py:854`) |
| 5 | 10.1 | **46 structure-requiring modules** | input is a model or register no document type carries; named individually in §2 |
| 6 | **10.3** | **Categories A2–C1 (ten of eleven)** | cannot light without changing `CORE_VOTING_MODULES` (`registry.py:164`, read at `compute.py:98`). Rule named. **Untouched.** |
| 7 | 10.4 | **§9's mint** | §9 orders `sim-2026.08-v42`. No executable behaviour changed, so a new stamp and a new digest would assert a behaviour change that did not happen — the exact false statement blocker **B05** exists to catch. **Not minted. Declared conflict; the owner decides.** |

---
## 10. §8 / §12-9 — the eleven guarantees, each with its injection

No new check file was written, because no production byte changed and §11.3 forbids a check that
would be vacuous by construction. The guarantees were verified by **live execution against the
production code**, with injections where an injection is meaningful.

| # | Guarantee | Status | Evidence / injection |
|---|---|---|---|
| 1 | every newly extracted field is present in the document it claims to come from | **N/A — no field was newly extracted** (§6) | — |
| 2 | every module newly computing produces a value derived from that field, hand-computed | **MET for the four §3.3 modules**, hand-computed independently: A4.2 37/30 = 1.2333/day → ×30 = **37.0 per 30d**, ×7 = 8.633 → **8.6/week**; 8.633 > 8 → **Red** ✓ (module: Red). Overdue 3/37 = 0.0811 → **8%** ✓. A4.3 18/120 = **15%** ✓. A4.4 4/100 = **0.04** ✓. A3.2 (100000−60000)/100000 = **40% consumed** at 40% complete → ratio **1** ✓ | all four match the module output exactly |
| 3 | **no module produces a value from an absent input** | **MET, by injection on the live path** | Delete `rfi_period_days` from the RFI-log extraction → `rfiPeriodDays=None` → A4.2 **ABSTAINS**: "Awaiting the number of days the request log covers: a rate of requests over time cannot be formed without the span of time it was measured over." **It did NOT substitute 30.** Delete `rfi_total` → A4.2 ABSTAINS. Delete `submittals_total` → A4.3 ABSTAINS. **Restored → all COMPUTE again, byte-identical output.** |
| 4 | every abstention still says what it is waiting for | **MET with one exception, reported as an incidental finding** | 55 of 57 abstentions name their input in a full sentence (§2 table). **A4.2 (`rfiCount` absent), A4.3, B1.1–B1.4 say only "Insufficient data: upload required documents"** — true, but it does not say *which* document. See I2. |
| 5 | every new field carries its source document | **N/A — no new field** | — |
| 6 | voting count is still exactly 2, A1.7 and A1.8 | **MET** | `sorted(CORE_VOTING_MODULES)` → `['A1.7','A1.8']`; freeze gate **B09** "voting count is not exactly 2 — is zero" PASS |
| 7 | no band, threshold or fusion rule changed | **MET** | `git status --porcelain` empty apart from this report; not one `.py` touched |
| 8 | modules in service 63, registry 101, both derived | **MET** | `len(service_index())=63`, `len(registry_index())=101`, derived live, not typed |
| 9 | every runtime lookup across all 101 registered modules resolves, asserted live | **MET** | ran `run_module` for all 101; unexpected-exception list = **`[]`** (only the governed `MissingModuleError` for A4.1 and `PortfolioModuleError` for the 5 portfolio targets) |
| 10 | the charts show what the row holds (Run 63's guarantee) | **NOT RE-RUN.** No browser session was opened this run. Nothing that feeds a chart changed, and Run 63's own suite is inside the 205 that passed. Reported honestly as not re-executed rather than claimed. | — |
| 11 | the successor freeze gate passes in full | **MET** | `python3 tools/test_run37_freeze_gate.py` → **`RESULT: 34/34 checks passed`**, B01–B15 each "is zero", `blocking_defects_zero` PASS |

**Because no browser session was opened, the `DEng\Demo` tell is reported as: not measured this
run, no session held.**

## 11. §12-10 — the behaviour digest, before and after

**Before: `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1`.
After: `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1`. It did not move.**

§8 of the order says the digest **will** move "because modules that abstained now compute", and the
briefing's corollary is exact: **the digest moving is expected only because modules newly compute.**
No module newly computes, no executable byte changed, and blocker **B15** ("candidate behaviour
changed during the run") **passed as zero** against the v35 record — which is the live proof that
nothing moved. **A moved digest here would have been the finding. An unmoved one is the correct
outcome of a run that changed nothing.**

## 12. §12-11 — the mint, the gate, the suite, the merge, the push

- **Mint: NOT TAKEN.** §9 orders `sim-2026.08-v42` / `og-participant-2026.08-v27`. Nothing executable
  changed, so the stamp would carry a false claim. Declared as stop 7 in §9 above. **Mint cost paid:
  zero passes.** Runs 56/57/59/62/63 paid 7/3/6/6/3; this run paid none because none was owed.
- **Gate: `RESULT: 34/34 checks passed`**, every row from live output, B01–B15 all zero,
  `blocking_defects_zero` PASS, `no_release_while_blocked` PASS, `no_self_reference` PASS, all six
  `predecessor_release_preserved` rows PASS.
- **Suite: `Suites run: 205   Total checks: 15334/15334` / `ALL SUITES GREEN`**, exit code 0, every
  suite on its own freshly migrated SQLite database via `server/run_all_suites.sh`. **Exactly the
  baseline figures**, unchanged.
- **Audit artifacts: 28 rewritten by the suite pass** (27 under `code_audit/` plus
  `server/tools/run17/coverage.csv`), **all 28 restored** with `git checkout --` naming each path
  explicitly. `git status --porcelain` afterwards showed only this untracked report. **None committed.**
- **Merge and push: no branch, no merge.** No production byte changed, so there is nothing to merge.
  This report is committed directly to `main`, which is where every prior run's report lives.
  `git add -A` and `git add .` were never run; the only `git add` names this file.

---
## 13. §12-12 — incidental findings, unacted

**I1. The one query that settles this run, and it takes a minute.** Against the platform's own
database, for PRJ-001:

```sql
SELECT du.period, d.doc_type, d.filename, d.extraction
FROM document_uploads du JOIN documents d ON d.document_id = du.document_id
WHERE du.project_id = <PRJ-001> ORDER BY du.period, d.doc_type;
```

Three things to look for: (a) is there a row with `doc_type` in
(`rfi_log`, `submittal_register`, `ncr_log`, `inspection_report`, `pay_application`)? (b) if so, is
`extraction->>'rfi_total'` / `'rfi_period_days'` / `'submittals_total'` / `'ncr_issued'` /
`'items_inspected'` / `'original_contingency'` **null**? (c) if null, does the document itself state
the figure? **If the answer is "the document states it and the extraction is null", that is the
defect the owner named, it is a model/classification defect, and it is fixable.** If the answer is
"no such document type is in the set", that is a corpus finding. I could not run this; it needs
either database access or an export of those rows dropped into the repository.

**I2. Six abstentions do not name the document they want.** A4.2, A4.3 and B1.1–B1.4 emit only
"Insufficient data: upload required documents". Every other abstaining module names its input in a
full sentence. A PM reading "upload required documents" on RFI Velocity has no way to know it wants
an RFI log with a stated period span. This is a §8.4 near-miss and worth one run's attention.
**Unacted.**

**I3. `rfi_period_days` is the single most fragile field on the platform.** A4.2 abstains on its
absence alone even with a perfect RFI total (proven by injection in §10 row 3). Most real RFI logs
state a date range, not a day count. `_derived(si, "rfiPeriodDays")` exists in
`models_doc.py:194`, so the concept of deriving it is already contemplated — deriving it from
`log_date` minus a period start would be a legitimate computation from stated dates, **but it is a
behaviour change and I did not make it.** **Unacted, flagged for a ruling.**

**I4. `server/dev.db` is untracked and stale** (2026-08-12, 2 documents, 8 projects). Harmless, but
anything reasoning from it would reason from nothing.

**I5. The extraction prompt's own commitment is worth re-reading against this run's conclusion.**
`extraction_client.py:207-213` records that every field in `ALL_FIELDS` "is a total, a date, a
rating, a percentage or a count a construction report states directly" — checked, not assumed. That
is precisely why the extraction contract cannot reach a structure: **it was designed to read stated
scalars, and 55 of 63 modules are defined on structures.** The gap is architectural, and closing it
is a decision about where structures come from, not a decision about prompting.

---

## 14. The statement this run owes the owner

**I did not make a single module compute, and I will not pretend otherwise.**

What I found is worth more than a lit chart would have been:

1. **The extraction pipeline is not broken.** Four modules — A3.2, A4.2, A4.3, A4.4 — compute the
   moment a document states their figures, with no code change at all. I proved it by running real
   documents through the real merge into the real modules.
2. **Better extraction has a hard ceiling of ten modules of sixty-three**, measured by populating
   every key the contract can produce. It is not 63 and it never was.
3. **Fifty-three modules are dark for a reason extraction cannot touch**: they are defined on
   governed structures, and the merge layer emits none.
4. **Ten of the eleven categories cannot light at all**, because only A1.7 and A1.8 vote and both
   are in A1. Extraction is irrelevant to that. **Only your ruling on the voting set can change it.**
5. **PRJ-001's documents could not be opened from this environment.** They are in the production
   database. I did not conclude anything about their contents, and incidental finding I1 is the one query
   that would.

A dark module honestly dark is the correct outcome where the evidence is missing. Four honest
modules stand. Nothing was invented.
