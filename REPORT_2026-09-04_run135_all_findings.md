# Run 135 — fix every finding from both hunts

**`SIMULATION_VERSION` MOVED: `sim-2026.09-v68` → `sim-2026.09-v69`**, once for the run, in agent A's Group 1 commit, because H1 and H2 change published bands on A1.7 and A1.8 (the two core voting modules) and S1, S5, the sweep's A3.4 find and M3 change published bands on A6.3, C1.3, A3.4 and A2.12. No migration; head `0033_recognition_matches` unchanged.

**Starting commit** `6d9899f`. **Ending commit** `44abd78`. Tree clean. Production Postgres never contacted; no model call made or simulated.

**How the run was executed.** Four agents in four isolated git worktrees, disjoint file ownership, each branch verified by the primary and merged into `main` with `--no-ff` in the order B → D → A → C, then one merge-interaction commit by the primary. Four sub-reports at repo root carry the full per-attempt iteration logs and are part of this report:

- `REPORT_2026-09-04_run135a_cost_modules.md` — Groups 1, 3, 5; the rounded-field sweep
- `REPORT_2026-09-04_run135b_backend_defaults.md` — Group 4, S6
- `REPORT_2026-09-04_run135c_tooling.md` — Group 6; R4 classification
- `REPORT_2026-09-04_run135d_selection_assembly.md` — Group 2

---

## Disposition, every finding

| Finding | Disposition | Attempts | Agent | Commit(s) |
|---|---|---|---|---|
| **H1** CPI rounded at storage | RESOLVED | 1 | A | on branch, merged `74b616d` |
| **H2** A1.8 edge flips with BAC | RESOLVED | 1 | A | ″ |
| **H6** `TCPI: 1` under Yellow | RESOLVED | 2 | A | ″ |
| **H7** `(0%)` under Yellow | RESOLVED | 1 | A | ″ |
| **H5** trade-table superset aliases | RESOLVED | 1 | D | merged `ba84e17` |
| **H3+M4** sha256 selecting values; undefined order | RESOLVED | 1 | D | ″ |
| **H4** archive filter at one seam | RESOLVED | 1 | D | ″ |
| **M5** bare 1/0 as probability | RESOLVED | 1 | D | ″ |
| **S6** backend/browser P80 | RESOLVED | 1 | B | merged `d407241` |
| **S2** missing status → Green | RESOLVED | 1 | B | ″ |
| **S3** missing/zero inputs defaulted | RESOLVED | 1 | B | ″ |
| **S4** zero EV as absence | RESOLVED | 1 | B | ″ |
| **S1** A6.3 rounds before banding | RESOLVED | 1 | A | `74b616d` |
| **S5** source reliability rounds first | RESOLVED | 1 | A | ″ |
| **M1** A3.3 stores rounded index | RESOLVED | 1 | A | ″ |
| **M2** four ladders print across boundary | RESOLVED | 1 | A | ″ |
| **L1** A6.3/A6.4 retired path | RESOLVED | 1 | A | ″ |
| **M3** A2.12 three of six edges | RESOLVED | 1 | A | ″ |
| Five orphaned band sets | RESOLVED (2 wired, 3 verdicts) | 1 | A | ″ |
| `project_posture.py:73,:80` asserts | RESOLVED | 1 | A | ″ |
| **H10** classification + retirement + check | RESOLVED | 1 | C | merged `0f4bca1` |
| **H10** repair of 66 active crashers | **NOT REACHED** | — | C | — |
| **M11** `test_run17_scientific_methods` | **NOT REACHED** (instance of H10) | — | C | — |
| **M13** `test_run34_holdout_provenance` | **NOT REACHED** (instance of H10) | — | C | — |
| **H9** `test_simulation.py` | RESOLVED, 36/36 | 1 | C | `0f4bca1` |
| **H8** A1.7 closure guards | RESOLVED, 15/15 | 1 + 1 merge fix | C, primary | `0f4bca1`, `44abd78` |
| **M6+M7+L2** run19 consistency | RESOLVED | 1 | C | `0f4bca1` |
| **M8** census on unrendered card | RESOLVED | 1 | C | ″ |
| **M9+L7** `or True` tautologies | RESOLVED | 1 | C | ″ |
| **M10** dead fault class | RESOLVED (removed, not restored) | 1 | C | ″ |
| **M12+L6** launch gate | RESOLVED | 1 | C | ″ |
| **M14** generators rewrite sealed evidence | **PARTIAL** — mechanism landed; 130 artefacts not yet routed | 1 | C | ″ |
| **S7** `test_export.py:134` | RESOLVED | 1 | C | ″ |
| **S8** `test_decision_sequence.py:179` | RESOLVED | 1 | C | ″ |
| **S9** run35 report guard | RESOLVED | 1 | C | ″ |
| **L3** `drive_run115.py:450` | RESOLVED | 1 | C | ″ |
| **L4** `drive_run107.py:695` | RESOLVED | 1 | C | ″ |
| **L5** `run18_production_hashes.py:85` | RESOLVED (split) | 1 | C | ″ |
| `run18` re-baseline-or-retire | RESOLVED (split) | 1 | C | ″ |
| `drive_run103_census.py:479` | RESOLVED | 1 | C | ″ |
| `extraction_client.py:829` | RESOLVED | 1 | D | `ba84e17` |
| `compliance_register._HEADINGS` | RESOLVED (three duplicates, not one) | 1 | D | ″ |

