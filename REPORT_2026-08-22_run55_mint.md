# Run 55: the mint, and what it carries

**Repository:** the Linux clone at `/home/user/LinPRojectRadar`. The Windows path in section 5
of the order was not reachable from this session and was not used.
**Interpreter:** `python3` 3.11.15, the documented fallback. `ls -d .venv` -> no venv, so
`server/run_all_suites.sh` fell through to `command -v python3` as it is written to.
**Branch:** `run54-phases`, rooted at `bf36ef6`, started at `d5f4243`.

---

## THE HEADLINE

1. **All four phases were completed and each was committed before the next began.**
2. **THE MINT IS PAID AND THE 34-ROW FREEZE GATE IS 34/34.** `sim-2026.08-v36`,
   `og-participant-2026.08-v21`. The gate was red for exactly one reason and it is now green,
   **without restoring `deepdive.js` and without weakening the generator.**
3. **THE BEHAVIOUR DIGEST WAS RE-DERIVED, NOT ASSUMED**, which Run 54 could not do and said so.
   It comes back `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1` - the digest
   of record, unmoved across the v35-to-v36 supersession.
4. **FOUR STALE GUARDS, NOT TWO.** The order named two. A sweep found a third
   (`tests_render.html`) and RUNNING the injection campaign found a fourth
   (`run52_injection_campaign.py` fault 1, whose subject `deepdive.js` no longer exists). Reading
   the diff had not shown it.
5. **A PREMISE IN PHASE A WAS CHECKED AND IS TRUE, WITH ONE QUALIFICATION** that is reported
   rather than resolved silently: two of the six control names already existed on the detail page
   in different words. See section 2.

---

## 1. The tree at the start, and whether anything was dirty

| Claim | Verified by | Found |
|---|---|---|
| tree clean | `git status --porcelain` | **EMPTY.** No leaked fault. |
| branch | `git branch --show-current` | `run54-phases` |
| head | `git rev-parse HEAD` | `d5f42436a00a2b5790f4b47fa28e183308faaab0` |
| `main == origin/main` | `git rev-parse main origin/main` | both `bf36ef6b9f5b3111dc010f015ef5e6dd30a666c8` |
| interpreter | `python3 -V` | `Python 3.11.15` |

**Nothing was dirty.** Work was done from `run54-phases`, never from `main`.

---

## 2. PHASE A: where each of the six controls was placed

### 2.1 Placement, reported and not decided silently

**The host:** a `<div class="detail-admin-host" data-admin-for="<project id>">` inside
`.detail-head`, **immediately after the pre-existing `.detail-head-actions` cluster**, added at
`assets/js/detail.js`. Mounted by `wireDetailAdmin(root, p.id)`, called from `render()` beside
`wireBack` and `wireReset`.

**The panel:** built by `LinIngest.openInlineManage(id, host)` - **the same function, the same
markup, the same six handlers** that built it on the portfolio row. Measured in the browser:

```
host parent element class : detail-head
panel parent element class: detail-admin-host
control order in the panel : ['Save info', 'Upload documents', 'Recompute this project',
                             'Reset signals', 'Archive', 'Close']
pre-existing head actions  : ['Upload documents', 'Generate signals for every period',
                             'Clear stored signals for this project']
```

| # | Control | Selector | Panel | Order | Verified per control |
|---|---|---|---|---|---|
| 1 | Save info | `.pe-save` | `.pr-admin` in `.detail-admin-host` | 1st | renders exactly once on each of 3 detail pages |
| 2 | Upload documents | `.pe-populate` | same | 2nd | same, and opens the upload dialog naming that project |
| 3 | Recompute this project | `.pe-recompute` | same | 3rd | same |
| 4 | Reset signals | `.pe-reset` | same | 4th | same |
| 5 | Archive | `.pe-archive` | same | 5th | same |
| 6 | Close | `.pe-cancel` | same | 6th | same, and removes the panel |

### 2.2 THE MOVE IS A MOVE, NOT A REWRITE (section 11.1)

`openInlineManage` gained one optional parameter, `hostEl`. With it absent the portfolio-row
journey is what it always was - find the row, toggle, one open at a time. With it supplied the
box is appended to that element instead of to the row's `<li>`. **Every one of the six click
handlers is unchanged.** Measured against the pinned pre-move commit `d5f4243`:

```
Archive (.pe-archive): confirmation before the move = NONE;  after = NONE
  PASS  Archive: the handler body is BYTE-IDENTICAL to the pinned pre-move commit
Reset signals (.pe-reset): confirmation before the move = NONE;  after = NONE
  PASS  Reset signals: the handler body is BYTE-IDENTICAL to the pinned pre-move commit
```

**THE ONE DEVIATION, REPORTED AS ONE.** `box.querySelector(".pe-id").focus()` and
`box.scrollIntoView({block:"nearest"})` run for the row path and are skipped for the hosted path.
On the row the panel opened in response to a CLICK, so taking focus was right; on the detail page
it is mounted by `render()`, which runs on every navigation, and taking focus there would drag
the reader past the project heading every time. **No handler and no action changed.**

### 2.3 THE DESTRUCTIVE CONTROLS (section 6 item 5)

| Control | Confirmation BEFORE the move | Confirmation AFTER | Survived unchanged? |
|---|---|---|---|
| **Archive** | **NONE** - no `window.confirm`, no dialog | **NONE** | **YES**, and the handler is byte-identical |
| **Reset signals** | **NONE** | **NONE** | **YES**, and the handler is byte-identical |

Measured, not asserted: the handler bodies were extracted from `d5f4243`'s committed
`ingest.js` and from the live file and compared byte for byte. **Neither control carried a
confirmation before this run and this run did not add or remove one.** Reported for the owner's
attention: two destructive controls now sit on the page the owner works from and neither asks
before acting. Changing that is not ordered here and was not done.

### 2.4 What became of the accordion

