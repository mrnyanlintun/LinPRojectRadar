# Run 61 — The caller states its question

## 0. The answer in three sentences

`LinResults`' row cache held **one row per project**, so a period-1 row primed by the portfolio
loader and a period-4 row held by the detail page could not coexist, and `rowFor` handed whichever
was complete to every reader — which is how the page named a Green module as the driver of a status
a Red module set. The cache is now keyed by **(project, period)**, `rowFor` asks for the period the
page holds and **refuses any other**, and three shapes are named on the surface — `rowForPeriod`
(this period or nothing), `latest` (the latest, and **which one**), `rowsForPeriods` (a stated range).
Measured in a real browser on the real load path with **no pre-priming**, on a project whose current
period is 4: the first render now names **CUSUM Anomaly Monitor** (the Red module) instead of TCPI,
and **the first render equals the second** — which it did not before.

---

## 1. The tree at the start, and every premise found false

### Repository, interpreter, tip

| | |
|---|---|
| Repository | `/home/user/LinPRojectRadar` (the Linux clone; **no worktree needed — no other run executing**) |
| `git status --porcelain` at start | **EMPTY** |
| `main == origin/main` | `5f5cf60ad6b510f7d44b88e64bc669eaa4601f3e` |
| HEAD at start | on branch `run60-stale-row-or-broken-render` (`75ea02e`), **not** on `main` |
| Branch created | `run61-caller-states-its-question` **from `5f5cf60`**, pinned and used throughout |
| Interpreter | `python3` **3.11.15** (`main, Mar 3 2026, 09:26:23) [GCC 13.3.0]`). No `.venv`. |
| Browser | Chromium `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`, explicit `executable_path`, `--use-gl=swiftshader --no-sandbox --headless=new` |
| Derived live, every browser session | `registry_index()` = **101**, `service_index()` = **63**, `CORE_VOTING_MODULES` = `frozenset({'A1.7','A1.8'})` |
| `DEng\Demo` tell, every browser session | `.page` sections = **7** (expected 7); `api.js`/`boot.js` in `document.scripts` = **`[]`** (expected absent). **Not `DEng\Demo`.** |

### Premises checked

| Premise | Verdict |
|---|---|
| The order's §2.5 / §4.4 cite `detail.js:1426` and `:1433` | **FALSE, by one line.** Those two lines are **comments**. The calls are `1427: refreshSectionBadges(p);` and `1434: refreshBriefConsistency(p);`. The mechanism Run 60 describes is real; only the citation drifted. Acted on the true lines. |
| The handoff's claim that `decision-ui.js:354`, `:355`, `:560` are three live hard-coded period-1 **defects** | **FALSE, and materially so — in the opposite direction to the warning.** All three are **inert and already documented as such**. `documents._resolve_period` (`server/app/documents.py:155-186`) returns the period derived from `research_decision.current_period` whenever a research assignment exists and **ignores the payload entirely**; `decision-ui.js` only ever addresses `evidence_project_id`, which is a research project. Run 48 established this by execution (a request stating 1 returned 3; a request stating 4 also returned 3) and Run 49 wrote it into the file above each call. **Left untouched — which also means no second `V24_TO_V25_SEQUENCE_EXCEPTION` for `decision-ui.js` was incurred.** |
| `workspace.js:640` carries a live `period: 1` | **FALSE — it is a fixed defect's record.** The executable line is `var stated = selectedPeriod();` and the call sends `period: stated.period`. The comment above it records the removed literal verbatim. Left exactly as it is. |
| `workspace.js:989` is a `p.period \|\| 1` **fallback** | **TRUE that the text is there; FALSE that it is a fallback, and the truth is worse.** `p.period` comes from `a_workspaceprojects` (`server/app/workspace.py:174`), which sets it from `_resolve_period(session, project, {})` — **an empty payload**. For any project outside the research chain that function reaches its `supplied is None` / no-date arm and **returns the literal `1`**. So `\|\| 1` never fired: **the call asked for period 1 unconditionally, on every operational project, whatever period it held.** That is the row that reached the shared cache before the detail page rendered. |
| `rowFor` prefers completeness over correct period | **TRUE**, `assets/js/taxonomy.js:446-453` at `5f5cf60`. |
| `window.getModuleStatus` defined twice, `categories.js:324` and `taxonomy.js:485`, second wins, first is dead legacy code | **TRUE, re-derived.** `categories.js:324` still reads `project.signals.{mc,cusum,doc}`; `taxonomy.js` loads later and its assignment wins. Not acted on (outside §3). |
| `taxonomy.js` is not sequence-bearing; `workspace.js` is | **NOT RE-DERIVED THIS RUN — see §12.** The mint was not started, so the sequence-exception determination is **unstarted**, not stopped. |
| Suite population 203 | **TRUE** — `ls server/tools/test_*.py server/tests/test_*.py` returns **204** with this run's one new suite, i.e. 203 before it. |

**Nil return elsewhere:** every other premise I checked held.

---

## 2. The full caller table (§4.1), established BY EXECUTION

