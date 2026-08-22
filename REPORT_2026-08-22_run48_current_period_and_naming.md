# Run 48: the detail page reads the current period, and the live naming instances

**Date:** 2026-08-22. **Repository:** the Linux clone at `/home/user/LinPRojectRadar` (the
Windows path was not used). **Interpreter:** the documented fallback, `python3` 3.11.15; this
clone carries no `.venv`, so `server/run_all_suites.sh` fell through to the interpreter on PATH,
which is what it is written to do.

**Branch:** `run48-current-period-and-naming`, rooted at `2d82b21`. **Stamp:** `sim-2026.08-v32`
(was `sim-2026.08-v31`). **Participant package:** `og-participant-2026.08-v17` (was v16).
**Suites:** 192 run, **14,513 / 14,513 checks, ALL SUITES GREEN.** **Freeze gate:** 15 blocker
classes, 0 blocked; the gate suite reports 34/34.

The naming authority sentence this run is measured against, quoted verbatim from
`NAMING_AUTHORITY.md:96`:

> **Never use a module id or number in user-facing text.** No "Cat 4", no "1.7", no "PH.2", no
> "A4.2". Groups and purposes only. The old "Cat N" scheme is retired along with the names.

---

## 1. How the current period is determined, and the code that does it

**The determination is the server's, and it is read out of the stored results themselves.**

`server/app/documents.py`, two new pure read functions:

* `_computed_periods(session, project)` selects `ComputedResult.period` where
  `project_id == project.id` **and `superseded_by IS NULL`**, and returns the sorted set. It is a
  read of the result table. It is not derived from the document table, it is not generated as a
  range, and it is not bounded by anything.
* `_latest_computed_period(session, project)` returns `periods[-1]` when that list is non-empty
  and **`None`** when it is empty.

`a_projectperiods` serves both, as two new read-only response fields: `computed_periods` (the
list) and `latest_computed_period` (the maximum, or `null`). **The per-period row shape is
untouched.** The first implementation added a `computed` key to each row of `periods`;
`test_period_number_picker.py:141` asserts that row shape by exact equality, so the key was
withdrawn and the information moved to its own field rather than change a contract this run has
no order to change.

`assets/js/detail.js`, `primeAndRefresh`, formerly `:1304`:

```js
async function currentPeriod(id, tok) {
  ...
  resp = await LinStore.postWithTimeout(
    { action: "projectperiods", id: id, session_token: tok }, 30000);
  if (!resp || resp.ok !== true) return null;
  const latest = resp.latest_computed_period;
  return (latest === null || latest === undefined) ? null : Number(latest);
}

async function primeAndRefresh(id, p) {
  ...
  const period = await currentPeriod(id, tok);
  if (period === null) return;                 // no computed period: keep the existing empty state
  if (currentRenderId !== id) return;          // the page moved on while the call was in flight
  resp = await LinStore.postWithTimeout(
    { action: "projectresults", id: id, period: period, session_token: tok }, 30000);
```

**Each of the three forbidden assumptions is refuted by a fixture, not by an argument**
(`server/tools/test_run48_current_period.py`, section 2, all built through the real routes):

| forbidden assumption | fixture | server's answer |
|---|---|---|
| the highest period number has results | `PRJ-R48-DOCS`: documents at 1, 2, 3; computed at 1, 2 | opens on **2**, not 3 |
| periods are contiguous | `PRJ-R48-GAP`: computed at 1 and 4, nothing at 2 or 3 | opens on **4** |
| there is a maximum period count | `PRJ-R48-HIGH`: computed at period 48 only | opens on **48** |
| a project always has a period to open on | `PRJ-R48-NONE`: documents at 1, never computed | `latest_computed_period` is **null**, `ok: true`, no error |

A superseded row is not a computed period: recomputing period 4 of `PRJ-R48-FOUR` through
`projectcompute` leaves `computed_periods == [1, 2, 3, 4]` and the opened period at 4.

**No control was added.** The detail page has no period selector and this run did not give it
one; the browser driver measured zero `select` elements under `#detail-root`. Hard limit 4 and
stop condition 9.1 did not fire.

---

## 2. Every panel found reading the results row, and confirmation each reads the selected period

Seven panels hold the row `primeAndRefresh` grafts, named in `detail.js`'s own
`REFRESH_SECTIONS` plus the badges recomputed beside them. Each was asked **separately, by name**
in the rendered DOM by `server/tools/drive_run48_browser.py` section 3, against a two-period
fixture built through the real routes whose two rows print different figures.

