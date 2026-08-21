# Run 43D — Retirement From Service

**Date:** 2026-08-21
**Repository used:** the Linux clone at `/home/user/LinPRojectRadar`. The Windows path at
`C:\Users\NTUN\OneDrive - Arora Engineers, LLC\DEng\LinPRojectRadar` was not used and is not
reachable from this session (section 4 asks which; this is the answer).
**Interpreter:** no `.venv` exists in this clone. `server/run_all_suites.sh` falls back to the
`python3` on `PATH` (3.11.15) by its own documented fallback. Every figure below came from that.
**Branch:** `claude/run43B-retirement-completion`, built on `83c832d`.
**Merged:** NO. **Successor stamp minted:** NO. The live stamp remains `sim-2026.08-v27` at
`server/app/simulation/models.py:475`.
**No browser session was opened.** Nothing in Phase D required one, so the section 4.3 `cwd`
question does not arise.

---

## 0. The outcome, stated first

**STOP CONDITION 7.1 FIRED: a third case appeared where a check body must change, and it is not a
third case but a third *class*, running to 181 measured checks across 26 suites.**

**STOP CONDITION 7.4 FIRED WITH IT: none of the four suites the Portfolio Health offload turned
red returns green under 5.1.** Section 5.4 says to stop if any does not. All four do not.

Phase D is left unmerged. **Phase E was not begun**, because the section 2 gate fails on all four
conditions. See section 9.

**Section 5.1's mechanism is nevertheless correct, and it is built, committed and measured.** It
does what the ruling says it does, and it dissolves four of Run 43B's five findings outright.
Four commits stand on the branch and every one of them is self-contained:

| commit | what |
|---|---|
| `7dc6053` | 5.1 and 5.2. Removal from service; the 38 identifiers restored; the `RETIRED` leak fixed |
| `0b2de50` | 5.3. The sanctioned change to `assert_retained_adaptation_not_reachable`, proved failable both ways |
| `776f130` | 5.4. The sanctioned change to `test_map_and_module_count.py`, proved failable |
| (this file) | the report, the decision record, the handoff |

The measured effect of the mechanism alone, before either sanctioned change:

