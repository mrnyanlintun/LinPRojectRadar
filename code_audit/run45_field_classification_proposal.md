# Run 45 §5.1 — the canonical field classification, PROPOSED

**Status: PROPOSAL. Nothing is implemented. No retrieval code was changed by this run.**
This document exists to be signed off or corrected by the owner before §5.2 begins.

Repository: the Linux clone at `/home/user/LinPRojectRadar`. Interpreter: the documented
`python3` fallback, 3.11.15 (no `.venv` on the clone). Branch: `run45-classification` from
`2c4171d`.

Naming authority, group naming, quoted verbatim (`NAMING_AUTHORITY.md:96-97`):

<!-- RUN 54, PHASE D: the sentence quoted below was SUPERSEDED by the owner on 2026-08-23.
     Displayed identifiers are acceptable. This is a historical audit document and is
     ANNOTATED rather than rewritten: it records what the authority said when the
     proposal was written, and rewriting it would falsify that record. -->
> **Never use a module id or number in user-facing text.** No "Cat 4", no "1.7", no "PH.2", no
> "A4.2". Groups and purposes only. The old "Cat N" scheme is retired along with the names.

Module identifiers appear throughout this document because it is an internal audit artifact,
not user-facing text.

---

## 1. How the kind was decided, and how it was NOT decided

The ruling (order §4) defines two kinds:

* **identity** — "They state a fact about the project that holds until superseded";
* **period** — "They state a fact about one reporting period".

**A kind is proposed only where a DECLARATION in the repository determines it.** The declaration
is quoted with file and line in every row. Three rules were applied without exception:

1. The kind never follows from what the implementation currently does. `_period_documents`
   (`server/app/documents.py:373`) scopes every field to its upload period today; that is the
   defect under repair and is evidence of nothing about any field's kind.
2. The kind never follows from what would make a module compute. Section 4's measurement is
   reported as a **consequence** of a proposal, never as a reason for one.
3. Where the declarations do not determine the kind — or where two declarations pull opposite
   ways — the field is listed in section 5 as **UNDETERMINED and nothing is proposed for it**
   (order §5.1 final paragraph; stop condition 9.1).

Two generic declarations recur and are quoted once here rather than in every row.

**D-SNAP** — `server/app/field_registry.py:11-12`:

> `* SNAPSHOT  — the latest revision within a period is that period's observation (register`
> `replace). Across periods, each period's selection is one point of a series.`

D-SNAP is a *within-period selection rule* plus a statement that the stored series has one
point per period. It is read here as supporting a **period** proposal where nothing more
specific contradicts it, and as **not** settling a field for which a more specific declaration
states persistence-until-amendment. Specific beats generic; where the specific declaration is
absent, D-SNAP alone is treated as sufficient only for fields whose group header also ties them
to a report of the period.

**D-PERM** — `server/app/field_registry.py:19`:

> `* PERMANENT — never superseded or replaced by anything later. The original baseline.`

D-PERM is the strongest identity declaration in the repository: a value that is *never*
superseded cannot be a fact about one reporting period.

---

## 2. What resolves through the defective path — the sweep

`_period_documents` is called at `server/app/documents.py:1001, 1215, 2240, 2282, 2747`. Every
one of those callers feeds `assemble_signal_inputs` / `select_signal_inputs`. **Therefore every
emittable field resolves through this path, not sixteen.** Measured from the registry itself:

```
len(FIELD_KINDS)  = 77   every field the emission layer can produce
len(WRITER_TIERS) = 16   the multi-writer subset Run 44 reported
```

The sixteen are not a distinct population; they are the fields where the fall-through is
*visible* because a lower-tier writer can stand in for an absent higher-tier one. The other
**61 single-writer fields fall through the same way** — silently, to absence. The classification
below therefore covers all 77.

---

## 3. The classification

Columns, per order §5.1: field | writers and declared precedence | proposed kind | the declared
meaning it rests on (quoted, with file:line) | supersession if identity.

### 3.1 The sixteen multi-writer fields

