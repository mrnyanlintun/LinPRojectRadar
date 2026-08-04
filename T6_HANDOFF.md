> **READ `NAMING_AUTHORITY.md` BEFORE ANY CONTENT WORK.** It is the authority for what the platform
> and its analytical taxonomy are called, and it carries the standing description that every
> user-facing surface quotes verbatim. It lives in the repository so it cannot fail to reach a
> session, which it did three times while it lived outside. Read it before this handoff, not after.

> **SECTION NUMBERING IS RETIRED, from 2026-08-02.** Five sessions collided on T-numbers in one
> day (T21 taken twice, T23 renumbered from T21, T24 taken twice, T26 renumbered from T24 at
> merge time). New sections are headed **`# <yyyy-mm-dd> — <task name>`** and appended at the TOP,
> newest first. Never renumber an existing section; on a merge conflict keep both sections whole.
> The historic T-numbered sections below keep their names as history.

# 2026-08-05 — EXTRACTION STOPS SUBSTITUTING A NEARBY VALUE. THE MODEL WAS ACTUALLY CALLED.

Full detail in `REPORT_2026-08-05_extraction-substitution.md`. **Server 39 suites, 2161/2161
(was 38/2042); `tests_render.html` 86/86; `tests.html` 51/51.** Seven faults injected, all
detected, all reverted byte-identical, baseline re-measured after each. No migration.
`simulation/` untouched.

## THIS RAN AGAINST TWO REAL PROJECT A DOCUMENTS, WITH A LIVE KEY. THE FIRST TIME EITHER HAS EVER HAPPENED.

The 2026-08-04 handoff said the same two blockers (no key, no real documents) would stop the next
real-extraction session. They did — this session started identically blocked — until Lin supplied
a key and the path to the real files. **Neither is in this repository and neither should be
assumed to be here next time.** The path used:
`Desktop\Project Samples\2028-11-01_ProjectA_Design_Revised_Verified_Corpus\ProjectA_Design\Period_01`.

## The defect, exactly as briefed, reproduced on the first real call

`2026_04_09 100% INFO - Contract Value Summary P01.docx` (classified `contract_value`, 0.97):
`original_contract_sum` correct at 5,874,620 and the two pending authorizations correctly
excluded — but `project_start_date`/`project_end_date` came back as **`2026-03-01`/`2026-03-31`**,
which is the document's REPORTING PERIOD (`Period \| 1 March 2026 through 31 March 2026`),
mislabelled as a project baseline. **The document has no project baseline dates at all.** Both
values were well-formed, in-range dates — neither `validate_doc_risk_score` nor
`validate_numeric_fields` could have caught this, because both guard the VALUE and a substituted
date is a perfectly good date. **The prompt is the only place this can be caught.**

`2026_04_06 100% INFO - Design Activity Status U03.docx` (classified `schedule_update`, 0.95): a
genuine miss, opposite direction — `activities_planned` (should be 9, the activity table's row
count) and `milestones_json` (should carry that table) both came back null, while six genuinely
absent fields correctly stayed null.

## The fix, and why it is two changes, not one

**Label-matching**, generalised across the whole field vocabulary (not just dates, per the
brief): a field is returned ONLY when the document states it under a matching label; a
same-typed value under no matching label is never a substitute. Checked, not assumed: no field in
the 87-field vocabulary legitimately needs a MODEL-derived value — `NAMING_AUTHORITY.md`'s own
"reads the reported figures" wording already committed to this, and CPI/SPI (the one genuinely
derived pair) are computed server-side, never asked of the model.

**`milestones_json`'s shape hint**, separate and opposite in direction — the miss was
under-application of "read what's there", not over-application. Nothing told the model a
document's own activity table qualifies as a milestones source or how to shape a whole table into
one JSON field. Tightening only the anti-substitution rule risked making this WORSE (a stricter
"never infer" could argue counting table rows is inferring); the fix explicitly says counting a
table's own rows is reading a stated fact, not inferring one.

**Acceptance test, run against production code via `real_extraction_regression.py`: 16/16.**
Re-run against the reverted (pre-fix) prompt: 11/15, failing exactly the two conditions the
defect predicts. The check is not vacuous.

## THE MILESTONES_JSON MERGE GAP IS CONFIRMED STILL OPEN, AND WAS NOT CLOSED

Exhaustively re-checked against the code (2026-08-02 reconciliation report's finding, still
true): `milestones_json` is requested by `schedule_update` and `monthly_report`'s field lists,
and now — after this fix — genuinely comes back from the model. It has **zero writers** into
`signalInputs`; `extraction_merge.py`'s per-type emission tables have no branch for it.
`field_registry.py` declares `milestoneHistory` (the SI-side name) `servable: False`. **Not a
one-line change**: closing it needs real date parsing (below), a SERIES-shape merge across
periods, and precedence rules that don't exist yet for this field, and eventually touches
`simulation/`, out of scope here. Reported, not started, per the brief.

## THE PIPELINE HAS NO REAL DATE PARSER, AND THE MILESTONE TABLE PROVES IT MATTERS

