# Run 56: the duplicate controls, and two confirmations

**Repository:** the Linux clone at `/home/user/LinPRojectRadar`. The Windows path was not used
and was not reachable, as Run 55 also recorded.
**Interpreter:** `python3` 3.11.15, the documented fallback. `ls -d .venv` -> no venv, so
`server/run_all_suites.sh` falls through to `command -v python3` as it is written to.
**Branch:** `run56-duplicate-controls`, rooted at `e13b4f1`.
**Stamp:** `sim-2026.08-v37`. **Package:** `og-participant-2026.08-v22`. **Freeze gate 34/34.**

---

## THE HEADLINE

1. **All three phases were completed and each was committed before the next began.**
2. **PHASE A IS HALF CARRIED AND HALF STOPPED, AND THE STOPPED HALF IS THE FINDING.** The
   duplicate "Upload documents" is gone from the detail page. **The ordered removal of
   `.detail-reset` was STOPPED under section 9.1: the order's premise that `.pe-reset` "clears
   more" is FALSE against the code.** Measured byte for byte at the explicit commit `e13b4f1`,
   **neither reset control is a superset of the other**, so removing either loses something the
   survivor does not do. Both remain. Runs 52, 53, 54 and 55 each found an order resting on a
   premise the code contradicted; this is Run 56's.
3. **PHASE B REUSED THE PATTERN THE APPLICATION ALREADY HAD, AND THE REASON NOT TO USE THE OTHER
   ONE WAS ALREADY WRITTEN DOWN IN THE REPOSITORY.** Four files record that `window.confirm`
   returns false in this container. Gating Archive on it would have made Archive impossible to
   perform, which is section 10.9. `LinUI.openModal` was reused instead.
4. **THE MINT IS PAID AND THE 34-ROW FREEZE GATE IS 34/34**, re-run on the committed tree.
   **SEVEN MINTS WERE PAID.**
5. **THE BEHAVIOUR DIGEST WAS RE-DERIVED SEVEN TIMES, NOT ASSUMED**, and comes back
   `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1` every time.
6. **TWO STALE GUARDS FOUND THAT THIS RUN DID NOT CREATE.** `test_run37_freeze_gate.py` was still
   pinned at the **RUN 51** release record and at **RUN 48's** candidate as the no-self-reference
   parent. The two stale pins were agreeing with each other, so gate rows 28, 33 and 34 had been
   asserting the disposition of a release three mints old. Both revised, neither deleted.
7. **INCIDENTAL: the Run 55 release report shipped headed "Run-52 successor freeze report" for
   `sim-2026.08-v35`.** The builder's report body had never been advanced past Run 52.

---
## 1. The tree at the start

| Claim | Verified by | Found |
|---|---|---|
| tree clean | `git status --porcelain` | **EMPTY.** No leaked fault, nothing half-written. |
| `main == origin/main == HEAD` | `git rev-parse HEAD main origin/main` | all three `e13b4f1905de3cd9703d4b2242f278b104c06774` |
| branch at start | `git branch --show-current` | `main`; work was done from `run56-duplicate-controls`, branched at `e13b4f1`, never from `main` |
| stamp | `grep -n SIMULATION_VERSION server/app/simulation/models.py` | `sim-2026.08-v36` at **line 689** of `server/app/simulation/models.py` (not `server/app/models.py`) |
| package | `participant_packages.CURRENT` | `og-participant-2026.08-v21` |
| interpreter | `python3 -V`, `ls -d .venv` | `Python 3.11.15`; **no `.venv`**, so the documented fallback |
| suites / checks / gate / digest | inherited from Run 55 and re-verified below | 203, 15269, 34/34, `8fb4d366…` |

**Nothing was dirty. No leaked fault.** The campaign guard had nothing to refuse.

---

## 2. PHASE A

### 2.1 Every `openInlineManage` call site, established by execution and by an UNCAPPED sweep

The sweep was `grep -rn "openInlineManage"` over the whole repository with **no head limit**, on
the standing rule that a truncated grep reads exactly like a complete one.

| # | Site | What it is | Reached? |
|---|---|---|---|
| 1 | `assets/js/ingest.js:270` | `function openInlineManage(id, hostEl) {` | the **definition**, not a call |
| 2 | `assets/js/ingest.js:469` | `openInlineManage(finalId, hostEl);` | **A REAL CALL SITE, INTERNAL.** The last thing the **Save info** handler does on success: it re-opens the (rebuilt) panel so the geocode outcome can be surfaced. **It forwards the same `hostEl` it was built with**, so on the detail page it rebuilds the hosted panel and on a row it rebuilds the row's. |
| 3 | `assets/js/ingest.js:790` | the `window.LinIngest = { … }` export | an export, not a call |
| 4 | `assets/js/detail.js:2328` | `try { LinIngest.openInlineManage(id, host); }` | **A REAL CALL SITE.** `wireDetailAdmin()`, guarded one line above at `:2327` by `typeof LinIngest.openInlineManage === "function"`. This is the hosted detail-page mount. |
| 5 | `assets/js/app.js:1106` and `:1116` | **COMMENTS**, recording Run 54's removal. Not call sites. Established by stripping `//` lines and re-testing, which is the same discrimination Run 55's driver makes. |
| 6 | `assets/js/detail.js:1074`, `code_audit/*.sha256`, `T6_HANDOFF.md`, three suites and two drivers | prose, guards and evidence. Not call sites. |

**So there are exactly TWO reachable call sites: `detail.js:2328` (hosted) and `ingest.js:469`
(internal re-open, which forwards `hostEl`).** There is **no surviving row-path call site** —
Run 54 removed it — so in the live application the hosted path is the only path.

**Does removing `.pe-populate` from the detail page affect `ingest.js:469`?** It affects it in
exactly the way it should and in no other. That site passes `hostEl` straight through, so the
panel it rebuilds after a save is the **same panel the reader was looking at**, with the same
five controls. Had the removal been done any other way — a second builder, a post-hoc DOM
removal — the re-open would have silently put the duplicate back. **Measured**: after phase A,
the moved panel's control list on every one of three projects is
`['Save info', 'Recompute this project', 'Reset signals', 'Archive', 'Close']`.

### 2.2 PAIR 1, UPLOAD — the handler comparison, pinned to `e13b4f1`

```
.pe-populate   @e13b4f1 : box.querySelector(".pe-populate").addEventListener("click", () => {
                            openUploadModal(id); }
.detail-upload @e13b4f1 : root.querySelectorAll("[data-upload]").forEach((b) =>
                            b.addEventListener("click", () => {
                              if (window.LinIngest && LinIngest.openUploadModal)
                                LinIngest.openUploadModal(b.dataset.upload); }
.pe-populate body statements: ['openUploadModal(id);']
```

The whole of `.pe-populate`'s body is **one statement**. That is enumerated, not eyeballed: every
non-empty line of the handler body is listed and there is exactly one. `.detail-upload` calls the
same function, and the id it passes is `data-upload="${esc(p.id)}"`, which `detail.js` renders
from `render()`'s own `p.id` — **the same project**. `.detail-upload` is additionally guarded by
a `typeof` check that `.pe-populate` did not have.

**VERDICT: `.pe-populate` does NOTHING that `.detail-upload` does not. The removal loses nothing
and PROCEEDED.**

### 2.3 PAIR 2, RESET — THE SECTION 9.1 STOP, AND EXACTLY WHAT WOULD HAVE BEEN LOST

The order rules: *"Keep the moved `.pe-reset`. Remove `.detail-reset`. `.pe-reset` clears more,
so it is the one that survives."* **That premise is FALSE against the code.** Measured by
extracting both handler bodies from `e13b4f1` and comparing them behaviour by behaviour:

| behaviour | `.detail-reset` | `.pe-reset` |
|---|---|---|
| `LinStore.resetSignals(` | **True** | **True** |
| `LinSignals.clearCache(` | **True** | **True** |
| `LinResults.clear(` | **True** | False |
| `LinStore.load(` | False | **True** |
| `logEvent(` | False | **True** |
| `LinApp.refresh(` | **True** | **True** |
| `renderPortfolioAdmin(` | False | **True** |
| `render(id)` | **True** | False |
| `LIN_PROJECTS` | **True** | False |
| `LinStore.getProject(` | **True** | False |
| `p.history = []` | **True** | False |

