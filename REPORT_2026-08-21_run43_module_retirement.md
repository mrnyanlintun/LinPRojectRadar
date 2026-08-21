# Run 43: module retirement, count correction, and successor freeze

Date: 2026-08-21
Branch: `claude/run43-module-retirement`, **left UNMERGED**
Repository: **the Linux clone at `/home/user/LinPRojectRadar`**, not the Windows path
`C:\Users\NTUN\OneDrive - Arora Engineers, LLC\DEng\LinPRojectRadar` that the prompt names first.
Interpreter: `/usr/local/bin/python3`. There is **no `.venv` in this clone**; the repository's own
`server/run_all_suites.sh` already falls back to the interpreter on `PATH` for exactly this case.
`PYTHONIOENCODING=utf-8` was set for every suite invocation.
No browser session was opened, so no `preview_start` and no `DEng\Demo` exposure arose.

---

## 0. Outcome, stated first

**STOP CONDITION 15.8 FIRED. The branch is not merged and the successor freeze was not minted.**

> 15.8 — The successor freeze cannot be taken without weakening the guard.

What was completed and is sound:

- The prose count correction, committed separately and first (`5282d72`).
- The retirement of exactly 38 modules, 101 -> 63 (`b37f133`), **proven to change no retained
  module's result**.
- Eight of the nine section 13 guarantees verified, each with an injection proving the check
  could fail.
- The decision record, `MODULE_RETIREMENT_DECISIONS.md`.

What was NOT completed:

- **Requalification.** 73 of 188 suites fail after the retirement.
- **The successor freeze `sim-2026.08-v28`.** Not minted. The live stamp remains
  `sim-2026.08-v27`. Taking the freeze requires the gates green, and bringing them green requires
  deleting roughly 4,359 checks, which section 6.1 forbids.

Section 8 of this report states the decision the owner now has to make.

---

## 1. Verification of the starting state

Every item was re-derived rather than accepted.

| Claim | Verdict |
|---|---|
| `HEAD == main == origin/main == f46163057f052c7968ce1569f03bbe7cdcc1fa77`, tree clean | confirmed |
| `SIMULATION_VERSION = "sim-2026.08-v27"` | confirmed, but at **`server/app/simulation/models.py:475`**. The prompt's section 6 says `server/app/models.py:475`, which does not hold the stamp. |
| Last complete suite 188 suites / 14176 checks green | **confirmed by re-running it** in a clean worktree at `f461630`: 188 suites, 14176/14176, ALL SUITES GREEN |
| `MODULE_RETIREMENT_DECISIONS.md` does not exist | confirmed. Section 12's "if a file of that name already exists" branch did NOT apply; the record was created fresh. |
| Registry holds 101, Group A 53 | confirmed: A 53, B 36, C 7, D 5 |
| `assets/js/taxonomy.js` agrees | confirmed: 101 unique ids, A 53, B 36, C 7, D 5 |
| Voting set is exactly 2 | confirmed: `A1.7`, `A1.8` |
| Three modules compute on the controlled corpus | confirmed: `A1.2`, `A1.7`, `A1.8` |

**`NAMING_AUTHORITY.md` was located** (stop condition 15.7 did not fire). The sentence that fixes
the group naming, quoted as required:

> **Never use a module id or number in user-facing text.** No "Cat 4", no "1.7", no "PH.2", no
> "A4.2". Groups and purposes only. The old "Cat N" scheme is retired along with the names.

with the taxonomy row of its own table reading:

> | The analytical taxonomy | **Groups A, B, C, D** | Referred to by group and purpose |

Also read as required: `T6_HANDOFF.md`, `code_audit/run36_parsimony_reconciliation.csv`,
`REPORT_2026-08-21_run41A_condition_survey.md`, and the Run 42 report
`REPORT_2026-08-21_period-binding-mechanism-repair.md`.

---

## 2. Step 0: the resolved list

### 2.1 The ten disabled identifiers, read from the live registry

Read from `server/app/simulation/registry.py`, not assumed. **All ten matched the list the prompt
offered for verification, exactly, set for set.**

