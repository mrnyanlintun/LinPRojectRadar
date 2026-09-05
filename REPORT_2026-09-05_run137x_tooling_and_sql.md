# Run 137 X — Item 2, Item 1, Item 5

**`SIMULATION_VERSION` DID NOT MOVE.** Nothing in this scope changes a stored or computed value.
Every change is to tooling: where a generator writes, what database the fleet gives a script, and
what a check about a removed module identifier says. Nothing under `server/app/` was modified —
`git diff --stat 2cb024e..HEAD -- server/app` is empty.

Agent X, working directly on `main`. Scope: Item 2, Item 1 (all buckets), Item 5.
Agent Y held `server/app/documents.py`, `tools/test_run17_scientific_methods.py`,
`tools/test_run36_fault_guards.py` and `tools/test_run41_preservation.py`; none of the four was
touched by this agent.

Starting sha `2cb024e`. Ending sha: the commit carrying this report — a report cannot name its own
hash, so read it from `git log -1`. This agent's code commits are `a153eba`, `7f5293d`, `fd90737`,
`d6a193d` and `be09743`.

**Agent Y's branch was merged into main at `e7f6672` while this agent was working, and every
figure below was re-taken after it.** The fleet run that was in flight at the time was killed by
pid and re-launched from `be09743`, which carries the merge; no coverage figure in this report was
taken before it. Y's merge released `tools/test_run17_scientific_methods.py`,
`tools/test_run36_fault_guards.py` and `tools/test_run41_preservation.py`, and the first of those
was the last known unrouted generator — it is routed in `be09743`.

---

## The coverage figure, on main

| | complete | of which exit 0 | of which reported failures | crash or time out |
|---|---|---|---|---|
| **Before** — Run 136 B's end-of-run fleet at `7ba00dd`, one shared database, 120s cap | **155 / 237 (65.4%)** | 97 | 58 | **82** |
| **After** — this run, on main at `be09743`, per-script databases, 120s cap | **181 / 237 (76.4%)** | 112 | 69 | **56** (37 crash, 19 timeout) |

Confirmed from `run136/B/after_exit.tsv` before anything else was done: 237 rows, 97 exit-0, 130
exit-1, 10 exit-124; applying the check's own definition of complete (`RESULT:` /
`checks passed` / `passed,` in stdout, and exit 124 always a crash) gives 155 complete and 82
crashing, which is B's figure exactly.

**The two figures are NOT taken under the same harness, and that is deliberate.** The owner ruled
per-script databases the standing fleet mode, so the after-figure measures the fleet as it now is.
The like-for-like figure is still available at any time with `--shared-db`.

**Net: +26 complete, -26 crashing.** 112 scripts now exit 0 against 97 before, and 69 complete
while reporting failures against 58 before — a red suite is a finding, a crashed suite is not a
finding at all, so both halves of that move are gains.

**Two scripts that completed on Run 136's fleet do not complete on this one, and both are named
rather than netted away:**

- `tools/drive_run82_gate_detail.py` now fails with `AssertionError: run drive_run80_gate.py
  first`. This is a **direct cost of the standing mode**: it depended on state left in the shared
  database by `drive_run80_gate.py` earlier in the same fleet run, and a database of its own has
  none. The mode is still right — a script whose result depends on which scripts ran before it was
  not measuring what it claimed to — but the dependency is real and now visible instead of
  implicit. **Smallest decision needed: should a driver that needs a predecessor's state seed it
  itself, or should the fleet grow a declared ordering?** Seeding it itself is the smaller change
  and the one that keeps every script independently runnable.
- `tools/drive_run63_four_charts.py` timed out at 120s. It is a browser driver that completed
  inside the cap on Run 136's fleet; nothing in this run touched it. Reported as measurement
  variance at the cap, the same way Run 136 reported `drive_run75_empty_period` moving the other
  way, and not as a regression from a repair.

**The fleet left no committed artefact modified.** `git status --porcelain` after the run shows
fifteen untracked droppings (`server/run*_capture.json`, `server/handbook_text.txt`,
`server/run51_handbook_*.txt`, `server/tools/run75_capture_run75.json`) and **not one ` M` entry**.
Run 136's baseline fleet left 21 committed `code_audit` CSVs modified and its end-of-run fleet
still left four CSVs and seven PNGs. That is Item 2's proof at fleet scale.

---

## Item 2 — the generators still rewriting committed files — **RESOLVED**

**R5: named ~130, routed 137 files / 192 sites, 3 files blocked by ownership, 40 sites
deliberately left alone with the reason recorded.**

