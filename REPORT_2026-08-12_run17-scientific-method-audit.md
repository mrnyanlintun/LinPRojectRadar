# Run 17 — Literature-grounded scientific method audit

## Test and audit only. No production algorithm was changed, and none was permitted to be.

Branch `claude/run17-scientific-method-audit`, taken from `origin/main` at `71150dd`.

---

## 1. Executive scientific verdict

Run 17 independently evaluated the implementation fidelity, mathematical and structural
correctness, reproducibility, parameter provenance, calibration status, threshold basis and
empirical-validation status of the analytical and portfolio modules of this platform against a
literature-grounded supervisory specification. Individual modules are classified separately.
Implementation verification does not imply empirical validation or production suitability.

**This run is a truthful partial audit and says so in the artifacts as well as in this
sentence.** Of the 100 mechanically reconciled scientific targets, **21 carry a full method card,
a positive known-answer or structural test, a negative or boundary or missingness test, and an
invariant or metamorphic test where one is mathematically applicable.** The remaining **79 are
recorded as `NOT_REACHED_IN_THIS_RUN`** in every artifact, with every assurance column set to
`NOT_ASSESSED`. No prior run's determination has been carried into a Run-17 row as though Run 17
had confirmed it, and no uncertainty has been rounded into `SCIENTIFIC_PASS` to reach a hundred.

Of the 21 reached: **2 SCIENTIFIC_PASS, 7 METHOD_PASS_CALIBRATION_PENDING, 4
METHOD_LABEL_MISMATCH, 3 CORRECT_PROXY_ONLY, 3 IMPLEMENTATION_DEFECT, 1
MISSING_CANONICAL_DATA_STRUCTURE, 1 OWNER_DECISION_REQUIRED.** Empirical validation is
`NOT_DONE` for all 21, which is the honest answer for a controlled research instrument with no
labelled outcome corpus and no expert reference standard.

**The largest finding is architectural rather than arithmetic.** The Category-9 qualification
boundary the target architecture requires is not enforced anywhere in code: the Category-6
ensembles accept raw assembled signal statuses and return a project status from evidence that
has passed through no qualification step. No module carries a lineage identifier, so an ensemble
cannot distinguish one piece of evidence seen twice from two independent pieces, and correlated
transforms of the same cost index each cast their own vote. Both deviations are honestly
declared in `signal_package.py`; neither is prevented.

**Three implementation defects were confirmed against canonical propositions.** Conservative
Dominance absorbs a single Red signal into Amber. Worst-N-of-M dilutes an unchanged adverse
finding when unrelated benign evidence arrives. The portfolio Anomaly Score re-weights its own
constituents according to which data happen to be available. None of the three is in the voting
set, and no participant-visible behaviour was altered by this run.

---

## 2. Exact Git baseline

| Item | Value |
|---|---|
| Branch point | `71150dd`, `Merge branch 'claude/run16-instrument-cleanup'` |
| Branch | `claude/run17-scientific-method-audit` |
| Merge commit | `4bc29fc` |
| Registry live modules | 101 |
| Simulation version at baseline | `sim-2026.08-v10`, unchanged by this run |
| Voting set at baseline and at end | exactly `A1.7` TCPI and `A1.8` Variance at Completion |

---

## 3. Run-16 prerequisite proof

Run 17 was permitted to begin only on proof from merged main. Every required statement was
checked mechanically, not read from prose, and the Run-16 commit was derived from Git rather than
taken from any prompt.

| Required Run-16 state | Evidence | Result |
|---|---|---|
| Material Cost Variance temporarily disabled operationally | `activation_state('A3.4')` is `DISABLED_EVIDENCE_UNDER_REVIEW` | PROVED |
| Its own state, not the concept-only one | distinct from the eight modules' `DISABLED_UNSAFE` | PROVED |
| Retained in registry and history, not deleted | registry row present, name intact | PROVED |
| Non-voting | absent from `CORE_VOTING_MODULES` | PROVED |
| Refused before its formula function is reached | four input shapes, each refused with no status colour | PROVED |
| No unintended voting expansion | voting set is exactly `{A1.7, A1.8}` | PROVED |
| Stale FINAL FLOW and reset-state truthfulness resolved | `test_run16_clear_all_invalidation.py` and `test_run16_final_flow_and_rail.py` green on merged main | PROVED |
| Merged-main suite green | 87 suites, 6957 of 6957, exit zero | PROVED |
| T6_HANDOFF records the Run-16 result | entry present | PROVED, WITH ONE REPAIR |

**The one repair.** The Run-16 handoff entry carried the literal placeholder `RUN16_MERGE_COMMIT`
where the merge hash belongs. Run 17 derived the actual hash from Git, `71150dd`, and repaired the
entry from committed evidence only. No date, test count, version or finding was invented.

No stop condition was hit at this gate.

---

## 4. Mechanical 100-module population proof

**A defect in the identifier source was found here, before any testing, and it would have
excluded the wrong module.**

`p0-baseline/module_renumbering_map.csv` carries an `old_id` column that superficially looks like
the v0.5 registry `Module_ID_Text_Key`. It is not. It is a legacy pre-renumbering identifier
whose sequence contains two retired alias rows, old `1.3` consolidated into `4.1` and old `3.2`
consolidated into `5.1`, so every row after each gap is displaced by one. Under `old_id`, key
`3.4` is **Labor Productivity Index**, while the v0.5 key `3.4` is **Material Cost Variance**. A
Run-17 exclusion driven off that column would have excluded Labor Productivity Index and then
executed the module the owner disabled.

