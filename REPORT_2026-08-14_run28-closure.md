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

---

## Final verification, on the exact final head

Defect 1 is that Run 28's verification and its final head were different commits. That is not
repeated here. The sequence actually followed:

1. all corrections made on `run28-closure`;
2. merged into `main` with `--no-ff`;
3. the closure freeze finalised on the merged head (stage-1 commit
   `65be2dbcb51c96c1bc47ad48825c8cb9c1dd8ce8`, manifest sha256
   `5e8c8ede73adf2171b48c1d43e1294299cee97ac1bdaedeebfc629133b25e159`);
4. this section committed, which is the LAST commit — no commit follows it;
5. **the complete suite run on that exact commit**, with a fresh migrated SQLite database per
   suite file, `PYTHONIOENCODING=utf-8`, `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`, and the
   runner's anchored `^RESULT: N/M( checks passed)?$` requirement;
6. `origin/main` confirmed equal to that commit after the push.

**The complete suite is 128 suites and 10811 checks, all green.** Run 28 finished at 127 suites
and 10730 checks; the closure adds `server/tools/test_run28_closure.py` (65 checks) and sixteen
further checks inside existing suites. The exact commit hash and the confirmation that
`origin/main` equals it are recorded in the run's handover message and are reproducible with
`git rev-parse HEAD` and `git rev-parse origin/main` on this branch.

---

# RUN 28 CLOSURE, SECOND PASS

Still Run 28. Not Run 28B, and Run 29 is not begun. Everything above this line is the first
pass's record and is not rewritten; where this pass overturns a judgement the first pass made,
it says so rather than quietly replacing it.

## 1. The final simulation version, and why

**`sim-2026.08-v12`. The first pass held the line at v11 and that judgement was wrong.**

The first pass argued the line should stay at v11 because "no arithmetic, band, boundary or
reported quantity moved". That is too narrow a reading of what a stamp identifies. A stamp
identifies **executable analytical behaviour**: if the layer, given one identical governed input,
emits something different from what v11 emitted, then results collected before and after are not
comparable, which is the exact ambiguity the stamp exists to prevent.

Settled by running both lines, not by arguing. `server/tools/test_run28_version_boundary.py`
extracts `canonical_v3.py` from git object `0e0dfbd` — the commit v11 was pushed at, which cannot
be mutated in place — imports it, **executes it**, and compares it with the current line on
identical inputs. On one governed input, a cost risk model with three risk events and no stated
dependence policy:

```
sim-2026.08-v11, executed from git   ->  p80_total_cost = 1200.0
the current line                     ->  StructureAbsent, reports nothing
```

Two further changes move what the layer emits, both asserted against git rather than described:

* `server/app/project_data.py` **does not exist at `0e0dfbd`**. Twenty-one of the twenty-three
  module-to-key entries were written by no production code, so a module needing one could only
  ever abstain. A module that could only abstain and can now compute is a behaviour change.
* `projectDataStructures` appears in no v11 stored row and appears in current ones.

The other direction is asserted too, so the divergence is understood rather than merely observed:
with the dependence policy stated, the current line reproduces v11's figure **exactly**. What
changed is what the layer refuses, not its arithmetic.

Preservation, asserted mechanically:

* every identifier in `SIMULATION_VERSION_HISTORY` is unique; v11 is not overwritten or re-used;
* the tuple **as it stood at `0e0dfbd`** is a strict PREFIX of the tuple now, read out of git, so
  this run appended and nothing else. It grew by exactly one stamp;
* `SIMULATION_VERSION_SUPERSEDED` names v11;
* `sim-2026.08-v2` remains executable evidence via `test_run7_fix_now_defects.py` and commit
  `021d5e2`.

**First v12 commit: recorded in section 5 below, which is the same commit the suite ran on.**

Scope stated honestly: the suite proves **at least one** divergence, which is all a boundary
needs. It does not claim to enumerate every divergence and does not imply a completeness it has
not established.

## 2. A1.1 naming closure

**The owner decided. `Monte Carlo EAC` → `Monte Carlo EAC Forecast`, final, and the current
naming authority was updated.**

The first pass found the conflict, aligned the surfaces to the authority, refused to edit the
authority on the strength of a prose sentence, and reported it as an owner decision. That was the
correct boundary and the owner has now crossed it explicitly. This is a **third rename beyond Run
28's two and it is authorised**.

