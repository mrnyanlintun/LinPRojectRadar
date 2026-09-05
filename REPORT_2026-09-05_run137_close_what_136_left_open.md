# Run 137 — close what Run 136 left open

**Date** 2026-09-05 · **Branch** `main` · **Start** `2cb024e` · **End** see final commit below.
**No migration was added.** Migration head unchanged at `0033_recognition_matches`.
**`SIMULATION_VERSION` did not move** (`sim-2026.09-v70`). The only change under
`server/app/` is Item 4 (`documents.py`, an alias removal), which affects a first-pass
extraction alias and not a stored figure; nothing is added to the v70 recomputation.

Two agents worked the order: **X** on `main` (Items 2, 1, 5; owned `server/tools/`,
`server/tests/`, `code_audit/`, `research/`) and **Y** in a worktree (Items 4 and 3; owned
`server/app/documents.py` and three test suites). Y was merged `--no-ff` at `e7f6672`. Every
figure below was re-taken by me on `main`, not copied from an agent: the three Y suites on
`main` at `e7f6672` with a throwaway SQLite, the after-fleet from X's `now.tsv` at `be09743`
(post-merge), and the F6 SQL executed against a throwaway SQLite.

Sub-reports: `REPORT_2026-09-05_run137x_tooling_and_sql.md`,
`REPORT_2026-09-05_run137y_alias_and_28_hunt.md`.

## Dispositions

| item | disposition |
|---|---|
| 1 crashers — login collisions (17) | RESOLVED as a standing mode; 9 complete, 8 became timeouts |
| 1 crashers — retired-id `MissingModuleError` (21) | PARTIAL, 14 of 21 |
| 1 crashers — `portfolio` (7) | PARTIAL, 1 of 7 (+1 advanced) |
| 1 crashers — timeouts (10) | harness option added, no script edited, 0 of 10 by design |
| 1 crashers — `KeyError` (15), other (12) | NOT REACHED; reported script by script |
| 2 unrouted generators | RESOLVED — 137 files / 192 sites; after-fleet dirtied nothing |
| 3 the 28 exposed failures | RESOLVED — 28/28 classified; 16 stale, 11 vacuous, 1 real |
| 4 `packages_due` bare alias | RESOLVED |
| 5 F6 archived-row SQL | RESOLVED — SQL and instructions below, nothing run on production |

## Coverage, on main

| | complete | exit 0 | reported failures | crash | timeout |
|---|---|---|---|---|---|
| Run 136 end (shared DB), `2cb024e` | 155/237 | 97 | 58 | 72 | 10 |
| Run 137 end (per-script DB, 120s cap), `be09743` | **181/237** | 112 | 69 | 37 | 19 |

Confirmed from the raw exit tables: Run 136 `after_exit.tsv` 97/130/10; Run 137
`fleet_exit.tsv` 112/106/19, with `now.tsv` classifying the 106 non-zero exits into 69 reported
failures and 37 crashes.

## Item 1 — per bucket, expected against actually resolved (R5)

Buckets re-derived on Run 136's end-of-run fleet (82 crashers; they differ from Run 136 B's
bucketing of the baseline 88 because B's repairs had already moved rows). No row of
`TOOLS_CLASSIFICATION.csv` changed (R4).

| bucket | was | now complete | still crash | now timeout | expected | actually resolved |
|---|---|---|---|---|---|---|
| login collision | 17 | 9 | 0 | 8 | 17 | **9** — the other 8 get past login and are cut by the 120s cap |
| retired-id `MissingModuleError` | 21 | 14 | 7 | 0 | 21 | **14** — 13 measured alone, +1 carried by the portfolio repair |
| `KeyError` (12 are a retired id in a literal map) | 15 | 1 | 14 | 0 | 0–1 | **1**, incidental |
| other | 12 | 3 | 9 | 0 | some | **3**, by the DB mode alone |
| timeout at 120s | 10 | 0 | 0 | 10 | 0 | **0**, cap deliberately unchanged |
| `portfolio` removed at Run 97 | 7 | 1 | 6 | 0 | 1–2 | **1** (`test_run45_period_scoping`, 0/77 evaluated → 73/77) |
| **total** | **82** | **28** | **36** | **18** | | |

