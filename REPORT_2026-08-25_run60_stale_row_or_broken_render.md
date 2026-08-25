# Run 60 — Do the fixes reach the page, or only reach new rows?

## 1. The answer, in the first three sentences

**The answer is a per-field split, and two of the nine rows are explanation 2: a defect in the render path that ten runs of browser verification could not have caught.** Rows 3, 4, 6 and 7 are render-side and corrected a pre-fix stored row immediately, with no recompute — those fixes work and reach the page; row 5 is half-corrected; row 8 is compute-side; row 9 was never fixed and still renders. **Rows 1 and 2 are NOT corrected: on the page the user actually gets, the provenance line is built from a DIFFERENT PERIOD'S module list than every other panel on the page, so it names a Green module as the driver and conceals a Red one — and it renders identically on pre-fix code and on current code, which is the definition of a fix that does not reach the page.**

A fourth finding sits underneath all of this and changes what you should do: **`projectcompute` on an unchanged document set writes nothing at all.** Step 5.3 produced a stored-row diff of ZERO. You cannot refresh a stale row by pressing "Generate signals for every period"; the server answers `computed: 0, skipped: 4, "documents unchanged since last computation; result left untouched"`.

And when the row IS genuinely rewritten by current code, **almost nothing in it changes**: of the whole stored row, only `simulation_version` and four identity fields (`baselineStart`, `baselineEnd`, `baselineContractSum`, `revisedContractSum`) differ. CPI, SPI, PV, EV, AC, `docRiskScore`, `project_status`, `category_statuses` and every module's `status_color` are byte-identical to what pre-fix code wrote. **Ten runs of fixes changed essentially nothing that is stored. Every one of the nine symptoms is a render question.**

---

## 2. The tree at the start, and every premise found false

### Repository, worktree, interpreter

Worked in an **isolated git worktree** at `/home/user/LinPRojectRadar/.claude/worktrees/agent-a34d9e99e4e30a095`, not in the main checkout. This was necessary because the experiment requires checking out the pre-fix commit `604291a`, and Run 59 was executing concurrently in `/home/user/LinPRojectRadar` and moving branches there. A checkout in the shared tree would have destroyed Run 59's work. Nothing was written to the main checkout.

Interpreter: `python3` **3.11.15**. `ls -d .venv` -> `No such file or directory`. The documented fallback was used, with `PYTHONIOENCODING=utf-8` set for every run.

### The starting state, and the premise that moved

At dispatch (`2026-08-25 15:05:40 UTC`):

```
git status --porcelain      -> (empty)
HEAD                        -> f4c1dbfddde280f2856c539f2ed7120be189e316
main == origin/main         -> f4c1dbfddde280f2856c539f2ed7120be189e316
```

**Section 3's premise `main == origin/main == f4c1dbf` was TRUE when I started.** I pinned **`f4c1dbf`** as "the current tip" and used that one commit throughout, rather than tracking a moving reference.

**That premise then became FALSE during the run.** At `15:30:28 UTC`:

```
main == origin/main -> 5f5cf60ad6b510f7d44b88e64bc669eaa4601f3e
5f5cf60  Run 59: NO MARKDOWN DOCUMENT CARRIES AUTHORITY. sim-2026.08-v39, ... 203 suites ALL GREEN.
```

Run 59 merged mid-experiment. **This does not invalidate anything**, and I checked rather than assumed:

```
git diff f4c1dbf 5f5cf60 -- assets/js/detail.js assets/js/taxonomy.js \
                             assets/js/workspace.js assets/js/categories.js \
                             assets/js/knowledge.js  | wc -l
-> 0
```

**All five files every finding in this report rests on are byte-identical between my pinned tip and the new `main`.** Run 59 touched six other files and moved the stamp `sim-2026.08-v38` -> `sim-2026.08-v39`. Every finding below holds at `5f5cf60`.

### Other premises checked

| Premise | Result |
|---|---|
| Stamp lives in `server/app/simulation/models.py` | **TRUE** — `SIMULATION_VERSION = "sim-2026.08-v38"` at line 718 |
| `registry_index()` = 101, `service_index()` = 63 | **TRUE** — printed by the driver at run time |
| `CORE_VOTING_MODULES = ['A1.7','A1.8']` | **TRUE** — `frozenset({'A1.8','A1.7'})` |
| `assets/js/deepdive.js` deleted by Run 54 | **TRUE** — absent from the tree |
| No `.venv`; `python3` is the fallback | **TRUE** |
| `signal_inputs.sources` records no source field name | **PARTLY FALSE, and the correction matters.** `sources` records **no field name within the document**, but it DOES record a **`docType` per field**, plus `documentId`, `documentVersion` and `asOf`. That is enough to answer section 9's open question mechanically — see section 10.5. |
| Schema differs between pre-fix and current | **FALSE — and this was load-bearing.** `git ls-tree` of `server/alembic/versions` at `604291a` vs the working tree differ only by a `.gitkeep`. **No migration was added between pre-fix and current**, so a database written by pre-fix code is read by current code with no migration at all. That is what makes this experiment possible. |

