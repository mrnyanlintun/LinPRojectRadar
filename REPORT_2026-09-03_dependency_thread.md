# Run 123 — The Dependency Thread: from an uploaded document to a published project status

**Date:** 2026-09-03. **Kind:** read-only trace. **Only file committed:** this report.

## 0. Run identity and invariants

| Fact | Value |
|---|---|
| Starting commit | `65bedfbca838ca1b456318dda504cc89e5b14f6e` (`65bedfb`, "Run 122: the complete authoring contract, measured (read-only)") |
| `origin/main` at start | `65bedfb` — identical, tree clean |
| Migration head | `server/alembic/versions/0033_recognition_matches.py`. Nothing above it. UNCHANGED. |
| `SIMULATION_VERSION` | `"sim-2026.09-v64"` at `server/app/simulation/models.py:1001`. UNCHANGED; `SIMULATION_VERSION_HISTORY` (models.py:1011) not appended to. |
| Model key | **NONE.** `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY` all absent. No model call made, none simulated. |
| `git status --porcelain` before commit | `?? REPORT_2026-09-03_dependency_thread.md` — the report only |
| Ending commit | recorded in the commit message of this file; see section 9 |
| Files edited | none. `T6_HANDOFF.md` NOT touched. |

**Environment actually used:** Linux container, `/usr/local/bin/python`, cwd `/home/user/LinPRojectRadar/server`.
There is no `.venv` here; the order's `.venv\Scripts\python.exe` is the owner's Windows path. No
`DATABASE_URL` was needed: every execution in this run was in-process against the pure simulation
layer, and production Postgres was never contacted.

### 0.1 Corrections to the briefing I was given

The briefing was accurate on every checkable point (commit, version, migration head, 31 modules,
16 `_ASSEMBLER_FIELDS` entries, no key, `risk_register.py:271-280` DOCX gate, file sizes). Two
statements *inside* the briefing's narrative, quoted from Run 89, are **stale against the code**:

1. **The weight profile is not Run 89's.** The briefing quotes "A1 .25, A2 .25, A3 .15, A4 .10,
   A6 .15, A5 .10" and "six category postures". The code
   (`server/app/simulation/project_posture.py:62-69`) holds **five** categories at
   **A1 0.28, A2 0.28, A3 0.17, A4 0.11, A6 0.16**, asserted to sum to 1.0 at line 71.
   **There is no A5 in the profile and no A5 module in service.** Run 106 replaced Run 89's
   figures. Where the report and the code disagree, the code wins.
2. **"Indeterminate" is no longer published.** Run 106 replaced it with `"Awaiting analysis"`
   (`compute.py:60`). Rows stored earlier keep the old word; nothing rewrites them.

---

## Section 1 — The entry point

### 1.1 The route and its server-side limits

The route is **`a_projectupload`**, `server/app/documents.py:4143`. It is an action-dispatch
handler (`a_` prefix), not a decorated FastAPI path; `app/main.py` dispatches to it by action name.

Guards, in the order they execute:

| Line | Guard | Refusal |
|---|---|---|
| 4150 | `resolve_caller(session, payload, secret)` | not authenticated |
| 4153 | `require_member(..., "projectupload")` | not a member of the project |
| 4156 | `_refuse_unless_pm(...)` (`documents.py:132`) | **only the project's PM may upload** |
| 4160 | `_resolve_period(session, project, payload)` (`documents.py:161`) | unresolvable period |
| 4189 | `payload["documents"]` must be a non-empty `list` | `"documents must be a non-empty list"` |
| 4194 | each entry must be a `dict` | `"each document must be an object"` |
| 4195 → `_decode` (`documents.py:195`) | see below | |

`_decode` enforces the **only size limits on this path**, both constants at `documents.py:109-110`:

* `MAX_BASE64_CHARS = 5_000_000` — refusal text: *"File too large. The maximum is about 3 MB, so please compress the PDF."*
* `MAX_FILE_BYTES = 20 * 1024 * 1024` — refusal text: *"File too large. The maximum is 20 MB"*
* `dataBase64` absent → `"dataBase64 is required for each document"`
* not valid base64 (`validate=True`) → `"dataBase64 is not valid base64"`
* decodes to zero bytes → `"decoded file is empty"`

**There is no limit on the NUMBER of documents in one batch** and no total-batch-byte limit. The
two size checks are per-file only. That is a real gap and is named here rather than glossed.

Request shape per entry (accepted key aliases, `documents.py:4197-4216`):
`dataBase64`|`data_base64`; `filename`|`name`; `mimeType`|`mime_type`; `docType`|`doc_type`;
`supersedes`|`supersedes_document_id`. Top level also accepts `period_end`|`periodEnd`.

A **supersedes** claim is validated *before any extraction* (4223-4243): the referenced
`document_id` must already exist **in this project and this period**, else
`"cannot supersede {claim}: this project has no such document in period {period}…"`; and a
document may not supersede itself.

### 1.2 What is written to the database, and when

Three tables are written in `a_projectupload` itself, plus four projection stores at the end.

**`documents`** (model `Document`), `documents.py:4326-4362` for extracted rows and
`documents.py:4370-4383` for reference rows. Keyed by `sha256` (content-addressed; two PMs
uploading identical bytes share one row).

* Analytical row columns populated: `sha256`, `filename`, `mime_type`, `size_bytes`, `content`,
  `doc_type`, `extraction`, `extraction_model`, `extraction_provider`, `extraction_contract`,
  `classification_confidence`, `first_uploaded_by`.
* **Reference row** (a spec/code/standard, decided by `reference_kind(filename)` at 4213):
  `doc_type`, `extraction`, `extraction_model`, `extraction_provider`,
  `classification_confidence` are **all NULL** — nothing read the file. `is_mapped(None)` is
  false, so it can never reach the analytical inputs.
* A **stale** row (0030: `extraction_contract` NULL or unequal to the current
  `extraction_contract_fingerprint(doc_type)`) is **refreshed in place** at 4310-4318 —
  `doc_type`, `extraction`, `extraction_model`, `extraction_provider`,
  `classification_confidence`, `extraction_contract`, `extracted_at`. `filename` is not restamped.

**`document_uploads`** (model `DocumentUpload`), `documents.py:4424-4432`: `project_id`, `period`,
`document_id`, `uploaded_by`, `was_cached`, `supersedes_document_id`, `folder_path`,
`filing_class`, `needs_filing_review`, `period_end`. `folder_path`/`filing_class`/
`needs_filing_review` come from `_decide_filing(doc_type, extraction, filename, confidence)`
(`documents.py:564`).

**`upload_attempts`** (model `UploadAttempt`), `documents.py:4486-4497`: one row per file
regardless of outcome — `project_id, period, batch_id, filename, sha256, size_bytes, status,
doc_type, error, attempted_by`. Written because a failed extraction leaves no row anywhere else.
A failure with no reason is stored as *"the extractor reported no reason for this failure"*.

Then, at `documents.py:4508-4520`, four **projection stores** are written at upload time so the
store is current before any compute:
`_persist_observations` (documents.py:593), `_persist_schedule_activities` (867),
`_persist_project_risks` (803), `_persist_project_notices` (715).

### 1.3 Does extraction run here, and what decides that

**Extraction runs HERE, synchronously, inside the upload call.** `documents.py:4287`:
`results = extract_many(extractor, jobs) if jobs else []`, with elapsed time measured at
4286-4288. `extract_many` (`extraction_client.py:988`) runs jobs concurrently at
`DEFAULT_CONCURRENCY` and captures failures **per job** so one unreadable document does not
discard the other twenty-six.

Three tests decide whether a file becomes a job (`documents.py:4272-4285`):

1. `d["reference"] is not None` → **skipped entirely.** `reference_kind()` decides from the
   filename alone, before any byte is read. A specification is never sent to the model.
2. `d["sha256"] in queued` → skipped: one extraction per distinct hash per batch.
3. An existing row whose `extraction_contract == extraction_contract_fingerprint(held.doc_type)`
   → **cache hit, skipped.** Unequal or NULL → added to `stale`, re-extracted, row updated in place.

So the cache has two keys: **the bytes and the extraction contract**.

### 1.4 What happens with no model key

`build_extractor()` — `extraction_client.py:955-982`:

```
cfg = ai_provider.load_provider("extraction")
if cfg.key_present():  return ProviderExtractor(...)
if require_real:       raise ExtractionError(...)
return StubExtractor(recorded or {}, delay_s=delay_s)
```

**The class that serves the substitute is `StubExtractor`, `server/app/extraction_client.py:896`.**

* **It keys on the sha256 of the document bytes.** `extract_with_confidence`
  (extraction_client.py:927-949) computes `hashlib.sha256(raw).hexdigest()` and looks the hash up
  in `self._recorded`.
* **An unknown hash RAISES rather than inventing an extraction** (line 941-945):
  *"stub extractor has no recording for sha256 {sha[:12]}…; refusing to invent an extraction.
  Record it, or run against the real model."* That exception becomes a per-file
  `{ok: False, error}` and the document is stored nowhere.
* Its identity fields are honest: `model_id = "stub/recorded-v1"`, `provider = "stub"`
  (lines 906-908) — *"Not a provider name: the honest statement that no provider was asked."*
  Those two strings are what land in `documents.extraction_model` / `extraction_provider`.
* A recording without a third element yields `confidence = None`, which `needs_review` treats as
  reviewable.
* `build_extractor(require_real=True)` — which production passes — turns the missing key into a
  loud failure naming the provider and the empty variable, instead of silently filling the
  research record with stub output.
* `app/ai_provider.py` never returns a key value and never falls back to a second provider.

**In this container `StubExtractor` is what would serve.** No model call was made and none was
simulated in this run.

---

## Section 2 — Extraction to stored fields

### 2.A Worked example one: `items_passing_first_inspection`

**1. Where declared, and in which collection.**
`server/app/extraction_fields.py:92` — in `ALL_FIELDS` (the tuple opened at line 77), beside
`critical_quality_failures_json`. It is attached to a document type at
`extraction_fields.py:509`, inside `_EXTRACTION_FIELDS["inspection_report"]` (the dict opened at
line 251). The comment there is explicit that `items_passed` is *not* reused for it: an item that
failed and passed on re-inspection is in `items_passed` and is not a first-pass pass.

**2. What the model is asked to return.** `extraction_client.py:390-405`, the `first_pass_hint`
block inside `build_prompt` (extraction_client.py:184), emitted only
`if "items_passing_first_inspection" in fields`. Quoted:

> " items_passing_first_inspection, if requested, is the number of inspected items that were
> ACCEPTED ON THE FIRST INSPECTION, before any rework or re-inspection. It is NOT the same as
> items_passed: an item that failed and later passed on re-inspection counts in items_passed and
> does NOT count here. Return it only where the document itself distinguishes first-pass
> acceptance -- for example a 'first time right', 'first-pass yield', 'accepted on first
> inspection' or 'passed without rework' figure -- and return null where the document states only
> a total passed count. Do not compute it by subtracting rework, and do not copy items_passed
> into it."

**3. Validation / coercion.** In `extract_many`'s `run(job)` (`extraction_client.py:1003-1050`),
before any `Document` row exists:

* `validate_doc_risk_score(...)` — `extraction_merge.py:249`.
* `validate_numeric_fields(doc_type, extraction, ...)` — `extraction_merge.py:512`. A value that
  is **readable but out of contract** (negative count, 10 000 % complete) raises
  `NumericRangeError`/`MalformedNumericError` and **refuses the whole document** — nothing is
  half-stored. A value that **cannot be read at all** (Run 80 fix two) does *not* refuse: it is
  returned in the result's `unreadable` list, surfaces to the PM as
  `files[].unreadable_fields` (`documents.py:4468-4471`), and is absent from the emission because
  `_coerce_numeric` (`extraction_merge.py:436`) yields `None` for it.

**4. Merge across documents in the same period.** `items_passing_first_inspection` **is not
merged as a signal input at all** — see point 5. Its merge happens at the *structure* level, in
`_run69_structures` (`documents.py:1897-1938`), and the precedence rule there is
**longest-register-wins** (documents.py:1923-1935): between two quality documents in one period,
the one with more `requirements` rows takes `qualityRequirementRegister`; a document carrying
first-pass figures and **no** register does not displace one that carries a register — it *adds*
its figures to whatever was assembled (`if _has_first_pass and existing.get("items_inspected") is
None`). First-pass figures are therefore **first-writer-wins**, and the winner is whichever
document the `documents` iteration reaches first with both figures present.

