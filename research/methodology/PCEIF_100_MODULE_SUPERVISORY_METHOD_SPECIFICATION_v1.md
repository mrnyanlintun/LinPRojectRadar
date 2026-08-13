RUN 17 — LITERATURE-GROUNDED SCIENTIFIC METHOD AUDIT
100-MODULE CANONICAL / DEFENSIBILITY VERIFICATION
TEST AND AUDIT ONLY — DO NOT REMEDIATE PRODUCTION ALGORITHMS IN THIS RUN

============================================================
0. PURPOSE AND ROLE BOUNDARY
============================================================

This run is different from the previous code audits.

The theoretical and methodological specification in this prompt has been supplied by the research/supervisory review after literature review.

YOUR ROLE IN RUN 17:
- inspect the current implementation;
- construct independent known-answer tests;
- construct structural, boundary, property and stochastic tests;
- compare the implementation against the theoretical contract below;
- determine exactly what the implementation does and does not satisfy;
- identify missing canonical structures, calibration, parameter provenance, regulatory evidence, or empirical validation;
- report discrepancies.

YOUR ROLE IS NOT:
- to infer the theory from the current implementation;
- to change the theory so the current implementation passes;
- to search for a convenient alternative formulation simply because it resembles the code;
- to treat existing application output as its own oracle;
- to repair production algorithms during this run;
- to activate disabled methods;
- to change voting;
- to change participant-visible behavior.

The code is evidence of IMPLEMENTATION.
It is not evidence of what the scientific method is supposed to be.

Where the literature permits multiple legitimate operators or formulations, do not arbitrarily fail one published formulation in favor of another. Instead determine:
1. which formulation the implementation claims to use;
2. whether that formulation is an established one;
3. whether its parameters/operators are explicitly declared;
4. whether the code faithfully implements that declared formulation.

If a methodological choice is genuinely unresolved, classify OWNER_DECISION_REQUIRED.
Do not invent the choice.

============================================================
1. MANDATORY HANDOFF AUDIT AT START
============================================================

Before touching tests:

1. Read T6_HANDOFF.md.
2. Inspect Git history for every merged remediation, audit, synthetic-data, calibration, integration, participant-readiness and Run-16 session since the last confirmed handoff.
3. Compare T6_HANDOFF.md against committed REPORT_* files and version/release records.
4. Repair missing chronological handoff entries from committed evidence only.
5. Do not invent dates, hashes, test counts, versions or findings.

Each repaired/current session entry must contain:
- date;
- run/session name;
- commit hash;
- simulation/synthetic/release version;
- scope;
- production files changed;
- synthetic/test files changed;
- voting/activation effect;
- tests and check counts;
- deviations;
- unresolved findings;
- stop/owner decisions;
- exact next-session requirements.

Run 17 is incomplete if the handoff is incomplete.

============================================================
2. HARD PRECONDITION — VERIFY RUN 16
============================================================

Run 17 is allowed to begin only after you prove from merged main that Run 16 completed successfully.

Required Run-16 state:
- Material Cost Variance 3.4 is TEMPORARILY DISABLED operationally;
- 3.4 remains in the registry/history and has not been deleted;
- 3.4 is non-voting;
- stale FINAL FLOW / reset-state truthfulness defect is resolved;
- no unintended voting expansion occurred;
- merged-main suite is green;
- T6_HANDOFF records the Run-16 result.

If any of those statements are not true:
STOP.
Do not perform Run 17.
Report the precise missing prerequisite.

Do not assume a Run-16 commit hash from this prompt. Derive it from Git.

============================================================
3. EXACT RUN-17 POPULATION
============================================================

The controlling research registry is:
PCEIF Master Module Registry & Data Contract v0.5.

Use literal registry identity / Module_ID_Text_Key.
Never parse identifiers such as 1.10, 2.10, 4.10, 7.10, etc. as floating-point numbers.
Never allow numeric coercion to turn 1.10 into 1.1.

The v0.5 project-level population is 96 modules.

Run 17 excludes exactly one module from scientific execution:
- 3.4 Material Cost Variance — TEMPORARILY DISABLED under the owner decision.

Therefore:
96 project-level
- 1 excluded 3.4
= 95 project-level Run-17 targets

Add the five portfolio modules:
PH.1 through PH.5

TOTAL RUN-17 SCIENTIFIC TARGET = 100 MODULES.

Mechanically prove this count from the registry before testing.

The following eight concept-only modules ARE included in the 100 scientific targets:
- 3.8 Parametric Cost Index
- 7.7 Plithogenic Sets
- 7.9 Quantum Probability
- 7.20 Hypersoft Sets
- 10.1 Multi-Objective Optimization
- 10.2 Linear Programming
- 10.5 Decision Sensitivity Matrix
- 10.6 Pareto Frontier Analysis

They are included because their mathematical methods are testable.

However:
THEY MUST REMAIN OPERATIONALLY DISABLED AND NON-VOTING.

A successful canonical laboratory test is NOT permission to activate them.

If your mechanical target count is not exactly 100:
STOP before scientific testing.
Produce the reconciliation instead of guessing.

============================================================
4. SCIENTIFIC VOCABULARY
============================================================

Do not use one word, "validated", to describe multiple forms of assurance.

Record these separately for every module:

IMPLEMENTATION_VERIFICATION
Does code reproduce the stated mathematical/rule specification?

STRUCTURAL_ELIGIBILITY
Does the required data/model structure actually exist?

PARAMETER_PROVENANCE
Are weights, probabilities, membership functions, rates, priors, process noise, thresholds, etc. sourced and versioned?

CALIBRATION
Were tunable parameters selected using a declared calibration procedure and separate data/fixture set?

EMPIRICAL_VALIDATION
Has intended-use performance been evaluated against independent real or appropriately governed reference outcomes?

REGULATORY_CURRENCY
For rule modules, is the applicable source/version/effective date current and applicable?

REPRODUCIBILITY
Can the result be regenerated from frozen inputs, parameters, method version and random seed where applicable?

Do not write:
"validated"

unless EMPIRICAL_VALIDATION is actually supported.

Use formulations such as:
- implementation verified;
- known-answer verified;
- calibration pending;
- empirically unvalidated;
- regulatory rule verified to snapshot;
- synthetic fixture verified;
- method-correct but intended-use validation pending.

============================================================
5. ALLOWED FINAL SCIENTIFIC DISPOSITIONS
============================================================

Every one of the 100 targets must receive exactly one primary disposition:

SCIENTIFIC_PASS
Canonical or explicitly defined method is faithfully implemented, required structure is present, and no material scientific deficiency was found. This does NOT imply empirical field validation unless separately stated.

METHOD_PASS_CALIBRATION_PENDING
Method/operator is correct but a tunable parameter, band or decision threshold still lacks sufficient calibration.

CORRECT_PROXY_ONLY
The code implements a coherent transparent indicator, but not the stronger canonical method implied by a broad name.

CORRECT_ABSTENTION
The canonical method properly refuses because the required scientific structure/evidence does not exist.

MISSING_CANONICAL_DATA_STRUCTURE
The method is legitimate but the implementation cannot represent the structure necessary to perform it.

PARAMETER_PROVENANCE_BLOCKED
The structure/operator exists but required priors, weights, reliability values, transition probabilities, membership functions, etc. lack defensible provenance.

THRESHOLD_CALIBRATION_BLOCKED
The underlying metric is correct but Green/Yellow/Amber/Red or another operational threshold has no defensible source/calibration.

REGULATORY_VERSION_BLOCKED
A conformance rule cannot be evaluated against an identified applicable/versioned authority.

METHOD_LABEL_MISMATCH
The implementation performs a materially different method from the registered name.

IMPLEMENTATION_DEFECT
The required method is represented, but the code implements it incorrectly.

FUTURE_RESEARCH_ONLY
The mathematical formalism is testable, but intended-use applicability/incremental value is not established and it must remain disabled/research-only.

OWNER_DECISION_REQUIRED
The literature permits alternatives and the project has not yet formally selected one.

Do not use NOT_TESTABLE merely because current code lacks the canonical structure.
Published mathematical methods remain testable.
If code cannot represent the canonical problem, use MISSING_CANONICAL_DATA_STRUCTURE or METHOD_LABEL_MISMATCH.

============================================================
6. METHOD-BASIS CLASSES
============================================================

Assign every module one:

A. STANDARDIZED_PROJECT_CONTROL_IDENTITY
B. ESTABLISHED_CANONICAL_METHOD
C. LITERATURE_SUPPORTED_ADAPTATION
D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR
E. PCEIF_GOVERNANCE_SYNTHESIS_RULE
F. VERSIONED_REGULATORY_CONFORMANCE_RULE
G. EXPERIMENTAL_OR_FUTURE_FORMALISM
H. EXTERNAL_EXTRACTION_OR_CLASSIFICATION_METHOD

A famous method name does not move a module into A/B if its code only implements a proxy.

============================================================
7. SOURCE HIERARCHY
============================================================

For THEORY / METHOD DEFINITION:
1. this Run-17 supervisory method specification;
2. the primary source or authoritative standard cited below;
3. peer-reviewed supporting literature;
4. category literature compendia;
5. v0.5 registry for architecture/data contracts.

For WHAT THE SOFTWARE CURRENTLY DOES:
1. current merged repository source;
2. current tests and frozen fixtures;
3. current handoff/reports;
4. older historical documents only as historical evidence.

Never use old design prose to override current code.

Never use current code to override the theoretical method.

For regulatory methods, use an explicitly dated rule snapshot.
The supervisory regulatory snapshot below is 2026-08-12.

If you have verified web access and find an official superseding source, STOP that module and identify the changed rule rather than silently updating it.
If you do not have web access, use the supplied snapshot and label it:
REGULATORY_SNAPSHOT_2026-08-12
not "current law".

============================================================
8. CORE LITERATURE / AUTHORITY LEDGER
============================================================

Use these as the starting theoretical authorities.

CATEGORY 1
- Page, E. S. (1954), Continuous Inspection Schemes, Biometrika 41, DOI 10.1093/biomet/41.1-2.100 — CUSUM.
- Caron, Ruggeri & Merli (2013), Bayesian Approach to Improve EAC in EVM, Project Management Journal, DOI 10.1002/pmj.21303.
- Caron, Ruggeri & Pierini (2016), Bayesian estimate-to-complete, International Journal of Project Management, DOI 10.1016/j.ijproman.2016.09.007.
- Kalman, R. E. (1960), A New Approach to Linear Filtering and Prediction Problems, DOI 10.1115/1.3662552.
- Box/Jenkins time-series framework for ARIMA identification, estimation, diagnostic checking and forecasting.
- Lipke (2003), Schedule Is Different — original Earned Schedule formulation.
- Lipke et al. (2009), Prediction of Project Outcome using EVM/Earned Schedule, DOI 10.1016/j.ijproman.2008.02.009.
- PMI EVM practice guidance / applicable EIA-748 contract basis for EVM identities.
- Vandevoorde & Vanhoucke (2006), duration forecasting using earned-value metrics, DOI 10.1016/j.ijproman.2005.10.004.

CATEGORY 2
- Arditi, Tokdemir & Suh (2001), Line of Balance learning, DOI 10.1016/S0263-7863(99)00079-4.
- Arditi, Tokdemir & Suh (2002), Challenges in LOB Scheduling, DOI 10.1061/(ASCE)0733-9364(2002)128:6(545).
- Al-Gahtani (2009), Float Allocation Using Total Risk, DOI 10.1061/(ASCE)0733-9364(2009)135:2(88).
- Al Haj & El-Sayegh (2015), Time-Cost Optimization Considering Float Consumption, DOI 10.1061/(ASCE)CO.1943-7862.0000966.
- Barraza, Back & Mata (2000), probabilistic project performance/SS-curves, Journal of Construction Engineering and Management.
- Dodin & Elmaghraby (1985), criticality indices in PERT networks, DOI 10.1287/mnsc.31.2.207.
- Elmaghraby (2000), criticality and sensitivity in activity networks, DOI 10.1016/S0377-2217(99)00483-X.
- Lu & Lam (2008), CPM under resource calendar constraints, DOI 10.1061/(ASCE)0733-9364(2008)134:1(25).

CATEGORY 3
- Reference Class Forecasting literature: outside-view empirical distribution from comparable completed projects; do not call a deterministic uplift without a governed reference class "RCF".
- Construction/project cost-risk literature: stochastic component/risk-event cost distributions, correlation, simulation and quantiles.
- Analogous estimating requires selected analogs plus governed normalization/adaptation.
- Parametric estimating requires calibrated coefficients relating cost to measurable drivers.
- Inflation/escalation requires a governed external index with time/geographic basis.

