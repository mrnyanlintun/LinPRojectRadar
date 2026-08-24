# Run-56 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v37`.

## Why there is a successor at all

A duplicate control was removed from a page a participant works on, and two destructive controls
on that page now ask before acting. What a participant READS AND CLICKS is part of the frozen
candidate, so v36 is **superseded, not amended**.

    v25 accepted freeze -> S1/S2 -> v26 -> mechanism repair -> v27 -> retirement -> v28
    -> render repairs -> v29 -> retrieval by field kind -> v30 -> the EVM consistency check
    -> v31 -> the current period and the live naming instances -> v32
    -> the completion of the naming correction -> v33
    -> the delivery of the six rulings Run 50 stopped on -> v34
    -> one dead control removed and one name across the wire -> v35
    -> the deep-dive deletion, Manage navigating, and the six admin controls moved -> v36
    -> one duplicate control removed and two confirmations added -> v37 successor

## The three rulings, and what each became

| ruling | what was built |
|---|---|
| 1. Remove the duplicate "Upload documents" (`.pe-populate`) from the detail page | **Carried.** The survivor `.detail-upload` was proved to do everything the removed control did BEFORE the removal, pinned to the explicit commit `e13b4f1`: the entire body of `.pe-populate`'s handler is one statement, `openUploadModal(id)`, and `.detail-upload` calls the same function with `render()`'s own `p.id`. Removal is scoped to the hosted path, so the portfolio-row journey is untouched and the listener is guarded rather than deleted. Measured in a real browser on three projects: the detail page carries EXACTLY ONE control that opens the upload dialog. |
| 2. Remove `.detail-reset` and keep `.pe-reset` | **NOT CARRIED. STOPPED under section 9.1, and BOTH controls remain.** The ruling's premise -- that `.pe-reset` clears more -- is FALSE, established by comparison at `e13b4f1` rather than by reading. NEITHER control is a superset of the other: only `.detail-reset` calls `LinResults.clear()`, re-fetches through `LinStore.getProject` into `LIN_PROJECTS`, forces the in-memory record to awaiting-ingest and re-renders the page; only `.pe-reset` calls `LinStore.load()`, `logEvent()` and `renderPortfolioAdmin()`. `detail.js` did not move. |
| 3. Archive and Reset signals ask before acting | **Carried, reusing the pattern the application already has.** `LinUI.openModal`, the shape used by `openDeleteArchivedModal` and `openDeleteProjectModal`, NOT `window.confirm` -- four files in this repository already record that `window.confirm` returns false in this container, which would have made Archive impossible to perform. Each confirmation names the project in its title, its detail and on its button. No control was added; cancelling is the dialog's own x, Escape and backdrop and was proved by execution to make no call, cause no navigation and change no state. |

## What a participant reads and clicks, before and after

Exactly one file a participant loads moved: `assets/js/ingest.js`. It is not sequence-bearing, so
this link carries **no sequence exception**, and that is DECLARED as an empty tuple rather than
left as a silence. All five members of `SEQUENCE_BEARING_FILES_FROM_V21` are present and byte for
byte identical to v21, measured.

NO STORED FIGURE MOVED. No formula, band, threshold, calibration, abstention rule or population
moved: voting is still exactly A1.7 and A1.8, 63 modules in service of 101 registered, and the
behaviour digest is RE-DERIVED and unchanged.

## Gate

15 blocker classes evaluated, 0 blocked. Artifact:
`research/freeze/run56_successor_freeze_gate.csv`.

The v25 to v36 release records are preserved unchanged and still record their own stamps.