| panel (by its own heading) | body element | period-2 figures found in the DOM | period-1 figures found | verdict |
|---|---|---|---|---|
| Executive Brief | `#body-d-brief` | `2,000,000`, `1,500,000` | none | **reads period 2** |
| Governance Decision | `#body-d-decision` | `2,000,000`, `1,500,000` | none | **reads period 2** |
| Documents and Extracted Signals | `#body-d-docsignals` | `2,000,000`, `2,100,000`, `1,500,000` | none | **reads period 2** |
| Signal Inputs | `#body-d-ledger` | none | none | **not distinguishable from the DOM** |
| Signal Web | `#body-d-web` | none | none | **not distinguishable from the DOM** |
| Ensemble Analysis | `#body-d-ensemble` | none | none | **not distinguishable from the DOM** |
| Project Signal Network | `#body-d-projnet` | none | none | **not distinguishable from the DOM** |

**Stated plainly rather than claimed as a pass.** Four of the seven print no figure that differs
between the two periods, so the DOM alone cannot say which period they are showing, and the
driver prints exactly that line for each and does not count it as a pass. What IS true of them,
and is asserted: they read the row through `LinResults.rowFor`, and that row's `period` was read
back from the live page as **2**. Every panel that CAN be distinguished from the DOM shows period
2, and none of the seven prints a figure belonging only to period 1.

The eighth surface the order names, the **Run 47 disagreement findings**, is the strongest of the
checks because period 1 of the fixture has no finding at all: period 1's planned value agrees
with its own percentage (4,000,000 x 25.50 / 100 = 1,020,000, exactly as stated) and period 2's
does not (4,000,000 x 50.00 / 100 = 2,000,000 against a stated 1,500,000, a difference of 25.0
per cent of the implied value). A page still reading period 1 would render **no block at all**.
The block is present and its text, read verbatim out of the DOM, is:

> Figures stated in one document that do not agree with each other:
> In period 2, the Time-phased Schedule / Baseline states a planned value to date of 1,500,000
> and a planned percent complete of 50. Applied to the budget at completion of 4,000,000, that
> percentage implies a planned value to date of 2,000,000. The stated and implied figures differ
> by 25.0 percent. Both figures were read from the same document, and both are reported as the
> document stated them.

`recommendation_basis`, the key drivers and the abstention reasons all travel on the same grafted
row and are inside the Executive Brief and Governance Decision panels above.

---

## 3. Every hard-coded period literal found by the section 5.1 sweep

`grep -rn "period[\"']\?\s*[:=]\s*[0-9]" assets/js/*.js`, excluding comment lines, over the whole
client. Four live literals were found, in two files.

| site | literal | disposition | reason |
|---|---|---|---|
| `assets/js/detail.js:1304` | `projectresults ... period: 1` | **CORRECTED** | The site the order names. It is now the server-derived latest computed period. |
| `assets/js/decision-ui.js:345` | `projectresults ... period: 1` | **FOUND AND LEFT** | See below. |
| `assets/js/decision-ui.js:346` | `projectuploadstatus ... period: 1` | **FOUND AND LEFT** | See below. |
| `assets/js/decision-ui.js:545` | `projectresults ... period: 1` | **FOUND AND LEFT** | See below. |

`assets/js/workspace.js:640` carries the words `period: 1` inside a COMMENT recording why that
call site stopped sending a constant. It is not a live literal and was not touched.

**Why the three `decision-ui.js` literals were left, and what they actually govern.**

`decision-ui.js` is one of the six sequence-bearing files. Ruling 2 authorises editing
`deepdive.js` and names only `deepdive.js`, so moving a second sequence-bearing file is outside
this run's authority. That is the constraint. What those literals GOVERN was not assumed from
their names; it was **established by execution** and is section 8 of
`test_run48_current_period.py`:

* `decision-ui.js` addresses only `STATE.server.evidence_project_id`, which is a scenario's
  evidence package, i.e. a project inside the research chain.
* `documents._resolve_period` ignores the payload entirely whenever a research assignment exists
  and derives the period from `research_decision.current_period`.
* Executed: a project computed at periods 1, 2, 3 and 4, whose PM is a consented research
  participant holding an assignment with an unsubmitted decision at **P3**, answers
  `projectresults` with **period 3** for a request stating `period: 1`, answers
  `projectuploadstatus` with **period 3** for the same stated 1, and answers **period 3** again
  for a request stating `period: 4`.
* The same suite executes the operational control: on `PRJ-R48-TWO`, with no assignment, a stated
  `period: 1` really does serve period 1's row. That is precisely why the detail page's literal
  pinned it, and why removing it was the fix.

**The three literals are therefore INERT on the surface that carries them**, and they cannot make
the ordered detail-page fix ineffective: they are on a different surface, and the server overrides
them there. Stop condition 9.6 did not fire, because no second sequence-bearing file moved. The
question of whether they should nevertheless be removed is carried to the owner in section 11.

