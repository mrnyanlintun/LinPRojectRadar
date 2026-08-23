# Run 50: the surfaces show what is in service — HALTED ON THREE STOP CONDITIONS

**Date:** 2026-08-22. **Repository:** the Linux clone at `/home/user/LinPRojectRadar` (the Windows
path `C:\Users\NTUN\OneDrive - Arora Engineers, LLC\DEng\LinPRojectRadar` was not used).
**Interpreter:** the documented fallback, `python3` **3.11.15** at `/usr/local/bin/python3`; this
clone carries no `.venv`, so `server/run_all_suites.sh` fell through to the interpreter on PATH,
which is what it is written to do.

**Branch:** `run50-surfaces-in-service`, rooted at `ad4f614`. **NOT MERGED. `main` is still at
`ad4f614` and was never moved.** No stamp was minted; the live stamp is still `sim-2026.08-v33`
and the participant package is still `og-participant-2026.08-v18`. **No production file in
`assets/`, `server/app/` or `server/tools/taxonomy_authority.json` was edited by this run.**

**Why the run halted:** three of the nine stop conditions in §9 fired, each established by
execution rather than argued:

| # | stop condition | where it fired | established by |
|---|---|---|---|
| **9.1** | Removing the Portfolio Health flyout would remove a control | `deepdive.js:2450` `renderCat8Health` | the flyout's own markup carries three buttons (§6) |
| **9.2** | A module's current category cannot be determined from its own identity | deep-dive panel `8.2–8.9` "Compliance Modules" | it names eight modules that fall in **two** current categories (§3) |
| **9.8** | Repairing `research/deepdive.html` would change what that surface shows | `store.js:727` `hasSignals` + all 77 panel bodies | every panel body computes from the legacy blob, not from the stored row (§7) |

§9 of the order and the dispatch brief both say: if any stop condition fires, **stop, leave
unmerged, and report exactly where and why.** That is what this report does. Nothing was
"acted then reported": §5.4 item 4 says stop **before** acting, and no removal was performed.

**Baseline verified before anything else, and again at the end.** 193 suites,
**14,591 / 14,591 checks, ALL SUITES GREEN**. Freeze gate **34/34**, 15 blocker classes,
**0 blocked**. Behaviour digest **`8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1`
— unchanged**, reproduced live from the current tree by the gate's B15 row.

**Browser sessions** were run from a clean subdirectory,
`/tmp/.../scratchpad/run50work/clean`, never the scratchpad root, and the driver printed that
cwd. **The `DEng\Demo` tell was checked before anything was measured: 7 `.page` sections, and
neither `api.js` nor `boot.js` in `document.scripts`.** Chromium 1194 was driven through
Playwright 1.48 with an explicit `executable_path` (the bundled 1140 build is absent).

---

## 1. Every visual surface: population before, population now, rendered node counts

Measured by **counting rendered nodes in a real browser**, against a fixture built through the
real `projectupload` / `projectcomputeall` routes, with the deep-dive surface additionally
supplied the legacy `signals` block from `p0-baseline/contracts/get/get.json` through the real
`save` route (the capture was read, never modified; its own `signalInputs` are refused by the
live write path). Driver: `server/tools/drive_run50_browser.py`. Log:
`before_dom.log` / `BEFORE_DOM_FINAL.log`.

**"After" equals "before" throughout, because the run halted before any edit.** The column is
kept so the owner can see exactly what a Run 51 has to move.

| # | surface | population it builds from TODAY | rendered node count BEFORE | count NOW | expected (in service) | verdict |
|---|---|---|---|---|---|---|
| 1 | **Signal Flow** diagram (`neural_flow.js` `buildModel`) | `window.LIN_CATEGORIES` minus portfolio — **the population in service** | **63** module nodes (`g.lnf-nd[data-kind=module]`), **11** category nodes | 63 / 11 | 63 / 11 | **population CORRECT**; its caption is not (row 6) |
| 2 | **Signal Web** sphere (`detail.js` `buildModuleAxes`) | `LIN_CATEGORIES` — in service | canvas; its own rendered footnote reads **"63 modules · 0 Red · 2 Amber · 1 Green"** | same | 63 | **population CORRECT** |
| 3 | **Ensemble Analysis** scatter (`detail.js` `ensembleTally`) | `projectCats()` — in service | canvas; rendered eyebrow **"Ensemble Scatter · 3 active modules (63 total)"**, sub **"63 modules in 3D"** | same | 63 | **population CORRECT** |
| 4 | **Project Signal Network** (`projectnet2d.js:196`) | `projectLevelCategories()` — in service | canvas; rendered eyebrow **"PROJECT SIGNAL NETWORK · 63 modules · 11 categories"** | same | 63 / 11 | **population CORRECT** |
| 5 | **Signal Ledger** (`app.js` `categoryLedgerHtml`) | `projectLevelCategories()` — in service | **11** `.cat-row`, **63** `.cat-mod-row` | 11 / 63 | 11 / 63 | **population CORRECT**; it renders identifiers (row 7) |
| 6 | **Signal Flow summary strip** (`neural_flow.js:1179`) | derived from the same in-service model | rendered verbatim: *"This diagram shows the platform's **registered architecture**: 27 supported document types, **63 registered project modules** and **11 registered categories**."* | unchanged | the words must say **in service** | **DEFECT — wrong word, right number** |
| 7 | **Signal Ledger identifier chips** (`app.js:1346`, `:1360`) | `m.num` / `cat.num` from the generated taxonomy | **63** module chips `A1.2 … C1.7`, **11** category chips `A1 … C1` | unchanged | **zero** | **DEFECT — guarantee 1** |
| 8 | **Detail-page section badges** (`detail.js:1080/1081/1084`) | `projectCats().length`, `projectModuleCount()` | rendered: `11 registered`, `63 registered`, `63 registered` | unchanged | **"in service"** | **DEFECT — wrong word, right number** |
| 9 | **Handbook, "Why 101 registered modules across four groups"** (`knowledge.js:585`) | a **hard-coded literal** | rendered verbatim: *"The analytical layer runs the project's **96 registered modules** in milliseconds"* | unchanged | **63 in service**, derived | **DEFECT — THIS IS THE "96" THE OWNER SAW** |
| 10 | **Handbook Signal Stack SVG** (`knowledge.js:417–419`) | hard-coded literals | visible SVG labels **`01 EVM`, `02 CUSUM`, `03 Doc Risk`, `04 Synthesis`, `05 ABM`, `06 PERT`, `07 LOB`, `08 CCPM`, `09 RCF`, `10 DSM`**, and the accessible name *"Signal stack of **10 categories** and Portfolio Health…"* | unchanged | no identifiers; **11** project categories | **DEFECT — guarantee 1 and a wrong category count. NEW: no previous sweep reached it** |
| 11 | **Deep-dive Signal Stack** (`research/deepdive.html`) | **77 hard-coded `panel()` call sites**, not the taxonomy | **63** `.dd-panel` rendered, **10** group headers | unchanged | see §3 | **DEFECT — mis-bucketed and draws retired identities** |

