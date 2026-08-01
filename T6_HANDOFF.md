# T6 handoff — Part F merged, Parts A–E outstanding

T6 was scoped as one phase covering the expert reference lock (Part F), the integration of three
standalone pages back into the application shell (Parts A, A.1, B), the admin surface rework
(Part C), the role vocabulary (Part D), and an interface cleanup sweep (Part E).

**Only Part F is merged.** It was split off because it is additive, self-contained, and fully
tested, and because no interface depends on it yet. Parts A–E were deliberately left for a
session with full context: the fold is all-or-nothing, and the guarantees attached to it have to
be proven in a real browser at three viewport widths.

---

## 1. What Part F added

The expert reference is the standard every participant decision is scored against. Its evidential
value rests on one claim — it was committed before the expert saw the AI package. B1 created the
`expert_references` table and its `locked_at` column but never created the lock; until this change
`locked_at` was a timestamp like any other and nothing stopped a sealed reference from being
rewritten.

### Migration 0012 (`server/alembic/versions/0012_expert_reference_lock.py`)

- Installs `trg_expert_references_lock_guard`, which rejects any UPDATE to the seven fields that
  constitute the reference once `locked_at` is set, and rejects moving or clearing `locked_at`
  itself. Re-locking is as much a falsification as editing.
- **This reuses 0003's mechanism rather than inventing a second one**, as T6 required. The trigger
  rejects loudly with SQLSTATE `OG002` (distinct from the pre-judgment lock's `OG001`), and
  `research_audit.py` writes the audit row on a separate connection — a trigger that raises cannot
  durably record its own rejection, because whatever it inserts belongs to the transaction that is
  about to unwind. That reasoning is 0003's, measured there, and unchanged here.
- Adds a nullable `period` column. B1 scoped a reference to (scenario, expert); participant
  decisions are per period, so a four-period scenario would have had one reference to score four
  decisions against.
- Adds a unique index on `(scenario_id, expert_id, period)`. A second INSERT is the trivial way
  around a trigger that only guards UPDATE.
- `realism_review` is deliberately **not** protected — it is the one thing written after the lock.

### `server/app/research_expert.py`

Five actions, wired into `facade.dispatch_post`:

| Action | Purpose |
|---|---|
| `expertreferencelist` | The expert's assigned scenarios and per-period lock state. Package-free. |
| `expertevidenceget` | Base project evidence only. Package-free. |
| `expertreferencecommit` | Commits and locks in one statement. |
| `expertpackageview` | The package, refused until the reference is locked. |
| `expertrealismreview` | Post-lock realism review; does not touch the reference. |

Two properties are worth knowing before extending this:

- **Evidence is package-free by construction, not by gate.** `a_expertevidenceget` never reads
  `assignments.package_id` and never touches `decision_support_packages`. That is a stronger
  property than a conditional, because it cannot be got wrong by a future edit adding a branch.
  Preserve it.
- **`locked_at` is set in the same INSERT as the content.** There is no write-then-lock path,
  because that would leave a window in which an unlocked reference exists. Do not add one.

### `server/tools/leak_detector.py`

T4's `scan_for_leak` was extracted here so T4 and T6 share **one** definition of what counts as a
leak. Two copies would drift, and a drifted copy reports green while proving something weaker than
it claims — the exact failure B7b already demonstrated once, where a leak survived eight phases
behind a grep clause that could never be false. Adding a marker or field name here strengthens
every importing suite at once.

`test_decision_ui_t4.py` now imports from it. Its behaviour and check count are unchanged (73/73).

### `server/tools/test_expert_reference_t6.py` — 59 checks

Guarantee 8 (nothing action-bearing reaches an expert pre-lock) and guarantee 9 (post-lock
immutability) are proven here. The detector is proven able to **fail** before it is trusted:

1. Against planted blobs, in a self-test block.
2. Against a **real** deliberate leak — the live evidence handler is monkeypatched to attach the
   package, the identical assertion that passes on the real handler is run against it and required
   to fail, then the patch is removed and the handler re-verified clean.

Guarantee 9 is proven across four routes — API resubmission, ORM update, Core update, raw driver
SQL — plus clearing `locked_at`, plus a duplicate INSERT. Three durable audit rows result.

### Regression at merge

All 16 prior suites unchanged; T6 adds 59. **838 checks total, all passing.**

| Suite | Checks | | Suite | Checks |
|---|---|---|---|---|
| test_admin_ops_t7t8 | 59 | | test_export | 64 |
| test_assignment_blinding | 44 | | test_features | 36 |
| test_auth_session | 52 | | test_membership | 46 |
| test_decision_sequence | 60 | | test_pre_lock_guard | 20 |
| test_decision_ui_t4 | 73 | | test_research_identity | 41 |
| test_documents_b7b | 66 | | test_simulation | 27 |
| test_drive_import | 37 | | test_transitions | 58 |
| **test_expert_reference_t6** | **59** | | test_workspace_t3t5 | 39 |
| | | | test_writes_a1b | 57 |

Two things that look like failures and are not:

- `test_simulation` exits 1 on Windows with `UnicodeEncodeError: 'charmap' … 'μ'`. It is a
  console encoding fault while printing `μ`, not a test failure. Run with `PYTHONIOENCODING=utf-8`
  and it reports 27/27.
- `test_decision_ui_t4` prints a line containing the word `FAIL` — it is the label of T4's own
  self-test, *"the detector must FAIL on a planted leak before it is trusted"*. Grepping for
  `FAIL` to count failures gives a false positive on this suite.

### MIGRATION

`/readyz` reports 503 with `SchemaOutOfDate` until `alembic upgrade head` is run against the
target database. `expected_head()` in `server/app/db.py` derives the expected revision from the
migration scripts, so this happens automatically on deploy of this commit.

---

## 2. What Parts A–E still require

Nothing below is started. No file was removed and no route was deleted.

### Part A — fold three pages into the shell
`workspace.html`, `admin-ops.html` and `questionnaires.html` become `<section class="page"
data-page="…">` inside `index.html`, using the existing pattern. Then delete the files and their
routes in `server/app/main.py` (`spa_workspace`, `spa_admin_ops`, `spa_questionnaires`, and their
`_WORKSPACE_HTML` / `_ADMIN_OPS_HTML` / `_QUESTIONNAIRES_HTML` constants) so they 404.
`decision.html` and its route are also in scope — the decision sequence must be reachable without
a page load, and the separate debrief page is to be dropped.

The participant profile becomes a one-time first-run step after consent and before the first
decision — same JSON definition (`assets/questionnaires/intake.json`), different placement. It
must not be a navigation destination.

### Part A.1 — navigation
`index.html:433-448` currently carries five controls: Admin, Workspace, Decision, Questionnaire,
Admin Ops. Target is that a participant and an operational user see an **identical** set with no
admin, workspace or questionnaire item, and an admin sees exactly one more: Admin, tabbed, holding
user management (T2) plus membership, monitoring and export (T7).

Note there are **two** navigation surfaces and both need changing: the topbar in `index.html`, and
the runtime-built icon dock from the `DOCK_NAV` array at `app.js:1686`, which a comment at
`app.js:1673` calls "the SOLE navigation".

### Part B — participant workflow
Portfolio → create project → project list → open project → upload documents → see signals →
decide → advance, all without leaving the shell. Applies to every user; no separate participant
mode.

### Part C — admin surface
Remove the Scenarios and Assignment UI. **Do not delete B3's backend** — `adminscenariocreate`,
`adminscenariolist`, `adminassign`, `adminassignmentlist` stay and stay tested. Add project
membership management in its place using B8's `adminmemberadd` / `adminmemberrevoke` /
`adminmemberlist`. Keep Membership, Monitoring, Export.

### Part D — roles
Admin / Participant / User (operational), with PM or Observer per project; Expert presented as a
research-panel role rather than a peer.

**Reported as asked:** `Demo` is defined at `research_identity.py:65`, permitted by the CHECK
constraint at `research_models.py:101`, and offered in `admin.js:165`'s role dropdown — but
nothing anywhere branches on it. It is assignable and behaviourally inert. Not removed.

### Part E — cleanup
See §3 for the line-level inventory.

### Outstanding guarantees
1–7 and 10 are unproven and need a real browser at 1280 / 1920 / 3840. 8 and 9 are proven at the
server layer by the T6 suite; they will need re-proving at the DOM layer once an expert UI exists
(inspect DOM, every network response, every reachable JS variable).

---

## 3. What the next session should know before starting the fold

These came out of two read-only surveys and are the main thing that would otherwise be
rediscovered from scratch.

### The fold is mechanically safer than it looks
`workspace.js`, `admin-ops.js` and `questionnaires.js` are each wrapped in a single top-level
IIFE and **export nothing to `window`** — they only read `window.LinAuth` / `window.LinStore`.
There are **zero DOM id collisions** with `index.html` and **zero global name collisions** with
`app.js`. No renaming is required.

### The stated reason these pages were kept separate does not hold as a runtime hazard
`main.py:288-296` and the header comment in each of the three pages claim they must never load
`sim.js` / `simulations.js` / `categories.js`, which `index.html` loads on every request. All
three were read in full:

- `sim.js` — one IIFE, sole top-level effect is `window.LinSim = {…}`. No `DOMContentLoaded`, no
  timers, no `document.*` at all.
- `simulations.js` — same shape, exports `window.LinSimulations`. Its only `window.` references
  are inside a function body, checked at call time.
- `categories.js` — not an IIFE, assigns ~12 globals at top level, but every one is static data or
  a pure function declaration. No listeners, no timers, no DOM writes, no storage access.

They are load-and-wait libraries. Loading them alongside the folded sections changes nothing
observable.

**But the invariant they were protecting is real**, and the fold weakens how it is enforced. Today
it is *structurally impossible* for `workspace.js` to call `LinSim.monteCarloEAC()`, because the
function does not exist in that page's context. Once folded, `LinSim`, `LinSimulations` and
`categories.js`'s helpers are ambiently available in the same document, and nothing stops a future
edit — or a copy-paste from `app.js`/`detail.js`, which legitimately call these for the legacy
dashboard — from silently substituting client computation for the stored `computed_results` row.
The invariant moves from enforced-by-absence to enforced-by-discipline. Decide deliberately how to
hold it, and say so in the fold's commit message.

### One real behavioural hazard in the fold
`workspace.js:164-166` does `window.location.href = "index.html"` on sign-out. Folded, that
becomes a full SPA reload. It needs to call the shell's own sign-out path instead.
`openDocument()` at `workspace.js:533` builds a root-absolute `/documents/…` URL, which is
unaffected by nesting — that one is fine.

### Part E, line-level

**Theme.** `tests.html` is the only screen that does not link `radar.css` at all and defines a
complete private dark palette — `tests.html:7,9,11,12,13,14,16,17,18`. It renders dark regardless
of the selected theme, and some of its literals coincidentally match Gotham's tokens without being
wired to them, so a palette edit in `radar.css` silently desyncs it. Elsewhere: `index.html:54-244`
has hard-coded hex in the decorative SVG with no `var()` fallback (gradient stops and fills);
`color:#fff` on brand buttons is duplicated as a literal in `admin-ops.html:37,40,56` and
`decision.html:78` — `radar.css` has no `--on-brand` token, which is why.

**Typography.** Only `tests.html` declares a font stack outside `radar.css`
(`ui-monospace,Menlo,Consolas,monospace`, 13px). Note `radar.css` defines `--font-display`,
`--font-body`, `--font-mono` but **no numeric type scale**, so "one scale across the platform"
means introducing one, not conforming to an existing one.

**Raw ULIDs as content.** `admin-ops.js:196` (`scenario_id` under a "Scenario id" column),
`admin-ops.js:252` (`scenario_id` under "Scenario"), `admin-ops.js:335` (`export_id` as the first
column), `workspace.js:230-231` (`project_id` in the sub-line of every project card, and as the
title fallback), `workspace.js:253` (`project_id` as the visible option label when name is empty).
Ids used as `data-*` attributes, option `value`s and API arguments are correct and were not
flagged. Worth knowing: `admin-ops.js:13-20,249-250` shows the same file deliberately *omitting*
`config_id`/`package_id` for blinding — so the exposures above read as oversight, not intent.

**Placeholder-as-label.** Eleven fields, none with an associated `<label>`. The worst are
`admin-ops.html:110` (`scenario_version`), `:111` (`project_type (optional)`), `:120`
(`order_group`), `:121` (`scenario_set`), `:124` (`scenario_ids, comma separated`) — raw variable
names as user-facing text. Also `admin-ops.html:88,161,162`, `workspace.html:131,133`, and
`decision-ui.js:550,552,554` (plain English, but no `.dc-label` where sibling fields in the same
file have one). `questionnaires.js:122` is the clean counter-example — every generated field gets
a real `<label for=…>`. If the questionnaire markup survives the fold, keep that.

**Navigation language.** `index.html` shows "Admin" (in-page panel) beside "Admin Ops" (separate
page) — two near-identical labels, two different surfaces. Separator differs: plain `·` at
`admin-ops.html:74` vs `&nbsp;·&nbsp;` at `decision.html:116-117`, and the link order is reversed
between them. `questionnaires.html` has no back-navigation at all. "Instrument home" and
"Workspace" are otherwise used consistently — they are the strings to replace wholesale.

**Module ids in user-facing text.** None found. `workspace.js:34-106` holds `A1.1`-style codes as
object keys only, and `moduleName()` at `:100` falls back to `"Unrecognised analytical module"`
rather than the raw code, so even its failure path does not leak one.

### One gap the survey could not close
`app.js` (2649 lines), `detail.js` (2049) and `signals.js` (1858) were **not** swept exhaustively
for raw-id-as-content or hard-coded colours. They render most of `index.html`'s dynamic content.
Treat the Part E inventory as complete for every screen except those three, and sweep them before
claiming guarantees 4 and 5.

### Test environment
Every suite and the app itself refuse to start without `DATABASE_URL` (`settings.py:69-74`); there
is no default. For local work use a throwaway SQLite file outside the repository — the settings
module itself suggests the form — and never point a suite at production. Suites are run as
`DATABASE_URL=… SESSION_SECRET=… python tools/test_*.py`, one freshly migrated database per suite,
and each prints its own `RESULT: n/n checks passed` line. Use that line for counts rather than
grepping for `PASS`/`FAIL`.
