# Run 43F — Retirement Is Delinking From Category

**Date:** 2026-08-21
**Repository used:** the Linux clone at `/home/user/LinPRojectRadar` (section 4 asks which). The
Windows path at `C:\Users\NTUN\OneDrive - Arora Engineers, LLC\DEng\LinPRojectRadar` is not
reachable from this session and was not used.
**Interpreter:** no `.venv` exists in this clone. `server/run_all_suites.sh` falls back to the
`python3` on `PATH` by its own documented fallback, and every figure below came from that.
**Branch:** `claude/run43F-retirement-delink`, built on `22bb7d2`.
**Merged:** NO. **Successor stamp minted:** NO. The live stamp remains `sim-2026.08-v27` at
`server/app/simulation/models.py:475`.
**No browser session was opened**, so the section 4.3 `cwd` question does not arise.

---

## 0. The outcome, stated first

**Section 5.1 is built, and it does exactly what the ruling says.** `run_module()` on every one of
the 101 registered identifiers — all 38 retired ones included — is now **byte-identical to
`f461630`**, measured against a worktree at that commit. Six of the fourteen suites that aborted
under Phase D now run. Test 6.1 passes and was proved failable.

**Two stop conditions nevertheless fire, and neither is the one Phase D hit.**

- **STOP CONDITION 7.1** — a check body must change beyond the two already sanctioned. **114
  checks across 34 suites and 8 further suites that abort outright** assert the *pre-retirement
  population*: that a named retired identifier reaches the ledger, the abstention list, the
  taxonomy, or a results dict. This class is not created by any refusal semantics — it is created
  by delinking itself, which is section 5.1's own requirement 2.
- **STOP CONDITION 7.6** — all four Portfolio Health suites fall into **class 1** at section 5.4:
  each asserts the pre-offload state. A fifth suite, `test_run34_count_fault_campaign.py`, joins
  them for the same reason.

Phase F is left **unmerged**. **The section 2 gate therefore fails on all four conditions and
Phase G was not begun.**

**Section 5.6's expected outcome does not hold, and the difference reconciles exactly.** Baseline
reproduced on this machine at `f461630`: **188 suites, 14,176/14,176, 0 red.** Phase F head: **188
suites, 13,326/13,440, 114 red.** The 736-check shortfall is accounted for item by item at
section 6 and sums to 736 with nothing left over.

---

## 1. Section 3.2 — the sentence fixing group naming, quoted

From `NAMING_AUTHORITY.md` line 96:

> **Never use a module id or number in user-facing text.** No "Cat 4", no "1.7", no "PH.2", no
> "A4.2". Groups and purposes only. The old "Cat N" scheme is retired along with the names.

---

## 2. Section 5.1 — what was removed, what was kept

One commit, `0206892`. Removed:

| removed | file | why |
|---|---|---|
| the `RETIRED_FROM_SERVICE` short-circuit in `run_module()` | `registry.py` | section 5.1 withdraws the retirement refusal outright |
| the `RETIRED_FROM_SERVICE` branch in `activation_state()` | `registry.py:307` | `activation_state()` feeds `run_module()`'s output at two sites (`registry.py:670`, `:716`), so a retirement branch there would also have changed `run_module()`'s bytes |
| `RETIRED_FROM_SERVICE_CODE` | `registry.py` | no consumer remains |
| Phase D's assertion change in `assert_retained_adaptation_not_reachable` | `models_sim.py` | see 2.1 |

Kept, unchanged from Phase D: the restoration of all 38 identifiers to
`p0-baseline/module_renumbering_map.csv`, and the derived roster — `retired_modules()`,
`is_retired()`, `modules_in_service()`, `service_index()` — together with every population that
now derives from `service_index()` (`available_modules()`, `unported_modules()`,
`training._abstained_by_category()`, `portfolio_health.live_portfolio_modules()`). No list of
retired identifiers is written anywhere; the CSV remains the single authority.