---

## 4. Every label before and after, and how each was verified

| site | before | after | verified |
|---|---|---|---|
| `deepdive.js` `CAT_FROM_MODULE` "01","02","03" | `Cat 1.1`, `Cat 1.2`, `Cat 1.3` | `Cost Performance` | **rendered DOM** |
| same, "04","05","06" | `Cat 2.1`, `Cat 2.2`, `Cat 2.3` | `Schedule Simulation` | not reached by this fixture; source-verified |
| same, "07","08" | `Cat 3.1`, `Cat 3.2` | `Cost Simulation` | not reached by this fixture; source-verified |
| same, "09" | `Cat 6.1` | `Signal Synthesis` | **rendered DOM** |
| same, "10".."18" | `Cat 7.1` .. `Cat 7.9` | `Evidence Combination` | not reached by this fixture; source-verified |
| same, "19" | `Cat 8.1` | `Governance and Compliance` | **rendered DOM** |
| same, the fallback | `"Cat " + key` | `Signal Analysis` | **rendered DOM** |
| `charts3d.js:2542` node label | `Synthesis\n(Cat 6)` | `Signal\nSynthesis` | **NOT verifiable from the DOM**; see below |
| `detail.js` brief prompt | `c.num + " " + c.name + ": " + c.status` | `c.name + ": " + c.status` | **NOT a DOM surface**; see below |

**What the rendered DOM actually returned**, verbatim, from
`http://127.0.0.1:<port>/research/deepdive.html` with the fixture project loaded through the
page's own control (63 `.dd-panel` elements rendered):

```
aria-labels (unique):
  Cost Performance deep dive
  Governance and Compliance deep dive
  Signal Analysis deep dive
  Signal Synthesis deep dive
headings (first five):
  Why COST PERFORMANCE (Hybrid Dynamic Simulation) is RED
  Why COST PERFORMANCE (Statistical Process Control (SPC) / Cumulative Sum Control Chart (CUSUM) Anomaly Monitor) is RED
  Why COST PERFORMANCE (Document-Risk Extraction) is GREEN
  Why SIGNAL ANALYSIS (Bayesian EAC) is AMBER
  Why SIGNAL ANALYSIS (Kalman Filter SPI Smoother) is AMBER
```

Asserted on that rendered text: no `Cat <digit>`, no ampersand, no em dash and no en dash.

**Two sites could not be verified from a rendered DOM, and that is said plainly rather than
claimed:**

1. `charts3d.js:2542` is a **canvas** renderer. The label is painted into a bitmap by
   `render_91`, so it has no DOM node and no accessible name to read back. It was verified in
   source only.
2. `detail.js`'s brief line is not rendered at all: it is assembled into the **prompt sent to the
   brief's model**. There is nothing in the DOM to read. It was verified in source, and
   independently by `test_run44_participant_defect_fixes.py`, which builds that prompt through
   the real function and now asserts the text reads `Cost and EVM Performance: Amber` with
   `A1 Cost and EVM Performance` absent.

**Two things about the deep-dive correction that a reader should not have to discover.** First,
the panel's GROUPING number used to be parsed back out of the displayed label
(`String(catRef).match(/Cat\s+(\d+)/)`), so correcting the text would silently have moved every
panel into a different collapsible group. It is now declared in its own map,
`CAT_NUM_FROM_MODULE`, and the DOM was read back panel by panel to confirm every module number
still buckets to the number the retired label parsed to: `01,02,03 -> 1`, `04,05,06 -> 2`,
`07,08 -> 3`, `09 -> 6`, `10..18 -> 7`, `19 -> 8`. Second, most panels on that surface pass keys
the map does not cover (`1.4`, `2.9`, `10.2-10.7`), so they take the fallback and now all read
**Signal Analysis** where they previously read `Cat 1.4`, `Cat 2.9` and so on. That is what
ruling 2 requires -- the fallback was ordered corrected -- but it costs specificity, and it is
raised as a decision in section 11 rather than resolved here.

---

## 5. The grep proving the label map was unread, and the assertion change

The constant deleted under ruling 3 was `BRIEF_CAT_LABEL` in `assets/js/detail.js:1724`.
`grep -rn "BRIEF_CAT_LABEL"` across the whole repository, before the deletion, returned the
definition and **no reader**. Restricted to code that could read it:

```
$ grep -rn "BRIEF_CAT_LABEL" assets/ index.html server/app/
assets/js/detail.js:1724:  const BRIEF_CAT_LABEL = {
```

Every other hit in the repository is prose or a guard's comment, and only ONE of them was a live
assertion. Reconciled, each named:

| file:line | what it is | action |
|---|---|---|
| `server/tools/test_run28_participant_packages.py:789` | a live check asserting the ten corrected labels are PRESENT | **CHANGED to require absence** (below) |
| `server/tools/production_tree.py:401` | a comment on the Run-47 manifest | unchanged; it is history |
| `server/tools/participant_packages.py:347` | the v16 package record's own prose | unchanged; a predecessor record is never rewritten |
| `server/tools/test_run2_fifteen_defects.py:1627` | a comment above the Run-47 line sets | unchanged; it is history |
| `server/tools/build_run47_candidate_identity.py:83` | Run 47's supersession reason | unchanged; it is history |
| `server/tools/build_run47_successor_release.py:180, :203` | Run 47's release text | unchanged; it is history |

That none of the five prose sites was load-bearing is not asserted from reading: only
`test_run28_participant_packages.py` turned red in the full run, and it is the only one changed.

**The assertion change, stated explicitly as section 5.3 requires.** Before:

```python
check('"Cost Performance (Cat 1)"' not in _det and '"Data Integrity (Cat 9)"' not in _det,
      "BRIEF_CAT_LABEL no longer prints a label carrying the retired scheme")
check('"Cat 1": "Cost Performance"' in _det and '"Cat 10": "Decision Optimization"' in _det,
      "and the ten labels are groups and purposes, ...")
```

After:

```python
check("BRIEF_CAT_LABEL" not in _det,
      "the dead category label map is ABSENT from detail.js: no declaration and no reference")
check('"Cat 1": "Cost Performance"' not in _det
      and '"Cat 10": "Decision Optimization"' not in _det,
      "and neither its corrected labels nor its retired keys survive anywhere in the file")
_det16 = git_bytes("assets/js/detail.js", V16_COMMIT).decode("utf-8")
check("BRIEF_CAT_LABEL" in _det16,
      "and it really was there to delete, so this is not a check that passes vacuously")
```

The third line is new and is there because an absence check is worthless without proof that the
thing was present to begin with.

**A SECOND check body had to change, and the order did not anticipate it. It is not a deletion.**
`test_run44_participant_defect_fixes.py:381` asserted the brief prompt contains
`"A1 Cost and EVM Performance: Amber"` -- the exact identifier ruling 2 orders out of that text.
It now asserts `"Cost and EVM Performance: Amber"` is present **and** `"A1 Cost and EVM
Performance"` is absent. The check keeps everything it had (it still fails if the category or its
status stops being reported) and gains a clause. No check was deleted, so stop condition 9.5 did
not fire, but the order authorised one check-body change and this run made two; the second is
recorded here rather than folded in silently.

---

## 6. Surviving live instances of the retired scheme after the second sweep

The re-sweep was executed over every file in `assets/js`, excluding comment lines. **The retired
scheme survives on rendered surfaces this run was not ordered to correct, and it is reported
rather than corrected**, which is what section 5.2 asks for. `deepdive.js` is the only file
affected.

Measured **in the rendered DOM** on `research/deepdive.html`, the ten collapsible group headers,
verbatim, built at `deepdive.js:2268` from `<span class="mod-mono">Cat ${n}</span>`:

```
Cat 1 Cost and EVM Performance            Cat 6 Delivery Quality Performance
Cat 2 Schedule Performance                Cat 7 Signal Synthesis
Cat 3 Cost Risk                           Cat 8 Evidence Combination
Cat 4 Document-Derived Condition Signals  Cat 9 Regulatory and Authority Thresholds
Cat 5 System Dynamics and Complexity       Cat 10 Decision Optimization
```

Also rendered, in source order:

| site | text |
|---|---|
| `deepdive.js:1059` | "The classification feeds Cat 8.1, which maps it to an action and an authority." |
| `deepdive.js:1404` | metric box label "Agrees with Cat 6.1" |
| `deepdive.js:1831, :1834, :1837` | three summary sentences naming "the Cat 6.1 baseline" and "the Cat 8.1 recommendation" |
| `deepdive.js:1841` | panel heading "Synthesis Methods Comparison: Cat 6.1 & Cat 7.1-7.9" -- also an ampersand and an en dash |
| `deepdive.js:1842` | note naming "Conservative dominance (Cat 6.1)" and "Cat 7.1-7.9" |
| `deepdive.js:2189` | the banner: "Cat 1-Cat 3 modules are quantitative signal generators. Cat 6.1 ... Cat 7.1-7.9 ... Cat 8.1 ..." -- en dashes throughout |

One further site reaches the brief's model rather than a screen: `detail.js:1741`, "a program
director does not think in Cat 1-12."

