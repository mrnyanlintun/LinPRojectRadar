"""
RUN 32 -- INDEPENDENT ORACLES FOR THE CANONICAL CATEGORY-10 DECISION LAYER.

Every number checked here comes from the SUPPLIED CONTRACT, not from the implementation. The
point of an oracle is that it was decided before the code ran: the Wyndor optimum, the
nondominated set, the feasible CSP assignments, the 4/7 crossover and the minimax-regret
alternative are all stated in the run's contract, and this file asserts them literally.

Three properties are checked in addition to the supplied values, because each is a way the
methods could return the right answer for the wrong reason:

  * PERMUTATION INVARIANCE  -- a frontier that depends on input order is not a frontier.
  * ORIENTATION SENSITIVITY -- reading a cost matrix as payoffs must change the answer.
  * ABSTENTION             -- an absent or incomplete structure must produce no reading at all,
                              rather than a figure computed from something else.
"""

from __future__ import annotations

import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.simulation.canonical import StructureAbsent  # noqa: E402
from app.simulation import canonical_v7 as v7  # noqa: E402

CHECKS: list[tuple[str, bool]] = []


def check(name: str, ok: bool) -> None:
    CHECKS.append((name, bool(ok)))


def abstains(fn, structure) -> bool:
    try:
        fn(structure)
    except StructureAbsent:
        return True
    except Exception:
        return False
    return False


CTX = {"context_id": "RUN32-ORACLE", "source": "run32 supplied contract",
       "project": "ORACLE", "period": "2026-08"}


# =================================================================================================
# ORACLE 1 -- MULTI-OBJECTIVE / PARETO.  A=(10,5) B=(8,8) C=(12,4) D=(13,9)
# Supplied expectation: nondominated set = A, B, C.  D is dominated.
# Both objectives are COSTS, so smaller is better; D is worst on both and is dominated by all.
# =================================================================================================

MOO = dict(CTX, criteria=[
    {"criterion_id": "cost", "orientation": "cost", "label": "cost"},
    {"criterion_id": "time", "orientation": "cost", "label": "time"},
], alternatives=[
    {"alternative_id": "A", "values": {"cost": 10, "time": 5}},
    {"alternative_id": "B", "values": {"cost": 8, "time": 8}},
    {"alternative_id": "C", "values": {"cost": 12, "time": 4}},
    {"alternative_id": "D", "values": {"cost": 13, "time": 9}},
])

r = v7.multi_objective(MOO)
check("10.1 nondominated set is A B C", sorted(r["nondominated_set"]) == ["A", "B", "C"])
check("10.1 D is dominated", [d["alternative_id"] for d in r["dominated_set"]] == ["D"])
check("10.1 names no single best alternative", r["selected_alternative"] is None)
check("10.1 records that no preference information was supplied",
      r["preference_information_supplied"] is False)

p = v7.pareto_frontier(MOO)
check("10.6 frontier is A B C", sorted(p["frontier"]) == ["A", "B", "C"])
check("10.6 D is off the frontier", [d["alternative_id"] for d in p["dominated_set"]] == ["D"])

# PERMUTATION INVARIANCE: all 24 orderings of the same four alternatives.
orders_ok = True
for perm in itertools.permutations(MOO["alternatives"]):
    q = v7.pareto_frontier(dict(MOO, alternatives=list(perm)))
    if sorted(q["frontier"]) != ["A", "B", "C"]:
        orders_ok = False
check("10.6 frontier is identical under all 24 input orderings", orders_ok)

# DUPLICATE POINTS: an exact copy of A must also be on the frontier, never dominated by A.
dup = v7.pareto_frontier(dict(MOO, alternatives=MOO["alternatives"] + [
    {"alternative_id": "A2", "values": {"cost": 10, "time": 5}}]))
check("10.6 duplicate objective vectors both remain on the frontier",
      sorted(dup["frontier"]) == ["A", "A2", "B", "C"])