**No finding hit the five-attempt cap. No finding is BLOCKED.** Three are NOT REACHED and one PARTIAL, all in Group 6, all named.

## The merge interaction, and one thing C found that qualifies every pre-merge suite result

C repaired H8 to 15/15 on its branch. On the merged main it read 11/15. Cause: **30 tool scripts hardcode `/home/user/LinPRojectRadar/server` on `sys.path`**, so a suite run inside a worktree imports **main's** application, not the branch's. C's 15/15 was measured against pre-A `models_evm.py`. Three of the four failures were the guards correctly refusing to pass vacuously — A's `band_figure` makes display and decision inseparable by construction, so the old "display ≠ canonical" fixture test became untestable; the fourth asserted `vac_pct == VAC/BAC`, the second arithmetic path R1 removed. The primary re-pointed all four under R2 to the invariants A introduced and to Run 114's identity `(1 − 1/CPI) × 100`, proved able to fail by reverting the display to `_round3` and `vac_pct` to the second path (11/15), restored (15/15). Commit `44abd78`.

Consequence for reading this run: **every tool-script result quoted from inside a worktree was measured against main-at-the-time, not the branch.** The primary's own proofs used relative imports from each worktree and stand. All straddling suites were re-run on the final merged main and are green — that is the authoritative result.

## Straddling suites on the final merged main (`44abd78`)

| Suite | Result |
|---|---|
| `test_run135a_cost_and_rounding` | 60/60 |
| `test_run135d_selection_and_assembly` | 48/48 |
| `test_run133_a1_a3_band_contract` | 54/54 (2 expectations re-pointed under R2 — they had pinned H2 as a defect) |
| `test_run132_actual_cost_selection` | 31/31 (2 re-pointed) |
| `test_run126_register_row_count` | 44/44 |
| `test_simulation` (H9) | 36/36 |
| `test_run35_closure_voter_identities` (H8) | 15/15 |
| `test_run34_version_boundary` | 18/18 |
| `backend/test_run135b_group4_defaults` | 23/23 |
| `backend/test_run135b_percentile_parity` | 5/5 |

**`test_run135c_active_suite_completes` was NOT re-run post-merge.** It requires `--run`, which executes all 237 active scripts against the working tree; one of them (`drive_run57_reset_merge.py`) checks an old commit's client files into the tree and leaves them there if interrupted, and M14 is only partially landed so the fleet still rewrites committed artefacts. Running it at the tail of a merge on `main`'s working copy is the wrong place. It is the first step of the next tooling run, on a clean checkout.

## R4 classification (C, committed before any repair)

`server/tools/TOOLS_CLASSIFICATION.csv`, 500 scripts: **active 237 · reader 102 · migration 137 · retired 24.** Produced by `run135c_classify_tooling.py` with the applied rule in each row.

