# Run-48 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v32`.

## Why there is a successor at all

The project detail page read the stored result back with a hard-coded `period: 1`. Every panel on
that page holds whatever that one call returns, so on a project whose current period was not 1
the key drivers, the abstention reasons, the served basis for the recommendation and the Run 47
disagreement findings all described period 1. WHICH STORED ROW A PAGE READS is executable
behaviour, so v31 is **superseded, not amended**.

    v25 accepted freeze -> S1/S2 -> v26 -> mechanism repair -> v27 -> retirement -> v28
    -> render repairs -> v29 -> retrieval by field kind -> v30 -> the EVM consistency check
    -> v31 -> the current period and the live naming instances -> v32 successor

## The three rulings, and what each became

| ruling | what was built |
|---|---|
| The page shows the latest period that has been computed | `_computed_periods` and `_latest_computed_period` in `server/app/documents.py`, read from the live computed results; `projectperiods` serves them; `primeAndRefresh` reads that period's row |
| The live naming instances are corrected | `deepdive.js` panel labels and fallback, `charts3d.js` node label, the brief prompt in `detail.js`: groups and purposes only |
| The dead category label map is deleted | Removed from `detail.js` outright |

## What changed, and what did not

| Subject | Result |
|---|---|
| Stored figures of any kind | **unchanged**; every addition is on the read path |
| Project status, category statuses, bands, colours, postures | **unchanged** |
| Registered / in service / voting | 101 / 63 / exactly A1.7 and A1.8, all identical |
| Sequence-bearing participant files | **one moved**, `assets/js/deepdive.js`, on ruling 2, with its own named exception record; the other five are byte-identical |
| User-facing controls | **none added, moved or removed**; the detail page still has no period selector |
| Participant package | SUPERSEDED to `og-participant-2026.08-v17` |
| Synthetic package | RETAINED `OG-SYNTH-0.6` |
| Analysis schema | RETAINED `og-analysis-2026.08-v1` |

## Gate

15 blocker classes evaluated, 0 blocked. Artifact:
`research/freeze/run48_successor_freeze_gate.csv`.

The v25, v26, v27, v28, v29, v30 and v31 release records are preserved unchanged and still record
their own stamps.