* **The authority file changed.** `p0-baseline/module_renumbering_map.csv` line 2 now reads
  `A1.1,Monte Carlo EAC Forecast,1.1,A,Project Health,A1,Cost & EVM Performance,`.
* **Re-propagated from it**, not hand-edited into agreement: `assets/js/ds_defensibility_evidence.js`
  was regenerated by its own generator (`tools/build_run11_defensibility_evidence.py`) and the
  suite that requires it to be byte-identical to generator output still passes.
* **Current surfaces carrying the name**: `categories.js`, `taxonomy.js`, `knowledge.js`,
  `deepdive.js`, `charts3d.js`, `decision-ui.js`, `workspace.js`, `neural_flow.js`,
  `ds_defensibility_data.js`, `ds_defensibility_evidence.js`, `recommendation_options.js`,
  `canonical_v3.py`, and the authority itself. Display strings and prose only.
* **`server/tools/run17/population.py`** transcribes the decision so the mapping proof compares
  the registry against the specification as it now stands. The supervisory specification document
  itself is **not** edited: it is the immutable controlling authority, pinned in the authority
  tree, and this is a transcription of a later owner decision, not an edit of it.

**The stale `owner_prose_alias` label, reconciled.**
`research_fixtures/production_contract/monte_carlo_eac_forecast/contract.json` recorded
`Monte Carlo EAC Forecast` as `owner_prose_alias` against a `canonical_module_name` of
`Monte Carlo EAC`. It is no longer an alias for anything. Now: `canonical_module_name` is
`Monte Carlo EAC Forecast`; `owner_prose_alias` is **nulled rather than deleted**, with an
`owner_prose_alias_note` recording that the disagreement existed and how it was settled; and
`Monte Carlo EAC` is the head of `backward_compatible_aliases`, so a joiner written before the
rename still resolves the module. The fixture's `CHECKSUMS.sha256` was re-taken.

**Current active naming conflicts for A1.1 = 0.** The guard the owner asked for is
`test_run28_closure.py` section 3: it matches `Monte Carlo EAC` **not followed by "Forecast"**
across thirteen current surfaces, so the new name does not trip its own check and any reversion
does — in a display table (**fault F4**) or in a sentence of prose (**fault F11**).

Historical reports, historical freezes and the Run-12 participant record keep the old wording, and
that is asserted, not assumed: `test_run28_closure.py` goes red if the historical evidence is
cleaned up.

## 3. The 23 structure-key entries, reconciled

`code_audit/run28_v3_structure_key_reconciliation.csv`, 23 rows.

**The arithmetic gap the first pass left, and what caused it.** It reported "23 keys, 2
production-reachable, 21 fixture-only, 19 exercised through the intake", and 19 + 2 = 21, not 23.
The gap is a **conflation of two different units**:

```
V3_STRUCTURE_KEYS holds 23 MODULE-TO-KEY ENTRIES
                  over 18 DISTINCT KEYS
```

because one `scheduleNetwork` serves five Category-2 methods (A2.1, A2.4, A2.5, A2.10, A2.11) and
one `timePhasedBaseline` serves two (A1.6, A2.6). "23" was entries; "19" was the count of supply
rows exercised; "2" was distinct keys. Three different units in one sentence.

Reconciled per **entry**, which is the unit a module's supply question is actually asked in:

```
23 entries  =  19 that need the project-data intake  +  4 that do not
18 distinct keys, 2 of them written by production code today
duplicates = 0   classified = 23   unexplained = 0
reasonably supplyable but unreachable = 0
fixture-only structures masquerading as production supply paths = 0
```

**The four that do not belong on the intake route, each for its own reason:**

| entry | why not |
|---|---|
| **A1.1** `costDriverDistributions` | the module does not need it to compute. A1.1 executes today on the reported budget and cost index; the declared distribution set is an **enrichment** that lets the module state its own elicitation record, not a precondition. The intake accepts it anyway |
| **A2.7** `milestoneForecastHistory` | **produced by document extraction, not supplied.** `documents.py` assembles it from baseline finish dates already extracted per activity. A supplied record would be second-best evidence, and the merge rule makes the document-derived structure win |
| **A3.6** `costRiskModel` | **produced by document extraction, not supplied.** `documents.py` assembles it from the period's own risk register. Same rule, same reason |
| **A3.8** `parametricCostModel` | the module is **registered disabled, laboratory-only, never executed.** A supply route for a structure no production execution can reach is a path to nowhere. Activating A3.8 is not this run's work and is not done |

