# Category A3 — Cost Risk

Seven modules in service: A3.1, A3.2, A3.3, A3.5, A3.6, A3.7, A3.9. (A3.4 Material Cost Variance
and A3.8 Parametric Cost are implemented but are **not in service** — they are absent from
`registry.service_index()` — and are therefore not specified here.)

**Every one of the seven is bandless.** Six of them were rebuilt at Run 28 to compute the method
they are named for instead of a proxy, and in each case the quantity changed, so the ladder the
module used to carry was drawn over something it no longer computes. The seventh, A3.2, had its
ladder removed by the supplied contract itself, which states that no universal traffic-light bands
are supplied for a contingency burn and that threshold calibration belongs later.

**No band may be attached to any module in this category.** Each reports calibration-pending with
the standard note verbatim: *"The method this measure is named for has been carried out and the
figure is reported. No status colour is offered with it, because no boundary for this quantity has
been established from evidence, and a colour drawn from an unestablished boundary would read as a
judgement nobody has made."*

## The abstention sentences six of the seven share

Six modules take their defining structure through `canonical_v3.require_v3_structure`, which
raises in one of exactly two forms. Writing `W` for the module's own plain-words description of
its structure, given per module below:

- **Absent:** `"Awaiting W. This measure is named for a method that cannot be carried out without
  it, so no reading is reported and no other figure is used in its place."`
- **Present but not a mapping:** `"The information provided for this project in place of W is not
  in a form this measure can read, so no reading is taken from it."`

---

## A3.1 — Reference Class Forecasting

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

## A3.2 — Contingency Burn Rate

**Identity.** Live id `A3.2`. Method class `Contingency_Burn_Rate`. How much of the money set
aside for the unknown has been spent, and whether it is being spent faster than the work is being
done.

**Required inputs, by their exact `signal_inputs` field names.**
`originalContingency` — the contingency the project started with. Required.
`remainingContingency` — the contingency left. Required.
`actualPctComplete` — the reported percent complete. **Optional.** Its absence removes the second
figure only, not the reading.

**Method.**
```
C              = (originalContingency - remainingContingency) / originalContingency
NormalizedBurn = C / ProgressFraction,        when ProgressFraction > 0
ProgressFraction = actualPctComplete / 100
```
Oracle from the source: original 100, remaining 60, progress 0.50 gives a consumed fraction of
0.40 and a normalized burn of 0.80.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
with the standard note. The supplied contract states in terms that **no universal traffic-light
bands are supplied** for either figure and that threshold calibration belongs later. The
four-band ladder this module carried over the normalized burn at 1.0, 1.3 and 1.6 was recorded as
uncited by Run 4 and removed by Run 28. It is not to be restored by this run.

**Interpretation.** The consumed fraction says how much of the reserve is gone. The normalized
burn compares that against how much of the work is done: a figure above 1 says the reserve is
being consumed faster than the project is being built, which is the condition that ends with no
reserve and work remaining. Neither figure carries a colour and neither should be read as one.

**Nothing to report.**
1. Either contingency figure absent: `"Insufficient data: the original and remaining contingency
   amounts are needed, and at least one of them has not been reported for this period."`
2. `actualPctComplete` **present** and not a finite number: `"Insufficient data: the reported
   percent complete was reported in a form that is not a number."`
3. `actualPctComplete` present and above the maximum a percentage can take: `"Insufficient data:
   the reported percent complete was reported as a figure this quantity cannot take, so it is not
   read as evidence of anything. No substitute figure is used in its place."`
4. Original contingency not above zero: `"No original contingency above zero was provided, so the
   share consumed has no denominator and none is reported."`
5. Remaining below nothing or above the original: `"The remaining contingency provided is below
   nothing or above the original amount, so the two figures do not describe one contingency and no
   share is reported."`

**One property a reader must be told.** An absent progress figure and an impossible one are
handled differently on purpose. Absent, the consumed fraction is still published and the
no normalized burn is reported. Impossible — reported, but outside the range a percentage can
occupy — refuses the whole reading, because treating a wrong number as a missing one is how a
reading error becomes invisible.

---

## A3.3 — Labor Productivity Index

**Identity.** Live id `A3.3`. Method class `Labor_Productivity`. Output per labour hour, against
what was planned.

**Required inputs.** `productionOutputRecord` — a mapping, and the only input read. It must carry
the quantity installed, the quantity planned, the unit both are counted in, the hours each took,
and where the quantities came from.