The v0.5 key is instead the `new_id` column with its group letter replaced by the specification's
category number. That mapping is **proved by module name against the supervisory specification's
own list of all 101 names**, not assumed, in `server/tools/run17/population.py`. Categories 8 and
10 make the proof necessary: registry group `B3` supplies `8.1` to `8.5` while group `A6` supplies
`8.6` to `8.9`, and group `B4` supplies category `10`, none of which is recoverable from the group
letter alone.

| Step | Count |
|---|---|
| Registry live rows | 101 |
| Project-level rows, groups A, B and C | 96 |
| Portfolio-level rows, group D | 5 |
| Less Material Cost Variance, v0.5 key `3.4` | −1 |
| Project-level Run-17 targets | 95 |
| Plus portfolio targets PH.1 to PH.5 | +5 |
| **Total Run-17 scientific targets** | **100** |
| Unique module identifiers | 100 |
| Name disagreements against the specification | **0** |
| Eight concept-only modules present inside the 100 | 8 of 8 |

**Identifiers are never coerced to floating point.** The reconciliation records which pairs would
have merged if they had been: `1.1` with `1.10`, `2.1` with `2.10`, `4.1` with `4.10`, `7.1` with
`7.10` and `7.2` with `7.20`. Five real collisions, avoided by keeping every key as text.

---

## 5. Research and theory source hierarchy

The Run-17 supervisory method specification is tier 1 and is the controlling authority for
theory. Every oracle equation in `server/tools/run17/oracle/canonical_oracles.py` is transcribed
from it and **self-proves against that specification's own worked numeric answers before it is
allowed to judge anything**: 22 self-tests, zero failures.

**Provenance is labelled honestly, and no primary source is implied to have been read when it was
not.** Run 15 established that several publisher PDFs are refused by this container's egress
proxy. `server/tools/run17/source_ledger.csv` therefore carries a `retrieved` column, and the
nine entries in it are marked `NOT_RETRIEVED_IN_CONTAINER` where the identifier is carried from
the supervisory specification rather than read here. The theory applied in those cases is the
specification's own statement of the method, which section 7 of the owner prompt makes
controlling. Nothing in this report claims a primary text was consulted.

The current merged repository source is the only authority for what the software does. No older
design document was used to override code, and no code was used to override theory.

---

## 6. Verification, calibration and empirical validation distinguished

The word "validated" appears as a verdict nowhere in this run's artifacts. Seven assurance
concepts are recorded separately for every reached module, and they are not interchangeable:

- **Implementation verification**, does the code reproduce the stated specification? For 20 of
  21 reached modules, yes; the one exception is Conservative Dominance.
- **Structural eligibility**, does the required data structure exist? Absent for Earned
  Schedule, ARIMA, Regression to Mean CPI, ICE Ratio, Weighted Voting and Worst-N-of-M.
- **Parameter provenance**, sourced and versioned? Definitional for the two identities;
  unsourced literals almost everywhere else.
- **Calibration**, a declared procedure on a separate fixture set? Only CUSUM and Isolation
  Forest, both on synthetic data, both frozen at Run 15 and **not retuned by this run**.
- **Empirical validation**, intended-use performance against independent reference outcomes?
  **NOT_DONE for all 21.** No labelled corpus and no expert reference standard exist.
- **Regulatory currency**, not applicable to any module reached; Category 8 was not reached.
- **Reproducibility**, regeneration from frozen inputs and seed? Verified for every reached
  module that has a stochastic element.

A module may be implementation-verified and empirically unvalidated. That is the normal state
here and it is not a failure.

---

## 7. The 100-module results table

The authoritative matrix is `server/tools/run17/scientific_results.csv`: exactly 100 rows, 100
unique identifiers, 29 columns. Material Cost Variance is recorded as an excluded record in
section 30 of this report and is **not** a 101st row.

