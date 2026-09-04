# Run 135C — Group 6, the tooling. Classification first, then repair.

Agent C of four. Branch `worktree-agent-af3ef56c9dde2a90e`.
Starting commit `6d9899f`. Ending commit `7d9b87f` before this report. Tree clean.
Migration head `0033_recognition_matches`, applied only to a throwaway SQLite file under the
scratchpad. Production Postgres was never contacted. No model key exists in this environment and
nothing here calls or simulates a model. `SIMULATION_VERSION` did not move: no file under
`server/app/` is changed by this branch.

---

## The four R4 counts, and the coverage figure

`server/tools/TOOLS_CLASSIFICATION.csv`, produced by `server/tools/run135c_classify_tooling.py`,
which carries the decision order in its docstring and writes the applied rule into every row's
`reason`. Re-running the script reproduces the counts; they are not taken on trust.

| kind | count | counts toward qualification coverage |
|---|---:|---|
| **active** — asserts on behaviour the platform has today | **237** | yes |
| **reader** — reads a sealed artefact or measurement and reports it | **102** | no, excluded in the CSV |
| **migration** — one-time run-scoped builder, seeder, exporter | **137** | no, excluded in the CSV |
| **retired** — its subject is a feature that no longer exists | **24** | no, retired explicitly |
| total | **500** | 492 in `server/tools`, 8 in `server/tests` |

### The coverage figure for the ACTIVE set alone

The hunt's 933 unreachable checks is a figure over the whole fleet. Split by kind, over the 237
active qualification tests only:

| | scripts | share |
|---|---:|---:|
| exit 0 | 80 | 33.8% |
| complete and report their own failures | 63 | 26.6% |
| **crash before reaching their own verdict** | **66** | **27.8%** |
| exceeded the 120 s cap, unmeasured | 28 | 11.8% |
| **run to completion** | **143** | **60.3%** |

**5634 of 5957 checks pass (94.6%) in the active scripts that reach a `RESULT` line.** The checks
inside the 66 crashers are unreachable and the 28 capped scripts are unmeasured, so the honest
statement is: three in five active qualification tests reach a verdict, and of the checks that
are reached, one in twenty is red.

Crash causes in the active set, matching the hunt's diagnosis: `KeyError` on a retired id in a
hardcoded dict (20), `MissingModuleError` on a retired id (17), `ModuleNotFoundError` and
`ImportError` from the Run 97 portfolio removal (14), `IndexError` (5), the remainder browser and
harness failures.

### The first fleet measurement was wrong, and this matters for anyone repeating it

With `DATABASE_URL` pointed at `sqlite+aiosqlite:///`, **133 scripts died in
`sqlalchemy.exc.MissingGreenlet`**. The cause is not in the scripts. `server/alembic/env.py` drives
a **synchronous** `engine_from_config`, and many tools run `alembic upgrade head` at startup; an
async driver cannot serve that, while the application needs one. Under Postgres, psycopg 3 serves
both and the conflict is invisible. Under SQLite the same URL cannot satisfy both, and the whole
fleet reads as broken.

Every figure above is from a second full run under a plain `sqlite:///` URL: 497 scripts, 120 s
cap, six at a time, each against its own copy of a migrated database.

**Reported as a finding in its own right, not fixed:** `server/alembic/env.py` is not in this
agent's scope.

---

## Disposition table

| finding | disposition | attempts |
|---|---|---:|
| H10 — 53 of 244 crash, 933 checks unreachable | **RESOLVED for classification, retirement and the required check; the 66 active crashers are NOT REACHED as repairs** | 1 |
| H9 — simulation-guarantee suite dead since Run 97 | **RESOLVED** — 36/36 | 4 |
| H8 — A1.7 boundary proof red since Run 114 | **RESOLVED** — 10/15 to 15/15 | 2 |
| M6 + M7 + L2 — vacuous oracle independence and re-execution | **RESOLVED** | 1 |
| M8 — census checks pass on a card that did not render | **RESOLVED** | 1 |
| M9 + L7 — literal tautologies on population coverage | **RESOLVED** — M9 now fails, which is the finding | 2 |
| M10 — a fault no guard can see | **RESOLVED** — 14 fault classes, not 15 | 1 |
| M12 + L6 — launch gate never queries the database | **RESOLVED** | 1 |
| M14 — sealed evidence regenerates | **PARTIAL** — mechanism built, scope measured at 132, two manifests fixed, 130 NOT REACHED | 1 |
| S7 — a literal passing check in the export fixture | **RESOLVED** | 2 |
| S8 — timestamp equality true when both absent | **RESOLVED** | 1 |
| S9 — a missing required report reads as success | **RESOLVED** | 1 |
| L3 — always-true comparison | **RESOLVED** | 1 |
| L4 — a literal PASS inflating the count | **RESOLVED** | 1 |
| L5 — a count where neighbours assert identity | **RESOLVED** | 1 |
| `run18_production_hashes.py` re-baseline-or-retire | **RESOLVED** — split, decision recorded | 1 |
| `drive_run103_census.py:479` fail loudly | **RESOLVED** | 2 |
| M11, M13 — instances of H10 | **classified, not repaired** | — |

