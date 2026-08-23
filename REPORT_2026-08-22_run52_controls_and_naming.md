# Run 52 — two redundant controls, and one name across the wire

**Repository:** the Linux clone at `/home/user/LinPRojectRadar`.
**Interpreter:** `python3` 3.11.15, the documented fallback. This clone has no `.venv`.
**Branch:** `run52-controls-and-naming`, rooted at `fe35504`, merged to `main` with `--no-ff`.
**Stamp:** `sim-2026.08-v35`. **Package:** `og-participant-2026.08-v20`.
**193 suites, 14,690/14,690, ALL GREEN.** Freeze gate 15 blocker classes, 0 blocked; suite
34/34; launch gate 100/100. Injection campaign 30/30.
**Behaviour digest UNCHANGED at `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1`.**

## Starting state, verified

`HEAD == main == origin/main == fe355043a8e71a2c9f16b50b8e01ac2696b757ec`, tree clean.
`SIMULATION_VERSION = "sim-2026.08-v34"` at `server/app/simulation/models.py:644` — **not**
`server/app/models.py`. Package `og-participant-2026.08-v19`. `service_index()` 63,
`registry_index()` 101, `CORE_VOTING_MODULES == ['A1.7', 'A1.8']`. All confirmed.

---

# THE HEADLINE: RULING 1'S PREMISE IS FALSE, ESTABLISHED BY EXECUTION

Ruling 1 says Manage and Open "both lead to the same project detail page". **They do not.**
Driven in real Chromium against the real application, with a real project row:

    project-list rows rendered: 1   ids=['PRJ-R50-BROWSER']
    .li-open controls: 1    .li-manage controls: 1
    visible .page sections before any click: ['portfolio']

    AFTER CLICKING MANAGE:
      visible .page sections : ['portfolio']
      detail page visible?   : False
      inline .pr-admin under the row? : True
      inline panel text      : Project number / code  Project name  Project type / sector
                               (drives which modules apply)  Design Construction Hybrid
                               Address (optional...)  Save info  Upload documents
                               Recompute this project  Reset signals  Archive  Close

    AFTER CLICKING OPEN:
      visible .page sections : ['detail']
      detail page visible?   : True
      detail-root head text  : Back to Portfolio  PROJECT DETAIL  PRJ-R50-BROWSER
                               Run 51 browser fixture  CONSTRUCTION  Reporting period: ·
                               State: Amber  Amber, driven by Cost and EVM Performance...

    >>> MANAGE REACHES THE PROJECT DETAIL PAGE: False
    >>> OPEN   REACHES THE PROJECT DETAIL PAGE: True

Evidence in code: `assets/js/app.js:1102-1104` binds Manage to
`LinIngest.openInlineManage(p.id)`, and `assets/js/ingest.js:207-266` inserts a `.pr-admin`
box into the row's own `<li>` — there is no `showPage` call anywhere in it. `app.js:1100` binds
Open to `openDetail(p.id)`, and `app.js:1615-1619` is `selectedId = id; showPage("detail"); …`.

**Open is the ONLY route from the project list to the project detail page.** Removing it would
have removed that route — precisely the harm §8.1 exists to prevent, and §6.1 item 3's check
("Manage still reaches the project detail page for the project whose row it sits in") FAILS.

**The surface is STOPPED under §8.1. Open was not removed. `assets/js/app.js` did not move,
byte for byte.** Manage was not "fixed" to navigate: that would change a control's behaviour,
which no ruling authorises. The driver that established this is committed as
`server/tools/drive_run52_premise.py`, and the finding is enforced, not merely asserted — fault
4 of the injection campaign removes Open and the package guard goes red.

The `title` attributes were not trusted: Manage's title reads "Edit info, upload, archive, reset
(inline)" and Open's "Open project detail". Both were verified by clicking.

---

## §11 item 1 — Every project list surface, its controls before and after

**There is exactly ONE project-list surface in the served application.** `grep -rn` for
`data-open=`, `li-open`, `data-manage=`, `li-manage` across `assets/`, `research/` and every
`.html` returns render sites at `assets/js/app.js:1083` (Manage) and `:1084` (Open) and nowhere
else; the CSS at `assets/css/radar.css:643-658, 3417, 3903-3940` styles them; `tests_render.html`
:461-463 exercises them. The single host `<ul id="project-list">` is at `index.html:566`, inside
`<section class="page" data-page="portfolio">`. `buildFallbackList()` (`app.js:1031`) is the one
builder; it is called from `app.js:2530, 2827, 2847` and `workspace.js:347`, all into that host.
Measured in the browser: `project-list host elements in the served DOM : 1`.

