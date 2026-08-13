Run 19 — Complete 100-Module Scientific Audit
Starting commit: d0af5a3
Run-18 merge commit: d0af5a3
Ending merge commit: PENDING
Supervisory specification committed: YES
Specification repository path: research/methodology/PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.md
Source attachment SHA-256: 328b50133f1d2a8d710d3cca787c24c22e2cdad0b09fe92ae2c7b7a55b8d299e
Committed specification SHA-256: 328b50133f1d2a8d710d3cca787c24c22e2cdad0b09fe92ae2c7b7a55b8d299e
Substantive content preserved: YES
Prior 21 consistent with committed specification: 21/21
Contradictions found: 0
Remaining modules assessed: 79/79
Final scientific-result rows: 100/100
NOT_REACHED remaining: 0
NOT_ASSESSED remaining: 0
Voting set: 2
Expected voting set: 2
Concept-only modules activated: 0
Material Cost Variance operationally disabled: YES
Production algorithm files changed: NO
Participant-visible files changed: NO
Production Postgres accessed: NO
Full suite: 8298/8298 across 96 suites

---

## 1. Handoff audit

`T6_HANDOFF.md` was read in full and reconciled against Git history through `d0af5a3`, the
Run-17 report and the Run-18 report. The handoff's account of the starting state matched the
repository exactly and no discrepancy needed repair from committed evidence.

Confirmed starting state:

- starting commit `d0af5a3`, working tree clean;
- simulation version `sim-2026.08-v10`;
- synthetic packages present at `OG-SYNTH-0.1`, `OG-SYNTH-0.2` and `OG-SYNTH-0.3`;
- voting set exactly `{A1.7, A1.8}`, which is the to-complete cost efficiency index and the
  variance at completion;
- eight concept-only modules disabled: `A3.8`, `B2.7`, `B2.9`, `B2.20`, `B4.1`, `B4.2`, `B4.5`,
  `B4.6`;
- Material Cost Variance registered, `DISABLED_EVIDENCE_UNDER_REVIEW`, non-voting;
- baseline suite green at 7207/7207 across 88 suites.

The strict runner was re-proved able to fail. Five throwaway suites were planted in scratch
copies of the runner's own directory and the runner's verdict recorded
(`code_audit/run19_harness_integrity.csv`):

| Failure mode planted | Runner verdict |
|---|---|
| false prose, "All 12 tests passed successfully", no canonical RESULT line | rejected, exit 1 |
| a reported failed count, `RESULT: 3/5` | rejected, exit 1 |
| a green RESULT line followed by a nonzero exit | rejected, exit 1 |
| a silent crash before any RESULT line | rejected, exit 1 |
| CONTROL: a genuinely green suite | accepted, exit 0 |

The control matters: a runner that rejected everything would prove nothing.

## 2. Specification ingestion and checksum proof

The supplied attachment was 3,600 lines and 102,006 bytes with sections 0 through 37 present,
ending with the Definition of Done and the final reporting language. Its SHA-256 was recomputed
rather than taken on trust.

```
source attachment    328b50133f1d2a8d710d3cca787c24c22e2cdad0b09fe92ae2c7b7a55b8d299e
committed file       328b50133f1d2a8d710d3cca787c24c22e2cdad0b09fe92ae2c7b7a55b8d299e
```

The two are identical, so the content is preserved **byte for byte**, not merely
line-ending-transformed. The file is UTF-8 with CRLF terminators and those terminators are
preserved. Because the repository's checkout filters would otherwise normalise them, a
`.gitattributes` rule marks the file `-text`, and the round trip was verified explicitly: the
working copy was deleted, restored from the index, and rehashed to the same digest.

The metadata record is `research/methodology/PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION
_v1.metadata.json`, carrying the document title, version, source attachment name, both
checksums, line and byte counts, the sections present, the date committed, the regulatory
snapshot date, the controlling status and the supersession rule. The controlling status is
stated there in terms: the repository code is the object under test and never a source of
theory, and the document may be superseded only by a later numbered supervisory specification
committed under the same convention with its own checksum.

## 3. Module-identity reconciliation

The population was derived mechanically, not asserted:

```
registry live rows                101
project level                      96
portfolio level                     5
excluded (3.4 Material Cost Variance)  1
project targets                    95
portfolio targets                   5
TOTAL TARGETS                     100
unique module ids                 100
mapping problems                   []
```

