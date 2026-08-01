# T6 handoff — Part F merged; Parts A–E implemented on a branch, unverified in a browser

T6 covered the expert reference lock (Part F), folding four standalone pages back into the
application shell (Parts A, A.1, B), the admin surface rework (Part C), the role vocabulary
(Part D), and an interface cleanup sweep (Part E).

**State of play:**

| | Status | Where |
|---|---|---|
| Part F — expert reference lock | Merged | `main` @ `8c1d67a` |
| Parts A, A.1, B, C, D, E | Implemented, committed, **not merged** | branch `t6-integration-cleanup` @ `ee754c0` |
| Browser verification | **Not done** | — |
| Guarantee 5 (compute libraries) | **Not met** | — |

Production is unaffected by the branch. `main` carries Part F only.

---

## 1. What Part F added (merged)

The expert reference is the standard every participant decision is scored against, and its value
rests on having been committed before the expert saw the AI package. B1 created the
`expert_references` table and its `locked_at` column but never created the lock.

**Migration 0012** installs an immutability trigger on `expert_references`, reusing the mechanism
0003 established rather than inventing a second one: the trigger rejects loudly with SQLSTATE
`OG002`, and `research_audit.py` writes the audit row on a separate connection, because a trigger
that raises cannot durably record its own rejection. It adds a `period` column — a scenario-level
reference cannot be scored against per-period decisions — and a unique index, because a second
INSERT is the trivial way around an UPDATE trigger.

**`server/app/research_expert.py`** holds the sequence, wired into `facade.dispatch_post`:
`expertreferencelist`, `expertevidenceget`, `expertreferencecommit`, `expertpackageview`,
`expertrealismreview`.

Two properties to preserve if you extend it:

- **Evidence is package-free by construction, not by gate.** `a_expertevidenceget` never reads
  `assignments.package_id`. That is stronger than a conditional, because a future branch cannot
  get it wrong.
- **`locked_at` is set in the same INSERT as the content.** There is no write-then-lock path.
  Do not add one.

**`server/tools/leak_detector.py`** extracts T4's detector so T4 and T6 share one definition of
what counts as a leak. **`server/tools/test_expert_reference_t6.py`** (59 checks) proves the
detector can FAIL before trusting it — against planted blobs, then against a real leak
monkeypatched into the live handler, which is then removed and the handler re-verified clean.
Guarantee 9 is proved across four routes (API, ORM, Core, raw SQL) plus clearing `locked_at` plus
a duplicate INSERT.

Both are proved at the **server layer only**. They still need re-proving at the DOM layer once an
expert interface exists — there is currently no expert UI at all.

---

## 2. What Parts A–E did (branch `t6-integration-cleanup`, commit `ee754c0`)

### Removed
`workspace.html`, `admin-ops.html`, `questionnaires.html`, `decision.html`, and their four routes
in `server/app/main.py` (`spa_workspace`, `spa_admin_ops`, `spa_questionnaires`, `spa_decision`
and their path constants). **All four paths return 404 — verified.**

### Where each capability went
- **workspace.html** → the Portfolio page gained create-project, the project list and portfolio
  health; a new `data-page="project"` section holds period upload, the document library and
  signals. `workspace.js` exposes `LinWorkspace.boot/openProject/switchPanel`.
- **decision.html** → the Period decision tab of the Project page. Its stage markup is now in
  `index.html`; `decision-ui.js` exposes `LinDecisionUI.render`.
- **questionnaires.html** → a first-run overlay (`#profile-overlay`) with no route and no nav
  item. `questionnaires.js` exposes `LinProfile.maybePrompt`, which asks the server whether
  intake is needed rather than keeping a flag of its own. The debrief is no longer reachable.
- **admin-ops.html** → tabs inside the Admin section. `admin-ops.js` exposes
  `LinAdminOps.boot/showTab`.

The old sign-out hazard is gone: `workspace.js` no longer does
`window.location.href = "index.html"`; the topbar's `LinAuth.logout()` is the single path.

