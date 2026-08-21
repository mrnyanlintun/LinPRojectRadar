# Run 43B — Retirement Completion

**Date:** 2026-08-21
**Repository used:** the Linux clone at `/home/user/LinPRojectRadar`. The Windows path at
`C:\Users\NTUN\OneDrive - Arora Engineers, LLC\DEng\LinPRojectRadar` was not used and is not
reachable from this session (section 4 asks which; this is the answer).
**Interpreter:** no `.venv` exists in this clone. `server/run_all_suites.sh` falls back to the
`python3` on `PATH` by its own documented fallback, which is what ran every figure below.
**Branch:** `claude/run43B-retirement-completion`, rooted at `b37f133`.
**Merged:** NO. **Successor stamp minted:** NO. The live stamp remains `sim-2026.08-v27`.

---

## 0. The outcome, stated first

**STOP CONDITION 7.1 FIRED: a check body must change for a suite to pass.**
**STOP CONDITION 7.8 FIRED WITH IT: the successor freeze cannot be taken without weakening a
guard.**

Phase A is left unmerged. **Phase B was not begun**, because the section 2 gate fails on all
four of its conditions, not merely on one. See section 8.

Three pieces of Phase A were completed and are committed, because each is self-contained, each
was independently ordered, and none of them depends on the repointing that the stop condition
blocks: the two known-stale artifact reconciliations of section 5.2, the Portfolio Health
offload of section 5.3, and the section 5.2 step 1 enumeration. They are reported in sections
4, 5 and 6. Nothing was removed under 5.2 step 3.

**The check count reconciliation of section 5.4 is NOT reported as a balanced three-bucket
account, because the phase that would have produced the post figure did not run.** Reporting a
reconciliation that does not sum would itself be stop condition 7.3. What is reported instead is
the measured before and after of the work that was done. See section 7.

---

## 1. The branch-point question the owner asked to be handled and reported

Section 1 says "Branch from `b37f133`", and that is what was done. `b37f133` does not carry the
Run 43 report or the decision record; they were created one commit later on `d8fe98d`, and
sections 3.3 and 5.5.4 require both to be read and updated.

Both files were brought forward onto this branch with
`git checkout d8fe98d -- MODULE_RETIREMENT_DECISIONS.md REPORT_2026-08-21_run43_module_retirement.md`
and committed as `b4ec696`. The branch is therefore rooted at `b37f133` as instructed, and it
carries the two documents. `T6_HANDOFF.md` was deliberately NOT brought forward in that commit;
it is updated at the end of the phase per section 3.1.

The history requirement at 5.5.3 is satisfied either way: `5282d72` (52 to 53, 100 to 101) and
`b37f133` (101 to 63) remain distinct commits in this branch's ancestry.

---

## 2. Section 3.2 — the sentence fixing group naming, quoted

From `NAMING_AUTHORITY.md` section 4:

> **Never use a module id or number in user-facing text.** No "Cat 4", no "1.7", no "PH.2", no
> "A4.2". Groups and purposes only. The old "Cat N" scheme is retired along with the names.

And, governing the same surface one line earlier:

> **Group C does not contribute to project status.** Evidence quality describes what is known
> about a project, not the project's condition.

Both governed the one user-facing sentence this run introduced. See section 5.

---

## 3. The baseline, reproduced rather than trusted — and one correction to it

Run at `b37f133` before any change, with `PYTHONIOENCODING=utf-8`, each suite against its own
freshly migrated SQLite database:

```
Suites run: 188   Total checks: 9671/9817
```

That reproduces the prior attempt's figure exactly.

**THE FAILING-SUITE COUNT IS 72, NOT 73.** The controlling prompt says 73 in sections 1 and 5.1,
and the prior attempt reported 73. The runner's own arithmetic contradicts both:

```
$ grep -c '^ok '   baseline.txt   -> 116
$ grep -c '^FAIL ' baseline.txt   -> 72
                                     116 + 72 = 188
$ FAILED SUITES: block               -> 72 entries, no duplicates
```

Every "73" below should be read as 72. This is reported, not corrected in the prompt.

**Failure modes, mechanically classified over the 72:**