| Id | Module | Basis class | Disposition | Empirical validation |
|---|---|---|---|---|
| 1.1 | Monte Carlo EAC | C. LITERATURE_SUPPORTED_ADAPTATION | METHOD_PASS_CALIBRATION_PENDING | NOT_DONE |
| 1.2 | CUSUM Anomaly Monitor | B. ESTABLISHED_CANONICAL_METHOD | METHOD_PASS_CALIBRATION_PENDING | NOT_DONE |
| 1.3 | Bayesian EAC | B. ESTABLISHED_CANONICAL_METHOD | METHOD_PASS_CALIBRATION_PENDING | NOT_DONE |
| 1.4 | Kalman Filter SPI Smoother | B. ESTABLISHED_CANONICAL_METHOD | METHOD_PASS_CALIBRATION_PENDING | NOT_DONE |
| 1.5 | ARIMA CPI Forecast | D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR | METHOD_LABEL_MISMATCH | NOT_DONE |
| 1.6 | Earned Schedule | D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR | METHOD_LABEL_MISMATCH | NOT_DONE |
| 1.7 | TCPI | A. STANDARDIZED_PROJECT_CONTROL_IDENTITY | SCIENTIFIC_PASS | NOT_DONE |
| 1.8 | Variance at Completion | A. STANDARDIZED_PROJECT_CONTROL_IDENTITY | SCIENTIFIC_PASS | NOT_DONE |
| 1.9 | Budget Execution Rate | D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR | CORRECT_PROXY_ONLY | NOT_DONE |
| 1.10 | Regression to Mean CPI | C. LITERATURE_SUPPORTED_ADAPTATION | MISSING_CANONICAL_DATA_STRUCTURE | NOT_DONE |
| 1.11 | ICE Ratio | D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR | METHOD_LABEL_MISMATCH | NOT_DONE |
| 2.1 | PERT Network Criticality | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 2.2 | Line of Balance | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 2.3 | CCPM Buffer Health | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 2.4 | Schedule Compression Index | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 2.5 | Float Consumption Rate | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 2.6 | S-Curve Deviation | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 2.7 | Milestone Trend Analysis | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 2.8 | Look-Ahead Schedule Health | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 2.9 | Resource Loading Index | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 2.10 | Schedule Risk Analysis P80 | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 2.11 | Critical Path Index | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 3.1 | Reference Class Forecasting | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 3.2 | Contingency Burn Rate | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 3.3 | Labor Productivity Index | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 3.5 | Overhead Absorption Rate | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 3.6 | Cost Risk Analysis P80 | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 3.7 | Analogous Estimating Ratio | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 3.8 | Parametric Cost Index | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 3.9 | Inflation Adjustment Index | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 4.1 | Document Risk Score | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 4.2 | RFI Velocity | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 4.3 | Submittal Rejection Rate | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 4.4 | NCR Rate | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 4.5 | Weather Day Impact | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 4.6 | Change Order Frequency | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 4.7 | Dispute Escalation Index | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 4.8 | Subcontractor Performance | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 4.9 | Procurement Lead Time Monitor | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 4.10 | Specification Conflict Density | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 5.1 | DSM Rework Propagation | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 5.2 | Sensitivity Analysis | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 5.3 | Tornado Risk Ranking | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 5.4 | Scenario Modeling | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 5.5 | Rework Feedback Loop | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 5.6 | Queueing Theory Bottleneck | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 5.7 | Agent-Based Supply Chain | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 5.8 | Discrete Event Simulation | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 8.6 | Quality Compliance Index | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 8.7 | Safety Performance Index | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 8.8 | Environmental Compliance Rate | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 8.9 | Contractor Performance Score | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 6.1 | Conservative Dominance | E. PCEIF_GOVERNANCE_SYNTHESIS_RULE | IMPLEMENTATION_DEFECT | NOT_DONE |
| 6.2 | Weighted Voting | E. PCEIF_GOVERNANCE_SYNTHESIS_RULE | METHOD_LABEL_MISMATCH | NOT_DONE |
| 6.3 | Majority Rules | E. PCEIF_GOVERNANCE_SYNTHESIS_RULE | METHOD_PASS_CALIBRATION_PENDING | NOT_DONE |
| 6.4 | Worst-N-of-M | E. PCEIF_GOVERNANCE_SYNTHESIS_RULE | IMPLEMENTATION_DEFECT | NOT_DONE |
| 7.1 | Dempster-Shafer | B. ESTABLISHED_CANONICAL_METHOD | METHOD_PASS_CALIBRATION_PENDING | NOT_DONE |
| 7.2 | Rough Sets | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 7.3 | Neutrosophic Logic | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 7.4 | Interval Fuzzy Sets | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 7.5 | Z-numbers | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 7.6 | PLTS | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 7.7 | Plithogenic Sets | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 7.8 | Belief Rule Base | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 7.9 | Quantum Probability | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 7.10 | Pythagorean Fuzzy Sets | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 7.11 | Picture Fuzzy Sets | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 7.12 | Hesitant Fuzzy Sets | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 7.13 | Type-2 Fuzzy Sets | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 7.14 | Maximum Entropy | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 7.15 | Possibility Theory | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 7.16 | Spherical Fuzzy Sets | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 7.17 | Fermatean Fuzzy Sets | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 7.18 | MARCOS Ranking | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 7.19 | CRITIC-TOPSIS | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 7.20 | Hypersoft Sets | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 8.1 | ABM Governance Layer | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 8.2 | FAR Threshold Monitor | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 8.3 | OMB A-11 Check | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 8.4 | EVM Reporting Threshold | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 8.5 | Contract Modification Frequency | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 10.1 | Multi-Objective Optimization | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 10.2 | Linear Programming | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 10.3 | Constraint Satisfaction Analysis | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 10.4 | What-If Scenario Matrix | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 10.5 | Decision Sensitivity Matrix | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 10.6 | Pareto Frontier Analysis | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 10.7 | Regret Minimization Index | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 9.1 | Missing Data Index | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 9.2 | Data Timeliness Score | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 9.3 | Source Reliability Weighting | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 9.4 | Audit Trail Completeness | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 9.5 | Information Completeness Ratio | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 9.6 | Cross-document Consistency Score | not assessed | NOT REACHED IN THIS RUN | not assessed |
| 9.7 | Reporting Frequency Index | not assessed | NOT REACHED IN THIS RUN | not assessed |
| PH.1 | Isolation Forest | B. ESTABLISHED_CANONICAL_METHOD | METHOD_PASS_CALIBRATION_PENDING | NOT_DONE |
| PH.2 | Portfolio Outlier Detection | D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR | CORRECT_PROXY_ONLY | NOT_DONE |
| PH.3 | Signal Trajectory Classifier | D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR | CORRECT_PROXY_ONLY | NOT_DONE |
| PH.4 | Cross-project Pattern Detector | D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR | OWNER_DECISION_REQUIRED | NOT_DONE |
| PH.5 | Anomaly Score | D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR | IMPLEMENTATION_DEFECT | NOT_DONE |

