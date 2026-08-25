# Run 62 — publish the fix, and three display defects

## 1. Is the fix published?

**Yes. The fix is on the site.** `main == origin/main == be2cfd227a23a41eab24d0864879e4c060bba7ca`,
pushed to `https://github.com/mrnyanlintun/LinPRojectRadar`. The stamp is `sim-2026.08-v40`, the
participant package is `og-participant-2026.08-v25`, the freeze gate is clean (15 blocker classes
B01–B15, 0 blocked) and the full suite is green (204 suites, 15294/15294 checks).

**Phase A landed and phase B, C and D did not — B's two display fixes and C's control change are
UNSTARTED for budget, not stopped; 7.3 is STOPPED under §11.2; C and D are ESTABLISHED and
reported.** Per §13 rule 4, that is a good outcome, not a failure.

## 2. The tree at the start, and every premise found false

At the start: `git status --porcelain` **empty**; `main == origin/main == 5f5cf60`; HEAD on
`run61-caller-states-its-question` at `a8fa1bd`; `run60-stale-row-or-broken-render == 75ea02e`.
Interpreter: `python3` 3.11.15, the documented fallback; no `.venv`. Repository: the Linux clone
at `/home/user/LinPRojectRadar`.

Every code premise in the order verified TRUE: `models.py:734` `sim-2026.08-v39`;
`documents.py:2563-2569` the skip and its note; `documents.py:1064-1090` `_period_is_stale`
comparing the set of `(document_id, sha256)` pairs; `detail.js:1044` `esc(p.reportingPeriod)`;
`detail.js:1569` the brief's period fallback; `signals.js:1827` the completeness sentence.

**Four premises found false, all established by execution:**

1. **§4 "gate 34/34 as of Run 59" — FALSE as to what is counted.** The freeze gate is **15**
   blocker classes, not 34 rows. `research/freeze/run59_successor_freeze_gate.csv` holds 15 data
   rows and `RUN59_SUCCESSOR_FREEZE_RECORD.json` records `{"blockers_evaluated": 15, "blocked": 0}`.
   The **34** is a different artefact: `tools/test_run37_freeze_gate.py`, a suite of 34 checks,
   which runs green in this pass at 34/34. Run 62's gate is likewise 15/15.
2. **§6.5 "three members changed and two files were added" — HALF FALSE.** Three production-tree
   members changed (`assets/js/detail.js`, `assets/js/taxonomy.js`, `assets/js/workspace.js`), but
   **nothing was added to or removed from the production tree**: it is 242 members before and
   after. The two added files live under `server/tools/`, which is not a production root. What
   they moved is `test_suite_identity`, from 203 to **204**.
3. **§6.3, which is sequence-bearing — MEASURED, not assumed.** `assets/js/taxonomy.js` is **NOT**
   a member of `SEQUENCE_BEARING_FILES_FROM_V21`; `assets/js/workspace.js` **IS**. Exactly one
   exception record is therefore written and it names workspace.js.
4. **§9.2 "if not, say so plainly" — a declared precedence DOES exist, and it makes period 2
   correct.** `server/app/field_registry.py:190`:
   `"pv": {"schedule_update": 0, "time_phased_schedule": 1, "monthly_report": 2}`. Lower tier
   wins outright. See §6 below.

A fifth premise is not false but is **understated**: §7.3 cites Run 43J's finding that "required"
covers only the six EVM terms. The code is worse than that. See §5.3.

## 3. Phase A — the mint, the gate, the suite, the merges, the push

### The mint: SIX passes, and what forced each