CATEGORY 4
- Moon, Lee & Chi (2022), automated construction specification review, Advanced Engineering Informatics 51, DOI 10.1016/j.aei.2021.101495.
- Construction RFI/submittal/NCR/change-order literature supports traceable rates/process indicators, but does not confer universal PCEIF status bands.
- Dispute progression must be based on actual dispute/claim-stage evidence, not generic project-stress variables.
- Specification "density" requires both a verified conflict numerator and explicit exposure denominator.

CATEGORY 5
- Zhao et al. (2010), construction change/DSM, DOI 10.1061/(ASCE)CO.1943-7862.0000168.
- Tuholski & Tommelein (2010), DSM implementation in AEC, DOI 10.1061/(ASCE)ME.1943-5479.0000016.
- Kermanshachi & Pamidimukkala (2023), sensitivity of cost-performance determinants, DOI 10.1061/(ASCE)LA.1943-4170.0000570.
- Collier et al. (2018), scenario analysis + PERT/CPM, DOI 10.1061/AJRUA6.0000976.
- Li & Taylor (2014), design-rework system dynamics, DOI 10.1061/(ASCE)CO.1943-7862.0000878.
- Love et al. (2011), rework dynamics, DOI 10.1061/(ASCE)CO.1943-7862.0000377.
- Carmichael (1986), construction queueing, DOI 10.1080/01446198600000013.
- Farid & Koning (1994), queueing/simulation, DOI 10.1061/(ASCE)0733-9364(1994)120:2(386).
- Min & Bjornsson (2008), Agent-Based Construction Supply Chain Simulator, DOI 10.1061/(ASCE)0742-597X(2008)24:4(245).
- Martinez (2010), DES studies in construction, DOI 10.1061/(ASCE)CO.1943-7862.0000087.
- Martinez & Ioannou (1999), construction simulation, DOI 10.1061/(ASCE)0733-9364(1999)125:4(265).

CATEGORY 7
- Shafer, A Mathematical Theory of Evidence — Dempster-Shafer.
- Pawlak (1982), Rough Sets, DOI 10.1007/BF01001956.
- Zadeh (1978), Possibility Theory, DOI 10.1016/0165-0114(78)90029-5.
- Zadeh (2011), Z-Numbers, DOI 10.1016/j.ins.2011.02.022.
- Pang, Wang & Xu (2016), Probabilistic Linguistic Term Sets, DOI 10.1016/j.ins.2016.06.021.
- Yang et al., RIMER Belief Rule Base inference, DOI 10.1109/TSMCA.2005.851270.
- Yager, Pythagorean fuzzy sets, DOI 10.1109/TFUZZ.2013.2278989.
- Torra (2010), Hesitant Fuzzy Sets, DOI 10.1002/int.20418.
- Mendel/type-2 fuzzy literature; Karnik-Mendel type reduction, including DOI 10.1109/TFUZZ.2006.882463.
- Jaynes (1957), Maximum Entropy, DOI 10.1103/PhysRev.106.620.
- Spherical fuzzy sets, DOI 10.3233/JIFS-181401.
- Senapati & Yager, Fermatean Fuzzy Sets, DOI 10.1007/s12652-019-01377-0.
- Stevic et al. (2020), MARCOS, DOI 10.1016/j.cie.2019.106231.
- Diakoulaki et al. (1995), CRITIC, DOI 10.1016/0305-0548(94)00059-H.
- Neutrosophic, Plithogenic and Hypersoft sources establish formal representations but do not establish PCEIF project-management utility. Treat applicability separately.
- Quantum probability is a genuine mathematical probability formalism; PCEIF project-control applicability requires an actual context/order-effect model and should remain future research otherwise.

CATEGORY 8 — REGULATORY SNAPSHOT 2026-08-12
- FAR FAC 2026-01, effective 2026-03-13.
- FAR 34.201 — EVMS policy.
- FAR 52.234-4 — EVMS contract clause.
- FAR Part 43 — contract modifications.
- FAR 43.102 — contracting-officer authority for modifications.
- FAR Subpart 46.2 — contract quality requirements.
- FAR Subpart 42.15 — contractor performance information; CPARS is the official source for past-performance information.
- OMB Circular A-11 edition dated 2025-08-29.
- OSHA incidence-rate formula and OSHA leading-indicator guidance.
- EPA NPDES construction stormwater / applicable CGP and governing jurisdictional permit.
These are rule/governance authorities, not statistical validation of a score.

CATEGORY 9
- Wang & Strong (1996), data quality, DOI 10.1080/07421222.1996.11518099.
- Pipino, Lee & Wang (2002), Data Quality Assessment, DOI 10.1145/505248.506010.
- Westin & Sein (2014), construction engineering data quality, DOI 10.1061/(ASCE)ME.1943-5479.0000202.
- Soman & Whyte (2020), construction data-science codification, DOI 10.1061/(ASCE)CO.1943-7862.0001846.
- Zadeh et al. (2017), information quality for facility management, DOI 10.1016/j.aei.2017.06.003.

CATEGORY 10
- El-Rayes & Kandil (2005), time-cost-quality trade-off, DOI 10.1061/(ASCE)0733-9364(2005)131:4(477).
- Kandil & El-Rayes (2006), multiobjective construction resource optimization, DOI 10.1061/(ASCE)0742-597X(2006)22:3(126).
- Karaa & Nasr (1986), resource management/optimization in construction, DOI 10.1061/(ASCE)0733-9364(1986)112:3(346).
- Lorterapong & Ussavadilokrit (2013), construction scheduling with CSP, DOI 10.1061/(ASCE)CO.1943-7862.0000582.
- Classical LP formulation and independently solvable small LP problems.
- Pareto nondominance.
- Savage/minimax-regret decision logic.

PORTFOLIO
- Liu, Ting & Zhou (2008), Isolation Forest, DOI 10.1109/ICDM.2008.17.
- PH.2-PH.5 must be evaluated according to their actual declared descriptive/statistical contracts; do not borrow Isolation Forest's pedigree for them.

NIST
- NIST AI RMF 1.0, NIST AI 100-1, DOI 10.6028/NIST.AI.100-1.
Use only as governance/TEVV context.
It does not certify any PCEIF algorithm.
AI RMF 1.0 is under revision as of this supervisory review.

============================================================
9. GENERAL SCIENTIFIC TEST PROTOCOL
============================================================

For EACH of the 100 modules create a METHOD CARD with:

module_id
module_name
category
basis_class
canonical_or_declared_method
primary_source
supporting_sources
formal_definition
required_structure
required_inputs
input_units
minimum_cardinality
valid_domain
parameters
parameter_provenance_requirement
stochastic_or_deterministic
output_definition
known_answer_oracle
invariants
metamorphic_properties
missing_input_behavior
invalid_input_behavior
calibration_requirement
threshold_status
empirical_validation_requirement
lineage/dependence_notes
permitted_claim
prohibited_claim
current_code_location
current_implementation_summary
scientific_disposition
evidence

Every module must have a module-specific result.
Do not mark 20 modules PASS because a common helper passed.

Every module must receive at minimum:
1. one positive known-answer/structural test;
2. one negative/boundary/missingness test;
3. one invariant/metamorphic/property test where mathematically applicable.

Every test must be proven capable of failing.
Use one or more of:
- deliberate operator mutation;
- incorrect expected value;
- removed structure;
- boundary corruption;
- invalid parameter;
- swapped sign/direction;
- duplicate lineage;
- random-seed perturbation;
- altered rule version.

Restore after each fault.

Production output is NEVER the expected answer simply because production produced it.

For stochastic methods:
- predeclare tolerance before observing results;
- use analytic expectation where available;
- use multiple seeds where appropriate;
- record sample size;
- record convergence diagnostics;
- compare to an independently implemented oracle where feasible;
- dev-only libraries are permitted as independent references;
- do not add them to production dependencies unless separately authorized.

For deterministic methods:
- use exact arithmetic when feasible;
- define numerical tolerance before running;
- include dimensions/units;
- test scale/unit invariance when mathematically required.

For symbolic/fuzzy/evidence methods:
- test defining axioms and admissibility constraints;
- test identity/extreme/boundary cases;
- test the declared combination operator;
- do not infer empirical calibration from algebraic correctness.

For regulatory modules:
- test applicability;
- rule version;
- effective date;
- required evidence;
- NOT_APPLICABLE;
- INSUFFICIENT_EVIDENCE;
- conflicting evidence;
- superseded rule;
- human authority;
- prohibit "legally compliant" conclusions.

============================================================
10. CATEGORY 1 — QUANTITATIVE EVM / FORECASTING
11 TARGETS
============================================================

1.1 MONTE CARLO EAC FORECAST
Basis: LITERATURE_SUPPORTED_ADAPTATION.

Canonical scientific requirement:
Monte Carlo is a sampling procedure over an explicitly declared stochastic final-cost model. The scientific object is the input probability model plus the sampling procedure, not the mere presence of random numbers.

Required:
- explicit uncertain variables/distributions;
- parameter provenance;
- dependencies/correlation if assumed;
- deterministic mapping from sampled variables to EAC;
- iteration count;
- seed/reproducibility;
- P50/P80 extracted from the empirical simulated distribution;
- convergence evidence.

Current PCEIF production model may retain the dedicated BAC/CPI/SPI/document-risk Beta-PERT adaptation established by the prior Monte Carlo fixture. Do NOT falsely claim that that specific spread mapping is a universal literature EAC model.

Beta-PERT laboratory identity for lambda=4:
mean = (a + 4m + b) / 6.

Oracle:
for a=80, m=100, b=140:
analytic mean = (80 + 400 + 140)/6 = 103.333333...
A sufficiently large seeded sample should converge within a predeclared statistical tolerance.
Also prove P50 <= P80 and both lie within support.

Pass ceiling without empirical calibration:
METHOD_PASS_CALIBRATION_PENDING.

1.2 CUSUM ANOMALY MONITOR
Basis: ESTABLISHED_CANONICAL_METHOD.

Use a two-sided tabular standardized CUSUM:
Cplus_t = max(0, Cplus_(t-1) + z_t - k)
Cminus_t = max(0, Cminus_(t-1) - z_t - k)

where:
z_t = (x_t - mu0)/sigma

Signal when:
Cplus_t > h or Cminus_t > h
according to the declared inclusive/exclusive boundary.

Run-15 frozen design:
k = 0.5 sigma
h = 5 sigma
calibration target = persistent level shifts, not isolated one-period spikes.

Do not retune these values in Run 17.
Verify the frozen calibration record and implementation.

Simple oracle:
mu0=0, sigma=1, x_t=1 repeatedly, k=.5.
Cplus increases .5 each observation.
At 10 observations Cplus=5.
At 11 observations Cplus=5.5.
The exact signal observation depends on declared > versus >= h and must agree with the frozen contract.

Also recheck the Run-15 holdout calibration evidence rather than silently replacing it.

1.3 BAYESIAN EAC
Basis: ESTABLISHED_CANONICAL_METHOD.

Bayesian requirement:
posterior proportional to likelihood times prior.

For a normal-normal laboratory case:
prior theta ~ N(mu0, tau0^2)
observation y ~ N(theta, sigma^2)

posterior variance:
tau1^2 = 1 / (1/tau0^2 + 1/sigma^2)

posterior mean:
mu1 = tau1^2 * (mu0/tau0^2 + y/sigma^2)

Oracle:
mu0=100
tau0^2=100
y=120
sigma^2=100

Expected:
posterior mean=110
posterior variance=50.

Production must state what theta represents, prior source, likelihood model and variance provenance.
Designed variances may verify algebra but cannot support calibrated-Bayesian claims.

1.4 KALMAN FILTER SPI SMOOTHER
Basis: ESTABLISHED_CANONICAL_METHOD.

For scalar random-walk state:
x_pred = x_prev
P_pred = P_prev + Q
K = P_pred / (P_pred + R)
x_post = x_pred + K(z - x_pred)
P_post = (1-K)P_pred

Oracle:
x0=1
P0=1
Q=0
R=1
z1=2

Expected:
P_pred=1
K=.5
x1=1.5
P1=.5

Q/R are model parameters requiring provenance/calibration.
Correct recursion with arbitrary fixed Q/R is METHOD_PASS_CALIBRATION_PENDING, not empirical validation.

1.5 ARIMA CPI FORECAST
Basis: ESTABLISHED_CANONICAL_METHOD.

ARIMA(p,d,q) requires:
- explicit differencing order d;
- AR coefficients;
- MA coefficients;
- intercept/drift treatment;
- identification/model-selection rule;
- estimation method;
- stationarity/invertibility handling;
- residual diagnostics;
- forecast and uncertainty interval.

