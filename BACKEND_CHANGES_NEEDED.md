# Backend (`Code.gs`) changes needed — Sprint 0 items 15, 16, 18

`Code.gs` lives only in the Apps Script project (not in this repo), so the items
below are **front-end-ready but require a matching backend update**. The client
already sends/handles everything described here; the backend just needs to
persist and return it.

---

## Item 16 — Spec reference in audit output (`audit_()`)

**Goal:** the audit results `Citation` column should read like
`SECTION 03 30 00, p.4, ¶2.1` (MasterFormat section · page · paragraph).

**Change:** in `audit_()`, update the OpenAI prompt so each returned line item's
`citation` field is requested in that exact format. Add to the system/user
instructions something like:

> For every line item, populate `citation` as
> `"SECTION <NN NN NN>, p.<page>, ¶<paragraph>"` using the MasterFormat section
> number, the page number, and the paragraph reference from the corpus document
> the finding is based on. If a component is unknown, omit it (e.g.
> `"SECTION 03 30 00, p.4"`). Never invent a section/page/paragraph.

No schema change is required — `items[].citation` is already returned and the
front end already renders it in the Citation column.

---

## Item 18 — Project-specific requirements store (`requirements_db.json`)

**Goal:** after corpus PDFs are ingested, maintain a per-project
`requirements_db.json` in the project's `_corpus` folder, keyed by MasterFormat
section.

**Change:** in `ingestCorpus_()`, after the file is stored successfully:

1. Extract the document text (the client now also sends a `masterFormatSections`
   array on the `ingestcorpus` POST body — see below — but the backend should
   also parse from its own extracted text as the source of truth).
2. Detect MasterFormat sections (`/SECTION\s+\d{2}\s+\d{2}\s+\d{2}[\s\w\-]*/gi`).
3. Build / merge a JSON object:
   ```json
   {
     "SECTION 03 30 00": [{ "page": 4, "content": "…clause text…" }],
     "SECTION 07 92 00": [{ "page": 9, "content": "…" }]
   }
   ```
4. Save / update it as `requirements_db.json` in the `_corpus` folder.
5. Return the detected section list on the `ingestCorpus_` response, e.g.
   `{ ok:true, file:{…}, masterFormatSections:[ "SECTION 03 30 00 - CONCRETE", … ] }`.

**Also (Item 15 persistence):** include `masterFormatSections` (and/or `sections`)
on each file returned by `listcorpus`, so the section tags survive a page reload.
The front end already:
- detects sections client-side from the PDF (PDF.js) and sends them as
  `masterFormatSections` on the `ingestcorpus` POST,
- renders `file.masterFormatSections` / `file.sections` as tags on the corpus
  list (falling back to a local in-session cache when the backend omits them).

---

## Client POST shape already sent (for reference)

`ingestcorpus` POST body now includes (when a PDF yields sections):
```json
{
  "action": "ingestcorpus",
  "id": "<projectId>",
  "name": "<file name>",
  "docType": "<doctype>",
  "mimeType": "<mime>",
  "dataBase64": "<base64>",
  "masterFormatSections": ["SECTION 03 30 00 - CONCRETE", "..."]
}
```

No other backend actions need changes for these items.

---

## Fix 1 — Simulation results + events persisted in project.json (`save_()`)

**Context:** The frontend already calls `LinStore.saveProject(project)` after every simulation run. The saved payload now includes two new fields:

- `project.simulationSignals` — full simulation output with enriched metadata:
  ```json
  {
    "signal_metadata": {
      "project_id": "SYN-01",
      "run_at": "2025-10-15T14:32:00.000Z",
      "reporting_period": "2025-10",
      "data_date": "2025-10-15",
      "signal_inputs_snapshot": { "cpi": 0.92, "spi": 0.88, "bac": 5000000 }
    },
    "signal_array": [ ... ]
  }
  ```
