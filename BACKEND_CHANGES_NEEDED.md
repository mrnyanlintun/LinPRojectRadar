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