Identity is taken from the current registry with the group letter mapped to the specification's
category number, asserted **by module name against the specification's own list** rather than
assumed. The `old_id` column of `p0-baseline/module_renumbering_map.csv` was not used: two
retired alias rows displace every later identifier by one, so `old_id` 3.4 is Labor Productivity
Index while the v0.5 key 3.4 is Material Cost Variance, and an exclusion driven off `old_id`
would have excluded the wrong module and executed the one the owner disabled.

Identifiers are text throughout. The pairs that would collide under float coercion were recorded
and each was proved distinct in the final table: 1.1 against 1.10, 2.1 against 2.10, 4.1 against
4.10, 7.1 against 7.10, and 7.2 against 7.20.

All eight concept-only modules are inside the hundred targets, as the specification requires,
and all eight remain disabled and non-voting.

## 4. Prior-21 consistency review

`code_audit/run19_prior_21_spec_consistency.csv`. Each of the twenty-one previously assessed
modules was located in the committed specification by its own section heading, and six things
were checked: the section exists; the method definition the prior result recorded appears in it;
the numeric oracle figures the prior run used appear in it; the disposition is in the allowed
vocabulary; the prior suite's block for that module calls the independent oracle rather than
production; and the prior suite is present and re-executed green.

**Result: 21 CONSISTENT, 0 CONTRADICTION_FOUND, 0 INCOMPLETE_EVIDENCE.**

One correction to record. The first version of this check inferred oracle independence from the
prose of each result row and reported 1.7, 1.8 and PH.1 as unproven, because those three cite
their primary literature source rather than the specification. That was a defect in the check,
not in the prior work: all three do call the independent oracle, and the check was rewritten to
verify that mechanically against the suite's source. The earlier reading is recorded here rather
than quietly corrected.

## 5. Remaining-79 methodology

**Parallelism.** The owner's Gate 5 authorises parallel category workers. No subagent-spawning
tool was available in this session, so the categories were executed serially by the integrating
agent. The rules Gate 5 sets for workers were nevertheless followed in full: each category has
its own oracle module, its own suite, its own result file and its own fault-injection file; the
consolidation validated every category file before merging it; and no production file was
touched. The only consequence of serial execution is elapsed time.

**Method.** For each category:

1. the specification's sections were read in full before any production file was opened;
2. an independent oracle was written **from the specification's equations**, which asserts the
   specification's own worked answers at import and refuses to load if it cannot reproduce them;
3. a suite was written testing each module for a positive known-answer or structural case, a
   negative, boundary, invalid-input or missingness case, and an invariant, property or
   metamorphic case where one is mathematically applicable;
4. the real implementation path was read;
5. method fidelity, structural eligibility, parameter provenance, threshold provenance,
   calibration status and empirical-validation status were classified separately;
6. faults were injected in scratch copies and required to turn a **named** check red.

**The anti-fossilisation rule.** Run 19 is forbidden from remediating production, so a canonical
proposition that production fails cannot be turned green by fixing code, and may not be asserted
as though the defective behaviour were correct. Every suite uses a two-directional
`proposition()`: a canonical proposition that fails and is not in the register turns the suite
red for an unrecorded defect, and a proposition in the register that starts holding **also**
turns the suite red, because a later run has repaired it and the recorded disposition has gone
stale. Neither a new defect nor a repaired one can pass silently. The shared implementation is
`server/tools/run17/audit_harness.py`.

**Oracle independence.** No oracle was written with a production module open. Where the
specification names the preferred oracle it was used: vertex enumeration for the linear
programme rather than a solver, exhaustive pairwise comparison for Pareto, a hand regret matrix,
closed-form M/M/1 with Little's Law, a hand event schedule for discrete event simulation, hand
network passes for the critical path, manual planned-value interpolation for earned schedule,
and hand-calculated focal sets for Dempster-Shafer.

## 6. Category-by-category results

| Category | Targets | Checks | Faults | Headline |
|---|---|---|---|---|
| 2 Schedule analytics | 11 | 148 | 5 | three canonical names over earned-value composites |
| 3 Cost risk | 8 | 117 | 5 | one open domain defect; two deterministic uplifts under canonical names |
| 4 Document and risk signals | 10 | 142 | 8 | exposure missing where the neighbouring module requires it |
| 5 System dynamics | 8 | 134 | 8 | one partial sensitivity; strong queueing and scenario work |
| 7 Evidence and uncertainty | 19 | 227 | 12 | algebra largely sound, provenance absent throughout |
| 8 Governance and compliance | 9 | 130 | 8 | three regulatory overclaims, one evidence defect |
| 9 Data integrity | 7 | 109 | 7 | two favourable readings from invalid or stale evidence |
| 10 Decision optimisation | 7 | 84 | 6 | no candidate actions anywhere in the category |
| **Total (this run)** | **79** | **1,091** | **59** | |

