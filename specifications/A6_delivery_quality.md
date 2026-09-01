# Category A6 — Delivery Quality Performance

Four modules: A6.1, A6.2, A6.3, A6.4. All four moved here from the former Category 8 Governance
because they describe **project performance**, not authority.

**All four are bandless.** Every one of them is routed through `models_cat89._route`, which sets
`status_color: None` and `band_asserted: False` on construction and **re-asserts `status_color =
None` after the canonical result is merged in**, so that no field arriving from the canonical
function can introduce a colour. The route's own comment on that line is *"no band is invented"*.
The Run-31 contract's section 53 forbids inventing a status threshold for any of them.

**No band may be attached to any module in this category.**

## The three ways a module here has nothing to report, and the exact words

**1. The structure is absent and the corpus cannot build it.** `canonical_v6.v6_structure` raises,
and the route first asks `_assemble` whether the project's own extracted evidence supports the
structure. Only if that returns nothing does the module abstain, in one of two forms, writing `W`
for the module's plain-words structure description:

- **Absent:** `"Awaiting W. This measure is named for a method that cannot be carried out without
  it, so no reading is reported and no other figure is used in its place."`
- **Present but not a mapping:** `"The information provided for this project in place of W is not
  in a form this measure can read, so no reading is taken from it."`

**2. The evidence is not qualified for the module's own use.** This is the INNER gate, reached only
after the boundary above has been passed. All four modules are constructed `gated=True`, so the
structure is put through Category 9 qualification for the module's own declared use before the
canonical function is reached. Where it does not qualify, the module abstains in these exact words:

> `"The evidence supplied for this measure has not been qualified for governance use, so no
> governed result is produced from it and no figure is used in its place."`

The declared uses are `A6.1 requirement_conformance`, `A6.2 safety_measurement`,
`A6.3 environmental_conformance`, `A6.4 official_assessment_ingestion`. None of those four uses
carries an additional requirement in `USE_REQUIREMENTS`; **a use absent a requirement does not
acquire one by default.**

**3. The structure is present and qualified, but does not establish the population the measure is
defined over.** This is **not an abstention.** The module **computes**, reports the measure as
`None` with a named disposition, and carries the real evidence out beside it. These dispositions
and their reasons are given per module below and are quoted verbatim by a specification applying
them.

## The qualification boundary, and it fires BEFORE anything below

Every module in this category is wrapped, **in the dispatch table itself**, by
`qualification_boundary.install`. After that call there is no entry in `registry.VALIDATED` for a
gated module that reaches its runner without the boundary first, and `registry.run_module` looks
the runner up there — **so a consumer cannot route around it by hand-building a signal package.**

The boundary reads the project's declared Category-9 assessment from `signal_inputs` under the key
**`evidenceQualification`**, and asks it for this category's declared use: **`requirement_conformance`**.

**Absence fails closed.** A package carrying no Category-9 assessment is UNASSESSED, and UNASSESSED
is ineligible. Nothing is inferred, nothing is imputed, and the consumer does not execute first and
get stamped afterwards. The refusals, in their exact words and in the order they are reached:

1. **No governed qualification requirement declared for the route** — a configuration failure:
   `"No governed qualification requirement is declared for this route, so it is not executed. An
   undeclared route is a configuration failure and is blocked rather than allowed through."`
2. **`evidenceQualification` absent** — the case a project with no declared assessment reaches:
   `"The evidence offered to this measure carries no Category-9 assessment, so it is unassessed and
   not eligible for this use. No reading is produced and no figure is used in its place."`
3. **Declared but not eligible for this use:** `"The evidence supplied for this measure has not been
   qualified for this use, so it is not read and no figure is produced in its place. "` followed by
   the qualification reasons, joined with `"; "`.

Every one of those carries the reason code `evidence_not_qualified_for_use` and is stamped
`QUALIFICATION_BOUNDARY_V18`, so a reader of the ledger can tell **a refusal by the gate** from **a
module's own abstention**.

**This is the abstention a project with no declared Category-9 assessment will actually see for
every module in this category, and it is reached before any input named below is looked at.** The
per-module abstentions specified further down are what the module says once the boundary has been
passed.


---

## A6.1 — Quality Compliance Index

**Identity.** Live id `A6.1`. Method class `Quality_Compliance`. The share of the applicable
quality requirements that were assessed and found satisfied.