No finding reached the five-attempt cap. No finding went BLOCKED, though five decisions are
recorded at the end that the owner may wish to overturn.

---

## Per finding

### H10 — classify, retire, measure, and add the check

**Classification, committed before any repair** (`dfa87ad`), so the counts cannot be tuned by the
repairs that follow. Decision order, fixed and printed per row:

0. the Run 135C classification harness itself -> reader (it reports on the fleet, it does not
   qualify the platform)
1. name marks a one-time run-scoped builder / seeder / exporter -> migration
2. name marks a measurement, reconciliation or census over sealed artefacts -> reader
3. every simulation module id it references was removed at Run 96 or 97 per
   `tools/run96_removed.py`, **and** it does not complete when run -> retired
4. does not import `app.*` at all -> reader
5. imports `app.*` but asserts nothing -> migration
6. imports `app.*` and asserts -> active

**Two deliberate departures, both of which change the counts.**

*Naming a removed feature is not retirement.* `tools/test_simulation.py` imports
`PortfolioModuleError`, removed at `88e6ca0`, but 20 of its 23 checks are about live behaviour. It
is an active suite with a broken reference — that is H9 — not a retired artefact. Rule 3 requires
the module ids to be the script's whole subject.

*Nor is failing to complete, on its own.* Rule 3's second half keeps five scripts out of the
retired set that reference only removed ids but still exit 0: whatever ids they mention, they are
still measuring something.

**Retirement mechanism: a top-of-file guard, not a move.** Moving 24 files to a `retired/`
directory would rename paths that the freeze manifests, the production hash inventories and a
long series of committed reports all cite. The guard leaves the artefact where every record
already points and — unlike a relocation — **declares itself when executed**:

    RETIRED: <file> measures <ids>, removed at Run 96/97 (88e6ca0); excluded from
    qualification coverage by tools/TOOLS_CLASSIFICATION.csv

exiting 0. Each guard also quotes the exact error the script died with beforehand, so the record
of what broke is not lost. A fleet run now records a retirement where it recorded a crash.
Verified: all 24 exit 0 and print the line.

Readers and migration tools are marked in the CSV and excluded from coverage there. **Not one was
edited.**

**The check the order requires:** `server/tools/test_run135c_active_suite_completes.py`.

It fails when any script classified active crashes rather than completing, and deliberately does
**not** require them to pass. A red suite is a finding that belongs in a report; a crashed suite
is not a finding at all, because nobody knows what it would have said. A script the fleet did not
cover fails too — an active test nobody ran is indistinguishable in its consequences from one
that crashed. It reads a fleet run's exit codes and captured output by default, because executing
237 scripts takes hours; `--run` performs one.

Proof it can fail **and** can pass:

| evidence | result |
|---|---|
| the real fleet run | 1/2 — "94 crashed" (66 crashes + 28 timeouts) |
| the 80 active scripts that exited 0 | 2/2 |

so it is not a check that is merely stuck red.

**NOT REACHED:** repairing the 66 active crashers. That is the bulk of H10 and it is not done.
M11 (`test_run17_scientific_methods.py`, 214 checks dead) and M13
(`tests/test_run34_holdout_provenance.py`, 27 of 41 dead) are both classified **active** and both
still crash — the latter on `ImportError: cannot import name 'portfolio_health'`. They are named
in the CSV with their exit code and first error and are not repaired.

### H9 — the canonical simulation-guarantee suite, 36/36

Dead since Run 97; it died on line 13 before the first check. Determinism, retirement bookkeeping
and `contributes_to_project_status` had been unqualified for 74 commits. Repairing the import was
one line. Running the file then exposed **five further defects, none suppressed**:

