# Run-62 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v40`.

## Why there is a successor at all

**The fix is published.** Two branches were finished, gated nowhere and stacked unmerged: Run
60's diagnosis and Run 61's fix. Three of the 242 governed production-tree members moved --
`assets/js/detail.js`, `assets/js/taxonomy.js`, `assets/js/workspace.js` -- and two files were
added under `server/tools`, which moves the suite population this freeze measures from 203 to
204.

    v25 accepted freeze -> ... -> v39 -> the caller states its question -> v40 successor

## The defect, and what closed it

A project detail page read a stored-signal row that was not necessarily the row of the period
the page holds. `taxonomy.js` now keys its row cache by `(project, period)` and exposes
`rowForPeriod` (that period or nothing), `latest` (the period travels with the row) and
`rowsForPeriods`. `workspace.js` resolves `projectperiods`, then `latest_computed_period`, then
`projectresults`, so the caller states its question before it asks. `detail.js` re-renders its
provenance line from the row it actually received.

## What a participant reads and clicks, before and after

One sequence-bearing file moved, `assets/js/workspace.js`, so this link carries a **named
exception of record** in `V24_TO_V25_SEQUENCE_EXCEPTION`. What moved inside it is the ORDER OF
THE SERVER CALLS. The other four members of `SEQUENCE_BEARING_FILES_FROM_V21` are present and
byte-identical, measured. `taxonomy.js` is **not** sequence-bearing, measured and not assumed.

NO STORED FIGURE MOVED. Voting is still exactly A1.7 and A1.8, 63 modules in service of 101
registered, and the behaviour digest is RE-DERIVED and unchanged. No control was added, moved or
removed.

## Gate

15 blocker classes evaluated, 0 blocked. Artifact:
`research/freeze/run62_successor_freeze_gate.csv`.

The v25 to v39 release records are preserved unchanged and still record their own stamps.
