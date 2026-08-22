# Run 49: the completion of the naming correction

**Date:** 2026-08-22. **Repository:** the Linux clone at `/home/user/LinPRojectRadar` (the Windows
path was not used). **Interpreter:** the documented fallback, `python3` **3.11.15** at
`/usr/local/bin/python3`; this clone carries no `.venv`, so `server/run_all_suites.sh` fell through
to the interpreter on PATH, which is what it is written to do.

**Branch:** `run49-naming-completion`, rooted at `5838a23`, merged to `main` with `--no-ff`.
**Stamp:** `sim-2026.08-v33` (was `sim-2026.08-v32`). **Participant package:**
`og-participant-2026.08-v18` (was v17). **Suites:** 193 run, **14,591 / 14,591 checks, ALL SUITES
GREEN.** **Freeze gate:** 15 blocker classes, **0 blocked**; the gate suite reports **34/34**.

**Browser sessions** were run from a clean subdirectory,
`/tmp/.../scratchpad/run49work/clean`, never the scratchpad root, and the driver printed that cwd.
The DEng\Demo tell was checked before anything else was measured: **7 `.page` sections**, and
neither `api.js` nor `boot.js` in `document.scripts`. Final driver result: **23/23**.

The authority this run is measured against, quoted verbatim from `NAMING_AUTHORITY.md:96`:

> **Never use a module id or number in user-facing text.** No "Cat 4", no "1.7", no "PH.2", no
> "A4.2". Groups and purposes only. The old "Cat N" scheme is retired along with the names.

---

## 1. Every site corrected, before and after, and how each was verified

All line numbers were verified against the current tree before editing, not trusted. Every one of
the order's §5.1 citations was accurate.

### 1.1 The sites the order enumerates

| site | before | after | verified |
|---|---|---|---|
| `deepdive.js:2268` — the ten group headers | `<span class="dd-cat-name"><span class="mod-mono">Cat ${n}</span> ${escg(catName)}</span>` | `<span class="dd-cat-name">${escg(catName)}</span>` | **rendered DOM** |
| `deepdive.js:1059` | `The classification feeds Cat 8.1, which maps it to an action and an authority.` | `The classification feeds the governance decision layer, which maps it to an action and an authority.` | source-verified; this arm renders only on a conflicting-signal project and the fixture did not reach it |
| `deepdive.js:1404` | `metricBox("Agrees with Cat 6.1", ...)` | `metricBox("Agrees with Conservative Dominance", ...)` | source-verified; the Dempster-Shafer panel did not render on this fixture |
| `deepdive.js:1831/:1834/:1837` | `... agree with the Cat 6.1 baseline (...). Act on the Cat 8.1 recommendation.` | `... agree with the conservative dominance baseline (...). Act on the governance recommendation.` | source-verified; the synthesis comparison panel needs the full ten-method signal array |
| `deepdive.js:1841` | `<b>Synthesis Methods Comparison: Cat 6.1 & Cat 7.1–7.9</b>` | `<b>Synthesis Methods Comparison: Conservative Dominance and the Evidence Combination Methods</b>` | source-verified. Three faults in one string — an identifier, an ampersand and a real EN DASH (U+2013) — all three removed |
| `deepdive.js:1842` | `Conservative dominance (Cat 6.1) is the governance baseline; Cat 7.1–7.9 provide independent cross-checks ...` | `Conservative dominance is the governance baseline; the evidence combination methods provide independent cross-checks ...` | source-verified |
| `deepdive.js:2189` — the banner | `Cat 1–Cat 3 modules are quantitative signal generators. Cat 6.1 (Conservative Dominance) is the baseline synthesis. Cat 7.1–7.9 are independent evidence-combination methods cross-checking Cat 6.1 ... Cat 8.1 (ABM Governance) is the decision output ...` | `The cost performance, schedule performance and cost risk modules are quantitative signal generators. Conservative Dominance is the baseline synthesis. The evidence combination methods are independent cross-checks on that baseline ... ABM Governance is the decision output ...` | **rendered DOM**, read back verbatim |
| `detail.js:1741` — the model instruction | see §1.3 | see §1.3 | not a DOM surface; source-verified, and asserted by the suite |
| `detail.js:1086` — the ampersand | `${cs("d-docsignals", "Documents & Extracted Signals",` | `${cs("d-docsignals", "Documents and Extracted Signals",` | **rendered DOM** |

**Stated plainly rather than dressed up.** Six of the nine could **not** be read back from a
rendered DOM, and the reason is one fixture property, not a claim about the code: `deepdive.js`
renders 63 panels for this project, and the panels that carry those six strings (the Dempster-Shafer
belief panel, the synthesis comparison panel and the conflict arm of the conservative-dominance
panel) need a signal array this fixture's captured `signals` blob does not populate. They were
verified in source, and each is asserted by `test_run49_naming_completion.py` **both ways**: the
retired text is absent from the tree AND present in the v32 blob, so none of those checks can pass
vacuously.

### 1.2 Three further live instances no order named, found by this run's own sweep

The order's §5.1 instruction to "sweep again after correcting and report any surviving live
instance" turned up three more rendered module identifiers in the same file. All three are in
`deepdive.js`, which ruling 1 authorises to move, and all three are corrected.

| site | before | after |
|---|---|---|
| `deepdive.js` synthesis table, row cell | `<td class="dd-cmp-mod">Module ${e.num}: ${esc(e.label)}</td>` — rendered `Module 09: Conservative Dominance`, `Module 10: Dempster-Shafer`, and so on for ten rows | `<td class="dd-cmp-mod">${esc(e.label)}</td>` |
| `deepdive.js` synthesis table, header | `<th>Module · Method</th> ... <th>Agrees with M09</th>` | `<th>Method</th> ... <th>Agrees with the baseline</th>` |
| `deepdive.js:2472` Portfolio Health flyout | `<b>${esc(m.num)} ${esc(m.name)}</b>` — rendered `D1.1 Isolation Forest` through `D1.5 Anomaly Score` | `<b>${esc(m.name)}</b>` |