Neither side of the check is derived from the other: the population is read from
`V3_STRUCTURE_KEYS` at check time, the producer column is verified by searching `server/app` for
an assignment of each key, and the intake's acceptance is decided by the intake's own vocabulary.
**Fault F12** adds a twenty-fourth entry (`A9.9 → run28ClosureOrphanStructure`) to production: the
guard goes RED because it has no classified row.

## 4. Participant v1, preserved executably

`server/tools/test_run28_participant_v1_preservation.py`, 19 checks.

**The exact Git object: `c44e3ced94a22a9def35fa5a2be3a2268fbed6bb`** — "Run 12 Gates 11-12:
simulation version sim-2026.08-v7, release freeze record, checksums and guard proof", found with
`git log --diff-filter=A -- code_audit/run12_participant_package_checksums.sha256`.

**Why this was necessary.** The first pass reported that fourteen of the seventy files had already
drifted from the Run-12 record before this closure, and did not draw the consequence: **the live
filesystem is not evidence for `og-participant-2026.08-v1`.** A preservation claim checked against
the working tree would be comparing the current package with the historical record.

What the test does:

1. extracts all seventy files from that commit into an **isolated temporary directory**, never
   into the application;
2. verifies the inventory: seventy files, no more and no fewer, exactly the record's names;
3. verifies **all seventy checksums** against the Run-12 record — all hold;
4. verifies the record itself has not been rewritten, byte for byte against the git object;
5. verifies `og-participant-2026.08-v2` **independently**, against its own successor record and
   the live tree, and asserts the two records genuinely differ (with `taxonomy.js` among the files
   that moved, which is what required a successor at all);
6. proves independence: a **current** v2 file is copied into the sandbox and mutated, the mutation
   is confirmed by re-reading it, and the reconstructed v1 hashes are recomputed and unchanged —
   because the reconstruction reads the git object graph and not the disk.

It also asserts the drift itself (≥14 of 70 files differ from v1 in the live tree), so the reason
this file exists cannot be lost.

**Non-vacuity, inline and in the campaign.** Inline: one extracted historical byte is mutated in
the sandbox, confirmed by re-reading, the checksum guard reports **exactly** `assets/js/taxonomy.js`
and no other file, the byte is restored and all seventy are green again. In the campaign,
**fault F13** alters the Run-12 record in the working tree: 19/19 → RED 18/19 → 19/19.

No historical file was restored into the live application. The Run-12 record was not rewritten.

## 5. Exact final-head verification

Recorded in the run's handover message with the commit hash, and reproducible with
`git rev-parse HEAD`, `git rev-parse origin/main` and `git status --porcelain`. The last commit on
`main` is the one the complete suite ran on; nothing follows it before the push.

**The complete suite is 130 suites and 10866 checks, all green** — `server/run_all_suites.sh`,
fresh migrated SQLite per test file, `PYTHONIOENCODING=utf-8`, anchored
`^RESULT: N/M( checks passed)?$`, nonzero exit fails. The first pass finished at 128 / 10811; this
pass adds `test_run28_version_boundary.py` (15) and `test_run28_participant_v1_preservation.py`
(19) and further checks inside existing suites.

## 6. A2.7, rechecked on the final tree

Unchanged and still true. `canonical_v3.milestone_trend` raises `StructureAbsent` for any milestone
with fewer than two forecasts; `documents._milestone_forecast_history` needs two or more schedule
snapshots and drops a milestone seen once rather than padding it; the corpus supplies repeated
forecasts for a stable identity across reporting periods — three milestones followed, D200 moving
14 Aug → 28 Aug, a fourteen-day drift and a fourteen-day variance against the committed date; the
contract's worked example reproduces (100 → 104, 108, 111 → slips 4, 8, 11, deteriorating); no
status colour is asserted. **F2** weakens the canonical guard (78/78 → 75/78); **F8** weakens the
real-corpus assembler (78/78 → 69/78).

## 7. A3.6, rechecked on the final tree

Single-event canonical route works. Multi-event route with no declared dependence policy
**refuses**. Declared-dependence route works and reproduces v11's figure exactly. The same seed
reproduces the distribution; two different seeds do not, which a deterministic proxy structurally
cannot. P80 is the empirical 0.80 quantile of the simulated total-cost distribution under the
frozen right-continuous convention; the contract's own oracle reproduces (base 100, one event
p=0.5 impact 20 → 120). With no model at all the module abstains rather than inflating the cost
index. The real route's dependence policy is declared from what the register itself supports.
**F6** makes the policy optional again (78/78 → 76/78).

