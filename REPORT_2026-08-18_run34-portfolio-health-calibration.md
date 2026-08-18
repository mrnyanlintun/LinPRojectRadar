# Run 34 — Portfolio Health calibration and parameter provenance (`sim-2026.08-v22`)

**Branch `run34-portfolio-health-calibration` from `main` at `f5c52d3`.**
Protocol: `research/methodology/run34_portfolio_calibration_protocol.md`.
Artifacts: `code_audit/run34_*`.

---

## 1. Starting Run-33 commit

`HEAD == main == origin/main == f5c52d3fd97498e031bad7e93ceb5cdc7ee65151`, tree clean, verified
from git before any edit. `sim-2026.08-v21`; participant `og-participant-2026.08-v11`; synthetic
`OG-SYNTH-0.5`; voting exactly 2 (A1.7 TCPI, A1.8 VAC).

## 2. The exact five-module scope

Derived mechanically from `p0-baseline/module_renumbering_map.csv`. **Five rows, five unique
identities, missing 0, duplicates 0.** `code_audit/run34_portfolio_health_scope.csv`.

| module | PH | name | canonical implementation |
|---|---|---|---|
| D1.1 | PH.1 | Isolation Forest | `canonical_v8.isolation_forest` |
| D1.2 | PH.2 | Portfolio Outlier Detection | `canonical_v8.portfolio_outlier` |
| D1.3 | PH.3 | Signal Trajectory Classifier | `canonical_v8.trajectory_classifier` |
| D1.4 | PH.4 | Cross-project Pattern Detector | `canonical_v8.cross_project_pattern` |
| D1.5 | PH.5 | Anomaly Score | `canonical_v8.anomaly_profile` |

## 3. The predeclared calibration protocol

Committed at **`a2ed922`, before any calibration search was written or run** — the ordering is a
matter of record, not a claim. It predeclares the objective, the candidate parameters and ranges,
the calibration and holdout datasets, the seeds, the metrics, the minimum acceptable conditions,
the decision rule, the tie-break, the compute-budget consideration, the sensitivity analysis and
the prohibited post-hoc changes.

**It also discloses that I was not blind.** Run 33 had already measured within-production
stability at t = 100/400/1000 (0.986049 / 0.995392 / 0.997836). Declaring a stability cut-point
after seeing those numbers would be choosing the answer and calling it a rule, so the decision
rule was built so that **its controlling clause does not depend on any cut-point fitted to them**:
an operational-relevance gate decidable from the state of the corpus. The stability numbers are
still measured and reported in full; they are simply not what selects the parameter.

No amendment was required. The protocol is unmodified.

## 4. PH.1 tree-count decision

**Retained at 100. `TREE_COUNT_CALIBRATION = UNRESOLVED_NO_OPERATIONAL_CONSEQUENCE`.**

Measured on the predeclared stability fixture across all 30 seeds
(`code_audit/run34_ph1_tree_count_calibration.csv`):

| t | S (rank stability) | A1 | A10 | score variance | runtime | peak memory |
|---|---|---|---|---|---|---|
| 100 | 0.986049 | 0.2299 | 0.4942 | 7.09e-05 | 0.401 s | 2.5 MB |
| 400 | 0.995392 | 0.5011 | 0.6717 | 1.78e-05 | 1.634 s | 9.1 MB |
| 1000 | 0.997836 | 0.7034 | 0.7495 | 6.60e-06 | 4.381 s | 22.4 MB |

Marginal: 100→400 `ΔS = +0.009343`, instability ratio 0.3303, runtime ×4.08. 400→1000
`ΔS = +0.002444`, instability ratio 0.4696, runtime ×2.68.

**D2, the controlling clause, FAILS — decided by executing the real production route, not by
assertion.** PH.1 on the corpus as it stands abstains (`STRUCTURE_ABSENT`): no governed portfolio
cohort is supplied, so PH.1 produces no operational reading and no authoritative flag under any
schema. A stability/compute trade-off requires units on both sides; here one side has none, so
**no candidate has defensible superiority** and D4 applies: retain the published default.

**The D3 counterfactual is reported and independently corroborates it.** Had the gate passed, D3
would still have retained 100: the 100→400 runtime ratio is **4.08**, failing D3's `≤ 4×` cost
condition. Two independent clauses reach the same answer.