## 7. Final 100-row table

`server/tools/run17/scientific_results.csv`, rebuilt to exactly 100 rows with 100 unique
canonical identifiers, the 21 prior rows carried forward unchanged and the 79 new rows merged in.
Zero rows carry NOT_REACHED, NOT_ASSESSED or a blank disposition, and zero rows record a
production change. Material Cost Variance appears in this report as an excluded record and not
as a 101st row.

`code_audit/run19_final_100_reconciliation.csv` gives the per-module reconciliation, naming which
run assessed each. `code_audit/run19_remaining_79_results.csv` carries the 79 new rows alone.

## 8. Scientific-disposition counts

Computed from the final 100-row table.

| Disposition | Count |
|---|---|
| METHOD_LABEL_MISMATCH | 23 |
| CORRECT_PROXY_ONLY | 17 |
| PARAMETER_PROVENANCE_BLOCKED | 11 |
| IMPLEMENTATION_DEFECT | 10 |
| METHOD_PASS_CALIBRATION_PENDING | 8 |
| MISSING_CANONICAL_DATA_STRUCTURE | 7 |
| CORRECT_ABSTENTION | 6 |
| THRESHOLD_CALIBRATION_BLOCKED | 6 |
| REGULATORY_VERSION_BLOCKED | 4 |
| OWNER_DECISION_REQUIRED | 3 |
| FUTURE_RESEARCH_ONLY | 3 |
| SCIENTIFIC_PASS | 2 |
| **Total** | **100** |

Two modules reach SCIENTIFIC_PASS and they are the two that vote: the to-complete cost
efficiency index and the variance at completion. Both are standardised project-control
identities, which is why they can pass: an identity has no calibration to lack.

## 9. Method-label mismatches (23)

The implementation performs a materially different method from the registered name.

1.5 ARIMA CPI Forecast; 1.6 Earned Schedule; 1.11 ICE Ratio; 2.7 Milestone Trend Analysis;
2.10 Schedule Risk Analysis P80; 2.11 Critical Path Index; 3.6 Cost Risk Analysis P80;
3.8 Parametric Cost Index; 4.6 Change Order Frequency; 4.7 Dispute Escalation Index;
4.10 Specification Conflict Density; 5.3 Tornado Risk Ranking; 5.5 Rework Feedback Loop;
5.8 Discrete Event Simulation; 6.2 Weighted Voting; 7.2 Rough Sets; 7.14 Maximum Entropy;
8.1 ABM Governance Layer; 9.6 Cross-document Consistency Score;
10.1 Multi-Objective Optimization; 10.4 What-If Scenario Matrix; 10.5 Decision Sensitivity
Matrix; 10.6 Pareto Frontier Analysis.

The most consequential, with the specification's own words where it addresses the case directly:

- **2.11 Critical Path Index** is `(actual percent complete / planned percent complete + SPI) / 2`.
  The specification: "A weighted combination of SPI and progress is not a critical-path
  calculation." Both terms derive from one earned-value vector, so the average is one reading
  counted twice, not two independent readings.
- **2.10 and 3.6, the two P80 modules**, are deterministic z-score uplifts of a point forecast.
  Neither has a network, a distribution, an iteration count or a sample. Both use 1.28, which is
  the normal ninetieth-percentile deviate, not an eightieth.
- **9.6 Cross-document Consistency** compares figures **within one flat input**. There is no
  second source anywhere, so two documents genuinely disagreeing about the budget at completion,
  which is the case the specification is written around, cannot be detected at all.
- **7.14 Maximum Entropy** reads a hard-coded probability vector off a threshold and measures its
  entropy. Nothing is maximised and no constraint is expressed.
- **10.4 What-If Scenario Matrix** produces four future states of the cost index, not four
  actions. The consequence reaches beyond the name: the action-by-scenario matrix that 10.7
  needs for regret analysis is never produced by anything in the instrument.
- **4.10 Specification Conflict Density** is the document risk score times the square root of the
  request count. It has the wrong **direction** as well as the wrong structure: a density falls
  as exposure rises and this rises with it.

## 10. Implementation defects (10)

The required method is represented and the code implements it incorrectly.

- **3.7 Analogous Estimating Ratio.** An overrun percent of minus fifty bands **Green** with an
  exposure of minus five hundred, a negative quantity of money at risk; a budget at completion of
  minus one thousand reaches **Yellow**. Neither input is guarded at all. This is the
  out-of-domain banding pattern the programme has corrected in eleven other modules and it
  remains open here.