### 1.3 `detail.js:1741`, which is an instruction to the model, not a label

The parent session was right that this is a guardrail and deleting it would remove a guard. The
sentence was **rewritten so the instruction keeps its force**.

**Before:**

> Do NOT mention category numbers except when grouping them in Signal Pattern; a program director
> does not think in Cat 1-12.

**After:**

> Do NOT print any module identifier or category number anywhere in the briefing: name what a
> category DOES, in words. A program director thinks in purposes, not in identifiers.

The new wording is **stronger**, not weaker: the old one carved out an exception ("except when
grouping them in Signal Pattern") that permitted the model to print numbers on one section. The
new one has no exception. `test_run49_naming_completion.py` asserts both halves — that `Cat 1-12`
is gone AND that `Do NOT print any module identifier or category number` is present — so a future
run cannot satisfy the first by deleting the sentence.

### 1.4 `deepdive.js:2464`, the site the parent session flagged: **established by execution, and it
is NOT a module identifier**

The parent asked that this be established rather than guessed from the variable name. It was traced
to its source rather than inferred:

* `deepdive.js:2462-2464` renders `<span class="cat8-flagged-id mod-mono">${esc(f.id)}</span>`
  inside a row whose sibling spans are `f.name` and `f.status`, and whose button carries
  `data-open-project="${esc(f.id)}"`.
* `f` is an element of `m.flagged`, built in exactly two places. `cat8HealthDataFromLive`
  (`:2342`): `flagged.push({ id: p.id, name: p.name, ... })` where `p` iterates
  `window.LIN_PROJECTS`. `cat8HealthData` (`:2377`): `flagged.push({ id: pid, name: entry.name || pid, ... })`
  where `pid` iterates the keys of the Portfolio Health results map, which is keyed by project id.
* The click handler at `:2476-2477` calls `openProject(b.dataset.openProject)`.

**`f.id` is a PROJECT identifier — `PRJ-001` and its kind — not a module identifier.** `mod-mono` is
a monospace CSS class, not a claim about content. It is **not** an instance of the class §5.1
enumerates and it is **not** corrected. Reported as the parent asked.

**But the same block did carry a real one, two lines below**, and that is item 3 of §1.2:
`m.num` on the module heading rendered `D1.1` through `D1.5`. That one is corrected.

---

## 2. Every key the call sites pass, with its resolved label

**Established by execution, not by reading.** The set was taken two ways and the two agree:
`test_run49_naming_completion.py` enumerates the first argument of every `panel(` call site in the
served file (**77**, with the one `"XX"` occurrence excluded because it is inside a comment), and
`drive_run49_browser.py` reads the `data-num` attribute of every rendered `.dd-panel` back out of
the DOM (**63** panels — the 14 the fixture does not reach are named in §3).

**All 77 keys now resolve to an explicit label. The map holds exactly those 77 keys and no others**
— it is not padded to pass the check, which the suite asserts in both directions.

| resolved label | keys | how the label was determined |
|---|---|---|
| Cost Performance | 12: `01`, `02`, `03`, `1.4`, `1.5`, `1.6`, `1.7`, `1.8`, `1.9`, `1.10`, `1.11`, `1.12` | Bayesian EAC, Kalman SPI smoother, ARIMA CPI, Earned Schedule, TCPI, VAC, Budget Execution Rate, CPI Shrinkage, Independent EAC Reconciliation — every one is a cost or EVM performance index. `01..03` are Run 48's, unchanged |
| Schedule Simulation | 3: `04`, `05`, `06` | Run 48's, unchanged (PERT, LOB, CCPM) |
| Cost Simulation | 2: `07`, `08` | Run 48's, unchanged (RCF cost prior, DSM rework) |
| Signal Synthesis | 5: `09`, `6.1`, `6.2`, `6.3`, `6.4` | Conservative Dominance, Weighted Voting, Majority Rules, Worst-N-of-M. `09` is Run 48's and is the same module as `6.1` |
| Evidence Combination | 12: `10`–`18`, `7.1`, `7.2–7.8`, `7.9–7.20` | Dempster-Shafer, rough sets, neutrosophic, interval fuzzy, Z-numbers, PLTS, plithogenic, BRB, quantum probability. `10..18` are Run 48's and are the same modules as `7.1–7.9` |
| Governance and Compliance | 3: `19`, `8.1`, `8.2–8.9` | ABM Governance Layer; the compliance modules (FAR, OMB, EVM reporting, quality, safety, environmental, contractor score). `19` is Run 48's and is the same module as `8.1` |
| Schedule Performance | 8: `2.4`–`2.11` | Schedule Compression Index, Float Consumption, S-Curve Deviation, Milestone Trend, Look-Ahead Health, Resource Loading, Schedule Risk P80, Critical Path Index |
| Cost Risk | 10: `3.1`–`3.10` | Reference Class Forecast, DSM Rework, Contingency Burn, Labor Productivity, Material Cost Variance, Overhead Absorption, Cost Risk P80, Analogous Estimate Ratio, Parametric Cost Index, Inflation Adjustment |
| Document-Derived Condition Signals | 10: `4.1`–`4.10` | Document Risk Score, RFI Velocity, Submittal Rejection, NCR Rate, Weather Day Impact, Change Order Frequency, Dispute Escalation, Subcontractor Performance, Procurement Lead Time, Spec Conflict Index |
| System Dynamics and Complexity | 8: `5.1`–`5.8` | DSM Propagation, Sensitivity, Tornado Ranking, Scenario Modeling, Rework Feedback Loop, Queueing Bottleneck, Agent-Based Supply Chain, Discrete Event Simulation |
| Evidence Quality | 2: `9.1`, `9.2–9.7` | Missing Data Index; Data Quality Modules (timeliness, reliability, audit trail, completeness, consistency, frequency) |
| Decision Optimization | 2: `10.1`, `10.2–10.7` | Multi-Objective Optimization; Optimization Modules (LP, constraint satisfaction, what-if, sensitivity, Pareto, regret minimization) |

**Every label came from the MODULE'S OWN TITLE at its own call site, never from the collapsible
group the panel is filed under.** That distinction is load-bearing, and §8 shows why: `6.1` is
labelled *Signal Synthesis* while the group it sits in is headed *Delivery Quality Performance*;
`9.1` is labelled *Evidence Quality* while its group is headed *Regulatory and Authority
Thresholds*. Taking the label from the header would have printed a false description on 19 panels.

**Keys left on the neutral fallback: NONE.** Ruling 3's §5.2 item 4 list is **empty**. Every one of
the 77 keys had a module title that determined its category without a judgement call, so **stop
condition 9.8 did not fire and no category assignment was invented.** The fallback remains in the
code for a key no call site currently passes.

**The measurable effect, from the DOM.** Before this run the 63 rendered panels carried **4**
distinct accessible names, roughly sixty of them reading `Signal Analysis`. They now carry **10**:

```
Cost Performance deep dive              Evidence Quality deep dive
Cost Risk deep dive                     Governance and Compliance deep dive
Decision Optimization deep dive         Schedule Performance deep dive
Document-Derived Condition Signals ...  Signal Synthesis deep dive
Evidence Combination deep dive          System Dynamics and Complexity deep dive
```

`Signal Analysis` — the fallback — reaches **no panel at all**, which the driver asserts.

---

## 3. Panel-by-panel confirmation that every module buckets exactly as before

Measured **in the rendered DOM**, all 63 panels, by reading each panel's `data-num` and `data-cat`
attributes. The full pairing, verbatim from the driver:

```
('01','1') ('02','1') ('03','1') ('09','6') ('19','8')
('1.4','1') ('1.5','1') ('1.6','1') ('1.7','1') ('1.8','1') ('1.9','1')
('1.10','1') ('1.11','1') ('1.12','1')
('2.4','2') ('2.5','2') ('2.6','2') ('2.7','2') ('2.8','2') ('2.9','2') ('2.10','2') ('2.11','2')
('3.1','3') ('3.2','3') ('3.3','3') ('3.4','3') ('3.5','3') ('3.6','3') ('3.7','3') ('3.8','3')
('3.9','3') ('3.10','3')
('4.1','4') ('4.2','4') ('4.3','4') ('4.4','4') ('4.5','4') ('4.6','4') ('4.7','4') ('4.8','4')
('4.9','4') ('4.10','4')
('5.1','5') ('5.2','5') ('5.3','5') ('5.4','5') ('5.5','5') ('5.6','5') ('5.7','5') ('5.8','5')
('6.1','6') ('6.2','6') ('6.3','6') ('6.4','6')
('7.1','7') ('7.2–7.8','7') ('7.9–7.20','7')
('8.1','8') ('8.2–8.9','8')
('9.1','9') ('9.2–9.7','9')
('10.1','10') ('10.2–10.7','10')
```

Against the Run 48 mapping the order names — `01,02,03 -> 1`, `04,05,06 -> 2`, `07,08 -> 3`,
`09 -> 6`, `10..18 -> 7`, `19 -> 8` — **zero panels bucket differently.** Stop condition 9.4 did not
fire.

**Stated plainly rather than dressed up.** This fixture reaches **5** of those 19 mapping rows
(`01`, `02`, `03`, `09`, `19`). The other **14** — `04`, `05`, `06`, `07`, `08`, `10` through `18`
— render **no panel at all** on it, so the DOM cannot speak for them and the driver prints exactly
that line and does not count it as a pass. What IS asserted for all 19, and is stronger than a DOM
read: `CAT_NUM_FROM_MODULE` and `catBucket()` are **byte-identical to their v32 bytes**, asserted by
string equality in `test_run49_naming_completion.py`, and this run did not touch either. A panel
cannot have moved without one of those two moving.

---

## 4. The second sweep, and every surviving live instance with its line number

The sweep was executed over every file in `assets/js`, excluding lines that OPEN with a comment
marker and excluding trailing `//` comments, for: the retired `Cat N` scheme, `M0N` module
identifiers, `PH.N`, `AN.N` and `D1.N`. **43 non-comment lines match.** Classified:

**In `deepdive.js` — nine matches, and every one is explained by its own line content, not
excused:**

| line | what it is | governed? |
|---|---|---|
| `:94` | continuation line of the block comment that QUOTES `NAMING_AUTHORITY.md:96` | no — a comment |
| `:1785`, `:1786` | continuation lines of a block comment describing the baseline | no — a comment |
| `:2257` | continuation line of the block comment recording why Portfolio Health moved (a §2 protected marker) | no — a comment |
| `:2355`–`:2359` | the `num: "D1.1"`..`"D1.5"` fields of `CAT8_MODULES` | no — **this run stopped rendering them**; the suite asserts `${esc(m.num)}` no longer appears anywhere in the file, so it is now a matched-against constant with no reader that prints it |

The sweep only skips lines that OPEN with a marker, so an indented continuation line is caught and
has to be classified rather than waved through; the suite does that classification in code, per
line, and fails if any match is left unexplained.

**Outside `deepdive.js` — 34 matches, and these are the honest finding of this run:**

| file:line | what renders | disposition |
|---|---|---|
| **`app.js:1346`** | `<span class="cat-mod-num">${esc(m.num)}</span>` — renders **`A1.2`, `A1.3`, …** beside every module name on the Categories page | **LIVE, RENDERED, NOT CORRECTED** |
| **`app.js:1360`** | `<span class="cat-row-num" ...>${esc(cat.num)}</span>` — renders **`A1`, `A2`, …** on every category row header | **LIVE, RENDERED, NOT CORRECTED** |
| `app.js:1298-1299` | the §2 protected comment marker | untouched by order |
| `categories.js:422`, `taxonomy.js` (45), `knowledge.js` (60), `ds_defensibility_*.js` (76), `workspace.js:59-104`, `decision-ui.js:71-120` | `num:`/`n:`/`id_display` fields and the KEYS of id→name maps | code constants matched against; the VALUES are what print. `categories.js` and `taxonomy.js` are GENERATED |
| `detail.js:84-86` | `MODULES = [["M01","Monte Carlo"], …]` | **not rendered.** `grep -n "MODULES\b" detail.js` returns the declaration and one use, `MODULES.length`. The labels never reach the DOM |
| `charts3d.js:3`, `decision.js:310`, `neural_flow.js:168-174`, `simulations.js:2380/2614/2616`, `deepdive.js:2202/2226` | comments, including the §2 protected markers | untouched |
| `knowledge.js:2327-2355`, `signals.js:515` | prose naming `PH.1-PH.5` in a handbook body and one comment | reported |

**`app.js:1346` and `app.js:1360` are the surviving live instances.** They are outside every site
§5.1 enumerates, and correcting them is not a text edit: `cat.num` and `m.num` come from
`window.LIN_CATEGORIES` in `assets/js/categories.js`, which carries a `GENERATED BLOCK. Do not edit
by hand.` header and is written by `server/tools/build_client_taxonomy.py` from
`server/tools/taxonomy_authority.json`. A hand edit is reverted by the guard. Correcting them means
changing the authority and regenerating, which is a different change with different blast radius,
and rule 3 of §8 forbids recommending fixes beyond what §3 orders. **Reported, not corrected.**

---

## 5. Every §6 guarantee, verified or not met, with the injection that proved its check could fail

**Eleven fault injections** were executed. The protocol on every one, without exception: snapshot
the file bytes, inject, **re-read the bytes from disk to confirm the injection landed**, run,
observe RED for the intended reason, **restore from the snapshot inside a `finally` that cannot be
skipped**, assert the restored bytes equal the snapshot, re-run, and **recheck the baseline after
every single injection**. Suite baseline **46/46**; browser driver baseline **23/23**. Every
baseline recheck came back at the baseline. **No injected byte reached a commit**, confirmed by
`git status --porcelain` and `git diff --quiet`.

| # | §6 guarantee | verdict | the injection that proved the check can fail |
|---|---|---|---|
| 1 | No user-facing text anywhere in `assets/` carries a module identifier, a category number, the retired scheme, an ampersand, an em dash or an en dash | **NOT MET, and it cannot be met inside stop condition 9.5.** See §5.1 below | I1 (restore the header identifier span) 45/46; I2 44/46; I3 44/46; I4 44/46; I8 44/46; I9 45/46; I10 44/46 — every constituent check is proved able to fail, but the guarantee as written is not met |
| 2 | Every one of the ten group headers renders its group name with no identifier, from the rendered DOM | **verified — rendered DOM** | I11: restore `<span class="mod-mono">Cat ${n}</span>`. Browser **21/23**, the DOM read back `Cat 1 Cost and EVM Performance` and both the header check and the sweep check went red |
| 3 | Every §5.1 site 2–9 corrected, DOM where a surface renders it, plainly source-only where it does not | **verified — three from the DOM, six source-only and said so** (§1.1) | I2 `Cat 8.1` sentence 44/46; I3 metric box 44/46; I4 table row prefix 45/46; I8 brief prompt 44/46; I9 ampersand 45/46; I10 flyout heading 44/46. Each check asserts presence in v32 as well as absence now, so none can pass vacuously |
| 4 | Every key a call site passes resolves to a label naming its own category's purpose | **verified.** 77 of 77; the §5.2 item 4 exception list is EMPTY | I5: delete `"1.4": "Cost Performance"` from the map. Suite **45/46**, red on "no key reaches the neutral fallback", reporting `['1.4']` |
| 5 | Every module buckets exactly as before, panel by panel in the DOM | **verified in the DOM for the 63 panels that render; the grouping map is byte-identical to v32 for all 19 mapping rows** (§3) | I6: change `"09": "6"` to `"09": "7"` in `CAT_NUM_FROM_MODULE`. Suite **45/46**, red on "THE GROUPING MAP IS BYTE-IDENTICAL TO v32" |
| 6 | The §2 comment markers are unchanged, asserted per file by content | **verified** | No injection. These are equality checks on strings this run never touched, and they are made stronger than content equality: `app.js`, `categories.js`, `neural_flow.js` and `taxonomy.js` are asserted **byte-identical to v32 in their entirety**, so no marker in them can have moved. `deepdive.js:2202/2226` are asserted by content |
| 7 | `decision-ui.js` behaviour unchanged: `period: 1` against an assignment at period 3 still returns 3 | **verified** | I7: change one literal from `period: 1` to `period: 2`. Suite **44/46**, red on both "with every whole-line comment removed the two versions are IDENTICAL" and "the three period literals are still there" (`2 vs 3`). The stronger claim is asserted directly: **strip every whole-line comment from the file and it is byte-identical to v32**, so not one byte of executable text changed and the executed behaviour cannot have. `test_run48_current_period.py` section 8, which executes exactly that request against a live research assignment, is **56/56** in the full run |
| 8 | No period text added to any panel, no control added, moved or removed | **verified — rendered DOM** | Measured in the DOM, not asserted: `select` elements under `#detail-root` = **0**; controls under `#detail-root` = 15, unchanged; no `reporting period` or `Period N` text anywhere in the deep-dive host. `test_run28_participant_packages.py` additionally counts `<button`, `<input`, `<select`, `<textarea` and `data-run-portfolio-analysis` in both moved files against v32 and requires the counts equal |
| 9 | The detail page still opens on the latest computed period, Run 48's four fixtures re-run | **verified** | Not by new injection: `test_run48_current_period.py` **56/56** in the full run, and its four fixtures (`PRJ-R48-DOCS` opens on 2, `PRJ-R48-GAP` opens on 4, `PRJ-R48-HIGH` opens on 48, `PRJ-R48-NONE` returns null without error) are unchanged and green |
| 10 | No stored figure changes | **verified** | By construction and by census: every Run-49 change is displayed text or a comment. **B15's behaviour digest is `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1` — byte-for-byte the SAME digest Run 48 recorded**, over 100 scientific targets executed through their real governed routes on the frozen corpus. `test_run6_known_answer.py` 488/488, `test_run45_period_scoping.py` 77/77, `test_run47_evm_consistency.py` 56/56 |
| 11 | No band, status, colour or posture changes | **verified** | Same evidence. B05 measures 100 served statements against executed behaviour and reports none failing; B06's census is `{ABSTAINS: 89, COMPUTES: 5, SUPPLIED_NOT_COMPUTED: 1, PORTFOLIO_ROUTE: 5}`, identical to Run 48's |
| 12 | Modules in service 63, registry 101, both derived | **verified** | `len(service_index()) == 63` and `len(registry_index()) == 101`, both called live in the suite. B02 measures the same populations independently and reports 0 |
| 13 | Voting count exactly 2, `A1.7` and `A1.8` | **verified** | `sorted(CORE_VOTING_MODULES) == ["A1.7", "A1.8"]`, called live; B09 reports the same list |
| 14 | Exactly two sequence-bearing files moved, each with its own record; a third must still turn the gate red | **verified, and the third-file proof was executed** | One byte appended to `assets/js/workspace.js`. The gate went from `[]` blocked to **`[('B01','1','BLOCKED'), ('B04','1','BLOCKED'), ('B11','1','BLOCKED')]`**. Restored byte-identically (`git diff --quiet assets/js/workspace.js` clean); gate back to 0 blocked |
| 15 | The successor freeze gate passes in full | **verified** | 15 blocker classes, 0 blocked; `test_run37_freeze_gate.py` **34/34** |

### 5.1 Guarantee 1, said plainly

Guarantee 1 is **NOT MET**, for the second run running. It is not met because meeting it **would
fire stop condition 9.5**, and the honesty standard prefers an honest NOT MET to a claimed pass.

Two independent obstacles, both measured rather than argued:

1. **`app.js:1346` and `app.js:1360`** render a module identifier and a category identifier on the
   Categories page (§4). Both read from the GENERATED `categories.js`; correcting them requires
   changing `server/tools/taxonomy_authority.json` and regenerating, which no ruling in §3 orders.
2. **En dashes (U+2013) and em dashes (U+2014) remain in user-facing text across roughly forty
   files in `assets/`**, and four of those files are **SEQUENCE-BEARING**. Counted by the suite:

   | sequence-bearing file | en/em dashes | may this run move it? |
   |---|---|---|
   | `assets/js/decision.js` | 26 | **no** |
   | `assets/js/workspace.js` | 32 | **no** |
   | `assets/questionnaires/intake.json` | 7 | **no** |
   | `assets/questionnaires/debrief.json` | 1 | **no** |
   | `assets/js/decision-ui.js` | 21 | moved this run, comments only |
   | `assets/js/deepdive.js` | 97 | moved this run |

   These are not comments. `intake.json:55` is the participant-facing option label
   `"PMP — Project Management Professional"`. `workspace.js:136` is `return "—";`, a rendered
   placeholder. Correcting them moves four more sequence-bearing files, which is exactly what stop
   condition 9.5 forbids and what §6 test 14 proves still turns B01, B04 and B11 red.

**The run did not stop on this**, and the reason is stated so the owner can disagree with it: no
action ordered by §3 or §5 required a third sequence-bearing file to move, so stop condition 9.5
did not fire on the ordered work. It fires only on the *test's* wording. The corrections §3 orders
are complete; guarantee 1 as written needs its own order, and §9 states it as a decision.

---

## 6. The two exception records, and confirmation the other four are unmoved

The six sequence-bearing files were re-verified from `server/tools/participant_packages.py`
`SEQUENCE_BEARING_FILES` before anything was edited: `assets/js/decision.js`,
`assets/js/decision-ui.js`, `assets/js/workspace.js`, `assets/js/deepdive.js`,
`assets/questionnaires/intake.json`, `assets/questionnaires/debrief.json`.

**The exception records**, declared by name in `participant_packages.py` rather than left for a
checksum to discover:

```python
V17_TO_V18_CHANGED = (
    "assets/js/decision-ui.js",
    "assets/js/deepdive.js",
    "assets/js/detail.js",
)
V17_TO_V18_SEQUENCE_EXCEPTION = ("assets/js/decision-ui.js", "assets/js/deepdive.js")
```

**Exception 1 — `assets/js/deepdive.js`, ruling 1.** What moved inside it, exactly: the ten
collapsible group headers drop the identifier span; the Signal Stack banner, the Dempster-Shafer
metric-box label, the synthesis comparison heading, its note and its three confidence sentences
name what a module does; the comparison table drops the `Module NN:` row prefix and the
`Agrees with M09` column header; the Portfolio Health flyout drops the `D1.N` identifier; and
`CAT_FROM_MODULE` is extended from 19 keys to 77. **`CAT_NUM_FROM_MODULE` and `catBucket()` were
not touched** and are asserted byte-identical to v32.

**Exception 2 — `assets/js/decision-ui.js`, ruling 4. COMMENTS ONLY, and that is measured, not
asserted.** A comment block is added above the pair of literals at `:351`/`:352` and above the
literal at `:557` (the order names `:345`, `:346`, `:545`; those are the pre-insertion line numbers
and they moved down by the comment's own length). The suite strips **every whole-line comment**
from both versions and requires the results to be **identical**. They are. The three `period: 1`
literals are unchanged in number and in place. The comment reads:

> RUN 49, ruling 4. The server DERIVES the period and IGNORES this value. This surface only ever
> addresses a research project's evidence package, and `documents._resolve_period` takes the period
> from `research_decision.current_period` whenever a research assignment exists. Executed in Run 48:
> a request stating 1 returned 3, and a request stating 4 also returned 3. The literal is inert; it
> does not govern. Recorded here because a reader who assumes it governs is exactly how the detail
> page defect survived unnoticed.

**The third file, `assets/js/detail.js`, is NOT sequence-bearing** and is named in the change set
for the ampersand and the model instruction.

**Confirmation that the other four are unmoved, measured four independent ways:**

* `test_run49_naming_completion.py` §8: hashes all six against the **v17 record's own bytes** and
  reports `moved == ['assets/js/decision-ui.js', 'assets/js/deepdive.js']`, with the other four
  hashing identically to v17.
* `test_run28_participant_packages.py` §v18: `_seq18` equals exactly
  `V17_TO_V18_SEQUENCE_EXCEPTION`, and `len(_seq_still18) == 4` with every one matching v17.
  **170/170.**
* Gate **B04**: 6 sequence-bearing files compared against the `og-participant-2026.08-v18` record,
  `moved: none`.
* `test_run36_fault_guards.py` fault 35 holds all six against the **frozen v11** bytes and permits
  exactly the two named exceptions and no more. **40/40.**
* And the injection: appending one byte to `workspace.js` turns B01, B04 and B11 red.

**The v17 record is PINNED, not regenerated.** `participant_packages.py` now pins v17 to `5838a23`,
and `test_run28_participant_packages.py` asserts the v17 record's bytes in the tree are
byte-identical to what that commit wrote, and evaluates every v17-era check against that commit's
blobs rather than the live tree.

---

## 7. The freeze gate, every row

| id | blocker class | count | required | verdict | evidence |
|---|---|---|---|---|---|
| B01 | dirty candidate identity | 0 | = 0 | **PASS** | 11 content-addressed digests recomputed from the tree and compared |
| B02 | population mismatch | 0 | = 0 | **PASS** | registered 101, project scientific 95, Portfolio Health 5, scientific 100 |
| B03 | controlled-stimulus mismatch | 0 | = 0 | **PASS** | 6 projects x 6 periods, 36 unique, 0 duplicates, 0 missing |
| B04 | participant-sequence drift | 0 | = 0 | **PASS** | 6 sequence-bearing files compared against the v18 record; **moved: none** |
| B05 | false defensibility statement | 0 | = 0 | **PASS** | 100 served statements measured against executed behaviour; failing: none |
| B06 | unexpected execution exception | 0 | = 0 | **PASS** | census `{ABSTAINS: 89, COMPUTES: 5, SUPPLIED_NOT_COMPUTED: 1, PORTFOLIO_ROUTE: 5}` |
| B07 | Category-9 bypass | 0 | = 0 | **PASS** | no unqualified probe reaches a banded result; no C-group voter; group C does not contribute |
| B08 | Category-10 authority violation | 0 | = 0 | **PASS** | human authorization required, creates no project evidence, no Category-10 identity votes |
| B09 | voting count is not exactly 2 | 0 | = 0 | **PASS** | `CORE_VOTING_MODULES = ['A1.7', 'A1.8']` |
| B10 | current taxonomy dual authority | 0 | = 0 | **PASS** | one authority; both mirrors trace to the generator; no failing runtime lookup across all 101 |
| B11 | package or predecessor mutation | 0 | = 0 | **PASS** | no rewritten predecessor record; no v18 file failing its record; live stamp `sim-2026.08-v33` |
| B12 | browser qualification failure | 0 | = 0 | **PASS** | 29 rows, none failing |
| B13 | unresolved blocking Run-36 defect | 0 | = 0 | **PASS** | no open instrument-level defect |
| B14 | unsupported final empirical-validation claim | 0 | = 0 | **PASS** | all 100 rows record `NOT_EMPIRICALLY_FIELD_VALIDATED` |
| B15 | candidate behaviour changed during the run | 0 | = 0 | **PASS** | behaviour digest reproduced identically: `8fb4d366…` |

Gate suite verdicts beyond the fifteen rows: the generator runs to completion; the committed gate
reproduces from the live tree; the v25 record still says v25; the v26, v27, v28, v30, v31 and v32
successor records still say their own stamps; no release record exists while a blocker stands; the
limitation contract states 0 of 100 empirical validation, denies validated real-world predictive
effectiveness, states OG-SYNTH-0.1's historical incompleteness and states bounded controlled-study
qualification; the disposition is `FINAL_FREEZE_ACCEPTED`; and the record names Run 48's candidate
`e3d1b698b4797bb0fad4bde413317e56ecfd2398` as its parent and not itself. **34/34.**

---

## 8. Incidental findings, unacted

1. **The deep-dive grouping mismatch is not one instance or two — it is a systematic drift across
   FOUR groups, and it is now measurable in the DOM.** Run 48 found two instances. Reading the ten
   group headers and the panel labels back from the same rendered page shows the pattern:

   | bucket | header name (current taxonomy) | what the panels in it actually are | agree? |
   |---|---|---|---|
   | 1 | Cost and EVM Performance | cost/EVM performance | yes |
   | 2 | Schedule Performance | schedule performance and simulation | yes |
   | 3 | Cost Risk | cost risk and simulation | yes |
   | 4 | Document-Derived Condition Signals | document-derived signals | yes |
   | 5 | System Dynamics and Complexity | system dynamics | yes |
   | 6 | **Delivery Quality Performance** | **Signal Synthesis** (`09`, `6.1`–`6.4`) | **no** |
   | 7 | **Signal Synthesis** | **Evidence Combination** (`10`–`18`, `7.1`–`7.9–7.20`) | **no** |
   | 8 | **Evidence Combination** | **Governance and Compliance** (`19`, `8.1`, `8.2–8.9`) | **no** |
   | 9 | **Regulatory and Authority Thresholds** | **Evidence Quality** (`9.1`, `9.2–9.7`) | **no** |
   | 10 | Decision Optimization | decision optimization | yes |

   The shape of the drift: the current gapless taxonomy inserted *Delivery Quality Performance* at
   position 6, pushing the retired scheme's 6, 7 and 8 down one, and the retired scheme's category 9
   (data and evidence quality) has no slot in the current headers at all. **NOT CORRECTED** — it
   moves panels between groups, which changes what a participant sees, and it needs its own order.
   It is the whole reason the panel labels in §2 are taken from each module's own title.
2. **`research/deepdive.html` renders only for a project carrying the LEGACY client-side signals
   blob** (`signals.evm`, `signals.cusum`, `signals.mc`, `signals.doc`). Confirmed again this run:
   the driver had to supply it through the real `save` route using the `signals` block from
   `p0-baseline/contracts/get/get.json`. A project computed entirely through `projectupload` and
   `projectcompute` shows "Awaiting analysis: no signal inputs yet." The captured baseline's own
   `signalInputs` are still refused by the live write path (`environmentalComplianceRate` 78.8
   against a bound of 1); only the `signals` block was used, and the capture was read, never
   modified.
3. **That blob populates only 63 of the 77 panels**, and the 14 it does not reach are exactly the
   two-digit simulation-stack keys `04`–`08` and `10`–`18`. Their labels are therefore
   source-verified only. This is a fixture limitation, not a code finding, and it is why §1.1 and
   §3 say so rather than claiming a DOM read.
4. **`deepdive.js:2464` is a PROJECT identifier, not a module identifier** (§1.4). Reported because
   the parent session asked, and because the `mod-mono` class on it will make a future sweep flag
   it again.
5. **`CAT8_MODULES[].num` (`D1.1`–`D1.5`) is now an unread field.** This run removed its only
   reader. It is left in place rather than deleted, because deleting data is a larger change than
   this run is ordered to make and the field may have a future reader.
6. **`assets/js/detail.js:1226` still contains the string `Documents & Extracted Signals` — inside a
   COMMENT.** Comments are not user-facing text under §2, so it is left. The suite's check is
   written against the `cs("d-docsignals", ...)` call site specifically, so it does not falsely go
   red on the comment.
7. **Run 47's handoff entry is still at the BOTTOM of `T6_HANDOFF.md`**, against that file's own
   rule. Run 48 reported it and left it; Run 49 does the same. Moving it rewrites history.

---

## 9. What the next session needs, stated as decisions for the owner

1. **Guarantee 1, and the four frozen files that block it.** The remaining module identifiers on
   the Categories page come from the GENERATED taxonomy, and the remaining en and em dashes sit in
   four sequence-bearing files this run may not move. **Decide:** (a) order a taxonomy-authority
   change plus a regeneration for `app.js`'s two identifiers; (b) authorise a fifth and sixth
   sequence-bearing exception for the dash sweep, knowing it moves `decision.js`, `workspace.js`
   and both questionnaires; (c) narrow the guarantee to the surfaces already corrected and record
   the rest as an accepted limitation. Until one of these is chosen, guarantee 1 will be reported
   NOT MET by every subsequent run, exactly as it has been by the last two.
2. **The deep-dive grouping mismatch, now known to span four groups** (§8 item 1). Correcting it
   moves panels between collapsible groups, which is a change to what a participant sees.
   **Decide:** re-bucket the panels so each group's contents match its header, or re-name the
   headers so they describe what they actually contain, or leave it and record it as a known
   presentation defect in the limitation contract.
3. **The 14 panels whose labels cannot be verified from a rendered DOM** (§8 item 3). They are
   source-verified and their map entries are Run 48's, unchanged. **Decide:** is source
   verification acceptable for those, or should a fixture be built that populates the full
   ten-method signal array so every panel on that surface can be read back?
4. **`CAT8_MODULES[].num`, now unread** (§8 item 5). **Decide:** delete the field, or keep it.

---

## Carried forward, unacted, so they are not rediscovered

1. **The deep-dive grouping mismatch**, Run 48 incidental finding 1. Panels bucket by the retired
   scheme's numbers while headers name the current taxonomy. Run 49 measured it across **four**
   groups, not two (§8 item 1). Correcting it moves panels between groups and needs its own order.
2. **`research/deepdive.html` renders only for a project carrying the legacy client-side signals
   blob.** The document pipeline does not write it, so a project computed entirely through
   `projectupload` and `projectcompute` shows "Awaiting analysis: no signal inputs yet." on that
   surface.
3. **The `historical_data` triple**, Run 47's only unimplemented relation.
   `analogous_overrun_pct` together with `similar_project_bac` and `similar_project_final_cost`
   determine each other against the REFERENCE project's budget at completion, not this project's.
   It awaits a ruling on whether "a known BAC" means this project's or any the same document states.
4. **`signal_inputs.sources` records no source field name**, so a finding cannot say which cell of a
   document a figure came from.
5. **Four status comparisons remain case-sensitive**, two of them in `decision.js`.
6. **Two Run 45 census artifacts do not match the v30 release manifest**, checksummed before their
   final bytes landed.
7. **`test_run47_evm_consistency.py` still has the traceback-swallowing shape**: its body is wrapped
   in `try/finally` with `sys.exit` in the `finally`, so a raise prints a clean RESULT line one
   check short. **Left alone as ordered.** Both files this run wrote —
   `test_run49_naming_completion.py` and `drive_run49_browser.py` — carry an `except BaseException`
   arm that counts a raise as a failure and prints the traceback.

---

## Audit artifacts the suites rewrote, and were restored

**Eighteen**, exactly as Runs 45, 47 and 48 recorded: seventeen under `code_audit/` plus
`server/tools/run17/coverage.csv`, which is outside it.

```
code_audit/run10_no_operational_effect.csv
code_audit/run20_cycle12_100_reaudit.csv
code_audit/run20_cycle12_guard_nonvacuity.csv
code_audit/run20_cycle12_lineage_campaign.csv
code_audit/run21_guard_nonvacuity_results.csv
code_audit/run30_cat7_operational_execution.csv
code_audit/run38_controlled_stimulus_execution_order.csv
code_audit/run38_lock_integrity.csv
code_audit/run38_participant_state_machine.csv
code_audit/run39_launch_identity.csv
code_audit/run8_expectation_mutation_proof.csv
code_audit/run9_abstention_results.csv
code_audit/run9_alias_overlay_verification.csv
code_audit/run9_fixture_import_results.csv
code_audit/run9_known_answer_results.csv
code_audit/run9_no_operational_effect.csv
code_audit/run9_validator_gap_recomputations.csv
server/tools/run17/coverage.csv
```

All eighteen restored with `git checkout --` after each full run and after each single-suite run
that touched them. **None was committed.** `git add -A` and `git add .` were never used; every
`git add` named its paths explicitly. No fault-injection suite was ever run in the background while
staging.

**Two audit files this run WROTE deliberately, and committed:**
`code_audit/run49_production_tree.sha256` (244 files; the guard was observed reporting exactly the
four expected CHANGED files and nothing added, removed or renamed before it was written) and
`code_audit/run49_participant_package_v18_checksums.sha256` (70 files).

`test_run22_production_tree_completeness.py` behaved exactly as the order predicted: red inside the
runner on the first pass, green standing alone, and green in the runner once the pinned manifest was
reconciled. Final result **44/44**.

---

## The commit chain

| commit | what |
|---|---|
| `5838a23` | `main` at the start of the run |
| `751d481` | Run 49: finish the naming correction, and reconcile the pinned guards |
| `1d68134` | Run 49: the naming-completion suite, the browser driver and the successor builders |
| `5b7b284` | Run 49: re-anchor the freeze gate's parent to Run 48's candidate |
| `a75c3c1` | Run 49: the successor freeze artefacts for `sim-2026.08-v33` |
| `82bd1f8` | Run 49: reconcile the remaining pinned guards to the v33 successor |
| `6a39427` | Run 49: re-mint the candidate identity onto the reconciled guards |

Candidate identity digest `15fa2845569178a821eb3970fa1d1e0400f5edb55c70774d7361cb850b7eb11d` at
candidate `82bd1f855313c09210b1de9829fa6773355534c9`, superseding Run 48's candidate
`e3d1b698b4797bb0fad4bde413317e56ecfd2398` and `sim-2026.08-v32`. Behaviour digest
`8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1`, **identical to Run 48's**,
which is the point: the text a participant reads moved, the instrument's behaviour did not. Release
content digest `e76bfefb65c8db0ddd0efce47e00530aef1d6ebd28467251b1eb57561dca8e30`.

**The re-mint cost was paid twice, and it is recorded rather than hidden.** §7.1 orders the pinned
guards reconciled before the candidate identity is taken. They were — the first mint came after
`751d481`. But two later reconciliations were only discoverable by *running* the full suite against
the new manifests (`test_run37_freeze_gate.py`'s parent anchor, then six guards that hold `detail.js`
and `decision-ui.js` against a freeze manifest), and every one of those files is a `test_*.py` inside
`test_suite_identity`, so each fix moved the digest and turned B01 red. Three mints in total. Runs 47
and 48 paid the same cost for doing it in the other order; this run paid a smaller version of it for
a reason the order does not cover: a guard you cannot know needs reconciling until you run it.

**No stop condition fired on any ordered action.** 9.1 (no control added, moved or removed): the DOM
shows 15 controls under `#detail-root` and zero `select` elements, and the package suite counts
control tags in both moved files against v32. 9.2 (no stored figure changed) and 9.3 (no band,
status, colour or posture changed): the behaviour digest reproduces identically. 9.4 (no module
buckets differently): the grouping map is byte-identical and 63 panels were read back. 9.5 (no third
sequence-bearing file): two moved, and the third-file proof was executed and restored. 9.6 (no check
deleted): none was deleted; three check bodies were reconciled to the successor and are named in §6
and in the commit chain, and one — `test_run2_fifteen_defects.py` — GAINED a named line set rather
than being widened. 9.7 (no gate row failed for a reason other than a manifest this run's edits
falsified): every failure seen during the run was a pinned manifest or a hard-coded predecessor
identifier, each reconciled to true bytes; not one gate row was disabled, weakened or widened. 9.8
(no invented category assignment): every one of the 77 keys was determined by its module's own
title, and the exception list is empty.