| Identifier | Name | Set it came from |
|---|---|---|
| `A3.8` | Parametric Cost Index | `DISABLED_CONCEPT_ONLY` |
| `B2.7` | Plithogenic Sets | `DISABLED_CONCEPT_ONLY` |
| `B2.9` | Quantum Probability | `DISABLED_CONCEPT_ONLY` |
| `B2.20` | Hypersoft Sets | `DISABLED_CONCEPT_ONLY` |
| `B4.1` | Multi-Objective Optimization | `DISABLED_CONCEPT_ONLY` |
| `B4.2` | Linear Programming | `DISABLED_CONCEPT_ONLY` |
| `B4.5` | Decision Sensitivity Matrix | `DISABLED_CONCEPT_ONLY` |
| `B4.6` | Pareto Frontier Analysis | `DISABLED_CONCEPT_ONLY` |
| `A3.4` | Material Cost Variance | `DISABLED_EVIDENCE_UNDER_REVIEW` |
| `A1.1` | Monte Carlo EAC Forecast | `DISABLED_CANONICAL_INPUT_NOT_GOVERNED` |

Eight plus one plus one, union of exactly ten, no overlap between the three sets.

### 2.2 The resolved total

| Reason | Count |
|---|---|
| 1, outside the unit of analysis | 5 |
| 2, already disabled | 10 |
| 3, input structure has never existed | 16 |
| 4, duplicate primitive source | 7 |
| **Total** | **38** |

**Registered count: 101 -> 63.** Group A 53 -> 44, Group B 36 -> 12, Group C 7 -> 7,
Group D 5 -> 0. Derived from the live registry, matching the expected figure, so stop condition
15.1 did not fire.

The full per-module table with each module's single assigned reason and every reason it also met
is in `MODULE_RETIREMENT_DECISIONS.md` section 3. Modules that met more than one reason:

| Module | Assigned | Also met |
|---|---|---|
| `D1.2`, `D1.4`, `D1.5` | 1 | 4 |
| `B2.7`, `B2.20` | 2 | 3 |
| `B2.9` | 2 | 3 and 4 |
| `B4.1`, `B4.6` | 2 | 4 |
| `B2.19` | 3 | 4 |

### 2.3 The prompt's internal inconsistency, resolved

Section 10.2 says "`B2.19` retires under reason 4 in this run". Section 8's reason 3 covers every
B2 module except the three already disabled and except `B2.18` — which includes `B2.19`. Under
section 2's lowest-numbered rule, **`B2.19` takes reason 3.**

It is recorded under reason 3 with reason 4 also met, and the CSV supports the additional reason
(`distinct_analytical_function = NO`, shares `decisionAlternatives` with `B2.18`). The total of 38
is unaffected, since `B2.19` retires under either reading.

### 2.4 Reason 4 verified against the CSV before retiring

All seven checked individually against `code_audit/run36_parsimony_reconciliation.csv`. Each shows
`SHARED_GOVERNED_STRUCTURE (same primitive source object)`, names exactly the partner section 8
names, and carries `distinct_analytical_function = NO`. **The CSV supported every one, so stop
condition 15.2 did not fire.**

Run 36's headline figures were also re-derived and match section 3 exactly: 100 targets,
75 NONE / 19 shared / 5 identical / 1 subset, 17 marked NO.

---

## 3. Prose locations where the count was corrected

Committed as `5282d72`, **before** the retirement, so history shows 100 -> 101 and 52 -> 53
corrected first and then 101 -> 63 by the retirement. The two are not conflated.

**Changed:**

| Location | Was | Now |
|---|---|---|
| `NAMING_AUTHORITY.md` section 4, heading line | "**100 distinct computations**" | "**101 registered modules**" |
| `NAMING_AUTHORITY.md` section 4, table row A | 52 | 53 |
| `NAMING_AUTHORITY.md` section 4, following paragraph | "it is 100 registry-computed modules (Group A 52 of them)" | rewritten to state which population each figure counts |
| `NAMING_AUTHORITY.md` section 4, closing paragraph | "the count becomes 101" | disambiguated to "the computed count becomes 101" |
| `assets/js/detail.js:19` | "Group A 52 modules" | "Group A 53 modules" (comment only) |

Edited in place, per the owner's ruling against a second versioned authority file. Git history is
the record.

**Examined and deliberately NOT changed, with the reason.** Reporting these matters as much as
reporting the changes, because most of them are not wrong:

| Location | Why it was left |
|---|---|
| `README.md:37` | "100 distinct computations ... The count excludes the document risk score". Counts the server-computed set and says so. Correct. |
| `GROUP_ASSIGNMENT.md` | Its counts are the server-registered set (`VALIDATED` + `PORTFOLIO_VALIDATED` = 100), and its generated `group-assignment` block is machine-checked by `test_group_assignment.py`. Line 54 already states "Group A's full roster is 53 named entries, not 52." Correct as written. |
| `assets/js/knowledge.js:554` and `:600`, `index.html:941` | Already state both figures correctly: "101 registered ... the analytical server computes 100 of the 101". These are the exemplary statements of the distinction. |
| `assets/js/simulations.js:2382` | "the other 100 modules" — correct at a registry of 101. |
| `assets/js/ds_defensibility_data.js:2,13` and `knowledge.js:2481` | Generated PCEIF-era content that `NAMING_AUTHORITY.md` already flags as stale. Editing generated text without its generator would deepen the drift. **Recorded as an open item.** |
| `T6_HANDOFF.md` (8825-8864), all `REPORT_*.md`, `remediation_*.md` | Dated historical findings. Rewriting a past finding to match present state is falsification; git history is the record. |

**The substance of the correction.** Both populations are real and differ by exactly one module.
`A4.1` Document Risk Score holds a registry row — so it counts in the 101 — but is supplied by the
extraction model rather than computed, and is the single member of `unported_modules()`. The
defect was that `NAMING_AUTHORITY.md`'s table is headed "the analytical taxonomy", which is the
REGISTERED population, but carried the COMPUTED population's numbers.

---

## 4. The section 13 guarantees

Every check below was proved able to fail by injecting the fault, and the baseline was rechecked
after every injection. No check asserts against a copy of the logic under test, and no generated
output validates itself against its own generator.

| # | Guarantee | Verdict | The injection that proved the check could fail |
|---|---|---|---|
| 13.1 | Registered count after retirement equals the figure resolved at step 0.4, derived from the registry and not from a constant | **VERIFIED** | Un-retired `B4.7` in the CSV: the derived count moved 63 -> 64. Restored; recheck 63. |
| 13.2 | `assets/js/taxonomy.js` and the live registry agree on the count after retirement, as they did before | **VERIFIED** | Two injections. Adding a phantom `A9.9` to taxonomy.js broke agreement (63 vs 64). Re-adding retired `B4.7` broke it again. Restored; recheck agrees at 63, symmetric difference empty. |
| 13.3 | No retained module's computed result changed | **VERIFIED** | Perturbed retained voting module `A1.7` by `tcpi + 0.001`. The comparator flagged 2 changes. The clean run flags 0. |
| 13.4 | A retired module is unreachable on every path | **VERIFIED with one documented exception** | See 4.1 below. |
| 13.5 | Runtime lookups do not fail for any remaining registered module | **VERIFIED** | All 63 exercised. The only lookup refusal is `A4.1`, and it is **pre-existing**: the same refusal was reproduced at the `f461630` baseline. Not a retirement regression. |
| 13.6 | The voting count is still exactly 2, `A1.7` and `A1.8` | **VERIFIED** | Set equality against `{A1.7, A1.8}`; both confirmed still registered. |
| 13.7 | Group C still does not contribute to project status | **VERIFIED** | `contributes_to_project_status` returns False for C and True for A and B, so the predicate discriminates rather than always returning one answer. |
| 13.8 | All four B1 modules remain reachable from `research_export.py` | **VERIFIED** | All four still named at `research_export.py:350`, all four in the registry, `run_module()` accepts all four. Stop conditions 15.4 and 15.9 did not fire for B1. |
| 13.9 | The successor freeze gate passes in full | **NOT MET** | Not applicable: the freeze was not taken. 73 of 188 suites fail. See section 8. |

### 4.1 Guarantee 13.4 in detail, including where it is not fully met