### 2.1 The one place section 1 item 6 and section 5.1 collide, and how it was resolved

Section 1 item 6 says the sanctioned `models_sim.py:254` guard change stands. That change asserts
`abstention_reason_code == RETIRED_FROM_SERVICE_CODE`. Section 5.1 withdraws the refusal that
produces that code, so the sanctioned assertion cannot hold and the guard would fail.

**The guard body was restored to its `f461630` text, byte for byte.** `server/app/simulation/models_sim.py`
now `diff`s empty against the `f461630` worktree. This is reported rather than decided: restoring a
body to baseline is not a *change beyond* baseline, and the alternative — keeping a sanctioned
assertion that section 5.1 makes false — is not available. **If the owner intends the Phase D
guard change to survive section 5.1, this decision must be reversed and section 5.1 amended,
because the two cannot both stand.**

Measured after restoration: the guard runs **7/7 green**. Its failability proof of record is Phase
D's, against this same body, by making the retained adaptation genuinely reachable at
`p50_eac = 1106667.41`. It could not be re-proved by monkeypatching in this session because the
guard reads its own subject through `inspect.getsource`, which a patched function does not have.

---

## 3. Section 6 — the tests

| # | test | verdict |
|---|---|---|
| 6.1 | `run_module()` on each of the 38 is byte-identical to `f461630` | **PASS** |
| 6.2 | no retired module is linked to any category | **PASS** |
| 6.3 | no retired module appears in the rollup, project status, category population, participant surfaces, brief, decision card, courses of action, export, browser taxonomy | **PASS**, see section 4 |
| 6.4 | modules in service is 63, derived from category linkage | **PASS** |
| 6.5 | registry total is 101, derived | **PASS** |
| 6.6 | `assets/js/taxonomy.js` and the live registry agree | **PASS against the service roster; the committed check compares against the 101 and is red** — see 7.1 |
| 6.7 | no module in service changed its computed result | **PASS**, subsumed by 6.1 |
| 6.8 | voting count is exactly 2, `A1.7` and `A1.8` | **PASS** (`test_run37_freeze_gate` B09 zero) |
| 6.9 | Group C does not contribute to project status | **PASS** |
| 6.10 | all four B1 modules remain reachable from `research_export.py` | **PASS** |
| 6.11 | Portfolio Health computes nowhere | **PASS** |
| 6.12 | the `models_sim.py:254` guard | **PASS 7/7** |
| 6.13 | all 188 suites run, none aborts | **FAIL — 8 abort** |
| 6.14 | the successor freeze gate passes 30/30 | **FAIL — 24/30** |

### 6.1, in full

A harness ran `run_module()` over **every one of the 101 registered identifiers** — not only the
38 — against two input fixtures (an empty `si`, and `build_run13_evidence.STRUCTURED`), serialised
the result or the exception deterministically, and diffed the two trees:

```
diff out_base.json out_head.json   ->   0 lines
```

**Proved failable.** Re-injecting a retirement short-circuit at the top of `run_module()` produced
**1,530 diff lines**; removing it returned the diff to **0**. `DISABLED_UNSAFE` is
`DISABLED_UNSAFE` again, `canonical_structure_absent` is `canonical_structure_absent` again, and
the Group D `PortfolioModuleError` is raised again with its original sentence.

### 6.4, 6.5, 6.6, 6.8, 6.9, 6.11 as measured

```
in service: 63 | registry: 101
voting: ['A1.7', 'A1.8']
contributes_to_project_status: A True  B True  C False  D False
live_portfolio_modules(): ()
taxonomy.js ids: 63   == modules_in_service(): True   retired present: []
categories.js ids: 63                                 retired linked:  []
```

---

## 4. Section 5.3 — the non-category-path check, run against all 38

