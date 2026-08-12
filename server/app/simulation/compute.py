"""
The compute entry point.

One function: signalInputs plus (scenario_id, period) in; module results, category statuses and a
fused project status out. No HTTP action here; B7b wires it to the upload path.
"""

from __future__ import annotations

from typing import Any

from .fusion import dst_fuse, governed_status_semantics
from .models import SIMULATION_VERSION
from .registry import CORE_VOTING_MODULES, registry_index, run_all


def contributes_to_project_status(group: str) -> bool:
    """
    Does this group describe the CONDITION of the project?

    Group C does not. It measures how trustworthy the evidence base is, which is a quality gate on
    scenario construction, not a property of the project. Early reporting periods carry the least
    evidence, so folding it into status would make every early scenario read worse for reasons that
    have nothing to do with the project. This mirrors contributesToProjectStatus() on the frontend.

    Group D does not appear here at all: the registry refuses it on a single-project path.
    """
    return group not in ("C", "D")


def compute_project(si: dict, scenario_id: str, period: str,
                    period_cutoff) -> dict[str, Any]:
    """
    Run the analytical layer and fuse it into a project status.

    period_cutoff is the reporting period's data cutoff date, and it is required. It is the
    only notion of "now" available to any module: nothing in this layer reads the system
    clock, because the same documents must produce the same result on any day they are run.
    """
    run = run_all(si, scenario_id, period, period_cutoff)
    index = registry_index()

    # Run 1 remediation, fusion-exclusion list (remediation_decisions_answered.md 1.1, Option C;
    # 1.2). The seven CORE_VOTING_MODULES vote on project status on an interim basis; every other
    # module still computes and still appears in `run["computed"]` for the ledger, but its status
    # is withheld from the category rollup below and therefore from project status fusion, the
    # generated recommendation text, and the decision card -- all three read this same
    # category_statuses / project_status result. Ledger visibility is untouched: this loop is the
    # ONLY thing that changed, nothing upstream of `run["computed"]` did.
    by_category: dict[str, list[str]] = {}
    for row in run["computed"]:
        if row["module_id"] not in CORE_VOTING_MODULES:
            continue
        by_category.setdefault(row["category"], []).append(row["status_color"])

    category_statuses: dict[str, dict[str, Any]] = {}
    for cat, statuses in sorted(by_category.items()):
        fused = dst_fuse(statuses)
        group = index[next(k for k, v in index.items() if v["category"] == cat)]["group"] \
            if any(v["category"] == cat for v in index.values()) else ""
        category_statuses[cat] = {
            "status": fused["status"] if fused else None,
            "conflict": fused["conflict"] if fused else 0.0,
            "group": group,
            "module_count": len(statuses),
            "contributes_to_project_status": contributes_to_project_status(group),
        }

    voting = [c["status"] for c in category_statuses.values()
              if c["status"] and c["contributes_to_project_status"]]
    project = dst_fuse(voting)

    # ------------------------------------------------------------------ RUN 11, GATES 5 AND 6
    # Derived, not asserted, and derived by the same pure function the read path uses, so a
    # freshly computed response and a stored row read back can never disagree about what the
    # rollup is called or whether its conflict is estimable. See fusion.governed_status_semantics.
    semantics = governed_status_semantics(category_statuses,
                                          project["conflict"] if project else 0.0)
    voting_module_ids = sorted(r["module_id"] for r in run["computed"]
                               if r["module_id"] in CORE_VOTING_MODULES)

    return {
        "simulation_version": SIMULATION_VERSION,
        "seed": run["seed"],
        "scenario_id": scenario_id,
        "period": period,
        "period_cutoff": str(period_cutoff),
        "modules": run["computed"],
        "abstained": run["abstained"],
        "unported": run["unported"],
        "category_statuses": category_statuses,
        "project_status": project["status"] if project else None,
        # RUN 11, GATES 5 AND 6. project_conflict keeps its original name so every reader that
        # already looks for it keeps working, but it is None rather than 0.0 when the coefficient
        # cannot be estimated: a consumer that prints it now prints nothing instead of printing a
        # zero it would have read as independent agreement.
        **semantics,
        "voting_module_ids": voting_module_ids,
        "categories_voting": len(voting),
    }
