# Run 32 - Category 10, Decision Optimization: canonical remediation and closure

**Date:** 2026-08-17
**Branch:** `run32-wip`, from `origin/main` at **`73297a63949004472889f0dac5510292d219ce29`**
**Simulation version:** **`sim-2026.08-v20`**, superseding `sim-2026.08-v19`, which is preserved
**Participant package:** **`og-participant-2026.08-v7`** (successor; v6 pinned, not regenerated)
**Synthetic package:** **unchanged**, therefore no successor minted

---

## 1. What this run was, in one paragraph

Category 10 is seven measures that were each named for a decision method none of them was
carrying out. Six of the seven read the same three numbers - the cost index, the schedule index
and a document risk score - and reported a blend of them under an optimization name. This run
implements each method as the method, routes production onto it, and holds the boundary that
stops a decision result from becoming an observation about the project or an approval of
anything. **The Category-10 readings that used to be produced become abstentions on the real
corpus, and that is the correct outcome rather than a regression.** The controlled corpus holds no
decision problem, and assembling one would invent the alternatives.

### Headline results

| | |
|---|---|
| Category-10 targets | **7 / 7** |
| Canonical production routes | **7 / 7** |
| Suite reconciliation | **53 rows, 53 PASS**, 0 blank, 0 duplicate, 0 ambiguous |
| Fault campaign | **32 attempted, 32 applied, 32 RED for the intended reason, 32 restored GREEN** |
| Full suite | **152 suites, 12427 / 12427** |
| Legacy Category-10 proxy reachable | **0** |
| Human approval authority exercised | **0** |
| Decision output re-entering as project evidence | **0** |
| Voting | **exactly 2** - A1.7 TCPI and A1.8 Variance at Completion |

---

## 2. Scope: the exact seven

Read from the live registry, not transcribed. All seven resolve through
`models_cat10.CAT10_CANONICAL` into `canonical_v7`.

| ID | Authoritative name | Registry state | Governed structure |
|---|---|---|---|
| B4.1 | Multi-Objective Optimization | DISABLED_CONCEPT_ONLY | `decisionAlternatives` |
| B4.2 | Linear Programming | DISABLED_CONCEPT_ONLY | `linearProgramModel` |
| B4.3 | Constraint Satisfaction Analysis | ENABLED | `constraintSatisfactionProblem` |
| B4.4 | What-If Scenario Matrix | ENABLED | `actionScenarioMatrix` |
| B4.5 | Decision Sensitivity Matrix | DISABLED_CONCEPT_ONLY | `decisionSensitivityModel` |
| B4.6 | Pareto Frontier Analysis | DISABLED_CONCEPT_ONLY | `decisionAlternatives` |
| B4.7 | Minimax Regret Decision Rule | ENABLED | `actionScenarioMatrix` |

**Four of the seven are disabled concept-only modules and remain disabled.** A laboratory pass is
not activation, and activation was not this run's to grant. They stop at their governed disabled
gate while retaining their canonical research engines.

---

## 3. The authoritative sensitivity fixture, and an agent error recorded as an agent error

The supplied contract's Decision Sensitivity case is:

```
A = (0.9, 0.4)     B = (0.6, 0.8)     crossover at exactly w = 4/7
at w = 0.5, B ranks above A          at w = 0.7, A ranks above B
```

**This is correct, and it is what the implementation and the oracle assert.** Solving in exact
rational arithmetic: score_A(w) = 0.9w + 0.4(1-w) = 0.5w + 0.4 and score_B(w) = 0.6w + 0.8(1-w) =
-0.2w + 0.8. Setting them equal gives 0.7w = 0.4, so w = 4/7. The crossover is solved as a linear
equation rather than detected by sampling, so `4/7` is returned as `4/7` and not as the nearest
grid point.