Every one of the 38 retired identifiers was searched for as a whole token across
`research_export.py`, `recommendation_basis.py`, `research_decision.py`, `documents.py`,
`models_gov.py`, `training.py`, `detail.js`, `decision-ui.js`, `export.js`, `signals.js`,
`store.js`, `app.js`, `workspace.js`, `ds_defensibility_data.js`, `ds_defensibility_evidence.js`,
`categories.js` and `taxonomy.js`. **163 textual hits over 38 identifiers.** Every one was
classified by reading its call site:

| class | example | is it a read? |
|---|---|---|
| lookup table keyed by `module_id` | `research_export._RUN1_DISABLED`, `decision-ui.js:123 moduleName(id)`, `workspace.js:109` | **No.** Resolved only for an id that arrives from a stored result. `build_module_results_rows` (`research_export.py:792`) iterates `result.module_results`, never the registry, so no retired id can arrive. |
| implementation dispatch table | `models_gov.py:943` `VALIDATED` | **No.** Reached only through `available_modules()`, which is `set(VALIDATED) & set(service_index())`. |
| comment or prose | `research_export.py:184`, `documents.py:1727`, `models_gov.py:11` | **No.** |
| defensibility data files | `ds_defensibility_data.js`, `ds_defensibility_evidence.js` | **No** — keyed lookups, not enumerations; but see the incidental finding at section 9. |

**No retired module is read by the research export, the Executive Brief, the Governance Decision
card or the courses of action by a path that does not go through its category.** Nothing was
removed. The four B1 modules at `research_export.py:350` (`_RUN3_NEWLY_WIRED`) are present and are
not retired.

---

## 5. Section 5.2 — what each affected surface now shows, and where

Delinking alone empties every participant surface of retired modules; **no style rule was added**,
because after delinking there is no rendered element for a rule to select, and a rule that selects
nothing cannot be proved to do anything. No control was added, moved or removed.

| surface | where | what it now shows |
|---|---|---|
| browser taxonomy | `assets/js/taxonomy.js`, `assets/js/categories.js` | 63 module rows in 12 category objects, of which 11 carry modules |
| Signal Ledger / project detail | driven by stored `module_results`, which derive from `available_modules()` | the 62 computable in-service modules; no retired row appears |
| Evidence Combination category | `categories.js` | **one** module row (MARCOS Ranking), down from twenty |
| Decision Optimisation category | `categories.js` | **two** module rows, down from seven |
| Portfolio Health category | `categories.js`, card at `workspace.js:1010` | **no module rows.** The stored snapshot carries `structure_absent` / `insufficient_data` / `message` and renders through the pre-existing `insufficient_data` branch, with the sentence at `portfolio_health.py:102`: *"Portfolio Health is no longer part of the analytical taxonomy, so no portfolio-level reading is produced. Project Status is unaffected: Portfolio Health never contributed to it."* |

**Placement was not decided here.** This section reports what the surfaces show.

---

## 6. Section 5.6 — the check count, reconciled item by item

Both figures were measured on this machine with the same runner.

| tree | suites | checks | red |
|---|---|---|---|
| `f461630`, in a worktree | 188 | **14,176 / 14,176** | 0 |
| Phase F head | 188 | **13,326 / 13,440** | **114** |

Shortfall against the baseline **total**: 14,176 − 13,440 = **736**.

| item | checks | direction |
|---|---|---|
| 8 suites that abort before printing a `RESULT:` line, losing their whole totals: `test_run16_material_cost_variance_disabled` (79), `test_run20_cycle10_truthful_labels` (52), `test_run30_cat7_operational_route` (67), `test_run30_lineage_semantics` (39), `test_run33_portfolio_health` (149), `test_run34_holdout_provenance` (53), `test_run3_adapter` (53), `test_run8_retest_classify_27` (241) | **−733** | not run |
| `test_run32_defensibility_truth`, 56 → 52: four checks are generated per taxonomy row and two rows are delinked | **−4** | not generated |
| `test_run20_lineage_declaration_truth`, 178 → 176: parametrised over the enumerated population | **−2** | not generated |
| `test_map_and_module_count`, 72 → 75: Phase D's sanctioned change at section 1 item 5 | **+3** | added |