**Method.**
```
ActualProductivity  = EarnedOutput  / ActualLaborHours
PlannedProductivity = PlannedOutput / PlannedLaborHours
ProductivityIndex   = ActualProductivity / PlannedProductivity
```
The output must be a comparable earned or installed quantity, an earned labour-hours basis, or
another explicitly equivalent production quantity. **Planned hours over actual hours alone is not
this metric**, and with no comparable output basis the answer is not estimable.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
with the standard note. What it replaced was
`((actualPctComplete / 100) * plannedLaborHours) / actualLaborHours`, whose numerator is not an
installed quantity but the planned hours scaled by a reported progress percentage — so the
"productivity" moved with whatever percentage was typed into a monthly report. **Neither
`actualPctComplete` nor `plannedLaborHours` is read here.**

**Interpretation.** An index below 1 says the crews are installing less per hour than the estimate
assumed. It is the earliest cost signal a project has, because it moves before the cost report
does, and it is stated in the unit the work is actually counted in.

**Nothing to report.** The two `require_v3_structure` sentences, with `W` = *"a record of production: the
quantity of work installed, the quantity planned, and the labour hours each of those took"*.

---

## A3.5 — Overhead Absorption Rate

**Identity.** Live id `A3.5`. Method class `Overhead_Absorption`. Whether indirect cost is being
absorbed over its allocation base at the rate that was planned.

**Required inputs.** `overheadAllocationBase` — a mapping, and the only input read. It must name
the allocation base, and carry the planned and actual overhead, the planned and actual amount of
the base, and where the driver figures came from.

**Method.**
```
PlannedRate            = PlannedOverhead / PlannedDriver
ActualRate             = ActualOverhead  / ActualDriver
RateVariance           = ActualRate - PlannedRate
RelativeRateVariance   = RateVariance / PlannedRate
```

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
with the standard note. What it replaced was
`indirectCostActual / (indirectCostPlan * actualPctComplete / 100)`. There is no driver anywhere
in that expression; overhead is absorbed over a base such as direct labour hours or direct cost,
and the supplied contract states in terms that indirect actual over indirect plan with no
allocation base **is not overhead absorption**.

**Interpretation.** The rate variance says how much more, or less, indirect cost each unit of the
base is carrying than the plan assumed. Under-absorption on a shrinking base is a different
problem from overhead overspend on a steady one, and reporting the rate rather than the total is
what keeps the two distinguishable.

**Nothing to report.** The two `require_v3_structure` sentences, with `W` = *"an overhead allocation
base: the planned and actual overhead and the planned and actual amount of the base it is absorbed
over"*.

---

## A3.6 — Cost Risk Analysis P80

**Identity.** Live id `A3.6`. Method class `Cost_Risk_Analysis`. The eightieth percentile of a
simulated total cost.

**Required inputs.** `costRiskModel` — a mapping, and the only input read. It must carry the base
cost components, the risk events, the probability of each, the impact distribution of each, and
the dependence policy where dependence is material.

**Method.**
```
TotalCost = BaseCostComponents + RealizedRiskEvents
```
Simulated over **20,000 trials**. In each trial every event occurs with its stated probability and,
when it does, its impact is drawn from its stated distribution. The reported figure is the
**empirical eightieth percentile** of the resulting total cost, under the quantile convention
frozen in `canonical_v3.empirical_quantile` and reported on the result as
`"right-continuous empirical inverse"`. The median and mean total cost are reported beside it.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
with the standard note. What it replaced was `eac = bac / cpi`, then
`uncertainty = max(0.03, abs(1 - cpi)) * 0.5` and `p80_eac = eac * (1 + uncertainty * 1.28)`: one
closed-form multiplication of a reported cost index by the standard normal 80th percentile, with
no component, no risk event, no probability, no impact and no trial anywhere in it. The supplied
contract states that a deterministic CPI uplift **is not** CRA P80.

**Interpretation.** The figure is the cost the project would not exceed in four runs out of five,
given the risks it has declared and the probabilities it has put on them. It is a statement about
the declared risk register and no better than that register is.

**Nothing to report.** The two `require_v3_structure` sentences, with `W` = *"a cost risk model: the base
cost components, the risk events that could occur, how likely each is and what it would cost"*.

**One property a reader must be told, and it bears on reproducibility.** This module **draws
random numbers**: `run_cost_risk` passes the registry's generator into `cost_risk_simulation` and
runs twenty thousand trials on it. **It is nonetheless absent from `models.STOCHASTIC`**, which
names only `{"A1.1", "A1.2", "A2.1"}`. The consequence is that its result set does not carry the
seed record that a stochastic module is supposed to carry. The module's own source is unambiguous
that it samples; the registry's set is what disagrees with it. **This specification records the
contradiction and changes neither.** In production the generator is seeded once from the scenario
and the period, so the reading is reproducible for a given project and period despite the missing
seed record.

---

## A3.7 — Analogous Estimating Ratio

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

## A3.9 — Inflation Adjustment Index

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

## Stopped specifications

None. All seven modules in service in this category have unambiguous sources and are specified
above.
