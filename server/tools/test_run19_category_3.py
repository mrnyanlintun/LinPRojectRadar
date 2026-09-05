"""
RUN 19 -- Category 3, cost risk. Eight scientific targets.

3.4 Material Cost Variance is NOT a target: it is registered, operationally disabled, non-voting
and excluded from the hundred result rows. Its disabled state is proved here as a guard, not
assessed as a method.

TEST AND AUDIT ONLY. Controlling theory: the committed supervisory specification, section 12.
Expected values come from run17/oracle/oracles_cat_3.py, which self proves against the
specification's worked answers at import. Production output is never the oracle.
"""

from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402
# Run 137, Item 1: a removed module identifier is SUBSTITUTED, not dispatched.
import os as _r96_os, sys as _r96_sys  # noqa: E402
_r96_sys.path.insert(0, _r96_os.path.dirname(_r96_os.path.abspath(__file__)))
from run96_removed_substitution import substitution as _R96  # noqa: E402

import datetime
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE / "run17"))
sys.path.insert(0, str(HERE / "run17" / "oracle"))

from audit_harness import (Audit, RESULT_HEADER, write_results,  # noqa: E402
                           oracle_gate)
from run20_production_changes import expected_flag       # noqa: E402
from population import population                                # noqa: E402
from app.simulation import registry as REG                       # noqa: E402

CUTOFF = datetime.date(2026, 6, 30)
RAND = lambda: 0.5  # noqa: E731

# RUN 28 EMPTIED THIS REGISTER. Each key named a canonical proposition of specification section
# 12 that production did not satisfy; the supplied Run-28 contract was implemented for all of
# them and production now satisfies each. The propositions are NOT removed -- every one is still
# evaluated below and will go red again if production regresses -- only the stale dispositions
# are. 3.8/design-matrix is resolved in the laboratory sense the contract asks for and no other:
# canonical_v3.parametric_cost implements the fitted linear model and its oracle, and the module
# REMAINS DISABLED AND NON-VOTING, which is checked below.
#
# RESOLVED IN RUN 28, with the disposition each carried before:
#   3.3/earned-output          CORRECT_PROXY_ONLY               -> output per hour on installed
#                                                                  quantity
#   3.5/allocation-base        CORRECT_PROXY_ONLY               -> rates over an explicit base
#   3.6/simulated-distribution METHOD_LABEL_MISMATCH            -> simulated total cost, P80 of it
#   3.7/analog-provenance      CORRECT_PROXY_ONLY               -> identified analog, adapted
#   3.8/design-matrix          METHOD_LABEL_MISMATCH            -> laboratory only, still disabled
#   3.9/external-index         MISSING_CANONICAL_DATA_STRUCTURE -> a named external index
#   3.9/deflation-visible      MISSING_CANONICAL_DATA_STRUCTURE -> a falling index deflates
KNOWN_DEFECTS: dict[str, str] = {}

A = Audit("category 3", KNOWN_DEFECTS)

#: Loaded through the gate so the oracle's own import-time self-proof becomes a
#: named red with a canonical RESULT line, rather than a traceback that the strict
#: runner would reject for the wrong reason.
O = oracle_gate(A, "oracles_cat_3")


def run(code_id: str, si: dict) -> dict:
    return _R96.dispatch(REG.run_module, globals(), code_id, si, RAND, CUTOFF)


def abstained(out: dict) -> bool:
    # RUN 28. A calibration-pending row is NOT an abstention: the canonical method ran and
    # produced a figure, and only the status colour is withheld because no boundary for the
    # quantity has been established from evidence. This is the same distinction
    # registry.record() makes when it routes such a row to `computed` rather than to
    # `abstained`. `insufficient_data` still wins, so a module that genuinely refuses is still
    # read as refusing and no guard below is weakened by this.
    if out.get("calibration_pending") and not out.get("insufficient_data"):
        return False
    return bool(out.get("insufficient_data")) or out.get("status_color") is None


# =============================================================================================
# GATE -- oracle, population, and the 3.4 exclusion the specification requires be proved
# =============================================================================================

def gate() -> None:
    A.check("GATE", "the Category 3 oracle reproduces the specification's worked answers",
            not O.self_test(), "; ".join(O.self_test()))
    ids = {t["module_id"] for t in population()}
    for mid in ("3.1", "3.2", "3.3", "3.5", "3.6", "3.7", "3.8", "3.9"):
        A.check("GATE", f"{mid} is one of the hundred scientific targets", mid in ids)
    A.check("GATE", "3.4 is excluded from the hundred scientific targets", "3.4" not in ids)
    for code in ("A3.1", "A3.2", "A3.3", "A3.5", "A3.6", "A3.7", "A3.8", "A3.9"):
        A.check("GATE", f"{code} is non-voting", code not in REG.CORE_VOTING_MODULES)

    # 3.4 -- registered, disabled, non-voting, and refused before its arithmetic is reached.
    idx = REG.registry_index()
    A.check("3.4", "registry identity is retained and not deleted", "A3.4" in idx)
    A.check("3.4", "the registry row still names Material Cost Variance",
            idx.get("A3.4", {}).get("module_name") == "Material Cost Variance")
    A.check("3.4", "its activation state is the evidence-under-review one, distinct from the "
                   "concept-only state the eight disabled methods carry",
            REG.activation_state("A3.4") == "DISABLED_EVIDENCE_UNDER_REVIEW")
    A.check("3.4", "non-voting", "A3.4" not in REG.CORE_VOTING_MODULES)
    for shape in ({}, {"materialCostBaseline": 100, "materialCostCurrent": 130,
                       "actualPctComplete": 50}, {"bac": 1000}):
        out = run("A3.4", shape)
        A.check("3.4", f"refused before its arithmetic on input shape {sorted(shape)}",
                out.get("activation_state") == "DISABLED_EVIDENCE_UNDER_REVIEW"
                and abstained(out))

    # 3.8 is one of the eight concept-only modules and must stay disabled.
    A.check("3.8", "remains disabled as concept-only and is short-circuited before its formula",
            run("A3.8", {"bac": 1000, "ev": 400, "ac": 500, "cpi": 0.8,
                         "actualPctComplete": 40}).get("activation_state") == "DISABLED_UNSAFE")
    A.check("3.8", "non-voting", "A3.8" not in REG.CORE_VOTING_MODULES)


