# 2026-08-04 — Real extraction: the wiring, the docx path, and what did not run

**Server 36 suites, 1940/1940 (was 35 suites, 1898/1898). `tests_render.html` 86/86.
`tests.html` 51/51.** Eight faults injected, all detected, all reverted byte-identical, baseline
re-measured after every single fault. Nothing under `server/app/simulation/` touched. No
migration.

---

## 1. LEAD: PART 3 DID NOT RUN. THE MODEL WAS NEVER CALLED.

**Extraction still has never run against a real document.** This report cannot give the
field-by-field comparison the brief asked for, and nothing below should be read as evidence about
what the model returns.

Two independent blockers, both measured rather than assumed:

**1.1 There is no real project document in this environment.** Searched all of `DEng` excluding
`Demo`, and the whole repository. 110 `.docx` files exist and every one is coursework or
literature (assignments, lecture summaries, papers). Zero pay applications, zero earned value
summaries, zero registers, zero construction project-controls documents of any kind. The
repository contains no `.docx`, `.pdf` or `.xlsx` at all; `server/dev_fixtures/` holds three
`.txt` files that `dev_serve.py` writes itself from hardcoded numbers, whose sha256 hashes are the
`StubExtractor`'s own recording keys. Using those would be running the stub against its own
recording.

**1.2 `ANTHROPIC_API_KEY` is not set here.** Measured, not read off a config file:

```
build_extractor()                  -> StubExtractor   (model_id: stub/recorded-v1)
build_extractor(require_real=True) -> ExtractionError: "ANTHROPIC_API_KEY is not set. Refusing
                                      to extract with the stub in an environment that requires
                                      real extraction."
```

The key is set on the Render service and `render.yaml` marks it `sync: false`, so it is
deliberately absent from every tracked file. That is the correct design; it just means the real
path cannot be exercised from this machine.

**This is the same wall the 2026-08-02 session hit** (`REPORT_2026-08-02_real-extraction.md`),
and the brief's premise that the run was merely blocked on the deferred-list entry does not hold:
the wiring was one of three things missing, and the other two are inputs only Lin can supply.

### 1.3 What was built so the run is one command when a key exists

`server/tools/real_extraction_probe.py` — calls the REAL model against given files and prints,
per field, what the model returned, what the document says, and the verdict, then runs both
guards and reports refusals with the causing value. Three properties are deliberate: it
**refuses to run without a key** (`require_real=True`, no stub fallback, verified), it **writes
nothing** to any database, and it runs **the same guards the upload path runs**.

```bash
ANTHROPIC_API_KEY=... PYTHONIOENCODING=utf-8 python tools/real_extraction_probe.py <files...>
```

`--make-fixtures DIR` writes three synthetic documents (a pay application with an AIA-style
continuation sheet, an earned value summary, and an RFI log) with their true values printed
alongside. **They are synthetic.** A run against them exercises the real model but does not
establish behaviour on real project documents, and the tool says so in its own output. The
2026-08-02 session's objection to substituting synthetic documents stands and is recorded here
rather than argued away.

---

## 2. What the deferred list actually contained

`extractsignals` was **the only genuinely stranded action of the eight** — an endpoint that
exists, has its key, and is simply not dispatched. Checked against every action registry in the
application, not assumed:

| Action | Handler anywhere in `server/app`? | Verdict |
|---|---|---|
| `extractsignals` | **Yes** — the whole `a_projectupload` path | **Was stranded. Now dispatched.** |
| `chat` | No | Refusal accurate. Never ported from Apps Script. |
| `analyze` | No | Refusal accurate. |
| `portfolioanalyze` | No | Refusal accurate. |
| `audit` | No | Refusal accurate. |
| `tts` | No | Refusal accurate. |
| `ingestcorpus` | No | Retired name. The live surface is `projectcorpus` in `files.py`, dispatched and gated on the existing `auditor` flag. |
| `identifyonly` | No handler, **but the capability exists and is reachable** | Left deferred **deliberately**. |

