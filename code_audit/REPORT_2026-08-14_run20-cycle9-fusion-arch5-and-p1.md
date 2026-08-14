# Run 20 cycle 9: silence is not independence, one measurement is not three votes, and four
# methods that did not perform the method they name

Merged-main commit `001c710`, merging `e41697e` with `--no-ff`. Full suite on merged main: 110
suites, 9882/9882, all green. Nine of twelve cycles are done. Cycles 10, 11 and 12 remain and
have not been started.

## FUSION.1: the safe default, and why the other two were rejected

`fuse_signals` replaced a missing lineage record with `lineage_record(mid)`. That record carries
an EMPTY primitive set, names no lineage group, no parent and no dependency, so all four rules of
the pairwise dependence test answer False against every other signal. An undeclared signal was
therefore selected as its own INDEPENDENT BODY OF EVIDENCE. Saying nothing produced the single
strongest claim the model can make, and nobody made it.

Three candidates were considered and two were rejected for reasons rather than preferences.

REFUSAL, returning nothing when any member is undeclared, discards a fusion that is largely
declared because one member is silent, and discards the adverse evidence in it. It converts a
modelling defect into an availability defect on the governed status.

ABSTENTION, dropping the undeclared signal, fails in the one direction that matters most: an
undeclared RED signal would make the fusion read GREENER than the evidence in hand. That is false
suppression, which cycle 5 exists to prevent.

EXPLICIT UNRESOLVED was chosen. The signal is kept and its most adverse reading is kept. Exactly
one thing is refused: the CERTAINTY that corroboration confers, which was never justified. All
undeclared signals form ONE unresolved body; that body is folded in with the IDEMPOTENT worst-band
operator and is never combined by Dempster rule, because Dempster rule is precisely the step that
requires the independence nobody declared. The condition is reported by name in
`unresolved_module_ids`, and `lineage_declared` is False.

Independence remains available but must be ASSERTED: `fuse_signals(assume_independent=True)`.
`dst_fuse` passes it, because its entire documented contract is a caller with genuinely
independent sources and nothing else to say about them, and it is the only caller that does. A
caller who asserts independence and a caller who merely forgot are no longer the same caller.

MEASURED. Three undeclared Amber signals were 0.9861 and are 0.7000. Two were 0.9273 and are
0.7000. An undeclared Red beside a declared Green reports Red, and an undeclared Green beside a
declared Red does not soften it. Adding an agreeing undeclared signal moves no mass at all. The
declared voting pair is unchanged at 0.7000 with conflict 0.0000, and two genuinely independent
declared bodies still corroborate. Seven mutations, zero survivors. 53 checks.

## ARCH.5: six siblings, and the difference between an arm and a body

The six are B2.2 Rough Sets, B2.3 Neutrosophic Logic, B2.4 Interval Fuzzy Sets, B2.5 Z-numbers,
B2.6 PLTS and B2.8 Belief Rule Base. B2.7 Plithogenic Sets and B2.9 Quantum Probability read the
same four arms and are DISABLED_UNSAFE, emit no signal on any project, and so have no signal
whose evidence there is anything to declare. That is the A2.1 precedent from cycle 5 and the
six-undeclared-modules precedent from cycle 8, and the disabled state was proved mechanically.

The register row carried a warning and it was obeyed: none of the six is a Dempster combination,
so B2.1 precondition does not transfer to them unaltered. What does transfer is the fact
underneath it, because evidence dependence is a property of ancestry and not of aggregation
syntax. The separation was re-established here BY EXECUTION, in BOTH schedule-index regimes,
using cycle 8 resolver, rather than inherited from cycle 7 write-up: with a planned value present
the index and trend arms intersect on the earned value, and with it absent they intersect on the
progress figures instead. Two bodies in both regimes, and the same three arms in one of them.

DUPLICATED INFLUENCE: found in all six. Three of the four arms are readings of one earned-value
measurement, so equal weight per arm gave that measurement three quarters of every vote. On the
Run 6 fixture B2.2 ratio is exactly 0.75, the boundary its lower-approximation test sits on, so
the duplication decided which side of the boundary it landed on. B2.4 duplication is INSIDE A
SINGLE ARM: the cost and schedule indices are two readings of one measurement and its per-band
maximum assembled a membership profile neither index asserts, taking the amber upper endpoint from
one reading and the red lower endpoint from the other. B2.8 duplication is INSIDE THE RULE
ANTECEDENTS: R1, R3 and R6 conjoin the index state with a cumulative sum computed over that same
index, so the rule base counted one measurement twice at the point where it decides which rule
fires at all, and the rule reached by the second count is the most extreme in the base.