## 8. Kalman parameter honesty, rechecked

No hidden Q, no hidden R. Both variance sources are required and a blank in either is refused,
asserted per field. With no state-space record the module abstains; no moving average is
substituted and **no traffic-light status is generated**. Both variances and both provenance
strings travel out onto the result. The v10 literals `q = 0.01` and `r = 0.1` are assigned nowhere
in `models_evm.py` — checked with `ast` over the module's assignments, so the docstring recording
what v10 did does not satisfy the check. Contract oracle reproduces (gain 0.5, state 1.5).
**F7** substitutes a hidden `"assumed"` default for both provenance fields (78/78 → 75/78).

**Q and R are not invented in this closure. Run 27's R estimator from repeated readings of one
period is still not implemented.** Calibration remains Run 33.

## 9. Untracked-file protection, rechecked

`walk_production()` discovers names from the filesystem and reports git-tracked state as an
attribute; `test_run22_production_tree_completeness.py` asserts that attribute over the whole
surface; `test_run8_retest_classify_27.py` enumerates `git status --porcelain --untracked-files=all`
alongside `git diff`. The four cases the guard claims: **added**, **modified**, **deleted** and
**renamed** are each proved in a real copy of the real tree inside that suite; **untracked** is
proved on the real tree by **fault F1** — baseline 44/44 → probe file created and confirmed present
on the filesystem and in `git status -uall` → guard RED 40/44 naming that exact path, with an
anchored RESULT line → deleted → 44/44.

## 10. Programme invariants, on the final tree

| invariant | state |
|---|---|
| historical simulation v2 reproducible | yes, `test_run7_fix_now_defects.py` executes it from `021d5e2` |
| simulation version history unique | yes, and append-only against git |
| current simulation version truthful | `sim-2026.08-v12`, proved by execution |
| participant v1 historically reproducible | yes, from `c44e3ce`, all 70 checksums |
| participant v2 successor reproducible | yes, against the live tree |
| participant experimental sequence | unchanged: preliminary, lock, reveal, final, lock |
| voting | exactly 2, A1.7 and A1.8 |
| concept-only activation | unchanged, 0 activated |
| Material Cost Variance A3.4 | registered, disabled, non-voting, not executed |
| Category-9 qualification | still honestly recorded as pending Run 31 |
| unauthorized renames | none: the third rename is the owner's explicit decision |
| production Postgres | not accessed; no production credentials; no real participant data |

## Successor records, second pass

| record | value |
|---|---|
| freeze identifier | `OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN28-CLOSURE-V12-1` |
| manifest | `research/freeze/RUN28_CLOSURE_V12_FREEZE_2026-08-14.json` |
| supersedes | `...-RUN28-CLOSURE-V11-2`, preserved unchanged — `RUN28_CLOSURE_FREEZE_2026-08-14.json` still verifies against its own companion `.sha256` |
| grandparent | `...-RUN28-CANONICAL-CAT1-3-V11-1`, likewise preserved |
| production surface | 228 files, `code_audit/run28_closure_production_tree.sha256` |
| participant package | `og-participant-2026.08-v2`, record re-taken over the renamed bytes |
| analytical line | `sim-2026.08-v12` |

### The twenty-three structure-key entries