**Required inputs, by their exact `signal_inputs` field names.**
*Governed path.* `qualityRequirementRegister` — a mapping carrying a `requirements` list, each row
with `requirement_id`, `applicable`, `assessed`, `satisfied`, `criticality`, `source`, `status`,
`corrective_action`, `period` and `provenance`.
*Corpus-assembled path*, used only when the governed structure is absent. `qualityAuditScore`,
`totalFindings`, `criticalFindings` — any one of them present triggers assembly. **The assembly
supplies no `requirements` list**; it carries these three onto the structure as
`recorded_audit_evidence`.

**Method.**
```
QualityComplianceRate = SatisfiedApplicableAssessed / ApplicableAssessed        (denominator > 0)
```
A requirement with `applicable is False` is skipped entirely. A requirement not `assessed` goes to
the **unassessed** list and enters **neither** the numerator nor the denominator. An assessed and
unsatisfied requirement of criticality `critical` or `high` is additionally returned in its own
**critical exceptions** list.

Governing rule: `FAR 46.2`, carried on the result as `rule`.

**Bands. RUN 101, THE OWNER'S ORDER, SECTION 3.5. NONE, UNLESS THE PROJECT SUPPLIES ONE.**

**The published rework benchmarks measure rework cost as a proportion of contract value. That is a
different quantity, with a different denominator — money, not requirements — and it must never be
applied to this rate.** Section 2 of the owner's order forbids substituting a threshold from a
related but different measure in exactly these words, and section 12.1 fails the run for it.

**The one thing that does band this module is an acceptance target the project's own documents
state** — a quality plan, an inspection and test plan, a specification or a contract saying, for
example, *"first-pass inspection acceptance shall be at least 95%"*. When the register carries one,
**that figure is the threshold and its source is the document**. Provenance class **CODIFIED**,
because the source is a governing instrument for this project.

| Band | Boundary |
|---|---|
| Green | conformance rate **at or above** the project's stated acceptance target |
| Red | below it |

**Two bands, because the document states one figure.** No intermediate ladder is drawn between
them: a stated target divides the range in two and nothing in the document says where a middle
would go.

**The target must be stated over this quantity.** `acceptance_target_quantity`, where the register
carries it, records what the document's target was stated over. A target stated over something else
is refused rather than applied, and the refusal reason is stored on the row.

**Fields the register must carry for a band to be asserted**, all three or none:
`acceptance_target` (a fraction between 0 exclusive and 1 inclusive), `acceptance_target_source`
(the document and clause), and optionally `acceptance_target_quantity`.

**A false premise in the order, corrected against the tree and recorded here.** Section 3.5 says
*"The module computes a first-pass inspection yield."* **It does not.** It computes
`SatisfiedApplicableAssessed / ApplicableAssessed` — a requirement conformance rate over a
requirement register. The two are different quantities, and this specification does not pretend
otherwise. The banding rule the order gives is applied to the quantity the module actually
computes, and a target stated for a first-pass inspection yield is **not** applied to it.

**Interpretation.** Unassessed requirements do not count as satisfied and do not shrink the
denominator either. A register with ninety unassessed requirements and ten satisfied ones is not
ninety per cent compliant and is not ten per cent compliant; **it is ten of ten with ninety
outstanding, and the reader needs both numbers.** Critical exceptions are **noncompensatory**: one
critical exception is returned in its own list and cannot disappear inside a 99 per cent aggregate.

**Nothing to report, and the not-estimable disposition.**
1. No governed register and no audit evidence to assemble: the structure-absent sentences, with
   `W` = *"a governed quality requirement register"*.
2. Evidence not qualified for `requirement_conformance`: the qualification sentence above.
3. **Structure present with `recorded_audit_evidence` and no `requirements`** — the corpus path —
   the module **computes** with `quality_compliance_rate: null` and
   `disposition: "NOT_ESTIMABLE"`, reason verbatim: `"the project's Quality Audit evidence is
   recorded below, but it establishes no applicable, assessed and satisfied requirement
   population, so no compliance rate is measurable and none is estimated"`. An audit score, a
   findings count and a critical-findings count are **summaries**, and section 13 forbids
   substituting a summary for a denominator.
4. A `requirements` key present but empty or unreadable: `"Awaiting a governed quality requirement
   register. No entries are recorded, so there is nothing to assess and no figure is produced in
   place of one."`

**One property a reader must be told.** `qualityDeficienciesNoted` is a meeting-minute **mention**
and is not read. A6.1's old prerequisite on it is gone: a project holding a real Quality Audit
Report is no longer refused because nobody mentioned deficiencies in the minutes.

