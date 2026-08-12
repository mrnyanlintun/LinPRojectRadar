Run 10 — Production Remediation and Synthetic Integration
Starting commit: e93a2393f6b48eb94c5273f760fcae98a9731154
Ending commit: PENDING_MERGE
Previous simulation version: sim-2026.08-v3
New simulation version: sim-2026.08-v4
Synthetic package version: OG-SYNTH-0.3
Monte Carlo EAC Forecast fixture: PASS
Monte Carlo permanent mapping: PASS
Bucket-2 corrected: 16/16
Bucket-3 integrated: 0/7
Bucket-4 integrated: 0/2
Bucket-5 still disabled: 2/2
Voting set changed: no
Activation set changed unexpectedly: no
Synthetic/operational separation: PASS
Known-answer tests: PASS
Abstention tests: PASS
Full suite: 5315/5315
Participant-visible change: no
Production Postgres accessed: no

**THIS IS A PARTIAL RUN, AND THE PARTIALITY IS DELIBERATE.** Gates 0, 1, 2 (including the
neighbour sweep), 5, 6, 7, 8, 9, 10 and 11 are complete. Gates 3 and 4, the integration of the
seven project-structure modules and the two reference and decision modules, were NOT started.
They are stated as not done rather than reported thin, and section 21 gives the next session
exactly what it needs to pick them up. Nothing in this run half-integrates a module.

## 1. Handoff-history audit, and repairs

Every committed report since the last handoff entry is represented in `T6_HANDOFF.md`: the
known-answer run, the fix-now run, the retest-and-classify run, the two synthetic package ingest
and closure runs, the test-only synthetic integration run and the v0.3 correction run each have
an entry, and the simulation and synthetic-package version histories are continuous
(sim-2026.08-v2 to v3; OG-SYNTH-0.1 to 0.2 to 0.3). **No repair was needed and none was made.**
Prior entries were appended to, never rewritten.

One naming collision is recorded rather than resolved: the previous session filed its work under
the name "Run 10" in the handoff while the owner's programme numbers this session Run 10. The
entries are distinguished by date, branch and subject, and this run's entry names its own branch
so the two are not confusable.

## 2. The exact sixteen Bucket-2 modules

Derived mechanically from `code_audit/run8_module_classification.csv`, count asserted at 16 in
two separate suites. `code_audit/run10_bucket2_scope.csv` carries the full table with the Run-8
defect, the expected behaviour, the behaviour before this run, the defect class, the production
file and the correction applied.

A1.5 ARIMA CPI Forecast; A1.6 Earned Schedule; A1.11 ICE Ratio; A2.1 PERT Network Criticality;
A2.5 Float Consumption Rate; A2.9 Resource Loading Index; A2.10 Schedule Risk Analysis P80;
A2.11 Critical Path Index; A3.6 Cost Risk Analysis P80; A4.10 Specification Conflict Density;
A5.5 Rework Feedback Loop; A5.8 Discrete Event Simulation; A6.1 Quality Compliance Index;
A6.2 Safety Performance Index; A6.4 Contractor Performance Score; B2.18 MARCOS Ranking.

## 3. The exact seven Bucket-3 modules (scope established, NOT integrated)

A1.1 Monte Carlo EAC; A2.2 Line of Balance; A2.3 CCPM Buffer Health; A4.4 NCR Rate;
A5.6 Queueing Theory Bottleneck; A5.7 Agent-Based Supply Chain; A6.3 Environmental Compliance
Rate. Count asserted at 7. No importer, adapter or integration test was written in this run.

## 4. The exact two Bucket-4 modules (scope established, NOT integrated)

A5.4 Scenario Modeling; B2.19 CRITIC-TOPSIS. Count asserted at 2. No versioned read-only
reference interface was built in this run and no leakage analysis was performed.

## 5. The exact two Bucket-5 modules, still disabled