General form after differencing:
phi(B)(1-B)^d y_t = c + theta(B)e_t.

A single AR coefficient on first differences is not automatically a complete "ARIMA forecasting" workflow.

Testing:
- separate coefficient-estimation tests from forecast-recursion tests;
- for a fixed supplied model object, hand-check one-step forecasts exactly;
- test constant series;
- test insufficient history;
- test nonfinite values;
- test residual handling.

If code only implements a fixed AR(1)-difference heuristic:
CORRECT_PROXY_ONLY or METHOD_LABEL_MISMATCH.

1.6 EARNED SCHEDULE
Basis: ESTABLISHED_CANONICAL_METHOD.

Canonical Earned Schedule requires the cumulative planned-value curve.

Find integer period C such that:
PV_C <= EV < PV_(C+1)

Then:
ES = C + (EV - PV_C) / (PV_(C+1) - PV_C)

Schedule variance in time:
SV(t) = ES - AT

Schedule performance index in time:
SPI(t) = ES / AT

Oracle:
PV cumulative at periods:
0 -> 0
1 -> 20
2 -> 40
3 -> 60

EV=50
AT=3

Expected:
C=2
ES=2 + (50-40)/(60-40) = 2.5
SV(t)=-0.5
SPI(t)=0.833333...

A ratio of actual percent complete to planned percent complete is not Earned Schedule.

1.7 TCPI
Basis: STANDARDIZED_PROJECT_CONTROL_IDENTITY.

To complete to BAC:
TCPI_BAC = (BAC - EV) / (BAC - AC)

To complete to an approved EAC:
TCPI_EAC = (BAC - EV) / (EAC - AC)

The target basis MUST be explicit.

Oracle:
BAC=100
EV=60
AC=70

TCPI_BAC = 40/30 = 1.333333...

If approved EAC=120:
TCPI_EAC = 40/50 = 0.8.

Test denominator <=0 and completed-project boundaries.
Do not infer a universal traffic-light band from the identity itself.

1.8 VARIANCE AT COMPLETION
Basis: STANDARDIZED_PROJECT_CONTROL_IDENTITY.

VAC = BAC - EAC

The selected EAC must be explicitly identified.

Oracle:
BAC=100
EAC=120
VAC=-20.

If production chooses EAC=BAC/CPI, that EAC convention must be recorded.
The identity does not validate a status band.

1.9 BUDGET EXECUTION RATE
Basis: PCEIF_CUSTOM_TRANSPARENT_INDICATOR.

There is no universal canonical "Budget Execution Rate" status algorithm for this PCEIF use.

A defensible contract compares actual expenditure to an approved time/progress expenditure profile:
ExecutionRatio(t) = AC(t) / ExpectedSpend(t)

or an explicitly documented equivalent.

Oracle candidate for the declared PCEIF contract:
ExpectedSpend=50
AC=60
ratio=1.20
deviation=+20%.

If code instead compares AC directly to BAC/progress without an approved spend profile, classify only the narrower proxy actually implemented.

No universal Green/Amber/Red thresholds may be attributed to literature.

1.10 REGRESSION TO MEAN CPI
Preferred scientific role: CPI Reference-Class Shrinkage.
Basis: LITERATURE_SUPPORTED_ADAPTATION.

Shrinkage form:
CPI_shrunk = w*CPI_project + (1-w)*mu_reference
0 <= w <= 1.

Oracle:
CPI_project=.80
mu_reference=1.00
w=.60
CPI_shrunk=.88.

The reference population and w need provenance or estimation.
A fixed .5 average may be algebraically coherent but remains an uncalibrated adaptation.

1.11 ICE RATIO
Preferred scientific role: Independent EAC Reconciliation Index.
Basis: PCEIF_CUSTOM_TRANSPARENT_INDICATOR.

A legitimate reconciliation requires TWO analytically/provenance-independent estimates.

Example:
IndependentEstimate=120
ManagementEAC=100

ratio=1.20
relative divergence=(120-100)/100=.20.

If both estimates are deterministic transformations of the same CPI/BAC inputs with no independent source/model:
the independence claim fails even if the division is correct.

============================================================
11. CATEGORY 2 — SCHEDULE ANALYTICS
11 TARGETS
============================================================

2.1 PERT NETWORK CRITICALITY
Basis: ESTABLISHED_CANONICAL_METHOD.

Requires an actual activity network with precedence relationships and duration distributions.

Classical PERT activity moments:
E[T] = (O + 4M + P)/6
Var[T] = ((P-O)/6)^2

For stochastic criticality:
CriticalityIndex_i =
number of simulation trials in which activity i is critical
/
total simulation trials

Known deterministic network:
A duration 3
B duration 2
C duration 1
A -> C
B -> C

Path A-C=4
Path B-C=3
Expected deterministic critical activities:
A and C.
B noncritical.

A hard-coded illustrative network is not project-specific PERT Network Criticality.

2.2 LINE OF BALANCE
Basis: ESTABLISHED_CANONICAL_METHOD.

Requires repetitive units/locations and activity production lines.

For an activity:
production rate = change in units / change in time.

The schedule must preserve:
- unit/location sequence;
- crew continuity;
- predecessor/successor offsets;
- line intersection/interference constraints.

Oracle:
locations 1,2,3
planned completion times 1,2,3 days
actual 1,2.25,3.5 days.
Derive planned and actual production slopes and prove the direction of deterioration.

No universal LOB traffic-light threshold is supplied by the method itself.

If no repetitive/location structure exists:
CORRECT_ABSTENTION.

2.3 CCPM BUFFER HEALTH
Basis: ESTABLISHED_CANONICAL_METHOD FAMILY.

Requires a governed critical-chain schedule and real project/feeding buffers.

Core observable:
BufferPenetration =
BufferConsumed / OriginalBuffer

Fever-chart interpretation additionally uses critical-chain progress.

Oracle:
OriginalBuffer=10 days
RemainingBuffer=6
Consumed=4
Penetration=.40.

Do not infer buffer consumption from SPI or percent complete alone.
Fever-chart bands are management/calibration choices, not universal mathematical constants.

No governed buffer object:
CORRECT_ABSTENTION.

2.4 SCHEDULE COMPRESSION INDEX
Basis: PCEIF_CUSTOM_TRANSPARENT_INDICATOR.

The literature strongly supports schedule crashing/fast-tracking/time-cost tradeoff, but there is no single universal PCEIF "Schedule Compression Index".

Therefore test:
- the exact declared numerator;
- denominator;
- time units;
- zero denominator;
- sign;
- scale invariance;
- monotonicity.

A defensible transparent form may quantify:
required duration reduction / available remaining duration,
but do NOT silently replace the current formula with this example in Run 17.

If the registry does not define the exact metric:
OWNER_DECISION_REQUIRED.

Do not attribute PCEIF bands to canonical crashing literature.

2.5 FLOAT CONSUMPTION RATE
Basis: LITERATURE_SUPPORTED_ADAPTATION.

Network-derived float:
TF = LS - ES = LF - EF.

One transparent burn measure:
FloatConsumed = TF_baseline - TF_current
FloatConsumptionFraction =
FloatConsumed / TF_baseline

Oracle:
baseline total float=5 days
current total float=2 days
consumed=3
fraction=.60.

Must retain activity/path/status-date identity.
Do not fabricate float from percent complete.

2.6 S-CURVE DEVIATION
Basis: LITERATURE_SUPPORTED_ADAPTATION.

Requires time-indexed cumulative planned and actual/earned curves.

Point deviation:
D(t) = ActualCumulative(t) - PlannedCumulative(t).

Oracle:
planned=.60
actual=.50
D=-.10 = -10 percentage points.

A single snapshot can support only point deviation.
It does not by itself constitute longitudinal S-curve analysis.

2.7 MILESTONE TREND ANALYSIS
Basis: LITERATURE_SUPPORTED_ADAPTATION.

Requires repeated forecast dates for the same stable milestone identity.

For baseline B and forecast F_t:
Slip_t = F_t - B.

Trend may be expressed as a declared regression slope or another explicitly specified summary.

Oracle:
baseline completion day=100
successive forecasts=104,108,111
slips=4,8,11 days.
Direction must be deteriorating.

Insufficient repeated forecasts:
CORRECT_ABSTENTION for trend claims.

2.8 LOOK-AHEAD SCHEDULE HEALTH
Basis: PCEIF_CUSTOM_TRANSPARENT_INDICATOR informed by look-ahead/make-ready planning.

Do not confuse:
- Percent Plan Complete: completed commitments / planned commitments
with
- constraint readiness: unconstrained / planned.

If PCEIF measures readiness:
ReadyFraction =
(ActivitiesPlanned - ActivitiesConstrained) / ActivitiesPlanned

Oracle:
planned=10
constrained=3
ready=.70.

Window/horizon and definition of "constrained" must be governed.
Bands require calibration/policy evidence.

2.9 RESOURCE LOADING INDEX
Basis: LITERATURE_SUPPORTED_ADAPTATION.

Canonical resource loading is time-phased:
LoadRatio_t = Demand_t / AvailableCapacity_t.

Oracle:
capacity=100 labor-hours
demand=120
ratio=1.20.

Project-total planned-vs-actual labor hours is a performance proxy, not a time-phased resource loading model.

2.10 SCHEDULE RISK ANALYSIS P80
Basis: ESTABLISHED_CANONICAL_METHOD.

Requires:
- project activity network;
- duration distributions;
- identified risk events where used;
- dependencies/correlations where material;
- Monte Carlo schedule recomputation;
- empirical completion-date distribution.

P80 = 0.80 quantile of simulated completion.

Analytic laboratory oracle:
single activity T ~ Uniform(0,10).
True P80=8.

Simulation must converge to 8 within a preregistered tolerance.

A deterministic z-score uplift is not Schedule Risk Analysis P80.

2.11 CRITICAL PATH INDEX
Preferred scientific role where retained:
Critical Path Stability & Margin.
Basis: ESTABLISHED CPM METHOD + PCEIF ADAPTATION.

Require actual CPM forward/backward passes.

Known network:
A=3 -> C=2
B=4 -> C=2

Earliest project finish=6.
Path A-C=5.
Path B-C=6.

Expected:
B and C critical;
A total float=1;
B total float=0;
C total float=0.

A weighted combination of SPI and progress is not a critical-path calculation.

============================================================
12. CATEGORY 3 — COST RISK
8 RUN-17 TARGETS
3.4 IS EXCLUDED
============================================================

3.1 REFERENCE CLASS FORECASTING
Basis: ESTABLISHED_CANONICAL_METHOD.

Requires a governed empirical outside-view reference class:
- completed comparable projects;
- inclusion/exclusion criteria;
- comparable outcome definition;
- normalization;
- forecast-error/overrun distribution;
- sample size;
- percentile/uplift selection.

If r_i is historical proportional overrun:
U_p = Quantile_p({r_i})

AdjustedForecast =
InsideViewForecast * (1 + U_p)
when that is the governed application.

Oracle:
reference overruns =
0.00, 0.10, 0.20, 0.30, 0.40.
Median uplift=.20.

For nonmedian quantiles, freeze the quantile convention before evaluating.

Embedded fixed multipliers with no retrieved reference population are not RCF.

3.2 CONTINGENCY BURN RATE
Basis: PCEIF_CUSTOM_TRANSPARENT_INDICATOR.

Consumed fraction:
C = (OriginalContingency - RemainingContingency)
    / OriginalContingency

One transparent progress-normalized burn:
NormalizedBurn = C / ProgressFraction
when ProgressFraction > 0.

Oracle:
original=100
remaining=60
progress=.50
consumed fraction=.40
normalized burn=.80.

There is no universal literature traffic-light band.
Thresholds are governance/calibration decisions.

3.3 LABOR PRODUCTIVITY INDEX
Basis: LITERATURE_SUPPORTED_ADAPTATION.

Productivity requires OUTPUT per labor input.

ActualProductivity =
EarnedOutput / ActualLaborHours

PlannedProductivity =
PlannedOutput / PlannedLaborHours

ProductivityIndex =
ActualProductivity / PlannedProductivity.

Oracle:
planned productivity=10 units/hour
actual productivity=8
index=.80.

A ratio of planned/actual labor hours without earned output is a labor-hours performance proxy, not full productivity.

3.4 MATERIAL COST VARIANCE
NOT A RUN-17 SCIENTIFIC TARGET.

Verify only:
- registry identity remains;
- operational state disabled;
- non-voting;
- excluded from the 100 result count.

