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
