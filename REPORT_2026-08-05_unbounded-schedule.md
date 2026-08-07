# The schedule read at any size, truncation named, the upload record, and every period computed

**Date:** 2026-08-05
**Branch:** `claude/unbounded-schedule-s5s90m`, from `origin/main` at `4e3d44e`, merged to `main` as `1eb5d07` via PR #224
**Model:** Opus

**Verification:** server suite **45 suites, 2471/2471** (fresh migrated SQLite per test file; the new `test_unbounded_schedule.py` adds 87). `tests.html` **51/51**. `tests_render.html` **184/185**, 15 checks added here, the one red being the pre-existing auth-gated "production read path" check that is red on `origin/main` too. Seven server faults and two render faults injected, each confirmed applied by SHA-256 before its run, each detected, each reverted with a SHA-256 comparison and the baseline re-run green.

**Migrations unapplied in production: 0020 (`abstained_modules`), 0021 (`schedule_activities`) and 0022 (`upload_attempts`, added here).** No `DATABASE_URL` pointed anywhere but throwaway SQLite. Production was neither inspected nor queried.

**Nothing under `server/app/simulation/` was modified.** No module's arithmetic changed. Nothing recomputes in the browser.

---

## LEAD: the largest table tested, and what it cost

**A 500-activity, 11-column table. One model call, and the model was sent 900 characters of document text.** The same document with 29 activities: one model call, 899 characters. **The one-character difference is a digit of the row count.**

| | 29 activities | 500 activities |
|---|---|---|
| model calls | **1** | **1** |
| document text sent to the model | **899 characters** | **900 characters** |
| prompt | byte-identical to the 500-row prompt | byte-identical to the 29-row prompt |
| activity rows sent to the model | **0** | **0** |
| activity rows asked back from the model | **0** | **0** |
| rows reaching the per-activity store | 29 | 500 |

### The scaling is structural, and was verified independently

The rows are replaced by the table's header row plus a note stating the count. Measuring that note directly against the shipped `ActivityTable.elision_note()`:

| data rows | elision note |
|---|---|
| 29 | 352 characters |
| 500 | 353 characters |
| 5,000 | 354 characters |

**The note grows only by the decimal digits of the row count.** That is why no table size can ever truncate this path again: the only part of the model's input that varies with the number of activities is the number itself.

### On the real document

Measured against the owner-supplied file directly:

- The document renders to **4,703 characters** of text with the activity table intact. That is the input that truncated three times.
- With the table elided, `docx_to_text` returns **1,262 characters** — a reduction of **3,441 characters**, which is the activity table.
- The activity table is found at body index 1: **29 data rows**, 11 source columns, **6 resolved** to stored fields.
- The note that stands in the rows' place carries the eleven headings, the row count, and an explicit instruction that the rows were read directly and must not be returned.

---

## Part 1 — the row count is unbounded in all three places

### 1a. Extraction does not ask the model to return the rows

`server/app/schedule_table.py` (new) finds the activity table among a `.docx`'s tables and takes its rows. Three pieces:

- **`docx_text.docx_tables(raw)`** returns every table in body order as a rectangular grid, with horizontal merges expanded, which the reader already did for the pipe-grid rendering.
- **`schedule_activities.map_headings(headings)`** resolves the column meaning **once per table**, from the heading vocabulary already in that file. This is the one judgement an activity table needs, and it is code that can be read and tested rather than a model's judgement repeated per row.
- **`schedule_table.find_activity_table(tables)`** picks the table that resolves an identity column **and** a finish column, scoring by how many columns it resolves. A document header block resolves neither and is passed over; a one-data-row table is a summary line, not a list of activities. A table that resolves nothing is **not guessed at**: the caller is told there is no activity table and the document's other fields extract as normal.

`extract_with_confidence` then drops `milestones_json` from the field list and elides the table's rows from the text. The header row survives, so the model can still see the document has a schedule and can still answer a scalar field about it.

