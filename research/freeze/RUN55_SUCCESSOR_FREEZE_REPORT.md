# Run-52 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v35`.

## Why there is a successor at all

A dead control was removed from a surface a participant reads, and the module identifier moved
to a single name on both sides of the wire. What a participant READS is part of the frozen
candidate, so v34 is **superseded, not amended**.

    v25 accepted freeze -> S1/S2 -> v26 -> mechanism repair -> v27 -> retirement -> v28
    -> render repairs -> v29 -> retrieval by field kind -> v30 -> the EVM consistency check
    -> v31 -> the current period and the live naming instances -> v32
    -> the completion of the naming correction -> v33
    -> the delivery of the six rulings Run 50 stopped on -> v34
    -> one dead control removed and one name across the wire -> v35 successor

## The four rulings, and what each became

| ruling | what was built |
|---|---|
| 1. Remove the Open button from the project list | **NOT CARRIED. Surface STOPPED under section 8.1.** The ruling's premise -- that Manage and Open lead to the same page -- is FALSE, established by execution in a real browser: Manage opens an inline admin accordion under its own row and never leaves the portfolio page, while Open is the ONLY route from the project list to the project detail page. `app.js` did not move. |
| 2. Remove the dead "see Health" button | Carried. `deepdive.js`: the button and its `[data-goto-health]` handler are gone; the anomaly sentence it sat beside is unchanged and still renders. |
| 3. One name for the module identifier: `module_id` | Carried. `taxonomy_authority.json` (101 module rows), `build_client_taxonomy.py`, both regenerated mirrors (63 rows each), and every client consumer. Two sites STOPPED under 8.2 and named. |
| 4. Identifiers on screen are not touched | Obeyed as the reversal it is. **No naming sweep was run.** Nothing stripped, nothing restored. |

## What changed, and what did not

| Subject | Result |
|---|---|
| Stored figures of any kind | **unchanged** |
| Project status, category statuses, bands, colours, postures | **unchanged** |
| Behaviour digest | **unchanged**, `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1` |
| Registered / in service / voting | 101 / 63 / exactly A1.7 and A1.8, all identical |
| Rendered identifiers | **unchanged**; no sweep was run |
| Sequence-bearing participant files | **one moved**, `deepdive.js`, with its own named exception record; the other five are byte-identical to v19 |
| User-facing controls | **one removed, and it was dead**: the see-Health button. Nothing else added, moved or removed. |
| Participant package | SUPERSEDED to `og-participant-2026.08-v20` |
| Synthetic package | RETAINED `OG-SYNTH-0.6` |
| Analysis schema | RETAINED `og-analysis-2026.08-v1` |

## Two rename sites recorded STOPPED, rather than forced

`p0-baseline/module_renumbering_map.csv`'s `new_id`/`old_id` column pair is not renamed. It is a
PAIR -- the current identity and the pre-renumbering identity -- not one name for one thing, its
name originates in the header row of a frozen baseline artifact the freeze gate pins, and it has
309 occurrences across more than thirty files. Where the identifier actually crosses the wire --
the stored row, the API response, the export -- it is already `module_id`.

`deepdive.js`'s methods-comparison `num` field is not renamed. It is the ordinal of a METHOD in
that table (09 = the conservative-dominance baseline, 10 = Dempster-Shafer), not a registry
module identifier; calling it `module_id` would assert an identity it does not have.

## Gate

15 blocker classes evaluated, 0 blocked. Artifact:
`research/freeze/run52_successor_freeze_gate.csv`.

The v25 to v34 release records are preserved unchanged and still record their own stamps.