**Cross-implementation Spearman was not used and was not computed.** The protocol forbids it as a
basis for selection and Run 33 established why: at t = 100 the implementation agrees with *itself*
across seeds (0.986049) essentially as closely as with scikit-learn (0.986057).

**No claim is made that 400 or 1,000 is the correct operational setting.**

## 5. PH.1 threshold disposition

**The frozen 0.576 remains a `SYNTHETIC_LAB_CALIBRATION` artifact and authorises nothing
operationally.** Run 34 tightened its confinement: it was already schema-bound, and it is now
**cohort-bound as well** — it yields no flag below the canonical cohort size even under its own
schema. `operational_anomaly_threshold` is classified **`UNSUPPORTED`** and is **not applied**.

**Cohort-size policy (§6B), now explicit and enforced:**

| cohort | behaviour |
|---|---|
| n < 3 | **`NOT_ESTIMABLE`.** No score of any kind. (v21 computed from n = 2.) |
| 3 ≤ n < 10 | Continuous exploratory score, `SMALL_COHORT_LIMITATION` explicit, **no authoritative flag**. |
| n ≥ 10 | Canonical score under the governed cohort/schema/model identity. **This does not authorise a field threshold.** |

**Holdout (D6), scored once, after selection was final:** ROC-AUC **0.9968**, PR-AUC 0.9263,
separation +0.2397 (calibration set: 0.9984 / 0.9698 / +0.2389). These are **separation statistics
on synthetic data with ground truth defined before the detector**. They are not field performance,
not a false-positive rate, not predictive validity, and they authorise no threshold.

## 6. PH.2 weighting disposition

**The composite is withdrawn. `composite = NONE`, disposition `PARAMETER_PROVENANCE_BLOCKED`,
result type `FEATURE_PERCENTILE_PROFILE`.**

v21 emitted an equal-weighted composite. It was *labelled* `OWNER_POLICY` — but it was emitted,
and an emitted number is read as a measurement whatever the label beside it says. Equal weighting
is an owner-policy choice, not a canonical fact, and §7B closes the gap: absent governed weights
the module returns the per-feature profile and no composite.

**Nothing measured was lost.** The supplied oracle midranks are unchanged and live in the profile:
`[1, 2, 3, 10] → 1/8, 3/8, 5/8, 7/8`, exact, through the production route. The version-boundary
proof asserts the per-feature midranks are **byte-identical across v21 and v22**, so what was
withdrawn is a *weighting*, not a *measurement*.

**Orientation (§7A):** four declarable orientations now — higher-is-worse, lower-is-worse,
**`TWO_SIDED`** (new; ranked on distance from the cohort centre, because treating it as one-sided
would declare half its adverse tail favourable) and no-adverse-orientation. **An undeclared or
unrecognised orientation is refused**; nothing is defaulted or inferred.

**Bands:** none. No percentile-to-colour mapping exists or was created.

## 7. PH.3 history and direction policy

- **Minimum observations predeclared at 3**; below it, `NOT_ESTIMABLE`. Not tuned.
- **Actual reporting times** enter the fit. Equal spacing is **reported** (`equally_spaced`),
  never assumed, so a reader can tell a genuinely regular series from one treated as regular.
  The regression trace, observation dates, slope units, orientation and history length are all
  preserved.
- **Vocabulary is the contract's:** `IMPROVING` / `STABLE` / `DETERIORATING` / `NOT_ESTIMABLE`.
  v21's `FLAT` is renamed `STABLE` and retained as a backward alias so stored v21 results stay
  readable; nothing emits it.
- **The 1e-12 is numerical tolerance for floating-point zero, and is identified as such.** It is
  not an operational threshold. `slope_magnitude_bands` is classified `UNSUPPORTED` and not
  applied. The supplied oracle is unchanged: slope −1/10, q = −1, AdverseSlope +1/10,
  `DETERIORATING`.

## 8. PH.4 distance/radius disposition

**Continuous distance only. The 0.15 radius stays retired and nothing replaced it.**
`match_radius` is classified `UNSUPPORTED` and not applied. The explicit feature schema,
normalization rule, missing-feature policy, cohort identity, metric and model version are all
required; comparison across schemas or normalization versions is refused. The tie rule is
deterministic and declared, and input ordering does not change any substantive result.