- **8.7 Safety Performance Index.** Two mentions of safety in meeting minutes become an incident
  rate of **20.0** through an uncited multiplication by ten, and the project bands Red. The
  specification forbids meeting minutes as an OSHA incidence-rate substitute in those terms. The
  zero case was closed by an earlier run; the non-zero case was left open.
- **9.2 Data Timeliness Score.** A document dated a year **after** the period cutoff reports an
  age of minus 365 days and bands **Green**, the freshest reading available. There is no lower
  guard on the age.
- **9.7 Reporting Frequency Index.** A project whose last upload was seventeen months before the
  cutoff reports a ten day average interval and tells the reader it has "high frequency
  reporting". The cutoff is never compared to the last event, so cessation is invisible.
- **5.2 Sensitivity Analysis.** One of three drivers is genuinely perturbed and recomputed. The
  other two are current deviations. Worse, the three are on three different scales, and an
  uncited 0.5 multiplier is the only thing setting their relative standing, so both the reported
  top driver and the band are determined by a scaling choice rather than by sensitivity.
- **7.10 Pythagorean Fuzzy Sets.** The hesitancy is computed from the pre-adjustment membership
  pair and reported beside the post-adjustment pair, so the triple a reader sees is not a
  Pythagorean triple: squared sums of 1.01, 0.91 and 0.87 rather than 1. The spherical module in
  the same file applies its renormalisation in the correct order and should be the model for the
  repair.
- **7.15 Possibility Theory.** The distribution is never normalised, so its supremum is not one,
  and the necessity is the degree less an uncited 0.3 rather than one less the possibility of the
  complement.
- **6.1 Conservative Dominance, 6.4 Worst-N-of-M, PH.5 Anomaly Score** are carried forward from
  the prior run unchanged.

## 11. Correct proxies (17)

A coherent transparent indicator published under a name implying the stronger canonical method.
1.9, 2.6, 2.9, 3.3, 3.5, 4.5, 4.9, 5.6, 5.7, 7.13, 8.5, 8.6, 9.1, 9.5, 10.3, PH.2, PH.3.

Several deserve to be named as good work rather than only as shortfalls. **5.6 Queueing Theory
Bottleneck** applies exactly one boundary, the definitional stability condition, invents no
warning level, and refuses to emit a reassuring steady-state solution at saturation, which is
the specific failure the specification warns about. **8.6 Quality Compliance Index** has the most
thorough guards in the instrument. **4.9 Procurement Lead Time Monitor** had a double count that
reported 180 per cent of a set as a proportion of it; the ratio is now bounded, proved across
every valid combination of counts rather than sampled.

## 12. Correct abstentions (6)

2.1 PERT Network Criticality; 3.1 Reference Class Forecasting; 4.4 NCR Rate; 5.1 DSM Rework
Propagation; 7.19 CRITIC-TOPSIS; 10.7 Regret Minimization Index.

Each was tested for the failure that matters here: that the abstention is genuine and not a
constant published under a method name. For 3.1, 5.1, 7.19 and 10.7 the result is
**byte-identical across every combination of inputs swept**, which proves no fixed multiplier,
score or choice is being emitted. An abstention is the scientifically correct result and these
six are not failures.

## 13. Missing canonical structures (7)

1.10 Regression to Mean CPI; 3.9 Inflation Adjustment Index; 4.1 Document Risk Score;
7.18 MARCOS Ranking; 8.9 Contractor Performance Score; 9.4 Audit Trail Completeness;
10.2 Linear Programming.

**10.2** is the clearest: the Wyndor Glass problem was solved independently by vertex enumeration
to the specification's optimum of (2, 6) with objective 36 and the correct binding constraints,
and production has no input through which two variables and three constraints could be supplied
at all. **4.1** has consequences beyond its own row: no labelled corpus exists, so the document
risk score's extraction accuracy is unmeasured, and it is an input to modules across four
categories.

## 14. Parameter-provenance gaps (11)

4.8; 7.3, 7.4, 7.5, 7.6, 7.8, 7.11, 7.12, 7.16, 7.17; 9.3.

Ten of the eleven are Category 7, and this is the general position of that category. Nearly every
formalism there derives its memberships, masses, linguistic probabilities or reliability values
from the same cost index, schedule index and document risk score by a piecewise map of literals.
Passing the algebra does not establish that the inputs to the algebra are calibrated, and the
specification says so directly. Specific cases: the Z-number reliabilities (0.85, 0.90, 0.65,
0.88) are the component that distinguishes a Z-number from an ordinary value; the interval fuzzy
half-widths (0.02, 0.01) are the entire content of the interval; the twelve source-reliability
weights in 9.3 are the entire content of that measure, since its output is their mean.