Do not execute its former method.

Owner rationale:
arithmetic baseline/current price variance alone cannot infer regional market conditions, procurement strategy, tariff/geopolitical conditions, substitution, quantity/mix effects or other contextual causal drivers without explicit evidence.

3.5 OVERHEAD ABSORPTION RATE
Basis: LITERATURE_SUPPORTED_ACCOUNTING/CONTROL ADAPTATION.

Requires:
- overhead amount;
- explicit allocation/absorption base;
- comparable planned and actual basis.

Example:
planned OH=100
planned driver=1000
planned rate=.10

actual OH=120
actual driver=1000
actual rate=.12

rate variance=.02
relative variance=20%.

If code only computes indirectCostActual / indirectCostPlan without an allocation base, it is an indirect-cost variance proxy, not an overhead absorption rate.

3.6 COST RISK ANALYSIS P80
Basis: ESTABLISHED CANONICAL METHOD FAMILY.

Requires a cost-risk model:
TotalCost =
BaseCostComponents + RealizedRiskEvents

with explicit distributions and material dependencies.

P80 = empirical 0.80 quantile of simulated total cost.

Simple oracle:
BaseCost=100
one independent Bernoulli event:
p=.5
impact=20

Distribution:
100 with probability .5
120 with probability .5
mean=110
P80=120 under the conventional right-continuous quantile interpretation.

Freeze exact empirical quantile convention in tests.

A deterministic CPI uplift is not CRA P80.

3.7 ANALOGOUS ESTIMATING RATIO
Basis: ESTABLISHED ESTIMATING METHOD FAMILY.

Requires:
- identified analogous project(s);
- comparability criteria;
- normalization;
- adaptation factors;
- provenance.

Example:
analog cost=100
size factor=1.20
location factor=1.10
adapted estimate=132.

A single preloaded "analog overrun percent" without analog selection/provenance is only a proxy.

3.8 PARAMETRIC COST INDEX
CONCEPT ONLY — REMAIN DISABLED.
Basis: ESTABLISHED CANONICAL METHOD.

A parametric model has measurable drivers and fitted/calibrated coefficients, e.g.:
Cost = beta0 + beta1*x1 + ... + betap*xp
or another declared nonlinear form.

Oracle for fixed coefficients:
Cost = 10 + 2*x1 + 3*x2
x1=4
x2=5
expected Cost=33.

Test:
- coefficient use;
- units;
- intercept;
- omitted driver behavior;
- design-matrix shape;
- prediction.

Comparing two EAC formulas is not parametric estimating.

Even if lab-correct:
remain CONCEPT_ONLY and non-voting.

3.9 INFLATION ADJUSTMENT INDEX
Basis: ESTABLISHED INDEX-ADJUSTMENT METHOD.

Requires an external governed price/cost index with:
- index series;
- geography;
- commodity/scope;
- base period;
- current period;
- vintage/source.

EscalationFactor =
Index_current / Index_base.

AdjustedCost =
BaseCost * EscalationFactor.

Oracle:
base index=200
current index=220
factor=1.10
base cost=100
adjusted=110.

Current/baseline material-price ratio with no external index is not a macro/regional inflation adjustment.

============================================================
13. CATEGORY 4 — DOCUMENT & RISK SIGNALS
10 TARGETS
============================================================

4.1 DOCUMENT RISK SCORE
Basis: EXTERNAL_EXTRACTION_OR_CLASSIFICATION_METHOD.

There is no universal scalar Document Risk Score.

A defensible implementation requires:
- governed risk taxonomy;
- source-document type;
- evidence span/excerpt;
- extracted candidate;
- severity;
- confidence;
- coverage;
- recency where used;
- score aggregation rule;
- labelled reference corpus;
- precision/recall/error analysis.

Run 17 must separate:
A. extraction/classification accuracy;
B. scalar aggregation arithmetic;
C. operational banding.

A correct score formula does not validate extraction accuracy.

Minimum test:
labelled positive/negative risk passages with held-out reference labels.
Report confusion counts, precision, recall and calibration if probabilities are claimed.

No source text / provenance:
ABSTAIN.

4.2 RFI VELOCITY
Basis: PCEIF_CUSTOM_TRANSPARENT_RATE.

Velocity:
RFI_count / exposure time.

Oracle:
12 RFIs over 30 days =
0.4 RFI/day
or 12/30*30 = 12 per standardized 30-day period if that is the declared unit.

If overdue ratio is separate:
OverdueRatio =
OverdueRFI / RelevantOpenRFI.

Do not combine revised cumulative registers as new events.

Bands require calibration.

4.3 SUBMITTAL REJECTION RATE
Basis: PCEIF_CUSTOM_TRANSPARENT_RATE.

RejectionRate =
Rejected / AssessedPopulation.

Oracle:
3 rejected of 20
=.15.

Validate:
0 <= rejected <= assessed.
Clarify status taxonomy:
rejected/resubmit/revise-and-resubmit/approved-as-noted etc.

A denominator mixing current-period decisions and cumulative backlog is invalid.

4.4 NCR RATE
Basis: PCEIF_CUSTOM_TRANSPARENT_QUALITY INDICATOR.

A true NCR rate requires an exposure denominator:
NCRRate =
NCR_events / inspected units, work hours, inspections, value, or another governed exposure.

Oracle:
4 NCRs / 100 inspections=.04.

Backlog state is separate:
OpenNCR
AgeOpenNCR
Severity
ClosureRate.

Do not call open/issued a universal NCR "rate" when populations differ.

4.5 WEATHER DAY IMPACT
Basis: LITERATURE_SUPPORTED_PROJECT IMPACT ANALYSIS.

Weather occurrence != schedule impact.

Required for a full impact claim:
- weather event/date;
- affected activity;
- planned work;
- actual lost time;
- governing allowance/calendar;
- available float/path;
- causal/linkage evidence;
- resulting schedule consequence.

Oracle:
verified weather event causes 2 days loss on a zero-float critical activity with no mitigation:
direct modeled path effect=2 days before downstream recovery logic.

A raw lost-day count without schedule linkage is only Weather Disruption Days, not full impact.

4.6 CHANGE ORDER FREQUENCY
Basis: PCEIF_CUSTOM_TRANSPARENT_RATE.

Frequency must have exposure:
number of governed change events / time or another declared opportunity basis.

Oracle:
6 changes in 180 days
=.033333/day
=1 per 30 days under standardized month.

Magnitude is separate:
sum change value / baseline contract value.

Do not combine frequency and magnitude into one quantity without naming it as a composite.

4.7 DISPUTE ESCALATION INDEX
Basis: PCEIF_GOVERNANCE/PROCESS ADAPTATION.

A real dispute-escalation signal requires actual claim/dispute state evidence.

Represent a versioned ordinal/state process such as:
issue/noticed
claim submitted
formal determination
negotiation
mediation/ADR
litigation/arbitration
or the actual project-specific governed process.

Do not invent universal stage names if the contract defines others.

Core properties:
- later governed escalation stage cannot look less escalated solely due missing generic KPI data;
- missing dispute evidence cannot improve condition;
- RFI/change counts alone do not establish dispute stage.

No dispute/claim-stage evidence:
CORRECT_ABSTENTION or explicit "project stress proxy", not dispute escalation.

4.8 SUBCONTRACTOR PERFORMANCE
Basis: LITERATURE_SUPPORTED_MULTI-CRITERIA PERFORMANCE ASSESSMENT.

Requires traceable criteria such as:
quality
schedule
safety
cost/change behavior
responsiveness
administration
and their governed ratings/weights.

If weighted average:
Score = sum(w_i*r_i)
with sum weights =1
and all weights versioned.

Simple arithmetic oracle:
ratings .80,.90,.70
equal weights
score=.80.

But critical violations may be noncompensatory by policy.

A precomputed compliance score with unknown construction cannot independently validate this module.

4.9 PROCUREMENT LEAD TIME MONITOR
Basis: ESTABLISHED SCHEDULE/PROCUREMENT CONTROL METHOD FAMILY.

Item-level slack:
ProcurementSlack =
RequiredOnSiteDate - ForecastDeliveryDate.

Oracle:
required day=100
forecast delivery day=110
slack=-10 days.

Risk classification should consider:
- item criticality;
- schedule/path need date;
- float;
- procurement status;
- forecast uncertainty.

Counts of "at risk" and "delayed" cannot be double-counted unless categories are explicitly disjoint.

4.10 SPECIFICATION CONFLICT DENSITY
Basis: LITERATURE_SUPPORTED DOCUMENT-REVIEW ADAPTATION.

True density:
ConflictDensity =
VerifiedConflictCandidates / ExposureUnit.

Exposure must be explicit:
requirements
clauses
sections
pages
cross-reference pairs
or other governed unit.

Oracle:
5 verified conflicts
250 requirements
density=.02 conflicts/requirement
=20 per 1,000 requirements.

Each conflict must retain the two or more conflicting evidence locations.

docRisk * sqrt(RFI_count) is not a specification-conflict density.

============================================================
14. CATEGORY 5 — SYSTEM DYNAMICS & COMPLEXITY
8 TARGETS
============================================================

5.1 DSM REWORK PROPAGATION
Basis: ESTABLISHED_CANONICAL_METHOD.

Require:
- named nodes/elements;
- directed dependency matrix D;
- matrix orientation;
- edge strengths/probabilities;
- seed rework vector;
- stopping/cycle policy.

Conceptual propagation:
R_(k+1) = D R_k

If cumulative:
declare whether seed is included and how multi-step propagation is accumulated.

Known oracle:
D =
[[0, 0.5],
 [0, 0]]

R0 =
[0,
 1]

under the convention R_next = D * R:
R1 =
[0.5,
 0]

R2 =
[0,
 0].

Test:
disconnected graph;
single edge;
chain;
cycle;
zero matrix;
edge-strength monotonicity.

No project DSM:
CORRECT_ABSTENTION.

5.2 SENSITIVITY ANALYSIS
Basis: ESTABLISHED_CANONICAL METHOD FAMILY.

Must name:
response Y
input Xi
base point
perturbation/range
local vs global method.

One normalized local sensitivity:
S_i =
(DeltaY / Y) / (DeltaXi / Xi).

Oracle:
Y = x1^2 + x2
base x1=2,x2=1 -> Y=5

increase x1 by 10%:
x1=2.2
Y=5.84
DeltaY=.84

S_x1 =
(.84/5)/(.2/2)
=1.68.

Do not call current badness/risk rank "sensitivity" unless an input is actually perturbed and output recomputed.

5.3 TORNADO RISK RANKING
Basis: ESTABLISHED SENSITIVITY PRESENTATION.

For each input:
Impact_i =
Y_i(high) - Y_i(low)

Rank descending by:
abs(Impact_i).

Oracle:
A low/high output=90/120 => impact30
B=98/105 =>7
C=80/110 =>30.

Expected A/C tie above B.
Tie policy explicit.

This should ordinarily present 5.2 sensitivity results.
If it independently creates duplicate evidence, flag lineage/double-count risk.

5.4 SCENARIO MODELING
Basis: ESTABLISHED SCENARIO-ANALYSIS METHOD FAMILY.

Scenario s is a coherent assumption vector:
X(s) = {x1(s),...,xp(s)}
Y(s)=f(X(s)).

Required:
- scenario name/version;
- rationale;
- jointly changed variables;
- consistency constraints;
- output model;
- no impossible combinations.

Oracle:
define an explicit two-variable test model and three coherent states
base/adverse/recovery.
Hand-calculate all three outputs.

Distinguish from Category 10:
Cat5 asks what happens to the system under conditions.
Cat10 asks which action should be selected.

5.5 REWORK FEEDBACK LOOP
Basis: ESTABLISHED SYSTEM-DYNAMICS METHOD FAMILY.

Requires time-dependent stocks/flows and feedback.

Core accounting example:
Backlog_(t+1) =
Backlog_t
+ NewWork_t
+ ReworkGenerated_t
- WorkCompleted_t

ReworkGenerated_t =
ErrorRate_t * WorkCompleted_t.

Oracle:
Backlog0=10
NewWork=5
WorkCompleted=8
ErrorRate=.25
Rework=2
Backlog1=9.

Test:
zero error;
zero work;
equilibrium;
conservation/accounting;
time-step sensitivity;
feedback amplification.

Weighted CPI/RFI/change score is not a feedback simulation.

5.6 QUEUEING THEORY BOTTLENECK
Basis: ESTABLISHED_CANONICAL METHOD.

Require:
arrival process/rate lambda
service process/rate mu
server count
queue discipline
stability assumptions
waiting/queue measures.

