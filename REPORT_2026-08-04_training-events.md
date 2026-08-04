# Training mode, run 3: effect table corrections, discrete events, narration

2026-08-04. Stacked on runs 1 and 2 (`origin/main` still at `a6d588b`; PRs #207 and #208 were
both open and unmerged at branch time, so this branch continues from `claude/training-loop`).
**Production remains unmigrated: 0018 and 0019 are both still unapplied there.** Run 3 adds no
migration — everything new lives in engine state JSON the existing `training_runs` table
already holds.

## The revised effect table, first

| Decision | Float | Contingency | Actual cost | Owner credibility | Dispute, clock, hazard |
|---|---|---|---|---|---|
| **Escalate** | minus (base + 2 per full period the position was left open), cap 12; base 4 exacting, 3 steady | unchanged | plus 0.2% of value | minus 1 (floor 1), and earn progress resets to 0 | Notice served; entitlement per the form's window |
| **Absorb** | unchanged | minus impact cost (1.5% of value) | plus impact cost | plus ONE PROGRESS STEP; two steps earn one point | Dispute closed, entitlement waived |
| **Defer** | minus drift (3 exacting, 2 steady) | unchanged | plus 0.3% of value drift | unchanged | Clock +30 days; drift repeats while the dispute stays open |
| **Accelerate** | RECOVERS 4 days | unchanged | plus 1.0% of value times the profile multiplier (1.5/1.25) | unchanged | Hazard +0.5; at 1.0 a second near miss fires the following period. An open dispute still ages +30 days |
| **Respond strong** (during SWO) | minus days lost: 6 exacting, 5 steady | unchanged | plus 0.8% of value | unchanged | SWO lifts; restart shadow 1 period at reduced earning. An open dispute still ages |
| **Respond minimal** (during SWO) | minus days lost: 18 exacting, 14 steady | unchanged | plus 0.2% of value | unchanged | Lifts late; restart shadow 2 periods |

Unchanged and deliberately so: **the FAR path halving recoverable money where A201 and
ConsensusDocs bar the claim** — untouched, per the instruction; resolution of a preserved
escalation (next-period change order, lookback fraction, low-credibility factor read from the
standing BEFORE the escalation's own penalty); earned value derivation (factors now multiply:
a deferred-dispute period earns 90%, a restart period earns 1 − restart loss).

### The four corrections, and one premise corrected back