A fault-campaign finding belongs here. Removing the Pythagorean, spherical and Fermatean
admissibility guards **changed nothing at all**. Sweeping each module's own input map shows the
constraints can never be violated, so all three guards are unreachable and admissibility holds by
construction of the map rather than by the guard. Three checks were added to record this, because
a reader of the guard would conclude the opposite.

## 15. Calibration gaps

`calibration_status` is NOT_CALIBRATED on 92 of 100 rows. The eight exceptions are the modules
whose calibration is either not applicable, because they are identities or abstentions, or
frozen on synthetic data. 1.2 CUSUM carries a Run-15 frozen calibration record which this run
verified is present and **did not retune**; that calibration is synthetic, so the operating point
is method-verified and not empirically established.

## 16. Threshold gaps

Classified per the specification's provenance vocabulary. The distribution is dominated by
HEURISTIC_UNCALIBRATED. Two rows reach LITERATURE_EXACT or REGULATORY_EXACT, and both are cases
where the boundary is definitional rather than empirical: the queueing stability condition at a
utilisation of one, and the to-complete index boundary at one.

Several modules carry their own source comments recording that a search for a source was made
and failed, which is exactly the right disclosure: the look-ahead constraint rate, the
contingency burn ladder, the request velocity ladder and the submittal rejection ladder each say
so in the code.

## 17. Regulatory findings (Category 8, previously unassessed)

All nine were assessed for the first time. The specification warns that Category 8 must not be
cleared merely because the code returns a result; every module here returns a result.

**Three regulatory overclaims, all P0C.**

- **8.2 FAR Threshold Monitor.** The module does not determine whether earned value management
  applies; it assumes it, on every project. None of the deciding evidence, the acquisition
  designation, agency, agency procedure, contract clauses, award date or rule version, is an
  input, and none of the four applicability states the specification requires is reported. The
  twenty-five per cent figure is presented to the reader as a **FAR Part 34** threshold. FAR
  34.201 states no numeric overrun threshold of any kind and none is cited. A boolean field
  asserts that reporting is required, resting on no applicability determination.
- **8.3 OMB A-11 Check.** The entire check is whether the cost index is below 0.90 and the budget
  is at least ten million dollars. The specification states in terms that the circular must not
  be reduced to budget, cost-index and progress thresholds. No requirement, section,
  applicability, required evidence or reviewer is represented, and **no edition is recorded**, so
  the reading cannot be tied to a version. The reader is told MANDATORY REPORTING TRIGGERED.
- **8.4 EVM Reporting Threshold.** Not one element of reporting compliance is represented: no
  applicability, clause, cadence, due date or received date. A contractor filing every required
  monthly report on time on a struggling project is reported as having breached a reporting
  threshold; one filing nothing on a healthy project is reported as within it.

**One evidence defect, P0B:** 8.7 Safety Performance Index, described in section 10.

**Two blocked on permit and record identity, P2:** 8.8 Environmental Compliance Rate has no permit
authority, jurisdiction or version, so it cannot say which permit its rate is against; 8.9
Contractor Performance Score has no official source identifier, assessment period, status or
review state, and CPARS is the official source under FAR Subpart 42.15.

**Better than expected.** 8.1 governance never lets a high-impact action carry the routine
project-level authority, and its fairness gate is honestly reported as always false with the
reason recorded rather than implying two escalation paths exist. 8.9 preserves the **worst**
contractor dimension noncompensatorily rather than averaging it away, which is stronger than the
specification's minimum. 8.8 no longer converts meeting mentions into a compliance percentage.

**Regulatory basis and access limitation.** Everything above is evaluated against the dated
snapshot the committed specification carries, `REGULATORY_SNAPSHOT_2026-08-12`. No web retrieval
was performed for this run, so nothing here is described as current law and no superseding source
is asserted. Where a module would need an authority the snapshot does not supply, that is
recorded as a gap rather than filled. No module claims FAR, OMB, OSHA or EPA compliance: that was
checked explicitly on every Category 8 module's reader-facing sentence and none does.

## 18. Category-9 boundary findings

The target architecture is project evidence, then Category 9 assessment, then qualified evidence,
then analytical and governance use, with Category 9 output being metadata rather than another
risk vote.

**The metadata half holds.** No Category 9 module votes; the voting set is exactly the two cost
identities. The qualification layer carries separate named dimensions with controlled states and
no composite score, so a known gap and a measured strength cannot cancel, and its own source
states that its dimensions never gate, never subtract and never become a number. The two
dimensions this repository cannot answer are named honestly as partial and not estimable rather
than converted into a penalty or a pass.

