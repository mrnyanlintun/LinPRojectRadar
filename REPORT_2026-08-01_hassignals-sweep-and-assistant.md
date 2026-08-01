# The hasSignals sweep, and the assistant

854 checks across 17 suites pass.

You were right that the pattern would exist wherever the old code checked for the blob first. It
did, in **nine** places, and one of them was crashing rather than degrading. The sweep also turned
up two things in the assistant that are worse than stale copy, because they are false statements
about what the platform is.

---

## 1. The sweep: every `hasSignals()` call site, classified

`hasSignals(p)` tests for the legacy client-side blob `p.signals.evm && .cusum && .mc && .doc`. A
project analysed server-side carries a stored `computed_results` row and does **not** necessarily
carry that blob. Nineteen call sites; nine were the bug.

### Fixed: gated on the blob, but read the stored row (or needed nothing)

| Where | What the user saw | What it does now |
|---|---|---|
| `app.js` `statusKey()` | The status legend, all five bands reading 0 | Fixed previously as T12 |
| `app.js` `stateLabel()` | Every project list row labelled "Awaiting ingest" | Asks `deriveHealthState()`, which reads the stored row |
| `app.js` project list colour | Status word rendered uncoloured | Asks `LinResults.hasResult()` |
| `app.js` `renderLedger()` | **Whole signal ledger replaced by "Awaiting ingest"** | Renders; 12 category rows verified |
| `app.js` `renderDecisionCard()` | **Whole governance decision card replaced by "Awaiting ingest"** | Renders; Amber badge verified |
| `detail.js` state badge | The page's top-line "State:" reading "Awaiting ingest" | Asks `deriveHealthState()` |
| `detail.js` `ensembleHtml()` | Ensemble Analysis section silently absent | Renders |
| `detail.js` `wireEnsembleScatter()` | Ensemble scatter silently blank | Renders |
| `assistant.js` `projectAnswer()` / `portfolioAnswer()` | Told the user a project was unanalysed | Reads the stored row |

**`renderLedger` was hiding something worse than a gate.** It built a `rows` array from
`p.signals.evm.cpi`, `.mc.iterations`, `.cusum.drift` and `.doc.score`, and then **never used it**.
The rendered HTML comes entirely from `categoryLedgerHtml()`, which already reads the stored row
through `getModuleStatus` and `getCategoryStatus`. The dead array was the only reason the gate had
to exist: building it threw a `TypeError` the moment `p.signals` was undefined. I removed the dead
code rather than repairing it, since nothing consumed its output.

**`classifyConflict()` would have crashed once the gates were corrected.** It reads
`project.signals.cusum.breached` directly and unguarded, one line below a call to
`signalStatuses()` that carefully guards the same object down to nulls. That was safe only while
every caller gated on `hasSignals()` first. Guarded now, and it returns a new honest value,
**"Signal breakdown not available"**, when there is no per-signal breakdown at all. Falling through
to "Mixed early warning" would have reported a specific finding the platform has no basis for. It
is styled as a neutral abstention, not an alert.

### Left alone: legitimate, and here is why

| Where | Why it is correct |
|---|---|
| `detail.js` `signalWebHtml()` | Genuinely needs `project.simulationSignals.signal_array`, a client-only field. `signals.js` notes "the backend never writes simulationSignals". |
| `deepdive.js` `render()` | The researcher surface that deliberately re-runs the models in the browser. It needs the inputs by design. |
| `ingest.js` (two) | Enables or disables a "Recompute this project" button, which acts on the legacy blob. |
| `signals.js` (two) | Merges freshly built blobs into the cache after a save. Blob-specific by nature. |

`deepdive.js`'s copy still said "Awaiting ingest" and pointed at "Manage Projects", a destination
`COPY_GLOSSARY.md` retired. Rewritten without changing its gate.

---

## 2. The assistant: two false statements, not stale copy

### 2.1 It told the user an AI was broken

`assistant.js` called `LinStore.chat()` on **every** question, displayed "Thinking...", and when
that failed appended:

> (scripted fallback — AI unreachable)

The `chat` action is in `DEFERRED_AI_ACTIONS` and the server answers *"Action not implemented in
this build"* (`facade.py:375`). **The call could never succeed, so that note was shown every single
time.** A director asking a question saw an assistant apologising for a broken AI feature. There is
no AI feature: this assistant is scripted by design, which is exactly what its own file header has
always said. Claiming a temporarily unavailable capability is worse than claiming none.

The scripted answer is now presented as the product, which is what it is. The call is kept, so that
if `chat` is ever implemented its answer arrives here, but the pretence is gone: no "Thinking..."
for a request not expected to return, and no apologetic note.