| Path | Verdict |
|---|---|
| Registry lookup | **VERIFIED.** None of the 38 is in `registry_index()`. |
| `run_module()` | **VERIFIED.** All 38 raise `MissingModuleError`. The control discriminates: retained `A1.7` does not raise. |
| The rollup | **VERIFIED.** `run_all()` enumerates `available_modules()`, now the intersection of `VALIDATED` with the registry, so no retired module is ever dispatched. Census confirms 59 abstained + 3 computed = 62 of 63, with `A4.1` unported. |
| The export | **VERIFIED.** `research_export.py` receives computed results; it does not enumerate the registry. A retired module produces no row. Its appearances in that file are keyed annotation mirrors consulted via `.get()` / `in`, which become dead keys, not reads. |
| The browser taxonomy | **VERIFIED.** Neither `taxonomy.js` nor `categories.js` contains any of the 38; both derive 63. |
| **Group D via the portfolio health path** | **NOT MET.** `canonical_v8.compute_portfolio_health` maps PH.1-PH.5 onto `D1.1`-`D1.5` internally and still computes for the Portfolio Health card. See section 7.1. |

### 4.2 Stop condition 15.9, checked before any module was retired

Every one of the 38 identifiers was grepped against `research_export.py`, the brief and decision
generation path, and the client decision card and courses of action, **before** the retirement was
applied. Many hits were found, and every one was read rather than counted.

**No retired module's OUTPUT is read by the research export, the Executive Brief, the Governance
Decision card, or the courses of action.** All hits are one of three kinds:

1. **Keyed annotation mirrors** in `research_export.py` (`_RUN1_DISABLED`, `_RUN4_BAND_SOURCES`,
   `_RUN1_PROXY_QUALIFIERS`, `_RUN3_NEWLY_WIRED`) consulted only when a row already exists.
2. **Implementation dispatch tables** (`models_cat10.py`, `models_gov.py`) that are never reached
   because dispatch goes through the registry.
3. **Client name and taxonomy tables** (`categories.js`, `decision-ui.js`), which are data.

One genuine cross-module read exists at `registry.py:658` — `B1.1`'s decision snapshot and a
`signal_array` of already-computed results feed the nested-input adapter. `B1.1` is retained, and
the census proves the array's contents did not change, since the only computing modules are
`A1.2`, `A1.7` and `A1.8` and none is retired. **Stop condition 15.9 did not fire.**

---

## 5. The before-and-after census

Captured **before any change** over three fixed signal-input cases and byte-compared afterwards,
rather than compared against a remembered figure.

| | Registered | Case A | Case B | Case EMPTY |
|---|---|---|---|---|
| Before | 101 | 3 computed, 92 abstained, **Amber** | 3 computed, 92 abstained, **Green** | 0 computed, 95 abstained, **None** |
| After | 63 | 3 computed, 59 abstained, **Amber** | 3 computed, 59 abstained, **Green** | 0 computed, 62 abstained, **None** |

**Retained modules whose result changed: ZERO.** Every retained module's payload is byte-identical
before and after, in both the computed and the abstained collections. Project status is unchanged
in all three cases.

The registered set lost exactly the 38 and gained nothing. The only other difference anywhere in
the census is the `evidence_qualification.missing_required_inputs` roster, which shrank from 76 to
53 (and 79 to 56 on the empty case) — and it was verified mechanically that the after-set equals
the before-set **minus exactly the 38**, with no other member added or removed. That is a roster
of module ids, not a computed result.

**Stop condition 15.3 did not fire.**

---

## 6. B4.4's current label

Section 9.2 required reading the live label and correcting it **only if it is actually wrong**.

**It is not wrong. Nothing was corrected.**

The live state, read from the code:

- `B4.4` has **no entry** in `TRUTHFUL_METHOD_LABELS`.
- `B4.4` has **no entry** in `STRUCTURAL_CLAIM_LIMITS`.
- `B4.4` has **no entry** in `registry.PROXY_QUALIFIERS`.

So the label `B4.4` presents is the registry's own canonical name, verbatim:

> **What-If Scenario Matrix**

with no proxy qualifier and no truthful-method override. `method_labels.py:223` explains why, and
Run 43 confirms the comment matches the code: Run 35's own closure removed the `B1.2` and `B4.4`
entries because "the proxy the label described no longer exists, so the label had become FALSE IN
THE OPPOSITE DIRECTION, advertising a weakness the code does not have", after Run 32 repointed
`B4.4` onto `models_cat10.run_B4_4` and the canonical v7 layer.

