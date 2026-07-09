# Lin Opus Gubernatio

(repo: `lin-project-radar`)

A static, client-side demonstration of the **PCEIF** (Public Capital EVM
Intelligence Framework) signal-to-action governance workflow — developed for a
Doctor of Engineering praxis (The George Washington University, Engineering
Management).

This is a **separate project** from the frozen `LinDemo` site. It reuses
LinDemo's front-end layout (radar scope, three themes, left nav rail, Project
Detail, decision card, signal ledger, scripted assistant shell, timezone
selector, badges/footer) and rebuilds the data and computation layers.

> **Phase 1 of 3.** Phase 1 is front-end only: **no backend, no AI, no Google
> Drive, no network calls.** Monte Carlo and CUSUM are *real* client-side
> computations. Phase 2 adds an Apps Script + Drive backend (behind the existing
> `store.js` seam); Phase 3 adds an explanatory AI layer and RFI-vs-spec compare.

## What Phase 1 does

- **Projects start empty.** A project is a numeric id (`"01"`, `"02"`, …), a
  name, a sector (design | construction | hybrid, used only for the radar
  angle), and an **empty `signals` object** until ingest populates it. There is
  no fixed project count. Empty projects render as a hollow, dashed,
  awaiting-ingest marker on the radar and an "awaiting ingest" state in Detail —
  **never a fabricated green/amber/red.**
- **Create project** assigns the next id, creates an empty project, and persists
  to `localStorage`.
- **Populate signals** (Manage Projects, or a project's Detail page) takes CPI /
  SPI (and optionally a BAC, a metric series, and a document) and runs the real
  models to derive the signal package.
- **Module 01 — real Monte Carlo.** `sim.js` derives a Beta-PERT three-point
  estimate from the project's EVM + risk signals (most-likely EAC = BAC / CPI;
  spread driven by a documented blend of CPI, SPI, document score, and the CUSUM
  result), runs a real **5,000-iteration** loop, and reads **P50 / P80** from the
  sorted simulated array. The Detail chart is the actual histogram with P50/P80
  markers. A higher-risk project yields a wider, more pessimistically skewed
  distribution.
- **Module 02 — real CUSUM.** `sim.js` runs the standard two-sided tabular CUSUM
  recursion (`SHi`/`SLo`, slack `k = 0.5σ`, decision interval `H = hUnits·σ`)
  over the project's metric series. A **breach is the statistic crossing H** —
  never a hardcoded boolean. The Detail chart is the computed statistic vs H with
  the breach point flagged.
- **Modules 03–05** stay rule-based: document-risk is transparent keyword/rule
  extraction (Phase 3 adds an explanatory AI layer); signal synthesis and the ABM
  governance layer are driven by `decision.js`.

These are **demonstration models** — the signal→spread mapping is a designed
heuristic, not a calibrated or validated forecast. (The Monte Carlo seeds its RNG
per inputs so a given project's distribution is reproducible across re-renders;
it is still a genuine sampled draw, not a drawn curve.)

## Data layer (swappable seam)

All project reads/writes go through **`assets/js/store.js`**:
`listProjects()`, `getProject(id)`, `createProject({name,sector})`,
`saveProject(project)`, `archiveProject` / `restoreProject`. Phase 1 backs these
with `localStorage` only. Phase 2 swaps the implementation for Apps Script/Drive
**without touching the UI** — the UI never calls storage directly.

## Boundaries

- Platform name **Lin** only. Synthetic demonstration data only — no real
  project, agency, employer, contractor, or vendor.
- **No backend, no LLM/API calls, no analytics, no build step** in Phase 1.
  Google Fonts is the only external resource.
- No fabricated AI stats; the contractor fairness gate is a blocking workflow
  step, never a percentage. The SYNTHETIC DEMONSTRATION DATA badge and the
  academic-boundary footer stay.
- `decision.js` is pure and DOM-free (governance + ABM rules), unchanged API.

## Structure

```
index.html
.nojekyll
assets/css/radar.css        visual system + two themes (Dark default / Light)
assets/js/data.js           empty-shell seed + live arrays
assets/js/store.js          data-access seam (localStorage in Phase 1)
assets/js/decision.js       PCEIF governance + ABM rules (pure functions)
assets/js/sim.js            REAL Monte Carlo (Beta-PERT) + CUSUM + signal builder
assets/js/modules.js        Signals overview (populated projects only)
assets/js/deepdive.js       per-project deep dive (live MC + CUSUM charts)
assets/js/ingest.js         create / populate / doc-ingest / archive (via store.js)
assets/js/detail.js         Project Detail drill-down
assets/js/assistant.js      scripted help assistant (no LLM)
assets/js/knowledge.js      knowledge library + term lens
assets/js/tz.js             timezone selector (default America/New_York)
assets/js/app.js            radar, page orchestration, decision card, audit export
```

## Run / deploy

Open `index.html` directly, or serve the folder
(`python -m http.server`). All paths are relative, so the site works under the
GitHub Pages project subpath `/lin-project-radar/`. `.nojekyll` is present.