| # | field | writers, best first (`field_registry.py`) | proposed kind | declared meaning it rests on | supersession (identity only) |
|---|---|---|---|---|---|
| 1 | `bac` | `change_order` 0, `contract_value` 1, `schedule_of_values` 2, `pay_application` 3, `monthly_report` 4 — `field_registry.py:182-183` | **identity** | `field_registry.py:50` `# -- effective contract state: amendments layered on the baseline`; `field_registry.py:179-180` `# A change order is the authoritative amendment to the contract sum; the contract` / `# establishes it`; `extraction_merge.py:757` `# The executed amendment. Effective values win by declared tier` | The next document that AMENDS the contract sum, by declared tier then by `as_of`: an executed `change_order` (tier 0), else a later `contract_value`. A `pay_application`/`monthly_report` restatement is a tier-3/4 fallback and must not supersede a tier-0/1 figure from an earlier period. |
| 2 | `baselineContractSum` | `contract_value` 0, `change_order` 1 — `field_registry.py:187` | **identity** | D-PERM (`field_registry.py:19`); `field_registry.py:47` `# -- contract baseline: the original persists, whatever arrives later`; `field_registry.py:185` `# The ORIGINAL baseline: the contract's own figure beats a change order's account of it.`; `extraction_merge.py:554-555` `# THE BASELINE PRESERVATION. The contract's own sum is also the original baseline,` / `# PERMANENT: it survives every change order` | **Nothing supersedes the value.** The declaration is "never superseded or replaced by anything later". The only replacement is a document-level revision of the contract itself (`DocumentUpload.supersedes_document_id`, honoured by `_superseded_document_ids`). A change order's account of the original NEVER replaces the contract's own, in any period — this is the Run 44 inversion, and carrying the contract forward is what kills it. |
| 3 | `baselineEnd` | `change_order` 0, `contract_value` 1 — `field_registry.py:189` | **identity** | `field_registry.py:188` `# The effective completion date: the latest executed amendment, else the contract.`; `field_registry.py:52` `"baselineEnd": SNAPSHOT,  # original preserved as contract_value's observation` | A later executed `change_order`'s `revised_completion_date` (`extraction_merge.py:764-768`), else a later `contract_value`'s `project_end_date`. |
| 4 | `ev` | `schedule_of_values` 0, `pay_application` 1, `monthly_report` 2 — `field_registry.py:190` | **period** | `field_registry.py:56` `# -- EVM / progress snapshots`, with D-SNAP `field_registry.py:11-12`; order §4 names earned value as a period field | — |
| 5 | `ac` | `pay_application` 0, `monthly_report` 1 — `field_registry.py:192` | **period** | as `ev`: `field_registry.py:56` + D-SNAP; order §4 names actual cost as a period field | — |
| 6 | `pv` | `schedule_update` 0, `time_phased_schedule` 1, `monthly_report` 2 — `field_registry.py:191` | **period** | as `ev`: `field_registry.py:56` + D-SNAP | — |
| 7 | `actualPctComplete` | `pay_application` 0, `monthly_report` 1 — `field_registry.py:193` | **period** | `field_registry.py:56` + D-SNAP; the value's own source key is `percent_complete_verified` on a pay application, i.e. verified for that billing period (`extraction_merge.py:560`) | — |
| 8 | `plannedPctComplete` | `schedule_update` 0, `time_phased_schedule` 1, `monthly_report` 2 — `field_registry.py:194-195` | **period** | `field_registry.py:56` + D-SNAP | — |
| 9 | `submittalsTotal` | `submittal_register` 0, `rfa_log` 1 — `field_registry.py:200` | **period** | `field_registry.py:63` `# -- registers and logs: latest revision within the period is the observation` (the group containing line 67), with D-SNAP | — |
| 10 | `submittalsRejected` | `submittal_register` 0, `rfa_log` 1 — `field_registry.py:201` | **period** | as `submittalsTotal`: `field_registry.py:63` | — |
| 11 | `qualityDeficienciesNoted` | `field_report` 0, `inspection_report` 1 — `field_registry.py:198` | **period** | D-SNAP; `field_registry.py:196-197` `# Two different quantities share this slot (the A7 collision). The field report's own` / `# count keeps winning` — a count *noted in* a report of the period | — |
| 12 | `totalFloat` | `schedule_update` 0, `time_phased_schedule` 1 — `field_registry.py:203` | **UNDETERMINED** | see §5.1 | — |
| 13 | `consumedFloat` | `schedule_update` 0, `time_phased_schedule` 1 — `field_registry.py:204` | **UNDETERMINED** | see §5.1 | — |
| 14 | `activitiesPlanned` | `schedule_update` 0, `lookahead_schedule` 1 — `field_registry.py:205` | **period** | D-SNAP; the module input contract for the quantity, `simulation/models_ext.py:346-347`: *"v3 REQUIRES THE LOOK-AHEAD INVENTORY: the window, the status date, and one row per activity"* — a window opened from a status date is an artefact of one reporting moment | — |
| 15 | `activitiesConstrained` | `schedule_update` 0, `lookahead_schedule` 1 — `field_registry.py:206` | **period** | as `activitiesPlanned` | — |
| 16 | `lookaheadWeeks` | `schedule_update` 0, `lookahead_schedule` 1 — `field_registry.py:207` | **period** | as `activitiesPlanned`; the field IS the horizon of that period's look-ahead | — |