**The headline, stated plainly.** The five surfaces the order names at §5.1 items 1–5 **already
draw the population in service, 63, and did so before this run** — Run 43H's delinking did reach
them, because every one of them builds from `LIN_CATEGORIES`, and `LIN_CATEGORIES` is generated
from `service_index()`. What survived Run 43H is **the word beside the number** and **three
hard-coded literals**. The Signal Flow diagram the owner saw declaring "96 registered project
modules" now declares **63**; the sentence still calls them "registered", and the handbook
article still says **96** because that figure is typed in rather than derived.

**Where the registry population is CORRECT and must stay** (the honest converse §5.1 demands):

| surface | population | why the registry is right there |
|---|---|---|
| `knowledge.js:554` — *"101 registered modules, of which 63 are in service…"* | registry **and** in service, both named | a methods surface describing what the platform registers versus what runs. **Verified present in the rendered handbook DOM.** Correct as written. **KEEP.** |
| `knowledge.js:600` — *"The registry holds 101 modules, of which 63 are in service… The 38 modules not in service were retired at Run 43"* | registry | provenance. Correct as written. **KEEP.** |
| `knowledge.js:579` — article title *"Why 101 registered modules across four groups"* | registry | the article is about what the platform registers. **KEEP.** |
| `ds_defensibility_data.js:13` — *"The module registry (100 registered computations, plus one value the extraction model supplies rather than the analytical server)"* | registry | a provenance statement about the registry. 100 + 1 = 101 and it is self-consistent. **KEEP.** |
| gate row **B02** — `registered total=101` | registry | the gate measures the registry deliberately. **KEEP.** |

---

## 2. Every remaining `registry_index()` caller

Swept across `server/`, `tools/` and `assets/`, excluding suites. **There are seven production
call sites and not one of them builds a population from the registry.**

| # | call site | what it does with the registry | corrected? | reason |
|---|---|---|---|---|
| 1 | `server/app/simulation/registry.py:437` (`available_modules`) | `sorted(set(registry_index()) - set(retired_modules()))` | **not corrected — correct as is** | this **is** the derivation of the in-service population. Subtracting the retirements from the registry is how the service roster is defined. |
| 2 | `server/app/simulation/registry.py:443` (`service_index`) | `{k: v for k, v in registry_index().items() if k not in retired}` | **not corrected — correct as is** | the same: `service_index()` is *defined* in terms of `registry_index()`. This is the one place the registry legitimately seeds a population. |
| 3 | `server/app/simulation/registry.py:488` (`group_of`) | `registry_index().get(new_id)` — one named identifier | **not corrected — correct as is** | a **lookup**, not a population. A retired identifier must still resolve its group, or audit lineage breaks. |
| 4 | `server/app/simulation/registry.py:507` (`run_module`) | membership test for one named identifier | **not corrected — correct as is** | a **lookup**. Run 43F ruled explicitly that `run_module()` on a retired identifier answers exactly as it did at `f461630`. |
| 5 | `server/app/simulation/registry.py:612` (`run_all`) | `index = registry_index()` as a lookup table; the population is `ids = only if only is not None else available_modules()` | **not corrected — correct as is** | the **population** comes from `available_modules()` (row 1), which is service-derived. The registry is only the name table. |
| 6 | `server/app/simulation/compute.py:50` | `index = registry_index()` as a lookup over `run["computed"]` | **not corrected — correct as is** | the population arrived from `run_all` → `available_modules()`. Lookup only. |
| 7 | `server/app/simulation/qualification.py:272` (`module_qualification`) | reports `"registered": module_id in index` | **not corrected — correct as is** | a **provenance statement** about what the platform registers, for one named identifier, in a field literally called `registered`. The registry is the right population and the honest one. |

`server/app/simulation/portfolio_health.py:88` already carries Run 43D's note that it uses
`service_index()`, not `registry_index()`.

**Independently confirmed in the DOM:** every surface counted in §1 drew **63**, never 96 or
101. If a production caller were still building a population from the registry, one of those
counts would have read 101.

---

## 3. The full module-by-module before-and-after category mapping

Determined from **`p0-baseline/module_renumbering_map.csv`, the naming authority**, by each
module's own identity, never from the retired numbering and never from the bucket it sat in.
"Bucket BEFORE" and "header BEFORE" are read **out of the rendered DOM**.

**No panel moved. The table is the mapping a Run 51 must apply.**

The mismatch is **wider than Run 49 measured. Run 49 reported four groups. It is seven
instances, and one of them is unassignable.**

