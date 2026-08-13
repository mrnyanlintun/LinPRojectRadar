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

KNOWN_DEFECTS = {
    "3.3/earned-output": "CORRECT_PROXY_ONLY",
    "3.5/allocation-base": "CORRECT_PROXY_ONLY",
    "3.6/simulated-distribution": "METHOD_LABEL_MISMATCH",
    "3.7/analog-provenance": "CORRECT_PROXY_ONLY",
    "3.8/design-matrix": "METHOD_LABEL_MISMATCH",
    "3.9/external-index": "MISSING_CANONICAL_DATA_STRUCTURE",
    "3.9/deflation-visible": "MISSING_CANONICAL_DATA_STRUCTURE",
}

A = Audit("category 3", KNOWN_DEFECTS)

#: Loaded through the gate so the oracle's own import-time self-proof becomes a
#: named red with a canonical RESULT line, rather than a traceback that the strict
#: runner would reject for the wrong reason.
O = oracle_gate(A, "oracles_cat_3")


def run(code_id: str, si: dict) -> dict:
    return REG.run_module(code_id, si, RAND, CUTOFF)


def abstained(out: dict) -> bool:
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
    A.near("3.2", "known-answer: production reports the same forty per cent consumed",
           out.get("burn_rate_pct"), 40, 0.5)
    A.near("3.2", "known-answer: production reports the same normalised burn of .80",
           out.get("burn_stress"), 0.80, 0.005)

    A.check("3.2", "invariant: the consumed share and the remaining share sum to one hundred",
            out.get("burn_rate_pct") + out.get("remaining_pct") == 100)
    A.check("3.2", "invariant: the burn rises monotonically as contingency is drawn down",
            [run("A3.2", {"originalContingency": 100, "remainingContingency": r,
                          "actualPctComplete": 50}).get("burn_rate_pct")
             for r in (100, 75, 40, 0)] == [0, 25, 60, 100])
    A.check("3.2", "metamorphic: at fixed consumption, greater progress lowers the normalised "
                   "burn, which is the direction the normalisation is for",
            run("A3.2", {"originalContingency": 100, "remainingContingency": 60,
                         "actualPctComplete": 80}).get("burn_stress")
            < out.get("burn_stress"))
    A.check("3.2", "boundary: an original contingency of zero leaves no denominator",
            abstained(run("A3.2", {"originalContingency": 0, "remainingContingency": 0,
                                   "actualPctComplete": 50})))
    A.check("3.2", "invalid input: a remaining contingency above the original is refused",
            abstained(run("A3.2", {"originalContingency": 100, "remainingContingency": 140,
                                   "actualPctComplete": 50})))
    A.check("3.2", "invalid input: a negative remaining contingency is refused",
            abstained(run("A3.2", {"originalContingency": 100, "remainingContingency": -10,
                                   "actualPctComplete": 50})))
    A.proposition(
        "3.2", "3.2/no-progress-substitute",
        "at nothing complete the module does not substitute the raw consumed share for the "
        "progress-normalised burn, which is a different quantity under the same name",
        abstained(run("A3.2", {"originalContingency": 100, "remainingContingency": 100,
                               "actualPctComplete": 0})))
    A.check("3.2", "invalid input: an impossible progress figure is refused rather than making "
                   "the normalised burn small and landing in the calm end of the band",
            abstained(run("A3.2", {"originalContingency": 100, "remainingContingency": 20,
                                   "actualPctComplete": 10000})))
    A.check("3.2", "missingness: all three figures are required",
            abstained(run("A3.2", {"originalContingency": 100})))


# =============================================================================================
# 3.3 LABOR PRODUCTIVITY INDEX -- specification 12, "3.3"
# =============================================================================================