A3.1 Reference Class Forecasting; A5.1 DSM Rework Propagation. Both abstain unconditionally,
on an empty input and on four different populated inputs including ones carrying the very
structure they would need. Neither votes, neither is in the recommendation, the courses of
action or the decision card. Asserted in `server/tools/test_run10_state_protection.py`.

## 6. The Monte Carlo EAC production contract

Established by reading `server/app/simulation/models_sim.py` and nothing else. The registry's
canonical name is **Monte Carlo EAC**; the owner's prose name "Monte Carlo EAC Forecast" is
carried as a backward-compatible alias rather than substituted for the registry's own name, and
that divergence is recorded here rather than silently reconciled.

Contract, as implemented:

- Inputs actually read: budget at completion; cost performance index; schedule performance
  index; document risk score, clamped to nought and one and defaulting to nought.
- **Inputs the owner's prompt assumed and production does not read: actual cost; earned value;
  any formula-selection rule.** There is no formula selection. One transformation is applied
  unconditionally: mode forecast equals budget over the cost index, the index-based independent
  estimate at completion.
- Spread driver: half the cost shortfall plus three tenths of the schedule shortfall plus a
  fifth of the document risk score, clamped to nought and one.
- Bounds: optimistic is the mode less a tenth of the spread; most likely is the mode;
  pessimistic is the mode plus four tenths of the spread.
- Distribution: **Beta-PERT with lambda four**, sampled as the ratio of two Marsaglia-Tsang gamma
  variates over Box-Muller normals. When the pessimistic and optimistic bounds coincide within a
  billionth, every sample is exactly the mode and the forecast collapses deterministically.
- Correlation: none. One scalar is drawn per iteration, so there is no correlation structure to
  declare, and none is invented for the fixture.
- Truncation: none beyond the support of the distribution itself.
- Generator: mulberry32, unsigned 32-bit, bit-for-bit as the browser runs it. Seed is the first
  four bytes of a hash of scenario identifier and period; participant identifier is excluded.
- Iterations: five thousand. Percentile convention: index based on the ascending sample, floor of
  the quantile times one less than the count, not interpolated. No rounding of the percentiles.
- Abstention: absent budget, cost index or schedule index; a budget not above zero; either index
  not above zero. The removed hundred-unit budget substitution must never return.

**A finding, reported and NOT fixed here.** `monte_carlo_eac` accepts a control-chart breach
penalty and its two supporting figures, and the module wrapper never passes them, so on every
production path that penalty is exactly zero. Wiring it would change what the module emits for
projects with a control-chart history, which is a production change outside the sixteen this run
is authorised to make. It is left for the owner.

## 7. The dedicated fixture family, and how it differs from the triangular family

`research_fixtures/production_contract/monte_carlo_eac_forecast/` holds `contract.json`,
`known_answer_cases.csv`, `known_answer_ground_truth.csv` and `CHECKSUMS.sha256`, generated once
by `tools/derive_mc_eac_fixture.py`. Every number in it is closed-form arithmetic transcribed
from the contract document. **The derivation script does not import, call or read the production
module**, and no production output was recorded as an expected value.

Ten cases span deterministic collapse at two different budgets, a single sampled cost index,
cost-index-driven and cost-and-schedule-index-driven forecasts, stable performance carrying only
document risk, deteriorating performance, strong performance where the spread clamps at nought,
the spread clamped at one, a small budget, and document risk at the top of its domain. Each case
carries budget, both indices, document risk, seed, iteration count, and the ground truth carries
the mode forecast, spread driver, all three bounds, lambda, both shape parameters, the degenerate
flag, the analytic mean, the analytic standard deviation and the deterministic percentiles where
they exist.

**How it differs from the existing family, which is preserved untouched.** The OG-SYNTH-0.3
package family is a bottom-up build-up: triangular cost elements under a Gaussian copula plus
Bernoulli risk events with triangular impacts, drawn on a PCG64 generator. This family is
top-down: a single Beta-PERT over a forecast derived from earned-value indices, drawn on
mulberry32. Different distribution, different level of aggregation, different dependence
assumption, different generator, different seed derivation. Neither is an oracle for the other,
both say so in their own contract file, and a suite check asserts the two declared distributions
differ so a future edit cannot quietly merge them.