For M/M/1:
rho=lambda/mu
stable only if rho<1

L = rho/(1-rho)
W = 1/(mu-lambda)
Lq = rho^2/(1-rho)
Wq = rho/(mu-lambda)

Oracle:
lambda=2
mu=3

rho=2/3
L=2
W=1
Lq=4/3
Wq=2/3

Verify Little's Law:
L=lambda*W=2
Lq=lambda*Wq=4/3.

lambda>=mu must not emit a reassuring steady-state solution.

Constrained/planned activity count alone is not queueing theory.

5.7 AGENT-BASED SUPPLY CHAIN
Basis: ESTABLISHED CANONICAL METHOD FAMILY.

A true ABM requires:
Agents
States
Behavior Rules
Interaction Rules
Environment
Time
and stochastic rules where applicable.

Minimum laboratory model:
Supplier agent:
state inventory
rule: ship one unit when inventory>0 and request pending.

Carrier agent:
state available/busy
rule: collect shipped unit and deliver after declared travel delay.

Project agent:
state demand received/backordered.

Use a deterministic tiny scenario with one supplier, one carrier, one project and a known event sequence.
The hand-computed state history must match exactly.

Then test:
two agents;
zero stock;
delay;
rule perturbation;
seeded stochastic replication if stochastic rules are present.

A long-lead at-risk ratio is not ABM.

5.8 DISCRETE EVENT SIMULATION
Basis: ESTABLISHED_CANONICAL METHOD.

Require:
entities
events
simulation clock
resources
queues
routing
service/activity durations
event ordering
termination condition
random seed/distributions if stochastic.

Oracle:
one server
job A arrival 0 service 2
job B arrival 1 service 2

Expected:
A starts0 ends2 wait0
B arrives1, starts2, ends4, wait1
mean wait=.5.

Test simultaneous-event policy explicitly.
Test resource release.
Test queue order.
Test deterministic limiting case.
Test seeded stochastic case.
Test replication/convergence when stochastic.

Closed-form progress ratio is not DES.

============================================================
15. CATEGORY 6 — SIGNAL SYNTHESIS
4 TARGETS
============================================================

Important:
Category 6 creates NO new independent project evidence.
It synthesizes already qualified signal states.

It must not vote directly on raw CPI/SPI/docRiskScore in the target architecture.

Use one ordered severity vocabulary.
Example:
Green < Yellow < Amber < Red
with Abstain/Insufficient handled separately, not converted to Green.

6.1 CONSERVATIVE DOMINANCE
Basis: PCEIF_GOVERNANCE_SYNTHESIS_RULE.

Primary rule:
result = worst credible qualified signal.

Oracle:
Green, Yellow, Amber -> Amber.
Green, Red, Red -> Red.

Properties:
monotonicity;
permutation invariance;
duplicate-lineage neutrality;
abstention visibility;
unknown label rejected;
case normalization.

One severe qualified signal cannot disappear inside an average.

6.2 WEIGHTED VOTING
Basis: PCEIF_GOVERNANCE_SYNTHESIS_RULE.

Formalize:
Score =
sum(w_i * s_i)

where:
weights and ordinal score mapping are versioned.

Do not silently assume weights.

If missing signals are allowed:
the exact missingness/quorum/renormalization rule must be predeclared and tested.

Oracle using a laboratory configuration only:
severity scores 0,1,2,3
weights .5,.3,.2
states Green,Amber,Red
score =
.5*0 + .3*2 + .2*3
=1.2.

The 1.2-to-status mapping is a POLICY parameter and must not be called literature-derived.

Duplicating a same-lineage module must not manufacture extra evidence weight.

6.3 MAJORITY RULES
Basis: PCEIF_GOVERNANCE_SYNTHESIS_RULE.

For a declared categorical majority/plurality rule:
count qualified governed states.

Oracle:
Green,Red,Red -> Red.

Test:
ties;
even number;
abstentions;
unknown labels;
duplicate lineage;
minimum quorum.

Tie handling must be explicit.
Missing/unknown must never default to Green.

6.4 WORST-N-OF-M
Basis: PCEIF_GOVERNANCE_SYNTHESIS_RULE.

Must predeclare:
M eligible signals
N
selection rule
aggregation after selecting worst N
threshold map
abstention/quorum treatment.

Exhaust all ordinal combinations for the configured small M.

Important:
if the second-stage operation is simply max(worst N),
the method collapses mathematically to Conservative Dominance.
If so, classify it as redundant rather than pretending it supplies independent evidence.

============================================================
16. CATEGORY 7 — EVIDENCE COMBINATION / EPISTEMIC UNCERTAINTY
20 TARGETS
============================================================

GENERAL CAT-7 RULE

These methods represent uncertainty/evidence in different mathematical forms.
Passing their algebra does NOT establish that their PCEIF memberships, masses, linguistic probabilities or reliability assignments are empirically calibrated.

Categories 7.18 MARCOS and 7.19 CRITIC-TOPSIS are mathematically alternative-ranking methods and conceptually fit Category 10 better, but retain current IDs during Run 17.
Do not fail their mathematics solely because of category placement.
Flag placement separately.

7.1 DEMPSTER-SHAFER
Basis: ESTABLISHED_CANONICAL_METHOD.

Frame Theta.
Mass:
m: 2^Theta -> [0,1]
m(empty)=0
sum_A m(A)=1.

Belief:
Bel(A)=sum_(B subseteq A) m(B)

Plausibility:
Pl(A)=sum_(B intersect A != empty) m(B).

Dempster normalized combination for eligible independent evidence:
K =
sum_(B intersect C = empty)
m1(B)m2(C)

for nonempty A:
m12(A) =
[sum_(B intersect C=A) m1(B)m2(C)]
/
(1-K).

Reliability discount alpha:
for A != Theta:
m'(A)=alpha*m(A)

m'(Theta)=1-alpha+alpha*m(Theta).

Oracle:
Theta={G,R}

m1({G})=.6
m1(Theta)=.4

m2({G})=.5
m2(Theta)=.5

K=0
combined:
m({G})=.8
m(Theta)=.2.

Total conflict oracle:
m1({G})=1
m2({R})=1
K=1.
Do not divide by zero or fabricate a verdict.
Return explicit total-conflict/review state.

Also test dependence/lineage: Dempster combination is not permission to multiply correlated transforms of the same CPI evidence as independent sources.

7.2 ROUGH SETS
Basis: ESTABLISHED_CANONICAL_METHOD.

Requires:
- information/decision table;
- objects;
- condition attributes;
- decision attribute;
- indiscernibility relation.

For attribute set B:
IND(B) partitions U into equivalence classes.

Lower approximation:
B_lower(X) =
union of equivalence classes fully contained in X.

Upper:
B_upper(X) =
union of equivalence classes having nonempty intersection with X.

Boundary:
Upper - Lower.

Oracle:
U={1,2,3,4}
equivalence classes:
{1,2}
{3,4}

X={1,3,4}

Lower={3,4}
Upper={1,2,3,4}
Boundary={1,2}.

A majority vote over states is not Rough Sets.

7.3 NEUTROSOPHIC LOGIC
Basis: EXPERIMENTAL_OR_FUTURE_FORMALISM for PCEIF intended use.

Operational single-valued representation may use:
(T,I,F)
with each in [0,1].
Unlike ordinary probabilities, the three components need not sum to 1.

Required:
- exact selected neutrosophic variant;
- membership derivation;
- aggregation operator;
- interpretation of indeterminacy I;
- provenance.

Tests:
boundary values;
T/I/F domain;
identity/extreme cases;
declared aggregation.

Do not fabricate I as a convenient residual unless the selected formulation explicitly defines that choice.

A formula-correct implementation is not evidence of incremental PCEIF value.

7.4 INTERVAL FUZZY SETS
Basis: ESTABLISHED FUZZY METHOD FAMILY.

Each membership is an interval:
mu_A(x)=[mu_L(x),mu_U(x)]
0 <= mu_L <= mu_U <= 1.

For the standard min/max set operators:
intersection:
[min(l1,l2), min(u1,u2)]

union:
[max(l1,l2), max(u1,u2)].

Oracle:
A=[.4,.7]
B=[.5,.8]

intersection=[.4,.7]
union=[.5,.8].

If another published t-norm/t-conorm is chosen, cite and test that operator instead.

Membership widths require provenance/calibration.

7.5 Z-NUMBERS
Basis: ESTABLISHED FORMAL METHOD.

Z = (A,B)

A = fuzzy restriction/value
B = fuzzy reliability/confidence of A.

Both components must survive the input contract.

Test:
- changing B with fixed A changes the reliability-qualified result in the declared direction;
- B=maximum reliability approaches the A-only limiting case;
- missing B cannot silently become 1.

If implementation reduces Z to ordinary confidence-weighted scoring, document the published reduction used or classify proxy-only.

7.6 PLTS
Basis: ESTABLISHED FORMAL METHOD.

A probabilistic linguistic term set contains linguistic terms and associated probabilities/weights:
L(p) = {s_k(p_k)}.

Required:
- ordered linguistic term set;
- probability semantics;
- normalization/completeness rule;
- score/aggregation operator.

Tests:
- probabilities nonnegative;
- normalization rule;
- permutation invariance of representation;
- degenerate one-term set;
- missing probability treatment.

Hard-coded linguistic masses without elicitation/calibration:
PARAMETER_PROVENANCE_BLOCKED.

7.7 PLITHOGENIC SETS
CONCEPT ONLY — REMAIN DISABLED.
Basis: EXPERIMENTAL_OR_FUTURE_FORMALISM.

Required defining structure:
- attributes;
- attribute values;
- dominant value where used;
- appurtenance degrees;
- contradiction/dissimilarity degree c(v,D);
- explicitly selected plithogenic aggregation operator.

Test operator limiting cases under the chosen published formulation, especially contradiction-degree endpoints.

A generic weighted fuzzy average is not sufficient.

Even if algebraically correct:
FUTURE_RESEARCH_ONLY unless incremental PCEIF value is separately established.

7.8 BELIEF RULE BASE
Basis: ESTABLISHED CANONICAL METHOD FAMILY.

A rule:
IF antecedent attributes take reference states
THEN {consequent_j with belief degree beta_j}

with:
beta_j >=0
sum beta_j <=1.

Require:
- antecedent reference values;
- rule weights;
- attribute weights;
- matching/activation degrees;
- belief distribution;
- evidential-reasoning aggregation.

Oracle:
one fully activated rule with consequent:
Green .7
Amber .2
Red .1

With activation=1 and no other rules, output must equal that consequent distribution exactly.

Then test two-rule aggregation against independent implementation/hand calculation for the selected ER formulation.

7.9 QUANTUM PROBABILITY
CONCEPT ONLY — REMAIN DISABLED.
Basis: ESTABLISHED MATHEMATICAL FORMALISM / FUTURE PCEIF APPLICATION.

Canonical probability representation:
state rho or |psi>
event projector P_A

Born rule:
P(A)=Tr(rho P_A)
or
P(A)=<psi|P_A|psi>.

Oracle:
|psi> =
(1/sqrt(2))(|0>+|1>)

P0=|0><0|
Expected P(0)=.5.

For sequential/context effects, use explicit noncommuting projectors and order-dependent measurement.

A cosine interference heuristic on CPI/SPI without Hilbert-space event structure is not canonical quantum probability.

Even if lab-correct:
FUTURE_RESEARCH_ONLY until a real project-manager context/order-effect construct exists.

7.10 PYTHAGOREAN FUZZY SETS
Basis: ESTABLISHED FORMAL METHOD.

Membership mu and nonmembership nu must satisfy:
mu^2 + nu^2 <= 1.

Hesitancy:
pi = sqrt(1 - mu^2 - nu^2).

Oracle:
mu=.6
nu=.8
sum squares=1
pi=0
valid boundary.

mu=.8
nu=.8
sum=1.28
invalid.

Test selected score/aggregation separately.

7.11 PICTURE FUZZY SETS
Basis: ESTABLISHED FORMAL METHOD.

For positive mu, neutral eta, negative nu:
mu>=0
eta>=0
nu>=0
mu+eta+nu <=1.

Refusal degree:
r = 1 - mu - eta - nu.

Oracle:
mu=.4
eta=.2
nu=.3
r=.1.

A sum >1 is inadmissible.

Test selected aggregation operator separately.

7.12 HESITANT FUZZY SETS
Basis: ESTABLISHED FORMAL METHOD.

A hesitant fuzzy element is a finite set of possible membership values:
h(x) subset of [0,1].

Oracle:
h={.2,.5,.7}.

If the chosen score is arithmetic mean:
score=.466666...
But the scoring function itself must be declared; do not claim the mean is the only canonical choice.