# =============================================================================================
# 3.1 REFERENCE CLASS FORECASTING -- specification 12, "3.1"
# =============================================================================================

def _refclass(overruns, p=0.50, evaluated="PRJ-UNDER-TEST") -> dict:
    return {"referenceClassPopulation": {
        "governed_percentile": p, "evaluated_project_id": evaluated,
        "inclusion_criteria": "completed, same delivery method, same size band",
        "exclusion_criteria": "terminated for convenience",
        "outcome_definition": "final cost over approved budget at award, less one",
        "normalization": "constant 2026 dollars",
        "data_vintage": "2026-06",
        "members": [{"reference_project_id": f"REF-{i}", "proportional_overrun": v}
                    for i, v in enumerate(overruns)]}}


def m_3_1() -> None:
    ref = [0.0, 0.10, 0.20, 0.30, 0.40]
    A.near("3.1", "known-answer: the specification's reference class has a median uplift of .20",
           O.quantile_of_reference_class(ref, 0.50), 0.20)
    A.near("3.1", "known-answer: the adjusted forecast at that uplift",
           O.rcf_adjusted_forecast(1000, 0.20), 1200)
    A.check("3.1", "invariant: the uplift is monotone in the quantile chosen",
            [O.quantile_of_reference_class(ref, p) for p in (0.10, 0.50, 0.90)]
            == sorted([O.quantile_of_reference_class(ref, p) for p in (0.10, 0.50, 0.90)]))
    A.check("3.1", "invariant: the quantile is invariant to the order the reference class is "
                   "presented in", O.quantile_of_reference_class(list(reversed(ref)), 0.50)
            == O.quantile_of_reference_class(ref, 0.50))
    try:
        O.quantile_of_reference_class([], 0.5)
        A.check("3.1", "boundary: an empty reference class is refused", False)
    except ValueError:
        A.check("3.1", "boundary: an empty reference class is refused, since the method is "
                       "defined by its reference class", True)

    # RUN 28 SUPPLIED THE REFERENCE CLASS THIS MODULE HAD BEEN ABSTAINING FOR WANT OF.
    out = run("A3.1", {"bac": 1000, **_refclass(ref)})
    A.check("3.1", "positive: executes on a governed reference class", not abstained(out))
    A.near("3.1", "known-answer: production reproduces the specification's median uplift of .20",
           out.get("uplift"), 0.20, 1e-9)
    A.near("3.1", "known-answer: and the adjusted forecast of 1200 on an inside view of 1000",
           out.get("adjusted_forecast"), 1200.0, 1e-9)
    A.check("3.1", "structure: the sample size, the criteria, the outcome definition, the "
                   "normalization and the data vintage are all reported",
            out.get("sample_size") == 5
            and all(bool(out.get(k)) for k in ("inclusion_criteria", "exclusion_criteria",
                                               "outcome_definition", "normalization",
                                               "data_vintage")))
    A.check("3.1", "invariant: the uplift is monotone in the governed percentile",
            run("A3.1", {"bac": 1000, **_refclass(ref, 0.90)}).get("uplift")
            >= out.get("uplift"))
    A.check("3.1", "self-training: the project may not be a member of the class it is compared "
                   "against",
            abstained(run("A3.1", {"bac": 1000, **{"referenceClassPopulation": {
                **_refclass(ref)["referenceClassPopulation"],
                "members": _refclass(ref)["referenceClassPopulation"]["members"]
                + [{"reference_project_id": "PRJ-UNDER-TEST",
                    "proportional_overrun": 0.9}]}}})))
    A.check("3.1", "boundary: a class of fewer than three completed projects carries no "
                   "distribution of outcomes",
            abstained(run("A3.1", {"bac": 1000, **_refclass([0.1, 0.2])})))
    A.check("3.1", "missingness: a class that does not state its inclusion criteria is refused",
            abstained(run("A3.1", {"bac": 1000, **{"referenceClassPopulation": {
                **_refclass(ref)["referenceClassPopulation"],
                "inclusion_criteria": ""}}})))

    A.proposition(
        "3.1", "3.1/abstains-without-reference-class",
        "with no governed population of comparable completed projects the module abstains, "
        "rather than publishing a fixed multiplier as though it were an outside view",
        all(abstained(run("A3.1", si)) for si in
            ({}, {"bac": 1000}, {"bac": 10 ** 7, "cpi": 0.5, "ev": 100, "ac": 300},
             {"actualPctComplete": 90, "bac": 500})))
    A.check("3.1", "missingness: the abstention names the reference class as what is absent",
            "reference class" in str(run("A3.1", {"bac": 1000}).get("evidence_metric", "")).lower())
    A.check("3.1", "invariant: no project input can move the result while the reference class "
                   "is absent, so no fixed multiplier is being published under this name",
            len({str(run("A3.1", {"bac": b, "cpi": c}))
                 for b in (10, 1000, 10 ** 8) for c in (0.4, 1.0, 1.6)}) == 1)


