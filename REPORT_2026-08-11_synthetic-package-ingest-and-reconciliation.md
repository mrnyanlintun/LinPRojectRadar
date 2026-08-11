# Synthetic Package Ingest and Reconciliation, OG-SYNTH-0.1

**Branch `claude/synthetic-package-ingest` from `origin/main` at `3fc37cc`, the Run 8 merge.
THIS RUN CHANGES NO PRODUCTION CODE.** Staging, audit scripts, audit CSVs, this report and the
handoff entry only. Audit and staging only: no module was integrated, activated or made voting,
and no synthetic record entered an operational or participant database.

```
Archive verified: yes
Checksums: pass (85 of 90 match, 0 mismatch, 5 files not supplied)
Validator: fail (cannot run, the validator script was not supplied)
Generator reproducibility: fail (cannot assess, the generator script was not supplied)
Run 8 mappings reconciled: 11/11
Missing or mismatched assets: 6 (2 absent corpora, 3 incomplete structures, 1 package-boundary contradiction)
Production files changed: none
```

## 1. Supplied files and the authoritative-source decision

The task prompt names a combined archive, `Opus_Gubernatio_Synthetic_Programme_v0.1.zip`, as
authoritative and directs that the three separate package archives be ignored as duplicate
convenience exports. **That combined archive was not supplied.** The five files actually
supplied were the three package archives, `package_summary.xlsx` and the handoff document.

The prompt's own fallback rule applies, so **the three separate package archives are the
authoritative source for this run**. They are not corrupt, they open cleanly, they contain no
path traversal and no absolute paths, and they do not contradict the handoff on any matter of
data content. They do contradict it on completeness, which is section 3.

**What could not be verified as a result.** Five files are listed in the programme checksum
manifest and are absent from all three archives. They are exactly the programme-level files that
would have existed only at the root of the combined archive:

| File | Consequence of its absence |
|---|---|
| `validators/validate_synthetic_programme.py` | The claimed 160 checks cannot be rerun. The claim is unverified. |
| `generators/generate_opus_synthetic_programme.py` | Reproducibility from seed `20260811` cannot be tested at all. |
| `validation_report.json` | The machine-readable validation record is absent; only the human-readable summary survives. |
| `module_asset_map.csv` | The programme-level module map is absent; three per-package maps survive and do not cover the same ground. |
| `schemas/schema_catalog.json` | There is no declared schema to check the data against, so schema conformance was re-derived from the data. |

A sixth file, `MANIFEST.csv`, is claimed by the handoff and **is not listed in the checksum
manifest either**, so it appears never to have been generated. This is a finding, not something to
invent. The three archives collectively lack the manifest, the checksum-covered validator and the
generator that the handoff claims exist.

This is not treated as a stop condition, per the instruction. It does mean two of the six lead
verdicts are negative for a reason that is about what was shipped rather than about the data.

## 2. Extraction location and git disposition

Staged once, into a new versioned directory that did not previously exist:

```
research_fixtures/synthetic/OG-SYNTH-0.1/package_A/
research_fixtures/synthetic/OG-SYNTH-0.1/package_B/
research_fixtures/synthetic/OG-SYNTH-0.1/package_C/
```

The repository had no existing research-fixture directory of this kind. `research/` holds a single
HTML page and `calibration/` and `p0-baseline/` hold platform artefacts, so a new top-level
`research_fixtures/` keeps the synthetic material visibly separate from production data,
participant data, operational project documents and research exports, which is what the task
required. Every archive was inspected for `../` components and absolute paths **before** extraction
and each member path was re-checked against the destination root during extraction. Nothing was
extracted over an existing version.

**Recommendation on committing the files: commit them, which is what this run did.** The three
archives total under one megabyte, the content is entirely synthetic by construction, the audit is
worthless without the bytes it was run against, and a gitignored fixture with only a manifest
committed would make every future known-answer test unreproducible for anyone who does not hold
the original archives. The countervailing risk, that synthetic rows are mistaken for real evidence,
is addressed by the directory name, the per-record provenance columns and the staged README rather
than by hiding the files. `.gitignore` gained rules for scratch and regeneration directories under
`research_fixtures/` so that a later reproducibility attempt cannot accidentally commit a
regenerated copy alongside the authoritative one.