---

## A6.2 — Safety Performance Index

**Identity.** Live id `A6.2`. Method class `Safety_Performance`. The OSHA recordable incidence rate,
and the leading indicators, reported as **two families that are never averaged**.

**Required inputs, by their exact `signal_inputs` field names.**
*Governed path.* `safetyPerformanceRecord` — a mapping with `recordable_cases`,
`employee_hours_worked`, `leading_indicators`, `severe_events`, `reporting_period`, `provenance`,
and optionally `document_stated_incident_rate`.
*Corpus-assembled path*, used when the governed structure is absent. `oshaRecordableIncidents` →
`recordable_cases`; `totalManhours` → `employee_hours_worked`; `oshaIncidentRate` →
`document_stated_incident_rate`; `reportPeriod` → `reporting_period`. Any one of the first three
present triggers assembly. A quantity the corpus does not carry does not appear on the structure.

**Method — lagging.** The OSHA identity exactly as supplied:
```
IncidenceRate = RecordableCases * 200000 / EmployeeHoursWorked
```
Governing rule: `OSHA incidence rate`, carried on the result as `rule`.

**Method — leading.** Governed proactive measures are reported as recorded, each with its
indicator, value, period and provenance. **There is no combined score.** Averaging the two families
without a governed combination policy is forbidden, none is supplied, and none is computed.

---

### RUN 101: THE REBUILD. ONE RECORDABLE RATE BECOMES THREE MEASURES.

The owner's Run 101 order, section 3.6: *"real practice uses accident frequency rate, accident
severity rate, and near-miss reporting, not a single recordable rate. Report the three separately.
Do not composite them — no standard supports a blended safety index."* Section 12.1d of that order
**fails the run for compositing them**, and `combined_index` stays `None` as it always has.

**Where one band must front the category, the rule is WORST-OF and the module says so on the row.**

**1. FREQUENCY RATE.** Recordable and lost-time cases per exposure hours, computed on the **OSHA
200,000-hour base** and also expressed on the **ILO 1,000,000-hour base**, since the two differ only
by a factor of five and the second is what international practice quotes. Both are published from
one measurement rather than computed twice, so they cannot drift.

**IT IS NOT BANDED, AND THE REASON IS A FINDING RATHER THAN AN OVERSIGHT.** The order requires the
band to be drawn against **the published construction industry average, stored as configured data
with its year and source, never a literal in code, because it is revised annually.** That entry
exists — `band_reference_data.json`, key `construction_industry_recordable_rate` — and it is
**`configured: false`**. **No industry average was supplied with the order, and the research report
the order names as its authority for every number was not present.** Supplying a figure here would
be inventing a threshold, which section 12.2 fails the run for. So the rate is computed, reported
on both bases, and asserts no band. **Supply value, unit, year and source together in that entry
and the frequency leg bands against them with no code change.**

**2. SEVERITY RATE.** Days lost per exposure hours, on both bases, **plus the mean days lost per
lost-time case** — the figure that says whether a severity rate is many small cases or one
catastrophic one.

**Two conventions are in force and both are applied**, as the order requires be stated here:
* the **OSHA cap of 180 days lost per case**;
* the **standard charge of 6,000 days** for a fatality or permanent total disability.

Both the raw and the charged day totals travel on the reading, and `cases_capped` reports how many
cases the cap acted on, so the cap is visible rather than silent.

**Days lost is not extracted from any document today.** The safety report must state, for each
lost-time case, **the days lost**, and separately **the count of fatalities or permanent total
disabilities**. Absent them the severity leg abstains with
`severity_disposition: "ABSTAIN_NO_DAYS_LOST_RECORDED"` and no substitute is used.

**No threshold for a severity rate was supplied, so none is applied and the leg asserts no band.**

**3. NEAR-MISS REPORTING. THE INTERPRETATION IS INVERTED, AND GETTING IT BACKWARDS IS A
RUN-FAILING ERROR** (order section 12.1c). **A HIGH reporting rate indicates a healthy reporting
culture. A LOW OR ZERO rate on an active project indicates under-reporting, not safety.** Nothing
in this module treats a low count as favourable.

No published expected near-miss rate exists for construction, so **no ladder is drawn over the raw
count**. The reported and closed counts and the closure proportion are computed and displayed. The
**one band** the order states in terms is asserted and no other:

| Band | Boundary |
|---|---|
| Amber | **zero** near-misses reported on a project with recorded exposure hours **above the floor** |