# =============================================================================================
# 3.2 CONTINGENCY BURN RATE -- specification 12, "3.2"
# =============================================================================================

def m_3_2() -> None:
    c = O.contingency_consumed_fraction(100, 60)
    A.near("3.2", "known-answer: the specification's consumed fraction", c, 0.40)
    A.near("3.2", "known-answer: the specification's normalised burn at half complete",
           O.normalised_burn(c, 0.50), 0.80)
    out = run("A3.2", {"originalContingency": 100, "remainingContingency": 60,
                       "actualPctComplete": 50})
    A.check("3.2", "positive: executes", not abstained(out))
    A.near("3.2", "known-answer: production reports the specification's consumed fraction",
           out.get("consumed_fraction"), 0.40, 1e-9)
    A.near("3.2", "known-answer: and the specification's normalised burn of 0.80",
           out.get("normalized_burn"), 0.80, 1e-9)
    A.check("3.2", "invariant: the consumed share and the remaining share sum to one hundred",
            out.get("burn_rate_pct") + out.get("remaining_pct") == 100)
    A.check("3.2", "invariant: the burn rises monotonically as contingency is drawn down",
            [run("A3.2", {"originalContingency": 100, "remainingContingency": r,
                          "actualPctComplete": 50}).get("burn_rate_pct")
             for r in (100, 75, 40, 0)] == [0, 25, 60, 100])
    A.check("3.2", "metamorphic: at fixed consumption, greater progress lowers the normalised "
                   "burn, which is the direction the normalisation is for",
            run("A3.2", {"originalContingency": 100, "remainingContingency": 60,
                         "actualPctComplete": 80}).get("normalized_burn")
            < out.get("normalized_burn"))
    A.check("3.2", "boundary: an original contingency of zero leaves no denominator",
            abstained(run("A3.2", {"originalContingency": 0, "remainingContingency": 0,
                                   "actualPctComplete": 50})))
    A.check("3.2", "invalid input: a remaining contingency above the original is refused",
            abstained(run("A3.2", {"originalContingency": 100, "remainingContingency": 140,
                                   "actualPctComplete": 50})))
    A.check("3.2", "invalid input: a negative remaining contingency is refused",
            abstained(run("A3.2", {"originalContingency": 100, "remainingContingency": -10,
                                   "actualPctComplete": 50})))
    # RUN 28. The contract conditions only the SECOND figure on progress, so with no progress
    # the consumed fraction is still reported and the normalised burn is withheld, rather than
    # the raw consumed share being substituted for it under the same name.
    no_progress = run("A3.2", {"originalContingency": 100, "remainingContingency": 60})
    A.check("3.2", "missingness: with no progress the normalised burn is withheld rather than "
                   "having the raw consumed share substituted for it",
            no_progress.get("normalized_burn") is None
            and abs(no_progress.get("consumed_fraction") - 0.40) < 1e-9)
    A.check("3.2", "calibration: no status band is asserted, and the contract supplies none",
            out.get("status_color") is None and out.get("calibration_pending") is True)


# =============================================================================================
# 3.3 LABOR PRODUCTIVITY INDEX -- specification 12, "3.3"
# =============================================================================================

def _production(earned=800.0, planned_out=1000.0, actual_h=100.0, planned_h=100.0) -> dict:
    return {"productionOutputRecord": {
        "output_unit": "cubic yards", "quantity_source": "surveyed installed quantities",
        "earned_output": earned, "planned_output": planned_out,
        "actual_labor_hours": actual_h, "planned_labor_hours": planned_h}}


def m_3_3() -> None:
    A.near("3.3", "known-answer: the specification's eight units an hour actual productivity",
           O.productivity(800, 100), 8.0)
    A.near("3.3", "known-answer: against ten planned, an index of 0.80",
           O.productivity_index(800, 100, 1000, 100), 0.80)
    out = run("A3.3", _production())
    A.check("3.3", "positive: executes on a governed production record", not abstained(out))
    A.near("3.3", "known-answer: production reports the specification's actual productivity",
           out.get("actual_productivity"), 8.0, 1e-9)
    A.near("3.3", "known-answer: and the specification's index of 0.80",
           out.get("productivity_index"), 0.80, 1e-9)
    A.check("3.3", "structure: the output unit and both quantities are reported, so the index "
                   "is a quantity per hour rather than a ratio of hours",
            out.get("output_unit") == "cubic yards" and out.get("earned_output") == 800.0
            and out.get("planned_output") == 1000.0)
    A.check("3.3", "invariant: installing the planned quantity in the planned hours is an "
                   "index of exactly one",
            run("A3.3", _production(earned=1000.0)).get("productivity_index") == 1.0)
    A.check("3.3", "invariant: more hours for the same quantity lowers the index",
            run("A3.3", _production(actual_h=200.0)).get("productivity_index")
            < out.get("productivity_index"))
    A.check("3.3", "missingness: with no comparable output basis the answer is not estimable, "
                   "and a hours ratio is not used in its place",
            abstained(run("A3.3", {"plannedLaborHours": 1000, "actualLaborHours": 1200,
                                   "actualPctComplete": 50})))
    A.check("3.3", "missingness: a record that does not say what unit the work is counted in "
                   "cannot compare two quantities",
            abstained(run("A3.3", {"productionOutputRecord": {
                **_production()["productionOutputRecord"], "output_unit": ""}})))
    A.check("3.3", "boundary: no labour hours on either side leaves no output per hour",
            abstained(run("A3.3", _production(actual_h=0.0))))
    A.proposition(
        "3.3", "3.3/earned-output",
        "productivity is measured as output per labour hour on a comparable installed quantity, "
        "rather than as planned hours scaled by a reported progress percentage",
        abs(out.get("actual_productivity") - O.productivity(800, 100)) < 1e-9,
        "RESOLVED IN RUN 28.")


