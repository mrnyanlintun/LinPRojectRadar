# Run 43H — Retirement Completion

**Date:** 2026-08-21
**Repository used:** the Linux clone at `/home/user/LinPRojectRadar` (section 4 asks which). The
Windows path is not reachable from this session and was not used.
**Interpreter:** no `.venv` exists in this clone. `server/run_all_suites.sh` falls back to the
`python3` on `PATH` by its own documented fallback, and every figure below came from that.
**Branch:** `claude/run43F-retirement-delink`, built on Phase F's tip `d951968`.
**Stamp minted:** `sim-2026.08-v28`. **Participant package minted:** `og-participant-2026.08-v14`.

---

## 0. The outcome, stated first

**Phase H is complete and merged.** 188 suites, **14,197 / 14,197**, 0 red, 0 aborting. The
successor freeze gate is **31/31** and its fifteen blocker classes report **0 blocked**. No stop
condition fired.

The 114 red checks and 8 aborting suites Phase F measured are closed. The count reconciles item by
item against the 188 / 14,176 baseline with nothing left over: **14,176 + 21 = 14,197**.

**One thing was NOT done and is reported rather than decided** — see section 5.3.4.

---

## 1. Section 3.2 — the sentence fixing group naming, quoted

From `NAMING_AUTHORITY.md` line 96:

> **Never use a module id or number in user-facing text.** No "Cat 4", no "1.7", no "PH.2", no
> "A4.2". Groups and purposes only. The old "Cat N" scheme is retired along with the names.

---

## 2. Section 5.1.1 — wrong population function. Every instance corrected

`registry_index()` and `load_registry()` resolve retired identifiers by design (`registry.py:426`,
`:402`). `service_index()` (`registry.py:440`) is the population in service. Every correction below
is a defect in the check, not a change to what it asserts.

| # | file | site | was | now |
|---|---|---|---|---|
| 1 | `test_run26_counts_and_wiring.py:183` | taxonomy vs registry | `registry_index()` | `service_index()` |
| 2 | `test_run32_client_authority.py:106` | runtime taxonomy identities | `load_registry()` | `service_index()` |
| 3 | `build_client_taxonomy.py:65` | the generator that emits BOTH client artifacts | `load_registry()` | `service_index()` |
| 4 | `test_run30_lineage_semantics.py:57` | `CAT7` population | `registry_index()` | `service_index()` |
| 5 | `test_run30_cat7_operational_route.py:83` | `CAT7` population | `registry_index()` | `service_index()` |
| 6 | `test_run32_method_class_agreement.py:187` | the live-consumer probe population | `sorted(VALIDATED)` | `set(VALIDATED) & set(service_index())` |
| 7 | `test_run3_adapter.py:321` | the fourteen's categories | `registry_index()` | `service_index()` |
| 8 | `test_simulation.py:48` | `available == validated` | `set(VALIDATED)` | `set(VALIDATED) − the retired set read from the CSV` |

Item 3 is the load-bearing one. `build_client_taxonomy.py` is the ORACLE of
`test_run32_client_authority`'s "editing either one by hand cannot silently fix or break
production" check: while the generator emitted the pre-retirement population, that check asserted
the pre-retirement population. With the generator deriving from `service_index()` it now
**reproduces Phase F's hand-delinked `taxonomy.js` and `categories.js` byte for byte**, so the
delinking is confirmed to be exactly what a derived generation produces, and a hand edit is still
caught.

Item 8's oracle is deliberately **not** `service_index()`, which would be asserting the function
under test against its own expression. The retired set is re-derived inside the check by reading
the `notes` column of `p0-baseline/module_renumbering_map.csv` directly.

**Positive control on the derivation.** Rewriting A2.5's `notes` cell in the CSV alone moved the
service roster to 64 and made the generator disagree with the committed artifacts immediately;
restoring the cell restored agreement. The population is derived from that one file and nothing
else.

---

## 3. Section 5.1.2 — genuine population assertions

Every update below satisfies both mandatory conditions. **Not one check was deleted**, and not one
assertion was weakened beyond removing its retired subject — in every case the retired subject was
replaced by the *stronger* statement that the module reaches no row at all, and the in-service
population kept everything it had.

### 3.1 The updates, and the failability proof of each