**The premise in the earlier instruction was stale, exactly as anticipated.** No judgement about
what the module claims was required, so **stop condition 15.5 did not fire.**

---

## 7. Incidental findings, unacted

### 7.1 Portfolio Health outlives its modules

Retiring Group D removes the portfolio-level modules from the registry and taxonomy, but the live
Portfolio Health card does not compute through those ids. It runs
`portfolio_health.compute_portfolio_health_snapshot` into `canonical_v8.compute_portfolio_health`,
which maps PH.1-PH.5 onto `D1.1`-`D1.5` internally. (`portfolio.compute_portfolio`, the v20 route
that does key off `PORTFOLIO_VALIDATED`, is already documented as preserved and unreachable.)

So the platform has now retired its portfolio-level modules while a portfolio-level card still
computes. **Not resolved, deliberately.** Resolving it in either direction changes a user-facing
surface, and section 5.4 forbids deciding that inside a run. **No control was added, moved or
removed**; the `D1` category container remains in the client taxonomy with an empty module list.
This is the one place guarantee 13.4 is not fully met, and it needs an owner decision.

### 7.2 The export's proxy-qualifier mirror has drifted by 29 entries

`registry.PROXY_QUALIFIERS` holds **1** entry. The export's deliberate mirror,
`research_export._RUN1_PROXY_QUALIFIERS`, holds **30**. Twenty-nine ids are in the mirror and not
in the registry — `B4.4` among them, whose qualifier **Run 32 explicitly withdrew**.

The export is committee-facing evidence, so on current code it can print a proxy qualifier the
platform has formally withdrawn. Found while checking the `B4.4` label, not by looking for it.
Unacted.

### 7.3 The PRJ-001 defects

None attempted, no cause inferred. The `detail.js:1521-1524` `Number(null)` candidate mechanism
for the `Document risk: 0.00 (Green)` defect is recorded as **UNCONFIRMED** and was neither tested
nor fixed. Listed in full in `MODULE_RETIREMENT_DECISIONS.md` section 7.1.

### 7.4 The freeze stamp path in the prompt is wrong

Section 6 says the live stamp is at `server/app/models.py:475`. It is at
`server/app/simulation/models.py:475`. `server/app/models.py` does not contain it.

---

## 8. The successor freeze, and why stop condition 15.8 fired

**The successor freeze `sim-2026.08-v28` was NOT minted. The live stamp remains
`sim-2026.08-v27`.** No gate row can therefore be reported green, because a freeze stamped without
the gates re-run is not a freeze, and the gates do not pass.

### 8.1 The measurement

Both figures produced with the repository's own `server/run_all_suites.sh`, which enforces the
canonical `RESULT:` line rule itself, so a suite that crashes cannot look clean.

| | Suites | Checks | Verdict |
|---|---|---|---|
| Baseline at `f461630`, re-run in a clean worktree | 188 | **14176/14176** | **ALL SUITES GREEN** |
| After the retirement | 188 | 9671/9817 | **73 SUITES FAILING** |

The baseline was reproduced rather than taken on trust, and matches the recorded 188 / 14176
exactly. Every failure is therefore attributable to this run.

Of the 73: **35 crash with no canonical RESULT line, 38 run but fail checks.** The dominant cause
is uniform — **56 `MissingModuleError` occurrences**.

### 8.2 The two failure classes

**Class 1, the freeze guards (expected, and designed for).** `test_run38_frozen_immutability.py`,
`test_run39_frozen_immutability.py`, `test_run37_freeze_gate.py`, `test_run41_preservation.py` and
the version-boundary suites fail because this run modified frozen-surface files. This class is
exactly what section 6's successor-freeze procedure exists to resolve, by naming
`assets/js/categories.js`, `assets/js/taxonomy.js`, `assets/js/detail.js`,
`p0-baseline/module_renumbering_map.csv` and `server/app/simulation/registry.py` in a v28
authorised change set. **This class alone would not have stopped the run.**

**Class 2, the per-module scientific audit suites (what actually stopped it).** The known-answer,
oracle, fault-campaign and per-module evidence suites enumerate the module population and call
`run_module()` on each id. Guarantee 13.4 requires that a retired module be unreachable through
`run_module()`, and it is. Those suites therefore crash by design.

### 8.3 Why this is a stop condition and not something to fix

