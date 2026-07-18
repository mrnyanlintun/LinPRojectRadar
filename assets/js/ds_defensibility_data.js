// PCEIF Statistical Defensibility handbook content.
// Generated from PCEIF_Module_Defensibility_Registry_v3.json (103 module
// records, authoritative) with front-matter sections (Executive Findings,
// two-axis Defensibility Model, Standards Crosswalk, Priority Refactor
// Register) drawn from the v2 handbook docx. Em dashes stripped to hyphens.
// Capabilities are referenced by name; module ids and code-source strings
// from the registry are intentionally NOT emitted into this object.
const DS_DEFENSIBILITY = {
 "title": "Statistical Defensibility - A Data Science Perspective on PCEIF",
 "intro": "This handbook explains how every analytical capability in Lin Opus Gubernatio is designed, what uncertainty model it rests on, and how it is validated. It is organized by data science method, not by module number: readers meet the probabilistic reasoning first and the framework second. PCEIF (Probabilistic Capital-project Executive Intelligence Framework) fuses three signal types - EVM forecasting, statistical anomaly detection, and NLP document-signal extraction - into governed status verdicts through evidence fusion, with a human judgment layer recording every concurrence or override. The research artifact is evaluated under a Design Science Research methodology with qualitative validation from practicing professionals.",
 "oneSentence": "PCEIF does not dress business rules as statistics; it separates estimation, calibrated measurement, and evidence combination under epistemic uncertainty, and validates each by the standard appropriate to its tier.",
 "executiveFindings": [
  "The 103-row module registry is now present and code-aligned. Module names, method classes, required inputs, computation source, and current implementation status are no longer unspecified.",
  "The handbook uses two independent assurance axes: an uncertainty-method tier (statistical/stochastic; calibrated indicator; epistemic fusion) and an implementation-assurance class (A, B, or C). A respected method name does not validate an implementation that only approximates or renames it.",
  "Each module now includes the four missing defense fields: deterministic/probabilistic step split, explainability method, failure modes, and human-oversight classification.",
  "Standards alignment is added as a governance wrapper using NIST AI RMF, NIST TEVV, ISO/IEC 42001, ISO/IEC 23894, ISO/IEC 25059, W3C PROV-O, model cards, and datasheets. This crosswalk is not a certification claim.",
  "SHAP and LIME are not recommended by default. Most PCEIF modules are transparent formulas, rules, simulations, or symbolic uncertainty methods. For the very small portfolio suite, feature-standardization, distance/percentile traces, and leave-one-feature-out sensitivity are more fit for purpose.",
  "The code review identifies several label-to-algorithm mismatches that should be renamed or reimplemented before a formal defense. The highest-priority items include ARIMA, Earned Schedule, ICE, SRA P80, CRA P80, Critical Path Index, Queueing, ABM Supply Chain, DES, ABM Governance, regulatory compliance labels, Linear Programming, Pareto Frontier, and Isolation Forest."
 ],
 "defensibilityModel": {
  "intro": "A committee may use the word accredited informally, but individual algorithms are not accredited merely because they appear in a standard or paper. A defensible module requires a chain of evidence: method pedigree, code verification, parameter and data provenance, calibration, validation for the intended use, explainability, human oversight, and lifecycle monitoring. ISO/IEC 42001 can support certification of an organizational AI management system; it does not certify a TCPI formula, fuzzy membership function, or simulation result. NIST AI RMF is voluntary guidance and is currently being revised, so the handbook version-locks its crosswalk to AI RMF 1.0 and the associated Playbook snapshot.",
  "axisA": {
   "header": [
    "Tier",
    "Definition",
    "Uncertainty treatment",
    "Primary validation standard",
    "Typical modules"
   ],
   "tiers": [
    [
     "Tier 1",
     "Statistical or stochastic model",
     "Probability model, sampling distribution, process noise, posterior, residuals, or empirical anomaly score",
     "Convergence, residual/holdout diagnostics, false-alarm/detection design, reference-implementation comparison, simulation V&V",
     "Monte Carlo, CUSUM, Bayesian, Kalman, time-series, validated ML"
    ],
    [
     "Tier 2",
     "Deterministic or calibrated indicator",
     "Exact arithmetic plus input uncertainty, measurement error, missingness, and threshold calibration",
     "Formula/unit tests, boundary harness, provenance, calibration sets, robustness to data quality",
     "EVM ratios, schedule/cost indicators, document rates, compliance and data-quality flags"
    ],
    [
     "Tier 3",
     "Epistemic uncertainty or evidence fusion",
     "Belief masses, memberships, linguistic terms, abstention, conflict, rankings, or votes",
     "Axiom/equation verification, boundary/conflict tests, parameter sensitivity, stability analysis, practitioner face validation",
     "Dempster-Shafer, fuzzy families, rough sets, voting and synthesis"
    ]
   ]
  },
  "axisB": {
   "header": [
    "Class",
    "Meaning",
    "Permitted defense claim",
    "Required next step"
   ],
   "classes": [
    [
     "A",
     "Formula/rule-faithful and directly testable",
     "The code implements the documented formula or rule on synthetic inputs.",
     "Maintain tests; calibrate thresholds; validate with non-confidential cases before production use."
    ],
    [
     "B",
     "Method-shaped demonstration with explicit simplification",
     "The module illustrates the named method family under stated assumptions.",
     "Add calibration, sensitivity, benchmark comparison, and stronger operational validation."
    ],
    [
     "C",
     "Label-method mismatch, concept proxy, or unsupported compliance claim",
     "The current module is an exploratory proxy inspired by the named concept.",
     "Rename or implement the canonical method before making a formal method claim."
    ]
   ]
  }
 },
 "standardsCrosswalk": {
  "note": "This is an interpretive crosswalk for design and assurance. It is not a claim of certification or legal compliance.",
  "pairs": [
   [
    "NIST AI RMF 1.0",
    "Organizes risk work into GOVERN, MAP, MEASURE, and MANAGE."
   ],
   [
    "NIST TEVV",
    "Emphasizes context-specific test, evaluation, validation, and verification."
   ],
   [
    "ISO/IEC 42001",
    "Provides AI management-system requirements."
   ],
   [
    "ISO/IEC 23894",
    "Provides AI risk-management guidance."
   ],
   [
    "ISO/IEC 25059",
    "Provides AI-system quality characteristics."
   ],
   [
    "W3C PROV-O",
    "Supports interoperable provenance."
   ],
   [
    "Model cards",
    "Support transparent documentation of intended use, limitations, and evaluation."
   ],
   [
    "Datasheets",
    "Support transparent documentation of dataset lineage."
   ]
  ]
 },
 "refactorRegister": {
  "framing": "Class C does not mean the idea is useless. It means the current code and the current method label do not support the same scientific claim. These items should be renamed, reimplemented, or explicitly moved to future work before a formal defense.",
  "rows": [
   {
    "id_display": "1.6",
    "currentName": "ARIMA CPI Forecast",
    "finding": "The current code estimates one autoregressive coefficient on first differences. It is not a complete Box-Jenkins ARIMA identification, diagnostic, and forecast workflow. Rename it as an AR(1)-difference proxy or implement a full ARIMA model.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "1.7",
    "currentName": "Earned Schedule",
    "finding": "The current code computes actual-percent-complete divided by planned-percent-complete. That is a time-based progress ratio, not Lipke earned-schedule interpolation. Rename it as an SPI(t) proxy or implement the canonical earned-schedule algorithm.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "1.12",
    "currentName": "ICE Ratio",
    "finding": "Both compared EACs are derived from the same project inputs; the second estimate is not organizationally independent. Rename this as an EAC divergence ratio unless an independently produced estimate is ingested.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "2.2",
    "currentName": "Line of Balance",
    "finding": "The code uses fixed grading and paving rates adjusted by SPI. It does not ingest a project-specific repetitive-work Line-of-Balance dataset; defend it only as a production-flow proxy.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "2.3",
    "currentName": "CCPM Buffer Health",
    "finding": "Buffer consumption is inferred from SPI and percent complete rather than measured from a Critical Chain buffer. The current label overstates implementation fidelity.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "2.10",
    "currentName": "Schedule Risk Analysis P80",
    "finding": "The code applies an analytical uplift using 1.28 as a percentile factor; it does not sample an activity network. Rename as a P80-style schedule-risk proxy or implement true schedule risk simulation.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "2.11",
    "currentName": "Critical Path Index",
    "finding": "The code averages a progress ratio and SPI. It does not identify or analyze a CPM critical path. Rename before defense.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "3.7",
    "currentName": "Cost Risk Analysis P80",
    "finding": "The code calculates a deterministic EAC uplift and calls it P80. It is not a Monte Carlo cost-risk analysis. Rename or replace with sampled cost-element distributions and correlations.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "3.9",
    "currentName": "Parametric Cost Index",
    "finding": "The code compares two EAC formulas and does not fit a parametric regression or unit-cost model. The current name is not defensible as a parametric cost model.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "5.1",
    "currentName": "DSM Rework Propagation",
    "finding": "This category entry aliases the same DSM result used by Module 3.2. The duplication must be removed or the cost-oriented and system-oriented computations must be made materially different.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "5.5",
    "currentName": "Rework Feedback Loop",
    "finding": "The code forms a weighted index from CPI, RFI count, and change-order count. It does not implement stock-flow equations or a system-dynamics feedback simulation.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "5.6",
    "currentName": "Queueing Theory Bottleneck",
    "finding": "The code computes constrained activities divided by planned activities. It does not calculate queue utilization, waiting time, or an M/M/c model. Rename as a constraint-bottleneck ratio or implement queueing equations.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "5.7",
    "currentName": "Agent-Based Supply Chain",
    "finding": "The code computes the share of long-lead items at risk. There are no agents, interactions, state transitions, or emergent outcomes. Rename as a supply-risk ratio or implement an ABM.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "5.8",
    "currentName": "Discrete Event Simulation",
    "finding": "The code computes an algebraic throughput index from progress and SPI. There is no event calendar, entity queue, resource seizure, or sampled service time. Rename or implement a discrete-event model.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "7.9",
    "currentName": "Quantum Probability",
    "finding": "The code is a heuristic amplitude-interference demonstration. Unless the praxis specifically studies order effects and validates the parameterization against judgment data, remove or relegate it to future work.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "8.1",
    "currentName": "ABM Governance Layer",
    "finding": "The implementation is a deterministic authority and decision tree in decision.js. That is a strong explainable governance mechanism, but it is not an agent-based simulation. Rename as Governance Decision Rules.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "8.2",
    "currentName": "FAR Threshold Monitor",
    "finding": "The hard-coded FAR Part 34 and 25-percent overrun logic must not be presented as a legal compliance determination. Replace with a versioned, cited, configurable rule set reviewed by a contracting specialist.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "8.3",
    "currentName": "OMB A-11 Check",
    "finding": "A BAC/CPI trigger does not constitute an OMB Circular A-11 compliance assessment. Treat the current output as a demonstration flag only.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "8.4",
    "currentName": "EVM Reporting Threshold",
    "finding": "The module applies custom CPI/SPI bands. It is not an authoritative reporting threshold unless the governing agency requirement, effective date, and applicability are configured and cited.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "10.1",
    "currentName": "Multi-Objective Optimization",
    "finding": "The code averages three normalized scores. It does not optimize decision variables over multiple objectives or generate a Pareto set.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "10.2",
    "currentName": "Linear Programming",
    "finding": "The code is a TCPI-style feasibility check and does not formulate or solve a linear program with decision variables, objective coefficients, and constraints.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "10.3",
    "currentName": "Constraint Satisfaction Analysis",
    "finding": "The code counts satisfaction of four rules. It is an explainable constraint checklist, not a general constraint-satisfaction solver.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "10.4",
    "currentName": "What-If Scenario Matrix",
    "finding": "The code creates four deterministic EAC scenarios. It is a useful scenario table but not an optimization algorithm.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "10.5",
    "currentName": "Decision Sensitivity Matrix",
    "finding": "The code ranks current deviations; it does not perturb inputs and measure decision-boundary changes. Rename or implement true decision sensitivity.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "10.6",
    "currentName": "Pareto Frontier Analysis",
    "finding": "The code evaluates threshold booleans and does not construct a frontier of non-dominated alternatives. Rename or implement multi-alternative Pareto analysis.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "10.7",
    "currentName": "Regret Minimization Index",
    "finding": "The expected-regret table is mathematically inspectable, but state probabilities and regret values are hard-coded and signal overrides bypass the stated minimax result. Defend only as a toy decision-analysis demonstration.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   },
   {
    "id_display": "PH.1",
    "currentName": "Isolation Forest",
    "finding": "The backend computes a standardized distance from the portfolio centroid. It does not construct isolation trees and therefore is not an Isolation Forest implementation.",
    "disposition": "Rename to match the current calculation or implement the canonical method; keep only as illustrative until validated."
   }
  ]
 },
 "categories": [
  {
   "key": "category-1-cost-evm-forecasting",
   "num": "Category 1",
   "name": "Cost / EVM Forecasting",
   "count": 12,
   "modules": [
    {
     "name": "Monte Carlo EAC Forecast",
     "methodClass": "Monte Carlo",
     "defenseTier": "Tier 1 - Statistical / stochastic model",
     "asCodedTier": "Tier 1 - Statistical / stochastic model",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Samples CPI/SPI perturbations around reported values to produce an EAC distribution; the reported EAC is presented as a percentile within it, not a certainty.",
     "detProbSplit": "Deterministic input preparation and parameterization; stochastic or empirical sampling/scoring step; deterministic percentile, interval, ranking, and status-band interpretation.",
     "uncertaintyMethod": "Propagates input uncertainty by repeated sampling from assumed input distributions; output is an empirical distribution of the target quantity from which percentiles (P50/P80) and exceedance probabilities are read.",
     "explainability": "Distribution summary: input assumptions, seed, iteration count, O/M/P bounds, histogram, P50/P80, convergence and sensitivity traces.",
     "oversightLevel": "SIMULATE",
     "oversightDescription": "Simulate - supports scenario understanding only; it cannot authorize project or contractual action.",
     "failureModes": "Incorrect O/M/P assumptions; ignored correlation; too few iterations; heuristic spread mapping; seed mistaken for validation; stale CPI/SPI.",
     "assumptionsLimitations": "Input distributions and independence structure are assumed, not estimated from large samples; results are conditional on those assumptions. Convergence requires sufficient iterations (LLN).",
     "implementationFidelity": "The sampling engine is genuine seeded Beta-PERT Monte Carlo. The risk-spread mapping and optimistic/most-likely/pessimistic bounds are designed heuristics, so the result is reproducible demonstration evidence rather than a calibrated forecast.",
     "accreditationBasis": "Traceable to standard risk-analysis practice (AACE RP 41R-08 / NASA cost-risk guidance). Validated by convergence checks (stability of percentiles across iteration counts) and sensitivity of outputs to input-distribution choices.",
     "validationRequired": "Verify equations and code; test deterministic seeds; perform convergence or residual diagnostics; use seeded known-pattern cases; conduct sensitivity analysis; compare with a trusted reference implementation; document calibration and holdout performance where data permit.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP and MEASURE, with MANAGE for response; NIST TEVV for validity, reliability, uncertainty, benchmark, robustness, and monitoring evidence; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 25059 quality characteristics.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Monte Carlo EAC Forecast method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Why simulate when EAC = BAC/CPI is exact?",
       "answer": "The formula is exact given CPI, but CPI is a noisy period measurement. Simulation propagates that measurement uncertainty into a forecast interval - the same argument as reporting a CI rather than a point estimate."
      }
     ],
     "requiredInputs": [
      "bac",
      "cpi",
      "spi"
     ]
    },
    {
     "name": "CUSUM Anomaly Monitor",
     "methodClass": "CUSUM",
     "defenseTier": "Tier 1 - Statistical / stochastic model",
     "asCodedTier": "Tier 1 - Statistical / stochastic model",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Accumulates SPI deviations from target across project.history; breach = Red. Reads multi-period series, so it abstains on single-period projects.",
     "detProbSplit": "Deterministic preprocessing and CUSUM recursion over observations; uncertainty is represented by the stochastic-process assumption and false-alarm/detection design, not by random sampling in the code.",
     "uncertaintyMethod": "Treats the periodic performance index as a monitored process; cumulative deviations from a target are accumulated (CUSUM) so small persistent shifts trigger before any single period looks alarming. Detection threshold trades Type I error (false alarm) against Type II error (missed shift) - the course's error framework applied sequentially.",
     "explainability": "Sequential trace: target, sigma, allowance k, decision interval H, period-by-period positive/negative cumulative sums, and breach index.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Short or synthetic history; autocorrelation; non-comparable periods; poorly chosen sigma floor, k, or H; confusing a breach with causation.",
     "assumptionsLimitations": "Requires a multi-period history; assumes period observations are comparable and approximately independent after detrending; reference value k and decision interval h are design choices.",
     "implementationFidelity": "The two-sided tabular CUSUM recursion is method-faithful. When real history is absent, the application synthesizes a 12-period series; statistical detection claims are defensible only when actual comparable history is supplied.",
     "accreditationBasis": "CUSUM (Page 1954) is a canonical sequential test; parameters justified by Average Run Length reasoning. Validated on seeded histories with known injected shifts.",
     "validationRequired": "Verify equations and code; test deterministic seeds; perform convergence or residual diagnostics; use seeded known-pattern cases; conduct sensitivity analysis; compare with a trusted reference implementation; document calibration and holdout performance where data permit.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP and MEASURE, with MANAGE for response; NIST TEVV for validity, reliability, uncertainty, benchmark, robustness, and monitoring evidence; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 25059 quality characteristics.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the CUSUM Anomaly Monitor method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "What is your false-alarm rate?",
       "answer": "Set by the decision interval h via Average Run Length design: h chosen so in-control ARL is long relative to reporting cadence. The seeded-history tests demonstrate detection of injected 0.03-0.05 SPI shifts without alarming on stable series."
      }
     ],
     "requiredInputs": [
      "spi"
     ]
    },
    {
     "name": "Document Risk Extraction",
     "methodClass": "Doc Risk",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "The project-level ingestion of NLP-extracted raw signals feeding docRiskScore; the EVM-category instance of the Cat 4 pipeline.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "LLM extraction converts unstructured documents into structured fields; docRiskScore aggregates raw fact signals (dispute language, unresolved RFIs, NCR counts) into [0,1]. Extraction uncertainty is acknowledged: documents carry raw facts only (no pre-judged verdicts), and the Opus audit pass is an independent second-reader check.",
     "explainability": "Provenance trace: source document, extracted raw facts, excerpt/page reference, extraction confidence or audit result, scoring terms, and threshold path.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Extraction error; ambiguous or missing documents; duplicate counts; stale records; threshold drift; mistaking a risk flag for fault or contractual responsibility.",
     "assumptionsLimitations": "LLM extraction can err; mitigations are the raw-facts-only authoring rule, dual-model audit, and Cat 9 consistency checks. Bands (0.30/0.70) are calibrated decision thresholds.",
     "implementationFidelity": "The module is an AI-assisted measurement pipeline rather than a statistical estimator. Defensibility depends on extraction accuracy, provenance, dual-review results, and calibration of the risk-score bands.",
     "accreditationBasis": "Accredited procedurally: documented extraction prompts, audit protocol, and inter-model agreement rates on the synthetic corpus (a measurable reliability statistic professors can interrogate).",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN, MAP, and MEASURE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894: risk-information quality, monitoring, and review; W3C PROV-O for entity/activity/agent provenance; dataset documentation principles from datasheets.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Document Risk Extraction method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How do you know the LLM extracted correctly?",
       "answer": "Dual-model protocol: Sonnet extracts, Opus audits independently; disagreement rate on the synthetic corpus is the measured reliability statistic. Documents carry raw facts only, so the model cannot parrot a pre-judged verdict."
      }
     ],
     "requiredInputs": [
      "docRiskScore"
     ]
    },
    {
     "name": "Bayesian EAC",
     "methodClass": "Bayesian EAC",
     "defenseTier": "Tier 1 - Statistical / stochastic model",
     "asCodedTier": "Tier 1 - Statistical / stochastic model",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Prior = baseline BAC-implied performance; likelihood = observed period CPIs; posterior EAC tightens as periods accrue.",
     "detProbSplit": "Deterministic parameter update or forecast calculation inside an explicit probabilistic/statistical model; uncertainty is carried through prior/likelihood, process/measurement noise, residual variation, or shrinkage assumptions.",
     "uncertaintyMethod": "Combines a prior belief (baseline estimate) with observed performance evidence via Bayes' theorem; the posterior narrows as evidence accumulates, giving a probability-weighted forecast rather than a point value.",
     "explainability": "Posterior summary: prior, likelihood, assumed variances, precision weights, posterior mean, and prior-sensitivity comparison.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Prior dominance; arbitrary variance parameters; double-counted evidence; denominator approaching zero when CPI is near one.",
     "assumptionsLimitations": "Prior choice matters when data are sparse (early project periods); likelihood model assumes reported CPI/SPI are unbiased measurements of true performance.",
     "implementationFidelity": "The code uses a precision-weighted normal-normal update, but the prior and likelihood variances are designed rather than estimated. It is a Bayesian-form demonstration, not an empirically calibrated Bayesian forecast.",
     "accreditationBasis": "Bayesian EAC methods are established in EVM literature (e.g., Kim & Reinschmidt). Validated by comparing posterior forecasts against realized finals on seeded multi-period histories.",
     "validationRequired": "Verify equations and code; test deterministic seeds; perform convergence or residual diagnostics; use seeded known-pattern cases; conduct sensitivity analysis; compare with a trusted reference implementation; document calibration and holdout performance where data permit.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP and MEASURE, with MANAGE for response; NIST TEVV for validity, reliability, uncertainty, benchmark, robustness, and monitoring evidence; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 25059 quality characteristics.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Bayesian EAC method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How sensitive is it to the prior?",
       "answer": "Deliberately reported: early-period forecasts show prior dominance and wide intervals; by period 4-5 the likelihood dominates. That sensitivity is displayed, not hidden - the honest Bayesian answer."
      }
     ],
     "requiredInputs": [
      "bac",
      "ev",
      "ac",
      "cpi"
     ]
    },
    {
     "name": "Kalman Filter SPI Smoother",
     "methodClass": "Kalman Filter",
     "defenseTier": "Tier 1 - Statistical / stochastic model",
     "asCodedTier": "Tier 1 - Statistical / stochastic model",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "State = latent true SPI; observation = reported period SPI with noise variance R; filter output is smoothed SPI with variance.",
     "detProbSplit": "Deterministic parameter update or forecast calculation inside an explicit probabilistic/statistical model; uncertainty is carried through prior/likelihood, process/measurement noise, residual variation, or shrinkage assumptions.",
     "uncertaintyMethod": "Models the observed index series as signal plus noise; the filter/model separates persistent trend from period noise and yields a forecast with quantified uncertainty (state variance / prediction interval).",
     "explainability": "State-update trace: observations, Q/R settings, Kalman gain, updated state estimate, state variance, and residuals.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Uncalibrated Q/R; structural breaks; non-Gaussian observations; treating smoothing as causal explanation.",
     "assumptionsLimitations": "Kalman assumes linear-Gaussian state evolution; ARIMA assumes (weak) stationarity after differencing. Short series (<6 periods) yield wide, honest uncertainty - the module abstains rather than overstate confidence.",
     "implementationFidelity": "The scalar Kalman recursion is structurally correct; Q and R are fixed demonstration parameters. The filter should be calibrated from residuals before a production-quality claim.",
     "accreditationBasis": "Standard estimation theory (Kalman 1960; Box-Jenkins). Validated by one-step-ahead holdout error on seeded histories.",
     "validationRequired": "Verify equations and code; test deterministic seeds; perform convergence or residual diagnostics; use seeded known-pattern cases; conduct sensitivity analysis; compare with a trusted reference implementation; document calibration and holdout performance where data permit.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP and MEASURE, with MANAGE for response; NIST TEVV for validity, reliability, uncertainty, benchmark, robustness, and monitoring evidence; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 25059 quality characteristics.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Kalman Filter SPI Smoother method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Why Kalman over a moving average?",
       "answer": "A moving average has fixed lag and no uncertainty output. The Kalman gain adapts weighting to signal/noise ratio and yields a variance - needed downstream so fusion can weight this evidence by confidence."
      }
     ],
     "requiredInputs": [
      "spi",
      "spiHistory"
     ]
    },
    {
     "name": "ARIMA CPI Forecast",
     "methodClass": "ARIMA Forecast",
     "defenseTier": "Tier 1 - Statistical / stochastic model",
     "asCodedTier": "Tier 1 - Statistical / stochastic model",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Low-order ARIMA on cpiHistory; abstains below minimum series length rather than fitting to 3 points.",
     "detProbSplit": "Deterministic parameter update or forecast calculation inside an explicit probabilistic/statistical model; uncertainty is carried through prior/likelihood, process/measurement noise, residual variation, or shrinkage assumptions.",
     "uncertaintyMethod": "Models the observed index series as signal plus noise; the filter/model separates persistent trend from period noise and yields a forecast with quantified uncertainty (state variance / prediction interval).",
     "explainability": "Time-series trace: differenced observations, estimated phi, last innovation, forecast, residual diagnostics, and explicit statement that the current code is an AR(1)-difference proxy.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Insufficient history; nonstationarity; no model-order selection; no residual diagnostics; method-name mismatch.",
     "assumptionsLimitations": "Kalman assumes linear-Gaussian state evolution; ARIMA assumes (weak) stationarity after differencing. Short series (<6 periods) yield wide, honest uncertainty - the module abstains rather than overstate confidence.",
     "implementationFidelity": "The current code estimates one autoregressive coefficient on first differences. It is not a complete Box-Jenkins ARIMA identification, diagnostic, and forecast workflow. Rename it as an AR(1)-difference proxy or implement a full ARIMA model.",
     "accreditationBasis": "Standard estimation theory (Kalman 1960; Box-Jenkins). Validated by one-step-ahead holdout error on seeded histories.",
     "validationRequired": "Verify equations and code; test deterministic seeds; perform convergence or residual diagnostics; use seeded known-pattern cases; conduct sensitivity analysis; compare with a trusted reference implementation; document calibration and holdout performance where data permit.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP and MEASURE, with MANAGE for response; NIST TEVV for validity, reliability, uncertainty, benchmark, robustness, and monitoring evidence; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 25059 quality characteristics.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by ARIMA CPI Forecast.\" Prohibited: \"The code implements the canonical ARIMA CPI Forecast method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Is stationarity plausible for CPI?",
       "answer": "CPI is bounded and mean-reverting in stable execution, so differencing-to-stationarity is defensible; the module's abstention rule prevents fitting where the assumption can't be checked."
      }
     ],
     "requiredInputs": [
      "cpiHistory"
     ]
    },
    {
     "name": "Earned Schedule",
     "methodClass": "Earned Schedule",
     "defenseTier": "Tier 1 - Statistical / stochastic model",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Converts SV from dollars to time (ES = time at which PV equaled current EV); Green at >=0.95. Corrects the known end-of-project SPI($) distortion.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Models the observed index series as signal plus noise; the filter/model separates persistent trend from period noise and yields a forecast with quantified uncertainty (state variance / prediction interval).",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Method-name mismatch; inconsistent percent-complete bases; inaccurate baseline dates; percent-complete subjectivity.",
     "assumptionsLimitations": "Kalman assumes linear-Gaussian state evolution; ARIMA assumes (weak) stationarity after differencing. Short series (<6 periods) yield wide, honest uncertainty - the module abstains rather than overstate confidence.",
     "implementationFidelity": "The current code computes actual-percent-complete divided by planned-percent-complete. That is a time-based progress ratio, not Lipke earned-schedule interpolation. Rename it as an SPI(t) proxy or implement the canonical earned-schedule algorithm.",
     "accreditationBasis": "Standard estimation theory (Kalman 1960; Box-Jenkins). Validated by one-step-ahead holdout error on seeded histories.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by Earned Schedule.\" Prohibited: \"The code implements the canonical Earned Schedule method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Why add ES if you have SPI?",
       "answer": "SPI($) converges to 1.0 at completion regardless of lateness - a documented bias. ES(t) is the literature's correction (Lipke 2003); including both shows awareness of estimator bias, a course-central concept."
      }
     ],
     "requiredInputs": [
      "ev",
      "pv",
      "bac",
      "actualPctComplete",
      "plannedPctComplete"
     ]
    },
    {
     "name": "TCPI",
     "methodClass": "TCPI",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "TCPI = (BAC-EV)/(BAC-AC); bands 1.05/1.10/1.20. Measures required future efficiency.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "A ratio computed exactly from reported figures (no sampling error in the arithmetic). Uncertainty enters through the inputs (measurement/reporting error in EV, AC, PV) and is handled at the governance layer: 4-tier bands act as control limits - decision thresholds calibrated to industry evidence, not p-values.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Assumes the underlying document figures are accurate; PCEIF explicitly compensates via Data Integrity (Cat 9) modules that score input quality, and via DST fusion that lets weak evidence abstain.",
     "implementationFidelity": "The TCPI formula is directly implemented and banded. The formula is defensible; the status bands require cited policy or calibration evidence.",
     "accreditationBasis": "Ratios and thresholds trace to DoD EVMIG / PMI Practice Standard for EVM; the 0.95/0.92/0.88 bands align with published EVM variance-tolerance conventions. Validated by the tests.html band harness (~30 edge cases from code constants) and calibrated synthetic document sets that hit each target band.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented TCPI formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Is a TCPI of 1.074 'statistically' Yellow?",
       "answer": "No test is claimed. 1.05/1.10/1.20 are decision thresholds from EVM practice (DoD guidance treats TCPI>1.10 as rarely recoverable). The band is a calibrated control limit, and the harness proves the code honors it."
      },
      {
       "question": "Professors will ask: 'Where is the statistical test?'",
       "answer": "There is none and none is claimed. This is a calibrated control-limit indicator in the SPC tradition: the arithmetic is exact, uncertainty lives in the inputs, and the band edges are decision thresholds with cited practice provenance, verified by the band harness. Pretending otherwise would be the indefensible position."
      }
     ],
     "requiredInputs": [
      "bac",
      "ev",
      "ac"
     ]
    },
    {
     "name": "Variance at Completion",
     "methodClass": "VAC",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "VAC = BAC - EAC, banded relative to BAC.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "A ratio computed exactly from reported figures (no sampling error in the arithmetic). Uncertainty enters through the inputs (measurement/reporting error in EV, AC, PV) and is handled at the governance layer: 4-tier bands act as control limits - decision thresholds calibrated to industry evidence, not p-values.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Assumes the underlying document figures are accurate; PCEIF explicitly compensates via Data Integrity (Cat 9) modules that score input quality, and via DST fusion that lets weak evidence abstain.",
     "implementationFidelity": "VAC is calculated from BAC minus BAC/CPI. The arithmetic is transparent; the forecast quality inherits all assumptions of the selected EAC formula.",
     "accreditationBasis": "Ratios and thresholds trace to DoD EVMIG / PMI Practice Standard for EVM; the 0.95/0.92/0.88 bands align with published EVM variance-tolerance conventions. Validated by the tests.html band harness (~30 edge cases from code constants) and calibrated synthetic document sets that hit each target band.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Variance at Completion formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Where does uncertainty appear?",
       "answer": "Through EAC: when the Monte Carlo EAC distribution is used, VAC inherits an interval; the deterministic VAC is its central value."
      },
      {
       "question": "Professors will ask: 'Where is the statistical test?'",
       "answer": "There is none and none is claimed. This is a calibrated control-limit indicator in the SPC tradition: the arithmetic is exact, uncertainty lives in the inputs, and the band edges are decision thresholds with cited practice provenance, verified by the band harness. Pretending otherwise would be the indefensible position."
      }
     ],
     "requiredInputs": [
      "bac",
      "cpi"
     ]
    },
    {
     "name": "Budget Execution Rate",
     "methodClass": "Budget Execution Rate",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "AC burn vs time elapsed; flags under/over-execution against plan corridor 0.90-1.10.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "A ratio computed exactly from reported figures (no sampling error in the arithmetic). Uncertainty enters through the inputs (measurement/reporting error in EV, AC, PV) and is handled at the governance layer: 4-tier bands act as control limits - decision thresholds calibrated to industry evidence, not p-values.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Assumes the underlying document figures are accurate; PCEIF explicitly compensates via Data Integrity (Cat 9) modules that score input quality, and via DST fusion that lets weak evidence abstain.",
     "implementationFidelity": "The code compares actual expenditure with a progress-proportional expected spend. It is a transparent custom control ratio, not a standardized statistical test.",
     "accreditationBasis": "Ratios and thresholds trace to DoD EVMIG / PMI Practice Standard for EVM; the 0.95/0.92/0.88 bands align with published EVM variance-tolerance conventions. Validated by the tests.html band harness (~30 edge cases from code constants) and calibrated synthetic document sets that hit each target band.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Budget Execution Rate method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Why is under-spend flagged?",
       "answer": "Under-execution predicts back-loaded risk; the symmetric corridor encodes that both tails are anomalous - same logic as a two-sided test region in W4-W5."
      },
      {
       "question": "Professors will ask: 'Where is the statistical test?'",
       "answer": "There is none and none is claimed. This is a calibrated control-limit indicator in the SPC tradition: the arithmetic is exact, uncertainty lives in the inputs, and the band edges are decision thresholds with cited practice provenance, verified by the band harness. Pretending otherwise would be the indefensible position."
      }
     ],
     "requiredInputs": [
      "ac",
      "bac",
      "actualPctComplete"
     ]
    },
    {
     "name": "Regression to Mean CPI",
     "methodClass": "Regression To Mean",
     "defenseTier": "Tier 1 - Statistical / stochastic model",
     "asCodedTier": "Tier 1 - Statistical / stochastic model",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Projects future CPI as weighted pull toward portfolio/historical mean; needs cpiHistory.",
     "detProbSplit": "Deterministic parameter update or forecast calculation inside an explicit probabilistic/statistical model; uncertainty is carried through prior/likelihood, process/measurement noise, residual variation, or shrinkage assumptions.",
     "uncertaintyMethod": "Models the observed index series as signal plus noise; the filter/model separates persistent trend from period noise and yields a forecast with quantified uncertainty (state variance / prediction interval).",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Kalman assumes linear-Gaussian state evolution; ARIMA assumes (weak) stationarity after differencing. Short series (<6 periods) yield wide, honest uncertainty - the module abstains rather than overstate confidence.",
     "implementationFidelity": "The code applies a fixed 50-percent shrinkage toward the observed historical mean. The regression-to-mean concept is valid, but the shrinkage coefficient is not estimated.",
     "accreditationBasis": "Standard estimation theory (Kalman 1960; Box-Jenkins). Validated by one-step-ahead holdout error on seeded histories.",
     "validationRequired": "Verify equations and code; test deterministic seeds; perform convergence or residual diagnostics; use seeded known-pattern cases; conduct sensitivity analysis; compare with a trusted reference implementation; document calibration and holdout performance where data permit.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP and MEASURE, with MANAGE for response; NIST TEVV for validity, reliability, uncertainty, benchmark, robustness, and monitoring evidence; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 25059 quality characteristics.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Regression to Mean CPI method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Isn't this just shrinkage?",
       "answer": "Yes - deliberately. Early extreme CPIs are partly noise; shrinkage estimators reduce MSE (Stein-type argument). The module names the phenomenon professors already teach: extreme observations regress."
      }
     ],
     "requiredInputs": [
      "cpi",
      "cpiHistory"
     ]
    },
    {
     "name": "ICE Ratio",
     "methodClass": "ICE Ratio",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Independent Cost Estimate ratio vs current EAC; divergence banded.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "A ratio computed exactly from reported figures (no sampling error in the arithmetic). Uncertainty enters through the inputs (measurement/reporting error in EV, AC, PV) and is handled at the governance layer: 4-tier bands act as control limits - decision thresholds calibrated to industry evidence, not p-values.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Assumes the underlying document figures are accurate; PCEIF explicitly compensates via Data Integrity (Cat 9) modules that score input quality, and via DST fusion that lets weak evidence abstain.",
     "implementationFidelity": "Both compared EACs are derived from the same project inputs; the second estimate is not organizationally independent. Rename this as an EAC divergence ratio unless an independently produced estimate is ingested.",
     "accreditationBasis": "Ratios and thresholds trace to DoD EVMIG / PMI Practice Standard for EVM; the 0.95/0.92/0.88 bands align with published EVM variance-tolerance conventions. Validated by the tests.html band harness (~30 edge cases from code constants) and calibrated synthetic document sets that hit each target band.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by ICE Ratio.\" Prohibited: \"The code implements the canonical ICE Ratio method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "What makes the ICE independent?",
       "answer": "Sourced from a different document (independent estimate doc) than the EAC chain; the module is a cross-validation check between two estimators - disagreement is evidence, agreement is corroboration in the DST sense."
      },
      {
       "question": "Professors will ask: 'Where is the statistical test?'",
       "answer": "There is none and none is claimed. This is a calibrated control-limit indicator in the SPC tradition: the arithmetic is exact, uncertainty lives in the inputs, and the band edges are decision thresholds with cited practice provenance, verified by the band harness. Pretending otherwise would be the indefensible position."
      }
     ],
     "requiredInputs": [
      "bac",
      "cpi",
      "ev",
      "ac"
     ]
    }
   ]
  },
  {
   "key": "category-2-schedule-analytics",
   "num": "Category 2",
   "name": "Schedule Analytics",
   "count": 11,
   "modules": [
    {
     "name": "PERT Network Criticality",
     "methodClass": "PERT Network Criticality",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Beta/PERT three-point durations ((O+4M+P)/6, variance ((P-O)/6)^2); path criticality from mean/variance of path sums.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Computed from schedule data (network, float, milestones); stochastic where noted (SRA P80 is Monte Carlo over activity durations). Bands encode planning-tolerance conventions as control limits.",
     "explainability": "Distribution summary: input assumptions, seed, iteration count, O/M/P bounds, histogram, P50/P80, convergence and sensitivity traces.",
     "oversightLevel": "SIMULATE",
     "oversightDescription": "Simulate - supports scenario understanding only; it cannot authorize project or contractual action.",
     "failureModes": "Hard-coded network; omitted correlation; wrong duration distributions; unstable criticality with too few runs.",
     "assumptionsLimitations": "Network logic and reported percent-complete are taken as ground truth; MTA slip bands (0/7/14 days, worst>21 override) are governance conventions, not estimated quantities.",
     "implementationFidelity": "The code performs Monte Carlo sampling on a fixed three-activity network with triangular durations. The stochastic core is real, but the topology and duration parameters are illustrative and must be replaced by project data for operational use.",
     "accreditationBasis": "PERT/CPM and SRA are standard (PMI SP for Scheduling; GAO Schedule Assessment Guide). Band edges validated in the band harness; SRA validated by convergence checks.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the PERT Network Criticality method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Why Beta-PERT?",
       "answer": "It is the canonical elicitation distribution for expert three-point estimates; the course's expectation/variance machinery applies directly, and the CLT justifies treating path sums as approximately normal."
      }
     ],
     "requiredInputs": [
      "spi",
      "bac"
     ]
    },
    {
     "name": "Line of Balance",
     "methodClass": "Line of Balance Velocity",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Production-rate consistency across repetitive units; slope deviation banded.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Computed from schedule data (network, float, milestones); stochastic where noted (SRA P80 is Monte Carlo over activity durations). Bands encode planning-tolerance conventions as control limits.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Network logic and reported percent-complete are taken as ground truth; MTA slip bands (0/7/14 days, worst>21 override) are governance conventions, not estimated quantities.",
     "implementationFidelity": "The code uses fixed grading and paving rates adjusted by SPI. It does not ingest a project-specific repetitive-work Line-of-Balance dataset; defend it only as a production-flow proxy.",
     "accreditationBasis": "PERT/CPM and SRA are standard (PMI SP for Scheduling; GAO Schedule Assessment Guide). Band edges validated in the band harness; SRA validated by convergence checks.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by Line of Balance.\" Prohibited: \"The code implements the canonical Line of Balance method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Statistical content?",
       "answer": "None claimed - it is a deterministic production analytic; its band is a planning tolerance. Tier-2 honesty: not every governance signal is an estimator."
      }
     ],
     "requiredInputs": [
      "spi",
      "actualPctComplete",
      "plannedPctComplete"
     ]
    },
    {
     "name": "CCPM Buffer Health",
     "methodClass": "CCPM Buffer Health",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Buffer consumption vs chain completion; fever-chart zones are the bands.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Computed from schedule data (network, float, milestones); stochastic where noted (SRA P80 is Monte Carlo over activity durations). Bands encode planning-tolerance conventions as control limits.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Network logic and reported percent-complete are taken as ground truth; MTA slip bands (0/7/14 days, worst>21 override) are governance conventions, not estimated quantities.",
     "implementationFidelity": "Buffer consumption is inferred from SPI and percent complete rather than measured from a Critical Chain buffer. The current label overstates implementation fidelity.",
     "accreditationBasis": "PERT/CPM and SRA are standard (PMI SP for Scheduling; GAO Schedule Assessment Guide). Band edges validated in the band harness; SRA validated by convergence checks.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by CCPM Buffer Health.\" Prohibited: \"The code implements the canonical CCPM Buffer Health method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Aren't fever zones arbitrary?",
       "answer": "They are published CCPM conventions (Goldratt); PCEIF cites them as adopted practice standards, and the zone edges are covered by the band harness."
      }
     ],
     "requiredInputs": [
      "actualPctComplete",
      "plannedPctComplete"
     ]
    },
    {
     "name": "Schedule Compression Index",
     "methodClass": "Schedule Compression",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Remaining work vs remaining duration relative to plan.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Computed from schedule data (network, float, milestones); stochastic where noted (SRA P80 is Monte Carlo over activity durations). Bands encode planning-tolerance conventions as control limits.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Network logic and reported percent-complete are taken as ground truth; MTA slip bands (0/7/14 days, worst>21 override) are governance conventions, not estimated quantities.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "PERT/CPM and SRA are standard (PMI SP for Scheduling; GAO Schedule Assessment Guide). Band edges validated in the band harness; SRA validated by convergence checks.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Schedule Compression Index method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Uncertainty handling?",
       "answer": "Input uncertainty only; feeds fusion as one bounded vote, never a standalone verdict."
      }
     ],
     "requiredInputs": [
      "baselineEnd",
      "baselineStart",
      "actualPctComplete"
     ]
    },
    {
     "name": "Float Consumption Rate",
     "methodClass": "Float Consumption",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Total float burn per period vs linear allowance.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Computed from schedule data (network, float, milestones); stochastic where noted (SRA P80 is Monte Carlo over activity durations). Bands encode planning-tolerance conventions as control limits.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Network logic and reported percent-complete are taken as ground truth; MTA slip bands (0/7/14 days, worst>21 override) are governance conventions, not estimated quantities.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "PERT/CPM and SRA are standard (PMI SP for Scheduling; GAO Schedule Assessment Guide). Band edges validated in the band harness; SRA validated by convergence checks.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Float Consumption Rate formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Why linear allowance?",
       "answer": "A neutral null model: consuming float faster than uniformly is early warning. Analogous to testing observed slope against a null slope."
      }
     ],
     "requiredInputs": [
      "totalFloat",
      "consumedFloat"
     ]
    },
    {
     "name": "S-Curve Deviation",
     "methodClass": "SCurve Deviation",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Actual vs planned cumulative progress; requires planned% <= actual% authoring discipline (the known SPI trap).",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Computed from schedule data (network, float, milestones); stochastic where noted (SRA P80 is Monte Carlo over activity durations). Bands encode planning-tolerance conventions as control limits.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Network logic and reported percent-complete are taken as ground truth; MTA slip bands (0/7/14 days, worst>21 override) are governance conventions, not estimated quantities.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "PERT/CPM and SRA are standard (PMI SP for Scheduling; GAO Schedule Assessment Guide). Band edges validated in the band harness; SRA validated by convergence checks.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented S-Curve Deviation formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Known failure mode?",
       "answer": "Yes - if synthetic docs state planned%>actual%, SPI recomputes below 1 and cascades. Documented as an input-integrity constraint, itself an example of why Cat 9 exists."
      }
     ],
     "requiredInputs": [
      "actualPctComplete",
      "plannedPctComplete",
      "ev",
      "pv"
     ]
    },
    {
     "name": "Milestone Trend Analysis",
     "methodClass": "Milestone Trend",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Slip in days per milestone across periods; bands 0/7/14, worst-slip>21 override.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Computed from schedule data (network, float, milestones); stochastic where noted (SRA P80 is Monte Carlo over activity durations). Bands encode planning-tolerance conventions as control limits.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Network logic and reported percent-complete are taken as ground truth; MTA slip bands (0/7/14 days, worst>21 override) are governance conventions, not estimated quantities.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "PERT/CPM and SRA are standard (PMI SP for Scheduling; GAO Schedule Assessment Guide). Band edges validated in the band harness; SRA validated by convergence checks.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Milestone Trend Analysis formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Why an override?",
       "answer": "A single catastrophic milestone should not be averaged away - a max-statistic guard against masking, the same reason worst-status-wins governs categories."
      }
     ],
     "requiredInputs": [
      "milestoneHistory"
     ]
    },
    {
     "name": "Look-Ahead Schedule Health",
     "methodClass": "Lookahead Health",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Near-horizon activity readiness ratio.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Computed from schedule data (network, float, milestones); stochastic where noted (SRA P80 is Monte Carlo over activity durations). Bands encode planning-tolerance conventions as control limits.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Network logic and reported percent-complete are taken as ground truth; MTA slip bands (0/7/14 days, worst>21 override) are governance conventions, not estimated quantities.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "PERT/CPM and SRA are standard (PMI SP for Scheduling; GAO Schedule Assessment Guide). Band edges validated in the band harness; SRA validated by convergence checks.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Look-Ahead Schedule Health formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Evidence value?",
       "answer": "Leading indicator with short horizon; weighted accordingly in fusion - low mass, early signal."
      }
     ],
     "requiredInputs": [
      "activitiesPlanned",
      "activitiesConstrained"
     ]
    },
    {
     "name": "Resource Loading Index",
     "methodClass": "Resource Loading",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Planned vs available resource profile ratio, corridor 0.90-1.10.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Computed from schedule data (network, float, milestones); stochastic where noted (SRA P80 is Monte Carlo over activity durations). Bands encode planning-tolerance conventions as control limits.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Network logic and reported percent-complete are taken as ground truth; MTA slip bands (0/7/14 days, worst>21 override) are governance conventions, not estimated quantities.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "PERT/CPM and SRA are standard (PMI SP for Scheduling; GAO Schedule Assessment Guide). Band edges validated in the band harness; SRA validated by convergence checks.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Resource Loading Index formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Two-sided again?",
       "answer": "Yes - overload predicts burnout/quality loss, underload predicts drift; symmetric corridor mirrors a two-sided rejection region."
      }
     ],
     "requiredInputs": [
      "plannedLaborHours",
      "actualLaborHours"
     ]
    },
    {
     "name": "Schedule Risk Analysis P80",
     "methodClass": "Schedule Risk Analysis",
     "defenseTier": "Tier 1 - Statistical / stochastic model",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Monte Carlo over activity-duration distributions; reports P80 completion vs contractual date.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Propagates input uncertainty by repeated sampling from assumed input distributions; output is an empirical distribution of the target quantity from which percentiles (P50/P80) and exceedance probabilities are read.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "SIMULATE",
     "oversightDescription": "Simulate - supports scenario understanding only; it cannot authorize project or contractual action.",
     "failureModes": "Percentile label without simulation; invalid 1.28 multiplier assumption; schedule logic omitted.",
     "assumptionsLimitations": "Input distributions and independence structure are assumed, not estimated from large samples; results are conditional on those assumptions. Convergence requires sufficient iterations (LLN).",
     "implementationFidelity": "The code applies an analytical uplift using 1.28 as a percentile factor; it does not sample an activity network. Rename as a P80-style schedule-risk proxy or implement true schedule risk simulation.",
     "accreditationBasis": "Traceable to standard risk-analysis practice (AACE RP 41R-08 / NASA cost-risk guidance). Validated by convergence checks (stability of percentiles across iteration counts) and sensitivity of outputs to input-distribution choices.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by Schedule Risk Analysis P80.\" Prohibited: \"The code implements the canonical Schedule Risk Analysis P80 method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Why P80 not P50?",
       "answer": "P50 is even odds; governance convention (GAO/DoD) funds to ~P70-P80 to control schedule overrun probability. The percentile choice is a risk-appetite policy, stated as such."
      }
     ],
     "requiredInputs": [
      "spi",
      "baselineEnd",
      "baselineStart",
      "actualPctComplete"
     ]
    },
    {
     "name": "Critical Path Index",
     "methodClass": "Critical Path Index",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "CPLI-style ratio of critical-path performance; Green >=0.95 with EVM bands.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "A ratio computed exactly from reported figures (no sampling error in the arithmetic). Uncertainty enters through the inputs (measurement/reporting error in EV, AC, PV) and is handled at the governance layer: 4-tier bands act as control limits - decision thresholds calibrated to industry evidence, not p-values.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Assumes the underlying document figures are accurate; PCEIF explicitly compensates via Data Integrity (Cat 9) modules that score input quality, and via DST fusion that lets weak evidence abstain.",
     "implementationFidelity": "The code averages a progress ratio and SPI. It does not identify or analyze a CPM critical path. Rename before defense.",
     "accreditationBasis": "Ratios and thresholds trace to DoD EVMIG / PMI Practice Standard for EVM; the 0.95/0.92/0.88 bands align with published EVM variance-tolerance conventions. Validated by the tests.html band harness (~30 edge cases from code constants) and calibrated synthetic document sets that hit each target band.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by Critical Path Index.\" Prohibited: \"The code implements the canonical Critical Path Index method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Shares inputs with SPI - double counting?",
       "answer": "Acknowledged correlation; fusion's design (abstention, Red-weighting, dominance at project level) limits the effect, and the limitation is stated in the praxis Limitations topic."
      },
      {
       "question": "Professors will ask: 'Where is the statistical test?'",
       "answer": "There is none and none is claimed. This is a calibrated control-limit indicator in the SPC tradition: the arithmetic is exact, uncertainty lives in the inputs, and the band edges are decision thresholds with cited practice provenance, verified by the band harness. Pretending otherwise would be the indefensible position."
      }
     ],
     "requiredInputs": [
      "spi",
      "plannedPctComplete",
      "actualPctComplete"
     ]
    }
   ]
  },
  {
   "key": "category-3-cost-risk",
   "num": "Category 3",
   "name": "Cost Risk",
   "count": 10,
   "modules": [
    {
     "name": "Reference Class Forecasting",
     "methodClass": "Reference Class Forecasting",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 1 - Statistical / stochastic model",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Positions the project against an outside-view distribution of comparable projects (Flyvbjerg); output is a percentile placement.",
     "detProbSplit": "Deterministic input preparation and parameterization; stochastic or empirical sampling/scoring step; deterministic percentile, interval, ranking, and status-band interpretation.",
     "uncertaintyMethod": "Represents epistemic uncertainty (vague, conflicting, or partially trusted evidence) that classical probability handles poorly: membership degrees, belief/plausibility intervals, or hesitancy terms instead of a single probability mass. Output is a graded status assessment carrying its own confidence.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Membership functions / mass assignments are elicited design choices; the defense is comparative (do rankings remain stable across reasonable parameterizations - a sensitivity argument), not inferential.",
     "implementationFidelity": "The outside-view idea is sound, but the multiplier set is hard-coded. The reference class, selection criteria, data source, and update date must be documented.",
     "accreditationBasis": "Each formalism is peer-reviewed decision-science literature with citable primary sources. Accreditation in PCEIF = published axioms + documented parameterization + sensitivity/stability checks, plus practitioner face-validation interviews.",
     "validationRequired": "Verify equations and code; test deterministic seeds; perform convergence or residual diagnostics; use seeded known-pattern cases; conduct sensitivity analysis; compare with a trusted reference implementation; document calibration and holdout performance where data permit.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP and MEASURE, with MANAGE for response; NIST TEVV for validity, reliability, uncertainty, benchmark, robustness, and monitoring evidence; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 25059 quality characteristics.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Reference Class Forecasting method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Where is your reference class data?",
       "answer": "Seeded from published overrun distributions for the sector; stated as an outside-view prior, exactly Kahneman/Flyvbjerg's accredited method for optimism-bias correction."
      },
      {
       "question": "How is a non-probabilistic formalism 'validated'?",
       "answer": "By the accreditation triad used throughout Cat 7: (1) primary peer-reviewed citation for the axioms, (2) documented parameterization with provenance, (3) sensitivity/stability analysis showing fused verdicts are robust to reasonable parameter variation, plus practitioner face validation. This is the accepted standard for decision-science formalisms, where frequentist error rates are category errors."
      }
     ],
     "requiredInputs": [
      "bac",
      "cpi"
     ]
    },
    {
     "name": "DSM Rework Propagation",
     "methodClass": "DSM Rework Propagation",
     "defenseTier": "Tier 1 - Statistical / stochastic model",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Design Structure Matrix rework loops; propagates rework probability through dependency cycles. (Note: verify distinct computation vs 5.1 or dedupe - open praxis punch-list item.)",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Mechanistic stochastic models of project workflows: arrival/service processes (queueing), entity flows (DES), interacting agents (ABM), feedback loops (rework). Outputs are distributions of throughput/delay under sampled randomness.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Arrival/service distributions parameterized from document-extracted rates; structural validity (does the model topology match the real workflow) argued via practitioner interviews, not statistics.",
     "implementationFidelity": "The code propagates a change through a fixed 3x3 dependency matrix for four passes. It is a deterministic DSM demonstration, not a stochastic rework model.",
     "accreditationBasis": "Poisson/queueing theory is canonical (M/M/1 assumptions stated); ABM/DES validated by face validation + extreme-condition tests (Sargent's simulation V&V framework - the citable accreditation standard for simulation models).",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the DSM Rework Propagation method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Duplicate of 5.1?",
       "answer": "Flagged: the draft lists it at 3.2 and 5.1. Either the computations differ (cost-weighted vs flow-weighted propagation) and that must be documented, or one is removed. This is on the discrepancy punch-list - do not defend it as-is."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi"
     ]
    },
    {
     "name": "Contingency Burn Rate",
     "methodClass": "Contingency Burn Rate",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Contingency drawdown vs risk-retirement schedule.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "A ratio computed exactly from reported figures (no sampling error in the arithmetic). Uncertainty enters through the inputs (measurement/reporting error in EV, AC, PV) and is handled at the governance layer: 4-tier bands act as control limits - decision thresholds calibrated to industry evidence, not p-values.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Assumes the underlying document figures are accurate; PCEIF explicitly compensates via Data Integrity (Cat 9) modules that score input quality, and via DST fusion that lets weak evidence abstain.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Ratios and thresholds trace to DoD EVMIG / PMI Practice Standard for EVM; the 0.95/0.92/0.88 bands align with published EVM variance-tolerance conventions. Validated by the tests.html band harness (~30 edge cases from code constants) and calibrated synthetic document sets that hit each target band.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Contingency Burn Rate formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Null model?",
       "answer": "Linear or risk-register-phased drawdown; faster burn than retired risk is the flag condition."
      },
      {
       "question": "Professors will ask: 'Where is the statistical test?'",
       "answer": "There is none and none is claimed. This is a calibrated control-limit indicator in the SPC tradition: the arithmetic is exact, uncertainty lives in the inputs, and the band edges are decision thresholds with cited practice provenance, verified by the band harness. Pretending otherwise would be the indefensible position."
      }
     ],
     "requiredInputs": [
      "originalContingency",
      "remainingContingency",
      "actualPctComplete"
     ]
    },
    {
     "name": "Labor Productivity Index",
     "methodClass": "Labor Productivity",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Earned hours / actual hours, EVM-style bands.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "A ratio computed exactly from reported figures (no sampling error in the arithmetic). Uncertainty enters through the inputs (measurement/reporting error in EV, AC, PV) and is handled at the governance layer: 4-tier bands act as control limits - decision thresholds calibrated to industry evidence, not p-values.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Assumes the underlying document figures are accurate; PCEIF explicitly compensates via Data Integrity (Cat 9) modules that score input quality, and via DST fusion that lets weak evidence abstain.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Ratios and thresholds trace to DoD EVMIG / PMI Practice Standard for EVM; the 0.95/0.92/0.88 bands align with published EVM variance-tolerance conventions. Validated by the tests.html band harness (~30 edge cases from code constants) and calibrated synthetic document sets that hit each target band.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Labor Productivity Index formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Measurement error?",
       "answer": "Timesheet-derived; Cat 9 timeliness/consistency scores down-weight stale inputs in fusion."
      },
      {
       "question": "Professors will ask: 'Where is the statistical test?'",
       "answer": "There is none and none is claimed. This is a calibrated control-limit indicator in the SPC tradition: the arithmetic is exact, uncertainty lives in the inputs, and the band edges are decision thresholds with cited practice provenance, verified by the band harness. Pretending otherwise would be the indefensible position."
      }
     ],
     "requiredInputs": [
      "plannedLaborHours",
      "actualLaborHours",
      "actualPctComplete"
     ]
    },
    {
     "name": "Material Cost Variance",
     "methodClass": "Material Cost Variance",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Committed+actual material vs budget line, banded.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "A ratio computed exactly from reported figures (no sampling error in the arithmetic). Uncertainty enters through the inputs (measurement/reporting error in EV, AC, PV) and is handled at the governance layer: 4-tier bands act as control limits - decision thresholds calibrated to industry evidence, not p-values.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Assumes the underlying document figures are accurate; PCEIF explicitly compensates via Data Integrity (Cat 9) modules that score input quality, and via DST fusion that lets weak evidence abstain.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Ratios and thresholds trace to DoD EVMIG / PMI Practice Standard for EVM; the 0.95/0.92/0.88 bands align with published EVM variance-tolerance conventions. Validated by the tests.html band harness (~30 edge cases from code constants) and calibrated synthetic document sets that hit each target band.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Material Cost Variance formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Inflation confound?",
       "answer": "Separated: 3.10 normalizes for index inflation so 3.5 isolates execution variance - a deliberate decomposition of variance sources."
      },
      {
       "question": "Professors will ask: 'Where is the statistical test?'",
       "answer": "There is none and none is claimed. This is a calibrated control-limit indicator in the SPC tradition: the arithmetic is exact, uncertainty lives in the inputs, and the band edges are decision thresholds with cited practice provenance, verified by the band harness. Pretending otherwise would be the indefensible position."
      }
     ],
     "requiredInputs": [
      "materialCostBaseline",
      "materialCostCurrent"
     ]
    },
    {
     "name": "Overhead Absorption Rate",
     "methodClass": "Overhead Absorption",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Indirects absorbed vs plan corridor.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "A ratio computed exactly from reported figures (no sampling error in the arithmetic). Uncertainty enters through the inputs (measurement/reporting error in EV, AC, PV) and is handled at the governance layer: 4-tier bands act as control limits - decision thresholds calibrated to industry evidence, not p-values.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Assumes the underlying document figures are accurate; PCEIF explicitly compensates via Data Integrity (Cat 9) modules that score input quality, and via DST fusion that lets weak evidence abstain.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Ratios and thresholds trace to DoD EVMIG / PMI Practice Standard for EVM; the 0.95/0.92/0.88 bands align with published EVM variance-tolerance conventions. Validated by the tests.html band harness (~30 edge cases from code constants) and calibrated synthetic document sets that hit each target band.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Overhead Absorption Rate formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Why include indirects?",
       "answer": "Overhead under-absorption is a leading insolvency indicator in contracting; corridor sourced from surety-industry practice."
      },
      {
       "question": "Professors will ask: 'Where is the statistical test?'",
       "answer": "There is none and none is claimed. This is a calibrated control-limit indicator in the SPC tradition: the arithmetic is exact, uncertainty lives in the inputs, and the band edges are decision thresholds with cited practice provenance, verified by the band harness. Pretending otherwise would be the indefensible position."
      }
     ],
     "requiredInputs": [
      "indirectCostPlan",
      "indirectCostActual"
     ]
    },
    {
     "name": "Cost Risk Analysis P80",
     "methodClass": "Cost Risk Analysis",
     "defenseTier": "Tier 1 - Statistical / stochastic model",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Monte Carlo over cost-element distributions; P80 cost vs budget+contingency.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Propagates input uncertainty by repeated sampling from assumed input distributions; output is an empirical distribution of the target quantity from which percentiles (P50/P80) and exceedance probabilities are read.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "SIMULATE",
     "oversightDescription": "Simulate - supports scenario understanding only; it cannot authorize project or contractual action.",
     "failureModes": "Percentile label without simulation; cost-element correlation omitted; uncertainty factor not calibrated.",
     "assumptionsLimitations": "Input distributions and independence structure are assumed, not estimated from large samples; results are conditional on those assumptions. Convergence requires sufficient iterations (LLN).",
     "implementationFidelity": "The code calculates a deterministic EAC uplift and calls it P80. It is not a Monte Carlo cost-risk analysis. Rename or replace with sampled cost-element distributions and correlations.",
     "accreditationBasis": "Traceable to standard risk-analysis practice (AACE RP 41R-08 / NASA cost-risk guidance). Validated by convergence checks (stability of percentiles across iteration counts) and sensitivity of outputs to input-distribution choices.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by Cost Risk Analysis P80.\" Prohibited: \"The code implements the canonical Cost Risk Analysis P80 method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Correlation between cost elements?",
       "answer": "Applied correlation matrix (default positive pairwise correlation) because independence understates tail risk - the classic CRA critique, addressed and documented."
      }
     ],
     "requiredInputs": [
      "bac",
      "cpi",
      "ac",
      "ev"
     ]
    },
    {
     "name": "Analogous Estimating Ratio",
     "methodClass": "Analogous Estimating",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Current unit cost vs analog project benchmark.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "A ratio computed exactly from reported figures (no sampling error in the arithmetic). Uncertainty enters through the inputs (measurement/reporting error in EV, AC, PV) and is handled at the governance layer: 4-tier bands act as control limits - decision thresholds calibrated to industry evidence, not p-values.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Assumes the underlying document figures are accurate; PCEIF explicitly compensates via Data Integrity (Cat 9) modules that score input quality, and via DST fusion that lets weak evidence abstain.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Ratios and thresholds trace to DoD EVMIG / PMI Practice Standard for EVM; the 0.95/0.92/0.88 bands align with published EVM variance-tolerance conventions. Validated by the tests.html band harness (~30 edge cases from code constants) and calibrated synthetic document sets that hit each target band.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Analogous Estimating Ratio formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Just one analog?",
       "answer": "Benchmark band widened to reflect analog uncertainty; presented as corroborative evidence, low fusion mass."
      },
      {
       "question": "Professors will ask: 'Where is the statistical test?'",
       "answer": "There is none and none is claimed. This is a calibrated control-limit indicator in the SPC tradition: the arithmetic is exact, uncertainty lives in the inputs, and the band edges are decision thresholds with cited practice provenance, verified by the band harness. Pretending otherwise would be the indefensible position."
      }
     ],
     "requiredInputs": [
      "analogousOverrunPct",
      "bac"
     ]
    },
    {
     "name": "Parametric Cost Index",
     "methodClass": "Parametric Cost",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Cost vs parametric model (e.g., $/sf regression) residual banded.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "A ratio computed exactly from reported figures (no sampling error in the arithmetic). Uncertainty enters through the inputs (measurement/reporting error in EV, AC, PV) and is handled at the governance layer: 4-tier bands act as control limits - decision thresholds calibrated to industry evidence, not p-values.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Assumes the underlying document figures are accurate; PCEIF explicitly compensates via Data Integrity (Cat 9) modules that score input quality, and via DST fusion that lets weak evidence abstain.",
     "implementationFidelity": "The code compares two EAC formulas and does not fit a parametric regression or unit-cost model. The current name is not defensible as a parametric cost model.",
     "accreditationBasis": "Ratios and thresholds trace to DoD EVMIG / PMI Practice Standard for EVM; the 0.95/0.92/0.88 bands align with published EVM variance-tolerance conventions. Validated by the tests.html band harness (~30 edge cases from code constants) and calibrated synthetic document sets that hit each target band.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by Parametric Cost Index.\" Prohibited: \"The code implements the canonical Parametric Cost Index method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Where's the regression?",
       "answer": "The parametric baseline is a fitted relationship from sector data; the module scores the residual - a standardized-residual outlier check, W2/EDA logic."
      },
      {
       "question": "Professors will ask: 'Where is the statistical test?'",
       "answer": "There is none and none is claimed. This is a calibrated control-limit indicator in the SPC tradition: the arithmetic is exact, uncertainty lives in the inputs, and the band edges are decision thresholds with cited practice provenance, verified by the band harness. Pretending otherwise would be the indefensible position."
      }
     ],
     "requiredInputs": [
      "bac",
      "ev",
      "ac",
      "actualPctComplete"
     ]
    },
    {
     "name": "Inflation Adjustment Index",
     "methodClass": "Inflation Adjustment",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Escalation-normalized cost ratio using published indices.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "A ratio computed exactly from reported figures (no sampling error in the arithmetic). Uncertainty enters through the inputs (measurement/reporting error in EV, AC, PV) and is handled at the governance layer: 4-tier bands act as control limits - decision thresholds calibrated to industry evidence, not p-values.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Assumes the underlying document figures are accurate; PCEIF explicitly compensates via Data Integrity (Cat 9) modules that score input quality, and via DST fusion that lets weak evidence abstain.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Ratios and thresholds trace to DoD EVMIG / PMI Practice Standard for EVM; the 0.95/0.92/0.88 bands align with published EVM variance-tolerance conventions. Validated by the tests.html band harness (~30 edge cases from code constants) and calibrated synthetic document sets that hit each target band.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Inflation Adjustment Index formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Source?",
       "answer": "Published construction cost indices (ENR/BLS); exogenous, citable, no estimation performed in-module."
      },
      {
       "question": "Professors will ask: 'Where is the statistical test?'",
       "answer": "There is none and none is claimed. This is a calibrated control-limit indicator in the SPC tradition: the arithmetic is exact, uncertainty lives in the inputs, and the band edges are decision thresholds with cited practice provenance, verified by the band harness. Pretending otherwise would be the indefensible position."
      }
     ],
     "requiredInputs": [
      "materialCostBaseline",
      "materialCostCurrent"
     ]
    }
   ]
  },
  {
   "key": "category-4-document-intelligence",
   "num": "Category 4",
   "name": "Document Intelligence",
   "count": 10,
   "modules": [
    {
     "name": "Document Risk Score",
     "methodClass": "Doc Risk Cat4",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Aggregate docRiskScore in [0,1] from raw extracted facts across RFI/OAC/correspondence/risk-register/NCR docs; bands 0.30/0.70.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "LLM extraction converts unstructured documents into structured fields; docRiskScore aggregates raw fact signals (dispute language, unresolved RFIs, NCR counts) into [0,1]. Extraction uncertainty is acknowledged: documents carry raw facts only (no pre-judged verdicts), and the Opus audit pass is an independent second-reader check.",
     "explainability": "Provenance trace: source document, extracted raw facts, excerpt/page reference, extraction confidence or audit result, scoring terms, and threshold path.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Extraction error; ambiguous or missing documents; duplicate counts; stale records; threshold drift; mistaking a risk flag for fault or contractual responsibility.",
     "assumptionsLimitations": "LLM extraction can err; mitigations are the raw-facts-only authoring rule, dual-model audit, and Cat 9 consistency checks. Bands (0.30/0.70) are calibrated decision thresholds.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Accredited procedurally: documented extraction prompts, audit protocol, and inter-model agreement rates on the synthetic corpus (a measurable reliability statistic professors can interrogate).",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN, MAP, and MEASURE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894: risk-information quality, monitoring, and review; W3C PROV-O for entity/activity/agent provenance; dataset documentation principles from datasheets.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Document Risk Score method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How were 0.30/0.70 chosen?",
       "answer": "Calibrated on the synthetic corpus so that fact-density profiles authored to represent healthy/strained/distressed projects land in the intended bands, then face-validated with practitioners. It is a calibrated instrument, and the calibration procedure is the accreditation."
      }
     ],
     "requiredInputs": [
      "docRiskScore"
     ]
    },
    {
     "name": "RFI Velocity",
     "methodClass": "RFI Velocity",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Open-RFI aging and arrival rate; Poisson-arrival framing for rate comparison.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "LLM extraction converts unstructured documents into structured fields; docRiskScore aggregates raw fact signals (dispute language, unresolved RFIs, NCR counts) into [0,1]. Extraction uncertainty is acknowledged: documents carry raw facts only (no pre-judged verdicts), and the Opus audit pass is an independent second-reader check.",
     "explainability": "Provenance trace: source document, extracted raw facts, excerpt/page reference, extraction confidence or audit result, scoring terms, and threshold path.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Extraction error; ambiguous or missing documents; duplicate counts; stale records; threshold drift; mistaking a risk flag for fault or contractual responsibility.",
     "assumptionsLimitations": "LLM extraction can err; mitigations are the raw-facts-only authoring rule, dual-model audit, and Cat 9 consistency checks. Bands (0.30/0.70) are calibrated decision thresholds.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Accredited procedurally: documented extraction prompts, audit protocol, and inter-model agreement rates on the synthetic corpus (a measurable reliability statistic professors can interrogate).",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN, MAP, and MEASURE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894: risk-information quality, monitoring, and review; W3C PROV-O for entity/activity/agent provenance; dataset documentation principles from datasheets.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented RFI Velocity formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Poisson justified?",
       "answer": "RFI arrivals are rare, independent-ish events in time - the course's Poisson-process conditions approximately hold; rate comparison uses the Poisson mean-variance relationship."
      }
     ],
     "requiredInputs": [
      "rfiCount",
      "rfiPeriodDays"
     ]
    },
    {
     "name": "Submittal Rejection Rate",
     "methodClass": "Submittal Rejection",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Rejected/total submittals as a proportion; banded.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "LLM extraction converts unstructured documents into structured fields; docRiskScore aggregates raw fact signals (dispute language, unresolved RFIs, NCR counts) into [0,1]. Extraction uncertainty is acknowledged: documents carry raw facts only (no pre-judged verdicts), and the Opus audit pass is an independent second-reader check.",
     "explainability": "Provenance trace: source document, extracted raw facts, excerpt/page reference, extraction confidence or audit result, scoring terms, and threshold path.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Extraction error; ambiguous or missing documents; duplicate counts; stale records; threshold drift; mistaking a risk flag for fault or contractual responsibility.",
     "assumptionsLimitations": "LLM extraction can err; mitigations are the raw-facts-only authoring rule, dual-model audit, and Cat 9 consistency checks. Bands (0.30/0.70) are calibrated decision thresholds.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Accredited procedurally: documented extraction prompts, audit protocol, and inter-model agreement rates on the synthetic corpus (a measurable reliability statistic professors can interrogate).",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN, MAP, and MEASURE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894: risk-information quality, monitoring, and review; W3C PROV-O for entity/activity/agent provenance; dataset documentation principles from datasheets.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Submittal Rejection Rate formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Why not a proportion test?",
       "answer": "With small n per period a z-test is fragile; the band acts as a practical-significance threshold. With larger samples the same statistic supports a formal one-proportion test - stated as an extension."
      }
     ],
     "requiredInputs": [
      "submittalsTotal",
      "submittalsRejected"
     ]
    },
    {
     "name": "NCR Rate",
     "methodClass": "NCR Rate",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Nonconformance reports per work volume; bands .15/.30/.50.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "LLM extraction converts unstructured documents into structured fields; docRiskScore aggregates raw fact signals (dispute language, unresolved RFIs, NCR counts) into [0,1]. Extraction uncertainty is acknowledged: documents carry raw facts only (no pre-judged verdicts), and the Opus audit pass is an independent second-reader check.",
     "explainability": "Provenance trace: source document, extracted raw facts, excerpt/page reference, extraction confidence or audit result, scoring terms, and threshold path.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Extraction error; ambiguous or missing documents; duplicate counts; stale records; threshold drift; mistaking a risk flag for fault or contractual responsibility.",
     "assumptionsLimitations": "LLM extraction can err; mitigations are the raw-facts-only authoring rule, dual-model audit, and Cat 9 consistency checks. Bands (0.30/0.70) are calibrated decision thresholds.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Accredited procedurally: documented extraction prompts, audit protocol, and inter-model agreement rates on the synthetic corpus (a measurable reliability statistic professors can interrogate).",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN, MAP, and MEASURE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894: risk-information quality, monitoring, and review; W3C PROV-O for entity/activity/agent provenance; dataset documentation principles from datasheets.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented NCR Rate formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Rate denominators?",
       "answer": "Normalized per inspection volume so projects of different sizes are comparable - the exposure adjustment any rate statistic requires."
      }
     ],
     "requiredInputs": [
      "ncrIssued",
      "ncrClosed",
      "ncrOpen"
     ]
    },
    {
     "name": "Weather Day Impact",
     "methodClass": "Weather Impact",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Weather delay days vs contractual allowance.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "LLM extraction converts unstructured documents into structured fields; docRiskScore aggregates raw fact signals (dispute language, unresolved RFIs, NCR counts) into [0,1]. Extraction uncertainty is acknowledged: documents carry raw facts only (no pre-judged verdicts), and the Opus audit pass is an independent second-reader check.",
     "explainability": "Provenance trace: source document, extracted raw facts, excerpt/page reference, extraction confidence or audit result, scoring terms, and threshold path.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Extraction error; ambiguous or missing documents; duplicate counts; stale records; threshold drift; mistaking a risk flag for fault or contractual responsibility.",
     "assumptionsLimitations": "LLM extraction can err; mitigations are the raw-facts-only authoring rule, dual-model audit, and Cat 9 consistency checks. Bands (0.30/0.70) are calibrated decision thresholds.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Accredited procedurally: documented extraction prompts, audit protocol, and inter-model agreement rates on the synthetic corpus (a measurable reliability statistic professors can interrogate).",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN, MAP, and MEASURE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894: risk-information quality, monitoring, and review; W3C PROV-O for entity/activity/agent provenance; dataset documentation principles from datasheets.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Weather Day Impact formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Exogenous risk?",
       "answer": "Yes - separated so weather variance is not misattributed to performance; a variance-decomposition argument."
      }
     ],
     "requiredInputs": [
      "weatherDaysLost"
     ]
    },
    {
     "name": "Change Order Frequency",
     "methodClass": "CO Frequency",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "CO count and value rate vs baseline expectations.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "LLM extraction converts unstructured documents into structured fields; docRiskScore aggregates raw fact signals (dispute language, unresolved RFIs, NCR counts) into [0,1]. Extraction uncertainty is acknowledged: documents carry raw facts only (no pre-judged verdicts), and the Opus audit pass is an independent second-reader check.",
     "explainability": "Provenance trace: source document, extracted raw facts, excerpt/page reference, extraction confidence or audit result, scoring terms, and threshold path.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Extraction error; ambiguous or missing documents; duplicate counts; stale records; threshold drift; mistaking a risk flag for fault or contractual responsibility.",
     "assumptionsLimitations": "LLM extraction can err; mitigations are the raw-facts-only authoring rule, dual-model audit, and Cat 9 consistency checks. Bands (0.30/0.70) are calibrated decision thresholds.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Accredited procedurally: documented extraction prompts, audit protocol, and inter-model agreement rates on the synthetic corpus (a measurable reliability statistic professors can interrogate).",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN, MAP, and MEASURE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894: risk-information quality, monitoring, and review; W3C PROV-O for entity/activity/agent provenance; dataset documentation principles from datasheets.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Change Order Frequency formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Expectation source?",
       "answer": "Sector norms for CO value as % of contract; deviation is the signal."
      }
     ],
     "requiredInputs": [
      "changeOrderCount",
      "baselineContractSum",
      "revisedContractSum"
     ]
    },
    {
     "name": "Dispute Escalation Index",
     "methodClass": "Dispute Escalation",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Extracted dispute-language intensity trend across correspondence.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "LLM extraction converts unstructured documents into structured fields; docRiskScore aggregates raw fact signals (dispute language, unresolved RFIs, NCR counts) into [0,1]. Extraction uncertainty is acknowledged: documents carry raw facts only (no pre-judged verdicts), and the Opus audit pass is an independent second-reader check.",
     "explainability": "Provenance trace: source document, extracted raw facts, excerpt/page reference, extraction confidence or audit result, scoring terms, and threshold path.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Extraction error; ambiguous or missing documents; duplicate counts; stale records; threshold drift; mistaking a risk flag for fault or contractual responsibility.",
     "assumptionsLimitations": "LLM extraction can err; mitigations are the raw-facts-only authoring rule, dual-model audit, and Cat 9 consistency checks. Bands (0.30/0.70) are calibrated decision thresholds.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Accredited procedurally: documented extraction prompts, audit protocol, and inter-model agreement rates on the synthetic corpus (a measurable reliability statistic professors can interrogate).",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN, MAP, and MEASURE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894: risk-information quality, monitoring, and review; W3C PROV-O for entity/activity/agent provenance; dataset documentation principles from datasheets.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Dispute Escalation Index method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Subjective?",
       "answer": "The extraction targets enumerable facts (claim notices, reserved rights, cure letters), not sentiment; the audit pass measures extraction agreement."
      }
     ],
     "requiredInputs": [
      "docRiskScore",
      "rfiCount",
      "changeOrderCount"
     ]
    },
    {
     "name": "Subcontractor Performance",
     "methodClass": "Subcontractor Performance",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Rating aggregation from reports; bands 4/3.5/3.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "LLM extraction converts unstructured documents into structured fields; docRiskScore aggregates raw fact signals (dispute language, unresolved RFIs, NCR counts) into [0,1]. Extraction uncertainty is acknowledged: documents carry raw facts only (no pre-judged verdicts), and the Opus audit pass is an independent second-reader check.",
     "explainability": "Provenance trace: source document, extracted raw facts, excerpt/page reference, extraction confidence or audit result, scoring terms, and threshold path.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Extraction error; ambiguous or missing documents; duplicate counts; stale records; threshold drift; mistaking a risk flag for fault or contractual responsibility.",
     "assumptionsLimitations": "LLM extraction can err; mitigations are the raw-facts-only authoring rule, dual-model audit, and Cat 9 consistency checks. Bands (0.30/0.70) are calibrated decision thresholds.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Accredited procedurally: documented extraction prompts, audit protocol, and inter-model agreement rates on the synthetic corpus (a measurable reliability statistic professors can interrogate).",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN, MAP, and MEASURE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894: risk-information quality, monitoring, and review; W3C PROV-O for entity/activity/agent provenance; dataset documentation principles from datasheets.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Subcontractor Performance formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Ordinal data treated how?",
       "answer": "As ordinal - banded on thresholds, never averaged as if interval-scaled without noting the assumption."
      }
     ],
     "requiredInputs": [
      "subcontractorComplianceScore"
     ]
    },
    {
     "name": "Procurement Lead Time Monitor",
     "methodClass": "Procurement Lead Time",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Actual vs quoted lead times; late fraction banded.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "LLM extraction converts unstructured documents into structured fields; docRiskScore aggregates raw fact signals (dispute language, unresolved RFIs, NCR counts) into [0,1]. Extraction uncertainty is acknowledged: documents carry raw facts only (no pre-judged verdicts), and the Opus audit pass is an independent second-reader check.",
     "explainability": "Provenance trace: source document, extracted raw facts, excerpt/page reference, extraction confidence or audit result, scoring terms, and threshold path.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Extraction error; ambiguous or missing documents; duplicate counts; stale records; threshold drift; mistaking a risk flag for fault or contractual responsibility.",
     "assumptionsLimitations": "LLM extraction can err; mitigations are the raw-facts-only authoring rule, dual-model audit, and Cat 9 consistency checks. Bands (0.30/0.70) are calibrated decision thresholds.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Accredited procedurally: documented extraction prompts, audit protocol, and inter-model agreement rates on the synthetic corpus (a measurable reliability statistic professors can interrogate).",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN, MAP, and MEASURE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894: risk-information quality, monitoring, and review; W3C PROV-O for entity/activity/agent provenance; dataset documentation principles from datasheets.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Procurement Lead Time Monitor formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Distributional view?",
       "answer": "Lead-time overrun fraction is a censored observation problem; the module reports the empirical late fraction, honest about right-censored open orders."
      }
     ],
     "requiredInputs": [
      "longLeadItemsTotal",
      "longLeadAtRisk",
      "longLeadDelayed"
     ]
    },
    {
     "name": "Specification Conflict Density",
     "methodClass": "Spec Conflict Density",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Extracted spec conflicts per division; density banded.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "LLM extraction converts unstructured documents into structured fields; docRiskScore aggregates raw fact signals (dispute language, unresolved RFIs, NCR counts) into [0,1]. Extraction uncertainty is acknowledged: documents carry raw facts only (no pre-judged verdicts), and the Opus audit pass is an independent second-reader check.",
     "explainability": "Provenance trace: source document, extracted raw facts, excerpt/page reference, extraction confidence or audit result, scoring terms, and threshold path.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Extraction error; ambiguous or missing documents; duplicate counts; stale records; threshold drift; mistaking a risk flag for fault or contractual responsibility.",
     "assumptionsLimitations": "LLM extraction can err; mitigations are the raw-facts-only authoring rule, dual-model audit, and Cat 9 consistency checks. Bands (0.30/0.70) are calibrated decision thresholds.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Accredited procedurally: documented extraction prompts, audit protocol, and inter-model agreement rates on the synthetic corpus (a measurable reliability statistic professors can interrogate).",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN, MAP, and MEASURE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894: risk-information quality, monitoring, and review; W3C PROV-O for entity/activity/agent provenance; dataset documentation principles from datasheets.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Specification Conflict Density method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Detection reliability?",
       "answer": "Bounded by extraction recall; reported jointly with Cat 9 completeness so a low score with poor document coverage is discounted in fusion."
      }
     ],
     "requiredInputs": [
      "docRiskScore",
      "rfiCount"
     ]
    }
   ]
  },
  {
   "key": "category-5-systems-dynamics-simulation",
   "num": "Category 5",
   "name": "Systems Dynamics & Simulation",
   "count": 8,
   "modules": [
    {
     "name": "DSM Rework Propagation",
     "methodClass": "DSM Rework Cat5",
     "defenseTier": "Tier 1 - Statistical / stochastic model",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Flow-weighted rework propagation through the dependency matrix (see 3.2 dedupe flag).",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Mechanistic stochastic models of project workflows: arrival/service processes (queueing), entity flows (DES), interacting agents (ABM), feedback loops (rework). Outputs are distributions of throughput/delay under sampled randomness.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "SIMULATE",
     "oversightDescription": "Simulate - supports scenario understanding only; it cannot authorize project or contractual action.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Arrival/service distributions parameterized from document-extracted rates; structural validity (does the model topology match the real workflow) argued via practitioner interviews, not statistics.",
     "implementationFidelity": "This category entry aliases the same DSM result used by Module 3.2. The duplication must be removed or the cost-oriented and system-oriented computations must be made materially different.",
     "accreditationBasis": "Poisson/queueing theory is canonical (M/M/1 assumptions stated); ABM/DES validated by face validation + extreme-condition tests (Sargent's simulation V&V framework - the citable accreditation standard for simulation models).",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by DSM Rework Propagation.\" Prohibited: \"The code implements the canonical DSM Rework Propagation method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Same as 3.2?",
       "answer": "On the punch-list - see 3.2. Defense posture: acknowledge and resolve before the review, do not improvise a distinction live."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi"
     ]
    },
    {
     "name": "Sensitivity Analysis",
     "methodClass": "Sensitivity Analysis",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "One-at-a-time and range-based sensitivity of project status to input perturbations.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Prescriptive layer: given fused statuses, explores trade-offs (LP, Pareto, regret). Uncertainty is carried in via scenario ranges and sensitivity matrices rather than re-estimated.",
     "explainability": "Decision/scenario trace: alternatives, assumptions, objectives, constraints or perturbations, scores, trade-offs, and sensitivity of the recommendation.",
     "oversightLevel": "SIMULATE",
     "oversightDescription": "Simulate - supports scenario understanding only; it cannot authorize project or contractual action.",
     "failureModes": "Unstated objectives or weights; infeasible or omitted constraints; scenario ranges selected to force a result; recommendation interpreted as an instruction.",
     "assumptionsLimitations": "Objective weights and constraint sets are stakeholder inputs; results presented as decision support, never as unique optima.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Standard OR methods (LP: Dantzig; Pareto/regret: Savage) with textbook provenance. Validated by hand-checkable small instances in the test harness.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Sensitivity Analysis method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "OAT limitations?",
       "answer": "Acknowledged - OAT misses interactions; the tornado (5.3) and scenario matrix (10.4) partially compensate, and the limitation is documented."
      }
     ],
     "requiredInputs": [
      "bac",
      "ev",
      "ac",
      "pv",
      "cpi",
      "spi"
     ]
    },
    {
     "name": "Tornado Risk Ranking",
     "methodClass": "Tornado Diagram",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Ranks inputs by output swing across plausible ranges.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Prescriptive layer: given fused statuses, explores trade-offs (LP, Pareto, regret). Uncertainty is carried in via scenario ranges and sensitivity matrices rather than re-estimated.",
     "explainability": "Decision/scenario trace: alternatives, assumptions, objectives, constraints or perturbations, scores, trade-offs, and sensitivity of the recommendation.",
     "oversightLevel": "SIMULATE",
     "oversightDescription": "Simulate - supports scenario understanding only; it cannot authorize project or contractual action.",
     "failureModes": "Unstated objectives or weights; infeasible or omitted constraints; scenario ranges selected to force a result; recommendation interpreted as an instruction.",
     "assumptionsLimitations": "Objective weights and constraint sets are stakeholder inputs; results presented as decision support, never as unique optima.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Standard OR methods (LP: Dantzig; Pareto/regret: Savage) with textbook provenance. Validated by hand-checkable small instances in the test harness.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Tornado Risk Ranking method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Range provenance?",
       "answer": "Ranges from band edges and historical variation - each bar's endpoints are traceable to a documented source."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore",
      "actualPctComplete",
      "plannedPctComplete"
     ]
    },
    {
     "name": "Scenario Modeling",
     "methodClass": "Scenario Modeling",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Named coherent scenarios (baseline/stress/recovery) recomputed end-to-end.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Prescriptive layer: given fused statuses, explores trade-offs (LP, Pareto, regret). Uncertainty is carried in via scenario ranges and sensitivity matrices rather than re-estimated.",
     "explainability": "Decision/scenario trace: alternatives, assumptions, objectives, constraints or perturbations, scores, trade-offs, and sensitivity of the recommendation.",
     "oversightLevel": "SIMULATE",
     "oversightDescription": "Simulate - supports scenario understanding only; it cannot authorize project or contractual action.",
     "failureModes": "Unstated objectives or weights; infeasible or omitted constraints; scenario ranges selected to force a result; recommendation interpreted as an instruction.",
     "assumptionsLimitations": "Objective weights and constraint sets are stakeholder inputs; results presented as decision support, never as unique optima.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Standard OR methods (LP: Dantzig; Pareto/regret: Savage) with textbook provenance. Validated by hand-checkable small instances in the test harness.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Scenario Modeling method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Scenario probability?",
       "answer": "None assigned - scenarios are conditional analyses; assigning probabilities would overstate knowledge (a deliberate epistemic-humility choice)."
      }
     ],
     "requiredInputs": [
      "bac",
      "ev",
      "ac",
      "cpi",
      "spi"
     ]
    },
    {
     "name": "Rework Feedback Loop",
     "methodClass": "Rework Feedback",
     "defenseTier": "Tier 1 - Statistical / stochastic model",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "System-dynamics loop: undiscovered rework stock degrading productivity.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Mechanistic stochastic models of project workflows: arrival/service processes (queueing), entity flows (DES), interacting agents (ABM), feedback loops (rework). Outputs are distributions of throughput/delay under sampled randomness.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "SIMULATE",
     "oversightDescription": "Simulate - supports scenario understanding only; it cannot authorize project or contractual action.",
     "failureModes": "Incorrect source data; threshold not calibrated; denominator instability; correlated indicators; band-edge sensitivity; status interpreted without context.",
     "assumptionsLimitations": "Arrival/service distributions parameterized from document-extracted rates; structural validity (does the model topology match the real workflow) argued via practitioner interviews, not statistics.",
     "implementationFidelity": "The code forms a weighted index from CPI, RFI count, and change-order count. It does not implement stock-flow equations or a system-dynamics feedback simulation.",
     "accreditationBasis": "Poisson/queueing theory is canonical (M/M/1 assumptions stated); ABM/DES validated by face validation + extreme-condition tests (Sargent's simulation V&V framework - the citable accreditation standard for simulation models).",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by Rework Feedback Loop.\" Prohibited: \"The code implements the canonical Rework Feedback Loop method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Validation?",
       "answer": "Sargent V&V: extreme-condition tests (zero rework -> plan trajectory; high rework -> known death-spiral shape from SD literature, Cooper's rework cycle)."
      }
     ],
     "requiredInputs": [
      "cpi",
      "rfiCount",
      "changeOrderCount"
     ]
    },
    {
     "name": "Queueing Theory Bottleneck",
     "methodClass": "Queueing Bottleneck",
     "defenseTier": "Tier 1 - Statistical / stochastic model",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "M/M/c approximation of approval/inspection queues from extracted arrival and service rates.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Mechanistic stochastic models of project workflows: arrival/service processes (queueing), entity flows (DES), interacting agents (ABM), feedback loops (rework). Outputs are distributions of throughput/delay under sampled randomness.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "SIMULATE",
     "oversightDescription": "Simulate - supports scenario understanding only; it cannot authorize project or contractual action.",
     "failureModes": "No arrival/service process; constraint ratio misread as waiting-time estimate.",
     "assumptionsLimitations": "Arrival/service distributions parameterized from document-extracted rates; structural validity (does the model topology match the real workflow) argued via practitioner interviews, not statistics.",
     "implementationFidelity": "The code computes constrained activities divided by planned activities. It does not calculate queue utilization, waiting time, or an M/M/c model. Rename as a constraint-bottleneck ratio or implement queueing equations.",
     "accreditationBasis": "Poisson/queueing theory is canonical (M/M/1 assumptions stated); ABM/DES validated by face validation + extreme-condition tests (Sargent's simulation V&V framework - the citable accreditation standard for simulation models).",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by Queueing Theory Bottleneck.\" Prohibited: \"The code implements the canonical Queueing Theory Bottleneck method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "M/M/c assumptions?",
       "answer": "Poisson arrivals and exponential service - course-taught conditions; stated as approximations with utilization-based results robust to moderate violations."
      }
     ],
     "requiredInputs": [
      "activitiesPlanned",
      "activitiesConstrained"
     ]
    },
    {
     "name": "Agent-Based Supply Chain",
     "methodClass": "Agent Supply Chain",
     "defenseTier": "Tier 1 - Statistical / stochastic model",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Agents = suppliers/subs with stochastic lead times; emergent delay distributions.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Mechanistic stochastic models of project workflows: arrival/service processes (queueing), entity flows (DES), interacting agents (ABM), feedback loops (rework). Outputs are distributions of throughput/delay under sampled randomness.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "SIMULATE",
     "oversightDescription": "Simulate - supports scenario understanding only; it cannot authorize project or contractual action.",
     "failureModes": "No agents or interaction rules; at-risk ratio misrepresented as emergent simulation.",
     "assumptionsLimitations": "Arrival/service distributions parameterized from document-extracted rates; structural validity (does the model topology match the real workflow) argued via practitioner interviews, not statistics.",
     "implementationFidelity": "The code computes the share of long-lead items at risk. There are no agents, interactions, state transitions, or emergent outcomes. Rename as a supply-risk ratio or implement an ABM.",
     "accreditationBasis": "Poisson/queueing theory is canonical (M/M/1 assumptions stated); ABM/DES validated by face validation + extreme-condition tests (Sargent's simulation V&V framework - the citable accreditation standard for simulation models).",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by Agent-Based Supply Chain.\" Prohibited: \"The code implements the canonical Agent-Based Supply Chain method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "ABM accreditation?",
       "answer": "Face validation with practitioners plus parameter provenance from documents; positioned as exploratory (tier-1 stochastic but structural-validity-limited), per Sargent."
      }
     ],
     "requiredInputs": [
      "longLeadItemsTotal",
      "longLeadAtRisk"
     ]
    },
    {
     "name": "Discrete Event Simulation",
     "methodClass": "Discrete Event Sim",
     "defenseTier": "Tier 1 - Statistical / stochastic model",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Workflow DES of the document-approval pipeline; outputs cycle-time distribution.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Mechanistic stochastic models of project workflows: arrival/service processes (queueing), entity flows (DES), interacting agents (ABM), feedback loops (rework). Outputs are distributions of throughput/delay under sampled randomness.",
     "explainability": "Formula/rule trace: named inputs with provenance, exact transformation, intermediate values, threshold bands, status result, and abstention reason when inputs are missing.",
     "oversightLevel": "SIMULATE",
     "oversightDescription": "Simulate - supports scenario understanding only; it cannot authorize project or contractual action.",
     "failureModes": "No event calendar or resource logic; throughput proxy misrepresented as DES.",
     "assumptionsLimitations": "Arrival/service distributions parameterized from document-extracted rates; structural validity (does the model topology match the real workflow) argued via practitioner interviews, not statistics.",
     "implementationFidelity": "The code computes an algebraic throughput index from progress and SPI. There is no event calendar, entity queue, resource seizure, or sampled service time. Rename or implement a discrete-event model.",
     "accreditationBasis": "Poisson/queueing theory is canonical (M/M/1 assumptions stated); ABM/DES validated by face validation + extreme-condition tests (Sargent's simulation V&V framework - the citable accreditation standard for simulation models).",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by Discrete Event Simulation.\" Prohibited: \"The code implements the canonical Discrete Event Simulation method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Why DES and queueing both?",
       "answer": "Queueing gives closed-form steady-state checks; DES relaxes assumptions. Agreement between them is a verification argument (model cross-validation)."
      }
     ],
     "requiredInputs": [
      "spi",
      "actualPctComplete",
      "plannedPctComplete",
      "cpi"
     ]
    }
   ]
  },
  {
   "key": "category-6-aggregation-rules",
   "num": "Category 6",
   "name": "Aggregation Rules",
   "count": 4,
   "modules": [
    {
     "name": "Conservative Dominance",
     "methodClass": "Conservative Dominance",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Project status = worst category. A max-type aggregation guaranteeing no masking.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Combines per-module status votes into a category verdict. DST assigns basic probability masses to status hypotheses and combines them with Dempster's rule (Red weighted 1.5x); missing-input modules abstain (no mass) rather than injecting uniform 25/25/25/25 noise. Simpler rules (dominance, weighted voting, worst-N-of-M) are transparent aggregation baselines.",
     "explainability": "Aggregation trace: each contributing status, weight or order statistic, abstentions, tie rule, and resulting category/project state.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Dempster's rule assumes evidential independence between modules; correlated modules (several EVM ratios share EV/AC) can double-count - mitigated by the 1.5x Red weighting design and conservative dominance at project level.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Shafer (1976) primary source. Validated by the fusion-table unit tests and by the calibration probe protocol (known-band document sets must reproduce target category status).",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Conservative Dominance method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Too conservative?",
       "answer": "Chosen policy for a governance instrument: the cost asymmetry between missed Red and false Amber justifies a minimax posture - a decision-theoretic, not statistical, argument, stated as such."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "Weighted Voting",
     "methodClass": "Weighted Voting",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Mass-weighted category vote; Red 1.5x.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Combines per-module status votes into a category verdict. DST assigns basic probability masses to status hypotheses and combines them with Dempster's rule (Red weighted 1.5x); missing-input modules abstain (no mass) rather than injecting uniform 25/25/25/25 noise. Simpler rules (dominance, weighted voting, worst-N-of-M) are transparent aggregation baselines.",
     "explainability": "Aggregation trace: each contributing status, weight or order statistic, abstentions, tie rule, and resulting category/project state.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Dempster's rule assumes evidential independence between modules; correlated modules (several EVM ratios share EV/AC) can double-count - mitigated by the 1.5x Red weighting design and conservative dominance at project level.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Shafer (1976) primary source. Validated by the fusion-table unit tests and by the calibration probe protocol (known-band document sets must reproduce target category status).",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Weighted Voting method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Why 1.5?",
       "answer": "Sensitivity-tested: rankings stable for weights 1.3-1.8; 1.5 sits mid-plateau. The stability analysis is the defense, not the number."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "Majority Rules",
     "methodClass": "Majority Rules",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Simple-majority baseline aggregator.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Combines per-module status votes into a category verdict. DST assigns basic probability masses to status hypotheses and combines them with Dempster's rule (Red weighted 1.5x); missing-input modules abstain (no mass) rather than injecting uniform 25/25/25/25 noise. Simpler rules (dominance, weighted voting, worst-N-of-M) are transparent aggregation baselines.",
     "explainability": "Aggregation trace: each contributing status, weight or order statistic, abstentions, tie rule, and resulting category/project state.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Dempster's rule assumes evidential independence between modules; correlated modules (several EVM ratios share EV/AC) can double-count - mitigated by the 1.5x Red weighting design and conservative dominance at project level.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Shafer (1976) primary source. Validated by the fusion-table unit tests and by the calibration probe protocol (known-band document sets must reproduce target category status).",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Majority Rules method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Purpose?",
       "answer": "A transparency baseline - showing fused verdicts against the naive rule quantifies what the sophisticated fusion adds."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "Worst-N-of-M",
     "methodClass": "Worst N of M",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Escalate if >=N modules of M are at/below a status.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Combines per-module status votes into a category verdict. DST assigns basic probability masses to status hypotheses and combines them with Dempster's rule (Red weighted 1.5x); missing-input modules abstain (no mass) rather than injecting uniform 25/25/25/25 noise. Simpler rules (dominance, weighted voting, worst-N-of-M) are transparent aggregation baselines.",
     "explainability": "Aggregation trace: each contributing status, weight or order statistic, abstentions, tie rule, and resulting category/project state.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Dempster's rule assumes evidential independence between modules; correlated modules (several EVM ratios share EV/AC) can double-count - mitigated by the 1.5x Red weighting design and conservative dominance at project level.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Shafer (1976) primary source. Validated by the fusion-table unit tests and by the calibration probe protocol (known-band document sets must reproduce target category status).",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Worst-N-of-M method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Relation to order statistics?",
       "answer": "It is a threshold on an order statistic of module votes - directly analyzable for false-alarm behavior under independence assumptions."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    }
   ]
  },
  {
   "key": "category-7-uncertainty-formalisms",
   "num": "Category 7",
   "name": "Uncertainty Formalisms",
   "count": 20,
   "modules": [
    {
     "name": "Dempster-Shafer",
     "methodClass": "DST Evidence Combination",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "The production fusion engine: masses per status, Dempster combination, abstention for missing inputs, Red 1.5x. The known open issue: fusion source table has no Yellow mass for evmMin 0.90-0.95 (probe protocol decides docs-vs-table fix).",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Combines per-module status votes into a category verdict. DST assigns basic probability masses to status hypotheses and combines them with Dempster's rule (Red weighted 1.5x); missing-input modules abstain (no mass) rather than injecting uniform 25/25/25/25 noise. Simpler rules (dominance, weighted voting, worst-N-of-M) are transparent aggregation baselines.",
     "explainability": "Evidence trace: input statuses, memberships or masses, reliability discounts, conflict/indeterminacy, combination steps, final score, and parameter-sensitivity table. SHAP/LIME is not appropriate for these symbolic formalisms.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Correlated evidence double-counting; extreme conflict normalization; arbitrary masses; hidden abstentions.",
     "assumptionsLimitations": "Dempster's rule assumes evidential independence between modules; correlated modules (several EVM ratios share EV/AC) can double-count - mitigated by the 1.5x Red weighting design and conservative dominance at project level.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Shafer (1976) primary source. Validated by the fusion-table unit tests and by the calibration probe protocol (known-band document sets must reproduce target category status).",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Dempster-Shafer method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Dempster's rule with conflicting evidence?",
       "answer": "Known Zadeh critique: high conflict can yield counterintuitive combinations. Mitigations: abstention removes vacuous mass, Red-weighting biases conservative, and conservative dominance caps the damage at project level. Critique and mitigations both documented."
      },
      {
       "question": "Why no Yellow mass at evmMin 0.90-0.95?",
       "answer": "Open defect under probe: if the PRJ-21476 Yellow set fuses to Amber, the fix is one line in the fusion source table - evidence the calibration protocol works as designed."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "Rough Sets",
     "methodClass": "Rough Sets Classification",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Lower/upper approximation of status classes given indiscernible evidence granules; boundary region = irreducible ambiguity.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Represents epistemic uncertainty (vague, conflicting, or partially trusted evidence) that classical probability handles poorly: membership degrees, belief/plausibility intervals, or hesitancy terms instead of a single probability mass. Output is a graded status assessment carrying its own confidence.",
     "explainability": "Evidence trace: input statuses, memberships or masses, reliability discounts, conflict/indeterminacy, combination steps, final score, and parameter-sensitivity table. SHAP/LIME is not appropriate for these symbolic formalisms.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Membership functions / mass assignments are elicited design choices; the defense is comparative (do rankings remain stable across reasonable parameterizations - a sensitivity argument), not inferential.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Each formalism is peer-reviewed decision-science literature with citable primary sources. Accreditation in PCEIF = published axioms + documented parameterization + sensitivity/stability checks, plus practitioner face-validation interviews.",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Rough Sets method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How is a non-probabilistic formalism 'validated'?",
       "answer": "By the accreditation triad used throughout Cat 7: (1) primary peer-reviewed citation for the axioms, (2) documented parameterization with provenance, (3) sensitivity/stability analysis showing fused verdicts are robust to reasonable parameter variation, plus practitioner face validation. This is the accepted standard for decision-science formalisms, where frequentist error rates are category errors."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "Neutrosophic Logic",
     "methodClass": "Neutrosophic Logic",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Truth/indeterminacy/falsity triplet per status claim; indeterminacy made explicit rather than split between T/F.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Represents epistemic uncertainty (vague, conflicting, or partially trusted evidence) that classical probability handles poorly: membership degrees, belief/plausibility intervals, or hesitancy terms instead of a single probability mass. Output is a graded status assessment carrying its own confidence.",
     "explainability": "Evidence trace: input statuses, memberships or masses, reliability discounts, conflict/indeterminacy, combination steps, final score, and parameter-sensitivity table. SHAP/LIME is not appropriate for these symbolic formalisms.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Membership functions / mass assignments are elicited design choices; the defense is comparative (do rankings remain stable across reasonable parameterizations - a sensitivity argument), not inferential.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Each formalism is peer-reviewed decision-science literature with citable primary sources. Accreditation in PCEIF = published axioms + documented parameterization + sensitivity/stability checks, plus practitioner face-validation interviews.",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Neutrosophic Logic method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How is a non-probabilistic formalism 'validated'?",
       "answer": "By the accreditation triad used throughout Cat 7: (1) primary peer-reviewed citation for the axioms, (2) documented parameterization with provenance, (3) sensitivity/stability analysis showing fused verdicts are robust to reasonable parameter variation, plus practitioner face validation. This is the accepted standard for decision-science formalisms, where frequentist error rates are category errors."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "Interval Fuzzy Sets",
     "methodClass": "Interval Fuzzy Sets",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Membership as an interval, encoding second-order uncertainty about the membership function itself.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Represents epistemic uncertainty (vague, conflicting, or partially trusted evidence) that classical probability handles poorly: membership degrees, belief/plausibility intervals, or hesitancy terms instead of a single probability mass. Output is a graded status assessment carrying its own confidence.",
     "explainability": "Evidence trace: input statuses, memberships or masses, reliability discounts, conflict/indeterminacy, combination steps, final score, and parameter-sensitivity table. SHAP/LIME is not appropriate for these symbolic formalisms.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Membership functions / mass assignments are elicited design choices; the defense is comparative (do rankings remain stable across reasonable parameterizations - a sensitivity argument), not inferential.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Each formalism is peer-reviewed decision-science literature with citable primary sources. Accreditation in PCEIF = published axioms + documented parameterization + sensitivity/stability checks, plus practitioner face-validation interviews.",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Interval Fuzzy Sets method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How is a non-probabilistic formalism 'validated'?",
       "answer": "By the accreditation triad used throughout Cat 7: (1) primary peer-reviewed citation for the axioms, (2) documented parameterization with provenance, (3) sensitivity/stability analysis showing fused verdicts are robust to reasonable parameter variation, plus practitioner face validation. This is the accepted standard for decision-science formalisms, where frequentist error rates are category errors."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi"
     ]
    },
    {
     "name": "Z-numbers",
     "methodClass": "Z Numbers",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Pairs (restriction, reliability): a status claim plus confidence in the source - the formal home of Cat 9 reliability weights.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Represents epistemic uncertainty (vague, conflicting, or partially trusted evidence) that classical probability handles poorly: membership degrees, belief/plausibility intervals, or hesitancy terms instead of a single probability mass. Output is a graded status assessment carrying its own confidence.",
     "explainability": "Evidence trace: input statuses, memberships or masses, reliability discounts, conflict/indeterminacy, combination steps, final score, and parameter-sensitivity table. SHAP/LIME is not appropriate for these symbolic formalisms.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Membership functions / mass assignments are elicited design choices; the defense is comparative (do rankings remain stable across reasonable parameterizations - a sensitivity argument), not inferential.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Each formalism is peer-reviewed decision-science literature with citable primary sources. Accreditation in PCEIF = published axioms + documented parameterization + sensitivity/stability checks, plus practitioner face-validation interviews.",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Z-numbers method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How is a non-probabilistic formalism 'validated'?",
       "answer": "By the accreditation triad used throughout Cat 7: (1) primary peer-reviewed citation for the axioms, (2) documented parameterization with provenance, (3) sensitivity/stability analysis showing fused verdicts are robust to reasonable parameter variation, plus practitioner face validation. This is the accepted standard for decision-science formalisms, where frequentist error rates are category errors."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "PLTS",
     "methodClass": "PLTS",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Probabilistic linguistic term sets: distributions over linguistic labels (e.g., 60% 'stressed', 40% 'stable') from practitioner-style judgments.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Represents epistemic uncertainty (vague, conflicting, or partially trusted evidence) that classical probability handles poorly: membership degrees, belief/plausibility intervals, or hesitancy terms instead of a single probability mass. Output is a graded status assessment carrying its own confidence.",
     "explainability": "Evidence trace: input statuses, memberships or masses, reliability discounts, conflict/indeterminacy, combination steps, final score, and parameter-sensitivity table. SHAP/LIME is not appropriate for these symbolic formalisms.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Membership functions / mass assignments are elicited design choices; the defense is comparative (do rankings remain stable across reasonable parameterizations - a sensitivity argument), not inferential.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Each formalism is peer-reviewed decision-science literature with citable primary sources. Accreditation in PCEIF = published axioms + documented parameterization + sensitivity/stability checks, plus practitioner face-validation interviews.",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the PLTS method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How is a non-probabilistic formalism 'validated'?",
       "answer": "By the accreditation triad used throughout Cat 7: (1) primary peer-reviewed citation for the axioms, (2) documented parameterization with provenance, (3) sensitivity/stability analysis showing fused verdicts are robust to reasonable parameter variation, plus practitioner face validation. This is the accepted standard for decision-science formalisms, where frequentist error rates are category errors."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "Plithogenic Sets",
     "methodClass": "Plithogenic Sets",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Multi-attribute membership with per-attribute contradiction degrees; suits multi-source project evidence.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Represents epistemic uncertainty (vague, conflicting, or partially trusted evidence) that classical probability handles poorly: membership degrees, belief/plausibility intervals, or hesitancy terms instead of a single probability mass. Output is a graded status assessment carrying its own confidence.",
     "explainability": "Evidence trace: input statuses, memberships or masses, reliability discounts, conflict/indeterminacy, combination steps, final score, and parameter-sensitivity table. SHAP/LIME is not appropriate for these symbolic formalisms.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Membership functions / mass assignments are elicited design choices; the defense is comparative (do rankings remain stable across reasonable parameterizations - a sensitivity argument), not inferential.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Each formalism is peer-reviewed decision-science literature with citable primary sources. Accreditation in PCEIF = published axioms + documented parameterization + sensitivity/stability checks, plus practitioner face-validation interviews.",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Plithogenic Sets method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How is a non-probabilistic formalism 'validated'?",
       "answer": "By the accreditation triad used throughout Cat 7: (1) primary peer-reviewed citation for the axioms, (2) documented parameterization with provenance, (3) sensitivity/stability analysis showing fused verdicts are robust to reasonable parameter variation, plus practitioner face validation. This is the accepted standard for decision-science formalisms, where frequentist error rates are category errors."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "Belief Rule Base",
     "methodClass": "Belief Rule Base",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "IF-THEN rules with belief degrees; the auditable middle ground between expert rules and probabilistic inference.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Represents epistemic uncertainty (vague, conflicting, or partially trusted evidence) that classical probability handles poorly: membership degrees, belief/plausibility intervals, or hesitancy terms instead of a single probability mass. Output is a graded status assessment carrying its own confidence.",
     "explainability": "Evidence trace: input statuses, memberships or masses, reliability discounts, conflict/indeterminacy, combination steps, final score, and parameter-sensitivity table. SHAP/LIME is not appropriate for these symbolic formalisms.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Membership functions / mass assignments are elicited design choices; the defense is comparative (do rankings remain stable across reasonable parameterizations - a sensitivity argument), not inferential.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Each formalism is peer-reviewed decision-science literature with citable primary sources. Accreditation in PCEIF = published axioms + documented parameterization + sensitivity/stability checks, plus practitioner face-validation interviews.",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Belief Rule Base method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How is a non-probabilistic formalism 'validated'?",
       "answer": "By the accreditation triad used throughout Cat 7: (1) primary peer-reviewed citation for the axioms, (2) documented parameterization with provenance, (3) sensitivity/stability analysis showing fused verdicts are robust to reasonable parameter variation, plus practitioner face validation. This is the accepted standard for decision-science formalisms, where frequentist error rates are category errors."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "Quantum Probability",
     "methodClass": "Quantum Probability",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "SOBER GROUNDING REQUIRED (open item): defensible only as non-commutative probability for order-effects in judgment (Busemeyer & Bruza literature) - NOT physics claims. If it cannot be grounded that way, cut it before the defense.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Represents epistemic uncertainty (vague, conflicting, or partially trusted evidence) that classical probability handles poorly: membership degrees, belief/plausibility intervals, or hesitancy terms instead of a single probability mass. Output is a graded status assessment carrying its own confidence.",
     "explainability": "Evidence trace: input statuses, memberships or masses, reliability discounts, conflict/indeterminacy, combination steps, final score, and parameter-sensitivity table. SHAP/LIME is not appropriate for these symbolic formalisms.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Conceptual overreach; parameter arbitrariness; no empirical order-effect data.",
     "assumptionsLimitations": "Membership functions / mass assignments are elicited design choices; the defense is comparative (do rankings remain stable across reasonable parameterizations - a sensitivity argument), not inferential.",
     "implementationFidelity": "The code is a heuristic amplitude-interference demonstration. Unless the praxis specifically studies order effects and validates the parameterization against judgment data, remove or relegate it to future work.",
     "accreditationBasis": "Each formalism is peer-reviewed decision-science literature with citable primary sources. Accreditation in PCEIF = published axioms + documented parameterization + sensitivity/stability checks, plus practitioner face-validation interviews.",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by Quantum Probability.\" Prohibited: \"The code implements the canonical Quantum Probability method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How is a non-probabilistic formalism 'validated'?",
       "answer": "By the accreditation triad used throughout Cat 7: (1) primary peer-reviewed citation for the axioms, (2) documented parameterization with provenance, (3) sensitivity/stability analysis showing fused verdicts are robust to reasonable parameter variation, plus practitioner face validation. This is the accepted standard for decision-science formalisms, where frequentist error rates are category errors."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "Pythagorean Fuzzy Sets",
     "methodClass": "Pythagorean Fuzzy",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Membership/non-membership with mu^2+nu^2<=1, a wider admissible region than intuitionistic sets.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Represents epistemic uncertainty (vague, conflicting, or partially trusted evidence) that classical probability handles poorly: membership degrees, belief/plausibility intervals, or hesitancy terms instead of a single probability mass. Output is a graded status assessment carrying its own confidence.",
     "explainability": "Evidence trace: input statuses, memberships or masses, reliability discounts, conflict/indeterminacy, combination steps, final score, and parameter-sensitivity table. SHAP/LIME is not appropriate for these symbolic formalisms.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Membership functions / mass assignments are elicited design choices; the defense is comparative (do rankings remain stable across reasonable parameterizations - a sensitivity argument), not inferential.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Each formalism is peer-reviewed decision-science literature with citable primary sources. Accreditation in PCEIF = published axioms + documented parameterization + sensitivity/stability checks, plus practitioner face-validation interviews.",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Pythagorean Fuzzy Sets method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How is a non-probabilistic formalism 'validated'?",
       "answer": "By the accreditation triad used throughout Cat 7: (1) primary peer-reviewed citation for the axioms, (2) documented parameterization with provenance, (3) sensitivity/stability analysis showing fused verdicts are robust to reasonable parameter variation, plus practitioner face validation. This is the accepted standard for decision-science formalisms, where frequentist error rates are category errors."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "Picture Fuzzy Sets",
     "methodClass": "Picture Fuzzy",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Adds neutrality degree: yes/abstain/no/refusal - matching how practitioners actually vote on status.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Represents epistemic uncertainty (vague, conflicting, or partially trusted evidence) that classical probability handles poorly: membership degrees, belief/plausibility intervals, or hesitancy terms instead of a single probability mass. Output is a graded status assessment carrying its own confidence.",
     "explainability": "Evidence trace: input statuses, memberships or masses, reliability discounts, conflict/indeterminacy, combination steps, final score, and parameter-sensitivity table. SHAP/LIME is not appropriate for these symbolic formalisms.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Membership functions / mass assignments are elicited design choices; the defense is comparative (do rankings remain stable across reasonable parameterizations - a sensitivity argument), not inferential.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Each formalism is peer-reviewed decision-science literature with citable primary sources. Accreditation in PCEIF = published axioms + documented parameterization + sensitivity/stability checks, plus practitioner face-validation interviews.",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Picture Fuzzy Sets method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How is a non-probabilistic formalism 'validated'?",
       "answer": "By the accreditation triad used throughout Cat 7: (1) primary peer-reviewed citation for the axioms, (2) documented parameterization with provenance, (3) sensitivity/stability analysis showing fused verdicts are robust to reasonable parameter variation, plus practitioner face validation. This is the accepted standard for decision-science formalisms, where frequentist error rates are category errors."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "Hesitant Fuzzy Sets",
     "methodClass": "Hesitant Fuzzy",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Multiple candidate membership values when evaluators disagree; keeps the disagreement instead of averaging it away.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Represents epistemic uncertainty (vague, conflicting, or partially trusted evidence) that classical probability handles poorly: membership degrees, belief/plausibility intervals, or hesitancy terms instead of a single probability mass. Output is a graded status assessment carrying its own confidence.",
     "explainability": "Evidence trace: input statuses, memberships or masses, reliability discounts, conflict/indeterminacy, combination steps, final score, and parameter-sensitivity table. SHAP/LIME is not appropriate for these symbolic formalisms.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Membership functions / mass assignments are elicited design choices; the defense is comparative (do rankings remain stable across reasonable parameterizations - a sensitivity argument), not inferential.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Each formalism is peer-reviewed decision-science literature with citable primary sources. Accreditation in PCEIF = published axioms + documented parameterization + sensitivity/stability checks, plus practitioner face-validation interviews.",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Hesitant Fuzzy Sets method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How is a non-probabilistic formalism 'validated'?",
       "answer": "By the accreditation triad used throughout Cat 7: (1) primary peer-reviewed citation for the axioms, (2) documented parameterization with provenance, (3) sensitivity/stability analysis showing fused verdicts are robust to reasonable parameter variation, plus practitioner face validation. This is the accepted standard for decision-science formalisms, where frequentist error rates are category errors."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi"
     ]
    },
    {
     "name": "Type-2 Fuzzy Sets",
     "methodClass": "Type2 Fuzzy",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Fuzzy membership of membership: uncertainty about the band edges themselves - the formalism that owns the 'why 0.95?' question.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Represents epistemic uncertainty (vague, conflicting, or partially trusted evidence) that classical probability handles poorly: membership degrees, belief/plausibility intervals, or hesitancy terms instead of a single probability mass. Output is a graded status assessment carrying its own confidence.",
     "explainability": "Evidence trace: input statuses, memberships or masses, reliability discounts, conflict/indeterminacy, combination steps, final score, and parameter-sensitivity table. SHAP/LIME is not appropriate for these symbolic formalisms.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Membership functions / mass assignments are elicited design choices; the defense is comparative (do rankings remain stable across reasonable parameterizations - a sensitivity argument), not inferential.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Each formalism is peer-reviewed decision-science literature with citable primary sources. Accreditation in PCEIF = published axioms + documented parameterization + sensitivity/stability checks, plus practitioner face-validation interviews.",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Type-2 Fuzzy Sets method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How is a non-probabilistic formalism 'validated'?",
       "answer": "By the accreditation triad used throughout Cat 7: (1) primary peer-reviewed citation for the axioms, (2) documented parameterization with provenance, (3) sensitivity/stability analysis showing fused verdicts are robust to reasonable parameter variation, plus practitioner face validation. This is the accepted standard for decision-science formalisms, where frequentist error rates are category errors."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi"
     ]
    },
    {
     "name": "Maximum Entropy",
     "methodClass": "Maximum Entropy",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Least-committal distribution consistent with known constraints; the principled answer to missing information (and the anti-25/25/25/25 argument formalized).",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Represents epistemic uncertainty (vague, conflicting, or partially trusted evidence) that classical probability handles poorly: membership degrees, belief/plausibility intervals, or hesitancy terms instead of a single probability mass. Output is a graded status assessment carrying its own confidence.",
     "explainability": "Evidence trace: input statuses, memberships or masses, reliability discounts, conflict/indeterminacy, combination steps, final score, and parameter-sensitivity table. SHAP/LIME is not appropriate for these symbolic formalisms.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Membership functions / mass assignments are elicited design choices; the defense is comparative (do rankings remain stable across reasonable parameterizations - a sensitivity argument), not inferential.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Each formalism is peer-reviewed decision-science literature with citable primary sources. Accreditation in PCEIF = published axioms + documented parameterization + sensitivity/stability checks, plus practitioner face-validation interviews.",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Maximum Entropy method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How is a non-probabilistic formalism 'validated'?",
       "answer": "By the accreditation triad used throughout Cat 7: (1) primary peer-reviewed citation for the axioms, (2) documented parameterization with provenance, (3) sensitivity/stability analysis showing fused verdicts are robust to reasonable parameter variation, plus practitioner face validation. This is the accepted standard for decision-science formalisms, where frequentist error rates are category errors."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "Possibility Theory",
     "methodClass": "Possibility Theory",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Possibility/necessity bounds; captures 'cannot be ruled out' vs 'must be' - natural for early-project sparse evidence.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Represents epistemic uncertainty (vague, conflicting, or partially trusted evidence) that classical probability handles poorly: membership degrees, belief/plausibility intervals, or hesitancy terms instead of a single probability mass. Output is a graded status assessment carrying its own confidence.",
     "explainability": "Evidence trace: input statuses, memberships or masses, reliability discounts, conflict/indeterminacy, combination steps, final score, and parameter-sensitivity table. SHAP/LIME is not appropriate for these symbolic formalisms.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Membership functions / mass assignments are elicited design choices; the defense is comparative (do rankings remain stable across reasonable parameterizations - a sensitivity argument), not inferential.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Each formalism is peer-reviewed decision-science literature with citable primary sources. Accreditation in PCEIF = published axioms + documented parameterization + sensitivity/stability checks, plus practitioner face-validation interviews.",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Possibility Theory method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How is a non-probabilistic formalism 'validated'?",
       "answer": "By the accreditation triad used throughout Cat 7: (1) primary peer-reviewed citation for the axioms, (2) documented parameterization with provenance, (3) sensitivity/stability analysis showing fused verdicts are robust to reasonable parameter variation, plus practitioner face validation. This is the accepted standard for decision-science formalisms, where frequentist error rates are category errors."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "Spherical Fuzzy Sets",
     "methodClass": "Spherical Fuzzy",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Membership/non-membership/hesitancy on the unit sphere; recent generalization with growing MCDM literature.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Represents epistemic uncertainty (vague, conflicting, or partially trusted evidence) that classical probability handles poorly: membership degrees, belief/plausibility intervals, or hesitancy terms instead of a single probability mass. Output is a graded status assessment carrying its own confidence.",
     "explainability": "Evidence trace: input statuses, memberships or masses, reliability discounts, conflict/indeterminacy, combination steps, final score, and parameter-sensitivity table. SHAP/LIME is not appropriate for these symbolic formalisms.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Membership functions / mass assignments are elicited design choices; the defense is comparative (do rankings remain stable across reasonable parameterizations - a sensitivity argument), not inferential.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Each formalism is peer-reviewed decision-science literature with citable primary sources. Accreditation in PCEIF = published axioms + documented parameterization + sensitivity/stability checks, plus practitioner face-validation interviews.",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Spherical Fuzzy Sets method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How is a non-probabilistic formalism 'validated'?",
       "answer": "By the accreditation triad used throughout Cat 7: (1) primary peer-reviewed citation for the axioms, (2) documented parameterization with provenance, (3) sensitivity/stability analysis showing fused verdicts are robust to reasonable parameter variation, plus practitioner face validation. This is the accepted standard for decision-science formalisms, where frequentist error rates are category errors."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "Fermatean Fuzzy Sets",
     "methodClass": "Fermatean Fuzzy",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "mu^3+nu^3<=1 admissible region; used where evaluations are strongly polarized.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Represents epistemic uncertainty (vague, conflicting, or partially trusted evidence) that classical probability handles poorly: membership degrees, belief/plausibility intervals, or hesitancy terms instead of a single probability mass. Output is a graded status assessment carrying its own confidence.",
     "explainability": "Evidence trace: input statuses, memberships or masses, reliability discounts, conflict/indeterminacy, combination steps, final score, and parameter-sensitivity table. SHAP/LIME is not appropriate for these symbolic formalisms.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Membership functions / mass assignments are elicited design choices; the defense is comparative (do rankings remain stable across reasonable parameterizations - a sensitivity argument), not inferential.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Each formalism is peer-reviewed decision-science literature with citable primary sources. Accreditation in PCEIF = published axioms + documented parameterization + sensitivity/stability checks, plus practitioner face-validation interviews.",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Fermatean Fuzzy Sets method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How is a non-probabilistic formalism 'validated'?",
       "answer": "By the accreditation triad used throughout Cat 7: (1) primary peer-reviewed citation for the axioms, (2) documented parameterization with provenance, (3) sensitivity/stability analysis showing fused verdicts are robust to reasonable parameter variation, plus practitioner face validation. This is the accepted standard for decision-science formalisms, where frequentist error rates are category errors."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi"
     ]
    },
    {
     "name": "MARCOS Ranking",
     "methodClass": "MARCOS",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Compromise ranking against ideal/anti-ideal reference projects.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Represents epistemic uncertainty (vague, conflicting, or partially trusted evidence) that classical probability handles poorly: membership degrees, belief/plausibility intervals, or hesitancy terms instead of a single probability mass. Output is a graded status assessment carrying its own confidence.",
     "explainability": "Evidence trace: input statuses, memberships or masses, reliability discounts, conflict/indeterminacy, combination steps, final score, and parameter-sensitivity table. SHAP/LIME is not appropriate for these symbolic formalisms.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Membership functions / mass assignments are elicited design choices; the defense is comparative (do rankings remain stable across reasonable parameterizations - a sensitivity argument), not inferential.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Each formalism is peer-reviewed decision-science literature with citable primary sources. Accreditation in PCEIF = published axioms + documented parameterization + sensitivity/stability checks, plus practitioner face-validation interviews.",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the MARCOS Ranking method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How is a non-probabilistic formalism 'validated'?",
       "answer": "By the accreditation triad used throughout Cat 7: (1) primary peer-reviewed citation for the axioms, (2) documented parameterization with provenance, (3) sensitivity/stability analysis showing fused verdicts are robust to reasonable parameter variation, plus practitioner face validation. This is the accepted standard for decision-science formalisms, where frequentist error rates are category errors."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "CRITIC-TOPSIS",
     "methodClass": "CRITIC TOPSIS",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Objective criteria weighting (CRITIC: contrast + correlation) feeding TOPSIS distance-to-ideal ranking - the statistically grounded weighting in the MCDM pair.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Represents epistemic uncertainty (vague, conflicting, or partially trusted evidence) that classical probability handles poorly: membership degrees, belief/plausibility intervals, or hesitancy terms instead of a single probability mass. Output is a graded status assessment carrying its own confidence.",
     "explainability": "Evidence trace: input statuses, memberships or masses, reliability discounts, conflict/indeterminacy, combination steps, final score, and parameter-sensitivity table. SHAP/LIME is not appropriate for these symbolic formalisms.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Membership functions / mass assignments are elicited design choices; the defense is comparative (do rankings remain stable across reasonable parameterizations - a sensitivity argument), not inferential.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Each formalism is peer-reviewed decision-science literature with citable primary sources. Accreditation in PCEIF = published axioms + documented parameterization + sensitivity/stability checks, plus practitioner face-validation interviews.",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the CRITIC-TOPSIS method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How is a non-probabilistic formalism 'validated'?",
       "answer": "By the accreditation triad used throughout Cat 7: (1) primary peer-reviewed citation for the axioms, (2) documented parameterization with provenance, (3) sensitivity/stability analysis showing fused verdicts are robust to reasonable parameter variation, plus practitioner face validation. This is the accepted standard for decision-science formalisms, where frequentist error rates are category errors."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "Hypersoft Sets",
     "methodClass": "Hypersoft Sets",
     "defenseTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "asCodedTier": "Tier 3 - Epistemic uncertainty / evidence fusion",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Parameter-family mappings for multi-attribute, multi-source evidence organization.",
     "detProbSplit": "Deterministic algebra over epistemic representations (belief masses, memberships, linguistic terms, rankings, or votes). No repeated-sampling probability is implied unless explicitly stated.",
     "uncertaintyMethod": "Represents epistemic uncertainty (vague, conflicting, or partially trusted evidence) that classical probability handles poorly: membership degrees, belief/plausibility intervals, or hesitancy terms instead of a single probability mass. Output is a graded status assessment carrying its own confidence.",
     "explainability": "Evidence trace: input statuses, memberships or masses, reliability discounts, conflict/indeterminacy, combination steps, final score, and parameter-sensitivity table. SHAP/LIME is not appropriate for these symbolic formalisms.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Arbitrary memberships or masses; correlated evidence; instability near thresholds; method disagreement hidden by a single rollup; result mistaken for probability.",
     "assumptionsLimitations": "Membership functions / mass assignments are elicited design choices; the defense is comparative (do rankings remain stable across reasonable parameterizations - a sensitivity argument), not inferential.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Each formalism is peer-reviewed decision-science literature with citable primary sources. Accreditation in PCEIF = published axioms + documented parameterization + sensitivity/stability checks, plus practitioner face-validation interviews.",
     "validationRequired": "Verify axioms and combination equations; test identities, boundary cases, conflict cases, and abstention; vary masses/memberships/weights; report rank/status stability; compare methods; obtain practitioner face validation.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894 risk analysis under incomplete or conflicting information. Model-card-style documentation records intended use and limitations.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Hypersoft Sets method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "How is a non-probabilistic formalism 'validated'?",
       "answer": "By the accreditation triad used throughout Cat 7: (1) primary peer-reviewed citation for the axioms, (2) documented parameterization with provenance, (3) sensitivity/stability analysis showing fused verdicts are robust to reasonable parameter variation, plus practitioner face validation. This is the accepted standard for decision-science formalisms, where frequentist error rates are category errors."
      }
     ],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    }
   ]
  },
  {
   "key": "category-8-governance",
   "num": "Category 8",
   "name": "Governance",
   "count": 9,
   "modules": [
    {
     "name": "ABM Governance Layer",
     "methodClass": "ABM Governance",
     "defenseTier": "Tier 1 - Statistical / stochastic model",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Agent-based model of governance actors (owner/CM/contractor) response latencies to signals.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Mechanistic stochastic models of project workflows: arrival/service processes (queueing), entity flows (DES), interacting agents (ABM), feedback loops (rework). Outputs are distributions of throughput/delay under sampled randomness.",
     "explainability": "Rule and authority trace: cited rule version, applicability conditions, threshold evaluation, authority, required record, and human judgment outcome.",
     "oversightLevel": "RECOMMEND",
     "oversightDescription": "Recommend - presents an action option; named human authority must approve, modify, defer, or reject.",
     "failureModes": "Governance rules mislabeled as ABM; authority matrix out of date; silent override; fairness gate bypass.",
     "assumptionsLimitations": "Arrival/service distributions parameterized from document-extracted rates; structural validity (does the model topology match the real workflow) argued via practitioner interviews, not statistics.",
     "implementationFidelity": "The implementation is a deterministic authority and decision tree in decision.js. That is a strong explainable governance mechanism, but it is not an agent-based simulation. Rename as Governance Decision Rules.",
     "accreditationBasis": "Poisson/queueing theory is canonical (M/M/1 assumptions stated); ABM/DES validated by face validation + extreme-condition tests (Sargent's simulation V&V framework - the citable accreditation standard for simulation models).",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN and MANAGE; ISO/IEC 42001: management-system clause families 4-10; ISO/IEC 23894: risk treatment, communication, monitoring, and review. Any legal threshold requires a versioned authoritative source. This is an alignment statement, not certification.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by ABM Governance Layer.\" Prohibited: \"The code implements the canonical ABM Governance Layer method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "FAR Threshold Monitor",
     "methodClass": "FAR Threshold",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Checks contract actions against FAR dollar/approval thresholds.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Binary or banded checks against externally defined regulatory thresholds. No estimation involved; the uncertainty question is data completeness, delegated to Cat 9 scores.",
     "explainability": "Rule and authority trace: cited rule version, applicability conditions, threshold evaluation, authority, required record, and human judgment outcome.",
     "oversightLevel": "FLAG_RECOMMEND",
     "oversightDescription": "Flag / recommend - routes a possible governance or compliance issue to the responsible human reviewer.",
     "failureModes": "Outdated or inapplicable legal threshold; false compliance claim; missing jurisdiction and contract type.",
     "assumptionsLimitations": "Thresholds are exogenous (FAR, OMB A-11, EVM reporting mandates) - the module's validity is fidelity to the cited source, which is the cleanest possible accreditation.",
     "implementationFidelity": "The hard-coded FAR Part 34 and 25-percent overrun logic must not be presented as a legal compliance determination. Replace with a versioned, cited, configurable rule set reviewed by a contracting specialist.",
     "accreditationBasis": "Direct citation to FAR clauses / OMB Circular A-11 / agency EVM reporting thresholds. Validated by test cases at threshold boundaries.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN and MANAGE; ISO/IEC 42001: management-system clause families 4-10; ISO/IEC 23894: risk treatment, communication, monitoring, and review. Any legal threshold requires a versioned authoritative source. This is an alignment statement, not certification.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by FAR Threshold Monitor.\" Prohibited: \"The code implements the canonical FAR Threshold Monitor method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "bac",
      "cpi",
      "ev",
      "ac"
     ]
    },
    {
     "name": "OMB A-11 Check",
     "methodClass": "OMB A11 Check",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Capital programming exhibit completeness per OMB Circular A-11.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Binary or banded checks against externally defined regulatory thresholds. No estimation involved; the uncertainty question is data completeness, delegated to Cat 9 scores.",
     "explainability": "Rule and authority trace: cited rule version, applicability conditions, threshold evaluation, authority, required record, and human judgment outcome.",
     "oversightLevel": "FLAG_RECOMMEND",
     "oversightDescription": "Flag / recommend - routes a possible governance or compliance issue to the responsible human reviewer.",
     "failureModes": "Outdated or inapplicable OMB rule; oversimplified trigger; false compliance claim.",
     "assumptionsLimitations": "Thresholds are exogenous (FAR, OMB A-11, EVM reporting mandates) - the module's validity is fidelity to the cited source, which is the cleanest possible accreditation.",
     "implementationFidelity": "A BAC/CPI trigger does not constitute an OMB Circular A-11 compliance assessment. Treat the current output as a demonstration flag only.",
     "accreditationBasis": "Direct citation to FAR clauses / OMB Circular A-11 / agency EVM reporting thresholds. Validated by test cases at threshold boundaries.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN and MANAGE; ISO/IEC 42001: management-system clause families 4-10; ISO/IEC 23894: risk treatment, communication, monitoring, and review. Any legal threshold requires a versioned authoritative source. This is an alignment statement, not certification.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by OMB A-11 Check.\" Prohibited: \"The code implements the canonical OMB A-11 Check method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "bac",
      "cpi",
      "actualPctComplete"
     ]
    },
    {
     "name": "EVM Reporting Threshold",
     "methodClass": "EVM Reporting Threshold",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Flags when contract size/type mandates formal EVMS reporting.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Binary or banded checks against externally defined regulatory thresholds. No estimation involved; the uncertainty question is data completeness, delegated to Cat 9 scores.",
     "explainability": "Rule and authority trace: cited rule version, applicability conditions, threshold evaluation, authority, required record, and human judgment outcome.",
     "oversightLevel": "FLAG_RECOMMEND",
     "oversightDescription": "Flag / recommend - routes a possible governance or compliance issue to the responsible human reviewer.",
     "failureModes": "Outdated rule source; applicability error; missing authority; compliance flag treated as legal conclusion; contractor response rights omitted.",
     "assumptionsLimitations": "Thresholds are exogenous (FAR, OMB A-11, EVM reporting mandates) - the module's validity is fidelity to the cited source, which is the cleanest possible accreditation.",
     "implementationFidelity": "The module applies custom CPI/SPI bands. It is not an authoritative reporting threshold unless the governing agency requirement, effective date, and applicability are configured and cited.",
     "accreditationBasis": "Direct citation to FAR clauses / OMB Circular A-11 / agency EVM reporting thresholds. Validated by test cases at threshold boundaries.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN and MANAGE; ISO/IEC 42001: management-system clause families 4-10; ISO/IEC 23894: risk treatment, communication, monitoring, and review. Any legal threshold requires a versioned authoritative source. This is an alignment statement, not certification.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by EVM Reporting Threshold.\" Prohibited: \"The code implements the canonical EVM Reporting Threshold method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "bac",
      "cpi",
      "spi"
     ]
    },
    {
     "name": "Contract Modification Frequency",
     "methodClass": "Contract Mod Frequency",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Mod rate vs sector norms; banded.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Binary or banded checks against externally defined regulatory thresholds. No estimation involved; the uncertainty question is data completeness, delegated to Cat 9 scores.",
     "explainability": "Rule and authority trace: cited rule version, applicability conditions, threshold evaluation, authority, required record, and human judgment outcome.",
     "oversightLevel": "FLAG_RECOMMEND",
     "oversightDescription": "Flag / recommend - routes a possible governance or compliance issue to the responsible human reviewer.",
     "failureModes": "Outdated rule source; applicability error; missing authority; compliance flag treated as legal conclusion; contractor response rights omitted.",
     "assumptionsLimitations": "Thresholds are exogenous (FAR, OMB A-11, EVM reporting mandates) - the module's validity is fidelity to the cited source, which is the cleanest possible accreditation.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Direct citation to FAR clauses / OMB Circular A-11 / agency EVM reporting thresholds. Validated by test cases at threshold boundaries.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN and MANAGE; ISO/IEC 42001: management-system clause families 4-10; ISO/IEC 23894: risk treatment, communication, monitoring, and review. Any legal threshold requires a versioned authoritative source. This is an alignment statement, not certification.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Contract Modification Frequency method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "changeOrderCount",
      "baselineContractSum",
      "revisedContractSum"
     ]
    },
    {
     "name": "Quality Compliance Index",
     "methodClass": "Quality Compliance",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Quality pass rate vs contractual quality plan.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Binary or banded checks against externally defined regulatory thresholds. No estimation involved; the uncertainty question is data completeness, delegated to Cat 9 scores.",
     "explainability": "Rule and authority trace: cited rule version, applicability conditions, threshold evaluation, authority, required record, and human judgment outcome.",
     "oversightLevel": "FLAG_RECOMMEND",
     "oversightDescription": "Flag / recommend - routes a possible governance or compliance issue to the responsible human reviewer.",
     "failureModes": "Outdated rule source; applicability error; missing authority; compliance flag treated as legal conclusion; contractor response rights omitted.",
     "assumptionsLimitations": "Thresholds are exogenous (FAR, OMB A-11, EVM reporting mandates) - the module's validity is fidelity to the cited source, which is the cleanest possible accreditation.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Direct citation to FAR clauses / OMB Circular A-11 / agency EVM reporting thresholds. Validated by test cases at threshold boundaries.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN and MANAGE; ISO/IEC 42001: management-system clause families 4-10; ISO/IEC 23894: risk treatment, communication, monitoring, and review. Any legal threshold requires a versioned authoritative source. This is an alignment statement, not certification.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Quality Compliance Index method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "qualityDeficienciesNoted"
     ]
    },
    {
     "name": "Safety Performance Index",
     "methodClass": "Safety Performance",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Recordable-incident rate vs sector baseline (exposure-normalized).",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Binary or banded checks against externally defined regulatory thresholds. No estimation involved; the uncertainty question is data completeness, delegated to Cat 9 scores.",
     "explainability": "Rule and authority trace: cited rule version, applicability conditions, threshold evaluation, authority, required record, and human judgment outcome.",
     "oversightLevel": "FLAG_RECOMMEND",
     "oversightDescription": "Flag / recommend - routes a possible governance or compliance issue to the responsible human reviewer.",
     "failureModes": "Outdated rule source; applicability error; missing authority; compliance flag treated as legal conclusion; contractor response rights omitted.",
     "assumptionsLimitations": "Thresholds are exogenous (FAR, OMB A-11, EVM reporting mandates) - the module's validity is fidelity to the cited source, which is the cleanest possible accreditation.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Direct citation to FAR clauses / OMB Circular A-11 / agency EVM reporting thresholds. Validated by test cases at threshold boundaries.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN and MANAGE; ISO/IEC 42001: management-system clause families 4-10; ISO/IEC 23894: risk treatment, communication, monitoring, and review. Any legal threshold requires a versioned authoritative source. This is an alignment statement, not certification.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Safety Performance Index method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Incident rates are count data - model?",
       "answer": "Exposure-normalized rate with Poisson variance for the comparison band; small-count instability handled by banding on cumulative exposure."
      }
     ],
     "requiredInputs": [
      "safetyIncidentsDiscussed"
     ]
    },
    {
     "name": "Environmental Compliance Rate",
     "methodClass": "Environmental Compliance",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Environmental findings per inspection; banded.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Binary or banded checks against externally defined regulatory thresholds. No estimation involved; the uncertainty question is data completeness, delegated to Cat 9 scores.",
     "explainability": "Rule and authority trace: cited rule version, applicability conditions, threshold evaluation, authority, required record, and human judgment outcome.",
     "oversightLevel": "FLAG_RECOMMEND",
     "oversightDescription": "Flag / recommend - routes a possible governance or compliance issue to the responsible human reviewer.",
     "failureModes": "Outdated rule source; applicability error; missing authority; compliance flag treated as legal conclusion; contractor response rights omitted.",
     "assumptionsLimitations": "Thresholds are exogenous (FAR, OMB A-11, EVM reporting mandates) - the module's validity is fidelity to the cited source, which is the cleanest possible accreditation.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Direct citation to FAR clauses / OMB Circular A-11 / agency EVM reporting thresholds. Validated by test cases at threshold boundaries.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN and MANAGE; ISO/IEC 42001: management-system clause families 4-10; ISO/IEC 23894: risk treatment, communication, monitoring, and review. Any legal threshold requires a versioned authoritative source. This is an alignment statement, not certification.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Environmental Compliance Rate method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "environmentalIssuesDiscussed"
     ]
    },
    {
     "name": "Contractor Performance Score",
     "methodClass": "Contractor Performance",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "CPARS-style composite of ratings; ordinal thresholds 4/3.5/3.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Binary or banded checks against externally defined regulatory thresholds. No estimation involved; the uncertainty question is data completeness, delegated to Cat 9 scores.",
     "explainability": "Rule and authority trace: cited rule version, applicability conditions, threshold evaluation, authority, required record, and human judgment outcome.",
     "oversightLevel": "FLAG_RECOMMEND",
     "oversightDescription": "Flag / recommend - routes a possible governance or compliance issue to the responsible human reviewer.",
     "failureModes": "Outdated rule source; applicability error; missing authority; compliance flag treated as legal conclusion; contractor response rights omitted.",
     "assumptionsLimitations": "Thresholds are exogenous (FAR, OMB A-11, EVM reporting mandates) - the module's validity is fidelity to the cited source, which is the cleanest possible accreditation.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Direct citation to FAR clauses / OMB Circular A-11 / agency EVM reporting thresholds. Validated by test cases at threshold boundaries.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN and MANAGE; ISO/IEC 42001: management-system clause families 4-10; ISO/IEC 23894: risk treatment, communication, monitoring, and review. Any legal threshold requires a versioned authoritative source. This is an alignment statement, not certification.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Contractor Performance Score method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "overallRating",
      "scheduleRating",
      "costRating"
     ]
    }
   ]
  },
  {
   "key": "category-9-data-integrity",
   "num": "Category 9",
   "name": "Data Integrity",
   "count": 7,
   "modules": [
    {
     "name": "Missing Data Index",
     "methodClass": "Missing Data Index",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Fraction of the 27-doc manifest present, weighted by module-feeding importance.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Scores the trustworthiness of the evidence base itself (missingness, timeliness, consistency). This is PCEIF's explicit handling of the course's caveat that inference is only as good as the data: these scores feed source-reliability weights into fusion.",
     "explainability": "Score decomposition: expected fields/events, observed fields/events, missing or stale items, source weights, reconciliation differences, and resulting data-quality score.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incomplete manifest; missingness mechanism misunderstood; stale timestamps; duplicate sources; quality score treated as proof of correctness.",
     "assumptionsLimitations": "Completeness ratios assume the 27-document manifest defines 'complete'; consistency checks assume cross-document fields should reconcile exactly.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Grounded in data-quality dimensions literature (accuracy/completeness/timeliness/consistency - Wang & Strong 1996). Validated by injecting known gaps/contradictions into synthetic sets.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN, MAP, and MEASURE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894: risk-information quality, monitoring, and review; W3C PROV-O for entity/activity/agent provenance; dataset documentation principles from datasheets.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Missing Data Index formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "Missingness mechanism?",
       "answer": "PCEIF treats missingness as informative (MNAR-leaning): absent risk documents on a distressed project are themselves a signal, which is why completeness feeds fusion rather than being silently imputed."
      }
     ],
     "requiredInputs": [
      "bac"
     ]
    },
    {
     "name": "Data Timeliness Score",
     "methodClass": "Data Timeliness Score",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Age of latest period data vs reporting cadence.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Scores the trustworthiness of the evidence base itself (missingness, timeliness, consistency). This is PCEIF's explicit handling of the course's caveat that inference is only as good as the data: these scores feed source-reliability weights into fusion.",
     "explainability": "Score decomposition: expected fields/events, observed fields/events, missing or stale items, source weights, reconciliation differences, and resulting data-quality score.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incomplete manifest; missingness mechanism misunderstood; stale timestamps; duplicate sources; quality score treated as proof of correctness.",
     "assumptionsLimitations": "Completeness ratios assume the 27-document manifest defines 'complete'; consistency checks assume cross-document fields should reconcile exactly.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Grounded in data-quality dimensions literature (accuracy/completeness/timeliness/consistency - Wang & Strong 1996). Validated by injecting known gaps/contradictions into synthetic sets.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN, MAP, and MEASURE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894: risk-information quality, monitoring, and review; W3C PROV-O for entity/activity/agent provenance; dataset documentation principles from datasheets.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Data Timeliness Score formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "docDate"
     ]
    },
    {
     "name": "Source Reliability Weighting",
     "methodClass": "Source Reliability Weighting",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Per-source reliability weights feeding fusion mass (the Z-number reliability component operationalized).",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Scores the trustworthiness of the evidence base itself (missingness, timeliness, consistency). This is PCEIF's explicit handling of the course's caveat that inference is only as good as the data: these scores feed source-reliability weights into fusion.",
     "explainability": "Score decomposition: expected fields/events, observed fields/events, missing or stale items, source weights, reconciliation differences, and resulting data-quality score.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incomplete manifest; missingness mechanism misunderstood; stale timestamps; duplicate sources; quality score treated as proof of correctness.",
     "assumptionsLimitations": "Completeness ratios assume the 27-document manifest defines 'complete'; consistency checks assume cross-document fields should reconcile exactly.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Grounded in data-quality dimensions literature (accuracy/completeness/timeliness/consistency - Wang & Strong 1996). Validated by injecting known gaps/contradictions into synthetic sets.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN, MAP, and MEASURE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894: risk-information quality, monitoring, and review; W3C PROV-O for entity/activity/agent provenance; dataset documentation principles from datasheets.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Source Reliability Weighting formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "bac"
     ]
    },
    {
     "name": "Audit Trail Completeness",
     "methodClass": "Audit Trail Completeness",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Upload/extraction event coverage vs expected pipeline events.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Scores the trustworthiness of the evidence base itself (missingness, timeliness, consistency). This is PCEIF's explicit handling of the course's caveat that inference is only as good as the data: these scores feed source-reliability weights into fusion.",
     "explainability": "Score decomposition: expected fields/events, observed fields/events, missing or stale items, source weights, reconciliation differences, and resulting data-quality score.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incomplete manifest; missingness mechanism misunderstood; stale timestamps; duplicate sources; quality score treated as proof of correctness.",
     "assumptionsLimitations": "Completeness ratios assume the 27-document manifest defines 'complete'; consistency checks assume cross-document fields should reconcile exactly.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Grounded in data-quality dimensions literature (accuracy/completeness/timeliness/consistency - Wang & Strong 1996). Validated by injecting known gaps/contradictions into synthetic sets.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN, MAP, and MEASURE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894: risk-information quality, monitoring, and review; W3C PROV-O for entity/activity/agent provenance; dataset documentation principles from datasheets.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Audit Trail Completeness formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "bac"
     ]
    },
    {
     "name": "Information Completeness Ratio",
     "methodClass": "Information Completeness Ratio",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Field-level extraction completeness across required inputs.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Scores the trustworthiness of the evidence base itself (missingness, timeliness, consistency). This is PCEIF's explicit handling of the course's caveat that inference is only as good as the data: these scores feed source-reliability weights into fusion.",
     "explainability": "Score decomposition: expected fields/events, observed fields/events, missing or stale items, source weights, reconciliation differences, and resulting data-quality score.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incomplete manifest; missingness mechanism misunderstood; stale timestamps; duplicate sources; quality score treated as proof of correctness.",
     "assumptionsLimitations": "Completeness ratios assume the 27-document manifest defines 'complete'; consistency checks assume cross-document fields should reconcile exactly.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Grounded in data-quality dimensions literature (accuracy/completeness/timeliness/consistency - Wang & Strong 1996). Validated by injecting known gaps/contradictions into synthetic sets.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN, MAP, and MEASURE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894: risk-information quality, monitoring, and review; W3C PROV-O for entity/activity/agent provenance; dataset documentation principles from datasheets.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Information Completeness Ratio formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "bac"
     ]
    },
    {
     "name": "Cross-document Consistency Score",
     "methodClass": "Cross Doc Consistency",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Reconciliation checks (e.g., pay-app EV vs monthly-report EV) with tolerance bands.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Scores the trustworthiness of the evidence base itself (missingness, timeliness, consistency). This is PCEIF's explicit handling of the course's caveat that inference is only as good as the data: these scores feed source-reliability weights into fusion.",
     "explainability": "Score decomposition: expected fields/events, observed fields/events, missing or stale items, source weights, reconciliation differences, and resulting data-quality score.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incomplete manifest; missingness mechanism misunderstood; stale timestamps; duplicate sources; quality score treated as proof of correctness.",
     "assumptionsLimitations": "Completeness ratios assume the 27-document manifest defines 'complete'; consistency checks assume cross-document fields should reconcile exactly.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Grounded in data-quality dimensions literature (accuracy/completeness/timeliness/consistency - Wang & Strong 1996). Validated by injecting known gaps/contradictions into synthetic sets.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN, MAP, and MEASURE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894: risk-information quality, monitoring, and review; W3C PROV-O for entity/activity/agent provenance; dataset documentation principles from datasheets.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Cross-document Consistency Score formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "ev",
      "ac"
     ]
    },
    {
     "name": "Reporting Frequency Index",
     "methodClass": "Reporting Frequency Index",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "A",
     "assuranceDescription": "Formula/rule-faithful implementation that is directly testable, subject to input and threshold validity",
     "engineeringProblem": "Observed vs contractual reporting frequency.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Scores the trustworthiness of the evidence base itself (missingness, timeliness, consistency). This is PCEIF's explicit handling of the course's caveat that inference is only as good as the data: these scores feed source-reliability weights into fusion.",
     "explainability": "Score decomposition: expected fields/events, observed fields/events, missing or stale items, source weights, reconciliation differences, and resulting data-quality score.",
     "oversightLevel": "FLAG",
     "oversightDescription": "Flag - surfaces evidence for PM review; final interpretation and action remain human decisions.",
     "failureModes": "Incomplete manifest; missingness mechanism misunderstood; stale timestamps; duplicate sources; quality score treated as proof of correctness.",
     "assumptionsLimitations": "Completeness ratios assume the 27-document manifest defines 'complete'; consistency checks assume cross-document fields should reconcile exactly.",
     "implementationFidelity": "Code-aligned formula/rule review required; defend only at the documented assurance class.",
     "accreditationBasis": "Grounded in data-quality dimensions literature (accuracy/completeness/timeliness/consistency - Wang & Strong 1996). Validated by injecting known gaps/contradictions into synthetic sets.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: GOVERN, MAP, and MEASURE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894: risk-information quality, monitoring, and review; W3C PROV-O for entity/activity/agent provenance; dataset documentation principles from datasheets.",
     "permittedProhibitedClaims": "Allowed: \"The proof-of-concept implements the documented Reporting Frequency Index formula or rule and produces an auditable synthetic signal.\" Prohibited: claims of predictive accuracy, causal validity, or production certification without field evidence.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "docDate"
     ]
    }
   ]
  },
  {
   "key": "category-10-decision-optimization",
   "num": "Category 10",
   "name": "Decision Optimization",
   "count": 7,
   "modules": [
    {
     "name": "Multi-Objective Optimization",
     "methodClass": "Multi Objective Optimization",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Cost/schedule/risk trade surface over candidate interventions.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Prescriptive layer: given fused statuses, explores trade-offs (LP, Pareto, regret). Uncertainty is carried in via scenario ranges and sensitivity matrices rather than re-estimated.",
     "explainability": "Decision/scenario trace: alternatives, assumptions, objectives, constraints or perturbations, scores, trade-offs, and sensitivity of the recommendation.",
     "oversightLevel": "RECOMMEND",
     "oversightDescription": "Recommend - presents an action option; named human authority must approve, modify, defer, or reject.",
     "failureModes": "Unstated objectives or weights; infeasible or omitted constraints; scenario ranges selected to force a result; recommendation interpreted as an instruction.",
     "assumptionsLimitations": "Objective weights and constraint sets are stakeholder inputs; results presented as decision support, never as unique optima.",
     "implementationFidelity": "The code averages three normalized scores. It does not optimize decision variables over multiple objectives or generate a Pareto set.",
     "accreditationBasis": "Standard OR methods (LP: Dantzig; Pareto/regret: Savage) with textbook provenance. Validated by hand-checkable small instances in the test harness.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894: risk evaluation, treatment, monitoring, and review. The mapping supports governance alignment, not algorithm certification.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by Multi-Objective Optimization.\" Prohibited: \"The code implements the canonical Multi-Objective Optimization method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "Linear Programming",
     "methodClass": "Linear Programming",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Resource reallocation LP under budget/capacity constraints.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Prescriptive layer: given fused statuses, explores trade-offs (LP, Pareto, regret). Uncertainty is carried in via scenario ranges and sensitivity matrices rather than re-estimated.",
     "explainability": "Decision/scenario trace: alternatives, assumptions, objectives, constraints or perturbations, scores, trade-offs, and sensitivity of the recommendation.",
     "oversightLevel": "RECOMMEND",
     "oversightDescription": "Recommend - presents an action option; named human authority must approve, modify, defer, or reject.",
     "failureModes": "Unstated objectives or weights; infeasible or omitted constraints; scenario ranges selected to force a result; recommendation interpreted as an instruction.",
     "assumptionsLimitations": "Objective weights and constraint sets are stakeholder inputs; results presented as decision support, never as unique optima.",
     "implementationFidelity": "The code is a TCPI-style feasibility check and does not formulate or solve a linear program with decision variables, objective coefficients, and constraints.",
     "accreditationBasis": "Standard OR methods (LP: Dantzig; Pareto/regret: Savage) with textbook provenance. Validated by hand-checkable small instances in the test harness.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894: risk evaluation, treatment, monitoring, and review. The mapping supports governance alignment, not algorithm certification.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by Linear Programming.\" Prohibited: \"The code implements the canonical Linear Programming method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "bac",
      "ev",
      "ac",
      "cpi"
     ]
    },
    {
     "name": "Constraint Satisfaction Analysis",
     "methodClass": "Constraint Satisfaction",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Feasibility check of recovery plans against hard constraints.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Prescriptive layer: given fused statuses, explores trade-offs (LP, Pareto, regret). Uncertainty is carried in via scenario ranges and sensitivity matrices rather than re-estimated.",
     "explainability": "Decision/scenario trace: alternatives, assumptions, objectives, constraints or perturbations, scores, trade-offs, and sensitivity of the recommendation.",
     "oversightLevel": "RECOMMEND",
     "oversightDescription": "Recommend - presents an action option; named human authority must approve, modify, defer, or reject.",
     "failureModes": "Unstated objectives or weights; infeasible or omitted constraints; scenario ranges selected to force a result; recommendation interpreted as an instruction.",
     "assumptionsLimitations": "Objective weights and constraint sets are stakeholder inputs; results presented as decision support, never as unique optima.",
     "implementationFidelity": "The code counts satisfaction of four rules. It is an explainable constraint checklist, not a general constraint-satisfaction solver.",
     "accreditationBasis": "Standard OR methods (LP: Dantzig; Pareto/regret: Savage) with textbook provenance. Validated by hand-checkable small instances in the test harness.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894: risk evaluation, treatment, monitoring, and review. The mapping supports governance alignment, not algorithm certification.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by Constraint Satisfaction Analysis.\" Prohibited: \"The code implements the canonical Constraint Satisfaction Analysis method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "cpi",
      "spi",
      "bac"
     ]
    },
    {
     "name": "What-If Scenario Matrix",
     "methodClass": "WhatIf Scenario Matrix",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Grid of input perturbations x decisions with recomputed statuses.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Prescriptive layer: given fused statuses, explores trade-offs (LP, Pareto, regret). Uncertainty is carried in via scenario ranges and sensitivity matrices rather than re-estimated.",
     "explainability": "Decision/scenario trace: alternatives, assumptions, objectives, constraints or perturbations, scores, trade-offs, and sensitivity of the recommendation.",
     "oversightLevel": "RECOMMEND",
     "oversightDescription": "Recommend - presents an action option; named human authority must approve, modify, defer, or reject.",
     "failureModes": "Unstated objectives or weights; infeasible or omitted constraints; scenario ranges selected to force a result; recommendation interpreted as an instruction.",
     "assumptionsLimitations": "Objective weights and constraint sets are stakeholder inputs; results presented as decision support, never as unique optima.",
     "implementationFidelity": "The code creates four deterministic EAC scenarios. It is a useful scenario table but not an optimization algorithm.",
     "accreditationBasis": "Standard OR methods (LP: Dantzig; Pareto/regret: Savage) with textbook provenance. Validated by hand-checkable small instances in the test harness.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894: risk evaluation, treatment, monitoring, and review. The mapping supports governance alignment, not algorithm certification.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by What-If Scenario Matrix.\" Prohibited: \"The code implements the canonical What-If Scenario Matrix method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "bac",
      "ev",
      "ac",
      "cpi",
      "spi"
     ]
    },
    {
     "name": "Decision Sensitivity Matrix",
     "methodClass": "Decision Sensitivity Matrix",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Which decisions flip under which input changes - decision-stability regions.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Prescriptive layer: given fused statuses, explores trade-offs (LP, Pareto, regret). Uncertainty is carried in via scenario ranges and sensitivity matrices rather than re-estimated.",
     "explainability": "Decision/scenario trace: alternatives, assumptions, objectives, constraints or perturbations, scores, trade-offs, and sensitivity of the recommendation.",
     "oversightLevel": "RECOMMEND",
     "oversightDescription": "Recommend - presents an action option; named human authority must approve, modify, defer, or reject.",
     "failureModes": "Unstated objectives or weights; infeasible or omitted constraints; scenario ranges selected to force a result; recommendation interpreted as an instruction.",
     "assumptionsLimitations": "Objective weights and constraint sets are stakeholder inputs; results presented as decision support, never as unique optima.",
     "implementationFidelity": "The code ranks current deviations; it does not perturb inputs and measure decision-boundary changes. Rename or implement true decision sensitivity.",
     "accreditationBasis": "Standard OR methods (LP: Dantzig; Pareto/regret: Savage) with textbook provenance. Validated by hand-checkable small instances in the test harness.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894: risk evaluation, treatment, monitoring, and review. The mapping supports governance alignment, not algorithm certification.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by Decision Sensitivity Matrix.\" Prohibited: \"The code implements the canonical Decision Sensitivity Matrix method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "Pareto Frontier Analysis",
     "methodClass": "Pareto Frontier",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Non-dominated intervention set.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Prescriptive layer: given fused statuses, explores trade-offs (LP, Pareto, regret). Uncertainty is carried in via scenario ranges and sensitivity matrices rather than re-estimated.",
     "explainability": "Decision/scenario trace: alternatives, assumptions, objectives, constraints or perturbations, scores, trade-offs, and sensitivity of the recommendation.",
     "oversightLevel": "RECOMMEND",
     "oversightDescription": "Recommend - presents an action option; named human authority must approve, modify, defer, or reject.",
     "failureModes": "Unstated objectives or weights; infeasible or omitted constraints; scenario ranges selected to force a result; recommendation interpreted as an instruction.",
     "assumptionsLimitations": "Objective weights and constraint sets are stakeholder inputs; results presented as decision support, never as unique optima.",
     "implementationFidelity": "The code evaluates threshold booleans and does not construct a frontier of non-dominated alternatives. Rename or implement multi-alternative Pareto analysis.",
     "accreditationBasis": "Standard OR methods (LP: Dantzig; Pareto/regret: Savage) with textbook provenance. Validated by hand-checkable small instances in the test harness.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894: risk evaluation, treatment, monitoring, and review. The mapping supports governance alignment, not algorithm certification.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by Pareto Frontier Analysis.\" Prohibited: \"The code implements the canonical Pareto Frontier Analysis method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "cpi",
      "spi",
      "docRiskScore"
     ]
    },
    {
     "name": "Regret Minimization Index",
     "methodClass": "Regret Minimization",
     "defenseTier": "Tier 2 - Deterministic or calibrated indicator",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Minimax-regret ranking under scenario uncertainty (Savage).",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Prescriptive layer: given fused statuses, explores trade-offs (LP, Pareto, regret). Uncertainty is carried in via scenario ranges and sensitivity matrices rather than re-estimated.",
     "explainability": "Decision/scenario trace: alternatives, assumptions, objectives, constraints or perturbations, scores, trade-offs, and sensitivity of the recommendation.",
     "oversightLevel": "RECOMMEND",
     "oversightDescription": "Recommend - presents an action option; named human authority must approve, modify, defer, or reject.",
     "failureModes": "Unstated objectives or weights; infeasible or omitted constraints; scenario ranges selected to force a result; recommendation interpreted as an instruction.",
     "assumptionsLimitations": "Objective weights and constraint sets are stakeholder inputs; results presented as decision support, never as unique optima.",
     "implementationFidelity": "The expected-regret table is mathematically inspectable, but state probabilities and regret values are hard-coded and signal overrides bypass the stated minimax result. Defend only as a toy decision-analysis demonstration.",
     "accreditationBasis": "Standard OR methods (LP: Dantzig; Pareto/regret: Savage) with textbook provenance. Validated by hand-checkable small instances in the test harness.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 6 and 8-10; ISO/IEC 23894: risk evaluation, treatment, monitoring, and review. The mapping supports governance alignment, not algorithm certification.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by Regret Minimization Index.\" Prohibited: \"The code implements the canonical Regret Minimization Index method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "cpi",
      "spi",
      "bac"
     ]
    }
   ]
  },
  {
   "key": "portfolio-health-portfolio-health-suite",
   "num": "Portfolio Health",
   "name": "Portfolio Health Suite",
   "count": 5,
   "modules": [
    {
     "name": "Isolation Forest",
     "methodClass": "Isolation Forest",
     "defenseTier": "Tier 1 - Statistical / stochastic model",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "C",
     "assuranceDescription": "Refactor or rename before making a formal method claim",
     "engineeringProblem": "Portfolio-level multivariate anomaly detection over project feature vectors.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Unsupervised: learns the portfolio's joint feature distribution and scores projects by atypicality (Isolation Forest path length; distance-based outlier scores). Output is a relative anomaly score, not a classification with claimed error rates.",
     "explainability": "Portfolio trace: standardized feature vector, comparator cohort, distance or percentile rank, component contribution, leave-one-feature-out sensitivity, and small-n warning. Do not use Tree SHAP unless a real tree ensemble is implemented.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Very small portfolio; scaling sensitivity; mislabeled algorithm; outliers dominating centroid/stddev.",
     "assumptionsLimitations": "Requires 3+ projects (stated explicitly; modules abstain below that). Small-n portfolios give unstable scores - reported as exploratory signals, never as sole escalation triggers.",
     "implementationFidelity": "The backend computes a standardized distance from the portfolio centroid. It does not construct isolation trees and therefore is not an Isolation Forest implementation.",
     "accreditationBasis": "Isolation Forest (Liu et al. 2008) peer-reviewed. Validated by seeding a known-deviant synthetic project and confirming it ranks top of the anomaly ordering.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The current module is an exploratory proxy inspired by Isolation Forest.\" Prohibited: \"The code implements the canonical Isolation Forest method\" until the label/code mismatch is resolved.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [
      {
       "question": "n=12 projects - is ML defensible?",
       "answer": "Framed honestly: with small n these are exploratory ranking tools, never sole escalation triggers; the 3+-project abstention floor is coded, and the praxis states the small-n limitation explicitly. The defense is scope discipline, not sample size."
      }
     ],
     "requiredInputs": [
      "portfolioVectors"
     ]
    },
    {
     "name": "Portfolio Outlier Detection",
     "methodClass": "Portfolio Outlier",
     "defenseTier": "Tier 1 - Statistical / stochastic model",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Distance/density outlier scoring (complementary to PH.1's tree-based isolation).",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Unsupervised: learns the portfolio's joint feature distribution and scores projects by atypicality (Isolation Forest path length; distance-based outlier scores). Output is a relative anomaly score, not a classification with claimed error rates.",
     "explainability": "Portfolio trace: standardized feature vector, comparator cohort, distance or percentile rank, component contribution, leave-one-feature-out sensitivity, and small-n warning. Do not use Tree SHAP unless a real tree ensemble is implemented.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Small-n instability; cohort heterogeneity; feature scaling; data leakage; relative anomaly mistaken for project failure.",
     "assumptionsLimitations": "Requires 3+ projects (stated explicitly; modules abstain below that). Small-n portfolios give unstable scores - reported as exploratory signals, never as sole escalation triggers.",
     "implementationFidelity": "The backend ranks CPI and SPI percentiles. This is a descriptive portfolio outlier score, not a learned model.",
     "accreditationBasis": "Isolation Forest (Liu et al. 2008) peer-reviewed. Validated by seeding a known-deviant synthetic project and confirming it ranks top of the anomaly ordering.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Portfolio Outlier Detection method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "portfolioVectors"
     ]
    },
    {
     "name": "Signal Trajectory Classifier",
     "methodClass": "Trajectory Classifier",
     "defenseTier": "Tier 1 - Statistical / stochastic model",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Classifies multi-period signal trajectories (improving/stable/deteriorating) across the portfolio.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Unsupervised: learns the portfolio's joint feature distribution and scores projects by atypicality (Isolation Forest path length; distance-based outlier scores). Output is a relative anomaly score, not a classification with claimed error rates.",
     "explainability": "Portfolio trace: standardized feature vector, comparator cohort, distance or percentile rank, component contribution, leave-one-feature-out sensitivity, and small-n warning. Do not use Tree SHAP unless a real tree ensemble is implemented.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Small-n instability; cohort heterogeneity; feature scaling; data leakage; relative anomaly mistaken for project failure.",
     "assumptionsLimitations": "Requires 3+ projects (stated explicitly; modules abstain below that). Small-n portfolios give unstable scores - reported as exploratory signals, never as sole escalation triggers.",
     "implementationFidelity": "The backend uses a short CPI slope and threshold bands. It is a deterministic trajectory heuristic, not a trained classifier.",
     "accreditationBasis": "Isolation Forest (Liu et al. 2008) peer-reviewed. Validated by seeding a known-deviant synthetic project and confirming it ranks top of the anomaly ordering.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Signal Trajectory Classifier method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "signalHistory"
     ]
    },
    {
     "name": "Cross-project Pattern Detector",
     "methodClass": "Cross Project Pattern",
     "defenseTier": "Tier 1 - Statistical / stochastic model",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Detects shared deterioration patterns across projects (common-cause vs project-specific).",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Unsupervised: learns the portfolio's joint feature distribution and scores projects by atypicality (Isolation Forest path length; distance-based outlier scores). Output is a relative anomaly score, not a classification with claimed error rates.",
     "explainability": "Portfolio trace: standardized feature vector, comparator cohort, distance or percentile rank, component contribution, leave-one-feature-out sensitivity, and small-n warning. Do not use Tree SHAP unless a real tree ensemble is implemented.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Small-n instability; cohort heterogeneity; feature scaling; data leakage; relative anomaly mistaken for project failure.",
     "assumptionsLimitations": "Requires 3+ projects (stated explicitly; modules abstain below that). Small-n portfolios give unstable scores - reported as exploratory signals, never as sole escalation triggers.",
     "implementationFidelity": "The backend uses a fixed Euclidean-distance threshold to count similar projects. It is an explainable proximity rule, not a learned cross-project pattern model.",
     "accreditationBasis": "Isolation Forest (Liu et al. 2008) peer-reviewed. Validated by seeding a known-deviant synthetic project and confirming it ranks top of the anomaly ordering.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Cross-project Pattern Detector method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "portfolioVectors"
     ]
    },
    {
     "name": "Anomaly Score",
     "methodClass": "Anomaly Score",
     "defenseTier": "Tier 1 - Statistical / stochastic model",
     "asCodedTier": "Tier 2 - Deterministic or calibrated indicator",
     "assuranceClass": "B",
     "assuranceDescription": "Method-shaped, explainable demonstration requiring calibration or stronger validation",
     "engineeringProblem": "Composite portfolio anomaly index rolled into Portfolio Health.",
     "detProbSplit": "Deterministic input checks and arithmetic/rule computation followed by a deterministic band or decision rule. Uncertainty resides in measurement error, data completeness, threshold calibration, and source reliability rather than random sampling.",
     "uncertaintyMethod": "Unsupervised: learns the portfolio's joint feature distribution and scores projects by atypicality (Isolation Forest path length; distance-based outlier scores). Output is a relative anomaly score, not a classification with claimed error rates.",
     "explainability": "Portfolio trace: standardized feature vector, comparator cohort, distance or percentile rank, component contribution, leave-one-feature-out sensitivity, and small-n warning. Do not use Tree SHAP unless a real tree ensemble is implemented.",
     "oversightLevel": "INFORM_ONLY_FLAG",
     "oversightDescription": "Inform-only / flag - supplies uncertainty, conflict, or portfolio context; never a sole action trigger.",
     "failureModes": "Small-n instability; cohort heterogeneity; feature scaling; data leakage; relative anomaly mistaken for project failure.",
     "assumptionsLimitations": "Requires 3+ projects (stated explicitly; modules abstain below that). Small-n portfolios give unstable scores - reported as exploratory signals, never as sole escalation triggers.",
     "implementationFidelity": "The backend averages component scores into a composite index. It is not a calibrated probability of anomaly.",
     "accreditationBasis": "Isolation Forest (Liu et al. 2008) peer-reviewed. Validated by seeding a known-deviant synthetic project and confirming it ranks top of the anomaly ordering.",
     "validationRequired": "Verify formula and threshold boundaries; trace each input to provenance; run missing/stale/contradictory-data tests; calibrate bands on synthetic scenarios and, later, non-confidential field cases; confirm that the output abstains when required inputs are absent.",
     "standardsAlignment": "NIST AI RMF 1.0: MAP, MEASURE, and MANAGE; ISO/IEC 42001: clauses 7-10; ISO/IEC 23894 risk analysis/evaluation; W3C PROV-O for traceability where source records drive the indicator.",
     "permittedProhibitedClaims": "Allowed: \"The module is an explainable, literature-grounded demonstration of the Anomaly Score method family under stated assumptions.\" Prohibited: \"This is a calibrated or production-grade implementation\" unless validation evidence is added.",
     "governanceRole": "Enters the signal package with provenance, method version, input completeness, uncertainty/confidence, status, evidence metric, and abstention state; cannot authorize action without human judgment.",
     "defenseQuestions": [],
     "requiredInputs": [
      "portfolioVectors"
     ]
    }
   ]
  }
 ],
 "praxisOutline": {
  "heading": "The Praxis Behind the Platform",
  "lead": "Lin Opus Gubernatio is the proof-of-concept instrument for a Doctor of Engineering praxis on AI-driven probabilistic governance for public capital project controls. The research problem is the signal-to-action gap: modern platforms generate predictive signals faster than public-sector governance can responsibly act on them. PCEIF closes that gap by pairing every analytical signal with governed human judgment.",
  "chapters": [
   [
    "Introduction",
    "Frames public AEC capital programs as decision systems and defines the signal-to-action gap: why signal generation alone is not governance, and why public-sector constraints of accountability, auditability, fairness, and procurement shape the design."
   ],
   [
    "Literature, Theory, Standards, and Technology",
    "Grounds the framework in earned value management and its limits, predictive project controls, public-sector AI governance, and theoretical lenses including bounded rationality, sociotechnical systems, procedural justice, and human judgment under multi-signal uncertainty: automation bias, algorithm aversion, anchoring, alert fatigue, and trust calibration."
   ],
   [
    "Research Methodology",
    "Design Science Research: the framework and instrument are built as artifacts and evaluated through structured practitioner validation rather than statistical hypothesis testing on outcomes."
   ],
   [
    "The PCEIF Governance Framework",
    "The governance architecture itself: signal packages routed to human review, conflict kept visible, and the Human Judgment Record with mandatory rationale capture, no silent overrides, an override taxonomy, and a judgment ledger whose patterns become learning inputs."
   ],
   [
    "Analytical Module Taxonomy",
    "The full capability taxonomy behind this handbook: ten project categories plus the Portfolio Health suite, each documented with its governance role, its human judgment risks, its module register, and validation questions."
   ],
   [
    "The Proof-of-Concept Instrument",
    "Lin Opus Gubernatio as built: document ingestion, signal extraction, probabilistic computation, evidence fusion, and the executive interfaces that surface every red signal regardless of overall status."
   ],
   [
    "Practitioner Validation and Refinement",
    "Twelve or more professionals across owner, contractor, and consultancy roles evaluate the framework qualitatively; their feedback drives framework refinement and defines the boundary of claims."
   ]
  ],
  "judgmentLayer": "Every capability in this handbook outputs evidence, not instructions. A module must expose its source, abstain when required inputs are absent, and enter a signal package that a project manager may accept, override, defer, or escalate. The judgment and its rationale become part of the audit record. Analytical transparency plus governed professional discretion is the design thesis of the entire praxis."
 },
 "governanceAxis": [
  [
   "NIST AI RMF",
   "Govern: controlled module registry and human Judgment Record. Map: tier taxonomy with per-capability purpose and oversight class. Measure: band harness, calibration probes, extraction audit agreement, seeded-detection tests. Manage: escalation logic, abstention discipline, human concur or override."
  ],
  [
   "Explainable AI principles",
   "Every capability declares its explanation method: rule traces and evidence chains for deterministic logic, posterior summaries for Bayesian estimation, score decompositions for anomaly detection. Knowledge limits are implemented literally as abstention on missing inputs."
  ],
  [
   "AI management and risk standards",
   "Versioned backend releases, single-change pull requests, honest commit history, no silent failures, and single-source status derivation constitute the lifecycle management evidence."
  ],
  [
   "Model cards and datasheets",
   "Each capability entry in this handbook is its model card; the 27-document ingestion manifest with raw-facts-only authoring rules is the dataset datasheet for the synthetic corpus."
  ],
  [
   "Provenance",
   "Every extracted signal traces from field to source document to source passage; upload events are preserved across resets and audit-trail completeness is itself scored."
  ]
 ],
 "accreditation": "Accreditation is layered along two axes. Statistical axis: every method traces to a citable primary source or published practice standard; every threshold is exogenous or calibrated and proven by an automated band harness against live code; every stochastic capability carries a stated validation test; fusion behavior is verified end to end by the calibration probe protocol. Governance axis: the platform is documented as a governed system of systems with per-capability explainability methods, oversight classifications, failure-mode registers, provenance chains, and a human judgment record gating every recommendation. No capability claims a statistical property it does not have."
};