| panel | panel title | old id(s) | current category, from the authority | bucket BEFORE | header BEFORE | agrees? |
|---|---|---|---|---|---|---|
| `01` | Hybrid Dynamic Simulation | composite (EVM + Monte Carlo) | A1 Cost and EVM Performance | 1 | Cost and EVM Performance | yes |
| `02` | SPC / CUSUM Anomaly Monitor | 1.2 | A1 Cost and EVM Performance | 1 | Cost and EVM Performance | yes |
| `03` | Document-Risk Extraction | 1.3 (alias of 4.1) | **A4 Document-Derived Condition Signals** | 1 | Cost and EVM Performance | **NO — NEW, not previously reported** |
| `1.4` | Bayesian EAC | 1.4 | A1 Cost and EVM Performance | 1 | Cost and EVM Performance | yes |
| `1.5` | Kalman Filter SPI Smoother | 1.5 | A1 Cost and EVM Performance | 1 | Cost and EVM Performance | yes |
| `1.6` | ARIMA CPI Forecast | 1.6 | A1 Cost and EVM Performance | 1 | Cost and EVM Performance | yes |
| `1.7` | Earned Schedule | 1.7 | A1 Cost and EVM Performance | 1 | Cost and EVM Performance | yes |
| `1.8` | To-Complete Performance Index | 1.8 | A1 Cost and EVM Performance | 1 | Cost and EVM Performance | yes |
| `1.9` | Variance at Completion | 1.9 | A1 Cost and EVM Performance | 1 | Cost and EVM Performance | yes |
| `1.10` | Budget Execution Rate | 1.10 | A1 Cost and EVM Performance | 1 | Cost and EVM Performance | yes |
| `1.11` | CPI Shrinkage Forecast | 1.11 | A1 Cost and EVM Performance | 1 | Cost and EVM Performance | yes |
| `1.12` | Independent EAC Reconciliation Index | 1.12 | A1 Cost and EVM Performance | 1 | Cost and EVM Performance | yes |
| `2.4` | Schedule Compression Index | 2.4 | A2 Schedule Performance | 2 | Schedule Performance | yes |
| `2.5` | Float Consumption Rate | 2.5 | A2 Schedule Performance | 2 | Schedule Performance | yes |
| `2.6` | S-Curve Deviation | 2.6 | A2 Schedule Performance | 2 | Schedule Performance | yes |
| `2.7` | Milestone Trend Analysis | 2.7 | A2 Schedule Performance | 2 | Schedule Performance | yes |
| `2.8` | Look-Ahead Schedule Health | 2.8 | A2 Schedule Performance | 2 | Schedule Performance | yes |
| `2.9` | Resource Loading Index | 2.9 | A2 Schedule Performance | 2 | Schedule Performance | yes |
| `2.10` | Schedule Risk P80 | 2.10 | A2 Schedule Performance | 2 | Schedule Performance | yes |
| `2.11` | Critical Path Index | 2.11 | A2 Schedule Performance | 2 | Schedule Performance | yes |
| `3.1` | Reference Class Forecast | 3.1 | A3 Cost Risk | 3 | Cost Risk | yes |
| `3.2` | DSM Rework Propagation | 3.2 (alias of 5.1) | **A5 System Dynamics and Complexity** | 3 | Cost Risk | **NO — NEW, not previously reported** |
| `3.3` | Contingency Burn Rate | 3.3 | A3 Cost Risk | 3 | Cost Risk | yes |
| `3.4` | Labor Productivity Index | 3.4 | A3 Cost Risk | 3 | Cost Risk | yes |
| `3.5` | Material Cost Variance | 3.5 | A3 Cost Risk | 3 | Cost Risk | yes |
| `3.6` | Overhead Absorption Rate | 3.6 | A3 Cost Risk | 3 | Cost Risk | yes |
| `3.7` | Cost Risk P80 | 3.7 | A3 Cost Risk | 3 | Cost Risk | yes |
| `3.8` | Analogous Estimate Ratio | 3.8 | A3 Cost Risk | 3 | Cost Risk | yes |
| `3.9` | Parametric Cost Index | 3.9 | A3 Cost Risk | 3 | Cost Risk | yes |
| `3.10` | Inflation Adjustment | 3.10 | A3 Cost Risk | 3 | Cost Risk | yes |
| `4.1` | Document Risk Score | 4.1 | A4 Document-Derived Condition Signals | 4 | Document-Derived Condition Signals | yes |
| `4.2` | RFI Velocity | 4.2 | A4 | 4 | Document-Derived Condition Signals | yes |
| `4.3` | Submittal Rejection Rate | 4.3 | A4 | 4 | Document-Derived Condition Signals | yes |
| `4.4` | NCR Rate | 4.4 | A4 | 4 | Document-Derived Condition Signals | yes |
| `4.5` | Weather Day Impact | 4.5 | A4 | 4 | Document-Derived Condition Signals | yes |
| `4.6` | Change Order Frequency | 4.6 | A4 | 4 | Document-Derived Condition Signals | yes |
| `4.7` | Dispute Escalation Index | 4.7 | A4 | 4 | Document-Derived Condition Signals | yes |
| `4.8` | Subcontractor Performance | 4.8 | A4 | 4 | Document-Derived Condition Signals | yes |
| `4.9` | Procurement Lead Time | 4.9 | A4 | 4 | Document-Derived Condition Signals | yes |
| `4.10` | Spec Conflict Index | 4.10 | A4 | 4 | Document-Derived Condition Signals | yes |
| `5.1` | DSM Propagation | 5.1 | A5 System Dynamics and Complexity | 5 | System Dynamics and Complexity | yes |
| `5.2` | Sensitivity Analysis | 5.2 | A5 | 5 | System Dynamics and Complexity | yes |
| `5.3` | Tornado Ranking | 5.3 | A5 | 5 | System Dynamics and Complexity | yes |
| `5.4` | Scenario Modeling | 5.4 | A5 | 5 | System Dynamics and Complexity | yes |
| `5.5` | Rework Feedback Loop | 5.5 | A5 | 5 | System Dynamics and Complexity | yes |
| `5.6` | Queueing Bottleneck | 5.6 | A5 | 5 | System Dynamics and Complexity | yes |
| `5.7` | Agent-Based Supply Chain | 5.7 | A5 | 5 | System Dynamics and Complexity | yes |
| `5.8` | Discrete Event Simulation | 5.8 | A5 | 5 | System Dynamics and Complexity | yes |
| `09` | Conservative Dominance: Signal Synthesis | 6.1 | **B1 Signal Synthesis** | 6 | Delivery Quality Performance | **NO** |
| `6.1` | Conservative Dominance | 6.1 | **B1 Signal Synthesis** | 6 | Delivery Quality Performance | **NO** |
| `6.2` | Weighted Voting | 6.2 | **B1 Signal Synthesis** | 6 | Delivery Quality Performance | **NO** |
| `6.3` | Majority Rules | 6.3 | **B1 Signal Synthesis** | 6 | Delivery Quality Performance | **NO** |
| `6.4` | Worst-N-of-M | 6.4 | **B1 Signal Synthesis** | 6 | Delivery Quality Performance | **NO** |
| `7.1` | Dempster-Shafer Theory | 7.1 | **B2 Evidence Combination** | 7 | Signal Synthesis | **NO** |
| `7.2–7.8` | Evidence Methods | 7.2–7.8 | **B2 Evidence Combination** | 7 | Signal Synthesis | **NO** |
| `7.9–7.20` | Advanced Methods Comparison | 7.9–7.20 | **B2 Evidence Combination** | 7 | Signal Synthesis | **NO** |
| `19` | ABM Governance Layer | 8.1 | **B3 Regulatory and Authority Thresholds** | 8 | Evidence Combination | **NO** |
| `8.1` | Agent-Based Governance Model | 8.1 | **B3 Regulatory and Authority Thresholds** | 8 | Evidence Combination | **NO** |
| `8.2–8.9` | **Compliance Modules** | 8.2, 8.3, 8.4, 8.5 → **B3**; 8.6, 8.7, 8.8, 8.9 → **A6** | **TWO CATEGORIES** | 8 | Evidence Combination | **NOT DETERMINABLE — STOP CONDITION 9.2** |
| `9.1` | Missing Data Index | 9.1 | **C1 Data Integrity** | 9 | Regulatory and Authority Thresholds | **NO** |
| `9.2–9.7` | Data Quality Modules | 9.2–9.7 | **C1 Data Integrity** | 9 | Regulatory and Authority Thresholds | **NO** |
| `10.1` | Multi-Objective Optimization | 10.1 | B4 Decision Optimization | 10 | Decision Optimization | yes |
| `10.2–10.7` | Optimization Modules | 10.2–10.7 | B4 Decision Optimization | 10 | Decision Optimization | yes |

