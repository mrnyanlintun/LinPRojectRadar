# The cross-period series: assembled from what is already stored

**Date:** 2026-08-05
**Branch:** `claude/period-series-s5s90m` (merged to `main`, commit `afbdee7`)
**Verification:** server suite **41 suites, 2269/2269** (fresh SQLite DB per test file, new `test_period_series.py` adds 40), `tests.html` **51/51**, `tests_render.html` **142/143** (the one red is the pre-existing auth-gated "production read path" check, red on `origin/main` too). Four faults injected against the new suite, each confirmed applied, each detected, each reverted with the baseline re-run green.

**Production has NOT been migrated. No migration was written or needed: this task added no column and no table. No `DATABASE_URL` pointed anywhere but throwaway SQLite, and production was neither inspected nor queried.**

---

## FINDING 1 — What a series can be assembled from today, per module

The premise held. Every reporting period already stores its own figures in one live `computed_results` row (`signal_inputs.cpi`, `signal_inputs.spi`, and the whole module result dict). Nothing needed to be stored that is not stored. What was missing was the join across periods, and there are exactly **two** join shapes the analytical layer can consume:

| Series | Shape the consumer requires | Assembled from | Minimum |
|---|---|---|---|
| `spiHistory` / `cpiHistory` (on `signalInputs`) | a flat list of floats, oldest first | each earlier live result's `signal_inputs.spi` / `.cpi`, then this period's own | 2 points (3 for ARIMA) |
| `compute_portfolio`'s third argument | `[{period, signal_inputs:{cpi, spi}}]`, oldest first | the same rows, in the element shape `portfolio.py` reads and the Apps Script wrote | 2 snapshots |

**The first was already assembled** by `_period_history` (D1) and is not new work. **The second never was**: `compute_portfolio(vectors, project.legacy_id, None, cutoff)` was the only call site and it passed a literal `None`, so both `len(history) >= 2` guards were permanently false on every project ever computed.

Three things a series cannot be assembled from, established rather than assumed:

- **A within-period distribution is not a cross-period series.** `REPORT_2026-08-05_module-charts.md` Group 2 mixes two unrelated deficits. Monte Carlo EAC, PERT Network Criticality, Schedule Risk Analysis P80 and Cost Risk Analysis P80 discard the histogram of their own 5,000/2,000 iterations *inside a single period*. Joining periods gives them nothing: what they threw away never crossed a period boundary. They remain "the server would have to store more per result", and this task does not touch them. Only the trend readers (CUSUM, Kalman, ARIMA, Regression to Mean, Trajectory Classifier) are cross-period, and their series is the join above.
- **Earned Schedule is in that Group 2 list and needs no series at all.** It computes from `actualPctComplete` / `plannedPctComplete` within the period and already computes; its listed "forecast endpoint" is a scalar, not a discarded trend.
- **`milestoneHistory` cannot be assembled** — see Finding 2.

## FINDING 2 — Which modules can now compute, and which still cannot

**Now compute that did not:**

| Module | Was | Is | Available from |
|---|---|---|---|
| Signal Trajectory Classifier (portfolio-level trend) | absent from every stored `portfolio_snapshot`, because `history` was `None` | computes on the project's own stored per-period cpi | the second period |
| Anomaly Score's trend term | the composite was always the three-term average | the trend term joins the composite when a real trend exists | the second period |
| CUSUM, Kalman, ARIMA, Regression to Mean **on training projects** | abstained on every training period ever generated: the series was assembled in `_compute_and_store`, which training never calls | compute, on the training run's own stored per-period figures | 2 periods (3 for ARIMA) |

**Exactly what D1 already covered, established as instructed:** `spiHistory` and `cpiHistory` reached **only the document upload path**. A training run generates its periods through `training.py` `_store_period`, which calls `run_and_store` directly and therefore bypassed the one line that assembled the series. So the four trend readers abstained on every training period, permanently, while appearing wired. Moving the assembly into `run_and_store` — the single function both paths pass through — closes that without changing what any module computes.

**Still cannot compute, and why:**

- **Milestone Trend — NOT closed, and not forced.** Two independent gaps, either one fatal. (1) `milestones_json` is stored on the document row, but the extraction prompt tells the model to use *the table's own column headings as keys and its values as printed* — the real activity table returns `Activity` / `Baseline start` / `Baseline finish`, while the module reads `name` and `forecast`. (2) Dates inside that field are explicitly exempted from `YYYY-MM-DD`, and `_js_date_ms` — the only date parser the module has — accepts nothing else. Bridging either gap means inventing a heading-to-field mapping and a multi-format date parser, i.e. manufacturing the input rather than supplying one. `field_registry.NEEDS` already declares `milestoneHistory` UNSERVABLE; that declaration is still correct and was left alone. The module abstains, correctly.
- **The operational recommendation stays coarse.** It is coarse because it holds no cost or duration for any course of action (`REPORT_2026-08-05_recommendation-options.md`: training can price a decision, operational can only rank one). A cross-period series supplies no price. This task does not move it, and no assembly of stored periods would.
- **A project in its first period abstains everywhere a series is required**, unchanged and asserted. Nothing is synthesised, interpolated or extended to reach a minimum.