# =============================================================================================
# 3.5 OVERHEAD ABSORPTION RATE -- specification 12, "3.5"
# =============================================================================================

def _overhead(p_oh=100.0, p_dr=1000.0, a_oh=120.0, a_dr=1000.0) -> dict:
    return {"overheadAllocationBase": {
        "allocation_base": "direct labour hours", "driver_source": "certified payroll",
        "planned_overhead": p_oh, "planned_driver": p_dr,
        "actual_overhead": a_oh, "actual_driver": a_dr}}


def m_3_5() -> None:
    A.near("3.5", "known-answer: the specification's planned absorption rate of 0.10",
           O.absorption_rate(100, 1000), 0.10)
    A.near("3.5", "known-answer: and its actual rate of 0.12", O.absorption_rate(120, 1000), 0.12)
    v = O.absorption_rate_variance(100, 1000, 120, 1000)
    A.near("3.5", "known-answer: the specification's rate variance of 0.02",
           v["rate_variance"], 0.02)
    A.near("3.5", "known-answer: and its relative variance of 0.20", v["relative_variance"], 0.20)
    out = run("A3.5", _overhead())
    A.check("3.5", "positive: executes on an explicit allocation base", not abstained(out))
    A.near("3.5", "known-answer: production reports the specification's planned rate",
           out.get("planned_rate"), 0.10, 1e-9)
    A.near("3.5", "known-answer: and its actual rate", out.get("actual_rate"), 0.12, 1e-9)
    A.near("3.5", "known-answer: and its rate variance", out.get("rate_variance"), 0.02, 1e-9)
    A.near("3.5", "known-answer: and its relative rate variance",
           out.get("relative_rate_variance"), 0.20, 1e-9)
    A.check("3.5", "structure: the allocation base is named and both driver amounts reported",
            out.get("allocation_base") == "direct labour hours"
            and out.get("planned_driver") == 1000.0 and out.get("actual_driver") == 1000.0)
    A.check("3.5", "invariant: absorbing at the planned rate is a variance of nothing",
            run("A3.5", _overhead(a_oh=100.0)).get("rate_variance") == 0.0)
    A.check("3.5", "invariant: the same overhead over a larger base absorbs at a lower rate",
            run("A3.5", _overhead(a_dr=2000.0)).get("actual_rate") < out.get("actual_rate"))
    A.check("3.5", "missingness: with no allocation base the answer is not estimable, and the "
                   "ratio of actual to planned indirect cost is not used in its place",
            abstained(run("A3.5", {"indirectCostPlan": 100, "indirectCostActual": 120,
                                   "actualPctComplete": 50})))
    A.check("3.5", "missingness: a record naming no allocation base is refused",
            abstained(run("A3.5", {"overheadAllocationBase": {
                **_overhead()["overheadAllocationBase"], "allocation_base": ""}})))
    A.check("3.5", "boundary: no amount of the base on one side leaves no rate",
            abstained(run("A3.5", _overhead(a_dr=0.0))))
    A.proposition(
        "3.5", "3.5/allocation-base",
        "overhead absorption is measured over an explicit allocation base rather than as a "
        "ratio of actual to planned indirect cost",
        bool(out.get("allocation_base")) and out.get("planned_driver") == 1000.0,
        "RESOLVED IN RUN 28.")


# =============================================================================================
# 3.6 COST RISK ANALYSIS P80 -- specification 12, "3.6"
# =============================================================================================

def _costrisk(base=100.0, prob=0.5, impact=20.0) -> dict:
    return {"costRiskModel": {
        "model_version": "CRM-1", "estimate_source": "approved base estimate",
        "cost_components": [{"component_id": "BASE", "base_amount": base}],
        "risk_events": [{"risk_id": "R1", "probability": prob,
                         "impact_distribution": "POINT", "impact": impact}]}}


def m_3_6() -> None:
    # The independent oracle's own sample of the specification's two-point model.
    sample = O.bernoulli_cost_model(100, 0.5, 20, draws=40000, seed=20260828)
    A.near("3.6", "known-answer: the specification's two point model has a mean of 110, within "
                  "the 1.0 tolerance declared before this run",
           sum(sample) / len(sample), 110.0, 1.0)
    A.near("3.6", "known-answer: and a P80 of 120 under the right-continuous convention",
           O.empirical_quantile_right_continuous(sample, 0.80), 120.0)
    # A REAL GENERATOR: a simulation driven by a constant draw is not a simulation.
    out = _R96.dispatch(REG.run_module, globals(), "A3.6", _costrisk(), REG.make_rng(20260828), CUTOFF)
    A.check("3.6", "positive: executes on a stochastic cost risk model", not abstained(out))
    A.near("3.6", "known-answer: the simulated P80 is the specification's 120",
           out.get("p80_total_cost"), 120.0, 1e-9)
    A.near("3.6", "known-answer: and the simulated mean converges on 110, within the 1.0 "
                  "tolerance declared before this run",
           out.get("mean_total_cost"), 110.0, 1.0)
    A.check("3.6", "structure: the trial count and the frozen quantile convention are reported",
            out.get("trials") == 20000
            and out.get("quantile_convention") == "right-continuous empirical inverse")
    A.check("3.6", "invariant: a risk that cannot occur leaves the total at the base cost",
            _R96.dispatch(REG.run_module, globals(), "A3.6", _costrisk(prob=0.0), REG.make_rng(1),
                           CUTOFF).get("p80_total_cost") == 100.0)
    A.check("3.6", "invariant: a risk that must occur puts the whole impact on every trial",
            _R96.dispatch(REG.run_module, globals(), "A3.6", _costrisk(prob=1.0), REG.make_rng(1),
                           CUTOFF).get("p80_total_cost") == 120.0)
    A.check("3.6", "missingness: with no stochastic cost risk model the answer is not "
                   "estimable, and a deterministic uplift on the cost index is not used in its "
                   "place",
            abstained(run("A3.6", {"bac": 1000, "cpi": 0.8, "ac": 600, "ev": 500})))
    A.check("3.6", "invalid input: a likelihood outside nought to one is not a probability",
            abstained(run("A3.6", _costrisk(prob=1.4))))
    A.check("3.6", "boundary: a model with no base cost above zero has nothing to add risk to",
            abstained(run("A3.6", _costrisk(base=0.0))))
    A.proposition(
        "3.6", "3.6/simulated-distribution",
        "a distribution of total cost is simulated and a percentile taken of it",
        out.get("trials", 0) > 1 and out.get("p80_total_cost") != out.get("p50_total_cost"),
        "RESOLVED IN RUN 28.")