- `project.events` — append-only audit trail array. Each simulation run appends:
  ```json
  {
    "event": "simulation_run",
    "at": "2025-10-15T14:32:00.000Z",
    "modules": [{ "method": "PERT", "status": "amber" }, ...],
    "worst_status": "amber"
  }
  ```

**Required backend change:** `save_()` must persist both `simulationSignals` and `events` as top-level fields in `project.json`. If `save_()` already writes the entire received project object, no change is needed — confirm and test. If it only writes a whitelist of fields, add `simulationSignals` and `events` to that whitelist.

---

## Fix 2 — Save audit result to Drive (`saveauditresult` — new action)

**New POST action:** `saveauditresult`

**Trigger:** After every successful audit run the frontend fires (non-fatally):
```json
{
  "action": "saveauditresult",
  "id": "<projectId>",
  "auditData": {
    "audit_id": "audit_1729000320000",
    "run_at": "2025-10-15T14:32:00.000Z",
    "submittal_file": "submittal-concrete-mix.pdf",
    "overall_verdict": "Approved as Noted",
    "items": [ ... ],
    "summary": { ... }
  }
}
```

**Required backend changes:**

1. **`saveauditresult_(body)`** — new handler:
   - Locate the project folder for `body.id`
   - Create or get sub-folder `_audits/`
   - Write `body.auditData` as JSON to `audit_<timestamp>.json`
   - Append an audit event to `project.events` in `project.json`:
     ```json
     { "event": "audit_saved", "at": "<run_at>", "audit_id": "<audit_id>", "verdict": "<overall_verdict>" }
     ```
   - Return `{ ok: true, audit_id: "<audit_id>" }`

2. **`audit_()` — also save automatically** — after returning results to the client, call `saveauditresult_()` internally so the record is persisted even if the client-side save fires (double-save is idempotent if both use the same `audit_id`).

---

## Fix 3 — List audit results with full item data (`listauditresults`)

**Current behaviour (assumed):** `listauditresults` returns only metadata (filename, date).

**Required change:** Return the full audit payload for each past result so the frontend can render the audit table inline and offer XLSX re-export without a re-run. Updated response shape:

```json
{
  "ok": true,
  "results": [
    {
      "audit_id": "audit_1729000320000",
      "name": "audit_1729000320000.json",
      "run_at": "2025-10-15T14:32:00.000Z",
      "submittal_file": "submittal-concrete-mix.pdf",
      "overall_verdict": "Approved as Noted",
      "items": [ ... ],
      "summary": { ... }
    }
  ]
}
```

If returning full items is too large for the list call, add a separate `GET ?action=getauditresult&id=<projectId>&auditId=<auditId>` endpoint instead. The frontend currently uses a client-side localStorage cache for items fetched in-session; the Drive-backed retrieval is the fallback for results fetched on a fresh page load.

---

## Fix 4 — Lin chat system context: final module reorder + PM-facing language

**Context:** The Lin chat assistant's system prompt lives in `Code.gs` (not in
this repo). Two things changed and must be propagated there: (a) the module
numbering was finalised — Conservative Dominance (formerly Module 10) is now
Module 09, ABM Governance (formerly Module 09) is now Module 19 and is the LAST
module in the stack, and old Modules 11–19 each shifted down by one to become
Modules 10–18; (b) Lin should use PM-facing confidence-band language when
answering questions about a project's classification.

**Required backend changes:**