**An earlier claim in this run that the crossover was 4/9 was an agent calculation error. It was
not a defect in the supplied contract.** The contract was briefly and wrongly judged defective on
the strength of that arithmetic. It has been re-verified in exact rational arithmetic and 4/7
stands. This is recorded here because the programme's standing rule is that a supplied contract
believed defective must first be checked against one's own arithmetic in exact terms, and this is
a worked example of why.

---

## 4. Module by module

Every entry below: what the contract supplies, what production used to do, the canonical
structure, the production supply path, the implementation, the oracle, qualification, authority,
the real-corpus result, and what remains.

### B4.1 Multi-Objective Optimization (10.1)

* **Supplied contract.** A = (10,5), B = (8,8), C = (12,4), D = (13,9). Nondominated set is
  A, B, C; D is dominated.
* **Old production behaviour.** Normalised the cost index, the schedule index and one minus the
  document risk score onto nought-to-one and reported their arithmetic mean, calling it
  `pareto_score`, then labelled the lowest-scoring of three descriptive scores the "binding
  constraint". There was no decision variable, no candidate intervention, no constraint, no
  feasible region and no decision horizon. Averaging is exactly the operation that destroys the
  trade-off information multi-objective optimization exists to expose.
* **Canonical structure.** `decisionAlternatives` - the alternatives being chosen between, the
  objectives they are measured on, and which way each objective is better.
* **Production supply path.** `project_data.governed_structure_keys()` admits the key; the owner
  supplies it through the project-data revision and `apply_to_signal_inputs`.
* **Implementation.** Dominance over an explicit alternative set, with orientation applied per
  objective rather than assumed. Infeasible alternatives are excluded before dominance, because
  an infeasible point cannot be on the frontier of a feasible region.
* **Oracle.** Nondominated set is A, B, C; D is dominated; a declared-infeasible alternative is
  excluded; abstains with no structure.
* **Qualification.** Category-9 boundary in front of the route.
* **Authority.** `selected_alternative` is **always None**. Choosing one point from a nondominated
  set requires supplied preference information, and none is governed. That is a refusal, not an
  omission, and the row records `preference_information_supplied: False`.
* **Real corpus.** Abstains, `canonical_decision_structure_absent`.
* **Remaining.** Disabled. No band, no calibration.

### B4.2 Linear Programming (10.2)

* **Supplied contract.** The Wyndor problem: optimum x1 = 2, x2 = 6, objective 36, with plant2
  and plant3 binding.
* **Old production behaviour.** Divided remaining work by remaining budget to get a required cost
  index, called it "feasible" at or below 1.20 and "optimal" at or below 1.00, and banded the
  result. There was no decision variable, no objective function, no constraint set and no
  feasible region: the words feasible and optimal were attached to a single ratio.
* **Canonical structure.** `linearProgramModel`.
* **Implementation.** **Exact vertex enumeration over rationals.** The fundamental theorem of
  linear programming puts an optimum of a bounded feasible region at a vertex, and a vertex is
  the solution of a square subsystem of the binding constraints. `Fraction` arithmetic gives an
  exact optimum with no tolerance to choose and no floating-point tie to resolve. Feasibility is
  tested at every candidate and the declared bounds, including non-negativity, are part of that
  test rather than an afterthought.
* **Oracle.** x1 = 2, x2 = 6, objective 36, disposition OPTIMAL, plant2 and plant3 binding, and
  **an independent exhaustive lattice search agrees on 36 at (2,6)**. Removing a binding
  constraint changes the optimum; minimising the same model gives 0 at the origin; an infeasible
  model reports INFEASIBLE rather than a number.
* **Authority.** No action is recommended; the optimum is reported, not approved.
* **Real corpus.** Abstains. **Remaining.** Disabled.

### B4.3 Constraint Satisfaction Analysis (10.3)

* **Supplied contract.** Feasible: (A,2), (B,1), (B,2). Infeasible: (A,1).
* **Old production behaviour.** Four rules hard-coded as comparisons against fixed thresholds on
  the two indices and the document risk score, reporting how many of four held. No variable, no
  domain, no assignment, no search. It also carried a provable arithmetic defect: of its four
  rules, `CPI >= 0.90` logically implies `CPI > 0.80`, so two of the four were one cost test and
  the satisfaction rate gave cost half the weight as a consequence of the redundancy rather than
  as a decision.
