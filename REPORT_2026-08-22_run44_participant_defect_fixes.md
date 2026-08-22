# Run 44 — The Participant-Facing Defect Fixes

**Date:** 2026-08-22
**Repository used:** the Linux clone at `/home/user/LinPRojectRadar`. The Windows path
(`C:\Users\NTUN\OneDrive - Arora Engineers, LLC\DEng\LinPRojectRadar`) is not reachable from this
session and was not used.
**Interpreter:** no `.venv` exists in this clone. `server/run_all_suites.sh` falls back to the
`python3` on `PATH` by its own documented fallback (3.11.15), and every figure below came from
that.
**Branch:** `claude/run44-participant-defect-fixes`, built on `604291a`.
**Candidate commit:** `e6889ad`. **Freeze artifacts commit:** `6554dc9`.
**Stamp minted:** `sim-2026.08-v29`. **Participant package minted:** `og-participant-2026.08-v15`.

---

## 0. The outcome, stated first

**189 suites, 14,280 / 14,280, 0 red, 0 aborting.** The successor freeze gate is **32/32** and its
fifteen blocker classes report **0 blocked**. The browser verification is **19/19**. No stop
condition fired.

Four defects Run 43J classified F are repaired, plus one stale docstring. **Every repair is at the
render. Storage was correct in all of them and was not touched.** No server computation moved:
`run_module()` on all 101 registered identifiers is byte-identical to `sim-2026.08-v28` on both a
full and a starved evidence package, proved by executing both lines.

**One invariant was broken deliberately and once**, under the owner's order at section 4.4:
`assets/js/deepdive.js` is one of the six `SEQUENCE_BEARING_FILES`, and this successor moves it.
The gate's B04 blocker and every package record were reconciled to the true bytes with the
exception **named**; nothing was disabled, weakened, widened or bypassed.

**Section 4.6 is report-only and nothing about period scoping was changed.**

---

## 1. `NAMING_AUTHORITY.md`, the sentence fixing group naming, quoted

From `NAMING_AUTHORITY.md` line 96:

> **Never use a module id or number in user-facing text.** No "Cat 4", no "1.7", no "PH.2", no
> "A4.2". Groups and purposes only. The old "Cat N" scheme is retired along with the names.

Every sentence this run wrote for a participant was checked against it. The new Portfolio Health
sentence names no module, no category number and no identifier, and the suite asserts that
directly.

---

## 2. Section 7 item 1 — each fix, what changed, and the evidence it works

### 2.1 Section 4.1 — the false Amber, and what the fix actually is

**What was wrong.** `assets/js/detail.js` carried **two** severity maps, at `:266` and `:1546`,
both keyed on the capitalised spellings only:

```js
const order = { Red: 0, "Red-review": 1, Amber: 2, Yellow: 3, Green: 4, Complete: 5 };
… (order[a.status] != null ? order[a.status] : 3) …
```

The platform does not emit one casing. `A1.2 CUSUM Anomaly Monitor` stores lowercase `'green'`
where every other module stores `'Green'`. A key miss fell through to the unknown default of **3**,
which is *more adverse than Green at 4*, so a module whose only irregularity was its capitalisation
was selected as its category's "worst" ahead of two properly-cased Green ones — and `A1.2` does not
vote, so it contributed nothing to the status it was being offered as the explanation of.

**What changed.** One shared rank, and it is the only ordering on the page:

```js
const STATUS_RANK = { red: 0, "red-review": 1, amber: 2, yellow: 3, green: 4, complete: 5 };
const STATUS_RANK_UNKNOWN = 3;
function statusRank(status) {
  const raw = String(status == null ? "" : status).trim().toLowerCase();
  if (STATUS_RANK[raw] != null) return STATUS_RANK[raw];
  const norm = normalizeStatus(status);            // orange, light-amber, critical, blue
  if (norm && STATUS_RANK[norm.toLowerCase()] != null) return STATUS_RANK[norm.toLowerCase()];
  return STATUS_RANK_UNKNOWN;
}
```

Three properties are deliberate. `Red-review` keeps its own rank between Red and Amber rather than
being folded into Red. An unrecognised value keeps the historical unknown rank of 3, so nothing
outside the vocabulary is silently read as reassuring. And the aliases resolve through the page's
existing `normalizeStatus` rather than being restated, so there is still one vocabulary.

**Requirement 3 needed its own change, at two sites.** Nothing checked that the module offered as
the driver was as adverse as the thing it drove. `c.status` is the server's fusion of the two
voting modules; `c.modules` is every module in service in the category. Both sites now refuse to
name a module better than the severity it would be offered as the driver of, and the expandable
provenance detail says so in words instead of going silent:

> **Modules**: no module in this category reads as adverse as the category status, so none is
> named as driving it. The most adverse of them is CUSUM Anomaly Monitor at Green.

**The evidence it works.** Executed on the shipped bytes and read out of a real browser render:

| what | before this run | after |
|---|---|---|
| `statusRank('green')` vs `statusRank('Green')` | 3 vs 4 | **4 and 4** |
| worst module on Phase J's own list | `CUSUM Anomaly Monitor` (`'green'`) | a module that reads **Green** |
| brief line, Amber category over all-Green modules | `A1 …: Amber (worst: CUSUM Anomaly Monitor)` | `A1 Cost and EVM Performance: Amber` — **no driver named** |
| rendered provenance line, same case (browser) | named a Green module | `Amber, driven by Cost and EVM Performance` |
| rendered provenance line, Amber module present (browser) | — | `Amber, driven by Cost and EVM Performance → CUSUM Anomaly Monitor (1.2)` |

