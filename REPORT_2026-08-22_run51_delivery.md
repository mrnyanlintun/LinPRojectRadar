# Run 51: the delivery of what Run 50 stopped on. MERGED.

**Date:** 2026-08-22. **Repository:** the Linux clone at `/home/user/LinPRojectRadar` (the Windows
path `C:\Users\NTUN\OneDrive - Arora Engineers, LLC\DEng\LinPRojectRadar` was not used).
**Interpreter:** the documented fallback, `python3` **3.11.15** at `/usr/local/bin/python3`; this
clone carries no `.venv`, so `server/run_all_suites.sh` falls through to the interpreter on PATH,
which is what it is written to do.

**Branch:** `run51-delivery`, rooted at `ad4f614`, **merged to `main` with `--no-ff` and pushed.**
**Stamp:** `sim-2026.08-v34`. **Package:** `og-participant-2026.08-v19`.
**Behaviour digest:** `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1` —
**unchanged**, reproduced live from the current tree by the gate's B15 row at every mint.

**No run-level stop condition at §10 fired.** Three items were stopped locally under §9; each is
named at section 8 below, and the run continued and merged, as §1 of the order directs.

**Browser sessions** were run from a clean subdirectory,
`/tmp/.../scratchpad/run51work/clean`, never the scratchpad root, and the driver printed that
cwd. The `DEng\Demo` tell was checked before anything was measured: **7 `.page` sections, and
neither `api.js` nor `boot.js` in `document.scripts`.** Chromium 1194 was driven through
Playwright 1.48 with an explicit `executable_path` and `--headless=new`.

**Run 50's report and browser driver were carried forward onto this branch and the driver was
taken forward rather than rewritten**, as `server/tools/drive_run51_browser.py`.

---

## 1. Every count corrected, and whether it now derives

The order's §6.1 requires a sweep of every hard-coded count of modules or categories in
`assets/`, a verdict on each, and a correction of every typed one to derive. **Every sweep in
this run reads SVG `<text>` nodes explicitly.**

| # | site | before | typed or derived | after | derives now? |
|---|---|---|---|---|---|
| 1 | `knowledge.js:585` (now `:623`) | *"the project's **96** registered modules"* | **TYPED. This is the number the owner saw.** | *"the **${taxCounts().inService}** modules in service"* → renders **63** | **YES** |
| 2 | `knowledge.js:554` (now `:592`) | *"101 registered modules, of which 63 are in service … computes 62"* | TYPED, and correct | `${taxCounts().registered}` / `${taxCounts().inService}` / `${taxCounts().serverComputes}` | **YES** |
| 3 | `knowledge.js:579` (now `:617`) article title *"Why 101 registered modules across four groups"* | TYPED, and correct | `` `Why ${taxCounts().registered} registered modules across four groups` `` | **YES** |
| 4 | `knowledge.js:600` (now `:638`) | *"registry holds 101 … 63 in service: 63 at project level and 0 at portfolio level … computes 62 of the 63 … 38 retired"* | TYPED, and correct | five derived tokens: `registered`, `inService`, `projectInService`, `portfolioInService`, `serverComputes`, `retired` | **YES** |
| 5 | `knowledge.js:417–419` **SVG accessible name** | *"Signal stack of **10 categories** and Portfolio Health"* | **TYPED, AND WRONG: eleven project categories are in service** | *"Signal stack: `${taxCounts().inService}` modules in service across `${taxCounts().projectCategories}` project categories"* → renders **63 / 11** | **YES** |
| 6 | `index.html:929` About page | *"101 registered modules … 63 are in service"* | TYPED | `<span data-taxcount="registered">` / `<span data-taxcount="inService">` | **YES** |
| 7 | `index.html:941` About note | *"registry holds 101 … 63 … computes 62 of the 63 … all three figures are correct"* | TYPED | seven `data-taxcount` spans | **YES** |
| 8 | `ds_defensibility_data.js:13` | *"(100 registered computations, plus one value the extraction model supplies)"* | TYPED | *"({{registered}} registered computations, of which {{supplied}} is a value the extraction model supplies)"* → renders **101 / 1** | **YES** |
| 9 | `neural_flow.js:1179` Signal Flow summary strip | *"the platform's **registered architecture**: 27 supported document types, 63 **registered** project modules and 11 **registered** categories"* | the three NUMBERS were already derived from the built model; **the WORD beside them was wrong** — the model is the population IN SERVICE, not the registry | *"the **analytical architecture in service**: 27 supported document types, 63 project modules **in service** and 11 categories **in service**"* | **YES**, and the word is now true |
| 10 | `neural_flow.js:1384/1400/1405` toggle button | *"Show / Hide the **registered** architecture"* | TYPED word | *"Show / Hide the **architecture in service**"* | n/a, no count |
| 11 | `detail.js:1080/1081/1084` section badges | `11 registered`, `63 registered`, `63 registered` | numbers derived, **word wrong** | `11 in service`, `63 in service`, `63 in service` | **YES** |
| 12 | `taxonomy.js` / `categories.js` | no counts shipped | — | **NEW, GENERATED:** `window.LIN_TAXONOMY_COUNTS = { registered: 101, inService: 63, retired: 38, serverComputes: 62, supplied: 1 }` | **YES** — written by `build_client_taxonomy.py` from `registry_index()`, `service_index()` and `REG.VALIDATED` |

**How the derivation works, so it cannot rot.** `server/tools/build_client_taxonomy.py` counts
`len(registry_index())`, `len(service_index())` and the subset of the roster in service that has a
production runner, and emits them into the generated block of BOTH client mirrors. `knowledge.js`
gains `taxCounts()`, which reads that object and additionally COUNTS the loaded taxonomy for the
in-service and category figures, and `fillCounts()`, which substitutes `{{token}}` in any curated
string. `app.js` gains `fillTaxCounts()`, which fills every `data-taxcount` span in static HTML. A
retirement rewrites every sentence on both surfaces with no edit to either file.

**Where a count was typed and CORRECT and is left stating the registry** (the honest converse):
`knowledge.js`'s three registry sentences and the About page's two are ABOUT what the platform
registers, so 101 is the right population there; they are now derived rather than typed, but the
population they name is unchanged. Gate row **B02** measures the registry deliberately and is
unchanged.

**Read back from the rendered DOM.** The handbook probe clicked all **51** topics, rendered all
51, read **799,810 characters** of `innerText` plus **34 SVG text nodes** and **6 accessible
names**, and:

* `"96 … modules"`, `"100 … modules"`, `"103 … modules"` — **absent**;
* `"101 registered modules, of which 63 are in service"` — **present** (the non-vacuity positive);
* `"101 registered modules"` and `"63 are in service"` — **both present**;
* every `data-taxcount` span on the About page **resolved to a digit**, and each matched the
  number `registry_index()` and `service_index()` returned in the driver's own process:
  `registered 101`, `inService 63`, `serverComputes 62`, three times over.

---

## 2. The handbook, before and after, including its SVG

**Before, as Run 50 measured it in the rendered DOM:**

* article *"Why 101 registered modules across four groups"* stated, in its own body, *"The
  analytical layer runs the project's **96 registered modules** in milliseconds"* — a typed
  literal, and the number the owner saw;
* the neighbouring articles at `:554` and `:600` stated **101 registered / 63 in service**
  correctly, which is why one page was right in one paragraph and wrong in the next;
* the **Signal Stack SVG** at `:417–419` drew **ten visible identifier chips** —
  `01 EVM`, `02 CUSUM`, `03 Doc Risk`, `04 Synthesis`, `05 ABM`, `06 PERT`, `07 LOB`, `08 CCPM`,
  `09 RCF`, `10 DSM` — and carried the accessible name *"Signal stack of **10 categories** and
  Portfolio Health feeding the governance decision"*, where **eleven** project-level categories
  are in service. **No sweep before Run 50 reached it, because SVG `<text>` is not in
  `innerText`.**

**After, read back from the rendered DOM by `drive_run51_browser.py`:**

* the article now reads *"The analytical layer runs the **63 modules in service** in
  milliseconds"*, and 63 is derived;
* every other count on the page is a derived token;
* the Signal Stack SVG's chips are now **`EVM`, `CUSUM`, `Doc Risk`, `Synthesis`, `ABM`, `PERT`,
  `LOB`, `CCPM`, `RCF`, `DSM`** — method names, no identifiers;
* its accessible name is *"Signal stack: 63 modules in service across 11 project categories,
  feeding the governance decision"*, both figures derived;