### The census

The mechanism is the one Run 135C built and Run 136 F10 extended, in
`server/tools/artifact_write.py`: `artifact_out(committed)` returns the mirrored path under
`$RUN135_ARTIFACT_SCRATCH` (default `<repo>/.artifact_scratch`) unless `--write-artifact` or
`RUN135_WRITE_ARTIFACT=1` was given, in which case it returns the committed path itself. **No
second mechanism was built.** Same flag, same environment variables, same scratch root, same
mirrored layout.

A write site was counted as a committed-artefact write when its path expression — expanded
recursively through the file's own assignments — resolves under `code_audit/`,
`research/freeze/`, `research/study_execution/` or `server/tools/run*/`. 494 write sites exist
across 243 files under `server/tools` and `server/tests`; 235 of them resolve to a committed
artefact, in 137 files. Nine were already routed by Runs 135C and 136.

### What was routed

| | files | sites |
|---|---|---|
| already routed before this run (Run 135C, Run 136 F10) | 8 | 9 |
| routed by the bulk pass, commit `a153eba` | 131 | 185 |
| routed afterwards, from shapes the census missed | 9 | 7 |
| **total routed** | **137** | **192** |

### The two classes deliberately NOT routed

**40 read-back sites.** The same path expression is also read, stat'd or unlinked in the same
file. These are fault-injection round trips, not generators: `test_run5_export.py:171` corrupts a
manifest-covered file, asserts the digest moved away from the manifest entry, and restores it in a
`finally`. Routing the write while the read stays on the committed path would make the check
vacuous — it would compare the committed file against itself and pass having proved nothing. The
first bulk pass DID route that site; it was caught by reading the diff, the whole pass was reverted
with `git checkout --`, the guard was added, and the pass was re-run. Those sites leave the tree
clean by construction.

**Sites already routed.** The first pass detected "already routed" on the literal expression
rather than the resolved one, and so wrapped `run38_build_manifest.py`'s
`out = AW.artifact_target(...)` a second time, sending it to a scratch-of-scratch path. Also
caught in the diff, also reverted, and the test now runs on the expanded expression.

### The three files blocked by ownership

`tools/test_run17_scientific_methods.py` (writes `code_audit/run17_failed_propositions.csv`,
`code_audit/run17_fault_injection.csv`, `server/tools/run17/coverage.csv`),
`tools/test_run36_fault_guards.py` and `tools/test_run41_preservation.py` belong to Agent Y for
this run. The first three CSVs are the dirt Run 136 B created by reviving `test_run17`, and they
are named here as the only committed artefacts this run knows to be still unrouted.
**Smallest decision needed: none — the edit is the same one-token wrap, it simply belongs to
whoever holds the file.**

### The shapes the census missed, and how they were found

Every one was found the same way: by running scripts and watching `git status --porcelain`.

| shape | example | why the census missed it |
|---|---|---|
| `io.open(path, "w")` | `test_run29_fault_campaign.py:619` | an attribute-form `open` was read as `path.open(mode)`, so the first argument was taken for the mode |
| a path handed to a helper defined in another file | `write_results(HERE / "run17" / "categories" / "category_2_results.csv", …)` in the five Run-19 category suites | the `open()` is in `run17/audit_harness.py` against a parameter, unresolvable at the site |
| a name rebound several times from an f-string | `out = ROOT / "code_audit" / f"run26_…_{LABEL}.csv"` in `drive_run16/24/25/26` | the expander takes a name's FIRST assignment, and `out` is assigned four times |

Seven sites across nine files; all routed, in `7f5293d` and `d6a193d`.

### Proof

*With `.artifact_scratch` removed first,* five routed generators were run —
`test_run21_instrument_invariants.py` (28/28), `test_run30_lineage_semantics.py`,
`test_run10_synthetic_v03.py`, `run41_derive_final_fields.py`, `test_run20_cycle12_reaudit.py` —
and `git status --porcelain` over `code_audit/`, `research/` and `server/` was **empty**, with
`.artifact_scratch/code_audit/run41_final_judgment_field_derivation.csv` and
`.artifact_scratch/code_audit/run21_guard_nonvacuity_results.csv` written instead.
`test_run21_instrument_invariants.py` dirtied `code_audit/run21_guard_nonvacuity_results.csv` on
Run 136's end-of-run fleet — the one CSV F10 left unrouted — and no longer does.

*Proof the flag still writes:* `code_audit/run21_guard_nonvacuity_results.csv` was overwritten with
the single line `CORRUPTED`; `test_run21_instrument_invariants.py --write-artifact` replaced it
with real generated content; `git checkout --` restored it.