**Not the retired scheme, but the same authority:** `detail.js:1086` titles a section
`Documents & Extracted Signals`, an ampersand in user-facing text against `NAMING_AUTHORITY.md`.
Reported, not corrected.

**Deliberately untouched, and verified untouched** (`test_run48_current_period.py` section 7):
the comment markers at `app.js:1298-1299`, `categories.js:255, 355, 422`,
`deepdive.js:2168, 2192` (now `:2202, :2226`), `neural_flow.js:174` and `taxonomy.js:286`. They
record why a thing moved.

`method_class` identifiers such as `Doc_Risk_Cat4` and `DSM_Rework_Cat5`, and the function name
`renderCat8Health`, are code constants matched against and never displayed. The naming authority
says explicitly not to rename the code constants, so they were not touched.

---

## 7. Every section 6 guarantee, verified or not met, with the injection that proved its check could fail

Twelve fault injections were executed. The protocol on every one: inject, **re-read the file
bytes from disk to confirm the injection landed**, run, observe RED for the intended reason,
restore byte-identically from a pre-injection snapshot, re-run, and recheck the baseline. Suite
baseline 56/56; browser driver baseline 33/33.

| # | section 6 guarantee | verdict | the injection that proved the check can fail |
|---|---|---|---|
| 1 | computed at 1 and 2 opens on 2 | **verified** | I2 `_latest_computed_period` returns `periods[0]`: suite 45/52, "PRJ-R48-TWO: the page opens on 2" red with `[1]` |
| 2 | computed 1, 2 with documents at 3 opens on 2 | **verified** | I1 returns `_highest_period` instead: suite 48/52, "THE HIGHEST PERIOD NUMBER IS NOT ASSUMED TO HAVE RESULTS" red with `[3]` |
| 3 | computed 1-4 opens on 4 | **verified** | I2 as above: "PRJ-R48-FOUR: the page opens on 4" red with `[1]` |
| 4 | non-contiguous 1 and 4 opens on 4 | **verified** | I4 generates the computed list as `range(1, max+1)`: suite 50/52, "the gap project's computed periods are 1 and 4 with a hole between them" red with `[[1,2,3,4]]` |
| 5 | a period of at least 48 opens on it | **verified** | I4 as above: "the high project is computed at period 48 and nowhere else" red with the generated 1..48 list |
| 6 | no computed results renders the existing empty state, no error | **verified** | I3 returns 1 instead of None: suite 50/52, "a project with no computed result in any period returns null, not 1" red. I6 removes the `if (period === null) return;` arm: suite 51/52 red on that arm alone |
| 7 | every panel reads the same period in one render, **per panel by name** | **verified for the three panels the DOM can distinguish; NOT DETERMINABLE from the DOM for the other four** (section 2) | I5 restores `period: 1` in `detail.js`: browser 27/33, the primed row reads period **1**, the per-panel check red naming `Documents and Extracted Signals`, and the disagreement block **absent** |
| 8 | no hard-coded period literal survives on a read path | **verified for `detail.js`; three survive in `decision-ui.js`, established inert, and are reported rather than corrected** (section 3) | I5 as above: "assets/js/detail.js carries NO `period: 1` literal anywhere" red, quoting the reinstated line |
| 9 | no stored figure changes | **verified** | Not by injection but by construction and by census: every Run-48 change is on the read path, `_computed_periods` and `_latest_computed_period` only SELECT, and B15's behaviour digest -- 100 scientific targets executed through their real governed routes on the frozen corpus -- reproduces identically across the re-mint. `test_run6_known_answer.py` 488/488, `test_run45_period_scoping.py` 77/77, `test_run47_evm_consistency.py` 56/56 |
| 10 | no band, status, colour or posture changes | **verified** | Same evidence: B05 measures 100 served statements against executed behaviour and reports none failing; B06's census is `{ABSTAINS: 89, COMPUTES: 5, SUPPLIED_NOT_COMPUTED: 1, PORTFOLIO_ROUTE: 5}`; the gate reproduces from the tree |
| 11 | no user-facing text carries a module identifier, a category number, the retired scheme, an ampersand or an em dash | **NOT MET, and the survivors are enumerated in section 6** | I7 restores `"01": "Cat 1.1"`: suite 50/52 and browser 32/33, the DOM read back `Cat 1.1 deep dive`. I8 restores the `"Cat " + key` fallback: suite 50/52, browser 31/33. I9 restores the chart node label: suite 51/52. I10 restores `c.num` in the brief prompt: suite 51/52 |
| 12 | the deleted label map is absent from the tree | **verified for every served file; the name still appears in this run's own reports and in six historical tool comments** | I11 reinstates `const BRIEF_CAT_LABEL = {...}` in `detail.js`: suite 49/52, three checks red including "no served JavaScript file in the tree carries the constant" with `[['detail.js']]` |
| 13 | the comment markers of section 5.2 are unchanged | **verified** | Asserted per file by content in section 7 of the suite. No injection was run against these five; they are equality checks on strings the run never touched |
| 14 | modules in service 63, registry 101, both derived | **verified** | `len(service_index()) == 63`, `len(registry_index()) == 101`, both called live. Gate B02 measures the same populations independently and reports 0 |
| 15 | voting count is exactly 2, A1.7 and A1.8 | **verified** | `sorted(CORE_VOTING_MODULES) == ["A1.7", "A1.8"]`, called live; gate B09 reports the same list |
| 16 | the successor freeze gate passes in full | **verified** | 15 blocker classes, 0 blocked; `test_run37_freeze_gate.py` 34/34 |

