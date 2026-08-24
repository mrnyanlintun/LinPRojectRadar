# Run 57: the reset merge, the derived pins, and the two fixed points

**Repository:** the Linux clone at `/home/user/LinPRojectRadar`. The Windows path was not
reachable, as Runs 55 and 56 also recorded.
**Interpreter:** `python3` 3.11.15. There is no `.venv`, so the documented fallback is what ran,
and `server/run_all_suites.sh` takes the same fallback itself (`[ -x "$VENV_PY" ] || VENV_PY="$(command -v python3)"`).
**Branch:** `run57-reset-merge-and-pins`, rooted at `50dfb40`.
**Stamp:** `sim-2026.08-v38`. **Package:** `og-participant-2026.08-v23`.

## THE HEADLINE

1. **The two reset controls are one control.** `.detail-reset` is gone; `.pe-reset` survives
   carrying the UNION of both handler bodies and Run 56's confirmation. Measured in real
   Chromium on three projects, 65/65: two controls that clear stored signals before, exactly one
   after, one button lost and none added or moved.
2. **The four release pins and the `no_self_reference` anchor are DERIVED.** The Run-55 state --
   one pin advanced and three left behind -- is no longer expressible, because there is no second
   place to leave behind. Nothing is loosened: the anchor still resolves to one specific named
   commit at evaluation time.
3. **`CANDIDATE` stays the owner's constant and stops being guesswork.** The mint computes what it
   should read, prints both values, and refuses to proceed (exit 3) when they disagree.
4. **B01's evidence is reproducible without changing what B01 measures** -- section 9.3 item 1,
   not item 2.
5. **THREE MINTS WERE PAID.** Run 51 paid four, Run 52 three, Run 55 four, Run 56 seven. **Phase B
   reduced it, and the reduction is attributable mint by mint** -- see section 4.3. The two
   extra mints were NOT fixed points; both were forced by the reconciliation cascade, and that
   is said plainly rather than folded into the number.

## 1. The tree at the start, and ONE PREMISE OF THE ORDER CORRECTED

`git status --porcelain` was **EMPTY**.

```
git rev-parse HEAD main origin/main
50dfb40fd83850a5342ab9106c063cbe87f367e9
50dfb40fd83850a5342ab9106c063cbe87f367e9
50dfb40fd83850a5342ab9106c063cbe87f367e9
```

**The order's section 3 says `main == origin/main == dbb4bf9`. IT IS `50dfb40`.** `dbb4bf9` is
Run 56's `--no-ff` merge commit; `50dfb40` is the record commit Run 56 made on top of it after
pushing, and it is the tip. Everything else in section 3 verified: stamp `sim-2026.08-v37`
(`server/app/simulation/models.py:704`), package `og-participant-2026.08-v22`
(`participant_packages.CURRENT`), 203 suites (193 in `server/tools/`, 10 in `server/tests/`),
freeze gate **34/34** re-run live, and the behaviour digest **RE-DERIVED**, not assumed, at
`8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1`.

The branch is rooted at `50dfb40`, the real tip.

## 2. PHASE A: the two reset controls merged into one

Driver: `server/tools/drive_run57_reset_merge.py`, **65 passed, 0 failed**. Browser session cwd
`/tmp/.../scratchpad/r57drive` (a clean subdirectory, printed first), Chromium at
`/opt/pw-browsers/chromium-1194/chrome-linux/chrome` by explicit `executable_path`,
`--use-gl=swiftshader --no-sandbox --headless=new`, `python3 -u`.

**The `DEng\Demo` tell, measured and reported:** `7 .page sections`, and the
`document.scripts` filter for `api.js`/`boot.js` returned `[]`. The application under test is the
right one.

### 2.1 Both handlers RE-MEASURED at the explicit commit `50dfb40`

Run 56's table was **not** taken as given. Both bodies were extracted from `50dfb40` by brace
balance and enumerated again:

```
behaviour                        .detail-reset   .pe-reset
LinStore.resetSignals(                    True        True
LinSignals.clearCache(                    True        True
LinResults.clear(                         True       False
LinStore.load(                           False        True
logEvent(                                False        True
LinApp.refresh(                           True        True
renderPortfolioAdmin(                    False        True
render(id)                                True       False
LIN_PROJECTS                              True       False
LinStore.getProject(                      True       False
p.history = []                            True       False
LinStore.getCached(                       True       False
btn.disabled = true                       True        True

ONLY .detail-reset does: ['LinResults.clear(', 'render(id)', 'LIN_PROJECTS',
                          'LinStore.getProject(', 'p.history = []', 'LinStore.getCached(']
ONLY .pe-reset does    : ['LinStore.load(', 'logEvent(', 'renderPortfolioAdmin(']
BOTH do                : ['LinStore.resetSignals(', 'LinSignals.clearCache(',
                          'LinApp.refresh(', 'btn.disabled = true']
```

**THE DIFFERENCE FROM RUN 56, REPORTED RATHER THAN ABSORBED.** Run 56 measured eleven
behaviours and this run measures twelve. On the eleven Run 56 measured, **its table is
reproduced exactly**. The twelfth probe, `LinStore.getCached(`, is a **sixth** `.detail-reset`-only
behaviour that Run 56's probe list did not carry. **The difference is in the probe, not in the
code**, and this run acts on its own measurement: `LinStore.getCached(` is in the union and is in
the merged handler.

**The verdict is unchanged: NEITHER handler is a superset of the other**, so removing either
alone loses behaviour, and the merge is the only removal that loses none. Both also carry an
`aria-live` region -- the Run 56 dispatch hypothesis that only `.detail-reset` does remains FALSE
and is recorded so.

### 2.2 Which selector survives, and why

**`.pe-reset` survives.** Stated rather than picked silently:

- Every behaviour unique to `.detail-reset` is reachable from `ingest.js` through interfaces that
  are **already public**: `window.LinResults`, `window.LIN_PROJECTS`, `LinStore.getProject` /
  `getCached`, and `detail.js`'s own exported `LinDetail.render` (`detail.js:2772`,
  `window.LinDetail = { render, teardown, __resetMapForTest }`).
- Two behaviours unique to `.pe-reset` -- `logEvent` (`ingest.js:36`) and `confirmDestructive`
  (`ingest.js:253`) -- are **module-private** to `ingest.js`. `window.LinIngest` (`ingest.js:790`)
  exports neither. Building the same union inside `detail.js` would have required **newly
  exporting both**.
- Merging into `.pe-reset` therefore adds **nothing** to any module's public surface, and it
  leaves Run 56's confirmation exactly where Run 56 put it. The gate body is asserted
  byte-identical to `50dfb40` once whitespace is normalised.

### 2.3 The merged handler's order, and the reasoning for it

By dependency, not by concatenation:

1. **Confirmation first** -- nothing happens until confirmed.
2. `await LinStore.resetSignals(id)` -- **the server is reset first**; everything after it
   reconciles clients to that truth.
