# Category A1 — Cost and EVM Performance

Ten modules. This is the category that carries both of the platform's two voting modules, A1.7
TCPI and A1.8 Variance at Completion, so an error here does not mis-state one row on a ledger; it
moves the project's status.

## Reconciliation of the module count, stated before anything else

The A1 registry in `server/app/simulation/models.py` and `models_evm.py` holds **eleven** module
identifiers: A1.1 through A1.11. **A1.1 Monte Carlo EAC Forecast was retired at Run 43** and sits
in `DISABLED_CANONICAL_INPUT_NOT_GOVERNED` in `server/app/simulation/registry.py`, short-circuited
before the dispatch table is ever consulted. Eleven registered, minus the one retired, is the ten
specified below. A1.1 is deliberately absent from this document and is also absent from the
category tree the interface renders (`assets/js/taxonomy.js`, whose A1 list begins at `a1_2`).

## How a module answers

Every module returns exactly one of three shapes, and they are not interchangeable.

- **A reading with a band.** A number and one of Green, Amber, Red. Only A1.2, A1.7 and A1.8 can
  produce this.
- **A reading with no band — calibration pending.** The method ran, the figure is real, and no
  colour is claimed because no source in this repository or in any publication it cites specifies
  a boundary for the quantity being measured. Seven of the ten modules answer this way and always
  will until a boundary is sourced. This is not a defect and it is not an abstention: the figure
  is published, and it contributes no mass to the category's status.
- **An abstention.** The evidence is not there. The module names what it wants, in the exact
  words recorded against it below. No substitute figure is used in its place.

**A band is never to be attached to a module this document records as bandless.** The ladders
those modules once carried were drawn over a different quantity from the one they now compute.
Attaching a ladder would be inventing a threshold for a measure nobody has calibrated.

---

## A1.2 — CUSUM Anomaly Monitor

**Identity.** Live id `A1.2`. Method class `CUSUM`. A project manager would call this the
control chart on schedule performance: it asks whether the schedule index has drifted away from
plan by more than ordinary variation explains.

**Required inputs, by their exact `signal_inputs` field names.**
`spi` — the schedule performance index for this period.
`spiHistory` — the list of schedule performance index readings, one per earlier period. At least
two readings are required.

**Method.** A standard two-sided tabular CUSUM over `spiHistory`, deterministic given the series.

1. Discard any entry of the series that is not a finite number.
2. Target `T` = 1.0 — the schedule index at which work is exactly on plan.
3. Estimate `sigma` as the sample standard deviation of the retained readings (divisor n−1). If
   the series is shorter than two readings, or the estimate is not above zero, `sigma` is set to
   the documented floor of **0.05**, so that the slack `k` and the decision interval `H` stay
   meaningful on a short or flat series.
4. Slack `k` = 0.5 × sigma. Decision interval `H` = 5 × sigma.
5. Walk the series, holding two running sums, both floored at zero:
   `hi = max(0, hi + (x − T) − k)` and `lo = max(0, lo + (T − x) − k)`.
6. The statistic at each step is `max(hi, lo)`. The chart is breached the first time either sum
   exceeds `H`; the index of that step is recorded.
7. The reported reading is the maximum statistic over the whole series.

**Bands, and where each threshold came from.**

| Band | Condition |
|---|---|
| Red | the chart was breached — either running sum exceeded `H` at some point |
| Amber | not breached, and the maximum statistic reached 0.6 × `H` or more |
| Green | otherwise |

**The source of these thresholds, stated honestly: the slack of 0.5 sigma and the decision
interval of 5 sigma are the standard tabular CUSUM design constants, and the source carries them
as such. The 0.6 × H amber warning line has NO citation anywhere in the module's source.** It is
recorded here exactly as it stands in `cusum_status` and it is not to be changed by this run; but
it is a band without a source and it is named as one. The sigma floor of 0.05 is likewise
described in the source as "documented" without naming the document.

**Interpretation.** A breach says the schedule index has moved away from 1.0 persistently rather
than noisily, and names the period at which the accumulated departure first exceeded what the
project's own variability explains. A clean run says any departure so far is inside that
variability. It is a monitor of drift, not a forecast.

