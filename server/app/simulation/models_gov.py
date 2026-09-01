"""
Group B models: signal synthesis, evidence combination, governance thresholds, decision
optimization. Ported from assets/js/simulations.js, validated against the JavaScript executed in
a browser. See VALIDATION.md for the per-module comparison.

INPUT CONTRACTS — three shapes share the registry's one signature fn(si, rand, period_cutoff):

- B1.2–B1.4 (voting ensembles) consume the ASSEMBLED PROJECT: si["signals"] holding the primary
  signal package ({mc, cusum, doc} each with .status and {decision} with .state) and
  si["simulationSignals"]["signal_array"] holding per-module results with .status_color.
- B2.1 (DST) and B2.2–B2.9 consume the assembled signal keys directly from si: si["evm"]
  ({cpi, spi}), si["mc"] ({p80DeltaPct}), si["cusum"] ({breached}), si["doc"] ({score}) and,
  for DST's agreement field, si["decision"] ({state}). In the browser these arrive as
  `existingSignals`; on the server the caller assembles them into the same dict.
- B2.10–B2.20, B3.x and B4.x consume flat signalInputs (cpi/spi/docRiskScore/…), as Group A does.

Quirks reproduced deliberately (all validated):

- DST reads `existingSignals.doc ? doc.score : 0`. A PRESENT doc with an undefined score makes
  both `< 0.30` and `< 0.70` false in JavaScript, landing in the Red-evidence branch; an absent
  doc lands Green. Reproduced exactly. Every other module uses `doc.score || 0`.
- voteBucket maps anything containing "Red" to Red, exactly "Amber"/"Yellow" to themselves, and
  EVERYTHING else — including "light-amber" and "Complete" — to Green. Reproduced, not fixed.
- Tie directions differ by site: dstFuse's band reduce keeps the EARLIER state on ties, runDST's
  max-state reduce and the voting reduces keep the LATER one. Each is reproduced per-site.
- Neutrosophic/IntervalFuzzy/ZNumbers/PLTS/Plithogenic emit an AMBER stub (not an abstention)
  when no signal contributes — that is what the instrument has always done.
- MARCOS and Linear Programming can divide by zero in JavaScript yet still produce a FINITE
  score via Infinity arithmetic; `_jsdiv` reproduces that limit instead of refusing.
- FAR / OMB A-11 / EVM Reporting / What-If divide by cpi with no finite fallback: cpi exactly 0
  abstains per the standing NaN/Infinity rule.
- The Object.keys reductions in the voting modules iterate insertion order. DO NOT SORT.
"""

from __future__ import annotations

import math
from typing import Any, Callable

from .fusion import BAND_SEVERITY, dst_combine, normalise_status
from .arm_lineage import (  # noqa: F401  (re-exported for existing readers)
    ARM_LINEAGE_CUSUM, ARM_LINEAGE_DOC, ARM_LINEAGE_EVM, ARM_LINEAGE_MC,
)
from .lineage import evidence_bodies
from .models import (
    ABSTAIN_DECISION_STRUCTURE_ABSENT, ABSTAIN_MALFORMED_INPUT, PROVENANCE_OWNER_CALIBRATED,
    PROVENANCE_WORDS, THRESHOLD_SOURCE_OWNER, THRESHOLD_SOURCE_WORDS, check_inputs, insufficient,
)
from .project_posture import (
    PROJECT_CATEGORY_WEIGHTS, PROJECT_EXCLUDED_CATEGORIES,
    WEIGHT_PROVENANCE as PROJECT_WEIGHT_PROVENANCE, project_posture,
)
from .models_ext import _derived, _js_str
from .rng import js_round, round1, round2
from .signal_package import SIGNAL_QUALIFICATION

_round3 = lambda v: js_round(v * 1000) / 1000  # noqa: E731


def _jsdiv(a: float, b: float) -> float:
    """JavaScript division: x/0 is ±Infinity (NaN for 0/0), never an exception."""
    if b == 0:
        if a == 0:
            return float("nan")
        return math.inf if a > 0 else -math.inf
    return a / b


# ================================================================ B2.1 Dempster-Shafer
#
# RUN 20 CYCLE 7. THE FOUR ARMS ARE TWO BODIES OF EVIDENCE, AND UNTIL NOW THEY WERE COMBINED AS
# FOUR. Dempster's rule normalises by a conflict coefficient defined only for INDEPENDENT bodies,
# so combining several readings of one body is not a stronger reading of that body: it is the
# same evidence counted again. Measured on the shipped module, three adverse readings of the ONE
# earned-value body drove Red belief from 0.3974 to 0.9646. Nothing was learned in between.
#
# WHICH ARMS ARE WHICH, ESTABLISHED FROM WHAT EACH ARM ACTUALLY READS AND WHAT MATERIALLY MOVES
# IT -- never from module id proximity, category membership, shared field names or schema
# similarity, all four of which are refused by the owner's rule for this work:
#
#   the index arm      reads the cost and schedule indices, which are the earned value over the
#                      actual cost and over the planned value. EARNED-VALUE MEASUREMENT.
#   the forecast arm   reads A1.1's eightieth-percentile overrun, which is a Beta-PERT forecast
#                      off the budget, BOTH indices AND the document risk score, the last of
#                      which genuinely widens its spread. EARNED-VALUE MEASUREMENT AND DOCUMENT
#                      EVIDENCE BOTH: this arm is the bridge.
#   the trend arm      reads A1.2's breach flag over the schedule index history, and that history
#                      ENDS WITH THIS PERIOD's index, so it shares this period's earned value and
#                      planned value with the index arm and not merely older ones. EARNED-VALUE
#                      MEASUREMENT AND REPORTING HISTORY.
#   the document arm   reads the document risk score. DOCUMENT EVIDENCE.
#
# So the index arm and the document arm SHARE NOTHING, and the forecast arm bridges them. This is
# the A={X}, B={X,Y}, C={Y} case in shipped production code and not in a thought experiment, and
# it is why the separation must be the pairwise, non-transitive one: a closure would let the
# forecast arm marry the two bodies and destroy corroboration that is really there.
#
# AND THE VACUOUS ARM WAS EVIDENCE, WHICH IS THIS MODULE'S OWN D1 LESSON LEFT HALF-APPLIED. An
# absent arm used to contribute {0.25 x 4}. That is not ignorance -- ignorance is all mass on the
# frame -- it is an assertion that the four states are equally likely, and Dempster's rule is not
# neutral to it: the same evidence gave a different answer according to how many arms happened to
# be MISSING. The comment below already states the principle for the all-absent case ("the honest
# representation of no evidence is no combination"). It now holds for the partial case too: an
# absent arm contributes no body and no mass, and the all-absent refusal is unchanged.
#
# NO BAND, BOUNDARY, THRESHOLD OR ARM MASS IS CHANGED BY ANY OF THIS. What changed is which
# masses are combined against each other.

# RUN 20 CYCLE 9, ARCH.5. The four arm declarations MOVED to arm_lineage.py unchanged,
# because seven more registered modules read the same four arms and a second copy of a
# lineage declaration is a second thing that can drift. Re-exported here so every existing
# reader of `models_gov.ARM_LINEAGE_EVM` keeps working.