The second and fourth rows are each other's control: the guard suppresses a false attribution and
**not** a true one.

**Stop condition 8.1 was checked and did not fire.** After the fix, can a category still report a
severity worse than its worst computing module? Measured, not assumed:

* **Server.** Every combination of 1, 2 and 3 module bands (84 of them) was pushed through the
  **production route** — `qualify(…, lineage=lineage_for(id))` then `fuse_qualified` then
  `fuse_signals`, which is exactly what `compute.py:118` does — and the fused band is never more
  adverse than the worst band that went in. All 84 entered the combination rather than the
  unresolved-lineage arm; that is asserted separately, because the unresolved arm reports the worst
  input band *by construction* and would have passed the check without testing anything. **This
  corrected a vacuity in my own first draft of the check**, which handed `fuse_signals` a dict of
  the wrong shape and therefore measured a route the application does not take.
* **Client.** `getCategoryStatus` returns `(stored && stored.status) || null` and derives nothing,
  so there is no second place a category status can be manufactured.

### 2.2 Section 4.2 — the document-risk fabrication

`select_signal_inputs` initialises every key to `None`, so a project with no document-risk
observation carries `docRiskScore` **present and null** — the shape `extraction_merge.py:1128`
exists to protect. `Number(null)` is `0` and finite, so `detail.js:1528` rendered it as `"0.00"`
with a Green status and shipped it into the Executive Brief as a key driver, while an *undefined*
score yielded `NaN` and was correctly omitted.

The guard now tests the **raw** value, never the number's truthiness:

```js
const docRaw = (s.doc && s.doc.score != null) ? s.doc.score : si.docRiskScore;
const docScore = (docRaw == null || docRaw === "") ? NaN : Number(docRaw);
```

The empty string is included because `Number("")` is `0` and finite too — the same trap.

**Evidence, executed on the shipped bytes:**

| stored value | key driver produced |
|---|---|
| `null` | **none** |
| absent | none (the case that was already correct, kept as the control) |
| `""` | **none** |
| `0` | `Document risk 0.00`, Green |
| `0.46` | `Document risk 0.46`, Amber |
| legacy blob `doc.score = null` | **none** |
| legacy blob `doc.score = 0` | `0.00` |

The zero and the absence are each other's control: a fix that suppressed both would fail row four.
Confirmed in the browser on the rendered signals panel: absent renders an em dash, a genuine zero
renders `0` with its extracted mark.

### 2.3 Section 4.3 — CPI and SPI labelled "extracted"

`extractedTableHtml` stamped **every** row that carried a value, with no test of whether the field
was read from a document or derived from two that were. CPI and SPI are computed by
`select_signal_inputs` and carry no entry in `signal_inputs.sources`, so they were shown as
extracted with no source to show.

Changed on three surfaces, and nowhere else shows them under an extraction claim:

1. `FIELD_ROWS` gains `computed: true` on the two rows, and the mark reads it: a computed mark with
   its own `.ds-computed` rule in the one stylesheet, so it is distinguishable rather than silently
   unstyled.
2. The panel heading `Extracted signal inputs` becomes `Signal inputs`. It labelled a table that
   now visibly contains both kinds.
3. The upload result line, which begins with the word *extracted*, now reads
   `extracted 5 fields · CPI 1.22 (computed) · SPI 0.96 (computed)`.

**Evidence.** Rendered in a browser: exactly two rows carry the computed mark, each row was checked
individually, and every extracted field still carries the extracted mark:

```
Document-risk score | 0.46 | ✓ extracted | ✎
CPI (computed)      | 1.22 | ✓ computed  |
SPI (computed)      | 0.96 | ✓ computed  |
```

A table with no values marks nothing at all, so neither mark can be read as a value.

### 2.4 Section 4.4 — the false Portfolio Health statement

**The mechanism used, as section 4.4 asks.** The `cat8Retired()` predicate Run 43H wrote and
verified. It is the correct mechanism and it was used, re-derived here rather than copied:

```js
function cat8Retired() {
  const cats = (typeof window !== "undefined" && window.LIN_CATEGORIES) || null;
  if (!Array.isArray(cats) || !cats.length) return false;   // no taxonomy loaded: assert nothing
  const ph = cats.filter((c) => c && c.level === "portfolio");
  if (!ph.length) return false;
  return ph.every((c) => !(c.modules && c.modules.length));
}
```

It is **derived from the taxonomy the page actually loaded**, so reinstating a Portfolio Level
module restores the old sentence with no edit to this file, and a page that has not loaded a
taxonomy claims nothing either way. Proved by execution: **true** with the live taxonomy, **false**
with none loaded, **false** with an empty one, **false** with a taxonomy carrying no
portfolio-level category, and **false** the moment a Portfolio Level module is put back. The live
taxonomy does carry a portfolio-level category with zero modules, so the `true` is not vacuous, and
`live_portfolio_modules()` returns `()` on the server, so the sentence is true of the code and not
merely of the artifact.

**The statement, before:**

> Portfolio Health needs at least 3 projects with computed signals to compare against the
> population: 2 loaded.

**The statement, after** (read verbatim out of the rendered DOM in a browser):

> Portfolio Health is no longer in service. The analysis that compared a project against the rest
> of the portfolio was withdrawn, so this panel does not compute for any portfolio, whatever number
> of projects it holds.

The project-count sentence is **retained** in the code for the case it is true of, rather than
deleted: it is the arm `cat8Retired()` selects against. **No user-facing control was added, moved
or removed** — the flyout's "Rebuild signals (repair)" button and its handler are exactly where
they were, asserted by count in two suites and observed in the browser.