**Nothing to report.**
- If `spi` is absent: `"Insufficient data: upload required documents"`.
- If `spiHistory` is not a list, or holds fewer than two readings:
  `"Awaiting history (2 periods needed)"`.

**Two properties of this module that a reader must be told.**

1. **It is registered as stochastic and it is not.** `STOCHASTIC` in `models.py` names
   `{"A1.1", "A1.2", "A2.1"}`. `run_cusum` accepts a random generator and a seed and **uses
   neither**; `cusum_series` is documented in its own docstring as "Deterministic given the
   series". A1.2's presence in `STOCHASTIC` is not borne out by its source. Applying this
   specification is therefore deterministic, and the reproducibility question does not arise for
   it in the way it would for a genuinely sampled module.
2. **Its band is emitted in lower case and the fusion rule cannot read it.** `cusum_status`
   returns `"red"`, `"amber"`, `"green"`. `fusion.BAND_SEVERITY` holds capitalised spellings
   only, and `worst_band` filters to the keys it knows before taking the maximum, so an unknown
   token is dropped rather than ranked. A1.2's band therefore reaches the ledger but does not
   reach the category rollup. **This specification records the behaviour and does not change it.**
   A model applying this specification must emit the band in the same lower case the module does,
   so that this run alters nothing about what fusion sees.

---



## A1.5 — ARIMA CPI Forecast

**Identity.** Live id `A1.5`. Method class `ARIMA_Forecast`. A one-period-ahead forecast of the
cost performance index from an identified time-series model of the project's own history.

**Required inputs.**
`cpiHistory` — the list of cost performance index readings. Where it is absent the module falls
back to `cpi` as a one-element series exactly as the original JavaScript's truthiness did, and
then abstains on the length check. **A minimum of eight readings is required.**

**Method.** `canonical_v3.identify_arima`. The differencing order `d` is set by a stated
stationarity rule, not assumed. `(p, q)` are searched up to `(2, 1)`, estimated by conditional
least squares, and selected by **AICc** — the small-sample criterion, which favours parsimony on
a short cost-index history by construction. Stationarity and invertibility are checked and a model
failing either refuses. The Ljung-Box statistic at lag 1 and the residual autocorrelation are
reported with the forecast, together with a 95 per cent prediction interval where one can be
formed.

**Bands.** **None, and none may be attached.** The ladder this module once carried was drawn over
the output of a different estimator.

**Interpretation.** The forecast states where cost efficiency is heading one period out, given only
its own history. The order `(p,d,q)`, the AICc and the residual diagnostics are part of the answer,
not decoration: a forecast from a model whose residuals fail Ljung-Box is a forecast whose
uncertainty is understated.

**Nothing to report.**
- No history at all: `"Awaiting a cost performance history"`.
- Fewer than eight readings, or an identification that fails stationarity or invertibility: the
  sentence `identify_arima` raises for that condition.

**Forbidden implementation, recorded because it was the previous one.** Differencing once
unconditionally, regressing each difference on the one before to get a single `phi`, clamping that
`phi` to ±0.9, and forecasting one step. That is an AR(1) on first differences, which the
supervisory contract names in terms as the thing ARIMA must not be hard-coded as. Three
observations were enough to run it. Eight are now required.

---

## A1.6 — Earned Schedule

**Identity.** Live id `A1.6`. Method class `Earned_Schedule`. Where the project stands in TIME:
how many periods' worth of planned work has actually been earned, against how many periods have
elapsed.

**Required inputs.**
`timePhasedBaseline` — the cumulative value of work planned complete at the end of each period,
with its baseline version and approval source, and the actual time elapsed
(`actual_time_periods`) inside it.
`ev` — the earned value for this period, read from `signal_inputs` directly.

**Method.** Interpolation on the cumulative planned value curve, exactly as the contract states.
Find the period `C` such that `PV_C <= EV < PV_(C+1)`. Then
`ES = C + (EV − PV_C) / (PV_(C+1) − PV_C)`, `SV(t) = ES − AT`, and `SPI(t) = ES / AT`.

**Bands.** **None, and none may be attached.** The former ladder read a ratio of two reported
percentages, which is a different quantity from a time-based schedule index taken off a planned
value curve.