def m_3_3() -> None:
    A.near("3.3", "known-answer: the specification's planned productivity of ten units per hour",
           O.productivity(1000, 100), 10.0)
    A.near("3.3", "known-answer: the specification's productivity index of .80",
           O.productivity_index(800, 100, 1000, 100), 0.80)
    A.check("3.3", "invariant: the index is invariant under a common rescaling of the output "
                   "unit, since it is a ratio of two productivities",
            abs(O.productivity_index(8000, 100, 10000, 100)
                - O.productivity_index(800, 100, 1000, 100)) < 1e-12)

    out = run("A3.3", {"plannedLaborHours": 1000, "actualLaborHours": 1000,
                       "actualPctComplete": 80})
    A.near("3.3", "structure: the declared earned-hours rate is progress times planned hours "
                  "over actual hours", out.get("earned_hours_rate"), 0.80, 1e-9)
    A.check("3.3", "invariant: the rate falls as hours are spent for the same progress",
            [run("A3.3", {"plannedLaborHours": 1000, "actualLaborHours": a,
                          "actualPctComplete": 50}).get("earned_hours_rate")
             for a in (400, 500, 800, 1000)] == [1.25, 1.0, 0.63, 0.5])
    A.check("3.3", "boundary: no actual hours leaves no denominator",
            abstained(run("A3.3", {"plannedLaborHours": 1000, "actualLaborHours": 0,
                                   "actualPctComplete": 50})))
    A.check("3.3", "invalid input: an impossible progress figure is refused rather than reading "
                   "as the best possible productivity",
            abstained(run("A3.3", {"plannedLaborHours": 1000, "actualLaborHours": 500,
                                   "actualPctComplete": 10000})))
    A.check("3.3", "missingness: all three figures are required",
            abstained(run("A3.3", {"plannedLaborHours": 1000})))

    A.proposition(
        "3.3", "3.3/earned-output",
        "productivity is computed from EARNED OUTPUT per labour hour, as specification 3.3 "
        "defines it, rather than from hours against hours",
        any(k in out for k in ("earned_output", "units_installed", "output_quantity",
                               "planned_productivity", "actual_productivity")),
        "the module computes (percent complete times planned hours) over actual hours. The "
        "numerator is an hours figure derived from progress, not a measured output quantity, so "
        "no unit of work appears anywhere. Specification 3.3 states that a ratio of hours "
        "without earned output is a labour-hours performance proxy and not full productivity. "
        "The module names its own output earned_hours_rate, which is an honest disclosure of "
        "exactly this, but the registered module name still says productivity")


# =============================================================================================
# 3.5 OVERHEAD ABSORPTION RATE -- specification 12, "3.5"
# =============================================================================================

def m_3_5() -> None:
    v = O.absorption_rate_variance(100, 1000, 120, 1000)
    A.near("3.5", "known-answer: the specification's planned absorption rate", v["planned_rate"],
           0.10)
    A.near("3.5", "known-answer: the specification's actual absorption rate", v["actual_rate"],
           0.12)
    A.near("3.5", "known-answer: the specification's rate variance", v["rate_variance"], 0.02)
    A.near("3.5", "known-answer: the specification's relative variance of twenty per cent",
           v["relative_variance"], 0.20)
    A.check("3.5", "invariant: an unchanged rate on a changed base is no rate variance, which "
                   "is the property that distinguishes a rate from an amount",
            abs(O.absorption_rate_variance(100, 1000, 200, 2000)["rate_variance"]) < 1e-12)

    out = run("A3.5", {"indirectCostPlan": 1000, "indirectCostActual": 600,
                       "actualPctComplete": 50})
    A.near("3.5", "structure: the declared ratio is actual indirect cost over a progress-scaled "
                  "plan", out.get("absorption_ratio"), 1.2, 1e-9)
    A.check("3.5", "invariant: the ratio rises monotonically with indirect cost incurred",
            [run("A3.5", {"indirectCostPlan": 1000, "indirectCostActual": a,
                          "actualPctComplete": 50}).get("absorption_ratio")
             for a in (250, 500, 750)] == [0.5, 1.0, 1.5])
    A.proposition(
        "3.5", "3.5/no-unscaled-plan-on-missing-progress",
        "withholding the progress figure does not enlarge the denominator and improve the band",
        abstained(run("A3.5", {"indirectCostPlan": 1000, "indirectCostActual": 900})))
    A.check("3.5", "boundary: a plan scaled to zero by zero progress leaves nothing to absorb "
                   "against and is refused rather than substituting a ratio of exactly one",
            abstained(run("A3.5", {"indirectCostPlan": 1000, "indirectCostActual": 900,
                                   "actualPctComplete": 0})))
    A.check("3.5", "boundary: an indirect plan of zero is refused",
            abstained(run("A3.5", {"indirectCostPlan": 0, "indirectCostActual": 900,
                                   "actualPctComplete": 50})))
    A.check("3.5", "invalid input: an impossible progress figure is refused",
            abstained(run("A3.5", {"indirectCostPlan": 1000, "indirectCostActual": 900,
                                   "actualPctComplete": 10000})))
    A.check("3.5", "missingness: both cost figures are required",
            abstained(run("A3.5", {"indirectCostPlan": 1000})))

    A.proposition(
        "3.5", "3.5/allocation-base",
        "absorption is computed as overhead per unit of an explicit allocation base, and the "
        "planned and actual rates are formed on a comparable basis",
        any(k in out for k in ("allocation_base", "absorption_base", "planned_rate",
                               "actual_rate", "driver_quantity")),
        "no allocation base exists. The module divides actual indirect cost by a plan scaled by "
        "percent complete, which compares two AMOUNTS rather than two RATES. Specification 3.5 "
        "states that indirectCostActual over indirectCostPlan without an allocation base is an "
        "indirect-cost variance proxy and not an overhead absorption rate. The property that a "
        "rate variance of zero survives a doubled base, which the oracle confirms, cannot hold "
        "here because no base is represented at all")


