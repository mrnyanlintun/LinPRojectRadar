"""
THE CANONICAL CATEGORY-10 DECISION-OPTIMIZATION LAYER, v20 (Run 32).

WHAT THIS REPLACES, and every one of these was real production behaviour at v19:

  B4.1  Multi-Objective Optimization   a weighted blend of cpi, spi and the document risk score.
                                       No alternatives, no objectives, no feasible region.
  B4.2  Linear Programming             a fixed rule score. No variables, no constraint matrix,
                                       no optimisation of anything.
  B4.3  Constraint Satisfaction        a checklist of fixed index thresholds. No variables, no
                                       domains, no constraint network.
  B4.4  What-If Scenario Matrix        several EAC formulas. No action identity, so nothing is
                                       being compared under anything.
  B4.5  Decision Sensitivity Matrix    a ranking of current KPI deviations. Nothing is perturbed
                                       and nothing is recomputed.
  B4.6  Pareto Frontier Analysis       threshold booleans over one project. One point is not a
                                       trade space.
  B4.7  Regret Minimization Index      an index with no payoff matrix, so no regret is defined.

THE GOVERNING FLOW, which is the whole architecture (section 4):

    QUALIFIED PROJECT STATE -> GOVERNED DECISION PROBLEM -> CANDIDATE ALTERNATIVES
    -> FEASIBILITY/CONSTRAINTS -> OBJECTIVES/CRITERIA -> SCENARIOS/PAYOFFS
    -> OPTIMIZATION/COMPARISON -> SENSITIVITY/ROBUSTNESS -> HUMAN-AUTHORIZED SELECTION.

CATEGORY 10 CREATES NO EVIDENCE. A recommendation is not an observation about the project.
Nothing here returns a `status_color`, nothing enters fusion, and `ANALYTICAL_RESULT` is stamped
on every result precisely so a reader -- and a guard -- can tell it from a `HUMAN_DECISION`.
Section 8 is not bookkeeping: an optimiser that could approve an action would be exercising an
authority no algorithm in this instrument holds.

ONE SHARED STRUCTURE, NOT SEVEN. `canonical_v5.decision_problem` already defines the alternative
identity, the criterion identity, the orientation vocabulary and the weight provenance that
B2.18 MARCOS and B2.19 CRITIC-TOPSIS were built on in Run 30. This layer REUSES it rather than
minting a parallel model, which is what section 17 requires and what stops a decision result
losing the alternatives it came from.

NO PARAMETER IS INVENTED. Section 23 forbids inventing preference weights, scenario
probabilities, utility weights, constraint penalties, soft-constraint weights, sensitivity ranges
and tie-breaking preferences. Every one of them must arrive IN the governed structure or the
method abstains and records that owner policy is required. That is why `minimax_regret` returns
its tie set rather than breaking a tie, and why `multi_objective` refuses to name a single best
alternative without supplied preference information.
"""

from __future__ import annotations

import itertools
from fractions import Fraction
from typing import Any, Iterable, Mapping, Sequence

from .canonical import StructureAbsent
from .canonical_v5 import decision_problem

#: The governed structure key each Category-10 module reads, and the reader's words for it.
V7_STRUCTURE_KEYS: dict[str, str] = {
    "B4.1": "decisionAlternatives",
    "B4.2": "linearProgramModel",
    "B4.3": "constraintSatisfactionProblem",
    "B4.4": "actionScenarioMatrix",
    "B4.5": "decisionSensitivityModel",
    "B4.6": "decisionAlternatives",
    "B4.7": "actionScenarioMatrix",
}

V7_STRUCTURE_WORDS: dict[str, str] = {
    "B4.1": "an explicit decision problem: the alternatives being compared, the objectives they "
            "are measured on, and the constraints that make them feasible",
    "B4.2": "a governed linear program: decision variables, objective coefficients, a constraint "
            "matrix, right-hand sides and variable bounds",
    "B4.3": "a governed constraint-satisfaction problem: variables, their domains, and the "
            "constraints over them",
    "B4.4": "a governed action-by-scenario matrix: the actions being compared, the scenarios "
            "they are compared under, and an outcome for every pair",
    "B4.5": "a governed decision model with base parameter values and the ranges they are to be "
            "perturbed over",
    "B4.6": "an explicit trade space: two or more alternatives, each with an objective vector "
            "and a declared orientation",
    "B4.7": "a governed action-by-scenario payoff or cost matrix",
}

#: Stamped on every Category-10 result. The ledger distinguishes this from a HUMAN_DECISION, and
#: the guard asserts against these constants rather than against a sentence.
ANALYTICAL_RESULT = "ANALYTICAL_RESULT"
HUMAN_DECISION = "HUMAN_DECISION"

