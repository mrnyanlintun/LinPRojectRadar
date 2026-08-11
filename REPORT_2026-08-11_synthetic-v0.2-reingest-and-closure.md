# Synthetic Programme v0.2 Re-ingest and Closure Audit, OG-SYNTH-0.2

**Branch `claude/synthetic-v02-reingest` from `origin/main` at `08c4905`, the v0.1 ingest audit
merge. THIS RUN CHANGES NO PRODUCTION CODE.** Staging, audit scripts, audit CSVs, this report and
the handoff entry only. No module was integrated, activated or made voting, no disabled module was
reactivated, and no synthetic record entered an operational or participant database.

```
Archive verified: yes (sha256 2606b6bfecbdbb86393c1473e036ff33a3502e695d6d7f835d7fb3c513139e1a, 118 files, single root, no traversal, no symlink, no absolute path)
Programme checksums: pass (117 of 117 recomputed independently, 0 mismatch, 0 missing, manifest covers every file)
Package-local checksums: pass (A 49, B 34, C 14; each package verifies alone with no path leaving its own directory)
Validator: pass (681 checks, 0 failures, rerun rather than accepted)
Validator fault injections: 7 of 7 detected and named
Generator reproducibility: pass (two builds byte-identical; the rebuilt combined ZIP equals the supplied archive bit for bit)
Run 8 mappings reconciled: 11/11 complete
Prior gaps closed: 6 of 7 fully, 1 partly (module numbering)
Remaining gaps: 3 (two Run 8 modules unmapped in the alias table, one declared agent branch never exercised, lxml unpinned in the dependency lock)
Production files changed: none
```

## 1. The authoritative-source decision

The combined archive was supplied this time and **is the sole source of truth for this run**:
`Opus_Gubernatio_Synthetic_Programme_v0.2.zip`, sha256
`2606b6bfecbdbb86393c1473e036ff33a3502e695d6d7f835d7fb3c513139e1a`, 2,138,482 bytes, 118 files.
The v0.1 material was not used as a source of truth and was not modified: the prior staging at
`research_fixtures/synthetic/OG-SYNTH-0.1/`, the prior report and the prior
`code_audit/synthetic_package_*.csv` outputs all stand untouched as history. v0.2 was staged
beside it, never over it, at
`research_fixtures/synthetic/OG-SYNTH-0.2/Opus_Gubernatio_Synthetic_Programme_v0.2/`.

The one place v0.1 is used at all is as an **input**: the archive bundles
`generators/base/Opus_Gubernatio_Synthetic_Programme_v0.1.zip` as the builder's base, and its
sha256 matches the value recorded in `BUILD_PROVENANCE.json`.

## 2. Archive safety results

Every member path was inspected **before** anything was written to disk:

| Check | Result |
|---|---|
| Entries | 118 files, 10 directories |
| Absolute paths | none |
| `..` components | none |
| Drive-qualified or backslash paths | none |
| Symlink entries (mode bits inspected, not filenames) | none |
| Single root named `Opus_Gubernatio_Synthetic_Programme_v0.2` | yes, the only root |
| Overwrite of an existing path | none; the destination did not exist and each target was re-checked against the destination root during extraction |
| Executable bit on any staged file | none |
| `.env`, `.pem`, `.key`, `.sh`, `.bat`, `.ps1`, `.exe` files | none |

All required root artefacts are present and usable: `AUDIT_RESOLUTION_v0.2.md`,
`BUILD_PROVENANCE.json`, `CHECKSUMS.sha256`, `CLAUDE_CODE_HANDOFF_v0.2.md`, `MANIFEST.csv`,
`README.md`, `VALIDATION_SUMMARY.md`, `validation_report.json`, `data_dictionary.csv`,
`module_asset_map.csv`, `module_id_aliases.csv`, `package_summary.xlsx`, `requirements-lock.txt`,
`schemas/schema_catalog.json`, the three generator scripts and the bundled v0.1 base archive.
Every one of the six files the v0.1 audit recorded as never shipped now exists.

