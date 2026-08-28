# Category A2 — Schedule Performance

Six modules in service: A2.1, A2.2, A2.3, A2.7, A2.8, A2.9. (A2.4, A2.5, A2.6, A2.10 and A2.11 are
implemented but are **not in service** — they are absent from `registry.service_index()` — and are
therefore not specified here.)

**All six are bandless.** Every one of them was rebuilt at Run 28 to compute the method it is named
for over a governed schedule structure, and in each case the quantity changed from the one the old
ladder was drawn over. Each reports calibration-pending with the standard note verbatim: *"The
method this measure is named for has been carried out and the figure is reported. No status colour
is offered with it, because no boundary for this quantity has been established from evidence, and a
colour drawn from an unestablished boundary would read as a judgement nobody has made."*

**No band may be attached to any module in this category.** A2.3 additionally reports two named
**policy lines**; those are not bands and must never be emitted as one. See A2.3.

## The abstention sentences

Four modules (A2.1, A2.7, A2.8, A2.9) take their structure through
`canonical_v3.require_v3_structure`; two (A2.2, A2.3) take it through `canonical.require_structure`.
The two helpers differ by one sentence and the difference is preserved here. Writing `W` for the
module's own plain-words description of its structure:

- **Absent, both helpers:** `"Awaiting W. This measure is named for a method that cannot be carried
  out without it, so no reading is reported and no other figure is used in its place."`
- **Present but not a mapping — v3 helper (A2.1, A2.7, A2.8, A2.9):** `"The information provided
  for this project in place of W is not in a form this measure can read, so no reading is taken
  from it."`
- **Present but not a mapping — v2 helper (A2.2, A2.3):** `"The W provided for this project is not
  in a form this measure can read, so no reading is taken from it."`

---

## A2.1 — PERT Network Criticality

**Identity.** Live id `A2.1`. Method class `PERT_Network_Criticality`. Which activities are
actually on the critical path once the durations are allowed to vary, and how often.

**Required inputs.** `scheduleNetwork` — a mapping, and the only input read. Each activity must
carry an identity, its predecessors, and a duration distribution or three-point estimate.

**Method.** Classical PERT moments per activity:
```
E[T]   = (O + 4M + P) / 6
Var[T] = ((P - O) / 6)^2
```
then **2,000 simulated trials**. In every trial each activity's duration is redrawn from its
three-point estimate and the **forward and backward passes are recomputed**. The criticality index
of an activity is the share of trials in which it is critical. The reported headline is the
activity with the highest index, ties broken by activity identifier, and the index is reported for
every activity. The eightieth percentile project finish is reported beside it.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending with
the standard note. The old ladder was drawn over a ratio of an eightieth percentile to a modal
baseline, which is not this quantity. Before Run 28 the module computed a criticality index from
three activity durations that were **literals in the source file, identical on every project**;
Run 10B removed that arithmetic and the ladder with it.

**Interpretation.** A criticality index says how often an activity decides the finish date, not
whether it is late. An activity critical in 40 per cent of trials is a real exposure even though a
single deterministic pass would not show it on the critical path at all. **Criticality is measured
here, not ranked.**

**Nothing to report.** The two sentences above, with `W` = *"the project's activity network: the
activities, the logic between them, and a duration for each"*. **`spi` and `bac` may not be used to
reconstruct topology** and are not read here.

**One property a reader must be told, and it bears on reproducibility.** This module genuinely
samples: it draws 2,000 trials from the registry's generator. It is one of the three modules named
in `models.STOCHASTIC`, so its result set carries the seed record, and in production the generator
is seeded once from the scenario and the period — never from the participant and never from how
many modules ran before it. **A specification applying this module cannot reproduce the sampling.**
Where the network is present, the honest answer from a specification-driven application is the
reading the platform's own simulation produced; a re-simulation performed elsewhere is a different
sample and must not be presented as the same figure.

---

