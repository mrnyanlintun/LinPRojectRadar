"""
Run 17 findings, keyed by v0.5 Module_ID_Text_Key.

EVERY ENTRY HERE IS BACKED BY AN EXECUTED TEST in test_run17_scientific_methods.py. A module with
no entry is written to the results matrix as NOT_REACHED_IN_THIS_RUN by build_artifacts.py. That
separation is deliberate: nothing in this file may be added on the strength of reading the code
alone without the corresponding named test having run.

The vocabulary is the owner specification's. In particular "validated" appears nowhere as a
verdict; empirical_validation_status is its own column and is NOT_DONE almost everywhere, which
is the honest answer for a controlled research instrument with no labelled outcome corpus.
"""

from __future__ import annotations

METHOD_CARD_DEFAULTS: dict[str, object] = {
    "module_id": "",
    "module_name": "",
    "category": "",
    "code_id": "",
    "basis_class": "",
    "canonical_or_declared_method": "",
    "primary_source": "",
    "supporting_sources": [],
    "formal_definition": "",
    "required_structure": "",
    "required_inputs": [],
    "input_units": "",
    "minimum_cardinality": "",
    "valid_domain": "",
    "parameters": [],
    "parameter_provenance_requirement": "",
    "stochastic_or_deterministic": "deterministic",
    "output_definition": "",
    "known_answer_oracle": "",
    "invariants": [],
    "metamorphic_properties": [],
    "missing_input_behavior": "",
    "invalid_input_behavior": "",
    "calibration_requirement": "",
    "threshold_status": "",
    "empirical_validation_requirement": "",
    "lineage_notes": "",
    "permitted_claim": "",
    "prohibited_claim": "",
    "current_code_location": "",
    "current_implementation_summary": "",
    "scientific_disposition": "",
    "evidence": "",
}

#: The literature and authority ledger. `retrieved` records honestly whether the primary source
#: itself was read in this container: Run 15 established that several publisher PDFs are refused
#: by the egress proxy. NOT_RETRIEVED_IN_CONTAINER means the identifier is carried from the
#: supervisory specification and the theory used is the supervisory specification's own
#: statement of it, which section 7 of the owner prompt makes the controlling authority.
SOURCE_LEDGER: list[dict[str, str]] = []

#: Findings, keyed by Module_ID_Text_Key. Populated by the run as each module is executed.
FINDINGS: dict[str, dict[str, object]] = {}


def _src(sid, citation, doi, tier, retrieved, note, modules):
    SOURCE_LEDGER.append({"source_id": sid, "citation": citation, "doi_or_identifier": doi,
                          "source_tier": tier, "retrieved": retrieved,
                          "provenance_note": note, "used_for_modules": modules})


#: PROVENANCE HONESTY. Run 15 established that several publisher PDFs are refused by this
#: container's egress proxy. Where the primary text was not retrieved here, `retrieved` says
#: NOT_RETRIEVED_IN_CONTAINER and the theory used is the supervisory specification's own
#: statement of the method, which section 7 of the Run-17 prompt makes the controlling authority
#: for theory. Nothing below implies a primary source was read when it was not.
_NR = "NOT_RETRIEVED_IN_CONTAINER"
_SPEC = "Run-17 supervisory method specification (tier 1, controlling for theory)"

_src("S1", "Run-17 supervisory method specification, sections 10 to 20", "n/a", "tier 1",
     "SUPPLIED_IN_PROMPT",
     "The controlling authority for theory in this run. Every oracle equation is transcribed "
     "from it and self-proved against its worked answers.",
     "all 100")
_src("S2", "Page, E. S., Continuous Inspection Schemes, Biometrika 41 (1954), 100-115",
     "10.1093/biomet/41.1-2.100", "tier 2", _NR,
     "Identifier carried from the supervisory specification; the CUSUM recursion tested is the "
     "specification's own statement of the tabular standardised form.", "1.2")
_src("S3", "Kalman, R. E., A New Approach to Linear Filtering and Prediction Problems, 1960",
     "10.1115/1.3662552", "tier 2", _NR,
     "Identifier carried from the supervisory specification; the scalar random-walk recursion "
     "tested is the specification's own statement.", "1.4")
_src("S4", "Lipke, W., Schedule Is Different, The Measurable News (2003); Lipke et al. (2009)",
     "10.1016/j.ijproman.2008.02.009", "tier 2", _NR,
     "Identifier carried from the supervisory specification; the earned-schedule interpolation "
     "tested is the specification's own statement.", "1.6")
