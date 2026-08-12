Run 10B — Critical Voter Fix and Bucket-3/4 Integration
Starting commit: c5d7101
Ending commit: see the final line of this report
Previous simulation version: sim-2026.08-v4
New simulation version: sim-2026.08-v5
Synthetic package version: OG-SYNTH-0.3
A1.7 domain defect: PASS
Voting set: 2 modules
Bucket-3 ready modules integrated: 6/6
Bucket-3 Monte Carlo disposition: resolved
Bucket-4 integrated: 2/2
Bucket-5 disabled: 2/2
Synthetic/operational separation: PASS
Known-answer tests: PASS
Abstention tests: PASS
Participant-visible change: yes, on the Signal Ledger only, and it is the intended
canonical-structure correction rather than a redesign. Four advisory modules that previously
reported a proxy reading now abstain and say which structure is missing. No layout, label,
sequence, recommendation, decision card or course of action changed, and project status is
unchanged for every in-domain project.
Production Postgres accessed: no
Full suite: 5627/5627

---

## 1. Handoff audit and repairs

`T6_HANDOFF.md` was read in full and reconciled against the committed history from the last
recorded handoff forward. Every completed session is represented: the fix-now defects run, the
retest-and-classify run, the synthetic package ingest and reconciliation, the v0.2 reingest and
closure, the test-only synthetic integration run, the v0.3 Monte Carlo and dependency matrix
correction, and the production remediation run that ended at `c5d7101`. The simulation version
history recorded there (sim-2026.07-v1, sim-2026.08-v2, sim-2026.08-v3, sim-2026.08-v4) matches
the freeze comments carried in the analytical layer itself, and the synthetic package history
(0.1, 0.2, 0.3) matches the three staged programme directories on disk. **No entry was missing
and no reconstruction was required. No earlier handoff history was overwritten.**

## 2. The A1.7 defect and the correction

**The reproducer, taken from the Run 10 neighbour sweep and run against the shipped baseline
code extracted from `c5d7101` by git rather than described.** A project with a budget at
completion of 1,000,000, an earned value of 400,000 and an actual cost of 900,000 reads Red at
the baseline, correctly: the remaining work of 600,000 against a remaining budget of 100,000 is
a ratio of 6.0, far above the sourced upper edge. The same project with the actual cost reported
as minus 900,000 read **Green**, with a ratio of 0.053. Nothing about the project improved. The
denominator, budget less actual cost, simply grew past the budget itself.

Two further faces of the same defect were found by independently establishing the domain rather
than by taking the sweep's word for it. An earned value above the budget at completion makes the
remaining work negative, so the ratio is negative and reads Green. A budget at completion below
zero, with an earned value and an actual cost below it, also produced a Green band.

**The correct domain, and where each part of it comes from.** Each is definitional rather than
chosen here. The budget at completion is the authorised total budget of the work and must be
above zero, because there is no cost efficiency that finishes remaining work against a budget of
nothing or less. Earned value is the budgeted value of work performed, so it cannot be below
zero and cannot exceed the value that was budgeted. Actual cost is cost incurred, so it cannot
be below zero.

**The disposition chosen is refusal, not clamping and not a not-applicable.** Clamping was
rejected explicitly: in every case found, pulling an out-of-domain figure back to the nearest
admissible value lands in the favourable direction, which is the harm the defect causes. A
not-applicable disposition was rejected because the quantity is not undefined for the project's
state; the reading offered is simply not a measurement. The module abstains with the malformed
input reason code, reports no ratio at all, and states in the reader's own words that no
substitute figure is used in its place.

**No boundary moved.** The three sourced band edges are byte-identical to the baseline's, and
the suite sweeps the ratio across 1.00 and 1.10 from both sides and asserts the baseline and this
branch agree at every one of those ten points.

Tests added: exact boundary tests from both sides of both sourced edges; a randomised sweep over
600 draws of which 279 landed out of domain, every one of which abstains and 174 of which read
Green or Amber at the baseline; one-unit-out-of-domain cases on each of the four domain rules;
admissible-edge cases that must still compute (an actual cost of exactly zero, an earned value of
exactly zero, an earned value exactly equal to the budget); missing-input tests for each of the
three inputs, both absent and reported as nothing; malformed-input tests over the empty string,
two words, and the three non-finite floats, on each input.

## 3. A1.7 project-status regression evidence

Project status is fused from the voting modules only, so this is measured through
`compute_project`, the same function the upload path calls, on both the baseline code and this
branch.

* With the other voter silent, the baseline fused the whole project to **Green** from an actual
  cost reported below zero. After the correction that project fuses to **no status at all**,
  because no voting module holds an admissible reading on it. There is nothing to fuse, rather
  than a favourable status to fuse.