| mode | count |
|---|---|
| crashes with `MissingModuleError` on a retired id | 32 |
| crashes with `KeyError` on a retired id | 6 |
| runs to completion with failing checks | 34 |

---

## 4. Section 5.1 — why the repointing could not be done, and the evidence

### 4.1 The premise of section 5.1 does not hold

Section 5.1 states: "The 73 suites enumerate hard-coded identifier lists. Repoint each to
enumerate the live registry." Constraint 1 then forbids changing a check body.

**The 72 suites do not, in the main, enumerate hard-coded identifier lists.** Measured over the
72 source files, counting only quoted literal module identifiers:

| | suites | literal retired-id occurrences |
|---|---|---|
| carry at least one literal retired identifier in the source | **53** | **845** |
| carry none | 19 | 0 |

In the 53, the retired identifier is not in an enumeration source. It is **inside the check
body** — as the subject of a hand-written per-module block, or as a hand-computed expected value.
There is nothing to repoint. Two examples, quoted:

`server/tools/test_run29_supply_path_guard.py:164`

```python
_t = REG.run_module("A5.3", _si53, RAND, CUTOFF)
check(not _t.get("insufficient_data") and _t.get("ranked_inputs") == ["A", "C", "B"],
      "A5.3 computes from the SAME governed key A5.2 does, which is the parsimony decision",
      str(_t.get("ranked_inputs")))
```

The identifier, the fixture, the expected value `["A", "C", "B"]` and the assertion are one
block about one retired module. There is no enumeration source in it.

`server/tools/test_run19_category_2.py:398`, inside a function named `m_2_4`:

```python
out = run("A2.4", _network(acts))
```

`m_2_4` exists to test A2.4. The suite's structure is one hand-written function per module, not
a loop over a list.

### 4.2 The 19 suites carrying no literal retired identifier do not fail for a repointable reason either

This is the part that decides the phase. Those 19 were the best candidates for a clean
enumeration repoint. Measured, they fail through four mechanisms, none of which is an
enumeration source:

**(a) Hard-coded expected COUNTS inside check bodies.** From the captured run of
`server/tools/test_map_and_module_count.py`:

```
FAIL  a project has 96 modules  [63]
FAIL  and the whole taxonomy is still 101 across 12, unchanged  [63/12]
FAIL  Portfolio Health keeps its five modules  [0]
```

and `server/tools/test_run16_final_flow_and_rail.py`:

```
FAILED: the registry declares 96 project-level modules, which is what the label now names  [63]
```

To make these pass, the literal `96` must become `63`, `101` must become `63`, and `five` must
become none. Those literals are the expected values of the assertions. **Changing them is
changing a check body.** That is constraint 5.1.1 and stop condition 7.1, in its plainest form.

**One of them is a direct contradiction between two sections of the same prompt.** Section 5.3
orders Portfolio Health offloaded so that it computes nowhere. `test_map_and_module_count.py`
asserts *"Portfolio Health keeps its five modules"*. Both cannot hold. Satisfying 5.3 necessarily
falsifies that check, and the only way to make the suite green again is to change that check's
body. This is reported, not resolved: section 5.3 says report what the surface now shows and
never decide; the same restraint applies to a check that contradicts it.

**(b) Pinned freeze manifests.** Seven suites are byte-identity guards over a governed manifest —
`test_run37_freeze_gate`, `test_run38_frozen_immutability`, `test_run39_frozen_immutability`,
`test_run22_production_tree_completeness`, `test_run41_preservation`, `test_run12_final_verification`,
`test_run11_defensibility_claims`. Run 43 edited four files inside the frozen surface
(`server/app/simulation/registry.py`, `assets/js/taxonomy.js`, `assets/js/categories.js`,
`p0-baseline/module_renumbering_map.csv`), so every one of these guards is correctly red. Making
them green means re-pinning their manifests. Re-pinning a byte-identity guard to accept the bytes
it was installed to refuse is weakening it, which section 5.5.1 forbids outright.

**(c) The retirement mechanism leaks the literal string `RETIRED` into derived populations.**
This is a defect in Run 43 itself, surfacing in at least three suites. From
`test_run31_pass2_acceptance`:

```
****  the gated population is exactly the 17 modules ... [missing=['RETIRED'] extra=[]]
****  Decision Optimization: all 3 modules are gated  [ungated=['RETIRED']]
```