Provenance class **OWNER-CALIBRATED** — no published basis; the owner's stated threshold. **Zero is
a value here and is not treated as missing.** Above zero, reporting activity is displayed and no
band is drawn.

**4. THE EXPOSURE FLOOR.** Beneath roughly **200,000 employee hours** a rate swings entirely on
whether one event happened, so **nothing bands beneath it** and the module says so on the row rather
than publishing a rate a single incident dominates. The floor is configured data
(`safety_exposure_floor_hours`), not a literal in code, and 200,000 hours is also the OSHA
normalising base itself — beneath it a rate is an extrapolation from less than one base period.
Provenance class **OWNER-CALIBRATED**.

---

**Bands. See the three measures above.** The module asserts at most one band, from the near-miss
leg, and abstains on frequency and severity for the reasons recorded there.

**Interpretation.** The incidence rate is exposure-normalised: it says how many recordable cases
occurred per 200,000 employee hours, which is roughly one hundred full-time workers for a year. It
is comparable between projects of different size, and a raw case count is not. **Zero recordables
alone never produces a favourable system claim** — `system_claim` is always `None`; the rate is a
rate.

**Nothing to report, and the two lagging dispositions.**
1. No governed record and nothing to assemble: the structure-absent sentences, with `W` = *"a
   governed safety exposure and leading-indicator record"*.
2. Evidence not qualified for `safety_measurement`: the qualification sentence above.
3. Cases and hours not **both** recorded as numbers — the module still **computes**, with
   `incidence_rate: null`, `lagging_disposition: "ABSTAIN_NO_EXPOSURE_DATA"` and reason verbatim:
   `"recordable cases and employee hours worked are not both recorded, so no exposure-normalised
   rate is computed and no substitute is used"`. The leading branch still reports.
4. Hours recorded at or below zero: `incidence_rate: null`,
   `lagging_disposition: "INVALID_DENOMINATOR"`, reason verbatim: `"no employee hours worked are
   recorded for this period, so an exposure-normalised rate has no denominator"`. **Hours are
   never fabricated.**
5. No leading indicators: `leading_disposition: "ABSTAIN_NO_LEADING_EVIDENCE"`, with the lagging
   branch unaffected.

**One property a reader must be told, and it is the one that matters most here.** A rate **stated
by a document** is carried out as `document_stated_incident_rate` and is **never** used as the
measurement. Executing the upstream extraction branch proved a stated rate is emitted unchecked: a
document asserting 99.9 survived beside a recorded 3-cases-per-200,000-hours pair. A stated rate is
a document's claim; the identity above is a measurement. Both travel, under names that say which is
which. A **meeting-minute incident mention is never an incidence-rate numerator**;
`safetyIncidentsDiscussed` is not read.

---

## A6.3 — Environmental Compliance Rate

**Identity.** Live id `A6.3`. Method class `Environmental_Compliance`. The share of applicable
environmental permit requirements that were assessed and found satisfied.

**Required inputs, by their exact `signal_inputs` field names.**
*Governed path.* `environmentalRequirementRegister` — a mapping with `jurisdiction`,
`permitting_authority`, `site_id`, `permit_id`, `permit_version`, `operator_status`, `provenance`
and a `requirements` list.
*Corpus-assembled path*, used when the governed structure is absent. `environmentalComplianceRate`
and `environmentalViolations` — either present triggers assembly, and they are carried as
`recorded_environmental_evidence`. **The assembly deliberately supplies no jurisdiction, no
permitting authority and no permit id**, because the corpus carries none and inventing any one of
them would be inventing regulatory applicability.

**Method.**
```
EnvironmentalComplianceRate = SatisfiedApplicableAssessed / ApplicableAssessed
```
with the same skip-if-not-applicable, unassessed-counts-nowhere and noncompensatory-critical rules
as A6.1.

**Applicability comes first, and it is a rule, not a measurement.** The permitting authority is
**read from the evidence** and may be EPA, state, tribal, local or another authority. Only where it
is exactly `"EPA"` is the governing rule set to the EPA Construction General Permit 2022; otherwise
`rule` is `null` and the result carries the note *"the permitting authority for this site is not
EPA, so the EPA Construction General Permit is not the governing instrument here"*. **EPA
applicability is never assumed and the function has no branch that could hard-code it.**

---

### RUN 101: THE REBUILD. SEVERITY AND CONSEQUENCE, NOT A CLOSURE RATE.

