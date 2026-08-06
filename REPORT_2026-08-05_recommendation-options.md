# The recommendation becomes a set of courses of action, with the consequence of each

**Date:** 2026-08-05
**Branch:** `claude/recommendation-options-s5s90m` (merged to `main`, commit `901cb31`)
**Suites:** server 40 suites, **2229/2229** (fresh SQLite per test file, +29 from a new `test_training_options.py`); `tests.html` **51/51**; `tests_render.html` **142/143** (the 1 is the pre-existing auth-gated "production read path" check, red on `origin/main` too).

---

## THE DEFECT, AND WHAT REPLACED IT

The Governance Decision card said one verb, one authority, one documentation line. A project manager could not act on it, argue with it, or be directed anywhere by it. It now lays out the courses of action open, states for each what it costs, what it forecloses and what it protects, and only then names the recommended one with its reason against the evidence.

**The hard constraint held throughout: every consequence traces to something the platform holds, and where a consequence cannot be established the surface says so instead of asserting one.** That is the whole of the work. The prose is written around figures; no figure is written around the prose.

---

## WHAT EACH SURFACE HOLDS (established from data and code, not assumed)

### Training, the strongest of the three

The training run holds a **stated effect table** (`server/app/training_engine.py`: the `EFFECTS` comment block plus `EVENT_FIGURES`, `QUALITY_FIGURES`, `RESOURCE_FIGURES`, `CONDITION_PROFILES`) and the **contract periods with their clause citations** transcribed from `training_us_contract_regimes.md` (`CONTRACT_FORMS`). It also holds live state variables: float total and consumed, contingency remaining, owner credibility, crew adequacy, liquidated damages per day, and the two derived notice clocks (`notice_position`, `dsc_position`).

So training can state a **rule**, not a guess: escalating costs `escalation_float_cost(state)` days of float because that is the curve the engine will actually apply, and deferring closes a 21 day window because `PERIOD_DAYS` is 30 and the clock is derived from the same arithmetic. `build_options(state)` computes every figure with the same helpers `advance` uses, so the option text and the outcome cannot disagree.

**What training cannot establish, and says so:**
- The incident hazard is **withheld, not unknown**: it is redacted from every response because a foreseen near miss teaches nothing, so accelerating says "the safety exposure of compressed work is deliberately not stated in advance in this run" rather than inventing or leaking it.
- A period with no open matter: escalating and absorbing both return `Not established: no open matter carries an entitlement for a notice to protect this period.`
- The ConsensusDocs documentation step is not one of the period's verbs (any active decision keeps the file moving, deferring loses it), so `recommended_decision` is `None` there rather than an invented single verb.

### Operational, grounded but thinner than training

The stored result (`ComputedResult.module_results`, `signal_inputs`) holds:
- **Regret Minimization** stores `expected_regret` as **named courses of action with a score each** (`{monitor: 11, investigate: 5, escalate: 8}`) plus `recommended_action`. This is the only place the platform holds a *set of courses of action* for an operational project, so it is the spine of the operational block. When it did not compute, there are no courses of action and the card says so and draws none.
- **the governance module in the Recommendation and Governance group** stores `authority`. This is the only authority the platform holds.
- **Cost Risk Analysis** (integer eightieth percentile estimate at completion and its percentage) or **Monte Carlo EAC**, for the exposure figure each option is weighed against.
- `signal_inputs` cost and schedule performance and budget at completion.

**What operational cannot establish, and now says so:**
- **Documentation required has no source anywhere.** Neither the analytical layer nor the stored result records a documentation requirement; the previous card value was a literal in `decision.js` (mirrored by a literal in `models_decision.py`) with nothing behind it. It is now `Not established: the platform holds no documentation requirement for this state.` It was not preserved in longer prose.
- **Authority is now read from the stored governance module**, not from the browser literal. Where that module abstained the field reads not established.
- **No deadline is asserted**, because nothing stores one. There is no "within 48 business hours" in the new block.
- **The cost and duration of investigating** are not figures the platform holds, and the option says so inside its own cost line.
- **Why the recommendation differs from the lowest score.** The stored result records the recommendation and the scores but not the rule that set one against the other, so the block states exactly that rather than guessing a threshold.