| # | key | module | producer | needs intake | corpus populates | behaviour when absent |
|---|---|---|---|---|---|---|
| 1 | `costDriverDistributions` | A1.1 | none | no | no | the module computes without it |
| 2 | `bayesianEacModel` | A1.3 | none | yes | no | NOT ESTIMABLE, reason code canonical_structure_absent |
| 3 | `kalmanStateSpaceModel` | A1.4 | none | yes | no | NOT ESTIMABLE, reason code canonical_structure_absent |
| 4 | `timePhasedBaseline` | A1.6 | none | yes | no | NOT ESTIMABLE, reason code canonical_structure_absent |
| 5 | `expenditureBaseline` | A1.9 | none | yes | no | NOT ESTIMABLE, reason code canonical_structure_absent |
| 6 | `cpiReferenceClass` | A1.10 | none | yes | no | NOT ESTIMABLE, reason code canonical_structure_absent |
| 7 | `independentEacPair` | A1.11 | none | yes | no | NOT ESTIMABLE, reason code canonical_structure_absent |
| 8 | `scheduleNetwork` | A2.1 | none | yes | no | NOT ESTIMABLE, reason code canonical_structure_absent |
| 9 | `scheduleNetwork` | A2.4 | none | yes | no | NOT ESTIMABLE, reason code canonical_structure_absent |
| 10 | `scheduleNetwork` | A2.5 | none | yes | no | NOT ESTIMABLE, reason code canonical_structure_absent |
| 11 | `timePhasedBaseline` | A2.6 | none | yes | no | NOT ESTIMABLE, reason code canonical_structure_absent |
| 12 | `milestoneForecastHistory` | A2.7 | documents.py | no | yes | NOT ESTIMABLE, reason code canonical_structure_absent |
| 13 | `lookAheadSchedule` | A2.8 | none | yes | no | NOT ESTIMABLE, reason code canonical_structure_absent |
| 14 | `resourceProfile` | A2.9 | none | yes | no | NOT ESTIMABLE, reason code canonical_structure_absent |
| 15 | `scheduleNetwork` | A2.10 | none | yes | no | NOT ESTIMABLE, reason code canonical_structure_absent |
| 16 | `scheduleNetwork` | A2.11 | none | yes | no | NOT ESTIMABLE, reason code canonical_structure_absent |
| 17 | `referenceClassPopulation` | A3.1 | none | yes | no | NOT ESTIMABLE, reason code canonical_structure_absent |
| 18 | `productionOutputRecord` | A3.3 | none | yes | no | NOT ESTIMABLE, reason code canonical_structure_absent |
| 19 | `overheadAllocationBase` | A3.5 | none | yes | no | NOT ESTIMABLE, reason code canonical_structure_absent |
| 20 | `costRiskModel` | A3.6 | documents.py | no | yes | NOT ESTIMABLE, reason code canonical_structure_absent |
| 21 | `analogEstimate` | A3.7 | none | yes | no | NOT ESTIMABLE, reason code canonical_structure_absent |
| 22 | `parametricCostModel` | A3.8 | none | no | no | registered disabled: never executed, so the structure is nev |
| 23 | `externalCostIndex` | A3.9 | none | yes | no | NOT ESTIMABLE, reason code canonical_structure_absent |

### The twenty-eight modules, final

| id | module | canonical impl | supply path | executes | abstains | disabled | cal R33 | validation pending | lineage R31 | disposition |
|---|---|---|---|---|---|---|---|---|---|---|
| A1.1 | Monte Carlo EAC Forecast | yes | yes | yes | no | no | yes | yes | yes | CANONICAL_RETAINED_CALIBRATION_PENDING |
| A1.2 | CUSUM Anomaly Monitor | yes | yes | yes | no | no | yes | yes | yes | CANONICAL_FROZEN_DESIGN |
| A1.3 | Bayesian EAC | yes | yes | no | yes | no | yes | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A1.4 | Kalman Filter SPI Smoother | yes | yes | no | yes | no | yes | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A1.5 | ARIMA CPI Forecast | yes | yes | no | yes | no | no | yes | yes | CANONICAL_IMPLEMENTED_HISTORY_REQUIRED |
| A1.6 | Earned Schedule | yes | yes | no | yes | no | no | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A1.9 | Budget Execution Rate | yes | yes | no | yes | no | no | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A1.10 | CPI Shrinkage Forecast | yes | yes | no | yes | no | yes | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A1.11 | Independent EAC Reconciliation Index | yes | yes | no | yes | no | yes | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A2.1 | PERT Network Criticality | yes | yes | no | yes | no | no | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A2.2 | Line of Balance | yes | yes | no | yes | no | yes | yes | yes | CANONICAL_EXTENDED_CALIBRATION_PENDING |
| A2.3 | CCPM Buffer Health | yes | yes | no | yes | no | yes | yes | yes | CANONICAL_EXTENDED_CALIBRATION_PENDING |
| A2.4 | Schedule Compression Index | yes | yes | no | yes | no | no | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A2.5 | Float Consumption Rate | yes | yes | no | yes | no | no | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A2.6 | S-Curve Deviation | yes | yes | no | yes | no | no | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A2.7 | Milestone Trend Analysis | yes | yes | yes | no | no | yes | yes | yes | CANONICAL_IMPLEMENTED_AND_WIRED |
| A2.8 | Look-Ahead Schedule Health | yes | yes | no | yes | no | no | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A2.9 | Resource Loading Index | yes | yes | no | yes | no | no | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A2.10 | Schedule Risk Analysis P80 | yes | yes | no | yes | no | no | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A2.11 | Critical Path Index | yes | yes | no | yes | no | no | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A3.1 | Reference Class Forecasting | yes | yes | no | yes | no | no | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A3.2 | Contingency Burn Rate | yes | yes | yes | no | no | yes | yes | yes | CANONICAL_RETAINED_BANDS_REMOVED |
| A3.3 | Labor Productivity Index | yes | yes | no | yes | no | no | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A3.5 | Overhead Absorption Rate | yes | yes | no | yes | no | no | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A3.6 | Cost Risk Analysis P80 | yes | yes | yes | no | no | yes | yes | yes | CANONICAL_IMPLEMENTED_AND_WIRED |
| A3.7 | Analogous Estimating Ratio | yes | yes | no | yes | no | no | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |
| A3.8 | Parametric Cost Index | yes | yes | no | no | yes | no | yes | yes | DISABLED_LABORATORY_ONLY |
| A3.9 | Inflation Adjustment Index | yes | yes | no | yes | no | no | yes | yes | CANONICAL_IMPLEMENTED_STRUCTURE_REQUIRED |

