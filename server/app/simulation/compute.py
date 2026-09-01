"""
The compute entry point.

One function: signalInputs plus (scenario_id, period) in; module results, category statuses and a
fused project status out. No HTTP action here; B7b wires it to the upload path.
"""

from __future__ import annotations

from typing import Any

from .category_posture import category_posture
from .fusion import fuse_signals, governed_status_semantics, worst_band
from .project_posture import project_posture
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
#: Run 89 goal three. The single definition; `spec_projection` imports these names so
#: the two status paths cannot drift about which categories are required.
#:
#: RUN 95, THE OWNER'S RULING, SECTION 3.2. THE REQUIRED CORE IS ALL FIVE, AND IT SUPERSEDES
#: RUN 89'S CORE OF FOUR. A4 Document Signals moves from supporting to required: an official
#: project status is issued only when every one of the five weighted performance categories
#: carries a posture, and if any one does not NO POSTURE IS ISSUED.
#:
#: RUN 106, GOAL TWO. THE WORD THE PLATFORM USES WHEN IT CANNOT ISSUE ONE IS NOW "Awaiting
#: analysis". The owner has ruled there are six statuses and Indeterminate is not one of them.
#: THE GATE ITSELF IS UNCHANGED -- what changed is the word, and that the word is never bare:
#: `project_status_reason` below states which category is unassessed and why no posture follows.
#:
#: A5 Systems and Dynamics IS NOT LISTED HERE AND IS NOT A CATEGORY OF THIS PLATFORM ANY MORE.
#: Run 95 retired every module it held, so it holds none in service; an empty category has
#: nothing to report rather than failing to report. It is gone from the required core, from the
#: weighted profile in `models_gov.py` and from both charts.
_REQUIRED_CATEGORIES: tuple[str, ...] = ("A1", "A2", "A3", "A4", "A6")
#: EMPTY, AND DELIBERATELY KEPT RATHER THAN DELETED. Every weighted performance category is now
#: required, so there is no supporting tier left to hold anything. The name and the two
#: `supporting_*` keys it feeds are kept because `documents._result_view`, `spec_projection` and
#: the client all read them, and a key that vanishes reads as a missing field rather than as an
#: empty tier. They publish `[]` and that is the true answer: no category is supporting.
_SUPPORTING_CATEGORIES: tuple[str, ...] = ()
# RUN 106, GOAL TWO. THE OWNER'S SIX STATUSES ARE Complete, Green, Yellow, Amber, Red AND
# "Awaiting analysis", and the seventh word this platform used to publish -- "Indeterminate" --
# is gone from every surface that issues, stores, renders or describes a status. His reason, in
# his words: nobody will understand one word. So "Awaiting analysis" now covers BOTH conditions
# a project can be in without a posture -- documents uploaded and not yet processed, and
# processed with a required category unassessed -- and every one of them renders a SENTENCE
# saying which it is and what is missing.
#
# ROWS ALREADY STORED CARRYING "Indeterminate" KEEP WHAT THEY HOLD. Nothing is rewritten and no
# migration is added; a row stamped v51 or earlier means what it meant when it was written.
_AWAITING = "Awaiting analysis"

#: Reader-facing category names for the sentence below. The registry is the authority and is read
#: first; this map exists only so a category with no registry row still gets a readable name
#: rather than a bare key. It is the same fallback `decision_brief` carries, for the same reason.
_CATEGORY_NAMES = {
    "A1": "Cost and EVM Performance",
    "A2": "Schedule Performance",
    "A3": "Cost Risk",
    "A4": "Document-Derived Signals",
    "A6": "Delivery Quality",
}


def category_name(key: str) -> str:
    """The registry's own name for a category, falling back to the map above, then to the key."""
    try:
        from .registry import load_registry
        for row in load_registry():
            if row.get("category") == key and row.get("category_name"):
                return str(row["category_name"]).strip()
    except Exception:                                                      # noqa: BLE001
        pass
    return _CATEGORY_NAMES.get(key, key)


