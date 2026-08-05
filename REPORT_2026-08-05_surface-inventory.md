# Surface Inventory — Opus Gubernatio
**Date:** 2026-08-05
**Branch:** main
**Method:** source-read + browser-probed (headless Chromium, Playwright, dev server port 8020, SQLite fixture seed)

---

## Part 1 — Call-out Categories

### UNREACHABLE — surfaces that exist in source but cannot be reached by any user

| Surface | Location | Reason |
|---|---|---|
| `simSummary()` render path | `assets/js/app.js` lines 1441-1579 | Gates on `result.simulationSignals` — a field the server never writes to `ComputedResult`. Dead code. [source-read] |
| `simLedgerRow()` render path | `assets/js/app.js` lines 1580-1629 | Same gate. Never called by any live path. Dead code. [source-read] |
| Portfolio Health modal | `assets/js/ingest.js` line 616; dock flyout "Health" pill | `openHealthModal()` returns early when `!window.LinDeepDive`. `deepdive.js` is not loaded by `index.html`. Clicking "Health" is a silent no-op. [source-read] |
| Signal Stack deep-dive content | `assets/js/detail.js` lines 1016-1019 (`d-stack` section) | Shows only a static note because `window.LinDeepDive` is undefined. [source-read] |

### DUPLICATED — the same data shown in more than one place simultaneously

| Data | Locations |
|---|---|
| Project overall status (RAG) | Portfolio list row + detail page header + Project page Signals tab dots |
| Per-category statuses | Detail page d-web spider labels + Project page Signals tab dot grid |
| Uploaded document list | Project page Files tab + Project page Documents tab |

### ORPHANED — reachable pages with no navigation link from the application

| Surface | URL | Notes |
|---|---|---|
| Module Deep Dive | `research/deepdive.html` | Not linked from `index.html`. Source comment: "NOT LINKED FROM THE APPLICATION." Loads categories.js, sim.js, simulations.js, deepdive.js — scripts deliberately excluded from the main app. Requires manual URL entry. [source-read] |

### STALE — surfaces present in the UI but non-functional due to known unresolved issues

| Surface | Location | Issue |
|---|---|---|
| "Commit preliminary judgment" button | Project page Decision tab; `decision-ui.js` line 459 | Calls `window.confirm()`. In headless/automated contexts returns false and silently skips. [source-read] |
| Auditor dock button | `data-nav="auditor"` | CSS hides `[data-page="auditor"]` when `body.og-no-auditor` but does NOT hide the dock button. Users with auditor flag off see the button but get a blank page. [source-read] |
| Consent DRAFT banner | `#lin-consent` | Placeholder copy not yet IRB-approved is live in the product. [source-read] |

---

## Part 2 — Page-by-Page Map

### Pre-auth surfaces (shown before login completes)

#### Login screen — `#lin-login`
- **Who sees it:** All visitors before authentication.
- **What it shows:** Google Sign-In button; platform wordmark.
- **Data source:** None (static HTML).
- **Renders:** Yes. [browser-probed]

#### Access Denied — `#lin-access-denied`
- **Who sees it:** Authenticated accounts not yet enrolled in any study.
- **What it shows:** "Access denied" message, sign-out link.
- **Data source:** Static HTML; auth state from auth.js.
- **Renders:** Yes. [source-read]

#### Consent screen — `#lin-consent`
- **Who sees it:** Research participants who have not yet consented.
- **What it shows:** Study overview, DRAFT consent text (see Stale above), "I agree" button.
- **Data source:** Static HTML; consent state persisted server-side via `/exec consent`.
- **Renders:** Yes. [source-read]

#### Participant profile overlay — `#profile-overlay`
- **Who sees it:** Research participants after consent, before first use.
- **What it shows:** Demographic form (age bracket, field, experience, prior PM tool use).
- **Data source:** Submitted to `/exec profile`.
- **Renders:** Yes. [source-read]

---

### Portfolio page — `data-page="portfolio"`

**Who sees it:** All authenticated users (first page after login for most roles).

#### Stage area — four mutually exclusive visualisations

| Mode | Element | Chart type | Data source | Renders |
|---|---|---|---|---|
| Radar | `#stage-radar` | 2D SVG radar/scatter | Stored `ComputedResult` category scores | Yes [source-read] |
| Atlas | `#stage-atlas` | Flat SVG world map (dots) | Project location field | Yes [source-read] |
| Globe | `#stage-globe` | WebGL 3D globe (charts3d.js) | Project location field | Yes — charts3d.js IS loaded by index.html [source-read] |
| Map | `#stage-map` | SVG choropleth | Stored results by region | Yes [source-read] |

