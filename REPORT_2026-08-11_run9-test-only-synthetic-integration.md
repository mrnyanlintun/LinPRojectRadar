Run 9 — Test-Only Synthetic Integration

Harness false-clean risk: closed
Alias joins: 11/11 automatic
Normal interpreter changed: no
lxml installed in normal interpreter: no
Read-only fixture schemas: pass
Independent recomputations: pass
Known-answer tests: pass
Abstention tests: pass
Voting changed: no
Activation changed: no
Participant-visible change: no
Production code changed: no

Scope note. Everything below is a test result over synthetic research fixtures. No synthetic
record touches a production project, a participant package, a project status, a recommendation
or a decision card. Synthetic data is not empirical evidence and nothing here validates a
module, a band or a threshold.

## 1. Permissions exercised

Read and wrote inside the repository only. Created a branch, committed, merged and pushed.
Ran Python, the full server suite and the suite runner. Created and deleted discarded scratch
test files under server/tools for the fault-injection proof, and scratch records under the
temporary directory for the malformed-input cases. Did not open production Postgres, did not
use production credentials, did not apply a migration, did not change a production algorithm,
and did not create any temporary generator environment (see section 4).

## 2. Harness correction and fault-injection proof

Two defects were fixed, in server/tools/test_run5_export.py and server/run_all_suites.sh.

The Run 5 export suite ended with `print(f"\n{PASSED} passed, {FAILED} failed")`. It now prints
the repository's canonical line, `RESULT: <passed>/<total> checks passed`.

The runner had three weaknesses. It accepted any line containing "RESULT:" followed by a
fraction anywhere in the output; it also grepped for a bare `^[0-9]+/[0-9]+` prose form into an
unused variable; and it discarded each suite's exit code entirely, so a suite that printed a
green result line and then died would have been recorded as ok. The runner now matches only
`^RESULT: N/M( checks passed)?$`, treats the absence of that line as a failure naming the suite
and the exit code, and fails a suite whose result line is green but whose exit code is nonzero.
It does not accept prose summaries.

Two suites, test_run3_adapter.py and test_unbounded_schedule.py, print `RESULT: N/M` without the
trailing words; the accepted pattern admits both canonical forms and nothing else. This was found
by the strict pattern itself on the first run after the change.

The proof used a discarded scratch suite, server/tools/test_zz_scratch_probe.py, created and
deleted within the run. Results are in code_audit/run9_harness_failure_proof.csv:

- control, canonical green line, exit 0: runner exit 0, suite listed ok.
- prose summary "34 passed, 0 failed", exit 0: runner exit 1, names the suite, NO CANONICAL
  RESULT LINE.
- reported failure, RESULT: 1/2, exit 1: runner exit 1, names the suite and 1/2.
- green line RESULT: 2/2 with exit 3: runner exit 1, names the suite and "2/2 but exit 3".
- crash with no output, exit nonzero: runner exit 1, names the suite.
- restored: scratch suite deleted, Run 5 returns 34/34, complete suite green.

## 3. Alias overlay and the two new mappings

Both missing modules were missing aliases, not missing assets. Every file each module needs is
present in the staged v0.2 package, and the test-only importer loads all of them. No stop
condition was hit here.

The overlay is research_fixtures/synthetic/module_id_aliases_overlay.csv, columns
repository_module_id, synthetic_module_id, module_name, category_number, category_name, source,
effective_version, plus primary_files so the join reaches assets rather than stopping at an
identifier. It adds exactly two rows and edits nothing in the package.

- A1.1 Monte Carlo EAC to synthetic 1.1, category 1 Cost Forecasting, resolving to
  cost_risk_events.csv, cost_elements.csv, cost_correlations.csv and cost_risk_ground_truth.csv
  in package A.
- A5.4 Scenario Modeling to synthetic 5.4, category 5 System Dynamics and Complexity, resolving
  to the six decision objects in package B, B3.

Derivation, stated plainly because one half of it is weaker than the other. Category 5 rows in
the package alias table preserve the suffix without exception (5.1 to A5.1, 5.6 to A5.6, 5.7 to
A5.7, 5.8 to A5.8), so 5.4 for A5.4 follows the table's own rule and collides with nothing.
Category 1 has no row anywhere in the package, so 1.1 for A1.1 is minted by the overlay in the
package's taxonomy, taking the category from the merged v0.1 reconciliation which recorded this
module as category 1 Cost Forecasting. The overlay marks both rows source run9_overlay_derived
so the minted identifier is never mistaken for a package-supplied one.

