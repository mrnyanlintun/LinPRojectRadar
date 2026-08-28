# Category C1 — Data Integrity

Seven modules: C1.1 through C1.7. These are **evidence qualification measures**. They read how
complete, how fresh, how traceable and how internally consistent the project's own evidence is —
not how the project is performing.

**Three properties hold for every module in this category and none of them may be relaxed.**

1. **Metadata only. No band. No vote.** Every result carries `category_9_metadata_only: true` and
   `voting_eligible: false`, set by `models_cat89._route` for any module whose id begins `C1.`.
   `status_color` is `None` and `band_asserted` is `False`, re-asserted after the canonical result
   merges in. The registry's own note on all seven reads: *"authoring-time quality gate; not
   participant-facing; must not enter project status aggregation"*.
2. **They are not gated.** Unlike A6 and B3, all seven are constructed with `gated=False`, because
   **Category 9 IS the assessment** and putting it through its own qualification gate would be
   circular. There is therefore **no unqualified-evidence abstention** in this category.
3. **No denominator is ever invented.** Every one of these measures is a ratio, and in every case
   the denominator arrives on the supplied structure. Where it does not, the module abstains. A
   completeness figure with an invented denominator is not a measurement.

**No band may be attached to any module in this category.**

## The shared structure-absent sentences

From `canonical_v6.v6_structure`, writing `W` for the module's plain-words description:

- **Absent:** `"Awaiting W. This measure is named for a method that cannot be carried out without
  it, so no reading is reported and no other figure is used in its place."`
- **Present but not a mapping:** `"The information provided for this project in place of W is not
  in a form this measure can read, so no reading is taken from it."`

---

## C1.1 — Missing Data Index

**Identity.** Live id `C1.1`. Method class `Missing_Data_Index`. Field-level mandatory missingness,
**for one module or use**.

**Required inputs.** `requiredInputContract` — a mapping, and the only input read. It carries
`required_fields` (the denominator), `values`, `not_applicable_fields`, `invalid_fields`,
`critical_fields`, `contract_id` and `contract_version`.

**Method.**
```
applicable       = required_fields minus not_applicable_fields
missing          = applicable fields absent from values, or present with a null value
MissingFraction  = |missing| / |applicable|
critical_missing = missing INTERSECT critical_fields
invalid          = applicable fields declared invalid that are not also missing
```

**The four rules, each a branch in the source and not a comment:**
1. **Zero is a value and is never missing.**
2. **Null is missing.**
3. **Absent is missing.**
4. **Optional and not-applicable fields never enter the denominator.**

**Invalid mandatory fields are identified separately** and are **not** folded into the missing
count, because *present but unreadable* and *absent* are different findings.

**The denominator is the active governed contract's required fields, supplied on the structure.**
It is not this platform's opinion about which fields matter.

**Bands.** **None, and this module does not vote.** Calibration-pending, metadata only.

**Interpretation.** The fraction says how much of what a specific use requires is actually there.
**A tiny missing fraction cannot compensate for a missing critical field**: `critical_missing` is
returned alongside and is treated noncompensatorily.

**Abstention and the one non-measured disposition.**
1. Structure absent or not a mapping: the two sentences above, with `W` = *"the required-input
   contract for the module or use being assessed"*.
2. `required_fields` absent, not a list, or empty: `"Awaiting the required-input contract for the
   module or use being assessed. Without it there is no denominator, and a completeness figure
   with an invented denominator is not a measurement."`
3. Every required field recorded not applicable — the module **computes**, with
   `missing_fraction: null` and `disposition: "NO_APPLICABLE_REQUIREMENT"`, reason verbatim:
   `"every field in this use's required-input contract is recorded as not applicable, so there is
   no completeness question to answer"`.

---

## C1.2 — Data Timeliness Score

**Identity.** Live id `C1.2`. Method class `Data_Timeliness_Score`. The age of **one** record
against the freshness rule for **one** source class and use.

**Required inputs.** `evidenceTimelinessRecord` — a mapping, and the only input read. It carries
`evaluation_date`, `effective_date` (or `source_date` where the first is absent), an explicit
`date_field`, `source_class`, `use`, and `freshness_rule` — itself carrying `allowed_age_days`,
`boundary` and `version`.

