# Run-49 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v34`.

## Why there is a successor at all

Run 48's own second sweep found that the retired "Cat N" scheme still rendered on the deep-dive
surface in ten group headers, a banner, a metric-box label, a panel heading, a note and three
prose sentences, and in one sentence reaching the executive brief's model. What a participant
READS is part of the frozen candidate, so v32 is **superseded, not amended**.

    v25 accepted freeze -> S1/S2 -> v26 -> mechanism repair -> v27 -> retirement -> v28
    -> render repairs -> v29 -> retrieval by field kind -> v30 -> the EVM consistency check
    -> v31 -> the current period and the live naming instances -> v32
    -> the completion of the naming correction -> v33
    -> the delivery of the six rulings Run 50 stopped on -> v34 successor

## The five rulings, and what each became

| ruling | what was built |
|---|---|
| Every surviving rendered instance is corrected | `deepdive.js`: the ten group headers, the banner, the metric-box label, the comparison heading and note, three confidence sentences, the comparison table's row prefix and column header, the Portfolio Health flyout headings; `detail.js`: the brief prompt |
| The ampersand is corrected | `detail.js:1086` now reads "Documents and Extracted Signals" |
| The fallback map is made specific again | `CAT_FROM_MODULE` extended from 19 keys to all 77 the call sites pass; no key left on the neutral fallback |
| The period literals are left and recorded | Three comments in `decision-ui.js`; not one byte of executable text changed |
| No panel states its period, no control anywhere | Nothing added |

## What changed, and what did not

| Subject | Result |
|---|---|
| Stored figures of any kind | **unchanged**; every change is displayed text |
| Project status, category statuses, bands, colours, postures | **unchanged** |
| Registered / in service / voting | 101 / 63 / exactly A1.7 and A1.8, all identical |
| Panel bucketing | **unchanged**; `CAT_NUM_FROM_MODULE` is byte-identical to v32 |
| Sequence-bearing participant files | **two moved**, `deepdive.js` and `decision-ui.js`, each with its own named exception record; the other four are byte-identical |
| User-facing controls | **none added, moved or removed** |
| Participant package | SUPERSEDED to `og-participant-2026.08-v19` |
| Synthetic package | RETAINED `OG-SYNTH-0.6` |
| Analysis schema | RETAINED `og-analysis-2026.08-v1` |

## A guarantee recorded NOT MET, rather than dressed up

Run 48's guarantee 11 -- that no user-facing text anywhere in `assets/` carries a module
identifier, a category number, the retired scheme, an ampersand, an em dash or an en dash -- is
**still not met**, and meeting it is outside this run's authority. `app.js` prints a category
identifier and a module identifier on the Categories page from the GENERATED taxonomy, and en and
em dashes remain in user-facing text across roughly forty files including four sequence-bearing
ones that stop condition 9.5 forbids this run to move.

## Gate

15 blocker classes evaluated, 0 blocked. Artifact:
`research/freeze/run51_successor_freeze_gate.csv`.

The v25 to v32 release records are preserved unchanged and still record their own stamps.