### 3.2 Further fields resolving through the same path — identity proposals

These are single-writer fields, outside Run 44's sixteen, that the sweep in §2 shows resolve
through `_period_documents` identically.

| field | writer | proposed kind | declared meaning it rests on | supersession |
|---|---|---|---|---|
| `baselineStart` | `contract_value` only (`extraction_merge.py:663-665`) | **identity** | D-PERM (`field_registry.py:19`) applied at `field_registry.py:48` `"baselineStart": PERMANENT`, under the header `field_registry.py:47` `# -- contract baseline: the original persists, whatever arrives later` | Nothing supersedes it; only a document-level revision of the contract itself. |
| `revisedContractSum` | `change_order` only (`extraction_merge.py:761`) | **identity** | `field_registry.py:50` `# -- effective contract state: amendments layered on the baseline` (the group containing line 53); `extraction_merge.py:757-758` `# The executed amendment. Effective values win by declared tier; the ORIGINAL` / `# baseline persists as contract_value's PERMANENT observations.` | The next executed `change_order`, by `change_order_date` (`extraction_merge.py:533`), never by upload order. |
| `analogousBac`, `analogousFinalCost`, `analogousOverrunPct` | `historical_data` only (`extraction_merge.py:625-629`) | **identity** | The document's declared subject is a *different, completed* project: `extraction_fields.py:266` `"analogous_overrun_pct", "analogous_project_type", "completion_year"` and the emission keys `similar_project_bac` / `similar_project_final_cost` (`extraction_merge.py:627-628`); and `extraction_merge.py:544-546` records that `historical_data` has **no as-of date** — `# historical_data's completion_year ("2019") is a year, not an as-of date`. A figure with no as-of date is not a point in this project's period series. | A later `historical_data` document restating the reference project. |
| `overallRating`, `scheduleRating`, `costRating`, `qualityRating` | `past_performance_report` only (`extraction_merge.py:620-624`) | **identity** | The declared subject is past performance, and `extraction_merge.py:544` declares the type carries **no as-of date**: `# contract_value, resource_report, past_performance_report, historical_data: no as-of` | A later `past_performance_report`. **Evidential weight is lower than the rows above**: the argument rests on the document's subject plus the absence of an as-of date, not on a persistence declaration. `resource_report` also carries no as-of date and is proposed *period* below, so "no as-of date" alone is not sufficient and is not used alone. Owner may reasonably move these four to UNDETERMINED. |

### 3.3 Further fields resolving through the same path — period proposals

Single-writer fields whose declaration ties them to a register, log, or report of the period.
Declaration: `field_registry.py:63` `# -- registers and logs: latest revision within the period
is the observation` for the register block, and `field_registry.py:71` `# -- everything else:
one writer, snapshot semantics` for the rest, both with D-SNAP (`field_registry.py:11-12`).
**No change of any kind is proposed for these** (order §5.2 item 2): today's retrieval is
already period-scoped, and Run 42's proof stands untouched for them.

Registers and logs (`field_registry.py:64-70`): `rfiCount`, `rfiPeriodDays`, `rfiOpen`,
`rfiOverdue`, `rfiAvgResponseDays`, `rfiOldestOpenDays`, `rfaTotal`, `rfaApproved`,
`rfaRejected`, `rfaResubmit`, `rfaOpen`, `rfaAvgReviewDays`, `ncrIssued`, `ncrClosed`,
`ncrOpen`.