1. `unported_modules() == ["A4.1"]` — A4.1 was itself removed, so nothing is unported.
2. `len(VALIDATED) + len(PORTFOLIO_VALIDATED) == 100` and the "101 declared" arithmetic behind it.
   The registry CSV carries 33 rows today, because Runs 96 and 97 deleted rows rather than marking
   them retired.
3. **The CSV retirement read looked in the wrong column.** It searched `notes` for "RETIRED"; the
   CSV marks a retirement in `new_id`. The retired set was therefore silently **empty**, which
   made the two checks under it compare `available_modules()` against the whole of `VALIDATED` —
   weaker than written, and invisible while the file did not run.
4. `check(all(m["group"] != "D" ...))` raised `KeyError` the moment the file executed: published
   module rows carry no `group` key.
5. Guarantee 5 ("Group D is unreachable from a single-project path") is restated as the stronger
   fact that Group D is not reachable from any path, because it is not in the registry at all.

Expectations for 1, 2 and 5 come from `tools/run96_removed.py` — the record of the removal, which
does not change when the registry changes — and not from the functions under test.

**One check was replaced rather than repaired, and it is called out because it is the one
judgement call in this finding.** `check(len(_RETIRED_FROM_CSV) > 0, ...)` was failing. Requiring
a positive count of retirements is not a platform guarantee — a registry with nothing retired is a
legitimate state. Its *intent* was that the retired set be derived from the CSV rather than
imported from the code it audits, and that intent is now carried by a two-way equality against
`registry.retired_modules()`, which is a real assertion. This is not suppression of a failing
check; it is the replacement of a wrong one. It is stated plainly so the owner can disagree.

Attempts: 4. Proof it can fail: appending a `D1.1` row to
`p0-baseline/module_renumbering_map.csv` takes the suite 36/36 to 30/36, all six failures naming
D1.1. Row removed, 36/36 restored.

### H8 — the A1.7 boundary proof, 10/15 to 15/15

Expectations were hardcoded against the pre-Run-114 three-rung ladder.

Under R2 the rungs are transcribed from the Run 114 report committed at `fc9d60c`, section 6,
"A1.7 TCPI — the owner's numbers, taken as given":

    Green   <= 1.00
    Yellow  > 1.00 to 1.05
    Amber   > 1.05 to 1.10
    Red     > 1.10

with that section's per-edge provenance — green 1.00 CODIFIED, yellow 1.05 OWNER-CALIBRATED,
amber 1.10 CONVENTION. Each rung carries the citation as a string beside it in
`RUN114_TCPI_RUNGS`, and `band_from_run114_tcpi()` is the only source of an expected band in the
file. **Nothing is read from `models_evm.py`, from `_TCPI_OWNER_YELLOW`, or from the module's
output.** That is what R2 requires, and it is what makes these expectations survive agent A's
change to the VAC computation path by construction.

g01, g03, g04 and g09 repointed. g14's subject B4.4 was removed at Run 96/97, so
`registry_name("B4.4")` is None: the guard is **not** narrowed to silence — a module that has left
the registry is now required to have left `assets/js/categories.js` and `assets/js/taxonomy.js`
too, which is the stronger condition.

**The CSV re-baselined deliberately.** `code_audit/run35_v22_v23_voter_execution_proof.csv`
recorded `tcpi=1.0001 band=Amber`, a band the instrument no longer emits. Its generator is
`server/tests/test_run35_closure_version_boundary.py`, whose own line 203 carried the same stale
"Amber", so the generator was repaired first — again from the Run 114 order, and without weakening
what the check is for: v22 must still answer Green where the full-precision index is above 1.00.
Only the name of the adverse band changes. That suite goes 28/29 to 29/29 and the CSV is
regenerated from it; one line differs.

Proof it can fail: collapsing `_TCPI_OWNER_YELLOW` from 1.05 to 1.00 takes the suite 15/15 to
11/15 with g01, g03, g04 and g09 all reporting Amber where the order says Yellow. `models_evm.py`
restored, `__pycache__` cleared, 15/15 confirmed, `git status` shows `server/app` clean.

### M6 + M7 + L2 — every one of twenty-one modules was proved consistent vacuously

`tools/run19_prior_21_consistency.py`.

**M6.** Oracle independence was a whole-file substring search. Now scoped to the module's own
block, delimited by the prior suite's `mid = "<id>"` markers; a module whose marker is absent is
reported rather than searched file-wide.

**M7.** Re-execution was `Path.exists()`. The suite is now executed and its verdict read.

**L2.** `return 0` regardless of what was found. Returns 1 when contradictions or incomplete
evidence exist — confirmed, the run exits 1 today where it exited 0.