**Method.**
```
Age = EvaluationDate - EffectiveOrSourceDate          (in days)
timely = Age <= allowed_age_days     when boundary == "inclusive"
         Age <  allowed_age_days     when boundary == "exclusive"
```
The status is one of exactly four values: `TIMELY`, `STALE`, `FUTURE_DATED`, or
`INSUFFICIENT_EVIDENCE`.

**Bands.** **None, and this module does not vote.** Calibration-pending, metadata only. The status
is a named state, not a colour, and must never be emitted as `band`.

**Interpretation.** A stale record is not a wrong record; it is a record that no longer speaks for
the period being assessed. The status names which of the four situations obtains and the age in
days is reported beside it.

**Abstention and the two non-measured statuses.**
1. Structure absent or not a mapping: the two sentences above, with `W` = *"a governed evidence
   date and freshness rule"*.
2. `freshness_rule` absent or not a mapping: `"Awaiting the governed freshness rule for this source
   class and use. No universal allowed age is supplied or invented, so no timeliness reading is
   taken."`
3. `allowed_age_days` not a number: `"The governed freshness rule records no allowed age, so there
   is nothing to compare this record's age against."`
4. `boundary` not exactly `"inclusive"` or `"exclusive"`: `"The governed freshness rule does not
   declare whether an age exactly equal to the allowed age is still timely, and that boundary is
   not chosen here."`
5. Either date absent or unreadable — the module **computes**, with `age_days: null`,
   `timeliness_status: "INSUFFICIENT_EVIDENCE"`, reason verbatim: `"a required date is absent or
   unreadable, so no age is computed"`.
6. Age below zero — `timeliness_status: "FUTURE_DATED"`, reason verbatim: `"the source date is
   later than the evaluation date"`.

**Two properties a reader must be told.** First, **the date field used is explicit.** "The date" on
a construction document is ambiguous, and choosing silently is how a stale record passes; the
structure names the field and the result reports it. Second, **the boundary rule is declared, never
defaulted.** Whether an age exactly equal to the allowed age is still timely is a governed choice,
and an absent boundary abstains rather than defaulting either way.

---

## C1.3 — Source Reliability Weighting

**Identity.** Live id `C1.3`. Method class `Source_Reliability_Weighting`. A transparent provenance
assessment — **and a number only if a governed rubric supplies one**.

**Required inputs.** `sourceProvenanceRecord` — a mapping, and the only input read. The eight
components assessed are `source_authority`, `verification_status`, `provenance_complete`,
`traceability`, `corroboration`, `extraction_confidence`, `superseded` and `conflicting_records`.
Optionally `rubric`, itself carrying `scores`, `version`, `basis`, `calibration_source`,
`effective_date` and `not_for_operational_weighting`.

**Method.** The eight components are reported as they stand, always. Then:
```
no rubric supplied      -> reliability_weight = None
rubric supplied         -> reliability_weight = sum over attributes of rubric.scores[attr][value]
                           for every attribute whose observed value appears in its score table
```
**This function chooses no score.** The rubric's own scores are applied and nothing else. Any
monotonicity in verification status is therefore a property of the **supplied** rubric, not of this
module.

**Bands.** **None, and this module does not vote.** Calibration-pending, metadata only.

**Interpretation.** With no governed rubric the weight is **`None` — not 1, not 0.5**. The
component evidence is still reported, and that is the point: a structural assessment of where the
evidence came from and whether anyone verified it remains useful without a fabricated scalar.

**Abstention and the one non-numeric disposition.**
1. Structure absent or not a mapping: the two sentences above, with `W` = *"a governed source
   provenance record"*.
2. A rubric supplied without a score mapping, a version or a basis — **abstain**: `"A reliability
   rubric was supplied without a score mapping, a version or a basis, so any weight computed from
   it would be undatable and unattributable."`
3. No rubric at all — the module **computes**, with `reliability_weight: null` and
   `disposition: "NO_GOVERNED_MAPPING"`, reason verbatim: `"no governed reliability rubric is
   established for this source, so no numeric reliability weight is asserted; the component
   evidence above is reported instead"`.

**One property a reader must be told.** **`bac` has no place here** and the weighting that once
used it is gone. What is assessed is the evidence's own characteristics, never the size of the
project it describes.

---

## C1.4 — Audit Trail Completeness

**Identity.** Live id `C1.4`. Method class `Audit_Trail_Completeness`. Whether the chain of record
behind a decision is actually complete.

