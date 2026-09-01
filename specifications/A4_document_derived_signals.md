# Category A4 — Document-Derived Condition Signals

Ten module identifiers, A4.1 through A4.10. **Nine are specified below. A4.1 is stopped and is
not specified**; the reason is recorded at the end of this file under "Stopped specifications".

Every module here reads a register — of requests, of submittal decisions, of nonconformances, of
weather events, of changes, of claims, of subcontractor assessments, of procurement items, of
specification conflicts. None of them reads a performance index, and none of them reconstructs a
register from a score. That was the Run 27 finding and Run 29 removed the reconstructions rather
than qualifying them.

## How a module in this category answers

- **A reading with a band.** **A4.2 RFI Velocity**, **A4.3 Submittal Rejection Rate**, **A4.4 NCR
  Rate** and **A4.6 Change Order Frequency** produce one. *(RUN 106 EDIT: A4.3 and A4.4 band for
  the first time, on the owner's Run 106 boundaries — see their sections. A4.3 bands only on the
  governed submittal decision register; A4.4 only where the exposure unit is inspections or active
  work packages.)* *(RUN 102 EDIT, on the owner's authority in his Run 102 order section 5. This sentence
  read "Only A4.2 RFI Velocity and A4.3 Submittal Rejection Rate can produce one. Both ladders
  are recorded in the source as uncited, and both modules are outside
  `registry.CORE_VOTING_MODULES`, so neither votes." Run 101 rebuilt A4.2 and A4.6 in code and
  was forbidden from editing this specification, so it described modules that no longer behave
  that way. **A4.3 no longer bands at all**: Run 101 removed its five/fifteen/twenty-five per
  cent ladder because it was sourced to nothing, and it now bands only where a project's own
  submittal plan states an acceptance target. **A4.6 does band**, on change impact. Neither A4.2
  nor A4.6 is in `registry.CORE_VOTING_MODULES` and neither votes; that part was and is true.)*
- **A reading with no band — calibration pending.** Seven of the nine. The method runs, the
  figure is real, and no colour is claimed. The module carries the standard note verbatim:
  *"The method this measure is named for has been carried out and the figure is reported. No
  status colour is offered with it, because no boundary for this quantity has been established
  from evidence, and a colour drawn from an unestablished boundary would read as a judgement
  nobody has made."*
- **An abstention.** The defining structure is absent from `signal_inputs`, and the module names
  what it wants in the exact words below.

**No band may be attached to a module this file records as bandless.**

## The abstention sentence every structure-fed module in this category shares

Seven of the nine take their structure through `canonical_v4.require_v4_structure`, which raises
in one of exactly two forms. Writing `W` for the module's own plain-words description of its
structure, given per module below:

- **The structure is absent:**
  `"Awaiting W. This measure is named for a method that cannot be carried out without it, so no
  reading is reported and no other figure is used in its place."`
- **The structure is present but is not a mapping:**
  `"The information provided for this project in place of W is not in a form this measure can
  read, so no reading is taken from it."`

A third and fourth form fire on a structure that is present and readable but internally
defective, and both come from `canonical_v4` rather than from the module:
`"The W provided for this project carries a count that is not a whole number, so no reading is
taken from it."` and `"The W provided for this project is missing a description this method needs
to read it, so no reading is taken from it."`

---

## A4.2 — RFI Velocity

**Identity.** Live id `A4.2`. Method class `RFI_Velocity`. A project manager would call this the
rate at which the field is asking questions: how many requests for information are being raised
per unit of time, and how many of the open ones are overdue.

**Required inputs, by their exact `signal_inputs` field names.** This module has **two supply
paths and prefers the first.**

*Governed path (preferred).* `rfiEventLog` — a mapping. Used whenever it is present, because only
the events themselves can be de-duplicated: a cumulative register uploaded every month repeats
every earlier row, and a total extracted from the latest upload cannot tell a re-reported request
from a new one.

*Extracted-totals path.* Used only when `rfiEventLog` is absent.
`rfiCount` — the number of requests raised. If it is absent, `rfiNumber` is read in its place;
those are the only two names read for the count.
`rfiPeriodDays` — the number of days the request log covers. Required; **never defaulted to 30.**
`rfiOverdue` — optional. The number of open requests that are overdue.
`rfiOpen` — optional, carried on the result and used in no band.
`rfiAvgResponseDays`, or `rfiResponseTimeDays` when the first is absent — optional, reported in
the evidence sentence only.
`rfiOldestOpenDays` — optional, reported in the evidence sentence only.