# ORIENTATION SENSITIVITY: flip both objectives to benefits and the answer must change.
flipped = v7.pareto_frontier(dict(MOO, criteria=[
    {"criterion_id": "cost", "orientation": "benefit"},
    {"criterion_id": "time", "orientation": "benefit"}]))
check("10.6 reading the same numbers as benefits changes the frontier to D",
      sorted(flipped["frontier"]) == ["D"])

# A DECLARED-INFEASIBLE alternative must leave the trade space.
infeas = v7.multi_objective(dict(MOO, alternatives=[
    dict(a, feasible=False) if a["alternative_id"] == "A" else a
    for a in MOO["alternatives"]]))
check("10.1 declared-infeasible alternative is excluded before dominance",
      "A" not in infeas["nondominated_set"]
      and [i["alternative_id"] for i in infeas["infeasible_alternatives"]] == ["A"])

check("10.1 abstains with no structure", abstains(v7.multi_objective, dict(CTX)))
check("10.6 abstains on a single alternative", abstains(v7.pareto_frontier, dict(
    MOO, alternatives=MOO["alternatives"][:1])))


# =================================================================================================
# ORACLE 2 -- LINEAR PROGRAMMING (Wyndor Glass).
#   maximise 3x1 + 5x2  s.t.  x1 <= 4;  2x2 <= 12;  3x1 + 2x2 <= 18;  x1, x2 >= 0
# Supplied expectation: x1 = 2, x2 = 6, objective = 36.
# =================================================================================================

LP = dict(CTX, objective_sense="maximize", variables=[
    {"variable_id": "x1", "objective_coefficient": 3, "lower_bound": 0},
    {"variable_id": "x2", "objective_coefficient": 5, "lower_bound": 0},
], constraints=[
    {"constraint_id": "plant1", "coefficients": {"x1": 1}, "operator": "<=", "rhs": 4},
    {"constraint_id": "plant2", "coefficients": {"x2": 2}, "operator": "<=", "rhs": 12},
    {"constraint_id": "plant3", "coefficients": {"x1": 3, "x2": 2}, "operator": "<=", "rhs": 18},
])

lp = v7.linear_program(LP)
check("10.2 Wyndor optimum x1 = 2", lp["optimum"]["x1"] == 2.0)
check("10.2 Wyndor optimum x2 = 6", lp["optimum"]["x2"] == 6.0)
check("10.2 Wyndor objective = 36", lp["objective_value"] == 36.0)
check("10.2 disposition is OPTIMAL", lp["disposition"] == "OPTIMAL")
check("10.2 plant2 and plant3 are binding at the optimum",
      {"plant2", "plant3"} <= set(lp["binding_constraints"]))

# INDEPENDENT CONFIRMATION: brute-force the integer lattice of the feasible region. The optimum
# happens to be integral here, so an exhaustive independent search must find the same value.
best = max((3 * a + 5 * b, a, b) for a in range(0, 5) for b in range(0, 10)
           if a <= 4 and 2 * b <= 12 and 3 * a + 2 * b <= 18)
check("10.2 independent exhaustive search agrees on 36", best[0] == 36 and (best[1], best[2]) == (2, 6))

# The declared non-negativity bound must be enforced: dropping the constraint that stops x2
# growing must change the answer, proving the bounds are live rather than decorative.
unbounded_side = v7.linear_program(dict(LP, constraints=[
    c for c in LP["constraints"] if c["constraint_id"] != "plant2"]))
check("10.2 removing a binding constraint changes the optimum",
      unbounded_side["objective_value"] != 36.0)

# MINIMISATION must not be assumed: the same model minimised is the origin.
mn = v7.linear_program(dict(LP, objective_sense="minimize"))
check("10.2 minimising the same model gives 0 at the origin", mn["objective_value"] == 0.0)

check("10.2 abstains when the objective sense is not declared",
      abstains(v7.linear_program, {k: v for k, v in LP.items() if k != "objective_sense"}))