**Fourteen further panels — `04`, `05`, `06`, `07`, `08`, `10`, `11`, `12`, `13`, `14`, `15`,
`16`, `17`, `18` — did not render on this fixture** (the legacy blob does not reach them), so
their bucket is **NOT DETERMINABLE FROM THIS DOM** and is not claimed. Their correct
categories, from the authority alone, are: `04`→A2, `05`→A2, `06`→A2, `07`→A3, `08`→**A5**,
`10`–`18`→B2. That is Run 49's incidental finding 3, unchanged.

**Which panels would move, and to where** (the work a Run 51 must do):

| from bucket / header | to category | panels |
|---|---|---|
| 1 Cost and EVM Performance | **A4 Document-Derived Condition Signals** | `03` |
| 3 Cost Risk | **A5 System Dynamics and Complexity** | `3.2` (and `08`, unmeasured) |
| 6 Delivery Quality Performance | **B1 Signal Synthesis** | `09`, `6.1`, `6.2`, `6.3`, `6.4` |
| 7 Signal Synthesis | **B2 Evidence Combination** | `7.1`, `7.2–7.8`, `7.9–7.20` (and `10`–`18`, unmeasured) |
| 8 Evidence Combination | **B3 Regulatory and Authority Thresholds** | `19`, `8.1` |
| 9 Regulatory and Authority Thresholds | **C1 Data Integrity** | `9.1`, `9.2–9.7` |
| 8 Evidence Combination | **NOT DETERMINABLE** | `8.2–8.9` |

**Two mechanical facts a Run 51 needs, both established by reading the executed code:**

1. `groupByCategory` (`deepdive.js:2280`) loops `for (let n = 1; n <= 10; n++)` and takes
   `projectCats[n - 1]`. There are **eleven** project-level categories in service
   (A1–A6, B1–B4, C1). **Bucket 11 can never render.** Today nothing buckets to 11, so nothing
   is lost; the moment `9.1` and `9.2–9.7` are correctly filed under C1 Data Integrity — the
   eleventh — they vanish unless the loop is widened. That is why re-bucketing cannot be done
   by editing the map alone.
2. `A6 Delivery Quality Performance` heads bucket 6 and **has no panel of its own**. Its four
   modules (old 8.6–8.9: quality, safety, environmental, contractor score) are the second half
   of the unassignable `8.2–8.9` panel. That is the root of stop condition 9.2: one panel is
   drawn for eight modules that no longer share a category.

**Stop condition 9.2, stated exactly.** Panel `8.2–8.9` "Compliance Modules" prints the note
*"FAR, OMB, EVM reporting, quality, safety, environmental, contractor score."* Under the current
taxonomy FAR / OMB / EVM-reporting / contract-modification are **B3 Regulatory and Authority
Thresholds**, and quality / safety / environmental / contractor-score are **A6 Delivery Quality
Performance**. One panel, two categories. **It was not assigned. "Not determinable" is recorded
rather than a plausible reconstruction.**

---

## 4. The taxonomy regeneration

**Command run** (read-only verification; nothing was regenerated because nothing was changed):

```
cd server/tools && python3 build_client_taxonomy.py --check
→ both client artifacts are exactly what the authorities generate
→ exit 0
```

`assets/js/categories.js` and `assets/js/taxonomy.js` **both match their generator**, verified
by **re-running the generator and comparing**, not by letting either file check itself.

**Both already carry the population in service:** 12 categories, **63** modules. Confirmed by
executing each file in `node` and counting:
`categories.js → cats 12, modules 63`; `taxonomy.js → cats 12, modules 63`. The generator
(`build_client_taxonomy.py:70`) reads **`REG.service_index()`**, not `registry_index()`, and
drops every retired identity before emitting.

**A finding the order's §5.3 item 1 needs before a Run 51 acts on it, reported rather than
argued.** The order directs `app.js:1346` and `:1360` to be corrected *by changing
`taxonomy_authority.json` and regenerating*. The string those two lines render is the module's
and the category's **`num`** — `A1.2`, `A1`. **`num` is not a display field; it is the primary
key.** It is `REG.VALIDATED[mid]`, the key of `service_index()` and `registry_index()`, and it
is read as a key at `decision.js:407` and `:426`, `projectnet2d.js:65`, `signals.js:423/430`,
`detail.js:381/473/1589/2565`, `deepdive.js:1835/1849` and `neural_flow.js:150`. Removing it
from the authority would break dispatch. The correction therefore has to be made where the
identifier *becomes user-facing text* — the two render sites in `app.js` — with the authority
left as the key table it is. **That is a deviation from the letter of §5.3 item 1 and it is
recorded here for the owner to rule on, not silently taken.**

---

## 5. Sequence-bearing files

**The six were re-verified from `server/tools/participant_packages.py` `SEQUENCE_BEARING_FILES`
before anything was examined**, exactly as the order requires:
`assets/js/decision.js`, `assets/js/decision-ui.js`, `assets/js/workspace.js`,
`assets/js/deepdive.js`, `assets/questionnaires/intake.json`, `assets/questionnaires/debrief.json`.

**NOT ONE OF THEM MOVED. No exception record was written, because no exception was needed.**
`git status --porcelain` at the end of the run reports one line, and it is the new browser
driver: `?? server/tools/drive_run50_browser.py`.