**Method.**

Governed path:
```
rate_per_day    = de-duplicated RFI events / exposure days     (canonical_v4.rfi_velocity)
per_week        = rate_per_day * 7
overdue_ratio   = overdue / open_relevant, or null where not separately exposed
```

Extracted-totals path, computed exactly as the source computes it, with the JavaScript rounding
the port preserves:
```
per30     = js_round((rfiCount / rfiPeriodDays) * 300) / 10
per_week  = js_round((rfiCount / rfiPeriodDays) * 70)  / 10
overdue_ratio = rfiOverdue / rfiCount        (only when rfiOverdue is present and rfiCount > 0)
```

**Bands, and where each threshold came from.**

*(RUN 102 EDIT, on the owner's authority in his Run 102 order section 5. What stood here is
quoted in full in `REPORT_2026-09-01_run102.md`; it described a two-axis ladder banding on
requests per week and on an overdue share against three uncited cutoffs. **THE VELOCITY LADDER
IS GONE.** Run 101 removed it because nothing sourced two, four and eight requests per week, and
because a rate of questions is not a condition. What bands now is the OVERDUE PROPORTION alone.)*

| Band | Condition on the overdue proportion `rfiOverdue / rfiOpen` |
|---|---|
| Green | `ratio == 0` — nothing open is overdue |
| Yellow | `0 < ratio <= 0.10` |
| Amber | `0.10 < ratio <= 0.25` |
| Red | `ratio > 0.25`, **or** any overdue request where no open count is reported |

**Where these thresholds came from, and the two halves have different provenance.**

- **THE BASIS IS THE CONTRACT'S OWN RESPONSE PERIOD**, which is what makes a request *overdue* at
  all: a request unanswered beyond it is overdue by the contract's definition, not by an industry
  average. Where this project's uploaded contract states its period, that figure governs and the
  reading's `threshold_source` is `project_specific`. Where it does not, the platform's
  configured stand-in is **seven business days**, held in
  `simulation/band_reference_data.json` under `rfi_contract_response_period_business_days` with
  its source, and the reading's `threshold_source` is `owner_configured_default`. The
  provenance class of the basis is **CODIFIED**.
- **THE FOUR BOUNDARIES DRAWN FROM IT ARE NOT CONTRACTUAL** and have no published basis. They are
  the owner's stated thresholds, and the reading's `band_boundary_provenance_class` is
  **OWNER-CALIBRATED** so that a platform-chosen cutoff is never presented as though a standard
  fixed it.
- **OVERDUE MUST BE COUNTED IN BUSINESS DAYS, EXCLUDING WEEKENDS AND HOLIDAYS.** This platform
  performs **no date arithmetic on requests for information**: it takes the overdue count as the
  source document states it, so that requirement falls on the document's author and is stated in
  the extraction contract. A calendar-day count marks every request overdue two days early.
- **CORROBORATION RECORDED, NOT USED AS THE SOURCE.** Aboseif et al. (2023), *Journal of
  Management in Engineering*, gives a high-performing RFI processing time of seven days or fewer.
  That corroborates the period from an empirical direction; **the contract remains the source**.
  The same paper's requests-per-million-dollars figure measures a different quantity and is
  applied nowhere.

**Where no band is asserted.** Where the request log states no overdue count, the issue rate and
the open count are displayed and **no band is drawn from them**. Where nothing is open there is
no denominator, and that is reported rather than banded as though it were compliance.

**This module does not vote.** It is outside `registry.CORE_VOTING_MODULES`, unchanged.

**Interpretation.** A high velocity says the field is asking a lot of questions per unit of time,
which is evidence about the clarity of the issued documents rather than about cost. A high overdue
share says the questions are not being answered, which is the condition that turns into a claim.
The two are separate readings and the worse one is shown.

**Nothing to report.**
1. `rfiEventLog` present but unreadable: the two `require_v4_structure` sentences above, with
   `W` = *"a register of requests for information as events, each with its own identity and the
   dates it was raised and answered, and the span of time the register covers"*.
2. No `rfiEventLog`, and both `rfiCount` and `rfiNumber` absent: the default sentence
   `"Insufficient data: upload required documents"`.
3. `rfiPeriodDays` absent: `"Awaiting the number of days the request log covers: a rate of
   requests over time cannot be formed without the span of time it was measured over"`.
