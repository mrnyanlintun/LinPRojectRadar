# Run 88 — Specifications for the retained roster, printed for audit

**Repository:** `/home/user/LinPRojectRadar`, branch `main`, starting commit **`a0b309a`** (`Run 87 report: the admission seam, the two document contracts, A6.4 measured not ruled`). `main == origin/main` verified by `git rev-parse`; tree clean at start.

**33 of 33 names resolved**, each to exactly one in-service module with exactly one specification section. **15 of 33 produce a reading today** on the richest stored `signal_inputs` row in the dev database; 18 abstain. Of the 15 that produce a reading, **3 carry a band** (A1.7 Red, A1.8 Red, A1.2 green) and one more bands outside the voting core (A4.2 Red, A4.3 Yellow); the rest are calibration-pending by ruling.

**This run changed nothing.** No source file, no specification, no code, no migration, no rename. The only file written is this report. `T6_HANDOFF.md` was read as ordered and was **not** modified.

---

## §5 — Findings, stated first

### §5.0 Two premises in the order's supporting material are false against the tree

Stated before the findings proper, because §6.5 requires it.

1. **The heading convention is `## <id> — <name>` (H2), not `### `.** A `grep -n '^###'` across `specifications/` returns exactly ONE line in the whole directory — `A4_document_derived_signals.md:417: ### A4.1 — Document Risk Score. STOPPED. Not specified.` Every one of the 63 live module sections is H2. Extraction was done on the H2 convention.
2. **"DSM rework propagation" is `A5.1`, not any `A5.4`-adjacent id, and the alias runs the other way.** The live id is `A5.1`, method class **`DSM_Rework_Cat5`**. The registry note on A5.1 reads *"absorbs former 3.2 DSM Rework Propagation (alias)"* — so `DSM_Rework_Propagation` is the RETIRED historical name and `DSM_Rework_Cat5` is the current method class. The order's supporting note had the direction of that alias reversed.

