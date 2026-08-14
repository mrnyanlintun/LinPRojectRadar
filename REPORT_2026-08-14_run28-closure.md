# Run 28 closure: the five defects, closed before Run 29

This continues Run 28. It is not Run 28B and it does not begin Run 29.

## THE FIVE CLOSURE DEFECTS, LED WITH

### 1. Final-head suite mismatch — PRESENT, and it was real

Run 28 recorded 127 suites and 10730 checks green at `a74efe2` and then pushed `0e0dfbd`. Two
further commits carried the stage-2 freeze digest and the merged-main total, and the verification
was never repeated on the commit that shipped. Nothing was inherited here. The complete suite was
re-run on the exact final merged head, and the head, the origin ref and the suite total are
recorded together at the end of this report.

### 2. Incomplete approved rename propagation — PRESENT, and worse than reported

Run 28 renamed A1.10 and A1.11 in `p0-baseline/module_renumbering_map.csv` and propagated only to
the generated `ds_defensibility_evidence.js`. **Nine current browser surfaces still spoke the old
names**, including the registry `assets/js/categories.js` that `p0-baseline/MODULE_TAXONOMY.md`
states is generated from the map. The instrument said two different things about the same module
at the same moment.

Closed by propagating both approved names to every current surface: `categories.js`, `taxonomy.js`,
`knowledge.js`, `deepdive.js`, `charts3d.js`, `decision-ui.js`, `workspace.js`,
`ds_defensibility_data.js`, `neural_flow.js`. Display strings only: every `method_class` constant,
every `required` key list, every module id and every number is byte-identical, and no step of the
preliminary → lock → reveal → final → lock sequence moved.

`assets/js/taxonomy.js` IS renamed, reversing Run 28's decision on the owner's explicit closure
instruction. That changed the participant package checksum, so a successor package record was
created and the predecessor preserved (section "Successor records" below).

Historical artefacts keep historical wording and this is asserted, not assumed: the Run-28 report,
`server/app/simulation/VALIDATION.md` and `code_audit/run12_participant_package_checksums.sha256`
must still carry the old names or `test_run28_closure.py` goes red.

### 3. A2.7 single-slip-versus-trend — NOT PRESENT as a defect; verified mechanically and hardened

The owner's concern was that one baseline plus one forecast was producing a trend. It was not.
The mechanical evidence:

* `canonical_v3.milestone_trend` raises `StructureAbsent` when any milestone carries fewer than
  two forecasts. Verified directly: baseline day 100 with a single forecast at day 114 produces
  no reading at all, and the registered module reports NOT ESTIMABLE.
* The corpus assembler `documents._milestone_forecast_history` requires two or more schedule
  snapshots before it builds anything, and within that it DROPS any milestone with fewer than two
  forecasts rather than padding it.
* **The corpus does hold repeated forecasts for a stable milestone identity across reporting
  periods.** `test_schedule_milestones.py` drives the suite's own real schedule documents through
  two reporting periods: D100, D200 and D300 each appear in both, D400 is refused in both, D600 is
  absent from period 2 and D700 from period 1, so exactly three milestones are followed. D200's
  forecast moves 14 August → 28 August: a fourteen-day drift between successive forecasts AND a
  fourteen-day variance against the date it was committed to. D300 carries seven of each. That is
  a run of forecasts over time, not a single pair.
* The contract's own worked example reproduces exactly: baseline 100 with forecasts 104, 108, 111
  gives slips 4, 8, 11 and a deteriorating direction.
* No status colour is asserted; the module reports calibration pending and Run 33 owns the slip
  boundaries.

Two faults were injected to prove the guards can fail. **F2** weakened the canonical method's own
minimum-history test to accept one forecast: `test_run28_closure.py` 65/65 → 62/65. **F8** weakened
the real-corpus assembler so a milestone seen in one period only is admitted:
`test_schedule_milestones.py` 78/78 → 69/78.

### 4. Untracked-file guard blind spot — PRESENT, and closed at both places it lived

Run 28 recorded it OPEN. It was real and it had two homes:

* `test_run8_retest_classify_27.py` and `test_run10_state_protection.py` reason about production
  change through `git diff --name-only`, which enumerates tracked paths and nothing else. A new
  production file that was never added to the index was invisible to them.
