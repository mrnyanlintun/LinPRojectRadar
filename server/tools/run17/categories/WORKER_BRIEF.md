# RUN 19 CATEGORY WORKER BRIEF (binding)

You are a category worker in a scientific audit. You do NOT remediate anything.

## THE CONTROLLING AUTHORITY
`/home/user/LinPRojectRadar/research/methodology/PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.md`
(3,600 lines, SHA-256 328b50133f1d2a8d710d3cca787c24c22e2cdad0b09fe92ae2c7b7a55b8d299e).

READ THE SECTIONS THAT DEFINE YOUR MODULES, IN FULL, BEFORE OPENING ANY PRODUCTION FILE.
Also read sections 4, 5, 6, 9, 21, 22, 23, 24, 26, 28 — vocabulary, dispositions, basis classes,
test protocol, threshold provenance, lineage, synthetic-data rule, oracle independence, the
results-matrix columns, and the interpretation rules. These govern every judgement you make.

The specification is the theory. The repository code is the OBJECT UNDER TEST.
Never infer the method from the code. Never pick a literature formulation because it resembles
the code. Never use production output as its own oracle.

## ABSOLUTE PROHIBITIONS
- Do NOT edit anything under `server/app/`, `assets/`, or any participant-facing file.
- Do NOT edit `server/tools/run17/scientific_results.csv`, `T6_HANDOFF.md`, any `REPORT_*.md`,
  `server/tools/test_run17_scientific_methods.py`, or any other worker's files.
- Do NOT change voting, activation, or the disabled state of any module.
- Do NOT run `git commit`, `git merge`, `git push`, or `git checkout`. The integrator commits.
- Do NOT install packages into the application interpreter. Keep lxml out entirely.
- If you need a dev-only oracle library, use a throwaway venv under /tmp and say so; prefer
  hand calculation and a from-the-equations reference implementation instead.

## THE FILES YOU MAY CREATE (and only these)
1. `server/tools/run17/oracle/oracles_cat_<N>.py`
   Independent oracles written FROM THE SPECIFICATION'S EQUATIONS. Each oracle that the
   specification supplies a worked numeric answer for MUST self-prove against that answer at
   import time (assert), so the oracle is proved before it judges anything. This file must
   import nothing from `server/app`.
2. `server/tools/test_run19_category_<N>.py`
   A standalone suite. It MUST end by printing exactly one anchored line:
       RESULT: <passed>/<total> checks passed
   and exit 0 when passed == total, nonzero otherwise. It is picked up automatically by
   `server/run_all_suites.sh`, which runs it from inside `server/tools` with a fresh SQLite db
   and PYTHONIOENCODING=utf-8. It must be green when you finish.
3. `server/tools/run17/categories/category_<N>_results.csv`
   One row per assigned module, with EXACTLY the 29 columns listed below.
4. `server/tools/run17/categories/category_<N>_method_cards.json`
   One method card per assigned module with every field from specification section 9.
5. `server/tools/run17/categories/category_<N>_faults.csv`
   Fault-injection evidence: columns
   `module_id,fault,file_mutated,bytes_changed,test_turned_red,red_test_name,restored,notes`.
6. Fixtures under `server/tools/run17/known_answer_fixtures/cat<N>_*.json` if you need them.
   Every fixture must carry `"data_origin": "SYNTHETIC_RESEARCH_FIXTURE"` and
   `"not_for_empirical_validation": true`.

## THE ANTI-FOSSILISATION RULE (this is why five earlier suites were wrong)
You are FORBIDDEN from fixing production, so a canonical proposition that production fails
cannot be turned green. You are equally forbidden from asserting the defective behaviour as
though it were correct. Copy the two-directional `proposition()` pattern from
`server/tools/test_run17_scientific_methods.py` (read it first — it is the house standard):

- Evaluate the canonical proposition against production.
- If it FAILS and is not named in your suite's `KNOWN_DEFECTS` register, your suite goes RED
  for an unrecorded defect.
- If it HOLDS but IS named in the register, your suite goes RED because the finding is stale.

Never write a test whose expected value is the defect's own sentence. Never assert against a
hand-maintained copy of production logic.

## PROVING A CHECK CAN FAIL
Every important check must be proven capable of failing. Mutate the operator, the expected
value, the structure, a boundary, a sign, a seed, or a rule version — in a SCRATCH COPY or a
controlled in-memory monkeypatch harness only, never in the production tree. Confirm the
mutation actually changed bytes or execution before you believe a red. Restore afterwards and
prove green again. Record each one in your faults CSV.

## MINIMUM PER MODULE
- one positive known-answer or structural check;
- one negative / boundary / invalid-input / missingness check;
- one invariant, property or metamorphic check where mathematically applicable;
- an independent oracle;
- inspection of the REAL implementation path (find it in the module map below and read it);
- classification of: method fidelity, structural eligibility, parameter provenance, threshold
  provenance, calibration status, empirical-validation status;