# =============================================================================================
# 3.6 COST RISK ANALYSIS P80 -- specification 12, "3.6"
# =============================================================================================

def m_3_6() -> None:
    A.near("3.6", "known-answer: the specification's two-point cost distribution has a P80 of "
                  "120 under the frozen right-continuous convention",
           O.empirical_quantile_right_continuous([100.0] * 500 + [120.0] * 500, 0.80), 120.0)
    # Tolerance frozen here before any result is observed: 40000 draws, mean within 0.5.
    sample = O.bernoulli_cost_model(100, 0.5, 20, 40000, 20260813)
    A.near("3.6", "known-answer: a seeded simulation of the specification's cost-risk model "
                  "converges to the analytic mean of 110", sum(sample) / len(sample), 110.0, 0.5)
    A.near("3.6", "known-answer: its simulated P80 is the upper atom",
           O.empirical_quantile_right_continuous(sample, 0.80), 120.0)
    again = O.bernoulli_cost_model(100, 0.5, 20, 40000, 20260813)
    A.check("3.6", "reproducibility: the same seed gives the identical sample", again == sample)
    A.check("3.6", "stochastic diagnostic: a different seed moves the sample but not the "
                   "quantile, which is the convergence the method relies on",
            O.bernoulli_cost_model(100, 0.5, 20, 40000, 7) != sample
            and O.empirical_quantile_right_continuous(
                O.bernoulli_cost_model(100, 0.5, 20, 40000, 7), 0.80) == 120.0)

    base = {"bac": 1000, "cpi": 0.80, "ac": 500, "ev": 400}
    out = run("A3.6", base)
    A.check("3.6", "structure: the module reports a P80 forecast and its deviation from budget",
            out.get("p80_eac") is not None and out.get("p80_delta_pct") is not None)
    A.check("3.6", "invariant: the P80 forecast is above budget when cost performance is below "
                   "one", out.get("p80_eac") > base["bac"])
    # The ordering invariant every quantile forecast must satisfy: an eightieth percentile
    # cannot sit below the point forecast it is an uplift of. This check was added after the
    # fault campaign showed that reversing the uplift direction went undetected without it,
    # which is the coverage gap the campaign exists to expose.
    A.check("3.6", "invariant: the P80 forecast is not below the point forecast it uplifts",
            out.get("p80_eac") >= base["bac"] / base["cpi"] - 1,
            f"P80 {out.get('p80_eac')} against point forecast {base['bac'] / base['cpi']}")
    A.check("3.6", "invariant: the ordering holds across the range of cost performance",
            all(run("A3.6", {**base, "cpi": c}).get("p80_eac") >= 1000 / c - 1
                for c in (1.4, 1.0, 0.8, 0.6)))
    A.check("3.6", "invariant: the forecast rises monotonically as cost performance falls",
            [run("A3.6", {**base, "cpi": c}).get("p80_eac") for c in (1.2, 1.0, 0.8, 0.5)]
            == sorted([run("A3.6", {**base, "cpi": c}).get("p80_eac")
                       for c in (1.2, 1.0, 0.8, 0.5)]))
    A.proposition(
        "3.6", "3.6/no-zero-cpi-crash",
        "a cost performance index of exactly zero abstains rather than raising and losing the "
        "whole project's result to an exception",
        abstained(run("A3.6", {**base, "cpi": 0})))
    A.check("3.6", "boundary: a negative cost performance index is refused",
            abstained(run("A3.6", {**base, "cpi": -0.4})))
    A.check("3.6", "boundary: no positive budget leaves nothing to measure an overrun against",
            abstained(run("A3.6", {**base, "bac": 0})))
    A.check("3.6", "missingness: the four earned-value figures are required",
            abstained(run("A3.6", {"bac": 1000})))
    A.check("3.6", "the sign of the reported deviation follows the figure rather than a "
                   "hard-coded plus, so the sentence cannot say the opposite of the number",
            "+" not in str(run("A3.6", {**base, "cpi": 1.6}).get("evidence_metric", ""))
            or run("A3.6", {**base, "cpi": 1.6}).get("p80_delta_pct") >= 0)

    A.proposition(
        "3.6", "3.6/simulated-distribution",
        "the eightieth percentile is the empirical quantile of a simulated total-cost "
        "distribution built from base cost components and risk events with explicit "
        "distributions",
        any(k in out for k in ("iterations", "risk_events", "distribution", "sample_size",
                              "components")),
        "no risk register, no component distributions, no dependencies, no iterations and no "
        "sample exist. The forecast is budget over the cost index, multiplied by "
        "(1 + max(0.03, |1 - CPI|) * 0.5 * 1.28). That is a deterministic uplift of the current "
        "index, which specification 3.6 states in terms is not Cost Risk Analysis P80. The 1.28 "
        "is the normal ninetieth-percentile deviate, not an eightieth, and the spread is a "
        "function of the cost index rather than of any modelled cost uncertainty. The module's "
        "own source comment records that it cannot consume risk-register data without changing "
        "its arithmetic")


