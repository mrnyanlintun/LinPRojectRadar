# Training Mode — Roadmap

Product, not praxis. Operational accounts only. Update the status marker after every run.

Status key: OPEN / RUNNING / DONE / BLOCKED

---

## Decisions, mine, before anything is built

1. OPEN — **The elicited figures.** Days lost to a stoppage against a strong versus weak response;
   productivity loss on restart and how long it persists; acceleration cost multiplier; probability
   a near miss becomes a stop work order and how acceleration changes it; what owner credibility is
   worth later; contingency drawn when a change is absorbed. Nothing below can run without these.
2. OPEN — **The state variables.** Which numbers the training project actually holds. Candidate
   set: cost performance, schedule performance, float, contingency, open dispute state, notice
   clock, owner credibility.
3. OPEN — **Which decisions a trainee should get wrong**, and what they should learn from it. Two
   or three, not a catalogue.

## Build, sequential

4. DONE (2026-08-04, run 1) — **Feature flag and gating.** `training` reuses the `auditor`
   pattern exactly (FEATURE_KEYS/FEATURE_LABELS/GATED_ACTIONS, same admin toggle). Nav item is
   real and hidden/shown by the flag (`[data-nav="training"]` driven in a browser, both states).
   Research accounts refused server-side, unconditionally (`RESEARCH_FORBIDDEN_ACTIONS`), not by
   the flag defaulting off — proven by setting the flag true on a research account and confirming
   the refusal still holds. Unauthenticated callers refused too, closing the same gap a previous
   session found on `getportfoliohealth`. Only `trainingstatus` has a real handler; the other
   four actions this roadmap will need are pre-listed in the gate, unimplemented, per
   `REPORT_2026-08-04_training-gating.md`.
5. DONE (2026-08-04, run 1) — **Training data isolation.** `projects.is_training` (migration
   0018, NOT NULL default false) is the single source of truth. `project_health`
   (`build_module_results_rows`) filters on it unconditionally — the one export path that had no
   `account_type` filter to lean on. `participant_inputs` needed no change: closed by construction
   via the research-account filter, since training is operational-only. A training project is
   also refused as research evidence at scenario creation AND at assignment (closing the one door
   from a training project into the research chain). Verified with a real training-marked project
   whose results are absent from all three export formats, and PROVEN able to fail by unmarking
   it and watching the same row reappear. Full table-by-table accounting of what was touched and
   what was considered and left alone is in the report.
6. DONE (2026-08-04, run 2) — **The state store.** `training_runs` (migration 0019, throwaway
   SQLite only — production unapplied, as is 0018): current state plus full decision history as
   JSON, beside the observations store. Advanced only by `training_engine.advance`, pure and
   deterministic; the figures stand in for decision 1's elicited numbers and are flagged for
   correction in `REPORT_2026-08-04_training-loop.md`, which leads with the effect table.
7. DONE (2026-08-04, run 2) — **Period generation.** `signal_inputs_from_state` projects the
   state into all 76 merge keys (None where the state knows nothing, so abstention holds —
   docRiskScore abstains, verified), then the SAME `documents.run_and_store` tail the document
   path uses computes and stores. No training-only computation path exists; the portfolio
   boundary between training and real projects is closed in both directions and fault-proven.
8. DONE (2026-08-04, run 2) — **The screen.** `assets/js/training.js`: the brief (form, notice
   periods, LD rule, conditions — reachable at any point), the notice clock, the PM figures,
   the platform's own signals by group name with module recommendations, three decision buttons
   carrying the three tensions, the decision log. Driven end to end in a real browser.
9. DONE (2026-08-04, run 2) — **Decision capture and advance.** `trainingdecision` applies the
   effect table, computes the next period through the normal path, and the next period renders.
   Ten decisions complete a run; the two clocks (period, notice days) provably do not blur —
   one deferral spends A201's and ConsensusDocs' windows even though one period passed.
10. DONE (2026-08-04, run 3) — **Discrete events.** The near miss is discrete, exogenous and
    undisclosed (period four, in code, never in a response); every one converts to a stop work
    order; duration follows the response (full correction package 6/5 days lost, minimal 18/14,
    with 1 or 2 restart-shadow periods); cost depends on remaining float, proven head to head
    (same incident and response: 24,000 exposure float-rich, 80,000 float-poor). Acceleration
    raises the hazard deterministically and its incidents carry cause "acceleration" for the
    debrief. Figures in EVENT_FIGURES, designed, led with in
    REPORT_2026-08-04_training-events.md. The run 3 corrections to the effect table (deferral
    drift made visible, the escalation cost curve, credibility asymmetry, facility-based LD
    rate) landed in the same run.