| suite | what it asserted | what it asserts now | fault injected | RED observed | restored |
|---|---|---|---|---|---|
| `test_run26_counts_and_wiring` | taxonomy == registry (101) | taxonomy == service (63), by SET not count | substitute `A2.5` for `C1.7` in `taxonomy.js` (63 vs 63) | 52/53 | 53/53 |
| `test_run32_client_authority` | runtime taxonomy == 101 identities; artifacts are generated | == 63 in service; artifacts are generated | same substitution | 16/18 | 18/18 |
| `test_run30_lineage_semantics` | all twenty B2 identities reach the ledger | the `len(CAT7)` in service reach it, derived | blank `_lineage_block` for `B2.18` | 27/35 | 39/39 |
| `test_run30_cat7_operational_route` | all twenty reach the ledger | those in service do, **and not one retired one does** | leak `B2.1`,`B2.9` into `available_modules()` | 48/50 | 50/50 |
| `test_run3_adapter` | all fourteen accounted for | the five in service are; the nine retired reach no row | leak `B2.1`,`B2.7` | 52/55 | 55/55 |
| `test_run16_material_cost_variance_disabled` | `A3.4` carries a `disabled: true` taxonomy row; ten such rows | `A3.4` carries NO row; **zero** disabled rows, derived | re-insert an `A3.4` disabled row in `taxonomy.js` | 77/79 | 79/79 |
| `test_run1_disable_and_relabel` | the eight disabled appear in the abstained list | they appear in NEITHER list | leak `DISABLED_CONCEPT_ONLY` into availability | 38/39 | 39/39 |
| `test_run20_cycle10_truthful_labels` | every labelled module is reached, carrying its truthful name | none is reached; no ledger row carries a truthful name | (a) leak `B4.1`,`A3.8`; (b) write a truthful name into every computed row | 52/53 both | 53/53 |
| `test_run8_retest_classify_27` | all 27 reached on the production path | those in service are; the retired reach nothing | (covered by the leak injections above) | — | 241/241 |
| `test_simulation` | `available == validated` (95) | `available == validated − retired`, from the CSV | (a) leak `A2.5` in; (b) drop `C1.7` out | 31/33, 32/33 | 33/33 |
| `test_run7_fix_now_defects` | `B4.7` absent from rows, present in abstentions | `B4.7` reaches neither, and is mentioned nowhere | leak `B4.7` | 288/290 | 290/290 |
| `test_six_fixes` | `B4.7`'s abstention row carries a reason and a code | `B4.7` reaches no row and is mentioned nowhere | leak `B4.7` | 22/24 | 24/24 |
| `test_courses_of_action` | `B4.7`'s silence recorded as an abstention with a structure code | `B4.7` reaches neither list; the structure-vs-figure distinction is asserted over the modules in service | leak `B4.7` | 30/32 | 32/32 |
| `test_documents_b7b` | `B4.7`'s silence recorded with a reason | `B4.7` reaches neither list; every in-service abstention still carries a reason | leak `B4.7` | 76/77 | 77/77 |
| `test_run4_validate_seven` | `A3.4` states "under review" on its row; `B4.7` recorded as an abstention | both reach no row | leak `A3.4`,`B4.7` | 239/241 | 241/241 |
| `test_run14_mismatch_remediation` | all eight mismatch modules accounted for | the six in service are; `A2.11`,`B2.19` reach nothing | leak `A2.11`,`B2.19` | 104/106 | 106/106 |
| `test_run10_synthetic_v03` | `A1.1`'s name read from `categories.js` | `A1.1`'s name read from the REGISTRY, and its ABSENCE from `categories.js` asserted | (a) corrupt `A5.4`'s name; (b) re-insert an `A1.1` row | 120/121 both | 121/121 |
| `test_run10b_canonical_integration` | the gainers are `SIX ∪ BUCKET_4` | those of them in service; the retired ones gain nothing on either run | leak `B2.19`,`A5.4` | 172/174 | 174/174 |
| `test_run20_lineage_declaration_truth` | every declared id runs on a project or across the portfolio | a third truthful disjunct — or is retired from service — **plus** a new check that a retired one runs on no project | leak `A1.1` | 191/192 | 191/191 |
| `test_run20_cycle12_reaudit` | `NOT_REACHED` is nought over the 100 targets | a new `RETIRED_FROM_SERVICE` outcome, **plus** two new checks that it cannot absorb an unreached module and cannot be dodged | (a) leak `A2.5`; (b) leak a PH key into the snapshot | 32/33 both | 33/33 |
| `test_run24_empty_project_diagram` | `(12,101,11,96)` literals | the same four figures DERIVED from `service_index()`, **plus** a new check that the registry is still 101 and reconciles | corrupt the knowledge-page figure | 51/52 | 52/52 |
| `test_run2_fifteen_defects` | `A1.1`,`B2.1`,`A2.5` abstain with named codes; three D1 identities land addressably | all six reach nothing; the snapshot states one reason in words | (a) leak all three; (b) leak a PH key | 248/257, 253/257 | 257/257 |
| `test_run32_defensibility_truth` | `B4.7`'s taxonomy row present and parseable | `B4.7` carries NO row; **and every name and method class IN SERVICE matches the registry** | (a) corrupt `C1.7`'s name; (b) re-insert a `B4.7` row | 55/56 both | 56/56 |
| `test_run32_method_class_agreement` | no module's status resolves to a silent null (over 95) | the same, over the 62 in service | rename `C1.7`'s method class in `taxonomy.js` | 34/36 | 36/36 |

### 3.2 Coverage per in-service module, before and after

The condition is that the coverage count for any module in service must not fall. It did not, and
in most suites it rose.

