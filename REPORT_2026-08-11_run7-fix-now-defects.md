# Run 7: the fix-now defects

Branch `claude/run7-fix-now-defects` from `origin/main` at `021d5e2`. This run is authorised to
change production files under `server/app/simulation/`, scoped to the fix-now defect class Run 6
identified and the shared eligibility machinery required to correct it. `sim-2026.08-v2` remains
the historical audit baseline and is not rewritten; this run creates the successor implementation
state, **`sim-2026.08-v3`**.

Sixteen modules were emitting a status from something they had not been given. All sixteen are
corrected. Nothing was invented to correct them: where a method's defining structure is absent
from the corpus, the correction is abstention.

---

## Lead table

| Module | Category | Run 6 defect | Old behavior | Corrected behavior | Formula changed? | Abstention changed? | Voting changed? | Tests | Result |
|---|---|---|---|---|---|---|---|---|---|
| Regret Minimization | decision optimisation, advisory | scores are literals, healthy outcome unreachable across the whole index grid | banded on every input, always investigate or escalate | abstains, decision structure absent | no, removed | yes, unconditional | no, non-voting before and after | grid of 3,721 index pairs exhausted, plus reason and injection | fixed |
| PERT Network Criticality | schedule, advisory | banded Green from an empty input | schedule index defaulted to on-plan | requires the schedule index | no | yes | no | valid, missing, malformed, reason, before and after | fixed |
| Line of Balance | schedule, advisory | banded Green from an empty input | same default | requires the schedule index | no | yes | no | same five | fixed |
| CCPM Buffer Health | schedule, advisory | banded Amber from an empty input | same default plus a completion of zero | requires the index and a completion figure | no | yes | no | same five, plus the planned-completion fallback | fixed |
| Reference Class Forecasting | cost, advisory | banded Red reading no project input at all | constant multipliers, constant band | abstains, reference class absent | no, removed | yes, unconditional | no | asserted on empty, rich and partial inputs | fixed by abstention |
| DSM Rework Propagation | schedule risk, advisory | banded Amber reading no project input at all | constant matrix, constant band | abstains, dependency matrix absent | no, removed | yes, unconditional | no | asserted on empty, rich and partial inputs | fixed by abstention |
| Overhead Absorption Rate | cost, advisory proxy | Green from an indirect plan of zero | absorption substituted as 1 | abstains, invalid denominator | no | yes | no | five cases, valid case 1.125 by hand | fixed |
| Inflation Adjustment Index | cost, advisory proxy | Green from a material baseline of zero | escalation substituted as 0 | abstains, invalid denominator | no | yes | no | five cases, valid case 10 per cent by hand | fixed |
| Queueing Theory Bottleneck | flow, advisory | Green from nothing planned | `max(planned, 1)` invented a denominator | abstains, invalid denominator; malformed counts refused | no | yes | no | five cases, valid case 0.19 by hand | fixed |
| Agent-Based Supply Chain | flow, advisory | Green from an empty long-lead log | `max(total, 1)` invented a denominator | abstains, no exposure; malformed counts refused | no | yes | no | five cases, valid case 0.15 by hand | fixed |
| Schedule Compression Index | schedule, advisory proxy | Green from a schedule index of zero, and not scale invariant | index defaulted to on-plan, denominator floored at one day, no remaining work read as a ratio of one | requires a positive index, floor removed, no remaining work is not applicable | **yes, arithmetic** | yes | no | five cases plus invariance exhausted over six baseline lengths | fixed |
| Critical Path Index | schedule, advisory | Amber from no planned progress | progress ratio substituted by the schedule index | abstains, invalid denominator | no | yes | no | five cases, valid case 0.92 by hand | fixed |
| Discrete Event Simulation | flow, advisory | Green from no planned progress | progress ratio substituted as 1 | abstains, invalid denominator | no | yes | no | five cases, valid case 1.0 by hand | fixed |
| Safety Performance Index | quality and safety, advisory | Green with a safety index of 1 at a rate of zero | index substituted as the literal 1 | index is the module's own cap of 2 at a zero rate; band stands on a true zero; negative rate refused | **yes, arithmetic** | yes, for a negative rate only | no | five cases, both directions against the shipped code | fixed |
| Specification Conflict Density | documents, advisory | Yellow from no requests | density substituted by the raw document risk | abstains, no exposure; negative count refused | no | yes | no | five cases, valid case 0.6 by hand | fixed |
| Dispute Escalation Index | claims, advisory proxy | reading improved three bands when two logs were withheld | absent sources scored zero; two names in the finding text described quantities not computed | all three sources required, a reported zero is evidence, finding text names the counts | no, weights and bands unchanged | yes | no | all seven strict subsets exhausted, plus text and trace | fixed |