Two non-regressions, not netted away: `drive_run82_gate_detail` depended on state another script
left in the shared database (a real cost of per-script databases) and `drive_run63_four_charts`
(cap variance). 181 = 155 + 28 − 2.

**Login collisions.** `--fresh-db` (per-script migrated SQLite) is now the default of
`tools/test_run135c_active_suite_completes.py`; `--shared-db` restores the old behaviour. The
mode empties the collision bucket into the timeout bucket: the seven drivers that now time out
are doing real browser work past login.

**Timeouts.** All ten are Playwright drivers cut mid-sweep (viewports, themes, page walks).
`--browser-timeout SECONDS` gives a separate cap to Playwright scripts; it defaults to 0 so the
coverage figure stays comparable with Runs 135 and 136. Raising it is the owner's choice.

**Retired-id bucket.** The Run 96 substitution used by `test_run17` was lifted into one shared
helper and adopted by 19 suites. Seven still crash on a later cause.

**BLOCKED (needs a ruling), X-1.** `app/simulation/models_sim.py:254`
`assert_retained_adaptation_not_reachable` dispatches A1.1 to prove the Category-9 gate
short-circuits, but Run 96/97 removed A1.1 rather than disabling it, so `run_module` raises
`MissingModuleError` first. `test_run36_closure_guards` and `test_run36_instrument_qualification`
crash inside it. Decision: should the guard assert A1.1 is refused as absent, or does it need a
live subject? The edit is in `server/app/`, outside this run's mandate.

**BLOCKED (needs a ruling), X-2.** `drive_run82_gate_detail` needs a predecessor's state.
Decision: should a driver seed its own predecessor state (smaller, keeps every script
independently runnable), or should the fleet grow a declared ordering?

**Not reached, listed by name.** `KeyError` on a retired id in a literal map: `drive_run105`
`'A2'`, `test_run10_state_protection` `'A3.1'`, `test_run16_material_cost_variance_disabled`
`'A3.4'`, `test_run20_cycle10_truthful_labels` `'A3.8'`, `test_run20_lineage_declaration_truth`
`'A1.1'`, `test_run27_remediation_matrix` `'A1.3'`, `test_run28_closure` `'A1.10'`,
`test_run30_lineage_semantics` `'B2.14'`, `test_run31_canonical_oracles` `'B3.2'`,
`test_run3_adapter` `'B1.3'`, `test_run4_validate_seven` `'A3.4'`,
`test_run14_mismatch_remediation` `'A2.11'`. Data-shape `KeyError`: `drive_run79` `'display'`,
`test_run42_period_binding_mechanism` `'category'`, `test_transitions` `'state'`. Other (12):
five `IndexError` drivers (`drive_run111`, `drive_run61_caller_shapes`,
`run41_ai_binding_digests`, `run41_browser_s1`, `run41_repro_s2`), three `AssertionError`
(`drive_run51_browser`, `drive_run82_charts`, `test_export`), `drive_run119` `AttributeError`,
`drive_run44_browser` page-side error, `test_run39_launch_gate` SQLAlchemy error,
`run32_closure_browser_verification` `ConnectionRefusedError` (needs a live server it does not
start). Portfolio, five still needing a judgement about what their portfolio section should
now say: `test_period_series`, `test_run13_module_evidence`, `test_run14_anomaly_detectors`,
`test_run20_cycle12_lineage_and_guards`, `test_run2_fifteen_defects`.

## Item 2 — the generators

Named ~130 in Run 136; census on main found **137 files / 192 write sites** and all are routed
through the Run 135C `.artifact_scratch` mechanism, with `--write-artifact` still overwriting
the committed file (proven by corrupting a CSV and regenerating it). 40 read-back
fault-injection round trips were deliberately not routed: routing them would make the check
vacuous (caught by reading the diff; the bulk pass was reverted and re-run with a guard).
Proof at fleet scale: the after-fleet left **no ` M` entry** against 21 dirty CSVs on Run 136's
baseline. I re-confirmed on `main` that `test_run17_scientific_methods.py` (222/222) leaves the
tracked tree clean. The fleet still leaves 15 untracked capture files under `server/` (driver
`*_capture.json` and handbook text dumps); untracked, so outside Item 2's definition; I deleted
them after the run.