#: What a Category-10 result may never claim.
AUTHORITY_NOTE = (
    "This is an analytical result. It does not approve, authorise, execute or lock any action, "
    "and it does not exercise the judgment of the responsible reviewer. Final selection remains "
    "human-authorised.")

#: Orientation vocabulary, shared with canonical_v5 so there is exactly one.
BENEFIT = "benefit"
COST = "cost"


def v7_structure(si: dict, module_id: str) -> dict:
    """The module's defining structure off the signal inputs, or StructureAbsent."""
    key = V7_STRUCTURE_KEYS[module_id]
    words = V7_STRUCTURE_WORDS[module_id]
    structure = si.get(key)
    if structure is None:
        raise StructureAbsent(
            f"Awaiting {words}. This measure is named for a method that cannot be carried out "
            f"without it, so no reading is reported and no other figure is used in its place.")
    if not isinstance(structure, dict):
        raise StructureAbsent(
            f"The information provided for this project in place of {words} is not in a form "
            f"this measure can read, so no reading is taken from it.")
    return structure


def _rows(structure: Mapping[str, Any], key: str, words: str) -> list[dict]:
    rows = structure.get(key)
    if not isinstance(rows, list) or not rows:
        raise StructureAbsent(
            f"Awaiting {words}. No entries are recorded, so there is nothing to solve and no "
            f"figure is produced in place of one.")
    for r in rows:
        if not isinstance(r, dict):
            raise StructureAbsent(
                f"An entry supplied as {words} is not in a form this measure can read.")
    return rows


def _context(structure: Mapping[str, Any], words: str) -> dict[str, Any]:
    """The decision context every Category-10 result carries, so a result can be attributed."""
    ctx = {
        "context_id": structure.get("context_id"),
        "project": structure.get("project"),
        "period": structure.get("period"),
        "purpose": structure.get("purpose"),
        "responsible_reviewer": structure.get("responsible_reviewer"),
        "authority_required": structure.get("authority_required"),
        "decision_horizon": structure.get("decision_horizon"),
        "source": structure.get("source"),
        "structure_version": structure.get("version"),
    }
    if not ctx["context_id"] or not ctx["source"]:
        raise StructureAbsent(
            f"The {words} provided for this project does not say which decision it belongs to or "
            f"where it came from, so a result taken from it could not be attributed later and "
            f"none is produced.")
    return ctx


def _result(module: str, context: dict[str, Any], **payload: Any) -> dict[str, Any]:
    """Every Category-10 result, stamped as analytical and carrying its authority boundary."""
    out: dict[str, Any] = {
        "measure": module,
        "decision_context": context,
        "result_class": ANALYTICAL_RESULT,
        "human_authorization_required": True,
        "authority_note": AUTHORITY_NOTE,
        "creates_project_evidence": False,
        "calibration_pending": True,
    }
    out.update(payload)
    return out


# =============================================================================================
# DOMINANCE -- shared by 10.1 and 10.6, because they are the same relation asked twice.
# =============================================================================================

def _objective_vectors(structure: Mapping[str, Any], words: str
                       ) -> tuple[list[dict], list[dict], dict[str, Any]]:
    """
    Alternatives with an objective vector each, read through the SHARED decision structure.

    `decision_problem` already enforces the properties this needs and that the campaign attacks:
    criteria are never alternatives, an alternative may not be named twice, and an orientation
    must be declared rather than assumed. Reusing it is section 17's requirement and it means
    MARCOS, CRITIC-TOPSIS and the Category-10 methods cannot drift apart.
    """
    problem = decision_problem(structure, module_id="B2.19", require_weights=False)
    criteria = problem["criteria"]
    alternatives = problem["alternatives"]
    # `decision_problem` validates identity and values but does not carry FEASIBILITY, which is a
    # Category-10 concern rather than a ranking concern. Re-attach the declared flag from the
    # governed structure by alternative identity, so a declared-infeasible alternative cannot
    # silently re-enter the trade space through the shared reader.
    declared = {str(a.get("alternative_id") or "").strip(): a
                for a in structure.get("alternatives", []) if isinstance(a, dict)}
    for a in alternatives:
        src = declared.get(a["alternative_id"], {})
        if src.get("feasible") is False:
            a["feasible"] = False
            a["infeasible_reason"] = src.get("infeasible_reason")
    if len(criteria) < 2:
        raise StructureAbsent(
            f"The {words} provided for this project declares fewer than two objectives, so there "
            f"is no trade-off to analyse and no frontier is reported.")
    if len(alternatives) < 2:
        raise StructureAbsent(
            f"The {words} provided for this project offers fewer than two alternatives, so there "
            f"is no trade space and no comparison is carried out.")
    return criteria, alternatives, problem


