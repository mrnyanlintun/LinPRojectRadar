# Charts from stored results: what closes, what stays open

**Leading with the split the brief asked for.**

- **Fed by stored data, rebuilt and verified this session/prior session:** the Signal Sphere
  (`signalWebHtml`/`wireSignalSphere`, `assets/js/detail.js`) — the one real per-module chart
  surface on the live Signals tab that gated on `simulationSignals`/the legacy blob and rendered
  nothing on a server-computed project. Fixed to gate on `LinResults.hasResult(project)` and tally
  from `getModuleStatus()`, the same pattern `ensembleHtml`/`ensembleTally` already used.
- **Confirmed already correct, no fix needed:** Ensemble Analysis (`ensembleHtml`/
  `wireEnsembleScatter`), Project Signal Network (`projectnet2d.js`), Signal Flow
  (`neural_flow.js`) — all three already read `getModuleStatus`/`getCategoryStatus`, i.e. the
  stored row, as their primary or only path.
- **Architecturally blocked, correctly abstaining, needs a specific follow-up to close:**
  cross-period trend charts and the trajectory classifier (D1.3) — both need a real `history`
  argument threaded through `server/app/documents.py` -> `compute_portfolio`, which today is always
  passed the literal `None`. That's a `server/app/documents.py` + `server/app/simulation/
  portfolio.py` change, not a front-end one.
- **Confirmed dead code, not a live gap:** `simLedgerRow()` in `assets/js/app.js` — a sixth
  "Simulation signals" ledger row that reads `project.simulationSignals` directly and would have
  the exact same permanently-blank defect as the old Signal Sphere gate, **except it is never
  called from anywhere** in `app.js` or any other file. It is orphaned code left over from an
  earlier refactor, not a chart currently reachable on any live screen. Confirmed by grepping every
  `.js` file for the function name; the only hit is its own definition. Not fixed, because there is
  nothing to wire it back into without inventing new UI the brief didn't ask for — flagged instead.
- **`deepdive.js`'s ~101 explainer panels:** confirmed, on a second pass, to be illustrative
  worked-example panels (synthetic walkthrough figures such as "RFI rate 3.2/week" next to a live
  status pill), not claims about the loaded project, and — separately confirmed this session — this
  file **is not even loaded on the live application page** (`index.html` loads `taxonomy.js` in
  its place; `deepdive.js`/`sim.js`/`simulations.js` are only loaded by `research/deepdive.html`,
  per the `T6 Part 3` comment at `detail.js`'s `d-stack` lazy-init, which falls back to a plain
  "not shown here" note on the live app). Correctly out of scope, as found previously — and now
  additionally confirmed unreachable from the surface the brief means by "the Signals tab".
- **The spi/cpi-as-raw-ratio-on-a-percent-delta axis bug the brief describes: not found anywhere in
  this codebase, after a documented broad search this session (see Part 3).** The one place spi/cpi
  are plotted as literal ratios (`render_82` in `charts3d.js`) uses a matching ratio-scaled axis and
  entirely hardcoded illustrative data, and `charts3d.js` is inside the same not-loaded-on-the-live-
  app surface as `deepdive.js`. The server's actual D1.2 (`Portfolio_Outlier`) module — the
  plausible source of a "spi/cpi feeding a chart" claim — outputs **percentiles** (`cpi_percentile`,
  `spi_percentile`, 0-100), not raw ratios, confirmed by reading `server/app/simulation/
  portfolio.py` directly. No live chart plots raw spi/cpi against a percent-delta-from-100 axis.

## Part 1 — what the stored result can supply, chart by chart

Per `REPORT_2026-08-02_stages-7-8-audit.md` (D7.1) and `REPORT_2026-08-02_storage-redesign.md`:

| Surface | Needs | Stored result has it? |
|---|---|---|
| Per-module status (Signal Sphere) | one status per module | **Yes.** Fixed the prior session, re-verified by fault injection this session. |
| Per-category status (Ensemble Analysis / Project Signal Network) | one status per category | **Yes.** Already read correctly. |
| Signal Flow (`neural_flow.js`) | one status per module | **Yes.** Already reads `getModuleStatus()` as its primary path; falls back to the (always-empty) legacy `simulationSignals` array only when `getModuleStatus` returns null, which degrades to a harmless "no data" bucket, not a false value. |
| Cross-period trend / trajectory classifier (D1.3) | a real `history` list | **No.** `documents.py`'s only caller of `compute_portfolio` passes `None`. Abstains correctly by absence (a documented, deliberate divergence from the validated Apps Script, which used to emit a false "Green" here) — closed in the analytical layer, stays visually absent until a second caller assembles real history. |
| "Simulation signals" ledger row (`simLedgerRow`, `app.js`) | — | **N/A.** Not called anywhere; not a live surface. |

## Part 2 — this session's search for surfaces beyond Signal Sphere/deepdive.js

**Method** (documented per the brief's instruction): grepped every file in `assets/js/` for
`simulationSignals`, `dd-chart-canvas`, `wireChart`, and canvas/bar-draw patterns; read every
render path found; cross-checked what `index.html` actually loads (`taxonomy.js`, not
`categories.js`/`simulations.js`/`sim.js`/`deepdive.js`) against what each file assumes is loaded;
traced every call site of every function found back to whether it is reachable from `LinDetail`'s
section list or any other entry point the live app calls.

Files touching `simulationSignals` directly: `app.js`, `categories.js`, `charts3d.js`,
`deepdive.js`, `detail.js`, `forcenet.js`, `neural_flow.js`, `signals.js`, `simulations.js`,
`store.js`.

- `categories.js` and `simulations.js` are **not loaded** by `index.html` — `taxonomy.js` and no
  simulation-running module replace them (confirmed by grepping `index.html`'s `<script>` list).
  Their `simulationSignals` reads are dead in the live app.
- `forcenet.js` **is** loaded, and `LinForceNet.updateFromProject()` reads `simulationSignals`
  directly (would have the exact same gate bug) — but `LinForceNet.init()` is never called from
  anywhere, and no container/canvas for it exists in `index.html` or `detail.js`'s section list.
  It is loaded but inert; the one call site that reaches `updateFromProject` (`signals.js:787`, the
  legacy client-compute path) is itself part of a flow whose output (`project.simulationSignals`)
  the server never populates, so this never fires with real data on a server-computed project
  either. Not a live gap; flagged as further dead weight worth removing in a cleanup session, not
  fixed here (out of scope — no visible surface to repair).
- `neural_flow.js`'s Signal Flow panel — **live, real, rendered on the Signals tab** — was checked
  line by line. `modInfo()` calls `window.getModuleStatus` first (the stored row) and only falls
  back to the local `simulationSignals`-derived `byClass` map when that returns null. Since
  `getModuleStatus` returning null and `simulationSignals` being empty both mean "no data", the
  fallback is a no-op in practice, not a silent wrong-value path. No fix needed; verified, not
  assumed.
- `projectnet2d.js` ("Project Signal Network") reads `getCategoryStatus`/`getModuleStatus`
  exclusively — no `simulationSignals` reference at all. Confirmed correct.
- `app.js`'s `simSummary()`/`simLedgerRow()` — see the lead-in above: real bug shape, zero live
  call sites. Confirmed dead by grep across every `.js` file for `simLedgerRow(`.
- `charts3d.js` — the rendering library `deepdive.js` uses. Not loaded by `index.html`. Its one
  spi/cpi scatter (`render_82`) is fully synthetic (`P01`..`P09`, hardcoded).

**Conclusion, stated plainly as the brief asked**: after this search, Signal Sphere was the only
live chart surface with the render-gate defect. No second per-category/per-module chart surface
exists on the live Signals tab that still needs the same fix.

## Part 3 — the ensemble scatter axis search

Searched: `assets/js/detail.js` (`ensembleHtml`, `wireEnsembleScatter` — plots module status
severity, not spi/cpi, confirmed by reading the `SY` map), `assets/js/charts3d.js` (every function
referencing `cpi`/`spi`; only `render_82` plots them as coordinates, against hardcoded data),
`assets/js/simulations.js` and `deepdive.js` (spi/cpi appear only in prose/bar-impact
calculations, never as scatter axis coordinates), `assets/js/knowledge.js` (formula documentation
text only, not a chart). Grepped for `delta`, `% from 100`, `axis` near `spi`/`cpi` across all of
`assets/js/` — no match describing a percent-delta-from-100 axis anywhere.

Read the server side directly rather than trusting a fixture: `server/app/simulation/portfolio.py`
`compute_portfolio()` builds its internal vector as `[cpi, spi, docRiskScore, pctComplete/100]` —
raw ratios internally, as the brief describes — but what it **returns** for `Portfolio_Outlier`
(D1.2), the module actually surfaced to a chart, is `cpi_percentile`/`spi_percentile`
(0-100 percentiles, via `cpi_rank`/`spi_rank`), not the raw ratio. Nothing downstream of that
return value is a raw-ratio scatter.

**Conclusion**: this bug is not reachable in the current codebase. Either it was already fixed
(the D1.2 percentile transform looks exactly like what a "raw ratio vs. percent-delta axis"
mismatch would have been fixed into), or the brief describes a chart that isn't rendered anywhere
today. A follow-up session should ask Lin to point at the exact screen before any further attempt —
guessing again risks the same non-result.

## Part 4 — abstention testing (new this session)

Added to `tests_render.html` Group 11, directly against the real fixture (a stored row with only
2 of ~100+ defined modules present, i.e. every other module is a genuine "no stored result for this
module" abstention, not a fabricated edge case):

- The Signal Sphere's own "N active" subtitle equals exactly 2 (the 2 modules that actually
  computed), never the full module count — abstaining modules are not counted as active.
- Red + Amber + Green in the Signal Sphere footnote sums to exactly 2 — no abstaining module leaks
  into any status bucket.
- The Ensemble Analysis panel's "N active modules" eyebrow also equals exactly 2, from the same
  stored row via `ensembleTally()`/`getModuleStatus()` — proving the abstention rule holds across
  both chart surfaces this session touched, not just one.

These sit alongside the pre-existing Group 11 checks that a project with **no** stored result at
all renders no Signal Sphere panel (not an empty canvas, not a zeroed footnote).

## Part 5 — fault injection (new this session)

Two faults were injected against the current code, one at a time, each confirmed to turn exactly
the expected checks red, then reverted and reconfirmed green (`tests_render.html` full run each
time via headless Chromium/Playwright):

1. **Reverted the abstention arithmetic**: in `signalWebHtml`, changed
   `normalizeStatus(status)` to `(normalizeStatus(status) || "Green")` so that an abstaining
   module (`status === null`) is counted as a fake Green. Result: 90/94 (was 93/94), with the 3
   new abstention checks going red exactly as expected (`1 Green counted` failed — actual false;
   active count read `10` instead of `2`; Red+Amber+Green summed to `1` instead of `2`). Reverted
   byte-for-byte (diffed against the pre-fault file); suite returned to 93/94.
2. **Reverted the original Signal Sphere gate fix**: changed the gate back to
   `window.hasSignals && window.hasSignals(project)` (the pre-fix condition). Result: 87/94, with
   every Group 11 check that depends on the panel existing going red (panel absent, canvas absent,
   both tallies absent, both new active-count checks unmatched). Reverted; suite returned to
   93/94.

Both faults are the two failure modes this session's tests are meant to catch — a) an abstaining
module leaking into a status count, b) the whole panel silently vanishing on a server-computed
project — and both are now demonstrated, not just claimed.

`93/94` (was `89/90` before this session's four new checks) — the one remaining red is the same
pre-existing, documented, environment-gated "production read path" check (needs a real signed-in
session token in the tab; unrelated to anything in this diff).

## Part 6 — server test suite (was skipped last session for lack of a venv; run this session)

A Python virtualenv was created at `server/.venv` (gitignored) and `requirements.txt` installed,
plus `httpx` (`fastapi.testclient.TestClient` depends on it but it wasn't pinned in
`requirements.txt` — a pre-existing gap, not introduced here; not touched further since adding it
to `requirements.txt` is outside this task's scope). PostgreSQL 16 was already installed in this
environment but not running; started it only to confirm the app can reach a real Postgres, but the
test suites themselves target SQLite per repo convention (`T6_HANDOFF.md`: "Build a throwaway
sqlite with `alembic upgrade head` and copy it per suite" — a stale/shared db silently swallows
failures as `KeyError`/no `RESULT:` line).

Wrote `server/run_all_suites.sh`: builds one migrated SQLite template via `alembic upgrade head`,
copies it fresh for every `tools/test_*.py` file (never shares a db across suites, matching the
convention exactly), runs each in its own subprocess with `SESSION_SECRET` set, and sums the
`RESULT: N/M` line from each.

**Result: 39 suites, 2196/2196, all green.** Matches the suite/check counts recorded in
`T6_HANDOFF.md`'s most recent prior entry exactly. Nothing under `server/app/` was touched this
session or the prior one, so this is a confirmation run, not a fix — but it is a real, executed
confirmation now, not a stated gap.

## Repository state

Branch `claude/charts-stored-results-s5s90m`. This session's changes: `tests_render.html`
(4 new abstention assertions in Group 11), `server/run_all_suites.sh` (new; its own gitignored
`.venv` is not committed). No `assets/js/detail.js` change this session — the fix from the prior
session (gate + tally rebuild) stands unchanged and was re-verified by fault injection. Nothing
under `server/app/simulation/` touched. `T6_HANDOFF.md` updated alongside this report.