and from `test_run34_parameter_count_closure`:

```
FAIL  the Run-34 artifact generator runs cleanly
      [REGISTRY DISAGREEMENT: ['RETIRED','RETIRED','RETIRED','RETIRED','RETIRED'] vs ['D1.1'..'D1.5']]
```

Run 43 retired modules by writing `RETIRED` into the `new_id` column.
`registry.load_registry()` filters those rows out, so every consumer going through the registry
is correct. Consumers that read `p0-baseline/module_renumbering_map.csv` directly do not filter,
and pick up `RETIRED` as though it were a module identifier. **This is recorded as a finding and
was not acted on.**

**(d) The browser taxonomy did not fully follow the retirement.** Measured:

```
taxonomy.js distinct module ids : 64
registry live                   : 63
in taxonomy but NOT in registry : ['A1.1']
```

Section 6.10 requires `assets/js/taxonomy.js` and the live registry to agree on the count. They
do not: A1.1 survives in the browser taxonomy. `test_run32_client_authority` reports the same
thing independently — *"A1.1 is in the taxonomy authority and not in the registry"*. **Recorded,
not acted on**, because it is a 5.2 step 3 removal and step 3 was never reached.

### 4.3 The irreducible case, demonstrated rather than argued

The clearest instance is `server/tools/test_run36_instrument_qualification.py`. It does not
crash inside itself. It crashes inside **production code**:

```
File ".../server/app/simulation/models_sim.py", line 254,
     in assert_retained_adaptation_not_reachable
File ".../server/app/simulation/registry.py", line 438, in run_module
app.simulation.registry.MissingModuleError: A1.1 is not in the module registry
```

`assert_retained_adaptation_not_reachable` is a production guard that proves A1.1's retained
Monte Carlo adaptation cannot be entered. It proves it by **executing** A1.1 and asserting the
specific abstention that comes back. Its own comment records why it executes, and it is the
whole argument of this section:

> THE PROBE MUST CARRY A QUALIFIED ASSESSMENT, and this is a correction the Run-36 closure
> fault campaign forced. The first version supplied scalars only, so the CATEGORY-9 GATE
> refused the module before this gate was ever reached — and the proof therefore passed
> while the retained adaptation was live and reachable. [...] **a guard that is satisfied by
> somebody else's refusal is proving nothing about its own subject.**

Both available routes were tried, and both were **measured, not reasoned about**:

*Route 1, leave the registry constants alone.* The guard executes A1.1, `run_module` refuses
retired identifiers before any short-circuit, the guard raises. Suite red.

*Route 2, remove the retired identifiers from the registry constants* — which is exactly what
5.2 step 3 authorises, `DISABLED_CONCEPT_ONLY` and its two siblings being registry constants
whose subjects are retired modules and only retired modules (measured: 10 entries, 10 retired,
0 in service). Simulated in-process, the guard then reports:

```
PRODUCTION GUARD assert_retained_adaptation_not_reachable AFTER the 5.2 removal:
  FAILS: A1.1 is in that set
  FAILS: RAISED MissingModuleError: A1.1 is not in the module registry
```

Suite red again, and now for two reasons instead of one.

**There is no third route.** The only way to make this suite green is to change the body of
`assert_retained_adaptation_not_reachable` or delete it.

- Changing it is **stop condition 7.1**.
- Deleting it removes a check, which section 5.5.1 forbids in terms: *"Do not disable, weaken,
  widen, or bypass any guard. Add to the authorised change set; never remove a check from it."*
  That is **stop condition 7.8**.
- Rewriting it to accept `MissingModuleError` as satisfaction would leave the guard resting on
  the registry's refusal while `models_sim.run_monte_carlo` remains present and callable. That
  is, precisely and by name, the weakening the guard's own comment records as having already
  been caught once by the Run-36 fault campaign.

The stop is therefore reported rather than worked around, which is what section 7 asks for.

---

## 5. Section 5.2 — the two known-stale artifacts, reported separately as required

Both are committed at `66519c5`.