_src("S5", "PMI, A Guide to the Project Management Body of Knowledge, 6th ed., 2017, 7.4.2.2; "
     "PMI Practice Standard for Earned Value Management, 2nd ed., 2011",
     "PMBOK 6e / EIA-748", "tier 2", _NR,
     "Cited in production for the definitional band boundaries of 1.7 and 1.8. Run 17 verified "
     "that the citation is recorded in code together with the sentence stating what it does "
     "NOT establish; it did not re-retrieve the standard.", "1.7, 1.8")
_src("S6", "Christensen, D. S. and Heise, S. R., Cost Performance Index Stability, National "
     "Contract Management Journal 25(1), 1993, 7-15", "n/a", "tier 3", _NR,
     "The source of the 0.10 stability figure production applies BY STATED INFERENCE to the "
     "1.10 and -11.11 per cent boundaries. The inference is declared in code rather than hidden; "
     "Run 17 classifies the resulting boundaries as LITERATURE_INFERRED, not LITERATURE_EXACT.",
     "1.7, 1.8")
_src("S7", "Shafer, G., A Mathematical Theory of Evidence, Princeton, 1976", "n/a", "tier 2",
     _NR,
     "Identifier carried from the supervisory specification; the combination rule, belief, "
     "plausibility and the reliability discount tested are the specification's own statements.",
     "7.1")
_src("S8", "Liu, F. T., Ting, K. M. and Zhou, Z.-H., Isolation Forest, ICDM 2008, 413-422",
     "10.1109/ICDM.2008.17", "tier 2", _NR,
     "Identifier carried from the supervisory specification and already cited verbatim in "
     "server/app/simulation/isolation_forest.py. Run 17 verified the implemented definition "
     "against the specification's statement of c(n) and s(x,n), using an EXACT harmonic number "
     "as an independent check on production's ln+gamma estimate.", "PH.1, PH.5")
_src("S9", "NIST AI Risk Management Framework 1.0", "10.6028/NIST.AI.100-1", "tier 4", _NR,
     "Governance and test-evaluation-verification-validation context only. It certifies no "
     "algorithm, and no module disposition in this run rests on it.", "governance context")


def _f(mid, **kw):
    """One module's finding. Every entry is backed by named checks in the Run-17 suite."""
    base = {
        "operational_activation": "ADVISORY_ONLY",
        "voting_status": "non-voting",
        "canonical_structure_required": "yes",
        "implementation_verified": "yes",
        "known_answer_pass": "yes",
        "boundary_pass": "yes",
        "missingness_pass": "yes",
        "invariant_pass": "yes",
        "stochastic_diagnostics_pass": "n/a",
        "reproducibility_pass": "yes",
        "parameter_provenance_status": "NOT_SOURCED",
        "calibration_status": "NOT_CALIBRATED",
        "threshold_status": "HEURISTIC_UNCALIBRATED",
        "empirical_validation_status": "NOT_DONE",
        "regulatory_snapshot": "n/a",
        "cat9_qualification_status": "RAW_UNQUALIFIED_INPUT",
        "lineage_status": "SHARED_EVM_INPUT_VECTOR",
        "production_change_made": "no",
        "evidence_paths": "server/tools/test_run17_scientific_methods.py; "
                          "server/tools/run17/coverage.csv",
    }
    base.update(kw)
    FINDINGS[mid] = base


# --------------------------------------------------------------------------- Category 1
_f("1.1", module_name="Monte Carlo EAC", category="1",
   basis_class="C. LITERATURE_SUPPORTED_ADAPTATION",
   primary_method_source="S1 supervisory specification 1.1; Beta-PERT adaptation frozen by the "
                         "Run-10 Monte Carlo fixture",
   canonical_structure_present="yes",
   stochastic_diagnostics_pass="yes",
   scientific_disposition="METHOD_PASS_CALIBRATION_PENDING",
   finding_summary="Samples a declared stochastic final-cost model, reports an iteration count, "
                   "a named spread driver and P50 and P80 read off the simulated distribution, "
                   "and reproduces exactly under a fixed scenario and period seed while moving "
                   "under a different one. The Beta-PERT mean identity was verified "
                   "independently at the specification's own worked figures. What is absent is "
                   "provenance for the distribution parameters and any dependence structure.",
   required_next_action="Source the Beta-PERT parameters and state whether the uncertain "
                        "variables are assumed independent.",
   test_names="1.1 positive/structure/invariant/boundary/reproducibility/stochastic")

