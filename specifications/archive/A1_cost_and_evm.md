# Retired module specifications — A1

Run 95. This file holds the specifications of modules in category A1 that have been RETIRED
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

## A1.3 — Bayesian EAC — RETIRED at Run 95, not in service

**Identity.** Live id `A1.3`. Method class `Bayesian_EAC`. The Bayesian posterior for the cost at
completion: what the project's own reported performance says about the final cost, once combined
with a prior somebody stated and sourced.

**Required inputs.**
`bayesianEacModel` — a mapping on `signal_inputs`, carrying the prior mean, the prior variance,
the source of the prior, the observation, the observation variance, the observation model, and the
basis on which that variance was estimated.

**Method.** Conjugate normal-normal updating, performed in `canonical_v3.bayesian_eac_model`
against the supplied record. The prior, its source, the observation and the observation variance
all arrive on the input; none is manufactured here. The posterior mean, the posterior variance
and a 95 per cent credible interval are reported.

**Bands.** **None. This module asserts no band and none may be attached.** The posterior of a
governed model is not the quantity the module's former ladder — a percentage of budget — was
drawn over. The module returns calibration-pending: a figure, published, with no colour.

**Interpretation.** The reported figure is the estimate of final cost after the stated prior and
the project's observed performance have been combined, with an interval stating how wide the
remaining uncertainty is. It is only as good as the prior's stated source; that source travels
with the reading and must be shown with it.

**Nothing to report.**
- If `bayesianEacModel` is absent: `"Awaiting a stated prior for the cost at completion, with its
  source, and a stated observation model with the uncertainty of the observation. This measure is
  named for a method that cannot be carried out without it, so no reading is reported and no
  other figure is used in its place."`
- If it is present but not a mapping: `"The information provided for this project in place of a
  stated prior for the cost at completion, with its source, and a stated observation model with
  the uncertainty of the observation is not in a form this measure can read, so no reading is
  taken from it."`
- If any figure inside it is missing or is not a number, the module refuses in the words
  `canonical_v3` raises for that field, which name the field.

**What this module must not do, recorded because it once did it.** The earlier implementation used
a prior variance of `(bac × 0.15)²` and a likelihood variance of `(bac × (1 − cpi) / cpi)²`. Both
were designed constants literal in the source, identical on every project the platform holds, so
the posterior was a property of the file as much as of the project. Falling back to them is
forbidden. Where the record is absent the answer is an abstention.

---

## A1.4 — Kalman Filter SPI Smoother — RETIRED at Run 95, not in service

**Identity.** Live id `A1.4`. Method class `Kalman_Filter`. The filtered schedule index: the
best estimate of true schedule performance once the noise in individual period readings has been
accounted for.

**Required inputs.**
`kalmanStateSpaceModel` — a mapping carrying the starting estimate and its uncertainty, the
process variance `Q`, the measurement variance `R`, the stated source of each of those two
variances, and the readings taken.

**Method.** The scalar random-walk Kalman recursion, exactly as the contract states it:
`x_pred = x_prev`; `P_pred = P_prev + Q`; `K = P_pred / (P_pred + R)`;
`x_post = x_pred + K(z − x_pred)`; `P_post = (1 − K)P_pred`. Reported: the filtered state, the
posterior variance, the final gain, the full sequence of gains, the filtered path, and both
variances with their sources.

**Bands.** **None, and none may be attached.** `Q` and `R` are calibration items and were handed
to Run 33; a band drawn over the output of a filter whose variances are uncalibrated would be a
band over an uncalibrated quantity.

**Interpretation.** The filtered index says what schedule performance most likely is, as opposed
to what the latest single reading happened to be. The final gain says how much weight the filter
placed on that latest reading: a high gain means the reading dominated, a low gain means the prior
state did.

**Nothing to report.** If `kalmanStateSpaceModel` is absent: `"Awaiting a state space model for the
schedule index: a starting estimate, its uncertainty, the process and measurement variances, and
the readings taken. This measure is named for a method that cannot be carried out without it, so
no reading is reported and no other figure is used in its place."` If present but not a mapping,
the corresponding "is not in a form this measure can read" sentence.

**Forbidden fallbacks, recorded because they were the previous implementation.** `q = 0.01` and
`r = 0.1` as literals with no stated origin; a starting variance of 1.0 chosen the same way; and a
reported "trend" that was a two-period difference divided by two, which is not part of a Kalman
filter at all. None may be reintroduced.

---

## A1.10 — CPI Shrinkage Forecast — RETIRED at Run 95, not in service

**Identity.** Live id `A1.10`. Method class `CPI_Shrinkage_Forecast`. Approved rename at Run 28
from "Regression to Mean CPI". What this project's cost performance is likely to settle at, once
its own short record is pooled with what comparable projects achieved.

**Required inputs.**
`cpi` — this project's cost performance index for the period.
`cpiReferenceClass` — a governed reference population: the comparable projects, the cost
performance each achieved, the basis of class membership, the reference mean and variance, the
shrinkage weight, the method by which that weight was estimated, the data vintage, and the project
stage the estimator is used at.

**Method.** Statistical partial pooling toward a governed outside expectation:

    CPI_shrunk = w * CPI_project + (1 - w) * mu_reference,   0 <= w <= 1

Two conditions are checked rather than assumed: **the project being assessed may not be a member of
the class it is pooled toward**, and **a weight declared as fixed or hard-coded is refused
outright.**

**Bands.** **None, and none may be attached.** The final empirical weight calibration was handed to
Run 33.

**Interpretation.** The pooled figure is a less over-confident statement of cost performance than
this period's raw index, because a short record on one project is a noisy estimate. The weight says
how much of the answer is this project and how much is the class; the member count and the data
vintage say how much the class itself is worth.

**Nothing to report.**
- `cpiReferenceClass` absent: `"Awaiting a governed reference population of comparable projects
  with the cost performance they achieved, and the weight to place on this project's own reading.
  This measure is named for a method that cannot be carried out without it, so no reading is
  reported and no other figure is used in its place."`
- `cpi` absent: `"This project's own cost performance has not been reported for this period, so
  there is nothing to pool toward the reference population."`
- The class present but the project is a member of it, or the weight is declared fixed: the
  sentence `canonical_v3.cpi_reference_class` raises for that condition.

**Forbidden implementation, which did both forbidden things at once.**
`mean + (current − mean) × 0.5`, where the weight was the literal 0.5 and the "mean" was the mean
of **this project's own history**. Pooling a reading toward the mean of the same readings is not
partial pooling toward an outside expectation; it is a smoother, and it carries no reference
population at all.

---