**AND A CORRECTION TO WHAT RUN 50 REPORTED, established by grep and stated because it changes
what the reader should believe.** Run 50 described those ten chips as *"visible SVG labels"*.
**They were not visible. `svgSignalStack()` HAS NO CALLER ANYWHERE IN THE REPOSITORY** —
`grep -n "svgSignalStack" assets/js/knowledge.js` returns exactly one line, its own definition.
The function is dead code, it renders on no surface, and a DOM sweep can never see it. Run 50's
own handbook probe did not find those chips either, and recorded that fact without drawing the
conclusion from it. **The identifiers were in the served bytes and were still corrected**, which
is right; but the honest statement is that they were never on a participant's screen. This run's
first attempt to prove the SVG check could fail (F12) therefore PASSED when it should have gone
red, and that is what surfaced the finding. The check was moved to the SOURCE, where the
identifiers actually lived: `run51_dash_sweep.py --svg` extracts every `<text>` body, every
`aria-label` and every interpolated chip array a file BUILDS — **113 of them** across six files —
and asserts none carries an identifier. **Reinstating `01 EVM` turns that red**, which is the
check §7.12 asks for.
* the driver read **34 SVG text nodes** on the handbook and **17** on the deep-dive surface —
  from the diagrams that DO render: the CUSUM chart, the EVM S-curve, the Monte Carlo
  distribution, the evidence-to-action flow and the signal agreement map. The full swept set,
  printed verbatim in the log, is:
  `$`, `AC, actual cost`, `AMBER`, `Audit Record`, `CUSUM`, `CUSUM Red + EVM Green → Anomaly
  Without Narrative (precedence rule 2)`, `CV (cost variance)`, `Cost`, `DOC`, `Documents +
  Schedule +`, `EV, earned value`, `EVM`, `Evidence combination`, `FORECAST`, `GREEN`,
  `Governance`, `H = 5σ (decision interval)`, `Named Human Approval`, `P50`, `P80`, `PV, planned
  value`, `Project Health: signal`, `RED`, `SV (schedule variance)`, `Signal synthesis:`, `The
  system surfaces a recommendation. A named human records the decision.`, `baseline state`,
  `generation`, `project time →`, `recommendation`, `reporting periods →`, `simulated EAC (5,000
  iterations) →`, `⚑ breach @ period 10`. **Not one carries a module identifier.**

---

## 3. The flyout deletion: the grep proof, every check reconciled, and the non-vacuity proof

### 3.1 The grep proof, before deleting anything

```
$ for s in renderCat8Health CAT8_MODULES cat8HealthData cat8HealthDataFromLive \
           isSnapshotStale cat8Retired; do grep -rn "\b$s\b" assets/ index.html research/; done

renderCat8Health         deepdive.js:2450 (definition), :2528 (its own recursive refresh call),
                         :2532 (the export)
CAT8_MODULES             deepdive.js:2354, :2364, :2399
                         knowledge.js:2140, :2385   <-- A DIFFERENT SYMBOL. SEE BELOW.
cat8HealthData           deepdive.js:2392 (definition), :2453 (called from renderCat8Health)
cat8HealthDataFromLive   deepdive.js:2361 (definition), :2418 (called from cat8HealthData)
isSnapshotStale          deepdive.js:2383 (definition), :2414 (called from cat8HealthData)
cat8Retired              deepdive.js:2430 (definition), :2460 (called from renderCat8Health)
```

**Every reader of every one of the six is inside the flyout itself.** The single entry point is
`window.LinDeepDive.renderCat8Health`, and the ONLY occurrence of `LinDeepDive` outside
`deepdive.js` is `research/deepdive.html:119`, which calls `.render()` and never
`renderCat8Health`. `index.html` does not load `deepdive.js` at all.

**A NAME COLLISION, REPORTED RATHER THAN ACTED ON.** `knowledge.js:2140` declares its **own**
`CAT8_MODULES`, in a different IIFE, and `knowledge.js:2385` renders a live handbook article from
it. It is a distinct symbol with a live reader. **It was NOT deleted.** Ruling 1 names the
flyout's symbols; deleting the handbook's would have removed served content.

### 3.2 Reachability, established by execution before each symbol was deleted (§9.5)

| line | control | reachable? | how established |
|---|---|---|---|
| `deepdive.js:2467` | `<button … data-run-portfolio-analysis>Rebuild signals (repair)</button>` | **NO** | it exists only inside `renderCat8Health`, which has no caller; the DOM query `.dd-cat8-health, .dd-health-flyout, .cat8-module` on a fully loaded deep-dive surface with 64 panels drawn returns **nothing** |
| `deepdive.js:2486` | `<button … data-refresh-health>refresh</button>` | **NO** | same |
| `deepdive.js:2494` | `<button class="cat8-flagged-row" data-open-project=…>` | **NO** | same |

The first of those delegated to `#recompute-all-btn`, which **is** a live control on the Portfolio
page at `index.html:563` — **and that control is untouched and still there.** What was removed was
a delegate to it that nothing could ever click.

**Measured after deletion, in the browser:** `window.LinDeepDive` exports **`['render']`** and
nothing else, and `.dd-cat8-health, .dd-health-flyout, .cat8-module` is absent from the rendered
deep-dive DOM while **64 `.dd-panel` nodes** are present on the same page — which is what makes
the absence check non-vacuous as a DOM query.

### 3.3 The non-vacuity proof (§6.2, §7.4)

Asserted in `test_run44_participant_defect_fixes.py` against the BYTES AT `ad4f614`, not against a
memory of them:

* all six symbols **present** in `git show ad4f614:assets/js/deepdive.js`, **absent** now;
* `data-run-portfolio-analysis`, `data-refresh-health` and `cat8-flagged-row` **present** at
  `ad4f614` (counts 2, 1, 1), **absent** now;
* `renderCat8Health` **present in the `window.LinDeepDive` export line** at `ad4f614`, absent now;
* both flyout sentences — *"Portfolio Health is no longer in service."* and *"needs at least 3
  projects"* — **present** at `ad4f614`, absent now.

**184 lines were removed** from `deepdive.js`, and `statusPillClass`, a pure helper whose only
readers were inside the flyout, went with them as part of the same contiguous block.

### 3.4 Every check that asserted the flyout's content, and how each was reconciled

**No check was deleted. §10.5 did not fire.**

| suite | check, before | reconciled to |
|---|---|---|
| `test_run44` | `cat8Retired()` is TRUE against the live taxonomy | the same fact asserted DIRECTLY against the taxonomy in the same four states, by a predicate written in the suite, since the function no longer exists |
| `test_run44` | FALSE with no taxonomy loaded / with an empty taxonomy | same, unchanged in meaning |
| `test_run44` | FALSE with no portfolio-level category | same |
| `test_run44` | FALSE the moment a Portfolio Level module is reinstated | same |
| `test_run44` | *"the flyout states the current state"* (the retired-state sentence present) | **neither sentence is served, because the surface is deleted** — plus a new check that both WERE at `ad4f614` |
| `test_run44` | *"the project-count sentence is RETAINED"* | folded into the same absence-and-non-vacuity pair |
| `test_run44` | `data-run-portfolio-analysis` occurs exactly twice, *"no control was added, moved or removed"* | **NO REACHABLE CONTROL WAS REMOVED**, proved by a `git grep` for `renderCat8Health` across `assets/`, `index.html` and `research/` returning nothing |
| `test_run49` | the `CAT8_MODULES` `num` field survives unrendered | the whole table is **gone**, plus the non-vacuity assertion that it was present at `ad4f614` |
| `test_run28` | `deepdive.js`'s `<button>` count unchanged v17→v18 | re-anchored to `ad4f614` (Run 49's own tree, which is what Run 49's claim was about), and a NEW v19 check asserts **exactly three** `<button>` occurrences left, that all three sat inside `renderCat8Health`, and that `<input>`, `<select>` and `<textarea>` counts are unchanged |
| `drive_run44_browser.py` | calls `window.LinDeepDive.renderCat8Health(...)` | a driver, not a suite; it is superseded by `drive_run51_browser.py`, which asserts the export set is `['render']` |

`test_run44` went from **74/74 to 74/74** with four checks replaced in place and three added; the
suite's own count is printed at the end of section 9.

---

## 4. What `num` was, what it is now, every consumer touched, and the live dispatch proof

### 4.1 What it was

`num` was the **primary key** of the analytical taxonomy, and it was ALSO being rendered as
user-facing text. It was:

* **the producer:** `server/tools/taxonomy_authority.json`, 113 occurrences — one per category and
  one per module;
* **the generator:** `server/tools/build_client_taxonomy.py`, which read `cat["num"]` and
  `m["num"]` and emitted `num:` into both mirrors;
* **both generated mirrors:** `assets/js/taxonomy.js` (91) and `assets/js/categories.js` (79);
* **the server-side key:** `REG.VALIDATED[mid]`, and the key of `service_index()` and
  `registry_index()`;
* **eleven client call sites** reading it AS A KEY: `decision.js:407`, `:426`;
  `projectnet2d.js:65`; `signals.js:423`, `:430`; `detail.js:381`, `:473`, `:1589`, `:2565`;
  `neural_flow.js:150`; `taxonomy.js:373`, `:548`; `categories.js:493`.

**AND SIX SITES RENDERING IT AS TEXT — three of which no previous run reported:**

| site | what it rendered |
|---|---|
| `app.js:1346` | `<span class="cat-mod-num">${esc(m.num)}</span>` — **63 module chips**, `A1.2 … C1.7`, in the Signal Ledger |
| `app.js:1360` | `<span class="cat-row-num" …>${esc(cat.num)}</span>` — **11 category chips**, `A1 … C1` |
| `decision.js:409` | **NEW, found by this run:** `trigger: c.num + " " + c.name + ": " + sev` — the action plan printed *"A1 Cost and EVM Performance: Red"* |
| `decision.js:429` | **NEW, found by this run:** `trigger: "Module " + f.num + " " + f.module + ": Red"` |
| `detail.js:1590–1596` | **NEW, found by this run:** the executive brief's Signal Pattern pushed `c.num`, so the brief read *"RED (2 categories): A1, A3"* |
| `neural_flow.js:1000` | **NEW, found by this run:** the Signal Flow tooltip printed `m.num` above the module name |
| `export.js:140/146/149` | **NEW, found by this run:** the exported workbook's `Category` and `Module` columns were the key |

### 4.2 What it is now