---

## 1. The exact deduplicated fix-now module list

Derived from the merged Run 6 tests and the current code before any edit, not from the prompt.
Sixteen unique modules, four groups, no module in two groups. The list is written into the suite
itself (`FIX_NOW` in `server/tools/test_run7_fix_now_defects.py`) so the scope is in the code and
not only here, and the suite asserts the count, the non-overlap, and that every one is a module
this server actually computes and none is a disabled concept-only module.

- **Group 1, regret:** B4.7.
- **Group 2, banded from an empty input:** A2.1, A2.2, A2.3, A3.1, A5.1.
- **Group 3, substituted rather than refused:** A2.4, A2.11, A3.5, A3.9, A4.10, A5.6, A5.7, A5.8, A6.2.
- **Group 4, dispute:** A4.7.

Group 2 was derived by executing every implemented module on an empty dictionary and printing
the ones that returned a band. Seven did. Two of the seven have absence as their subject, which
is correct for them and they are untouched: the missing-data measure and the information
completeness measure. The other five are the ones corrected.

## 2. How the nine substitute modules were identified

Not by taking the nine names from the prompt. Three passes, and they agreed:

1. Run 6's own table in finding 1.3, which names the input and the returned band for each.
2. A targeted search of the analytical layer for denominator substitutions and equivalent
   fallback constructs: `max(x, 1)`, `... if d > 0 else <constant>`, `x || default` reproduced as
   `_or_default`, and ternaries substituting one measured quantity for another.
3. Run 6's own domain-safety section, which had already executed each zero or absent case and
   recorded whether the module refused. That section is the strongest evidence, because it runs
   the code rather than reading it, and it is where the nine were confirmed rather than assumed.

Each was then classified into exactly one of the four dispositions **before** anything was
edited. The dispositions are recorded in the code as `ZERO_CASE_DISPOSITIONS`:

| Module | Zero or missing case | Disposition |
|---|---|---|
| Overhead Absorption Rate | planned indirect cost of zero | `ABSTAIN_INVALID_DENOMINATOR` |
| Inflation Adjustment Index | progress-adjusted baseline of zero | `ABSTAIN_INVALID_DENOMINATOR` |
| Queueing Theory Bottleneck | no planned activities | `ABSTAIN_INVALID_DENOMINATOR` |
| Agent-Based Supply Chain | empty long-lead log | `ABSTAIN_NO_EXPOSURE` |
| Schedule Compression Index | schedule index of zero | `ABSTAIN_INVALID_DENOMINATOR` |
| Critical Path Index | no planned progress | `ABSTAIN_INVALID_DENOMINATOR` |
| Discrete Event Simulation | no planned progress | `ABSTAIN_INVALID_DENOMINATOR` |
| Specification Conflict Density | no requests for information | `ABSTAIN_NO_EXPOSURE` |
| Safety Performance Index | a reported zero incidents | `RETURN_ZERO_TRUE_ZERO` |

The ninth is what proves the classification did work rather than refusing everywhere. A safety
record that was read and recorded no incidents is a measurement, so the band stands. What does
not stand is the index beside it: the safety index is the benchmark over the rate, capped by the
module's own `min(2, ...)`, and at a rate of zero that ratio is unbounded, so the module's own
answer is its cap. The shipped code substituted the literal 1, a value its formula never produces
at a zero rate and which reads as performance exactly at benchmark. It is now 2, which is derived
from the module's own stated formula rather than from a literal.