1. **Module count and final numbering.** The platform has **19 signal modules**.
   The final numbering is:

   - 01 Monte Carlo EAC Forecast
   - 02 CUSUM Anomaly Monitor
   - 03 Document Risk Extraction
   - 04 PERT Network Criticality
   - 05 Line of Balance Production Velocity
   - 06 CCPM Buffer Health
   - 07 Reference Class Forecasting
   - 08 DSM Rework Propagation
   - **09 Conservative Dominance (Signal Synthesis)** — was Module 10
   - 10 Dempster-Shafer — was Module 11
   - 11 Rough Sets — was Module 12
   - 12 Neutrosophic Logic — was Module 13
   - 13 Interval-valued Fuzzy Sets — was Module 14
   - 14 Z-numbers — was Module 15
   - 15 Probabilistic Linguistic Term Sets (PLTS) — was Module 16
   - 16 Plithogenic Sets — was Module 17
   - 17 Belief Rule Base (BRB) — was Module 18
   - 18 Quantum Probability — was Module 19
   - **19 ABM Governance Layer** — was Module 09 (now LAST, the decision output)

2. **Tier description.** Insert the following verbatim into the Lin chat
   system/context prompt:

   > The platform has 19 signal modules organised in five tiers. Modules 01–03
   > are quantitative EVM inputs (Monte Carlo EAC, CUSUM, Document Risk).
   > Modules 04–08 are extended construction and design simulations (PERT, Line
   > of Balance, CCPM, Reference Class Forecasting, DSM). Module 09 is
   > Conservative Dominance — the baseline synthesis where the worst single
   > signal class drives the state. Modules 10–18 are nine independent
   > evidence-combination and uncertainty-reasoning methods that cross-check
   > Module 09 (Dempster-Shafer, Rough Sets, Neutrosophic Logic, Interval-valued
   > Fuzzy Sets, Z-numbers, PLTS, Plithogenic Sets, Belief Rule Base, Quantum
   > Probability). Module 19 is the ABM Governance Layer — the LAST module —
   > which consumes the Module 09 baseline and the Modules 10–18 cross-checks
   > and produces the recorded governance decision card with named authority,
   > recommended action, required documentation, and fairness gate state.

3. **PM-facing language.** When answering questions about a project's
   classification, Lin should use the confidence band derived from how many of
   Modules 10–18 agree with the Module 09 baseline:

   - **8 or 9 of 9 agree → HIGH CONFIDENCE.** Phrasing examples:
     - Green: "All signal methods agree this project is on track. Routine
       monitoring is appropriate."
     - Amber: "Multiple methods flag this project as needing attention. The
       signals are consistent — a weekly review with the controls lead is
       recommended before the next reporting cycle."
     - Red: "The project requires escalation. All evidence methods confirm the
       classification. A recovery plan review with the program director is
       required within 48 hours."
   - **5–7 of 9 agree → MODERATE CONFIDENCE.** Act on the Module 19
     recommendation but document the uncertainty explicitly.
   - **Fewer than 5 of 9 agree → LOW CONFIDENCE.** Phrasing: "The classification
     is [state] but the signal methods disagree. [Specific reason]. Investigate
     the discrepancy before recording a formal governance action."
   - **Destructive quantum interference (M18) present.** Phrasing: "The signals
     are genuinely contradictory. The governance layer recommends [action] but
     the evidence base is divided — document the uncertainty explicitly."

No client change is required for this fix — the modules already compute and
render client-side under the new numbering (`simulations.js`, `deepdive.js`,
`modules.js`, `knowledge.js`). This note only tracks the matching backend prompt
update.

---

## Fix 5 - Project history snapshots and signal source change log

**Context:** the frontend now stores a `project.history` array after each full
19-module run. Each snapshot contains:

- `period` and `computed_at`
- `signal_inputs`
- `signal_inputs_with_history` for BAC, EV, AC, PV, CPI, and SPI
- `module_results` for Modules 01-19
- `governance` output from the Module 19 decision card

**Required backend changes:**

1. **`save_()` persistence:** confirm `save_()` writes the entire received
   project object. If it uses a field whitelist, add `history`, `signals`,
   `simulationSignals`, and `signalInputs.sources`. The `history` array must be
   preserved exactly as sent by the client.

2. **New GET action:** add `GET ?action=gethistory&id=XX`, returning:
   ```json
   { "ok": true, "history": [ "...snapshots..." ] }
   ```
   Read the array from `project.json.history`; return an empty array when no
   history exists.