check("10.2 abstains when a variable has no objective coefficient",
      abstains(v7.linear_program, dict(LP, variables=[
          {"variable_id": "x1", "lower_bound": 0},
          {"variable_id": "x2", "objective_coefficient": 5, "lower_bound": 0}])))
check("10.2 infeasible model reports INFEASIBLE rather than a number",
      v7.linear_program(dict(LP, constraints=LP["constraints"] + [
          {"constraint_id": "impossible", "coefficients": {"x1": 1}, "operator": ">=",
           "rhs": 99}]))["disposition"] == "INFEASIBLE")


# =================================================================================================
# ORACLE 3 -- CONSTRAINT SATISFACTION.
#   X in {A,B}, Y in {1,2};  constraint: if X = A then Y = 2.
# Supplied expectation: feasible = (A,2) (B,1) (B,2).  Infeasible = (A,1).
# =================================================================================================

CSP = dict(CTX, variables=[
    {"variable_id": "X", "domain": ["A", "B"]},
    {"variable_id": "Y", "domain": [1, 2]},
], constraints=[
    {"constraint_id": "c1", "type": "implication", "if": {"X": "A"}, "then": {"Y": 2}},
])

c = v7.constraint_satisfaction(CSP)
feasible = sorted((a["assignment"]["X"], a["assignment"]["Y"]) for a in c["feasible_assignments"])
infeasible = sorted((a["assignment"]["X"], a["assignment"]["Y"])
                    for a in c["infeasible_assignments"])
check("10.3 feasible assignments are (A,2) (B,1) (B,2)",
      feasible == [("A", 2), ("B", 1), ("B", 2)])
check("10.3 the single infeasible assignment is (A,1)", infeasible == [("A", 1)])
check("10.3 all four assignments were examined", c["assignments_examined"] == 4)
check("10.3 problem is satisfiable", c["satisfiable"] is True)

check("10.3 abstains when a variable has no domain", abstains(v7.constraint_satisfaction, dict(
    CSP, variables=[{"variable_id": "X", "domain": ["A"]}, {"variable_id": "Y"}])))
check("10.3 abstains when no constraints are declared",
      abstains(v7.constraint_satisfaction, dict(CSP, constraints=[])))
check("10.3 an unrecognised rule form is refused, never treated as satisfied",
      abstains(v7.constraint_satisfaction, dict(CSP, constraints=[
          {"constraint_id": "c9", "type": "handwave"}])))


# =================================================================================================
# ORACLES 4 & 5 -- ACTION-BY-SCENARIO MATRIX AND MINIMAX REGRET.
#   Payoffs, maximisation:      S1   S2
#                          A    20   12
#                          B    16   16
#                          C    12   20
# Supplied regrets: A = (0,8) max 8;  B = (4,4) max 4;  C = (8,0) max 8.
# Supplied expectation: minimax-regret alternative = B.
# =================================================================================================

MATRIX = dict(CTX, orientation="benefit", units="score", actions=[
    {"action_id": "A"}, {"action_id": "B"}, {"action_id": "C"},
], scenarios=[
    {"scenario_id": "S1"}, {"scenario_id": "S2"},
], cells={"A": {"S1": 20, "S2": 12}, "B": {"S1": 16, "S2": 16}, "C": {"S1": 12, "S2": 20}})

w = v7.whatif_scenario_matrix(MATRIX)
check("10.4 matrix is 3 actions by 2 scenarios",
      w["actions"] == ["A", "B", "C"] and w["scenarios"] == ["S1", "S2"])
check("10.4 every cell is carried through", w["matrix"] == {
    "A": {"S1": 20.0, "S2": 12.0}, "B": {"S1": 16.0, "S2": 16.0},
    "C": {"S1": 12.0, "S2": 20.0}})
check("10.4 recommends no action", w["recommended_action"] is None)
check("10.4 invents no scenario probabilities and no expected values",
      w["scenario_probabilities"] is None and w["expected_values"] is None)