**Measured en/em dash counts (whole file, U+2014 + U+2013), for the Run 51 that moves them:**

| sequence-bearing file | em (U+2014) | en (U+2013) | total | Run 49 recorded |
|---|---|---|---|---|
| `assets/js/decision.js` | 25 | 1 | **26** | 26 |
| `assets/js/decision-ui.js` | 21 | 0 | **21** | 21 |
| `assets/js/workspace.js` | 32 | 0 | **32** | 32 |
| `assets/js/deepdive.js` | 53 | 44 | **97** | 97 |
| `assets/questionnaires/intake.json` | 7 | 0 | **7** | 7 |
| `assets/questionnaires/debrief.json` | 1 | 0 | **1** | 1 |

Every count reproduces Run 49's exactly. `intake.json:55` is still the participant-facing
`"PMP — Project Management Professional"`. `workspace.js:136` is still `return "—";`, a
rendered placeholder that ruling 3 requires be replaced with text saying what it means.

**The true size of guarantee 1, measured across all of `assets/` on non-comment lines:
562 en/em dashes across 39 files**, of which `assets/css/radar.css` holds 72 (stylesheet, not
user-facing text), `assets/vendor/xlsx.full.min.js` holds 39 (a vendored minified library), and
the two **generated** taxonomy artifacts hold 18 between them (`categories.js` 7,
`taxonomy.js` 11) and must be corrected at the authority, never in the output. The remainder —
about 433 across 35 hand-maintained files — is the real sweep, and it is roughly ten times the
four-file scope Run 49 was blocked on.

### 5.1 The §5.3 item 4 / test 10 injection — EXECUTED AND PROVED

A sequence-bearing file moving **without** its own record must still turn the gate red. Proved
by injection, with the protocol the order tightened after Runs 48 and 49 both aborted
mid-injection: snapshot → inject → **re-read the bytes from disk** → observe RED for the
intended reason → restore inside a `finally` that cannot be skipped → assert restored bytes ==
snapshot → re-run and recheck the baseline.

```
snapshot: assets/js/workspace.js  53518 bytes  sha256 444535e9bb76af7fde3aa3901761480b8c4a4f810de08daa8c9db8ef64b8ca49
declared exception set for v17->v18: decision-ui.js, deepdive.js  -> workspace.js is OUTSIDE it

BASELINE BEFORE INJECTION      RESULT: 34/34 checks passed   blocked rows: none
INJECTION: one newline byte appended
  re-read from disk: 53519 bytes  sha256 4d4d90fed900c128a00fa6f6d359796935217800a240f74eeaba92e72f1460c9
  the injection LANDED (bytes re-read from disk, not assumed)
  RESULT: 27/34 checks passed
    FAIL  run37.gate.reproduces            [15 fresh vs 15 committed]
    FAIL  run37.gate.B01                   dirty candidate identity
    FAIL  run37.gate.B04                   participant-sequence drift  moved: ['assets/js/workspace.js']
    FAIL  run37.gate.B11                   og-participant-2026.08-v18 files not matching their record: ['assets/js/workspace.js']
    FAIL  run37.gate.blocking_defects_zero [['B01', 'B04', 'B11']]
    FAIL  run37.gate.no_release_while_blocked   blocked=3 record=True report=True
    FAIL  run37.gate.disposition           FINAL_FREEZE_ACCEPTED
RESTORE (in a finally that cannot be skipped)
  restored: 53518 bytes  sha256 444535e9bb76af7fde3aa3901761480b8c4a4f810de08daa8c9db8ef64b8ca49
  restored bytes == snapshot bytes: True
  git diff --quiet assets/js/workspace.js -> exit 0 (clean)
BASELINE RECHECK AFTER RESTORE  RESULT: 34/34 checks passed   blocked rows: none
INJECTION PROVED THE CHECK CAN FAIL: True      BASELINE RECOVERED: True
```

---

## 6. The Portfolio Health flyout — STOP CONDITION 9.1

**What it shows: nothing, on any surface, to anyone. It has no caller.**

Established by execution and by exhaustive search, not by reading one file:

1. `renderCat8Health` is defined at `deepdive.js:2450` and exported at `deepdive.js:2532` as
   `window.LinDeepDive = { render, renderCat8Health }`.
2. **The only occurrence of `LinDeepDive` anywhere in `assets/`, `index.html` or `research/` is
   `research/deepdive.html:119`, and it calls `LinDeepDive.render(...)`, never
   `renderCat8Health`.** `grep -rn "LinDeepDive" assets/ index.html research/` returns exactly
   two lines: the definition and that one call.
3. `index.html:1327` states in terms that **`deepdive.js` is NOT loaded there**. The file is
   loaded only by `research/deepdive.html:77`.
4. **Measured in the rendered DOM:** the driver queried
   `.dd-cat8-health, .dd-health-flyout` on a fully-loaded deep-dive surface with 63 panels
   drawn. Result: **`Portfolio Health flyout present on this surface: False`** — check
   *"PORTFOLIO HEALTH RENDERS NOWHERE on the deep-dive surface"* **PASSED**.

**What it reads.** `cat8HealthData()` reads the stored `portfolio_health.json` snapshot through
`LinStore.getPortfolioHealth()`, falling back to scanning `window.LIN_PROJECTS`'
`simulationSignals.signal_array` for the five Group D method classes
(`Isolation_Forest`, `Portfolio_Outlier`, `Trajectory_Classifier`, `Cross_Project_Pattern`,
`Anomaly_Score`). Since Run 43 retired all five, `data.anyData` is always false, and
`cat8Retired()` — which is **derived** from the loaded taxonomy, not hardcoded — is true, so
the only body it could ever draw is the retired-state sentence: *"Portfolio Health is no longer
in service. The analysis that compared a project against the rest of the portfolio was
withdrawn…"*.

**Why it was not removed. Stop condition 9.1 fires.** Removing `renderCat8Health` removes
**three button controls** from the served bytes:

| line | control |
|---|---|
| `deepdive.js:2467` | `<button type="button" class="btn primary small" data-run-portfolio-analysis>Rebuild signals (repair)</button>` |
| `deepdive.js:2486` | `<button type="button" class="dd-link" data-refresh-health>refresh</button>` |
| `deepdive.js:2494` | `<button type="button" class="cat8-flagged-row" data-open-project="…">` (row click → `openProject`) |

