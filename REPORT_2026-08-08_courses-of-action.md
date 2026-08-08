# The courses of action are readable on an operational project, and the message tells the truth

**Date:** 2026-08-08
**Branch:** `claude/courses-of-action-1nfjnx`, from `origin/main` at `5fb0be7`
**Model:** Opus

**Verification:** server suite **47 suites, 2546/2546** (fresh migrated SQLite per test file; the
new `test_courses_of_action.py` adds 30). `tests.html` **51/51**. `tests_render.html`
**204/205**, 20 checks added here in a new group, the one red being the pre-existing auth-gated
"production read path" check that is red on `origin/main` too. Both surfaces driven in real
headless Chromium: the operational card, and the research path before and after the lock
(**15/15**). Five faults injected, each confirmed applied before its run, each detected, each
reverted with a SHA-256 comparison, and the baseline re-run green after every one.

**No migration was written and none is needed: no column, no table.** Migrations still unapplied
in production are unchanged from the prior sessions and remain Lin's to run: **0020
(`abstained_modules`), 0021 (`schedule_activities`), 0022 (`upload_attempts`)**. No
`DATABASE_URL` pointed anywhere but throwaway SQLite. Production was neither inspected nor
queried.

**Nothing under `server/app/simulation/` was modified.** No module's arithmetic changed. Nothing
recomputes in the browser.

---

## LEAD: what the two paths are told apart by

**`research_membership.reveal_gate_applies(session, project, caller)`, and it is a disjunction of
two facts, neither of which is the `Decision` row.**

```
the reveal gate applies when
    the caller is a research participant            (account_type == "research")
 OR the project is a scenario's evidence package    (Scenario.evidence_package_id == project)
```

Either arm is sufficient, so the gate lifts for exactly one case: **an operational account
reading a project no scenario is built on.** That is the project manager on their own project,
which is the case that was broken.

### Why two arms and not one

I started with the project arm alone, on the reasoning that the gate protects a project's
package and the module docstring is explicit that it is withheld from *every* member, observers
included. **A failing test proved that insufficient, and it was right to.**
`test_decision_ui_t4.py` computes `PRJ-T4-ANALYTICS` — a plain project no scenario names — and
reads it **as a research participant**, asserting that no action-bearing prose reaches them
pre-lock. With the project arm alone that read released `Minimax regret recommends: escalate`
to a study subject. The suite went to 70/73 and named the leak. A participant is a study subject
wherever they are on the platform, so an action-bearing finding on any project they can reach
can prime the judgment they are about to record on their own scenario.

So the caller arm is not a convenience; it is the T4 prose-leak protection, and dropping it is
Fault 2 below.

### Why each rejected candidate is wrong, asserted rather than argued

| Candidate | What it would leak | Held by |
|---|---|---|
| the `Decision` row (the old route in) | `project_decision_state` returns a decision only when the project has an active PM **and** a scenario names it **and** that PM holds an assignment. Absence conflates an operational project with a study project that is merely early, or has had a membership change. A revoked PM row on a study project would release the courses. | a check that revokes the PM row on a research project and asserts an observer still sees nothing |
| the caller's `account_type` alone | an operational-account **observer** on a study project would bypass it, and an observer may be senior to the PM, which is the exact reason the rule says "every member" | a check that adds an operational observer to a research project and asserts they are still gated |
| the project alone | the T4 participant prose leak above | Fault 2, and `test_decision_ui_t4.py` |

Both leaks are asserted as checks that must not fire, and Fault 3 (project arm removed) turns
both red.

## Whether the Workspace surface had it too

Not applicable here: this defect is on one read path, `a_projectresults`, which every surface
that renders the card goes through. Both the operational Governance Decision card and the
research decision support call the same generator on the same row, so one server change fixes
both, and the research path is verified separately below to prove it did not weaken.

---

## Part 2. Why the message was wrong, established rather than guessed

The brief offered two possibilities: the earlier `recommendation_withheld` fix is not reaching
this surface, or the project falls into the did-not-compute branch for another reason.
**It is the first, and the mechanism is a third state neither branch modelled.**

Reproduced live, on the unmodified code, by reading the page's own objects in the browser:

```
storedResult_keys:      ["result_id", "period", "project_status", "category_statuses"]
row_has_module_results: false
regret_present:         false
regret_withheld:        null
spec_reason:            "...did not compute for this project..."
```

`facade._stored_status_map` attaches `storedResult` as a **four-field status projection with no
`module_results`**. `taxonomy.js` `rowFor()` preferred `project.storedResult` over the complete
row primed into `ROWS` from `projectresults`, and returned it unconditionally. So the scoring
module was not *redacted* on that row, it was **absent** — and `recommendation_withheld` is a
per-module flag, which cannot be read off a module that is not there. The earlier fix was
correct and simply never got the chance to fire.

`detail.js` `primeAndRefresh` grafts the complete row in afterwards, so the false state is a
race. But a race that resolves to a false sentence on screen is still a false sentence, and the
card was making a claim about a module whose status the Signal Ledger was rendering two panels
down on the same page.

**Three facts had been sharing two sentences. They are now three:**