## A2.2 — Line of Balance

**Identity.** Live id `A2.2`. Method class `Line_of_Balance_Velocity`. Repetitive,
location-based production: whether the crews following are catching the crews leading.

**Required inputs.** `lobStructure` — a mapping, and the only input read. It must carry the
locations in sequence, the crews working them, and for each line of work the activity, the location
or unit, the quantity, the crew, the **planned** production rate, the **actual** production rate,
and the sequence.

**Method.**
```
rate                    = change in units / change in time
minimum_separation_days = the smallest gap in time between the leading and the following line
                          across all locations
```
A line of work is **deteriorating** when its actual production rate is below its planned rate. Both
slopes are reported per line of work, and the count of deteriorating lines is reported.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
with the standard note. The minimum separation is the quantity the module's old boundaries were
drawn over and it is still computed; the production-rate ratio the module now also reports has no
established boundary in this platform. No colour is asserted on either.

**Interpretation.** The minimum separation is the buffer between trades: when it reaches zero the
following crew is standing on the leading crew and production stops. The planned-against-actual
slopes say whether that buffer is closing because of the crew ahead or the crew behind — a
distinction the module could not make before Run 28, when only actual rates were read and a crew
running at half its planned rate was indistinguishable from one running exactly to plan.

**Nothing to report.** The two sentences above, with `W` = *"a line of balance: locations in sequence, the
crews working them, and a production rate and start for each line of work"*.

---

## A2.3 — CCPM Buffer Health

**Identity.** Live id `A2.3`. Method class `CCPM_Buffer_Health`. How much of the project buffer has
been eaten, against how much of the critical chain has been completed.

**Required inputs.** `ccpmStructure` — a mapping, and the only input read. It must carry the
critical chain with its activities and a **sized** project buffer. **A buffer derived from a
performance index is not a sized buffer** and no such derivation is performed here.

**Method.**
```
BC  = B0 - Bt                       buffer consumed, in days
BCR = (B0 - Bt) / B0                buffer consumption ratio
```
reported alongside the percentage of the chain complete and the percentage of the buffer consumed,
the feeding buffer count and the chain activity count.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
with the standard note.

**The two policy lines, and why they are not bands.** The module computes and reports two
positions on the fever chart:
```
amber_policy_line = pct_chain_complete
red_policy_line   = pct_chain_complete + (100 - pct_chain_complete) / 3
```
and a `zone_relative_to_policy_lines` which takes exactly one of three values —
`"beyond the red policy line"`, `"beyond the amber policy line"`, `"inside both policy lines"`. The
module carries its own note on them verbatim: *"the amber line is chain completion, which is
definitional; the red line adds a third of the chain remaining, which is a policy choice no source
in this repository establishes"*. **These are reported as policy positions and must never be
emitted as `band`.** A specification applying this module reports the zone in the evidence
sentence, with `band: null` and `band_asserted: false`.

**Interpretation.** Buffer consumption ahead of chain completion means the project is spending its
protection faster than it is earning it. The zone says where that sits relative to two lines the
project's own policy drew, one of which is definitional and one of which is a choice.

**Nothing to report.** The two sentences above, with `W` = *"a critical chain with its activities and a
sized project buffer"*.

---

## A2.7 — Milestone Trend Analysis

**Identity.** Live id `A2.7`. Method class `Milestone_Trend`. How far each milestone has moved from
what was committed, and whether it moved again this period.

**Required inputs.** `milestoneForecastHistory` — a mapping, and the only input read. It must carry
**stable milestone identity across reporting periods** — an identity, not a name — and for each
milestone its original baseline date, its current approved baseline date, the report date, the
forecast date, the schedule version, and the actual date once achieved.

**Method.** Two variances, per milestone:
```
MV = forecast date - BASELINE date            variance against the commitment
MD = forecast date - PREVIOUS forecast date   drift since the last report
```
The reported headline is the largest `MV` across milestones and the count of milestones whose
forecast moved further out this period.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending with
the standard note.