# =============================================================================================
# 3.7 ANALOGOUS ESTIMATING RATIO -- specification 12, "3.7"
# =============================================================================================

def m_3_7() -> None:
    A.near("3.7", "known-answer: the specification's analog adapted by size and location",
           O.adapted_analog_estimate(100, [1.20, 1.10]), 132.0)
    A.check("3.7", "invariant: adaptation factors commute, so the order they are applied in "
                   "cannot change the estimate",
            abs(O.adapted_analog_estimate(100, [1.10, 1.20])
                - O.adapted_analog_estimate(100, [1.20, 1.10])) < 1e-12)
    A.check("3.7", "invariant: an analog needing no adaptation estimates itself",
            O.adapted_analog_estimate(100, [1.0]) == 100)

    out = run("A3.7", {"analogousOverrunPct": 8, "bac": 1000})
    A.near("3.7", "structure: the declared exposure is the budget times the overrun percent",
           out.get("bac_exposure"), 80, 0.5)
    A.check("3.7", "invariant: exposure is monotone in the overrun percent",
            [run("A3.7", {"analogousOverrunPct": p, "bac": 1000}).get("bac_exposure")
             for p in (1, 5, 12)] == [10, 50, 120])
    A.check("3.7", "missingness: both figures are required",
            abstained(run("A3.7", {"bac": 1000})))

    A.proposition(
        "3.7", "3.7/analog-provenance",
        "the module identifies the analogous projects it drew from, with comparability criteria, "
        "normalisation and adaptation factors, as specification 3.7 requires",
        any(k in out for k in ("analog_projects", "analog_ids", "comparability_criteria",
                               "adaptation_factors", "normalisation")),
        "a single preloaded overrun percent arrives as a scalar input with no analog selection, "
        "no comparability criteria, no normalisation and no adaptation factors. Specification "
        "3.7 states that this is only a proxy. Nothing in the module or its output records where "
        "the percent came from, so its provenance cannot be established at all")

    neg = run("A3.7", {"analogousOverrunPct": -50, "bac": 1000})
    neg_bac = run("A3.7", {"analogousOverrunPct": 5, "bac": -1000})
    A.proposition(
        "3.7", "3.7/domain-guarded",
        # RUN 20 amended this proposition rather than deleting it. Run 19 required BOTH a
        # negative overrun and a negative budget to be refused. The budget half was a real
        # invalid-evidence hole and is closed. The overrun half conflicted with
        # field_registry.SIGNED_SI_FIELDS, which names analogousOverrunPct as one of four fields
        # where a negative value is a real project condition because a reference project can
        # underrun. That contract was followed, and what the proposition now requires of the
        # negative case is the part that was genuinely wrong: no negative quantity of money at
        # risk may be reported.
        "a budget outside the domain it can occupy is refused rather than producing a banded "
        "result, and no result reports a negative quantity of money at risk",
        abstained(neg_bac) and (neg.get("bac_exposure") or 0) >= 0,
        f"an overrun percent of minus fifty bands "
        f"{neg.get('status_color')!r} and reports an exposure of "
        f"{neg.get('bac_exposure')!r}, a negative quantity of money at risk. A budget at "
        f"completion of minus one thousand bands {neg_bac.get('status_color')!r} with an "
        f"exposure of {neg_bac.get('bac_exposure')!r}. Neither input is guarded at all: the "
        f"band reads the percent alone and the budget only scales a displayed figure, so an "
        f"invalid budget reaches a coloured result. This is the pattern the programme has "
        f"already corrected in eleven other modules")