*Proof at fleet scale* is the after-fleet's dirty list, below.

---

## Item 1 — the crashers

### The buckets, re-derived on Run 136's end-of-run fleet

Using the check's own definition of crashed, the 82 divide as:

| bucket | count |
|---|---|
| `MissingModuleError` on a retired id | 21 |
| login collision (`KeyError` on `session_token` / `access_token`) | 17 |
| `KeyError`, of which 12 are a retired id in a hardcoded dict | 15 |
| other | 12 |
| timeout at 120s | 10 |
| `portfolio` / `portfolio_health` removed at Run 97 | 7 |

These differ slightly from Run 136 B's bucketing of the *baseline* 88 (20/17/11/15/11/14) because
they are taken on the *after* fleet, which B's own repairs had already moved. **No row of
`TOOLS_CLASSIFICATION.csv` was changed by this bucketing** — R4 stands, and no misclassification
was found that required correcting the CSV: every script examined in the retired-id and portfolio
buckets names live identifiers as well as dead ones, so not one of them is a retired artefact.

### Per bucket: expected against actually resolved

Every figure is taken from the after-fleet on main at `be09743`, scored by the check's own
definition, and compared script by script against Run 136's end-of-run fleet.

| bucket | was | now complete | still crashing | now timing out | R5: expected vs actually resolved |
|---|---|---|---|---|---|
| login collision | 17 | **9** | 0 | 8 | expected all 17 to be reachable by the mode; **9 resolved**. The other 8 get past login and are then cut off by the 120s cap — the bucket empties into the timeout bucket, exactly as the isolated measurement predicted |
| `MissingModuleError` on a retired id | 21 | **14** | 7 | 0 | expected the shared substitution to reach all 21; **14 resolved** — one more than the 13 measured in isolation, `test_run14_mismatch_remediation` having been carried over by the portfolio repair |
| `KeyError` (12 of them a retired id in a literal map) | 15 | **1** | 14 | 0 | not worked; expected 0 to 1 and **1 resolved**, incidentally |
| other | 12 | **3** | 9 | 0 | not worked; expected some to be shared-database artefacts and **3 resolved** by the mode alone |
| timeout at 120s | 10 | **0** | 0 | 10 | expected 0 — the cap was deliberately not raised for the measurement, so the figure stays comparable. All ten remain, unedited |
| `portfolio` removed at Run 97 | 7 | **1** | 6 | 0 | expected 1 to 2; **1 resolved** (`test_run45_period_scoping`), 1 more advanced past its import to a later cause |
| **total** | **82** | **28** | **36** | **18** | |

The 56 that still crash or time out are 36 crashes and 18 of the 82 timing out, plus the two
regressions named above.

### Login collisions, 17 — `--fresh-db` is now the default

Implemented in `tools/test_run135c_active_suite_completes.py`: per-script migrated SQLite
databases are the default, in `<fleet-dir>/../fresh_db` unless `--fresh-db DIR` names one, and
`--shared-db` restores the pre-Run-137 behaviour. **It is the default rather than a documented
invocation** because a standing mode that must be remembered is a mode that will be forgotten, and
the figure it produces would then silently depend on whether the operator typed a flag. The
like-for-like escape hatch is kept and named in the help text.

**R5, measured: 9 of 17 complete, not 17.** Each of the 17 was re-run alone on a freshly migrated
database at the same 120s cap.

| outcome | n | scripts |
|---|---|---|
| complete | 9 | `test_auth_session` 52/52, `test_run40_serve_content_security` 11/11, `test_run41_security_acceptance` 11/11, `run41_repro_s1` (exit 0), `drive_run24_empty_project_diagram` 19/31, `drive_run25_rail_removal` 33/35, `drive_run49_browser` 7/11, `drive_run52_browser` 6 passed 3 failed, `drive_run52_premise` 4 passed 3 failed |
| timed out at 120s | 7 | `drive_run18_final_flow`, `drive_run21_instrument`, `drive_run21_participant`, `drive_run54_navigation`, `drive_run55_admin_controls`, `drive_run56_duplicate_controls`, `drive_run57_reset_merge` |
| still crashes | 1 | `drive_run23_signal_flow_ui`, on a page-side error inside `page.evaluate`, not on login |

The seven that time out are the measurement's second half and belong in the report as plainly as
the nine: **the mode empties the collision bucket into the timeout bucket.** They are no longer
failing at login — they get past it and then do real browser work that a 120s cap cuts off. The
fleet's timeout bucket therefore GROWS as its collision bucket empties, and any reading of the
after-figure that does not account for that is wrong.

