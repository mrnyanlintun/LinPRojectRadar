> **READ `NAMING_AUTHORITY.md` BEFORE ANY CONTENT WORK.** It is the authority for what the platform
> and its analytical taxonomy are called, and it carries the standing description that every
> user-facing surface quotes verbatim. It lives in the repository so it cannot fail to reach a
> session, which it did three times while it lived outside. Read it before this handoff, not after.

> **SECTION NUMBERING IS RETIRED, from 2026-08-02.** Five sessions collided on T-numbers in one
> day (T21 taken twice, T23 renumbered from T21, T24 taken twice, T26 renumbered from T24 at
> merge time). New sections are headed **`# <yyyy-mm-dd> — <task name>`** and appended at the TOP,
> newest first. Never renumber an existing section; on a merge conflict keep both sections whole.
> The historic T-numbered sections below keep their names as history.

# 2026-08-02 — THE BLANK DETAIL PAGE FIXED; MAP AND GLOBE HAVE NOTHING TO PLACE

Full detail in `REPORT_2026-08-02_detail-page-and-markers.md`. **1159 checks across 22 suites,
`tests.html` 51/51, `tests_render.html` 37/37.** Playwright + pre-installed Chromium; compositing
proven first. No `preview_start` tooling exists in this container.

**MAP AND GLOBE, the lead: the render path is HEALTHY and the #198 fix is intact — verified in a
browser by giving two throwaway projects fixture coordinates, placing both, forcing the exact slim
refresh that used to strip locations, and watching both markers survive (store rows slim:true and
still carrying lat).** The remaining explanation is that **the projects have no coordinates**:
`projectcreate` with a real address in this container yields `lat: null` and geocodeError "The
location service could not be reached…", Nominatim being unreachable through the proxy, so no
session has ever produced a live geocode. **Stopped there as instructed — nothing was backfilled;
production not inspected.** The one-look test for Lin: open a project on Render and read either
"Matched to: …" or the geocode error; if the latter, re-saving the address retries it. Also worth
knowing: `w_save` on a CHANGED address re-geocodes, and an unreachable geocoder then **erases**
existing coordinates rather than keeping them.

**THE BLANK PAGE IS FIXED.** `populated` was `hasSignals(p)` gating the provenance line; its
correct value now is the stored-row gate its two siblings got in T12b:
`const populated = !!(window.LinResults && LinResults.hasResult(p))`. Detail renders for BOTH
account types (operational: full page, Red badge, provenance line, 11 sections; research: full
page, honest "Awaiting analysis"). Screenshots looked at, not just taken.

**THE CATCH AT `showPage` NOW REPORTS.** Navigation still wins, and a caught render error goes to
`console.error` (the existing per-item render shape) AND `LinStore.banner(..., "warn")` (the
existing user-visible non-fatal shape, role="status"). Proven live with an injected fault: banner
text shown verbatim, Handbook still navigable.