def _dominates(a: Sequence[float], b: Sequence[float], senses: Sequence[str]) -> bool:
    """
    `a` dominates `b`: no worse on every objective and strictly better on at least one.

    Orientation is applied per objective rather than assumed to be minimisation, which is what
    makes the same function correct for a cost objective and a benefit objective side by side.
    """
    better_somewhere = False
    for av, bv, sense in zip(a, b, senses):
        if sense == COST:
            if av > bv:
                return False
            if av < bv:
                better_somewhere = True
        else:
            if av < bv:
                return False
            if av > bv:
                better_somewhere = True
    return better_somewhere


def _nondominated(alternatives: Sequence[dict], criteria: Sequence[dict]
                  ) -> tuple[list[dict], list[dict]]:
    """
    The nondominated set and the dominated set, with the dominator named for each.

    PERMUTATION INVARIANCE IS STRUCTURAL, not asserted: an alternative is nondominated exactly
    when no other alternative dominates it, which does not depend on the order they were offered
    in. DUPLICATE POINTS both survive, because neither strictly beats the other on any objective
    and dominance requires a strict improvement somewhere.
    """
    senses = [c["orientation"] for c in criteria]
    keys = [c["criterion_id"] for c in criteria]
    vecs = {a["alternative_id"]: [float(a["values"][k]) for k in keys] for a in alternatives}
    front, dominated = [], []
    for a in alternatives:
        aid = a["alternative_id"]
        dominators = [b["alternative_id"] for b in alternatives
                      if b["alternative_id"] != aid
                      and _dominates(vecs[b["alternative_id"]], vecs[aid], senses)]
        row = {"alternative_id": aid, "label": a.get("label", aid),
               "objective_vector": dict(zip(keys, vecs[aid]))}
        if dominators:
            dominated.append(dict(row, dominated_by=sorted(dominators)))
        else:
            front.append(row)
    return front, dominated


