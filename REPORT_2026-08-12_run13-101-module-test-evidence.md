Run 13 — 101-Module Independent Test Evidence
Starting commit: 7e8648b
Ending audit commit: (recorded at the end of this report)
Simulation version under test: sim-2026.08-v7
Synthetic package: OG-SYNTH-0.3
Participant package: og-participant-2026.08-v1
Registered project modules: 96/96
Registered portfolio modules: 5/5
Registered total: 101/101
Non-disabled project modules: 88
Non-disabled portfolio modules: 5
Non-disabled total: 93
Disabled modules: 8
Modules individually exercised: 101/101
MATCH: 83
MISMATCH: 8
NOT_TESTABLE: 2
NOT_APPLICABLE: 0
DISABLED_AS_DESIGNED: 8
Voting modules exercised: 2/2
Existing full suite: 6102/6102
Run-13 checks: 188/188
Mutation proofs: 83/87 proven, 4 unconditional abstentions with no fault site
Production algorithms modified: NO
Participant-visible behavior changed: NO
Architectural dispositions assigned: NO

**This run collected evidence. It assigned no disposition. Nothing was repaired, and the eight
mismatches below are reproduced and left standing for the owner to judge.**

**101 registered entries are not 101 validated algorithms, and this report does not describe them
as any such thing.** Eight are disabled and execute nothing. One is registered and not
implemented. Of the rest, the reading itself is verified against an independently derived
expected value only where one exists, and every row says which.

## 1. Handoff audit

`T6_HANDOFF.md` was read end to end and compared against the `REPORT_*` files on disk and the
version records. **No repair was needed and none was invented.** Every session through Run 12 is
represented in chronological order, each with its date, branch, commit, simulation version,
package versions, scope, files, voting state, test totals, deviations and next-session
requirements. The Run 12 entry names its ending commit `73933a3` and its merge `058345c`; the
starting commit for this run, `7e8648b`, is the descendant that records that merge, and it is
the head of `origin/main`. The two discrepancies Run 12 recorded rather than reconstructed
remain true: there is no `COMMON_PREAMBLE.md` in this repository, and the `code_audit/run10_*.csv`
files named in the Run 10 entry are not present. Neither was fabricated here.

The pre-change suite reproduced the recorded baseline exactly: **77 suites, 6102 of 6102**, each
against its own freshly migrated database.

## 2. Gate 0 — the frozen target

`origin/main` fetched; starting commit `7e8648b` confirmed; working tree clean. Simulation
version read from the code as `sim-2026.08-v7`. Fifty-nine production files (every file under
`server/app/simulation/`, `server/app/documents.py` and every live browser asset) were hashed
before any test was written; the same fifty-nine were hashed at the end and **all fifty-nine are
byte-identical**. The record is `code_audit/run13_production_hashes.sha256`.

The strict harness was re-proved, by running **the real `run_all_suites.sh`** over a staged copy
of the server directory containing four planted suites and nothing else: one printing prose
instead of a result line, one reporting 3 of 4, one printing a green result line and then exiting
3, and one dying silently. The runner failed all four and exited nonzero. That proof is checks
inside the Run 13 suite, so it re-runs on every future run rather than being a claim in a report.

## 3. Gate 1 — the exact 101-module inventory

`code_audit/run13_master_101_inventory.csv`, 101 rows, one per registered module, derived
mechanically by `server/tools/build_run13_inventory.py` from `p0-baseline/module_renumbering_map.csv`
(the same source the frontend registry is generated from), the implementation tables, the disabled
set, the voting set and the canonical-structure contracts. Aliases are not counted: the row set is
exactly the set of live `new_id` values, 101 distinct ids, and the retired rows are excluded by the
same rule the production registry applies.

Reconciliation, all derived and all asserted in the suite:

| | Project | Portfolio | Total |
|---|---|---|---|
| Registered | 96 | 5 | 101 |
| Disabled | 8 | 0 | 8 |
| Non-disabled | 88 | 5 | 93 |
| Executable | 87 | 5 | 92 |
| Voting | 2 | 0 | 2 |