# =============================================================================================
# 3.7 ANALOGOUS ESTIMATING RATIO -- specification 12, "3.7"
# =============================================================================================

def _analog(cost=100.0, factors=((("size", 1.20)), ("location", 1.10))) -> dict:
    return {"analogEstimate": {
        "analog_project_id": "PRJ-ANALOG-1", "source": "closed project cost ledger",
        "comparability_criteria": "same structure type, same delivery method",
        "normalization": "constant 2026 dollars", "analog_cost": cost,
        "adaptation_factors": [{"factor_name": n, "factor_value": v} for n, v in factors]}}


def m_3_7() -> None:
    A.near("3.7", "known-answer: the specification's analog adapted by size and location",
           O.adapted_analog_estimate(100, [1.20, 1.10]), 132.0)
    out = run("A3.7", _analog())
    A.check("3.7", "positive: executes on an identified analog", not abstained(out))
    A.near("3.7", "known-answer: production reproduces the specification's 132",
           out.get("adapted_estimate"), 132.0, 1e-9)
    A.check("3.7", "structure: the analog is identified and its adaptation factors are named",
            out.get("analog_project_id") == "PRJ-ANALOG-1"
            and [f["factor_name"] for f in out.get("adaptation_factors")] == ["size", "location"])
    A.check("3.7", "invariant: factors of one leave the analog cost unchanged",
            run("A3.7", _analog(factors=(("size", 1.0),))).get("adapted_estimate") == 100.0)
    A.check("3.7", "invariant: the order the factors are applied in does not change the result",
            run("A3.7", _analog(factors=(("location", 1.10), ("size", 1.20)))
                ).get("adapted_estimate") == out.get("adapted_estimate"))
    A.check("3.7", "missingness: with no identified analog the answer is not estimable, and a "
                   "stored overrun percentage is not used in its place",
            abstained(run("A3.7", {"analogousOverrunPct": 8.0, "bac": 1000})))
    A.check("3.7", "missingness: an analog with no adaptation factors cannot be carried across",
            abstained(run("A3.7", {"analogEstimate": {
                **_analog()["analogEstimate"], "adaptation_factors": []}})))
    A.check("3.7", "missingness: an analog that does not state its comparability criteria is "
                   "refused", abstained(run("A3.7", {"analogEstimate": {
                       **_analog()["analogEstimate"], "comparability_criteria": ""}})))
    A.check("3.7", "boundary: a factor of zero or below is not a multiplier onto a cost",
            abstained(run("A3.7", _analog(factors=(("size", 0.0),)))))
    A.proposition(
        "3.7", "3.7/analog-provenance",
        "an analog project is identified, with its provenance, comparability criteria and "
        "adaptation factors, rather than a stored overrun percentage standing in for one",
        bool(out.get("analog_project_id")) and len(out.get("adaptation_factors")) == 2,
        "RESOLVED IN RUN 28.")


# =============================================================================================
# 3.8 PARAMETRIC COST INDEX -- specification 12, "3.8"
# =============================================================================================

def m_3_8() -> None:
    # RUN 28. THE LABORATORY IMPLEMENTATION ONLY. The contract requires the canonical v3
    # structure and a laboratory implementation to be built, and requires the module to REMAIN
    # DISABLED AND NON-VOTING until a later owner or research activation decision. Both halves
    # are asserted here: the mathematics is checked directly against canonical_v3, and the
    # module's disabled and non-voting state is checked against the registry.
    from app.simulation import canonical_v3 as CV3
    A.near("3.8", "known-answer: the specification's fitted model 10 + 2*4 + 3*5 predicts 33",
           O.parametric_cost(10, [2, 3], [4, 5]), 33.0)
    model = {"intercept": 10.0,
             "coefficient_source": "least squares fit on the closed project ledger",
             "fit_dataset": "OG-CLOSED-2019-2025", "model_version": "PCM-1",
             "coefficients": [{"driver": "x1", "coefficient": 2.0, "unit": "square metres"},
                              {"driver": "x2", "coefficient": 3.0, "unit": "storeys"}]}
    lab = CV3.parametric_cost(model, {"x1": 4.0, "x2": 5.0})
    A.near("3.8", "known-answer: the laboratory implementation reproduces the same 33",
           lab["predicted_cost"], 33.0, 1e-9)
    A.check("3.8", "structure: the intercept, every coefficient with its unit, and the design "
                   "row length are reported",
            lab["intercept"] == 10.0 and lab["driver_count"] == 2
            and lab["design_row_length"] == 3
            and all(t["unit"] for t in lab["terms"]))
    for bad, why in (({"x1": 4.0}, "a driver the model was fitted on but the project did not "
                                   "supply"),
                     ({"x1": 4.0, "x2": 5.0, "x3": 1.0}, "a driver the model was never fitted "
                                                         "on")):
        try:
            CV3.parametric_cost(model, bad)
            A.check("3.8", f"omitted driver: {why} is refused", False)
        except Exception:
            A.check("3.8", f"omitted driver: {why} is refused, rather than being silently "
                           f"valued at zero", True)
    A.check("3.8", "the module remains DISABLED after Run 28, which the contract requires",
            "A3.8" in REG.DISABLED_MODULES)
    A.check("3.8", "and remains NON-VOTING", "A3.8" not in REG.CORE_VOTING_MODULES)
    A.check("3.8", "and no production path reaches the laboratory implementation: asking the "
                   "registry for it returns the disabled refusal rather than a prediction",
            abstained(run("A3.8", {"bac": 1000, "ev": 500, "ac": 600, "cpi": 0.8,
                                   "actualPctComplete": 50})))
    A.proposition(
        "3.8", "3.8/design-matrix",
        "a parametric estimating relationship with drivers, units and fitted coefficients "
        "exists, rather than a comparison of two estimate-at-completion formulas",
        lab["driver_count"] == 2 and bool(model["fit_dataset"]),
        "RESOLVED IN RUN 28, in the laboratory sense the contract asks for and no other: the "
        "module remains disabled and non-voting.")


