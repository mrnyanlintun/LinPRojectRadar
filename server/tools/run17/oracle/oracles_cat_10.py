"""
Run 19 independent oracles for Category 10, decision optimisation.

Written from supervisory specification section 19 and from nothing else. The specification names
the preferred oracle for each of these explicitly in section 24: vertex enumeration for the
linear programme, a hand nondominated set for Pareto, and a hand regret matrix for minimax
regret. That is what is implemented here. Nothing is imported from server/app and no solver
library is used, so the linear programme is solved by enumerating the vertices of the feasible
polytope and checking each for feasibility, which is independent of any simplex implementation.
"""

from __future__ import annotations

import itertools


# ------------------------------------------------------------------ 10.1 / 10.6 Pareto

def dominates(a: tuple[float, ...], b: tuple[float, ...]) -> bool:
    """
    Specification 10.6, for minimisation: a dominates b if a is no worse in every objective and
    strictly better in at least one.
    """
    return all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b))


def nondominated(points: dict[str, tuple[float, ...]]) -> set[str]:
    """The nondominated frontier, by exhaustive pairwise comparison."""
    return {name for name, p in points.items()
            if not any(dominates(q, p) for other, q in points.items() if other != name)}


# ------------------------------------------------------------------ 10.2 Linear programming

def solve_lp_by_vertex_enumeration(objective: tuple[float, ...],
                                   constraints: list[tuple[tuple[float, ...], float]],
                                   maximise: bool = True) -> dict:
    """
    Solve a two-variable linear programme by enumerating basic solutions.

    Every candidate optimum of a linear programme lies at a vertex of the feasible region, and a
    vertex is the intersection of two active constraints. So: form every pair of constraints
    including the nonnegativity constraints, solve the two-by-two system, discard any point that
    violates any constraint, and take the best feasible vertex. This is deliberately NOT a
    simplex implementation, so it is independent of any solver.

    `constraints` are (coefficients, right-hand side) meaning coefficients . x <= rhs.
    Nonnegativity is added here rather than passed in.
    """
    rows = list(constraints) + [((-1.0, 0.0), 0.0), ((0.0, -1.0), 0.0)]

    def feasible(pt) -> bool:
        return all(sum(c * v for c, v in zip(coef, pt)) <= rhs + 1e-9 for coef, rhs in rows)

    best, best_val = None, None
    for (c1, r1), (c2, r2) in itertools.combinations(rows, 2):
        det = c1[0] * c2[1] - c1[1] * c2[0]
        if abs(det) < 1e-12:
            continue
        x = (r1 * c2[1] - c1[1] * r2) / det
        y = (c1[0] * r2 - r1 * c2[0]) / det
        if not feasible((x, y)):
            continue
        val = objective[0] * x + objective[1] * y
        if best_val is None or (val > best_val if maximise else val < best_val):
            best, best_val = (x, y), val
    if best is None:
        return {"feasible": False, "solution": None, "objective": None, "binding": []}
    binding = [i for i, (coef, rhs) in enumerate(constraints)
               if abs(sum(c * v for c, v in zip(coef, best)) - rhs) < 1e-9]
    return {"feasible": True, "solution": best, "objective": best_val, "binding": binding}


WYNDOR = {
    "objective": (3.0, 5.0),
    "constraints": [((1.0, 0.0), 4.0), ((0.0, 2.0), 12.0), ((3.0, 2.0), 18.0)],
}


# ------------------------------------------------------------------ 10.3 Constraint satisfaction

def csp_solutions(domains: dict[str, list], constraints: list) -> list[dict]:
    """
    Specification 10.3. A general constraint satisfaction problem: variables, domains and
    constraints, with a solution being a total assignment satisfying every constraint.

    Solved by exhaustive enumeration over the product of the domains, which is an independent
    reference for the tiny problems the specification uses.
    """
    names = list(domains)
    out = []
    for combo in itertools.product(*(domains[n] for n in names)):
        assignment = dict(zip(names, combo))
        if all(c(assignment) for c in constraints):
            out.append(assignment)
    return out


# ------------------------------------------------------------------ 10.4 / 10.7 Decision matrix

def regret_matrix(payoffs: dict[str, dict[str, float]]) -> dict:
    """
    Specification 10.7, for payoff maximisation.

    M_s = max_a P_as; R_as = M_s - P_as; R_a = max_s R_as; choose the action minimising R_a.

    The specification's matrix, A/B/C against S1/S2, has scenario maxima of 10 and 10, action
    maximum regrets of 8, 4 and 8, and a minimax-regret choice of B.
    """
    actions = list(payoffs)
    scenarios = list(next(iter(payoffs.values())))
    maxima = {s: max(payoffs[a][s] for a in actions) for s in scenarios}
    regrets = {a: {s: maxima[s] - payoffs[a][s] for s in scenarios} for a in actions}
    max_regret = {a: max(regrets[a].values()) for a in actions}
    best = min(max_regret, key=lambda a: (max_regret[a], a))
    return {"scenario_maxima": maxima, "regrets": regrets, "max_regret": max_regret,
            "choice": best}


