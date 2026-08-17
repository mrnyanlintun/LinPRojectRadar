"""
RUN 19 -- Category 10, decision optimisation. Seven scientific targets.

Four of them, 10.1, 10.2, 10.5 and 10.6, are concept-only and MUST REMAIN DISABLED AND
NON-VOTING. Their mathematics is testable in the laboratory and is tested here, and a laboratory
result is not permission to activate.

Supervisory specification section 19 states the canonical flow:
    Qualified Project State -> Candidate Actions -> Feasibility and Constraints -> Objectives
    -> Optimisation and Comparison -> Scenario, Sensitivity and Regret -> Human Authorised
    Selection,
and states that the input to this category is not merely cost and schedule indices. Whether
candidate ACTIONS exist at all is therefore the first question asked of every module here.

Oracles come from run17/oracle/oracles_cat_10.py, self proved at import: the linear programme is
solved by vertex enumeration rather than by any solver, Pareto by exhaustive pairwise
comparison, and minimax regret from a hand regret matrix, which is what specification 24 asks for.
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

# =================================================================================================
# RUN 31 v19: THIS SUITE SUPPLIES THE GOVERNED CATEGORY-9 ASSESSMENT ITS MODULES NOW REQUIRE.
#
# From sim-2026.08-v19 a package with no Category-9 assessment FAILS CLOSED for every
# Category-6/7/8/10 consumer. This suite's purpose is a module's ARITHMETIC, so it supplies the
# ordinary governed assessment a real caller supplies, through the ordinary signal-input key, and
# then tests the arithmetic it was written to test. It is not exempt from the gate: the ordinary
# precedence still applies, and the gate's own guards never install this.
# =================================================================================================
import run31_qualified_fixture as _R31Q                                       # noqa: E402
_R31Q.install()


CUTOFF = datetime.date(2026, 6, 30)
RAND = lambda: 0.5  # noqa: E731

KNOWN_DEFECTS = {
    "10.1/candidate-actions": "METHOD_LABEL_MISMATCH",
    "10.1/nondominated-set": "METHOD_LABEL_MISMATCH",
    "10.2/decision-variables": "MISSING_CANONICAL_DATA_STRUCTURE",
    "10.3/general-csp": "CORRECT_PROXY_ONLY",
    "10.4/action-identity": "METHOD_LABEL_MISMATCH",
    "10.5/decision-model-perturbed": "METHOD_LABEL_MISMATCH",
    "10.6/dominance-computed": "METHOD_LABEL_MISMATCH",
}

A = Audit("category 10", KNOWN_DEFECTS)

#: Loaded through the gate so the oracle's own import-time self-proof becomes a
#: named red with a canonical RESULT line, rather than a traceback that the strict
#: runner would reject for the wrong reason.
O = oracle_gate(A, "oracles_cat_10")

CONCEPT_ONLY = ("B4.1", "B4.2", "B4.5", "B4.6")
FULL = {"bac": 1000, "ev": 400, "ac": 500, "pv": 500, "cpi": 0.80, "spi": 0.85,
        "docRiskScore": 0.30}


# HISTORICAL_ONLY (Run 32). This entire suite is Run 19's audit OF THE v19 CATEGORY-10
# IMPLEMENTATIONS. Run 32 repointed all seven onto the canonical decision layer, so resolving
# these assertions through the live dispatcher would stop measuring the thing Run 19 measured.
# The v19 implementations are PRESERVED, not deleted, precisely because this audit is evidence
# about them, and `run` resolves to them through the historical extension mechanism. Every
# assertion below is unchanged.
#
# The disabled short-circuit is preserved by asking the registry FIRST: a concept-only module
# must still report its governed disabled state, which is a fact about the registry rather than
# about either implementation.
import run32_historical_cat10 as _H32  # noqa: E402


def run(code_id: str, si: dict) -> dict:
    if code_id in _H32.LEGACY_CAT10 and code_id not in REG.DISABLED_MODULES:
        return _H32.run_legacy(code_id, dict(si), RAND, CUTOFF)
    return REG.run_module(code_id, si, RAND, CUTOFF)


def abstained(out: dict) -> bool:
    return bool(out.get("insufficient_data")) or out.get("status_color") is None


def source_of(fn_name: str) -> str:
    src = (HERE.parent / "app" / "simulation" / "models_gov.py").read_text(encoding="utf-8")
    return src.split(f"def {fn_name}")[1].split("\ndef ")[0]


def gate() -> None:
    A.check("GATE", "the Category 10 oracle reproduces the specification's worked answers",
            not O.self_test(), "; ".join(O.self_test()))
    ids = {t["module_id"] for t in population()}
    for mid in ("10.1", "10.2", "10.3", "10.4", "10.5", "10.6", "10.7"):
        A.check("GATE", f"{mid} is one of the hundred scientific targets", mid in ids)
    for code in ("B4.1", "B4.2", "B4.3", "B4.4", "B4.5", "B4.6", "B4.7"):
        A.check("GATE", f"{code} is non-voting", code not in REG.CORE_VOTING_MODULES)
    for code in CONCEPT_ONLY:
        out = run(code, dict(FULL))
        A.check("GATE", f"{code} remains disabled as concept-only and is short-circuited before "
                        f"its formula function is reached, on a complete input",
                out.get("activation_state") == "DISABLED_UNSAFE" and abstained(out))


# =============================================================================================
# 10.1 MULTI-OBJECTIVE OPTIMISATION -- specification 19, "10.1". CONCEPT ONLY, STAYS DISABLED.
# =============================================================================================

def m_10_1() -> None:
    pts = {"A": (10.0, 5.0), "B": (8.0, 8.0), "C": (12.0, 4.0), "D": (13.0, 9.0)}
    front = O.nondominated(pts)
    A.check("10.1", "known-answer: the specification's discrete feasible set has A, B and C "
                    "nondominated and D dominated", front == {"A", "B", "C"}, str(sorted(front)))
    A.check("10.1", "known-answer: A dominates D", O.dominates(pts["A"], pts["D"]))
    A.check("10.1", "invariant: two mutually nondominated points dominate each other in neither "
                    "direction, which is what a genuine trade-off is",
            not O.dominates(pts["A"], pts["B"]) and not O.dominates(pts["B"], pts["A"]))
    A.check("10.1", "invariant: the frontier does not depend on the order the alternatives are "
                    "presented in",
            O.nondominated({k: pts[k] for k in ("D", "C", "B", "A")}) == front)

    body = source_of("run_multi_objective")
    A.proposition(
        "10.1", "10.1/candidate-actions",
        "the module carries decision variables and candidate interventions to optimise over, "
        "with constraints and a feasible region, as specification 10.1 requires",
        any(t in body for t in ("candidate", "action", "decision_variable", "constraint_set",
                                "feasible_region")),
        "the formula the module would run normalises the cost index, the schedule index and one "
        "minus the document risk score onto nought to one, and reports their arithmetic mean. "
        "Specification 10.1 states in terms that a weighted average of current cost, schedule "
        "and risk is not multi-objective optimisation. There is no decision variable, no "
        "candidate intervention, no constraint, no feasible region and no decision horizon: "
        "there is nothing to optimise over, only a description of the project's current state")
    A.proposition(
        "10.1", "10.1/nondominated-set",
        "the output exposes nondominated trade-offs rather than collapsing several objectives "
        "into one number, which specification 10.1 says should normally be the case",
        "pareto" in body.lower() and "nondominated" in body.lower(),
        "the three objectives are averaged into a single score and the lowest-scoring one is "
        "labelled the binding constraint. Averaging is exactly the operation that destroys the "
        "trade-off information multi-objective optimisation exists to expose, and calling the "
        "worst of three descriptive scores a binding constraint attaches an optimisation term "
        "to a quantity that constrains nothing. The field carrying the average is named "
        "pareto_score, which the laboratory oracle shows has no relation to Pareto dominance")
    A.check("10.1", "the module remains operationally disabled and non-voting whatever this "
                    "laboratory finding says",
            run("B4.1", dict(FULL)).get("activation_state") == "DISABLED_UNSAFE")


# =============================================================================================
# 10.2 LINEAR PROGRAMMING -- specification 19, "10.2". CONCEPT ONLY, STAYS DISABLED.
# =============================================================================================

def m_10_2() -> None:
    lp = O.solve_lp_by_vertex_enumeration(O.WYNDOR["objective"], O.WYNDOR["constraints"])
    A.check("10.2", "known-answer: the Wyndor Glass problem is feasible", lp["feasible"])
    A.near("10.2", "known-answer: the optimal first variable is 2", lp["solution"][0], 2.0, 1e-6)
    A.near("10.2", "known-answer: the optimal second variable is 6", lp["solution"][1], 6.0, 1e-6)
    A.near("10.2", "known-answer: the optimal objective value is 36", lp["objective"], 36.0, 1e-6)
    A.check("10.2", "known-answer: the second and third constraints are binding at the optimum",
            set(lp["binding"]) == {1, 2}, str(lp["binding"]))
    A.check("10.2", "boundary: nonnegativity is enforced, so a constraint requiring a negative "
                    "value of a nonnegative variable is infeasible and is rejected",
            not O.solve_lp_by_vertex_enumeration(
                (1.0, 1.0), [((1.0, 0.0), -5.0)])["feasible"])
    A.check("10.2", "invariant: an infeasible candidate is rejected rather than returned as an "
                    "optimum with a violated constraint",
            O.solve_lp_by_vertex_enumeration(
                (1.0, 1.0), [((1.0, 0.0), -5.0)])["solution"] is None)
    A.check("10.2", "invariant: scaling the objective scales the optimal value and leaves the "
                    "optimal point unchanged, since the feasible region did not move",
            O.solve_lp_by_vertex_enumeration((6.0, 10.0), O.WYNDOR["constraints"])["solution"]
            == lp["solution"])

    body = source_of("run_linear_programming")
    A.proposition(
        "10.2", "10.2/decision-variables",
        "the module can represent a linear programme: decision variables, an objective function, "
        "linear constraints and a feasible region, such that the Wyndor problem could be posed "
        "to it",
        any(t in body for t in ("objective_function", "decision_variable", "constraints",
                                "simplex", "vertex")),
        "the formula the module would run divides remaining work by remaining budget to get a "
        "required cost index, calls it feasible when that is at most 1.20 and optimal when it is "
        "at most 1.00, and bands the result. There is no decision variable, no objective "
        "function, no constraint set and no feasible region: nothing is being optimised and "
        "nothing is being chosen. Specification 10.2 states that where the module cannot "
        "represent the Wyndor problem the disposition is a missing canonical data structure, and "
        "it cannot: there is no input through which two variables and three constraints could "
        "be supplied. The words feasible and optimal are attached to a single ratio")
    A.check("10.2", "the module remains operationally disabled and non-voting",
            run("B4.2", dict(FULL)).get("activation_state") == "DISABLED_UNSAFE")


# =============================================================================================
# 10.3 CONSTRAINT SATISFACTION ANALYSIS -- specification 19, "10.3"
# =============================================================================================

def m_10_3() -> None:
    sols = O.csp_solutions({"X": ["A", "B"], "Y": [1, 2]},
                           [lambda a: not (a["X"] == "A" and a["Y"] == 1)])
    got = {(s["X"], s["Y"]) for s in sols}
    A.check("10.3", "known-answer: the specification's tiny problem has three feasible "
                    "assignments", got == {("A", 2), ("B", 1), ("B", 2)}, str(sorted(got)))
    A.check("10.3", "known-answer: the one assignment the constraint forbids is infeasible",
            ("A", 1) not in got)
    A.check("10.3", "boundary: a constraint set with no satisfying assignment returns none "
                    "rather than the closest near miss",
            O.csp_solutions({"X": [1, 2]}, [lambda a: a["X"] > 5]) == [])
    A.check("10.3", "invariant: removing a constraint cannot remove a solution",
            len(O.csp_solutions({"X": ["A", "B"], "Y": [1, 2]}, []))
            >= len(sols))

    out = run("B4.3", dict(FULL))
    A.check("10.3", "structure: the module reports which of its rules were violated by name",
            isinstance(out.get("violated_constraints"), list))
    A.check("10.3", "known-answer: a project meeting every rule satisfies four of four",
            run("B4.3", {"cpi": 1.0, "spi": 1.0, "bac": 1000,
                         "docRiskScore": 0.1}).get("satisfied") == 4)
    A.check("10.3", "known-answer: a project failing every rule satisfies none",
            run("B4.3", {"cpi": 0.5, "spi": 0.5, "bac": 1000,
                         "docRiskScore": 0.9}).get("satisfied") == 0)
    A.check("10.3", "invariant: the satisfaction rate is monotone as rules begin to fail",
            [run("B4.3", {"cpi": c, "spi": 1.0, "bac": 1000,
                          "docRiskScore": 0.1}).get("satisfied")
             for c in (1.0, 0.85, 0.5)] == [4, 3, 2])
    A.check("10.3", "boundary: exactly at a rule boundary the rule is satisfied, since the "
                    "declared comparison is inclusive",
            run("B4.3", {"cpi": 0.90, "spi": 0.90, "bac": 1000,
                         "docRiskScore": 0.1}).get("satisfied") == 4)
    A.check("10.3", "missingness: the cost index, schedule index and budget are required",
            abstained(run("B4.3", {"cpi": 0.9})))

    body = source_of("run_constraint_satisfaction")
    A.proposition(
        "10.3", "10.3/general-csp",
        "the module accepts variables, domains and constraints and searches for assignments "
        "satisfying all of them, which is what a constraint satisfaction problem is",
        any(t in body for t in ("domain", "assignment", "variables", "solution_space")),
        "four rules are hard-coded as comparisons against fixed thresholds on the cost index, "
        "the schedule index and the document risk score, and the module reports how many of the "
        "four hold. There is no variable, no domain, no assignment and no search. Specification "
        "10.3 says in terms that a four-rule management checklist is a transparent feasibility "
        "rule set rather than a general solver, and should be classified according to its actual "
        "claim. The rule set is coherent and its results are exact; the module name is what "
        "overstates it")
    far_rule = [c for c in run("B4.3", {"cpi": 0.75, "spi": 1.0, "bac": 1000,
                                        "docRiskScore": 0.1}).get("violated_constraints", [])
                if "FAR" in c]
    # RUN 20 CYCLE 2. This proposition now HOLDS and is no longer in the register above.
    #
    # THE SUPERSEDED READING, recorded because it must not come back: one of the four rules was
    # presented to the reader as 'FAR threshold (overrun < 25%)' and implemented as a cost index
    # above 0.80. The arithmetic is self-consistent, since a forecast of budget over an index of
    # 0.80 is a twenty-five per cent overrun, but no provision of the Federal Acquisition
    # Regulation states a twenty-five per cent overrun threshold of this kind and none was
    # cited. The remediation removed the attribution and changed no comparison: the rule is now
    # named for the forecast overrun it measures.
    A.proposition(
        "10.3", "10.3/no-regulatory-label-on-a-performance-threshold",
        "no rule carries a regulatory authority's name unless that authority actually states "
        "the threshold the rule applies",
        not far_rule)
    A.check("10.3", "the renamed rule still names the comparison it makes and still fires on the "
                    "same projects, so a false attribution was removed and no boundary moved",
            [c for c in run("B4.3", {"cpi": 0.75, "spi": 1.0, "bac": 1000,
                                     "docRiskScore": 0.1}).get("violated_constraints", [])
             if "Forecast overrun below 25%" in c]
            and not [c for c in run("B4.3", {"cpi": 0.81, "spi": 1.0, "bac": 1000,
                                             "docRiskScore": 0.1}).get("violated_constraints", [])
                     if "Forecast overrun" in c])
    A.check("10.3", "the four rule thresholds have no cited source and the module does not vote",
            "B4.3" not in REG.CORE_VOTING_MODULES)


# =============================================================================================
# 10.4 WHAT-IF SCENARIO MATRIX -- specification 19, "10.4"
# =============================================================================================

def m_10_4() -> None:
    # The specification's action-by-scenario matrix, preserved here for 10.7 as it requires.
    A.check("10.4", "known-answer: the specification's decision matrix has three actions and two "
                    "scenarios, and each cell is one action's outcome under one scenario",
            len(O.SPEC_PAYOFFS) == 3
            and all(set(v) == {"S1", "S2"} for v in O.SPEC_PAYOFFS.values()))
    A.check("10.4", "invariant: no action in the specification's matrix dominates every other "
                    "under every scenario, which is what makes the decision non-trivial",
            not any(all(O.SPEC_PAYOFFS[a][s] >= O.SPEC_PAYOFFS[b][s] for s in ("S1", "S2"))
                    and a != b
                    for a in O.SPEC_PAYOFFS for b in O.SPEC_PAYOFFS if a != b))

    out = run("B4.4", dict(FULL))
    A.check("10.4", "structure: four named scenarios are reported with a forecast for each",
            len(out.get("scenarios", [])) == 4)
    A.near("10.4", "known-answer: the base scenario is budget over the cost index",
           out.get("base_eac"), 1000 / 0.80, 1.0)
    A.check("10.4", "invariant: the optimistic scenario forecasts no more than the pessimistic",
            out["scenarios"][0]["eac"] <= out["scenarios"][2]["eac"])
    A.check("10.4", "invariant: the reported range widens as cost performance falls",
            [run("B4.4", {**FULL, "cpi": c}).get("scenario_range_pct")
             for c in (1.0, 0.8, 0.6)] == sorted(
                [run("B4.4", {**FULL, "cpi": c}).get("scenario_range_pct")
                 for c in (1.0, 0.8, 0.6)]))
    A.proposition(
        "10.4", "10.4/domains-guarded",
        "a zero or negative index, a non-positive budget, negative earned value or actual cost, "
        "and earned value exceeding the budget are each refused rather than forecast from",
        all(abstained(run("B4.4", {**FULL, **bad})) for bad in
            ({"cpi": 0}, {"spi": 0}, {"cpi": -0.5}, {"bac": 0}, {"bac": -100},
             {"ev": -50}, {"ac": -50}, {"ev": 1500})))
    A.check("10.4", "missingness: all five earned-value figures are required",
            abstained(run("B4.4", {"bac": 1000})))

    A.proposition(
        "10.4", "10.4/action-identity",
        "the rows of the matrix are CANDIDATE ACTIONS with identity, and the columns are "
        "scenarios, so each cell is the outcome of taking one action under one future state",
        any("action" in str(s.get("name", "")).lower()
            or s.get("action_id") for s in out.get("scenarios", [])),
        "the four rows are 'Optimistic (CPI recovers to 1.0)', 'Base (current CPI continues)', "
        "'Pessimistic (CPI degrades 5%)' and 'Recovery (CPI improves 5%)'. Every one of them is "
        "a FUTURE STATE of the cost index, not an action anyone could take, and each is a "
        "different arithmetic transformation of the same three earned-value figures. "
        "Specification 10.4 states that several EAC formulas with no action identity are not an "
        "action-by-scenario decision matrix, and distinguishes this category from Category 5 on "
        "exactly this point: Category 5 models what happens to the system under conditions, "
        "Category 10 compares which action to take. This module does the former under the "
        "latter's name, so the matrix specification 10.7 needs preserved for regret analysis is "
        "never produced")


# =============================================================================================
# 10.5 DECISION SENSITIVITY MATRIX -- specification 19. CONCEPT ONLY, STAYS DISABLED.
# =============================================================================================

def m_10_5() -> None:
    x = O.ranking_crossover(lambda w: w, lambda w: 1 - w)
    A.near("10.5", "known-answer: two alternatives whose ranking flips at a weight of one half",
           x, 0.5, 1e-4)
    A.check("10.5", "known-answer: the ranking really does differ on the two sides of the "
                    "crossover, so the decision changes rather than only the scores",
            (0.4 > 1 - 0.4) != (0.6 > 1 - 0.6))
    A.check("10.5", "boundary: two alternatives whose ranking never flips report no crossover",
            O.ranking_crossover(lambda w: w + 10, lambda w: w) is None)

    body = source_of("run_decision_sensitivity")
    A.proposition(
        "10.5", "10.5/decision-model-perturbed",
        "a decision model with base parameter values is perturbed over declared ranges and the "
        "action ranking recomputed, so the output shows whether the DECISION changes",
        any(t in body for t in ("perturb", "crossover", "base_case", "recompute", "range")),
        "the formula the module would run takes the absolute deviation of the cost index from "
        "one, the same for the schedule index, and the document risk score times fifty, and "
        "ranks those three numbers by size. Specification 10.5 states in terms that ranking "
        "current cost and schedule deviations without perturbing a decision model is not "
        "decision sensitivity. No parameter is perturbed, no ranking is recomputed and no "
        "decision exists to be sensitive. The reported sentence tells the reader that a small "
        "change in the top driver 'most changes the governance recommendation', which is a "
        "causal claim about a recommendation the module never evaluates. The 50 multiplier on "
        "document risk sets the relative weight of the three drivers and has no source")
    A.check("10.5", "the module remains operationally disabled and non-voting",
            run("B4.5", dict(FULL)).get("activation_state") == "DISABLED_UNSAFE")


# =============================================================================================
# 10.6 PARETO FRONTIER ANALYSIS -- specification 19. CONCEPT ONLY, STAYS DISABLED.
# =============================================================================================

def m_10_6() -> None:
    pts = {"A": (10.0, 5.0), "B": (8.0, 8.0), "C": (12.0, 4.0), "D": (13.0, 9.0)}
    front = O.nondominated(pts)
    A.check("10.6", "known-answer: the specification's frontier is A, B and C, with D dominated",
            front == {"A", "B", "C"}, str(sorted(front)))
    A.check("10.6", "invariant: permutation invariance, the frontier does not depend on input "
                    "order", O.nondominated({k: pts[k] for k in ("C", "A", "D", "B")}) == front)
    dup = dict(pts, A2=pts["A"])
    A.check("10.6", "invariant: duplicate points do not dominate each other and both remain on "
                    "the frontier", {"A", "A2"} <= O.nondominated(dup))
    A.check("10.6", "boundary: a single point is trivially nondominated",
            O.nondominated({"only": (1.0, 1.0)}) == {"only"})
    A.check("10.6", "invariant: a point strictly worse in every objective than another is always "
                    "dominated", O.dominates((1.0, 1.0), (2.0, 2.0)))

    body = source_of("run_pareto_frontier")
    A.proposition(
        "10.6", "10.6/dominance-computed",
        "the module compares two or more alternatives and computes which are dominated, which "
        "is the entire content of Pareto analysis",
        any(t in body for t in ("dominates(", "alternatives", "frontier_points", "nondominated")),
        "the formula the module would run evaluates three booleans on ONE project, cost index at "
        "least 0.95, schedule index at least 0.95 and document risk below 0.30, and reports the "
        "project as efficient, dominated or requiring a trade-off according to how many hold. "
        "Specification 10.6 states in terms that threshold booleans over one project are not "
        "Pareto analysis. Dominance is a relation BETWEEN alternatives and there is only ever "
        "one alternative here, so nothing can dominate anything. The word dominated is applied "
        "to a project failing two thresholds, which is a different meaning of the same word, and "
        "the reader is told the project 'is Pareto-dominated'. The 0.95 and 0.30 boundaries have "
        "no source")
    A.check("10.6", "the module remains operationally disabled and non-voting",
            run("B4.6", dict(FULL)).get("activation_state") == "DISABLED_UNSAFE")


# =============================================================================================
# 10.7 REGRET MINIMISATION INDEX -- specification 19, "10.7"
# =============================================================================================

def m_10_7() -> None:
    r = O.regret_matrix(O.SPEC_PAYOFFS)
    A.check("10.7", "known-answer: the specification's scenario maxima are ten and ten",
            r["scenario_maxima"] == {"S1": 10.0, "S2": 10.0}, str(r["scenario_maxima"]))
    A.check("10.7", "known-answer: the specification's maximum regrets are eight, four and eight",
            r["max_regret"] == {"A": 8.0, "B": 4.0, "C": 8.0}, str(r["max_regret"]))
    A.check("10.7", "known-answer: the minimax-regret choice is the hedging action",
            r["choice"] == "B", str(r["choice"]))
    A.check("10.7", "invariant: an action that is best under every scenario has no regret at all",
            max(O.regret_matrix({"best": {"S1": 10.0, "S2": 10.0},
                                 "other": {"S1": 1.0, "S2": 1.0}})["regrets"]["best"].values())
            == 0)
    A.check("10.7", "invariant: every regret is non-negative, since it is measured against the "
                    "best available payoff in its own scenario",
            all(v >= 0 for row in r["regrets"].values() for v in row.values()))
    A.check("10.7", "metamorphic: adding a constant to every payoff in one scenario leaves the "
                    "regrets in that scenario unchanged, since both the maximum and each payoff "
                    "shift together",
            O.regret_matrix({a: {"S1": p["S1"] + 100, "S2": p["S2"]}
                             for a, p in O.SPEC_PAYOFFS.items()})["max_regret"]
            == r["max_regret"])

    A.proposition(
        "10.7", "10.7/abstains-without-payoff-matrix",
        "with no set of courses of action scored against defined future states the module "
        "abstains, which specification 10.7 states is the correct result",
        all(abstained(run("B4.7", si)) for si in
            ({}, dict(FULL), {"cpi": 1.3, "spi": 1.3, "bac": 1000, "docRiskScore": 0.0},
             {"cpi": 0.5, "spi": 0.5, "bac": 10 ** 8, "docRiskScore": 1.0})))
    A.check("10.7", "missingness: the abstention names the missing structure as courses of "
                    "action scored against future states, without inventing one",
            "courses of action" in str(run("B4.7", {}).get("evidence_metric", "")).lower())
    A.check("10.7", "invariant: no project input can move the result while the payoff matrix is "
                    "absent, so no fixed project-independent choice is being published",
            len({str(run("B4.7", {"cpi": c, "spi": s, "bac": 1000, "docRiskScore": d}))
                 for c in (0.7, 1.0, 1.3) for s in (0.7, 1.3) for d in (0.0, 0.9)}) == 1)
    A.check("10.7", "the module does not vote and is excluded from the recommendation text and "
                    "the courses of action a participant chooses among",
            "B4.7" not in REG.CORE_VOTING_MODULES)


# =============================================================================================
# RESULT ROWS
# =============================================================================================

def _row(mid, name, basis, source, sreq, spres, impl, thresh, lineage, disp, finding, nxt,
         activation="ADVISORY_ONLY") -> dict:
    return {
        "module_id": mid, "module_name": name, "category": "10", "basis_class": basis,
        "operational_activation": activation, "voting_status": "non-voting",
        "primary_method_source": source, "canonical_structure_required": sreq,
        "canonical_structure_present": spres, "implementation_verified": impl,
        "known_answer_pass": "yes", "boundary_pass": "yes", "missingness_pass": "yes",
        "invariant_pass": "yes", "stochastic_diagnostics_pass": "n/a",
        "reproducibility_pass": "yes", "parameter_provenance_status": "NOT_SOURCED",
        "calibration_status": "NOT_CALIBRATED", "threshold_status": thresh,
        "empirical_validation_status": "NOT_DONE", "regulatory_snapshot": "n/a",
        "cat9_qualification_status": "RAW_UNQUALIFIED_INPUT", "lineage_status": lineage,
        "scientific_disposition": disp, "production_change_made": expected_flag(mid),
        "finding_summary": finding, "required_next_action": nxt,
        "test_names": "; ".join(A.coverage.get(mid, []))[:1800],
        "evidence_paths": ("server/tools/test_run19_category_10.py; "
                           "server/tools/run17/oracle/oracles_cat_10.py; "
                           "server/tools/run17/categories/category_10_faults.csv"),
    }


ROWS = lambda: [  # noqa: E731
    _row("10.1", "Multi-Objective Optimization", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 19 section 10.1; El-Rayes and Kandil (2005); Kandil and El-Rayes (2006)",
         "yes", "no", "no", "HEURISTIC_UNCALIBRATED", "SHARED_EVM_INPUT_VECTOR",
         "METHOD_LABEL_MISMATCH",
         "Concept-only and short-circuited before its formula, which was proved on a complete "
         "input. The formula it would run normalises the cost index, the schedule index and one "
         "minus document risk and reports their arithmetic mean, which specification 10.1 states "
         "in terms is not multi-objective optimisation. There is no decision variable, candidate "
         "intervention, constraint, feasible region or horizon: there is nothing to optimise "
         "over, only a description of the current state. Averaging is precisely the operation "
         "that destroys the trade-off information the method exists to expose, and the field "
         "carrying the average is named pareto_score although it has no relation to Pareto "
         "dominance, which the independent oracle establishes on the specification's own "
         "four-point set. Calling the lowest of three descriptive scores a binding constraint "
         "attaches an optimisation term to a quantity that constrains nothing.",
         "Remains disabled and non-voting. A laboratory result is not permission to activate. "
         "P3 on the naming; a real implementation is a new build, not a rename.",
         "DISABLED_UNSAFE"),
    _row("10.2", "Linear Programming", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 19 section 10.2; classical linear programming",
         "yes", "no", "no", "HEURISTIC_UNCALIBRATED", "SHARED_EVM_INPUT_VECTOR",
         "MISSING_CANONICAL_DATA_STRUCTURE",
         "Concept-only and short-circuited before its formula. The Wyndor Glass problem was "
         "solved independently by vertex enumeration, not by any solver, reproducing the "
         "specification's optimum of two and six with an objective value of thirty-six and the "
         "correct pair of binding constraints, and rejecting an infeasible candidate rather than "
         "returning it with a violated constraint. Production cannot represent that problem at "
         "all: the formula it would run divides remaining work by remaining budget to get a "
         "required cost index and calls the result feasible below 1.20 and optimal below 1.00. "
         "There is no decision variable, objective function, constraint set or feasible region, "
         "and no input through which two variables and three constraints could be supplied. "
         "Specification 10.2 states that where the module cannot represent the linear programme "
         "the disposition is a missing canonical data structure. The words feasible and optimal "
         "are attached to a single ratio.",
         "Remains disabled and non-voting. If linear programming is ever wanted it needs a "
         "decision-variable and constraint structure that does not exist anywhere in the corpus.",
         "DISABLED_UNSAFE"),
    _row("10.3", "Constraint Satisfaction Analysis", "D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
         "Specification 19 section 10.3; Lorterapong and Ussavadilokrit (2013)",
         "yes", "no", "yes", "HEURISTIC_UNCALIBRATED", "SHARED_EVM_INPUT_VECTOR",
         "CORRECT_PROXY_ONLY",
         "RUN 20 CYCLE 2 removed the governance overclaim carried inside this module. One rule "
         "was presented to the reader as 'FAR threshold (overrun < 25%)' and implemented as a "
         "cost index above 0.80. The arithmetic is self-consistent, since a forecast of budget "
         "over an index of 0.80 is a twenty-five per cent overrun, but no provision of the "
         "Federal Acquisition Regulation states such a threshold and none was cited. The rule "
         "is now named for the forecast-overrun comparison it makes; no comparison changed, so "
         "the same projects violate the same rules. "
         "The four rules are evaluated exactly, the satisfaction count is monotone as rules "
         "begin to fail, boundary values are handled inclusively as declared, and violated rules "
         "are reported by name rather than only counted, which is genuinely useful. The "
         "disposition does not move, and that is the honest result: there is still no variable, "
         "domain, assignment or search, and specification 10.3 says a four-rule management "
         "checklist is a transparent feasibility rule set that should be classified by its "
         "actual claim, which is what this is.",
         "P3. Rename the module to the transparent feasibility rule set it is, or build "
         "variables, domains and a search. The four rule thresholds remain unsourced."),
    _row("10.4", "What-If Scenario Matrix", "C. LITERATURE_SUPPORTED_ADAPTATION",
         "Specification 19 section 10.4; Collier et al. (2018)",
         "yes", "no", "no", "HEURISTIC_UNCALIBRATED", "SHARED_EVM_INPUT_VECTOR",
         "METHOD_LABEL_MISMATCH",
         "The domain guards here are the most thorough in the category and all hold: a zero or "
         "negative index, a non-positive budget, negative earned value or actual cost, and "
         "earned value exceeding the budget are each refused rather than forecast from. The four "
         "forecasts are exact and the reported range widens correctly as cost performance falls. "
         "But the four rows are 'Optimistic', 'Base', 'Pessimistic' and 'Recovery', which are "
         "all FUTURE STATES of the cost index rather than actions anyone could take, and each is "
         "a different arithmetic transformation of the same three earned-value figures. "
         "Specification 10.4 states that several EAC formulas with no action identity are not an "
         "action-by-scenario decision matrix, and separates this category from Category 5 on "
         "exactly this point. The consequence reaches further than the name: the matrix that "
         "specification 10.7 requires be preserved for regret analysis is never produced.",
         "P1. Carry candidate actions with identity as the rows and scenarios as the columns, or "
         "rename the module for the earned-value range analysis it performs and move it to "
         "Category 5."),
    _row("10.5", "Decision Sensitivity Matrix", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 19 section 10.5",
         "yes", "no", "no", "HEURISTIC_UNCALIBRATED", "SHARED_EVM_INPUT_VECTOR",
         "METHOD_LABEL_MISMATCH",
         "Concept-only and short-circuited before its formula. The laboratory oracle located the "
         "exact weight at which two alternatives change places and confirmed the ranking really "
         "differs on the two sides of it, which is what decision sensitivity establishes. "
         "Production does none of that: the formula it would run ranks the absolute deviation of "
         "the cost index from one, the same for the schedule index, and the document risk score "
         "times fifty. Specification 10.5 states in terms that ranking current deviations "
         "without perturbing a decision model is not decision sensitivity. No parameter is "
         "perturbed, no ranking is recomputed and no decision exists to be sensitive to "
         "anything. The sentence shown to a reader claims a small change in the top driver most "
         "changes the governance recommendation, which is a causal claim about a recommendation "
         "the module never evaluates. The 50 multiplier that sets the three drivers' relative "
         "weight has no source.",
         "Remains disabled and non-voting. The reported sentence should not survive a rebuild in "
         "its present form even if the module stays disabled.",
         "DISABLED_UNSAFE"),
    _row("10.6", "Pareto Frontier Analysis", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 19 section 10.6; Pareto nondominance",
         "yes", "no", "no", "HEURISTIC_UNCALIBRATED", "SHARED_EVM_INPUT_VECTOR",
         "METHOD_LABEL_MISMATCH",
         "Concept-only and short-circuited before its formula. Dominance was verified "
         "independently on the specification's four-point set, including permutation invariance "
         "and the duplicate-point case the specification asks for, and a single point is "
         "correctly trivially nondominated. Production evaluates three booleans on ONE project "
         "and reports it as efficient, dominated or requiring a trade-off according to how many "
         "hold. Specification 10.6 states in terms that threshold booleans over one project are "
         "not Pareto analysis. Dominance is a relation BETWEEN alternatives and there is only "
         "ever one alternative, so nothing can dominate anything; the word dominated is being "
         "used in a different sense from the method's, and the reader is told the project is "
         "Pareto-dominated. The 0.95 and 0.30 boundaries have no source.",
         "Remains disabled and non-voting. The Pareto vocabulary should not be applied to a "
         "single project even while the module is disabled.",
         "DISABLED_UNSAFE"),
    _row("10.7", "Regret Minimization Index", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 19 section 10.7; Savage minimax regret",
         "yes", "no", "n/a", "n/a", "NO_EVIDENCE_EMITTED", "CORRECT_ABSTENTION",
         "The method is defined by its action-by-scenario payoff matrix and no such matrix is "
         "held. The module abstains unconditionally and names the missing structure as courses "
         "of action scored against future states, without inventing one. Its result is "
         "byte-identical across every combination of cost index, schedule index, budget and "
         "document risk tested, which proves no fixed project-independent choice is being "
         "published under this name; the earlier state, in which every project was told to "
         "investigate because the healthy branch was unreachable from any input, is gone. The "
         "minimax-regret rule itself was verified independently against the specification's own "
         "matrix, reproducing scenario maxima of ten and ten, maximum regrets of eight, four and "
         "eight, and the hedging choice, together with the invariance of regret under a constant "
         "shift within a scenario. Abstention is the scientifically correct result.",
         "OWNER DECISION on whether a governed action-by-scenario payoff matrix should be built. "
         "Note that Category 10.4 does not currently produce one, so this module has no upstream "
         "source even in principle."),
]


def main() -> int:
    gate()
    m_10_1(); m_10_2(); m_10_3(); m_10_4(); m_10_5(); m_10_6(); m_10_7()
    rows = ROWS()
    write_results(HERE / "run17" / "categories" / "category_10_results.csv", RESULT_HEADER, rows)
    A.check("ROWS", "seven Category 10 result rows were written", len(rows) == 7)
    A.check("ROWS", "the four concept-only modules are recorded as disabled",
            sum(1 for r in rows if r["operational_activation"] == "DISABLED_UNSAFE") == 4)
    # RUN 20 CYCLE 2. Run 19 changed no production and this asserted so. Cycle 2 changed 10.3,
    # so the guard is narrowed to the declared manifest rather than removed: exactly the modules
    # the manifest names may record a change, and the manifest itself is checked against
    # production bytes by test_run20_declared_production_changes.py.
    A.check("ROWS", "a production change is recorded on exactly the rows the declared Run-20 "
                    "manifest names",
            {r["module_id"] for r in rows if r["production_change_made"] == "yes"} == {"10.3"})
    # THE OTHER HALF OF A HISTORICAL PROOF (Run 32). Everything above describes the v19
    # implementations. This proves current production reaches none of them, so no later run can
    # satisfy this audit by reconnecting a proxy.
    _H32.assert_not_reachable(
        lambda ok, label, detail="": A.check("ROUTE", label, ok))
    return A.finish()


if __name__ == "__main__":
    sys.exit(main())