**One additional guarantee, not in section 6, proved because section 7 requires it.** A second
sequence-bearing file moving without its own record must still turn the gate red. One byte was
appended to `assets/js/workspace.js`: B04 went to 1 and reported
`moved: ['assets/js/workspace.js']`, the gate suite fell to **27/34** with B01, B04 and B11
blocked, and the package suite failed five checks including the sequence-exception check, which
reported `['assets/js/deepdive.js', 'assets/js/workspace.js']` against a declared exception of
one. Restored byte-identically; `git diff --quiet` clean; gate 34/34 and package suite 138/138
again.

**A run incident, recorded because the honesty standard requires it.** The first injection pass
aborted inside injection I11 on a harness assertion, **after** writing the fault and **before**
restoring it, leaving one injected line in `detail.js`. A later baseline read 49/52 instead of
52/52, and a second interrupted pass left an injected line in `documents.py`, which a later
baseline caught at 45/52. Both were found by the baseline recheck the protocol mandates, both
were repaired by hand, and every injection reported in the table above was re-executed from a
clean 52/52 baseline with a restore that cannot be skipped. No injected byte reached a commit.

### The freeze gate, every row

| id | blocker class | count | required | verdict |
|---|---|---|---|---|
| B01 | dirty candidate identity | 0 | = 0 | **PASS** -- 11 content-addressed digests recomputed from the tree and compared |
| B02 | population mismatch | 0 | = 0 | **PASS** -- registered 101, project scientific 95, Portfolio Health 5, scientific 100 |
| B03 | controlled-stimulus mismatch | 0 | = 0 | **PASS** -- 6 projects x 6 periods, 36 unique combinations, 0 duplicates, 0 missing |
| B04 | participant-sequence drift | 0 | = 0 | **PASS** -- 6 sequence-bearing files compared against the v17 record; moved: none |
| B05 | false defensibility statement | 0 | = 0 | **PASS** -- 100 served statements measured against executed behaviour; failing: none |
| B06 | unexpected execution exception | 0 | = 0 | **PASS** -- census ABSTAINS 89, COMPUTES 5, SUPPLIED_NOT_COMPUTED 1, PORTFOLIO_ROUTE 5 |
| B07 | Category-9 bypass | 0 | = 0 | **PASS** -- no unqualified probe reaches a banded result; no C-group voter; group C does not contribute |
| B08 | Category-10 authority violation | 0 | = 0 | **PASS** -- human authorization required, creates no project evidence, no Category-10 identity votes |
| B09 | voting count is not exactly 2 | 0 | = 0 | **PASS** -- `CORE_VOTING_MODULES = ['A1.7', 'A1.8']` |
| B10 | current taxonomy dual authority | 0 | = 0 | **PASS** -- one authority, both mirrors trace to the generator, no failing runtime lookup |
| B11 | package or predecessor mutation | 0 | = 0 | **PASS** -- no rewritten predecessor record; no v17 file failing its record |
| B12 | browser qualification failure | 0 | = 0 | **PASS** -- 29 rows, none failing |
| B13 | unresolved blocking Run-36 defect | 0 | = 0 | **PASS** -- no open instrument-level defect |
| B14 | unsupported final empirical-validation claim | 0 | = 0 | **PASS** -- all 100 rows record NOT_EMPIRICALLY_FIELD_VALIDATED |
| B15 | candidate behaviour changed during the run | 0 | = 0 | **PASS** -- behaviour digest `8fb4d366...` over 100 executed targets |

Gate suite verdicts beyond the fifteen rows: the generator runs to completion; the committed gate
reproduces from the live tree; the v25 record still says v25; the v26, v27, v28, **v30 and v31**
successor records still say their own stamps (Run 48 added the last two to that loop, which
strengthens it); no release record exists while a blocker stands; the limitation contract states
0 of 100 empirical validation, denies validated real-world predictive effectiveness, states
OG-SYNTH-0.1's historical incompleteness and states bounded controlled-study qualification; the
disposition is FINAL_FREEZE_ACCEPTED; and the record names Run 47's candidate
`0f46551d5c2d99e15a6a4d2f036938e823691b48` as its parent and not itself. **34/34.**