---

## 8. Category 1 findings: quantitative EVM and forecasting, 11 of 11 reached

**Fully reached. Every one of the eleven targets carries a method card and three classes of test.**

**1.7 TCPI and 1.8 Variance at Completion are the two SCIENTIFIC_PASS results of this run, and
they are also the only two voting modules.** Both reproduce the specification's worked answers
exactly, are invariant under a change of currency scale, and refuse every out-of-domain shape
tested, including the negative actual cost that once banded Green and the zero remaining budget
that once manufactured a Red. Both record their target basis explicitly rather than leaving the
forecast convention implicit. Their band boundaries are the strongest in the platform and are
still not empirically validated: `1.00` and `0` per cent are definitional and the source states
them, while `1.10` and `−11.11` per cent apply the Christensen and Heise stability figure **by
stated inference**, which is declared in the code together with the sentence saying the measure's
false-positive and false-negative rates are unmeasured.

**Three method-label mismatches, and none of the three carries a proxy qualifier**, so each
presents to the export and the methods documentation under its full canonical name.

- **1.6 Earned Schedule** computes actual percent complete over planned percent complete. The
  specification states plainly that this is not Earned Schedule. The discriminating test was run
  rather than asserted: the canonical measure moves by more than a tenth when the planned-value
  curve is re-shaped at constant earned value and actual time, and the implemented measure cannot
  move at all, because no curve reaches it.
- **1.5 ARIMA CPI Forecast** is a fixed AR(1)-on-first-differences heuristic. Its constant-series
  behaviour and domain guards are correct, but the result carries no differencing order, no
  moving-average terms, no identification rule, no residual diagnostics and no forecast interval.
- **1.11 ICE Ratio** divides correctly but has no independent estimate. The independence test was
  explicit: both forecasts are deterministic functions of the same four inputs, and perturbing
  the shared cost index moves one while the other cannot move at all.

**1.10 Regression to Mean CPI is MISSING_CANONICAL_DATA_STRUCTURE.** The shrinkage arithmetic is
correct and the result lies between the current value and the mean, but the reference mean is the
project's own history rather than an outside reference class, and the weight is a fixed one half
rather than an estimated coefficient.

**1.1, 1.2, 1.3 and 1.4 are METHOD_PASS_CALIBRATION_PENDING**, each for a different reason worth
distinguishing. Monte Carlo samples a declared model and reports P50 and P80 from the simulated
distribution, reproducing under a fixed seed and moving under a different one, but its
distribution parameters have no provenance. CUSUM's recursion is canonical and behaves exactly as
its frozen Run-15 design requires, signalling on a persistent level shift and staying silent on
an isolated spike; its calibration is synthetic. Bayesian EAC reproduces the normal-normal
identity at a hand calculation, with a posterior variance smaller than either input variance, but
its prior and likelihood variances are designed constants. Kalman matches an independent
implementation of the canonical predict-update step and treats a constant series as a fixed
point, but Q and R are the bare literals 0.01 and 0.1.

**1.9 Budget Execution Rate is CORRECT_PROXY_ONLY**, correctly labelled as such already, because
no approved time-phased expenditure profile exists anywhere in the input contract.

---

## 9. Category 2 findings: schedule analytics

**NOT REACHED IN THIS RUN.** All 11 targets carry `NOT_REACHED_IN_THIS_RUN` and `NOT_ASSESSED` in
every assurance column. No determination of any kind is made about them here.

---

## 10. Category 3 findings: cost risk, and the Material Cost Variance exclusion

**The 8 scientific targets were NOT REACHED IN THIS RUN.** The exclusion itself was fully
executed and is proved in section 30.

---

## 11. Category 4 findings: document and risk signals

**NOT REACHED IN THIS RUN.** All 10 targets.

## 12. Category 5 findings: system dynamics and complexity

**NOT REACHED IN THIS RUN.** All 8 targets.

---

## 13. Category 6 findings: signal synthesis, 4 of 4 reached

**Fully reached, and it is the worst-performing category in the run: two implementation defects,
one label mismatch, and one calibration-pending result.**

**6.1 Conservative Dominance, IMPLEMENTATION_DEFECT.** The defining property does not hold.
Conservative dominance is the worst credible qualified signal; production escalates only at two
Reds, or at a breached control chart coinciding with a Red forecast, so **a single Red signal
among three Greens returns Amber**. The specification's own sentence is that one severe qualified
signal cannot disappear inside an average, and here it disappears into a three-arm ladder. Much
about the module is genuinely sound and was verified: the result is permutation invariant across
signal slots, monotone non-decreasing as one signal worsens, two Reds do escalate, an absent
signal does not read Green, an unknown string does not read Green, and the module refuses
entirely without a package. The module is non-voting, but it is the input to the governance
layer's authority and action selection, so a lone Red currently selects routine early warning
rather than management escalation.