**It is not deleted, and it is not empty.** `ingest.js` still builds one `.pr-admin` panel and it
is the SAME panel - it now has a different parent. What is gone is the portfolio-row MOUNT: the
row renders no `.pr-admin` at all, measured as `0` on every row of the one surface that hosts a
project list. The panel also still carries the four inputs it always carried - Project number /
code, Project name, Project type / sector (Design / Construction / Hybrid), Address - which
**Save info reads**; moving Save info without them would have changed what it does, which section
11.1 forbids, so they moved with it.

### 2.5 THE PREMISE CHECK (section 2, "premise checking")

The order's premise is that all six controls can move without changing what they do. **It holds**,
and the evidence is in 2.2. But one thing the order does not say, and the code does:

**TWO OF THE SIX NAMES ALREADY EXISTED ON THE DETAIL PAGE IN DIFFERENT WORDS.** Before this run,
`detail.js` already rendered `.detail-upload` labelled **"Upload documents"** (the same action:
both call `LinIngest.openUploadModal(id)`) and `.detail-reset` labelled **"Clear stored signals
for this project"** (the same underlying call, `LinStore.resetSignals(id)`, plus extra cache
clearing). Moving the panel intact therefore places a SECOND control labelled "Upload documents"
on the same page. **This was not resolved silently and it was not resolved by me.** Deleting
either pre-existing control would be removing a reachable control outside the six phase-A names,
which section 12.6 makes a run-level halt; renaming one would change rendered text. Both are
reported to the owner in section 11 as a decision.

### 2.6 The `.li-open` CSS

Four dead rules removed at `assets/css/radar.css` (formerly lines 643, 648, 3417, 3940), plus two
comment mentions of the selector reworded. **No `.li-open` selector survives**, measured; and
**NON-VACUITY at `d5f4243`: `radar.css` DID carry them**, measured, so the absence check is not
vacuous.

### 2.7 The browser session

Run 54's environment reused, not rediscovered. Chromium
`/opt/pw-browsers/chromium-1194/chrome-linux/chrome` by explicit `executable_path`;
`args=["--use-gl=swiftshader","--no-sandbox","--headless=new"]`; `python3 -u`; driver run from a
CLEAN SUBDIRECTORY with the cwd printed as the first line.

```
browser session cwd: .../scratchpad/run55drivers/phasea
repository root:     /home/user/LinPRojectRadar
in service:          63    registry: 101    retired: 38
  PASS  7 .page sections
  PASS  neither api.js nor boot.js in document.scripts
```

The DEng\Demo tell was measured: **7 `.page` sections, `api.js`/`boot.js` in `document.scripts`
= `[]`.** The application under test is the right one.

**`server/tools/drive_run55_admin_controls.py`. RESULT: 66 passed, 0 failed. Page errors: `[]`.**

---

## 3. PHASE B: the fifteen repairs, the runner, `arm()`, and `atexit`

### 3.1 All fifteen, each with its `finally` count after the repair

| # | Campaign | `finally` before | after |
|---|---|---|---|
| 1 | `drive_run26_faults.py` | 0 | 2 |
| 2 | `run26_fault_campaign.py` | 0 | 2 |
| 3 | `run27_fault_campaign.py` | 0 | 1 |
| 4 | `run31_full_fault_campaign.py` | 0 | 1 |
| 5 | `run31_pass2_targeted_faults.py` | 0 | 1 |
| 6 | `run31_synthetic_scope_faults.py` | 0 | 4 |
| 7 | `run32_b3_fault_campaign.py` | 0 | 1 |
| 8 | `run32_closure_fault_campaign.py` | 0 | 1 |
| 9 | `run32_fault_campaign.py` | 0 | 1 |
| 10 | `run32_qualifier_count_fault_campaign.py` | 0 | 1 |
| 11 | `run36_closure_fault_campaign.py` | 0 | 1 |
| 12 | `run36_fault_campaign.py` | 0 | 1 |
| 13 | `run38_fault_campaign.py` | 0 | 1 |
| 14 | `run39_fault_campaign.py` | 0 | 1 |
| 15 | `test_run41_fault_campaign.py` | 0 | 1 |

**23 of 23 now repaired** (Run 54 did 8). Each loop shape was read and repaired individually -
these are not one pattern applied fifteen times. `run31_synthetic_scope_faults.py` needed four
because it has four module-level faults across three different files. Every file was re-parsed
with `ast.parse` after editing.

### 3.2 `server/tests/` inside the runner, and the new count

`server/run_all_suites.sh` globbed `tools/test_*.py` only. It now globs
`tools/test_*.py tests/test_*.py`. Counted from the filesystem: **193 + 10 = 203.**

**THE TWO DIRECTORIES ARE NOT CONFLATED.** Every suite is keyed and reported by its FULL RELATIVE
PATH, and each gets a database named after that path (`tr '/' '_'`), so
`tools/test_run34_fault_campaign.py` and `tests/test_run34_fault_campaign.py` can never share a
db or a result line. `server/tools/test_run34_*` are stubs that write nothing; `server/tests/`
holds the real mutating campaigns - including `test_run34_fault_campaign.py`, which injects two
of the three guards Run 52 found neutered. **The campaign most implicated in the leak is now
inside the pass meant to catch it.**

**EVERY RECORD RECONCILED TO 203:**

| Record | Before | After | How |
|---|---|---|---|
| `run55_freeze_candidate_identity.json` -> `test_suite_identity.files` | 193 | **203** | derived from the runner's own glob, both directories |
| `run55_freeze_candidate_identity.json` -> `test_suite_identity.members` | 193 paths | **203 paths** | same |
| `run55_freeze_candidate_identity.json` -> `test_suite_identity.digest` | - | `fc3adab2f430db10...` | recomputed |
| `candidate_identity_digest` | - | `091d3fab7d8ca150591dacee9f5e53e8746368e5cce1f068bb98437cbbc1fd2d` | recomputed over all group digests |
| the v21 `Package(...)` prose and the supersession reason | - | states the 193 -> 203 move | written |
| `T6_HANDOFF.md`, new top section | - | states 203 | written |

The historical identity files (`run49`, `run51`, `run52`) still read 193 and are **deliberately
not rewritten**: each is the evidence for what was measured under that stamp. `T6_HANDOFF.md`
lines 223 and 274 are historical run entries and are left alone for the same reason.

