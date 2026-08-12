Run 14 - Targeted Remediation, Anomaly Validation and Disabled-Method Functional Tests
Starting commit: ed762bf
Ending commit: PENDING_MERGE
Previous simulation version: sim-2026.08-v7
New simulation version: sim-2026.08-v8
Synthetic package: OG-SYNTH-0.3, unchanged and not reingested
Participant package: og-participant-2026.08-v1, unchanged
RUN-13 MISMATCH MODULES: 8/8 identified
MISMATCH modules fixed: 8/8
MISMATCH modules post-fix MATCH: 8/8
RUN-13 NOT_TESTABLE MODULES: 2/2 identified
Anomaly detectors tested: 2/2
Anomaly detection function verified: 2/2
Anomaly detectors failed: 0/2
Anomaly detectors inconclusive: 0/2
DISABLED MODULES: 8/8 identified
Disabled methods functionally tested: 8/8
WORKS: 8
DOES_NOT_WORK: 0
NOT_IMPLEMENTED: 0
NOT_TESTABLE: 0
Disabled methods activated in production: 0
Voting set: 2
Expected: 2
Production Postgres accessed: no
Participant-visible decision sequence changed: no
Full regression suite: 81 suites, 6569/6569

A ninth production module was corrected. It was not in the eight. It was found by this run's
own dependent sweep over the validator that the eight required, and it is reported in section 6.

---

## 1. Handoff audit

`T6_HANDOFF.md` was compared against the committed reports and the git history through the Run 13
merge. The Run 13 entry names ending commit `515a972`, merged as `46a3f8f`, a baseline of 78
suites and 6290 checks, and the four evidence files. All four exist on disk under the names the
entry gives, the two commits exist in history in that order, and `ed762bf` follows them recording
the merge in the report and the entry. The baseline suite run at the head of this session
reproduced 78 suites and 6290 of 6290 exactly. **No chronological entry was missing and nothing
was repaired, because there was nothing to repair.** One naming discrepancy is recorded rather
than fixed: several prompts refer to a `COMMON_PREAMBLE.md` and no such file exists in this
repository, and never has according to the history.

## 2. The Run 13 scope, derived mechanically

Every module list in this run is read from `code_audit/run13_101_module_evidence.csv` at test
time. Nothing is transcribed from a prompt. The `factual_result` column partitions the hundred
and one registered modules into 83 MATCH, 8 MISMATCH, 8 DISABLED_AS_DESIGNED and 2 NOT_TESTABLE.
The three non-matching populations are disjoint, so the run's scope is eighteen unique modules,
recorded in `code_audit/run14_scope.csv`.

## 3. The exact eight mismatch modules

| Module | Name | Defect class |
|---|---|---|
| A2.11 | Critical Path Index | out-of-domain favourable banding |
| A3.2 | Contingency Burn Rate | out-of-domain favourable banding |
| A3.3 | Labor Productivity Index | out-of-domain favourable banding |
| A3.5 | Overhead Absorption Rate | out-of-domain favourable banding AND missing evidence improves the reading |
| A5.4 | Scenario Modeling | canonical method replaced by proxy |
| A5.8 | Discrete Event Simulation | out-of-domain favourable banding |
| B2.19 | CRITIC-TOPSIS | canonical method replaced by proxy |
| C1.6 | Cross-document Consistency Score | missing evidence improves the reading |

None of the eight votes. None became voting.

## 4. Nine occurrences across eight modules

The anomaly file carries nine defect rows against these eight ids: five banding, two missingness,
two canonical method. **The overlapping module is A3.5, Overhead Absorption Rate**, which carries
one banding occurrence and one missingness occurrence. It is not a coincidence that one module
carried both, and the reason is in section 5: in A3.5 the two defects are the same line of code
read from two directions. The reconciliation is asserted in the suite from the evidence file, so
it cannot drift from the files it describes.

## 5. Before and after, for each of the eight