**6.4 Worst-N-of-M, IMPLEMENTATION_DEFECT, and it does not collapse to Conservative Dominance
either.** N is never predeclared. The rule fires Red when the Red count reaches `ceil(0.3 M)` and
Amber at `ceil(0.4 M)`. Because the bar is proportional to M, enlarging M with benign evidence
raises it: **three signals carrying one Red report Red, and adding a single Green module to the
same unchanged adverse finding downgrades it to Yellow.** That was demonstrated directly. Under
any genuine worst-N-of-M rule the selected worst N are unchanged by a benign arrival, so the
answer cannot improve.

**6.2 Weighted Voting, METHOD_LABEL_MISMATCH.** The canonical form is a weighted ordinal
severity score. Production accumulates weight into per-band buckets and reports whichever band
holds the most weight, which is a weighted plurality; no score field exists on the result. The
weights 1.5, 1.0, 0.6 and 1.5 are bare literals with no source, version or provenance field.

**6.3 Majority Rules, METHOD_PASS_CALIBRATION_PENDING.** The count is correct and the tie policy
is conservative in effect, an even split resolving to the more severe state, which was verified.
Two gaps, neither arithmetic: no minimum quorum is declared, so a single surviving signal decides
the ensemble, and duplicating one signal changes the count.

One property is genuinely good across all four and deserves recording: **an unrecognised status
string casts no vote at all and never reads as Green.** That was the fifteen-defects correction
and it holds under every probe this run made.

---

## 14. Category 7 findings: evidence combination, 1 of 20 reached

**7.1 Dempster-Shafer, METHOD_PASS_CALIBRATION_PENDING.** The combination rule is canonical and
was verified against an independent implementation written over explicit focal **sets** rather
than labels. Ignorance is handled correctly: the frame intersects every state instead of
conflicting with it, so the specification's worked combination reproduces exactly at mass 0.8 on
the singleton, 0.2 on the frame and a conflict coefficient of zero. Belief and plausibility, the
reliability discount and its normalisation, commutativity, and the admissibility of every
declared mass row all hold. Total conflict is flagged with a coefficient of one and yields no
decidable verdict, since every state is left carrying equal mass.

Two real limits. The mass table is a set of designed constants with no elicitation behind them.
And Dempster's rule assumes independent sources: **combining a source with an identical copy
sharpens belief beyond the original**, which is exactly the hazard when several correlated
transforms of one cost index are combined.

**The remaining 19 Category-7 targets were NOT REACHED IN THIS RUN**, including all four of the
category's concept-only modules.

---

## 15. Category 8 findings: governance and compliance

**NOT REACHED IN THIS RUN.** All 9 targets. **No regulatory determination of any kind was made by
this run**, and the regulatory snapshot column is `n/a` on every row rather than carrying an
unverified date.

## 16. Category 9 findings: data integrity

**The 7 module-level targets were NOT REACHED IN THIS RUN.** The **Category-9 architecture test,
which the specification makes mandatory, WAS executed** and is reported in section 28.

## 17. Category 10 findings: decision optimization

**NOT REACHED IN THIS RUN.** All 7 targets, including the four concept-only modules.

---

## 18. Portfolio Health findings: 5 of 5 reached

**Fully reached.**

**PH.1 Isolation Forest, METHOD_PASS_CALIBRATION_PENDING. Run 15's claim was checked rather than
believed, and it holds.** This is a genuine isolation forest: random attribute, split drawn
uniformly between the observed minimum and maximum, height limit at the log of the subsample,
external-node path-length correction, ensemble mean, and the canonical score transform, all
verified against an independently computed `c(n)` using the **exact** harmonic number. Production
uses the paper's own natural-log-plus-gamma estimate, so its normaliser sits below the exact
value; the size and the direction of that deviation were both checked and both are as the paper
describes. The scored project is excluded from its own reference cohort. On continuously
distributed features, one forest ranks a planted anomaly well above a central inlier, and the
inlier sits below the one-half no-anomaly level the paper states. Scores reproduce exactly and
move under a different seed.

**Two limits were found that Run 15 did not report.** On a degenerate cohort, where document risk
and progress are constant and the cost index takes three distinct values, **an extreme outlier
and a central inlier receive the same score**, because splits are drawn between the reference
minimum and maximum, so a point outside that range can never be separated by a single split, and
with two constant features the trees exhaust the height limit first. And because each project is
scored against a forest that excludes itself, two projects' scores come from different forests
and are not strictly comparable. The 0.576 threshold was frozen on synthetic data and **was not
retuned by this run.**

**PH.5 Anomaly Score, IMPLEMENTATION_DEFECT.** The weights change with data availability. The
composite is a plain mean over whichever constituents exist, so the presence of a history moves
the effective weight of the distance and rank terms from one half to one third; the score moves
with no change in the project. The specification names this exact failure. Two further lineage
problems compound it: **the first constituent is the standardised-distance quantity Run 15
retired from PH.1 for not being an isolation forest**, surviving here under a different name and
still feeding a composite; and the second is PH.2's own percentile rank, so the composite
re-reports portfolio-position evidence already reported. Genuinely good: the Run-14 constant
placeholder is gone, the score stays in the unit interval, and a more extreme project does not
score less anomalous.