---

## 3. Which commit I took as pre-fix, and why

**`604291a5878b16f1770bd424158a1659c7941ce8` — "Run 43J: render defect diagnosis".**

The choice is **not** under-determined, and here is the rule that fixes it:

1. `git rev-parse e6889ad^` -> `604291a`. `e6889ad` is *"Run 44: the participant-facing render defects"*, the **first commit of the first fix**. `604291a` is therefore the last commit before any of the nine fixes existed.
2. `git show --stat 604291a` shows it adds **only two files**, a report and a CSV (`REPORT_2026-08-22_run43J_render_defect_diagnosis.md`, `code_audit/run43J_in_service_abstentions.csv`). It changes **no production code**, so its tree is the production tree of `405f3d3` (*Merge Run 43*).
3. It is the commit at which Run 43J **diagnosed the owner's render**. It is literally the tree the render was taken against.
4. Every one of the nine fixes (Runs 44, 45, 47, 48, 51) lands after it.

**Non-vacuity — I proved the defects are actually present in that tree before using it:**

```
assets/js/detail.js:266   const order = { Red: 0, "Red-review": 1, Amber: 2, ... }   (no lowercase key)
assets/js/detail.js:1546  const order = { Red: 0, ... }                              (the second copy)
assets/js/detail.js:1528  const docScore = Number(s.doc && s.doc.score != null ? ... : si.docRiskScore);
assets/js/detail.js:1447  const score = Number(s.doc.score);
assets/js/detail.js:1267  { action: "projectresults", id: id, period: 1, session_token: tok }
assets/js/knowledge.js:585 "...the project's 96 registered modules in milliseconds..."
grep -c 'modDrives' assets/js/detail.js -> 0
```

All six pre-fix defects present. The pre-fix tree is genuinely pre-fix.

---

## 4. The fixture, and the command that built it

Built **on `604291a`**, through the **real routes only** — `researchlogin`, `adminparticipantcreate`, `adminmemberadd`, `projectupload`, `projectcompute`. Extraction is stubbed (`StubExtractor`), the one substitution every suite in this repository makes; everything downstream of it is the production path.

Database: throwaway SQLite in the scratchpad, migrated with `alembic upgrade head` on pre-fix code. **`DATABASE_URL` never pointed at Postgres.** The PRJ-001 document set and every synthetic corpus were left untouched — the fixture is new projects with new documents.

```bash
export DATABASE_URL="sqlite:///.../run60/db/stale.sqlite3"
export SESSION_SECRET=...  PYTHONIOENCODING=utf-8
cd <worktree>/server && python3 -u -m alembic upgrade head
cd <scratchpad>/run60/drive && python3 -u ../fixture.py     # run from a clean subdirectory
```

### Two projects, four reporting periods each

**`PRJ-R60`** carries the owner's figures. Period ends `2026-03-31`, `04-30`, `05-31`, `06-30`. BAC 4,000,000. At period 4: EV 2,440,000 / AC 2,000,000 / PV 1,921,260, giving **CPI 1.220 and SPI 1.270** — the owner's numbers exactly.

**`PRJ-R60B`** exists for one reason: its SPI history is flat at 1.00, so A1.2 CUSUM does **not** breach and stores the **lowercase `'green'`** Run 44 named, beside a properly-cased Green TCPI and Green VAC. That is symptom 1's exact configuration.

**Document types — 27 of the 27 the platform supports**, including all four the owner's render shows (Contract Value, Pay Application, Monthly Progress Report, Time-phased Baseline). 36 documents on `PRJ-R60`, 9 on `PRJ-R60B`.

**No document states a `document_risk_score` anywhere.** Deliberate: it reproduces the "Document risk 0.00 (Green) with nothing stored" symptom at its source, by leaving `docRiskScore` present-and-null in the stored row.

### What pre-fix code actually stored

```
PRJ-R60  P4: cpi=1.22  spi=1.27  doc=None  status=Green  ver=sim-2026.08-v28
             colors={'A1.2': 'red',   'A1.7': 'Green', 'A1.8': 'Green'}
PRJ-R60B P4: cpi=1.053 spi=1.0   doc=None  status=Green  ver=sim-2026.08-v28
             colors={'A1.2': 'green', 'A1.7': 'Green', 'A1.8': 'Green'}
```

