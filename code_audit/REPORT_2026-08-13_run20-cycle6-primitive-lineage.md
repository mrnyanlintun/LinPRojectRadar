# Run 20 cycle 6: dependence is not transitive, and the closure that said it was is replaced

One defect class, one commit. NO BAND, BOUNDARY, THRESHOLD OR ARITHMETIC RESULT OF ANY MODULE
CHANGED. What changed is which signals are treated as one body of evidence and which as two.

## What the owner overturned

Cycles 3 to 5 separated signals into bodies of evidence by taking the connected components of the
dependence relation. That is a transitive closure, and it asserts that if A depends on B and B
depends on C then A depends on C. Dependence is not transitive. For A resting on primitive source
{X}, B on {X,Y} and C on {Y}, A and C share nothing at all and may still corroborate each other.

## The defect was in production, not in a thought experiment

The three signals are in the shipped declarations.

* A is the to-complete performance index on the earned-value measurement.
* C is the overhead absorption rate on the indirect cost ledger, which cycle 5 had only just
  rescued from a false dependence declaration.
* B is the tornado risk ranking, which reads the earned-value indices and also the progress figure
  that scales C's denominator.

Measured on the closure, before this cycle:

| signals | bodies | belief on Amber | conflict |
|---|---|---|---|
| A and C | 2 | 0.9273 | 0.4414 estimable |
| A, B and C | 1 | 0.7000 | not estimable |

Adding the bridging signal destroyed corroboration that was really there, purely by existing. It is
the same harm cycle 5 found in a wrong declaration, arriving this time through the framework.

After the replacement, both rows read 2 bodies, 0.9273, conflict 0.4414 estimable.

## The declaration sweep came first, and three of thirteen were wrong

Every shipped declaration was read against what the module's arithmetic actually consumes, by
static analysis of the model source and by hand. Recorded in
`code_audit/run20_cycle6_primitive_lineage_sweep.csv`.

* **A1.3 Bayesian EAC** declared the planned value and the reporting history. It reads neither. It
  requires the budget, earned value, actual cost and the cost index, and its arithmetic uses the
  budget and that one index. The declaration put it in the reporting-history body, where it was
  falsely dependent on the trend, filter and forecast modules and could not corroborate them, and
  it named a planned value it never reads, which asserts a dependence on every schedule reader that
  does not exist. Both directions of error in one record.
* **A1.5 ARIMA Forecast** declared the planned value. The series it extrapolates is the COST index,
  earned value over actual cost. Declaring the planned value asserted a dependence that is not
  there while omitting the actual cost hid one that is.
* **PH.5** was keyed by an audit target id, not a registry module id, so `lineage_for` could never
  have returned it for any signal the platform computes: a declaration no consumer could reach.
  The signal it meant is the portfolio Anomaly Score, D1.5, whose constituents are the portfolio
  outlier distance and rank and an optional cost trend term. It has never touched the two voting
  modules its record named. Re-keyed and redeclared.

The existence check that should have caught the third one was the thing that excused it: it
skipped any id beginning `PH.`. It now checks against the registry.

The other ten hold. A5.3's fact list is right; its derivation prose named a budget it never reads
and is corrected.

## The model as implemented

`server/app/simulation/lineage.py`. Records carry `primitive_source_ids`, `source_fact_ids`,
`source_document_ids`, `dependency_ids`, `parent_signal_ids`, `lineage_group_ids`,
`evidence_relationship` and `derivation_chain`.

`resolve_primitive_sources` applies the synthesis rule for every consumer at once: a derived,
synthesized, quality, governance or decision output creates no new primitive evidence, and its
primitive set is the union of its parents', resolved to a fixed point. Carrying another module id
does not manufacture a source.

`dependent` asks the question PAIRWISE and is never closed: two signals are dependent when their
resolved primitive sets intersect, or they share a declared lineage group, or one names the other
as a parent or dependency, or one names the other in its derivation chain. None of these is an
inference from a module id.

`evidence_bodies` replaces the closure. The bodies are a MAXIMUM SET OF PAIRWISE-INDEPENDENT
signals; every other signal is absorbed into exactly one body it depends on. So a duplicate, a
transform or a derived metric adds no body; a bridging signal is absorbed into one of the bodies it
draws from and can neither become a third body nor marry the two it bridges; and two genuinely
disjoint bodies both survive.