11. DONE (2026-08-04, run 3) — **Narration.** One call narrates a state the engine already
    computed (training_narration.py); nothing reads the sentence back, so the generator cannot
    judge, structurally. A layer, not a dependency: no key, a failure, or a raising narrator
    all leave the run on the figures alone, byte-identical state either way. Em dashes are
    stripped mechanically.
12. DONE (2026-08-04, run 4) — **Debrief.** `trainingdebrief`, complete runs only: what was
    spent, what closed with each matter's entitlement and reason, WHY each incident happened
    (acceleration incidents attributed in words from the engine-recorded cause; scheduled ones
    honestly not attributed), and the counterfactual as a REPLAY of the same pure engine with
    the first decision swapped to escalate — honest or reported unavailable with the reason,
    never estimated. Fault-proven both ways.

## Content

13. DONE (2026-08-04, run 4) — **Three contract regimes wired to the brief.** The form now
    matters across the whole run: the differing site condition (period five, 17 days old at
    first decision) fires trap 1 under A201 (14 not 21, Section 3.7.4) and gets form-specific
    duties under the other two; ConsensusDocs escalation is a two-step clock whose quiet
    period loses the claim (Section 8.4); FAR claims grow while deferred, the lookback halves
    the grown amount, and a threshold crossing during the last deferred period makes an
    immediate escalation uncertified (52.233-1). All four traps reachable, each fault-proven.
    Per `REPORT_2026-08-04_training-regimes.md`, which leads with them.
14. OPEN, LIN'S — **Verify A201 and ConsensusDocs periods** against the licensed documents. FAR
    and CDA figures came from primary sources; those two came from law firm summaries. Reported
    outstanding by run 4, not attempted there, per instruction.
15. DONE (2026-08-04, run 4) — **Disclaimer.** In the brief (before period one) and the
    debrief: the governing form and jurisdiction, the amendment note with "check which rules
    actually govern", and the sourced-versus-designed marking of every figure. No liability or
    consent language composed; the platform's approved notice text stands unchanged.

## Deferred, deliberately

16. OPEN — International regimes. US only for now.
17. OPEN — Document generation. The screen states the position; no documents are produced.
18. OPEN — Branching content authored per scenario. Generated runs instead, with deterministic
    mechanics underneath.

---

## Standing constraints

- Operational only. Research accounts refused at the action.
- Training data never reaches the export or the research chain.
- Signals compute from real numbers. Nothing fabricates; abstention still applies.
- Mechanics are fixed even where judgement is open. Directors disagree about the right call, not
  about whether escalating spends float.
- The platform is a research instrument first. This does not touch anything the study depends on.

## Log

Append one line per run: date, items attempted, items completed, what moved to BLOCKED and why.

- 2026-08-04: run 1, items 4 and 5 attempted and completed (gating + isolation). Nothing moved to
  BLOCKED. Items 1–3 remain OPEN and block items 6 onward. See
  `REPORT_2026-08-04_training-gating.md`.
- 2026-08-04: run 2, items 6 to 9 attempted and completed (the loop). Nothing moved to BLOCKED.
  Items 1–3 remain OPEN: the designed figures now standing in for them are in
  `training_engine.py` and are led with in `REPORT_2026-08-04_training-loop.md` for correction.
  `training_us_contract_regimes.md` was missing from the repository and is now committed.
- 2026-08-04: run 3, items 10 and 11 attempted and completed (events and narration), plus the
  four effect-table corrections. Nothing moved to BLOCKED. Items 1–3 remain OPEN; the event
  figures join the designed layer, in `EVENT_FIGURES`, led with in
  `REPORT_2026-08-04_training-events.md`. Item 12 (the debrief) is the remaining build item and
  its raw material (incident causes, decisions, per-period changes) is now all captured.
- 2026-08-04: run 4, items 12, 13 and 15 attempted and completed (regimes across the run,
  debrief, disclaimer). Nothing moved to BLOCKED. THE BUILD IS COMPLETE: items 4 to 13 and 15
  are DONE. Open now: items 1 to 3 (the designed figures await correction), item 14 (period
  verification against the licensed documents, Lin's), items 16 to 18 (deferred deliberately),
  and production migrations 0018 and 0019 before the first training run. See
  `REPORT_2026-08-04_training-regimes.md`.