_f("1.2", module_name="CUSUM Anomaly Monitor", category="1",
   basis_class="B. ESTABLISHED_CANONICAL_METHOD",
   primary_method_source="S2 Page (1954) via S1",
   canonical_structure_present="yes",
   calibration_status="CALIBRATED_SYNTHETIC_RUN15_FROZEN",
   threshold_status="EMPIRICALLY_CALIBRATED_ON_SYNTHETIC_DATA",
   scientific_disposition="METHOD_PASS_CALIBRATION_PENDING",
   finding_summary="The two-sided tabular standardised recursion was reproduced independently "
                   "and behaves as the frozen Run-15 design requires: it signals on a persistent "
                   "level shift and does not signal on an isolated one-period spike, and both "
                   "statistics stay non-negative. The Run-15 calibration record is present in "
                   "the repository and was NOT retuned by this run. The calibration is "
                   "synthetic, so the operating point is not empirically established.",
   required_next_action="Nothing in Run 18. Retuning requires a governed non-synthetic study.",
   test_names="1.2 frozen-record/known-answer/spike/boundary/invariant")

_f("1.3", module_name="Bayesian EAC", category="1",
   basis_class="B. ESTABLISHED_CANONICAL_METHOD",
   primary_method_source="S1 supervisory specification 1.3, normal-normal conjugate update",
   canonical_structure_present="yes",
   parameter_provenance_status="DESIGNED_CONSTANTS_NO_SOURCE",
   scientific_disposition="METHOD_PASS_CALIBRATION_PENDING",
   finding_summary="The posterior reproduces the normal-normal identity exactly at a hand "
                   "calculation, lies between the prior and likelihood means, and its variance "
                   "is smaller than either input variance. The prior is centred on the budget "
                   "with a standard deviation of fifteen per cent of it and the likelihood "
                   "variance is a designed function of the cost index; neither has a source. "
                   "The algebra is verified; a calibrated-Bayesian claim is not available.",
   required_next_action="Source or elicit the prior and the likelihood variance, or restate the "
                        "module as a designed sensitivity rather than a Bayesian forecast.",
   test_names="1.3 known-answer/structure/boundary/missingness/invariant")

_f("1.4", module_name="Kalman Filter SPI Smoother", category="1",
   basis_class="B. ESTABLISHED_CANONICAL_METHOD",
   primary_method_source="S3 Kalman (1960) via S1",
   canonical_structure_present="yes",
   parameter_provenance_status="FIXED_Q_AND_R_NO_SOURCE",
   scientific_disposition="METHOD_PASS_CALIBRATION_PENDING",
   finding_summary="The scalar random-walk recursion matches an independent implementation of "
                   "the canonical predict-update step, the specification's worked step "
                   "reproduces exactly, the smoothed estimate stays inside the observed range "
                   "and a constant series is a fixed point. Process and measurement noise are "
                   "the fixed literals 0.01 and 0.1 with no provenance and no calibration "
                   "procedure, which is exactly the case the specification caps at "
                   "METHOD_PASS_CALIBRATION_PENDING.",
   required_next_action="Estimate or source Q and R, or declare them an owner policy choice.",
   test_names="1.4 known-answer/spec-step/boundary/missingness/invariant/metamorphic")

_f("1.5", module_name="ARIMA CPI Forecast", category="1",
   basis_class="D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
   primary_method_source="S1 supervisory specification 1.5, Box-Jenkins framework",
   canonical_structure_present="no",
   implementation_verified="yes",
   scientific_disposition="METHOD_LABEL_MISMATCH",
   finding_summary="What runs is a single autoregressive coefficient on first differences, "
                   "estimated by one lag-one ratio and clamped to plus or minus 0.9, with the "
                   "forecast being the last observation plus phi times the last difference. A "
                   "constant series correctly forecasts itself and the domain guards hold. But "
                   "the result object carries no differencing order, no moving-average terms, "
                   "no identification or model-selection rule, no residual diagnostics and no "
                   "forecast interval, so the declared ARIMA(p,d,q) contract is not represented. "
                   "The module carries NO proxy qualifier, so it presents under the full "
                   "canonical name while implementing a fixed AR(1)-on-differences heuristic.",
   required_next_action="P3: either add a proxy qualifier naming what it computes, or build the "
                        "identification, diagnostics and interval the registered name implies.",
   test_names="1.5 positive/structure x7/boundary x2/invariant")