## 8. Statistical validation

The analytic Beta-PERT mean is the mode forecast times one plus a twentieth of the spread driver,
and the analytic standard deviation is the square root of three eight-hundredths times the spread
driver times the mode forecast. Both are derived in closed form from the contract, so a real
statistical acceptance test is possible rather than an arbitrary percentage tolerance.

Acceptance rule, fixed before any result was computed: the absolute difference between the
simulated and analytic means must not exceed 3.290526731491896 standard errors, the two-sided
0.001 critical value, which is 0.05 Bonferroni corrected across fifty mean checks in the
programme. Standard error is the simulated standard deviation over the square root of the count.
Run at one thousand, five thousand and twenty thousand samples on three cases. All nine pass;
every row with its analytic expectation, simulated mean, difference, standard error, tolerance
and result is in `code_audit/run10_mc_eac_statistical_acceptance.csv`.

Properties proved: the forecast is finite for every valid input; the fiftieth percentile is at or
below the eightieth, and both at or below the ninetieth on the ordered sample; the same seed and
input reproduce exactly; a worse cost index raises both percentiles and widens the spread; a
worse schedule index widens the spread; doubling the budget doubles the forecast and leaves the
spread driver alone; a zero or negative budget, a zero or negative index, a zero, negative or
fractional iteration count and a bound ordering violation all refuse; and no substitute budget is
returned for a budget of zero, absent or empty.

**Permanent identity.** The v0.3 package already carries authoritative alias-table and asset-map
rows for both A1.1 and A5.4, so neither needs the Run 9 overlay and neither joins on name alone.
The fixture contract carries the permanent repository identifier and the permanent synthetic
identifier in the file itself. All asserted.

Two production guards were added in this gate and are the only production change outside the
sixteen: a positive whole iteration count is required, and the three bounds must be ordered. The
bounds are derived rather than supplied, so the second cannot trip on any accepted input; it
exists so a later edit that makes them settable cannot sample a mis-shaped distribution silently.

## 9. The sixteen corrections, by defect class

**Class one, open input domains, eleven modules.** A reading outside the domain a quantity can
occupy was reaching a band, and in most cases the calmest one. Each now refuses and publishes no
figure. A1.5: a cost performance history containing a reading at or below zero. A1.6: a
completion percentage outside nought to one hundred, and separately the module demanded earned
value, planned value and budget and read none of them, so that requirement is dropped to the two
percentages the arithmetic actually uses. A1.11: a cost index at or below zero, not merely
exactly zero, which had produced a negative completion forecast printed as currency. A2.5: a
negative consumed float, which had added float and read Green. A2.9: negative actual labour
hours. A2.10: a schedule index at or below zero, which had raised inside the division and lost
the entire project result rather than one module's abstention, and a completion outside nought to
one hundred; a negative index had reported the project finishing one thousand and seventy-five
days early and read Green. A2.11 and A5.8: a schedule index at or below zero. A4.10: a document
risk score outside nought to one. A6.1: an audited quality score outside nought to one hundred,
which had reached the participant-visible finding as a hundred and fifty out of a hundred. A6.4:
a rating outside the five-point scale the finding text itself names.

**Class two, the finding text contradicting the figure, one module.** A3.6 hard-coded a leading
plus and then formatted a negative delta, so a forecast below budget printed a plus and a minus
together. The sign now comes from the figure.