**PH.2 and PH.3 are CORRECT_PROXY_ONLY**, and both are honest about what they are. PH.2's
percentile rank recomputes independently and is invariant to cohort order. PH.3's slope is
computed over **intervals rather than observations** and matches an independent least-squares
slope on the specification's own worked series at minus 0.1 per period; the trap the
specification warns about is not present, the Run-14 correction holds, and the module abstains by
absence rather than showing a colour when history is missing.

**PH.4 Cross-project Pattern Detector, OWNER_DECISION_REQUIRED.** The structural oracles hold:
an identical project is matched, a distant cohort yields no match, order does not matter, and
matching a healthy peer correctly reports Green rather than implying distress. But there is no
explicit pattern definition. The operator is a bare Euclidean distance under a literal radius of
0.15 with no provenance, and **it silently ignores the fourth feature of the declared
four-element vector**, so the declared feature vector and the operator's domain disagree.

---

## 19. Threshold provenance matrix

Classified for every band reached. **No citation was stretched to cover a threshold it does not
state.**

| Provenance class | Thresholds | Where |
|---|---|---|
| LITERATURE_EXACT | 2 | TCPI at 1.00 and VAC at 0 per cent, both definitional and stated by the source |
| LITERATURE_INFERRED | 2 | TCPI at 1.10 and VAC at −11.11 per cent, applying the Christensen and Heise 0.10 figure by an inference declared in code |
| REGULATORY_EXACT | 0 | Category 8 not reached |
| EMPIRICALLY_CALIBRATED (on synthetic data) | 2 | CUSUM k and h; Isolation Forest at 0.576 |
| OWNER_POLICY, unversioned | 4 | all four Category-6 ensembles |
| HEURISTIC_UNCALIBRATED | 11 | the remaining reached modules |
| UNSUPPORTED | 0 | none found among those reached |

`LITERATURE_INFERRED` is used deliberately in place of `LITERATURE_EXACT`: the sources state the
0.10 stability figure, not the band. The distinction is the specification's own instruction and
the code already carries it.

---

## 20. Parameter provenance matrix

| Status | Count | Modules |
|---|---|---|
| DEFINITIONAL | 2 | 1.7, 1.8 |
| PAPER DEFAULTS | 1 | PH.1, 100 trees and 256 subsample as published |
| DESIGNED CONSTANTS, no source | 3 | 1.3, 7.1, 1.4 |
| UNSOURCED LITERALS | 6 | 6.2 weights; PH.4 radius; 1.10 coefficient; band ladders in 1.9, PH.2, PH.3 |
| NO GOVERNED WEIGHTS | 1 | PH.5 |
| NOT ASSESSED | 79 | not reached |

---

## 21. Canonical-structure gaps

Six modules cannot represent the structure their registered name implies. **In every case the
gap is missing structure, not broken arithmetic**, which is why none is classified NOT_TESTABLE.

| Module | Structure required | Structure present |
|---|---|---|
| 1.6 Earned Schedule | cumulative planned-value curve | two percent-complete scalars |
| 1.5 ARIMA | p, d, q, diagnostics, interval | one AR coefficient on differences |
| 1.10 Regression to Mean | outside reference population | the project's own history |
| 1.11 ICE Ratio | two provenance-independent estimates | two formulas on one input vector |
| 6.2 Weighted Voting | ordinal severity score | per-band weight buckets |
| PH.5 Anomaly Score | governed constituent weights | availability-dependent mean |

---

## 22. Correct-abstention cases

Abstention was the scientifically correct result and was verified, not merely observed, in:
CUSUM and Kalman and Regression to Mean with insufficient history; ARIMA below three
observations and on a non-positive cost index; TCPI at a zero or negative remaining budget; VAC
and ICE at a non-positive cost index; Budget Execution on negative cost or out-of-range progress;
Earned Schedule outside the percentage domain; Bayesian EAC at a unit cost index; all four
Category-6 ensembles when nothing qualifies; Isolation Forest below two reference projects, **by
absence rather than beside a colour**; and PH.3 with no usable history, likewise by absence.

---

## 23. Label and method mismatches

`1.5 ARIMA CPI Forecast`, `1.6 Earned Schedule`, `1.11 ICE Ratio`, `6.2 Weighted Voting`.

**The first three carry no proxy qualifier at all**, so they reach the export, the API and the
methods documentation under their full canonical names. Thirty other modules do carry a
qualifier. These three are the gap in that scheme.

---

## 24. Implementation defects

`6.1 Conservative Dominance`, `6.4 Worst-N-of-M`, `PH.5 Anomaly Score`. Each is detailed above,
each was demonstrated by a canonical proposition failing against an independent oracle, and
**none was repaired**, because Run 17 is an audit.

**How these are held without fossilising them.** A defect cannot be turned green by fixing the
code in this run, and asserting the defective behaviour as expected would repeat a failure this
programme has already found five times. So `proposition()` in the suite records each failing
proposition in an anti-fossilisation register that fails in **both** directions: an unrecorded
defect fails the suite, and **a registered defect that starts holding also fails the suite**,
saying the Run-17 disposition has become stale and must be revised. Neither a new defect nor a
repaired one can pass silently.

---

## 25. Calibration gaps