3. **Caches dropped before any re-fetch or re-render**, or the re-render repopulates from the
   stale copies: `LinSignals.clearCache(id)` then `LinResults.clear()`. `LinResults.clear()` is
   the line whose absence left a cleared project drawing **41 modules with a current result and
   an Amber rollup in the same session**, from a row the server had already retired.
4. `await LinStore.load()` **before** `await LinStore.getProject(id)` -- the store-wide reload
   rebuilds the list first, then the single authoritative record is spliced into `LIN_PROJECTS`.
   The other order lets `load()` overwrite the record just fetched.
5. The **awaiting-ingest mutation after the re-fetch** (`p.signals = null`, `p.history = []`, the
   document arrays, the status fields), or the fetch would restore the very fields it nulls.
   `p.events` is deliberately not blanked: Run 22 proved that mask made the live page less
   truthful than the reloaded one.
6. `logEvent(...)` **once**, after the state change succeeded and before the re-renders, so the
   activity log renders with the entry already in it.
7. Re-render **broadest to narrowest**: `LinApp.refresh()`, `renderPortfolioAdmin()`, and
   `LinDetail.render(id)` **last**, because it rebuilds the host that contains this very button.
8. `catch`: the union of both failure paths -- re-enable the control and report the failure in
   the `aria-live` region. The survivor's own wording is kept; a textual union of two different
   sentences would be nonsense, and both originals' *behaviours* (re-enable, report) are present.

### 2.4 The union is exact

- **Every behaviour of both originals is present**, asserted behaviour by behaviour against
  `50dfb40`: `missing from the merged handler: []`.
- **Nothing neither original did is present**: every statement line of the merged handler appears
  verbatim in one of the two originals, except **two declared adaptations**:
  - `if (window.LinResults && LinResults.clear) LinResults.clear();` -- `detail.js`'s guarded
    call, verbatim.
  - `if (hostEl && window.LinDetail && LinDetail.render) LinDetail.render(id);` -- `detail.js`'s
    `render(id)`, reached through its own export and guarded on the hosted path. On a portfolio
    row there is no detail page to re-render and `.detail-reset` never existed there, so this is
    the union **on the surface each original actually lived on**.
  `merged statements not present verbatim in either original: []`.

### 2.5 What was removed, each with a non-vacuity proof pinned to `50dfb40`

| removed | existed at `50dfb40` | absent now |
|---|---|---|
| `.detail-reset` button markup (`detail.js:1061`) | PASS | PASS |
| `.detail-reset-msg` aria-live span (`detail.js:1064`) | PASS | PASS |
| `wireReset()` (`detail.js:2334`) | PASS | PASS |
| the `wireReset(root);` call site (`detail.js:1258`) | PASS | PASS |
| `radar.css:895` `.detail-reset-msg { margin: 0; }` | PASS | PASS |

**GUARANTEE 7 IS A REAL CHECK THIS TIME, NOT A VACUOUS ONE.** Run 56 reported its dead-CSS check
as vacuous because there was nothing to remove. Here there was: the rule existed at `50dfb40`,
its control is gone, and `radar.css` now carries **zero** `.detail-reset` selectors. Every
remaining mention of `detail-reset` in `detail.js` is comment, not code (`0` live occurrences).

### 2.6 The page's full control inventory, before and after, measured live

The "before" was measured by injecting the `50dfb40` bytes of all three files, **reading them
back from disk to confirm the injection landed**, measuring, and restoring inside a `finally`.
Tree before the injection and after the restore were compared and are identical.

```
BEFORE PRJ-R50-BROWSER: reset controls = 2 ['Clear stored signals for this project', 'Reset signals']
BEFORE PRJ-R50-BROWSER: all buttons    = ['← Back to Portfolio', 'why?', 'Upload documents',
   'Generate signals for every period', 'Clear stored signals for this project', 'Save info',
   'Recompute this project', 'Reset signals', 'Archive', 'Close', 'Regenerate ↺', 'Free rotate',
   'Top', 'Cost cluster', 'Evidence cluster', 'Governance', 'Free rotate', 'Front', 'Side', 'Top']
BEFORE PRJ-R54-B / PRJ-R54-C: reset controls = 2, same two labels

AFTER  PRJ-R50-BROWSER: reset controls = 1 ['Reset signals']
AFTER  PRJ-R50-BROWSER: all buttons    = ['← Back to Portfolio', 'why?', 'Upload documents',
   'Generate signals for every period', 'Save info', 'Recompute this project', 'Reset signals',
   'Archive', 'Close', 'Regenerate ↺', 'Free rotate', 'Top', 'Cost cluster', 'Evidence cluster',
   'Governance', 'Free rotate', 'Front', 'Side', 'Top']
AFTER  panel order (all three) = ['Save info', 'Recompute this project', 'Reset signals',
   'Archive', 'Close']

PRJ-R50-BROWSER: buttons lost = ['Clear stored signals for this project']   gained = []
PRJ-R54-B:       buttons lost = ['Clear stored signals for this project']   gained = []
PRJ-R54-C:       buttons lost = ['Clear stored signals for this project']   gained = []
```

On all three projects: **exactly one control clears stored signals**, exactly one button was
lost, **none was added or moved** (section 12.6 holds), the panel order is unchanged, the panel
is bound to the viewed project and no other, and the detail page is open and reachable (section
12.8 holds).

### 2.7 Ask, cancel, confirm -- by execution, with counting spies

```
confirmation title  : 'Reset signals for PRJ-R50-BROWSER'
confirmation detail : "This clears PRJ-R50-BROWSER's stored signal values so its documents can be
                       read again. It does not delete documents and it does not touch other projects."
confirmation buttons: ['Reset signals for PRJ-R50-BROWSER']
at the moment the dialog is open, calls made = []
after CANCEL (Escape): calls=[] nav=[] modals=0 page=['detail'] id=PRJ-R50-BROWSER
```

**Cancelling makes no call and changes no state.** No em dash and no en dash in the confirmation
text.

```
CONFIRM on PRJ-R54-B: calls = ['resetSignals(PRJ-R54-B)', 'LinResults.clear()', 'load()',
                               'getProject(PRJ-R54-B)', 'LinDetail.render(PRJ-R54-B)']
logEvent entries in the append-only store: ['RESET signals for PRJ-R54-B.']
not one call mentions PRJ-R50-BROWSER
```

**Confirming really performs the union**, proved by execution and not by reading: the behaviour
that was only in the removed control (`LinResults.clear()`, `getProject`, `LinDetail.render`) and
the behaviour that was only in the survivor (`LinStore.load()`, `logEvent()`) both fire, on that
project and no other. No uncaught page error during the whole drive.

`window.confirm` was **not** introduced: `ingest.js` carries exactly as many as it did at
`50dfb40` (**one**, the pre-existing upload-modal "leave anyway?" guard at `ingest.js:590`), and
the merged handler contains none.

## 3. PHASE B: the derived pins and the two fixed points

Driver: `server/tools/drive_run57_derived_pins.py`, **29 passed, 0 failed**. Every claim is
established by injection: snapshot from the **committed reference** (`campaign_safety.head_text`),
bytes read back from disk to confirm the injection landed, restore inside a `finally`, and the
**start-AND-end** `git status --porcelain` check that is the actual fix for the Run 53 leak class.