# =============================================================================================
# 3.8 PARAMETRIC COST INDEX -- specification 12, "3.8". CONCEPT ONLY, STAYS DISABLED.
# =============================================================================================

def m_3_8() -> None:
    A.near("3.8", "known-answer: the specification's parametric model 10 + 2*4 + 3*5",
           O.parametric_cost(10, [2, 3], [4, 5]), 33.0)
    A.near("3.8", "invariant: the intercept is the prediction when every driver is zero",
           O.parametric_cost(10, [2, 3], [0, 0]), 10.0)
    A.check("3.8", "invariant: the model is linear in each driver, so doubling a driver's "
                   "contribution is doubling its coefficient",
            abs(O.parametric_cost(0, [4], [5]) - O.parametric_cost(0, [2], [10])) < 1e-12)
    try:
        O.parametric_cost(10, [2, 3], [4])
        A.check("3.8", "boundary: a nonconforming design matrix is refused", False)
    except ValueError:
        A.check("3.8", "boundary: a design matrix that does not conform with the coefficient "
                       "vector is refused rather than predicted from", True)

    # Production is short-circuited before its formula, so what is assessed is the formula the
    # module WOULD run, read from source, against the canonical definition.
    src = (HERE.parent / "app" / "simulation" / "models_ext.py").read_text(encoding="utf-8")
    body = src.split("def run_parametric_cost")[1].split("\ndef ")[0]
    A.proposition(
        "3.8", "3.8/design-matrix",
        "the module carries measurable cost drivers and fitted coefficients, which is what makes "
        "a model parametric",
        any(t in body for t in ("coefficient", "beta", "driver", "design_matrix")),
        "the formula the module would run is (BAC / CPI) divided by (AC + BAC - EV): the ratio "
        "of two earned-value forecasts of the same project. Specification 3.8 states in terms "
        "that comparing two EAC formulas is not parametric estimating. There is no driver, no "
        "coefficient, no intercept and no design matrix anywhere in it, and both forecasts are "
        "transformations of the same earned-value inputs, so their ratio is one body of evidence "
        "divided by itself rather than a model of cost against measurable drivers")
    A.check("3.8", "the module remains operationally disabled and non-voting whatever this "
                   "laboratory finding says, since a laboratory result is not permission to "
                   "activate", run("A3.8", {"bac": 1000, "ev": 400, "ac": 500, "cpi": 0.8,
                                            "actualPctComplete": 40}).get("activation_state")
            == "DISABLED_UNSAFE" and "A3.8" not in REG.CORE_VOTING_MODULES)


# =============================================================================================
# 3.9 INFLATION ADJUSTMENT INDEX -- specification 12, "3.9"
# =============================================================================================