def multi_objective(structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    10.1 MULTI-OBJECTIVE OPTIMIZATION.

        minimise over x: [f1(x), ..., fk(x)]  subject to g_j(x) <= 0, h_l(x) = 0, x in domain

    Over an explicit discrete alternative set this is the dominance relation, and the honest
    output is the feasible set, the objective vectors, the dominance relationships and the
    nondominated set.

    NO SINGLE BEST ALTERNATIVE IS NAMED. Choosing one from a nondominated set requires preference
    information -- weights, a utility function, a priority order -- and section 23 forbids
    inventing any of them. `selected_alternative` is therefore always None and the reason says
    so, which is a refusal rather than an omission.

    INFEASIBLE ALTERNATIVES ARE EXCLUDED BEFORE DOMINANCE, because an infeasible point cannot be
    on the frontier of a feasible region.
    """
    words = V7_STRUCTURE_WORDS["B4.1"]
    ctx = _context(structure, words)
    criteria, alternatives, _p = _objective_vectors(structure, words)
    feasible, infeasible = [], []
    for a in alternatives:
        if a.get("feasible") is False:
            infeasible.append({"alternative_id": a["alternative_id"],
                               "reason": a.get("infeasible_reason") or "declared infeasible"})
        else:
            feasible.append(a)
    if len(feasible) < 2:
        raise StructureAbsent(
            f"Fewer than two feasible alternatives remain in the {words} provided for this "
            f"project, so there is no trade-off to optimise over.")
    front, dominated = _nondominated(feasible, criteria)
    return _result(
        "multi_objective_optimization", ctx,
        objectives=[{"criterion_id": c["criterion_id"], "label": c["label"],
                     "orientation": c["orientation"], "units": c.get("units")}
                    for c in criteria],
        feasible_alternatives=[a["alternative_id"] for a in feasible],
        infeasible_alternatives=infeasible,
        objective_vectors={a["alternative_id"]:
                           {c["criterion_id"]: float(a["values"][c["criterion_id"]])
                            for c in criteria} for a in feasible},
        nondominated_set=[r["alternative_id"] for r in front],
        nondominated_detail=front,
        dominated_set=dominated,
        selected_alternative=None,
        selection_reason=(
            "no single alternative is named: selecting one point from a nondominated set "
            "requires supplied preference information, and none is governed here"),
        preference_information_supplied=False,
    )


def pareto_frontier(structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    10.6 PARETO FRONTIER ANALYSIS.

    The same dominance relation as 10.1, asked as a question about the trade space rather than
    about an optimisation. Threshold booleans over a single project are not this: one point has
    no frontier, which is why fewer than two alternatives abstains.
    """
    words = V7_STRUCTURE_WORDS["B4.6"]
    ctx = _context(structure, words)
    criteria, alternatives, _p = _objective_vectors(structure, words)
    feasible = [a for a in alternatives if a.get("feasible") is not False]
    if len(feasible) < 2:
        raise StructureAbsent(
            f"Fewer than two feasible alternatives remain in the {words} provided for this "
            f"project, so there is no frontier to report.")
    front, dominated = _nondominated(feasible, criteria)
    dupes: dict[str, list[str]] = {}
    keys = [c["criterion_id"] for c in criteria]
    for a in feasible:
        sig = tuple(float(a["values"][k]) for k in keys)
        dupes.setdefault(str(sig), []).append(a["alternative_id"])
    return _result(
        "pareto_frontier_analysis", ctx,
        objectives=[{"criterion_id": c["criterion_id"], "orientation": c["orientation"]}
                    for c in criteria],
        frontier=[r["alternative_id"] for r in front],
        frontier_detail=front,
        dominated_set=dominated,
        duplicate_points={k: v for k, v in dupes.items() if len(v) > 1},
        duplicate_policy=(
            "identical objective vectors do not dominate one another, because dominance requires "
            "a strict improvement on some objective, so every copy remains on the frontier"),
        permutation_invariant=True,
    )


# =============================================================================================
# 10.2 LINEAR PROGRAMMING
# =============================================================================================

def _lp_model(structure: Mapping[str, Any], words: str) -> dict[str, Any]:
    variables = _rows(structure, "variables", words)
    constraints = _rows(structure, "constraints", words)
    sense = str(structure.get("objective_sense") or "").strip().lower()
    if sense not in ("maximize", "minimize"):
        raise StructureAbsent(
            f"The {words} provided for this project does not say whether its objective is to be "
            f"maximised or minimised, so no optimum is computed and neither is assumed.")
    names, lower, upper, obj = [], {}, {}, {}
    for v in variables:
        vid = str(v.get("variable_id") or "").strip()
        if not vid:
            raise StructureAbsent(
                f"A decision variable in the {words} provided for this project has no identity.")
        if vid in names:
            raise StructureAbsent(
                f"The {words} provided for this project names the variable {vid} twice.")
        if "objective_coefficient" not in v:
            raise StructureAbsent(
                f"The {words} provided for this project states no objective coefficient for "
                f"{vid}, so the objective is undefined and none is assumed.")
        names.append(vid)
        obj[vid] = Fraction(str(v["objective_coefficient"]))
        lo = v.get("lower_bound", 0)
        lower[vid] = None if lo is None else Fraction(str(lo))
        up = v.get("upper_bound")
        upper[vid] = None if up is None else Fraction(str(up))
    rows = []
    for c in constraints:
        cid = str(c.get("constraint_id") or "").strip()
        op = str(c.get("operator") or "").strip()
        if op not in ("<=", ">=", "="):
            raise StructureAbsent(
                f"A constraint in the {words} provided for this project uses no recognised "
                f"operator, so the feasible region is undefined.")
        coeffs = c.get("coefficients")
        if not isinstance(coeffs, dict) or not coeffs:
            raise StructureAbsent(
                f"Constraint {cid} in the {words} provided for this project states no "
                f"coefficients.")
        if "rhs" not in c:
            raise StructureAbsent(
                f"Constraint {cid} in the {words} provided for this project states no "
                f"right-hand side.")
        rows.append({"constraint_id": cid, "operator": op,
                     "coefficients": {k: Fraction(str(x)) for k, x in coeffs.items()},
                     "rhs": Fraction(str(c["rhs"])), "units": c.get("units"),
                     "hard": bool(c.get("hard", True)), "source": c.get("source")})
    return {"sense": sense, "variables": names, "objective": obj,
            "lower": lower, "upper": upper, "constraints": rows}


def _lp_feasible(model: Mapping[str, Any], point: Mapping[str, Fraction]) -> tuple[bool, list]:
    """Feasibility of one point, including the declared variable bounds."""
    violations = []
    for vid in model["variables"]:
        lo, up = model["lower"][vid], model["upper"][vid]
        if lo is not None and point[vid] < lo:
            violations.append(f"{vid} below its lower bound {lo}")
        if up is not None and point[vid] > up:
            violations.append(f"{vid} above its upper bound {up}")
    for c in model["constraints"]:
        lhs = sum(c["coefficients"].get(v, Fraction(0)) * point[v] for v in model["variables"])
        if c["operator"] == "<=" and lhs > c["rhs"]:
            violations.append(f"{c['constraint_id']} violated ({lhs} > {c['rhs']})")
        elif c["operator"] == ">=" and lhs < c["rhs"]:
            violations.append(f"{c['constraint_id']} violated ({lhs} < {c['rhs']})")
        elif c["operator"] == "=" and lhs != c["rhs"]:
            violations.append(f"{c['constraint_id']} violated ({lhs} != {c['rhs']})")
    return (not violations), violations


def linear_program(structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    10.2 LINEAR PROGRAMMING, solved by EXACT VERTEX ENUMERATION over rationals.

    WHY VERTEX ENUMERATION AND NOT A LIBRARY SIMPLEX. The fundamental theorem of linear
    programming puts an optimum of a bounded feasible region at a vertex, and a vertex is the
    solution of a square subsystem of the binding constraints. Enumerating them with `Fraction`
    arithmetic gives an EXACT optimum with no tolerance to choose and no floating-point tie to
    resolve, and it is independently checkable: the oracle recomputes the objective by hand and
    confirms the same vertex.

    Feasibility is tested at every candidate, so an infeasible vertex cannot be returned, and the
    declared bounds -- including non-negativity -- are part of that test rather than an
    afterthought.
    """
    words = V7_STRUCTURE_WORDS["B4.2"]
    ctx = _context(structure, words)
    m = _lp_model(structure, words)
    n = len(m["variables"])
    if n == 0:
        raise StructureAbsent(f"The {words} provided declares no decision variables.")

    # Every half-space that can be binding: constraints plus the declared bounds.
    planes: list[tuple[dict, str]] = [(c, c["constraint_id"]) for c in m["constraints"]]
    for vid in m["variables"]:
        if m["lower"][vid] is not None:
            planes.append(({"coefficients": {vid: Fraction(1)}, "rhs": m["lower"][vid],
                            "operator": ">="}, f"{vid}>=lower"))
        if m["upper"][vid] is not None:
            planes.append(({"coefficients": {vid: Fraction(1)}, "rhs": m["upper"][vid],
                            "operator": "<="}, f"{vid}<=upper"))

    best = None
    vertices = []
    for combo in itertools.combinations(range(len(planes)), n):
        A = [[planes[i][0]["coefficients"].get(v, Fraction(0)) for v in m["variables"]]
             for i in combo]
        b = [planes[i][0]["rhs"] for i in combo]
        sol = _solve_exact(A, b)
        if sol is None:
            continue
        point = dict(zip(m["variables"], sol))
        ok, _viol = _lp_feasible(m, point)
        if not ok:
            continue
        value = sum(m["objective"][v] * point[v] for v in m["variables"])
        binding = [planes[i][1] for i in range(len(planes))
                   if _binding(planes[i][0], point, m["variables"])]
        vertices.append({"point": {k: float(v) for k, v in point.items()},
                         "objective_value": float(value), "binding": sorted(set(binding))})
        if best is None or (value > best[0] if m["sense"] == "maximize" else value < best[0]):
            best = (value, point, sorted(set(binding)))

    if best is None:
        return _result("linear_programming", ctx, disposition="INFEASIBLE",
                       reason="no feasible vertex exists for the governed model as stated",
                       optimum=None, objective_value=None)
    value, point, binding = best
    return _result(
        "linear_programming", ctx,
        objective_sense=m["sense"],
        variables=m["variables"],
        optimum={k: float(v) for k, v in point.items()},
        objective_value=float(value),
        binding_constraints=binding,
        vertices_examined=len(vertices),
        method="exact vertex enumeration over rationals",
        disposition="OPTIMAL",
    )


def _binding(plane: Mapping[str, Any], point: Mapping[str, Fraction],
             variables: Sequence[str]) -> bool:
    lhs = sum(plane["coefficients"].get(v, Fraction(0)) * point[v] for v in variables)
    return lhs == plane["rhs"]


def _solve_exact(A: list[list[Fraction]], b: list[Fraction]) -> list[Fraction] | None:
    """Exact Gaussian elimination. None when the subsystem is singular."""
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for col in range(n):
        piv = next((r for r in range(col, n) if M[r][col] != 0), None)
        if piv is None:
            return None
        M[col], M[piv] = M[piv], M[col]
        pv = M[col][col]
        M[col] = [x / pv for x in M[col]]
        for r in range(n):
            if r != col and M[r][col] != 0:
                f = M[r][col]
                M[r] = [x - f * y for x, y in zip(M[r], M[col])]
    return [M[i][n] for i in range(n)]


# =============================================================================================
# 10.3 CONSTRAINT SATISFACTION
# =============================================================================================

def constraint_satisfaction(structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    10.3 CONSTRAINT SATISFACTION ANALYSIS.

    A canonical CSP is variables, domains and constraints, and a solution assigns EVERY variable
    while satisfying EVERY applicable constraint. The old fixed-threshold checklist is not this
    and is not preserved under the canonical route: a checklist has no variables and no domains,
    so there is nothing to assign.

    Constraints are declared as governed rules, including the implication form the supplied
    oracle uses. Every rule is evaluated against every complete assignment -- no rule may be
    skipped, which is fault 9's target.
    """
    words = V7_STRUCTURE_WORDS["B4.3"]
    ctx = _context(structure, words)
    variables = _rows(structure, "variables", words)
    domains: dict[str, list] = {}
    for v in variables:
        vid = str(v.get("variable_id") or "").strip()
        dom = v.get("domain")
        if not vid:
            raise StructureAbsent(f"A variable in the {words} provided has no identity.")
        if not isinstance(dom, list) or not dom:
            raise StructureAbsent(
                f"Variable {vid} in the {words} provided for this project has no domain, so "
                f"there is nothing for it to be assigned from.")
        if vid in domains:
            raise StructureAbsent(f"The {words} provided names variable {vid} twice.")
        domains[vid] = list(dom)
    constraints = structure.get("constraints")
    if not isinstance(constraints, list) or not constraints:
        raise StructureAbsent(
            f"The {words} provided for this project declares no constraints, so every assignment "
            f"would be a solution and there is no satisfaction problem to analyse.")

    names = list(domains)
    feasible, infeasible = [], []
    for combo in itertools.product(*(domains[v] for v in names)):
        assignment = dict(zip(names, combo))
        failed = [c.get("constraint_id") for c in constraints
                  if not _csp_holds(c, assignment, words)]
        if failed:
            infeasible.append({"assignment": assignment, "violated": failed})
        else:
            feasible.append({"assignment": assignment})
    return _result(
        "constraint_satisfaction", ctx,
        variables=names,
        domains=domains,
        constraint_ids=[c.get("constraint_id") for c in constraints],
        assignments_examined=len(feasible) + len(infeasible),
        feasible_assignments=feasible,
        infeasible_assignments=infeasible,
        satisfiable=bool(feasible),
    )


def _csp_holds(constraint: Mapping[str, Any], assignment: Mapping[str, Any],
               words: str) -> bool:
    """
    One governed constraint against one complete assignment.

    Only DECLARED rule forms are evaluated; an unrecognised form RAISES rather than being
    skipped, because a constraint silently treated as satisfied is exactly how a checklist passes
    for a constraint network.
    """
    kind = str(constraint.get("type") or "").strip().lower()
    if kind == "implication":
        ante, cons = constraint.get("if"), constraint.get("then")
        if not isinstance(ante, dict) or not isinstance(cons, dict):
            raise StructureAbsent(
                f"An implication constraint in the {words} provided is not stated as a condition "
                f"and a consequence, so it cannot be evaluated.")
        if all(assignment.get(k) == v for k, v in ante.items()):
            return all(assignment.get(k) == v for k, v in cons.items())
        return True
    if kind == "forbidden":
        combo = constraint.get("assignment")
        if not isinstance(combo, dict):
            raise StructureAbsent(f"A forbidden-combination constraint states no assignment.")
        return not all(assignment.get(k) == v for k, v in combo.items())
    if kind == "all_different":
        vs = constraint.get("variables")
        if not isinstance(vs, list) or len(vs) < 2:
            raise StructureAbsent("An all-different constraint names fewer than two variables.")
        vals = [assignment.get(v) for v in vs]
        return len(set(vals)) == len(vals)
    raise StructureAbsent(
        f"A constraint in the {words} provided uses the rule form {kind!r}, which this method "
        f"does not evaluate. It is not treated as satisfied, so no solution set is reported.")


# =============================================================================================
# 10.4 / 10.7 -- THE ACTION-BY-SCENARIO MATRIX AND THE DECISION RULE OVER IT
# =============================================================================================

def _matrix(structure: Mapping[str, Any], words: str) -> dict[str, Any]:
    ctx = _context(structure, words)
    actions = _rows(structure, "actions", words)
    scenarios = _rows(structure, "scenarios", words)
    orientation = str(structure.get("orientation") or "").strip().lower()
    if orientation not in (BENEFIT, COST):
        raise StructureAbsent(
            f"The {words} provided for this project does not say whether its cells are payoffs "
            f"to be maximised or costs to be minimised, so no comparison is made and neither is "
            f"assumed.")
    aids, sids = [], []
    for a in actions:
        aid = str(a.get("action_id") or "").strip()
        if not aid:
            raise StructureAbsent(
                f"An action in the {words} provided has no identity. Formulas with no action "
                f"identity are not an action-by-scenario matrix.")
        if aid in aids:
            raise StructureAbsent(f"The {words} provided names action {aid} twice.")
        aids.append(aid)
    for s in scenarios:
        sid = str(s.get("scenario_id") or "").strip()
        if not sid:
            raise StructureAbsent(f"A scenario in the {words} provided has no identity.")
        if sid in sids:
            raise StructureAbsent(f"The {words} provided names scenario {sid} twice.")
        sids.append(sid)
    cells_in = structure.get("cells")
    if not isinstance(cells_in, dict):
        raise StructureAbsent(
            f"The {words} provided for this project carries no outcome cells, so there is no "
            f"matrix to compare over.")
    cells: dict[tuple[str, str], float] = {}
    missing = []
    for aid in aids:
        for sid in sids:
            row = cells_in.get(aid)
            val = row.get(sid) if isinstance(row, dict) else None
            if val is None:
                missing.append(f"{aid}/{sid}")
            else:
                cells[(aid, sid)] = float(val)
    # A MATRIX WITH A HOLE IS NOT A COMPLETE MATRIX. Section 12 asks for explicit missing-cell
    # behaviour, and the honest behaviour is refusal: a decision rule over an incomplete matrix
    # would silently treat an unknown outcome as if it were known.
    if missing:
        raise StructureAbsent(
            f"The {words} provided for this project has no outcome for "
            f"{', '.join(missing[:6])}{' and others' if len(missing) > 6 else ''}, so the matrix "
            f"is incomplete and no comparison is made across it.")
    return {"context": ctx, "actions": aids, "scenarios": sids, "cells": cells,
            "orientation": orientation, "units": structure.get("units"),
            "model_version": structure.get("model_version"),
            "probabilities": {s.get("scenario_id"): s.get("probability") for s in scenarios
                              if s.get("probability") is not None}}


def whatif_scenario_matrix(structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    10.4 WHAT-IF SCENARIO MATRIX.

    Rows are candidate ACTIONS, columns are SCENARIOS, cells are outcomes. Several EAC formulas
    with no action identity are not this, which is why an action without an id refuses.

    This module COMPARES; it does not choose. No decision rule is applied here and no action is
    recommended -- 10.7 applies a rule to the same matrix, and a human authorises the selection.
    Scenario probabilities are carried ONLY where supplied; none is invented, so no expected
    value is computed unless the governed structure states the probabilities.
    """
    words = V7_STRUCTURE_WORDS["B4.4"]
    m = _matrix(structure, words)
    grid = {a: {s: m["cells"][(a, s)] for s in m["scenarios"]} for a in m["actions"]}
    return _result(
        "whatif_scenario_matrix", m["context"],
        actions=m["actions"], scenarios=m["scenarios"], matrix=grid,
        orientation=m["orientation"], units=m["units"], model_version=m["model_version"],
        complete=True,
        scenario_probabilities=m["probabilities"] or None,
        expected_values=None if not m["probabilities"] else {
            a: sum(m["cells"][(a, s)] * float(m["probabilities"][s]) for s in m["scenarios"]
                   if s in m["probabilities"]) for a in m["actions"]},
        recommended_action=None,
        recommendation_reason=(
            "this measure compares alternatives under scenarios and applies no decision rule; "
            "it names no action"),
    )


def minimax_regret(structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    10.7 MINIMAX REGRET DECISION RULE.

    For payoff maximisation:  M_s = max_a P(a,s);  R(a,s) = M_s - P(a,s);
                              R_max(a) = max_s R(a,s);  choose argmin_a R_max(a).

    For a COST matrix the best outcome in a scenario is the minimum, so the regret is
    P(a,s) - min_a P(a,s). The orientation is DECLARED in the governed structure and is never
    assumed, which is fault 17's target: reading a cost matrix as payoffs inverts every regret.

    THE TIE POLICY IS EXPLICIT AND IS A REFUSAL. When several alternatives share the minimum
    maximum regret, all of them are returned and none is chosen, because breaking the tie needs a
    preference that section 23 forbids inventing.

    THE RESULT DOES NOT AUTHORISE ANYTHING. It identifies the minimax-regret alternative under
    the supplied matrix and stops there; `human_authorization_required` is True on every row.
    """
    words = V7_STRUCTURE_WORDS["B4.7"]
    m = _matrix(structure, words)
    best_in_scenario = {}
    for s in m["scenarios"]:
        vals = [m["cells"][(a, s)] for a in m["actions"]]
        best_in_scenario[s] = max(vals) if m["orientation"] == BENEFIT else min(vals)
    regret = {}
    for a in m["actions"]:
        regret[a] = {}
        for s in m["scenarios"]:
            v = m["cells"][(a, s)]
            regret[a][s] = (best_in_scenario[s] - v if m["orientation"] == BENEFIT
                            else v - best_in_scenario[s])
    max_regret = {a: max(regret[a].values()) for a in m["actions"]}
    lowest = min(max_regret.values())
    tied = sorted(a for a in m["actions"] if max_regret[a] == lowest)
    return _result(
        "minimax_regret", m["context"],
        actions=m["actions"], scenarios=m["scenarios"],
        orientation=m["orientation"], units=m["units"],
        payoff_matrix={a: {s: m["cells"][(a, s)] for s in m["scenarios"]} for a in m["actions"]},
        scenario_best=best_in_scenario,
        regret_matrix=regret,
        maximum_regret=max_regret,
        minimax_regret_value=lowest,
        minimax_regret_alternatives=tied,
        minimax_regret_alternative=(tied[0] if len(tied) == 1 else None),
        tie_policy=("all alternatives sharing the minimum maximum regret are returned and none "
                    "is chosen; breaking the tie requires a supplied preference and none is "
                    "governed here"),
        tied=len(tied) > 1,
    )


# =============================================================================================
# 10.5 DECISION SENSITIVITY
# =============================================================================================

def decision_sensitivity(structure: Mapping[str, Any]) -> dict[str, Any]:
    """
    10.5 DECISION SENSITIVITY MATRIX.

    A decision model, base parameter values, declared perturbation ranges, and the RANKINGS
    RECOMPUTED across those ranges -- with the crossover points where the ranking reverses.
    Ranking today's KPI deviations is not this: nothing is perturbed and nothing is recomputed.

    The supplied contract's case is a two-criterion weighted additive model where one weight `w`
    is swept and the other is `1 - w`. The crossover is solved EXACTLY as a linear equation in
    `w` rather than detected by sampling, so `4/7` is returned as `4/7` and not as the nearest
    grid point.

    NO DEFAULT WEIGHT AND NO DEFAULT RANGE IS INVENTED. Both arrive in the structure or the
    method abstains.
    """
    words = V7_STRUCTURE_WORDS["B4.5"]
    ctx = _context(structure, words)
    model = structure.get("model")
    if not isinstance(model, dict) or str(model.get("type") or "").lower() != "weighted_additive":
        raise StructureAbsent(
            f"The {words} provided for this project does not declare a decision model this "
            f"method can perturb, so nothing is recomputed and no sensitivity is reported.")
    params = _rows(structure, "parameters", words)
    alts = _rows(structure, "alternatives", words)
    scores = {}
    for a in alts:
        aid = str(a.get("alternative_id") or "").strip()
        vals = a.get("values")
        if not aid or not isinstance(vals, dict):
            raise StructureAbsent(
                f"An alternative in the {words} provided carries no identity or no criterion "
                f"values, so it cannot be scored.")
        scores[aid] = {k: float(v) for k, v in vals.items()}
    if len(scores) < 2:
        raise StructureAbsent(
            f"The {words} provided offers fewer than two alternatives, so no ranking can reverse "
            f"and no sensitivity is reported.")
    swept = [p for p in params if p.get("perturbation") == "sweep"]
    if len(swept) != 1:
        raise StructureAbsent(
            f"The {words} provided for this project does not declare exactly one swept "
            f"parameter, so this method does not know what to vary and varies nothing.")
    p = swept[0]
    pid = str(p.get("parameter_id") or "").strip()
    lo, hi = p.get("range_low"), p.get("range_high")
    if lo is None or hi is None:
        raise StructureAbsent(
            f"The swept parameter in the {words} provided states no range, so there is nothing "
            f"to perturb over and no range is assumed.")
    lo, hi = Fraction(str(lo)), Fraction(str(hi))
    partner = str(model.get("complement_criterion") or "").strip()
    primary = str(model.get("swept_criterion") or "").strip()
    if not partner or not primary:
        raise StructureAbsent(
            f"The decision model in the {words} provided does not say which criterion the swept "
            f"weight applies to, so no score can be recomputed.")

    def score(aid: str, w: Fraction) -> Fraction:
        return (Fraction(str(scores[aid][primary])) * w
                + Fraction(str(scores[aid][partner])) * (Fraction(1) - w))

    aids = sorted(scores)
    crossovers = []
    for a, b in itertools.combinations(aids, 2):
        # score_a(w) - score_b(w) is linear in w: (da - db)*w + (ca - cb)
        da = Fraction(str(scores[a][primary])) - Fraction(str(scores[a][partner]))
        db = Fraction(str(scores[b][primary])) - Fraction(str(scores[b][partner]))
        ca = Fraction(str(scores[a][partner]))
        cb = Fraction(str(scores[b][partner]))
        slope, intercept = da - db, ca - cb
        if slope == 0:
            continue
        w = -intercept / slope
        if lo <= w <= hi:
            crossovers.append({"between": [a, b], "parameter_id": pid,
                               "crossover_value": float(w),
                               "crossover_exact": f"{w.numerator}/{w.denominator}"})
    def ranking_at(w: Fraction):
        return [aid for aid, _s in sorted(((a, score(a, w)) for a in aids),
                                          key=lambda t: (-t[1], t[0]))]
    samples = [lo, (lo + hi) / 2, hi]
    for c in crossovers:
        w = Fraction(c["crossover_exact"])
        for delta in (Fraction(-1, 100), Fraction(1, 100)):
            cand = w + delta
            if lo <= cand <= hi:
                samples.append(cand)
    trace = [{"parameter_value": float(w), "ranking": ranking_at(w)}
             for w in sorted(set(samples))]
    return _result(
        "decision_sensitivity", ctx,
        model=model, swept_parameter=pid,
        base_value=(float(Fraction(str(p["base_value"]))) if p.get("base_value") is not None
                    else None),
        range=[float(lo), float(hi)],
        alternatives=aids,
        crossovers=crossovers,
        rank_reversal=bool(crossovers),
        perturbation_trace=trace,
        recomputed=True,
    )