| suite | modules in service covered BEFORE | AFTER |
|---|---|---|
| the 8 suites that ABORTED (`run16`, `run20_cycle10`, `run30_cat7`, `run30_lineage`, `run33_portfolio_health`, `run34_holdout_provenance`, `run3_adapter`, `run8_retest_classify_27`) | **0** — a suite that prints no `RESULT:` line has not run, so it covered nothing | every in-service module in each suite's own population |
| `test_run26_counts_and_wiring` | 0 (the check was red) | 63, by set identity |
| `test_run32_client_authority` | 0 (red) | 63 identities, and the name / method-class / disabled loops iterate that same set — every id they reached before is an id present in `rows`, and `rows` IS the in-service set |
| `test_run32_defensibility_truth` | `B4.7` only, for name and method class | **all 63 in service**, for name and method class, in BOTH client artifacts. This is a strict increase: the retired subject's two checks were replaced by four that range over the whole roster in service |
| `test_run32_method_class_agreement` | 89 of 95 probed ids resolved; 6 resolved to null | 62, all resolving |
| `test_simulation` | 0 (red) | 62, each asserted present and each asserted not retired |
| `test_run20_lineage_declaration_truth` | 1 check per declared id | **2** checks per declared id |
| `test_run20_cycle12_reaudit` | 100 rows, 1 execution-outcome check | 100 rows, 3 execution-outcome checks |
| `test_run30_cat7_operational_route` | 0 (aborted) | `B2.18` covered by all eight CAT7 checks, plus 2 new retirement checks |
| `test_run3_adapter` | 0 (aborted) | `B1.1`–`B1.4`, `B3.1` covered by every population check |
| every remaining suite | unchanged | unchanged |

**Not one in-service module lost a check.** Stop conditions 7.1, 7.2 and 7.3 did not fire.

---

## 4. Section 5.2 — the six Portfolio Health suites

All five Group D identities are retired from service, `live_portfolio_modules()` returns `()`, and
the dispatcher returns a retired snapshot. The offload is complete.

**The scientific oracles were NOT lost.** `canonical_v8` is untouched and still computes; the
Run-33 supplied oracles — the PH.2 mid-rank percentile `7/8`, the cohort-membership rule — are now
executed **against the library directly** rather than through a dispatcher that no longer reaches
it. That is a change of route, not of assertion, and it was proved by injection: perturbing
`canonical_v8`'s percentile numerator turned the supplied oracles red.

| # | suite | before | after | what it asserts now |
|---|---|---|---|---|
| 1 | `test_run33_portfolio_health` | ABORTED (`KeyError: 'cat8_2_portfolio_outlier'`) | **150/150** | the dispatcher assembles no cohort and computes nothing; the PH.2 oracle holds against `canonical_v8`; the snapshot is stamped `retired`, non-voting, creating no evidence; with no cohort it answers the same way it answers with one |
| 2 | `test_run34_holdout_provenance` | ABORTED (generator `KeyError`) | **53/53** | the D2 probe reads the LIVE route, finds no reading and no permitted flag, and decides on what it finds |
| 3 | `test_run34_count_fault_campaign` | 14/26 | **26/26** | its own five-fault campaign runs green-red-green |
| 4 | `test_run34_provenance_fault_campaign` | 7/26 (5 crashes) | **26/26** | same; 0 crashes accepted as RED |
| 5 | `test_period_series` | 42/46 | **46/46** | one snapshot produces no portfolio reading at all; no identity is addressable; the snapshot says why once, in words |
| 6 | `test_workspace_t3t5` | 74/79 | **79/79** | a second project cannot manufacture a portfolio reading either; the server's own retirement reason is present unmodified; the snapshot is non-voting and creates no project evidence |
| + | `test_run34_parameter_count_closure` | 50/51 | **51/51** | the artifact generator runs cleanly |

Failability proved on 5 of the 6 by leaking a `cat8_*` key into `_retired_snapshot`'s `results`
(each went red and restored), and on `test_workspace_t3t5` additionally by emptying the retirement
sentence. Suites 3 and 4 carry their own internal fault campaigns, which are their failability
proof of record.

Two **generators** had to move with them, and both are recorded in the manifest at
`server/tools/run43_production_changes.py`: `build_run34_artifacts.py` (the per-identity abstention
reason becomes the snapshot's own single reason) and `run34_ph1_tree_count_calibration.py` (the D2
probe reads an empty dict rather than an abstaining row, which yields the same two answers).

---

## 5. Section 5.3 — the post-removal population on the surfaces

### 5.3.1 The populations, verified against `service_index()` rather than trusted

The prompt's figures are corrected where they differ. **`B2` falls to 1, not 4.**