The one non-disabled project module that is not executable is **A4.1**, registered and never
ported. `registry.run_module` raises `MissingModuleError` for it rather than approximating, which
is the governed contract, and that refusal is what was tested.

## 4. Gate 2 — the disabled population

Derived from the registry, not from the prompt: **A3.8 Parametric Cost Index, B2.7 Plithogenic
Sets, B2.9 Quantum Probability, B2.20 Hypersoft Sets, B4.1 Multi-Objective Optimization,
B4.2 Linear Programming, B4.5 Decision Sensitivity Matrix, B4.6 Pareto Frontier Analysis.** Eight,
exactly the historical set, all project-level.

For each, proved: the registry marks it disabled; `run_module` short-circuits it before its
formula function is reached and returns a refusal with no band; it carries the disabled activation
state; it cannot vote; it produces no result on the real computation path, so it reaches neither
fusion, nor the rollup, nor recommendations, nor courses of action, nor the decision card; and
supplying it canonical structures does not reactivate it. Recorded factual state
`DISABLED_AS_DESIGNED` for all eight. **Whether any of them should ultimately be retained or
removed is not decided here.**

## 5. Gate 3 — oracle methodology, stated before any result

Two oracles were used and they are never conflated, because they are not equally strong.

**The contract oracle** is independent of production arithmetic and applies to every module. It
is read from the governed registry, `canonical.py`, `field_registry.py` and the abstention
contract: a module must not raise on an input the platform can actually deliver; it must abstain
with a reader's sentence rather than substitute a figure; it must be deterministic; a portfolio id
must be refused on the single-project path; a defining structure that is absent must produce a
refusal and not a proxy; and **removing evidence must never improve the reading**. Every module
was tested against all of it.

**The numeric oracle** is the independently derived expected value for a nominal case. It exists
where a committed known-answer suite carries a hand-derived literal for the module, and for the
two voters it was derived again by hand in this run. Where it does not exist, the row says
`NOT INDEPENDENTLY ESTABLISHED` in `expected_nominal_result` and the oracle confidence is LOW.
**No production result was ever read back and recorded as the expected answer.**

Reachability is decided by the governed numeric contract rather than by the harness. A value that
`extraction_merge.validate_numeric_fields` refuses at every entry point (a string, an infinity, a
NaN, a negative in any field outside `SIGNED_SI_FIELDS`) cannot reach a module in production, so a
module raising on one is recorded as a **stated reliance on the ingestion contract, not as a
defect**. Thirty-nine such reliances are recorded in the anomaly file as observations. What no
layer bounds is an upper limit: no range check anywhere refuses a percentage above one hundred,
and that is where five of the eight mismatches live.

## 6. Gates 4 and 6 — every non-disabled project module

`server/tools/build_run13_evidence.py` exercises all 87 executable project modules individually,
**no sampling**, through the real production entry points (`registry.run_module`,
`registry.run_all`, `compute.compute_project`). **2,508 test cases** were executed across the
dimensions: nominal; boundary; domain; missingness with every read input dropped one at a time;
malformed input across six malformed values per input; canonical structure; determinism and
vocabulary invariants; and the real run-and-store path. The per-module record is
`code_audit/run13_101_module_evidence.csv`, 101 rows, thirty-four columns.

Sweeps run across all applicable modules: out-of-domain favourable banding; missing evidence
improving the reading; non-finite output; abstention without a reason; absence from the real
computation path; canonical method replaced by a proxy; and layer leakage. Because every module
was exercised on every input it reads, each sweep is exhaustive by construction, so the neighbour
set for a defect class is the complete set that shows it rather than a sample.

## 7. Gate 5 — the five portfolio modules

Tested separately through `portfolio.compute_portfolio`, on a designed four-project portfolio
where every rank is countable by hand.

- **D1.2 Portfolio Outlier** — cost and schedule percentiles of 50 and a composite of 50, counted
  by hand and matched exactly. MATCH.
