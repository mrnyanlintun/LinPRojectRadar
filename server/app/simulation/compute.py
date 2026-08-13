"""
The compute entry point.

One function: signalInputs plus (scenario_id, period) in; module results, category statuses and a
fused project status out. No HTTP action here; B7b wires it to the upload path.
"""

from __future__ import annotations

from typing import Any

from .fusion import fuse_signals, governed_status_semantics
from .lineage import lineage_for, lineage_record
from .qualification_gate import (
    GATE_VERSION,
    QualifiedSignal,
    fuse_qualified,
    preflight,
    qualify,
)
from .models import SIMULATION_VERSION
from .qualification import build_qualification
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
    # ------------------------------------------------------------------- RUN 20 CYCLE 3, P0D
    # THE VOTES NOW CARRY THEIR LINEAGE INTO THE COMBINATION. Both voting modules are transforms
    # of one body of earned-value evidence: the to-complete performance index reaches the earned
    # value directly, the variance at completion reaches it through the cost performance index
    # and the estimate at completion. Fused as two independent sources they manufactured
    # corroboration that one body of evidence does not warrant, and in the one disagreement the
    # old rule did not resolve conservatively -- a Green and a Yellow reading -- they produced a
    # GREEN cost recovery status out of evidence one of whose two readings was not green.
    #
    # Nothing about a module's own band, boundary or arithmetic changed. What changed is that the
    # combination is told what it is combining. A module with no declared lineage is NOT assumed
    # independent: it gets a record of its own and the fusion reports `lineage_declared` false,
    # which the qualification gate reads.
    # --------------------------------------------------- RUN 20 CYCLE 3, THE CATEGORY-9 GATE
    # PROJECT EVIDENCE -> CATEGORY-9 PREFLIGHT -> ANALYTICAL MODULE -> CATEGORY-9 SIGNAL
    # QUALIFICATION -> the combination. Every vote is now a QualifiedSignal, and the combination
    # is reached through `fuse_qualified`, which refuses anything that did not come through the
    # gate. A signal the gate rejects or degrades has no band to offer and therefore casts no
    # vote: the verdict changes what executes rather than annotating what executed anyway.
    #
    # On the evidence packages this platform produces today the preflight assesses exactly one
    # of its conditions, the presence of what a module requires, because those packages declare
    # no as-of dates, no document identities, no audit record and no domains. That is the honest
    # position and it is stated in the gate itself: what is not declared is not assessed, and it
    # is certainly not assumed clean. The remaining conditions become live for any package that
    # carries the declarations, without this call site changing.
    # WHERE THE REQUIRED-EVIDENCE CONDITION IS DECIDED, and why it is not decided here. ONE place
    # decides what a module requires, and it is the module: `check_inputs` inside the module's own
    # function. Restating those field lists at this call site would be a hand-maintained copy of
    # production logic checked against production logic, which is the failure this programme has
    # already found nine times. So a voting module that could not run appears in `run["abstained"]`
    # and reaches the gate as an ABSTAINED signal, rather than the gate re-deriving the answer the
    # module has already given. The preflight's own required-evidence rule stays live for any
    # caller that supplies a package and a field list, and the gate suite exercises it directly.
    _abstained_voters = {r["module_id"] for r in run["abstained"]
                         if r["module_id"] in CORE_VOTING_MODULES}
    by_category: dict[str, list[QualifiedSignal]] = {}
    gate_reports: list[dict[str, Any]] = []
    for row in run["computed"]:
        if row["module_id"] not in CORE_VOTING_MODULES:
            continue
        pre = preflight(si, (), period_cutoff)
        qs = qualify(row["module_id"], row["status_color"], row.get("evidence_metric"),
                     pre, lineage=lineage_for(row["module_id"]),
                     module_abstained=row["module_id"] in _abstained_voters)
        gate_reports.append(qs.report())
        by_category.setdefault(row["category"], []).append(qs)
    for r in run["abstained"]:
        if r["module_id"] not in CORE_VOTING_MODULES:
            continue
        gate_reports.append(qualify(r["module_id"], None, None,
                                    preflight(si, (), period_cutoff),
                                    lineage=lineage_for(r["module_id"]),
                                    module_abstained=True).report())

    category_statuses: dict[str, dict[str, Any]] = {}
    category_bodies: dict[str, tuple[str, ...]] = {}
    for cat, signals in sorted(by_category.items()):
        fused = fuse_signals(fuse_qualified(signals))
        group = index[next(k for k, v in index.items() if v["category"] == cat)]["group"] \
            if any(v["category"] == cat for v in index.values()) else ""
        bodies = tuple(b["lineage_group"] for b in fused["lineage_bodies"]) if fused else ()
        category_bodies[cat] = bodies
        category_statuses[cat] = {
            "status": fused["status"] if fused else None,
            "conflict": fused["conflict"] if fused else 0.0,
            "group": group,
            "module_count": len(signals),
            "contributes_to_project_status": contributes_to_project_status(group),
            # The audit trail of the combination, so a reader of a stored row can see how many
            # bodies of evidence stood behind a band and whether they disagreed, rather than
            # having to infer it from a module count that says nothing about dependence.
            "lineage_bodies": list(bodies),
            "lineage_body_count": len(bodies),
            "lineage_declared": bool(fused and fused["lineage_declared"]),
            "within_lineage_disagreement": bool(
                fused and any(b["disagreement"] for b in fused["lineage_bodies"])),
        }

    # A category's fused status INHERITS the bodies of evidence behind it, so two categories that
    # rest on one body cannot corroborate each other at the project level either. With one voting
    # category today this changes nothing; it is written now because the alternative is a second
    # place that has its own opinion about dependence, which is what this cycle exists to remove.
    voting = [{"status": c["status"], "module_id": cat,
               "lineage": lineage_record(cat, lineage_group_ids=category_bodies.get(cat, ()))}
              for cat, c in category_statuses.items()
              if c["status"] and c["contributes_to_project_status"]]
    project = fuse_signals(voting)

    # ------------------------------------------------------------------ RUN 11, GATES 5 AND 6
    # Derived, not asserted, and derived by the same pure function the read path uses, so a
    # freshly computed response and a stored row read back can never disagree about what the
    # rollup is called or whether its conflict is estimable. See fusion.governed_status_semantics.
    semantics = governed_status_semantics(category_statuses,
                                          project["conflict"] if project else 0.0)
    voting_module_ids = sorted(r["module_id"] for r in run["computed"]
                               if r["module_id"] in CORE_VOTING_MODULES)

    result = {
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
        # The Category-9 gate's verdict on every vote, so a reader of a stored row can see what
        # was allowed, degraded, abstained or rejected and why, rather than only what survived.
        "signal_qualification": gate_reports,
        "signal_qualification_version": GATE_VERSION,
        "categories_voting": len(voting),
    }

    # ------------------------------------------------------------------------ RUN 12, GATE 2
    # The evidence qualification (the category nine question), attached AFTER the status is
    # fused and derived FROM the run that produced it. Placed here and only here because this is
    # the smallest point at which the resolved evidence and the abstentions it caused are both
    # in hand. It is metadata: it adds no module, casts no vote, moves no band and cannot change
    # `project_status`, which is already computed above and is not read back. The two dimensions
    # this repository cannot answer stay PARTIAL and NOT_ESTIMABLE rather than becoming a
    # penalty or a score.
    result["evidence_qualification"] = build_qualification(
        si, result,
        project_id=si.get("projectId") or si.get("id"),
        reporting_period=period,
        period_cutoff=period_cutoff,
        generated_at=None,
    )
    return result