`simulation_version = sim-2026.08-v28` — the pre-fix stamp. **This is a genuine stale row**, and `PRJ-R60B` reproduces Run 44's lowercase-`green`-beside-capitalised-`Green` case exactly.

### Preservation and the contamination guard

The database was copied to a **read-only** `stale.PRESERVED.sqlite3` (`chmod 444`) before anything rendered it, and 5.2 ran against a separate working copy. After the 5.2 render I re-dumped the live `computed_results` rows and diffed them against the pre-render dump:

```
IDENTICAL: the 5.2 render wrote nothing to computed_results
```

**5.2 was recorded on an uncontaminated stale row, in a browser, before anything recomputed.**

---

## 5. The 5.2 table — the stale row rendered under current code

Chromium at `/opt/pw-browsers/chromium-1194/chrome-linux/chrome` by explicit `executable_path`, args `--use-gl=swiftshader --no-sandbox --headless=new`, `python3 -u`, driver run from a clean subdirectory whose cwd is printed. Read from the **rendered DOM** (`innerText`, plus `svg text` nodes and `aria-label`s), never from the JSON the server returns.

**The application under test is the right one — the `DEng\Demo` tell, measured:**

```
.page sections in the DOM            : 7        (expected 7)
api.js / boot.js in document.scripts : []       (expected absent)
window.LinDetail present             : True
registry 101   in service 63         : as expected
page errors                          : 0
```

Not `DEng\Demo`. The measurement is of the real application.

### PRJ-R60, stale row, current code

| Field | What the page shows at 5.2 |
| --- | --- |
| Reporting period (head line) | **blank** — `Reporting period:  ·` |
| Period the page actually holds | **4** (correct — `projectperiods` -> `projectresults period=4`, captured on the wire) |
| Key Drivers | `CPI: 1.220 (Green)` · `SPI: 1.270 (Green)` — **and nothing else** |
| Document risk | **absent** from Key Drivers |
| CPI / SPI labelling | ledger heading is **"Signal inputs"**; rows read `CPI (computed)`, `SPI (computed)` |
| Project status + attributed driver | `Green, driven by Cost and EVM Performance -> **TCPI**` |
| Provenance hops | `Project: Green` / `Cost and EVM Performance: Green` / `TCPI: Green (tied with 1 other module...)` |
| Category statuses (stored, held) | `A1: Green` (module_count 2, voting A1.7+A1.8, conflict 0.0) |
| Module status_colors on the held row | `A1.2='red'`, `A1.7='Green'`, `A1.8='Green'` |
| Panel populations | Project Signal Network `11 in service` · Signal Flow `63 in service` · Signal Web `63 in service` · Documents `36 docs · 12 fields` · Ensemble `3 active · 0 est.` |
| Module identifiers rendered anywhere (DOM + SVG + aria) | **0** |
| Signal Flow body | "63 REGISTERED PROJECT MODULES / **3 WITH A CURRENT RESULT** / 60 with no current result" |
| Signal Pattern | `GREEN (1 category): **Cost and EVM Performance**` (a name, not `A1`) |
| "All required values present. Nothing outstanding" | **PRESENT** |
| Handbook | "101 registered modules ... of which 63 are in service" |
| `consistency_findings` block | absent (not exercised by this fixture — see section 10.8) |

**The line to look at is the driver.** The held row says `A1.2 = 'red'`. The page names **TCPI, which is Green**, and never mentions the Red module.

### PRJ-R60B, stale row, current code

Identical in shape. Held row `A1.2='green'` (lowercase) beside `A1.7='Green'`, `A1.8='Green'`; page renders `Green, driven by Cost and EVM Performance -> TCPI`, `CPI: 1.053 (Green)`, `SPI: 1.000 (Green)`, no Document risk, 0 module identifiers, "All required values present" present.

### The control that makes this readable — the SAME stale row on PRE-FIX code

This is the counterfactual: the render you saw. Same database file, same browser, same driver; only the checkout differs.

| Probe | PRE-FIX `604291a` | CURRENT `f4c1dbf` (5.2) | |
| --- | --- | --- | --- |
| Document risk key driver | **`Document risk: 0.00 (Green)`** | **absent** | DIFF |
| Ledger heading | **`Extracted signal inputs`** | `Signal inputs` | DIFF |
| CPI / SPI ledger rows | `CPI (computed)` / `SPI (computed)` | same | same |
| Signal Pattern naming | **`GREEN (1 category): A1`** | `...: Cost and EVM Performance` | DIFF |
| Signal Flow badge | **`63 registered`** | `63 in service` | DIFF |
| Module identifiers rendered | **63** (`A1.2 ... C1.7`) | **0** | DIFF |
| head `Reporting period:` | blank | blank | **SAME** |
| `All required values present` / `Nothing outstanding` | present | present | **SAME** |
| provenance driver | `driven by Cost and EVM Performance -> TCPI` | identical | **SAME** |