check("10.4 an incomplete matrix is refused rather than partially compared",
      abstains(v7.whatif_scenario_matrix, dict(MATRIX, cells={
          "A": {"S1": 20, "S2": 12}, "B": {"S1": 16}, "C": {"S1": 12, "S2": 20}})))
check("10.4 an action with no identity is refused",
      abstains(v7.whatif_scenario_matrix, dict(MATRIX, actions=[
          {"action_id": "A"}, {}, {"action_id": "C"}])))
check("10.4 abstains when the cells' orientation is not declared",
      abstains(v7.whatif_scenario_matrix, {k: v for k, v in MATRIX.items()
                                           if k != "orientation"}))

g = v7.minimax_regret(MATRIX)
check("10.7 regret row for A is (0, 8)", g["regret_matrix"]["A"] == {"S1": 0.0, "S2": 8.0})
check("10.7 regret row for B is (4, 4)", g["regret_matrix"]["B"] == {"S1": 4.0, "S2": 4.0})
check("10.7 regret row for C is (8, 0)", g["regret_matrix"]["C"] == {"S1": 8.0, "S2": 0.0})
check("10.7 maximum regrets are A=8 B=4 C=8",
      g["maximum_regret"] == {"A": 8.0, "B": 4.0, "C": 8.0})
check("10.7 minimax-regret alternative is B", g["minimax_regret_alternative"] == "B")
check("10.7 minimax regret value is 4", g["minimax_regret_value"] == 4.0)
check("10.7 no tie is reported for this matrix", g["tied"] is False)

# ORIENTATION SENSITIVITY: the identical numbers read as COSTS must not give the same answer by
# accident. Best-in-scenario becomes the minimum, so the regrets invert.
gc = v7.minimax_regret(dict(MATRIX, orientation="cost"))
check("10.7 the same numbers read as costs give different regrets",
      gc["regret_matrix"]["A"] == {"S1": 8.0, "S2": 0.0})

# TIE POLICY IS AN EXPLICIT REFUSAL: two actions with identical rows tie and neither is chosen.
tie = v7.minimax_regret(dict(MATRIX, actions=[{"action_id": "A"}, {"action_id": "B"},
                                              {"action_id": "B2"}, {"action_id": "C"}],
                             cells={"A": {"S1": 20, "S2": 12}, "B": {"S1": 16, "S2": 16},
                                    "B2": {"S1": 16, "S2": 16}, "C": {"S1": 12, "S2": 20}}))
check("10.7 a tie returns every tied alternative", tie["minimax_regret_alternatives"] == ["B", "B2"])
check("10.7 a tie chooses none of them", tie["minimax_regret_alternative"] is None
      and tie["tied"] is True)


# =================================================================================================
# ORACLE 6 -- DECISION SENSITIVITY.
#   Two alternatives on two criteria, weight w on c1 and (1 - w) on c2.
#   Supplied expectation: w = 4/7 ~ 0.5714285714; at w = 0.5 B outranks A; at w = 0.7 A ranks
#   above B.
#
#   THE FIXTURE IS THE OWNER'S SUPPLIED ONE, unchanged: A = (0.9, 0.4), B = (0.6, 0.8). It is
#   the contract that is the oracle, so the numbers are not re-derived or substituted here. All
#   three supplied facts follow from it in EXACT rational arithmetic:
#
#       score_A(w) = 0.9w + 0.4(1-w) = 0.4 + 0.5w
#       score_B(w) = 0.6w + 0.8(1-w) = 0.8 - 0.2w
#       equal when 0.4 + 0.5w = 0.8 - 0.2w, i.e. 0.7w = 0.4, i.e. w = 4/7
#
#       at w = 1/2:  A = 0.65 < B = 0.70   -> B ranks above A
#       at w = 7/10: A = 0.75 > B = 0.66   -> A ranks above B
#
#   The crossover is asserted as the exact string "4/7" rather than a float, so a method that
#   located it by sampling a grid could not pass.
# =================================================================================================