4. `rfiPeriodDays` not above zero, or the count below zero: `"Awaiting a request count and a log
   period that can form a rate: the figures read from the request log cannot both be right"`.
5. `rfiOverdue` present and either below zero or above the total: `"Awaiting an overdue count
   that lies within the total: the figures read from the request log cannot both be right"`.

**One property a reader must be told.** On the extracted-totals path, where `rfiPeriodDays` was
supplied by derivation rather than read from a document, the evidence sentence gains the suffix
`" (assumed 30-day period; upload RFI log for precise velocity)"`. The reading is still published
and still banded.

---

## A4.3 — Submittal Rejection Rate

**Identity.** Live id `A4.3`. Method class `Submittal_Rejection`. The share of submittal decisions
that were rejections.

**Required inputs, by their exact `signal_inputs` field names.** Three supply paths, in this
order of preference.

*Governed path.* `submittalDecisionRegister` — a mapping. Used whenever present, because only the
decisions themselves carry a disposition to be governed and a period to be filtered on.

*RFA path.* Used when `rfaTotal` and `rfaRejected` are both present and `rfaTotal > 0`.
`rfaTotal`, `rfaRejected`, and optionally `rfaResubmit`, `rfaOpen`, `rfaAvgReviewDays` — the last
three appear in the evidence sentence only and enter no band.

*Submittal-totals path.* `submittalsTotal` and `submittalsRejected`.

**Method.**
```
rate = rejected / total
```
On the extracted paths the source rounds as JavaScript does: `rate = js_round((rejected/total) *
1000) / 1000`. On the governed path the full-precision rate is banded and rounded to three places
for display.

**Bands, and where each threshold came from.**

| Band | Condition |
|---|---|
| Green | `rate <= 0.05` |
| Yellow | `rate <= 0.15` |
| Amber | `rate <= 0.25` |
| Red | otherwise |

**Bands — RUN 106. The owner supplied the boundary, and it is drawn over a NEW quantity.**

*The measure.* **First-review rejection rate** = submittals rejected or returned for revision **on
first review** ÷ submittals **receiving a first review**, as a percentage. **Later resubmittal
outcomes are not in the denominator.** This measures first-pass document quality, not eventual
cycles. `canonical_v4.submittal_rejection` now returns `first_review_rate`,
`first_review_rejected` and `first_review_assessed` beside the contract-4.3 `rejection_rate` over
all assessed decisions; the contract quantity is unchanged, still reported, and is **not** the
banded figure. The first review is the earliest decision for a submittal, by decision day and then
by revision identifier.

| Band | First-review rejection rate |
|---|---|
| Green | below 10% |
| Yellow | at or above 10%, below 20% |
| Amber | at or above 20%, below 35% |
| Red | at or above 35% |

Each boundary is inclusive on its lower side.

*Red regardless of rate*, where any holds: a rejected critical-path or long-lead submittal whose
forecast approval falls after its need-by date; a rejected submittal unresolved beyond the
project-defined review deadline and blocking planned work; two or more rejected resubmittals for a
critical work package.

*Basis.* `owner_configured_construction_document_control_tolerance`, **OWNER-CALIBRATED**,
`threshold_source = owner_configured_default`. Recorded in `band_reference_data.json` as
`submittal_first_review_rejection_bands`. **Informal sources reporting first-submission rejection
around 30 to 40 per cent are descriptive, not normative, and are not cited as the source.** A
stricter figure stated in a project document — a submittal plan's acceptance target — overrides
these under the threshold precedence order.

*Zero denominator.* Not Assessed. Never a division by zero, and never a raw count banded as if it
were a rate.

*The extracted-totals path does not band.* A rejected count and a register total with no revision
or decision-date structure cannot identify the first-review population, so the share formed from
them is a different quantity and the owner's boundary is not attached to it. The figure is
displayed and the reason is stated.

*Overrides that could not be evaluated are disclosed, not assumed away.* Where the record states
none of the three override fields, the row carries `band_overrides_evaluated: false` and names the
absent fields; a field the record does not carry is **not** read as false.

*This module still does not vote* — it is outside `registry.CORE_VOTING_MODULES` — but its band
now enters A4's category average.

**Distinct from A6.1 Quality Compliance.** That module measures first-pass **inspection**
acceptance and sits in Delivery Quality. This measures first-pass **submittal** quality in
Document-Derived Signals. A project can inspect well and submit badly. They are kept separate.