| tree | suites | checks | red |
|---|---|---|---|
| pre-retirement baseline `f461630` (Run 43's figure) | 188 | 14,176 / 14,176 | 0 |
| `b37f133`, Run 43's removal-from-existence | 188 | 9,671 / 9,817 | 72 |
| `83c832d`, Run 43B's branch, reproduced by this run | 188 | 9,434 / 9,615 | 76 |
| `7dc6053`, removal from service | 188 | 12,194 / 12,536 | 64 |
| `776f130`, this run's head | 188 | **12,203 / 12,539** | **62** |

**2,924 checks that could not run under Run 43's mechanism now run.** That is the ruling working.
What it does not do — and this is the finding — is make those checks pass.

---

## 1. Section 3.2 — the sentence fixing group naming, quoted

From `NAMING_AUTHORITY.md` section 4:

> **Never use a module id or number in user-facing text.** No "Cat 4", no "1.7", no "PH.2", no
> "A4.2". Groups and purposes only. The old "Cat N" scheme is retired along with the names.

And, governing the same surface one line earlier:

> **Group C does not contribute to project status.** Evidence quality describes what is known
> about a project, not the project's condition.

Neither sentence was strained by this run: Phase D introduced no user-facing text. The one
user-facing sentence in scope is Run 43B's Portfolio Health message, verified unchanged at
section 5.2 below.

---

## 2. Section 5.1 and 5.2 — the mechanism, and what it fixed

### 2.1 What was built

`p0-baseline/module_renumbering_map.csv`: every one of the 38 rows gets its `new_id` back.
**Verified column-for-column against `f461630` rather than asserted**: outside the `notes` column
the file is identical to the pre-retirement registry, row order included.

```
103 rows both sides; non-notes differences: []; id order identical: True
```

The RETIRED marking and each module's assigned reason stay exactly where Run 43 wrote them, in
the notes column, which is now the only place the retirement is recorded and therefore the only
place anything can read it from. Section 5.2's "preserving the reason each carries" is satisfied
by not moving it.

`server/app/simulation/registry.py`:

- `load_registry()` returns all 101 again. The two rows it still filters are **not**
  retirements — they are pre-existing alias rows with no identifier of their own (Document Risk
  Extraction into `A4.1`, the Cat 3 DSM entry into `A5.1`) and they were filtered here before
  Run 43 existed.
- `retired_modules()` derives `{id: reason}` from the notes. `modules_in_service()` and
  `service_index()` derive the 63. There is no list of retired identifiers anywhere in the file.
- `available_modules()` and `unported_modules()` intersect with the 63.
- `run_module()` resolves a retired id and **refuses** it with its stated reason, ahead of the
  Group D routing error and ahead of all three DISABLED short-circuits, returning
  `activation_state` and `abstention_reason_code` `RETIRED_FROM_SERVICE`, `retired: True` and
  `retired_reason`. It no longer raises `MissingModuleError` on a retired id.

`portfolio_health.live_portfolio_modules()` and `training.py`'s abstention population moved from
`registry_index()` to `service_index()`. Both build a population rather than resolve a reference,
and `registry_index()` now resolves retired ids; leaving them would have put Portfolio Health
straight back into service and listed retired modules as abstaining on a participant surface.

### 2.2 The `RETIRED` literal leak — verified, not trusted, and fixed

Run 43B found the literal leaking into every population built by a consumer that reads the CSV
without going through `load_registry()`. Verified independently here, and the fix is the
restoration itself: with the identifiers back, there is no `RETIRED` for such a consumer to pick
up.

```
qualification_contract population has RETIRED: False   (size 101)
export module-name table has RETIRED:          False
retired ids anywhere in compute_project output: []
RETIRED literal anywhere in compute_project output: False
```

`test_run31_pass2_acceptance`'s `missing=['RETIRED']` and `test_run34_parameter_count_closure`'s
`['RETIRED','RETIRED','RETIRED','RETIRED','RETIRED'] vs ['D1.1'..'D1.5']` are both gone from the
current run's output.

### 2.3 `A1.1` in `assets/js/taxonomy.js` — Run 43B's finding does not reproduce

Section 5.2 asks for taxonomy to be reconciled to the registry, on Run 43B's measurement of 64
against 63 with `A1.1` extra. **Measured on this tree, it is 63 against 63 with no difference in
either direction**, and no edit to `taxonomy.js` was needed or made.

```
taxonomy.js distinct module ids : 63
in service                      : 63
taxonomy not in service : []
in service not taxonomy : []
```

The three literal `A1.1` occurrences on browser surfaces are `taxonomy.js:368` (a comment naming
the format of a method_class map), `workspace.js:59` and `decision-ui.js:71` (id-to-display-name
lookup tables). None is a population. A retired module produces no stored row, so no lookup table
entry for one is ever reached. Run 43B's 64 is reported as not reproduced rather than as wrong:
its extraction is not recorded, so the two figures may be counting different things.

---

## 3. Section 5.3 — the sanctioned guard change, with its text before and after

One line of `assert_retained_adaptation_not_reachable` moved, and it is the only one.

**BEFORE** (`server/app/simulation/models_sim.py`):

```python
    check(row.get("abstention_reason_code")
          == "CANONICAL_DRIVER_DISTRIBUTION_MAPPING_NOT_GOVERNED",
          "with the reason code that distinguishes an ungoverned method definition from an "
          "ordinary missing value", str(row.get("abstention_reason_code")))
```

**AFTER**:

```python
    check(row.get("abstention_reason_code") == _reg.RETIRED_FROM_SERVICE_CODE
          and row.get("retired") is True
          and str(row.get("retired_reason", "")).startswith(_reg.RETIRED_NOTE_PREFIX),
          "refusing with its stated retirement reason rather than computing, and saying which "
          "reason", str(row.get("abstention_reason_code")))
```

### 3.1 Constraint 1 — the guard still proves its own subject

Its subject is the retained scalar Monte Carlo adaptation's **unreachability**, not the identity
of whichever gate refuses. The check immediately above the changed one carries that, and it was
not touched: it EXECUTES `A1.1` on inputs the adaptation would happily have computed from, and
fails the moment a figure comes back, by any route and through any gate. Retirement sits in
**front of** the canonical-input gate rather than replacing it, and the two structural checks
asserting that gate is present and still precedes the dispatch table are also untouched.

### 3.2 Constraint 2 — proved it can fail, both ways, measured not argued

**Injection A** — bypass the retirement short-circuit for `A1.1` only. It falls through to the
canonical-input gate and answers `CANONICAL_DRIVER_DISTRIBUTION_MAPPING_NOT_GOVERNED`:

```
FAIL refusing with its stated retirement reason rather than computing  | CANONICAL_DRIVER_DISTRIBUTION_MAPPING_NOT_GOVERNED
INJECTION A caught: True
```

**Injection B** — bypass the retirement short-circuit AND the canonical-input gate, which is what
genuinely makes the retained adaptation reachable. **Verified reachable rather than assumed:**

```
ADAPTATION REACHABLE? p50_eac= 1106667.4124324322 status= None method= Monte_Carlo
FAIL and EXECUTED on inputs the adaptation would happily have computed from, A1.1 ret...
FAIL refusing with its stated retirement reason rather than computing, and saying whi...
INJECTION B caught: True  2 checks failed
```

The untouched subject-level check is one of the two that caught it. Restored after each;
`test_run36_closure_guards` 15/15 on the restored tree. **Stop condition 7.5 does not fire.**

---

## 4. Section 5.4 — the sanctioned suite change, and the four suites

### 4.1 `test_map_and_module_count.py`, before and after

**BEFORE:**

```python
    check(tx["allCats"] > tx["projCats"] and tx["allMods"] > tx["projMods"],
          "the taxonomy genuinely has a portfolio-level category to exclude "
          "(so the checks below are not vacuous)", json.dumps(tx))
    check(tx["projMods"] == 96, "a project has 96 modules", str(tx["projMods"]))
    check(tx["projCats"] == 11, "across 11 categories", str(tx["projCats"]))
    check(tx["allMods"] == 101 and tx["allCats"] == 12,
          "and the whole taxonomy is still 101 across 12, unchanged",
          f"{tx['allMods']}/{tx['allCats']}")
    check(tx["d1Modules"] == 5, "Portfolio Health keeps its five modules", str(tx["d1Modules"]))
```

**AFTER:** the vacuity guard drops its module-count half, which retirement made false without
making the check vacuous (12 categories against 11 still carries it); `projMods == 63`;
`projCats == 11` unchanged; `allMods == 63 and allCats == 12`; `d1Modules == 0`, "Portfolio Health
computes nowhere: its category container is retained and empty". Then three checks were **added**,
because an empty `d1` list is also what a taxonomy that merely lost the rows would look like: the
five Group D identifiers still RESOLVE in the registry, every one is retired from service WITH A
STATED REASON, and `live_portfolio_modules()` is empty. The expected values stay hand-written
literals: this suite exists to catch the browser taxonomy drifting from the registry, and a check
deriving its expectation from the thing under test would catch nothing.

**Proved it can fail**, at the source rather than at the assertion — the RETIRED marking was
cleared from `D1.1`'s notes column, the single authority both populations derive from:

```
FAIL  and every one of them is retired from service, with a stated reason
      [{'D1.1': None, 'D1.2': 'RETIRED Run 43 as D1.2: ...', ...}]
FAIL  so no Portfolio Health module is live on the portfolio route  [('D1.1',)]
RESULT: 73/75   ->  restored  ->  RESULT: 75/75
```

That is also an independent confirmation of section 5.5.2: restoring one row's marking resumes the
portfolio route for exactly that identifier, with no edit to `portfolio_health.py`.
Before 68/72, after 75/75.

### 4.2 The four suites the offload turned red — STOP CONDITION 7.4

Section 5.4 asks whether all four return green under 5.1 without further change, and says to stop
if any does not. **None of the four does.** Measured on this run's head:

| suite | verdict | why |
|---|---|---|
| `tools/test_run33_portfolio_health.py` | **RED, crashes** | `KeyError: 'cat8_2_portfolio_outlier'` at line 743. The dispatcher no longer computes PH.2, so the results dict has no such key. Refusal does not create one. |
| `tools/test_run34_holdout_provenance.py` | **RED, crashes** | `KeyError: 'cat8_1_isolation_forest'`, reached at line 24 through `run34_ph1_tree_count_calibration.py:128`. Same cause. |
| `tools/test_run34_provenance_fault_campaign.py` | **RED, 7/26** | 19 failing checks, all portfolio parameter provenance. |
| `tools/test_period_series.py` | **RED, 42/46** | 4 failing checks, all Portfolio Health. |

The reason is structural and it is the same reason section 5 below gives. Section 5.1 makes a
retired **identifier** resolve; it does not make a retired **computation** produce the reading a
check indexes for by name. These four index a results dict by the key a Group D module used to
write. There is no refusal shape that puts that key back without computing the module.

---

## 5. STOP CONDITION 7.1 — the third case, enumerated

Section 5.1 states: *"No check body changes and no check is removed under this ruling. Checks
referencing a retired identifier continue to run and now assert the refusal rather than a
computation."*

**The first half of that sentence is true and was the point. The second half does not hold, and
the difference is the whole of this stop.** Those checks do now run. They do not assert *the*
refusal — they assert **a specific, different refusal or computation, named in the check body, and
belonging to the module's pre-retirement behaviour**. A refusal cannot satisfy an assertion
written about a different refusal.

Measured on this run's head: **62 red suites, 317 failing check lines detected in the two common
output formats, of which 181 name a retired module in the failure line itself.** Fourteen suites
still abort without a canonical RESULT line.

### 5.1 The classes, with quoted evidence

**Class 1 — a retired module's former abstention is asserted by name (largest class).** These
modules were disabled or abstaining before retirement, and the check asserts *which* refusal.

```
test_d1_module_inputs      ****  B2.7 carries activation_state DISABLED_UNSAFE  [RETIRED_FROM_SERVICE]
test_d1_module_inputs      ****  B2.1 records that the canonical route produced the silence, not a proxy  [None]
test_d1_module_inputs      ****  B2.1 names the structure it was waiting for
test_run13_module_evidence FAIL  A3.8: carries the disabled activation state
test_run13_module_evidence FAIL  B4.6: classified disabled
test_run31_pass2_acceptance ****  Evidence Combination B2.10: raw unassessed evidence was consumed
test_run6_known_answer     ****  dempster-shafer: ... the canonical route abstains and says which structure it awaited  [None]
test_run1_disable_and_relabel FAIL  every concept-only module reports DISABLED_UNSAFE  ['A3.8','B2.7','B2.9','B2.20','B4.1','B4.2','B4.5','B4.6']
```

Ten of the 38 were retired under reason 2, *"already disabled"*. Their check bodies assert
`DISABLED_UNSAFE` or `DISABLED_EVIDENCE_UNDER_REVIEW` by name. Section 5.1.1 requires the retired
reason instead. Both cannot hold. Sixteen more were retired under reason 3, and their bodies
assert `canonical_structure_absent` and the named structure awaited. Same collision.

**Class 2 — a retired module's computed value is asserted.** Seven modules retired under reason 4
were computing correctly and their checks hand-compute the expected figure.

```
test_run10b_canonical_integration FAIL  B2.19: with its defining structure present the method computes  {... 'retired': True ...}
test_run29_supply_path_guard      FAIL  A5.3 computes from the SAME governed key A5.2 does
```

**Class 3 — the retired module is absent from an enumerated results dict, and the suite aborts.**
All fourteen crashers. Requirement 5.1.3 mandates that absence. Every one is a body-level index
or attribute access, not a filter:

```
test_run19_category_2   line 407  tighter.get("schedule_compression_index") < 1.0   TypeError: NoneType < float
test_run19_category_5   line 262  {b["input_id"]: b for b in out["bars"]}           KeyError: 'bars'
test_run29_canonical_oracles line 319  _r["bars"]                                   KeyError: 'bars'
test_run29_fault_campaign    line 407  _t13["bars"]                                 KeyError: 'bars'
test_run30_cat7_operational_route line 209  _o["belief"]["G"]                       KeyError: 'belief'
test_run30_lineage_semantics line 136  _rows["B2.1"]                                KeyError: 'B2.1'
test_run3_adapter            line 265  abst4["B2.1"]                                KeyError: 'B2.1'
test_run8_retest_classify_27 line 1596 _abst["A2.5"]                                KeyError: 'A2.5'
test_run20_advisory_lineage_disclosure line 271  _a53["calibration_pending"]        KeyError: 'calibration_pending'
test_run20_cycle10_truthful_labels line 435  next(m for m in MISMATCH_23 ...)       StopIteration
test_run16_material_cost_variance_disabled line 209  entry[0]                       IndexError
test_run10b_canonical_integration line 516  _w["EXPECTED_COST_DELTA_USD"]           KeyError
test_run33_portfolio_health  line 743  _snap["results"]["cat8_2_portfolio_outlier"] KeyError
test_run34_holdout_provenance line 24 (via run34_ph1_tree_count_calibration.py:128) KeyError: 'cat8_1_isolation_forest'
```

**Class 4 — a hard-coded population count in an unsanctioned suite.**

```
test_simulation.py:49   FAIL  available == validated (95 modules)  [62 listed]
                              check(available_modules() == sorted(VALIDATED), ...)
test_run21_instrument_invariants  FAIL  NON-VACUITY: removing it from the disabled sets really
                              does change its activation state, so the check above is not true
                              by construction  disabled=RETIRED_FROM_SERVICE undisabled=RETIRED_FROM_SERVICE
```

The `test_simulation.py` check derives its expected value from `VALIDATED` rather than hard-coding
95, so it is not a stale literal: it asserts that the implemented set and the available set are the
same set, which retirement makes false by design. It cannot be repointed without changing what it
asserts. The `test_run21` non-vacuity check is the sharper instance: it proves the disabled check
above it is not true by construction, by removing a module from the disabled sets and asserting its
activation state moves. Under 5.1 retirement is tested first in `activation_state()`, so the state
does not move and the non-vacuity proof is lost. Section 5.4 sanctions `test_map_and_module_count.py`
and no other suite.

`test_run16_final_flow_and_rail.py`, which Run 43B reported red on `the registry declares 96
project-level modules`, is **green again at 73/73** on this tree: it derives the label from the
registry rather than from a literal, and the restoration made the derivation work.

**Class 5 — pinned byte-identity freeze manifests**, seven suites. Unchanged in kind from Run 43B
and correctly red: this run edited files inside the frozen surface. Section 5.7.1 orders them
reconciled, but re-pinning belongs to a freeze this run may not take.

### 5.2 Why no refusal shape resolves it

Three shapes were considered and each is refused by the ruling itself:

1. Return the module's **former** refusal and add the retirement to it — makes classes 1 and 3
   largely green. Refused: for the reason-3 modules the canonical route must run to produce
   `canonical_structure_absent`, and 5.1.1 says the module **does not compute**.
2. Keep retired modules in `run_all`'s output carrying the retirement refusal — resolves the
   `KeyError` half of class 3. Refused by 5.1.3: the ledger is a participant surface.
3. Give the refusal dict the module-specific keys the bodies index — refused: those keys hold
   figures, and supplying them is computing.

**There is no fourth.** The collision is between 5.1.1 and 5.1.3 on one side and several hundred
hand-written per-module check bodies on the other, and it is the collision Run 43B measured. The
ruling changed the mechanism, which was the right change and fixed the crashes for 2,924 checks.
It did not change what those bodies assert.

---

## 6. Section 5.5 — the two kept Run 43B items, re-verified

Section 5.5 says verify, not assume. Both proofs were re-executed on this tree.

**5.5.1, `_RUN1_PROXY_QUALIFIERS` reconciled 30 to 1. HOLDS.**

```
export mirror: {'A1.2': 'hard-coded transformations of two-sided CUSUM on real SPI history; ...'}
live registry: ['A1.2']
IDENTICAL, reconciled
```

The `registry.py` prose beside `PROXY_QUALIFIERS` still reads `len(PROXY_QUALIFIERS)` rather than a
restated count, so there is still no second place for it to drift.

**5.5.2, Portfolio Health offloaded. HOLDS, and `canonical_v8.py` is untouched.** Re-proved by
monkeypatching both `canonical_v8.compute_portfolio_health` and `assemble` to raise, then computing
a snapshot on a four-project cohort that *does* carry a `portfolioCohort`:

```
live: ()
route: 'retired'   retired: True   results: {}   insufficient_data: True   portfolio_size: 0
```

Neither was reached. **What the surface shows**, reported and not decided: `assets/js/workspace.js`
lines 1009-1021, the Portfolio Health list, unmodified. `snap.insufficient_data` is true, so the
card takes the branch it already had and prints `snap.message` once for the portfolio in a single
`<p class="ws-note">`, with no per-project Portfolio Health cards. The message, verified verbatim
from `portfolio_health.RETIRED_REASON`:

> Portfolio Health is no longer part of the analytical taxonomy, so no portfolio-level reading is
> produced. Project Status is unaffected: Portfolio Health never contributed to it.

**No control was added, moved or removed.** Stop condition 7.6 does not fire.

---

## 7. Section 6 — the tests, each with its verdict

Every verdict below is measured on this run's head. Where a test could not be established it says
so rather than being passed over.

| # | test | verdict |
|---|---|---|
| 1 | `run_module()` on each of the 38 refuses with its retired reason, not `MissingModuleError` | **PASSES.** All 38 probed; failures = `[]`. Each returns `retired: True`, `abstention_reason_code` `RETIRED_FROM_SERVICE`, a `retired_reason` beginning `RETIRED `, `status_color` None, `insufficient_data` True. |
| 2 | the registry resolves each of the 38 without `KeyError` | **PASSES.** All 38 present in `registry_index()`. |
| 3 | no retired module in the rollup, project status, category population, participant surfaces, brief, decision card, courses of action, research export, browser taxonomy | **PASSES for every server population measured, WITH ONE FINDING.** `compute_project` output contains no retired identifier and no `RETIRED` literal; `available_modules()` is 62, all in service; the export's module-name table and `qualification_contract()` carry no `RETIRED`. **Finding, not acted on:** `assets/js/knowledge.js` and `assets/js/deepdive.js` still enumerate retired modules on the methods-documentation surface. Acting would change a user-facing surface, which section 4.4 forbids deciding. |
| 4 | modules in service is 63, derived from the registry | **PASSES.** `len(modules_in_service()) == 63`. |
| 5 | registry total is 101, derived from the registry | **PASSES.** `len(registry_index()) == 101`. |
| 6 | `assets/js/taxonomy.js` and the live registry agree | **PASSES.** 63 against 63, no difference either way. See section 2.3. |
| 7 | the `RETIRED` literal appears in no derived population | **PASSES.** See section 2.2. |
| 8 | no module in service changed its computed result, byte-compared against Run 43's census | **PASSES.** Run 43 committed no census artifact, so an independent one was built rather than trusted: a `git worktree` at `f461630`, three fixed signal-input cases, every module in `available_modules()` run through `run_module` on both trees and the results JSON-serialised with sorted keys. **186 common results, 0 differences.** The 99 keys present only at `f461630` are 33 retired modules times three cases. |
| 9 | voting count is exactly 2, `A1.7` and `A1.8` | **PASSES.** `['A1.7', 'A1.8']`. |
| 10 | Group C does not contribute to project status | **PASSES.** No Group C key appears in `category_statuses` on the probe; `assets/js/taxonomy.js:605` states the same exclusion. |
| 11 | all four B1 modules reachable from `research_export.py` | **PASSES.** `"B1.1", "B1.2", "B1.3", "B1.4"` present, and none is retired. |
| 12 | Portfolio Health computes nowhere | **PASSES.** Section 6 above. |
| 13 | the `models_sim.py:254` guard fails if the retained adaptation becomes reachable | **PASSES, proved by injection.** Section 3.2. |
| 14 | the successor freeze gate passes in full | **FAILS.** `test_run37_freeze_gate` 23/30, blocker classes B01, B11 and B15 non-zero. **B02 is now zero** — `registered total=63 expected 101` was Run 43B's reading and the restoration cleared it. |

### 7.1 The self-rewriting audit artifacts

Run 41A saw 13, Run 43 saw 14, Run 43B saw 15. **This run's full suite rewrote 18.** All 18 were
restored with `git checkout --`. **None was committed.** The three not on Run 43B's list are new to
this run's list and are reported as such:

```
code_audit/run10_no_operational_effect.csv          code_audit/run9_abstention_results.csv
code_audit/run20_cycle12_100_reaudit.csv     NEW    code_audit/run9_alias_overlay_verification.csv
code_audit/run20_cycle12_guard_nonvacuity.csv       code_audit/run9_fixture_import_results.csv
code_audit/run20_cycle12_lineage_campaign.csv       code_audit/run9_known_answer_results.csv
code_audit/run21_guard_nonvacuity_results.csv NEW   code_audit/run9_no_operational_effect.csv
code_audit/run30_closure_fault_injection.csv        code_audit/run9_validator_gap_recomputations.csv
code_audit/run34_count_fault_injection_results.csv  code_audit/run38_lock_integrity.csv
code_audit/run34_provenance_fault_injection_results.csv  code_audit/run38_participant_state_machine.csv
code_audit/run38_controlled_stimulus_execution_order.csv
server/tools/run17/coverage.csv              NEW  (outside code_audit/ — the first one seen there)
```

`git add -A` and `git add .` were not used at any point in this run. Every commit named its paths
explicitly, and no suite ran in the background while anything was staged.

---

## 8. Section 5.6 — the check count

| | suites | checks |
|---|---|---|
| pre-retirement baseline, `f461630` | 188 | 14,176 / 14,176 |
| this run's head, `776f130` | 188 | **12,203 / 12,539** |
| difference | 0 | **-1,637 in the denominator** |

**The totals do not match the baseline, and section 5.6 asks for the difference item by item
rather than a forced reconciliation. It is presented that way, and no bucket is invented.**

The denominator shortfall of 1,637 is **entirely and only** the checks in the fourteen suites that
abort before printing a canonical RESULT line. It is not a set of removed checks: **no check was
removed by this run**, and the two sanctioned changes are net +3 (five assertions rewritten in
place in `test_map_and_module_count.py`, three added; one rewritten in place in `models_sim.py`).
The fourteen are named individually with their aborting line and exception at section 5.1 class 3
above. The instrument still cannot report how many checks a crashed suite would have had — Run
43B's finding 5, unchanged — so the 1,637 is derived as the residual against the baseline and is
labelled as such rather than counted directly.

**Every check that changed state, and why:**

| what changed | count | why |
|---|---|---|
| checks that ran under `83c832d` and now pass | +2,769 net passing | the retirement refusal replaced `MissingModuleError`, so suites no longer abort and their checks execute |
| suites that stopped aborting | 76 red to 62 red, 14 still aborting | as above |
| `test_map_and_module_count.py` | 5 rewritten, 3 added | sanctioned at 5.4; 68/72 to 75/75 |
| `models_sim.assert_retained_adaptation_not_reachable` | 1 rewritten | sanctioned at 5.3; `test_run36_closure_guards` 15/15 |
| checks removed | **0** | none, by any route |

---

## 9. Section 2 — the gate between phases, and the Phase E verdict

| # | condition | verdict |
|---|---|---|
| 1 | Phase D merged, `HEAD == main == origin/main` | **FAILS.** Not merged. `main` remains at `f461630`. |
| 2 | full suite green on merged main, count reported per 5.6 | **FAILS.** 62 red. The count is reported at section 8; it does not match the baseline. |
| 3 | `sim-2026.08-v28` stamped, every gate re-run and reported | **FAILS.** Not minted; the live stamp is `sim-2026.08-v27`. |
| 4 | no Phase D stop condition open | **FAILS.** 7.1 and 7.4 are open. |

**All four fail. PHASE E WAS NOT BEGUN.** No file of Phase E's was created: no diagnosis of the
eleven defects at section 10, no abstention classification at section 11, no fixture, and no
artifact under `code_audit/`. Section 8's instruction is unambiguous, and the gate is not partly
satisfied — it is unsatisfied in every condition.

---

## 10. Section 5.7 — freeze and merge, not done

1. `sim-2026.08-v28` **not minted.** Minting a successor over 62 red suites would be a stamp
   without re-run gates, which 5.7.2 says is not a freeze. The freeze manifests of 5.7.1 were
   **not** re-pinned: re-pinning a byte-identity guard to a tree that is being left unmerged would
   pin a state nothing has accepted, and the reconciliation is meaningless until the tree is final.
   Reported as blocked on the stop, not skipped.
2. Gates **not re-run to a verdict table**, because the freeze was not taken. The one gate that can
   be reported is `test_run37_freeze_gate`: 23/30, blockers B01, B11, B15; B02 cleared.
3. **Not merged.** The branch is left unmerged, as section 7 requires.
4. This report is written; the decision record and `T6_HANDOFF.md` are updated.

---

## 11. Findings recorded and not acted on

1. **`A1.1` in `assets/js/taxonomy.js` does not reproduce.** 63 against 63. Section 2.3.
2. **`assets/js/knowledge.js` and `assets/js/deepdive.js` still enumerate retired modules** on the
   methods-documentation surface. Section 7, test 3.
3. **`server/tools/run17/coverage.csv` is a self-rewriting audit artifact outside `code_audit/`.**
   Every prior run's list assumed they were all under `code_audit/`; a `git checkout -- code_audit/`
   alone would have left this one modified.
4. **The `retired` key on the portfolio snapshot is still carried and unread** by any surface.
   Run 43B's finding 7, unchanged.
5. **`registry_index()` now resolves retired ids, which makes it the wrong function for any caller
   building a population.** Two were found and moved to `service_index()`. Any future caller has
   the same trap in front of it, and the two function names are one word apart.

---

## 12. What the next session needs, stated as a decision for the owner

This is a decision, not a recommendation.

**Section 5.1's ruling was right about the mechanism and wrong about the cost, and the difference is
now measured rather than predicted.** Removal from service is the correct mechanism: it restored
2,924 checks to execution, fixed the `RETIRED` literal leak by construction, made the registry
resolve all 101 while serving 63, and let the one production guard at `models_sim.py:254` keep
proving its own subject. None of that should be reverted, whatever is decided next.

What it does not do is make the instrument green, because the instrument's qualification evidence
is not written against "a module refuses". It is written against **which** refusal, and against
hand-computed figures, per module, per check body. Retiring a module falsifies every one of those
bodies whose subject it is. That is true of removal from existence and it is equally true of
removal from service; the ruling moved the failure from a crash to a failed assertion, which is
progress in diagnosis and no change at all in the count of bodies that must move.

The owner sanctioned exactly two body changes because Run 43B surfaced exactly two. Run 43B
surfaced two because it stopped before the mechanism existed to reveal the rest. The rest is now
visible and counted: **181 failing checks naming a retired module, across 26 suites, plus 14 suites
that abort on a body-level index into a results dict that no longer carries the key.**

The choice is unchanged in shape from Run 43B's and narrowed in content by this run:

- **(A)** Sanction check-body changes wherever the check's subject is a retired module, as a class
  rather than case by case, and state what such a check must assert instead. On the measurement
  above this is roughly 181 assertions in 26 suites plus 14 body-level index sites. The instrument
  keeps its check count and changes what a large part of it asserts.
- **(B)** Sanction removing the suites and guards whose subject is wholly retired. The instrument's
  check count falls by that amount and the evidence covering the 38 goes with it.
- **(C)** Narrow the retirement. The collision is proportional to how many of the 38 had
  qualification evidence written about them; reason-4 retirements (7 modules, all computing
  correctly, all sharing a governed structure with a partner in service) cost the most evidence per
  module retired.

**Do not choose by counting suites.** Each option changes what the instrument's qualification
evidence *consists of*, and that is a research-integrity decision, not a maintenance one. That is
why Run 43 stopped, why Run 43B stopped, and why this run stops — one mechanism further along, with
the mechanism built and the cost counted instead of estimated.