* **Canonical structure.** `constraintSatisfactionProblem` - variables, their domains, and
  constraints over them.
* **Implementation.** Every complete assignment is classified feasible or infeasible against
  every declared constraint. **No rule may be skipped**, and an unrecognised rule form is refused
  rather than treated as satisfied.
* **Oracle.** The four assignments, the single infeasible one, satisfiability, and abstention when
  a variable has no domain or when no constraints are declared.
* **Real corpus.** Abstains. **Remaining.** Enabled but abstaining; no calibration.
* **Lineage.** Its stale lineage record was **removed** - see section 6.

### B4.4 What-If Scenario Matrix (10.4)

* **Supplied contract.** The full 3x2 matrix A = (10,2), B = (6,6), C = (2,10). **No action
  recommended.**
* **Old production behaviour.** Several completion-estimate formulas over the cost index reported
  as named scenarios, carrying **no action identity at all**, so nothing was being compared under
  anything.
* **Canonical structure.** `actionScenarioMatrix` - rows are candidate actions, columns are
  scenarios, cells are outcomes.
* **Implementation.** The matrix is compared cell by cell. **An action without an identity is
  refused**, and **a matrix with a hole is refused**, because a decision rule over an incomplete
  matrix would silently treat an unknown outcome as known. Scenario probabilities are carried
  only where supplied; none is invented, so no expected value is computed unless the structure
  states the probabilities.
* **Authority.** `recommended_action` is **always None**. This measure applies no decision rule
  and names no action.
* **Real corpus.** Abstains. **Remaining.** Enabled but abstaining.

### B4.5 Decision Sensitivity Matrix (10.5)

* **Supplied contract.** A = (0.9, 0.4), B = (0.6, 0.8), crossover exactly 4/7. See section 3.
* **Old production behaviour.** Took the absolute deviation of the cost index from one, the same
  for the schedule index, and the document risk score times fifty, and ranked those three numbers
  by size. Nothing was perturbed, nothing was recomputed, and no decision existed to be sensitive.
  The reported sentence told the reader that a small change in the top driver "most changes the
  governance recommendation", which is a causal claim about a recommendation the module never
  evaluated. The 50 multiplier set the relative weight of the three drivers and had no source.
* **Canonical structure.** `decisionSensitivityModel`.
* **Implementation.** A weighted-additive model perturbed over a declared range, with rankings
  recomputed and crossovers solved exactly. **No default weight and no default range is
  invented**: both arrive in the structure or the method abstains.
* **Oracle.** One crossover, exactly `4/7`, not a sampled grid point; at w = 0.5 B ranks above A;
  at w = 0.7 A ranks above B; abstains with no range, nothing swept, or no model.
* **Real corpus.** Abstains. **Remaining.** Disabled.

### B4.6 Pareto Frontier Analysis (10.6)

* **Supplied contract.** Same alternatives as 10.1. Frontier is A, B, C; D is dominated.
* **Old production behaviour.** Threshold booleans over a single project. **One point is not a
  trade space.**
* **Canonical structure.** `decisionAlternatives`, the same object B4.1 reads.
* **Implementation.** The same dominance relation asked of the trade space.
  **Permutation invariance is structural, not asserted**: an alternative is nondominated exactly
  when no other alternative dominates it, which cannot depend on offer order. Duplicate points
  both survive, because dominance requires a strict improvement somewhere.
* **Oracle.** Frontier is A, B, C; **identical under all 24 orderings**; duplicates both remain;
  reading the same numbers as benefits changes the frontier to D, which proves orientation is
  read and not assumed; abstains on a single alternative.
* **Real corpus.** Abstains. **Remaining.** Disabled.

### B4.7 Minimax Regret Decision Rule (10.7)