| group | registered | in service | prompt said |
|---|---|---|---|
| A1 | 11 | 10 | — |
| **A2** | 11 | **6** | 11 → 6 ✓ |
| A3 | 9 | 7 | — |
| A4 | 10 | 10 | — |
| A5 | 8 | 7 | — |
| A6 | 4 | 4 | — |
| B1 | 4 | 4 | — (all four HELD) |
| **B2** | 20 | **1** (`B2.18` only) | 20 → 4 ✗ — **the correct figure is 1** |
| B3 | 5 | 5 | — |
| **B4** | 7 | **2** | 7 → 2 ✓ |
| C1 | 7 | 7 | — |
| **D1** | 5 | **0** | 5 → 0 ✓ |
| **total** | **101** | **63** | |

A second measured fact the prompt does not state: **every one of the ten modules in
`DISABLED_MODULES` is also retired**, so `DISABLED_MODULES ∩ service_index() = ∅` and the client
taxonomy now flags **zero** entries disabled.

### 5.3.2 The stylesheet, item by item against section 5.3's five headings

`assets/css/radar.css` is the only stylesheet.

| # | in scope | measured | changed |
|---|---|---|---|
| 1 | rules selecting retired modules or their categories | **none.** Searched every one of the 38 identifiers as a whole token in three casings (`A2.5`, `a2_5`, `a2-5`): 0 hits. The stylesheet selects by role class (`.cat8-flagged-row`, `.li-state`), never by module identity | nothing — a rule that selects nothing cannot be proved to do anything, and there was no such rule to remove |
| 2 | grid and column definitions sized for the old counts | **none.** Every grid is `1fr 1fr`, `auto-fit minmax(...)` or a named-track layout. Not one is a count of modules or categories | nothing |
| 3 | spacing, gaps, empty regions where removed rows sat | **none.** Rows are emitted per module by the renderers; with fewer modules the flex/grid containers close up. No fixed heights or `nth-child` rules keyed to a population were found | nothing |
| 4 | any panel whose population fell to zero | **one: the Portfolio Health flyout.** See 5.3.4 — **reported, not changed** | nothing |
| 5 | any count, legend or label naming a pre-removal figure | **three, all outside the stylesheet, in its adjacent markup** | see below |

### 5.3.3 The three counts corrected, per surface

| surface | rendered BEFORE | renders NOW | what was changed |
|---|---|---|---|
| **About panel** (`index.html:929`, `:941`) | "The analytical layer is 101 registered modules… 96 of the 101 run on a single project; the other 5 are Portfolio Level" and "computes 100 of the 101 registered modules. Both figures are correct" | "101 registered modules… of which 63 are in service. All 63 in service run on a single project; the Portfolio Level modules are not in service." and "The registry holds 101 modules and 63 of them are in service. The analytical server computes 62 of the 63… All three figures are correct" | two paragraphs of prose. **No control touched.** Both figures are derived and asserted by `test_run26_counts_and_wiring` against `registry_index()`, `service_index()` and `available_modules()` |
| **Knowledge page** (`knowledge.js:554`, `:600`, `:2439`) | "The registry holds 101 modules: 96 at project level and 5 at portfolio level. The analytical server computes 100 of the 101" | "The registry holds 101 modules, of which 63 are in service: 63 at project level and 0 at portfolio level. The analytical server computes 62 of the 63… The 38 modules not in service were retired at Run 43; they keep their registry entries and their audit lineage, and they compute nothing and appear on no participant surface." The reference list's "100 modules, 95 at project level and 5 Portfolio Health" is now unqualified | three sentences. Asserted by `test_run24_empty_project_diagram` against the derived figures |
| **Project detail page** (`detail.js:18`) | the `LIN_CATEGORIES` comment said "the whole taxonomy: Group A 53 modules… Group D 5, across twelve categories" — false once `LIN_CATEGORIES` became the roster in service | "the taxonomy IN SERVICE, across twelve categories. The REGISTRY holds 101… Run 43 retired 38 of them from service… Group D… All five are now retired from service as well, so the category renders with no module rows at all" | one comment block. It is the only comment on that page that explains why every count on it uses `projectCats()`; leaving it saying "the whole taxonomy" would have made a participant-facing file state a falsehood about itself |

Renderers, category population and module rows needed no change at all: they all read
`LIN_CATEGORIES`, and `LIN_CATEGORIES` is generated from `service_index()`.

### 5.3.4 THE ONE CORRECTION NOT MADE, reported as section 5.3 requires

**The Portfolio Health flyout states a false reason, and correcting it moves a sequence-bearing
participant file. It was reverted and is reported instead.**

`assets/js/deepdive.js:2373` renders the flyout when no Portfolio Health data is present:

```js
const reason = data.projectCount < 3
  ? "Portfolio Health needs at least 3 projects with computed signals to compare against the population: " + data.projectCount + " loaded."
  : "Portfolio Health hasn't run yet for the current portfolio.";
```

After the offload no project's stored result carries a `D1` method class, so `anyData` is always
false and this panel tells a participant that Portfolio Health needs more projects. **No number of
projects would make it compute.** This is exactly section 5.3's item 4.