### 3.1 The four pins before and after

| pin | before (typed, `50dfb40`) | after (derived) |
|---|---|---|
| `SUCCESSOR_GATE` | `"run56_successor_freeze_gate.csv"` | `f"run{_RUN}_successor_freeze_gate.csv"` |
| `SUCCESSOR_RECORD` | `"RUN56_SUCCESSOR_FREEZE_RECORD.json"` | `f"RUN{_RUN}_SUCCESSOR_FREEZE_RECORD.json"` |
| `SUCCESSOR_REPORT` | `"RUN56_SUCCESSOR_FREEZE_REPORT.md"` | `f"RUN{_RUN}_SUCCESSOR_FREEZE_REPORT.md"` |
| `SUCCESSOR_CHECKSUMS` | `"RUN56_SUCCESSOR_FREEZE_CHECKSUMS.csv"` | `f"RUN{_RUN}_SUCCESSOR_FREEZE_CHECKSUMS.csv"` |
| `no_self_reference` anchor | `"8e557b7b28857171a8611baf28f2c99cfd70c875"`, twice | `PREDECESSOR_ANCHOR`, read from the predecessor release record |

### 3.2 The derivation

`_RUN` is the minting run's number, read from `participant_packages.CURRENT`'s **own checksum
record filename** (`code_audit/run56_participant_package_v22_checksums.sha256` -> `56`). **Four
names become one fact.** `_PRED_RUN` is the same for `PARTICIPANT_PACKAGES[-2]`, and
`PREDECESSOR_ANCHOR` is `RUN{_PRED_RUN}_SUCCESSOR_FREEZE_RECORD.json`'s own
`freeze_candidate_commit`.

Live output at the start of the run, on the Run-56 release:

```
DERIVED from participant_packages.CURRENT (og-participant-2026.08-v22, record
  code_audit/run56_participant_package_v22_checksums.sha256): run 56
  SUCCESSOR_GATE      = run56_successor_freeze_gate.csv
  SUCCESSOR_RECORD    = RUN56_SUCCESSOR_FREEZE_RECORD.json
  SUCCESSOR_REPORT    = RUN56_SUCCESSOR_FREEZE_REPORT.md
  SUCCESSOR_CHECKSUMS = RUN56_SUCCESSOR_FREEZE_CHECKSUMS.csv
DERIVED from the predecessor link (og-participant-2026.08-v21, run 55):
  no_self_reference anchor = 8e557b7b28857171a8611baf28f2c99cfd70c875
```

**The derivation reproduces all five hand-typed values exactly**, so it is a change of mechanism
and not of content.

### 3.3 Nothing is loosened -- section 9.1.3 and guarantee 10

- `git cat-file -t 8e557b7b28857171a8611baf28f2c99cfd70c875` -> `commit`. The anchor is a full
  40-character commit id that **resolves to a specific named commit in this repository at
  evaluation time**. The rule accepts that commit and no other.
- It is read out of the **predecessor's** record, not the record under test, so the check is not
  circular. The two clauses it feeds are unchanged: the current record must **not** name it as its
  own `freeze_candidate_commit`, and **must** name it as `supersedes_candidate`.
- A derivation that cannot resolve **raises** rather than falling back: a record filename with no
  run number, a missing predecessor record, or a `freeze_candidate_commit` that is not a full
  40-character hash each `raise SystemExit` with a message saying the check would otherwise be
  loosened. **Section 11.2 did not fire** -- no pin had to be left typed.

### 3.4 Guarantee 8: no typed release constant survives, and the sweep is uncapped

```
typed release filenames in gate-suite CODE (comments stripped):
  ['"RUN41_SUCCESSOR_FREEZE_RECORD.json"', '"RUN42_..."', '"RUN43_..."',
   '"RUN45_..."', '"RUN47_..."']
typed 40-character commit hashes in gate-suite CODE: []
at 50dfb40 the same sweep found 9 typed release filenames and 2 typed commit hashes
naming the release under test or its predecessor: now [], at 50dfb40
  ['"run56_successor_freeze_gate.csv"', '"RUN56_SUCCESSOR_FREEZE_RECORD.json"',
   '"RUN56_SUCCESSOR_FREEZE_REPORT.md"', '"RUN56_SUCCESSOR_FREEZE_CHECKSUMS.csv"']
```

**The five that remain are the SEALED HISTORICAL predecessor roster** (runs 41, 42, 43, 45, 47)
that the `predecessor_release_preserved` rows walk. They are typed **deliberately**: a sealed
predecessor's name is fixed forever, and deriving it would stop the row noticing if one were
rewritten. The check is scoped to the release under test and its predecessor, and it is **not
vacuous**: at the explicit commit `50dfb40` the same uncapped sweep found four such names and two
typed commit hashes.

### 3.5 Guarantee 9: the non-vacuity injection

`participant_packages.py` was injected with a two-line append pointing the chain one link back
(`PARTICIPANT_PACKAGES = PARTICIPANT_PACKAGES[:-1]`). Bytes read back from disk; restored in a
`finally`; tree clean before and after; baseline gate re-run after the restore.

```
UNDER FAULT SUCCESSOR_GATE         = run55_successor_freeze_gate.csv
UNDER FAULT SUCCESSOR_RECORD       = RUN55_SUCCESSOR_FREEZE_RECORD.json
UNDER FAULT SUCCESSOR_REPORT       = RUN55_SUCCESSOR_FREEZE_REPORT.md
UNDER FAULT SUCCESSOR_CHECKSUMS    = RUN55_SUCCESSOR_FREEZE_CHECKSUMS.csv
UNDER FAULT ANCHOR                 = d236a2706a801cad8547ba34d68b0dc83521ff52
RESULT: 32/34 checks passed
  - run37.gate.generator_runs
  - run37.gate.reproduces
```

- **The pins go red for the intended reason**: `run37.gate.reproduces` fails, because the gate
  artefact now being named is the predecessor's, which the live tree does not reproduce.
- **ALL FOUR NAMES MOVED TOGETHER.** They cannot disagree with one another. **The Run-55 state --
  one advanced, three left behind -- is not expressible**, which is section 9.1 item 5 answered
  by construction rather than by a simulation of it.
- **AND THE FINDING THIS INJECTION MAKES.** `no_self_reference` and `disposition` stayed **GREEN**
  under the fault, because the RUN55 record is internally consistent. **That is exactly the "two
  stale pins agreeing with each other" phenomenon.** A consistent stale release reads exactly like
  the right one, which is precisely why these pins had to be **derived** rather than cross-checked.
  Reported as the measurement, not dressed up.

### 3.6 Guarantee 11: `CANDIDATE` refuses, proved twice

`CANDIDATE` **remains a constant the owner edits.** What was removed is the guesswork.
`expected_candidate()` computes what it should read: the **oldest commit in the unbroken run back
from HEAD whose tree agrees with the working tree on every member path of the candidate
identity**. Later commits that touch only reports, handoffs and records do not move it, which is
why the value survives the several commits a mint makes after the production edit lands.

