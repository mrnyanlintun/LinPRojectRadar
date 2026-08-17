"""
THE CATEGORY-10 DECISION-OPTIMIZATION RUNNERS, v20. ONE THIN ROUTE PER MODULE.

WHY THIS FILE EXISTS, AND IT IS THE SAME LESSON RUN 30 PAID FOR. Run 30 built a correct canonical
library that production never called: twenty identities, 239 green oracle checks, and
`canonical_v5` reached on ZERO of twenty when the production entry point was actually profiled.
A correct library behind an unchanged ledger is a failed remediation. So `canonical_v7.py` is
worth nothing until `registry.VALIDATED` points here, and the operational-route proof executes
`registry.run_module` and profiles the interpreter rather than calling the canonical functions
directly.

WHAT EACH RUNNER IS ALLOWED TO DO, and it is deliberately almost nothing:

    governed decision structure -> canonical validation -> canonical implementation
                                -> analytical result or explicit abstention -> row

A runner reads its module's governed structure off the signal inputs, hands it to the canonical
function and renders the answer. IT PERFORMS NO ARITHMETIC OF ITS OWN, so there is nowhere for a
proxy to live. In particular NOTHING HERE READS `cpi`, `spi` OR `docRiskScore` -- those three
fields are precisely what the v19 Category-10 implementations blended into an "optimization"
score, and a route that cannot see them cannot rebuild one.

THE QUALIFICATION GATE IS NOT REPEATED HERE. `qualification_contract` already declares
"Decision Optimization" as REQUIRED and `qualification_boundary.install` wraps every entry in the
dispatch table, so a Category-10 route reaches this file only through the boundary. Gating again
inside the runner would put a second copy of the rule in the tree, and two copies drift.

THE AUTHORITY BOUNDARY IS THE POINT OF THE ROW SHAPE (section 8). Every row this file emits
carries `result_class = ANALYTICAL_RESULT`, `human_authorization_required = True` and
`creates_project_evidence = False`, and NO row ever carries a `status_color`. A decision
recommendation is not an observation about the project: it must not enter fusion, it must not
become new project-condition evidence, and it must not read as an approval. The ledger can
therefore separate an ANALYTICAL_RESULT from a HUMAN_DECISION by a named field rather than by
reading a sentence.

CATEGORY 10 IS NOT ACTIVATED BY THIS FILE. Four of the seven are disabled concept-only modules
and stay disabled; a laboratory pass is not activation, and activation is not this run's to
grant.
"""

from __future__ import annotations

from typing import Any, Callable

from . import canonical_v7 as V7
from .canonical import StructureAbsent
from .canonical_v7 import (
    ANALYTICAL_RESULT, AUTHORITY_NOTE, V7_STRUCTURE_KEYS, v7_structure,
)
from .models import ABSTAIN_STRUCTURE_ABSENT

#: Stamped on every Category-10 ledger row this file produces, computed or abstaining. A row
#: without this marker did not come from here, which is how the route inventory is verified from
#: the ledger rather than from a report.
RESULT_SOURCE = "CANONICAL_V7_LAYER"

DISPOSITION_COMPUTED = "CANONICAL_RESULT"
DISPOSITION_STRUCTURE_ABSENT = "NOT_ESTIMABLE_STRUCTURE_ABSENT"


def _authority_fields() -> dict[str, Any]:
    """
    The section-8 boundary, asserted identically on a computed row and an abstaining one.

    An abstention must carry it too. A reader who sees only "no result" still needs the row to
    say that this measure could not have approved anything even if it had produced a number.
    """
    return {
        "result_class": ANALYTICAL_RESULT,
        "human_authorization_required": True,
        "creates_project_evidence": False,
        "authority_note": AUTHORITY_NOTE,
        "status_color": None,
        "band_asserted": False,
        "calibration_pending": True,
    }


def _abstain(module_id: str, method_class: str, sentence: str) -> dict[str, Any]:
    row = {
        "abstention_reason_code": ABSTAIN_STRUCTURE_ABSENT,
        "method_class": method_class,
        "insufficient_data": True,
        "result_source": RESULT_SOURCE,
        "canonical_disposition": DISPOSITION_STRUCTURE_ABSENT,
        "canonical_structure": V7_STRUCTURE_KEYS.get(module_id),
        "evidence_metric": sentence,
    }
    row.update(_authority_fields())
    return row