### Research, the same evidence plus a frozen stimulus it must not touch

Two different things sit on the research surface and are labelled as two different things.

1. The **decision support package** is researcher-authored and frozen (`DecisionSupportPackage`: `recommended_action`, `alternatives`, `uncertainty`, `limitations`, `applicability_boundary`, `expiration_trigger`, all free-form JSON or text with **no figures and no consequence structure**). It is rendered exactly as frozen and is not touched.
2. The **stored analytical result for the period's evidence project** is available to the participant through `projectresults`, and **after the reveal it is not redacted**. Before the lock, `documents.py` `_ACTION_KEYS` strips `expected_regret` / `recommended_action` / `authority` and replaces the action-bearing prose, which is what keeps the pre-lock evidence screen safe.

So research holds **exactly what operational holds** for the option block, plus a package that holds nothing quantitative. The option block is therefore generated at display time by the same generator the card calls, after the reveal, and the reveal gate is preserved for free: before the lock the generator finds no scored courses of action and reports none available, which is the same sentence a project whose analysis abstained gets. Nothing was frozen and nothing is generated at package creation, per the owner's settled decision.

### Where the three differ

| | Training | Operational | Research |
|---|---|---|---|
| Source of the option set | `allowed_decisions(state)`, the run's own verbs | the named courses the regret analysis scored | same as operational |
| Source of consequences | the effect table, computed with `advance`'s helpers | stored module figures | same as operational |
| Contract periods and citations | yes, per form | none held | none held |
| Cost of each course in money and days | yes, exactly | no; a worst case score out of 30, plus one shared exposure figure | same as operational |
| Authority | not modelled; the run is the PM's own decision | stored governance module, else not established | same as operational |
| Documentation requirement | not held | **not held, now marked** | not held |
| Deadline | yes, a real date from the period calendar | not held, not asserted | not held, not asserted |
| Generated at display time | yes | yes | yes |

The honest summary: **training can price a decision, operational and research can only rank one.** Operational's consequences are real but coarser, and the block says which parts are coarse rather than dressing the gap.

---

## THE FULL RENDERED RECOMMENDATION ON EACH SURFACE

All three were driven in headless Chromium against the production renderers. Quoted verbatim.

### 1. Operational, the Governance Decision card

Stored row: regret scores `{monitor: 11, investigate: 5, escalate: 8}`, recommended action `escalate`, governance authority `Program director / PMO lead`, cost risk eightieth percentile estimate at completion `15748571` at `31.2` per cent above budget, cost performance `0.84`, schedule performance `0.88`.

```
GOVERNANCE DECISION
Recommended action                                                    Red
CONFLICT
Mixed early warning
AUTHORITY
Program director / PMO lead
DOCUMENTATION REQUIRED
Not established: the platform holds no documentation requirement for this state.

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
other two, where a lower score means a smaller worst case. It moves the decision to Program
director / PMO lead.

What it forecloses. It closes off settling this inside the project: once it is a matter for
review, Program director / PMO lead holds it, not you.

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

Recommended actions require named human approval before they are recorded; fairness gates
require contractor response opportunity before any formal action.
```

### 2. Training, the trainee screen

Real server view from `build_options`, period one, AIA A201-2017, exacting conditions, contract value 12,000,000 dollars, rendered by the real `LinTraining.render`.