Every case below was independently reproduced against the shipped code before any change was
made. The full record is `code_audit/run14_mismatch_remediation.csv`.

**The five banding cases.** Run 13's input was the nominal project with the reported percent
complete set to ten thousand. Before: A2.11 Amber to Green, A3.2 Yellow to Green, A3.3 Red to
Green, A3.5 Red to Green, A5.8 Yellow to Green. After: all five abstain, and the reader sentence
says the figure is one the quantity cannot take and that no substitute is used.

**A3.5 missingness.** Before: removing the reported progress moved the reading from Red to
Yellow. After: it abstains, naming the absent required input.

**C1.6 missingness.** Before: removing the reported progress turned Amber to Green, and removing
the budget at completion did the same. After: both stay at Amber.

**A5.4 and B2.19.** Before: with the defining structure removed, each returned a computed Amber
under the canonical method's name. After: each abstains with the reason code
`canonical_decision_structure_absent`, and no combination of single-project figures reaches a
band. The canonical path is untouched and still computes when the structure is present.

Each of the eight was retested on nominal behaviour, the Run 13 reproducer, boundary, domain,
missingness, malformed input, canonical structure, invariants, the real compute path and a
mutation proof. The missingness sweeps are exhaustive rather than sampled: every one of the seven
strict subsets of A3.5's inputs and every one of the hundred and twenty-seven strict subsets of
C1.6's.

## 6. The root cause of the five, and whether the shared-validator hypothesis held

Run 13's hypothesis was that `validate_numeric_fields` bounds values from below only, that no
upper range check exists anywhere, and that banding runs before any domain guard. It was treated
as a hypothesis and checked in the code. **It held, with one correction and one nuance.**

It held: `_range_check` refuses a negative value and returns; there is no upper comparison in it,
and a reported percent complete of ten thousand was accepted at the document boundary and stored,
so the invalid input genuinely reached the analytical layer. Banding does run before any domain
guard in all five modules.

The correction: the claim that no upper range check exists **anywhere** is not right.
`validate_doc_risk_score` has enforced a zero-to-one range on the document risk score at the same
boundaries throughout, and A6.3 already refuses an audited compliance rate above one hundred per
cent rather than clipping it. So the platform already held the principle. What it lacked was the
principle applied per field to the other bounded quantities.

The nuance: it is not one defect at one layer. The value was **storable** because the numeric
contract had no upper end, and it was **read as health** because the analytical preflight only
knew how to refuse a value at or below zero. Fixing either alone leaves the other open, so both
were fixed.

The fix. `field_registry.BOUNDED_MAX_SI_FIELDS` declares the upper end of the domain for the five
fields whose own definition supplies one: the two percent complete figures at one hundred, the
environmental compliance rate at one, and the quality audit and subcontractor compliance scores
at one hundred. Membership of that table is not new: it is the bounded set Run 13's own evidence
builder used when it decided which out-of-domain values counted as findings, so the guard and the
audit that found the defect agree by construction. The document risk score is deliberately absent
because its own guard remains the single authority for its range. **No ceiling was invented for
any quantity whose definition does not supply one**, and the suite asserts that for the cost and
schedule indices, the money fields, the hour figures, the counts and the reference overrun. Both
entry points now refuse rather than clamp, and the shared preflight refuses a declared input
outside its own bound using the existing `malformed_input` reason code, whose documented meaning
already covered a value outside the domain it must lie in. No new string key was introduced.

**Dependent-module regression, and the ninth module.** The changed validator is shared, so every
executable module was swept against every bounded field driven just above its bound, ten times
it, a thousand times it, and to a billion. That sweep found one module outside the eight:
**A3.4, Material Cost Variance**, banded from Red to Yellow on a reported progress a fraction
above one hundred per cent. Run 13 drove that field only to ten thousand, at which A3.4 did not
improve, so it was classified MATCH on a sample that missed the case. It is the same defect on the
same field and it was corrected the same way. This is reported rather than quietly folded in: it
means the Run 13 domain pass sampled where it should have swept.

