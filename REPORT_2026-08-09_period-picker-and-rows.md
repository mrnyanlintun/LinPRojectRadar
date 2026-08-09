# The calendar period picker, the recommendation reading documents, and the dead rows

**Date:** 2026-08-09
**Branch:** `claude/period-recompute-new-docs-1nfjnx`, restarted from `origin/main` at `25113d3`
(its previous pull request was already merged, so it could not carry new work)
**Model:** Opus

**Verification:** server suite **52 suites, 2826/2826**, fresh migrated SQLite per test file (the
new `test_period_picker_and_evidence.py` adds 126). `tests.html` **51/51**. `tests_render.html`
**220/221**, twelve net new checks, the one red being the pre-existing auth-gated "production
read path" row that is red on unmodified `origin/main` too. Real headless-Chromium drives of the
picker (14/14), the diagram, the card, and the map. Four faults injected, each confirmed applied
by hash, each detected, each reverted with the hash matching the original.

**No migration was added.** Unapplied in production, unchanged: **0020, 0021, 0022, 0023.** No
`DATABASE_URL` pointed anywhere but throwaway SQLite. Production was neither inspected nor
queried. **Nothing under `server/app/simulation/` was modified.**

---

## LEAD: does the calendar picker work end to end? Yes, now. It did not, and not for the reason
## it looked like.

**The owner is right that it did not work, and the cause was not the period control at all.**

Commit `fe72b1b` (the previous session) removed the duplicate create-project card from
`index.html`. It left `wireProjectsPanel()` in `workspace.js` reaching for `ws-create-btn`, an
element that no longer exists. `boot()` calls that function FIRST:

```js
wireProjectsPanel();   // threw: Cannot read properties of null (reading 'addEventListener')
wireUploadPanel();     // never ran
wireDocumentsPanel();  // never ran
wireDetailPanel();     // never ran
await refreshProjects();  // never ran
renderPortfolio();        // never ran
```

Measured in a browser on `origin/main` before any change, on the Workspace project page:

```
upload_project_options: 0
docs_project_options:   0
detail_project_options: 0
portfolio_rows:         0
```

**Every project picker on that page was empty and every control beside them was unwired**,
including the reporting-period controls on the Period documents panel. There was no project to
select, so there was nothing the period control could do. That is what "it does not work" was.

Fixed two ways, because one was not enough: the dead wiring is guarded, and `boot()` now wires
each panel independently inside its own try/catch that reports to the console, so a single
missing element can never again silently unwire the page. After the fix, same drive, same page:
`1 / 1 / 1` options and no page errors.

**Separately, the control was a number spinner, not a calendar.** It now is one.

### How the calendar produces both the number and the date

The platform holds a period NUMBER and a stated period ENDING DATE (`DocumentUpload.period_end`).
It also holds `ComputedResult.period_cutoff`, which is a different thing and stays derived from
the period's own evidence dates; the model's own note says so, and it was not touched.

The person picks the ending date. The number is derived from it by ONE function,
`documents.period_for_end_date`, whose rule is:

> The period is the earliest one whose stated ending date falls on or after the date you picked.
> If the date is later than every stated ending date, it opens the next period.

That function has exactly two callers: the new read-only `projectperiodfordate` action, which
previews the answer in the dialog before anything is uploaded, and `_resolve_period` at the
upload itself. **The client sends only the date.** There is no number for it to get wrong and no
second copy of the rule to disagree with the one that files the document. Each answer carries a
`basis` sentence, so a derived number is never unexplained.

`_resolve_period` change is purely additive: an explicit `period` is still honoured (every
existing caller and suite is unaffected), and the research-derived period still overrides
everything on a study project. The preview says so rather than showing a number the upload would
then ignore.

**No date, no upload.** The dropzone refuses rather than defaulting to period one, which is how a
second period's documents used to land silently in the first.

### Driven in a real browser, on a fresh database, 14/14