The first of those delegates to `#recompute-all-btn`, which is a **live control on the
Portfolio page** (`index.html:563`). §5.4 item 4 and stop condition 9.1 both say: if removing it
would remove a control, **stop and report before acting**. §7 of the dispatch adds: *"Do not act
and then report."* **Nothing was removed. What the surface showed before is what is there now:
nothing, because it renders nowhere.**

**The decision the owner must make** is in §11 item 1.

---

## 7. `research/deepdive.html` — STOP CONDITION 9.8

**The finding, established by execution.**

`LinDeepDive.render(project, root)` opens with
`if (!window.hasSignals || !hasSignals(project))` and, when that is false, writes
*"Awaiting analysis: no signal inputs yet."* and returns. `hasSignals` is
`store.js:727`:

```js
function hasSignals(p) {
  return !!(p && p.signals && p.signals.evm && p.signals.cusum && p.signals.mc && p.signals.doc);
}
```

That is the **legacy client-side blob**. The document pipeline never writes it: `projectupload`
extracts, `projectcompute` writes the server-side computed row, and `get` serves
`signalInputs` and `module_results`. `project.signals` stays empty, so `hasSignals` is false and
a project computed entirely through the normal pipeline shows the awaiting sentence. **This run
had to write that blob through the real `save` route, from the `signals` block of
`p0-baseline/contracts/get/get.json`, to make the surface draw at all.**

**Why the repair is NOT confined to the read path, which is what fires 9.8.** The gate is not
the only thing that reads the blob — **every panel body computes from it**. `m01` opens
`const e = p.signals.evm, m = p.signals.mc;` and derives its CPI, SPI, P80-EAC-overrun and
milestone-delay bands straight from those objects; the same pattern runs through all 77 panel
functions. Re-pointing the surface at `signalInputs` / `module_results` would not change *where*
the same numbers come from — it would change **which numbers are shown**, because the legacy
blob and the stored row are different computations of different vintages. That is precisely
*"would change what the surface shows"*. **Stop condition 9.8. REPORTED, NOT REPAIRED, and the
surface was not redesigned — which §5.5 forbids in this run anyway.**

The capture at `p0-baseline/contracts/get/get.json` was **read only and never modified**. Its
own `signalInputs` are still refused by the live write path
(`environmentalComplianceRate` 78.8 against a bound of 1), so only the `signals` block was used.

---

## 8. Every guarantee at §6, verified or not met, with its injection

| # | guarantee | verdict | the injection that proved the check can fail |
|---|---|---|---|
| 1 | Every surface at §5.1 renders exactly the population in service, counted in a browser | **PARTLY VERIFIED.** Five of the six named surfaces render **63**, counted in the DOM (§1 rows 1–5) and already did before this run. **NOT MET** for the deep-dive Signal Stack, whose 77 panels are hard-coded call sites, not the taxonomy | not injected: the run halted before the edit that would need a fault to prove it |
| 2 | No surface draws a retired module, asserted by name against the retired set | **NOT MET, and measured.** The deep-dive draws panels for retired identities — `2.4`, `2.5`, `2.6`, `2.10`, `2.11`, `3.5`, `3.9`, `5.3`, `7.1`, `7.2–7.8`, `10.1` all rendered and every module they name is in the 38-strong retired set | not injected — the defect is present, so no fault is needed to show the check would fail |
| 3 | Every remaining `registry_index()` caller either should be the registry, with its reason, or is corrected | **VERIFIED** (§2). Seven production call sites, all lookups, provenance or the definition of the service population itself. Zero build a population from the registry | the DOM counts are the converse proof: had one been wrong, a surface would have drawn 101 |
| 4 | Every module is filed under and labelled with its current-taxonomy category, per module | **NOT MET.** Seven mis-filings measured (§3), one panel unassignable | not injected: nothing was moved |
| 5 | No module is filed under a category whose name does not describe it | **NOT MET** — same evidence | as above |
| 6 | `categories.js` matches its generator, run from `taxonomy_authority.json` | **VERIFIED** by **re-running the generator and comparing**: `build_client_taxonomy.py --check` → *"both client artifacts are exactly what the authorities generate"*, exit 0. The file was not allowed to validate itself | not injected this run; the generator's `--check` arm is itself the fault detector and Run 49 exercised it |
| 7 | **Guarantee 1 of Run 49 is MET** | **NOT MET, for the third run running, and now measured more widely than before.** 63 module chips and 11 category chips render in the Signal Ledger; ten identifier labels render inside the handbook Signal Stack SVG; 562 en/em dashes stand on non-comment lines across 39 files in `assets/` | not injected: the defects are present |
| 8 | Portfolio Health renders nowhere, asserted on every surface | **VERIFIED** (§6). `.dd-cat8-health, .dd-health-flyout` absent from the rendered deep-dive DOM; `renderCat8Health` has no caller anywhere in the served application | the check is non-vacuous because the same query on the same page returned 63 `.dd-panel` nodes |
| 9 | No control was added, moved or removed | **VERIFIED.** Nothing was added, moved or removed. The detail page's controls were counted in the DOM and are unchanged; the flyout removal was **not performed** (stop condition 9.1) | n/a |
| 10 | A sequence-bearing file moving without a record still turns the gate red | **VERIFIED AND EXECUTED** (§5.1). One byte appended to `assets/js/workspace.js`; gate 34/34 → **27/34**, B01, B04 and B11 all red, `blocking_defects_zero` red; restored byte-identically; baseline recovered 34/34 | **the injection is the proof** |
| 11 | The behaviour digest is unchanged from `8fb4d366…` | **VERIFIED.** Gate row B15 reproduced it live from the current tree: `behaviour digest reproduced identically: 8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1`. It could not have moved: no production file was edited | the workspace.js injection turned B01/B04/B11 red while B15 stayed green, which is the correct discrimination |
| 12 | No stored figure changes | **VERIFIED.** No production file was edited; 193 suites 14,591/14,591 green at the end as at the start | as above |
| 13 | No band, status, colour or posture changes | **VERIFIED.** B05 measures 100 served statements against executed behaviour and reports none failing; B06's census is `{ABSTAINS: 89, COMPUTES: 5, SUPPLIED_NOT_COMPUTED: 1, PORTFOLIO_ROUTE: 5}` — identical to Runs 48 and 49 | as above |
| 14 | Modules in service 63, registry total 101, both derived | **VERIFIED.** `len(service_index()) == 63` and `len(registry_index()) == 101`, both called live inside the browser driver and printed: `in service: 63    registry: 101    retired: 38`. Gate B02 measures the same populations independently and reports 0 | n/a |
| 15 | Voting count is exactly 2, `A1.7` and `A1.8` | **VERIFIED.** Gate B09: `CORE_VOTING_MODULES = ['A1.7', 'A1.8']` | n/a |
| 16 | The detail page still opens on the latest computed period, Run 48's four fixtures re-run | **VERIFIED.** `test_run48_current_period.py` **56/56** in the full 193-suite run; its four fixtures (`PRJ-R48-DOCS` opens on 2, `PRJ-R48-GAP` on 4, `PRJ-R48-HIGH` on 48, `PRJ-R48-NONE` returns null without error) unchanged and green | n/a |
| 17 | The successor freeze gate passes in full | **VERIFIED.** 15 blocker classes, 0 blocked; `test_run37_freeze_gate.py` **34/34** | the injection at §5.1 proves the gate is not vacuous |