---

## 6. The 5.3 table — after `projectcompute` for every period

Same database, same current code. `projectcompute` was run for periods 1-4 on both projects. All eight calls returned `ok: True`.

**Every field in the 5.2 table is unchanged at 5.3. Every single one.** Provenance line still `-> TCPI`; head reporting period still blank; Document risk still absent; module identifiers still 0; "All required values present" still present; badges identical; Key Drivers identical.

**The reason is the finding.** The rows still carry `sim-2026.08-v28` after the recompute, and the stored-row diff is empty:

```
=========== 5.1 stale  vs  5.3 after projectcompute ===========
IDENTICAL - projectcompute wrote nothing at all
```

`projectcomputeall` answers, verbatim:

```json
{"period": 4, "computed": false, "skipped": true,
 "note": "documents unchanged since last computation; result left untouched"}
... "computed": 0, "skipped": 4
```

The rule is at `server/app/documents.py:2563-2569` in `a_projectcompute`, resting on `_period_is_stale` (`documents.py:1065-1090`), which compares the set of `(document_id, sha256)` pairs on the stored result against the period's current live document set. Unchanged documents => nothing is written.

**So step 5.3 as the order specifies it is, on this platform, a no-op.** To obtain a row genuinely written by current code I additionally ran the **`resetsignals`** route and then `projectcompute` — reported in section 9, and kept in a *separate* database copy so the 5.2 artefacts were not disturbed.

---

## 7. The per-field classification — all nine rows of section 6

Classified **individually**, as section 7.4 requires. "Side" is what I established by execution, not what the order assumed.

| # | Symptom | Fix | Side | 5.2 | 5.3 | Verdict |
|---|---|---|---|---|---|---|
| 1 | A1 Amber while TCPI and VAC Green — lowercase status falling to unknown rank | Run 44 `statusRank` | **RENDER** | **not corrected** | **not corrected** | **DEFECT — explanation 2** |
| 2 | Status attributed to a module that does not drive it | Run 44 `modDrives` | **RENDER** | **not corrected** | **not corrected** | **DEFECT — explanation 2** |
| 3 | `Document risk: 0.00 (Green)` with nothing stored | Run 44 null guard | **RENDER** | **corrected** | corrected | **works, reaches a stale row** |
| 4 | CPI and SPI labelled "extracted" when computed | Run 44 / naming | **RENDER** | **corrected** | corrected | **works, reaches a stale row** |
| 5 | Blank reporting period; longitudinal locked with four periods | Run 48 `period: 1` | **RENDER** | **SPLIT** | same | **half works** |
| 6 | Signal Flow declaring 96 registered modules | Run 51 literal -> derived | **RENDER (client constant)** | corrected at source | same | **works** (source evidence; caveat below) |
| 7 | Retired modules drawn on the visual surfaces | Runs 43H / 51 | **RENDER (client taxonomy)** | **corrected** | corrected | **works, reaches a stale row** |
| 8 | PV understated by 24%, CPI 1.22, SPI 1.27 | Run 45 identity; Run 47 consistency | **COMPUTE** | not corrected (cannot be) | **not corrected either** | **compute-side, and unreachable by recompute** |
| 9 | "All required values present. Nothing outstanding" while most modules abstain | not fixed | — | renders | renders | **not fixed — confirmed live** |

### Row by row, with the evidence

**Rows 1 and 2 — the defect. Section 8 names it in full.** The rendered provenance line is **byte-identical on pre-fix code and on current code**: `Green, driven by Cost and EVM Performance -> TCPI`. On a row whose `A1.2` is `'red'`, the page names a Green module as the driver and does not mention the Red one anywhere. Run 44's fixes are real and correct code; this path never reaches them with the right data. Note also that the provenance line ranks through `provRank` (`detail.js:820`), which normalises case via `normalizeStatus` and therefore was *already* case-insensitive — so Run 44's `statusRank` fix does not touch this line at all.

**Row 3 — corrected, and demonstrably.** Pre-fix rendered `Key Drivers ... Document risk: 0.00 (Green)`. Current code renders `CPI` and `SPI` and stops. The same stored row, the same null `docRiskScore`. Measured in the browser on both trees. The guard at `detail.js:1666-1670` tests the **raw** value for null/blank rather than the number for finiteness, so a genuine stored zero would still print. Render-side, corrects a stale row with no recompute.