| surface | Manage before | Open before | Manage after | Open after | verdict |
|---|---|---|---|---|---|
| `index.html` `[data-page=portfolio]` `#project-list` (the only one) | 1 per row | 1 per row | 1 per row | **1 per row — unchanged** | **STOPPED under §8.1** |

Browser verification that Manage still reaches the right project: **it does not reach the detail
page at all**, which is the finding. What was verified instead, per row: Manage opens the inline
admin accordion under its own row (`PASS`), Open reaches the detail page (`PASS`), and it is the
detail page of **this row's** project — the row id `PRJ-R50-BROWSER` appears in `detail-root`'s
head text (`PASS`).

**Out of scope, reported so a later run does not think it was missed:** `assets/js/workspace.js:763`
renders an "Open" button for a **DOCUMENT**, not a project. Ruling 1 does not name it. It was not
touched and it is not part of the project list.

## §11 item 2 — The health button removal, what became unreachable, and the grep proof

Removed at `assets/js/deepdive.js` (Run 51's 184-line deletion moved it from :2322 to **:2311**,
handler lookup :2312, dead call :2314 — verified before editing):

    -    healthLine.innerHTML = `${escg(anomaly)} <button type="button" class="dd-link"
    -                            data-goto-health>see Health &rarr;</button>`;
    -    const healthLink = healthLine.querySelector("[data-goto-health]");
    -    if (healthLink) healthLink.addEventListener("click", () => {
    -      if (window.LinIngest && LinIngest.openHealthModal) LinIngest.openHealthModal();
    -    });
    +    healthLine.innerHTML = `${escg(anomaly)}`;

with a comment at the site recording what was there and why it went.

**The grep proof, verbatim:**

    $ grep -rn "goto-health\|openHealthModal\|see Health" assets/ research/ server/ *.html
    assets/js/app.js:1381:    // project's own stored result. Checked, not assumed -- `LinIngest.openHealthModal`, which
    assets/js/deepdive.js:2311:    healthLine.innerHTML = `${escg(anomaly)} <button type="button" class="dd-link" data-goto-health>see Health &rarr;</button>`;
    assets/js/deepdive.js:2312:    const healthLink = healthLine.querySelector("[data-goto-health]");
    assets/js/deepdive.js:2314:      if (window.LinIngest && LinIngest.openHealthModal) LinIngest.openHealthModal();

Three of the four hits were the button itself. The fourth is the `app.js:1381` **comment**
recording that the same check was made in an earlier run and the symbol was absent. **That comment
was NOT deleted.** It is the record of why things moved, and it is not stale — it is now
corroborated by this run.