#### Status legend
RAG key (Red / Amber / Green / Unscored). Count badges driven by portfolio results. [source-read]

#### Project list
Scrollable cards: name, status badge, score. Data: `/exec portfolio` action → `portfolio_snapshot`. Filters by search box and status toggle. [source-read]

#### Portfolio flyout (via "..." on a project card)
Pills: Open, Archive, Health. "Health" calls `openHealthModal()` — silent no-op (see UNREACHABLE). [source-read]

#### ws-fold section

| Tab | Content | Data source |
|---|---|---|
| Create | New project form — **hidden for research accounts** | `/exec createproject` |
| Your projects | Compact owned-project list | `portfolio_snapshot` |
| Portfolio health | Summary health table — button triggers no-op | `portfolio_snapshot` |

---

### Detail page — `data-page="detail"`

**Who sees it:** All users; opened by clicking a project. 11 collapsible sections, lazy-loaded on expand.

| Section | Label | Chart / content | Data source | Renders |
|---|---|---|---|---|
| `d-globe` | Location | Flat SVG dot on atlas map | project `location` field | Yes [source-read] |
| `d-projnet` | Project Signal Network | 2D force graph (projectnet2d.js) | stored signal edges | Yes [source-read] |
| `d-neural` | Signal Flow | Animated neural flow (neural_flow.js) | signal weights | Yes [source-read] |
| `d-brief` | Executive Brief | AI-generated prose (streamed) | `/exec chat` — requires chat flag | Yes if flag on [source-read] |
| `d-decision` | Governance Decision | Decision form and history | `/exec decision*` | Yes [source-read] |
| `d-web` | Signal Web | SVG spider + WebGL sphere (charts3d.js) | stored category scores | Yes [source-read] |
| `d-ledger` | Signal Inputs | Table of raw signal values and weights | stored ledger rows | Yes [source-read] |
| `d-docsignals` | Documents & Extracted Signals | Doc list + per-doc signal chips | stored doc signals | Yes [source-read] |
| `d-ensemble` | Ensemble Analysis | Tally bar + WebGL scatter (charts3d.js) | stored ensemble rows | Yes [source-read] |
| `d-periods` | Period Comparison | Table + sparkline rows | stored period snapshots | Yes [source-read] |
| `d-stack` | Signal Stack | Static note only — LinDeepDive undefined | n/a | No — always shows note [source-read] |

`primeAndRefresh()` re-fetches stored result and redraws: d-ledger, d-projnet, d-web, d-ensemble, d-docsignals.

---

### Project page — `data-page="project"`

**Who sees it:** All users. Five tabs (`data-wstab`).

#### Upload tab — `data-wstab="upload"`
Drag-and-drop/file-picker for project documents. Hidden for research accounts. Data: `/exec upload`. Renders: Yes for operational users. [source-read]

#### Files tab — `data-wstab="files"`
List of uploaded files with metadata. Data: `/exec projectfiles`. Renders: Yes. [source-read]

#### Documents tab — `data-wstab="documents"`
Document list + extracted signal chips per document. Duplicates file list from Files tab (see DUPLICATED). Data: `/exec projectresults` → `doc_signals`. Renders: Yes. [source-read]

#### Signals tab — `data-wstab="detail"`
Category dot grid with labels and scores. **Not a chart** — dots rendered by `buildProjectDetailHtml()`. Data: `/exec projectresults`. Renders: Yes. [source-read]

#### Decision tab — `data-wstab="decision"`
Preliminary judgment form, final decision, history. "Commit" gated by `window.confirm()` (see STALE). Data: `/exec decisionstate`, `/exec commitjudgment`, `/exec commitdecision`. Renders: Yes. [source-read]

---

### Auditor page — `data-page="auditor"`

**Who sees it:** Users with `auditor` feature flag on. Dock button visible to all (see STALE). Two sections.

#### Section A — Corpus upload
Upload reference corpus. Data: `/exec auditorupload`. Renders: Yes. [source-read]

#### Section B — Technical audit
Submission form, results panel, history table, export XLSX. Data: `/exec auditsubmit`, `/exec auditresults`, `/exec audithistory`, `/exec auditexport`. Renders: Yes. [source-read]