### Navigation
Five topbar controls became one (`Admin`, admin-only). The icon dock was already clean — it only
ever held Portfolio, Technical Auditor and Handbook. `index.html` now contains exactly one
`data-nav` item.

### Part C
Scenarios and Assignment UI withdrawn. **B3's backend is untouched and proved intact**:
`adminscenariocreate`, `adminscenariolist`, `adminassign`, `adminassignmentlist` all dispatch when
called directly (they reach the auth check, not "unknown action"), and `test_assignment_blinding`
is still 44/44. Project membership on B8's actions replaced it.

### Part D
`Demo` removed from `admin.js`'s role dropdown — it was constraint-permitted and branched on
nowhere, so selecting it silently meant nothing. The CHECK constraint and data model are
deliberately untouched. Expert is presented as a research-panel role.

### Part E
- `tests.html` was the only screen with no `radar.css` link and a complete private palette; two of
  its literals were the dark theme's status colours hard-coded, so a palette edit would have
  desynced it silently while it still reported green. Now on the theme, zero colour literals.
- The four folded pages' `<style>` blocks moved into `radar.css`. `--on-brand` added because
  `#fff` was hard-coded on brand buttons in four files.
- Raw ids no longer serve as content: `project_id` was the subtitle of every project row and the
  title of any row without a name; `export_id` was the first column of the exports table. Both are
  now truncated secondary metadata (`.ws-id`) behind a real name.
- Placeholder-as-label fixed on the admin fields that read `order_group`, `scenario_set`,
  `scenario_ids, comma separated`, `scenario_version`.

---

## 3. Regression

**838 checks across 17 suites, all passing. Total unchanged.**

One count needs stating: `test_decision_ui_t4` remains 73/73, but two of its checks were
repointed. Its guarantee-10 scan read `decision.html`, which no longer exists — it failed loudly
with an `IndexError` rather than passing vacuously. It now reads `index.html`, where that markup
lives, and is indexed by filename rather than list position so a future reorder cannot silently
assert against the wrong file. Substance unchanged: both the markup and the script must still be
free of module ids.

Two results that look like failures and are not:
- `test_simulation` exits 1 on Windows from a `charmap` error printing the character mu. It is
  27/27 under `PYTHONIOENCODING=utf-8`.
- `test_decision_ui_t4` prints a line containing `FAIL` — the label of its own self-test.

---

## 4. What still has to be done

### 4a. Browser verification — none of it is done

Guarantees 1, 3, 4, 6, 7, 8 and 10 have static evidence only. There is partial static support
(one `data-nav` item; `tests.html` clean of literals; the label and id fixes are in the markup),
but nothing has been seen running. **The fold has never been exercised.**

**The trap that cost the last session this work:** `preview_start` resolves `.claude/launch.json`
from the shell's working directory. If that is `DEng\Demo`, it starts the **dead
`opus-gubernatio` repo** on port 8099. It looks plausible — same brand, same page title. The tell
is that it serves `api.js`/`boot.js` and has **zero** `.page` sections. Check `preview_list`'s
`cwd` field before trusting any preview.

`.claude/launch.json` in this repo now points at `server/.venv/Scripts/python.exe` (the old
`python3` does not exist on this machine) but still only serves **static files**, which cannot
answer `/exec`. Verifying guarantee 1 end to end needs the FastAPI app running against a
throwaway SQLite — that wiring does not exist yet and is the first thing to build.

### 4b. Guarantee 5 — not met, and the honest scope

`sim.js`, `simulations.js` and `categories.js` **still load** in the participant-facing
application, exactly as before the fold. The fold neither introduced this nor removed it.

The split, measured on non-comment call sites across the nine files that use them:

**Group 1 — visualisation rendering values already stored: 79 sites.** Each has a direct
equivalent in the `ComputedResult` row (`signal_inputs`, `module_results`, `category_statuses`,
`project_status`, `portfolio_snapshot`), whose own docstring says *"Every surface downstream READS
this; none of them recompute."*

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
exported but dead. `workspace.js` is the working model for this rewrite: it renders the same
information from a static name table plus server-supplied status strings, with zero
compute-library calls.

