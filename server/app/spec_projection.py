"""
Run 79. THE SPECIFICATION READINGS BECOME THE SOURCE FOR EVERY SURFACE.

WHAT WAS WRONG. Run 76 and 77 built the specification layer. It stores what it read in
`specification_readings` (migration 0028). Every surface -- the signal ledger, the project
signal network, the signal flow diagram, the executive brief, the governance decision card,
the project header and the portfolio row -- read `computed_results`, which the retired Python
module layer writes. The category panel showed one thing and the rest of the page showed
another, and the page was showing figures from a layer the owner has replaced.

WHERE THE FIX GOES, AND WHY HERE. Run 73 established by execution that every chart and panel
on the detail page reads the SAME stored row through `LinResults.rowFor(project)` in
taxonomy.js, and that row arrives from exactly two server projections:

    documents._result_view   -> `projectresults`, primed as the detail row
    facade.live_statuses     -> `storedResult`, the header line and the portfolio row

So the substitution is made ONCE, server-side, in the three fields those two projections carry
that name a reading or a status -- `module_results`, `category_statuses`, `project_status`.
Every client surface then follows without a client change, which is also why NO COMPUTATION
MOVES INTO THE CLIENT (order section 2, "What this must not do", item 2): the client keeps
rendering exactly what the server hands it.

THE RULE, from the order's section 2, implemented literally:

    A surface renders the stored specification reading, or it renders nothing.

There is NO FALLBACK. When a category has no live specification reading it is ABSENT from
`category_statuses`, and its modules are ABSENT from `module_results`. `getCategoryStatus`
then returns null and the ledger renders the category as not called; `getModuleStatus` returns
"NODATA", which is the existing "the row exists, this module has no entry" state. Neither ever
reaches back into `computed_results` for an older figure.

NOT CALLED IS NOT ABSTAINED, and the order's proof 3 tests exactly that. Four states cross the
API from `spec_readings.reading_payload`; a category that was never called has no row at all,
so it carries no state, and `category_statuses` simply does not have the key. The two are
distinguishable on the wire and on the page.

THE POSTURE RULE STAYS IN PYTHON AND IS THE SHARED ONE. `simulation.category_posture` decides
a CATEGORY's posture, here as in `spec_apply.apply_category` and as in the Python rollup, and
there is no second severity table in this file.

RUN 104 REPLACED ONE RULE WITH TWO, BY CATEGORY, AND THIS FILE NO LONGER DESCRIBES ITSELF AS
WORST-WINS THROUGHOUT, because that is no longer true of four categories out of five:

  * A1 Cost and EVM, A2 Schedule, A3 Cost Risk and A4 Document-Derived Signals AVERAGE their
    banded modules' scores -- Green +2, Yellow +1, Amber -1, Red -2 -- over only the modules
    that asserted a band. They are performance measures and one weak module among several
    should move the posture without dominating it.
  * A6 Delivery Quality takes the WORST band any of its modules asserted. Quality, safety,
    environmental and contractor performance are conformance and compliance measures; an
    adverse reading in one of them is a finding in its own right and is not averaged against
    three good ones.
  * A category the owner did not assign keeps worst-wins, unchanged.

An abstention is still an absence of a reading, not an adverse one, and it is NOT a zero in the
average either. THE PROJECT STATUS IS UNCHANGED: it is still `worst_band` over the categories
that contribute, by `compute.contributes_to_project_status`, which excludes groups C and D.

`computed_results` IS NOT TOUCHED, NOT WRITTEN AND NOT DELETED. It remains the record of what
the Python layer produced and the freeze architecture keeps referencing it. This module only
declines to READ it for a module reading or a status.

BAND CASE. `spec_apply.normalise_module` PRESERVES the spelling the specification emitted and
validates on `band.capitalize()`, because A1.2 CUSUM legitimately emits lower case. `worst_band`
filters on the capitalised spelling only, so this module capitalises before ranking and before
publishing `status_color`, which is the same thing `apply_category` already does at its own
fusion call. Nothing is invented: the capitalised form is the only one `BAND_SEVERITY` names.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .research_models import SpecificationReading
from .simulation import spec_apply as sa
from .simulation.compute import contributes_to_project_status
from .simulation.category_posture import category_posture
from .simulation.fusion import BAND_SEVERITY, worst_band
from .simulation.registry import service_index

#: The registry group each category sits in, derived from the registry rather than stated, so
#: this file cannot drift from it. {'A1': 'A', ..., 'C1': 'C'}.
def _category_groups() -> dict[str, str]:
    out: dict[str, str] = {}
    for row in service_index().values():
        cat = row.get("category")
        if cat and cat not in out:
            out[cat] = row.get("group") or ""
    return out


def _band(value) -> str | None:
    """The capitalised spelling, or None. Never ranks a token the rule cannot rank."""
    if value is None:
        return None
    text = str(value).capitalize()
    return text if text in BAND_SEVERITY else None


def live_readings(session: Session, project_id: str, period: int) -> dict[str, SpecificationReading]:
    """
    The live (non-superseded) specification reading per category for one project-period.

    Same predicate as `spec_readings._live_reading`, batched: one query for the page rather
    than eleven. A category with no row is ABSENT from the mapping -- that absence is the
    "never called" state and is what every consumer below preserves.
    """
    rows = session.scalars(
        select(SpecificationReading).where(
            SpecificationReading.project_id == project_id,
            SpecificationReading.period == period,
            SpecificationReading.superseded_by.is_(None),
        ).order_by(SpecificationReading.created_at)
    ).all()
    out: dict[str, SpecificationReading] = {}
    for r in rows:
        out[r.category_key] = r  # later created_at wins, matching the ORDER BY desc + first()
    return out


def module_rows(readings: dict[str, SpecificationReading]) -> list[dict[str, Any]]:
    """
    The COMPUTED module readings, in the shape taxonomy.js already reads.

    `module_id` and `status_color` are the two fields `getModuleStatus` and `getModuleResult`
    look for, and they carry the same meaning they carried on the Python row. The
    specification's own fields ride alongside, unrenamed, so the ledger can show the value it
    was given rather than a re-derived one.

    A module that ABSTAINED is not here, exactly as an abstaining Python module was never in
    `module_results`. It is in `abstention_rows` below, where `getModuleAbstentionReason`
    reads it and prints its reason verbatim.
    """
    out: list[dict[str, Any]] = []
    for key in sa.ALL_CATEGORIES:
        stored = readings.get(key)
        if stored is None or stored.state != sa.COMPUTED:
            continue
        for m in (stored.modules or []):
            if not isinstance(m, dict) or m.get("state") != sa.COMPUTED:
                continue
            out.append({
                "module_id": m.get("module_id"),
                "category": key,
                "status_color": _band(m.get("band")),
                "band": m.get("band"),
                "band_asserted": m.get("band_asserted"),
                "value": m.get("value"),
                "display": m.get("display"),
                "evidence_metric": m.get("evidence_metric"),
                "narrative": m.get("reason"),
                # Provenance on the row itself, so a reader of one module reading can see which
                # layer produced it without consulting the category panel.
                "source": "specification_reading",
                "served_by": stored.served_by,
                "model_id": stored.model_id,
                "specification_sha256": stored.specification_sha256,
                "reading_id": stored.reading_id,
            })
    return out


def abstention_rows(readings: dict[str, SpecificationReading]) -> list[dict[str, Any]]:
    """Every module that spoke and declined, with the reason it stated, verbatim."""
    out: list[dict[str, Any]] = []
    for key in sa.ALL_CATEGORIES:
        stored = readings.get(key)
        if stored is None:
            continue
        for m in (stored.modules or []):
            if isinstance(m, dict) and m.get("state") == sa.ABSTAINED:
                out.append({"module_id": m.get("module_id"), "reason": m.get("reason"),
                            "category": key})
    return out


# ---------------------------------------------------------------------------------------------
# RUN 87. WHICH MODULES ARE ADMITTED TO THE CATEGORY ROLLUP.
#
# THIS CHANGES ADMISSION, NOT THE DECISION RULE. The posture rule still decides, here and in
# `spec_apply.apply_category` -- since Run 104 that rule is `category_posture`, not `worst_band`
# alone. The only thing this set changes is which computed module readings are handed to it.
#
# THE DEFECT THIS CLOSES. `compute.contributes_to_project_status` is a GROUP-level predicate and
# is correctly True for group B: B1.1 Conservative Dominance is a decision rule over the four
# assembled arms and legitimately carries a band. There was no MODULE-level admission rule
# anywhere on this path, so a comparison ensemble's band set its category's status and reached
# the project status. (RUN 104: the category rule is no longer worst-wins everywhere -- see the
# header -- but ADMISSION is untouched by that change and this set still decides it.)
#
# THE SET IS ESTABLISHED FROM THE TREE, NOT INVENTED. Two texts establish it:
#
#   `simulation/models_gov.py`, the header over the three runners:
#       "RUN 30, v15. THE THREE COMPARISON ENSEMBLES NOW SYNTHESISE GOVERNED SIGNALS."
#       "All three remain ADVISORY_ONLY and non-voting. Voting is exactly A1.7 and A1.8."
#     The three runners under that header are run_weighted_voting (B1.2), run_majority_rules
#     (B1.3) and run_worst_n_of_m (B1.4).
#
#   `specifications/B1_signal_synthesis.md`, on exactly B1.2-B1.4:
#       "Three of the four (B1.2, B1.3, B1.4) read the four assembled arms the signal package
#        carries"
#       "Every other module this run computed is deliberately excluded. Those are not further
#        evidence; they are further transformations of these same four arms, and a
#        transformation retains the lineage of what produced it rather than becoming an
#        independent project fact."
#     A transformation of the arms is not an independent project fact, so it cannot be a voter
#     over the arms' own categories either -- that is the specification's own duplicate-lineage
#     rule applied one level up.
#
# B1.1 IS NOT IN THE SET AND IS NOT EXCLUDED. Its specification says "Unlike B1.2-B1.4 this
# module reads the assembled mapping directly", and "This module does emit a band". It stays.
#
# THE SET IS NOT EXTENDED. "ADVISORY_ONLY" alone establishes nothing narrower: `registry.
# activation_state` returns it for EVERY module not in CORE_VOTING_MODULES and not disabled, so
# reading that string as "excluded from its category" would empty every category on the page.
# The narrowing word in the tree is COMPARISON, and it names exactly these three.
#
# RUN 98. TRIMMED TO {B1.2}. B1.3 and B1.4 were removed from the registry at Run 97 and no
# longer resolve to anything: the roster is thirty modules and neither id is among them. A set
# naming two identifiers that do not exist cannot exclude them from a rollup they can never
# reach, and it made the set unreadable as a statement about the platform in service. B1.2 is
# unchanged and the RULE is unchanged -- what it names is now only what exists.
COMPARISON_ONLY_MODULES: frozenset[str] = frozenset({"B1.2"})


def admitted_to_category_rollup(module_id: str | None) -> bool:
    """Does this module's band set its category's status? Comparison ensembles do not."""
    return module_id not in COMPARISON_ONLY_MODULES


def category_statuses(readings: dict[str, SpecificationReading]) -> dict[str, dict[str, Any]]:
    """
    One entry per category THAT WAS CALLED. A category never called has no entry, and that is
    the whole of the order's proof 3.

    The entry keeps the field names the surfaces already read -- `status`, `group`,
    `contributes_to_project_status`, `status_set_by` -- and adds the reading's own `state`,
    `reason` and `missing_upstream` so a surface can say WHY a called category carries no band
    instead of leaving it blank.
    """
    groups = _category_groups()
    out: dict[str, dict[str, Any]] = {}
    for key in sa.ALL_CATEGORIES:
        stored = readings.get(key)
        if stored is None:
            continue
        mods = [m for m in (stored.modules or [])
                if isinstance(m, dict) and m.get("state") == sa.COMPUTED]
        bands = [(m.get("module_id"), _band(m.get("band"))) for m in mods
                 if admitted_to_category_rollup(m.get("module_id"))]
        # RUN 104. THE POSTURE RULE IS `category_posture`, not a rule written here, and it is
        # the SAME function the Python rollup and `spec_apply` call. ADMISSION is decided above
        # and is unchanged. A1, A2, A3 and A4 average their banded modules' scores; A6 takes the
        # worst; a category the owner did not assign keeps worst-wins. The arithmetic is carried
        # on the entry so the brief can show its working.
        posture = category_posture(key, [(mid, b) for mid, b in bands if b])
        fused = posture["status"]
        group = groups.get(key, "")
        out[key] = {
            "status": fused,
            "posture_rule": posture["posture_rule"],
            "posture_rule_words": posture["posture_rule_words"],
            "posture_rule_short": posture["posture_rule_short"],
            "posture_boundary": posture["posture_boundary"],
            "posture_arithmetic": posture["posture_arithmetic"],
            "posture_module_scores": posture["posture_module_scores"],
            "posture_banded_count": posture["posture_banded_count"],
            "posture_average": posture["posture_average"],
            # No belief-conflict coefficient is defined over a specification reading, and one is
            # not invented. 0.0 is what `governed_status_semantics` reads for "no disagreement
            # measured"; the state below is what a reader should judge the reading by.
            "conflict": 0.0,
            "group": group,
            "module_count": len(mods),
            # RUN 104. WHICH MODULES SET IT, as the rule that formed it defines "set". Under
            # worst-wins that is the modules holding the worst band; under averaging every
            # banded module set it, because there is no single setter in a mean.
            "status_set_by": posture["status_set_by"],
            "contributes_to_project_status": contributes_to_project_status(group),
            "state": stored.state,
            "reason": stored.reason,
            "missing_upstream": stored.missing_upstream or [],
            "counts": stored.counts or {},
            "reading_id": stored.reading_id,
            "served_by": stored.served_by,
            "source": "specification_reading",
        }
    return out


# ---------------------------------------------------------------------------------------------
# RUN 89, GOAL THREE. THE REQUIRED CORE, AND INDETERMINATE.
#
# RUN 95, SECTION 3.2, SUPERSEDES RUN 89's CORE OF FOUR. An OFFICIAL project status is issued
# only when ALL FIVE weighted performance categories -- A1, A2, A3, A4, A6 -- carry a posture.
# A4 Document Signals is now REQUIRED, not supporting. A5 Systems and Dynamics holds no module
# in service after Run 95's retirements and is not a category of this platform any more. There
# is NO SUPPORTING TIER LEFT: `SUPPORTING_CATEGORIES` is empty and the `supporting_*` keys
# publish `[]`, which is the true answer rather than a dead key. When any required category is
# not assessed, the official status is INDETERMINATE.
#
# THE PROJECT-LEVEL RULE IS NOT TOUCHED. `worst_band` over the CATEGORIES is still the only
# severity rule in this file and its arithmetic is not altered, not re-ordered and not consulted
# twice -- Run 104 changed how a CATEGORY forms its posture and nothing about how the project
# forms its status. The gate is a CONDITION LAYERED ON TOP of the fused band: when all five
# required categories carry a posture, this function returns EXACTLY what it returned before
# Run 89, byte for byte. That equality is
# measured, not argued, in `tools/test_run89_required_core.py`.
#
# "INDETERMINATE" IS NOT A BAND. It is deliberately NOT added to `fusion.BAND_SEVERITY` and it
# never enters `worst_band`, because it is not a severity and cannot be ranked against one. It is
# the answer to a different question -- may an official status be issued at all -- and it is
# produced only here, at the point where that question is asked.
#
# ONE DEFINITION, IMPORTED. The required and supporting sets live in `simulation/compute.py`
# beside the Python rollup that also applies them, and are imported here rather than restated,
# so the two status paths cannot drift about which categories are required. That is the failure
# this programme has already found nine times.
from .simulation.compute import (  # noqa: E402
    _COMPLETE as COMPLETE,
    delivery_complete,
    _INDETERMINATE as INDETERMINATE,
    _REQUIRED_CATEGORIES as REQUIRED_CATEGORIES,
    _SUPPORTING_CATEGORIES as SUPPORTING_CATEGORIES,
)


def required_core_missing(cats: dict[str, dict[str, Any]]) -> list[str]:
    """
    The required categories that carry NO posture, in the owner's stated order.

    NOT ASSESSED AND NEVER CALLED ARE BOTH MISSING HERE, and deliberately so: the question this
    answers is whether a posture EXISTS, and a category with no entry and a category with an
    entry carrying a null status are equally without one. They stay distinguishable everywhere
    else -- a category never called has no entry at all, which is Run 79's proof 3 -- and the
    reason string below names which of the two each missing category is.
    """
    return [k for k in REQUIRED_CATEGORIES if not (cats.get(k) or {}).get("status")]


def project_status_basis(cats: dict[str, dict[str, Any]],
                         signal_inputs: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Why the project status is what it is: the fused band, the gate's verdict, and the reason.

    Carried beside `project_status` so a surface can render the Indeterminate brief the owner
    specified without re-deriving the gate, and so nothing has to infer WHY from the word alone.

    RUN 99, THE COMPLETE PROMOTION. `signal_inputs` is the computed row's own figures and is
    OPTIONAL, so every existing caller that has no row to hand keeps its previous behaviour
    exactly: without figures nothing can be complete, and this function returns byte for byte
    what it returned before this run. The rule itself is NOT restated here -- it is
    `simulation.compute.delivery_complete`, imported above, for the same reason the required
    core is imported rather than restated: two status paths that each hold their own copy of a
    rule are two status paths that will disagree, and this programme has found that nine times.

    Complete is decided AHEAD of the required-core gate. The gate withholds an official RISK
    POSTURE when a required category carries none; completion is not a posture but a fact about
    delivery, and no unassessed category can make a finished project unfinished. Behind the
    gate the owner's three complete projects could never publish Complete at all.
    """
    missing = required_core_missing(cats)
    complete = delivery_complete(signal_inputs)
    fused = worst_band([c.get("status") for c in cats.values()
                        if c.get("status") and c.get("contributes_to_project_status")])
    detail = []
    for key in missing:
        entry = cats.get(key)
        detail.append({
            "category": key,
            # The two are different facts about the same absence and both are reported.
            "state": "never_called" if entry is None else (entry.get("state") or "not_assessed"),
            "missing": "no specification reading was stored for this category this period"
                       if entry is None else
                       (entry.get("reason")
                        or "the category was called and no module in it asserted a band"),
        })
    return {
        "required_categories": list(REQUIRED_CATEGORIES),
        "supporting_categories": list(SUPPORTING_CATEGORIES),
        "required_assessed": [k for k in REQUIRED_CATEGORIES if k not in missing],
        "required_missing": missing,
        "required_missing_detail": detail,
        "supporting_assessed": [k for k in SUPPORTING_CATEGORIES
                                if (cats.get(k) or {}).get("status")],
        "supporting_not_assessed": [k for k in SUPPORTING_CATEGORIES
                                    if not (cats.get(k) or {}).get("status")],
        # The band worst-wins produced over the contributing categories, WHETHER OR NOT the gate
        # lets it be official. It is reported either way so an Indeterminate brief can still show
        # every assessed category and any that are Red.
        "fused_band": fused,
        "official": complete or not missing,
        "delivery_complete": complete,
        "status": COMPLETE if complete else (INDETERMINATE if missing else fused),
    }