```
Courses of action

These are the decisions open to you this period, with what each one costs, what it closes off,
and what it protects. The figures are the run's own rules. Where the run holds nothing to say,
it says so instead of asserting a consequence. The recommendation follows, so the choice stays
yours.

Escalate it as a claim   [Recommended]
Serve written notice of claim and open the position formally.
What it costs.
  - 4 days of float, against 12 days remaining, leaving 8.
  - 24,000 dollars in claim preparation, and the affected work held.
  - One point of owner credibility, from 3 to 2, and any progress towards earning a point back
    resets to zero. Earning a point takes 2 concessions.
What it forecloses. It closes off absorbing the matter quietly: the position becomes formal and
the owner answers it formally.
What it protects. It protects the entitlement to 180,000 dollars if the window holds: 11 days
remain of the 21 day period in Section 15.1.3.1.

Absorb it
Draw the cost from contingency and close the matter.
What it costs.
  - 180,000 dollars from contingency, leaving 420,000 dollars.
  - The work is done anyway, so the cost lands whether or not it is claimed.
What it forecloses. It closes the matter and waives the entitlement permanently. It cannot be
reopened later on the same facts.
What it protects. It protects float entirely, which escalating spends, and it earns one step
towards owner credibility. 2 steps earn a point.

Defer the decision
Take no formal step on the matter this period.
What it costs.
  - 3 days of float, against 12 days remaining, leaving 9. Coordination drift, and it repeats
    every period the matter stays open.
  - 36,000 dollars of unmanaged change cost, again every period.
  - The period earns 90 per cent of what an undisturbed period earns, and lost earning is never
    recovered.
What it forecloses. The clock runs 30 more days before the next decision. Today 11 days remain
of the 21 day period in Section 15.1.3.1, so by the next decision point the window will have
closed.
What it protects. It protects contingency and owner credibility, both unchanged, and it keeps
every other course open for one more period.

Accelerate the works
Buy schedule back by compressing the works.
What it costs.
  - 180,000 dollars: 1.0 per cent of contract value at this profile's premium of 1.5 times.
  - The safety exposure of compressed work is deliberately not stated in advance in this run, so
    it cannot be planned around.
What it forecloses. It closes off nothing formally, and it spends money that contingency does
not cover once contingency is gone.
What it protects. It buys back 4 days of float, from 12 days remaining to 16, which is the only
course here that adds float.
```

The recommendation that follows it (unchanged in content, now marked against the options above):

```
Recommendation
Serve notice of claim for the unforeseen utility conflict
What        Serve written notice of claim for the unforeseen utility conflict, with the current
            cost record attached, for an estimated 180,000 dollars.
Why         Cost performance stands at 1.0 and schedule performance at 1.0, with 12 days of
            float remaining; 11 days remain of the 21 day period in Section 15.1.3.1. Notice now
            preserves the entitlement whatever the final quantum proves.
Who acts    The project manager prepares and signs the notice; the project executive is
            informed, not asked. Waiting for an executive decision spends days the window does
            not have.
To whom     the architect and the owner's representative
By what means  certified or registered mail, or a courier with proof of delivery, as Article 15
            requires for a claim. Email is not service.
Next step   Serve the notice by 2026-02-04; the period closes the window after that.
By when     2026-02-04
```

The deferral line is the teaching point the run was built for and it now appears before the choice rather than after it: one deferral spends a 21 day window although only one period passed.

### 3. Research, the decision support the participant responds to

Driven through the real `LinDecisionUI.mount()` and the real reveal button, stage `awaiting_reveal` then `deciding`.

The frozen, researcher-authored package, rendered exactly as frozen:

```
Shown at 8/5/2026, 12:00:00 PM. Your preliminary judgment was recorded before this point and is
unchanged.
Recommended action        Escalate to recovery review
Detected condition        Cost and schedule performance both below plan.
Alternatives considered   ["Monitor for one period", "Re-baseline"]
Limitations               Reported figures only.
Model ref-1 · package version 1
```

Then, generated at display time from the stored result, the identical block the operational card produces from the identical evidence:

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
other two, where a lower score means a smaller worst case. It moves the decision to Program
director / PMO lead.
What it forecloses. It closes off settling this inside the project: once it is a matter for
review, Program director / PMO lead holds it, not you.
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

---

## THE BUILD

**New `assets/js/recommendation_options.js`** (dependency free, plain global). `build(result)` reads `module_results` and `signal_inputs` off the primed stored row and returns `{available, reason, options[], recommendation, authority, unknowns}`; `html(spec)` renders it. `buildForProject` / `htmlForProject` go through `LinResults.rowFor`, the primed row of the `primeAndRefresh` pattern. Nothing recomputes: the file calls no model, and `sim.js` / `simulations.js` / `deepdive.js` are not loaded on these routes.