**Required inputs.** `auditChainRecord` — a mapping, and the only input read. It carries
`audit_schema` (with `mandatory_critical`, `mandatory_noncritical` and `version`),
`not_applicable_elements`, `present_elements`, `links` and `chronology_valid`.

**Method.**
```
required   = mandatory_critical + mandatory_noncritical
applicable = required minus not_applicable_elements
ATC_d      = |applicable elements present| / |applicable|
audit_complete = (ATC == 1.0) AND no critical element missing
                 AND no broken link AND chronology_valid
```
A link is broken where its entry in `links` is falsy; `broken_links` is the sorted list of those
keys.

**Bands.** **None, and this module does not vote.** Calibration-pending, metadata only.
`audit_complete` is a boolean and is not a band.

**Interpretation.** Completeness here is **noncompensatory**: adding a hundred optional fields
cannot compensate for a missing mandatory one, because **optional elements never enter either side
of the ratio** — which is a structural fact about the function, not a promise in a docstring.
Optional elements that are present are reported separately in `optional_elements_present`.

The elements assessed are the real research and governance objects: the signal package, the
judgment ledger, the authority, the response, the override/defer/escalation record, the method
version, the evidence, and the event and timestamp linkage.

**Abstention.**
1. Structure absent or not a mapping: the two sentences above, with `W` = *"a governed audit chain
   record"*.
2. `audit_schema` absent or not a mapping: `"Awaiting the versioned audit schema that says which
   elements are mandatory, which are critical and which are optional. Without it, completeness has
   no definition."`
3. The schema declares no mandatory elements: `"The audit schema declares no mandatory elements, so
   every chain would be complete."`

**One property a reader must be told.** **`bac` is not assessed and is not assessable here.**

---

## C1.5 — Information Completeness Ratio

**Identity.** Live id `C1.5`. Method class `Information_Completeness_Ratio`. **Package-level**
coverage: whether the documents the assessment needs are there and usable.

**Required inputs.** `informationPackageRecord` — a mapping, and the only input read. It carries
`package_id`, `package_version` and a `components` list; each component carries `component_id` (or
`domain`), `applicable`, `required`, `present`, `critical`, `mandatory_fields` and `values`.

**Method.**
```
applicable      = components with applicable != False and required != False
present_usable  = applicable components that are present AND usable
usable          = NOT (the component has mandatory_fields and ALL of them are null)
InformationCompleteness = |present_usable| / |applicable|
```
A component that is absent goes to `missing_domains`; one that is present but unusable goes to
`unusable_components`. A critical component in either list also goes to
`missing_critical_domains`.

**Bands.** **None, and this module does not vote.** Calibration-pending, metadata only.

**Interpretation.** **"Usable" is the load-bearing word.** A component whose mandatory internal
fields are all missing is not usable merely because a filename exists. A package can be 100 per
cent present and materially incomplete, and this module is what makes that visible.

**Abstention and the one non-measured disposition.**
1. Structure absent or not a mapping: the two sentences above, with `W` = *"a governed information
   package definition"*.
2. `components` absent, empty or unreadable: `"Awaiting the applicable required information
   package. No entries are recorded, so there is nothing to assess and no figure is produced in
   place of one."`
3. No applicable required component — the module **computes**, with
   `information_completeness: null` and `disposition: "NO_APPLICABLE_COMPONENT"`.

**One property a reader must be told.** **This is not C1.1.** It reads a different key from a
different structure so the two cannot silently become the same measure: C1.1 measures fields inside
one use's contract, C1.5 measures whether the package's components are there at all. A project can
be field-complete on what it has and package-incomplete on what it is missing, and both readings
are needed.

---

## C1.6 — Cross-document Consistency Score

**Identity.** Live id `C1.6`. Method class `Cross_Doc_Consistency`. Whether the **same governed
fact** agrees across the actual source records that report it.

**Required inputs.** `crossDocumentFactSet` — a mapping, and the only input read. It carries a
`facts` list; each fact carries `fact_id`, `reference_source`, `normalization`, `tolerance` (with
`relative` and/or `absolute`), `tolerance_version`, and an `observations` list whose rows carry
`source_id`, `value`, `units`, `period`, `effective_date`, `revision` and `source_authority`.