**Row 4 — corrected.** Pre-fix the ledger heading read **"Extracted signal inputs"**, over rows that include computed indices. Current code renders **"Signal inputs"**, and CPI/SPI carry `(computed)` in both trees. The false "extracted" framing is gone. Render-side, corrects a stale row.

**Row 5 — a genuine split, and the half that is still broken is the half you look at.**
- *Corrected:* the page now opens on the right period. Captured on the wire: `{"action":"projectperiods","id":"PRJ-R60"}` followed by `{"action":"projectresults","id":"PRJ-R60","period":4}`. The row it holds is period 4.
- *Not corrected:* the head line still renders `Reporting period:  ·` — **blank, in both trees**. It reads `p.reportingPeriod` (`detail.js:1044`), a project-document field which is `None` for every server-computed project. Run 48 fixed which row the page fetches; it did not give that head line a value, and nothing else has.
- A third panel renders `Reporting period: 2026-08` — the wall-clock month, not the period being displayed. Reported, not acted on.

**Row 6 — corrected at source; rendered form not reached.** At `604291a`, `knowledge.js:585` reads `"the project's 96 registered modules"`. At `f4c1dbf`, `knowledge.js:628` reads `"the ${taxCounts().inService} modules in service"` — derived, not typed. The only surviving `96 registered` in the file is inside a comment describing the historic defect. **Honest caveat: that particular article did not appear in the handbook text my capture reached, in either tree, so I did not observe the string change on a rendered page.** The handbook text I did capture says "101 registered modules ... of which 63 are in service" in **both** trees, so the rendered count was already correct at pre-fix. Source-level evidence only.

**Row 7 — corrected, and this one is stark.** Pre-fix, the rendered page carried **63 module identifiers** across its DOM text, SVG `<text>` nodes and `aria-label`s — `A1.2, A1.3, ... C1.7`. Current code renders **zero**. The Signal Flow diagram now draws module *names*. This is a client-taxonomy fix: it depends on no stored row at all, so it corrects a stale row trivially and completely.

**Row 8 — compute-side, and `projectcompute` will not deliver it.** CPI 1.220 and SPI 1.270 are what the documents state; current code recomputes them to the same values. The Run 45 identity carry-forward IS a real stored-data improvement (section 9), but it is invisible until the row is rewritten, and `projectcompute` refuses to rewrite it. Run 47's `consistency_findings` is derived **at read time** (`documents.py:1817-1826`), so it *would* reach a stale row — but my fixture states no figure that disagrees with itself above tolerance, so **no finding was produced and this branch is untested by this run**. Reported as unexercised, not as working.

**Row 9 — not fixed, confirmed on the rendered page in all three renders.** "All required values present. Nothing outstanding" renders on `PRJ-R60` while the same page's Signal Flow panel says **"3 modules with a current result, 60 with no current result"**. Two statements in direct contradiction, on one screen, in one scroll.

---

## 8. Explanation 2, in full — the defect for rows 1 and 2

### 8.1 The file and line that reads the stored row on the render path

```
assets/js/taxonomy.js:446-453     function rowFor(project)
assets/js/taxonomy.js:485-498     window.getModuleStatus(methodClass, project)   <- reads rowFor()
assets/js/detail.js:851-905       buildProvenanceTrace(project)                  <- calls getModuleStatus
assets/js/detail.js:1047          ${populated ? provenanceLineHtml(p) : ""}      <- inside render()'s innerHTML
assets/js/detail.js:1380          LinResults.prime(id, resp.result)              <- inside primeAndRefresh, AFTER
assets/js/workspace.js:989        period: p.period || 1                          <- primes the PERIOD 1 row
assets/js/workspace.js:796, :993  LinResults.prime(...) call sites
```

### 8.2 What it reads, and why the fix does not reach it

`rowFor` (taxonomy.js:446):

```js
function rowFor(project) {
  var k = keyOf(project);
  var primed = k ? (ROWS[k] || null) : null;
  var stored = (project && project.storedResult) || null;
  if (stored && primed && !stored.module_results && primed.module_results) return primed;
  if (stored) return stored;
  return primed;
}
```

Measured sequence, on the real load path, with `LinResults.prime` wrapped by an **init script** installed before any application script ran (so nothing is missed), and sampled at 0/50/150/400/1000/3000/8000 ms after `render()`:

1. **At page load, before any detail render**, `workspace.js:993` (inside `renderPortfolio`, requesting `period: p.period || 1` at line 989) and `workspace.js:796` prime `ROWS['PRJ-R60']` with the **PERIOD 1** row — captured stacks: `at v.prime | at renderPortfolio (workspace.js:988) | ... workspace.js:993`. That row's modules are `['A1.7=Green', 'A1.8=Green', 'A4.3=Yellow']`.
2. `project.storedResult` is the `a_get` **projection**. Its keys, measured: `['result_id', 'period', 'project_status', 'category_statuses']` — period **4**, and **no `module_results`**.
3. `render()` runs. `rowFor` takes the third branch — `stored` has no `module_results`, `primed` does — and returns the **PERIOD 1** row. `getModuleStatus('CUSUM')` therefore returns **`'NODATA'`**, because period 1 has no A1.2 at all. `buildProvenanceTrace` sees only `A1.7=Green` and `A1.8=Green`, and names **TCPI**.
4. At about **+1000 ms**, `primeAndRefresh` (`detail.js:1380`) primes the **period 4** row. `rowFor` now returns `['A1.2=red', 'A1.7=Green', 'A1.8=Green']` and `getModuleStatus('CUSUM')` returns **`'red'`**.
5. **The provenance line is never rebuilt.** Sampled at +3000 ms and +8000 ms: still `-> TCPI`. `refreshSectionBadges` and `refreshBriefConsistency` ARE re-run at that point (`detail.js:1426`, `:1433`); the provenance line is not.

Proof by execution that this is a build-order problem and not a ranking problem — the **same project, rendered twice in one page**:

```
FIRST render  (the load the user gets)  ->  'Green, driven by Cost and EVM Performance -> TCPI'
                                            hop: 'TCPI: Green (tied with 1 other module...)'
SECOND render (row already primed)      ->  'Green, driven by Cost and EVM Performance -> CUSUM Anomaly Monitor'
                                            hop: 'CUSUM Anomaly Monitor: Red'
```

And on `PRJ-R60B`, the lowercase-`green` case:

```
FIRST render  -> '... -> TCPI'                     hop: 'TCPI: Green (tied with 1 other module...)'
SECOND render -> '... -> CUSUM Anomaly Monitor'    hop: 'CUSUM Anomaly Monitor: Green (tied with 2 other modules...)'
```

The second render is correct in both cases. The first render — the only one a user ever gets — is wrong in both. **The page attributes the project status to a module selected from a different period's module list, and on `PRJ-R60` it conceals a Red module.**

Note what this means for staleness: **this defect has nothing to do with the row being stale.** It fires on any project whose current period is not 1. A fixture computed only at period 1 can never show it.

### 8.3 Would every fixture-based browser verification since Run 44 have passed?

**Yes. Plainly: yes.** And the reason is visible in the harness itself.

`server/tools/drive_run44_browser.py:250-252`:

```js
window.LIN_PROJECTS = [p];
window.LinResults.prime('PRJ-B44', row);      // <-- the row is primed FIRST
window.LinDetail.render('PRJ-B44');           // <-- render() runs SECOND
```

The harness **constructs the row in JavaScript and primes it before calling `render()`**. That is precisely the "second render" condition — the one order in which the fix works. It never issues a `projectperiods` or `projectresults` request, never goes through `primeAndRefresh`, and never lets `workspace.js` prime a period-1 row first. It measured the code path in which the fix is correct, and **could not have failed against this defect**.

So: **ten runs of browser verification were measuring something that could not fail.** Every one of them was run against a fixture the session itself built and primed, and not one exercised the real load order on a project whose current period is not 1. That is the finding, and it is not softened.

I record the one thing that is *not* true of that criticism: those verifications were not worthless. Rows 3, 4 and 7 were verified in a real browser and **do** correct a real stale row — I re-measured all three here against a pre-fix database and they hold.

### 8.4 What a fix would have to change

Stated as diagnosis, not as a recommendation, and not attempted in this run (section 10.5 of the order).

A fix would have to change at least one of three things, and the third is the deepest:

1. **`detail.js`** would have to rebuild the provenance line after `primeAndRefresh` primes the row — the way `refreshSectionBadges` and `refreshBriefConsistency` already are rebuilt at `detail.js:1426` and `:1433`. Every other panel gets a second pass; this one does not.
2. **`workspace.js:989`** would have to stop defaulting to `period: p.period || 1`. It is the same hard-coded period-1 fallback Run 48 removed from `detail.js:1267`, still live in a second file, and it is what puts the wrong row into `ROWS` in the first place.
3. **`taxonomy.js:446` `rowFor`** would have to refuse to return a row whose `period` disagrees with `project.storedResult.period`. As written it silently prefers *completeness* over *correct period*, so a caller asking for module results can be handed a different period's modules with no signal that it happened. Every surface that reads module statuses through `getModuleStatus` is exposed to this, not only the provenance line.

---

## 9. The section 9 stored-row diff