**`milestones_json` is not deleted.** It remains the fallback for a document this reader cannot open. A PDF's tables are not available on this side of the model boundary, and that limit is reported rather than worked around by guessing at rendered layout. `_persist_schedule_activities` tries the reader first and falls back, which also keeps every extraction stored before this change readable.

**The unhit risk this removes, stated because nothing would have caught it.** A model retyping five hundred rows will get some of them wrong, silently. The rows would be well-formed, in-range and plausible, so no validator on this platform could notice. Rows the reader takes are the document's own cells.

### Two findings from the real document that fixtures did not have

Both were found by running against the owner's real file, and both would have silently lost data.

1. **The current finish is spread over two columns.** The real extract carries `Actual finish` and `Forecast finish` side by side, with exactly one filled per row and the other holding an em-dash the date parser correctly refuses. Reading only the first mapped column would have lost the finish date of every completed activity, or of every live one, depending which was listed first. `read_activity_table` now walks the whole mapped chain in preference order and takes the first candidate yielding a **date**; where none does, the first candidate that held anything carries the refusal, so the row still says why it is unusable. A fault reading only the first mapped column takes the suite to 82/87.
2. **A column heading can state the kind.** A column headed `Actual finish` is the document saying every date under it is a recorded finish, not a prediction — exactly what a trailing `A` marker says at the cell level. `kind_from_heading` reads it. Without this, the real document's eight completed activities were stored as forecasts, which are the only dates that can slip. The cell's own marker still wins where it said something, because a cell is more specific than a column. `Current finish / actual` is deliberately **not** treated this way: it is one column holding both kinds and only the cell can say which a row is.

### 1b. Storage is one row per activity per period

Unchanged in shape, deliberately: `schedule_activities` (migration 0021) already has it, and a second store was not invented. What changed is where the rows come from — re-read from the stored document bytes at persist time rather than from anything a model retyped — so no JSON field ever holds a schedule.

What **is** stored on the extraction is a bounded descriptor, `Document.extraction["schedule_table"]`: the table's body-order index, its headings, the resolved column map and the row count. A few hundred bytes that do not grow with the row count. It names the table; it does not contain it.

Verified through the real pipeline: the 29-activity document produces **29 rows** with 8 marked actual and 0 unusable; the 500-activity document produces **500 rows** through the identical path.

### 1c. Display does not render every row

`schedule_activities.select_for_display(rows, previous)` is pure and tested directly. **The rule, returned on the response beside the selection rather than left to be inferred:**

> Shown: every activity whose forecast finish moved later since the previous period, every activity forecast to finish later than its own baseline finish, the next five activities due to finish, and the last activity in the schedule. Ordered by how far each has moved, then by finish date, and capped at 20 rows. Everything else is stored and not drawn.

Four things earn a row: **movement**, **lateness against plan**, **imminence**, and **being the end of the job**. Everything else is stored, queryable, and counted rather than drawn. The response carries `total`, `not_shown` and `unusable`, so a short list can never be mistaken for a short schedule.

An activity absent from the previous period has **arrived, not moved**, and no movement is claimed for it. That is the rule Milestone Trend Analysis applies, for the same reason.

On the real document the surface draws **15 of 29**. On the 500-row document it draws 20 of 500 and says 480 are stored and not drawn.

### The P1 invariant, proven

**Recomputing period 1 after periods 2 and 3 exist is byte-identical to the period-1 row produced when period 1 was the only period the project had.**

The suite computes period 1 alone and captures its bytes, uploads the later periods, runs the all-periods compute, then recomputes period 1 through `adminrecompute` and compares. The comparison is the one `REPORT_2026-08-05_schedule-milestones.md` describes and is deliberately identical, with `result_id` and `computed_at` excluded **by name** because a recompute is a new append-only row required to have a new id.

**It is a check that can fail.** A fault removing the period bound from `_milestone_history` takes the suite to **84/87**, and the byte comparison is one of the three that go red.