## 3. Checksum results

All three archives ship a byte-identical, **programme-level** `CHECKSUMS.sha256` listing all 90
programme files, not a per-archive one. No single archive can therefore verify itself: run inside
`package_A` alone the check reports 39 of 90 and fails the rest as missing. Verification was
performed against a merged tree assembled from all three archives, which is the tree the manifest
describes.

| Result | Count |
|---|---|
| MATCH | 85 |
| MISMATCH | **0** |
| MISSING (not supplied with the three archives) | 5 |
| Total listed | 90 |

Full per-file results: `code_audit/synthetic_package_checksum_results.csv`. A per-file inventory
with independently computed hashes, row counts and column counts is at
`code_audit/synthetic_package_file_inventory.csv` (99 staged files, counting the shared
programme-level files once per archive).

Four files common to all three archives are byte-identical across them and each matches its
checksum entry: `README.md`, `VALIDATION_SUMMARY.md`, `data_dictionary.csv` and
`package_summary.xlsx`. The separately supplied `package_summary.xlsx` is byte-identical to the
copy inside the archives, so the spreadsheet supplied loose alongside the archives is the same
checksum-covered artefact and not a divergent build.

No unexpected executable was found, no file carries an execute bit, and no `.env`, `.pem`, `.key`,
`.sh`, `.bat` or `.ps1` file is present. Every staged file is `.csv`, `.json`, `.md` or `.xlsx`.

## 4. Validator results and failure proof

**The included validator could not be run because it was not included.** `VALIDATION_SUMMARY.md`
is a stored report, not an executable check: it lists 160 rows, all PASS, and the claim of zero
failures is consistent within that document. Per the instruction not to trust 160 of 160 without
rerunning it, **the claim stands unverified and is recorded as such.**

In its place this run wrote an **independent** checker, `tools/audit_synthetic_package.py`, written
against the data rather than against the package's own report, which is the difference between a
check and a restatement. It reads only and never writes into the staged fixture.

| | |
|---|---|
| Command | `python3 tools/audit_synthetic_package.py` |
| Interpreter | CPython 3.11, standard library only, no third-party dependency |
| Checks | 74 |
| Pass | 63 |
| Fail | 11 |
| Warnings | none; every result is a hard pass or fail |

The 11 failures are 6 absent programme files (section 1) and 5 substantive data findings
(section 9). Full results: `code_audit/synthetic_package_independent_checks.csv`.

**Proof that the checker can fail.** Three faults were injected into a **scratch copy** of the
staged tree, never into the authoritative assets:

| Injected fault | Detected by | Result |
|---|---|---|
| One reference project moved from the locked holdout to validation in a derived table only | `leakage:reference_project_periods.csv_split_agrees_with_manifest` | RED, named `REF-0012` |
| One `data_origin` value blanked in `anomaly_labels.csv` | `provenance:all_csv_records` | RED, named the file |
| A reversed dependency appended to create a schedule cycle | `schedule:acyclic_per_project` and `record_hash:unique_within_file` | RED, named `PRJ-AIR` |

The same injection dropped the checksum verification inside `package_A` from 85 matching to 39.
The scratch copy was discarded and the checker rerun against the authoritative tree, returning to
the baseline 63 pass and 11 fail.

## 5. Generator reproducibility

**Not assessable. The generator was not supplied.** No claim about regeneration from seed
`20260811` can be made, confirmed or denied by this run. What is recorded rather than inferred:

- every record in every CSV carries `random_seed = 20260811` and
  `generator_version = generate_opus_synthetic_programme.py@0.1`, so the seed and generator
  version are at least stamped consistently;
- no dependency pinning is visible anywhere in the delivered material, because no script was
  delivered to pin anything;
- which files are intentionally stochastic but seed-controlled cannot be determined without the
  generator, though the ground-truth files are internally consistent with their source event logs,
  which is the evidence in section 6;
- regeneration into a scratch directory was therefore not attempted, and the authoritative package
  was not overwritten.

Verdict `fail` in the lead block means unverifiable, not disproved.

## 6. Package counts and independent integrity findings

Package A holds 6 synthetic projects and 36 reporting periods across 36 data files. Package B
holds 360 reference projects, 2,880 project-period observations, 15 expert profiles, 24 epistemic
scenarios and 12 decision problems across 31 data files. Package C holds 8 activation candidates
and their fixtures across 13 data files. These agree with the handoff.