**1. `research_export._RUN1_PROXY_QUALIFIERS` reconciled from 30 entries to 1.** The live
registry holds one qualifier, `A1.2`. Runs 28, 29, 30, 32 and 33 withdrew the other 29 as each
proxy was replaced by the canonical method the module's registered name claims; this mirror was
never updated with any of them. It still carried `B4.4`, whose qualifier Run 32 withdrew
explicitly, and `D1.2`, whose qualifier Run 33 withdrew and whose module Run 43 retired. The
export was therefore appending to module names a sentence advertising a weakness the code no
longer has — the error `registry.PROXY_QUALIFIERS`' own note says the table exists to prevent,
in the direction it warns about. Proved reconciled:

```
export mirror: ['A1.2']
live registry: ['A1.2']
IDENTICAL, reconciled
```

It remains a mirror rather than becoming an import, because the reason it is a mirror is
unchanged: `research_export` deliberately holds no import dependency on `app.simulation`. What
changed is that the mirror is now true of the thing it mirrors.

**2. `registry.py`'s prose beside `PROXY_QUALIFIERS` corrected.** It read *"The thirty proxy
modules and the qualifier appended to their canonical name"* beside a dictionary holding one.
The count is deliberately **not** restated as a new number: it is `len(PROXY_QUALIFIERS)`, and
there is now no second place for it to drift out of.

---

## 6. Section 5.3 — the Portfolio Health offload, and what the surface now renders

Committed at `3b49764`. `server/app/simulation/canonical_v8.py` is untouched.

**What was wrong.** Run 43 retired `D1.1` to `D1.5`, but `canonical_v8` computes those same five
readings under the names `PH.1` to `PH.5`, and `canonical_v8.RESULT_KEYS` is the mapping between
the two. Retiring the identifiers in the registry did not stop the computation: the production
dispatcher went on calling `V8.compute_portfolio_health` and storing five readings for five
modules that no longer exist in the taxonomy.

**How it was offloaded.** `portfolio_health.live_portfolio_modules()` intersects
`canonical_v8.RESULT_KEYS` with the live registry, exactly as `registry.available_modules()`
intersects the implemented set with the live registry. There is no list anywhere saying
"Portfolio Health is off"; there is a registry that no longer carries `D1.1` to `D1.5`. Restoring
any of the five rows in `p0-baseline/module_renumbering_map.csv` resumes the route for exactly
that identifier, with no edit to this file.

**The check is made before `assemble()`**, so the intake path is offloaded too. Proved by
monkeypatching both `canonical_v8.compute_portfolio_health` and `assemble` to raise, then
computing a snapshot on a signal package that *does* carry a `portfolioCohort`:

```
live Group D modules: ()
no v8, no assemble. calls= []
route: retired | retired: True | results: {}
```

The formulas are kept, exactly as Run 43 kept the single-project formulas: Runs 15, 33 and 34
recorded findings about these five implementations, and deleting the code would delete the
subject of those findings.

### 6.1 WHAT THE PORTFOLIO SURFACE NOW RENDERS, AND WHERE — reported, not decided

Section 5.3 forbids deciding what the surface shows. Nothing was decided: the offload reuses a
branch the card already had.

**Where:** `assets/js/workspace.js`, the Portfolio Health list, at lines 1009 to 1021. That code
was **not modified**.

**What it renders:** the card already branched on `snap.insufficient_data` and printed
`snap.message` once for the portfolio, in a single `<p class="ws-note">` element, in place of the
per-project cards. The retired snapshot sets both keys, so the panel now renders exactly one line
of text, and no per-project Portfolio Health cards:

> Portfolio Health is no longer part of the analytical taxonomy, so no portfolio-level reading is
> produced. Project Status is unaffected: Portfolio Health never contributed to it.

**No control was added, moved or removed**, so stop condition 7.6 does not fire. The snapshot
keeps its shape, is still stored on every compute, and still carries the three keys the card
branches on.

That sentence was written against `NAMING_AUTHORITY.md` section 4 as quoted in section 2 above:
it contains no module id and no module number, it names the group and its purpose, and it carries
no em dash. Verified mechanically. The second clause is there because the same authority states
that Group D does not contribute to project status, and a reader seeing an analysis disappear
will otherwise reasonably assume their project status just changed.