**What became unreachable: nothing.** Checked by grep before removing:

    $ grep -rn "cat8SummaryLine\|dd-link" assets/js/ assets/css/
    assets/js/detail.js:937:  ...class="dd-link det-prov-toggle" aria-expanded="false">why?</button>
    assets/js/deepdive.js:2310:    const anomaly = cat8SummaryLine(project);
    assets/js/deepdive.js:2331:  function cat8SummaryLine(project) {
    assets/css/radar.css:2262:.dd-link { ... }

`cat8SummaryLine` still has its caller at :2310 — the anomaly sentence stays. `.dd-link` still has
`detail.js:937`. Nothing was removed beyond the button and its handler, and nothing needed to be.

**Browser verification:** deep-dive panels rendered **64**; `[data-goto-health]` nodes **0**;
occurrences of the string "see Health" **0**; `.dd-health-line` text still reads
`Portfolio Health: no anomaly flagged.`; no uncaught page error.

## §11 item 3 — What `drive_run44_browser.py` became

**FIXED, not deleted, and here is which and why.** The block at :141-160 called
`window.LinDeepDive.renderCat8Health(root, () => {})`, deleted by Run 51, and would have raised
`TypeError: … is not a function` on every run since. It is the **Run-44 audit record** and
deleting it would destroy that record, so it was repaired instead. The three checks it made about
the flyout's wording cannot be made against a surface that no longer exists, so they were
**replaced — not deleted** — by the check that actually holds now: `renderCat8Health` is gone from
`window.LinDeepDive`'s export, so the surface is unreachable. The file now parses and runs.

## §11 item 4 — The full identifier rename

`module_id` is the name. **The server was already right**: `assets/js/taxonomy.js:493, 508, 528`
have always matched `row.module_results[i].module_id` and `a.module_id`, and
`server/app/simulation/registry.py:650, 688` emit `module_id`. So the client and the authority
moved to the server's name, not the reverse.

### Producers

| file:line | what it called it | what it calls it now |
|---|---|---|
| `server/tools/taxonomy_authority.json` | `"key"` on 101 module rows | **`"module_id"`**, 101 rows |
| `server/tools/taxonomy_authority.json` | `"key"` on 12 **category** rows | **`"key"` — deliberately unchanged** |
| `server/tools/build_client_taxonomy.py:120,122,125,127,128` | `_m["key"]`, `m["key"]`, emits `key:` | **`_m["module_id"]`, `m["module_id"]`, emits `module_id:`** |
| `assets/js/taxonomy.js` (generated, 63 module rows) | `key: 'A1.1'` | **`module_id: 'A1.1'`** |
| `assets/js/categories.js` (generated, 63 module rows) | `key: 'A1.1'` | **`module_id: 'A1.1'`** |
| `server/app/simulation/registry.py:650,688` | `module_id` | **`module_id` — already correct, untouched** |

### Consumers

| file:line | what it called it | what it calls it now |
|---|---|---|
| `assets/js/taxonomy.js:371,377` | `METHOD_TO_NUM`, `m.key` | **`METHOD_TO_MODULE_ID`, `m.module_id`** — this is THE dispatch path |
| `assets/js/taxonomy.js:406,491,509,528` | `numForMethodClass`, `var num` | **`moduleIdForMethodClass`, `var moduleId`** |
| `assets/js/categories.js:494` (hand tail) | `key: m.key` on the red-flag record | **`module_id: m.module_id`** (no reader anywhere) |
| `assets/js/detail.js:473` | `key: m.key` | **`module_id: m.module_id`** |
| `assets/js/detail.js:2573` | `key: m.key` | **`module_id: m.module_id`** |
| `assets/js/signals.js:423` | `key: m.key` | **`module_id: m.module_id`** |
| `assets/js/neural_flow.js:150,160` | `key: m.key`, synthesized `key:` | **`module_id: m.module_id`, `module_id:`** |
| `assets/js/projectnet2d.js:178` | `key: m && m.key` | **`module_id: m && m.module_id`** |
| `assets/js/projectnet2d.js:65` | `String(a.key)` — a **CATEGORY** key | **unchanged, correctly named** |
| `assets/js/deepdive.js:132,137,144,146,149,150` | parameter `num`, attribute `data-num` | **parameter `moduleId`, attribute `data-module-id`** |
| `assets/js/decision.js:407,426`, `detail.js:381`, `signals.js:430`, `knowledge.js:2699`, `deepdive.js:133,140` | `cat.key` / `c.key` — **CATEGORY** identifiers | **unchanged, correctly named** |

### Server-side guards and tools reconciled to the new bytes

`build_client_taxonomy.py`, `build_run32_b3_reconciliation.py`, `run26_fault_campaign.py`,
`run32_b3_browser_verification.py`, `run32_qualifier_fault_campaign.py`,
`run51_injection_campaign.py`, `test_run10_synthetic_v03.py`,
`test_run16_material_cost_variance_disabled.py`, `test_run24_empty_project_diagram.py`,
`test_run26_counts_and_wiring.py`, `test_run32_client_authority.py`,
`test_run32_defensibility_truth.py`, `test_run32_method_class_agreement.py`,
`test_run35_closure_voter_identities.py`, `test_run44_participant_defect_fixes.py`,
`test_run49_naming_completion.py`, `test_run2_fifteen_defects.py`,
`test_run28_participant_packages.py`, `test_run36_fault_guards.py`. **No check was weakened,
widened or deleted** — each still asserts exactly what it asserted; only the name it looks for
moved, and each carries a comment saying so.

### Mirrors regenerated and confirmed

    $ python build_client_taxonomy.py
    wrote assets/js/categories.js
    wrote assets/js/taxonomy.js
    $ python build_client_taxonomy.py --check
    both client artifacts are exactly what the authorities generate

Independently, so that the generated file does not validate itself against its own generator:
each mirror carries **63** `module_id: '…'` rows, hand-computed as `len(service_index()) == 63`
from the registry, and **12** `key: '…'` rows, hand-computed as the 12 category rows of the
authority. Measured in the live browser: 12 categories shipped, 63 modules shipped, 63 carrying
`module_id`, **0** still carrying `key`, **0** still carrying `num`, 12 categories still carrying
`key`.

### Consumers STOPPED under §8.2, with reasons

**1. `p0-baseline/module_renumbering_map.csv`'s `new_id` / `old_id` columns, and their 309
occurrences across more than thirty files.** STOPPED. Three reasons, each sufficient. (a) They are
a **pair** — the current identity and the pre-renumbering identity — not one name for one thing;
`old_id` is a *retired* identity, a different referent, and renaming half a pair makes the pairing
illegible. (b) The name originates in the **header row of a frozen p0-baseline artifact** that the
freeze gate pins as `service_roster_digest`; changing it edits a baseline record. (c) Among the 309
occurrences are fault campaigns and freeze-gate campaigns whose mutation strings must match TRUE
bytes. **Where the identifier actually crosses the wire — the stored row, the API response, the
export — it is already `module_id`, which is what ruling 3 asks for.**

**2. `assets/js/deepdive.js:1789-1798, 1808, 1822`, the methods-comparison array's local `num`.**
STOPPED — §6.3 note 2 permits renaming "if that is safe", and it is not. This `num` holds `"09"`
through `"18"`: the ordinal of a **method** in the synthesis comparison table (09 = the
conservative-dominance baseline, 10 = Dempster-Shafer, 11 = Rough Sets …), joined to the local
`s09`…`s18` values and compared as `e.num === "09"`. Registry module identifiers are `"A1.7"`,
`"B4.2"`. Calling this field `module_id` would assert an identity it does not have — a third wrong
name rather than one right one. A comment at the site records the stop.

**No half-rename occurred.** Every consumer that could move, moved; the two that could not are
named above and carry their reasons in the code.

## §11 item 5 — The live dispatch proof across all 101

Asserted by **execution**, not by reading. Server side, the exact contract gate row B10 uses:

    registry modules              : 101
    all four lookups resolved     : 101
    raised                        : none
    of which method_label non-None: 5
    LIVE DISPATCH PROOF: PASS -- 101/101

`REG.method_label(m)`, `REG.group_of(m)`, `REG.parameter_provenance(m)` and
`REG.activation_state(m)` were called for every member of `registry_index()`; none raised. Gate row
**B10 PASS, count 0**: *"one authority present=True; both mirrors trace to the generator=True;
runtime lookups failing across all 101 registered modules: none"*.

Client side, in the live browser after the rename, the served resolver was exercised module by
module through `getModuleStatus`, `getModuleResult` and `getModuleAbstentionReason`:

    live client dispatch exercised over 63 dispatching modules; raised: none

63 is the population the client ships; the other 38 are retired and by design never reach it.
**§9.4 does not fire.**

## §11 item 6 — Confirmation that no rendered identifier changed

**No naming sweep was run.** Ruling 4 is a reversal and was obeyed as one: nothing was stripped
from rendered text and nothing was restored.

Proved by capturing the RENDERED TEXT of every affected surface from a git worktree at `fe35504`
and from the live tree, with the same fixture and the same driver
(`server/tools/run52_rendered_text_capture.py`), and diffing:

| surface | before | after | difference |
|---|---|---|---|
| portfolio (`[data-page=portfolio]` innerText) | 648 chars | 648 chars | **IDENTICAL** |
| deep-dive SVG text, aria-labels, titles | 40147 chars | 40147 chars | **IDENTICAL** |
| project detail innerText | 11237 | 11237 | only the five fixture upload timestamps (`09:58 EDT` → `10:00 EDT`) — the two captures built their fixtures two minutes apart |
| project detail SVG/aria/title | 40721 | 40721 | the same five timestamps and five activity-log timestamps |
| deep-dive innerText | 1321 | 1308 | **exactly one line:** |

    -Portfolio Health: no anomaly flagged. see Health →
    +Portfolio Health: no anomaly flagged.

That is the one removed control and nothing else. **No rendered identifier changed. §9.8 does not
fire.**

## §11 item 7 — Every item stopped under §8, with its reason

| # | condition | item stopped | reason |
|---|---|---|---|
| 1 | **§8.1** | the project-list surface (ruling 1) | The ruling's premise is false. Manage does not reach the project detail page; Open is the only route to it. Removing Open would have removed the only route to a project's detail. Established by execution in a browser, not by reading. `assets/js/app.js` did not move. |
| 2 | **§8.2** | `new_id` / `old_id` in `p0-baseline/module_renumbering_map.csv` and its 309 downstream occurrences | A renumbering PAIR, not one name for one thing; originates in a frozen baseline artifact the freeze gate pins; where the identifier crosses the wire it is already `module_id`. |
| 3 | **§8.2** | the methods-comparison `num` at `deepdive.js:1789-1822` | It is a METHOD ordinal (09…18), not a registry module identifier. Renaming it would assert a false identity. |
| 4 | — | **§8.3 did not fire.** | Nothing became unreachable through ruling 2. `cat8SummaryLine` keeps its caller; `.dd-link` keeps `detail.js:937`. Proved by grep before removing. |

## §11 item 8 — Every §7 guarantee, verified or not met, each with its injection

**Injection protocol, tightened as ordered:** snapshot → inject → **re-read the bytes from disk**
→ observe RED **for the intended reason** → restore inside a `finally` that cannot be skipped →
assert `restored == snapshot` → **re-run the baseline after EVERY injection**.
`server/tools/run52_injection_campaign.py`, **RESULT: 30/30 checks passed**, and the working tree
was byte-clean afterwards.

| # | §7 guarantee | verdict | how |
|---|---|---|---|
| 1 | No project list renders an Open control | **NOT MET, DELIBERATELY. STOPPED under §8.1.** | Open is present on every row by design; asserting its absence would assert the harm. What was asserted instead: `app.js` is byte-identical to v19, and BOTH row controls still render. **Fault 4** removes Open and the package guard goes red — the stop is enforced, not narrated. |
| 2 | Every project list renders Manage, and Manage reaches the detail page of its own row's project | **PARTLY MET, and the failing half is the headline.** Manage renders on every row (`PASS`). **Manage does not reach the detail page** — measured, `visible pages ['portfolio']`, `.pr-admin` under the row `True`. Open does, and it is this row's project. | browser |
| 3 | The Open control existed before this run, against the prior commit's bytes | **MET** | `git show fe35504:assets/js/app.js` contains `class="btn small li-open"` and `class="btn small li-manage"`. Non-vacuity holds. |
| 4 | The "see Health" button renders nowhere | **MET** | browser: `[data-goto-health]` 0, "see Health" 0. **Fault 1** puts the button back; `test_run28_participant_packages.py` goes red for the intended reason; restored; baseline green. |
| 5 | That button existed before this run, against the prior commit's bytes | **MET** | `git show fe35504:assets/js/deepdive.js` contains `data-goto-health` and `see Health`. |
| 6 | The deep-dive surface still renders after the removal | **MET** | 64 panels rendered, no page error, anomaly sentence intact. |
| 7 | One name on both sides; every other name searched for and found none, except those stopped | **MET, with the two §8.2 stops named** | browser: 63/63 `module_id`, 0 `key`, 0 `num`. **Fault 2** reverts one authority row to `key`; `test_run32_client_authority.py` goes red. **Fault 5** reverts the dispatch join to `m.key`; `test_run32_method_class_agreement.py` goes red. |
| 8 | Both generated mirrors match their generator | **MET** | `--check` passes, and independently: 63 module rows hand-computed from `service_index()`, 12 category rows from the authority. **Fault 3** hand-edits a mirror; the guard goes red. |
| 9 | Every runtime lookup across all 101 resolves, asserted live | **MET** | 101/101 server-side by execution; 63/63 client-side by execution in the browser. Gate B10 PASS, count 0. |
| 10 | **No rendered identifier changed** | **MET** | before/after rendered-text capture; the only difference is the one removed control. See item 6. |
| 11 | Behaviour digest unchanged | **MET** | `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1`, reproduced. |
| 12 | No stored figure changes | **MET** | gate B15 PASS, count 0; the detail page's rendered figures are byte-identical before and after. |
| 13 | No band, status, colour or posture changes | **MET** | detail-page rendered text identical apart from fixture timestamps; `State: Amber` unchanged. |
| 14 | Modules in service 63, registry 101, both derived | **MET** | `len(service_index()) == 63`, `len(registry_index()) == 101`, read live. Gate B02 PASS. |
| 15 | Voting is exactly 2, `A1.7` and `A1.8` | **MET** | `sorted(REG.CORE_VOTING_MODULES) == ['A1.7','A1.8']`. Gate B09 PASS, count 0. |
| 16 | The detail page still opens on the latest computed period; Run 48's four fixtures re-run | **MET** | `test_run48_current_period.py` green in the full suite; the rendered detail page is byte-identical to the predecessor apart from fixture timestamps. |
| 17 | Every sequence-bearing file that moved has its own named exception record; one moving without a record still turns the gate red | **MET** | `V19_TO_V20_SEQUENCE_EXCEPTION = ("assets/js/deepdive.js",)`, declared in `participant_packages.py` and named in the v20 record's header. **Fault 6** deletes the exception record while the file still moved; `test_run28_participant_packages.py` goes red for the intended reason. |
| 18 | The successor freeze gate passes in full | **MET** | 15 blocker classes, **0 blocked**; `test_run37_freeze_gate.py` **34/34**; `test_run39_launch_gate.py` **100/100**. |

## §11 item 9 — Every sequence-bearing file that moved, and its exception record

The six, verified from `participant_packages.SEQUENCE_BEARING_FILES`: `assets/js/decision.js`,
`assets/js/decision-ui.js`, `assets/js/workspace.js`, `assets/js/deepdive.js`,
`assets/questionnaires/intake.json`, `assets/questionnaires/debrief.json`.

| file | moved in Run 52? | record |
|---|---|---|
| `assets/js/deepdive.js` | **YES** | `V19_TO_V20_SEQUENCE_EXCEPTION`, plus a named `# assets/js/deepdive.js -- SEQUENCE-BEARING` block in `code_audit/run52_participant_package_v20_checksums.sha256` saying exactly what moved inside it |
| `assets/js/decision.js` | no | byte-identical to v19, asserted file by file |
| `assets/js/decision-ui.js` | no | byte-identical to v19 |
| `assets/js/workspace.js` | no | byte-identical to v19 |
| `assets/questionnaires/intake.json` | no | byte-identical to v19 |
| `assets/questionnaires/debrief.json` | no | byte-identical to v19 |

**ONE of six moved**, not all six. A second moving is still red, proved by fault 6.

## §11 item 10 — Audit artifacts the suites rewrote and restored

**26 rewritten on the final full run, all restored, none committed** (23 on earlier passes; the
last pass, in which every suite went green, rewrote three more): 22 under `code_audit/` —
`run8_expectation_mutation_proof.csv`, `run9_abstention_results.csv`,
`run9_alias_overlay_verification.csv`, `run9_fixture_import_results.csv`,
`run9_known_answer_results.csv`, `run9_no_operational_effect.csv`,
`run9_validator_gap_recomputations.csv`, `run10_no_operational_effect.csv`,
`run20_cycle12_100_reaudit.csv`, `run20_cycle12_guard_nonvacuity.csv`,
`run20_cycle12_lineage_campaign.csv`, `run21_guard_nonvacuity_results.csv`,
`run30_cat7_operational_execution.csv`, `run33_portfolio_fault_injection_results.csv`,
`run33_simulation_version_execution_proof.csv`, `run34_count_fault_injection_results.csv`,
`run34_fault_injection_results.csv`, `run34_portfolio_parameter_provenance.csv`,
`run34_provenance_fault_injection_results.csv`, `run34_simulation_version_execution_proof.csv`,
`run38_controlled_stimulus_execution_order.csv`, `run38_lock_integrity.csv`,
`run38_participant_state_machine.csv`, `run39_launch_identity.csv` — plus
`server/tools/run17/coverage.csv`. Runs 48-51 each recorded 18; this run saw 23, and the three
`code_audit/run37_*.csv` files were kept out of the tree entirely by running
`build_run37_acceptance.py --out-audit` into a scratch directory.

## §11 item 11 — Incidental findings, unacted

1. **A FAULT INJECTION LEAKED INTO THE WORKING TREE during this run's first full-suite pass.**
   `server/app/simulation/canonical_v8.py` was left carrying three neutered guards — `if False:`
   in place of `if orientation not in ORIENTATIONS:` at :283, `if str(raw["period"]) != self.period:`
   at :388 and `if str(raw["feature_schema_version"]) != self.schema_version:` at :393, and a
   silently-defaulting `orientation`. It came from one of `test_run33_portfolio_fault_injection.py`
   or a `test_run34_*` campaign aborting after writing and before restoring, and it produced
   **eleven** downstream suite failures that were purely collateral: every one of them went green
   standing alone once the file was restored from `HEAD`. This is the fifth consecutive run
   (48, 49, 50, 51, 52) to record a mid-injection abort. It was caught only because the tree was
   checked with `git status` rather than trusted. **The leaking campaign was not identified and
   the leak was not repaired — restoring the file is not the same as fixing the campaign.**
2. **`NAMING_AUTHORITY.md` CONFLICTS WITH RULING 4.** Lines 96-97: *"**Never use a module id or
   number in user-facing text.** No "Cat 4", no "1.7", no "PH.2", no "A4.2". Groups and purposes
   only. The old "Cat N" scheme is retired along with the names."* Ruling 4 rules those acceptable.
   As ordered, **the file was left alone** and the conflict is reported; its revision is not
   ordered here.
3. **`REG.method_label(m)` returns `None` for 96 of the 101 registered modules.** Only five carry a
   method label. B10 requires no exception, which is met, so this is not a defect against any
   current contract — but a reader assuming a label exists for every module would be wrong.
4. **`assets/js/deepdive.js`'s `data-num` attribute had no reader anywhere** — not in `assets/`,
   not in `research/`, not in `assets/css/`, not in `index.html`. The comment at :2255 mentions it,
   but the bucketing actually reads `data-cat`. It was renamed to `data-module-id` with no
   behavioural consequence, and the fact is recorded here so a later run does not go looking for a
   consumer that never existed.
5. **`assets/js/categories.js` is never loaded by `index.html`** and its hand-written tail
   (`redFlags`) is therefore dead on the live participant surface; `decision.js:445` already
   carries a comment saying `getProjectFusion` has not returned `redFlags` since `taxonomy.js`
   replaced `categories.js`. The rename was carried there anyway for the single-name guarantee.
6. `drive_run51_browser.py` reads `data-num` off deep-dive panels at its line ~560 and will now
   read `None` for each. It only prints them; no check depends on the value. Not repaired, because
   it is a superseded driver and repairing it was not ordered.

## §11 item 12 — What the next session needs, stated as a decision for the owner

**Decision 1 — the one this run exists to put in front of you.** Ruling 1 rested on a premise that
is false: Manage and Open do not lead to the same place. Manage opens an inline admin accordion
under its own row; Open is the only route from the project list to the project detail page. Three
courses are open, and only you can choose:

  (a) **Leave both controls.** Nothing further is done. The redundancy you were removing does not
      exist, so there is nothing to remove.
  (b) **Remove Manage instead**, and reach the inline admin panel from inside the detail page.
      That moves a reachable control and needs its own authorisation.
  (c) **Make Manage navigate to the detail page and then remove Open.** That changes a control's
      behaviour, which no ruling authorises and which this run deliberately did not do.

**Decision 2.** Rulings 4 and `NAMING_AUTHORITY.md` now contradict each other in the repository.
Until one is revised, any future run reading the authority first — which the handoff's own banner
instructs it to do — will act against ruling 4. Say which is the authority.

**Decision 3.** Five consecutive runs have leaked or aborted a fault injection, and this one leaked
neutered guards into a *production analytical file*. Authorise a run whose whole object is the
campaigns themselves: make every one of them restore inside a `finally`, and add a guard that
fails the suite runner if `git status --porcelain` is non-empty at the end of any campaign.

**Decision 4.** `new_id`/`old_id` is the last surviving second name for the module identifier, and
moving it means either editing a pinned baseline artifact's header row or accepting a translation
layer. Say which, or say it stays.

Carry-forward items 1 and 2 (the hard-coded deep-dive illustrations, and
`research/deepdive.html` computing from the legacy client-side signals blob) remain **Run 53** and
were not attempted here.

---

## Carry-forward, unacted

1. **The deep-dive illustrations are hard-coded** — "3 of 8", "73%",
   `metricBox("Audit trail","100%","amber")` — and three were left with no honest replacement after
   Run 51's compliance split. They must compute from the stored row. **Run 53**, entangled with
   item 2. Not attempted.
2. **`research/deepdive.html` computes from the legacy client-side signals blob in all 77 panel
   bodies**, which the document pipeline does not write, so a project computed through
   `projectupload` and `projectcompute` shows "Awaiting analysis: no signal inputs yet." there.
   Re-pointing it changes what it shows. **Run 53.** Not attempted; its panel bodies and hard-coded
   illustrations were not touched.
3. **CPI 1.22 on the site render.** Needs read access to PRJ-001's stored rows, which no session
   may have. The open question is which document type wrote `pv`.
4. **The `historical_data` triple**, Run 47's only unimplemented relation.
5. **`signal_inputs.sources` records no source field name.**
6. **Four status comparisons remain case-sensitive**, two in `decision.js`.
7. **Two Run 45 census artifacts do not match the v30 release manifest.**
8. **`test_run47_evm_consistency.py` swallows its own traceback.**
9. **Run 47's handoff entry is at the bottom of `T6_HANDOFF.md`.** Left there.
10. **`NAMING_AUTHORITY.md` conflicts with ruling 4.** Confirmed this run at lines 96-97, quoted in
    incidental finding 2. The file was left alone; its revision is not ordered.
11. **`groupByCategory` drops a panel whose key resolves to no category.** Run 51's guard appending
    unclaimed panels beneath the groups is still in place at `deepdive.js:2318-2324`.

---

## §10 — Freeze and merge

**Reconciliation first, then the identity.** Run 51 paid four mints. This run paid **three**, and the
second and third were discoverable only by running the full suite against the new manifests: the first pass
reconciled the identifier guards, and the second surfaced ten pinned version-boundary and
frozen-immutability guards still pinned to `sim-2026.08-v34` / `og-participant-2026.08-v19` plus
`run36.fault35`, whose exception-record check had to be re-pointed at the record of the successor
that moved each file rather than at the current record. The third pass found `test_run25_rail_removal.py`'s
manifest-chain allowlist, which had to be extended by `run52_production_tree.sha256`; because
that file is a member of `test_suite_identity`, reconciling it moved the candidate identity
digest, so the identity, the gate and the release records had to be recomputed and committed
again. Blocker B01 is not cleared by editing anything: a dirty working tree is itself the
blocker, so it clears only on a pass taken after the commit.

**Final state: 193 suites, 14,690/14,690, ALL SUITES GREEN, zero red.**

**Minted:** `sim-2026.08-v35` (`server/app/simulation/models.py:679`, with the boundary comment and
`SIMULATION_VERSION_SUPERSEDED = "sim-2026.08-v34"`) and `og-participant-2026.08-v20`
(`code_audit/run52_participant_package_v20_checksums.sha256`, 70 files, seven moved, one
sequence-bearing).

**The change set, every file named:** `assets/js/categories.js`, `assets/js/deepdive.js`,
`assets/js/detail.js`, `assets/js/neural_flow.js`, `assets/js/projectnet2d.js`,
`assets/js/signals.js`, `assets/js/taxonomy.js`, `server/app/simulation/models.py`,
`server/tools/taxonomy_authority.json`, `server/tools/build_client_taxonomy.py`,
`server/tools/participant_packages.py`, `server/tools/production_tree.py`,
`server/tools/build_run37_acceptance.py`, `server/tools/drive_run44_browser.py`,
`server/tools/build_run32_b3_reconciliation.py`, `server/tools/run26_fault_campaign.py`,
`server/tools/run32_b3_browser_verification.py`, `server/tools/run32_qualifier_fault_campaign.py`,
`server/tools/run51_injection_campaign.py`, `server/tools/test_run10_synthetic_v03.py`,
`server/tools/test_run16_material_cost_variance_disabled.py`,
`server/tools/test_run24_empty_project_diagram.py`, `server/tools/test_run26_counts_and_wiring.py`,
`server/tools/test_run28_participant_packages.py`, `server/tools/test_run2_fifteen_defects.py`,
`server/tools/test_run31_version_boundaries.py`, `server/tools/test_run32_client_authority.py`,
`server/tools/test_run32_closure_version_boundary.py`,
`server/tools/test_run32_defensibility_truth.py`,
`server/tools/test_run32_method_class_agreement.py`,
`server/tools/test_run35_closure_voter_identities.py`, `server/tools/test_run36_fault_guards.py`,
`server/tools/test_run36_instrument_qualification.py`, `server/tools/test_run37_freeze_gate.py`,
`server/tools/test_run38_frozen_immutability.py`, `server/tools/test_run39_frozen_immutability.py`,
`server/tools/test_run39_launch_gate.py`, `server/tools/test_run41_preservation.py`,
`server/tools/test_run44_participant_defect_fixes.py`,
`server/tools/test_run49_naming_completion.py`, and NEW:
`code_audit/run52_participant_package_v20_checksums.sha256`,
`code_audit/run52_production_tree.sha256`, `research/freeze/run52_freeze_candidate_identity.json`,
`research/freeze/run52_successor_freeze_gate.csv`,
`research/freeze/run52_candidate_behaviour_digest.json`,
`research/freeze/RUN52_SUCCESSOR_FREEZE_RECORD.json`,
`research/freeze/RUN52_SUCCESSOR_FREEZE_REPORT.md`,
`research/freeze/RUN52_SUCCESSOR_FREEZE_CHECKSUMS.csv`,
`server/tools/build_run52_candidate_identity.py`,
`server/tools/build_run52_successor_release.py`, `server/tools/drive_run52_browser.py`,
`server/tools/drive_run52_premise.py`, `server/tools/run52_injection_campaign.py`,
`server/tools/run52_rendered_text_capture.py`, `T6_HANDOFF.md`, and this report.

**`assets/js/app.js` is NOT in the change set. That is the point of the run.**

### Every gate row, with its verdict

| row | blocker | count | verdict |
|---|---|---|---|
| B01 | dirty candidate identity | 0 | **PASS** |
| B02 | population mismatch | 0 | **PASS** |
| B03 | controlled-stimulus mismatch | 0 | **PASS** |
| B04 | participant-sequence drift | 0 | **PASS** |
| B05 | false defensibility statement | 0 | **PASS** |
| B06 | unexpected execution exception | 0 | **PASS** |
| B07 | Category-9 bypass | 0 | **PASS** |
| B08 | Category-10 authority violation | 0 | **PASS** |
| B09 | voting count is not exactly 2 | 0 | **PASS** — `CORE_VOTING_MODULES = ['A1.7','A1.8']` |
| B10 | current taxonomy dual authority | 0 | **PASS** — one authority present, both mirrors trace to the generator, **runtime lookups failing across all 101 registered modules: none** |
| B11 | package or predecessor mutation | 0 | **PASS** |
| B12 | browser qualification failure | 0 | **PASS** |
| B13 | unresolved blocking Run-36 defect | 0 | **PASS** |
| B14 | unsupported final empirical-validation claim | 0 | **PASS** |
| B15 | candidate behaviour changed during the run | 0 | **PASS** — digest `8fb4d366…` reproduced |

**15 blocker classes evaluated, 0 BLOCKED, gate clean.**
`test_run37_freeze_gate.py` **34/34**. `test_run39_launch_gate.py` **100/100**.
No gate row was disabled, weakened or widened. Every manifest reconciled to TRUE bytes.

### No §9 run-level condition fired

Behaviour digest held; no stored figure changed; no band, status, colour or posture changed; every
runtime lookup for all 101 resolved; no check was deleted; every gate row passed; no reachable
control other than the one ruling 2 names was added, moved or removed; no rendered identifier
changed. **The run merged.**