**The key is renamed to `key`, across the registry authority, the generator, both generated
mirrors and every consumer, in one change.** What renders is the **name**, which carries no
identifier. The rename is the point: a field called `key` cannot be mistaken for a display field
by the next reader, which is what `num` was mistaken for at six sites.

* `taxonomy_authority.json`: **113** `"num"` → `"key"`; `python3 -c "json.load(...)"` parses, 12
  categories, and **not one identifier, module or category changed** — only the field name.
* `build_client_taxonomy.py`: emits `key:` and reads `cat["key"]` / `m["key"]`.
* Both mirrors regenerated: **75 `key:` occurrences each** (12 categories + 63 modules), **0
  `num:`**.
* Client consumers rewritten: `app.js`, `decision.js`, `detail.js`, `export.js`,
  `neural_flow.js`, `projectnet2d.js`, `signals.js`, `taxonomy.js`, `categories.js`.
* Server-side tools and suites that PARSE the mirror or the authority were reconciled to the new
  field name, not weakened: `build_run32_b3_reconciliation.py`, `run26_fault_campaign.py`,
  `run32_b3_browser_verification.py`, `run32_qualifier_fault_campaign.py`,
  `test_run10_synthetic_v03.py`, `test_run16_material_cost_variance_disabled.py`,
  `test_run24_empty_project_diagram.py`, `test_run26_counts_and_wiring.py`,
  `test_run32_client_authority.py`, `test_run32_defensibility_truth.py`,
  `test_run32_method_class_agreement.py`, `test_run35_closure_voter_identities.py`,
  `test_run44_participant_defect_fixes.py`.

**`app.js:1346` and `:1360`, before and after, as §6.3 requires:**

```
BEFORE  <span class="cat-mod-num">${esc(m.num)}</span>
        <span class="cat-row-num" style="color:${esc(cat.color)}">${esc(cat.num)}</span>

AFTER   (the module chip is gone entirely)
        <span class="cat-row-swatch" style="background:${esc(cat.color)}" aria-hidden="true"></span>
```

The category's COLOUR was the only non-identifier information the second span carried, and it is
preserved as a swatch. **No colour changed** — the same `cat.color` value is used.

**Read back from the rendered DOM:** `.cat-mod-num` → **0 nodes**; `.cat-row-num` → **0 nodes**;
`.cat-row` → **11**, `.cat-mod-row` → **63**. The ledger still draws the whole population in
service; it just no longer names it by identifier.

### 4.3 The live dispatch proof (§7.5, §10.4)

**Asserted by execution, not by reading, in three independent places:**

1. **Gate row B10, live in this process:** for each of the **101** identifiers in
   `registry_index()`, `method_label`, `group_of`, `parameter_provenance` and `activation_state`
   were all called. Evidence, verbatim from `run51_successor_freeze_gate.csv`:
   *"one authority present=True; both mirrors trace to the generator=True; **runtime lookups
   failing across all 101 registered modules: none**"*.
2. **Independently, in a bare interpreter:** `registered: 101, lookups failing: none`; and every
   one of the **75** `key:` values the client mirror emits resolves in `registry_index()` —
   `client module keys absent from the registry: none`.
3. **In the browser, on a real fixture:** the Signal Flow drew **63** module nodes and **11**
   category nodes; the Signal Ledger drew **11** category rows and **63** module rows; the
   Project Signal Network's eyebrow read *"PROJECT SIGNAL NETWORK · 63 modules · 11 categories"*.
   Had the rename broken a lookup, one of those counts would have collapsed.

**F5, the injection that proves the check can fail:** one character changed in
`taxonomy_authority.json` (`"key": "A1.7"` → `"key": "A1.7-GONE"`); bytes re-read from disk
confirmed the injection landed; the freeze gate went **RED**; the file was restored inside a
`finally` and asserted byte-identical to its snapshot; the gate was re-run and returned to
**34/34**.

**§9.4 — no call site was stopped.** Every one of the eleven had a correct alternative: read
`.key` where the value dispatches, render `.name` where it is read.

---

## 5. The compliance panel split, and any illustrative figure now wrong for its panel

**Before:** one panel, `panel("8.2–8.9", "Compliance Modules", "amber", …)`, drawing eight modules
that the current taxonomy splits between two categories. Its note read *"FAR, OMB, EVM reporting,
quality, safety, environmental, contractor score."*

**After: two panels.**

| panel key | title | category | modules it names |
|---|---|---|---|
| `8.2 to 8.5` | **Regulatory Threshold Modules** | **B3 Regulatory and Authority Thresholds** (bucket 9) | federal acquisition thresholds, budget reporting thresholds, earned value reporting thresholds, contract modification authority |
| `8.6 to 8.9` | **Delivery Quality Modules** | **A6 Delivery Quality Performance** (bucket 6) | quality performance, safety performance, environmental performance, contractor performance score |

**Measured in the rendered DOM:** `"8.2–8.9"` is **absent**; `8.2 to 8.5` → bucket **9**, header
*Regulatory and Authority Thresholds*; `8.6 to 8.9` → bucket **6**, header *Delivery Quality
Performance*. **A6 had no panel of its own before this run and now has one** — the sixth
collapsible group appears on the surface for the first time. That is a change to what a
participant sees, and §3 ruling 3 says it is intended.

### Illustrative figures that became wrong for the panel they now sit in

The single panel carried three `metricBox` illustrations of an EIGHT-module rollup:
**`Compliant "3 of 8"`, `Amber "4 of 8"`, `Red "1 of 8"`.**

**All three became wrong for BOTH halves the moment the panel was split,** because neither half
holds eight modules. **No honest four-module figure exists and none was reconstructed.** The three
metric boxes are not carried into either panel. "Not determinable" is preferred to a plausible
reconstruction, and inventing `2 of 4` would have been exactly that.

The eight-series canvas `data-chart="92_99"` stays on the **regulatory** panel, which keeps the
original panel's chart identity; the **quality** panel draws no chart rather than reuse an
eight-series one for four modules. Both facts are recorded in a comment above the two functions.

**Other illustrative figures that moved with a re-bucketed panel and are reported, not changed:**
`9.1 Missing Data Index` carries `Complete "73%"`, `Missing "27 fields"`, `Worst "Field Rpt"`, and
`9.2 to 9.7 Data Quality Modules` carries `Audit trail "100%"`, `Timeliness "0.58"`,
`Overall "Amber"`. Both panels moved from bucket 9 to bucket 11 (C1 Data Integrity). **The figures
are illustrations of the modules themselves, not of the bucket, so none of them becomes wrong for
its new group.** Panels `03` and `3.2`, which moved category, likewise carry only figures about
their own module. **No stored figure is involved anywhere in this section: these are hard-coded
illustrations on a research-only surface, as Run 50 recorded.**

---

## 6. The full module-by-module bucket mapping, before and after

"Before" is Run 50's rendered-DOM measurement at `ad4f614`; "after" is this run's rendered-DOM
measurement. The authority for the "belongs to" column is
`p0-baseline/module_renumbering_map.csv` and each module's own identity, never the retired
numbering. The eleven project-level categories, in the order the taxonomy holds them, are
**A1, A2, A3, A4, A5, A6, B1, B2, B3, B4, C1** — so bucket *n* is the *n*th of those.

| panel | title | belongs to (authority) | bucket BEFORE | header BEFORE | bucket AFTER | header AFTER | moved? |
|---|---|---|---|---|---|---|---|
| `01` | Hybrid Dynamic Simulation | A1 | 1 | Cost and EVM Performance | 1 | Cost and EVM Performance | no |
| `02` | SPC / CUSUM Anomaly Monitor | A1 | 1 | Cost and EVM Performance | 1 | Cost and EVM Performance | no |
| `03` | Document-Risk Extraction | **A4** (old 1.3, an alias of 4.1) | 1 | Cost and EVM Performance | **4** | **Document-Derived Condition Signals** | **YES** |
| `1.4` – `1.12` (9 panels) | Bayesian EAC … Independent EAC Reconciliation | A1 | 1 | Cost and EVM Performance | 1 | Cost and EVM Performance | no |
| `04`, `05`, `06` | schedule panels | A2 | *not rendered on the fixture* | — | 2 | Schedule Performance | mapping corrected |
| `2.4` – `2.11` (8 panels) | Schedule Compression … Critical Path Index | A2 | 2 | Schedule Performance | 2 | Schedule Performance | no |
| `07` | cost-risk panel | A3 | *not rendered on the fixture* | — | 3 | Cost Risk | mapping corrected |
| `3.1`, `3.3` – `3.10` (9 panels) | Reference Class Forecast … Inflation Adjustment | A3 | 3 | Cost Risk | 3 | Cost Risk | no |
| `3.2` | DSM Rework Propagation | **A5** (old 3.2, an alias of 5.1) | 3 | Cost Risk | **5** | **System Dynamics and Complexity** | **YES** |
| `08` | system-dynamics panel | **A5** | *not rendered on the fixture* | — | **5** | **System Dynamics and Complexity** | mapping corrected |
| `4.1` – `4.10` (10 panels) | Document Risk Score … Spec Conflict Index | A4 | 4 | Document-Derived Condition Signals | 4 | Document-Derived Condition Signals | no |
| `5.1` – `5.8` (8 panels) | DSM Propagation … Discrete Event Simulation | A5 | 5 | System Dynamics and Complexity | 5 | System Dynamics and Complexity | no |
| `8.6 to 8.9` | **Delivery Quality Modules** (NEW, ruling 3) | **A6** | *did not exist* | — | **6** | **Delivery Quality Performance** | **NEW PANEL** |
| `09` | Conservative Dominance: Signal Synthesis | **B1** | 6 | **Delivery Quality Performance** | **7** | **Signal Synthesis** | **YES** |
| `6.1` – `6.4` (4 panels) | Conservative Dominance … Worst-N-of-M | **B1** | 6 | **Delivery Quality Performance** | **7** | **Signal Synthesis** | **YES** |
| `7.1` | Dempster-Shafer Theory | **B2** | 7 | **Signal Synthesis** | **8** | **Evidence Combination** | **YES** |
| `7.2 to 7.8` | Evidence Methods | **B2** | 7 | **Signal Synthesis** | **8** | **Evidence Combination** | **YES** |
| `7.9 to 7.20` | Advanced Methods Comparison | **B2** | 7 | **Signal Synthesis** | **8** | **Evidence Combination** | **YES** |
| `10` – `18` (9 panels) | Dempster-Shafer … Quantum Probability | **B2** | *not rendered on the fixture* | — | **8** | **Evidence Combination** | mapping corrected |
| `19` | ABM Governance Layer | **B3** | 8 | **Evidence Combination** | **9** | **Regulatory and Authority Thresholds** | **YES** |
| `8.1` | Agent-Based Governance Model | **B3** | 8 | **Evidence Combination** | **9** | **Regulatory and Authority Thresholds** | **YES** |
| `8.2 to 8.5` | **Regulatory Threshold Modules** (ruling 3) | **B3** | 8 (as part of `8.2–8.9`) | **Evidence Combination** | **9** | **Regulatory and Authority Thresholds** | **YES** |
| `9.1` | Missing Data Index | **C1** | 9 | **Regulatory and Authority Thresholds** | **11** | **Data Integrity** | **YES** |
| `9.2 to 9.7` | Data Quality Modules | **C1** | 9 | **Regulatory and Authority Thresholds** | **11** | **Data Integrity** | **YES** |
| `10.1` | Multi-Objective Optimization | B4 | 10 | Decision Optimization | 10 | Decision Optimization | no |
| `10.2 to 10.7` | Optimization Modules | B4 | 10 | Decision Optimization | 10 | Decision Optimization | no |

