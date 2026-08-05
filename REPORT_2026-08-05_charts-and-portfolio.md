# Charts and portfolio: three dead surfaces removed, the portfolio list consolidated

**Date:** 2026-08-05
**Branch:** `claude/charts-and-portfolio-s5s90m`
**Method:** source-read + headless Chromium (Playwright, vendored chromium-1194) against the
loaded app context, plus the offline render/math suites and the server suite.

---

## Part 1 — the three chart surfaces that never drew

The platform rule applied to all three: a surface with nothing to show must say so plainly and
never render an empty frame, a zero, or a flat line. In every case the correct outcome was
**removal**, because none had real stored data to draw and each either duplicated a working
surface or depended on research tooling the application does not load.

### 1a. `LinForceNet` (`forcenet.js`) — REMOVED

A 3D force-network canvas of every module across the analytical groups, with inter-group "signal
flow" arrows and status-coloured module dots. Verified dead and removed, not revived, for four
independent reasons:

- **No container exists anywhere.** It draws into `#fn-canvas` (plus `#fn-cat-btns`,
  `#fn-tooltip`, `#fn-stat`, `#fn-btn-all`). None of those ids exist in `index.html` or
  `detail.js`. `init()` is never called from any site.
- **It reads dead data.** `updateFromProject()` reads `project.simulationSignals.signal_array`,
  the legacy client-compute blob the server never writes (same ancestry as the Signal Sphere gate
  bug). Its one call site (`signals.js:787`) sat inside the `window.LinSimulations` client-compute
  path, which `index.html` does not load.
- **It duplicates working surfaces.** A network of groups connected by signal flow with
  status-coloured module dots is exactly what Project Signal Network (`projectnet2d.js`) and
  Signal Flow (`neural_flow.js`) already draw from the stored row.
- **It violates the naming authority.** Hardcoded `"Cat 1".."Cat 10"`, `"PH"`,
  `"FORCE NETWORK — 103 MODULES"` — module numbers in user-facing text.

Removed: deleted `assets/js/forcenet.js`, its `<script>` tag, and the `LinForceNet` call in
`signals.js`. Nothing else referenced it.

### 1b. Portfolio Health modal — control REMOVED

The "Health" control (dock fly-out pill + a "See Portfolio Health" button on the Portfolio Health
ledger row) called `openHealthModal()`, which returned early when `!window.LinDeepDive`.
`deepdive.js` re-runs the models live and is deliberately not loaded by `index.html`, so the
control was a silent no-op and its modal reads no stored data (it recomputes).

Decision: **removed the control** (loading deepdive.js is not trivial; the modal shows recomputed,
not stored, figures). The capability is not lost — Portfolio Health from each project's own stored
result already renders in the "Portfolio health" card (`renderPortfolio` in `workspace.js`,
reading `portfolio_snapshot`). Removed the fly-out pill, the "See Portfolio Health" button and its
wiring (`app.js`), and `openHealthModal()` plus its export (`ingest.js`); corrected two stale
comments.

### 1c. Signal Stack `d-stack` section — REMOVED

