# Stages 7 and 8: reporting and display, audit trail and logging

**Read-only session. No code was modified. No test file was edited.**

Continues `REPORT_2026-08-02_pipeline-audit.md`, which covered stages 1 to 4 and the period scope
and stopped. This covers the two stages it named as not started, and answers the three questions
it left open.

**Method, and its limit.** Everything below was established by reading the shipped code, plus one
execution of `compute_portfolio` to confirm D7.1. **I did not drive a browser this session**, so
where a finding depends on which route renders which panel I say so rather than asserting it. The
`Demo` trap in the brief did not arise: no browser session was started.

---

## Leading with the ones where what a user reads is not what was stored

### D7.1. Two Group D results are displayed, and neither is computed from anything. PROVEN.

| | |
|---|---|
| **Stage** | 7, and 6 |
| **Where** | `server/app/documents.py:326` passes `None`; `server/app/simulation/portfolio.py:120-164`; rendered by `assets/js/workspace.js:747-767` |
| **Reachable** | **Today, on every portfolio view of every project, always** |
| **Reaches a user** | **Yes**, as a green dot and an evidence sentence |

**This answers the audit's open question about `compute_portfolio`'s `history` argument. Nothing
supplies it.** `_compute_and_store` is the only caller on the server path, and it passes the
literal `None`:

```python
snapshot = compute_portfolio(vectors, project.legacy_id, None, cutoff)
```

There is no other caller. `history` is therefore always `[]` inside the function, so both guards
on `len(history) >= 2` are permanently false. Executed:

```
cat8_3_trajectory_classifier
  status_color     : "Green"
  trend            : 0.0
  periods_analyzed : 0
  insufficient_data: true
  evidence_metric  : "No history available"

cat8_5_anomaly_score
  status_color     : "Amber"
  composite_score  : 0.5      (scores = [anomaly, 1-rank, 0.5]; the trend term is never appended)
```

Two things follow, and the first is worse than the second.

**Signal Trajectory Classifier is permanently Green.** `status_color` initialises to `"Green"` and
is only ever reassigned inside the `len(history) >= 2` branch. The module also sets
`insufficient_data: true` — honestly — but `workspace.js:750` renders `statusDotColor(m.status_color)`
and `m.evidence_metric`, and **reads neither `insufficient_data` nor the sibling
`insufficient_data` shape the outer snapshot uses**. So a director sees a green dot beside
"Signal Trajectory Classifier" with the note "No history available". The dot says healthy; the
sentence says nothing is known. The dot is the thing that carries at a glance.

This is the same failure shape as D1's Rough Sets: a colour derived from nothing, presented
without abstention. It differs in that the module *does* declare its own abstention and the
display surface discards it.

**Composite Anomaly Score is computed from a portfolio that never includes the trend.** Its
`scores` list is `[anomaly_score, 1 - composite_rank, 0.5]` with a fourth term appended only when
history exists. The constant `0.5` is always a third of the mean. The number is not wrong for its
inputs; it is a different statistic from the one the method name and the Methods tab describe.

**Test coverage: `test_workspace_t3t5.py` Guarantee 9 line 254 asserts the snapshot carries five
sub-results and asserts nothing about any of them.** It would pass with all five permanently
Green.

---

### D7.2. The recommendation a user reads is derived in the browser, not read from the stored row

| | |
|---|---|
| **Stage** | 7 |
| **Where** | `assets/js/decision.js` `deriveDecision`; rendered by `assets/js/app.js:1605-1650` (`renderDecisionCard`) |
| **Reachable** | **Today**, on the project detail page of any project with a stored result |
| **Reaches a user** | **Yes**: the recommended action, the authority entitled to act, the documentation required, and whether a fairness gate applies |

`renderDecisionCard` gates correctly on a stored row existing (`LinResults.hasResult(p)`), and the
**status** it shows is the stored `project_status`. Everything else on that card is computed in the
browser:

```javascript
function deriveDecision(project) {
  const healthState = deriveHealthState(project);      // stored — correct
  const conflictType = classifyConflict(project);       // legacy blob
  const escalate = healthState === "Red" || healthState === "Red-review";
  const fairnessGateRequired = escalate && project.fairnessSensitive === true;
  // action / authority / documentation assigned from healthState by if/else
}
```