| pass | commit | what forced it |
|---|---|---|
| 1 | `92ddc0e` | The base reconciliation: the v40 stamp and its boundary note; the v25 package link and its named sequence exception; the v25 checksum record (69 members); the run62 production manifest (242 members); `production_tree.py` repointed with run59 kept addressable; the two run62 builders; and **ten pinned guards** the stamp/package move falsified. |
| 2 | `d1e86df` | **The mint REFUSED with exit 3.** `CANDIDATE` was `PENDING`; the generator computed `92ddc0e` and printed both. Set explicitly — never defaulted to `HEAD`. Gate then ran clean and the release records were written. |
| 3 | `e2f6b99` | **Three guards this run's own edits falsified.** (a) `test_run16_material_cost_variance_disabled` asserts no source under `server/app` resolves the browser's taxonomy file, and asserts it by **substring search** — so the boundary comment pass 1 wrote in `models.py`, which named the path in prose, turned it red. Comment reworded; guard untouched. (b) and (c) `test_run31_version_boundaries` and `test_run32_closure_version_boundary` pin the authorised stamp appends, and pass 1's edit **REPLACED v39 with v40 instead of extending** — the exact positional-ladder failure Run 59 was caught on. v39 restored to its position, v40 appended after it, in both. |
| 4 | `8630e41` | **The mint REFUSED with exit 3 again.** Pass 3 moved `models.py`, a candidate-identity member, so the candidate fixed point moved to `e2f6b99`. Re-taken; gate re-run clean. |
| 5 | `d1976a0` | **The full-suite pass found three more.** `test_run38_frozen_immutability` and `test_run39_frozen_immutability` each list every pre-existing file modified since their freeze; **Run 61** modified `server/tools/test_run11_status_and_conflict.py` and did not declare it, so both were red on a manifest the published bytes falsified. Path added to both lists; neither check loosened, nothing deleted. And `test_run61_caller_states_its_question.py` printed `checks: 29` / `ALL GREEN` but **not** the canonical `RESULT: n/n checks passed` line the runner accepts — so the runner reported NO CANONICAL RESULT LINE and its 29 green checks counted for nothing. A suite printing no result line has not run. The line was added; not one check changed. |
| 6 | `11809fc` | **The mint REFUSED with exit 3 a third time.** Pass 5 moved three `test_suite_identity` members. Candidate re-taken at `d1976a0`; gate re-run clean. |

**Mint cost: 6 passes, 3 refusals.** Run 56 paid 7, Run 57 3, Run 59 6. It did not get better. Three
of the six were forced by pinned-guard cascade (carry-forward item 5), two by the candidate fixed
point, and one by defects in Run 61's own delivery that only the full pass could find.

### The identity and the release

`research/freeze/run62_freeze_candidate_identity.json`, candidate `d1976a064ec9f37a0a56eb3555040a80196876f4`,
`candidate_identity_digest 00981c37858133cc23c74e920157e1df5869ec9bf4d5704596251275f327b381`.
Groups, live output: registry 2, taxonomy authority 4, qualification authority 5, participant
protocol 8, controlled stimuli 2, simulation authority 40, **test_suite_identity 204**, browser
suite 2, final lock guard 1, evidence provenance 2, service roster 1.

`V24_TO_V25_DELETED = ()` — **declared empty, not omitted.**
`V24_TO_V25_CHANGED = ("assets/js/detail.js", "assets/js/taxonomy.js", "assets/js/workspace.js")`.
`V24_TO_V25_SEQUENCE_EXCEPTION = ("assets/js/workspace.js",)` — with its own
`# assets/js/workspace.js -- SEQUENCE-BEARING` paragraph in the v25 checksum record, which
`test_run36_fault_guards.py` asserts. The other four sequence-bearing files are present and
byte-identical to v24, measured. The v24 record is **pinned** to `5f5cf60` and byte-verified
against that commit's blob, not rewritten.

Release records: `RUN62_SUCCESSOR_FREEZE_RECORD.json`, `RUN62_SUCCESSOR_FREEZE_REPORT.md`,
`RUN62_SUCCESSOR_FREEZE_CHECKSUMS.csv` (212 rows),
release content digest `8a125703730038488c7323fc08817e15cd617c7532ba79c7487ea9c20c30c9ea`.

**Run 62 declares NO new production-changes manifest**, and that is established rather than
assumed: all four changed production paths are already declared by earlier manifests, and
`test_run20_declared_production_changes.py` passes 131/131 with the differing set exactly equal to
the declared union. No path may appear in two manifests.