## Item 3 — the 28 exposed failures, each classified

| classification | count |
|---|---|
| Stale expectation, re-pointed under R2 | 16 |
| Vacuous check, repaired (10) or retired (1) | 11 |
| Real defect, reported, not fixed | 1 |
| Unclear | 0 |

| suite | before | after, on main |
|---|---|---|
| `test_run17_scientific_methods` | 214/231 | **222/222** |
| `test_run36_fault_guards` | 34/41 | **42/43** (residual is D1) |
| `test_run41_preservation` | 29/33 | **32/33** (residual is D2) |

All three suites resolve `sys.path` from `__file__`, so Y's worktree figures were of Y's branch;
I re-took them on `main` after the merge and they match.

| id | suite | class | source / evidence | commit |
|---|---|---|---|---|
| Y-1…Y-10 | run17 | VACUOUS | `_suppressed_for` paired section labels to ids by stripping the group letter; Run 43's renumbering (`6.3→B1.3`, `6.4→B1.4`) broke it, so ten checks evaluated the `_Absent` sentinel and could never pass. Repaired with an explicit `SECTION_TO_MODULE`. | `7987daf` |
| Y-11, Y-12, Y-13 | run17 | STALE | A1.5 / A1.6 / A1.9 band ladders re-pointed to Run 107 (v53), asserting provenance class and threshold source | `1fa9c19` |
| Y-14 | run17 | STALE | 6.2 plurality replaced by the project rule's own band (Run 106, v52); expectation computed from the owner's profile and cuts | `622a77a` |
| Y-15 | run17 | STALE | GATE mapping: A2.12 registered after the sealed audit (Run 103); roster-is-real check added | `622a77a` |
| Y-16 | run17 | VACUOUS | GATE float round-trip: premise falsified by Run 96; repaired to assert the coercion trap | `622a77a` |
| Y-17 | run17 | STALE | register entries PH.1, PH.5 retired with Run 97 (`88e6ca0`) deletion recorded beside them | `622a77a` |
| Y-18 | run36 | STALE | A2.12 post-audit roster (Run 103) | `bd713be` |
| Y-19 | run36 | STALE | removal roster read from `run96_removed` (Runs 96, 97) | `bd713be` |
| Y-20 | run36 | **REAL DEFECT D1** | see below; left failing | — |
| Y-21…Y-24 | run36 | STALE | four "disabled and still registered" checks re-pointed to "removed" (Run 96); two non-vacuity checks added | `bd713be` |
| Y-25, Y-26, Y-27 | run41 | STALE | pinned stamp tails (v42…v70) re-pointed to append-only invariants anchored at v25 | `7822878` |
| Y-28 | run41 | STALE derivation | package-delta union stopped at v19; now reads every link v13 onward; residual failure is **D2** | `7822878` |

Every re-point and repair was proven able to fail by injection (Y-14 four faults → 218/222;
run36 three injections → 36/43; run41 injections → 30/33, 29/33) and restored.

### Real defects for a ruling

**D1 · A6.2 Safety Performance contradicts itself.** `app/simulation/parameters.py:325` lists
A6.2 in `_LADDER_ONLY` ("an unsourced band ladder"), so `parameter_provenance("A6.2")` is class
`UNSUPPORTED`. The reading published through `CAT89_CANONICAL` bands Amber with
`band_provenance_class` `CODIFIED`, `threshold_source` `owner_configured_default`, and a
`band_boundary` stating the recordable-rate formula and benchmark are codified with the owner's
multipliers 0.75 / 1.0 / 1.5. I confirmed the `_LADDER_ONLY` entry on `main`. Fix stated, not
applied: either move A6.2 out of `_LADDER_ONLY` into its own `PARAMETER_PROVENANCE` row matching
what the reading publishes, or rule the benchmark not codified and stop A6.2 banding. Check
A6.3 and A6.4 the same way; Run 133 named all three as overridden by `CAT89_CANONICAL`.