**The gate half does not exist.** The signal package is marked `unqualified` in production and
carries the recorded deviation: the Category 9 eligibility gate that would qualify a versioned
signal package before evidence combination and governance read it is not implemented, and nothing
gates those inputs on evidence quality. Categories 6, 7, 8 and 10 read raw cost, schedule and
document-risk values. The bypass is **disclosed on the data** rather than hidden, which is
materially better than an undisclosed one, but the gate is absent. Run 19 is an audit and does
not repair it. P0D.

## 19. Lineage and double-count findings

**Combining one body of evidence twice sharpens belief.** One Amber source gives mass 0.7000 on
Amber; the same source presented twice gives 0.9273. The combination rule has no lineage
argument, so nothing prevents two correlated transforms of one cost index being combined as
independent evidence. In the **current** deployment this is latent rather than active: only two
modules vote and both are the same lineage, and the semantics layer withholds the conflict
coefficient precisely because of that, naming the state rather than publishing a zero a reader
could not distinguish from perfect agreement. It becomes live the moment a second lineage is
admitted. P0D.

**Three module-level duplications**, each of which would let a reader see one reading twice and
mistake it for agreement:

- **5.3 Tornado Risk Ranking** recomputes its own impacts from the same evidence 5.2 reads, by an
  incompatible definition. The specification asks specifically that this be flagged.
- **4.6 Change Order Frequency and 8.5 Contract Modification Frequency** read the same change
  order count and the same two contract sums by almost identical ladders.
- **2.4 Schedule Compression Index** reduces exactly to one over the schedule performance index
  at every value tested, so it carries no information that signal does not already carry.

## 20. Empirical-validation gaps

`empirical_validation_status` is NOT_DONE on all 100 rows. This is the honest answer for an
instrument with no labelled outcome corpus, and it is reported as a separate column precisely so
it cannot be confused with implementation verification. Nothing in this report describes any
module as validated.

The specification's distinction is preserved throughout: implementation verification, structural
eligibility, parameter provenance, calibration, empirical validation and operational activation
are six separate questions and were classified separately for every module.

## 21. Concept-only results

All eight remain disabled and non-voting, and each was proved short-circuited **before its
formula function is reached** on a complete input, so none is merely non-voting.

| Module | Laboratory finding | Disposition |
|---|---|---|
| 3.8 Parametric Cost Index | the ratio of two earned-value forecasts of the same project; no driver, coefficient or design matrix | METHOD_LABEL_MISMATCH |
| 7.7 Plithogenic Sets | no published operator named, so no limiting case to check | FUTURE_RESEARCH_ONLY |
| 7.9 Quantum Probability | a cosine interference heuristic; no state, projector or measurement | FUTURE_RESEARCH_ONLY |
| 7.20 Hypersoft Sets | any undefined attribute tuple silently receives 0.35 | FUTURE_RESEARCH_ONLY |
| 10.1 Multi-Objective Optimization | the mean of three descriptive scores, named a pareto score | METHOD_LABEL_MISMATCH |
| 10.2 Linear Programming | cannot represent the Wyndor problem at all | MISSING_CANONICAL_DATA_STRUCTURE |
| 10.5 Decision Sensitivity Matrix | ranks current deviations; nothing perturbed | METHOD_LABEL_MISMATCH |
| 10.6 Pareto Frontier Analysis | three booleans on one project; dominance is a relation between alternatives | METHOD_LABEL_MISMATCH |

7.20 deserves emphasis because it fails the specification's own critical test for it directly: a
missing Cartesian-product tuple may not silently receive a default, and here it receives 0.35,
which bands Amber, so a combination the table never defined is indistinguishable from one
deliberately scored at 0.35.

**A laboratory result is not permission to activate, and none of these was activated.**

One correction to record. An earlier version of this run's category files typed the activation
column by hand and recorded four of these eight, 3.8, 7.7, 7.9 and 7.20, as advisory when the
registry has them disabled. That was a factual misstatement in the very table whose purpose
includes proving concept-only activation is zero. The activation column is a fact about the
registry, so the consolidation step now reads `registry.activation_state` for every module and
**refuses to consolidate** on any disagreement. All eight rows now read DISABLED_UNSAFE and agree
with the code. The error is recorded here rather than quietly corrected, and the guard means this
class of error cannot recur.

## 22. Fault-injection proof