Progress and period reports (`field_registry.py:57-62, 71-91`): `docRiskScore`,
`workPeriodFrom`, `workPeriodTo` (the pay application's own billing window,
`extraction_merge.py:666-668`), `weatherDaysLost`, `floatRemaining`, `oshaIncidentRate`,
`oshaRecordableIncidents`, `totalManhours`, `qualityAuditScore`, `totalFindings`,
`criticalFindings`, `environmentalComplianceRate`, `environmentalViolations`,
`subcontractorComplianceScore`, `longLeadItemsTotal`, `longLeadAtRisk`, `longLeadDelayed`,
`plannedLaborHours`, `actualLaborHours`, `indirectCostPlan`, `indirectCostActual`,
`materialCostBaseline`, `materialCostCurrent`, `subcontractorIssuesDiscussed`,
`outstandingActionItems`, `subcontractorDisputes`, `safetyIncidentsDiscussed`,
`safetyActionsOpen`, `environmentalIssuesDiscussed`, `qualityIssuesDiscussed`,
`weatherDaysDiscussed`, `itemsInspected`, `itemsFailed`, `criticalDeficiencyCount`.

`materialCostBaseline` is named "baseline" but is emitted by `cost_report`, a periodic report
(`extraction_merge.py:615-619`); no declaration states that it persists, so the generic
declaration governs. Flagged here so the naming is not mistaken for a persistence declaration.

---

## 4. What changes on a computed project, per identity proposal

**Method: measurement.** Not a static trace. Every claim in this section was produced by
executing the real `server/app/simulation/registry.run_all` over the modules in service, on a
full `signalInputs` package, and then again with one field moved to the shape a period has
today when the identity document was uploaded into an earlier period (`None`), and separately
with the field moved to a markedly different in-domain value. `cpi`/`spi` were re-derived in
each variant by `extraction_merge`'s own formula (`extraction_merge.py:967-980`) so a field's
effect through the derived indices is not lost. Same seed, scenario and period cutoff in every
run, so a difference is attributable to the field alone. Script:
`measure_fields.py` / `measure_all.py` in the run scratchpad (throwaway; no database, no
fixture mutation, nothing written into the repository).

Population executed: **62 modules**. `available_modules()` returns 62 of the 63 in service —
`A4.1` is in service but not available on this path. `service_index()` = 63 and the registry
total 101 are unchanged and were re-derived during this run.

| identity proposal | modules that would NEWLY receive the value in a period where it previously fell through | method |
|---|---|---|
| `bac` | **`A1.7`, `A1.8`** — and only those two. Both are the CORE_VOTING_MODULES, so the fall-through Run 44 measured (4,463,290 instead of 5,874,620) reaches the vote directly. | measurement |
| `baselineContractSum` | **none.** No module in service consumes its value. | measurement |
| `baselineEnd`, `baselineStart`, `revisedContractSum` | **none.** No module in service consumes their values. | measurement |
| `analogousBac`, `analogousFinalCost`, `analogousOverrunPct` | **none.** The modules named for reference-class forecasting abstain on a canonical-structure contract before reading these scalars. | measurement |
| `overallRating`, `scheduleRating`, `costRating`, `qualityRating` | **none.** | measurement |

**Read this carefully before signing off.** Of the identity proposals, **only `bac` changes any
computed module result today.** The rest change what is *shown and recorded* — the per-field
`sources` provenance, the signals surface, the evidence and completeness narrative — not any
band. That is not an argument against carrying them forward: their kind follows from their
declared meaning, and correcting a value that no module currently reads is still correcting it.
It is stated so the owner is not surprised when §5.3's census moves in exactly two modules.

The measurement was run over **all 77 emittable fields**, not only the ones proposed identity,
so "no module consumes it" is a measured result and not an untested assumption. Exactly 25 of
the 77 move any module row in either pass; every field proposed identity except `bac`, and every
field left UNDETERMINED except `originalContingency`/`remainingContingency`, is among the 52
that move nothing.

For completeness, the same measurement over the period-classified fields (whose retrieval does
NOT change) recorded: `ev` → `A1.5, A1.7, A1.8, B1.1, B1.2, B1.3, B1.4, B3.1`; `ac` → the same
plus `A1.9`; `pv` → `B1.3, B1.4`; `actualPctComplete` → `A3.2`; `submittalsTotal`,
`submittalsRejected` → `A4.3`; `originalContingency`, `remainingContingency` → `A3.2`. These are
recorded only as the control on the measurement — nothing is proposed to change for them.