Test:
empty set;
single value;
permutation;
domain bounds.

7.13 TYPE-2 FUZZY SETS
Basis: ESTABLISHED FORMAL METHOD.

For an interval type-2 implementation:
membership has lower and upper membership functions defining the footprint of uncertainty:
0 <= lower(x) <= upper(x) <= 1.

A full fuzzy-logic implementation must state:
fuzzification
rule base
inference
type reduction
defuzzification.

If centroid type-reduction uses Karnik-Mendel, test it against an independent reference implementation/known example.

Merely storing [lower,upper] and averaging them is an interval uncertainty proxy, not a complete type-2 fuzzy inference system.

7.14 MAXIMUM ENTROPY
Basis: ESTABLISHED_CANONICAL_METHOD.

For discrete probabilities:
maximize
H(p) = -sum_i p_i ln p_i

subject to:
p_i >=0
sum_i p_i=1
and explicit evidence/moment constraints.

Oracle:
two outcomes
only normalization constraint.

Expected maximum-entropy distribution:
(.5,.5)

H=ln(2).

Calculating entropy of an arbitrary hard-coded probability vector is entropy measurement, not Maximum Entropy inference.

7.15 POSSIBILITY THEORY
Basis: ESTABLISHED_CANONICAL METHOD.

Possibility distribution:
pi(x) in [0,1]
with sup pi(x)=1 for normalized case.

Possibility:
Pi(A)=sup_(x in A) pi(x)

Necessity:
N(A)=1-Pi(A_complement)

Maxitivity:
Pi(A union B)=max(Pi(A),Pi(B)).

Oracle:
pi(a)=1
pi(b)=.4

Pi({b})=.4
N({a})=1-.4=.6.

Test maxitivity and normalized supremum.

7.16 SPHERICAL FUZZY SETS
Basis: ESTABLISHED FORMAL METHOD.

For membership mu, nonmembership nu and hesitancy pi:
mu^2 + nu^2 + pi^2 <=1.

Oracle:
(.6,.6,.5)
squares=.36+.36+.25=.97
valid.

(.8,.8,.1)
=.64+.64+.01=1.29
invalid.

Test selected score/aggregation separately.

7.17 FERMATEAN FUZZY SETS
Basis: ESTABLISHED FORMAL METHOD.

Membership mu and nonmembership nu:
mu^3 + nu^3 <=1.

Oracle:
mu=.8
nu=.7
.512+.343=.855
valid.

mu=.9
nu=.9
.729+.729=1.458
invalid.

Test score/accuracy operator exactly as declared.
Membership design/calibration is separate from algebraic correctness.

7.18 MARCOS RANKING
Basis: ESTABLISHED MCDM METHOD.
Conceptually belongs with decision alternatives.

Requires:
- >=2 alternatives;
- >=2 criteria for substantive MCDM use;
- benefit/cost criterion designation;
- weights;
- decision matrix;
- ideal alternative;
- anti-ideal alternative;
- MARCOS normalization;
- weighted matrix;
- utility degrees/functions;
- final ranking.

Do NOT let a single project's three health values masquerade as three alternatives.

Build one small independent decision matrix and implement the published MARCOS steps separately from production.
Compare final utility ordering.

Test:
dominated alternative;
benefit/cost reversal;
weight scaling/normalization;
identical alternatives;
ideal/anti-ideal boundaries.

7.19 CRITIC-TOPSIS
Basis: ESTABLISHED COMBINED MCDM METHOD.
Conceptually belongs with decision alternatives.

CRITIC:
derive criterion contrast from standard deviation and intercriterion conflict/correlation.
A common form:
C_j = sigma_j * sum_k(1-r_jk)
w_j = C_j / sum C.

TOPSIS:
normalize decision matrix;
apply weights;
identify positive ideal A+ and negative ideal A-;
compute D_i+ and D_i-;
closeness:
CC_i = D_i- / (D_i+ + D_i-).

Rank descending CC.

Requires multiple alternatives.
A single project row cannot provide CRITIC contrast/correlation.

Test a small matrix with an independent implementation and inspect intermediate:
sigma
correlations
weights
ideal points
distances
closeness.

7.20 HYPERSOFT SETS
CONCEPT ONLY — REMAIN DISABLED.
Basis: EXPERIMENTAL_OR_FUTURE_FORMALISM.

Required structure:
- attributes;
- disjoint attribute-value subspaces;
- Cartesian product of subattribute/value selections;
- mapping/approximation relation over those tuples.

Critical test:
all required Cartesian-product tuples must be explicit.
Missing tuples may not silently receive a favorable/default value.

Use a tiny 2x2 Cartesian-product fixture and enumerate all 4 tuples.
Delete one tuple and prove explicit incompleteness/abstention.

Even if structurally correct:
FUTURE_RESEARCH_ONLY unless incremental value is established.

============================================================
17. CATEGORY 8 — GOVERNANCE & COMPLIANCE
9 TARGETS
============================================================

GENERAL:
Rule Check != Legal Determination.

No module may claim:
"FAR compliant"
"OMB compliant"
"OSHA compliant"
"EPA compliant"
or equivalent legal certification.

Permitted:
"Available evidence satisfies/does not satisfy/is insufficient for the configured rule check, subject to responsible-authority review."

8.1 ABM GOVERNANCE LAYER
Preferred theoretical identity:
Action Boundary & Authority Matrix.
Basis: PCEIF_GOVERNANCE_SYNTHESIS_RULE.

This should be deterministic governance, not agent-based modeling.

Inputs:
qualified signal package
evidence sufficiency
action class
decision authority
fairness/procedural-review requirement
override/defer/escalate rules.

Flow:
Signal package
-> evidence sufficiency
-> action class
-> required authority
-> procedural/fairness gate
-> human decision.

Exhaustively test combinations.

High-impact action must never bypass required human authority.

If registered name remains "ABM Governance Layer" while no agents exist:
METHOD_LABEL_MISMATCH.

8.2 FAR THRESHOLD MONITOR
Preferred:
FAR/Agency EVMS Applicability Monitor.
Basis: VERSIONED_REGULATORY_CONFORMANCE_RULE.

Snapshot:
FAR FAC 2026-01 effective 2026-03-13.
FAR 34.201.

EVMS applies to major acquisitions for development in accordance with OMB A-11, and agencies may require EVMS for other acquisitions under agency procedures.

Therefore applicability cannot be inferred from BAC alone.

Required evidence:
- acquisition status/designation;
- agency;
- applicable agency procedure;
- contract clause(s);
- award/effective date;
- rule version.

Output:
Applicable
Not Applicable
Review Required
Insufficient Evidence.

Test all four states.

8.3 OMB A-11 CHECK
Preferred:
Versioned A-11 Capital Programming Conformance Check.
Basis: VERSIONED_REGULATORY_CONFORMANCE_RULE.

Snapshot edition:
OMB Circular A-11 dated 2025-08-29.

Do NOT reduce A-11 to BAC/CPI/progress thresholds.

Represent each configured requirement:
rule_id
A-11 edition
section/appendix
applicability
required evidence
result
reviewer.

Result per rule:
Satisfied
Not Satisfied
Not Applicable
Insufficient Evidence.

No evidence:
never "compliant".

8.4 EVM REPORTING THRESHOLD
Preferred:
EVMS Reporting Compliance Monitor.
Basis: VERSIONED_REGULATORY_CONFORMANCE_RULE.

Snapshot:
FAR 34.201(c):
as a minimum, contractors submit monthly EVMS reports for contracts to which EVMS applies.

FAR 52.234-4:
applicable contractor EVMS must comply with EIA-748 current at time of award and submit reports as required by the contract.

Therefore required inputs include:
- applicability;
- contract clause;
- required reporting cadence/data item;
- due date;
- received date;
- governing contract/rule version.

CPI/SPI performance bands do not establish reporting compliance.

8.5 CONTRACT MODIFICATION FREQUENCY
Preferred governance role:
Modification Governance Check.
Basis: VERSIONED_REGULATORY/PCEIF GOVERNANCE ADAPTATION.

Avoid duplicate evidence with Cat4.6.

FAR Part 43 / 43.102 require authority and govern modification processing.

Test:
- authorized CO;
- modification type;
- written instrument;
- effective date;
- required approvals;
- missing authority;
- unilateral/bilateral distinction where applicable.

If module only counts changes:
CORRECT_PROXY_ONLY and note duplication with 4.6.

8.6 QUALITY COMPLIANCE INDEX
Basis: VERSIONED REQUIREMENT-CONFORMANCE INDICATOR.

FAR Subpart 46.2 supports acquisition-specific quality requirements.

Use:
ApplicableRequirements
AssessedRequirements
SatisfiedRequirements
CriticalExceptions.

One transparent aggregate:
ComplianceRate =
SatisfiedApplicableAssessed
/
ApplicableAssessed

but critical/high-consequence failures may be noncompensatory by policy.

Oracle:
92 satisfied of 100 assessed applicable requirements
=.92.

One critical exception must remain separately visible.

Unassessed requirements cannot silently count as satisfied.

8.7 SAFETY PERFORMANCE INDEX
Basis: REGULATORY/EMPIRICAL SAFETY-MEASUREMENT ADAPTATION.

Lagging incidence-rate identity:
IncidenceRate =
RecordableCases * 200000
/
EmployeeHoursWorked.

Oracle:
3 cases
200,000 hours
rate=3.0.

Zero hours:
abstain.

OSHA also explicitly supports leading indicators.
Therefore a PCEIF safety package should distinguish:
lagging outcomes
and
leading preventive evidence:
hazard reporting
inspections
training
corrective-action closure
etc.

Zero recorded injuries alone must not produce "strong safety system".

Never use "incidents discussed in meeting minutes" as an OSHA incidence-rate substitute.

8.8 ENVIRONMENTAL COMPLIANCE RATE
Basis: VERSIONED REQUIREMENT/PERMIT CONFORMANCE.

Environmental applicability is project/jurisdiction/permit specific.

For construction-stormwater:
identify whether NPDES/CGP or state/tribal/local authority applies;
permit version;
site/operator applicability;
required BMP/inspection/reporting obligations;
evidence for each applicable requirement.

Transparent rate, where appropriate:
SatisfiedApplicableRequirements
/
AssessedApplicableRequirements.

Critical permit violation remains separately noncompensatory.

Environmental issues mentioned in documents are evidence candidates, not a compliance percentage.

8.9 CONTRACTOR PERFORMANCE SCORE
Preferred:
Contractor Performance Assessment Signal.
Basis: GOVERNED OFFICIAL-ASSESSMENT INGESTION.

FAR Subpart 42.15 governs contractor performance information.
CPARS is the official source for federal past-performance information.

Required:
official/governed rating fields
supporting narratives
assessment period
status
review/comment state
source identifier.

Do not create an unofficial CPARS substitute.

If PCEIF aggregates official dimensions, weights/rules must be explicit.
Also preserve the worst/critical dimension separately rather than averaging it away without policy authority.

============================================================
18. CATEGORY 9 — DATA INTEGRITY & INFORMATION QUALITY
7 TARGETS
============================================================

CATEGORY-9 ARCHITECTURE TEST IS MANDATORY.

Target architecture:
Project Evidence
-> Category 9 assessment
-> Qualified Evidence
-> analytical/governance use.

Category 9 output is metadata/qualification.
It is NOT another independent risk vote.

Cats 6, 7, 8 and 10 must reject raw unqualified CPI/SPI/document-risk values under the v0.5 target contract.

9.1 MISSING DATA INDEX
Basis: PCEIF_CUSTOM_DATA-QUALITY INDICATOR grounded in data-quality literature.

Determine applicable required fields from the active module contract.

MissingFraction =
RequiredApplicableMissing
/
RequiredApplicableCount.

Oracle:
10 applicable required fields
2 missing
index=.20.

Important:
zero is a value.
null/missing != zero.

Not-applicable fields must not be counted missing.

9.2 DATA TIMELINESS SCORE
Basis: PCEIF_CUSTOM_DATA-QUALITY INDICATOR.

Age:
Age = period_cutoff - effective/source date.

Pass/fail/score must use a governed source-class freshness requirement, not one universal age.

Oracle:
allowed age 30 days
record age 20 -> timely
record age 40 -> stale.

Future-dated records require explicit invalid/review handling.

Separate this from reporting cadence in 9.7.

9.3 SOURCE RELIABILITY WEIGHTING
Basis: LITERATURE_SUPPORTED/PCEIF QUALITY ADAPTATION.

