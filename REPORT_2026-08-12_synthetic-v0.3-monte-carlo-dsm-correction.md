# Synthetic programme v0.3, Monte Carlo and DSM correction

Synthetic programme version: OG-SYNTH-0.3
Monte Carlo EAC status: PASS
DSM status: PASS
Monte Carlo permanent alias: yes
Scenario Modeling permanent alias: yes
Monte Carlo distribution: triangular marginals on low, most likely and high, with element
dependence induced by a Gaussian copula over the declared correlation matrix, and risk events
modelled as an independent Bernoulli occurrence times a triangular impact
Monte Carlo analytic mean check: pass
Monte Carlo statistical convergence: pass
Monte Carlo reproducibility: pass
DSM first-order recomputation: pass
DSM cumulative recomputation: pass
DSM node-count recomputation: pass
Validator fault injections: 16/16 caught
Programme checksum: PASS
Production code changed: no
Voting changed: no
Activation changed: no
Participant-visible change: no

Scope note. Everything below is a result over synthetic research fixtures. No synthetic record
touches a production project, a participant package, a project status, a recommendation or a
decision card. Synthetic data verifies implementation only. It is not empirical evidence, and
nothing here validates a module, a band or a threshold. The corrected assets were not connected
to production module execution in this run, which the owner's prompt forbade.

## 1. What Run 9 left open

Run 9 recorded two unresolved synthetic ground-truth families and one identity gap.

- Monte Carlo EAC. Across all six synthetic projects the stored mean total cost sat about 0.84
  to 1.00 per cent above an independent analytic Beta-PERT expectation, one-sided in every case.
  Run 9 correctly refused to edit the package to force agreement.
- DSM Rework Propagation. Stored cumulative impact differed from seed times edge strength in 6
  of 18 first-order cases, and the stored impacted-node count disagreed with the positively
  impacted node count in 11 of 36 rows.
- Monte Carlo EAC reached its assets only through the Run 9 alias overlay, because the package
  carried no category one row at all. Scenario Modeling was in the same position.

## 2. Determining the Monte Carlo distribution

The distribution was read out of the generator, not assumed. The v0.2 builder carries the cost
risk family across from v0.1 untouched, so the v0.1 generator is the authority. In its cost risk
model it draws, per project:

- ten cost elements, each `scipy.stats.triang.ppf(u, c=(mode-low)/(high-low), loc=low,
  scale=high-low)`, where `u` is the normal cumulative distribution applied to a correlated
  standard normal draw. That is a triangular marginal under a Gaussian copula.
- six risk events, each an occurrence draw `RNG.random(n) < probability` multiplied by
  `scipy.stats.triang.rvs` over the same low, mode and high parameterisation.
- five thousand iterations, one `numpy.random.default_rng` stream seeded from the programme
  seed, correlation induced through a Cholesky factor of the declared matrix.

There is no Beta-PERT anywhere in the cost risk model. Beta-PERT does appear in the same
generator, but for schedule activity durations, which is a different family; the schedule
fixtures and the cost fixtures were built by different code paths and the Run 9 oracle carried
the schedule family's assumption into the cost family.

The arithmetic settles it. For a triangular variable the expectation is `(a + m + b) / 3`; for
Beta-PERT with lambda four it is `(a + 4m + b) / 6`. The synthetic cost elements are built with
`low = mode * (1 - 0.55s)` and `high = mode * (1 + s)`, so the triangular expectation exceeds
the mode by `0.15 * s * mode` and the Beta-PERT expectation exceeds it by `0.075 * s * mode`.
With the spreads in the package, that difference is between 0.85 and 1.01 per cent of the total,
and it is one-sided by construction because the fixtures are right-skewed. That is the Run 9
finding, exactly.

So the roughly one per cent bias was the oracle, not the generator. Measured against the
triangular expectation the same v0.2 stored means are within 0.05 per cent, which is sampling
noise at five thousand draws. `code_audit/run10_monte_carlo_distribution_gap.csv` carries both
residuals per project for the regenerated v0.3 data.