- **D1.3 Trajectory Classifier** — 0.9, 1.0, 1.1 is two intervals of one tenth, so the trend is
  0.1 per period, derived by hand and matched; a flat history is exactly zero; with no usable
  history the module is **absent** rather than present with a colour. MATCH.
- **D1.4 Cross-Project Pattern** — four identical projects give a count of three, so a project is
  never counted as similar to itself; adding one project inside the radius raises the count by
  exactly one. At a hand-computed distance of exactly the radius the comparison is strictly less
  than, and binary rounding decides membership; that is recorded rather than asserted away.
  MATCH.
- **D1.5 Anomaly Score** — with no history the composite is the mean of exactly two measured
  terms, recomputed independently from its own published components; no placeholder third term
  enters it. MATCH.
- **D1.1 Isolation Forest** — the distance is reproducible, but the threshold multiplier of 1.5
  and the band fractions 0.7 and 0.4 have no cited source and no reference population exists
  against which an anomaly threshold could be derived. **NOT_TESTABLE**, with that as the exact
  missing evidence.

Across all five: the denominator is the count of projects carrying both indices, each counted
once; zero and one-project portfolios abstain rather than fabricating a denominator; a project
without signal data leaves the population rather than entering it as a neutral value; a reported
zero index stays in the population because it is a measurement; the computation is deterministic
and its result keys are stably ordered; a null portfolio abstains and a portfolio with no current
project id is refused outright; computing the portfolio changes neither any project's status nor
the voting set; and `registry.run_module` refuses every one of the five ids on the single-project
path. The small-portfolio guard admits two projects while its message says three, reproduced
verbatim from the validated source and recorded here, not corrected.

## 8. Gate 9 — the two voters

Mechanically identified as exactly **A1.7 and A1.8**, both cost lineage, and the fusion's own
`voting_module_ids` agrees. No other module reports itself as voting.

**A1.7, to-complete performance index.** Hand-derived: a budget of 1,000,000 with 400,000 earned
and 500,000 spent leaves 600,000 of work against 500,000 of remaining budget, which is 1.2, above
the published 1.10 boundary, therefore Red. Matched. The definitional boundary of exactly 1.00 is
Green. It refuses a zero budget, earned value above budget and spent above budget, and abstains
when any of its three inputs is absent.

**A1.8, variance at completion.** Hand-derived: a cost index of 0.8 on a budget of 1,000,000
forecasts 1,250,000, a variance of minus 250,000, minus 25 per cent of budget, below the published
minus 11.11 boundary, therefore Red. Matched to the currency figure and the percentage. Exactly
zero variance is Green; a cost index of 0.90 is the minus 11.11 boundary and is Amber; 0.89 is
Red. It refuses a zero and a negative cost index and a zero budget, and abstains when either
input is absent.

Both agreeing badly and both agreeing well give different project statuses; with neither available
the project still returns an answerable status field; and every status the fusion returns is inside
the one recognised vocabulary, which `fusion.normalise_status` remains the single place to
recognise. **The voting set stays exactly two and nothing else can move Cost Recovery Status.**

## 9. Gate 7 — stochastic modules

Exactly three are declared stochastic: A1.1, A1.2, A2.1. The seed is derived from scenario and
period only, so the same scenario and period reproduce every figure exactly and a different period
draws a different stream; the forecast module records the seed it drew on, so any figure can be
reproduced. A constant generator gives a reproducible result and every figure it reports is
finite. Impossible parameters abstain rather than being simulated from. No different statistical
family was used as an oracle, and the synthetic fixtures are treated as evidence about
implementation mechanics only, never about predictive validity.

## 10. Gate 8 — optimisation and decision methods

Four of the modules named for an optimisation method (Multi-Objective Optimization, Linear
Programming, Decision Sensitivity Matrix, Pareto Frontier Analysis) are in the disabled set, so no
defining mathematical object is claimed to exist for them and none was found. Among the live
modules, B4.7, named for regret minimisation, abstains without an actions-by-scenarios payoff
matrix rather than reporting a regret computed from something else. A5.4 and B2.19 do have a
defining object and apply the version, split and self-comparison guards before reading it: a
decision object drawn from locked holdout material is refused, and one carrying no asset version
is refused. What they also do without that object is the subject of two of the mismatches below.