**All seven mis-filings Run 50 named are corrected, including the two alias cases, and the
unassignable panel is split rather than assigned.** Every panel that rendered on the fixture was
asserted **one by one** against a table hand-computed from the naming authority — not read back
from the map under test — and the check passed with **zero** mis-filings and **zero** wrong
headers.

**The eleventh group, confirmed in the DOM (§7.9).** `C1 Data Integrity` is project category
**#11 of 11**, and the panels rendered in it are exactly **`9.1`** and **`9.2 to 9.7`**. Its
header reads *Data Integrity*. Before the loop bound was derived, bucket 11 could not exist and
both panels would have vanished the moment they were filed correctly.

**The group headers now rendered, verbatim from the DOM, with their counts:**

```
[1]  Cost and EVM Performance             (11 modules)
[2]  Schedule Performance                  (8 modules)
[3]  Cost Risk                             (9 modules)
[4]  Document-Derived Condition Signals   (11 modules)
[5]  System Dynamics and Complexity        (9 modules)
[6]  Delivery Quality Performance          (1 module)     <-- had no panel at all before
[7]  Signal Synthesis                      (5 modules)
[8]  Evidence Combination                  (3 modules)
[9]  Regulatory and Authority Thresholds   (3 modules)
[10] Decision Optimization                 (2 modules)
[11] Data Integrity                        (2 modules)    <-- could not exist before
```

**64 panels rendered**, against 58 before the run on the same fixture: the six extra are the
panels whose keys the old label map spelt with an en dash and the new split panel.

### How rulings 5 and 6 are implemented, so they cannot drift apart again

The two maps Run 48 separated — `CAT_FROM_MODULE` (the label) and `CAT_NUM_FROM_MODULE` (the
bucket) — are **replaced by ONE table**, `CAT_KEY_FROM_MODULE`, whose value is the **category key**
in the current taxonomy. `catLabel()` looks that key up in the LOADED taxonomy and returns the
category's **name**; `catBucket()` returns that category's **position** in the in-service
project-level list. The label and the bucket therefore cannot disagree, and **neither is a
literal**. `groupByCategory`'s loop runs to `projectCats.length`, **derived from the taxonomy, not
a new literal**, exactly as ruling 6 requires.

A defensive change came with it: `groupByCategory` clears the root and appends only the groups it
built, so a panel whose key resolved to no category was **silently dropped**. Unclaimed panels are
now appended beneath the groups instead of vanishing, so a missing mapping is visible rather than
silent. **This run hit that failure mode during development and it is why the guard exists.**

### §6.5 item 5: no module was stopped

Every one of the 78 keys the call sites pass resolves to a category in the current taxonomy,
asserted by set difference in `test_run49_naming_completion.py`: *"NOT ONE call-site key falls
through to the neutral fallback"*, empty difference both ways. **No module's category was
undeterminable, so nothing was stopped under §9.2.** Panel `8.2–8.9`, the one Run 50 could not
assign, was **split** rather than assigned, which is what ruling 3 orders.

---

## 7. The dash inventory, what was corrected, and every survivor with its reason

### 7.1 Why the inventory is smaller than 562, and what the right instrument is

Run 50 counted **562 en/em dashes on non-comment lines across 39 files**. That number counts a
dash in a code comment that happens not to start its line, a dash in a CSS token, and a dash
inside minified vendor code — **none of which a participant can read**. A line-based grep cannot
answer guarantee 1.

`server/tools/run51_dash_sweep.py` walks each file as CHARACTERS, tracking line comments, block
comments, single- and double-quoted strings, template literals, **regular expressions** (without
which an apostrophe inside `/'/g` opens a phantom string and desynchronises the whole file), and
for HTML it reads text nodes, `aria-label` attributes **and SVG `<text>` content**. Only STRING,
TEMPLATE, HTML-text, aria, SVG-text, JSON-string and CSS-`content` states are candidate
user-facing text.

**And the STATIC sweep is only the inventory. The VERDICT is the rendered DOM**, which is what
§7.2, §7.7 and §7.11 all ask for, and which is where this report's guarantee-1 answer comes from.

### 7.2 The full inventory, before

| file | classification | total dashes | user-facing candidates |
|---|---|---|---|
| `assets/css/radar.css` | stylesheet | 135 | **0** |
| `assets/js/deepdive.js` | hand-maintained script | 93 | 49 |
| `assets/js/app.js` | hand-maintained script | 114 | 6 |
| `assets/js/simulations.js` | hand-maintained script | 91 | 0 |
| `assets/vendor/xlsx.full.min.js` | **vendored library** | 39 | 37 |
| `assets/js/detail.js` | hand-maintained script | 80 | 41 |
| `assets/js/signals.js` | hand-maintained script | 57 | 11 |
| `assets/js/knowledge.js` | hand-maintained script | 27 | 22 |
| `assets/js/charts3d.js` | hand-maintained script | 83 | 9 |
| `assets/js/decision.js` | hand-maintained script | 26 | 0 |
| `assets/js/admin-ops.js` | hand-maintained script | 26 | 7 |
| `assets/js/store.js` | hand-maintained script | 31 | 1 |
| `assets/js/workspace.js` | hand-maintained script | 32 | 7 |
| `assets/vendor/ASSETS.md` | documentation, not served as interface | 16 | 0 |
| `assets/js/auditor.js` | hand-maintained script | 18 | 13 |
| `assets/js/globe.js` | hand-maintained script | 24 | 0 |
| `assets/js/decision-ui.js` | hand-maintained script | 21 | 5 |
| `assets/js/taxonomy.js` | **generated output** | 14 | 0 |
| `assets/js/auth.js` | hand-maintained script | 17 | 0 |
| `assets/js/categories.js` | **generated output** | 16 | 0 |
| `assets/js/config.js` | hand-maintained script | 11 | 0 |
| `assets/questionnaires/intake.json` | hand-maintained data | 7 | **7** |
| `assets/js/ingest.js` | hand-maintained script | 22 | 6 |
| `assets/js/export.js` | hand-maintained script | 6 | 0 |
| `assets/js/sim.js` | hand-maintained script | 9 | 0 |
| `assets/js/assistant.js` | hand-maintained script | 8 | 5 |
| `assets/js/projectnet2d.js` | hand-maintained script | 11 | 0 |
| `assets/js/neural_flow.js` | hand-maintained script | 37 | 0 |
| `assets/vendor/fonts.css` | **vendored stylesheet** | 19 | 0 |
| `assets/vendor/globe.gl.min.js` | **vendored library** | 2 | 2 |
| `assets/visualizations/pceif_neural_signal_flow.html` | hand-maintained markup | 6 | 2 |
| `assets/questionnaires/debrief.json` | hand-maintained data | 1 | **1** |
| 13 further hand-maintained scripts | — | 41 | 0 |
| **TOTAL** | | **1,130** | **231** |

### 7.3 What was corrected, and how

**The order forbids substituting another punctuation mark for a dash. It does not forbid writing
English.** Five patterns, each stated so the owner can see the policy rather than infer it:

1. **A dash standing where a value would be** — `return "—"`, `x || "—"`, `${v == null ? "—" : v}`.
   The order names `workspace.js:136` explicitly and says: replace with TEXT SAYING WHAT IT MEANS.
   **Every one becomes `"not recorded"`.** `workspace.js:136` is now `if (!iso) return "not
   recorded";`. Sites corrected, counted from `git diff ad4f614 HEAD` line by line: `admin-ops.js` **6**,
   `auditor.js` **9**, `decision-ui.js` **4**, `deepdive.js` **6**, `detail.js` **10**,
   `ingest.js` **1**, `signals.js` **4**, `workspace.js` **7** — **47 in all**.