```
ONLY .detail-reset does: ['LinResults.clear(', 'render(id)', 'LIN_PROJECTS',
                          'LinStore.getProject(', 'p.history = []']
ONLY .pe-reset does    : ['LinStore.load(', 'logEvent(', 'renderPortfolioAdmin(']
```

**NEITHER CONTROL IS A SUPERSET OF THE OTHER.** Removing `.detail-reset`, as ordered, would have
lost **four things the survivor does not do**:

1. **`LinResults.clear()`** — the derived-results cache is dropped. `.pe-reset` never calls it.
   `detail.js` carries a long comment recording exactly why this line exists: without it, the
   browser drive found a cleared project *still drawing 41 modules with a current result and a
   project rollup of Amber in the same session*, from a row the server had already retired.
2. **The `LIN_PROJECTS` re-fetch** — `await LinStore.getProject(id)` and splicing the fresh copy
   back into the in-memory list.
3. **Forcing the in-memory record to a true "Awaiting ingest" state** — `p.signals`,
   `p.signalInputs`, `p.simulationSignals`, `p.status`, `p.reportingPeriod`, `p.derivedState` to
   null, `p.history = []`, and the `documents` / `uploadedDocuments` / `docs` arrays emptied.
4. **`render(id)`** — the detail page is re-rendered so it actually shows the cleared state.

Removing `.pe-reset` instead would have lost `LinStore.load()`, the append-only `logEvent()`
entry and `renderPortfolioAdmin()`. **There is no safe direction.**

**SECTION 9.1 THEREFORE FIRES: that removal is STOPPED, both controls are LEFT IN PLACE, and the
detail page still carries TWO controls that clear stored signals — deliberately and on the
record.** `assets/js/detail.js` did not move at all this run.

**THE SCOUTING HYPOTHESIS AT DISPATCH WAS ALSO FALSE, AND IS RECORDED AS FALSE.** It was
suggested that `.detail-reset` reports through an `aria-live` region and `.pe-reset` does not.
Both do: `detail.js` carries `<span class="detail-reset-msg kn-sub" aria-live="polite">` and
`ingest.js` carries `<p class="pe-msg kn-sub" aria-live="polite">`. Accessible status feedback is
**not** the differentiator. The differentiator is the four items above.

### 2.4 The detail page's FULL control inventory, before and after, measured live

"Before" is not reconstructed. It was measured **live on a second browser** with `e13b4f1`'s
`ingest.js` injected **from the committed reference**, restored inside a `finally`, with the tree
checked before and after and found byte-identical.

**BEFORE (PRJ-R50-BROWSER):**
```
detail-head controls : ['<- Back to Portfolio', 'why?', 'Upload documents',
                        'Generate signals for every period',
                        'Clear stored signals for this project', 'Save info',
                        'Upload documents', 'Recompute this project', 'Reset signals',
                        'Archive', 'Close']
admin panel order    : ['Save info', 'Upload documents', 'Recompute this project',
                        'Reset signals', 'Archive', 'Close']
upload controls      : ['Upload documents', 'Upload documents']        <- TWO
pre-existing .detail-head-actions : ['Upload documents',
                        'Generate signals for every period',
                        'Clear stored signals for this project']
```

**AFTER (measured on all three of PRJ-R50-BROWSER, PRJ-R54-B, PRJ-R54-C):**
```
detail-head controls : ['<- Back to Portfolio', 'why?', 'Upload documents',
                        'Generate signals for every period',
                        'Clear stored signals for this project', 'Save info',
                        'Recompute this project', 'Reset signals', 'Archive', 'Close']
admin panel order    : ['Save info', 'Recompute this project', 'Reset signals',
                        'Archive', 'Close']
upload controls      : ['Upload documents']                            <- ONE
reset controls       : ['Clear stored signals for this project', 'Reset signals']  <- TWO, 9.1
pre-existing .detail-head-actions : UNCHANGED, the same three, same order
```

- **EXACTLY ONE control opens the upload dialog**, on each of three projects.
- **The head as a whole lost EXACTLY ONE control, no more and no less.**
- The panel still acts on the viewed project and no other: `data-admin-for` and the panel's
  project-number field both read back the viewed id on every project.
- **`why?` appears only on PRJ-R50-BROWSER** because that is the only fixture with provenance to
  trace. It is pre-existing and untouched.

### 2.5 Dead CSS: the honest answer is that there was none, and the check is VACUOUS

```
.pe-populate rules in radar.css at e13b4f1: 0   now: 0
```

**`radar.css` carried NO `.pe-populate` rule at `e13b4f1` either.** The removal therefore left no
dead CSS rule behind and **none was removed**. The absence check is vacuous and is reported as
vacuous rather than presented as a passing guarantee. This is unlike Run 55's `.li-open`, which
genuinely had four dead rules.

`.detail-reset-msg { margin: 0; }` at `radar.css:895` — the rule the dispatch note flagged as a
removal candidate — **is NOT dead and was NOT touched**, because its control survives.

### 2.6 The other four moved controls

Untouched by phase A, and measured: **Save info, Recompute this project, Reset signals, Archive**
and **Close** each still render **exactly once** in the moved panel on each of three projects.

### 2.7 The browser session

Run 55's environment reused, not rediscovered. Chromium at
`/opt/pw-browsers/chromium-1194/chrome-linux/chrome` by explicit `executable_path`;
`args=["--use-gl=swiftshader","--no-sandbox","--headless=new"]`; `python3 -u`; driver run from a
**clean subdirectory** with the cwd printed first.

```
browser session cwd: .../scratchpad/run56drivers/phaseb
repository root:     /home/user/LinPRojectRadar
in service:          63    registry: 101    retired: 38
  PASS  7 .page sections
  PASS  neither api.js nor boot.js in document.scripts
```

The `DEng\Demo` tell was measured: **7 `.page` sections, `api.js`/`boot.js` in
`document.scripts` = `[]`.** The application under test is the right one.

**`server/tools/drive_run56_duplicate_controls.py`. RESULT: 92 passed, 0 failed. Page errors: `[]`.**

---
## 3. PHASE B

### 3.1 The confirmation pattern the application ALREADY has, established FIRST

Section 7 requirement 6 orders that this be established before anything is implemented. It was,
by counting calls with comment lines stripped:

```
app.js           window.confirm calls= 1   LinUI.openModal calls= 0
decision-ui.js   window.confirm calls= 1   LinUI.openModal calls= 0
ingest.js        window.confirm calls= 2   LinUI.openModal calls= 7
admin-ops.js     window.confirm calls= 0   LinUI.openModal calls= 1
workspace.js     window.confirm calls= 0   LinUI.openModal calls= 0
detail.js        window.confirm calls= 0   LinUI.openModal calls= 0
```

**TWO patterns exist.**

- **Pattern 1, `window.confirm(...)`.** `app.js:2485` gates "Recompute every project" with a
  multi-line message ending "Continue?". `decision-ui.js:488` gates "Commit your preliminary
  judgment?".
- **Pattern 2, `LinUI.openModal(...)`.** The shape used for destructive **project-scoped**
  actions: this file's own `openDeleteArchivedModal` and `admin-ops.js`'s
  `openDeleteProjectModal`.

**PATTERN 2 WAS REUSED, AND THE REASON IS ALREADY WRITTEN DOWN IN THE REPOSITORY IN FOUR PLACES.**
`ingest.js`, `admin-ops.js`, `workspace.js` and `detail.js` each record that `window.confirm`
**returns false in this container and in any dialog-suppressing browser**. `workspace.js:504`
puts it plainly: *"an action behind that is an action nobody can take."* `detail.js:1057` says
the platform *"has already lost one action that way."*

**Gating Archive on `window.confirm` would therefore have made Archive impossible to perform in
this environment — which changes what the confirmed action does, and is section 10.9.** It was
not used. Measured: the new helper contains no `window.confirm`.