Per-file inventory with independently computed hashes, row counts and column counts:
`code_audit/synthetic_v02_file_inventory.csv` (118 rows).

## 3. Root and package checksum results

The included verifier was run and passed. **It was not trusted alone**: every line of every
checksum manifest was recomputed independently, and the manifests were checked for coverage in the
other direction as well, so a file present on disk but absent from the manifest would be caught.

| Manifest | Entries | MATCH | MISMATCH | MISSING | Files on disk not listed |
|---|---|---|---|---|---|
| `CHECKSUMS.sha256` (programme) | 117 | 117 | 0 | 0 | only `CHECKSUMS.sha256` itself |
| `package_A_project_structures/PACKAGE_CHECKSUMS.sha256` | 49 | 49 | 0 | 0 | only the checksum file itself |
| `package_B_reference_training_decisions/PACKAGE_CHECKSUMS.sha256` | 34 | 34 | 0 | 0 | only the checksum file itself |
| `package_C_optional_activation_lab/PACKAGE_CHECKSUMS.sha256` | 14 | 14 | 0 | 0 | only the checksum file itself |

**The specific v0.1 defect is closed.** In v0.1 all three archives shipped the same programme-level
manifest, so no package could verify itself and Package A alone reported 39 of 90. In v0.2 each
package carries its own `PACKAGE_MANIFEST.csv` and `PACKAGE_CHECKSUMS.sha256` listing **only paths
inside that package**, with no entry starting with `..`, `/` or a backslash, and each verifies
standing alone with no file from another archive. Each package-local entry also agrees with the
corresponding programme-level entry, so the two manifests cannot drift apart unnoticed.

Full per-file results: `code_audit/synthetic_v02_checksum_results.csv` (214 rows, all MATCH).

## 4. Validator results and mutation proof

`python generators/validate_synthetic_programme_v0_2.py --root <staged root>` reports **681 checks
and zero failures**, reproducing the release claim. The claim was treated as a claim: the validator
was rerun here, and then proved able to fail.

Seven faults were injected, each into a **fresh discarded scratch copy** of the staged tree. The
authoritative extraction was never mutated. Each injection was **confirmed to have changed bytes on
disk before the validator was rerun**, so an injection that silently failed to apply could not
report a false clean. Machine-readable: `code_audit/synthetic_v02_mutation_proof.csv`.

| Injection | Applied | Detected | Named by |
|---|---|---|---|
| CCPM chain foreign-key break (a chain activity repointed to an undeclared chain) | yes | yes | `ccpm:chain_activity_fk`, `ccpm:member_count:PRJ-AIR-CC` |
| Agent decision-rule foreign-key break (an agent repointed to an undeclared rule) | yes | yes | `abm:agent_rule_fk` |
| NCR ground-truth mismatch (issued count inflated by three at one cutoff) | yes | yes | `ncr:issued:PRJ-AIR:P02` |
| Environmental compliance-rate mismatch (rate overwritten at one period) | yes | yes | `env:rate:PRJ-AIR:P01` |
| LP coefficient change (first objective coefficient scaled by 1.75) | yes | yes | `LP:objective:DP-01` |
| Module-ID alias collision (code id A2.2 collided onto A2.3) | yes | yes | `aliases:unique_code` |
| Train/validation/holdout leakage (a development project given a locked-holdout feature vector) | yes | yes | `B1:no_duplicate_feature_vectors_across_splits` |

Baseline before injections: 681 checks, 0 failures. Every scratch copy was discarded and the
authoritative extraction rechecked afterwards: **681 checks, 0 failures**, back at baseline.

**An independent checker was also written and run**, because a package's own validator restating
its own build is not evidence. `tools/audit_synthetic_v02.py` reads the data, not the validator,
and recomputes the quantities from source rows. 107 checks, 105 pass, 2 fail; both failures are
honest residual findings reported in sections 6 and 7, not data corruption. Results:
`code_audit/synthetic_v02_independent_checks.csv`.

