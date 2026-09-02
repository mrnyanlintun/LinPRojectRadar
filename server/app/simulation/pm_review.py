"""
RUN 107. THE PM REVIEW STATE -- A MODULE-LEVEL STATE, NOT A SEVENTH PROJECT STATUS.

THE OWNER'S RULING, RUN 107, SECTION 2, A4.8. "An Amber or Red normalised result is not a
finding until a Project Manager has reviewed it." Green or Yellow stands and acknowledgement is
optional; Amber or Red puts the MODULE into `pending_pm_review` and it does not enter the
Document Signals category posture until a disposition is recorded. The category proceeds
without it.

WHY THIS IS NOT A NEW PROJECT STATUS, AND HOW THAT IS KEPT TRUE STRUCTURALLY. Run 106 fixed the
project status vocabulary at exactly six -- Complete, Green, Yellow, Amber, Red, Awaiting
analysis. `pending_pm_review` is NEVER written to `status_color`, never to `project_status` and
never to a category's `status`. A held module returns `status_color = None`, which is the
platform's existing, proven meaning of "this row asserts no band": `category_posture` averages
only banded modules, so a row with no band contributes nothing, cannot drag its category down
and cannot lift it. The held state lives in its own key, `module_state`, beside the reading. A
reader who greps for the six statuses will never find this string among them.

WHY THE HOLD IS NOT `EXCLUDED_FROM_CATEGORY_ROLLUP`. That set is a PERMANENT property of a
module -- B1.2 is derived from the rollup it would feed, so it may never enter it, on any
project, in any period. This is a PER-READING state: the same module on the same project enters
the rollup the moment a disposition is recorded, and enters it on a Green reading without any
review at all. Putting it in that set would hold A4.8 out of Document Signals forever, which is
the opposite of the owner's ruling.

THE PLATFORM NEVER ACTS. It states the finding; the human decides. Nothing here issues a
notice, changes a payment, directs corrective action or makes a contractual determination, and
the source rating is never altered or erased -- the audit record carries it verbatim beside the
PM's own posture, and both are rendered.
"""
from __future__ import annotations

from typing import Any

#: The module-level states. NOT project statuses and never assigned to `status_color`.
MODULE_STATE_STANDS = "stands"
MODULE_STATE_PENDING = "pending_pm_review"
MODULE_STATE_REVIEWED = "reviewed_by_pm"

MODULE_STATES: tuple[str, ...] = (MODULE_STATE_STANDS, MODULE_STATE_PENDING,
                                  MODULE_STATE_REVIEWED)

#: The postures that require a review before they are a finding. The owner's words.
POSTURES_REQUIRING_REVIEW: frozenset[str] = frozenset({"Amber", "Red"})

#: THE SENTENCE A HELD MODULE CARRIES. Composed here once so the ledger, the census, the brief
#: and the card cannot each write a different one.
PENDING_WORDS = (
    "This reading normalised to a posture the owner has ruled is not a finding until a Project "
    "Manager has reviewed it. The module is held pending that review: it asserts no band, it "
    "does not enter the Document Signals category posture, and the category is formed from the "
    "modules that are available. A single unreviewed subcontractor rating holds neither the "
    "category nor the project.")

#: WHAT EACH DISPOSITION DOES TO THE POSTURE. The five codes are `research_decision.
#: PROJECT_DECISION_DISPOSITIONS` -- the SAME five the Governance Decision card offers, reused
#: rather than duplicated, so the platform can never grow a second review vocabulary.
#:
#:   requires_rationale -- the owner's order states it for Modify and Override.
#:   takes_pm_posture   -- whether the PM's own posture replaces the normalised one.
DISPOSITION_EFFECT: dict[str, dict[str, Any]] = {
    "accept": {
        "label": "Accept finding", "takes_pm_posture": False, "requires_rationale": False,
        "not_assessed": False,
        "words": "the normalised posture stands"},
    "modify": {
        "label": "Modify finding", "takes_pm_posture": True, "requires_rationale": True,
        "not_assessed": False,
        "words": "the Project Manager's revised posture stands"},
    "defer": {
        "label": "Defer pending evidence", "takes_pm_posture": False,
        "requires_rationale": False, "not_assessed": True,
        "words": "Not Assessed, with the limitation 'Pending PM evidence review'"},
    "reject": {
        "label": "Override finding", "takes_pm_posture": True, "requires_rationale": True,
        "not_assessed": False, "allows_not_assessed": True,
        "words": "the Project Manager's posture, or Not Assessed"},
    "no_action_within_current_authority": {
        "label": "Record no action within current authority", "takes_pm_posture": False,
        "requires_rationale": False, "not_assessed": False,
        "words": "the normalised posture stands; the record notes no action"},
}