### 2.5 Section 4.5 — the false docstring

`available_modules()`'s docstring at `registry.py:461` said a retired identifier "is refused with
its stated retirement reason rather than computed". Phase F withdrew that refusal. Corrected to
describe what the function does:

> A retired id is unreachable through this list because it is not in service. It is NOT refused
> anywhere: Phase D's retirement-reason refusal was withdrawn at Run 43F section 5.1 (see the note
> in `run_module()` below), so asking `run_module()` for a retired id by name returns exactly what
> it returned at `f461630` — the same result, or the same pre-existing refusal, with the same
> reason in the same words. Retirement is expressed by roster membership and category linkage, and
> nowhere else.

**The function body was not touched**, and the execution proof shows every one of the 101 emitted
rows is byte-identical to v28.

---

## 3. Section 7 item 2 — every status-comparison site the section 4.1 sweep found

Every site in the repository that ranks, orders or compares a status string. **Two were defective;
both are in `detail.js`; both are fixed.** Everything else was already correct, and the reason each
one is correct is stated rather than asserted.

| # | file:site | what it does | verdict |
|---|---|---|---|
| 1 | `detail.js:265` `pickWorstModule` | capitalised-only `order` map | **DEFECTIVE — fixed.** Also **referenced nowhere**: it is defined and never called. Fixed anyway, because a live copy of a broken rule is what a later site gets written from |
| 2 | `detail.js:1546` `buildBriefPrompt` | capitalised-only `order` map, feeds "Per-category worst module" into the brief prompt | **DEFECTIVE — fixed**, and given the requirement-3 guard |
| 3 | `detail.js:794` `PROV_RANK` / `provRank` | ranks through `normalizeStatus` first | already correct; given the requirement-3 guard |
| 4 | `detail.js:97` `normalizeStatus` | lowercases, then matches | already correct |
| 5 | `detail.js:436` `ensembleTally` | buckets through `normalizeStatus` | already correct |
| 6 | `detail.js:534` red-module count | `normalizeStatus(st) === "Red"` | already correct |
| 7 | `detail.js:871` `otherFlags` | `normalizeStatus` then Red/Amber | already correct |
| 8 | `detail.js:1485` `briefCategoryGroups` | lowercases, then substring | already correct |
| 9 | `detail.js:107/235/291` radius maps | all through `normalizeStatus` | already correct |
| 10 | `detail.js:1782` `stKey` | `String(state).toLowerCase()` | already correct |
| 11 | `signals.js:447` `byStatus` tally | lowercases, then substring | already correct |
| 12 | `taxonomy.js:481/539` `getModuleStatus` / `getCategoryStatus` | return the stored value **verbatim**; compare nothing | correct by design, and it is what makes the client unable to manufacture a status |
| 13 | `neural_flow.js:268` `statusFromSig` | lowercases, and also normalises legacy hex colours | already correct |
| 14 | `neural_flow.js:282` `worstStatus` / `STATUS_RANK` | ranks capitalised keys, fed only by `statusFromSig` | already correct |
| 15 | `deepdive.js:2196` `WORST_RANK` / `panelStatusKey` | lowercases the class name first | already correct |
| 16 | `deepdive.js:2356` `statusPillClass` | lowercases, then substring | already correct |
| 17 | `decision.js:98` `normalizeStatusLabel` | lowercases, then matches | already correct |
| 18 | `decision.js:404` courses-of-action severity | through `normalizeStatusLabel` | already correct |
| 19 | `app.js:158` `statusKey` | `.toLowerCase()` | already correct |
| 20 | `fusion.py:40` `normalise_status` | explicitly case-insensitive; this is defect 1 of the fifteen, already fixed on the server | already correct |
| 21 | `fusion.py:138/141` `BAND_SEVERITY` / `worst_band` | operates only on values `normalise_status` produced | already correct |
| 22 | `models_decision.py:55`, `models_gov.py:300`, `canonical_v5.py:342` | all route through `normalise_status` | already correct |

**Four sites are case-sensitive and were NOT changed. Each is correct for its population, and the
reason is stated because "correct in practice" is a weaker claim than "correct":**

| site | why it is correct today | why it was not changed |
|---|---|---|
| `decision.js:87` `countStatus`, `:160` `classifyConflict` | every input is lowercased at source: `storedSignalStatuses` lowercases explicitly, and the legacy `sim.js` blob emits `"red"/"amber"/"green"` | `decision.js` is one of the six `SEQUENCE_BEARING_FILES`. The owner's order authorises moving **one** of them, named, for the Portfolio Health sentence. Moving a second for a defensive change that fixes no observed defect is not authorised |
| `decision.js:264/273` `healthState === "Green"` | the project status is the server's fused band, and `fusion.BANDS` is capitalised | same |
| `app.js:2712-2713` red/amber tally | reads project-level state only, which is either a fused band or `normalizeStatusLabel` output | not a severity **ranking**; no observed defect; reported instead |
| `assistant.js:115` portfolio tally | reads `deriveDecision().healthState`, already normalised | same |

They are recorded as incidental findings at section 9 so the next run has them.

---

## 4. Section 7 item 3 — every surface where an absent doc-risk score previously rendered as a value

**Two, both in `detail.js`, both fixed.**

| # | surface | what it showed | now |
|---|---|---|---|
| 1 | `detail.js:1528-1531` `briefKeySignals`, shipped into the **Executive Brief's Key Drivers** at `:1609` as *"quote these ACTUAL numbers"* | `Document risk 0.00`, status **Green** | the entry is not produced at all |
| 2 | `detail.js:1447` `briefEvidenceLine` | `Number(null)` is 0, so the brief's evidence sentence read *"documents clean"* | the clause is not produced at all |