A correction was written and verified — a `cat8Retired()` predicate derived from `LIN_CATEGORIES`
(true with the live taxonomy, false with no taxonomy loaded, false if a Portfolio Health module is
reinstated), selecting the server's own sentence. **It was then reverted**, because
`assets/js/deepdive.js` is one of the six files in `participant_packages.SEQUENCE_BEARING_FILES`,
and every participant-package record since v10 and the freeze gate's B04 blocker assert that those
six are byte-identical across a successor. Section 5.3 authorises styling and layout; it does not
authorise moving a byte in the participant sequence, and doing so silently would break the
strongest invariant this instrument holds.

**This is a decision for the owner.** The panel is reachable and it is wrong.

### 5.3.5 Browser verification, and the `cwd` of the session

The application was served from `/home/user/LinPRojectRadar/server` on `127.0.0.1:8099` against a
throwaway migrated SQLite database in the scratchpad. **Production Postgres was not contacted.**
The Chromium session's working directory was **`/home/user/LinPRojectRadar`**, and
`window.confirm` was forced to return false.

**The application under test is the right one.** Section 4.3's tell was checked directly: the DOM
carries **7 `.page` sections** (`portfolio`, `detail`, `project`, `auditor`, `training`,
`handbook`, `admin`) and **zero** `api.js` or `boot.js` in `document.scripts`. `DEng\Demo` was not
served.

Read from the running page, not from source:

```
taxonomy categories                 12
taxonomy module ids                 63
sorted(ids) == sorted(service_index())   True
retired identifiers in the taxonomy      []   (all 38 checked)
retired identifiers in the rendered text []   (all 38 checked)
per category  A1 10  A2 6  A3 7  A4 10  A5 7  A6 4  B1 4  B2 1  B3 5  B4 2  C1 7  D1 0
empty categories                    ['D1']
project-level categories / modules  11 / 63
cat8Retired() derived in the page   true
About panel, verbatim from the DOM:
  "The registry holds 101 modules and 63 of them are in service. The analytical server
   computes 62 of the 63... All three figures are correct: 101 is what the platform has
   registered, 63 is what is in service, and 62 is what it computes."
  "101 registered modules, organised into four groups, of which 63 are in service.
   All 63 in service run on a single project; the Portfolio Level modules are not in service."
page errors                         none (CSP meta-tag notice and one pre-existing SVG
                                    attribute warning only, both present before this run)
```

**Stop condition 7.9 did not fire: no retired module is reachable on a participant surface.**

**What the browser could NOT reach.** The Knowledge page body renders only inside an authenticated
participant session and its module array is local to `knowledge.js` rather than exposed on
`window`; calling `LinKnowledge.renderKnowledgePage` into a detached node produced no text. Its
corrected figures are guarded at source instead, by `test_run24_empty_project_diagram` and
`test_run26_counts_and_wiring`, both of which derive the expected figures rather than quoting the
sentence. This is the same limitation `test_run32_defensibility_truth` records for that surface.

---

## 6. Section 5.4 — the freeze gate, row by row

**31/31, and the fifteen blocker classes report 0 blocked.** Phase F left it at 24/30.

| row | verdict | cause, and what reconciled it |
|---|---|---|
| `run37.gate.generator_runs` | PASS | — |
| `run37.gate.reproduces` | PASS | the committed gate now reproduces from the tree |
| `run37.gate.B01` dirty candidate identity | PASS | **reconciled.** A pinned byte-identity manifest falsified by this retirement's edits: 11 content-addressed group digests recomputed from the tree. A `run43_freeze_candidate_identity.json` was minted at the candidate commit, naming the v27 identity as its parent, which is untouched. The member lists of the two globbed groups are re-derived from the filesystem, and a new `service_roster_digest` group measures the retirement authority itself — the registry CSV — so a freeze that did not measure it could not be measuring the retirement |
| `run37.gate.B02` … `B10`, `B12` … `B15` | PASS | never fired |
| `run37.gate.B11` package or predecessor mutation | PASS | **reconciled — the one row section 5.4 names.** Five of the seventy governed participant bytes moved, so `og-participant-2026.08-v14` was minted and `v13` pinned to commit `428a6c6`. The generator's hardcoded `v13` filename was replaced by `PP.CURRENT.record`: hardcoding a superseded record makes the blocker measure a predecessor and stop measuring the package a participant actually receives |
| `run37.gate.blocking_defects_zero` | PASS | consequence of B01 and B11 |
| `run37.gate.predecessor_release_preserved` | PASS | the v25 record still says v25 |
| `run37.gate.immediate_predecessor_release_preserved` | PASS ×2 | now checks **every** predecessor: the v26 record still says v26 and the v27 record still says v27. Checking only the oldest would let the most recent be quietly rewritten |
| `run37.gate.no_release_while_blocked` | PASS | consequence |
| `run37.gate.release_present_when_clean` | PASS | record, report and checksum manifest all exist |
| `run37.gate.limitation_stated` ×4 | PASS | carried forward verbatim from the predecessor |
| `run37.gate.disposition` | PASS | `FINAL_FREEZE_ACCEPTED` and the gate agrees |
| `run37.gate.no_self_reference` | PASS | **re-anchored.** The record must now name RUN 42's candidate (`07dccf7`) as its parent, not Run 41's. Named explicitly rather than loosened to "any commit" |