## 11. Gate 12 — mutation proof

`code_audit/run13_mutation_proof.csv`, one record for each of the 87 executable project modules.
Production files are never edited: for each module an **isolated copy** of its own implementation
source is compiled with a fault injected (comparisons reversed, arithmetic reversed, or every
branch guard inverted; and where a module is a thin wrapper, the fault goes into the worker it
delegates to and the unmutated wrapper is compiled against it). Each run is bounded in a forked
child, because a reversed loop guard does not terminate.

**83 modules turned red under a fault and returned to their exact baseline behaviour afterwards.**
Four (A2.1, A3.1, A5.1, B4.7) abstain unconditionally: they have no branch, no comparison and no
arithmetic, so no fault can change their output, and that is recorded as
`UNCONDITIONAL_ABSTENTION_NO_FAULT_POSSIBLE` rather than dressed up as a proof. Every record
carries the implementation file hash before and after, and all 87 are unchanged. **No expected
answer was mutated anywhere.**

## 12. Gate 10 — one computational authority

The participant page loads neither browser instrument file; the only mentions left in `index.html`
are comments recording why they are gone. The historical arithmetic remains on the researcher
deep-dive route only, and that route loads the version guard before it. The guard stamps the
browser arithmetic `client-legacy-2026.07-historical` and does not carry the current simulation
version, so a historical figure cannot present itself as the current analysis. On the served
result, abstention survives with its reason on every abstaining module, the single-lineage
conflict state `NOT_ESTIMABLE_SINGLE_LINEAGE` is carried rather than computed for display, no
coefficient is published beside it, and the governed label is Cost Recovery Status. **No browser
behaviour was modified in this audit.**

## 13. Gate 11 — Category-9 interaction

The qualification object is rebuilt on the audit's own project. The only numbers anywhere in it
are counts of evidence inside the provenance and timeliness blocks; no dimension carries a
composite score and no dimension state is a number. Provenance and timeliness report PARTIAL,
revision resolution reports NOT_ESTIMABLE, exactly as governed. Removing an input cannot increase
the number of modules that produced a reading and cannot turn a non-green project green, so
qualification cannot fabricate a healthy status; and it creates no vote, the voting set being read
from the registry alone.

## 14. Every MISMATCH

Eight, all in `code_audit/run13_failures_and_anomalies.csv` with input, actual output,
independently expected output, code path, oracle, defect class and likely technical cause.
**None of the eight is a voting module, so none of them can affect Cost Recovery Status.** None
was repaired.

**Class A — a percentage above one hundred is unguarded and reads as health (5 modules).**
A2.11 Critical Path Index, A3.2 Contingency Burn Rate, A3.3 Labor Productivity Index,
A3.5 Overhead Absorption Rate, A5.8 Discrete Event Simulation. Setting reported progress to
10,000 per cent moves each of them from a non-green band to Green. The likely cause is common to
all five: banding is applied before any domain guard, and no layer bounds a percentage from above.
`validate_numeric_fields` refuses a negative and refuses a malformed value, and `_range_check`
returns early for the one field with its own guard, but no upper limit is checked anywhere, so the
value is production-reachable. The neighbour sweep for this class is exhaustive: every module was
driven on every input it reads, and these five are the complete set that shows it.

**Class B — removing evidence improves the reading (2 modules).**
A3.5 Overhead Absorption Rate: with reported progress absent, the planned indirect cost is used
whole instead of prorated to progress, so the denominator grows, the absorption ratio falls and the
band improves from Red to Yellow. C1.6 Cross-document Consistency Score: dropping reported progress
or the budget moves it from Amber to Green, because a field that is absent cannot be inconsistent
with anything. A3.5 therefore carries both classes.