SENS = dict(CTX, model={"type": "weighted_additive", "swept_criterion": "c1",
                        "complement_criterion": "c2"},
            parameters=[{"parameter_id": "w", "perturbation": "sweep",
                         "base_value": 0.5, "range_low": 0, "range_high": 1}],
            alternatives=[
                {"alternative_id": "A", "values": {"c1": 0.9, "c2": 0.4}},
                {"alternative_id": "B", "values": {"c1": 0.6, "c2": 0.8}},
            ])

s = v7.decision_sensitivity(SENS)
cross = [c for c in s["crossovers"] if sorted(c["between"]) == ["A", "B"]]
check("10.5 a crossover between A and B is found", len(cross) == 1)
check("10.5 the crossover is exactly 4/7", cross and cross[0]["crossover_exact"] == "4/7")
check("10.5 the crossover is not a sampled grid point",
      bool(cross) and abs(cross[0]["crossover_value"] - 0.5714285714) < 1e-9)
check("10.5 a rank reversal is reported", s["rank_reversal"] is True)

below = [t for t in s["perturbation_trace"] if abs(t["parameter_value"] - 0.5) < 1e-12]
check("10.5 at w = 0.5 B ranks above A", bool(below) and below[0]["ranking"] == ["B", "A"])

s7 = v7.decision_sensitivity(dict(SENS, parameters=[
    {"parameter_id": "w", "perturbation": "sweep", "base_value": 0.7,
     "range_low": 0.7, "range_high": 1}]))
at7 = [t for t in s7["perturbation_trace"] if abs(t["parameter_value"] - 0.7) < 1e-12]
check("10.5 at w = 0.7 A ranks above B", bool(at7) and at7[0]["ranking"] == ["A", "B"])

check("10.5 abstains when no perturbation range is declared",
      abstains(v7.decision_sensitivity, dict(SENS, parameters=[
          {"parameter_id": "w", "perturbation": "sweep", "base_value": 0.5}])))
check("10.5 abstains when nothing is declared as swept",
      abstains(v7.decision_sensitivity, dict(SENS, parameters=[
          {"parameter_id": "w", "base_value": 0.5, "range_low": 0, "range_high": 1}])))
check("10.5 abstains when no decision model is declared",
      abstains(v7.decision_sensitivity, {k: v for k, v in SENS.items() if k != "model"}))


# =================================================================================================
# AUTHORITY -- section 8. No Category-10 result may exercise human approval authority, and the
# ledger must be able to tell an ANALYTICAL_RESULT from a HUMAN_DECISION.
# =================================================================================================

ALL_RESULTS = [
    ("B4.1", r), ("B4.2", lp), ("B4.3", c), ("B4.4", w),
    ("B4.5", s), ("B4.6", p), ("B4.7", g),
]
check("every Category-10 result is stamped ANALYTICAL_RESULT",
      all(x["result_class"] == v7.ANALYTICAL_RESULT for _m, x in ALL_RESULTS))
check("no Category-10 result is ever stamped HUMAN_DECISION",
      all(x["result_class"] != v7.HUMAN_DECISION for _m, x in ALL_RESULTS))
check("every Category-10 result requires human authorization",
      all(x["human_authorization_required"] is True for _m, x in ALL_RESULTS))
check("no Category-10 result creates project evidence",
      all(x["creates_project_evidence"] is False for _m, x in ALL_RESULTS))
check("every Category-10 result is marked calibration-pending",
      all(x["calibration_pending"] is True for _m, x in ALL_RESULTS))
check("no Category-10 result carries a status colour into fusion",
      all("status_color" not in x for _m, x in ALL_RESULTS))
check("every Category-10 result carries its decision context",
      all(x["decision_context"]["context_id"] == "RUN32-ORACLE" for _m, x in ALL_RESULTS))