### 3.3 `arm()`'s allow list, tightened to declared outputs (section 8 item 1)

Established **by execution over the files**, not by reading Run 54's note:

| Campaign | Allow BEFORE | Allow AFTER | Why |
|---|---|---|---|
| `test_run20_cycle12_fault_evidence.py` | 3 `code_audit/` entries | `[]` | **contains no write to `code_audit` at all** - all three were read-only inputs |
| `test_run36_fault_guards.py` | 2 `.sha256` entries | `[]` | same: no write op in the file |
| `test_run41_fault_campaign.py` | `run41_fault_campaign_results.csv` | `[]` | that artifact is written by `run41_fault_campaign.py`, **a different file** |
| `run39_fault_campaign.py` | `run39_pilot_browser_execution.csv` | `run39_fault_campaign_results.csv` | the old entry is a file it READS as an oracle and MUTATES as fault 17's target - not an output; **and the file it actually writes was not declared at all.** Both halves corrected. |

### 3.4 `atexit`, answered (section 8 item 2)

`grep -rn "atexit" server/tools/*.py server/tests/*.py server/app/**/*.py` returns **four lines,
all in `server/tools/campaign_safety.py`**, and all belong to one guard: `arm()`'s end check.

**IT DOES NOT RELY ON AN EXCEPTION TO FAIL THE PROCESS.** It prints and calls `os._exit(1)` -
precisely because Run 54 proved that an exception raised in a CPython `atexit` callback is
IGNORED and leaves the exit status at 0. **No other guard anywhere in the repository uses
`atexit`.** Nothing to repair.

---

## 4. PHASE C: each guard's assertion before and after, with its injection

Every injection ran inside `run52_injection_campaign.py`'s protocol: the tree checked before and
after, the snapshot taken from the **committed bytes at HEAD** (converted in this run - it had
snapshotted from disk), restore inside a `finally`, and **the baseline rechecked after every
injection**.

```
  TREE CLEAN (start): run52_injection_campaign.py
  ...
  RESULT: 31/31 checks passed
  TREE CLEAN (end): run52_injection_campaign.py
```

### 4.1 `test_run28_participant_packages.py:1262-1267`

**BEFORE:** `assets/js/app.js` is BYTE-IDENTICAL to v19, **and** both row controls (`li-manage`
and `li-open`) render. That was the record of Run 52's stop under its section 8.1.

**AFTER**, keeping every property still true and dropping only the two facts the ruling reversed:
- **NON-VACUITY, pinned to the explicit commit `V19_COMMIT`**: app.js DID render both at v19.
- **AT `d236a270` (v20) app.js WAS still byte-identical to v19** - Run 52's stop was real and
  stays on the record.
- the project list no longer renders Open;
- Manage is still rendered on every row;
- **`.li-manage").addEventListener("click", () => openDetail(` is present** - Manage carries the
  route the removed Open used to carry, so no detail page became unreachable;
- app.js differing from v19 is the DECLARED v21 change, not a defect.

**INJECTION (fault 4, revised): PUT OPEN BACK.**
```
FAULT 4: the Open control is PUT BACK into the project list...
  PASS  INJECTION LANDED in assets/js/app.js, confirmed by re-reading the bytes from disk
  PASS  test_run28_participant_packages.py goes RED with the fault in place
  PASS  and it goes red FOR THE INTENDED REASON, not incidentally
  PASS  RESTORED: assets/js/app.js is byte-identical to its pre-injection snapshot
  PASS  BASELINE RECHECKED after fault 4: test_run28_participant_packages.py is green again
```

### 4.2 `run52_injection_campaign.py` fault 4

**BEFORE:** it REMOVED Open and required the package suite to go red - proving Run 52's stop was
enforced and not merely written down. Run 54 carried the removal, so **the anchor no longer
existed**: the fault could not apply, and a fault that cannot apply proves nothing.

**AFTER:** the exact inverse, as quoted above.

### 4.3 FOUND BY SWEEP: `tests_render.html` row-actions group

**BEFORE:** `exactly one Open control` = 1; the Open control is labelled `Open ->`; the cluster is
`Manage|Open ->` in that order.

**AFTER:** no Open control renders; exactly one Manage control; it is labelled `Manage`; it
carries the row's own project id so the row still reaches that project's detail page; the cluster
is `Manage`. **The "no control anywhere in the cluster says Signals, whatever class it carries"
check is untouched.**

### 4.4 FOUND BY RUNNING THE CAMPAIGN: fault 1

**This one reading the diff did not show.** Fault 1 put the dead see-Health button back into
`assets/js/deepdive.js`. That file was deleted by Run 54 phase B, so
`head_bytes(ROOT, "assets/js/deepdive.js")` raised and **the campaign died at its first
injection**.

The guarantee has not gone away; it has become STRICTER, from *"the button renders nowhere"* to
*"the file renders nowhere because it does not exist"*. So the fault is revised to the inverse:
**it PUTS THE FILE BACK.** `fault()` gains an `absent` branch - when the target does not exist at
HEAD the fault CREATES it and the `finally` DELETES it again; everything else is unchanged.

```
FAULT 1: ... THE FILE IS PUT BACK. The v21 package guard must go red...
  PASS  NON-VACUITY: assets/js/deepdive.js really is absent before this fault
  PASS  INJECTION LANDED in assets/js/deepdive.js, confirmed by re-reading the bytes from disk
  PASS  test_run28_participant_packages.py goes RED with the fault in place
  PASS  and it goes red FOR THE INTENDED REASON, not incidentally
  PASS  RESTORED: assets/js/deepdive.js is absent again, as it is at HEAD
```

### 4.5 The sweep (section 9 item 4), uncapped

`grep -rn "li-open\|Open ->\|data-open\|openInlineManage"` over `*.py`, `*.html`, `*.js`, `*.md`,
**not capped**, excluding only `REPORT_*`. Every hit classified:

| Site | Verdict |
|---|---|
| `test_run28_participant_packages.py` | **REVISED** (4.1) |
| `run52_injection_campaign.py` faults 1 and 4 | **REVISED** (4.2, 4.4) |
| `tests_render.html` | **REVISED** (4.3) |
| `drive_run52_premise.py`, `drive_run52_browser.py` | **NOT TOUCHED.** Evidence capture pinned to the runs they served, exactly as Run 54 stopped on the same class. Rewriting them would falsify the record of what Run 52 measured. |
| `drive_run54_navigation.py` | Run 54's own driver; its absence branch already measures the post-removal state and passes. Not touched. |
| `assets/js/app.js:1106,1116`, `T6_HANDOFF.md:71,110` | comments and history describing the change. Not guards. |
| `assets/js/workspace.js:762`, `assets/js/assistant.js:361` | a DOCUMENT "Open" button and unrelated prose. Out of scope, untouched. |

**No guard asserting the pre-Run-54 state survives.**

### 4.6 The guard proved its own value twice, unprompted

The campaign **REFUSED TO BEGIN** on four untracked mint artifacts
(`?? research/freeze/run55_freeze_candidate_identity.json` named as leak-class dirt), and again
when it could not take a snapshot from HEAD. Both refusals are correct. This is Run 54's phase-A
guard doing exactly what it was built for, on a real session.

---

## 5. PHASE D: the mint

### 5.1 Every piece

| # | Piece | Value |
|---|---|---|
| 1 | `sim-2026.08-v36` | `models.py`; `SIMULATION_VERSION_SUPERSEDED` -> `sim-2026.08-v35`; history appended, never edited (36 entries) |
| 2 | `og-participant-2026.08-v21` | appended to `PARTICIPANT_PACKAGES`; `CURRENT` |
| 3 | The v21 checksum record | `code_audit/run55_participant_package_v21_checksums.sha256`, **69 members** (70 minus the one deletion), with the named exception record in its header |
| 4 | Production-tree re-take | `code_audit/run55_production_tree.sha256`, **242 files**, manifest sha256 `92e2f95960333defdacf76d50f6997fd6a1951d74f91afbc1c6ceadb1187604b` |
| 5 | Authority-tree re-take | **RE-TAKEN AND DELIBERATELY NOT SUPERSEDED.** `compare()` over `AUTHORITY_ROOTS`: added=0 removed=0 changed=0 renamed=0, and the recomputed sha256 `b52c47a68a20ab1629681ea240abdea2167c67f289d181f446a8170704dc1596` is byte for byte the pinned file's. A manifest is superseded when what it describes moves, not once per run. |
| 6 | `run55_freeze_candidate_identity.json` | identity digest `091d3fab7d8ca150591dacee9f5e53e8746368e5cce1f068bb98437cbbc1fd2d`, candidate `c2fc689` |
| 7 | The v21 `Package(...)` prose | covers Run 54's three phases and this run's three, one file at a time |
| + | `run55_successor_freeze_gate.csv` | 15 blockers, 0 blocked |
| + | `run55_candidate_behaviour_digest.json` | `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1` |
| + | `RUN55_SUCCESSOR_FREEZE_{RECORD.json,REPORT.md,CHECKSUMS.csv}` | `FINAL_FREEZE_ACCEPTED`, release content digest `6cd87f8655a614b9df68f9290582724e698e277acd7eaf8d9f4d871f8b450a4c`, 106 rows |

### 5.2 The candidate identity, group by group

```
registry_digest                       2 files  668d23c00a325cee
taxonomy_authority_digest             4 files  f5c03a7e3f6d59b3
qualification_authority_digest        5 files  76d61886845bc8ce
participant_protocol_digest           8 files  b5a05f98344f226a   <- was 9
controlled_stimuli_digest             2 files  56ac9665332fbb19
simulation_authority_digest          40 files  b17c315eed609793
test_suite_identity                 203 files  fc3adab2f430db10   <- was 193
browser_suite_identity                2 files  ad3aa92e703d0f07
final_lock_guard_digest               1 files  cfd6fb3bc25ef538
evidence_provenance_digest            2 files  b5c29e0a44c0c75e
service_roster_digest                 1 files  8fed04ffb3ed0338
candidate_identity_digest  091d3fab7d8ca150591dacee9f5e53e8746368e5cce1f068bb98437cbbc1fd2d
```

### 5.3 THE NAMED EXCEPTION RECORD for a sequence-bearing DELETION (section 10 item 3)

`assets/js/deepdive.js` is the **first link in this chain whose sequence-bearing delta is a
DELETION** - it moves the SET, not a member of it. The record is carried in four places, none of
them a widened comparison:

1. `participant_packages.V20_TO_V21_DELETED` (2 entries) and `V20_TO_V21_SEQUENCE_EXCEPTION`
   (1 entry).
2. `SEQUENCE_BEARING_FILES` keeps **six** and is NOT shortened;
   `SEQUENCE_BEARING_FILES_FROM_V21` has **five**. Asserted by execution that the difference
   between them is EXACTLY the named exception.
3. The v21 checksum record's own header, a named paragraph headed
   `assets/js/deepdive.js -- SEQUENCE-BEARING`, with the reason, the route evidence, and the
   non-vacuity sha256 `afc1e2ef...` matching line 81 of the v20 record.
4. `V20_TO_V21_CHANGED` - the five files whose bytes moved - **deliberately does NOT contain
   deepdive.js**: it did not change, it ceased to exist, and conflating the two would make the
   record unreadable.

**v20 -> v21 measured, not assumed:** 1 deleted, 5 changed
(`assets/css/radar.css`, `assets/js/app.js`, `assets/js/detail.js`, `assets/js/ingest.js`,
`index.html`), 0 added. **No surviving sequence-bearing file moved.**

### 5.4 FOUR RECONCILIATIONS, EVERY ONE A NARROWING RATHER THAN A WEAKENING

**Section 12.9 was live throughout: `deepdive.js` was NOT restored and the generator was NOT
weakened.**