2. **A dash meaning "no change"** — `detail.js:530` `return "–"` for a zero delta, and
   `detail.js:603` `!changed ? "–"`. They become **`"no change"`** and **`"same"`**.
3. **A numeric or unit range `A–B`** — becomes **`A to B`**. Applied inside string and template
   bodies in `charts3d.js`, `deepdive.js` and `knowledge.js`: threshold ladders
   (`AMBER if 0.90–0.95` → `AMBER if 0.90 to 0.95`), axis labels (`Signal score (0–1)` →
   `(0 to 1)`), legend bands, confidence ranges, and the bibliographic page ranges in the
   handbook's citations (`2923–2932` → `2923 to 2932`).
4. **A compound joined by a dash** — `MEP–Struct conflict` → **`MEP and Struct conflict`**;
   `Arch–MEP` → **`Arch and MEP`**.
5. **A prose em dash inside a sentence** — rewritten as a sentence.
   `intake.json:5` and `debrief.json:5`: *"PLACEHOLDER INSTRUMENT — NOT FINAL."* →
   *"PLACEHOLDER INSTRUMENT, NOT FINAL."*; `intake.json:115` *"PLACEHOLDER SCALE — the instrument
   owner…"* → *"PLACEHOLDER SCALE. The instrument owner…"*; `intake.json:83` *"(usage items —
   placeholder list)"* → *"(usage items, a placeholder list)"*.
   `app.js:898` map-marker title `name + " — " + status` → `name + " is " + status`.
   `auditor.js:666` model prompt `${item} — ${remark}` → `${item} with the remark ${remark}`.
   `pceif_neural_signal_flow.html` title and heading → *"PCEIF Signal Flow, Neural Net View"*.
6. **Console separators** — `console.warn(..., "—", e.message)` in `app.js` (5), `signals.js` (3)
   and `store.js` (1) become `"reason:"`. Not participant text, but free to correct and reported.

**The four credential labels in `intake.json`, which the order names.** `"PMP — Project
Management Professional"` becomes **`"Project Management Professional (PMP)"`**, and the same for
`PgMP`, `PE` and `CCM`. The expansion is preserved and the abbreviation is preserved; only the
dash is gone, and the result reads as ordinary English rather than as a substituted mark.
**NO ITEM, NO RESPONSE OPTION, NO SCALE AND NO ORDER CHANGED** — asserted structurally in
`test_run28_participant_packages.py`, which strips every human-readable label from both
questionnaires and requires the remaining structure to be identical to `ad4f614`.

### 7.4 The ampersands, swept under the same guarantee

Guarantee 1 bars an ampersand as well. Rendered sites were found and corrected across five files, none of them
reported by a previous run: `knowledge.js` (3: *"Program Evaluation & Review Technique"*,
*"Document & Risk Signals"*, *"Governance & Compliance"*), `neural_flow.js` (2: two category node
labels), `signals.js` (8: the document-group labels a participant picks from, e.g. *"Financial &
Schedule Documents"* → *"Financial and Schedule Documents"*, and *"Missing values & required
documents"*), `deepdive.js` (1: *"(Busemeyer & Bruza, 2012)"*, plus two metric-box labels that carried an en
dash, `MEP–Struct` and `Arch–MEP`), and
`ds_defensibility_data.js` (*"simulation V&V"* → *"simulation verification and validation"*,
*"Sargent V&V"*, *"Kim & Reinschmidt"*, *"Wang & Strong"*, *"Busemeyer & Bruza literature"*).

### 7.5 The 74 identifier chips in the Signal Ledger

**What they are:** `app.js:1346` rendered `<span class="cat-mod-num">` for every module in the
loaded taxonomy — **63 chips**, `A1.2` through `C1.7` — and `app.js:1360` rendered
`<span class="cat-row-num">` for every category — **11 chips**, `A1` through `C1`. **74 in total.**
Both read the taxonomy's primary key. **Both are removed**; the category's colour survives as a
swatch. Counted in the rendered DOM after the change: **zero of each**.

### 7.6 Every survivor, and why each survived

| survivor | count | why it survived |
|---|---|---|
| **`assets/vendor/xlsx.full.min.js`** | **37 user-facing-state, 39 total** | **STOPPED under §9.1 and ruling 4's own condition.** They are inside **code-page tables**: `cptable[437]`, `cptable[850]` and their siblings map byte values to characters, and U+2013/U+2014 are the CHARACTERS at specific code points. Editing one changes what the library decodes, so the spreadsheet export would produce different text. **Editing this file would alter its behaviour. The file is stopped, reported, and the run continued.** |
| **`assets/vendor/globe.gl.min.js`** | 2 | **STOPPED under §9.1.** Minified third-party library; the two dashes sit inside a bundled string table. Same reason, same disposition. |
| **`assets/js/detail.js:1840`** | 1 | **STOPPED under §9.3 — the dash is syntactically significant, not prose.** `line.indexOf("—")` is a PARSER over text the MODEL produced, splitting a Signal Pattern line at whatever separator the model wrote. **The blanket placeholder pass replaced it with words, which would have stopped the parse; the change was caught by `test_run2_fifteen_defects.py`'s byte guard and REVERTED.** This is reported as a defect this run introduced and then corrected. `detail.js:1847`'s `/^[—-]\s*/` is the same parser and is untouched. |
| `assets/css/radar.css` | 135 | **CORRECTED WHERE SAFE, WHICH IS NOWHERE, BECAUSE NONE IS USER-FACING.** Every one is inside a comment or a CSS token. The file has **no `content:` declaration carrying a dash**, which is the only way a stylesheet puts text on a screen. Verified by the sweep's `css_content` state returning **zero**. |
| `assets/vendor/fonts.css` | 19 | Same, and vendored. Zero user-facing. |
| `assets/vendor/ASSETS.md` | 16 | Repository documentation, never served as interface. |
| `assets/js/taxonomy.js`, `assets/js/categories.js` | 14 + 16 | **GENERATED OUTPUT. Zero user-facing**, and the order's rule — fix at the authority, never the output — was followed: the authority carries none. |
| block-comment continuation lines across 13 hand-maintained scripts | ~87 | **Comments are not user-facing text**, which is the standing rule this repository has applied since Run 49. The static lexer flags some of them because a template literal elsewhere in the file leaves it mid-state; **each was read individually and each is a comment.** The rendered-DOM sweep, which is the authority, returns **zero**. |

### 7.7 Guarantee 1, the verdict, measured on the rendered DOM

`drive_run51_browser.py` walks the whole `document.body` text tree node by node, **plus every
`svg text`, `svg tspan` and `svg title`**, **plus every `aria-label`, `title`, `placeholder` and
`alt`**, across the Portfolio, Handbook, About, Workspace, Auditor and Admin pages, and separately
across the research deep-dive surface, and applies six patterns: module identifier, category
identifier, the retired `Cat N` scheme, the retired `Module NN` / `M09` / `PH.n` scheme,
ampersand, and en or em dash.

```
pages swept, strings read: [('portfolio', 1321), ('handbook', 1321), ('about', 1321),
                            ('workspace', 1321), ('auditor', 1373), ('admin', 1374)]
candidate hits: 0   excused with a stated reason: 0   SURVIVORS: 0
PASS  GUARANTEE 1: NO USER-FACING TEXT ON ANY RENDERED SURFACE, SVG TEXT NODES AND ACCESSIBLE
      NAMES INCLUDED, CARRIES A MODULE IDENTIFIER, A CATEGORY IDENTIFIER, THE RETIRED SCHEME,
      AN AMPERSAND, AN EM DASH OR AN EN DASH
```

**GUARANTEE 1 IS MET**, for the first time in four runs, on every rendered participant surface,
with **zero survivors to name**, and the sweep is proved non-vacuous three ways: it read 8,031
strings; it read 34 SVG text nodes the previous sweeps could not see; and the check that would
fail if the ten SVG identifiers were reinstated was **injected and observed failing** (F12).

The three files STOPPED at §7.6 are outside the rendered participant surface: the two vendored
libraries put none of their dashes on a page, and `detail.js:1840` is a parser, not text.

---

## 8. Every item stopped under §9, with its reason

**Three items were stopped. Each stopped ONE work item; the run continued and merged, which is
what §1 of the order directs and what Run 50 did not do.**

| # | condition | item stopped | reason, established rather than argued |
|---|---|---|---|
| 1 | **§9.1** — editing a vendored file would alter its behaviour | **`assets/vendor/xlsx.full.min.js`**, 37 user-facing-state dashes of 39 | The dashes are **inside code-page tables** — `cptable[437]`, `cptable[850]` and siblings map byte values to characters, and U+2013 / U+2014 ARE the characters at particular code points. Changing one changes what the spreadsheet exporter decodes and encodes. Ruling 4's own condition says: do not break a third-party library to remove punctuation nobody reads. **Nothing in this file reaches a rendered page.** |
| 2 | **§9.1** — same | **`assets/vendor/globe.gl.min.js`**, 2 | Minified third-party bundle; the two dashes sit in a bundled string table. Same reason, same disposition. |
| 3 | **§9.3** — the dash is syntactically significant rather than prose | **`assets/js/detail.js:1840`**, one em dash | `line.indexOf("—")` is a **PARSER over text the MODEL produced**, splitting a Signal Pattern line at whatever separator the model wrote. Replacing it with words stops the parse. **This run's blanket placeholder pass DID replace it, `test_run2_fifteen_defects.py`'s byte guard caught it, and it was reverted.** Reported as a defect this run introduced and corrected rather than quietly fixed. |