_f("1.6", module_name="Earned Schedule", category="1",
   basis_class="D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
   primary_method_source="S4 Lipke (2003, 2009) via S1",
   canonical_structure_present="no",
   scientific_disposition="METHOD_LABEL_MISMATCH",
   finding_summary="Earned Schedule requires the cumulative planned-value curve and an "
                   "interpolation into it. The module computes actual percent complete over "
                   "planned percent complete, which the supervisory specification states is not "
                   "Earned Schedule. The discriminating test was run: the canonical measure "
                   "moves by more than a tenth when the planned-value curve is re-shaped at "
                   "constant earned value and actual time, and the implemented measure cannot "
                   "move at all because no curve reaches it. No proxy qualifier is carried, so "
                   "the module presents under the canonical name.",
   required_next_action="P3 now, P1 if the module is ever brought into voting: either rename to "
                        "a progress ratio or ingest a planned-value curve.",
   test_names="1.6 positive/known-answer/structural-discriminator x2/boundary/missingness")

_f("1.7", module_name="TCPI", category="1",
   basis_class="A. STANDARDIZED_PROJECT_CONTROL_IDENTITY",
   operational_activation="ENABLED_QUALIFIED", voting_status="VOTING",
   primary_method_source="S5 PMI PMBOK 6e 7.4.2.2 and PMI EVM Practice Standard",
   canonical_structure_present="yes",
   parameter_provenance_status="DEFINITIONAL",
   calibration_status="NOT_APPLICABLE_IDENTITY",
   threshold_status="LITERATURE_EXACT_AT_1.00; LITERATURE_INFERRED_AT_1.10",
   scientific_disposition="SCIENTIFIC_PASS",
   finding_summary="The budget-basis identity reproduces the specification's worked answer "
                   "exactly, states its target basis in the finding, is invariant under a "
                   "change of currency scale, and refuses every out-of-domain shape tested "
                   "including the negative actual cost that previously banded Green and the "
                   "zero remaining budget that previously manufactured a Red. The 1.00 boundary "
                   "is definitional and the source states it. The 1.10 boundary applies the "
                   "Christensen and Heise 0.10 figure BY STATED INFERENCE, which is recorded in "
                   "code together with the sentence saying the measure's error rates are "
                   "unmeasured. This is implementation verification of an identity, not "
                   "empirical validation of the band.",
   required_next_action="None. The band's false-positive and false-negative rates remain "
                        "unmeasured and no surface may call it validated.",
   test_names="1.7 known-answer/structure/boundary x3/missingness/metamorphic/threshold x2")

_f("1.8", module_name="Variance at Completion", category="1",
   basis_class="A. STANDARDIZED_PROJECT_CONTROL_IDENTITY",
   operational_activation="ENABLED_QUALIFIED", voting_status="VOTING",
   primary_method_source="S5 PMI PMBOK 6e 7.4.2.2",
   canonical_structure_present="yes",
   parameter_provenance_status="DEFINITIONAL",
   calibration_status="NOT_APPLICABLE_IDENTITY",
   threshold_status="LITERATURE_EXACT_AT_0_PCT; LITERATURE_INFERRED_AT_-11.11_PCT",
   scientific_disposition="SCIENTIFIC_PASS",
   finding_summary="The identity reproduces the specification's worked answer, the index-based "
                   "forecast convention is explicitly recorded in the band citation rather than "
                   "left implicit, a unit cost index gives exactly zero variance, the result is "
                   "scale invariant, and a non-positive cost index is refused in both "
                   "directions. The minus 11.11 per cent boundary is the exact restatement of a "
                   "0.90 cost index, so a sourced statement about the index transfers to it "
                   "without stretching; the transfer is nonetheless an inference and is "
                   "declared as one, including the citation's own unenforced precondition that "
                   "the project be past twenty per cent complete.",
   required_next_action="None. The unenforced twenty-per-cent precondition stays on the record.",
   test_names="1.8 known-answer/structure/boundary x2/missingness/invariant/metamorphic")