**What re-running exposes. Every state changes: 21 CONSISTENT to 0 CONSISTENT, 21
INCOMPLETE_EVIDENCE.**

* The prior suite does not re-execute at all. It dies on
  `ModuleNotFoundError: No module named 'app.simulation.portfolio'` and prints no verdict line.
  All 21 rows carried the note "the prior suite re-executed green". **It had never been executed.**
* The order asked what 1.9 and 1.11 become: both **INCOMPLETE_EVIDENCE**, both now reporting that
  their own block does not call the independent oracle. **Two more do the same, which the finding
  did not predict: 1.5 and 6.4.**
* **PH.1 through PH.5 carry no block marker at all** — five modules whose oracle independence was
  never locatable, now reported as five rather than assumed.

`code_audit/run19_prior_21_spec_consistency.csv` is re-baselined: 21 rows change state.

Proof it can fail, using the finding's own sandbox fault: appending a trailing comment mentioning
`O.worst_n_of_m` flipped 6.4 INCOMPLETE to CONSISTENT before the fix; after it, 6.4 stays
INCOMPLETE. Positive control: 1.7 and 1.8, whose oracle calls genuinely sit in their own blocks,
still satisfy oracle independence.

### M8 — three census drivers guarded

The Run 106 guard copied into `drive_run101_card.py`, `drive_run102_card.py`,
`drive_run103_census.py`, reporting the raw value of `out["text"]` so `None` is distinguishable
from an empty render. Proof it can fail: forcing `out["text"] = None` makes the guard FAIL and —
this *is* the finding — **one of the two previously failing terminal checks flips to PASS on the
empty string**, so the total stays 5/7 while the card is not there at all.

### M9 + L7 — `or True` removed, and M9 fails

`drive_run106.py:383` was the only check standing over the population coverage of the driver that
sets the weighted project status. Removing `or True` exposes a failure, which is the finding:

**14 of the 31 modules in service are not reached on that corpus** — A1.11, A1.2, A1.5, A1.6,
A1.7, A1.8, A1.9, A2.1, A2.12, A2.7, A2.8, A2.9, B1.1, C1.5. RESULT 38/50 to 37/50; exactly one
check moves from vacuous pass to fail, and it is not suppressed.

`drive_run49_browser.py:317` and `drive_run57_reset_merge.py:458` both now assert and both pass.

**Eight further `or True` instances exist beyond the three named, and are not fixed:**
`test_run13_module_evidence.py:476` and `:525`, `test_run17_scientific_methods.py:1374`,
`test_run19_category_4.py:398`, `test_run20_p0b_evidence_domain.py:331`,
`test_run38_readiness.py:775`, `test_run39_launch_gate.py:266`,
`test_training_portfolio_isolation.py:180`.

### M10 — the dead fault class removed, and the decision

Fault 2's guard body was retired by Run 59 (`RETIRED_RUN59_DOCUMENT_WORDING = True`) under the
owner's 2026-08-25 ruling that no markdown document carries authority. The fault landed in the
bytes and nothing could see it; the CSV recorded RED, YES, COUNTED for a guard that never ran.

**Removed rather than restored.** Restoring the guard would reverse an owner's standing ruling on
documentation authority, which a fault campaign is not entitled to do on its own initiative. What
the fault reached for is not lost: the placeholder's actual occurrences are counted against the
tree in section 1 of the guard file, which Run 59 left untouched. **Fourteen fault classes, not
fifteen.** If the owner wants the guard back, that is a ruling on documentation authority and it
restores this fault class with it.

`research/freeze/run37_documentation_scope_campaign.csv` re-baselined by re-running the campaign
against a clean tree; the fault-2 row is gone and the three survivors are unchanged.

### M12 + L6 — the launch gate queries the database

Reproduced exactly as stated: `main_study_row_count` called with a session whose `.execute` raises
returned `(0, [])`. The query now runs first and unconditionally over every participant carrying
decisions, and MAIN_STUDY membership is decided per row by `DC.classify`. The same raising session
now raises. L6: a zero-decision participant is reported with `observations` 0 and `complete_36`
False instead of being dropped from the set.

`tools/test_run39_launch_gate.py` 98/100 before and after, same two failures both times —
`identity: simulation expected 'sim-2026.08-v41' observed 'sim-2026.09-v68'` and the drift check
that reads it. Pre-existing, belonging to the frozen launch identity.

### S7, S8, S9 — three vacuous checks