Gate 3 asked for one governed contract and forbade choosing whichever distribution makes the
stored value pass. The choice here is not a choice between two candidates that both fit: it is
the distribution the code samples, stated in the code, in one family only, with no ambiguity in
comments, schema or historical tests. It is now declared in `cost_elements.csv`,
`cost_risk_events.csv`, `cost_risk_ground_truth.csv`, `monte_carlo_contract.json`, the schema
catalog, the validator and the test suite, which all refer to the same declaration.

One matter is recorded for the owner rather than resolved here. The repository's own Monte Carlo
EAC module forecasts a completion cost from earned value indices through a Beta-PERT over a
single triple derived from the budget and the performance indices. The synthetic family mapped
to it is a bottom-up triangular cost build-up with discrete risk events. Both are legitimate
cost risk models and neither is wrong, but they are not the same model, so this fixture family
is not a drop-in oracle for the production module. `monte_carlo_contract.json` says so in a
field named for the purpose, and section 17 lists it as an owner decision.

## 3. Permanent Monte Carlo and Scenario Modeling identity

Both are now rows in the package's authoritative tables, not in an overlay.

| Repository module id | Synthetic module id | Name | Category | Source in v0.3 |
|---|---|---|---|---|
| A1.1 | 1.1 | Monte Carlo EAC | 1 | module_id_aliases.csv and module_asset_map.csv |
| A5.4 | 5.4 | Scenario Modeling | 5 | module_id_aliases.csv and module_asset_map.csv |

The repository identifiers come from the registry in `assets/js/categories.js`, and the suite
reads them out of that file rather than restating them. The synthetic identifiers follow the
package's own rule, which the builder applies mechanically: category one to five map to `A` plus
the literature identifier, so 1.1 becomes A1.1 and 5.4 becomes A5.4 through the same function
that produced every other row. Nothing was minted by hand and nothing collides.

The registry's display name for A1.1 is "Monte Carlo EAC Forecast" and the alias table carries
"Monte Carlo EAC". The suite checks the alias name is the registry name or its stem rather than
silently accepting a mismatch. The join is by identifier throughout; there is no name-only join
anywhere in the importer.

The v0.3 importer switches the overlay off entirely, so a module that still needed it would fail
rather than pass. All three identity checks pass with the overlay disabled.

## 4. Analytic expectation

For each project the expected total is the sum of ten triangular element expectations plus, for
each of six risk events, the probability times its triangular impact expectation:

    E[total] = sum_i (a_i + m_i + b_i) / 3 + sum_j p_j * (a_j + m_j + b_j) / 3

Correlation is irrelevant to this quantity. A Gaussian copula changes the joint distribution and
leaves every marginal alone, so the expectation of a sum is the sum of the expectations whatever
the dependence is. That is why the analytic oracle needs no correlation term while the simulator
uses one.

Every element and every event now has its own row in `cost_risk_component_ground_truth.csv`
carrying its parameters, its distribution type, its dependency group, its expectation and the
formula that produced it, so every stored output traces to its stochastic inputs.

## 5. Convergence

Sampling error, not a percentage, is the acceptance rule:

    SE = simulated standard deviation / sqrt(iterations)
    accept when abs(simulated mean - analytic mean) <= z * SE, with z = 3.2905

z is the two-sided normal quantile for alpha 0.001, which is 0.05 Bonferroni corrected across
fifty mean checks. It was fixed in the contract before any result was computed and it was not
adjusted afterwards.

At five thousand draws the six project means sit between 0.35 and 1.88 standard errors from
their analytic means, and the relative errors are between 0.009 and 0.048 per cent. Convergence
was then run at one thousand, five thousand and twenty thousand draws for all six projects, each
with its own derived seed: all eighteen points are inside the rule, and the standard error
contracts by a factor between 3.5 and 5.5 from one thousand to twenty thousand draws, against
the square root of twenty, which is 4.47. No seed was tried and discarded; each seed is a
deterministic function of the programme seed, the project and the purpose.

## 6. Reproducibility

