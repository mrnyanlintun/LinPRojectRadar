# Run-47 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v31`.

## Why there is a successor at all

A Time-phased Schedule states a planned value to date and a planned percent complete in the same
document. Against a known budget at completion the two determine each other, and on the render
that prompted this run they did not agree: a stated 824,370 against a budget at completion of
5,874,620 and a planned percent complete of 18.47, which implies 1,085,042. The platform
extracted both figures, stored both, and never compared them. Schedule performance is earned
value over planned value, so a planned value that low reads a project as ahead of schedule when
the document's own percentages say it is behind.

What a served result CARRIES is executable behaviour, so v30 is **superseded, not amended**.

    v25 accepted freeze -> S1/S2 -> v26 -> mechanism repair -> v27 -> retirement -> v28
    -> render repairs -> v29 -> retrieval by field kind -> v30 -> Run 46's CPI trace
    -> owner's four rulings -> v31 successor

## The four rulings, and what each became

| ruling | what was built |
|---|---|
| The document takes precedence | `pv` and `ev` are stored exactly as stated. Nothing is derived into storage, nothing is clamped, and `pv` is still absent from `BOUNDED_MAX_SI_FIELDS` |
| The platform computes the implied value and compares | `server/app/evm_consistency.py`, a pure function called on the READ path from the stored row |
| Tolerance is 2 per cent | `TOLERANCE = 0.02`, measured against the **implied** value; both sides of the boundary are exercised |
| A disagreement is text, not a posture change | Rendered on the Executive Brief and beside the recommendation. The full census with and without it is identical |

## What changed, and what did not

| Subject | Result |
|---|---|
| Stored `pv`, `ev`, `bac`, percentages | **unchanged**, byte-identical across a full recompute |
| Project status, category statuses, bands, colours, postures | **identical** with and without a disagreement |
| Abstentions | **identical**; no module abstains that would otherwise compute |
| Registered / in service / voting | 101 / 63 / exactly A1.7 and A1.8, all identical |
| Sequence-bearing participant files | **none moved** |
| User-facing controls | **none added, moved or removed**; the rendered blocks hold zero controls |
| Participant package | RETAINED `og-participant-2026.08-v15` |
| Synthetic package | RETAINED `OG-SYNTH-0.6` |
| Analysis schema | RETAINED `og-analysis-2026.08-v1` |

## Gate

15 blocker classes evaluated, 0 blocked. Artifact:
`research/freeze/run47_successor_freeze_gate.csv`.

The v25, v26, v27, v28, v29 and v30 release records are preserved unchanged and still record
their own stamps.