**Where the shipped validator is thinner than its 681 figure suggests**, found by writing the
independent checks beside it. None of this is a defect in the data; it is a limit on what a green
validator run proves:

- the NCR checks recompute issued and open only; closed, overdue, cumulative inspections,
  incidence, closure ratio, open ratio, overdue open ratio and mean open age are unchecked by the
  validator. **All ten were recomputed here and all reconcile at all 36 cutoffs.**
- the environmental check recomputes the rate only; the applicable, assessed, compliant,
  noncompliant, unassessed and severe-noncompliance counts are unchecked. **All were recomputed
  here and all reconcile at all 36 periods.**
- the LP check consumes `LE` constraints only, so a `GE` or `EQ` constraint would be silently
  dropped from the model it solves. There are none in this release, and the independent solve
  handled all three senses and agreed.
- the analogous-pair check flags holdout-to-holdout pairs only, not an analog drawn from the
  holdout into another split. **That stronger property was checked here and holds.**
- the DSM boundary check reads the alias table only, not the asset map, the Package A README or the
  resolution document. **All four were checked here and agree.**
- the branch counts in `abm_rule_ground_truth.csv` are not recomputed by the validator at all.
  **They were recomputed here from the state history and agree.**

## 5. Generator reproducibility

The builder was run **twice**, from the bundled v0.1 base archive, into two different output roots
and two different ZIP directories, with more than a minute between the runs so that a current-time
dependence would show. Dependencies were the pinned `requirements-lock.txt` versions, installed in
an isolated virtual environment. Machine-readable: `code_audit/synthetic_v02_reproducibility.csv`.

| Property | Result |
|---|---|
| Same file set | pass, 118 files both times |
| Byte-identical file contents | pass, all 118 |
| Byte-identical combined ZIP | pass |
| Byte-identical Package A ZIP | pass |
| Byte-identical Package B ZIP | pass |
| Byte-identical Package C ZIP | pass |
| No output-path dependence | pass, two different roots produced identical bytes |
| No current-time dependence | pass, the builder pins its generated-at stamp and its ZIP entry times |
| No filesystem-order dependence | pass, trees walked and hashed independently and compared by relative path |
| Regenerated tree matches the staged extraction | pass, all 118 files |
| **Rebuilt combined ZIP equals the supplied archive** | **pass, sha256 `2606b6bf…13139e1a` both** |
| Recorded seed `20260811` | pass |
| Builder, validator and base-archive checksums match `BUILD_PROVENANCE.json` | pass, all three |

The strongest result available was obtained: rebuilding from the bundled base reproduces the
delivered archive **bit for bit**, so the delivered bytes and the recorded provenance are the same
build.

**One reproducibility caveat, found rather than assumed.** `requirements-lock.txt` pins numpy,
pandas, scipy, networkx and openpyxl but **does not pin `lxml`**. openpyxl serialises the workbook
through lxml when it is installed and through the standard library when it is not, and the two
serialisations differ in namespace placement and empty-element spacing. With lxml absent,
`package_summary.xlsx` rebuilds to different bytes, and `MANIFEST.csv` and `CHECKSUMS.sha256`
follow it because they carry its digest. Nothing about the data changes: all 116 data and
documentation files are byte-identical either way, and the validator still reports 681 and zero.
**To reproduce the archive bit for bit, lxml must be present.** That belongs in the lock file.

**A related operational warning.** Installing lxml into the interpreter that runs the repository
suites breaks three of them (`test_export_workbook.py`, `test_run5_export.py`,
`test_training_gating.py`) because the export workbook is then serialised through lxml and the
suites reparse it. The reproducibility environment must stay isolated from the repository test
environment. This run used a separate virtual environment for the rebuild and removed lxml from the
repository interpreter before the final suite run.

## 6. Closure of the prior six findings

Machine-readable: `code_audit/synthetic_v02_gap_closure.csv`.