Proof 1 -- on the real tree, before `CANDIDATE` was set for this mint:

```
CANDIDATE FIXED POINT (Run 57 section 9.2)
  CANDIDATE as set in this file : db942f2ebe4ae27b598f76bd8307517e862f4a69
  CANDIDATE as computed         : e09ad18f4f2bee9c1b430abe0a700acef13403e6
REFUSING TO PROCEED. ...
  build_run37_acceptance.py CANDIDATE = db942f2ebe4ae27b598f76bd8307517e862f4a69
  it should read                      = e09ad18f4f2bee9c1b430abe0a700acef13403e6
  ... This generator does not edit the constant ...
exit status 3
```

Proof 2 -- deliberate injection of `CANDIDATE = "0000...0"`, bytes read back from disk, restored
in a `finally`: exit **3**, **both values named**, the constant **not edited** (byte-identical
after the refusal), and **no gate produced at all** -- a stop, not a warning.

**NOT DETERMINABLE is reported and does not refuse.** When the working tree diverges from every
commit on the identity's member paths -- which is a dirty tree, which is blocker B01's own job --
the generator prints `CANDIDATE as computed : NOT DETERMINABLE` with the reason, and continues.
Refusing there would make the generator unrunnable on the dirty tree every mint necessarily
starts from, which would be a change of mechanism dressed as a check.

### 3.7 The B01 evidence fixed point: SECTION 9.3 ITEM 1, NOT ITEM 2

**The count is the governed property and it is unchanged.** B01's count is `dirty` -- the number
of content-addressed digests in the candidate identity the live tree no longer reproduces
(`build_run37_acceptance.py:461-477`). The git porcelain line count is **incidental**: B01 never
reads it, never compares it and never fails on it. It appeared only in the evidence *string*.

So item 1 applies and item 2 does not, and section 11.3 did not fire. The evidence now records
the governed property:

```
before: "11 content-addressed digests recomputed from the tree and compared;
         git porcelain lines at evaluation: N"
after : "11 content-addressed digests recomputed from the tree and compared;
         digests that diverge from the candidate identity: 0"
```

The porcelain count is **not discarded** -- it is printed to the mint log, where a varying number
belongs:

```
B01: git porcelain lines at evaluation: 2 (INCIDENTAL to B01 and deliberately not written into
the gate artefact; B01's governed property is the digest comparison, whose divergence count is 0)
```

**Effect, measured:** the committed gate artefact now reproduces byte for byte from a
regeneration taken on a tree that is not already clean. Run 56 paid two whole mints for that
condition (its mints 5 and 7). This run paid none.

## 4. PHASE C: the mint

### 4.1 Every piece

| # | Piece | Value |
|---|---|---|
| 1 | `sim-2026.08-v38` | `server/app/simulation/models.py`; `SIMULATION_VERSION_SUPERSEDED` -> `sim-2026.08-v37`; history **appended**, never edited (38 entries) |
| 2 | `og-participant-2026.08-v23` | appended to `PARTICIPANT_PACKAGES`; `CURRENT` |
| 3 | v22 **PINNED** | `og-participant-2026.08-v22`'s `source_commit` moves from `None` to **`50dfb40fd83850a5342ab9106c063cbe87f367e9`**. See 4.2 -- the order named `dbb4bf9` and the byte check says the tip. **The v22 record FILE is not touched.** |
| 4 | The v23 checksum record | `code_audit/run57_participant_package_v23_checksums.sha256`, **69 members**. v22 -> v23 **measured, not assumed**: **3 changed** (`assets/css/radar.css`, `assets/js/detail.js`, `assets/js/ingest.js`), **0 added, 0 deleted**. |
| 5 | **NO sequence exception, DECLARED not omitted** | `V22_TO_V23_SEQUENCE_EXCEPTION` and `V22_TO_V23_DELETED` are **empty tuples that are declared**. All five members of `SEQUENCE_BEARING_FILES_FROM_V21` (`decision.js`, `decision-ui.js`, `workspace.js`, `intake.json`, `debrief.json`) are present and byte-identical to v22, measured. **The empty tuple is the declaration this run makes.** |
| 6 | Production-tree re-take | `code_audit/run57_production_tree.sha256`, **242 files**, manifest sha256 `6e7a783697ebf032d9b4d21f4869989f06edcd8c944e348eb2b69f270fc42e07`. The guard was observed reporting **exactly four CHANGED** (`radar.css`, `detail.js`, `ingest.js`, `models.py`) and nothing added, removed or renamed **before** the manifest was written. `production_tree.PINNED` -> run57, `PINNED_RUN56` kept addressable. |
| 7 | Authority-tree re-take | **RE-TAKEN AND DELIBERATELY NOT SUPERSEDED**, for the fourth run running: `added=0 removed=0 changed=0 renamed=0`, recomputed sha256 `b52c47a68a20ab1629681ea240abdea2167c67f289d181f446a8170704dc1596`, byte for byte the pinned file's. A manifest is superseded when what it describes moves. |
| 8 | `run57_freeze_candidate_identity.json` | identity digest `24ba66f249f14a4da5ca372af0a50fa979618e5348e0c2dd59a4a91f988a2ec4`, candidate `e09ad18f4f2bee9c1b430abe0a700acef13403e6`, supersedes `db942f2ebe4ae27b598f76bd8307517e862f4a69` |
| + | `run57_successor_freeze_gate.csv` | 15 blockers, **0 blocked** |
| + | `run57_candidate_behaviour_digest.json` | `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1` |
| + | `RUN57_SUCCESSOR_FREEZE_{RECORD.json,REPORT.md,CHECKSUMS.csv}` | `FINAL_FREEZE_ACCEPTED`, **146 rows**, release content digest `3bdeaa2fa09ed8ba7745e69a0418b4318e9caefa715fd49253d7f0098c072691` |

**The change set names every file that moved:**

```
assets/js/ingest.js                              phase A: the merged union handler
assets/js/detail.js                              phase A: .detail-reset removed, markup + span + handler + call site
assets/css/radar.css                             phase A: the dead .detail-reset-msg rule removed
server/app/simulation/models.py                  the stamp
server/tools/participant_packages.py             v23, the v22 pin, the three v22->v23 declarations
server/tools/production_tree.py                  PINNED -> run57, PINNED_RUN56 addressable
server/tools/test_run37_freeze_gate.py           phase B: the four pins and the anchor DERIVED
server/tools/build_run37_acceptance.py           phase B: expected_candidate() + the refusal + B01 evidence; the mint constants
server/tools/drive_run57_reset_merge.py          NEW, the phase A driver
server/tools/drive_run57_derived_pins.py         NEW, the phase B injection driver
server/tools/build_run57_candidate_identity.py   NEW
server/tools/build_run57_successor_release.py    NEW
code_audit/run57_participant_package_v23_checksums.sha256   NEW
code_audit/run57_production_tree.sha256                     NEW
research/freeze/run57_freeze_candidate_identity.json        NEW
research/freeze/run57_successor_freeze_gate.csv             NEW
research/freeze/run57_candidate_behaviour_digest.json       NEW
research/freeze/RUN57_SUCCESSOR_FREEZE_RECORD.json          NEW
research/freeze/RUN57_SUCCESSOR_FREEZE_REPORT.md            NEW
research/freeze/RUN57_SUCCESSOR_FREEZE_CHECKSUMS.csv        NEW
```

