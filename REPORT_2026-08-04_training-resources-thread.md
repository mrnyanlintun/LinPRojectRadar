# Training upgrade run 2: the resources thread, and the spacing rule

2026-08-04. Branched from `origin/main` at `fc7be2c`, with training mode runs 1 to 5 and PMP
upgrade run 1 (quality, #212) all merged. No migration; the two new state fields live on
`TrainingRun.state`'s existing JSON column. Nothing under `server/app/simulation/` modified.
**Production still lacks migrations 0018 and 0019 and must be migrated before the first real
training run.**

## The effect figures, DESIGNED, for correction

In `RESOURCE_FIGURES`, `server/app/training_engine.py`, beside `EVENT_FIGURES` and
`QUALITY_FIGURES`:

| Figure | Value | What it does |
|---|---|---|
| `adequacy_full` | 1.0 | full crews earn a full period |
| `shortage_adequacy` | 0.75 | what the shortage drops crews to on discovery |
| `adequacy_floor` | 0.40 | adequacy never falls below this |
| `pay_premium_cost_rate` | 0.012 (1.2% of contract value) | the premium, drawn from shared contingency first |
| `resequence_float_days` | 4 | float spent to reorder the work |
| `resequence_adequacy_recovery` | 0.15 | how much of the shortage reordering actually fills |
| `accept_delay_float_days` | 3 | float spent by accepting |
| `accept_delay_adequacy_decay` | 0.10 | how much deeper the shortage gets each time it is accepted |
| `low_adequacy_at_or_below` | 0.85 | at or below this the crews count as scarce |
| `accelerate_low_adequacy_cost_multiplier` | 1.8 | acceleration premium multiplier when scarce |
| `accelerate_low_adequacy_hazard_extra` | 0.25 | extra incident hazard when accelerating scarce |

On a $12,000,000 contract, read back from the DOM in a browser: the shortage opens at 75
percent productivity; accepting the delay costs 3 float days and drops crews to 65 percent;
paying the premium costs **$144,000**, drawn entirely from contingency ($600,000 to $456,000),
and returns crews to 100 percent.

## The spacing rule, since run 4 depends on it

Run 1 picked period 6 for the quality inspection **by hand**, after discovering it collided
with the scheduled near miss at period 4. With three threads and run 4 composing them, hand
picking is how two threads silently land on the same period and one is never seen. Openings are
now derived:

> Secondary threads open in declaration order, starting at `THREAD_OPENING_FIRST_PERIOD` (5),
> stepping by `THREAD_OPENING_MIN_GAP` (1), **skipping any period a discrete event already
> reserves** (today: `EVENT_FIGURES["near_miss_period"]`, period 4). A thread allocated later
> than `THREAD_OPENING_LAST_PERIOD` (`PERIODS_TOTAL - 3`, so 7) **raises rather than returning
> a period nobody can play out.**

`thread_opening_periods()` returns `{dsc: 5, quality: 6, resources: 7}`, and `DSC_PERIOD`,
`QUALITY_INSPECTION_PERIOD` and `RESOURCE_SHORTAGE_PERIOD` are all derived from it rather than
written down beside it. **The rule reproduces the two periods already in use rather than
renumbering them** — that is the property that makes it a rule and not a rewrite: run 4's
regimes work and run 1's quality work keep the exact geometry they were verified against.

**What run 4 needs to know, and it is a real constraint, not a detail.** With a 10 period run,
a first opening at 5 and three periods of play reserved after the last opening, the rule
supports **exactly three secondary threads**. A fourth is refused with a stated reason, and a
check proves the refusal fires. Run 4's roadmap entry wants "spine plus two secondary, or plus
three for a hard run" — **that is exactly at the ceiling, with nothing spare.** Composition
will pick *which* three from the pool of six thread types, which fits; but if run 4 ever wants
four live at once it must first change one of `PERIODS_TOTAL`, `THREAD_OPENING_FIRST_PERIOD`,
or the three-period play-out reserve, and the refusal will say so rather than quietly
overlapping two threads. That decision is yours, and it is better made deliberately in run 4
than discovered by a collision.

## The coupling: crew adequacy feeds the schedule engine

This is the structural difference from run 1 the brief asked to be reported. Quality's backlog
is a figure that costs money and float **when it is acted on**. Crew adequacy is a **multiplier
on earning**: it multiplies into the same `ev_factor` chain as the deferral penalty and the
restart productivity loss, so while it is low **every period earns less, whatever the trainee
spent that period doing.**

```python
ev_factor = DEFER_EV_FACTOR if disturbed else 1.0
if restarting: ev_factor *= (1.0 - profile["restart_productivity_loss"])
ev_factor *= crew_adequacy          # run 2's coupling, one line, applies to everything
```

Proven head to head on two states differing **only** in adequacy (a constructed input to a pure
function, stated as such in the suite, because no sequence of real decisions can isolate
adequacy — reaching a low value necessarily spends float or money on the way): a period spent
**escalating the claim**, **reworking the quality defect**, **absorbing the change**, or
**accelerating** each earns strictly less with crews short. The earning is exactly
`adequacy × full period`, so the coupling is the multiplier it claims to be and not an
unrelated penalty; and at full adequacy it multiplies by 1.0, so **a run that never meets the
shortage is untouched by this thread.**

Because the cost is taken out of earning rather than charged as a line item, it would read as
bad luck if nothing said so. Two places do: the period's own notes state the rate and that it
applies to all the work, and the debrief names the shortage and what the crews ended at.

**Acceleration is worse with scarce trades, on both axes.** The premium is multiplied by 1.8
(you are bidding for people who are already unavailable) and the incident hazard rises by a
further 0.25 (compressing work you are short handed for is how people get hurt). Both are
deterministic, so the debrief's attribution stays a read rather than a reconstruction, and the
period's notes state the interaction.

## Competition, on the same pools

`allowed_decisions` returns `DECISIONS + QUALITY_DECISIONS + RESOURCE_DECISIONS` while all
three are open — a ten verb menu, one decision per period. All three threads' actions move the
**same** `float_consumed_days`; absorbing a change and paying the trade premium draw on the
**same** `contingency_remaining`. Acting on one thread leaves the other two exactly where they
were, which for resources means still degrading every period. Run 1's fault 5 was repeated here
as **R3** (give the shortage its own budget pool) and was caught by the shared-pool checks.

## Verify

**`server/tools/test_training_resources.py`, 63/63.** Server suite **2000/2000 across 37
suites**, every file against a fresh database (shared-database contamination reads as failures,
per the brief). `tests_render.html` **80/81 — the same single pre-existing gap**, confirmed by
name and text: *"production read path: exercised against the server / a session token in this
tab / none: sign in to the application, then navigate this tab to /tests_render.html"*.
`tests.html` 51/51.

**Eight faults, each detected, each reverted byte-identical, baseline rechecked after every
one:**

| Fault | Detected by |
|---|---|
| R1 crew adequacy stops multiplying into `ev_factor` (the coupling itself) | 55/61 — six checks, across all four decision types |
| R2 acceleration no longer penalised when crews are scarce | 56/61 — cost, ratio, hazard, extra, notes |
| R3 the premium draws from its own budget instead of shared contingency | 59/61 — the shared-pool checks (run 1's fault 5, repeated) |
| R4 `accept_delay` stops compounding the shortage | 58/61 — deepening, second deepening, second period earns less |
| R5 the spacing rule stops reserving the near miss period | 55/60 — five checks; the count drops to 60 because the shortage opens a period earlier, so the pre-opening loop emits one fewer check |
| R6 `resequence` fully fills the shortage instead of partly | 59/61 — partial-fill and stays-open |
| R7 `research_export.py` grows a `TrainingRun` reference | 60/61 — the isolation check |
| R8 `resource_position` drops `resolution` again | 61/63 — the two closure-wording checks |

**Two defects of my own, both found by the campaign rather than by the suite's first version:**

1. **A wrong statement on screen, found by the browser drive.** `resource_position` omitted
   `resolution`, so the JS ternary that distinguishes the two closures always fell to its else
   branch: **a trainee who paid a premium was told they had resequenced the work.** The suite
   passed 61/61 while this was true, because every check asserted on state and none on how the
   closure was described. Fixed by carrying `resolution` on the position, and two checks now
   hold it. This is the run 5 lesson again in a new place: a check that asserts the mechanism
   does not assert the sentence.
2. **A check that crashed instead of failing.** The first version of that fix's check read
   `resource_position(paid)["resolution"]`, so injecting R8 raised `KeyError` and the suite
   died **printing no `RESULT:` line at all** — the failure mode that skims like a clean run,
   which the handoff records from the encoding problem. Rewritten with `.get()`; R8 then
   reported 61/63 properly.

**Minimum coverage from the brief**, each with its own checks: low adequacy slows productivity
across the whole run, not only the resource thread's own work (THE COUPLING, four decision
types); accelerating with low adequacy costs more than with high (ACCELERATION, plus the exact
multiplier and the hazard); paying premium holds the schedule and spends contingency from the
shared pool (PAY PREMIUM, including that the *next* period earns a full increment again); the
resource thread and the others draw on the same float (COMPETITION); the spacing rule prevents
collision with the near miss and with the quality opening (THE SPACING RULE).

**Isolation, by construction and not by a filter.** `research_export.py` contains zero
references to `TrainingRun`. `crew_adequacy` and the `resources` dict live inside the JSON
state column no export path reads, so they inherited the guarantee rather than needing a new
one. `signal_inputs_from_state` was **not** touched and no `SIGNAL_INPUT_KEYS` entry was added:
the shortage acts on the run through `ev`, which the merge already projects, so signals still
compute through the platform's own path with no training-only computation.

**Browser drive, one full run, all three secondary threads plus the spine live at once.** At
period 7 the screen carried the claim notice, the site condition notice, the failed inspection
and the trade shortage simultaneously, with a **ten verb** decision menu. Figures matched the
effect table exactly: crews at 75 percent; accept the delay → 3 float days, crews to 65
percent, note stating the compounding; pay the premium → $144,000, all from contingency
($600,000 → $456,000), crews to 100 percent. The Google SSO script request was aborted before
navigation; no compositing, DOM read is structure and text only.

## Not touched, and why

`build_recommendation` still says nothing about an open shortage or an open defect — the same
gap run 1 reported and deliberately left. It is now two threads wide rather than one, which
raises its priority: a trainee mid run gets a recommendation that reasons only about the claim
while three other matters compete for the same period. Still the right call for run 4's
composition work to absorb, but it should not slip past run 4.

## Session usage against the 80% target

**This run came in around the 80% target, and the reason is worth recording because it
contradicts what run 1 predicted.** Run 1 reported that verification, not wiring, was the
overrun, and that per-thread verification should be treated as a fixed cost that does not
shrink. Half of that held and half did not:

- **The wiring did shrink**, materially. Run 1 had to *invent* the thread pattern; run 2
  followed it, and the engine changes (constants, state field, position function, three
  decision branches, one trigger, the `ev_factor` line, the acceleration interaction) went in
  without redesign. The pattern paid for itself exactly as intended.
- **The verification did not shrink, and the browser drive is why.** Standing up a live
  operational account and session token by hand is still the single most expensive step, and it
  is still per-run. It also remains the step that *finds the most*: it caught the wrong-closure
  defect that 61 passing server checks did not.

Net: the spacing rule was extra scope this run carried that runs 3 and 4 will not, and it
roughly offset the wiring savings. **Runs 3 and 4 should budget the same 80%**, and should not
assume the browser drive gets cheaper — it should instead be made reusable. A small fixture
that bootstraps an operational training account and returns a session token would pay for
itself immediately across runs 3 and 4; I did not build it here because it is shared test
infrastructure and building it inside a thread task is how shared infrastructure ends up shaped
by one caller.

## Updated

`training_pmp_upgrade_roadmap.md` (run 2 marked DONE, the three-thread ceiling and the
recommendation gap carried forward to runs 3 and 4) and `T6_HANDOFF.md` (new top section).