**5. The exact key it is stored under, and in what form.**

* **NOT a signal input.** `_NUMERIC_EMISSIONS["inspection_report"]`
  (`extraction_merge.py:761-767`) emits only `items_inspected → itemsInspected`,
  `items_failed → itemsFailed`, `deficiency_count → qualityDeficienciesNoted`,
  `critical_deficiency_count → criticalDeficiencyCount`. `items_passing_first_inspection` is
  absent from that table and absent from `_KEY_ORDER` (`extraction_merge.py:121-166`), so
  `select_signal_inputs` never produces a key for it.
* **Stored as a STRUCTURE only**, under `signalInputs["qualityRequirementRegister"]
  ["items_passing_first_inspection"]` (documents.py:1936-1937), beside `items_inspected` and
  `critical_quality_failures`.
* It is read by `canonical_v6.py:948` (`structure.get("items_passing_first_inspection")`) into
  the A6.1 first-pass acceptance rate, and echoed in a sentence at `models_cat89.py:1467`.

### 2.B Worked example two: `procurement_items_json` (a JSON structure)

**1. Declared** at `extraction_fields.py:679`, in `_EXTRACTION_FIELDS["procurement_log"]`,
alongside `procurement_day_basis`. Also declared in `information_completeness._ASSEMBLER_FIELDS
["procurement_log"]` (`information_completeness.py:75`).

**2. Shape instruction**, `extraction_client.py:462-473`, `procurement_items_hint`, emitted only
`if "procurement_items_json" in fields`:

> " procurement_items_json, if requested and the log contains an ITEM-LEVEL procurement table
> (one row per monitored item, with the date it is required on site and the date it is forecast
> to be delivered), is a JSON array with one object per PRINTED ROW of that table, using the
> table's own column headings as keys and its values as printed; return every row the document
> prints and no others. Do not add an item the document does not list, do not compute a slack, a
> lateness or a state -- the platform computes those from the two dates -- and do not decide for
> yourself whether an item is long lead or sits on controlling or near-critical work: return the
> criticality word and the long-lead cell the register prints, and omit them where it prints
> neither. procurement_day_basis is the register's own word for which kind of day its dates are
> counted in, one of approved_calendar_working_days or calendar_days; return null where it states
> neither."

**3. Validation / coercion.** It is a JSON array, not a numeric field, so `validate_numeric_fields`
does not bound it. Coercion happens in the assembler, `documents.py:2402-2459`:
`_json_rows(ex.get("procurement_items_json"))` (`documents.py:375`) turns it into rows; each row
is read through `_first_of(row, keys)` (`documents.py:413`), which tries a list of synonym column
headings. **A row missing ANY of the seven mandatory cells is silently dropped**
(`documents.py:2419-2420`: `if None in (_iid, _req, _fc, _flt, _crit, _stat, _act): continue`).
The mandatory seven are item id, required-on-site day, forecast delivery day, available float
days, criticality, procurement status, schedule activity id. Four optional cells
(`forecast_uncertainty_days`, `long_lead`, `protection_date_missed`,
`causes_required_milestone_late`) are **omitted from the row entirely** when the register did not
print them — which is what lets A4.9 report its override as NOT TESTED rather than as not holding.

**4. Merge and precedence.** `documents.py:2457-2459`:
```
_prev = out.get("procurementItems")
if _prev is None or len(_pitems) > len(_prev.get("items") or []):
    out["procurementItems"] = _prec
```
**Longest-register-wins, and the losing register is discarded whole** — the assignment replaces
the whole dict; no row-level merge occurs.

**5. The key.** Stored as a **structure only**, `signalInputs["procurementItems"]` =
`{"source", "items": [...], "assembled_by", "source_document_type", optional "day_basis"}`.
No signal-input scalar is produced from it. `procurement_day_basis` rides on the same structure as
`day_basis` and is likewise never a signal input.

### 2.C The general precedence rule for signal inputs

For fields that *do* become signal inputs, the rule is in `extraction_merge.select_signal_inputs`
(`extraction_merge.py:1111`), which groups observations per field and picks with one of two
functions, chosen by the field's declared **kind** in `app/field_registry.py`:

* `_snap_pick` (`extraction_merge.py:1048`) — SNAPSHOT: **lowest writer tier wins; within it,
  dated beats undated; latest `as_of` wins**; remaining ties by `(rank, doc_type, sha256)`.
* `_perm_pick` (`extraction_merge.py:1059`) — PERMANENT: lowest tier, then the **EARLIEST** dated
  observation, and **nothing later ever replaces it**.

`_DOC_TYPE_RANK` (`extraction_merge.py:645`): `contract_value`, `schedule_of_values`,
`time_phased_schedule` = 0 (`_RANK_BASELINE`); `change_order`, `schedule_update` = 2
(`_RANK_REVISION`); everything else = 1.
Field kinds are SNAPSHOT / EVENT / DELTA / PERMANENT (`field_registry.py:33-38`);
`baselineStart` and `baselineContractSum` are PERMANENT (`field_registry.py:84-85`).

---

## Section 3 — Stored fields to assembled structures

Three assembler functions exist in `documents.py`, plus one record-builder helper.

