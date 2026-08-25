# Training Simulation — PMP Area Coverage Upgrade

Threads, not runs of different length. One primary thread runs the whole simulation; secondary
threads open and close inside it. Thread count is the difficulty knob.

**Covered by the dispute thread:** schedule, cost, risk, procurement.
**Not covered:** quality, resources, communications, stakeholder, scope, integration.

Each run adds thread types: an event, decision options, consequences, and one state variable that
persists. Integration is not a thread; it emerges when threads compete for the same float and
contingency.

Status key: OPEN / RUNNING / DONE

---

## Run 1 — Quality thread — 50% — Sonnet

DONE (2026-08-04). Failed inspection, opening at period 6 (clear of the standing period-4 near
miss and of periods 1-2, which stay dispute-only on purpose). Its own three verbs
(`accept_nonconforming` / `rework_now` / `rework_later`), NOT the dispute's — the one place this
thread diverges from the `dsc` precedent, and it mattered: reusing the dispute's verbs (as `dsc`
does) would not have created real competition, since the trainee would be deciding one thing for
two matters at once. Defect backlog compounds 20% per deferral and forces automatically after 3
deferrals, at whatever period that lands on. `QUALITY_FIGURES`, designed, beside
`EVENT_FIGURES`, led with in `REPORT_2026-08-04_training-quality-thread.md` for correction.
**The pattern is now explicit** (event, own verbs, effect table, registration via
`allowed_decisions`/`quality_position`/the debrief) and is what runs 2-4 should match.

**Session usage ran close to a full session, not half** — the design and wiring across five
files fit the target; verification (fault injection plus a real browser drive requiring a
hand-bootstrapped operational account) was the larger, unbudgeted half. **Runs 2-4 should treat
per-thread verification as a fixed cost on top of the wiring cost, not assume it shrinks with
practice.**

**Left open, reported rather than built:** `build_recommendation` does not yet reason about an
open quality matter — a trainee mid-run sees nothing about it in the recommendation panel. Not
picked up here; a candidate for a small follow-up or for run 4's composition/debrief work, which
already touches the "what was traded against what" surface this would extend.

## Run 2 — Resources thread — 80% — Opus

DONE (2026-08-04). Key trade shortage opening at period 7 by the new spacing rule, with its own
three verbs (`pay_premium` / `resequence` / `accept_delay`) following run 1's shape. Crew
adequacy is a MULTIPLIER ON EARNING, not a cost paid when acted on: it multiplies into the same
`ev_factor` chain as the deferral penalty and the restart loss, so a low value slows every
period whatever the trainee spent it doing. Accelerating with scarce trades costs 1.8x the
premium and adds 0.25 extra hazard. `RESOURCE_FIGURES`, designed, led with in
`REPORT_2026-08-04_training-resources-thread.md` for correction.

**THE SPACING RULE IS SOLVED AND RUN 4 DEPENDS ON READING IT.** Openings are derived
(`thread_opening_periods()`), skip periods reserved by discrete events, and REPRODUCE the
periods run 4 and run 1 were verified against rather than renumbering them. **It supports
exactly three secondary threads at the current run length; a fourth is refused with a stated
reason.** Run 4's "spine plus three for a hard run" is exactly at that ceiling with nothing
spare -- see the report before assuming a fourth will fit.

Came in around the 80% target. The wiring shrank because the pattern existed; verification did
not, and the browser drive remains the most expensive step and the one that finds the most (it
caught a defect 61 passing server checks missed). **A reusable fixture that bootstraps an
operational training account and session token would pay for itself across runs 3 and 4;** not
built here because shared test infrastructure built inside a thread task gets shaped by one
caller.

As originally scoped: key trade shortage; pay premium, resequence, accept delay; crew adequacy
degrading productivity while low. Built as scoped, with its own verbs, and the pattern held.

**Correct the effect table after playing this before starting run 3.** Run 3 builds on top of it,
and an uncorrected productivity penalty propagates -- more so than for any earlier table, because
this one is a multiplier on earning rather than a one-off charge, so an error in it compounds
across every period of every run rather than landing once.

## Run 3 — Communications, stakeholder and scope threads — 80% — Opus

OPEN

Communications: bad news arrives. Tell the owner now, wait for the next report, let them find out.
Variable: information currency.

Stakeholder: the owner's representative is not the decision maker. Work through them, escalate above
them, proceed on their word. Variable: stakeholder alignment.

Scope: informal owner request. Treat as change, absorb as goodwill, refuse. Variable: undocumented
scope, converting to claim exposure or a loss at closeout.

Three together because communications and stakeholder both act on owner credibility, which already
exists, and scope shares the notice mechanics from the contract regimes. Splitting them would mean
three sessions touching the same two variables.

Scope's consequence lands at closeout rather than the next period, which is a longer feedback path
than anything built so far. Report how that is surfaced so a trainee connects it back.

**From run 2: the spacing rule caps live secondary threads at three.** These are three new
thread TYPES, which is fine (composition picks which are live), but three of them cannot all be
live alongside the site condition and quality without changing `PERIODS_TOTAL`,
`THREAD_OPENING_FIRST_PERIOD` or the play-out reserve. The rule refuses loudly rather than
overlapping, so this surfaces as an error, not a silent collision.

## Run 4 — Composition, difficulty and cross-area debrief — 80% — Opus

OPEN

A run picks its threads rather than having them authored: spine plus two secondary, or plus three
for a hard run. Thread count is the difficulty setting. Threads open and close at varied periods so
no two runs feel identical.

This is where integration becomes teachable, because it is the first time threads compete for the
same float and contingency by design rather than by accident.

The debrief extends to say which areas the run exercised and what was traded against what. A trainee
who protected schedule by neglecting quality should see that stated.

Composition is mostly wiring once the threads exist, which is why it carries the debrief work too.

**From runs 1 and 2, both outstanding and both now overdue:**
- `build_recommendation` still reasons only about the claim. Two threads' worth of open matters
  are invisible to it mid run. It should not slip past this run.
- The spacing rule's three-thread ceiling is exactly where "plus three for a hard run" lands.
  Decide deliberately whether to raise it rather than discovering it by a refusal.
- A reusable operational-training-account fixture for the browser drive.

---

## Budget

Four runs: one at roughly half a session, three at roughly 80%. Around three sessions total,
assuming no rework.

Sonnet for run 1, which establishes a pattern rather than inventing one. Opus for 2 to 4, where the
effect tables and the interaction between variables need judgement.

## Standing constraints, unchanged

- Operational accounts only; research accounts refused server-side.
- Training data never reaches the export or the research chain.
- Mechanics fixed for the same conditions. Directors disagree about the call, not about whether
  escalating spends float.
- The narration layer computes nothing.
- Signals compute through the platform's own path. No training-only computation.
- Groups and purposes are the better default. Displayed module ids and numbers are acceptable;
  the former prohibition was SUPERSEDED by the owner on 2026-08-23.

## Open before or alongside

- Items 1 to 3: the designed figures, yours to tune after playing.
- Item 14: A201 and ConsensusDocs periods verified against the licensed documents.
- The category rollup divergence, 47 of 80 categories fusing green over a red contributor. Not a
  training defect; a fact about the real instrument, and it outranks this roadmap.
