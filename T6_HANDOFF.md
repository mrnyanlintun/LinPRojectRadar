# T6 handoff — Part 4 (the copy audit) is all that remains

| | Status | Where |
|---|---|---|
| Part F — expert reference lock | Merged | `main` @ `8c1d67a` |
| Parts A–E — the fold | Merged, browser-verified | `main` @ `dbdd261` |
| Project-creation gate, admin projects/assignment | Merged | `main` @ `dbdd261` |
| Part 3 — the compute rewrite | **Merged, proven** | `main` @ `dbdd261` |
| **Part 4 — the copy audit** | **Inventoried, not rewritten** | — |

`main` is at `dbdd261`. 843 checks across 17 suites pass. No migration is pending; the schema
stays at 0012 and `/readyz` is unaffected by anything merged since.

The false-Red defect that dominated the last two sessions is **fixed and merged**. What follows in
§1 is kept as the record of what it was, because it explains why the architecture is now what it
is. §4 is the outstanding work.

---

## 1. The defect that is now fixed (record, not a to-do)

Two computations existed for the same project. The server computed status from documents and
stored it; the legacy dashboard recomputed it in the browser. They disagreed:

| Case | CPI | Server | Legacy browser | |
|---|---|---|---|---|
| healthy | 1.05 | Green | **Red — 40 of 40 seeds** | deterministic |
| on-budget | 1.00 | Green | **Green 38 / Amber 2** | seed-dependent |
| distressed | 0.833 | Red | Red | agreed |

**Mechanism.** `LinSim.buildSignals` expects a time series; `ingest.js` never passed one, so it
fell through to `deriveSeries(metricValue, seed)` and invented one from a single value plus a
seed. That fabricated series tripped the CUSUM Anomaly Monitor. The seed derived from the project
id, so two identical projects could differ. On the healthy case the browser reported
`evm: green, mc: green, doc: green, cusum: red`, and the fusion promoted that one red to Red.

**After the rewrite, re-measured:** stored, `getProjectFusion` and `deriveHealthState` all return
Green for cpi 1.05, Green for cpi 1.00, Red for cpi 0.833. There is one computation now.

---

## 2. How Part 3 was done, and what to preserve

**Four functions, not 79 edits.** The split counted 79 call sites across eight files. Rather than
edit them, `getModuleStatus`, `getCategoryStatus` and `getProjectFusion` kept their names and
signatures and changed where the answer comes from: they read the stored `computed_results` row.
Every call site became correct without being touched.

- **`assets/js/taxonomy.js`** replaces `categories.js` on the application. The taxonomy is
  carried over unchanged, because it is data. The derivation is not.
- **`LinResults.prime(projectId, row)`** is how a stored row reaches the accessors. The loaders
  that already fetch `projectresults` call it. **The cache deliberately cannot fetch**: a module
  that could fetch would eventually fetch during a render, and a render that issues a request can
  audit an evidence view the participant never asked for. Note the row is `resp.result`, not
  `resp` — priming the envelope silently yields `undefined` statuses.
- **`deriveHealthState` has no fallback derivation.** No stored row now means "Awaiting analysis".
  Restoring a fallback would restore the defect.
- **Enforced by absence.** `index.html` loads none of `sim.js`, `simulations.js`,
  `categories.js`, `deepdive.js`. Verified by resource timing across all six page sections.

**`research/deepdive.html`** is the one surface that computes in the browser, on purpose: it
re-runs the models live to show the working. Nothing links to it, it holds no data of its own, and
every action it would call is refused server-side without the right role. It is not a security
boundary and does not claim to be — the guarantee is that no participant-facing route loads a
client-side model.

---

## 3. Verified in a browser (all merged)

| Guarantee | Result |
|---|---|
| Full workflow, no page load | Verified — `navigation` entries stayed at 1 |
| Profile once, no questionnaire nav | Verified — absent on reload and fresh sign-in |
| Nav sets | Verified — participant topbar `[]`, admin `["Admin"]`, dock identical |
| Platform theme | Verified — `radar.css` the only palette |
| No raw ULIDs | Verified — zero across every page section |
| Every field labelled | Verified — zero unlabelled fields |
| No module ids in text | Verified — zero across every page section |
| **Compute libraries absent** | **Verified — resource timing, all six sections** |
| Layout | Verified — clamps to 1280px at 1920 and 3840, no overflow |

**Known open design gap** (not a bug, and Part 3 does not address it): the decision sequence is
keyed to **assignments**, not projects. A participant can no longer create an unassigned project,
so the dead end is closed for them, but Part B's workflow is still not one continuous chain — a
participant uploads to a project and decides against an assigned scenario, and nothing links the
two.

---

## 4. PART 4 — the outstanding work

Inventoried, not rewritten. **Do not rewrite before re-reading the inventory**, and note that a
partial sweep is worse than none: half-converted spelling is more jarring than uniform British.

Run `python tools/copy_inventory.py` from the repository root to regenerate these numbers. It
separates user-facing copy from comments, which matters more than it sounds.

### Em dashes: 212 in user-facing copy

The naive repository-wide count is **1015**. The count in copy a user can read is **212**. A sweep
driven by the first number rewrites a great deal of prose nobody reads and reports success.

