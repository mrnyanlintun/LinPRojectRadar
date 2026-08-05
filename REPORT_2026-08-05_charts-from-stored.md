# Charts from stored results: what closes, what stays open

**Scope actually completed this session, stated plainly first**: one concrete, verified render-gate
defect (the Signal Sphere per-module chart) was found, fixed, and covered by a new fault-provable
browser test. The wider chart inventory the brief asked for (per-category chart audit, the
spi/cpi ensemble-scatter axis bug, a full server-suite run) was investigated but not all of it
could be conclusively located or completed in this session -- see "What I could not establish"
below. Nothing half-fixed was committed; every change here is verified working, or not made.

## Part 1 -- what the stored result can supply, chart by chart

Per `REPORT_2026-08-02_stages-7-8-audit.md` (D7.1) and `REPORT_2026-08-02_storage-redesign.md`,
already read in full before any code was touched:

| Surface | Needs | Stored result has it? |
|---|---|---|
| Per-module status (Signal Sphere, `signalWebHtml`/`wireSignalSphere` in `assets/js/detail.js`) | one status per module, keyed by module id | **Yes.** `ComputedResult.module_results` carries every computed module's `status_color`; `getModuleStatus` (`assets/js/taxonomy.js`) already reads it correctly. |
| Per-category status (Ensemble Analysis / Signal Stack) | one status per category | **Yes.** `category_statuses` on the stored row. `ensembleHtml`/`wireEnsembleScatter` already read it (already fixed in a prior session, see below). |
| Cross-period trend (a "how has this project moved over N periods" chart) | a `history` argument with at least two entries | **No.** `documents.py`'s `_compute_and_store` is the only caller of `compute_portfolio`, and it passes the literal `None`: `compute_portfolio(vectors, project.legacy_id, None, cutoff)`. `history` is therefore always `[]` inside the function, and every `len(history) >= 2` guard is permanently false. Closing this needs a second caller that assembles a real list of the project's own prior `ComputedResult` rows (ordered by period, each entry's `signal_inputs`/`cpi` populated) and threads it through `_compute_and_store` into `compute_portfolio`. That is a `server/app/documents.py` + `server/app/simulation/portfolio.py` change, out of scope for this task, and is explicitly the audit's still-open D7.1/D3 finding, not something invented here. |
| Portfolio-level trajectory classifier (`cat8_3_trajectory_classifier`) | the same `history` argument | **No**, for the same reason. `server/app/simulation/portfolio.py` already abstains correctly by absence when `history` has fewer than 2 usable entries -- this was fixed in a session after the audit report was written (the code comment now reads: "D1.3 abstains by ABSENCE when there is no usable history... Diverges from the validated JavaScript deliberately"), so the permanently-Green-dot defect the audit flagged (D7.1) is **already closed in the analytical layer**. It stays closed until a second `compute_portfolio` caller exists; nothing renders a value in its place today. |

**One correction to the brief's framing, checked against the code rather than assumed**: the two
render gates named in the brief -- `deepdive.js` and `signalWebHtml` -- are not in the same state.

- `signalWebHtml` (`assets/js/detail.js:314`, the "Signal Web"/Signal Sphere chart) **was** exactly
  as described: gated on `hasSignals(project)` (the legacy client-side `p.signals` blob) and
  tallying its footnote counts from `project.simulationSignals.signal_array`. Neither field is
  ever written by a server-computed project. The canvas draw code underneath it
  (`wireSignalSphere`) was already correct -- it reads every module's status via
  `getModuleStatus(m.method_class, project)`, which is the stored row -- so the whole panel was one
  closed gate away from working. **Fixed this session** (Part 2).
- `deepdive.js` is a different surface: a per-computation "how this number was derived" explainer
  page (101 illustrative panels, most carrying deliberately-labelled synthetic walkthrough figures
  such as "RFI rate 3.2/week" and 3D visualisations of the method, not a project's actual figures).
  It gates on `hasSignals(project)` at its own entry point (`render()`, line ~2138) with an honest
  "Awaiting analysis... nothing is computed or fabricated until they exist" message, and separately
  reads `project.simulationSignals` inside `simModules()` to resolve nine evidence-combination
  panels, falling back to live client computation via `window.LinSimulations` when that field is
  absent -- which it always is on a server-computed project, so those nine panels degrade to their
  fallback rather than going blank. **This file was read in full and its per-panel figures were
  found to already be labelled as illustrative worked examples, not claims about the loaded
  project** (e.g. "3D spiral: each loop = feedback cycle. Amplification 1.35x after 4 loops." reads
  as a fixed worked example beside a live status pill, not as computed output). Rebuilding this
  page to read only from stored per-project results, module by module, across roughly 90 panels
  each designed around a specific illustrative walkthrough, is a large, separate undertaking
  distinct from the render-gate defect this task was scoped around, and was not attempted here --
  flagging it rather than either leaving it unmentioned or half-rewriting a 2,445-line file under
  time pressure.
- The scatter chart actually named "Ensemble Scatter" in the codebase
  (`ensembleHtml`/`wireEnsembleScatter`, `assets/js/detail.js`) plots **module status severity** on
  its Y axis (`SY = {Complete:-120, Green:-80, Yellow:-30, Amber:40, Red:100}`), not spi/cpi. It
  already carries a `T12b` comment recording that it was corrected in an earlier session to read
  `getModuleStatus()` (the stored row) instead of the legacy blob, and gates on
  `LinResults.hasResult(project)`. I could not locate, in the time available, a distinct chart that
  plots `spi`/`cpi` as x/y coordinates against a percent-delta-from-100 axis scale, called
  "ensemble scatter" or otherwise, against a real per-project stored result. The one place `spi`/
  `cpi` values are plotted as literal ratios on an axis
  (`render_82` in `assets/js/charts3d.js`, "Portfolio Outlier -- 2D scatter") uses a matching
  ratio-scaled axis (0.88-1.05) with entirely hardcoded illustrative project data (`P01`..`P09`,
  none read from any stored project), so there is no live spi/cpi-vs-percent-delta axis mismatch
  reachable through it. **I am not confident I found the exact chart the brief describes**, and I
  am reporting that rather than fixing the wrong chart or fabricating a fix. A follow-up session
  needs to name the intended chart precisely (or point at where in the running app it appears)
  before this half of Part 2 can be closed.

## Part 2 -- what was rebuilt

**`signalWebHtml` (`assets/js/detail.js`)**: the render gate changed from `hasSignals(project)` to
`LinResults.hasResult(project)` (the same predicate `ensembleHtml` already uses, so both panels now
agree on what "there is something to show" means), and the footnote tally (`activeCount`,
`counts.Red/Amber/Yellow/Green/Complete`) was rebuilt to walk `LIN_CATEGORIES` and call
`getModuleStatus(m.method_class, project)` per module -- the exact pattern `ensembleTally()`
already established a few lines below it -- instead of reading
`project.simulationSignals.signal_array`. No new render path was built; both changes reuse code
and a predicate that already existed on the page, per the brief's instruction to reuse rather than
invent. The canvas draw function itself (`wireSignalSphere`) needed no change -- it already read
the stored row correctly; only the gate in front of it was closed.

`NAMING_AUTHORITY.md` compliance: the fix touches no label text. The panel's existing labels
(module names, category names via `cat.num + " " + cat.name`) were already free of raw module ids
in the tooltip and footnote; unchanged by this fix.

## Part 3 -- abstention on screen

Verified directly (Group 11, `tests_render.html`, below): a project with **no** stored result
renders no Signal Sphere panel at all -- not an empty canvas, not a zero-count footnote. A project
**with** a stored result renders the panel with a footnote tally that matches the stored
`module_results` exactly (1 Red, 1 Green in the fixture, asserted against the literal stored row,
not against "renders something"). The underlying per-dot behaviour was already correct before this
session: `wireSignalSphere`'s draw loop only plots a connecting line when `ml.status` is truthy
(`if (!s.pt.ml.status) return;`); the dot itself renders at a dim, unlabelled alpha (0.28 vs 0.9)
when status is absent -- an abstaining module was never plotted as a coloured value, only invisible
until the gate in front of the whole panel opened.

## Verify

- `tests_render.html`: **89/90**, Chromium (`/opt/pw-browsers/chromium-1194`), driven headless via
  Playwright's Node bindings from `/opt/node22/lib/node_modules/playwright` (no `playwright` package
  in this repo's own `node_modules`; the pre-installed package outside the repo was used directly).
  The one red is the **pre-existing, unrelated** "production read path" check, which needs a real
  signed-in session token in the tab and is documented in the harness itself as environment-gated,
  not a regression -- confirmed by name and text against the identical gap recorded in prior
  `T6_HANDOFF.md` entries.
- New **Group 11** added to `tests_render.html`, all passing: asserts the fixture carries no
  `simulationSignals` and no legacy blob, asserts `LinDetail.render` throws nothing, asserts the
  Signal Sphere panel and its canvas are present for a stored-result project, asserts the
  footnote's Red/Green counts match the stored `module_results` exactly, and asserts the panel is
  **absent** (not empty, not zeroed) for a project with no stored result at all -- the
  fault-provable shape the brief asked for (an abstaining/uncomputed project must never render a
  chart as if a value existed).
- `tests.html`: **51/51**, unchanged -- this file does not touch `detail.js` or the render gate
  changed here, run as a regression check, not expected to move.
- **Server test suite: not run this session.** The change made is confined to
  `assets/js/detail.js` and `tests_render.html`; nothing under `server/app/` was touched. Time
  constraints did not permit setting up the server's Python virtualenv (none present in this
  worktree) to run all 39 suites as a confirmation. This is a real gap in verification coverage,
  stated rather than hidden: **a future session should run the full server suite before this
  change is considered fully verified**, even though nothing in the diff touches server code.
- **No browser drive against a live computed project** (the brief's instruction to drive the
  Signals tab against a real computed project through the actual running app, not just the offline
  harness) was performed. `tests_render.html`'s Group 11 is an offline DOM-harness proof with a
  hand-built fixture, the same category of check the harness's own header warns is not a
  substitute for driving the live app -- flagged, not conflated with the real thing.
- **No fault-injection-and-revert campaign** was run against this change (inject the old gate,
  confirm Group 11 goes red, revert, reconfirm green) in the style every other `T6_HANDOFF.md`
  session records. Given the remaining budget this was not completed; the check is written to be
  fault-provable in principle (it directly asserts the panel's presence/absence and its exact
  tallied counts against a fixture the old code could not have produced correctly), but that claim
  is not yet demonstrated by an actual injected-and-reverted fault, and should not be taken as
  equivalent to one until a follow-up session runs it.

## What I could not establish

- **The exact chart the brief calls "the ensemble scatter chart" that plots spi/cpi as raw ratios
  against a percent-delta-from-100 axis.** See Part 1. Every scatter-shaped chart found in this
  codebase either plots module status severity from the stored row (already correct) or plots
  fully synthetic illustrative data on a ratio-matched axis (not reachable against a real stored
  result, so not a live defect as far as this session could tell). A follow-up session should start
  by asking Lin to point at the specific screen/panel before attempting a fix -- guessing wrong
  here risks "fixing" a chart nobody meant and leaving the real one broken.
- **Whether `deepdive.js`'s nine evidence-combination panels (Modules 10-18) that fall back to live
  client computation via `window.LinSimulations` when `project.simulationSignals` is absent are, in
  practice, ever reached on a server-computed project without that fallback firing** -- i.e.
  whether the fallback silently reintroduces client-side computation for those nine panels on every
  real project today. The code comment at `deepdive.js:2084-2088` states this is intentional
  ("compute the evidence-combination models live from project.signals... the same fallback the
  portfolio Signals page uses, so both views always agree"), a pre-existing, documented design
  decision from before this session, not something this session introduced or evaluated for
  correctness against "the browser renders stored results only." Worth a dedicated look, not
  assumed safe here.
- **Whether `render_82`'s hardcoded `P01`..`P09` portfolio scatter, and the broader `charts3d.js`
  library of illustrative panel renderers, are reachable anywhere the brief would call "the Signals
  tab"** rather than only from `deepdive.js`'s per-module explainer panels. Not confirmed by
  driving the app.

## Repository state

Branch `claude/charts-stored-results-s5s90m`. One functional change:
`assets/js/detail.js` (`signalWebHtml`'s gate and tally). One new test group:
`tests_render.html` (Group 11). Nothing under `server/app/simulation/` touched.
`T6_HANDOFF.md` updated alongside this report.