The server has 36 Group B computations whose stated purpose is Recommendation and Governance,
including B4.4 Regret Minimization which emits `recommended_action` and is subject to the
pre-lock redaction. **None of them reach this card.** The card's recommendation is a four-branch
`if` over the fused colour, carried over from the retired client-side engine.

Three consequences.

**The fairness gate can never fire.** `project.fairnessSensitive` is written by nothing on the
server. The only writers in the repository are `ingest.js:105` (the legacy browser ingest path)
and two hardcoded `false` entries in the demo fixture `data.js`. `signals.js:620` states the field
"is left" unset. So `fairnessGateRequired` is always `false`, the fairness checkbox is never
rendered, and `wireDecisionControls`'s gate on it is dead. The server module that reads the same
concept (`models_decision.py:81`, `si["fairnessSensitive"]`) is reading one of D1's eleven
unobtainable keys, so the gate is absent on both sides for the same reason.

**"Conflict" says one honest thing and the card presents it as a finding.** `classifyConflict`
returns `"Signal breakdown not available"` for a stored-only project, which is correct and
deliberate (`decision.js:135-140`), and the card prints it in a field labelled `Conflict` beside
three fields that do carry content. That is a display choice, not a defect, but it is the only
place on the card that admits the card is not reading the analytical layer.

**This is the surviving half of the defect T6 Part 3 fixed.** That work removed the browser-side
*status* derivation and left the browser-side *recommendation* derivation in place. The status is
now the server's; the recommendation never was.

---

### D7.3. The XLSX export reads a different store from the screen beside it

| | |
|---|---|
| **Stage** | 7 |
| **Where** | `assets/js/export.js`; button at `app.js:1644`, handler at `app.js:1703` |
| **Reachable** | Today, from the same card as D7.2 |
| **Reaches a user** | **Yes**, as a spreadsheet they will circulate |

`export.js` is loaded by `index.html:1159`. Its entire input is `project.history` — the legacy
snapshot array written by `signals.js:387` and `:498` — and **not** `computed_results`:

```javascript
const snapshot = (project.history && project.history.length)
  ? project.history[project.history.length - 1] : null;
if (!snapshot) { alert("No snapshot available. Run signal extraction first."); return; }
```

For a server-computed project, `project.history` is empty, so the export **refuses with a message
naming a step ("Run signal extraction first") that does not exist on the current path**, on a
project whose analysis has in fact been run and whose result is displayed on the same screen. That
is a mismatch between the export and the screen, in the safe direction: it produces nothing rather
than producing the wrong thing.

Where `project.history` *is* populated (a legacy project carried over from the Apps Script era),
the export ships numbers from a store nothing has written since T6 Part 3, beside a screen showing
the server's. Sheet 1's Signal Inputs, Sheet 2's category and module statuses, and the executive
brief all come from that snapshot. The two can differ arbitrarily and nothing reconciles them.

Two further things about this file, both minor beside the above:

- **Sheet 3 is a cross-period trend built from stored snapshots.** This is the second half of the
  audit's open question (see "The three open questions" below). Its column headers are `"Cat 1
  EVM"` through `"Cat 8 Governance"` and `"Overall"` — **module and category numbering in
  user-facing text**, which `NAMING_AUTHORITY.md` section 4 forbids without qualification. The
  Methods tab sweep (T15) removed 101 rendered ids and did not reach this file.
- `deriveActionPlan(project)` is called into Sheet 1 inside a `try` whose `catch` is empty, so the
  action plan is derived client-side and its failure is silent by design.

The sibling JSON export at `app.js:1681` (`buildAuditRecord`, `decision.js:419`) has the same
shape: it stamps `pceif_version: PCEIF_VERSION` — the retired name, in a file a user downloads —
records `signal_package: project.signals` (the legacy blob, empty on server-computed projects),
and takes `reporting_period` from `project.reportingPeriod`, which server-created projects do not
carry. Its filename template is `audit_${p.id}_${p.reportingPeriod}.json`.

---

### D7.4. Every display surface reads period 1 by name; correctness depends on the server ignoring it

| | |
|---|---|
| **Stage** | 7 |
| **Where** | `assets/js/workspace.js:396, 432, 540, 593, 642`; `assets/js/decision-ui.js:322, 323` |
| **Reachable** | Today |
| **Reaches a user** | **Not today for research projects.** See below. |