---

## Part 2 — the schedule and the field extraction are separated

**How.** They no longer share an output budget, because the activity table is not in the output at all. `extract_with_confidence` computes the activity table before building the prompt; where it has one, `milestones_json` is removed from the requested fields and the table's rows are removed from the text. The scalar fields then have the whole budget, which is what they always needed and never had. The response that failed three times died at its **seventh scalar key**, before it reached the table.

The separation is structural rather than a matter of tuning. Raising the output cap would have bought one document. Removing the unbounded thing from the response makes the budget question disappear, because what remains is a fixed handful of scalars whose size does not depend on the document.

**Confirmed on the real document: it yields its scalar fields as well as its activities.** Driven end to end: extraction status `extracted`, type `schedule_update`, no truncation, **29 rows** stored with 8 actual and 0 unusable, **scalar fields stored** (`plannedPctComplete` and `activitiesPlanned`) and read back, and the display drawing 15 of 29 with its rule.

The model call itself was stubbed with a recorded extraction, because no API key is available in this environment. What was measured against the real bytes and not stubbed: the table recognition, the column mapping, every parsed row, the elision, the prompt, and the exact size of what would have been sent.

---

## Part 3 — a truncated response says so

`TruncatedResponseError` (a subclass of `ExtractionError`, so every existing caller handles it without a new branch) and `describe_json_truncation`. Two independent detections:

1. **The API's own statement.** `stop_reason == "max_tokens"` raises immediately. Authoritative, and catches even a truncated prefix that happens to close its own braces.
2. **The shape of the text.** A single scan tracking string state, escapes and bracket depth, remembering the most recent object key. Unterminated structure at the end is truncation, not a syntax error.

**The message names what was being read.** Against the real failure's recorded prefix, verbatim in the suite:

> the model ran out of output space before it finished answering: the model's answer was cut off while writing a field name, after `'activities_planned'`; the name it had reached was `'activities_constrain'`. Retrying will stop in the same place; the answer has to be made smaller.

The partial field name, the last completed field, and the fact that retrying will not help — which is what three retries established and nothing recorded. **Prose still reports as not JSON**: making everything read as truncation would be the same defect with the words swapped, and a check asserts the two stay distinguishable.

### Every other message on this path that misdescribed its cause

| Where | What it said | What was true | Done |
|---|---|---|---|
| `extraction_client.parse_json_response` | "model response was not JSON" | The response was valid JSON, cut off. Cost three retries. | **Fixed.** |
| `assets/js/files.js` | "Extraction failed. See the upload panel for the reason." | The upload panel is on a different tab and its contents had already been overwritten by the next status refresh. The sentence sent people where the information was not, and the reason was in hand, unused. | **Fixed**: the actual words are shown in place. |
| `assets/js/workspace.js` | `s.recognised + " of " + s.total + " recognized from cache"` | The server key is `recognized`. Every upload reported "undefined of 27 recognized from cache". | **Fixed.** |
| `assets/js/signals.js` `showResultModal` | Title "Extraction failed" on the catch-all handler | Fires for a network failure, an over-cap payload, and an unreachable store, where no extraction was attempted. | **Reported, not changed.** Legacy single-document ingest path; its status line already distinguishes the cases. |
| `extraction_client.classify_with_confidence` | Silently falls back to the filename guess on any `ExtractionError` | Accurate in outcome, but the reason is discarded, including a truncation. | **Reported, not changed.** Nothing reads a classification failure reason. |
| `extraction_client.StubExtractor` | "refusing to invent an extraction" | Accurate. Named only to say it was checked. | No change. |

---

## Part 4 — the upload path shows what succeeded and what failed

**The constraint, and why it decides the design.** Extraction refuses a whole document rather than storing part of it. That rule is right and unchanged: a half-stored extraction puts a coerced figure into the research record. But its consequence had not been recorded anywhere — a failed document leaves **no `documents` row and no `document_uploads` row**. It is not marked bad, it is **absent**, and no query over what is stored can recover it. So "what failed" is written down when the attempt is **made**.