**Interpretation.** `ES` is the point on the plan the project has actually reached. `SV(t)`
expressed in periods is the honest statement of how far behind or ahead the project is, and unlike
the cost-denominated schedule variance it does not collapse to zero at the end of the project.

**Nothing to report.**
- `timePhasedBaseline` absent: `"Awaiting a time phased baseline: the cumulative value of work
  planned to be complete at the end of each period. This measure is named for a method that cannot
  be carried out without it, so no reading is reported and no other figure is used in its place."`
- `ev` absent: `"The value of work performed has not been reported for this period, so there is
  nothing to place on the planned value curve and no schedule position is read."`
- A non-numeric figure in the baseline: `"The time phased baseline provided carries a figure that
  is not a number, so no schedule position is read from it."`
- A computed `SPI(t)` of exactly zero is treated as insufficient rather than as a value, because
  the original JavaScript's `if (!SPI_t)` did so. A project at nought per cent actual progress
  abstains from Earned Schedule rather than reporting `SPI(t) = 0`. **This is faithful
  reproduction of the ported behaviour and is recorded, not repaired, by this run.**

**Forbidden implementation.** `actualPctComplete / plannedPctComplete`, published as "ES SPI(t)".
There is no curve in that, no interpolation and no earned schedule at all.

---

## A1.7 — TCPI (To-Complete Performance Index)

**Identity.** Live id `A1.7`. Method class `TCPI`. A project manager would call this "how
efficiently must we spend from here to finish inside the budget". **This module votes on project
status.**

**Required inputs, by their exact `signal_inputs` field names.**
`bac` — budget at completion. `ev` — earned value. `ac` — actual cost. All three are required;
the module's own check is `check_inputs(si, ("bac", "ev", "ac"))`.

**Method.**

    remaining_work   = BAC - EV
    remaining_budget = BAC - AC
    TCPI             = remaining_work / remaining_budget

**Precision is part of the method and is not negotiable.** `TCPI` is carried at the full precision
the application already holds and **the band is derived from that full-precision value.** A
separate display value, rounded to three decimals, exists for presentation only and nothing
analytical reads it.

> **This is a ruling of record and a model applying this specification must not round before
> banding.** Run 35 measured the defect: the band used to be assigned from the rounded value, and
> on the governed corpus **twenty-eight inputs read Green while the full-precision index was above
> 1.00 and implied Amber**. Because this module votes, that was a wrong vote and not a cosmetic
> rounding. Round for display, after the band has been decided, or not at all.

**Bands, with their thresholds and the source of each.**

| Band | Condition | Words carried with the reading |
|---|---|---|
| Green | `TCPI <= 1.00` | "within the efficiency already planned" |
| Amber | `1.00 < TCPI <= 1.10` | "above the efficiency planned" |
| Red | `TCPI > 1.10` | "beyond the improvement a cumulative cost index is observed to make" |

**1.00 — DEFINITIONAL, and the source states it in exactly these terms.** Project Management
Institute, *A Guide to the Project Management Body of Knowledge (PMBOK Guide)*, 6th edition, 2017,
section 7.4.2.2, and PMI's *Practice Standard for Earned Value Management*, 2nd edition, 2011.
TCPI is the cost performance the remaining work must achieve to meet the stated financial goal. At
or below 1.00 the remaining budget is sufficient at the efficiency already planned; above 1.00 the
project must do better than planned for the rest of the work. The source specifies this boundary,
not merely the metric.

**1.10 — SOURCED NUMBER, APPLIED BY INFERENCE, and the inference is stated rather than hidden.**
Christensen, D. S. and Heise, S. R., "Cost Performance Index Stability", *National Contract
Management Journal*, 25(1), 1993, pp. 7-15: on a large defence acquisition sample the cumulative
cost performance index does not change by more than 0.10 from the twenty per cent completion point
to the end of the project. The number 0.10 is the source's own. The inference this platform draws
from it, and it is an inference: a demand for cost efficiency more than 0.10 above what is
currently planned asks for a movement in the cumulative index larger than the one that study
observed, so it is not supported by the remaining work. That is the same reasoning defence
earned-value practice applies when it compares TCPI against CPI; this module has no CPI term, so
the 0.10 is applied to the planned efficiency of 1.00.