| Prior finding | Closed | Evidence, recomputed rather than read |
|---|---|---|
| 1. NCR Rate corpus absent | **yes** | `quality_audits.csv` (36), `ncr_events.csv` (69), `ncr_ground_truth.csv` (36) exist and reconcile. Issued, closed, open, overdue, cumulative inspections, incidence per hundred inspections, closure ratio, open ratio, overdue open ratio and mean open age were recomputed from the event rows at every one of the 36 period cutoffs; all 360 quantities agree. Every NCR traces to a declared audit. |
| 2. Environmental Compliance Rate corpus absent | **yes** | `environmental_requirements.csv` (48), `environmental_assessments.csv` (288), `environmental_violations.csv` (28), `environmental_ground_truth.csv` (36) exist. Applicable, assessed, compliant, noncompliant, unassessed, the compliance rate and severe noncompliances were recomputed at all 36 periods and agree. Assessments resolve to requirements and violations resolve to assessments. |
| 3. CCPM traceability and sizing | **yes** | 18 chains, 72 chain activities, 72 sizing inputs, 108 buffer rows. Every chain activity, buffer and sizing input traces to a declared chain and to a real schedule activity, and `schedule_activities.csv` now carries `ccpm_chain_id` and `ccpm_chain_type`. PERT sigma and variance were recomputed from the three-point estimates, the variance sums recomputed per chain, and **every original buffer recomputed as 1.645 times the root of the summed variance**, agreeing to within 1e-6. **The flat fifteen per cent sizing is absent**: no chain's buffer equals fifteen per cent of its chain length. |
| 4. Agent decision rules | **yes** | `agent_decision_rules.csv` defines three ordered branches; `agents.csv` (48) and all 576 rows of `agent_state_history.csv` resolve to a declared rule and branch. Every condition and action parses as a JSON object. Branch selection was **replayed independently** by evaluating the declared conditions in rule order for all 576 state rows, and the branch counts in `abm_rule_ground_truth.csv` were reproduced for all 12 rows. |
| 5. DSM package boundary | **yes** | DSM is assigned to Package A consistently in `module_asset_map.csv`, `module_id_aliases.csv`, the Package A README and `AUDIT_RESOLUTION_v0.2.md`, and the three DSM files physically live in Package A. Package A is the right boundary because the matrix is a project-specific dependency structure. |
| 6. Linear-programming model form | **yes** | `lp_models.json` declares `LP-MODEL-0.2` with 12 models, each carrying a numeric objective coefficient vector, numeric variable bounds, numeric constraint coefficient vectors with right-hand sides and senses, a solver reference, and a ground-truth solution, objective and success flag. **All 12 were solved independently**, handling all three constraint senses and the objective sense, and every objective value and success flag matches the stored ground truth to within 1e-4. |
| 7. Module numbering | **partly** | `module_id_aliases.csv` is a genuine **one-to-one** mapping: 39 rows, 39 distinct literature ids, 39 distinct code ids, no collision in either direction, and the asset map agrees with it on every row it covers. `7.19 -> B2.19`, `4.4 -> A4.4` and `8.8 -> A6.3` are all present and correct. **Residual:** two of the eleven Run 8 modules in scope, Monte Carlo EAC and Scenario Modeling, have **no row in the alias table or the asset map**, so those two repository joins remain manual. |

## 7. Run 8 reconciliation, all Bucket 3, 4 and 5 modules

The module set was read from `code_audit/run8_module_classification.csv` and set equality is
asserted by the build script, so drift in either direction fails rather than passing quietly:
Bucket 3 = 7, Bucket 4 = 2, Bucket 5 = 2, eleven modules. Completeness is judged by whether the
asset supplies the defining canonical structure, not by filename. Machine-readable:
`code_audit/synthetic_v02_run8_reconciliation.csv`.