**Group 2 — genuine client compute: 22 sites, four files.**

| File | Sites | What it is | Disposition |
|---|---|---|---|
| `signals.js` | 10 | legacy browser ingest | retire — superseded |
| `ingest.js` | 4 | legacy browser ingest | retire — superseded |
| `deepdive.js` | 5 | live 5,000-iteration Monte Carlo re-run | move researcher-side |
| `detail.js` | 3 | `LinSimulations[r.fn]` display recompute | backfill fallback, becomes dead |

**No server ingest endpoint is required.** B7b already owns the whole path:
`documents.py:420` `projectupload` extracts server-side, `projectcompute` (line 651) *"Runs the
analytical layer for a period and stores the result"*, `projectresults` (line 703) *"READS ONLY —
never computes."* The 14 browser-ingest sites in `ingest.js`/`signals.js` are a legacy duplicate
of a path the server already owns, left from the Apps Script era.

`detail.js:121` (`if (statusFromResult(results[r.key])) return; // already populated`) and
`deepdive.js:2085-2089` only compute **when the stored result is absent** — they are backfill
fallbacks for legacy demo seeds, not ongoing compute. With `projectcompute` producing full
`module_results` they become dead.

So the genuinely compute-only surface is **one**: `deepdive.js`'s re-run animation, which
recomputes deliberately because the live run *is* the feature. That is the honest candidate for a
researcher-only route.

---

## 5. Things that are easy to rediscover the hard way

- **The fold was mechanically safe.** All four folded files were single IIFEs exporting nothing to
  `window`; zero DOM-id collisions with `index.html` and zero global collisions. No renaming was
  needed. They now export exactly one namespace each, added by this work.
- **`app.js`, `detail.js` and `signals.js` are clean** on three of the five Part E problems: no
  raw ULIDs as content (the `PRJ-08421` codes are intentional display ids), no module ids in
  user-facing text, no unlabelled form fields. Their only issue is hard-coded colours —
  `detail.js` has ~15, mostly canvas drawing, and reads no CSS variable anywhere
  (`getComputedStyle`: zero hits), so there is no correct-pattern example in that file to copy.
  `app.js` has ~10, mostly SVG that already proves `var()` works. `signals.js` has none.
- **`index.html`'s remaining hex** is the decorative NYC skyline SVG (gradient stops and fills,
  ~30 literals). It is theme-specific art; decide deliberately whether it should repaint.
- **Verify survey findings before acting on them.** A prior sweep reported `ws-new-name` and
  `ws-new-sector` as having no labels; both had real `<label for=…>` elements. One false positive
  in a list of eleven.
- **The compute-library premise was wrong in the brief, and worth restating.** The fold was
  described as reducing enforcement from absence to discipline. In fact `index.html` already
  computed in the browser, extensively, before any of this; the four folded pages were the only
  ones that did not. Folding changed nothing about that either way.
- **Test environment.** No `DATABASE_URL` default exists (`settings.py:69-74`); every suite and
  the app itself refuse to start without one. Use a throwaway SQLite **outside** the repository,
  never production. One freshly migrated database per suite. Read counts from each suite's own
  `RESULT: n/n` line, never by grepping `PASS`/`FAIL`.

---

## 6. Suggested order for the next session

1. Wire a dev runner that serves the FastAPI app against a throwaway SQLite, and confirm
   `preview_list`'s `cwd` is `LinPRojectRadar` before trusting anything it shows.
2. Walk guarantee 1 end to end — create project, upload, signals, decide, advance — and verify
   3, 4, 6, 7, 8 and 10 in the DOM at 1280 / 1920 / 3840.
3. Fix whatever that surfaces.
4. Merge Parts A–E once it holds up.
5. Then Group 1's 79-site rewrite for guarantee 5, retiring the legacy ingest path and moving
   `deepdive.js` researcher-side.