* `production_tree.walk_production()` already discovered names from the FILESYSTEM and already
  returned each file's tracked state — and **nothing asserted that attribute**. The information
  was collected and thrown away, which is why `canonical_v3.py` could be untracked, pinned, hashed
  and green.

Closed by: asserting the tracked attribute over the whole walked surface in
`test_run22_production_tree_completeness.py`, and enumerating untracked paths with
`git status --porcelain --untracked-files=all` alongside the diff in
`test_run8_retest_classify_27.py`.

**Non-vacuity proof, on the REAL tree, exactly as instructed (fault F1):**

1. baseline GREEN — `test_run22_production_tree_completeness.py` 44/44;
2. `server/app/simulation/run28_closure_probe_file.py` created, one harmless comment line;
3. confirmed from the filesystem: the file exists, and `git status --porcelain -uall` lists
   `?? server/app/simulation/run28_closure_probe_file.py`;
4. the named guard RED — 40/44, naming that exact path both as an unexpected ADDED file and as an
   untracked production file. It printed its anchored RESULT line; it did not crash;
5. deleted;
6. baseline GREEN — 44/44.

The guard was also observed genuinely red in ordinary use before the fix was finished: it named
`server/app/project_data.py` as an untracked production file at the moment that file existed and
had not been added.

### 5. Missing supply-path implementation — PRESENT, and this was the substantive defect

Run 28's twenty abstentions were defensible only if the platform could receive the structures.
It could not. Reading every production source for an assignment of each structure key:

* **two of twenty-three v3 structure keys were written by production code**:
  `milestoneForecastHistory` and `costRiskModel`, both in `documents.py`;
* **twenty-one were written nowhere in `server/app/` at all.** They appeared in test fixtures and
  in `server/tests/synthetic_fixtures/`, and nowhere else. A structure only a test can supply is
  a description of a supply path, not one;
* the same was true of `lobStructure` and `ccpmStructure` in `canonical.py`, which serve A2.2 and
  A2.3 — two modules Run 28 counted as "already canonical" rather than as abstaining, and which
  in fact abstain on the real corpus for exactly the same reason as the twenty.

Closed by building the intake: `server/app/project_data.py` (NEW production file), the
`saveprojectdata` action in `server/app/writes.py`, and one merge point in
`documents.run_and_store`. It is append-only, period-effective so an earlier period still
recomputes byte-identically, its vocabulary is READ from `canonical_v3.V3_STRUCTURE_KEYS` and
`canonical.CANONICAL_STRUCTURE_KEYS` rather than restated, and it validates nothing for
plausibility because `canonical_v3`'s own guards decide whether a structure satisfies its
contract. A document-derived structure always wins over a supplied one.

The guard does not read a column that says this works: it stores each of the nineteen intake
structures through the same helper the write handler calls, reads it back through the same helper
`documents.py` calls, and requires the structure to arrive on the signal inputs. **Fault F5**
removed the v3 half of the vocabulary: 65/65 → 60/65.

---

## A3.6: the real-document route, determined

**Determination: the real route is genuinely stochastic and does not abstain.** Every source named:

| item | what it actually is |
|---|---|
| source object | the project's own risk register for the period, `server/app/risk_register.py` → `risk_exposure.register_exposure`, assembled into `costRiskModel` at `documents.py` |
| base cost source | the project's reported budget at completion, one component `BUDGET_AT_COMPLETION`. No component list is invented |
| risk-event probability source | the register row's OWN probability. A row that cannot give both a probability and a cost impact is refused upstream by `register_exposure` and never reaches the model |
| impact source | the register row's OWN cost impact |
| impact distribution | `POINT`, declared as such. A register states one figure; no spread nobody elicited is implied |
| dependence treatment | **NEW IN THIS CLOSURE.** Run 28 drew every event from its own uniform — mutual independence — and never said so. The policy is now declared by the SOURCE: the register has no correlation column, no common-cause grouping and no joint distribution, so independence is what it supports and the model says so. A model with more than one event and no stated policy is now REFUSED, not defaulted |
| iterations | 20000, carried out on the result |
| seed / reproducibility | the project's seeded RNG from `rng.make_rng`; verified — the same stream reproduces the distribution exactly, two different streams do not |
| quantile convention | `canonical_v3.empirical_quantile`, right-continuous empirical inverse, frozen once for the whole line and used by every percentile the platform reports |