**The suite population is unchanged at 203.** The two new files are `drive_*`, not `test_*`, which
is the established shape: `test_suite_identity` measured **203 files** in the new candidate
identity.

### 4.2 The v22 pin: the order said `dbb4bf9`, the byte check says `50dfb40`

Section 10.3 directs pinning v22's `source_commit` to `dbb4bf9`, "the commit whose blobs it
describes". **That is checked, not assumed.** Every one of the v22 record's 69 members was re-read
with `git show <commit>:<path>` and sha256'd against the record:

```
db942f2: mismatches=0        fa3ad7e: mismatches=0
67e709d: mismatches=0        dbb4bf9: mismatches=0
09bf7f1: mismatches=0        50dfb40: mismatches=0
e13b4f1: mismatches=1  [('assets/js/ingest.js', 'DIFFERS')]
```

**SIX commits reproduce the record exactly, so the record's bytes alone do not single one out.**
`dbb4bf9` is one of them, so the order's premise is not wrong -- it is under-determined.

The chain's own rule settles it, and it is the rule **v21 was pinned under**: *the tip of `main`
at which the package was still current*. The v21 header states it in those words for `e13b4f1`.
For v22 that tip is **`50dfb40`** -- the record commit Run 56 made on top of its own `--no-ff`
merge after pushing, and the last commit on `main` before this link's successor exists.
`dbb4bf9` is the merge commit beneath it.

**Pinned to `50dfb40`, byte-verified member by member, and the reason is on the record in
`participant_packages.py` and in the v23 header.** The v22 record file is **not edited** -- its
header still says it describes the live tree, exactly as Run 56 wrote it, because rewriting a
predecessor record to agree with the present is what B11 exists to catch.

### 4.3 HOW MANY MINTS WERE PAID, AND WHETHER PHASE B REDUCED THE NUMBER

**THREE.** Run 51 paid four, Run 52 three, Run 55 four, Run 56 seven.

| Mint | What surfaced |
|---|---|
| **1** (after the phase-C production commit `e09ad18`) | The generator **REFUSED**, naming both values, because `CANDIDATE` still read Run 56's `db942f2`; it said to set it to `e09ad18`. Set, re-run: **gate clean on that pass** -- 15 blockers, 0 blocked; B01 divergence 0; behaviour digest RE-DERIVED to `8fb4d366...`; release built; **freeze gate suite 34/34** with no stale-pin chase of any kind. |
| **2** (after the twelve-suite reconciliation `bb065bc`) | The full 203-suite pass came back **15264/15290 with twelve suites red**, every one a guard this run's phase A or its own mint had falsified. Reconciling them changed twelve `test_*.py` files, **all members of `test_suite_identity`**, so the identity had to be re-taken against the commit carrying them. Identity `7fe9b642...`, release `ced8b9bc...`, **gate clean**, digest `8fb4d366...` again, gate suite 34/34. **`run57_successor_freeze_gate.csv` did not move on this pass.** |
| **3** (after the two immutability guards `13c1509`) | The second full pass came back **15305/15307 with two red**: `test_run38_frozen_immutability` and `test_run39_frozen_immutability`, whose PERMITTED_MODIFICATIONS lists name by name every pre-existing file a run may modify, and `test_run21_reset_disclosure.py` was not in them. Added by name with the reason. Both are `test_suite_identity` members, so the identity was re-taken once more. Identity `5d2a1ca9...`, release `bd15840f...`, **gate clean**, digest `8fb4d366...` again, gate suite 34/34, gate CSV unmoved. |

**PHASE B REDUCED IT, AND THE REDUCTION IS ATTRIBUTABLE RATHER THAN CLAIMED.** Four of Run 56's
seven mints existed to chase exactly the three fixed points phase B closed, and every one of
them is observably absent here:

| Run 56 mint | Why it was paid | What happened this run |
|---|---|---|
| its 2 | Gate row 3 (`reproduces`) red: `SUCCESSOR_GATE` still pinned at `run55_`, and chasing it uncovered three more stale pins | **Did not occur, on any of the three mints.** The four names derived to `run57_`/`RUN57_` from `participant_packages.CURRENT`, with nothing typed. |
| its 4 | Row 34 (`no_self_reference`) red: the anchor was still Run 48's candidate | **Did not occur, on any of the three mints.** The anchor derived to `db942f2` from the predecessor release record, with nothing typed. |
| its 5 and its 7 | The committed gate CSV and a fresh regeneration differed on **one line**, B01's porcelain evidence, so a further regeneration on an already-clean tree was needed each time | **Did not occur.** B01's evidence is deterministic, so `run37.gate.reproduces` passed on the same pass that wrote the artefact, all three times, and `run57_successor_freeze_gate.csv` did not move on mints 2 or 3 at all. |

**WHAT STILL FORCED EACH EXTRA PASS, STATED PLAINLY.** Neither of the two extra mints was a
fixed point and neither is something phase B claimed to remove:

- **Mint 2 and mint 3 were both forced by the SAME mechanism: reconciling a pinned guard changes
  a `test_*.py` file, and every `test_*.py` file is a member of `test_suite_identity`, so the
  candidate identity must be re-taken against the commit that carries the reconciliation.** Run
  56 paid its mint 6 for exactly this. It is the cost of the guards being *in* the thing they
  guard, not the cost of a fixed point.
- **Mint 3 exists because the first full pass could not have found what the second found.** The
  twelve suites of mint 2 had to be *fixed* before the two immutability guards could observe that
  one of those fixes touched a file they did not permit. That is a genuinely serial dependency,
  not a repeated failure.

**The floor is one mint**: the candidate identity is a statement about a commit, so the
production edits must be committed before the identity can name the commit carrying them. Phase B
removed the fixed-point mints entirely; what remains is the reconciliation cascade, and section
10 names it as the decision for the owner.


### 4.5 EVERY GATE ROW, WITH ITS VERDICT, FROM LIVE OUTPUT

`python3 -u server/tools/test_run37_freeze_gate.py`, exit status 0, **RESULT: 34/34 checks
passed**. No row is reported from a cached artefact; each line below is the suite's own output.