| Code Module ID | Literature ID | Module | Run 8 Bucket | Package | Required Structure | v0.2 Assets | Complete? | Remaining Gap |
|---|---|---|---|---|---|---|---|---|
| A1.1 | not mapped | Monte Carlo EAC | 3 | A | cost risk quantification: three-point or distributional cost ranges per risk or work package | cost_risk_events.csv, cost_elements.csv, cost_correlations.csv, cost_risk_ground_truth.csv | yes | no alias or asset-map row, so the join is manual |
| A2.2 | 2.2 | Line of Balance | 3 | A | locations or units, crews, quantities and production rates | lob_work_packages.csv, lob_ground_truth.csv | yes | none |
| A2.3 | 2.3 | CCPM Buffer Health | 3 | A | a critical chain with a project buffer and feeding buffers sized from activity estimates | ccpm_chains.csv, ccpm_chain_activities.csv, ccpm_buffer_sizing_inputs.csv, ccpm_buffers.csv, ccpm_ground_truth.csv | yes | none; every activity and buffer traces to a chain and every buffer recomputes from the RSS PERT variance at z = 1.645 |
| A4.4 | 4.4 | NCR Rate | 3 | A | an audited nonconformance cohort carrying a findings total | quality_audits.csv, ncr_events.csv, ncr_ground_truth.csv | yes | none; the corpus absent in v0.1 now exists and recomputes at every cutoff |
| A5.6 | 5.6 | Queueing Theory Bottleneck | 3 | A | arrival and service processes, capacity and a queue discipline | queue_events.csv, queue_ground_truth.csv | yes | none |
| A5.7 | 5.7 | Agent-Based Supply Chain | 3 | A | agents, states, rules and interactions | agent_decision_rules.csv, agents.csv, agent_state_history.csv, abm_ground_truth.csv, abm_rule_ground_truth.csv | yes | the low inventory restock branch is declared but never exercised, so replay covers two of the three branches |
| A6.3 | 8.8 | Environmental Compliance Rate | 3 | A | audited permit condition compliance | environmental_requirements.csv, environmental_assessments.csv, environmental_violations.csv, environmental_ground_truth.csv | yes | none; the corpus absent in v0.1 now exists and recomputes at every period |
| A5.4 | not mapped | Scenario Modeling | 4 | B3 | an actions-by-scenarios payoff structure with defined scenarios and probabilities | decision_problems.csv, actions.csv, scenarios.csv, action_scenario_outcomes.csv, payoff_matrices.csv, ground_truth_decisions.csv | yes | no alias or asset-map row, so the join is manual |
| B2.19 | 7.19 | CRITIC-TOPSIS | 4 | B3 | an alternatives-by-criteria decision matrix, weights computed across alternatives | alternative_criteria_matrix.csv, criteria.csv, ground_truth_decisions.csv | yes | none structurally; the degenerate single-alternative weighting remains a separate production decision |
| A3.1 | 3.1 | Reference Class Forecasting | 5 | B1 | a population of comparable completed projects with realised overruns | reference_projects.csv, reference_class_membership.csv, reference_outcomes.csv, split_manifest.csv | yes | none; **stays disabled and abstaining** |
| A5.1 | 5.1 | DSM Rework Propagation | 5 | A | a project-specific dependency matrix | dsm_nodes.csv, dsm_edges.csv, dsm_ground_truth.csv | yes | none; Package A is now the stated boundary; **stays disabled and abstaining** |

**11 of 11 complete.** This was not forced: each row was checked by the presence of the named files
and by the recomputations in section 6, and the two rows with a residual say so in their own gap
column rather than being written up as clean.

## 8. Schema and key integrity

Verified independently, against the data rather than against the schema catalogue's own claims:

- 6 projects, 36 reporting periods, period primary key unique;
- schedule activity primary key unique, every dependency endpoint resolves to a real activity in
  the same project, every status row resolves to a real activity, and all six schedule networks are
  acyclic;
- CCPM chain primary key unique, and chain activities, sizing inputs and buffers all resolve to a
  declared chain and a real activity;
- NCR events resolve to declared audits, NCR ids unique;
- environmental assessments resolve to requirements, violations resolve to assessments,
  requirement primary key unique;
- agents and all 576 state history rows resolve to a declared rule and branch;
- the alias table is one-to-one in both directions and the asset map agrees with it;
- `record_hash` is present and unique within every file, and the provenance columns are complete;
- the package-local manifests cover their packages exactly and agree with the programme manifest.