**This answers the audit's P5.** Every client call that names a period names `1`, hardcoded:

```javascript
workspace.js:396   call("projectcompute",       { id: pid, period: 1 })
workspace.js:432   call("projectuploadstatus",  { id: pid, period: 1 })
workspace.js:540   call("projectupload",        { id: pid, period: 1, documents })
workspace.js:642   call("projectresults",       { id: pid, period: 1 })
decision-ui.js:322 call("projectresults",       { id: pid, period: 1 })
decision-ui.js:323 call("projectuploadstatus",  { id: pid, period: 1 })
```

`workspace.js:740` is the one exception, passing `p.period || 1` from the project list.

**For a research project this is harmless, and the reason matters.** `_resolve_period`
(`documents.py:128-151`) ignores the payload entirely whenever a research assignment exists and
returns the participant's server-derived current period. So the client's `1` is discarded and the
correct period is served. The property "no surface shows a result under the wrong period" holds
today **because the server overrides the client, not because any client passes the right value**.
If `_resolve_period`'s research branch were ever relaxed, six call sites would immediately start
reading and writing period 1.

**For an operational project the payload IS used**, and `workspaceprojects` also calls
`_resolve_period(project, {})`, which returns `1`. So an operational project holding results for
periods 2 and above — reachable, because P2 established the period is caller-declared and
unbounded on that path — is displayed as "Period 1" in the project card (`workspace.js:232, 322`)
and its later periods are unreachable through the interface. Nothing shows the wrong number; the
later periods are simply invisible, and the card asserts a period that is a default rather than a
fact.

**The detail panel never shows a period at all.** `renderProjectDetail`'s provenance line
(`workspace.js:718-723`) prints computed-at, simulation version, seed, period cutoff and the
supersession note. `_result_view` returns `"period": row.period` and no surface renders it. So a
reader has no way to tell which period they are looking at, and the one field that would let them
check is available and dropped.

**The assistant prints a different period from a different store.** `assistant.js:41` prints
`period ${p.reportingPeriod}` — the legacy document field (a `YYYY-MM` string), not
`ComputedResult.period`. The T12b comment above it records that server-created projects carry no
`reportingPeriod`, and absent fields are correctly omitted rather than printed as `undefined`. So
today the assistant prints no period on a server-computed project. On a legacy project it prints
one that has no relation to the period of the result it is describing.

---

## The three open questions the audit raised, answered

**1. Can any display surface show a result under the wrong period?**
**Not today, and not by design.** Six of the seven client call sites name period 1 unconditionally
(D7.4). The property holds only because `_resolve_period` overrides the payload for exactly the
projects where it matters. No surface displays the period it is showing, so a reader cannot
verify it. I did not find a path that renders a period-N result under a period-M label.

**2. Does any display surface build a cross-period trend from stored results?**
**Two do, and neither reads stored results.**

- `export.js:139-161`, Sheet 3 "Signal History", one row per period, from `project.history`.
- `detail.js:534-576`, the "Period Comparison" panel, rendered at `detail.js:926`: a delta table
  for the last two periods and CPI/SPI/doc-risk sparklines across every period, from
  `storedHistory(project)` (again `project.history`) and `project.milestoneHistory`.

Both read the legacy client-side snapshot store, which nothing on the current path writes. The
detail panel degrades honestly: with fewer than two entries it renders "Longitudinal view unlocks
after two reporting periods", which is what every server-computed project sees. **So the answer to
"if a display surface builds one anyway, from what" is: from `project.history`, a store the
analytical layer does not write and `computed_results` does not feed.** Nothing assembles a trend
from `computed_results`, on the server or in the browser.

**3. What supplies `compute_portfolio`'s `history` argument on the server path?**
**Nothing. It is the literal `None` at `documents.py:326`, and there is no second caller.** Fully
covered as D7.1 above.

---

## Stage 7, generally

**Where a displayed number is recomputed client-side rather than read from the stored row:**