**1. Deferral was already not free — the premise was half wrong, and the missing half was
visibility.** Run 2's defer already cost 3 float days (exacting) and 0.3% of value per deferred
period; the report and handoff recorded it. What did not exist is what the correction actually
asks for: the drift was invisible in the period's figures — a trainee saw totals move, not what
moved them. Run 3 adds `period_changes` to the state: every advance states its decision, float
days spent, cost added, contingency drawn, credibility change, and plain-language notes
("Deferral drift: 3 float days and 0.3 percent of contract value while the dispute stays open.
Waiting has a price before the cliff."), rendered as "What the last period cost" on the screen.
The drift figures themselves stand as run 2 set them, for correction rather than re-invention.

**2. The escalation curve.** `float cost = base + 2 × full periods the position has been open,
capped at 12`; base 4 exacting / 3 steady (down from run 2's flat 8/6, so an immediate,
well-documented escalation is now genuinely cheap). Periods open is derived from the notice
clock itself, so the cost and the clock cannot disagree. Escalate at once: 4 days. After one
deferred period: 6. After two: 8. The screen's note states the position's age with the cost.

**3. Credibility asymmetry.** Losing stays instant: one escalation, minus one point, and it
also resets earn progress to zero. Earning is stepped: one concession is one progress step, and
`CRED_EARN_CONCESSIONS = 2` steps convert to one point. Two concessions to build what one
escalation spends. (With this run's single standing dispute a second concession only arises
through later events; the reset-on-escalation property is exercised on the pure function with
progress pre-set, stated as a constructed input, because the application cannot yet produce
that sequence — run 4's events will.)

**4. The LD rate follows the brief.** `facility` is a third start condition: `critical` 0.05%,
`standard` 0.035% (the new default), `utilitarian` 0.02% — the common band's ends. Derivation
from contract value and the $500 rounding unchanged. On $12M: $6,000 / $4,000 / $2,500 per day.
The brief names the facility and states its rate and the band; the same decisions on the same
value now carry different exposure by facility alone (asserted: 14 float days consumed costs
$12,000 on a critical facility and $5,000 on a utilitarian one).

## The event constants, second

All designed figures, one table (`EVENT_FIGURES` in `training_engine.py`), marked as elicited:

| Constant | Value | Meaning |
|---|---|---|
| `near_miss_period` | 4 | The exogenous near miss: scheduled by the run's geometry, fires once, never disclosed in advance |
| `swo_conversion` | 1.0 | Every near miss becomes a stop work order this run (designed; the machinery takes a lower rate without change) |
| `incident_direct_cost_rate` | 0.001 | The incident itself costs little (0.1% of value); the days are the mechanism |
| `acceleration_hazard_per_use` | 0.5 | Each accelerated period adds this to the hazard |
| `hazard_threshold` | 1.0 | At the threshold a second near miss fires the following period, cause recorded as "acceleration" |
| `acceleration_float_recovered_days` | 4 | What accelerating buys back |
| `acceleration_cost_rate` | 0.01 | Times the profile multiplier: 1.5% exacting, 1.25% steady |
| `respond_strong` | 6/5 days lost, 0.8% cost, 1 restart period | The full correction package at once |
| `respond_minimal` | 18/14 days lost, 0.2% cost, 2 restart periods | The least each round; stopped longer, longer shadow |

Design points, mapped to the brief:

- **The SWO is the mechanism.** Direct incident cost is $12,000 on $12M; the days (6 vs 18) are
  where the money and schedule go, through float and the LD rate.
- **Duration follows the response.** During a stoppage the ONLY decision offered is the
  response (`allowed_decisions`), per the DOB regime's shape: lifting requires the Certificate
  of Correction plus what the cause demands, and how completely it is assembled decides the
  duration. A standard decision during an SWO is refused with the reason; so is a response with
  no SWO.
- **Severity depends on state the trainee influenced.** Asserted head to head: the same
  period-4 incident with the same minimal response lands 6 days over float on a run that
  absorbed early ($24,000 exposure) and 20 days over on one that spent its float on the dispute
  ($80,000). Same event, different consequence, because of earlier decisions.
- **Acceleration raises the hazard, attributably and deterministically.** Two accelerated
  periods guarantee a second stop work order, recorded with `cause: "acceleration"` in the
  incident history the debrief will read; a run that never accelerated can never meet one, so
  the attribution cannot be wrong. Deterministic on purpose (same decisions, same incidents) —
  the platform's replay-determinism contract holds, and "bad luck" is structurally excluded.
- **The hazard accumulator is redacted from every response**: at the threshold it would
  forecast the next incident. Same reasoning as run 2's rule about the event schedule.
- **A stoppage or an accelerated period does not pause the notice clock**: an open dispute ages
  +30 days through either, because the correction package (or the compressed site) consumed the
  attention the notice needed. Stated in the table.

## Narration

`training_narration.py`: one call narrates a state the engine has already computed. The prompt
is narrate-only — no evaluation, no prediction, no invented figures — and the structural
guarantee is stronger than the prompt: **nothing reads the narration back.** `training_engine`
never imports the narrator; the sentence goes to the screen and nowhere else. Verified end to
end: the same decisions with narration disabled and with a stub installed produce byte-identical
state, differing only in the sentence.

**A layer, not a dependency**: no API key → None → the run continues on the figures (this
container has no key, so that path is the one every test exercises); a narrator that *raises*
is swallowed by `_narrate`'s guard and the decision still lands (fault E7 removes the guard and
the check goes red). Transport reuses the extraction client's endpoint and version header, on
the fast model tier — a mediocre sentence costs nothing, unlike a wrong extracted figure. Em
dashes are stripped from model output mechanically, since a prompt instruction is a request and
the naming authority's ban is a rule. The narration payload carries only the figures a narrator
needs — hazard and anything that forecasts an event stays out.

## Verify

**`server/tools/test_training_events.py`, 42 checks, all green**, covering the brief's minimum:
deferral costs before the window closes (and is stated in `period_changes`); escalating early
(4 days) costs less than late (6, then 8) for the same position; one concession earns a step,
not a point, and an escalation resets progress; the LD rate follows the facility in the brief,
the derivation, and the exposure; the same incident and response cost $24,000 on a float-rich
state and $80,000 on a float-poor one; and identical state transitions with narration disabled,
stubbed, and raising.

**Eight faults injected (E1–E8), all detected with distinct signatures, all reverted
byte-identical (diffed), baseline 42/42 after every single one:**

| Fault | Injected into | Result |
|---|---|---|
| E1 defer drift removed | training_engine.py | 36/42 — six reds, including the figures-vs-notes split: the note still claimed drift, the FIGURES check caught it |
| E2 escalation cost flat again | training_engine.py | 38/42, the curve checks |
| E3 absorb grants a full point directly | training_engine.py | 41/42, the asymmetry check |
| E4 LD rate ignores the facility | training_engine.py | 36/42, all four facility checks plus both severity figures |
| E5 minimal response costs the same days as strong | training_engine.py | 39/42, duration-follows-response and both severity checks |
| E6 acceleration stops raising the hazard | training_engine.py | 39/42, the attribution chain |
| E7 a narration failure propagates | training.py | 41/42, the raising-narrator check |
| E8 hazard leaks into the state view | training.py | 41/42, the redaction check |

**One defect found by the suite during its own construction**: the escalation-resets-progress
check was first written as absorb-then-escalate, a sequence this run's single dispute cannot
produce (absorbing closes it), so the check was green against the no-op branch — a fixture
building state by a route the application does not take, exactly the listed failure mode. It
now constructs the pure function's input directly and says so.

**Run 2's suite was reconciled to the corrected table** (flat-8 → curve base 4, credibility +1
→ progress step, LD 6,000 → facility-aware, and its run-out loop now decides from the server's
`allowed_decisions` since period 4 brings an SWO): **54/54**. Full server suite: **1788/1788
across 33 suites**, fresh SQLite through migration 0019.

