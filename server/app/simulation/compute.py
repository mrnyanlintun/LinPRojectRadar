"""
The compute entry point.

One function: signalInputs plus (scenario_id, period) in; module results, category statuses and a
fused project status out. No HTTP action here; B7b wires it to the upload path.
"""

from __future__ import annotations

from typing import Any

from .fusion import dst_fuse
from .models import SIMULATION_VERSION
from .registry import registry_index, run_all


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

    # Category rollup, then project rollup, matching the frontend's two-stage fusion.
    by_category: dict[str, list[str]] = {}
    for row in run["computed"]:
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
        "project_conflict": project["conflict"] if project else 0.0,
        "categories_voting": len(voting),
    }
