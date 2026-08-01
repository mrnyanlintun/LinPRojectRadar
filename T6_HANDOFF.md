# T6 handoff — read the finding in §1 before scoping anything

| | Status | Where |
|---|---|---|
| Part F — expert reference lock | Merged | `main` @ `8c1d67a` |
| Parts A–E — the fold | Implemented and **browser-verified** | branch `t6-integration-cleanup` @ `f09e4ab` |
| Project-creation gate + admin projects/assignment | Implemented and verified | same branch |
| **Part 3 — the Group 1 rewrite** | **Not started** | — |
| **Guarantee 5 (compute libraries)** | **Not met** | — |

`main` carries Part F only. Production is unaffected by the branch. No migration is pending
beyond 0012, which is already applied.

---

## 1. THE FINDING THAT CHANGES THE SCOPE — the legacy dashboard reports false Reds

This is no longer a tidiness question about which library loads where.

Two computations exist for the same project. The server computes status from documents and stores
it in `computed_results`. The legacy dashboard recomputes it in the browser from
`simulations.js`. **They disagree, and the browser one is wrong in the direction that destroys
credibility.**

Measured on identical earned-value inputs, server against browser:

| Case | CPI | SPI | Server (`computed_results`) | Legacy dashboard (browser) | Agree? |
|---|---|---|---|---|---|
| healthy | 1.05 | 1.05 | **Green** | **Red** | **no** |
| on-budget | 1.00 | 1.00 | **Green** | **Amber** | **no** |
| distressed | 0.833 | 0.80 | Red | Red | yes |

Repeated across 40 different seeds:

- **cpi 1.05 → Red in 40 of 40.** A project 5% under budget and 5% ahead of schedule is
  **deterministically** Red on the legacy dashboard. This is not an edge case; it is the ordinary
  healthy project.
- **cpi 1.00 → Green 38, Amber 2.** Seed-dependent. The seed is derived from the project id
  (`LinSim.hashSeed(project.id)`), so **two identical projects get different statuses because
  they have different ids.**

The server says Green for both. The stored computation is right; the browser one is wrong.

### The mechanism: a synthesised series trips the CUSUM monitor

On the healthy case the legacy path reports `evm: green, mc: green, doc: green, cusum: red`, and
the fusion promotes that single red to a project status of Red. The culprit is the **CUSUM
Anomaly Monitor**, and specifically how it gets its input:

`LinSim.buildSignals(inputs)` expects a time series. `ingest.js` never passes one — it calls
`buildSignals({cpi, spi, bac, docScore, docSource, docExcerpt, seed})` with no `series`. So
`buildSignals` falls through to:

```js
const series = (Array.isArray(inputs.series) && inputs.series.length >= 3)
  ? inputs.series.map(Number)
  : deriveSeries(metricValue, seed);     // <- synthesised from ONE value plus a seed
```

`deriveSeries` invents a series from a single metric value and the seed. That invented series
trips the anomaly detector on a project with no anomaly in it. There is no real history behind the
Red; it is manufactured by the fallback.

### Why this matters for scoping Part 3

The rewrite is what removes this. It is not cleanup deferred from a previous phase — it is the
fix for a defect that will be visible to directors on their own healthy projects, deterministically,
the first time they look. Scope Part 3 accordingly: the priority is getting the participant-facing
surfaces onto the stored row, not the tidiness of dropping three script tags.

**Reproduce it in one line.** `server/tools/dev_serve.py` seeds three fixture documents,
including `on-budget` with earned value exactly equal to actual cost. Start the server, upload
`server/dev_fixtures/monthly_report_healthy.txt`, compute, and compare the stored `project_status`
against `getProjectFusion(p)` in the console.

---

## 2. What Part F added (merged, on `main`)

The expert reference is the standard participant decisions are scored against, and its value rests
on having been committed before the expert saw the AI package. B1 created `expert_references` and
its `locked_at` column but never created the lock.

**Migration 0012** installs an immutability trigger, reusing 0003's mechanism rather than inventing
a second one: reject loudly with SQLSTATE `OG002`, audit row written on a separate connection
because a trigger that raises cannot durably record its own rejection. Adds a `period` column (a
scenario-level reference cannot be scored against per-period decisions) and a unique index (a
second INSERT is the trivial way around an UPDATE trigger).

**`server/app/research_expert.py`** — five actions. Two properties to preserve:

- **Evidence is package-free by construction, not by gate.** `a_expertevidenceget` never reads
  `assignments.package_id`. Stronger than a conditional, because a future branch cannot get it
  wrong.
- **`locked_at` is set in the same INSERT as the content.** No write-then-lock path. Do not add one.

**`server/tools/leak_detector.py`** — shared by T4 and T6 so there is one definition of a leak.
**`test_expert_reference_t6.py`** (59 checks) proves the detector can FAIL before trusting it,
including against a real leak monkeypatched into the live handler. Guarantee 9 proved across four
routes plus clearing `locked_at` plus a duplicate INSERT.