# =============================================================================================
# 3.9 INFLATION ADJUSTMENT INDEX -- specification 12, "3.9"
# =============================================================================================

def _index(base=200.0, current=220.0, exposure=100.0) -> dict:
    return {"externalCostIndex": {
        "index_name": "Construction Cost Index, all items",
        "authority": "national statistical office",
        "geography": "national", "scope": "construction materials and labour",
        "base_period": "2020-01", "observation_period": "2026-06", "vintage": "2026-07 release",
        "base_index_value": base, "current_index_value": current, "cost_exposure": exposure}}


def m_3_9() -> None:
    A.near("3.9", "known-answer: the specification's index moving 200 to 220 is a factor of 1.10",
           O.escalation_factor(220, 200), 1.10)
    out = run("A3.9", _index())
    A.check("3.9", "positive: executes on a named external index", not abstained(out))
    A.near("3.9", "known-answer: production reproduces the specification's factor of 1.10",
           out.get("escalation_factor"), 1.10, 1e-9)
    A.near("3.9", "known-answer: and the specification's adjusted cost of 110 on an exposure "
                  "of 100", out.get("adjusted_cost"), 110.0, 1e-9)
    A.check("3.9", "structure: the series is named and carries its authority, geography, "
                   "scope, base period, observation period and vintage",
            all(bool(out.get(k)) for k in ("index_name", "index_authority", "geography",
                                           "index_scope", "base_period", "observation_period",
                                           "vintage")))
    A.check("3.9", "invariant: an unchanged index is a factor of exactly one and no escalation",
            run("A3.9", _index(current=200.0)).get("escalation_factor") == 1.0)
    A.check("3.9", "deflation: a FALLING index gives a factor below one and a negative "
                   "escalation amount, which a floored proxy structurally could not show",
            run("A3.9", _index(current=180.0)).get("escalation_factor") < 1.0
            and run("A3.9", _index(current=180.0)).get("escalation_amount") < 0)
    A.check("3.9", "missingness: with no governed external index the answer is not estimable, "
                   "and the project's own material price movement is not used in its place",
            abstained(run("A3.9", {"materialCostBaseline": 100, "materialCostCurrent": 120,
                                   "actualPctComplete": 50})))
    A.check("3.9", "missingness: an index that does not name its authority is refused",
            abstained(run("A3.9", {"externalCostIndex": {
                **_index()["externalCostIndex"], "authority": ""}})))
    A.check("3.9", "missingness: an index that does not name its geography is refused",
            abstained(run("A3.9", {"externalCostIndex": {
                **_index()["externalCostIndex"], "geography": ""}})))
    A.check("3.9", "boundary: an index level of zero or below is not an index level",
            abstained(run("A3.9", _index(base=0.0))))
    A.check("3.9", "no hard-coded market index: both levels come off the supplied structure, so "
                   "changing them changes the answer",
            run("A3.9", _index(current=240.0)).get("escalation_factor")
            != out.get("escalation_factor"))
    A.proposition(
        "3.9", "3.9/external-index",
        "escalation is measured from a named external price index with an authority, a "
        "geography and a base period, rather than from the project's own material prices",
        bool(out.get("index_name")) and bool(out.get("index_authority"))
        and bool(out.get("base_period")),
        "RESOLVED IN RUN 28.")
    A.proposition(
        "3.9", "3.9/deflation-visible",
        "a falling index is visible as deflation rather than floored at nothing",
        run("A3.9", _index(current=180.0)).get("escalation_factor") < 1.0,
        "RESOLVED IN RUN 28.")


# =============================================================================================
# RESULT ROWS
# =============================================================================================