---

### Training page — `data-page="training"`

**Who sees it:** Users with `training` feature flag on. Dock button and page hidden when flag off. Three states (state machine, not tabs).

#### State 1 — Not enabled
Static message: training not active for this account. Renders: Yes (when flag on but no run). [source-read]

#### State 2 — Start form
Contract form, condition selection, facility picker, value input. Data: `/exec trainingstart`. Renders: Yes. [source-read]

#### State 3 — Run in progress
Notices panel, current state display, decision buttons, signal ledger. Data: `/exec trainingdecide`, `/exec trainingadvance`, `/exec trainingdebrief`. Renders: Yes. [source-read]

---

### Handbook page — `data-page="handbook"`

**Who sees it:** All authenticated users. Two tabs.

#### About tab — `data-tab="about"`
Platform overview prose, contact info, version string. Static HTML. [source-read]

#### Methods tab — `data-tab="methods"`
Analytical taxonomy (Groups A, B, C, D — 100 computations), scoring methodology, data lineage. Static HTML. [source-read]

---

### Administration page — `data-page="admin"`

**Who sees it:** ResearchAdmin role only. Dock button hidden for all other roles (`hidden` attribute confirmed by browser probe). [browser-probed] Two tabs.

#### Access tab — `data-admintab="access"`
User roster, role assignment, feature flag toggles per account. Data: `/exec adminusers`, `/exec adminsetrole`, `/exec adminsetflag`. Renders: Yes. [source-read]

#### Reporting tab — `data-admintab="reporting"`
Aggregate usage statistics, export options. Data: `/exec adminreporting`. Renders: Yes. [source-read]

---

### In-app assistant — `#lin-assistant`

**Who sees it:** Users with `chat` feature flag on (`body.og-no-chat` hides it when off). Floating panel activated from header. Streams responses from `/exec chat`. Renders: Yes when flag on. [source-read]

---

### Footer

Platform name, version, legal line. Static HTML; always visible inside `#lin-app`. [source-read]

---

## Part 3 — Charts Summary

| Chart | Location | Type | Library | Data source | Renders |
|---|---|---|---|---|---|
| Radar scatter | Portfolio stage-radar | 2D SVG | inline SVG (app.js) | `portfolio_snapshot` scores | Yes |
| Atlas map | Portfolio stage-atlas | Flat SVG dots | inline SVG | project `location` | Yes |
| Globe | Portfolio stage-globe | WebGL 3D globe | charts3d.js | project `location` | Yes |
| Choropleth | Portfolio stage-map | SVG fill | inline SVG | results by region | Yes |
| Location dot | Detail d-globe | Flat SVG dot | inline SVG | project `location` | Yes |
| Signal Network | Detail d-projnet | 2D force graph | projectnet2d.js | signal edges | Yes |
| Neural Flow | Detail d-neural | Animated SVG | neural_flow.js | signal weights | Yes |
| Signal Web + Sphere | Detail d-web | SVG spider + WebGL sphere | charts3d.js | category scores | Yes |
| Ensemble scatter | Detail d-ensemble | Tally bar + WebGL scatter | charts3d.js | ensemble rows | Yes |
| Period sparklines | Detail d-periods | SVG sparklines | inline SVG | period snapshots | Yes |
| Signals dots | Project Signals tab | Dot grid (no chart) | buildProjectDetailHtml() | `projectresults` | Yes — dots, not a chart |

`LinForceNet` (forcenet.js) IS loaded by index.html but never initialised by any call site. Dead code. No surface rendered.

---

## Part 4 — Surfaces Not Reached (and Reason)

| Surface | Reason not reached |
|---|---|
| Consent screen (live) | Dev server fixture seed creates already-consented accounts; not shown in probed session |
| Participant profile overlay (live) | Same — fixture accounts already have profile |
| Upload tab (research account) | Research accounts cannot see the tab; not probed under operational account |
| Administration page (live) | No ResearchAdmin fixture account in dev seed; confirmed hidden in browser probe |
| Training run in-progress state | No active training run in fixture data |
| Auditor history / export | No prior audit run in fixture data |

---

*All findings based on source-read of worktree at `/home/user/LinPRojectRadar/.claude/worktrees/agent-a0db6bb18218d3623` and browser-probe of dev server (SQLite, port 8020, fixture seed) on 2026-08-05.*