**Schema and key integrity, all verified independently:**

- primary keys unique in projects, reporting periods and schedule activities; `record_hash` present
  and unique within every file;
- foreign keys resolve: every reporting period, activity and dependency to its project, every
  dependency endpoint to a real activity in the same project, every Package B derived row to a real
  reference project, every decision object to a real decision problem;
- **schedule networks are acyclic in all six projects**, and no fixture claims to test an invalid
  cycle;
- triangular durations satisfy optimistic at most mode at most pessimistic across all 72 activities,
  and all durations are positive;
- the eightieth percentile is at or above the fiftieth in the schedule ground truth;
- units are explicit in column names throughout (`_usd`, `_days`, `_pct`, `_m2`, `_km`,
  `_locations_per_day`, `_steps`, `_units`);
- date and day ordering is valid, with no required finish preceding its baseline;
- action by scenario is complete for all 12 problems, payoff matrices are complete, scenario
  probabilities sum to one for every problem, the alternatives-by-criteria matrix has no blank cell
  and every problem carries at least two alternatives;
- regret values are non-negative and each scenario column contains a zero, which is the property a
  minimax regret computation depends on;
- the belief rule base carries 27 rules over three antecedents at three levels each, covering the
  antecedent space exactly, with belief distributions summing to one and explicit rule weights;
- the rough-set table is a genuine decision table: four banded condition attributes and a
  `decision_class` decision attribute.

**Leakage, which is the finding most worth hunting for, was hunted properly and is clean.** Every
one of the 360 reference projects appears in exactly one split (216 development, 72 validation, 72
locked holdout). The split manifest agrees with the inline split column in `reference_projects.csv`
for all 360. Every derived table that carries a split agrees with the manifest for every row. Going
past filenames, **no two projects in different splits share an identical twelve-field feature
vector**, so there is no duplicated project smuggled across the boundary, and the analogous-pairs
table contains no pair bridging the locked holdout to another split. Ground truth reproduces
independently: mean wait recomputed from the raw queue event log matches the stored value for all
six queues, and project buffer consumption recomputed from the buffer table matches the stored
ground truth for all 36 project-periods.

**Confidentiality screen, run explicitly.** Every CSV was scanned for email addresses, telephone
numbers and social security patterns. **Nothing was found.** Project names are archetypes
(`PRJ-AIR`), reference projects are sequential identifiers (`REF-0001`), experts are profiles
rather than people, regions are broad (`US-NORTHEAST`) and no free-text narrative field exists that
could carry an employer detail. **Nothing in these packages looks like real participant or
employer-confidential data.** The one apparent hit was the generator version string
`generate_opus_synthetic_programme.py@0.1`, which is not an address.

**Provenance rule: verified.** Every record of every CSV in all three packages carries
`data_origin = SYNTHETIC_RESEARCH_FIXTURE`, `not_for_empirical_validation = true` and
`programme_version = OG-SYNTH-0.1`. No record lacks them. Nothing was repaired.

## 7. The Run 8 reconciliation

Run 8's totals were verified against `code_audit/run8_module_classification.csv` rather than taken
from the prompt: Bucket 1 = 0, Bucket 2 = 16, Bucket 3 = 7, Bucket 4 = 2, Bucket 5 = 2, across 27
modules. The reconciliation therefore covers **11 modules, and all 11 are reconciled**. The build
script asserts set equality between the Run 8 Bucket 3/4/5 set and the reconciled set, so a drift
in either would fail rather than pass quietly.

One structural note before the table. **The packages use a different module numbering from Run 8**:
the package maps say `2.1`, `3.1`, `5.1`, `7.18`, `7.19` where Run 8 says `A2.1`, `A3.1`, `A5.1`,
`B2.18`, `B2.19`. The category numbers line up, so the mapping is recoverable, but no automated
join between the two would work without it, and the programme-level `module_asset_map.csv` that
might have settled the question is one of the five missing files.

Machine-readable: `code_audit/synthetic_package_module_reconciliation.csv`.