The selection is exact by search rather than greedy, because a greedy pass presented with the
bridge first selects it and then rejects both of the bodies it bridges, which is the same defect
wearing different clothes. The suite proves this by running all six orderings. The search carries a
declared node cap and an honest `body_selection_exact` flag rather than a silent fallback. The cap
is a computational bound on a search; no band, threshold or belief depends on its value.

The search is decomposed over the connected components of the dependence graph, and that is NOT
the closure returning. Signals in different components cannot constrain one another's selection, so
a maximum independent set is the union of the components' maximum independent sets. It is a
statement about the search and not about the evidence: WITHIN a component the answer stays
non-transitive, which is precisely why A, B and C, a single connected component, still separate
into two bodies and not one. Mutation M19 replaces the per-component answer with the component
itself and is caught. Without the decomposition the search fell back to greedy at a hundred
signals; with it, a hundred signals resolve exactly in a hundredth of a second.

Ties are broken by the lexicographically smallest member module ids, and deliberately NOT by which
separation produces the most or least adverse fused result. Selecting a separation by the answer it
gives is the boundary-moved-to-fit-an-example failure this programme refuses.

Dempster's rule is applied only ACROSS bodies whose primitive lineage sets are disjoint. Within a
body the existing idempotent most-adverse-reading treatment is unchanged. No correlation weight,
no calibration constant and no new parameter was introduced.

## The five oracle claims

`server/tools/test_run20_primitive_lineage.py`, run against hand-written records built from first
principles and independently against the shipped production declarations.

| claim | result |
|---|---|
| 1. A + B creates no independent corroboration | one body, 0.7000, conflict not estimable |
| 2. B + C creates no independent corroboration | one body, 0.7000, conflict not estimable |
| 3. A + C can genuinely corroborate | two bodies, 0.9273, conflict 0.4414 estimable |
| 4. A + B + C is not three independent bodies | two bodies, never three |
| 5. adding B to A + C cannot strengthen by bridging | 0.9273 and 0.4414, identical to A + C alone |

All five hold on the synthetic records and on the production trio A1.7, A5.3, A3.5, in all six
orderings.

## The acceptance test

Ten controls plus two rule-level duplicates, each scored on both directions. False duplicate
reinforcement 0, false suppression of genuine independent corroboration 0. Recorded in
`code_audit/run20_cycle6_acceptance_controls.csv`.

The independent Amber positive control still gives 0.9273 with conflict 0.4414 estimable, both
from the two-module production pair and from the three-module bridged case.

## Mutations

Twenty, in `server/tools/run20_cycle6_mutation_battery.py`, each byte-confirmed applied and each
restored. Zero survivors. Two are recorded honestly as having needed re-aiming: a first M13 changed
bytes without changing behaviour, because the search is exact regardless of the order it walks, and
was replaced by two mutations that genuinely substitute a greedy pass.

## Three suites were repaired rather than deleted

`test_run20_lineage_model.py`, `test_run20_lineage_declaration_truth.py` and
`test_run20_lineage_reproduction.py` were written against `lineage.partition`, which no longer
exists, and two of them asserted the closure behaviour the owner overturned. The cycles' findings
stand as historical evidence; the call sites moved onto the non-transitive separation and every
claim the decision reversed is corrected IN PLACE with the reversal stated, because a deleted check
is a check nobody can see was wrong. Two checks are now the exact negation of what they said:

* "dependence is transitive: two signals with no shared fact are one body when a third shares a
  fact with each" is now "dependence is NOT transitive", expecting two bodies.
* "remove the tornado ranking from the table and the two separate again" was true under the
  closure. It is now "removing the bridge changes the body count not at all".

Cycle 5's open methodological question, recorded rather than engineered away, is closed by the
owner decision and marked closed at the place it was raised.

## What this cycle did NOT do

B2.1, ARCH.3, the remaining P1 and P2 work and the 100-module re-audit are untouched and remain
open. The lineage block is complete; the run is not.