Seeds derive as `sha256(programme_version | project_id | purpose | programme_seed)`, truncated to
four bytes, and are stored in the data as `simulation_seed`. The generator was then rerun from
scratch in a separate virtual environment: the resulting tree is byte identical, `diff -rq`
reports nothing, and the combined archive digest is the same
`b478a2cb21d8acda89767abb6582913f39b64f3b20afd9ef2cdf0095cd5d93a6`. Known-answer case H repeats
case B's seed and reproduces its mean exactly; case I changes only the seed and moves the mean
while staying inside the acceptance rule.

## 7. Monte Carlo known-answer cases

Eight cases are stored in the package with hand-calculated expectations, and the suite states the
hand arithmetic itself rather than reading it back:

| Case | Construction | Hand expectation | Result |
|---|---|---|---|
| A | low = mode = high = 250,000 | 250,000 exactly | exact, zero spread |
| B | single triangular 100,000 / 200,000 / 600,000 | 300,000 | inside z SE |
| D | one event at probability 0.25 over 40,000 / 80,000 / 120,000 | 20,000 | inside z SE |
| E | three independent elements | 150,000 + 80,000 + 20,000 = 250,000 | inside z SE |
| F | probability zero | 0 | exactly zero |
| G | probability one | 80,000 | inside z SE |
| H | case B repeated with the same seed | 300,000 | identical to B |
| I | case B with a different seed | 300,000 | different draws, inside z SE |

Case C, a Beta-PERT known answer, is deliberately absent: Beta-PERT is not the governed
distribution for this family, and a case asserting it would encode the Run 9 defect as expected
behaviour. Cases J, K and L are refusals rather than stored data. The domain rules reject low
above mode, mode above high, an unrecognised distribution name, a probability below zero or above
one, and a zero or negative iteration count, and the same rules accept a well-formed case, so
they are not simply rejecting everything. Fault injections 6, 7 and 8 prove the package validator
refuses the same three classes on real data. Case M holds: the hundred-unit budget fallback is
still absent from the production model, with only the comment recording its removal left in
place.

## 8. The DSM semantic contract

The contract was written from the propagation structure before any stored number was compared
against it, and it is stored in `dsm_contract.json` and repeated in every row. `matrix[target,
source]` carries the rework strength of the edge from source to target.

| Concept | Field | Definition |
|---|---|---|
| seed | seed_impact_vector, seed_magnitude, seed_node_id | the seed magnitude at the seed node, zero elsewhere |
| direct impact | first_order_impact_vector | matrix applied once to the seed vector |
| step rule | propagation_steps, propagation_rule | step k is the matrix applied to step k minus one |
| multi-step impact | propagated_impact_vector | the sum of the step vectors, seed excluded |
| cumulative state | cumulative_state_vector | seed plus propagated |
| totals | total_first_order_impact, total_propagated_impact_excluding_seed, total_state_including_seed | the three sums, named for what they include |
| positive counts | positive_impacted_node_count_excluding_seed, positive_state_node_count_including_seed | nodes above zero, once without and once with the seed |
| material counts | material_impacted_node_count_excluding_seed, material_state_node_count_including_seed | nodes strictly above the threshold, likewise |
| threshold | materiality_threshold | 0.05, stored per row |
| seed inclusion | seed_included_in_cumulative_state, seed_included_in_propagated_impact | true and false, stated rather than implied |
| cycles | cycle_handling | fixed-depth truncation, not convergence |

The graphs contain a cycle, so the stored state is a partial sum of the series and not its limit.
That is now said in the data instead of being left for a reader to infer.

Applying this contract to the v0.2 numbers reproduces every one of the 36 rows exactly. The v0.2
arithmetic was never wrong; the two fields were carrying several different quantities under two
names. `total_propagated_rework` was the multi-step propagated total excluding the seed, which is
why comparing it with a first-order product disagreed, and `impacted_node_count` was a material
count above 0.05 including the seed node, which is why comparing it with a positive count
disagreed. The correction is a contract correction, not a number correction, which is the reason
no field was redefined after seeing a result.

## 9. DSM first-order and cumulative ground truth