**NO TYPED CONFIRMATION.** The typed-project-id shape is this application's answer to
**permanent delete**. Archive is reversible from the Archived dialog's Restore, and Reset signals
keeps the documents. Reusing the typed shape here would overstate both actions.

### 3.2 NO CONTROL WAS ADDED — section 7 requirement 5 and section 10.6

The dialog carries **ONE button, the confirm**, exactly as `openDeleteArchivedModal` does.
Cancelling is `LinUI.openModal`'s own `x`, `Escape` and backdrop, which **every dialog in the
application already provides**. Nothing is added to the page; the dialog exists only while open.

Proved live against the phase A commit `527cf08`, with its `ingest.js` injected from the
committed reference and restored inside a `finally`:

```
detail-page controls at 527cf08 (phase A only): ['<- Back to Portfolio', 'why?',
  'Upload documents', 'Generate signals for every period',
  'Clear stored signals for this project', 'Save info', 'Recompute this project',
  'Reset signals', 'Archive', 'Close', 'Regenerate', 'Free rotate', 'Top',
  'Cost cluster', 'Evidence cluster', 'Governance', 'Free rotate', 'Front', 'Side', 'Top']
detail-page controls now (phase A + phase B): IDENTICAL, all twenty
  PASS  PHASE B ADDED, MOVED AND REMOVED NO REACHABLE CONTROL
```

### 3.3 The exact confirmation text, READ BACK FROM THE RENDERED PAGE

**Archive:**
```
title  : 'Archive PRJ-R50-BROWSER'
detail : 'This moves PRJ-R50-BROWSER out of the active portfolio. Its documents and its
          computed results are kept, and it can be brought back from the Archived dialog.
          Nothing is deleted and no other project is touched.'
button : 'Archive PRJ-R50-BROWSER'
```

**Reset signals:**
```
title  : 'Reset signals for PRJ-R50-BROWSER'
detail : "This clears PRJ-R50-BROWSER's stored signal values so its documents can be read
          again. It does not delete documents and it does not touch other projects."
button : 'Reset signals for PRJ-R50-BROWSER'
```

The Reset wording is the **application's own wording for this action**, taken from the `title`
attribute `detail.js` already carries on `.detail-reset`, so the two controls that clear stored
signals describe themselves the same way.

- **Each NAMES THE PROJECT** in its title, its detail sentence **and** on its button.
- **That identifier is the one RENDERED ON THE PAGE**: asserted equal to the detail heading's
  `#detail-root h1 .mod-mono`, which read back `'PRJ-R50-BROWSER'`.
- **No em dash and no en dash.** **No ampersand.** Identifiers on screen, which are allowed.

### 3.4 CANCEL DOES NOTHING AT ALL — proved BY EXECUTION, not by reading

`LinStore.archiveProject`, `resetSignals`, `load`, `saveProject` and `deleteProject` were wrapped
in **counting spies**, and `LinApp.showPage` in a **navigation spy**, before the control was
clicked. Then `Escape`:

```
Archive        after CANCEL: store calls=[]  navigation=[]  modals=0  page=['detail']
  PASS  Archive: CANCEL MADE NO CALL -- LinStore was not touched at all
  PASS  Archive: CANCEL CAUSED NO NAVIGATION
  PASS  Archive: the dialog closed
  PASS  Archive: CANCEL CHANGED NO STATE -- the same detail page for PRJ-R50-BROWSER is
        still open with its panel intact

Reset signals  after CANCEL: store calls=[]  navigation=[]  modals=0  page=['detail']
  PASS  Reset signals: CANCEL MADE NO CALL -- LinStore was not touched at all
  PASS  Reset signals: CANCEL CAUSED NO NAVIGATION
  PASS  Reset signals: the dialog closed
  PASS  Reset signals: CANCEL CHANGED NO STATE
```

`location.href` was also captured before and compared after: unchanged.

### 3.5 CONFIRMING DOES EXACTLY WHAT THE CONTROL DID BEFORE

**By bytes, against `e13b4f1`.** Each action body was moved unchanged into `doArchive()` /
`doReset()` and compared with the pinned pre-gate handler body, comments and whitespace
normalised away so the comparison is of the ACTION and not of its layout:

```
  PASS  Archive: the ACTION body is BYTE-IDENTICAL to e13b4f1 once the confirmation gate
        is stripped -- the confirmation changed nothing about what the action does
  PASS  Reset signals: the ACTION body is BYTE-IDENTICAL to e13b4f1 once the confirmation
        gate is stripped
```

**By execution**, on separate projects so the two cannot interfere:

```
CONFIRM Reset signals on PRJ-R54-B: store calls = ['resetSignals(PRJ-R54-B)', 'load()']
CONFIRM Archive on PRJ-R54-C:       store calls = ['archiveProject(PRJ-R54-C)']
portfolio after the confirmed archive: ['PRJ-R50-BROWSER', 'PRJ-R54-B']
  PASS  and the confirmed archive REALLY ARCHIVED PRJ-R54-C: it is gone from the active portfolio
```

### 3.6 Scope, stated plainly