1. **the row carries no module results at all** — nothing is known about any module, so the
   block says the analysis has not been read back yet and asserts nothing about whether it ran;
2. **the module is present and its action fields were withheld** by the reveal gate;
3. **the row carries module results and the scoring module is not among them** — it abstained,
   and this alone is "did not compute".

`rowFor()` was also fixed to return whichever copy actually carries module results, which closes
the race rather than only labelling it. Both are needed: the `rowFor` change stops the wrong
branch being reached in the ordinary case, and the third state stops a false claim whenever a
caller genuinely has nothing but the projection.

### Is the operational withheld message now dead?

**No, and it was confirmed rather than assumed.** After Part 1 the withheld sentence is
unreachable on an operational project, and a check asserts that no module on an operational read
carries the redaction flag. But the branch is **live on the research path**, which is where it
was always meant to fire, and the browser drive below quotes it firing. It is kept for that, not
left behind as a dead branch: removing it would break the instrument.

---

## The rendered Courses of action block, quoted

All three read back from the real application in headless Chromium against a throwaway SQLite
instance. Stored row: scores `{monitor: 11, investigate: 5, escalate: 8}`, recommended
`escalate`, eightieth percentile estimate at completion `15748571` at `31.2` per cent above
budget, cost performance `0.84`, schedule performance `0.88`. The governance module abstained on
this project, so authority reads not established, which is the traceability rule working.

### 1. Operational project, after the fix

```
Courses of action

These are the courses of action the analysis scored for this period, each with what it costs,
what it closes off, and what it protects. Where the platform does not hold what would be needed
to state a consequence, it says so instead of asserting one. The recommendation follows the
options, so the choice stays yours.

Keep the project under routine monitoring

Carry the position into the next reporting period unchanged and record the signals as they
stand.

What it costs. The analysis scores the worst case of this course at 11 out of 30, the highest
of the set, where a lower score means a smaller worst case.

What it forecloses. It closes off nothing, and it spends a reporting period during which the
position is unchanged: an eightieth percentile estimate at completion of 15,748,571 dollars,
31.2 per cent above budget.

What it protects. It protects the working relationship and the project's own authority over the
matter, and it adds no cost of its own.

Investigate before taking a formal step

Open the variance inside the project: test the figures behind the forecast and establish what is
driving them before any formal step is taken.

What it costs. The analysis scores the worst case of this course at 5 out of 30, the lowest of
the set, where a lower score means a smaller worst case. Not established: how long an
investigation takes, and what it costs, is not a figure the platform holds.

What it forecloses. It closes off nothing formally, and it spends a reporting period. The
forecast the period would close on is unchanged by investigating it: an eightieth percentile
estimate at completion of 15,748,571 dollars, 31.2 per cent above budget.

What it protects. It protects the decision from leaving the project before the figures behind it
have been tested, and it keeps the formal step available afterwards.

Escalate to management review

Put the position formally in front of management as a matter for review, rather than settling it
inside the project.

What it costs. The analysis scores the worst case of this course at 8 out of 30, between the
other two, where a lower score means a smaller worst case. Not established: the platform holds
no record of which authority an escalation moves this decision to.

What it forecloses. It closes off settling this inside the project. Not established: who it
moves the decision to is not recorded for this project.

What it protects. It protects the position from being carried further on the project's own
judgment: the figure that goes up is an eightieth percentile estimate at completion of
15,748,571 dollars, 31.2 per cent above budget.

Recommended: Escalate to management review

It is not the lowest scoring course: it scores 8 out of 30, against 11 for keep the project
under routine monitoring and 5 for investigate before taking a formal step. The stored result
records the recommendation and the scores. It does not record the rule that set the
recommendation against the score, so the reason for the difference is not established here.
Against this period's evidence, cost performance stands at 0.84 and schedule performance at
0.88.
```

The sentence the brief opened with is gone, and every figure in the block is a value the stored
row holds.

### 2. Research participant, BEFORE the preliminary judgment is locked

```
Courses of action

The analysis that scores the courses of action against each other computed for this project,
but its finding is withheld until this period's preliminary judgment is recorded and locked.
Once it is, the courses of action appear here.
```

No course title, no score, no exposure figure. Asserted absent by name in the drive:
`11 out of 30`, `5 out of 30`, `8 out of 30`, `Keep the project under routine monitoring`,
`Escalate to management review`.

### 3. The same research participant, AFTER the lock

```
Courses of action

These are the courses of action the analysis scored for this period, each with what it costs,
what it closes off, and what it protects. Where the platform does not hold what would be needed
to state a consequence, it says so instead of asserting one. The recommendation follows the
options, so the choice stays yours.

Keep the project under routine monitoring

Carry the position into the next reporting period unchanged and record the signals as they
stand.

What it costs. The analysis scores the worst case of this course at 11 out of 30, the highest of
the set, where a lower score means a smaller worst case.

What it forecloses. It closes off nothing, and it spends a reporting period during which the
position is unchanged: an eightieth percentile estimate at completion of 15,748,571 dollars,
31.2 per cent above budget.
...
```

