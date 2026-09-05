# Run 136 — finish what Run 135 left

**`SIMULATION_VERSION` MOVED: `sim-2026.09-v69` → `sim-2026.09-v70`**, once, in agent A's F1 commit, because F1 changes what a published band rests on at B2.18 MARCOS and B2.19 CRITIC-TOPSIS, which are not overridden by any canonical layer. No migration; head `0033_recognition_matches` unchanged.

**Starting commit** `cd98235`. **Ending commit** `7ba00dd` (this report follows). Tree clean. Production Postgres never contacted; no model call made or simulated.

**Execution.** Baseline fleet first, alone, on a clean worktree at `cd98235`. Then agent A (F1–F8) in a worktree, verified by the primary with relative imports, merged `--no-ff`, every tool-script number re-taken on main. Then agent B (F9–F11) **on main directly**, alone, so every number it took is authoritative. Two sub-reports at repo root carry the full per-attempt iteration logs and are part of this report: `REPORT_2026-09-04_run136a_remaining_findings.md`, `REPORT_2026-09-04_run136b_tooling.md`.

---

## The completion-check baseline, and the figure after

Taken with `tools/test_run135c_active_suite_completes.py --run --timeout 120`, one shared throwaway SQLite, on `main`:

| | complete | exit 0 | reported failures | crash / timeout |
|---|---|---|---|---|
| **Baseline** — `cd98235`, v69, before this run | **149 / 237 (62.9%)** | 94 | 55 | **88** (77 crash + 11 timeout) |
| **After** — `7ba00dd`, v70 | **155 / 237 (65.4%)** | 97 | 58 | **82** |

+6 complete, −6 crashing, **empty regression set**. Five are repairs; `drive_run75_empty_period.py` is a browser driver that fell the other side of the 120 s cap — variance, not a fix. Run 135 C's pre-merge figure (143 / 66 / 28 over-cap) was taken before four merges landed and is not comparable.

**The `sys.path` constraint, recorded.** 30 tool scripts hardcode `/home/user/LinPRojectRadar/server`; a suite run from a worktree imports main's application. Every tool-script number in this report was taken on the final merged `main`. One correction from A: `test_risk_register_and_notices.py:36` sets `sys.path` from its own `__file__`, so its worktree result did test the branch.

## Whether the harness cause accounted for most of the 88 — no; Run 135 named the wrong one

`alembic/env.py`'s synchronous engine is real, reproduced, fixed (F9-a) and proven able to fail again — and it accounts for **0 of the 88**. The baseline ran under a plain `sqlite:///` URL and no script names an async driver.

**The fault that does account for a large share: the fleet gives all 237 scripts one shared database.** Drivers bootstrap "the" ResearchAdmin by role and then sign in with their own hardcoded code; `a_researchlogin` refuses the mismatched pair (correctly — collapsing the two failure messages is a documented anti-probing property at `app/research_identity.py:254`), and the driver reads `session_token` off an error dict. Four of five sampled crashers complete **unedited** on a fresh database. `--fresh-db` was added to the completion check, **off by default** so the coverage figure stays comparable with its baseline.

**Cause buckets of the 88:** retired-id `MissingModuleError` 20 · retired-id `KeyError` 11 · **auth-token collision 17** · timeout 11 · `portfolio`/`portfolio_health` removed in Run 97 14 · other 15. 45 of the 88 drive a browser.

---

## Disposition, every finding