| # | row | verdict |
|---|---|---|
| 1 | `run37.gate.generator_runs` -- the acceptance generator runs to completion; a crash is a blocker, not a pass | PASS |
| 2 | `run37.gate.artifact_present` -- the committed freeze gate exists | PASS |
| 3 | `run37.gate.reproduces` -- and it REPRODUCES from the current tree, so it is not a stale snapshot | PASS |
| 4 | `run37.gate.fifteen_blocker_classes` -- all fifteen blocker classes are evaluated | PASS |
| 5 | `run37.gate.B01` dirty candidate identity is zero | PASS |
| 6 | `run37.gate.B02` population mismatch is zero | PASS |
| 7 | `run37.gate.B03` controlled-stimulus mismatch is zero | PASS |
| 8 | `run37.gate.B04` participant-sequence drift is zero | PASS |
| 9 | `run37.gate.B05` false defensibility statement is zero | PASS |
| 10 | `run37.gate.B06` unexpected execution exception is zero | PASS |
| 11 | `run37.gate.B07` Category-9 bypass is zero | PASS |
| 12 | `run37.gate.B08` Category-10 authority violation is zero | PASS |
| 13 | `run37.gate.B09` voting count is not exactly 2 is zero | PASS |
| 14 | `run37.gate.B10` current taxonomy dual authority is zero | PASS |
| 15 | `run37.gate.B11` package or predecessor mutation is zero | PASS |
| 16 | `run37.gate.B12` browser qualification failure is zero | PASS |
| 17 | `run37.gate.B13` unresolved blocking Run-36 defect is zero | PASS |
| 18 | `run37.gate.B14` unsupported final empirical-validation claim is zero | PASS |
| 19 | `run37.gate.B15` candidate behaviour changed during the run is zero | PASS |
| 20 | `run37.gate.blocking_defects_zero` -- BLOCKING DEFECTS = 0 | PASS |
| 21 | `run37.gate.predecessor_release_preserved` -- v25 still present and still says v25 | PASS |
| 22 | `run37.gate.immediate_predecessor_release_preserved` -- v26 | PASS |
| 23 | `run37.gate.immediate_predecessor_release_preserved` -- v27 | PASS |
| 24 | `run37.gate.immediate_predecessor_release_preserved` -- v28 | PASS |
| 25 | `run37.gate.immediate_predecessor_release_preserved` -- v30 | PASS |
| 26 | `run37.gate.immediate_predecessor_release_preserved` -- v31 | PASS |
| 27 | `run37.gate.no_release_while_blocked` | PASS |
| 28 | `run37.gate.release_present_when_clean` -- record, report and checksum manifest exist | PASS |
| 29 | `run37.gate.limitation_stated` -- empirical field validation is 0 of 100 | PASS |
| 30 | `run37.gate.limitation_stated` -- no claim of validated real-world predictive effectiveness | PASS |
| 31 | `run37.gate.limitation_stated` -- the historical incompleteness of OG-SYNTH-0.1 | PASS |
| 32 | `run37.gate.limitation_stated` -- bounded controlled-study instrument use | PASS |
| 33 | `run37.gate.disposition` -- FINAL_FREEZE_ACCEPTED and the gate agrees | PASS |
| 34 | `run37.gate.no_self_reference` -- the record distinguishes `freeze_candidate_commit`, `release_content_digest` and `release_commit_recording_method`, and contains no self-referential placeholder | PASS |

**Rows 3, 28, 33 and 34 are the four that depend on the release pins, and every one of them ran
against names DERIVED from `participant_packages.CURRENT` rather than typed.** Row 34's anchor
resolved to `db942f2`, the Run-56 candidate, read out of the Run-56 release record.

### 4.6 THE BEHAVIOUR DIGEST, RE-DERIVED

`8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1`, **re-derived on both mints
and unchanged**. Section 12.1 did not fire. It is written last and only when the gate is clean,
so a run that mutated behaviour cannot quietly re-baseline itself.

### 4.7 THE FULL SUITE, AND THE FOURTEEN IT FOUND

**FINAL: `Suites run: 203   Total checks: 15307/15307` -- `ALL SUITES GREEN`**, from
`server/run_all_suites.sh`, which builds a migrated SQLite template and copies it per suite.
No suite left production or client source dirty on any pass.

| pass | result |
|---|---|
| 1, after mint 1 | `203 suites, 15264/15290`, **twelve red** |
| 2, after mint 2 | `203 suites, 15305/15307`, **two red** |
| 3, after mint 3 | `203 suites, 15307/15307`, **ALL SUITES GREEN** |

**NO CHECK WAS DELETED AND SEVENTEEN WERE ADDED.** 15290 -> 15307, and the rise is accounted for
exactly: `test_run21_reset_disclosure` 32 -> 33 (one check added, requiring that `detail.js`
carries no reset control at all) and `test_run28_participant_packages` 292 -> 308 (the full v23
block). **The suite population is unchanged at 203.**

**The fourteen, and what each was:**

| suite | before | after | reconciliation |
|---|---|---|---|
| `test_run21_reset_disclosure` | 31/32 | **33/33** | the promise "Does not delete documents" was read off `.detail-reset`'s title in `detail.js`. **The control moved file; the promise did not move and is not weakened.** Re-pointed at `ingest.js`, where the survivor's confirmation makes it in the same words, and a check **added** requiring `detail.js` to carry no reset control at all -- so the sentence cannot be satisfied by a control that is no longer there |
| `test_run2_fifteen_defects` | 257/259 | **259/259** | the `detail.js` freeze diff. `RUN57_REMOVED` names **all forty** lines that left and `RUN57_ADDED` **all thirteen** that arrived, line by line. Every addition is prose: no code was added to this file. The allowance is extended by exactly the lines this run moved, never widened by a pattern |
| `test_run28_participant_packages` | 285/292 | **308/308** | the v22 block converted from CURRENT to **PREDECESSOR** and measured at the explicit commit `50dfb40` -- stricter than reading disk, which has moved on -- and a **full v23 CURRENT block added**, because converting v22 alone would have left the chain's central guarantee (the CURRENT record's checksums hold against the LIVE TREE) with **no subject at all** |
| `test_run25_rail_removal` | 55/56 | **56/56** | `run57_production_tree.sha256` appended to the manifest chain. Nothing removed from the tuple |
| `test_run31_version_boundaries` | 55/56 | **56/56** | `sim-2026.08-v38` appended to the stamp ladder |
| `test_run32_closure_version_boundary` | 25/26 | **26/26** | same |
| `test_run36_fault_guards` | 40/41 | **41/41** | `V22_TO_V23_SEQUENCE_EXCEPTION` folded into the authorised union -- **empty, so the set does not grow and the `len(...) == 6` assertion is unchanged** -- and the v23 record added to `_BY_SUCCESSOR`, whose last entry must **be** `PP.CURRENT.record`, so a mint that forgot its own link goes red rather than passing by omission |
| `test_run36_instrument_qualification` | 75/76 | **76/76** | current package advanced to v23 |
| `test_run38_frozen_immutability` | 15/17 -> 16/17 | **17/17** | stamp and package advanced; then `test_run21_reset_disclosure.py` added **by name** to `PERMITTED_MODIFICATIONS`, with the reason |
| `test_run39_frozen_immutability` | 17/19 -> 18/19 | **19/19** | same |
| `test_run39_launch_gate` | 97/100 | **100/100** | identity expectations advanced by one |
| `test_run41_preservation` | 29/33 | **33/33** | **the whole ladder SHIFTED, not inserted into.** The tail is checked position by position, so appending v38 moves every index below it; adding a row without shifting the rest would leave two clauses asserting the same index and **silently drop one stamp from the check while still passing** |