## 9. Split leakage and privacy

**Splits.** All 360 reference projects appear in exactly one split, 216 development, 72 validation,
72 locked holdout. The split manifest agrees with the inline split column for all 360, and every
derived table that carries a split agrees with the manifest on every row. Going past filenames, an
eight-field feature vector was hashed for every project and **no feature vector is shared by
projects in different splits**, so no duplicate project is smuggled across a boundary.

**Analogous pairs.** 120 pairs. Every analog is drawn from the development split; targets are
validation (55) or locked holdout (65). **No analog is drawn from the locked holdout and there is
no holdout-to-holdout pair**, so no locked-holdout information reaches another split. A holdout
target drawing development analogs is the intended direction and is not leakage.

**Privacy.** Every CSV and every JSON file was scanned for email addresses, telephone numbers,
national identifier patterns and street addresses. **Nothing was found.** Project identifiers are
archetypes (`PRJ-AIR`), reference projects are sequential identifiers (`REF-0001`), experts are
profiles rather than people, jurisdictions are explicitly synthetic (`SYNTHETIC-US`,
`SYNTHETIC-PERMIT-PRJ-AIR`), regions are broad (`US-NORTHEAST`), and there is no free-text
narrative field that could carry an employer detail; descriptions are coded values such as
`TEST_FAILURE`. No participant or employer-confidential data is present. Every record of every data
file carries `data_origin = SYNTHETIC_RESEARCH_FIXTURE`, `not_for_empirical_validation = true` and
`programme_version = OG-SYNTH-0.2`; no record lacks them and nothing was repaired.

**Nothing in this package constitutes empirical validation.** It supports implementation fidelity,
known-answer testing, structural verification, solver agreement and abstention behaviour. It does
not support predictive accuracy, calibration, threshold justification or field validity, and no
surface may describe it as validation.

## 10. Modules that remain abstaining or disabled

- **Remain disabled and abstaining: Reference Class Forecasting and DSM Rework Propagation.** Both
  were made to abstain unconditionally by Run 7. Both now have complete fixtures. **That changes
  nothing.** A fixture does not authorise a disabled module to run. Reactivation is an owner
  decision and this run did not touch either module.
- **Every other module in scope continues to behave exactly as it did before this run**, because no
  module code was touched and no module was connected to synthetic data. The two modules whose
  corpora were absent in v0.1, NCR Rate and Environmental Compliance Rate, still abstain in
  production: the corpus now exists in a research fixture, which is not the same as the platform
  having the data.
- **Voting state: unchanged for every module.** Participant-surface effect: none. The participant
  does not see the remediation; qualifiers live in the export, the API and the methods
  documentation only.

## 11. Is v0.2 ready for a separate scoped integration run

**Yes, for a test-only integration run, with three conditions.** Stated plainly: the archive
verifies completely, the packages verify independently, the validator reruns and can be made to
fail on every property that matters, the build is bit-reproducible from the bundled base, and all
eleven Run 8 modules in scope now have the canonical structure their method requires. That is the
evidence an integration run needs before it starts.

What would block or complicate it:

1. **Two unmapped modules.** Monte Carlo EAC and Scenario Modeling have no alias or asset-map row.
   An automated importer keyed on the alias table will silently skip them. Either the alias table
   gains two rows or the integration run hard-codes those two joins and says so.
2. **The lxml pin.** Anyone who needs to regenerate the archive bit for bit needs lxml, and
   installing lxml in the repository test interpreter breaks three suites. Integration work must
   keep the two environments apart.
3. **Scope discipline, which is the real risk rather than a data problem.** Integration means
   test-only importers reading `research_fixtures/`, read-only research schemas that are never part
   of the operational database, known-answer tests and abstention tests. It does not mean voting,
   activation, participant-visible change, or reactivating either disabled module. Absence of a
   fixture must continue to read as abstention and never as a healthy project.

## 12. Guarantees

