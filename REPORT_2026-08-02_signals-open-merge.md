# The project list carries one control to the detail page, not two

2026-08-02. Merged at `origin/main` = `757ee4b` (#203). **Server suites 1338/1338 across 23 suites,
`tests_render.html` 49/49 (up from 43/43), `tests.html` 51/51, all green on merged `main`.** No
stored data altered, production not inspected, nothing under `server/app/simulation/` touched.

## 1. They were the same control. Established before anything was changed.

The task said to verify the premise and to stop rather than collapse the controls if a user would
notice a difference. The premise holds, and it holds on every axis I could find one:

**The handlers were the same expression.** At `assets/js/app.js:1326-1327`, before the change:

```js
btn.querySelector(".li-open").addEventListener("click", () => openDetail(p.id));
btn.querySelector(".li-signals").addEventListener("click", () => openDetail(p.id));
```

Same function, same argument, no second parameter, no ordering effect. The comment above them
already said so: `// Signals + Open → both land on Detail`.

**`openDetail` cannot express a difference.** `app.js:1768`:

```js
function openDetail(id) {
  selectedId = id;
  showPage("detail");
  try { selectProject(id); } catch (e) { /* ... */ }
  hydrateFullProject(id);
}
```

It takes an id and nothing else. There is no section argument, no tab argument, no scroll target,
no hash, and `showPage("detail")` receives no second parameter. So the "opens the detail page at
the signal ledger" reading that the Signals tooltip implied is not something this code path is
capable of doing.

**Nothing else listened.** `li-signals` and `data-signals` appear, across the whole repository, in
exactly three places: the button's own markup, the `stopPropagation` selector list beside
`.li-manage, .li-open`, and the click handler above. No delegated listener, no `data-signals`
reader anywhere in any js, html or css file. The `data-signals` attribute was written and never
read by anything.

**The CSS was identical, not merely similar.** `.li-open` and `.li-signals, .li-manage` carried
byte-identical rule bodies (same font, size, padding, radius, border, background, colour, cursor)
and identical `:hover` rules. The two buttons were indistinguishable visually as well as
behaviourally.

The only differences were the label and the `title` tooltip. The tooltip was the more interesting
one, because it made a promise the code did not keep: `title="Open the signal ledger on the Detail
page"` versus `title="Open project detail"`. Since `openDetail` has no way to land on a section,
the Signals tooltip described behaviour that did not exist. That is an argument for removing it,
not for preserving it.

## 2. Which label was kept, and why

**Kept `Open →`.** `NAMING_AUTHORITY.md` is the deciding authority and it points one way:

- Section 5 records that "Anything that says the browser computes signals is stale". "Signals" on
  a row control is a word out of the retired framing, sitting on the surface a user reads first.
- The naming rules forbid module ids and numbers in user-facing text and, more generally, push
  toward naming what a thing does rather than what the system calls it internally.
- "Signals" names an internal concept — the signal ledger, `signalInputs`, `hasSignals` — and the
  project row is not where a user learns that vocabulary. "Open" names the action the control
  performs, which is the whole of what it does.

The arrow in `Open →` is kept as it was. It is not an em dash and `NAMING_AUTHORITY.md`'s
prohibition does not reach it; changing it would be churn beyond the task.

The surviving control keeps `title="Open project detail"`, which describes what happens. The
tooltip that promised a signal ledger is gone with the button that carried it.

## 3. The label elsewhere: swept, and nothing needed changing

The task warned that a control renamed in one place and described by its old name in another is
the pattern that produced three incompatible taxonomies. I swept for it and found no such case.

**What was searched:** every `.js`, `.html`, `.css` and `.md` file in the repository for
`li-signals`, `data-signals`, `"Signals"`, `'Signals'`, `>Signals<`, `the Signals`, `Signals
button`, `Signals control`, `press Signals`, `click Signals`, and `Signals or Open`.

**What the hits were, none of them this control:**

| Where | What it is | Action |
|---|---|---|
| `assets/js/knowledge.js`, many | The analytical vocabulary: "Document-Derived Condition Signals", "Document and Risk Signals", module reference prose | Left. Different concept, correctly named. |
| `assets/js/signals.js:397`, `BACKEND_CHANGES_NEEDED.md:371` | "the signal ledger, the Signals page, and the executive brief" — the retired standalone Signals page, folded into Detail (the consolidation redirect at `app.js:1843`) | Left. Refers to a page, not this row button, and is already-known stale prose about a retired surface. |
| `index.html:629` | `<button data-wstab="detail">Signals</button>` — the **workspace tab strip**, a different surface with its own routing | Left. Not the project list. Renaming it is a separate decision about a different control. |
| `assets/js/deepdive.js:2057` | A metric box labelled "Signals" inside a module visualisation | Left. Unrelated. |

**The assistant's scripted answers do not name this control.** `assistant.js` and `knowledge.js`
were read specifically for guidance text about the project list. The one place that describes how
to reach the detail page is `knowledge.js:88`, and it is already generic and already correct:

> "Click a blip, or use the project list, to open that project's Detail page with its signal ledger
> and decision card."

It says "use the project list" rather than naming a button, so it was accurate before this change
and stays accurate after it. No documentation, help text or scripted answer required an edit. I
would rather report that plainly than manufacture a change to look thorough.

## 4. What changed

Three files, and the whole functional change is the removal of one button and its handler.

- **`assets/js/app.js`** — the `Signals` button removed from the row markup; its click handler
  removed; the `stopPropagation` selector narrowed from three classes to two; the comment replaced
  with one recording that the two handlers were the same call and why "Open" was the label kept.
- **`assets/css/radar.css`** — `.li-signals` dropped from the two rules that carried it, and the
  action-cluster comment corrected from `Signals · Manage · Open →` to `Manage · Open →`. It now
  describes what the cluster is. Leaving a dead selector behind is how the next session concludes
  the button still exists.
- **`tests_render.html`** — a new group 4b over the action cluster. See below.

## 5. The check, and proof that it can fail

**Nothing covered the row's action cluster before.** `tests_render.html` group 4 calls
`buildFallbackList()` — the same function — but asserts only on the status word's colour and
class. Both controls could have been deleted, or duplicated, and it would have stayed green.

Group 4b adds six assertions: the list builds without throwing, the cluster is present, `.li-signals`
count is 0, `.li-open` count is 1, the label is exactly `Open →`, and the cluster's button labels
join to exactly `Manage|Open →`.

**The last one is deliberate and is the reason this group is not just a class check.** Asserting
only `document.querySelectorAll(".li-signals").length === 0` passes if someone deletes the button
and adds a differently-classed control labelled "Signals" back into the cluster. Asserting the
label sequence catches that. Faults 1 and 2 below take different routes to failure precisely
because of it.

**Three faults, three distinct signatures, restored and re-checked green after every one:**

| Fault | Result | Which checks went red |
|---|---|---|
| Baseline, no fault | **49/49** | none |
| 1. `Signals` button restored to the markup | **47/49** | 30 (`no Signals control remains`), 33 (cluster order) |
| restored | **49/49** | none |
| 2. Merged control relabelled `Signals` | **47/49** | 32 (`labelled for the action it performs`), 33 (cluster order) |
| restored | **49/49** | none |
| 3. `Open →` button duplicated | **47/49** | 31 (`exactly one Open control`), 33 (cluster order) |
| restored | **49/49** | none |

Each fault produced a red on a *different* check, which is what establishes that the six
assertions are not one assertion written six ways. The handoff records a previous session whose
revert silently corrupted the module and whose harness printed success without matching; every
restore above was re-run to full green before the next fault was applied, and the final restore
was confirmed by reading the rendered row markup out of the DOM, not only the pass count.

## 6. Verification by DOM read, both account types

There is no compositing in this container, so the evidence below is read out of the live DOM, not
taken from a screenshot.

**How the app was served.** `preview_start` resolves `.claude/launch.json` from `DEng\Demo`, whose
only entry points at `Demo/opus-gubernatio`, a different repository. **I did not add an entry there
and nothing under `Demo` was modified.** Instead the real FastAPI app was run on 127.0.0.1:8011
against a throwaway sqlite built with `alembic upgrade head` in the scratchpad, and the browser was
pointed at it with `preview_start {url}`, which needs no `launch.json` at all. `main.py` serves
`index.html` and `/assets` from the same origin as `/exec`, so this is the real application, not a
static mirror. The two browser suites, which the app does not serve, were run off a plain
`http.server` on the repository root at 127.0.0.1:8012.

**Fixtures.** An operational account (`verifyadmin`, ResearchAdmin, created by
`tools/bootstrap_admin.py`) and a research account (`VERIFY-RSCH`, Participant, created through
`adminparticipantcreate`), one project each, PM membership on each. `listslim` confirmed the scoping
was real: each account saw exactly its own project, not the other's.

**Read on merged `main`, operational account:**

```json
{ "signedInAs": "verifyadmin", "rowCount": 1,
  "signalsControls": 0, "openControls": 1, "anySignalsLabel": false,
  "labels": [["Manage", "Open →"]],
  "afterClick": { "children": 12, "text": "← Back to Portfolio … Project detail PRJ-OPS-1 Operational v…" } }
```

**Read on merged `main`, research account:**

```json
{ "signedInAs": "VERIFY-RSCH", "rowCount": 1,
  "signalsControls": 0, "openControls": 1, "anySignalsLabel": false,
  "labels": [["Manage", "Open →"]],
  "afterClick": { "children": 12, "text": "← Back to Portfolio … Project detail PRJ-RSCH-1 Research ver…" } }
```

`anySignalsLabel` scans every `button` in the list for the text `Signals` regardless of class, so
it would catch a survivor that had lost its class. Both accounts: one control, correct label, and
it navigates to the right project's detail page with a populated root (12 children, not the blank
page of the 2026-08-02 defect).

