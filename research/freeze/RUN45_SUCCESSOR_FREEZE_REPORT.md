# Run-45 successor freeze report

**Disposition: FINAL_FREEZE_ACCEPTED** for `sim-2026.08-v30`.

## Why there is a successor at all

Run 44 accepted a successor freeze of the v29 instrument and, separately and without acting,
MEASURED a defect in retrieval: every observation was scoped to the period its document was
uploaded into. A contract uploaded at period 1 was invisible from period 2 on, `bac` fell through
to a pay application's weaker restatement -- **4,463,290 where the contract said 5,874,620** --
and `baselineContractSum` **inverted its own declared precedence**, a change order's account of
the original beating the contract that established it.

What a module is GIVEN is executable behaviour, so v29 is **superseded, not amended**.

    v25 accepted freeze -> S1/S2 -> v26 successor -> Run 42 mechanism repair -> v27 successor
    -> owner's retirement ruling -> v28 successor -> Run 43J render diagnosis
    -> owner's repair order -> v29 successor -> Run 44's period-scoping measurement
    -> owner's classification ruling -> v30 successor

## The classification is canonical and was signed off BEFORE any code changed

Run 45 stopped at its section 5.1, proposed the classification with the declaration each kind was
read off quoted per field, and reported five fields as UNDETERMINED rather than resolving them.
The owner ruled. Only then did retrieval change.

| kind | count | retrieval |
|---|---|---|
| IDENTITY | 13 | the latest value **at or before** the period being computed, declared document-type precedence holding **across** the carry-forward |
| PERIOD | 62 | the period's own documents and nothing else - **byte-identical to v29** |
| UNDETERMINED | 2 | retrieved as period fields, which is the unchanged behaviour; the contradiction is recorded, not resolved |
| **total emittable** | **77** | every field in `FIELD_KINDS`, asserted at import to partition exactly |

## What changed, and what did not

| Subject | Result |
|---|---|
| An identity field uploaded at period 1, read at periods 2-4 | now **retrieved**; previously absent |
| `baselineContractSum` with a contract at period 1 and a change order at period 2 | **5,874,620**, the contract's own figure; the 6,100,000 inversion is dead |
| A period field absent in its period | still **absent**; no carry-forward |
| Upload order, chronological vs reversed, both kinds | **identical** derived state - Run 42's proof re-run under the new retrieval |
| Cross-project leakage | none |
| Registered / in service / computed / voting | 101 / 63 / 62 / exactly A1.7 and A1.8, all identical |
| Modules moving on the fixtures | exactly **three**: A1.7, A1.8 (`bac` newly visible) and A3.2 (`originalContingency` newly visible) |
| The two control corpora | **byte-identical before and after** |
| Sequence-bearing participant files | **none moved** |
| User-facing controls | **none added, moved or removed** |
| Synthetic package | RETAINED `OG-SYNTH-0.6` |
| Analysis schema | RETAINED `og-analysis-2026.08-v1` |

The census is not inferred from a diff: it drives the real routes -- upload, extract, compute,
read back -- on this tree and on the predecessor, and compares the two CSVs row by row.

## Two things recorded so a later session does not rediscover them

1. **`changeOrderCount` is strictly neither kind.** It is declared EVENT, and an event population
   accumulates: nothing supersedes it, and earlier periods' executed change orders have not
   stopped existing. The correct retrieval would be a third rule, a union at or before the period
   with latest-per-entity. The owner ruled at 1.3 that the rule is not to be defined and section 4
   is not to be widened. It stays PERIOD, as today.
2. **`totalFloat` and `consumedFloat` remain UNDETERMINED.** `field_registry.py:56` calls both a
   progress snapshot; `:202` says `schedule_update` revises what `time_phased_schedule`
   ESTABLISHED, which is the grammar `baselineEnd` was classified identity on. No module in
   service consumes either value, so the ambiguity costs nothing today.

## The scientific position

No input was invented, no fact fabricated, no qualification rule relaxed and no scientific method
changed. A module that abstains for want of its governed structure still abstains, with the same
reason and the same code. Every kind was read off a DECLARATION quoted with file and line, never
off what the implementation happened to do and never off what would make a module compute.

## Gate

15 blocker classes evaluated, 0 blocked. Artifact:
`research/freeze/run45_successor_freeze_gate.csv`.

The v25, v26, v27, v28 and v29 release records are preserved unchanged and still record their own
stamps.
