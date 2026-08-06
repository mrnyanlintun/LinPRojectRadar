# Dead Surfaces — wiring six detail-page surfaces to the primed row, the extraction display, and admin dropdowns

**Date:** 2026-08-05
**Branch:** `claude/dead-surfaces-s5s90m`
**Method:** source-read + in-process API shape probes + headless Chromium drive (Playwright, dev server port 8020, SQLite) of a real computed project and an uncomputed project, both account types + the admin page; server suite (fresh DB per file), `tests.html`, `tests_render.html`.

---

## Route chosen

**I extended the `primeAndRefresh` pattern PR #215 introduced (not a third route).** Signal Flow (`neural_flow.js`) draws correctly because it renders *entirely* inside its lazy-init from the shared resolvers (`getModuleStatus` / `getCategoryStatus` / `getProjectFusion`), which read `rowFor(project)` -> the row primed by `primeAndRefresh`. The six broken surfaces read the same resolvers, but each also **baked HTML (counts, tallies, key-signal lines) at `render()` time — before `primeAndRefresh` grafts `module_results` / `signal_inputs`** — and `primeAndRefresh` only re-ran the *canvas* lazy-inits, never the surrounding HTML. So the fix is the same graft-and-refresh mechanism, made to rebuild each surface's body (and its section badge) from the now-complete row. This is cleaner than rerouting through Signal Flow's per-call resolvers, because these surfaces are HTML-string builders, not live redraws.

### Confirmed data shapes (in-process + over the wire)

- `get` (a_get, what the detail page renders from) returns `storedResult = {result_id, period, project_status, category_statuses}` — **no `module_results`, no `signal_inputs`** (facade.py, by design).
- `projectresults` returns the full `_result_view`: `module_results`, `signal_inputs` (incl. `cpi`/`spi`/`docRiskScore` and a `sources` ledger), `category_statuses`.
- `project.signalInputs` (legacy client field) is **empty** on a server-computed project.
- The `signals_extracted` event the server writes carries **only** `docType`/`fileName`/`period`/`wasCached` — **never an applied-fields array** (documents.py). This is the root of the Part 2 defect.

---

## Part 1 — the six surfaces: was reading -> now reads

For each: the render-time source, what it needs, and the fix. In every case the needed data (`module_results`, `signal_inputs`, `category_statuses`) **is present in the stored result** — no surface had to derive anything the row does not contain, so no Part-1 stop condition fired.

### 1. Project Signal Network (`projectnet2d.js`) — needs `category_statuses` + `module_results`
- **WAS:** rendered zero nodes and the permanent "Awaiting signal extraction, all categories no-data" note with a `0/0/0/0/0` footer. Two bugs compounded: (a) its node table was keyed to **retired category ids `cat1..cat11`** while the taxonomy keys categories `a1..c1`, so `cats.filter(c => LAYOUT[c.id])` matched **nothing** — the diagram was empty on *every* project, computed or not; (b) even with nodes, module dots read `getModuleStatus`, which returned null pre-graft.
- **NOW:** the layout/edges/labels are built from the **live taxonomy** (`projectLevelCategories()`), grouped A->B->C into a flow. Category nodes colour from `getCategoryStatus`; module dots from `getModuleStatus`; the footer counts real statuses. Verified: a computed project shows `6 Red · 2 Amber · 3 No-data` (matching the Signal Ledger), awaiting-note gone; an uncomputed project shows `11 No-data` + the awaiting note (honest abstention). Category/module numbers were removed from node labels and callouts per NAMING_AUTHORITY.

### 2. Signal Sphere (`signalWebHtml` / `wireSignalSphere`) — needs `module_results`
- **WAS:** "101-module sphere · **0 active**", footnote `0 Red 0 Amber 0 Green`. The tally is computed from `getModuleStatus` at `render()`, before the graft; the lazy-init only redrew the canvas, not the tally HTML.
- **NOW:** the `d-web` lazy-init rebuilds the panel body from `signalWebHtml(p)` each time it runs, so `primeAndRefresh` re-running it re-derives the counts from the grafted row. Verified: "**36 active**", footnote `17 Red · 12 Amber · 4 Green`. #214 had already switched the *gate/source* to the stored row; this finishes it by making the count re-render after the async graft.