**D2 · three governed participant-package bytes moved with no successor link declaring them.**
Of 70 governed files, 28 moved; 25 are declared across links v13→v14 … v26→v27 in
`tools/participant_packages.py`. Undeclared: `assets/js/assistant.js` (Run 106, `2d0ff85`),
`assets/js/config.js` (Run 94b, `bdc37e2`), `assets/js/files.js` (Run 127, `6235050`). The
six sequence-bearing files are not implicated (that check passes). Fix stated, not applied: the
owner decides per file whether the edit was participant-visible; each such run owes a declared
delta at its link, or one successor re-baselines all three. The v13 record is evidence and is
not to be edited.

## Item 4 — `packages_due` bare alias — RESOLVED, attempt 1

`server/app/documents.py` `_TD_COLS`: `"packages"` removed from the `packages_due` aliases,
with F8's reasoning recorded beside it. A column headed only "Packages" states no period and no
status, so it may be every package in scope, a superset. The error direction is unfavourable
(larger denominator bands the firm worse) and it is removed anyway: the recorded position on an
adjacent quantity carries no direction, and the honest alternative is already in the factor
(no denominator reads UNAVAILABLE, not Green). Proof: `_first_of({"Packages": 100}, aliases)`
returned 100, now returns `None`; restoring the alias returns 100. `test_run136a_remaining_h1_copies`
23/23. Every heading that states the population is untouched.

## Item 5 — the F6 archived-row count

Read-only. Executed only against a throwaway SQLite (I re-ran it; it parses and returns no rows
on empty tables). Clearing the rows belongs with the v70 recomputation, not ahead of it.

**Command** (`$DATABASE_URL` from the environment; no credential on the command line):

```
psql "$DATABASE_URL" -f run137_f6_archived_rows.sql
```

Add `--csv` to keep the result as a file.

```sql
-- RUN 136, F6. Rows ALREADY PROJECTED from a document the document control has ARCHIVED.
-- H4 (Run 135) stopped NEW rows being projected for an archived document. It did not remove
-- rows projected before that. This is the count. IT DELETES NOTHING.
-- The archive mark lives on document_uploads.archived_at and is scoped to (project_id, period);
-- documents is shared content-addressed storage, so every join matches all three keys,
-- exactly as _archived_document_ids does.

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

ORDER BY 1, 2, 3;
```

| column | meaning |
|---|---|
| `store` | which projection or observation store the row was counted in |
| `project_id`, `period` | the scope of the archive mark; a document archived in one period may be live in another |
| `rows_from_archived_documents` | rows in that store, for that project and period, projected from a since-archived document. This is the F6 number |
| `archived_documents` | distinct archived documents those rows came from |

An empty result means H4 closed the door before anything came through. The two observation
lines are separate because `observations.withdrawn_at` (migration 0029) is already an archive
mark on the row itself.

## Decisions outstanding for the owner

1. D1: reclassify A6.2's parameter row, or stop it banding (and check A6.3, A6.4).
2. D2: which of `assistant.js`, `config.js`, `files.js` were participant-visible; declare or re-baseline.
3. X-1: `assert_retained_adaptation_not_reachable` — assert A1.1 refused as absent, or find a live subject.
4. X-2: driver seeds its predecessor state, or the fleet declares an ordering.
5. Whether to raise `--browser-timeout` for the 45 Playwright scripts (fleet wall-clock cost).
6. Run the F6 SQL against production and report the count.
7. The v70 recomputation trigger, unchanged from Run 136.

## Commits this run

`a153eba` `7f5293d` `fd90737` `d6a193d` (X, Items 2 and 1) · `3bd0069` `7987daf` `1fa9c19`
`622a77a` `bd713be` `7822878` `36000fc` (Y) · `e7f6672` merge · `be09743` `9a841c6` (X) · this
report.