Proved at the **server layer only** — there is still no expert UI, so nothing is proved at the DOM
layer.

---

## 3. What Parts A–E did, and what is now browser-verified

### Removed
`workspace.html`, `admin-ops.html`, `questionnaires.html`, `decision.html` and their four routes.
All four paths 404.

### Where each capability went
- **workspace.html** → Portfolio gained the project list and portfolio health; a new
  `data-page="project"` section holds upload, documents and signals. `LinWorkspace.boot/openProject/switchPanel`.
- **decision.html** → the Period decision tab of the Project page. `LinDecisionUI.mount`.
- **questionnaires.html** → a first-run overlay with no route and no nav item.
  `LinProfile.maybePrompt`, which asks the server rather than keeping a flag.
- **admin-ops.html** → tabs in the Admin section. `LinAdminOps.boot/showTab`.

### Verified in a real browser, against this repository

| Guarantee | Result |
|---|---|
| 1. Full workflow, no page load | **Verified** — `navigation` entries stayed at 1. See caveat in §5. |
| 2. Profile once, no questionnaire nav | **Verified** — absent on reload and on fresh sign-in |
| 3. Nav sets | **Verified** — participant topbar `[]`, admin `["Admin"]`, dock identical |
| 4. Platform theme | **Verified** — `radar.css` the only palette; the lone inline `<style>` is Google's injected sign-in widget |
| 5. No raw ULIDs | **Verified** — zero across every page section |
| 6. Every field labelled | **Verified** — zero unlabelled fields application-wide |
| 7. No module ids in text | **Verified** — zero across every page section |
| Layout | **Verified** — clamps to 1280px at 1920 and 3840, no overflow at 1280/1920/3840 |

### The defect running it found
`decision-ui.js` already had an internal `render()`; the exported wrapper was also `render()`.
Declarations hoist, so `LinDecisionUI.render` bound to the internal **stage** renderer, which
assumes `STATE.server` is populated. The decision tab threw `cannot read current_stage of null`.
Renamed to `mount()`. **No static check would have caught this** — only running it did.

---

## 4. This session's two changes

### Research accounts cannot create projects
`features.RESEARCH_FORBIDDEN_ACTIONS`, refused in `gate_action` before dispatch — same chokepoint
and same reasoning as the feature flags. Covers `projectcreate` **and** the legacy facade
`create`, which reaches the same outcome by another door. Sessionless callers untouched, so the
A1b contract fixtures stay green. Operational accounts keep it.

Verified: research refused on both actions; operational created `PRJ-XNWKEJCRKC` successfully.

**COVERAGE GAP THIS EXPOSED, AND HOW IT WAS CLOSED.** The gate initially had **no test coverage at
all**, and the full suite passed anyway. The reason: **every account in every existing suite is
`account_type: "operational"`** (e.g. `test_workspace_t3t5.py:87`), so the gate correctly never
fired. That is not a bypass, but it means a research-account guard is invisible to the suite by
default — worth remembering for any future gate keyed on `account_type`.

