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

**Bands. RUN 101, THE OWNER'S ORDER, SECTION 3.1. The module now asserts a band, on the
progress-normalized burn and on nothing else.** Provenance class **CONVENTION**.

| Band | Boundary on `NormalizedBurn` |
|---|---|
| Green | at or below **1.0** |
| Yellow | above 1.0 and **at or below 1.2** |
| Amber | above 1.2 and **at or below 1.5** |
| Red | above 1.5, **or** the contingency exhausted while work remains |

Every boundary is **inclusive on its upper side** and the module's stored `band_boundary` says so
in words. **Source, as the owner's order states it:** the owner's Run 101 order, section 3.1, on
the owner's stated authority — a contingency drawdown that outruns progress is the condition that
ends with no reserve and work remaining. **No standards clause fixes 1.0, 1.2 or 1.5**, which is
why the class is CONVENTION and not CODIFIED. `RESEARCH_1_threshold_bands_eight_metrics.md`
section 30 confirms the class and weakens the boundaries further: the heuristic *"is widely
repeated in practice, but no single standards clause fixes the 1.2/1.5 boundaries — those are
illustrative and should be calibrated to owner history."*

**The consumed fraction alone does not band.** Forty per cent consumed is healthy at half-time and
alarming at ten per cent complete, so where no progress is reported the figures are published and
**no band is asserted**, with the reason stored on the row. That is section 2's rule and it is not
a failure to band.

**One honest limitation, stated because it is a substitution and substitutions must be visible.**
The Red arm reads *"contingency exhausted before substantial completion"*. **Substantial completion
is not a figure this platform holds**: no module and no extraction contract carries the contract
milestone or its date. The arm is therefore applied against the **reported percent complete being
below one hundred**, and the boundary text says so in those words wherever it is printed. Where no
progress is reported the arm cannot fire and does not.

The ladder Run 4 recorded as uncited and Run 28 removed sat at 1.0, 1.3 and 1.6. **This is not
that ladder restored**: it is the owner's, at different boundaries, with its basis recorded and
travelling with every stored reading.

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

**Bands. RUN 101, THE OWNER'S ORDER, SECTION 3.2.** Provenance class **CONVENTION**.

| Band | Boundary on `ProductivityIndex` |
|---|---|
| Green | **at or above 0.95** |
| Yellow | at or above 0.90 and **below 0.95** |
| Amber | at or above 0.85 and **below 0.90** |
| Red | below 0.85 |

Every boundary is **inclusive on its lower side**, which is what makes 0.95 Green and 0.9499
Yellow. The direction of favourability is **upward**. **Source, as the owner's order states it:**
the owner's Run 101 order, section 3.2, on the owner's stated authority. **No standards clause
fixes 0.95, 0.90 or 0.85.** `RESEARCH_1` section 44 confirms the class and calls the 0.85 and 0.90
cut points *"conventional practitioner values, not codified."*

**Why the quantity matches, which section 2 requires be established rather than assumed.** The
order's words are *"earned hours over expended hours"*. What this module computes is earned output
per actual hour over planned output per planned hour — the same ratio expressed on an
installed-quantity basis rather than an hours basis. Numerator and denominator are both
hours-normalised production, the time basis is the reporting period for both, and one is
favourable upward. Quantity, denominator, time basis and direction all match.

What this module replaced was
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

**Bands. NONE, AND THE RUN 101 ORDER RULES IT SO EXPRESSLY. NO APPROVED THRESHOLD BASIS IS
CONFIGURED FOR THIS QUANTITY.**

The owner's Run 101 order, section 3.3: *"No published construction-controls basis exists, and the
owner has ruled against inventing one from audit-materiality convention. The module computes and
displays its variance and trend, asserts no band, and casts no vote."*

`RESEARCH_1` section 58 supports the ruling rather than merely permitting it: overhead has *"no
sourced basis for bands"*, and it lists *"leave the module bandless and report the raw variance"*
as an option — the owner has chosen it, and section 165 calls **"no published basis found"** the
correct answer.

**A ±5 / ±10 / ±15 per cent ladder, or any other, is expressly forbidden here**, and section 12.1e
of that order fails the run for attaching one. Audit-materiality convention measures a different
thing — whether a misstatement would change a reader's decision about a financial statement — and
applying it to a mid-execution overhead rate variance is substituting a threshold from a related
but different measure, which section 2 forbids in terms.

The module computes and displays both rates and both variances. The reason no colour accompanies
them is **stored on the row** as `band_withheld_reason` and is carried into the decision brief's
limitations, so a reader is told why rather than left to infer it.

What this module replaced was
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

**Required input added by Run 101.** `bac` — the budget at completion. **It was not read before.**
The banded quantity is the GAP between the P80 outcome and the budget at completion, so the budget
is now part of the reading: a P80 of nine million is comfortable against a ten-million budget and
ruinous against eight. Where no budget above zero is reported the percentiles are published and
**no band is asserted**.

**Bands. RUN 101, THE OWNER'S ORDER, SECTION 3.4.** Provenance class **CODIFIED**.

| Band | Boundary on the budget at completion |
|---|---|
| Green | **at or above** the P80 total cost |
| Yellow | below P80, with a gap **at or below +10%** |
| Amber | a gap **above +10%**, with the budget still **at or above** P50 |
| Red | below P50 |

Every boundary is **inclusive on its lower side**. **Source, as the owner's order states it:** DOE
Order 413.3B's P80 baseline requirement and the GAO Cost Estimating and Assessment Guide's
best practice of funding to a stated confidence level.

**The one place the order's four arms overlap, and where the figure that divides them came from.**
The order gives Yellow as *"BAC sits between P50 and P80"* and Amber as *"BAC is near or just above
P50"* — two descriptions of the same interval, and it gives no figure for the division.
`RESEARCH_1_threshold_bands_eight_metrics.md` sections 66–70 supply one, on the gap
**gap = (P80 − BAC) / BAC**: Green gap ≤ 0; Yellow gap 0 to about **+10%**; Amber about +10–20%;
Red above +20%. **The Yellow/Amber division is taken from that research at +10%.**

**THE ORDER'S ORDERING WINS WHERE THE TWO DIFFER, AND THEY DIFFER AT THE BOTTOM.** The order puts
**Red at a budget below the median**, not at a gap above twenty per cent, and that is what is
implemented. Only the division the order left qualitative is taken from the research.

**THE BASIS AND THE BOUNDARY DO NOT HAVE THE SAME PROVENANCE.** The **P80 concept is CODIFIED** —
DOE Order 413.3B and GAO-20-195G. The **+10% gap cutoff is not**: `RESEARCH_1` section 76 calls the
exact gap boundaries *"moderate … interpretive"*. Basis provenance **CODIFIED**; boundary
provenance **OWNER-CALIBRATED**. Both are stored on the reading and both are printed on the card.

**NEITHER FIGURE IS VERIFIED AGAINST ITS PRIMARY SOURCE.** The research reports state that a
primary-source verification pass — including the **DOE Order 413.3B section number** — was not
completed.

What this module replaced was `eac = bac / cpi`, then
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



## Stopped specifications

None. All seven modules in service in this category have unambiguous sources and are specified
above.
