# Training mode, run 4: regimes across the run, the debrief, the disclaimer

2026-08-04. The last run of the training build; training mode is feature complete. Branched
from `origin/main` at `3e8b2fb` with runs 1 to 3 all merged (#207, #208, #209). No new
migration. **Production remains unmigrated: 0018 (`projects.is_training`) and 0019
(`training_runs`) are both still unapplied there and must run before the first training run
starts.**

## The four traps: which are reachable, and why

**All four are reachable.** Each fires with its own clause citation and a different failure,
and each is fault-proven (a fault that disables the trap turns its check red).

**Trap 1 — 21 days applied to a differing site condition under A201, where it is 14:
REACHABLE, by construction of the geometry.** A second discrete matter, a differing site
condition, is discovered on day 3 of period five — 17 days old at that period's decision. 17
is inside A201's 21 day claim window and outside its 14 day site-conditions window (Section
3.7.4), so this is the one decision point in the run where believing 21 applies and being
wrong are different states. A trainee who escalates there on the 21-day belief is told the
site condition's own period governed and had already run, with the note saying explicitly that
Section 15.1.3.1's 21 days does not apply to site conditions. The site condition has its own
clock surface (`dsc_position`, its own notice line on the screen), separate from the claim's,
because conflating the two clocks is the mistake the trap teaches. Under A201 this condition
is unpreservable at this geometry — deliberately: the deadline ran before the first review,
which is the file's own warning about the 2017 edition shortening it from 21.

**Trap 2 — ConsensusDocs notice given, then no documentation within 21 days: REACHABLE, at
period grain.** A 30 day period has no decision point inside the 21 day documentation window,
so the second step is modelled at the grain the run has: an in-window escalation gives notice
(step one) and holds the recovery **conditional**; the following period's decision is the
documentation window, and **deferring it is going quiet** — the claim dies with the Section
8.4 citation. Any active decision keeps the file moving and the documentation lands, booking
the change order one period later than A201's one-step path, which is itself the price of the
two-step clock made visible. The abstraction (documentation rides the next period's activity
rather than a day-counted filing) is a designed simplification, stated here for correction.

**Trap 3 — a federal change worked for weeks before notice, recovering only 20 days back:
REACHABLE, since run 2, now compounded by growth.** The FAR lookback (52.243-4(d)) was built
in run 2. Run 4 adds what makes it bite harder: a deferred federal claim GROWS at 0.25% of
contract value per deferred period (work continues under the change), so the late notice
reaches half of a larger number — on the default contract, 210,000 grown, 105,000 recoverable.
Nothing is barred; the money is simply gone.

**Trap 4 — a claim that grows past $100,000 during preparation and is submitted uncertified:
REACHABLE, when the contract value puts the claim near the threshold.** On a contract under
about $6.67M the claim starts under $100,000 (1.5% of value). One deferred period grows it
across the threshold; escalating **immediately after the crossing** submits the form prepared
before it grew — uncertified, and an uncertified claim over the threshold is not a claim at
all (FAR 52.233-1, 41 USC 7103): entitlement lost, with that citation in the note. The trap is
the CROSSING, not the amount: wait a further period and the team knows the size and carries
the certification; start over the threshold and it was always carried. On the default $12M
contract the claim starts at $180,000, already over, so trap 4 needs the smaller contract —
the start form's contract value field is how a run reaches it.

**Form choice now changes the whole run, not just the notice check**: the same immediate
escalation books at once under A201 but goes conditional under ConsensusDocs; the same late
escalation is barred under A201 and ConsensusDocs but preserved-and-halved under FAR; the same
site condition is dead on arrival under A201, preserved-if-immediate under ConsensusDocs
(Section 3.16.2's stop-and-prompt duty), and preserved-if-undisturbed under FAR (52.236-2(a) —
a period of continued work disturbs the conditions and the entitlement is gone). The A201
service rule (Article 15 claims by certified or registered mail or courier with proof of
delivery, not email) and the IDM/60-day waiver are stated in the brief; they are content, not
mechanics, this run — noted as the remaining A201 texture if a run 5 ever exists.

## Part 2: the debrief

`trainingdebrief`, complete runs only (mid-run it is refused with the reason — a running
commentary would be the narrator judging). Deterministic, engine-computed, no model call:

- **What was spent**: float, contingency, cost over earned, credibility, LD exposure, cpi/spi.
- **What closed**: each matter (the change, the site condition) with status, entitlement, and
  any recovered amount.
- **The why, per incident**: an incident with `cause: "acceleration"` is attributed in words —
  "acceleration raises the chance of an incident, and this one is its consequence, not bad
  luck" — read from the cause the engine recorded when it fired, not reconstructed. A
  scheduled incident is honestly NOT attributed to the trainee; what their decisions set is
  what it cost.
- **The counterfactual**: the SAME pure engine replays the run from the same initial state
  with the first decision replaced by escalate and every later decision verbatim. Where the
  replay cannot proceed honestly it says so instead of estimating: the trainee escalated first
  ("the counterfactual is the run you played"), or the replayed world diverges structurally (a
  response landing where the replay has no stop work order) — reported with the reason,
  **never estimated across**. Fault R6 made the divergence path return an estimated position
  instead; the check went red.

The debrief's raw material was all captured by runs 2 and 3 (incident causes, decisions,
per-period changes); run 4 is a read plus one replay.

## Part 3: the disclaimer