SILENT REWEIGHTING: found in all six. Every aggregator divides by the number of arms it happens to
have. The division is KEPT, because a fabricated neutral for an absent arm is worse and this
programme refuses it, but the counts are now reported on every result. One threshold had to move
with it: B2.3 status rule was an ABSOLUTE count of two, written when four arms were counted, so it
meant two of four, one half. Left absolute it would have meant unanimity over two bodies, and a
project reading Red on its earned value with a clean document score would have reported GREEN.
That is false suppression and it is the failure this cycle was least willing to introduce, so the
threshold is expressed as the share it always was. It reproduces the old rule exactly on four
components and it also repairs the pre-existing reweighting, where three arms silently demanded
two thirds and two demanded unanimity.

ORDERING EFFECTS: none found. Measured over all 24 orderings of the four arms and over both
directions of module execution, and no module mutates the assembled package it is handed.

NO WEIGHT, correlation coefficient, reliability discount or tuned multiplier was introduced, and
that claim is checked against the emitted values rather than promised. No band moved on the Run 6
fixture for any of the six. The six known-answer derivations were reworked BY HAND beside the
workings they replace, and no working was deleted. Eight mutations, zero survivors. 108 checks.

## The four P1 implementation defects

A5.2 Sensitivity Analysis ranked three quantities of which only ONE was a sensitivity. The
cost-index driver perturbs the index by 0.05 either way and recomputes the estimate at completion.
The schedule term was the index distance from one, halved, and the document term was the raw risk
score; the estimate at completion is the budget over the cost index and is not a function of
either, so no perturbation of them could move it. The ranking compared an elasticity against two
raw levels, and both the top driver and the band were decided by whichever number won. It now
reports the one driver it perturbs, and reports the other two under their own names as LEVELS that
are not ranked and cannot set the band. Nothing was invented to fill the gap.

B1.1 Conservative Dominance applied a COUNTING rule: two or more Reds, or a breach with a Red
forecast, escalated, and everything else that was not uniformly Green read Amber. So a lone Red
signal read Amber and selected routine early-warning review. It now reports the most adverse band
any present signal reads, which is what dominance means and which has no parameter at all. It is
also idempotent, which matters because three of the four signals it reads are one body. Absent or
unrecognised evidence still cannot reach the calmest band: the pre-existing all-present-and-Green
requirement is kept exactly, and the first draft of the fix lost it, which is why that is a named
mutation. B3.1 governance projection is untouched and its decision-layer state is reported beside
the dominance state rather than silently reconciled.

B2.10 Pythagorean Fuzzy Sets applied the constraint to the RAW membership pair, took the hesitancy
from it, and THEN adjusted the pair, reporting the adjusted pair beside a hesitancy belonging to
the discarded one. At cpi = spi = 0.95 with a document risk of 0.8 the reported triple summed to
0.34 rather than 1. The order is corrected rather than the arithmetic, which is what the spherical
module in the same file already did.

B2.15 Possibility Theory did not normalise its distribution, so on some projects nothing was fully
possible, which is not a statement possibility theory can make; and its necessity was the
possibility less 0.30, a constant that is dual to nothing. The distribution is normalised by its
own supremum, a monotone rescaling proved over a sweep to leave every band where it was, and the
necessity is now the dual of the complement possibility.

Seven mutations, zero survivors. 125 checks.

## The two rows deliberately not closed

B1.4 Worst-N-of-M triggers on a FRACTION of the total, so every benign arrival can raise the count
needed and can switch an existing Red set off. The canonical rule has a k fixed by design, and
repairing it means CHOOSING k. There is no k in the controlling specification, none in this
repository and none in any cited source, and the 0.3 and 0.4 are themselves literals with no
provenance. PH.5 anomaly weights move with data availability, and governing them means fixing them
with no calibration evidence to fix them from. Both are carried forward, advisory, non-voting, and
reaching no governed status. A register count is not worth a fabricated constant.

## Guards

Three fired correctly and by name before anything was transcribed: the Run-20 production manifest
guard named both undeclared production files, and the Run-6 and Run-8 pinned-baseline guards named
the changed file. The Run-17 and Run-19 canonical proposition registers refused to let a repaired
finding pass silently, saying in terms that the disposition must be revised and not the test.

One was found VACUOUS and fixed. The manifest guard module-level check required a Run-20 note in
`test_run19_category_N.py`. Categories 1 and 6 have no such file, so a change to a category 1 or 6
module could have been declared with nothing anywhere demonstrating it, and the check that exists
to prevent exactly that would have failed for a missing file rather than passed for a present
note. It now looks up the suite that actually assesses the target, and a target assessed by no
suite at all is still a failure.

## Verification on merged main

110 suites, 9882/9882. Voting reads A1.7 and A1.8, count 2. ENABLED_QUALIFIED 2, ADVISORY_ONLY 90,
DISABLED_UNSAFE 8, DISABLED_EVIDENCE_UNDER_REVIEW 1. No concept-only module is activated. Material
Cost Variance remains DISABLED_EVIDENCE_UNDER_REVIEW. Every key in the shipped lineage table
resolves in the registry. Register 110 rows, 81 open.