3. **Snapshot retention:** the client retains a maximum of 24 periods per
   project. The backend should not expand this or duplicate same-period entries.

4. **Sources array format:** preserve `signalInputs.sources[field]` as an array
   of change-log entries. Do not flatten it back to a single object. Each entry
   has:
   ```json
   {
     "value": 24900000,
     "docType": "contract_value",
     "fileName": "contract.pdf",
     "at": "2026-06-17T09:15:00.000Z",
     "reason": null
   }
   ```

5. **Manual overrides:** in `overwriteSignal_()`, append a source-log entry for
   the overridden field with `docType: "manual_override"`, `fileName: null`, the
   current timestamp, and the PM-provided reason (or `"Manual override by PM"`).

---

## Fix 6 - Lin chat system prompt: executive-brief mode

**Context:** the Project Detail page now generates a 4-6 sentence executive
brief from the 19-module signal package by POSTing a structured prompt to
`?action=chat`. The frontend prompt already carries the rules, but the Lin
system prompt should be updated to reinforce them so the response style is
consistent across reporting periods.

**Required system-prompt additions for `action=chat`:**

When the prompt asks for an "executive brief for a program director", Lin must:

- Write as if briefing a senior official before a governance meeting.
- 4-6 sentences maximum.
- Lead with the overall health state in plain English.
- Name the single most important concern.
- State the recommended action and who takes it.
- Note the confidence level (do the 19 methods agree or disagree?).
- Never mention module numbers (no "Module 09", "M10", "DST", etc).
- Never read out metric values (no "CPI 0.92", no "P80 EAC +7%").
- No bullet points, no headers, no preamble.

**Persistence:** the client also writes the generated brief to
`project.executiveBrief = { text, generated_at, period }`. `save_()` already
persists the whole project; confirm it does not whitelist this field out.

---


---

## Fix 7 - Preserve the stored 19-module log on `save_()`

**Context:** the frontend now writes a rich `module_log` array (M01..M19, one
entry per module) onto every `project.history[].snapshot`. The executive brief
generates from THAT stored log — not from recomputed live signals. If the
backend `save_()` strips `history` (or its nested `module_log` / `evidence_agreement`
fields), the brief reverts to "Run signal extraction first" on every reload.

**Required backend behaviour:**

1. **Preserve `history` verbatim.** `save_()` must write `project.history` to
   `project.json` without filtering, reshaping, or dropping fields. Each
   snapshot now carries:
   - `period`, `computed_at`, `project_id`, `project_name`, `sector`
   - `signal_inputs` (bac, ev, ac, pv, cpi, spi, doc_risk_score)
   - `module_log[]` (M01-M19 per-module entries with status, tier, metrics)
   - `total_modules`
   - `governance` (state, conflict, authority, action, fairness_gate)
   - `evidence_agreement` (methods_checked, methods_agreeing, confidence)

2. **Max 24 periods retained.** Front end enforces this before save — back
   end does not need to expand it but must not duplicate same-period entries.

3. **No whitelist trimming.** If `save_()` uses a field allow-list, add
   `history`, `signals`, `simulationSignals`, `signalInputs.sources`, and
   `executiveBrief` to it. Dropping any of these silently regresses the
   brief / spider / audit-trail flows.

4. **The executive brief is generated from this stored log**, not recomputed
   signals. The brief prompt the client sends to `action=chat` references
   `snapshot.module_log` line-by-line — keeping the stored log intact is what
   makes the brief reproducible across reporting periods.
## Fix 8 - History endpoint + chat-with-snapshot

The frontend now persists a rich category snapshot per reporting period on
`project.history`. It is the audit-trail artefact that drives the spider web,
the signal ledger, the Signals page, and the executive brief.

**Required backend endpoints:**