* **Supplied contract.** Regrets A = (0,8), B = (4,4), C = (8,0); maxima 8, 4, 8; **selects B,
  value 4**.
* **Old production behaviour.** An index with no payoff matrix, so no regret was defined. Regret
  is the gap between an outcome and the best outcome available in the same future state, and with
  no matrix of futures there is no best to measure against.
* **Canonical structure.** `actionScenarioMatrix`, the same object B4.4 reads.
* **Implementation.** For payoff maximisation, `R(a,s) = max_a P(a,s) - P(a,s)`, then
  `argmin_a max_s R(a,s)`. For a cost matrix the best in a scenario is the minimum. **Orientation
  is declared and never assumed.**
* **Oracle.** The three regret rows, the maxima, alternative B, value 4, no tie for this matrix,
  a tie returns every tied alternative and chooses none, and the same numbers read as costs give
  different regrets.
* **Authority.** **The tie policy is an explicit refusal**: when several alternatives share the
  minimum maximum regret, all are returned and none is chosen, because breaking the tie needs a
  preference that may not be invented. Final selection remains human-authorised.
* **Real corpus.** Abstains. **Remaining.** Enabled but abstaining.
* **Renamed** by section 3 of the contract - see section 8.

---

## 5. The authority boundary, which is the point of the row shape

Every Category-10 row, computed **or abstaining**, carries:

```
result_class                 = ANALYTICAL_RESULT        (never HUMAN_DECISION)
human_authorization_required = True
creates_project_evidence     = False
status_color                 = None
band_asserted                = False
calibration_pending          = True
```

An abstention carries it too, because a reader who sees only "no result" still needs the row to
say that this measure could not have approved anything even if it had produced a number. The
ledger separates an ANALYTICAL_RESULT from a HUMAN_DECISION by a named field rather than by
reading a sentence.

**A decision recommendation is not an observation about the project.** It must not enter fusion,
it must not become new project-condition evidence, and it must not read as an approval. Because no
row carries a `status_color`, none can reach status fusion, which in any case reads only the two
voting modules.

These two properties - **faults 18 and 24**, the scientifically load-bearing pair - were asserted
as a single conjunction and are now four separate checks. A conjunction that catches two different
defects cannot say which one it caught, so neither could be proved non-vacuous. Each now turns its
own check red.

---

## 6. Suite reconciliation: 53 rows, and why not 23

`code_audit/run32_suite_reconciliation.csv`, one row per distinct failing test, **derived from
execution** at commit `6f7cd7e` - the point where the production repoint and the v20 stamp had
landed and no reconciliation had been done.

Sixteen suites were red there. **Three of them crashed before printing a `RESULT` line**
(`test_run14_disabled_method_functional` on `KeyError: 'pareto_score'`, `test_run19_category_10`
on `KeyError: 'scenarios'`, `test_run20_cycle10_truthful_labels` on `StopIteration`), so their
failing assertions were hidden, not absent.

**The owner's prompt says 23 rows, and that figure was measured through exactly that
partly-obscured window.** The thirteen suites that did print a RESULT line sum to 21 visible
failures, and the three crashed suites contributed only the handful they managed to print before
dying. The crashes were cleared in a throwaway worktree, never committed, and those three suites
then reported 95/113, 71/82 and 49/51 - **31 failing assertions between them, not 3.** Adding the
21 visible, plus one further failure that appears only once the production pin advances
(`test_run25_rail_removal`, a fourth red suite the handoff did not name), the true number of
distinct failing tests is **53**. No row was padded, merged or suppressed.

| Classification | Rows |
|---|---|
| HISTORICAL_ONLY | 30 |
| TEST_INFRASTRUCTURE_DEFECT | 18 |
| GENUINE_REGRESSION | 5 |
| **Total** | **53** - all PASS |

No fourth classification value exists in the file.

**The one production regression this run introduced, and one it inherited:**

