# Category A6 — Delivery Quality Performance

Four modules: A6.1, A6.2, A6.3, A6.4. All four moved here from the former Category 8 Governance
because they describe **project performance**, not authority.

**All four are bandless.** Every one of them is routed through `models_cat89._route`, which sets
`status_color: None` and `band_asserted: False` on construction and **re-asserts `status_color =
None` after the canonical result is merged in**, so that no field arriving from the canonical
function can introduce a colour. The route's own comment on that line is *"no band is invented"*.
The Run-31 contract's section 53 forbids inventing a status threshold for any of them.

**No band may be attached to any module in this category.**

## The three ways a module here declines, and the exact words

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

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending.

**Interpretation.** Unassessed requirements do not count as satisfied and do not shrink the
denominator either. A register with ninety unassessed requirements and ten satisfied ones is not
ninety per cent compliant and is not ten per cent compliant; **it is ten of ten with ninety
outstanding, and the reader needs both numbers.** Critical exceptions are **noncompensatory**: one
critical exception is returned in its own list and cannot disappear inside a 99 per cent aggregate.

**Abstention and the not-estimable disposition.**
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

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending.

**Interpretation.** The incidence rate is exposure-normalised: it says how many recordable cases
occurred per 200,000 employee hours, which is roughly one hundred full-time workers for a year. It
is comparable between projects of different size, and a raw case count is not. **Zero recordables
alone never produces a favourable system claim** — `system_claim` is always `None`; the rate is a
rate.

**Abstention and the two lagging dispositions.**
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

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending.

**Interpretation.** The rate is meaningful only against a named permit issued by a named authority
in a named jurisdiction. Without those three, a compliance percentage is a number about nothing,
which is why the module refuses to form one rather than reporting the figure the document asserts.

**Abstention and the two non-estimable dispositions.**
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

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending.
**No aggregate is computed** unless a governed aggregation policy is supplied, because inventing
contractor-assessment weights is forbidden; `aggregate` is otherwise `None`.

**Interpretation.** An official CPARS record is a rating an agency has made and stands behind. An
internal signal is the project's own opinion of its contractor. They look alike on a page and mean
entirely different things, which is why this module derives the label from the source system and
the assessment id rather than accepting one.

**Abstention.**
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