**One distinction was deliberate and is flagged for the owner.** The snapshot carries a new
`retired: True` key and leaves `results` empty rather than filling it with five abstentions.
`structure_absent` has always meant "the governed cohort was not supplied", which is a statement
about a project's evidence and invites supplying it. Retirement is a statement about the taxonomy
and no evidence will change it. Without the distinction, a surface would go on inviting a user to
supply a cohort for an analysis that no longer exists. **No surface currently reads the `retired`
key**; it is available and unused.

---

## 7. Section 5.4 — the check count, and why the three buckets are not presented

Measured, both figures from full runs of `server/run_all_suites.sh` on this machine:

| | suites | checks |
|---|---|---|
| pre-retirement baseline, `f461630` (Run 43's figure, not re-measured here) | 188 | 14,176 / 14,176 |
| post-retirement, `b37f133`, reproduced by this run | 188 | 9,671 / 9,817 |
| after this phase's three commits | 188 | see section 7.1 |

**The three-bucket reconciliation of section 5.4 is not presented, and that is deliberate.** The
buckets are "removed because their subject retired", "removed for another reason, each named"
and "added by this phase". Bucket 1 is empty and bucket 2 is empty, because 5.2 step 3 was never
reached and nothing was removed. Bucket 3 is empty, because the repointing that would have added
the 5.1.3 population assertions was blocked by the stop condition. Three empty buckets cannot sum
to a delta of 4,359. Presenting them as if they did would be the failure 7.3 exists to catch, so
the delta is left explicitly unaccounted rather than balanced by assertion.

**The 4,359-check delta is not a set of deleted checks. It is checks that never ran**, because 38
of the 72 suites abort on an uncaught exception partway through. That is why the post figure has
a denominator of 9,817 rather than 14,176: 4,359 checks are unexecuted, not removed. Any real
reconciliation has to separate "did not run" from "was removed", and the instrument cannot
currently report the first, because a suite that dies mid-file never prints how many checks it
would have had.

### 7.1 What this phase's three commits changed in the suite result

Full suite re-run on this branch after all three commits:

```
Suites run: 188   Total checks: 9434/9615
FAIL lines: 76   ok: 112
```

| | suites | checks |
|---|---|---|
| `b37f133`, this run's reproduced baseline | 188 | 9,671 / 9,817 — 72 red |
| this branch, after the three commits | 188 | 9,434 / 9,615 — 76 red |

**Four suites that were green at `b37f133` are red on this branch. All four are collateral of
the section 5.3 offload, which the owner ordered, and all four have a retired-module subject.**
Named individually, as section 5.4 bucket 2 would require:

| suite | before | after | cause |
|---|---|---|---|
| `tools/test_run33_portfolio_health.py` | green | crashes | `KeyError: 'cat8_2_portfolio_outlier'` at line 743 — the dispatcher no longer computes PH.2 |
| `tools/test_run34_holdout_provenance.py` | green | crashes | portfolio parameter provenance, same cause |
| `tools/test_run34_provenance_fault_campaign.py` | green | 7/26 | portfolio parameter provenance, same cause |
| `tools/test_period_series.py` | green | 42/46 | all four failing checks are Portfolio Health checks, verified individually |

Each was confirmed by running the suite in isolation and reading the failing check text, not
inferred from the aggregate. `test_period_series.py`'s four failures were checked one by one and
every one names the trajectory classifier or a Portfolio Health identity.

**These four are exactly the artifacts 5.2 step 3 would have removed** — their subject is the
retired `D1.1` to `D1.5` computation and nothing else. Step 3 was not reached, so they stay red
and are reported rather than removed. **This is not a hidden cost of the offload; it is the
offload's visible consequence, and it is why 5.2 step 3 and 5.3 were meant to land together.**

### 7.2 The self-rewriting audit artifacts, per section 6

Running the suites rewrote committed audit artifacts, as Run 41A (13) and Run 43 (14) both
recorded. **This run's full suite rewrote 15. All 15 were restored with
`git checkout -- code_audit/`. None was committed.** They are:

```
code_audit/run10_no_operational_effect.csv
code_audit/run20_cycle12_guard_nonvacuity.csv
code_audit/run20_cycle12_lineage_campaign.csv
code_audit/run30_closure_fault_injection.csv
code_audit/run34_count_fault_injection_results.csv
code_audit/run34_provenance_fault_injection_results.csv
code_audit/run38_controlled_stimulus_execution_order.csv
code_audit/run38_lock_integrity.csv
code_audit/run38_participant_state_machine.csv
code_audit/run9_abstention_results.csv
code_audit/run9_alias_overlay_verification.csv
code_audit/run9_fixture_import_results.csv
code_audit/run9_known_answer_results.csv
code_audit/run9_no_operational_effect.csv
code_audit/run9_validator_gap_recomputations.csv
```

**A related incident is reported rather than buried.** An early commit on this branch used
`git add -A` while a fault-injection suite was running in the background, and captured that
suite's *transient* mutation of `server/app/simulation/canonical_v8.py` — a deliberately injected
fault, mid-injection:

```
-        self.members.sort(key=lambda m: m["project_id"])
+        pass  # members left in arrival order
```

It was caught by reading `git show --stat` immediately after committing, and the commit was
amended to contain only the two intended files. **No injected fault reached any commit on this
branch**, and every later commit named its paths explicitly instead of using `-A`. The general
lesson is recorded for the next session: on this repository `git add -A` is unsafe whenever a
suite may be running, because the fault campaigns mutate production files in place.

---

## 8. Section 2 — the gate between phases, and the Phase B verdict

| # | condition | verdict |
|---|---|---|
| 1 | Phase A merged, `HEAD == main == origin/main` | **FAILS.** Not merged. `main` remains at `f461630`. |
| 2 | Full suite green on merged main, count reconciled per 5.5 | **FAILS.** 76 suites red; the reconciliation does not sum and is not presented. |
| 3 | `sim-2026.08-v28` stamped, every gate re-run and reported | **FAILS.** Not minted. The live stamp is `sim-2026.08-v27`. |
| 4 | No Phase A stop condition open | **FAILS.** 7.1 and 7.8 are open. |

**All four fail. PHASE B WAS NOT BEGUN.** No file of Phase B's was created; no diagnosis of the
eleven defects at section 10, no abstention classification at section 11, and no fixture. Section
8's instruction is unambiguous — "Do not begin until the section 2 gate is satisfied" — and the
gate is not partially satisfied, it is unsatisfied in every condition.

---

## 9. Section 5.5 — freeze and merge, not done

1. `sim-2026.08-v28` **not minted**. `server/app/simulation/models.py:475` still reads
   `SIMULATION_VERSION = "sim-2026.08-v27"`. Minting a successor over 76 red suites would be a
   stamp without re-run gates, which section 5.5.2 says is not a freeze.
   *(Note for the record: the prompt has elsewhere in this programme cited `server/app/models.py:475`
   for this stamp. That path does not hold it; the file is `server/app/simulation/models.py`.)*
2. Gates **not re-run to a verdict table**, because the freeze was not taken.
3. **Not merged.** The branch is left unmerged, as section 7 requires.
4. This report is written; the decision record and `T6_HANDOFF.md` are updated.

---

## 10. Section 6 — which tests could be established, and which could not

Only the tests that do not depend on the blocked repointing could be run. Reported honestly,
with those that could not be established named as not established rather than passed over.

| # | test | verdict |
|---|---|---|
| 6.1 | each repointed suite catches an injected fault | **NOT ESTABLISHED.** No suite was repointed. |
| 6.2 | each repointed suite asserts a non-empty population equal to the live count | **NOT ESTABLISHED.** No suite was repointed. |
| 6.3 | per-module check count unchanged for modules in service | **NOT ESTABLISHED.** Requires the post-removal state, which does not exist. |
| 6.4 | retired ids refused at `run_module` | **PASSES.** `registry.py:436-438` raises `MissingModuleError` on any id absent from `registry_index()`, and the check is first, before the Group D check and before all three DISABLED short-circuits. Verified by reading the ordering in the live source. |
| 6.5 | runtime lookups do not fail for any module in service | **PASSES for the registry path.** `available_modules()` intersects `VALIDATED` with the live registry, so no enumeration through it can name a retired id. |
| 6.6 | no module in service changed its computed result | **NOT RE-ESTABLISHED HERE.** Run 43 byte-compared its census with zero retained modules changed, and section 1 forbids redoing it. This phase changed no formula. |
| 6.7 | voting count is exactly 2, `A1.7` and `A1.8` | **PASSES.** Measured: `CORE_VOTING_MODULES: total=2 retired=[] inservice=['A1.7','A1.8']`. |
| 6.8 | Group C does not contribute to project status | **PASSES on the stated authority.** `assets/js/taxonomy.js:605` states `contributes_to_project_status()` excludes Group C and Group D. |
| 6.9 | all four B1 modules reachable from `research_export.py` | **PASSES.** `server/app/research_export.py:334` reads `"B1.1", "B1.2", "B1.3", "B1.4"`. Section 1 records the same four at line 350 pre-Run-43B; the line moved because this phase shortened `_RUN1_PROXY_QUALIFIERS` above it. |
| 6.10 | `assets/js/taxonomy.js` and the live registry agree on the count | **FAILS.** 64 against 63; `A1.1` is in the browser taxonomy and not in the registry. Reported in section 4.2(d), not acted on. |
| 6.11 | Portfolio Health computes nowhere after the offload | **PASSES.** Proved by monkeypatching `canonical_v8.compute_portfolio_health` and `assemble` to raise; neither is reached. See section 6. |
| 6.12 | the successor freeze gate passes in full | **FAILS.** `test_run37_freeze_gate` reports blocker classes B01, B02 and B11 non-zero, including `B02: registered total=63 expected 101`. |

---

## 11. Findings recorded and not acted on

1. **The failing-suite count is 72, not 73.** Section 3.
2. **The retirement mechanism leaks the literal string `RETIRED` into derived populations.**
   Consumers that read `p0-baseline/module_renumbering_map.csv` without going through
   `registry.load_registry()` treat `RETIRED` as a module identifier. Section 4.2(c).
3. **`A1.1` survives in `assets/js/taxonomy.js`** after Run 43. Section 4.2(d).
4. **`test_map_and_module_count.py` asserts "Portfolio Health keeps its five modules"**, which
   section 5.3 of this prompt orders falsified. Two instructions of the same prompt cannot both
   be satisfied. Section 4.2(a).
5. **The instrument cannot report how many checks a crashed suite would have had**, which is why
   the 4,359 delta cannot be split into "did not run" and "was removed". Section 7.
6. **`git add -A` is unsafe on this repository while any suite may be running.** Section 7.2.
7. **The `retired` key on the portfolio snapshot is carried and unread.** Section 6.1.

---

## 12. What the next session needs, stated as a decision for the owner

This is a decision, not a recommendation, and it is the same shape as the one Run 43 left.

**Section 5.1's constraint and the state of the suites are incompatible, and no ordering of the
work resolves it.** The instrument's qualification evidence is, to a large extent, hand-written
per-module checks and pinned byte-identity manifests. Retiring 38 modules necessarily falsifies
every check whose subject is one of them and every manifest that pins a file the retirement
edited. Those checks cannot be repointed, because they have no enumeration source to repoint;
they can only be removed, or their bodies changed.

Section 5.2 authorises removing artifacts whose subject is retired. Section 5.5.1 forbids
removing a check from the authorised change set and forbids weakening a guard. **For the
production guard `models_sim.assert_retained_adaptation_not_reachable` the two collide with no
gap between them**, and that collision was demonstrated in section 4.3 rather than argued.

The owner has to choose which of these the retirement is allowed to cost, because both are
owner-mandated and this session may not choose between them:

- **(A)** Permit check bodies to change where the check's subject is a retired module — including
  the body of a production guard — and state what the guard must assert instead once its subject
  no longer exists.
- **(B)** Permit whole guards and suites to be removed where their subject is wholly retired,
  accepting that the instrument's qualification evidence shrinks by the checks that covered the
  38, and that `assert_retained_adaptation_not_reachable` goes with them.
- **(C)** Re-pin the frozen manifests to the post-retirement tree as an owner-authorised successor
  change, which is what Run 41 did for its own successor changes, and state whether the
  retirement counts as one.

**Whichever is chosen, it changes what the instrument's qualification evidence consists of.** That
is why Run 43 stopped, and it is why Run 43B stops at the same wall one step further along, with
the wall now measured instead of predicted.