**Class three, absence of evidence improving the reading, two modules.** A5.5: an absent count
contributed exactly what a perfect one contributes, so withholding two logs moved the reading
three bands. Both counts are now required and the module abstains without them. Renormalising
over the present terms was considered and refused, because it would still let a project missing
the two highest-risk sources read on the strength of the cost index alone. **The property is
proved over every strict subset of the required evidence, exhaustively, not on a sample: all
three strict subsets abstain, and a reported nought still bands, so a measurement and an absence
are no longer indistinguishable.** A6.2: a count derived from how often safety came up in meeting
records, when no safety report had been uploaded, turned silence into a rate of nought, which
took the module's own cap and read Green with the best safety index the module can award. Four
dispositions are now distinguished: a rate or count from an uploaded record, including a
documented zero over a valid exposure, bands; meeting silence abstains and says so; missing
evidence abstains; a negative rate abstains as malformed.

**Class four, a disposition no input could reach, two modules.** B2.18 set the anti-ideal utility
to one minus the ideal utility, so the two summed to one by construction, the score was bounded
above by a third while the next band up begins at 0.35, and a project at every ideal divided by
zero and scored nothing. **No boundary was moved.** The method's own structure was restored: each
criterion normalised against its own ideal, three weighted sums formed (project, ideal reference,
anti-ideal reference), and the two utility degrees taken as separate ratios rather than as a
number and its complement. All four dispositions are now reachable over an exhausted grid of
sixty-five thousand eight hundred and fifty-six combinations, the score is monotone in each of
the three criteria, and two known answers were derived by hand from the published method before
production was run: 0.798 at every ideal and 0.652 at a mid state.

A2.1 divided an eightieth percentile of a sum of right-skewed durations by a baseline built from
the modes of the same durations, so the two sides were different statistics and no schedule index
could close the gap. **A boundary was not invented to make a healthy reading reachable**, because
that would have left the deeper fault standing: the three activities were the file's own literals
and identical for every project the platform holds, so the index described the file rather than
the project. Canonical criticality needs an activity network with logic and three-point
durations, and the production corpus carries none: the schedule reader assembles a milestone and
activity table with dates and percent complete, with no predecessor logic and no optimistic or
pessimistic duration anywhere. The literal-driven sampling is **removed** rather than gated, and
the module abstains on the absent canonical structure, on the same footing as reference class
forecasting and rework propagation.

## 10. Neighbour-defect sweep

Every live module was probed programmatically over its whole numeric input surface for the two
recurring patterns: an out-of-domain input reading Green, and removing an input improving the
reading. Eight same-class neighbours were found in modules outside the authorised sixteen and
outside the Bucket-3 and Bucket-4 scope. **None was fixed.** Full table in
`code_audit/run10_neighbour_sweep.csv`.

Out-of-domain input reads Green: A1.7 TCPI (negative actual cost); A1.9 Budget Execution Rate
(negative actual cost); A2.6 S-Curve Deviation (negative planned completion); A3.9 Inflation
Adjustment Index (negative current material cost); A5.3 Tornado Diagram (negative document risk);
B3.2 FAR Threshold (negative cost index). Removing evidence improves the reading: A3.9 Inflation
Adjustment Index (completion removed); A5.2 Sensitivity Analysis (document risk removed).

**A1.7 is one of the two modules that vote on project status.** That is the highest-severity item
in this sweep and it is flagged for the owner rather than fixed inside this run's authorisation.

## 11. Bucket-3 integrations

None. Gate 3 was not started.

## 12. Bucket-4 integrations

None. Gate 4 was not started.

## 13. Synthetic and operational separation

Every row of the v0.3 alias table and asset map declares the research origin and refuses
empirical standing, and so does every case in the new forecast fixture family and its contract.
No file under `server/app/` mentions `research_fixtures`, `OG-SYNTH`, `production_contract`,
`SYNTHETIC_RESEARCH_FIXTURE` or a synthetic project identifier, so no production module can reach
a fixture and operational evidence has nothing to fall back to. The frozen v0.2 and v0.3 packages
are both present and unmodified; the bottom-up triangular contract still declares its triangular
distribution and still disclaims being the production oracle. No synthetic data were inserted
into any database, and production Postgres was not accessed at any point.

## 14. Voting and status protection