---

## 8. The `deepdive.js` exception record, and the other five sequence-bearing files

The six sequence-bearing files were verified from `server/tools/participant_packages.py`
`SEQUENCE_BEARING_FILES` before anything was edited: `assets/js/decision.js`,
`assets/js/decision-ui.js`, `assets/js/workspace.js`, `assets/js/deepdive.js`,
`assets/questionnaires/intake.json`, `assets/questionnaires/debrief.json`.

**The exception record**, declared by name in `participant_packages.py` rather than left for a
checksum to discover:

```python
V16_TO_V17_CHANGED = ("assets/js/charts3d.js", "assets/js/deepdive.js", "assets/js/detail.js")
V16_TO_V17_SEQUENCE_EXCEPTION = ("assets/js/deepdive.js",)
```

with the v17 package record stating, in the `Package.why` field and in the header of
`code_audit/run48_participant_package_v17_checksums.sha256`, exactly what moved inside it: the
map from a legacy module number to the panel's displayed label, its fallback, and the separation
of the panel's grouping number from the displayed text. Nothing else.

**Confirmation that the other five are unmoved**, measured three independent ways:

* `test_run28_participant_packages.py`: `_seq17` -- the sequence-bearing files whose live hash
  differs from the v16 record -- equals exactly `V16_TO_V17_SEQUENCE_EXCEPTION`, and the other
  five hash identically to v16. 138/138.
* Gate **B04**: 6 sequence-bearing files compared against the `og-participant-2026.08-v17`
  record, `moved: none`.
* The injection above: appending one byte to `workspace.js` turns both red.

Inside the exception, measured rather than asserted: `<button`, `<input`, `<select`, `<textarea`
and `data-run-portfolio-analysis` occur exactly as many times as in v16, and the whole-word counts
of `submitPreliminary`, `reveal` and `lock` are unchanged. No control moved and no sequence step
was touched.

The v16 record is **pinned** to commit `2d82b21`, not regenerated, and the suite asserts its bytes
in the tree are byte-identical to what that commit wrote.

---

## 9. Audit artifacts the suites rewrote, and were restored

**Eighteen**, exactly as Run 45 and Run 47 recorded: seventeen under `code_audit/` plus
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

All eighteen restored with `git checkout --` after each of the three full runs, and after each
single-suite run that touched them. **None was committed.** `git add -A` and `git add .` were
never used; every `git add` named its paths explicitly.

`test_run22_production_tree_completeness.py` behaved exactly as the order predicted: red inside
the runner on the first pass, green standing alone, and green in the runner once the pinned
manifest was reconciled.

**Two audit files this run WROTE deliberately, and committed:**
`code_audit/run48_production_tree.sha256` (244 files; the guard was observed reporting exactly
five CHANGED and nothing added or removed before it was written) and
`code_audit/run48_participant_package_v17_checksums.sha256` (70 files).

---

## 10. Incidental findings, unacted

1. **The deep-dive grouping is mismatched to the group names it files panels under, and has been
   since before this run.** Module `09` (Conservative Dominance, a synthesis method) buckets to
   `data-cat="6"`, and `groupByCategory` labels bucket 6 from `LIN_CATEGORIES[5]`, which is
   **Delivery Quality Performance**. Module `19` (Agent-Based Governance) buckets to 8, labelled
   **Evidence Combination**. The bucket numbers are the retired scheme's, the header names are the
   current gapless taxonomy's, and the two do not describe the same thing. Run 48 preserved the
   existing bucketing exactly, because changing it would move panels; the mismatch is reported. It
   is also the reason the corrected panel labels do not simply reuse the group header names.
2. **`research/deepdive.html` renders only for a project carrying the LEGACY client-side signals
   blob** (`signals.evm`, `signals.cusum`, `signals.mc`, `signals.doc`). The document pipeline does
   not write that blob; the browser driver had to supply it through the real `save` route, using
   the `signals` block captured in `p0-baseline/contracts/get/get.json`. A project computed
   entirely through `projectupload` and `projectcompute` shows "Awaiting analysis: no signal
   inputs yet." on that surface.
3. **The captured baseline's own `signalInputs` are refused by the live write path**
   (`environmentalComplianceRate` 78.8 against a bound of 1). Only the `signals` block was used.