**No gate row was disabled, weakened, widened or bypassed.** Every row that failed did so because a
pinned byte-identity manifest was falsified by an edit this retirement made, which is the class
section 5.4 permits reconciling. **No row failed for any other reason, so the section 5.4 stop did
not fire.**

### 6.1 The other manifests in the same class

| manifest / guard | how it was falsified | how it was reconciled |
|---|---|---|
| `code_audit/run20_production_freeze.sha256` declared-changes guard | `research_export.py` and `training.py` differed and no manifest declared them | **new** `server/tools/run43_production_changes.py`, following the Run-28→42 precedent. `portfolio_health.py` is NOT declarable there and the reason is recorded in that file: it was CREATED by Run 33, so it is outside the Run-20 baseline list the guard's own scope is defined by. Proved failable by removing `training.py` from the manifest — red |
| `production_tree.PINNED` | eleven production files moved | **new** `code_audit/run43_production_tree.sha256`; the run42 manifest is kept addressable as its parent, not rewritten |
| the v13 participant package record | five of seventy bytes moved | **new** `code_audit/run43_participant_package_v14_checksums.sha256`, 70 files, same inventory; v13 pinned to its commit |
| `test_run6_known_answer` / `test_run8_retest_classify_27` pinned-baseline scopes | `training.py` | `training.py` NAMED in each run's scope set, not the comparison widened |
| `test_run10_state_protection` analytical-layer scope | `research_export.py`, `training.py` | both NAMED; neither performs any computation — both change only WHICH modules are enumerated |
| `test_run38` / `test_run39` frozen-immutability scopes | eleven files, the stamp, the package | three named sets added (`RUN43_AUTHORISED_MANIFEST_CHANGES`, `RUN43_AUTHORISED_SUCCESSOR_CHANGES`, the permitted-modification list). Anything outside them still fails |
| `test_run25_rail_removal` pinned-manifest chain | the pin moved | `run43_production_tree.sha256` appended to the accepted chain |
| `test_run2_fifteen_defects` `detail.js` pinned diff | the `LIN_CATEGORIES` comment | the allowance is **confined to that one comment block**, identified by its own opening line in each file rather than by a list of sentences. Proved failable: adding a `//` comment is still excused (it always was), but changing `projectModuleCount()` to `return 99` turns it red |

---

## 7. Section 5.5 — the check count, reconciled item by item

Both figures measured on this machine with the same runner, the baseline in a `git worktree` at
`f461630`.

| tree | suites | checks | red | aborting |
|---|---|---|---|---|
| `f461630`, in a worktree | 188 | **14,176 / 14,176** | 0 | 0 |
| Phase F tip `d951968` | 188 | 13,326 / 13,440 | 114 | 8 |
| **Phase H head** | **188** | **14,197 / 14,197** | **0** | **0** |

Against the 14,176 baseline the delta is **+21**, and every suite that moved is accounted for:

| suite | baseline | now | Δ |
|---|---|---|---|
| `test_run30_cat7_operational_route` | 67 | 50 | **-17** |
| `test_run7_fix_now_defects` | 291 | 290 | **-1** |
| `test_courses_of_action` | 31 | 32 | **+1** |
| `test_documents_b7b` | 76 | 77 | **+1** |
| `test_run10b_canonical_integration` | 173 | 174 | **+1** |
| `test_run20_cycle10_truthful_labels` | 52 | 53 | **+1** |
| `test_run24_empty_project_diagram` | 51 | 52 | **+1** |
| `test_run26_counts_and_wiring` | 53 | 54 | **+1** |
| `test_run33_portfolio_health` | 149 | 150 | **+1** |
| `test_run37_freeze_gate` | 30 | 31 | **+1** |
| `test_run2_fifteen_defects` | 255 | 257 | **+2** |
| `test_run3_adapter` | 53 | 55 | **+2** |
| `test_simulation` | 31 | 33 | **+2** |
| `test_map_and_module_count` | 72 | 75 | **+3** |
| `test_run20_cycle12_reaudit` | 30 | 33 | **+3** |
| `test_run28_participant_packages` | 78 | 84 | **+6** |
| `test_run20_lineage_declaration_truth` | 178 | 191 | **+13** |

Sum of the deltas: **+21**. 14,176 + 21 = **14,197**. The reconciliation closes exactly, with
nothing left over, and no suite moved that is not in the table.

Why each one moved, so no figure is a residual:

- **−17 `test_run30_cat7_operational_route`.** Nineteen of the twenty Category-7 identities are
  retired. Its per-identity loops (section 2's route trace, section 4's disposition sweep) emit one
  check per identity, so nineteen fewer are generated. Two new checks were ADDED — the registered
  population is still twenty, and not one retired identity reaches the ledger — so the arithmetic is
  −19 generated + 2 added = −17.