**Surfaces checked and already correct — no change made, each with the guard that made it correct:**

| surface | guard |
|---|---|
| `signals.js:1737` `extractedTableHtml` | gates on `raw != null && raw !== ""`, so it renders an em dash |
| `detail.js:319` module evidence metric | `s.doc.score != null` |
| `detail.js:627/633` period comparison and sparkline | `pcNum()` returns `null` for `null` and `""` |
| `decision.js:78` stored signal classes | `si.docRiskScore != null` |
| `decision.js:128` `deriveStatusFromMetrics` | `if (docRisk != null)`, with its own comment naming this exact trap |
| `detail.js:1765` brief concerns | `Number(null)` is 0, which raises no concern — the correct behaviour for an absence |

**`signals.js:535-536` `portfolioVector` was excluded by Phase J and is unchanged.** It defaults an
absent doc risk to `0`, but it builds the Portfolio Health comparison vector and nothing else, it
is not on the Executive Brief path, and all five Portfolio Health identities are retired from
service so it emits nothing at all. It is reported at section 9, not fixed.

---

## 5. Section 7 item 4 — the `deepdive.js` statement, the mechanism, and every record reconciled

The statement before and after, and the mechanism, are at section 2.4. **The mechanism used is the
`cat8Retired()` predicate Run 43H wrote and reverted**, re-derived and re-verified here.

### 5.1 Every gate and package record reconciled

| record | how this run falsified it | how it was reconciled |
|---|---|---|
| `run37.gate.B04` participant-sequence drift | B04 hashes the six sequence-bearing files against **`PP.CURRENT.record`**. `deepdive.js` moved | `og-participant-2026.08-v15` minted, so `PP.CURRENT` describes the true bytes. **B04 reports 0 and was not touched** — Run 43's replacement of the hardcoded record name with `PP.CURRENT.record` is what let the blocker follow the supersession instead of measuring a predecessor |
| `run37.gate.B01` dirty candidate identity | eleven content-addressed digests recomputed from a tree six production files had moved in | `research/freeze/run44_freeze_candidate_identity.json` minted at candidate `e6889ad`, naming `4ad9f73` as its parent, which is untouched. Member lists of the two globbed groups re-derived from the filesystem, so the new suite is measured |
| `run37.gate.B11` package or predecessor mutation | the live stamp and the current package both advanced | v15 record; v14 **pinned** to `604291a`; the stamp expectation advanced in the generator, not in the gate |
| `run37.gate.no_self_reference` | the record must name RUN 43's candidate as its parent, not Run 42's | re-anchored to `4ad9f73` **explicitly**, not loosened to "any commit" |
| `run37.gate.immediate_predecessor_release_preserved` | — | a third assertion added: the v28 record must still say v28. This is why the gate is 32/32 and not 31/31 |
| `participant_packages.PARTICIPANT_PACKAGES` | four of seventy governed bytes moved | v15 appended; `V14_TO_V15_CHANGED` declares the four; **`V14_TO_V15_SEQUENCE_EXCEPTION` declares the one sequence-bearing file by name** |
| `test_run28_participant_packages` | v14 became a predecessor; one sequence-bearing file moved | v14's own checks now measure the blobs of `V14_COMMIT` rather than the live tree; a v15 block asserts the moved set is exactly the four declared, the moved sequence-bearing set is exactly the one declared, the exception is **one** named member, and the **other five are byte-identical**. Four further checks measure what moved *inside* the exception: the new sentence is what the file gained, the control count is unchanged, and its references to `submitPreliminary`, `reveal` and `lock` are unchanged in number |
| `test_run41_preservation` sections 14-15 | measured the live tree against the **v13** record | measured against the union of the declared deltas since v13, and the sequence check asserts exactly the one authorised file moved and the other five did not |
| `test_run36_fault_guards` fault35 | asserted all six sequence-bearing files identical to the frozen **v11** package | asserts the same, **except the one named exception**. A second file moving, or a different one, is still red |
| `test_run38_frozen_immutability`, `test_run39_frozen_immutability` | frozen-surface and manifest scopes | `RUN44_AUTHORISED_SUCCESSOR_CHANGES` and `RUN44_AUTHORISED_MANIFEST_CHANGES` added, each **naming** its five files; `test_run36_fault_guards.py` added to the permitted-modification set with its reason |
| `test_run39_launch_gate` identity rows | pinned to v28 and v14 | advanced to v29 and v15 |
| `production_tree.PINNED` | six production files moved | **new** `code_audit/run44_production_tree.sha256`; the run43 manifest kept addressable as its parent; `test_run25_rail_removal`'s accepted chain extended |
| `code_audit/run20_production_freeze.sha256` declared-changes guard | `assets/js/signals.js` differed and no manifest declared it | **new** `server/tools/run44_production_changes.py`, declaring the one path no earlier manifest already names, with what changed in the five already-declared files recorded in its header |
| `test_run2_fifteen_defects` `detail.js` pinned diff | three repairs moved lines in a pinned participant file | `RUN44_REMOVED` (9 lines) and `RUN44_ADDED` (24 lines) named **literally**, plus a span allowance for the one new comment block identified by its own opening line. Every other line of that file is still held to the original rules |
| `test_run31_version_boundaries`, `test_run32_closure_version_boundary`, `test_run36_instrument_qualification` | pinned stamp history and package identity | one appended stamp and one package identifier each |