Nothing else was removed. Numerical-stability epsilons, the contingency measure's `max(expected,
0.01)`, the uncertainty floors in the cost-risk and schedule-risk models, and the sigma floor in
the control chart are all left exactly as they were: none of them fabricates a denominator or an
input, and no proof was available that they belong to this defect class.

## 3. Regret Minimization disposition

**The corpus contains no governed action-by-scenario payoff matrix.** The only such structure
anywhere in the repository was the nine literals inside this module, which no project input
reached: the three expected regrets were 11, 5 and 8 on every project in every period, the
minimum was always to investigate, the two overrides could only move that to escalate, and the
one branch that produced a healthy reading was unreachable from any input. Run 6 exhausted 3,721
index pairs and found no pair that produced one.

So the module abstains, with the stable reason `canonical_decision_structure_absent`. No new
literals were substituted, no minimax-regret engine was built, and no owner approval was sought
for one because none was needed: the disposition is refusal, not redesign. The literals are gone
from the analytical layer, and the suite asserts that they are gone rather than merely
unreachable.

**It does not gate or suppress participant courses of action, and it did not before this run
either.** The courses of action have been unavailable from this module since Run 1, by the
owner's settled decision that a non-voting module is excluded from the recommendation text and
the courses of action; `recommendation_options.js` has carried that branch, with its own sentence,
since then. What changes is which sentence a reader sees when the platform holds no set of
courses of action: previously the non-voting sentence, now the file's existing "did not compute
for this project ... and it will not invent one". Both are true of every project, neither carries
remediation language, and no new decision policy was introduced. **No file under `assets/` was
edited**, which is asserted in the guard.

The participant course-of-action path itself is unchanged. The recommendation package a research
participant receives after locking a preliminary judgment is researcher-authored and reaches them
through the reveal gate, not through this module; that path is driven end to end in
`test_courses_of_action.py` and is green.

## 4. The empty-input modules

Three of the five read the schedule index with a default of 1.0, the value of a project running
exactly to plan, so a project nobody had reported anything about was modelled as one performing
to plan. They now require the index, and the CCPM measure additionally requires a completion
figure, taking the planned one where no reported one exists exactly as it always did. On a real
upload that reports an index, all three still compute, and their results are byte-identical to
the shipped code's on the same input. That is asserted, not claimed: no formula moved.

Two of the five read no project input at all and abstain unconditionally, because there is no
input that could make them eligible.

- **Reference Class Forecasting.** The method is defined by its reference class, a population of
  comparable completed projects whose realised overruns give the distribution. There is none. The
  nine multipliers were literals, so the debiasing factor and the band were the same numbers on
  every project. Building a reference population is explicitly out of scope.
- **DSM Rework Propagation.** The method is defined by its dependency matrix, for the project
  being analysed. There is none. The nine coefficients and the initiating wave were literals and
  no project input reached the arithmetic.

The preflight distinguishes missing scalar inputs, missing canonical structure, not applicable,
insufficient history, malformed input, invalid denominator and no exposure. Each is a distinct
stable code, and the suite asserts that a module handed an absent figure and the same module
handed a non-numeric one give different reasons.

## 5. Denominator and refusal corrections

Eight of the nine now refuse; the ninth keeps its band and loses its fabricated index. Two
corrections changed a number rather than only a refusal, and both are corrections to the module's
own stated arithmetic rather than new methods:

- **Schedule Compression.** The ratio is required days over available days, and available is
  required multiplied by the index, so the ratio is one over the index and cannot depend on the
  project's duration. The shipped code floored the denominator at one day, which is why the same
  index gave 2.0 on a year-long baseline and 1.0 on a two-day one, Red against Green. The floor
  is removed and the invariance the ratio always claimed now holds, exhausted over baseline
  lengths from two days to two and a half years.
- **Safety Performance.** Described in section 2.

The two modules that read the identical pair of fields, the look-ahead measure and the queue
measure, now agree about an empty window. Run 6's sentence was that one abstained on it and the
other read Green; both go through the shared layer.

## 6. Dispute Escalation correction

The weights are 0.3 for the request term, 0.3 for the change term and 0.4 for the document risk.
Only the document risk was required, and an absent source contributed zero to the sum rather than
being absent from it, so the identical project read 0.8 with both logs and 0.2 with neither:
three bands better for withholding the evidence. The counts were also tested for truthiness, so a
log that had been read and recorded no entries was indistinguishable from a log never read.

**All three sources are now required.** A project reporting all three is measured on the same
weighted sum with the same weights and the same bands, and 0.8 is re-derived by hand in the
suite. A project reporting fewer abstains and names which sources are missing, so they stay
visible in the trace. A reported zero is evidence and computes, at the document-risk term alone.

Renormalising over the present sources was considered and rejected: it would still let removing a
high term improve the reading, which is the same fault in a subtler form. Requiring all three is
the only rule under which removing evidence cannot improve the reading, and it is asserted over
**all seven strict subsets**, not one.

The finding text said "RFI velocity" of a raw count capped at twenty and "CO frequency" of a raw
count capped at ten. Neither term has a time or exposure denominator, so neither is a velocity or
a frequency. The text now names the counts the module actually uses. No dispute document, claim
register or new corpus was added, no formal dispute is inferred from this activity, and the
module stays the advisory, non-voting proxy its qualifier describes.

## 7. Shared eligibility changes

One mechanism, in `server/app/simulation/models.py`, and it is deliberately small: eight reason
codes, one `eligible()` preflight that validates required inputs present, denominator domain
valid and input well formed, and one `refuse()` that turns its verdict into the existing
abstention contract. It does not band, it does not score, and it does not touch a module outside
the proven defect set. Modules whose refusal needs to name a structure or a state the preflight
cannot see call `insufficient()` directly with the code, which keeps the layer from growing a
vocabulary of special cases.

The reason **code** is a stable machine string. The reason **sentence** is what a reader sees,
and it obeys the naming rules: words, no module ids, no key names, no reason codes, no em dashes,
"and" rather than an ampersand. The two are separate on purpose, because a code in a sentence is
exactly what the ledger must never render. The suite asserts the separation on every corrected
module.

The code is propagated onto the stored abstention row by the registry, served on the API read,
and carried in the module-results export in a new `abstention_reason_code` column. **The export
had never carried an abstention at all**, so a reader could not tell a computation that was never
registered from one that refused and said why; with sixteen computations now refusing where they
had been emitting a status, that gap became a hole in the record. One row per abstention, status
empty, the module's own sentence in the evidence column and the code beside it.

## 8. Browser and server divergence

**This run increases it, by sixteen modules, and does not touch the browser instrument.**

`assets/js/simulations.js` and `assets/js/sim.js` still carry the pre-remediation arithmetic,
including all fifteen defects the fifteen-defects run fixed on the server, and now also the
sixteen this run corrected. `research/deepdive.html` loads both, so the researcher deep-dive route
shows the old behaviour: the constant reference-class overrun, the constant rework multiplier, the
regret ranking with its unreachable healthy branch, and every substituted denominator. No
participant route loads either file.

Repairing the browser copies was explicitly out of scope for this run unless the same production
source was necessarily changed, and it was not: the server modules are Python and the browser
copies are separate JavaScript. The divergence is recorded rather than reduced, and it remains an
owner decision: annotate it, or bring the browser copies into line in a run scoped to do so.
`VALIDATION.md`'s parity claims now describe parity with sixteen more defects than before.

Nothing under `assets/` was edited by this run, which the frozen-file guard asserts directly.

## 9. Test results

**Server suite: 63 files, 4,379/4,379 checks under the `RESULT: n/n` convention, plus
`test_run5_export.py`'s own 34/34, so 4,413 in total, 0 failing files.** Fresh SQLite per file via
`alembic upgrade head`, `PYTHONIOENCODING=utf-8` throughout, interpreter confirmed real. The
baseline on `origin/main` at `021d5e2` was 62 files, 4,065/4,065 plus 34, so 4,099.

New: `server/tools/test_run7_fix_now_defects.py`, **265 checks**.

Existing suites whose counts moved, and why each moved. **No check was re-pointed merely because
production behaviour changed**; in each case the property the check protected is stated below and
either preserved with a live vehicle or restated because the property itself was the defect.

| Suite | Before | After | Why |
|---|---|---|---|
| `test_run6_known_answer.py` | 437 | 472 | the known-answer cases for the sixteen re-derived; the frozen-file guard re-based; four findings that recorded a defect now record the correction, each over the same exhausted domain |
| `test_run4_validate_seven.py` | 228 | 230 | the exclusion-layer check read `votes` off the scoring module's stored row; that module has no row now, so both halves are asserted: it is outside the voting set AND it produces no result to exclude |
| `test_courses_of_action.py` | 13 | 30 | every assertion used the scoring module as the vehicle for the reveal gate; the gate is unchanged and is now asserted on what defines it, the action-bearing key set and the recommendation package itself |
| `test_decision_ui_t4.py` | 73 | 86 | the redaction had no live vehicle on a first-period read, so the redactor's contract is asserted directly over each action-bearing key and the served read is asserted to carry none |
| `test_six_fixes.py` | 14 | 24 | the section pinned the served basis against the scoring module's threshold rule; that rule has no module, so the property is restated over the same grid: no ranking, no basis, nothing invented |
| `test_documents_b7b.py` | 74 | 76 | withheld against absent, asserted directly instead of through the scored set |
| `test_workspace_t3t5.py` | 76 | 77 | the same |
| `test_risk_register_and_notices.py` | 75 (crashed) | 124 | it recorded the reference-class constancy as a finding; the finding is corrected, so it records the correction, and the suite no longer aborts partway |

`tests.html`: **51/51**, real headless Chromium
(`/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell`, swiftshader).
`tests_render.html`: **286/287**, the one red being the pre-existing auth-gated production-read
row that has been red in every run since Run 2 and needs a signed-in session in the same tab.
Both identical to the Run 6 baseline, which is the point: no participant surface moved.

## 10. Mutation and fault-injection proof

Three mechanisms, and the first is the one that carries the weight.

1. **The shipped code is loaded and run, not described.** Every "it used to substitute a value"
   half of every proof executes the actual pre-run function, extracted with `git show` from the
   pinned baseline commit `021d5e2` into a throwaway package, on the identical input the
   corrected function is given. Each proof therefore reads "the shipped code returned a band on
   this input; this branch refuses it", and neither half can be satisfied by a mistake in the
   suite. The extraction is proved real before anything depends on it, by checking that the
   baseline is stamped `sim-2026.08-v2`, that its functions are different objects, and that it
   reproduces Run 6's lead finding: a project twenty per cent ahead on both indices told to
   investigate on scores identical for every project. If the extraction fails the suite refuses
   to run rather than testing one direction.
2. **Direct injection, section 9 of the new suite.** Three corrected functions are replaced in
   turn by ones reproducing the defect, the check protecting each is shown to go red, and the
   correction is restored and shown green again. Three of three caught, all restored.
3. **Expectation perturbation.** The known-answer suite's `ka()` refuses any case whose expected
   value cannot be perturbed, and reports the count: **283 of 283 expectations proved live**. The
   corrected safety index is additionally proved not to equal the literal it replaced nor an
   arbitrary third value, so the assertion of 2 is not vacuous.

The complete suite was re-run after every injection was restored, and is green.

## 11. Version transition

| Item | Value |
|---|---|
| Old version | `sim-2026.08-v2`, the Run 4 freeze, preserved as the historical audit baseline and not rewritten |
| New version | `sim-2026.08-v3` |
| Convention | the repository's own: `sim-<year>.<month>-v<n>`, the stamp moving when the analytical layer's behaviour changes. Run 4 moved it once for four runs of changes and recorded that as a fault to avoid; this run moves it for its own change |
| Changed module ids | A2.1, A2.2, A2.3, A2.4, A2.11, A3.1, A3.5, A3.9, A4.7, A4.10, A5.1, A5.6, A5.7, A5.8, A6.2, B4.7 |
| Changed formulas | two only: the schedule compression ratio (the one-day denominator floor removed, restoring scale invariance) and the safety index at a zero rate (the module's own cap instead of a literal) |
| Changed abstention or domain behaviour | the other fourteen, plus the two above |
| Voting set | `{A1.7 TCPI, A1.8 Variance at Completion}`, **unchanged** |
| Held non-voting for want of a sourced band | `{A2.8, A3.2, A3.4, A4.2, A4.3}`, **unchanged** |
| Disabled concept-only | the same eight, **unchanged**, and each proved still to refuse on a fully reported project |
| Band citations | `{A1.7, A1.8}`, **unchanged**. No band was created, relaxed or cited in this run |
| Test counts | 4,379 plus 34, from a baseline of 4,065 plus 34; new suite 265 |
| Migration | none. Alembic head unchanged at `0025_project_notices`; **0020 through 0025 remain unapplied in production**, which this run neither inspected nor queried |
| Dependency versions | unchanged, none added or removed |

## 12. Deliberately not fixed, because the defining structure is absent

Abstention is the fix for the first two; the rest are recorded as unchanged and out of scope.

- **Reference Class Forecasting** and **DSM Rework Propagation** abstain. No reference
  population, no dependency matrix.
- **Regret Minimization** abstains. No action-by-scenario payoff matrix.
- **PERT, Line of Balance, CCPM, Queueing, Agent-Based, Discrete Event** keep their literal
  structures and their proxy qualifiers, and are corrected only in what they refuse. No activity
  network, locations and crews, governed critical-chain buffer, arrival and service process,
  agent rule base or event and resource model exists, and this run invents none.
- **Schedule Risk Analysis P80** and **Isolation Forest** are untouched: neither is in the Run 6
  fix-now list, and both are named out of scope.
- **Rework Feedback Loop (A5.5)** carries the same missingness construct as the dispute
  composite: two of its terms score zero when their source is absent rather than being absent
  from the sum. **It is not in the deduplicated Run 6 list and was therefore not changed.** This
  is the clearest single candidate for the next run and is recorded here rather than fixed,
  because a fix outside the proven defect set is a stop condition.
- **The fused conflict figure's order dependence** (Run 6 finding 1.5) is untouched: it is
  shared machinery, not a fix-now module, and correcting it changes a number on every stored row.
- **The defensibility handbook's 69 validation claims** are untouched. Owner content.
- **The browser instrument.** Section 8.

## 13. Guarantees, each marked

- **No disabled module becomes executable.** VERIFIED. The disabled set is asserted as an exact
  set, and each of the eight is executed on a fully reported project and proved to refuse with
  its disabled activation state.
- **No advisory or non-voting module becomes voting.** VERIFIED. The voting set is asserted as an
  exact set, and no corrected module is in it.
- **Only the modules already authorised to vote can affect project status.** VERIFIED, on the
  stored row of a real upload as well as in the set comparison.
- **Fixing a non-voting module cannot change project status, recommendation text, courses of
  action or the decision card.** VERIFIED for status: no corrected module votes, so none reaches
  the category rollup or the fusion. For the courses of action, see section 3: the only change is
  which of two existing, already-reachable sentences a reader sees when the platform holds no
  scored set, and both were true of every project before this run as well.
- **The participant does not see remediation labels or qualifiers.** VERIFIED. Every corrected
  module's rendered sentence is asserted to carry no remediation word, no module id, no key name,
  no reason code, no em dash and no ampersand, and nothing under `assets/` was edited.
- **Abstention reasons survive storage, API and export propagation and the renderer path.**
  VERIFIED for storage, the API read and the export, on a real upload driven through the upload,
  compute and results routes. For the renderer, PARTLY MET on the same footing Run 6 recorded:
  `tests_render.html` drives the renderer and asserts the reason element's text, and it passes at
  286/287, but the live detail page was not re-driven end to end in a browser in this run.
- **No fabricated default remains in the Run 6 substitute-instead-of-refuse list.** VERIFIED.
  Each of the nine is executed on its own zero case and proved to refuse or, for the true zero,
  to report a value derived from its own formula. The invented denominators are additionally
  proved absent from the executable source with the comment lines stripped, and the strip is
  proved not to have emptied the string.
- **Empty input produces no substantive status for every affected module.** VERIFIED. All sixteen
  abstain on an empty dictionary, and across the whole implemented set only the two modules whose
  subject is absence still band on one.
- **Dispute Escalation does not improve when required evidence is removed.** VERIFIED, over all
  seven strict subsets of its three inputs.
- **The complete suite passes after all fault injections are restored.** VERIFIED. 63 files,
  4,379/4,379 plus 34, 0 failing files, re-run after restoration and again on merged `main`.
- **Nothing outside the scoped list changed behaviour.** VERIFIED. Every implemented module's
  result is compared function by function against the pinned baseline on a fully reported
  project; every module whose result moved is in the fix-now list, and the comparison is proved
  live by the modules that did move.

---

## The frozen-file guard: how it was re-based, and what it protects now

Run 4 froze the analytical layer and Run 6's suite asserted that **nothing** under `server/app/`
or `assets/` differed from `origin/main`. That guard cannot survive this run unchanged in either
direction: left as it was it fails, and compared against this branch it would compare the fix
with itself the moment the run merged. It was not deleted.

It is re-based in one place, section 0 of `test_run6_known_answer.py`, and narrowed rather than
loosened:

1. **The comparison is against a pinned SHA, `021d5e2`, not a branch name.** After the merge it
   still means the same thing, which is what the branch-name form would have stopped meaning.
2. **The files permitted to differ are enumerated by name.** Six: the five simulation sources
   this run's scope covers and `research_export.py`, which the owner's instruction names as
   metadata this run may update. A change to **any other file** under `server/app/` or `assets/`
   still fails the guard.
3. **`assets/` is in the permitted set nowhere at all.** The guard asserts separately that
   nothing under it differs, so every participant surface and the whole browser instrument remain
   byte-identical to the freeze, asserted rather than described.
4. **The guard is proved live**: it asserts that it does see the files this run changed, so a
   future edit that made the diff empty could not pass it silently.
5. The version assertion moved with it, from `sim-2026.08-v2` to `sim-2026.08-v3`, with
   `sim-2026.08-v2` recorded in the same place as the historical audit baseline.

The next run inherits this list and should narrow it back to empty once its own scope is settled.

## Stop conditions

None fired. No fix required inventing project data; no module outside the deduplicated list and
the shared machinery was changed; no voting or band change became necessary; the production
database was never touched, inspected or queried, and `DATABASE_URL` pointed only at throwaway
SQLite. The one candidate that would have breached scope, the Rework Feedback Loop, was left
alone and reported in section 12 rather than fixed.

## Files

Production: `server/app/simulation/models.py`, `models_doc.py`, `models_ext.py`, `models_gov.py`,
`registry.py`, `server/app/research_export.py`. Methods documentation, regenerated from the
changed sources: `code_audit/GROUP_A_project-health.md`,
`code_audit/GROUP_B_recommendation-governance.md`, `code_audit/CHECKSUMS.sha256`. Tests:
`server/tools/test_run7_fix_now_defects.py` (new), and the eight existing suites listed in
section 9. This report and `T6_HANDOFF.md`. No file under `assets/`. No file outside the
repository was touched.