Confirmed true: "Rework feedback loop" is **A5.5** (A5.4 is `Scenario_Modeling`, a different module, not retained); "What-if scenario matrix" is **B4.4** (B4.5 `Decision_Sensitivity_Matrix` is not in the A-to-Z of B4's spec file at all — B4 specifies only B4.3 and B4.4).

### §5.1 Names that did not resolve, or resolved to more than one

**None. All 33 resolved to exactly one module.** Resolution was done on three independent keys agreeing: the registry `module_name`, the specification's own `## <id> — <name>` heading, and the `method_class` returned by the module at runtime. All 33 are in `service_index()` (63 in service, 101 registered).

One name needed judgement and it was not ambiguous: the owner's *"Contractor performance assessment"* resolves to **A6.4 `Contractor Performance Assessment Signal`** — the tree's name carries the trailing word *Signal*, which the owner's list drops. One candidate, not two.

**But the owner's nine category headings do not match the tree's, in two places, and one of those is substantive:**

| Owner's heading | Tree's category for the module it names | Match? |
|---|---|---|
| Cost and EVM Performance | A1 Cost & EVM Performance | yes |
| Schedule | A2 Schedule Performance | yes |
| Cost Risk | A3 Cost Risk | yes |
| Document Signals | A4 Document-Derived Condition Signals | yes |
| Delivery Quality | A6 Delivery Quality Performance | yes |
| Systems and Dynamics | A5 System Dynamics & Complexity | yes |
| **Evidence Quality** | **C1 Data Integrity** | **NO** |
| Signal Synthesis | B1 Signal Synthesis | yes |
| Decision Optimisation | B4 Decision Optimization | yes |

**"Evidence Quality — Information completeness ratio" is C1.5, in C1 Data Integrity — it is not in B2 Evidence Combination.** B2 has exactly one module in service, B2.18 MARCOS Ranking, which is not on the roster. This matters beyond naming: C1.5 carries the registry note 

> `authoring-time quality gate; not participant-facing; must not enter project status aggregation`

so the single module the owner filed under "Evidence Quality" is, by the tree's own record, **barred from the project status it appears to be retained to inform.** It is group **C** (Data & Evidence Health), not group B. The other 32 are group A or group B.

### §5.2 Retained modules with no specification file at all

**None.** All 33 have a specification section. The known casualty, **A4.1 Document Risk Score — `STOPPED. Not specified.`** — is *not* on the retained roster, so it is not a §5.2 finding here. It returns under §5.4, because a retained module depends on it.

The two A4 modules in service that the roster does **not** retain are **A4.1** (Document Risk Score, unspecified) and **A4.10** (Specification Conflict Density). The owner's eight Document Signals names cover the other eight of A4's ten.

### §5.3 Specifications that contradict each other

**No two retained modules claim the same computation.** The one historic duplicate pair that touched this roster — A4.6 Change Order Frequency against B3.5 Contract Modification Frequency, recorded at Run 20 as an advisory duplicate — was **dissolved at Run 29** and the dissolution is declared in `server/app/simulation/lineage.py`:

> `The pair with Contract Modification Frequency is therefore no longer a pair: B3.5 still reads the extracted sums, this one reads the register, and declaring them a transform of one body would assert a corroboration that has stopped existing.`

B3.5 is not retained in any case.

**One input name carries three different meanings across the roster, and it is worth the owner's eye:** the field `status`.

- In **A6.1** it is a *requirement's* compliance status inside `qualityRequirementRegister`.
- In **A6.4** it is the *assessment's lifecycle* status inside `contractorAssessmentRecord` (draft / final / etc.).
- In **B1.1** it is a *signal's band* — one of `Green Yellow Amber Red` or one of the five did-not-speak states.

These live inside different governed structures and so do not collide at runtime; it is a naming hazard, not a live defect. The same is true of `applicable` (A6.1 vs C1.5), `requirements` (A6.1 vs A6.3) and `provenance` (A6.1, A6.2, A6.3, A6.4). No genuine semantic contradiction was found between two retained specifications.

### §5.4 Retained specifications that depend on modules being dropped — THE FINDING THAT MATTERS

Six retained specifications name a module other than themselves. Four of those names are safe. **Two are not, and one of them is a break in the load-bearing part of the instrument.**

| Retained spec | Names | Retained? |
|---|---|---|
| A1.9 Budget Execution Rate | A1.7, A1.8 | both retained — safe |
| A6.3 Environmental Compliance Rate | A6.1 | retained — safe |
| A1.2 CUSUM | A1.1, A2.1 | **A1.1 DROPPED** (and retired at Run 43) |
| A3.6 Cost Risk Analysis P80 | A1.1, A1.2, A2.1 | **A1.1 DROPPED** |
| C1.5 Information Completeness Ratio | C1.1 | **C1.1 DROPPED** |
| B1.1 Conservative Dominance | B1.2, B1.4, B3.1 | **B1.4 and B3.1 DROPPED** |

**The serious one is B1.2 Weighted Voting, and the dependency is not visible in its own section — it is in the B1 file's preamble, which governs it.** `specifications/B1_signal_synthesis.md:9-13` states that B1.2, B1.3 and B1.4 read the **four assembled arms**, verbatim:

> Three of the four (B1.2, B1.3, B1.4) read the **four assembled arms** the signal package carries —
> `evm` the cost and schedule indices, `mc` the cost forecast, `cusum` the performance trend, `doc` the
> document risk score — resolved through `canonical_v5.governed_signals_from_project`, each with
> its identity, state, period, source provenance, evidence-lineage body, qualification state and
> abstention reason.

Resolved against the code — `server/app/simulation/arm_lineage.py:69-112`, which is where the arms' lineage is actually declared — those four arms trace to:

| Arm | Declared derivation chain begins | Status on the retained roster |
|---|---|---|
| `evm` | `ev,ac,pv` — raw earned-value facts | not a module; **safe** |
| `cusum` | **`A1.2`** | **retained** |
| `mc` | **`A1.1`** | **NOT retained — and already RETIRED at Run 43** |
| `doc` | `the document risk score` — i.e. **A4.1** | **NOT retained, and `STOPPED. Not specified.`** |

**So B1.2 Weighted Voting — a module the owner is retaining — is specified to synthesise four arms, two of which are produced by modules that are not on the retained roster. One of those two (A1.1) was retired three weeks ago and is short-circuited before dispatch; the other (A4.1) has no specification at all.** Half of what the retained synthesiser is defined to weigh comes from outside the roster. This is a break the owner needs before the drop, and it is exactly the case §5.4 was written to catch.

**B1.1 Conservative Dominance has the same shape with a different cast.** Its own section names **B1.4 Worst-N-of-M** and **B3.1 Agent-Based Governance Model**, neither retained. Note also that B1.1 is the ONE B1 module NOT in `spec_projection.COMPARISON_ONLY_MODULES` (which Run 87 set to `{B1.2, B1.3, B1.4}`) — so on the retained roster the owner keeps one B1 module that DOES set a category band (B1.1) and one that is excluded from the rollup as a comparison ensemble (B1.2). Retaining B1.2 retains a module the projection layer deliberately refuses to admit.

**A secondary break: the B1 qualification boundary.** `B1_signal_synthesis.md:64-93` states that every B1 module is wrapped in the dispatch table by `qualification_boundary.install`, which reads `evidenceQualification` from `signal_inputs` and **fails closed** when it is absent. That key is a Category-9 (C1-group) artefact. Both retained B1 modules therefore depend on the C-group assessment machinery, of which the roster retains only C1.5 — which is itself marked *must not enter project status aggregation*.

---

## The measurement basis, stated once

Every §4.1 line below is a **REAL** run of the production `registry.run_module(id, si, rand, period_cutoff)` dispatch — the canonical route — against a **real stored row**, not a fixture:

- **Row:** `computed_results.result_id = 01M11XEYX5V5S6CQSCSJBHBV6T`, project `507be211e77c465cb2eb638a79121938`, **period 8**, `period_cutoff = 2026-10-31`. This is the richest stored `signal_inputs` in the database (23,527 bytes, **97 keys**) — chosen deliberately for that reason, so that an abstention below is a real absence of evidence and not a thin row.
- **Database:** `server/dev.db` copied to the scratchpad as `r88.db` and read there. The repository copy was not written. `DATABASE_URL` was never pointed at production.
- **No `ANTHROPIC_API_KEY` is set** (verified: unset in the environment). Nothing below is a model output. No extraction was run this session, so the StubExtractor and the recorded applier were never reached — **there is no harness measurement in this report.** Every figure is arithmetic executed by production code on stored data.

The 97 keys the row actually supplies, for reference against every §4.2 line:

```
ac activitiesConstrained activitiesPlanned actualLaborHours actualPctComplete analogousBac
analogousFinalCost analogousOverrunPct bac baselineContractSum baselineEnd baselineStart
changeOrderCount consumedFloat contractModificationRegister costRating cpi cpiHistory
criticalDeficiencyCount criticalFindings docDate docRiskScore environmentalComplianceRate
environmentalIssuesDiscussed environmentalViolations ev events evidenceQualification
evmsApplicabilityEvidence expenditureBaseline floatRemaining indirectCostActual indirectCostPlan
itemsFailed itemsInspected longLeadAtRisk longLeadDelayed longLeadItemsTotal lookaheadWeeks
materialCostBaseline materialCostCurrent milestoneForecastHistory milestoneHistory ncrClosed
ncrExposureRecord ncrExposureRecordDerivation ncrIssued ncrOpen originalContingency oshaIncidentRate
outstandingActionItems overallRating overheadAllocationBase plannedLaborHours plannedPctComplete
productionOutputRecord pv qualityAuditScore qualityDeficienciesNoted qualityIssuesDiscussed
qualityRating remainingContingency resourceProfile revisedContractSum rfaApproved rfaAvgReviewDays
rfaOpen rfaRejected rfaResubmit rfaTotal rfiAvgResponseDays rfiCount rfiNumber rfiOldestOpenDays
rfiOpen rfiOverdue rfiPeriodDays rfiResponseTimeDays safetyActionsOpen safetyIncidentsDiscussed
scheduleRating sources spi spiHistory subcontractorComplianceScore subcontractorDisputes
subcontractorIssuesDiscussed submittalsRejected submittalsTotal timePhasedBaseline totalFindings
totalFloat totalManhours weatherDaysDiscussed weatherDaysLost workPeriodFrom workPeriodTo
```

---

## The thirty three specifications

# Cost and EVM Performance

## 1. TCPI → **A1.7 — TCPI**

**Identifier:** `A1.7` · **Method class:** `TCPI` · **Tree category:** A1 Cost & EVM Performance · **In service:** yes

**Where it lives:** `specifications/A1_cost_and_evm.md`, section `A1.7 — TCPI (To-Complete Performance Index)`, lines **270–377**.

### Specification text, verbatim

> ## A1.7 — TCPI (To-Complete Performance Index)
>
> **Identity.** Live id `A1.7`. Method class `TCPI`. A project manager would call this "how
> efficiently must we spend from here to finish inside the budget". **This module votes on project
> status.**
>
> **Required inputs, by their exact `signal_inputs` field names.**
> `bac` — budget at completion. `ev` — earned value. `ac` — actual cost. All three are required;
> the module's own check is `check_inputs(si, ("bac", "ev", "ac"))`.
>
> **Method.**
>
>     remaining_work   = BAC - EV
>     remaining_budget = BAC - AC
>     TCPI             = remaining_work / remaining_budget
>
> **Precision is part of the method and is not negotiable.** `TCPI` is carried at the full precision
> the application already holds and **the band is derived from that full-precision value.** A
> separate display value, rounded to three decimals, exists for presentation only and nothing
> analytical reads it.
>
> > **This is a ruling of record and a model applying this specification must not round before
> > banding.** Run 35 measured the defect: the band used to be assigned from the rounded value, and
> > on the governed corpus **twenty-eight inputs read Green while the full-precision index was above
> > 1.00 and implied Amber**. Because this module votes, that was a wrong vote and not a cosmetic
> > rounding. Round for display, after the band has been decided, or not at all.
>
> **Bands, with their thresholds and the source of each.**
>
> | Band | Condition | Words carried with the reading |
> |---|---|---|
> | Green | `TCPI <= 1.00` | "within the efficiency already planned" |
> | Amber | `1.00 < TCPI <= 1.10` | "above the efficiency planned" |
> | Red | `TCPI > 1.10` | "beyond the improvement a cumulative cost index is observed to make" |
>
> **1.00 — DEFINITIONAL, and the source states it in exactly these terms.** Project Management
> Institute, *A Guide to the Project Management Body of Knowledge (PMBOK Guide)*, 6th edition, 2017,
> section 7.4.2.2, and PMI's *Practice Standard for Earned Value Management*, 2nd edition, 2011.
> TCPI is the cost performance the remaining work must achieve to meet the stated financial goal. At
> or below 1.00 the remaining budget is sufficient at the efficiency already planned; above 1.00 the
> project must do better than planned for the rest of the work. The source specifies this boundary,
> not merely the metric.
>
> **1.10 — SOURCED NUMBER, APPLIED BY INFERENCE, and the inference is stated rather than hidden.**
> Christensen, D. S. and Heise, S. R., "Cost Performance Index Stability", *National Contract
> Management Journal*, 25(1), 1993, pp. 7-15: on a large defence acquisition sample the cumulative
> cost performance index does not change by more than 0.10 from the twenty per cent completion point
> to the end of the project. The number 0.10 is the source's own. The inference this platform draws
> from it, and it is an inference: a demand for cost efficiency more than 0.10 above what is
> currently planned asks for a movement in the cumulative index larger than the one that study
> observed, so it is not supported by the remaining work. That is the same reasoning defence
> earned-value practice applies when it compares TCPI against CPI; this module has no CPI term, so
> the 0.10 is applied to the planned efficiency of 1.00.
>
> **No source was found for the boundaries this module carried before — 1.05, 1.10, 1.20. They were
> removed rather than re-cited. The band has three levels because two boundaries are sourced; a
> fourth level would need a third boundary and there is not one.**
>
> **Interpretation.** The reading is the cost efficiency the remaining work must achieve to finish
> within budget. Green: the remaining budget is sufficient at the efficiency already planned. Amber:
> the project must beat its own plan for the rest of the work, but by an amount a cumulative cost
> index has been observed to move. Red: the required improvement is larger than that study observed
> a cumulative index to make, so the budget is not recoverable by efficiency alone.
>
> **Nothing to report. Six conditions, each with the exact words it reports in.**
>
> 1. Any of `bac`, `ev`, `ac` absent: `"Insufficient data: upload required documents"`.
> 2. `bac <= 0`, or not a number: `"No cost efficiency is measurable for the remaining work: the
>    budget at completion is reported at or below zero, which is not a budget the remaining work can
>    be measured against. No substitute figure is used in its place."`
> 3. `ev < 0`, or not a number: `"No cost efficiency is measurable for the remaining work: the
>    earned value is reported below zero, and the budgeted value of work performed cannot be
>    negative. No substitute figure is used in its place."`
> 4. `ac < 0`, or not a number: `"No cost efficiency is measurable for the remaining work: the
>    actual cost is reported below zero, and a cost incurred cannot be negative. No substitute
>    figure is used in its place."`
> 5. `ev > bac`: `"No cost efficiency is measurable for the remaining work: the earned value is
>    reported above the budget at completion, and the budgeted value of work performed cannot exceed
>    the value that was budgeted. No substitute figure is used in its place."`
> 6. `BAC - AC <= 0`: `"Awaiting a remaining budget to measure against: actual cost has reached or
>    passed the budget at completion, so there is no remaining funding for the efficiency this
>    measure states"`.
>
> **Where each domain comes from, and each is definitional rather than chosen.** BAC > 0: it is the
> authorised total budget of the work, and there is no cost efficiency that finishes remaining work
> against a budget of nothing or less. EV >= 0: it is the budgeted value of work performed, and
> negative work has not been performed. EV <= BAC: the same definition bounds it above. AC >= 0: it
> is cost incurred, and a negative incurred cost is not a measurement of spending.
>
> **No boundary moves and nothing is clamped.** An out-of-domain figure is **not** pulled back to the
> nearest admissible value. Clamping would hand the module a number nobody reported, and it would
> land, in every case found, in the favourable direction. The module refuses instead. The reproducer
> Run 10 found: an actual cost reported below zero enlarges the denominator beyond the budget itself,
> the ratio falls, and the module reads Green.
>
> **Condition 6 is the one that most often fires in ordinary practice.** `BAC − AC` is exactly zero
> when actual cost has reached the budget, which is the ordinary state of a project at completion
> rather than an exotic one. This used to return Red with no ratio — a status manufactured from a
> division that could not be performed and indistinguishable downstream from a Red that was
> measured. **The honest output is no finding, not the worst finding.**
>
> **Output fields.** `method_class: "TCPI"`, `status_color`, `tcpi` (canonical, full precision),
> `tcpi_display` (three decimals, presentation only), and an `evidence_metric` sentence of the form
> `"TCPI: <display>, the cost efficiency the remaining work must achieve to finish within budget,
> <words>"`.
>
> ---

### Measured

**1. Does it compute today.** **YES — computes.** Band: **Red**. Reading: TCPI: 3.5, the cost efficiency the remaining work must achieve to finish within budget, beyond the improvement a cumulative cost index is observed to make

**2. Named inputs no stored observation supplies.** **None** — every input this specification names by field name is present in the stored row.

**3. Governed structure?** **NO.** This module is defined on plain numeric facts a document states directly; it names no governed structure in `CANONICAL_STRUCTURE_KEYS` or any of the v3–v8 layers.

---

## 2. Variance at completion → **A1.8 — Variance at Completion**

**Identifier:** `A1.8` · **Method class:** `VAC` · **Tree category:** A1 Cost & EVM Performance · **In service:** yes

**Where it lives:** `specifications/A1_cost_and_evm.md`, section `A1.8 — Variance at Completion`, lines **378–448**.

### Specification text, verbatim

> ## A1.8 — Variance at Completion
>
> **Identity.** Live id `A1.8`. Method class `VAC`. What the project is forecast to be over or under
> its budget by, when it finishes. **This module votes on project status.**
>
> **Required inputs.** `bac` — budget at completion. `cpi` — cost performance index. The module's own
> check is `check_inputs(si, ("bac", "cpi"))`.
>
> **Method.** The index-based forecast.
>
>     EAC  = BAC / CPI
>     VAC  = BAC - EAC
>     VAC% = (VAC / BAC) * 100
>
> Because the forecast is the index-based one, the percentage is an exact restatement of the index:
> `VAC% = (1 − 1/CPI) × 100`. A boundary on the percentage is therefore a boundary on CPI, exactly
> and not approximately, which is what lets a sourced statement about CPI be cited here honestly.
>
> `vac` and `vac_pct` are carried at full precision and the band is derived from `vac_pct` at full
> precision. `vac_display` (whole dollars) and `vac_pct_display` (one decimal) are presentation only.
>
> **Bands, with their thresholds and the source of each.**
>
> | Band | Condition |
> |---|---|
> | Green | `VAC% >= 0` |
> | Amber | `-11.111… <= VAC% < 0` |
> | Red | `VAC% < -11.111…` |
>
> **0 per cent — DEFINITIONAL.** PMBOK Guide 6th edition, 2017, section 7.4.2.2, and PMI's *Practice
> Standard for Earned Value Management*, 2nd edition, 2011: variance at completion is the difference
> between the approved budget and the forecast final cost, and a negative variance at completion is a
> forecast overrun. The source specifies the boundary: at zero the forecast meets the budget, below
> zero it does not.
>
> **−11.11 per cent — SOURCED NUMBER, APPLIED BY INFERENCE.** Christensen and Heise, 1993, as above:
> the cumulative cost performance index does not change by more than 0.10 from the twenty per cent
> completion point to the end. The inference: an index below 0.90 forecasts an overrun the remaining
> work is not observed to recover, because recovery would require the cumulative index to move
> further than that study saw it move. **The threshold is computed as `(1 − 1/0.90) × 100`, not
> written as a rounded figure**, so the boundary is the source's number and not a near one. It
> evaluates to −11.111111111111114.
>
> **No source was found for the boundaries this module carried before — −5, −10, −20 per cent. They
> were removed rather than re-cited.**
>
> **The stated limit of this citation, which belongs beside the band.** The stability finding is
> conditional on the project being past twenty per cent complete, and **this module does not read
> percent complete, so the condition is not enforced here.** Enforcing it would change the module's
> input contract. Recorded as a stated limit of the band rather than left for a reader to discover.
>
> **Interpretation.** Green: the index-based forecast finishes at or under the approved budget.
> Amber: a forecast overrun, but one within the range a cumulative cost index has been observed to
> recover. Red: a forecast overrun that would require the cumulative index to improve by more than
> the source observed it ever to move, so it should be treated as an overrun that will be realised.
>
> **Nothing to report.**
> 1. `bac` or `cpi` absent: `"Insufficient data: upload required documents"`.
> 2. `cpi <= 0`: `"Awaiting a cost performance index above zero: the forecast at completion is the
>    budget divided by that index, which cannot be formed here"`. A zero index produces infinity
>    arithmetic; a negative index produces a negative estimate at completion, hence a positive
>    variance, hence **Green on a project that has recorded no earned value at all**. Both refuse.
> 3. `bac == 0`, making the percentage not-a-number:
>    `"Insufficient data: upload required documents"`.
>
> **Output fields.** `method_class: "VAC"`, `status_color`, `vac`, `vac_pct`, `vac_display`,
> `vac_pct_display`, and an `evidence_metric` of the form
> `"VAC: <money> over|under budget (<pct>%)"`.
>
> ---

### Measured

**1. Does it compute today.** **YES — computes.** Band: **Red**. Reading: VAC: $608,295 over budget (15.2%)

**2. Named inputs no stored observation supplies.** **None** — every input this specification names by field name is present in the stored row.

**3. Governed structure?** **NO.** This module is defined on plain numeric facts a document states directly; it names no governed structure in `CANONICAL_STRUCTURE_KEYS` or any of the v3–v8 layers.

---

## 3. Earned schedule → **A1.6 — Earned Schedule**

**Identifier:** `A1.6` · **Method class:** `Earned_Schedule` · **Tree category:** A1 Cost & EVM Performance · **In service:** yes

**Where it lives:** `specifications/A1_cost_and_evm.md`, section `A1.6 — Earned Schedule`, lines **228–269**.

### Specification text, verbatim

> ## A1.6 — Earned Schedule
>
> **Identity.** Live id `A1.6`. Method class `Earned_Schedule`. Where the project stands in TIME:
> how many periods' worth of planned work has actually been earned, against how many periods have
> elapsed.
>
> **Required inputs.**
> `timePhasedBaseline` — the cumulative value of work planned complete at the end of each period,
> with its baseline version and approval source, and the actual time elapsed
> (`actual_time_periods`) inside it.
> `ev` — the earned value for this period, read from `signal_inputs` directly.
>
> **Method.** Interpolation on the cumulative planned value curve, exactly as the contract states.
> Find the period `C` such that `PV_C <= EV < PV_(C+1)`. Then
> `ES = C + (EV − PV_C) / (PV_(C+1) − PV_C)`, `SV(t) = ES − AT`, and `SPI(t) = ES / AT`.
>
> **Bands.** **None, and none may be attached.** The former ladder read a ratio of two reported
> percentages, which is a different quantity from a time-based schedule index taken off a planned
> value curve.
>
> **Interpretation.** `ES` is the point on the plan the project has actually reached. `SV(t)`
> expressed in periods is the honest statement of how far behind or ahead the project is, and unlike
> the cost-denominated schedule variance it does not collapse to zero at the end of the project.
>
> **Nothing to report.**
> - `timePhasedBaseline` absent: `"Awaiting a time phased baseline: the cumulative value of work
>   planned to be complete at the end of each period. This measure is named for a method that cannot
>   be carried out without it, so no reading is reported and no other figure is used in its place."`
> - `ev` absent: `"The value of work performed has not been reported for this period, so there is
>   nothing to place on the planned value curve and no schedule position is read."`
> - A non-numeric figure in the baseline: `"The time phased baseline provided carries a figure that
>   is not a number, so no schedule position is read from it."`
> - A computed `SPI(t)` of exactly zero is treated as insufficient rather than as a value, because
>   the original JavaScript's `if (!SPI_t)` did so. A project at nought per cent actual progress
>   abstains from Earned Schedule rather than reporting `SPI(t) = 0`. **This is faithful
>   reproduction of the ported behaviour and is recorded, not repaired, by this run.**
>
> **Forbidden implementation.** `actualPctComplete / plannedPctComplete`, published as "ES SPI(t)".
> There is no curve in that, no interpolation and no earned schedule at all.
>
> ---

### Measured

**1. Does it compute today.** **YES — computes.** Band: **no band (calibration pending by ruling)**. Reading: Earned schedule 5.75 periods against 8 elapsed, a time based schedule index of 0.719 and a schedule variance of -2.25 periods

**2. Named inputs no stored observation supplies** (1): `actual_time_periods`

**3. Governed structure?** **YES — `timePhasedBaseline`.** It is **present** in the stored row. Could a document state it in words? **YES** — a time-phased baseline is a printed S-curve table of planned value by period.

---

## 4. Budget execution rate → **A1.9 — Budget Execution Rate**

**Identifier:** `A1.9` · **Method class:** `Budget_Execution_Rate` · **Tree category:** A1 Cost & EVM Performance · **In service:** yes

**Where it lives:** `specifications/A1_cost_and_evm.md`, section `A1.9 — Budget Execution Rate`, lines **449–492**.

### Specification text, verbatim

> ## A1.9 — Budget Execution Rate
>
> **Identity.** Live id `A1.9`. Method class `Budget_Execution_Rate`. Whether spending is running
> ahead of, or behind, the profile somebody approved for it.
>
> **Required inputs.**
> `ac` — actual cost for this period, read from `signal_inputs` directly.
> `expenditureBaseline` — an approved time-phased expenditure baseline: the amount planned to be
> spent by the end of each period, with its version, its approval source, and a
> `status_period_index` saying which period the project is being reported at.
>
> **Method.** `ExecutionRatio(t) = AC(t) / ExpectedSpend(t)` and
> `ExecutionDeviation(t) = ratio − 1`, where `ExpectedSpend` is read off the approved baseline at the
> stated status period. Both figures are reported, with the baseline version and the approval source.
>
> **Bands.** **None, and none may be attached.** The supervisory contract supplies none. This is
> described in the contract as a transparent expenditure-control indicator and is expressly not
> claimed to be a universal standardised statistical method. The boundaries the module carried before
> were drawn over a progress-scaled figure rather than over this one.
>
> **Interpretation.** A ratio above 1 means the project has spent more by this point than the
> approved profile planned; below 1, less. It says nothing on its own about whether the work was
> done — that is what A1.7 and A1.8 are for. Read together with earned value it distinguishes
> "spending fast on work that is getting done" from "spending fast on work that is not".
>
> **Nothing to report.**
> - `ac` absent: `"Insufficient data: the actual cost has not been reported for this period."`
> - `expenditureBaseline` absent: `"Awaiting an approved time phased expenditure baseline: the
>   amount planned to be spent by the end of each period. This measure is named for a method that
>   cannot be carried out without it, so no reading is reported and no other figure is used in its
>   place."`
> - The baseline present but carrying no status period: `"The approved expenditure baseline provided
>   does not say which period the project is being reported at, so no planned amount can be read off
>   it."`
> - A computed execution rate of exactly zero is treated as insufficient rather than as a value,
>   reproducing the original JavaScript's `if (!executionRate)`. Recorded, not repaired.
>
> **Forbidden implementation.** `expected = bac × (actualPctComplete / 100)`. That treats spending as
> planned to follow physical progress in a straight line, which no expenditure baseline asserts, and
> it makes the ratio a function of the progress figure rather than of a plan anybody approved. The
> contract names this in terms.
>
> ---

### Measured

**1. Does it compute today.** **YES — computes.** Band: **no band (calibration pending by ruling)**. Reading: Spending is $3,800,000 against the $3,930,000 the approved expenditure baseline plans by this point, an execution ratio of 0.967

**2. Named inputs no stored observation supplies** (1): `status_period_index`

**3. Governed structure?** **YES — `expenditureBaseline`.** It is **present** in the stored row. Could a document state it in words? **YES** — an approved expenditure baseline is a printed spend plan by period.

---

## 5. CUSUM anomaly monitor → **A1.2 — CUSUM Anomaly Monitor**

**Identifier:** `A1.2` · **Method class:** `CUSUM` · **Tree category:** A1 Cost & EVM Performance · **In service:** yes

**Where it lives:** `specifications/A1_cost_and_evm.md`, section `A1.2 — CUSUM Anomaly Monitor`, lines **36–104**.

### Specification text, verbatim

> ## A1.2 — CUSUM Anomaly Monitor
>
> **Identity.** Live id `A1.2`. Method class `CUSUM`. A project manager would call this the
> control chart on schedule performance: it asks whether the schedule index has drifted away from
> plan by more than ordinary variation explains.
>
> **Required inputs, by their exact `signal_inputs` field names.**
> `spi` — the schedule performance index for this period.
> `spiHistory` — the list of schedule performance index readings, one per earlier period. At least
> two readings are required.
>
> **Method.** A standard two-sided tabular CUSUM over `spiHistory`, deterministic given the series.
>
> 1. Discard any entry of the series that is not a finite number.
> 2. Target `T` = 1.0 — the schedule index at which work is exactly on plan.
> 3. Estimate `sigma` as the sample standard deviation of the retained readings (divisor n−1). If
>    the series is shorter than two readings, or the estimate is not above zero, `sigma` is set to
>    the documented floor of **0.05**, so that the slack `k` and the decision interval `H` stay
>    meaningful on a short or flat series.
> 4. Slack `k` = 0.5 × sigma. Decision interval `H` = 5 × sigma.
> 5. Walk the series, holding two running sums, both floored at zero:
>    `hi = max(0, hi + (x − T) − k)` and `lo = max(0, lo + (T − x) − k)`.
> 6. The statistic at each step is `max(hi, lo)`. The chart is breached the first time either sum
>    exceeds `H`; the index of that step is recorded.
> 7. The reported reading is the maximum statistic over the whole series.
>
> **Bands, and where each threshold came from.**
>
> | Band | Condition |
> |---|---|
> | Red | the chart was breached — either running sum exceeded `H` at some point |
> | Amber | not breached, and the maximum statistic reached 0.6 × `H` or more |
> | Green | otherwise |
>
> **The source of these thresholds, stated honestly: the slack of 0.5 sigma and the decision
> interval of 5 sigma are the standard tabular CUSUM design constants, and the source carries them
> as such. The 0.6 × H amber warning line has NO citation anywhere in the module's source.** It is
> recorded here exactly as it stands in `cusum_status` and it is not to be changed by this run; but
> it is a band without a source and it is named as one. The sigma floor of 0.05 is likewise
> described in the source as "documented" without naming the document.
>
> **Interpretation.** A breach says the schedule index has moved away from 1.0 persistently rather
> than noisily, and names the period at which the accumulated departure first exceeded what the
> project's own variability explains. A clean run says any departure so far is inside that
> variability. It is a monitor of drift, not a forecast.
>
> **Nothing to report.**
> - If `spi` is absent: `"Insufficient data: upload required documents"`.
> - If `spiHistory` is not a list, or holds fewer than two readings:
>   `"Awaiting history (2 periods needed)"`.
>
> **Two properties of this module that a reader must be told.**
>
> 1. **It is registered as stochastic and it is not.** `STOCHASTIC` in `models.py` names
>    `{"A1.1", "A1.2", "A2.1"}`. `run_cusum` accepts a random generator and a seed and **uses
>    neither**; `cusum_series` is documented in its own docstring as "Deterministic given the
>    series". A1.2's presence in `STOCHASTIC` is not borne out by its source. Applying this
>    specification is therefore deterministic, and the reproducibility question does not arise for
>    it in the way it would for a genuinely sampled module.
> 2. **Its band is emitted in lower case and the fusion rule cannot read it.** `cusum_status`
>    returns `"red"`, `"amber"`, `"green"`. `fusion.BAND_SEVERITY` holds capitalised spellings
>    only, and `worst_band` filters to the keys it knows before taking the maximum, so an unknown
>    token is dropped rather than ranked. A1.2's band therefore reaches the ledger but does not
>    reach the category rollup. **This specification records the behaviour and does not change it.**
>    A model applying this specification must emit the band in the same lower case the module does,
>    so that this run alters nothing about what fusion sees.
>
> ---

### Measured

**1. Does it compute today.** **YES — computes.** Band: **green**. Reading: CUSUM max 0.249 against H 0.837 over 8 periods; no breach

**2. Named inputs no stored observation supplies.** **None** — every input this specification names by field name is present in the stored row.

**3. Governed structure?** **NO.** This module is defined on plain numeric facts a document states directly; it names no governed structure in `CANONICAL_STRUCTURE_KEYS` or any of the v3–v8 layers.

---

## 6. ARIMA CPI forecast → **A1.5 — ARIMA CPI Forecast**

**Identifier:** `A1.5` · **Method class:** `ARIMA_Forecast` · **Tree category:** A1 Cost & EVM Performance · **In service:** yes

**Where it lives:** `specifications/A1_cost_and_evm.md`, section `A1.5 — ARIMA CPI Forecast`, lines **189–227**.

### Specification text, verbatim

> ## A1.5 — ARIMA CPI Forecast
>
> **Identity.** Live id `A1.5`. Method class `ARIMA_Forecast`. A one-period-ahead forecast of the
> cost performance index from an identified time-series model of the project's own history.
>
> **Required inputs.**
> `cpiHistory` — the list of cost performance index readings. Where it is absent the module falls
> back to `cpi` as a one-element series exactly as the original JavaScript's truthiness did, and
> then abstains on the length check. **A minimum of eight readings is required.**
>
> **Method.** `canonical_v3.identify_arima`. The differencing order `d` is set by a stated
> stationarity rule, not assumed. `(p, q)` are searched up to `(2, 1)`, estimated by conditional
> least squares, and selected by **AICc** — the small-sample criterion, which favours parsimony on
> a short cost-index history by construction. Stationarity and invertibility are checked and a model
> failing either refuses. The Ljung-Box statistic at lag 1 and the residual autocorrelation are
> reported with the forecast, together with a 95 per cent prediction interval where one can be
> formed.
>
> **Bands.** **None, and none may be attached.** The ladder this module once carried was drawn over
> the output of a different estimator.
>
> **Interpretation.** The forecast states where cost efficiency is heading one period out, given only
> its own history. The order `(p,d,q)`, the AICc and the residual diagnostics are part of the answer,
> not decoration: a forecast from a model whose residuals fail Ljung-Box is a forecast whose
> uncertainty is understated.
>
> **Nothing to report.**
> - No history at all: `"Awaiting a cost performance history"`.
> - Fewer than eight readings, or an identification that fails stationarity or invertibility: the
>   sentence `identify_arima` raises for that condition.
>
> **Forbidden implementation, recorded because it was the previous one.** Differencing once
> unconditionally, regressing each difference on the one before to get a single `phi`, clamping that
> `phi` to ±0.9, and forecasting one step. That is an AR(1) on first differences, which the
> supervisory contract names in terms as the thing ARIMA must not be hard-coded as. Three
> observations were enough to run it. Eight are now required.
>
> ---

### Measured

**1. Does it compute today.** **YES — computes.** Band: **no band (calibration pending by ruling)**. Reading: Cost performance forecast 0.854 one period ahead from an identified (0,1,0) model over 8 readings, with a 95 per cent prediction interval from 0.847 to 0.861

**2. Named inputs no stored observation supplies.** **None** — every input this specification names by field name is present in the stored row.

**3. Governed structure?** **NO.** This module is defined on plain numeric facts a document states directly; it names no governed structure in `CANONICAL_STRUCTURE_KEYS` or any of the v3–v8 layers.

---

## 7. Independent EAC reconciliation → **A1.11 — Independent EAC Reconciliation Index**

**Identifier:** `A1.11` · **Method class:** `Independent_EAC_Reconciliation` · **Tree category:** A1 Cost & EVM Performance · **In service:** yes

**Where it lives:** `specifications/A1_cost_and_evm.md`, section `A1.11 — Independent EAC Reconciliation Index`, lines **540–583**.

### Specification text, verbatim

> ## A1.11 — Independent EAC Reconciliation Index
>
> **Identity.** Live id `A1.11`. Method class `Independent_EAC_Reconciliation`. Approved rename at
> Run 28 from "ICE Ratio". How far an independently prepared forecast of the final cost stands from
> the project management team's own.
>
> **Required inputs.**
> `independentEacPair` — two separately prepared forecasts of the cost at completion, one from the
> project management team and one prepared independently of it. **Each side must state all five
> lineage fields: source, method, assumptions, model version and responsible party.**
>
> **Method.**
>
>     IER        = Independent / Management
>     Divergence = (Independent - Management) / Management
>
> **Independence is checked, not asserted.** Both sides must carry all five lineage fields, and the
> two must differ **on the method AND on the responsible party**. Where the pair is absent,
> incomplete, or not genuinely distinct, the module abstains.
>
> **Bands.** **None, and none may be attached.** Reconciliation bands are named in the supervisory
> contract as calibration dependent.
>
> **Interpretation.** An index of 1 means the two forecasts agree. Above 1 means the independent
> estimate is higher — the management forecast may be optimistic. The divergence, expressed as a
> percentage, is the figure a governance board would act on; the two lineages beside it are what make
> the divergence mean anything.
>
> **Nothing to report.**
> - `independentEacPair` absent: `"Awaiting two separately prepared forecasts of the cost at
>   completion, one from the project management team and one prepared independently of it. This
>   measure is named for a method that cannot be carried out without it, so no reading is reported
>   and no other figure is used in its place."`
> - Present but incomplete or not genuinely distinct: the sentence
>   `canonical_v3.independent_eac_reconciliation` raises for that condition.
>
> **Forbidden implementation, which was exactly the thing the contract names.**
> `(bac / cpi)` divided by `(ac + (bac − ev))`. Both sides are arithmetic on one vector of four
> reported figures, prepared by nobody, with no method, assumptions or responsible party attached to
> either. The ratio was published as a reconciliation between an independent estimate and a
> management one **when no second estimate existed anywhere.**
>
> ---

### Measured

**1. Does it compute today.** **NO — abstains.** Stated reason, verbatim: *"Awaiting two separately prepared forecasts of the cost at completion, one from the project management team and one prepared independently of it. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place."*

**2. Named inputs no stored observation supplies** (1): `independentEacPair`

**3. Governed structure?** **YES — `independentEacPair`.** It is **absent** from the stored row. Could a document state it in words? **YES** — two forecast figures with their preparers named; a document can state both.

---

# Schedule

## 8. Milestone trend analysis → **A2.7 — Milestone Trend Analysis**

**Identifier:** `A2.7` · **Method class:** `Milestone_Trend` · **Tree category:** A2 Schedule Performance · **In service:** yes

**Where it lives:** `specifications/A2_schedule_performance.md`, section `A2.7 — Milestone Trend Analysis`, lines **157–199**.

### Specification text, verbatim

> ## A2.7 — Milestone Trend Analysis
>
> **Identity.** Live id `A2.7`. Method class `Milestone_Trend`. How far each milestone has moved from
> what was committed, and whether it moved again this period.
>
> **Required inputs.** `milestoneForecastHistory` — a mapping, and the only input read. It must carry
> **stable milestone identity across reporting periods** — an identity, not a name — and for each
> milestone its original baseline date, its current approved baseline date, the report date, the
> forecast date, the schedule version, and the actual date once achieved.
>
> **Method.** Two variances, per milestone:
> ```
> MV = forecast date - BASELINE date            variance against the commitment
> MD = forecast date - PREVIOUS forecast date   drift since the last report
> ```
> The reported headline is the largest `MV` across milestones and the count of milestones whose
> forecast moved further out this period.
>
> **Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending with
> the standard note.
>
> **Interpretation.** `MV` is the measurement the method is named for: the distance between what was
> promised and what is now expected. `MD` is the movement since last time. Reporting both is what
> makes a rebaseline visible — before Run 28 the module reported the drift alone, matched milestones
> by name, and a rebaseline erased the slip because no original commitment was retained. **The
> original commitment history may not be erased after a rebaseline.**
>
> **Nothing to report.**
> 1. Structure absent or not a mapping: the two sentences above, with `W` = *"a milestone forecast
>    history: each milestone's committed date and the date it was forecast for in each reporting
>    period since"*.
> 2. **A milestone forecast only once abstains rather than being reported as a trend**, in the words
>    `canonical_v3.milestone_trend` raises for that condition. Insufficient repeated forecasts is not
>    estimable for a trend claim.
>
> **A known extraction gap, recorded and not fixed here.** On the owner's deployment this module
> abstains on TST-007 because the forecast dates sit in a table the extractor does not read as
> per-milestone data. **That is a document and extraction question, not a specification one.** The
> specification above is correct and the abstention it produces is the correct behaviour until the
> extractor supplies the structure.
>
> ---

### Measured

**1. Does it compute today.** **YES — computes.** Band: **no band (calibration pending by ruling)**. Reading: 3 milestones followed across their forecasts; the largest variance against the original commitment is 37 days, and 0 of them moved further out this period

**2. Named inputs no stored observation supplies.** **None** — every input this specification names by field name is present in the stored row.

**3. Governed structure?** **YES — `milestoneForecastHistory`.** It is **present** in the stored row. Could a document state it in words? **YES** — a milestone log printing each forecast date as it was reissued.

---

## 9. Look-ahead schedule health → **A2.8 — Look-Ahead Schedule Health**

**Identifier:** `A2.8` · **Method class:** `LookAhead_Health` · **Tree category:** A2 Schedule Performance · **In service:** yes

**Where it lives:** `specifications/A2_schedule_performance.md`, section `A2.8 — Look-Ahead Schedule Health`, lines **200–234**.

### Specification text, verbatim

> ## A2.8 — Look-Ahead Schedule Health
>
> **Identity.** Live id `A2.8`. Method class `Lookahead_Health`. What share of the work planned in the
> look-ahead window is actually ready to start.
>
> **Required inputs.** `lookAheadSchedule` — a mapping, and the only input read. It must carry the
> governed horizon, the status date, and **one row per activity** with its identity, whether its
> constraints are cleared, and for an open constraint what category of constraint it is.
>
> **Method.**
> ```
> ReadyFraction = (P - C) / P = 1 - C/P
> ```
> over `P` planned activities and `C` still carrying an open constraint. **The counts are derived
> from the inventory**, not supplied as bare totals. Constraint categories are reported alongside.
>
> **Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending with
> the standard note; the supplied contract states in terms that bands here remain policy and
> calibration.
>
> **Interpretation.** The ready fraction is a readiness indicator grounded in constraint removal.
> **Percent Plan Complete may not be substituted for it** — PPC says what was finished, this says
> what can be started. Before Run 28 the module read two bare counts and reported `C/P`, the
> complement of the quantity the contract asks for, with no inventory behind the counts to audit.
>
> **Nothing to report.**
> 1. Structure absent or not a mapping: the two sentences above, with `W` = *"a look ahead schedule:
>    the window it covers, the activities planned in it, and whether each one still carries an open
>    constraint"*.
> 2. No planned activities, an activity appearing twice, or a constraint status not stated: the
>    module abstains in the words `canonical_v3.look_ahead_ready_fraction` raises for that condition.
>    An unreliable constraint inventory is not estimable.
>
> ---

### Measured

**1. Does it compute today.** **NO — abstains.** Stated reason, verbatim: *"Awaiting a look ahead schedule: the window it covers, the activities planned in it, and whether each one still carries an open constraint. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place."*

**2. Named inputs no stored observation supplies** (1): `lookAheadSchedule`

**3. Governed structure?** **YES — `lookAheadSchedule`.** It is **absent** from the stored row. Could a document state it in words? **YES** — the look-ahead is itself a printed document; Run 86 read one.

---

## 10. Resource loading index → **A2.9 — Resource Loading Index**

**Identifier:** `A2.9` · **Method class:** `Resource_Loading` · **Tree category:** A2 Schedule Performance · **In service:** yes

**Where it lives:** `specifications/A2_schedule_performance.md`, section `A2.9 — Resource Loading Index`, lines **235–263**.

### Specification text, verbatim

> ## A2.9 — Resource Loading Index
>
> **Identity.** Live id `A2.9`. Method class `Resource_Loading`. Time-phased demand against capacity.
>
> **Required inputs.** `resourceProfile` — a mapping, and the only input read. Every bucket must carry
> its time period, its resource type, the planned or required demand, the available capacity, the
> amount deployed where used, and the resource constraints.
>
> **Method.**
> ```
> LoadRatio_t = Demand_t / AvailableCapacity_t          for every bucket t
> ```
> The **peak** load ratio is the headline, reported with the bucket and the resource type it belongs
> to, together with the count of buckets above capacity out of the total.
>
> **Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending with
> the standard note.
>
> **Interpretation.** The peak is the headline because a profile that is over capacity in one period
> is over capacity: the work in that period will not happen, whatever the average across the project
> says. Before Run 28 the module reported `actualLaborHours / plannedLaborHours` — one ratio for the
> whole project, with no time bucket, no resource type and **no capacity anywhere in it**, capacity
> being the denominator the index is defined on. **Neither of those two fields is read here.**
>
> **Nothing to report.** The two sentences above, with `W` = *"a time phased resource profile: for each
> period and each kind of resource, the amount of work demanded and the amount available"*.
>
> ---

### Measured

**1. Does it compute today.** **YES — computes.** Band: **no band (calibration pending by ruling)**. Reading: The heaviest period is 2026-04 for Electrical, demanding 5,200 against 4,000 available, a load ratio of 1.3; 2 of 4 periods are above capacity

**2. Named inputs no stored observation supplies.** **None** — every input this specification names by field name is present in the stored row.

**3. Governed structure?** **YES — `resourceProfile`.** It is **present** in the stored row. Could a document state it in words? **YES** — a resource histogram table of demand against availability by period.

---

## 11. PERT network criticality → **A2.1 — PERT Network Criticality**

**Identifier:** `A2.1` · **Method class:** `PERT_Criticality` · **Tree category:** A2 Schedule Performance · **In service:** yes

**Where it lives:** `specifications/A2_schedule_performance.md`, section `A2.1 — PERT Network Criticality`, lines **34–78**.

### Specification text, verbatim

> ## A2.1 — PERT Network Criticality
>
> **Identity.** Live id `A2.1`. Method class `PERT_Network_Criticality`. Which activities are
> actually on the critical path once the durations are allowed to vary, and how often.
>
> **Required inputs.** `scheduleNetwork` — a mapping, and the only input read. Each activity must
> carry an identity, its predecessors, and a duration distribution or three-point estimate.
>
> **Method.** Classical PERT moments per activity:
> ```
> E[T]   = (O + 4M + P) / 6
> Var[T] = ((P - O) / 6)^2
> ```
> then **2,000 simulated trials**. In every trial each activity's duration is redrawn from its
> three-point estimate and the **forward and backward passes are recomputed**. The criticality index
> of an activity is the share of trials in which it is critical. The reported headline is the
> activity with the highest index, ties broken by activity identifier, and the index is reported for
> every activity. The eightieth percentile project finish is reported beside it.
>
> **Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending with
> the standard note. The old ladder was drawn over a ratio of an eightieth percentile to a modal
> baseline, which is not this quantity. Before Run 28 the module computed a criticality index from
> three activity durations that were **literals in the source file, identical on every project**;
> Run 10B removed that arithmetic and the ladder with it.
>
> **Interpretation.** A criticality index says how often an activity decides the finish date, not
> whether it is late. An activity critical in 40 per cent of trials is a real exposure even though a
> single deterministic pass would not show it on the critical path at all. **Criticality is measured
> here, not ranked.**
>
> **Nothing to report.** The two sentences above, with `W` = *"the project's activity network: the
> activities, the logic between them, and a duration for each"*. **`spi` and `bac` may not be used to
> reconstruct topology** and are not read here.
>
> **One property a reader must be told, and it bears on reproducibility.** This module genuinely
> samples: it draws 2,000 trials from the registry's generator. It is one of the three modules named
> in `models.STOCHASTIC`, so its result set carries the seed record, and in production the generator
> is seeded once from the scenario and the period — never from the participant and never from how
> many modules ran before it. **A specification applying this module cannot reproduce the sampling.**
> Where the network is present, the honest answer from a specification-driven application is the
> reading the platform's own simulation produced; a re-simulation performed elsewhere is a different
> sample and must not be presented as the same figure.
>
> ---

### Measured

**1. Does it compute today.** **NO — abstains.** Stated reason, verbatim: *"Awaiting the project's activity network: the activities, the logic between them, and a duration for each. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place."*

**2. Named inputs no stored observation supplies** (1): `scheduleNetwork`

**3. Governed structure?** **YES — `scheduleNetwork`.** It is **absent** from the stored row. Could a document state it in words? **YES** — an activity list with predecessors and durations is printed in every schedule report.

---

# Cost Risk

## 12. Contingency burn rate → **A3.2 — Contingency Burn Rate**

**Identifier:** `A3.2` · **Method class:** `Contingency_Burn_Rate` · **Tree category:** A3 Cost Risk · **In service:** yes

**Where it lives:** `specifications/A3_cost_risk.md`, section `A3.2 — Contingency Burn Rate`, lines **77–130**.

### Specification text, verbatim

> ## A3.2 — Contingency Burn Rate
>
> **Identity.** Live id `A3.2`. Method class `Contingency_Burn_Rate`. How much of the money set
> aside for the unknown has been spent, and whether it is being spent faster than the work is being
> done.
>
> **Required inputs, by their exact `signal_inputs` field names.**
> `originalContingency` — the contingency the project started with. Required.
> `remainingContingency` — the contingency left. Required.
> `actualPctComplete` — the reported percent complete. **Optional.** Its absence removes the second
> figure only, not the reading.
>
> **Method.**
> ```
> C              = (originalContingency - remainingContingency) / originalContingency
> NormalizedBurn = C / ProgressFraction,        when ProgressFraction > 0
> ProgressFraction = actualPctComplete / 100
> ```
> Oracle from the source: original 100, remaining 60, progress 0.50 gives a consumed fraction of
> 0.40 and a normalized burn of 0.80.
>
> **Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
> with the standard note. The supplied contract states in terms that **no universal traffic-light
> bands are supplied** for either figure and that threshold calibration belongs later. The
> four-band ladder this module carried over the normalized burn at 1.0, 1.3 and 1.6 was recorded as
> uncited by Run 4 and removed by Run 28. It is not to be restored by this run.
>
> **Interpretation.** The consumed fraction says how much of the reserve is gone. The normalized
> burn compares that against how much of the work is done: a figure above 1 says the reserve is
> being consumed faster than the project is being built, which is the condition that ends with no
> reserve and work remaining. Neither figure carries a colour and neither should be read as one.
>
> **Nothing to report.**
> 1. Either contingency figure absent: `"Insufficient data: the original and remaining contingency
>    amounts are needed, and at least one of them has not been reported for this period."`
> 2. `actualPctComplete` **present** and not a finite number: `"Insufficient data: the reported
>    percent complete was reported in a form that is not a number."`
> 3. `actualPctComplete` present and above the maximum a percentage can take: `"Insufficient data:
>    the reported percent complete was reported as a figure this quantity cannot take, so it is not
>    read as evidence of anything. No substitute figure is used in its place."`
> 4. Original contingency not above zero: `"No original contingency above zero was provided, so the
>    share consumed has no denominator and none is reported."`
> 5. Remaining below nothing or above the original: `"The remaining contingency provided is below
>    nothing or above the original amount, so the two figures do not describe one contingency and no
>    share is reported."`
>
> **One property a reader must be told.** An absent progress figure and an impossible one are
> handled differently on purpose. Absent, the consumed fraction is still published and the
> no normalized burn is reported. Impossible — reported, but outside the range a percentage can
> occupy — refuses the whole reading, because treating a wrong number as a missing one is how a
> reading error becomes invisible.
>
> ---

### Measured

**1. Does it compute today.** **YES — computes.** Band: **no band (calibration pending by ruling)**. Reading: Contingency is 55 per cent consumed at 83 per cent complete, a burn against progress of 0.67

**2. Named inputs no stored observation supplies.** **None** — every input this specification names by field name is present in the stored row.

**3. Governed structure?** **NO.** This module is defined on plain numeric facts a document states directly; it names no governed structure in `CANONICAL_STRUCTURE_KEYS` or any of the v3–v8 layers.

---

## 13. Labor productivity index → **A3.3 — Labor Productivity Index**

**Identifier:** `A3.3` · **Method class:** `Labor_Productivity` · **Tree category:** A3 Cost Risk · **In service:** yes

**Where it lives:** `specifications/A3_cost_risk.md`, section `A3.3 — Labor Productivity Index`, lines **131–165**.

### Specification text, verbatim

> ## A3.3 — Labor Productivity Index
>
> **Identity.** Live id `A3.3`. Method class `Labor_Productivity`. Output per labour hour, against
> what was planned.
>
> **Required inputs.** `productionOutputRecord` — a mapping, and the only input read. It must carry
> the quantity installed, the quantity planned, the unit both are counted in, the hours each took,
> and where the quantities came from.
>
> **Method.**
> ```
> ActualProductivity  = EarnedOutput  / ActualLaborHours
> PlannedProductivity = PlannedOutput / PlannedLaborHours
> ProductivityIndex   = ActualProductivity / PlannedProductivity
> ```
> The output must be a comparable earned or installed quantity, an earned labour-hours basis, or
> another explicitly equivalent production quantity. **Planned hours over actual hours alone is not
> this metric**, and with no comparable output basis the answer is not estimable.
>
> **Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
> with the standard note. What it replaced was
> `((actualPctComplete / 100) * plannedLaborHours) / actualLaborHours`, whose numerator is not an
> installed quantity but the planned hours scaled by a reported progress percentage — so the
> "productivity" moved with whatever percentage was typed into a monthly report. **Neither
> `actualPctComplete` nor `plannedLaborHours` is read here.**
>
> **Interpretation.** An index below 1 says the crews are installing less per hour than the estimate
> assumed. It is the earliest cost signal a project has, because it moves before the cost report
> does, and it is stated in the unit the work is actually counted in.
>
> **Nothing to report.** The two `require_v3_structure` sentences, with `W` = *"a record of production: the
> quantity of work installed, the quantity planned, and the labour hours each of those took"*.
>
> ---

### Measured

**1. Does it compute today.** **YES — computes.** Band: **no band (calibration pending by ruling)**. Reading: 0.06 linear metres of conduit an hour installed against 0.08 planned, a productivity index of 0.83

**2. Named inputs no stored observation supplies.** **None** — every input this specification names by field name is present in the stored row.

**3. Governed structure?** **YES — `productionOutputRecord`.** It is **present** in the stored row. Could a document state it in words? **YES** — quantities installed and hours expended are printed in the progress report.

---

## 14. Cost risk analysis P80 → **A3.6 — Cost Risk Analysis P80**

**Identifier:** `A3.6` · **Method class:** `Cost_Risk_P80` · **Tree category:** A3 Cost Risk · **In service:** yes

**Where it lives:** `specifications/A3_cost_risk.md`, section `A3.6 — Cost Risk Analysis P80`, lines **201–245**.

### Specification text, verbatim

> ## A3.6 — Cost Risk Analysis P80
>
> **Identity.** Live id `A3.6`. Method class `Cost_Risk_Analysis`. The eightieth percentile of a
> simulated total cost.
>
> **Required inputs.** `costRiskModel` — a mapping, and the only input read. It must carry the base
> cost components, the risk events, the probability of each, the impact distribution of each, and
> the dependence policy where dependence is material.
>
> **Method.**
> ```
> TotalCost = BaseCostComponents + RealizedRiskEvents
> ```
> Simulated over **20,000 trials**. In each trial every event occurs with its stated probability and,
> when it does, its impact is drawn from its stated distribution. The reported figure is the
> **empirical eightieth percentile** of the resulting total cost, under the quantile convention
> frozen in `canonical_v3.empirical_quantile` and reported on the result as
> `"right-continuous empirical inverse"`. The median and mean total cost are reported beside it.
>
> **Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
> with the standard note. What it replaced was `eac = bac / cpi`, then
> `uncertainty = max(0.03, abs(1 - cpi)) * 0.5` and `p80_eac = eac * (1 + uncertainty * 1.28)`: one
> closed-form multiplication of a reported cost index by the standard normal 80th percentile, with
> no component, no risk event, no probability, no impact and no trial anywhere in it. The supplied
> contract states that a deterministic CPI uplift **is not** CRA P80.
>
> **Interpretation.** The figure is the cost the project would not exceed in four runs out of five,
> given the risks it has declared and the probabilities it has put on them. It is a statement about
> the declared risk register and no better than that register is.
>
> **Nothing to report.** The two `require_v3_structure` sentences, with `W` = *"a cost risk model: the base
> cost components, the risk events that could occur, how likely each is and what it would cost"*.
>
> **One property a reader must be told, and it bears on reproducibility.** This module **draws
> random numbers**: `run_cost_risk` passes the registry's generator into `cost_risk_simulation` and
> runs twenty thousand trials on it. **It is nonetheless absent from `models.STOCHASTIC`**, which
> names only `{"A1.1", "A1.2", "A2.1"}`. The consequence is that its result set does not carry the
> seed record that a stochastic module is supposed to carry. The module's own source is unambiguous
> that it samples; the registry's set is what disagrees with it. **This specification records the
> contradiction and changes neither.** In production the generator is seeded once from the scenario
> and the period, so the reading is reproducible for a given project and period despite the missing
> seed record.
>
> ---

### Measured

**1. Does it compute today.** **NO — abstains.** Stated reason, verbatim: *"Awaiting a cost risk model: the base cost components, the risk events that could occur, how likely each is and what it would cost. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place."*

**2. Named inputs no stored observation supplies** (1): `costRiskModel`

**3. Governed structure?** **YES — `costRiskModel`.** It is **absent** from the stored row. Could a document state it in words? **YES** — a risk register with probability and cost impact per event; Run 86 read one from a .docx.

---

## 15. Overhead absorption rate → **A3.5 — Overhead Absorption Rate**

**Identifier:** `A3.5` · **Method class:** `Overhead_Absorption` · **Tree category:** A3 Cost Risk · **In service:** yes

**Where it lives:** `specifications/A3_cost_risk.md`, section `A3.5 — Overhead Absorption Rate`, lines **166–200**.

### Specification text, verbatim

> ## A3.5 — Overhead Absorption Rate
>
> **Identity.** Live id `A3.5`. Method class `Overhead_Absorption`. Whether indirect cost is being
> absorbed over its allocation base at the rate that was planned.
>
> **Required inputs.** `overheadAllocationBase` — a mapping, and the only input read. It must name
> the allocation base, and carry the planned and actual overhead, the planned and actual amount of
> the base, and where the driver figures came from.
>
> **Method.**
> ```
> PlannedRate            = PlannedOverhead / PlannedDriver
> ActualRate             = ActualOverhead  / ActualDriver
> RateVariance           = ActualRate - PlannedRate
> RelativeRateVariance   = RateVariance / PlannedRate
> ```
>
> **Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
> with the standard note. What it replaced was
> `indirectCostActual / (indirectCostPlan * actualPctComplete / 100)`. There is no driver anywhere
> in that expression; overhead is absorbed over a base such as direct labour hours or direct cost,
> and the supplied contract states in terms that indirect actual over indirect plan with no
> allocation base **is not overhead absorption**.
>
> **Interpretation.** The rate variance says how much more, or less, indirect cost each unit of the
> base is carrying than the plan assumed. Under-absorption on a shrinking base is a different
> problem from overhead overspend on a steady one, and reporting the rate rather than the total is
> what keeps the two distinguishable.
>
> **Nothing to report.** The two `require_v3_structure` sentences, with `W` = *"an overhead allocation
> base: the planned and actual overhead and the planned and actual amount of the base it is absorbed
> over"*.
>
> ---

### Measured

**1. Does it compute today.** **YES — computes.** Band: **no band (calibration pending by ruling)**. Reading: Overhead is being absorbed at 4.28 for each unit of direct labour hours against 4 planned, a rate variance of 7.1 per cent

**2. Named inputs no stored observation supplies.** **None** — every input this specification names by field name is present in the stored row.

**3. Governed structure?** **YES — `overheadAllocationBase`.** It is **present** in the stored row. Could a document state it in words? **YES** — planned and actual overhead over a stated driver is printed in a cost report.

---

# Document Signals

## 16. RFI velocity → **A4.2 — RFI Velocity**

**Identifier:** `A4.2` · **Method class:** `RFI_Velocity` · **Tree category:** A4 Document-Derived Condition Signals · **In service:** yes

**Where it lives:** `specifications/A4_document_derived_signals.md`, section `A4.2 — RFI Velocity`, lines **49–132**.

### Specification text, verbatim

> ## A4.2 — RFI Velocity
>
> **Identity.** Live id `A4.2`. Method class `RFI_Velocity`. A project manager would call this the
> rate at which the field is asking questions: how many requests for information are being raised
> per unit of time, and how many of the open ones are overdue.
>
> **Required inputs, by their exact `signal_inputs` field names.** This module has **two supply
> paths and prefers the first.**
>
> *Governed path (preferred).* `rfiEventLog` — a mapping. Used whenever it is present, because only
> the events themselves can be de-duplicated: a cumulative register uploaded every month repeats
> every earlier row, and a total extracted from the latest upload cannot tell a re-reported request
> from a new one.
>
> *Extracted-totals path.* Used only when `rfiEventLog` is absent.
> `rfiCount` — the number of requests raised. If it is absent, `rfiNumber` is read in its place;
> those are the only two names read for the count.
> `rfiPeriodDays` — the number of days the request log covers. Required; **never defaulted to 30.**
> `rfiOverdue` — optional. The number of open requests that are overdue.
> `rfiOpen` — optional, carried on the result and used in no band.
> `rfiAvgResponseDays`, or `rfiResponseTimeDays` when the first is absent — optional, reported in
> the evidence sentence only.
> `rfiOldestOpenDays` — optional, reported in the evidence sentence only.
>
> **Method.**
>
> Governed path:
> ```
> rate_per_day    = de-duplicated RFI events / exposure days     (canonical_v4.rfi_velocity)
> per_week        = rate_per_day * 7
> overdue_ratio   = overdue / open_relevant, or null where not separately exposed
> ```
>
> Extracted-totals path, computed exactly as the source computes it, with the JavaScript rounding
> the port preserves:
> ```
> per30     = js_round((rfiCount / rfiPeriodDays) * 300) / 10
> per_week  = js_round((rfiCount / rfiPeriodDays) * 70)  / 10
> overdue_ratio = rfiOverdue / rfiCount        (only when rfiOverdue is present and rfiCount > 0)
> ```
>
> **Bands, and where each threshold came from.**
>
> | Band | Velocity condition | Overdue-share condition |
> |---|---|---|
> | Green | `per_week <= 2` | `ratio < 0.10` |
> | Yellow | `per_week <= 4` | `ratio < 0.20` |
> | Amber | `per_week <= 8` | `ratio < 0.35` |
> | Red | otherwise | otherwise |
>
> The reported band is the **worse of the two** on the rank `Green < Yellow < Amber < Red`; the
> overdue band is used only when it outranks the velocity band.
>
> **Where these thresholds came from: nothing.** The source says so in those terms — Run 4 looked
> for a source specifying two, four and eight requests per week, and for one specifying ten, twenty
> and thirty-five per cent overdue, and found neither. The boundaries are left exactly as they
> stand, uncited, and **this module does not vote**. This specification records them and does not
> change them.
>
> **Interpretation.** A high velocity says the field is asking a lot of questions per unit of time,
> which is evidence about the clarity of the issued documents rather than about cost. A high overdue
> share says the questions are not being answered, which is the condition that turns into a claim.
> The two are separate readings and the worse one is shown.
>
> **Nothing to report.**
> 1. `rfiEventLog` present but unreadable: the two `require_v4_structure` sentences above, with
>    `W` = *"a register of requests for information as events, each with its own identity and the
>    dates it was raised and answered, and the span of time the register covers"*.
> 2. No `rfiEventLog`, and both `rfiCount` and `rfiNumber` absent: the default sentence
>    `"Insufficient data: upload required documents"`.
> 3. `rfiPeriodDays` absent: `"Awaiting the number of days the request log covers: a rate of
>    requests over time cannot be formed without the span of time it was measured over"`.
> 4. `rfiPeriodDays` not above zero, or the count below zero: `"Awaiting a request count and a log
>    period that can form a rate: the figures read from the request log cannot both be right"`.
> 5. `rfiOverdue` present and either below zero or above the total: `"Awaiting an overdue count
>    that lies within the total: the figures read from the request log cannot both be right"`.
>
> **One property a reader must be told.** On the extracted-totals path, where `rfiPeriodDays` was
> supplied by derivation rather than read from a document, the evidence sentence gains the suffix
> `" (assumed 30-day period; upload RFI log for precise velocity)"`. The reading is still published
> and still banded.
>
> ---

### Measured

**1. Does it compute today.** **YES — computes.** Band: **Red**. Reading: 120 RFIs over 30 days (120/30d, 28/week), 8 overdue (7%), avg response 11 days, oldest open 44 days

**2. Named inputs no stored observation supplies** (1): `rfiEventLog`

**3. Governed structure?** **YES — `rfiEventLog`.** It is **absent** from the stored row. Could a document state it in words? **YES** — an RFI log is a printed register.

---

## 17. Submittal rejection rate → **A4.3 — Submittal Rejection Rate**

**Identifier:** `A4.3` · **Method class:** `Submittal_Rejection` · **Tree category:** A4 Document-Derived Condition Signals · **In service:** yes

**Where it lives:** `specifications/A4_document_derived_signals.md`, section `A4.3 — Submittal Rejection Rate`, lines **133–187**.

### Specification text, verbatim

> ## A4.3 — Submittal Rejection Rate
>
> **Identity.** Live id `A4.3`. Method class `Submittal_Rejection`. The share of submittal decisions
> that were rejections.
>
> **Required inputs, by their exact `signal_inputs` field names.** Three supply paths, in this
> order of preference.
>
> *Governed path.* `submittalDecisionRegister` — a mapping. Used whenever present, because only the
> decisions themselves carry a disposition to be governed and a period to be filtered on.
>
> *RFA path.* Used when `rfaTotal` and `rfaRejected` are both present and `rfaTotal > 0`.
> `rfaTotal`, `rfaRejected`, and optionally `rfaResubmit`, `rfaOpen`, `rfaAvgReviewDays` — the last
> three appear in the evidence sentence only and enter no band.
>
> *Submittal-totals path.* `submittalsTotal` and `submittalsRejected`.
>
> **Method.**
> ```
> rate = rejected / total
> ```
> On the extracted paths the source rounds as JavaScript does: `rate = js_round((rejected/total) *
> 1000) / 1000`. On the governed path the full-precision rate is banded and rounded to three places
> for display.
>
> **Bands, and where each threshold came from.**
>
> | Band | Condition |
> |---|---|
> | Green | `rate <= 0.05` |
> | Yellow | `rate <= 0.15` |
> | Amber | `rate <= 0.25` |
> | Red | otherwise |
>
> **Where these thresholds came from: nothing.** The source states it in those words — Run 4 looked
> for a source specifying five, fifteen and twenty-five per cent for a submittal rejection share and
> found none. The boundaries are unchanged and uncited, and **this module does not vote**.
>
> **Interpretation.** A high rejection share says the packages arriving for review are not meeting
> the specification on first presentation, which costs review cycles and float. It says nothing
> about cost performance and must not be read as though it did.
>
> **Nothing to report.**
> 1. `submittalDecisionRegister` present but unreadable: the two `require_v4_structure` sentences,
>    with `W` = *"a submittal decision register: each submittal, each revision of it, and the
>    decision recorded against it on the project's own disposition list"*.
> 2. Neither total nor rejected count available on any path:
>    `"Insufficient data: upload required documents"`.
> 3. Total not above zero: `"Awaiting a submittal register with entries in it: a rejection share
>    has no denominator without one"`.
> 4. Rejected below zero or above the total: `"Awaiting a rejected count that lies within the total:
>    the figures read from the register cannot both be right"`.
>
> ---

### Measured

**1. Does it compute today.** **YES — computes.** Band: **Yellow**. Reading: 24 of 200 submittals rejected (12%)

**2. Named inputs no stored observation supplies** (1): `submittalDecisionRegister`

**3. Governed structure?** **YES — `submittalDecisionRegister`.** It is **absent** from the stored row. Could a document state it in words? **YES** — a submittal log is a printed register.

---

## 18. NCR rate → **A4.4 — NCR Rate**

**Identifier:** `A4.4` · **Method class:** `NCR_Rate` · **Tree category:** A4 Document-Derived Condition Signals · **In service:** yes

**Where it lives:** `specifications/A4_document_derived_signals.md`, section `A4.4 — NCR Rate`, lines **188–220**.

### Specification text, verbatim

> ## A4.4 — NCR Rate
>
> **Identity.** Live id `A4.4`. Method class `NCR_Rate`. Nonconformances per unit of governed
> exposure.
>
> **Required inputs.** `ncrExposureRecord` — a mapping, and the only input read. There is no
> extracted-totals path.
>
> **Method.** `canonical_v4.ncr_rate` over the supplied record:
> ```
> ncr_rate = NCR events / governed exposure quantity
> ```
> where the exposure is inspections, inspected units, labour hours, work value or another explicit
> denominator declared on the record. Four nonconformances over one hundred inspections reads 0.04.
> Open count, age of open, severity and closure rate are tracked **separately** and are not folded
> into the rate. **With no exposure, no normalised rate is fabricated.**
>
> **Bands.** **None. This module asserts no band and none may be attached.** It reports
> calibration-pending with the standard note. The former ladder was drawn over a different quantity:
> until Run 28 this module reported open nonconformances as a share of an audited findings cohort,
> which is a backlog share, not a rate — the numerator a stock carried across periods, the
> denominator the size of an audit. That quantity is gone and its ladder went with it.
>
> **Interpretation.** The reading is how often nonconforming work is found per unit of the work that
> was actually looked at. It rises when quality falls and it also rises when inspection improves, so
> it is read against the exposure it names, never alone.
>
> **Nothing to report.** The two `require_v4_structure` sentences, with `W` = *"a nonconformance record
> with the exposure it is measured against: the nonconformances raised, and the inspections, hours
> or value they arose from"*.
>
> ---

### Measured

**1. Does it compute today.** **YES — computes.** Band: **no band (calibration pending by ruling)**. Reading: 14 nonconformances against 300 inspections, a rate of 0.0467 for each one. 5 are still open.

**2. Named inputs no stored observation supplies.** **None** — every input this specification names by field name is present in the stored row.

**3. Governed structure?** **YES — `ncrExposureRecord`.** It is **present** in the stored row. Could a document state it in words? **YES** — an NCR log with the inspection count it is measured against.

---

## 19. Change-order frequency → **A4.6 — Change Order Frequency**

**Identifier:** `A4.6` · **Method class:** `Change_Order_Frequency` · **Tree category:** A4 Document-Derived Condition Signals · **In service:** yes

**Where it lives:** `specifications/A4_document_derived_signals.md`, section `A4.6 — Change Order Frequency`, lines **252–283**.

### Specification text, verbatim

> ## A4.6 — Change Order Frequency
>
> **Identity.** Live id `A4.6`. Method class `CO_Frequency`. Governed change events per unit of
> exposure time, with magnitude reported separately.
>
> **Required inputs.** `changeEventRegister` — a mapping, and the only input read.
>
> **Method.** `canonical_v4.change_frequency`:
> ```
> change_frequency_per_day     = governed change events / exposure days
> change_frequency_per_30_days = change_frequency_per_day * 30
> change_magnitude_net         = sum of change values / baseline contract value
> ```
> Six changes over one hundred and eighty days reads 0.0333… a day, or one per standardised thirty
> day period. **Frequency and magnitude are two quantities and are never combined into one unnamed
> composite** — that combination is what the module did before Run 28 and it is what the supplied
> contract forbids. Change type, cause, direction and contract lineage are retained on the reading.
>
> **Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
> with the standard note.
>
> **Interpretation.** The frequency says how often the scope is being changed; the magnitude says
> how much of the contract those changes represent. A project with many small changes and one with
> one enormous change are different conditions and this module reports them as two figures so they
> stay different.
>
> **Nothing to report.** The two `require_v4_structure` sentences, with `W` = *"a change event register
> with the exposure it is measured over: each change, its type, cause and value, and the span of
> time or contract value it arose against"*.
>
> ---

### Measured

**1. Does it compute today.** **NO — abstains.** Stated reason, verbatim: *"Awaiting a change event register with the exposure it is measured over: each change, its type, cause and value, and the span of time or contract value it arose against. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place."*

**2. Named inputs no stored observation supplies** (1): `changeEventRegister`

**3. Governed structure?** **YES — `changeEventRegister`.** It is **absent** from the stored row. Could a document state it in words? **YES** — a change order log with value, type and cause per change.

---

## 20. Dispute escalation index → **A4.7 — Dispute Escalation Index**

**Identifier:** `A4.7` · **Method class:** `Dispute_Escalation` · **Tree category:** A4 Document-Derived Condition Signals · **In service:** yes

**Where it lives:** `specifications/A4_document_derived_signals.md`, section `A4.7 — Dispute Escalation Index`, lines **284–316**.

### Specification text, verbatim

> ## A4.7 — Dispute Escalation Index
>
> **Identity.** Live id `A4.7`. Method class `Dispute_Escalation`. How far the project's claims have
> travelled up the project's own governed escalation process.
>
> **Required inputs.** `claimDisputeRegister` — a mapping, and the only input read.
>
> **Method.** `canonical_v4.dispute_escalation`. The register declares the project's own escalation
> process, its stages in order, and the stage each issue has reached. The module reports the
> **highest stage reached**, its **rank** among that process's stages, and
> `escalation_position` = that rank as a position on the declared process. Stage names, stage count
> and process version travel with the reading, because a rank of 3 means nothing without the process
> it is a rank on.
>
> **Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
> with the standard note. What it replaced was a generic composite — a capped request count at 0.3,
> a capped change order count at 0.3 and a document risk score at 0.4 — none of which is dispute
> evidence. **None of those three fields is read here.**
>
> **Interpretation.** The reading names the furthest point a dispute on this project has reached on
> the process the project itself declared. It is a position, not a score, and it is comparable only
> against the same process.
>
> **Nothing to report.** The two `require_v4_structure` sentences, with `W` = *"a claim and dispute
> register: the project's own governed escalation process and the stage each issue has reached on
> it, with the dates it reached them"*.
>
> **One property a reader must be told.** Missing dispute evidence cannot improve this reading.
> Run 7 removed the truthiness contribution that made an absent log and a log recording nothing
> indistinguishable, precisely so a project could not improve its condition by withholding evidence.
>
> ---

### Measured

**1. Does it compute today.** **NO — abstains.** Stated reason, verbatim: *"Awaiting a claim and dispute register: the project's own governed escalation process and the stage each issue has reached on it, with the dates it reached them. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place."*

**2. Named inputs no stored observation supplies** (1): `claimDisputeRegister`

**3. Governed structure?** **YES — `claimDisputeRegister`.** It is **absent** from the stored row. Could a document state it in words? **YES** — a claims log with the escalation stage and date reached.

---

## 21. Weather-day impact → **A4.5 — Weather Day Impact**

**Identifier:** `A4.5` · **Method class:** `Weather_Day_Impact` · **Tree category:** A4 Document-Derived Condition Signals · **In service:** yes

**Where it lives:** `specifications/A4_document_derived_signals.md`, section `A4.5 — Weather Day Impact`, lines **221–251**.

### Specification text, verbatim

> ## A4.5 — Weather Day Impact
>
> **Identity.** Live id `A4.5`. Method class `Weather_Impact`. The modelled schedule consequence of
> verified weather events.
>
> **Required inputs.** `weatherImpactEvents` — a mapping, and the only input read.
>
> **Method.** `canonical_v4.weather_day_impact`. Weather occurrence is not schedule impact. The
> method requires, per event: the event, the affected activity, the planned work, the time actually
> lost, the governing allowance or calendar, the path and its float, causal evidence, and a modelled
> consequence. It reports the **direct modelled path effect in days**, after the contract weather
> allowance and after the float on each path, per path; the reported worst path is the one with the
> greatest effect, ties broken by path identifier. A verified event costing two lost days on a
> zero-float critical activity with no mitigation has a direct modelled path effect, before recovery
> logic, of two days.
>
> **Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
> with the standard note. Until Run 28 it divided lost days by a reported float figure and banded
> the ratio; there was no activity, no path, no allowance and no causal evidence in it, and the
> current quantity is not the one that ladder was drawn over.
>
> **Interpretation.** The reading is the number of days of schedule the weather actually cost after
> the contract's own allowance and the float that protected the work — not the number of bad days.
> A project can lose ten weather days and carry a direct path effect of zero.
>
> **Nothing to report.** The two `require_v4_structure` sentences, with `W` = *"a weather impact record:
> the weather events, the activities they stopped, the time actually lost, the allowance in the
> contract calendar, and the float on the path"*.
>
> ---

### Measured

**1. Does it compute today.** **NO — abstains.** Stated reason, verbatim: *"Awaiting a weather impact record: the weather events, the activities they stopped, the time actually lost, the allowance in the contract calendar, and the float on the path. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place."*

**2. Named inputs no stored observation supplies** (1): `weatherImpactEvents`

**3. Governed structure?** **YES — `weatherImpactEvents`.** It is **absent** from the stored row. Could a document state it in words? **YES** — a weather-day log with the activities stopped and the contract allowance.

---

## 22. Subcontractor performance → **A4.8 — Subcontractor Performance**

**Identifier:** `A4.8` · **Method class:** `Subcontractor_Performance` · **Tree category:** A4 Document-Derived Condition Signals · **In service:** yes

**Where it lives:** `specifications/A4_document_derived_signals.md`, section `A4.8 — Subcontractor Performance`, lines **317–351**.

### Specification text, verbatim

> ## A4.8 — Subcontractor Performance
>
> **Identity.** Live id `A4.8`. Method class `Subcontractor_Performance`. A traceable multi-criteria
> assessment of the firms doing the work.
>
> **Required inputs.** `subcontractorAssessments` — a mapping, and the only input read.
>
> **Method.** `canonical_v4.subcontractor_performance`:
> ```
> Score_firm = sum over criteria of ( w_i * r_i ),   with sum(w_i) = 1
> ```
> Ratings of 0.80, 0.90 and 0.70 under equal weights score 0.80. Every weight must be versioned and
> provenanced; `weights`, `weights_version`, the criteria list and the evaluator travel with the
> reading. The module reports the **mean score across firms**, the **lowest score** and the firm it
> belongs to, and any critical violations recorded.
>
> **Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
> with the standard note.
>
> **Interpretation.** The mean says how the supply chain is performing on the criteria the project
> declared; the lowest score and the firm named against it are the actionable half, because the
> project manages firms, not averages.
>
> **Nothing to report.** The two `require_v4_structure` sentences, with `W` = *"a subcontractor performance
> assessment: each firm, the criteria it was rated against, the rating on each, who assessed it and
> the weights that were applied"*.
>
> **One property a reader must be told.** In the browser this module could lazily derive a single
> `subcontractorComplianceScore`. **That path is not ported and must not be reconstructed.** An
> opaque precomputed compliance score with no criteria, no ratings, no evaluator and no weights
> behind it is exactly what the supplied contract names as an invalid validation of this module. On
> the server the assessment structure is supplied or the module abstains.
>
> ---

### Measured

**1. Does it compute today.** **NO — abstains.** Stated reason, verbatim: *"Awaiting a subcontractor performance assessment: each firm, the criteria it was rated against, the rating on each, who assessed it and the weights that were applied. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place."*

**2. Named inputs no stored observation supplies** (1): `subcontractorAssessments`

**3. Governed structure?** **YES — `subcontractorAssessments`.** It is **absent** from the stored row. Could a document state it in words? **YES** — a subcontractor evaluation form with criteria, ratings and weights.

---

## 23. Procurement lead-time monitor → **A4.9 — Procurement Lead Time Monitor**

**Identifier:** `A4.9` · **Method class:** `Procurement_Lead_Time` · **Tree category:** A4 Document-Derived Condition Signals · **In service:** yes

**Where it lives:** `specifications/A4_document_derived_signals.md`, section `A4.9 — Procurement Lead Time Monitor`, lines **352–381**.

### Specification text, verbatim

> ## A4.9 — Procurement Lead Time Monitor
>
> **Identity.** Live id `A4.9`. Method class `Procurement_Lead_Time`. Item-level procurement slack.
>
> **Required inputs.** `procurementItems` — a mapping, and the only input read.
>
> **Method.** `canonical_v4.procurement_slack`, per item:
> ```
> ProcurementSlack_item = RequiredOnSiteDate - ForecastDeliveryDate      (in days)
> ```
> A required day of 100 against a forecast of 110 reads minus ten days. The module reports the
> **minimum slack across all items** and the item it belongs to, the **mean slack**, and a count of
> items in each state — `LATE`, `AT_RISK`, `ON_TIME`. **Every item is counted once**: delayed items
> are not also counted inside at-risk.
>
> **Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
> with the standard note. What it replaced was a weighted count ratio over the long-lead set — half
> weight for at-risk items, full weight for delayed ones — which contains no date and therefore no
> slack, and which the supplied contract states is not this method.
>
> **Interpretation.** The tightest slack, and the item carrying it, is the procurement exposure the
> project has to act on. A negative figure means that item is already forecast to arrive after the
> work needs it.
>
> **Nothing to report.** The two `require_v4_structure` sentences, with `W` = *"an item level procurement
> register: for each item, the date it is required on site, the date it is forecast to arrive, and
> the activity it feeds"*.
>
> ---

### Measured

**1. Does it compute today.** **NO — abstains.** Stated reason, verbatim: *"Awaiting an item level procurement register: for each item, the date it is required on site, the date it is forecast to arrive, and the activity it feeds. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place."*

**2. Named inputs no stored observation supplies** (1): `procurementItems`

**3. Governed structure?** **YES — `procurementItems`.** It is **absent** from the stored row. Could a document state it in words? **YES** — a procurement/long-lead log with required and forecast dates.

---

# Delivery Quality

## 24. Quality compliance index → **A6.1 — Quality Compliance Index**

**Identifier:** `A6.1` · **Method class:** `Quality_Compliance` · **Tree category:** A6 Delivery Quality Performance · **In service:** yes

**Where it lives:** `specifications/A6_delivery_quality.md`, section `A6.1 — Quality Compliance Index`, lines **81–134**.

### Specification text, verbatim

> ## A6.1 — Quality Compliance Index
>
> **Identity.** Live id `A6.1`. Method class `Quality_Compliance`. The share of the applicable
> quality requirements that were assessed and found satisfied.
>
> **Required inputs, by their exact `signal_inputs` field names.**
> *Governed path.* `qualityRequirementRegister` — a mapping carrying a `requirements` list, each row
> with `requirement_id`, `applicable`, `assessed`, `satisfied`, `criticality`, `source`, `status`,
> `corrective_action`, `period` and `provenance`.
> *Corpus-assembled path*, used only when the governed structure is absent. `qualityAuditScore`,
> `totalFindings`, `criticalFindings` — any one of them present triggers assembly. **The assembly
> supplies no `requirements` list**; it carries these three onto the structure as
> `recorded_audit_evidence`.
>
> **Method.**
> ```
> QualityComplianceRate = SatisfiedApplicableAssessed / ApplicableAssessed        (denominator > 0)
> ```
> A requirement with `applicable is False` is skipped entirely. A requirement not `assessed` goes to
> the **unassessed** list and enters **neither** the numerator nor the denominator. An assessed and
> unsatisfied requirement of criticality `critical` or `high` is additionally returned in its own
> **critical exceptions** list.
>
> Governing rule: `FAR 46.2`, carried on the result as `rule`.
>
> **Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending.
>
> **Interpretation.** Unassessed requirements do not count as satisfied and do not shrink the
> denominator either. A register with ninety unassessed requirements and ten satisfied ones is not
> ninety per cent compliant and is not ten per cent compliant; **it is ten of ten with ninety
> outstanding, and the reader needs both numbers.** Critical exceptions are **noncompensatory**: one
> critical exception is returned in its own list and cannot disappear inside a 99 per cent aggregate.
>
> **Nothing to report, and the not-estimable disposition.**
> 1. No governed register and no audit evidence to assemble: the structure-absent sentences, with
>    `W` = *"a governed quality requirement register"*.
> 2. Evidence not qualified for `requirement_conformance`: the qualification sentence above.
> 3. **Structure present with `recorded_audit_evidence` and no `requirements`** — the corpus path —
>    the module **computes** with `quality_compliance_rate: null` and
>    `disposition: "NOT_ESTIMABLE"`, reason verbatim: `"the project's Quality Audit evidence is
>    recorded below, but it establishes no applicable, assessed and satisfied requirement
>    population, so no compliance rate is measurable and none is estimated"`. An audit score, a
>    findings count and a critical-findings count are **summaries**, and section 13 forbids
>    substituting a summary for a denominator.
> 4. A `requirements` key present but empty or unreadable: `"Awaiting a governed quality requirement
>    register. No entries are recorded, so there is nothing to assess and no figure is produced in
>    place of one."`
>
> **One property a reader must be told.** `qualityDeficienciesNoted` is a meeting-minute **mention**
> and is not read. A6.1's old prerequisite on it is gone: a project holding a real Quality Audit
> Report is no longer refused because nobody mentioned deficiencies in the minutes.
>
> ---

### Measured

**1. Does it compute today.** **NO — abstains.** Disposition `NOT_ESTIMABLE`. Stated reason, verbatim: *"the project's Quality Audit evidence is recorded below, but it establishes no applicable, assessed and satisfied requirement population, so no compliance rate is measurable and none is estimated"*

**2. Named inputs no stored observation supplies** (13): `qualityRequirementRegister`, `requirements`, `requirement_id`, `applicable`, `assessed`, `satisfied`, `criticality`, `source`, `status`, `corrective_action`, `period`, `provenance`, `recorded_audit_evidence`

**3. Governed structure?** **YES — `qualityRequirementRegister`.** It is **absent** from the stored row. Could a document state it in words? **YES** — a quality audit report printing applicable, assessed and satisfied per requirement; Run 87 built exactly this.

---

## 25. Safety performance index → **A6.2 — Safety Performance Index**

**Identifier:** `A6.2` · **Method class:** `Safety_Performance` · **Tree category:** A6 Delivery Quality Performance · **In service:** yes

**Where it lives:** `specifications/A6_delivery_quality.md`, section `A6.2 — Safety Performance Index`, lines **135–191**.

### Specification text, verbatim

> ## A6.2 — Safety Performance Index
>
> **Identity.** Live id `A6.2`. Method class `Safety_Performance`. The OSHA recordable incidence rate,
> and the leading indicators, reported as **two families that are never averaged**.
>
> **Required inputs, by their exact `signal_inputs` field names.**
> *Governed path.* `safetyPerformanceRecord` — a mapping with `recordable_cases`,
> `employee_hours_worked`, `leading_indicators`, `severe_events`, `reporting_period`, `provenance`,
> and optionally `document_stated_incident_rate`.
> *Corpus-assembled path*, used when the governed structure is absent. `oshaRecordableIncidents` →
> `recordable_cases`; `totalManhours` → `employee_hours_worked`; `oshaIncidentRate` →
> `document_stated_incident_rate`; `reportPeriod` → `reporting_period`. Any one of the first three
> present triggers assembly. A quantity the corpus does not carry does not appear on the structure.
>
> **Method — lagging.** The OSHA identity exactly as supplied:
> ```
> IncidenceRate = RecordableCases * 200000 / EmployeeHoursWorked
> ```
> Governing rule: `OSHA incidence rate`, carried on the result as `rule`.
>
> **Method — leading.** Governed proactive measures are reported as recorded, each with its
> indicator, value, period and provenance. **There is no combined score.** Averaging the two families
> without a governed combination policy is forbidden, none is supplied, and none is computed.
>
> **Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending.
>
> **Interpretation.** The incidence rate is exposure-normalised: it says how many recordable cases
> occurred per 200,000 employee hours, which is roughly one hundred full-time workers for a year. It
> is comparable between projects of different size, and a raw case count is not. **Zero recordables
> alone never produces a favourable system claim** — `system_claim` is always `None`; the rate is a
> rate.
>
> **Nothing to report, and the two lagging dispositions.**
> 1. No governed record and nothing to assemble: the structure-absent sentences, with `W` = *"a
>    governed safety exposure and leading-indicator record"*.
> 2. Evidence not qualified for `safety_measurement`: the qualification sentence above.
> 3. Cases and hours not **both** recorded as numbers — the module still **computes**, with
>    `incidence_rate: null`, `lagging_disposition: "ABSTAIN_NO_EXPOSURE_DATA"` and reason verbatim:
>    `"recordable cases and employee hours worked are not both recorded, so no exposure-normalised
>    rate is computed and no substitute is used"`. The leading branch still reports.
> 4. Hours recorded at or below zero: `incidence_rate: null`,
>    `lagging_disposition: "INVALID_DENOMINATOR"`, reason verbatim: `"no employee hours worked are
>    recorded for this period, so an exposure-normalised rate has no denominator"`. **Hours are
>    never fabricated.**
> 5. No leading indicators: `leading_disposition: "ABSTAIN_NO_LEADING_EVIDENCE"`, with the lagging
>    branch unaffected.
>
> **One property a reader must be told, and it is the one that matters most here.** A rate **stated
> by a document** is carried out as `document_stated_incident_rate` and is **never** used as the
> measurement. Executing the upstream extraction branch proved a stated rate is emitted unchecked: a
> document asserting 99.9 survived beside a recorded 3-cases-per-200,000-hours pair. A stated rate is
> a document's claim; the identity above is a measurement. Both travel, under names that say which is
> which. A **meeting-minute incident mention is never an incidence-rate numerator**;
> `safetyIncidentsDiscussed` is not read.
>
> ---

### Measured

**1. Does it compute today.** **YES — computes.** Band: **no band (calibration pending by ruling)**. Reading: recordable cases and employee hours worked are not both recorded, so no exposure-normalised rate is computed and no substitute is used

**2. Named inputs no stored observation supplies** (10): `safetyPerformanceRecord`, `recordable_cases`, `employee_hours_worked`, `leading_indicators`, `severe_events`, `reporting_period`, `provenance`, `document_stated_incident_rate`, `oshaRecordableIncidents`, `reportPeriod`

**3. Governed structure?** **YES — `safetyPerformanceRecord`.** It is **absent** from the stored row. Could a document state it in words? **YES** — recordable cases and hours worked are printed on an OSHA 300A.

---

## 26. Environmental compliance rate → **A6.3 — Environmental Compliance Rate**

**Identifier:** `A6.3` · **Method class:** `Environmental_Compliance` · **Tree category:** A6 Delivery Quality Performance · **In service:** yes

**Where it lives:** `specifications/A6_delivery_quality.md`, section `A6.3 — Environmental Compliance Rate`, lines **192–245**.

### Specification text, verbatim

> ## A6.3 — Environmental Compliance Rate
>
> **Identity.** Live id `A6.3`. Method class `Environmental_Compliance`. The share of applicable
> environmental permit requirements that were assessed and found satisfied.
>
> **Required inputs, by their exact `signal_inputs` field names.**
> *Governed path.* `environmentalRequirementRegister` — a mapping with `jurisdiction`,
> `permitting_authority`, `site_id`, `permit_id`, `permit_version`, `operator_status`, `provenance`
> and a `requirements` list.
> *Corpus-assembled path*, used when the governed structure is absent. `environmentalComplianceRate`
> and `environmentalViolations` — either present triggers assembly, and they are carried as
> `recorded_environmental_evidence`. **The assembly deliberately supplies no jurisdiction, no
> permitting authority and no permit id**, because the corpus carries none and inventing any one of
> them would be inventing regulatory applicability.
>
> **Method.**
> ```
> EnvironmentalComplianceRate = SatisfiedApplicableAssessed / ApplicableAssessed
> ```
> with the same skip-if-not-applicable, unassessed-counts-nowhere and noncompensatory-critical rules
> as A6.1.
>
> **Applicability comes first, and it is a rule, not a measurement.** The permitting authority is
> **read from the evidence** and may be EPA, state, tribal, local or another authority. Only where it
> is exactly `"EPA"` is the governing rule set to the EPA Construction General Permit 2022; otherwise
> `rule` is `null` and the result carries the note *"the permitting authority for this site is not
> EPA, so the EPA Construction General Permit is not the governing instrument here"*. **EPA
> applicability is never assumed and the function has no branch that could hard-code it.**
>
> **Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending.
>
> **Interpretation.** The rate is meaningful only against a named permit issued by a named authority
> in a named jurisdiction. Without those three, a compliance percentage is a number about nothing,
> which is why the module refuses to form one rather than reporting the figure the document asserts.
>
> **Nothing to report, and the two non-estimable dispositions.**
> 1. No governed register and nothing to assemble: the structure-absent sentences, with `W` = *"a
>    governed environmental permit and requirement register"*.
> 2. Evidence not qualified for `environmental_conformance`: the qualification sentence above.
> 3. **Authority or jurisdiction not established** — the module **computes**, with
>    `environmental_compliance_rate: null`, `disposition: "APPLICABILITY_NOT_ESTABLISHED"`, reason
>    verbatim: `"the jurisdiction and permitting authority for this site are not established, so
>    environmental conformance is not assessed"`. This is the disposition the corpus-assembled path
>    always reaches.
> 4. Authority and jurisdiction established but no requirement list:
>    `disposition: "NOT_ESTIMABLE"`, reason verbatim: `"no applicable environmental requirement
>    register is recorded"`.
>
> Where recorded evidence is carried, it travels with the note verbatim: *"a rate asserted by the
> source document and a reported violations count; neither is an applicable/assessed/satisfied
> requirement population, so neither is used as the environmental compliance rate"*.
>
> ---

### Measured

**1. Does it compute today.** **NO — abstains.** Disposition `APPLICABILITY_NOT_ESTABLISHED`. Stated reason, verbatim: *"the jurisdiction and permitting authority for this site are not established, so environmental conformance is not assessed"*

**2. Named inputs no stored observation supplies** (10): `environmentalRequirementRegister`, `jurisdiction`, `permitting_authority`, `site_id`, `permit_id`, `permit_version`, `operator_status`, `provenance`, `requirements`, `recorded_environmental_evidence`

**3. Governed structure?** **YES — `environmentalRequirementRegister`.** It is **absent** from the stored row. Could a document state it in words? **YES** — a permit schedule with jurisdiction, authority and per-requirement status; Run 87 built exactly this.

---

## 27. Contractor performance assessment → **A6.4 — Contractor Performance Assessment Signal**

**Identifier:** `A6.4` · **Method class:** `Contractor_Performance` · **Tree category:** A6 Delivery Quality Performance · **In service:** yes

**Where it lives:** `specifications/A6_delivery_quality.md`, section `A6.4 — Contractor Performance Assessment Signal`, lines **246–288**.

### Specification text, verbatim

> ## A6.4 — Contractor Performance Assessment Signal
>
> **Identity.** Live id `A6.4`. Method class `Contractor_Performance`. The governed ingestion of an
> official or internal contractor performance assessment.
>
> **Required inputs.** `contractorAssessmentRecord` — a mapping, and the only input read. There is no
> corpus-assembled path. It carries `source_system`, `assessment_id`, `contract_id`,
> `assessment_period`, `status`, `factor_definitions_version`, `factor_ratings`, `narratives`,
> `contractor_comments_state`, `agency_review_state`, `reviewer`, `data_origin` and `provenance`.
>
> **Method — a decision rule, not a formula.**
> ```
> is_official_cpars_record = (source_system == "CPARS") AND assessment_id is present
> label = "CPARS past-performance record"                     when that holds
>         "internal Contractor Performance Assessment Signal"  otherwise
> ```
> **The label is derived, never supplied.** An internal assessment is labelled internal and **can
> never carry the CPARS label**: labelling an internal project score as CPARS or as an official
> past-performance rating is forbidden. Factor ratings are preserved row by row with their narrative
> and critical flag, and the worst or critical factor is returned separately.
>
> Governing rule: `FAR 42.15`, carried on the result as `rule`.
>
> **Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending.
> **No aggregate is computed** unless a governed aggregation policy is supplied, because inventing
> contractor-assessment weights is forbidden; `aggregate` is otherwise `None`.
>
> **Interpretation.** An official CPARS record is a rating an agency has made and stands behind. An
> internal signal is the project's own opinion of its contractor. They look alike on a page and mean
> entirely different things, which is why this module derives the label from the source system and
> the assessment id rather than accepting one.
>
> **Nothing to report.**
> 1. Structure absent or not a mapping: the structure-absent sentences, with `W` = *"a governed
>    contractor assessment record"*.
> 2. Evidence not qualified for `official_assessment_ingestion`: the qualification sentence above.
> 3. No `factor_ratings` list, or an empty one — the module **computes**, with
>    `disposition: "ABSTAIN_NO_GOVERNED_ASSESSMENT"` and reason verbatim: `"no governed official or
>    internal contractor assessment with factor ratings is recorded, so no signal is produced"`.
>    The derived label and `is_official_cpars_record` are still reported.
>
> ---

### Measured

**1. Does it compute today.** **NO — abstains.** Disposition `NOT_ESTIMABLE_STRUCTURE_ABSENT`. Stated reason, verbatim: *"Awaiting a governed contractor assessment record. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place."*

**2. Named inputs no stored observation supplies** (14): `contractorAssessmentRecord`, `source_system`, `assessment_id`, `contract_id`, `assessment_period`, `status`, `factor_definitions_version`, `factor_ratings`, `narratives`, `contractor_comments_state`, `agency_review_state`, `reviewer`, `data_origin`, `provenance`

**3. Governed structure?** **YES — `contractorAssessmentRecord`.** It is **absent** from the stored row. Could a document state it in words? **YES** — a CPARS-shaped assessment prints its factor ratings and narratives.

---

# Systems and Dynamics

## 28. DSM rework propagation → **A5.1 — DSM Rework Propagation**

**Identifier:** `A5.1` · **Method class:** `DSM_Rework_Cat5` · **Tree category:** A5 System Dynamics & Complexity · **In service:** yes

**Where it lives:** `specifications/A5_system_dynamics.md`, section `A5.1 — DSM Rework Propagation`, lines **32–69**.

### Specification text, verbatim

> ## A5.1 — DSM Rework Propagation
>
> **Identity.** Live id `A5.1`. Method class `DSM_Rework_Cat5`. How rework started in one part of the
> design spreads to the rest of it through the dependencies between them.
>
> **Required inputs.** `dsmDependencyModel` — a mapping, and the only input read. It must carry named
> nodes, a directed dependency matrix `D`, a **declared matrix orientation**, edge strengths, a seed
> rework vector, and a stopping or cycle policy.
>
> **Method.**
> ```
> R(k+1) = D * R(k)          under the declared orientation
> ```
> Oracle from the source: with `D = [[0, 0.5], [0, 0]]` and `R0 = [0, 1]`, then `R1 = [0.5, 0]` and
> `R2 = [0, 0]`. The module reports the propagated rework per node, the number of waves, the most
> affected node (ties broken by node name), the total propagated rework, and **why the propagation
> stopped** — either `CONVERGED` or having reached the step limit the model declares.
>
> **Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending.
> **No ladder was ever drawn over propagated rework** and inventing one is a decision to be made from
> evidence, not here.
>
> **Interpretation.** The reading says which part of the design absorbs the most consequence when
> rework starts somewhere else. It is a property of the *topology*, so it identifies structural
> fragility that no schedule or cost figure would show.
>
> **Nothing to report.** The two sentences above, with `W` = *"a dependency matrix for the design: the parts
> of the design, which of them depend on which others and how strongly, and the rework the
> propagation starts from"*.
>
> **What it is waiting for, stated plainly.** A governed design structure matrix. **`cpi` and `spi`
> may not be substituted for dependency topology** and are not read. Before Run 7 this module held
> nine coefficients and an initiating wave as literals: handed an empty dictionary it read Amber, and
> handed a complete project it read the same Amber, because nothing about a project could reach the
> arithmetic.
>
> ---

### Measured

**1. Does it compute today.** **NO — abstains.** Stated reason, verbatim: *"Awaiting a dependency matrix for the design: the parts of the design, which of them depend on which others and how strongly, and the rework the propagation starts from. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place."*

**2. Named inputs no stored observation supplies** (2): `dsmDependencyModel`, `D`

**3. Governed structure?** **YES — `dsmDependencyModel`.** It is **absent** from the stored row. Could a document state it in words? **PARTLY** — a dependency matrix CAN be printed, but no routine project document prints one; it is an engineering artefact prepared for this method.

---

## 29. Rework feedback loop → **A5.5 — Rework Feedback Loop**

**Identifier:** `A5.5` · **Method class:** `Rework_Feedback_Loop` · **Tree category:** A5 System Dynamics & Complexity · **In service:** yes

**Where it lives:** `specifications/A5_system_dynamics.md`, section `A5.5 — Rework Feedback Loop`, lines **151–188**.

### Specification text, verbatim

> ## A5.5 — Rework Feedback Loop
>
> **Identity.** Live id `A5.5`. Method class `Rework_Feedback`. A genuine time-dependent stock and
> flow model of work coming back.
>
> **Required inputs.** `systemDynamicsModel` — a mapping, and the only input read. It must carry the
> stock of work in the backlog, the work arriving and completed each step, and the share of completed
> work that returns as rework.
>
> **Method.**
> ```
> Backlog(t+1)       = Backlog(t) + NewWork(t) + ReworkGenerated(t) - WorkCompleted(t)
> ReworkGenerated(t) = ErrorRate(t) * WorkCompleted(t)
> ```
> Oracle from the source: `Backlog0 = 10`, `NewWork = 5`, `WorkCompleted = 8`, `ErrorRate = 0.25`
> gives `ReworkGenerated = 2` and `Backlog1 = 9`. The module reports the initial and final backlog,
> the number of steps run, the full per-step trace, the totals of new work, completed work and rework
> generated, the rework share of completed work, and an **accounting residual** so a reader can check
> the stock balanced.
>
> **Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending.
>
> **Interpretation.** A backlog that rises while work is being completed is the signature of a
> feedback loop: the project is generating work faster than it clears it, and the rework share says
> how much of that is self-inflicted.
>
> **Nothing to report.** The two sentences above, with `W` = *"a system dynamics rework model: the stock of
> work in the backlog, the work arriving and completed each step, and the share of completed work
> that returns as rework"*.
>
> **What it is waiting for, stated plainly.** A stock-and-flow model with a time step. **A weighted
> CPI/RFI/change-order score is not a feedback loop.** Before Run 29 this module computed exactly
> that: a capped request count at 0.3, a capped change order count at 0.3 and the shortfall of the
> cost index at 0.4 — no stock, no flow, no time and no feedback. **None of those three inputs is
> read here.**
>
> ---

### Measured

**1. Does it compute today.** **NO — abstains.** Stated reason, verbatim: *"Awaiting a system dynamics rework model: the stock of work in the backlog, the work arriving and completed each step, and the share of completed work that returns as rework. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place."*

**2. Named inputs no stored observation supplies** (1): `systemDynamicsModel`

**3. Governed structure?** **YES — `systemDynamicsModel`.** It is **absent** from the stored row. Could a document state it in words? **NO** — a calibrated stock-and-flow model with rates and a rework fraction is a simulation artefact, not something a document states in words.

---

# Evidence Quality

## 30. Information completeness ratio → **C1.5 — Information Completeness Ratio**

**Identifier:** `C1.5` · **Method class:** `Information_Completeness_Ratio` · **Tree category:** C1 Data Integrity · **In service:** yes

**Where it lives:** `specifications/C1_data_integrity.md`, section `C1.5 — Information Completeness Ratio`, lines **223–265**.

### Specification text, verbatim

> ## C1.5 — Information Completeness Ratio
>
> **Identity.** Live id `C1.5`. Method class `Information_Completeness_Ratio`. **Package-level**
> coverage: whether the documents the assessment needs are there and usable.
>
> **Required inputs.** `informationPackageRecord` — a mapping, and the only input read. It carries
> `package_id`, `package_version` and a `components` list; each component carries `component_id` (or
> `domain`), `applicable`, `required`, `present`, `critical`, `mandatory_fields` and `values`.
>
> **Method.**
> ```
> applicable      = components with applicable != False and required != False
> present_usable  = applicable components that are present AND usable
> usable          = NOT (the component has mandatory_fields and ALL of them are null)
> InformationCompleteness = |present_usable| / |applicable|
> ```
> A component that is absent goes to `missing_domains`; one that is present but unusable goes to
> `unusable_components`. A critical component in either list also goes to
> `missing_critical_domains`.
>
> **Bands.** **None, and this module does not vote.** Calibration-pending, metadata only.
>
> **Interpretation.** **"Usable" is the load-bearing word.** A component whose mandatory internal
> fields are all missing is not usable merely because a filename exists. A package can be 100 per
> cent present and materially incomplete, and this module is what makes that visible.
>
> **Nothing to report, and the one non-measured disposition.**
> 1. Structure absent or not a mapping: the two sentences above, with `W` = *"a governed information
>    package definition"*.
> 2. `components` absent, empty or unreadable: `"Awaiting the applicable required information
>    package. No entries are recorded, so there is nothing to assess and no figure is produced in
>    place of one."`
> 3. No applicable required component — the module **computes**, with
>    `information_completeness: null` and `disposition: "NO_APPLICABLE_COMPONENT"`.
>
> **One property a reader must be told.** **This is not C1.1.** It reads a different key from a
> different structure so the two cannot silently become the same measure: C1.1 measures fields inside
> one use's contract, C1.5 measures whether the package's components are there at all. A project can
> be field-complete on what it has and package-incomplete on what it is missing, and both readings
> are needed.
>
> ---

### Measured

**1. Does it compute today.** **NO — abstains.** Disposition `NOT_ESTIMABLE_STRUCTURE_ABSENT`. Stated reason, verbatim: *"Awaiting a governed information package definition. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place."*

**2. Named inputs no stored observation supplies** (12): `informationPackageRecord`, `package_id`, `package_version`, `components`, `component_id`, `domain`, `applicable`, `required`, `present`, `critical`, `mandatory_fields`, `values`

**3. Governed structure?** **YES — `informationPackageRecord`.** It is **absent** from the stored row. Could a document state it in words? **PARTLY** — a document-control transmittal register could state components present against required, but the per-component criticality and mandatory-field lists are a contract the platform defines, not a document.

---

# Signal Synthesis

## 31. Conservative dominance → **B1.1 — Conservative Dominance**

**Identifier:** `B1.1` · **Method class:** `Conservative_Dominance` · **Tree category:** B1 Signal Synthesis · **In service:** yes

**Where it lives:** `specifications/B1_signal_synthesis.md`, section `B1.1 — Conservative Dominance`, lines **99–152**.

### Specification text, verbatim

> ## B1.1 — Conservative Dominance
>
> **Identity.** Live id `B1.1`. Method class `Conservative_Dominance`. The decision is taken against
> the **worst state the evidence supports**.
>
> **Required inputs, by their exact `signal_inputs` field names.** `signals` — a mapping, and it
> must carry `signals.cusum`; the module refuses outright otherwise. Within it, `signals.evm`,
> `signals.mc`, `signals.cusum` and `signals.doc`, each carrying a `status`. Unlike B1.2–B1.4 this
> module reads the assembled mapping directly rather than through the governed signal list.
>
> **Method — a decision rule, and it has no parameter.**
> ```
> bands      = each of (evm, mc, cusum, doc) normalised onto one band, or None where absent
>              or outside the platform's status vocabulary
> dominant   = the most severe band among those present, or None where none is present
> all_green  = every one of the four is present AND every one is Green
>
> dominant is None                    -> state = the decision layer's own health state
> dominant == "Green" and not all_green -> state = "Amber"
> otherwise                           -> state = dominant
> ```
>
> **Bands.** This module **does** emit a band: `status_color` is the state above, in the platform's
> capitalised vocabulary. **No threshold, weight or constant is introduced anywhere in the rule** —
> it is a maximum over bands the signals themselves already assigned.
>
> **Interpretation.** **Conservative dominance is not a count.** Before Run 20 this module returned
> the shared decision-layer health state, which is a *counting* rule — two or more Red signals, or a
> cumulative-sum breach with a Red forecast, reach Red-review; everything else not uniformly Green
> reaches Amber. So a project whose worst signal was Red, **alone**, reported Amber and selected
> routine early-warning review rather than escalation: adverse evidence was outvoted by the count of
> signals that had nothing adverse to say. **A single adverse signal is enough, because that is
> precisely what "conservative" means.** The rule is also idempotent, which matters because three of
> the four signals are readings of one earned-value measurement — a counting rule was counting one
> measurement up to three times, and a dominance rule cannot.
>
> **The conservative treatment of absent evidence is part of the rule, not an exception to it.** A
> dominance rule over the signals *present* would let an absent signal read as agreement: three
> Greens and one missing would dominate to Green, which is the strongest claim available and the one
> the missing signal never made. **The calmest band is reachable only on complete evidence, and
> incomplete evidence cannot be calmer than Amber.** That is the middle branch above.
>
> **What is reported alongside, and why.** `decision_layer_state` — the decision layer's own health
> state — is reported **beside** the dominance state, never reconciled with it. B3.1 reads the same
> decision layer to decide *which action and whose authority*, which is a different question from
> *what the evidence most adversely supports*. The two states are shown side by side so a reader can
> see both and is never shown one while believing it is the other. `evidence_complete` and
> `signal_bands` travel with them.
>
> **Nothing to report.** `signals` absent, or `signals.cusum` absent:
> `"Insufficient data: upload required documents"`.
>
> ---

### Measured

**1. Does it compute today.** **NO — abstains.** Stated reason, verbatim: *"Insufficient data: upload required documents"*

**2. Named inputs no stored observation supplies** (6): `signals`, `signals.cusum`, `signals.evm`, `signals.mc`, `signals.doc`, `status`

**3. Governed structure?** **NO.** This module is defined on plain numeric facts a document states directly; it names no governed structure in `CANONICAL_STRUCTURE_KEYS` or any of the v3–v8 layers.

---

## 32. Weighted voting → **B1.2 — Weighted Voting**

**Identifier:** `B1.2` · **Method class:** `Weighted_Voting` · **Tree category:** B1 Signal Synthesis · **In service:** yes

**Where it lives:** `specifications/B1_signal_synthesis.md`, section `B1.2 — Weighted Voting`, lines **153–203**.

### Specification text, verbatim

> ## B1.2 — Weighted Voting
>
> **Identity.** Live id `B1.2`. Method class `Weighted_Voting`. Class-weighted voting over the
> governed signals.
>
> **Required inputs, by their exact `signal_inputs` field names.**
> `signals` — the assembled arms, read through `governed_signals_from_project`.
> `signalWeightPolicy` — a mapping carrying `weights` (a weight per signal id), `set_by` and
> `authority`. **Required. There is no default weight anywhere in this function**, so a project with
> no policy cannot be given one implicitly.
>
> **Method.**
> ```
> Vote(c) = sum over voting signals i of  w_i * I(s_i = c)
> winner  = argmax over c of Vote(c)
> ```
> Weights must be non-negative and are **normalised to sum to one over the eligible independent
> signals actually voting**, which is what makes class votes comparable between projects with
> different signal counts. The classes are the four severity classes in order.
>
> **Bands.** The winner is emitted as `status_color`. Where there is no unique winner,
> `status_color` is `None` and `tied_classes` names the tied classes.
>
> **Interpretation.** The weighted vote says which state carries most of the authority-assigned
> weight, and the normalised weights and their provenance travel with the reading so a reader can see
> whose judgment produced them.
>
> **Nothing to report.**
> 1. No governed signals: the shared sentence above.
> 2. Every governed signal abstained: `"every governed signal for this project abstained, so there
>    is nothing to weigh and no vote is reported"`.
> 3. `signalWeightPolicy` absent or not a mapping: `"Awaiting a weighting policy for this project's
>    governed signals. A weighted vote cannot be taken without stated weights, and none is
>    assumed."`
> 4. The policy states no weights: `"The a weighting policy for the project's governed signals: a
>    weight for each signal, and the authority that set it provided for this project states no
>    weights, so no weighted vote is taken and no weight is assumed for any signal."`
> 5. The policy omits a weight for a voting signal: the same sentence stem ending `"...does not
>    state a weight for every signal being voted on, so no weighted vote is taken and no weight is
>    assumed for the signals it omits."`
> 6. A negative weight: the same stem ending `"...states a negative weight, which a vote is not
>    defined on, so no weighted vote is taken."`
> 7. Every voting signal weighted zero: `"the weighting policy for this project gives every voting
>    signal no weight at all, so no winner is reported"`.
>
> **The tie policy is declared, not resolved.** A tie between classes returns **no winner** and says
> so. Choosing a winner from a tie is a governance decision with a direction — the calmer class or
> the more severe one — and it is not this module's to make.
>
> ---

### Measured

**1. Does it compute today.** **NO — abstains.** Stated reason, verbatim: *"Insufficient data: upload required documents"*

**2. Named inputs no stored observation supplies** (6): `signals`, `governed_signals_from_project`, `signalWeightPolicy`, `weights`, `set_by`, `authority`

**3. Governed structure?** **YES — `signalWeightPolicy`.** It is **absent** from the stored row. Could a document state it in words? **YES-BUT** — a weighting policy with who set it and under what authority is stateable in words, but it is a GOVERNANCE artefact about the platform, not a fact about the project.

---

# Decision Optimisation

## 33. What-if scenario matrix → **B4.4 — What-If Scenario Matrix**

**Identifier:** `B4.4` · **Method class:** `WhatIf_Scenario_Matrix` · **Tree category:** B4 Decision Optimization · **In service:** yes

**Where it lives:** `specifications/B4_decision_optimisation.md`, section `B4.4 — What-If Scenario Matrix`, lines **151–204**.

### Specification text, verbatim

> ## B4.4 — What-If Scenario Matrix
>
> **Identity.** Live id `B4.4`. Method class `WhatIf_Scenario_Matrix`. Candidate actions compared
> across scenarios.
>
> **Required inputs.** `actionScenarioMatrix` — a mapping, and the only input read. It must carry the
> **actions** being compared (each with an identity), the **scenarios** they are compared under, an
> outcome for **every** action-scenario pair, the declared `orientation`, the `units` and the
> `model_version`. Optionally, scenario probabilities.
>
> **Method — a comparison, not a choice.**
> ```
> rows    = candidate ACTIONS
> columns = SCENARIOS
> cells   = the declared outcome for each (action, scenario) pair
> matrix[a][s] = cell(a, s)          for every action a and every scenario s
> ```
> Where — and **only** where — the governed structure states scenario probabilities:
> ```
> ExpectedValue(a) = sum over s of  cell(a, s) * P(s)
> ```
> Otherwise `expected_values` is `null`. **No probability is invented, so no expected value is
> computed unless the governed structure states the probabilities.**
>
> **Bands.** **None**, and the authority boundary above applies in full.
>
> **The refusal to choose, and it is on the result.** `recommended_action` is **always `None`**, and
> the result carries `recommendation_reason` verbatim: *"this measure compares alternatives under
> scenarios and applies no decision rule; it names no action"*. The evidence sentence says the same
> thing: *"N actions are compared across M scenarios; this measure applies no decision rule and names
> no action."* **A specification applying this module must not name a preferred action, must not rank
> the actions, and must not describe any action as best, safest or recommended.** Applying a decision
> rule to this same matrix is a different module's work, and a human authorises the selection.
>
> **Interpretation.** The matrix says what each action is expected to produce under each scenario, in
> the declared units and the declared orientation. It is the material for a decision; it is not the
> decision.
>
> **Nothing to report.**
> 1. Structure absent or not a mapping: the two sentences above, with `W` = *"a governed
>    action-by-scenario matrix: the actions being compared, the scenarios they are compared under,
>    and an outcome for every pair"*.
> 2. No actions or no scenarios recorded: `"Awaiting a governed action-by-scenario matrix: the
>    actions being compared, the scenarios they are compared under, and an outcome for every pair.
>    No entries are recorded, so there is nothing to solve and no figure is produced in place of
>    one."`
> 3. **An action without an identity refuses**, in the words `canonical_v7` raises for it. Several
>    forecast formulas with no action identity are not a what-if matrix, which is why that case is a
>    refusal rather than a default naming.
> 4. A missing cell: the matrix must be complete, and an incomplete one refuses in the words
>    `canonical_v7` raises for the missing pair.
>
> ---

### Measured

**1. Does it compute today.** **NO — abstains.** Disposition `NOT_ESTIMABLE_STRUCTURE_ABSENT`. Stated reason, verbatim: *"Awaiting a governed action-by-scenario matrix: the actions being compared, the scenarios they are compared under, and an outcome for every pair. This measure is named for a method that cannot be carried out without it, so no reading is reported and no other figure is used in its place."*

**2. Named inputs no stored observation supplies** (4): `actionScenarioMatrix`, `orientation`, `units`, `model_version`

**3. Governed structure?** **YES — `actionScenarioMatrix`.** It is **absent** from the stored row. Could a document state it in words? **PARTLY** — an options-vs-scenarios table can be printed in an options appraisal, but the outcome for every pair is analysis output, not a stated project fact.

---

# Closing statements

## The governed-structure count — the owner's headline rule

The owner's rule is that **no module is defined on a structure**. Against the tree: **27 of the 33 retained modules are defined on a governed structure**; only 6 are not.

The six that are **not** structure-defined — the only six that satisfy the rule as written — are:

- **A1.7 TCPI** — computes, band Red
- **A1.8 Variance at Completion** — computes, band Red
- **A1.2 CUSUM Anomaly Monitor** — computes, band green
- **A1.5 ARIMA CPI Forecast** — computes, band None
- **A3.2 Contingency Burn Rate** — computes, band None
- **B1.1 Conservative Dominance** — abstains

Both voting modules (A1.7, A1.8) are in that six, and both compute Red today. So the part of the instrument that actually moves project status is structure-free; the rule bites on everything else.

Of the 27 structure-defined modules, the structures split as follows on the question §4.3 asks — *could a document state this in words?*

- **Document-stateable (23):** A1.6 (`timePhasedBaseline`), A1.9 (`expenditureBaseline`), A1.11 (`independentEacPair`), A2.7 (`milestoneForecastHistory`), A2.8 (`lookAheadSchedule`), A2.9 (`resourceProfile`), A2.1 (`scheduleNetwork`), A3.3 (`productionOutputRecord`), A3.6 (`costRiskModel`), A3.5 (`overheadAllocationBase`), A4.2 (`rfiEventLog`), A4.3 (`submittalDecisionRegister`), A4.4 (`ncrExposureRecord`), A4.6 (`changeEventRegister`), A4.7 (`claimDisputeRegister`), A4.5 (`weatherImpactEvents`), A4.8 (`subcontractorAssessments`), A4.9 (`procurementItems`), A6.1 (`qualityRequirementRegister`), A6.2 (`safetyPerformanceRecord`), A6.3 (`environmentalRequirementRegister`), A6.4 (`contractorAssessmentRecord`), B1.2 (`signalWeightPolicy`)
- **Partly / an artefact prepared for the method (3):** A5.1 (`dsmDependencyModel`), C1.5 (`informationPackageRecord`), B4.4 (`actionScenarioMatrix`)
- **Not document-stateable (1):** A5.5 (`systemDynamicsModel`)

This is reported, not ruled. The judgement offered is whether a routine project document could print the thing; the owner's rule is his to apply.

## Real versus harness

**Every measurement in this report is real.** All 33 §4.1 lines are production `registry.run_module` dispatches on a stored `signal_inputs` row. No `ANTHROPIC_API_KEY` was present, no extraction was invoked, and neither the StubExtractor nor the recorded applier was reached. Nothing here is a stub reported as the model's behaviour.

## What changed

**Nothing but this file.** No specification, no code, no migration, no rename, no `SIMULATION_VERSION` move. `T6_HANDOFF.md` was read and deliberately NOT appended to, because §6.1 forbids changing any source file. `git status --porcelain` shows only this report, and after its commit shows nothing.