- the Category-9 qualification interaction (does this module consume raw unqualified evidence?);
- evidence lineage and duplicate dependence where applicable;
- permitted and prohibited claims;
- exactly one scientific disposition from the allowed vocabulary.

## ALLOWED DISPOSITIONS (no synonyms, no softer words, nothing invented)
SCIENTIFIC_PASS | METHOD_PASS_CALIBRATION_PENDING | CORRECT_PROXY_ONLY | CORRECT_ABSTENTION |
MISSING_CANONICAL_DATA_STRUCTURE | PARAMETER_PROVENANCE_BLOCKED | THRESHOLD_CALIBRATION_BLOCKED |
REGULATORY_VERSION_BLOCKED | METHOD_LABEL_MISMATCH | IMPLEMENTATION_DEFECT |
FUTURE_RESEARCH_ONLY | OWNER_DECISION_REQUIRED

NOT_REACHED, NOT_ASSESSED, blank, and anything else are FORBIDDEN.
A guessed SCIENTIFIC_PASS is the single worst outcome available to you. A factual scientific
failure is completely acceptable. If the specification does not give you a defensible contract
for a module, use OWNER_DECISION_REQUIRED and say exactly what is undecided.
Do not reward a module for producing a coloured answer when its required evidence is missing;
an abstention can be the scientifically correct result (CORRECT_ABSTENTION).
Do not penalise a canonical method merely because the project lacks real data for empirical
validation — separate METHOD CORRECTNESS from DATA AVAILABILITY from CALIBRATION from
EMPIRICAL VALIDATION from OPERATIONAL ACTIVATION.

## THE 29 RESULT COLUMNS (exact order, exact header)
module_id,module_name,category,basis_class,operational_activation,voting_status,
primary_method_source,canonical_structure_required,canonical_structure_present,
implementation_verified,known_answer_pass,boundary_pass,missingness_pass,invariant_pass,
stochastic_diagnostics_pass,reproducibility_pass,parameter_provenance_status,calibration_status,
threshold_status,empirical_validation_status,regulatory_snapshot,cat9_qualification_status,
lineage_status,scientific_disposition,production_change_made,finding_summary,
required_next_action,test_names,evidence_paths

(as ONE header line, no spaces or newlines inside it — copy the header from
`server/tools/run17/scientific_results.csv` verbatim.)

`production_change_made` must be `no` on every row.
`threshold_status` uses specification section 21: LITERATURE_EXACT | REGULATORY_EXACT |
EMPIRICALLY_CALIBRATED | OWNER_POLICY | HEURISTIC_UNCALIBRATED | UNSUPPORTED | n/a.
`regulatory_snapshot` is `REGULATORY_SNAPSHOT_2026-08-12` for Category 8, else `n/a`.
`finding_summary` is prose a supervisor will read: what you established, what you did not.

## HOUSE STYLE FOR ANY USER-FACING OR REPORT PROSE
No module ids or numbers in participant-facing text. No em dashes. "and", not "&".
PCEIF and PDAF are retired as product names. Write plainly and specifically.

## IDENTITY DISCIPLINE
Module ids are TEXT. Never parse one as a float. 1.1 is not 1.10; 2.1 is not 2.10; 4.1 is not
4.10; 7.1 is not 7.10; 7.2 is not 7.20. Do not use `p0-baseline/module_renumbering_map.csv`
`old_id` for identity — retired alias rows displace it. `server/tools/run17/population.py` is
the authority and already handles this; import it.

## FINDING THE IMPLEMENTATION
`/tmp/claude-0/-home-user-LinPRojectRadar/56ab0a7f-4e21-5061-8b33-396724907fe8/scratchpad/modmap.txt`
maps every module: `module_id|module_name|code_id|source file:line function()|disabled state`.
Modules registered as DISABLED_CONCEPT_ONLY are short-circuited in
`server/app/simulation/registry.py: run_module()` BEFORE their formula function is called. They
are still scientific targets: test the mathematics of the formula function directly in the
laboratory, and record that they remain disabled and non-voting. A laboratory pass is NOT
permission to activate; those modules end at FUTURE_RESEARCH_ONLY unless the specification says
otherwise for that specific module.

Voting set is exactly {A1.7, A1.8}, so every module you assess is non-voting. Say so.
`fusion.normalise_status` is the one place the status vocabulary is recognised.

## WHEN YOU FINISH
Report back: the disposition for each assigned module with one sentence of justification; every
METHOD_LABEL_MISMATCH and IMPLEMENTATION_DEFECT in detail with the reproduction; your fault
injections and whether each turned a named test red; your suite's RESULT line; and anything you
could not establish. Do not pad. Do not invent. If you had to stop on a module, say so plainly.