### The retired-id bucket, 21 — one substitution, lifted

New file `server/tools/run96_removed_substitution.py`. It is `test_run17_scientific_methods.py`'s
own answer to what a check about a removed module should say, lifted so there is one of it rather
than twenty-one: the proposition is **replaced**, once per identifier, by the two facts now true
of it — the identifier does not resolve, and the dispatcher refuses it **by name** — and the
propositions that followed are suppressed until the next dispatch of a module still in service.
Nothing is silenced. The substituted assertions are counted, and they go red the moment a removed
row is written back.

**It does not inherit the F11 defect Run 136 repaired.** Suppression is cleared by the next live
dispatch, and every suppressed check is counted in `substitution.suppressed`, so over-suppression
is visible rather than invisible in a RESULT line.

Two departures from `test_run17`'s version, each forced by evidence:

1. **Removal is decided by calling and catching `MissingModuleError`, not by a lookup in the live
   registry index.** `test_run31_version_boundaries.py` deliberately dispatches against an *older*
   vendored registry line in which some of these identifiers still exist; a live-index lookup
   would have substituted a module the line under test really carries. Under the call-and-catch
   rule that suite goes from a crash to **24/24**.
2. **The wrapper is installed over the script's own check surface, whatever its shape.** The
   Run-19 category suites route assertions through an imported audit object (`A.check`, `A.near`,
   `A.proposition`) rather than module-level functions. Wrapping only the globals left a removed
   module's propositions asserted against a reading that is not there, which reads as a red suite
   instead of as a removal: `test_run19_category_2.py` reported **81/148** with the globals-only
   wrapper and **62/70** once the audit object was covered. The 81/148 was not a finding, it was
   an artefact of an incomplete wrap, and it was caught by reading the failures rather than the
   count.

**Result: 13 of 21 complete.**

| script | before | after |
|---|---|---|
| `test_run19_category_2` | MissingModuleError A2.2 | 62/70 |
| `test_run19_category_3` | MissingModuleError | 67/74 |
| `test_run19_category_4` | MissingModuleError | 135/144 |
| `test_run19_category_8` | MissingModuleError | 64/70 |
| `test_run19_category_9` | MissingModuleError | 19/25 |
| `test_run20_advisory_lineage_disclosure` | MissingModuleError | 9/10 |
| `test_run20_cycle8_arch3_clusters` | MissingModuleError | 62/69 |
| `test_run20_p0b_evidence_domain` | MissingModuleError | **21/21** |
| `test_run29_fault_campaign` | MissingModuleError | **64/64** |
| `test_run29_supply_path_guard` | MissingModuleError | **53/53** |
| `test_run29_synthetic_packages` | MissingModuleError | **17/17** |
| `test_run31_pass2_acceptance` | MissingModuleError B4.3 | **35/35** |
| `test_run31_version_boundaries` | MissingModuleError | **24/24** |
| `test_run80` | MissingModuleError A3.1 | 32/33 |

The eight that still crash, each on a cause that is **not** this one:

| script | now | shape |
|---|---|---|
| `test_run36_closure_guards` | MissingModuleError A1.1 | **BLOCKED** — see below |
| `test_run36_instrument_qualification` | MissingModuleError A1.1 | **BLOCKED** — see below |
| `test_run10b_a1_7_domain` | `oldsim10b.registry.MissingModuleError: A1.1` | `run_all` over a VENDORED old registry line that still declares A1.1 while its module source no longer exists on this tree |
| `test_run30_final_version_decision` | `oldsim30v16.registry.MissingModuleError: A1.1` | the same shape, v16 line |
| `test_run10b_canonical_integration` | `KeyError: 'A2.2'` | reaches past the dispatch; now in the hardcoded-dict bucket |
| `test_run1_disable_and_relabel` | `KeyError: 'category'` | reaches past the dispatch |
| `test_run29_canonical_oracles` | `KeyError: 'A'` | reaches past the dispatch |
| — | | |

### BLOCKED — a production guard whose subject was removed

`app/simulation/models_sim.py:254`, inside
`assert_retained_adaptation_not_reachable`, dispatches A1.1 with a fully qualified assessment to
prove that the Category-9 gate short-circuits before the dispatch table is consulted. The
correction that put it there was forced by Run 36's own fault campaign: with a bare probe the
guard stayed green while the retained adaptation was live, so a guard satisfied by somebody else's
refusal was proving nothing about its own subject.