**Nothing was stopped under §9.2** (a module's category undeterminable): every one of the 78
call-site keys resolves, and the one panel Run 50 could not assign was **split** by ruling 3
rather than assigned.
**Nothing was stopped under §9.4** (a call site where key/label separation would break dispatch):
all eleven had a correct alternative, and the live dispatch proof at section 4.3 shows none broke.
**Nothing was stopped under §9.5** (deleting a flyout symbol would remove a reachable control):
reachability was established by execution for each of the three buttons before any symbol was
deleted, and all three were unreachable.

**NO §10 RUN-LEVEL CONDITION FIRED.** The behaviour digest is unchanged; no stored figure changed;
no band, status, colour or posture changed; no runtime lookup failed for any of the 101; no check
was deleted; no gate row failed for a reason other than a manifest this run's edits falsified; and
no reachable user-facing control was added, moved or removed.

---

## 9. Every guarantee at §7, verified or not met, each with its injection

The injection protocol is the one the order tightened after Runs 48, 49 and 50 all aborted
mid-injection: **snapshot → inject → RE-READ THE BYTES FROM DISK → observe RED for the intended
reason → restore inside a `finally` that cannot be skipped → assert restored bytes == snapshot →
re-run → RECHECK THE BASELINE.** It is implemented once, in
`server/tools/run51_injection_campaign.py`, and every fault goes through it.

| # | guarantee | verdict | the injection that proved the check can fail |
|---|---|---|---|
| 1 | Every count of modules or categories in `assets/` is derived, not typed, asserted per site | **VERIFIED.** Twelve sites at section 1, each named with its before and after; every one derives | **F1.** `knowledge.js`: `${taxCounts().registered}` → the literal `96`. Re-read from disk confirmed the injection landed (bytes and sha256 printed). `test_run26_counts_and_wiring.py` went **RED**. Restored byte-identically; baseline back to **54/54** |
| 2 | The handbook states 101 registered and 63 in service consistently across every article, read back from the rendered DOM including SVG text nodes | **VERIFIED.** 51 topics clicked, 799,810 characters of rendered text, 34 SVG text nodes, 6 accessible names. `96`/`100`/`103` absent; `101 registered modules` and `63 are in service` both present | **F1**, same injection: the same literal is what the handbook check reads |
| 3 | Portfolio Health renders nowhere, and none of the six deleted symbols exists in the tree | **VERIFIED.** `window.LinDeepDive` exports `['render']` alone; the DOM query returns nothing while 64 panels are drawn on the same page | **F3.** A `cat8Retired` stub reinstated in `deepdive.js` and re-exported. `test_run44_participant_defect_fixes.py` went **RED**. Restored; baseline back to **74/74** |
| 4 | The deleted symbols were present at `ad4f614`, so the absence checks are not vacuous | **VERIFIED.** All six symbols, all three buttons, both flyout sentences and the export line asserted present in `git show ad4f614:assets/js/deepdive.js` | non-vacuity is itself the positive; **F3** proves the paired absence check can fail |
| 5 | Every runtime lookup across all 101 registered modules resolves after the key work | **VERIFIED** three ways at section 4.3, the primary one being gate row **B10** calling four lookups on each of the 101 live | **F5.** `taxonomy_authority.json`: `"key": "A1.7"` → `"key": "A1.7-GONE"`. The freeze gate went **RED**. Restored byte-identically; gate back to **34/34** |
| 6 | Both generated mirrors match their generator | **VERIFIED by RE-RUNNING the generator and comparing**, never by letting a file check itself: `build_client_taxonomy.py --check` → *"both client artifacts are exactly what the authorities generate"*, exit 0 | **F6.** One character added to a module name in `categories.js`. `--check` went **RED** (exit 1, *"NOT GENERATED FROM THE CURRENT AUTHORITIES"*). Restored; back to exit 0 |
| 7 | `app.js:1346` and `:1360` render no identifier, read back from the rendered DOM | **VERIFIED.** `.cat-mod-num` 0 nodes, `.cat-row-num` 0 nodes, while `.cat-row` 11 and `.cat-mod-row` 63 on the same page | **F7.** The `cat-mod-num` span reinstated in `app.js`, reading `m.key`. `test_run49_naming_completion.py` went **RED**. Restored; baseline back to **72/72** |
| 8 | Every module is filed under and labelled with its current-taxonomy category, asserted per module | **VERIFIED.** Every rendered panel checked ONE BY ONE against a table hand-computed from `p0-baseline/module_renumbering_map.csv`, not read from the map under test: **zero mis-filings, zero wrong headers** | **F8.** `"03": "A4"` → `"03": "A1"` in the panel table. The browser driver went **RED** on *"EVERY RENDERED PANEL IS FILED UNDER THE CATEGORY ITS MODULE BELONGS TO"*. Restored byte-identically; driver back to **37/37** |
| 9 | The two data-quality panels render, in an eleventh group | **VERIFIED.** `C1 Data Integrity` is project category **#11 of 11**; the panels in bucket 11 are exactly `9.1` and `9.2 to 9.7`; the header reads *Data Integrity* | **F9.** The loop bound `projectCats.length` → the literal `10`. The driver went **RED**: the eleventh group vanished and both data-quality panels with it. Restored; driver back to **37/37** |
| 10 | The compliance panel is two panels, each holding only the modules of its own category | **VERIFIED.** `"8.2–8.9"` absent; `8.2 to 8.5` → bucket 9 (B3), `8.6 to 8.9` → bucket 6 (A6) | **F10.** `m9_2b(project)` removed from the render list, merging the split back. The driver went **RED**. Restored; driver back to **37/37** |
| 11 | **Guarantee 1: no user-facing text anywhere in `assets/` carries a module identifier, a category number, the retired scheme, an ampersand, an em dash or an en dash** | **MET.** On the rendered DOM of six participant pages and the deep-dive surface, SVG text nodes and accessible names included: **8,031 strings read, 0 candidate hits, 0 survivors.** Three files are stopped under §6.6 item 3 and each is named at section 8; none of them puts a character on a rendered page. **NOT MET for three runs; MET now** | **F11.** An em dash reinstated in a rendered panel heading (`"Regulatory — Threshold Modules"`). The driver's guarantee-1 check went **RED** and named the survivor. Restored; driver back to **37/37** |
| 12 | Sweeps read SVG text nodes, proved by a check that fails if the SVG identifiers are reinstated | **VERIFIED, IN TWO PLACES, AND THE FIRST ATTEMPT WAS WRONG.** (a) IN THE DOM: the driver reads `svg text`, `svg tspan` and `svg title` — 34 nodes on the handbook, 17 on the deep dive — and its positive is a label that exists ONLY inside an SVG (`H = 5σ (decision interval)`, `SV (schedule variance)`). (b) IN THE SOURCE: `run51_dash_sweep.py --svg` reads **113** SVG text bodies, accessible names and interpolated chip arrays out of what six files BUILD. **(b) exists because `svgSignalStack()` HAS NO CALLER and renders nowhere, so no DOM sweep can reach it** | **F12, and it took two attempts, which is reported rather than hidden.** `mods: ["EVM", "CUSUM"]` → `mods: ["01 EVM", "02 CUSUM"]`. Against the DOM check it **did not go red** — because the diagram never renders — and that failure is what established the dead-code finding. Against the SOURCE check it went **RED** and named the survivor. Restored byte-identically; the source check back to **1/1** and the driver to **37/37** |
| 13 | The behaviour digest is unchanged from `8fb4d366…` | **VERIFIED.** Gate row **B15** reproduced it live from the current tree at every one of the three mints: `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1` | **F13.** `models_evm.py`: A1.7 TCPI's band boundary `_TCPI_STABILITY_MARGIN = 0.10` → `0.30` — a real behaviour change on a scientific target. The gate went **RED**. Restored byte-identically; gate back to **34/34** |
| 14 | No stored figure changes | **VERIFIED.** No server computation moved; B15 reproduced identically; the whole change set is the served client, the taxonomy's field NAME, the stamp and the guards. Gate rows **B03**, **B05**, **B06** all 0 | **F13** is the discriminating injection: it turned the gate red while every purely-textual injection left B15 green |
| 15 | No band, status, colour or posture changes | **VERIFIED.** **B05**: 100 served statements measured against EXECUTED behaviour, failing: none. **B06**: census `{ABSTAINS: 89, COMPUTES: 5, SUPPLIED_NOT_COMPUTED: 1, PORTFOLIO_ROUTE: 5}` — **identical to Runs 48, 49 and 50**. The one colour this run touched is `cat.color` on the Categories page, which is passed to a swatch instead of to a text span: **the same value** | **F13**, as above |
| 16 | Modules in service is 63, registry total 101, both derived | **VERIFIED.** `len(service_index()) == 63`, `len(registry_index()) == 101`, called live in the driver's own process and printed: `in service: 63    registry: 101    retired: 38`. Gate **B02** measures the same populations independently and reports 0 | n/a — a positive measurement, not an absence |
| 17 | Voting count is exactly 2, `A1.7` and `A1.8` | **VERIFIED.** Gate **B09**: `CORE_VOTING_MODULES = ['A1.7', 'A1.8']` | n/a |
| 18 | The detail page still opens on the latest computed period, Run 48's four fixtures re-run | **VERIFIED.** `test_run48_current_period.py` **56/56**, its four fixtures unchanged: `PRJ-R48-DOCS` opens on 2, `PRJ-R48-GAP` on 4, `PRJ-R48-HIGH` on 48, `PRJ-R48-NONE` returns null without error | n/a |
| 19 | Every sequence-bearing file that moved has its own named exception record; one moving without a record still turns the gate red | **VERIFIED.** All six moved, all six are declared in `participant_packages.V18_TO_V19_SEQUENCE_EXCEPTION`, and **each is named individually with what moved inside it** in the v19 checksum record's header, asserted file by file by both `test_run28` and `test_run36_fault_guards` | **F19.** One newline byte appended to `assets/js/workspace.js` so its bytes no longer match its record. The gate went **RED**. Restored byte-identically; gate back to **34/34** |
| 20 | The successor freeze gate passes in full | **VERIFIED.** 15 blocker classes, **0 blocked**; `test_run37_freeze_gate.py` **34/34** | **F5**, **F13** and **F19** each turned it red for a different reason, which is what makes the pass non-vacuous |

**A suite printing no result line has not run; a crash is not a pass.** Both files this run wrote,
`drive_run51_browser.py` and `run51_injection_campaign.py`, count a raise as a failure and print
the traceback, and neither uses the `try/finally` + `sys.exit`-in-`finally` shape.

**One fixture fault, reported rather than hidden.** The first pass of the browser-driven
injections reused one SQLite database across invocations, so the second `adminparticipantcreate`
raised `KeyError: 'access_token'` — a FIXTURE fault, not the fault under test. **The restores
still ran and were still asserted byte-identical**, which is exactly what the `finally` is for.
The campaign now migrates a fresh database per invocation and the five browser-driven faults were
re-run against it.

---

## 10. Every sequence-bearing file that moved and its exception record

The six were re-verified from `server/tools/participant_packages.py` `SEQUENCE_BEARING_FILES`
before anything was edited. **ALL SIX MOVED. That is the first time all six have moved at once,
and it is asserted as SIX EXCEPTIONS WITH NAMES, not by widening the invariant.**

| file | ruling | what moved inside it, exactly |
|---|---|---|
| `assets/js/deepdive.js` | 1, 3, 4, 5, 6 | The Portfolio Health flyout DELETED with its six symbols and three buttons; the eight-module compliance panel SPLIT into two; the label map and the bucket map replaced by ONE table of category keys from which both derive, correcting seven mis-filings; the grouping loop's bound derived from the taxonomy instead of the literal ten; en dashes and an ampersand in rendered prose replaced by words |
| `assets/js/decision.js` | 2 | The action-plan trigger lines stopped concatenating a category identifier and a module identifier into rendered text and now name the category and the module; the field read for dispatch is renamed `num` → `key` |
| `assets/js/decision-ui.js` | 4 | Four rendered placeholders that were a bare em dash now say `not recorded`. **The three inert `period: 1` literals are untouched** |
| `assets/js/workspace.js` | 4 | The same placeholder correction at seven sites, including `workspace.js:136`, which the order names explicitly: `return "—"` → `return "not recorded"` |
| `assets/questionnaires/intake.json` | 4 | Em dashes inside existing participant-facing labels and notes replaced by words: four credential labels, three placeholder notices, one usage-item note |
| `assets/questionnaires/debrief.json` | 4 | One em dash in the placeholder notice |

**Where each record lives, and what makes the invariant still real now that the exception spans
the whole set.** Each is declared in `participant_packages.V18_TO_V19_SEQUENCE_EXCEPTION`, and —
this is the part that keeps it honest — **each is named INDIVIDUALLY, with what moved inside it,
in the header of `code_audit/run51_participant_package_v19_checksums.sha256`**. Two suites assert
that file by file:

* `test_run28_participant_packages.py`: *"every sequence-bearing file that moved carries its OWN
  named exception record"*, six checks, one per file;
* `test_run36_fault_guards.py`, new check `run36.fault35.every_sequence_exception_has_its_own_record`:
  a file moving without one is a failure **even though the exception now spans the whole set**.

**And no sequence STEP moved inside any of them, measured rather than asserted:**

* `deepdive.js`'s references to `stage`, `reveal`, `lock` and `randomi` are **unchanged in
  number** across v18 → v19, each counted;
* both questionnaires: with every human-readable label, note, text, prompt and title stripped, the
  remaining JSON structure is **identical** to `ad4f614`. **NO ITEM, NO RESPONSE OPTION, NO SCALE
  AND NO ORDER CHANGED**, and that is asserted structurally rather than by byte-identity, which
  byte-identity could not have told the owner;
* `deepdive.js` lost **exactly three** `<button>` occurrences, all three inside `renderCat8Health`;
  `<input>`, `<select>` and `<textarea>` counts are unchanged.

**F19 proves the check can fail:** one newline byte appended to `workspace.js` turned the gate red
at **B01**, **B04** and **B11**; restored byte-identically; gate back to 34/34.

---

## 11. Which audit artifacts the suites rewrote, and were restored

The full 193-suite run and the acceptance generator rewrote **18** artifacts — **17 under
`code_audit/` plus `server/tools/run17/coverage.csv`, which is outside it** — exactly as Runs 48,
49 and 50 each recorded:

```
code_audit/run10_no_operational_effect.csv          code_audit/run9_abstention_results.csv
code_audit/run20_cycle12_100_reaudit.csv            code_audit/run9_alias_overlay_verification.csv
code_audit/run20_cycle12_guard_nonvacuity.csv       code_audit/run9_fixture_import_results.csv
code_audit/run20_cycle12_lineage_campaign.csv       code_audit/run9_known_answer_results.csv
code_audit/run21_guard_nonvacuity_results.csv       code_audit/run9_no_operational_effect.csv
code_audit/run30_cat7_operational_execution.csv     code_audit/run9_validator_gap_recomputations.csv
code_audit/run38_controlled_stimulus_execution_order.csv
code_audit/run38_lock_integrity.csv
code_audit/run38_participant_state_machine.csv
code_audit/run39_launch_identity.csv
code_audit/run8_expectation_mutation_proof.csv
server/tools/run17/coverage.csv
```

All 18 were restored with `git checkout --` naming each path, and **none was committed.**
Three further `code_audit/run37_*.csv` files are rewritten by `build_run37_acceptance.py` when it
is run without `--out-audit`; they were restored the same way and **none was committed** either.
`git status --porcelain` at the end of the run reports the report file and nothing else.

**Three mints were paid, exactly as §8.1 warned.** Run 49 paid three for the same reason and this
run paid three: (1) the identity was minted at the branch's first commit and B01 read a dirty
tree, so the change set had to be committed first; (2) the identity was re-minted at that commit,
the gate and release rebuilt, and committed; (3) `test_run2_fifteen_defects.py`'s byte guard —
runnable only against the new manifests — caught the `detail.js:1840` parser regression, which
moved `detail.js` and `signals.js` again and forced a third mint. **Two of the three
reconciliations were discoverable only by running the full suite against the new manifests, which
is precisely what §8.1 predicted.**

**The pinned guards reconciled, and every one to TRUE bytes, none widened:**
`code_audit/run51_participant_package_v19_checksums.sha256` (new, 70 files),
`code_audit/run51_production_tree.sha256` (new, 244 files),
`code_audit/run51_authority_tree.sha256` (new, 9 files — the FIRST time the authority tree has
moved since Run 39, because the authority's primary-key field is renamed),
`research/freeze/run51_freeze_candidate_identity.json`,
`research/freeze/run51_successor_freeze_gate.csv`,
`research/freeze/run51_candidate_behaviour_digest.json`,
`research/freeze/RUN51_SUCCESSOR_FREEZE_{RECORD.json,REPORT.md,CHECKSUMS.csv}`,
plus `server/tools/run51_production_changes.py`, the declared-change manifest.
**Every predecessor record is untouched:** `run39_authority_tree.sha256`,
`run49_production_tree.sha256` and the v18 checksum record are all byte-identical to their
committed bytes, and the v18 package record is now pinned to the commit whose blobs it describes,
`ad4f614`, exactly as v16 and v17 are.

---

## 12. Incidental findings, unacted

1. **A REACHABLE control on the deep-dive surface has a dead handler.** `deepdive.js:2322` renders
   `<button class="dd-link" data-goto-health>see Health →</button>` inside `render()`, which
   `research/deepdive.html` DOES call, so this button is genuinely reachable. Its handler calls
   `window.LinIngest.openHealthModal()` — and **`openHealthModal` does not exist anywhere in the
   repository**; the only other occurrence of the name is a comment in `app.js:1382`. Clicking it
   does nothing. **It was NOT removed**: removing a reachable control is §10.7, a run-level halt,
   and it is not one of the six symbols ruling 1 names. It belongs with carry-forward item 2.
2. **The count sweep found three identifier render sites no order named**, all now corrected and
   all reported at section 4.1: the action plan's trigger lines, the executive brief's Signal
   Pattern list, and the Signal Flow tooltip. The exported workbook's two identifier columns are a
   fourth. **Guarantee 1 had never been measured on the rendered DOM before, which is why they
   survived four runs of source greps.**
3. **`groupByCategory` silently DROPS a panel whose key resolves to no category.** It clears the
   root and appends only the groups it built. This run hit it during development — six panels
   vanished because their keys were spelt with an en dash on one side of the table and words on
   the other. A guard now appends unclaimed panels beneath the groups so the failure is visible.
   **Any future edit to the panel table should know that this used to fail silently.**
4. **`knowledge.js` declares its own `CAT8_MODULES`**, unrelated to the flyout's, with a live
   reader at `knowledge.js:2385` that renders a handbook article. A naive symbol-name sweep will
   flag it as a survivor of ruling 1. It is not; it was correctly left alone.
5. **`deepdive.js:1789–1849` keeps a LOCAL `num` field** on the methods-comparison array
   (`"09"`…`"18"`). It is a dispatch key and is never rendered — only `e.label`, `e.year` and
   `e.val` reach the DOM. **It is already the shape ruling 2 asks for**, and it was left alone.
6. **`deepdive.js:2464`'s `f.id` is a PROJECT identifier, not a module identifier** (Run 49 §1.4,
   re-confirmed by Run 50). It went with the flyout, so the trap is gone, but the `mod-mono` class
   still exists in the stylesheet and will make a naive sweep flag whatever next uses it.
7. **`test_run47_evm_consistency.py` still swallows its own traceback** in a `finally` with
   `sys.exit`. Left alone, as instructed, and carried forward.
8. **`test_run22_production_tree_completeness.py` was red in the runner on a first pass and green
   standing alone**, exactly as the order predicted. So were `test_run10_state_protection.py`,
   `test_run16_final_flow_and_rail.py` and `test_run20_declared_production_changes.py` on the
   first pass; each was a real manifest reconciliation and each is now green in both modes.
9. **The static dash sweep's lexer cannot always tell a comment from a string**, because a
   template literal containing a `${…}` expression leaves it mid-state. It over-reports, never
   under-reports, which is the safe direction; every over-report was read individually. **The
   rendered-DOM sweep is the authority and it needs no such judgement.**
10. **Playwright 1.48 in this environment still cannot find its own browser.** It expects
    `chromium-1140`; the image ships `chromium-1194` and `chromium_headless_shell-1194` under
    `/opt/pw-browsers`. An explicit `executable_path` plus `--headless=new` is required. Recorded
    again so the next run does not spend the time.
11. **`drive_run44_browser.py:145` still calls `window.LinDeepDive.renderCat8Health`.** It is a
    driver, not a suite, and it is superseded by `drive_run51_browser.py`. It will raise if run.
    Left alone: fixing it is outside what §3 orders.
12. **The deep-dive fixture cannot reach 14 panels.** `04`, `05`, `06`, `07`, `08` and `10`–`18`
    render only when `project.simulationSignals.signal_array` is populated, which the legacy blob
    on this fixture does not supply. Their CATEGORY MAPPING is corrected in the table and asserted
    there; their BUCKET could not be measured in the DOM and is not claimed to have been.

---

## 13. What the next session needs, stated as a decision for the owner

1. **`research/deepdive.html` is now the only surface carrying a reachable control that does
   nothing.** Ruling 1 removed the dead flyout, but the `see Health →` button that used to be the
   only plausible route to it is still on the page with a handler calling a function that does not
   exist. **Decide:** (a) remove the button, which is removing a REACHABLE control and therefore
   needs your explicit authority because §10.7 otherwise halts a run; (b) give it a destination;
   or (c) record it as an accepted limitation of a research-only surface. This is the smallest
   remaining piece of carry-forward item 2 and it can be settled without the redesign.

2. **Guarantee 1 is met on the rendered DOM and NOT met on a static grep of `assets/`, and those
   two are different claims.** This run's answer is the DOM one, because that is what §7.2, §7.7
   and §7.11 all ask to be read back from. The static inventory still counts 87 dashes in
   candidate string states, of which 39 are the two stopped vendored libraries and the rest are
   block comments. **Decide:** write into the limitation contract that guarantee 1 means
   RENDERED text, measured in a browser including SVG text nodes and accessible names — or keep
   it as a source-level claim, in which case the two vendored libraries must be named as
   permanent exceptions in the contract itself rather than re-stopped by every run.

3. **The compliance split left three illustrative figures with no honest replacement.** `3 of 8`,
   `4 of 8` and `1 of 8` described an eight-module rollup and are wrong for both halves. They were
   removed rather than reconstructed. **Decide:** leave both panels without a metric row; or
   supply the four-module figures you want each to state; or rule that these deep-dive
   illustrations should be computed from the stored row rather than hard-coded, which is the same
   redesign carry-forward item 2 asks for.

4. **The `num` → `key` rename is done in the client and the authority but the SERVER still calls
   the same thing `module_id` in some places and a bare key in others.** Nothing is broken — the
   live dispatch proof covers all 101 — but the naming is now consistent on one side of the wire
   and not the other. **Decide:** whether a future run should carry `key` through
   `registry.py`'s own signatures, or whether the server's `module_id` is the better name and the
   client should follow IT instead. Either is defensible; having two is what produced this defect
   in the first place.

---

## Carried forward, unacted, so they are not rediscovered

1. **CPI 1.22 on the site render.** Run 46 established the code cannot narrow it further; it needs
   read access to PRJ-001's stored rows, which no session may have. **The open question is which
   document type wrote `pv`.**
2. **`research/deepdive.html`.** Run 50 found it does not merely gate on the legacy signals blob
   but COMPUTES from it in all 77 panel bodies, so re-pointing it changes what it shows. It needs
   its own run as a redesign, or a ruling that it is a research-only surface outside the
   participant path. **Not touched here**, as the order requires.
3. **The `historical_data` triple**, Run 47's only unimplemented relation, awaiting a ruling on
   whether "a known BAC" means this project's or any the same document states.
4. **`signal_inputs.sources` records no source field name**, so a finding cannot say which cell of
   a document a figure came from.
5. **Four status comparisons remain case-sensitive**, two of them in `decision.js`.
6. **Two Run 45 census artifacts do not match the v30 release manifest.**
7. **`test_run47_evm_consistency.py` swallows its own traceback** in a `finally` with `sys.exit`.
8. **Run 47's handoff entry is at the bottom of `T6_HANDOFF.md`**, against that file's own rule.
   Left where it is: moving it rewrites history.

---

## The freeze gate, every row with its verdict

Re-run live from the current tree after the third mint. `test_run37_freeze_gate.py`:
**34/34 checks passed**, 15 blocker classes, **0 blocked**.

| row | blocker | count | requirement | evidence | result |
|---|---|---|---|---|---|
| B01 | dirty candidate identity | 0 | = 0 | 11 content-addressed digests recomputed from the tree and compared; git porcelain lines at evaluation: 2 | **PASS** |
| B02 | population mismatch | 0 | = 0 | registered total=101 expected 101; project scientific targets=95 expected 95; Portfolio Health targets=5 expected 5; scientific targets=100 expected 100 | **PASS** |
| B03 | controlled-stimulus mismatch | 0 | = 0 | projects=6, periods/project=[6], unique=36, rows=36, duplicates=0, missing=0 | **PASS** |
| B04 | participant-sequence drift | 0 | = 0 | 6 sequence-bearing files compared against the og-participant-2026.08-v19 record; moved: none | **PASS** |
| B05 | false defensibility statement | 0 | = 0 | 100 served statements measured against EXECUTED behaviour; failing: none | **PASS** |
| B06 | unexpected execution exception | 0 | = 0 | census {'ABSTAINS': 89, 'COMPUTES': 5, 'SUPPLIED_NOT_COMPUTED': 1, 'PORTFOLIO_ROUTE': 5}; populated analytical results 3: ['A1.7', 'A1.8', 'A6.2'] | **PASS** |
| B07 | Category-9 bypass | 0 | = 0 | unqualified-package probes reaching a banded result: none; C-group voters: none; group C contributes to project status: False | **PASS** |
| B08 | Category-10 authority violation | 0 | = 0 | human_authorization_required True, creates_project_evidence False, and no Category-10 identity in the voting set | **PASS** |
| B09 | voting count is not exactly 2 | 0 | = 0 | CORE_VOTING_MODULES = ['A1.7', 'A1.8'] | **PASS** |
| B10 | current taxonomy dual authority | 0 | = 0 | one authority present=True; both mirrors trace to the generator=True; **runtime lookups failing across all 101 registered modules: none** | **PASS** |
| B11 | package or predecessor mutation | 0 | = 0 | rewritten predecessor package records: none; og-participant-2026.08-v19 files not matching their record: none; live stamp sim-2026.08-v34 (expected sim-2026.08-v34); predecessor 82bd1f855313 still stamped sim-2026.08-v33: True | **PASS** |
| B12 | browser qualification failure | 0 | = 0 | 29 rows; failing: none | **PASS** |
| B13 | unresolved blocking Run-36 defect | 0 | = 0 | open instrument-level defects: none; target rows carrying one: none | **PASS** |
| B14 | unsupported final empirical-validation claim | 0 | = 0 | every one of the 100 rows records NOT_EMPIRICALLY_FIELD_VALIDATED; exceptions: none | **PASS** |
| B15 | candidate behaviour changed during the run | 0 | = 0 | **behaviour digest reproduced identically: 8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1** | **PASS** |

Beyond the fifteen blocker rows the suite also passed: `generator_runs`, `artifact_present`,
`reproduces` (the gate is not a stale snapshot: 15 fresh rows against 15 committed),
`fifteen_blocker_classes`, `blocking_defects_zero`, `predecessor_release_preserved` (v25), five
`immediate_predecessor_release_preserved` rows (v26, v27, v28, v30, v31),
`no_release_while_blocked`, `release_present_when_clean`, four `limitation_stated` rows,
`disposition` (FINAL_FREEZE_ACCEPTED) and `no_self_reference`. **34/34.**