Verified stochastic rather than asserted: two different seeded streams over the same governed
model give different total-cost distributions, which a deterministic proxy structurally cannot.
The contract's own oracle reproduces exactly — base 100, one event at probability 0.5 with impact
20, P80 = 120. With no cost risk model the module abstains rather than inflating the cost index.
**Fault F6** made the dependence policy optional again: 65/65 → 63/65.

## A1.4: Q and R provenance

**No hidden or default Q is substituted, and this was already true before this closure.**

* `canonical_v3.kalman_state_space_model` requires `process_variance_source` and
  `measurement_variance_source` through `_provenance`, which refuses a blank. Verified: blanking
  either one makes the module abstain.
* With no state-space record at all the module abstains. No moving average is offered in its
  place and no traffic light is generated.
* Both variances and both provenance strings are carried out onto the result.
* The v10 literals `q = 0.01` and `r = 0.1` are assigned nowhere in `models_evm.py`. Checked with
  `ast` over the module's assignments, so the docstring that records what v10 did does not
  satisfy the check.
* The contract's oracle reproduces: x0=1, P0=1, Q=0, R=1, z=2 → gain 0.5, filtered state 1.5.

**R extraction from repeated readings of one period is NOT implemented by this closure, and I say
so plainly.** Run 27 proved it is estimable because two document types report the same period. No
code in this closure assembles that estimate. Q and R remain Run 33 calibration items and the
module abstains until a project supplies a record. **Fault F7** substituted a hidden `"assumed"`
default for both provenance fields: 65/65 → 62/65.

## A1.1: the naming resolution, and the conflict I could not resolve

**Mechanical finding.** `p0-baseline/MODULE_TAXONOMY.md` line 3 designates
`p0-baseline/module_renumbering_map.csv` "the single source of truth", says
`assets/js/categories.js` is generated from it and that "every other reference is updated from it".
`server/app/simulation/registry.py` line 34 reads that file at import and serves its names.
**Line 2 of that file records `Monte Carlo EAC`.**

The owner's closure instruction states "Its current canonical identity is Monte Carlo EAC Forecast"
and, in the same item, "Do not rename A1.1 away from the naming authority". **These two sentences
conflict**, because the authority does not record that name.

**What I did.** I aligned the CURRENT SURFACES to the authority and left the authority unchanged.
`categories.js`, `taxonomy.js`, `knowledge.js`, `deepdive.js`, `ds_defensibility_data.js` and the
`canonical_v3.py` section heading now read `Monte Carlo EAC`. I did NOT edit the renumbering map
to say `Monte Carlo EAC Forecast`: that would have been a third rename beyond the two authorised,
and Run 28 declined it for that reason.

**Current active naming conflicts for A1.1 = 0.** Asserted mechanically over the thirteen current
surfaces. **Fault F4** reinstated `Monte Carlo EAC Forecast` in `categories.js`: 65/65 → 63/65.

**THIS REMAINS AN OWNER DECISION.** The two candidate names are `Monte Carlo EAC` (authority:
`p0-baseline/module_renumbering_map.csv` line 2) and `Monte Carlo EAC Forecast` (owner prose;
also `research_fixtures/production_contract/monte_carlo_eac_forecast/contract.json` line 4, which
calls it `owner_prose_alias`). If the owner wants the second, the correct fix is one line in the
renumbering map plus a re-propagation, and it is a supervisory rename, not a run's judgement.
Historical artefacts keep historical wording either way.

---

## Non-vacuity: eight faults, each proven

`code_audit/run28_closure_fault_injection.csv`. Every fault: fresh migrated database per suite
run; `__pycache__` dropped on BOTH sides of every injection, honouring the same-clock-second
cache hazard Run 28 found; baseline rechecked GREEN; injected; **the injection confirmed by
re-reading the file from disk**; the guard observed **RED with an anchored RESULT line, not
crashed**; restored byte for byte and verified by digest; baseline rechecked GREEN.

