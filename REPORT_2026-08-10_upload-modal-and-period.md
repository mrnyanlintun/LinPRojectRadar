# The upload modal goes wide, and the period picker is a number

**Date:** 2026-08-10
**Branch:** `claude/upload-modal-and-period-picker`, started fresh from `origin/main` at `853635f`
**Model:** Sonnet 5

**Verification:** server suite **56 suites, 3047/3047** (new `test_period_number_picker.py` adds
25), fresh migrated SQLite per test file. `tests.html` **51/51**. `tests_render.html`
**286/287**, the one red being the pre-existing auth-gated "production read path" row (red on
unmodified `origin/main` too, unrelated to this change). A real headless-Chromium drive against a
live in-process server, **26/26**, at desktop and phone viewports, with a genuine extraction
failure and retry. Faults injected in both the server suite and the browser drive, each confirmed
applied, detected, and reverted.

No migration was added or needed. No `DATABASE_URL` pointed anywhere but throwaway SQLite.
Production was neither inspected nor queried. **Nothing under `server/app/simulation/` was
touched.**

---

## 1. The upload modal is now wide

**What it actually was.** The narrow, tall dialog described in the brief is
`ingest.js:openUploadModal`, built from `signals.js:dropzoneHtml` — the "Upload Documents" modal
reached from the portfolio. (It is a separate surface from the "Period documents" tab on the
project page, `workspace.js`, which already used a plain number + optional date and was not
touched.)

**The fix is a modal width flag, not a rewrite of the content.** `LinUI.openModal` (`app.js`) now
accepts `opts.wide`, which adds a class:

```css
.app-modal.app-modal-wide { width: min(920px, 96vw); }
@media (max-width: 560px) {
  .app-modal, .app-modal.app-modal-wide { width: 100%; ... }
}
```

Only `openUploadModal` passes `wide: true`. Create Project and the Archived-projects dialog are
unchanged at 480px — they are short forms with a handful of fields and were never the complaint.
The phone-width override already existed for every modal and applies identically to the wide one:
the mobile rule has two classes to beat the wide rule's specificity, so a 560px-or-narrower
viewport gets the exact same full-width sheet every other modal already used, not a stretched
"wide" dialog squeezed into a phone.

**The document-type reference and the per-file results are the two things that were cramped**, and
neither needed new markup, only room:

- `.doc-type-reference .dtr-grid` was already `flex-wrap`; it needed the container's width, which
  it now has. At 920px it lays out in far fewer rows than at 480px.
- `.dz-queue` (the per-file result list) changed from a single-column flex list to
  `grid-template-columns: repeat(auto-fill, minmax(260px, 1fr))`, so a batch of 27 documents reads
  as a scannable grid instead of a scrolling strip of truncated filenames. A dedicated
  `@media (max-width: 560px)` rule forces it back to one column on a phone, matching how every
  other list on the mobile layout behaves.

**Nothing else in the modal's content changed.** Every per-file result still shows exactly what it
showed before — success with field count and CPI/SPI, or failure with the reason and its own Retry
control (`renderFailedUploads`/`processOne`/`setError` in `signals.js` are untouched apart from
what the number-picker section below required).

**The approved notice text is untouched, character for character.** `LinDisclaimers.uploadNoticeHtml()`
(`disclaimers.js`) was not edited; the modal still calls the same function. A real-browser check
reads `.upload-disclaimer.notice-research` back out of the live DOM and compares it against the
three paragraphs quoted verbatim from `DISCLAIMERS_DRAFT.md`; `server/tools/test_disclaimers.py`
(147/147, untouched) independently guards the source-vs-live match on every server run.

## 2. The period picker is a number, not a date

**What it was, immediately before this change.** The Upload modal's dropzone (`signals.js`) had a
`<input type="date">` labelled "Reporting period ending". The person picked a date; the server
(`documents.period_for_end_date`) derived a period **number** from it and previewed the answer
over `projectperiodfordate` before anything uploaded. (`workspace.js`'s separate "Period
documents" tab already had a number field plus an optional date field, sent explicitly — that
surface was not the one described in the brief and was left as it was.)

**How the cutoff was derived before, read from the code (`documents.py`):**

- `period_for_end_date(session, project, chosen_date)` — the picker's rule — has three arms: an
  exact match on a period's own stored ending date; the earliest period whose stored ending date
  is on or after the chosen date (returns **that period's own stored end date**, not the date the
  person typed); or, when the date is later than every stored end, a brand-new next period whose
  end becomes the date the person typed.