`buildFallbackList` contains no `account_type` branch, which is why the two reads agree. That was
read out of the code as well as measured.

**A zero that was not a regression, worth recording.** The research account first rendered **0
rows**, which is exactly the shape an over-refusing filter takes and is the failure the handoff
warns reads like a real regression. It was not one: `routeFromView` in `auth.js` sends a research
participant without consent to the consent screen, so `LinApp.init()` never runs and the portfolio
is never loaded. After `consentgrant` the row rendered. Nothing about the list was wrong; the
account was never past the gate.

## 7. Suites

Run per the handoff's rule, each suite against its own byte copy of a pristine migrated sqlite,
because six of them collide on shared state. The runner reports a suite printing **no `RESULT:`
line** as CRASHED rather than letting it skim as clean.

**Server: 1338/1338 across 23 suites on merged `main`.** `tests_render.html` **49/49** (43/43
before this change). `tests.html` **51/51**.

**One environment trap, and it cost a full run.** `test_simulation.py` died with
`UnicodeEncodeError: 'charmap' codec can't encode character 'μ'` and printed no `RESULT:`
line. This container's default stdout encoding is cp1252 and the suite prints a `μ`. It is not a
code defect and there is nothing to fix in the repository; **set `PYTHONIOENCODING=utf-8` before
running the suites here.** With it set, 29/29.