*(Superseded: "Where these thresholds came from: nothing." Run 4 looked for a source specifying
five, fifteen and twenty-five per cent and found none; Run 101 removed that ladder. The Run 106
boundaries above are the owner's own and carry his recorded basis.)*

**Interpretation.** A high rejection share says the packages arriving for review are not meeting
the specification on first presentation, which costs review cycles and float. It says nothing
about cost performance and must not be read as though it did.

**Nothing to report.**
1. `submittalDecisionRegister` present but unreadable: the two `require_v4_structure` sentences,
   with `W` = *"a submittal decision register: each submittal, each revision of it, and the
   decision recorded against it on the project's own disposition list"*.
2. Neither total nor rejected count available on any path:
   `"Insufficient data: upload required documents"`.
3. Total not above zero: `"Awaiting a submittal register with entries in it: a rejection share
   has no denominator without one"`.
4. Rejected below zero or above the total: `"Awaiting a rejected count that lies within the total:
   the figures read from the register cannot both be right"`.

---

## A4.4 — NCR Rate

**Identity.** Live id `A4.4`. Method class `NCR_Rate`. Nonconformances per unit of governed
exposure.

**Required inputs.** `ncrExposureRecord` — a mapping, and the only input read. There is no
extracted-totals path.

**Method.** `canonical_v4.ncr_rate` over the supplied record:
```
ncr_rate = NCR events / governed exposure quantity
```
where the exposure is inspections, inspected units, labour hours, work value or another explicit
denominator declared on the record. Four nonconformances over one hundred inspections reads 0.04.
Open count, age of open, severity and closure rate are tracked **separately** and are not folded
into the rate. **With no exposure, no normalised rate is fabricated.**

**Bands — RUN 106. The owner supplied the boundary, and it applies to TWO denominators and no
others.**

*The measure.* **NCR rate** = new NCRs opened in the period ÷ inspections performed in the period,
as a percentage. **Fallback denominator** where inspections cannot be reliably identified: active
work packages in the period.

| Band | NCR rate |
|---|---|
| Green | below 2% |
| Yellow | at or above 2%, below 5% |
| Amber | at or above 5%, below 10% |
| Red | at or above 10% |

Each boundary is inclusive on its lower side.

*Red regardless of rate*, where any holds: any open critical, life-safety, structural or
code-compliance NCR; any NCR on a hold point, failed commissioning test or required inspection
blocking turnover; three or more repeat NCRs for one root cause or trade in the period; any NCR
open beyond a documented contractual closure date. **A high inspection count must not dilute an
open critical NCR — the override takes precedence over the rate.** The severity counts the record
already carries are read as well as the dedicated override fields, so an open critical
nonconformance fires the override whether or not the dedicated field was stated.

*The ladder applies only where the exposure unit is `inspections` or `active_work_packages`.* A
nonconformance rate per labour hour, per unit of work value or per inspected item is a different
quantity and 2/5/10 per cent means nothing over it: those records report the figure with
calibration pending and the reason names the unit. The ladder is not widened to cover them.

*The denominator type and the reporting period are stored with every result*
(`denominator_type`, `denominator_type_words`, `reporting_period`). The denominator must be
consistent across periods — the two denominators are **not** mixed within one project's trend, and
a trend that silently switched denominator would be a fabricated trend. **Posture uses the current
period only; earlier periods are trend.**

*Zero denominator.* Not Assessed. `canonical_v4.ncr_rate` already refuses one; the runner states
the rule as well so no future supply path can reach a division by zero.

*Basis.* `owner_configured_construction_quality_control_tolerance`, **OWNER-CALIBRATED**,
`threshold_source = owner_configured_default`. Recorded in `band_reference_data.json` as
`ncr_rate_bands`.

**Distinct from A6.1 Quality Compliance**, which measures first-pass inspection acceptance in
Delivery Quality. A project can inspect well and still raise many nonconformances, or the reverse.
They are separate measures and are kept separate.

*(Superseded: "None. This module asserts no band and none may be attached." That was true until
Run 106. The former ladder — open nonconformances as a share of an audited findings cohort, a
backlog share and not a rate — is still gone and is not what the owner's boundaries are drawn
over.)*

**Interpretation.** The reading is how often nonconforming work is found per unit of the work that
was actually looked at. It rises when quality falls and it also rises when inspection improves, so
it is read against the exposure it names, never alone.

**Nothing to report.** The two `require_v4_structure` sentences, with `W` = *"a nonconformance record
with the exposure it is measured against: the nonconformances raised, and the inspections, hours
or value they arose from"*.

---

## A4.5 — Weather Day Impact

**Identity.** Live id `A4.5`. Method class `Weather_Impact`. The modelled schedule consequence of
verified weather events.

**Required inputs.** `weatherImpactEvents` — a mapping, and the only input read.

**Method.** `canonical_v4.weather_day_impact`. Weather occurrence is not schedule impact. The
method requires, per event: the event, the affected activity, the planned work, the time actually
lost, the governing allowance or calendar, the path and its float, causal evidence, and a modelled
consequence. It reports the **direct modelled path effect in days**, after the contract weather
allowance and after the float on each path, per path; the reported worst path is the one with the
greatest effect, ties broken by path identifier. A verified event costing two lost days on a
zero-float critical activity with no mitigation has a direct modelled path effect, before recovery
logic, of two days.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
with the standard note. Until Run 28 it divided lost days by a reported float figure and banded
the ratio; there was no activity, no path, no allowance and no causal evidence in it, and the
current quantity is not the one that ladder was drawn over.

**Interpretation.** The reading is the number of days of schedule the weather actually cost after
the contract's own allowance and the float that protected the work — not the number of bad days.
A project can lose ten weather days and carry a direct path effect of zero.

**Nothing to report.** The two `require_v4_structure` sentences, with `W` = *"a weather impact record:
the weather events, the activities they stopped, the time actually lost, the allowance in the
contract calendar, and the float on the path"*.

---

## A4.6 — Change Order Frequency

**Identity.** Live id `A4.6`. Method class `CO_Frequency`. Governed change events per unit of
exposure time, with magnitude reported separately.

**Required inputs.** `changeEventRegister` — a mapping, and the only input read.

**Method.** `canonical_v4.change_frequency`:
```
change_frequency_per_day     = governed change events / exposure days
change_frequency_per_30_days = change_frequency_per_day * 30
change_magnitude_net         = sum of change values / baseline contract value
```
Six changes over one hundred and eighty days reads 0.0333… a day, or one per standardised thirty
day period. **Frequency and magnitude are two quantities and are never combined into one unnamed
composite** — that combination is what the module did before Run 28 and it is what the supplied
contract forbids. Change type, cause, direction and contract lineage are retained on the reading.

**Bands.**

*(RUN 102 EDIT, on the owner's authority in his Run 102 order section 5. What stood here read:
"**None. This module asserts no band and none may be attached.** Calibration-pending with the
standard note." Run 101 rebuilt this module in code — it bands on change IMPACT — and was
forbidden from editing this file, so the specification described a module that no longer behaves
that way.)*

**WHAT IS BANDED IS CHANGE IMPACT, NOT FREQUENCY.** The frequency is still computed and is still
reported, and it is explicitly **not** what the band is drawn over: the count of changes over a
span of days says how often the scope moved, not what the movement did. Two halves band, and the
**worse of the two** is what the module asserts, with the other reported beside it.

**Cost impact — ADDITIONS as a proportion of the ORIGINAL contract value.** Additions and
omissions are measured separately and an omission is never adverse: a reduction is Green and is
never netted into the additions, because a scope reduction and a scope increase are different
conditions and cancelling one against the other hides both.

| Band | Condition |
|---|---|
| Green | net change at or below zero, **or** additions strictly under 5 per cent |
| Yellow | additions at or above 5 per cent and at or below 10 per cent |
| Amber | additions above 10 per cent and at or below 20 per cent |
| Red | additions above 20 per cent |

**Schedule impact — the days a change adds, and the float it consumes.** Reported and banded on
the same worse-of rule where the register states them.

**Where these thresholds came from.** The owner's stated authority, and the ladder's basis is a
**CONVENTION**: a contingency reserve is conventionally around twenty per cent of contract value,
held in `simulation/band_reference_data.json` under
`change_order_contingency_reserve_fraction`, so change exposure beyond it has passed the money set
aside to absorb it, and Amber begins at half the reserve. **No standards clause fixes 5, 10 or 20
per cent.** The reading's `threshold_source` is `owner_configured_default`. A project whose own
contract states a change-order tolerance overrides this, and the source is then that document.

**Interpretation.** The frequency says how often the scope is being changed; the impact says what
those changes did to the money and to the time. A project with many small changes and one with
one enormous change are different conditions and this module reports them as separate figures so
they stay different.

**Nothing to report.** The two `require_v4_structure` sentences, with `W` = *"a change event register
with the exposure it is measured over: each change, its type, cause and value, and the span of
time or contract value it arose against"*.

---

## A4.7 — Dispute Escalation Index

**Identity.** Live id `A4.7`. Method class `Dispute_Escalation`. How far the project's claims have
travelled up the project's own governed escalation process.

**Required inputs.** `claimDisputeRegister` — a mapping, and the only input read.

**Method.** `canonical_v4.dispute_escalation`. The register declares the project's own escalation
process, its stages in order, and the stage each issue has reached. The module reports the
**highest stage reached**, its **rank** among that process's stages, and
`escalation_position` = that rank as a position on the declared process. Stage names, stage count
and process version travel with the reading, because a rank of 3 means nothing without the process
it is a rank on.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
with the standard note. What it replaced was a generic composite — a capped request count at 0.3,
a capped change order count at 0.3 and a document risk score at 0.4 — none of which is dispute
evidence. **None of those three fields is read here.**

**Interpretation.** The reading names the furthest point a dispute on this project has reached on
the process the project itself declared. It is a position, not a score, and it is comparable only
against the same process.

**Nothing to report.** The two `require_v4_structure` sentences, with `W` = *"a claim and dispute
register: the project's own governed escalation process and the stage each issue has reached on
it, with the dates it reached them"*.

**One property a reader must be told.** Missing dispute evidence cannot improve this reading.
Run 7 removed the truthiness contribution that made an absent log and a log recording nothing
indistinguishable, precisely so a project could not improve its condition by withholding evidence.

---

## A4.8 — Subcontractor Performance

**Identity.** Live id `A4.8`. Method class `Subcontractor_Performance`. A traceable multi-criteria
assessment of the firms doing the work.

**Required inputs.** `subcontractorAssessments` — a mapping, and the only input read.

**Method.** `canonical_v4.subcontractor_performance`:
```
Score_firm = sum over criteria of ( w_i * r_i ),   with sum(w_i) = 1
```
Ratings of 0.80, 0.90 and 0.70 under equal weights score 0.80. Every weight must be versioned and
provenanced; `weights`, `weights_version`, the criteria list and the evaluator travel with the
reading. The module reports the **mean score across firms**, the **lowest score** and the firm it
belongs to, and any critical violations recorded.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
with the standard note.

**Interpretation.** The mean says how the supply chain is performing on the criteria the project
declared; the lowest score and the firm named against it are the actionable half, because the
project manages firms, not averages.

**Nothing to report.** The two `require_v4_structure` sentences, with `W` = *"a subcontractor performance
assessment: each firm, the criteria it was rated against, the rating on each, who assessed it and
the weights that were applied"*.

**One property a reader must be told.** In the browser this module could lazily derive a single
`subcontractorComplianceScore`. **That path is not ported and must not be reconstructed.** An
opaque precomputed compliance score with no criteria, no ratings, no evaluator and no weights
behind it is exactly what the supplied contract names as an invalid validation of this module. On
the server the assessment structure is supplied or the module abstains.

---

## A4.9 — Procurement Lead Time Monitor

**Identity.** Live id `A4.9`. Method class `Procurement_Lead_Time`. Item-level procurement slack.

**Required inputs.** `procurementItems` — a mapping, and the only input read.

**Method.** `canonical_v4.procurement_slack`, per item:
```
ProcurementSlack_item = RequiredOnSiteDate - ForecastDeliveryDate      (in days)
```
A required day of 100 against a forecast of 110 reads minus ten days. The module reports the
**minimum slack across all items** and the item it belongs to, the **mean slack**, and a count of
items in each state — `LATE`, `AT_RISK`, `ON_TIME`. **Every item is counted once**: delayed items
are not also counted inside at-risk.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
with the standard note. What it replaced was a weighted count ratio over the long-lead set — half
weight for at-risk items, full weight for delayed ones — which contains no date and therefore no
slack, and which the supplied contract states is not this method.

**Interpretation.** The tightest slack, and the item carrying it, is the procurement exposure the
project has to act on. A negative figure means that item is already forecast to arrive after the
work needs it.

**Nothing to report.** The two `require_v4_structure` sentences, with `W` = *"an item level procurement
register: for each item, the date it is required on site, the date it is forecast to arrive, and
the activity it feeds"*.

---


## Stopped specifications