- Separately, and only at the actual upload (`a_projectupload`), `period_end` was read directly
  from the payload (`payload.get("period_end")`) and stored on the `DocumentUpload` row, used
  solely by `_out_of_period` to flag (never reject) a document whose own extracted date falls
  outside the period's stated window. It bounds nothing in the analysis —
  `ComputedResult.period_cutoff` stays derived from the period's own evidence dates, per migration
  0023, and this change does not touch that.

**What changed.** The picker (`signals.js:dropzoneHtml`) is now a `<select>` populated from a new
read-only action, `projectperiods`, which lists the periods this project already holds (each with
its own stated ending date, if one is on file) plus the next new period. The client sends only
`period: N` — no date at all — through the same `extractsignals` -> `a_projectupload` path as
before.

**The cutoff derivation is reproduced, not reinvented, starting from the number:**

```python
# a_projectupload, after period is resolved
period_end = _parse_iso_date(payload.get("period_end") or payload.get("periodEnd"))
if period_end is None:
    period_end = dict(_stated_period_ends(session, project)).get(period)
```

This is the exact same behaviour `period_for_end_date`'s matched-period arms already had — when
the picked value names an existing period, the period's own previously stated ending date is
reused, never the newly picked value. The only thing that changes is what "picked value" means:
a date before, a period number now. A **brand-new** period has no stated ending date to reuse
(nothing has stated one yet), so `period_end` stays `NULL` — precisely the pre-existing "nothing to
measure against, says nothing" behaviour that already applied to any upload with an absent or
unparseable date (`test_period_assignment.py`'s "quiet" case, unmodified, still asserts this). That
is not a new gap this change introduces; it is what happens whenever nobody has stated an end date
for a period yet, exactly as before.

`period_for_end_date`, the `projectperiodfordate` action, and every existing caller that sends an
explicit `period` plus its own `period_end` (`workspace.js`) are **untouched** — `_resolve_period`'s
"supplied" branch, which honours an explicit period number, already existed and needed no change.

**Existing documents keep their existing period.** Nothing was re-filed, nothing was recomputed
for data already in the store; the change is confined to how a **new** upload's `period_end` is
filled in when the client sends a number and no date.

### What the picker offers, and why

**Bounded to the periods this project already holds, plus one new period — not a free-text
number.** `a_projectperiods` returns exactly that list; the `<select>` shows "Period 1 (ends
2026-03-31)" style options for existing periods and "Period N (new)" for the next one, and defaults
to the next new period.

The reasoning: periods are sequential bookkeeping the platform already assigns in order
(`_highest_period(project) + 1` is always the only "next" period a new upload can open). A
free-text number field would let someone type period 9 while periods 2 through 8 stay forever
empty — a gap nothing downstream (the ledger, the per-period compute, the recommendation) is built
to explain or backfill. The list the picker offers can never disagree with what the server would
actually do with that number, because it is read from the same tables `_resolve_period` and
`_highest_period` already query — there is no second copy of "what period comes next" to drift.
`_resolve_period` itself still accepts any `period >= 1` from a payload for backward compatibility
(other existing callers, e.g. `workspace.js`, are unaffected and still send an explicit number);
this change constrains only what the **picker offers**, not what the server will accept from a
caller that already knows a specific number.

A research-assigned project is called out rather than offered a choice: `projectperiods` reports
`server_derived` when the project's period is fixed by its study sequence, and the picker's helper
text says so instead of presenting a menu that upload would then override anyway.

## 3. Verification

### Server suite

56 suites, 3047/3047, fresh SQLite per file. New `server/tools/test_period_number_picker.py`
(25/25) covers: `projectperiods` before and after uploads, refusing an unmember'd/unknown project;
the number-only upload landing in the picked period; a brand-new period's `period_end` staying
`NULL`; two periods computing and aggregating independently (`projectresults` returns period 1 for
period 1, period 2 for period 2, and the two stored results are distinct objects); the cutoff
fallback reusing a period's own previously stated ending date to flag AND store an out-of-window
document with **zero date** in that particular upload's payload; and a fault injection that patches
`_stated_period_ends` to always return nothing, showing the exact defect the fallback prevents (the
late document goes unflagged), then reverting and showing green again.

`tests.html` 51/51, `tests_render.html` 286/287 (the one red is the pre-existing auth-gated
production-read-path row -- present on unmodified `origin/main`, unrelated to this branch, and not
touched here per the standing instruction not to paper over what a red test is correctly catching;
it is not this either, since it is documented as already red before this work started).