Recorded before any edit and asserted after: the voting set is exactly A1.7 and A1.8, and it is
unchanged. No module corrected by this run joined it. Every voting module still carries its band
source and the statement of what those citations do not establish is intact. The five modules
held non-voting for unsourced bands are still held, and the eight concept-only modules are still
disabled. Correcting a module did not grant it a vote, and nothing in this run asserts that
known-answer correctness establishes band calibration or that synthetic data establish empirical
field validation.

**Project status did move for some projects, and that is the intended consequence rather than a
surprise.** Fourteen of the sixteen corrected modules now abstain on inputs they previously
banded, so those modules drop out of the ledger for affected projects. None of them votes, so
project status fusion is unaffected by the abstentions themselves.

## 15. Browser and server divergence

Not addressed, by instruction: the consolidated browser and server cleanup remains the next run.
No browser asset, no served page and no participant-facing server module was touched by this run,
and a suite check asserts that the whole diff under `server/app/` lies inside the analytical
layer. The divergences this run **creates** are the sixteen corrections themselves: the browser
still carries the pre-correction arithmetic for all sixteen, including the criticality module,
which still computes in the browser from the same three hard-coded activities. The divergences
this run **preserves** are every one Run 9 and earlier recorded.

## 16. Test-mutation proof

Every check in this run was proved capable of failing, and **every injection was verified to have
altered bytes before its result was believed**.

Gate 1: six mutations. Perturbing the expected optimistic bound, the expected analytic mean and
the expected spread driver each turned the suite red; changing the pessimistic multiplier, the
lambda in either shape parameter and the percentile convention in production each turned it red.
The lambda mutation initially survived, because production does not return its shape parameters;
a check comparing production's percentiles against a reference draw parameterised from the
fixture's own frozen shape parameters was added, after which it fails.

Gate 2: eighteen mutations, in `code_audit/run10_bucket2_mutation_proof.csv`. Removing each of
the fifteen guards individually, restoring the hard-coded plus sign, and restoring the complement
utility each turns the suite red, as do three expectation-side perturbations. Two mutations
survived the first pass and both were treated as suite defects and closed: reverting only the
input requirement in A5.5 was still caught downstream, so the full defect revert is now the
mutation and it fails; and the complement utility in B2.18 was not detected until the two
hand-derived known answers were added.

## 17. Version transition

sim-2026.08-v3 to **sim-2026.08-v4**. The freeze records for sim-2026.08-v2 and sim-2026.08-v3
are preserved verbatim in the module and asserted present by the state-protection suite. The
synthetic package version in use is OG-SYNTH-0.3; OG-SYNTH-0.2 and OG-SYNTH-0.1 are untouched.

Production files changed: `server/app/simulation/models.py`, `models_doc.py`, `models_evm.py`,
`models_ext.py`, `models_fuzzy.py`, `models_sim.py`, and nothing else under `server/app/`.
Fixture and interface files added: the four files of the new forecast fixture family and its
generator. No dependency changed; lxml remains out of the interpreter.

## 18. Complete suite results

Pre-change baseline: 66 suites, 4851 of 4851. After Gate 2: 68 suites, 5230 of 5230. Final,
including the state-protection suite: **70 suites, 5315 of 5315, all green**, each suite against
its own freshly migrated database. The strict harness was proved still effective against all four
failure modes plus a green control; results in `code_audit/run10_harness_failure_proof.csv`.

Four earlier suites asserted behaviour this run corrects, and each was restated rather than
loosened, with the original finding preserved as the reason for the correction: the known-answer
suite's scope guard now carries a separate Run 10 authorised-file set beside Run 7's; the fix-now
suite's criticality block records that Run 10 supersedes one row of it and why; the
retest-and-classify suite's defect assertions for the sixteen are restated as abstentions through
a supersession helper, with every in-domain known answer left untouched; and the simulation
suite's seeding guarantee is read off the forecast module, which is seeded from the same pair
through the same holder. **No assertion was deleted to make a suite pass, and no threshold in any
suite was relaxed.**

## 19. Guarantees