def _route(module_id: str, method_class: str,
           fn: Callable[[dict], dict[str, Any]]) -> Callable:
    """Build ONE runner. It validates, delegates, and renders. It computes nothing."""

    def run(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
        try:
            structure = v7_structure(si, module_id)
        except StructureAbsent as exc:
            return _abstain(module_id, method_class, exc.sentence)
        try:
            result = fn(structure)
        except StructureAbsent as exc:
            # THERE IS NO CORPUS ASSEMBLY FALLBACK HERE, and that is deliberate. A decision
            # problem is a statement of what the owner is choosing between; the controlled
            # corpus holds no candidate action set, so assembling one would be inventing the
            # alternatives. Section 23 forbids inventing the parameters, and inventing the
            # alternatives themselves would be worse.
            return _abstain(module_id, method_class, exc.sentence)
        row: dict[str, Any] = {
            "method_class": method_class,
            "result_source": RESULT_SOURCE,
            "canonical_disposition": DISPOSITION_COMPUTED,
            "canonical_structure": V7_STRUCTURE_KEYS[module_id],
        }
        row.update(result)
        # RE-ASSERTED AFTER `result`, so a canonical payload cannot introduce a band or claim an
        # authority by overwriting these keys.
        row.update(_authority_fields())
        row["evidence_metric"] = _sentence(module_id, result)
        return row

    run.__name__ = f"run_{module_id.replace('.', '_')}"
    return run


def _sentence(module_id: str, result: dict[str, Any]) -> str:
    """
    The reader's sentence. It reports what was compared; it never recommends and never approves.
    """
    m = result.get("measure")
    if m == "multi_objective_optimization":
        n = len(result.get("nondominated_set") or [])
        d = len(result.get("dominated_set") or [])
        return (f"{n} of {n + d} feasible alternatives are non-dominated across the declared "
                f"objectives; no single alternative is selected, because choosing one requires "
                f"preference information that is not governed here")
    if m == "pareto_frontier_analysis":
        f = result.get("frontier") or []
        d = result.get("dominated_set") or []
        return (f"{len(f)} of {len(f) + len(d)} alternatives lie on the Pareto frontier of the "
                f"declared trade space")
    if m == "linear_programming":
        if result.get("disposition") != "OPTIMAL":
            return "the governed linear program has no feasible solution as stated"
        return (f"the governed linear program attains {result.get('objective_value')} at the "
                f"reported vertex, with "
                f"{len(result.get('binding_constraints') or [])} binding constraints")
    if m == "constraint_satisfaction":
        f = len(result.get("feasible_assignments") or [])
        return (f"{f} of {result.get('assignments_examined')} complete assignments satisfy every "
                f"declared constraint")
    if m == "whatif_scenario_matrix":
        return (f"{len(result.get('actions') or [])} actions are compared across "
                f"{len(result.get('scenarios') or [])} scenarios; this measure applies no "
                f"decision rule and names no action")
    if m == "decision_sensitivity":
        c = result.get("crossovers") or []
        return (f"the ranking reverses at {len(c)} point(s) over the declared range of "
                f"{result.get('swept_parameter')}" if c else
                f"the ranking does not reverse anywhere in the declared range of "
                f"{result.get('swept_parameter')}")
    if m == "minimax_regret":
        if result.get("tied"):
            alts = ", ".join(result.get("minimax_regret_alternatives") or [])
            return (f"{alts} share the lowest maximum regret of "
                    f"{result.get('minimax_regret_value')}; none is chosen, because breaking the "
                    f"tie requires a preference that is not governed here")
        return (f"{result.get('minimax_regret_alternative')} has the lowest maximum regret, "
                f"{result.get('minimax_regret_value')}, under the supplied matrix; final "
                f"selection remains human-authorised")
    return str(result.get("reason") or "")


#: THE ROUTE TABLE. `registry.VALIDATED` is repointed at these, and nothing else reaches the
#: Category-10 legacy implementations from a production run.
#:
#: THE §3 RENAME IS VISIBLE HERE. B4.7 was "Regret Minimization Index", a name for an index that
#: had no payoff matrix and therefore defined no regret. The canonical method IS the minimax
#: regret decision rule, so the method class says so.
CAT10_CANONICAL: dict[str, tuple[str, Callable]] = {
    "B4.1": ("Multi_Objective_Optimization",
             _route("B4.1", "Multi_Objective_Optimization", V7.multi_objective)),
    "B4.2": ("Linear_Programming",
             _route("B4.2", "Linear_Programming", V7.linear_program)),
    "B4.3": ("Constraint_Satisfaction",
             _route("B4.3", "Constraint_Satisfaction", V7.constraint_satisfaction)),
    "B4.4": ("WhatIf_Scenario_Matrix",
             _route("B4.4", "WhatIf_Scenario_Matrix", V7.whatif_scenario_matrix)),
    "B4.5": ("Decision_Sensitivity_Matrix",
             _route("B4.5", "Decision_Sensitivity_Matrix", V7.decision_sensitivity)),
    "B4.6": ("Pareto_Frontier",
             _route("B4.6", "Pareto_Frontier", V7.pareto_frontier)),
    "B4.7": ("Minimax_Regret_Decision_Rule",
             _route("B4.7", "Minimax_Regret_Decision_Rule", V7.minimax_regret)),
}