**`identifyonly` is the one worth knowing about.** Unlike the rest, what it names is not missing:
`AnthropicExtractor.classify_with_confidence` runs on every upload, and the type and confidence
come back on the `projectupload` / `extractsignals` response. Wiring the standalone action would
add a second model call per document for an answer the upload already returns. It is deferred by
choice, and the reason now sits next to it in `writes.py` so the next session does not "fix" it.

**A trap for whoever reads `features.py` next.** `chat`, `portfolioanalyze` and `audit` all have
feature flags (`chat`, `health_dialog`, `auditor`). A flag makes an action look implemented from
the frontend. It gates a feature; it does not supply one. That is most likely why `chat` was
reported as stranded previously — it is not.

**No action is registered in two registries**, verified by set comparison across all twelve.

### 2.1 The dispatch order is what made the entry unreachable, not just wrong

`facade.py` consults the identity/document/workspace registries **before** `DEFERRED_AI_ACTIONS`.
So registering `extractsignals` in `DOCUMENT_ACTIONS` is sufficient on its own; the deferred entry
was removed because leaving it would be a false statement, not because it would still fire.

---

## 3. The docx defect, measured

`extraction_client._content_block` sent PDFs as a `document` block and decoded **everything else**
as UTF-8 text, truncated at 12000 characters. A `.docx` is a ZIP archive, so it took that second
branch. Measured on a real 19,583-byte Word file:

```
block type : text
text length: 12015     (the cap, reached inside the archive)
U+FFFD     : 5071      replacement characters
first bytes: 'PK\x03\x04 ... word/_rels/document.xml.rels ...'
```

The model was shown ZIP local-file headers and deflate-compressed bytes. **The 12000-character
truncation was consumed by the archive's own structure before the document body was reached at
all**, so no amount of model capability could have recovered a figure from it.

### 3.1 How table structure was preserved

`server/app/docx_text.py`, stdlib only — `zipfile` plus `xml.etree.ElementTree`. **No new pinned
dependency**, which matches the standing reason `extraction_client` uses `urllib` rather than the
anthropic SDK. (`python-docx` is not in `requirements.txt` and is not in the server virtualenv;
it was never a candidate.)

Tables are rendered as **pipe-delimited grids with the header row marked**, in document order
with the surrounding prose:

```
| Item | Description of Work | Scheduled Value | Work Completed This Period | Total Completed and Stored to Date | % (G/C) | Balance to Finish |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | General Conditions | 450,000.00 | 37,500.00 | 337,500.00 | 75.0 | 112,500.00 |
| GRAND TOTAL |  | 4,600,000.00 | 342,000.00 | 3,040,000.00 | 66.1 | 1,560,000.00 |
```

Four decisions carry the structure, each with a check that fails without it:

- **`w:gridSpan` is expanded.** A merged "GRAND TOTAL" cell spanning two grid columns is emitted
  once and the remainder padded. Without this every figure in that row shifts one column left and
  4,600,000.00 lands under "Description of Work". The check asserts the grand total sits under
  **"Scheduled Value"** by index, not that the row merely exists.
- **Body order is preserved**, walking the direct children of `w:body`. A figure's meaning often
  depends on the heading immediately above its table.
- **Tracked deletions are excluded.** `w:delText` is not read, so a struck-through superseded
  figure cannot read as current. The fixture carries a deleted `9,999,999.00` decoy.
- **Direct children only** for table rows, so a nested table's rows are not hoisted into the outer
  table with the wrong column count.

The branch is chosen **from the bytes**, tested before the PDF branch. This is not defensive
paranoia: `signals.js` sends `file.type || "application/pdf"`, so a docx the browser did not type
arrives *claiming to be a PDF*. A mime-first test would send the archive as a PDF document block.