## 7. The exact two not-testable modules

**A1.2, CUSUM Anomaly Monitor**, and **D1.1, Isolation Forest**. Both are anomaly detection
methods by their registered names and by their code.

## 8. Why Run 13 could not test them

Derived from the evidence file, not assumed. A1.2: the contract dimensions all conform and the
value is reproducible, but no independent numeric oracle exists for the reading, so the value
could be reproduced and not judged; oracle confidence LOW. D1.1: the anomaly threshold constants
are unsourced, so the distance can be reproduced but the band drawn on it cannot be judged against
anything; oracle confidence LOW. In both cases the missing thing is an external standard of
correctness, not a missing input.

## 9. The anomaly-detection validation methodology

Run 13's difficulty cannot be removed by asserting production against itself. What can be
established is whether each implementation behaves as an anomaly detector on data whose labels
exist before the detector runs. The methodological sources are the standard formulations: for
A1.2, the two-sided tabular CUSUM recursion with a reference value, a reference shift and a
decision interval; for D1.1, the isolation forest as an ensemble of randomised isolation trees
scored by mean path length. Detection performance is measured by the standard quantities: false
alarm rate, detection rate, detection delay, average run length in and out of control for the
sequential detector, and score ordering with ROC-AUC, PR-AUC and a confusion matrix at the
shipped threshold for the multivariate one.

## 10. Controlled anomaly fixture design and 11. ground-truth generation

Every case is generated from a seeded process whose parameters define its label. A1.2 uses ten
change-point families, two hundred replicates each: stable, stable and noisier, sudden positive
and negative level shifts, small persistent positive and negative shifts, gradual drift, an
isolated one-period spike, repeated short excursions, and a shift that returns to baseline. The
change point is a property of the generator. D1.1 uses a reference normal population of forty
projects and a separate labelled holdout of a hundred and six cases across nine families:
clean normal, duplicated normal, boundary near-normal, extreme single feature, moderate single
feature, multivariate joint anomaly, unusual feature combination, isolated outlier and small
anomaly cluster. No holdout case appears in the reference population, and the shipped threshold
was not selected on the holdout it is reported against. All fixtures carry
`data_origin = SYNTHETIC_RESEARCH_FIXTURE` and `not_for_empirical_validation = true`, and none of
them enters operational storage. **No production detector output labels anything.**

## 12. CUSUM results

Method fidelity: the two-sided recursion is present in the code, the statistic matches the
recursion recomputed by hand outside production, the zero reset behaves as the method requires,
and the reference shift and decision interval are the conventional half a standard deviation and
five standard deviations.

Detection: both sudden level shifts detected in two hundred of two hundred runs, median delay
three periods, and the arm that breaches matches the direction of the shift every time. A shift
that returns to baseline is detected while it is happening. Gradual drift detected in every run.
The small persistent shifts are detected in 69 per cent and 58.5 per cent of runs and those
numbers are reported as measured.

False alarms: five and eight in two hundred in-control runs of twenty-four periods for the two
stable families. ARL0 estimated at about 390 periods over sixty-period in-control runs, with 29
alarms in two hundred runs. ARL1 for a five-sigma negative shift estimated at 4.28 periods.

**A finding recorded as it fell.** An isolated one-period excursion from 1.00 to 0.70 is detected
in none of two hundred runs. Part of that is the method behaving as defined, since a CUSUM is a
shift detector rather than a spike detector. The rest is the implementation: with the scale held
at the true in-control value instead of estimated from the monitored series, the same excursion is
detected in over ninety of a hundred runs. **The self-estimated scale is inflated by the very
excursion it is meant to judge.**