Three dumps of the live `computed_results` rows for `PRJ-R60`, with `id`, `result_id`, `project_id` and `computed_at` removed (they must differ between two writes and say nothing).

**(a) 5.1 stale vs 5.3 after `projectcompute`:**

```
IDENTICAL - projectcompute wrote nothing at all
```

**(b) 5.1 stale vs a row genuinely rewritten by current code** (`resetsignals` then `projectcompute`, in a separate database copy so the 5.2 artefacts were untouched):

```
period 1:  simulation_version : sim-2026.08-v28 -> sim-2026.08-v38
period 2:  signal_inputs changed: ['baselineContractSum','baselineEnd','baselineStart',
                                   'revisedContractSum','sources']
           simulation_version : sim-2026.08-v28 -> sim-2026.08-v38
period 3:  (same four fields + sources)
period 4:  (same four fields + sources)
```

### 9.1 Which stored fields changed

Exactly five, and only on periods 2-4:

| Field | Stale (pre-fix) | Current code | Source recorded |
|---|---|---|---|
| `simulation_version` | `sim-2026.08-v28` | `sim-2026.08-v38` | — |
| `signal_inputs.baselineStart` | `null` | `2026-01-01` | `contract_value` |
| `signal_inputs.baselineEnd` | `null` | `2027-06-30` | `contract_value` |
| `signal_inputs.baselineContractSum` | `null` | `4000000` | `contract_value` |
| `signal_inputs.revisedContractSum` | `null` | `4000000` | `change_order` |
| `signal_inputs.sources` | lacks those entries | gains them | — |

That is **Run 45's identity-field carry-forward** working exactly as designed: an identity field stated once in a period-1 contract document is now carried into later periods, where pre-fix code left it null. It is a real compute-side improvement.