```
PASS  the period control is a calendar date input  [date]
PASS  the number spinner is gone
PASS  no date picked: the upload is refused, loudly
PASS  and nothing was posted to the server
PASS  a date matching period 1's end reads as EXISTING period 1
      [Period 1 - period 1 is the period stated as ending 2026-03-31]
PASS  a later date reads as NEW period 2
      [Period 2 (new) - period 2 is new: 2026-04-30 is later than 2026-03-31, the last
       period's stated ending date]
PASS  a date inside period 1's window reads as period 1
      [Period 1 - period 1 ends 2026-03-31, the first period ending on or after 2026-03-10]
PASS  the client sent ONLY the date, no period number
      [{"period": null, "period_end": "2026-04-30", "fileName": "P2_0.pdf"}, ...]
      DOCS PER PERIOD: {'1': 1, '2': 2, '3': 0}
PASS  period 1 still holds only its own document
PASS  the calendar-picked documents landed in PERIOD 2
PASS  the project now reports TWO periods
PASS  period 2 computed from its own two documents
PASS  no page errors during the whole drive
```

**Picked by calendar, filed to that period, computed as that period.**

---

## Every string key mismatch found across all surfaces

The sweep for this class was completed in the previous session and is already on `main`
(`REPORT_2026-08-09_document-rows.md`, commit `facc0ec`). Restated here in full because this
brief asks for it, with the current status of each:

| # | File | What was keyed | Live/dead | Status |
|---|------|-----------------|-----------|--------|
| 1 | `neural_flow.js` `DOC_KEYS[7]` | `'rfi'` - retired, not in `DOC_TYPES` | Live, row permanently dark | **Fixed** (row removed; `rfi_log` already had its own correct row) |
| 2 | `neural_flow.js` `DOC_KEYS[8]` | `'submittal'` - renamed `submittal_register` | Live, row permanently dark | **Fixed** (repointed) |
| 3 | `signals.js` `DOC_TYPE_GROUPS` | `'rfi'`, `'submittal'` in the upload dropdown | Live: offered two types the server can never classify into | **Fixed** |
| 4 | `simulations.js` `sourceWeights` | `'rfi': 0.65, 'submittal': 0.65` | Live but low impact: unknown types fall back to `0.50`, so the intended weights were silently not applied | **Fixed** |
| 5 | `app.js:1607` `categoryLedgerHtml` | `cat.id === "cat9"` | Live: `LIN_CATEGORIES` has no `cat9`, so the Governance row never auto-opened | **Fixed** to `"b3"` |
| 6 | `server/app/simulation/models_dq.py:96` | same stale dict, server-side | Live, same shape as #4 | **Not fixed - `server/app/simulation/` is off limits.** Still outstanding. |
| 7 | `detail.js:296` `buildModuleAxes` | `cat.id === "cat8"` | Dead: the function is never called | Not fixed, dead code |
| 8 | `decision.js` `CATEGORY_ACTIONS` | `cat1..cat11` | Dead: both call sites commented unreachable | Not fixed, owner decision pending |

Checked clean: `export.js`, `store.js`, `admin-ops.js`, `workspace.js`, `files.js`, `config.js`,
`jdrive_tree.py`, `documents.py`. `knowledge.js:104`'s `"rfi"`/`"submittal"` are search keywords,
not type lookups.

After the fix, `neural_flow.js`'s `DOC_KEYS` is **exactly** the current 27-type `DOC_TYPES` set,
asserted by equality rather than by absence of the two known-bad strings, so a future rename
fails a check instead of killing a row. The dropdown is exactly `DOC_TYPES + UI_ONLY_DOC_TYPES`.

**#6 is the one live instance still outstanding**, and it needs someone who may edit
`server/app/simulation/`.

### The rows, confirmed in a browser on this branch

```
LIT ROWS: Monthly Progress Report, Submittal Register, OAC Meeting Minutes,
          Procurement Log, Correspondence / Notice, RFI Log (register)
NOT-APPLICABLE (blue) ROWS: Past Performance Report, Historical Project Data,
                            Test & Commissioning Report

PASS  27 document rows render
PASS  the uploaded RFI log LIGHTS the RFI row
PASS  the uploaded submittal register LIGHTS its row
PASS  no row keyed on the retired individual RFI type
PASS  the three deliberately-absent types read as not applicable, not as no data
```