**A trap avoided, stated because Run 56 hit the same one.** `test_run41_preservation`'s history
check is positional. The ladder now runs `[-1]` v38 through `[-9]` v30, one deeper than before.

## 5. Every item STOPPED under section 11, with its reason

**NONE.** All four local stop conditions were evaluated and none fired.

| condition | evaluated | outcome |
|---|---|---|
| 11.1 the union cannot be built without changing what either control does | Both bodies extracted from `50dfb40` and compared statement by statement. No two calls in the union conflict: `LinStore.load()` and `getProject(id)` are ordered so the reload cannot overwrite the fetch, and the awaiting-ingest mutation follows both. | **Did not fire.** The union was built and asserted exact. |
| 11.2 deriving a release pin would loosen a check | The anchor still resolves, at evaluation time, to one specific named commit that `git cat-file -t` confirms. The four names still each resolve to one file for one release. | **Did not fire.** No pin was left typed. |
| 11.3 making the B01 evidence reproducible would change what B01 asserts | B01's count is the digest divergence; the porcelain line count was evidence text only. | **Did not fire.** Section 9.3 item 1 was taken, not item 2. |
| 11.4 a ruling rests on a premise the code contradicts | Two premises were checked by execution. See below. | **Did not fire as a stop**, but two premise corrections are reported. |

**TWO PREMISE CORRECTIONS, reported rather than absorbed.** Neither required stopping an item,
because in both cases the ruling could be carried once the true fact was established.

1. **Section 3's `main == origin/main == dbb4bf9` is wrong; it is `50dfb40`.** Reported in section
   1. The branch is rooted at the real tip.
2. **Section 10.3's "pin the v22 record's `source_commit` to `dbb4bf9`, the commit whose blobs it
   describes" is under-determined.** Six commits reproduce those blobs exactly. Reported in
   section 4.2, and pinned to `50dfb40` under the chain's own rule -- byte-verified, not asserted.

## 6. Every item UNSTARTED FOR BUDGET, named as unstarted

**NONE.** Every ordered item in sections 6 through 10 was executed. Section 13's nineteen
guarantees were all attempted; their verdicts are in section 7 below.

## 7. Every guarantee at section 13, verified or not met, each with its injection

| # | guarantee | verdict | injection / evidence |
|---|---|---|---|
| 1 | The detail page carries exactly one control that clears stored signals, in a browser on more than one project | **VERIFIED** | `50dfb40` bytes of `detail.js`, `ingest.js` and `radar.css` injected, read back from disk, "before" measured on **three** projects (2 controls each), restored in a `finally`, tree compared before and after, "after" measured (1 control each) |
| 2 | The merged handler performs every behaviour of both originals, against an explicit commit | **VERIFIED** | 13-behaviour table extracted from `50dfb40`; `missing from the merged handler: []`; and by execution with counting spies |
| 3 | The merged handler performs nothing neither original did | **VERIFIED** | statement-by-statement: `merged statements not present verbatim in either original: []`, plus two **declared** adaptations |
| 4 | The removed control existed before this run, pinned explicitly | **VERIFIED** | five separate existence checks at `50dfb40fd83850a5342ab9106c063cbe87f367e9` -- markup, span, handler, call site, CSS rule |
| 5 | The surviving control asks before clearing; cancelling makes no call and changes no state, by execution with counting spies | **VERIFIED** | spies on six `LinStore` methods, `LinResults.clear`, `LinDetail.render` and `LinApp.showPage`; at dialog-open `calls == []`; after Escape `calls=[] nav=[] modals=0 page=['detail'] id=PRJ-R50-BROWSER` |
| 6 | Confirming clears the signals of that project and no other, by execution | **VERIFIED** | `['resetSignals(PRJ-R54-B)', 'LinResults.clear()', 'load()', 'getProject(PRJ-R54-B)', 'LinDetail.render(PRJ-R54-B)']`; no call mentions `PRJ-R50-BROWSER`; the append-only log reads `['RESET signals for PRJ-R54-B.']` |
| 7 | No dead CSS rule survives the removal, with a non-vacuity proof | **VERIFIED, AND NOT VACUOUS** | `.detail-reset-msg { margin: 0; }` **existed** at `50dfb40` and `radar.css` now carries zero `.detail-reset` selectors. Run 56 had to report this check vacuous; this run does not |
| 8 | The four release pins are derived, and no typed release constant survives in the gate suite | **VERIFIED** | uncapped sweep of the gate suite's code: zero typed names for the release under test or its predecessor, zero typed 40-character hashes; at `50dfb40` the same sweep found 4 and 2. The five sealed historical names (runs 41-47) remain and are typed deliberately |
| 9 | The derived pins go red for the intended reason when the chain is pointed at a predecessor | **VERIFIED** | `participant_packages.py` injected to drop the last link; all four names moved to `run55_`/`RUN55_` together, the anchor moved to `d236a27`, and `run37.gate.reproduces` went red. Restored; tree clean before and after; baseline re-run |
| 10 | The `no_self_reference` anchor is a specific named commit at evaluation, not a loosened rule | **VERIFIED** | 40-hex format check plus `git cat-file -t 8e557b7b...` -> `commit`, and equality with the predecessor record's own `freeze_candidate_commit` |
| 11 | The mint refuses to proceed while `CANDIDATE` does not match, naming both values, proved by running it with a deliberately wrong value | **VERIFIED TWICE** | (a) on the real tree with Run 56's stale value: exit 3, both values named; (b) injected `CANDIDATE = "0000...0"`, read back from disk: exit 3, both values named, constant unedited, no gate produced |
| 12 | The behaviour digest is re-derived, not assumed | **VERIFIED** | re-derived on both mints to `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1` |
| 13 | No stored figure changes | **VERIFIED** | gate B02, B05, B09, B10, B14 all zero; `run37_defensibility_reconciliation.csv` 105 rows and `run37_execution_census.csv` 109 rows regenerate identically (they are not in `git status` after the mint) |
| 14 | Modules in service is 63, registry total 101, both derived | **VERIFIED** | `len(service_index()) == 63`, `len(registry_index()) == 101`, printed live by the browser driver (`in service: 63  registry: 101  retired: 38`) and asserted by gate B02 |
| 15 | Voting count is exactly 2, `A1.7` and `A1.8` | **VERIFIED** | gate B09 zero; live: `frozenset({'A1.8', 'A1.7'})` |
| 16 | Every runtime lookup across all 101 registered modules resolves, asserted live | **VERIFIED** | gate B06 (unexpected execution exception) zero over the full execution census, 109 rows |
| 17 | No rendered identifier changed | **VERIFIED** | the browser inventory's full button list is identical before and after except the one removed label; no naming sweep was run and no identifier was added or removed |
| 18 | No em dash or en dash renders in user-facing text | **VERIFIED** | the confirmation text read back from the rendered dialog: `no em dash and no en dash` |
| 19 | The successor freeze gate passes in full | **VERIFIED** | 34/34, section 4.5 |

## 8. Which audit artifacts the suites rewrote, and were restored