59 injections, recorded in `code_audit/run19_fault_injection_results.csv`. Every one changed
bytes in a scratch copy, was reached, left the suite running so it printed its canonical RESULT
line, and turned a **named** check red. The real tree was never written to, which is proved by
hashing it before and after each campaign.

The specification's required minimum list is covered:

| Required fault | Where | Named red |
|---|---|---|
| wrong Earned Schedule interpolation | prior run, re-executed green | yes |
| wrong LP optimum | 10.2, feasibility tolerance widened | yes |
| Dempster ignorance treated as conflict | 7.1, discount stops returning freed mass to the frame | yes |
| queueing denominator or operator defect | 5.6, both the denominator and the queue-length operator | yes |
| dominated Pareto point admitted | 10.6, strictness dropped from the dominance relation | yes |
| Isolation Forest path or score mutation | prior run, re-executed green | yes |
| fuzzy admissibility violation | 7.16 and 7.13 | yes |
| regulatory rule-version mismatch | 8.3, committed A-11 edition replaced by a superseded one | yes |
| Category-9 raw-input bypass | signal package qualification marker flipped | yes |
| duplicated lineage accepted as independent | 5.3 and the combination rule | yes |

**Seven injections were attempted, failed to qualify, and were replaced. All seven are recorded
rather than hidden**, because a fault that does not qualify is itself evidence:

- **Five crashed instead of failing.** Removing a zero-denominator guard, or a minimum-count
  guard, restores a division by zero, so the suite dies before printing a RESULT line. A crash is
  not a red: the runner rejects it for the wrong reason and the campaign cannot tell a reached
  mutation from an unreached one. The harness detects this explicitly and scores it
  `NO_CRASHED_INSTEAD`.
- **One was absorbed by defence in depth.** Removing the locked-holdout refusal changed nothing,
  because a locked split is caught one branch later by the rule that an unrecognised split is
  refused. That is the guard working as intended.
- **Three changed nothing at all**, which produced the unreachable-guard finding in section 14.

One injection exposed a **genuine coverage gap in this run's own work**: reversing the direction
of the 3.6 P80 uplift went undetected, because the suite never checked the P80 against the point
forecast it uplifts. That invariant was added, and the fault then turned it red. This is what the
campaign is for.

An earlier version of the fault harness copied only `server/` into the scratch directory, so
every suite died on a missing registry file before reaching the mutation, and every fault scored
a false red. That was caught, the harness was corrected to copy the repository root, and every
result in this report comes from the corrected harness.

## 23. Production-hash proof

```
server/app tree digest   f70787ee33d1d0b146adec920a937b2edfd7c1cfbaf97c9e6ff10d77375f7fe4
assets tree digest       333a7ef1d060fc63b1fa187d840eb8484dba5e8a5be596ac937067c9bb42440e
```

`git diff d0af5a3 -- server/app assets index.html tests.html` is **empty**. Not one production
analytical file, participant-facing asset, registry activation rule or voting rule differs from
the Run-18 merge commit. A separate file-by-file digest of every `.py`, `.js`, `.html` and `.css`
under `server/app` and `assets` was taken at the start and end of this run and is byte-identical:
`92c1d81215258b4044a9645898a5df23640d9100c981063e4d6147fad0c0c75d`.

Permitted repository changes only: the committed specification and its metadata, the shared audit
and fault harnesses, eight independent oracle modules, eight category suites, eight category
result files, eight fault-injection files, the consolidated results table, the audit CSVs, three
audit scripts, this report and the handoff.

**One observation to record.** Two historical audit files, `code_audit/run9_no_operational_effect
.csv` and `code_audit/run10_no_operational_effect.csv`, are **rewritten by pre-existing suites on
every run**, because those suites recompute an assets tree digest and store the current value.
Running the baseline suite therefore modified them. They were restored to their committed state
and this is recorded as a pre-existing side effect Run 19 did not create and did not repair.

## 24. Voting and activation proof

- Voting set: exactly `{A1.7, A1.8}`, unchanged. Asserted in every one of the eight new suites.
- Concept-only activations: **0**. All eight remain `DISABLED_UNSAFE` and each was proved
  short-circuited before its formula function on a complete input.
- Material Cost Variance: registered, named, `DISABLED_EVIDENCE_UNDER_REVIEW`, non-voting,
  refused before its arithmetic on every input shape tested, and excluded from the hundred rows.
  Its state is distinct from the concept-only state and was checked as distinct.
- No participant-visible file changed and no research treatment assignment was touched.
- Production Postgres was not accessed. Every suite runs against a throwaway SQLite database
  migrated from scratch.

## 25. Complete suite