DEFER_LIMITATION = "Pending PM evidence review"


def resolve(normalised_posture: str, review: dict | None) -> dict[str, Any]:
    """
    What this module publishes, given its normalised posture and the review (if any) on record.

    Returns `posture` (the band to assert, or None for Not Assessed), `module_state`, and the
    audit fields the owner's order requires to be visible. THE SOURCE RATING IS NEVER ALTERED:
    it is carried through untouched and the PM's posture is carried BESIDE it, never over it.
    """
    if normalised_posture not in POSTURES_REQUIRING_REVIEW:
        return {"posture": normalised_posture, "module_state": MODULE_STATE_STANDS,
                "review_required": False, "review": None,
                "module_state_words": (
                    "the normalised posture is not one the owner holds for review, so it "
                    "stands; a Project Manager's acknowledgement is optional and none is "
                    "required for this reading to enter its category")}
    if not review:
        return {"posture": None, "module_state": MODULE_STATE_PENDING,
                "review_required": True, "review": None,
                "not_assessed_reason": PENDING_WORDS,
                "module_state_words": PENDING_WORDS}
    disposition = str(review.get("disposition") or "")
    effect = DISPOSITION_EFFECT.get(disposition)
    if effect is None:
        # A disposition outside the five is not resolved into a posture. The module stays held
        # rather than falling to the normalised band, because a record nobody can interpret is
        # not a review.
        return {"posture": None, "module_state": MODULE_STATE_PENDING,
                "review_required": True, "review": review,
                "not_assessed_reason": (
                    "A review was recorded against this reading carrying a disposition this "
                    "platform does not hold, so it is not read as a review and the reading "
                    "stays held. " + PENDING_WORDS),
                "module_state_words": PENDING_WORDS}
    pm_posture = review.get("pm_posture")
    posture: str | None
    if effect["not_assessed"]:
        posture = None
    elif effect["takes_pm_posture"]:
        posture = pm_posture if pm_posture in ("Green", "Yellow", "Amber", "Red") else None
    else:
        posture = normalised_posture
    out = {
        "posture": posture,
        "module_state": MODULE_STATE_REVIEWED,
        "review_required": True,
        "review": review,
        "disposition": disposition,
        "disposition_label": effect["label"],
        "disposition_effect_words": effect["words"],
        "module_state_words": (
            f"A Project Manager reviewed this reading and recorded the disposition "
            f"'{effect['label']}': {effect['words']}. The platform's own normalised posture "
            f"was {normalised_posture} and is preserved beside the Project Manager's, never "
            f"replaced by it."),
    }
    if effect["not_assessed"]:
        out["not_assessed_reason"] = DEFER_LIMITATION
        out["assessment_limitation"] = DEFER_LIMITATION
    elif posture is None:
        out["not_assessed_reason"] = (
            "The Project Manager overrode the finding and recorded Not Assessed in place of a "
            "posture.")
    return out


def audit_record(*, normalised_posture: str, source_rating: str, source_document_id: str | None,
                 source_document_version: str | None, period: str | None,
                 normalisation_rule: str, normalisation_rule_version: str,
                 resolution: dict) -> dict[str, Any]:
    """
    THE AUDIT RECORD THE OWNER'S ORDER ENUMERATES, assembled in one place so a surface cannot
    render a partial one. Every field the order names is a key here, and a field with nothing
    behind it is None rather than absent, so a reader can see that it was asked for.
    """
    review = resolution.get("review") or {}
    return {
        "source_rating": source_rating,
        "source_document_id": source_document_id,
        "source_document_version": source_document_version,
        "assessment_period": period,
        "normalisation_rule": normalisation_rule,
        "normalisation_rule_version": normalisation_rule_version,
        "platform_mapped_posture": normalised_posture,
        "pm_participant_id": review.get("recorded_by"),
        "pm_recorded_at": review.get("recorded_at"),
        "disposition": review.get("disposition"),
        "disposition_label": resolution.get("disposition_label"),
        "rationale": review.get("rationale"),
        "evidence_references": review.get("evidence_references"),
        "pm_final_posture": resolution.get("posture"),
        "both_visible_words": (
            "Both the platform's mapping and the Project Manager's final posture are recorded "
            "and rendered. The source rating is never altered or erased."),
        "platform_takes_no_action": (
            "The platform never issues a notice, changes payment, directs corrective action, or "
            "makes a final contractual determination. It states the finding; the human decides."),
    }