Rendered a heading over a static note that always fell through to "not shown here", because it
needed `window.LinDeepDive`. Its data does not exist in the stored result (the deep dive
recomputes; the stored row's module results are drawn by the sections above it). Removed the
section and its lazy-init handler in `detail.js`; updated the section-order comment. No stored
data lost.

**Verification (headless Chromium, app context loaded):** `window.LinForceNet` undefined;
`window.LinIngest.openHealthModal` absent; detail render emits no `d-stack` node. `tests_render.html`
stays 93/94 (the one red is the pre-existing "production read path" check, unrelated).

---

## Part 2 — the portfolio page reorganised

### 2a. Two project lists consolidated into one

Kept `#project-list` (`buildFallbackList`, `app.js`) as the single list — it is universal,
keyboard-accessible, and marker-linked — and merged the membership columns from the operational-
only "Your projects" list (`#ws-project-list`, `workspace.js`) onto it. The join is safe:
`workspaceprojects` returns `project_id === project.legacy_id`, the same identifier `#project-list`
keys on. `workspace.js` now publishes `window.LIN_PM_META` (role/period/computed by code) and calls
`LinApp.buildFallbackList()`, which reads it plus `formattedAddress`/`address`.

The single list carries exactly: **code, name, sector, status, PM, period, computed state,
address, Manage, Open.**

Where each former capability landed:

| Former list | Capability | Now |
|---|---|---|
| Projects (list view) | code, name, sector, status | single list, unchanged |
| Projects (list view) | Manage (inline edit/upload/archive/reset) | single list, unchanged |
| Projects (list view) | Open -> detail | single list, unchanged |
| Your projects | PM role | `.li-pm` column |
| Your projects | current period | `.li-period` column |
| Your projects | computed state (dot + label) | `.li-computed` column |
| Your projects | address / geocode line | `.li-address` column |
| Your projects | Open | already present |

Nothing was outside the required set, so nothing was surfaced-and-dropped. The "Your projects"
card was removed from `index.html`; the now-orphaned `locationLine` helper was removed.
`.list-item` moved from a fixed 5-column grid to flex-wrap so the variable, partly-conditional
columns flow (mobile already used flex; new columns got explicit `order`s).

### 2b. Placement count

No literal double-render found in current source. Each geographic view prints the placement count
once in its own note (`atlas-note`, `globe-note`); the MapLibre view prints only an unplaced-ids
note. The shared status legend shows per-status counts, which is different information, not a
duplicate. Conclusion: the placement count already appears exactly once per view — the duplication
was likely removed by an earlier session or lived on a surface no longer present. Left as-is and
reported rather than guessing at a change (removing either would drop distinct information).

### 2c. Radar / Map / Globe tabs vs the list beneath

The stage toggle switches only the map region; the project list beneath it is always present (the
keyboard path the views' aria-labels reference), not a fourth switched view. Per least-structural-
change, made it consistently a permanent section beneath — structurally already true, so the change
is clarifying: the heading "Projects (list view)" (which read like a fourth view) is now
"Projects", with a comment stating it is a permanent section.

### 2d. Portfolio Health "too small" said once

`renderPortfolio` repeated the same portfolio-too-small message per project. Rewritten to partition
projects into computed (each keeps its own card) and not-computed, emitting the portfolio-level
reason once above the cards. When nothing is computed, exactly one note shows.

**Verification (headless Chromium, app context):** with membership metadata present the single row
carries code, PM, period, computed, address, Manage, Open (asserted from the live DOM); with
metadata absent (research/observer path) the membership spans are gone but code and name remain;
exactly one row per project. A fault injection set the role to "Observer" and confirmed the PM-column
check discriminates (cell read "Observer") — not vacuous.

---

## Part 3 — dead code removed

`simSummary()` and `simLedgerRow()` in `app.js`, confirmed dead by exact-identifier grep across
every `.js`/`.html`: `simLedgerRow` has only its own definition (no call site); `simSummary` is
called only from `simLedgerRow` (now removed). No reference embedded in a longer identifier. Both
removed; `node --check` passes.

---

## Suites

- **Server suite:** 39 suites, **2196/2196** (fresh SQLite per suite). No server files changed —
  confirmation run.
- **`tests_render.html`:** **93/94** (the one red is the pre-existing "production read path" check).
- **`tests.html`:** **51/51.**

## What was driven live, and what was not

Verified in headless Chromium against the loaded app context: the consolidated list's columns and
controls, the two rendering modes (membership present = operational; absent = research/observer),
one-row-per-project, the absence of `LinForceNet`/`openHealthModal`/`d-stack`, and a discriminating
fault injection on the PM column. A full end-to-end dual-account drive against a running FastAPI
server with a seeded fixture and two live session tokens was not stood up this session (the
account/token bootstrap is the heavy step the handoff repeatedly flags); the two account-type paths
were exercised through the metadata-present/absent split, which is exactly what differs between them
on this list. A follow-up wanting the full server-backed dual-account drive should budget the
fixture-and-token bootstrap separately.

## Files changed

`index.html`, `assets/css/radar.css`, `assets/js/app.js`, `assets/js/detail.js`,
`assets/js/ingest.js`, `assets/js/signals.js`, `assets/js/workspace.js`, and
`assets/js/forcenet.js` (deleted).
