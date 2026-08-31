# Retired module specifications — A3

Run 95. This file holds the specifications of modules in category A3 that have been RETIRED
from service. It exists so the history can still be read.

ARCHIVING IS NOT DELETION, and that is Run 43D's ruling applied to the written record rather than
to the registry. A retired module keeps its identifier — `registry.retired_modules()` still lists
it and every reference to it still resolves — and it keeps its specification too. The live
specification for this category keeps ONE LINE per retired module, recording that it was retired
and pointing here. Nothing else about the module's specification is changed: the sections below are
the text as it stood in the live specification, moved verbatim.

THE CONVENTION IS RUN 91'S, NOT A NEW ONE. Run 91 established `specifications/archive/<file>.md`,
mirroring the live filename, for `A5_system_dynamics.md` and `B4_decision_optimisation.md`. This
run follows it exactly and invents nothing.

A1'S PRECEDENT WENT THE OTHER WAY AND IS NOT FOLLOWED. `A1_cost_and_evm.md` records that A1.1
Monte Carlo EAC Forecast was retired at Run 43 and states that "A1.1 is deliberately absent from
this document". Its section was DELETED, not archived, and this run does not attempt to
reconstruct it — a reconstruction would be a composition, not a record.

## A3.1 — Reference Class Forecasting — RETIRED at Run 95, not in service

**Identity.** Live id `A3.1`. Method class `Reference_Class_Forecasting`. The outside view: what
comparable completed projects actually overran by, applied to this project's own forecast.

**Required inputs, by their exact `signal_inputs` field names.**
`referenceClassPopulation` — a mapping carrying the completed comparable projects, the inclusion
and exclusion criteria that put them in the class, the comparable outcome definition, the
normalization, each member's realised proportional overrun, the sample size, the data vintage,
and `governed_percentile` — the percentile of the historical outcomes that governs the uplift.
`bac` — the inside-view forecast of the cost at completion. There is no other source for it.

**Method.**
```
U_p              = the p quantile of the members' historical proportional overruns
AdjustedForecast = InsideViewForecast * (1 + U_p)
```
`p` is `governed_percentile` off the structure; it is never assumed. The quantile convention is
the one frozen for the whole v3 line in `canonical_v3.empirical_quantile`. **The project being
assessed may not be a member of the class it is compared against.**

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
with the standard note. Nine overrun multipliers were once literals in this file, so the
percentile, the debiasing factor and the band were the same numbers on every project in every
period; Run 7 removed the arithmetic and the ladder with it.

**Interpretation.** The reading says what this project's forecast becomes once the record of
comparable finished projects is allowed to speak. A large uplift is not a statement that this
project is badly run; it is a statement that projects of this class systematically overran, and
that the inside view has no standing to claim exemption without argument.

**Nothing to report.**
1. `referenceClassPopulation` absent or not a mapping: the two sentences above, with `W` = *"a
   reference class of completed comparable projects, with the criteria that put them in it and
   the overrun each of them finished with"*.
2. `bac` absent or not a number: `"No inside view forecast of the cost at completion has been
   reported for this project, so there is nothing for an outside view to adjust."`
3. `governed_percentile` absent from the structure: `"The reference class provided does not say
   which percentile of the historical outcomes governs the uplift, so no uplift is taken from
   it."`
4. Any defect inside the structure refuses in the words `canonical_v3` raises for that field,
   which name the field.

---

## A3.7 — Analogous Estimating Ratio — RETIRED at Run 95, not in service

**Identity.** Live id `A3.7`. Method class `Analogous_Estimating`. What this project would cost if
a named earlier project were adapted to it.

**Required inputs.** `analogEstimate` — a mapping, and the only input read. It must identify the
analog project, state its cost and provenance, state the comparability criteria, and carry the
normalization and adaptation factors.

**Method.**
```
AdaptedEstimate = AnalogCost * product of the stated adaptation factors
```
Each factor is reported by name with its value, and the combined factor is reported.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
with the standard note. What it replaced was a single scalar, `analogousOverrunPct`, applied to
the budget and banded — no analog selection, no comparability criteria, no adaptation factors.
The supplied contract states that a preloaded analog overrun percentage with no identified analog
is not canonical analogous estimating. **`analogousOverrunPct` is not read here.**

**Interpretation.** The reading is an independent order-of-magnitude check on the estimate,
traceable to a named project and to the stated reasons that project is comparable. Its whole value
is in the traceability; the number alone is worth nothing.

**Nothing to report.** The two `require_v3_structure` sentences, with `W` = *"an identified analogous
project with its cost, why it is comparable, and the factors that adapt it to this project"*. The
structure is also refused where it carries no identified project, no cost, or no adaptation
factors, in the words `canonical_v3` raises for that field.

---

## A3.9 — Inflation Adjustment Index — RETIRED at Run 95, not in service

**Identity.** Live id `A3.9`. Method class `Inflation_Adjustment`. What a named external price
index does to a stated cost exposure.

**Required inputs.** `externalCostIndex` — a mapping, and the only input read. **Every one of its
seven provenance fields must be stated or the structure is refused:** the named series, its
authoritative source, the geography, the commodity or cost scope, the base period, the current or
forecast period, and the data vintage. It must additionally carry `cost_exposure` — the amount of
cost the index is to be applied to.

**Method.**
```
EscalationFactor = Index_current / Index_base
AdjustedCost     = BaseCost * EscalationFactor
EscalationAmount = AdjustedCost - BaseCost
```

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
with the standard note. What it replaced was
`(materialCostCurrent - materialCostBaseline * progress) / (materialCostBaseline * progress)`,
floored at zero and published as a material escalation. That is this project's own price movement
against its own progress-scaled baseline: no geography, no time base, no authority and no index.
The supplied contract states that a baseline-to-current project material price ratio is not an
external inflation index and that **no external market index may be fabricated or hard-coded**.

**Interpretation.** The factor says what the market did to this class of cost between the base
period and the period being adjusted to, on the authority of the named series. Applied to the
stated exposure, it says how much of a cost movement was the market rather than the project.

**Nothing to report.**
1. Structure absent or not a mapping: the two sentences above, with `W` = *"a named external price
   index with its authority, geography, base period and the period being adjusted to"*.
2. `cost_exposure` absent from the structure: `"The price index provided does not say which cost
   exposure it is to be applied to, so no adjusted cost is reported from it."`
3. Any of the seven provenance fields missing: the module refuses in the words `canonical_v3`
   raises for that field, which name the field.

**One property a reader must be told.** **No index level appears anywhere in this repository's
production code.** Both index values come off the supplied structure. A specification applying this
module must never supply, recall or estimate an index level; if the structure does not carry it,
the module abstains.

---