def _awaiting_reason(required_missing, category_statuses) -> str:
    """
    RUN 106, GOAL TWO. THE SENTENCE THAT MUST ACCOMPANY "Awaiting analysis".

    The owner's words: a bare label is not enough, nobody will understand one word. So the
    reason NAMES WHAT IS MISSING -- which required category carries no posture, and whether it
    was never called or was called and produced no band -- and says plainly that no posture is
    issued this period.

    It asserts nothing about the project. "Cost Risk has not been assessed" is a statement about
    the platform's evidence, not a finding about the work, which is why it needs no figure and
    passes the Run 70 recommendation checks unchanged.
    """
    missing = list(required_missing or [])
    if not missing:
        return ("No project posture is issued this period. The analysis has not produced a "
                "band for this project.")
    cats = category_statuses if isinstance(category_statuses, dict) else {}
    parts = []
    for key in missing:
        if key not in cats:
            why = ("no module in this category was run for this period")
        else:
            why = ("the category was called and no module in it asserted a band")
        parts.append(f"{category_name(key)} ({key}) has not been assessed \u2014 {why}")
    return ("No project posture is issued this period, because a required category could not be "
            "assessed: " + "; ".join(parts) + ". The project status is withheld rather than "
            "imputed, and no value was substituted for what is missing.")


# --------------------------------------------------------------- RUN 99, THE COMPLETE STATUS
#
# THE OWNER'S RULING, RUN 99 SECTION 4: "Complete" is one of the six statuses every project must
# resolve to, and he states its condition precisely -- "earned value, planned value and actual
# cost all equal to budget at 100 percent". Three of his fifteen planned projects are authored
# to exactly that.
#
# BEFORE THIS RUN NOTHING IN THE SERVED TREE COULD EMIT IT. Measured, not argued: a project
# seeded through the real upload and compute routes with EV = PV = AC = BAC and 100 per cent
# complete published "Indeterminate", identically to a project 25 per cent through its work.
# `--status-complete` existed as a CSS token and `LEGEND_BANDS` named it, but a token and a
# legend row are not a code path. The one promotion rule in the tree, `deriveProjectStatus` in
# assets/js/taxonomy.js, is reachable ONLY from the researcher deep-dive surface, which
# recomputes in the browser; nothing on the participant's route calls it.
#
# IT IS A FACT ABOUT DELIVERY, NOT A RISK BAND, and that is why it sits AHEAD of the required-
# core gate rather than behind it. The gate asks "may an OFFICIAL RISK POSTURE be issued" and
# withholds one when a required category carries none. Completion is not a posture: the work is
# delivered at budget or it is not, and no schedule-risk or quality reading can make a finished
# project unfinished. Behind the gate, the owner's three complete projects could never publish
# Complete -- they carry the same unassessed categories as every other project -- and a status
# he has ruled the platform publishes would be unreachable by construction.
#
# "COMPLETE" IS NOT A BAND AND IS DELIBERATELY NOT ADDED TO `fusion.BAND_SEVERITY`. It never
# enters `worst_band` and is never ranked against Green, Yellow, Amber or Red. THE PROJECT RULE
# IS UNTOUCHED BY THIS PROMOTION: `fused_band` -- since Run 105 the worst band across the
# contributing categories -- is reported beside the status either way, so nothing that needs the
# SEVERITY of a completed project's evidence loses it to this promotion.
#
# EXACT EQUALITY, AND NO TOLERANCE. The owner's condition is an equality and it is applied as
# one. A tolerance would be a threshold this run invented, and an invented threshold is the
# thing this programme fails runs for. A project one pound short of budget is not Complete here
# and that is the honest answer, not a rounding defect.
_COMPLETE = "Complete"


def _as_number(value):
    """The value as a finite number, or None. Booleans are not numbers here."""
    if value is None or isinstance(value, bool):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if out == out and out not in (float("inf"), float("-inf")) else None