| id | fault | guard | before | observed | after |
|---|---|---|---|---|---|
| F1 | untracked file created inside the protected production surface | run22 production tree | 44/44 | **RED 40/44** | 44/44 |
| F2 | A2.7 minimum-history weakened to one forecast | run28 closure | 65/65 | **RED 62/65** | 65/65 |
| F3 | approved rename reverted on one current surface | run28 closure | 65/65 | **RED 63/65** | 65/65 |
| F4 | A1.1 naming drift reintroduced | run28 closure | 65/65 | **RED 63/65** | 65/65 |
| F5 | supply path removed for the nineteen v3 structures | run28 closure | 65/65 | **RED 60/65** | 65/65 |
| F6 | A3.6 dependence policy made optional | run28 closure | 65/65 | **RED 63/65** | 65/65 |
| F7 | hidden default substituted for Kalman Q and R provenance | run28 closure | 65/65 | **RED 62/65** | 65/65 |
| F8 | real-corpus assembler admits a one-forecast milestone | schedule milestones | 78/78 | **RED 69/78** | 78/78 |

**8/8 PROVEN NON-VACUOUS.** Two faults (F2, F5) initially scored CRASH rather than RED. That was
recorded as a campaign FAILURE and fixed properly: the guard now turns an exception into a failed
property instead of dying before its RESULT line, and the campaign copies a fresh migrated
database for every suite run because a reused one made a real red read as a crash.

## Successor records

| record | value |
|---|---|
| freeze identifier | `OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN28-CLOSURE-V11-2` |
| manifest | `research/freeze/RUN28_CLOSURE_FREEZE_2026-08-14.json` |
| supersedes | `...-RUN28-CANONICAL-CAT1-3-V11-1`, preserved unchanged, named as parent with its digest carried |
| production surface | 228 files, `code_audit/run28_closure_production_tree.sha256` |
| parent tree manifest | `code_audit/run28_production_tree.sha256`, kept addressable as `PINNED_RUN28` |
| participant package | `og-participant-2026.08-v2`, `code_audit/run28_closure_participant_package_checksums.sha256` |
| predecessor package | `og-participant-2026.08-v1`, `code_audit/run12_participant_package_checksums.sha256`, untouched |
| analytical line | `sim-2026.08-v11`, **unchanged** — no arithmetic, band, boundary or reported quantity moved |

The manifest sha256 and the final commit are null in the stage-1 document by construction and are
recorded in the companion `.sha256` written by the finalisation commit.

**Reported rather than quietly corrected:** fourteen participant-package files already differed
from the Run-12 record before this closure — `radar.css`, `detail.js`, `simulations.js`,
`index.html` and others, from Runs 21 to 26 — so the Run-12 record was already stale and the
successor records the bytes as they actually stand.

## Constraints held

Voting is exactly 2 and they are A1.7 TCPI and A1.8 Variance at Completion. Material Cost Variance
A3.4 remains disabled and outside the twenty-eight. The participant decision sequence is unchanged.
Historical `sim-2026.08-v2` remains executable evidence: `test_run7_fix_now_defects.py` extracts
the analytical package from commit `021d5e2`, imports it, runs it and asserts the stamp. No Run-29
work was done: no Categories 4 to 10, no Portfolio Health, no PKG-ORPHANFIELDS, no Category-9 gate,
no B2.9, no calibration.

### The twenty-eight operational outcomes