1. **POST `?action=savehistory`** — body `{ id, snapshot: { ...full snapshot... } }`.
   - Save to `_history/<period>_snapshot.json` inside the project folder.
   - Append `{ event: "snapshot_saved", period, at }` to `project.events`.
   - Return `{ ok: true, period, snapshot_id }`.
   - Idempotent on `period` — re-saving the same period replaces the file.

2. **GET `?action=gethistory&id=<id>`** — already exists in spec from Fix 5; behaviour now extended:
   - Read every JSON file in `_history/` and return them sorted by `period` ascending.
   - Return `{ ok: true, history: [ ... ] }`.

3. **POST `?action=chat` (updated)** — body may now include an optional `snapshot` field:
   - If `snapshot` is present, use `snapshot.summary` (plus `snapshot.categories` rollups) as the project context for the prompt, instead of reading `project.json` from Drive.
   - This keeps the brief grounded in the stored computational log instead of refetching live signals and reduces Drive reads to one write per period.
   - Snapshot context shape: `{ categories, summary, governance }`.

**Snapshot field reference (must be persisted verbatim):**

```
period, computed_at, project_id, project_name, sector,
signal_inputs { bac, ev, ac, pv, cpi, spi, doc_risk_score,
                baseline_start, baseline_end },
categories { cat1..cat9: { id, num, name, status, parked, modules[] } },
summary { total_modules, by_status, by_category, evidence_agreement {
          methods_checked, methods_agreeing, confidence } },
governance { state, conflict, authority, action, documentation, fairness_gate },
executive_brief
```

**Retention:** the front end keeps at most 24 periods; the back end stores everything written and never deletes.

## Fix 9 - 11 new document types + full-89 signalInputs merge