def delivery_complete(signal_inputs: dict | None) -> bool:
    """
    The owner's Complete condition, in one place, read by BOTH status paths.

    True when the budget is a positive number, earned value, planned value and actual cost are
    all exactly equal to it, and the recorded percent complete is 100. Any missing figure is
    False: an absent number is not evidence of completion.
    """
    si = signal_inputs or {}
    bac = _as_number(si.get("bac"))
    if bac is None or bac <= 0:
        return False
    for key in ("ev", "pv", "ac"):
        value = _as_number(si.get(key))
        if value is None or value != bac:
            return False
    pct = _as_number(si.get("actualPctComplete"))
    if pct is None:
        pct = _as_number(si.get("pctComplete"))
    return pct == 100.0
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
    # rollup are, at Run 65, unchanged -- what changed then is which computed rows are allowed
    # to reach them. RUN 104 CHANGED THE WITHIN-CATEGORY RULE and this sentence no longer
    # describes it: A1, A2, A3 and A4 AVERAGE their banded modules' scores, A6 takes the worst,
    # and an unassigned category keeps worst-wins. The worst category still wins the project.
    #
    # A MODULE THAT DECLINED DOES NOT VOTE AND DOES NOT DRAG ITS CATEGORY DOWN. `by_category`
    # receives COMPUTED rows only; an abstention is an absence of a reading, not an adverse one,
    # so a category's posture is formed from the modules that actually spoke -- and since Run 104
    # a module that spoke without a band is not in the average either, and is never a zero.
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
        #
        # RUN 104. THE POSTURE IS NO LONGER THE FUSION'S BAND. `category_posture` decides, by the
        # owner's two rules -- A1, A2, A3 and A4 average their banded modules' scores; A6 takes
        # the worst; an unassigned category keeps worst-wins. The fusion is STILL RUN and its
        # record is still stored, because `conflict`, the lineage bodies and the within-body
        # disagreement flag are read by surfaces and by the qualification record and are not
        # this run's to remove; what it no longer does is DECIDE. That is the defect Run 103
        # measured: the fusion treated modules declaring no lineage as independent bodies, so
        # three Greens outvoted an Amber and the category read greener than the evidence.
        posture = category_posture(
            # ADMISSION IS UNCHANGED and is the gate's, not a second opinion written here:
            # `to_fusion_signal` presents no status for a signal that may not vote, which is
            # exactly what the fusion was handed a line above.
            cat, [(qs.module_id, qs.to_fusion_signal()["status"]) for qs in signals])
        setters = posture["status_set_by"]
        category_statuses[cat] = {
            "status": posture["status"],
            "posture_rule": posture["posture_rule"],
            "posture_rule_words": posture["posture_rule_words"],
            "posture_rule_short": posture["posture_rule_short"],
            "posture_boundary": posture["posture_boundary"],
            "posture_arithmetic": posture["posture_arithmetic"],
            "posture_module_scores": posture["posture_module_scores"],
            "posture_banded_count": posture["posture_banded_count"],
            "posture_average": posture["posture_average"],
            # RUN 105, GOAL THREE. Whether this posture is an average over one reading, and the
            # sentence that says so. This call site hands over EVERY admitted module, banded or
            # not, so `posture_modules_considered` is the length of that list.
            "posture_single_reading": posture["posture_single_reading"],
            "posture_thinness_words": posture["posture_thinness_words"],
            "posture_modules_considered": posture["posture_modules_considered"],
            # The band the fusion would have produced, kept BESIDE the posture and never in
            # place of it, so the change this run made is visible in a stored row.
            "fusion_band": fused["status"] if fused else None,
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
    # structurally by ordering. Nothing in the rollup or in the project-level rule is altered.
    #
    # RUN 104 MEASURED B1.2's INPUT MOVING. B1.2 reads the six category postures, and this run
    # changed how four of them are formed, so its input changed on any project where a category
    # holds more than one banded module. Its own weights, its renormalisation and its exclusion
    # from the rollup are untouched.
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

    # ------------------------------------------------------- RUN 89, GOAL THREE, REQUIRED CORE
    # THE OWNER'S RULING, RUN 95 SECTION 3.2, SUPERSEDING RUN 89's. An OFFICIAL status is issued
    # only when all FIVE required categories -- A1 Cost and EVM, A2 Schedule, A3 Cost Risk,
    # A4 Document Signals, A6 Delivery Quality -- carry a posture. There is no supporting tier
    # any more, and no category can create a Green merely because no documents were supplied.
    #
    # THE GATE IS A CONDITION LAYERED ON TOP of whatever band the project rule produces, and
    # Run 105 changed that rule (below) without touching the gate: when all five required
    # categories carry a posture the gate passes the band through unaltered, exactly as before.
    #
    # RUN 106, GOAL ONE. THE WEIGHTS SET THE STATUS, AND WORST-WINS IS GONE FROM PROJECT LEVEL.
    #
    # WHAT STOOD HERE. Run 105 made `_fused_band = worst_band([v["status"] for v in voting])`,
    # replacing the Dempster fusion that had decided it before. The owner has now ruled that
    # rule out at project level for a stated reason: worst-wins means a project is almost never
    # Green, everyone lives in permanent alarm, and nobody trusts the dashboard. The project
    # status is the WEIGHTED VOTE over the five category postures on his profile -- A1 0.28,
    # A2 0.28, A3 0.17, A4 0.11, A6 0.16 -- scored Green +2, Yellow +1, Amber -1, Red -2 and
    # banded on the same cuts the category averages use. The rule is `project_posture`, which
    # both this path and `spec_projection` call, so the two paths cannot drift.
    #
    # NO OVERRIDE. A Red in Delivery Quality moves the sum by 0.16 and no more. The consequence
    # -- a Green project with an adverse module inside it -- is DISCLOSED rather than softened:
    # `decision_brief` names every adverse module reading as a material driver regardless of
    # the band above it.
    #
    # CATEGORY RULES ARE UNCHANGED. `category_posture` still averages A1-A4 and takes the worst
    # in A6. This changed only how the project combines the five.
    #
    # THE FUSION IS STILL RUN AND STILL STORED, and still does not decide. `project["conflict"]`
    # is the belief-conflict coefficient `governed_status_semantics` reads below and is a real
    # measurement over the same voting categories; removing the call would have forced a zero to
    # be invented there. `dempster_band` keeps publishing the band Dempster's rule would give,
    # beside the status and never in place of it.
    #
    # `worst_band` IS STILL IMPORTED AND STILL USED -- by `category_posture` for A6 and by the
    # per-module fusion above. It is only the PROJECT rule that stopped being worst-wins.
    #
    # THE GATE IS UNCHANGED. What it publishes when it withholds is now "Awaiting analysis",
    # with a sentence naming the unassessed category beside it.
    _required_missing = [k for k in _REQUIRED_CATEGORIES
                         if not (category_statuses.get(k) or {}).get("status")]
    _dempster_band = project["status"] if project else None
    _posture = project_posture(category_statuses)
    _fused_band = _posture["status"]
    # RUN 99. The Complete promotion, decided by the one function above and applied identically
    # on the specification path in `spec_projection`. Ahead of the gate; see the note there.
    _complete = delivery_complete(si)
    # RUN 106, GOAL TWO. A project with no posture publishes "Awaiting analysis" -- and it does
    # so BOTH when a required category is unassessed and when the weighted rule formed no band
    # at all. The second arm cannot be reached while the first stands (no posture at all means
    # every required category is missing), and it is written anyway so no future edit to the
    # gate can let a None reach a surface as a status.
    _published = (_COMPLETE if _complete
                  else (_AWAITING if (_required_missing or not _fused_band) else _fused_band))
    _status_reason = _awaiting_reason(_required_missing, category_statuses) if (
        _published == _AWAITING) else None

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
        "project_status": _published,
        # Why the status is what it is, so a surface can render the Awaiting-analysis brief
        # without re-deriving the gate. The weighted band is reported EITHER WAY, so an
        # Awaiting-analysis brief can still show every assessed category and any that are Red.
        "project_status_basis": {
            "required_categories": list(_REQUIRED_CATEGORIES),
            "supporting_categories": list(_SUPPORTING_CATEGORIES),
            "required_assessed": [k for k in _REQUIRED_CATEGORIES
                                  if k not in _required_missing],
            "required_missing": _required_missing,
            "required_missing_detail": [
                {"category": k,
                 "state": "never_called" if k not in category_statuses else "not_assessed",
                 "missing": "no module in this category was run for this period"
                            if k not in category_statuses else
                            "the category was called and no module in it asserted a band"}
                for k in _required_missing],
            "supporting_assessed": [k for k in _SUPPORTING_CATEGORIES
                                    if (category_statuses.get(k) or {}).get("status")],
            "supporting_not_assessed": [k for k in _SUPPORTING_CATEGORIES
                                        if not (category_statuses.get(k) or {}).get("status")],
            "fused_band": _fused_band,
            # RUN 106, GOAL ONE. The project rule's own working, so a card can show the sum
            # instead of asking a reader to trust it, and goal two's sentence.
            "project_rule": _posture["project_rule"],
            "project_rule_short": _posture["project_rule_short"],
            "project_rule_words": _posture["project_rule_words"],
            "project_boundary": _posture["project_boundary"],
            "project_arithmetic": _posture["project_arithmetic"],
            "project_weighted_sum": _posture["weighted_sum"],
            "project_category_scores": _posture["category_scores"],
            "project_weights": _posture["weights"],
            "project_weight_provenance": _posture["weight_provenance"],
            "project_renormalised": _posture["renormalised"],
            "status_reason": _status_reason,
            "official": _complete or not _required_missing,
            "delivery_complete": _complete,
            "status": _published,
        },
        # The band the WEIGHTED RULE produced, kept under its own name so nothing that needs
        # the band loses it to the gate. This is not a second project status. The NAME is Run
        # 89's and is kept because every stored row and every surface already reads it; what it
        # holds has been the project rule's own band since Run 105 and is the weighted band now.
        "fused_band": _fused_band,
        # RUN 106, GOAL TWO. The sentence that goes with "Awaiting analysis", so no surface has
        # to compose it and none can render the bare word.
        "project_status_reason": _status_reason,
        # RUN 105. The band Dempster's rule would have produced over the same categories, kept
        # BESIDE the status and never in place of it, so the change this run made is visible in
        # a stored row -- the same discipline Run 104 applied to `fusion_band` per category.
        "dempster_band": _dempster_band,
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