### Non-vacuity, thirteen faults

| id | fault | guard | before | observed | after | injection confirmed | verdict |
|---|---|---|---|---|---|---|---|
| F1 | a harmless UNTRACKED file created inside the protected production surface. The guard must repor | `test_run22_production_tree_completeness.py` | 44/44 | **RED 40/44** | 44/44 | yes, re-read from disk | PASS |
| F2 | A2.7's minimum-history guard weakened so ONE forecast is enough. A single baseline and a single | `test_run28_closure.py` | 78/78 | **RED 75/78** | 78/78 | yes, re-read from disk | PASS |
| F3 | the approved rename reverted on ONE current surface while the registry keeps the new name: exac | `test_run28_closure.py` | 78/78 | **RED 76/78** | 78/78 | yes, re-read from disk | PASS |
| F4 | the retired A1.1 name reintroduced in the DISPLAY TABLE of the registry the taxonomy is generat | `test_run28_closure.py` | 78/78 | **RED 76/78** | 78/78 | yes, re-read from disk | PASS |
| F5 | the supply path removed for the nineteen v3 structures: the intake stops accepting them, so the | `test_run28_closure.py` | 78/78 | **RED 72/78** | 78/78 | yes, re-read from disk | PASS |
| F6 | A3.6's dependence policy made optional again, so a many-event model silently assumes independen | `test_run28_closure.py` | 78/78 | **RED 76/78** | 78/78 | yes, re-read from disk | PASS |
| F7 | a hidden default substituted for Q and R provenance, so an uncalibrated variance passes as a ca | `test_run28_closure.py` | 78/78 | **RED 75/78** | 78/78 | yes, re-read from disk | PASS |
| F9 | A DUPLICATE SIMULATION VERSION: the history is made to carry v11 twice, which is what an overwr | `test_run28_version_boundary.py` | 15/15 | **RED 12/15** | 15/15 | yes, re-read from disk | PASS |
| F10 | the stamp rolled back to v11 while the layer's behaviour is v12's, so already-collected results | `test_run28_version_boundary.py` | 15/15 | **RED 13/15** | 15/15 | yes, re-read from disk | PASS |
| F11 | the retired A1.1 name reintroduced in a sentence of prose on a current knowledge surface, which | `test_run28_closure.py` | 78/78 | **RED 76/78** | 78/78 | yes, re-read from disk | PASS |
| F12 | AN ORPHAN STRUCTURE KEY: a twenty-fourth module-to-key entry added to production with no classi | `test_run28_closure.py` | 78/78 | **RED 76/78** | 78/78 | yes, re-read from disk | PASS |
| F13 | the historical Run-12 participant record altered. The reconstruction reads the git object, so t | `test_run28_participant_v1_preservation.py` | 19/19 | **RED 18/19** | 19/19 | yes, re-read from disk | PASS |
| F8 | the real-corpus assembler admits a milestone with only one historical forecast, so a single bas | `test_schedule_milestones.py` | 78/78 | **RED 69/78** | 78/78 | yes, re-read from disk | PASS |

## What the second pass could not complete

* **Run 27's R estimator is still not implemented.** A1.4 abstains; Q and R are not invented.
* **The version-boundary suite proves at least one divergence, not all of them.** It does not
  enumerate every behavioural difference between v11 and v12 and does not claim to.
* **A3.8 Parametric Cost Index is still disabled laboratory-only.** Its structure key has no
  production supply route because no production execution can reach it. Activating it is Run 29+
  work and is not done.
