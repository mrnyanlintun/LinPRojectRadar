# Run 20 cycle 4 — two advisory modules that rest on another module's evidence now say so

Continues Run 20 from merged main `ee2e683`.

## The exit block

```
modules whose lineage is newly declared                  = 4, the two findings and their two
                                                           partners, because a partition needs
                                                           both members
bands swept per pair                                     = 4 of 4, swept and not sampled
same or dependent lineage cases increasing evidential
  strength                                               = 0
Change Order Frequency with Contract Modification Frequency
  Green  0.8000 -> duplicate before 0.9722 -> after 0.8000
  Yellow 0.7000 -> duplicate before 0.9267 -> after 0.7000
  Amber  0.7000 -> duplicate before 0.9273 -> after 0.7000
  Red    0.8340 -> duplicate before 0.9787 -> after 0.8340
Sensitivity Analysis with Tornado Risk Ranking             identical figures
conflict a pair reported against itself                  = 0.4414 before, not estimated at all after
positive control, an independent Amber body              = 0.9273, unchanged, two bodies, conflict
                                                           estimable
bands, boundaries or arithmetic results changed          = 0
voting modules                                           = 2, unchanged
mutations                                                = 8, M22 to M29, each byte-confirmed,
                                                           each a named red, each restored green
full regression                                          = 103 suites, 8929 checks, all green
working tree                                             = clean
```

## What was open, and what this cycle actually closes

Run 19 recorded two lineage findings and Run 20 cycle 3 left both open: Change Order Frequency was
`DUPLICATE_WITH_8.5` and Tornado Risk Ranking was `DUPLICATE_OF_5.2_EVIDENCE`. Cycle 3 built the
framework to express exactly this and then used it only on the path that votes, so the framework
existed and these four modules declared nothing at all.

This cycle declares lineage. **It rebands nothing.** The method-label mismatches these modules
carry are untouched and remain open at P1: a raw count with no exposure is still not a frequency,
and a ranking that evaluates no output at any input's low or high value is still not a tornado.
A lineage declaration is a statement about which body of evidence a reading rests on. It is not a
repair of the reading, and the pinned module outputs in the suite are there so that a future cycle
cannot quietly turn one into the other.

## The duplication, established rather than assumed

Change Order Frequency and Contract Modification Frequency read the **same three governed fields**,
compute the **same** scope-growth expression from the same two contract sums, and report the same
change count. They differ only in the thresholds they band it with, which is why on one and the
same project they return **different colours**: on the cycle's fixture, six modifications and eight
per cent growth, one reads Yellow and the other reads Amber. That is not two sources disagreeing.
It is one body of evidence read two ways, and it is now recorded as a within-body disagreement and
resolved to the more adverse reading in both orders, never scored as conflict.

Sensitivity Analysis and Tornado Risk Ranking share most of a body: the same earned-value figures
behind the same two indices, and the same document risk score. Tornado Risk Ranking adds the two
progress figures, and it is not computed FROM the sensitivity signal, so it is declared CORRELATED
rather than a transform. The partition does not depend on that distinction, because the shared
facts settle it. The label is recorded because a label is a claim, and a claim is not evidence.

## The oracle, and the correction the oracle itself needed

The declared facts are checked against **execution**, not against a hand-written expectation: for
every governed field behind a declared fact, withholding the field must make the module abstain.

That oracle **called a true declaration false**, on three checks, and the finding is recorded
rather than quietly relaxed. Tornado Risk Ranking is handed a cost index and a schedule index as
fields and is never handed the earned value, yet it rests on the earned value, which is precisely
what the lineage model says a source fact is: what the signal ultimately rests on and not its
immediate argument. A ratio is never a fact. The oracle is two-armed now: a fact read directly must
make the module abstain when withheld, and a fact reached through a supplied ratio must have that
ratio's own definition written into the derivation chain, so the path from the fact to the reading
is written down and not merely asserted. Neither arm is derived from the expression the declaration
is built from.

## Mutations

| id | mutation | caught by |
|---|---|---|
| M22 | the Change Order Frequency declaration removed | the pinned historical defect returns, 25 checks |
| M23 | Tornado Risk Ranking relabelled INDEPENDENT | the three relationship checks; the partition still held |
| M24 | its source facts renamed so they no longer intersect the partner's | the fact checks and the shared-fact disclosure |
| M25 | the two index definitions removed from the derivation chain | the through-a-ratio arm of the oracle, 3 checks |
| M26 | the declared evidence body removed, leaving the shared facts | only the disclosure check; the partition still held |
| M27 | BOTH defences removed | the defect returns exactly, 27 checks |
| M28 | the within-body reading inverted to the most favourable | the conservative comparison, both pairs, both orders |
| M29 | the cycle-4 declaration removed from the manifest | the widened cycle-set check |

M26 and M27 are a deliberate pair. The partition has two independent rules, a declared body and
intersecting facts, and removing either alone leaves it standing on the other, while removing both
restores the defect exactly. That is what proves neither rule is dead code, and neither could have
been established by removing one and observing a green.

## The neighbour sweep, and what it found

The sweep was mechanical rather than by inspection: every module was grouped by the exact set of
fields its own preflight requires. **Six clusters of modules rest on an identical required-input
set, and only the pair this cycle declares is declared.** The largest is ten modules on the cost
index, the schedule index and the document risk score. Five modules share the budget, earned value,
actual cost and cost index, of which one declares anything.

An identical required-input set is not by itself proof of one body of evidence, but it is the
signature both confirmed findings carry. It is opened as register row ARCH.3 at P1 and **not
remediated here**: every module in it is non-voting and advisory, several are disabled outright,
and the combination rule does not assume independence for an undeclared signal, so none of it can
reach a governed status. Each declaration needs its own derivation chain and its own execution
oracle, which is a cycle of its own and not a rider on this one.

**A second structural gap, in cycle 3's own guard.** The manifest's cycle-set check exists to catch
a cycle that forgets to declare itself, and it read the cycles off the baseline-file declarations
only. Cycle 4 changes nothing but a file cycle 3 CREATED, which has no baseline row to differ from,
so cycle 4 would have declared itself nowhere and that check would have stayed green while it did.
It is cycle 3's finding one level further out. A new production file now declares the tuple of
cycles that have changed it, the check reads those too, and M29 turns it red.

**No new fossilized suite.** One property is recorded rather than asserted away: a lineage record's
tuples return from a JSON round trip as lists, so a record does not compare equal to its own round
trip. Nothing stores these records today and equality across a serialisation boundary was never a
contract of the model, so what is asserted is that every field survives with the same contents.

## What is complete and what remains

Complete: the lineage disclosure of 4.6 and 5.3 and of their two partners; the register, the
transitions, the cycle record, the lineage results, the neighbour sweep, the fault-injection rows
and this report; and the manifest gap.

Remaining: the P1 method-label mismatches on all four of these modules, which this cycle
deliberately did not touch; ARCH.3, the five undeclared clusters; B2.1; and the rest of the
register in its own order, ending in the mandatory complete 100-module re-audit. Run 21 has not
been launched.