| Module ID | Module | Cat | Category Name | Run 8 Bucket | Required Structure per Run 8 | Package Asset | Asset Path | Complete? | Mismatch | Recommended Later Action |
|---|---|---|---|---|---|---|---|---|---|---|
| A1.1 | Monte Carlo EAC | 1 | Cost Forecasting | 3 | cost risk quantification: three-point or distributional cost ranges per risk or work package | Package A quantified risk register with three-point impacts, cost elements with three-point ranges, correlation matrix | `package_A/.../cost_risk_events.csv`, `cost_elements.csv`, `cost_correlations.csv`, `cost_risk_ground_truth.csv` | yes | The package asset map has no row for this module and maps these files to the cost risk module only. The structure exists under different names. | Test-only importer and a known-answer test. Leave the present arithmetic in production. |
| A2.2 | Line of Balance | 2 | Schedule Analytics | 3 | locations or units, crews, quantities and production rates | Package A line of balance work packages and ground truth | `package_A/.../lob_work_packages.csv`, `lob_ground_truth.csv` | yes | none | Test-only importer, known-answer test on catch-up location and interference. |
| A2.3 | CCPM Buffer Health | 2 | Schedule Analytics | 3 | a critical chain with a project buffer and feeding buffers sized from activity estimates | Package A buffers and ground truth | `package_A/.../ccpm_buffers.csv`, `ccpm_ground_truth.csv`, `schedule_activities.csv` | **partial** | Buffers carry `chain_id`, activities carry only a boolean flag and no `chain_id`, so no buffer can be traced to its chain. Buffers are a flat fifteen per cent of baseline, not sized from activity estimates. | Ask for a chain identifier on activities and estimate-derived sizing. Do not integrate until the chain is traceable. |
| A4.4 | NCR Rate | 4 | Quality | 3 | an audited nonconformance cohort carrying a findings total | **NONE** | none | **no** | Absent outright. Run 8 required quality audits and audit findings; Package A category 4 is document and risk signals and holds no quality audit cohort. | Request the missing corpus. The module keeps abstaining. |
| A5.6 | Queueing Theory Bottleneck | 5 | Systems and Complexity | 3 | arrival and service processes, capacity and a queue discipline | Package A queue event log and ground truth | `package_A/.../queue_events.csv`, `queue_ground_truth.csv` | yes | none; arrivals, service, capacity by server and an explicit discipline are all present | Test-only importer, known-answer test on mean wait, p90, throughput and utilisation. |
| A5.7 | Agent-Based Supply Chain | 5 | Systems and Complexity | 3 | agents, states, rules and interactions | Package A agent roster, per-step state history and ground truth | `package_A/.../agents.csv`, `agent_state_history.csv`, `abm_ground_truth.csv` | **partial** | Agents carry `decision_rule_id` but no table defines the rules. Run 8 required interaction rules. Interaction logic cannot be reconstructed. | Request the rule definitions. Supports state replay, not an independent agent simulation. |
| A6.3 | Environmental Compliance Rate | 6 | Health, Safety and Environment | 3 | audited permit condition compliance | **NONE** | none | **no** | Absent outright. Run 8 required permits, permit conditions and compliance assessments. Package A has no category 6 asset at all. | Request the missing corpus. The module keeps abstaining. |
| A5.4 | Scenario Modeling | 5 | Systems and Complexity | 4 | an actions-by-scenarios payoff structure with defined scenarios and probabilities | Package B decision problems, actions, probability-weighted scenarios, full outcome and payoff matrices | `package_B/.../B3_decision_optimization/` (six files) | yes | The map carries no row under Run 8's identifier and assigns these objects to the what-if and regret modules instead. The structure is present. | Test-only importer and a known-answer test. Replacing the three divisors is an owner decision. |
| B2.19 | CRITIC-TOPSIS | 7 | Evidence Combination and Ranking | 4 | an alternatives-by-criteria decision matrix, weights computed across alternatives | Package B six alternatives per problem across five criteria, with directions, owner weights, stored CRITIC weights and top action | `package_B/.../alternative_criteria_matrix.csv`, `criteria.csv`, `ground_truth_decisions.csv` | yes | none structurally. The fixture exercises the degenerate single-alternative weighting Run 8 found; it does not fix it. | Test-only importer and known-answer test on the weights and ranking. The degenerate weighting stays a separate production decision. |
| A3.1 | Reference Class Forecasting | 3 | Cost Risk | 5 | a population of comparable completed projects with realised overruns | Package B 360-project reference population, membership rule, outcomes, locked split | `package_B/.../reference_projects.csv`, `reference_class_membership.csv`, `reference_outcomes.csv`, `split_manifest.csv` | yes | none structurally | **Stays disabled and abstaining.** Reactivation is an owner decision, not a consequence of a fixture existing. |
| A5.1 | DSM Rework Propagation | 5 | Systems and Complexity | 5 | a project-specific dependency matrix | Package A typed nodes, weighted directed edges, propagation delay and propagation ground truth | `package_A/.../dsm_nodes.csv`, `dsm_edges.csv`, `dsm_ground_truth.csv` | yes | Package boundary contradiction. Run 8 specified this as a Package B reference object; it was delivered in Package A. The delivery is arguably more correct because the matrix is per project, but it contradicts the handoff rule that Bucket 5 draws on B or C. | **Stays disabled and abstaining.** Reactivation is an owner decision. |