Only two of the 21 reached modules have any calibration procedure at all, CUSUM and Isolation
Forest, both synthetic, both frozen at Run 15, **both left untouched by this run** as the
specification directs. Every other reached module's tunable parameters were selected without a
declared calibration procedure or a separate calibration fixture set.

## 26. Empirical-validation gaps

**Universal among the reached modules. All 21 are `NOT_DONE`.** No labelled outcome corpus, no
expert reference standard and no independent reference outcomes exist for this platform. The two
SCIENTIFIC_PASS results are identities whose arithmetic is definitional; that verifies the
identity, and says nothing about how often the band around it is right. Synthetic fixtures
establish arithmetic, structure, reproducibility and boundary behaviour, and they cannot
establish real-world predictive accuracy, effect size, external validity or production readiness.

## 27. Regulatory and version gaps

**No regulatory module was reached, so this run makes no regulatory determination.** The snapshot
column is `n/a` on every row rather than carrying a date this run did not verify. No module
anywhere in the reached set asserts legal compliance.

---

## 28. Lineage and double-count findings

**Executed in full, and this is the most consequential section of the run.**

- **The Category-9 qualification boundary is not enforced in code.** A Category-6 ensemble
  accepts a raw assembled status carrying no qualification object and returns a project status
  from it. The platform's own marker for that evidence is the single word `unqualified`, so the
  deviation is honestly declared in `signal_package.py` and is not prevented.
- **Qualification is not enforced at the boundary.** The ensemble returns an identical answer
  with and without a qualification marker attached, so nothing downstream can tell qualified
  evidence from raw.
- **No module carries a lineage identifier.** A second transform of the same adverse evidence
  raises the adverse count, which was demonstrated. Correlated transforms of one cost index each
  cast their own vote in Weighted Voting and Majority Rules.
- **Dempster combination sharpens belief when a source is combined with an identical copy**, so
  the rule's independence assumption is unenforced at exactly the point it matters.
- **PH.5 recycles a retired proxy and duplicates PH.2**, both confirmed numerically.
- **Genuinely good and confirmed:** all seven Category-9 modules are non-voting; abstentions are
  reported in a separate list and never beside a band; unknown status strings and empty strings
  and nulls all return no band rather than Green; and the status vocabulary is recognised in
  exactly one place, `fusion.normalise_status`, which handles casing and the `light-amber`
  substring trap correctly.

---

## 29. Concept-only scientific results without activation

**None of the eight concept-only modules was reached for scientific testing.** Each was
nonetheless individually re-checked for activation state and each refuses to execute, returning
no status colour under `DISABLED_UNSAFE`. **No concept-only module was activated, and none may be
activated on the strength of anything in this report.**

---

## 30. Material Cost Variance disabled-state proof

`3.4`, registry code `A3.4`. **Verified only, never executed.** Its registry identity and name
are retained. Its activation state is `DISABLED_EVIDENCE_UNDER_REVIEW`, which is deliberately not
the `DISABLED_UNSAFE` the eight concept-only modules carry: nothing here calls its arithmetic
wrong. It is non-voting. It was refused before its formula function was reached on four separate
input shapes, including shapes carrying its own material inputs. It is excluded from the Run-17
scientific population and is **an excluded record in this report, not a 101st results row.** Its
former method was not executed.

---

## 31. Mutation and fault-injection proof

Ten faults, **each byte-confirmed to have applied before any red was believed**, each turning its
guarded check red, each restored immediately. Evidence: `code_audit/run17_fault_injection.csv`.

| Fault | Applied | Turned red |
|---|---|---|
| Wrong Earned Schedule interpolation, fractional term dropped | yes | yes |
| Dempster-Shafer ignorance converted to conflict | yes | yes, canonical 0.8 became 0.6 |
| Pareto dominated point admitted to the frontier | yes | yes |
| M/M/1 denominator operator error | yes | yes, canonical L=2 became 0.4 |
| Isolation Forest score exponent sign | yes | yes, score left the unit interval |
| Pythagorean fuzzy admissibility violation | yes | yes |
| Linear Programming wrong optimum | yes | yes, vertex enumeration gives (2,6) at 36 |
| Regulatory rule-version mismatch | yes | yes |
| Category-9 raw-input bypass | yes | yes |
| Random-seed perturbation | yes | yes |

**Harness integrity was re-proved** against the four known lies: false prose claiming success, a
reported failed count, an unanchored result line, and the requirement that the numerator equal
the denominator. The runner accepts only `^RESULT: N/M( checks passed)?$` and fails on a nonzero
exit even beside a green line.

---

## 32. Full test results

| Suite | Checks |
|---|---|
| `test_run17_scientific_methods.py` (new) | 250 of 250 |
| Full server suite on the branch | 88 suites, 7207 of 7207 |
| Full server suite on merged main at `4bc29fc` | 88 suites, 7207 of 7207, exit zero |

Oracle self-test: 22 propositions from the specification's worked answers, zero failures.

---

## 33. Production byte-change proof

**GREEN. All 115 production files are byte-identical to `origin/main`.**

Every `.py`, `.js`, `.css`, `.html` and `.csv` under `server/app/`, `assets/`, `p0-baseline/` and
`index.html` was SHA-256 hashed before any work began and again at the end. The two manifests are
identical. `git diff origin/main` over those paths is empty. Nothing outside `server/tools/`,
`code_audit/` and the report and handoff was written.

## 34. Voting and activation proof