* Where the other voter already read Red, the fused status is Red before and after. The
  correction removes a false favourable reading; it does not manufacture an unfavourable one.
* Over **300 randomised in-domain projects the fused status is identical before and after**, so
  status moves only where the input was outside its domain.
* The voting set is exactly two modules before and after.

## 4. The exact seven Bucket-3 modules

Derived mechanically from `code_audit/run8_module_classification.csv` by the suite, not typed
from any report: **A1.1, A2.2, A2.3, A4.4, A5.6, A5.7, A6.3**. The seventh is identified by the
fact that its recorded canonical structure is a cost risk quantification, which is a different
analytical method from what the production module of that name computes.

## 5. The six integrated Bucket-3 modules, and what computes versus abstains

| Module | Canonical structure now required | Computes on the structure | Abstains without it |
| --- | --- | --- | --- |
| Line of Balance | locations in sequence, crews, a production rate and a start per line of work | yes, over all 18 project periods the package carries | yes |
| CCPM Buffer Health | a critical chain with its activities and a sized project buffer | yes, over all 36 project periods | yes |
| NCR Rate | an audited nonconformance cohort | yes, over 32 project periods | yes, as before |
| Queueing Theory Bottleneck | entities, service, servers and an observation window | yes, all six projects | yes |
| Agent-Based Supply Chain | agents with rules and an interaction group, and a state history over time | yes, all six projects | yes |
| Environmental Compliance Rate | audited permit condition compliance | yes, over all 36 project periods | yes, as before |

**On the real document corpus all six abstain**, because the corpus carries none of these
structures, and that is the canonical-structure rule doing exactly what it exists to do. The
production path assertion is made on the real upload-and-compute route, not on a direct call.

**No band boundary moved for five of the six.** Each keeps the ladder it carried, applied to a
quantity of the same kind now taken from the real structure: the minimum crew separation in days,
the fever-chart point, the open share of an audited cohort, the at-risk share of the supply
chain, and the audited compliance percentage. The queueing measure is the exception and is stated
as such: its old ladder was a ladder on a share of a look-ahead window, which is not a queue
statistic, so it could not be carried across. **It now reports two levels on one boundary, and
that boundary is definitional**: at a utilisation of one or more the servers cannot keep up with
arrivals, the queue has no steady state and waiting grows without bound. No source was found for
a utilisation at which a project queue becomes a warning rather than a fact, and none was
invented, so there is no second boundary. The measured mean and ninetieth percentile waits are
carried on the finding so a reader sees the queue and not only a colour.

Independent oracles: the separation is re-derived from the two lines' rates and starts by the
stated geometry; the buffer sizing is checked against 1.645 times the root sum of the member
activities' PERT variances, which is a property of the buffer and not of the module; the queue
utilisation is checked against the package's per-server utilisations, which are built a different
way, from each server's busy time; the agent states are counted from the state history; the
compliance rate is the share of assessed conditions found compliant. **None of these takes a
production output as its expectation and none copies a production formula.**

Absent and malformed structure: every one of the six abstains on a fully reported project that
carries every scalar the platform can extract, on an empty structure, on a structure that is not
a structure, on a structure reported as nothing, and on between two and four hand-built malformed
cases each. The four that previously computed a proxy name the absent canonical structure as the
reason, which is a different reason code from a missing figure.

`code_audit/run10b_bucket3_integration.csv` carries the row-by-row record.

## 6. The seventh module: the Monte Carlo disposition

**Disposition A was chosen: the production forecast already has its own dedicated verified
fixture family and therefore does NOT consume the bottom-up Bucket-3 cost register.**

Why A rather than B. The two are different analytical methods and neither is an oracle for the
other. The production module forecasts from a budget at completion, a cost performance index, a
schedule performance index and a document risk score, and Run 10 built it a dedicated
production-contract fixture family with closed-form analytic means and a real sampling-error
acceptance rule. The Bucket-3 structure is a bottom-up triangular cost build-up over cost
elements and Bernoulli risk events, which is a different model of a different thing. Registering
the bottom-up family as its own production module is outside this run's authorisation, so under
the owner's own instruction it stays a validated synthetic and future analytical family and is
documented rather than registered.

What is asserted rather than promised: the production module is not in the canonical-structure
contract list; no cost register asset is named anywhere in the production layer; the module still
computes from budget, indices and document risk exactly as before; an actual cost and an earned
value handed to it change nothing, because it reads neither; and a cost register handed to it is
simply not read, so no second method is smuggled in under the same name.

## 7. The exact two Bucket-4 modules, and 8. their leakage controls

