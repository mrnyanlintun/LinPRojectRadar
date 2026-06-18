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