The activity table's date column carries four real shapes: `12-Jan-26`, `29-May` (no year),
`14 August 2026`, and `24-Mar-26 A` (a scheduling tool's actual-date marker). **None parse** with
`date.fromisoformat` — the ONLY date parser anywhere in `server/app` (`extraction_merge.py:442`,
`documents.py:386`), tested directly against all four. This is why the `milestones_json` hint
tells the model NOT to reformat table-internal dates to ISO: normalising `"24-Mar-26 A"` would
either drop the actual-date marker or fail, and there is no code today that would know what to do
with either outcome. Whoever closes the merge gap above needs to solve this first.

## Verify

`server/tools/test_extraction_prompt.py` is DETERMINISTIC — no key, no documents, always
runnable, 119/119 — and asserts the prompt's WORDS survive an edit. It cannot prove the fix
works; only the real-model run can. `server/tools/real_extraction_regression.py` is the live
re-check, deliberately NOT named `test_*` (a `test_*` suite that needs a key and two
uncommitted files would either fail or need skip logic every future runner has to remember —
silently downgrading "the suite passed" from fact to approximation). It refuses to run without a
key, writes nothing, and is what produced the 16/16 above.

## A repeat of the port-8010 trap from 2026-08-04

A dev server left running on port 8012 from the prior session was still serving PRE-FIX code
(the pre-2026-08-04 `extractsignals` wiring) when first checked. Stopped; a fresh instance on
8013 was confirmed to be running current code before any harness number was trusted. **This is
the second time in two sessions.** Check what a port is actually running, every time, not once
per task.

## Open, carried forward

- `milestones_json` merge gap (above) — needs real date parsing first, then a SERIES-shape merge,
  then `field_registry` and eventually `simulation/` changes.
- Only two of 27 document types have ever been run against the real model
  (`contract_value`, `schedule_update`). The fix generalises by design across the whole
  vocabulary; the evidence does not, yet.
- The key and the two real files are not persisted anywhere. The next real-extraction session
  starts exactly as blocked as this one did, unless Lin supplies both again.

# 2026-08-04 — PMP UPGRADE RUN 2: THE RESOURCES THREAD, AND THE SPACING RULE

Full detail in `REPORT_2026-08-04_training-resources-thread.md` — **it leads with the effect
figures and the spacing rule**, which are what Lin corrects and what run 4 depends on. Second
secondary thread, following run 1's pattern without redesign. **Server 2000/2000 across 37
suites** (new `test_training_resources.py` adds 63), every file against a FRESH DATABASE.
`tests_render.html` **80/81 — the SAME pre-existing gap**, confirmed by name and text.
`tests.html` 51/51. Eight faults, all detected, all reverted byte-identical, baseline after
each. No migration.

## THREAD OPENING PERIODS ARE NOW DERIVED, NOT HAND-PICKED

Run 1 moved the quality inspection to period 6 BY HAND after it collided with the scheduled near
miss. `thread_opening_periods()` now derives openings: start at 5, step by 1, **skip any period
a discrete event reserves** (period 4), and **raise** rather than allocate past
`PERIODS_TOTAL - 3`. It returns `{dsc: 5, quality: 6, resources: 7}` — **reproducing the two
periods already verified against rather than renumbering them**, which is what makes it a rule
and not a rewrite. `DSC_PERIOD`, `QUALITY_INSPECTION_PERIOD` and `RESOURCE_SHORTAGE_PERIOD` all
read from it.

**RUN 4 MUST READ THIS: the rule supports EXACTLY THREE live secondary threads at the current
run length.** A fourth is refused with a stated reason (a check proves the refusal fires). Run
4's "spine plus three for a hard run" is exactly at the ceiling with nothing spare. Raising it
means changing `PERIODS_TOTAL`, `THREAD_OPENING_FIRST_PERIOD` or the three-period play-out
reserve — a deliberate decision, not something to discover by hitting the refusal.

## CREW ADEQUACY IS A MULTIPLIER ON EARNING, NOT A CHARGE

The structural difference from quality. One line — `ev_factor *= crew_adequacy` — puts it in the
same chain as the deferral penalty and the restart loss, so **while crews are short EVERY period
earns less, whatever the trainee spent it doing**: escalating, reworking, absorbing, or
accelerating. Proven head to head on states differing only in adequacy (a constructed input to a
pure function, stated as such, because no real decision sequence isolates it). At full adequacy
it multiplies by 1.0, so a run that never meets the shortage is untouched. **Accelerating with
scarce trades costs 1.8x the premium and adds 0.25 extra hazard.** Because the cost comes out of
earning rather than a line item, the period notes and the debrief both name it, or a trainee
reads lost EV as bad luck.

## TWO DEFECTS OF MINE, BOTH FOUND BY THE CAMPAIGN NOT THE SUITE

1. **The screen told a lie the state did not.** `resource_position` omitted `resolution`, so the
   JS ternary always fell through and **a trainee who paid a premium was told they had
   resequenced**. 61 server checks passed while this was true, because every one asserted on
   state and none on the sentence. The BROWSER DRIVE caught it. Same lesson as run 5's
   most-severe-contributor marker: asserting the mechanism does not assert the wording.
2. **A check that crashed instead of failing.** Its first version indexed
   `position["resolution"]`, so the fault raised `KeyError` and the suite died **printing no
   `RESULT:` line at all** — the failure mode that skims like a clean run. `.get()` now.

## BUDGET, AND ONE CORRECTION TO RUN 1'S PREDICTION

Came in around 80%. Run 1 predicted verification is a fixed per-thread cost that will not
shrink; **half held.** The WIRING did shrink because the pattern existed. VERIFICATION did not,
and the browser drive is why — bootstrapping an operational account and session token by hand is
still the most expensive step and still the one that finds the most. **Build a reusable fixture
for it before run 3** rather than inside a thread task, where shared infrastructure gets shaped
by one caller.

## STILL OPEN

`build_recommendation` reasons only about the claim — now two threads' worth of open matters are
invisible to it mid run. Overdue; run 4 at the latest. Production still lacks migrations 0018
and 0019.

---

# 2026-08-04 — PMP UPGRADE RUN 1: THE QUALITY THREAD, AND THE THREAD PATTERN

Full detail in `REPORT_2026-08-04_training-quality-thread.md` — **it leads with the pattern**,
since three more runs (`training_pmp_upgrade_roadmap.md`) copy it. New track, separate from the
now-complete `training_mode_roadmap.md`: threads, not runs of different length — one spine
(dispute) plus secondary threads that open and close inside it, competing for the same float
and contingency. This run is the first secondary thread built on top of the complete run-1-to-5
build, and the first proof the shape generalises.

## THE PATTERN: event, own verbs, effect table, registration

A thread type is four things. Quality (failed inspection, `QUALITY_INSPECTION_PERIOD = 6`,
clear of the standing period-4 near miss) opens via the SAME discrete-trigger block `dsc` and
the near miss already use; decides through its OWN three verbs (`accept_nonconforming /
rework_now / rework_later`, **not** the dispute's escalate/absorb/defer, which `dsc` reuses);
carries a designed effect table (`QUALITY_FIGURES`, beside `EVENT_FIGURES`); and registers via
`allowed_decisions` (unions the verb sets while open), `quality_position` (mirrors
`dsc_position`), `training.py`'s `_state_view` (`quality_notice`, same shape as `dsc_notice`),
and the debrief (`quality` outcome alongside `closed`). It closes one of three ways, all
terminal statuses on the one dict: `resolved`, `accepted` (permanent, non-growing closeout
exposure), or `forced_resolved` (the state closes it without a decision, in the same
period-open trigger the opening lives in).

**DIVERGED FROM `dsc` ON PURPOSE: quality does NOT reuse the dispute's verbs.** `dsc` does,
because a site condition is still a notice matter under the same clock family. Quality is not a
claim, and reusing the dispute's verbs would have let one act decide two matters at once — no
real choice, so no real competition. **Carried forward to run 2**: give resources its own verbs
too (pay premium / resequence / accept delay), not the dispute's.

## COMPETITION IS PROVEN, NOT ASSERTED

`escalate` and `rework_now` both move `float_consumed_days` — the SAME counter, no
`quality_float` pool. A fault that gave `rework_now` its own float pool was caught precisely by
a check asserting on the shared counter after each of two different threads' actions from the
same starting state, not by checking either thread's own status. **Server 1937/1937 across 36
suites** (new `test_training_quality.py` adds 39), `tests_render.html` **80/81 — the SAME
single pre-existing gap** (production read path, session token), `tests.html` 51/51. **Six
faults, all detected, all reverted byte-identical, baseline rechecked after every one.**
Browser-driven: a $12,000,000 contract produced a $48,000 defect exactly, read back from the DOM
at period 6 with the dispute, the site condition, AND quality all live at once.

## SESSION USAGE RAN CLOSE TO A FULL SESSION, NOT HALF

Wiring across five files fit the 50% target; verification (fault injection against a live
suite, plus a browser drive that needed a hand-bootstrapped operational account and session
token, since no existing fixture does this for training) did not. **Runs 2 to 4 should budget
per-thread verification as a fixed cost, not assume it shrinks.**

## LEFT OPEN

`build_recommendation` does not yet reason about an open quality matter — out of scope for this
run, a candidate for a follow-up or for run 4's composition/debrief work. Production still
lacks migrations 0018 and 0019, unchanged again this run (no new migration needed; the quality
dict lives inside `TrainingRun.state`'s existing JSON column, structurally excluded from both
export kinds the same way run 1's isolation excludes the rest of that column).

---

# 2026-08-04 — TRAINING MODE RUN 5: THE LEDGER, THE FULL RECOMMENDATION, TWO NAMING FIXES

Full detail in `REPORT_2026-08-04_training-detail.md` — **it leads with the recommendation
quoted in full as it renders**, which is what Lin judges. **Server 1898/1898 across 35 suites**
(new `test_training_detail.py` adds 65), `tests_render.html` **80/81** (group 10 adds 17; the
one red is STILL the same pre-existing production-read-path gap, by name and text),
`tests.html` 51/51. Eight faults, all detected, all reverted byte-identical, baseline after
each. Browser drive read the recommendation and an expanded category back. No migration.

## THE CATEGORY ROLLUP IS NOT WORST-STATUS-WINS. Measured, and it changes the display.

`dst_fuse` is Dempster-Shafer with Red at 1.5x; the status is the highest-belief band. **Across
a ten period run the category status differs from its worst contributor in 47 of 80 cases** —
Cost Risk fuses to GREEN with a RED contributor. So the brief's "which one drove it under
worst-status-wins" describes a mechanism the platform does not have. The ledger therefore names
the **most severe contributor** (true, and what a PM scans for) and, where the category differs
from it, says so in place: "Combined from 8 computations by evidence combination, not by taking
the worst: PERT Network Criticality reports Amber." Do not "simplify" that line back into an
implied maximum; checks in both halves hold it.

## The render path is SHARED, and the drill-down lives in the shared half

`workspace.js` now exports `buildProjectDetailHtml(result, opts)` + `wireCategoryRows`;
training calls them. Same name tables, same markup, same dots. `opts.expandable` renders
categories as disclosures carrying their contributors; `opts.abstained` renders abstentions.
**Default rendering is byte-unchanged**, so the real project panel is untouched (its 70 checks
pass) — the drill-down is one flag away there and enabling it is Lin's call.

**An abstention is a NAMED ABSENCE: no value, no colour, NO DOT.** Derived server-side from the
registry (`_abstained_by_category`), excluding unported (`A4.1`) and group D, whose exclusion
is structural rather than a per-period abstention.

## The recommendation is generated, never narrated

`build_recommendation(state)` in the engine, pure. What / why / who / to whom / by what means /
next step / by when, plus a `basis` block of the raw figures the tests match against the state.
Service is form-specific: A201 says **email is not service** (Article 15), ConsensusDocs
carries the 21-day second step, FAR goes to the Contracting Officer and raises certification.
**Policy is `entitlement first, maximal correction`, carried on the payload** — deliberately
fallible: it recommends notice on a 5,000 dollar impact under a collaborative owner where
absorbing is the better call. **Nothing on screen hedges**; an oracle that admits its own
unreliability is no longer something the trainee must weigh.

## Three verification defects found by the campaign, all mine, all fixed

1. **A check that could not fail**: the id scan ran `\b`-anchored regex over `textContent`,
   which concatenates labels ("Project HealthA3show...") and destroys word boundaries, so it
   matched nothing regardless of content and fault D1 sailed past. Now scans **leaf elements**,
   where one element is one label.
2. **A check that matched its own comment**: the static "most severe contributor" assertion was
   satisfied by a comment quoting the phrase; deleting the real marker left it green. Now
   matches emitted markup (`ws-worst`). Same failure as the notices work.
3. **A false positive in the detector**: `[A-D]\d+` matches `A201` — the AIA form name. A
   category id is a letter plus EXACTLY ONE digit; a second digit now disqualifies. Verified
   against `AIA A201-2017`, `ConsensusDocs 200`, `Section 15.1.3.1`, `FAR 52.243-4(d)`.

Also: my own first "most severe contributor" marker used an EM DASH (forbidden). Fixed to a
parenthetical, with a check over quoted literals only — a first version of THAT check went red
on an em dash in a comment, which renders to nobody.

# 2026-08-04 — TRAINING MODE RUN 4: REGIMES ACROSS THE RUN, DEBRIEF, DISCLAIMER. THE BUILD IS COMPLETE

Full detail in `REPORT_2026-08-04_training-regimes.md` — **it leads with which of the four
contract traps are reachable: ALL FOUR**, each with its own citation and failure, each
fault-proven. **Server 1833/1833 across 34 suites** (new `test_training_regimes.py` adds 45),
`tests_render.html` 62/63 (STILL the same single pre-existing gap, by name and text),
`tests.html` 51/51. Six faults (R1–R6), all detected distinctly, all reverted byte-identical,
baseline after each. One full browser run PER CONTRACT FORM, deadlines differing per the table,
each ending in the rendered debrief. **Production still lacks 0018 AND 0019 — both must be
applied before the first training run.** Training mode is feature complete.

## The four traps, and the geometry that makes trap 1 exist

A DIFFERING SITE CONDITION is discovered on day 3 of period five: **17 days old at that
period's decision — inside A201's 21 day claim window, outside its 14 day DSC window (Section
3.7.4)**. That is the only decision point in a run where the 21-day belief and the truth
diverge, and it is why the discovery day is 3, not 10. The DSC is a SECOND matter with its own
derived clock (`dsc_position`), never conflated with the claim's. Under A201 it is
unpreservable at this geometry, deliberately. ConsensusDocs: preserved iff escalated at the
first opportunity (stop-and-prompt, 3.16.2). FAR: preserved iff undisturbed — one period of
continued work loses it (52.236-2(a)).

- **Trap 2**: ConsensusDocs escalation goes `noticed`/`conditional`; the NEXT period's defer is
  going quiet (Section 8.4) and kills it; any active decision lands the documentation and books
  the CO one period later than A201. Period-grain abstraction, stated as designed.
- **Trap 3**: the run 2 lookback, now over a claim that GROWS 0.25% of value per deferred
  period under FAR (this reconciled ONE run-2 check: 90,000 → 105,000).
- **Trap 4**: crossing 100,000 during the LAST deferred period makes an immediate escalation
  uncertified → lost (52.233-1). The trap is the crossing: wait a period and certification is
  carried; start over the threshold and it always was. Needs a sub-$6.67M contract value.

**ONE ACT SERVES EVERY OPEN MATTER** (escalate notices both claim and DSC, absorb absorbs
both, defer defers both); the act's costs are paid once, each matter's entitlement decided by
its own clause. The escalation float curve prices on the OLDEST open matter.

## The debrief and its counterfactual

`trainingdebrief`, COMPLETE runs only. Spent / closed / why-per-incident (acceleration
attribution read from the recorded cause; scheduled incidents honestly unattributed) / the
counterfactual as a REPLAY: same engine, first decision swapped to escalate, later decisions
verbatim. Three honest outcomes: computed; "you escalated first, the counterfactual is the run
you played"; or "the replay diverges structurally" with the reason — NEVER estimated across a
divergence (fault R6 made it estimate; the check went red). The debrief needed no new capture:
runs 2–3 stored everything.

## The disclaimer

`build_disclaimer` in the brief AND debrief: governing form, jurisdiction, "periods are
routinely amended in negotiation... check which rules actually govern", and sourced-vs-designed
marking of every figure. NO liability/consent language composed — asserted mechanically.

## Worth knowing after the build

- **Item 14 is OUTSTANDING AND LIN'S**: A201/ConsensusDocs periods rest on law-firm summaries,
  not the licensed documents. Reported, not attempted, per instruction.
- **Open on the roadmap**: items 1–3 (designed figures await correction), 14, 16–18 (deferred),
  and the two production migrations.
- **The container's proxy now BLACKHOLES `accounts.google.com/gsi/client`** — a
  parser-blocking script in index.html — so DOMContentLoaded hangs forever in Playwright.
  The browser drives `page.route(...).abort()` it; password sign-in does not use it. Any
  future DOM drive here needs the same, and earlier sessions' "it worked" predates the proxy
  change.
- **Two suite defects found by this run's own verification, again**: a fixture assuming the
  hazard SWO fires at period five (it fires at six, after the restart shadow), and an R6
  KeyError crash-not-fail (now `.get` with the fault reading as a red check). Also one
  premise corrected: the accelerated run's counterfactual IS computable — the SWO schedule
  is invariant to swapping the first decision.
- **A201's service rule and the IDM 60-day waiver are brief content, not mechanics.** The
  remaining A201 texture if training ever gets a run 5.

# 2026-08-04 — TRAINING MODE RUN 3: EFFECT TABLE CORRECTIONS, DISCRETE EVENTS, NARRATION

Full detail in `REPORT_2026-08-04_training-events.md` — **it leads with the revised effect
table and the event constants, the two things Lin corrects.** Stacked on run 2's branch (PRs
#207/#208 unmerged at branch time). **Server 1788/1788 across 33 suites** (new
`test_training_events.py` adds 42; run 2's suite reconciled to the corrected table, 54/54),
`tests_render.html` 62/63 (STILL the same single pre-existing gap, confirmed by name and
text), `tests.html` 51/51. Eight faults (E1–E8), all detected distinctly, all reverted
byte-identical, baseline re-run after each. Browser drive included a full incident. **No new
migration; production still lacks 0018 AND 0019.**

## The four corrections, and one premise corrected back

- **Deferral was already not free** (run 2 built 3 float days + 0.3% cost drift per deferred
  period); what was missing was VISIBILITY. `state.period_changes` now states each advance's
  float/cost/contingency/credibility deltas with plain-language notes, rendered as "What the
  last period cost". The drift figures stand as run 2 set them, for correction not
  re-invention.
- **Escalation cost is a curve**: base (4 exacting / 3 steady) + 2 days per full period the
  position sat open, cap 12, derived FROM the notice clock so cost and clock cannot disagree.
- **Credibility is asymmetric**: minus 1 instantly on escalation (which also zeroes earn
  progress); earning takes 2 concessions per point (`credibility_progress`).
- **The LD rate follows the brief's facility**: critical 0.05% / standard 0.035% (new default)
  / utilitarian 0.02%, third `trainingstart` condition. Derivation and rounding unchanged.
- **UNCHANGED BY INSTRUCTION**: the FAR lookback halving money where A201/ConsensusDocs bar
  the claim.

## Discrete events: deterministic, undisclosed, response-priced

`EVENT_FIGURES` is the single designed-constants table. Near miss at period four (in code,
NEVER in a response — and the `hazard` accumulator is likewise REDACTED from every view, or it
would forecast the second incident). Every near miss converts to an SWO (designed 1.0). The
incident costs 0.1%; the DAYS are the mechanism: respond_strong 6/5 days lost + 1 restart
period at reduced earning, respond_minimal 18/14 + 2. During an SWO the ONLY allowed decision
is the response (`allowed_decisions`, enforced in `advance` with named refusals both ways).
`accelerate` is a fourth standard decision: buys 4 float days at 1%×multiplier, hazard +0.5;
hazard 1.0 fires a second near miss next period with `cause: "acceleration"` recorded in
`incidents` — attributable for run 4's debrief, and impossible on a run that never accelerated.
An open dispute AGES (+30 days) through an SWO response and through an accelerated period.
Severity-depends-on-state is proven head to head: same incident, same minimal response, 24,000
exposure float-rich vs 80,000 float-poor.

## Narration: a layer, and never the judge — structurally

`training_narration.py` narrates a computed state; NOTHING reads the sentence back (the engine
never imports it), so the judge property is structural, not a prompt promise. No key / failure
/ raising narrator all degrade to figures-only with byte-identical state (asserted; fault E7
removes the guard and goes red). Test seam: `training.set_narrator_override`, mirroring
`set_extractor_override`. Em dashes stripped mechanically from model output. Narration runs on
decision/start responses only; `trainingstate` reads never cost a model call.

## Worth knowing before run 4 (the debrief)

- **All debrief raw material is captured already**: `incidents` with causes, `decisions`,
  `period_changes`, full `history` on the run row. Run 4 is a read.
- **A suite defect was caught during construction, again**: the reset-on-escalation check was
  first written as absorb-then-escalate — a sequence the single standing dispute cannot
  produce, so it passed against the no-op branch (a fixture building state by a route the
  application does not take). Now a stated constructed input to the pure function; run 4's
  events will make the sequence real.
- **`swo_conversion` documents the rate but is not wired as a probability.** Lowering it below
  1.0 needs a deterministic, state-derived tie-breaker to keep replay determinism.
- Run 2's suite now decides from the server's `allowed_decisions` in its run-out loop; any
  future test looping "defer" ten times will hit the period-4 SWO refusal.

# 2026-08-04 — TRAINING MODE RUN 2: THE LOOP — BRIEF, STATE, PERIODS, DECIDE AND ADVANCE

Full detail in `REPORT_2026-08-04_training-loop.md` — **it leads with the effect table and the
liquidated damages rule, which are the two things Lin corrects.** Builds on run 1 (branch
stacked on `claude/training-mode-gating`). **Server 1746/1746 across 32 suites** (new
`test_training_loop.py` adds 54), `tests_render.html` 62/63 (the SAME single pre-existing gap
as run 1, confirmed to be that one by name and text), `tests.html` 51/51. Seven faults, all
detected with distinct signatures, all reverted byte-identical, baseline re-run after each. One
full run driven in a real browser: brief, period 1, escalate, period 2, every figure exactly
per the effect table. **Production still unmigrated: 0018 AND 0019 both pending there.**

## THE CORE IS ONE PURE FUNCTION AND ONE SHARED TAIL

`training_engine.py` is pure — no clock, no randomness, no session. `advance(state, decision)`
is the ONLY implementation of the effect table (escalate spends float and a credibility point
and preserves entitlement if the window holds; absorb spends contingency and earns credibility;
defer spends nothing and runs the notice clock 30 days per period, with drift while the dispute
stays open). Determinism is asserted byte-for-byte at the engine AND over HTTP with two
accounts.

**`documents.run_and_store` is the extracted computation-and-storage tail** shared by the
document path and training period generation. `signal_inputs_from_state` fills all 76 merge
keys (None → abstention holds; docRiskScore abstains, asserted). There is NO training-only
computation path, and `server/app/simulation/` is untouched.

## THE TWO CLOCKS, AND WHY THE GEOMETRY IS WHAT IT IS

Event day 10 of period one, decision day 20 of every period: first decision 10 days after the
event, each deferral +30 days. So ONE deferral spends A201's 21-day and ConsensusDocs' 14-day
windows though only one period passed — deliberate, the teaching point. FAR has no bar: the
20-day lookback shrinks the recoverable fraction instead (0.5 after one deferral), and a FAR
deferral does NOT mark entitlement lost. `notice_position` is DERIVED from state per form,
never stored. Contract periods come from `training_us_contract_regimes.md` (WAS MISSING from
the repo — Lin supplied it; now committed; its own caveat about unverified A201/ConsensusDocs
figures stands, roadmap item 14).

## A CONTAMINATION POINT RUN 1 COULD NOT REACH, NOW CLOSED BOTH WAYS

The portfolio snapshot in `run_and_store` selects EVERY live result at or before the cutoff.
Once training results exist, a real project's stored snapshot would ingest training vectors and
vice versa. Now a vector enters only when its project's `is_training` matches the computing
project's. Fault-proven WITH a planted real vector — without one, the check passes whether or
not the filter exists (a first version of the check did exactly that, reading a snapshot key
that does not exist; rewritten against `insufficient_data`/`portfolio_size`).

## Things worth knowing before run 3

- **Two of my own verification defects were found by injection**: the suite crashed (no RESULT
  line) under fault F5 instead of failing — now guarded reds; and the vacuous portfolio check
  above. Both match the brief's listed failure modes exactly. Keep re-running faults after
  fixing a suite.
- **The engine had a real ordering bug the suite caught on first run**: escalation applied its
  own credibility penalty to the claim it carried (every first escalation docked 15%).
  `credibility_before` is read before the decrement; F6 re-injects the bug.
- **Designed figures stand in for roadmap items 1–3** (still OPEN): LD = 0.05% of contract
  value per day rounded to $500; impact 1.5%; contingency 5%; float 12 days; profiles
  `exacting`/`steady`. All in `training_engine.py` constants, led with in the report.
- **Acceleration multiplier and restart loss are in the brief but mechanically inert** until
  run 3's stoppages. ConsensusDocs' second step (documentation within 21 days of notice) is
  stated, not mechanical — run 3's natural territory.
- **Run 3 must not ship the event schedule in `trainingstate`**: today the full state travels
  (fine — nothing is hidden yet), but a discrete near-miss schedule a trainee can read defeats
  the exercise.
- `trainingadvance` stays gate-listed, unimplemented, reserved.

# 2026-08-04 — TRAINING MODE RUN 1: THE FLAG, THE GATE, AND DATA ISOLATION

Full detail in `REPORT_2026-08-04_training-gating.md` — **read the isolation section first**, per
its own lead. `training_mode_roadmap.md` did not exist anywhere before this run (checked working
tree, `origin/main`, full history, disk); Lin supplied it directly rather than it being
reconstructed from the task brief. It is now committed, with items 4 and 5 marked DONE.

**Server 1692/1692 across 31 suites** (new `test_training_gating.py` adds 43), `tests_render.html`
62/63 (the one red is pre-existing and unrelated, confirmed by stashing every change in this run
and reproducing the identical result), `tests.html` 51/51. Four faults injected against the
running modules, all confirmed applied, all distinct signatures, all reverted byte-identical,
baseline re-run clean after each. **NOTHING GENERATES A TRAINING PROJECT OR ADVANCES A PERIOD IN
THIS RUN.** No production migration applied — 0018 is written and verified on throwaway SQLite
only.

## `projects.is_training` IS THE ONLY COLUMN, AND IT IS THE SINGLE SOURCE OF TRUTH

Migration 0018: one `NOT NULL DEFAULT false` boolean on `projects`, indexed like `archived`
already is. Every dependent table — `computed_results`, and whatever training state a later run
builds — joins back to it rather than carrying its own copy, for the same reason the storage
redesign gave field kinds one home each: a duplicated marker is a marker that drifts.

**The one export path that needed a real filter: `project_health`
(`research_export.build_module_results_rows`).** It has NO `account_type` filter at all — its own
docstring says a project carries none — so before this run a training project's `ComputedResult`
rows (which roadmap item 7 will produce with the SAME shape as a real project's, since training
reuses the existing computations) were exactly as exportable as a real operational project's. One
`continue` keyed on `project.is_training`, in the single function all three formats (json/csv/xlsx)
funnel through, closes it everywhere at once. `participant_inputs` needed **no code change**: it
was already closed by construction (`_eligible_instances` filters to research accounts
unconditionally, and training is operational-only, refused server-side to research whatever the
flag says).

**The research chain (assignments/consents/decisions/transitions) cannot structurally hold a
training row**, because none of it is reachable except through a scenario naming a training
project as evidence — and that door is now shut too, at BOTH `adminscenariocreate` (creation) and
`adminassign` (its own pre-existing re-check, for a project renumbered after the scenario was
made). Full table-by-table accounting — touched, and considered-but-left-alone with the reason —
is in the report; do not assume a table is safe without reading that list.

## THE GATE REUSES THE `auditor` PATTERN EXACTLY, PLUS TWO THINGS THAT PATTERN DOESN'T HAVE

`training` is a fifth `FEATURE_KEYS` entry, same `adminfeaturesset` admin toggle, same
`effective_features` default resolution. `trainingstatus` is the only action with a real handler
this run; four more (`trainingstart`/`state`/`decision`/`advance`) are pre-listed in
`GATED_ACTIONS`, unimplemented, the same way `chat` and `audit` were before they existed.

**Research is refused UNCONDITIONALLY, not by the flag defaulting off.** Proven, not assumed: the
suite has an admin explicitly write `training: true` onto a research participant's stored
`features` (nothing stops that write — `adminfeaturesset` checks the CALLER's role, never the
TARGET's account_type) and confirms the refusal still holds, because it lives in
`RESEARCH_FORBIDDEN_ACTIONS`, independent of what the flag resolves to.

**The unauthenticated-caller gap is closed for training specifically.** `gate_action` itself still
leaves a sessionless caller alone (unchanged, documented scope note) — the exact shape of gap a
previous session found letting an anonymous `getportfoliohealth` bypass a flag a signed-in user
with it off was held to. `a_trainingstatus` does not lean on `gate_action` for authentication: it
calls `resolve_caller` itself first. Probed with no token and with a garbage token.

## THE OPERATIONAL-AND-RESEARCH COMBINATION IS POSSIBLE, AND account_type WINS

`a_adminassign` never checks a target's `account_type`, so an admin can assign an operational
account to a scenario and it can proceed through consent and decisions. Nothing catches that at
write time. What DOES hold: `research_export._eligible_instances` filters on
`account_type == "research"` and nothing else, so however such rows came to exist, they never
leave through `participant_inputs`. Unchanged by this run; stated because the brief asked for the
combination to be settled rather than assumed.

## Things worth knowing before the next training-mode run

- **The `auditor` nav button has a pre-existing hiding gap**: `radar.css` hides
  `[data-page="auditor"]` (the page content) but never `[data-nav="auditor"]` (the dock button
  itself), so the Auditor icon is visible to every operational account regardless of the flag —
  the page behind it still refuses correctly. Found while building `training`'s own CSS rule
  correctly (`[data-nav="training"]` IS hidden). Not fixed; out of this run's scope.
- **Items 1–3 of the roadmap (the elicited figures, the state variables, which decisions a
  trainee should get wrong) are still Lin's open decisions** and block everything from item 6
  onward. This run's items 4–5 do not depend on them.
- **`RESEARCH_FORBIDDEN_ACTIONS` and `GATED_ACTIONS` were extended together** for all five
  training actions, not just `trainingstatus`, so a later run adding a real `trainingstart`
  handler inherits both the gate and the refusal without touching either list.

# 2026-08-04 — extractsignals WIRED, DOCX READ LOCALLY. THE MODEL WAS STILL NEVER CALLED.

Full detail in `REPORT_2026-08-04_real-extraction.md`. **Green on merged `main`: server 38
suites, 2042/2042; `tests_render.html` 86/86; `tests.html` 51/51.** (On the branch alone,
36/1940, from a 35/1898 baseline; `origin/main` moved mid-session and added two training suites.) Eight faults injected, all detected,
all reverted byte-identical, baseline re-measured after each. No migration. `simulation/`
untouched.

## READ THIS BEFORE PLANNING ANOTHER REAL-EXTRACTION SESSION

**Extraction has STILL never run against a real document, and the deferred-list entry was only
one of three reasons.** The other two are inputs a session cannot manufacture:

- **There is no real project document on this machine.** 110 `.docx` files exist under `DEng`;
  every one is coursework or literature. Zero pay applications, zero registers, zero
  project-controls documents. The repository holds no `.docx`/`.pdf`/`.xlsx` at all.
- **No `ANTHROPIC_API_KEY` here.** Measured: `build_extractor()` returns the stub,
  `require_real=True` raises. It is set on Render, `sync: false`.

`server/tools/real_extraction_probe.py` is built and ready: it calls the REAL model on given
files, prints field by field what the model returned versus what the document says, runs both
guards, **refuses to run without a key**, and **writes nothing**. `--make-fixtures` writes three
synthetic documents with their truths printed. **Synthetic, and the tool says so** — the
2026-08-02 objection to substituting them still stands.

## What changed

- **`extractsignals` is dispatched**, as an ADAPTER onto `a_projectupload` — not a second
  extraction path. Authorisation, the content-hash cache, both guards, supersession, filing,
  observation emission and the project event log are inherited, so the two upload surfaces
  cannot drift.
- **`server/app/docx_text.py`**: stdlib `zipfile` + `ElementTree`, **no new pinned dependency**
  (`python-docx` is not in requirements and not in the venv). Tables render as pipe grids with
  the header row marked; `w:gridSpan` is expanded so a merged total keeps its figures under the
  right headings; `w:delText` is excluded so a tracked deletion cannot read as current.
- **The format branch is chosen from the BYTES, before the mime test.** `signals.js` sends
  `file.type || "application/pdf"`, so a docx the browser did not type arrives claiming to be a
  PDF. PDF document-block path and the plain-text 12000-char branch are unchanged.

## THE DEFERRED LIST: extractsignals WAS THE ONLY STRANDED ONE

Checked against every action registry. The other seven have **no handler anywhere** in
`server/app`, so their refusal is accurate. Two things to not re-derive:

- **`identifyonly` is deferred DELIBERATELY.** Its capability exists and is reachable —
  `classify_with_confidence` runs on every upload and the type/confidence come back on the
  response. Wiring it adds a second model call for an answer you already have. The reason is
  recorded next to it in `writes.py`.
- **A FEATURE FLAG IS NOT AN IMPLEMENTATION.** `chat`, `portfolioanalyze` and `audit` all have
  flags in `features.py`, which is almost certainly why `chat` was once reported stranded. It is
  not. `ingestcorpus` is a retired name; the live surface is `projectcorpus` in `files.py`.

## Traps that cost time here

- **THE BASELINE WAS WRONG FOR AN HOUR: the wrong interpreter.** The first full run read 5/35
  suites passing. The system Python has no `fastapi`. Use
  `server/.venv/Scripts/python.exe` and `server/.venv/Scripts/alembic.exe`. There is still no
  runner script in the repo and this is the second session to lose time to it.
- **A STALE DEV SERVER ON PORT 8010 WAS SERVING DIFFERENT CODE** — it answered `Unknown POST
  action: extractsignals`, neither the old deferred wording nor this change. Verification moved
  to 8011 and was confirmed to be this branch before any harness number was recorded. **Probe
  what is on a port before trusting a run against it.**
- **A STUB RECORDING CAN CARRY FIELDS THE REAL EXTRACTOR WOULD DROP.** The real client filters to
  `extraction_fields_for(doc_type)`; `StubExtractor` does not. A fixture recording `earned_value`
  for a `pay_application` stored fine and the guard correctly ignored it, which read exactly like
  a missing guard. **Key future recordings off `extraction_fields_for`.**
- **`tests_render.html` is 86 checks and the gap is environmental, not 62/63.** Bare tab 80/81;
  ResearchAdmin token 82/83 (an admin is not a member of any project); **PM token + a computed
  project 86/86.** That movement is the evidence the over-the-wire group is not vacuous.

## Open, carried forward

- **Part 3 is undone** and needs a real document set plus a key. Nothing else blocks it.
- **An image-only `.docx` is un-extractable.** One real file (`Coursera.docx`: six PNGs, no text)
  reads empty and is REFUSED. Correct behaviour, real limitation — a scanned Word document cannot
  be read where a PDF of the same content could. Adding image blocks reopens the OCR question the
  docx route was chosen to avoid. Lin's call.
- **The `docRiskScore` range guard has still never met a real document.** Only
  `submittal_register` requests the field among the 27 types.
- **Two upload surfaces now share one server path**, but the legacy `signals.js` panel has no
  period selector and leans on `_resolve_period`'s default. Whether it should exist is Lin's call.

# 2026-08-03 — CHART-DATA AND ABSTENTION SUITES: BOTH FINDINGS CHECKED, NEITHER STANDS

Full detail in `REPORT_2026-08-03_chart-abstention-tests.md`. **Nothing was changed.** Server
1649/1649, `tests_render.html` 68/68, `tests.html` 51/51, tree clean.

A session was briefed to rebuild two suites said to be vacuous. Both premises were checked
against the code and both are false. **Do not rebuild these suites on the strength of that brief.**

- **There is no chart-data suite and no JavaScript reimplementation of `_result_view`.** Zero
  matches for `_result_view` in any `.js`/`.html`. Nothing anywhere asserts `spi`, `cpi` or the
  ensemble scatter. The complete inventory is 30 Python suites plus the two HTML harnesses.
- **The D1 abstention checks already assert the abstention itself**, and carry the exact
  anti-vacuity control the brief asked for (section 1: "with every key present, all twelve
  COMPUTE ... without this, section 2's abstentions would prove nothing").

## The fault proofs, because the counts are not the evidence

- **Fabrication reintroduced**: `insufficient()` patched IN MEMORY to return a confident Green
  instead of declining. Nothing under `server/app/simulation/` touched on disk. Confirmed to take
  effect first (B2.4 on empty inputs returned `green / insufficient=False`). Result
  **100/100 → 60/100**, all twelve abstention assertions red.
- **Grafting faulted**: `graftUnmodelledFields` stopped carrying unmodelled fields forward.
  `tests_render.html` **68/68 → 65/68**, exactly the three coordinate-survival checks.

## THE TRAP THAT ALMOST PRODUCED A FALSE FINDING

**A fault can apply, be live in the loaded source, and still not reproduce the defect's shape.**
My first attempt made `hydrate` return early — a no-op on `LIN_PROJECTS` rather than a stripping
operation. The coordinate checks stayed green and a different check went red. Stopping there
would have reported those checks vacuous, wrongly. Aim the fault at the behaviour the check
claims, then confirm the behaviour actually changed, not merely the file.

Related: I probed "did the fault take effect" by string-matching `hydratePortfolio`'s source,
which read `false` for a fault living in an inner function. **A source-string probe is not proof
a fault is active**; the behavioural result is.

## Open, carried forward

- **A narrow real gap, not the one briefed**: the slim-row fields other than `status` (`cpi`,
  `spi`, `docRiskScore`, `simModuleCount`, `docCount`) are asserted nowhere against the live
  server. `slimOf()` in `tests_render.html` is hand-written and would not notice if `slim_row`
  changed. `status` is covered by the over-the-wire group.
- `test_d1_module_inputs.py` marks failures with `****`, not `FAIL`, unlike every other suite. It
  still prints a correct RESULT line and exits non-zero, so it is not the part 2 §5.5 crash class,
  but a cross-suite `grep FAIL` misses it.

# 2026-08-03 — AUDIT FIXES 1 TO 4

Full detail in `REPORT_2026-08-03_audit-fixes-1-4.md`. **Server 30/30 suites, 1649/1649 checks;
`tests_render.html` 69/69 (was 62); `tests.html` 51/51.** Every fix fault-injected, restored, and
the baseline re-measured after each. No migration. Finding 5 (the withdrawn scenario UI) not
touched.

## Finding 0 first, because it decided what finding 1 was

**The status contradiction was always on, not a supersede artifact.** Clean project, one upload,
one compute, nothing else: stored row Green, Signals Green, list row and legend "Awaiting
analysis". Every computed project on the portfolio surface was affected.

## What changed

- **`facade.py`**: `a_list` / `a_listslim` / `a_get` now resolve the live `computed_results` row
  and let it supply the status. Chosen over writing back into `project.doc` because a second
  copy drifts on the next recompute. One `IN` query per page, `superseded_by IS NULL`, status
  only (never `module_results` — it carries the action fields `_result_view` redacts).
  **`with_stored_status` returns a copy**: `project.doc` is a live ORM JSON column and assigning
  into it would be flushed to the database.
- **`tests_render.html`**: `fresh()` no longer calls `LinResults.prime` — nothing in production
  primes a list, which is exactly why it passed 62/62 while the list was broken. New
  over-the-wire group calls `listslim`/`list`/`projectresults` for real, borrowing the app's
  session token from `sessionStorage` (same origin, same tab). No token means a FAILING row, not
  a skip.
- **`research_assignment.py`**: `adminscenariocreate` requires an `evidence_package_id` that
  names an existing project; `adminassign` re-checks per scenario, audited, naming which one.
  Both, because the creation guard cannot reach scenarios that already exist.
- **`documents.py`**: `reference_kind` is consulted at decode time and a reference document is
  never queued for extraction. Stored with type/extraction/model/confidence all NULL. New third
  upload status `"filed"`; `workspace.js` renders it "filed, not analysed".

## THREE THINGS THAT WOULD HAVE READ AS CLEAN AND WERE NOT

**A downstream check passed with its own fault applied.** The finding-4 check asserted status
`filed` + class `reference` + no stored extraction. With the extraction skip removed it stayed
GREEN, because the reference-storage branch still created the row and the symptoms were
identical. Rewritten to assert the RULE — `StubExtractor.calls` must not contain the
specification's hash — plus a positive control that an analysable document IS in that list. Then
it failed correctly. **Assert the thing the design forbids, not a consequence of it.**

**The files-tab fixture recorded an extraction for the specification** under a comment reading
"documents the analytical extractor is never asked about". Comment stated the intent; fixture
guaranteed the opposite could not be detected. Same shape as the render harness's primed cache.
Recording removed — `StubExtractor` refuses unknown hashes, so a regression now has nothing to
answer with. Do not add it back to make a red go away.

**A backup that was never written made a restore silently do nothing.**
`cp x /tmp/b || cp x $SCRATCH/b` took the first branch, so the fallback never ran; the restore
later read the scratchpad path, found nothing, and left the fault applied. Caught only because
the baseline was re-measured. **Re-measure after every restore. The restore command succeeding
is not evidence.**

Also: `rm -f` on a SQLite file silently fails while locked on Windows, so a suite re-ran against
a populated database and failed on leftover state that looked like a code defect. Use a new
filename. And the CRLF needle trap bit again — the count assert caught it before a partial write.

## Open, carried forward

- **A stuck instance exists in the local audit database** (`AUD-P-001`, judgment locked, never
  revealable). Not altered, reported only. Whether production has one is UNKNOWN: production was
  not inspected.
- **Green project status alongside a Red contributing category** (`A3`, conflict 0.94) is still
  undiagnosed. Read the fusion rule against `tests.html`'s promotion assertions.
- Audit sections **5, 6 and 7 remain unstarted**.

# 2026-08-02 — FULL PLATFORM AUDIT, SECTIONS 1 TO 4 (STOPPED AT A CLEAN BOUNDARY)

Read-only audit, nothing changed. Full detail in `REPORT_2026-08-02_full-audit.md`.
**Sections 1, 2, 3 and 4 complete and committed. Sections 5, 6 and 7 NOT STARTED.**

## The four findings that matter, in order

1. **The list row says "Awaiting analysis" for a project whose stored result says Green.**
   Detail page reads it correctly; list row, legend and portfolio health do not. `a_listslim`
   and `a_get` return `project.doc` and never read `computed_results`, and compute never writes
   a status back into the doc. `tests_render.html` asserts this exact thing and passes 62/62,
   so its fixture supplies the stored result by a route the live app does not take. **Start
   here.**
2. **The study cannot be prepared through the interface.** Scenario, frozen condition sequence,
   frozen configuration and an attached decision support package are all enforced by
   `adminassign` / `researchreveal` and none has a UI. The scenario UI was withdrawn as
   describing "nothing the platform does"; the enforcement disagrees. Four hand-made API calls
   were needed to reach one recorded decision.
3. **An evidence-less scenario walks a participant into an irreversible dead end.** Preliminary
   judgment locks against an empty evidence panel, then reveal refuses forever. The stuck
   instance still exports.
4. **Reference documents go through the analytical extractor and vanish when it fails.**
   `_decide_filing` (the only caller of `reference_kind`) runs AFTER extraction. A spec that
   fails extraction is never filed at all. Directly contradicts `reference_kind`'s docstring.

## Where to pick up

Section 5 first, and 4.1 is the reason: at least one harness passes against a fixture the live
path does not reproduce. Then 6 (five naming candidates already recorded in the report's 1.5),
then 7.

**One thing section 4 could not settle**: whether the list has always shown "Awaiting analysis"
for a computed project, or whether the superseding upload done during section 2 broke it.
Compute a clean project, read the list without any intervening upload. Do that before anything
else in section 4.

**Also open, recorded not diagnosed**: a stored result with `project_status: Green` while
contributing category `A3` is `Red` with conflict 0.94. Read the fusion rule against
`tests.html`'s promotion assertions.

## Two things worth knowing before repeating this

- **`window.confirm` returns false in this container.** The preliminary-judgment commit silently
  did nothing and looked like a defect for several cycles. Override it before driving any
  confirm-guarded control.
- **Admin dropdowns populate on tab CLICK, and "People and access" is already the active tab.**
  So the scenario picker is always empty on first open of Administration. Click to the other tab
  and back. The participant pickers separately go stale after creating a user, needing a full
  reload.

# 2026-08-02 — THE SITE ON A PHONE

Full detail in `REPORT_2026-08-02_mobile-layout.md`. **Server 30/30 suites, `tests_render.html`
62/62, `tests.html` 51/51.** Two faults injected (dock/launcher overlap, upload/decision gate),
both detected, both reverted and re-confirmed against a freshly re-read stylesheet.

## What changed, in one line each

- `.list-item` on mobile: `display: grid` (4-34px overflow) to `display: flex; flex-wrap: wrap`
  with a forced line break after id/name. Desktop grid untouched.
- `.li-manage.btn, .li-open.btn` gets the 44px tap target; a single-class `.li-manage` rule LOST
  to `.btn.small`'s two-class specificity and had no effect (see traps below).
- Files tab table stacks into cards on mobile (`display: block` cascade + `data-label` via
  `content: attr()`); `files.js` `paintList()` now emits `data-label` on four `<td>` cells — the
  one JS change needed for a layout decision this pass.
- Globe never opens a WebGL context below 700px: `window.matchMedia("(max-width: 700px)")`
  gates `LinGlobe.mount()` in `buildGeoStage()`, before the call, not just the canvas's CSS.
  This was a **real, previously unguarded gap** — the brief's premise that Globe already
  degraded to a static image on mobile did not hold; Map and the flat atlas already did, Globe
  did not.
- Icon dock vs. assistant launcher: 156px^2 real overlap at 390x844, fixed by raising the
  launcher's mobile `bottom` from 16px to 88px.
- Icon dock vs. last list row: 101.5625px^2 real overlap (nothing reserved space below the
  scrollable list for the fixed dock), fixed with `#project-list { padding-bottom: 88px }` on
  mobile only.
- Upload, administration, and the decision sequence are explicitly out of scope on a phone now:
  CSS-only, children `display: none`, panel itself stays so its own `::before`/`::after` can
  show "This needs a desktop browser."
- The light theme's user-facing label: "Plain" to "Fairbanks" (`THEME_META` in `app.js` only).
  The internal key stays `"plain"` — `THEMES` in `server/app/theme.py`, the stored preference
  value, `body[data-theme="plain"]` in `radar.css`, and `test_theme_plain.py`'s filename are all
  unchanged on purpose. Renaming those is a schema/vocabulary change with its own migration, not
  a display-string change, and was explicitly out of scope for this pass.

## A trap worth repeating from the theme session, because it bit fault injection here too

**A fault-injection needle must actually reproduce the defect's shape.** The first attempt at
reverting the dock/launcher fix used a simplified 1-button dock fixture for speed and measured
0px^2 overlap even WITH the fault present — a false clean, because the simplified dock was
narrower than the real 3-button dock and never reached the launcher regardless of its `bottom`
offset. Rebuilding the fixture with the real `dock-nav-btn` count (3, matching `DOCK_NAV` in
`app.js`) reproduced the actual 135px^2-class overlap. If a revert check comes back clean, check
whether the fixture is faithful before trusting the number.

**The browser HTTP cache trap from the theme session is still live and still costs time.**
`fetch(url, {cache: 'no-store'})` before every measurement, every time the stylesheet changes,
not just once at the start of a session.

# 2026-08-02 — A SECOND THEME: PLAIN. WHITE, HIGH CONTRAST, AND FIXED FOR RESEARCH ACCOUNTS

Full detail in `REPORT_2026-08-02_light-theme.md`. **Server 1634/1634 across 30 suites,
`tests_render.html` 62/62, `tests.html` 51/51.** Nine faults injected, all detected, all reverted
byte for byte.

## TWO TRAPS THAT WILL COST THE NEXT SESSION TIME IF IT DOES NOT KNOW THEM

**A CSS transition freezes the computed value in this container.** `body` has
`transition: background .35s, color .35s`. With the document timeline frozen at 0, both
`CSSTransition` objects sit at `currentTime: 0` and never advance, so `getComputedStyle(body)`
returns the PREVIOUS theme's colours indefinitely. My first surface read said `rgb(10,14,18)` on a
white theme and looked like a plain failure; with `transition: none` the same element snaps to
`rgb(245,246,248)`. **Suppress transitions before reading any computed style here**, or you will
report a false failure. A probe element with `background: var(--page-bg)` is the quick cross-check:
it has no transition and resolves correctly.

**A REVERT needle must be as unique as the injection needle.** The globe fault reverted on
`#0e3049`, which already existed in the Miami and Maria blocks: three matches, harness aborted,
fault left applied. Use a marker value that exists nowhere else. Also, again: a needle written
with `\n` matches nothing in these CRLF files.

## What was added

- **`body[data-theme="plain"]`**, a fourth theme. Variable set only, no component rewritten.
  White surfaces, neutral greys, one blue accent `#0b6bcb`. `applyTheme()` adds `t-light` for it,
  which is why several existing `body.t-light` overrides corrected themselves for free.
- **Contrast is MEASURED, not asserted.** `tools/test_theme_plain.py` reads the hex values out of
  `radar.css` and computes the ratios, so a comment cannot make it pass. Worst text is `--phosphor`
  at 5.28 on white and 4.88 on the page; everything else is 5.7 or better.
- **`participants.theme`** (migration 0017), nullable. NULL means "has not chosen" and resolves to
  `newyork`, which is what keeps every existing account's appearance unchanged.

## THE RESEARCH GATE IS IN THREE PLACES AND THAT IS DELIBERATE

`themeset` in `RESEARCH_FORBIDDEN_ACTIONS` (pre-dispatch, audited); `a_themeset` refuses again;
and `resolve_theme` IGNORES the stored column entirely for a research account. `themeget` is
deliberately NOT gated. The fixed theme is `newyork`, the existing default, not the new one: the
study's stimulus must not move because a theme was added for operational users.

**A check that could not fail, found by injection.** Removing `themeset` from the gate left the
suite GREEN, because the handler caught it. Defence in depth working, and a check blind to half
its own claim. Two checks were added: the gate asserted structurally, and `a_themeset` called
DIRECTLY to reach the inner layer with the gate bypassed.

**The gate's refusal is now per action.** It used to write `project_creation_denied` and a sentence
about projects for anything in the set, which would have been a false audit record for a theme.

## Other things in this change

- **The caption above Radar, Map and Globe is gone, with no replacement.** It described radar
  geometry (meaningless on the other two) and promised a governance decision with authority,
  documentation and a contractor fairness gate. The decision card was dead code on retired category
  ids and the fairness gate was removed because it read a field nothing writes.
- **The globe sea on this theme is `#a9c6da`**, using the ABSTRACT treatment. The photographic
  treatment multiplies `material.color` into the texture, so the other light themes' `#0e3049`
  darkens the Blue Marble further, which is the hole in the page. Land 3.56, graticule 3.58, worst
  marker 3.46. **Nothing outside this theme's block was touched, so the dark themes are unchanged
  by construction.** Miami still has the near-black sea; changing it is Lin's call.
- **The logo sweep needs NO light variant, and that is measured.** 576 samples under the sweep's
  own radius: zero transparent, mean `rgb(81,84,99)`, luminance 0.09. It lies entirely on the
  wheel's own dark face, which is a raster and does not vary by theme.
- **All four dock icons animate now.** All four always had a rule declared and running; two moved
  almost nothing. `dock-book-breathe` was `rotateY(-13deg)` with NO PERSPECTIVE, which is not a
  hinge but `scaleX(cos 13°)`: the whole animation was **0.308 px**, measured (matrix
  `a=0.9744`). With `perspective(70px)` and 26 degrees it travels 1.891 px. The menu emblem's 3.3px
  blip moved 0.36 of alpha and now uses `dock-amb-pulse` (0.38 to 1.0 plus a slight scale).
  Transform and opacity only, so theme independent, and both were already inside the existing
  reduced-motion block.

## Open

- About 40 hardcoded shadows and scrims remain (`rgba(0,0,0,.35)` and friends). Legible on this
  theme, heavier than it wants. Inventory is in the report so the next pass need not re-derive it.
- `.theme-switch` is dead code; the switcher has been the dock fly-out for some time.
- Project detail, administration, the Files tab, the assistant and the knowledge pages were NOT
  verified by computed style: their panels are built by JS and need auth and data. They read the
  same tokens, but that is not the same as having checked.

# 2026-08-02 — THE FILES TAB: THE ARORA DIRECTORY, AUTOMATIC FILING, AND THE TWO FILED STATES

Full detail in `REPORT_2026-08-02_files-tab.md` — **read its first section**, which is how the
tree is handled per project. **Server 1571/1571 across 28 suites, `tests_render.html` 62/62
(was 49), `tests.html` 51/51.** Eleven faults injected, all detected, all reverted
byte-identical, baseline re-run after each; the new render group separately fault-proven. The
tab was driven in a real browser and confirmed by DOM read.

## NO FOLDER IS EVER CREATED, AND THERE IS NO `folders` TABLE. This is the decision.

The Arora template is CODE (`server/app/jdrive_tree.py`), transcribed verbatim from
`JDrive_Project_Directory_Structure_NEW_v202604.pdf` by column position. A project's real tree
is **the template plus the distinct `document_uploads.folder_path` values for that project**.

That answers all three of the source document's pruning instructions without any pruning:
disciplines outside Arora's scope are never created so never deleted; the CAD-versus-REVIT
choice resolves itself because whichever folder receives a file is the one that appears (filed
by file EXTENSION); and the room-by-room photo folders come into being when something is filed
into them. `occupied` on every node drives "only folders in use" versus the full template.

- **Folder names are VERBATIM including the template's own inconsistencies**: `C. PHOTOS` has a
  period where every other lettered folder has an underscore, `YYYY_MM_DD XX% INFO` uses
  underscores in the date, `1_ACTIVE CONSTR. SET` has an abbreviating period. Do not tidy them.
- **THE BRIEF'S DESCRIPTION OF THE TOP LEVEL WAS WRONG** and this is why the brief said not to
  reconstruct the tree from it. `1_RFP` is a SUB folder of `0_PROJ-MGMNT`. The real top level is
  `0_PROJ-MGMNT`, `1_PROJ INFO`, `2_DELIVERABLES`, `3_DESIGN`, `4_QC`, `5_CONST ADMIN`,
  `6_RECEIVED`, `NEWFORMA`.
- **Placeholders are PATTERNS, not folders** (`YYYY-MM-DD`, `CLAIM #`, `CREDIT NAME`). Shown
  greyed, not selectable, refused as a move destination, instantiated into real names at filing.
- **The two identifier branches have DIFFERENT shapes and must never be merged**: claims are
  `8_CLAIMS/CLAIM 014/2026-06-10` (identifier ABOVE date, two levels); field visits are
  `7_FIELD-SITE VISITS/2026-06-12 SITE OBS 3` (identifier INSIDE the dated name, one level). A
  check asserts their path depths differ.

## THE CONFIDENCE WAS BEING THROWN AWAY. The brief's premise was half true.

`classify()` has always asked the model for `{"docType", "confidence"}`, parsed it, and
returned only the type. **No confidence had ever reached the platform.** It is now kept, and
the existing rule is preserved exactly: confidence is returned ONLY when the model's own claim
decided the type. A filename fallback or UNMAPPED carries `None`, which is the
"rejected classification" case the old docstring already refused to inherit from. **`None` is
treated as REVIEWABLE, never as fine.**

**Threshold 0.70, and it is NOT calibrated** — it is the legacy Apps Script's own default
(`parsed.confidence != null ? parsed.confidence : 0.7`), the only number the instrument ever
committed to. `CONFIDENCE_THRESHOLD` is the single place to change it.

Low-confidence documents go to `6_RECEIVED/<date>_INFO` (a REAL template folder, not an
invented `_UNFILED`) and are flagged `needs_filing_review`. **The flag is what makes it
reviewable, not the folder**: it sits in its real folder with a "Check filing" mark and a count
badge. Moving resolves the flag and is audited.

## Four columns, NO new table (migration 0016)

`document_uploads.folder_path` / `.filing_class` / `.needs_filing_review` (statements about a
project's copy, same argument 0013 made for `supersedes_document_id`), and
`documents.classification_confidence` (qualifies the classification, which is of the bytes).

## The three filing classes, and why a filed document is not a failed extraction

`analysed` / `reference` / `filed`. Before this, ANYTHING not a mapped type carried
"contributes nothing to the analysis", so a Revit model, a LEED credit and a specification all
read as a fault. Most of the Arora tree is documents stored and never analysed; that is the
expected outcome.

**The `_corpus` separation is preserved WITHOUT a `_corpus` folder.** Specifications go to
`4_QC/<dated>/D_SPECIFICATIONS` and codes/standards/requirements to
`3_DESIGN/2_CODE & STANDARDS/B_CODE - CLIENT STANDARDS` — the template's own folders, named for
exactly these documents. The separation is carried by the CLASS, and holds two ways: a reference
document is not a mapped type so the merge skips it (a check assembles one alone and asserts the
result equals the empty signal inputs), and it is classed `reference` so it does not read as
failed. **Reference detection is deliberately SEPARATE from the analytical classifier** and is
filename-based: adding a "specification" type to `DOC_TYPES` would put specs inside the
vocabulary the classifier chooses from, which is the one thing this must prevent.

**`projectcorpus` is gated by the EXISTING `auditor` flag** in `features.GATED_ACTIONS`, no
third scheme, refused before dispatch, for anonymous callers too. **FILING IS NOT GATED**: with
the reviewer off a specification is still filed, still classed reference, still out of the
analytical path. Asserted directly.

## Things worth knowing before touching this again

- **The template and the analytical vocabulary overlap only PARTLY.** Eleven types have a folder
  named for them in the source; **fifteen do not** (RFI log, submittal register, safety report,
  NCR log and so on) and file to `6_RECEIVED`, whose own description is the template's answer
  for a document arriving without a designated home. One table, one comment per entry.
- **The template wants a claim number and a site-observation number that `extraction_fields.py`
  never asks for.** Read off the filename when present, omitted when not; never invented.
- **`document_as_of` is now public in `extraction_merge`** so filing and observation emission
  cannot disagree about a document's date. A folder is named for the DOCUMENT's date, never the
  upload clock; a document with no readable date gets `UNDATED`, not `1970-01-01` and not today.
- **My render group THREW and that read as a clean run** — the results table never rendered, so
  the runner saw zero checks rather than a failure. It is now wrapped so a throw is a red check.
  The real cause was `files.js` calling `LinAuth.getToken` without checking the method exists;
  fixed there too, since a preview that cannot build a URL must not take the page down.
- **One injection anchor did not match and the harness refused to report a result**, rather than
  showing a false clean. Keep that property.

# 2026-08-02 — THE EXPORT PRODUCES TWO THINGS: PARTICIPANT INPUTS AND PROJECT HEALTH, AS AN XLSX WORKBOOK

Full detail in `REPORT_2026-08-02_export.md` — **read that report's Part 2 first**, it is the
field inventory Lin asked to strike against the analysis plan. **Server 1517/1517 across 28
suites, `tests_render.html` 49/49, `tests.html` 51/51.** Seven faults injected, all detected,
all reverted byte-identical, baseline re-run after every fault. Both admin controls driven end
to end in a real browser and confirmed by DOM read; the produced workbook was opened with
openpyxl and read back, not only asserted against the code that wrote it.

## The two kinds, and why the banner and notice both had to become conditional

`participant_inputs` is the original export, unchanged in name/behaviour/defaults
(`build_rows`, `EXPORT_COLUMNS`, `serialise` all keep their signatures — `test_export.py`'s 77
checks pass completely unmodified). `project_health` is new: per project, reads
`computed_results` directly, windows on `computed_at` (a decision timestamp does not exist in
this scope; a reporting period is an integer a date range cannot bound), and is **NOT**
filtered to research accounts — a project carries no `account_type` of its own. Both facts are
now stated in every response (`research_account_filtered`, `date_window_field`) and both the
banner and the "From"/"To" labels switch live in the UI when the kind changes.

**The Notice text follows the same reasoning**: `participant_inputs` carries the research
variant (true — everything in it is synthetic research-account data);
`project_health` carries the **operational** variant (the one that makes no "all synthetic"
claim), because that scope can genuinely include real operational project data. Both quoted
whole from `DISCLAIMERS_DRAFT.md`, nothing composed. This flipped one pre-existing check in
`test_disclaimers.py` that had asserted `research_export.py` must NEVER carry the operational
variant — the premise (only one scope existed) no longer holds, and the check's reasoning was
rewritten in place, not just its assertion.

## The workbook

`participant_inputs`: **Notice, Decisions, Stimulus, Module results, analysis_long.**
`project_health`: **Notice, Module results** only — no participant sheets, since there is no
participant dimension in that scope. Sheets always named explicitly.

- **Decisions** (44 cols, was 39): the original allowlist plus `instance_id` (the join key —
  `decision_id`) and four judgement-only fields (Part 5): `time_on_instance_seconds`,
  `pre_committed_before_disclosure`, `completion_state`, `session_break` (a STATED HEURISTIC —
  a login event strictly between instance start and end; `None`, not `False`, before the
  instance has an end, so "no break" and "not yet judgeable" don't collapse into each other).
- **Stimulus**: one row per instance, the frozen `DecisionSupportPackage` as disclosed —
  `detected_condition`, `alternatives`, `uncertainty`, `limitations`, `applicability_boundary`,
  `expiration_trigger`, `provenance`, `recommended_action`, exactly what `decision-ui.js`
  renders on reveal. Nothing here is analytically produced.
- **Module results**: one row per project/period/computation, named by `computation` (module
  name) and `group` (group name) — **never a module id or number**, per
  `NAMING_AUTHORITY.md`. Scoped to the touched projects for `participant_inputs`, to everything
  in the date window for `project_health`.
- **analysis_long**: Part 4, exactly TWO rows per instance always (`post_ai` 0/1), including an
  instance whose final decision does not exist yet — verified directly with an abandoned
  mid-instance fixture; omitting that second row would have been exactly the silent filtering
  Part 5 forbids. `expert_reference_score` is a reserved, always-empty column — the rubric score
  does not exist anywhere in the schema yet (confirmed, not assumed: `expert_references` has no
  numeric score column at all).

## Established, not assumed — read before touching this again

- **openpyxl is NOT byte-deterministic by default.** Two builds of identical data a second
  apart differ: `docProps/core.xml`'s created/modified timestamps AND every zip entry's own
  timestamp both stamp the wall clock. Setting `workbook.properties.created/modified` alone
  fixes only the first. `_normalize_xlsx_bytes` rewrites the whole archive with fixed per-entry
  timestamps and textually-pinned docProps, entries reordered by name. Proven fixed by building
  twice a second apart and diffing bytes — do that again if this code is ever touched.
- **A participant who consented but decided nothing produces ZERO rows, not a placeholder.** An
  instance is anchored on a `Decision` row, which is created only at the preliminary-judgment
  INSERT. This is not a bug to fix; a participant who never opened the evidence has nothing yet
  to report.
- **The checksum-legacy path now covers xlsx too**: `include_notice=False` drops the Notice
  sheet from the workbook the same way it drops the notice keys from JSON, reproducing the
  pre-notice sheet set for the second-chance comparison in `a_adminexportfetch`.
- **No migration-as-backfill**: `research_exports.kind` is NOT NULL with a server default of
  `participant_inputs` — correct for every row that existed before the column, because that was
  the only kind that could have produced it.

## Still open, referred to Lin (Part 2's "available" list)

Person-level fields collected at intake (`experience_level`, `industry`, `certifications`,
`organizational_role`, `risk_attitude`, raw `intake_responses`/`debrief_responses`) are stored
but not exported anywhere yet. `Assignment.status` and most of `ComputedResult`'s own top-level
fields (`signal_inputs`, `category_statuses`, `project_status`, `portfolio_snapshot`,
`source_documents`) are stored and unexported. **Scenario-domain familiarity per participant
per project is not stored anywhere at all** — no questionnaire item, no column — confirmed by
reading both `intake.json` and `debrief.json` in full. Adding any of these is a column-list
edit once told which ones the analysis plan needs.
# 2026-08-02 — THE LOGO'S RADAR SWEEP TURNS (DECLARED, NOT OBSERVED)

Full detail in `REPORT_2026-08-02_logo-sweep.md`. **Server 1517/1517 across 28 suites,
`tests_render.html` 49/49, `tests.html` 51/51.** CSS only, no library, `logo.png` untouched.

## COMPOSITING IS STILL UNAVAILABLE. The animation is declared, not seen.

Measured before claiming anything, and the numbers are worth keeping because the next session will
want them: **0 requestAnimationFrame frames in 1515 ms**, `document.visibilityState` is `"hidden"`,
and `document.timeline.currentTime` reads **0 across four samples over 2.1 seconds**. The animation
exists and reports `playState: "running"`, but the timeline never advances so no frame is drawn.
A screenshot returns "the Browser pane is not displayed, so the page is not compositing frames."
**A frame counter is the right check here**: it reads zero when nothing is painted, and unlike a
pixel test it cannot be satisfied by a page flattened to black.

## Where the logo appears: SIX places, not two

`index.html` lines 40 (favicon), 280 (sign-in), 360 (access-denied), 383 (consent), 422 (top bar),
and `assets/js/app.js:2347` (dock emblem). Five now carry the sweep.

- **The favicon cannot be animated** and was left alone. It is browser tab chrome; the only way
  would be swapping `href` on a timer, which is an animation library by another name.
- **There is no separate loading screen.** The four `auth.js` screens are all hidden until auth
  resolves, so the first thing an unauthenticated visitor sees is the sign-in panel. The map's
  loader uses `LinWorkingRobot`, not the logo.
- **The dock already had its own sweep** (`.dock-emblem-sweep`, a `--phosphor` quadrant turning over
  the whole button including the gold rim). Replaced by the shared `.logo-sweep`.

## A ROTATING QUADRANT DOES NOT WORK. Do not try it again.

The artwork already carries a bright quarter of the radar face, twelve o'clock to three o'clock.
Rotating a second quadrant above it puts two equally large bright blocks in different places at
every angle but the start: two sweeps on one instrument. Built it, rendered it at 96 px, confirmed
it, discarded it. Masking or patching the drawn quadrant was rejected because the face under it
carries range arcs and coloured returns the rest of the face does not have, so covering it means
repainting the artwork.

**What reconciles is a narrow leading edge with a short tail**, which does not compete with the
drawn quadrant because it is not the same kind of shape: the line reads as the sweep, the quadrant
reads as the sector it lit.

## Numbers that matter if you touch this

- `logo.png` is 1531 by 1413; **the wheel centre is 765,705, which is the image centre to within a
  pixel**, so the sweep centres with `inset: 0; margin: auto`. The radar face radius is 400 image
  pixels = **56.6% of image height**. That is the one magic number, and it is why the sweep stops
  before the gold rim.
- The three panel logos are 56 by 56 with **no `object-fit`**, so the image is squashed and the face
  is a slight ellipse; they get 54.4% instead. The dock is `object-fit: cover` into a square, so
  56.6% is right there.
- **The bright core is ten degrees wide and must stay wide.** The first version used half a degree,
  which at the dock's eleven pixel radius is a tenth of a pixel: it anti-aliased away entirely and
  the logo looked static. Check any change at 40 px, not at 96.
- Reduced motion stops it at the three o'clock radius, which is where the artwork's own bright edge
  is drawn, so the frozen state is the logo as illustrated.

## An injection that silently failed to apply, again

The no-layout-shift check would not go red under `position: static !important`. That looked like a
weak check; it was a weak **fault**. The overlay is a `<span>`, so as a static *inline* box width
and height do not apply and it collapsed to zero, shifting nothing. The fault needs
`display: block` too; the panel then grows by exactly the 40 px injected. **Assert the fault
changed something before believing the check survived it.**

# 2026-08-02 — RUN 2: PORTFOLIO HEALTH APPENDS, OVERWRITESIGNAL VALIDATES ITS FIELD NAME, USER ARCHIVE AND DELETE BUILT

Full detail in `REPORT_2026-08-02_facade-and-user-lifecycle.md`. **Server 1469/1469 across 27
suites, `tests_render.html` 49/49, `tests.html` 51/51.** Sixteen faults injected across two
campaigns, all detected, all reverted byte-identical, baseline re-run after every fault. Both
admin controls also driven end to end in a real browser, confirmed by DOM read.

## What delete reaches, the lead of the report

Six tables are current relational state and are cleared EXPLICITLY in code, not left to the
database: `participant_profiles`, `consents`, `assignments`, `decisions`, `transitions`,
`project_members`. **SQLite — used for every local check in this run — does not enforce `ON
DELETE CASCADE` without `PRAGMA foreign_keys=ON`, which this app does not set.** Relying on the
declared FK cascade alone would have looked correct in Postgres and silently orphaned rows in
every local verification. Four text columns (`audit_events.participant_id`,
`document_uploads.uploaded_by`, `documents.first_uploaded_by`, `research_exports.initiated_by`,
plus `added_by`/`revoked_by` on OTHER people's membership rows) are NOT foreign keys and are
left exactly as they are, by the same design `AuditEvent`'s own docstring states: they must
survive the deletion of whatever they describe.

**Deleting a research participant destroys their decision records — `assignments` cascades to
`decisions` and `transitions`.** Reported, not softened: that is why archive exists as an
independent, non-destructive control rather than delete having a "keep the research data" mode.

## Part 1: the one `session.delete` in the app is gone

`w_saveportfoliohealth` appends now. **Nothing depended on there being exactly one row** —
`a_getportfoliohealth` already SELECTS the latest rather than reading a singleton, verified
before changing anything. **Fixing this surfaced a real ordering bug**: the DB's `saved_at`
column is second-resolution on SQLite, so two saves in the same second tied, and `ORDER BY ...
DESC` over a tie is not guaranteed stable — invisible while deletion removed the old row first,
immediately visible once both rows persist. Both read and write-side verification now order by
the snapshot's own `savedAt` string (millisecond resolution) instead of the column.

## Part 2: overwritesignal's field name is now checked

Restricted to `field_registry.ALL_SI_FIELDS` — verified by set equality to match
`extraction_merge.SIGNAL_INPUT_KEYS` plus `cpi`/`spi` exactly, so the vocabulary cannot drift
from what the merge can actually produce. An unknown name is refused, named, before the project
is even looked up.

## Part 3: archive already existed; delete is new

**Archive needed no backend change.** `setactive(is_active=false)` already matches the
definition exactly (cannot sign in, everything retained) — `resolve_caller` refuses an inactive
account everywhere, and archiving never touches membership, consent, or anything else. Only the
UI changed: relabelled "Archive"/"Restore" (was "Deactivate"/"Activate") to match the vocabulary
the platform already uses for the same concept on projects. **Confirmed, not assumed: an
archived user still appears in `adminmemberlist`** — that handler never filters on `is_active`.

**Delete is `admindeleteparticipant`**, admin-only, no other condition (explicit instruction —
`setactive`'s last-admin guard is deliberately NOT mirrored here). Reports exactly what it
removed; writes `participant_deleted` to `audit_events` for the now-gone id.

## Things worth knowing before the next session

- **`add_repo`-style DB cascade assumptions are unsafe in this codebase's SQLite test path.**
  Any future feature relying on `ON DELETE CASCADE` needs the same explicit-deletion treatment
  this task gave user deletion, or `PRAGMA foreign_keys=ON` needs to be added to `db.py` first
  (not done here — out of scope, and would need its own verification pass across every existing
  cascade).
- **The delete confirmation UI requires typing the exact username** before the submit button
  enables — friction deliberately placed on an irreversible action.
- Whether `getportfoliohealth` should be membership-scoped is still open, unrelated to this run.

# 2026-08-02 — D2 CLOSED: MALFORMED NUMERICS REFUSE AT ALL FOUR ENTRY POINTS

Full detail in `REPORT_2026-08-02_malformed-numerics.md`. **Server 1440/1440 across 26 suites,
`tests_render.html` 49/49, `tests.html` 51/51.** Eight faults injected, all confirmed applied,
all detected, all reverted byte-identical, baseline re-run after every fault. Three faults
crashed the suite mid-run and STILL read as red, because the suite wraps its whole run.

- **Four entry points, enumerated not assumed, all guarded**: (1) `extract_many` — refuses the
  whole document BEFORE any row, per document not per batch; (2) `emit_observations` — the
  stored-row backstop, validates before emitting so refusal is all-or-nothing; (3)
  `overwritesignal`; (4) **`save`** — the wholesale doc replacement carrying a client
  signalInputs blob, the live action nobody had listed (the risk guard never covered it
  either). `save` validates CHANGED fields only, so a legacy-stored bad value cannot brick
  every later edit.
- **Three cases**: absent passes (abstention unchanged); malformed ("TBD", "N/A", booleans,
  "1.2.3") refuses; out of contract (negative count/sum) refuses. Range contract in
  `field_registry`: everything numeric non-negative EXCEPT totalFloat/consumedFloat/
  floatRemaining/analogousOverrunPct (signed set — negative float is a real state). NO percent
  upper bounds: the 0..1-vs-0..100 scale question is unresolved and was not guessed at.
- **The parser accepts real-world decoration**: "$1,200,000", "1,200", "45%", and "(500)"
  reads as NEGATIVE 500 — the legacy stripper made it +500 and made "TBD" a 0.0. Emission now
  coerces through the SAME parser, so the guard and selection can never disagree about a value.
  `_num_or_null`'s malformed-to-zero quirk is dead at every guarded boundary.
- **The uploader sees the existing extraction-failure dialog**, per-file error verbatim, field
  and file and value named, "Nothing was stored", remedy stated. New strings are operational
  error wording only and are flagged in the report.
- `docRiskScore` keeps `validate_doc_risk_score` as its range authority; "N/A" for it is now
  refused as malformed BEFORE the range guard ever sees the coerced 0.0.

# 2026-08-02 — THE STORAGE REDESIGN IS BUILT: OBSERVATIONS, SELECTION, FOUR DEFECTS CLOSED

Full detail in `REPORT_2026-08-02_storage-redesign.md`. **Server 1394/1394 across 25 suites
(up from 1361/24), `tests_render.html` 49/49, `tests.html` 51/51, green on merged `main`.**
Nine faults injected, all detected with distinct signatures, all reverted byte-identical,
baseline re-run after every single fault. `server/app/simulation/` untouched.

**Part F of the reconciliation report is implemented.** Migration **0014** adds `observations`
(append-only, one row per project/period/document/field/entity, `as_of` from the document's own
date or NULL — never the clock, `revision_of` promoted from `supersedes_document_id`).
`signalInputs` is now the OUTPUT of `select_signal_inputs(observations, cutoff)` — same keys,
same order, same quirks, so the 100 computations receive exactly what they always did.
`field_registry.py` owns per-FIELD kinds (SNAPSHOT/EVENT/DELTA/PERMANENT), writer precedence
tiers, and need declarations. Run 0014 on production BEFORE the first upload, with 0013.

## The four defects

- **Baseline preservation CLOSED**: `baselineContractSum` is the contract's own sum, PERMANENT;
  a CO wins `bac` by declared tier as an executed amendment; the `baselineEnd` direct dict
  write is gone; `projectuploadstatus` returns a `baseline` block (original + amendments).
- **docDate CLOSED**: derived as the latest `as_of`, same rule as the cutoff — one answer.
  Always ISO now; `historical_data`'s bare "2019" no longer leaks into it.
- **P1 CLOSED**: portfolio vectors selected by `period_cutoff <= cutoff`, never `max(period)`.
  Byte-identical recompute of period 1 after another project reaches period 2, fault-proven.
- **Registers only CLOSED**: individual `rfi` routes to UNMAPPED (stored, `contributes:false`,
  never asked for totals). The `add()` accumulators are gone; **`"rfi" < "rfi_log"` is gone BY
  CONSTRUCTION and verified**: a check asserts `rfiCount` has exactly one writer.

## Facts the next session needs

- **Selection rules**: SNAPSHOT = lowest tier, then latest `as_of`; dated beats undated; wholly
  undated ties fall back to the historical (rank, doc_type, sha256) LAST-write order — including
  legacy first-non-null fields, a small documented divergence. PERMANENT = earliest, nothing
  later replaces it. EVENT = latest per entity, then aggregate; stated total beats counting;
  counted ledgers write NO `sources` entry (models_dq weighting parity).
- **`rfiNumber` / `rfiResponseTimeDays` are permanently None** (only the individual form wrote
  them); recorded in `field_registry.UNEMITTABLE_FIELDS`. A4.2's rfiNumber fallback abstains.
- **On adminrecompute the reused cutoff now BOUNDS selection**: later-dated documents added to
  the period after the fact no longer change the recomputed figures. Intended.
- **`test_document_versioning` section 1 flipped meaning**: it used to reproduce the old
  defects, it now asserts them dead, and its fixture pair orders the ORIGINAL's hash HIGHER
  (equal-date tiebreak) so supersession is still provably what flips the outcome.
- **D2 IS STILL OPEN AND NOW MORE VISIBLE**: coerced 0.0s persist as authoritative-looking
  observation rows. The reconciliation report said fix D2 before the store; it was not in this
  task's scope and changes validated instrument behaviour. It should be the next fix. D3
  (wall-clock cutoff fallback) also unchanged; undated observations pass the cutoff filter.
- **Layer 3's registry enforcement was NOT built** — it lives inside `simulation/`, which is
  out of scope. Declarations exist in `field_registry.NEEDS` (`milestoneHistory` declared
  unservable). Opening `simulation/` for enforcement is Lin's decision.
- One of my own checks was vacuous (compared an expression to itself) and was rewritten before
  it could lie — the P1 byte-identical comparison is the check that fault F1 turns red.

# 2026-08-02 — FIVE CHECKS THAT CANNOT FAIL: TWO FIXED, TWO CONFIRMED, ONE ALREADY DONE

Full detail in `REPORT_2026-08-02_vacuity-fixes.md`. Test files only, no application code touched.
**Server 1361/1361 before and after** (no checks added or removed).

- **`test_workspace_t3t5.py:229`** was `check(True, ...)` — `redacted_any` was computed and printed
  but never tested. Now `check(redacted_any, ...)`. Ground truth was `True` on the real fixture
  before the fix landed, so this was not silently hiding a live defect.
- **`test_features.py:158`** was `audit_rows("features_set", changed_by=None) == [] or any(...)`.
  `changed_by` is never `None` in a real audit row, so the left disjunct is always `[] == []` and
  the right side, the only part reading real content, never runs. Now filters by the real
  `changed_by=admin_id` and asserts `applied`/`previous`/`now_stored` match. **A second defect was
  found fixing the first**: filtering by `participant_id` cannot work at all, because `audit()`
  stores it as a dedicated `AuditEvent` column, never inside `event_metadata`, and `audit_rows()`
  only reads metadata. Worth knowing for any future audit-content check in this suite.
- **Three `all()`-over-possibly-empty checks in `test_d1_module_inputs.py`** — already fixed, in
  the same D1 session that found them, before commit `c05d028`. All three carry a `>= 3` or `> 0`
  guard today. No edit made.

Both fixes proven able to fail by injecting a fault into the TEST FILE's own local computation
(app code was off limits for this task) — renaming the key `redacted_any` reads, and pointing the
audit filter at a wrong id. Both went red, both reverted byte-identical, checked after each fault
individually, not once at the end.

# 2026-08-02 — DOCUMENT TABLE RECONCILIATION (RUN 1), AND THE FAIRNESS GATE REMOVED

Full detail in `REPORT_2026-08-02_document-reconciliation.md`. **Server 1361/1361 across 24 suites,
`tests_render.html` 49/49, `tests.html` 51/51, green on merged `main`.** 15 faults injected for the
Part 4 checks, all detected, all reverted and rechecked byte-for-byte.

**THE STORAGE REDESIGN IS NOT IMPLEMENTED.** This session reconciled, reported, and made the four
small changes. The design is Part F of the report and Lin reads it before anything is built.

## The three rules Lin suspected were absent. All three CONFIRMED absent.

- **Change order state gating.** Worse than suspected: `extraction_fields.py` never asks for a
  state at all, so there is nothing to gate on. A draft and an executed CO are the same document.
- **Contract Value baseline preservation.** `change_order` is rank 2 and `contract_value` rank 0,
  so the CO folds last and overwrites `bac`. `baselineEnd` is worse: a direct dict write that
  bypasses `set_field`. The original baseline is destroyed and has nowhere to live.
- **Field report atomic vs period-to-date.** No cumulative-versus-atomic flag exists on any field
  of any type. `weatherDaysLost` is the ambiguous one and the pipeline cannot tell which it is.

## Facts worth carrying, verified against the code not the audits

- **BOTH PREREQUISITE AUDITS ARE STALE.** The evidence-policy audit is not on `main` at all: it is
  on `t15-local-unpushed`, dated 2026-08-01, and its headline CUSUM finding is fixed. The pipeline
  audit says no evidence-policy report existed, which was true when written. Verify against code.
- **`_period_history` now supplies real cpi/spi series** from earlier periods' live
  `ComputedResult` rows, `period < period`, minimum two points. Period-safe by construction. The
  brief's premise that there is no series concept is no longer quite true — for those two fields.
- **Only three non-replacing operations exist in the whole merge**: `add()` on `rfiCount` and
  `changeOrderCount`, and `keep_max()` on `rfiNumber`. Everything else is last-wins or
  first-non-null. The double-count surface is small and precisely located.
- **`"rfi" < "rfi_log"` is load-bearing.** It is the only thing stopping the individual-RFI sum
  from surviving alongside the log's absolute total. Rename either type and the double-count
  returns. Nothing records this.
- **`docDate` is one field written by 16 document types**, last-wins by sort order, so the as-of
  date is whichever type sorts last, not the latest date. `_derive_cutoff` uses a different and
  better rule (max parseable date). Two notions of "as of" that disagree.
- **The table and the code agree on all 28 document types exactly.** No additions, no omissions.
- **`_DOC_TYPE_RANK` is a code-only precedence concept** the table has no equivalent for:
  baseline 0 (contract_value, schedule_of_values, time_phased_schedule), revision 2 (change_order,
  schedule_update), everything else 1.

## What changed in code

- **The `fairnessSensitive` gate is gone** from `models_decision.py`. Proven unable to fire: not in
  `SIGNAL_INPUT_KEYS`, written by no merge branch. **The `fairnessGateRequired` key STAYS, always
  False**, because `app.js:1625/1669/1682` reads it to render a checkbox and gate submit, and this
  task could not touch the frontend. The browser's own `decision.js:228` gate is untouched.
- **`submittal` is now `submittal_register`**, with `LEGACY_TYPE_ALIASES` mapping the old string.
  The alias is not optional: stored `Document.doc_type` rows carry `submittal`, and dropping it
  would make every one silently stop contributing at the next recompute.
  **Individual submittals now classify as a register and will be asked for totals they lack**, so
  they will yield nulls or a guess. Routing them to `UNMAPPED` instead is Lin's decision.

## Things that cost this session time

- **A source-scan helper that was reading 24% of the file.** Hand-rolled comment/docstring
  stripping desynchronised and silently dropped 735 of `extraction_merge.py`'s 964 lines,
  including every merge branch. A fault injected into a branch left the suite green. **Use
  `tokenize` plus `ast`, never line-by-line triple-quote toggling.** Keep string literals: a merge
  branch names its field as a literal, which is what the scan is for.
- **A suite that died instead of failing.** A raising module killed the file at module scope and it
  printed no `RESULT:` line, reading exactly like a clean run. Wrap calls to the code under test.
- **CRLF.** A multi-line fault needle written with `\n` matches nothing in these files and reports
  "found 0". Use single-line anchors or explicit `\r\n`.
- **A revert needle that was not unique** left a fault applied in `extraction_fields.py`; the
  baseline re-check caught it. Deletion faults must replace with a unique marker, never `""`.

## Open, and Lin's to decide

- Individual submittals: register-with-nulls, or `UNMAPPED`.
- **D2 (malformed numerics becoming a confident `0.0`) should be fixed BEFORE an observation store
  is built**, not with it: otherwise a coerced zero becomes a durable, authoritative-looking row.
- P1 (portfolio vectors by `max(period)`) is closed by the design's cutoff-aligned selector, and
  the report states the rule. It needs a check that recomputes an earlier period after a later one.
- The evidence-policy audit should be landed on `main` or discarded.
- `UI_ONLY_DOC_TYPES` is still dead code.

# 2026-08-02 — FOUR NOTICE ITEMS, AND unported_modules CORRECTED

Full detail in `REPORT_2026-08-02_notices-and-unported.md`. **Server 1338/1338 across 23 suites,
`tests_render.html` 49/49, `tests.html` 51/51, green on merged `main`.** 21 faults injected, all
detected, all reverted and rechecked byte-for-byte.

## ONE THING IS NOT DONE AND IS LIN'S DECISION: the CSV export still carries no notice

The XLSX export and the JSON research export now carry the approved text. **The CSV cannot.**
RFC 4180 has no comment syntax, so anything above the header row IS the header row, and
`test_export.py` asserts `list(reader[0].keys()) == EXPORT_COLUMNS`. The alternatives all fail:
a `#` block silently breaks every existing reader, repeating 600 characters per row is not a
notice, and shortening it is composing a new liability variant, which a session may not do.

Three options are in the report. **Do not resolve this by writing shorter wording.** Every fetch
now returns `notice_in_payload` so the gap is visible at the point the file is taken.

## What changed

- **Access-denied panel**: its one-line notice is removed, not replaced. It was a third variant,
  switching on nothing, shown BEFORE authentication, telling a failed operational sign-in the
  platform is for academic research. The approved attribution sentence stays.
- **Exports**: XLSX gets a Notice sheet, FIRST so it is the sheet that opens. JSON gets `notice`,
  `attribution`, `copyright`. Text comes from the shared approved constant, never restated.
- **Meta description**: now the short-form standing description from `NAMING_AUTHORITY.md`,
  verbatim. It no longer asserts "public AEC capital programs".
- **Framework strings**: three chapter descriptions in `ds_defensibility_data.js` said the
  framework is grounded, built and evaluated, contradicting their own lead. Now "the research"
  and "the platform". The nine remaining uses of the word are external citations (Sargent's V&V)
  and are correct.
- **`unported_modules()`**: subtracts `PORTFOLIO_VALIDATED`. Answers `['A4.1']`, not six.

## Things worth knowing before the next session

- **`research_export.py` deliberately does NOT switch on account_type.** `build_rows()` filters to
  research accounts unconditionally, so an operational branch would be unreachable by construction
  and would assert an export that cannot exist. A check pins the exact guard statement; if that
  filter is ever relaxed, the notice is wrong and the suite says so.
- **Adding the notice changed the checksummed bytes.** Exports taken earlier would have been
  withheld as "the underlying data has changed", which would be a false accusation. Fetch now
  re-checks against the pre-notice serialisation and reports `predates_notice`. A genuinely wrong
  checksum is still refused; both directions are fault-proven.
- **`t15-local-unpushed` can be deleted.** It is 28 commits BEHIND origin, not ahead. Merging it
  would have deleted ~11,500 lines. Verified commit by commit: its PCEIF sweep and its CUSUM fix
  are both superseded by better versions already on origin, and `unported_modules()` was the only
  substantive thing missing. It is now landed, so nothing on that branch is needed.
- **Three of my own checks passed for the wrong reason and injection found all three.**
  `unported_modules()[0]` and `old_f["payload"]` both raised instead of failing, printing NO
  `RESULT:` line, which reads exactly like a clean run. And a check searching for
  `participant.account_type != "research"` matched the COMMENT I had just written quoting that
  expression, so deleting the real guard left it green. Match statements, not phrases.
- **Fault injection needs a restore check after EVERY fault, not at the end.** A deletion fault
  reverted with an empty needle, the harness aborted mid-revert, and `index.html` lost a paragraph.
  The next run's BASELINE came back 144/146 instead of 146/146, which is the only reason it was
  caught. Also: a multi-line needle written with `\n` matches nothing in a CRLF file.
- **The DB-backed suites are not idempotent.** Run twice against one database, the second run dies
  with no `RESULT:` line. Rebuild from `alembic upgrade head` before every run.
- **Two sessions shared this working directory today.** My byte comparison caught `app.js` moving
  underneath a running campaign, with another session's live `title="FAULT"` injection in it.
  Check `git status` for files you did not touch before staging anything.

## Still open, and referred to Lin

- The CSV export notice, above.
- Whether the word **Framework** belongs in the "Methods and Framework" tab label. Not obvious from
  the authority: the tab's `governanceAxis` content genuinely maps to external frameworks (NIST AI
  RMF, XAI principles). The ampersand-vs-"and" inconsistency WAS obvious and is fixed.
  "Methods and Standards" is the suggestion if it is to change; it touches four files.
- `ds_defensibility_data.js` still frames the RESEARCH as concerning "public AEC capital programs".
  That is a claim about the doctoral work, not the platform's scope, so it was left.

# 2026-08-02 — THE PROJECT LIST CARRIES ONE CONTROL TO THE DETAIL PAGE, NOT TWO

Full detail in `REPORT_2026-08-02_signals-open-merge.md`. **Server 1338/1338 across 23 suites,
`tests_render.html` 49/49 (up from 43/43), `tests.html` 51/51, all green after merging
`origin/main` at `757ee4b`.** No stored data altered, production not inspected, nothing under
`server/app/simulation/` touched.

**THEY REALLY WERE THE SAME CONTROL, and the premise was checked before anything was changed.**
Both handlers were the identical expression `openDetail(p.id)`, and **`openDetail` takes only an
id** — `showPage("detail")` with no section, tab, hash or scroll target, so the "opens the signal
ledger" reading was not something the code path could express. `li-signals` / `data-signals`
appeared in exactly three places repo-wide (the markup, the `stopPropagation` selector, the
handler): **no delegated listener, and `data-signals` was written and never read.** The CSS rule
bodies were byte-identical. The only real difference was the Signals tooltip, which **promised
behaviour that did not exist**.

**KEPT `Open →`.** "Open" names the action; "Signals" names an internal concept, and
`NAMING_AUTHORITY.md` section 5 already records that signal-computation framing on the client is
stale. The arrow is not an em dash and was left alone.

**THE LABEL SWEEP FOUND NOTHING TO UPDATE, and that is the finding, not a skipped step.** Every
`.js/.html/.css/.md` file was searched. The hits are the analytical vocabulary in `knowledge.js`,
the retired standalone **Signals page** prose (`signals.js:397`, `BACKEND_CHANGES_NEEDED.md:371`),
a `deepdive.js` metric box, and **`index.html:629`, the workspace tab strip's own `Signals` tab —
a different control on a different surface, deliberately NOT renamed here.** The assistant's
scripted guidance never named the button: `knowledge.js:88` says "use the project list", which was
correct before and stays correct.

**NOTHING COVERED THE ROW'S ACTION CLUSTER.** Group 4 called `buildFallbackList()` but asserted
only the status word's colour and class; both buttons could have been deleted or duplicated and it
stayed green. New group 4b asserts the counts AND the label sequence (`Manage|Open →`), because a
count-only check passes if someone re-adds a differently-classed control still labelled "Signals".
**Three faults, three DISTINCT signatures, restored to full green after each:** Signals button
restored 47/49 (checks 30, 33); merged control relabelled "Signals" 47/49 (checks 32, 33); Open
button duplicated 47/49 (checks 31, 33).

**A ZERO THAT WAS NOT A REGRESSION — read this before diagnosing an empty list.** The research
account first rendered **0 rows**, the exact shape of an over-refusing filter. It was not one:
`routeFromView` in `auth.js` sends a research participant **without consent** to the consent
screen, so `LinApp.init()` never runs and the portfolio is never loaded. After `consentgrant`, one
row. Both account types then read identically (0 Signals controls, 1 Open, `Manage|Open →`,
navigating to the right project with a populated detail root) — `buildFallbackList` has no
`account_type` branch.

**TWO ENVIRONMENT FACTS THAT COST TIME.**

- **This container has no `.venv`, no server dependencies and no Chromium**, unlike the ones
  earlier sessions describe. Build a throwaway venv in the scratchpad from
  `server/requirements.txt`.
- **`PYTHONIOENCODING=utf-8` IS REQUIRED to run the suites here.** `test_simulation.py` prints a
  `μ`, stdout defaults to cp1252, and the suite dies with `UnicodeEncodeError` printing **no
  `RESULT:` line at all** — the failure mode that skims like a clean run. With it set, 29/29.
- **`preview_start` was NOT pointed at `Demo`.** Its `{url}` form needs no `launch.json`, so the
  real FastAPI app was run on 127.0.0.1:8011 against a scratchpad sqlite and opened directly.
  **Nothing under `Demo` was modified.** The two browser suites, which the app does not serve, ran
  off a plain `http.server` on the repo root.

**ONE FAILURE SEEN ONCE, NOT REPRODUCED, AND IT IS NOT MINE.** The first full run had
`test_admin_ops_t7t8.py` at 56/59, all three reds in **Guarantee 7** (the tampered-export checksum
checks). It has returned 59/59, then 60/60 after the merge, in **twelve consecutive runs** across
both encodings against fresh databases. `server/app/research_export.py` is **uncommitted-modified
by a parallel session**; the likely explanation is reading that file mid-edit with the tampered
column momentarily outside the export's column set. **Flagged for whoever owns that change.**

**I TOUCHED ONE FILE ANOTHER SESSION OWNS: `assets/js/app.js`**, which held their uncommitted
`Methods & Framework` → `Methods and Framework` pill change at line 2285 plus a paired `index.html`
edit. **It was not swept into my commit**: only my own hunk was staged with `git apply --cached`.
The merge required their changes stashed; they were backed up first and `git stash pop` restored
them cleanly. **Verified after the merge: their change is present and still uncommitted.**

---

# 2026-08-02 — ADMINISTRATION CONSOLIDATED, A PM AT CREATION, AND THE UNMEMBERED GAP CLOSED

Full detail in `REPORT_2026-08-02_admin-and-membership.md`. **1268 server checks across 23
suites, 29 browser checks, `tests.html` 51/51, `tests_render.html` 43/43.** Ten faults injected,
**all ten produce the expected red**; three checks were rewritten because the injection showed
they proved nothing. Compositing proven
before anything was read off the page. **No overlap with the parallel geocoding session:
`geocode.py` and `documents.py` are untouched.** No stored data altered or deleted, production
not inspected.

**PRODUCTION STARTS FRESH. That is now a standing fact and it settles two open items.**

- **Migration 0013 is applied BEFORE the first upload, not as a repair.** It was carried as
  "written and verified, production not yet migrated, the supersede path will fail there until it
  is". On an empty database there is nothing to repair: it is part of bringing the schema up, and
  it stops being a risk to sequence against live data. Still Lin's to run, and it must be run
  before the first document is uploaded.
- **The coordinate backfill question is closed.** There are no stored projects to backfill. Every
  project from now on is geocoded at creation by the path the parallel session rebuilt.

**A PROJECT CAN NO LONGER EXIST WITHOUT A PM.** `projectcreate` takes `pm_participant_id` and
writes the membership row in the same transaction as the project, so a refusal leaves neither.
The legacy `create` on the facade writes the creator's PM row the same way. Naming someone else
as PM is admin-only and audited.

This fixed a silent defect: the old "Assign as PM (optional)" made **two** calls, and the second
was refused every time with "this project already has an active PM" because creation had already
made the caller PM. The project was created and the intended owner never got it.

**THE UNMEMBERED GAP IS CLOSED.** `guard_project_write`, `guard_project_read` and
`readable_project_ids` no longer wave through a project with no membership rows. That was the
last route from one authenticated user to another user's project. **Eight projects in the local
development database become inaccessible; all eight are fixture debris** (`PRJ-LEGACY-NOMEM` and
seven `ST-*` / `STATE-*` transition-target stubs), listed with a recommendation in the report.
**Nothing was deleted.** Production has no projects, so nothing there is affected.

**`refuse_unless_pm_for_assignment` WAS NOT CLOSED THE SAME WAY, AND THIS NEEDS LIN.** Closing it
literally would stop the study running: a scenario names one evidence project, several
participants share a scenario, and migration 0006 allows exactly one active PM per project, so
requiring PM there means **one evidence project can serve exactly one participant**. Leaving the
old test in place was not an option either, because creation now always writes a PM row, so
"does this project have members" is true everywhere from today. The guard now reads **the
caller's own row**: an Observer is still refused, a caller with no row proceeds on the strength
of an assignment that `_resolve_target` has already bound to them. **If participants sharing an
evidence project must each be its PM, that needs either per-participant evidence projects or a
change to 0006's unique index — a study-design decision, not made here.**

**ADMINISTRATION IS TWO TABS.** People and access (accounts, project membership, scenario
assignment) and Monitoring and export. Nothing withdrawn; all 28 controls checked by id in a
browser. The two relationships on the first tab, operational access and study participation, sit
under separate headings with a rule between them, and the check resolves which heading each
control actually sits under rather than reading wording.

**Two defects found on the way.** The **Create export button did nothing at all**: its handler
wrote into an `ao-export-error` element that was never in the markup, on its first line, so it
threw before doing anything and the statement that would have shown the error was the statement
that threw. And the tab switcher held a **hardcoded list of panel names** in `app.js` separate
from the markup, which would have silently revealed nothing after any rename; it now derives them
from the tab bar.

**The admin is PM of nothing, and that is correct.** Every local project with an owner already
has the right one; the eight without are debris that should be deleted, not adopted. Production
is empty. Creation assigns the PM from here on.

# 2026-08-02 — GEOCODING: NOMINATIM IS GONE, GOOGLE IS PRIMARY, CENSUS IS THE FALLBACK

Full detail in `REPORT_2026-08-02_geocoding-provider.md`. **Server 1259 checks across 23 suites,
`tests_render.html` 43/43, `tests.html` 51/51, all green after merging `origin/main` at `aa681ab`.**

## NOTHING GEOCODES WORLDWIDE UNTIL A KEY IS PROVISIONED. This is the first thing to check.

- Environment variable: **`GOOGLE_GEOCODING_API_KEY`**, set on the Render web service.
- Enable the **Geocoding API** in the existing Google Cloud project (the OAuth one).
- Billing must be enabled on that project or the key returns `REQUEST_DENIED`.
- Restrict the key to the **Geocoding API**. Application restriction: **IP, not HTTP referrer.**
  This key is used server side and a referrer restriction would reject every request.

Until then the code is inert and safe: with no key, `_google()` returns `NOT_CONFIGURED` **without
making any request**, Census still handles United States addresses, and the user is told the
service is not configured rather than told their address is wrong.

## The seam is a tuple of functions. Do not build an abstraction layer on it.

```python
_PROVIDERS = (_google, _census)   # in server/app/geocode.py
                                  # order is precedence; append to add a third
```

`geocode()` walks it and stops at the first provider returning a position. `_get_json(url)` is the
single HTTP seam, and it is the one thing the tests replace, which is why they are fully offline.
The public contract (`geocode`, `apply_to_doc`) is unchanged and both callers are untouched.

## What must not regress

1. A failed geocode does **not** erase coordinates it cannot replace. `apply_to_doc` reads
   `previous`, the STORED doc, so a client payload cannot delete stored coordinates.
2. The matched address is shown back to the user, as `formattedAddress`.
3. A retained position is flagged `geocodeStale` and labelled as belonging to a previous address.
4. Answers about the **address** are cached. Answers about the **service** (quota, rejected key,
   absent key, timeout) are **never** cached, or one bad minute becomes permanent.
5. A "not found" is never claimed on the strength of Census alone. Census is United States only.
6. Google's `error_message` is logged, never shown. It can name the key restriction that refused
   the request.

All six are asserted by checks in `server/tools/test_geocode_providers.py`, 31 checks, all proven
able to fail by 18 injected faults.

## Things that cost this session time. Read these.

- **The old note in this file said the geocoding tests stub `app.geocode.geocode` and to keep it
  that way. That is still true of `test_workspace_t3t5.py`, and it means that suite never
  exercised a provider at all.** Every provider branch was uncovered. That is why
  `test_geocode_providers.py` exists separately. Do not merge them.
- **Reverting a fault injection is as easy to get wrong as writing one.** A string-replace patcher
  that hits the first occurrence swapped two error sentences on revert, silently, and six later
  results were measured against a corrupted module before a restore-and-recheck caught it. Check
  the suite returns to full green after **every** fault, not just at the end.
- **Most server suites need a migrated database and `SESSION_SECRET`.** Run against a stale
  `server/dev.db` they abort with `KeyError` and print **no `RESULT:` line at all**, which skims
  like a clean run. Build a throwaway sqlite with `alembic upgrade head` and copy it per suite.
- **`preview_start` resolves `.claude/launch.json` from `DEng\Demo`, not from the repository**, so
  the repo's own config is not what runs. `Demo/opus-gubernatio` is a different repository. Serving
  the repo needs a temporary config entry there; remember to revert it.
- **The Census fallback is patchier than it looks.** It missed a plain numbered street address in
  Philadelphia, not just facility names. Do not read "Census is the fallback" as "United States
  addresses are covered".

## Backfill: not run, and it is two different questions

Locally: 2 projects, both already have coordinates, **0 need a backfill to gain any**. Production
was not queried; the SQL to count it yourself is in the report.

Separately, both local projects were placed by the retired provider and one is wrong: "Philadelphia
International Airport" resolved to a Hampton Inn on Bartram Avenue. Re-placing everything the old
provider placed is a **different and larger** backfill than filling gaps, and it overwrites data.
Both are yours to approve. Neither script was written.

## Still open, from an earlier session

Branch **`t15-local-unpushed`** (`9dc137d`) holds five never-pushed commits. The only substantive
code in them is the `unported_modules()` correction at `server/app/simulation/registry.py:49`;
`origin` still has the version that over-reports the five Group D modules as unported. Preserved,
nothing lost, needs a decision. Acting on it means editing `server/app/simulation/`.
# 2026-08-02 — READS FAIL CLOSED TOO: THE FACADE IS AUTHENTICATED END TO END

Full detail in `REPORT_2026-08-02_read-authorisation.md`. **1228 checks across 22 suites,
`tests.html` 51/51, `tests_render.html` 43/43.** Compositing proven (62–63 rAF/s). No stored data
altered, production not inspected. **No overlap with the parallel geocoding session:
`documents.py` and `geocode.py` are untouched.**

**WHAT WAS READABLE WITH NO CREDENTIAL, probed against a PM-owned project with membership rows:**
`list` and `listarchived` returned **every project's full document** (name, sector, status,
`signals`, `signalInputs`, the whole event log); `listslim` returned every project's cpi / spi /
docRiskScore; `get`, `gethistory`, `listcorpus`, `listauditresults` returned one project's
document, stored period snapshots, corpus and audit rows; `getportfoliohealth` returned the
deployment-wide snapshot. All eight now refuse. Verified over real HTTP, not only in a test.

**WHAT STAYS PUBLIC: `health`, `ping`, `version`, and nothing else.** Probed against a populated
database — build/capability info only, no project data. Named explicitly in `PUBLIC_GET_ACTIONS`,
so **a read added to GET_ACTIONS is closed by default** and opening it is a visible edit to that
line. That inversion is the fix for what let the write side rot.

**NOTHING LEGITIMATELY PUBLIC BROKE, and I expected it to.** Instrumented the browser: **zero
`/exec` GETs before sign-in** — `LinApp.init()` (which calls `loadSlim`) runs only after
`LinAuth.init()` resolves a session, so the sign-in page needs no project read. The **static
mirror** already degrades to "can't reach the store" and is unchanged. The **captured GET
contract** is read from disk by `seed_from_fixtures.py` / `import_from_drive.py` and never
replayed against the server, so no contract breaks; response shapes are unchanged.

**THE CREDENTIAL IS A HEADER.** `Authorization: Bearer`, with `X-Session-Token` accepted.
store.js's "no custom headers → no preflight" comment came from Apps Script; **that constraint
expired at T1** when the app moved to the same origin as `/exec` (config.js says so). Verified in
the browser: every GET after sign-in carried the header, **no token in any URL**.
`session_token` in the query string is kept ONLY as a fallback for `/documents/{id}/content`,
which is an iframe `src` and cannot set headers — the reasoning, including that URLs are logged by
intermediaries, is written at `_session_token_from` so it is not re-adopted as the general
mechanism.

**MEMBERSHIP, ON THE WRITE GUARD'S TERMS.** `guard_project_read` authenticates first, then
requires an ACTIVE MEMBER (not PM — an Observer exists to read) for the four project-scoped reads.
A missing project still returns its own "Not found" rather than an authorisation error, so an
attacker cannot tell absent from invisible. **Collections are FILTERED, not refused** — a
portfolio call that failed because one row belongs to someone else would be unusable. Verified
live: OPS-1's portfolio went from 3 projects to 2, dropping the research participant's.

**A GAP CLOSED AS A SIDE EFFECT:** `gate_action` leaves sessionless callers alone (no flags to
apply), so an anonymous `getportfoliohealth` used to **bypass the feature flag** a signed-in user
with it off is held to. The read guard sits one layer up; dropping the credential is no longer a
way round the flag. That was the previous report's authorisation gap 2.

**REPORTED NOT FIXED, both hinging on the same missing membership rows.** (1) **An unmembered
project is readable AND writable by any authenticated caller** — measured: an unrelated signed-in
user read and archived one. It is now the only route from one authenticated user to another's
project. Closing it makes every such project invisible and unwritable **to its real owner too**
until membership is backfilled; locally 1 of 4 projects, **production unknown and not inspected**,
and the imported Apps Script projects are exactly that population. Two-step change, and the
backfill needs a decision about what "owner" means for a Drive-imported project. (2)
`refuse_unless_pm_for_assignment` has the same unmembered arm on the decision flow; smaller,
because those actions already require a session.

**EIGHTH SESSION, AND THE TWO KNOWN FAILURE MODES BOTH RECURRED — both caught.** (a) Faults aimed
at the header carrier made `test_writes_a1b` **crash with no RESULT line** rather than fail,
because its fixture setup reads the facade everywhere; the carrier checks moved to `test_features`,
whose reads are not load-bearing and whose assertions use `.get()`. (b) The injection harness now
prints `fault applied` only when the anchor matched and `ANCHOR DID NOT MATCH` otherwise, so no
result is read from a fault that never applied. **Seven faults, all confirmed applied, all clean
reds:** 89/92, 41/43, 90/92, 91/92, 48/49, 47/49, 48/49.

**A SEED ARTIFACT NEARLY READ AS A REGRESSION.** The research participant's browser check first
showed 0 projects — which looks exactly like the filter over-refusing. It was not: the seed created
that project through the sessionless `create` the PREVIOUS session had already closed, so it never
existed. Worth knowing because "the legitimate user sees nothing" is the shape a real regression
takes.

**STILL OPEN:** whether `getportfoliohealth` should be membership-scoped (it is a cross-project
aggregate with no owning project, so there is nothing to scope against; the feature flag still
gates it per account). Reads leave **no trace**, so whether the exposure was exercised in
production is less detectable than the write case, where the project event log at least records
that something happened.

---

# 2026-08-02 — THE FACADE FAILS CLOSED: UNAUTHENTICATED WRITES ARE DENIED

Full detail in `REPORT_2026-08-02_unauthenticated-writes.md`. **1216 checks across 22 suites,
`tests.html` 51/51, `tests_render.html` 43/43.** Compositing proven (63 rAF/s). No stored data
altered, production not inspected.

**WHAT WAS REACHABLE WITH NO SESSION TOKEN AT ALL, measured against a signed-in PM's project WITH
membership rows: every legacy facade write.** `save` (replaced the whole document), `resetsignals`,
`archive`, `restore`, **`setprojectnumber` (renamed the project id so the old one stopped
resolving)**, `overwritesignal` (set `cpi` to 0.01, and invented a field name), `savehistory`,
`saveauditresult`, `create`, `saveportfoliohealth`. **All GETs too** — `list`, `get`, `gethistory`,
`listauditresults`, `getportfoliohealth` return any project's full document to anyone.

**WHAT WAS NEVER EXPOSED, and this boundary held:** every research / document / workspace / admin
action refuses without a token — `projectupload`, `projectcompute`, `projectresults`,
`adminrecompute`, `researchprejudgment`, `adminexportcreate` and the rest, eleven probed, all
refused. **The research record, decision sequence, exports and computed results were not reachable.**

**WHY IT WAS OPEN, and the reason has expired.** `486487c` (B8) layered authorisation onto a facade
that had never had authentication and deliberately kept sessionless calls working "so nothing
changes for pre-B8 flows" — because `store.js` posted no token. But the browser already held the
session (`LinAuth.getToken()`; workspace.js and decision-ui.js always sent it). **That is a client
not presenting a credential it had, not a dependency on anonymous writes.** `store.js` now attaches
it in one `withSession` helper used by both POST paths.

**THE FIX, at the guard.** No token → refuse. `settings is None` → refuse. The guard now covers
`PROJECT_WRITE_ACTIONS ∪ POST_ACTIONS`, because the two lists had drifted: **`create` and
`saveportfoliohealth` were in POST_ACTIONS and in no guard at all.** `PUBLIC_WRITE_ACTIONS` is a
named, deliberately EMPTY allowlist: anything needing to be public says so at its own site.

**TWO MORE FAIL-OPENS FOUND INSIDE THE SAME GUARD.** `resolve_caller` ran AFTER the membership
check, so on an unmembered project a **forged or expired token** was as good as a valid one —
authentication now runs first. And **the PM rule had never applied to `save`**: every other action
puts its id at `payload["id"]`, `save` puts it at `payload["project"]["id"]`, so the guard resolved
no project and allowed it. Measured: an authenticated non-PM renamed someone else's project. **The
old test asserted that as correct**, which is why nothing caught it.

**STILL OPEN, REPORTED NOT FIXED: reads.** Every GET is unauthenticated and returns project
documents including `signalInputs` and the event log. Not fixed because authenticating them means
a token in a query string, changes the captured GET contract, and affects the static mirror. It is
the largest remaining item and it is Lin's. Also still open, all authorisation rather than
authentication: a project with **no membership rows** is writable by any authenticated caller (the
pre-B8 legacy shape — closing it locks out every imported project until membership is backfilled);
`gate_action` leaves sessionless callers alone, which is harmless for flags and NOT harmless for
`getportfoliohealth` reads; `refuse_unless_pm_for_assignment` has the same unmembered arm.
`enforce_consent` was checked and **fails closed correctly**.

**REPORTED NOT FIXED, as instructed:** `w_saveportfoliohealth` still deletes prior snapshots (still
the only `session.delete`), `w_overwritesignal` still accepts an arbitrary field name and value
(measured: `totally_made_up = "anything"` stored; only `docRiskScore` is range-checked, and that
guard fired even for the anonymous caller). **Both are now unreachable unauthenticated.**

**THE DECIDED ITEM IS IN: `signals_extracted` on upload, not backdated.** One event per
CONTRIBUTING document, server clock. **C1.4 goes Amber 50% → Yellow 100%.** Qualification worth
knowing: it counts only when the period cutoff is on/after the upload date. On a genuinely
back-dated document (June report, August upload, cutoff 2026-06-30) `_events_as_of` truncates it
and **C1.4 stays Red 0%** — the improvement lands on wall-clock-cutoff projects (the D3 fallback),
not on ones with real document dates. Backdating would falsify the trail to improve the module that
measures it; the understatement stands.

**TWO TESTS STRENGTHENED as a side effect.** `test_d1_module_inputs` asserted truncation against a
hardcoded date while its fixture had no parseable `document_date`, so the cutoff was silently the
wall clock and the assertion passed by coincidence; it now supplies real dates and compares against
each period's own stored cutoff. `test_documents_b7b` Guarantee 1 compared the whole
`signal_inputs` blob across two projects sharing a cached document — since D1 that includes
project-scoped `events`/history, which legitimately differ; it now excludes those three keys AND
asserts the difference is confined to them, which is stronger than what it replaced.

**SEVENTH CONSECUTIVE SESSION WITH A VACUOUS CHECK — TWO THIS TIME, BOTH FOUND BY INJECTION.**
(1) The anonymous-write checks CRASHED instead of failing: a successful anonymous
`setprojectnumber` moved the target project, the read-back did `["project"]` on a missing key, and
the suite died printing **no RESULT line** — exactly the failure mode last session recorded. The
rename now has its own throwaway target and every read-back uses `.get(...) or {}`. (2) The "per
contributing document, not per request" check could not tell the two apart, because every upload in
that fixture carried one document; it now uploads two in a single request. Also caught an
injection-HARNESS bug: one fault silently failed to apply and reported a false clean.

**Eight faults injected, distinct signatures:** 73/87, 85/87, 86/87, 84/87 on the guard; 70/73,
73/74, 72/73, 70/73 on the upload event.

**PRODUCTION:** the deployed code is what was measured and the exposure needs no credential, but
**whether it was exercised is unknown and was not investigated.** The facade writes nothing to
`audit_events`, so an anonymous write leaves no audit trace — though the project's own log does
record `signals_reset` / `project_archived` / `project_number_changed` / `signal_overwritten` with
a timestamp. A query Lin can run is named in the report.

---

# 2026-08-02 — THE EVENT LOG STOPS BEING DELETED; UPLOAD EVENTS ESTABLISHED, NOT SHIPPED

Full detail in `REPORT_2026-08-02_append-only-fix.md`. **1190 checks across 22 suites,
`tests.html` 51/51, `tests_render.html` 43/43.** Compositing proven (63 rAF/s). No stored data
altered, production not inspected.

**PART 3 IS A DECISION WAITING ON LIN, AND NOTHING WAS SHIPPED FOR IT.** `docCount` is read by
**no user-facing surface anywhere** (grepped the whole repo outside the baseline capture), so
writing upload events changes it 0 → N in an API response nobody displays. **But C1.4 DOES move
and is user-visible:** `project_created` only (every server project today) = **Amber 50%**;
+`signals_extracted` = **Yellow 100%**; + a compute event = **Green 100%** (it needs
`total_events >= 3`). Category C1 moves with it; **project colour does not** (Group C does not
vote). Two things to know before deciding: `_events_as_of` truncates at the period cutoff, so a
June report uploaded in August produces an August event that **does not count for that period** —
measured, C1.4 stayed at 50%; backdating it would be recording an event as having happened when it
did not, which I would not do unasked. And `signals_extracted` also populates `detail.js`'s
Uploaded Documents table, currently empty for server uploads.

**THE BRIEF'S PREMISE NEEDED CORRECTING, AND IT CHANGES THE DEFECT.** `w_resetsignals` does **not**
touch `audit_events`. There are two stores: `audit_events` (the research trail — **verified
genuinely append-only**, no UPDATE or DELETE anywhere in `server/app/`, untouched across a reset)
and `doc["events"]` (the legacy per-project JSON list, written by `_append_event`). The latter is
what was truncated. Narrower than feared — the research record was never at risk — and wider in
another direction: **the legacy facade writes nothing to `audit_events` at all**, so a reset leaves
no research-audit record that it happened, even now. Reported, not fixed.

**THE DELETION WAS NOT LOAD-BEARING, checked before deciding.** Every surface that reads the log
filters it itself, and `docCount` counts `signals_extracted` specifically. What the deletion DID
change, since D1 wired `events` into signalInputs, is **C1.4: dropping `project_created` takes it
from Green 100%/3 events to Red 0%/1 event** on a project whose trail was intact. The reset was
reporting a worse audit trail than the project had. It now leaves the log alone and records itself
with `_append_event` — the shape this module already uses for every other mutation — carrying what
it cleared **by shape, not by value** (field count, field names, blocks, module count, reason);
writing the values into an event `get` returns would defeat the action.

**PART 2 FOUND A LARGER VIOLATION IN `w_save`, AND IT IS FIXED.** It replaced the stored doc
wholesale, so `events` was whatever the client sent. Measured: **a save with no events key wiped
the log; a save with a fabricated one-entry list replaced it; both accepted with no concurrency
token**, because `_check_not_stale` passes when the client presents none — and the legacy frontend
presents none. This is the path the frontend actually uses, and a slim-loaded project never carried
`events`, so an ordinary address edit destroyed the log. Rule now: **the log may be extended, never
shortened or substituted.** The client is a legitimate appender (`signals.js` pushes
`simulation_run` then saves), so the server cannot own the list; a check asserts the append still
works.

**EVERY OTHER FACADE ACTION SURVEYED BY EXERCISING IT, not by grepping `.pop`.** create / archive /
restore / setprojectnumber / savehistory / saveauditresult all append (savehistory verified to
accumulate: two saves for one period leave two rows). **`w_saveportfoliohealth` still deletes** all
prior portfolio-health snapshots — the only `session.delete` in the app, atomic, deliberate per its
comment. Reported, not changed. **`w_overwritesignal` unchanged as instructed**: still accepts an
arbitrary field name and value, PM-gated, `docRiskScore` range-checked only.

**WHO CAN CALL THE RESET: anyone.** `guard_project_write` returns allow when no session token is
present. A completely unauthenticated POST of `{"action":"resetsignals","id":...}` is accepted —
measured. Documented as the deliberate B8 posture; not changed here.

**ALREADY-LOST DATA: none locally (3 project rows, 0 with a `signals_reset`), production not
inspected.** Detectability differs: a reset-truncated log is identifiable (`signals_reset` present,
`project_created` absent — a query Lin can run on production), **the `w_save` wipe leaves no trace
at all and is neither detectable nor recoverable.**

**THE RESEARCH EXPORT IS NOT EXPOSED.** It reads `AuditEvent` only, and only `evidence_viewed` for
the two timing variables; it never reads `doc["events"]`. `EXPORT_COLUMNS` (39) names no event,
result or audit column — the stages 7-8 finding that it carries no `result_id` is unchanged. A
decision traces through `Decision.result_id` → `ComputedResult.source_documents`, none of it
through the deleted log.

**SIXTH CONSECUTIVE SESSION WITH A VACUOUS CHECK, CAUGHT BY INJECTION.** The `w_save` checks read
`resp["project"]["events"]` directly, so with the fix removed the suite died on `KeyError` before
asserting and printed **no RESULT line** — the first injection pass looked clean. They now go
through a helper returning `None` for a missing key, so the fault makes them FAIL. Four faults,
distinct signatures: 67/70, 68/70, 66/70, 68/70.

---

# 2026-08-02 — GEOCODE RETENTION, AND THE DECISION CARD STOPS CONTRADICTING ITSELF

Full detail in `REPORT_2026-08-02_geocode-and-decision-card.md`. **1177 checks across 22 suites,
`tests.html` 51/51, `tests_render.html` 43/43.** Playwright + pre-installed Chromium, compositing
proven first (62 rAF/s). No coordinate data was written, repaired or backfilled.

**A FAILED GEOCODE NO LONGER ERASES THE COORDINATES IT CANNOT REPLACE.** `apply_to_doc` cleared
lat/lng/formattedAddress on every failure, and since Nominatim has never been reachable from this
deployment that meant **every address edit destroyed the project's location**. The coordinates now
stay, `geocodeStale` marks them as belonging to an earlier address, and `formattedAddress` is
carried with them because it names the address they actually matched. Nothing is retained when
there was nothing to retain; a later success clears the flag; clearing the address still drops
everything, because that is the user saying there is no place. **Retention reads the STORED doc**
(`apply_to_doc(..., previous=project.doc)`), since `w_save` replaces the stored doc wholesale and a
client omitting lat/lng must not be able to delete a position by leaving it out.

**THE SAME SHAPE ELSEWHERE: exactly one instance, and it was this one.** Every `.pop` on a stored
document outside `simulation/` is either the defect above or `w_save`'s address-CLEARED branch,
which is a success path. `_derive_cutoff` substitutes the wall clock for a missing value rather
than discarding a stored one (still D3, still open). `extract_many` refuses and stores nothing.
`store.js hydrate` was this shape and was fixed generally in PR #198.

**ONE COMPOSED STRING, FLAGGED FOR REVIEW.** The unreachable-geocoder message said "so this project
has **no map position yet**", which became false once a position was retained — it would have shown
a pin while asserting there was none. It now reads "so this **address has not been matched** yet".
The "Map position is for the previous address (X)." clause is also composed. Neither is liability
language; one string each. `linLocationNote()` in `config.js` is now the single definition of how a
location reads, because four surfaces render it (disclaimers.js reasoning).

**THE CARD'S CONTRADICTION WAS TWO SOURCES, ONE OF THEM DEAD.** The badge reads stored
`project_status`. `deriveActionPlan` has three branches and **only the third was ever reachable**:
`CATEGORY_ACTIONS` is keyed cat1..cat11 while `LIN_CATEGORIES` ids have been a1..d1 since
`fd5bf45`, so its lookup never matches; `fusion.redFlags` has not existed since taxonomy.js
replaced categories.js. So its only output was a hardcoded "All categories Green / Routine
monitoring" row, printed beside a Red badge. **The all-clear fallback is deleted and nothing
replaces it** — `actionPlanHtml` already renders nothing for an empty plan, which is the same
abstain-by-absence contract the server keeps. `CATEGORY_ACTIONS` was NOT repointed: that would
switch on a recommendation engine that has never run, which is Lin's decision.

**WHAT A FULL D7.2 FIX NEEDS, and it is not a wiring job.** Measured across every key on every
stored module: **only `recommended_action` exists** (B4.7 Regret Minimization, vocabulary
{monitor, investigate, escalate}, redaction-gated). **Nothing stored emits an authority, a
documentation requirement, or a fairness gate.** `fairnessSensitive` is still absent from
SIGNAL_INPUT_KEYS and still not wired by `documents.py` — D1 wired `events`/`spiHistory`/
`cpiHistory` and left it in the permanently-abstaining set, so **the gate has never been able to
fire and still cannot.** Three routes are laid out in the report; all three need a decision about
`fairnessSensitive` of its own. The card's four derived fields are untouched and are NOT
contradictory (they derive from the badge's own status); removing them needs wording that does not
exist, so I stopped there as instructed.

**A VACUOUS CHECK WAS WRITTEN AND CAUGHT BY FAULT INJECTION.** The address-cleared check first ran
on a project whose flag had already been cleared by an earlier success, so it passed whatever the
code did. It now asserts the precondition that the flag is set at that moment. Fifth session
running that a check turned out to pass for the wrong reason, and again injection caught it, not
review.

**ALSO DEAD, REPORTED NOT TOUCHED:** `detail.js:1558` reads the same non-existent `f.redFlags`. It
fails safe, so it makes no false statement.

---

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