`build_disclaimer(contract_form)`, carried in the brief (so it reaches the trainee before
period one) and in the debrief. It states: the governing form and jurisdiction; that contract
periods are routinely amended in negotiation so a real project may not match its own form, and
that the first move on any real project is to check which rules actually govern; which figures
are **sourced** (the notice periods, citations, certification threshold and lookback, per
`training_us_contract_regimes.md`) and which are **designed** (the decision effects and drift,
the escalation curve, the credibility mechanics, the LD band and facility rates, the
acceleration and productivity figures, the event schedule). **No liability or consent language
was composed** — asserted mechanically: the disclaimer text contains none of those words, and
the platform's approved notice text stands unchanged elsewhere.

## Part 4: roadmap item 14 — outstanding, not attempted

`training_us_contract_regimes.md` records that the FAR and Contract Disputes Act figures came
from primary sources (acquisition.gov, eCFR, 41 USC) and that the A201 and ConsensusDocs
periods came from law firm summaries, **not the licensed documents. That verification remains
outstanding and was not attempted in this run**, per instruction. Until it is done, the A201
21/14/60 figures and the ConsensusDocs 14/21 figures carried by the engine rest on secondary
sources. Item 14 stays OPEN on the roadmap, marked as Lin's.

## Verify

**`server/tools/test_training_regimes.py`, 45 checks, all green**: the same late escalation
under three forms yields three different fates; all four traps fire with their citations, and
their inverses hold (in-window, active-after-notice, certified-when-known, undisturbed); the
site condition's three form-specific duties; the debrief's acceleration attribution and its
honest non-attribution of the scheduled incident; the computable counterfactual (preserved
claim, 180,000 recovered, against the played run's lost entitlement, with genuinely different
positions), the escalate-first case, and the structurally-divergent case reported unavailable;
the disclaimer's content and its absence of composed liability language; and the HTTP surface
(gated, complete-only, hazard still redacted).

**Six faults injected (R1–R6), all detected with distinct signatures, all reverted
byte-identical (diffed), baseline 45/45 after every one:**

| Fault | Injected into | Result |
|---|---|---|
| R1 the A201 DSC window quietly becomes 21 days | training_engine.py | 43/45, both trap 1 checks |
| R2 notice-then-quiet no longer loses the ConsensusDocs claim | training_engine.py | 44/45, trap 2 |
| R3 the FAR claim stops growing | training_engine.py | 41/45, traps 3 and 4 plus both growth assertions |
| R4 certification stops being checked | training_engine.py | 44/45, trap 4 |
| R5 the debrief stops attributing acceleration incidents | training_debrief.py | 44/45, the attribution check |
| R6 a diverging replay returns an estimate instead of refusing | training_debrief.py | 44/45 — after the check itself was hardened; see below |

**Two defects in my own suite were found during verification, the pattern runs 2 and 3 also
hit.** First, a fixture sequence that assumed the acceleration-triggered stop work order fires
at period five (it fires at six, after the restart shadow clears) crashed the suite. Second,
fault R6 initially killed the suite with a KeyError and **no RESULT line** — the
crash-not-fail mode the brief lists — because the check indexed a key the faulted code no
longer produced; it now uses `.get` and the same fault reads as a clean red. Separately, one
check's premise was corrected: the accelerated run's counterfactual IS honestly computable
(the SWO schedule is unchanged by swapping the first decision), so the check asserts
availability rather than assuming unavailability.

**Suites reconciled**: one run-2 check updated for FAR growth (90,000 → 105,000 recoverable,
the grown claim halved). **Full server suite: 1833/1833 across 34 suites** (fresh SQLite
through migration 0019). **`tests_render.html` 62/63 — still exactly the same single
pre-existing gap** (the "production read path" check needing a pasted session token, same name
and text). **`tests.html` 51/51.**

**One full run per contract form driven in a real browser**, each to completion: A201 showing
"11 days remaining of 21 (Section 15.1.3.1)" and the site condition's "17 days against a 14
day period (Section 3.7.4)"; ConsensusDocs showing "4 days remaining of 14 (Section 8.4)" and
the Section 3.16.2 prompt-notice line; FAR showing "No fixed notice bar" with the recoverable
fraction and the 52.236-2(a) undisturbed line — the deadlines differing exactly as the table
says — and each run ending in the rendered debrief with the counterfactual. (One environment
note: the Google SSO script `accounts.google.com/gsi/client` is parser-blocking and this
container's proxy now blackholes it, holding DOMContentLoaded forever; the browser drives
abort that request. Password sign-in does not use it. Worth knowing for any future DOM drive
here.)

## The roadmap, now the build is complete

Items 4–13 and 15 are DONE. What remains open:

- **Items 1–3 (Lin's decisions)**: the elicited figures, the state variables, the decisions a
  trainee should get wrong. The build embodies designed stand-ins for all three, led with in
  the run 3 and run 4 reports for correction; the items stay formally open until Lin blesses
  or replaces the figures.
- **Item 14 (Lin's verification)**: A201 and ConsensusDocs periods against the licensed
  documents, outstanding as above.
- **Items 16–18 (deferred deliberately)**: international regimes, document generation,
  authored branching content — unchanged.
- **Production migrations 0018 and 0019**, before the first training run.

Server 1833/1833 across 34 suites. `tests_render.html` 62/63 (the same single pre-existing
gap). `tests.html` 51/51. Six faults, all detected, all reverted byte-identical, baseline
re-run green after each. `server/app/simulation/` untouched. Training mode is feature
complete.