| # | Assembler | Location |
|---|---|---|
| 1 | `_baseline_structures(session, project, period, documents, si)` | `documents.py:1539-1656` |
| 2 | `_run69_structures(session, project, period, documents)` | `documents.py:1785-3053` |
| 3 | `_run80_a3_structures(ex)` | `documents.py:3065-3167` |
| — | `_weather_impact_record(ex, doc_type)` (helper called by #2) | `documents.py:1700-1784` |

All three are drained into `si` with **`setdefault`** in `_compute_and_store`
(`documents.py:3427-3435`) — so *a structure supplied through the governed intake is never
displaced by one assembled from a document*, and the ordering baseline → run69 → recognition is
itself a precedence chain.

### 3.1–3.4 Per assembler

**Assembler 1 — `_baseline_structures`.**
Returns `{}` immediately (line 1568) when its guard fails. Produces two keys:
`timePhasedBaseline` (line 1642) and `expenditureBaseline` (line 1646). Reads the time-phased
schedule / schedule-of-values document's printed curve. Where the document states less than a
curve, **the key is absent rather than partial** — the docstring's own words. Fields read that are
declared in `_ASSEMBLER_FIELDS`: **none** (no `time_phased_schedule` or `schedule_of_values` entry
exists in `_ASSEMBLER_FIELDS` at all).

**Assembler 2 — `_run69_structures`.** The large one. Its 19 structure keys, the document type
that produces each, and the fields read:

| Structure key | doc_type branch | line | Key fields read |
|---|---|---|---|
| `ncrRateContributions` (list, appended) | `ncr_log`, `quality_audit_report`, `field_report` | 1874 | `inspections_performed`, `active_work_packages`, `quality_deficiencies_noted`, `total_findings`, `ncr_denominator_basis` |
| `resourceProfile` | `resource_report` | 1884 | resource demand/capacity cells |
| `productionOutputRecord` (setdefault) | `resource_report` | 1895 | production output cells |
| `qualityRequirementRegister` | `inspection_report`, `quality_audit_report` | 1933 | `quality_requirements_json`, `quality_register_id`, `quality_register_period`, `items_inspected`, **`items_passing_first_inspection`**, `critical_quality_failures_json` |
| `environmentalRequirementRegister` | `environmental_report` | 1968 | jurisdiction + permitting authority, requirement rows, corrective-action rows |
| `lookAheadSchedule` | `lookahead_schedule` | 1998 | `lookahead_activities_json` |
| `overheadAllocationBase` (setdefault) | `cost_report` | 2009 | overhead base cells |
| `scheduleNetwork` | `schedule_update` | 2030 | `schedule_network_json` |
| `projectCalendar` | `schedule_update` | 2067 | calendar cells |
| `scheduleReferenceDates` (setdefault) | `schedule_update` | 2089 | data date / baseline dates |
| `scheduleRemainingDuration` (setdefault) | `schedule_update` | 2101 | remaining duration |
| `submittalDecisionRegister` | `submittal_register` | 2191 | `submittal_decisions_json`, `submittal_disposition_legend_json`, `submittal_reporting_period`, the three override tables |
| `ncrExposureRecord` | `ncr_log` | 2241 | `ncr_issued/open/closed`, `report_period`, four override tables |
| `commissioningClearance` | `commissioning_report` | 2265 | `commissioning_items_total`, `commissioning_items_cleared` |
| `weatherImpactEvents` | `field_report` (2302) and `oac_minutes` (2309) | via `_weather_impact_record` | `weather_events_json`, `weather_allowance_*`, `weather_calendar_id`, `weather_day_basis`, `weather_days_claimed/approved`, `weather_milestone_*` |
| `disputeRecord` | `oac_minutes` | 2390 | `disputes_json`, `disputes_recorded` |
| `procurementItems` | `procurement_log` | 2459 | **`procurement_items_json`**, `procurement_day_basis` |
| `subcontractorAssessments` | `subcontractor_report` | 2536 | `subcontractor_ratings_json`, `subcontractor_rating_scale`, `subcontractor_report_date`, `subcontractor_report_version` |
| `contractModificationRegister` / `changeEventRegister` / `pendingChangeExposure` | `change_order` | 2543 / 2644 / 2685 | `modifications_json`, `change_events_json`, `change_exposure_days`, `baseline_contract_sum`, `change_related_delay_days`, `change_available_total_float_days`, `original_contract_duration_days`, `change_time_extension_approved`, `change_forecast_completion_moved` |
| `evmsApplicabilityEvidence` (setdefault) | `contract_value` | 2734 | `federal_acquisition`, `agency_procedure_requires_evms`, `major_acquisition`, `contracting_agency`, `acquisition_designation`, `evms_clause_id`, `award_date`, `acquisition_id` |
| `enforcementNotices` (setdefault) | post-loop, `correspondence_notice` | 2804 | `notice_enforcement_domain/severity/authority/reference` |
| `safetySevereEvents` (setdefault) | post-loop | 2821 | derived from `enforcementNotices["safety"]` |
| `environmentalRequirementRegister["environmental_findings"]` | post-loop | 2829 | derived from `enforcementNotices["environmental"]` |
| `tradeAttributionRecords` (setdefault) | post-loop, eight doc types | 3017 | `trade_attribution_json`, `trade_denominators_json` |

**Scalars that make it return nothing vs. a degraded structure.** The pattern throughout is
`if <rows or figures present>: out[key] = ...`, so **the absence of the driving table means the key
is simply never written** — the structure is `None` by omission, and the module downstream raises
`StructureAbsent` and abstains. Two branches degrade instead of vanishing:

* `qualityRequirementRegister` (1923-1938) assembles from **either** a requirement table **or**
  the two first-pass figures; with only one of them present the structure exists carrying only the
  half that was stated — A6.1 then bands on whichever half it can.
* `procurementItems` (2419-2456) assembles from the rows that were complete and **drops incomplete
  rows silently**; the structure exists degraded, and the optional override cells are omitted so
  A4.9 reports its override as NOT TESTED.

**Assembler 3 — `_run80_a3_structures(ex)`.** Pure, takes one extraction dict. Produces
`analogEstimate` (3077), `externalCostIndex` (3101, plus optional `["cost_exposure"]` at 3113),
`referenceClassPopulation` (3128, plus optional `["governed_percentile"]` at 3145). Reads through
`_text(ex, key)` (3053) and `_pos(ex, key)` (3057) — `_pos` returns `None` for anything not a
positive number, so a non-positive figure degrades the structure rather than refusing it.
Member rows go through `_reference_class_members` (3168).

### 3.5 Which read fields are declared in `information_completeness._ASSEMBLER_FIELDS`

`_ASSEMBLER_FIELDS` (`information_completeness.py:64-146`) has **16 document-type entries**
(confirmed by execution). It is the declaration for "path 2" of the completeness denominator; a
field on neither path is not counted as required.

**Document types whose assembler branch exists but which have NO `_ASSEMBLER_FIELDS` entry at all
— every field they read is undeclared:**

| doc_type | Structure(s) it feeds | Undeclared fields it reads |
|---|---|---|
| `resource_report` | `resourceProfile`, `productionOutputRecord` | all resource demand/capacity and production-output cells |
| `lookahead_schedule` | `lookAheadSchedule` | `lookahead_activities_json` |
| `cost_report` | `overheadAllocationBase` | the overhead base cells |
| `time_phased_schedule` | `timePhasedBaseline`, `expenditureBaseline` | the printed curve fields |
| `schedule_of_values` | `expenditureBaseline` | the printed curve fields |
| `historical_data` / `past_performance_report` | `analogEstimate`, `externalCostIndex`, `referenceClassPopulation` (via `_run80_a3_structures`) | every field those three read |

**Document types WITH an entry, where the entry omits fields the assembler demonstrably reads:**

| doc_type | Declared | Read by the assembler but NOT declared |
|---|---|---|
| `inspection_report` | `trade_attribution_json`, `trade_denominators_json` | **`items_passing_first_inspection`**, `critical_quality_failures_json`, `quality_requirements_json`, `quality_register_id`, `quality_register_period` (`items_inspected` is covered by path 1, the numeric emission table) |
| `quality_audit_report` | `trade_*`, `total_findings`, `inspections_performed`, `active_work_packages` | `quality_requirements_json`, `quality_register_id`, `quality_register_period`, `critical_quality_failures_json`, `items_passing_first_inspection` |
| `environmental_report` | `trade_*` only | jurisdiction, permitting authority, requirement rows, corrective-action rows — i.e. the whole `environmentalRequirementRegister` path |
| `field_report` | weather + trade + three NCR-rate figures | — (the most complete entry) |
| `commissioning_report` | `commissioning_items_total`, `commissioning_items_cleared`, `trade_*` | — |

**This is a finding, not an error of measurement.** `_ASSEMBLER_FIELDS` is the completeness
denominator's declaration of path 2. Every undeclared field above is a real path from a document to
a module that the "based on XX per cent of the information required" caveat **does not count**. The
caveat therefore systematically **overstates** completeness on any project supplying a resource
report, a look-ahead schedule, a cost report, a baseline curve, historical data, or an inspection
report carrying first-pass figures. `information_completeness.py:41` says
`drive_run115.py` section 0 pins every name *in* the declaration to the code — it does not, and
cannot, detect a field the assembler reads that was never declared.

### 3.6 Every precedence rule between two documents supplying the same structure

Read from the code, all in `_run69_structures` unless noted:

| Rule | Structures | Code | Loser discarded whole? |
|---|---|---|---|
| **Longest register wins** | `qualityRequirementRegister` | 1925: `if existing is None or len(requirements) > len(existing.get("requirements", []))` | **Yes** — `out[...] = _reg` replaces the dict. One exception: first-pass figures are then *added* to the surviving register at 1935-1938 if it has none, so the losing document's two figures can survive its register's loss. |
| **Longest register wins** | `procurementItems` | 2457: `if _prev is None or len(_pitems) > len(_prev.get("items") or [])` | **Yes** — whole-dict replacement, no row merge |
| **Longest register wins** | `submittalDecisionRegister` | 2191 area, same shape | **Yes** |
| **Longest register wins** | `subcontractorAssessments` | 2536 area, same shape | **Yes** |
| **First writer wins** (`setdefault`) | `productionOutputRecord`, `overheadAllocationBase`, `scheduleReferenceDates`, `scheduleRemainingDuration`, `evmsApplicabilityEvidence`, `enforcementNotices`, `safetySevereEvents`, `tradeAttributionRecords` | `out.setdefault(...)` at 1895, 2009, 2089, 2101, 2734, 2804, 2821, 3017 | **Yes** — the second document's record is never looked at |
| **Last writer wins** (plain assignment, no guard) | `resourceProfile`, `environmentalRequirementRegister`, `lookAheadSchedule`, `scheduleNetwork`, `projectCalendar`, `ncrExposureRecord`, `commissioningClearance`, `weatherImpactEvents`, `disputeRecord`, `contractModificationRegister`, `changeEventRegister`, `pendingChangeExposure` | plain `out[key] = ...` | **Yes** — silently overwritten by whichever document `documents` iterates last |
| **Accumulating** (the one exception) | `ncrRateContributions` | 1874: `out.setdefault("ncrRateContributions", []).append(_contrib)` | **No** — every contributing document adds a row; this is the only structure where two documents both survive |
| **Governed intake beats document** | all of the above | `documents.py:3428, 3432, 3459` — `si.setdefault(_key, _structure)` | Yes: an intake-supplied structure is never displaced |

**Confirmed from the code: for every longest-register-wins and every last-writer-wins structure,
the losing register is discarded WHOLE. There is no field-level or row-level merge anywhere in
`_run69_structures` except `ncrRateContributions` and the two first-pass scalars noted above.**

---

## Section 4 — Structures to module results (THE MODULE TABLE)

All 31 modules in `registry.service_index()`. Dispatch is
`registry.run_module(new_id, si, rand, period_cutoff)` (`registry.py:531`), which looks the module
up in `models.VALIDATED` (id → `(method_class, function)`). Reachability below was established by
**execution**: `registry.service_index()` and `models.VALIDATED` were resolved in-process, each
runner's source located by `inspect.getsourcelines`, and each was invoked with an empty `si` to
observe its no-input outcome. Structure-vs-scalar reading was read out of each function's actual
source, not grepped for key names — which is exactly the trap Run 116 named.

**Abstain vocabulary** (`models.py`): `insufficient(method_class, sentence, code)` → row with
`status_color: None, insufficient_data: True` and lands in `result["abstained"]`.
`band_abstained(...)` → the module **computed** and **withheld the band**: figures are on the row,
`status_color` is `None`, and it therefore casts no vote. `banded(...)` → computed with a band.
`calibration_pending(...)` → computed, no ladder exists.

The distinction the order asks for: **abstain** = `insufficient(...)`, no arithmetic ran, the
structure was absent. **Computed-without-band** = `band_abstained(...)` / `calibration_pending(...)`,
the arithmetic ran and the figures are published with no colour.

`registry.py:170` — `CORE_VOTING_MODULES = {A1.7, A1.8}`. `registry.py:761` sets `row["votes"]`
from it. `DISABLED_MODULES` (registry.py:153) holds ten ids, **none of which is in service**, so no
module in this table is short-circuited by it.

### Category A1 — Cost & EVM Performance (7 modules)

**A1.2 — CUSUM Anomaly Monitor.** `models.py:2149` → `models_sim.run_cusum` (`models_sim.py:329`).
Reads scalars `si["spi"]` and the **`spiHistory` series** (assembled cross-period in
`run_and_store`), not a structure. `spi` absent → `insufficient("CUSUM")` (abstain).
`spiHistory` shorter than 2 → `insufficient("CUSUM", "Awaiting history (2 periods needed)")`.
**Band cuts, `models_sim.py:196-201`:** breached → `red`; `maxStat >= 0.6 * H` → `amber`; else
`green`. **The only cut value is the 0.6 × H fraction, at `models_sim.py:199`.** No override arm.

**A1.5 — ARIMA CPI Forecast.** `models_evm.py:181`. Reads the **CPI history series** (scalar
fallback path, not a structure key). Fewer than **8** readings → `insufficient("ARIMA_Forecast",
"Awaiting a cost performance history", ...)` (`models_evm.py:203, 208, 213`) — abstain.
**Band cuts, `models_evm.py:219`:** `_OB.descending(v, 0.95, 0.90, 0.85)` applied to each of three
forecast periods, **worst-of the three governing** (line 220-221). At or above **0.95** Green; at or
above **0.90** and below 0.95 Yellow; at or above **0.85** and below 0.90 Amber; below **0.85** Red.
No override arm.

**A1.6 — Earned Schedule.** `models_evm.py:273`. Reads structure **`scheduleReferenceDates`** and
scalar `ev`. Structure absent → `insufficient(..., ABSTAIN_STRUCTURE_ABSENT)` (line 304) — abstain.
**Band cuts:** primary at `models_evm.py:315` — `_OB.descending(_spit, 0.95, 0.90, 0.85)`, i.e.
earned schedule ÷ actual time: ≥0.95 Green, ≥0.90 Yellow, ≥0.85 Amber, <0.85 Red. Second component
at `models_evm.py:377-378`: time variance `_tv` ≤ **0.02** Green, ≤ **0.05** Yellow, ≤ **0.10**
Amber, above Red — **inclusive on the UPPER side**, and being ahead is Green.
**Override arm, `models_evm.py:418-420`:** fires when an approved contractual milestone forecasts
late; `_OB.at_least_as_adverse_as(_posture, "Red")` — publishes **Red**. Where the baseline declares
no approved milestone the override is **NOT EVALUABLE** and its absence is not read as compliance
(line 427-429). `band_hard_override_evaluable` records which.

**A1.7 — TCPI.** `models_evm.py:611`. Reads scalars `bac`, `ev`, `ac` (no structure key).
Missing → `insufficient("TCPI")` at 613, 651, 657, 674 — abstain.
**Band cuts, `models_evm.py:705-707`,** constants at `models_evm.py:580, 601, 582`:
`_TCPI_PLANNED_EFFICIENCY = 1.00`; `_TCPI_OWNER_YELLOW = 1.05`;
`_TCPI_BEYOND_OBSERVED = 1.00 + _TCPI_STABILITY_MARGIN`.
TCPI ≤ **1.00** Green; ≤ **1.05** Yellow; ≤ `_TCPI_BEYOND_OBSERVED` Amber; above Red.
`band_owner_inserted_edge = "Yellow at or below 1.05"` (line 726). **A core voting module.**
No override arm.

**A1.8 — Variance at Completion.** `models_evm.py:805`. Scalars `bac`, `eac`. `bac == 0` →
`insufficient("VAC")` (line 822) — abstain. **Band cuts, `models_evm.py:823-825`,** constants at
`models_evm.py:765, 793, 766`: `_VAC_BUDGET_MET_PCT = 0.0`;
`_VAC_OWNER_YELLOW_PCT = (1 - 1/_VAC_OWNER_YELLOW_CPI) * 100 = -5.2631578…`;
`_VAC_BEYOND_OBSERVED_PCT = (1 - 1/_VAC_STABILITY_CPI) * 100`.
VAC % ≥ **0.0** Green; ≥ **-5.26** Yellow; ≥ `_VAC_BEYOND_OBSERVED_PCT` Amber; below Red.
**A core voting module.** No override arm.

**A1.9 — Budget Execution Rate.** `models_evm.py:865`. Reads a **structure** (absent →
`insufficient(..., ABSTAIN_STRUCTURE_ABSENT)` at line 900) plus scalar `ac`.
**Band cuts, `models_evm.py:917` and `925`:** `_OB.ascending(_cum, 1.05, 1.10, 1.15)` on the
cumulative rate and the same ladder on the period rate: **at or below 1.05 Green; above 1.05 and at
or below 1.10 Yellow; above 1.10 and at or below 1.15 Amber; above 1.15 Red.** Inclusive on the
UPPER side. Under-execution, however far below, is Green (`band_direction_note`, line 965).
**Override arm, `models_evm.py:941-943`:** actual cost above a stated approved cumulative funding
limit → Red. NOT EVALUABLE where no limit is stated (line 947-950).

**A1.11 — Independent EAC Reconciliation Index.** `models_evm.py:1178`. Reads structure
**`independentEacPair`**, plus `bac`, `remainingContingency`, `pendingChangeExposure`.
Pair absent/incomplete/not genuinely distinct → `insufficient(...)` at 1234, 1248 — abstain.
**Band cuts, `models_evm.py:1261` and `1267`:** `_OB.ascending(_spread * 100, 3.0, 5.0, 10.0)` and
`_OB.ascending(_over * 100, 3.0, 5.0, 10.0)`; boundary words at 1253-1254: **at or below 3 per cent
Green; above 3 and at or below 5 Yellow; above 5 and at or below 10 Amber; above 10 Red.**
**Override arm, `models_evm.py:1287-1289`:** the higher forecast exceeds BAC **and** remaining
contingency is smaller than the gap → Red. Reported NOT EVALUABLE when BAC is absent or when the
gap is positive but no contingency figure exists.

### Category A2 — Schedule Performance (5 modules)

**A2.1 — PERT Network Criticality.** `models.py:1646`. Reads the **schedule network structure**;
absent → `insufficient(..., ABSTAIN_STRUCTURE_ABSENT)` at 1696, 1715, 1739 — abstain.
**Cuts come from `band_reference_data.json`, key `pert_path_concentration_bands`**, loaded at
`models.py:1767` (`_BR.entry(...)`). Values: **green_at_or_above 0.8, yellow_at_or_above 0.6,
amber_at_or_above 0.4, red_below 0.4**; margin cap **margin_no_cap_at_or_above 0.2,
margin_cap_yellow_at_or_above 0.1, margin_cap_amber_below 0.1**.
Applied at `models.py:1833-1843`: primary band on C1, then the **dominance-margin cap** (M = C1−C2)
which can only worsen the band. If the entry is not configured → `band_abstained` (line 1821-1824)
— **computed without band**.
**Override arm, `models.py:1846-1847`:** `_controlling_float < 0` → Red outright. Where the network
states no imposed completion date the override is not evaluable and was not applied (1869-1870).
(`pert_criticality_bands` — 0.2/0.5/0.8 — is also configured in the JSON but the module bands on
path concentration, not the activity criticality index.)

**A2.7 — Milestone Trend Analysis.** `models_ext.py:288`. Reads a **structure**; absent →
`insufficient(..., ABSTAIN_STRUCTURE_ABSENT)` at 312.
**Cuts from `band_reference_data.json`, key `critical_path_control_bands`**, loaded at
`models_ext.py:352`, applied through `hybrid_schedule_slip_band(...)` at `models_ext.py:385`.
Values (all in the JSON): **float_green_above 20, float_yellow_at_or_above 11,
float_yellow_at_or_below 20, float_amber_at_or_above 1, float_amber_at_or_below 10,
float_red_at_or_below 0; slip_green_at_or_below 0, slip_yellow_at_or_below 10,
slip_amber_at_or_below 20, slip_red_above 20; guardrail_yellow_above_fraction 0.02,
guardrail_amber_above_fraction 0.05, guardrail_red_above_fraction 0.1;
critical_flag_tolerance_days 0.0, near_critical_band_days 10.** Working days.
The JSON's `worst_of` note: the posture is the **most severe of four applicable results**.
Unconfigured or no rule evaluable → `band_abstained` (380, 399) — computed without band.
**Override arm, `models_ext.py:412`:** `band_hard_override_fired = bool(_committed)` — a committed
milestone forecasting late. The separate `milestone_slip_ratio_bands` entry in the JSON
(0.02/0.05/0.10) is **configured but not the ladder this runner uses**; see Section 8.

**A2.8 — Look-Ahead Schedule Health.** `models_ext.py:427`. Reads structure **`lookAheadSchedule`**
via `canonical_v3.look_ahead_ready_fraction`; absent → `insufficient(..., ABSTAIN_STRUCTURE_ABSENT)`
at 453. **Cuts from `lookahead_readiness_bands`**, `_BR.entry` at `models_ext.py:467`, applied at
`models_ext.py:514-515`: **at or above 0.9 Green; at or above 0.8 Yellow; at or above 0.7 Amber;
below 0.7 Red.** Inclusive on the lower side. Unconfigured → `band_abstained` (507-510).
**Override arm, `models_ext.py:483-505`:** a critical-path or zero/negative-float activity blocked
by an unresolved constraint → returns **Red directly**, bypassing the ratio entirely
(`banded(..., status_color="Red", band_hard_override_fired=True)`).

**A2.9 — Resource Loading Index.** `models_ext.py:543`. Reads structure **`resourceProfile`**;
absent → `insufficient(..., ABSTAIN_STRUCTURE_ABSENT)` at 568.
**Cuts from `resource_peak_load_bands`**, `_BR.entry` at 585, applied at `models_ext.py:645-646`:
**at or below 1.0 Green; at or below 1.1 Yellow; at or below 1.2 Amber; above 1.2 Red.**
Unconfigured → `band_abstained` (638-641). **Override arm, `models_ext.py:608-635`:** any resource
overload on a zero or negative float path → **Red directly**, bypassing the ratio.
Unlike resources are never aggregated and no conversion is invented.

**A2.12 — Critical Path Analysis.** `models_ext.py:1652`. Reads structure **`scheduleNetwork`**;
absent → `insufficient(..., ABSTAIN_STRUCTURE_ABSENT)` at 1680, 1711. Gated behind A2.1: A2.1
abstains where the network does not validate.
**Cuts from `critical_path_control_bands`** (same JSON entry and same values as A2.7), `_BR.entry`
at `models_ext.py:1704`, applied through `hybrid_schedule_slip_band` at 1764. `near_critical_band_days`
= **10** is passed explicitly at line 1709. Unconfigured, or `_band["colour"] is None` →
`band_abstained` (1759, 1774) — computed without band, naming which rules were not evaluable.
**Override arm, `models_ext.py:1787`:** `band_hard_override_fired = bool(reading
["committed_milestones_forecast_late"])`.

### Category A3 — Cost Risk (4 modules)

**A3.2 — Contingency Burn Rate.** `models_ext.py:771`. Reads **scalars only** —
`originalContingency`, `remainingContingency`, `actualPctComplete` (**a scalar-fallback module: it
carries no structure key at all**). Missing → `insufficient(...)` at 792; zero/invalid denominator
→ `insufficient(..., ABSTAIN_INVALID_DENOMINATOR)` at 816.
**Band cuts, `models_ext.py:866-874`, boundary words at 879-880:** burn against progress
**at or below 1.0 Green; above 1.0 and at or below 1.2 Yellow; above 1.2 and at or below 1.5 Amber;
above 1.5 Red.** `band_basis_id = "owner_configured_contingency_burn_tolerance"`.
Where progress is not the quantity the threshold is drawn over → `band_abstained` (858-864).
**Override arm, `models_ext.py:866` + `906`:** the **exhaustion arm** —
`band_exhaustion_arm_fired`; contingency exhausted forces `color = "Red"` ahead of the ladder.

**A3.3 — Labor Productivity Index.** `models_ext.py:913`. Reads a **structure** (the production
output record); absent → `insufficient(..., ABSTAIN_STRUCTURE_ABSENT)` at 937.
**Band cuts written as literals at `models_ext.py:951-952`: at or above 0.95 Green; at or above
0.90 Yellow; at or above 0.85 Amber; below 0.85 Red.** `band_basis_id =
"owner_configured_labor_productivity_tolerance"`. **No override arm.** These four values are **not**
in `band_reference_data.json` — they are code literals, which is a live inconsistency with the
Run 101 §12.3 rule that band reference numbers never be literals. Named, not fixed.

**A3.5 — Overhead Absorption Rate.** `models_ext.py:1055`. Reads structure
**`overheadAllocationBase`**; absent → `insufficient(..., ABSTAIN_STRUCTURE_ABSENT)` at 1079.
**Cuts from `overhead_absorption_variance_bands`**, `_BR.entry` at 1104, applied at
`models_ext.py:1142`: variance **at or below 0.05 Green; at or below 0.10 Yellow; at or below 0.15
Amber; above 0.15 Red** (rendered as per cent in the boundary words). A positive variance is
UNFAVOURABLE; a favourable variance is Green. Unconfigured → `band_abstained` (1133-1137).
**Override arm, `models_ext.py:1149-1150`:** the **substantial-completion floor** — where the
project is substantially complete and final overhead remains materially unabsorbed, a Green or
Yellow is lifted to **Amber**. This is a floor, not a Red override.

**A3.6 — Cost Risk Analysis P80.** `models_ext.py:1189`. Reads a **structure** plus scalar `bac`;
absent → `insufficient(..., ABSTAIN_STRUCTURE_ABSENT)` at 1216.
**Cut from `p80_gap_boundary`: `yellow_gap_at_or_below = 0.1`**, used as `_gap_cut` at
`models_ext.py:1294-1295`. Ladder at `models_ext.py:1279-1285`: **gap of zero or below → Green;
budget below P80 with a gap at or below 0.1 → Yellow; gap above 0.1 with the budget still at or
above the median → Amber; budget below the median → Red.** Where the banded quantity is not
measurable, or the distribution does not support a P80 → `band_abstained` (1252-1261) — computed
without band. **No override arm.**

### Category A4 — Document-Derived Condition Signals (8 modules)

**A4.2 — RFI Velocity.** `models_doc.py:237`. Reads a structure **or** falls back to the scalars
`rfiCount, rfiPeriodDays, rfiOpen, rfiOverdue, rfiAvgResponseDays, rfiOldestOpenDays, rfiNumber,
rfiResponseTimeDays`. **This is one of the scalar-fallback modules Run 116 found**: a grep for
structure keys misses the second arm entirely (lines 301-374). Structure absent AND scalars absent
→ `insufficient("RFI_Velocity", ...)` at 257, 301, 308, 314, 321.
**Band cuts, `_rfi_band` at `models_doc.py:231-232`:** `ratio = overdue / open_count`;
**ratio == 0 → Green; ≤ 0.10 → Yellow; ≤ 0.25 → Amber; above → Red.**
Special arms: overdue not a number → **no band**, reason returned (185-192);
`open_count <= 0` with `overdue > 0` → **Red** (`_RFI_OVERDUE_BOUNDARY`, lines 223-225);
`open_count <= 0` with no overdue → **no band** ("with nothing open there is nothing that can be
overdue"). No-band arms come back as `band_abstained` (294, 373).
**Threshold-source precedence is genuinely exercised** (lines 189-193): a project stating
`rfiResponsePeriodBusinessDays > 0` sets `THRESHOLD_SOURCE_PROJECT` (rung 1); otherwise the
configured `rfi_contract_response_period_business_days = 7` from the JSON is rung 3.

**A4.3 — Submittal Rejection Rate.** `models_doc.py:536`. Reads structure
**`submittalDecisionRegister`**, with a **scalar fallback** on `submittalsTotal`,
`submittalsRejected`, `rfaTotal`, `rfaRejected`, `rfaResubmit`, `rfaOpen`, `rfaAvgReviewDays`
(lines 618-666) — **second scalar-fallback module**. Absent both → `insufficient(...)` at 555, 585,
618, 620, 628; register present but without identifier/revision/decision date → `band_abstained`
(657-666).
**Band cuts: `SUBMITTAL_REJECTION_CUTS` at `models_doc.py:404-405`** —
`((35.0, "Red"), (20.0, "Amber"), (10.0, "Yellow"))`, applied by `_pct_band`
(`models_doc.py:462-467`), Green being the bottom. In words (line 411-412): **below 10 % Green; at
or above 10 and below 20 Yellow; at or above 20 and below 35 Amber; at or above 35 Red**, each
boundary inclusive on its lower side.
**Override arm, `models_doc.py:590-591`:** `_override_state(structure, SUBMITTAL_OVERRIDE_FIELDS)`
— fields at `models_doc.py:473-477`:
`rejected_critical_or_long_lead_forecast_after_need_by`,
`rejected_unresolved_past_review_deadline_blocking_work`,
`critical_package_rejected_resubmittals`. Any firing → `_colour = "Red"` regardless of rate.
Absent fields are reported as ABSENT (`band_override_fields_absent`), never as "tested and did not
fire".

**A4.4 — NCR Rate.** `models_doc.py:682`. Reads structure **`ncrExposureRecord`** through
`canonical.ncr_rate`, and the accumulating **`ncrRateContributions`** for the pooled denominator;
absent → `insufficient(..., ABSTAIN_STRUCTURE_ABSENT)` at 702, 750.
Where the denominator type is not one the ladder is drawn over → `band_abstained` (757) with
*"No band is asserted: the owner's Run 106 NCR ladder is a percentage of…"* — computed without band.
**Band cuts: `NCR_RATE_CUTS` at `models_doc.py:428-430`** — `((10.0, "Red"), (5.0, "Amber"),
(2.0, "Yellow"))`, applied by `_pct_band` at line 779. In words (441-444): **below 2 % Green; at or
above 2 and below 5 Yellow; at or above 5 and below 10 Amber; at or above 10 Red.**
Denominator: inspections performed, falling back to active work packages
(`NCR_DENOMINATOR_TYPES`, `models_doc.py:436-439`); the type is stored with every result and the
two are never mixed within one project's trend.
**Override arm, `models_doc.py:767, 779`:** `NCR_OVERRIDE_FIELDS` (`models_doc.py:478-483`) —
`open_critical_life_safety_structural_or_code_ncr`,
`hold_point_or_commissioning_or_required_inspection_blocking_turnover`,
`max_repeat_ncrs_one_root_cause_or_trade`, `ncr_open_past_contractual_closure_date`.
Any firing → **Red regardless of rate**; a high inspection count cannot dilute an open critical NCR.

**A4.5 — Weather Day Impact.** `models_doc.py:808`. Reads structure **`weatherImpactEvents`**
(assembled from OAC minutes *and* field report); absent → `insufficient(...,
ABSTAIN_STRUCTURE_ABSENT)` at 825.
**Band cuts, two components:**
allowance consumption, `models_doc.py:838` — `_OB.ascending(_consumed, 0.80, 1.00, 1.20)`: **at or
below 0.80 Green; above 0.80 and at or below 1.00 Yellow; above 1.00 and at or below 1.20 Amber;
above 1.20 Red**;
float consumption, `models_doc.py:921` — `_OB.ascending(_fc, 0.50, 0.75, 1.00)`: **at or below 0.50
Green; above 0.50 and at or below 0.75 Yellow; above 0.75 and at or below 1.00 Amber; above 1.00
Red**. Both inclusive on the upper side. Neither component evaluable → `band_abstained` (999).
**Override arm, `models_doc.py:945-962`:** a documented weather event causing a **contractual** or
**owner_committed** milestone to forecast late → `at_least_as_adverse_as(_posture, "Red")`.
Where the record says nothing about a milestone forecasting late the override is **NOT EVALUABLE**
and silence is not read as compliance.

**A4.6 — Change Order Frequency.** `models_doc.py:1026`. Reads structures
**`changeEventRegister`** / **`pendingChangeExposure`**; absent → `insufficient(...,
ABSTAIN_STRUCTURE_ABSENT)` at 1043.
**Band cuts, `models_doc.py:1073-1075`**, whose 0.20 anchor is the configured
`change_order_contingency_reserve_fraction = 0.2` from `band_reference_data.json`:
**net change of zero or below, or additions strictly under 0.05 → Green; additions at or above 0.05
and at or below 0.10 → Yellow; above 0.10 and at or below 0.20 → Amber; above 0.20 → Red.**
An omission is never adverse: a reduction is Green and is never added to the additions.
A **schedule-impact** band is computed separately and the published band is
`max(bands, key=_RANK)` — **worst-of the two halves** (line 1077-1078). **No override arm.**

**A4.7 — Dispute Escalation Index.** `models_doc.py:1229`. Reads structures
**`claimDisputeRegister`** (governed process path) **or** **`disputeRecord`** (the OAC-minutes
count path). Neither → `insufficient(...)` at 1262, 1294, 1355.
**Two ladders, and they are different measures.**
*(a)* The **escalation-class ladder**, `canonical_v4.DISPUTE_ESCALATION_CLASSES`
(`canonical_v4.py:916-927`): `normal_administration` → **Green**; `open_issue_or_reservation` →
**Yellow**; `formal_notice_or_escalation` → **Amber**; `legal_or_stoppage` → **Red**. Aggregation
rule: *"highest documented open stage"* (line 1457). These are class labels, not numeric cuts.
*(b)* The **count ladder** (Run 115, `canonical_v4.py:931-936`): no dispute recorded → Green; one →
Amber; more than one → Red. Owner-calibrated; no published standard fixes these three rungs.
A separate **duration** arm bands the oldest open dispute in working days,
`band_basis_id = "owner_configured_dispute_duration"` (1330).
Where no dispute is recorded and Green would be an overstatement → `band_abstained` (1432-1435):
*"Green is a statement that items were resolved through normal administration"*.
**Override arm, `models_doc.py:1388-1398, 1423-1431, 1438-1439`:** any documented dispute preventing
progress on a controlling or near-critical activity → **Red**, and it fires even from the
`band_abstained` arm (1424-1431: `banded(..., status_color="Red",
band_posture_before_override=None)`). Where no open issue states the fact either way, NOT EVALUABLE.

**A4.8 — Subcontractor Performance.** `models_doc.py:1709`. Reads structure
**`subcontractorAssessments`**; absent → `insufficient(...)` at 1748.
**Band cuts, `models_doc.py:1884-1886` — the owner's Run 107 ladder, a dual label/number scale:**
**Exceptional or Very Good, or 90 to 100 → Green; Satisfactory, or 80 to 89 → Yellow; Marginal, or
70 to 79 → Amber; Unsatisfactory, or below 70 → Red.** Each numeric boundary inclusive on its lower
side. The numeric arm's values are also configured in `band_reference_data.json` as
`contractor_numeric_fallback_bands` (green_at_or_above 90, yellow_at_or_above 80,
amber_at_or_above 70, red_below 70) — used only where no owner scale is provided, and yielding to
the contract's own scorecard.
`band_basis_id = "source_report_rating_normalization"`.
**Override arms, two.** (i) **Eight trade factors** (`trade_factors.py`, `_TF`) adjust the stated
rating; `trade_overrides_fired` / `trade_override_detail` are on the row, and a fired trade
override *"bypasses the average"* (1853-1855) — including `_TF.STOP_WORK_WORDS`, which is
**Red outright and is not one voice among eight** (1901). (ii) **PM review** (`pm_review.resolve`
at `models_doc.py:1770`) can hold the reading: an Amber or Red normalised posture, or a lift of two
or more bands, is held until a Project Manager reviews it → `band_abstained` (1913-1917) carrying
`band_boundary_if_reviewed`.

**A4.9 — Procurement Lead Time Monitor.** `models_doc.py:1976`. Reads structure
**`procurementItems`**; absent → `insufficient(..., ABSTAIN_STRUCTURE_ABSENT)` at 1993.
**Band cuts, per item, `models_doc.py:2063-2073`, boundary words at 2107-2110:**
**Green** where the item is on or before required-on-site; **Yellow** where it is **1 to 5 working
days** late and NOT on controlling or near-critical work; **Amber** where it is **6 to 10 days**
late, or 1 to 5 days late **on** controlling or near-critical work; **Red** where it is **more than
10 days** late. Aggregation: `band_aggregation_rule = "most adverse item"` (2139).
Where the register does not state criticality, Yellow cannot be told from Amber and the item is
**not assessed** (2070-2071) — criticality is never guessed.
No item bandable → `band_abstained` (2156-2164) — computed without band.
**Override arm, `models_doc.py:2086-2093`:** a long-lead item whose `protection_date_missed` is
true → `at_least_as_adverse_as(_worst_band, "Red")`. Where no item states the fact either way, NOT
EVALUABLE (2103).

### Category A6 — Delivery Quality Performance (4 modules)

All four route through one shared runner factory, `models_cat89.py:1275`
(`run_A6_1 / run_A6_2 / run_A6_3 / run_A6_4` are closures over it), which calls
`_a6_band(module_id, result, structure)` at `models_cat89.py:1344` → `_a6_band` at
`models_cat89.py:389`. `_a6_band` returns `(colour, boundary, basis, provenance, boundary_provenance,
threshold_source)`; a colour without a `threshold_source` **raises** rather than storing a band
(line 1363). A `StructureAbsent` → `_abstain(...)` at 1301, 1307, 1317, 1320. A withheld band sets
`row["status_color"] = None` and `row["band_withheld_reason"] = _basis` (1378) — **computed without
band, no vote cast**.

**A6.1 — Quality Compliance Index.** `_band_quality_compliance`, `models_cat89.py:418`.
Measure: `first_pass_acceptance = items passing on FIRST inspection / items inspected`, computed by
`canonical_v6._first_pass_acceptance` (`canonical_v6.py:948-980`) from the
**`qualityRequirementRegister`** structure. Rate `None` → band withheld with the reason (461-476);
the requirement conformance rate is reported and explicitly **is not** what bands.
**Cuts from `quality_first_pass_acceptance_bands`**, `_BR.entry` at `models_cat89.py:479`:
**at or above 0.95 Green; at or above 0.90 Yellow; at or above 0.80 Amber; below 0.80 Red.**
Precedence: a project quality plan or ITP stating an acceptance target **for this quantity**
(`acceptance_target`, `acceptance_target_source`, `acceptance_target_quantity` on the structure,
lines 481-486) overrides at rung 1; otherwise the owner's 95/90/80 ladder at rung 3.
**Override arm, `models_cat89.py:478, 488`:** any failed critical inspection, hold-point inspection,
life-safety requirement, commissioning acceptance test or explicitly designated critical quality
item → **Red however high the rate**; noncompensatory, and it is tested **first**.
The rework-cost benchmarks are explicitly **not** the source and are not applied.

**A6.2 — Safety Performance Index.** `_band_safety`. Computes the OSHA identity
(recordable cases × 200 000 ÷ employee hours) from `oshaRecordableIncidents` and `totalManhours`.
**Cuts from `safety_benchmark_ratio_bands`:** benchmark ratio = project TRIR ÷ the applicable BLS
construction TRIR — **at or below 0.75 Green; at or below 1.00 Yellow; at or below 1.50 Amber;
above 1.50 Red.** The benchmark itself is the separately configured
`construction_industry_recordable_rate = 2.4` (BLS SOII, NAICS 23, 2023, marked
`verified: false`), never a literal. The absolute-frequency ladder
`construction_frequency_band_cutoffs` is also configured: **green_below 1.2, yellow_at_or_below 2.4,
red_at_or_above 4.8** per 200 000 hours.
**Floor:** `safety_exposure_floor_hours = 200000` — beneath it the module abstains rather than band
a rate that swings on one event. **Severity computes and displays and asserts NO band**: the JSON
records `no_severity_benchmark` — no published construction severity cutoff exists.
**Override arm:** *Red for a fatality, serious life-threatening event, stop-work order, or
unresolved high-severity safety violation* (`safety_benchmark_ratio_bands.hard_override`), fed from
the `safetySevereEvents` structure derived from `enforcementNotices`.
A6.2 is the one module whose **basis and boundary provenance differ** (`_a6_band` note, lines
408-411): the formula and benchmark are CODIFIED, the multipliers OWNER-CONFIGURED —
`band_provenance_split_note` (1371).

**A6.3 — Environmental Compliance Rate.** `_band_environmental`. Reads
**`environmentalRequirementRegister`**. Refuses to assess conformance without **both** a
jurisdiction and a permitting authority (documents.py:1943-1955): a half-established applicability
is not an applicability, so the structure is not assembled and
`APPLICABILITY_NOT_ESTABLISHED` stands.
**Cuts from `environmental_timely_closure_bands`:** timely closure rate = corrective actions closed
by their required deadline ÷ actions requiring closure — **at 1.0 Green; at or above 0.95 Yellow;
at or above 0.85 Amber; below 0.85 Red.** The deadline itself is CODIFIED:
`cgp_corrective_action_deadline_days = 7` calendar days from discovery (EPA CGP Part 5).
**Override arm:** *Red for any overdue critical permit violation, enforcement notice, stop-work
condition* — fed from `environmentalRequirementRegister["environmental_findings"]`, itself derived
from `enforcementNotices` (documents.py:2829).

**A6.4 — Contractor Performance Assessment Signal.** `_band_contractor`, which takes only
`result` (no structure argument). Reads the contractor factor set assembled by
`contractor_factors.py` / `trade_factors.py`. **Cuts from `contractor_numeric_fallback_bands`:**
**at or above 90 Green; at or above 80 Yellow; at or above 70 Amber; below 70 Red** on a 0-100
score — used **only where no owner scale is provided**, and yielding to the contract's own
scorecard or rating method. Where no numeric score and no owner scale exist, the band is withheld
and the figures are displayed.

### Category B1 — Signal Synthesis (2 modules)

**B1.1 — Conservative Dominance.** `models_decision.py:174`. Reads **the other modules' bands**,
not signal inputs: `_signal_statuses(si)` over `SIGNAL_NAMES`. Nothing available →
`insufficient("Conservative_Dominance")` at 177.
**Rule, `models_decision.py:213-222` — no numeric cuts:** `_dominant = _dominant_band(_bands)`;
if `_dominant is None` the state falls back to the decision layer's `healthState`;
**if `_dominant == "Green"` but not every signal is Green, the state is forced to `"Amber"`**
(218-219) — the conservative treatment of absent evidence is part of the rule, not an exception:
the calmest band is reachable only on complete evidence. Otherwise `state = _dominant`.
The related `_derive_health_state` (`models_decision.py:85-98`) has one numeric-ish cut:
**`reds >= 2`, or a CUSUM breach with `s["mc"] == "Red"`, → `"Red-review"`**, tested *first* so no
ordering accident can let two red signals reach Green.

**B1.2 — Weighted Voting.** `models_gov.py:489-497`. **At dispatch it reads nothing and abstains**:
`return dict(insufficient("Weighted_Voting"), abstention_reason=WEIGHTED_VOTING_DEFERRED)`.
It is re-evaluated in a **second pass** in `compute.compute_project` (`compute.py:511-542`), after
the category rollup, by `_weighted_voting_result(category_statuses)`. Its row is popped out of
whichever bucket it landed in and replaced with the second-pass reading, or with the abstention
the postures state. **It cannot reach the rollup it reads**: `category_statuses` is already built
and is not rebuilt, so a B1.2 band sets no category and reaches no project status (compute.py:517-520).
Its cuts are the ones in `project_posture`/`category_posture` (Section 5.4). No override arm.

### Category C1 — Data Integrity (1 module)

**C1.5 — Information Completeness Ratio.** Runs through the same `models_cat89.py:1275` factory,
but `_a6_band` returns `(None, None, None, None)` for it (`models_cat89.py:399-401`): *"C1.5 and
anything else: Category 9 is metadata and casts no vote."* **It therefore never asserts a band and
never carries one.** Its arithmetic is `information_completeness.information_completeness(documents)`
(`information_completeness.py:190`): `extracted / REQUIRED_TOTAL`, where `REQUIRED_PAIRS` is
computed once at import from `_NUMERIC_EMISSIONS`, `_DATESTR_EMISSIONS`, `_AS_OF_KEYS` and
`_ASSEMBLER_FIELDS`. **`NO THRESHOLD IS APPLIED ANYWHERE IN THIS FILE`** (module docstring, line 49):
there is no rung, no colour and no cut-off. Its output is the caveat sentence at the bottom of the
recommendation. It is excluded from the project status by `contributes_to_project_status`
(compute.py:341-353) and by `PROJECT_EXCLUDED_CATEGORIES` (project_posture.py:76).

### 4.2 note — reachability established other than by grep

The four modules that band through **scalar fallbacks and carry no structure key** are
**A1.7 TCPI**, **A1.8 Variance at Completion**, **A3.2 Contingency Burn Rate**, and
**A4.2 RFI Velocity** (whose fallback arm at `models_doc.py:301-374` is entirely separate from its
structure arm at 257-297). **A4.3 Submittal Rejection Rate** carries a structure key *and* a full
scalar fallback arm (618-666), so it appears on both sides. **A1.2 CUSUM** reads `spi` plus a
cross-period series and no structure. A grep for structure key names finds none of these.

---

## Section 5 — Module results to category posture

### 5.1 The five weighted categories, their weights, and their modules

`server/app/simulation/project_posture.py:62-69`:

| Key | Category | Weight | Modules in service |
|---|---|---|---|
| A1 | Cost & EVM Performance | **0.28** | A1.2, A1.5, A1.6, A1.7, A1.8, A1.9, A1.11 (7) |
| A2 | Schedule Performance | **0.28** | A2.1, A2.7, A2.8, A2.9, A2.12 (5) |
| A3 | Cost Risk | **0.17** | A3.2, A3.3, A3.5, A3.6 (4) |
| A4 | Document-Derived Condition Signals | **0.11** | A4.2, A4.3, A4.4, A4.5, A4.6, A4.7, A4.8, A4.9 (8) |
| A6 | Delivery Quality Performance | **0.16** | A6.1, A6.2, A6.3, A6.4 (4) |

Sum asserted `== 1.0` at `project_posture.py:71`. Provenance (line 81): *"the owner's stated
authority, Run 95 section 3 restated at Run 106 section 1: his decision, not a derived or
literature value and not calibrated."* **28 modules across the five.**

### 5.2 Categories not weighted, and where their results go

Two, holding the remaining **3** modules:

* **B1 Signal Synthesis** (B1.1 Conservative Dominance, B1.2 Weighted Voting). Group B.
  `contributes_to_project_status("B")` is **True** (`compute.py:353` excludes only C and D), so B1
  *does* form a category status and *does* enter `voting` for the Dempster fusion at
  `compute.py:549-553`. But it carries **no weight in `PROJECT_CATEGORY_WEIGHTS`**, and
  `project_posture` iterates only `PROJECT_CATEGORY_WEIGHTS` (line 127), so **B1's posture reaches
  the stored `dempster_band` and the conflict coefficient, and reaches nothing that sets
  `project_status`.**
* **C1 Data Integrity** (C1.5). Excluded twice over: by `contributes_to_project_status("C")` →
  False, and by `PROJECT_EXCLUDED_CATEGORIES = frozenset({"C1"})` with an executable assert at
  `project_posture.py:78`. C1.5's number goes to the **caveat sentence** on the recommendation and
  nowhere else.

### 5.3 The fusion rule per category, read from the code

`category_posture.CATEGORY_RULES`, `category_posture.py:91-98`:

| Category | Rule | Constant |
|---|---|---|
| A1 | **average of module scores** | `RULE_AVERAGE` |
| A2 | **average of module scores** | `RULE_AVERAGE` |
| A3 | **average of module scores** | `RULE_AVERAGE` |
| A4 | **average of module scores** | `RULE_AVERAGE` |
| A6 | **worst wins** | `RULE_WORST` |
| any unassigned (B1, C1) | **worst wins** | `DEFAULT_RULE = RULE_WORST` (line 100) |

Implementation: average at `category_posture.py:227-246`; worst at 248-256 via
`fusion.worst_band` (`fusion.py:141-144`), which ranks on `fusion.BAND_SEVERITY =
{"Green": 0, "Yellow": 1, "Amber": 2, "Red": 3}` (`fusion.py:138`).
A6's rule is worst-wins *because* its modules are conformance and compliance measures and an
adverse reading in one is a finding in its own right (`WORST_BOUNDARY_WORDS`, line 117-121).

### 5.4 The band-score mapping and the cut points, quoted from the constants

`category_posture.py:104` — `BAND_SCORE: dict[str, float] = {"Green": 2.0, "Yellow": 1.0,
"Amber": -1.0, "Red": -2.0}`. *"Adverse is negative, so a single Red pulls the mean twice as hard
as a Yellow lifts it."*

`category_posture.py:108` — `AVERAGE_CUTS: tuple[tuple[float, str], ...] = ((1.5, "Green"),
(0.5, "Yellow"), (-0.5, "Amber"))`, applied by `band_average` (line 148-158), Red being the open
bottom. In the constant's own words (`AVERAGE_BOUNDARY_WORDS`, 110-115):

> "at or above 1.5 is Green; at or above 0.5 and below 1.5 is Yellow; at or above -0.5 and below
> 0.5 is Amber; below -0.5 is Red. Each boundary is INCLUSIVE ON ITS LOWER SIDE. A module that
> computed without a band, abstained or failed is not in the average and does not count as zero."

**The project level reuses exactly these:** `project_posture.py:55` imports `AVERAGE_CUTS` and
`BAND_SCORE` from `category_posture`, and `band_weighted` (project_posture.py:105-110) walks the
same tuple. There is one ladder, not two.

`category_posture.py:135` — `SINGLE_READING_COUNT = 1`: *not* a threshold and not a floor on
publication. Where an average rests on one banded module the record sets `posture_single_reading`
and appends `thinness_words` (160-176) to the arithmetic.

### 5.5 What a category does when some of its modules abstain

**Abstentions are DROPPED. They are neither counted as zero nor allowed to block the category.**

* `category_posture` (line 199-204) walks the pairs it is handed and skips any band not in
  `BAND_SEVERITY` — `None` included. Only survivors become `contributors`.
* `posture_banded_count` is the number that survived; `posture_modules_considered` is how many were
  on the table, taken from the caller's explicit count or the length of what was handed over,
  **never inflated** (lines 197-198). `compute.py:487-491` hands over **every admitted module,
  banded or not**, so `posture_modules_considered` is the full category size on that path.
* No contributors at all → `record["status"] = None` and the arithmetic reads: *"No module in this
  category asserted a band, so the category carries no posture. That is an absence of a reading,
  not a favourable one."* (lines 219-223). The category is then **unassessed** at project level.

---

## Section 6 — Category posture to published status

### 6.1 The project-level rule and the file it lives in

`server/app/simulation/project_posture.py`, function **`project_posture(category_statuses)`**
(line 113). `PROJECT_RULE = "weighted_vote_over_category_postures"` (line 84).

Arithmetic (lines 158-171): weights are **renormalised over the categories that actually carry a
posture** — `total = sum(PROJECT_CATEGORY_WEIGHTS[k] for k in present)`, `weights = {k: w/total}`.
An unassessed category is **removed from the denominator and never scored as zero**, which would
read as a neutral assessment when nothing was assessed at all (line 187-189). The weighted sum is
computed from the **unrounded** normalised weights and rounded to ten places so a repeated binary
fraction cannot put the sum a hair under a cut it is exactly on (lines 173-176); the published
figure is rounded to four. `band_weighted` then bands it on `AVERAGE_CUTS`.

`PROJECT_BOUNDARY_WORDS` (line 88-93) states it: **"at or above 1.5 is Green; at or above 0.5 and
below 1.5 is Yellow; at or above -0.5 and below 0.5 is Amber; below -0.5 is Red. Each boundary is
INCLUSIVE ON ITS LOWER SIDE. There is no override: an adverse category moves the sum by its own
weight and no more."**

The caller is `compute.compute_project` (`compute.py:355`), and `spec_projection` calls the same
`project_posture`, so the two paths cannot drift.

### 6.2 What is required before a status is issued, and what is published when it is not

`compute.py:43` — `_REQUIRED_CATEGORIES: tuple[str, ...] = ("A1", "A2", "A3", "A4", "A6")`.
`compute.py:49` — `_SUPPORTING_CATEGORIES: tuple[str, ...] = ()` — **the supporting tier is empty;
there is no second tier any more.**

`compute.py:600-602`:
```
_required_missing = [k for k in _REQUIRED_CATEGORIES
                     if not (category_statuses.get(k) or {}).get("status")]
```
`compute.py:624-626`:
```
_published = (_COMPLETE if _complete
              else (_AWAITING if (_required_missing or not _fused_band) else _fused_band))
```

**All five required categories must carry a posture.** Otherwise the published status is
**`"Awaiting analysis"`** (`_AWAITING`, `compute.py:60`), accompanied by
`project_status_reason` from `_awaiting_reason(...)` (`compute.py:86`) naming which category is
unassessed and why. `project_status_basis.required_missing_detail` (compute.py:655-662)
distinguishes `"never_called"` (no module in the category ran) from `"not_assessed"` (the category
ran and no module asserted a band).

The weighted band is still computed and still published **beside** the status as `fused_band`
(compute.py:672-676), so an Awaiting-analysis brief can still show every assessed category and any
that are Red. `dempster_band` (compute.py:683) carries the band Dempster's rule would have given.
`project_status_basis.official` (compute.py:666) is `_complete or not _required_missing`.

"Indeterminate" is gone (compute.py:51-58). Rows already stored carrying it keep what they hold;
nothing is rewritten.

### 6.3 The completion path, and how it interacts with the banded status

**Completion is a SEPARATE STATE that the platform publishes IN THE `project_status` FIELD,
displacing the band — and it sits AHEAD of the required-core gate.**

`compute.py:324` — `delivery_complete(signal_inputs)`, the one function both this path and
`spec_projection` call. Two paths, **ORed**, and the order between them is immaterial and is not a
precedence (compute.py:262-264):

1. **The cost identity** — `_cost_identity_complete(si)` (`compute.py:222`): EV, PV and AC all
   **exactly equal** to a positive BAC, at 100 per cent complete. **Exact equality, no tolerance**
   (compute.py:146-149): *"A tolerance would be a threshold this run invented… A project one pound
   short of budget is not Complete here."*
2. **The commissioning register** — `commissioning_clearance(si)` (`compute.py:286`), reading the
   **`commissioningClearance`** structure (`COMMISSIONING_CLEARANCE_CONTRACT`, compute.py:266):
   `commissioning_items_total` and `commissioning_items_cleared`. Both must be present, whole,
   the total positive, and `0 <= cleared <= total` (lines 300-306). **Every item cleared →
   Complete.** Where some remain, **NOT Complete**, and the reading states **how many remain**
   (lines 320-323). A report stating neither figure returns `None` — which is *not* the same as
   stating that items remain, and the two are never conflated.

`_COMPLETE = "Complete"` (compute.py:149). **It is deliberately NOT a band and is NOT in
`fusion.BAND_SEVERITY`** (compute.py:139-146): it never enters `worst_band` and is never ranked
against Green/Yellow/Amber/Red. `fused_band` is reported beside it either way, so nothing needing
the severity of a completed project's evidence loses it to the promotion.

It sits ahead of the gate **on purpose** (compute.py:131-137): the gate asks *"may an OFFICIAL RISK
POSTURE be issued"*, and completion is not a posture — the work is delivered at budget or it is
not, and no schedule-risk or quality reading can make a finished project unfinished. Behind the
gate, a complete project carrying unassessed categories could never publish Complete.

**Plain answer to the order's question: `Complete` IS published in `project_status`, in place of
the band. It is not a band and does not participate in any banded arithmetic. So it is a status the
platform publishes, and simultaneously a separate state — the banded reading survives alongside it
in `fused_band`, `project_status_basis.project_weighted_sum` and `dempster_band`.**

### 6.4 Every point where a review, hold, disposition or override can change the answer

Between the category postures and the published status, in execution order:

1. **`_weighted_voting_result(category_statuses)`**, `compute.py:511`. Replaces B1.2's row. It
   **cannot** change `project_status` — `category_statuses` is already built and is not rebuilt.
   Structurally ring-fenced.
2. **`delivery_complete(si)`**, `compute.py:614`. The **only** thing that displaces the banded
   status. Two ORed paths; either publishes `Complete`.
3. **The required-core gate**, `compute.py:600, 624`. Can only *withhold* — turn a band into
   `Awaiting analysis`. It cannot improve a band.
4. **`governed_status_semantics(category_statuses, conflict)`**, `compute.py:632` →
   `fusion.py:390`. Renames the rollup and marks conflict not-estimable
   (`NOT_ESTIMABLE_SINGLE_LINEAGE`, `CONFLICT_ESTIMATED`, `fusion.py:385-387`) where all voting
   lineage is one body. Changes the *semantics* published beside the status, not the status.
5. **PM module review**, `documents.py:6017` (`a_projectmodulereview`), `documents.py:6137/6162`
   (`_module_reviews_for`, `latest_module_reviews`), applied inside modules through
   `simulation/pm_review.py`. A6.4 / A4.8's holds run through it: an Amber or Red normalised
   posture, or a lift of two or more bands, is **held from banding** until a PM reviews it. This
   changes a *module's* band, hence a category posture, hence the weighted sum.
6. **The per-module hard overrides** listed in Section 4 — nine of them (A1.6, A1.9, A1.11, A2.1,
   A2.7, A2.8, A2.9, A2.12, A4.2, A4.3, A4.4, A4.5, A4.7, A4.9, A6.1, A6.2, A6.3, plus A3.2's
   exhaustion arm, A3.5's substantial-completion floor and A4.8's trade/stop-work arms). Each
   fires **below** the category, so its effect on the published status is bounded by its category's
   weight — except in A6, where worst-wins means a single Red override sets the whole category
   posture, which then moves the weighted sum by 0.16.
7. **`_redact_module_actions(modules)`**, `documents.py:3898`, and `_result_view(row, ...)`,
   `documents.py:3926`. Read-path presentation controls; they can withhold a module's *action text*
   from a surface. They do not alter the stored status.
8. **`_withdraw_live_result`** (`documents.py:1182`) and the supersede-then-insert dance in
   `_compute_and_store` (`documents.py:3369-3382`). A result can be withdrawn and replaced; the
   partial unique index `uq_computed_results_one_live` over `(project_id, period)
   WHERE superseded_by IS NULL` guarantees at most one live row.
9. **`a_adminrecompute`**, `documents.py:5395`, and **`a_projectcomputeall`**,
   `documents.py:5106`. Re-run the whole path; see Section 7.4 on whether the answer can move.
10. **Document archive / filing control**, `a_projectdocumentarchive` (documents.py:5591) and
    `a_projectdocumentcontrol` (documents.py:5766). Archiving a document removes it from
    `_period_documents`, which changes the evidence base and therefore every downstream reading.
11. **`a_projectdecisionrecord`** (documents.py:5864). A recorded decision. It is stored beside the
    result; nothing in `compute.py` reads it back into the status.

**There is NO project-level override.** `PROJECT_BOUNDARY_WORDS` says so in terms, and
`project_posture` contains no arm that can force a band.

---

## Section 7 — Implicit state and side effects

### 7.1 Environment variables read anywhere on this path

| Variable | Read at | Default | What breaks when absent |
|---|---|---|---|
| `DATABASE_URL` | `settings.py:75` | **none** | `SettingsError`; **the service does not start**. Also normalised: `postgres://` and `postgresql://` → `postgresql+psycopg://` (settings.py:85-88) |
| `SESSION_SECRET` | `settings.py:94` | a per-process `secrets.token_urlsafe(48)` | Service still starts. Sessions stop working across a restart or a second instance; participants are asked to log in again. `session_secret_is_ephemeral()` (settings.py:116) makes it loggable, so it is never a silent downgrade |
| `SESSION_TTL_SECONDS` | `settings.py:101` | `8 * 3600` | Non-integer → `SettingsError` |
| `CORS_ORIGINS` | `settings.py:106` | `""` → empty list | Browser calls from other origins refused |
| `LOG_LEVEL` | `main.py:47` | `"INFO"` | nothing; verbosity only |
| `ANTHROPIC_API_KEY` | `settings.py:112`, `ai_provider.py:186` (via `key_env`) | absent | **`StubExtractor` serves** (and, under `require_real=True`, extraction raises). See 1.4 |
| `OPENAI_API_KEY` | same | absent | same |
| `GROQ_API_KEY` | `ai_provider.PROVIDERS["groq"]["key_env"]` | absent | same |
| `AI_PROVIDER` | `ai_provider.py:196` | `DEFAULT_PROVIDER` (anthropic) | falls back to the default provider |
| `AI_EXTRACTION_PROVIDER` / `AI_SPEC_PROVIDER` / `AI_NARRATION_PROVIDER` / `AI_RECOGNITION_PROVIDER` | `ai_provider.py:209` | the `AI_PROVIDER` value | per-role provider not overridden |
| `AI_<ROLE>_MODEL`, `AI_<PROVIDER>_<ROLE>_MODEL` | `ai_provider.py:219-220` | the provider table's model for that role | the table default is used |
| `AI_<PROVIDER>_BASE_URL` | `ai_provider.py:226` | the table's `base_url` | table default |
| `AI_<PROVIDER>_KEY_ENV` | `ai_provider.py:228` | the table's `key_env` | table default |
| `GOOGLE_CLIENT_ID` | `research_identity.py:321` | `""` | Google sign-in unavailable |
| Drive credential env (`CREDENTIAL_ENV`) | `drive_adapter.py:76` | `""` | Drive adapter inert |
| Drive parent folder (`PARENT_FOLDER_ENV`) | `drive_adapter.py:128` | `DEFAULT_PARENT_FOLDER_ID` | the default folder is used |
| Geocode key (`GOOGLE_KEY_ENV`) | `geocode.py:151` | `""` | geocoding unavailable |
| Maps browser key (`MAPS_BROWSER_KEY_ENV`) | `map_config.py:41` | `""` | map surface degrades |

**No environment variable on this path carries a band cut, a weight or a threshold.** Every
threshold is either a code constant or an entry in `band_reference_data.json`.

### 7.2 Database state the compute path assumes exists

`_compute_and_store` (`documents.py:3369-3467`) assumes, and reads:

* **`document_uploads` for this project and period** — `_period_documents` (documents.py:452),
  which excludes superseded (`_superseded_document_ids`, 336) and archived
  (`_archived_document_ids`, 355) documents and deduplicates by content hash.
* **`document_uploads` for EVERY EARLIER period** — `_identity_observations_before`
  (documents.py:509); see 7.3.
* **A prior `ComputedResult` row**, optionally, as `reuse_cutoff_from` — `_derive_cutoff`
  (documents.py:1313) reuses an earlier row's cutoff so evidence added to the period later cannot
  silently change what the period reports.
* **Cross-period series** assembled in `run_and_store` (documents.py:3473) — this is where
  `spiHistory` (A1.2), the CPI history (A1.5) and the milestone history
  (`_milestone_history`, documents.py:1039; `_milestone_forecast_history`, 1074) come from. A
  first-period project has none of them and those modules abstain naming the history.
* **Project event log** — `_events_as_of(project, cutoff)` (documents.py:1458), attached as
  `si["events"]` at documents.py:3406. Explicitly *not* produced by the pure merge because it is
  not a property of this period's documents.
* **`schedule_activities`, `project_risks`, `project_notices`, observation rows** — the four
  projection stores, written at upload and rewritten here (see 7.4).
* **Structures written by an earlier upload**: none directly. Structures are re-derived from this
  period's live documents every compute. The one genuine cross-upload carry is the identity fields.

### 7.3 The contract-value carry-forward specifically

**Where:** `_identity_observations_before(session, project, period)` —
`server/app/documents.py:509-542`. Called at `documents.py:3404` on the compute path and at
`documents.py:4738` on the `a_extractsignals` path.

**How far back it reaches: ALL THE WAY.** The query is
```
select(DocumentUpload.period).where(DocumentUpload.project_id == project.id,
                                    DocumentUpload.period < period).distinct()
```
— **every earlier period, unbounded.** There is no window and no decay. For each such period it
re-runs `_period_documents`, so supersession and archiving are honoured **per period** (a revision
in period 2 cannot resurrect the document it replaced). **The period being computed is never
re-read here** — reading it twice would put two copies of every observation into one group.

**What is carried:** only observations whose field is in `field_registry.IDENTITY_FIELDS`, which
resolves to **13 fields**: `analogousBac`, `analogousFinalCost`, `analogousOverrunPct`, `bac`,
`baselineContractSum`, `baselineEnd`, `baselineStart`, `costRating`, `originalContingency`,
`overallRating`, `qualityRating`, `revisedContractSum`, `scheduleRating`.

**What happens when no earlier period has one:** `carried` is an empty list. `select_signal_inputs`
then has only this period's observations for that field, so the field resolves from whatever the
current period supplies — or is absent, and every module that needs it abstains naming it. **No
default is substituted and no figure is invented.** The defect this fixes (Run 45, documented at
documents.py:514-521): before it, *"a contract uploaded at period 1 was invisible from period 2 on,
and the contract sum fell through to whatever weaker writer the later period happened to hold."*

`baselineContractSum` and `baselineStart` are **PERMANENT** in `field_registry` (lines 84-85), so
`_perm_pick` takes the **earliest dated** observation and **nothing later ever replaces it**.
`bac`, `baselineEnd` and `revisedContractSum` are SNAPSHOT (lines 87-89), so `_snap_pick` takes the
latest dated within the lowest writer tier.

### 7.4 Where the path writes as well as reads during a compute, and determinism

`_compute_and_store` **writes before it computes** (`documents.py:3391-3396`):

```
_persist_observations(session, project, period)
_persist_schedule_activities(session, project, period)
_persist_project_risks(session, project, period)
_persist_project_notices(session, project, period)
```

All four are the same four written at upload time. They are written again here so a compute
triggered without a fresh upload still runs against a current store.

**Can a second compute on the same data produce a different answer?** From the code, three
properties are in place to make the answer *no*:

1. **The cutoff is reused, not re-derived.** `_derive_cutoff(documents, reuse_cutoff_from)`
   (documents.py:1313) takes an earlier row's cutoff when one is offered, and every selection is
   `as_of <= cutoff`. Evidence added to the period after the first compute cannot silently move it.
2. **The projection stores are written once per period and never rewritten by a later one** —
   documents.py:3393-3395 in terms: *"written once for this period, never rewritten by a later one,
   which is what keeps a recompute of an earlier period byte-identical."*
3. **`select_signal_inputs` is pure** and its tie-breaks are total orders on
   `(tier, dated, as_of, rank, doc_type, sha256)`, so ordering accidents cannot move a selection.

Three ways a second compute **can** differ, all of them legitimate and all visible:

* A **new upload** into the period, computed **without** a reused cutoff — a different document set
  and a later cutoff.
* **An extraction-contract change** (0030). The next upload of the same bytes re-extracts and
  updates the `documents` row **in place**. A recompute then reads a different `extraction` for the
  same sha256. The row's `extraction_contract` records which contract produced it.
* **The recognition step** (`documents.py:3450-3462`). `recognised_structures(...)` calls a model.
  With no key it recognises nothing and writes the diagnosis into `si["recognitionLog"]`; with a
  key it is a live model call and **is not guaranteed to return the same label twice**. It is
  `setdefault` and last in the chain, so it can only fill a key nothing else supplied — but on that
  key it is the one non-deterministic input on the whole path. The value is read out of the
  evidence store by the identifier the platform offered, never from the model's answer, so a model
  cannot put a *figure* into a reading — only a *choice of label*.

Also: `run_and_store` writes the `ComputedResult` row, and `_withdraw_live_result`
(documents.py:1182) marks the outgoing row superseded **before** the new one is inserted, because
`uq_computed_results_one_live` would correctly refuse two live rows during the flush. ULIDs are
generated in Python precisely so an id can be known before its row exists.

### 7.5 Fields the platform writes that no rendered surface reads

Measured, not asserted. Method: collect every `band_*` key written anywhere under
`server/app/simulation/`, then test membership against (a) the concatenated text of every
`assets/**/*.js`, `assets/**/*.html` and root `*.html`, and (b) the concatenated text of every
`server/app/*.py` outside `simulation/`. The browser surfaces read specific named keys — the only
`Object.keys` on a module row is `detail.js:2496`, a count — so there is no generic key dump that
would rescue an unread field.

**44 `band_*` keys are written. NOT ONE of them appears in any browser surface.** Ten are read by a
server module outside `simulation/` (`band_asserted`, `band_basis`, `band_basis_provenance_class`,
`band_boundary`, `band_boundary_provenance_class`, `band_boundary_provenance_words`,
`band_provenance_class`, `band_provenance_words`, `band_source`, `band_withheld_reason`).

**The remaining 34 reach no rendered surface and no server reader outside the simulation package:**

`band_aggregation_rule`, `band_aggregation_words`, `band_basis_id`, `band_boundary_if_reviewed`,
`band_boundary_provenance_by_edge`, `band_boundary_provenance_classes`, `band_components`,
`band_components_assessed`, `band_components_not_assessed`, `band_direction_note`,
`band_dominance_margin_cap`, `band_exhaustion_arm_fired`, `band_first_review_pct`,
`band_from_rate`, `band_governing_item_id`, `band_governing_period`, `band_governing_rules`,
**`band_hard_override_evaluable`**, **`band_hard_override_fired`**, `band_item_postures`,
`band_items_not_assessed`, `band_override_conditions`, `band_override_fields_absent`,
`band_override_fired`, `band_override_words`, `band_overrides_evaluated`,
`band_owner_inserted_edge`, `band_posture_before_override`, `band_primary_before_cap`,
`band_provenance_split_note`, `band_rate_pct`, `band_rules`, `band_rules_not_evaluable`,
`band_source_limit`.

Plus **`module_state_words`** (`models_cat89.py:1139`, `models_doc.py:1659`, `models_doc.py:1817`,
`pm_review.py:208, 215`) — confirmed still in that state, as Run 121 found; zero hits in any `.js`
or `.html` in the repository.

**This matters beyond tidiness.** `band_hard_override_fired`, `band_hard_override_evaluable`,
`band_override_fields_absent` and `band_overrides_evaluated` are precisely the fields the code
writes so that a reader can tell *"the override was tested and did not fire"* from *"the override
was never evaluable"* — a distinction the code goes to considerable trouble to preserve at nine
different modules. **No participant-facing surface renders that distinction.** The stored row
carries it; the dashboard does not show it.

Note the scope limit: this measurement covers `band_*` keys and `module_state_words`. There may be
other unread fields with different naming; establishing that exhaustively would need a full key
census of every module row shape against every surface, which this run did not do — named in
Section 8.

### 7.6 Fixtures named, per the order's Method 3

**No census number in this report was taken from a fixture.** Every count here was derived by
executing the code in-process:

* 31 modules — `registry.service_index()`.
* 16 `_ASSEMBLER_FIELDS` entries — `len(information_completeness._ASSEMBLER_FIELDS)`.
* 13 `IDENTITY_FIELDS` — `sorted(field_registry.IDENTITY_FIELDS)`.
* 5 weighted categories, weights, and their sum — `project_posture.PROJECT_CATEGORY_WEIGHTS` and
  the module's own executable assert.
* 44 / 10 / 34 `band_*` keys — the regex-and-membership script described in 7.5, run against the
  working tree at `65bedfb`.
* 10 `DISABLED_MODULES`, 2 `CORE_VOTING_MODULES` — `registry.DISABLED_MODULES`,
  `registry.CORE_VOTING_MODULES`.

I did not run either census driver, so this report does not compare against them and does not
conclude any regression from them.

---

## Section 8 — Where the trace could not be completed

Named gaps. None is filled from an earlier report.

1. **`_baseline_structures`' exact field reads.** I established its two output keys
   (`timePhasedBaseline`, `expenditureBaseline`), its early `return {}` at documents.py:1568, and
   that neither `time_phased_schedule` nor `schedule_of_values` has an `_ASSEMBLER_FIELDS` entry.
   I did **not** read lines 1569-1641 field by field, so the exact extraction key names it reads
   are not stated. Budget.

2. **The degraded-vs-`None` line for eleven of the `_run69_structures` branches.** I established
   the general pattern (no driving table → key never written) and read the two branches that
   genuinely degrade in full. For `resourceProfile`, `productionOutputRecord`,
   `environmentalRequirementRegister`, `lookAheadSchedule`, `overheadAllocationBase`,
   `scheduleNetwork`, `projectCalendar`, `ncrExposureRecord`, `submittalDecisionRegister`,
   `subcontractorAssessments` and the three change-order structures, I did not read each guard
   individually, so I cannot state per-branch which specific scalar makes it return nothing versus
   which lets it assemble degraded. The order asked for that distinction and I have it only for
   `qualityRequirementRegister` and `procurementItems`.

3. **`_TCPI_STABILITY_MARGIN` and `_VAC_STABILITY_CPI` numeric values.** A1.7's Amber edge is
   `1.00 + _TCPI_STABILITY_MARGIN` and A1.8's is `(1 - 1/_VAC_STABILITY_CPI) * 100`. I located
   `_TCPI_PLANNED_EFFICIENCY = 1.00` (models_evm.py:580), `_TCPI_OWNER_YELLOW = 1.05` (601) and
   `_VAC_BUDGET_MET_PCT = 0.0` (765), and derived `_VAC_OWNER_YELLOW_PCT = -5.2631578…` from the
   source comment at line 793. **I did not read the two stability constants' own values.** Per the
   standing rule, I do not reconstruct them: the Amber edge of A1.7 and A1.8 is stated here as the
   expression, not as a number.

4. **A6.2, A6.3 and A6.4's runner-side abstention arms.** Their cuts are fully established from
   `band_reference_data.json` and from `_a6_band`'s dispatch (`models_cat89.py:389-401`), and A6.1's
   arm I read in full at `models_cat89.py:418-490`. I read only the dispatch, not the bodies, of
   `_band_safety`, `_band_environmental` and `_band_contractor`, so the exact guard that makes each
   withhold rather than abstain is stated from the shared factory's behaviour rather than from each
   function's own lines.

5. **Whether A2.7's `milestone_slip_ratio_bands` entry is live.** The JSON configures
   0.02/0.05/0.10, with a `hard_override`. The runner at `models_ext.py:352` loads
   `critical_path_control_bands` instead and bands through `hybrid_schedule_slip_band`. I could not
   establish from the code whether `milestone_slip_ratio_bands` is read anywhere on the served path
   or is a configured-but-orphaned entry. **This is a real candidate for a stale threshold and I am
   not guessing which.** Same question, unresolved, for `pert_criticality_bands` (0.2/0.5/0.8)
   against A2.1, which bands on `pert_path_concentration_bands`.

6. **Section 4.2 by removal-and-recompute.** The order's Method 2 asks for reachability
   established by removing an input, re-running assembly and compute, and seeing whether the result
   moves — as Runs 110 and 112 did. **I did not do that.** I established reachability by resolving
   every runner in-process, invoking each with an empty `si`, and reading each function's own source
   for its structure and scalar arms. That is stronger than grep and weaker than an end-to-end
   removal experiment. The four scalar-fallback modules named in 4.2 are read out of the code's own
   two-arm structure, not out of a moved result. Building an upload-through-compute fixture would
   have needed either a recorded stub corpus keyed by sha256 (none was available to me) or a real
   model key (there is none). **This is the single largest gap in the run.**

7. **A complete unread-field census.** Section 7.5 covers `band_*` and `module_state_words` only.
   A full census — every key on every module row shape, every key on `project_status_basis`, every
   key on each structure, against every rendering surface — was not attempted.

8. **`hybrid_schedule_slip_band` and `hybrid_band_words`.** Used by A2.7 and A2.12. I read the
   thirteen configured values in `critical_path_control_bands` and the JSON's `worst_of` note
   ("the MOST SEVERE of four applicable results"), but I did not read the function itself, so
   **which four rules those are, and how each maps to a cut, is not established here.**

9. **`_evidence_qualification` / Category-9 gate.** `documents.py:3259` writes
   `si["evidenceQualification"]`, and `compute.py` stores "the Category-9 gate's verdict on every
   vote… what was allowed, degraded, abstained or rejected and why". **A vote can apparently be
   DEGRADED by that gate**, which would be a further point in the Section 6.4 list. I did not trace
   `qualification_gate.py` / `qualified_evidence.py`, so I cannot say whether degradation changes a
   band, drops a vote, or only annotates it.

10. **`spec_projection.py`.** It calls the same `project_posture` and `delivery_complete`, so the
    two paths cannot drift on those two. I did not trace the rest of it, so any *other* way a
    specification projection reaches a published status is not covered.

---

## 9. Verification block

* **Starting commit:** `65bedfbca838ca1b456318dda504cc89e5b14f6e`
* **`git status --porcelain` before commit:** `?? REPORT_2026-09-03_dependency_thread.md` — the
  report and nothing else.
* **Tree clean of production changes:** yes. No file under `server/app/`, `server/alembic/`,
  `server/tools/`, `specifications/`, or `server/tests/` was modified, added or removed.
  `server/app/simulation/` untouched.
* **Migration head unchanged:** `0033_recognition_matches.py`. No migration written, none run.
* **`SIMULATION_VERSION` unchanged:** `"sim-2026.09-v64"`, `models.py:1001`.
  `SIMULATION_VERSION_HISTORY` not appended to.
* **`T6_HANDOFF.md`:** read (top block) and **not modified**. Nothing in this run's findings makes
  its top block stale — it correctly declares itself non-authoritative.
* **No key printed, no key committed.** No model call made, none simulated.
* **`git add` by explicit path only.** No `git add -A`, no `git add .`.
* **Not pushed.** The owner verifies and pushes.
* **Ending commit:** the commit created by this run, containing this file alone.