def _row(mid, name, basis, source, sreq, spres, impl, param, calib, thresh, lineage, disp,
         finding, nxt, activation="ADVISORY_ONLY") -> dict:
    return {
        "module_id": mid, "module_name": name, "category": "3", "basis_class": basis,
        "operational_activation": activation, "voting_status": "non-voting",
        "primary_method_source": source, "canonical_structure_required": sreq,
        "canonical_structure_present": spres, "implementation_verified": impl,
        "known_answer_pass": "yes", "boundary_pass": "yes", "missingness_pass": "yes",
        "invariant_pass": "yes", "stochastic_diagnostics_pass": "n/a",
        "reproducibility_pass": "yes", "parameter_provenance_status": param,
        "calibration_status": calib, "threshold_status": thresh,
        "empirical_validation_status": "NOT_DONE", "regulatory_snapshot": "n/a",
        "cat9_qualification_status": "RAW_UNQUALIFIED_INPUT", "lineage_status": lineage,
        "scientific_disposition": disp,
        # RUN 20. Derived from the module id rather than fixed at "no", so a module
        # this run changed in production cannot report that nothing was changed.
        "production_change_made": expected_flag(mid),
        "finding_summary": finding, "required_next_action": nxt,
        "test_names": "; ".join(A.coverage.get(mid, []))[:1800],
        "evidence_paths": ("server/tools/test_run19_category_3.py; "
                           "server/tools/run17/oracle/oracles_cat_3.py; "
                           "server/tools/run17/categories/category_3_faults.csv"),
    }