Parameter sensitivity: at decision intervals of two, three, four, five, six and eight, the false
alarms per hundred were 79, 30, 7, 3, 2 and 0 and the small-shift detections per hundred were 99,
87, 84, 63, 48 and 19. The shipped value of five sits on a real tradeoff, which is precisely why
it needs a source.

## 13. Isolation Forest results

**Method fidelity: MISMATCH, established rather than asserted.** Once the method name is removed
from the source, the portfolio layer contains no tree, no path length, no subsample and no
estimator count, and no randomisation of any kind. What it contains is a per-axis standardised
Euclidean distance from the portfolio centroid over four features. The score is identical on
repeated calls with no seed anywhere, which an ensemble of randomised trees would not be.

Detection, for the method that is actually implemented: ROC-AUC 0.994 and PR-AUC 0.995 over the
hundred and six labelled holdout cases, and ROC-AUC of 1.000 on each of five independently seeded
fixtures. The continuous score orders the two classes well.

At the shipped decision threshold: 56 true positives, 0 false negatives, 14 false positives, 36
true negatives; recall 1.000, precision 0.800, specificity 0.720. Ten of thirty clean normal
holdout cases and four of ten boundary near-normal cases were flagged; no duplicated normal case
was. **The uncalibrated threshold errs toward calling ordinary projects anomalous.** It was not
moved: moving it here would be inventing the calibration this run exists to report the absence
of.

One property of the shipped detector is recorded because it is real: production forms the
centroid, the spread and the threshold from the portfolio that includes the project being scored,
so the reference population is not independent of the case being judged.

## 14 to 17. False positives, recall, delay and curves

Consolidated in sections 12 and 13 and in
`code_audit/run14_anomaly_detector_validation.csv`, which carries them per detector alongside the
fixture design, the leakage guard and the mutation proof.

## 18. Parameter calibration limitations, reported separately

| Module | Method fidelity | Detection function | Parameter basis | Threshold basis |
|---|---|---|---|---|
| A1.2 CUSUM Anomaly Monitor | VERIFIED | VERIFIED | UNCALIBRATED | UNCALIBRATED |
| D1.1 Isolation Forest | MISMATCH | VERIFIED for the implemented method | UNSOURCED | UNSOURCED |

These four columns are not forced to agree and are not translated into a disposition. A1.2's
reference value is fixed at one rather than estimated from an in-control period; its scale is
estimated from the series being monitored; its reference shift and decision interval are
conventional values with no source in this repository; and the amber band at six tenths of the
decision interval has no source at all. D1.1's threshold expression adds a standardised distance
to a sum of raw per-axis standard deviations, which are not the same kind of quantity, and
neither the summation nor the multiplier of one and a half has a source; its four features are
equally weighted with no stated basis; and absent figures are replaced by fixed stand-in values
inside the feature builder, so a missing figure enters the geometry as a value rather than as an
abstention.

## 19 to 22. The eight disabled methods

Derived from the evidence file and confirmed identical to the registry's live disabled set. Each
was tested by calling its own function directly in this process; the registry short circuit was
never touched and was re-asserted intact after every module had been exercised. Full detail in
`code_audit/run14_disabled_method_functional_tests.csv`.

| Module | Name | Implementation state | Method fidelity | Functional verdict |
|---|---|---|---|---|
| A3.8 | Parametric Cost Index | PROXY_ONLY | MISMATCH | WORKS |
| B2.7 | Plithogenic Sets | PARTIAL_IMPLEMENTATION | PARTIAL | WORKS |
| B2.9 | Quantum Probability | PROXY_ONLY | MISMATCH | WORKS |
| B2.20 | Hypersoft Sets | PARTIAL_IMPLEMENTATION | PARTIAL | WORKS |
| B4.1 | Multi-Objective Optimization | PROXY_ONLY | MISMATCH | WORKS |
| B4.2 | Linear Programming | PROXY_ONLY | MISMATCH | WORKS |
| B4.5 | Decision Sensitivity Matrix | PROXY_ONLY | MISMATCH | WORKS |
| B4.6 | Pareto Frontier Analysis | PROXY_ONLY | MISMATCH | WORKS |