| Guarantee | Status |
|---|---|
| Archive opens, no traversal, no absolute path, no symlink, single expected root | **verified** |
| All required root artefacts present and usable | **verified**, all 18 |
| Programme checksums verify, recomputed independently | **verified**, 117 of 117 |
| Checksum manifest covers every file on disk | **verified** |
| Each package has a self-contained local manifest and checksum file | **verified** |
| Each package verifies itself without files from another archive | **verified**, the v0.1 defect is closed |
| Validator reruns as documented, 681 checks, zero failures | **verified**, rerun rather than accepted |
| Validator proved able to fail | **verified**, 7 of 7 injections detected and named, then baseline restored |
| Validator coverage is as broad as the check count suggests | **partly met**, six properties named in section 4 are unchecked by it and were checked here instead |
| Generator regenerates byte-identically from the pinned dependencies | **verified**, twice, and equal to the supplied archive |
| No current-time, output-path or filesystem-order dependence | **verified** |
| Seed and builder, validator and base checksums match the provenance record | **verified** |
| Dependency versions pinned | **partly met**, lxml is not pinned and changes the workbook bytes |
| NCR corpus exists and reconciles at every cutoff | **verified**, 10 quantities at 36 cutoffs |
| Environmental corpus exists and reconciles at every period | **verified**, 6 quantities at 36 periods |
| CCPM traceable and sized from the declared RSS PERT variance at z = 1.645 | **verified**; flat fifteen per cent sizing absent |
| Agent decision rules defined, resolvable and independently reproducible | **verified**; one declared branch is never exercised |
| DSM assigned to Package A consistently in all four places | **verified** |
| LP models machine-readable and independently solvable to the stored ground truth | **verified**, all 12 |
| Alias table one-to-one in both directions, with the three named mappings | **verified** |
| Every Run 8 Bucket 3/4/5 module joinable by the alias table | **not met**, two modules unmapped |
| Provenance on every record | **verified** |
| Primary keys unique, foreign keys resolve, schedules acyclic | **verified** |
| No project or duplicate feature vector crosses a split | **verified** |
| No analogous-pair leakage involving the locked holdout | **verified** |
| No participant or employer-confidential data | **verified**, screened explicitly |
| All 11 Run 8 Bucket 3/4/5 mappings reconcile | **verified**, 11 of 11, asserted by set equality |
| No production code or database change | **verified**, nothing outside `research_fixtures/`, `tools/`, `code_audit/`, this report and the handoff |
| Disabled modules remain disabled, no voting or participant-surface change | **verified**, no module code touched |
| No synthetic data in an operational or participant database | **verified**, nothing was imported anywhere |
| Prior v0.1 staging and audit preserved unmodified | **verified** |
| Repository suite green | **verified**, 64 suites, 4,612 of 4,612 checks; see the note below |

**The suite note, so it is not mistaken for a new failure.** `run_all_suites.sh` reports
`test_run5_export.py` as having no result line. The suite itself passes, 34 of 34, and prints
`34 passed, 0 failed` rather than the `RESULT: n/n` line the runner greps for. This mismatch is
pre-existing on `main` from the Run 5 merge and is untouched by this run, which changes no test
code. It is worth fixing in a run that is allowed to change that file.

## 13. Owner decisions

1. **Add lxml to `requirements-lock.txt`**, or accept that the workbook is not byte-reproducible
   across environments and that only the 116 data and documentation files are.
2. **Add alias and asset-map rows for Monte Carlo EAC and Scenario Modeling**, or accept two manual
   joins in the integration run.
3. **The unexercised agent branch.** Either regenerate so the low inventory restock branch occurs,
   which would let a known-answer test cover all three branches, or accept two-branch coverage.
4. **Authorise the scoped integration run**, on the terms in section 11, or hold.
5. **Reactivation of Reference Class Forecasting and DSM Rework Propagation.** Still no, unless the
   owner decides otherwise. A complete fixture is not a reason.
6. **Whether the fixture stays committed** in the repository. This run committed it, on the same
   reasoning as v0.1: the audit is worthless without the bytes it ran against.