4. **Run 47's handoff entry was appended at the BOTTOM of `T6_HANDOFF.md`** (line 12904), against
   that file's own stated rule that new sections go at the top, newest first. Run 48's entry is at
   the top. Run 47's is left where it is; moving it would rewrite history.
5. **A suite whose body is wrapped in `try/finally` with `sys.exit` in the `finally` swallows its
   own traceback** and prints a clean RESULT line one check short. This bit `test_run48` during
   development; that suite now has an `except BaseException` arm that counts a raise as a failure
   and prints the traceback. The same shape exists in `test_run47_evm_consistency.py` and is
   untouched.

---

## 11. What the next session needs, stated as decisions for the owner

1. **The three `period: 1` literals in `decision-ui.js`.** Established by execution to be inert:
   that surface only ever addresses a research project, and the route derives the period from the
   assignment and ignores the payload entirely. They were left because `decision-ui.js` is
   sequence-bearing and ruling 2 authorised only `deepdive.js`. **Decide:** remove them as dead
   constants under a named exception record, or leave them and record in the file itself that the
   server overrides them?
2. **The surviving rendered instances of the retired scheme in `deepdive.js`** -- the ten
   collapsible group headers, the banner, the metric-box label and five prose sentences, all
   enumerated in section 6 with their line numbers, plus the en dashes and the ampersand they
   carry. `deepdive.js` is sequence-bearing, so each correction is a further sequence-bearing
   edit. **Decide:** correct them in one further authorised pass, or leave them?
3. **The fallback label on the deep-dive panels.** Most panels on that surface pass a key the map
   does not cover and now read **Signal Analysis** where they read `Cat 1.4`, `Cat 2.9` and so on.
   The identifier is gone as ordered, but so is the distinction between them, and the panel
   heading now repeats one phrase across roughly sixty panels. **Decide:** accept the neutral
   fallback, extend the explicit map to every key the call sites actually pass, or take the label
   from the group the panel is filed under, noting incidental finding 1 before choosing the third.
4. **`Documents & Extracted Signals`** at `detail.js:1086` is an ampersand in user-facing text.
   One-token fix, not ordered here. **Decide:** schedule it, or leave it.
5. **Whether the four panels that print no period-distinguishing figure should state their
   period.** Section 2 records that the DOM cannot establish which period Signal Inputs, Signal
   Web, Ensemble Analysis and Project Signal Network are showing. They read the same grafted row,
   but nothing on those surfaces says so to a reader. **Decide:** is that acceptable, or should the
   reporting period appear on the panels that hold the row? Note that this would be text, not a
   control.

---

## Carried forward, unacted, so they are not rediscovered

1. **The `historical_data` triple** -- Run 47's only unimplemented relation.
   `analogous_overrun_pct` together with `similar_project_bac` and `similar_project_final_cost`
   determine each other against the REFERENCE project's budget at completion, not this project's.
   It awaits a ruling on whether "a known BAC" means this project's or any the same document
   states.
2. **`signal_inputs.sources` records no source field name**, so a finding cannot say which cell of
   a document a figure came from.
3. **Four status comparisons remain case-sensitive**, two of them in `decision.js`.
4. **Two Run 45 census artifacts do not match the v30 release manifest**, checksummed before their
   final bytes landed.

---

## The commit chain

| commit | what |
|---|---|
| `2d82b21` | `main` at the start of the run |
| `57c66f5` | Run 48: the detail page reads the current period, and the live naming instances |
| `8cca3f4` | Run 48: the successor freeze artefacts for `sim-2026.08-v32` |
| `e3d1b69` | Run 48: declare `sim-2026.08-v32` and `og-participant-2026.08-v17` in the four version-boundary and identity guards |
| `cdf5540` | Run 48: re-mint the candidate identity onto the reconciled guards |

Candidate identity digest `3d1bdd938eb2ba1b3e2c9b08c895e4328295c630cf84a36b270b18e0bead2637` at
candidate `e3d1b698b4797bb0fad4bde413317e56ecfd2398`, superseding Run 47's candidate
`0f46551d5c2d99e15a6a4d2f036938e823691b48` and `sim-2026.08-v31`. Behaviour digest
`8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1` over 100 executed scientific
targets, **identical before and after the re-mint**, which is the point: the guards moved, the
instrument's behaviour did not. Release content digest
`2e168123aad53f11bd77bac9f699adfe073fcabd249f348b0ee671374f1bb2ac`.

**Browser sessions.** Both were run from a clean subdirectory,
`/tmp/.../scratchpad/run48work/clean`, never the scratchpad root, and the driver printed that cwd.
The DEng\Demo tell was checked before anything else was measured: 7 `.page` sections, and neither
`api.js` nor `boot.js` in `document.scripts`. Final driver result: **33/33**.
