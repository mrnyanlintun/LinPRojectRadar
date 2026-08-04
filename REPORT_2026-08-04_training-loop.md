# Training mode, run 2: the loop

2026-08-04. Builds on run 1 (branch `claude/training-mode-gating`, PR #207, unmerged at the time
of writing — this run's branch stacks on it). `training_us_contract_regimes.md` did not exist in
the repository, any branch, git history, or disk; Lin supplied it directly and it is committed
verbatim. **Production has NOT been migrated: neither 0019 (this run's `training_runs`) nor 0018
(run 1's `projects.is_training`) has been applied there.** Both were written and run against
throwaway SQLite only, and both must be applied before the first training run starts.

Out of scope, per the brief: discrete safety events, model narration, the debrief (runs 3–4).
`trainingadvance` remains gate-listed but unimplemented — decide-and-advance is one act
(`trainingdecision`), and a separate advance without a decision has no meaning in this design.

## The effect table, first

Implemented in `training_engine.py` as data plus one pure function (`advance`). Deterministic:
the same decision under the same conditions produces the same state change, proven byte-for-byte
at the engine and over real HTTP with two accounts running identical runs.

| Decision | Float | Contingency | Actual cost | Owner credibility | Dispute and clock |
|---|---|---|---|---|---|
| **Escalate** | minus `escalate_float_days` (8 exacting, 6 steady) | unchanged | plus 0.2% of contract value (claim preparation) | minus 1 (floor 1) | Notice served; entitlement decided by the form's window against days since the event |
| **Absorb** | unchanged | minus the impact cost (1.5% of contract value) | plus the impact cost (the work is done anyway) | plus 1 (cap 5) | Dispute closed, entitlement waived |
| **Defer** | minus `defer_drift_float_days` (3 exacting, 2 steady) | unchanged | plus 0.3% of contract value (unmanaged change drift) | unchanged | Clock runs 30 more days; the drift repeats every deferred period |

Supporting rules, all in `training_engine.py` constants:

- **Earned value**: a period earns one tenth of contract value; a period spent with the dispute
  open and deferred earns 90% of that, and the lost earning is never recovered. cpi and spi are
  always **derived** (ev/ac, ev/pv, three decimal places, the merge's own rounding) — never set
  directly, so the state and the signals cannot disagree about a ratio.
- **Resolution of a preserved escalation**: booked the **next** period as a change order —
  contract value and revised contract sum rise by the recoverable amount, change order count
  increments, contingency untouched. Recoverable = the estimated impact, times the FAR lookback
  fraction where that form applies, times `low_credibility_recovery_factor` (0.85 exacting, 0.95
  steady) when owner credibility was **2 or less before the escalation's own minus one**. That
  last clause was a bug my own suite caught: the first implementation applied the escalation's
  own credibility penalty to the claim it was carrying, so every first escalation was docked 15%.
  Credibility at the moment of escalation means the standing earned by prior conduct.
- **Drift stops when the dispute closes**: after escalation or absorption, deferral is the
  neutral close of a period (nothing spent). Drift is a property of the unmanaged change, not of
  time itself.
- **Liquidated damages follow float mechanically**: days over total float × LD per day. With 12
  days of total float, the exhausting sequence is defer, defer, escalate (3+3+8 = 14): two days
  over, and that same sequence arrives with the notice window already spent — exposure and no
  recovery, the compounding `training_us_contract_regimes.md`'s chain describes.
- A decision recorded after the dispute has closed changes nothing but the record; the screen
  says there is nothing left to decide rather than refusing the period.

## The liquidated damages derivation rule

**LD per day = 0.05 percent of contract value (five basis points), rounded to the nearest 500
dollars.** $12M → $6,000/day; $50M → $25,000/day. Deterministic, stated in the brief, one
constant pair (`LD_RATE`, `LD_ROUND`). The coefficient is a designed figure with no external
authority, chosen so daily exposure scales with the value at risk; it is one of the figures this
report exists for Lin to correct.

Other designed scaling: impact cost 1.5% of contract value; contingency 5%; total float 12 days
of a 300-day, 10-period schedule; contract value clamped to $1M–$500M (default $12M).

## Part 1: the brief

`build_brief` is a pure projection returned by **every** state response, so the brief is
reachable at any point in the run (verified in the browser: hide, re-show, mid-run). It carries:

1. **The form and its periods**, per `training_us_contract_regimes.md`, not overridable: A201
   21 days (Section 15.1.3.1, with the certified-mail service note); ConsensusDocs 14 days then
   documentation within 21 (Section 8.4 — the two-step clock is stated; step two becomes
   mechanical with run 3's discrete events); FAR no bar but the 20-day cost lookback
   (FAR 52.243-4(d)) plus the $100,000 certification note. Clause numbers cited, no clause text
   reproduced, per the file's copyright note. The file's own caveat stands: A201 and
   ConsensusDocs figures are from law-firm summaries, unverified against the licensed documents
   (roadmap item 14, still open).
2. **The LD figure and its rule**, above.
3. **Site and market conditions**: two profiles, `exacting` (tight labour, long-lead exposure,
   formal owner) and `steady`. Each states labour, procurement and owner disposition in words
   plus the acceleration multiplier and restart productivity loss. Those two figures are stated
   but not yet mechanical — they price recovery from stoppages, which are run 3. The mechanical
   figures this run are `escalate_float_days`, `defer_drift_float_days` and
   `low_credibility_recovery_factor`.

The brief also carries a designed-figures note, so a trainee is told which numbers are training
design and which follow from the contract form.

## Part 2: the state, and the two clocks

`training_runs` (migration 0019): one row per run — contract form, value, conditions, current
`state` JSON, full `history` JSON, status. Beside the observations store, never inside it; the
run's analytical outputs go to `computed_results` through the normal path like any project's.

The state holds cost performance (as ev/ac/pv, ratios derived), float (total/consumed),
contingency (original/remaining), the open dispute with its entitlement, **the notice clock in
days**, and owner credibility (1–5, start 3).

**The two axes do not blur.** The event lands on day 10 of period one; the trainee decides on
day 20 of every period. So the first decision is 10 days after the event, and each deferral adds
30 days to the notice clock while advancing one period. Under A201 (21 days) or ConsensusDocs
(14), one deferral spends the window even though only one period passed — asserted directly, and
the notice position is **derived** from days-since-event per form (`notice_position`), never
stored, so the clock and the state cannot disagree.

## Part 3: period generation through the normal path

`signal_inputs_from_state` projects the state into the merge's own vocabulary: every one of the
76 `SIGNAL_INPUT_KEYS` present in the merge's own order, None where the state genuinely knows
nothing (docRiskScore, quality, RFI ledgers — no documents exist, so those signals **abstain**,
verified). Then the shared tail runs: `_compute_and_store`'s computation-and-storage half was
extracted into `documents.run_and_store`, and **both** the document path and the training path
call that one function — `compute_project`, the cutoff-aligned portfolio snapshot, and the
`ComputedResult` row are literally the same code. There is no training-only computation path to
drift; nothing under `server/app/simulation/` was touched. `source_documents` is stored as an
empty list — no document produced a training period, and inventing provenance would be worse
than stating none.

**A boundary this exposed, closed in both directions.** The portfolio snapshot in
`run_and_store` selects every live result at or before the cutoff — once training results exist,
a real project's stored snapshot would have ingested training vectors, and a training run's
would have ingested real ones. A vector is now included only when its project's `is_training`
matches the project being computed. Proven able to fail with a real project's live result
planted in the fixture: removing the filter flipped a training compute's `portfolio_size` from
insufficient to 2 and a real compute's from insufficient to 3, and both checks went red.

## Parts 4 and 5: the screen and the loop

`assets/js/training.js` renders the run: the brief (toggleable, always reachable), the notice
clock (with tight and expired stylings), the PM's figures (cost and schedule performance, float,
contingency, credibility, LD exposure, dispute position), **the platform's own signals** —
project status and category statuses by group name, from the stored result via `_result_view`
with module-level recommended actions included (there is no researcher-authored package in
training, and the reveal gate protects a research pre-judgment, which a training run does not
have) — the three decision buttons carrying the three tensions verbatim, and the decision log.
Category and group appear by **name**; no module ids, no em dashes (the platform's own module
`evidence_metric` strings pass through unmodified, as they do on every other surface).

Actions: `trainingstart` (form, conditions, value → project with `is_training` at creation, PM
membership row, run row, period one computed, one transaction), `trainingstate` (read),
`trainingdecision` (advance by the effect table, compute the next period, return the new view).
Ownership is enforced: another account's run_id answers "not found", indistinguishable from
absent. Ten decisions complete a run; an eleventh is refused with the reason.

## Verify

**`server/tools/test_training_loop.py`, 54 checks, all green.** The brief's required coverage:

- **Determinism**: `advance` twice from the same state is byte-identical (the engine itself, not
  a copy), and two accounts running identical runs over real HTTP reach byte-identical state.
- **The clocks**: one deferral advances one period but 30 clock days; the A201 window closes;
  escalating after closure recovers nothing.
- **The form changes the clock**: A201 21 days (11 remaining at first decision), ConsensusDocs
  14 (4 remaining), FAR no bar but recoverable fraction 0.5 after one deferral — with the FAR
  deferral explicitly NOT marking entitlement lost, unlike A201.
- **The effect table, cell by cell**, including the steady-vs-exacting modulation (6 vs 8 float
  days for the same decision), the change order booked the following period, and the LD chain.
- **The normal path**: one `ComputedResult` per period, real `simulation_version`, empty
  `source_documents`, docRiskScore abstaining, a fused project status.
- **Run 1's isolation still holds** now that training `ComputedResult` rows exist:
  `project_health` excludes them (and the check still proves it can fail by unmark/remark); a
  training project still cannot become research evidence; a research account is still refused;
  and the new portfolio boundary holds in both directions.

**Seven faults injected, all detected with distinct signatures, all reverted byte-identical
(diffed), baseline 54/54 re-run after every single one:**

| Fault | Injected into | Result |
|---|---|---|
| F1 run marker stamped into state at decision time | training.py | 53/54, the HTTP determinism check |
| F2 defer stops running the notice clock | training_engine.py | 47/54, seven clock and FAR checks |
| F3 A201's window quietly becomes 14 days | training_engine.py | 51/54, the form checks |
| F4 portfolio training boundary removed | documents.py | 52/54, both boundary directions, with portfolio_size as evidence |
| F5 period generation severed from the normal path | training.py | 45/54 — see below |
| F6 the credibility ordering bug reintroduced | training_engine.py | 51/54, the recoverable-amount checks |
| F7 run 1's export isolation filter removed | research_export.py | 53/54, the project_health check |

**Two defects in my own work were found and fixed during verification, which is what it is
for.** First, the engine bug F6 re-injects: the suite caught it on its first run (a first
escalation was docked 15% by its own credibility penalty). Second, fault F5 initially made the
suite **crash with no RESULT line** — an IndexError on a missing row, exactly the failure mode
the brief lists — and a first version of the portfolio check read a snapshot key that does not
exist, so it could never fail. Both were rewritten (guarded reds instead of a crash;
`insufficient_data`/`portfolio_size` assertions with a planted real vector) and F4/F5 were
re-run against the corrected suite.

**Full server suite: 1746/1746 across 32 suites** (fresh SQLite, `alembic upgrade head` through
0019). **`tests_render.html` 62/63 — the one red is still exactly run 1's pre-existing gap**
(the "production read path" check that needs a session token pasted into that tab; same name,
same expected/actual text). **`tests.html` 51/51.**

**One full run driven in a real browser** (Chromium/Playwright): sign in, Train tab, start form
(A201, exacting), brief rendered with form, 21-day period, $6,000/day LD and conditions; period
1 Green, float 12 of 12, notice 11 of 21 remaining; brief hidden and re-shown mid-run; escalate;
period 2 renders with float 4 of 12, credibility 2 of 5, dispute escalated with entitlement
preserved, contingency untouched at $600,000, and the decision log showing period 1: escalate —
each figure exactly what the effect table says.

## Things worth knowing before run 3

- **The elicited layer (roadmap items 1–3) is now partially embodied** in the two condition
  profiles and the designed constants. Items 1–3 remain formally OPEN — the figures here are
  placeholders of mine for Lin to correct, which is why the report leads with them.
- **Acceleration and restart figures are stated in the brief but mechanically inert** until
  discrete stoppages exist. The profile carries them so run 3 does not need a brief change.
- **ConsensusDocs' documentation step (21 days after notice) is stated, not mechanical.** Run 3's
  discrete events are the natural place to make going-quiet-after-notice lose the claim.
- **`trainingadvance` is still gate-listed and unimplemented**; posting it answers "Unknown POST
  action" after passing the gate. Harmless, reserved.
- **The state view returns the full state dict**, including `pending_recovery` before it books.
  Fine for training (nothing is blinded), but worth remembering if run 3 adds anything a trainee
  should not see coming: the discrete event schedule must NOT travel in `trainingstate`.
- **`run_and_store` is now a public seam in documents.py.** Anything else that can produce
  signalInputs without documents should use it rather than growing a third tail.

Server 1746/1746 across 32 suites. `tests_render.html` 62/63 (the same single pre-existing gap
as run 1, confirmed to be that one). `tests.html` 51/51. Seven faults, all detected, all
reverted byte-identical, baseline re-run green after each. `server/app/simulation/` untouched.
Production not migrated: 0018 and 0019 both pending there.