**Active-set coverage (C's branch, pre-merge):** 143 of 237 active tests (60.3%) run to completion — 80 exit 0, 63 complete reporting their own failures, **66 (27.8%) crash before a verdict**, 28 exceed a 120 s cap unmeasured. 5,634 / 5,957 checks (94.6%) pass in scripts reaching a RESULT line. The hunt's original fleet figures could not be reproduced until C found why: under `sqlite+aiosqlite://` 133 scripts die in `MissingGreenlet` because `server/alembic/env.py` drives a synchronous engine. Under plain `sqlite:///` they run.

## New failures exposed by repairing dead suites

- **H9 `test_simulation.py`**: after the import repair, the "at least one module retired" check was replaced rather than repaired — a registry with nothing retired is legitimate; it is now a two-way equality against `registry.retired_modules()`. 36/36 after.
- **H8**: C established the true pre-repair baseline was **9/15, not 10/15** as the hunt reported (verified by stash both sides of A's work).
- **M5** exposed `tools/test_risk_register_and_notices.py:147-148` encoding the defect as correct — `("0", 0.0)`, `("1", 1.0)` — 127/127 → 125/127. **Reported, not suppressed; needs an R2 re-point** (two lines, outside D's scope).
- Pre-existing, unmoved by this run, measured identical at the parent: `drive_run71_document_control` 15/17, `drive_run115` 22/34, `test_run86` 14/16.

## The H1 rounded-field sweep — every instance

Fixed in this run: H1 (`si["cpi"]`, `si["spi"]`), M1 (A3.3), S1 (A6.3, retired path), S5 (C1.3), and two the sweep found — **A3.4** (variance within 0.0005 of its cuts) and the **C1.2 tolerance** at `models_dq.py:252`, which was ten times the rounding step.

**Found and NOT fixed — need an owner:**
- `training_engine.py:1283-84, :1301-02, :1377-78` and `training_debrief.py:43-44` — **second copies of H1**, CPI rounded before use. No agent owned these files.
- `models_fuzzy.py:378, :418` — B2.18 MARCOS and B2.19 CRITIC-TOPSIS band on a `_round3`'d score, and unlike A6.3 they are **not** overridden by a canonical layer.

## Band sets in `band_reference_data.json` that no module read

| Set | Verdict |
|---|---|
| `pert_criticality_bands` | **KEEP** — `drive_run104.py:160` reads it to measure the Run 102→104 reversal |
| `submittal_first_review_rejection_bands` | **wired** — A4.3 now reads it instead of the literal at `models_doc.py:404` |
| `ncr_rate_bands` | **wired** — A4.4 now reads it instead of the literal at `models_doc.py:428` |
| `milestone_slip_ratio_bands` | true orphan — **owner's call to delete** provenanced data |
| `construction_frequency_band_cutoffs` | true orphan — **owner's call to delete** |

## Recomputation required — not triggered

Every period whose `signalInputs` carry `cpi`/`spi` (H1, H3+M4, H4 — six of D's seven changes alter stored inputs); A1.7 and A1.8 on every period (project-status-moving); A3.4 where |variance| is within 0.0005 of 0.05/0.12/0.20; C1.3 where the raw average is within 0.005 of 0.80/0.65/0.50; A2.12 where controlling-path float is fractional in (0,1) or (10,11); category and project postures for every period touched. **Not** A6.3/A6.4 — `CAT89_CANONICAL` overrides both at `models.py:2310`. Rows already projected from archived documents are **not deleted** by H4; clearing them is a separate deliberate act. This must land before the v68 reassembly, which now becomes a v69 reassembly.

## Decisions the owner is asked for

1. **`tools/test_risk_register_and_notices.py:147-148`** — R2 re-point of two expectations that encode M5's defect. Two lines.
2. **H4's superseded-document consequence** — routing three stores through `_period_documents` also stops projecting new rows for *superseded* documents. If they should keep projecting, one-line widening of `_live_document_ids`.
3. **Delete the two true-orphan band sets**, or state they are retained.
4. **Own the four un-fixed H1 copies** in `training_engine.py`, `training_debrief.py`, `models_fuzzy.py`.
5. **`backend/render.yaml`** still describes a Render service with an `OPENAI_API_KEY`; `backend/` is established dead (no page loads it; `models.py:8` and `fusion.py:4` say so). Tear down or not is not visible from the tree.
6. **`server/alembic/env.py`** drives a synchronous engine; C's finding, out of every agent's scope.
7. **30 tools hardcode main's path on `sys.path`** — every per-branch measurement with them is a measurement of main. Fix or accept.
8. **M10** — C removed the dead fault class rather than restore its guard, because restoring would reverse Run 59's markdown-carries-no-authority ruling. Confirm.
9. **`run18_production_hashes.py`** — split: Run 18's freeze comparison retired behind `--verify-freeze`, live registry invariants always run. A live freeze needs a new baseline. Confirm.

## Also established this run

- **`backend/` is dead**, and the earlier port survey caught S6 as a reason not to port while never checking whether the module abstained — S2/S3/S4 passed it entirely.
- **S6 was three percentile definitions, not two**; `run_pert` used `np.percentile`.
- **H5's sweep** found one more superset, `commitments_due` ← `"commitments"`, left because it sits in a denominator and fails unfavourably.
- **`compliance_register` had three duplicated headings**, not one: "status", "closure status", "disposition" all under both `satisfied` and `status`. A "Closed" NCR read as satisfied.
- **H3+M4's R3 design**: keys exhausted and values differ → the platform publishes a figure and **reports the disagreement on `evidenceQualification.material_conflicts`**; it does not abstain. Selection functions factored into explicit business key + tie set + hash, return values unchanged. PERMANENT fields had a second silent gap (earliest as-of vs the old rule's latest), now closed.
- **M4's ORDER BY**: SQL stable base `(doc_type, document_id)`; full order in Python via `document_ordering_key` — tier → dated → `as_of` → doc type → sha256 last.

## Closing

`git status --porcelain` before each merge and before the final commit: empty. Migration head `0033_recognition_matches`. `SIMULATION_VERSION = "sim-2026.09-v69"`. Ending commit `44abd78`; this report follows it.