1. `models_cat10` emitted the generic `canonical_structure_absent` where the Category-10 contract
   requires `canonical_decision_structure_absent` - the established code for a method whose
   defining structure is a decision structure, and the one B2.18 and B2.19 already emit for the
   same object. Three suites asserted it and were right to. **Production fixed; no test
   weakened**, and the invariant is now fault-injected.
2. **B4.3's lineage record still declared the two performance indices** into the earned-value body
   as CORRELATED. That was true of the v19 checklist and is precisely why the v19 implementation
   was a proxy. B4.3 now reads a governed constraint network and no index at all. Leaving the
   declaration would assert a dependence that has stopped existing, and that is the dangerous
   direction: a false CORRELATED edge lets a consumer **suppress corroboration that is really
   there**. **Removed**, not rewritten onto its governed structure, on the identical precedent Run
   30 set for eleven Category-7 records and Run 31 for B3.2, B3.4 and B3.5. `lineage_status` now
   derives LINEAGE_UNRESOLVED, which is the truthful state: not independent, not dependent, not
   established. `ACTUAL_INDEX_READS` is now **empty** - no production lineage record declares any
   derived-index read.

**Two fixtures were examined for purpose and left sparse.** `test_run20_voting_lineage` and
`test_run4_validate_seven` both encode "the vote is a restriction of a larger computed
population" as a numeric floor. Both fixtures supply only earned-value primitives and were never
intended to exercise a Category-10 decision method; the large populations of earlier runs were an
artefact of proxies computing off six scalars. **Canonical abstention was retained and neither
fixture was enriched.** In `test_run4_validate_seven` the floor is restated 10 to 8 with the
reason recorded, exactly as at Runs 10B, 28, 30 and 31; the ratio is the finding and six of eight
computed modules still do not vote. In `test_run20_voting_lineage` the **multiple is retired
rather than lowered again**: at three computed against two voters "materially larger" is not
supportable by any multiple, and picking one that three happens to satisfy would be fitting the
check to the answer. The terminal computed set is asserted by name instead, which is strictly
stronger - it still forbids the degenerate "only two modules existed", and it goes red if any
further module computes or if A1.1 stops computing.

---

## 7. MARCOS and CRITIC-TOPSIS placement

`code_audit/run32_marcos_critic_placement.csv`, 2 rows, every field read from the live registry.

**B2.18 and B2.19 keep their historical Category-7 identities and registry names.** No new module
ID is minted. They are exposed operationally as decision methods over the **same
`decisionAlternatives` structure** B4.1 and B4.6 read, validated by the one
`canonical_v5.decision_problem`, so a Category-10 decision result cannot drift from the
alternatives it came from. **`canonical_v7` defines no MARCOS and no CRITIC-TOPSIS engine of its
own** and imports `decision_problem` instead: one engine each, no duplication. Explicit
alternatives and explicit criteria are required or the method abstains. Both remain wrapped by the
Category-9 boundary, both are non-voting, and neither creates project evidence. **A ranking is
never project-condition evidence.**

| Counter | Value |
|---|---|
| Duplicate engines | 0 |
| Unauthorized new module IDs | 0 |
| Voting | false, both |
| Creates project evidence | false, both |

---

## 8. The section-3 rename

**Regret Minimization Index becomes Minimax Regret Decision Rule.** This is the only Category-10
rename authorised and the only one made.

Propagated to the registry map, the server-side parity table, and the eight participant-visible
surfaces carrying the display name. The owner-approved-rename allowances in `run17/population.py`
and `test_run27_remediation_matrix.py` are extended exactly as Runs 28 and 31 extended them, and
the supervisory specification's own wording is preserved beside them rather than edited.

**Historical wording is preserved** in `canonical_v7.py`'s table of what each module was under
v19, in `models_cat10.py`'s note that "B4.7 was Regret Minimization Index", in the p0-baseline API
contract captures, and in every past run's audit CSV and report.

### Participant package v7, and v6 pinned rather than regenerated