Voting set at end: **exactly `A1.7` TCPI and `A1.8` Variance at Completion**, unchanged.
Activation: the eight concept-only modules remain `DISABLED_UNSAFE` and each was individually
re-checked; Material Cost Variance remains `DISABLED_EVIDENCE_UNDER_REVIEW`. No disabled module
votes. No participant-visible file was touched, so the participant sequence, the pre-judgment
lock, the reveal and the final lock are all unchanged by construction rather than by inspection.

---

## 35. Owner decisions required

Surfaced, **not made**, and none was made in code.

1. **PH.4's pattern definition.** What pattern is this module meant to detect, over which
   features, at what radius? It currently ignores the fourth feature of its own declared vector.
2. **PH.5's composite weights.** They must be governed rather than emerging from data
   availability. Separately: should the retired standardised-distance proxy continue to feed it?
3. **The three unqualified label mismatches**, 1.5, 1.6 and 1.11. Rename, add a proxy
   qualifier, or rebuild to the canonical structure?
4. **Worst-N-of-M's exact aggregation.** It is neither worst-N-of-M nor conservative dominance.
   If the second stage becomes the maximum of the worst N it collapses to 6.1 and becomes
   redundant, which is a parsimony decision as much as a correctness one.
5. **Conservative Dominance's escalation rule.** Should a single Red escalate? The canonical
   answer is yes; the current rule is a deliberate-looking three-arm ladder, so this may be an
   owner policy that was never written down as one.
6. **Whether the Category-6 band maps become versioned owner policy** rather than remaining
   unsourced heuristics presented alongside sourced ones.
7. **Whether the Category-9 qualification boundary should be enforced in code** or remain a
   declared and accepted deviation.

---

## 36. Prioritised Run-18 remediation list

**Nothing in this queue was remediated in Run 17.**

**P0A, defect in a voting module or able to change participant status.** None. The two voting
modules are the run's two SCIENTIFIC_PASS results.

**P0B, a method emitting a favourable or adverse result from scientifically invalid or missing
evidence.**
1. `6.1` a lone Red signal is absorbed into Amber, so it selects routine early warning instead of
   management escalation through the governance layer.
2. `6.4` an unchanged adverse finding is downgraded by the arrival of unrelated benign evidence.
3. `PH.5` the composite moves when no project fact has changed, because its weights follow data
   availability.
4. The Category-9 raw bypass and the absence of any lineage identifier, which together let
   correlated evidence accumulate as though independent.

**P0C, overstated compliance or authority claim.** None found among the modules reached.
Category 8 was not reached and is therefore **unassessed, not cleared**.

**P1, canonical method implementation defect in non-voting analytical evidence.** None beyond
the P0B set.

**P2, missing calibration or parameter provenance where arithmetic is correct.** `1.3` prior and
likelihood variances; `1.4` Q and R; `1.1` distribution parameters; `6.2` weights; `7.1` mass
table and an enforced independence rule; `1.9`, `PH.2`, `PH.3` band ladders; `PH.1` a minimum
feature-variance abstention and a note that cross-project score comparison is unsupported;
`6.3` a declared quorum; `1.10` a reference population and an estimated coefficient.

**P3, naming and parsimony with no current decision consequence.** `1.5`, `1.6`, `1.11`, `6.2`.

**FUTURE, concept-only formalisms with no demonstrated incremental value.** The eight, all still
disabled, none reached.

**AND FIRST: the 79 unreached targets.** Categories 2, 3, 4, 5, 8, 9 and 10, and 19 of the 20
Category-7 modules, have no Run-17 determination. **Absence of a finding is not a clean bill.**

---

## 37. T6_HANDOFF audit and update

`T6_HANDOFF.md` was audited against committed `REPORT_*` files and Git history before any test
ran. It was chronologically complete through Run 16 with **one defect: the Run-16 entry carried
the literal placeholder `RUN16_MERGE_COMMIT`.** Repaired to `71150dd` from Git. No date, hash,
test count, version or finding was invented, and nothing else was altered. The Run-17 entry
records the branch and merge commits, the 100-module count proof, the `3.4` exclusion, production
files changed = none, test and audit files changed, voting and activation state, test counts,
disposition counts, gaps, fault-injection results, owner decisions and the exact Run-18 queue.

---

## 38. What Run 17 does and does not establish

**It establishes**, for 21 of 100 targets: whether the code reproduces the stated method; whether
the required structure exists; where every parameter and threshold comes from; whether results
regenerate from frozen inputs and seeds; and where the method's name and its behaviour diverge.
It establishes mechanically that the population is exactly 100, that the identifier source in the
repository is not the registry key and would have excluded the wrong module, that Material Cost
Variance is disabled and excluded, that the eight concept-only modules remain disabled, that the
voting set is unchanged, and that no production byte moved.

**It does not establish** that any module is validated. **The phrase "all 100 algorithms are
validated" is not supported by this run and would be false.** 79 targets have no determination at
all. Empirical validation is `NOT_DONE` for every one of the 21 that do. Every calibration found
is synthetic. No regulatory conformance was assessed. Synthetic known-answer testing cannot
establish real-world predictive accuracy, construction-project effect size, legal compliance,
external validity, practitioner utility or production readiness, and no result here should be
read as if it could.

The strongest legitimate conclusion is the one in section 1.