**S7.** `check(True, "two participants completed two periods each")` stood for twenty seeding calls
whose responses were never examined. Seeding now goes through `seed()`, which asserts each
response, and the completion claim is derived from stored decision rows. Proof: suppressing the
period-one `researchadvance` makes the seed assert fire loudly where the old form stayed green.
77/77 both before and after — the difference is that the claim is now true for a reason.

**S8.** `None == None` was true. Both timestamps must now be non-empty before comparison. Proof:
deleting both keys gives FAIL and 59/60 where the old form passed.

**S9.** A missing required report returned True. It is now a FAILURE with the reason and search
root named — not a skip, because the report is required by that guard, so "absent" is a defect in
the evidence set. Proof: moving the report aside gives 23/30. The six standing failures in that
suite (faults 11-15 and 29, on B2.7, B2.9, B2.20, A3.4, A3.8) are pre-existing H10 instances.

**For the queued consolidation run:** after this fix a reroute of that glob that finds nothing
fails loudly instead of passing silently.

### L3, L4, L5

**L3.** `x == (x or None)` replaced by the comparison it was evidently meant to make. Proof:
injecting `C1.5` into the project status turns it FAIL.

**L4.** A literal PASS removed rather than given an invented expectation — deciding what an item
with no stated criticality should band to is a ruling the file cannot make, and deriving one from
the function would breach R2. The observation is printed as a NOTE. 89/94 to 88/93: the count is
inflated by exactly one, as the finding says.

**L5.** `len(CORE_VOTING_MODULES) == 2` sat beneath `set(...) == {"A1.7","A1.8"}`. A count beside
an identity cannot fail unless the identity has already failed. Removed.

### `run18_production_hashes.py` — the decision

Reproduced: the freeze is reported broken by 43 added, 3 removed, 61 changed. Permanently red.

**Neither offered option on its own.** Re-baselining blesses whatever is in the tree today and
silently re-arms a gate nobody watches. Retiring the whole script discards three registry
invariants that are live facts and all pass.

**Split.** The freeze comparison is retired — Run 18's audit phase ended and roughly 117 runs of
authorised change have happened since, so comparing today's bytes to it measures the passage of
time. It is opt-in behind `--verify-freeze`; `--write` still re-baselines deliberately. The
registry invariants always run. Default 5/5 with the retirement printed; `--verify-freeze` 7/10.

Proof it can fail: adding `A3.4` to `CORE_VOTING_MODULES` takes the default run 5/5 to 3/5.
Restored, `__pycache__` cleared, `server/app` clean.

### `drive_run103_census.py:479` — fail loudly

`str.index` does raise, but with no indication of which marker moved or which file was read, and
it is silent about three ways this succeeds wrongly: reversed markers (empty slice, exec'd
silently, `NameError` hundreds of lines later), a duplicated marker (wrong occurrence), and a
slice that defines nothing or defines it empty (every imperative check passes vacuously — the
same class of defect as M8, 200 lines further down the same file). All are checked and named, and
the number of patterns read is printed.

**Proved in isolation, and why it had to be.** `drive_run103_census.py:19` hardcodes
`HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools")` — the **main checkout** — so a
fault injected into this worktree's `drive_run98.py` cannot reach it. The guard block was lifted
verbatim, pointed at a temporary copy, and each mode injected:

| case | exit | message |
|---|---:|---|
| control | 0 | read 5 imperative patterns ... |
| start marker renamed | 1 | the marker ... appears 0 times in ... |
| end marker renamed | 1 | the marker ... appears 0 times in ... |
| markers reordered | 1 | ... no longer precedes ... the slice between them is empty |
| start marker duplicated | 1 | the marker ... appears 2 times in ... |
| patterns emptied | 1 | ... defined IMPERATIVE_PATTERNS as empty ... pass vacuously |

### M14 — PARTIAL

**The scope is five times what the hunt saw: 132, not 24.** Two full fleet runs plus the tree
snapshot `drive_run57_reset_merge.py` takes of its own accord give 132 committed artefacts
rewritten simply by executing the tooling — 33 `code_audit` CSVs, 12 `code_audit` PNGs, 30
`research/freeze` manifests and checksum records, the two study manifests, and one committed
REPORT markdown. Listed in
`code_audit/run135c_m14_artifacts_rewritten_by_running_the_fleet.txt`.