**The package rule held in every other respect.** Package A supplied only project-structure
requirements, Package B only reference, training, expert, rule and decision objects, and Package C
reused A and B through an explicit reuse manifest without inventing new project structures. The one
exception is the DSM row above.

## 8. Complete assets

Line of Balance, queueing, agents-as-state-history, cost uncertainty, the reference population, the
dependency matrix, the decision and payoff objects and the alternatives matrix all supply the
defining canonical structure their method requires, judged by column semantics and by recomputation
rather than by filename. The belief rule base, the rough-set decision table, the Dempster-Shafer
masses and the probabilistic linguistic term sets are likewise genuine structures rather than
proxies, though none of those modules is in the reconciliation scope.

## 9. Incomplete, contradictory, redundant or unsafe assets

1. **Absent: the quality audit corpus (A4.4).** No file supports it.
2. **Absent: the environmental audit corpus (A6.3).** No file supports it.
3. **Incomplete: CCPM (A2.3).** Buffers are not traceable to chain activities and are not sized
   from activity estimates. A fever chart computed on this would be a fever chart over a flat
   percentage, which is close to what the module already does.
4. **Incomplete: agent interaction rules (A5.7).** Referenced by identifier, never defined.
5. **Incomplete: the linear programming models.** All 12 carry variables and bounds, but the
   objective survives only as `objective_description` prose and the constraints only as strings such
   as `action_cost <= budget_cap`. **No solver can consume this.** Linear programming and
   multi-objective optimisation require a feasible machine-readable model, so for those methods this
   is a proxy input rather than the canonical structure, notwithstanding the stored
   `lp_objective_value` and `lp_solution_json` in the ground truth. Those modules are outside the
   reconciliation scope but the gap will block them later.
6. **Contradictory: the DSM package placement**, and the divergent module numbering, both above.
7. **Redundant, harmlessly:** four programme-level files are duplicated byte-for-byte in all three
   archives.
8. **Unsafe to integrate: nothing**, on the evidence available. No executable, no secret, no
   traversal, no real-looking personal or employer data. The safety issue is not the content, it is
   the risk of the content being read as evidence it is not.

## 10. Modules that must remain abstaining, and disabled modules that remain disabled

**Remain abstaining because the corpus is still absent:** A4.4 NCR Rate and A6.3 Environmental
Compliance Rate. Run 8 recorded both as corpus gaps rather than defects, and this package closes
neither.

**Remain abstaining because the asset is incomplete:** A2.3 CCPM Buffer Health, until a chain is
traceable, and A5.7 Agent-Based Supply Chain, until the interaction rules exist.

**Remain disabled: A3.1 Reference Class Forecasting and A5.1 DSM Rework Propagation.** Both were
made to abstain unconditionally by Run 7. **A complete synthetic fixture now exists for both, and
that changes nothing.** A fixture does not authorise a disabled module to run, and synthetic
availability does not convert a concept-only module into a canonical active module. Reactivation is
an owner decision. The handoff itself says the activation laboratory does not authorise activation.

**Nothing in this package constitutes empirical validation.** The staged material supports
implementation fidelity, known-answer testing, structural verification, solver agreement, edge and
abstention behaviour and adapter development. It does not support predictive accuracy, calibration,
threshold justification or field validity, and no surface may describe it as validation.