SPEC_PAYOFFS = {"A": {"S1": 10.0, "S2": 2.0},
                "B": {"S1": 6.0, "S2": 6.0},
                "C": {"S1": 2.0, "S2": 10.0}}


# ------------------------------------------------------------------ 10.5 Decision sensitivity

def ranking_crossover(score_a, score_b, lo: float = 0.0, hi: float = 1.0,
                      steps: int = 100001) -> float | None:
    """
    Specification 10.5. Find the weight at which the ranking of two alternatives flips.

    Decision sensitivity is about whether the DECISION changes when a parameter is perturbed, so
    the object located here is the crossover weight itself, not a ranking of current deviations.
    """
    prev = None
    for i in range(steps):
        w = lo + (hi - lo) * i / (steps - 1)
        order = score_a(w) > score_b(w)
        if prev is not None and order != prev:
            return w
        prev = order
    return None


# ------------------------------------------------------------------ self proof

def self_test() -> list[str]:
    fails: list[str] = []

    # 10.6 / 10.1 -- the specification's four-point discrete feasible set.
    pts = {"A": (10.0, 5.0), "B": (8.0, 8.0), "C": (12.0, 4.0), "D": (13.0, 9.0)}
    front = nondominated(pts)
    if front != {"A", "B", "C"}:
        fails.append(f"10.6 nondominated set: got {sorted(front)}, specification says A, B and C")
    if not dominates(pts["A"], pts["D"]):
        fails.append("10.6 A dominates D in the specification's set")
    if dominates(pts["A"], pts["B"]) or dominates(pts["B"], pts["A"]):
        fails.append("10.6 A and B are mutually nondominated")
    # Permutation invariance and duplicate points, which the specification requires be tested.
    if nondominated({k: pts[k] for k in ("D", "C", "B", "A")}) != front:
        fails.append("10.6 the frontier must not depend on the order the points are given in")
    dup = dict(pts)
    dup["A2"] = pts["A"]
    if not {"A", "A2"} <= nondominated(dup):
        fails.append("10.6 duplicate points do not dominate each other and both stay on the "
                     "frontier")

    # 10.2 -- the Wyndor Glass problem: x1=2, x2=6, objective 36.
    lp = solve_lp_by_vertex_enumeration(WYNDOR["objective"], WYNDOR["constraints"])
    if not lp["feasible"]:
        fails.append("10.2 the Wyndor problem is feasible")
    else:
        x1, x2 = lp["solution"]
        if abs(x1 - 2) > 1e-6 or abs(x2 - 6) > 1e-6:
            fails.append(f"10.2 optimum: got {lp['solution']}, specification says (2, 6)")
        if abs(lp["objective"] - 36) > 1e-6:
            fails.append(f"10.2 optimal value: got {lp['objective']}, specification says 36")
        if set(lp["binding"]) != {1, 2}:
            fails.append(f"10.2 binding constraints: got {lp['binding']}, the second and third "
                         f"constraints are binding at (2, 6)")
    infeasible = solve_lp_by_vertex_enumeration(
        (1.0, 1.0), [((1.0, 0.0), -5.0)], maximise=True)
    if infeasible["feasible"]:
        fails.append("10.2 a constraint requiring a negative value of a nonnegative variable is "
                     "infeasible and must be rejected")

    # 10.3 -- X in {A,B}, Y in {1,2}, constraint: if X=A then Y=2.
    sols = csp_solutions({"X": ["A", "B"], "Y": [1, 2]},
                         [lambda a: not (a["X"] == "A" and a["Y"] == 1)])
    got = {(s["X"], s["Y"]) for s in sols}
    if got != {("A", 2), ("B", 1), ("B", 2)}:
        fails.append(f"10.3 feasible assignments: got {sorted(got)}, specification says "
                     f"(A,2), (B,1) and (B,2)")
    if ("A", 1) in got:
        fails.append("10.3 (A,1) is infeasible under the specification's constraint")

    # 10.7 -- the specification's payoff matrix chooses B.
    r = regret_matrix(SPEC_PAYOFFS)
    if r["scenario_maxima"] != {"S1": 10.0, "S2": 10.0}:
        fails.append(f"10.7 scenario maxima: got {r['scenario_maxima']}, specification says 10 "
                     f"and 10")
    if r["max_regret"] != {"A": 8.0, "B": 4.0, "C": 8.0}:
        fails.append(f"10.7 maximum regrets: got {r['max_regret']}, specification says 8, 4, 8")
    if r["choice"] != "B":
        fails.append(f"10.7 minimax regret choice: got {r['choice']}, specification says B")

    # 10.5 -- two alternatives whose ranking flips at a known weight. With
    # a(w) = w and b(w) = 1 - w the crossover is exactly one half.
    x = ranking_crossover(lambda w: w, lambda w: 1 - w)
    if x is None or abs(x - 0.5) > 1e-4:
        fails.append(f"10.5 ranking crossover: got {x!r}, the analytic answer is one half")

    return fails


_FAILS = self_test()
assert not _FAILS, "Category 10 oracle does not reproduce the specification: " + "; ".join(_FAILS)