| Surface | Number | Source |
|---|---|---|
| Decision card, `app.js:1605` | recommended action, authority, documentation, fairness gate | derived, `decision.js` (D7.2) |
| Decision card | conflict type | legacy blob, abstains honestly |
| Executive brief, `detail.js:1075-1145` | P80 EAC vs BAC percentage, CPI/SPI band, CUSUM verdict, doc-risk band | recomputed from `project.signals` / `project.signalInputs` with thresholds hardcoded in the browser (`cpi < 0.90 ? "Red" : cpi < 0.95 ? "Amber"`) |
| Executive brief | category grouping | `LinSignals.buildCategorySnapshot(project)` built on the fly when the stored snapshot lacks category fields |
| XLSX export | everything | `project.history` (D7.3) |
| JSON audit export | signal package, derived decision, action plan | legacy blob + client derivation |
| Period Comparison, `detail.js:534` | CPI/SPI/doc-risk deltas, red-module count, milestone slip | `project.history`, `project.milestoneHistory` |

The `detail.js` executive brief is the one I am least sure about. It is gated on the legacy blob
being present at several points and reads `project.signals` throughout, so on a server-computed
project most of it should produce nothing; I did not drive the page to confirm which of its
branches render empty and which render a number. **Treat the executive brief row as UNCONFIRMED
for reachability**, and note that if it does render, its thresholds are a second, independent set
of bands from the server's.

**Correct, and worth stating.** `taxonomy.js`'s `LinResults` layer is clean: it caches a stored row,
deliberately cannot fetch, and `getModuleStatus` / `getCategoryStatus` / `getProjectFusion` read
the row and fuse nothing. `deriveHealthState` has no fallback derivation and returns "Awaiting
analysis" rather than a colour. The assistant (`assistant.js:69-79`) explicitly refuses to supply
per-signal figures it does not have and says so to the user. `workspace.js`'s detail panel renders
group names, never module ids, and labels Group C entries "informational, does not contribute to
project status". The recommendation is never rendered on the workspace detail screen at all, so
the pre-lock redaction has nothing to leak around there.

**Where a label is derived rather than stored.** The five portfolio module names are translated in
the browser from the stored `cat8_N_*` keys (`workspace.js:772-780`), and the analogous
`categoryName` / `moduleName` lookups map stored ids to display names. That is the correct
direction — the store keeps the id, the display resolves the name — and I found no case of a label
being invented rather than looked up. The one exception is `deriveDecision`'s `authority` and
`documentation` strings, which are composed in the browser and are not labels for anything stored
(D7.2).

**Where the export could differ from the screen.** D7.3 in full. Both export paths read a
different store from every screen. Both also still carry no notice, attribution or copyright,
which T16 flagged and which remains open and is a liability decision, not a defect to fix here.

---

## Stage 8, audit trail and logging

### What events exist, and what writes them

**Two independent event stores, and they are not connected.**

**1. `audit_events` — the research audit trail.** Append-only by construction: the model's
docstring says so, `research_identity.audit()` (line 73) only ever `session.add(...)`s a row,
`server_ts` comes from the column default and never from a caller, and `participant_id` /
`scenario_id` are deliberately not foreign keys so a row survives the deletion of what it
describes. There are **84 `audit(session, ...)` call sites across the server writing 66 distinct
event types**, covering identity, consent, assignment, membership, the decision sequence, expert
references, features, exports, and every refusal path. `research_audit.record_rejected_write`
additionally writes on **its own connection**, so a trigger rejection is durably recorded even
though the caller's transaction unwinds — the reasoning is in that module's docstring and it is
sound.

**2. `doc["events"]` — the legacy per-project event list.** A JSON array inside the project
document, appended by `writes.py:_append_event`. Event types include `project_created`,
`signals_extracted`, `signals_reset`. This is the store the facade's `getslim` counts to produce
`docCount` (`facade.py:116`).

### Are events recorded, or not recorded at all?

**They are recorded. C1.4 Audit Trail Completeness is unwired, not lied to.**

This answers the audit's question directly. The eleven unobtainable keys are the keys
`extraction_merge.SIGNAL_INPUT_KEYS` can emit into `signalInputs`, and `events` is not among them.
But the events themselves exist in two places, both populated. C1.4 reads `si["events"]`, finds
nothing there, and reports "0% audit trail completeness, 0 events recorded" about a platform whose
`audit_events` table is one of the best-maintained things in the repository.

**So the finding is: a Group C module reports a false zero about a real and healthy store, because
nothing plumbs either store into `signalInputs`.** It is a wiring gap, not a missing capability.
That matters for how it gets fixed — the work is a merge-layer branch, not building an audit
trail — and it matters for the claim itself: the report "0 events recorded" is false, not merely
uninformed.