- **−1 `test_run7_fix_now_defects`.** `B4.7` carried three checks (absent from rows, carries its
  reason, carries its code). A module that reaches no row cannot carry a reason or a code, so those
  three become two: it reaches neither list, and it is mentioned nowhere in the served result.
- **+13 `test_run20_lineage_declaration_truth`.** One new check per declared id: if it is retired
  from service it runs on no single project.
- **+6 `test_run28_participant_packages`.** The v14 link's own six checks.
- **+3 `test_map_and_module_count`.** Phase D's sanctioned change, carried forward unaltered.
- **+3 `test_run20_cycle12_reaudit`.** Two new re-audit checks on the `RETIRED_FROM_SERVICE`
  outcome, plus one on what the PRODUCTION portfolio route emits.
- **+2 `test_simulation`.** The retired set is now read from the CSV (one check) and the
  no-retired-module-is-available assertion is separated out (one check).
- **+2 `test_run3_adapter`.** The retired nine reach no row (one), and no concept-only identity
  still in service computes (one).
- **+2 `test_run2_fifteen_defects`.** The retired members of the fifteen reach nothing (one), and
  the portfolio snapshot states its reason once (one).
- **+1 each** in `test_courses_of_action`, `test_documents_b7b`, `test_run10b_canonical_integration`,
  `test_run20_cycle10_truthful_labels`, `test_run24_empty_project_diagram`,
  `test_run26_counts_and_wiring`, `test_run33_portfolio_health`, `test_run37_freeze_gate` — one
  added assertion each, named in the tables above.

---

## 8. Section 5.6 — freeze and merge

1. **`sim-2026.08-v28` minted** at `server/app/simulation/models.py:475`, with the boundary
   recorded above it. `SIMULATION_VERSION_SUPERSEDED` advances to `sim-2026.08-v27`, and v28 is
   APPENDED to `SIMULATION_VERSION_HISTORY` — nothing was edited or removed, so every earlier stamp
   remains the audit baseline for results computed under it. **No check was removed from the
   authorised change set**; three were added to it (`RUN43_AUTHORISED_*`).
2. **Every gate re-run and reported** at section 6.
3. **Merged to `main`.** The count correction and the retirement are preserved as distinct commits:
   `776f130` (Run 43D, the sanctioned `test_map_and_module_count` change) and `7dc6053` / `0206892`
   (the retirement itself) are unaltered on the branch.
4. This report, the decision record and `T6_HANDOFF.md` are updated.

---

## 9. Section 6 — the seventeen Phase H tests

| # | test | verdict | how |
|---|---|---|---|
| 1 | `run_module()` over all 101 identifiers is byte-identical to `f461630`, 0 diff lines | **PASS** | Phase F's harness, re-run: 0 diff lines over 101 identifiers on two fixtures. Proved failable at 1,530 diff lines by re-injecting a short-circuit, and restored to 0 |
| 2 | no retired module is linked to any category | **PASS** | 0 of 38 present in `taxonomy.js`, `categories.js` or the live `window.LIN_CATEGORIES` |
| 3 | no retired module in the rollup, project status, category population, participant surfaces, brief, decision card, courses of action, export or browser taxonomy | **PASS** | asserted by the updated suites and re-measured in the browser: 0 of 38 in the rendered text |
| 4 | modules in service is 63, derived | **PASS** | `service_index()` = 63; the browser taxonomy = 63; the two are set-equal |
| 5 | registry total is 101, derived | **PASS** | `registry_index()` = 101; 63 + 38 = 101 asserted in `test_run24` |
| 6 | `taxonomy.js` and `service_index()` agree at 63 | **PASS** | set equality, not count equality — proved failable by an equal-count substitution |
| 7 | no module in service changed its computed result | **PASS** | subsumed by test 1 |
| 8 | coverage per in-service module did not fall | **PASS** | section 3.2 |
| 9 | every updated check proved able to fail | **PASS** | section 3.1 and section 4 |
| 10 | voting is exactly 2, `A1.7` and `A1.8` | **PASS** | `test_run37_freeze_gate` B09 zero; `test_run26` section 7 |
| 11 | Group C does not contribute to project status | **PASS** | `contributes_to_project_status`: A True, B True, C False, D False |
| 12 | all four B1 modules reachable from `research_export.py` | **PASS** | `B1.1`–`B1.4` all in service, all present at `research_export.py:350`, all four reached in `test_run3_adapter` |
| 13 | Portfolio Health computes nowhere | **PASS, with a stated qualification** | `live_portfolio_modules()` returns `()`; the dispatcher returns a retired snapshot; no production path reaches a portfolio computation. **The superseded v20 route `portfolio.compute_portfolio` still computes and is preserved deliberately** — it is reachable from no production path (`portfolio_health.py:14`, `documents.py:1556`), exactly as the 38 retired formula functions are preserved and unreachable. `test_run20_cycle12_reaudit` now asserts both halves separately so the preserved route cannot be mistaken for a live one |
| 14 | `models_sim.py` byte-identical to `f461630` | **PASS** | `git diff f461630 HEAD -- server/app/simulation/models_sim.py` is empty |
| 15 | all 188 suites run, none aborts | **PASS** | 188 suites, every one printing a canonical `RESULT:` line |
| 16 | every affected surface renders correctly, verified in a browser | **PASS, with one surface unreachable** | section 5.3.5. The Knowledge page body could not be reached from an unauthenticated session and is guarded at source instead |
| 17 | the successor freeze gate passes 30/30 | **PASS at 31/31** | the gate grew by one check this run (the second predecessor-release assertion), so 30/30 became 31/31 |