**Interpretation.** `MV` is the measurement the method is named for: the distance between what was
promised and what is now expected. `MD` is the movement since last time. Reporting both is what
makes a rebaseline visible — before Run 28 the module reported the drift alone, matched milestones
by name, and a rebaseline erased the slip because no original commitment was retained. **The
original commitment history may not be erased after a rebaseline.**

**Nothing to report.**
1. Structure absent or not a mapping: the two sentences above, with `W` = *"a milestone forecast
   history: each milestone's committed date and the date it was forecast for in each reporting
   period since"*.
2. **A milestone forecast only once abstains rather than being reported as a trend**, in the words
   `canonical_v3.milestone_trend` raises for that condition. Insufficient repeated forecasts is not
   estimable for a trend claim.

**A known extraction gap, recorded and not fixed here.** On the owner's deployment this module
abstains on TST-007 because the forecast dates sit in a table the extractor does not read as
per-milestone data. **That is a document and extraction question, not a specification one.** The
specification above is correct and the abstention it produces is the correct behaviour until the
extractor supplies the structure.

---

## A2.8 — Look-Ahead Schedule Health

**Identity.** Live id `A2.8`. Method class `Lookahead_Health`. What share of the work planned in the
look-ahead window is actually ready to start.

**Required inputs.** `lookAheadSchedule` — a mapping, and the only input read. It must carry the
governed horizon, the status date, and **one row per activity** with its identity, whether its
constraints are cleared, and for an open constraint what category of constraint it is.

**Method.**
```
ReadyFraction = (P - C) / P = 1 - C/P
```
over `P` planned activities and `C` still carrying an open constraint. **The counts are derived
from the inventory**, not supplied as bare totals. Constraint categories are reported alongside.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending with
the standard note; the supplied contract states in terms that bands here remain policy and
calibration.

**Interpretation.** The ready fraction is a readiness indicator grounded in constraint removal.
**Percent Plan Complete may not be substituted for it** — PPC says what was finished, this says
what can be started. Before Run 28 the module read two bare counts and reported `C/P`, the
complement of the quantity the contract asks for, with no inventory behind the counts to audit.

**Nothing to report.**
1. Structure absent or not a mapping: the two sentences above, with `W` = *"a look ahead schedule:
   the window it covers, the activities planned in it, and whether each one still carries an open
   constraint"*.
2. No planned activities, an activity appearing twice, or a constraint status not stated: the
   module abstains in the words `canonical_v3.look_ahead_ready_fraction` raises for that condition.
   An unreliable constraint inventory is not estimable.

---

## A2.9 — Resource Loading Index

**Identity.** Live id `A2.9`. Method class `Resource_Loading`. Time-phased demand against capacity.

**Required inputs.** `resourceProfile` — a mapping, and the only input read. Every bucket must carry
its time period, its resource type, the planned or required demand, the available capacity, the
amount deployed where used, and the resource constraints.

**Method.**
```
LoadRatio_t = Demand_t / AvailableCapacity_t          for every bucket t
```
The **peak** load ratio is the headline, reported with the bucket and the resource type it belongs
to, together with the count of buckets above capacity out of the total.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending with
the standard note.

**Interpretation.** The peak is the headline because a profile that is over capacity in one period
is over capacity: the work in that period will not happen, whatever the average across the project
says. Before Run 28 the module reported `actualLaborHours / plannedLaborHours` — one ratio for the
whole project, with no time bucket, no resource type and **no capacity anywhere in it**, capacity
being the denominator the index is defined on. **Neither of those two fields is read here.**

**Nothing to report.** The two sentences above, with `W` = *"a time phased resource profile: for each
period and each kind of resource, the amount of work demanded and the amount available"*.

---

## Stopped specifications

None. All six modules in service in this category have unambiguous sources and are specified above.