`server/tools/artifact_write.py` implements the rule once: scratch by default, `--write-artifact`
(or `RUN135_WRITE_ARTIFACT=1`) to overwrite, with the scratch root mirroring the repository layout
under `.artifact_scratch/` (gitignored). Retrofitted into the two study manifests, taken first
because both regenerate at a **newer identity than the one committed** — v68 against v25, v26
against v13 — so any casual run silently proposed a new launch identity. Both directions proved.

**NOT REACHED: the other 130 artefacts.** The remaining work is mechanical and now fully
specified — the list is committed, the helper exists, the change per generator is the three lines
applied here — but it is not done.

---

## New failures exposed by repairing dead suites

Every one is a finding, and none is suppressed.

1. **14 of 31 modules in service are not reached** by `drive_run106.py`'s corpus — the driver that
   sets the weighted project status (M9).
2. **The prior 21-module consistency evidence never existed.** 21 CONSISTENT to 21
   INCOMPLETE_EVIDENCE. `test_run17_scientific_methods.py` has never been re-executed; the note
   claiming it had was printed unconditionally (M7).
3. **1.5 and 6.4 join 1.9 and 1.11** as modules whose oracle call is not in their own block (M6).
4. **PH.1-PH.5 have no block marker** in the prior suite at all (M6).
5. **The registry CSV retirement convention moved from `notes` to `new_id`** and
   `test_simulation.py`'s read was silently returning an empty retired set, weakening two checks
   (H9).
6. **`run["modules"]` rows carry no `group` key** — a latent `KeyError` in `test_simulation.py`,
   unreachable since Run 97 (H9).
7. **A4.1 was removed**, so nothing is unported and the "unported module refuses to compute"
   guarantee had lost its subject (H9).
8. **`test_run39_launch_gate.py` fails on launch identity**: `sim-2026.08-v41` expected,
   `sim-2026.09-v68` observed. Pre-existing, unrelated to M12, and it means the frozen launch
   identity is stale against the running instrument.
9. **`test_run35_validation_governance.py` has six standing failures** on removed modules B2.7,
   B2.9, B2.20, A3.4, A3.8 — H10 instances inside a governance campaign.
10. **`server/alembic/env.py` drives a synchronous engine** while the app requires an async one, so
    a single `DATABASE_URL` cannot serve both under SQLite. 133 scripts read as broken because of
    it. Out of scope to fix here.
11. **30 scripts under `server/tools` hardcode `/home/user/LinPRojectRadar/server`** on `sys.path`.
    Run from a worktree they import the *main checkout's* application, so a worktree's changes are
    invisible to them and a fault injected in a worktree cannot be seen. This silently invalidates
    any per-branch measurement taken with them.
12. **`drive_run57_reset_merge.py` checks an old commit's client files into the working tree** and
    restores them at the end. If it is interrupted — it exceeded a 500 s cap here — the tree is
    left carrying `50dfb40`'s `radar.css`, `detail.js`, `ingest.js` and a modified
    `app/simulation/lineage.py`. Running the fleet against a tree with uncommitted work is unsafe.

---

## Which of my repaired suites assert on files agents A and D are changing

| suite | asserts on | risk at merge |
|---|---|---|
| `tools/test_run35_closure_voter_identities.py` | A1.7, A1.8, `models_evm` by name | **low by construction** — every expectation comes from the Run 114 order, not the function. Run 114's rungs do not move. It goes red only if a *band* moves, which the order forbids. |
| `tests/test_run35_closure_version_boundary.py` | `run_tcpi`, `run_vac`, `models_evm` | **medium** — it executes both v22 and today's module and compares. The *band* expectation is from Run 114 and will hold, but the recorded value strings in the regenerated CSV will move and it will need re-baselining again. |
| `tools/drive_run107.py` | `run_tcpi`, `run_vac`, A1.7, A1.8 | **medium** — five pre-existing failures already; A's change may move more. |
| `tools/drive_run115.py` | `documents.py` | **medium** — 34 pre-existing failures; D's `documents.py` changes may move them. |
| `tools/test_run35_validation_governance.py`, `tools/run18_production_hashes.py` | A1.7/A1.8 as *ids* only | **low** — registry membership, not computation. |
| `tools/test_simulation.py`, `tools/test_export.py`, `tools/test_decision_sequence.py`, `tools/run39_launch_gate.py`, `tools/drive_run10{1,2,3,6}*` | none of A's or D's files | **low** |

Expect the middle three to move at merge. That is expected and is not evidence the repairs failed.

---

