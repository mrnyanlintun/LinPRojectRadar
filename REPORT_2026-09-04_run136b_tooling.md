# Run 136 B — Group 3: the tooling Run 135 did not reach

Agent B, working directly on `main`. Scope: F9, F10, F11.
Files owned: `server/tools/`, `server/tests/`, `server/alembic/env.py`, `code_audit/`,
`research/freeze/`, `research/study_execution/`. `server/app/` was not touched — see BLOCKED.

Starting sha `e29fb2c` (Agent A's merge, stamp `sim-2026.09-v70`).
Ending sha: the commit carrying this report, which is `HEAD` on `main` when it lands; the last
code change before it is `8847d02`. A report cannot name its own hash, so the primary should read
it from `git log -1` rather than from this line.

---

## The coverage figure

| | complete | of which exit 0 | of which report failures | crash or time out |
|---|---|---|---|---|
| **Baseline** (clean worktree at `cd98235`, v69, before A's merge) | **149 / 237 (62.9%)** | 94 | 55 | **88** (77 crash, 11 timeout at 120s) |
| **After this run** (main, all commits below) | **155 / 237 (65.4%)** | 97 | 58 | **82** |

Both figures are taken by `tools/test_run135c_active_suite_completes.py --run --timeout 120`
against **one shared SQLite database**, which is what the baseline used. That matters: see
"the harness cause" below. Both were taken on `main`, never in a worktree, so the `sys.path`
constraint Run 135 recorded does not apply to either.

**Net: +6 complete, -6 crashing.** No script that completed at baseline crashes now — the
regression set is empty. The six that moved:

| script | baseline | after | why |
|---|---|---|---|
| `tools/test_run17_scientific_methods.py` | ModuleNotFoundError | **214/231** | F11 / M11 |
| `tests/test_run34_holdout_provenance.py` | ImportError | **41/41** | F11 / M13 |
| `tools/test_run32_client_authority.py` | ModuleNotFoundError | **18/18** | F9-c |
| `tools/test_run36_fault_guards.py` | ModuleNotFoundError | **34/41** | F9-c |
| `tools/test_run41_preservation.py` | ModuleNotFoundError | **29/33** | F9-c |
| `tools/drive_run75_empty_period.py` | timeout at 120s | completes | not attributable to a repair — a browser driver that fell the other side of the cap. Reported as measurement variance, not as a fix. |

So **five of the six are repairs and one is noise.** Pass rate where a verdict is reached is
reported per script; the fleet check deliberately does not aggregate it, because a red suite is a
finding and a crashed suite is not a finding at all.

**What the figure does not move, and why.** 82 still crash, and the two harness causes repaired
this run are the reason the number did not move further: the alembic fault fires only under an
async URL, which the fleet does not use, and the shared-database fault is repaired behind a switch
that is off by default so this figure stays comparable with its baseline. On the evidence in the
sample above, turning `--fresh-db` on would move a large share of the 17 auth-collision crashes
and probably more; that measurement belongs to the next run.

---

## The harness cause: Run 135 named the wrong one

Run 135 recorded `alembic/env.py`'s synchronous engine as the harness fault behind the crashes.
**It accounts for 0 of the 88.**

- It is real and it is fixed. Under `sqlite+aiosqlite://` or `postgresql+asyncpg://`,
  `run_migrations_online` built a synchronous engine and died with `MissingGreenlet` on its first
  connection. Reproduced, repaired, proven able to fail again (F9-a below).
- But the baseline ran under a plain `sqlite:///` URL, and **no script under `server/tools` or
  `server/tests` names an async driver** (`grep -rl aiosqlite` returns nothing). The fault cannot
  have fired in the run that produced the 88.

**The harness fault that does account for a large share is a different one.** `run_active` gave
all 237 scripts one shared database. Many drivers bootstrap "the" ResearchAdmin *by role* —
`select(Participant).where(Participant.role == "ResearchAdmin")` — reset that row's token, then
sign in with their *own hardcoded pseudonymous code*. That matches only while no earlier script
has created an admin. `a_researchlogin` checks the code after the token match and refuses the
pair, so the driver reads `session_token` / `access_token` off an error dict and dies with a
KeyError. **17 of the 88 crash exactly there.**

Measured, not assumed — five of the 88, re-run unchanged on a freshly migrated database each:

| script | shared database | own database |
|---|---|---|
| `tools/test_auth_session.py` | crash, `KeyError: 'session_token'` | **RESULT: 52/52** |
| `tools/test_run40_serve_content_security.py` | crash, `KeyError: 'session_token'` | **RESULT: 11/11** |
| `tools/test_run41_security_acceptance.py` | crash, `KeyError: 'session_token'` | **RESULT: 11/11** |
| `tools/drive_run21_participant.py` | crash, `KeyError: 'access_token'` | **RESULT: 73/77** |
| `tools/run41_repro_s1.py` | crash, `KeyError: 'session_token'` | still no RESULT |

Four of five complete with no edit to the script. `drive_run105.py` shows the same shape one step
further: it crashes on `KeyError: 'access_token'` in the shared run and, on its own database, gets
past login and runs on to a genuine defect (`KeyError: 'A2'` at line 227).

`--fresh-db DIR` is now available on the fleet check and is **off by default**, deliberately:
turning it on changes what the coverage figure measures, and a figure taken under a different
harness cannot be compared with the run before it. The next run should take one measurement each
way and then make it the default.

---

## The 88, bucketed by cause

Bucketed from the `.err` files of the baseline fleet, using the check's own definition of
"crashed" (exit non-zero with no RESULT line, or exit 124).

| bucket | count | what it is |
|---|---|---|
| `MissingModuleError` on a retired id | 20 | the registry no longer resolves an id the script dispatches |
| `KeyError` on retired id in a hardcoded dict | 11 | the same removals, reached through a literal map |
| `KeyError: 'access_token'` / `'session_token'` | 17 | **the shared-database collision above**, not a script fault |
| timeout at 120s | 11 | all eleven are browser drivers |
| `portfolio` / `portfolio_health` removed at Run 97 | 14 | import-time death |
| other | 15 | one each: IndexError, ConnectionRefused, assorted KeyErrors |

**45 of the 88 depend on a browser or a live application server** (they name `playwright`,
`sync_playwright`, a `BASE_URL`, or `127.0.0.1:`/`localhost:`); 31 of those use Playwright.
Playwright and its Chromium are installed and the drivers do start their own browser — headless
Chromium was observed running throughout the end-of-run fleet — so this is not a missing
dependency. It is a **cost**: those drivers are what makes the fleet take hours and what fills the
eleven-script timeout bucket at a 120s cap. The one script that needs a server it does not start,
`tools/run32_closure_browser_verification.py`, moved straight to `ConnectionRefusedError` once its
import crash was repaired. Both are environment facts rather than script faults, and together they
bound how much of the 88 any amount of script repair can reach. **They are reported, not
reclassified** — R4 says read the classification, and I have not moved a row.

---

## Findings

### F9-a — `alembic/env.py` drives a synchronous engine — **RESOLVED**, 1 attempt

*Files:* `server/alembic/env.py:19,49-88`. *Commit* `bca095a`.

Before: `DATABASE_URL=sqlite+aiosqlite:///... python -m alembic upgrade head` →
`sqlalchemy.exc.MissingGreenlet`. After: exits 0 to head `0033_recognition_matches`; a plain
`sqlite:///` URL still exits 0. The driver decides, via
`make_url(url).get_dialect().is_async`, with a substring fallback.

*Proof it can fail:* reverting the file brought `MissingGreenlet` straight back; restoring it
cleared it again.

*Share of the 88:* **zero**, as established above. Repaired on its own merits.

### F9-b — the shared-database collision — **RESOLVED as a harness switch**, 1 attempt

*File:* `server/tools/test_run135c_active_suite_completes.py`. *Commit* `8847d02`.

`--fresh-db DIR` migrates an empty SQLite database per script. Proof: `--run --limit 3 --fresh-db`
created one `.db` per script and reported 2 exit-0, 1 crashed; without it the same three share one
database as before. Off by default so this run's figure stays comparable with its baseline.

*Not fixed:* the ~36 scripts that select an admin by role rather than by their own code. That is
the script-side half of the same defect and is a clean, mechanical repair for the next run
(`select(...).where(Participant.pseudonymous_code == <the script's own code>)`).

### F9-c — `PORTFOLIO_VALIDATED` imported from a module Run 97 deleted — **RESOLVED**, 1 attempt

*Files:* new `server/tools/run97_removed_portfolio.py`; imports repointed in
`build_run13_evidence.py:41`, `build_run32_defensibility_inventory.py:53`,
`build_run36_audit.py:31`, `test_run32_client_authority.py:31`, `test_run36_fault_guards.py:55`,
`test_run36_instrument_qualification.py:32`. *Commit* `4c8d5ac`.

One cause, six files, one shared edit. The name is now **derived from the live registry** — the
Group D rows the registry currently holds — not written as a literal empty set. A literal would
bake today's answer in and keep being "right" after a restoration, which is the failure mode Run
97 warned about. Three of the six are generators other suites import, so the crash reached further
than the six that named it.

| script | before | after |
|---|---|---|
| `test_run32_client_authority.py` | ModuleNotFoundError | **18/18** |
| `test_run36_fault_guards.py` | ModuleNotFoundError | **34/41** |
| `test_run41_preservation.py` | ModuleNotFoundError | **29/33** |
| `test_run36_instrument_qualification.py` | ModuleNotFoundError | reaches its body, dies later on `MissingModuleError: A1.1` |
| `run32_closure_browser_verification.py` | ModuleNotFoundError | reaches its body, fails on `ConnectionRefused` — needs a live server |
| `test_run14_mismatch_remediation.py` | ImportError | reaches further, dies on `PortfolioModuleError`, also removed at Run 97 |

*Proof it can fail:* restoring any of the six imports reinstates the crash — `app.simulation.portfolio` does not exist on this tree.

### F9-d — the remaining ~60 crashing scripts — **NOT REACHED**

The retired-id buckets (31 scripts) each assert properties of specific removed identifiers and need
a per-script judgement about what the check should now say. That is real work and the budget went
to the harness causes and F10/F11, which is what the order's own ordering asked for. No script in
this group was silenced, edited or reclassified.

**The shape is known, which makes the next run cheap.** All 20 in the
`MissingModuleError` bucket die inside a small per-file `run()` wrapper that is
literally `return REG.run_module(code_id, si, RAND, CUTOFF)` — verified at
`test_run19_category_2.py:77`, `test_run29_canonical_oracles.py:75`,
`test_run1_disable_and_relabel.py:75` and seventeen more. The repair already
exists in this codebase: `test_run17_scientific_methods.py`'s `run()` substitutes,
once per identifier, the two assertions that are still true of a removed module —
the id does not resolve, and the dispatcher refuses it by name — instead of
dispatching it. Lifting that wrapper into a shared helper and pointing the twenty
`run()` bodies at it is one shared edit, not twenty judgements. **It must be
lifted together with `_suppressed_for`'s per-module scoping**, or every file that
adopts it inherits the silent-skipper defect repaired here as F11.

The twenty: `test_run10b_a1_7_domain.py`, `test_run10b_canonical_integration.py`,
`test_run19_category_2.py`, `_3`, `_4`, `_8`, `_9`,
`test_run1_disable_and_relabel.py`, `test_run20_advisory_lineage_disclosure.py`,
`test_run20_cycle8_arch3_clusters.py`, `test_run20_p0b_evidence_domain.py`,
`test_run29_canonical_oracles.py`, `test_run29_fault_campaign.py`,
`test_run29_supply_path_guard.py`, `test_run29_synthetic_packages.py`,
`test_run30_final_version_decision.py`, `test_run31_pass2_acceptance.py`,
`test_run31_version_boundaries.py`, `test_run36_closure_guards.py`,
`test_run80.py`.

The 11 in the `KeyError` bucket are the same removals reached through a literal
map rather than the dispatcher, and each needs its own answer about what the map
should now contain — those are genuinely per-script. Their crash sites, for the
next run: `drive_run105.py:227`, `test_run10_state_protection.py:46`,
`test_run16_material_cost_variance_disabled.py:54`,
`test_run20_cycle10_truthful_labels.py:150`,
`test_run20_lineage_declaration_truth.py:129`,
`test_run27_remediation_matrix.py:172`, `test_run28_closure.py:203`,
`test_run30_lineage_semantics.py:176`, `test_run31_canonical_oracles.py:929`,
`test_run3_adapter.py:279`, `test_run4_validate_seven.py:868`.

### F11 / M11 — `tools/test_run17_scientific_methods.py` — **RESOLVED**, 2 attempts

*File:* `server/tools/test_run17_scientific_methods.py:37` (import), `:104-146` (suppression),
`:1147-1210` (the section). *Commit* `b9fa0d0`.

**Two defects, both repaired, as the order required.**

1. *The crash.* Line 37 imported `compute_portfolio` from `app.simulation.portfolio`, deleted at
   Run 97 (`88e6ca0`). Nothing in the file had run since. `portfolio_health()` no longer computes:
   in its place stands the assertion that the removal **held** — both modules unimportable, all
   five D1 ids absent and refused by name by the dispatcher, no Group D row left, the D1.2 proxy
   qualifier gone. That check goes red if any of it is written back. Deleting the section silently
   would have revived the suite while dropping five modules' coverage with no record.
2. *The silent skipper.* `check()` and `proposition()` tested `_SUPPRESSED["module"]` for
   **truthiness**. `run()` sets it when it substitutes a Run-96-removed module and clears it only
   at the next `run()` for a live module, so a block ending on a removed module suppressed every
   subsequent check of every module — returned True, never counted in `TOTAL`, invisible in the
   RESULT line. Suppression now applies only to the module it was raised for, through
   `_suppressed_for()`, which accepts both spellings in use (`run()` passes `"A1.3"`, sections
   label checks `"1.3"`).

| state | result |
|---|---|
| before | crashed at import, no RESULT line, **0 checks evaluated** |
| attempt 1 — import fix only | RESULT: 127/133 |
| attempt 2 — + suppression scoping | **RESULT: 214/231** |

The import fix alone reached 133 checks. The truthiness suppression was eating a further **98**.

*Proof each can fail, both taken on this tree:* restoring the truthiness test → 127/133, the 98
vanish again; restoring the dead import → ModuleNotFoundError, no RESULT line; restoring both
fixes → 214/231.

### F11 / M13 — `tests/test_run34_holdout_provenance.py` — **RESOLVED**, 1 attempt

*File:* `server/tools/run34_ph1_tree_count_calibration.py:125` (`selection_decision`).
*Commit* `76543cd`.

The guard executes `selection_decision` at line 214 to prove the selection never reads the
holdout; that function imported `app.simulation.portfolio_health`, deleted at Run 97, so the guard
died there — 14 of 41 checks had run since, the other 27 had not. Run 43 had already recorded the
answer this D2 probe gets from a retired D1.1: no operational reading, no authoritative flag, both
conjuncts False. Run 97 removed the route altogether. The probe now **observes** that absence
instead of dying on it. It still reads the live route and still decides on what it finds there; if
Group D is restored the import succeeds and D2 decides on the real reading again.

Before: ImportError, no RESULT line, 27 of 41 dead. After: **RESULT: 41/41 checks passed.**
*Proof it can fail:* reverting the file brought the ImportError back and the RESULT line vanished.
**No new failures exposed** — all 27 revived checks pass.

### F10 — route the artefact generators — **PARTIAL (the fleet's writers, not all 130)**, 1 attempt

*Files:* `server/tools/artifact_write.py` (+`repo_root`, `artifact_out`),
`drive_run12_participant_cycle.py`, `drive_run21_instrument.py`, `drive_run21_participant.py`,
`test_run30_non_vacuity.py`, `test_run38_readiness.py`, `test_run39_launch_gate.py`.
*Commit* `159f815`.

The baseline fleet run recorded exactly what a plain `--run` rewrites in place: **21 committed
`code_audit` CSVs**, from six scripts. All six are now routed. **No second mechanism was built** —
same `--write-artifact` flag, same `RUN135_WRITE_ARTIFACT` / `RUN135_ARTIFACT_SCRATCH`, same
scratch root and mirrored layout. `artifact_out(committed)` is a thin call through the existing
`artifact_target` that finds the repository root itself, so routing a write is a one-token wrap;
for the two scripts with a `write_csv` helper it is one edit covering every CSV they emit, so no
call site could be missed.

*Proof, with `.artifact_scratch` removed first:* ran `test_run30_non_vacuity.py` (116/118),
`test_run38_readiness.py` (107/107), `test_run39_launch_gate.py` (98/100),
`drive_run12_participant_cycle.py` (50/56) → `git status --porcelain` showed **only the seven
source files**; not one committed artefact was touched, and 13 CSVs appeared under
`.artifact_scratch/code_audit/` mirroring their committed paths (`.artifact_scratch/` is already
in `.gitignore`).
*Proof the flag still writes:* `test_run30_non_vacuity.py --write-artifact` →
` M code_audit/run30_fault_injection.csv`, restored with `git checkout`.

*Proof at fleet scale, which is the measurement that matters.* The baseline fleet run left **21
committed `code_audit` CSVs modified**. The end-of-run fleet run, on this tree, left **four CSVs
and seven PNGs**, and **not one of the 21** — `run12_*`, `run21_*` (except
`run21_guard_nonvacuity_results.csv`, written by `test_run21_instrument_invariants.py`, which is
not routed), `run30_fault_injection`, `run38_*`, `run39_launch_identity` — appears in it. The four
that remain are `run17_failed_propositions.csv`, `run17_fault_injection.csv`,
`server/tools/run17/coverage.csv` and `run21_guard_nonvacuity_results.csv`; the first three are
dirt this run *created*, because `test_run17_scientific_methods.py` now runs at all and writes
them. They are the obvious next three to route. The 23 untracked droppings are unchanged.

*What remains, stated plainly:* the wider census is **476 write sites across 226 files** under
`server/tools` and `server/tests`, most of them writing to temporary directories rather than to
committed artefacts. Separating those two populations site by site is the rest of M14 and is not
done here. The 23 untracked droppings the baseline recorded (`server/run*_capture.json`,
`code_audit/run16_*`, `server/handbook_text.txt`) are also not routed.

### BLOCKED

**The `researchlogin` bootstrap defect's production half.** The collision described in F9-b is
half script-side and half in `app/research_identity.py:254` (`a_researchlogin` refuses the pair
when the username does not match the token's row). Nothing in the production code is wrong — the
collapse of the two failure messages is a deliberate anti-probing property, documented in the
function — so no production change is warranted and the repair belongs entirely in the scripts.
Recorded here because establishing it required reading `server/app/`, which was out of scope to
change. **Smallest decision needed: none.** No production change is proposed.

No other finding in this scope required a change under `server/app/`.

---

## Every new failure exposed by a revived script

These are findings for the next run, not problems with this one. **Nothing was silenced to make a
script complete.**

| script | now | failures exposed |
|---|---|---|
| `tools/test_run17_scientific_methods.py` | 214/231 | **17**: GATE ×3 (A2.12 has no owner-specification module at that key; the identifier-coercion detail; one register entry not exercised this run), 1.5 / 1.6 / 1.9 calibration-band checks, 6.2 weighted-vote authority, 6.3 ×4, 6.4 ×4, ARCH duplicate-lineage count, FAULT Category-9 raw bypass |
| `tools/test_run36_fault_guards.py` | 34/41 | **7** |
| `tools/test_run41_preservation.py` | 29/33 | **4** |
| `tools/test_run32_client_authority.py` | 18/18 | none |
| `tests/test_run34_holdout_provenance.py` | 41/41 | none |
| `tools/test_run36_instrument_qualification.py` | still crashes | its `len(_portfolio) == 5` and `== 95` / `== 94` population checks are now false against a Group-D-free registry; it dies before reaching them, on `MissingModuleError: A1.1` |
| `tools/run32_closure_browser_verification.py` | still fails | `ConnectionRefusedError` — needs a live server |
| `tools/test_run14_mismatch_remediation.py` | still crashes | `PortfolioModuleError` was also removed at Run 97 |

`drive_run105.py`, on a database of its own, reaches `KeyError: 'A2'` at line 227 — a real defect
the shared-database crash had been hiding.

---

## Iteration log

finding | attempt | change made | proof result | suite | disposition
---|---|---|---|---|---
F9-a env.py | 1 | async engine when the URL's dialect `is_async`; sync path unchanged | async URL migrates to head; revert → MissingGreenlet; restore → clean | alembic head `0033_recognition_matches`, both URL forms | RESOLVED
F9-b shared db | 1 | `--fresh-db DIR` on the fleet check, off by default | `--limit 3 --fresh-db` wrote one `.db` per script, 2 exit-0 / 1 crash | 5-script sample: 4 of 5 complete on their own database | RESOLVED (harness half)
F9-c PORTFOLIO_VALIDATED | 1 | new `run97_removed_portfolio.py` deriving the set from the registry; six imports repointed | 3 suites revived (18/18, 34/41, 29/33); 3 advanced to later, different causes | see table above | RESOLVED
F11 test_run17 | 1 | drop the dead `compute_portfolio` import; `portfolio_health()` asserts the Run 97 removal | RESULT: 127/133 — suite runs, but far short of its span | test_run17 | PARTIAL
F11 test_run17 | 2 | suppression scoped to the module it was raised for (`_suppressed_for`) | RESULT: 214/231; revert the scoping → 127/133; revert the import → crash | test_run17 | RESOLVED
F11 test_run34 | 1 | D2 probe observes a removed route instead of importing it | RESULT: 41/41; revert → ImportError, no RESULT line | test_run34_holdout_provenance | RESOLVED
F10 | 1 | `artifact_out` + six generators routed at their write sites | 4 generators run, tree clean; `--write-artifact` writes and was reverted | the four run above | PARTIAL
F9-d remainder | — | none | — | — | NOT REACHED

---

## Confirmations

- **Starting commit** `e29fb2c`. **Ending commit** is this report's own commit; the seven commits
  are `bca095a`, `b9fa0d0`, `76543cd`, `4c8d5ac`, `159f815`, `8847d02`, and this one.
- **Migration head** `0033_recognition_matches`, reached from an empty database under both
  `sqlite:///` and `sqlite+aiosqlite:///`.
- **`DATABASE_URL`** pointed only at throwaway SQLite files under the run-136 scratchpad.
  Production Postgres was never contacted. No recomputation was run.
- **`SIMULATION_VERSION` did not move.** Nothing in this scope changes a computed value; the stamp
  stands where Agent A left it, `sim-2026.09-v70`.
- **`git status --porcelain` before every commit** showed only the intended source files. The
  fleet and the individual driver runs dirtied `code_audit/` repeatedly (`run17_*`, `run18_shot_*`,
  `run21_*`, `run30_fault_injection`, `server/tools/run17/coverage.csv`); every one was restored
  with `git checkout --` before committing, and **no `code_audit` artefact is committed by this
  agent**. `git add` was by explicit path throughout; no `-A`, no `.`.
- **Nothing under `server/app/` was modified.** `git diff --stat e29fb2c..HEAD -- server/app` is
  empty.
- **Not pushed.** The primary verifies and pushes.

## What the v69/v70 recomputation must now cover

Nothing is added by this agent. Every change here is to tooling, to the migration harness, and to
where generators write; none of them changes a stored or computed value. Agent A's F1–F8 set the
recomputation scope and it is unchanged by Group 3.