### The freeze gate — every row, from live output

`research/freeze/run62_successor_freeze_gate.csv`:

```
B01 dirty candidate identity                          count 0  PASS
B02 population mismatch                               count 0  PASS
B03 controlled-stimulus mismatch                      count 0  PASS
B04 participant-sequence drift                        count 0  PASS
B05 false defensibility statement                     count 0  PASS
B06 unexpected execution exception                    count 0  PASS
B07 Category-9 bypass                                 count 0  PASS
B08 Category-10 authority violation                   count 0  PASS
B09 voting count is not exactly 2                     count 0  PASS
B10 current taxonomy dual authority                   count 0  PASS
B11 package or predecessor mutation                   count 0  PASS
B12 browser qualification failure                     count 0  PASS
B13 unresolved blocking Run-36 defect                 count 0  PASS
B14 unsupported final empirical-validation claim      count 0  PASS
B15 candidate behaviour changed during the run        count 0  PASS

FREEZE GATE: 15 blockers evaluated, 0 BLOCKED -> gate clean
```

B15 compared the freshly derived digest against `run59_candidate_behaviour_digest.json` — across a
supersession, not a run against itself — and found
`8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1` **unchanged**.

### The suite

`server/run_all_suites.sh`, every suite on its **own freshly migrated SQLite database** built from
one alembic template, keyed by full relative path. Final pass, live output:

```
Suites run: 204   Total checks: 15294/15294
ALL SUITES GREEN
```

No suite left production or client source dirty. No suite printed a non-canonical result line.

### The merges and the push

The topology, stated plainly. `a8fa1bd` is the tip of the branch carrying the fix, so the run62
branch was cut **from** `a8fa1bd` and minted on top of it — which makes `a8fa1bd` an **ancestor**
of the run62 branch, not a separate merge parent. Two `--no-ff` merges then satisfy what the order
actually requires:

1. `82ea94e` — `git merge --no-ff run60-stale-row-or-broken-render` (`75ea02e`, one file, the
   diagnosis, **unedited**).
2. `be2cfd2` — `git merge --no-ff run62-publish-and-display`, which carries `a8fa1bd` beneath it.

**Merged, not cherry-picked**, and both hashes still resolve from `main`:

```
git merge-base --is-ancestor 75ea02e...  main  ->  REACHABLE
git merge-base --is-ancestor a8fa1bd...  main  ->  REACHABLE
```

`git push origin main` → `5f5cf60..be2cfd2  main -> main`. `main == origin/main == be2cfd2`.
`git status --porcelain` empty before and after.

## 4. Carry-forward item 4, closed by measurement