### Real browser, against a real (in-process) server, headless Chromium

Playwright driving `chromium_headless_shell` (SwiftShader WebGL enabled), 26/26:

```
PASS  the Upload modal opened
PASS  the modal carries the wide class
PASS  the modal renders wide on a desktop viewport (>700px)          [width: 920]
PASS  the approved research notice text is present character-for-character
PASS  the period control is a NUMBER select, not a date input
PASS  no date input remains in the upload modal
PASS  before any upload, only 'Period 1 (new)' is offered
PASS  a per-file result row rendered after upload
PASS  the result row shows a success status
PASS  reopening the modal now offers existing period 1 (with its stated end) plus new period 2
      ['Period 1 (ends 2026-03-31)', 'Period 2 (new)']
PASS  both files in the batch produced result rows
PASS  both filenames appear in the per-file results
PASS  period 2 holds both documents that were dropped on period 2
PASS  a document dated outside period 2's window is FLAGGED
      'dated 2026-06-20, which is after the 2026-04-30 end of the reporting period it was filed to'
PASS  and it is still STORED in period 2 rather than refused
PASS  period 2 computes
PASS  the computed/stored result is recorded against period 2
PASS  no page errors occurred during the desktop drive
PASS  a failed document renders an error row, not silently dropped
PASS  the failure reason is shown on the row
PASS  the failed row carries its own retry control
PASS  retrying the SAME document, after the fault is fixed, now succeeds
PASS  the Upload modal opens on a phone viewport
PASS  the modal collapses to full (phone) width rather than staying desktop-wide   [width: 390]
PASS  no horizontal page scroll is introduced on the phone viewport
PASS  no page errors occurred on the phone viewport
```

This exercises every item in the minimum-coverage list: the modal's width at desktop and phone
viewports; the notice text read back byte-for-byte from the live DOM; a document uploaded with
period 2 selected landing in period 2 and computing/aggregating as period 2 (a separate, distinct
stored result from period 1's); a document whose own date falls outside the chosen period being
both flagged and stored (not rejected); and the per-file success/failure list rendering correctly,
including a genuine extraction failure (an unrecorded document hash, refused by the stub
extractor exactly as an unrecognised document would be) and its per-document retry actually
succeeding once the fault is fixed.

### Faults injected, each confirmed applied and reverted

| Fault | Detected by | Result |
|---|---|---|
| `_stated_period_ends` patched to return nothing | `test_period_number_picker.py` section 6 | period_end stays NULL and the same late document is silently NOT flagged -- the exact defect the fallback prevents |
| An unrecorded document hash (stub extractor refuses it) | browser drive | error row rendered with the refusal reason, Retry control present, retry succeeds once the hash is recorded |

## 4. Not changed

- `period_for_end_date`, the `projectperiodfordate` action, and `workspace.js`'s own
  period-number-plus-date fields -- all untouched, all still covered by
  `test_period_picker_and_evidence.py` (123/123).
- `ComputedResult.period_cutoff` -- stays derived from the period's own evidence dates.
- `server/app/simulation/`.
- `DISCLAIMERS_DRAFT.md` / `disclaimers.js` -- not edited; the modal calls the same function it
  always did.
- Existing documents' period assignment -- nothing was re-filed or recomputed.

## 5. Files changed

- `assets/js/signals.js` -- the dropzone's period control (`<select>` instead of `<input
  type=date>`), `refreshPeriodOptions` replacing `previewPeriod`, `readStatedPeriod` returning a
  number, `processOne`/`handleFiles` sending `period` instead of `period_end`.
- `assets/js/ingest.js` -- `openUploadModal` passes `wide: true`.
- `assets/js/app.js` -- `LinUI.openModal` accepts `opts.wide`.
- `assets/css/radar.css` -- `.app-modal-wide`, `.dz-queue` grid layout, phone-width overrides.
- `server/app/documents.py` -- `a_projectupload`'s `period_end` fallback (reuse a period's own
  stated ending date when the client sends only a number); new `a_projectperiods` action.
- `server/tools/test_period_number_picker.py` -- new suite, 25 checks.
- `REPORT_2026-08-10_upload-modal-and-period.md`, `T6_HANDOFF.md`.

## 6. Git state

All three suites green on this branch (server 3047/3047, `tests.html` 51/51, `tests_render.html`
286/287 with only the documented pre-existing red), verified again after merging with `main`
(branch started at `main`'s current tip, so the merge is a fast-forward with no conflicts). No
stop condition applies. **Merged into `main` and pushed.**