### 3. Ensemble Analysis (`ensembleHtml` / `ensembleTally`) — needs `module_results`
- **WAS:** section body empty (`ensembleHtml` returns `""` when `activeTotal === 0`) and the badge read "**0 active · 0 est.**" — the badge came from `p.simulationSignals`, a field **the server never writes**.
- **NOW:** the `d-ensemble` lazy-init rebuilds from `ensembleHtml(p)`; the badge is recomputed by `refreshSectionBadges` from `ensembleTally` (active) and `module_results` evidence metrics (est). Verified: "36 active modules (101 total)", badge "**36 active · 1 est.**".

### 4. Signal Web — needs `module_results`
- Same panel/lazy-init as the Signal Sphere (`d-web`); fixed by the same rebuild. Renders with the real module set.

### 5. Executive Brief (`executiveBriefHtml` -> `briefKeySignals`) — needs `signal_inputs` (Signal Pattern already read `category_statuses`)
- **WAS:** "Key Drivers: **No computed key signals are available yet**" while the Signal Pattern above it correctly grouped categories. `briefKeySignals` read only `project.signals` / `project.signalInputs` (the empty legacy blobs).
- **NOW:** `briefKeySignals` reads CPI/SPI/BAC/document-risk/contingency from the stored `signal_inputs` (grafted), falling back to the legacy blob. Verified: "CPI: 0.833 (Red) · SPI: 0.800 (Red) · Document risk: 0.00 (Green)". A scripted brief cached before the graft is dropped in `primeAndRefresh` so it regenerates.

### 6. Governance Decision (`decision.js` `classifyConflict` -> `signalStatuses`) — needs `signal_inputs` + `module_results`
- **WAS:** "Signal breakdown not available" — `signalStatuses` read only `project.signals.{evm,mc,cusum,doc}.status`, all null on a server-computed project.
- **NOW:** `signalStatuses` fills any missing class from the stored row: EVM/doc bands from `signal_inputs` (CPI/SPI, docRiskScore) via the existing `deriveStatusFromMetrics`, and Monte Carlo / CUSUM from `module_results` via `getModuleStatus`. It reads the stored answer; it does not recompute one, and a class with no stored basis stays null (abstains). Verified: "Multi-signal red-review".

### Abstention (uncomputed project), verified end-to-end
No stored result -> Signal Sphere / Ensemble render **no panel** (not a zeroed chart), Project Signal Network shows all-no-data + awaiting, Governance Decision shows "Awaiting analysis...", badges read `0 active · 0 est.` / `0 docs · 0 fields`. No empty frames, no fake zeros, no flat lines.

