# Run 63: the four charts

## 1. What is fixed and what is not

**Two defects on the Signal Flow are FIXED, merged and pushed to `main`: it reported "0 uploaded documents across 0 types" on a page listing every one of them, and it announced a category the stored row does not carry.** **The Project Signal Network, the Signal Web and the Ensemble Analysis are NOT broken: every count they render was measured against the stored row and every one of them agrees with it — they look empty because 3 of 63 modules held a result on the fixture and 4 of 63 do on PRJ-001, and that is CORRECT BUT BLEAK, reported and deliberately left alone.** Nothing else about the four charts was changed; the mint took three passes, the freeze gate is clean at 15 blocker classes with 0 blocked, all 205 suites are green at 15334/15334, and `main` is published at `2e20c29`.

## 2. The tree at the start, and every false premise found

```
git status --porcelain                         EMPTY
main == origin/main == HEAD                    5fec302c29c9f90256d74c1eeded1747d34e2900
git branch --show-current                      main
server/app/simulation/models.py:758            SIMULATION_VERSION = "sim-2026.08-v40"
participant_packages.CURRENT                   og-participant-2026.08-v25
registry_index() / service_index()             101 / 63
CORE_VOTING_MODULES                            ['A1.7', 'A1.8']
python3                                        3.11.15  (no .venv; documented fallback)
repository                                     /home/user/LinPRojectRadar (the Linux clone)
```

**Premises in the order, checked:**

| Premise | Verdict |
|---|---|
| §6 starting point (commit, stamp, package, gate 15 blockers) | **TRUE**, re-derived above |
| §6 "the freeze gate is 15 blocker classes, not 34 rows; the 34 is `test_run37_freeze_gate.py`" | **TRUE.** The gate CSV has 15 rows; the suite prints `RESULT: 34/34` |
| §4 "Signal Flow header `27 supported document types`" | **TRUE and DERIVED.** `neural_flow.js` `DOC_KEYS` is 27 entries and is **set-equal to the server's `extraction_fields.DOC_TYPES`** (27), verified by execution, no member on either side only |
| §4 "the Signal Flow caption sums to 63" | **TRUE** (4 + 53 + 6 + 0). Measured on the fixture: 3 + 60 + 0 + 0 = 63 |
| §4 "Signal Web says 4 active and reports 2 Amber + 2 Green = 4" | **TRUE and consistent.** Measured: 3 active, 0 Red + 2 Amber + 1 Green = 3 |
| Briefing hypothesis: "both counters walk an event list, not the document list the Documents panel counts" | **HALF FALSE, and the correction matters.** Both walk *the same* event list, `project.events`. They differ in the **window**: `detail.js:683 uploadedDocEvents` walks the whole log; `neural_flow.js` walked only the slice after the last `signals_reset`. The defect is the window, not a different list |
| Briefing hypothesis: "`projectIsEmpty` at :599 may be drawing an empty-project layout for a project with 100 documents" | **FALSE, measured.** `projectIsEmpty` requires `modWithResult === 0` as well, and 3 modules had results, so it was false and the full layout was drawn. The zero was in the caption and the header only |
| Briefing: "`signals.js:1260` says *The 15 supported document types* against `neural_flow.js`'s 27" | **TRUE, and the 27 is the authoritative one.** `signals.js` `DROPZONE_REFERENCE` is a stale editorial list of 15 labels for a non-interactive reference panel. Reported as an incidental finding; **not touched**, because it is not one of the four charts and §12 rule 3 forbids going further |
| Briefing: "`neural_flow.js`, `projectnet2d.js`, `signals.js`, `detail.js` are NOT sequence-bearing — verify" | **TRUE**, verified against `SEQUENCE_BEARING_FILES_FROM_V21` |
| Briefing: "26/28 audit artifacts are rewritten by a full suite pass" | **28**, matching Run 62 exactly. Named in §12 below |

## 3. The §5.1 table: what each chart builds from, which period, and every count beside the row value it describes