The owner's Run 101 order, section 3.7: **any violation goes Red outright**, and severity and
consequence must be carried — stop-work orders, fines, and the rest. **No published closure-rate
benchmark exists**, so the satisfied-over-assessed rate above is **not** what bands. What **is**
codified is the **EPA Construction General Permit's corrective-action deadline** — generally before
the next storm event, **no later than seven calendar days from discovery** — and its inspection
frequency.

**THE CGP'S OWN DISTINCTION GOVERNS, and it is the whole ladder:** an **open-but-within-deadline**
corrective action is a **deficiency**; a **missed deadline** or an **unauthorised discharge** is a
**violation**.

**Bands.** Drawn over `environmental_findings`, worst-wins. Provenance class **CODIFIED**.

| Band | Boundary |
|---|---|
| **Red** | **any confirmed violation**: a stop-work or cease-and-desist order, an unauthorised discharge, a permit suspension or revocation, criminal exposure, a debarment trigger, or a **missed corrective-action deadline** |
| **Amber** | a notice of violation, an administrative order, or a monetary penalty issued |
| **Yellow** | an open corrective action **still within** its deadline, or a documentation deficiency |
| **Green** | in compliance, corrective actions **closed within** the deadline |

**Worst-wins, and it is not an average.** One Red finding is Red however many findings are closed,
because a violation does not average away.

**THE ORDERING IS DERIVED FROM STATUTORY CONSEQUENCE AND IS NOT PUBLISHED AS A TAXONOMY**, and this
specification records it as a derivation rather than claiming a published severity taxonomy exists.
A stop-work order, an unauthorised discharge, a permit suspension, criminal exposure, a debarment
trigger and a missed corrective-action deadline are each a consequence the statute attaches; a
notice of violation, an administrative order or a monetary penalty is an enforcement action short of
those; an open action still inside its deadline is neither.

**A finding whose severity is none of the recognised words falls into NO rung** and is reported
unranked rather than dropped to the nearest one — boundary rule 2 of the order's section 3.

**An empty findings list is not Green.** *"No findings are recorded"* is not the same statement as
*"in compliance, corrective actions closed within the deadline"*, and it is not read as one: the
module abstains and says so.

**THE EXTRACTION CONTRACT MUST GROW, AND IT HAS NOT YET.** The environmental document must state,
per finding: `finding_id`, `severity` (one of the recognised words below), `enforcement_consequence`,
`discovered_date`, `corrective_action_deadline`, `corrective_action_closed_date`. The recognised
severity words are, verbatim:
`stop_work`, `cease_and_desist`, `unauthorised_discharge` (or `unauthorized_discharge`),
`permit_suspension`, `permit_revocation`, `criminal_exposure`, `debarment_trigger`,
`missed_corrective_action_deadline`, `violation` → **Red**;
`notice_of_violation`, `administrative_order`, `monetary_penalty` → **Amber**;
`open_corrective_action_within_deadline`, `documentation_deficiency`, `deficiency` → **Yellow**.
**Until the extraction contract and its assembler carry `environmental_findings`, this module
computes and asserts no band**, with the reason stored on the row. That is the honest state and it
is reported as such.

**A fixture trap that survives this rebuild and is recorded rather than fixed.**
`environmental_report.compliance_rate` is validated as a **0–1 fraction** and a value of `100` is
**rejected outright, discarding the whole document**. That is unchanged by this rebuild and it still
loses A6.3 its evidence on any document stating a percentage.

---

**Interpretation.** The rate is meaningful only against a named permit issued by a named authority
in a named jurisdiction. Without those three, a compliance percentage is a number about nothing,
which is why the module refuses to form one rather than reporting the figure the document asserts.

**Nothing to report, and the two non-estimable dispositions.**
1. No governed register and nothing to assemble: the structure-absent sentences, with `W` = *"a
   governed environmental permit and requirement register"*.
2. Evidence not qualified for `environmental_conformance`: the qualification sentence above.
3. **Authority or jurisdiction not established** — the module **computes**, with
   `environmental_compliance_rate: null`, `disposition: "APPLICABILITY_NOT_ESTABLISHED"`, reason
   verbatim: `"the jurisdiction and permitting authority for this site are not established, so
   environmental conformance is not assessed"`. This is the disposition the corpus-assembled path
   always reaches.
4. Authority and jurisdiction established but no requirement list:
   `disposition: "NOT_ESTIMABLE"`, reason verbatim: `"no applicable environmental requirement
   register is recorded"`.