## 9. PH.5 weight/composite disposition

**`score = null`, `PARAMETER_PROVENANCE_BLOCKED`. Preserved, and now measured rather than
merely unwired.**

Run 34 threaded a governed weight record through the route so the block is a *measured* absence:
`governed_weights_supplied` is a field, and it reads false because no record exists. And the
reason now separates the **two** preconditions §10B/§10C require: there are no governed weights,
**and** there is no governed missingness policy. Even had weights been supplied, the composite
would still abstain on the second.

Equal weights are never adopted as a default; weights are never derived from the fixture the
composite would be evaluated on; duplicate lineage cannot reinforce (evidence bodies are counted,
not constituents); a missing constituent never silently reweights the remainder.

## 10. Real-corpus outcome

`code_audit/run34_real_portfolio_calibration_reconciliation.csv`. **All five abstain**: the
controlled portfolio supplies no governed cohort, no history, no weights and no calibration
record. Real-corpus computation is not possible, continuous output is not possible, and an
authoritative flag is not possible — for any of the five. No module was forced to produce a
status.

## 11. Parameter-provenance table

`code_audit/run34_portfolio_parameter_provenance.csv` — **19 parameters, no unclassified
parameter, and nothing classified `UNSUPPORTED` is applied operationally** (asserted from the live
registry, not asserted about).

| class | n | examples |
|---|---|---|
| `UNSUPPORTED` | 7 | operational anomaly threshold, PH.2 weights and bands, PH.3 magnitude bands, PH.4 radius, PH.5 weights and missingness policy — **all `applied = no`** |
| `OWNER_POLICY` | 5 | cohort minima, PH.3 minimum observations, PH.4 tie rule and standardisation |
| `THEORETICAL_CONSTANT` | 4 | seed, height limit, `c(n)` harmonic form, numerical tolerance |
| `PUBLISHED_DEFAULT` | 2 | `n_trees = 100`, `psi = 256` |
| `SYNTHETIC_LAB_CALIBRATION` | 1 | frozen 0.576 threshold — schema-bound, cohort-bound, `applied = no` |
| `EMPIRICAL_CALIBRATION` | 0 | **nothing is empirically calibrated** |
| `HEURISTIC` | 0 | — |

Seven `UNSUPPORTED` rows is the honest count. Each is a parameter that would have to be invented
to produce a reading, so the reading is withheld instead.

### Parameter-provenance count correction (Run-34 final closure)