Closed with five checks in `test_features.py` (36 → 41): both actions refused for a research
account, **both refusals audited against that participant specifically** (a whole-table count
would pass on someone else's rows), operational still permitted, sessionless unaffected.

### Admin gained Projects & assignment
Five tabs: Users & access · Projects & assignment · Project membership · Monitoring · Export.
Creation and assignment sit together because they are one act — a project with no assignment stops
after signals; an assignment with no project has nothing to show. Scenarios are named by version
and project type, never by identifier. Order group and scenario set are shown as real labelled
fields rather than invented silently, because B3 still resolves a frozen condition sequence from
them and refuses when there isn't one. `config_id` is still never rendered.

### The operational dead end, found while verifying the above
The intake check in `decision-ui.js` ran **before** the assignment check, so an operational user
with their own unassigned project was told *"Your background profile has to be recorded before your
first decision."* They can never record one: the profile is only offered to a consented research
account, and an operational account can never obtain a consents row. Assignment is now asked
first. It reads:

> "No decision sequence is assigned to this account. Period decisions are recorded against a
> scenario the researcher assigns."

---

## 5. Part 3 — the work, unchanged in shape, changed in urgency

`sim.js`, `simulations.js` and `categories.js` still load in the participant-facing application.

**Group 1 — visualisation rendering values already stored: 79 non-comment call sites.** Each has a
direct equivalent in the `ComputedResult` row (`signal_inputs`, `module_results`,
`category_statuses`, `project_status`, `portfolio_snapshot`), whose docstring says *"Every surface
downstream READS this; none of them recompute."*

| Symbol | Sites | Stored equivalent |
|---|---|---|
| `LIN_CATEGORIES` | 36 | static label/membership table — names, ordering, module→category |
| `getModuleStatus` | 12 | `module_results[].status_color` |
| `getCategoryStatus` | 11 | `category_statuses` |
| `getProjectFusion` | 8 | `project_status` |
| `normalizeSector` | 4 | static mapping |
| `projectLevelCategories` | 4 | static table |
| `deriveProjectStatus` | 2 | `project_status` |
| `categoryNAModules` | 1 | static / served flag |
| `projectCompletionDate` | 1 | stored project field |

`isModuleSectorNA`, `isPortfolioLevelCategory`, `contributesToProjectStatus`: **zero call sites** —
exported but dead. `workspace.js` is the working model: same information, static name table plus
server-supplied status strings, zero compute-library calls.

**Group 2 — genuine client compute: 22 sites, four files.**

| File | Sites | What it is | Disposition |
|---|---|---|---|
| `signals.js` | 10 | legacy browser ingest | retire — superseded |
| `ingest.js` | 4 | legacy browser ingest | retire — superseded |
| `deepdive.js` | 5 | live 5,000-iteration Monte Carlo re-run | move researcher-side |
| `detail.js` | 3 | `LinSimulations[r.fn]` display recompute | backfill fallback, becomes dead |

**No server ingest endpoint is required.** B7b already owns the path: `documents.py:420`
`projectupload` extracts server-side, `projectcompute` (651) runs the analytical layer and stores
the result, `projectresults` (703) *"READS ONLY — never computes."* The 14 browser-ingest sites are
a legacy duplicate of a path the server already owns — **and they are the source of the false Red
in §1**, because that is where `buildSignals` synthesises a series.

`detail.js:121` and `deepdive.js:2085-2089` only compute **when the stored result is absent** —
backfill fallbacks for legacy demo seeds, dead once `projectcompute` supplies full
`module_results`. So the genuinely compute-only surface is **one**: `deepdive.js`'s re-run
animation, which recomputes deliberately because the live run *is* the feature.

### Caveat on guarantee 1 that Part 3 does not fix
The decision sequence is keyed to **assignments**, not to projects. Since this session a research
participant can no longer create an unassigned project, so the dead end is closed for them. But
Part B's workflow still is not one continuous chain: a participant uploads to a project and
decides against an assigned scenario, and nothing links the two.

---

## 6. Traps and environment

- **`preview_start` resolves `launch.json` from the shell's working directory.** From `Demo` it
  starts the dead `opus-gubernatio` app on port 8099 — same brand, same title. It was started
  twice this session and stopped both times. The tell: it serves `api.js`/`boot.js` and has
  **zero** `.page` sections. **Always check `preview_list`'s `cwd` before trusting a browser
  session.** The workaround is `preview_start({url: "http://127.0.0.1:8010"})` attaching to a
  server started separately.
- **`server/tools/dev_serve.py`** starts the real app: fills `DATABASE_URL` only if unset, defaults
  to a gitignored repo-local file, migrates to head, seeds B7b's StubExtractor with three
  recordings (`healthy`, `on-budget`, `distressed`). Never on Render's path.
- **Browser caching bit once.** After editing a JS file the page kept the old copy while the server
  served the new one; a fresh tab was needed. Check `String(window.LinX.fn).includes(...)` if
  behaviour disagrees with the source.
- **`window.confirm` auto-dismisses** in the automated browser, so `commitPreJudgment` silently
  returns. Stub it to `true` when driving the decision sequence.
- **Re-renders clear programmatically set field values.** Set and submit in the same tick.
- **No `DATABASE_URL` default exists** (`settings.py:69-74`). Use a throwaway SQLite outside the
  repository, never production. One freshly migrated database per suite. Read counts from each
  suite's own `RESULT: n/n` line, never by grepping `PASS`/`FAIL`.
- `test_simulation` exits 1 on Windows from a `charmap` error printing mu; it is 27/27 under
  `PYTHONIOENCODING=utf-8`. `test_decision_ui_t4` prints a line containing `FAIL` that is the label
  of its own self-test.

---

## 7. Regression

**843 checks across 17 suites, all passing.**

Changes from the 838 baseline, both stated where they occurred:
- `test_features` 36 → **41**: five new checks covering the project-creation gate.
- `test_decision_ui_t4` stays 73/73, but its guarantee-10 scan was repointed from `decision.html`
  (deleted) to `index.html`, and indexed by filename rather than list position.

---

## 8. Suggested order for the next session

1. Read §1. Decide scope knowing the rewrite fixes a deterministic false Red, not a lint.
2. Retire the legacy browser-ingest path in `ingest.js`/`signals.js` first — it is 14 of the 22
   Group 2 sites, it is superseded by `projectupload`/`projectcompute`, and it is where the false
   Red is manufactured.
3. Rewrite Group 1's 79 sites onto the stored row, keeping the radar working — it draws from
   status and drift, both stored.
4. Move `deepdive.js`'s re-run animation researcher-side.
5. Drop the three script tags and prove absence with
   `performance.getEntriesByType('resource')` on every participant-facing route.
6. Re-verify the guarantees in §3, then merge.