| # | What was red | The reconciliation | Why it is not a weakening |
|---|---|---|---|
| 1 | The identity builder raised `SystemExit` on any vanished pinned member | narrowed by a DECLARED deletion list read from `PP.V20_TO_V21_DELETED` | an UNDECLARED disappearance still raises; a declaration for a file that is **still present** raises; a declaration for a file that did **not exist at the explicit commit `bf36ef6`** raises. The declaration can record a deletion; it cannot cause one. |
| 2 | **B04**, `FileNotFoundError` on the six-member sequence-bearing set | from v21 the set is five, and three things are asserted BEFORE the shorter set is used, each counting into the blocker | the difference between the sets must be EXACTLY the exception; every excepted file must be genuinely absent; every excepted file must be declared. **A SECOND sequence-bearing file disappearing still turns B04 red.** |
| 3 | **B15** would have been silently turned VACUOUS by a rename | the generator used ONE constant to read the prior digest and write the new one. Renaming it to the successor's filename would have made B15 read a non-existent file, take the "first evaluation" branch and PASS WITHOUT COMPARING ANYTHING. Read and write are now separate constants. | **STRICTER than before**: B15 now compares the freshly derived digest against the **v35** record, spanning a supersession, instead of comparing a run to itself. |
| 4 | **B11**, `rewritten predecessor package records: ['og-participant-2026.08-v20']` | v20's record described the LIVE TREE while v20 was current; now that v21 exists it is pinned to `d236a270` | verified: `git show d236a270:<record>` is byte-identical to the file on disk, and `models.py` at that commit still reads `sim-2026.08-v35`. Exactly one record in the chain reads the working tree, and the suite asserts it. |

`test_run28_participant_packages.py`'s v19-to-v20 comparisons were moved off the working tree and
onto `d236a270`, the commit whose blobs the v20 record describes - **a superseded record is
evidence about a commit, not about today's tree.** Every check it made still runs, against the
same bytes, and is now immune to any later change. The `not (ROOT / rel).is_file()` clause in the
v18 and v19 blocks was **replaced, not dropped**, by the same declared-deletion narrowing.
**Suite result: 271/271.**

### 5.5 HOW MANY MINTS WERE PAID, AND WHAT SURFACED ON EACH

**THREE.**

| Mint | What surfaced |
|---|---|
| **1** (dry run, `--out-audit`/`--out-freeze` to a scratch dir) | **`FileNotFoundError` moved but did not go away.** Fixing the identity's `participant_protocol_digest` exposed a SECOND crash site the identity had been masking: **B04 at line 506**, hashing the six-member sequence-bearing set. Reconciliation 2. Then, with the generator finally running end to end, **B11 went BLOCKED**: `rewritten predecessor package records: ['og-participant-2026.08-v20']`. Reconciliation 4. |
| **2** (committed artifacts, pre-commit tree) | **Gate clean, 15 blockers, 0 blocked; freeze gate suite 34/34.** The behaviour digest re-derived to `8fb4d366...` for the first time. |
| **3** (after the phase-D commit) | **`candidate_commit_verified_is_head` did its job.** A candidate identity is a statement about a COMMIT and cannot be finished before that commit exists: the identity named the phase-C tip and `CANDIDATE` in the generator still named Run 52's commit. Both re-taken against `c2fc689`. Gate clean again, 34/34 again, digest `8fb4d366...` again. |

Run 51 paid four and Run 52 three. **This run paid three.**

### 5.6 EVERY GATE ROW, WITH ITS VERDICT, FROM LIVE OUTPUT

`server/tools/test_run37_freeze_gate.py` on the committed tree. **RESULT: 34/34 checks passed.**

| # | Gate row | Verdict |
|---|---|---|
| 1 | `run37.gate.generator_runs` - the acceptance generator runs to completion; a crash is a blocker, not a pass | **PASS** |
| 2 | `run37.gate.artifact_present` - the committed freeze gate exists | **PASS** |
| 3 | `run37.gate.reproduces` - and it REPRODUCES from the current tree, so it is not a stale snapshot | **PASS** |
| 4 | `run37.gate.fifteen_blocker_classes` - all fifteen blocker classes are evaluated | **PASS** |
| 5 | `run37.gate.B01` - dirty candidate identity is zero | **PASS** |
| 6 | `run37.gate.B02` - population mismatch is zero | **PASS** |
| 7 | `run37.gate.B03` - controlled-stimulus mismatch is zero | **PASS** |
| 8 | `run37.gate.B04` - participant-sequence drift is zero | **PASS** |
| 9 | `run37.gate.B05` - false defensibility statement is zero | **PASS** |
| 10 | `run37.gate.B06` - unexpected execution exception is zero | **PASS** |
| 11 | `run37.gate.B07` - Category-9 bypass is zero | **PASS** |
| 12 | `run37.gate.B08` - Category-10 authority violation is zero | **PASS** |
| 13 | `run37.gate.B09` - voting count is not exactly 2 is zero | **PASS** |
| 14 | `run37.gate.B10` - current taxonomy dual authority is zero | **PASS** |
| 15 | `run37.gate.B11` - package or predecessor mutation is zero | **PASS** |
| 16 | `run37.gate.B12` - browser qualification failure is zero | **PASS** |
| 17 | `run37.gate.B13` - unresolved blocking Run-36 defect is zero | **PASS** |
| 18 | `run37.gate.B14` - unsupported final empirical-validation claim is zero | **PASS** |
| 19 | `run37.gate.B15` - candidate behaviour changed during the run is zero | **PASS** |
| 20 | `run37.gate.blocking_defects_zero` - BLOCKING DEFECTS = 0 | **PASS** |
| 21 | `run37.gate.predecessor_release_preserved` (v25) | **PASS** |
| 22 | `run37.gate.immediate_predecessor_release_preserved` (v26) | **PASS** |
| 23 | `run37.gate.immediate_predecessor_release_preserved` (v27) | **PASS** |
| 24 | `run37.gate.immediate_predecessor_release_preserved` (v28) | **PASS** |
| 25 | `run37.gate.immediate_predecessor_release_preserved` (v30) | **PASS** |
| 26 | `run37.gate.immediate_predecessor_release_preserved` (v31) | **PASS** |
| 27 | `run37.gate.no_release_while_blocked` | **PASS** |
| 28 | `run37.gate.release_present_when_clean` | **PASS** |
| 29 | `run37.gate.limitation_stated` - empirical field validation is stated as 0 of 100 | **PASS** |
| 30 | `run37.gate.limitation_stated` - no validated real-world predictive claim | **PASS** |
| 31 | `run37.gate.limitation_stated` - OG-SYNTH-0.1 historical incompleteness | **PASS** |
| 32 | `run37.gate.limitation_stated` - bounded controlled-study instrument use | **PASS** |
| 33 | `run37.gate.disposition` - FINAL_FREEZE_ACCEPTED and the gate agrees | **PASS** |
| 34 | `run37.gate.no_self_reference` - no self-referential placeholder | **PASS** |