_f("1.9", module_name="Budget Execution Rate", category="1",
   basis_class="D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
   primary_method_source="S1 supervisory specification 1.9 (no universal canonical method)",
   canonical_structure_present="n/a",
   scientific_disposition="CORRECT_PROXY_ONLY",
   finding_summary="Actual cost over a progress-scaled budget, verified against an independent "
                   "hand calculation, scale invariant, and refusing negative cost and "
                   "out-of-range progress rather than banding them Green. There is no approved "
                   "time-phased expenditure profile anywhere in the input contract, so this is "
                   "the narrower proxy the specification permits, not a comparison against an "
                   "approved spend curve. The module already carries a proxy qualifier saying "
                   "so. Its bands have no literature basis and none is claimed.",
   required_next_action="P2: the bands 1.05, 1.10 and 1.20 are unsourced and should be declared "
                        "owner policy or calibrated.",
   test_names="1.9 known-answer/structure/boundary x2/missingness/metamorphic/label")

_f("1.10", module_name="Regression to Mean CPI", category="1",
   basis_class="C. LITERATURE_SUPPORTED_ADAPTATION",
   primary_method_source="S1 supervisory specification 1.10",
   canonical_structure_present="no",
   scientific_disposition="MISSING_CANONICAL_DATA_STRUCTURE",
   finding_summary="The shrinkage arithmetic is correct: the result matches an independent "
                   "computation of w times the current index plus one minus w times the "
                   "reference mean, lies between the two, and a flat history is its own fixed "
                   "point. But the reference mean is the PROJECT'S OWN history, not an outside "
                   "reference class, and no reference-population field exists on the result. "
                   "Reference-class shrinkage needs a population the project is not a member "
                   "of; there is none here, so the canonical structure cannot be represented. "
                   "The weight is a fixed one half rather than an estimated coefficient.",
   required_next_action="P2: either supply a governed reference population and estimate w, or "
                        "rename to self-shrinkage of the project's own history.",
   test_names="1.10 known-answer/structure x2/boundary/missingness/invariant x2/parameter")

_f("1.11", module_name="ICE Ratio", category="1",
   basis_class="D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
   primary_method_source="S1 supervisory specification 1.11",
   canonical_structure_present="no",
   lineage_status="BOTH_ESTIMATES_FROM_ONE_INPUT_VECTOR",
   scientific_disposition="METHOD_LABEL_MISMATCH",
   finding_summary="The division is correct and identical forecasts give exactly one. The "
                   "independence claim is what fails. Both quantities are deterministic "
                   "functions of the same four inputs: budget over cost index, and actual cost "
                   "plus remaining budgeted work. The independence test was run explicitly, "
                   "perturbing the shared cost index and showing one forecast moves while the "
                   "other cannot, and confirming no independent-source field exists anywhere on "
                   "the result. A reconciliation index needs two analytically or "
                   "provenance-independent estimates; this has one input vector and two "
                   "formulas. The module carries no proxy qualifier.",
   required_next_action="P3: rename to an internal EAC-formula divergence index, or ingest a "
                        "genuinely independent estimate.",
   test_names="1.11 known-answer/independence x2/boundary x2/missingness/invariant")


# --------------------------------------------------------------------------- Category 6
_CAT6_NOTE = ("Category 6 must synthesise already qualified signal states and must not vote on "
              "raw cost, schedule or document-risk values. All four ensembles read the assembled "
              "primary signals directly, so the Qualified Evidence boundary is not enforced.")

_f("6.1", module_name="Conservative Dominance", category="6",
   basis_class="E. PCEIF_GOVERNANCE_SYNTHESIS_RULE",
   primary_method_source="S1 supervisory specification 6.1",
   canonical_structure_present="yes", invariant_pass="partial",
   known_answer_pass="no",
   threshold_status="OWNER_POLICY_UNVERSIONED",
   scientific_disposition="IMPLEMENTATION_DEFECT",
   finding_summary="THE DEFINING PROPERTY DOES NOT HOLD. Conservative dominance is the worst "
                   "credible qualified signal. Production escalates only when two signals are "
                   "Red, or when a breached control chart coincides with a Red forecast; a "
                   "single Red signal among three Greens returns Amber. The specification's own "
                   "sentence is that one severe qualified signal cannot disappear inside an "
                   "average, and here it disappears into a three-arm ladder. What DOES hold: "
                   "the result is permutation invariant across signal slots, monotone "
                   "non-decreasing as one signal worsens, two Reds do escalate, an absent "
                   "signal does not read Green, an unknown string does not read Green, and the "
                   "module refuses entirely without a package. The module is non-voting, but it "
                   "is the input to the governance layer's authority and action selection.",
   required_next_action="P0B in the Run-18 queue. A lone Red currently selects routine early "
                        "warning rather than escalation.",
   test_names="6.1 positive x2/known-answer x2/invariant x2/missingness x2/boundary")