The same is true of C1.7 Reporting Frequency Index, which reads the same key.

### What mutates rather than appends

The append-only discipline holds where it was designed to and does not hold in the legacy facade.

**Holds:**

- `computed_results`: a recompute INSERTs and sets `superseded_by` on the old row, which stays
  readable forever. Once a submitted decision references a row, the migration 0009 trigger rejects
  every UPDATE except setting `superseded_by`. Verified by `test_documents_b7b.py:417-432`.
- `decisions`: the pre-judgment lock trigger (0009) and the `ck_decisions_reveal_after_pre_lock`
  CHECK. Three modification paths tested and rejected in `test_pre_lock_guard.py`.
- `expert_references`: the same mechanism with its own SQLSTATE. Four routes tested.
- `audit_events`: nothing updates or deletes it anywhere in the application. I grepped for it.
- `project_members`: revocation sets `revoked_at` (`research_membership.py:320`) and keeps the
  row. A soft delete, and the test asserts the row survives.

**Does not hold, all in `writes.py`, all on the legacy facade path:**

1. **`w_resetsignals` DELETES from the event log.** It rebuilds `fresh["events"]` keeping **only**
   `signals_extracted` entries, discarding `project_created` and every other prior event, then
   appends `signals_reset`. The code comment explains why `signals_extracted` is preserved
   (`docCount` depends on it) and does not address the deletion of everything else. **This is the
   clearest append-only violation in the codebase: a write action that truncates the project's own
   event history.**
2. **`w_saveportfoliohealth` DELETEs prior snapshots** (`writes.py:446`, `session.delete(old)`) to
   keep exactly one current portfolio-health row. The comment says this "matches the live model,
   which keeps a single portfolio_health.json at the Drive root" — a deliberate reproduction of the
   Apps Script, and the only outright `session.delete` on the server.
3. **`w_save` and `w_overwritesignal` replace `project.doc` in place**, bumping `record_version`.
   The prior document is not retained anywhere. Optimistic concurrency is enforced (`StaleWrite`),
   so a lost update is refused, but the previous state is gone. `w_overwritesignal` appends an
   event recording the field and the from/to values, which is the only trace.
4. **`w_setprojectnumber` rewrites the project id.** The old id no longer resolves; the check at
   `writes.py:300-303` asserts exactly that.

None of these touch `computed_results`, `decisions` or `audit_events`, so the **research** record
is not affected. They are the operational/legacy surface. That distinction is real and worth
keeping, but "the platform's stated discipline is append-only" is not true of the whole platform.

### Can a stored decision be traced to the exact evidence, recommendation and code version?

**Evidence: yes.** `Decision.result_id` names the exact `computed_results` row, and that row is
frozen by a trigger from the moment `pre_submitted_at` is set. `ComputedResult.source_documents`
(migration 0013) names the document versions that produced it, by `document_id` and `sha256`, so
"which version of the pay application produced this status" is answerable even after the period's
document set has moved on. `projectresults` accepts an explicit `result_id` so a superseded row
still resolves. This is the strongest part of the whole record.

**Recommendation: partially, and the gap is D7.2.** The *research* recommendation — the decision
support package — is traced properly: `Decision.package_id` plus `package_hash`, copied at reveal
time, so an edited package makes the affected decisions identifiable rather than silently
reinterpreted. But the recommendation on the **operational** project detail page is derived in the
browser at render time and stored nowhere (D7.2). For that surface, what was recommended at the
moment of a decision is reconstructible only by re-running the browser code of the day against the
stored status.

**Code version: no. This is the significant gap in stage 8.**

`ComputedResult.simulation_version` is NOT NULL and is taken from the run rather than defaulted,
which is right. But its value is a hand-maintained constant:

```python
# server/app/simulation/models.py:32
SIMULATION_VERSION = "sim-2026.07-v1"
```

It is a string a person edits. **Nothing ties it to the code.** Every module body in
`server/app/simulation/` could change today and every result computed after the change would carry
the same `sim-2026.07-v1` as every result computed before it. The model's own docstring states the
purpose — "a later change to the analytical layer becomes undetectable in already-collected data"
— and a hand-edited constant does not achieve it; it achieves it only if every change to the
package is accompanied by a discipline nothing enforces. There is no git sha, no build id, and no
checksum of the package anywhere in a stored row. `seed` and `period_cutoff` genuinely pin the
inputs, so a result is reproducible *given* the code; identifying *which* code is the missing link.