**Rows 2 and 3, which were Run 54's two failures, are the two this run existed to turn green.**

---

## 6. Every item stopped under section 11, with its reason

| # | Item | Condition | Reason |
|---|---|---|---|
| 1 | **Removing or renaming the detail page's PRE-EXISTING "Upload documents" (`.detail-upload`) and "Clear stored signals for this project" (`.detail-reset`)** | **11.1 / 12.6** | Two of the six control names already existed on the detail page in different words, doing the same underlying thing. Moving the panel intact therefore places a second control labelled "Upload documents" on the page. Deleting either pre-existing control would remove a reachable control outside the six phase-A names, which section 12.6 makes a **run-level halt**; renaming one would change rendered text. **Put to the owner in section 11 as a decision rather than resolved by me.** |
| 2 | **Adding a confirmation to Archive and to Reset signals** | 11.1 | Neither carried one before the move. Adding one would change what the control does, and moving is not rewriting. Reported in 2.3 for the owner's attention. |
| 3 | **Rewriting `drive_run52_premise.py` and `drive_run52_browser.py`** | 11.3 | Evidence capture pinned to the runs they served. Rewriting them would falsify the record of what Run 52 measured. Run 54 stopped on the same class for the same reason. |
| 4 | **Writing a `run55_authority_tree.sha256`** | premise contradicted by execution | The authority tree did not move: added=0 removed=0 changed=0 renamed=0, manifest sha256 identical. Writing a successor manifest would assert a supersession that did not happen. Re-taken and reported, not superseded. |
| 5 | **Rewriting the historical `run49`/`run51`/`run52` identity files to read 203** | 11.3 | Each is the evidence for what was measured under that stamp. 193 was true then. |

**No item was stopped because it was hard. Each of the five is a stop the code or the order
required.**

---

## 7. Every item UNSTARTED FOR BUDGET, named as unstarted and not as stopped

1. **The `snapshot_from HEAD` conversion for the remaining campaigns.** Run 54 converted two;
   this run converted a third (`run52_injection_campaign.py`, because it had to run it). The
   others are unstarted. All 39 are armed, so a leak from any is caught at the start of the next
   campaign, which section 6 of the Run 54 order calls the fix.
2. **A browser re-verification of the six controls after phases B, C and D.** Phase A's driver
   ran on the phase-A tree and passed 66/66; the later phases moved no client byte that the
   panel depends on (`git diff --stat 4a5f501..HEAD -- assets/` is empty), but a second browser
   pass was not run and is not claimed.

**Nothing else was left unstarted.** All four phases were completed.

---

## 8. Every section-13 guarantee, verified or not met, each with its injection

| # | Guarantee | Verdict | Evidence |
|---|---|---|---|
| 1 | Each of the six controls renders on the detail page, acts on that project, verified in a browser | **MET** | `drive_run55_admin_controls.py`, **66/66**, three projects, one surface. Per control: `renders exactly once`; per project: `the panel's project-number field reads back <id>`. |
| 2 | The controls existed before the move, pinned to an explicit commit | **MET** | Six `NON-VACUITY at d5f4243` lines, one per control, plus `the builder took ONE argument, so the panel could only ever be appended to a portfolio row`. |
| 3 | Archive and Reset signals carry the confirmation they carried before | **MET** | Both carried **NONE** before and carry **NONE** after; handler bodies **byte-identical** to `d5f4243`. |
| 4 | No `.li-open` rule survives | **MET** | `no .li-open selector remains in radar.css`, with `NON-VACUITY at d5f4243: radar.css DID carry .li-open rules`. |
| 5 | All 23 campaigns restore inside a `finally`, or are stopped with reasons | **MET** | 8 by Run 54, **15 by this run**, table at 3.1. 23 of 23. |
| 6 | `server/tests/` runs in the pass, and the new count is reconciled everywhere | **MET** | `Suites run: 203`; the ten `tests/…` suites appear in the pass log and every one is green. Reconciliation table at 3.2. |
| 7 | The revised guards assert the current state and can still fail, each proved by injection | **MET** | `run52_injection_campaign.py` **31/31**, tree clean at start and end. Faults 1 and 4 quoted in section 4. |
| 8 | No guard asserting the pre-Run-54 state survives | **MET** | Uncapped sweep, table at 4.5. Four revised, the rest classified. |
| 9 | `build_run37_acceptance.py` reproduces from the live tree | **MET** | `run37.gate.generator_runs` **PASS** and `run37.gate.reproduces` **PASS** - the two rows Run 54 could not turn green. |
| 10 | The behaviour digest is **RE-DERIVED**, not assumed | **MET** | Derived four times over all 100 scientific targets: `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1`. **Run 54 could not do this and said so; this run did it.** |
| 11 | No stored figure changes | **MET** | No compute path, model, parameter, band, threshold, calibration, abstention rule, migration or corpus was touched. `git diff bf36ef6..HEAD -- server/app/` is `main.py` (route table) and `models.py` (stamp only). B15 zero is the executed proof. |
| 12 | Modules in service 63, registry total 101, both derived | **MET** | `in service: 63    registry: 101    retired: 38`, printed live by the phase-A driver from `service_index()` / `registry_index()`. |
| 13 | Voting count is exactly 2, `A1.7` and `A1.8` | **MET** | Gate **B09 PASS**: `CORE_VOTING_MODULES = ['A1.7','A1.8']`, read live. |
| 14 | Every runtime lookup across all 101 registered modules resolves, asserted live | **MET** | Gate **B10 PASS**: `runtime lookups failing across all 101 registered modules: none`, over `method_label`, `group_of`, `parameter_provenance`, `activation_state`. |
| 15 | No rendered identifier changed | **MET** | The only `assets/` and `index.html` deltas in this run are phase A's, and `index.html` did not move at all in Run 55. No naming sweep was run. |
| 16 | No em dash or en dash renders in user-facing text | **MET, by the existing sweep, not by a new one** | `run51_dash_sweep.py` is byte-identical to `bf36ef6` (Run 54 proved that and this run did not touch it). No user-facing text was added by this run: phase A added markup and comments only. |
| 17 | The successor freeze gate passes in full | **MET** | **34/34**, every row in 5.6. |
| + | Every sequence-bearing file that moved has a named exception record; one moving without a record still turns the gate red, **proved by injection** | **MET** - and this is the proof Run 54 could not perform | `run52_injection_campaign.py` fault 6 deletes the exception record while the file still moved: `test_run28_participant_packages.py goes RED with the fault in place`, `and it goes red FOR THE INTENDED REASON`. Fault 1 proves the deletion record the same way. |