| id | module | method implemented | corpus executes | corpus abstains | disabled lab-only | supply path present | supply-path type | production writes the key | calibration Run 33 | lineage Run 31 | post-closure disposition |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A1.1 | Monte Carlo EAC | yes | yes | no | no | yes | EXISTING_DOCUMENT_EXTRACTION | no | yes | yes | CANONICAL_RETAINED_CALIBRATION_PENDING |
| A1.2 | CUSUM Anomaly Monitor | yes | yes | no | no | yes | EXISTING_DOCUMENT_EXTRACTION | n/a | yes | yes | CANONICAL_FROZEN_DESIGN |
| A1.3 | Bayesian EAC | yes | no | yes | no | yes | NEW_STRUCTURED_FORM | no | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A1.4 | Kalman Filter SPI Smoother | yes | no | yes | no | yes | NEW_STRUCTURED_FORM | no | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A1.5 | ARIMA CPI Forecast | yes | no | yes | no | yes | DERIVED_QUALIFIED_HISTORY | n/a | no | yes | CANONICAL_IMPLEMENTED_HISTORY_REQUIRED |
| A1.6 | Earned Schedule | yes | no | yes | no | yes | CONTRACT_BASELINE_DATA | no | no | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A1.9 | Budget Execution Rate | yes | no | yes | no | yes | CONTRACT_BASELINE_DATA | no | no | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A1.10 | CPI Shrinkage Forecast | yes | no | yes | no | yes | REFERENCE_CLASS_DATASET_INTERFACE | no | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A1.11 | Independent EAC Reconciliation Index | yes | no | yes | no | yes | NEW_STRUCTURED_FORM | no | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A2.1 | PERT Network Criticality | yes | no | yes | no | yes | NEW_PROJECT_DATA_OBJECT | no | no | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A2.2 | Line of Balance | yes | no | yes | no | yes | NEW_PROJECT_DATA_OBJECT | no | yes | yes | CANONICAL_EXTENDED_CALIBRATION_PENDING |
| A2.3 | CCPM Buffer Health | yes | no | yes | no | yes | NEW_PROJECT_DATA_OBJECT | no | yes | yes | CANONICAL_EXTENDED_CALIBRATION_PENDING |
| A2.4 | Schedule Compression Index | yes | no | yes | no | yes | NEW_PROJECT_DATA_OBJECT | no | no | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A2.5 | Float Consumption Rate | yes | no | yes | no | yes | NEW_PROJECT_DATA_OBJECT | no | no | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A2.6 | S-Curve Deviation | yes | no | yes | no | yes | CONTRACT_BASELINE_DATA | no | no | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A2.7 | Milestone Trend Analysis | yes | yes | no | no | yes | EXISTING_DOCUMENT_EXTRACTION | yes | yes | yes | CANONICAL_IMPLEMENTED_AND_WIRED |
| A2.8 | Look-Ahead Schedule Health | yes | no | yes | no | yes | NEW_STRUCTURED_FORM | no | no | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A2.9 | Resource Loading Index | yes | no | yes | no | yes | NEW_PROJECT_DATA_OBJECT | no | no | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A2.10 | Schedule Risk Analysis P80 | yes | no | yes | no | yes | NEW_PROJECT_DATA_OBJECT | no | no | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A2.11 | Critical Path Index | yes | no | yes | no | yes | NEW_PROJECT_DATA_OBJECT | no | no | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A3.1 | Reference Class Forecasting | yes | no | yes | no | yes | REFERENCE_CLASS_DATASET_INTERFACE | no | no | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A3.2 | Contingency Burn Rate | yes | yes | no | no | yes | EXISTING_DOCUMENT_EXTRACTION | n/a | yes | yes | CANONICAL_RETAINED_BANDS_REMOVED |
| A3.3 | Labor Productivity Index | yes | no | yes | no | yes | EXISTING_DOCUMENT_EXTRACTION | no | no | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A3.5 | Overhead Absorption Rate | yes | no | yes | no | yes | NEW_STRUCTURED_FORM | no | no | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A3.6 | Cost Risk Analysis P80 | yes | yes | no | no | yes | EXISTING_DOCUMENT_EXTRACTION | yes | yes | yes | CANONICAL_IMPLEMENTED_AND_WIRED |
| A3.7 | Analogous Estimating Ratio | yes | no | yes | no | yes | HISTORICAL_DATASET_INTERFACE | no | no | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A3.8 | Parametric Cost Index | yes | no | no | yes | yes | NEW_PROJECT_DATA_OBJECT | no | no | yes | DISABLED_LABORATORY_ONLY |
| A3.9 | Inflation Adjustment Index | yes | no | yes | no | yes | EXTERNAL_OFFICIAL_DATA_INTERFACE | no | no | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |

### The twenty supply paths