**One failure observed once and not reproduced, reported rather than chased.** In the first full
run, `test_admin_ops_t7t8.py` returned 56/59, the three reds all in Guarantee 7 (`fetch fails after
the underlying data changed`, `the failure names itself as a checksum verification failure`, `no
payload key at all on a checksum mismatch`). That guarantee tampers with a stored `Decision` and
expects the export's checksum to stop verifying. It has since returned **59/59 (now 60/60 after the
merge) in twelve consecutive runs**, across both stdout encodings and against fresh databases each
time. `server/app/research_export.py` is **uncommitted-modified by a parallel session**, and the
most likely explanation is that the first run read that file in an intermediate state in which the
tampered column was momentarily outside the export's column set, so the checksum did not move. I
have not chased it further because the file belongs to another session's in-flight work and my
change does not touch it. **Flagged for whoever owns that change to confirm.**

## 8. Files another session owns

**I touched one file another session had uncommitted work in: `assets/js/app.js`.** That session
had changed the Handbook fly-out pill from `Methods & Framework` to `Methods and Framework` at
line 2285, with a paired edit in `index.html`.

That work was **not** swept into my commit. The commit was built by staging only my own hunk
(`@@ -1314,17 +1314,18 @@`) with `git apply --cached`, leaving theirs in the working tree.
Merging `origin/main` then required their uncommitted changes to be stashed; they were backed up to
the scratchpad first, and `git stash pop` restored them cleanly afterwards. Verified after the
merge: their `Methods and Framework` change is still present and still uncommitted, and their
`index.html` edit is untouched.

Working-tree files left modified and belonging to other sessions, none of them mine and none
committed by me: `assets/js/app.js` (their hunk only), `assets/js/disclaimers.js`,
`assets/js/ds_defensibility_data.js`, `assets/js/export.js`, `index.html`,
`server/app/research_export.py`, `server/app/simulation/registry.py`,
`server/tools/test_disclaimers.py`, `server/tools/test_export.py`,
`server/tools/test_group_assignment.py`, `server/tools/test_simulation.py`.

## 9. Not done, deliberately

- **The workspace tab strip's `Signals` tab (`index.html:629`) was not renamed.** It is a different
  control on a different surface with its own routing. The task was the project list's two
  controls. Renaming it is a real question — the same NAMING_AUTHORITY argument applies — but it is
  a decision about the workspace, and collapsing it into this change would be exactly the
  scope creep that produces surfaces nobody decided on.
- **The retired standalone "Signals page" prose in `signals.js:397` and
  `BACKEND_CHANGES_NEEDED.md:371` was left.** It describes a surface that no longer exists,
  which is a pre-existing staleness, not something this change created or made worse.
- **Nothing was backfilled and production was not inspected.**