**No gate row was disabled, weakened, widened or bypassed. Every row that failed did so because a
pinned byte-identity manifest was falsified by an edit this run made, which is the class the
standing contract permits reconciling. Stop condition 8.7 did not fire.**

---

## 6. Section 7 item 5 — every comment or docstring corrected by the section 4.5 sweep

**One, and the sweep that found it is now a check.** A regular expression for the withdrawn
semantics — a refusal within 120 characters of "retirement reason" or "stated retirement", in
either order — was run over every `server/**/*.py`, every `assets/js/*.js` and every `*.html` in
the repository.

| file:line | sentence | disposition |
|---|---|---|
| `server/app/simulation/registry.py:461` | *"asking `run_module()` for one by name resolves, and is refused with its stated retirement reason rather than computed"* | **corrected** — section 2.5 |

**One further hit is legitimate and is excluded by name, not by a loose pattern:**
`registry.py:507`, the note inside `run_module()` that **records the withdrawal** ("PHASE D REFUSED
A RETIRED IDENTIFIER HERE… THAT REQUIREMENT IS WITHDRAWN"). Deleting the record of a withdrawal is
not the same as deleting a false sentence.

`assets/js/taxonomy.js:607` was examined and left: *"the registry refuses it on a single-project
path"* describes the **Group D `PortfolioModuleError`**, which is still live and still refuses.

---

## 7. Section 7 item 6 — the section 4.6 findings, unacted

**Nothing about period scoping was changed. This is a report.**

### 7.1 Is the path reachable on the current code? **Yes.**

`_period_documents` (`server/app/documents.py:373`) is unchanged at `604291a`:

```python
.where(DocumentUpload.project_id == project.id, DocumentUpload.period == period)
```

The observation set for a period is only the documents uploaded into that period, and every caller
of `select_signal_inputs` on the production path is fed from it (`documents.py:1215/1231`,
`:2240/2244`, `:2282`, `:2747`). Nothing carries an earlier period's observations forward — the
`PERMANENT` field kind resolves "earliest wins" **within the supplied set**, so it cannot reach
back either.

Reproduced by execution against the real `select_signal_inputs`:

```
bac with no contract in the period  -> 4,463,290  source: pay_application  asOf 2026-06-30
bac with the contract in the period -> 5,874,620  source: contract_value   asOf 2026-03-01
```

The declared precedence is correct and is honoured **when the contract is present**. Precedence can
only choose among observations that exist.

### 7.2 Which documents in a period could supply a contract sum and be selected by the fall-through

Five, in the declared precedence order `bac` carries (`field_registry.py:183`), each with the field
it emits it from (`extraction_merge._NUMERIC_EMISSIONS` / `_EXTRA_NUMERIC_KEYS`):

| tier | document type | field on the document |
|---|---|---|
| 0 | `change_order` | `revised_contract_sum` |
| 1 | `contract_value` | `original_contract_sum` |
| 2 | `schedule_of_values` | `scheduled_value_total` |
| 3 | `pay_application` | `original_contract_sum` |
| 4 | `monthly_report` | `budget_at_completion` |

In a period holding only a pay application and a monthly report — the ordinary case for periods 2
onwards — the pay application's `original_contract_sum` wins. **`FIELD_KINDS` and `WRITER_TIERS`
have no basis dimension and no code path compares a value's basis**, so a fee-basis figure in that
slot is admitted with nothing to stop it.

### 7.3 Does any field other than `bac` have the same exposure? **Yes — fifteen others.**

`WRITER_TIERS` declares **16** multi-writer fields, and every one has the same structural exposure:
the top-tier writer can be absent from a period while a lower-tier writer is present.

| field | precedence, best first |
|---|---|
| `bac` | change_order, contract_value, schedule_of_values, pay_application, monthly_report |
| `baselineContractSum` | **contract_value**, change_order |
| `baselineEnd` | change_order, contract_value |
| `ev` | schedule_of_values, pay_application, monthly_report |
| `pv` | schedule_update, time_phased_schedule, monthly_report |
| `ac` | pay_application, monthly_report |
| `actualPctComplete` | pay_application, monthly_report |
| `plannedPctComplete` | schedule_update, time_phased_schedule, monthly_report |
| `qualityDeficienciesNoted` | field_report, inspection_report |
| `submittalsTotal`, `submittalsRejected` | submittal_register, rfa_log |
| `totalFloat`, `consumedFloat` | schedule_update, time_phased_schedule |
| `activitiesPlanned`, `activitiesConstrained`, `lookaheadWeeks` | schedule_update, lookahead_schedule |

**`baselineContractSum` is the sharpest of them and is worse than `bac`'s case**, because its
declared precedence is the *inversion*: the contract's own figure must beat a change order's
account of it, and that is the whole point of the `PERMANENT` kind. Executed:

```
baselineContractSum, change order alone in the period -> 6,100,000   (the CO's account)
baselineContractSum, contract + change order          -> 5,874,620   (the contract, correctly)
```

A contract uploaded at period 1 is invisible at period 2, so from period 2 onward a change order's
account of the original baseline wins by default — against the field registry's own declared rule.
It is a documented finding here and **nothing was changed**. Any change to period scoping is a
separate decision.

---

## 8. Section 7 item 7 — the fifteen guarantees, each with the injection that proved its check failable

The campaign ran **twelve** injections. Each one was **re-read from disk after writing** to confirm
it had landed before anything was concluded — two injections initially reported "did not land" and
were reported as such rather than counted, then re-anchored. Each ran green, then red for the
intended reason, then restored, then green.

| # | guarantee | verdict | the injection that proved its check can fail |
|---|---|---|---|
| 1 | a status differing only in case ranks identically at every comparison site | **VERIFIED** | **I1** — the whole pre-fix capitalised-only `order` map restored into `statusRank`. 70 → **62**, 8 checks red (every band's casing check, and the worst-module selection). Restored 70 |
| 2 | a category never reports a severity worse than the worst severity among its computing modules | **VERIFIED** | **I9** — `fuse_signals` made to return Amber whenever the argmax was Green. 70 → **68**; the 84-combination sweep and the named all-Green case both went red. Restored 70. The sweep also carries its own non-vacuity check (all 84 must enter the combination), which is what caught the first draft measuring the wrong route |
| 3 | the driver attribution never names a module better than the severity it drives | **VERIFIED** | **I4** — `modDrives` forced true: 70 → **67** (trace, rendered line, panel). **I5** — the brief's guard defeated: 70 → **69**. Both restored |
| 4 | an absent document risk score renders as absent on every surface, including the Executive Brief's key drivers | **VERIFIED** | **I2** — the absence guard removed, `Number(null)` again: 70 → **68** (null and blank-string cases). Restored 70 |
| 5 | a genuine stored zero document risk score renders as zero | **VERIFIED** | **I3** — the guard made truthiness-based (`&& docScore`): 70 → **68** (stored zero and legacy-blob zero). Restored 70. This is the control on I2 |
| 6 | CPI and SPI are labelled computed on every surface that shows them | **VERIFIED** | **I6** — the mark reverted to unconditional `extracted`: 70 → **67**. Restored 70 |
| 7 | the `deepdive.js` statement describes the current state, verified in a browser | **VERIFIED** | **I7** — `cat8Retired()` made a constant instead of a derivation: 70 → **69** (the no-taxonomy case). Restored 70. Verified in a browser at section 10 |
| 8 | no comment or docstring describes the withdrawn refusal semantics | **VERIFIED** | **I8** — the withdrawn sentence restored to the docstring: 70 → **67**. Restored 70 |
| 9 | `run_module()` over all 101 identifiers returns byte-identical output to a worktree at `604291a` | **VERIFIED** | `build_run44_v28_v29_execution_proof.py`: the v28 line extracted from its own git object and imported as its own package, both lines executed on a **full** and a **starved present-and-null** package. 0 of 101 rows differ on either. Proved failable by perturbing `run_tcpi`'s own `bac` by one per cent: `module divergence on FULL is ['A1.7']`, one module and only one. Restored to 0 |
| 10 | no module in service changed its computed result | **VERIFIED** | subsumed by 9, and separately: the merged signal inputs and their per-field source record are identical, `docRiskScore` is still present-and-null, and the fusion returns the same band for every voting pair tried |
| 11 | modules in service is 63, registry total 101, both derived | **VERIFIED** | **I11** — `available_modules()` made to stop intersecting with the roster in service: 70 → **68**. Restored 70. The counts are derived from `service_index()` and `registry_index()` and reconcile as 63 + 38 = 101 |
| 12 | voting count is exactly 2, `A1.7` and `A1.8` | **VERIFIED** | **I10** — a third module added to `CORE_VOTING_MODULES`: 70 → **69**. Restored 70. Freeze gate B09 reports 0 independently |
| 13 | Portfolio Health computes nowhere on any production path | **VERIFIED** | **I12** — a portfolio identity put back into `live_portfolio_modules()`: 70 → **69**. Restored 70 |
| 14 | every affected surface renders correctly, verified in a browser | **VERIFIED** | section 10. Not an injection: it is a real render of the real application, and the two-sided cases (driver named or not named, zero or absent) are each other's control |
| 15 | the successor freeze gate passes in full | **VERIFIED** | **32/32**, 15 blocker classes, 0 blocked. Section 11 |

**Not one check was deleted, and no check was weakened.** Every reconciliation replaced a pinned
expectation with the true bytes plus a **named** exception; the negative case is asserted every
time.

---

## 9. Section 7 items 8 and 9 — audit artifacts, and incidental findings

### 9.1 The self-rewriting audit artifacts

The full-suite run rewrote **18** committed artifacts, **17** under `code_audit/` and one outside
it. All 18 were restored with `git checkout --`. **None was committed**, verified by
`git status --porcelain` being empty before each commit.

```
code_audit/run10_no_operational_effect.csv          code_audit/run9_abstention_results.csv
code_audit/run20_cycle12_100_reaudit.csv            code_audit/run9_alias_overlay_verification.csv
code_audit/run20_cycle12_guard_nonvacuity.csv       code_audit/run9_fixture_import_results.csv
code_audit/run20_cycle12_lineage_campaign.csv       code_audit/run9_known_answer_results.csv
code_audit/run21_guard_nonvacuity_results.csv       code_audit/run9_no_operational_effect.csv
code_audit/run30_cat7_operational_execution.csv     code_audit/run9_validator_gap_recomputations.csv
code_audit/run38_controlled_stimulus_execution_order.csv
code_audit/run38_lock_integrity.csv                 server/tools/run17/coverage.csv  <-- outside
code_audit/run38_participant_state_machine.csv                                        code_audit/
code_audit/run39_launch_identity.csv
code_audit/run8_expectation_mutation_proof.csv
```

The `604291a` worktree used for the baseline reconciliation was likewise dirtied and was removed
with `git worktree remove` afterwards.

### 9.2 Incidental findings, unacted

1. **The provenance panel's contents are hoisted out of their own container by the HTML parser.**
   `provenanceLineHtml` emits `<div class="det-prov-hop">` inside a `<p>`, and a `<div>` closes an
   open `<p>`, so the browser makes every hop a **sibling** of the paragraph and leaves
   `<span class="det-prov-panel" hidden>` empty. The "why?" toggle therefore shows and hides an
   empty span while the hops sit outside it. This is pre-existing and is not this run's doing; it
   was found while verifying in a browser and nothing about it was changed.
2. **Four status comparisons remain case-sensitive** (`decision.js:87/160/264`, `app.js:2712-2713`,
   `assistant.js:115`). Each is correct for its population today because every input is normalised
   at source. Two of them live in `decision.js`, a sequence-bearing file this run was not
   authorised to move. Section 3 states the reasoning for each.
3. **`signals.js:535` `portfolioVector` still defaults an absent document risk to `0`.** Excluded
   by Phase J and doubly irrelevant now that Portfolio Health is retired from service, but it is
   the same class as the defect section 4.2 repaired and it is still in the file.
4. **The signals panel and the Executive Brief format a genuine zero differently** — `0` and
   `0.00`. Both are correct for their own formatter and both are distinguishable from an absence,
   which is what matters; recorded so it is not mistaken for a defect later.
5. **`A4.1 Document Risk Score` is in service, registered and computed by nothing.** Phase J's
   finding is unchanged: it is the sole member of `registry.unported_modules()` and publishes no
   row, which is why nothing on the analytical side ever contradicted a document-risk value
   invented at the render.
6. **Sixteen fields carry the period-scoping exposure, not one.** Section 7.3.
7. **`BRIEF_CAT_LABEL` in `detail.js` still carries the retired "Cat N" scheme** as user-facing
   category labels, against `NAMING_AUTHORITY.md:96`. Phase J found it; it is outside this run's
   four fixes and was not touched.

---

## 10. Section 5 items 7 and 14 — the browser verification, and the `cwd`

**19 / 19.** Driver: `server/tools/drive_run44_browser.py`, which changes nothing.

The application was served from `/home/user/LinPRojectRadar/server` on `127.0.0.1:8412` against a
**throwaway migrated SQLite database in the session scratchpad**. Production Postgres was never
configured or contacted. `window.confirm` was forced to return false.

**The `cwd` of the browser session was `/home/user/LinPRojectRadar/server`**, and the repository
root it measured is `/home/user/LinPRojectRadar`.

**The application under test is the right one**, checked before anything else was measured: the DOM
carries **7 `.page` sections** and **zero** `api.js` or `boot.js` in `document.scripts`. `DEng\Demo`
was not served.

Read from the running page, not from source:

```
.page sections                      7
api.js / boot.js in scripts         []
taxonomy categories / modules       12 / 63
portfolio-level categories          [{"id": "d1", "modules": 0}]

Portfolio Health flyout, verbatim from the rendered DOM:
  "Portfolio Health is no longer in service. The analysis that compared a project against the
   rest of the portfolio was withdrawn, so this panel does not compute for any portfolio,
   whatever number of projects it holds."
  repair controls rendered            1   (unchanged)

signals panel, rendered rows:
  docRiskScore null : Document-risk score | (em dash) | (no mark)
  docRiskScore 0    : Document-risk score | 0 | extracted | pencil
  docRiskScore 0.46 : Document-risk score | 0.46 | extracted | pencil
  CPI (computed)    | 1.22 | computed
  SPI (computed)    | 0.96 | computed
  rows marked computed                2
  heading                             "Signal inputs"

project detail page, rendered provenance line:
  Amber over all-Green modules : "Amber, driven by Cost and EVM Performance"
  Amber over an Amber module   : "Amber, driven by Cost and EVM Performance
                                  -> CUSUM Anomaly Monitor (1.2)"
  expandable detail, first case: "... Modules: no module in this category reads as adverse as the
                                  category status, so none is named as driving it. The most
                                  adverse of them is CUSUM Anomaly Monitor at Green."

page errors                         none
```

`deepdive.js` is not loaded on the landing route, so it was loaded **from the server** with a
script tag: the bytes executed are the bytes the application serves.

---

## 11. Section 6 — the freeze, row by row

**`sim-2026.08-v29` minted** at `server/app/simulation/models.py:531`, with the boundary recorded
above it. `SIMULATION_VERSION_SUPERSEDED` advances to `sim-2026.08-v28`, and v29 is **APPENDED** to
`SIMULATION_VERSION_HISTORY` — nothing edited, nothing removed. **No check was removed from the
authorised change set**; four were added (`RUN44_AUTHORISED_SUCCESSOR_CHANGES`,
`RUN44_AUTHORISED_MANIFEST_CHANGES`, `RUN44_PRODUCTION_CHANGES`, `V14_TO_V15_SEQUENCE_EXCEPTION`),
and **the change set names `assets/js/deepdive.js` explicitly** in every one of them that lists
files.

### 11.1 The fifteen blocker classes

| blocker | count | verdict |
|---|---|---|
| B01 dirty candidate identity | 0 | **PASS** — reconciled; see section 5.1 |
| B02 population mismatch | 0 | PASS |
| B03 controlled-stimulus mismatch | 0 | PASS |
| B04 participant-sequence drift | 0 | **PASS** — reconciled to `og-participant-2026.08-v15` |
| B05 false defensibility statement | 0 | PASS |
| B06 unexpected execution exception | 0 | PASS |
| B07 Category-9 bypass | 0 | PASS |
| B08 Category-10 authority violation | 0 | PASS |
| B09 voting count is not exactly 2 | 0 | PASS |
| B10 current taxonomy dual authority | 0 | PASS |
| B11 package or predecessor mutation | 0 | **PASS** — reconciled; v14 pinned to `604291a` |
| B12 browser qualification failure | 0 | PASS |
| B13 unresolved blocking Run-36 defect | 0 | PASS |
| B14 unsupported final empirical-validation claim | 0 | PASS |
| B15 candidate behaviour changed during the run | 0 | PASS |

### 11.2 The gate suite, row by row — 32 / 32

| row | verdict | note |
|---|---|---|
| `run37.gate.generator_runs` | PASS | |
| `run37.gate.artifact_present` | PASS | |
| `run37.gate.reproduces` | PASS | the committed gate reproduces from the tree |
| `run37.gate.fifteen_blocker_classes` | PASS | |
| `run37.gate.B01` … `B15` (15 rows) | PASS x15 | table above |
| `run37.gate.blocking_defects_zero` | PASS | |
| `run37.gate.predecessor_release_preserved` | PASS | the v25 record still says v25 |
| `run37.gate.immediate_predecessor_release_preserved` | PASS x3 | v26 still says v26, v27 still says v27, **v28 still says v28** — the third is new this run |
| `run37.gate.no_release_while_blocked` | PASS | |
| `run37.gate.release_present_when_clean` | PASS | record, report and checksum manifest all exist |
| `run37.gate.limitation_stated` x4 | PASS | carried forward verbatim from the predecessor |
| `run37.gate.disposition` | PASS | `FINAL_FREEZE_ACCEPTED`, and the gate agrees |
| `run37.gate.no_self_reference` | PASS | **re-anchored** to `4ad9f73`, named explicitly |

31 became 32 because the predecessor-release assertion now covers three predecessors instead of
two.

---

## 12. The check count, reconciled item by item

Both figures measured on this machine with the same runner, the baseline in a `git worktree` at
`604291a`.

| tree | suites | checks | red | aborting |
|---|---|---|---|---|
| `604291a`, in a worktree | 188 | **14,197 / 14,197** | 0 | 0 |
| **Run 44 head** | **189** | **14,280 / 14,280** | **0** | **0** |

Delta **+83**, and every suite that moved is accounted for:

| suite | baseline | now | delta | why |
|---|---|---|---|---|
| `test_run44_participant_defect_fixes` | — | 70 | **+70** | new: the four fixes, the docstring sweep, and the derived populations |
| `test_run28_participant_packages` | 84 | 96 | **+12** | v15's own block: 8 package checks plus 4 measuring what moved inside the authorised exception |
| `test_run37_freeze_gate` | 31 | 32 | **+1** | the third predecessor-release assertion |

**Sum of the deltas: +83. 14,197 + 83 = 14,280.** The reconciliation closes exactly, with nothing
left over, and no suite moved that is not in the table.

---

## 13. Section 8 — the stop conditions

| # | condition | verdict |
|---|---|---|
| 8.1 | after the 4.1 fix, a category can still report a severity worse than its worst computing module | **not fired** — 84 combinations through the production route, no violation; section 2.1 |
| 8.2 | a fix would require adding, moving or removing a user-facing control | **not fired** — none was; the flyout's repair button is asserted by count in two suites and observed in the browser |
| 8.3 | any module in service changes its computed result | **not fired** — 0 of 101 rows moved on two packages |
| 8.4 | `run_module()` on any identifier is not byte-identical to `604291a` | **not fired** — 0 of 101, both packages, both lines executed |
| 8.5 | a check must be deleted | **not fired** — none was |
| 8.6 | a gate row fails for a reason other than a manifest this run's edits falsified | **not fired** — every failing row was that class |
| 8.7 | reconciling B04 would require disabling, weakening or widening the gate | **not fired** — B04 was reconciled by minting v15; the blocker itself was not touched |
| 8.8 | a fix proves to require the stored-row access section 4.7 places out of scope | **not fired** — every one of the four was closed from the repository |

**Section 4.7's four exclusions were respected.** The CPI defect was not guessed at; the six G
questions were not touched; the D-classified abstentions (`A2.8`, `A3.3`, `A4.6`) were left as the
correct behaviour they are; and the ten unconsumed extraction fields were not touched.

---

## 14. What the next session needs, stated as a decision for the owner

Stated as decisions, not recommendations, and not ranked.

1. **The period-scoping fall-through is real, reachable, and touches sixteen fields, not one.**
   Section 7 evidences it by execution, including the `baselineContractSum` inversion where a
   change order's account of the original baseline beats the contract at every period after the
   one the contract was uploaded into — against the field registry's own declared precedence. The
   owner decides whether observations become visible across periods for `PERMANENT` facts, whether
   the writer tiers gain a basis dimension, or whether both stay as they are. Any of the three is a
   change to what a stored figure means, so none was made here.
2. **Six questions from Run 43J remain G, and every one needs the same thing: read access to
   PRJ-001's stored rows.** Nothing in this run changed that, and nothing in this run could. The
   owner decides whether a read-only export of PRJ-001's `computed_results`, `documents` and
   observation rows is produced for diagnosis, or whether those six stay G. **The CPI defect is one
   of them and was not guessed at**, as section 4.7 required.
3. **Four status comparisons stay case-sensitive because two of them live in a sequence-bearing
   file.** They are correct today because every input is normalised at source. The owner decides
   whether a second sequence-bearing file may move to make them case-insensitive by construction
   rather than by convention, or whether the convention is the guarantee.
4. **`assets/js/deepdive.js` has now moved once.** Every package record since v10 asserted the six
   sequence-bearing files were byte-identical across a successor; v15 is the first that cannot say
   it, and it says so instead. The owner decides whether that exception is closed — no further
   sequence-bearing file moves without a fresh order — or whether the invariant is now one that
   admits named exceptions as a class.
