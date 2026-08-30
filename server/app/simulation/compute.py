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
from .models_gov import weighted_voting_result as _weighted_voting_result
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
                    period_cutoff, project_id: str | None = None) -> dict[str, Any]:
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
    # ----------------------------------------------------------- RUN 65, EVERY MODULE VOTES
    # A MODULE THAT PRODUCED A VALUE VOTES INTO ITS OWN CATEGORY. Before this run only the two
    # CORE_VOTING_MODULES reached fusion, and both sit in Cost and EVM, so ten of the eleven
    # categories could not carry a status no matter what computed beneath them: a project whose
    # document signals held three computing modules still rendered grey. The rules of the
    # rollup are unchanged -- worst status wins within a category, and the worst category wins
    # the project -- what changed is which computed rows are allowed to reach them.
    #
    # A MODULE THAT DECLINED DOES NOT VOTE AND DOES NOT DRAG ITS CATEGORY DOWN. `by_category`
    # receives COMPUTED rows only; an abstention is an absence of a reading, not an adverse
    # one, so a category's status is the worst of the modules that actually spoke.
    #
    # CORE_VOTING_MODULES IS UNCHANGED and still names the two modules whose band boundaries a
    # source specifies (Run 4). It keeps its second job here: the ABSTENTION loop below reports
    # those two to the qualification gate whether they ran or not, which is what the gate and
    # blocker B05 read. Widening that loop to all 101 would flood the gate record with 57
    # abstentions that say only "this module needs evidence this project does not carry", so it
    # stays narrow; the gate record for a vote is written by the computed loop, which now
    # writes one for every module that voted.
    _abstained_voters = {r["module_id"] for r in run["abstained"]
                         if r["module_id"] in CORE_VOTING_MODULES}
    by_category: dict[str, list[QualifiedSignal]] = {}
    gate_reports: list[dict[str, Any]] = []
    for row in run["computed"]:
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
        # RUN 65, 2.4. THE CATEGORY RECORDS WHICH MODULE SET IT, so a status stays explainable
        # once more than two modules can produce one. Derived from the fusion's own record --
        # the member bands inside each lineage body, plus any unresolved signal that carried the
        # band forward -- rather than re-deciding the worst band at this call site.
        setters: list[str] = []
        if fused and fused["status"]:
            for b in fused["lineage_bodies"]:
                setters += [m for m, band in zip(b["member_module_ids"], b["member_bands"])
                            if band == fused["status"]]
            if fused.get("unresolved_band") == fused["status"]:
                setters += list(fused.get("unresolved_module_ids") or ())
        setters = sorted(set(setters))
        category_statuses[cat] = {
            "status": fused["status"] if fused else None,
            "conflict": fused["conflict"] if fused else 0.0,
            "group": group,
            "module_count": len(signals),
            "status_set_by": setters,
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

    # ---------------------------------------------------------------- RUN 89, GOAL ONE, PASS TWO
    # B1.2 WEIGHTED VOTING READS THE SIX PERFORMANCE CATEGORY POSTURES, so it can only be
    # evaluated once those postures exist -- which is here, after the rollup and before the
    # project fusion. `models_gov.run_weighted_voting` abstained at dispatch naming exactly this;
    # its row is replaced now with the reading, or with the abstention the postures state.
    #
    # IT CANNOT REACH THE ROLLUP IT READS. `category_statuses` is already built above and is not
    # rebuilt, so a B1.2 band computed here sets no category and reaches no project status. That
    # is the same conclusion Run 87 reached by admission in `spec_projection`, here reached
    # structurally by ordering. Nothing in the rollup or in worst-wins is altered.
    _b12 = _weighted_voting_result(category_statuses)
    _b12_row = None
    for _bucket in ("computed", "abstained"):
        for _i, _r in enumerate(run[_bucket]):
            if _r.get("module_id") == "B1.2":
                _b12_row = dict(_r)
                run[_bucket].pop(_i)
                break
        if _b12_row is not None:
            break
    if _b12_row is not None:
        _b12_row.update(_b12)
        _b12_row["status_color"] = _b12.get("status_color")
        _b12_row["abstention_reason"] = _b12.get("abstention_reason")
        if _b12.get("status_color"):
            _b12_row.pop("abstention_reason", None)
            run["computed"].append(_b12_row)
        else:
            run["abstained"].append(_b12_row)

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
    # RUN 65. THE MODULES THAT ACTUALLY VOTED, which is now every module that computed.
    voting_module_ids = sorted(r["module_id"] for r in run["computed"])

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
        # RUN 42. THE PROJECT'S OWN IDENTITY, PASSED IN. This read `si.get("projectId") or
        # si.get("id")` and the signal-inputs dict has neither key -- `extraction_merge._KEY_ORDER`
        # is the reported figures and nothing else -- so the qualification record recorded
        # project_id as null for every project ever computed, while the caller had the identity
        # in hand the whole time. The si keys are kept ahead of it so a caller that really does
        # carry the identity in its inputs still wins.
        project_id=si.get("projectId") or si.get("id") or project_id,
        reporting_period=period,
        period_cutoff=period_cutoff,
        generated_at=None,
    )
    return result