**Verified.** The forecast module has its own production-compatible fixture family; its identity
is permanent and needs no overlay; the bottom-up triangular family remains distinct and untouched;
all sixteen Bucket-2 modules are corrected; both Bucket-5 modules remain disabled; no synthetic
fixture became operational evidence; voting did not expand; every new check is proved capable of
failing; the strict harness remains effective; the complete suite passes; the handoff is current.

**Partly met.** Test discipline: two mutations survived the first pass and both were closed, so
the discipline held only because the mutation pass was run. Browser and server divergence is
recorded but not closed, by instruction.

**Not met.** All seven Bucket-3 modules using their canonical structures or correctly abstaining:
not attempted. Both Bucket-4 modules using versioned reference objects without leakage: not
attempted.

## 20. Owner decisions remaining

1. **A1.7 accepts a negative actual cost and reads Green, and it votes on project status.** Fix
   it, or accept the exposure knowingly. This is the sweep's most serious finding.
2. Seven further same-class neighbours in section 10: authorise as a batch, or leave.
3. The control-chart penalty in the forecast module is accepted by the arithmetic and never
   passed by the wrapper. Wire it, or remove it as dead.
4. The registry canonical name is "Monte Carlo EAC" and the programme prose says "Monte Carlo EAC
   Forecast". Settle which is authoritative; this run kept the registry's and aliased the other.
5. Two prior-run audit artefacts, `code_audit/run9_no_operational_effect.csv` and
   `code_audit/run10_no_operational_effect.csv`, are rewritten by their suites on every execution,
   so a prior run's recorded digest is overwritten by whatever the current tree hashes to. They
   were restored to their committed values here. Decide whether those suites should stop writing.
6. A1.6 now computes for projects that reported progress but no earned value, where it previously
   abstained. It does not vote, so status is unaffected, but more ledger rows will appear.

## 21. Exact next-session requirements

1. Branch from `origin/main` at this run's merge commit. Run the complete suite first and record
   70 suites and 5315 checks as the baseline.
2. **Gate 3, the seven Bucket-3 modules**, derived from the classification CSV and asserted at
   seven: A1.1, A2.2, A2.3, A4.4, A5.6, A5.7, A6.3. For each: name the canonical structure from
   `code_audit/run8_required_project_corpus_specs.csv`; name the v0.3 asset from
   `module_asset_map.csv`; write the smallest importer and adapter; require the structure
   explicitly; abstain when absent; never fabricate a fallback; add known-answer and
   malformed-structure tests; test the real run-and-store path. Produce
   `code_audit/run10_bucket3_integration.csv` with the columns the owner specified. Note that
   A1.1's canonical structure is the bottom-up cost risk register, which is a **different model
   from the production Beta-PERT documented in section 6**, so integrating it means either changing
   what A1.1 computes, which needs authorisation, or abstaining. Resolve that before writing code.
2b. Note for A2.1, now abstaining on the absent activity network: the v0.3 package does carry
   `schedule_activities.csv` and `schedule_dependencies.csv`. A2.1 is not in Bucket 3 and was not
   integrated here, so integrating it needs separate authorisation.
3. **Gate 4, the two Bucket-4 modules**: A5.4 and B2.19, from
   `code_audit/run8_required_reference_decision_specs.csv`. Versioned read-only interface; record
   which reference population or decision object produced each result; prevent train, validation
   and holdout leakage; no module may train on the project it evaluates; no locked holdout
   outcome may enter training. Produce `code_audit/run10_bucket4_integration.csv`.
4. Re-run the state-protection suite unchanged after the integrations. Voting must still be
   exactly A1.7 and A1.8, and Bucket 5 must still be two modules abstaining.
5. Bump to sim-2026.08-v5 if and only if the analytical layer's emissions change again, and
   preserve v2, v3 and v4.
6. Decide the six owner questions in section 20 before the browser and server cleanup run, because
   the A1.7 finding touches a voting module and the browser still carries all sixteen defects.