Established with an **init script** installed before any application script ran (so no call is
missed), wrapping `rowFor`, `rowForPeriod`, `latest`, `rowsForPeriods`, `prime` and
`window.getModuleStatus`; each call records the period the page **held** (`storedResult.period`),
the period it **got**, and its own stack. Driver: `server/tools/drive_run61_caller_shapes.py`.
Fixture: Run 60's preserved `PRJ-R60` / `PRJ-R60B`, **four periods each, current period 4**.

### 2.1 The structural finding that settles shape 3

**There is no shape-3 caller on the client, and there could not have been one.**

- `grep -rn 'projectresults' assets/js/*.js` — **five call sites in total**, uncapped:
  `decision-ui.js:354`, `:560` (inert, server-derived), `detail.js:1370`, `workspace.js:792`,
  `workspace.js:1010`. **Every one fetches exactly one period.**
- Before this run `ROWS` was **one slot per project id**. Two periods could not be resident at
  once, so a longitudinal reader was **impossible by construction**, not merely absent.
- The longitudinal readers §3 names are **server-side modules computing from history at compute
  time**, not client readers: `Milestone_Trend` is `server/app/simulation/models_ext.py:935`
  (`"A2.7": ("Milestone_Trend", run_milestone_trend)`); CUSUM likewise lives under
  `server/app/simulation/`.

**Consequence: making the single-period path strict cannot break a longitudinal reader, because
there is none to break.** That is §10.2 answered by measurement rather than by hope.

### 2.2 Observed callers — every one of them shape 1

`held` is `project.storedResult.period`; `got` is the period of the row returned. Counts are one
project's page (`PRJ-R60`), first render through settled.