---

## 5. UNDETERMINED — reported, not resolved

Order §5.1: *"If a field's declared meaning does not determine its kind, say so and propose
nothing for it."* Nothing is proposed for the following, and §5.2 must not touch them until the
owner rules.

### 5.1 `totalFloat`, `consumedFloat`

Two declarations pull opposite ways and neither is subordinate to the other.

* Toward **period**: `field_registry.py:56` places them under `# -- EVM / progress snapshots`,
  and D-SNAP makes each period's selection one point of a series.
* Toward **identity**: `field_registry.py:202` `# schedule_update revises what
  time_phased_schedule established.` "Revises what was established" is the grammar of a
  standing fact amended by a later document — the same grammar `baselineEnd` is classified
  identity on.

A total float figure is also genuinely both-natured: it is a property of the network as it
stood at a data date, and the network persists between updates. **The repository does not say
which**, and the module that would settle it does not read the fields at all
(`simulation/models_ext.py:189-198`: *"It read two reported scalars, totalFloat and
consumedFloat, neither of which any document in this corpus carries"*; v3 abstains without the
schedule network). Measured consequence either way: **no module in service consumes their
values**, so the ambiguity costs nothing to leave open.

### 5.2 `changeOrderCount`

Neither kind fits, and that is a defect in the two-kind taxonomy rather than in the field.

* It is declared `EVENT` (`field_registry.py:55`), and D-EVENT (`field_registry.py:13-14`) says
  *"dated records with identity; a revision supersedes THAT record, never the population."*
* An event population **accumulates**; it is neither "a fact holding until superseded" (order
  §4.1 — nothing supersedes the population) nor "a fact about one reporting period" (order
  §4.2 — the executed change orders of earlier periods have not stopped existing).
* The emission layer already carries both readings in one field:
  `extraction_merge.py:772-778` emits a stated ledger total as a `SNAPSHOT` observation and an
  unstated one as an `EVENT` row of `1`, and `NEEDS` (`field_registry.py:241`) declares it an
  `EVENT_SET` filtered to `executed`.

Retrieving it as "latest at or before the period" would be wrong for the counting form (it
would report one change order forever); retrieving it as a period field is wrong for the stated
form. **The correct retrieval for an EVENT field is a third rule — union of the event
population at or before the period, latest-per-entity — which order §4 does not define.**
Proposed to the owner as a decision, not resolved here. Measured consequence: no module in
service consumes its value, so leaving it exactly as today is safe.

### 5.3 `originalContingency`, `remainingContingency`

* Toward **identity** for `originalContingency`: the quantity is by name the *original* one, and
  the parallel case `baselineContractSum` is `PERMANENT` on exactly that reasoning.
* Toward **period**: `field_registry.py:56` groups both under `# -- EVM / progress snapshots`,
  they are emitted by `pay_application` alone (`extraction_merge.py:562-563`), and the module
  input contract states the requirement in period terms —
  `simulation/models_ext.py:538-540`: *"the original and remaining contingency amounts are
  needed, and at least one of them has not been reported **for this period**."*

The name is not a declaration. The two declarations that exist conflict. **UNDETERMINED.**
This one is *not* free: `A3.2` consumes both values (measured), so whichever way the owner rules
changes a computed result. It must be ruled on explicitly before §5.2, not carried by default.

---

## 6. What the owner is being asked to sign

1. **identity**: `bac`, `baselineContractSum`, `baselineEnd`, `baselineStart`,
   `revisedContractSum`, `analogousBac`, `analogousFinalCost`, `analogousOverrunPct`, and —
   with the lower evidential weight noted in §3.2 — `overallRating`, `scheduleRating`,
   `costRating`, `qualityRating`.
2. **period, retrieval unchanged**: the twelve period rows of §3.1 and every field of §3.3.
3. **UNDETERMINED, ruling required**: `totalFloat`, `consumedFloat`, `changeOrderCount`,
   `originalContingency`, `remainingContingency` (§5).
4. Confirmation that §5.2 may treat "further fields beyond the sixteen" as in scope — §2 shows
   all 77 emittable fields resolve through the same path, so a fix limited to sixteen would
   leave `baselineStart` and `revisedContractSum` still falling through.

**The run stops here. No retrieval code has been written.**