Established **by execution** in real Chromium on the real load path (`server/tools/drive_run63_four_charts.py`), against a fixture built to PRJ-001's shape: 35 documents across two periods, then `resetsignals`, then `projectcomputeall`. **DEng\Demo tell, both sessions: 7 `.page` sections (expected 7); `api.js`/`boot.js` in `document.scripts`: `[]` (expected `[]`).** No page errors in either session. **WebGL panels opened ONE AT A TIME**, in the order `d-docsignals → d-projnet → d-neural → d-web → d-ensemble`, 6 s apart.

**The stored row the whole table is measured against** (period 2, the period the page holds; `page_holds_period = 2`, `row_period = 2` for every surface):

```
row.module_results        3   ->  A1.2 'green', A1.7 'Amber', A1.8 'Amber'
row.category_statuses     1   ->  {A1: Amber}, module_count 2   (the two VOTING modules)
row.project_status            Amber
row.source_documents     17   (period 2's own set; 12 distinct doc_types)
row.signal_inputs        16 keys, of which one is `events`, so 15 signal fields
project.events           36   ->  35 `signals_extracted` + 1 `signals_reset`, 0 after the reset
```

| # | Chart | Built by | Reads | Period | Count rendered | The row value it claims to describe |
|---|---|---|---|---|---|---|
| 1 | **Signal Flow** | `assets/js/neural_flow.js`, `LinNeuralFlow.render`, lazy-init `d-neural` (`detail.js:1124`) | module and category status through `window.getModuleStatus` / `getCategoryStatus` (taxonomy.js → **stored row**); document counts through **`project.events`** and, before this run, `project.signalInputs` | **2** — via `rowFor` inside the shared resolvers | `27 SUPPORTED DOCUMENT TYPES` | `DOC_KEYS.length`; = server `DOC_TYPES` (27) |
| | | | | | `0 UPLOADED SINCE THE RESET, 35 RETAINED` | 35 documents on file, 17 behind the current row |
| | | | | | `63 REGISTERED PROJECT MODULES` | `len(service_index())` = 63 |
| | | | | | `3 WITH A CURRENT RESULT` | `row.module_results` = 3 |
| | | | | | `11 REGISTERED CATEGORIES` | `projectLevelCategories()` = 11 |
| | | | | | `1 ESTIMABLE NOW` | `row.category_statuses` = 1 |
| | | | | | `COST RECOVERY STATUS / CURRENT` | `row.project_status` = Amber |
| | | | | | caption `0 uploaded documents across 0 types, 3 with a current result, 60 with no current result, 0 not applicable, 0 disabled, 1 estimable category` | 35 docs / 13 types; 3; 60; 0; 0; 1 |
| 2 | **Project Signal Network** | `assets/js/projectnet2d.js`, `LinProjectNet2D.render`, lazy-init `d-projnet` | `window.getCategoryStatus` and `getModuleStatus`, **stored row only, no fallback** (`projectnet2d.js:99-104`) | **2** | `63 modules · 11 categories` | derived from `projectLevelCategories()` |
| | | | | | `0 Red · 1 Amber · 0 Yellow · 0 Green · 10 No-data` | `row.category_statuses` = {A1: Amber}, 1 of 11 |
| | | | | | per-module dots | `row.module_results`, 3 coloured of 63 |
| 3 | **Signal Web** | `signalWebHtml` (`detail.js:407`) + `wireSignalSphere`, lazy-init `d-web` | `LinResults.hasResult`, `getModuleStatus`, **stored row** | **2** | `63-module sphere · 3 active` | 3 modules carry a status in the row |
| | | | | | `63 modules · 0 Red · 2 Amber · 1 Green` | exactly the row's three status colours |
| | | | | | eyebrow `Signal Sphere: August 2026` | **nothing** — the wall-clock month (carry-forward 4) |
| 4 | **Ensemble Analysis** | `ensembleHtml` / `ensembleTally` (`detail.js:461`), lazy-init `d-ensemble` | `getModuleStatus`, **stored row** | **2** | `Ensemble Scatter · 3 active modules (63 total)` | `row.module_results` = 3 |
| | | | | | `63 modules in 3D` | `projectModuleCount()` = 63 |
| | | | | | badge `3 active · 0 est.` | 3 with a status; 0 whose `evidence_metric` is estimated/derived/assumed |
| — | Documents panel (§8-2's other half) | `uploadedDocsPanelHtml` / `uploadedDocEvents` (`detail.js:683`) | **`project.events`, whole log** | n/a (project-lifetime) | `Documents: 35 documents`, 35 rows, badge `35 docs · 16 fields` | 35 extraction events; 16 counted signal-input keys, one of which is `events` |

**The two facts this table established that nothing in the tree said out loud:**

1. **`neural_flow.js` and `projectnet2d.js` never touch `LinResults` at all** — zero occurrences in either file before this run. They reached the row only indirectly, through `window.getModuleStatus` / `getCategoryStatus`. Run 61 measured six DOM panels and neither of these; §8-5 was therefore unasserted for two of the four charts.
2. **`row.source_documents` was reaching the browser as `null`** against a stored row holding 17 of them. `documents.py _result_view` serves it; `detail.js primeAndRefresh` grafted `module_results`, `signal_inputs`, `recommendation_basis`, `abstained` and `consistency_findings` onto `storedResult` but **not** `source_documents`, so `LinResults.rowFor(p).source_documents` was undefined on every detail page.

## 4. The §5.2 classification, item by item

**WRONG — fixed**

| Item | Measured | Should be |
|---|---|---|
| Signal Flow header, document column | `0 UPLOADED SINCE THE RESET, 35 RETAINED` | `35 UPLOADED ON THIS PROJECT` |
| Signal Flow caption, document count | `0 uploaded documents` | `35 uploaded documents` |
| Signal Flow caption, type count | `across 0 types` | `across 13 types` |
| Signal Flow, category-status derivation | a browser-side worst-of fallback that can announce a category the row has no status for | read the row, or read as no data |
| `rowFor(p).source_documents` on the detail page | `null` against a row holding 17 | the served record |

**CORRECT BUT BLEAK — reported, unchanged** (see §6)

| Item | Measured | The row |
|---|---|---|
| Signal Flow `3 WITH A CURRENT RESULT` / `60 with no current result` | 3 / 60 | 3 module results of 63 |
| Signal Flow `1 ESTIMABLE NOW` / `1 estimable category` | 1 | 1 category status of 11 |
| Project Signal Network `0 Red · 1 Amber · 0 Yellow · 0 Green · 10 No-data` | 1 of 11 | identical |
| Project Signal Network per-module dots | 3 coloured of 63 | identical |
| Signal Web `63-module sphere · 3 active` | 3 | identical |
| Signal Web `63 modules · 0 Red · 2 Amber · 1 Green` | 0/2/1 | identical |
| Ensemble `3 active modules (63 total)` | 3 | identical |
| Ensemble badge `0 est.` | 0 | no module recorded an estimated evidence metric |

**CORRECT — derived, not typed**

`27 SUPPORTED DOCUMENT TYPES` (= server `DOC_TYPES`, set-equal, verified), `63 REGISTERED PROJECT MODULES` (= `service_index()`), `11 REGISTERED CATEGORIES`, `63 modules · 11 categories`, `63 modules in 3D`, project status `CURRENT` (= `row.project_status`).

**NOT DETERMINABLE**

- **The owner's `6 not applicable to this project`.** My fixture is hybrid-sector and rendered `0 not applicable`. The derivation is `isModuleSectorNA` reading the taxonomy's own `sectors` list, not a literal, so the mechanism is sound — but **I cannot state which six modules PRJ-001 excludes without PRJ-001, and I did not guess.**
- **The owner's `2 estimable categories`.** I established the **only** site in the client that can produce a category status the row does not carry — `neural_flow.js`'s worst-of fallback — and removed it. **I did not reproduce the 2-against-1 divergence on my own fixture**, because all three of its module results sat in A1, which the row *does* give a status. The mechanism is established from the stored row itself: `category_statuses.A1` records `module_count: 2` while three modules held results, so a category is fused from its **voting** modules (`A1.7`, `A1.8`) only, and a non-voting result in a category the server gave no status was enough for the fallback to invent one. **That is a derivation, not a reproduction, and it is stated as such.**

## 5. What was fixed, and the injection proving each fix can fail

Three sites, two files. No computed value, no stored figure, no control.

1. **`assets/js/neural_flow.js` — the document count.** The since-the-reset window rests on a premise the server does not honour: that evidence becomes current again only by being uploaded again. `w_resetsignals` (`writes.py:439`) supersedes every live row and appends the marker but **deletes no document** — its own control says so — and `projectcompute` then re-reads the retained documents and writes a fresh live row **without appending one new `signals_extracted` event**. The counter now calls **`LinDetail.uploadedDocEvents`**, the Documents panel's own reader, gated on a **live stored row for the period the page holds**. That is a *stronger* form of Run 18's cleared-project requirement, not a weaker one: a reset supersedes every live row, so a project cleared and not recomputed still has no current evidence and still lights nothing.
2. **`assets/js/neural_flow.js` — the invented category status.** The worst-of fallback is removed and **nothing replaces it**. A category the row gives no status reads as no data, which is what the Project Signal Network already says.
3. **`assets/js/detail.js`** — exports `uploadedDocEvents` so there is one implementation, and grafts `source_documents` onto `storedResult`.

**Measured after the fix, same driver, same fixture, real Chromium:**

```
BEFORE  header  : 0 UPLOADED SINCE THE RESET, 35 RETAINED
AFTER   header  : 35 UPLOADED ON THIS PROJECT
BEFORE  caption : This project currently has 0 uploaded documents across 0 types, 3 modules with a
                  current result, 60 with no current result, 0 not applicable ... and 1 estimable category.
AFTER   caption : This project currently has 35 uploaded documents across 13 types, 3 modules with a
                  current result, 60 with no current result, 0 not applicable ... and 1 estimable category.
Documents panel : Documents: 35 documents / 35 rows   (unchanged, both runs)
row_source_documents in the browser:  null  ->  17
page errors: []   .page sections: 7   api.js/boot.js: []
```

**Nine injections, each against the COMMITTED REFERENCE `4378b990a72847b695f7e0524d53d744194acadc` (never from disk), each read back from disk to confirm it landed, each restored in a `finally`, baseline rechecked after every one, tree checked clean at start AND end via `campaign_safety.require_clean_tree`.** Baseline `RESULT: 24/24`.

| # | Site deleted or reverted | Landed | Result |
|---|---|---|---|
| F1 | `currentDocs = LinDetail.uploadedDocEvents(project) \|\| [];` → `[]` | yes | 23/24 |
| F2 | the `LinDetail` export line reverted | yes | 23/24 |
| F3 | `hasCurrentRow = !!(... rowFor(project))` → `true` | yes | 22/24 |
| F4 | the worst-of category fallback restored | yes | 23/24 |
| F5 | the `source_documents` graft deleted | yes | 23/24 |
| F6 | the document-type fill deleted | yes | 23/24 |
| F7 | `DOC_KEYS.length` → the literal `'27'` | yes | 22/24 |
| F8 | `projectnet2d.js` stops reading `getCategoryStatus` | yes | 23/24 |
| F9 | the driver primes a row before rendering | yes | 23/24 |

**All nine landed and all nine went red for the intended reason**, each naming its own check. F1, F3, F4, F5 and F8 also fail `test_run21_reset_disclosure` and `test_run28_participant_packages`, which pin the same sites independently.

## 6. Everything classified CORRECT BUT BLEAK, stated plainly

**Three of the four charts you named are not broken.** On the fixture, three modules of sixty-three held a result and one category of eleven had a status. Every number those charts printed was exactly that:

- The **Project Signal Network** drew eleven category nodes with one Amber and ten grey, and 63 module dots with three coloured. The row has one category status and three module results. It is telling the truth.
- The **Signal Web** drew a 63-node sphere with three lit and said so twice — `3 active` and `0 Red · 2 Amber · 1 Green`. Both equal the row.
- The **Ensemble Analysis** plotted 63 points, three of them in status columns, and said `3 active modules (63 total)`. That equals the row.
- On the **Signal Flow**, `3 WITH A CURRENT RESULT`, `60 with no current result` and `1 ESTIMABLE NOW` were already right before this run and are unchanged by it.

**These charts look empty because the project is sparse, not because they are broken, and I changed none of them.** On your PRJ-001 the same arithmetic gives four modules and (once the invented one is gone) one estimable category out of eleven. Making any of them look fuller would have been the one failure this instrument cannot afford.

## 7. Anything needing a rebuild

**None of the four requires a rebuild.** Each is a display surface over `row.module_results` and `row.category_statuses`, and each can be — and now is — made truthful by reading that row. §5.4's three answers are therefore not reached for any of the four, and no rebuild is proposed. The honest picture is sparse and the honest picture is what ships; **what would make these charts full is more modules computing, not different drawing code**, and that is your decision, not this run's.

## 8. Every item stopped under §10

**None.** No fix required a computed or stored value to change (§10.1), none required a redesign (§10.2), none required a control (§10.4). Two counts are reported **NOT DETERMINABLE** under §10.3 and are named in §4 above: PRJ-001's six not-applicable modules, and a live reproduction of the two-against-one category divergence. §10.5 fired repeatedly and the corrections are in §2.

## 9. Every item unstarted for budget

**None.** Every item §5 orders was measured, classified, and either fixed or reported. The mint, the gate, the full suite pass, the merge and the push all completed.

## 10. The §8 guarantees

| # | Guarantee | Verdict | Injection |
|---|---|---|---|
| 1 | every count equals the row value it describes | **MET**, count by count in §3 | F6, F7 |
| 2 | the Signal Flow document count equals the Documents panel's, on the same render | **MET: 35 == 35**, one render, one implementation | F1, F2 |
| 3 | the three accounts of module status agree with each other and with the row | **MET.** Signal Flow `3 with a current result` / `1 estimable category`; Project Signal Network `1 Amber, 10 No-data` over 11; Signal Web `3 active`, `0 Red 2 Amber 1 Green`. All from `row.module_results` and `row.category_statuses` | F4, F8 |
| 4 | no typed literal where a derived count belongs | **MET.** `DOC_KEYS` proved set-equal to the server's `DOC_TYPES` | F7 |
| 5 | every chart reads the period the page holds | **MET.** `page_holds_period = row_period = 2` for all four; all four reach the row through `rowFor`, which asks for `storedResult.period` and refuses any other | F3, F5 |
| 6 | first render equals second render | **MET on the settled render.** Reported precisely: at the 500 ms first capture the Ensemble badge reads `0 active · 0 est.` and the Documents badge `35 docs · 0 fields`, because `projectresults` has not returned; after `primeAndRefresh` and on the second full render every value is identical. **That transient is the documented two-pass behaviour, not a disagreement between renders**, and §11.7 is not triggered | — |
| 7 | no computed value changed | **MET.** B15 re-derived the behaviour digest and reproduced it identically | gate B15 |
| 8 | no stored figure changed | **MET.** Both files are client display code; no write path touched | gate B11 |
| 9 | the behaviour digest is RE-DERIVED, not assumed | **MET**: `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1` | gate B15 |
| 10 | 63 in service, 101 registered, both derived | **MET**, asserted live | — |
| 11 | voting count exactly 2, A1.7 and A1.8 | **MET** | gate B09 |
| 12 | every runtime lookup across all 101 modules resolves, live | **MET**, gate B10: "runtime lookups failing across all 101 registered modules: none" | gate B10 |
| 13 | the successor freeze gate passes in full | **MET**: 15 blockers, 0 BLOCKED; `test_run37_freeze_gate` 34/34 | gate |

## 11. The mint: passes, gate rows, suite, merge, push

**Three passes. Two forced refusals, both by the mint's own exit-3 guard, plus one self-caught predecessor rewrite.**

| Pass | What forced it |
|---|---|
| 1 | `CANDIDATE` read `d1976a06` (Run 62's). The mint computed `514096af` and **REFUSED with exit 3**, printing both. Set explicitly and re-run |
| 2 | Gate clean at `514096af`. Then `build_run63_successor_release.py` **wrote over `RUN62_SUCCESSOR_FREEZE_RECORD.json`** because its three output filenames were copied forward with the rest of the file — **precisely the predecessor rewrite B11 exists to catch, caught by reading the tool's own output**. Restored from git before anything else ran; the three paths corrected |
| 3 | The full suite exposed six suites pinning the identity this mint advances. Reconciling them moved six `test_suite_identity` members, which moved the candidate identity digest, which moved the candidate. The mint **REFUSED with exit 3** again, naming `5c023bc`. Set explicitly; gate re-run clean |

**`CANDIDATE` was passed explicitly on every identity build; `--candidate HEAD` was never relied on.**

**Sequence-bearing files: the EMPTY TUPLE, declared and not omitted.** Exactly two of the sixty-nine governed files moved — `assets/js/detail.js` and `assets/js/neural_flow.js` — and **neither is a member of `SEQUENCE_BEARING_FILES_FROM_V21`** (`decision.js`, `decision-ui.js`, `workspace.js`, `intake.json`, `debrief.json`), measured by membership, not assumed. `V25_TO_V26_SEQUENCE_EXCEPTION` and `V25_TO_V26_DELETED` are both written out as `()` with the reason recorded. All five sequence-bearing files are present and byte-identical to v25, measured.

**The pinned ladders: shift and append, never replace.** `test_run41_preservation`'s ladder is positional; every index was moved down by one and a **twelfth** clause added so `v30` is still reached rather than falling off the bottom. `test_run31_version_boundaries` and `test_run32_closure_version_boundary` were **appended to**, with `v40` keeping its position. Nothing was inserted, replaced or removed.

**The freeze gate, every row from live output** (`research/freeze/run63_successor_freeze_gate.csv`):

| Blocker | Count | Evidence | Result |
|---|---|---|---|
| B01 dirty candidate identity | 0 | 11 content-addressed digests recomputed from the tree; divergences: 0 | **PASS** |
| B02 population mismatch | 0 | registered 101/101; project scientific targets 95/95; Portfolio Health 5/5; scientific 100/100 | **PASS** |
| B03 controlled-stimulus mismatch | 0 | projects 6, periods 6, unique 36, rows 36, duplicates 0, missing 0 | **PASS** |
| B04 participant-sequence drift | 0 | 5 sequence-bearing files compared against the v26 record; **moved: none** | **PASS** |
| B05 false defensibility statement | 0 | 100 served statements against EXECUTED behaviour; failing: none | **PASS** |
| B06 unexpected execution exception | 0 | census ABSTAINS 89, COMPUTES 5, SUPPLIED_NOT_COMPUTED 1, PORTFOLIO_ROUTE 5 | **PASS** |
| B07 Category-9 bypass | 0 | unqualified probes reaching a banded result: none | **PASS** |
| B08 Category-10 authority violation | 0 | human_authorization_required True, creates_project_evidence False | **PASS** |
| B09 voting count is not exactly 2 | 0 | `CORE_VOTING_MODULES = ['A1.7', 'A1.8']` | **PASS** |
| B10 current taxonomy dual authority | 0 | one authority; both mirrors trace to the generator; **runtime lookups failing across all 101: none** | **PASS** |
| B11 package or predecessor mutation | 0 | **rewritten predecessor package records: none**; v26 files not matching their record: none; live stamp sim-2026.08-v41; predecessor d1976a06 still stamped v40: True | **PASS** |
| B12 browser qualification failure | 0 | 29 rows; failing: none | **PASS** |
| B13 unresolved blocking Run-36 defect | 0 | open instrument-level defects: none | **PASS** |
| B14 unsupported empirical-validation claim | 0 | all 100 rows NOT_EMPIRICALLY_FIELD_VALIDATED | **PASS** |
| B15 candidate behaviour changed during the run | 0 | behaviour digest RE-DERIVED and reproduced identically: `8fb4d366…3bd3a7a1` | **PASS** |

`FREEZE GATE: 15 blockers evaluated, 0 BLOCKED -> gate clean`.

**The full suite**, `server/run_all_suites.sh`, every suite on its own freshly migrated SQLite database from one alembic template:

```
Suites run: 205   Total checks: 15334/15334
ALL SUITES GREEN
```

205, up from 204: `drive_run63_four_charts.py` is a driver and does not enter `test_suite_identity`; `test_run63_four_charts.py` does. **Every suite printed a canonical `RESULT: n/n checks passed` line**; the new suite prints one, checked deliberately.

**Merge and push.** The gate status was **known and clean** before the merge.

```
git merge --no-ff run63-four-charts    ->  2e20c29c8f80bb81d5b3a8e2d5146dd87a9c108a
git push origin main                   ->  5fec302..2e20c29  main -> main
main == origin/main == 2e20c29
SIMULATION_VERSION = sim-2026.08-v41    participant package = og-participant-2026.08-v26
```

**Not one check was deleted.** Five checks in `test_run21_reset_disclosure.py` were **RETIRED**: they are kept in the file, readable, with the reason recorded in a `RUN63_RETIRED` block, and the suite **prints the retirement and its reason when it runs**. They pinned the since-the-reset window as the document source, which this run disproved by measurement. **This is a conflict between an earlier run's guard and your ruling, reported here as §1 requires and resolved in your favour.** Three replacements were added over the predicate that took its place, and the suite is green at 31/31.

## 12. Audit artifacts rewritten by the suites and restored

**28**, matching Run 62's measurement (Runs 58/59 measured 26; the handoff records 18). Restored by explicit `git checkout --` naming each path; **none committed**; `build_run37_acceptance.py` was run with `--out-audit <scratch dir>` throughout.

`code_audit/`: `run8_expectation_mutation_proof.csv`; `run9_abstention_results.csv`, `run9_alias_overlay_verification.csv`, `run9_fixture_import_results.csv`, `run9_known_answer_results.csv`, `run9_no_operational_effect.csv`, `run9_validator_gap_recomputations.csv`; `run10_dsm_known_answers.csv`, `run10_dsm_recomputation.csv`, `run10_module_identity.csv`, `run10_monte_carlo_convergence.csv`, `run10_monte_carlo_distribution_gap.csv`, `run10_monte_carlo_known_answers.csv`, `run10_monte_carlo_recomputation.csv`, `run10_no_operational_effect.csv`, `run10_validator_fault_injection.csv`; `run20_cycle12_100_reaudit.csv`, `run20_cycle12_guard_nonvacuity.csv`, `run20_cycle12_lineage_campaign.csv`; `run21_guard_nonvacuity_results.csv`; `run30_cat7_operational_execution.csv`; `run34_count_fault_injection_results.csv`, `run34_provenance_fault_injection_results.csv`; `run38_controlled_stimulus_execution_order.csv`, `run38_lock_integrity.csv`, `run38_participant_state_machine.csv`; `run39_launch_identity.csv`. Plus `server/tools/run17/coverage.csv`.

## 13. Incidental findings, unacted

1. **`signals.js:1260` says "The 15 supported document types"** above a `DROPZONE_REFERENCE` list of 15 labels, while the Signal Flow renders 27 from the server's own list. **The 27 is authoritative** — proved set-equal to `extraction_fields.DOC_TYPES`. Two surfaces describing one quantity from two sources; the second is a stale editorial list. **Not touched: it is not one of the four charts.**
2. **The Documents badge counts `events` as an extracted signal field.** `storedInputFields` excludes `sources` but not `events`, and `documents.py:1317` writes `si["events"]` onto the row, so `35 docs · 16 fields` describes 15 signal fields plus the event log.
3. **The Signal Web footnote reports only Red, Amber and Green** (`detail.js:449`), omitting Yellow and Complete, while the subtitle above it counts all five as "active". On this row and on yours they happen to agree; on a row carrying a Yellow or a Complete module they would not sum.
4. **The `d-projnet` collapsed badge reads `11 in service`** while the panel it heads says `63 modules · 11 categories`. The number is right for categories; the badge's wording matches the module badges beside it.
5. **`window.getModuleStatus` is defined twice and `categories.js` is not loaded at all** — confirmed: `index.html` loads `taxonomy.js` and never `categories.js`, so `categories.js:324` is dead in the browser, as carry-forward 10 records.
6. **`neural_flow.js` still keeps a worst-of fallback for the PROJECT rollup** (`:621`), reached only when `getProjectFusion` returns nothing, which happens only when there is no row at all — where every category is `None` and the answer is `None`. Honest, and left alone.

## 14. What the next session needs, as decisions for you

1. **The Executive Brief's recommendation does not read its own evidence.** Carry-forward 1, and you have named it as the next substantial run. Nothing in this run touched it.
2. **Three of the four charts are truthful and sparse. That is now measured, not asserted.** The decision in front of you is not a drawing decision: **do you want more of the 63 modules computing on PRJ-001, and if so which?** Three modules of 63 computed on a 35-document fixture and four on your 100-document project. Until that changes, these charts will keep looking like this, correctly.
3. **`Document risk: 0.00 (Green)` in key drivers** (carry-forward 2) is worth an early look — Run 44 fixed this class at `detail.js:1528` and it is back or was never gone on this path. Not started here; not in §5's scope.
4. **Whether the Signal Flow should also state the period's own evidence.** It now says "35 uploaded documents", which is the project's whole set and agrees with the Documents panel exactly as §8-2 requires. The row separately records that **17 of them** produced the current period's result, and that number is now available in the browser for the first time. Saying both would be more informative; saying it is a design choice, and it is yours.

---

## Carry-forward, unacted — not this run's work

1. **The Executive Brief's recommendation does not read its own evidence.** "Review the cost and schedule trend" and "meaningful risk" beside CPI Green, SPI Green, Document risk Green, on a page holding TCPI 1.036, VAC $200,478 over budget and a 22 per cent single-document disagreement. **The next substantial run.**
2. **`Document risk: 0.00 (Green)` still renders in key drivers** while the ledger shows Document Risk Score as No data. Run 44 fixed this class at `detail.js:1528`. **May be one line.**
3. **The head line renders `Reporting period:` blank.** `detail.js:1044`; `reportingPeriod` appears nowhere in `server/app/`.
4. **A panel renders the wall-clock month as a reporting period.** `signals.js:321-322`. **Confirmed live this run**: the Signal Web eyebrow read `Signal Sphere: August 2026` on a page holding period 2.
5. **"All required values present. Nothing outstanding" checks nothing at all** — `a_extractsignals` returns no `missing` key, so the sentence renders unconditionally for every project.
6. **Period Comparison says it unlocks after two reporting periods, with four loaded.**
7. **`projectcompute` declines when documents are unchanged.** A control saying "generate" must generate; Run 62 established nothing is lost by recomputing. Still unwritten.
8. **The three WebGL surfaces had never been measured under the real load order before Run 63.** They now have been, one at a time, and three of the four are correct.
9. **`workspace.py:174` reports `"period": 1` for every operational project.** A trap left armed.
10. **`window.getModuleStatus` is defined twice; `categories.js:324` is dead** and still reads the legacy signals blob. **Confirmed this run: `categories.js` is not loaded by `index.html` at all.**
11. **The pinned-ladder cascade is now the dominant cost of a mint.** Three passes this run; six suites reconciled purely because they pin the identity a mint advances.
12. **The suite population is 205**, up from 204: `test_run63_four_charts.py` enters `test_suite_identity`, `drive_run63_four_charts.py` does not.