**WORKS means the code executes, is deterministic, abstains where it should, and reproduces a
hand-derived known answer. It does not mean the named method is present.** Those are separate
columns because collapsing them would destroy the evidence the owner asked for. Every one of the
eight has a hand-derived known-answer case in the suite, and every one has a mutation proof: a
fault injected into an isolated copy of its own source changes its behaviour, and the production
function is confirmed unchanged afterwards.

What was found per method, against the canonical definition:

**A3.8 Parametric Cost Index.** Canonically a cost estimated from measured driver quantities
through a fitted relationship. What is implemented is the ratio of a cost-index forecast to a
remaining-work forecast, an algebraic identity in two earned-value numbers. It does not move when
every quantity a cost estimating relationship would be built on is changed, which is the property
a parametric method must not have.

**B2.7 Plithogenic Sets.** Genuinely carries an appurtenance degree and a contradiction degree
per attribute, and the aggregation weight is a function of both, which distinguishes it from
ordinary fuzzy scoring. It carries no designated dominant attribute value, which is what a
contradiction degree is defined relative to, and the degrees take exactly three literal values
across the whole input range. It reads a nested earned-value object, so on an ordinary project it
abstains.

**B2.9 Quantum Probability.** The vocabulary is present: square-root amplitudes, a cosine
interference term. The structure is not. The squared amplitudes sum to about 0.86 rather than to
one, so there is no normalised state and the Born rule is not what produces the reported
probabilities; the middle probability is a residual; the interference term is scaled by a bare
constant; and the phase angle takes only the four values a count of three indicators can produce,
so it is a tally rather than a phase. **This is metaphorical weighting in the vocabulary of the
method.**

**B2.20 Hypersoft Sets.** The multi-argument parameter tuple is genuinely present and the mapping
is keyed on it over the Cartesian product of three attribute value sets, which is the structure
that separates a hypersoft set from ordinary fuzzy scoring. Exhausting all twenty-seven reachable
tuples found that the table does not cover the product: two reachable combinations,
a fair cost with poor schedule at medium risk and its mirror, fall silently to a default value of
0.35 rather than to a refusal. The
mapping also returns a scalar where the method maps a tuple to a subset of the universe.

**B4.1 Multi-Objective Optimization.** Three objectives are present, which is the one part of the
definition it satisfies. There is no decision variable, no feasible region and no candidate to
trade off against: it evaluates one point, the project itself, and reports the equally weighted
mean of three normalised indicators. Nothing is optimised.

**B4.2 Linear Programming.** No variables, no objective vector, no constraint matrix, no bounds
and no solver. It computes the cost index a project would need to finish inside its remaining
budget. The infeasible case is determinate, which is the one part of the definition present. An
independently solved known-answer linear program cannot be posed against it, and an unbounded
case cannot exist, because there is no objective to be unbounded.

**B4.5 Decision Sensitivity Matrix.** Nothing is perturbed and nothing is recomputed. The
reported sensitivity is each input's scaled distance from a reference value, shared out as a
percentage; with both indices exactly at their reference the whole share falls to the third
driver, which shows the quantity is a distance and not an influence. The zero-perturbation
control passes trivially because there is no perturbation mechanism at all.

**B4.6 Pareto Frontier Analysis.** Dominance is a relation between alternatives and this module
holds one point. A strictly worse project receives the same dominance verdict as the original,
because nothing is compared. The excluded-dominated, retained-nondominated and permutation-
invariance tests were carried out here against an independently derived nondominated set to show
what the method requires; production has nothing to put against them. That independent derivation
also corrected a hand error made while writing this run's own oracle, which is the point of
having one.

**No KEEP, REMOVE, RETAIN_DISABLED or ACTIVATE conclusion is offered for any of the eight.**