The order names **Archive** and **Reset signals** — the two moved controls Run 55 section 2.3
identified. Those are `.pe-archive` and `.pe-reset`. **`.detail-reset` ("Clear stored signals for
this project") was NOT given a confirmation**, because it is not one of the two the order names
and adding one would have been unordered work on a control the order does not mention. It is
raised in section 10 as a decision for the owner.

---
## 4. PHASE C: the mint

### 4.1 Every piece

| # | Piece | Value |
|---|---|---|
| 1 | `sim-2026.08-v37` | `server/app/simulation/models.py`; `SIMULATION_VERSION_SUPERSEDED` -> `sim-2026.08-v36`; history **appended**, never edited (37 entries) |
| 2 | `og-participant-2026.08-v22` | appended to `PARTICIPANT_PACKAGES`; `CURRENT` |
| 3 | v21 **PINNED** | `og-participant-2026.08-v21`'s `source_commit` moves from `None` to `e13b4f1905de3cd9703d4b2242f278b104c06774`. Verified: `git show e13b4f1:<record>` is byte-identical to the file on disk, and `models.py` at that commit reads `sim-2026.08-v36`. **The v21 record FILE is not touched** — editing its header to stop saying "LIVE TREE" would be exactly the predecessor rewrite B11 exists to catch. |
| 4 | The v22 checksum record | `code_audit/run56_participant_package_v22_checksums.sha256`, **69 members**. v21 -> v22 **measured, not assumed**: **1 changed** (`assets/js/ingest.js`), **0 added, 0 deleted**. |
| 5 | **NO sequence exception, DECLARED not omitted** | `V21_TO_V22_SEQUENCE_EXCEPTION` and `V21_TO_V22_DELETED` are **empty tuples that are declared**. All five members of `SEQUENCE_BEARING_FILES_FROM_V21` (`decision.js`, `decision-ui.js`, `workspace.js`, `intake.json`, `debrief.json`) are present and byte-identical to v21, **measured**. |
| 6 | Production-tree re-take | `code_audit/run56_production_tree.sha256`, **242 files**, manifest sha256 `5c069a135882fa66411ba9185a50870e3eeb90a218b146c26beed22fac69bbbd`. The guard was observed reporting **exactly two CHANGED** and nothing added, removed or renamed **before** the manifest was written. |
| 7 | Authority-tree re-take | **RE-TAKEN AND DELIBERATELY NOT SUPERSEDED**, for the third run running. `compare()` over `AUTHORITY_ROOTS`: **added=0 removed=0 changed=0 renamed=0**, recomputed sha256 `b52c47a68a20ab1629681ea240abdea2167c67f289d181f446a8170704dc1596` is byte for byte the pinned file's. A manifest is superseded when what it describes moves, not once per run. |
| 8 | `run56_freeze_candidate_identity.json` | identity digest `a7db166ccd7551dd05dda5d50fec827c128cc050c95e47b8bf79cb65ed391d38`, candidate `db942f2ebe4ae27b598f76bd8307517e862f4a69` |
| 9 | The v22 `Package(...)` prose | covers phase A carried, phase A stopped, and phase B, one file at a time |
| + | `run56_successor_freeze_gate.csv` | 15 blockers, **0 blocked** |
| + | `run56_candidate_behaviour_digest.json` | `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1` |
| + | `RUN56_SUCCESSOR_FREEZE_{RECORD.json,REPORT.md,CHECKSUMS.csv}` | `FINAL_FREEZE_ACCEPTED`, **123 rows**, release content digest `fef55efdd634bf2e40db5f6abfd7146dfd527600b8ba7848dfe0dcf2c98cfaba` |

**The change set names every file that moved:**

```
assets/js/ingest.js                              phases A and B
server/app/simulation/models.py                  the stamp
server/tools/participant_packages.py             v22, the v21 pin, the two empty declarations
server/tools/production_tree.py                  PINNED -> run56, PINNED_RUN55 addressable
server/tools/build_run37_acceptance.py           the mint constants
server/tools/test_run37_freeze_gate.py           four stale pins revised
server/tools/drive_run55_admin_controls.py       two checks revised, not deleted
server/tools/drive_run56_duplicate_controls.py   NEW, the phase A + B driver
server/tools/build_run56_candidate_identity.py   NEW
server/tools/build_run56_successor_release.py    NEW
code_audit/run56_participant_package_v22_checksums.sha256   NEW
code_audit/run56_production_tree.sha256                     NEW
research/freeze/run56_freeze_candidate_identity.json        NEW
research/freeze/run56_successor_freeze_gate.csv             NEW
research/freeze/run56_candidate_behaviour_digest.json       NEW
research/freeze/RUN56_SUCCESSOR_FREEZE_RECORD.json          NEW
research/freeze/RUN56_SUCCESSOR_FREEZE_REPORT.md            NEW
research/freeze/RUN56_SUCCESSOR_FREEZE_CHECKSUMS.csv        NEW
```

**`assets/js/detail.js` is deliberately ABSENT: the second removal was stopped under 9.1.**

### 4.2 The candidate identity, group by group

```
registry_digest                       2 files  668d23c00a325cee   SAME
taxonomy_authority_digest             4 files  f5c03a7e3f6d59b3   SAME
qualification_authority_digest        5 files  76d61886845bc8ce   SAME
participant_protocol_digest           8 files  b5a05f98344f226a   SAME
controlled_stimuli_digest             2 files  56ac9665332fbb19   SAME
simulation_authority_digest          40 files  <moved>            MOVED (the stamp is in it)
test_suite_identity                 203 files  <re-derived>       SAME population, 203
browser_suite_identity                2 files  ad3aa92e703d0f07   SAME
final_lock_guard_digest               1 files  cfd6fb3bc25ef538   SAME
evidence_provenance_digest            2 files  b5c29e0a44c0c75e   SAME
service_roster_digest                 1 files  8fed04ffb3ed0338   SAME
candidate_identity_digest  91db6d4e60f8913099a37c56a946ef65c696b1663a25fb6ae407a99810d56efe
```

**Exactly ONE of the eleven groups moved, and only because the stamp lives in it.** Group
membership was diffed member by member: **added=[] removed=[]** on every group.

### 4.3 HOW MANY MINTS WERE PAID, AND WHAT SURFACED ON EACH

**SEVEN.** Run 51 paid four, Run 52 three, Run 55 four. This is the most any run has paid, and the reason is stated rather than hidden: **three of the seven exist only to chase two fixed points**, and a fourth was forced by the ten-suite reconciliation, which itself changed files the identity measures.

| Mint | What surfaced |
|---|---|
| **1** (dry run, `--out-audit`/`--out-freeze` to a scratch dir) | **Clean on the first pass, and the behaviour digest re-derived to `8fb4d366…`.** But the dry run wrote its gate CSV to the scratch dir, so `build_run56_successor_release.py` then died on a missing `research/freeze/run56_candidate_behaviour_digest.json`. Not a defect: the release builder reads the real tree by design. |
| **2** (real out-dirs, then the release builder) | **The release builder REFUSED to run**: *"a governed file named by the predecessor manifest is missing and is NOT declared as deleted: assets/js/deepdive.js"*. Reconciliation A below. Then the freeze-gate suite came back **33/34**, failing row 3 (`reproduces`, `0 fresh vs 15 committed`) because `SUCCESSOR_GATE` in the suite was still pinned at `run55_successor_freeze_gate.csv`. Chasing that pin uncovered **three more stale pins the run did not create** — reconciliation B. |
| **3** (after the phase-C commit `80f9cc9`) | **`B01` and `candidate_commit_verified_is_head` both did their job.** The second mint was taken on a dirty tree, so B01 (dirty candidate identity) was correctly BLOCKED and four further rows fell with it. Re-taken against `80f9cc9`: identity `8225d31c…`, release `2f733146…`, **gate clean**, digest `8fb4d366…` again. Gate suite then **33/34**, failing only row 34 (`no_self_reference`). |
| **4** (after the re-anchoring commit `3d507dc`) | Row 34's failure was **the second stale-pin finding**, below. Re-anchoring changed `test_run37_freeze_gate.py`, which is a **member of `test_suite_identity`**, so the identity had to be re-taken against the commit carrying it. Re-taken against `3d507dc`: identity `91db6d4e…`, release `76b4ba26…`, **gate clean**, digest `8fb4d366…` again. **`run56_successor_freeze_gate.csv` did not move on this pass.** Gate suite: **34/34.** |
| **5** (on an already-clean tree) | Row 3 was passing, but the committed gate CSV and a fresh regeneration were **not byte-identical**. One line differed: B01's **evidence** string records the porcelain line count at evaluation, and any mint taken during a regeneration necessarily records a non-zero count there, because the generator's own unwritten outputs are the dirt it counts. Regenerated once on an already-clean tree so the artefact itself was the only dirty file, then committed. Release digest re-taken: `642f13eb…`. **Verified after: a fresh regeneration is now IDENTICAL byte for byte.** |
| **6** (after the ten-suite reconciliation `db942f2`) | The full 203-suite pass came back **15247/15269 with ten suites red**, every one a guard this mint had falsified. Reconciling them changed ten `test_*.py` files, **all members of `test_suite_identity`**, so the identity had to be re-taken again. Identity `a7db166c…`, release `95481d02…`, **gate clean**, digest `8fb4d366…` again. |
| **7** (on an already-clean tree) | The B01-evidence fixed point **reopened by mint 6**, because that mint was necessarily taken while its own outputs were unwritten (`porcelain lines at evaluation: 6`). Regenerated once on a clean tree: `0`. Release digest `fef55efd…`. **Gate 34/34, and a fresh regeneration is byte-identical.** |

### 4.4 THE RECONCILIATIONS, EVERY ONE A NARROWING RATHER THAN A WEAKENING

| # | What was red | The reconciliation | Why it is not a weakening |
|---|---|---|---|
| **A** | `build_run56_successor_release.py` refused: the predecessor manifest names `assets/js/deepdive.js`, deleted by Run 54, and Run 56 declares no deletions | The RUN55 manifest already **carries that row forward** with an empty `sha256` and `moved_since_v32 = DELETED_BY_RUN54`. Such a row is an **already-recorded** deletion, not a new one. It is accepted **only** when the predecessor row itself recorded the deletion **AND** its sha256 is empty **AND** the file really is still absent. | Requiring a fresh declaration for every historical deletion forever would turn the declaration list into a list of history and **hide a genuinely new disappearance among them**. A file vanishing for the FIRST time still needs a declaration in `participant_packages`, still has to have existed at the pinned commit, and **still raises without one**; a predecessor row that carried real bytes and whose file has now vanished **still raises**. |
| **B** | Gate row 3 (`reproduces`) red: `0 fresh vs 15 committed` | `SUCCESSOR_GATE` advanced from `run55_` to `run56_`. **And then three more pins were found stale:** `SUCCESSOR_RECORD`, `SUCCESSOR_REPORT` and `SUCCESSOR_CHECKSUMS` were still `RUN51_…` — Run 55 advanced the gate name and left the other three behind. All four advanced to the release actually being minted. | **No check is deleted and none is weakened.** The same checks now run against the record that is actually being released, rather than against a release three mints old. This is strictly stricter. |
| **C** | Gate row 34 (`no_self_reference`) red once `SUCCESSOR_RECORD` was truthful | The row asserts the release names its IMMEDIATE predecessor's candidate as its parent. Its anchor was **RUN 48's** candidate `e3d1b698…`, set by Run 49 and never advanced. Re-anchored to Run 55's candidate `8e557b7b…`. | **The anchor is named EXPLICITLY and was NOT loosened to "any commit"** — loosening it would be the weakening the order forbids. The whole point of the row is that a record cannot silently reparent. |

| **D** | The full pass: ten suites red, 15247/15269 | Ten pinned guards advanced by exactly one entry each; `test_run28`'s v21 block converted from CURRENT to PREDECESSOR and measured at `e13b4f1`; a **new v22 block added**, 271 -> 292 checks. | **Nothing removed from any append-only list.** Every check still runs; where a predecessor is measured moved from disk to the commit its record describes, which is stricter, not looser. **Twenty-one checks were ADDED**, because converting v21's block would otherwise have left the chain's central guarantee with no subject. |

**THE TWO STALE PINS WERE AGREEING WITH EACH OTHER.** Row 34 kept passing through Runs 51, 52
and 55 only because `SUCCESSOR_RECORD` was *also* still `RUN51`, whose parent really is Run 48's
candidate. Two stale guards that reinforce one another read exactly like a passing check. This
run did not create either of them and states so.

---
### 4.5 EVERY GATE ROW, WITH ITS VERDICT, FROM LIVE OUTPUT

`server/tools/test_run37_freeze_gate.py`, re-run **on the final committed tree**, tree clean
before and after. **RESULT: 34/34 checks passed.**

| # | Gate row | Verdict |
|---|---|---|
| 1 | `run37.gate.generator_runs` — the acceptance generator runs to completion; a crash is a blocker, not a pass | **PASS** |
| 2 | `run37.gate.artifact_present` — the committed freeze gate exists | **PASS** |
| 3 | `run37.gate.reproduces` — and it REPRODUCES from the current tree, so it is not a stale snapshot | **PASS** |
| 4 | `run37.gate.fifteen_blocker_classes` — all fifteen blocker classes are evaluated | **PASS** |
| 5 | `run37.gate.B01` — dirty candidate identity is zero | **PASS** |
| 6 | `run37.gate.B02` — population mismatch is zero | **PASS** |
| 7 | `run37.gate.B03` — controlled-stimulus mismatch is zero | **PASS** |
| 8 | `run37.gate.B04` — participant-sequence drift is zero | **PASS** |
| 9 | `run37.gate.B05` — false defensibility statement is zero | **PASS** |
| 10 | `run37.gate.B06` — unexpected execution exception is zero | **PASS** |
| 11 | `run37.gate.B07` — Category-9 bypass is zero | **PASS** |
| 12 | `run37.gate.B08` — Category-10 authority violation is zero | **PASS** |
| 13 | `run37.gate.B09` — voting count is not exactly 2 is zero | **PASS** |
| 14 | `run37.gate.B10` — current taxonomy dual authority is zero | **PASS** |
| 15 | `run37.gate.B11` — package or predecessor mutation is zero | **PASS** |
| 16 | `run37.gate.B12` — browser qualification failure is zero | **PASS** |
| 17 | `run37.gate.B13` — unresolved blocking Run-36 defect is zero | **PASS** |
| 18 | `run37.gate.B14` — unsupported final empirical-validation claim is zero | **PASS** |
| 19 | `run37.gate.B15` — candidate behaviour changed during the run is zero | **PASS** |
| 20 | `run37.gate.blocking_defects_zero` — BLOCKING DEFECTS = 0 | **PASS** |
| 21 | `run37.gate.predecessor_release_preserved` (v25) | **PASS** |
| 22 | `run37.gate.immediate_predecessor_release_preserved` (v26) | **PASS** |
| 23 | `run37.gate.immediate_predecessor_release_preserved` (v27) | **PASS** |
| 24 | `run37.gate.immediate_predecessor_release_preserved` (v28) | **PASS** |
| 25 | `run37.gate.immediate_predecessor_release_preserved` (v30) | **PASS** |
| 26 | `run37.gate.immediate_predecessor_release_preserved` (v31) | **PASS** |
| 27 | `run37.gate.no_release_while_blocked` | **PASS** |
| 28 | `run37.gate.release_present_when_clean` | **PASS** |
| 29 | `run37.gate.limitation_stated` — empirical field validation is stated as 0 of 100 | **PASS** |
| 30 | `run37.gate.limitation_stated` — no validated real-world predictive claim | **PASS** |
| 31 | `run37.gate.limitation_stated` — OG-SYNTH-0.1 historical incompleteness | **PASS** |
| 32 | `run37.gate.limitation_stated` — bounded controlled-study instrument use | **PASS** |
| 33 | `run37.gate.disposition` — FINAL_FREEZE_ACCEPTED and the gate agrees | **PASS** |
| 34 | `run37.gate.no_self_reference` — no self-referential placeholder, and the parent is the immediate predecessor | **PASS** |

**Every row above has command output behind it. No row is reported green without one.**
Rows **28, 33 and 34** are the three that had been asserting a release three mints old; they are
now asserting `RUN56_SUCCESSOR_FREEZE_RECORD.json`.

**And the fifteen blocker classes themselves, from the regenerated CSV:**

```
B01   PASS  count=0   dirty candidate identity
B02   PASS  count=0   population mismatch
B03   PASS  count=0   controlled-stimulus mismatch
B04   PASS  count=0   participant-sequence drift
B05   PASS  count=0   false defensibility statement
B06   PASS  count=0   unexpected execution exception
B07   PASS  count=0   Category-9 bypass
B08   PASS  count=0   Category-10 authority violation
B09   PASS  count=0   voting count is not exactly 2
B10   PASS  count=0   current taxonomy dual authority
B11   PASS  count=0   package or predecessor mutation
B12   PASS  count=0   browser qualification failure
B13   PASS  count=0   unresolved blocking Run-36 defect
B14   PASS  count=0   unsupported final empirical-validation claim
B15   PASS  count=0   candidate behaviour changed during the run
FREEZE GATE: 15 blockers evaluated, 0 BLOCKED -> gate clean
```

### 4.6 THE BEHAVIOUR DIGEST, RE-DERIVED SEVEN TIMES

```
{
  "targets": 100,
  "simulation_version": "sim-2026.08-v37",
  "participant_package": "og-participant-2026.08-v22",
  "behaviour_digest": "8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1",
  "candidate_git_commit": "db942f2ebe4ae27b598f76bd8307517e862f4a69"
}
```

**Derived, never copied forward.** Identical on all seven passes and identical to the digest of
record inherited from Run 55, **unmoved across the v36-to-v37 supersession**. Section 10.1 did
not fire.

---
### 4.7 THE FULL SUITE, AND THE TEN IT FOUND

**FIRST PASS, on the mint before reconciliation:**
```
Suites run: 203   Total checks: 15247/15269
FAILED SUITES: 10
```
**All ten were guards this run's own mint falsified** by advancing the stamp to
`sim-2026.08-v37` and the package to `og-participant-2026.08-v22`. Not one was red for any other
reason, which is what section 10.5 requires before a mint may proceed.

| Suite | Was | What it pinned |
|---|---|---|
| `test_run25_rail_removal.py` | 55/56 | the pinned production-manifest chain, which had to gain `run56_production_tree.sha256` |
| `test_run28_participant_packages.py` | 265/271 | six checks: v21 was still asserted CURRENT |
| `test_run31_version_boundaries.py` | 55/56 | the authorised-append stamp list |
| `test_run32_closure_version_boundary.py` | 25/26 | the same list |
| `test_run36_fault_guards.py` | 40/41 | the sequence-exception ledger's last entry must BE the current record |
| `test_run36_instrument_qualification.py` | 75/76 | current package v21 |
| `test_run38_frozen_immutability.py` | 15/17 | live stamp v36, package v21 |
| `test_run39_frozen_immutability.py` | 17/19 | live stamp v36, package v21 |
| `test_run39_launch_gate.py` | 97/100 | identity pins v36 / v21 |
| `test_run41_preservation.py` | 29/33 | live stamp v36, superseded v35, package v21, and the history ladder |

**A REAL TRAP INSIDE `test_run41_preservation.py`, CAUGHT AND FIXED PROPERLY.** Its history check
tests the tail **position by position** — `[-1]`, `[-2]`, `[-3]` … Appending v37 shifts every
index below it. Inserting a row without shifting the rest left **two clauses asserting the same
index**, which would have **silently dropped one stamp from the check while still passing**. The
whole ladder was shifted by one instead: `[-1]=v37` through `[-8]=v30`.

**NO CHECK WAS DELETED, AND TWENTY-ONE WERE ADDED.** Converting `test_run28`'s v21 block from
"current" to "predecessor" would have left the chain's central guarantee — *the CURRENT record's
checksums hold against the LIVE TREE* — with **no subject at all**. A full v22 block was added.
That suite went **271 -> 292**.

**CONFIRMING SECOND PASS, on the final committed tree:**
```
Suites run: 203   Total checks: 15290/15290
ALL SUITES GREEN
```

**203 suites. 15290 of 15290 checks. ZERO RED. No suite left production or client source dirty**
— the only dirt after the pass was the 26 audit artifacts, restored and uncommitted.

The check total rose from Run 55's **15269** to **15290**: **+21**, exactly the v22 block added
to `test_run28_participant_packages.py`. **The suite population is unchanged at 203.**

`tests/test_run33_ph1_fault_campaign.py` scored **46/46** in both passes, which does not resolve
carry-forward item 11. `isolation_forest.py` was not flagged dirty in either pass, which does not
resolve carry-forward item 10.

---
## 5. Every item STOPPED under section 9, with its reason

| # | Item | Condition | Reason |
|---|---|---|---|
| **1** | **Removing `.detail-reset` ("Clear stored signals for this project")** | **9.1 and 9.3** | **THE MAIN FINDING OF THIS RUN.** The order rules that `.pe-reset` "clears more" and so survives. Measured byte for byte at the explicit commit `e13b4f1`, **neither control is a superset of the other**. Removing `.detail-reset` would lose **`LinResults.clear()`** (the derived-results cache drop, whose absence once had a cleared project still drawing 41 modules with a current result and an Amber rollup in the same session), the **`LIN_PROJECTS` re-fetch** through `LinStore.getProject`, the **forcing of the in-memory record to a true awaiting-ingest state** (nine field assignments including `p.history = []` and the document arrays), and **`render(id)`**, the re-render that makes the page actually show the cleared state. Removing `.pe-reset` instead would lose `LinStore.load()`, the append-only `logEvent()` entry and `renderPortfolioAdmin()`. **There is no safe direction, so BOTH were left in place** and the duplication is on the record rather than resolved by guess. |
| **2** | **Giving `.detail-reset` a confirmation** | not ordered | Section 7 names **Archive** and **Reset signals**, which are `.pe-archive` and `.pe-reset`. `.detail-reset` is a third control the order does not mention. Adding a confirmation to it would have been unordered work on a control outside the run's scope. Raised in section 10 as a decision. |
| **3** | **Using `window.confirm` for the two confirmations** | 9.2 in spirit, 10.9 in fact | Four files in this repository already record that `window.confirm` returns false in this container. Gating Archive on it would have made Archive **impossible to perform**, which changes what the confirmed action does. The application's other confirmation pattern was reused instead. Reported rather than discovered late. |
| **4** | **Editing the v21 checksum record's header** | 10.4 / B11 | The header still says it describes the LIVE TREE, which stopped being true the moment v22 existed. **It was left exactly as it is** and the supersession is recorded by pinning `source_commit` in `participant_packages.py`. Rewriting a predecessor record to agree with the present is the precise failure B11 exists to catch. |
| **5** | **Writing a `run56_authority_tree.sha256`** | premise contradicted by execution | The authority tree did not move: added=0 removed=0 changed=0 renamed=0, manifest sha256 identical to the pinned file's. Writing a successor manifest would assert a supersession that did not happen. Re-taken and reported, not superseded. Run 55 stopped on the same class for the same reason. |
| **6** | **Rewriting the historical `run51`/`run52`/`run55` freeze artefacts** | 10.4 | Each is the evidence for what was measured under its own stamp. They are named as parents, not edited. |

**No item was stopped because it was hard. Every one of the six is a stop the code or the order
required.**

---

## 6. Every item UNSTARTED FOR BUDGET, named as unstarted and not as stopped

| # | Item | Why it is unstarted rather than stopped |
|---|---|---|
| 1 | **A naming sweep over rendered text** | Not ordered by this run and not attempted. No identifier was stripped or restored, so section 10.7 is satisfied without one. |
| 2 | **The `CANDIDATE` fixed-point repair** (carry-forward 14) | Explicitly **not ordered fixed** by section 8's note. Paid twice this run, by hand, and left as it is. |
| 3 | **Any work on the fifteen carry-forward items** | The order carries them forward *unacted*. None was touched. |
| 4 | **Extending the confirmation pattern to any other destructive control** (for example `.detail-reset`, or the portfolio-row paths) | Beyond the two the order names. Not begun. |
| 5 | **Re-running the 23 armed fault campaigns individually outside the suite pass** | The full 203-suite pass runs them; a second standalone sweep was not begun. |

**Nothing in this list was attempted and abandoned. Each is work that was never begun.**

---

## 7. Every guarantee at section 11, verified or not met, each with its injection

The injection protocol was the ordered one throughout: **the tree was checked before and after,
the snapshot was taken from a COMMITTED REFERENCE and never from disk, the restore was inside a
`finally`, and the baseline was rechecked after every injection.** Every proof of absence is
pinned to the explicit hash `e13b4f1` or `527cf08`, **never** to a relative reference.

| # | Guarantee | Status | Evidence and injection |
|---|---|---|---|
| 1 | The detail page carries exactly one control that opens the upload dialog, and exactly one that clears stored signals, verified in a browser | **PARTLY MET, AND THE UNMET HALF IS THE 9.1 STOP** | Upload: **MET** — `EXACTLY ONE control opens the upload dialog`, on each of three projects. Signals: **NOT MET, DELIBERATELY** — the page carries **two**, because the removal was stopped under 9.1. Asserted as `inv["reset"] == 2`, so the guard is exact and would go red if either vanished. |
| 2 | Both removed controls existed at `e13b4f1`, pinned explicitly, so the absence checks are not vacuous | **MET** | Four non-vacuity checks at `e13b4f1`: `.pe-populate`, `.detail-upload`, `.detail-reset`, `.pe-reset` all PRESENT. |
| 3 | The surviving control of each pair does everything the removed one did, proved by handler comparison against `e13b4f1` | **MET for pair 1; DISPROVED for pair 2, which is why pair 2 stopped** | Pair 1: `.pe-populate`'s entire body enumerated as `['openUploadModal(id);']`. Pair 2: the eleven-behaviour table in section 2.3, `only_detail` and `only_pe` both non-empty. |
| 4 | `.pe-populate` still renders and works wherever else `openInlineManage` is used, or the report states there is no other call site | **MET** | Section 2.1. Two reachable call sites; the builder still emits the button when `hostEl` is absent; the internal re-open forwards `hostEl` so it rebuilds the same panel the reader had. |
| 5 | No dead CSS rule survives the removals, with a non-vacuity proof | **MET, AND REPORTED AS VACUOUS** | `.pe-populate` rules in `radar.css` at `e13b4f1`: **0**; now: **0**. There was none to remove. Reported as a vacuous absence check rather than dressed up as a guarantee. |
| 6 | The other four moved controls still render on the detail page and act on that project | **MET** | Save info / Recompute this project / Reset signals / Archive / Close each render exactly once, on three projects; `data-admin-for` and `.pe-id` both read back the viewed id. |
| 7 | Archive asks before archiving, and Reset signals asks before clearing, verified in a browser | **MET** | `ASKS BEFORE ACTING -- a confirmation dialog opens and the action has not run`, both controls. |
| 8 | Each confirmation names the project it will act on | **MET** | Named in title, detail and button; and asserted equal to the identifier rendered in the detail heading. |
| 9 | Cancelling makes no call and changes no state, proved by execution | **MET** | Counting spies on five `LinStore` methods and a navigation spy on `LinApp.showPage`. After Escape: `store calls=[] navigation=[] modals=0 page=['detail']`, `location.href` unchanged, panel intact. |
| 10 | Confirming does exactly what the control did before, proved against `e13b4f1` | **MET** | Action bodies BYTE-IDENTICAL to `e13b4f1` once the gate is stripped; and by execution `resetSignals(PRJ-R54-B)` and `archiveProject(PRJ-R54-C)`, with PRJ-R54-C really leaving the active portfolio. |
| 11 | No control was added | **MET** | **Injection**: `527cf08`'s `ingest.js` written from the committed reference, a **second browser** launched, the twenty-entry button list read, restored inside a `finally`, tree byte-identical before and after. The lists are **IDENTICAL**. |
| 12 | No em dash or en dash renders in user-facing text | **MET** | Confirmation text of both controls, and the whole `#detail-root` `innerText`: no em dash, no en dash. Ampersand rule also holds. |
| 13 | The behaviour digest is **re-derived**, not assumed | **MET** | Derived **seven times**; `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1` every time. |
| 14 | No stored figure changes | **MET** | No compute path, model, parameter, band, threshold, calibration, abstention rule, migration or corpus touched. **B15 count 0.** |
| 15 | Modules in service is 63, registry total 101, both derived | **MET** | `service_index()` / `registry_index()` at driver start: `in service: 63  registry: 101  retired: 38`. |
| 16 | Voting count is exactly 2, `A1.7` and `A1.8` | **MET** | **B09 count 0** ("voting count is not exactly 2"), derived by the generator. |
| 17 | Every runtime lookup across all 101 registered modules resolves, asserted live | **MET** | **B10 count 0**, and `B06` (unexpected execution exception) count 0 across the generator's full execution census of 109 rows. |
| 18 | No rendered identifier changed | **MET** | No naming sweep run; nothing stripped or restored. The only rendered text this run adds is the two confirmations, and the identifiers in them are read from the page. |
| 19 | Every sequence-bearing file that moved has its own named exception record; one moving without a record still turns the gate red | **MET, AND THE ANTECEDENT IS EMPTY — STATED AS EMPTY** | **No sequence-bearing file moved.** All five members of `SEQUENCE_BEARING_FILES_FROM_V21` are present and byte-identical to v21, measured. `V21_TO_V22_SEQUENCE_EXCEPTION` is an **empty tuple that is DECLARED**, not omitted, so a later reader sees a declaration rather than a silence. The machinery that turns the gate red on an undeclared move is `B04`, which is **inherited unchanged from Run 55 and was not touched**; **this run did not re-prove it by injection**, and says so rather than claiming a proof it did not take. |
| 20 | The successor freeze gate passes in full | **MET** | **34/34**, every row listed in section 4.5 from live output. |

**The one guarantee not re-proved by injection is 19's red-on-undeclared-move half**, because
nothing sequence-bearing moved and the guard was inherited untouched. That is stated as not
re-proved rather than reported as verified.

---
## 8. Which audit artifacts the suites rewrote, and were restored

**TWENTY-SIX. The same 26 as Runs 52, 54 and 55.** `git status --porcelain` was taken
**before** the campaign pass (empty) and **after** it, and every one was restored with an
explicit `git checkout --` naming each path. **None was committed.**

```
code_audit/run10_dsm_known_answers.csv
code_audit/run10_dsm_recomputation.csv
code_audit/run10_module_identity.csv
code_audit/run10_monte_carlo_convergence.csv
code_audit/run10_monte_carlo_distribution_gap.csv
code_audit/run10_monte_carlo_known_answers.csv
code_audit/run10_monte_carlo_recomputation.csv
code_audit/run10_no_operational_effect.csv
code_audit/run10_validator_fault_injection.csv
code_audit/run20_cycle12_100_reaudit.csv
code_audit/run20_cycle12_guard_nonvacuity.csv
code_audit/run20_cycle12_lineage_campaign.csv
code_audit/run21_guard_nonvacuity_results.csv
code_audit/run30_cat7_operational_execution.csv
code_audit/run38_controlled_stimulus_execution_order.csv
code_audit/run38_lock_integrity.csv
code_audit/run38_participant_state_machine.csv
code_audit/run39_launch_identity.csv
code_audit/run8_expectation_mutation_proof.csv
code_audit/run9_abstention_results.csv
code_audit/run9_alias_overlay_verification.csv
code_audit/run9_fixture_import_results.csv
code_audit/run9_known_answer_results.csv
code_audit/run9_no_operational_effect.csv
code_audit/run9_validator_gap_recomputations.csv
server/tools/run17/coverage.csv
```

`build_run37_acceptance.py` was run with **`--out-audit <scratch dir>`** for the digest
re-derivations, so the three `code_audit/run37_*.csv` acceptance artifacts were written to the
scratchpad and the repository copies were never touched by those passes. `git status
--porcelain` was **empty before and after** every one of them.

`code_audit/run39_launch_identity.csv` was rewritten a second time by the individual re-run of
`test_run39_launch_gate.py` during reconciliation, and was restored the same way.

---
## 9. Incidental findings, unacted

| # | Finding | Evidence | Why unacted (or acted, where the run authored the file) |
|---|---|---|---|
| 1 | **The Run 55 release report shipped with Run 52's prose.** `research/freeze/RUN55_SUCCESSOR_FREEZE_REPORT.md` begins `# Run-52 successor freeze report` and `**Disposition: FINAL_FREEZE_ACCEPTED** for sim-2026.08-v35`. The builder's Markdown body had never been advanced past Run 52, so the shipped report describes the wrong run and the wrong stamp. | `head -3 research/freeze/RUN55_SUCCESSOR_FREEZE_REPORT.md` | **The Run 55 artefact is NOT rewritten** — it is that release's evidence. The Run 56 builder writes a truthful report for its own release, and the record's stale key `behavioural_delta_v34_to_v35` becomes `behavioural_delta_v36_to_v37` with content that describes what this run changed. |
| 2 | **`SUCCESSOR_RECORD`, `SUCCESSOR_REPORT` and `SUCCESSOR_CHECKSUMS` in the freeze-gate suite had been stale since Run 51**, and the `no_self_reference` anchor stale since Run 49. Gate rows 28, 33 and 34 were asserting a release three mints old. They kept passing because the two stale pins agreed with each other. | Section 4.4 reconciliations B and C | **Acted**, because leaving them would have meant minting v37 behind guards that were not looking at v37. Revised, never deleted, never loosened. |
| 3 | **B01's evidence string can never read 0 on a mint taken during regeneration**, because the generator's own unwritten outputs are the dirt it counts. The count is unaffected; only the evidence text is. | Section 4.3, mint 5 | **Acted** for this run by taking one regeneration on an already-clean tree. The general shape — an artefact that records the tree state it is itself dirtying — is the same fixed point as carry-forward 14 and is **not** fixed generally. |
| 4 | **`assets/js/ingest.js` is not a member of the release's governed manifest** (`governed files moved since v32` lists only `models.py` and `drive_run55_admin_controls.py`). The client file is covered by the participant-package checksum record instead. | `build_run56_successor_release.py` output | Unacted. Widening a governed manifest is not ordered here and would change what the freeze measures at the same time as changing the instrument. |
| 5 | **`.detail-reset` remains without a confirmation** while the moved `.pe-reset` beside it now has one. Two controls on the same page that clear stored signals now behave differently at the point of asking. | Sections 2.3 and 3.6 | Unacted: outside the two names section 7 gives. Raised as a decision in section 10. |
| 6 | **`drive_run55_admin_controls.py` section 3 had never driven `.detail-upload` in a browser.** It drove the duplicate `.pe-populate` instead. | The revision made in phase A | Acted as part of the required revision. The surviving control is now the one exercised. |
| 7 | **`test_run33_ph1_fault_campaign.py` scored 46/46 in this run's pass**, the figure carry-forward 11 says it only ever produces standing alone. | The suite pass | Unacted and **does not resolve** carry-forward 11. Recorded, not explained. |

---

## 10. What the next session needs, stated as a decision for the owner

1. **THE DETAIL PAGE STILL HAS TWO CONTROLS THAT CLEAR STORED SIGNALS, AND THAT IS THIS RUN'S
   ONE UNFINISHED THING.** `.detail-reset` ("Clear stored signals for this project") and the
   moved `.pe-reset` ("Reset signals"). The order said remove the first; **the code says that
   would lose four behaviours the survivor does not have** — `LinResults.clear()`, the
   `LIN_PROJECTS` re-fetch, the forced awaiting-ingest state, and `render(id)`. Removing the
   other loses `LinStore.load()`, `logEvent()` and `renderPortfolioAdmin()`.
   **Decision: (a) leave both, as now; (b) MERGE them — give the survivor the union of the two
   handler bodies, which is the only removal that loses nothing, and then remove the other; or
   (c) relabel one so a reader can tell them apart?** Option (b) is real work on a handler and
   was not ordered, so it was not done.
2. **`.detail-reset` ASKS NOTHING BEFORE CLEARING**, while `.pe-reset` beside it now does.
   **Decision: extend the same confirmation to it?** It is a third control the Run 56 order does
   not name, so it was left alone.
3. **THE FREEZE GATE'S RELEASE PINS NEED AN OWNER.** Three of them sat stale for five runs and
   passed the whole time because they agreed with each other. **Decision: derive
   `SUCCESSOR_RECORD` / `SUCCESSOR_REPORT` / `SUCCESSOR_CHECKSUMS` and the no-self-reference
   anchor from `participant_packages.CURRENT` and the package chain, instead of hand-editing four
   string constants each mint?** That is the same class of problem as carry-forward 14 and is now
   two problems, not one. Not ordered here.
4. **THE `CANDIDATE` FIXED POINT WAS PAID TWICE THIS RUN**, and mint 5 shows it has a sibling in
   B01's evidence string. **Decision: fix the fixed point, or keep paying it?** Section 8 of this
   order explicitly declined to fix it.
5. **`main` HAS BEEN MERGED AND PUSHED.** See the merge section.

---

## Carry-forward items, unacted

1. **CPI 1.22 on the site render.** Needs read access to PRJ-001's stored rows, which no session
   may have. The open question is which document type wrote `pv`.
2. **The `historical_data` triple**, Run 47's only unimplemented relation.
3. **`signal_inputs.sources` records no source field name.**
4. **Four status comparisons remain case-sensitive**, two in `decision.js`.
5. **Two Run 45 census artifacts do not match the v30 release manifest.**
6. **`test_run47_evm_consistency.py` swallows its own traceback.**
7. **Run 47's handoff entry is at the bottom of `T6_HANDOFF.md`.** Left there.
8. **`REG.method_label(m)` returns `None` for 96 of 101 registered modules.**
9. **`new_id` and `old_id` stay.** Not a naming survivor.
10. **`isolation_forest.py`** was flagged dirty four times in Run 54 and not at all in Run 55's
    two passes. **Not determinable.** On watch; it did not reproduce in this run's pass either,
    which does not resolve it.
11. **`test_run33_ph1_fault_campaign.py`** scored 36/46 in Run 54's runner and 46/46 in Run 55's.
    Order- or dirt-dependent, unresolved. It scored **46/46** in this run's pass, which again
    does not resolve it.
12. **`test_run2_fifteen_defects.py`** produces two different check totals depending on the
    database it is handed. Reported, not explained.
13. **The `snapshot_from HEAD` conversion** is unstarted for most campaigns. All 39 are armed, so
    a leak is caught at the start of the next campaign.
14. **`build_run37_acceptance.py`'s `CANDIDATE` constant** must be hand-edited after each commit
    it describes. A fixed-point problem since Run 41. **Paid twice this run.**
15. **The suite population is 203.** Stated so it is not re-derived as a discrepancy.

---
## THE MERGE AND THE PUSH

### No section-10 run-level condition fired

| # | Condition | Status |
|---|---|---|
| 1 | The behaviour digest moves from `8fb4d366…` | **DID NOT FIRE.** Re-derived **seven** times; identical every time. |
| 2 | Any stored figure changes | **DID NOT FIRE.** No compute path, model, parameter, band, threshold, calibration, abstention rule, migration or corpus touched. **B15 count 0.** |
| 3 | A runtime lookup fails for any of the 101 registered modules | **DID NOT FIRE.** B10 and B06 both count 0; `in service: 63  registry: 101`. |
| 4 | A check must be deleted | **DID NOT FIRE.** Sixteen guards revised across the run; **none deleted**; **twenty-one added**. Where a check's subject changed it was RE-POINTED, never dropped. |
| 5 | A gate row fails for a reason other than a manifest this run's edits falsified | **DID NOT FIRE.** Every red was a manifest this run's own edits falsified — **except the two stale pins, which were falsified by EARLIER runs and are reported as such rather than claimed as this run's.** All reconciled. |
| 6 | A reachable control other than the two phase A names would be added, moved or removed | **DID NOT FIRE.** Exactly one control was removed, `.pe-populate`, one of the two the order names. The other, `.detail-reset`, was **STOPPED under 9.1 and left in place**. Phase B added none, measured live against `527cf08`. |
| 7 | A rendered identifier would change | **DID NOT FIRE.** No naming sweep run; nothing stripped or restored. The identifiers in the two confirmations are **read from the page** and were asserted equal to the detail heading. |
| 8 | Any project's detail page becomes unreachable | **DID NOT FIRE.** The detail page was opened on three projects in both drivers; `'detail' in visible pages` on every one. |
| 9 | A confirmation would change what the confirmed action does | **DID NOT FIRE.** Both action bodies BYTE-IDENTICAL to `e13b4f1` once the gate is stripped, **and** `window.confirm` was refused precisely because it WOULD have fired this condition. |

### The merge

The gate is **known and clean**: **34/34** on the final committed tree, **203 suites,
15290/15290, ALL SUITES GREEN**, tree clean before and after every campaign. The merge condition
of section 8.6 is met, so the branch is merged to `main` with `--no-ff` **and pushed**, which is
ordered this run.

---
### The merge and the push, recorded exactly

```
branch          run56-duplicate-controls, rooted at e13b4f1
main before     e13b4f1905de3cd9703d4b2242f278b104c06774
merge           git merge --no-ff run56-duplicate-controls
main after      dbb4bf9
push            git push origin main
                To https://github.com/mrnyanlintun/LinPRojectRadar
                   e13b4f1..dbb4bf9  main -> main
main == origin/main == dbb4bf9
freeze gate ON MERGED main   34/34
git status --porcelain       EMPTY, before and after
```

**The push is done. Run 55 left its merge local until asked; this run was ordered to push and
did.** No force-push was used and none would have been.

### The eleven commits on the branch, in order

```
527cf08  phase A: remove the duplicate "Upload documents"; STOP the reset removal under 9.1
282e70d  phase B: Archive and Reset signals ask before acting, reusing the app's own pattern
80f9cc9  PHASE C: the mint. sim-2026.08-v37, og-participant-2026.08-v22
631be12  PHASE C: THE THIRD MINT, taken against the committed tree
3d507dc  PHASE C: re-anchor the freeze gate's no-self-reference parent, which had stopped advancing
b68cc08  PHASE C: THE FOURTH MINT, after the re-anchoring commit
06d49b0  PHASE C: THE FIFTH MINT, so the committed gate reproduces BYTE FOR BYTE
db942f2  PHASE C: the TEN suites the full 203-suite pass found, reconciled to true bytes
09bf7f1  PHASE C: THE SIXTH MINT, after the ten-suite reconciliation
         (folded with the seventh, taken on a clean tree)
fa3ad7e  the report, and the handoff updated at the top
dbb4bf9  Merge Run 56  (--no-ff, on main, pushed)
```

**Each phase was committed before the next began, as section 1 requires.**
