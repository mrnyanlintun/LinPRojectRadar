# Run-57 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v38`.

## Why there is a successor at all

A user-facing control was removed from a page a participant works on, and the control that
survives it now does the work of both. What a participant READS AND CLICKS is part of the frozen
candidate, so v37 is **superseded, not amended**.

    v25 accepted freeze -> S1/S2 -> v26 -> mechanism repair -> v27 -> retirement -> v28
    -> render repairs -> v29 -> retrieval by field kind -> v30 -> the EVM consistency check
    -> v31 -> the current period and the live naming instances -> v32
    -> the completion of the naming correction -> v33
    -> the delivery of the six rulings Run 50 stopped on -> v34
    -> one dead control removed and one name across the wire -> v35
    -> the deep-dive deletion, Manage navigating, and the six admin controls moved -> v36
    -> one duplicate control removed and two confirmations added -> v37
    -> the two reset controls MERGED into one -> v38 successor

## The ruling, and what it became

| ruling | what was built |
|---|---|
| Merge the two reset handler bodies into one control that does the union, then remove the other | **Carried in full.** Run 56 stopped this removal because NEITHER handler was a superset of the other, so removing either alone would have lost behaviour. Run 57 removes that objection rather than overruling it: the survivor is given the UNION first. Both bodies were RE-MEASURED at the explicit commit `50dfb40` rather than taken from Run 56's table -- Run 56's eleven-behaviour comparison reproduces exactly, and a twelfth probe finds a sixth `.detail-reset`-only behaviour, `LinStore.getCached(`, which this release acts on. |
| Which selector survives | **`.pe-reset`**, and the reason is stated rather than picked silently: every behaviour unique to `.detail-reset` is reachable from `ingest.js` through interfaces that are ALREADY public (`window.LinResults`, `window.LIN_PROJECTS`, `LinStore.getProject`/`getCached`, and `detail.js`'s exported `LinDetail.render`), whereas `logEvent()` and `confirmDestructive()` -- unique to `.pe-reset` -- are module-private to `ingest.js` and would have had to be newly EXPORTED to build the union inside `detail.js`. Merging into the survivor adds nothing to any module's public surface, and it leaves Run 56's confirmation byte-identical and in place. |
| The order of the merged handler | **By dependency, not by concatenation.** Server reset first; both caches dropped before any re-fetch or re-render; `LinStore.load()` before `getProject(id)` so the store-wide reload cannot overwrite the record just fetched; the awaiting-ingest mutation after the re-fetch; `logEvent()` once before the re-renders; `LinDetail.render(id)` LAST, because it rebuilds the host that contains the surviving button. |
| What went with the removal | `.detail-reset`'s markup, its `.detail-reset-msg` aria-live span, `wireReset()`, `wireReset`'s call site in `render()`, and `radar.css`'s now-dead `.detail-reset-msg` rule. **That dead-CSS check is a real one and not a vacuous one**, because the rule existed at `50dfb40`. |

## What a participant reads and clicks, before and after

Measured in real Chromium on three projects: **BEFORE, each detail page carried TWO controls that
clear stored signals; AFTER, exactly ONE.** Exactly one button was lost -- "Clear stored signals
for this project" -- and NONE was added or moved. The admin panel's control order is unchanged and
its panel is bound to the viewed project and no other. Confirming really calls `resetSignals`,
`LinResults.clear()`, `LinStore.load()`, `getProject()`, `LinDetail.render()` and `logEvent()`,
proved with counting spies rather than by reading, and touches no other project; cancelling makes
no call and changes no state.

Three files a participant loads moved: `assets/js/ingest.js`, `assets/js/detail.js` and
`assets/css/radar.css`. Not one is sequence-bearing, so this link carries **no sequence
exception**, and that is DECLARED as an empty tuple rather than left as a silence. All five
members of `SEQUENCE_BEARING_FILES_FROM_V21` are present and byte for byte identical to v22,
measured.

NO STORED FIGURE MOVED. No formula, band, threshold, calibration, abstention rule or population
moved: voting is still exactly A1.7 and A1.8, 63 modules in service of 101 registered, and the
behaviour digest is RE-DERIVED and unchanged.

## Gate

15 blocker classes evaluated, 0 blocked. Artifact:
`research/freeze/run57_successor_freeze_gate.csv`.

The v25 to v37 release records are preserved unchanged and still record their own stamps.
