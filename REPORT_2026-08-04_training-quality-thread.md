# Training upgrade run 1: the quality thread, and the pattern

2026-08-04. Branched from `origin/main` at `176a65a`, with training mode runs 1 to 5 all merged
(#207 to #211). No migration; state lives on `TrainingRun.state`'s existing JSON column.
Nothing under `server/app/simulation/` modified. Production still lacks 0018 and 0019, and now
needs no further migration for this run either — **but that gap is still open, and production
must still be migrated before the next training run reaches it**.

## The pattern, first, since three more runs depend on it

A thread type is four things, and this run had to name all four before it could build one:

1. **An event** that fires at a fixed period, undisclosed until then. `s["period"] ==
   QUALITY_INSPECTION_PERIOD and s.get("quality") is None` in the same discrete-trigger block
   that already opens the differing site condition (`DSC_PERIOD`) and the standing near miss —
   one place in `advance()`, not three.
2. **Its own decision verbs**, not the spine's. Quality decides through `accept_nonconforming
   / rework_now / rework_later` (`QUALITY_DECISIONS`), never through the dispute's
   `escalate/absorb/defer/accelerate`. This is the one place this thread diverges from the
   `dsc` precedent it otherwise follows: a differing site condition is still a notice matter and
   reuses the dispute's own verbs; a failed inspection is not a claim and needed its own three.
3. **An effect table of designed figures**, in one place (`QUALITY_FIGURES`, beside
   `EVENT_FIGURES`), explicitly marked designed and reported below for correction.
4. **A registration**: `allowed_decisions(state)` returns the union of the standing set and the
   thread's own verbs while it is open; `advance()`'s validation accepts the union too;
   `quality_position(state)` derives the thread's screen surface the same way `dsc_position`
   does; `_state_view` in `training.py` carries it as `quality_notice`, the same shape as
   `dsc_notice`; the debrief carries a `quality` outcome alongside `closed`.

**How a secondary thread opens and closes.** `dsc` is None until its period, then a dict; a
thread's presence on the state IS its open/closed state, nothing else tracks it. It closes one
of three ways, and all three are terminal statuses on the same dict rather than three different
mechanisms: `resolved` (rework_now, or a later deferral), `accepted` (a permanent closeout
figure, not a zero), or `forced_resolved` (the state forced it without a decision at all,
inside the SAME period-open trigger block the opening lives in — a thread can close itself the
same way it opens itself, on the clock alone). A run 2 thread that needs a fourth close state
fits this shape; one that genuinely can't should say so rather than force it.

**Where I diverged from the `dsc` precedent, and why it mattered.** My first instinct was to
give quality the SAME menu the dispute uses, the way `dsc` does. That would have been faster to
build and would have taught nothing: reusing `escalate/absorb/defer` doesn't create competition,
because the trainee would just be deciding the SAME thing for two matters in one act (as `dsc`
does today — one escalate serves both the claim and the site condition, on purpose, since both
are notice matters under one clock family). Quality needed a genuinely separate verb set so that
choosing one thread's action is visibly NOT choosing the other's. **Report this explicitly for
run 2**: resources' pay-premium/resequence/accept-delay is already a different verb family from
the dispute's, so it should follow quality's shape, not `dsc`'s.

## The effect figures, DESIGNED, for correction

In `QUALITY_FIGURES`, `server/app/training_engine.py`, beside `EVENT_FIGURES`:

| Figure | Value | What it does |
|---|---|---|
| `defect_value_rate` | 0.004 (0.4% of contract value) | the defect's rework cost when found |
| `rework_now_float_days` | 3 | float spent to clear it immediately |
| `rework_later_growth_rate` | 0.20 (20% per deferred period) | the backlog compounds while deferred |
| `rework_later_float_drift_days` | 1 | a small drift even before the cliff |
| `force_after_periods` | 3 | deferrals before the backlog forces rework |
| `forced_rework_float_penalty_days` | 5 | costs more float than choosing it would have |
| `accept_credibility_cost` | 1 | credibility spent by accepting nonconforming work |

`QUALITY_INSPECTION_PERIOD = 6`, not an earlier period. Periods 1 and 2 leave the dispute the
only live thread on purpose (a trainee meets one thread's shape before a second arrives).
Period 4 is the standing scheduled near miss (`EVENT_FIGURES["near_miss_period"]`, from run 3):
opening quality there would force every run's very first quality decision through a stop work
order response, by construction, before the trainee ever sees the three verbs. Six is clear of
both, still well inside AIA's 21 day claim window and past ConsensusDocs/FAR's own claim
mechanics, and leaves four periods for the backlog to compound or force before the run ends.

Driven in a browser: a $12,000,000 contract produces a $48,000 defect ($12,000,000 × 0.004),
read back from the DOM at period 6 exactly as designed.

## Two things to get right

**Competition, proven, not asserted.** `allowed_decisions` returns `DECISIONS +
QUALITY_DECISIONS` while quality is open — one menu, one decision per period, drawn from
whichever threads are live. `escalate` and `rework_now` both move `float_consumed_days`, the
SAME counter (`test_training_quality.py`, "COMPETITION"); `absorb` draws
`contingency_remaining`, the SAME pool `rework_now`'s AC draw sits beside. There is no
`quality_float` or `quality_contingency`. Choosing one thread's action for the period leaves the
other's exactly where it was — proven, not assumed, by checking both states after
`escalate` and after `rework_now` from the same starting state. A fault that gave quality its
own float pool (fault injection, below) was caught by exactly this check.

**Lifecycle.** Quality opens at a fixed period (undisclosed before it, same as `dsc` and the
near miss); it closes at a period the state determines, not the run's end: `resolved` on
`rework_now` or a documentation-style close, `accepted` (permanent, non-growing exposure) on
`accept_nonconforming`, or `forced_resolved` automatically once deferred
`force_after_periods` times, landing at whatever period that arithmetic produces. The dispute,
by contrast, is the spine: it is present from period 1 and the run's own length is its only
outer bound. A run can therefore have zero, one, or (from run 4) several secondary threads live
in any combination, and the pattern above is what "the same shape" means for whichever run adds
the next one.

## Verify

**`server/tools/test_training_quality.py`, 39/39.** Server suite **1937/1937 across 36 suites**
(35 pre-existing at 1898, unchanged, plus this run's 39). `tests_render.html` **80/81 — the
same single pre-existing gap**, confirmed by name and text (the production-read-path check
needing a pasted session token). `tests.html` 51/51. The 62/63 gap from early runs is now
80/81 by count (group 10, run 5) but the SAME one red, unchanged again this run.

**Six faults, each detected, each reverted byte-identical, baseline rechecked after every
one:**

| Fault | Detected by |
|---|---|
| Q1 rework_later stops growing the backlog | test 38/39 ("grown by the deferral rate") |
| Q2 the forced-rework trigger disabled | test 37/39 (forced-resolved status, forcing notes) |
| Q3 accept_nonconforming stops spending credibility | test 38/39 ("credibility is spent") |
| Q4 accept_nonconforming stops recording closeout exposure | test 37/39 (exposure checks) |
| Q5 rework_now spends its own float pool instead of the shared counter | test 37/39 (competition checks) |
| Q6 `research_export.py` grows a `TrainingRun` reference | test 38/39 (isolation check) |

Q5 is the one that matters most: it directly attacks the competition claim, and the check
caught it precisely because it asserts on the SHARED counter rather than on quality's own
status.

**Minimum coverage from the brief, each with its own check(s) in the suite above:** deferring
rework raises the backlog value and, once forced, the eventual cost (REWORK LATER, THE BACKLOG
FORCES REWORK); the backlog forces rework at a period not chosen (same section, plus the
period-changes notes assertion); accepting nonconforming spends credibility and creates
permanent closeout exposure (ACCEPT NONCONFORMING); the quality and dispute threads draw on the
SAME float and contingency (COMPETITION); the new state is excluded from both export kinds
(ISOLATION — `research_export.py` never references `TrainingRun` at all, so the `quality` key
inside the JSON state column was never reachable by either export path; verified further by a
grep-backed source check plus a fault that adds a stray reference and confirms it is caught).

**Isolation, stated plainly.** `research_export.py` contains zero references to `TrainingRun`
or its `state` column — this was true before this run and remains true; the quality dict added
to that JSON blob was never a new isolation surface, it inherited run 1's guarantee by
construction. `signal_inputs_from_state` was not touched: quality moves `ac`, `float_consumed_
days`, `contingency_remaining` and `owner_credibility`, all of which the merge already projects
through the normal path; no new `SIGNAL_INPUT_KEYS` entry was needed or added, so the "signals
compute through the platform's own path" constraint required no new plumbing to hold.

**Browser drive, one full run, both (in fact three) threads live at once.** Played from period 1
through completion: the dispute open from period 1, the differing site condition opening at
period 5 (unchanged from run 4), and quality opening at period 6 — all three live simultaneously
for one period. At period 6 the figures panel read `QUALITY resolved, backlog $48,000` after
choosing `Rework now`, matching `$12,000,000 × 0.004` exactly; the dispute and site condition
had both already escalated with entitlement lost (the trainee deferred long enough to run both
notice windows out, which is a real outcome, not a bug — the same run's debrief states it
plainly: "the change: escalated, entitlement lost", "the site condition: escalated, entitlement
lost", "the failed inspection: resolved"). The Google SSO script request was aborted before
navigation, as in every prior run; no compositing tool was used, and the DOM read is structure
plus text only.

## Not touched, and why

`build_recommendation` was left unmodified. The brief's two required properties (competition,
lifecycle) do not require the recommendation surface to reason about quality, and adding a
fourth matter type to that ~180-line function was more scope than the budget below supports
cleanly. This is a real gap for a trainee mid-run — the recommendation panel has nothing to say
about an open defect — and it should be picked up either in a small follow-up or folded into
run 4's composition work, which already touches the debrief end of the same concern (the
"what was traded against what" cross-area statement run 4 adds is a natural place for the
first mention of quality's exposure, if the recommendation itself stays out of scope).

## Session usage against the half-session target

This run took close to a full session, not half. The design and engine work (constants,
state field, two decision-branch groups, two discrete triggers, `allowed_decisions`,
`training.py` wiring, debrief wiring, JS rendering) was the smaller half; verification
(fault injection against a real running suite, six faults each reverted and rechecked,
plus a real browser drive requiring bootstrapping an operational account and a session token
by hand since no existing fixture does this for training) was the larger half and is where the
overrun happened. **Say so plainly, per instruction, rather than push through: the pattern
itself is not too heavy — the wiring across five files (engine, `training.py`, debrief, JS,
tests) is what a "secondary thread" costs structurally, and that cost is fixed per thread type,
not per run. What is heavier than assumed is the VERIFICATION cost per thread, particularly
standing up a live browser session against a bootstrapped account by hand.** Run 2 (resources)
should budget for that fixed verification cost explicitly rather than assume run 1's 50% holds;
the roadmap's own "80%" figure for runs 2 to 4 already assumes this, which is the right call.

## Updated

`training_pmp_upgrade_roadmap.md` (run 1 marked DONE, the `dsc`-verb-reuse-versus-own-verb
finding carried forward for run 2) and `T6_HANDOFF.md` (new top section).