Eight of v6's seventy files moved. **v6 is pinned to commit `93942ca`, whose blobs it describes,
and its bytes are untouched.** Regenerating a predecessor to match the present is the defect the
Run-28 closure had to correct in the v2 record, and it is not repeated.

**The delta is proved, not asserted, by inverse mapping:** applying the single reverse
substitution to those eight files reproduces the v6 bytes exactly. The package suite asserts it.

**The participant experimental sequence is unchanged.** Evidence review, preliminary judgment,
preliminary lock, AI reveal, final judgment, rationale and evidence capture, final lock and period
advancement are all untouched. No threshold, no step, no lock and no advancement moved. The whole
delta on the participant surface is three lines, each a module display name.

**The synthetic package did not move, so no synthetic successor is minted.** Minting one to match
a run rather than a byte change would be the same defect in the other direction.

---

## 9. The 32-fault campaign

`code_audit/run32_fault_injection_results.csv`, driven by `server/tools/run32_fault_campaign.py`.

| | |
|---|---|
| Attempted | **32** |
| Applied, verified by re-reading bytes from disk | **32** |
| RED for the intended reason | **32** |
| Restored byte for byte, baseline GREEN again | **32** |
| NOT_APPLIED | **0** |
| Crashes accepted as RED | **0** |
| Unrelated failures accepted as RED | **0** |

**This 32/32 was not manufactured, and the route to it is the evidence.** The first run scored
**1/32**: eight guards did not fire, three crashed, and twenty went red somewhere unrelated. Every
one was resolved by repointing the fault or the guard onto the property actually at stake, never
by loosening the acceptance rule. The harness requires the intended property to appear among the
guard's **own failing check sentences**, so a passing line carrying the same words cannot be read
as evidence and an unrelated failure cannot be credited. `__pycache__` is cleared on both sides of
every injection, because a restore inside the same clock second changes neither mtime nor size and
a cached mutant would otherwise survive.

### The campaign found three real defects in the instrument

1. **The Category-10 oracles were not in the acceptance gate.** `run_all_suites.sh` globs
   `tools/test_*.py`, and the 68 oracle checks live under `server/tests/`, so they were never
   executed by the gate: a regression in `canonical_v7` would not have turned the run red. They
   are now wired in - executed in-process, not copied, so there is one set of oracle values.
2. **The v7 supply path had no guard** (fault 32). Runs 29 and 31 both carry the equivalent check
   for their canonical layers; v7 had none. Removing the v7 keys from
   `governed_structure_keys()` turned nothing red anywhere in the tree, meaning a Category-10
   structure could have been readable by the method and unwritable through the real intake with
   every oracle green. The check is added.
3. **B2.19's minimum-three rule was untested** (fault 20). The only existing check feeds
   `critic_topsis` a single row, and a single row is already refused upstream by the shared
   `decision_problem`. The check passed whether or not the minimum-three rule existed: lowering
   the threshold from three to two broke nothing. Two rows is the case that distinguishes the two
   layers, and that check is added.

---

## 10. Version decision (section 6 of the contract)

**`sim-2026.08-v20` remains current. No new stamp is minted.** The decision rests on executed
behaviour, not on the fact that files changed.

* **What is published.** `main` and `origin/main` are at `73297a6`, whose `models.py`, executed
  from the git object, stamps **`sim-2026.08-v19`**. **`v20` has never been published.**
* **Did executable behaviour change after v20 was stamped?** Yes, once: the removal of B4.3's
  lineage record, which changes `lineage_status(B4.3)` from a declared CORRELATED edge to
  LINEAGE_UNRESOLVED. Everything else in this run is tests, tools, artifacts, display names and
  the parity table.
* **New boundary, or continuation of the unpublished v20?** **Continuation.** The lineage removal
  is the lineage consequence of the very repointing that v20 stamps - an incomplete part of the
  v20 change, not a new behaviour point after v20 was published. Because v20 was never public, no
  results were ever collected under a v20 that declared B4.3's lineage, so there is no ambiguity
  to resolve and nothing frozen is being silently changed under an unchanged version.