**Schedule of Values.** `CLASSIFY_HINTS` had no clause for it at all: the audit's finding was a
genuine zero, not a wrong hint. It now carries a clause naming its structure against a sharpened
pay-application clause, written to say what is present in one and absent in the other:

> "pay application has contract sum, amount paid to date and a billing period, and is a numbered
> request for payment; a schedule of values breaks the contract sum into line items, each with
> its own scheduled value and percent or amount complete, and unlike a pay application carries no
> amount paid and no billing period"

**The design-engagement wording: the classifier did not recognise it, and now does.** The only
RFI clause was "an RFI log lists requests for information with totals" - nothing tied "design
query" or "owner decision" to `rfi_log`, which is how Project 1 names the document. Extended to:

> "an RFI log lists requests for information with totals, whatever it is titled - a document
> titled a design query log or an owner decision log records the same request, response and
> decision content and is the same type"

Both are deterministically pinned, with a self-test proving the pin can fail. **Neither can be
verified against a real model here**: no `ANTHROPIC_API_KEY` and no sample document exist in this
environment. That remains a key-and-documents-gated step.

**The three absent types could not be derived and the code says so.** Modules carry a `sectors`
list that `getModuleStatus()` reads to return NA; document types carry no equivalent field
anywhere in the data model, and `documents._EXPECTED_DOC_TYPES` names a different, unrelated four
types. So `DOC_NOT_APPLICABLE` is a documented hardcoded list, presented as an editorial decision
rather than a computed one.

---

## What the recommendation can now establish from documents that it could not from signals

**The scores were never about any project.** `expected_regret` is `{monitor: 11, investigate: 5,
escalate: 8}` on every project and every period, because the payoff matrix and the future
probabilities are literals with no input dependence. Those three numbers were printed twice per
card: once per course under "What it costs", and once in the recommendation. **They are no longer
printed at all.**

Per the brief, no replacement scoring was invented. A fresh weighting built out of document
counts would be the same defect in new clothes: a number that looks like a finding and is really
a choice nobody made. `document_evidence.ranking` is a refusal carrying its reason, and the card
prints the reason.

**What replaces them is what the documents say.** New `server/app/document_evidence.py` reads the
period's LIVE documents (superseded revisions already excluded) at display time and reports what
their stored extractions support. Served on `projectresults` beside `signal_inputs`, ungated,
because it is evidence and a participant forms a preliminary judgment from evidence.

The brief named four things the signals reduce away. Three are now established as figures, and
the fourth is honestly refused:

| The brief asked for | Established from | Field |
|---|---|---|
| an open dispute | OAC meeting minutes | `subcontractor_disputes` |
| a procurement position | procurement log | `delayed`, `at_risk` |
| an unresolved scope item | RFI log, NCR log, OAC minutes | `rfi_open`, `rfi_overdue`, `oldest_open_days`, `ncr_open`, `outstanding_action_items` |
| **a notice served** | **the notice is reported as present; its content is NOT established** | `correspondence_notice` stores only `document_risk_score` and `document_date` |

**Why the fourth cannot be done and is not faked.** `extraction_client` keeps only the field list
each type declares and drops every other key the model returns. For `correspondence_notice` and
`risk_register` that list is a risk score and a date. So a notice in the period is a fact the
platform holds; what the notice SAYS is not. The card names the document and says the content is
not established, rather than omitting it, because a card that silently drops a served notice is
worse than one that admits it did not read it. The suite asserts those two types genuinely store
nothing more, so if extraction ever grows a content field this claim turns red rather than
staying quietly stale.

Fifteen findings across nine document types, every one keyed on a field
`extraction_fields._EXTRACTION_FIELDS` actually declares (asserted, so a rename fails a check
rather than silently reporting nothing forever). A zero count is not a finding; the document is
still listed as read, so its silence is visible as silence.

### The rendered recommendation, quoted, for a real project

Project "Terminal C Apron Rehabilitation", period 2 ending 2026-04-30, six documents uploaded and
computed. Read back out of the DOM after `LinApp.renderDecisionCard`:

> **The courses below are not ranked.** The scores the analysis holds are the same for every
> project and every reporting period, so they say nothing about this one. What decides the
> recommendation is stated with it, and what this period's documents say is set out below.
>
> [... the three courses, each with what it costs, forecloses and protects ...]
>
> **What this period's documents say**
>
> These are read from the documents uploaded for this period, not from the computed figures.
> Each statement names the document it came from.
>
> - 11 requests for information are still open  *Read from RFI and Design Query Log April 2026.pdf.*
> - 4 requests for information are overdue  *Read from RFI and Design Query Log April 2026.pdf.*
> - the oldest open request for information has been open 47 days  *Read from RFI and Design Query Log April 2026.pdf.*
> - 6 submittals were rejected  *Read from Submittal Register April 2026.pdf.*
> - 2 procurement items are delayed  *Read from Procurement Log April 2026.pdf.*
> - 2 procurement items are at risk  *Read from Procurement Log April 2026.pdf.*
> - 1 subcontractor dispute was recorded in the meeting  *Read from OAC Meeting Minutes 2026-04-22.pdf.*
> - 7 action items from the meeting are outstanding  *Read from OAC Meeting Minutes 2026-04-22.pdf.*
> - 3 safety actions are open  *Read from OAC Meeting Minutes 2026-04-22.pdf.*
> - This period contains correspondence or a notice. Its content is not stored, so what it says
>   is not established here.  *Notice of Delay 2026-04-18.pdf.*
>
> **Recommended: Escalate to management review**
>
> The stored courses carry the same three scores on every project and every reporting period,
> because the table they come from does not read any project input. They rank nothing about this
> project, so no ranking is shown. The recommendation is not taken from the scores. This period's
> cost performance at 0.84 and schedule performance at 0.85 are below 0.88, and the analysis
> escalates whenever either figure falls below 0.88, whatever the ranking says. Against this
> period's evidence, cost performance stands at 0.84 and schedule performance at 0.851.

Every numeric token in that block is a stored value: `0.84`, `0.85`, `0.851`, `0.88`,
`15,748,571`, `31.2` from the row; `11`, `4`, `47`, `6`, `2`, `2`, `1`, `7`, `3` from named
documents. **`5`, `8` and `30` no longer appear**, and they are off the suite's figure allowlist
so their reappearance anywhere in the block now fails a check.

### The third surface

Operational and research share `recommendation_options.js` and both get this. **Training does
not, and cannot**: `training_engine.build_options` is a separate server-side generator over a
simulated run whose `source_documents` is deliberately empty, so there are no documents to read.
That is a property of training, not a gap in this change, but it does mean "all three surfaces"
is true of display-time generation and not of document evidence.

---

## The street map: no, it does not render streets here, and the blocker is named

**Driven in a real browser, not inferred.** The map is in the lazily-initialised Location section;
firing `lin:section-opened` for `d-globe` mounts it. Observed, before the fix:

```
maplibreCanvas: true, 400x300
containerClass: maplibregl-canvas-container maplibregl-interactive ...
NETWORK: https://tiles.openfreemap.org/styles/dark  ->  net::ERR_TUNNEL_CONNECTION_FAILED
```

The vendored library (`assets/vendor/maplibre-gl.min.js`, same-origin, 791 KB) loads and
instantiates fine. The single remote host, `tiles.openfreemap.org`, is refused at CONNECT by the
container's egress proxy with HTTP 403 (a policy denial; the proxy's own log records
`connect_rejected`). The style JSON is the FIRST request and it fails, so no tile URL is ever
resolved and no tile is ever requested. Control hosts through the same proxy succeed, so the
proxy works and the denial is host-specific. `demotiles.maplibre.org` is equally blocked.
`index.html`'s CSP allows only `tiles.openfreemap.org`, so no substitute host would work either.

**Verdict: streets cannot render in this container. This says nothing about the deployed site.**

**What the owner must open to confirm.** The deployed Render URL, signed in, a project that has
coordinates (the seeded fixture uses 1600 Pennsylvania Ave NW), project detail page, expand the
**Location** section. Streets render if `https://tiles.openfreemap.org/styles/dark` is reachable
from the browser. To check the host alone without the app, open
`https://tiles.openfreemap.org/styles/dark` directly: a JSON style document means reachable, a
connection error or 403 means the same block exists there.