A1.1 was not *disabled* at Run 96/97. It was **removed**. `run_module` therefore raises
`MissingModuleError` before the gate is reached, and the guard's own premise —
`"A1.1" in DISABLED_CANONICAL_INPUT_NOT_GOVERNED` — is stale. Two active scripts
(`test_run36_closure_guards.py:96`, `test_run36_instrument_qualification.py:180`) crash inside it.

The repair is in `server/app/`, which this agent may not change. **Smallest decision needed:
should `assert_retained_adaptation_not_reachable` now assert that A1.1 is REFUSED AS ABSENT rather
than short-circuited as disabled?** If yes it is a small edit in `models_sim.py` and both scripts
follow. If the retained adaptation must still be proven unreachable through a *live* identifier,
the guard needs a new subject and that is a larger question about what the guard is for.

### The `portfolio` bucket, 7 — 1 resolved, 1 advanced, 5 reported

Two of the removed names carry a check that is still true and merely cannot be evaluated, and both
are repaired:

- **`PortfolioModuleError`.** Until Run 97 `run_module` carried a Group D branch refusing a
  portfolio-level identifier on a single-project call by that name. The branch and the five rows
  are gone, so the identifier is refused one step earlier as `MissingModuleError` — the refusal
  still happens and is now stronger. `tools/run97_removed_portfolio.py` exports the removed name
  as an **alias** of the refusal that replaced it. Deliberately an alias and not a fresh class: a
  fresh class would stop `except PortfolioModuleError` catching anything, and the check at
  `test_run13_module_evidence.py:251` would either die or — worse — pass having caught nothing.
  Repointed at `build_run13_evidence.py:53` and `test_run13_module_evidence.py:32`.
  `test_run14_mismatch_remediation.py`, which crashed on this import reached *through*
  `build_run13_evidence`, now runs past it and dies later on `KeyError: 'A2.11'`.
- **`live_portfolio_modules`** — `test_run45_period_scoping.py:47`. The check asked whether
  Portfolio Health computes anywhere on a production path and expected the empty tuple. It is
  replaced by the stronger fact now true: the module that would compute it cannot be imported at
  all. **Before: ModuleNotFoundError, no RESULT line, 0 of 77 checks evaluated. After: RESULT
  73/77.** *Proof it can fail:* restoring the import reinstates ModuleNotFoundError and the RESULT
  line disappears.