**What each requires, stated plainly:** CUSUM 2 periods, Kalman 2, Regression to Mean 2, ARIMA 3, Trajectory Classifier 2 snapshots (and a portfolio of at least two projects carrying signal data, its own separate guard). One period is not a series and never becomes one.

## FINDING 3 — What changed under `server/app/simulation/`

**Nothing. The directory is untouched.** The exception this task granted was not needed: `compute_portfolio` has always accepted `history` as its third parameter and has always guarded it at `len(history) >= 2`. The defect was entirely on the calling side. No module was changed to accept an input, and no module's computation was changed.

One pre-existing staleness noted and deliberately not edited, because editing it would mean opening the directory for no functional reason: `VALIDATION.md`'s trajectory-classifier row still describes the Apps Script behaviour of emitting a status colour beside `insufficient_data: true`, which `portfolio.py` already diverges from on purpose (it abstains by absence). That divergence predates this task and is documented in `portfolio.py` itself.

---

## What was built

`server/app/documents.py` only:

- **`_earlier_live_results(session, project, period)`** — new. The single read every cross-period series is assembled from: `period < period` (evaluated against the period being computed) and `superseded_by IS NULL`, ordered by period. This is the `_period_history` filter promoted to a named function so there is one place the alignment invariant lives.
- **`_period_snapshots(session, project, period, si)`** — new. `compute_portfolio`'s `history` argument: the earlier live results as `{period, signal_inputs:{cpi, spi}}`, oldest first, with the period being computed as the last element. The current period is included for the same reason `_period_history` ends its series with the current value — the trend asked for is the one ending now — and it keeps both assemblies on one rule, so a trajectory becomes available at exactly the period `cpiHistory` does and never before.
- **`_period_history`** — body unchanged; it now calls `_earlier_live_results` instead of running the same query inline.
- **The assembly moved from `_compute_and_store` into `run_and_store`**, before `compute_project`, so both assembly paths (documents and training) receive it. `si["events"]` stays in `_compute_and_store`, because training supplies its own.
- **`compute_portfolio(vectors, project.legacy_id, history, cutoff)`** — the literal `None` is gone.

The series are written onto `si`, which is the dict stored on the row, so a stored result records the series its modules were actually given.

## The acceptance condition, proven

**Recomputing period 1 after periods 2, 3 and 4 exist is byte-identical to the original period-1 result.** Asserted directly in `server/tools/test_period_series.py` section 3, on a real four-period project driven through `projectupload` / `projectcompute` / `adminrecompute`.

What "byte-identical" compares: the stored row's `period`, `signal_inputs`, `module_results`, `category_statuses`, `project_status`, `portfolio_snapshot`, `simulation_version`, `seed`, `period_cutoff` and `source_documents`, serialised `json.dumps(sort_keys=True)` and compared as bytes. `result_id` and `computed_at` are excluded **by name and for a stated reason**: a recompute is a new append-only row and is required to have a new id, so including them would make the check unpassable for a reason unrelated to period alignment. Everything any reader is ever shown is inside the compared payload.

The design makes this reachable rather than lucky: a computation reads only rows with a strictly smaller period, so a later period cannot exist in an earlier period's input set at any wall-clock moment.

## Verification, and proof each check can fail

New suite `server/tools/test_period_series.py`, **40 checks**, five sections: single period abstains everywhere; a real three-period series computes and its figures match the stored periods exactly (the trajectory trend is recomputed independently from the stored rows, not read back from the module); the byte-identical acceptance condition; no series from a later period, asserted at every one of four periods against a fixture whose four cpi values are all different so a wrong-period series cannot match by coincidence; and live-rows-only with superseded rows actually present in the table.

Four faults, each anchor asserted to match exactly once, each confirmed applied before the run, each reverted with a SHA-256 comparison against the original file:

| Fault | Result |
|---|---|
| `period < period` becomes `period != period` (the P1 shape) | **28/40** — turns the byte-identical check red, first difference at byte 46 |
| `history` passed back as a literal `None` | 37/40 |
| the snapshot series fabricates a second point from the current value | 32/40 |
| superseded rows no longer excluded | 32/40 |

Baseline 40/40 before and after every fault. The first fault is the one that matters: it proves the acceptance condition is a check that can fail, not an assertion.

## Files changed

`server/app/documents.py`, `server/tools/test_period_series.py` (new), `T6_HANDOFF.md`, this report. **No file under `server/app/simulation/` was modified.** No front-end file was modified: `workspace.js` already renders whatever keys the stored `portfolio_snapshot` holds, so the trajectory row appears with no browser change.