# ABSTENTION IS UNIVERSAL: with no governed structure at all, every one of the seven refuses.
EMPTY = {}
FNS = [v7.multi_objective, v7.linear_program, v7.constraint_satisfaction,
       v7.whatif_scenario_matrix, v7.decision_sensitivity, v7.pareto_frontier,
       v7.minimax_regret]
check("all seven methods abstain on an empty structure",
      all(abstains(fn, EMPTY) for fn in FNS))
check("all seven methods abstain when the structure cannot be attributed",
      all(abstains(fn, {"criteria": [], "alternatives": []}) for fn in FNS))

# The structure-key map must name a key for exactly the seven Category-10 modules.
check("the v7 structure map covers exactly B4.1 through B4.7",
      sorted(v7.V7_STRUCTURE_KEYS) == ["B4.1", "B4.2", "B4.3", "B4.4", "B4.5", "B4.6", "B4.7"])
check("10.1 and 10.6 read the same shared decision structure",
      v7.V7_STRUCTURE_KEYS["B4.1"] == v7.V7_STRUCTURE_KEYS["B4.6"] == "decisionAlternatives")
check("10.4 and 10.7 read the same action-by-scenario matrix",
      v7.V7_STRUCTURE_KEYS["B4.4"] == v7.V7_STRUCTURE_KEYS["B4.7"] == "actionScenarioMatrix")

# THE SUPPLY PATH. A DECISION STRUCTURE THAT EXISTS ONLY IN TEST FIXTURES IS NOT SUPPLIED.
#
# This check was MISSING and the Run-32 fault campaign is what found it. Fault 32 removes the v7
# keys from `project_data.governed_structure_keys()` -- which is exactly what "the structure lives
# only in fixtures" looks like in this tree -- and no guard anywhere went red. Run 29 and Run 31
# both carry the equivalent check for their own canonical layers (`test_run29_supply_path_guard`
# for v3/v4 and `test_run31_canonical_oracles` for v6); v7 had none, so a Category-10 structure
# could have been readable by the canonical method and unwritable through the real production
# intake, with every oracle still green.
from app.project_data import governed_structure_keys as _gsk               # noqa: E402

check("every governed Category-10 decision structure is admitted by the production intake",
      not sorted(set(v7.V7_STRUCTURE_KEYS.values()) - _gsk()))

# B2.19 CRITIC-TOPSIS'S OWN MINIMUM, WHICH HAD NO INDEPENDENT GUARD UNTIL THE FAULT CAMPAIGN
# LOOKED FOR ONE.
#
# B2.19 is exposed operationally through the Category-10 decision service over the SAME
# `decisionAlternatives` structure B4.1 and B4.6 read, so its refusals are a Category-10 concern
# too. CRITIC derives its weights from the DISPERSION of each criterion across the alternative
# set and from the correlations between criteria, and neither means anything below three rows --
# the sample standard deviation divides by m - 1, so two rows give a degenerate spread and one
# gives none at all. `critic_topsis` therefore refuses fewer than three.
#
# THAT LINE WAS UNTESTED. The only existing check feeds it a SINGLE row, and a single row is
# already refused further upstream by the shared `decision_problem`, which requires at least two
# alternatives before CRITIC is ever reached. So the check passed whether or not the minimum-three
# rule existed, and lowering the threshold from three to two broke nothing anywhere in the tree.
# Two rows is the case that distinguishes the two layers, and this is the check that asks for it.
from app.simulation import canonical_v5 as v5                              # noqa: E402

check("CRITIC-TOPSIS refuses two project rows, because the spread it weights by needs at least "
      "three and two rows are already past the shared decision structure's own minimum",
      abstains(v5.critic_topsis, dict(MOO, alternatives=MOO["alternatives"][:2])))


passed = sum(1 for _n, ok in CHECKS if ok)
for name, ok in CHECKS:
    if not ok:
        print(f"FAIL: {name}")
print(f"RESULT: {passed}/{len(CHECKS)} checks passed")
sys.exit(0 if passed == len(CHECKS) else 1)