−733 − 4 − 2 + 3 = **−736**. The reconciliation closes exactly, with nothing left over.

**Of the 14 suites that aborted under Phase D, 6 now run and 8 still abort.** The 8 are named
above. None aborts on an activation state or a reason code — every one aborts on a
`KeyError` / `IndexError` / `StopIteration` while indexing a results dict, a ledger row map or a
taxonomy match list **by the identifier of a retired module**:

```
test_run30_cat7_operational_route.py:319  _rows[m]                       KeyError: 'B2.1'
test_run30_lineage_semantics.py:136       _rows[m]                       KeyError: 'B2.1'
test_run3_adapter.py:265                  abst4[mid]                     KeyError: 'B2.1'
test_run8_retest_classify_27.py:1596      _abst[_mid]                    KeyError: 'A2.5'
test_run33_portfolio_health.py:743        _snap["results"]["cat8_2_..."] KeyError: 'cat8_2_portfolio_outlier'
run34_ph1_tree_count_calibration.py:128   real["results"]["cat8_1_..."]  KeyError: 'cat8_1_isolation_forest'
test_run16_material_cost_variance_disabled.py:209  entry[0]              IndexError: list index out of range
test_run20_cycle10_truthful_labels.py:435 next(...)                      StopIteration
```

---

## 7. The stop conditions

### 7.1 — a check body must change beyond the two already sanctioned

**FIRED.** 114 red checks across 34 suites, plus the 8 aborting suites above. The class is
uniform and it is not the Phase D class: nothing here asserts a refusal or a reason code. Every
one asserts that a **retired module is present in an enumerated population**. Section 5.1's own
requirement 2 says it must not be. Both cannot hold, and only a check body can resolve it.
Quoted, unaltered, from the run:

```
test_run30_lineage_semantics ****  all twenty Category-7 identities reach the ledger
                                   [['B2.1','B2.2',...,'B2.20']]
test_run26_counts_and_wiring ****  the taxonomy carries exactly the registry's module ids, so the
                                   browser and the server cannot describe different platforms
                                   [63 taxonomy ids / 101 registry]
test_run32_client_authority  ****  the runtime taxonomy carries exactly the registry's identities
                                   (101), derived rather than counted here
                                   [['A1.1','A2.10','A2.11','A2.4','A2.5','A2.6','A3.4','A3.8']]
test_run24_empty_project_diagram ****  the registry holds 96 project-level modules in 11
                                   project-level categories, and 101 in 12 counting Portfolio
                                   Health  [12/63/11/63]
test_simulation              FAILED: available == validated (95 modules)
test_run1_disable_and_relabel FAILED: all eight disabled modules appear in the abstained list
                                   instead  ['A3.8','B2.20','B2.7','B2.9','B4.1','B4.2','B4.5','B4.6']
test_run7_fix_now_defects    ****  B4.7 is absent from the stored rows and present in the
                                   abstention list, on a real project computed through the real
                                   route  [False]
test_run14_mismatch_remediation  - A2.11: is accounted for on the application's own compute path,
                                   computed or abstained
test_run32_defensibility_truth FAIL: assets/js/taxonomy.js: the B4.7 taxonomy row is present and
                                   parseable
```

**`test_run26_counts_and_wiring` is the clearest single statement of the collision.** It compares
`taxonomy.js` against `registry_index()`. The taxonomy now carries the 63 in service; the registry
resolves 101 by section 5.1's own design. The comparison is correct against `service_index()` and
wrong against `registry_index()`, and only the check body says which.

**Nothing was changed.** No check body was edited and no check was removed.

### 7.6 — the four Portfolio Health suites, section 5.4 classification