def project_status(cats: dict[str, dict[str, Any]],
                   signal_inputs: dict[str, Any] | None = None) -> str | None:
    """
    The official project status.

    When all four required categories carry a posture this is the worst contributing category's
    band, or None -- the same rule, the same arithmetic, one level up, unchanged by this run.
    When any required category carries none, it is INDETERMINATE, which is not a band and is not
    ranked against one.
    """
    return project_status_basis(cats, signal_inputs)["status"]


def projection(session: Session, project_id: str, period: int,
               signal_inputs: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    The three fields every surface reads, built from the specification readings alone.

    Returned even when there are NO readings: the fields are then an empty list, an empty map
    and None, which is what "this project has not been called" must look like on the wire.
    Nothing here consults `computed_results`.
    """
    readings = live_readings(session, project_id, period)
    cats = category_statuses(readings)
    return {
        "module_results": module_rows(readings),
        "abstained": abstention_rows(readings),
        "category_statuses": cats,
        "project_status": project_status(cats, signal_inputs),
        "project_status_basis": project_status_basis(cats, signal_inputs),
        "specification_categories_called": sorted(readings),
        "specification_reading_count": len(readings),
    }


def projections(session: Session, pairs: list[tuple[str, int]],
                inputs_by_project: dict[str, dict[str, Any]] | None = None
                ) -> dict[str, dict[str, Any]]:
    """
    The same projection for many (project_id, period) pairs, in ONE query.

    `facade.live_statuses` is a collection endpoint -- it exists because a per-project query
    there is paid on every portfolio load -- so the batched form is what it calls. Keyed by
    project id, because that is what the caller keys its map by and each project contributes
    exactly one period here.
    """
    if not pairs:
        return {}
    wanted = {(pid, int(per)) for pid, per in pairs}
    rows = session.scalars(
        select(SpecificationReading).where(
            SpecificationReading.project_id.in_({p for p, _ in wanted}),
            SpecificationReading.superseded_by.is_(None),
        ).order_by(SpecificationReading.created_at)
    ).all()
    per_project: dict[str, dict[str, SpecificationReading]] = {p: {} for p, _ in wanted}
    for r in rows:
        if (r.project_id, r.period) in wanted:
            per_project[r.project_id][r.category_key] = r
    out: dict[str, dict[str, Any]] = {}
    for pid, period in wanted:
        readings = per_project.get(pid) or {}
        cats = category_statuses(readings)
        si = (inputs_by_project or {}).get(pid)
        out[pid] = {
            "module_results": module_rows(readings),
            "abstained": abstention_rows(readings),
            "category_statuses": cats,
            "project_status": project_status(cats, si),
            "project_status_basis": project_status_basis(cats, si),
            "specification_categories_called": sorted(readings),
            "specification_reading_count": len(readings),
        }
    return out


# =============================================================================================
# RUN 102, GOAL ONE. THE PYTHON ROW FILLS AN ABSENCE, AND IT SAYS SO.
#
# WHAT WAS MEASURED FIRST, BEFORE ANYTHING WAS CHANGED (order section 2.1). `documents.
# _result_view` DID already have a fallback, and the briefing's "there is no fallback" is only
# half right: the fallback was ALL-OR-NOTHING ON WHETHER THE CALLER BUILT A PROJECTION AT ALL --
#
#     _spec_cats = spec["category_statuses"] if spec is not None else row.category_statuses
#
# -- and `a_projectresults` ALWAYS builds one. So `spec is not None` was true on every
# participant read, an EMPTY projection was taken in full, and `row.category_statuses` was never
# consulted. A row carrying four Python postures rendered as "0 of 5 carry a posture".
#
# WHY MIXING THE LAYERS IS COHERENT, AND THE ESCAPE CLAUSE IN SECTION 2 DOES NOT FIRE. The two
# layers are not two opinions about one quantity that would have to be averaged. They are two
# producers of the SAME shape:
#
#   * the unit of merge is a CATEGORY, and a category is taken WHOLE from one layer or the
#     other. No category's posture is ever formed from modules of both layers, so nothing is
#     averaged, reconciled or blended anywhere;
#   * both layers form a category posture by the SAME rule, `fusion.worst_band` over the bands
#     of the modules that computed -- `spec_projection.category_statuses` calls it and
#     `simulation.compute` calls it through `fuse_signals`. Conservative Dominance is untouched;
#   * both then hand those postures to the SAME required-core gate and the SAME project fusion,
#     which is `project_status_basis` below, called ONCE on the merged mapping.
#
# So a merged row is exactly what the platform would publish if the specification layer had been
# asked about only the categories it was asked about. That is filling an absence, not overriding
# a reading, and it is why the merge is per-category rather than per-field.
#
# THE FALLBACK IS NEVER SILENT (section 12.1). Every merged category carries `posture_layer` and
# `posture_layer_words`, every module row served from the Python layer carries the same two, and
# `merge_note` on the projection names which categories came from which layer. The decision
# brief prints it. A reader of one module reading can tell which layer produced it without
# consulting anything else.
#
# THE SPECIFICATION LAYER WINS WHERE IT HAS A READING (section 2.3), AND "HAS A READING" IS A
# MEASURED DISTINCTION RATHER THAN A GUESS AT ONE. `spec_apply` stores four states, and only two
# of them are a reading:
#
#   computed     -- the layer read the specification and produced module readings. A READING. It
#                   wins, and the fallback does not touch that category.
#   abstained    -- the layer read the specification and DECLINED, with its reason. ALSO A
#                   READING: a stated refusal is an answer, and replacing it with a Python
#                   posture would be OVERRIDING a reading rather than filling an absence, which
#                   section 12.2 fails the run for.
#   failed       -- "no recorded answer is held for category A1 on these figures ... and there
#                   is no API key". NOT A READING. It is the row recording that the layer could
#                   not be asked. Keyless, this is the state of EVERY category, which is
#                   precisely the condition the owner's ruling is about.
#   out_of_order -- "this category reads what the categories before it produced, and they have
#                   not run yet". NOT A READING either: a record that the question was not put.
#
# THIS WAS MEASURED BEFORE IT WAS IMPLEMENTED, NOT ASSUMED, AND THE FIRST BUILD WAS WRONG. That
# build tested only whether the specification layer had an ENTRY for the category. On the
# owner's own route, keyless, `projectcategoryapply` STORES an entry for all ten categories --
# state `failed`, served_by `recorded`, zero modules -- so that test found an entry everywhere
# and the fallback never fired: the rendered card still read "0 of the 5 required categories
# carry a posture" over a stored Python row carrying five Green ones. The distinction above is
# what that measurement forced, and it is recorded here rather than quietly corrected.
SPEC_STATES_THAT_ARE_A_READING: frozenset[str] = frozenset({sa.COMPUTED, sa.ABSTAINED})
# =============================================================================================

POSTURE_LAYER_SPEC = "specification_reading"
POSTURE_LAYER_PYTHON = "python_module_layer"

POSTURE_LAYER_WORDS: dict[str, str] = {
    POSTURE_LAYER_SPEC: ("read by the specification layer, from the module specification, and "
                         "stored as a specification reading"),
    POSTURE_LAYER_PYTHON: ("computed by the platform's own Python module layer and served here "
                           "because the specification layer holds no reading for this category "
                           "this period"),
}


def _python_category_of(entry: dict[str, Any], module_id: Any) -> str:
    """The category a stored Python row belongs to. Stated on the row, else its id's prefix."""
    cat = entry.get("category")
    if cat:
        return str(cat)
    return str(module_id or "").split(".")[0]


def merge_python_row(spec: dict[str, Any] | None,
                     row_module_results: Any,
                     row_abstained: Any,
                     row_category_statuses: Any,
                     signal_inputs: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    The specification projection, with the Python row filling the categories it has no reading
    for. Visibly. See the block above for why this is coherent and where it refuses to act.

    Returns the four fields `_result_view` publishes plus `project_status_basis` and the
    merge's own record of what came from where.
    """
    spec = spec or {"module_results": [], "abstained": [], "category_statuses": {},
                    "specification_categories_called": []}
    spec_cats = dict(spec.get("category_statuses") or {})
    row_cats = dict(row_category_statuses or {})

    # The specification layer's answer is authoritative for every category it ANSWERED. A
    # category whose stored state records that it could NOT be asked -- `failed`,
    # `out_of_order` -- has not answered, and is open to the fallback.
    answered = {k: e for k, e in spec_cats.items()
                if (e or {}).get("state") in SPEC_STATES_THAT_ARE_A_READING}
    unanswered = {k: e for k, e in spec_cats.items() if k not in answered}
    merged: dict[str, dict[str, Any]] = {}
    for key, entry in answered.items():
        e = dict(entry)
        e["posture_layer"] = POSTURE_LAYER_SPEC
        e["posture_layer_words"] = POSTURE_LAYER_WORDS[POSTURE_LAYER_SPEC]
        merged[key] = e
    filled: list[str] = []
    for key, entry in row_cats.items():
        if key in merged:
            continue                      # the specification layer answered; it wins. Section 2.3.
        e = dict(entry)
        e["posture_layer"] = POSTURE_LAYER_PYTHON
        e["posture_layer_words"] = POSTURE_LAYER_WORDS[POSTURE_LAYER_PYTHON]
        e["source"] = POSTURE_LAYER_PYTHON
        e["served_from_python_fallback"] = True
        # WHAT THE SPECIFICATION LAYER SAID INSTEAD, CARRIED ONTO THE ENTRY rather than
        # discarded. A reader of one category can see both that the Python layer produced this
        # posture and why the specification layer produced none.
        _un = unanswered.get(key)
        if _un:
            e["specification_layer_state"] = _un.get("state")
            e["specification_layer_reason"] = _un.get("reason")
        merged[key] = e
        filled.append(key)
    # A category the specification layer could not be asked about and for which the PYTHON row
    # also holds nothing keeps its unanswered entry, so the page still says why. Not dropped.
    for key, entry in unanswered.items():
        if key not in merged:
            merged[key] = dict(entry)
    filled.sort()

    # The module rows follow their category, so no category's evidence is split across layers.
    modules: list[dict[str, Any]] = [dict(m) for m in (spec.get("module_results") or [])]
    for m in modules:
        m.setdefault("posture_layer", POSTURE_LAYER_SPEC)
        m.setdefault("posture_layer_words", POSTURE_LAYER_WORDS[POSTURE_LAYER_SPEC])
    abstained: list[dict[str, Any]] = [dict(a) for a in (spec.get("abstained") or [])]
    if filled:
        wanted = set(filled)
        for m in (row_module_results or []):
            if not isinstance(m, dict):
                continue
            if _python_category_of(m, m.get("module_id")) in wanted:
                e = dict(m)
                e["source"] = POSTURE_LAYER_PYTHON
                e["posture_layer"] = POSTURE_LAYER_PYTHON
                e["posture_layer_words"] = POSTURE_LAYER_WORDS[POSTURE_LAYER_PYTHON]
                modules.append(e)
        for a in (row_abstained or []):
            if not isinstance(a, dict):
                continue
            if _python_category_of(a, a.get("module_id")) in wanted:
                e = dict(a)
                e["source"] = POSTURE_LAYER_PYTHON
                e["posture_layer"] = POSTURE_LAYER_PYTHON
                abstained.append(e)

    basis = project_status_basis(merged, signal_inputs)
    served_by_layer = {
        POSTURE_LAYER_SPEC: sorted(answered),
        POSTURE_LAYER_PYTHON: filled,
    }
    note = None
    if filled:
        note = ("The specification layer holds no reading for "
                + ", ".join(filled) + " this period, so "
                + ("that category's" if len(filled) == 1 else "those categories'")
                + " posture is served from the platform's own Python module layer and is "
                  "labelled as such on every reading it produced. Where the specification layer "
                  "does hold a reading it is the source and nothing replaces it.")
    return {
        "module_results": modules,
        "abstained": abstained,
        "category_statuses": merged,
        "project_status": basis["status"],
        "project_status_basis": basis,
        "specification_categories_called": sorted(spec_cats),
        "specification_reading_count": len(answered),
        "specification_categories_unanswered": sorted(unanswered),
        "posture_layers": served_by_layer,
        "python_fallback_categories": filled,
        "posture_layer_note": note,
    }