Reliability should be based on declared evidence characteristics such as:
source authority
verification status
provenance completeness
freshness
corroboration
extraction confidence where relevant.

A single BAC-based weight is nonsensical.

If using a weighted model:
every component weight must be versioned/provenanced.

Test monotonicity:
improving source verification while holding everything else constant must not lower reliability.

Do not let reliability weight become independent project-risk evidence.

9.4 AUDIT TRAIL COMPLETENESS
Basis: PCEIF_CUSTOM NONCOMPENSATORY GOVERNANCE QUALITY CHECK.

Required audit fields must come from actual signal/judgment/audit objects.

Define:
mandatory critical fields
optional fields
event sequence
immutable IDs/timestamps.

Critical fields are noncompensatory:
missing method version, evidence ID, judgment identity or required timestamp should not be averaged away by many optional fields.

Test:
complete record;
missing optional;
missing critical;
broken linkage;
chronology violation.

9.5 INFORMATION COMPLETENESS RATIO
Basis: PCEIF_CUSTOM PACKAGE-LEVEL QUALITY INDICATOR.

Must be distinct from 9.1.

9.1 asks:
Are mandatory fields missing?

9.5 should ask:
How much of the applicable overall evidence package is present/assessed?

Example:
8 applicable evidence components
6 present
package coverage=.75.

If implementation duplicates 9.1 with a second name:
METHOD_LABEL_MISMATCH or OWNER_DECISION_REQUIRED.

9.6 CROSS-DOCUMENT CONSISTENCY SCORE
Basis: PCEIF_CUSTOM MULTISOURCE CONSISTENCY CHECK.

Compare SAME governed fact across real source records:
field identity
unit
period/effective date
revision status
source authority
tolerance.

Oracle:
BAC source A=100.0
BAC source B=100.0
consistent.

A=100
B=110
with allowed tolerance 2%
material conflict.

Never average conflicting sources and make the conflict disappear.

9.7 REPORTING FREQUENCY INDEX
Basis: PCEIF_CUSTOM CADENCE QUALITY INDICATOR.

Requires report history and governed expected cadence.

For expected interval Delta:
compare actual reporting intervals to expected schedule.

Test:
perfect cadence;
one missed report;
duplicate report;
late report;
approved extension;
changed cadence;
cessation;
multiple report classes.

Frequency/cadence is not the same as freshness/timeliness.

============================================================
19. CATEGORY 10 — DECISION OPTIMIZATION
7 TARGETS
============================================================

GENERAL CATEGORY-10 CONTRACT

Input is not merely CPI/SPI/doc risk.

Canonical flow:
Qualified Project State
-> Candidate Actions
-> Feasibility/Constraints
-> Objectives
-> Optimization/Comparison
-> Scenario/Sensitivity/Regret
-> Human Authorized Selection.

10.1 MULTI-OBJECTIVE OPTIMIZATION
CONCEPT ONLY — REMAIN DISABLED.
Basis: ESTABLISHED_CANONICAL METHOD.

Formal form:
minimize_x
[f1(x), f2(x), ..., fk(x)]

subject to:
g_j(x) <= 0
h_l(x) = 0
and variable domains.

Requires:
decision variables
candidate interventions
objectives
constraints
feasible region
decision horizon.

Output should normally expose nondominated tradeoffs rather than one magically "best" option without preferences.

Oracle discrete feasible set:
A=(cost10, delay5)
B=(8,8)
C=(12,4)
D=(13,9)

minimize both objectives.

Expected nondominated:
A, B, C.
D is dominated.

Weighted average of current CPI/SPI/risk is not MOO.

Remain disabled even if lab passes.

10.2 LINEAR PROGRAMMING
CONCEPT ONLY — REMAIN DISABLED.
Basis: ESTABLISHED_CANONICAL METHOD.

Use the Wyndor Glass known-answer problem:

maximize:
3*x1 + 5*x2

subject to:
x1 <= 4
2*x2 <= 12
3*x1 + 2*x2 <= 18
x1 >=0
x2 >=0.

Known optimum:
x1=2
x2=6
objective=36.

Required test:
- exact feasible optimum;
- infeasible candidate rejection;
- binding constraints;
- nonnegativity;
- independent solver or vertex enumeration.

If current module cannot represent this LP:
MISSING_CANONICAL_DATA_STRUCTURE.

Remain disabled.

10.3 CONSTRAINT SATISFACTION ANALYSIS
Basis: ESTABLISHED CANONICAL METHOD FAMILY.

CSP requires:
variables X_i
domains D_i
constraints C_j.

A solution assigns all variables such that every constraint is satisfied.

Tiny oracle:
X in {A,B}
Y in {1,2}

constraint:
if X=A then Y=2.

Feasible:
(A,2)
(B,1)
(B,2)

Infeasible:
(A,1).

A four-rule management checklist is a transparent feasibility rule set, not a general CSP solver.
Classify according to actual claim.

10.4 WHAT-IF SCENARIO MATRIX
Basis: LITERATURE_SUPPORTED DECISION-SCENARIO METHOD.

Requires:
rows = candidate actions
columns = scenarios
cells = outcomes/payoffs or objective vector.

Example:
             S1   S2
Action A     10    2
Action B      6    6
Action C      2   10

Preserve this matrix for 10.7 regret testing.

This is different from Category 5 scenario modeling:
Cat5 models system conditions.
Cat10 compares actions under conditions.

Several EAC formulas with no action identity are not a full action-by-scenario decision matrix.

10.5 DECISION SENSITIVITY MATRIX
CONCEPT ONLY — REMAIN DISABLED.
Basis: ESTABLISHED SENSITIVITY/ROBUSTNESS METHOD FAMILY.

Requires:
decision model
base parameter values
perturbation ranges
recomputed action ranking/selection.

Output should show whether the decision changes.

Oracle:
define two alternatives whose ranking flips when one weight crosses a known value.
Verify the exact crossover.

Ranking current CPI/SPI deviations without perturbing a decision model is not decision sensitivity.

Remain disabled.

10.6 PARETO FRONTIER ANALYSIS
CONCEPT ONLY — REMAIN DISABLED.
Basis: ESTABLISHED CANONICAL METHOD.

For minimization, solution a dominates b if:
a is no worse than b in every objective
and strictly better in at least one.

Use the same oracle:
A=(10,5)
B=(8,8)
C=(12,4)
D=(13,9).

Expected nondominated frontier:
A,B,C.
D dominated.

Test permutation invariance and duplicate points.

Threshold booleans over one project are not Pareto analysis.

Remain disabled.

10.7 REGRET MINIMIZATION INDEX
Preferred:
Minimax Regret Decision Rule.
Basis: ESTABLISHED DECISION METHOD.

Requires action x scenario payoff/cost matrix.

For payoff maximization:
best payoff in scenario s:
M_s=max_a P_as

Regret:
R_as=M_s-P_as

Maximum regret for action:
R_a=max_s R_as

Choose action minimizing R_a.

Use matrix:
             S1   S2
A            10    2
B             6    6
C             2   10

Scenario maxima:
10,10.

Regrets:
A=(0,8), max8
B=(4,4), max4
C=(8,0), max8

Expected minimax-regret choice:
B.

No action/scenario payoff matrix:
CORRECT_ABSTENTION.

Fixed project-independent payoff constants that always choose the same action are not a meaningful project-specific regret analysis unless the matrix itself is the governed input.

============================================================
20. PORTFOLIO HEALTH
5 TARGETS
============================================================

Portfolio Health remains:
informational/program-context evidence,
not a sole contractual/escalation trigger.

Small-n performance must be explicitly reported.

PH.1 ISOLATION FOREST
Basis: ESTABLISHED_CANONICAL ML METHOD.

Run 15 reportedly replaced the former distance proxy with genuine pure-Python Liu/Ting/Zhou Isolation Forest.
Do not trust that statement blindly.
Verify current main.

Canonical concepts:
- random isolation trees;
- random feature;
- split selected between observed min/max;
- path length;
- ensemble expected path length;
- normalization c(n);
- anomaly score.

For n>2:
c(n)=2*H_(n-1) - 2*(n-1)/n.

Anomaly score:
s(x,n)=2^(-E[h(x)]/c(n)).

Requirements:
- training cohort separate from test item where appropriate;
- feature scaling contract;
- subsample size;
- number trees;
- seed;
- path-length correction for external nodes;
- reproducibility.

Run-15 reported independent sklearn-oracle rank agreement and frozen calibration.
Verify those frozen artifacts; do not retune the threshold.

Test:
known inlier cluster + distant anomaly;
rank anomaly highest;
seed reproducibility;
unit rescaling under the declared preprocessing;
small-n behavior.

Do not reuse old pre-Run-15 "not real Isolation Forest" findings as current truth.

PH.2 PORTFOLIO OUTLIER DETECTION
Basis: PCEIF_CUSTOM DESCRIPTIVE PORTFOLIO INDICATOR unless current code establishes another named method.

A percentile/rank-based outlier score is legitimate as descriptive comparison.

Required:
cohort definition;
feature orientation;
rank/percentile convention;
tie method;
minimum n;
missing-data policy.

Tiny ordinal oracle:
risk-oriented values:
[1,2,3,10].
The value 10 must receive the most extreme upper-tail rank under the declared convention.

Do not call a percentile rule a trained ML model.

PH.3 SIGNAL TRAJECTORY CLASSIFIER
Basis: PCEIF_CUSTOM TIME-TREND CLASSIFIER unless an actual trained classifier is present.

If the declared method uses slope:
fit/compute slope against time or reporting intervals.

Oracle with equally spaced times:
t=[0,1,2]
x=[1.0,.9,.8]
OLS slope=-.1 per period.

If negative direction means deterioration for the oriented feature, classification must follow the explicitly declared direction/bands.

Important:
3 observations contain 2 adjacent intervals.
Do not divide endpoint change by the wrong count.

A deterministic thresholded slope is a rule-based trajectory classifier, not learned ML.

PH.4 CROSS-PROJECT PATTERN DETECTOR
Basis: PCEIF_CUSTOM PORTFOLIO PATTERN INDICATOR unless a recognized clustering/similarity method is explicitly declared.

Require:
feature vector;
orientation;
normalization;
cohort;
similarity/distance operator;
pattern/match threshold;
minimum n.

Structural oracles:
- identical vectors produce maximum similarity/minimum distance;
- permutation of project order does not change pairwise result;
- uniformly distant vector is not a close match;
- matching a healthy peer must not automatically imply adverse status.

If the algorithm has no explicit pattern definition/operator:
METHOD_LABEL_MISMATCH or OWNER_DECISION_REQUIRED.

PH.5 ANOMALY SCORE
Basis: PCEIF_CUSTOM COMPOSITE PORTFOLIO INDICATOR.

This is a composite, not new independent evidence.

Require:
exact constituent PH inputs;
orientation;
normalization;
weights;
missingness behavior;
dependency/lineage.

No constant placeholder may enter as though observed evidence.

Properties:
- with all anomaly constituents at their minimum, composite should reach its declared minimum unless the contract explicitly says otherwise;
- increasing one adverse constituent while all others fixed must not improve the score;
- absence of history must not silently change all other effective weights;
- duplicating PH.1/PH.2 lineage must not manufacture additional confidence.

If weights change with data availability, that rule must be explicit and scientifically justified.

============================================================
21. CROSS-MODULE THRESHOLD AUDIT
============================================================

For every operational band/threshold classify its provenance:

LITERATURE_EXACT
The cited source actually states the same quantity and exact numeric threshold.

REGULATORY_EXACT
The applicable official rule states it.

EMPIRICALLY_CALIBRATED
The parameter was estimated/tuned under a documented calibration protocol using appropriate calibration data.

OWNER_POLICY
Explicit governance choice, versioned and approved, but not presented as a scientific empirical constant.

HEURISTIC_UNCALIBRATED
Designed number with no sufficient calibration/source.

UNSUPPORTED
No credible provenance.

Do not stretch a citation about a related metric to justify a PCEIF threshold.

A paper discussing "good schedule reliability" does not automatically source a particular PCEIF band.
A regulatory source establishing applicability does not automatically source a health threshold.

============================================================
22. CATEGORY-9 / LINEAGE / DOUBLE-COUNT SCIENTIFIC TEST
============================================================

This is a whole-system scientific requirement.

Build tests proving:

1. raw evidence is assessed/qualified by Category 9;
2. downstream Cats 6/7/8/10 consume qualified governed objects where the v0.5 target contract requires them;
3. a Category-9 quality score is not itself counted as another independent adverse/favorable project condition;
4. multiple transformations of the same CPI/SPI/document evidence preserve lineage;
5. duplicating a correlated/aliased module cannot manufacture stronger agreement/confidence;
6. abstentions remain visible;
7. missing evidence cannot silently become Green;
8. unknown status strings cannot become favorable evidence.