**FIRED. All four are class 1: each asserts the pre-offload state.** None is class 2: the offload
is complete and correct, and it is derived rather than declared —
`portfolio_health.live_portfolio_modules()` intersects `canonical_v8.RESULT_KEYS` with
`service_index()` and returns `()`, `canonical_v8` is untouched, and reinstating any of the five in
the CSV would resume the route with no edit. There is no shape of a correct offload that puts back
the dictionary key each of these suites indexes by name.

| suite | verdict | the assertion, and why it fails |
|---|---|---|
| `test_run33_portfolio_health.py` | RED, aborts | line 743 indexes `_snap["results"]["cat8_2_portfolio_outlier"]`. The dispatcher no longer computes it, so the key does not exist. Asserts the pre-offload state. |
| `test_run34_holdout_provenance.py` | RED, aborts | `run34_ph1_tree_count_calibration.py:128` indexes `real["results"]["cat8_1_isolation_forest"]`. Same. |
| `test_run34_provenance_fault_campaign.py` | RED, 7/26 | 19 portfolio-parameter-provenance checks; the campaign's generator depends on the same computed snapshot. `intended RED = 0`, `crashes accepted as RED = 5`. Same. |
| `test_period_series.py` | RED, 42/46 | *"every Portfolio Health identity is addressable in the snapshot with its own reason, so an abstention is distinguishable from a module that was never there"* `[[]]`. It asserts five addressable identities; requirement 2 forbids a retired module contributing to any surface. Same. |

**A fifth suite belongs to the same class and was not in Phase D's four:**
`test_run34_count_fault_campaign.py`, 14/26, whose fault campaign runs the same Run-34 artifact
generator. `test_workspace_t3t5.py` (74/79) carries the same assertion in a sixth suite: *"all five
Portfolio Health identities are addressable in the stored snapshot"* `[]`.

**No check body was changed under section 5.4.**

### 7.7 — the freeze gate

**Not fired as a stop in its own right, but reported here in full.** The gate is **24/30**, up
from Phase D's 23/30. Six rows fail:

| row | verdict | cause |
|---|---|---|
| `run37.gate.reproduces` | FAIL | `[15 fresh vs 15 committed]` — the acceptance record does not reproduce from the current tree |
| `run37.gate.B01` dirty candidate identity | FAIL | `git porcelain lines at evaluation: 17`. **This is the instrument's own artifact rewriting, not an edit of this run** — see section 8. |
| `run37.gate.B11` package or predecessor mutation | FAIL | `v13 files not matching their record: ['assets/js/categories.js','assets/js/detail.js','assets/js/taxonomy.js', …]`. **This is a pinned byte-identity manifest falsified by this retirement's edits** and is the one row section 5.5 permits reconciling. |
| `run37.gate.blocking_defects_zero` | FAIL | consequence of B01 and B11 |
| `run37.gate.no_release_while_blocked` | FAIL | consequence |
| `run37.gate.disposition` | FAIL | consequence |

**B02 (population mismatch) is zero and B15 (candidate behaviour changed during the run) is now
zero** — B15 was non-zero under Phase D and section 5.1's withdrawal cleared it.

**No manifest was reconciled and no row was disabled, weakened, widened or bypassed.** Section 5.5
reconciliation and section 5.7's mint-and-merge were not reached: 7.1 and 7.6 fired first, and
reconciling a manifest to a tree that is not going to merge would pin a state the owner has not
accepted. The same reasoning covers the other manifest-class reds, which are the same finding seen
from six more suites: `test_run22_production_tree_completeness` (41/44),
`test_run28_closure` (77/78), `test_run28_participant_packages` (75/78),
`test_run38_frozen_immutability` (11/17), `test_run39_frozen_immutability` (14/19),
`test_run20_declared_production_changes` (126/128, undeclared: `research_export.py`,
`training.py`), `test_run6_known_answer` (487/488, `training.py`), `test_run41_preservation`
(32/33), `test_run10_state_protection` (83/84).

### The other stop conditions