The note also contained an em dash, in shipped user-facing text.

### 2.2 It could not answer about any current project

`liveAnswer()` matched project codes with `/syn-[a-z]{3}-\d{3}/i`, the retired **SYN-XXX-000** demo
format. The server has issued `PRJ-` plus ten ULID characters since B7b (`workspace.py:46`). So
asking "status of PRJ-D17HNYWDFA" fell straight through to "outside my script". Both shapes match
now, since archived SYN- projects may still exist.

### 2.3 What it does not know

The out-of-scope answer now states the limits as well as the scope:

> I'm a scripted guide, not a model. I match your question against a written knowledge library and
> a few live project and portfolio lookups, and I answer only with what is written there or read
> from the stored server result. I have no access to anything outside this platform, I do not
> browse or fetch, and I cannot answer a question the library does not cover; this is one of those.

`projectAnswer()` now distinguishes **three** states rather than two, and says which it is in. For a
project with a stored result but no legacy blob it gives the status and then says plainly: *"I do
not have the per-signal figures (EVM, Monte Carlo, CUSUM, document risk) for this project."* Those
figures are not in the stored row in that form, so inventing them was the only alternative.

Also corrected: the suggestion chip "What is PCEIF?", the intro naming "PCEIF concepts", and the
out-of-scope line saying "the five signals" when there are **four** signal classes (EVM, Monte
Carlo, CUSUM, document risk).

### 2.4 Rendering defects in the same templates

The templates printed `( sector, period undefined)` for server-created projects, which carry
neither field. Absent fields are now omitted rather than printed as the word `undefined`.

---

## 3. Verified

Measured against a project with a stored result and no legacy blob, which is the exact condition:

```
hasLegacyBlob: false      hasStoredRow: true      fusion: Amber
classifyConflict: "Signal breakdown not available"   (previously: TypeError)
ledger:        rendered, 12 category rows           (previously: "Awaiting ingest")
decision card: rendered, Amber badge                (previously: "Awaiting ingest")
list row:      "Amber", coloured                    (previously: uncoloured "Awaiting ingest")
legend:        Amber=1, Awaiting analysis=1
assistant:     status Red from the stored row, states what it lacks
               no em dash, no "undefined", no false fallback note
```

---

## 4. Not done, and why

The bulk of the content rewrite remains, and it is the part that needs your naming decision applied
across two very large files. I stopped rather than start it with the context left, because doing
half of `knowledge.js` would leave the platform contradicting itself in a new way instead of the
current one.

Outstanding, in the priority order from the inventory report:

1. **`knowledge.js` (324 KB) and `ds_defensibility_data.js` (401 KB).** Roughly 60 user-visible
   PCEIF occurrences, two mutually exclusive expansions of the acronym, the whole "Cat N" title
   scheme, three incompatible category taxonomies, three layer models, a chapter titled "The PCEIF
   Governance Framework", the "How PCEIF Is Accredited" heading, and leftover coursework voice
   ("the course's caveat"). The decision to call it a "decision-support framework" applies here.
2. **The About tab's remaining sections**: the Capabilities table caveats you approved, and the
   corrected computation claims (101 declared / 100 implemented, Groups C **and** D excluded,
   "a rationale field captured").
3. **`README.md`**, which still describes a static client-side Phase 1 app with no backend.
4. **Both export paths**, which carry no notice, attribution or copyright at all.
5. **The em dash sweep** on `index.html`, `auditor.js`, `README.md`.

Two items from the inventory remain open and are not mine to close:

- The **operational notice wording is still drafted, not approved**. It is live for operational
  accounts today because `auth.js:85` sets the class from the login response, while its own comment
  still says it can never display.
- **`ds_defensibility_data.js:3717`** asserts "No capability claims a statistical property it does
  not have", contradicted by its own line 18 listing fourteen label-to-algorithm mismatches.

---

## Regression

854 checks across 17 suites, unchanged.

| Suite | | Suite | |
|---|---|---|---|
| `test_admin_ops_t7t8` | 59/59 | `test_membership` | 46/46 |
| `test_assignment_blinding` | 44/44 | `test_pre_lock_guard` | 20/20 |
| `test_auth_session` | 52/52 | `test_research_identity` | 41/41 |
| `test_decision_sequence` | 60/60 | `test_simulation` | 27/27 |
| `test_decision_ui_t4` | 73/73 | `test_transitions` | 58/58 |
| `test_documents_b7b` | 66/66 | `test_workspace_t3t5` | 50/50 |
| `test_drive_import` | 37/37 | `test_writes_a1b` | 57/57 |
| `test_expert_reference_t6` | 59/59 | `test_export` | 64/64 |
| `test_features` | 41/41 | | |