The frontend dropdown (`signals.js` → `DOC_TYPE_GROUPS`, new "Compliance &
Performance Documents" optgroup) now offers 11 additional document types. The
Stage-2 simulation modules (`simulations.js` → `LinSimulations.runAll`) read
their inputs straight off `signalInputs`, so `extractsignals` must extract the
new fields and `Code.gs` `extractionFieldsFor_()` must handle these doc types:

- `safety_report`: osha_recordable_incidents, total_manhours, incident_rate, report_period
- `quality_audit_report`: total_findings, critical_findings, deficiency_count, audit_score, audit_date
- `environmental_report`: permit_conditions_total, violations, compliance_rate, report_date
- `ncr_log`: ncr_issued, ncr_closed, ncr_open, ncr_overdue, report_period
- `subcontractor_report`: scheduled_deliveries, on_time_deliveries, compliance_score
- `procurement_log`: long_lead_items_total, on_schedule, at_risk, delayed, report_date
- `lookahead_schedule`: activities_planned, activities_constrained, constraint_rate, lookahead_weeks
- `resource_report`: planned_labor_hours, actual_labor_hours, planned_equipment_days, actual_equipment_days
- `cost_report`: indirect_cost_plan, indirect_cost_actual, material_cost_baseline, material_cost_current
- `past_performance_report`: overall_rating, schedule_rating, cost_rating, quality_rating
- `historical_data`: analogous_overrun_pct, analogous_project_type, completion_year
- `field_report` (update): add weather_days_lost, float_remaining to existing fields

**Also merge these into `signalInputs`** (camelCase keys the frontend modules read):

- rfiCount, rfiPeriodDays (from rfi docs — count ingested RFIs)
- submittalsTotal, submittalsRejected (from submittal docs)
- changeOrderCount, baselineContractSum, revisedContractSum (from change_order docs)
- totalFloat, consumedFloat (from time_phased_schedule)
- originalContingency, remainingContingency (from pay_application)
- oshaIncidentRate, totalManhours (from safety_report)
- qualityAuditScore, totalFindings (from quality_audit_report)
- environmentalComplianceRate (from environmental_report)
- ncrIssued, ncrClosed, ncrOpen (from ncr_log)
- subcontractorComplianceScore (from subcontractor_report)
- longLeadItemsTotal, longLeadAtRisk, longLeadDelayed (from procurement_log)
- activitiesPlanned, activitiesConstrained (from lookahead_schedule)
- plannedLaborHours, actualLaborHours (from resource_report)
- indirectCostPlan, indirectCostActual, materialCostBaseline, materialCostCurrent (from cost_report)
- overallRating, scheduleRating, costRating (from past_performance_report)
- analogousOverrunPct (from historical_data)
- weatherDaysLost, floatRemaining (from field_report)

These feed the 15 currently-inactive modules (Cat 2.7-2.9, 3.4-3.6, 3.8, 3.10,
4.4-4.5, 4.8-4.9, 9.6-9.9). Until the backend supplies them, those modules
return the standard `insufficient_data` stub and are excluded from the
spider / ensemble counts — no fabricated statuses.

---

## Fix 10 — Diagnose a project missing from the portfolio (`listProjects_()` logging + `testProject07`)

**Symptom:** project 07 exists in Drive (`Lin Project Radar/07/project.json`,
modified June 17) but does not appear on the portfolio page. Most likely
`?action=list` is **silently skipping** that folder because reading or parsing
its `project.json` throws (malformed JSON, or a field that trips parsing), and
`listProjects_()` swallows the per-folder error.

These are **backend-only diagnostics** — paste into `Code.gs` in the Apps Script
editor. They don't change behaviour, they just make the failure visible in the
execution log (View → Executions / `Logger.log`).

### 1. Log per-folder read failures instead of swallowing them

In `listProjects_()`, wherever each project folder is read via
`readProjectJson_(folder)`, wrap it so a failure logs the **folder name and the
error** and is then skipped (so one bad project can't break the whole list):

```javascript
function listProjects_() {
  var root = getRootFolder_();              // existing helper — Lin Project Radar root
  var folders = root.getFolders();
  var projects = [];
  var skipped = [];

  while (folders.hasNext()) {
    var folder = folders.next();
    var name = folder.getName();
    // Skip non-project folders (e.g. _corpus) exactly as the current code does.
    if (name.charAt(0) === '_') continue;

    try {
      var p = readProjectJson_(folder);     // existing helper
      if (p) {
        projects.push(p);
      } else {
        skipped.push(name + ' (readProjectJson_ returned null/empty)');
        Logger.log('listProjects_: SKIP folder "%s" — no parseable project.json', name);
      }
    } catch (err) {
      // Previously this folder was silently dropped. Log it loudly instead.
      skipped.push(name + ' (' + err + ')');
      Logger.log('listProjects_: ERROR reading folder "%s" — %s', name, err);
    }
  }

  if (skipped.length) {
    Logger.log('listProjects_: %s folder(s) skipped: %s', skipped.length, skipped.join('; '));
  }
  Logger.log('listProjects_: returning %s project(s)', projects.length);
  return projects;
}
```

> Adapt the iteration/helper names to your actual `Code.gs` — the key change is
> the `try/catch` around `readProjectJson_(folder)` that logs
> `folder.getName()` + the error, plus the summary `skipped`/count logs.

### 2. `testProject07()` — read and log project 07's JSON directly

Run this from the Apps Script editor (Run → `testProject07`, then check
View → Executions) to see exactly what is in `07/project.json` and whether it
parses:

```javascript
function testProject07() {
  var root = getRootFolder_();              // existing helper
  var folders = root.getFoldersByName('07');
  if (!folders.hasNext()) {
    Logger.log('testProject07: no folder named "07" under the root');
    return;
  }
  var folder = folders.next();
  Logger.log('testProject07: folder id=%s name=%s', folder.getId(), folder.getName());

  var files = folder.getFilesByName('project.json');
  if (!files.hasNext()) {
    Logger.log('testProject07: folder "07" has no project.json');
    return;
  }
  var file = files.next();
  var raw = file.getBlob().getDataAsString();
  Logger.log('testProject07: project.json is %s chars, last modified %s',
             raw.length, file.getLastUpdated());
  Logger.log('testProject07: raw (first 1000 chars):\n%s', raw.slice(0, 1000));

  try {
    var p = JSON.parse(raw);
    Logger.log('testProject07: PARSED OK — id=%s, name=%s, archived=%s, keys=%s',
               p.id, p.name, p.archived, Object.keys(p).join(','));
  } catch (err) {
    Logger.log('testProject07: JSON.parse FAILED — %s', err);
  }

  // Also exercise the real read path so we see what listProjects_ would get.
  try {
    var viaHelper = readProjectJson_(folder);
    Logger.log('testProject07: readProjectJson_ returned %s',
               viaHelper ? JSON.stringify(viaHelper).slice(0, 500) : '(null/empty)');
  } catch (err2) {
    Logger.log('testProject07: readProjectJson_ THREW — %s', err2);
  }
}
```

**What to look for in the execution log:**

- `JSON.parse FAILED` → the file is malformed; the logged raw text shows where.
- `archived=true` → it's not missing, it was archived (the frontend now warns
  when archived projects exist — see `store.js` `load()`).
- `readProjectJson_ THREW` but `JSON.parse OK` → the helper trips on a specific
  field (e.g. an unexpected type); the error message names it.

---

## Fix 11 — `POST portfolioanalyze` (Cat 8 ML/AI) — already implemented in Code.gs v10.17

**Status:** implemented in `Code.gs` **v10.17** and deployed. Documented here so
the frontend↔backend contract is recorded in-repo.

**What the frontend does** (`signals.js` → `runPortfolioAnalysis`, called from
`runModels()` immediately after `runAll()`/`runDST()` and before the snapshot is
built):

1. Builds a `portfolio` array of signal vectors from every loaded project (plus
   the current one) that has `signalInputs.cpi`:
   ```json
   { "id": "06", "cpi": 0.82, "spi": 0.84, "docRiskScore": 0.55, "actualPctComplete": 42 }
   ```
2. If fewer than 2 projects have signal data, it does **not** call the backend —
   it fills the 5 Cat 8 modules with `insufficient_data` stubs client-side.
3. Otherwise it POSTs (CORS-safe `text/plain` body, same as every other action):
   ```json
   { "action": "portfolioanalyze", "id": "<project id>",
     "portfolio": [ …vectors… ], "history": [ …project.history… ] }
   ```

**Expected response shape** (what the frontend parses):

```json
{
  "ok": true,
  "results": {
    "Isolation_Forest":      { "method_class": "Isolation_Forest",      "status_color": "Amber", "evidence_metric": "Mahalanobis distance 2.1σ from portfolio centroid" },
    "Portfolio_Outlier":     { "method_class": "Portfolio_Outlier",     "status_color": "Red",   "evidence_metric": "Bottom 12th percentile CPI & SPI" },
    "Trajectory_Classifier": { "method_class": "Trajectory_Classifier", "status_color": "Amber", "evidence_metric": "Declining CPI over 3 periods" },
    "Cross_Project_Pattern": { "method_class": "Cross_Project_Pattern", "status_color": "Green", "evidence_metric": "No matching distress cluster" },
    "Anomaly_Score":         { "method_class": "Anomaly_Score",         "status_color": "Amber", "evidence_metric": "Composite anomaly index 64%" }
  }
}
```

- Each entry must carry `method_class` and `status_color` (Green/Amber/Red/null).
  `evidence_metric` is shown in the spider-web tooltip. The frontend converts
  `results` (object) to an array and merges it into
  `simulationSignals.signal_array`, where `getModuleStatus()` reads it like any
  other Cat 8 module.
- For not-enough-data, return either `{ "ok": true, "insufficient_data": true,
  "message": "…" }` or `{ "ok": false, "message": "…" }`; the frontend renders
  the 5 modules as no-data with the message in the tooltip.

**Contract summary:**
- Called after `runAll()` completes (once per signal extraction run).
- Returns the 5 Cat 8 module results.
- Requires the `portfolio` array to contain **at least 2** projects with signal
  data (the frontend short-circuits below that and never calls the endpoint).

---

## Fix 12 — `chat` action must honour `max_tokens` (longer executive brief)

The executive brief was restructured into a longer **4-section** format (Overall
Status · Category Analysis · Conclusion · Recommendations). The frontend now
sends a `max_tokens` hint on the brief's chat call:

```json
{ "action": "chat", "question": "…structured brief prompt…", "id": "06", "max_tokens": 1200 }
```

**Change in `Code.gs`:** in the `chat` action handler, read `max_tokens` from the
request body and pass it through to the OpenAI/Groq call, clamped to a sane range,
defaulting to the current value when absent:

```javascript
// inside the chat action handler, before the model call
var maxTokens = Number(body.max_tokens) || 400;
maxTokens = Math.max(200, Math.min(2000, maxTokens));
// …pass maxTokens as the max_tokens / max_completion_tokens parameter…
```

Without this, the model truncates the brief mid-Recommendations. (The repo's
reference `backend/main.py` `/chat` already does this clamp — mirror it in
`Code.gs`, which is the production backend.) Other `chat` callers omit
`max_tokens` and keep the 400 default, so nothing else changes.

---

## Fix 13 — Derived signalInputs + new extraction fields (Code.gs v10.18)

The frontend now **derives** ~15 extended signalInputs from the figures we
already extract (BAC, AC, CPI, SPI, doc-risk, RFI, %-complete) using
industry-standard ratios — see `signals.js` `deriveExtendedFields()`. Each
derived value is tagged in `si.sources[key] = { docType: 'derived', … }` and the
UI shows an `[est.]` badge; the modules note "estimated" in their evidence
metric. This activates ~14 previously-inactive modules (Cat 2.8, 3.5, 3.6, 3.10,
4.5, 4.8, 9.6, 9.7, 9.8 plus richer 3.3 / 4.2 / 4.3 / 4.6 / 9.5) from the
existing document set, with no backend change required for the estimates.

To **replace estimates with exact figures**, `Code.gs` v10.18 should extract the
real values where the documents contain them. In particular, **OAC minutes**
should additionally extract:

```
case 'oac_minutes': extract additionally:
  - subcontractor_issues_discussed   (count of subcontractor issues raised)
  - outstanding_action_items         (count of open action items)
  - subcontractor_disputes           (count of dispute items)
  - safety_incidents_discussed
  - environmental_issues_discussed
  - quality_issues_discussed
```

Merge into `signalInputs` (camelCase) as: `subcontractorIssuesDiscussed`,
`outstandingActionItems`, `subcontractorDisputes`, `safetyIncidentsDiscussed`,
`environmentalIssuesDiscussed`, `qualityDeficienciesNoted`. These feed **Cat 4.8**
(subcontractor), **9.7** (safety), and **9.8** (environmental) without requiring
dedicated reports. When a real value is supplied the frontend uses it instead of
the derived estimate (the derivation only fires when the field is absent), and
the `[est.]` badge disappears for that field.

Other useful real values, when present in their source documents:
`materialCostBaseline` / `materialCostCurrent` / `indirectCostPlan` /
`indirectCostActual` (Cost Report), `originalContingency` / `remainingContingency`
(Pay Application), `rfiNumber` / `rfiResponseTimeDays` (RFI log),
`weatherDaysLost` / `floatRemaining` (Field Report), `activitiesPlanned` /
`activitiesConstrained` (Look-Ahead Schedule), `qualityAuditScore`
(Quality Audit), `oshaIncidentRate` (Safety Report), `environmentalComplianceRate`
(Environmental Report), `subcontractorComplianceScore` (Subcontractor report).