Verified in the suite: one-to-one in both directions across the combined table of 41 modules; no
duplicate repository identifier; no duplicate synthetic identifier; all 11 Run 8 modules resolve
by identifier with every named asset present on disk; no test performs a name-only match, and the
resolver offers no name-matching function at all; the package alias table's sha256 still equals
its entry in the package CHECKSUMS.sha256 file. See code_audit/run9_alias_overlay_verification.csv.

## 4. Isolated lxml environment decision

No temporary generator environment was created and lxml was not installed. Regeneration was
unnecessary: this run reads the staged package and never rewrites it, and the only workbook in
the package, package_summary.xlsx, is not read by any test here. `import lxml` in the normal
interpreter still fails, which is the state the previous runs required. No entry was added to the
application requirements lock and no .gitignore entry was needed.

## 5. Test-only importer and schema design

server/tests/synthetic_fixtures/ holds importers, schemas, validators, known_answers and
abstention_cases. The importer, importers/fixture_loader.py:

- resolves every path inside the staged v0.2 package and refuses anything that escapes it;
- returns frozen records and frozen tables, so a test cannot edit a fixture and assert on its
  own edit;
- rejects any record whose data_origin is not SYNTHETIC_RESEARCH_FIXTURE or whose
  not_for_empirical_validation is not true;
- enforces primary keys and offers an explicit foreign-key check;
- carries programme version, package version, generator version and seed with every table;
- resolves modules by identifier through the package alias table, the package asset map and the
  Run 9 overlay, and locates each asset by the files that exist on disk rather than trusting the
  map's word;
- names no database, no network client and no production module anywhere in its source, and
  contains no write call, both asserted by the suite. There is no fallback to production data
  because there is no production path in the file.

Two provenance gaps were found and are handled explicitly rather than waved through. The package
manifests carry no data_origin column, and the reference population's ground_truth_model.json
carries no data_origin marker at all; both are read through separate metadata loaders that are
never used for data records, and the gap in the JSON model is reported here.

## 6. Independent recomputations

Full detail in code_audit/run9_validator_gap_recomputations.csv (703 rows). The stored
validator's 681 checks were not relied on.

A. NCR, all 36 project-period cutoffs, all ten stored quantities recomputed from raw events and
audits and equal to the stored ground truth: ncr_issued_to_date, ncr_closed_to_date,
ncr_open_at_cutoff, ncr_overdue_at_cutoff, cumulative_inspections,
ncr_incidence_per_100_inspections, closure_ratio, open_ratio, overdue_open_ratio,
mean_open_age_days. The cutoff is the period end date, established by recomputation rather than
assumed: the status date does not reproduce the stored counts and the period end does, exactly,
for all 360 quantities. Event identity holds, no event closes before it is issued, no due date
precedes issue, and no event issued after a cutoff is admitted at that cutoff. The fixture models
no reopening: there is no reopen column, so reopen timing is verified as absent rather than
asserted as correct.

B. Environmental compliance, all 36 cutoffs. The package stores eight quantities, not six, and
all eight were recomputed and matched: applicable_requirements, applicable_requirements_assessed,
compliant_requirements, noncompliant_requirements, unassessed_requirements,
environmental_compliance_rate, severe_noncompliances, overdue_corrective_actions. Applicability
is by the requirement's own applicable flag and effective date against the cutoff; assessed
excludes NOT_ASSESSED and NOT_APPLICABLE results; the rate's denominator is the assessed set and
never exceeds the applicable set; compliant plus noncompliant equals assessed in every period;
severe counts CRITICAL and HIGH; overdue corrective actions accumulate to the cutoff rather than
resetting each period, which is what the stored values require.

C. CCPM. Every buffer recomputed as 1.645 times the square root of the sum of PERT variances of
its declared chain activities, taken from the three-point estimates in schedule_activities.csv.
All 18 chains and all 108 buffer rows agree. Every buffer joins exactly one declared chain, every
chain activity exists, every activity's own chain field agrees with the chain it is declared in,
project and feeding buffers are both present and distinguishable, and no chain is sized at a flat
fifteen per cent of its duration.