**`assets/js/app.js`** `renderDecisionCard` appends the block, sources Authority from the stored governance module, and marks Documentation required as not established. The single verb "Recommended action" field is gone; the recommendation now lives at the foot of the options with its reason.

**`assets/js/decision-ui.js`** gains `renderRevealedOptions()`, called after the reveal, which re-reads `projectresults` (un-redacted at that point) and renders the same block into a new `#dc-options` host beneath the frozen package.

**`server/app/training_engine.py`** gains `build_options(state)`, pure, covering all twelve decisions the engine defines, plus a `decision` key on each `build_recommendation` return so the recommended option can be marked without re-deriving the policy. `server/app/training.py` returns it as `options` on the state view. **`assets/js/training.js`** renders it above the recommendation.

### A pre-existing crash found and fixed on the way

`build_recommendation` raised `KeyError: 'recoverable_fraction'` whenever a differing site condition was the open matter under **ConsensusDocs or FAR**: those forms' site condition positions carry no lookback fraction, and the function fell into the cost lookback arm. That is the recommendation crashing for exactly the two forms whose site condition rule the run exists to teach. Fixed with a branch that states the prompt notice duty and its citation (Section 3.16.2 / FAR 52.236-2(a)) and reproduces no clause text. Found by the exhaustive form by decision exercise in the new suite.

---

## VERIFICATION

Every check was proven able to fail: fault applied, red confirmed, reverted, green confirmed. Faults target block elements and exact string matches.

**`tests_render.html` group 15 (new, 21 checks)** renders the production `LinApp.renderDecisionCard`:
- **every numeric token in the entire block** must be one of the stored values (`11, 5, 8, 30, 15,748,571, 31.2, 0.84, 0.88`); any other number fails;
- the exposure sentence and the score sentence are asserted as exact substrings;
- the option keys and their order equal the stored `expected_regret` keys;
- a row without the cost figure renders "Not established" and asserts **no** completion figure;
- a row without the scoring analysis renders the unavailable notice and **zero** options;
- a **pre-lock redacted** result yields no courses of action;
- Authority equals the stored authority, Documentation required starts with "Not established";
- byte identical output on two builds from two independently constructed identical rows;
- the research surface's rendered block **contains the card's block verbatim**;
- no leaf carries a module or category id (anchored `[A-D]\d(\.\d+)?` scan).

**Faults proven (browser):**
1. `money()` returns value plus one: the exactness scan went red with `15,748,572` and the exact quote check went red. 140/143, reverted to 142/143.
2. `exposure()` fabricates a figure when neither module computed: both abstention checks went red. 140/143, reverted.
3. `build()` fabricates a score set when the scoring analysis is absent: four checks went red, **including the pre-existing "card does not recommend routine monitoring on a Red project"**. 137/143, reverted.

**`server/tools/test_training_options.py` (new, 29 checks)** asserts each figure against the effect table constants directly (`escalation_float_cost`, `ESCALATE_PREP_COST_RATE`, `CRED_EARN_CONCESSIONS`, `defer_drift_float_days`, `DEFER_EV_FACTOR`, `PERIOD_DAYS`, `acceleration_float_recovered_days`), that the option list equals `allowed_decisions` in order, that the output is byte identical on a repeat build, that the hazard appears nowhere, that the form decides the words (federal lookback vs A201's 21 days vs ConsensusDocs' 14), that a quiet period abstains rather than recommending, and that every form against every decision ten periods deep builds options without raising, with all twelve decisions actually exercised.

**Faults proven (server):**
4. float sentence quotes `days + 1`: two checks red (27/29), reverted.
5. escalating with no open matter asserts an entitlement: the abstention check red (28/29), reverted.

---

## FILES CHANGED

`assets/js/recommendation_options.js` (new), `assets/js/app.js`, `assets/js/decision-ui.js`, `assets/js/training.js`, `assets/css/radar.css`, `index.html`, `tests_render.html`, `server/app/training_engine.py`, `server/app/training.py`, `server/tools/test_training_options.py` (new), `T6_HANDOFF.md`. Nothing under `server/app/simulation/` was touched. No migration. No liability or consent language was composed. No module id or number appears in any user facing string; no em dashes.