---

## 10. Section 7 — the stop conditions

| # | condition | verdict |
|---|---|---|
| 7.1 | an update would reduce what is asserted about any module in service | **not fired** — section 3.2 |
| 7.2 | the coverage count for any in-service module falls | **not fired** |
| 7.3 | an updated check cannot be proved able to fail | **not fired** — every one was proved |
| 7.4 | any check must be deleted | **not fired** — none was |
| 7.5 | `run_module()` differs from `f461630` | **not fired** — 0 diff lines |
| 7.6 | any module in service changes its computed result | **not fired** |
| 7.7 | a layout correction would require adding, moving or removing a control | **not fired** — no control was touched. The one correction that could not be made (section 5.3.4) was blocked by the participant-sequence invariant, not by a control |
| 7.8 | a gate row fails for a reason other than a falsified byte-identity manifest | **not fired** — every failing row was that class |
| 7.9 | a retired module reachable on a participant surface after the CSS update | **not fired** — 0 of 38, measured in the browser |

---

## 11. The self-rewriting audit artifacts

The full-suite run rewrote **18** artifacts, one of them outside `code_audit/`. Phase D reported
18, Phase F observed 17; this run observed 18 and the difference is stated rather than reconciled
with a guess — two of them (`run30_cat7_operational_execution.csv` and
`run8_expectation_mutation_proof.csv`) are written by suites that ABORTED under Phase F and
therefore never reached their write, and `run39_launch_identity.csv` now records the new stamp.

```
code_audit/run10_no_operational_effect.csv          code_audit/run9_abstention_results.csv
code_audit/run20_cycle12_100_reaudit.csv            code_audit/run9_alias_overlay_verification.csv
code_audit/run20_cycle12_guard_nonvacuity.csv       code_audit/run9_fixture_import_results.csv
code_audit/run20_cycle12_lineage_campaign.csv       code_audit/run9_known_answer_results.csv
code_audit/run21_guard_nonvacuity_results.csv       code_audit/run9_no_operational_effect.csv
code_audit/run30_cat7_operational_execution.csv     code_audit/run9_validator_gap_recomputations.csv
code_audit/run38_controlled_stimulus_execution_order.csv
code_audit/run38_lock_integrity.csv                 server/tools/run17/coverage.csv  <-- outside code_audit/
code_audit/run38_participant_state_machine.csv
code_audit/run39_launch_identity.csv
code_audit/run8_expectation_mutation_proof.csv
```

**All 18 were restored with `git checkout --`. None was committed.** The `f461630` worktree was
likewise dirtied during the baseline run and was removed afterwards.

---

## 12. Incidental findings, unacted

1. **The Portfolio Health flyout states a false reason.** Section 5.3.4. Reported, not changed.
2. **`available_modules()`'s docstring is stale.** `registry.py:461` still says a retired id
   "is refused with its stated retirement reason rather than computed". Phase F withdrew that
   refusal, so the sentence is now false — `run_module()` on a retired id computes exactly what it
   computed at v27. Left alone because correcting it moves `registry.py`, which is inside a frozen
   surface, for a comment. It should be corrected under the next stamp.
3. **`ds_defensibility_data.js` and `ds_defensibility_evidence.js` still carry rows for retired
   identifiers** (10 and 34). They are keyed lookups, nothing renders from them, and
   `test_run32_client_authority` is green because it checks the two TAXONOMY artifacts. Phase F
   recorded this; it is unchanged.
4. **`portfolio.compute_portfolio` still computes all five Group D readings.** Deliberate and
   unreachable — see test 13 — but a reader who called it directly would get five readings for
   modules that are retired.

---

## 13. What the next session needs, as a decision for the owner

Stated as decisions, not recommendations, and not ranked.

1. **The Portfolio Health flyout's reason sentence.** Correcting it moves `deepdive.js`, a
   sequence-bearing participant file. Either the owner accepts a participant-package successor that
   moves one sequence-bearing file for a text correction, or the panel keeps a sentence that is
   false. The correction is written and verified; it is one instruction away.
2. **`available_modules()`'s stale docstring.** A one-line comment correction inside a frozen
   surface, which needs its own authorisation.