8298 of 8298 checks across 96 suites, all green, on the branch before merge. The prior baseline
was 7207 of 7207 across 88 suites, so this run adds 8 suites and 1,091 checks and changes no
prior count. The eight new category suites are picked up automatically by the
strict runner and each prints one anchored canonical RESULT line.

## 26. Owner decisions

1. **2.4 Schedule Compression Index.** Define the metric against a governed required completion
   date, or retire it as a restatement of the schedule performance index. It reduces exactly to
   one over that index today.
2. **5.4 Scenario Modeling and its category.** The method is correct and its guards are the
   strongest in the instrument, but it answers the action-selection question the specification
   assigns to Category 10. Note the connection: 10.4 does not produce the action-by-scenario
   matrix, and this module consumes exactly one. Consider whether 5.4, 10.4 and 10.7 should share
   one governed decision object.
3. **7.18 MARCOS and 7.19 CRITIC-TOPSIS placement.** Both belong with decision alternatives.
   Identifiers should stay stable.
4. **9.5 Information Completeness Ratio.** Should package coverage be measured over evidence
   components rather than fields? Its nineteen-field list contains 9.1's eleven as a subset, so
   the two scores move together by construction.
5. **PH.4 Cross-project Pattern Detector** pattern definition, carried forward.
6. **PH.5 Anomaly Score** composite weights, carried forward.
7. **6.4 Worst-N-of-M** aggregation, carried forward.
8. **Thresholds as owner policy.** A large number of bands are HEURISTIC_UNCALIBRATED with no
   prospect of literature calibration. A decision is needed on which become declared, versioned
   owner policy rather than remaining presented as though empirical.
9. **Proxy naming.** Seventeen modules are honest proxies under names implying stronger methods.
   Rename, rebuild, or disclose in the participant-facing text?

## 27. Prioritised next remediation queue

`code_audit/run19_next_remediation_queue.csv`, 94 items. **Not executed in this run.**

| Priority | Count |
|---|---|
| P0A voting or project-status defects | 0 |
| P0B invalid or missing evidence producing a favourable or adverse result | 4 |
| P0C regulatory or governance overclaim | 4 |
| P0D Category-9 bypass or lineage double counting | 4 |
| P1 canonical implementation defects | 27 |
| P2 missing canonical structures | 8 |
| P3 calibration, thresholds, provenance, naming, placement | 44 |
| FUTURE experimental methods | 3 |

**P0A is empty and that is a real result, not an omission.** The rule was applied rather than
assumed: both voting modules were checked and both reach SCIENTIFIC_PASS.

**The twelve P0 items:**

- P0B: 3.7 Analogous Estimating Ratio; 8.7 Safety Performance Index; 9.2 Data Timeliness Score;
  9.7 Reporting Frequency Index.
- P0C: 8.2 FAR Threshold Monitor; 8.3 OMB A-11 Check; 8.4 EVM Reporting Threshold;
  10.3 Constraint Satisfaction Analysis.
- P0D: ARCH.1 the Category 9 qualification gate; ARCH.2 evidence lineage in the combination rule;
  5.3 Tornado Risk Ranking; 4.6 Change Order Frequency.

## 28. What this audit establishes, and what it does not

**Establishes.** Run 19 independently evaluated the implementation fidelity, mathematical and
structural correctness, reproducibility, parameter provenance, calibration status, threshold
basis, regulatory basis and empirical-validation status of 100 analytical and portfolio modules
against a literature-grounded supervisory specification that is now committed to the repository
with its checksum. Each module is classified separately. Every expected value came from an
independent oracle written from the specification's equations, which self-proves against the
specification's own worked answers before it is allowed to judge anything, and no production
output was used as its own oracle. Every important check was proved capable of failing.

**Does not establish.** Implementation verification is not empirical validation, and no module
in this instrument has empirical validation: that column reads NOT_DONE on all 100 rows. A
synthetic known-answer test is not field validation. A rule check is not a legal determination,
and no regulatory conclusion in this report is one. The regulatory findings are evaluated against
`REGULATORY_SNAPSHOT_2026-08-12` and not against current law; no web retrieval was performed, so
where a primary source could not be consulted that is recorded as an access limitation rather
than implied to have been read. Nothing here establishes real-world predictive accuracy, effect
size on actual construction projects, external validity, practitioner utility or production
readiness.

**Nothing in this report should be read as "all 100 algorithms are validated."** Two modules
reach SCIENTIFIC_PASS, both are standardised identities, and even for those the claim is that no
material scientific deficiency was found, not that they predict anything.

See `T6_HANDOFF.md` for the chronological record.
