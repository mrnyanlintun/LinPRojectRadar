# Category A2 — Schedule Performance

Five modules in service: A2.1, A2.7, A2.8, A2.9 and A2.12. (A2.2 through A2.6, A2.10 and A2.11
were REMOVED FROM THE REGISTRY at Run 96 — "retired means retired" — and are not specified here.
Their identifiers are NOT reused: their names are recorded in sealed freeze records, and reusing
one would make a sealed record name two different modules by one identifier. A2.12 is the lowest
identifier never used, and that is why this category's identifiers have a gap.)

**THIS OPENING WAS STALE AND IS CORRECTED BY RUN 103.** Until this run it read "Six modules in
service" and "All six are bandless. … No band may be attached to any module in this category."
Neither sentence had been true since Run 102, which banded all four modules in service on the
owner's ruling; the specification had not been edited since Run 96. Production code is the truth
and the code had moved. The correction is recorded rather than made silently.

**Every module in this category now asserts a band**, each on a threshold the owner has
configured and none on a published construction standard. Each band's boundary, basis,
provenance class and threshold source travel on the row.

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

**Bands (Run 102, kept unchanged by Run 103).** On the criticality index, adverse upward: below
0.20 Green; 0.20 to below 0.50 Yellow; 0.50 to below 0.80 Amber; 0.80 and above Red. Each
boundary is inclusive on its lower side. **These are the owner's configured tolerances and are
not a published standard.** The old ladder Run 28 removed is not restored: it was drawn over a
ratio of an eightieth percentile to a modal baseline, which is a different quantity.

**The hard override, and why it is evaluated against an IMPOSED finish.** Red where the
deterministic schedule has zero or negative total float on the controlling path — but that is
measured against the **imposed completion date the network states**, never against the backward
pass alone, whose float on the critical path is zero by construction when no date is imposed.
Where the network states no imposed date the override is **not evaluable, is not applied, and
the reading says so**. Run 103 did not overturn this reading.

**GATED, RUN 103.** This module runs **only after the network validates** and **only where
duration uncertainty is stated** — a three-point estimate or a duration distribution for every
activity. Absent either, it is **Not Assessed** and says which condition failed; A2.12 Critical
Path Analysis still reports on the same network. Before Run 103 the module fell back to a single
deterministic pass when three-point durations were missing and reported a criticality index of
1.0 or 0.0 from one trial — a deterministic critical-path flag wearing a stochastic measure's
name. **PERT is never a substitute for Critical Path Analysis.**

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

**Bands (Run 103).** The **same hybrid rule A2.12 uses, from the same function** — the owner's
ruling that two modules banding the same quantity must not band it differently. Working-day slip
bands lead; the percentage guardrail is a floor; the committed-milestone override is absolute;
the posture is the **worst of** them. The quantity banded is the worst milestone variance against
its **approved** baseline, in working days, which is the same quantity A2.12 bands as forecast
completion slip.

Run 102 gave this module percentage-only bands (2, 5 and 10 per cent of remaining duration). The
owner ruled at Run 103 that percentage-only is too coarse, and the ratio is now the **guardrail**
rather than the band.

**The denominator, and the contract that supplies it.** The guardrail needs remaining planned
duration. Run 102 measured that **no document stated it**. Run 103 grew `schedule_update`'s
extraction contract with `remaining_planned_duration_days` and `remaining_duration_basis`, both
printed cells. Where the record states neither, the **guardrail is not evaluable and says so** —
it is never passed as a zero, and no denominator is derived from a clock. The working-day slip
band still governs in that case, which is the point of the hybrid.

**The hard override needs the milestone's class and it must be STATED.** Contractual, regulatory,
turnover, owner-committed or required. A milestone whose record does not say which of those it is
cannot be judged against the condition, and its class is **never inferred from its name**.

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

**Bands (Run 102).** On the ready fraction, with the blocked-critical hard override. The
boundaries and the override are recorded on the row; they are the owner's configured tolerances
and are not a published standard.

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

**Bands (Run 102).** On the peak load ratio, with the zero-float-overload hard override. The
boundaries are the owner's configured tolerances and are not a published standard.

**Interpretation.** The peak is the headline because a profile that is over capacity in one period
is over capacity: the work in that period will not happen, whatever the average across the project
says. Before Run 28 the module reported `actualLaborHours / plannedLaborHours` — one ratio for the
whole project, with no time bucket, no resource type and **no capacity anywhere in it**, capacity
being the denominator the index is defined on. **Neither of those two fields is read here.**

**Nothing to report.** The two sentences above, with `W` = *"a time phased resource profile: for each
period and each kind of resource, the amount of work demanded and the amount available"*.

---

---

## A2.12 — Critical Path Analysis

**Identity.** Live id `A2.12`. Method class `Critical_Path_Analysis`. The deterministic
controlling path through the project's own schedule network, its float, and its forecast finish
against the approved baseline.

**Why the identifier is A2.12 and not A2.2.** A2.2 through A2.6, A2.10 and A2.11 existed and were
removed from the registry at Run 96. Their names live on in sealed freeze records — A2.2 Line of
Balance and A2.3 CCPM Buffer Health are named in the Run 28 freezes — so reusing one of those
identifiers would make a sealed record name two different modules by one identifier. A2.12 is the
lowest identifier never used.

**Required inputs.** `scheduleNetwork` — a mapping, and the only input read. The supported
flattened schedule export must carry, per activity: the activity id, the duration, the
predecessor references with relation type and lag, and the calendar; and on the export itself:
the calendar list, the approved baseline finish, and — for A2.1 PERT beside it — three-point
durations.

**Network assembly and diagnostics.** The network is built on canonical activity ids.
**Failures are REPORTED and NEVER repaired.** No inferred links, no dropped rows, no best-effort
path. The scheduler corrects the source; the platform names which rows made it unreadable.
`canonical_v3.schedule_network_diagnostics` reports, in ONE pass, with the affected source rows
or activity ids beside each: activities read, activities accepted, missing activity id, duplicate
activity id, dangling predecessor, dangling successor, self link, cycle, missing duration,
negative duration, unreadable predecessor list, unrecognised relation type, unreadable lag,
disconnected components, invalid calendar.

**When the network is invalid, BOTH this module and A2.1 PERT are Not Assessed**, with the
diagnostics as the stated reason, and Information Completeness Ratio reports the schedule fields
or rows that prevented analysis.

**The deterministic calculation.** On a valid network, for every activity: earliest start,
earliest finish, latest start, latest finish, total float (LS − ES), free float (earliest
successor start − activity finish), a critical flag where total float is at or below the stated
tolerance, and a near-critical flag within the configured low-float band. Relation types FS, SS,
FF and SF are honoured on the start or finish each names, and lags shift the constraint. For the
project: the controlling path (the longest valid start-to-finish path), the forecast completion
from it, the baseline completion variance, and counts of critical, near-critical and
negative-float activities. Reported beside them: minimum and median float, the ten lowest-float
activities, and the logic-integrity result.

**The critical-flag tolerance is 0 working days and the near-critical band is 10 working days.
BOTH ARE OWNER-CONFIGURED and are stated here rather than inferred.** The near-critical band is
the owner's own Amber float band (1 to 10 days), so that "near critical" means the same thing as
the band that would colour it Amber.

**Bands — worst-of across four rules.** The most severe applicable result governs. Float and
forecast slip measure different exposures and are banded separately, then combined worst-of with
the percentage guardrail and the milestone override.

1. **Total float on the controlling path**, working days on the approved project calendar:
   `> 20` Green · `11 to 20` Yellow · `1 to 10` Amber · `<= 0` Red.
2. **Forecast completion slip**, current forecast finish minus approved baseline finish, working
   days: on or before baseline Green · `> 0 to 10` Yellow · `> 10 to 20` Amber · `> 20` Red.
3. **The percentage guardrail** — slip as a share of remaining planned working duration. **A
   FLOOR, NOT A BAND:** at least Yellow above 2 per cent, at least Amber above 5 per cent, Red
   above 10 per cent. It can raise the posture and can never lower it.
4. **The hard override:** Red if any contractual, owner-committed, turnover or required milestone
   is forecast later than its approved baseline date, whatever the day count.

The band basis is `owner_configured_construction_control_tolerance`. **These numbers are not
universal construction standards and are not described as any.**

**Why day bands lead and percentages guard**, recorded here because the owner's ruling requires it
to be: on a two-year project a 5 per cent slip is about 36 calendar days and 10 per cent about 73
— far too late for an early warning. Fixed day bands give control sensitivity; the percentage
keeps the rule sane on much shorter or much longer projects.

**A rule with no input is NOT EVALUATED and is NOT counted as Green.** Where the network states no
imposed or required completion date, the **float rule is not evaluable**: the backward pass
anchors on the network's own finish, so the controlling path's total float is zero by construction
and firing Red from it would measure the arithmetic rather than the schedule. That is the same
reading Run 102 gave A2.1's override and it is unchanged. Where no remaining planned duration is
stated, the guardrail is not evaluable. Each non-evaluable rule says so on the row.

**One rule, one copy.** A2.7 Milestone Trend bands the same forecast slip and calls the **same
function**. There is no second copy of the rule to drift.

**Nothing to report.** The two abstention sentences above, with `W` = *"the project's activity
network: the activities, the logic between them, a duration for each, the calendar, and the
approved baseline finish"*.

---

## Stopped specifications

None. All five modules in service in this category have unambiguous sources and are specified
above.