### One real bug found and fixed while verifying
`primeAndRefresh` is async; opening project X then quickly opening Y (before X's fetch resolves) let X's resolution write X's badges/panels into Y's DOM (elements are shared by section id). Added a `currentRenderId` stamp: a stale resolution still primes the `ROWS` cache (harmless) but does **not** graft onto, rebuild, or re-badge the page that has moved on. Without it, an uncomputed project briefly showed the previous project's "36 active / 1 doc / 10 fields".

---

## Part 2 — the extraction display: **"partial" is a display defect, not accurate extraction**

The values reached the analysis (they are in the stored `signal_inputs`, and the modules compute from them). The defect is that the **per-document event never recorded which fields it applied** — the server's `signals_extracted` event carries only `docType`/`fileName`. So:

- **Documents header "0 fields":** read from `p.signalInputs` (the empty legacy blob). **Fixed** to count distinct fields from the stored `signal_inputs` (badge recomputed by `refreshSectionBadges`). Verified: "1 doc · **10 fields**".
- **Per-document "partial" on every document:** `uploadedDocIsPartial` branded a document partial whenever its (always-empty) event field list was empty. **Fixed:** per-document fields are now reconstructed from the stored `signal_inputs.sources` ledger (which maps each field to the document *type* it came from); a document is "partial" only when its record *explicitly* carries a missing/partial flag, or when the project has **no** stored inputs at all (genuinely awaiting — where "partial" is honest). Verified: the monthly report now shows its fields (`bac, ev, ac, pv, actualPctComplete, plannedPctComplete, docDate`) and a check mark, not "partial / —".
- **"No extracted values cached this session":** already wired by #215 to read `LinResults.rowFor(project).signal_inputs`; it resolves once the row is grafted. The `d-docsignals` lazy-init now rebuilds the whole panel body (uploaded-docs table + extracted-inputs panel) so the async graft fills both. Verified: the extracted-inputs table renders; the cache message is gone.

This is a display fix only. The **extraction finding** for the record: extraction attribution is *per document type*, not *per file* — `signal_inputs.sources` records one document type per field, so two files of the same type share a field attribution and a field's source is the last document that set it. Making per-*file* attribution honest would require the extraction/event layer to record applied fields per upload, which is out of scope and was **not** changed. No extraction-layer change was needed to stop the display lying about "0 fields" / "partial", so no Part-2 stop condition fired.

---

## Part 3 — admin dropdowns

1. **Project membership picker** — was a typed input (`placeholder "e.g. PRJ-08421"`, error "Enter a project id."). Replaced with a `<select>` populated from a **new admin-only server action `adminprojectlist`** (every non-archived project by id and name; admin-scoped, *not* member-scoped like `a_list`, because an admin acts across the whole record). It fills on first admin open, and again after a project is created (no reload). Error text updated to "Choose a project." Verified: options `Choose a project · Dead Surfaces Demo (PRJ-DEAD01) · Never Computed (PRJ-EMPTY01)`.
2. **PM selector on "Create a project"** — already a dropdown populated from `adminparticipantlist`. Confirmed it opens on the "Choose a PM" prompt with all accounts. The stale-after-user-create issue: `admin.js` now calls `LinAdminOps.reloadParticipants()` after `adminparticipantcreate`, so a just-created participant appears in the PM and member pickers without a full reload.
3. **Scenario selector on "Assign a participant"** — rendered empty until the (already-active) tab was clicked again, because `loadScenarios()` only ran on a tab *reveal*. Now called in `boot()`, so it populates on first open. Verified the select is present and populated on first admin open (empty in the fixture only because no scenarios exist; the load path runs without a tab re-click).

All new labels follow NAMING_AUTHORITY: no module/category ids or numbers, no em dashes.

---

## Reconstructed note — the uncommitted `REPORT_2026-08-05_signal-display.md`

PR #215 (`3150d69`, session `claude/signal-display-s5s90m`) never committed its report. Reconstructed from the diff for the trail: it found that `detail.js`'s `render()` never called `projectresults` and never primed `LinResults`, so every surface needing `module_results` read the truncated `a_get` object (`category_statuses` only). It added `primeAndRefresh(id, p)` — POST `projectresults`, `LinResults.prime`, graft `module_results` + `signal_inputs` onto `p.storedResult`, re-run the open data-dependent sections — which fixed the **Signal Ledger** and Project Signal Network's module rows; fixed `signals.js` `panelInnerHtml` to fall back to `rowFor(project).signal_inputs`; and added a MapLibre `NavigationControl`. It fixed the *ledger*; it did **not** rebuild the HTML-string surfaces' counts/tallies after the async graft, which is exactly the gap this task closes.

---

## Verification

- **Server suite:** 2200/2200 (was 2196; +4 new `adminprojectlist` checks in `test_membership.py`), fresh DB per file.
- **`tests.html`:** 51/51.
- **`tests_render.html`:** 106/107 — the one failure is the pre-existing auth-gated "production read path" check that needs a signed-in tab (same on `origin/main`). Added **group 12** (Project Signal Network reads the live taxonomy; abstention on an uncomputed project) and **group 13** (Documents panel reports fields from the stored ledger, not "0 fields / partial"; a project with no stored inputs still reads "partial" honestly).
- **Fault-injection (every new check proven able to fail):** reintroducing the stale `cat*` id-keying drove group 12 red (`101/107`) then green on revert; disabling the `signal_inputs.sources` reconstruction drove group 13 red (`105/107`) then green on revert.
- **Headless Chromium drive:** operational PM and research observer both read every Part-1 surface as the same non-zero picture as the Signal Ledger on a real computed project; an uncomputed project shows the abstaining state everywhere; the admin page's three pickers populate on first open.

Files changed: `assets/js/detail.js`, `assets/js/decision.js`, `assets/js/projectnet2d.js`, `assets/js/admin-ops.js`, `assets/js/admin.js`, `index.html`, `server/app/research_membership.py`, `server/tools/test_membership.py`, `tests_render.html`.