**The PDF path is unchanged** and asserted so: a PDF still goes as a `document` block carrying its
original bytes byte-for-byte. The plain-text branch and its 12000-character cap are also
unchanged. The docx branch carries its own larger bound (60000 characters) because that text has
already been parsed and a pay application's summary rows can sit past 12000; **truncation is
announced in the prompt**, never silent.

### 3.2 Read against 110 real Word documents

Not a synthetic-only result. Every `.docx` reachable on this machine:

| | |
|---|---|
| Files | 110 |
| Read without error | **110** |
| Replacement characters, any file | **0** |
| Contained at least one table | 44 |
| Exceeded the 60000-character bound | 6 |
| Parsed to empty text | **1** |

Two things this establishes. The truncation path is a **real condition, not hypothetical** — six
real documents hit it. And the one empty parse is a genuine document class, below.

---

## 4. What breaks on real input

Reported, not repaired, per the brief.

**4.1 An image-only `.docx` cannot be extracted at all.** `Coursera.docx` is 664 KB, six embedded
PNGs, zero tables, and three `w:t` runs that are whitespace. Its content is entirely `w:drawing`
elements. The reader returns empty text and `docx_content_block` **refuses**:

```
DocxReadError: the .docx contains no readable text or tables
```

That refusal is correct — loud refusal over quiet approximation, and it surfaces to the PM through
the existing extraction-failure dialog. But the consequence is real: **a scanned or
screenshot-based Word document is now un-extractable**, where a PDF of the same content would have
gone to the model as a document block and been read. This is a limitation, not a regression (the
previous behaviour was to send ZIP binary, which failed too, but *silently produced a plausible
wrong answer path* rather than refusing). **Not fixed here**: extracting embedded images and
sending them as image blocks is not a small or obviously correct change, and it reopens the OCR
question the docx route was chosen to avoid.

**4.2 The stub does not filter to the declared field list; the real extractor does.**
`AnthropicExtractor.extract_with_confidence` ends with
`{k: v for k, v in extracted.items() if k in set(fields)}`. `StubExtractor` has no such filter and
returns its recording verbatim. So **a stub recording can carry fields the real path would drop**,
and any check written against such a recording asserts behaviour the real extractor does not have.
This bit during this session: a fixture recording `earned_value` for a `pay_application` stored it
happily, and the malformed-numeric guard correctly ignored it, because `earned_value` is not a
pay-application field at all. The fixture was wrong, the code was right, and the failure looked
like a missing guard. **Any future stub recording should use `extraction_fields_for(doc_type)` to
choose its keys.**

**4.3 The guards have still never met a real document.** No refusal can be reported with a real
causing value, because no real document was extracted. What *is* established is that both guards
fire correctly through the new docx path on a constructed case: `completed_to_date` of `"TBD"` on a
pay application is refused whole-document, the field is named, the value is quoted, and **nothing
is stored** (asserted by absence of the `Document` row, not by the response alone). The
`document_risk_score` range guard was not reachable by a natural case here: of the 27 document
types, `submittal_register` is the one whose field list requests it, and no real register document
exists to test.