ROWS = lambda: [  # noqa: E731
    _row("3.1", "Reference Class Forecasting", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 12 section 3.1; reference class forecasting literature",
         "yes", "no", "n/a", "n/a", "n/a", "n/a", "NO_EVIDENCE_EMITTED", "CORRECT_ABSTENTION",
         "The method is defined by its reference class, and no population of comparable "
         "completed projects is held. The module abstains unconditionally and names the "
         "reference class as what is absent. Its result is byte-identical across every "
         "combination of budget and cost index tested, which proves no fixed multiplier is being "
         "published under this name and nothing about a project can move a band that has no "
         "basis. The oracle reproduced the specification's own five-point reference class and "
         "its median uplift of twenty per cent independently, establishing what the method would "
         "require. Abstention here is the scientifically correct result.",
         "Build a governed reference class of comparable completed projects with inclusion "
         "criteria, normalisation and realised overruns, or leave the module abstaining."),
    _row("3.2", "Contingency Burn Rate", "D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
         "Specification 12 section 3.2",
         "no", "n/a", "yes", "n/a", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED",
         "SHARED_PROGRESS_INPUT", "THRESHOLD_CALIBRATION_BLOCKED",
         "Both quantities the specification defines are reproduced exactly: the consumed "
         "fraction of forty per cent and the progress-normalised burn of point eight zero. The "
         "consumed and remaining shares sum to one hundred, the burn is monotone in the drawdown, "
         "and greater progress at fixed consumption lowers the normalised burn as the "
         "normalisation intends. A remaining contingency above the original or below zero is "
         "refused, nothing complete abstains rather than substituting the raw share, and an "
         "impossible progress figure is refused rather than landing in the calm band. What has "
         "no basis is the banding: the module's own comment records that no source specifies "
         "one, three tenths and one and six tenths for contingency against progress, and that "
         "the premise those boundaries rest on, contingency consumed in proportion to progress, "
         "is not what the contingency literature describes.",
         "Convert the boundaries to declared owner policy or calibrate them. The arithmetic "
         "needs no change."),
    _row("3.3", "Labor Productivity Index", "C. LITERATURE_SUPPORTED_ADAPTATION",
         "Specification 12 section 3.3",
         "yes", "no", "yes", "n/a", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED",
         "SHARED_PROGRESS_AND_LABOUR_INPUT", "CORRECT_PROXY_ONLY",
         "The implemented ratio is arithmetically exact and correctly guarded: no actual hours "
         "abstains, an impossible progress figure is refused rather than reading as the best "
         "possible productivity, and all three inputs are required. But the numerator is percent "
         "complete times planned hours, which is an hours figure derived from progress, not a "
         "measured output quantity. No unit of installed work appears anywhere. Specification "
         "3.3 states that a ratio of hours without earned output is a labour-hours performance "
         "proxy and not full productivity. The module names its own output the earned-hours "
         "rate, which is an honest disclosure; the registered module name is what overstates it.",
         "P3. Either carry measured output quantities and compute output per hour, or rename "
         "the module for the earned-hours rate it already discloses."),
    _row("3.5", "Overhead Absorption Rate", "C. LITERATURE_SUPPORTED_ADAPTATION",
         "Specification 12 section 3.5",
         "yes", "no", "yes", "n/a", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED",
         "SHARED_PROGRESS_INPUT", "CORRECT_PROXY_ONLY",
         "The implemented ratio is exact and monotone, and its guards are sound: withholding "
         "progress no longer enlarges the denominator and improves the band, a plan scaled to "
         "zero is refused rather than substituting a ratio of exactly one, and an impossible "
         "progress figure is refused. But no allocation base exists. The module compares two "
         "AMOUNTS, actual indirect cost against a progress-scaled indirect plan, where an "
         "absorption rate is overhead per unit of an explicit base. The oracle demonstrates the "
         "property that separates them: a doubled overhead on a doubled base is no rate variance "
         "at all, and this module cannot represent that case because it has no base. "
         "Specification 3.5 names the implemented quantity an indirect-cost variance proxy.",
         "P3. Carry an allocation base and compare planned against actual rates, or rename the "
         "module for the indirect-cost variance it computes."),
    _row("3.6", "Cost Risk Analysis P80", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 12 section 3.6",
         "yes", "no", "no", "NOT_SOURCED", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED",
         "DERIVED_FROM_CPI", "METHOD_LABEL_MISMATCH",
         "The crash that lost every project-level result to an exception on a zero cost index is "
         "fixed, negative indices and non-positive budgets abstain, and the reported sign now "
         "follows the figure rather than a hard-coded plus. The forecast is monotone in cost "
         "performance. But there is no risk register, no component distribution, no dependency "
         "structure, no iteration count and no sample. The P80 is budget over the cost index "
         "multiplied by one plus max(0.03, absolute one minus CPI) times 0.5 times 1.28, a "
         "deterministic uplift of the current index, which specification 3.6 states in terms is "
         "not Cost Risk Analysis P80. The 1.28 is the normal ninetieth-percentile deviate rather "
         "than an eightieth. An independent simulation of the specification's own Bernoulli cost "
         "model converged to the analytic mean of 110 and the correct P80 of 120 under a frozen "
         "quantile convention, showing what the canonical method yields and this one does not.",
         "P1. Either build the cost simulation over a risk register or rename the module for the "
         "deterministic uplift it performs. Correct or document the 1.28 constant either way."),
    _row("3.7", "Analogous Estimating Ratio", "C. LITERATURE_SUPPORTED_ADAPTATION",
         "Specification 12 section 3.7",
         "yes", "no", "no", "NOT_SOURCED", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED",
         "UNTRACEABLE_SCALAR_INPUT", "CORRECT_PROXY_ONLY",
         "RUN 20 CYCLE 1. The invalid-evidence hole is closed: a budget at completion of zero or below now goes through the shared positive preflight and abstains on the invalid denominator instead of reaching a Yellow band, and no result reports a negative quantity of money at risk. Run 19's further instruction to refuse a NEGATIVE overrun percent was not adopted, and the reason is recorded rather than waived: field_registry.SIGNED_SI_FIELDS names analogousOverrunPct one of four fields where a negative value is a real project condition, because a reference project can underrun. The underrun is now reported as an underrun with no exposure carried, rather than as a negative exposure. What remains is the proxy finding the specification itself states: a single preloaded overrun percent with no analog selection, comparability criteria, normalisation or adaptation factors is only a proxy for analogous estimating.",
         'P2 and P3. Carry identified analogs with comparability criteria and adaptation factors, or rename the module to the transparent indicator it is.'),
    _row("3.8", "Parametric Cost Index", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 12 section 3.8",
         "yes", "no", "no", "NOT_SOURCED", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED",
         "SHARED_EVM_INPUT_VECTOR", "METHOD_LABEL_MISMATCH",
         "The module is one of the eight concept-only methods and is short-circuited before its "
         "formula is reached, which was proved on a complete input. Its activation state is the "
         "concept-only one and it does not vote, and this run does not change that. What the "
         "formula WOULD compute, read from source, is the ratio of budget over cost index to "
         "actual cost plus budget less earned value: two earned-value forecasts of the same "
         "project divided by each other. Specification 3.8 states in terms that comparing two "
         "EAC formulas is not parametric estimating. No driver, coefficient, intercept or design "
         "matrix exists, and both forecasts are transformations of one earned-value input "
         "vector, so the ratio is one body of evidence divided by itself. The canonical model "
         "was verified independently in the laboratory at the specification's own worked figures, "
         "including refusal of a nonconforming design matrix.",
         "Remains disabled and non-voting. A laboratory result is not permission to activate. If "
         "the module is ever wanted, it must be rebuilt around measurable drivers and calibrated "
         "coefficients, not renamed.",
         activation="DISABLED_UNSAFE"),
    _row("3.9", "Inflation Adjustment Index", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 12 section 3.9",
         "yes", "no", "no", "NOT_SOURCED", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED",
         "OWN_MATERIAL_COST_ONLY", "MISSING_CANONICAL_DATA_STRUCTURE",
         "The guards are sound: negative material costs are refused rather than floored to "
         "exactly nought escalation, progress outside nought to one hundred is refused, a "
         "baseline scaled to zero is refused, and withholding progress no longer buys a calmer "
         "band. The arithmetic is monotone and exact. But the canonical structure is entirely "
         "absent: there is no external index series, no geography, no commodity scope, no base "
         "period and no vintage. The module divides the project's own current material cost by "
         "its own progress-scaled baseline, which specification 3.9 states is not a macro or "
         "regional inflation adjustment. A secondary consequence of the max(0, ...) floor is "
         "that a project eighty per cent under its material baseline is indistinguishable from "
         "one exactly on it, and both read Green. The module's own sentence calls the figure a "
         "proxy, which is honest; the registered name is not.",
         "P2. Source a governed external price index with geography, base period and vintage, or "
         "rename the module for the material cost ratio it computes. Decide whether deflation "
         "should be visible rather than floored."),
]


def main() -> int:
    gate()
    m_3_1(); m_3_2(); m_3_3(); m_3_5(); m_3_6(); m_3_7(); m_3_8(); m_3_9()
    rows = ROWS()
    write_results(artifact_out(HERE / "run17" / "categories" / "category_3_results.csv"), RESULT_HEADER, rows)
    A.check("ROWS", "eight Category 3 result rows were written, with 3.4 excluded",
            len(rows) == 8 and "3.4" not in {r["module_id"] for r in rows})
    # RUN 20. Run 19 changed no production file and this check refused any row that claimed
    # otherwise. Run 20 is authorized to change production, so the guard is narrowed rather than
    # removed: a row may record a change only if its module is in the declared Run-20 manifest,
    # and a module in that manifest that records no change fails just as loudly. An accidental
    # production edit is still caught, and so is a fix that was made but never declared.
    A.check("ROWS", "every row's production-change flag matches the declared Run-20 manifest",
            all(r["production_change_made"] == expected_flag(r["module_id"]) for r in rows),
            str({r["module_id"]: r["production_change_made"] for r in rows
                 if r["production_change_made"] != expected_flag(r["module_id"])}))
    return A.finish()


if __name__ == "__main__":
    sys.exit(main())
