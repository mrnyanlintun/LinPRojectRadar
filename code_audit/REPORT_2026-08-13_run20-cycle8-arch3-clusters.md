# Run 20 cycle 8: ARCH.3, the identical required-input clusters

Merged-main commit `29e07ef`. Full suite on merged main: 107 suites, 9571/9571, all green.

## The question, and the answer that was refused

ARCH.3 grouped modules by the exact set of field names their preflight demands. That grouping is
a question, never a verdict. Every verdict below came from execution: each primitive fact moved
through the real production derivation, four multipliers per fact, the module's whole emitted
result compared. The probe is `server/tools/run20_cycle8_probe.py` and its output is
`code_audit/run20_cycle8_material_influence.csv`.

## The six clusters

| Cluster | Modules | Verdict |
| --- | --- | --- |
| Budget, earned value, actual cost and the cost index | A1.11, A1.3, A3.6, B3.2, plus disabled B4.2 | One earned-value body, reached through the cost index and never through a field name. B3.2 does not read the budget. B4.2 undeclared. |
| Budget and the two indices | B3.4, B4.3 | One earned-value body. Neither reads the budget. |
| The two indices and the document risk score | B2.10, B2.11, B2.14, B2.15, B2.16, B2.18, plus disabled B2.20, B4.1, B4.5, B4.6 | Five on the earned-value and document bodies. B2.14 does not read the cost index. Four undeclared. |
| The two indices | B2.12, B2.13, B2.17 | One earned-value body. |
| The two material cost figures | A3.4 disabled, A3.9 | Not a cluster. A3.9 is a body of one on the material cost record. |
| The change order log, declared in cycle 4 | A4.6, B3.5 | Positive control. Reached independently by this cycle's probe. |

## Where the field set and the evidence disagree, in shipped production code

B3.2, B3.4 and B4.3 all demand the budget and none of them reads it: each reports a percentage of
the budget, and the ratio is scale-invariant in it. B2.14 demands the cost index and does not read
it at all. A field-set reading would have declared four false dependences. The Bayesian EAC
negative control was re-executed and holds.

## The schedule index has two ancestries

`extraction_merge` derives the schedule index from the earned value over the planned value, and
falls back to actual over planned progress when no planned value exists. So the same module on the
same code rests on the earned value on one project and on the two progress figures on another. A
record keyed only by module id is wrong in one regime whichever ancestry it names. Records now
declare `derived_index_reads`, carry the union when no evidence is in hand, and
`lineage.resolve_for_evidence` narrows to the branch the evidence selects. The resolution can only
narrow, never add.

## What moved and what did not

Three cluster modules, all Amber, all on one earned-value body: undeclared they fused as three
bodies and drove Amber belief 0.7000 to 0.9861; declared, one body at 0.7000. The band never
changed. A cluster module against the material cost body is still two bodies, so real
corroboration survives. False reinforcement 0, false suppression 0. No band, boundary, threshold
or arithmetic result of any module changed.

## Instrument defects found in this cycle

The probe's own first version compared the band alone and scored four real dependences as absent.
One mutation changed bytes without changing the verdict and was re-aimed rather than counted. Two
existing guards fired correctly and by name. All four are recorded in
`code_audit/run20_anti_fossilization_register.csv`, which this cycle created.

## New register row

FUSION.1 at P1: the combination rule does treat an undeclared signal as independent, because an
empty primitive set intersects nothing. The ARCH.3 row said otherwise and was wrong. Exposure is
bounded and the bound was measured: only the two voting modules reach the fusion, and both are
declared.