Bringing class 2 green means deleting or skipping roughly **4,359 checks across 73 suites**
(14176 - 9817). Section 6.1 is unambiguous:

> Do not disable, weaken, or bypass the guard. Add to the authorised set; never remove or widen a
> check.

Deleting four thousand checks is removing checks. The only alternative — leaving `run_module()`
able to compute retired modules so the audit suites keep passing — violates guarantee 13.4, which
is equally an owner-mandated check.

**Both available routes weaken something the owner mandated.** That is precisely stop condition
15.8, so the run stopped, the freeze was not taken, and the branch was left unmerged.

### 8.4 The decision the owner now has to make

Neither option can be chosen inside a run, because both change what the instrument's qualification
evidence consists of.

**Option A — retire from the taxonomy only.** Relax guarantee 13.4 so `run_module()` still
computes a retired module when called explicitly by id, while the module stays absent from the
registry enumeration, the rollup, the export, the ledger and the browser taxonomy. The defence
burden the retirement exists to remove is removed, because the committee-facing surfaces are the
taxonomy and the ledger. All 14176 checks survive. The cost is that "unreachable on every path"
becomes "absent from every enumerated path", which is a weaker and more careful claim.

**Option B — retire fully and re-baseline the qualification evidence.** Accept that the audit
suites for 38 retired modules are themselves retired, with their own authorisation, their own
record of which checks were withdrawn and why, and a new baseline check count. This is a larger
piece of work than Run 43 and needs to be commissioned as such, not absorbed.

My reading, offered as input and not as a decision: **Option A matches the stated purpose.**
Section 1 says the burden is the justification the owner must deliver under hostile questioning,
and that burden lives on the taxonomy and the ledger, not on `run_module()`. Option B destroys
several thousand checks of qualification evidence to satisfy a reachability claim stronger than
the purpose requires.

---

## 9. Audit artifacts the suites rewrote, and were restored

The Run 41A finding reproduced exactly. Running the suites caused the suites to rewrite committed
audit artifacts. **14 files**, all restored with `git checkout -- code_audit/`, and **none was
committed as if it were a change this run made.** `git status` was checked before every commit.

`code_audit/run9_abstention_results.csv`, `run9_alias_overlay_verification.csv`,
`run9_fixture_import_results.csv`, `run9_known_answer_results.csv`,
`run9_no_operational_effect.csv`, `run9_validator_gap_recomputations.csv`,
`run10_no_operational_effect.csv`, `run20_cycle12_guard_nonvacuity.csv`,
`run20_cycle12_lineage_campaign.csv`, `run30_closure_fault_injection.csv`,
`run34_count_fault_injection_results.csv`, `run38_controlled_stimulus_execution_order.csv`,
`run38_lock_integrity.csv`, `run38_participant_state_machine.csv`.

---

## 10. What the next session needs

1. **The section 8.4 decision, Option A or Option B.** Nothing else in this run can be finished
   until it is made. This is the blocking item.
2. **The Portfolio Health coherence decision at 7.1.** Group D is retired; a portfolio-level card
   still computes. Either gate the snapshot on the registry or state plainly that portfolio health
   is a capability outside the module taxonomy. Do not decide it inside a run.
3. **The successor freeze.** Once 8.4 is settled and the gates are green, mint `sim-2026.08-v28`
   with an authorised change set naming `assets/js/categories.js`, `assets/js/taxonomy.js`,
   `assets/js/detail.js`, `p0-baseline/module_renumbering_map.csv` and
   `server/app/simulation/registry.py`. Add to the set; never widen a check.
4. **The export proxy-qualifier mirror at 7.2**, 29 entries adrift, on a committee-facing surface.
5. This branch, `claude/run43-module-retirement`, is unmerged and its two implementing commits are
   sound. It does not need redoing; it needs the decision at 8.4.

## 11. Constraints observed

- Nothing outside the repository root was deleted or moved.
- `DATABASE_URL` was pointed only at throwaway SQLite files under the scratchpad and the runner's
  own `mktemp` directory. Production Postgres was never referenced.
- The PRJ-001 document set and every synthetic corpus were untouched.
- **No user-facing control was added, moved or removed.**
- No `preview_start` and no browser session, so no `DEng\Demo` exposure.