| Finding | Disposition | Attempts | Agent | Notes |
|---|---|---|---|---|
| **F1** B2.18/B2.19 band a rounded score | RESOLVED | 1 | A | stamp → v70; sweep 400,001 + 12,003 points, 0 misbands after, 940 + 1,500 with fault reinjected |
| **F2** CPI rounded, training engine | RESOLVED — **LIVE** | 1 | A | `/exec` → `main.py:305` → `TRAINING_ACTIONS`; second fault found beneath it — `training_engine._round3` was half-to-even against the platform's half-up |
| **F3** CPI rounded, training debrief | RESOLVED — **LIVE** | 1 | A | debrief printed 0.85000 and 0.85004 identically |
| **F4** test encodes M5's defect | RESOLVED | 1 | A | 127/127 → 129/129 on main with DB; expectations sourced from D's M5 rule, not the function |
| **F5** superseded vs archived | RESOLVED, **no change — the code settles it** | 1 | A | `_live_document_ids` docstring: "ONE DELIBERATE CONSEQUENCE, STATED RATHER THAN DISCOVERED LATER"; widening reopens the sha256 tiebreak `_period_documents` records |
| **F6** already-projected archived rows | SQL written and proven on SQLite; **production count OUTSTANDING** | 1 | A | nothing deleted; count needs the owner to run it |
| **F7** two orphan band sets | RESOLVED | 1 | A | repo-wide search first; `pert_criticality_bands` kept |
| **F8** `commitments_due` ← `"commitments"` | RESOLVED | 1 | A | position recorded at `contractor_factors.py:530` and `extraction_fields.py` ("stated, never derived") applies to denominators too |
| **F9-a** `alembic/env.py` async engine | RESOLVED | 1 | B | real, fixed, accounts for 0 of the 88 |
| **F9-b** shared-database harness fault | RESOLVED (harness half) | 1 | B | `--fresh-db`, off by default; ~36 scripts' own hardcoded codes are the script half |
| **F9-c** `PORTFOLIO_VALIDATED` derived from the registry | RESOLVED | 1 | B | six files, one shared edit |
| **F9-d** the ~60 remaining crashers | **NOT REACHED** | — | B | shape and crash line recorded per script |
| **F11 / M11** `test_run17_scientific_methods` | RESOLVED | 2 | B | crash → 214/231; the import alone reached 133 — the truthiness `_SUPPRESSED` test was eating a further **98** checks |
| **F11 / M13** `test_run34_holdout_provenance` | RESOLVED | 1 | B | → 41/41, 27 revived |
| **F10** generator routing | **PARTIAL** — the fleet's writers, not all 130 | 1 | B | baseline fleet dirtied 21 committed CSVs; end-of-run fleet dirtied 4 CSVs + 7 PNGs, none of the 21 |

**No finding hit the ten-attempt cap. One BLOCKED, needing no ruling:** the login-collision's production half at `app/research_identity.py:254` is correct as written; the repair belongs entirely in the scripts. `git diff e29fb2c..7ba00dd -- server/app` is empty.

## Every new failure exposed by repairing a dead script — findings for the next run, nothing silenced

- **`test_run17_scientific_methods`, 17 failures at 214/231:** GATE ×3; 1.5, 1.6, 1.9 calibration bands; 6.2; 6.3 ×4; 6.4 ×4; ARCH duplicate lineage; FAULT Cat-9 raw bypass.
- **`test_run36_fault_guards`:** 7.
- **`test_run41_preservation`:** 4.
- **`drive_run105.py`** reaches `KeyError: 'A2'` at line 227 on its own database.
- **`test_run36_instrument_qualification`** still crashes on `MissingModuleError: A1.1`.
- **`run32_closure_browser_verification`** now `ConnectionRefused`; **`test_run14_mismatch_remediation`** now `PortfolioModuleError`.
- From A: `packages_due` carries the identical bare alias `"packages"` (F8's shape, not fixed — no bundling); `extraction_fields.py` still documents `inspections_passed` and `commitments_met` as recognised headings though H5 removed them.

## Whether the training path executes — yes, both

F2 and F3 are **live**: `/exec` → `main.py:305` → `TRAINING_ACTIONS` → `training_engine` / `training_debrief`. Both enter the recomputation set.

## F6 — the count of already-projected rows from archived documents

Not obtainable from this container. A wrote the SQL against `schedule_activities`, `project_risks`, `project_notices` and the observation store joined to `document_uploads.archived_at`, proved it runs on a migrated throwaway SQLite, and it is in `REPORT_2026-09-04_run136a_remaining_findings.md` §F6. **The owner must run it against production to get the number.** Nothing was deleted. Clearing belongs with the recomputation, never before it, and is not covered by recomputation alone.

## What the v70 recomputation must now cover

Everything Run 135 listed for v69, plus: **every stored B2.18 and B2.19 reading** (F1); **every training period's computed result, recommendation basis and debrief** (F2, F3 — live); **A6.4 factors whose denominator came from a bare "Commitments" column** (F8). F6's rows are additionally a deliberate clearing act, counted first. Not triggered; left to the owner.

## Decisions the owner is asked for

1. **Run the F6 SQL against production** and report the count before any clearing.
2. **`packages_due` ← `"packages"`** — same shape as F8, same recorded position applies; fix or accept.
3. **The ~36 drivers with hardcoded login codes** — repair each to bootstrap its own participant, or accept `--fresh-db` as the standing fleet mode (which changes the comparability of every future coverage figure).
4. **The 17 + 7 + 4 exposed failures** in the three revived suites are unruled findings against modules 1.5, 1.6, 1.9, 6.2, 6.3, 6.4 and the Cat-9 gate. They need a hunt-style run of their own, not a fix-in-passing.

## Closing

`git status --porcelain` before each commit: only the intended files (pasted in the sub-reports). Migration head `0033_recognition_matches`. `SIMULATION_VERSION = "sim-2026.09-v70"`. Ending commit `7ba00dd`; this report follows it.