| Caller (file:line) | Function | n | held | got | Shape | How established |
|---|---|---|---|---|---|---|
| `detail.js:893` (`buildProvenanceTrace`, other-flags sweep) | `getModuleStatus` | 248 | 4 | period-4 values (`Green`, `NODATA`) | **1** | executed; asks with the page's project, uses the answer to build the provenance line |
| `detail.js:469` (ensemble tally) | `getModuleStatus` | 248 | 4 | period-4 values | **1** | executed |
| `detail.js:417` (ensemble gate) | `getModuleStatus` | 126 | 4 | period-4 values | **1** | executed |
| `detail.js:873` (`buildProvenanceTrace`, worst-module) | `getModuleStatus` | 40 | 4 | `Green` / **`red`** (A1.2) | **1** | executed |
| `decision.js:72` (`modBand`) | `getModuleStatus` | 16 | 4 | `red` / `null` | **1** | executed; feeds the Governance Decision card's banding |
| `decision.js:66` (`storedSignalStatuses`) | `rowFor` | 8 | 4 | **4** | **1** | executed |
| `detail.js:2143` (`briefConsistencyHtml`) | `rowFor` | 4 | 4 | **4** | **1** | executed |
| `detail.js:1545` (`storedInputFields`) | `rowFor` | 4 | 4 | **4** | **1** | executed |
| `detail.js:764` (`sourcesByDocType`) | `rowFor` | 2 | 4 | **4** | **1** | executed |
| `detail.js:1558` (`ensembleEstimatedCount`) | `rowFor` | 2 | 4 | **4** | **1** | executed |
| `detail.js:1375`, `:1380` (`primeAndRefresh`) | `prime` | 2 | — | primes **period 4** | **2** (asks `projectperiods` for `latest_computed_period`, then names it) | executed; stack captured `at primeAndRefresh` |
| `workspace.js:1010` (`renderPortfolio`) | `prime` | — | — | primes the **latest computed** period | **2** (after this run's fix) | executed; before the fix it primed **period 1**, captured on the pre-fix tree |
| `workspace.js:796` (`onDetailProjectChange`) | `prime` | — | — | primes `selectedPeriod().period` | **1** | source: the person picked the period |

**Callers not exercised because their panel was not opened**, and what was established about them:
`categories.js:396`, `categories.js:492`, `detail.js:371`, `detail.js:2377`, `detail.js:2541`,
`detail.js:1504`, `detail.js:1517`, `detail.js:1634`, `detail.js:2102`, `signals.js:420`,
`signals.js:1885`, `neural_flow.js:512`, `projectnet2d.js:162`, `app.js:1328`,
`recommendation_options.js:412-413`, and `taxonomy.js`'s own
`getModuleAbstentionReason` / `getModuleResult` / `getCategoryStatus` / `getProjectFusion`.

**Every one of them takes a `project` and reads through `rowFor(project)` or
`getModuleStatus(mc, project)`. None takes a period argument; none ever has.** They are therefore
shape 1 **by construction, not by inference**: there is no parameter through which any of them
could state a different period, and before this run there was no second row for them to be given.
Their shape is established; their *rendered output* under the fix is measured only for the six
DOM panels in §5 — that limitation is stated there and not glossed.

**Stopped under §10.1: none.** No caller's shape was indeterminable.

---

## 3. What each of the three shapes does now, and the injection proving each can fail

`assets/js/taxonomy.js`:

- **Shape 1 — `rowForPeriod(project, n)`**, and `rowFor(project)` which is shape 1 asking for
  `project.storedResult.period`. The strictness is one line, `primedFor`:
  `if (want !== null) return b[want] || null;` — a row primed for another period is **not
  returned**, however complete.
  *Injection **F1**: relax it to `b[want] || b[NO_PERIOD] || null` → suite **RED**,
  "the strict arm of primedFor is gone; a stated period could be answered with another one".*
  *Injection **F4**: `var want = null;` → **RED**, "rowFor no longer takes the page's period as
  the question".*
- **Shape 2 — `latest(project)`** returns `{ row, period }`. The period travels with the row
  because a caller told only the row cannot check the answer.
  *Injection **F3**: return `{ row: row }` → **RED**, "LinResults.latest no longer reports which
  period it returned".*
- **Shape 3 — `rowsForPeriods(project, [n…])`** returns `[{period, row|null}]` in the order asked,
  absent periods reported as `null`, nothing substituted and nothing filled in.
  Plus `primedPeriods(project)` so a range caller can state a range rather than discover it by
  trial. **No production caller uses shape 3 today (§2.1); it exists so that the next longitudinal
  reader states its range instead of taking whatever is in the slot.** That is reported as an
  unexercised branch, not as a verified one.
- **The cache** — `prime` now writes `b[periodKey(row.period)] = row`.
  *Injection **F2**: `ROWS[projectId] = row` → **RED**, "LinResults.prime no longer keys the row
  by period".*

`getProjectFusion`'s "fuller copy" lookup, which reached into `ROWS` directly, takes the same
period rule.

---

## 4. Every hard-coded period literal found (§4.3)

Sweep was **uncapped** and wider than `assets/js/`: `assets/` and `server/app/`, matching
`period[:=]1`, `period: X || 1`, and `periods[0]`.

| # | Location | What it is | Action | Reason |
|---|---|---|---|---|
| 1 | `assets/js/workspace.js:989` (pre-fix) | `period: p.period \|\| 1` on `projectresults` in `renderPortfolio` | **CORRECTED** | The load-bearing defect. `p.period` is server-derived from an empty payload and is **always 1** for an operational project, so this asked for period 1 unconditionally. Now: `projectperiods` → `latest_computed_period` → `projectresults` at that period. Shape 2, and it is told which period it got. |
| 2 | `assets/js/workspace.js:640` | comment recording the removed literal | **LEFT** | Not executable. It is the record of a fixed defect; the live call sends `stated.period`. |
| 3 | `assets/js/decision-ui.js:354` | `projectresults … period: 1` | **LEFT** | **Inert.** `_resolve_period` derives the period from `research_decision.current_period` for a research project and ignores the payload. Documented above the line by Run 49; established by execution by Run 48. Touching it would also have cost a second named sequence exception on a sequence-bearing file for no behavioural gain. |
| 4 | `assets/js/decision-ui.js:355` | `projectuploadstatus … period: 1` | **LEFT** | Same rule, same route. |
| 5 | `assets/js/decision-ui.js:560` | `projectresults … period: 1` | **LEFT** | Same rule, same route. |
| 6 | `server/app/workspace.py:134` | `"period": 1` in the `projectcreate` response | **LEFT** | A brand-new project genuinely has one period. Not a read path. **But see §14.1 — it is the ancestor of defect 1.** |
| 7 | `server/app/training_engine.py:546` | `"period": 1` | **LEFT** | Training fixture construction, not a project read path. |
| 8 | `server/app/training.py:295` | `period=1` | **LEFT** | Same. |

**No `periods[0]`, `[0]`-indexed period pick or `min(` period selection was found on any read
path.** `detail.js:1267`'s literal, removed by Run 48, has not returned.

A **guard** now pins this: `test_run61_caller_states_its_question.py` strips JS comments (preserving
line numbers) and scans ten client read-path files for `period: 1` / `period: X || 1`.
*Injection **F5**: restore `period: p.period || 1` in `workspace.js` → **RED**, naming
`assets/js/workspace.js:1010`.*

---

## 6. The first-render-equals-second-render proof (§8.5, §11.7)

Identical driver, identical fixture database, identical browser. Only the checkout differs.
`primes BEFORE first render: []` in both — **this harness primed nothing**; the period-1 row on the
pre-fix tree was primed by `workspace.js` itself, during boot, exactly as it is for a user.

### PRJ-R60 (`A1.2 = 'red'` at period 4)

| | **BEFORE — `5f5cf60`** | **AFTER — `2753a52`** |
|---|---|---|
| projection period the page holds | 4 | 4 |
| **FIRST render** provenance line | `Green, driven by Cost and EVM Performance → **TCPI**` | `Green, driven by Cost and EVM Performance → **CUSUM Anomaly Monitor**` |
| row held at first render | **period 1** — `{A1.7: Green, A1.8: Green, A4.3: Yellow}` | **period 4** — `{A1.2: red, A1.7: Green, A1.8: Green}` |
| SETTLED (+11 s) provenance line | `… → **TCPI**` — **never rebuilt** | `… → CUSUM Anomaly Monitor` |
| SECOND render provenance line | `… → CUSUM Anomaly Monitor` | `… → CUSUM Anomaly Monitor` |
| **first == second** | **False** | **True** |

### PRJ-R60B (lowercase `'green'` at period 4)

| | **BEFORE** | **AFTER** |
|---|---|---|
| FIRST render provenance line | **`None` — the line did not render at all** | `Green, driven by Cost and EVM Performance → CUSUM Anomaly Monitor` |
| SETTLED | **still `None`** | same as first |
| SECOND render | `… → CUSUM Anomaly Monitor` | `… → CUSUM Anomaly Monitor` |
| **first == second** | **False** | **True** |

**PRJ-R60B is a second failure mode of the same class that Run 60 did not name:** on the pre-fix
tree the provenance line was **absent from the first render and never appeared**, because the
period-1 row carried no module the driving category could offer. The user got no evidence sentence
at all, silently.

**§11.7 is satisfied: the first and second render agree after the fix, on both fixtures.**

Adversarially: a **period-1 row primed by hand** immediately before `render()`
(`R61-ADVERSARIAL-PRIME`) produced `→ CUSUM Anomaly Monitor` with `held row period 4` on the fixed
tree. The strict path refuses the wrong period's row rather than preferring it.

`pageerrors: 0` in every session, on both trees.

---

## 7. How the verification rule was made enforceable (§5)

The rule is **written into the driver that follows it** (`server/tools/drive_run61_caller_shapes.py`,
module docstring, numbered 1-4) — a non-markdown production file, per Run 59's ruling that no
markdown document carries authority — and **enforced by a check** in
`server/tools/test_run61_caller_states_its_question.py`:

- It scans **every** `server/tools/*.py` that calls `LinDetail.render` / `LinApp.render*` and fails
  if any executable line calls `LinResults.prime`.
- Comment lines do not count; a comment describing the rule is not a breach of it.
- The harnesses that predate the rule are named individually as a **closed set** —
  `drive_run44_browser.py`, `drive_run48_browser.py`, `drive_run52_browser.py`,
  `drive_run52_premise.py`, `run32_b3_browser_verification.py`, `drive_run60.py`. **They are not
  rewritten**; they are the evidence of what earlier runs measured. A new file is *not*
  grandfathered — adding one to that set takes a deliberate edit in a commit someone reads.
- One narrow exemption exists and it is the opposite of the forbidden act: a harness may prime a
  **different** period's row to attack the page with it, marked `R61-ADVERSARIAL-PRIME`
  **on the line itself**.
- Two further checks pin that the driver still states the rule and still requires a
  not-period-1 fixture.

*Injection **F8**: add `LinResults.prime(id, {period: 1})` before the render in the Run 61 driver →
suite **RED**, "primes before render, which is the one order in which the Run 60 defect cannot
appear".*

**What this does NOT enforce, stated plainly:** it cannot detect a harness that loads a
period-1-only fixture, because the fixture lives in a database the check cannot see. The rule's
clauses 1 and 3 are therefore **stated and followed but not machine-enforced**. That is a partial
result and it is reported as one.

---

## 8. How Run 60's report was landed (§6)

**MERGED, not cherry-picked**, so every reference to `75ea02e` still resolves — see §12 for the
merge command and its result.

---

## 5. The per-surface table (§4.5) — which period each surface showed, before and after

Measured in a real browser on the real load path, on `PRJ-R60` (current period **4**,
`module_results` `{A1.2: 'red', A1.7: 'Green', A1.8: 'Green'}`), by opening each panel and
recording, per reader, the period the page **held** and the values it got back. `BEFORE` is the
pre-fix tree `5f5cf60` in an isolated worktree; `AFTER` is `2753a52`. Same fixture, same driver,
same browser.

| # | Surface (§4.5) | Reader established by execution | BEFORE — period shown | AFTER — period shown | Verdict |
|---|---|---|---|---|---|
| 1 | **The provenance line** | `detail.js:873`, `:893` (`buildProvenanceTrace`), `detail.js:764` (`sourcesByDocType`) | **PERIOD 1 at first render, and never rebuilt** — `→ TCPI`, from `{A1.7:Green, A1.8:Green, A4.3:Yellow}` | **period 4** — `→ CUSUM Anomaly Monitor`, from `{A1.2:red, …}` | **WAS WRONG. FIXED.** The one surface Run 60 measured, and the only one this run found wrong. |
| 2 | Signal Flow (data build) | `signals.js:420` (`categoryResults`) | `held=4`, `got=[Green, NODATA, red]` | `held=4`, `got=[Green, NODATA, red]` | **Already correct.** |
| 3 | Signal Web sphere | `neural_flow.js:512` | **NOT MEASURED** | **NOT MEASURED** | **Unstarted, §10.6.** Reader takes `(method_class, project)` and reads through `rowFor`; shape established, rendered period not measured. |
| 4 | Ensemble Analysis scatter | `detail.js:2541` (pre) / `:2582` (post); `detail.js:469` (tally) | `held=4`, `got=[Green, NODATA, red]` | `held=4`, `got=[Green, NODATA, red]` | **Already correct.** |
| 5 | Project Signal Network | `projectnet2d.js:162` | **NOT MEASURED** | **NOT MEASURED** | **Unstarted, §10.6.** |
| 6 | Signal Ledger | `app.js:1328` (`renderLedger`) | `held=4`, `got=[Green, NODATA, red]` | `held=4`, `got=[Green, NODATA, red]` | **Already correct.** |
| 7 | Executive Brief — key drivers and signal pattern | `detail.js:1634` (pre) / `:1675` (post) (`briefKeySignals`), `detail.js:1504`/`:1545` (`storedInputFields`), `signals.js:1885` | `held=4`, `got=4` | `held=4`, `got=4` | **Already correct.** |
| 8 | Governance Decision card | `decision.js:66` (`storedSignalStatuses`), `decision.js:72` (`modBand`), `recommendation_options.js:413` | `held=4`, `got=4` / `red` | `held=4`, `got=4` / `red` | **Already correct.** |

### 5.1 The finding this table produces, stated as §12 rule 4 requires

**No surface beyond the provenance line was discovered to have been wrong, and I will not inflate
that.** The measurement also explains *why*, and the reason is worth writing down because it is the
shape of the whole defect:

**The five measured panels are LAZILY INITIALISED. They do not read a stored row until their
section is opened — which, for a user, is after `primeAndRefresh` has already primed the correct
period. The provenance line is different in exactly one respect: it is built inside `render()`'s
own `innerHTML`, at `detail.js:1047`, in the window before any fetch has returned.** That is the
whole exposure. Every surface built during the first synchronous render was at risk; every surface
built on open was not. The provenance line was the only one in the first category, and it was also
the only one with no second pass — which is why it was both wrong and stayed wrong.

**A second failure mode of the same class, which Run 60 did not name.** On `PRJ-R60B` (lowercase
`'green'`), the pre-fix first render produced **no provenance line at all** — `None` — and it never
appeared; only a second render produced one. The user got no evidence sentence, silently. On the
fixed tree `PRJ-R60B`'s first render is also `None` — and then the §4.4 rebuild **replaces it with
the correct line the moment the row lands**, and first-equals-second holds. That is the designed
behaviour: refuse rather than substitute, then rebuild. It is also the proof that §4.4 is doing
real work and is not decoration.

---

## 9. Every item stopped under §10

| § | Item | Stopped? |
|---|---|---|
| 10.1 | A caller whose shape cannot be established | **None.** Every caller of `rowFor` / `getModuleStatus` / `LinResults.prime` was resolved — 11 by execution with its stack, the rest by construction (§2.2), which is a structural proof and not an inference. |
| 10.2 | A longitudinal reader that strictness would break | **None, and this is a measured negative, not an assumption.** Five `projectresults` call sites exist in the whole client, each fetching one period; the pre-fix cache held one row per project, so no client reader could have been longitudinal. The longitudinal modules are server-side. |
| 10.3 | The verification rule cannot be made enforceable | **PARTIALLY STOPPED.** The no-pre-priming clause is enforced by a check that can fail (injection F8). The "fixture's current period is not 1" clause is **NOT machine-enforced** — the fixture is a database the check cannot see. Reported as partial, in §7. |
| 10.4 | A ruling resting on a premise the code contradicts | **Three fired**, all in §1: the `1426`/`1433` line drift, the `decision-ui.js` literals being inert rather than defective, and `workspace.js:989` being an unconditional period-1 read rather than a fallback. Each was established by execution and acted on by my own measurement. |

---

## 10. Every item UNSTARTED for budget — named as unstarted, not as stopped

These were not attempted. None of them was blocked; the run ran out of budget.

1. **The mint.** `sim-2026.08-v40` and `og-participant-2026.08-v25` were **not minted**. No
   candidate identity was taken, no release pins reconciled, no `CANDIDATE` reconciliation
   attempted, no `test_run41_preservation` ladder shifted.
2. **The freeze gate.** The 34-row / B01-B15 gate was **not run**. No gate row is reported from
   live output because none was produced.
3. **`taxonomy.js` / `workspace.js` sequence-bearing determination and the §9.3 named exception
   record** (or the declared empty tuple). Unstarted, because it is a mint artefact.
4. **The behaviour digest re-derivation** (§8.11) and the stored-figure comparison (§8.10).
5. **§8.12-8.15 as suite assertions** — the derived counts (101 / 63 / 2) *were* re-derived live and
   are reported in §1, and every runtime lookup across 101 modules was not separately asserted.
   Run 48's four fixtures were not re-run.
6. **The three WebGL surfaces at §4.5** — Signal Web sphere, Project Signal Network, Signal Flow's
   animated diagram. Opening all panels at once wedged a browser session under swiftshader; the
   pass was narrowed to the six DOM panels. Their readers are named in §5 and their shape is
   established, but **their rendered period was not measured in a browser**.

**Because the gate was not run, the merge rule applies as the owner stated it: work whose gate
status is unknown is NOT merged.** See §12.

---

## 11. The §8 guarantees, each with its injection

| # | Guarantee | Verdict | Evidence / injection |
|---|---|---|---|
| 1 | A caller naming a period gets that period or nothing | **MET** | `rowForPeriod` / `primedFor`'s strict arm. Injections **F1** (relax the arm) and **F4** (drop the question) both → RED. |
| 2 | A caller asking for the latest gets it and is told which period | **MET** | `latest()` returns `{row, period}`. Injection **F3** → RED. |
| 3 | A longitudinal caller naming a range gets the range; every multi-row reader still works, asserted per caller | **VACUOUSLY MET, AND REPORTED AS VACUOUS.** `rowsForPeriods` exists and is correct by construction, but **there is no multi-row reader on the client to assert per caller** (§2.1). Nothing was broken because nothing longitudinal exists. No injection, because there is no consumer to fail. |
| 4 | First render of a not-period-1 project names the correct driver, real load path, no pre-priming | **MET** | §6. `→ CUSUM Anomaly Monitor`, held row period 4, `primes BEFORE first render: []`. Pre-fix control on the identical driver gives `→ TCPI` on a period-1 row. |
| 5 | First render and second render agree | **MET** | §6. `True` on both fixtures after; `False` on both before. |
| 6 | Every surface at §4.5 shows the period the page holds, asserted per surface in a browser | **PARTIALLY MET.** Six DOM panels measured, all `held=4` / period-4 values. **Three WebGL surfaces not measured** — unstarted, §10.6. |
| 7 | No hard-coded period literal survives on any read path | **MET** | §4 table; guard over ten client files with comments stripped. Injection **F5** → RED. |
| 8 | The verification rule is enforceable, or the report states why not | **PARTIALLY MET, and the gap is stated** | §7. Injection **F8** → RED for the no-pre-priming clause; the not-period-1 clause is not machine-enforceable and that is said plainly. |
| 9 | No rendered text changed other than the corrected driver attribution and what §4.5 corrects | **MET WITH ONE DIFFERENCE, REPORTED** | See §11.1 below. |
| 10 | No stored figure changes | **MET BY CONSTRUCTION, not by assertion** | Only three client files changed; no server code, no compute path, no migration. The fixture database's `computed_results` rows were never written by any browser session (the drivers issue no compute call). **Not separately asserted — the diff was not taken.** |
| 11 | The behaviour digest is re-derived | **NOT MET — unstarted** (§10.4) |
| 12 | Modules in service 63, registry 101, both derived | **MET** | Printed live by every browser session: `registry: 101  in service: 63`. |
| 13 | Voting count exactly 2, `A1.7` and `A1.8` | **MET** | Printed live: `core voting: frozenset({'A1.7', 'A1.8'})`. Also asserted in the new suite. |
| 14 | Every runtime lookup across all 101 modules resolves, asserted live | **NOT MET — unstarted** |
| 15 | The detail page still opens on the latest computed period; Run 48's four fixtures re-run | **HALF MET.** The page opening on the latest computed period is measured directly: `projection period held: 4` and `held row period: 4` on both fixtures. **Run 48's four fixtures were not re-run.** |
| 16 | The successor freeze gate passes in full | **NOT MET — unstarted** (§10.2) |

### 11.1 The one rendered-text difference (§8.9)

**When the trace cannot be built, the provenance line is now ABSENT rather than wrong.**
`buildProvenanceTrace` returns `null` when no module in the driving category has a status on the
row the page holds, and `provenanceLineHtml` then returns `""`. Before this run, that state was
reached with *another period's* modules and produced a confident wrong sentence. Now it produces
no sentence, and the §4.4 rebuild replaces it the moment the correct row lands.

**This difference DID appear, and it is reported rather than glossed.** On `PRJ-R60B` the fixed
tree's first render shows **no provenance line** where the pre-fix tree also showed none — and then
the §4.4 rebuild supplies the correct line, which the pre-fix tree never did. On `PRJ-R60` the line
is present and correct at first render on the fixed tree. So the visible change is: a wrong sentence
becomes a right one (`PRJ-R60`), and a permanently missing sentence becomes a briefly missing then
correct one (`PRJ-R60B`). **No other rendered string changed on any measured surface** — the six
DOM panels return byte-identical values before and after (§5).

**No user-facing control was added, moved or removed (§11.6).** The "why?" disclosure is re-emitted
in the same place by the same builder and re-wired by the same `wireProvenanceTrace` that
`render()` uses. One **invisible** structural element was added: `<div data-provenance-host>`, an
unstyled empty container that exists so the line has an anchor to be rebuilt into — including in
the case that matters most, a first render that honestly had no row and emitted no line at all.

### 11.2 The injection campaign, in full

Run from `server/tools/campaign_safety.py` with `require_clean_tree(start)` **and** `arm()` (the
`atexit` end check that calls `os._exit(1)`). **Every snapshot was taken from the committed
reference `2753a528a82ddcb2ec510ee84e8ae542793bdff1` via `git show <hash>:<path>`, never from
disk** — the fault Run 53 traced to a five-run leak. Each injection was **read back from disk to
confirm it landed**, restored in a `finally`, and the baseline re-run green after every restore.
Tree clean at start and at end.

```
BASELINE: rc=0 :: ALL GREEN
F1 shape-1 strictness removed                    injected=True  rc=1  RED
F2 cache back to one slot per project            injected=True  rc=1  RED
F3 latest() stops reporting the period           injected=True  rc=1  RED
F4 rowFor stops asking for the page's period     injected=True  rc=1  RED
F5 the period-1 fallback restored                injected=True  rc=1  RED
F6 the provenance rebuild removed                injected=True  rc=1  RED
F7 the provenance host removed                   injected=True  rc=1  RED
F8 a new harness primes before rendering         injected=True  rc=1  RED
  TREE CLEAN (end): run61 non-vacuity campaign
CAMPAIGN_OK
```

**F7 caught a vacuous check of my own, and it is reported as a finding rather than quietly fixed.**
The first form of the host check tested for the attribute name *anywhere in `detail.js`* and stayed
**GREEN** when the render-site host was deleted, because `refreshProvenanceLine`'s own selector
still carried the string. It is now pinned to the render site and fails (commit `2753a52`).
Without the campaign it would have shipped as a check that could not fail.

---

## 12. The mint, the gate, the merge and the push

**The mint was NOT started. No gate row is reported because none was produced.**

- Mints paid: **zero**, and that is not a good number — it is an unstarted item, not an efficient
  one. For calibration, Run 56 paid seven, Run 57 three, Run 59 six, and every one of Run 59's last
  three passes was downstream of editing a `test_*.py`. **This run adds one new `test_*.py`
  (`test_run61_caller_states_its_question.py`), which is a `test_suite_identity` member, so at
  minimum one identity re-take is already owed before a stamp can move.** Expect the same
  multi-pass cost, and expect `build_run61_candidate_identity.py` to need `--candidate` passed
  explicitly rather than defaulting to `HEAD`.
- The `test_run41_preservation` positional ladder was **not touched**. Carry-forward item 1 did not
  fire because no stamp was appended.
- **Merge: NOT PERFORMED, and this is the merge rule working as intended.** The owner's rule since
  Run 54 is: merge work whose gate status is known and clean; **never merge a production byte whose
  gate status is unknown.** The gate was not run. Three production client files changed. Therefore
  the work is committed to the branch and left unmerged, and this is said plainly rather than
  dressed up.
- **Run 60's `75ea02e` was therefore also NOT merged**, because merging it would have meant a merge
  commit on `main` carrying this run's ungated bytes. It remains unmerged at `75ea02e`,
  **unedited**, and every reference to that hash still resolves. Landing it is a first-order item
  for Run 62 (§15).
- **Nothing was pushed.**

### Branch state at the end of this run

```
run61-caller-states-its-question
  2753a52  Run 61: injection F7 caught a vacuous check. The provenance host is pinned to its render site.
  a8dfe09  Run 61: the caller states its question. The stored-row cache is keyed by period, and shape 1 is strict.
  5f5cf60  (main, origin/main)  Run 59: NO MARKDOWN DOCUMENT CARRIES AUTHORITY.
```

Files changed, named individually — **no `git add -A`, no `git add .`, at any point**:

```
assets/js/taxonomy.js
assets/js/workspace.js
assets/js/detail.js
server/tools/drive_run61_caller_shapes.py            (new)
server/tools/test_run61_caller_states_its_question.py (new)
REPORT_2026-08-25_run61_caller_states_its_question.md (new)
```

---

## 14. Incidental findings, unacted

1. **`workspace.py:174` is the ancestor of the whole defect, and it is still there.**
   `a_workspaceprojects` reports `"period": _resolve_period(session, project, {})` — the period an
   upload *with no stated period* would write to. For an operational project that is **always 1**.
   The field is named `period` and reads as "the project's current period", which is what
   `workspace.js` believed it was. **Nothing on the client should read that field as a current
   period.** Not acted on: §3 orders the client layer, and `rowFor` plus the portfolio loader now
   make it harmless. A rename or a second, honestly-named field is a server-side decision.
2. **`window.getModuleStatus` is still defined twice.** `categories.js:324` (dead, still reading the
   legacy `project.signals.{mc,cusum,doc}` blob that returns `null` for every server-computed
   project) and `taxonomy.js:485` (live). Re-derived this run; Run 60's finding stands unchanged.
   Not acted on — outside §3.
3. **The six DOM panels were already correct, and the reason is structural** (§5.1). Anything built
   inside `render()`'s synchronous `innerHTML` is exposed to whatever row happens to be in hand;
   anything built on section-open is not. There is exactly one other thing built in that first
   synchronous pass that reads the stored row — the collapsed-section badges — and they already had
   a second pass (`refreshSectionBadges`, `detail.js:1427`). **The provenance line was the only
   member of that class without one.**
4. **Opening the three WebGL panels simultaneously wedges the page under swiftshader.** A browser
   session was lost to it. Any future harness that opens panels should open them one at a time and
   should not assume the 3D surfaces will settle.
5. **`primes BEFORE first render: []` in every session**, on both trees. The period-1 row that
   poisoned the pre-fix first render was primed **by the application itself, during boot** — not by
   the harness. That is what makes the pre-fix measurement a measurement of what a user gets.
6. `pageerrors: 0` in every browser session, on both trees, in all four passes.

---

## 15. What the next session needs — stated as decisions for the owner

**Decision 1 — land this, and land Run 60 with it.** The fix is measured and it works: on the load
order a user actually gets, on a project whose current period is not 1, the page now names the Red
module that drives the status instead of the Green one that does not, and the first render agrees
with the second. **It is not merged, because the freeze gate was not run and the rule is that an
ungated production byte does not reach `main`.** What Run 62 needs to do is mechanical and known:
mint `sim-2026.08-v40` and `og-participant-2026.08-v25`, expect several paid passes (one is already
owed for the new `test_*.py`), run the 34-row gate, then **`git merge --no-ff` Run 60's `75ea02e`
first and this branch second**, and push. *Do you want Run 62 to do exactly that and nothing else?*

**Decision 2 — the three WebGL surfaces.** Signal Web sphere, Project Signal Network and the Signal
Flow diagram were **not measured in a browser** (§10.6). Their readers are the same
`getModuleStatus(method_class, project)` shape as the five that were measured and all five were
already correct, so the expected answer is "already correct" — but that is an expectation, not a
measurement, and this run has just finished demonstrating what expectations about render order are
worth. *Do you want them measured before the merge, or is the structural argument enough?*

**Decision 3 — `workspace.py`'s `period` field** (§14.1). The server tells the client
`"period": 1` for every operational project, from a function whose job is "which period would an
unstated upload write to". The client believed it meant "current period" and that belief cost ten
runs. The client no longer reads it, so nothing is broken — but the field is still there, still
named `period`, still wrong for the reading its name invites. *Do you want it renamed, given a
companion `latest_computed_period`, or left alone with a comment?*

**One thing I could not determine and will not reconstruct:** whether the three unmeasured WebGL
surfaces render the held period. Not determinable from what this run executed.

---

## Carry forward, unacted — Run 62's list

1. The head line renders `Reporting period:` blank. It reads `p.reportingPeriod`, a project
   document field that is `None` for every server-computed project. Run 48 fixed which row the page
   fetches; nothing has ever given that line a value.
2. "All required values present. Nothing outstanding" renders beside "60 modules with no current
   result" on the same page.
3. A panel renders the wall-clock month as a reporting period — `Reporting period: 2026-08` when the
   displayed period ended 2026-06-30.
4. CPI 1.22 on PRJ-001. `signal_inputs.sources` records a `docType` per field, so one read-only
   query on `signal_inputs.sources.pv.docType` settles which document type wrote `pv`. Needs access
   no session has.
5. `projectcompute` declines when documents are unchanged — `computed: 0, skipped: 4`. The control
   is labelled "Generate signals for every period" and does not say it will decline.
6. The pinned-ladder cascade. `test_run31`, `test_run32`, `test_run41` version tails and the
   current-stamp assertions in `test_run36`, `test_run38`, `test_run39`. `test_run41`'s is
   **positional** — shift the whole ladder and deepen it by one clause; never insert into it.
7. `test_run39_launch_gate.py:786`, stopped by Run 59: it asserts the study governance defines no
   withdrawal state, and there is no non-markdown place that fact lives.
8. The specification sidecar's `controlling_status` still reads CONTROLLING, stopped by Run 59.
9. Two Run-34 fault-campaign artifacts now differ in content, not merely in churn.
10. The suite rewrites 26 committed artifacts each pass; the handoff still records 18.
11. The suite population is 203 (204 with this run's new suite).

---

## Provenance of this run

- Shared checkout `/home/user/LinPRojectRadar`; **no other run executing**, so no worktree was
  needed for the work itself. One throwaway worktree at `5f5cf60`
  (`…/scratchpad/run61/pre`) was used solely to run the pre-fix control, and nothing was written
  into it that the main checkout depends on.
- **Pinned tip `5f5cf60`**, named before any work began and used throughout. Branch
  `run61-caller-states-its-question` cut from it.
- Pre-fix control tip **`5f5cf60`** for the BEFORE renders; fixed tip **`2753a52`** for the AFTER
  renders and for every injection snapshot.
- Fixture: Run 60's preserved `PRJ-R60` / `PRJ-R60B` databases, four periods each, current period
  **4**, copied out of `stale.PRESERVED.sqlite3` before use. **`DATABASE_URL` was throwaway SQLite
  in the scratchpad at every step and never pointed at Postgres.** PRJ-001 and every synthetic
  corpus untouched. Nothing outside the repository root was deleted or moved.
- `git status --porcelain` checked before every commit and at both ends of the injection campaign.
  **`git add -A` and `git add .` were never run.**
- No user-facing control added, moved or removed.
