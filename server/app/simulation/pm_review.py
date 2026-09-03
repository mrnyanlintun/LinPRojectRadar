"""
RUN 121. THE HOLD COMES OFF. PM REVIEW IS A DISCRETE EVENT, NOT A GATE.

THE OWNER'S RULING, RUN 121, SECTION 1, IN HIS OWN WORDS. "PM feedback on contractor
performance is a discrete event. Otherwise the rest goes as planned until the PM flags there is
an issue with the contractor." So NOTHING WAITS ON REVIEW. A computed posture -- Amber, Red, or
any other -- asserts its band and flows to its category as normal. The PM flags an issue when
there is one, and that flag is the event, not the absence of one.

WHAT THIS REVERSES. Run 107 introduced `pending_pm_review` for A4.8: an adverse normalised
posture asserted no band until a disposition was recorded. Run 118 applied it to the eight-factor
subcontractor engine, Run 119 extended it to catch a lift of two or more bands, and Run 120
applied it to A6.4's four-factor chain. The owner's ruling covers all four. The PENDING exit is
GONE from `resolve` and `pending_pm_review` is no longer a state this platform can produce.

WHAT DID NOT GO, AND WHY EACH SURVIVED THE DELETION UNTOUCHED.

  * THE REVIEW ROUTE. `documents.a_projectmodulereview` never consulted the hold: it validates
    the disposition against `research_decision.PROJECT_DECISION_DISPOSITIONS`, reads the
    platform's own mapping off the stored row and appends one `audit_events` row. It refuses a
    review only where no reading is stored, never because a reading was or was not held. A PM
    can still record a disposition on any reading, held or not, and always could.
  * THE RECORDED DISPOSITION'S AUTHORITY. `DISPOSITION_EFFECT` is unchanged and so is the
    REVIEWED exit below. Where a PM has modified or overridden a posture, `takes_pm_posture`
    puts the PM's band in place of the computed one exactly as it did before this run. That exit
    was ALREADY independent of the hold -- it fired whenever a review existed -- so removing the
    PENDING exit did not touch it.
  * THE AUDIT RECORD. `audit_record` below is unchanged in every field the owner enumerates: the
    source rating, the factor values, the overrides that fired, the computed posture, the
    disposition, the rationale and the timestamp.
  * THE LIFT DISCLOSURE. Run 119 built the hold so a firm rated Unsatisfactory could not
    SILENTLY publish Green. The hold goes; the silence does not come back. `lift_bands` is
    unchanged, the movement is still measured, still on the audit record, and a lift of
    `LIFT_BANDS_REQUIRING_DISCLOSURE` bands or more now composes `LIFT_DISCLOSURE_WORDS` into
    the sentence a reader reads. The reading publishes AND says it was lifted.

THE PLATFORM NEVER ACTS. It states the finding; the human decides. Nothing here issues a notice,
changes a payment, directs corrective action or makes a contractual determination, and the source
rating is never altered or erased -- the audit record carries it verbatim beside the PM's own
posture, and both are rendered.
"""
from __future__ import annotations

from typing import Any

#: The severity ordering the size of a movement is counted on -- `fusion.BAND_SEVERITY`,
#: IMPORTED and not restated, so the distance between two bands cannot come to mean one thing
#: here and another in `category_posture` or `project_posture`.
from .fusion import BAND_SEVERITY as _BAND_SEVERITY

#: The module-level states. NOT project statuses and never assigned to `status_color`.
#:
#: RUN 121. `MODULE_STATE_PENDING` / `pending_pm_review` IS DELETED, not merely unused. A
#: constant left behind is a hold waiting to be re-wired by the next run that greps for it, and
#: `drive_run121.py` asserts the name is absent from this module's executing code. There are now
#: exactly two module states: a reading STANDS, or a Project Manager has REVIEWED it.
MODULE_STATE_STANDS = "stands"
MODULE_STATE_REVIEWED = "reviewed_by_pm"

MODULE_STATES: tuple[str, ...] = (MODULE_STATE_STANDS, MODULE_STATE_REVIEWED)

