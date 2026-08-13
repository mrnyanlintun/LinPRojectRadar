# Run 20 cycle 7: four arms, two bodies of evidence

B2.1 was the last open P0D row. It combines four arms through Dempster's rule, and Dempster's
rule normalises by a conflict coefficient defined only between INDEPENDENT bodies of evidence.
Three of the four arms are readings of one earned-value body. Reading one body three times is not
three sources agreeing; it is one source quoted three times.

## What each arm actually reads, established by execution

The rule this cycle worked under is the owner's: dependence must come from actual evidence and
computation lineage, and not from module id proximity, category membership, shared field names or
schema similarity. So nothing here was settled by reading a declaration. Each arm was probed by
moving one fact at a time and observing whether the arm's reading moved.

| arm | reads | materially influenced by | body | verdict |
|---|---|---|---|---|
| index | the two indices only | earned value, actual cost, planned value | earned-value measurement | contributes the body |
| cost forecast | the eightieth-percentile overrun only | earned value, actual cost, planned value, document risk score | earned-value measurement AND document evidence | suppressed as dependent; it is the bridge |
| trend | the breach flag only | earned value, planned value, the reporting history | earned-value measurement AND reporting history | suppressed as dependent |
| document | the document risk score | document risk score | document evidence | REINFORCES: the one genuinely independent body |

The index arm and the document arm share nothing. The cost forecast arm touches both. **B2.1 is
the A={X}, B={X,Y}, C={Y} case in shipped production code**, which is why the separation had to be
the pairwise, non-transitive one cycle 6 built: a transitive closure would let the forecast arm
marry the two bodies and destroy corroboration that is really there.

Two findings came out of the probing rather than out of inspection. The trend arm's history
**ends with this period's own index**, so it shares this period's earned value and planned value
with the index arm and not merely older ones; that dependence is real and not a temporal
coincidence. And the cost forecast arm does **not** rest on the budget, though the module that
produces its number does: the arm reads a percentage of the budget, and that ratio is
scale-invariant in it. This cycle's own first draft declared the budget and the probe caught it.
A producer's declaration is not a safe substitute for asking what the consumer reads.

## The pinned numbers

Reproduced before any correction, as the cycle discipline requires.

| case | before | after |
|---|---|---|
| one reading of the earned-value body, plus the document body | Red 0.3974 | Red 0.3974 |
| a second reading of that same body added | Red 0.9526 | Red 0.3974 |
| a third reading added | Red 0.9646 | Red 0.3974 |
| the known-answer case, all four arms adverse | Red 1.00, conflict 0.21 | Red 0.93, conflict 0.31 |
| both bodies adverse | Red 1.00 | Red 0.93 |

The band never changed. What changed is the certainty attached to it, which was manufactured.

## The negative control for schema-based inference, executed and not asserted

Bayesian EAC's preflight requires the budget, the earned value, the actual cost and the cost
index. Its arithmetic reads the budget and the index. The earned value and the actual cost were
moved across four wide ranges, including to values that contradict the index sitting beside them,
and the posterior, the variance from budget and the band did not move by a rounding step; the
index, which it does read, moved it immediately, so the null result means something. Anything
inferring common evidence from a required or declared input schema would call that module a
reader of the earned value in its own right. It reaches the earned-value body honestly, through
the index being earned value over actual cost, and the primitive resolution is what establishes
that, never the field list.

A second negative control came out of the sweep. `monte_carlo_eac` accepts three trend inputs and
genuinely widens its spread when they are given; the only caller in production never gives them.
A schema reading would make the forecast arm derived from the trend arm's output. It is not. The
two arms are dependent for a different and real reason, and being right for the wrong reason is
not being right.

## A framework defect found and remediated inside the same cycle

Cycle 6 separated signals correctly and then absorbed each remaining signal into the **first**
selected body it depended on, in module-id order. B2.1 is where that showed. With the index arm
absent, the cost forecast arm was absorbed by name order into the DOCUMENT body, whose band then
became its adverse earned-value reading: a document body reading Red on no document evidence, and
Red belief driven from 0.3974 to 0.9526. That is false reinforcement arriving through the
absorption step rather than the separation step, and the first-in-order rule could not have been
right except by luck. A bridge is now absorbed into the body it shares the most primitive evidence
with, which is a set comparison over the identifiers the separation already uses and not a weight,
a threshold or a correlation estimate. Ties fall back to the declared body order, and the choice
is deliberately not made by which assignment gives the more or less adverse answer.

Every cycle 6 figure was remeasured afterwards and none moved.

## Mutation proof

Twelve mutations. **Two survived the first pass** and were closed with named checks rather than
explained away: restoring the vacuous mass an absent arm used to contribute, and reporting the
conflict coefficient as estimable when there is only one body for it to be estimated across.
Zero survivors on the rerun.

## The vacuous arm, which was this module's own lesson left half-applied

An absent arm used to contribute a quarter of the mass to each of the four states. That is not
ignorance, and Dempster's rule is not neutral to it: the same evidence gave a different answer
according to how many arms happened to be MISSING. The module's own comment already stated the
principle for the all-absent case. It now holds for the partial case too. The all-absent refusal
is unchanged, and the module's separate quirk of reading an absent document arm as a score of zero
is untouched, because that is a validated reproduction of the instrument and not this cycle's
defect.

## What did not change

No band, boundary, threshold or arm mass. The module is still non-voting and advisory and reaches
no governed status. Voting is still exactly two.
