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
6. OPEN — **The state store.** Small, deterministic, advances by the rules in decision 1. Sits
   beside the observations store rather than inside it.
7. OPEN — **Period generation.** State sets `signalInputs` directly. No documents, no extraction,
   no filing. The existing computations run unchanged so signals stay honest and abstention still
   works.
8. OPEN — **The screen.** Same signals and status the platform already shows, plus the figures a PM
   needs to read, plus the recommendation. Brief states jurisdiction and contract form.
9. OPEN — **Decision capture and advance.** Trainee decides, state advances by the rules, next
   period renders. This is the loop.
10. OPEN — **Discrete events.** Near miss occurs discretely, stop work order follows, duration
    depends on the response, cost depends on remaining float.
11. OPEN — **Narration.** The model writes prose around numbers the state model produced. **The
    generator must not be the judge**: one call narrates, the arithmetic stays deterministic, or it
    will retroactively justify whatever the trainee chose.
12. OPEN — **Debrief.** At the end of a run, what was spent, what closed, what the alternatives
    would have cost. Without this a trainee learns nothing they can carry.

## Content

13. OPEN — **Three contract regimes wired to the brief.** A201-2017, ConsensusDocs 200, Federal
    FAR. Periods per `training_us_contract_regimes.md`. The brief names the form; the deadlines
    follow from it.
14. OPEN — **Verify A201 and ConsensusDocs periods** against the licensed documents. FAR and CDA
    figures came from primary sources; those two came from law firm summaries.
15. OPEN — **Disclaimer.** States the jurisdiction and form in use, and that periods are routinely
    amended in negotiation so a real project may not match its own form.

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