**`tests_render.html` NOW ACTUALLY CALLS `LinDetail.render`** (group 3b, into the real
#detail-root; the harness had the element and never loaded detail.js). Proven able to fail by
restoring the dangling reference: 33/37, exactly the four new assertions red. Group 3's misleading
"The detail page State badge renders" heading is corrected to what it checks, a pure label helper.

**D1.3 ABSTAINS BY ABSENCE.** `portfolio.py` no longer emits the Trajectory Classifier with a
colour beside `insufficient_data: true`; with no usable history it is absent from the snapshot's
results, matching the project-level contract. With real history it computes unchanged (verified
directly: Red, "CPI trend: -3.3% per period"). **The task named portfolio.py, so the standing
simulation/ prohibition was overridden for that one file only.** On screen the portfolio panel now
shows four rows and no green-dot-from-nothing. `test_workspace_t3t5` Guarantee 9 upgraded from a
bare `== 5` count to named-key assertions plus "no sub-result carries a colour and an
insufficiency flag together" — all three proven to fail (49/52) with the fault restored. Note the
server path still passes `history=None`, so D1.3 currently abstains on every snapshot; it starts
reporting if the portfolio path ever gets the `_period_history` treatment.

**REPORTED NOT FIXED: fixing the blank page brings D7.2 back.** The Governance Decision card
renders again and is still the browser-derived four-branch `if` — seen live: badge Red beside an
action plan reading "All categories Green → Routine monitoring" on the same card. The stages 7–8
finding stands; it was moot only while the page was blank. Also: the provenance line prints module
ids ("A1.1 Monte Carlo EAC Forecast") in user-facing text, against NAMING_AUTHORITY, pre-existing
and visible again now the page renders.

---

# T26 — THE PROJECT DETAIL PAGE IS BLANK, AND THAT IS WHY NOBODY SEES THE BROWSER-DERIVED RECOMMENDATION. BROWSER-VERIFIED. READ-ONLY.

Full detail in `REPORT_2026-08-02_decision-card-routing.md`. **No code, no test and no data was
modified.** Driven with Playwright against the pre-installed Chromium and `dev_serve.py` on 8010;
compositing proven first (`visibilityState: "visible"`, **62 rAF frames/s**). **There is no
`preview_start` tooling in this container**, so the `Demo` trap could not arise.

**`assets/js/detail.js:894` references `populated`, which does not exist.** Commit `062731b`
(T12b, the hasSignals sweep, 2026-08-01) deleted `const populated = hasSignals(p);` and rewrote
two of its three uses. The third survived, inside the template literal that builds
`root.innerHTML`, so **`LinDetail.render` throws before assigning anything and the project detail
page has rendered header-and-footer-with-nothing-between for a day.** Measured on both account
types; screenshot in the report. **`showPage`'s `try/catch` at `app.js:1868` swallows it**, which
is why the console is clean and the page is empty.

**THAT ANSWERS T23's OPEN QUESTION, and not in either direction it anticipated. NOBODY sees the
browser-derived recommendation.** `renderDecisionCard` has exactly two mount points: its default
root `#decision-card`, **which does not exist in `index.html`** (so it returns at line one), and
`detail.js:988` on the page that no longer renders. `.dc-field` count in the live DOM, both
account types, every route: **0**. The four derived strings ("Recovery-plan review and management
escalation", "Program director / PMO", …) appear **nowhere**. So D7.2 is not a research-instrument
problem and not a live operational defect; it is unreachable code behind a blank page. **The blank
page is the live defect.**

**WHAT A PARTICIPANT ACTUALLY SEES AS THE DISCLOSED RECOMMENDATION: the frozen
`DecisionSupportPackage`, printed verbatim from the server.** Every field in the revealed panel
carried the `PKGMARK` markers planted in the seeded package. **Note carefully: that is not the
browser's recommendation and it is also not the 36 Group B computations'** — it is a
researcher-authored artefact from `adminpackagecreate`. The analytical layer reaches the
participant through the *evidence* panel above the judgment form instead. Whether the frozen
package is meant to be the disclosed recommendation is a design question, not a defect.

**`tests_render.html` cannot catch this, and it is the harness written to.** Its group 3 is headed
"The detail page State badge renders" and calls `LinApp.stateLabel(p)`, a pure function; its group
2 renders the decision card into a synthetic host, bypassing the page. **Nothing anywhere calls
`LinDetail.render`.** This belongs in the vacuity sweep and was not in it.

**THE ABSTENTION QUESTION, and the answer is better than feared except in one place.**
**Abstaining project-level modules are absent from `module_results` entirely** — the stored row
carries 47 of 95 modules, **0 with `insufficient_data`, 0 with a null `status_color`** — so an
abstention *disappears* from a surface rather than rendering Green. No rendered dot on any surface
carried the `--status-nodata` colour. **So making modules abstain WOULD work on every
project-level surface.** The exception is `portfolio.py`, the only path that emits a colour and an
insufficiency flag together: **"Signal Trajectory Classifier | No history available | GREEN dot"
seen on screen** on both operational projects. The distinction is not which surfaces read the flag
(none do) but which code paths emit a colour beside one.

**WHAT A RESEARCH PARTICIPANT SEES FROM D1, on the evidence screen, before committing anything:**
five B2 modules Amber with the text "Insufficient signal data"; Audit Trail Completeness **Red**,
"0 events recorded"; Reporting Frequency **Yellow**, "no documents uploaded yet" — on a screen
that lists the uploaded document by filename fourteen rows below. The D1 fabrications reach the
person whose judgment is the dependent variable.

**ALSO FOUND, for Lin rather than for a session:** before the lock, the Regret Minimization Index
evidence row withholds its prose ("This module's finding is withheld until…") **and still shows
its Red dot**. `decision-ui.js:373` colours every row unconditionally and the server redacts
`evidence_metric` only. `test_decision_ui_t4`'s leak markers are prose, so on the face of it they
do not cover a colour; I did not run the injection that would settle it.

**MEASURED AT `a5c3da7`; RE-VERIFIED AT `c05d028` AFTER T25 MERGED.** The blank page and the D1.3
green dot both survive T25 unchanged, and abstentions are still absent from `module_results` (36 of
95 stored now, still 0 carrying the flag, still 0 with a null colour). **T25 supersedes the specific
fabrication strings I recorded a participant seeing** — the five B2 Ambers and C1.4's "0 events
recorded" are fixed; C1.4 now reads "Amber, 50% audit trail completeness, 1 events recorded". Read
that part of the report as the record of what they looked like, not as live. **T25 does not touch
`portfolio.py`**, so D1.3 is now the only place emitting a colour and an insufficiency flag together.

**NOT ESTABLISHED:** whether the admin route or `research/deepdive.html` render a card (neither
reached in a browser; no source reference in `admin.js`/`admin-ops.js`); whether anyone opened the
detail page between `062731b` and now; whether the blank page differs on a project with no stored
result. Production not inspected.

---

# T25 — D1 IMPLEMENTED. THE OBTAINABLE KEYS WIRED, THE REST ABSTAINING.

Full detail in `REPORT_2026-08-02_d1-implementation.md`. **1157 checks across 22 suites**;
`tests_render.html` **33/33**, `tests.html` **51/51**. No stored data altered, production not inspected, `assets/`
untouched. Lin's decision: option 3 where the data exists, option 1 everywhere else.

**T22'S COLOUR ANSWER WAS WRONG AND IS CORRECTED HERE. PROJECT COLOUR DOES MOVE.** Measured
against the test suite's own fixtures rather than a hand-built variant: **healthy Red to Green**,
**on-budget Amber to Green**, distressed Red to Red. **A healthy project was being reported as
RED**, because with no `spiHistory` A1.2 synthesised twelve observations from the current SPI and
drew a control chart over them; a project running ahead of plan drifts from the control target, so
the chart breached, A1.2 went Red, category A1 went Red, and the project went Red. Direction
matters: healthy improves, distressed's B2 gets **worse** (Amber to Red), distressed stays Red.
Nothing softens a bad project.

**END TO END, THE BIGGER RESULT IS C1.4.** Across three real periods: **C1.4 Red to GREEN in every
period** — it was reporting "0 events recorded" about a platform that has recorded events in
exactly that shape since `_append_event` was written. **Four modules that never computed now
compute** (Kalman, ARIMA, Regression to Mean, and CUSUM on real data, where at period 3 it
disagrees with its own fabrication: red becomes amber). **Category C1 now improves as the record
builds**, Amber to Yellow to Green, where it was frozen by an immovable Red.

**Abstaining: 48 of 95 before, 60 if everything abstained, implemented 58/55/54 at periods 1/2/3.**
The count FALLS as history accumulates, because wiring gives evidence back. Twelve fabricated
verdicts per stored result before; two or three of the twelve compute from real evidence after.

**WIRED** in `documents.py` (not in `assemble_signal_inputs`, which must stay pure): `events` via
`_events_as_of`, `spiHistory`/`cpiHistory` via `_period_history`. **ABSTAINING**: the eight legacy
browser-blob keys. Every fabrication path DELETED — `derive_series`, `hash_seed`, R0, the five
AMBER stubs, Rough Sets' `or 1`. `insufficient()` reused; no new abstention form.

**NO LEAKAGE, and P1 IS NOT ENLARGED.** `_period_history` filters `period < period`, so recomputing
period 1 with 2 and 3 stored reads neither. The event log is truncated at the period cutoff for the
same reason C1.2 takes its "now" there. Both asserted, both fault-injected.

**`milestoneHistory` STILL CANNOT BE SUPPLIED; A2.7 still abstains, correctly.** `milestones_json`
is requested from the extraction model but is not in `ALL_FIELDS`, so it never reaches
`signalInputs`. Merge-layer work, not this task.

**TWO GAPS FOUND, REPORTED NOT FIXED. (a) No `signals_extracted` event is written on upload** by
any current code path, so C1.4 is truthful about a log thinner than it should be; fixing it changes
the user-facing **docCount**, which `facade.py` derives from that event count — Lin's call.
**(b)** `_js_date_ms` refuses datetime strings by design while `_append_event` writes them, so
`_events_as_of` narrows `at` to its date part at the boundary; without that C1.7 would abstain on
every real project while LOOKING wired.

**VALIDATION.md**: all twelve exact-match rows kept, each annotated `D1: DIVERGES`, plus a banner
stating that a matched row establishes only that the server computes what the JavaScript computed,
not that the module is correct.

**NEW SUITE** `server/tools/test_d1_module_inputs.py`, 100 checks, **nine faults injected**
including the two that leave the code looking correct (date narrowing removed; history reading all
periods). **Three more vacuous checks were caught by that injection** — `all()` over an empty list
— which is the fourth session running. **The pre-existing 1013 checks passed with every change in
place before a single new test was written**: the suite could not detect twelve removed
fabrications, one of which was turning a healthy project Red.
---

# T24 — Notice and copyright revision. DONE. One question back to Lin.

Full detail, with the live text quoted from the rendered browser page, in
`REPORT_2026-08-02_notice-revision.md`.

**The approved copyright paragraph and the approved university sentence are live everywhere.**
`DISCLAIMERS_DRAFT.md` section 3 is the source; `server/tools/test_disclaimers.py` (now **90
checks**, up from 62) fails if any of the six surfaces diverges from it by a character.

**Three things are retired and must not come back**, and the check fails on the exact strings:

- `the associated framework` in the copyright. `NAMING_AUTHORITY.md` says there deliberately is no
  framework and the About page says so in prose; the copyright asserted one existed.
- The trademark symbol. It is `Opus Gubernatio`, never `Opus Gubernatio™`.
- The attribution as a **title block**. It is now a **sentence** that states what the relationship
  is not: "The university is not a party to this notice and does not endorse or warrant the
  platform." A bare degree-and-school block sitting under a liability disclaimer read as though
  the university were issuing the notice. The sign-in box's middot line had the same defect.

**Nine surfaces carried the text, in six wordings. Lin had seen two.** Two more were found: the
**access-denied panel's** `GWU Doctor of Engineering Praxis, Nyan Lin Tun`, the shortest form of
the same defect; and **four developer-facing pages** (`calibration/verify.html`,
`tools/export_lib.html`, `tests.html`, `assets/visualizations/pceif_neural_signal_flow.html`) each
carrying one locally-invented sentence that fused the attribution with the advisory statement.
All now carry approved sentences only. **Nothing was composed.**

**THE ONE QUESTION BACK TO LIN, in the report's section 2.** The approved block's three notice
paragraphs ARE the existing operational variant, character for character. They are not the
research variant. **The research variant was NOT replaced**, because doing so would delete "All
project data is synthetic" and the do-not-upload restrictions from every participant-facing
surface, and removing liability language is composing it. If Lin intended the research variant
retired, that is a five-line change awaiting her word.

**Still flagged, not changed, all needing Lin's judgement:**

- The **access-denied panel's own one-line notice**, `Access restricted to authorized use. This
  platform is an academic proof-of-concept; no warranty is provided.` A third notice variant,
  never approved, and it does not switch on account type, so an operational user who fails sign-in
  is told the platform is an academic proof of concept.
- **Both export paths still carry no notice, attribution, or copyright.** Confirmed, not assumed.
  Unchanged since the last handoff said so.
- The sign-in box's **short copyright** line stays short, per the task.
- The **`<meta name="description">`** asserts the domain scope `public AEC capital programs`,
  which `NAMING_AUTHORITY.md` section 3 deliberately keeps out of the standing description.
- **`ds_defensibility_data.js`** carries three strings asserting a framework exists and is being
  evaluated, while the same file's lead string correctly says "not a new governance framework".
  Research-methodology prose about the praxis design, so not a session's to rewrite.
- The **`Methods and Framework`** tab label, in three files and eight strings.

**Suites: 1057/1057 across 21 suites**, `tests.html` 51/51, `tests_render.html` 33/33.

**Run each server suite against its own fresh database.** Six of them collide on shared state
(`action_families` unique constraint, `pseudonymous_code already in use: T3T5-PM`, `duplicate
column name: secret_side_channel`) and all six pass when isolated. Fixture collisions, not
defects, but they will look like a real failure to the next session.

---
# T23 — STAGES 7 AND 8 AUDITED, AND THE SUITE SWEPT FOR CHECKS THAT CANNOT FAIL. READ-ONLY.

Two reports, both committed: `REPORT_2026-08-02_stages-7-8-audit.md` and
`REPORT_2026-08-02_vacuity-sweep.md`. **No code was modified and no test file was edited.** T20's
stage 7 and stage 8 gaps are now closed; its three named UNKNOWNs are answered.

**THE THREE OPEN QUESTIONS, ANSWERED.**

**What supplies `compute_portfolio`'s `history`? Nothing.** `documents.py:326` passes the literal
`None` and there is no second caller, so both `len(history) >= 2` guards are permanently false.
**Executed: D1.3 Signal Trajectory Classifier returns `status_color: "Green"` on every project
forever**, with `insufficient_data: true` and `"No history available"` beside it — and
`workspace.js:750` renders the colour dot and the evidence sentence and **reads neither
`insufficient_data` flag**. A green dot from no data, the same shape as D1's Rough Sets except
that here the module declares its abstention and the display discards it. D1.5's composite anomaly
score is likewise always missing its trend term (`scores` is always the three-element list).

**Can a surface show a result under the wrong period? Not today, and not by design.** Six of the
seven client call sites name `period: 1` hardcoded (`workspace.js` 396/432/540/593/642,
`decision-ui.js` 322/323). It is correct only because `_resolve_period` discards the payload for
research projects. **The property holds because the server overrides the client, not because any
client passes the right value.** No surface displays the period it is showing; `_result_view`
returns it and nothing renders it.

**Does a display surface build a cross-period trend? Two do, from `project.history`** — the legacy
snapshot store nothing has written since T6 Part 3 — not from `computed_results`. `export.js`
Sheet 3, and the "Period Comparison" panel at `detail.js:534`, rendered at `detail.js:926`.

**THE TWO TO ACT ON FIRST:** D7.1 above, and **D7.2, the recommendation shown on the project
detail page is derived in the browser, not read from the stored row.** `renderDecisionCard`
(`app.js:1605`) reads the stored *status* correctly and then computes action, authority,
documentation and the fairness gate from it with a four-branch `if` in `decision.js`. The 36
Group B computations never reach it. **The fairness gate can never fire**: nothing on the server
writes `project.fairnessSensitive`, and the server module reading the same concept is reading one
of D1's eleven unobtainable keys. T6 Part 3 removed the browser-side status derivation and left
the browser-side recommendation derivation in place.

**STAGE 8. Events ARE recorded; C1.4 is unwired, not lied to.** `audit_events` is genuinely
append-only (84 call sites, 66 event types, own-connection writes for trigger rejections), and
`doc["events"]` exists besides. `signalInputs` carries neither, so C1.4 reports "0 events
recorded" — **a false zero about a healthy store.** The fix is a merge-layer branch, not an audit
trail.

**Append-only does NOT hold on the legacy facade.** `w_resetsignals` **deletes from the event
log**, keeping only `signals_extracted`; `w_saveportfoliohealth` `session.delete`s prior
snapshots; `w_save` / `w_overwritesignal` replace `project.doc` in place. None touch
`computed_results`, `decisions` or `audit_events`, so the research record is unaffected — but the
platform-wide claim is not true as stated.

**A decision traces to its evidence (yes, `result_id` + `source_documents`, frozen by the 0009
trigger) but NOT to a code version.** `SIMULATION_VERSION` is a hand-edited constant in
`models.py:32`. Every module body could change and every result would still say `sim-2026.07-v1`.
And **`EXPORT_COLUMNS` carries no `result_id`, `simulation_version`, `seed` or `period_cutoff`**,
so the analysable dataset cannot join a decision to what the analytical layer showed.

**THE VACUITY SWEEP: EIGHT FINDINGS, and the first two are unconditional passes.**
**`test_workspace_t3t5.py:229` is `check(True, ...)`** guarding the per-module recommendation
redaction — the file's own comment calls it "the precise proof" of Guarantee 8, and it computes
`redacted_any`, formats it into the detail string, and never tests it. **`test_features.py:158`
cannot fail** because `audit_rows("features_set", changed_by=None)` is always `[]` (the server
always writes a non-None `changed_by`), so the `or` short-circuits: the only audit check on a
feature change would pass if features were never audited. `test_export.py:133` is `check(True)`
standing in for the whole two-participant fixture. Then three checks asserting a property the
defect satisfies (`test_workspace_t3t5.py:210` asserts determinism where it claims read-only-ness;
`test_decision_sequence.py:169` passes on a shared absence; `test_export.py:243/245` bound the
study's timing measures only by `>= 0`), and **`tests.html`'s 52 assertions run against
`sim.js`/`simulations.js`/`categories.js`, which `index.html` deliberately does not load** — a
correct harness pointed at retired code.

**Read the sweep's method note before quoting its coverage.** I read every call site; I did not
inject faults. It is thorough on the mechanical patterns and **partial on the semantic pattern**,
which is where both cases named in the brief live. Three items are recorded as too expensive to
judge rather than guessed.

**RECONCILED WITH T22 BELOW, which landed in parallel.** T22 executed every module and corrected
T20's count from eleven unobtainable keys to **twelve** (`cpiHistory` was missed), so where the
stage 7/8 report says "eleven" it is quoting T20 and T22's figure is the right one. The two
sessions reached the `events` finding independently and agree exactly: the store exists
(`writes._append_event`), nothing passes it into `signalInputs`, and C1.4's "0 events recorded" is
a wiring gap. **T22 additionally establishes that A2.7 Milestone_Trend abstains correctly**, which
T20 recorded as unknown. Nothing in the stage 7/8 report contradicts T22; read T22 for the D1
membership list.

**NOT COVERED:** whether the `detail.js` executive brief renders anything on a server-computed
project (it recomputes CPI/SPI bands in the browser with its own thresholds), and **which routes
render the decision card for which account type — that decides whether D7.2 reaches a research
participant and is the most useful thing to settle next.** Stage 6's remaining question (can a
snapshot change under a stored decision by a route other than P1) is still open.

---


# T22 — D1. STOPPED WITHOUT CHANGING CODE. AWAITING LIN'S DECISION.

Full detail in `REPORT_2026-08-02_d1-unobtainable-inputs.md`. **No code changed. Nothing under
`server/app/simulation/` was touched, no stored data altered, `assets/` untouched.**

**WHY IT STOPPED.** The task said to stop if any fabrication path turned out to be deliberate and
documented. **All of them are**, in three places each: the module docstring, the `VALIDATION.md`
per-module note, and `VALIDATION.md`'s input-contract section. `models_evc.py`: *"These modules
never abstain with the standard stub... That is the instrument's behaviour, reproduced."*
`models_dq.py`: *"Both emit non-abstaining stubs on sparse input... the instrument's behaviour,
reproduced."* `VALIDATION.md` C1.7: *"emits the Yellow stub the JS emits, not an abstention."*
Authored deliberately in batches 1, 7b and 9.

**The distinction that matters:** what was decided was "reproduce the JavaScript faithfully". What
was never decided is whether the input contract those decisions assume would ever be satisfied
server-side. In the browser the blob arrived and the fallback was an edge case; server-side the
blob never arrives, so **the fallback is the only path that ever executes**. Sound as a port,
unsound as a deployment. That is Lin's call, not a session's.

**THE COLOUR ANSWER, measured: project colour does NOT move. One category does.** Executing
`compute_project` twice on identical inputs, once as shipped and once with all twelve forced to
abstain: healthy stays Green, on-budget stays Green, distressed stays Red. **B2 Evidence
Combination moves, and in BOTH directions** (healthy Amber to Green, distressed Amber to Red) —
the fabricated Amber was pulling B2 toward the middle regardless of evidence. Modules abstaining
per computation go 48 to 60 of 95; note that **over half already abstain today**. Locally: 20 of
20 stored results carry a fabricated verdict, **237 individual verdicts**. Production not
inspected.

**THE AUDIT (T20) UNDERCOUNTED — corrected by executing every module with a recording dict rather
than by regex.** Twelve unobtainable keys, not eleven (`cpiHistory` was missed, read via
`_history`). **Twenty-one modules touch one; nine ALREADY ABSTAIN correctly** — including
**A2.7 Milestone_Trend, whose behaviour T20 recorded as unknown: it abstains, and needs no
change.** **Twelve do not abstain**, one more than T20 said, and the membership differs: B2.1 and
B2.4 were missing from that list. Ten of the twelve vote in status, not nine.

**NONE of the twelve keys is permanently unobtainable. All are UNWIRED.** `events` is the clearest:
`writes._append_event` already writes `{"event", "at"}` into `project.doc["events"]`, exactly the
shape `models_dq` documents, and nothing passes it into `signalInputs` — which is why C1.4 reports
"0 events recorded" on every project. `spiHistory`/`cpiHistory` are reconstructible from
`ComputedResult.signal_inputs` across periods. `evm`/`mc`/`cusum`/`doc` are outputs of the same
run, so an ordering problem. `fairnessSensitive` and `milestoneHistory`'s source remain UNKNOWN.

**WHAT IS NEEDED TO PROCEED:** a decision between (1) abstain everywhere, accepting divergence from
the JavaScript with `VALIDATION.md` annotated; (2) abstain only where the fallback is provably
unreachable in the browser too, which needs the JavaScript examined and has not been done; or
(3) wire the keys instead, starting with `events` and the histories. Not exclusive: 3 for `events`
and the histories plus 1 for the rest is coherent. The session's recommendation is abstain and
wire `events`, but it is a research-instrument decision.
---

# T21 — THE MAP AND THE GLOBE ARE FIXED. THE CAUSE WAS IN NEITHER VIEW.

Full detail in `REPORT_2026-08-02_map-globe-markers.md`. **1013 checks across 21 suites**;
`tests_render.html` **33/33**, up from 26.

**`hydrate()` in `store.js` read absence in the slim projection as deletion.**
`facade.slim_row()` is thirteen fields and carries **nothing about location**. The geographic
views hydrate full project JSON to get coordinates, and then every background portfolio refresh
replaced those rows with slim rows and the coordinates went with them. `refreshPortfolio()` runs
after **create, rename, archive, restore and recompute-all** — so creating a second project
silently un-placed the first. Measured: Map draws 3 markers on first open, **0** after one
refresh, "0 project(s) placed. 5 have no location yet".

**IT AFFECTS EVERY PROJECT WITH COORDINATES, UNIFORMLY.** Nothing about a project distinguishes
an affected one: not how it was created, not analysed versus awaiting analysis, not its status.
The distinguishing factor is **when you look** — before or after the first portfolio-refreshing
action in the session.

**`statusColorFor` and `proxyHealth` were NOT the cause**, and were checked rather than assumed.
Neither skips a marker; an unresolvable status costs a marker its letter, never its dot. The
Radar is unaffected (it places by status, not position) and rendered throughout.

**Fixed at root in two places, both genuine, neither a workaround for the other.**

1. `store.js`: for a row carrying `slim: true`, `hydrate()` carries forward **every key the local
   copy has that the incoming row does not**. **Deliberately general — do not narrow it back to
   an allowlist.** It was already fixed once as an allowlist (graft simulationSignals, signals,
   signalInputs, status, history), which is exactly why it recurred: a list only covers the
   fields somebody remembered. Confined to slim rows, because a **full** row omitting a field is
   a real deletion (clearing an address server-side drops lat/lng, and that must reach the client).
2. `app.js`: `mapHydrated` was a one-shot boolean, so once coordinates were stripped nothing ever
   re-fetched them and the views stayed empty until a page reload. It is now a **Set of ids** —
   still at most one GET per project per session, but a project that arrives later is not locked
   out, and a failed fetch is retried rather than remembered as done.

**`tests_render.html` group 8, seven assertions, is the regression net, and its shape matters.**
Three assertions cover the render site, four cover the round trip through `hydratePortfolio()`.
Proven by reverting: 30/33, and **the three render-site assertions stayed GREEN**. A check written
only at the render site would have passed through the entire defect.

**Not covered by a test, stated plainly:** the `app.js` latch fix has no automated check.
`hydrateProjectsForGeo()` is not exported and its failure mode is browser lifecycle ordering. It
was verified by driving the real application; it is not defended against regression.

**Nothing was backfilled.** The cause was a render-path defect, not missing or failed geocoding,
so the stop-before-backfilling instruction did not come into play. Geocoding works: it runs on
create and on address change, stores `lat`/`lng`/`formattedAddress`, and a failure clears the
coordinates and stores a `geocodeError` the API returns. Production was not inspected.

**ENVIRONMENT: THE BROWSER-PANE WARNING BELOW DID NOT APPLY.** There is no `preview_start` tooling
in this container at all. The app was driven with the pre-installed Chromium through Playwright,
which composites: `visibilityState` `"visible"`, rAF ~6 frames/s under software WebGL. **That is
why the Globe could be checked rather than only measured** — `LinGlobe.mount()` returned
`{ok: true, points: 3, unplaceable: 2}`, one canvas, watchdog stood down. Nominatim is not
reachable through the proxy, so the geocoder was stubbed as the existing suite stubs it.

---

# T20 — PIPELINE AUDIT. READ-ONLY. STAGES 1 TO 4 AND PERIOD DONE; 7 AND 8 NOT STARTED.

Full detail in `REPORT_2026-08-02_pipeline-audit.md`. **No code was modified.** Nothing here is
fixed; this is a findings list.

**THE PREREQUISITE WAS MISSING.** There is no evidence policy audit report in this repository. I
searched the tree and the history. Whatever it establishes did not reach this session.

**THE TWO TO ACT ON FIRST, both proven by execution:**

**D1. Eleven module inputs can never be produced, and nine of them feed a project colour.** Set
difference between what `server/app/simulation/` reads and what `extraction_merge.SIGNAL_INPUT_KEYS`
can emit: `cusum decision doc events evm fairnessSensitive mc milestoneHistory signals
simulationSignals spiHistory`. These are the legacy browser blob and the two history series. **11
of 95 project-level modules read one** (A1.2, A2.7, B2.2, B2.3, B2.5, B2.6, B2.7, B2.8, B2.9,
C1.4, C1.7); nine are in Groups A and B and therefore vote in status. **None abstain.** Measured
with the keys absent, which is every server-computed project: Rough Sets returns **Amber from zero
evidence** ("Green 0, Amber 0, Red 0 of 1 signals"), Audit Trail Completeness returns **Red
permanently** ("0 events recorded"), and CUSUM returns **red, breached, over a 12-period series it
fabricated from the seed**. No test references any of the eleven keys. `VALIDATION.md` records all
of them as exact matches against the JavaScript, which is true and is the trap: the JavaScript was
handed the blob, so it validates the port while the input contract is broken under both.

**P1. Recomputing an earlier period rewrites it with later information. PROVEN.** The property the
research record was said to depend on being impossible. `_compute_and_store` builds the portfolio
vectors from every other project's **most recent** live result (`max(period)`), with no alignment
to the period being computed. Demonstrated: project A's **period 1** recomputed with A's own
documents unchanged went from `insufficient_data` to a Yellow anomaly with `anomaly_score 1.0`,
purely because project B had advanced to period 2. The old row is superseded and kept, so nothing
is destroyed, but the live period-1 result now carries period-2 information. **The only test
touching `portfolio_snapshot` (`test_workspace_t3t5` Guarantee 9) never varies period and would
pass unchanged with the defect present.** Blast radius is limited for RESEARCH projects because
`_resolve_period` forces the current period there (see P7), so this is reachable on operational
projects.

**Also proven:** malformed numeric text becomes `0.0`, so `earned_value="TBD"` yields **cpi=0.0**
(D2, no test); a malformed or absent document date makes `period_cutoff` the **wall clock** (D3); a
declared `docType` is **silently discarded** for any already-seen bytes, so the first uploader's
classification is global and permanent (D4, measured across two projects); an **undeclared**
revision still merges by content hash and double-counts additive fields, because 0013 only helps
when the claim is made and there is still no frontend control (D5).

**Correctly excluded, verified:** Groups C and D do not vote in project status
(`compute.contributes_to_project_status`).

**NOT COVERED, and a future session should not assume otherwise:** stage 7 (reporting and display,
including whether anything can show a result under the wrong period) and stage 8 (audit trail and
logging) were **not started**. Stage 5 covered only the C/D exclusion; stage 6 only via P1. Named
UNKNOWNs are listed in Part 5 of the report, including what supplies `compute_portfolio`'s
`history` on the server path.

**A vacuity sweep of the full suite was NOT run** and is worth its own session: five vacuous
checks have been found by accident so far, and this audit found a sixth pattern (a test blind to
the defect in the code it covers) without looking for it.

---

# T19 — DOCUMENT VERSIONING. MIGRATION 0013 IS WRITTEN AND **NOT** APPLIED TO PRODUCTION.

Full detail in `REPORT_2026-08-02_document-versioning.md`. **1013 checks across 21 suites**;
`tests_render.html` 26/26.

**THE ACTUAL DEFECT WAS WORSE THAN THE BRIEF DESCRIBED, and it is worth knowing what it was.** A
revision did not collide and was not frozen out by the cache: **both versions were stored and both
reached computation**, because `_period_documents` filtered on (project, period) and deduped on
sha256 only. Which version's figures survived was decided by `_ordered_docs`'s tiebreak, **the
SHA256** — a content hash. Measured: first-wins fields took the lower hash, last-wins fields the
higher (opposite directions, so one revision could produce a signalInputs **mixing both
versions**), additive fields counted BOTH (an RFI log revised 10 to 12 assembled to **22**), and a
downward correction to a keep_max field was discarded. It was deterministic, which is worse than
random: it reproduced, so it looked stable.

**Built:** `document_uploads.supersedes_document_id` (new -> old, so superseding is an INSERT and
never an UPDATE of a row a decision may reference, and so a revision can itself be revised);
supersession excluded from computation but **kept readable** under a new `superseded` key on
`projectuploadstatus`, with bytes and extraction retained; and
`computed_results.source_documents`, so a result names the document versions that produced it.

**It is on `document_uploads`, NOT on `documents`, and that is load-bearing.** `documents` is
content-addressed and shared across projects; the same file can be current in one project and
superseded in another. Marking the shared row would leak a revision into every project holding
those bytes.

**AWAITING LIN'S DECISION: results computed against a now-superseded document.** Options are laid
out in section 3 of the report. I chose **leave them** for this session (it changes nothing about
already-collected data, and `source_documents` makes "was this computed from a superseded version"
answerable), and **recommend a stale flag as the follow-up**. **Automatic recompute is the one to
avoid**: it rewrites what a participant was shown, which is what the append-only discipline exists
to prevent. Nothing was recomputed, backfilled, or marked.

**REMAINING GAP, reported not fixed: an undeclared duplicate is unchanged.** A revision uploaded
**without** the `supersedes` field still merges arbitrarily, exactly as before. No inference was
added, deliberately: two documents of the same type in one period are not necessarily versions of
each other (two RFI logs from different weeks are both current). The suggested follow-up is to
**detect and report the ambiguity** on upload rather than infer it, which needs Lin's wording.
**There is also no frontend control yet** — the field is reachable only by an API caller.

---

# DEFERRED WITH AN OWNER — NOT DEFECTS, NOT YOURS TO ACT ON

**Four items are deliberately deferred and three of them are Lin's.** A session that finds one of
these and treats it as an open defect is acting on work that has already been assigned. Read the
owner line before doing anything.

## 0. Applying migration 0013 to production. OWNER: LIN.

Written and verified against a throwaway SQLite in T19 above; **production has not been migrated
and was not inspected or queried**. Migrations are applied manually by Lin. Until it is applied,
the document-versioning columns do not exist in production and the supersede path will fail there.

## 1. The production range query. OWNER: LIN. Do not do this yourself.

No stored `docRiskScore` outside 0 to 1 exists in anything reachable locally (the dev store and
all per-suite throwaway databases: zero). **Production was deliberately not inspected**, and no
session may query or migrate production data.

This matters because the T18 guard refuses at the merge boundary: a project holding an
out-of-range row **will stop computing** once the guard is deployed, rather than computing without
that document. **Lin will query production before the first real document run.** That is the whole
of the follow-up; there is nothing for a session to do here except leave it alone.

## 2. The general shape of `w_overwritesignal`. DEFERRED, and NOT resolved by the range guard.

The T18 range guard closes this action for **`docRiskScore` only**. Everything else about it is
unchanged: it still accepts **an arbitrary `signalInputs` field name and an arbitrary value**,
PM-gated but otherwise unvalidated. A caller can still write nonsense into `cpi`, `bac`,
`actualPctComplete`, or a field name that does not exist at all.

**Do not read the range guard as having fixed this.** Validating the rest is a separate piece of
work on its own terms: every field needs its own contract decided first, and inventing range rules
for `cpi` or `bac` on a session's own judgement is exactly the kind of quiet assumption this
codebase keeps having to undo. It needs Lin's decisions per field before any of it is written.

## 3. Step 6, real extraction against an actual project document. OWNER: LIN. STILL BLOCKED.

Unchanged and not clearable from a local session. It needs a real project document and a live
`ANTHROPIC_API_KEY` in the same place; the container has neither, and `render.yaml` marks the key
`sync: false` so it exists only in the Render dashboard. **The unblocking run is a manual upload
of one real document through the deployed platform, and it is Lin's to do.** Detail in T17 below.

---

# T18 — THE DOCUMENT RISK SCORE RANGE IS GUARDED. PR #197 IS MERGED.

Full detail in `REPORT_2026-08-02_risk-score-guard.md`. **985 checks across 20 suites**;
`tests_render.html` 26/26. Merged to `main` and pushed.

**STEP 6 IS STILL BLOCKED AND IS LIN'S TO CLEAR.** Real extraction needs a real project document
and a live `ANTHROPIC_API_KEY` in the same place, and neither is reachable from a local session.
The unblocking run is **one real document through the deployed platform on Render**, where the key
already is. Nothing in this session moved that; the T17 section below still stands in full.

**THE FINDING IS FIXED, AND THERE WERE THREE ENTRY POINTS, NOT TWO.** The one the earlier finding
missed is the dangerous one: **`w_overwritesignal` in `writes.py`** is a live PM-gated `/exec`
action that writes a caller-supplied value into an arbitrary `signalInputs` field with **no
validation at all**, so `docRiskScore` could be set to 85 or -3 and reach fusion **without a
document being involved**. A guard confined to `extraction_merge.py` would have left that wide
open. All four sites now refuse:

1. `extract_many()` — the extraction boundary, where the value enters from the model
2. `_merge_one()` shared risk branch
3. `_merge_one()` `commissioning_report` branch (a separate path; guarding the shared branch
   alone leaves it open)
4. `w_overwritesignal()` — the document-free route

**REFUSE, NOT CLAMP, and the reasoning is in the validator's docstring so it is not
re-litigated.** Clamping turns -3 into a confident 0.0 that reads as the BEST band and traces back
to nothing. 0 and 1 remain VALID and must survive; `"N/A"` still coerces to 0.0 by the documented
legacy quirk and is deliberately untouched.

**The refusal reaches the uploader through an existing surface.** `extract_many` already turns any
exception into the per-file `{ok: False, error}` that `signals.js` renders verbatim in its
"Extraction failed" dialog, and `documents.py` only stores rows whose `ok` is true, so a refusal
leaves nothing behind. **The message text is composed operational wording, flagged in the report
for review**; it is not liability language and it is one string to change.

**No already-stored out-of-range values exist** in anything reachable from a local session (the
dev store and all twenty per-suite databases: zero). **Production Postgres was not inspected and
must not be.** Worth knowing before the first real run: a project that DOES hold such a row will
**fail to compute** once this deploys, because the merge boundary raises rather than dropping the
value. That is refusal applied consistently, and it is a hard stop, not a degraded result.

**`server/tools/test_doc_risk_range.py`, 66 checks**, proven able to fail five independent ways
(each guard removed in turn, plus the range widened to accept a percentage). **One vacuous test
was caught while writing it**: the `overwritesignal` checks initially passed because the action
refuses an empty `signalInputs` *before* reaching the guard, so they were green while proving
nothing. The suite now seeds first and reads back independently.

---

# T17 — STEP 6 (REAL EXTRACTION) DID NOT RUN. THE DEPENDENCY IS UNMET.

Full detail in `REPORT_2026-08-02_real-extraction.md`. Merged to `main` as PR #197 (T18 above);
the "unmerged" note that stood here is stale.

**Treat the extraction verification as NOT STARTED, not as partial progress.** Parts 1 to 4 were
not attempted. Three independent blockers, any one of them sufficient:

1. **No real project document exists in the container.** Zero PDFs/DOCX/XLSX in the repo. The
   three files in `server/dev_fixtures/` are **the stub in file form**: `dev_serve.py` writes them
   itself at startup from hardcoded numbers, and their sha256 hashes *are* the StubExtractor's
   recording keys. Using one would be running the stub against its own recording.
2. **No `ANTHROPIC_API_KEY`, so the extraction path cannot run at all.** Measured, not assumed:
   `build_extractor()` returns `StubExtractor`; `require_real=True` raises; and `extract()` on any
   unrecorded bytes raises "refusing to invent an extraction". **This is decisive even if a real
   document were supplied.** `render.yaml` marks the key `sync: false`, so it lives only in the
   Render dashboard.
3. **The Drive connector needs per-call approval** unavailable in a non-interactive session.

**To unblock:** run one real document through the deployed platform on Render, where the key
already is, and bring back the stored extraction; or attach a document to a session that also has
the key. Local work cannot substitute.

**`NAMING_AUTHORITY.md` is untouched and its wording still stands.** "Reads the reported figures"
remains correct because extraction still has not run. Note for whoever gets the first successful
run: **one clean extraction would not justify "extracts the figures" either.** That is a claim
about reliability across real document structures. One run justifies only "has been run against a
real project document". See section 3 of the report.

**FINDING (NOW FIXED IN T18 ABOVE, kept as the record of what it was): `document_risk_score` had
no range guard, and the silent failure was in the safe-looking direction.** Measured through the
merge path: `85` stored as `85` (pinning every project Red), `"85%"` stored as `85.0`, and **`-3`
stored as `-3` and read as GREEN**. There was no validation anywhere on the server; the only guard
was a sentence in the extraction prompt, and no test asserted the range. Lin decided refuse rather
than clamp, and T18 implements it at all four entry points. **This paragraph is history, not an
open item.**

**Disclaimer wording gap: CLOSED.** The four upload panels in `signals.js` and `auditor.js` carried
wording matching neither the approved notice nor each other. All four now render the approved text
verbatim from one shared constant, `assets/js/disclaimers.js`. The sign-in notice and footer stay
static HTML on purpose, so a liability notice never depends on JavaScript. `test_disclaimers.py`
is now **46 checks** (was 28) and additionally asserts each call site sits **inside a template
literal**, because `${...}` in an ordinary string is valid syntax that ships the placeholder text
to the user and `node --check` accepts both. Server suite is **919 across 19 suites**.

---

# ACCEPTED STATES — DELIBERATE, DECIDED, NOT DEFECTS

**Read this before "fixing" either of the two things below.** Both have been decided. A session
that rediscovers one of them and treats it as a defect is repeating work that has already been
done, and in the second case would undo a rule rather than a bug.

## 1. The Methods tab navigates ten categories relabelled by group. That is deliberate.

`GROUP_ASSIGNMENT.md` defines **four** groups. The Methods tab still navigates the **ten** legacy
categories, each now labelled with the group its modules belong to (where a category's modules
split across groups, the label follows the majority). The two are not in conflict: the taxonomy is
four groups, and the navigation is a finer-grained index into it.

**Restructuring the tab around the four groups is a rebuild, not a sweep, and it has been deferred
on purpose.** It would mean re-cutting every module reference section, re-parenting every topic,
and re-deciding what a group-level article says where a category-level one exists today. Nothing
about the current arrangement is untrue; a reader expanding "Recommendation and Governance /
Governance and Compliance" finds four delivery-quality methods that belong to Project Health,
which is a granularity mismatch, not a false statement. Do not start the rebuild as a side effect
of another task.

## 2. Method thresholds appear in the module reference and NOT in the assistant. This is a rule.

Stated as a rule so future surfaces follow it rather than re-deciding it each time:

> **Numeric thresholds belong where a reader has navigated to method detail, and never where they
> arrive unbidden as apparent fact.**

The module reference in the Methods tab carries its `bands` values, because a method reference
without thresholds is not a reference: the reader is there precisely to see where the boundaries
fall. The scripted assistant carries none, because an answer to "what is CUSUM?" that volunteers
"Red at five sigma" presents a number as established fact to someone who did not ask for it and
has no context to weigh it.

This is why the two surfaces differ, and the difference is **not** an inconsistency to reconcile.
When adding a new surface, ask which of the two it resembles: a reference the reader navigated
into, or an answer delivered to them. Only two thresholds have been verified against
`server/app/simulation/` directly (the Monte Carlo 5%/10% bands and the CUSUM constants: target
1.00, k = 0.5 sigma, H = 5 sigma, amber at 60% of H). The rest of the module reference's `bands`
are carried from the pre-existing entries and have not been re-derived.

---

# T16 — PR #196 IS MERGED. THE DISCLAIMERS ARE LIVE.

Full detail in `REPORT_2026-08-02_merge-and-disclaimers.md`, which includes the live text verbatim.

**PR #196 merged to `main` and pushed** after 873 checks and `tests_render.html` passed on the
merged result, not just on the branch.

**The approved disclaimers are live on both surfaces, both account types.** Research variant on
the sign-in notice and the footer for research accounts and before sign-in; operational variant on
the same two surfaces for operational accounts. Verified in a browser: the class switch selects
the right variant on both surfaces in all three states, and **"All project data is synthetic" is
never visible to an operational account**, which is the sentence that must never reach a user
uploading real project documents by design.

**`DISCLAIMERS_DRAFT.md` is now the source of the live text, not a draft of it.** Its header says
so; the filename is historical. **`server/tools/test_disclaimers.py` (28 checks) fails if the live
text in `index.html` diverges from that file by a character**, in either direction, so the
reviewable wording and the shipped wording cannot drift apart. Proven able to fail four ways: a
one-word change live, research text leaking onto the operational surface, a surface losing its
notice class, and the source edited without the live text following.

**The suite count is now 901 across 19 suites** (873 + 28 from the new disclaimer check).

**`tests_render.html` is 26, up from 22.** Four assertions now prove `knowledge.js` parsed and its
library is populated: the exact gap that let a fatal syntax error hide the entire Methods tab and
the assistant's knowledge library for an unknown number of builds while the server suite stayed
green. Proven by reproducing the original fault (deleting one object's opening line): all four
fail, then restore.

**`taxonomy.js`'s stale header is corrected.** It claimed the project rollup fuses "all 11
registry category statuses" and that "Portfolio Health still votes here", and described a
Red-review advisory at conflict 0.55. All three are false against the shipped server, and all
three had already been removed from the Methods tab for that reason. The corrected comment states
what the block actually does and records why the old claims were wrong, so they are not
reintroduced.

**One thing removed that was not in the approved draft, flagged for review:** the footer's
`footer-praxis-notice` line. Its liability sentence is now carried verbatim by both variants, and
keeping it would have printed that sentence twice in adjacent paragraphs. See the report.

**Still open, unchanged:** both export paths carry no notice, attribution, or copyright; and the
sign-in page's own attribution and copyright lines are shorter forms that do not match section 3
of the approved file. Both are flagged in `DISCLAIMERS_DRAFT.md` and neither was changed, because
neither was part of the approval.

**Superseded in part by T23**, above: the sign-in page's *attribution* was reconciled to section 3
on 2026-08-02 and section 3 itself was rewritten. Its *copyright* is still the short form, and the
export paths still carry nothing. The check is 90 checks now, not 28, and the suite is 1057.

---

# T15 — THE METHODS TAB IS SWEPT. PR #196 IS READY TO REVIEW.

Full detail in `REPORT_2026-08-02_methods-tab.md`, including ten judgement calls awaiting Lin's
review. 873 checks across 18 suites pass; `tests_render.html` 22/22.

**The Methods tab now renders and measures clean.** All 51 topics render, 645,818 characters of
rendered text with every collapsible expanded: **zero PCEIF, zero PDAF, zero em dashes, zero
module ids, zero "Cat N", zero "PH.N"**, standing description verbatim in both forms, zero page
errors. The About and Methods tabs agree: groups by name, no ampersand forms, the document risk
footnote on both, no "103" anywhere.

**The real scope was bigger than the estimate, and in a different place.** PCEIF was 40 + 49
occurrences, close to the reported 37 + 49 (the earlier figure counted lines). But **"Cat N" was
405 occurrences**, ten times the name problem, and **module ids reached the user through three
render paths, not through prose**: `modDoc()` printed `m.n` before every method name, the nav
prefixed every module topic from `CAT_LABEL_BY_ID`, and the defensibility categories printed
"Category N". Fixing three functions removed 101 rendered ids.

**Part 2, the truncation check: the two entries in `knowledge.js` were the only ones.** All ten JS
files the renumbering commit touched parse. Its diff removed 103 `{ n:` opening lines and added
101, and that two-entry difference is exactly the two truncations. `ds_defensibility_data.js` was
edited by a different, safe mechanism (it rewrites `id_display` values in place, deletes no lines).
A parse check cannot rule out a cut that left valid syntax; the registry cross-check (101 entries,
ids distinct, matching `GROUP_ASSIGNMENT.md`) covers that and agrees.

**Removed rather than caveated, all checked against the server first:** the eight-code override
taxonomy (exists nowhere in the repo, replaced with the real `DISPOSITIONS` and `REASON_CODES`),
the learning-governance section, the `redReview` advisory (**the server never writes
`red_review`**, so the flag is permanently false), the claim that Portfolio Health votes in project
status (`contributes_to_project_status()` excludes **groups C and D**), the document-risk threshold
row (an extraction-supplied input, not a server computation), the platform-wide "48 business hours"
deadline and its FAR/OMB justification, the six-row authority matrix's "Critical" tier, and
"mandatory rationale" (the form requires it; the server field is optional and unvalidated).

**Still open, unchanged:** export paths carry no notice, the live operational notice is unreviewed
but can display (both are liability decisions, see `DISCLAIMERS_DRAFT.md`), and the em dash sweep on
`auditor.js` and the legacy researcher surfaces.

**Two things the next session should know.** First, **nothing tests `knowledge.js` in a browser**,
which is how a fatal syntax error survived for weeks; a one-line `window.LIN_KNOWLEDGE` assertion
in `tests_render.html` is the cheapest insurance and was left undone deliberately. Second,
**`taxonomy.js` carries a stale comment** claiming the project rollup fuses "all 11 registry
category statuses" and that "Portfolio Health still votes here" — the same false claim removed from
the Methods tab, left in place because that file was outside this brief.

---

# T14 — STEP 5, THE JUDGMENT PROSE, IS DONE FOR ITS FOUR SURFACES

Full detail in `REPORT_2026-08-01_judgment-prose.md`, including the judgment calls awaiting
Lin's review. 873 checks across 18 suites pass; `tests_render.html` 22/22 in a real browser.

**Done:** the About tab (standing description quoted verbatim, new framework and method
sections, false Tech stack / Capabilities tables removed), the assistant (says scripted plainly;
its TERMS and TOPICS carry no PCEIF, no module ids, no retired-behaviour claims), `README.md`
(rewritten against the shipped system), and `DISCLAIMERS_DRAFT.md` (drafted, NOT live, requires
Lin's review).

**Found and fixed: `knowledge.js` did not parse since the module renumbering (`e34fa50`).** Two
module entries were removed by deleting only each object's opening line, a fatal syntax error,
so `LIN_KNOWLEDGE` never loaded: the Methods tab rendered nothing and the assistant had no
library in every build since. Fixed by removing the orphan bodies. Nothing tests that file in a
browser; a `window.LIN_KNOWLEDGE` assertion in `tests_render.html` is a cheap next item.

**The big remaining content item was the Methods and Framework tab. DONE in T15 above** — the
deploy consideration recorded here no longer applies: that tab is swept and measures clean.

Also still open: export paths carry no notice (a liability decision, see the draft file), the
em dash sweep on `auditor.js` and the legacy researcher surfaces, and the live operational
notice which is unreviewed but can now display (flagged in `DISCLAIMERS_DRAFT.md`).

---

# T13b — THE TAXONOMY IS SETTLED AND COMMITTED. 100, not 101.

`GROUP_ASSIGNMENT.md` at the repository root is the authority. Merged to `main`.

| Group | Name in user-facing text | Count |
|---|---|---|
| A | Project Health | 52 |
| B | Recommendation and Governance | 36 |
| C | Data and Evidence Health | 7 |
| D | Portfolio Level | 5 |
| | **Total** | **100** |

**Document Risk Score is not counted.** It is a value the extraction model supplies and the server
carries through, not a computation the analytical server performs. **100 is current, not
permanent**: if it is ever implemented server-side the count becomes 101 and Group A becomes 53.

**Do not describe the registry refusal as a Document Risk Score exclusion.** It is a generic
catch-all for anything absent from `VALIDATED`, and its message is the wording of work outstanding.
Whether the value is unported by design or by accident is still unestablished.

**User-facing text uses "and", not the ampersand the code constants use.** Do not rename the
constants.

`server/tools/test_group_assignment.py` fails if the code and the artifact diverge. If it goes red,
the published taxonomy and the code have parted company and no sweep should run until that is
understood.

**`unported_modules()` is still wrong and is deliberately not fixed.** It counts the five Group D
modules as unported although `portfolio.py` implements them, reporting six where exactly one is.
The fix is inside `server/app/simulation/`, which the task forbade modifying. Both new checks
compute the genuinely unported set themselves and assert the over-report explicitly, so nothing
inherits the error. **This needs a decision: lift the prohibition for that function, or leave it.**

**STEP 4, THE MECHANICAL SWEEP, HAS NOT STARTED.** The naming authority document has now failed to
reach three consecutive sessions, and step 4 stops without it by its own terms: it rewrites
surfaces that must quote that document's standing description wording verbatim, and the task
summary carries the taxonomy but not the wording.

**A tenth hasSignals instance was found, and it was the root.** `statusKey()` still had the legacy
gate; the T12 legend fix had added a parallel `storedStatusKey()` beside it rather than correcting
it. It drives eight call sites, so an analysed project was placed on the radar's neutral mid-ring
and given the wrong marker colour, not merely mislabelled. Fixed, duplicate removed.

**`tests_render.html` now exists** and is the regression net for that whole family. 22 assertions,
every one proven able to fail by reverting its gate. It is NOT part of the 854 and will not run
itself: open `http://127.0.0.1:8010/tests_render.html` with the dev server up, after any change to
`app.js`, `detail.js`, `decision.js` or `taxonomy.js`. `dev_serve.py` serves it and `tests.html` by
exact name; `app/main.py` is unchanged and still refuses to mount StaticFiles at `/`.

**Two more vacuous checks found.** `test_simulation.py:49-50` asserts
`len(unported_modules()) == 101 - len(VALIDATED)`, a tautology that cannot detect the A4.1 gap. And
`unported_modules()` itself counts D1.1 to D1.5 as unported although they are implemented in
`portfolio.py`, reporting 6 where 1 is genuine.

---

# T11a — THE GLOBE HAS BEEN SEEN, AND IT RENDERS

The researcher confirmed by eye: hex-dot continents, cyan rim, atmosphere and the 23.4° tilt all
visible. After three sessions of measurement-only evidence, the globe is verified visually. Two
bugs came out of that first look, both fixed — see
`REPORT_2026-08-01_globe-view-sticks-and-rotates.md`.

**The watchdog asked once and broke the working case.** `mount()` resolves in ~40 ms; globe.gl does
not build its scene group until ~1 s later. A single `hasScene()` check at resolve always saw
false, so four seconds later the watchdog destroyed a healthy globe and switched to the atlas — the
symptom being "Globe switches back to Map on its own". It now **polls to a 6 s deadline** and stands
down the moment a scene appears. Do not return it to a single check.

**The globe was never rotating where it mattered.** `autoRotate` was only enabled for the empty
state and the non-interactive detail globe, so the portfolio globe *with projects on it* — the one
case a director sees — had rotation off by construction. It now rotates in every state.

**"Verified rotating at 0.35" was a property read, never a look.** three.js turns at 6°/s per unit
of `autoRotateSpeed`, so 0.35 was ~171 seconds per revolution: a still image. It is now `1.0`,
6°/s, one revolution a minute, and it respects `prefers-reduced-motion`. **Check motion by watching
it, not by reading the property** — that is precisely how this survived three sessions.

**The globe does place points.** Confirmed with two located projects: `points: 2, unplaceable: 0`,
tilt 23.4 after reload. A portfolio showing "0 project(s) placed" is a data condition — projects
without coordinates — not a globe fault.

**View selection sticks.** Radar, Map and Globe each persist and restore correctly, and globe assets
stay unloaded unless Globe is the restored view.

**The default is Map** for a user with no stored preference. A stored preference always wins, so
anyone who has selected Globe will keep landing on Globe. Moving the default to Globe is now a
defensible product decision rather than a safety question, but it has not been made.

---

# T11 — the default geographic view is now the flat SVG atlas, and it is MERGED

`assets/js/atlas.js`. SVG, no WebGL, no 3D library, **no animation loop**. It is the default on the
portfolio and on project detail, and it draws the country geometry already vendored for the globe,
so it needed no new assets.

**This is the view that cannot fail to render**, and that is why it exists: two sessions could not
verify the globe because the pane does not composite, and a globe that resolves `ok` while drawing
nothing is a black panel in front of a director. Verified with **0 rAF frames**: 177 country paths,
markers, 215 nodes, 11 ms — and at pixel level, marker centre `#26344f`, halo ring `#05080b`,
ocean beyond `#0e3049`, all exactly their variables. Full detail in
`REPORT_2026-08-01_flat-atlas-default-view.md`.

**The globe is kept, demoted to a third stage button, and now has a watchdog.** `mount()` resolving
is not the same as the globe drawing, so `LinGlobe` exposes `hasScene()` and the caller falls back
to the atlas after 4 s if the scene was never built. That watchdog fired for real in this session
and the fallback worked end to end.

**Marker legibility is solved by the halo, not by the background.** Without the dark disc, Yellow on
Miami/Maria land is **1.01:1** — invisible. With it, every status is ≥5.66:1 in every theme. Do not
"simplify" the halo away, and do not try to fix legibility by darkening the land; that was measured
on the globe's texture and only changes which status fails.

**MapLibre is now orphaned** — `scheduleMapWarmup()` has no callers and `buildMap()` is unreachable.
It is left in place, clearly marked, and deleting it (~400 lines, 837 KB of vendored files, the map
markup, and the `tiles.openfreemap.org` CSP entry) is a clean scoped follow-up.

**Nobody has looked at the atlas.** Everything above is measurement and pixel sampling, not a
picture. That is the first thing to do with a visible pane.

---

# READ FIRST — check the browser pane before planning any visual work

**Two consecutive sessions have now been lost to this.** Before anything else:

```js
document.visibilityState            // must be "visible"
// and count rAF frames over 1s     // must be > 0
```

If it is `"hidden"` with 0 frames, **globe.gl never builds its scene**, screenshots fail, and no
visual check or frame-rate measurement is possible. Say so and stop; do not spend the session
discovering it late. **This now applies only to GLOBE work** — since T11 the default geographic
view is the flat atlas, which renders fully with 0 rAF frames and is checkable either way. `preview_start` reporting "Browser pane opened", and the `PostToolUse` hook
saying a file "is now visible in the Browser pane", **both appear even when the pane is hidden** —
neither is evidence. Only the two checks above are.

Everything measurable works fine while hidden: `performance.getEntriesByType('resource')`,
`LinGlobe.palette()`, DOM state, the action API. That is how everything below was verified.

## Per-session report files

From 2026-08-01 onward every session writes `REPORT_<yyyy-mm-dd>_<short-task-name>.md` at the
repository root and commits it. The most recent is
`REPORT_2026-08-01_globe-verification-and-vendoring.md`.

## Dev-server caching — now fixed at the source

`dev_serve.py` sent `no-store` for `/assets` **or** paths ending `.html`. `index.html` served at
`/` matches neither, so the root document was still being cached — it hid an `index.html` edit in
this session exactly as the old `/assets` gap hid `detail.js`. It now also keys on a `text/html`
content type. If a page-level edit still seems not to apply, compare
`performance.getEntriesByType('resource')` `encodedBodySize` against what `curl` returns before
suspecting the code.

---

# T10 — two globe treatments. Built, NOT merged, and here is exactly what is missing.

Branch `t10-globe-treatments` at `3b5ee7d`. `main` is at `5ccc395`. 854 checks across 17 suites
pass. **Not merged**, for one reason: nothing was ever seen rendering.

## The blocker, and how to clear it

`document.visibilityState` was `"hidden"` for the whole session and `requestAnimationFrame`
produced **0 frames per second**. globe.gl builds its scene inside that loop, so the scene graph
never populated: no screenshot, no visual confirmation of either treatment, and **no frame rate**.

**Guarantee 7 is unmet.** The hex-dot resolution (3) was chosen conservatively *because* it could
not be measured, not because a measurement supported it.

**What the next session must do, with the pane visible:**

1. Look at both treatments. Nothing below has been seen.
2. Measure frame rate on each. If the abstract globe costs more than a few fps against the plain
   sphere, lower `hexPolygonResolution` from 3, or raise `hexPolygonMargin`.
3. Confirm the marker halo actually reads. The argument for it is analytic (below) and I believe
   it is sound, but it is not evidence.
4. Capture the three themes at 1280 / 1920 / 3840.

**Diagnostic that saves time:** `performance.getEntriesByType('resource')` and
`LinGlobe.palette()` work regardless of compositing — that is how everything below was verified.
But `globe.scene()` will show only a bare `Mesh` and `palette()` will return `tiltDeg: null` while
the pane is hidden. **That is not a bug.** Do not go chasing the tilt again; it is verified at
`fe4f59b` and unchanged.

Also: a scene walk over the abstract globe enumerates thousands of hex objects and will time the
tool out. Keep probes shallow.

## Marker legibility — the reasoning, so it is not re-litigated

The obvious fix does not work, and this was measured rather than assumed. Sampling the real
texture at six sites and computing WCAG contrast per status:

| Variant | Worst case |
|---|---|
| Texture as-is | **1.02:1** — Yellow over the Sahara |
| Dimmed to 62% brightness / 72% saturation | **1.01:1** — Red, once the sand is dark |

**Dimming only changes which status fails.** A single background brightness cannot serve four
colours at four different luminances. That is why the texture ships undimmed — do not "fix" it by
dimming.

What ships instead is a dark disc under every marker (`--globe-marker-halo`, `#05080b`), so
contrast is a property of the marker's own surround and is identical over ocean, desert, ice and
cloud: Red 4.9, Amber 7.5, Green 10.5, Yellow 13.4. Status colours are untouched.

It is a **labels layer with empty text**, not a second points layer — globe.gl allows only one
`pointsData`. Both are real 3D layers, so the disc is depth-tested. An HTML-overlay marker was
rejected: it would float in front of the far side of the planet.

## Verified by measurement (these do not need redoing)

| | |
|---|---|
| Treatment follows theme, both directions, real buttons | NYC abstract (177 hex polygons, cyan rim) ↔ Miami/Maria photographic |
| Repaint, not remount | `liveCount` steady at 1 across every switch |
| Texture only where used | 0 bytes under NYC; 529 KB same-origin on the photographic themes |
| Status colours across themes | byte-identical on all three |
| `rgba()` audit | all **14** variables the globe reads, all three themes — none |
| Empty state | still rotates at 0.35 with zero points |

## Guarantee 5 — Google Fonts is now vendored; two dependencies remain by necessity

**Fonts are done.** 18 woff2 (Archivo, Inter, IBM Plex Mono; latin + latin-ext) plus a generated
`assets/vendor/fonts.css`, all same-origin, SIL OFL 1.1. `unicode-range` is preserved so only 4
files / 142 KB actually transfer on the sign-in page. Vendor total **4.5 MB → 5.9 MB**.

Two remain and neither can be vendored. **Both failure paths are verified live, so neither needs
re-testing:**

- **`accounts.google.com`** — with the Google global deleted, the username and password form still
  renders, stays enabled, and authenticates. A blocked network does not lock anyone out.
- **`tiles.openfreemap.org`** — with `maplibregl` deleted, the map degrades to a muted panel
  reading "Map tiles unavailable: check connection" with the project list still present. Not a
  blank panel. A 9-second watchdog in `app.js` covers the style-never-loads case.

Note the portfolio stage buttons are now **Radar** and **Globe** only — the MapLibre map is the
globe's WebGL-off fallback rather than a stage the user picks, which makes the tile host a
fallback-of-a-fallback.

## The `[data-set-theme]` trap is gone

`applyTheme` no longer sweeps `[data-set-theme]`; nothing ever carried it. A comment now names
`openThemeFlyout()` as the real switcher, so the next grep does not repeat the false negative.

---

# T9 — the detail globe is VERIFIED. Read this section first.

## Task 1 is settled. The detail globe renders, and the fault was never in detail.js

All three checks pass, measured live on a clean profile at `fe4f59b`:

| Check | Result |
|---|---|
| `LinDetail.teardown` exists | **function** |
| Location section renders on a project with coordinates | **yes** — badge "located", note "Matched to: …" |
| `LinGlobe.liveCount()` 2 with both globes, 1 on leaving detail | **1 → 2 → 1**, detail canvas released |

**The cause of the previous session's failure was a stale HTTP cache entry, not the code.**
Do not go looking at the section markup again; it was always correct.

- The browser held `detail.js` at **111,064 bytes** with `transferSize: 0` and
  `deliveryType: "cache"`, while the server served **112,583 bytes**.
- That entry was stored **before** `no-store` was added, so it carried the old freshness
  lifetime and the browser reused it **without revalidating**. A new tab does not help: the HTTP
  disk cache is per profile, not per tab.
- `globe.js` was first fetched *after* `no-store` landed, so it never had a cacheable entry and
  always updated. That is the whole of the "same directory, different behaviour" mystery.
- **The fix that works:** `fetch(url, {cache:'reload'})` once, then reload. That overwrites the
  poisoned entry. After that `no-store` keeps it correct.
- **Diagnostic to reach for first:** compare `performance.getEntriesByType('resource')`
  `encodedBodySize` against the bytes `curl` gets from the server. If they differ, it is the
  cache, whatever the response headers currently say.

## Two traps found while verifying, both of which cost time

- **`requestAnimationFrame` does not fire when the pane is not displayed.** The automated
  browser does not composite frames unless the Browser pane is visible, so rAF callbacks never
  run — and screenshots fail with "not compositing" for the same reason. globe.gl still builds
  its scene, because it uses its own timers. Anything that must run after a library finishes
  building should be on `setTimeout`, not rAF. This silently left the globe upright.
- **`[data-view]` is not `[data-nav]`.** `[data-view="globe"]` is the portfolio's radar/globe
  toggle. Leaving the detail page — and therefore `LinDetail.teardown` — is `showPage`, driven
  by `[data-nav]` (`app.js:1704`). Clicking the wrong one looks like a teardown leak.
- Automated typing of `!` into the password field was rejected by the server while the identical
  credentials succeeded through `LinStore.postWithTimeout`. A typing artefact, not a product
  fault, but it will cost you a detour.

## Running the suite: migrate first

`854 checks across 17 suites` reproduced exactly at `fe4f59b`. The suites need a **freshly
migrated** database and do not migrate themselves — run `python -m alembic upgrade head` against
each throwaway SQLite before the suite, or every one of them dies on `no such table:
participants` and reports nothing. A Git Bash `mktemp -d` path is not a valid SQLite URL on
Windows; use a Windows-style absolute path.

## What T9 completed, and what is untouched

| Task | State |
|---|---|
| 1 — verify the detail globe | **Done, measured** |
| 3 — axial tilt + empty state | **Done, measured** (`fe4f59b`) |
| 2 — rewrite the About page | **Not started** |
| 4 — globe follows the theme | **Colour done, measured** (`9dbf5c3`) |
| 4 — the Miami-only beach motif | **Not started** — the one part of Task 4 still outstanding |
| 5 — the 84 em dashes | **Not started**, deliberately: a partial pass is worse than none |

### Task 4, before anyone starts it

One real bug was found and fixed on the way to Task 3, and it is the mechanism Task 4 depends on:
**`three.js` `Color.set()` cannot parse `rgba()`**, and several theme surfaces are declared with
alpha (`newyork`'s `--surface-soft` is `rgba(21,28,32,.86)`). `Color.set` threw, the `try/catch`
swallowed it, and the globe kept globe.gl's default material. `stripAlpha()` in `globe.js` now
handles this. **Every further theme variable piped into the globe must go through `themeColor()`**,
or it will hit the same wall.

**Both of the questions raised here have since been answered, and Task 4's colour work is done
(`9dbf5c3`). The claim that there was no theme switcher was WRONG — corrected below.**

1. **The switcher exists.** It is built in JS as fly-out pills (`app.js:2065`, opened from
   `.dock-menu`), whose `onClick` calls `applyTheme` directly. **Nothing carries
   `[data-set-theme]`** — the `querySelectorAll` for it inside `applyTheme` matches nothing and is
   dead code. Grepping for that attribute is what produced the false negative. Grep `THEME_META`
   or `openThemeFlyout` instead.
2. **The mapping**, from `THEME_META` (`app.js:1845`) and confirmed by clicking all three pills:

   | Button | `data-theme` |
   |---|---|
   | Miami | `light` |
   | NYC | `newyork` (default) |
   | Maria | `maria` |

   **`dark` is Gotham and is the unused fourth** — archived, still renders if forced, not offered
   and not the default; a persisted `"dark"` falls through to `newyork` (`app.js:2658`).

   So `app.js:1653` and the brief never actually disagreed: Miami's identifier *is* `light`.

`LIN_STATUS_COLORS.refresh()` (`config.js`) is already the established "re-resolve the palette
after a theme change" hook, and `applyTheme` already calls it. A globe repaint belongs there
rather than in a new listener.

### Screenshots were not possible this session

The Browser pane is not displayed in a non-interactive session, so `computer{action:"screenshot"}`
fails with "not compositing frames". Everything above is **measurement**, not a picture. Tasks 3
and 4 ask for the globe to be shown at 1280 / 1920 / 3840 in three themes; that needs a session
with the pane visible.

---

# T6 handoff — Part 4 (the copy audit) is all that remains

| | Status | Where |
|---|---|---|
| Part F — expert reference lock | Merged | `main` @ `8c1d67a` |
| Parts A–E — the fold | Merged, browser-verified | `main` @ `dbdd261` |
| Project-creation gate, admin projects/assignment | Merged | `main` @ `dbdd261` |
| Part 3 — the compute rewrite | **Merged, proven** | `main` @ `dbdd261` |
| **Part 4 — the copy audit** | **Inventoried, not rewritten** | — |

`main` is at `dbdd261`. 843 checks across 17 suites pass. No migration is pending; the schema
stays at 0012 and `/readyz` is unaffected by anything merged since.

The false-Red defect that dominated the last two sessions is **fixed and merged**. What follows in
§1 is kept as the record of what it was, because it explains why the architecture is now what it
is. §4 is the outstanding work.

---

## 1. The defect that is now fixed (record, not a to-do)

Two computations existed for the same project. The server computed status from documents and
stored it; the legacy dashboard recomputed it in the browser. They disagreed:

| Case | CPI | Server | Legacy browser | |
|---|---|---|---|---|
| healthy | 1.05 | Green | **Red — 40 of 40 seeds** | deterministic |
| on-budget | 1.00 | Green | **Green 38 / Amber 2** | seed-dependent |
| distressed | 0.833 | Red | Red | agreed |

**Mechanism.** `LinSim.buildSignals` expects a time series; `ingest.js` never passed one, so it
fell through to `deriveSeries(metricValue, seed)` and invented one from a single value plus a
seed. That fabricated series tripped the CUSUM Anomaly Monitor. The seed derived from the project
id, so two identical projects could differ. On the healthy case the browser reported
`evm: green, mc: green, doc: green, cusum: red`, and the fusion promoted that one red to Red.

**After the rewrite, re-measured:** stored, `getProjectFusion` and `deriveHealthState` all return
Green for cpi 1.05, Green for cpi 1.00, Red for cpi 0.833. There is one computation now.

---

## 2. How Part 3 was done, and what to preserve

**Four functions, not 79 edits.** The split counted 79 call sites across eight files. Rather than
edit them, `getModuleStatus`, `getCategoryStatus` and `getProjectFusion` kept their names and
signatures and changed where the answer comes from: they read the stored `computed_results` row.
Every call site became correct without being touched.

- **`assets/js/taxonomy.js`** replaces `categories.js` on the application. The taxonomy is
  carried over unchanged, because it is data. The derivation is not.
- **`LinResults.prime(projectId, row)`** is how a stored row reaches the accessors. The loaders
  that already fetch `projectresults` call it. **The cache deliberately cannot fetch**: a module
  that could fetch would eventually fetch during a render, and a render that issues a request can
  audit an evidence view the participant never asked for. Note the row is `resp.result`, not
  `resp` — priming the envelope silently yields `undefined` statuses.
- **`deriveHealthState` has no fallback derivation.** No stored row now means "Awaiting analysis".
  Restoring a fallback would restore the defect.
- **Enforced by absence.** `index.html` loads none of `sim.js`, `simulations.js`,
  `categories.js`, `deepdive.js`. Verified by resource timing across all six page sections.

**`research/deepdive.html`** is the one surface that computes in the browser, on purpose: it
re-runs the models live to show the working. Nothing links to it, it holds no data of its own, and
every action it would call is refused server-side without the right role. It is not a security
boundary and does not claim to be — the guarantee is that no participant-facing route loads a
client-side model.

---

## 3. Verified in a browser (all merged)

| Guarantee | Result |
|---|---|
| Full workflow, no page load | Verified — `navigation` entries stayed at 1 |
| Profile once, no questionnaire nav | Verified — absent on reload and fresh sign-in |
| Nav sets | Verified — participant topbar `[]`, admin `["Admin"]`, dock identical |
| Platform theme | Verified — `radar.css` the only palette |
| No raw ULIDs | Verified — zero across every page section |
| Every field labelled | Verified — zero unlabelled fields |
| No module ids in text | Verified — zero across every page section |
| **Compute libraries absent** | **Verified — resource timing, all six sections** |
| Layout | Verified — clamps to 1280px at 1920 and 3840, no overflow |

**Known open design gap** (not a bug, and Part 3 does not address it): the decision sequence is
keyed to **assignments**, not projects. A participant can no longer create an unassigned project,
so the dead end is closed for them, but Part B's workflow is still not one continuous chain — a
participant uploads to a project and decides against an assigned scenario, and nothing links the
two.

---

## 4. PART 4 — the outstanding work

Inventoried, not rewritten. **Do not rewrite before re-reading the inventory**, and note that a
partial sweep is worse than none: half-converted spelling is more jarring than uniform British.

Run `python tools/copy_inventory.py` from the repository root to regenerate these numbers. It
separates user-facing copy from comments, which matters more than it sounds.

### Em dashes: 212 in user-facing copy

The naive repository-wide count is **1015**. The count in copy a user can read is **212**. A sweep
driven by the first number rewrites a great deal of prose nobody reads and reports success.

| Count | File | | Count | File |
|---|---|---|---|---|
| 53 | `assets/js/detail.js` | | 8 | `assets/js/store.js` |
| 30 | `assets/js/signals.js` | | 7 | `assets/js/app.js` |
| 21 | `index.html` | | 7 | `assets/js/assistant.js` |
| 16 | `assets/js/auditor.js` | | 7 | `assets/js/decision-ui.js` |
| 14 | `assets/js/workspace.js` | | 6 | `assets/js/deepdive.js` |
| 11 | `assets/js/admin.js` | | 3 each | `tests.html`, `charts3d.js`, `export.js`, `forcenet.js`, `projectnet2d.js` |
| 10 | `assets/js/admin-ops.js` | | 1–2 each | `neural_flow.js`, `documents.py`, `extraction_client.py`, `ingest.js`, `research/deepdive.html` |

### Spelling: American English, decided

Raw tally in strings is British 55 / American 162, but the headline is misleading and **two
exclusions are load-bearing**:

- **`center` (122 occurrences) is CSS and geometry**, not prose. Not a spelling decision.
- **`analyze` is an `/exec` action name** — `writes.py:441` `DEFERRED_AI_ACTIONS`, and
  `store.js:519` sends `action: "analyze"`. **Renaming it breaks the facade contract.**

Excluding those, prose leans British: `authorised` 26, `recognised` 10, `behaviour` 8,
`organisation` 4, `summarised` 1. **American English is confirmed as the convention** — GWU is the
institution and the directors work US federal and commercial projects — so roughly **55 prose
instances change**, and no technical token is touched.

### Still to do, none of it started

- The em dash sweep (212), the phrasing and redundancy pass, and the empty-state, error-message
  and confirmation-dialog review across portfolio, project detail, upload, decision sequence,
  admin, profile and expert workflow.
- **The glossary** of the platform's own terms, applied consistently.
- **The sign-in page**, the named worst offender: "authorisation" two lines from "authorized";
  "Access is restricted to authorized users only" beside a sign-in form; "Need an account, or
  forgot your password?" as one control asking two questions; copyright sitting above the access
  notice when the order should be notice, attribution, copyright.
- **The two-audience notice.** T1a built a conditional notice keyed on `account_type`. Verify it
  still works after the fold. The research variant should be protective; the operational variant
  should be accurate about responsibility without implying the platform is a toy; the
  pre-sign-in state, where account type is unknown, must keep the restrictive text.
  **Draft both variants for the researcher's review. Do not adopt liability wording, and treat
  consent text as requiring IRB approval.**

Constraints for that work: **no behavioural change**, no layout change beyond what text length
forces, and no change to a string a test asserts against without updating the test and saying so.

---

## 5. Traps and environment

- **`preview_start` resolves `launch.json` from the shell's working directory.** From `Demo` it
  starts the dead `opus-gubernatio` app on 8099 — same brand, same title. It was started twice in
  one session and stopped both times. The tell: `api.js`/`boot.js` in the sources and **zero
  `.page` sections**. **Check `preview_list`'s `cwd` before trusting any browser session.** The
  working route is `preview_start({url: "http://127.0.0.1:8010"})` attached to a server started
  separately.
- **`server/tools/dev_serve.py`** runs the real app: fills `DATABASE_URL` only if unset, defaults
  to a gitignored repo-local file, migrates to head, and seeds B7b's StubExtractor with three
  recordings (`healthy`, `on-budget`, `distressed`) written to `server/dev_fixtures/`. The
  `on-budget` fixture has earned value exactly equal to actual cost, so the pathological cpi = 1.0
  case is reproducible on demand. Never on Render's path.
- **Duplicate function declarations silently win.** `decision-ui.js` had an internal `render()`
  and an exported wrapper also named `render()`; hoisting bound the export to the wrong one and
  the decision tab threw on open. Check for name collisions when adding a module export.
- **Browser caching bit once.** After editing a JS file the page kept the old copy while the
  server served the new one. Check `String(window.LinX.fn).includes(...)` if behaviour disagrees
  with the source; a fresh tab clears it.
- **`window.confirm` auto-dismisses** in the automated browser, so `commitPreJudgment` silently
  returns. Stub it to `true` when driving the decision sequence.
- **Re-renders clear programmatically set field values.** Set and submit in the same tick.
- **Every account in every existing suite is `account_type: "operational"`** — so any gate keyed
  on `account_type` is invisible to the suite by default. That is how the project-creation gate
  initially had no coverage while the full suite passed.
- **No `DATABASE_URL` default exists** (`settings.py:69-74`). Throwaway SQLite outside the
  repository, never production. One freshly migrated database per suite. Read counts from each
  suite's own `RESULT: n/n` line, never by grepping `PASS`/`FAIL`.
- `test_simulation` exits 1 on Windows from a `charmap` error printing mu; 27/27 under
  `PYTHONIOENCODING=utf-8`. `test_decision_ui_t4` prints a line containing `FAIL` that is the
  label of its own self-test.

---

## 6. Regression

**843 checks across 17 suites, all passing**, verified after the merge to `main`.

Both changes from the 838 baseline, stated where they happened:
- `test_features` 36 → **41**: five checks covering the project-creation gate.
- `test_decision_ui_t4` holds at 73/73; its guarantee-10 scan was repointed from the deleted
  `decision.html` to `index.html` and indexed by filename rather than list position.

---

# PART A (copy) — progress, and exactly what is left

Branch `t7-copy-and-globe`. **Not merged**: Part A merges only when complete, and 84 prose em
dashes remain. 843 checks pass at every commit.

## Done

| | |
|---|---|
| `218618d` | American spelling (79 words), the sign-in page, `index.html` em dashes (17) |
| `6cf2122` | Participant-facing em dashes (25) |
| `84f74d4` | `detail.js` em dashes (35), including the assistant prompt |
| `54d7338` | `COPY_GLOSSARY.md`, and the pre-judgment commit wording |

**Spelling is finished.** 79 words, British to American, in strings only. The sweep only ever
rewrites British into American, so it cannot touch `center` (CSS) or `analyze` (an `/exec` action
name). Three tests asserted `"not authorised"` against server refusals and were updated:
`test_assignment_blinding:244`, `test_export:302`, `test_research_identity:131`. They failed
first, which is how they were found.

**The assistant was instructed to write em dashes.** `detail.js:1155` told the model to put
`' — '` on the same line as a group heading, so the platform generated them at runtime. Fixing
static strings alone would have left that in place. Worth checking for again if new prompts land.

**The conditional notice works** after the fold and the Part 3 rewrite. Verified in a browser:
research is the pre-sign-in default with operational hidden, and they swap only when
`og-account-operational` resolves. Footer order is now notice, attribution, copyright.

## Left: 84 prose em dashes

Run `python tools/copy_inventory.py`, and the classifier distinguishes prose from placeholders.
**Of the original 212, only 165 were ever prose**; the other 47 are the standalone `—` meaning
"no value" in a table cell, which must stay.

| Count | File |
|---|---|
| 24 | `assets/js/signals.js` |
| 14 | `assets/js/auditor.js` |
| 11 | `assets/js/admin.js` |
| ~11 | `assets/js/detail.js` (remainder) |
| 7 | `assets/js/assistant.js` |
| 4 | `assets/js/deepdive.js` |
| 3 each | `tests.html`, `assets/js/export.js` |
| 1–2 each | `projectnet2d.js`, `charts3d.js`, `forcenet.js`, `neural_flow.js`, `research/deepdive.html` |

These are the legacy dashboard and researcher surfaces. The participant-facing path is done.

**Method that worked:** dump the strings with the emdash script, write explicit before/after pairs
in a script, run it, re-measure. Do not apply a blanket rule. A mechanical hyphen is its own tell,
and a mechanical comma reads only slightly better; each sentence wants a specific mark.

## Also left in Part A

- Task 7 across the remaining screens: empty states, refusal messages a participant can actually
  trigger, and tooltips on portfolio, project detail, upload, admin and the expert workflow.
  The pre-judgment confirmation and "Awaiting analysis" are done.
- Apply `COPY_GLOSSARY.md` consistently. The glossary exists; the sweep that enforces it does not.

---

# PART B (globe) — investigated, not started, awaiting approval

The brief requires the library choice to be approved before building. Findings:

## 1. What exists today

**MapLibre GL 4.7.1, CDN-loaded from cdnjs**, in `assets/js/app.js` only:

- `GL_CSS_URL` / `GL_JS_URL` at `app.js:591-592`
- `loadMapLibre()` at `app.js:598` injects the tag and rejects on `onerror`
- `showMapFailure()` at `app.js:714` is the existing fallback when the CDN is blocked or offline
- markers built at `app.js:849`, popup at `app.js:905`, `hideMapCard()` at `app.js:890`
- double-clicking a marker calls `openDetail(p.id)` (`app.js:856`) — that is the existing
  selection behavior the globe must reproduce rather than replace

**There is already a graceful-degradation path.** `app.js:733` checks `typeof maplibregl ===
"undefined"` and calls `showMapFailure()`. Any globe should reuse this shape rather than invent
one, and the existing map is the natural fallback target.

## 2. Coordinates

`hasCoords(p)` at `app.js:668` already gates on `p.lat`/`p.lng` being finite, and `app.js:845`
already warns when latitude exceeds ±90 (a lat/lng ordering mistake). So **projects without
coordinates are already a handled case on the map**, and the globe inherits the same question:
they must remain listed and reachable, not silently dropped.

Geocoding is referenced in `app.js`, `ingest.js` and `server/app/models.py`. **Confirm before
building** whether geocoding actually runs at project creation on the current server path
(`projectcreate` in `workspace.py`), because the projects created during Part 3 testing had no
coordinates and still rendered in the project list.

## 3. Library recommendation, for approval

**Recommend: `globe.gl` or raw `three.js`, CDN-loaded, with the existing MapLibre map as the
fallback.** Reasoning to weigh:

- It matches the existing delivery model. MapLibre is already CDN-loaded with a working failure
  path, so the globe adds no new *kind* of risk, only another asset on the same CDN.
- The repository has been bitten twice by dependency availability, so **vendoring the library
  into `assets/vendor/` is the safer option** and I would lean that way despite the size: it
  removes the CDN from the critical path entirely and makes the fallback about WebGL only.
- Fallback chain: WebGL unavailable or library fails → render the existing MapLibre map →
  MapLibre also unavailable → the plain project list. No blank panel at any step.
- Performance constraints from the brief are real on a single small instance: do not block page
  load, stop the animation loop when the tab is hidden or the view is left, and release the WebGL
  context on teardown. `hideMapCard()` and the existing view-switch are where that hooks in.

**Decide before I build:** vendored or CDN, and `globe.gl` or `three.js` directly.

Nothing in Part B has been written.

---

# T8 — geocoding, vendoring, and the globe

Branch `t8-geocode-globe`, **not merged**. `main` is at `c17e4fd`. 854 checks across 17 suites
pass at every commit. No migration anywhere in this branch.

| Stage | Status |
|---|---|
| Server-side geocoding (Nominatim) | Done, tested, live-verified |
| Near-miss handling (`Matched to:`) | Done, browser-verified |
| Stage 1 — vendor MapLibre | Done, verified served |
| Stage 2 — verify the four insertions | Done, found and fixed a colour bug |
| Stage 3 — vendor globe.gl | Done, verified served |
| **Stage 3 — build the globe** | **NOT STARTED** |

## What was learned about Nominatim, from live calls

Response shape: always HTTP 200 with a JSON array. No match is `[]`, not a 404. A match carries
`lat`, **`lon`** (not `lng`), `display_name`, `class`, `type`, `importance`.

Verified plausible: PHL `39.87397, -75.24382`; BNA `36.11958, -86.68266`.

**Two failure modes matter more than the not-found case:**

1. **A street address and a facility name concatenated returns `[]`.** "8000 Essington Avenue,
   Philadelphia International Airport, Philadelphia, PA 19153" finds nothing, though each half
   alone resolves. The original error message advised adding city and state, which that query
   already had; it now says to try one or the other, not both.

2. **The top hit is often nearby but wrong.** "Philadelphia International Airport, Philadelphia,
   PA" returns a Hampton Inn 1.5 km away. "8000 Essington Ave" returns "Mezzogiorno", a business
   at that street number. Both are correct for the string typed and wrong for the project.

   This is why `formattedAddress` (the geocoder's `display_name`) is surfaced at create, in the
   project list, on the project page and in the admin create flow. **Do not remove it.** A blank
   map invites a fix; a pin on the wrong building signals nothing.

   Deliberately NOT solved by raising `limit` and filtering on `class`/`type`: airports resolve
   as aeroway, but a postal facility, an office fit-out or a highway package will not, and that
   filter would encode an assumption that holds for one project type and fails for the rest.

## Colour carries meaning

Stage 2 found the create confirmation rendering a **successful** match in `--status-red`, because
it reused the error slot. Fixed: `ws-note` for a match, `ws-note ws-geo-warn` (amber) for a
missing position, `ws-error` only for an actual failure. Amber rather than red for "no map
position" because the project is fine and only its position is missing.

## Stage 3 — building the globe

Everything below is investigated but unwritten.

**Dependency is in place.** `assets/vendor/globe.gl.min.js`, 1.48 MB, verified served and
exposing `window.Globe` as a function. It bundles three.js, so there is no second file and no
version-compatibility question. `assets/vendor/` totals 2.3 MB with MapLibre; both load on demand.

**Where the map lives**, all in `assets/js/app.js`:

| | |
|---|---|
| `app.js:565` | the block comment describing the map view |
| `app.js:591-592` | `GL_CSS_URL` / `GL_JS_URL`, now `assets/vendor/` |
| `app.js:598` | `loadMapAssets()`, on-demand injection with an `onerror` reject |
| `app.js:714` | `showMapFailure()` — the existing no-blank-panel path, reuse it |
| `app.js:733` | the `typeof maplibregl === "undefined"` guard |
| `app.js:849` | marker construction |
| `app.js:856` | **`openDetail(p.id)` on double-click — the selection behaviour to reproduce** |
| `app.js:890` | `hideMapCard()`, where teardown hooks in |
| `app.js:668` | `hasCoords(p)` — projects without coordinates are already a handled case |

**Data.** `workspaceprojects` already returns `address`, `formattedAddress`, `geocodeError`,
`lat`, `lng` per project. Status comes from the stored row via `getProjectFusion(p)` in
`taxonomy.js`, which reads `computed_results` and computes nothing. **The globe must not compute
a status**, and `sim.js` / `simulations.js` / `categories.js` must still not load on any
participant-facing route.

**Degradation chain, no blank panel at any step:** WebGL unavailable or `Globe` fails to load →
the existing MapLibre map → MapLibre unavailable → the plain project list. Test WebGL with a
throwaway canvas and `getContext('webgl2') || getContext('webgl')` before constructing anything.

**Lifecycle, which is where this kind of thing usually goes wrong:**
- do not block page load — load on first open of the view, as the map already does
- stop the animation loop on `document.visibilitychange` when hidden
- stop it and release the WebGL context when the view is left; `hideMapCard()` and the
  radar/globe toggle are the hooks
- guarantee 6 asks you to *demonstrate* the loop stopping, so instrument it in a way that can be
  observed from the console rather than asserted

**Projects without coordinates stay listed and reachable.** They are not dropped because they
cannot be placed. The project list already shows them with "No map position".

**Theme variables only.** No private palette, same rule as every other screen. Status colours come
from `--status-green` / `--status-amber` / `--status-red` / `--status-nodata`.

**The radar is not to be touched.** Guarantee 1 is that it renders identically before and after.

## Remaining Part A copy work, unchanged

84 prose em dashes in the legacy dashboard and researcher surfaces: `signals.js` 24, `auditor.js`
14, `admin.js` 11, `detail.js` ~11, `assistant.js` 7, then singles. The participant-facing path is
done. Method that worked: dump the strings, write explicit before/after pairs in a script, run it,
re-measure. Never a blanket rule.

## Also worth knowing

- **The browser caches edited JS** while the server serves the new file. It bit this session
  again. Check `String(window.LinX.fn).includes(...)` if behaviour disagrees with the source; a
  fresh tab clears it.
- **PDF.js and SheetJS are still CDN-loaded** at `index.html:1060` and `:1062`. The same corporate
  network that would have blocked MapLibre will block those, breaking client-side PDF extraction
  and the audit export. Not in scope for T8, but the same argument applies.
- The geocoding tests stub `app.geocode.geocode`, so the suite stays offline and never spends
  Nominatim's rate limit. Keep it that way.