| # | verdict |
|---|---|
| 7.2 any check must be removed | not fired; none was removed |
| 7.3 `run_module()` differs from `f461630` | **not fired** — 0 diff lines over all 101 identifiers |
| 7.4 any module in service changed its computed result | not fired, subsumed by 7.3 |
| 7.5 a retired module read by a non-category path | not fired — section 4 |
| 7.8 a step would add, move or remove a user-facing control | not fired; none was touched |

---

## 8. The self-rewriting audit artifacts

The suite run rewrote **17** artifacts, one of them outside `code_audit/`. Phase D reported 18;
this run observed 17 and the difference is not explained here rather than reconciled with a guess.

```
code_audit/run10_no_operational_effect.csv        code_audit/run9_abstention_results.csv
code_audit/run20_cycle12_100_reaudit.csv          code_audit/run9_alias_overlay_verification.csv
code_audit/run20_cycle12_guard_nonvacuity.csv     code_audit/run9_fixture_import_results.csv
code_audit/run20_cycle12_lineage_campaign.csv     code_audit/run9_known_answer_results.csv
code_audit/run21_guard_nonvacuity_results.csv     code_audit/run9_no_operational_effect.csv
code_audit/run34_count_fault_injection_results.csv        code_audit/run9_validator_gap_recomputations.csv
code_audit/run34_provenance_fault_injection_results.csv   server/tools/run17/coverage.csv   <-- outside code_audit/
code_audit/run38_controlled_stimulus_execution_order.csv
code_audit/run38_lock_integrity.csv
code_audit/run38_participant_state_machine.csv
```

**All 17 were restored. None was committed.** The working tree is clean apart from this run's own
commits. The `f461630` worktree was likewise dirtied by 40 paths during the baseline run and
restored.

---

## 9. Incidental findings, unacted

1. **`test_run34_holdout_provenance` aborts inside a generator, not inside a check body.** The
   failing index is at `server/tools/run34_ph1_tree_count_calibration.py:128`, a tool the suite
   imports. Whether that counts as a check body for the purposes of stop condition 7.1 is a
   question for the owner; it was treated as one here and nothing was edited.
2. **`assets/js/ds_defensibility_data.js` and `ds_defensibility_evidence.js` still carry rows for
   retired identifiers** (10 and 34 respectively). They are keyed lookups today, so nothing renders
   from them, and section 5.3's question is answered No. But they are generated artifacts of the
   client-taxonomy authorities, and `test_run32_client_authority` reports them
   `NOT GENERATED FROM THE CURRENT AUTHORITIES`. Regenerating them is a change no section of this
   prompt authorises.
3. **The `A1.1`-in-`taxonomy.js` discrepancy does not reproduce**, confirming Phase D against Run
   43B: taxonomy 63 against service 63, exact set equality, no edit needed.
4. **`registry_index()` resolves retired identifiers by design.** Every population built in this
   phase uses `service_index()`. This is restated because the collision at section 7.1 is exactly
   what happens where a committed check still uses the first.

---

## 10. What the next session needs, as a decision for the owner

Stated as a decision, not a recommendation, and not ranked.

1. **The 114 red checks and 8 aborting suites cannot be resolved without changing check bodies.**
   The retirement's own requirement 2 and those bodies assert contradictory populations. Either
   the bodies are re-scoped from `registry_index()` to `service_index()` — a sanction the owner
   has not given and that this phase would not take — or the delinking is narrowed.
2. **Section 1 item 6 and section 5.1 are in direct conflict** (see 2.1). One must be amended.
3. **The four Portfolio Health suites are class 1 and the offload is correct.** Section 5.4 says
   stop. A sanction to re-scope them, or a decision to keep Portfolio Health computing, is the
   only thing that moves them.
4. **The freeze gate's B11 row is reconcilable under section 5.5 and was left alone** because the
   tree is not merging. Reconciling it is one instruction away once items 1 to 3 are settled.