**Original headline row count.** The provenance artifact contained — and still contains — **21
rows**. That is what the generator's own console line reported: `wrote
run34_portfolio_parameter_provenance.csv: 21 rows`.

**Original reported distribution.** `UNSUPPORTED` 7, `OWNER_POLICY` 5, `THEORETICAL_CONSTANT` 4,
`PUBLISHED_DEFAULT` 2, `SYNTHETIC_LAB_CALIBRATION` 1, `EMPIRICAL_CALIBRATION` 0, `HEURISTIC` 0.
**Total 19.**

**Why the distribution summed to 19 while the artifact held 21 rows.** Because **two of the 21
rows were never parameters.** They are acceptance counters:

| module | parameter | value | class |
|---|---|---|---|
| `-` | `UNCLASSIFIED PARAMETERS` | `0` | `-` |
| `-` | `UNSUPPORTED PARAMETERS APPLIED` | `0` | `-` |

Each carries `module = '-'`, `parameter_class = '-'` and a *count* as its value. They assert two
acceptance conditions; they describe no parameter. 19 parameters + 2 counters = 21 rows, and the
distribution was right to sum to 19.

**Authoritative final distribution** (derived from the artifact by
`code_audit/run34_parameter_class_count_closure.csv`, all seven classes including zeros):

| class | n |
|---|---|
| `UNSUPPORTED` | 7 |
| `OWNER_POLICY` | 5 |
| `THEORETICAL_CONSTANT` | 4 |
| `PUBLISHED_DEFAULT` | 2 |
| `SYNTHETIC_LAB_CALIBRATION` | 1 |
| `EMPIRICAL_CALIBRATION` | **0** |
| `HEURISTIC` | **0** |
| **total governed parameters** | **19** |

**The two "omitted" rows are not `HEURISTIC`, and `HEURISTIC` is genuinely zero.** They are not
parameters of any class. Stated mechanically: filtering the artifact to `row_type = PARAMETER`
yields 19 rows, and the seven class counts over those 19 rows sum to 19 exactly.

**Was the CSV wrong, or only the prose?** *Neither was wrong.* This is the finding, and it differs
both from the contract's premise and from the diagnosis offered to me, so it is stated plainly:

- The **artifact was correct.** 21 rows, of which 19 are parameters and 2 are counters.
- The **report was correct.** Section 11 as merged at `41f01e8` states "**19 parameters**" and
  lists all seven classes, including the two zeros, summing to 19. **The report never claimed 21
  parameters.** Verified by reading the report out of the merged git object, not the working tree:
  `git show 41f01e8:REPORT_…md` contains no "21 parameters", no "rows = 21" and no "= 21".
- The contract's section states that "the Run-34 report states parameter-provenance rows = 21".
  That claim is not supported by the merged report. Both 21 and 19 were correct *about different
  things* — 21 rows, 19 parameters — and the appearance of a contradiction came from reading a
  row count as a parameter count.

**What was genuinely defective was the artifact's structure, not either number.** Nothing
distinguished a counter row from a parameter row except a `module` of `-`, so a reader counting
rows could not help but read 21 parameters. The fix is structural: a declared **`row_type`**
column (`PARAMETER` / `ACCEPTANCE_COUNTER`), and every count downstream taken over
`row_type == PARAMETER` rather than over the row count.

**The section-1 target of "21 unique parameter identities" is NOT satisfied and has NOT been
padded.** There are 19 governed parameters; reaching 21 would require inventing two, which the
same contract forbids. The target was written from the same row-count-as-parameter-count reading.
The *spirit* of section 1 is satisfied in full: every governed parameter classified, blanks 0,
duplicates 0, illegal classes 0, counts summing to the real parameter total, and the discrepancy
reported rather than absorbed. The closure artifact records it as
`SECTION_1_TARGET_DISCREPANCY = REPORTED_DISCREPANCY`.

**Did any calibration conclusion change? No.** Not one. The tree count is still 100, the frozen
threshold is still synthetic and schema- and cohort-bound and unapplied, PH.2's composite is still
`NONE`, PH.3's history and time policy are unchanged, PH.4 is still continuous distance only,
PH.5's score is still `null`, empirical validation is still pending for all five, and voting is
still false for all five. This closure changed an artifact's *structure* and a *count's
description*. It changed no measurement, no parameter and no decision.

**Module reconciliation (contract section 3), derived from the code and not from the artifact
under test.** Expected parameters per module come from the live `canonical_v8` registry:

| module | expected | represented | missing | extra |
|---|---|---|---|---|
| D1.1 | 9 | 9 | 0 | 0 |
| D1.2 | 2 | 2 | 0 | 0 |
| D1.3 | 3 | 3 | 0 | 0 |
| D1.4 | 3 | 3 | 0 | 0 |
| D1.5 | 2 | 2 | 0 | 0 |

**Five modules represented, missing governed parameter records 0, unexplained extra records 0.**

An AST scan of the governed code for numeric literals that might be unregistered parameters found
exactly two, and **both were adjudicated non-parameters with a mechanical reason**, recorded in
the closure rather than silently dropped:

- the epoch origin `1970` in `_as_days` — an OLS slope is invariant to a shift of the time origin,
  verified by fitting the same series against two origins and obtaining the identical exact slope
  `-1/10`;
- the `0.5` degenerate-normaliser fallback in `IsolationForest.anomaly_score` — **unreachable**
  from the PH.1 route, because the cohort gate refuses below three eligible projects so
  `psi >= 3` and `c(3) = 1.2074 > 0`, verified over every reachable cohort size.

## 12. The 20-fault campaign

`code_audit/run34_fault_injection_results.csv`.
**required 20 · applied 20 · intended RED 20 · restored GREEN 20 · NOT_APPLIED 0 · crashes
accepted as RED 0.**

**Six faults were wrong on the first pass and each correction is recorded in the campaign file
rather than quietly repointed.** F2 *crashed*: removing the cohort gate entirely made a
one-project cohort reach the forest constructor, and a crash is not a RED — the honest mutation is
v21's own `n < 2` gate, exercised on the two-project case that runs on both sides. F6 went red for
the *wrong reason*: leaving an invalid orientation string in place still refuses downstream,
because an unrecognised orientation is not rankable either; the defect being modelled is a silent
*default*, so the mutation defaults. F7 returned the wrong tuple shape and crashed. F9 needed
**both** the count gate and the distinct-times gate, since either alone still refuses. F15 and F20
had anchors that were not unique or not in the file the value actually lives in.

Faults **4, 19 and 20** guard the protocol discipline itself: that selection completed before the
holdout was read; that a synthetic fixture cannot relabel itself as empirical field validation;
and that the calibration and holdout sets are genuinely independent draws.

## 13. Version and package decisions

- **Simulation → `sim-2026.08-v22`.** Production behaviour changed, so the stamp moved, and the
  move is proved **by execution** (`code_audit/run34_simulation_version_execution_proof.csv`):
  the v21 package is extracted from its git object and run beside the current one on identical
  inputs. **Three genuine divergences** — the PH.2 composite withdrawn (with per-feature midranks
  byte-identical), PH.1 `NOT_ESTIMABLE` at a two-project cohort, PH.3 `STABLE` with the time basis
  reported — and **two real non-divergences**: with no governed cohort both lines abstain
  identically with the same five reasons, and A1.7 TCPI is byte-identical.
- **Synthetic → `OG-SYNTH-0.6`.** New labelled calibration and holdout fixtures. `OG-SYNTH-0.1`
  to `0.5` untouched; `0.5` demoted from current, its record not rewritten.
- **Participant → `og-participant-2026.08-v11`, UNCHANGED.** No participant-facing byte moved.
- **Production tree → successor manifest**, and for the first time since Run 22 a successor
  **authority** manifest: the predeclared protocol is a scientific authority document. Both
  parents kept addressable and unrewritten.

## 14. Remaining empirical-validation work (Run 35)

**Layer 5 — real empirical validation — is `PENDING` for all five modules, without exception.**
Nothing in Run 34 is field validated. Synthetic calibration establishes numerical behaviour,
stability, sensitivity and known anomaly separation; it establishes nothing about real
construction-project anomaly prevalence, field false-positive rates, practitioner usefulness,
operational business thresholds or predictive validity.

Run 35 owns: empirical validation against real project outcomes; the final parsimony and removal
decisions; and, only if the owner wants them, an operational PH.1 threshold, PH.2 weights, PH.3
magnitude distinctions and a PH.4 radius — **none of which exists today, and none of which was
created here.**

---

## The five assurance layers, per module, never collapsed

`code_audit/run34_portfolio_health_calibration_closure.csv`. **5 rows, 5 unique, voting false for
all five, unsupported operational thresholds 0, invented weights 0, synthetic-as-empirical claims
0.**

| module | 1 canonical | 2 provenance | 3 synthetic calibration | 4 holdout | 5 empirical |
|---|---|---|---|---|---|
| D1.1 | ESTABLISHED_RUN_33 | ESTABLISHED_RUN_34 | ESTABLISHED_RUN_34_SYNTHETIC | ESTABLISHED_RUN_34_SYNTHETIC | **PENDING** |
| D1.2 | ESTABLISHED_RUN_33 | ESTABLISHED_RUN_34 | NOT_APPLICABLE_NO_PARAMETER | NOT_APPLICABLE_NO_PARAMETER | **PENDING** |
| D1.3 | ESTABLISHED_RUN_33 | ESTABLISHED_RUN_34 | NOT_APPLICABLE_NO_PARAMETER | NOT_APPLICABLE_NO_PARAMETER | **PENDING** |
| D1.4 | ESTABLISHED_RUN_33 | ESTABLISHED_RUN_34 | NOT_APPLICABLE_NO_PARAMETER | NOT_APPLICABLE_NO_PARAMETER | **PENDING** |
| D1.5 | ESTABLISHED_RUN_33 | ESTABLISHED_RUN_34 | NOT_ATTEMPTED_COMPOSITE_BLOCKED | NOT_ATTEMPTED_COMPOSITE_BLOCKED | **PENDING** |

Layers 3 and 4 read `NOT_APPLICABLE_NO_PARAMETER` for three modules because **no parameter reaches
production for them** — there is nothing to calibrate, because the reading is withheld rather than
fitted. That is a different statement from "calibrated and passed", and it is kept different.
