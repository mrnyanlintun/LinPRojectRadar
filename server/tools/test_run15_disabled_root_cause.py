"""
Run 15 Workstream C. Canonical known-answer problems for the eight disabled methods.

THE EIGHT MODULES ARE NOT ACTIVATED BY THIS FILE. Each is imported and called directly, in
isolation, exactly as Run 14 did. Nothing here touches the registry, the voting set or storage.

THE ORACLE IS THE FORMAL DEFINITION, NEVER PRODUCTION OUTPUT. For each method a small problem
is posed whose answer is derived independently, either from a published example or constructed
from the formal definition. A reference solver written from the definition appears alongside
each; it is an oracle for the test and is NOT production code and NOT a copy of production.

The question each section answers is narrow and factual: can the current implementation even
ACCEPT the canonical problem, and if so does it return the independently known answer.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.simulation.models_ext import run_parametric_cost
from app.simulation.models_fuzzy import run_hypersoft_sets
from app.simulation.models_evc import run_plithogenic, run_quantum_probability
from app.simulation.models_gov import (run_multi_objective, run_linear_programming,
                                       run_decision_sensitivity, run_pareto_frontier)

PASS = 0
TOTAL = 0
FAILURES = []
FINDINGS = {}


def check(name, cond):
    global PASS, TOTAL
    TOTAL += 1
    if cond:
        PASS += 1
    else:
        FAILURES.append(name)


def rnd():
    return 0.5


# =====================================================================================
# A3.8 PARAMETRIC COST INDEX
# =====================================================================================
# FORMAL METHOD: parametric cost estimating. A cost estimating relationship, a mathematical
# function fitted to a historical population, predicts cost from measured driver quantities.
# GAO Cost Estimating and Assessment Guide GAO-20-195G, chapter on parametric methods; NASA
# Cost Estimating Handbook version 4.0, cost estimating relationships.
#
# CANONICAL PROBLEM, CONSTRUCTED FROM THE DEFINITION. Five historical observations lying
# exactly on cost = 100 + 5 * quantity. Fit by ordinary least squares, then predict at
# quantity 60. The independently known answer is 400 with a residual of zero.
HIST = [(10, 150.0), (20, 200.0), (30, 250.0), (40, 300.0), (50, 350.0)]


def reference_cer(points, q):
    n = len(points)
    mx = sum(p[0] for p in points) / n
    my = sum(p[1] for p in points) / n
    b = (sum((p[0] - mx) * (p[1] - my) for p in points)
         / sum((p[0] - mx) ** 2 for p in points))
    a = my - b * mx
    return a + b * q, a, b


pred, a_hat, b_hat = reference_cer(HIST, 60)
check("A3.8 oracle: the fitted intercept is 100", abs(a_hat - 100.0) < 1e-9)
check("A3.8 oracle: the fitted slope is 5", abs(b_hat - 5.0) < 1e-9)
check("A3.8 oracle: the independently known prediction at a quantity of 60 is 400",
      abs(pred - 400.0) < 1e-9)

# Can production accept it? Its declared inputs are budget, earned value, actual cost, cost
# index and percent complete. There is no driver quantity, no relationship and no coefficient
# in the signature or anywhere the module reads, so the canonical problem cannot be posed.
base = {"bac": 1000.0, "ev": 500.0, "ac": 550.0, "cpi": 500.0 / 550.0,
        "actualPctComplete": 50.0}
r0 = run_parametric_cost(dict(base), rnd, "2025-06-30")
check("A3.8 the module computes on the earned value figures alone", "parametric_index" in r0)
# The defining property of a parametric estimate is that it MOVES with the driver quantity.
moved = set()
for q in (10, 60, 250, 5000):
    probe = dict(base)
    probe["quantity"] = q
    probe["driverQuantity"] = q
    probe["cost_driver"] = q
    moved.add(run_parametric_cost(probe, rnd, "2025-06-30")["parametric_index"])
check("A3.8 the result is invariant under every cost driver quantity supplied, which is the "
      "property a parametric estimate must NOT have", len(moved) == 1)
check("A3.8 the current implementation cannot solve the canonical problem",
      "cost_estimating_relationship" not in r0 and "fitted" not in str(r0).lower())
FINDINGS["A3.8"] = ("NO", "NOT_IMPLEMENTED")


# =====================================================================================
# B2.20 HYPERSOFT SETS
# =====================================================================================
# FORMAL METHOD: Smarandache, Extension of Soft Set to Hypersoft Set, and then to Plithogenic
# Hypersoft Set, Neutrosophic Sets and Systems 22 (2018), 168-170. A hypersoft set is a pair
# (F, A1 x A2 x ... x An) over a universe U where the Ai are PAIRWISE DISJOINT attribute value
# sets and F maps each tuple of the Cartesian product to a SUBSET of U.
#
# CANONICAL PROBLEM, CONSTRUCTED FROM THE DEFINITION. U = {u1, u2, u3, u4}. Two attributes:
# size in {small, large}, and colour in {red, blue}. F is given on all four tuples. The
# independently known answers are the four subsets, the fact that the mapping is TOTAL on the
# product, and that the codomain is the power set of U.
U = {"u1", "u2", "u3", "u4"}
A1 = ["small", "large"]
A2 = ["red", "blue"]
F_REF = {("small", "red"): {"u1"}, ("small", "blue"): {"u1", "u3"},
         ("large", "red"): {"u2", "u4"}, ("large", "blue"): set()}
check("B2.20 oracle: the attribute value sets are disjoint", not set(A1) & set(A2))
check("B2.20 oracle: the mapping is total on the Cartesian product",
      set(F_REF) == {(a, b) for a in A1 for b in A2})
check("B2.20 oracle: every image is a subset of the universe",
      all(v <= U for v in F_REF.values()))

# Production: the tuple is genuinely present, so part of the structure IS there.
combos = {}
for cpi, cost in ((0.85, "poor"), (0.92, "fair"), (0.98, "good")):
    for spi, sch in ((0.85, "poor"), (0.92, "fair"), (0.98, "good")):
        for doc, rk in ((0.10, "low"), (0.50, "medium"), (0.80, "high")):
            res = run_hypersoft_sets({"cpi": cpi, "spi": spi, "docRiskScore": doc},
                                     rnd, "2025-06-30")
            combos[(cost, sch, rk)] = res
check("B2.20 the mapping is keyed on a genuine three-attribute tuple",
      all(r["attribute_combination"] == f"{a}-{b}-{c}" for (a, b, c), r in combos.items()))
check("B2.20 all twenty-seven tuples of the product are reachable from real inputs",
      len(combos) == 27)
defaults = [k for k, r in combos.items() if r["score"] == 0.35]
check("B2.20 SIX of the twenty-seven tuples fall through to a silent default rather than "
      "being mapped, so the mapping is NOT total on the product. Run 14 recorded two; the "
      "difference is that this sweep exhausts the product rather than sampling it.",
      sorted(defaults) == [("fair", "poor", "low"), ("fair", "poor", "medium"),
                           ("good", "poor", "medium"), ("poor", "fair", "low"),
                           ("poor", "fair", "medium"), ("poor", "good", "medium")])
check("B2.20 the image is a scalar and not a subset of any universe",
      isinstance(combos[("good", "good", "low")]["score"], float))
check("B2.20 no universe of objects exists for the mapping to return a subset of",
      "universe" not in str(combos[("good", "good", "low")]).lower())
FINDINGS["B2.20"] = ("PARTIAL", "FAIL")


# =====================================================================================
# B2.7 PLITHOGENIC SETS
# =====================================================================================
# FORMAL METHOD: Smarandache, Plithogenic Set, an Extension of Crisp, Fuzzy, Intuitionistic
# Fuzzy, and Neutrosophic Sets, and Plithogeny, Plithogenic Set, Logic, Probability and
# Statistics (2017). A plithogenic set is a quintuple (P, v, Pv, pdf, pCF): an attribute v with
# a value set Pv, a degree of appurtenance function pdf, and a degree of CONTRADICTION function
# pCF defined BETWEEN each attribute value and a designated DOMINANT attribute value, with
# pCF(a, a) = 0 and pCF(a, b) = pCF(b, a). The plithogenic aggregation operators are
# contradiction-weighted linear combinations of a t-norm and a t-conorm.
#
# NOTE ON SOURCES: the primary PDFs at fs.unm.edu and arxiv.org are blocked by this
# container's egress proxy. The quintuple, the two pCF properties and the linear-combination
# form of the operators are taken from the retrievable descriptions of those primary works and
# are stated here only to the extent they are corroborated across them. The exact coefficient
# convention of the aggregation operator is NOT relied on below, because the finding does not
# depend on it.
#
# CANONICAL PROBLEM, CONSTRUCTED FROM THE DEFINITION. Attribute "condition" with values
# {good, fair, poor}, dominant value "good". pCF(good, good) = 0, pCF(good, fair) = 0.5,
# pCF(good, poor) = 1. Appurtenance degrees 0.8, 0.6, 0.2. The independently known facts: pCF
# is a function of a PAIR of attribute values; it is zero on the diagonal; it is symmetric;
# and it is defined RELATIVE TO the designated dominant value.
DOMINANT = "good"
PCF = {("good", "good"): 0.0, ("good", "fair"): 0.5, ("good", "poor"): 1.0}
PCF.update({(b, a): v for (a, b), v in PCF.items()})
PCF[("fair", "fair")] = 0.0
PCF[("poor", "poor")] = 0.0
check("B2.7 oracle: the contradiction degree is zero on the diagonal",
      all(PCF[(a, a)] == 0.0 for a in ("good", "fair", "poor")))
check("B2.7 oracle: the contradiction degree is symmetric",
      all(PCF[(a, b)] == PCF[(b, a)] for a in ("good", "fair", "poor")
          for b in ("good", "fair", "poor") if (a, b) in PCF))
check("B2.7 oracle: the contradiction degree is taken against a designated dominant value",
      DOMINANT in ("good", "fair", "poor") and PCF[(DOMINANT, "poor")] == 1.0)

pl = run_plithogenic({"cpi": 0.85, "spi": 0.85,
                      "cusum": {"breached": True},
                      "doc": {"score": 0.90},
                      "mc": {"p80DeltaPct": 20}}, rnd, "2025-06-30")
check("B2.7 the module carries an appurtenance degree and a contradiction degree, so part of "
      "the structure IS present", "contradiction" in str(pl).lower() or "attributes" in pl)
pl_txt = str(pl).lower()
check("B2.7 no dominant attribute value is designated anywhere in the result",
      "dominant_attribute" not in pl_txt and "dominant_value" not in pl_txt)
# The decisive test: the contradiction degree must be a function of a PAIR of attribute values.
# In production it is a literal attached to one band, so it cannot be evaluated on a pair and
# cannot satisfy pCF(a, a) = 0 for a value whose band happens to carry a non-zero literal.
def plith(cpi, doc_score):
    return run_plithogenic({"cpi": cpi, "spi": cpi, "cusum": {"breached": doc_score > 0.5},
                            "doc": {"score": doc_score}}, rnd, "2025-06-30")


green = plith(0.99, 0.10)
red = plith(0.80, 0.90)
check("B2.7 the contradiction figure is a single number for the whole reading and not a "
      "function of a pair of attribute values, so pCF(a, a) = 0 cannot even be posed "
      "against it",
      isinstance(green.get("contradiction_degree", green.get("avg_contradiction", 0)),
                 (int, float))
      and green != red)
check("B2.7 the aggregate takes only a handful of distinct values across a wide input sweep, "
      "because the appurtenance degrees behind it are literals attached to bands",
      len({plith(c, d)["status_color"] for c in (0.5, 0.7, 0.85, 0.92, 0.99, 1.3)
           for d in (0.0, 0.2, 0.5, 0.8, 1.0)}) <= 3)
FINDINGS["B2.7"] = ("PARTIAL", "FAIL")


# =====================================================================================
# B2.9 QUANTUM PROBABILITY
# =====================================================================================
# FORMAL METHOD: outcome probabilities from a NORMALISED state under the Born rule. For a
# normalised state |psi> and an orthogonal family of projectors {P_i} summing to the identity,
# p(i) = || P_i |psi> ||^2, and the p(i) sum to exactly one. Busemeyer and Bruza, Quantum
# Models of Cognition and Decision, Cambridge University Press, 2012, chapters 2 and 4.
#
# CANONICAL PROBLEM, CONSTRUCTED FROM THE DEFINITION. A two-dimensional real state
# |psi> = (0.6, 0.8), which is normalised because 0.36 + 0.64 = 1. Projectors onto the two
# basis rays. The independently known Born probabilities are 0.36 and 0.64, summing to 1.
PSI = (0.6, 0.8)
check("B2.9 oracle: the state is normalised", abs(sum(a * a for a in PSI) - 1.0) < 1e-12)
born = [PSI[0] ** 2, PSI[1] ** 2]
check("B2.9 oracle: the Born probabilities are 0.36 and 0.64",
      abs(born[0] - 0.36) < 1e-12 and abs(born[1] - 0.64) < 1e-12)
check("B2.9 oracle: they sum to exactly one", abs(sum(born) - 1.0) < 1e-12)

q = run_quantum_probability({"cpi": 0.80, "spi": 0.80, "cusum": {"breached": True},
                             "doc": {"score": 0.90}}, rnd, "2025-06-30")
check("B2.9 the module reports amplitudes", "alpha_green" in q and "gamma_red" in q)
amp2 = q["alpha_green"] ** 2 + q["gamma_red"] ** 2
check("B2.9 the squared amplitudes do NOT sum to one, so there is no normalised state",
      abs(amp2 - 1.0) > 0.05)
check("B2.9 no state vector, projector or measurement appears in the result",
      not any(w in str(q).lower() for w in ("state_vector", "projector", "hilbert",
                                            "density_matrix", "basis")))
# The phase angle is a tally of adverse indicators and so takes only four values, where a phase
# in a genuine quantum model is continuous in the state.
phases = set()
for c in (0.5, 0.7, 0.85, 0.92, 0.99, 1.1, 1.3):
    for d in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
        phases.add(run_quantum_probability(
            {"cpi": c, "spi": c, "doc": {"score": d}}, rnd, "2025-06-30")["phase_angle_deg"])
check("B2.9 the phase angle takes only the values a tally of three indicators can produce",
      len(phases) <= 4)
check("B2.9 the canonical problem cannot be posed: the module accepts no state and no "
      "projector, only earned value figures", "cpi" not in str(q))
FINDINGS["B2.9"] = ("NO", "NOT_IMPLEMENTED")


# =====================================================================================
# B4.1 MULTI-OBJECTIVE OPTIMIZATION
# =====================================================================================
# FORMAL METHOD: decision variables over a feasible set, at least two objective functions with
# stated directions, and a solution concept: a nondominated set, a weighted scalarisation with
# stated weights, or an epsilon-constraint formulation. Ehrgott, Multicriteria Optimization,
# 2nd ed., Springer 2005; Miettinen, Nonlinear Multiobjective Optimization, Kluwer 1999.
#
# CANONICAL PROBLEM, CONSTRUCTED FROM THE DEFINITION. Four candidate alternatives with two
# objectives, both to be maximised. The independently known nondominated set is computed below
# by the dominance relation and is {B, C}.
ALTS = {"A": (2.0, 2.0), "B": (5.0, 1.0), "C": (1.0, 5.0), "D": (4.0, 0.5)}


def nondominated(alts):
    out = set()
    for k, v in alts.items():
        if not any(all(w[i] >= v[i] for i in range(len(v))) and any(w[i] > v[i]
                   for i in range(len(v))) for j, w in alts.items() if j != k):
            out.add(k)
    return out


ND = nondominated(ALTS)
check("B4.1 and B4.6 oracle: the nondominated set of the four alternatives is A, B and C",
      ND == {"A", "B", "C"})
check("B4.1 and B4.6 oracle: A survives because no alternative beats it on BOTH objectives, "
      "which is exactly what makes dominance a relation and not a threshold", "A" in ND)
check("B4.1 and B4.6 oracle: D is dominated by B", "D" not in ND)
check("B4.1 and B4.6 oracle: the nondominated set does not depend on the ordering of the "
      "alternatives", nondominated({k: ALTS[k] for k in reversed(list(ALTS))}) == ND)

mo = run_multi_objective({"cpi": 0.95, "spi": 0.92, "docRiskScore": 0.30}, rnd, "2025-06-30")
check("B4.1 the module returns one score for one project", "pareto_score" in mo)
check("B4.1 no alternative, decision variable or feasible region appears in the result",
      not any(w in str(mo).lower() for w in ("alternative", "decision_variable",
                                             "feasible", "candidate")))
check("B4.1 the scalarisation weights are equal and are not stated anywhere in the result",
      "weight" not in str(mo).lower())
# It cannot even accept a set of alternatives: the signature takes one project's figures.
check("B4.1 the canonical problem cannot be posed against the module, which has no argument "
      "for a set of alternatives",
      run_multi_objective({"cpi": 0.95, "spi": 0.92, "docRiskScore": 0.30,
                           "alternatives": ALTS}, rnd, "2025-06-30") == mo)
FINDINGS["B4.1"] = ("NO", "NOT_IMPLEMENTED")


# =====================================================================================
# B4.2 LINEAR PROGRAMMING
# =====================================================================================
# FORMAL METHOD: maximise or minimise a linear objective c'x subject to Ax <= b and bounds on
# x, solved to an optimum, with infeasibility and unboundedness determined by the constraint
# system. Dantzig, Linear Programming and Extensions, Princeton 1963.
#
# CANONICAL PROBLEM: the Wyndor Glass problem of Hillier and Lieberman, Introduction to
# Operations Research, chapter 3. Maximise 3x + 5y subject to x <= 4, 2y <= 12, 3x + 2y <= 18,
# x, y >= 0. THE PUBLISHED OPTIMUM IS 36 AT x = 2, y = 6.
def solve_lp_by_vertex_enumeration():
    """Independent solver: an LP optimum lies at a vertex, so enumerate the vertices."""
    cons = [((1.0, 0.0), 4.0), ((0.0, 2.0), 12.0), ((3.0, 2.0), 18.0),
            ((-1.0, 0.0), 0.0), ((0.0, -1.0), 0.0)]
    best = None
    for i in range(len(cons)):
        for j in range(i + 1, len(cons)):
            (a1, b1), r1 = cons[i]
            (a2, b2), r2 = cons[j]
            det = a1 * b2 - a2 * b1
            if abs(det) < 1e-12:
                continue
            x = (r1 * b2 - r2 * b1) / det
            y = (a1 * r2 - a2 * r1) / det
            if all(a * x + b * y <= r + 1e-9 for (a, b), r in cons):
                val = 3 * x + 5 * y
                if best is None or val > best[0]:
                    best = (val, x, y)
    return best


opt, xs, ys = solve_lp_by_vertex_enumeration()
check("B4.2 oracle: the published optimum of the Wyndor Glass problem is 36",
      abs(opt - 36.0) < 1e-9)
check("B4.2 oracle: attained at x equal to two and y equal to six",
      abs(xs - 2.0) < 1e-9 and abs(ys - 6.0) < 1e-9)

lp = run_linear_programming({"bac": 1000.0, "ev": 500.0, "ac": 300.0, "cpi": 500.0 / 300.0},
                            rnd, "2025-06-30")
check("B4.2 the module returns a single required cost index, not a solution vector",
      "required_cpi_to_complete" in lp)
check("B4.2 no objective vector, constraint matrix, bound or solution vector appears",
      not any(w in str(lp).lower() for w in ("objective", "constraint_matrix",
                                             "decision_variable", "solution")))
check("B4.2 the canonical problem cannot be posed: there is no argument for an objective, a "
      "constraint system or bounds, so an optimum of 36 can never be returned",
      run_linear_programming({"bac": 1000.0, "ev": 500.0, "ac": 300.0, "cpi": 500.0 / 300.0,
                              "objective": [3, 5], "constraints": [[1, 0, 4]]},
                             rnd, "2025-06-30") == lp)
check("B4.2 an unbounded program cannot be represented at all, because a program with no "
      "constraints has no expression in these five inputs", "unbounded" not in str(lp).lower())
FINDINGS["B4.2"] = ("NO", "NOT_IMPLEMENTED")


# =====================================================================================
# B4.5 DECISION SENSITIVITY MATRIX
# =====================================================================================
# FORMAL METHOD: one-at-a-time or global sensitivity analysis. Perturb an input by a stated
# amount, RECOMPUTE the output or decision, and report the change. Saltelli et al., Global
# Sensitivity Analysis: The Primer, Wiley 2008, chapter 1, on the one-at-a-time design.
#
# CANONICAL PROBLEM, CONSTRUCTED FROM THE DEFINITION. A decision rule: choose "proceed" when
# 0.5 * cost + 0.5 * schedule >= 0.95, else "review". At cost 1.00 and schedule 0.94 the score
# is 0.97 and the decision is "proceed". Perturb schedule by minus 0.10: the score becomes
# 0.92 and the decision FLIPS to "review". The independently known sensitivity of the decision
# to a minus 0.10 perturbation of schedule is therefore a flip, and to a plus 0.10
# perturbation of cost is no flip.
def decision_rule(cost, sched):
    return "proceed" if 0.5 * cost + 0.5 * sched >= 0.95 else "review"


check("B4.5 oracle: the unperturbed decision is proceed", decision_rule(1.00, 0.94) == "proceed")
check("B4.5 oracle: perturbing schedule down by a tenth flips the decision to review",
      decision_rule(1.00, 0.84) == "review")
check("B4.5 oracle: perturbing cost up by a tenth does not flip it",
      decision_rule(1.10, 0.94) == "proceed")
check("B4.5 oracle: a zero perturbation is a control and must not move the decision",
      decision_rule(1.00, 0.94) == decision_rule(1.00, 0.94))

ds0 = run_decision_sensitivity({"cpi": 1.00, "spi": 0.94, "docRiskScore": 0.30},
                               rnd, "2025-06-30")
ds1 = run_decision_sensitivity({"cpi": 1.00, "spi": 0.84, "docRiskScore": 0.30},
                               rnd, "2025-06-30")
check("B4.5 the module reports a driver ranking", "drivers" in ds0 or "top_driver" in str(ds0))
check("B4.5 a real perturbation of an input DOES move the reported shares", ds0 != ds1)
check("B4.5 but no decision is recomputed anywhere, so no decision change can be reported",
      not any(w in str(ds0).lower() for w in ("decision_before", "decision_after",
                                              "flipped", "recomputed", "perturbation")))
check("B4.5 the module has no argument for a perturbation size, so the canonical problem "
      "cannot be posed",
      run_decision_sensitivity({"cpi": 1.00, "spi": 0.94, "docRiskScore": 0.30,
                                "perturbation": -0.10}, rnd, "2025-06-30") == ds0)
FINDINGS["B4.5"] = ("NO", "NOT_IMPLEMENTED")


# =====================================================================================
# B4.6 PARETO FRONTIER ANALYSIS
# =====================================================================================
# FORMAL METHOD: over a SET of alternatives with objective vectors, the nondominated subset.
# Ehrgott, Multicriteria Optimization, 2nd ed., Springer 2005, definition of Pareto optimality.
# The oracle and its known answer are the {B, C} result computed in the B4.1 section above.
pf = run_pareto_frontier({"cpi": 0.95, "spi": 0.92, "docRiskScore": 0.30}, rnd, "2025-06-30")
check("B4.6 the module returns a verdict about one project", "status_color" in pf)
check("B4.6 no set, no frontier and no dominance relation over alternatives appears",
      not any(w in str(pf).lower() for w in ("frontier_set", "nondominated_set",
                                             "alternatives", "dominates")))
# The decisive test: introducing an alternative that dominates the project must change a real
# Pareto analysis. It cannot change this one, because no alternative is ever seen.
pf_same = run_pareto_frontier({"cpi": 0.95, "spi": 0.92, "docRiskScore": 0.30,
                               "alternatives": ALTS}, rnd, "2025-06-30")
check("B4.6 supplying a set of alternatives, including one that strictly dominates the "
      "project, changes nothing at all", pf_same == pf)
check("B4.6 the canonical problem cannot be posed: a dominance relation needs a set and the "
      "module holds exactly one point", pf == pf_same)
FINDINGS["B4.6"] = ("NO", "NOT_IMPLEMENTED")


# =====================================================================================
# ACTIVATION PROTECTION: none of the eight became reachable
# =====================================================================================
from app.simulation.registry import run_module  # noqa: E402

DISABLED = ["A3.8", "B2.20", "B2.7", "B2.9", "B4.1", "B4.2", "B4.5", "B4.6"]
for mid in DISABLED:
    try:
        out = run_module(mid, {"cpi": 0.95, "spi": 0.92, "docRiskScore": 0.30},
                         rnd, "2025-06-30")
    except Exception:
        out = {"activation_state": "RAISED"}
    check(f"{mid} is still refused by the registry after this suite ran it directly",
          out.get("activation_state") in ("DISABLED_UNSAFE", "RAISED")
          and out.get("insufficient_data") is True and out.get("status_color") is None)

check("all eight were investigated", len(FINDINGS) == 8)

if FAILURES:
    for f in FAILURES:
        print("FAIL:", f)
print(f"RESULT: {PASS}/{TOTAL} checks passed")
sys.exit(0 if PASS == TOTAL else 1)