_f("6.2", module_name="Weighted Voting", category="6",
   basis_class="E. PCEIF_GOVERNANCE_SYNTHESIS_RULE",
   primary_method_source="S1 supervisory specification 6.2",
   canonical_structure_present="no",
   parameter_provenance_status="UNSOURCED_LITERAL_WEIGHTS",
   threshold_status="OWNER_POLICY_UNVERSIONED",
   lineage_status="DOUBLE_COUNTS_CORRELATED_TRANSFORMS",
   scientific_disposition="METHOD_LABEL_MISMATCH",
   finding_summary="The canonical form is a weighted ordinal severity score. Production instead "
                   "accumulates weight into per-band buckets and reports whichever BAND holds "
                   "the most weight, which is a weighted plurality, not a weighted score: no "
                   "score field exists on the result. The weights 1.5, 1.0, 0.6 and 1.5 are "
                   "bare literals with no source, no version and no provenance field. Every "
                   "simulation module contributes its own 0.6 regardless of whether it is a "
                   "fresh observation or another transform of the same cost index, and the "
                   "lineage test confirmed that duplicating one signal moves the tally. One "
                   "genuinely good property: an unrecognised status casts no vote at all.",
   required_next_action="P2 for weight provenance, P3 for the label. " + _CAT6_NOTE,
   test_names="6.2 positive/structure/known-answer/provenance/lineage/missingness/boundary")

_f("6.3", module_name="Majority Rules", category="6",
   basis_class="E. PCEIF_GOVERNANCE_SYNTHESIS_RULE",
   primary_method_source="S1 supervisory specification 6.3",
   canonical_structure_present="yes",
   threshold_status="OWNER_POLICY_UNVERSIONED",
   lineage_status="DOUBLE_COUNTS_CORRELATED_TRANSFORMS",
   scientific_disposition="METHOD_PASS_CALIBRATION_PENDING",
   finding_summary="The count reproduces the specification's worked answer, and the tie policy "
                   "is both explicit in effect and conservative: an even split resolves to the "
                   "more severe state, which was verified directly. Missing signals are not "
                   "counted as Green and unknown strings are not counted at all. Two gaps, "
                   "neither arithmetic. No minimum quorum is declared, so a single surviving "
                   "signal decides the ensemble, which was demonstrated. And duplicating one "
                   "signal changes the count, so correlated transforms of one piece of evidence "
                   "each get a vote.",
   required_next_action="P2: declare a quorum and a lineage rule. " + _CAT6_NOTE,
   test_names="6.3 known-answer/boundary x2/missingness x2/quorum/lineage")

_f("6.4", module_name="Worst-N-of-M", category="6",
   basis_class="E. PCEIF_GOVERNANCE_SYNTHESIS_RULE",
   primary_method_source="S1 supervisory specification 6.4",
   canonical_structure_present="no", invariant_pass="no",
   threshold_status="OWNER_POLICY_UNVERSIONED",
   scientific_disposition="IMPLEMENTATION_DEFECT",
   finding_summary="This is not Worst-N-of-M and it does not collapse to Conservative "
                   "Dominance either. N is never predeclared; the rule fires Red when the Red "
                   "COUNT reaches ceil(0.3 M) and Amber when the Amber count reaches "
                   "ceil(0.4 M). Because the bar is proportional to M, enlarging M with benign "
                   "evidence raises it: three signals carrying one Red report Red, and adding a "
                   "single Green module to the same unchanged adverse finding downgrades it to "
                   "Yellow. That was demonstrated directly. Under any genuine worst-N-of-M rule "
                   "the selected worst N are unchanged by adding a benign signal, so the answer "
                   "cannot improve. All-Green correctly gives Green and unknown statuses are "
                   "dropped from the denominator rather than diluting it.",
   required_next_action="P0B in the Run-18 queue: adverse evidence is diluted by the arrival of "
                        "unrelated benign evidence. " + _CAT6_NOTE,
   test_names="6.4 positive/structure/invariant x2/known-answer/missingness/boundary")