**A suite printing no result line has not run; a crash is not a pass.** The one file this run
wrote, `server/tools/drive_run50_browser.py`, counts a raise as a failure and prints the
traceback, and does **not** use the `try/finally` + `sys.exit`-in-`finally` shape.

---

## 9. Audit artifacts the suites rewrote, and restored

The full 193-suite run rewrote **18** artifacts — **17 under `code_audit/` plus
`server/tools/run17/coverage.csv`, which is outside it**, exactly as Runs 48 and 49 recorded:

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

All 18 were restored with `git checkout -- code_audit/ server/tools/run17/coverage.csv`.
**None was committed.** The freeze-gate runs and the injection campaign rewrote none: after
them `git status --porcelain` reported only the untracked driver.

---

## 10. Incidental findings, unacted

1. **The mismatch is seven instances, not four.** Run 49 measured four groups. Two further
   mis-filings are reported here for the first time, both traceable to an **alias row** in the
   renumbering map rather than to the 6/7/8 shift: panel `03` "Document-Risk Extraction" is old
   `1.3`, an alias of `4.1`, so it belongs to **A4** and is filed under Cost and EVM
   Performance; panel `3.2` "DSM Rework Propagation" is old `3.2`, an alias of `5.1`, so it
   belongs to **A5** and is filed under Cost Risk. The seventh is the unassignable `8.2–8.9`.
2. **`groupByCategory` can never render an eleventh group** (`deepdive.js:2280`,
   `for (let n = 1; n <= 10; n++)`), and C1 Data Integrity is the eleventh project-level
   category in service. Correcting the buckets without widening that loop would make the two
   data-quality panels disappear.
3. **The handbook's Signal Stack SVG carries ten retired module identifiers as visible text**
   (`knowledge.js:417`): `01 EVM`, `02 CUSUM`, `03 Doc Risk`, `04 Synthesis`, `05 ABM`,
   `06 PERT`, `07 LOB`, `08 CCPM`, `09 RCF`, `10 DSM`, and its accessible name says
   *"Signal stack of 10 categories"* where eleven project-level categories are in service. **No
   previous sweep reached it, because SVG `<text>` does not appear in `innerText`** — which is
   also why this run's own handbook probe found the `96` literal but not these. Any future
   guarantee-1 sweep must read SVG text nodes explicitly.
4. **`knowledge.js:585` is a literal, not a derived count**, and is the source of the "96" the
   owner saw. The two neighbouring articles (`:554`, `:600`) already state 101 registered and 63
   in service correctly, which is why the same page can be right in one paragraph and wrong in
   the next.
5. **`assets/vendor/xlsx.full.min.js` holds 39 en/em dashes** and `assets/css/radar.css` holds
   72. Neither is hand-maintained user-facing prose. Guarantee 1 as written does not exclude
   them, and it should say whether it means to.
6. **`deepdive.js:2464` is a PROJECT identifier, not a module identifier** (Run 49 §1.4).
   Re-confirmed, not re-flagged. The `mod-mono` class on it will make a naive sweep flag it
   again.
7. **`CAT8_MODULES[].num` (`D1.1`–`D1.5`) is still an unread field** — Run 49 removed its only
   reader. Left in place.
8. **Run 47's handoff entry is still at the BOTTOM of `T6_HANDOFF.md`**, against that file's own
   rule. Runs 48 and 49 reported it and left it; this run does the same. Moving it rewrites
   history.
9. **The deep-dive panels carry hard-coded illustrative figures** (`"3 of 8"`, `"73%"`,
   `metricBox("Audit trail","100%","amber")`). They are not stored figures and no stop condition
   applies, but a Run 51 that re-buckets those panels should know it is moving illustrations,
   not computed values.
10. **Playwright 1.48 in this environment cannot find its own browser.** It expects
    `chromium-1140`; the image ships `chromium-1194` and `chromium_headless_shell-1194` under
    `/opt/pw-browsers`. An explicit `executable_path` plus `--headless=new` is required — the
    old headless mode has been removed from the binary. Recorded so the next run does not spend
    the time again.

---

## 11. What the next session needs, stated as decisions for the owner

1. **The Portfolio Health flyout, and whether an unreachable button is a control.** It renders
   nowhere — it has no caller anywhere in the served application — but its markup contains three
   buttons, and stop condition 9.1 fired on that. **Decide:** (a) an unreachable control is not a
   control, so remove `renderCat8Health`, `CAT8_MODULES`, `cat8HealthData`,
   `cat8HealthDataFromLive`, `isSnapshotStale` and `cat8Retired` outright, taking the three
   buttons with them; or (b) it is a control, so leave the dead surface in place and record it as
   an accepted limitation. **This run cannot choose. It is exactly the case §5.4 item 4 reserved
   to you.**
2. **Panel `8.2–8.9` "Compliance Modules", which cannot be filed.** It draws eight modules that
   the current taxonomy splits between B3 Regulatory and Authority Thresholds (old 8.2–8.5) and
   A6 Delivery Quality Performance (old 8.6–8.9). **Decide:** (a) split it into two panels, one
   per category — which adds a panel and changes what a participant sees; (b) file the whole
   panel under B3 and rename it so its note names only the four regulatory modules — which drops
   four modules from the surface; or (c) leave it where it is and record it. **Until this is
   ruled, §5.2's "every module is filed under the category it belongs to" cannot be delivered,
   and that is why this run did not merge a partial re-bucketing.**