If current architecture still permits raw bypass:
report it.
Do not repair production in Run 17.

============================================================
23. SYNTHETIC DATA RULE
============================================================

Synthetic fixtures are allowed and expected for known-answer verification.

Every Run-17 synthetic fixture must carry:
data_origin = SYNTHETIC_RESEARCH_FIXTURE
not_for_empirical_validation = true

Synthetic known-answer data can establish:
- arithmetic correctness;
- structural correctness;
- reproducibility;
- boundary behavior;
- calibration mechanics where a calibration study is explicitly synthetic.

It cannot by itself establish:
- real-world predictive accuracy;
- actual construction-project effect size;
- legal compliance;
- external validity;
- practitioner utility;
- production readiness.

Never use synthetic PASS as equivalent to empirical validation.

============================================================
24. INDEPENDENT ORACLE RULE
============================================================

Do not copy production formulas into the test and call that independent.

Preferred oracle hierarchy:
1. hand calculation from the formal method above;
2. published worked example;
3. analytically known result;
4. independently written reference implementation from the formal equations;
5. reputable dev-only solver/library, cross-checked against 1-4.

Examples:
- LP: vertex enumeration and optionally independent solver.
- Isolation Forest: dev-only sklearn comparison plus canonical path-length properties.
- Dempster-Shafer: hand-calculated focal-set examples.
- Queue: closed-form M/M/1.
- CPM: hand network.
- DES: hand event schedule.
- Earned Schedule: manual PV interpolation.
- Pareto: hand nondominated set.
- Regret: hand regret matrix.
- fuzzy methods: admissibility and published operator identities.
- Monte Carlo: analytic means/quantiles where available plus convergence.

A second function copied from the first function is not independent.

============================================================
25. REQUIRED FILE ARTIFACTS
============================================================

Create TEST/AUDIT artifacts only.

Recommended:
server/tools/run17/
  method_cards.json
  source_ledger.csv
  scientific_results.csv
  known_answer_fixtures/
  oracle/
  README.md

and appropriate automated test file(s), for example:
server/tools/test_run17_scientific_methods.py

Produce:
REPORT_2026-08-XX_run17-scientific-method-audit.md

Use the actual execution date in the filename.

Do not modify production simulation algorithms.

Do not modify participant-visible HTML/JS/CSS.

Do not modify voting/activation.

Do not enable the eight concept-only methods.

Do not enable Material Cost Variance.

A small test-only adapter/oracle/helper under tests/tools is allowed if it cannot enter production imports.

============================================================
26. RESULTS MATRIX — EXACT REQUIRED COLUMNS
============================================================

scientific_results.csv must have exactly one target row for each of the 100 modules and include at least:

module_id
module_name
category
basis_class
operational_activation
voting_status
primary_method_source
canonical_structure_required
canonical_structure_present
implementation_verified
known_answer_pass
boundary_pass
missingness_pass
invariant_pass
stochastic_diagnostics_pass
reproducibility_pass
parameter_provenance_status
calibration_status
threshold_status
empirical_validation_status
regulatory_snapshot
cat9_qualification_status
lineage_status
scientific_disposition
production_change_made
finding_summary
required_next_action
test_names
evidence_paths

Assert:
row count = 100
unique module_id count = 100.

Create a separate excluded-record entry for 3.4 in the REPORT, not as a 101st scientific-results row.

============================================================
27. REPORT STRUCTURE
============================================================

The report must contain:

1. Executive scientific verdict
2. Exact Git baseline
3. Run-16 prerequisite proof
4. Mechanical 100-module population proof
5. Research/theory source hierarchy
6. Verification vs calibration vs empirical-validation distinction
7. 100-module results table
8. Category 1 findings
9. Category 2 findings
10. Category 3 findings + 3.4 exclusion confirmation
11. Category 4 findings
12. Category 5 findings
13. Category 6 findings
14. Category 7 findings
15. Category 8 findings
16. Category 9 findings
17. Category 10 findings
18. Portfolio Health findings
19. Threshold provenance matrix
20. Parameter provenance matrix
21. Canonical-structure gaps
22. Correct-abstention cases
23. Label/method mismatches
24. Implementation defects
25. Calibration gaps
26. Empirical-validation gaps
27. Regulatory/version gaps
28. Lineage/double-count findings
29. Concept-only scientific results without activation
30. Material Cost Variance disabled-state proof
31. Mutation/fault-injection proof
32. Full test results
33. Production byte-change proof
34. Voting/activation proof
35. Owner decisions required
36. Prioritized Run-18 remediation list
37. T6_HANDOFF audit/update
38. Final statement of what Run 17 does and does not establish.

============================================================
28. IMPORTANT INTERPRETATION RULES
============================================================

A module may have:
implementation_verified = true
and
empirical_validation_status = NOT_DONE.

That is normal.

A module may be mathematically canonical while its status bands remain unsupported.

A module may be a scientifically honest proxy and deserve CORRECT_PROXY_ONLY rather than "failure."

An abstention can be the scientifically correct result.

Do not reward a module for producing a colored answer when its required evidence is missing.

Do not penalize a canonical method merely because the controlled research project currently lacks real data needed for empirical validation.

Instead separate:
METHOD CORRECTNESS
from
DATA AVAILABILITY
from
CALIBRATION
from
EMPIRICAL VALIDATION
from
OPERATIONAL ACTIVATION.

============================================================
29. NO-PRODUCTION-CHANGE GUARD
============================================================

Before starting, hash/record all production code and participant assets relevant to simulation and research routes.

At end prove they are byte-identical unless a non-semantic report/test manifest file is intentionally outside those directories.

At minimum prove no unauthorized change to:
server/app/
participant-facing assets/
simulation production modules/
registry activation/voting logic.

If you accidentally change a production file:
revert it before completion.

Run 17 is an audit.
Run 18 will make owner-approved corrections.

============================================================
30. TEST HARNESS INTEGRITY
============================================================

Retain the strict harness behavior established by prior runs.

A suite counts as PASS only when:
- process exit is zero;
- expected anchored RESULT line is present;
- reported numerator equals denominator;
- no contradictory failure marker exists.

Re-prove the harness can fail using at least:
- false prose "all passed";
- reported failed count;
- green result line plus nonzero exit;
- silent crash.

For Run-17-specific tests, additionally inject scientific faults:
- wrong Earned Schedule interpolation;
- wrong LP optimum;
- D-S ignorance converted to conflict;
- queue denominator/operator error;
- Pareto dominated point admitted;
- iForest score/path mutation;
- one fuzzy admissibility violation;
- one regulatory rule-version mismatch;
- one Cat9 raw-input bypass.

Each must turn the relevant scientific test red.

============================================================
31. BROWSER / PARTICIPANT ROUTE
============================================================

Because Run 17 is not changing production:

Do not redesign participant pages.

Perform a focused regression only to prove:
- existing participant sequence still works;
- no new method/audit details leaked into participant view;
- no concept-only method became visible as an active recommendation source;
- 3.4 remains disabled;
- voting remains exactly the pre-Run-17 set;
- no audit tool affects research treatment assignment;
- pre-judgment lock/reveal/final lock behavior remains unchanged.

If these fail because of a pre-existing defect:
report it.
Do not silently repair unless it is necessary to restore a state Run 17 itself broke.

============================================================
32. OWNER DECISIONS TO SURFACE, NOT MAKE
============================================================

Explicitly surface any decision needed on:

- whether a proxy should ultimately be renamed or rebuilt;
- whether a mathematically correct but redundant Cat7 formalism has enough incremental value to retain;
- whether MARCOS/CRITIC-TOPSIS should later move logically to Cat10 while keeping stable IDs;
- exact Worst-N-of-M aggregation if not already frozen;
- exact PCEIF Schedule Compression Index definition if still underdefined;
- exact custom PH.4 pattern definition if underdefined;
- exact PH.5 composite weights if not governed;
- whether any threshold should become owner policy rather than empirical calibration;
- whether a canonical method should remain research-only despite passing implementation verification.

Do NOT make these owner decisions in code.

============================================================
33. RUN-18 PRIORITIZATION RULE
============================================================

At the end, construct a Run-18 queue ordered by:

P0A:
Any defect in a voting module or anything capable of changing participant/project status.

P0B:
A method emitting a favorable/adverse result from scientifically invalid or missing evidence.

P0C:
A regulatory/governance module making an overstated compliance/authority claim.

P1:
Canonical method implementation defect in non-voting analytical evidence.

P2:
Missing calibration/parameter provenance where arithmetic is otherwise correct.

P3:
Naming/category/parsimony cleanup with no current decision consequence.

FUTURE:
Experimental concept-only methods with no demonstrated incremental research value.

Do not remediate the queue in Run 17.

============================================================
34. PERMISSIONS
============================================================

You may work freely inside the repository.

You may:
- inspect all repo files;
- run code;
- run tests;
- run generators;
- run validators;
- run solvers;
- use browser automation;
- create temporary local environments;
- create temporary test databases;
- install dev-only packages in isolated temporary environments when needed for independent oracles;
- perform normal Git operations including fetch, status, diff, branch, checkout, switch, add, commit, merge, rebase and push;
- create and commit Run-17 test/report artifacts;
- merge/push main after the merged-main suite is green.

Do not ask permission for normal in-repo actions.

You may NOT:
- access or alter production Postgres;
- access production credentials;
- modify anything outside the repository;
- run production migrations;
- place synthetic data into operational or participant databases;
- change participant-visible behavior;
- change voting;
- change activation;
- change production algorithms in this run.

============================================================
35. GIT / MERGE RULE
============================================================

Work on a focused branch.

Before merge:
- full Run-17 suite green;
- all pre-existing required suites green except any explicitly documented known row that demonstrably predates this run;
- production-file hash guard green;
- activation/voting guard green;
- 100/100 result rows present;
- report present;
- handoff prepared.

Merge to main.
Run merged-main full suite again.
Only push final main after merged-main evidence is green.

If merged main differs materially from branch results:
STOP and investigate.

============================================================
36. T6_HANDOFF AT END
============================================================

Before declaring completion, update T6_HANDOFF.md with:

date
Run 17 name
branch commit
merge commit
release/simulation version if applicable
scope
100-module count proof
3.4 exclusion
production files changed = none expected
test/audit files changed
voting state
activation state
test counts
scientific disposition counts
canonical-structure gaps
parameter/calibration gaps
empirical-validation gaps
regulatory snapshot
fault-injection results
owner decisions
exact Run-18 queue

The final report must reference T6_HANDOFF.md.

If merged-main commit is only known after merge, update the handoff with the final hash and commit that update.

Run 17 is incomplete if T6_HANDOFF is missing or materially incomplete.

============================================================
37. DEFINITION OF DONE
============================================================

Run 17 is complete only if ALL are true:

[ ] Run 16 prerequisite proved.
[ ] 3.4 remains disabled/non-voting and excluded.
[ ] Exactly 100 scientific targets mechanically reconciled.
[ ] Every target has a full method card.
[ ] Every target has a primary scientific disposition.
[ ] Every target has positive known-answer/structural evidence.
[ ] Every target has a negative/boundary/missingness check.
[ ] Every mathematically suitable target has an invariant/property check.
[ ] Tests are proved capable of failing.
[ ] No current production output was used as its own oracle.
[ ] Verification, calibration and empirical validation are reported separately.
[ ] All stochastic tolerances were frozen before observing results.
[ ] Threshold provenance is classified.
[ ] Parameter provenance is classified.
[ ] Cat9 qualification architecture is explicitly tested.
[ ] Lineage/double-count behavior is explicitly tested.
[ ] Concept-only methods remain disabled and non-voting.
[ ] Voting set is unchanged.
[ ] Participant-visible behavior is unchanged.
[ ] Production algorithm files are unchanged.
[ ] Full suite passes on merged main.
[ ] Report is committed.
[ ] T6_HANDOFF is complete.
[ ] Run-18 remediation queue is produced.
[ ] No unsupported claim of "validated" appears.

FINAL REPORTING LANGUAGE:

Do not conclude:
"All 100 algorithms are validated."

The strongest legitimate conclusion, if supported by results, is of the form:

"Run 17 independently evaluated the implementation fidelity, mathematical/structural correctness, reproducibility, parameter provenance, calibration status, threshold basis, regulatory basis, and empirical-validation status of 100 analytical and portfolio modules against a literature-grounded supervisory specification. Individual modules are classified separately; implementation verification does not imply empirical validation or production suitability."

Begin.