Derived mechanically: **A5.4 Scenario Modeling** and **B2.19 CRITIC-TOPSIS**.

Scenario Modeling now takes a decision problem: the actions open to the project, the scenarios
they play out under, and the probability of each. It computes the probability weighted
expectation of each action, chooses the one with the smallest expected cost, and places that
action's worst scenario against the budget, which is the quantity its existing ladder always
read. CRITIC-TOPSIS now takes a decision matrix of more than one alternative scored against
criteria that each state which direction is better. It computes the weights the way the method
defines them, across the alternatives, which removes the degeneracy Run 8 recorded: with one
alternative a criterion equal to the mean of that project's three carried a weight of exactly
zero and dropped out of its own decision. Every weight is now above zero and each matches the
weight the package recorded to the places it records, and the alternative ranked first is the one
the package records.

Leakage controls, each asserted separately on both modules:

* **The locked holdout is refused outright.** Material marked as the locked split produces an
  abstention, never a reading. The whole purpose of locking it is that nothing consults it.
* **Only the development and validation splits are readable**, and material that does not say
  which split it belongs to is refused rather than assumed readable.
* **A version is required.** Material that does not say which package version produced it is
  refused, because a result taken from it could not be interpreted later.
* **No self-training.** If the project being assessed is itself in the reference population it
  would be compared against, the module refuses, so nothing is compared with itself.
* **The reference material is read-only.** The loader hands back frozen records and a write
  through one raises, which is asserted rather than assumed.
* Each result records which decision object and which asset version produced it.

An injection proof accompanies these: with the lock rule deliberately removed the holdout becomes
readable, so the checks are reading the shipped guard rather than a description of it, and with
the rule restored it is locked again.

`code_audit/run10b_bucket4_integration.csv` carries the record.

## 9. The exact two Bucket-5 modules

Derived mechanically: **A3.1 Reference Class Forecasting** and **A5.1 DSM Rework Propagation**.
Both abstain unconditionally, on an empty input and on a fully reported project; neither votes;
neither was given a canonical structure by this run, so nothing here can reactivate them. The
eight concept-only modules remain refused before their formula function is reached. Synthetic
fixtures for both remain available for future evaluation and are untouched.

## 10. The other seven neighbour defects

All seven were reproduced against the current code and every one still stands. None was fixed,
because none is one of the six Bucket-3 or two Bucket-4 modules being integrated and none had to
be corrected for a valid integration. `code_audit/run10b_neighbour_findings.csv` carries the
module, the defect class, the exact reproducer, the scope decision and the status impact. In
summary: Budget Execution Rate, S-Curve Deviation, Inflation Adjustment Index (twice, once for an
out-of-domain reading and once for an improvement on removed evidence), Sensitivity Analysis,
Tornado Risk Ranking and FAR Threshold Monitor. **All seven are non-voting and excluded from
category rollup, project status fusion, recommendation text, courses of action and the decision
card, so none can move a project's status. All seven are visible on the Signal Ledger, which is
participant-reachable, so the readings themselves are wrong where the defect fires.**

## 11. Synthetic and operational separation

* Every structure the adapters produce carries `data_origin = SYNTHETIC_RESEARCH_FIXTURE` and
  `not_for_empirical_validation = true`, asserted on all eight structure kinds.
* **No file under `server/app/` names the fixture root, the fixture package, or the programme
  version.** This is asserted by walking every application source file, so operational execution
  has no path through which it could fall back to a research fixture.
* The production canonical layer opens no file at all. It takes structures off the caller's
  signal inputs exactly as it takes scalars, which is what makes the separation structural rather
  than declared.
* The adapters live under `server/tests/`, which the application imports nothing from.
* The locked holdout cannot enter any computation, as above.
* No synthetic asset was inserted into production Postgres; production Postgres was not accessed.
* Participant study scenarios remain separately versioned and untouched.

## 12. Voting and status protection

Exactly two modules vote before and after. Every integrated module is asserted individually to be
outside the voting set. The strongest form of the guarantee is asserted directly: the same
project computed with and without **every** structure this run integrated fuses to the same
project status, with the same categories voting, and the only modules that gain a reading are
exactly the six given a structure, with no module losing one.

## 13. Participant-surface regression

`tests.html`: **51 of 51 assertions pass** in headless Chromium. `tests_render.html`: **286 of
287 checks pass**; the single non-passing check is number 264, which requires a signed-in session
token against a running server and reports that requirement as its own result. It is an
infrastructure precondition of the offline harness, not a regression, and no browser asset was
touched by this run, which git confirms.

