# Four document rows that can never light up

**Date:** 2026-08-09
**Branch:** `claude/document-rows-fix`, from `origin/main` at `784792e`
**Model:** Sonnet

**Verification:** server suite **51 suites, 2700/2700** (fresh migrated SQLite per test file; the
new `test_document_rows.py` adds 36). `tests.html` **51/51**. `tests_render.html` **208/209**,
the one red being the pre-existing auth-gated "production read path" check, confirmed red on
unmodified `origin/main` too (see Verification below). Real headless-Chromium drive of the Signal
Flow diagram itself, against a harness built from the actual `assets/js` files (not a mock),
before and after the fix, with every check proven able to fail by reverting the fix and
re-running. No migration added. Nothing under `server/app/simulation/` modified. `DATABASE_URL`
never pointed anywhere but throwaway SQLite; production neither inspected nor queried.

---

## LEAD: the string-key sweep

The submittal defect is not an isolated typo. It is the third confirmed instance of one class —
a surface keys on a document-type or category string that a taxonomy rename or retirement left
behind — and the sweep below found a fourth, live instance and two further dead ones. Every
surface in the repository that keys on a document-type or category string was checked against
the current vocabulary (`server/app/extraction_fields.py DOC_TYPES`, 27 types, and
`assets/js/taxonomy.js LIN_CATEGORIES`, ids `a1..a6, b1..b4, c1, d1`). Findings:

| # | File | What was keyed | Live/dead | Fixed here |
|---|------|-----------------|-----------|------------|
| 1 | `assets/js/neural_flow.js` `DOC_KEYS[7]` | `'rfi'` — retired, not in `DOC_TYPES` | Live (diagram row permanently dark) | **Yes — row removed** |
| 2 | `assets/js/neural_flow.js` `DOC_KEYS[8]` | `'submittal'` — renamed to `submittal_register` | Live (diagram row permanently dark) | **Yes — repointed** |
| 3 | `assets/js/signals.js` `DOC_TYPE_GROUPS` | `'rfi'` and `'submittal'` entries in the upload dropdown | Live (offers a PM two type names the server will never classify a document into; `rfi` also duplicated the already-correct `rfi_log` entry) | **Yes — removed / renamed** |
| 4 | `assets/js/simulations.js` `runSourceReliability` `sourceWeights` | `'rfi': 0.65, 'submittal': 0.65` | Live but low-impact — any docType not in the dict falls back to `0.50` (line below), so the practical effect was `rfi_log`/`submittal_register` silently getting the generic default instead of the reliability weight the author intended for them | **Yes — renamed to `rfi_log`/`submittal_register`** |
| 5 | `assets/js/app.js` `categoryLedgerHtml` line 1607 | `cat.id === "cat9"` (auto-expand the Governance row) | Live — `LIN_CATEGORIES` has no `cat9` id (current scheme is `a1..a6, b1..b4, c1, d1`), so the comparison can never be true and the Governance row never auto-opens | **Yes — corrected to `"b3"`** (Regulatory & Authority Thresholds / Governance, matched by identical `method_class` set: `ABM_Governance`, `FAR_Threshold`, `OMB_A11_Check`, `EVM_Reporting_Threshold`, `Contract_Mod_Frequency`) |
| 6 | `server/app/simulation/models_dq.py` line 96 | `"rfi": 0.65, "submittal": 0.65, "field_report": 0.60` — the identical stale dict, server-side | Live, same low-impact shape as #4 | **No — `server/app/simulation/` is off-limits by this task's own constraints. Reported, not touched.** |
| 7 | `assets/js/detail.js` line 296 `buildModuleAxes` | `cat.id === "cat8"` | Dead — `buildModuleAxes` is defined but never called anywhere in the codebase (not exported, not invoked) | **No — dead code, left alone per established codebase policy (matches the precedent of `charts3d.js`'s "Cat 6" label)** |
| 8 | `assets/js/decision.js` `CATEGORY_ACTIONS` (`cat1..cat11` keys) | Already-known dead instance | Dead — both call sites are commented "unreachable today" (line 443) | **No — pre-existing, owner decision pending, not this task's to touch (per prior-session T6_HANDOFF record)** |

**Checked and clean, no defect:** `export.js`, `store.js`, `admin-ops.js`, `workspace.js`,
`files.js`, `config.js`, `jdrive_tree.py` (already uses `submittal_register`/`rfi_log`/`rfa_log`),
`server/app/documents.py`. `assets/js/knowledge.js` line 104 has `"rfi"`/`"submittal"` in a
documentation-search keyword list — not a document-type lookup, not a defect.

**Existing test suites checked for the same defect encoded as expected behaviour** (per this
task's warning that three suites had already done this and passed for months): none found.
`server/tools/test_submittal_and_fairness.py`, `test_storage_redesign.py`,
`test_document_versioning.py`, `test_documents_b7b.py`, and `extraction_merge.py`'s own doctest
all use the bare `"rfi"` / `"submittal"` strings deliberately — as the INPUT to prove the
server-side alias/retirement machinery does the right thing with a legacy or retired string
(`canonical_doc_type("submittal") == "submittal_register"`, `"rfi" not in DOC_TYPES and not
is_mapped("rfi")`). That is the correct, intended behaviour and is exactly what stayed in place;
none of them assert anything about the diagram's own key comparison, so none needed to change.
`tests_render.html` has one incidental use of `docType: "rfi"` (line 1142) as a stand-in for "an
unmapped document type" in a documents-panel fixture unrelated to `neural_flow.js` — also not a
defect.

Confirmed after the fix: `neural_flow.js`'s `DOC_KEYS` (27 entries) is now **exactly** the current
`DOC_TYPES` set — no diagram key is stale and no current type is missing a row. `signals.js`'s
dropdown offers exactly `DOC_TYPES ∪ UI_ONLY_DOC_TYPES` (42 keys), same guarantee for the
upload surface. Both are asserted by `server/tools/test_document_rows.py`.

---

## What the classifier was given to tell a Schedule of Values from a Pay Application

Before this fix, `CLASSIFY_HINTS` had exactly one clause bearing on either document, and it
described Pay Application only:

> "Match on content: pay application has contract sum and amount paid; ..."

Nothing named `schedule_of_values` at all — the audit's finding was literally that the hint list
had a zero-length entry for it, not a wrong one. `_EXTRACTION_FIELDS` confirms the two are
structurally distinct downstream (`schedule_of_values`: `completed_to_date`,
`scheduled_value_total`, `period_to_date` — a line-item breakdown; `pay_application`:
`amount_paid_to_date`, `application_date`, `work_period_from/to`, plus contingency and
percent-complete fields — a numbered payment request), but the classifier prompt never told the
model that distinction existed.

The fix adds a `schedule_of_values` clause and sharpens the `pay_application` clause, written to
name what is present in one and absent in the other rather than describing each in isolation:

> "Match on content: pay application has contract sum, amount paid to date and a billing period,
> and is a numbered request for payment; a schedule of values breaks the contract sum into line
> items, each with its own scheduled value and percent or amount complete, and unlike a pay
> application carries no amount paid and no billing period; ..."

This is deterministic-pinned in `test_document_rows.py` section 7 (the phrases `"line item"`,
`"billing period"`, `"amount paid"`, and the "carries no" contrast are all asserted present, and
a self-test confirms the pre-fix hint text — reconstructed — does NOT carry them, so the check
can fail). **It cannot prove a real model now classifies the two correctly** — no
`ANTHROPIC_API_KEY` and no sample PDF/DOCX document exist in this environment (checked: `env |
grep -i anthropic` empty, `find . -iname "*.pdf" -o -iname "*.docx"` empty). That live
verification is a separate, key-and-documents-gated step, same limitation `test_extraction_prompt.py`
already documents for the rest of the classifier prompt.

**The filename heuristic (`guess_type_from_filename`) was NOT touched.** It has no
`"schedule of values"` match today (a bare `"schedule"` filename still falls to
`schedule_update`), which is a real, separate gap — but the task's language throughout ("give
the classifier enough", "the classifier's only hint") points at `CLASSIFY_HINTS`, the model
prompt, and the task explicitly excludes "extraction fields or module inputs." Flagged here for a
future task, not fixed in this one.

---

## The RFI row: the log, not the retired individual form

`neural_flow.js` had **two** RFI-related rows before this fix: `DOC_KEYS[7]` = `'rfi'` (dead by
construction — `'rfi'` is not in `DOC_TYPES` at all, so no classified document can ever produce
an event with that `docType`) and `DOC_KEYS[26]` = `'rfi_log'` (already structurally correct).
The fix removes the dead row rather than repointing it onto `'rfi_log'`, which would have
produced two rows fed by the identical signal. `DOC_TO_CATS[7]` (the parallel category-mapping
array) was removed at the same index to preserve the array's index-alignment with `DOC_KEYS`.

**Does the classifier recognise the design-engagement wording?** Checked directly against the
pre-fix `CLASSIFY_HINTS`: no. The only RFI-related clause was `"an RFI log lists requests for
information with totals"` — no mention of "design query" or "owner decision," the titling
Project 1 uses (`"Design Query and Owner Decision Log"`) and Projects 2/3 partially use
(`"RFI and Design Query Log"`). The fix extends the clause:

> "an RFI log lists requests for information with totals, whatever it is titled — a document
> titled a design query log or an owner decision log records the same request, response and
> decision content and is the same type; ..."

Same pinning/self-test limitation as the Schedule of Values clause above applies here.

---

## Three rows that are correctly absent: can the platform tell?

Checked whether the platform has any existing signal that could distinguish "this project will
never produce a Past Performance Report / Historical Project Data / Test and Commissioning
Report" from an ordinary missing document, before hardcoding anything:

- **`server/app/documents.py`'s `_EXPECTED_DOC_TYPES`** (line 1822) is an advisory completeness
  hint, but it names the OPPOSITE four types — `pay_application`, `monthly_report`,
  `schedule_update`, `contract_value` — the ones a period is normally expected to carry. It says
  nothing about the three in question and is not usable for this.
- **Modules DO carry this kind of signal.** Each module's taxonomy entry has a `sectors` list
  (`taxonomy.js` `LIN_MODULE_SECTORS`, built from `m.sectors`), and `getModuleStatus()` reads it
  to return `'NA'` for a module not applicable to the project's sector — this is exactly the
  mechanism that already powers the diagram's existing blue/NotRelevant state, just at module
  granularity.
- **Document types carry no equivalent field.** `DOC_TYPES` in `extraction_fields.py` is a flat
  tuple of strings — no per-type sector list, no per-type applicability metadata of any kind.
  There is no project attribute, sector tag, or config value anywhere in the data model that
  distinguishes these three types from any other type a project simply hasn't uploaded yet this
  period.

**So the distinction cannot be drawn from what the platform knows.** Saying so rather than
pretending otherwise: `DOC_NOT_APPLICABLE` in `neural_flow.js` is a **hardcoded editorial list**
of the three type names the creator confirmed, documented in the code as exactly that (not a
computed signal, unlike the module case it otherwise mirrors visually). If the platform later
grows a real per-document-type applicability field, this list should be replaced by reading it —
this is the seam where that would plug in.

**What it does, given that:** a doc row in `DOC_NOT_APPLICABLE` that is not uploaded now renders
with the diagram's existing `NotRelevant` colour (`#5b3dd6`, the same blue module NA rows use) as
a square marker — the same shape the legend's existing "Not relevant" key already promised but
that no document row had ever used — instead of the dark, low-opacity "no data" circle every
other unlit row still gets. The gate is `!uploaded && DOC_NOT_APPLICABLE[key]`: a document that
somehow WAS uploaded for one of these three types still lights normally, so nothing here can mask
a genuine future upload.

---

## What was NOT done, per the task's explicit exclusions

- No fee-basis vocabulary was added anywhere.
- No extraction field or module input was changed. `_EXTRACTION_FIELDS`, `ALL_FIELDS`,
  `extraction_fields_for()` are untouched.
- The Schedule of Values / four-other-types field-precedence overlap was reported, not changed.
  `field_registry.py WRITER_TIERS` is untouched. The overlap, read directly from the (unmodified)
  table:

  ```
  "bac": {"change_order": 0, "contract_value": 1, "schedule_of_values": 2,
          "pay_application": 3, "monthly_report": 4}
  "ev":  {"schedule_of_values": 0, "pay_application": 1, "monthly_report": 2}
  ```

  Even correctly classified, `schedule_of_values` competes for `bac` with `change_order` and
  `contract_value` (both ranked ahead of it) and `pay_application`/`monthly_report` (ranked
  behind), and for `ev` with `pay_application` and `monthly_report` (both ranked behind it, so
  `schedule_of_values` wins `ev` whenever it is present). The union of the other writers across
  both fields is exactly four types: `change_order`, `contract_value`, `pay_application`,
  `monthly_report` — matching the task's own framing. Lower tier number wins; ties break on
  latest `as_of`. Not changed here.
- `server/app/simulation/` was not modified — the `models_dq.py` stale-key instance (#6 above)
  is reported, not fixed.

---

## Verification

**Server suite:** `server/run_all_suites.sh` (fresh migrated SQLite per file) —
**51 suites, 2700/2700 checks, ALL SUITES GREEN**, including the new
`server/tools/test_document_rows.py` (36/36). That suite is deterministic (no DB, no model key):
it pins the `CLASSIFY_HINTS` wording, sweeps `neural_flow.js`/`signals.js`/`simulations.js`/
`app.js` for retired keys with a regex detector that is self-tested against a planted bad string
before being trusted against the real files, checks the `DOC_KEYS`/`DOC_TO_CATS` parallel-array
invariant, and checks `DOC_KEYS` is exactly the current `DOC_TYPES` set.

**`tests.html`:** 51/51, unchanged (this page does not touch document types or categories).

**`tests_render.html`:** 208/209. The one red row (`"production read path: exercised against the
server"`) is a deliberate, by-design failure documented in the file itself
("NO TOKEN, NO SILENT SKIP") when no signed-in session token is present in the tab —
confirmed identically red (208/209, same row, same `LinAuth.getToken is not a function` console
errors) on this branch's changes fully reverted (`git stash` of all five changed files, rerun,
`git stash pop`), so it is pre-existing and unrelated to this task.

**Signal Flow diagram, driven in a real headless Chromium** (`--use-gl=swiftshader
--enable-webgl --ignore-gpu-blocklist`, the real `config.js`/`taxonomy.js`/`signals.js`/
`neural_flow.js` loaded exactly as `index.html` orders them, `LinNeuralFlow.render()` called on
synthetic project fixtures — not a mock of the renderer, the actual file):

- **Baseline (nothing uploaded):** all 27 rows render; `Past Performance Report`,
  `Historical Project Data`, and `Test & Commissioning Report` render as blue squares
  (`fill=#5b3dd6`, the `NotRelevant` colour), every other unlit row still renders as the plain
  dark circle (`fill=#1e2a3c`) it always did. No row is labelled `"RFI / RFI Log"` any more.
- **Documents uploaded** (`rfi_log`, `submittal_register`, `schedule_of_values`, plus
  `contract_value` as a control — AND the retired strings `rfi` and `submittal` fed in
  alongside them): exactly those four real types light (`fill=#a0bcd8`, `opacity=0.88`); feeding
  the retired `rfi`/`submittal` strings lights nothing extra, proving no row is still reachable
  through the old names. The three not-applicable rows stay blue, unaffected by unrelated
  uploads.
- **Every check proven able to fail:** `assets/js/neural_flow.js` alone was reverted to its
  pre-fix content (`git stash` of just that file) and the identical harness re-run. Result: the
  three not-applicable rows read dark (`fill=#1e2a3c`, plain circle) instead of blue, and the
  `Submittal Register` row does not exist at all (`None` — the row was still keyed `'submittal'`,
  so nothing in the harness's output matches the label). The fix was then restored (`git stash
  pop`) and the harness re-run clean. `rfi_log` and `schedule_of_values` correctly still passed
  in the reverted state, because those two checks exercise parts this task did not need to touch
  in `neural_flow.js` itself (the RFI-log row already existed correctly; the Schedule of Values
  row was always keyed correctly — that document's defect was in the classifier prompt, not the
  diagram key).

No live-document, live-model classification test was run (no `ANTHROPIC_API_KEY`, no sample
PDF/DOCX in this environment) — see the classifier-hints section above for what is and is not
proven there.