3. **`num` is a key, not a label.** §5.3 item 1 directs the `app.js` identifiers to be corrected
   in `taxonomy_authority.json`. `num` is the primary key of the registry and of eleven client
   call sites (§4). **Decide:** authorise the correction at the two `app.js` render sites with
   the authority left as the key table it is, or order a key rename across the registry, the
   authority, both generated mirrors and every consumer.
4. **Guarantee 1's true scope.** It is not four sequence-bearing files. It is 562 en/em dashes
   across 39 files, plus 74 identifier chips in the Signal Ledger, plus ten identifier labels
   inside an SVG no sweep has read. **Decide:** (a) authorise the full sweep, naming the
   vendored library and the stylesheet in or out; (b) narrow the guarantee to hand-maintained
   user-facing prose and say so in the limitation contract. Until one of these is chosen,
   guarantee 1 will be reported NOT MET by every subsequent run, as it has been by three.
5. **The eleventh group.** `groupByCategory` loops to 10 and there are 11 project categories in
   service. Widening it is a prerequisite for filing the data-quality panels correctly, and it
   makes an eleventh collapsible group appear on the surface. **Decide:** widen it, or accept
   that C1 Data Integrity has no group of its own on the deep dive.
6. **`research/deepdive.html`.** Stop condition 9.8 fired: the surface does not merely *gate* on
   the legacy blob, it *computes* from it in all 77 panel bodies, so re-pointing it changes what
   it shows. **Decide:** order a redesign of that surface as its own run, or record it as a
   research-only surface that requires the legacy blob and is out of the participant path.
7. **Whether Run 50 should have stopped at all.** Stop conditions 9.1, 9.2 and 9.8 are each
   worded locally in §5 ("stop and report before acting", "do not assign it", "otherwise stop and
   report") and collectively in §9 as run-level. This run read §9 and the dispatch instruction
   literally and halted with `main` untouched. **Decide:** if you intend §5's local wording to
   govern, say so and a Run 51 can proceed with items 1, 2 and 6 carved out and everything else
   delivered.

---

## Carried forward, unacted, so they are not rediscovered

1. **CPI 1.22 on the site render.** Run 46 established the code cannot narrow it further; it
   needs read access to PRJ-001's stored rows, which no session may have. The remaining question
   is which document type wrote `pv`.
2. **The `historical_data` triple**, Run 47's only unimplemented relation, awaiting a ruling on
   whether "a known BAC" means this project's or any the same document states.
3. **`signal_inputs.sources` records no source field name**, so a finding cannot say which cell
   of a document a figure came from.
4. **Four status comparisons remain case-sensitive**, two in `decision.js`.
5. **Two Run 45 census artifacts do not match the v30 release manifest.**
6. **`test_run47_evm_consistency.py` swallows its own traceback** in a `finally` with
   `sys.exit`. Left alone this run, as instructed.

---

## The freeze gate, every row with its verdict

Re-run live from the current tree at the end of the run. `test_run37_freeze_gate.py`:
**34/34 checks passed**, 15 blocker classes, **0 blocked**.

| row | blocker | count | requirement | evidence | result |
|---|---|---|---|---|---|
| B01 | dirty candidate identity | 0 | = 0 | 11 content-addressed digests recomputed from the tree and compared; git porcelain lines at evaluation: 2 | **PASS** |
| B02 | population mismatch | 0 | = 0 | registered total=101 expected 101; project scientific targets=95 expected 95; Portfolio Health targets=5 expected 5; scientific targets=100 expected 100 | **PASS** |
| B03 | controlled-stimulus mismatch | 0 | = 0 | projects=6, periods/project=[6], unique=36, rows=36, duplicates=0, missing=0 | **PASS** |
| B04 | participant-sequence drift | 0 | = 0 | 6 sequence-bearing files compared against the og-participant-2026.08-v18 record; moved: none | **PASS** |
| B05 | false defensibility statement | 0 | = 0 | 100 served statements measured against EXECUTED behaviour; failing: none | **PASS** |
| B06 | unexpected execution exception | 0 | = 0 | census {'ABSTAINS': 89, 'COMPUTES': 5, 'SUPPLIED_NOT_COMPUTED': 1, 'PORTFOLIO_ROUTE': 5}; populated analytical results 3: ['A1.7', 'A1.8', 'A6.2'] | **PASS** |
| B07 | Category-9 bypass | 0 | = 0 | unqualified-package probes reaching a banded result: none; C-group voters: none; group C contributes to project status: False | **PASS** |
| B08 | Category-10 authority violation | 0 | = 0 | human_authorization_required True, creates_project_evidence False, and no Category-10 identity in the voting set | **PASS** |
| B09 | voting count is not exactly 2 | 0 | = 0 | CORE_VOTING_MODULES = ['A1.7', 'A1.8'] | **PASS** |
| B10 | current taxonomy dual authority | 0 | = 0 | one authority present=True; both mirrors trace to the generator=True; runtime lookups failing across all 101 registered modules: none | **PASS** |
| B11 | package or predecessor mutation | 0 | = 0 | rewritten predecessor package records: none; og-participant-2026.08-v18 files not matching their record: none; live stamp sim-2026.08-v33 (expected sim-2026.08-v33); predecessor e3d1b698b479 still stamped sim-2026.08-v32: True | **PASS** |
| B12 | browser qualification failure | 0 | = 0 | 29 rows; failing: none | **PASS** |
| B13 | unresolved blocking Run-36 defect | 0 | = 0 | open instrument-level defects: none; target rows carrying one: none | **PASS** |
| B14 | unsupported final empirical-validation claim | 0 | = 0 | every one of the 100 rows records NOT_EMPIRICALLY_FIELD_VALIDATED; exceptions: none | **PASS** |
| B15 | candidate behaviour changed during the run | 0 | = 0 | behaviour digest reproduced identically: **8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1** | **PASS** |

Beyond the fifteen blocker rows the suite also passed: `generator_runs`, `artifact_present`,
`reproduces` (the gate is not a stale snapshot), `fifteen_blocker_classes`,
`blocking_defects_zero`, `predecessor_release_preserved` (v25), five
`immediate_predecessor_release_preserved` rows (v26, v27, v28, v30, v31),
`no_release_while_blocked`, `release_present_when_clean`, four `limitation_stated` rows,
`disposition` (FINAL_FREEZE_ACCEPTED) and `no_self_reference`. **34/34.**

**No stamp was minted and no merge was made. `main` remains at `ad4f614`.**