**THE FULL SUITE PASS, MEASURED:** **203 suites, 15232/15262 checks, 13 red**, and **not one
suite left production or client source dirty.** Twelve of the thirteen were reconciled and
committed; the thirteenth was `test_run37_freeze_gate` red on a dirty tree, which section 10.1
says clears on a pass taken after the commit, and it did: **34/34.**

---

## 9. Which audit artifacts the suites rewrote, and were restored

The complete pass left **26** modified - **the same figure Run 52 recorded and the same figure
Run 54 recorded.** Named in full, not abbreviated:

```
code_audit/run10_dsm_known_answers.csv              code_audit/run10_dsm_recomputation.csv
code_audit/run10_module_identity.csv                code_audit/run10_monte_carlo_convergence.csv
code_audit/run10_monte_carlo_distribution_gap.csv   code_audit/run10_monte_carlo_known_answers.csv
code_audit/run10_monte_carlo_recomputation.csv      code_audit/run10_no_operational_effect.csv
code_audit/run10_validator_fault_injection.csv      code_audit/run20_cycle12_100_reaudit.csv
code_audit/run20_cycle12_guard_nonvacuity.csv       code_audit/run20_cycle12_lineage_campaign.csv
code_audit/run21_guard_nonvacuity_results.csv       code_audit/run30_cat7_operational_execution.csv
code_audit/run38_controlled_stimulus_execution_order.csv
code_audit/run38_lock_integrity.csv                 code_audit/run38_participant_state_machine.csv
code_audit/run39_launch_identity.csv                code_audit/run8_expectation_mutation_proof.csv
code_audit/run9_abstention_results.csv              code_audit/run9_alias_overlay_verification.csv
code_audit/run9_fixture_import_results.csv          code_audit/run9_known_answer_results.csv
code_audit/run9_no_operational_effect.csv           code_audit/run9_validator_gap_recomputations.csv
server/tools/run17/coverage.csv
```

**ALL RESTORED. NONE COMMITTED.** `git checkout -- code_audit server/tools/run17`, verified by
`git status --porcelain` immediately after. A single later diagnostic run of
`test_run39_launch_gate.py` rewrote `code_audit/run39_launch_identity.csv` once more and it was
restored the same way. **`build_run37_acceptance.py` was run with `--out-audit <scratch dir>` on
every one of its four invocations**, as ordered, so it wrote no repository audit artifact.

---

## 10. Incidental findings, unacted

1. **`test_run2_fifteen_defects.py` scores 147/147 STANDING ALONE and 259/259 IN THE RUNNER** -
   two different TOTALS, not two different outcomes. Its check population depends on the database
   it is handed, so a standalone run does not exercise the same set. Same class as Run 54's note
   about `test_run33_ph1_fault_campaign`. **Reported, not explained.**
2. **The detail page now carries two controls labelled "Upload documents"** and two that clear
   stored signals. See 2.5 and section 11 item 1.
3. **Two destructive controls now sit on the page the owner works from and neither asks before
   acting.** Archive and Reset signals carried no confirmation on the row either; the move did
   not change that, but it did change how easily they are reached.
4. **The campaign guard refused to begin twice during this run, both times correctly** - once on
   four untracked mint artifacts under `research/freeze/`, once on a snapshot it could not take
   from HEAD. Working sessions that hold uncommitted freeze artifacts cannot run an armed
   campaign at all. That is the guard behaving as designed and it is also friction worth knowing
   about.
5. **`isolation_forest.py` did not reproduce as dirty in either of this run's full passes.**
   Run 54 saw it flagged four times and called it not determinable. Two clean passes here are not
   proof of absence and it is not claimed as resolved - **still not determinable.**
6. **`build_run37_acceptance.py`'s `CANDIDATE` constant must be edited by hand after each commit
   it describes.** Three of this run's four mints existed only to chase that. It is a fixed-point
   problem every run since 41 has paid; nothing here fixes it.

---

## 11. What the next session needs, stated as a decision for the owner

1. **THE DETAIL PAGE NOW HAS TWO "Upload documents" CONTROLS.** The pre-existing
   `.detail-upload` and the moved `.pe-populate` call the same function with the same argument.
   The pre-existing `.detail-reset` ("Clear stored signals for this project") and the moved
   `.pe-reset` ("Reset signals") both call `LinStore.resetSignals(id)`, the second with extra
   cache clearing. **Decision: remove one of each pair (and which), relabel one of each pair, or
   leave both?** Removing one is removing a reachable control, which is a run-level halt without
   an explicit instruction, so this run left both and said so.
2. **ARCHIVE AND RESET SIGNALS ASK NOTHING BEFORE ACTING**, and they now sit on the page the
   owner works from every day. They were the same on the portfolio row. **Decision: give either
   or both a confirmation?** Adding one changes what the control does, so it was not done here.
3. **THE CAMPAIGN GUARD'S TWO LEVELS** (Run 54's section 2.3) still depart from the literal
   wording, and this run met the strict behaviour twice. **Decision: keep the two levels with
   `CAMPAIGN_SAFETY_STRICT=1` for freeze runs, or make any dirt a refusal?** Unchanged and still
   open.