# ======================================================= RUN 121. THE LIFT IS DISCLOSED, NOT HELD.
#
# THE DEFECT RUN 118 MEASURED. A firm the performance report rated Unsatisfactory, with clean
# trade records and full denominators, was lifted three bands to Green by the averaging rule --
# and published, SILENTLY, because an improved posture is not adverse.
#
# RUN 119 ANSWERED IT WITH A HOLD. The owner has now ruled the hold off: "PM feedback on
# contractor performance is a discrete event." Run 121 therefore keeps the WHOLE of Run 119's
# measurement -- `lift_bands`, the two-band size, the audit fields -- and changes only what
# happens when it fires. The reading PUBLISHES ITS BAND and SAYS IT WAS LIFTED.
#
# WHY THE DISCLOSURE IS NOT ALSO DELETED, WHEN THE HOLD IT SERVED IS. The owner's Run 121 order
# names it under "what must NOT be lost", in terms: "The hold goes; the disclosure must not. A
# posture two or more bands better than the stated rating still says so on the reading, in the
# sentence a reader reads." So the reader-facing sentence is the whole of the mechanism now, and
# it is the thing `drive_run121.py` proves able to fail.
#
# THE NUMBER IS STILL THE OWNER'S. Two bands, from his Run 119 words. Nothing here invents a
# size, and a lift of one band is not disclosed, exactly as it was not held.
LIFT_BANDS_REQUIRING_DISCLOSURE: int = 2

#: RUN 121. The Run 119 name, kept as an alias so no caller and no suite silently reads a
#: DIFFERENT number than the one the owner stated. It is the same integer, not a second one.
LIFT_BANDS_REQUIRING_REVIEW: int = LIFT_BANDS_REQUIRING_DISCLOSURE


def lift_bands(source_posture: str | None, final_posture: str | None) -> int | None:
    """
    How many bands BETTER `final_posture` is than `source_posture`, or None where no movement
    can be measured. UNCHANGED BY RUN 121.

    Positive is an improvement, negative an adverse move, zero no move. None where either end is
    absent or is not one of the four bands: a reading with no starting posture has not MOVED,
    and silence is never read as a starting Green.
    """
    a = _BAND_SEVERITY.get(str(source_posture)) if source_posture is not None else None
    b = _BAND_SEVERITY.get(str(final_posture)) if final_posture is not None else None
    if a is None or b is None:
        return None
    return a - b


#: RUN 121. THE SENTENCE A LIFTED READING CARRIES ONTO THE PAGE. Composed here once so the
#: ledger, the census, the brief and the card cannot each write a different one -- the same
#: reason `LIFT_PENDING_WORDS` was composed here when the lift was held.
LIFT_DISCLOSURE_WORDS = (
    "DISCLOSED LIFT: this reading is two or more bands BETTER than the rating its source "
    "document stated, and the owner requires that to be said rather than published silently. "
    "The stated rating is the owner's own assessment and the records may overturn it; where they "
    "do, the size and direction of the movement are stated here and the source rating is "
    "preserved beside the adjusted posture on the audit record. The reading is NOT held: a "
    "Project Manager's review is a discrete event he records when there is an issue, and the "
    "absence of one holds nothing.")

#: RUN 121. The rule sentence carried on every resolution and every audit record, replacing Run
#: 119's hold sentence. It states the size, what happens at it, and what is NOT inferred.
LIFT_RULE_WORDS = (
    f"A lift of {LIFT_BANDS_REQUIRING_DISCLOSURE} or more bands above the posture the source "
    f"document's own rating normalised to is DISCLOSED on the reading a person reads. It is not "
    f"held: the owner has ruled that Project Manager feedback is a discrete event and that "
    f"nothing waits on the absence of one. A lift of one band is not disclosed. Where no "
    f"starting posture is known there is no movement to measure and none is inferred.")

#: RUN 121. The sentence a reading that is NOT lifted carries, so a reader can tell the two
#: apart and cannot read silence as "we did not check".
STANDS_WORDS = (
    "This reading stands: the owner has ruled that Project Manager feedback on contractor "
    "performance is a discrete event, so no computed posture waits on a review. The band below "
    "is asserted and enters its category as normal. A Project Manager may record a disposition "
    "against it at any time, and where he does, that disposition governs.")

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