# --------------------------------------------------------------------------- Category 7
_f("7.1", module_name="Dempster-Shafer", category="7",
   basis_class="B. ESTABLISHED_CANONICAL_METHOD",
   primary_method_source="S7 Shafer via S1",
   canonical_structure_present="yes",
   parameter_provenance_status="DESIGNED_MASS_TABLE_NO_ELICITATION",
   lineage_status="DEPENDENCE_ASSUMPTION_UNENFORCED",
   scientific_disposition="METHOD_PASS_CALIBRATION_PENDING",
   finding_summary="The combination rule is canonical and was verified against an independent "
                   "implementation over explicit focal SETS. Ignorance is handled correctly: "
                   "the frame intersects every state instead of conflicting with it, so the "
                   "specification's worked combination reproduces exactly at mass 0.8 on the "
                   "singleton, 0.2 on the frame and a conflict coefficient of zero. Belief and "
                   "plausibility, the reliability discount and its normalisation, commutativity "
                   "and the admissibility of every declared mass row all hold. Total conflict "
                   "is flagged with a coefficient of one and yields no decidable verdict, since "
                   "every state carries equal mass. TWO REAL LIMITS. The mass table is a set of "
                   "designed constants with no elicitation or calibration behind them. And "
                   "Dempster's rule assumes independent sources: combining a source with an "
                   "identical copy sharpens belief beyond the original, which is exactly the "
                   "hazard when several correlated transforms of one cost index are combined.",
   required_next_action="P2: elicit or source the mass table; declare and enforce a "
                        "source-independence rule before combination.",
   test_names="7.1 known-answer x5/implementation x3/invariant x4/boundary x2/lineage/missingness")

# --------------------------------------------------------------------------- Portfolio Health
_f("PH.1", module_name="Isolation Forest", category="PH",
   basis_class="B. ESTABLISHED_CANONICAL_METHOD",
   primary_method_source="S8 Liu, Ting and Zhou (2008)",
   canonical_structure_present="yes",
   stochastic_diagnostics_pass="yes",
   parameter_provenance_status="PAPER_DEFAULTS_100_TREES_256_SUBSAMPLE",
   calibration_status="CALIBRATED_SYNTHETIC_RUN15_FROZEN",
   threshold_status="EMPIRICALLY_CALIBRATED_ON_SYNTHETIC_DATA",
   lineage_status="OWN_REFERENCE_COHORT_EXCLUDES_SCORED_PROJECT",
   scientific_disposition="METHOD_PASS_CALIBRATION_PENDING",
   finding_summary="Run 15's claim was checked rather than believed, and it holds. This is a "
                   "genuine isolation forest: random attribute, split drawn uniformly between "
                   "the observed minimum and maximum, height limit at the log of the subsample, "
                   "external-node path-length correction, ensemble mean and the canonical "
                   "score transform, all verified against an independently computed c(n) using "
                   "the EXACT harmonic number. The normaliser sits below the exact value by the "
                   "documented amount, because production uses the paper's own ln plus gamma "
                   "estimate, and the direction of that deviation was checked too. The scored "
                   "project is excluded from its own reference cohort. On continuously "
                   "distributed features one forest ranks a planted anomaly well above a "
                   "central inlier, and the inlier sits below the one-half no-anomaly level the "
                   "paper states. Scores reproduce exactly and move under a different seed. "
                   "TWO LIMITS FOUND. On a degenerate cohort, where document risk and progress "
                   "are constant and the cost index takes three distinct values, an extreme "
                   "outlier and a central inlier receive the SAME score, because splits are "
                   "drawn between the reference minimum and maximum so an out-of-range point "
                   "can never be separated by one split. And because each project is scored "
                   "against a forest that excludes itself, two projects' scores come from "
                   "different forests and are not strictly comparable. The 0.576 threshold was "
                   "frozen on synthetic data and was NOT retuned by this run.",
   required_next_action="P2: state the minimum feature variance below which the detector "
                        "abstains; record that cross-project score comparison is not supported.",
   test_names="PH.1 positive/structure x2/known-answer x5/invariant x2/reproducibility/"
              "stochastic/boundary x2/threshold")

_f("PH.2", module_name="Portfolio Outlier Detection", category="PH",
   basis_class="D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
   primary_method_source="S1 supervisory specification PH.2",
   canonical_structure_present="yes",
   scientific_disposition="CORRECT_PROXY_ONLY",
   finding_summary="A percentile rank on cost and schedule performance, recomputed "
                   "independently and matching. The declared orientation is performance rather "
                   "than risk, so the worst project takes the lowest rank, and the extreme "
                   "project does land in the most extreme tail. A better-performing project "
                   "takes a higher rank, the rank is bounded, it is invariant to cohort order, "
                   "and a cohort below the declared minimum is refused. The module already "
                   "carries a proxy qualifier stating it is an empirical percentile rank rather "
                   "than a trained model, which is the honest label. Its bands are uncalibrated "
                   "and its small-n behaviour is unvalidated, which the qualifier also says.",
   required_next_action="P2: calibrate or declare as owner policy the 0.15, 0.30 and 0.45 bands.",
   test_names="PH.2 positive/known-answer x2/invariant x2/metamorphic/boundary/label")