| Count | File | | Count | File |
|---|---|---|---|---|
| 53 | `assets/js/detail.js` | | 8 | `assets/js/store.js` |
| 30 | `assets/js/signals.js` | | 7 | `assets/js/app.js` |
| 21 | `index.html` | | 7 | `assets/js/assistant.js` |
| 16 | `assets/js/auditor.js` | | 7 | `assets/js/decision-ui.js` |
| 14 | `assets/js/workspace.js` | | 6 | `assets/js/deepdive.js` |
| 11 | `assets/js/admin.js` | | 3 each | `tests.html`, `charts3d.js`, `export.js`, `forcenet.js`, `projectnet2d.js` |
| 10 | `assets/js/admin-ops.js` | | 1–2 each | `neural_flow.js`, `documents.py`, `extraction_client.py`, `ingest.js`, `research/deepdive.html` |

### Spelling: American English, decided

Raw tally in strings is British 55 / American 162, but the headline is misleading and **two
exclusions are load-bearing**:

- **`center` (122 occurrences) is CSS and geometry**, not prose. Not a spelling decision.
- **`analyze` is an `/exec` action name** — `writes.py:441` `DEFERRED_AI_ACTIONS`, and
  `store.js:519` sends `action: "analyze"`. **Renaming it breaks the facade contract.**

Excluding those, prose leans British: `authorised` 26, `recognised` 10, `behaviour` 8,
`organisation` 4, `summarised` 1. **American English is confirmed as the convention** — GWU is the
institution and the directors work US federal and commercial projects — so roughly **55 prose
instances change**, and no technical token is touched.

### Still to do, none of it started

- The em dash sweep (212), the phrasing and redundancy pass, and the empty-state, error-message
  and confirmation-dialog review across portfolio, project detail, upload, decision sequence,
  admin, profile and expert workflow.
- **The glossary** of the platform's own terms, applied consistently.
- **The sign-in page**, the named worst offender: "authorisation" two lines from "authorized";
  "Access is restricted to authorized users only" beside a sign-in form; "Need an account, or
  forgot your password?" as one control asking two questions; copyright sitting above the access
  notice when the order should be notice, attribution, copyright.
- **The two-audience notice.** T1a built a conditional notice keyed on `account_type`. Verify it
  still works after the fold. The research variant should be protective; the operational variant
  should be accurate about responsibility without implying the platform is a toy; the
  pre-sign-in state, where account type is unknown, must keep the restrictive text.
  **Draft both variants for the researcher's review. Do not adopt liability wording, and treat
  consent text as requiring IRB approval.**

Constraints for that work: **no behavioural change**, no layout change beyond what text length
forces, and no change to a string a test asserts against without updating the test and saying so.

---

## 5. Traps and environment

- **`preview_start` resolves `launch.json` from the shell's working directory.** From `Demo` it
  starts the dead `opus-gubernatio` app on 8099 — same brand, same title. It was started twice in
  one session and stopped both times. The tell: `api.js`/`boot.js` in the sources and **zero
  `.page` sections**. **Check `preview_list`'s `cwd` before trusting any browser session.** The
  working route is `preview_start({url: "http://127.0.0.1:8010"})` attached to a server started
  separately.
- **`server/tools/dev_serve.py`** runs the real app: fills `DATABASE_URL` only if unset, defaults
  to a gitignored repo-local file, migrates to head, and seeds B7b's StubExtractor with three
  recordings (`healthy`, `on-budget`, `distressed`) written to `server/dev_fixtures/`. The
  `on-budget` fixture has earned value exactly equal to actual cost, so the pathological cpi = 1.0
  case is reproducible on demand. Never on Render's path.
- **Duplicate function declarations silently win.** `decision-ui.js` had an internal `render()`
  and an exported wrapper also named `render()`; hoisting bound the export to the wrong one and
  the decision tab threw on open. Check for name collisions when adding a module export.
- **Browser caching bit once.** After editing a JS file the page kept the old copy while the
  server served the new one. Check `String(window.LinX.fn).includes(...)` if behaviour disagrees
  with the source; a fresh tab clears it.
- **`window.confirm` auto-dismisses** in the automated browser, so `commitPreJudgment` silently
  returns. Stub it to `true` when driving the decision sequence.
- **Re-renders clear programmatically set field values.** Set and submit in the same tick.
- **Every account in every existing suite is `account_type: "operational"`** — so any gate keyed
  on `account_type` is invisible to the suite by default. That is how the project-creation gate
  initially had no coverage while the full suite passed.
- **No `DATABASE_URL` default exists** (`settings.py:69-74`). Throwaway SQLite outside the
  repository, never production. One freshly migrated database per suite. Read counts from each
  suite's own `RESULT: n/n` line, never by grepping `PASS`/`FAIL`.
- `test_simulation` exits 1 on Windows from a `charmap` error printing mu; 27/27 under
  `PYTHONIOENCODING=utf-8`. `test_decision_ui_t4` prints a line containing `FAIL` that is the
  label of its own self-test.

---

## 6. Regression

**843 checks across 17 suites, all passing**, verified after the merge to `main`.

Both changes from the 838 baseline, stated where they happened:
- `test_features` 36 → **41**: five checks covering the project-creation gate.
- `test_decision_ui_t4` holds at 73/73; its guarantee-10 scan was repointed from the deleted
  `decision.html` to `index.html` and indexed by filename rather than list position.