* **The history remains append-only and a strict prefix extension** of main's, proved by
  executing both: main's history ends at v19 and the current history is that tuple plus v20.

Bumping here would have been a bump because files moved, which is exactly what the contract
forbids.

---

## 11. Acceptance counters

| Counter | Required | Actual |
|---|---|---|
| Category-10 targets | 7/7 | **7/7** |
| Canonical routes | 7/7 | **7/7** |
| Corpus-present-but-unwired | 0 | **0** |
| Reasonably supplyable structures with no production path | 0 | **0** |
| Raw evidence bypassing Category 9 into Cat 10 | 0 | **0** |
| Missing-assessment bypass into Cat 10 | 0 | **0** |
| Legacy Category-10 proxy route | 0 | **0** |
| Decision-output feedback into evidence | 0 | **0** |
| Human-authority bypass | 0 | **0** |
| MARCOS/CRITIC duplicate engines | 0 | **0** |
| Unauthorized new module IDs | 0 | **0** |
| Voting | exactly 2 | **2** - A1.7 TCPI, A1.8 Variance at Completion |
| A3.4 Material Cost Variance | disabled | **disabled** (evidence under review) |
| B2.7 Plithogenic Sets | disabled | **disabled** |
| B2.9 Quantum Probability | archived | **disabled and `DISPOSITION_ARCHIVED`** |
| B2.20 Hypersoft Sets | disabled | **disabled** |
| Participant protocol changes | 0 | **0** |

Production Postgres was never accessed. Every suite ran against its own freshly migrated SQLite
database; `DATABASE_URL=:memory:` was never used for acceptance.

---

## 12. What remains, stated plainly

**No Category-10 module computes on the real corpus, and none should yet.** What is missing is the
decision problem itself, and it can only come from the owner.

* **Supply.** The controlled corpus carries no candidate action set, no linear program, no
  constraint network, no action-by-scenario matrix and no sensitivity model. There is deliberately
  **no corpus-assembly fallback**: the corpus holds no candidate action set, so assembling one
  would invent the alternatives, which is worse than inventing a parameter. The production intake
  admits all five structure keys, so an owner-supplied decision problem will compute the moment it
  arrives.
* **Calibration.** No band is asserted and none is calibrated. No labelled corpus of project
  outcomes and no expert reference standard exists in this repository, so no boundary can be
  fitted or tested. Every row carries `calibration_pending: True`.
* **Empirical validation.** **The oracles are synthetic known-answer tests against the supplied
  contract. That is not empirical validation.** How often a Category-10 reading would be right on
  real projects is unknown, because no comparison against real project outcomes exists.
* **Rule checks are not legal compliance.** Nothing in this layer makes a regulatory or legal
  determination.
* **Portfolio Health** is untouched by this run and remains outstanding.
* **Activation.** Four modules stay disabled. A canonical engine passing its oracle is not grounds
  for activation.

### Carried finding: defensibility-claim drift, platform-wide

The served defensibility evidence object still says of B4.7 "implemented and computed by the
server" and "canonicalStructure: not required by this module". Both stopped being true when the
module was repointed onto `canonical_v7` and began requiring a governed `actionScenarioMatrix`.
**The same drift exists for the modules Runs 28 to 31 remediated** - B3.2 carries its Run-31 name
beside the identical stale claims - so this is a platform-wide defensibility-claim reconciliation,
not a Category-10 remainder. Rewriting a defensibility claim is not a rename and was not this
run's to grant. It is recorded for the owner.

### Carried finding: `method_class` divergence on the client surface

`assets/js/categories.js` and `assets/js/taxonomy.js` still carry `method_class:
'Regret_Minimization'` for B4.7 while the server now emits `Minimax_Regret_Decision_Rule`. No
guard compares them and no suite is red, but the two identifiers no longer agree. Changing a
`method_class` is a code identifier change rather than a display rename and could affect ledger
joins, so it is reported rather than made.