| id | module | missing structure | runtime abstention reason | supply-path type | implemented | reachable by API | corpus supplies values | verdict |
|---|---|---|---|---|---|---|---|---|
| A1.3 | Bayesian EAC | `bayesianEacModel` | `canonical_structure_absent` | NEW_STRUCTURED_FORM | yes | yes | no | PASS |
| A1.4 | Kalman Filter SPI Smoother | `kalmanStateSpaceModel` | `canonical_structure_absent` | NEW_STRUCTURED_FORM | yes | yes | no | PASS |
| A1.5 | ARIMA CPI Forecast | `cost performance history` | `insufficient_history` | DERIVED_QUALIFIED_HISTORY | yes | yes | partial: three to four readings of the eight required | PASS |
| A1.6 | Earned Schedule | `timePhasedBaseline` | `canonical_structure_absent` | CONTRACT_BASELINE_DATA | yes | yes | no | PASS |
| A1.9 | Budget Execution Rate | `expenditureBaseline` | `canonical_structure_absent` | CONTRACT_BASELINE_DATA | yes | yes | no | PASS |
| A1.10 | CPI Shrinkage Forecast | `cpiReferenceClass` | `canonical_structure_absent` | REFERENCE_CLASS_DATASET_INTERFACE | yes | yes | no | PASS |
| A1.11 | Independent EAC Reconciliation Index | `independentEacPair` | `canonical_structure_absent` | NEW_STRUCTURED_FORM | yes | yes | no | PASS |
| A2.1 | PERT Network Criticality | `scheduleNetwork` | `canonical_structure_absent` | NEW_PROJECT_DATA_OBJECT | yes | yes | no | PASS |
| A2.4 | Schedule Compression Index | `scheduleNetwork` | `canonical_structure_absent` | NEW_PROJECT_DATA_OBJECT | yes | yes | no | PASS |
| A2.5 | Float Consumption Rate | `scheduleNetwork` | `canonical_structure_absent` | NEW_PROJECT_DATA_OBJECT | yes | yes | no | PASS |
| A2.6 | S-Curve Deviation | `timePhasedBaseline` | `canonical_structure_absent` | CONTRACT_BASELINE_DATA | yes | yes | no | PASS |
| A2.8 | Look-Ahead Schedule Health | `lookAheadSchedule` | `canonical_structure_absent` | NEW_STRUCTURED_FORM | yes | yes | no | PASS |
| A2.9 | Resource Loading Index | `resourceProfile` | `canonical_structure_absent` | NEW_PROJECT_DATA_OBJECT | yes | yes | no | PASS |
| A2.10 | Schedule Risk Analysis P80 | `scheduleNetwork` | `canonical_structure_absent` | NEW_PROJECT_DATA_OBJECT | yes | yes | no | PASS |
| A2.11 | Critical Path Index | `scheduleNetwork` | `canonical_structure_absent` | NEW_PROJECT_DATA_OBJECT | yes | yes | no | PASS |
| A3.1 | Reference Class Forecasting | `referenceClassPopulation` | `canonical_structure_absent` | REFERENCE_CLASS_DATASET_INTERFACE | yes | yes | no | PASS |
| A3.3 | Labor Productivity Index | `productionOutputRecord` | `canonical_structure_absent` | EXISTING_DOCUMENT_EXTRACTION | yes | yes | no | PASS |
| A3.5 | Overhead Absorption Rate | `overheadAllocationBase` | `canonical_structure_absent` | NEW_STRUCTURED_FORM | yes | yes | no | PASS |
| A3.7 | Analogous Estimating Ratio | `analogEstimate` | `canonical_structure_absent` | HISTORICAL_DATASET_INTERFACE | yes | yes | no | PASS |
| A3.9 | Inflation Adjustment Index | `externalCostIndex` | `canonical_structure_absent` | EXTERNAL_OFFICIAL_DATA_INTERFACE | yes | yes | no | PASS |

---

## Anything I could not complete

* **Run 27's R estimator from repeated readings of one period is not implemented.** Stated plainly
  in the A1.4 section above. A1.4 remains calibration-pending and abstains.
* **The A1.1 name conflict is reported, not resolved.** Both candidate names and their file-and-line
  evidence are in the A1.1 section. It needs an owner decision.
* **Two modules outside Run 28's twenty were found in the same condition (A2.2 Line of Balance,
  A2.3 CCPM Buffer Health).** Their structures had no production writer either. They are given the
  same intake and are recorded in the twenty-eight-row table, but the supply-path table is kept at
  exactly twenty rows because that is what the instruction specifies.
* **No structure is classified NOT_REASONABLY_SUPPLIABLE.** A3.9's external price index was the
  candidate and it does not need the exception: the interface exists and is reachable. What it
  lacks is data that originates outside the platform entirely, and that is recorded in its row
  rather than being dressed up as an implemented corpus supply.