The withholding still holds before the lock and releases after. That is the instrument working,
unchanged.

---

## Three suites asserted the defect, and were rewritten

Not silently. Two blocks pinned the broken behaviour and one found the real gap in my first cut.

- **`test_decision_ui_t4.py`** — did NOT assert the defect. It caught my incomplete first fix and
  drove the design to the disjunction. Now **73/73, unmodified**.
- **`test_documents_b7b.py` Guarantee 6** and **`test_workspace_t3t5.py` Guarantee 8** — both
  read a project created by an **operational** account that no scenario names, and both asserted
  the read was "withheld pending the pre-judgment lock". There is no preliminary judgment on such
  a project and never will be, so the lock they waited on could not occur: what they pinned was
  precisely the defect. Rewritten to assert what is actually true there — no researcher-authored
  package is spliced in, nothing is reported as withheld, and the PM **can** read the scored
  courses — with the reason recorded in both files and a pointer to where the withholding is
  asserted for real. The package assertions (`package_hash`, `package_id`, `alternatives`,
  `detected_condition`) were always right and are unchanged.

The withholding is now asserted in two places that are about withholding rather than incidental
to it: `test_decision_ui_t4.py` and the new `test_courses_of_action.py`.

## What changed in code

- **`server/app/research_membership.py`** — `project_under_research_protocol(session, project)`
  and `reveal_gate_applies(session, project, caller)`, new. `recommendation_visible` is
  untouched: the reveal predicate itself did not change, only which reads it is applied to.
- **`server/app/documents.py`** — `a_projectresults` consults `reveal_gate_applies`; the audit
  record carries `reveal_gated` so a reader can tell which path a read took. `_result_view` now
  sets `recommendation_withheld` only when the gate actually withheld something, instead of on
  every read with no package — an operational project has no package to withhold, and flagging
  those reads told a project manager something was being kept from them when nothing was.
- **`assets/js/taxonomy.js`** — `rowFor()` returns whichever copy carries module results.
- **`assets/js/recommendation_options.js`** — the three-way distinction, plus `pending` and
  `withheld` on the returned spec so a caller and a check can tell them apart without matching
  prose.

No module id or number appears in any string added. No em dashes in user-facing text. No course,
consequence or figure was invented: the operational block quotes only stored values and states
"Not established" where the platform holds nothing, including the authority this project's
governance module abstained on.

## Proof each check can fail

Five faults, each anchor matching exactly once, each confirmed applied before the run, each
reverted with a SHA-256 comparison against the original, baseline re-run green after every one.

| Fault | Result | What went red |
|---|---|---|
| the gate applies to every read again (the reported defect, reproduced) | **23/30** | the operational project's scored set is stripped, the withheld placeholder returns, the read is marked withheld |
| the caller arm removed (project-only discriminator) | **70/73** on `test_decision_ui_t4` | the T4 participant prose leak: `recommended_action`, `expected_regret`, `minimax regret recommends` |
| the project arm removed (account_type-only discriminator) | **26/30** | both leaks: the operational-account observer on a study project, and the study project with a revoked PM row |
| the generator treats a projection row as if it carried module results | **200/205** | the false did-not-compute sentence returns for a row that knows nothing |
| `rowFor` prefers the four-field projection again | **202/205** | the generator cannot resolve the courses despite a complete row being primed |

Baselines: 30/30, 73/73, 204/205 before and after every fault. Faults 1 and 3 are the ones that
matter: the first reproduces the reported defect as a failing check, and the third proves the
research withholding is a property the suite can actually detect the loss of.

**The interpreter was confirmed real before any green was believed**: the server's `/healthz`
reported Python 3.11.15 and `/readyz` reported `schema at head 0022_upload_attempts`, so every
drive ran against a migrated database on the pinned interpreter.

## Open, and flagged rather than built

- **`primeAndRefresh` still repairs the projection by grafting.** `rowFor` no longer depends on
  that graft having happened, so the false message is gone, but two copies of a row on one page
  with different shapes remains a shape that invites this class of bug. Making the projection
  and the complete row one object is a larger change than this task should carry.
- **Abstention messages are still discarded before storage** (`registry.py` `run_all()`), so a
  module that genuinely did not compute still cannot say *why*. Unchanged from the
  ledger-calculations session's open item 1, and still a `server/app/simulation/` change.
- **The governance module abstained on the drive project**, so authority read not established.
  That is correct behaviour, not a gap, but it means the operational block's authority sentences
  were exercised on their abstention path here rather than their populated one; the populated
  path is covered by the existing `tests_render.html` group 15 fixture.

## Files changed

`server/app/research_membership.py`, `server/app/documents.py`, `assets/js/taxonomy.js`,
`assets/js/recommendation_options.js`, `tests_render.html`,
`server/tools/test_courses_of_action.py` (new), `server/tools/test_documents_b7b.py`,
`server/tools/test_workspace_t3t5.py`, `T6_HANDOFF.md`, this report.

No file under `server/app/simulation/` was modified. No migration. Nothing outside
`DEng\LinPRojectRadar` was touched, and nothing was deleted or moved outside it.