**No source was found for the boundaries this module carried before — 1.05, 1.10, 1.20. They were
removed rather than re-cited. The band has three levels because two boundaries are sourced; a
fourth level would need a third boundary and there is not one.**

**Interpretation.** The reading is the cost efficiency the remaining work must achieve to finish
within budget. Green: the remaining budget is sufficient at the efficiency already planned. Amber:
the project must beat its own plan for the rest of the work, but by an amount a cumulative cost
index has been observed to move. Red: the required improvement is larger than that study observed
a cumulative index to make, so the budget is not recoverable by efficiency alone.

**Nothing to report. Six conditions, each with the exact words it reports in.**

1. Any of `bac`, `ev`, `ac` absent: `"Insufficient data: upload required documents"`.
2. `bac <= 0`, or not a number: `"No cost efficiency is measurable for the remaining work: the
   budget at completion is reported at or below zero, which is not a budget the remaining work can
   be measured against. No substitute figure is used in its place."`
3. `ev < 0`, or not a number: `"No cost efficiency is measurable for the remaining work: the
   earned value is reported below zero, and the budgeted value of work performed cannot be
   negative. No substitute figure is used in its place."`
4. `ac < 0`, or not a number: `"No cost efficiency is measurable for the remaining work: the
   actual cost is reported below zero, and a cost incurred cannot be negative. No substitute
   figure is used in its place."`
5. `ev > bac`: `"No cost efficiency is measurable for the remaining work: the earned value is
   reported above the budget at completion, and the budgeted value of work performed cannot exceed
   the value that was budgeted. No substitute figure is used in its place."`
6. `BAC - AC <= 0`: `"Awaiting a remaining budget to measure against: actual cost has reached or
   passed the budget at completion, so there is no remaining funding for the efficiency this
   measure states"`.

**Where each domain comes from, and each is definitional rather than chosen.** BAC > 0: it is the
authorised total budget of the work, and there is no cost efficiency that finishes remaining work
against a budget of nothing or less. EV >= 0: it is the budgeted value of work performed, and
negative work has not been performed. EV <= BAC: the same definition bounds it above. AC >= 0: it
is cost incurred, and a negative incurred cost is not a measurement of spending.

**No boundary moves and nothing is clamped.** An out-of-domain figure is **not** pulled back to the
nearest admissible value. Clamping would hand the module a number nobody reported, and it would
land, in every case found, in the favourable direction. The module refuses instead. The reproducer
Run 10 found: an actual cost reported below zero enlarges the denominator beyond the budget itself,
the ratio falls, and the module reads Green.

**Condition 6 is the one that most often fires in ordinary practice.** `BAC − AC` is exactly zero
when actual cost has reached the budget, which is the ordinary state of a project at completion
rather than an exotic one. This used to return Red with no ratio — a status manufactured from a
division that could not be performed and indistinguishable downstream from a Red that was
measured. **The honest output is no finding, not the worst finding.**

**Output fields.** `method_class: "TCPI"`, `status_color`, `tcpi` (canonical, full precision),
`tcpi_display` (three decimals, presentation only), and an `evidence_metric` sentence of the form
`"TCPI: <display>, the cost efficiency the remaining work must achieve to finish within budget,
<words>"`.

---

## A1.8 — Variance at Completion

**Identity.** Live id `A1.8`. Method class `VAC`. What the project is forecast to be over or under
its budget by, when it finishes. **This module votes on project status.**

**Required inputs.** `bac` — budget at completion. `cpi` — cost performance index. The module's own
check is `check_inputs(si, ("bac", "cpi"))`.

**Method.** The index-based forecast.

    EAC  = BAC / CPI
    VAC  = BAC - EAC
    VAC% = (VAC / BAC) * 100

Because the forecast is the index-based one, the percentage is an exact restatement of the index:
`VAC% = (1 − 1/CPI) × 100`. A boundary on the percentage is therefore a boundary on CPI, exactly
and not approximately, which is what lets a sourced statement about CPI be cited here honestly.

`vac` and `vac_pct` are carried at full precision and the band is derived from `vac_pct` at full
precision. `vac_display` (whole dollars) and `vac_pct_display` (one decimal) are presentation only.