**Class C — the named method is replaced by a stated proxy when its defining structure is absent
(2 modules).** A5.4 Scenario Modeling computes three deterministic forecasts under three divisors,
and B2.19 CRITIC-TOPSIS computes a single-project closeness whose criterion weighting degenerates,
when no decision problem and no decision matrix are supplied. Both are deliberate and disclosed:
Run 10B added the real method where the structure exists and recorded in the code that keeping the
prior behaviour was outside its authorisation. It is recorded as a mismatch here because the
independent contract for a module named after a method is that it abstains rather than producing an
unrelated reading, and the disclosure does not change what the module does.

A6.3 Environmental Compliance Rate was examined for the same class and is **not** an instance: its
structure is an audited permit-condition cohort and its other input is the audited compliance
rate, which is the same governed quantity in a second form, and with neither form present it
abstains.

## 15. Every NOT_TESTABLE, and the exact missing evidence

**A1.2 CUSUM Anomaly Monitor.** Every contract dimension conforms, but no independently derived
expected value exists for its reading. Missing: a hand-derived expectation for the two-sided
cumulative sum as this module parameterises it. Its own registry qualifier already states that
the control constant, the decision interval, the deviation floor and the Amber band are
uncalibrated, so there is no governed value to derive one from.

**D1.1 Isolation Forest.** The distance is reproducible and its aggregation semantics are proved,
but the anomaly threshold is the mean distance plus 1.5 times the summed deviations, and neither
the 1.5 nor the 0.7 and 0.4 band fractions has a cited source; no reference population exists
against which any of them could be derived. Missing: a source for those constants, or a labelled
population.

A NOT_TESTABLE result was preferred to an invented oracle in both cases.

## 16. Count reconciliation

All headline counts are derived mechanically from the 101-row evidence file.

- REGISTERED: Project 96/96; Portfolio 5/5; Total 101/101
- NON-DISABLED: Project 88; Portfolio 5; Total 93
- DISABLED: Project 8; Portfolio 0; Total 8
- FACTUAL RESULTS: MATCH 83; MISMATCH 8; NOT_TESTABLE 2; NOT_APPLICABLE 0; DISABLED_AS_DESIGNED 8
- TOTAL UNIQUE MODULE ROWS: 101
- VOTING: 2; expected 2

## 17. Production-file hash comparison

Fifty-nine production files hashed at Gate 0 and again at the end of the run: **all fifty-nine
identical**. `git diff` against `origin/main` shows no change under `server/app`, `assets`,
`index.html`, `research` or `backend`. Recorded in `code_audit/run13_production_hashes.sha256`.

## 18. Evidence files for the owner's classification

- `code_audit/run13_master_101_inventory.csv` — the canonical inventory, 101 rows.
- `code_audit/run13_101_module_evidence.csv` — the per-module evidence, 101 rows.
- `code_audit/run13_failures_and_anomalies.csv` — 48 rows: the eight mismatches, the two
  not-testable modules and the thirty-nine recorded reliances on the ingestion contract.
- `code_audit/run13_mutation_proof.csv` — 87 rows.
- `code_audit/run13_production_hashes.sha256` — the frozen-target hashes.
- `server/tools/build_run13_inventory.py`, `build_run13_evidence.py`,
  `build_run13_mutation_proof.py` — the derivation scripts.
- `server/tools/test_run13_module_evidence.py` — 188 checks, in the strict suite.

## 19. Limitations of this run

The suite total rests on the committed known-answer suites for most nominal readings; where that
is the oracle, the row says so and its confidence is MEDIUM, because a hand-derived literal
committed in an earlier run is strong evidence about arithmetic and no evidence at all about
whether the arithmetic measures what its name claims. Band boundaries outside the two voters
remain unsourced across the platform, so a MATCH means the module computed what its contract says
it computes, never that its band is right. No labelled corpus and no expert reference standard
exist here, so no module's false-positive or false-negative performance is measured, and nothing
in this report should be read as validation or calibration. Nothing was driven in a browser in
this run; the Gate 10 findings are from the served files and the stored result, and the live-route
evidence remains the Run 11 and Run 12 records.

## 20. Suite and merge

Complete suite on the branch: **78 suites, 6290 of 6290**, each against its own freshly migrated
database, and reconfirmed on merged main. No stop condition was hit.