Every row is recomputed from nodes, edges, seed node and seed magnitude, with no generator
involved: 36 project periods times 11 quantities, plus 8 known-answer cases. All agree.

The Run 9 comparison is repeated against v0.3 in the suite and now separates cleanly: seed
magnitude times edge strength equals the first-order field in every one of the 18 first-order
cases (48 seed-edge comparisons across all 36 rows), and the same comparison against the
cumulative field still differs on 12 of them, which is
recorded as the demonstration that the two fields are different quantities rather than as a
failure.

## 10. Node-count definitions

Four counts are stored where one used to be. Positive means above zero; material means strictly
above the stored threshold, so a node landing exactly on the threshold is not material. Each
count says whether the seed node is inside it. Known-answer case DSMKA-07 is built so one node
lands exactly on 0.05 and another just above it, which fixes the boundary convention in data.
The counts differ from each other on real rows, so the split is doing work rather than decorating.

## 11. Validator expansion

The v0.3 validator runs 1,609 checks with no failures. It recomputes rather than re-reads.

For Monte Carlo it verifies the permanent alias and the asset map, that every mapped file exists,
the distribution declarations, low, mode and high ordering, the probability domain, every
component expectation, the project analytic totals from those components, the standard error from
the standard deviation and the iteration count, the acceptance threshold, the mean against it,
quantile ordering including P90, the iteration count, the seed, the declared generator, the
ground-truth hash, all eighteen convergence points, and every known-answer case including the
reproducibility pair and the different-seed pair. It also records that the Beta-PERT expectation
differs from the governed one by more than a standard error, so the two can never be confused
silently.

For DSM it verifies seed identity against the node table, matrix structure, the first-order,
multi-step and cumulative vectors element by element, all four counts, the threshold against the
contract, the seed-inclusion flags, propagation depth, and the ground-truth hash, over both the
programme rows and the known-answer cases. DSM location is proved from the package manifest and
from the files on disk rather than from the alias table's word.

The prior audit's validator gaps are closed in the package validator as well as in the test
layer: all ten NCR quantities and all eight environmental quantities are recomputed for all 36
periods; agent branches are replayed from their own machine-readable conditions, counted per
project and per branch, and a branch no state row reaches is required to have no count rather
than being ignored; analogous pairs are enumerated over every split combination that occurs, with
the analog side required to come from the development split and the target side required to be
the held-out splits; the linear programming models are checked so that every constraint is of a
relation type the solver receives, which for this package is the single type present.

## 12. Fault injection

Sixteen corruptions, each made only in a discarded scratch copy, each proved to alter bytes, each
restored, with the clean run reconfirmed after every restore. All sixteen were caught by name.
`code_audit/run10_validator_fault_injection.csv` carries the injection, the file, the byte-change
flag, the validator exit code and the named failing checks.

| # | Injection | Named failure |
|---|---|---|
| 1 | wrong Monte Carlo alias | identity:alias_present:A1.1 |
| 2 | wrong distribution type | mc:element_distribution_declared |
| 3 | altered analytic mean | mc:analytic_total, mc:ground_truth_hash |
| 4 | altered simulation mean | mc:mean_check_recorded, mc:ground_truth_hash |
| 5 | altered seed | mc:ground_truth_hash |
| 6 | invalid low, mode, high | mc:element_ordering |
| 7 | invalid probability | mc:probability_domain |
| 8 | iteration count changed without regenerating | mc:acceptance_threshold_recomputed, mc:ground_truth_hash |
| 9 | mean biased by ten standard errors | mc:mean_check_recorded, mc:ground_truth_hash |
| 10 | wrong DSM seed | dsm:first_order, dsm:cumulative, dsm:ground_truth_hash |
| 11 | changed edge strength | dsm:first_order, dsm:cumulative on every affected period |
| 12 | wrong first-order impact | dsm:total_first_order |
| 13 | wrong cumulative value | dsm:total_state |
| 14 | wrong positive node count | dsm:positive_including_seed |
| 15 | wrong material count | dsm:material_including_seed |
| 16 | threshold changed without regenerating | dsm:threshold_matches_contract, both material counts |