Where recorded evidence is carried, it travels with the note verbatim: *"a rate asserted by the
source document and a reported violations count; neither is an applicable/assessed/satisfied
requirement population, so neither is used as the environmental compliance rate"*.

---

## A6.4 — Contractor Performance Assessment Signal

**Identity.** Live id `A6.4`. Method class `Contractor_Performance`. The governed ingestion of an
official or internal contractor performance assessment.

**Required inputs.** `contractorAssessmentRecord` — a mapping, and the only input read. There is no
corpus-assembled path. It carries `source_system`, `assessment_id`, `contract_id`,
`assessment_period`, `status`, `factor_definitions_version`, `factor_ratings`, `narratives`,
`contractor_comments_state`, `agency_review_state`, `reviewer`, `data_origin` and `provenance`.

**Method — a decision rule, not a formula.**
```
is_official_cpars_record = (source_system == "CPARS") AND assessment_id is present
label = "CPARS past-performance record"                     when that holds
        "internal Contractor Performance Assessment Signal"  otherwise
```
**The label is derived, never supplied.** An internal assessment is labelled internal and **can
never carry the CPARS label**: labelling an internal project score as CPARS or as an official
past-performance rating is forbidden. Factor ratings are preserved row by row with their narrative
and critical flag, and the worst or critical factor is returned separately.

Governing rule: `FAR 42.15`, carried on the result as `rule`.

**Required inputs — RUN 101 CORRECTS "There is no corpus-assembled path."** There is one now.
`past_performance_report` is a **live document type** and `extraction_merge` has emitted its four
CPARS-shaped ratings — `overallRating`, `scheduleRating`, `costRating`, `qualityRating` — to signal
inputs all along, **where no module read them**. They were orphan fields. `models_cat89._assemble`
now builds a `contractorAssessmentRecord` from them. **No new document type was created and none
was needed.**

**The assembly never asserts CPARS.** `source_system` is passed through exactly as the document
stated it, so a document that did not say CPARS produces a correctly-labelled **internal**
assessment. The derivation rule above is untouched.

**Bands. RUN 101, THE OWNER'S ORDER, SECTION 3.8.** Provenance class **CODIFIED** — the five ratings
are defined in the CPARS guidance and referenced by **FAR Subpart 42.15**.

| CPARS rating | Band |
|---|---|
| Exceptional | **Green** |
| Very Good | **Green** |
| Satisfactory | **Yellow** |
| Marginal | **Amber** |
| Unsatisfactory | **Red** |

**COLLAPSING FIVE ORDINAL LEVELS INTO FOUR BANDS IS A DESIGN CHOICE, AND THIS SPECIFICATION RECORDS
IT AS ONE.** The five ratings are codified; the decision to join **Exceptional** and **Very Good**
into one band is not. They are the pair joined because both stand **above** the Satisfactory level
the guidance defines as meeting contract requirements. Nothing else was merged, and the stored
`band_boundary` says so wherever it is printed.

**Worst-of across the factors, never an average.** A marginal schedule rating is not cancelled by an
exceptional cost one. **No aggregate is computed** and `aggregate` stays `None`: inventing
contractor-assessment weights is forbidden and no governed aggregation policy is supplied. The band
is the worst factor's band, which is a selection rather than an aggregation.

**A rating that is neither one of the five words nor its number on the shipped five-point scale
falls into no band** and the module abstains naming what it saw — boundary rule 2. A rating arrives
as the word or as its number depending on which path assembled the record, and both resolve through
`extraction_merge.CPARS_RATING_SCALE` **inverted**, so that scale keeps one authority.

**Interpretation.** An official CPARS record is a rating an agency has made and stands behind. An
internal signal is the project's own opinion of its contractor. They look alike on a page and mean
entirely different things, which is why this module derives the label from the source system and
the assessment id rather than accepting one.

**Nothing to report.**
1. Structure absent or not a mapping: the structure-absent sentences, with `W` = *"a governed
   contractor assessment record"*.
2. Evidence not qualified for `official_assessment_ingestion`: the qualification sentence above.
3. No `factor_ratings` list, or an empty one — the module **computes**, with
   `disposition: "ABSTAIN_NO_GOVERNED_ASSESSMENT"` and reason verbatim: `"no governed official or
   internal contractor assessment with factor ratings is recorded, so no signal is produced"`.
   The derived label and `is_official_cpars_record` are still reported.

---

## Stopped specifications

None. All four modules in this category have unambiguous sources and are specified above.