**Migration 0022, `upload_attempts`** (new). One row per file per upload: project, period, `batch_id`, filename, sha256, size, status (`extracted` / `matched` / `filed` / `failed`, the same four words the upload response uses so the durable record and the dialog cannot drift), doc type, `error`, who, when. Two CHECK constraints: the status is one of the four, and **a failure must carry a reason** — the database refuses a silent NULL.

**`error` holds the words of the actual failure, verbatim.** Not a category, not a code. The thing that refused the document wrote a sentence naming what it saw, and replacing it with "extraction failed" is exactly the loss this record exists to stop. The suite asserts the stored string equals the refusing code's sentence character for character, and that `activities_constrain` survives from the model's cut-off response to the reader.

**Append only.** A retry writes a new row and the failed one stays, because a document that failed once and then worked is a different fact from one that always worked.

Served on `projectuploadstatus` as `attempts` (everything, newest first) and `failed` (filenames whose **most recent** attempt failed). Ordering is by `attempted_at` **and the row's ULID**, because the database clock can give two attempts the same timestamp and a retry that succeeded must not lose to the failure it replaced.

**Retry is per document.** `renderFailedUploads` draws one row per outstanding failure with its own file input. The suite drives it: a batch of two where one fails, a fresh status read finding the failure by filename with its reason, a retry of that **one** file, and afterwards nothing outstanding, three attempt rows, and two distinct batch ids.

**Nothing is gated on `window.confirm`**, here or on the Part 5 control. A render check clicks the Part 5 button with `window.confirm` replaced by a recording stub and asserts it was never consulted; a fault adding a confirm gate turns it red.

---

## Part 5 — signals for every period, from the project

**New action `projectcomputeall`.** PM only, operational accounts only.

**Periods compute in order, and each sees only itself and earlier periods.** Held two ways rather than one. The loop runs ascending, so a period is never computed while a later one is being written. And the bound is not the loop's to keep: `_earlier_live_results`, `_period_history` and `_milestone_history` each select on the period being computed or earlier, so a period computed last would still see only itself and its predecessors. The ordering makes results sensible to read; the selection bound makes the invariant true. A fault reversing the loop order takes the suite to 83/87.

**An already-computed period is left alone**, and reported as skipped. `projectcompute` refuses to overwrite a live result and points at `adminrecompute`, because replacing a result is an append-only, audited, reason-bearing operation; doing it in bulk here would be that operation without the reason and without the audit.

**Refused server-side for research accounts, in two places.** The action checks `account_type` itself before the membership check, and `features.RESEARCH_FORBIDDEN_ACTIONS` carries it so a research caller is refused at dispatch. The suite **calls the action directly** with a research participant's session and asserts the refusal and its wording; a fault removing **both** gates turns two checks red. The same suite confirms an operational PM is still allowed, so the gate is on the account and not on the action being broken.

**The control**: a "Generate signals for every period" button in the project detail head actions, beside Upload documents. It reports how many periods computed, how many were left untouched, and the order they ran in.

### Is the Workspace per-period button now redundant?

**No, and it was not removed.** It is redundant in *capability* but not in *meaning*, and the difference is the research design.

`projectcomputeall` is refused for research accounts precisely because the frozen package depends on when computation happens relative to a participant's judgment. A research participant therefore needs a control that computes **one named period**, and the Workspace button is that control. It is also the only control that computes a period **without** touching any other, which is what a participant working through periods one at a time does.

Two things about it worth flagging, neither changed here: it is hard-coded to period 1, and its label is accurate. If the platform gains a period selector on that panel, the button becomes the general single-period control and the question closes properly.

---

## Proof each check can fail

Seven server faults, each anchor asserted to match exactly once, each confirmed applied by SHA-256 before the run, each reverted with a SHA-256 comparison, baseline re-run green after every one.