## 23. Mutation and fault proof

For the eight corrected modules: each defect was reproduced red before the fix and is green
after, and a fault injected into an isolated copy of each production function makes the corrected
behaviour disappear. The shared guard itself was mutated by emptying the bounded-field table, at
which all five banding occurrences returned, then restored and re-verified, which proves the
domain sweep passes because of the guard rather than because the inputs never arrive.

For the detectors: suppressing the accumulation stops the CUSUM detecting a small persistent
shift; disabling the threshold comparison stops it detecting a large one; reversing the anomaly
score inverts the multivariate ordering; randomising the labels collapses it to chance; and
removing the per-axis standardisation changes the measured separation.

For the eight disabled methods: a defining-method behaviour was mutated in each, not the disabled
flag, and every one bound.

## 24. Voting and activation protections

Voting set exactly two, A1.7 and A1.8, both cost lineage, neither among the eight corrected. None
of the eight corrected modules votes, so no correction can move a project status through the vote.
The eight disabled modules remain the same eight, still refused by the registry after the whole
functional suite has run them directly. Cost Recovery Status and the single-lineage conflict
semantics are untouched. The participant decision sequence is unchanged. No participant surface,
no route and no storage behaviour was modified. No synthetic fixture entered operational storage.
No production Postgres access occurred and no migration was run outside throwaway SQLite.

## 25 and 26. Regression

Targeted: the eight corrected modules, the ninth found by the dependent sweep, the two detectors,
the eight disabled methods, and every executable module against every bounded field. Six existing
suites required an expectation correction and each carries the reason at the change: three were
frozen-file and scope guards that had to learn Run 14's authorised file list, one pinned the Run 13
inventory to the current simulation stamp when it should pin it to the stamp the inventory was
built at, one asserted a leak marker on a bare English word the analytical layer is entitled to
use, and one section of the Run 8 suite asserted, literal by literal, the two proxies Run 13
recorded as mismatches. That last one is the case the preamble warns about, and the old expected
values are kept in comments as the historical record rather than deleted.

Full suite on merged main: **81 suites, 6569 of 6569, all green**, each against its own freshly
migrated database. Three new suites, 281 checks between them.

## 27. The evidence the owner should use to decide KEEP or REMOVE

For the eight disabled methods: `code_audit/run14_disabled_method_functional_tests.csv` is the
file. Its `implementation_state`, `method_fidelity`, `structure_available` and `limitations`
columns carry what the decision turns on, and `server/tools/test_run14_disabled_method_functional.py`
carries the reasoning behind every cell. For the two detectors:
`code_audit/run14_anomaly_detector_validation.csv`, whose four state columns are deliberately
independent of each other.

## Owner decisions required next

1. **The eight disabled methods.** KEEP, REMOVE or ACTIVATE, per module, on the evidence above.
   Six implement something other than the method they are named for.
2. **D1.1's name.** The module is registered and reported as an isolation forest and is a
   standardised distance detector. Renaming it, replacing it, or stating the substitution openly
   are three different decisions and all three are outside this run's authorisation.
3. **Detector parameters and thresholds.** Whether A1.2's reference value, reference shift and
   decision interval, and D1.1's threshold expression, are to be sourced, or the platform is to
   state that they are not.
4. **A1.2's estimated scale.** Whether the standard deviation should be estimated from a
   designated in-control window rather than from the series being monitored.
5. **The retired earned-value forecast.** A5.4's three-divisor forecast was removed rather than
   renamed or relocated. Whether it should return under a name of its own is a design decision.
6. **The Run 13 domain pass.** It sampled one out-of-domain value per field where a sweep was
   needed, and that is how A3.4 was missed. Whether the other 82 MATCH modules warrant a
   re-sweep on the axes Run 14 swept is an owner decision.
7. All decisions outstanding from Runs 10B, 11 and 12 remain open.