The remaining five — `test_period_series.py`, `test_run13_module_evidence.py`,
`test_run14_anomaly_detectors.py`, `test_run20_cycle12_lineage_and_guards.py`,
`test_run2_fifteen_defects.py` — import `compute_portfolio` or the `portfolio` module itself and
use it to compute a portfolio reading. Each needs a judgement about what its portfolio *section*
should now say, not a name repointed, and each still tests live modules alongside it
(`test_run2_fifteen_defects` names eleven live identifiers against seven dead; its "portfolio
three", defects 6, 7 and 8, are the only part that has lost its subject). **Not reached. None was
edited, silenced or reclassified.**

### Timeouts, 10 — what each was doing

All ten are Playwright drivers, and every one was cut off **mid-work, not spinning**. Read from
the captured stdout at the moment of the cap:

| script | where the 120s cap cut it off |
|---|---|
| `drive_run86_panel_widths` | inside a viewport sweep, "VIEWPORT 1280px — collapsed rows" |
| `drive_run90_charts` | viewport sweep, "VIEWPORT 1024px" |
| `drive_run91_brief` | viewport sweep, "VIEWPORT 1024px" |
| `drive_run94_charts` | theme sweep, "THEME dark (set: dark)" |
| `drive_run50_browser` | inside a "GROUP HEADERS" section |
| `drive_run38_browser` | mid page-walk, with passes already recorded |
| `drive_run39_pilot_browser` | mid page-walk, with passes already recorded |
| `drive_run100_awaiting` | mid assertion about an un-run analysis |
| `drive_run70_partb` | after a `SESSION_SECRET` warning, mid session work |
| `drive_run73_two_projects` | the same |

The work is real and it is bounded — a fixed list of viewports, themes and pages. **Not one of
the ten is repaired by editing the script**, and none was edited. The cap is the wrong instrument
for them, so `--browser-timeout SECONDS` now gives a separate, longer cap to any script whose
source names Playwright. **It defaults to 0 — use `--timeout` for everything — so the coverage
figure stays comparable with Runs 135 and 136.** Raising it for the whole fleet would multiply the
fleet's wall-clock by the 45 browser-dependent scripts, which is a cost the owner should choose
deliberately rather than inherit from this report.

### `KeyError` (15) and other (12) — reported, not repaired

Twelve of the fifteen `KeyError`s are a retired identifier reached through a literal map rather
than the dispatcher, and each needs its own answer about what the map should now contain:
`drive_run105.py` `'A2'`, `test_run10_state_protection.py` `'A3.1'`,
`test_run16_material_cost_variance_disabled.py` `'A3.4'`,
`test_run20_cycle10_truthful_labels.py` `'A3.8'`, `test_run20_lineage_declaration_truth.py`
`'A1.1'`, `test_run27_remediation_matrix.py` `'A1.3'`, `test_run28_closure.py` `'A1.10'`,
`test_run30_lineage_semantics.py` `'B2.14'`, `test_run31_canonical_oracles.py` `'B3.2'`,
`test_run3_adapter.py` `'B1.3'`, `test_run4_validate_seven.py` `'A3.4'`, plus
`test_run14_mismatch_remediation.py` `'A2.11'` which this run moved into the bucket. The other
three (`drive_run79` `'display'`, `test_run42_period_binding_mechanism` `'category'`,
`test_transitions` `'state'`) are data-shape faults, not retired identifiers.

The twelve in "other" are one each: four `IndexError: list index out of range` in drivers
(`drive_run111`, `drive_run61_caller_shapes`, `run41_ai_binding_digests`, `run41_browser_s1`,
`run41_repro_s2`), three `AssertionError` (`drive_run51_browser` "not a member of this project",
`drive_run82_charts` "the Signal Flow SVG did not render", `test_export.py` "no frozen transition
rule"), `drive_run119` `AttributeError` on `None`, `drive_run44_browser` a page-side script error,
`test_run39_launch_gate` a SQLAlchemy error, and `run32_closure_browser_verification` a
`ConnectionRefusedError` — the one script that needs a live application server it does not start.
Several of these read like empty-result faults that a database of a script's own may clear; the
after-fleet is the measurement of that and is reported above rather than guessed at here.

---

## Item 5 — the F6 archived-row count

**This is the SQL and the instructions. Nothing was run against anything but a throwaway SQLite,
and nothing was deleted.** Clearing these rows belongs with the v70 recomputation, not ahead of it.

### The command

```
psql "$DATABASE_URL" -f run137_f6_archived_rows.sql
```

or, with the statement inline:

```
psql "$DATABASE_URL" -c '<the SELECT below, as one line or a quoted heredoc>'
```

`$DATABASE_URL` is read from the environment so **no credential is typed on the command line or
recorded in shell history**. It is a read-only `SELECT`; it deletes nothing and writes nothing.
Add `--csv` if the result should be kept as a file.

### The SQL

```sql

-- RUN 136, F6. Rows ALREADY PROJECTED from a document the document control has ARCHIVED.
--
-- H4 (Run 135) stopped NEW rows being projected for an archived document. It did not remove
-- rows projected before that, which remain in the three projection stores and in the
-- observation store and are still read. This is the count. IT DELETES NOTHING.
--
-- The archive mark lives on `document_uploads.archived_at` and is scoped to
-- (project_id, period) -- `documents` is shared content-addressed storage, so the same bytes
-- may be live evidence in another project or another period. Every join below therefore
-- matches on all three of project_id, period and document_id, exactly as
-- `_archived_document_ids` does.

SELECT 'schedule_activities' AS store, s.project_id, s.period,
       COUNT(*) AS rows_from_archived_documents,
       COUNT(DISTINCT s.document_id) AS archived_documents
FROM schedule_activities s
JOIN document_uploads u
  ON u.project_id = s.project_id AND u.period = s.period AND u.document_id = s.document_id
WHERE u.archived_at IS NOT NULL
GROUP BY s.project_id, s.period

UNION ALL

SELECT 'project_risks', r.project_id, r.period, COUNT(*), COUNT(DISTINCT r.document_id)
FROM project_risks r
JOIN document_uploads u
  ON u.project_id = r.project_id AND u.period = r.period AND u.document_id = r.document_id
WHERE u.archived_at IS NOT NULL
GROUP BY r.project_id, r.period

UNION ALL

SELECT 'project_notices', n.project_id, n.period, COUNT(*), COUNT(DISTINCT n.document_id)
FROM project_notices n
JOIN document_uploads u
  ON u.project_id = n.project_id AND u.period = n.period AND u.document_id = n.document_id
WHERE u.archived_at IS NOT NULL
GROUP BY n.project_id, n.period

UNION ALL

-- The observation store. `_persist_observations` runs off `_period_documents`, so it has
-- never emitted for an archived document; rows here would predate the 0027 archive mark or
-- predate the archiving of a document that was live when it was read. Counted separately, and
-- withdrawn rows are counted separately again because `observations.withdrawn_at` is already
-- an archive mark on the row itself (migration 0029).
SELECT 'observations (not withdrawn)', o.project_id, o.period, COUNT(*),
       COUNT(DISTINCT o.document_id)
FROM observations o
JOIN document_uploads u
  ON u.project_id = o.project_id AND u.period = o.period AND u.document_id = o.document_id
WHERE u.archived_at IS NOT NULL AND o.withdrawn_at IS NULL
GROUP BY o.project_id, o.period

UNION ALL

SELECT 'observations (withdrawn)', o.project_id, o.period, COUNT(*),
       COUNT(DISTINCT o.document_id)
FROM observations o
JOIN document_uploads u
  ON u.project_id = o.project_id AND u.period = o.period AND u.document_id = o.document_id
WHERE u.archived_at IS NOT NULL AND o.withdrawn_at IS NOT NULL
GROUP BY o.project_id, o.period

ORDER BY 1, 2, 3;   -- positional: a UNION's ORDER BY may only name the first SELECT's columns
```

### What each column means

| column | meaning |
|---|---|
| `store` | which projection or observation store the row was counted in — `schedule_activities`, `project_risks`, `project_notices`, `observations (not withdrawn)`, `observations (withdrawn)` |
| `project_id` | the project the rows belong to |
| `period` | the period the rows belong to. The archive mark is scoped to `(project_id, period)`, so a document archived in one period may still be live evidence in another |
| `rows_from_archived_documents` | how many rows in that store, for that project and period, were projected from a document the document control has since archived. **This is the number the finding is about** |
| `archived_documents` | how many DISTINCT archived documents those rows came from. A large row count against a small document count means one archived document is carrying many rows |

**No row means nothing to count.** An empty result is the answer that H4 (Run 135) closed the door
before anything came through it.

**Why the two observation lines are separate.** `observations.withdrawn_at` (migration 0029) is
already an archive mark on the row itself, so a withdrawn observation from an archived document is
doubly marked and is not the same finding as a live one. Counting them together would overstate
what is still being read.

**Why every join matches on all three of `project_id`, `period` and `document_id`.** `documents`
is shared content-addressed storage: the same bytes may be live evidence in another project, or in
another period of the same project. Joining on `document_id` alone would count rows that are not
from an archived document at all. This is exactly what `_archived_document_ids` does.

**Proof the query still parses and executes**, re-taken this run: the statement was executed
against a throwaway SQLite carrying the five tables and returned cleanly (no rows, the tables being
empty). Run 136 A's seeded proof — one archived document and one live document in project 1
period 3, plus the *same archived bytes live in project 2 period 1* — returned exactly the rows
from the archived document and nothing from the live document or the other project.

---

## Iteration log

finding | attempt | change made | proof result | suite | disposition
---|---|---|---|---|---
Item 2 census | 1 | AST census of 494 write sites, path expressions expanded through the file's own assignments | 235 sites in 137 files resolve to a committed artefact | — | (measurement)
Item 2 routing | 1 | bulk wrap of every resolving site in `artifact_out()` | 142 files, 232 sites — **but** double-wrapped `run38_build_manifest` into scratch-of-scratch, and routed `test_run5_export`'s fault-injection round trip, making its check vacuous | compile clean, diff read | FAILED, reverted with `git checkout --` |
Item 2 routing | 2 | same pass, plus two guards: "already routed" tested on the EXPANDED expression, and read-back sites skipped | 131 files, 185 sites; 40 read-back sites skipped; `run38`/`run39` untouched | 5 generators run, `git status --porcelain` empty; `--write-artifact` overwrote a deliberately corrupted CSV | RESOLVED
Item 2 gaps | 3 | `io.open` and the `write_results` helper call sites | 6 files run, tree clean afterwards | `test_run29_fault_campaign` 0, five Run-19 suites | RESOLVED
Item 2 gaps | 4 | f-string paths rebound several times in one file | `drive_run16/24/25/26`, 4 sites | the 17-script collision run left the tree clean where it had dirtied two CSVs | RESOLVED
Item 1 login mode | 1 | `--fresh-db` made the default, `--shared-db` added | the 17 re-run one at a time on their own databases | **9 complete, 7 timeout, 1 crash** | RESOLVED (9 of 17, measured)
Item 1 retired-id | 1 | shared substitution, removal decided by live-registry lookup | 13 suites revived, but `test_run31_version_boundaries` substituted a module its vendored line really carries | — | PARTIAL
Item 1 retired-id | 2 | removal decided by calling and catching `MissingModuleError` | `test_run31_version_boundaries` 24/24 | — | PARTIAL
Item 1 retired-id | 3 | suppressing wrapper extended to the imported audit object | `test_run19_category_2` 81/148 → 62/70, propositions about removed modules substituted rather than asserted against an absent reading | 13 of 21 complete | RESOLVED (13 of 21)
Item 1 portfolio | 1 | `PortfolioModuleError` aliased to the refusal that replaced it | `test_run14_mismatch_remediation` past the import, dies later on `KeyError 'A2.11'` | — | PARTIAL (bucket)
Item 1 portfolio | 2 | `live_portfolio_modules` check replaced by the unimportability of the module | crash → **73/77**; restoring the import brings the crash back | `test_run45_period_scoping` | RESOLVED (1 script)
Item 1 timeouts | 1 | `--browser-timeout`, default 0 | all ten established as bounded browser work cut off mid-sweep | — | RESOLVED as a harness option; no script edited
Item 1 keyerror / other | — | none | — | — | NOT REACHED
Item 5 | 1 | SQL printed with its command pattern and column meanings | executes cleanly on a throwaway SQLite | — | RESOLVED
Item 2 test_run17 | 5 | three write sites routed once agent Y released the file | 222/222 unchanged, tree clean afterwards | test_run17 | RESOLVED
after-fleet | 1 | full fleet re-run on main at `be09743`, per-script databases, 120s cap | 181 complete / 56 crash, against 155 / 82 | all 237 | (measurement)

---

## Confirmations

- **Starting commit** `2cb024e`. Code commits `a153eba`, `7f5293d`, `fd90737`, `d6a193d`; the
  ending commit is this report's own.
- **Migration head** `0033_recognition_matches`, reached from an empty database.
- **`DATABASE_URL`** pointed only at throwaway SQLite files under
  `scratchpad/run137/X/`. Production Postgres was never contacted, and the F6 SQL was run only
  against an empty throwaway SQLite to confirm it parses. No recomputation was run.
- **`SIMULATION_VERSION` did not move.** Nothing here changes a stored or computed value, so
  **nothing is added to what the v69/v70 recomputation must cover.**
- **`git status --porcelain` before every commit** showed only the intended source files, and is
  recorded in this report at each point. The runs dirtied committed artefacts three times
  (`code_audit/run29_fault_injection.csv` and five `server/tools/run17/categories/*_results.csv`;
  `code_audit/run26_browser_facts_after.csv` and `run26_empty_project_colours_after.csv`); each
  was restored with `git checkout --` and the write site that caused it was routed. **No
  `code_audit`, `research/freeze` or `research/study_execution` artefact is committed by this
  agent, and nothing was re-baselined.**
- **`git add` by explicit path throughout.** No `-A`, no `.`.
- **Nothing under `server/app/` was modified.** The one repair that would have needed it is
  recorded as BLOCKED with the smallest decision named.
- **Not pushed.**
- **Agent Y's merge `e7f6672` is in the history this report describes.** The fleet run that was
  in flight when it landed was killed by pid — never by a `pkill` pattern — and re-launched from
  `be09743`. Y's residual findings (`test_run36` 42/43, `test_run41` 32/33) are Y's to report and
  are not restated here; both suites complete, so neither affects this agent's coverage figure
  except as part of the 181.

## Dispositions

| item | disposition |
|---|---|
| Item 2 — the ~130 unrouted generators | **RESOLVED** — 137 files, 192 sites; proven at fleet scale with no committed artefact modified |
| Item 1, login mode | **RESOLVED** — `--fresh-db` is the default; 9 of 17 measured, not assumed |
| Item 1, retired-id (21) | **PARTIAL** — 14 of 21; 2 BLOCKED on `server/app/`, 2 on vendored registry lines, 3 advanced into the `KeyError` bucket |
| Item 1, portfolio (7) | **PARTIAL** — 1 of 7 resolved, 1 advanced; 5 need a per-script judgement about their portfolio section |
| Item 1, timeouts (10) | **RESOLVED as a harness option** — all ten established as bounded browser work; `--browser-timeout` added, default off, no script edited |
| Item 1, `KeyError` (15) and other (12) | **NOT REACHED** as repairs; 4 of them resolved by the mode alone; every one characterised above |
| Item 5 — the F6 count | **RESOLVED** — SQL, command pattern and column meanings printed; nothing run against production, nothing deleted |