def m_3_9() -> None:
    A.near("3.9", "known-answer: the specification's index 200 to 220 is a factor of 1.10",
           O.escalation_factor(220, 200), 1.10)
    A.near("3.9", "known-answer: a base cost of 100 adjusts to 110",
           O.adjusted_cost(100, 220, 200), 110.0)
    A.check("3.9", "invariant: an unchanged index leaves the cost unchanged",
            O.adjusted_cost(100, 200, 200) == 100)
    A.check("3.9", "invariant: a falling index deflates rather than flooring at zero, which is "
                   "a property of the canonical factor",
            O.escalation_factor(180, 200) < 1.0)

    out = run("A3.9", {"materialCostBaseline": 1000, "materialCostCurrent": 600,
                       "actualPctComplete": 50})
    A.near("3.9", "structure: the declared escalation is the excess above a progress-scaled "
                  "material baseline", out.get("escalation_pct"), 20, 0.5)
    A.check("3.9", "invariant: escalation rises monotonically with current material cost",
            [run("A3.9", {"materialCostBaseline": 1000, "materialCostCurrent": c,
                          "actualPctComplete": 50}).get("escalation_pct")
             for c in (500, 550, 600)] == [0, 10, 20])
    A.proposition(
        "3.9", "3.9/no-unscaled-baseline-on-missing-progress",
        "withholding the progress figure does not enlarge the denominator and buy a calmer band",
        abstained(run("A3.9", {"materialCostBaseline": 1000, "materialCostCurrent": 900})))
    A.check("3.9", "invalid input: a negative material cost is refused rather than being floored "
                   "to exactly nought escalation, which is the reading of a project with none",
            abstained(run("A3.9", {"materialCostBaseline": 1000, "materialCostCurrent": -100000,
                                   "actualPctComplete": 50})))
    A.check("3.9", "invalid input: a negative baseline is refused",
            abstained(run("A3.9", {"materialCostBaseline": -1000, "materialCostCurrent": 500,
                                   "actualPctComplete": 50})))
    A.check("3.9", "invalid input: progress outside nought to one hundred is refused",
            abstained(run("A3.9", {"materialCostBaseline": 1000, "materialCostCurrent": 500,
                                   "actualPctComplete": 400})))
    A.check("3.9", "boundary: a baseline scaled to zero by zero progress is refused",
            abstained(run("A3.9", {"materialCostBaseline": 1000, "materialCostCurrent": 500,
                                   "actualPctComplete": 0})))
    A.check("3.9", "missingness: both cost figures are required",
            abstained(run("A3.9", {"materialCostBaseline": 1000})))

    A.proposition(
        "3.9", "3.9/external-index",
        "escalation is computed from an external governed price index carrying a series, a "
        "geography, a commodity scope, a base period, a current period and a vintage",
        any(k in out for k in ("index_series", "index_base", "index_current", "index_source",
                              "index_vintage", "geography")),
        "the module divides this project's own current material cost by its own progress-scaled "
        "material baseline. Specification 3.9 states in terms that a current over baseline "
        "material-price ratio with no external index is not a macro or regional inflation "
        "adjustment. No index, no base period, no geography and no vintage exist anywhere. The "
        "module's own evidence sentence calls the figure a material escalation proxy, which is "
        "an honest disclosure, but the registered name says inflation adjustment index")
    deflation = run("A3.9", {"materialCostBaseline": 1000, "materialCostCurrent": 100,
                             "actualPctComplete": 50})
    A.proposition(
        "3.9", "3.9/deflation-visible",
        "a current cost below the progress-scaled baseline is reported as the deflation it is, "
        "rather than floored to zero",
        deflation.get("escalation_pct") is not None and deflation.get("escalation_pct") < 0,
        f"a current material cost eighty per cent below the progress-scaled baseline reports "
        f"{deflation.get('escalation_pct')!r} per cent escalation, because the quantity is "
        f"floored by max(0, ...). A genuine index factor deflates below one, as the oracle "
        f"confirms. The floor is defensible for a measure named escalation, but it means the "
        f"module cannot distinguish a project exactly on its material baseline from one eighty "
        f"per cent under it, and both read Green")


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
    write_results(HERE / "run17" / "categories" / "category_3_results.csv", RESULT_HEADER, rows)
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