_f("PH.3", module_name="Signal Trajectory Classifier", category="PH",
   basis_class="D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
   primary_method_source="S1 supervisory specification PH.3",
   canonical_structure_present="yes",
   scientific_disposition="CORRECT_PROXY_ONLY",
   finding_summary="The slope is computed over INTERVALS rather than observations and matches "
                   "an independent least-squares slope on the specification's own worked series "
                   "at minus 0.1 per period. The trap the specification warns about, dividing "
                   "an endpoint change by the number of observations, is not present: the Run-14 "
                   "correction holds. A flat history gives exactly zero, reversing the series "
                   "exactly reverses the sign, a deteriorating slope is classified adversely, "
                   "and the module abstains BY ABSENCE rather than showing a colour when there "
                   "is no usable history or only one observation. It is a deterministic "
                   "thresholded slope and is not a learned classifier; no surface should call "
                   "it one. Its bands have no source.",
   required_next_action="P2: source or declare as owner policy the 0.01 and 0.03 band edges.",
   test_names="PH.3 positive/known-answer x2/invariant/metamorphic/missingness/boundary")

_f("PH.4", module_name="Cross-project Pattern Detector", category="PH",
   basis_class="D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
   primary_method_source="S1 supervisory specification PH.4",
   canonical_structure_present="partial",
   parameter_provenance_status="BARE_LITERAL_MATCH_RADIUS",
   scientific_disposition="OWNER_DECISION_REQUIRED",
   finding_summary="The structural oracles hold: an identical project is matched, a uniformly "
                   "distant cohort yields no match, the result is invariant to cohort order, "
                   "and matching a healthy peer correctly reports Green rather than implying "
                   "distress, which was the Run-14 correction. But there is no explicit pattern "
                   "definition. The similarity operator is a bare Euclidean distance under a "
                   "literal radius of 0.15 with no provenance and no threshold field on the "
                   "result, and it silently ignores the FOURTH feature of the declared "
                   "four-element vector, so the declared feature vector and the operator's "
                   "domain disagree. The specification directs this case to owner decision "
                   "rather than to a scientific verdict.",
   required_next_action="OWNER DECISION: define the pattern this module is meant to detect, the "
                        "features it spans and the radius, or rename it a near-neighbour count.",
   test_names="PH.4 positive/known-answer x2/metamorphic/structure/invariant/parameter")

_f("PH.5", module_name="Anomaly Score", category="PH",
   basis_class="D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
   primary_method_source="S1 supervisory specification PH.5",
   canonical_structure_present="no", invariant_pass="no",
   parameter_provenance_status="NO_GOVERNED_WEIGHTS",
   lineage_status="RECYCLES_RETIRED_PROXY_AND_DUPLICATES_PH2",
   scientific_disposition="IMPLEMENTATION_DEFECT",
   finding_summary="THE WEIGHTS CHANGE WITH DATA AVAILABILITY. The composite is a plain mean "
                   "over whichever constituents happen to exist, so the presence of a history "
                   "moves the effective weight of the distance and rank terms from one half to "
                   "one third. The specification names this exact failure: absence of history "
                   "must not silently change all other effective weights. It was demonstrated "
                   "directly, the score moving with no change in the project. TWO FURTHER "
                   "LINEAGE PROBLEMS. The first constituent is the standardised-distance "
                   "quantity Run 15 RETIRED from PH.1 for not being an isolation forest; it "
                   "survives here under a different name and still feeds a participant-visible "
                   "composite. The second constituent is PH.2's own percentile rank, so the "
                   "composite re-reports portfolio-position evidence already reported, and this "
                   "was confirmed numerically. Genuinely good: the Run-14 constant 0.5 "
                   "placeholder is gone, the score stays in the unit interval, and a more "
                   "extreme project does not score less anomalous.",
   required_next_action="P0B in the Run-18 queue: govern the weights so they do not move with "
                        "data availability, and resolve the recycled retired proxy.",
   test_names="PH.5 positive/invariant x3/lineage/missingness/boundary")