4. **THE SUITE POPULATION IS NOW 203 AND EVERY GATE RECORD SAYS SO.** The ten `server/tests/`
   suites are all green. **Decision: none needed - stated so the figure is not re-derived as a
   discrepancy next run.**
5. **`main` IS STILL AT `bf36ef6` UNTIL THE MERGE BELOW.** See the merge section.

---

## Carry-forward items, unacted

1. **CPI 1.22 on the site render.** Needs read access to PRJ-001's stored rows, which no session
   may have. The open question is which document type wrote `pv`.
2. **The `historical_data` triple**, Run 47's only unimplemented relation.
3. **`signal_inputs.sources` records no source field name.**
4. **Four status comparisons remain case-sensitive**, two in `decision.js`.
5. **Two Run 45 census artifacts do not match the v30 release manifest.**
6. **`test_run47_evm_consistency.py` swallows its own traceback.** Related in kind to the leak: a
   campaign that cannot fail visibly certifies its own corruption.
7. **Run 47's handoff entry is at the bottom of `T6_HANDOFF.md`.** Left there.
8. **`REG.method_label(m)` returns `None` for 96 of 101 registered modules.**
9. **`new_id` and `old_id` stay.** Not a naming survivor.
10. **`isolation_forest.py` was reported dirty four times in Run 54's baseline pass** and did not
    reproduce standalone. **Not determinable.** It did not reproduce in either of this run's two
    full passes either; that is not proof and it is still on watch.
11. **`test_run33_ph1_fault_campaign.py` scores 36/46 in the runner and 46/46 standing alone.**
    Order- or dirt-dependent, pre-existing. It was green in both of this run's passes, which does
    not resolve it.

---

## THE CONFIRMING FULL PASS, AND THE MERGE

### The second full pass, taken on the committed tree

```
====================================================
Suites run: 203   Total checks: 15269/15269
ALL SUITES GREEN
```

**203 suites. 15269 of 15269 checks. ZERO RED. No suite left production or client source dirty.**

The ten `server/tests/` suites, inside the pass for the first time, are all green, including
`tests/test_run34_fault_campaign.py 86/86` - the campaign that injects two of the three guards
Run 52 found neutered, now running inside the pass meant to catch it. And
`tests/test_run33_ph1_fault_campaign.py` scored **46/46 in the runner**, which is the figure it
has only ever produced standing alone; that does not resolve carry-forward item 11 and is not
claimed to.

The freeze gate was re-run once more on the final committed tree after the audit artifacts were
restored: **34/34.**

### No section-12 run-level condition fired

| # | Condition | Status |
|---|---|---|
| 1 | The behaviour digest moves from `8fb4d366…` | **DID NOT FIRE.** Re-derived four times; identical each time. |
| 2 | Any stored figure changes | **DID NOT FIRE.** No compute path, model, parameter, band, threshold, calibration, abstention rule, migration or corpus touched. B15 zero. |
| 3 | A runtime lookup fails for any of the 101 registered modules | **DID NOT FIRE.** B10: `runtime lookups failing across all 101 registered modules: none`. |
| 4 | A check must be deleted | **DID NOT FIRE.** Four guards revised, none deleted; where a check's subject ceased to exist it was REPLACED by a stricter one. |
| 5 | A gate row fails for a reason other than a manifest this run's edits falsified | **DID NOT FIRE.** Every red was a manifest this run's own edits falsified, and every one is reconciled. |
| 6 | A reachable control other than the six phase-A names would be added, moved or removed | **DID NOT FIRE.** Only the six moved. The duplication at 2.5 is a consequence of moving two of the six onto a page that already had equivalents, not a new control, and removing either pre-existing one was STOPPED for exactly this reason. |
| 7 | A rendered identifier would change | **DID NOT FIRE.** No naming sweep run; no identifier stripped or restored. |
| 8 | Any project's detail page becomes unreachable | **DID NOT FIRE.** Manage reaches every row's own detail page, measured in a browser on three projects. |
| 9 | Reconciling the generator would require restoring `deepdive.js` or weakening it | **DID NOT FIRE.** The file is still deleted; every reconciliation is a narrowing, and B15 is strictly stronger than it was. |

### THE MERGE

**The gate is known and clean: 34/34, from live output, on the committed tree, with a full
203-suite pass at 15269/15269 behind it.** The merge rule is therefore satisfied and
`run54-phases` was merged to `main` with `--no-ff`.

**This merges Run 54's four phases, which Run 54 was right not to merge, together with Run 55's
four. Eight phases of work reach `main` on one clean gate.**

---

## Closing statement of honesty

The run reached what it existed for. Four phases were ordered, four were completed, each was
committed before the next began, and the mint was paid.

**Four things are weaker than they could be read as, and are stated so deliberately.**

The phase-A move places a SECOND control labelled "Upload documents" on the detail page, because
two of the six names already existed there in different words. That is a real consequence of
obeying the ruling literally, it is not tidy, and removing either pre-existing control would have
been a run-level halt. **It is put to the owner rather than resolved by me.** Archive and Reset
signals still ask nothing before acting. The browser verification of the six controls was taken
on the phase-A tree and not re-taken after phases B, C and D - `git diff --stat` shows no client
byte moved after phase A, but a second browser pass was not run and is not claimed. And
`test_run2_fifteen_defects` produces two different check TOTALS depending on the database it is
handed; that is reported, not explained.

**Three things are stronger than the order asked for.** The order named two stale guards; a
sweep found a third and RUNNING the injection campaign found a fourth, which reading the diff had
not shown. The behaviour digest was **re-derived**, four separate times, which Run 54 could not
do. And the injection proof Run 54 recorded as "not performed" - that a sequence-bearing file
moving without its named record still turns the gate red - **was performed**, twice, once for an
edit and once for a deletion.

**The campaign guard Run 54 built refused to begin twice during this run, both times correctly,
on this session's own uncommitted work.** A guard that only ever fires on other people's mistakes
has not been tested.