def _arm_band(mass: dict) -> str:
    """The band an arm's mass asserts, which is the state carrying most of it.

    Read off the mass rather than recorded beside it deliberately: an oracle and an
    implementation that both derive the expected condition from the same expression prove
    nothing, so the arm's band is not stored at the branch that chose the mass and then compared
    against itself. Ties keep the more adverse state, matching the module's own reduce below.
    """
    best = "Green"
    for b in ("Amber", "Red"):
        if mass.get(b, 0.0) >= mass.get(best, 0.0):
            best = b
    return best


def run_dst(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    ex = si
    sources: list[dict] = []
    # One lineage record per PRESENT arm, in the module's own evaluation order. The records carry
    # the primitive facts established above; the framework in lineage.py, which knows nothing
    # about this module, does the separating.
    arm_records: list[dict] = []
    arm_masses: list[dict] = []

    # Presence checks are `is not None`, not Python truthiness: a JS empty object {} is truthy,
    # so an empty mc/cusum/doc still takes the signal-present branch there.
    evm = ex.get("evm")
    cpi = evm.get("cpi") if evm is not None else None
    spi = evm.get("spi") if evm is not None else None

    # D1. With none of the four signals present, the three vacuous {0.25 × 4} masses below
    # combined to nothing while the doc arm's `absent -> score 0 -> Green` branch supplied a
    # real Green mass, so the fusion returned Green on every project the server computed. This
    # is Dempster-Shafer: the honest representation of no evidence is no combination, not a
    # combination of ignorance with one asserted belief.
    if not (cpi and spi) and ex.get("mc") is None and ex.get("cusum") is None \
            and ex.get("doc") is None:
        return insufficient("DST_Evidence_Combination")

    def arm(record: dict, mass: dict) -> None:
        arm_records.append(record)
        arm_masses.append(mass)

    if cpi and spi:
        evm_min = min(cpi, spi)
        if evm_min >= 0.95:
            m = {"Green": 0.80, "Amber": 0.10, "Red": 0.05, "Unknown": 0.05}
        elif evm_min >= 0.90:
            m = {"Green": 0.10, "Amber": 0.70, "Red": 0.15, "Unknown": 0.05}
        else:
            m = {"Green": 0.05, "Amber": 0.15, "Red": 0.75, "Unknown": 0.05}
        arm(ARM_LINEAGE_EVM, m)

    mc = ex.get("mc")
    if mc is not None:
        p80 = mc.get("p80DeltaPct") or 0
        if p80 <= 5:
            m = {"Green": 0.75, "Amber": 0.15, "Red": 0.05, "Unknown": 0.05}
        elif p80 <= 10:
            m = {"Green": 0.10, "Amber": 0.65, "Red": 0.20, "Unknown": 0.05}
        else:
            m = {"Green": 0.05, "Amber": 0.10, "Red": 0.80, "Unknown": 0.05}
        arm(ARM_LINEAGE_MC, m)

    cusum = ex.get("cusum")
    if cusum is not None:
        if not cusum.get("breached"):
            m = {"Green": 0.75, "Amber": 0.15, "Red": 0.05, "Unknown": 0.05}
        else:
            m = {"Green": 0.05, "Amber": 0.15, "Red": 0.75, "Unknown": 0.05}
        arm(ARM_LINEAGE_CUSUM, m)

    doc = ex.get("doc")
    # JS: `doc ? doc.score : 0` — a present doc with an undefined score makes both comparisons
    # below false and lands in the Red branch. Absent doc -> 0 -> Green.
    #
    # RUN 20 CYCLE 7. The absent-doc branch is kept exactly as it was: an absent document arm
    # still reads as score 0 and still contributes the Green evidence mass. That is a QUIRK OF
    # THIS MODULE, validated against the instrument and reproduced deliberately, and it is not
    # this cycle's defect to correct. It is called out here so no reader mistakes it for the
    # vacuous-arm treatment above, which is a different thing and was.
    doc_score = (doc.get("score") if doc is not None else 0)
    if doc_score is not None and doc_score < 0.30:
        m = {"Green": 0.75, "Amber": 0.15, "Red": 0.05, "Unknown": 0.05}
    elif doc_score is not None and doc_score < 0.70:
        m = {"Green": 0.10, "Amber": 0.70, "Red": 0.15, "Unknown": 0.05}
    else:
        m = {"Green": 0.05, "Amber": 0.15, "Red": 0.75, "Unknown": 0.05}
    arm(ARM_LINEAGE_DOC, m)

    # ---- THE SEPARATION, AND THE TWO OPERATORS.
    #
    # ACROSS bodies Dempster's rule applies unchanged, because the independence it assumes is now
    # true by construction. WITHIN a body the question is not whether the readings agree -- one
    # body cannot agree with itself -- but what that body says when it is read in more than one
    # way, and the answer taken is the MOST ADVERSE of those readings. That operator is
    # IDEMPOTENT, which is the property the defect required: a second and a third reading of one
    # body change nothing at all. It is a governance choice and carries no weight, no correlation
    # estimate and no tuned parameter, and it is the same operator fusion.fuse_signals already
    # applies for the same reason.
    #
    # Ties within a body keep the EARLIEST arm in the module's own evaluation order. That is
    # declared, deterministic, and deliberately NOT a choice between readings by which of them
    # gives the more or less adverse fused answer: choosing by the answer is the
    # boundary-moved-to-fit-an-example failure this programme refuses.
    separation = evidence_bodies(arm_records)
    body_summary = []
    for group in separation["bodies"]:
        members = sorted(group)                 # the module's own evaluation order
        worst = max(BAND_SEVERITY.get(_arm_band(arm_masses[i]), -1) for i in members)
        pick = next(i for i in members
                    if BAND_SEVERITY.get(_arm_band(arm_masses[i]), -1) == worst)
        sources.append(arm_masses[pick])
        body_summary.append({
            "representative_module_id": arm_records[pick]["module_id"],
            "member_module_ids": [arm_records[i]["module_id"] for i in members],
            "member_bands": [_arm_band(arm_masses[i]) for i in members],
            "primitive_source_ids": sorted(separation["primitive_sources"][pick]),
            "disagreement": len({_arm_band(arm_masses[i]) for i in members}) > 1,
        })

    result = dict(sources[0])
    for s in sources[1:]:
        result = dst_combine(result, s)

    # JS reduce with `>` keeps the LATER state on ties.
    max_state = "Green"
    for b in ("Amber", "Red"):
        max_state = max_state if result[max_state] > result[b] else b

    decision = ex.get("decision")
    conservative = decision.get("state") if decision is not None else None
    # JS `a && expr`: null when conservative is null/'' — not False.
    agrees = (max_state.lower() == conservative.lower()) if conservative else conservative
    conflict = result.get("conflict", 0.0)
    conflict_level = "High" if conflict > 0.3 else ("Moderate" if conflict > 0.1 else "Low")
    status = "Red" if max_state == "Red" else ("Amber" if max_state == "Amber" else "Green")

    # RUN 20 CYCLE 7. WITH ONE BODY THERE IS NOTHING FOR THE CONFLICT COEFFICIENT TO MEASURE, and
    # a zero is not manufactured into a claim. The number is still reported for every caller that
    # has always read it; what is added is whether it means anything, which nobody could tell
    # before.
    conflict_estimable = len(sources) >= 2
    if not conflict_estimable:
        conflict_level = None

    return {
        "method_class": "DST_Evidence_Combination",
        "evidence_bodies": len(sources),
        "conflict_estimable": conflict_estimable,
        "lineage_bodies": body_summary,
        "body_selection_exact": separation["selection_exact"],
        "status_color": status,
        "belief_green": round2(result["Green"]),
        "belief_amber": round2(result["Amber"]),
        "belief_red": round2(result["Red"]),
        "belief_unknown": round2(result["Unknown"]),
        "conflict_mass": round2(conflict),
        "conflict_level": conflict_level,
        "agrees_with_conservative": agrees,
        "conservative_state": conservative,
        "evidence_metric": (
            f"Belief: Green {int(js_round(result['Green'] * 100))}% · "
            f"Amber {int(js_round(result['Amber'] * 100))}% · "
            f"Red {int(js_round(result['Red'] * 100))}% · "
            + (f"Conflict mass {int(js_round(conflict * 100))}%" if conflict_estimable
               else "Conflict: not estimable from one body of evidence")
        ),
    }


# ================================================================ B1 voting ensembles


def _vote_bucket(status) -> str | None:
    """
    Bucket one status onto a band, or None to cast no vote at all.

    THE FIFTEEN DEFECTS, defect 1, extended to the three voting ensembles per the adapter run's
    incidental finding 2. This function used to match `"Red" in status` and then EXACTLY "Amber"
    or EXACTLY "Yellow", with a final `else Green`. Every one of those tests is case-sensitive
    and capitalised, while the assembled primary signals these three ensembles read arrive in
    LOWERCASE from the instrument's own assembler. So `red` was not Red, `light-amber` was not
    Amber, and an unrecognised value was not refused: all three landed in the final else and
    voted GREEN. The forecast, the control chart and the document risk signals therefore voted
    green on every project regardless of what they said.

    Two changes, and they are separate. Matching now runs through the shared vocabulary, so
    casing cannot decide a vote. And an unrecognised value now casts NO VOTE rather than a Green
    one, because a value this platform does not recognise is not evidence that a project is well.
    """
    return normalise_status(status)


# ---------------------------------------------------------------------------------------------
# RUN 30, v15. THE THREE COMPARISON ENSEMBLES NOW SYNTHESISE GOVERNED SIGNALS.
#
# WHAT CHANGED AND WHY, stated once for all three because it is one change.
#
# The v14 ensembles voted the three primary signals PLUS every entry of
# `simulationSignals.signal_array` -- every other module this run had already computed. Those
# entries are not further evidence about the project. They are further TRANSFORMATIONS of the
# same four assembled arms, and a transformation retains the lineage of what produced it. Voting
# them made the COUNT OF REGISTERED MODULES an input to the answer:
#
#   * Worst-N-of-M compared a red COUNT against `ceil(0.3 * M)` where M grew with the array, so
#     Run 27 measured identical adverse evidence reading RED beside a three-module array and
#     YELLOW beside a sixty-three-module array. Registering a module diluted the evidence.
#   * Weighted Voting gave every array entry a 0.6 weight taken from a literal in this file with
#     no provenance anywhere, so the same duplication decided the winner.
#   * Majority Rules counted each transformation as a separate voter.
#
# The v15 rule is the contract's: synthesise the governed signals, one per independent body of
# evidence, with duplicate lineage collapsed. `canonical_v5.governed_signals_from_project` builds
# them from the arms the signal package already carries and the lineage `arm_lineage` already
# declares. NOTHING IS WEIGHTED, DISCOUNTED OR TUNED to compensate for the removal.
#
# Weighted Voting now requires a GOVERNED WEIGHTING POLICY and abstains without one, because the
# four literals it used had no authority behind them and section 14 forbids inventing weights.
# Its scientific disposition was already PARAMETER_PROVENANCE_BLOCKED; the code now says so.
#
# Worst-N-of-M is the frozen Worst-2 MEAN statistic and asserts NO traffic-light boundary,
# because the contract forbids inventing one and Run 33 owns the mapping.
#
# All three remain ADVISORY_ONLY and non-voting. Voting is exactly A1.7 and A1.8.
# ---------------------------------------------------------------------------------------------

def _governed(si, period_cutoff):
    from .canonical_v5 import governed_signals_from_project
    return governed_signals_from_project(si or {}, period_cutoff)


def _synthesis_lineage(out: dict) -> dict[str, Any]:
    """The audit trail every one of the three carries, so a reader can see what was synthesised
    and what was set aside as the same evidence read twice."""
    return {
        "duplicate_lineage_suppressed": out.get("duplicate_lineage_suppressed", []),
        "abstaining_signals": [
            {"signal_id": s["signal_id"], "reason": s.get("abstention_reason")}
            for s in out.get("abstaining", [])],
        "signal_qualification": SIGNAL_QUALIFICATION,
        "synthesis_role": "comparison and sensitivity regime; not an independent project fact "
                          "and not a voter",
    }


# ---------------------------------------------------------------------------------------------
# RUN 89, GOAL ONE. WEIGHTED VOTING READS THE SIX PERFORMANCE CATEGORY POSTURES.
#
# WHAT WAS WRONG. Run 88 established that this module weighed the four assembled arms -- `evm`,
# `mc`, `cusum`, `doc`. Two of the four trace to modules the owner has dropped: `mc` to the Monte
# Carlo EAC forecast retired at Run 43, and `doc` to the Document Risk Score, whose specification
# carries "STOPPED. Not specified." Half of what the retained synthesiser weighed came from
# outside the retained roster.
#
# THE OWNER'S RULING, RUN 89 SECTION 2. Weighted Voting reads the SIX PERFORMANCE CATEGORY
# POSTURES, not the arms. The weight set below is THE OWNER'S STATED AUTHORITY -- his decision,
# recorded as such. It is NOT derived, NOT taken from any literature and NOT calibrated.
#
# DATA INTEGRITY (C1) IS NOT IN THIS PROFILE AND MUST NEVER BE ADDED TO IT. Integrity is a
# precondition for using the criteria, not a criterion to trade against performance. The guard
# below is executable, not a comment.
#
# THE ARMS ARE NOT DELETED. `arm_lineage.py`, `canonical_v5.governed_signals_from_project`,
# `signal_package.py` and `models_evc.py` (which serves B2.2-B2.9, Evidence Combination) still
# read them, and B1.3 and B1.4 still synthesise them. Only THIS module's input path changed.
#
# THE ORDERING PROBLEM, AND HOW IT IS ANSWERED. Category postures do not exist at module dispatch
# -- they are the rollup of the modules that dispatch produces. So B1.2 is computed in a SECOND
# PASS, after the rollup, by `weighted_category_vote` below, called from `compute.compute_project`.
# It remains a module with a registry row, a method class and a specification; what moved is WHEN
# in the run it is evaluated. A second-pass module is also structurally incapable of reaching the
# category rollup that produced its own input, which is the same conclusion Run 87 reached by
# admission and is why B1.2 stays excluded from the category rollup.
#
# RUN 106, GOAL ONE. B1.2 STOPS BEING A COMPARISON ENSEMBLE AND BECOMES THE STATUS RULE, AND
# THE ARITHMETIC IT USED TO PUBLISH IS RETIRED RATHER THAN KEPT BESIDE THE NEW ONE.
#
#   WHAT IT DID. `weighted_category_vote` computed a PLURALITY OF WEIGHT: it summed the
#   renormalised weights that landed on each band CLASS and named the class holding the most.
#   That is a different rule from the owner's, and on many postures it gives a different answer
#   -- {A1 Green .28, A2 Green .28, A3 Red .17, A4 Red .11, A6 Red .16} is Green by plurality
#   of weight (0.56 Green against 0.44 Red) and Amber by the owner's scored sum (+0.32). A
#   module named "Weighted Voting" that disagreed with the weighted vote that sets the status
#   would be the same defect Run 104 measured one level down.
#
#   WHERE THE RULE LIVES, AND WHY NOT HERE. The project rule is `simulation.project_posture`,
#   called by BOTH status paths. It is not computed here, for a reason the platform has already
#   paid for once: a module row is dispatch machinery. It can be retired, disabled or fail
#   qualification, and a project status that existed only where a module runner returned it
#   would vanish with it -- and it would exist on the Python rollup path while the specification
#   projection, which dispatches no modules at all, had nothing to read. So the rule lives in one
#   pure function, and B1.2 REPORTS it: its reading is now the project rule's own band and its
#   own working, and it can no longer disagree with the status it is named for.
#
#   THE PLURALITY FIGURES ARE STILL PUBLISHED ON THE ROW, under `class_votes`, because they are
#   a real measurement of how the weight is distributed across bands and a reviewer may want it.
#   They no longer decide anything.
# ---------------------------------------------------------------------------------------------

#: RUN 106. ONE COPY OF THE WEIGHT PROFILE, AND IT IS NOT HERE ANY MORE.
#:
#: These five numbers were B1.2's own profile from Run 89 to Run 105 (restated at Run 95 section
#: 3 when A5 Systems and Dynamics lost every module it held). At Run 106 the owner gave them
#: PROJECT-LEVEL AUTHORITY: they decide the project status. So they moved to
#: `simulation.project_posture`, where the project rule lives, and are IMPORTED here under the
#: names this file has always used. A second copy beside the first is a thing that can drift,
#: and a drifted weight profile would mean the module called Weighted Voting and the status the
#: weighted vote sets disagree -- exactly the class of defect Run 104 closed one level down.
WEIGHTED_VOTING_CATEGORY_WEIGHTS = PROJECT_CATEGORY_WEIGHTS
WEIGHTED_VOTING_EXCLUDED_CATEGORIES = PROJECT_EXCLUDED_CATEGORIES
WEIGHT_PROVENANCE = PROJECT_WEIGHT_PROVENANCE



def weighted_category_vote(category_statuses: dict) -> dict[str, Any]:
    """
    B1.2, second pass. THE OWNER'S WEIGHTED VOTE OVER THE FIVE CATEGORY POSTURES.

    RUN 106. THE ARITHMETIC IS `simulation.project_posture.project_posture` AND NOTHING IS
    RECOMPUTED HERE. That function is the project status rule; this module reports it, so the
    module named Weighted Voting and the status the weighted vote sets are the same number by
    construction rather than by agreement.

    THE RULE FOR A CATEGORY WITH NO POSTURE is unchanged and is stated where the arithmetic is:
    an unassessed category is REMOVED FROM THE DENOMINATOR and the remaining weights are
    renormalised. `specifications/B1_signal_synthesis.md` shared rule 3 already states it --
    "an abstaining signal casts no vote, CARRIES NO WEIGHT" -- and carrying no weight is not the
    same as carrying weight toward zero. Zero is never used: on the -2..+2 scale it would sit
    between Yellow and Amber and read as a measured middling assessment.

    WITH NO WEIGHTED CATEGORY ASSESSED AT ALL there is nothing to weigh and the module abstains,
    naming the postures. It does not report a state in place of one.

    `class_votes` -- the share of the renormalised weight sitting on each band class -- is still
    computed and still published. Since Run 106 it DECIDES NOTHING; it is a distribution a
    reviewer may read beside the sum.
    """
    assert not (set(WEIGHTED_VOTING_CATEGORY_WEIGHTS) & WEIGHTED_VOTING_EXCLUDED_CATEGORIES), \
        "Data Integrity is a precondition for using the criteria, not a criterion in them."
    cats = category_statuses if isinstance(category_statuses, dict) else {}
    posture = project_posture(cats)
    present = {c["category"]: c["band"] for c in posture["category_scores"]}
    unassessed = list(posture["unassessed_categories"])
    if not present:
        return {"estimable": False, "unassessed_categories": unassessed,
                "reason": "none of the five weighted performance categories carries a posture, so "
                          "there is nothing to weigh and no weighted vote is reported"}
    weights = {c["category"]: c["normalised_weight"] for c in posture["category_scores"]}
    votes = {c: 0.0 for c in BAND_SEVERITY}
    for key, band in present.items():
        votes[band] = votes.get(band, 0.0) + weights[key]
    return {
        "estimable": True,
        "status": posture["status"],
        "weighted_sum": posture["weighted_sum"],
        "category_scores": posture["category_scores"],
        "project_arithmetic": posture["project_arithmetic"],
        "project_boundary": posture["project_boundary"],
        "votes": votes,
        "normalised_weights": weights,
        "assessed_categories": posture["assessed_categories"],
        "unassessed_categories": unassessed,
        "renormalised": posture["renormalised"],
        "weight_provenance": posture["weight_provenance"],
    }


#: The dispatch-time abstention. Its reason is ABOUT THE POSTURES, per Run 89 section 2.1.
WEIGHTED_VOTING_DEFERRED = (
    "Weighted Voting reads the six performance category postures. Those postures are the rollup "
    "of the modules this run dispatches, so they do not exist yet at module dispatch; this "
    "module is evaluated in the second pass, after the category rollup.")


def run_weighted_voting(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    B1.2 at DISPATCH. Reads nothing and abstains, naming the postures as what it is waiting for.

    The four-arm input path is gone: this function no longer calls `_governed`, no longer reads
    `signalWeightPolicy`, and no longer reaches `canonical_v5.weighted_voting`. The reading is
    produced by `weighted_category_vote` above, in `compute.compute_project`'s second pass.
    """
    return dict(insufficient("Weighted_Voting"), abstention_reason=WEIGHTED_VOTING_DEFERRED)


def weighted_voting_result(category_statuses: dict) -> dict[str, Any]:
    """
    The B1.2 module row for the second pass: a reading, or the abstention it states.

    RUN 106. `status_color` IS THE PROJECT RULE'S OWN BAND. Before this run it was the band
    class holding a plurality of the weight, which is a different quantity; see the header above
    for the measured case where the two disagree.

    NO BAND PROVENANCE IS ASSERTED AND NONE IS INVENTED. This row does not go through `banded()`
    because its boundary is not a threshold over a measured quantity -- it is the owner's stated
    project rule, published verbatim in `band_boundary` with `OWNER-CALIBRATED` provenance and
    the `owner_configured_default` threshold source, which is the same treatment every other
    owner-stated tolerance in this tree receives.
    """
    out = weighted_category_vote(category_statuses)
    if not out.get("estimable"):
        return dict(insufficient("Weighted_Voting"), abstention_reason=out.get("reason"),
                    unassessed_categories=out.get("unassessed_categories", []))
    return {
        "method_class": "Weighted_Voting",
        "status_color": out["status"],
        "weighted_sum": out["weighted_sum"],
        "category_scores": out["category_scores"],
        "project_arithmetic": out["project_arithmetic"],
        "band_boundary": out["project_boundary"],
        "band_basis": ("the owner's Run 106 ruling, section 1: the project status is the "
                       "weighted vote over the five category postures on his weight profile"),
        "band_basis_id": "owner_configured_project_weighted_vote_profile",
        "band_provenance_class": PROVENANCE_OWNER_CALIBRATED,
        "band_provenance_words": PROVENANCE_WORDS[PROVENANCE_OWNER_CALIBRATED],
        "threshold_source": THRESHOLD_SOURCE_OWNER,
        "threshold_source_words": THRESHOLD_SOURCE_WORDS[THRESHOLD_SOURCE_OWNER],
        # NOT `votes`. RUN 89 MEASURED A REAL COLLISION: `registry.run_all` sets a BOOLEAN
        # `votes` on every computed row -- "is this module one of the CORE_VOTING_MODULES" --
        # and this module's class-weight distribution was landing on the same key, so a truthy
        # dict made B1.2 read as a voter on the stored row. The distribution keeps its own name.
        # (The collision was latent before this run only because B1.2 never computed.)
        "class_votes": out["votes"],
        "normalised_weights": out["normalised_weights"],
        "weight_provenance": out["weight_provenance"],
        "assessed_categories": out["assessed_categories"],
        "unassessed_categories": out["unassessed_categories"],
        "renormalised": out["renormalised"],
        "lineage": {
            "signal_qualification": SIGNAL_QUALIFICATION,
            # RUN 106. It is no longer a comparison regime. It is a RESTATEMENT of the project
            # rule, and it is still not an independent project fact and still not admitted to
            # its own category's rollup -- it is derived from that rollup.
            "synthesis_role": "restates the project status rule; derived from the category "
                              "rollup and therefore not evidence within it, and not a voter",
        },
        "evidence_metric": (
            f"Weighted vote over {len(out['assessed_categories'])} of the five weighted "
            f"performance categories: weighted sum {out['weighted_sum']:+.4g}, "
            f"{out['status']}"),
    }


def run_majority_rules(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    from .canonical import StructureAbsent
    from .canonical_v5 import SignalNotEligible, majority_rules
    try:
        out = majority_rules(_governed(si, period_cutoff))
    except (SignalNotEligible, StructureAbsent) as exc:
        return dict(insufficient("Majority_Rules"), abstention_reason=str(exc))
    if not out.get("estimable"):
        return dict(insufficient("Majority_Rules"), abstention_reason=out.get("reason"))
    counts = out["counts"]
    return {
        "method_class": "Majority_Rules",
        "status_color": out["winner"],
        "counts": counts,
        "total_votes": out["voters"],
        "quorum": out["quorum"],
        "unique_winner": out["unique_winner"],
        "tied_classes": out["tied_classes"],
        "conflict": out["conflict"],
        "lineage": _synthesis_lineage(out),
        "evidence_metric": (
            f"{out['winner']} by majority ({counts[out['winner']]} of {out['voters']} "
            f"independent signals)" if out["unique_winner"]
            else "No single state holds a majority of the independent signals"),
    }


def run_worst_n_of_m(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    from .canonical import StructureAbsent
    from .canonical_v5 import SignalNotEligible, worst_two_of_m
    try:
        out = worst_two_of_m(_governed(si, period_cutoff))
    except (SignalNotEligible, StructureAbsent) as exc:
        return dict(insufficient("Worst_N_of_M"), abstention_reason=str(exc))
    if not out.get("estimable"):
        return dict(insufficient("Worst_N_of_M"), abstention_reason=out.get("reason"))
    a, b = out["selected"]
    return {
        "method_class": "Worst_N_of_M",
        # NO BAND. The statistic has no calibrated boundaries and none is invented here.
        "status_color": None,
        "mean_worst_2": out["mean_worst_2"],
        "selected_signals": out["selected"],
        "independent_signals": out["m"],
        "classification": out["classification"],
        "calibration_pending": out["classification_blocked"],
        "lineage": _synthesis_lineage(out),
        "evidence_metric": (
            f"Worst two of {out['m']} independent signals: {a['status']} and {b['status']}, "
            f"mean severity {out['mean_worst_2']:g} (of a possible 3)"),
    }


# ================================================================ B3 governance thresholds


def run_far_threshold(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 11, NEIGHBOUR DEFECT 7 OF 7. OUT-OF-DOMAIN BANDING.

    The reproducer from the Run 10B sweep: a cost performance index of -0.857 turned Amber into
    Green. The forecast at completion is the budget divided by the index, so a negative index
    produces a negative forecast, hence a negative overrun, hence the calmest band and a printed
    headroom against the reporting threshold that the project does not have. The zero case was
    already refused for the division; the negative half of the same domain was left open.

    THE DOMAIN. The cost performance index is earned value over actual cost and is a ratio of two
    quantities that cannot be negative, so it cannot be at or below zero. The budget at
    completion is an authorised amount and cannot be below zero. This is the same domain the
    variance-at-completion module states for the same field. The threshold, the band and the
    reporting rule are untouched.

    RUN 20 CYCLE 2, P0C GOVERNANCE AND REGULATORY OVERCLAIM.

    The reader was shown "FAR Part 34: 17.6% overrun, threshold 25% (REPORTING REQUIRED)". Two
    separate overclaims sat in that one sentence.

    First, the twenty-five. FAR 34.201 establishes earned value management POLICY and
    applicability: an earned value management system is required for major acquisitions for
    development in accordance with OMB Circular A-11, agencies may require one for other
    acquisitions under agency procedures, and contracting officers shall as a minimum require
    monthly reports on contracts to which it applies. It states no numeric cost-overrun
    threshold of any kind, and none was cited anywhere in this module. The number is an internal
    review level. It is now named as one, with its provenance stated on the result, and the
    regulation's name and part number are gone from the sentence. The number itself is NOT
    changed and no substitute regulatory threshold is introduced, because none exists to
    introduce.

    Second, "REPORTING REQUIRED". A reporting obligation follows from applicability, which this
    module does not determine and has none of the evidence for: no acquisition designation, no
    agency, no agency procedure, no contract clause, no award date, no rule version. Asserting
    the obligation from a cost ratio is the governance overclaim specification section 17
    prohibits in terms. The result now records regulatory_determination NOT_MADE and says so.

    The arithmetic, the domain guards and the band are untouched. Authority basis is the
    committed REGULATORY_SNAPSHOT_2026-08-12, corroborated on the text of 34.201 by web search;
    the official acquisition.gov and eCFR hosts are refused by this container's egress proxy, so
    no primary document is claimed to have been read. Nothing here is described as current law.
    """
    if not check_inputs(si, ("bac", "cpi", "ev", "ac")):
        return insufficient("FAR_Threshold")
    if si["cpi"] <= 0:
        return insufficient(
            "FAR_Threshold",
            "No overrun against the reporting threshold is measurable: the cost performance "
            "index is reported at or below zero, and the forecast at completion is the budget "
            "divided by that index. No substitute figure is used in its place.",
            ABSTAIN_MALFORMED_INPUT)
    if si["bac"] <= 0:
        return insufficient(
            "FAR_Threshold",
            "No overrun against the reporting threshold is measurable: the budget at completion "
            "is reported at or below zero, and the overrun is expressed as a share of it. No "
            "substitute figure is used in its place.",
            ABSTAIN_MALFORMED_INPUT)
    eac = si["bac"] / si["cpi"]
    overrun = ((eac - si["bac"]) / si["bac"]) * 100
    threshold = 25
    headroom = threshold - overrun
    color = ("Green" if overrun <= 5 else "Yellow" if overrun <= 15
             else "Amber" if overrun <= 25 else "Red")
    return {
        "method_class": "FAR_Threshold",
        "status_color": color,
        "overrun_pct": round1(overrun),
        "review_threshold_pct": threshold,
        "threshold_provenance": "UNCITED_INTERNAL_REVIEW_LEVEL",
        "distance_to_threshold": round1(headroom),
        "exceeds_review_threshold": overrun >= threshold,
        "regulatory_determination": "NOT_MADE",
        "evidence_metric": (
            f"{_js_str(round1(overrun))}% forecast overrun against an internal review level of "
            f"{threshold}%, which no regulation states ("
            + ("above the review level" if overrun >= threshold
               else f"{_js_str(round1(headroom))}% headroom") + "). "
            "Whether earned value management applies, and whether any report is due, is not "
            "determined here."
        ),
    }


def run_omb_a11_check(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    RUN 20 CYCLE 2, P0C GOVERNANCE AND REGULATORY OVERCLAIM.

    The reader was shown "OMB A-11: CPI 0.85: MANDATORY REPORTING TRIGGERED" whenever the cost
    index fell below 0.90 on a budget of ten million or more. That sentence asserts a legal
    obligation under a named federal circular on the strength of two uncited literals.

    Specification section 17, 8.3, states in terms that OMB Circular A-11 must NOT be reduced to
    budget, cost-index and progress thresholds, and that is precisely what the check is. Nothing
    the circular requires is represented here: no rule identifier, no section or appendix, no
    applicability, no required evidence, no result per requirement, no reviewer, and no edition.
    A check that evaluates none of a circular's requirements cannot conclude that the circular
    obliges anything.

    What is removed is the conclusion, not the observation. The two conditions are real
    observations about the project and remain, renamed for what they are: a cost index below an
    internal review level, and a budget at or above an internal size level. The result records
    regulatory_determination NOT_MADE and the sentence states that no requirement of the
    circular was evaluated. The conjunction, the boundaries and the band are untouched, and no
    substitute regulatory threshold is introduced.

    Representing the circular's configured requirements properly, with sections, applicability,
    required evidence and the edition dated 2025-08-29 that the committed snapshot carries, is
    the P2 work the register records for this module. It is not attempted here, and the module
    does not pretend to have done it.
    """
    if not check_inputs(si, ("bac", "cpi", "actualPctComplete")):
        return insufficient("OMB_A11_Check")
    if si["cpi"] == 0:
        return insufficient("OMB_A11_Check")  # JS Infinity; refused
    cpi_below = si["cpi"] < 0.90
    major = si["bac"] >= 10000000
    triggered = cpi_below and major
    eac = si["bac"] / si["cpi"]
    overrun = eac - si["bac"]
    color = ("Green" if not cpi_below else "Yellow" if si["cpi"] >= 0.92
             else "Amber" if si["cpi"] >= 0.88 else "Red")
    return {
        "method_class": "OMB_A11_Check",
        "status_color": color,
        "cpi_below_90": cpi_below,
        "large_budget": major,
        "review_condition_met": triggered,
        "threshold_provenance": "UNCITED_INTERNAL_REVIEW_LEVEL",
        "regulatory_determination": "NOT_MADE",
        "projected_overrun": int(js_round(overrun)),
        "evidence_metric": (
            f"Cost index {_js_str(si['cpi'])}"
            + (", below the internal review level of 0.90 on a budget of ten million or more, "
               "which is an internal review condition and not a reporting obligation"
               if triggered
               else ", below the internal review level of 0.90" if cpi_below
               else ", at or above the internal review level of 0.90")
            + ". No requirement of the circular is evaluated here, so no conformance finding is "
              "made."
        ),
    }


def run_evm_reporting_threshold(si: dict, rand: Callable[[], float],
                                period_cutoff) -> dict[str, Any]:
    """
    RUN 20 CYCLE 2, P0C GOVERNANCE AND REGULATORY OVERCLAIM.

    This module is registered as a reporting threshold and measures cost and schedule
    performance. Specification section 17, 8.4, states in terms that cost and schedule
    performance bands do not establish reporting compliance, and Run 19 verified the consequence
    directly: a contractor submitting every required monthly report on time on a struggling
    project was reported as having BREACHED a reporting threshold, and one submitting nothing at
    all on a healthy project was reported as within it. The word "BREACHED" beside a
    reporting-compliance name is the overclaim.

    Reporting compliance is made of applicability, the contract clause, the required cadence or
    data item, the due date and the received date. Under the committed snapshot FAR 34.201(c)
    requires as a minimum monthly reports on contracts to which earned value management applies,
    and FAR 52.234-4 requires the reports the contract calls for. Not one of those inputs exists
    in this module, so reporting compliance is not assessed, and the result now says so on its
    face through reporting_compliance_assessed and through the sentence.

    The three flags are renamed from breach to what they measure, a performance index below an
    internal review level of 0.90. The arithmetic, the guards, the conjunction and the band are
    untouched, and no regulatory threshold is introduced. Carrying cadence, due date and
    received date is the P2 work the register records for this module.
    """
    if not check_inputs(si, ("bac", "cpi", "spi")):
        return insufficient("EVM_Reporting_Threshold")
    if si["cpi"] == 0 or si["bac"] == 0:
        return insufficient("EVM_Reporting_Threshold")  # JS Infinity/NaN; refused
    cpi_b = si["cpi"] < 0.90
    spi_b = si["spi"] < 0.90
    both = cpi_b and spi_b
    eac = si["bac"] / si["cpi"]
    delta = ((eac - si["bac"]) / si["bac"]) * 100
    if not cpi_b and not spi_b:
        color = "Green"
    elif cpi_b != spi_b:
        color = "Yellow"
    elif both and delta <= 15:
        color = "Amber"
    else:
        color = "Red"
    return {
        "method_class": "EVM_Reporting_Threshold",
        "status_color": color,
        "cpi_below_review_level": cpi_b,
        "spi_below_review_level": spi_b,
        "both_below_review_level": both,
        "threshold_provenance": "UNCITED_INTERNAL_REVIEW_LEVEL",
        "reporting_compliance_assessed": False,
        "eac_delta_pct": round1(delta),
        "evidence_metric": (
            f"Cost index {'below' if cpi_b else 'at or above'} the internal review level of "
            f"0.90, schedule index {'below' if spi_b else 'at or above'} it, forecast at "
            f"completion {_js_str(round1(delta))}% over budget. No reporting cadence, due date "
            f"or received date is held, so whether required reports were submitted is not "
            f"assessed here."
        ),
    }


def run_contract_mod_frequency(si: dict, rand: Callable[[], float],
                               period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("changeOrderCount", "baselineContractSum", "revisedContractSum")):
        return insufficient("Contract_Mod_Frequency")
    growth = (((si["revisedContractSum"] - si["baselineContractSum"])
               / si["baselineContractSum"]) * 100 if si["baselineContractSum"] > 0 else 0)
    co = si["changeOrderCount"]
    if co >= 10 or growth >= 20:
        risk = "Red"
    elif co >= 6 or growth >= 10:
        risk = "Amber"
    elif co >= 3 or growth >= 5:
        risk = "Yellow"
    else:
        risk = "Green"
    is_derived = _derived(si, "changeOrderCount", "baselineContractSum")
    word = ("contracting officer review merits consideration" if risk == "Red"
            else "elevated modification frequency" if risk == "Amber"
            else "within normal range")
    return {
        "method_class": "Contract_Mod_Frequency",
        "status_color": risk,
        "co_count": co,
        "scope_growth_pct": round1(growth),
        "evidence_metric": (
            f"{_js_str(co)} contract modifications, {_js_str(round1(growth))}% scope growth, "
            + word
            + (" (estimated; upload Change Order log for precise figures)" if is_derived else "")
        ),
    }


# ================================================================ B4 decision optimization


def run_multi_objective(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("Multi_Objective_Optimization")
    norm_cpi = min(1, max(0, (si["cpi"] - 0.80) / 0.25))
    norm_spi = min(1, max(0, (si["spi"] - 0.80) / 0.25))
    norm_risk = 1 - (si.get("docRiskScore") or 0)
    pareto = round2((norm_cpi + norm_spi + norm_risk) / 3)
    objectives = sorted(
        [
            {"name": "Cost performance", "score": norm_cpi},
            {"name": "Schedule performance", "score": norm_spi},
            {"name": "Document risk", "score": norm_risk},
        ],
        key=lambda o: o["score"],
    )
    binding = objectives[0]
    color = ("Green" if pareto >= 0.75 else "Yellow" if pareto >= 0.55
             else "Amber" if pareto >= 0.35 else "Red")
    return {
        "method_class": "Multi_Objective_Optimization",
        "status_color": color,
        "pareto_score": pareto,
        "binding_constraint": binding["name"],
        "objectives": objectives,
        "evidence_metric": (
            f"Multi-objective score: {int(js_round(pareto * 100))}%, "
            f"binding constraint: {binding['name']} "
            f"(score {int(js_round(binding['score'] * 100))}%)"
        ),
    }


def run_linear_programming(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("bac", "ev", "ac", "cpi")):
        return insufficient("Linear_Programming")
    remaining_work = si["bac"] - si["ev"]
    remaining_budget = si["bac"] - si["ac"]
    if remaining_budget <= 0:
        return {
            "method_class": "Linear_Programming",
            "status_color": "Red",
            "feasible": False,
            "evidence_metric": "No feasible solution: budget exhausted before project completion",
        }
    required = remaining_work / remaining_budget
    feasible = required <= 1.20
    optimal = required <= 1.00
    lp_score = min(1, _jsdiv(1.0, required)) if feasible else 0
    color = ("Green" if optimal else "Yellow" if required <= 1.05
             else "Amber" if required <= 1.15 else "Red")
    word = ("achievable at current performance" if optimal
            else "requires productivity improvement" if feasible
            else "budget infeasible, recovery plan needed")
    return {
        "method_class": "Linear_Programming",
        "status_color": color,
        "required_cpi_to_complete": _round3(required),
        "feasible": feasible,
        "optimal": optimal,
        "lp_score": round2(lp_score),
        "evidence_metric": (
            f"LP: requires CPI {_js_str(_round3(required))} to complete within budget, {word}"
        ),
    }


def run_constraint_satisfaction(si: dict, rand: Callable[[], float],
                                period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "bac")):
        return insufficient("Constraint_Satisfaction")
    doc = si.get("docRiskScore") or 0
    constraints = [
        {"name": "Cost constraint (CPI ≥ 0.90)", "satisfied": si["cpi"] >= 0.90},
        {"name": "Schedule constraint (SPI ≥ 0.90)", "satisfied": si["spi"] >= 0.90},
        {"name": "Document risk (score < 0.70)", "satisfied": doc < 0.70},
        # RUN 20 CYCLE 2. This rule was presented to the reader as "FAR threshold
        # (overrun < 25%)". FAR 34.201 states earned value management policy and applicability
        # and states no numeric overrun threshold of any kind, so the regulation's name and part
        # number were attached to an uncited internal level. The comparison itself is coherent
        # and unchanged: a forecast at completion of budget over cost index overruns by less
        # than a quarter exactly when the cost index exceeds 0.80. Only the false attribution
        # is removed.
        {"name": "Forecast overrun below 25% (CPI > 0.80)", "satisfied": si["cpi"] > 0.80},
    ]
    satisfied = sum(1 for c in constraints if c["satisfied"])
    violated = [c["name"] for c in constraints if not c["satisfied"]]
    rate = satisfied / len(constraints)
    color = ("Green" if rate >= 1.0 else "Yellow" if rate >= 0.75
             else "Amber" if rate >= 0.50 else "Red")
    return {
        "method_class": "Constraint_Satisfaction",
        "status_color": color,
        "satisfied": satisfied,
        "total": len(constraints),
        "violated_constraints": violated,
        "satisfaction_rate": int(js_round(rate * 100)),
        "evidence_metric": (
            f"{satisfied} of {len(constraints)} constraints satisfied"
            + (f"; violated: {', '.join(violated)}" if violated else "; all constraints met")
        ),
    }


def run_whatif_matrix(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    """
    THE FIFTEEN DEFECTS, defect 13, applied to the second of the two computations it can name.

    The defect list identifies this one by code and by the name of its sibling, so both were
    read and both carried the same unguarded earned value domains: a guard at exactly zero, and
    nothing at all for a negative index, a negative budget, or earned value exceeding the budget
    at completion. The guards below are the same as the sibling's and refuse for the same
    reasons. Which of the two the audit meant does not change what either needed.
    """
    if not check_inputs(si, ("bac", "ev", "ac", "cpi", "spi")):
        return insufficient("WhatIf_Scenario_Matrix")
    if si["cpi"] <= 0 or si["spi"] <= 0:
        return insufficient(
            "WhatIf_Scenario_Matrix",
            "Cost or schedule performance is recorded as zero or below, which no remaining "
            "work can be divided by")
    if si["bac"] <= 0:
        return insufficient(
            "WhatIf_Scenario_Matrix",
            "No positive budget at completion is recorded to scale the scenarios against")
    if si["ev"] < 0 or si["ac"] < 0:
        return insufficient(
            "WhatIf_Scenario_Matrix",
            "Negative earned value or actual cost is not a measurable position to forecast from")
    if si["ev"] > si["bac"]:
        return insufficient(
            "WhatIf_Scenario_Matrix",
            "More value is recorded as earned than the budget at completion contains, so there "
            "is no remaining work to forecast")
    remaining = si["bac"] - si["ev"]
    scenarios = [
        {"name": "Optimistic (CPI recovers to 1.0)", "eac": si["ac"] + remaining * 1.00},
        {"name": "Base (current CPI continues)", "eac": si["bac"] / si["cpi"]},
        {"name": "Pessimistic (CPI degrades 5%)", "eac": si["bac"] / (si["cpi"] * 0.95)},
        {"name": "Recovery (CPI improves 5%)", "eac": si["bac"] / (si["cpi"] * 1.05)},
    ]
    base_eac = scenarios[1]["eac"]
    range_pct = int(js_round(((scenarios[2]["eac"] - scenarios[0]["eac"]) / si["bac"]) * 100))
    color = ("Green" if range_pct <= 5 else "Yellow" if range_pct <= 10
             else "Amber" if range_pct <= 20 else "Red")
    return {
        "method_class": "WhatIf_Scenario_Matrix",
        "status_color": color,
        "scenarios": [
            {"name": s["name"], "eac": int(js_round(s["eac"])),
             "delta_pct": round1(((s["eac"] - si["bac"]) / si["bac"]) * 100)}
            for s in scenarios
        ],
        "scenario_range_pct": range_pct,
        "base_eac": int(js_round(base_eac)),
        "evidence_metric": (
            f"Scenario range: {range_pct}% of BAC, "
            f"base EAC ${int(js_round(base_eac / 1000))}k, "
            f"worst ${int(js_round(scenarios[2]['eac'] / 1000))}k, "
            f"best ${int(js_round(scenarios[0]['eac'] / 1000))}k"
        ),
    }


def run_decision_sensitivity(si: dict, rand: Callable[[], float],
                             period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("Decision_Sensitivity_Matrix")
    cpi_i = abs(1 - si["cpi"]) * 100
    spi_i = abs(1 - si["spi"]) * 100
    risk_i = (si.get("docRiskScore") or 0) * 50
    total = (cpi_i + spi_i + risk_i) or 1
    sensitivity = sorted(
        [
            {"driver": "Cost performance (CPI)", "impact": cpi_i,
             "pct": int(js_round(cpi_i / total * 100))},
            {"driver": "Schedule performance (SPI)", "impact": spi_i,
             "pct": int(js_round(spi_i / total * 100))},
            {"driver": "Document risk", "impact": risk_i,
             "pct": int(js_round(risk_i / total * 100))},
        ],
        key=lambda d: -d["impact"],
    )
    top = sensitivity[0]
    mx = top["impact"]
    color = ("Green" if mx <= 3 else "Yellow" if mx <= 7 else "Amber" if mx <= 12 else "Red")
    return {
        "method_class": "Decision_Sensitivity_Matrix",
        "status_color": color,
        "top_driver": top["driver"],
        "top_driver_pct": top["pct"],
        "sensitivity_matrix": sensitivity,
        "evidence_metric": (
            f"Decision most sensitive to: {top['driver']} ({top['pct']}% of decision weight); "
            f"a small change here most changes the governance recommendation"
        ),
    }


def run_pareto_frontier(si: dict, rand: Callable[[], float], period_cutoff) -> dict[str, Any]:
    if not check_inputs(si, ("cpi", "spi", "docRiskScore")):
        return insufficient("Pareto_Frontier")
    doc = si.get("docRiskScore") or 0
    cost_ok = si["cpi"] >= 0.95
    sched_ok = si["spi"] >= 0.95
    risk_ok = doc < 0.30
    dominated = not cost_ok and not sched_ok
    efficient = cost_ok and sched_ok and risk_ok
    tradeoff = (cost_ok != sched_ok) or (not risk_ok and (cost_ok or sched_ok))
    score = ((1 if cost_ok else si["cpi"] / 0.95)
             + (1 if sched_ok else si["spi"] / 0.95)
             + (1 if risk_ok else (1 - doc / 0.30))) / 3
    score = round2(min(1, score))
    color = ("Green" if efficient else "Yellow" if tradeoff
             else "Amber" if not dominated else "Red")
    evidence = ("Project is Pareto-efficient: all objectives met simultaneously" if efficient
                else "Project is Pareto-dominated: multiple objectives failing simultaneously"
                if dominated
                else "Trade-off required: improving one objective may affect another" if tradeoff
                else "Partial Pareto efficiency: some objectives met")
    return {
        "method_class": "Pareto_Frontier",
        "status_color": color,
        "pareto_efficient": efficient,
        "dominated": dominated,
        "tradeoff_required": tradeoff,
        "pareto_score": score,
        "evidence_metric": evidence,
    }


def run_regret_minimization(si: dict, rand: Callable[[], float],
                            period_cutoff) -> dict[str, Any]:
    """
    RUN 7, AND THIS ONE ABSTAINS UNCONDITIONALLY.

    Minimax regret is defined by an action-by-scenario payoff matrix: what each course of action
    costs under each future state, for the decision actually in front of the reader. This
    platform holds no such matrix. The one below was nine literals and three literal state
    probabilities, so the three expected regrets were 11, 5 and 8 on every project and in every
    period, the minimum was always to investigate, and the two overrides could only move that to
    escalate. The known-answer run exhausted 3,721 cost and schedule index pairs from 0.70 to
    1.30 and found no pair that produced a healthy reading: a project twenty per cent ahead on
    both indices was still told to investigate, because the only branch that reads healthy was
    unreachable from any input.

    The corpus was searched for a governed payoff matrix before this was written, and there is
    none: no action-by-scenario structure exists anywhere in the repository outside these
    literals. Substituting different literals would repeat the fault at a different set of
    numbers, and building a real minimax-regret engine needs owner approval and a matrix that
    does not exist. So the module refuses and states which structure is missing.

    What this does NOT do is decide anything for a participant. The courses of action a
    participant chooses among were already outside this module's reach: a non-voting module is
    excluded from the recommendation text and the courses of action by the owner's settled
    decision, which this module has been subject to since Run 1, and it stays non-voting here.
    No new decision policy is introduced by this run.
    """
    return insufficient(
        "Regret_Minimization",
        "Insufficient data: no set of courses of action scored against defined future states is "
        "held for this project, so there is no worst case per course to compare and no course "
        "can be identified as carrying the smallest one. No ranking is offered in its place.",
        ABSTAIN_DECISION_STRUCTURE_ABSENT)


GOV_BATCH_A: dict[str, tuple[str, Callable]] = {
    "B1.2": ("Weighted_Voting", run_weighted_voting),
}

GOV_BATCH_B: dict[str, tuple[str, Callable]] = {
}