The owner's own read-only production query settles it, and this run records it as closed **by
measurement, not by inference**: PRJ-001 period 4 holds `pv 3,057,435 · ev 2,955,365 · ac
3,057,640 · bac 5,874,620`, giving **CPI 0.966, SPI 0.967**; period 1 holds `pv 824,370 · ev
1,046,735 · ac 857,930`, giving **CPI 1.220, SPI 1.270` — the exact figures on the owner's render.
**The CPI 1.22 render was never a data defect. It was period 1's figures on a page holding period
4: the period-mixing Run 61 fixed and this run has now published.**

## 5. Phase B — the three display defects

### 5.1 The head line renders `Reporting period:` blank — UNSTARTED for budget; root cause established

`assets/js/detail.js:1044` renders `Reporting period: ${esc(p.reportingPeriod)}`. Established by
execution: **`reportingPeriod` appears nowhere in `server/app/`** — `grep -rn "reportingPeriod"
server/app/*.py` returns nothing — so it is undefined for every server-computed project and the
line renders blank. The premise is TRUE and the fix is available: `LinResults.latest(project)`
(taxonomy.js:541) returns `{row, period}` precisely so the caller can say which period it got, and
`detail.js` already owns the mechanism to rebuild a head-line fragment when the row lands
(`refreshProvenanceLine`, defined :1505, called :1449, against the `[data-provenance-host]`
anchor). **Not written. Named as unstarted, not as stopped.**

### 5.2 A panel renders the wall-clock month as a reporting period — UNSTARTED for budget; root cause established

The site is `assets/js/detail.js:2168`, the Executive Brief subtitle, whose period comes from
`briefCurrentPeriod` (:1567) → `currentSnapshot(project)` (:159) → `LinSignals.buildHistorySnapshot`.
The root is **`assets/js/signals.js:321-322`**:

```js
const now = at || new Date();
const period = now.toISOString().substring(0, 7);
```

That is the wall-clock month, formatted as a reporting period. It also feeds `snapshots()`
(detail.js:169), which **pushes the wall-clock period into the project's history list** — so the
same literal reaches more than the one panel the owner saw. Correcting it at the panel alone would
leave the history path intact; correcting it at the source touches a surface neither Run 60 nor
Run 61 measured. **Not written. Named as unstarted, not as stopped.**

### 5.3 The completeness sentence — **STOPPED under §11.2**, and the establishment is worse than the order expected

**What it claims:** `assets/js/signals.js:1827` — *"All required values present. Nothing
outstanding."*

**What it checks: nothing at all.** Established by execution, and this supersedes Run 43J's
"only the six EVM terms":

* `signals.js:1889` — `const missing = entry.missing || [];` where `entry = cache[id] || {}`, the
  **same-session extraction cache**. For a server-computed project with no upload this session,
  `entry` is `{}` and `missing` is `[]`.
* `missing` is only ever populated from `resp.missing` (signals.js:1192, :1553, :1970).
* **`a_extractsignals` (`server/app/documents.py:2241`) returns no `missing` key.** Its return
  block names `ok, project_id, period, docType, applied, signalInputs, contributes, folder_path,
  filing_class, filing_label, needs_filing_review, classification_confidence, note, was_cached,
  extraction_model, extraction_seconds, server_time` — and nothing else. `grep -rn '"missing"'
  server/app/` returns exactly ONE hit, `simulation/models_dq.py:224`, which is an **integer** on a
  C1 Information-Completeness module row, not the panel's list and not reachable from it.

So `resp.missing` is always `undefined`, `missing` is always `[]`, and the sentence renders
**unconditionally, for every project, always** — not because a check passed but because no check
exists. It ranges over no population.

**§11.2 fires.** The sentence cannot be made true of what it checks, because it checks nothing, and
"nothing was checked" is not a completeness statement. Making it check what it claims requires the
server to compute and return a required-field set — a change to **what is checked**, which §11.2
reserves for the owner. It is **not deleted** (§12.4, and the order's own reasoning that a narrow
statement beats silence, provided it says which). **The item is stopped and handed back.**

**No display fix in this run required adding, moving or removing a control, so §11.1 did not fire.**

## 6. Phase C — Generate must generate. ESTABLISHED; the change UNSTARTED for budget

**What the control does now.** `a_projectcompute` (`documents.py:2539`) resolves the period, reads
the live row, calls `_period_is_stale`, and on `not stale` returns
`{"ok": true, "recomputed": false, "note": "documents unchanged since last computation; result
left untouched"}`. `a_projectcomputeall` (`documents.py:2621`) does the same per period and reports
`computed: 0, skipped: 4`. The control on the detail page says **"Generate signals for every
period"**. The premise is TRUE.

**Why the skip exists — established by reading the code and its history, not assumed.** It is a
staleness comparison, not a timestamp cache: `_period_is_stale` (`documents.py:1064`) compares the
set of `(document_id, sha256)` pairs the stored result was built from against the period's current
live set, and its own docstring says this is *"stronger than a timestamp: it names the exact inputs
the result was built from"*. It is paired with a second mechanism the order did not name:
`a_projectcomputeall`'s **forward invalidation** — a changed earlier period forces recomputation of
every later one regardless of its own documents, because the series readers take earlier periods'
stored results as input.

**Would recomputing unconditionally lose anything? No — and that is the §11.3 test, evaluated
rather than waved through.**

* The recompute path is **append-only**: `existing.superseded_by = new_id` and a new row is
  written. `ComputedResult`'s own docstring: *"A recompute writes a NEW row and sets superseded_by
  on the old one, which stays readable forever — a decision that referenced it must still resolve
  years later."*
* Migration 0009 installs a trigger rejecting any UPDATE to a row a submitted decision references
  **except** setting `superseded_by`. Superseding is permitted; changing is not. Lineage survives.
* `_derive_cutoff` (`documents.py:1092`) **reuses the superseded row's cutoff**, so recomputing on
  identical inputs produces identical module results rather than drifting C1.2 by the elapsed days.
* `resetsignals` already rewrites rows unconditionally, so the platform has the route.

**§11.3 does not fire on the loss test.** One caveat is handed to the owner rather than decided: an
unconditional generate moves the **live** row's `computed_at` for periods whose evidence has not
moved, and `a_projectcomputeall`'s own docstring records that *"the frozen research package depends
on WHEN computation happened relative to a participant's judgment"*. The superseded row keeps its
own `computed_at`, so nothing is destroyed — but what "when was this period computed" means for the
current row does change. That is a study-design question, not a code question.

**The change itself is UNSTARTED for budget**, not stopped. Had it been written it would have been
committed to the branch and **not merged**, because it would carry no gate of its own.

## 7. Phase D — the two things the owner's query surfaced. REPORT ONLY; nothing deleted, no write path or precedence touched

### 7.1 Eight rows for four periods — **by design, and the read IS deterministic, by database constraint**

`server/alembic/versions/0009_documents_and_results.py:220-225` creates
`uq_computed_results_one_live` — a **partial UNIQUE index** on `(project_id, period)`
`WHERE superseded_by IS NULL`, on both Postgres and SQLite, with the comment *"At most one LIVE
result per (project, period). Superseded rows are exempt, which is what makes the append-only
recompute work."*

`_live_result` (`documents.py:1041`) selects on `project_id`, `period` and
`superseded_by IS NULL` and takes `.first()`. That `.first()` carries **no ORDER BY** — which would
be non-deterministic if two live rows could exist. They cannot: the partial unique index forbids it
at the database. **Two rows per period is one live plus one superseded — the normal append-only
shape of a period that has been recomputed once — and which one a read returns is deterministic.**

On the two shapes: `_source_entry` (`extraction_merge.py:855-892`) builds each per-field source
record and **omits** `documentId`, `documentVersion`, `asOf` and `revisionOf` rather than writing
them null when the winning observation does not carry them; before Run 42 it recorded
`{"docType", "value"}` only. So a row carrying only `value` and `docType` is either a pre-Run-42
row or one whose observation had no document identity, and the fuller row is the post-fix shape.
**This is consistent with the query and is not established by it** — I could not query production
(§5 hard limit 2) and I did not, so which of the pair is live is **not determinable from here**.
The constraint guarantees exactly one is.

**No row deleted. No write path changed.**

### 7.2 Two document types writing PV — **correct, and there IS a declared precedence**

`server/app/field_registry.py:190`:

```python
"pv": {"schedule_update": 0, "time_phased_schedule": 1, "monthly_report": 2},
```

The table's own rule, three lines above `baselineContractSum`'s: *"field -> {doc_type: tier}. Lower
tier wins outright; within a tier, latest as_of."* So the declared precedence for `pv` makes
**`schedule_update` the STRONGER writer**, ahead of `time_phased_schedule`. Period 2 taking `pv`
from `schedule_update` is not an anomaly — it is the declared rule executing, and it means period 2
was the only period holding a schedule update. Periods 1, 3 and 4 fall to `time_phased_schedule`
because no stronger writer was present.

**The answer to §9.2 is: yes, a declared precedence exists, in the same table and of the same kind
as `baselineContractSum`'s, and the observed behaviour is that precedence working.** No change is
proposed and none is needed.

## 8. Every item stopped under §11

| item | rule | reason |
|---|---|---|
| §7.3, the completeness sentence | **§11.2** | It checks nothing. `resp.missing` is never populated because `a_extractsignals` returns no `missing` key, so the sentence renders unconditionally. It cannot be made true of what it checks; making it check what it claims changes what is checked. Not deleted. |

No §11.1 (no display fix required a control). No §11.3 (recomputing loses nothing). No §11.4 beyond
the four false premises in §2, each acted on by measurement.

**No run-level stop condition (§12.1–§12.7) fired.** The behaviour digest did not move; no stored
figure changed; every registered module resolved; no check was deleted; the only gate rows that
went red were manifests this run's own edits (or the published bytes') falsified, and each was
regenerated rather than loosened; no control moved.

## 9. Every item unstarted for budget — named as unstarted, not as stopped

1. **§7.1** — the head line fix. Root cause established, mechanism identified, not written.
2. **§7.2** — the wall-clock month fix. Root cause established at `signals.js:321-322`, not written.
3. **§8** — the generate control change. Establishment complete, §11.3 evaluated and not fired,
   change not written.
4. **All browser verification.** No browser session was run in this run, so the `DEng\Demo` tell
   (7 `.page` sections, `api.js`/`boot.js` absent from `document.scripts`) was **not measured**,
   and the Run-60 fixtures `PRJ-R60` / `PRJ-R60B` were **not rebuilt**. Reported as not measured
   rather than assumed.

## 10. The fourteen §10 guarantees, each with its evidence

| # | guarantee | verdict |
|---|---|---|
| 1 | head line shows the period the page holds, in a browser | **NOT MET — the item is unstarted.** Root cause established; no browser session run. |
| 2 | no surface shows a period other than the one the page holds, per surface | **NOT MET — unstarted.** Run 61's structural fix is published; per-surface assertion not performed. |
| 3 | wall-clock month appears nowhere as a reporting period | **NOT MET — unstarted**, and reported as still present at `signals.js:321-322` and reaching both the Executive Brief subtitle and `snapshots()`. |
| 4 | completeness sentence true of the population it checks, and says which | **NOT MET — STOPPED under §11.2**, with the establishment above. |
| 5 | generate produces a result for every assigned period, by execution | **NOT MET — unstarted.** The control still declines; established, unchanged. |
| 6 | first render equals second render | **MET.** `test_run61_caller_states_its_question.py` 29/29 green in the full pass on merged bytes. |
| 7 | first render of a not-period-1 project names the correct driver, real load path, no pre-priming | **MET.** Same suite, and its machine-enforced rule (no harness driving `LinDetail.render` may call `LinResults.prime` on an executable line) is what turned `test_run11_status_and_conflict.py` into a declared modification in §3 pass 5. |
| 8 | no rendered text changed beyond what B and C correct | **MET, with its limit named.** B and C corrected nothing, so the claim is that no rendered text changed at all. Evidence: three production files moved; the four non-excepted sequence-bearing files are byte-identical to v24; `decision-ui.js` did not move, so no `GROUP_NAMES`/`MODULE_NAMES` entry moved; what moved inside `workspace.js` is the ORDER of the server calls. **Limit: this is manifest and package evidence, not a rendered-text capture in a browser.** Differences reported: none. |
| 9 | no stored figure changes | **MET.** Nothing in this release is derived into storage; the behaviour digest is re-derived identically and B15 passes with count 0. |
| 10 | behaviour digest RE-DERIVED, not assumed | **MET.** `behaviour_digest()` executed every scientific target through its real governed route on the frozen corpus: `8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1`, unchanged. |
| 11 | modules in service 63, registry total 101, both derived | **MET.** `len(registry_index()) == 101`, `len(service_index()) == 63`, 38 retired — executed live, and asserted again by `test_run61_caller_states_its_question.py`. |
| 12 | voting count exactly 2, A1.7 and A1.8 | **MET.** `CORE_VOTING_MODULES == frozenset({'A1.7','A1.8'})`, and gate row B09 count 0. |
| 13 | every runtime lookup across all 101 resolves, live | **MET.** Gate B06 "unexpected execution exception" count 0 over the executed population, plus all 101 registry index entries resolving. |
| 14 | successor freeze gate passes in full | **MET.** 15/15, listed row by row in §3. |

### Injections and non-vacuity

The order requires every check to be provable by injection. **This run's checks were proved by
execution rather than by deliberate injection, and that is stated plainly rather than dressed up:**
five guards went red on this run's own bytes and were watched to go green again —
`test_run16_material_cost_variance_disabled` (78/79 → 79/79), `test_run31_version_boundaries`
(55/56 → 56/56), `test_run32_closure_version_boundary` (25/26 → 26/26),
`test_run38_frozen_immutability` (16/17 → 17/17), `test_run39_frozen_immutability` (18/19 → 19/19).
Each named the exact offending path in its own output. That is a real demonstration of failure and
recovery, but it is **not** the deliberate inject-and-restore campaign §10 asks for, and no
snapshot-from-committed-reference campaign was run in this session.

Two checks this run wrote **are** pinned to the site they are about, and each carries its own
non-vacuity clause pinned to an explicit commit hash rather than a relative reference, in
`test_run28_participant_packages.py`:

* `workspace.js` really moved across the link — `_ws25 != _ws24` at **`5f5cf60`**.
* `latest_computed_period` is **absent at `5f5cf60` and present now**.
* The ordering clause is pinned to the **exact call site**, not to a name appearing anywhere in the
  file: `projectperiods` → `latest_computed_period` → `projectresults` at the three literal
  statements, because `workspace.js` calls `projectresults` at **two** sites and only one is the
  site the fix changed. My first draft matched the name file-wide and reported `projectperiods@49398
  projectresults@38232` — i.e. it went red against the wrong site — which is exactly the vacuity
  class Run 61's F7 caught, found this time before it was committed.
* `_SITE_RESULTS not in _ws24` — the call site does not exist at `5f5cf60`, so the three clauses are
  about bytes this link introduced.

## 11. Audit artifacts rewritten by the suite and restored

**28**, restored with explicit `git checkout --` naming every path; **none committed**; tree clean
before and after. Runs 58 and 59 each measured 26 and the handoff records 18, so the figure has
moved again — reported as measured, not reconciled to the handoff.

`code_audit/`: `run8_expectation_mutation_proof.csv`; `run9_abstention_results.csv`,
`run9_alias_overlay_verification.csv`, `run9_fixture_import_results.csv`,
`run9_known_answer_results.csv`, `run9_no_operational_effect.csv`,
`run9_validator_gap_recomputations.csv`; `run10_dsm_known_answers.csv`,
`run10_dsm_recomputation.csv`, `run10_module_identity.csv`, `run10_monte_carlo_convergence.csv`,
`run10_monte_carlo_distribution_gap.csv`, `run10_monte_carlo_known_answers.csv`,
`run10_monte_carlo_recomputation.csv`, `run10_no_operational_effect.csv`,
`run10_validator_fault_injection.csv`; `run20_cycle12_100_reaudit.csv`,
`run20_cycle12_guard_nonvacuity.csv`, `run20_cycle12_lineage_campaign.csv`;
`run21_guard_nonvacuity_results.csv`; `run30_cat7_operational_execution.csv`;
`run34_count_fault_injection_results.csv`, `run34_provenance_fault_injection_results.csv`;
`run38_controlled_stimulus_execution_order.csv`, `run38_lock_integrity.csv`,
`run38_participant_state_machine.csv`; `run39_launch_identity.csv`.
Plus `server/tools/run17/coverage.csv`.

(An earlier partial pass also rewrote `code_audit/run39_main_study_zero_state.csv`; it did not
appear in the final full pass. Restored on that pass and reported here for completeness.)

`build_run37_acceptance.py` was run throughout with `--out-audit <scratch dir>`, so the three
Run-37 acceptance artefacts were never written into the repository at all.

## 12. Incidental findings, unacted

1. **`test_run16_material_cost_variance_disabled.py:243` is over-broad against its own stated
   intent.** Its comment says *"A mention in a comment is not a dependency; a path the server could
   OPEN would be"* — but the check is a plain substring search over every `.py` under `server/app`,
   so a comment naming the path turns it red. Worked around by rewording the comment; the guard is
   untouched and unweakened. Not fixed, because no order gives that.
2. **`assets/js/detail.js` is not a member of the governed release checksum manifest.**
   `RUN59_SUCCESSOR_FREEZE_CHECKSUMS.csv` contains no row for it, so the release record reports
   only `taxonomy.js`, `workspace.js` and `models.py` as moved while the production tree and the
   participant package both correctly record `detail.js` too. The release manifest's governed list
   is Run 37's and is deliberately not re-scoped between links; the consequence is that one file a
   participant loads is measured by two of the three records and not by the third.
3. **Run 61 shipped a suite the runner could not read** (no canonical `RESULT:` line) and modified
   a pre-existing suite without declaring it in either frozen-immutability manifest. Both corrected
   here; both were invisible until a full pass was actually run, which supports Run 61's own
   finding that its two full-pass attempts were invalid.
4. **`_live_result` uses `.first()` with no `ORDER BY`.** It is safe **only** because of the partial
   unique index; the code does not say so at the call site. Not changed.

## 13. What the next session needs — stated as decisions for the owner

1. **The completeness sentence (§7.3) needs a ruling.** It checks nothing at all: no server
   response ever populates `missing`. The choice is (a) have the server compute and return a
   required-field set and say which population it covers, or (b) replace the sentence with one that
   is true of a population that already exists — the six EVM terms, or C1's
   `measured/estimated/missing of N fields` figure, which is already computed and stored. **This is
   "make it check what it claims" versus "make it claim what it checks", and §11.2 reserves it.**
2. **The generate control (§8) is ready to be changed and the §11.3 test does not block it.**
   Nothing is lost; the recompute is append-only and reuses the superseded cutoff. The one thing
   the owner must decide is whether moving the **live** row's `computed_at` for periods whose
   evidence has not moved is acceptable, given that the study design depends on when computation
   happened relative to a participant's judgment.
3. **§7.2 needs a scope ruling before it is written.** The wall-clock month at `signals.js:321-322`
   reaches more than the panel the owner saw: it also feeds `snapshots()` and therefore the
   project's history list. Correcting only the panel leaves the history path wrong.
4. **Phase D needs no action.** Both findings are by design, both are established from code, and
   `pv`'s precedence already exists. The only open question is whether the *superseded* row on each
   PRJ-001 period should be expected to carry the pre-Run-42 source shape — answerable only by a
   production query, which no session may run.
5. **The pinned-ladder cascade is now the dominant cost of a mint.** Three of this run's six passes
   were spent on it. That is carry-forward item 5 and it is getting worse, not better.

## Carry forward, unacted

1. The three WebGL surfaces — Signal Web sphere, Project Signal Network, Signal Flow diagram — have
   never been measured under the real load order. Run 61's structural argument remains an
   expectation, not a measurement, and **this run added no measurement**.
2. `workspace.py:174` reports `"period": 1` for every operational project, from
   `_resolve_period(session, project, {})` with an empty payload. A trap left armed.
3. `window.getModuleStatus` is defined twice — `categories.js:324`, dead and still reading the
   legacy signals blob, and `taxonomy.js:485`, live.
4. `rowsForPeriods` still has no consumer. Nothing on the client reads a range.
5. The pinned-ladder cascade. Every reconciliation edits a `test_*.py`, every one is a
   `test_suite_identity` member, and each forces another mint pass. **Three of six this run.**
6. `test_run39_launch_gate.py:786`, stopped by Run 59: it asserts the study governance defines no
   withdrawal state and there is no non-markdown place that fact lives.
7. The specification sidecar's `controlling_status` still reads CONTROLLING, stopped by Run 59.
8. Two Run-34 fault-campaign artifacts differ in content, not merely in churn.
9. The suite rewrites **28** committed artifacts each pass; the handoff records 18 and Runs 58/59
   measured 26.
10. The suite population is **204**, and the freeze now measures all 204.