**4.4 Two upload surfaces now exist and only one is period-aware in the UI.** `signals.js` (the
project detail page's "Upload a Document" panel, via `ingest.renderScopedIngest`) and
`workspace.js` / `files.js` (via `projectupload`). They now share one server path, which is the
point of the adapter, but the legacy panel does not present a period selector and relies on
`_resolve_period`'s default. Worth Lin's decision whether the legacy panel should exist at all;
**not touched here** because the brief asked for the action to be wired, not for a surface to be
retired.

**4.5 A stale dev server on port 8010 was serving different code.** It answered
`Unknown POST action: extractsignals` — neither the old deferred wording nor this change's
handler — so it is running a branch where the action was removed from the deferred set and never
registered. Verification was moved to port 8011 and confirmed to be running this branch before any
harness result was recorded. **Check what is on a port before trusting a harness run against it.**

---

## 5. Verification

### 5.1 Fault injection

Every fault applied, confirmed to change the file, run, detected, reverted, **verified
byte-identical**, and the baseline re-measured **after each one individually**.

| Fault | Detected by | Baseline |
|---|---|---|
| F1 docx branch removed from `_content_block` | docx suite 41 → 16 | restored |
| F2 `extractsignals` unregistered | docx 41 → 31; `test_writes_a1b` 104 → 103 | restored |
| F3 `gridSpan` not expanded | docx 41 → 39 | restored |
| F4 tracked deletions read as current | docx 41 → 40 | restored |
| F5 truncation silent | docx 41 → 40 | restored |
| F6 stub no longer the default without a key | docx 41 → 38 | restored |
| F7 malformed-numeric guard skipped | docx 41 → 37 | restored |
| F8 byte sniffing disabled | docx 41 → 40 | restored |

F8 required strengthening a check first. The "bytes win" assertion originally used the filename
`payapp.docx`, so the extension fallback answered it and the sniff could have been deleted without
the check noticing. It now passes a filename with **no extension** and a lying mime type, so only
the bytes can decide.

### 5.2 The existing check that had to change

`test_writes_a1b.py` asserted the deferred wording for all eight actions and went red on
`extractsignals` — the check correctly noticing the behaviour changed. It now loops over the
seven that are still deferred, **plus a positive control**: without one, deleting
`extractsignals` from `DOCUMENT_ACTIONS` would return it to the deferred set and nothing would
notice, because the loop no longer names it. The control asserts the answer is neither the
deferred sentence nor the unknown-action sentence.

**That same check found a real ordering flaw.** The adapter originally returned
"extractsignals needs either dataBase64 or text" *before* `a_projectupload` ran, so an
unauthenticated caller got a payload critique instead of an auth refusal. The shape check now
happens inside `_decode`, after `resolve_caller` and the PM check. Confirmed live: an
unauthenticated `extractsignals` now answers `not authorized: sign in to make this change`.

### 5.3 The HTML harnesses, and the gap

**`tests.html` 51/51.** Unchanged.

**`tests_render.html` 86/86 — the gap is not 62/63 and never was a defect.** The harness now
carries 86 checks (the training-mode runs added to it since the 69/69 recorded in the handoff).
The gap is entirely environmental, and it moves in three documented steps:

| Condition | Result |
|---|---|
| Bare tab, no session token | 80/81 — the one red is the documented "a session token in this tab" row |
| A **ResearchAdmin** token in `sessionStorage` | 82/83 — unlocks two checks, then fails "a computed project is present" because an admin is not a *member* of any project |
| A **PM** token plus a project uploaded and computed | **86/86** |

**That movement is itself the evidence the group is not vacuous**: the count changes with server
state, so the over-the-wire checks genuinely reach the server rather than asserting against a
primed fixture — the exact failure mode the 2026-08-03 handoff records for the pre-fix harness.

### 5.4 The baseline was wrong for the first hour, and it matters

The first full run reported 5 suites passing and 30 failing. That was **the wrong interpreter** —
the system Python, which has no `fastapi` — not a broken tree. The project's environment is
`server/.venv`. Anyone running these suites must use `server/.venv/Scripts/python.exe` and
`server/.venv/Scripts/alembic.exe`; there is no runner script in the repository and this is the
second session to lose time to it. Each suite is run against a **fresh, uniquely-named** SQLite
file (`rm -f` on a locked SQLite file silently fails on Windows, per the 2026-08-03 handoff).

---

## 6. Open

- **Part 3 remains undone.** It needs a real document set and a key. Nothing else blocks it;
  `real_extraction_probe.py` is ready.
- **Image-only `.docx` is un-extractable** (4.1). Lin's call whether that warrants image blocks.
- **`docRiskScore` range guard is still untested against any real document** (4.3).
- **Whether the legacy `signals.js` upload panel should exist** now that both surfaces share one
  server path (4.4).
- **Stub recordings should be keyed off `extraction_fields_for`** to stop 4.2 recurring.