The participant-visible change this run does make is stated plainly rather than minimised. Four
advisory modules that used to show a proxy reading on the Signal Ledger now show an abstention
with a sentence naming the structure that is missing. That is the canonical-structure rule the
owner's Gate 3 requires, applied to non-voting advisory modules, and it follows the precedent Run
10 set for the criticality module. Nothing else moved: not the preliminary and final decision
sequence, not module labels, not the project-status display, not recommendation text, not the
decision card, not courses of action, not the consent or research flow.

## 14. Test mutation proof

Every new expectation was proved capable of failing. The voter suite carries seven perturbations
plus a real injection into the shipped module: a planned-efficiency boundary of 99 changes the
module's answer, then is restored and the band returns to where the sources put it. The
integration suite carries seven perturbations of the structures themselves, each derived so the
correct answer is known: moving the following line ten days later moves the separation by exactly
ten days; halving the servers changes the utilisation; marking every agent disrupted takes the
at-risk share to one; a fully consumed buffer reads a hundred per cent consumed. Plus the
leakage injection described above. **Every injection was confirmed to alter the bytes or the
object it claimed to alter before any red or green was believed**, including a byte-length
comparison of the shipped module file against the pinned baseline.

The strict harness keeps its anchored result-line rule and its nonzero-exit rule, unchanged and
unloosened, and the Run 10 harness failure proof still runs green against all four failure modes.

## 15. Simulation-version transition

sim-2026.08-v4 to **sim-2026.08-v5**. sim-2026.07-v1, sim-2026.08-v2, sim-2026.08-v3 and
sim-2026.08-v4 all remain in the freeze record as historical audit baselines for results already
collected under them, and a suite asserts each is still present in the file rather than
overwritten. Three suites that tracked the previous stamp were restated with their original
reason preserved beside the new assertion.

## 16. Complete suite results

Pre-change baseline on merged main: 69 suites, 5310 of 5310. After this run: **71 suites, 5627 of
5627, all green**, each suite against its own freshly migrated database. Two suites are new
(`test_run10b_a1_7_domain.py`, 101 checks; `test_run10b_canonical_integration.py`, 178 checks) and
six were restated rather than deleted or loosened: the validate-seven suite, the known-answer
suite, the fix-now-defects suite, the retest-and-classify suite, the state-protection suite and
the version assertions. Every restatement carries the original finding as the recorded reason.

## 17. Guarantees

**Verified.** A1.7 no longer returns a favourable status for invalid-domain input, and does not
return any status for it. The voting set is exactly two. The six ready modules use their actual
canonical structures and abstain when those are absent. The production forecast is not replaced.
The seventh classification is explicitly disposed of. Both reference-object modules integrate
through versioned, split-disciplined, leakage-guarded objects. Both Bucket-5 modules remain
disabled. Synthetic fixtures cannot become operational evidence by any path in the application.
Every new check is proved capable of failing. The full suite passes on merged main.

**Partly met.** The no-participant-visible-change guarantee, in the precise sense set out in
section 13: no redesign, no relabelling, no status change, but four advisory ledger rows now read
as abstentions instead of proxy findings. This is the intended effect of the rule the run was
told to enforce, and it is recorded here rather than absorbed silently.

**Not met.** Nothing in this run's acceptance criteria is unmet. The seven neighbour defects are
outstanding by instruction rather than by failure.

## 18. Remaining owner decisions

1. Whether the bottom-up triangular cost-risk method should become a separately named, separately
   registered production module. It is a validated synthetic analytical family today and needs an
   authorisation to become anything more.
2. Whether the seven neighbour defects are authorised for correction. They are the same class as
   the one fixed here and none of them can move project status, but each is wrong on the ledger.
3. Whether the queueing measure's single definitional boundary is acceptable as a two-level band,
   or whether a second boundary should be sought from a source before that module reports a
   colour at all.
4. Whether the four modules that now abstain on the real corpus should carry a corpus-gap note on
   the ledger, which would be a participant-surface change and is not authorised here.
5. Three items carried forward and still open: the dead control-chart penalty in the forecast
   module, the registry canonical name reading "Monte Carlo EAC" while the programme prose says
   "Monte Carlo EAC Forecast", and the two prior-run audit artefacts that are rewritten by their
   own suites on every execution.

## 19. Exact next-session requirements

Run the complete suite first and record **71 suites and 5627 checks** as the baseline. Then, in
order: the seven neighbour defects, if authorised, each with a baseline reproducer, an
independently derived domain and a mutation proof, on the pattern of section 2. Then the three
carried-forward items in 18.5. Do not reopen A1.7, the six canonical integrations or the two
reference-object integrations unless a regression test proves one is broken. The bottom-up
triangular family must not be given the production forecast's identity under any circumstances.