**And the research export cannot join a decision to its result at all.** `EXPORT_COLUMNS`
(`research_export.py:45-92`) carries `package_id`, `package_version` and `package_hash`, and
carries **none of** `result_id`, `simulation_version`, `seed`, `period_cutoff` or
`project_status`. The allowlist is the right design and the omission is presumably deliberate
de-identification caution, but the consequence is that the analysable dataset cannot answer "what
did the analytical layer say to this participant at this moment" without going back to the live
database. For a study whose independent variable is AI decision support, the support that was
shown is not in the export.

### Also worth recording

- **`export_checksum_mismatch` is audited and the payload is withheld** (`test_export.py:275-281`).
  The export payload is regenerated on fetch and compared against a stored checksum rather than
  stored as bytes, so underlying rows changing after an export was taken is *detected*. That is a
  stronger property than a stored blob and it is worth not losing.
- **No wall-clock reads in the analytical layer.** `test_simulation.py:178-185` scans every file in
  `server/app/simulation/` for `datetime.now(`, `time.time(`, `date.today(`, `datetime.utcnow(` and
  asserts none. That check can fail and is a good one. The clock re-enters through `period_cutoff`
  when no document carries a parseable date, which is the audit's D3 and is unchanged.
- **`buildAuditRecord` stamps `exported_at: new Date().toISOString()`** in the browser, so the
  downloaded JSON audit record's timestamp is the client clock. Nothing else in the record is
  server-assigned.

---

## What I could not establish

- **Whether the `detail.js` executive brief renders anything on a server-computed project.** It is
  guarded on the legacy blob in places and reads it unguarded in others. This needs the page
  driven in a browser. Listed as UNCONFIRMED in the stage 7 table above.
- **Which routes render the decision card and the export buttons for which account type.**
  `renderDecisionCard` returns early when `#decision-card` is absent and its comment says the
  portfolio no longer hosts it, "only the detail page does". I did not confirm whether a research
  participant reaches that detail page or only the workspace surfaces. **If they do not, D7.2 and
  D7.3 are operational-only.** That is the single most useful thing for a next session to settle,
  because it decides whether D7.2 reaches a research participant.
- **Whether any legacy project with a populated `project.history` exists in production.** D7.3's
  wrong-numbers case needs one. Production was not inspected and must not be.
- **Whether `w_resetsignals`'s event truncation has ever run against a real project.** The action
  is live and PM-gated; I did not look for evidence of use.
- **The stage 6 question the audit left open** — whether a snapshot can change underneath a stored
  decision by a route other than P1 — is still open. I did not reach it.

---

## Summary

| # | Stage | Reachable today | Reaches a user | Test covers it |
|---|---|---|---|---|
| D7.1 | 7, 6 | yes, always | yes, a green dot from no data | no; the nearest check asserts only that five results exist |
| D7.2 | 7 | yes, detail page | yes, the whole recommendation | no |
| D7.3 | 7 | yes | yes, as a refusal today; as wrong numbers on a legacy project | no |
| D7.4 | 7 | yes | not today; the server override is what prevents it | no |
| Stage 8, events unwired | 4, 8 | yes, always | yes, C1.4 reports a false zero | no |
| Stage 8, `w_resetsignals` truncates events | 8 | yes, PM-gated | indirectly | partially: `test_writes_a1b.py:156` asserts what survives, nothing asserts what is lost |
| Stage 8, `simulation_version` is a hand-edited constant | 8 | yes, always | no; it degrades the research record | no |
| Stage 8, `result_id` absent from the export | 8 | yes | no; it degrades the analysable dataset | no |

**D7.1 and D7.2 are the two I would act on first.** D7.1 because a permanently Green dot on a
module that has declared its own insufficiency is the exact failure the platform's "loud refusal
over quiet approximation" rule exists to prevent, and the fix is a display change, not an
analytical one. D7.2 because the platform's standing description says it "presents a
recommendation that a project manager records a decision against" — and on that surface the
recommendation is not the one the analytical layer computed.