**Bands, with their thresholds and the source of each.**

| Band | Condition |
|---|---|
| Green | `VAC% >= 0` |
| Amber | `-11.111… <= VAC% < 0` |
| Red | `VAC% < -11.111…` |

**0 per cent — DEFINITIONAL.** PMBOK Guide 6th edition, 2017, section 7.4.2.2, and PMI's *Practice
Standard for Earned Value Management*, 2nd edition, 2011: variance at completion is the difference
between the approved budget and the forecast final cost, and a negative variance at completion is a
forecast overrun. The source specifies the boundary: at zero the forecast meets the budget, below
zero it does not.

**−11.11 per cent — SOURCED NUMBER, APPLIED BY INFERENCE.** Christensen and Heise, 1993, as above:
the cumulative cost performance index does not change by more than 0.10 from the twenty per cent
completion point to the end. The inference: an index below 0.90 forecasts an overrun the remaining
work is not observed to recover, because recovery would require the cumulative index to move
further than that study saw it move. **The threshold is computed as `(1 − 1/0.90) × 100`, not
written as a rounded figure**, so the boundary is the source's number and not a near one. It
evaluates to −11.111111111111114.

**No source was found for the boundaries this module carried before — −5, −10, −20 per cent. They
were removed rather than re-cited.**

**The stated limit of this citation, which belongs beside the band.** The stability finding is
conditional on the project being past twenty per cent complete, and **this module does not read
percent complete, so the condition is not enforced here.** Enforcing it would change the module's
input contract. Recorded as a stated limit of the band rather than left for a reader to discover.

**Interpretation.** Green: the index-based forecast finishes at or under the approved budget.
Amber: a forecast overrun, but one within the range a cumulative cost index has been observed to
recover. Red: a forecast overrun that would require the cumulative index to improve by more than
the source observed it ever to move, so it should be treated as an overrun that will be realised.

**Nothing to report.**
1. `bac` or `cpi` absent: `"Insufficient data: upload required documents"`.
2. `cpi <= 0`: `"Awaiting a cost performance index above zero: the forecast at completion is the
   budget divided by that index, which cannot be formed here"`. A zero index produces infinity
   arithmetic; a negative index produces a negative estimate at completion, hence a positive
   variance, hence **Green on a project that has recorded no earned value at all**. Both refuse.
3. `bac == 0`, making the percentage not-a-number:
   `"Insufficient data: upload required documents"`.

**Output fields.** `method_class: "VAC"`, `status_color`, `vac`, `vac_pct`, `vac_display`,
`vac_pct_display`, and an `evidence_metric` of the form
`"VAC: <money> over|under budget (<pct>%)"`.

---

## A1.9 — Budget Execution Rate

**Identity.** Live id `A1.9`. Method class `Budget_Execution_Rate`. Whether spending is running
ahead of, or behind, the profile somebody approved for it.

**Required inputs.**
`ac` — actual cost for this period, read from `signal_inputs` directly.
`expenditureBaseline` — an approved time-phased expenditure baseline: the amount planned to be
spent by the end of each period, with its version, its approval source, and a
`status_period_index` saying which period the project is being reported at.

**Method.** `ExecutionRatio(t) = AC(t) / ExpectedSpend(t)` and
`ExecutionDeviation(t) = ratio − 1`, where `ExpectedSpend` is read off the approved baseline at the
stated status period. Both figures are reported, with the baseline version and the approval source.

**Bands.** **None, and none may be attached.** The supervisory contract supplies none. This is
described in the contract as a transparent expenditure-control indicator and is expressly not
claimed to be a universal standardised statistical method. The boundaries the module carried before
were drawn over a progress-scaled figure rather than over this one.

**Interpretation.** A ratio above 1 means the project has spent more by this point than the
approved profile planned; below 1, less. It says nothing on its own about whether the work was
done — that is what A1.7 and A1.8 are for. Read together with earned value it distinguishes
"spending fast on work that is getting done" from "spending fast on work that is not".

**Nothing to report.**
- `ac` absent: `"Insufficient data: the actual cost has not been reported for this period."`
- `expenditureBaseline` absent: `"Awaiting an approved time phased expenditure baseline: the
  amount planned to be spent by the end of each period. This measure is named for a method that
  cannot be carried out without it, so no reading is reported and no other figure is used in its
  place."`