def resolve(normalised_posture: str, review: dict | None,
            source_posture: str | None = None) -> dict[str, Any]:
    """
    What this module publishes, given its normalised posture, the posture it STARTED from, and
    the review (if any) on record.

    RUN 121. THERE ARE NOW TWO EXITS WHERE THERE WERE THREE, AND THE ONE THAT WENT IS THE HOLD.

      * STANDS -- no interpretable review on record. The COMPUTED POSTURE IS PUBLISHED, whatever
        it is. Before this run an Amber or Red posture, or a posture lifted two or more bands,
        returned `posture: None` here and waited. It no longer waits.
      * REVIEWED -- a review is on record carrying one of the five dispositions, and
        `DISPOSITION_EFFECT` decides. THIS EXIT IS BYTE-FOR-BYTE WHAT IT WAS: it never consulted
        the hold, it fired whenever a review existed, and a PM who has modified or overridden a
        posture still governs the computed one exactly as before.

    A REVIEW CARRYING A DISPOSITION THIS PLATFORM DOES NOT HOLD no longer leaves the module
    held -- there is nothing to be held by. It is reported as an uninterpretable record and the
    COMPUTED POSTURE STANDS, which is the same answer the platform now gives to no review at all,
    because a record nobody can interpret is not a review.

    THE SOURCE RATING IS NEVER ALTERED: it is carried through untouched and the PM's posture is
    carried BESIDE it, never over it. THE LIFT IS STILL MEASURED and, at two bands or more, is
    disclosed in `module_state_words` and on the audit record.
    """
    _lift = lift_bands(source_posture, normalised_posture)
    _disclosed = _lift is not None and _lift >= LIFT_BANDS_REQUIRING_DISCLOSURE
    _movement = {
        "source_posture": source_posture,
        "lift_bands": _lift,
        "lift_disclosed": _disclosed,
        # RUN 121. KEPT AND ALWAYS FALSE, deliberately, rather than deleted. Every stored audit
        # record written between Runs 119 and 120 carries `held_for_lift`, and a reader
        # comparing an old record with a new one is entitled to see the field answer "no" rather
        # than vanish and leave him unable to tell a lift that was not held from a field that
        # was never asked. Nothing branches on it.
        "held_for_lift": False,
        "lift_rule": LIFT_RULE_WORDS,
    }
    _lift_sentence = (" " + LIFT_DISCLOSURE_WORDS) if _disclosed else ""
    if not review:
        return {"posture": normalised_posture, "module_state": MODULE_STATE_STANDS,
                "review_required": False, "review": None, **_movement,
                "module_state_words": STANDS_WORDS + _lift_sentence}
    disposition = str(review.get("disposition") or "")
    effect = DISPOSITION_EFFECT.get(disposition)
    if effect is None:
        return {"posture": normalised_posture, "module_state": MODULE_STATE_STANDS,
                "review_required": False, "review": review, **_movement,
                "uninterpretable_review": True,
                "module_state_words": (
                    "A review was recorded against this reading carrying a disposition this "
                    "platform does not hold, so it is not read as a review and it changes "
                    "nothing. " + STANDS_WORDS + _lift_sentence)}
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
        "review_required": False,
        "review": review,
        **_movement,
        "disposition": disposition,
        "disposition_label": effect["label"],
        "disposition_effect_words": effect["words"],
        "module_state_words": (
            f"A Project Manager reviewed this reading and recorded the disposition "
            f"'{effect['label']}': {effect['words']}. The platform's own normalised posture "
            f"was {normalised_posture} and is preserved beside the Project Manager's, never "
            f"replaced by it." + _lift_sentence),
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
        # RUN 119, GOAL 1, KEPT BY RUN 121. THE MOVEMENT, ON THE AUDIT RECORD. A lift must be
        # readable as a lift: the band the source rating normalised to, how many bands the
        # reading moved above it, and whether that movement was large enough to be disclosed.
        "source_rating_posture": resolution.get("source_posture"),
        "lift_bands": resolution.get("lift_bands"),
        "held_for_lift": resolution.get("held_for_lift"),
        # RUN 121. THE HOLD IS GONE AND THE DISCLOSURE IS THE RECORD OF THE MOVEMENT.
        "lift_disclosed": resolution.get("lift_disclosed"),
        "lift_rule": resolution.get("lift_rule"),
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