**Everything else is unchanged.** `cpi`, `spi`, `pv`, `ev`, `ac`, `bac`, `docRiskScore`, `actualPctComplete`, `plannedPctComplete`, `project_status`, `category_statuses`, `module_results` (including `A1.2`'s lowercase `'red'`), `abstained`, `portfolio_snapshot`, `seed`, `period_cutoff`, `source_documents` — byte-identical.

### 9.2 Which symptoms are explained by stored data, and which by rendering

| Explained by a **stored-field difference** | Explained by a **render difference** |
|---|---|
| Row 8, and only its identity half (four baseline/contract fields) | Rows 1, 2, 3, 4, 5, 6, 7, 9 |

**Eight of the nine symptoms are render questions.** The ninth is half a stored-data question, and its numeric half (CPI 1.22, SPI 1.27) is not a defect current code corrects at all — those are what the documents state.

**Note the consequence for A1.2's lowercase status:** current code still stores `'red'` and `'green'` in lower case while every other module stores `'Green'`. The casing inconsistency Run 44 diagnosed was **never fixed at source**; Run 44 made the *client* tolerant of it. That tolerance is correct, and it is why row 1 would be fine — if the ranking code were reached with the right period's modules.

---

## 10. Incidental findings, unacted

1. **`window.getModuleStatus` is defined twice, and the first definition is dead code.** `assets/js/categories.js:324` and `assets/js/taxonomy.js:485` both assign it; taxonomy.js loads later and wins. The live one reads the stored row. **The dead one still contains the legacy `project.signals.{mc,cusum,doc,decision}` reads** — `case "CUSUM": return s.cusum ? s.cusum.status : null` — which would return `null` for every server-computed project. Two definitions of one global with materially different behaviour, one unreachable. I spent real time reasoning from the dead one before execution corrected me.

2. **`workspace.js:989` still carries `period: p.period || 1`** — the same hard-coded period-1 fallback Run 48 removed from `detail.js:1267`, alive in a second file, and load-bearing for the section 8 defect.

3. **`rowFor` can silently mix periods.** `taxonomy.js:446` may return a row whose `period` disagrees with `project.storedResult.period`, with no warning to the caller. Measured directly: `project.storedResult.period = 4` while `rowFor().period = 1`.

4. **`projectcompute` and `projectcomputeall` cannot refresh a stale row.** On an unchanged document set they return `computed: 0, skipped: 4`. The user-facing control on the detail page is labelled **"Generate signals for every period"**, which does not say that it will decline. `resetsignals` does rewrite the rows.

5. **Section 9's standing open question is now mechanically answerable, but not for PRJ-001.** `signal_inputs.sources` records a **`docType`, `documentId`, `documentVersion` and `asOf` per field**. For my fixture, `pv` was written by **`time_phased_schedule`** and `ev`/`ac`/`bac` by **`pay_application`**. **For PRJ-001 specifically this remains NOT DETERMINABLE** — I had no access to its stored rows, and I did not touch its document set. Any session with read access to PRJ-001's `computed_results` can now answer it in one query: `signal_inputs.sources.pv.docType`.

6. **Two contradictory statements render on one page.** The Signal Flow panel says "3 modules with a current result, 60 with no current result"; the same page says "All required values present. Nothing outstanding." That is row 9, seen from a new angle.

7. **A panel renders the wall-clock month as a reporting period.** `Reporting period: 2026-08 · grouped analysis across 11 signal categories` — August 2026 is when the page was opened, not the period being displayed (period 4 ends 2026-06-30).

8. **Run 47's `consistency_findings` was not exercised.** It is derived at read time and would reach a stale row, but my documents state no self-disagreeing figure above tolerance, so no finding was produced. **Untested by this run**, not verified.

9. **The Executive Brief renders deterministically without an LLM** — "Generated from stored log · 63 modules · LOW confidence". This is why Key Drivers were measurable at all in a headless browser, and it is what made rows 3 and 4 checkable.

10. **`page errors: 0`** in every browser session, on both trees.

11. I did **not** run the 203 suites and do **not** cite them. Section 7.5 is right: they were green before this question was asked, and a green suite that primes a row before rendering it cannot speak to a defect that only appears when the row arrives after.

---

## 11. What the next session needs — stated as a decision for the owner

**What is settled, and needs no further work:** rows 3, 4 and 7 are fixed, render-side, and correct a pre-fix stored row the moment the page loads — measured in a real browser against a real pre-fix database. Row 6 is fixed at source. Those four fixes reached the page.

**Three decisions are yours.**

**Decision 1 — the render-order defect (rows 1 and 2).** The page names a Green module as the driver of the project status while concealing a Red one, on any project whose current period is not 1, on both stale and freshly computed rows. Section 8 names the file, the line and the mechanism. This run diagnosed it and did not fix it, as ordered. **Do you want it fixed, and if so, at which of the three layers section 8.4 identifies?** Fixing only `detail.js` repairs the visible symptom; fixing `rowFor` repairs the class of defect and touches every surface that reads a module status.

**Decision 2 — how verification is done from here.** The reason this survived ten runs is structural, not careless: every harness primed the row before rendering, so no harness ever executed the load order a user gets. **Do you want a standing rule that a browser verification must drive the page through `LinDetail.render` on a project loaded from the server, with no pre-priming — and on a project whose current period is not 1?** Without that rule the next fix will be verified the same way and the same class of defect will pass again.

**Decision 3 — what you actually do about your own site, today.** This one has a concrete answer and it contradicts the comfortable one. **Recomputing will not help you.** `projectcompute` and "Generate signals for every period" both decline to rewrite a row whose documents have not changed. And it would barely matter if they did: current code writes an almost identical row — only the four baseline/contract identity fields and the version stamp differ. **Your figures are not stale in any way that a recompute would repair.** Rows 3, 4, 6 and 7 should already look different to you on a page reload with a cleared cache; if they do not, that is a new fact and worth telling the next run. Rows 1, 2, 5 (the blank head line) and 9 will not change until code changes.

**One thing I could not determine and will not reconstruct:** which document type wrote PRJ-001's `pv`, and therefore whether its CPI of 1.22 rests on an understated PV. I had no read access to PRJ-001's stored rows. I did establish the mechanism that answers it (section 10.5), so a session with that access can settle it in one query rather than another trace.

---

### Provenance of this run

- Isolated worktree `.claude/worktrees/agent-a34d9e99e4e30a095`; nothing written to the main checkout; `main` and every `run58-*`/`run59-*` branch untouched. Worktree left clean (`git status --porcelain` empty) at `f4c1dbf`.
- Pinned current tip **`f4c1dbf`**, named before the experiment began and used throughout; `main` moved to `5f5cf60` mid-run and the five files this report rests on are byte-identical between the two.
- Pre-fix tip **`604291a`**, non-vacuity proved by locating all six pre-fix defects in its bytes.
- Stale database preserved read-only before any render; the 5.2 render proved by diff to have written nothing to `computed_results`.
- `DATABASE_URL` was throwaway SQLite in a scratchpad at every step. PRJ-001 and every synthetic corpus untouched. No user-facing control added, moved or removed. No production behaviour changed. Nothing fixed.

### A note on how this report was committed

The Run 60 agent's harness blocked it from writing report files, so it returned the report as its reply and named the artefacts it left in the session scratchpad. The orchestrating session wrote this file from that reply verbatim and committed it, so the order's section 11 requirement is met. The report's content is the agent's; the commit is the orchestrator's.