## Iteration log

    finding | attempt | change made | proof result | suite | disposition
    R4/H10  | 1 | classifier written; static rules; committed CSV | 498 rows, 4 kinds | n/a | RESOLVED (step 0)
    R4/H10  | 1 | rule order corrected (name rules before subject rule) | build_* no longer read as retired | n/a | RESOLVED
    R4/H10  | 1 | fleet re-run under sqlite:/// after MissingGreenlet diagnosis | 133 false crashes removed | n/a | RESOLVED
    R4/H10  | 1 | retired rule gains "and does not complete" | retired 29 -> 24 | n/a | RESOLVED
    R4/H10  | 1 | 24 retirement guards inserted after docstring + __future__ | 24/24 exit 0 with RETIRED line | n/a | RESOLVED
    R4/H10  | 1 | test_run135c_active_suite_completes.py added | 1/2 real, 2/2 on clean subset | itself | RESOLVED
    H9      | 1 | drop PortfolioModuleError / PORTFOLIO_VALIDATED imports | file executes; 2 fails + 1 crash | 34/36 then KeyError | PARTIAL
    H9      | 2 | population re-derived from CSV; A4.1 expectation from run96_removed | 35/35 | 35/35 | PARTIAL
    H9      | 3 | Guarantee 5 restated; group looked up in registry not module row | KeyError gone | 35/35 | PARTIAL
    H9      | 4 | CSV retirement read fixed (new_id, not notes); >0 check replaced | 36/36 | 36/36 | RESOLVED
    H9      | - | fault: D1.1 row appended to registry CSV | 30/36, six failures name D1.1 | restored 36/36 | proof-can-fail
    H8      | 1 | RUN114_TCPI_RUNGS from fc9d60c s6; g01,g03,g04,g09 repointed | 14/15, only g14 red | 14/15 | PARTIAL
    H8      | 2 | g14 narrowed to modules in service + stronger absence condition | 15/15 | 15/15 | RESOLVED
    H8      | - | fault: _TCPI_OWNER_YELLOW 1.05 -> 1.00 | 11/15, four guards red | restored 15/15 | proof-can-fail
    H8      | 1 | generator test_run35_closure_version_boundary.py:203 repointed | 28/29 -> 29/29; CSV re-baselined | 29/29 | RESOLVED
    M6/M7/L2| 1 | block scoping, real execution, non-zero exit | 21 CONSISTENT -> 21 INCOMPLETE | exits 1 | RESOLVED
    M6      | - | fault: trailing comment naming O.worst_n_of_m | 6.4 stays INCOMPLETE | restored | proof-can-fail
    M8      | 1 | Run 106 guard copied into three drivers | 5/7, guard PASS | 5/7 | RESOLVED
    M8      | - | fault: out["text"] = None | guard FAIL; a terminal check FLIPS to PASS | restored | proof-can-fail
    M9/L7   | 1 | or True removed from three named checks | M9 fails: 14 modules not reached | 38/50 -> 37/50 | PARTIAL
    M9/L7   | 2 | re-applied after an over-broad git checkout reverted them | same | same | RESOLVED
    M10     | 1 | fault class 2 removed; campaign re-run on a clean tree | CSV loses one row; 3 survivors intact | 3 faults, all RED/YES | RESOLVED
    M12/L6  | 1 | query first, classify per row; zero-decision participants kept | raising session now raises | 98/100 unchanged | RESOLVED
    M14     | 1 | artifact_write.py; two manifests retrofitted; 132 measured | scratch by default, flag overwrites | n/a | PARTIAL
    S7      | 1 | seed() asserts responses; completion derived from Decision rows | AttributeError: no participant_id | crash | FAILED
    S7      | 2 | joined through Assignment.participant_id | 77/77 | 77/77 | RESOLVED
    S7      | - | fault: suppress period-one researchadvance | seed assert fires loudly | restored 77/77 | proof-can-fail
    S8      | 1 | require both timestamps non-empty before comparing | 60/60 | 60/60 | RESOLVED
    S8      | - | fault: delete both keys | FAIL, 59/60 (old form passed) | restored 60/60 | proof-can-fail
    S9      | 1 | missing required report returns False with the reason | 24/30 unchanged | 24/30 | RESOLVED
    S9      | - | fault: move the report aside | fault30 FAIL, 23/30 | restored 24/30 | proof-can-fail
    L3      | 1 | x == (x or None) replaced with a real comparison | PASS on real data | 22/34/56 unchanged | RESOLVED
    L3      | - | fault: inject C1.5 into project_status | FAIL | restored | proof-can-fail
    L4      | 1 | literal PASS removed, observation printed as NOTE | 89/94 -> 88/93 | 88/93 | RESOLVED
    L5      | 1 | redundant count removed; freeze comparison made opt-in | 5/5 default, 7/10 --verify-freeze | 5/5 | RESOLVED
    L5      | - | fault: A3.4 added to CORE_VOTING_MODULES | 3/5 | restored 5/5 | proof-can-fail
    :479    | 1 | four named guards around the marker slice | 5/7 + patterns-read line | 5/7 | PARTIAL
    :479    | 2 | proved in isolation (script hardcodes the main checkout) | 5 modes fail loudly, control passes | n/a | RESOLVED

