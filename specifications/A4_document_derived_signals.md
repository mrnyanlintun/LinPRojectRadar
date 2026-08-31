# Category A4 — Document-Derived Condition Signals

Ten module identifiers, A4.1 through A4.10. **Nine are specified below. A4.1 is stopped and is
not specified**; the reason is recorded at the end of this file under "Stopped specifications".

Every module here reads a register — of requests, of submittal decisions, of nonconformances, of
weather events, of changes, of claims, of subcontractor assessments, of procurement items, of
specification conflicts. None of them reads a performance index, and none of them reconstructs a
register from a score. That was the Run 27 finding and Run 29 removed the reconstructions rather
than qualifying them.

## How a module in this category answers

- **A reading with a band.** Only **A4.2 RFI Velocity** and **A4.3 Submittal Rejection Rate** can
  produce one. Both ladders are recorded in the source as **uncited**, and both modules are
  outside `registry.CORE_VOTING_MODULES`, so neither votes.
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

| Band | Velocity condition | Overdue-share condition |
|---|---|---|
| Green | `per_week <= 2` | `ratio < 0.10` |
| Yellow | `per_week <= 4` | `ratio < 0.20` |
| Amber | `per_week <= 8` | `ratio < 0.35` |
| Red | otherwise | otherwise |

The reported band is the **worse of the two** on the rank `Green < Yellow < Amber < Red`; the
overdue band is used only when it outranks the velocity band.

**Where these thresholds came from: nothing.** The source says so in those terms — Run 4 looked
for a source specifying two, four and eight requests per week, and for one specifying ten, twenty
and thirty-five per cent overdue, and found neither. The boundaries are left exactly as they
stand, uncited, and **this module does not vote**. This specification records them and does not
change them.

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

**Where these thresholds came from: nothing.** The source states it in those words — Run 4 looked
for a source specifying five, fifteen and twenty-five per cent for a submittal rejection share and
found none. The boundaries are unchanged and uncited, and **this module does not vote**.

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

**Bands.** **None. This module asserts no band and none may be attached.** It reports
calibration-pending with the standard note. The former ladder was drawn over a different quantity:
until Run 28 this module reported open nonconformances as a share of an audited findings cohort,
which is a backlog share, not a rate — the numerator a stock carried across periods, the
denominator the size of an audit. That quantity is gone and its ladder went with it.

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

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending
with the standard note.

**Interpretation.** The frequency says how often the scope is being changed; the magnitude says
how much of the contract those changes represent. A project with many small changes and one with
one enormous change are different conditions and this module reports them as two figures so they
stay different.

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

## A4.10 — Specification Conflict Density — RETIRED at Run 95, not in service. Its specification is archived verbatim at `specifications/archive/A4_document_derived_signals.md`; the identifier still resolves and is still listed by `registry.retired_modules()`.

## Stopped specifications

### A4.1 — Document Risk Score — RETIRED at Run 95, not in service. Its stopped-specification note is archived verbatim at `specifications/archive/A4_document_derived_signals.md`; the identifier still resolves and is still listed by `registry.retired_modules()`.

