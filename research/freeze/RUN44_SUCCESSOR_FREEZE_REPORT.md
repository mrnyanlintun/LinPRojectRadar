# Run-44 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v29`.

## Why there is a successor at all

Run 43 accepted a successor freeze of the v28 instrument. Run 43J then diagnosed eleven defects
on a participant render, classified seven of them F (render or presentation defect, storage
correct), one C and three G, and **changed nothing**. The owner ordered four of the F defects
repaired on 2026-08-22.

Every repair is at the render. **Storage was correct in every one of them**, and the record of
what a participant was SHOWN is what the freeze governs, so v28 is **superseded, not amended**.

    v25 accepted freeze -> S1/S2 -> v26 successor -> Run 42 mechanism repair -> v27 successor
    -> owner's retirement ruling -> v28 successor -> Run 43J render diagnosis
    -> owner's repair order -> v29 successor

## The four defects, and what each one showed a participant

| Defect | What it showed | What it shows now |
|---|---|---|
| Severity ranked on capitalisation | a module storing lowercase `green` was selected as its category's "worst" ahead of two properly-cased Green ones, because a key miss fell through to the unknown rank | one shared, case-insensitive rank at every site on the page that orders a status |
| Driver attribution unchecked | an Amber category offered a Green module as the driver of its Amber | a module better than the severity it would drive is not named as driving it, and the panel says why |
| Absent document risk rendered as a value | an absent score is stored present-and-null, and `Number(null)` is 0 and finite, so it rendered `0.00` Green and was carried into the Executive Brief as a key driver | absent renders as absent; a genuine stored zero still renders as zero |
| Computed figures labelled extracted | CPI and SPI carried the extracted mark with no source to show | both are labelled computed, on the panel and in the upload result line |

The fifth change is the Portfolio Health flyout, which told a participant the panel needed at
least three projects when after the Run-43 offload no number of projects makes it compute. It now
states the current state, from a predicate **derived from the taxonomy the page loaded**.

## What did NOT change, proved by execution

| Subject | Result |
|---|---|
| Registered module population | 101, identical |
| `run_module()` over all 101 identifiers, full package | **0 rows differ** against the v28 line |
| `run_module()` over all 101 identifiers, starved package | **0 rows differ** against the v28 line |
| Modules in service, available, retired, voting | identical |
| Merged signal inputs and per-field source record | identical |
| `docRiskScore` on an absent observation | still PRESENT AND NULL |
| Fused category status over the voting pair | identical for every band pair tried |
| Synthetic package | RETAINED `OG-SYNTH-0.6` |
| Analysis schema | RETAINED `og-analysis-2026.08-v1` |

This is not inferred from a source diff. The v28 line is extracted from its own pinned git object
and imported as its own package, both lines are executed on identical inputs, and the comparison
was **proved failable** by perturbing one module's own input and observing that module, and only
that module, diverge. The stamp is normalised out of the row comparison and asserted separately,
so a run that minted no stamp could not pass.

## The one invariant this release deliberately breaks

`assets/js/deepdive.js` is one of the six `SEQUENCE_BEARING_FILES`, and every participant-package
record since v10 asserts those six are byte-identical across a successor. **This release cannot
say that, and says so instead.** The change is the Portfolio Health flyout's reason sentence and
nothing else: no step of the decision sequence, no reveal gate, no lock, no randomization, no
server contract, no append-only record and no user-facing control moved. Its authority is the
owner's order at Run 44 section 4.4. The gate's B04 blocker and the package checks were
reconciled to the true bytes and to a NAMED exception; neither was disabled, weakened or widened,
and a second sequence-bearing file moving is still a failure.

## The scientific position

No input was invented, no fact fabricated, no qualification rule relaxed and no scientific method
changed. Nothing on the analytical side was touched. **Three of Run 43J's eleven defects remain
classified G and are unresolved**, together with three further G questions: every one of them
needs read access to stored rows that this run did not have and did not take.

## Gate

15 blocker classes evaluated, 0 blocked. Artifact:
`research/freeze/run44_successor_freeze_gate.csv`.

The v25, v26, v27 and v28 release records are preserved unchanged and still record their own
stamps.