**One process failure, recorded because it cost an attempt.** A `git checkout -- server/tools
server/tests` issued to undo a bad retirement-guard insertion also reverted three uncommitted
M9/L7 edits and the classifier refinements. They were re-applied and M9/L7 is logged at two
attempts for that reason. The lesson is the order's own rule: `git add` and `git checkout` by
explicit path.

---

## `git status --porcelain` before each commit

The tree was clean at `6d9899f`. Running the fleet dirties 132 artefacts (that *is* M14), so
before every commit the intended paths were staged explicitly and the rest reverted. Immediately
before each commit, `git status --porcelain` showed only these staged paths:

    dfa87ad  A  server/tools/TOOLS_CLASSIFICATION.csv
             A  server/tools/run135c_classify_tooling.py
             (68 M14-dirtied artefacts were present, unstaged, and reverted afterwards)
    0a77d9f  M  server/tools/test_simulation.py
    ae405f6  M  server/tools/drive_run115.py
    7d0b72b  M  server/tools/drive_run107.py
    92364c0  M  server/tools/test_export.py
    9bdd2a1  M  server/tools/test_decision_sequence.py
    489185d  M  server/tools/test_run35_validation_governance.py
    461ee8d  M  server/tools/run39_launch_gate.py
    d4a2357  M  server/tools/drive_run101_card.py
             M  server/tools/drive_run102_card.py
             M  server/tools/drive_run103_census.py
    4fd845a  M  server/tools/drive_run106.py
             M  server/tools/drive_run49_browser.py
             M  server/tools/drive_run57_reset_merge.py
    0093be4  M  server/tools/TOOLS_CLASSIFICATION.csv
             M  server/tools/run135c_classify_tooling.py
             A  server/tools/test_run135c_active_suite_completes.py
             M  the 24 retirement guards, each by explicit path
    1638e4f  M  server/tools/test_run35_closure_voter_identities.py
             M  server/tests/test_run35_closure_version_boundary.py
             M  code_audit/run35_v22_v23_voter_execution_proof.csv
    744fd15  M  server/tools/run19_prior_21_consistency.py
             M  code_audit/run19_prior_21_spec_consistency.csv
    a2df814  M  server/tools/run37_documentation_scope_campaign.py
             M  research/freeze/run37_documentation_scope_campaign.csv
    720c758  M  server/tools/run18_production_hashes.py
    34a4eb7  M  server/tools/drive_run103_census.py
    7d9b87f  M  .gitignore
             M  server/tools/run38_build_manifest.py
             M  server/tools/run39_build_launch_manifest.py
             A  code_audit/run135c_m14_artifacts_rewritten_by_running_the_fleet.txt
             A  server/tools/artifact_write.py

`git add -A` and `git add .` were never used. No push, no merge to main.

---

## Decisions the owner may want to make

None of these blocked the run; each is a judgement recorded so it can be overturned.

1. **M10.** Fault class 2 was removed rather than its guard restored, because restoring it would
   reverse Run 59's owner ruling that no markdown document carries authority. If that ruling is to
   change, the fault class comes back with it.
2. **`run18_production_hashes.py`.** Run 18's freeze comparison is retired rather than
   re-baselined. If the owner wants a live production freeze, it needs a new baseline commit and a
   stated end date, not a revival of Run 18's.
3. **H9.** `check(len(retired_from_csv) > 0)` was replaced rather than repaired, on the ground that
   a registry with nothing retired is legitimate.
4. **`server/alembic/env.py`** should take an async engine, or the tools should not run
   `alembic upgrade head`. Out of this agent's scope; it makes SQLite-based fleet measurement
   fragile.
5. **The 30 scripts hardcoding `/home/user/LinPRojectRadar/server`** should derive their root from
   `__file__`. Out of scope here because those files are being edited on other branches, but until
   it is done, no per-branch measurement taken with them means what it appears to mean.