### One thing was fixed, because the code promised it and did not do it

`detail.js` says the map degrades to the outline "if MapLibre is absent, **or its tiles cannot be
reached**". Only the first half was true. The tile half ran through `m.on("error", function () {})`
and then returned, so an unreachable tile host left the reader with MapLibre's empty background
under a note reading "Matched to: 1600 Pennsylvania Ave NW" - a blank panel claiming success.

An error before `load` now means there is no basemap and never will be, so it degrades to the
atlas and says so. Errors after `load` are transient tile failures on a map the reader can
already see, and are still swallowed exactly as before. Observed after the fix, same drive:

```
maplibreCanvas: false
atlasSvg:       true
note: "The street map could not be reached, so this is the outline view.
       Matched to: 1600 Pennsylvania Ave NW, Washington, DC"
```

**Note for the next session driving this in a browser here:** the detail map will now show the
atlas outline, not a MapLibre canvas, because the tile host is always blocked in this container.
A drive asserting `.maplibregl-canvas` is present will fail, and that is the fix working.

---

## Tests that went red, and which kind each was

Three checks in `tests_render.html` group 15 went red. Per the standing warning, each was
classified before being touched:

1. **`"the stored score for escalating is quoted exactly"`** - asserted
   `"worst case of this course at 8 out of 30"` was present. **Recorded the defect.** Replaced.
2. **`"and it still quotes the stored score rather than hiding it"`** - asserted
   `"It scores 8 out of 30"` was present; its name says it was written to keep the constant on
   screen. **Recorded the defect.** Replaced.
3. **`"the fixed scores are named as a property of the method"`** - **protected a real property,
   and caught a real bug in my change.** My first draft gated the "not ranked" explanation on the
   server having attached `document_evidence`, so a read without it dropped both the scores and
   the reason they were absent, telling the reader less than either. The refusal is now
   unconditional, because the scores are constants on every read. The check passes again on its
   original merit.

Replacing 1 and 2, the property they were reaching for is kept and inverted: a figure that says
nothing about this project must not be printed as though it did, and its absence must be
explained rather than silent. `5`, `8` and `30` came off the figure allowlist, so the scan that
already existed now fails if any of them reappears anywhere in the block.

## Faults injected, each confirmed applied and reverted by hash

| Fault | Detected by | Result |
|---|---|---|
| Drop the filename guard so unattributed findings print | 2 checks | `"a finding with no document to name is DROPPED"` and the figure scan (stray `9`) |
| Put the constant score back into a course's cost | 2 checks | figure scan (strays `11 \| 30 \| 5 \| 30 \| 8 \| 30`) and `"no course quotes the fixed score"` |
| `_resolve_period` stops deriving from the date | 7 checks | including `upload=1 preview=2`, the exact defect signature |
| Plant `"escalate to management review"` in a findings sentence | section 6 | see below |

**The leak-scanner claim was measured, not assumed, and the first version of it was wrong.** I
wrote in a comment that `test_decision_ui_t4.py`'s prose scanner holds the pre-lock evidence to
account. It does not: with the planted advice sentence in place that suite stayed green at 73/73,
because it scans the decision-state endpoint and this block is served from `projectresults`. The
comment was corrected to say so, and section 6 of the new suite now scans every sentence the
findings table can generate, at both singular and plural counts, and is proven able to fail on
exactly the fault T4 missed.

## Not changed

- No fee-basis vocabulary anywhere.
- No extraction field, no module input, no `field_registry.py`.
- `ComputedResult.period_cutoff` stays derived from evidence dates, per the model's own note.
- `server/app/simulation/` untouched, so mismatch #6 above is still live.

## Two pre-existing display artifacts, found and left alone

- `recommendation_basis._fmt` rounds to two places, so a schedule performance of 0.879 prints as
  "0.88 ... below 0.88", which reads as self-contradictory at the threshold boundary. The
  substance is right; the rounding makes it look wrong.
- The same sentence's trailing evidence clause prints raw `si.spi` (`0.851`) beside the rounded
  `0.85`, so one figure appears at two precisions in one paragraph.

Both are in wording this task did not own. Worth a small follow-up.