Every injection inside a package directory also broke that package's local checksum file, which
is a second independent catch.

## 13. Generator and dependency record

- Python 3.11.15
- numpy 2.3.5, pandas 2.2.3, scipy 1.17.0, networkx 3.6.1, openpyxl 3.1.5
- lxml: not installed in the generator environment and not installed in the normal application
  or test interpreter. Nothing was added to the application requirements lock.
- Random number generator: `numpy.random.Generator(PCG64)` through `numpy.random.default_rng`
- Programme seed 20260812; every simulation seed is derived from it by sha256 and stored

The v0.3 builder imports the v0.2 builder for the manifest, checksum, workbook and schema-catalog
machinery rather than copying it, so those parts of the two versions cannot drift.

## 14. Programme checksum and reproducibility

126 files, root manifest and root checksum file regenerated, all three package-local checksum
files regenerated and verified. The independent checksum sweep in
`code_audit/synthetic_v03_checksum_results.csv` reports zero mismatches. The second build in an
isolated environment produced an identical tree and an identical archive digest. There is no
intentionally variable metadata: timestamps are fixed and archive entries are normalised. The
combined archive is not committed, because it is a byte-for-byte function of the committed tree.

## 15. Complete suite results

- Run 10, the new suite: 121/121 checks passed.
- The package validator: 1,609 checks, zero failures.
- Package checksum verification: pass.
- Run 6 known-answer 472/472, Run 8 classification 233/233, Run 9 test-only integration 84/84,
  all unchanged. Run 9 continues to read v0.2, which is left exactly as it was, so its recorded
  disagreements remain a true record of that version rather than being rewritten.
- The complete server suite under `run_all_suites.sh`, with its Run 9 strictness intact: 66
  suites, 4,851 of 4,851 checks, ALL SUITES GREEN, on the branch and again on merged main.
- `server/app` and `assets` are byte identical to the pre-run baseline; `git diff` against the
  merge base reports no change under either path.

## 16. Guarantees

Verified:

- Monte Carlo EAC and Scenario Modeling resolve permanently, one to one, by identifier, with the
  overlay switched off.
- The Monte Carlo distribution is determined from the generator, declared in the data, and used
  identically by generator, schema, ground truth, validator and tests.
- Every Monte Carlo output traces to its stochastic inputs.
- The mean check is a statistical one with a justified z fixed in advance, and convergence
  behaves as the square root of the sample count.
- The DSM contract separates seed, first order, multi-step, cumulative, positive and material
  quantities, states the threshold, states seed inclusion per count, and states cycle handling.
- Every DSM quantity recomputes from raw structure, exactly, on every row.
- Sixteen of sixteen fault injections are caught by name.
- v0.3 is reproducible byte for byte, and the programme checksums verify.
- No production code, voting, activation, threshold or participant-visible behaviour changed.

Partly met:

- Gate 6 case C is not present, deliberately. A Beta-PERT known-answer case would assert a
  distribution this family does not use.
- Gate 10's linear programming request to use all relation types present is met only in the sense
  that the package contains one relation type. Adding others would be new synthetic content
  rather than validation of what exists.

Not met:

- Nothing in the gate list was skipped for convenience.

## 17. Owner decisions

1. The repository's Monte Carlo EAC module is a Beta-PERT over earned value indices; the
   synthetic family mapped to it is a triangular bottom-up cost model with discrete risk events.
   If the intention is for the synthetic package to exercise the production module, the package
   needs a fixture family shaped like the production model's inputs. That is a new fixture
   family, not a correction, and it was out of scope here.
2. The registry name for A1.1 is "Monte Carlo EAC Forecast" and the synthetic tables say "Monte
   Carlo EAC". Worth settling in one direction.
3. v0.2 remains staged and unchanged so the Run 9 record stays true. If the owner wants a single
   staged version, v0.2 can be retired once nothing reads it.
4. Connecting the corrected assets to production module execution remains untaken work, and this
   run was explicitly told not to do it.