D. Agent rules. All 576 agent-state rows replayed from the rule table. Every referenced rule
exists, every condition is machine-readable JSON with a recognised predicate, exactly one branch
is selected for every row, the selected branch equals the stored branch in all 576, and the twelve
stored branch application counts recompute exactly from the raw states. No prose-only rule is
consumed.

E. DSM package boundary. Verified from the files on disk: every dsm_*.csv found by walking the
package sits in package A, each appears in the package A manifest, and the node table is
project-specific rather than one global matrix. The alias table was not used to establish this.

F. Numerical models. All 12 solved independently with scipy HiGHS from the stored objective
vector, coefficient matrix, right-hand sides, bounds and integrality flags. Solver status,
objective value and decision vector match the stored ground truth in all 12. The solver written
here supports LE, GE and EQ and integer variables; the fixture as staged contains only LE
constraints, minimisation and continuous variables, and no infeasible or unbounded case, so those
paths are supported but unexercised by the data.

G. Leakage, over all three splits present (development 216, validation 72, locked holdout 72; no
participant stimulus split is present in the package). No project-identifier overlap between any
pair of splits; every project in exactly one split with the manifest and the project row agreeing;
no duplicate feature vector; no near-duplicate pair across any split boundary under a normalised
distance threshold; every analogous pair drawn from the development split, checked over all 120
pairs rather than holdout to holdout only; no outcome column reused as a feature; every stored
analog outcome equal to that analog's own outcome row; no repeated record hash.

H. Module joins. All 11 join automatically by identifier: seven Bucket 3, two Bucket 4, two
Bucket 5.

Disagreement found and not resolved. Two stored DSM quantities do not reproduce.
First, in 6 of 18 first-order cases, all of them period three rows, the stored cumulative impact
of a node with a single inbound edge from the seed sits about one per cent below the seed impact
times that edge strength, which no reading of the edge table explains.
Second, the stored impacted node count differs from the number of positively impacted non-seed
nodes in 11 of 36 rows, eight lower and three higher.
Neither can be resolved without editing the synthetic package, which was not done. The DSM
oracle therefore asserts only what the fixture unambiguously supplies and the disagreement is
recorded as a disagreement in code_audit/run9_known_answer_results.csv.

Observed characteristic, reported not resolved. The stored Monte Carlo mean total cost sits 0.84
to 1.00 per cent above the analytic mean of the same Beta-PERT structure in all six projects. A
five thousand draw mean should straddle the analytic mean, so a one-sided bias of that size in
every project suggests the sampler is not the Beta-PERT the columns describe. The known-answer
test states its tolerance openly at one and a half per cent rather than presenting an
approximate agreement as an exact one.

## 7. Module test table

| Module | Name | Bucket | Synthetic id | Independent oracle | Expectations | Verdict |
|---|---|---|---|---|---|---|
| A1.1 | Monte Carlo EAC | 3 | 1.1 overlay | analytic Beta-PERT mean, quantile ordering | 12 | pass, with the bias noted above |
| A2.2 | Line of Balance | 3 | 2.2 | production rates from work packages, hand-derived line intersection | 162 | pass |
| A2.3 | CCPM Buffer Health | 3 | 2.3 | 1.645 root sum of PERT variances | 18 | pass |
| A3.1 | Reference Class Forecasting | 5 | 3.1 | class coverage, class key from attributes, documented cost generator | 3 | pass |
| A4.4 | NCR Rate | 3 | 4.4 | cutoff replay from raw events | 360 | pass |
| A5.1 | DSM Rework Propagation | 5 | 5.1 | edge and seed structural identities | 3 | pass; two stored quantities disagree, recorded |
| A5.4 | Scenario Modeling | 4 | 5.4 overlay | probability weighted expectation | 372 | pass |
| A5.6 | Queueing Theory Bottleneck | 3 | 5.6 | statistics recomputed from the event log | 36 | pass |
| A5.7 | Agent-Based Supply Chain | 3 | 5.7 | rule replay over every state row | 12 | pass |
| A6.3 | Environmental Compliance Rate | 3 | 8.8 | cutoff replay from raw assessments | 288 | pass |
| B2.19 | CRITIC-TOPSIS | 4 | 7.19 | CRITIC definition and TOPSIS closeness | 72 | pass |

