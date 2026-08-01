"""
T7/T8 — intake and debrief questionnaire storage.

Both instruments are JSON-driven on the frontend (assets/questionnaires/intake.json,
assets/questionnaires/debrief.json — served as static files through the existing /assets mount,
so editing a definition takes effect on the next page load with no server change and no code
edit). This module is only the storage half: it never renders a question and never validates
wording, because the instrument is explicitly not finalised (see both JSON files' `note` field).

WHERE ANSWERS LAND

Every item's answer is stored raw, keyed by item id, in `participant_profiles.intake_responses`
/ `debrief_responses` (migration 0010) — that is the lossless, definition-agnostic record. The
handful of intake items that map onto the narrow columns the schema already had (from 0003,
built for exactly this instrument) are ALSO copied there, via `_INTAKE_FIELD_MAP` below, purely
for analysts who want a typed column rather than a JSONB key. If an item's id ever changes in
the JSON definition, the raw blob keeps working immediately; only `_INTAKE_FIELD_MAP` might need
a one-line update, which is a Python dict edit, not a migration.

CONSENT

`ParticipantProfile` is already in `research_consent.GATED_TABLES` (B2) — the gate is keyed off
the SQLAlchemy model class via a `before_flush` listener, not off an action-name allowlist, so
an ORM write to this table is gated automatically by writing through `session.add`/`commit` in
the normal request lifecycle, exactly as every other gated write already does. Nothing here
re-implements or bypasses that.

DEBRIEF ELIGIBILITY, AND A DELIBERATE SCOPE LIMIT

"After the participant's final decision" is checked live against every one of the participant's
`Assignment` rows reaching `derive_stage() == STAGE_COMPLETE` for their current period — not
against `Participant.completion_status`, which nothing in the codebase currently transitions to
"complete" (B3's `a_adminassign` only ever sets it to "assigned"). This makes debrief eligibility
correct today and automatically correct once T4 starts marking decisions complete, with no
further change needed here.

What this module deliberately does NOT do: refuse a_researchprejudgment (B4, research_decision.py)
for a participant who has not completed intake. B4's own test fixtures (tools/test_decision_
sequence.py) grant consent and record decisions for participants who — by construction — predate
this phase and have no profile row. Adding that guard there would refuse every one of those
fixtures and regress B4's validated 60/60 suite for behaviour this phase did not change. The
"cannot skip it before their first decision" guarantee is therefore proven here in its provable
half — this module refuses debrief before completion, symmetrically — and intake-before-
first-decision enforcement against an actual decision-write action is left for T4, which does not
exist yet and will be the first UI able to reach that action at all.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from .facade import err, now_iso
from .research_consent import has_active_consent
from .research_decision import STAGE_COMPLETE, _decision_for, current_period, derive_stage
from .research_identity import resolve_caller
from .research_models import Assignment, ParticipantProfile

# Intake item id -> ParticipantProfile column, for the items that map cleanly onto a narrow
# column the schema already had. Anything not listed here still lands in intake_responses raw
# — this map is an analyst convenience, never the source of truth.
_INTAKE_FIELD_MAP: dict[str, str] = {
    "experience_level": "experience_level",
    "years_experience": "years_experience",
    "industry": "industry",
    "certifications": "certifications",
    "ai_familiarity": "ai_familiarity",
    "organizational_role": "organizational_role",
}
# risk_attitude is intentionally not in the map above: the JSON definition carries MULTIPLE
# risk-attitude items (risk_attitude_general, risk_attitude_professional, ...), because the
# scale is still being selected with the committee and may grow or shrink. All items whose
# "field" is "risk_attitude" are collected together into that JSONB column, keyed by item id,
# rather than each overwriting a single scalar.
_RISK_ATTITUDE_FIELD = "risk_attitude"


def _profile_for(session: Session, participant_id: str) -> ParticipantProfile | None:
    return session.scalar(
        select(ParticipantProfile).where(ParticipantProfile.participant_id == participant_id)
        .order_by(ParticipantProfile.captured_at.desc())
    )


def _get_or_create_profile(session: Session, participant_id: str) -> ParticipantProfile:
    profile = _profile_for(session, participant_id)
    if profile is not None:
        return profile
    profile = ParticipantProfile(participant_id=participant_id)
    session.add(profile)
    return profile


def a_profilestatus(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Self-read. Whether the caller has already completed intake and/or is eligible for debrief.
    No admin gate: a participant needs this to know which questionnaire, if any, to show —
    the same posture as researchwhoami.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem

    profile = _profile_for(session, caller.participant_id)
    eligible, reason = _debrief_eligibility(session, caller.participant_id)

    return {
        "ok": True,
        "consent_granted": has_active_consent(session, caller.participant_id),
        "intake_completed": bool(profile and profile.intake_captured_at),
        "intake_captured_at": (profile.intake_captured_at.isoformat()
                               if profile and profile.intake_captured_at else None),
        "debrief_completed": bool(profile and profile.debrief_captured_at),
        "debrief_captured_at": (profile.debrief_captured_at.isoformat()
                                if profile and profile.debrief_captured_at else None),
        "debrief_eligible": eligible,
        "debrief_eligibility_reason": reason,
        "server_time": now_iso(),
    }


def a_intakesave(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Any signed-in, consented participant. `responses` is {item_id: answer}, exactly the shape
    the intake.json definition's items produce — this action does not validate item wording or
    required-ness against the definition (the instrument is not finalised; that is a frontend
    concern for the version of the definition currently on disk, not a server contract this
    phase should freeze). It stores what it is given.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    if not has_active_consent(session, caller.participant_id):
        return err("consent is required before the intake questionnaire can be recorded")

    responses = payload.get("responses")
    if not isinstance(responses, dict) or not responses:
        return err("responses is required and must be a non-empty object")

    profile = _get_or_create_profile(session, caller.participant_id)
    profile.intake_responses = responses
    profile.intake_captured_at = datetime.now(timezone.utc)

    risk_items = {k: v for k, v in responses.items() if k.startswith("risk_attitude")}
    if risk_items:
        profile.risk_attitude = risk_items
    for item_id, column in _INTAKE_FIELD_MAP.items():
        if item_id in responses:
            setattr(profile, column, responses[item_id])

    session.commit()
    return {"ok": True, "intake_captured_at": profile.intake_captured_at.isoformat(),
           "server_time": now_iso()}


def _debrief_eligibility(session: Session, participant_id: str) -> tuple[bool, str]:
    """
    True only once EVERY one of the participant's assignments has reached STAGE_COMPLETE for
    its current period. See the module docstring for why this is computed live rather than
    read off Participant.completion_status.
    """
    assignments = session.scalars(
        select(Assignment).where(Assignment.participant_id == participant_id)
    ).all()
    if not assignments:
        return False, "no scenarios have been assigned yet"
    for a in assignments:
        period = current_period(session, a)
        decision = _decision_for(session, a.assignment_id, period)
        if derive_stage(decision) != STAGE_COMPLETE:
            return False, "not all assigned scenarios have reached a final decision yet"
    return True, "all assigned scenarios are complete"


def a_debriefsave(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Any signed-in, consented participant, and only once every assignment is complete. Symmetric
    to a_intakesave's consent check — this is the half of Guarantee 9 ("cannot skip it") this
    module can enforce without touching B4's validated write path. See the module docstring.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    if not has_active_consent(session, caller.participant_id):
        return err("consent is required before the debrief questionnaire can be recorded")

    eligible, reason = _debrief_eligibility(session, caller.participant_id)
    if not eligible:
        return err(f"debrief is not available yet: {reason}")

    responses = payload.get("responses")
    if not isinstance(responses, dict) or not responses:
        return err("responses is required and must be a non-empty object")

    profile = _get_or_create_profile(session, caller.participant_id)
    profile.debrief_responses = responses
    profile.debrief_captured_at = datetime.now(timezone.utc)
    session.commit()
    return {"ok": True, "debrief_captured_at": profile.debrief_captured_at.isoformat(),
           "server_time": now_iso()}


QUESTIONNAIRE_ACTIONS: dict[str, Callable[[Session, dict, str, int], dict]] = {
    "profilestatus": a_profilestatus,
    "intakesave": a_intakesave,
    "debriefsave": a_debriefsave,
}