**Method — comparability first, then agreement.** For each fact, every observation is compared
against the one whose `source_id` matches `reference_source`.
```
fewer than two observations                     -> NOT_COMPARABLE
no observation matches reference_source         -> NOT_COMPARABLE
different period or different units             -> NOT_COMPARABLE
numeric pair, no tolerance rule configured      -> NOT_COMPARABLE
numeric pair, tolerance states neither bound    -> NOT_COMPARABLE
numeric pair, relative bound and reference != 0 -> ok when |b-a| / |a| <= relative
numeric pair, absolute bound                    -> ok when |b-a| <= absolute
non-numeric pair                                -> ok when str(a) == str(b),
                                                   casefolded when normalization == "casefold"
ok      -> CONSISTENT
not ok  -> MATERIAL_CONFLICT
ConsistencyFraction = consistent / comparable
```

**Bands.** **None, and this module does not vote.** Calibration-pending, metadata only.

**Interpretation.** **The conflict is never averaged away.** A material conflict is returned as a
row naming both sources and both values; there is no reconciliation step, no mean and no "resolved"
value. Averaging 100 and 110 to 105 and declaring the conflict gone is forbidden, and there is no
arithmetic in the function that could do it.

**Comparability is checked before agreement.** Different reporting periods, different units or
different revision contexts are `NOT_COMPARABLE` — **not inconsistent**. Two documents describing
different months do not contradict one another.

**Abstention.**
1. Structure absent or not a mapping: the two sentences above, with `W` = *"a governed
   cross-document fact set"*.
2. `facts` absent, empty or unreadable: `"Awaiting a governed cross-document fact set. No entries
   are recorded, so there is nothing to assess and no figure is produced in place of one."`

**One property a reader must be told.** **Numeric tolerance arrives in the fact's own rule and no
universal tolerance is supplied or invented.** It is relative to the **governed reference source's**
value, not to the mean of the two. Where a fact carries no tolerance rule, its numeric comparison
is `NOT_COMPARABLE` and it is removed from the comparable count rather than being judged against a
guess.

---

## C1.7 — Reporting Frequency Index

**Identity.** Live id `C1.7`. Method class `Reporting_Frequency_Index`. Whether the recurring
reports actually arrived, and on time.

**Required inputs.** `reportingCadenceRecord` — a mapping, and the only input read. It carries
`expected_periods` (each with `period_id` and `due_date`), `report_history` (each with `period_id`
and `received_date`), `approved_extensions` (a mapping of period id to a revised due date),
`report_class`, `observation_window`, `cadence_version` and `cessation_status`.

**Method.**
```
ReportingCoverage   = UniqueValidExpectedPeriodsReceived / ExpectedPeriods
OnTimeReportingRate = ExpectedReportsReceivedWithinGovernedWindow / ExpectedReports
```
Per expected period, the status is exactly one of `MISSING` (no report matched),
`INSUFFICIENT_EVIDENCE` (a report matched but a date is unreadable), `ON_TIME`
(`received <= due`), or `LATE` (with `days_late` reported). Coverage counts the `ON_TIME` and
`LATE` periods.

**Bands.** **None, and this module does not vote.** Calibration-pending, metadata only.

**Interpretation.** Coverage says whether the reports exist; the on-time rate says whether they
arrived when they were owed. A project can have perfect coverage and a nil on-time rate, and the
two readings are kept separate so that condition is visible.

**Abstention.**
1. Structure absent or not a mapping: the two sentences above, with `W` = *"a governed reporting
   cadence record and report history"*.
2. `expected_periods` absent, empty or unreadable: `"Awaiting the governed reporting schedule. No
   entries are recorded, so there is nothing to assess and no figure is produced in place of one."`

**Two properties a reader must be told, and both are anti-gaming rules.** First, **duplicates
cannot inflate the numerator**: coverage counts unique expected periods matched, so a second report
for period 1 matches a period already matched and changes nothing; the count of ignored duplicates
is reported. Second, **an approved extension moves the governed due date** for that period and the
report is evaluated against the revised date, with `due_date_revised_by_approved_extension` set on
that row. **No grace window is invented**: a report is late if it arrives after its governed due
date, extension included.

**One property that distinguishes this from C1.2.** C1.2 asks whether **one record is fresh now**.
C1.7 asks whether a **recurring cadence** was kept, over a history. They are different questions and
read different structures.

---

## Stopped specifications

None. All seven modules in this category have unambiguous sources and are specified above.