| Fault | Result |
|---|---|
| the activity table is asked back from the model as well | 84/87 |
| the activity table's rows are still sent to the model | **82/87** |
| a truncated response is reported as "not JSON" again | **80/81** |
| only the first mapped finish column is read | **82/87** |
| the milestone series is not bounded by the period being computed | **84/87**, byte-identical check among the three |
| the all-periods compute runs newest first | 83/87 |
| the failures are left out of the upload record | **82/87** |

Two render faults: drawing only the first failed upload row takes `tests_render.html` to 182/185; putting the all-periods control behind `window.confirm` takes it to 183/185. Both reverted byte-identical.

---

## Real document versus constructed, stated plainly

**Against the real document** (owner-supplied, at a path outside the repository, and **not committed**): the table is recognised among the document's three tables; all **29** rows parse; every row carries a readable finish date; the column map resolves six fields including `Actual finish` as the current finish; **8** rows are marked actual and **21** forecast; one model call is made and `milestones_json` is not in its prompt. End to end: uploaded, extracted, 29 rows stored, both scalar fields stored and read back, the display drawing 15 of 29, and the all-periods control computing its one period.

**Constructed**, and committed as the suite's fixture: a document of the same shape — the real extract's eleven column headings verbatim (the headings are the export format, not the project's data), the same two-finish-column layout with an em-dash in the unused one, and 29 or 500 data rows. The activity identifiers and names are invented.

The suite runs the real-document checks when `REAL_SCHEDULE_DOCX` names a file and says plainly in its output when it did not: **87/87 without it, 89/89 with it.**

**The limit that remains.** The 500-row table is constructed. No real document of that size was available, so what is demonstrated at 500 rows is that the reader, the store and the model call behave identically at that size, not that a real thousand-row export has been read. The argument that size no longer matters rests on the rows never entering a model's input or output, which is a property of the design rather than of any file, and the measurements above are what show the design has that property.

**Also not observed**: a PDF schedule. Its tables are not available on this side of the model boundary, so a PDF still takes the `milestones_json` path and is still subject to the original truncation, now at least reported honestly as truncation. **A real remaining gap, named rather than papered over.**

---

## Left open, deliberately

- **The model is not asked to map columns.** The brief allowed for the model identifying which column carries what, once. In the event the deterministic heading vocabulary already in `schedule_activities` resolved the real document's eleven headings without help, so no second model call was built: an unrecognised heading contributes nothing and the table is reported as unrecognised rather than guessed at. If a real export appears whose headings the vocabulary does not know, the fix is either a heading added to the vocabulary or a bounded header-row-only model call. Stated so the next session does not rediscover the choice.
- **`extraction_fields.py` still lists `milestones_json`** for schedule and monthly report types. Deliberate: it is the PDF fallback.
- **`server/app/simulation/VALIDATION.md`** remains stale on the milestone series, for the reason the schedule-milestones report gave: editing it means opening a directory that is off limits, for a documentation change.

## A tooling defect found on the way

`server/run_all_suites.sh` assumed a `.venv` and, where there was none, ran every suite with a non-existent interpreter and reported "no RESULT line" for all 44 rather than failing loudly. Fixed to fall back to `python3` on PATH and to pass `PYTHONIOENCODING=utf-8`. Worth knowing because a suite runner that reports nothing rather than failing is the shape of a green that means nothing.

## Files changed

New: `server/app/schedule_table.py`, `server/alembic/versions/0022_upload_attempts.py`, `server/tools/test_unbounded_schedule.py`. Changed: `server/app/docx_text.py`, `server/app/extraction_client.py`, `server/app/schedule_activities.py`, `server/app/documents.py`, `server/app/features.py`, `server/app/research_models.py`, `assets/js/workspace.js`, `assets/js/detail.js`, `assets/js/files.js`, `index.html`, `tests_render.html`, `server/run_all_suites.sh`, `T6_HANDOFF.md`.