No expectation in this table was obtained by running a module and recording its output, and no
production formula was copied into an oracle. Each oracle was proved able to fail: the suite
perturbs one derived expectation per module and asserts the comparison then fails, and asserts
the unperturbed expectation passes.

Two derivations are worth stating because they were established by recomputation rather than
assumed: the CRITIC weights reproduce exactly under min-max normalisation, while the TOPSIS
ranking on top of them reproduces only under vector normalisation, and the queue throughput and
utilisation denominators are the horizon measured from day zero, not from the first arrival.

## 8. Abstention and refusal results

For each of the eleven modules the importer was offered a missing asset, a wrong package, an
invalid data_origin, an invalid not_for_empirical_validation and a malformed asset. Every case was
refused or rejected, and no production call was made in any of them. See
code_audit/run9_abstention_results.csv.

## 9. Bucket 5 remains disabled

A3.1 Reference Class Forecasting and A5.1 DSM Rework Propagation were driven directly with fifty
randomised input dictionaries each. Both abstain on every one, with insufficient_data set and no
status colour, and neither is in the voting set. Loading their synthetic fixtures changed nothing
about that: nothing in this run activates a module, and the synthetic assets are reachable only
from the test-only importer.

## 10. Production hash and participant surface

- server/app tree digest 73099de7e124dff4a1d4f0231ffdfe3a1af5d7522cb71b02de105caea1d58153, and
  `git diff origin/main -- server/app` is empty.
- assets tree digest b2b27d8b803a1dc83ffc0f55e1cb1334499d8d4980a82de83078c41c5e690526, and
  `git diff origin/main -- assets` is empty.
- No production database model and no migration changed; no migration was applied; 0020 through
  0025 remain unapplied.
- The voting set is unchanged at two modules and the disabled concept-only set unchanged at eight,
  both asserted in the suite.
- No participant-visible route, template or export was touched, so no participant-visible output
  can change. The browser infrastructure was not driven: with the production tree byte-identical
  to origin/main, a rendered page cannot differ, and a browser pass would have added no evidence
  beyond the diff.

See code_audit/run9_no_operational_effect.csv.

## 11. Complete suite results

Pre-change, on the recorded commit 95b0a28: 64 suites, 4,612 of 4,612 checks, and the runner
failed with tools/test_run5_export.py reporting NO RESULT LINE, which is the defect this run
was asked to close.

Post-change, on merged main: 65 suites including the new Run 9 suite, all green, with Run 9
contributing 84 of 84 checks and Run 5 returning 34 of 34 through the canonical line.

## 12. Guarantees

Verified: the harness cannot accept a suite with no canonical result line, a suite that crashes,
or a suite that exits nonzero, and the runner names the suite in each case. All eleven module
joins are automatic by identifier. Monte Carlo EAC and Scenario Modeling need no manual join.
lxml is not in the normal interpreter. The fixture layer is read-only, refuses foreign origins
and never reaches production data. Recomputations A, B, C, D, E, F, G and H pass. Every new check
is proved able to fail. Both Bucket 5 modules remain disabled and abstaining. No voting,
activation, production-code, production-database or participant-visible change occurred.

Partly met: the environmental gap was specified as six quantities and the package stores eight;
all eight were recomputed, so the requirement is exceeded in substance but the count in the
instruction does not match the fixture. The numerical model checks support GE and EQ relations and
integrality, but the staged data exercises none of them.

Not met: the DSM stored propagation vector and impacted node count are not reproducible from the
staged edge table, so DSM ground truth is not independently confirmed. The Monte Carlo mean is
confirmed only to within one and a half per cent and shows a consistent one-sided bias.

## 13. Remaining owner decisions

1. The synthetic identifier 1.1 for Monte Carlo EAC is minted by this overlay because the package
   carries no category 1 row. Confirm it, or have the next package version issue the identifier.
2. The DSM disagreements need a decision: correct the package, or record the DSM ground truth as
   advisory and leave A5.1 abstaining on that basis.
3. The Monte Carlo sampler's one-sided bias against its own stated Beta-PERT structure needs the
   same decision.
4. ground_truth_model.json carries no data_origin marker; every other asset does.
5. Nothing here justifies activating any module or restoring any vote, and this run makes no such
   recommendation.