**`tests_render.html` 62/63 — still exactly the same single pre-existing gap** (the
"production read path" check needing a pasted session token; same name, same expected/actual
text). **`tests.html` 51/51.**

**One full run driven in a real browser, including an incident**: utilitarian facility brief
stating "$2,500 per day" and "0.020 percent" (the band's low end); absorb showing contingency
drawn and credibility HELD at 3 of 5 (one concession is a step); two neutral defers; period 4
renders the stop work order panel (Certificate of Correction language) with respond
strong/minimal as the only buttons; the strong response lands float at 6 of 12 (exacting 6 days
lost), the restart panel shows the shadow, and "What the last period cost" states 6 float days
spent with "duration followed the response". Every figure per the tables.

## Things worth knowing before run 4

- **The debrief's raw material now exists**: `incidents` with causes, `decisions`,
  `period_changes` per advance, and full `history` on the run row. Run 4 reads; nothing needs
  new capture.
- **`swo_conversion` is 1.0 but not wired as a probability** — it documents the designed rate.
  Making it fractional needs a deterministic tie-breaker (state-derived, never random) to keep
  the replay contract.
- **ConsensusDocs' documentation step is still stated, not mechanical** (carried from run 2).
- **Narration is per decision/start response only** — `trainingstate` reads do not re-narrate,
  so a page refresh costs no model call; the screen keeps the last sentence in memory.
- The `accelerate` decision joined `GATED_ACTIONS`' vocabulary implicitly (it is a payload
  value of `trainingdecision`, not a new action) — nothing to gate.

Server 1788/1788 across 33 suites. `tests_render.html` 62/63 (the same single pre-existing
gap). `tests.html` 51/51. Eight faults, all detected, all reverted byte-identical, baseline
re-run green after each. `server/app/simulation/` untouched. Production not migrated: 0018 and
0019 both pending.