## 11. Proposed later integration file map and tests required

Per module, with importer, adapter, schema, the module code file that would change, the test files,
the known-answer fixture, abstention behaviour, the separation control, the voting state and the
participant-surface effect: `code_audit/synthetic_package_integration_plan.csv`, 11 rows.
Summarised:

- The code files that would later change are `server/app/simulation/models.py` (A2.2, A2.3, A3.1,
  A5.1), `models_doc.py` (A4.4, A5.4, A5.6, A5.7, A6.3), `models_sim.py` (A1.1) and
  `models_fuzzy.py` (B2.19). **None of them was touched in this run.**
- Each integrable module needs one test-only importer, one adapter, a read-only research-schema
  model that is never part of the operational database, a known-answer test file and an abstention
  test.
- **Abstention behaviour is uniform and non-negotiable: when the synthetic object is absent the
  module abstains with its existing reason code. The absence of a fixture must never read as a
  healthy project**, which is Run 6 finding 1.1 and the reason several of these modules are in
  their buckets.
- **Separation control:** the fixture is loaded only by test-only importers reading
  `research_fixtures/`, no synthetic row may reach an operational or participant database, and
  `DATABASE_URL` is never pointed at production for this work.
- **Voting state after integration: non-voting for every module.** Becoming voting is a separate
  owner decision, as is reactivating either disabled module.
- **Participant-surface effect: none, for every module.** The participant does not see the
  remediation; qualifiers live in the export, the API and the methods documentation only.

## 12. Owner decisions required

1. **The combined archive.** Supply it, or confirm the three-archive substitution stands as the
   authoritative source of record for OG-SYNTH-0.1.
2. **The validator and generator.** Without them the 160-check claim and the seed reproducibility
   claim cannot be verified, and no report should repeat either as established.
3. **The two absent corpora**, quality audit and environmental audit. Commission them or accept
   that those modules keep abstaining.
4. **CCPM chain traceability and buffer sizing**, and **agent interaction rules**: regenerate, or
   accept those two modules as not integrable from this package.
5. **The linear programming model form.** Prose constraints and a prose objective will not support
   the optimisation modules later.
6. **Module numbering.** Settle whether the programme uses Run 8's identifiers or the packages'.
7. **Reactivation of A3.1 and A5.1.** Explicitly still no, unless the owner decides otherwise.
8. **Whether the fixture stays committed** in the repository, as recommended in section 2.

## 13. Guarantees

| Guarantee | Status |
|---|---|
| Archives open, no path traversal, no absolute paths, extracted safely | **verified** |
| Expected top-level directories exist in each archive | **verified** |
| `MANIFEST.csv` exists | **not met**, never generated, absent from the checksum manifest too |
| `CHECKSUMS.sha256` exists | **verified**, programme-level and identical in all three archives |
| Every listed file exists | **partly met**, 85 of 90 |
| Every checksum matches | **verified** for all 85 files present, zero mismatches |
| No unexpected executable or secret file | **verified** |
| Validator rerun as documented | **not met**, the validator was not supplied |
| Validator or checker proved able to fail | **verified**, by three injections into a scratch copy |
| Claimed 160 checks with zero failures | **not met**, unverifiable |
| Generator regenerates from seed `20260811` | **not met**, unverifiable |
| Dependency versions pinned | **not met**, no script to pin them |
| Provenance on every record | **verified**, all three fields on every row of every file |
| Primary keys unique, foreign keys resolve | **verified** |
| Splits do not overlap and rows do not leak across them | **verified**, including a feature-vector duplicate hunt |
| Schedule networks acyclic | **verified** |
| Action, scenario, criterion and payoff matrices complete | **verified** |
| Ground truth reproduces independently | **verified** for the queue and CCPM ground truth |
| Units explicit and date ordering valid | **verified** |
| No real participant or employer-confidential data | **verified**, screened explicitly |
| All Run 8 Bucket 3/4/5 modules reconciled | **verified**, 11 of 11, asserted by set equality |
| No production code changed | **verified**, nothing under `server/app/` or `assets/` differs from the pinned baseline |
| No module activated, no voting change | **verified**, no module code touched |
| No synthetic data in an operational or participant database | **verified**, nothing was imported anywhere |
| Fixture staged once, not over an existing version | **verified** |