**TWENTY-SIX**, the same 26 Runs 52, 54, 55 and 56 each saw. None was committed; every one was
restored with an explicit `git checkout --` naming the path, and `git status --porcelain` was
empty afterwards.

```
code_audit/run8_expectation_mutation_proof.csv
code_audit/run9_abstention_results.csv
code_audit/run9_alias_overlay_verification.csv
code_audit/run9_fixture_import_results.csv
code_audit/run9_known_answer_results.csv
code_audit/run9_no_operational_effect.csv
code_audit/run9_validator_gap_recomputations.csv
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
server/tools/run17/coverage.csv
```

The three `code_audit/run37_*.csv` are **not** in that list: every digest re-derivation was run
with `--out-audit <scratch dir>` so they were never touched, exactly as the order directs.

## 9. Incidental findings, unacted

1. **`assets/js/ingest.js:590` gates the upload modal's "Uploads in progress, leave anyway?" on
   `window.confirm`.** Four files in this repository record that `window.confirm` returns false in
   this container, so that branch never runs here and `doClose()` is unreachable by that path.
   It is **pre-existing**, this run does not touch it, and no fix is recommended -- the order does
   not ask for one.
2. **`server/tools/drive_run56_duplicate_controls.py` no longer passes against this tree.** Its
   sections 1 and 5 assert that `.detail-reset` exists and that `.detail-reset-msg` is *not* dead
   CSS -- both true of Run 56's tree and false of this one. It is **not rewritten**: it is Run 56's
   evidence for Run 56's release, and it reads the live tree by design. It is a `drive_*` file and
   is therefore not in the 203-suite population, so nothing in the acceptance run depends on it.
3. **`test_run39_launch_gate.py`, `test_run21_reset_disclosure.py` and
   `test_run2_fifteen_defects.py` fail with a SQLite `IntegrityError` if handed a database another
   suite has already seeded.** `run_all_suites.sh` copies a fresh template per suite, so this is
   invisible there; it is only visible when a suite is run by hand against a reused database. This
   is the same family as carry-forward 12.
4. **The `no_self_reference` row would stay green against a *consistent* stale release.** Measured
   in section 3.5. Deriving the pins removes the way that state can arise; the row itself is
   unchanged and is not able to detect it on its own.

## 10. What the next session needs, stated as a decision for the owner

1. **`participant_packages.py` is now the single source of truth for the freeze gate's release
   names.** A mint that advances `CURRENT` advances the gate's four names and its anchor with it.
   **Decision: is any other hand-edited mint constant to be moved onto the same footing?** The
   remaining ones are `build_run37_acceptance.py`'s `PREDECESSOR_CANDIDATE`, `PREDECESSOR_VERSION`,
   `EXPECTED_VERSION`, `IDENTITY_FILE`, `GATE_FILE`, `PRIOR_BEHAVIOUR_FILE` and `BEHAVIOUR_FILE`,
   and `production_tree.PINNED`. Each is the same shape as the four just derived, and each is
   currently advanced by hand every mint. Not ordered this run and not done.
2. **`CANDIDATE` is now checked but still set by hand, deliberately.** The refusal fires on every
   run where it is wrong. **Decision: keep it as the owner's assignment (the current design), or
   allow the mint to write it when the computed value is unambiguous?** The order settled this for
   Run 57; it will recur every mint.
3. **The twelve-suite reconciliation is the remaining cost of a mint, and it is not shrinking.**
   Run 56 reconciled ten, Run 57 twelve, and each reconciliation changes `test_suite_identity`
   members and so forces one further mint. **Decision: is a mechanism for the pinned-ladder guards
   -- the `sim-2026.08-vNN` tails in `test_run31`, `test_run32`, `test_run41`, and the
   current-stamp assertions in `test_run36`, `test_run38`, `test_run39` -- worth building, on the
   same "derive from one fact" principle phase B applied to the release pins?** It is the largest
   remaining hand-edit surface, and it is exactly the shape phase B just proved out. Not ordered
   and not done.

## Carry-forward items, unacted

1. **CPI 1.22 on the site render.** Needs read access to PRJ-001's stored rows, which no session
   may have. Unacted. The open question is still which document type wrote `pv`.
2. **The `historical_data` triple**, Run 47's only unimplemented relation. Unacted.
3. **`signal_inputs.sources` records no source field name.** Unacted.
4. **Four status comparisons remain case-sensitive**, two in `decision.js`. Unacted; `decision.js`
   is sequence-bearing and did not move this run.
5. **Two Run 45 census artifacts do not match the v30 release manifest.** Unacted.
6. **`test_run47_evm_consistency.py` swallows its own traceback.** Unacted.
7. **Run 47's handoff entry is at the bottom of `T6_HANDOFF.md`.** Left there.
8. **`REG.method_label(m)` returns `None` for 96 of 101 registered modules.** Unacted.
9. **`new_id` and `old_id` stay.** Not a naming survivor. Unacted.
10. **`isolation_forest.py`** flagged dirty four times in Run 54, not at all since, and not at all
    in either full pass this run. Still not determinable. On watch.
11. **`test_run33_ph1_fault_campaign.py`** scored 36/46 in Run 54's runner and 46/46 since,
    including both full passes this run. Unresolved.
12. **`test_run2_fifteen_defects.py`** produces two different check totals depending on the
    database it is handed. Observed again this run (see incidental finding 3). Unacted.
13. **The `snapshot_from HEAD` conversion** is unstarted for most campaigns. All 39 remain armed.
    The two drivers this run adds both use `campaign_safety` from the start.
14. **`RUN55_SUCCESSOR_FREEZE_REPORT.md` ships headed "Run-52 successor freeze report" for
    `sim-2026.08-v35`.** NOT rewritten -- it is that release's evidence. **CONFIRMED for this
    run:** `research/freeze/RUN57_SUCCESSOR_FREEZE_REPORT.md` is headed
    `# Run-57 successor freeze report` and reads
    `**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v38``. Its body was rewritten for
    this release rather than carried forward: it names the merge, the survivor and the reason,
    the handler order, what went with the removal, and the before/after browser measurement. The
    record's delta key is `behavioural_delta_v37_to_v38`.
15. **`assets/js/ingest.js` is not a member of the release's governed manifest.** Confirmed again:
    the release builder reports `governed files moved since v32: ['server/app/simulation/models.py']`
    and nothing else, although three client files moved. The client files are covered by the
    participant-package checksum record (`code_audit/run57_participant_package_v23_checksums.sha256`,
    69 members, 3 moved). Widening a governed manifest was not ordered and was not done.
16. **The suite population is 203.** Confirmed and unchanged: 193 in `server/tools/`, 10 in
    `server/tests/`, and `test_suite_identity` in the candidate identity measures 203 files. The
    two files this run adds are `drive_*`, not `test_*`.

## Rules

Every claim above carries its evidence: a file and line, or a command and its output. Where a
value could not be established it is named **not determinable** rather than reconstructed -- the
`expected_candidate()` NOT DETERMINABLE branch is that discipline in code. No fix is recommended
beyond what the order requires; the three items in section 10 are stated as decisions, not as
recommendations.