- The baseline present but carrying no status period: `"The approved expenditure baseline provided
  does not say which period the project is being reported at, so no planned amount can be read off
  it."`
- A computed execution rate of exactly zero is treated as insufficient rather than as a value,
  reproducing the original JavaScript's `if (!executionRate)`. Recorded, not repaired.

**Forbidden implementation.** `expected = bac × (actualPctComplete / 100)`. That treats spending as
planned to follow physical progress in a straight line, which no expenditure baseline asserts, and
it makes the ratio a function of the progress figure rather than of a plan anybody approved. The
contract names this in terms.

---


## A1.11 — Independent EAC Reconciliation Index

**Identity.** Live id `A1.11`. Method class `Independent_EAC_Reconciliation`. Approved rename at
Run 28 from "ICE Ratio". How far an independently prepared forecast of the final cost stands from
the project management team's own.

**Required inputs.**
`independentEacPair` — two separately prepared forecasts of the cost at completion, one from the
project management team and one prepared independently of it. **Each side must state all five
lineage fields: source, method, assumptions, model version and responsible party.**

**Method.**

    IER        = Independent / Management
    Divergence = (Independent - Management) / Management

**Independence is checked, not asserted.** Both sides must carry all five lineage fields, and the
two must differ **on the method AND on the responsible party**. Where the pair is absent,
incomplete, or not genuinely distinct, the module abstains.

**Bands.** **None, and none may be attached.** Reconciliation bands are named in the supervisory
contract as calibration dependent.

**Interpretation.** An index of 1 means the two forecasts agree. Above 1 means the independent
estimate is higher — the management forecast may be optimistic. The divergence, expressed as a
percentage, is the figure a governance board would act on; the two lineages beside it are what make
the divergence mean anything.

**Nothing to report.**
- `independentEacPair` absent: `"Awaiting two separately prepared forecasts of the cost at
  completion, one from the project management team and one prepared independently of it. This
  measure is named for a method that cannot be carried out without it, so no reading is reported
  and no other figure is used in its place."`
- Present but incomplete or not genuinely distinct: the sentence
  `canonical_v3.independent_eac_reconciliation` raises for that condition.

**Forbidden implementation, which was exactly the thing the contract names.**
`(bac / cpi)` divided by `(ac + (bac − ev))`. Both sides are arithmetic on one vector of four
reported figures, prepared by nobody, with no method, assumptions or responsible party attached to
either. The ratio was published as a reconciliation between an independent estimate and a
management one **when no second estimate existed anywhere.**

---

## Specifications stopped under section 5 of the Run 76 order

None in this category. All ten were derivable from their own source without a guess.

**Two contradictions were found and are recorded above rather than resolved**, because in each case
the source is unambiguous about what the code does and the contradiction is with something outside
the module:

1. **A1.2 is registered in `STOCHASTIC` and its source draws nothing from the generator or the
   seed.** The specification is written to the source, which is deterministic, and the registry
   entry is reported as unreconciled. It is not changed by this run.
2. **A1.2 emits its band in lower case, and `fusion.BAND_SEVERITY` holds capitalised spellings
   only**, so the band is dropped by the fusion rule rather than ranked. The specification
   preserves the lower case exactly so that applying it changes nothing about what fusion sees.

## A divergence between the interface's stated inputs and the modules' actual inputs

`assets/js/taxonomy.js` declares a `required` list for each A1 module, and for six of the ten it
does not match what the module's own `check_inputs` and structure requirements ask for. The clearest
cases: A1.6 Earned Schedule is declared as requiring `ev, pv, bac, actualPctComplete,
plannedPctComplete` and in fact requires `timePhasedBaseline` and `ev`; A1.9 Budget Execution Rate
is declared as requiring `ac, bac, actualPctComplete` and in fact requires `ac` and
`expenditureBaseline`; A1.11 is declared as requiring `bac, cpi, ev, ac` and in fact requires
`independentEacPair`. Those declarations are the pre-Run-28 input contracts, left behind when the
methods were replaced. **The specifications above are derived from the Python, which is what runs.**
This divergence is reported and not repaired by this run.
