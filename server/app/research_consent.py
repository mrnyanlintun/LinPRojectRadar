"""
Consent gate.

No write to participant_profiles, assignments, decisions, transitions or research_exports is
permitted for a participant without an active consent: a consents row with granted_at set and
withdrawn_at null.

Enforced with a SQLAlchemy before_flush listener rather than a check at the top of each endpoint.
An endpoint-level check is only as good as the discipline of whoever adds the next endpoint, and
the failure mode is silent: research data captured from a participant who never consented, which
cannot be repaired after the fact because the consent did not exist at the time. The listener sees
every INSERT and UPDATE the ORM performs, including from code written later that never heard of
this module.

The gate deliberately does not cover audit_events, participants or consents themselves. Audit rows
must record what happened regardless of consent state, a participant row has to exist before it can
consent, and the consents row is the act of consenting.
"""

from __future__ import annotations

from typing import Iterable

from sqlalchemy import event, select
from sqlalchemy.orm import Session

from .research_models import (
    Assignment, Consent, Decision, ParticipantProfile, ResearchExport, Transition,
)


class ConsentRequired(Exception):
    """Raised when a gated write is attempted for a participant without active consent."""

    def __init__(self, participant_id: str | None, table: str) -> None:
        self.participant_id = participant_id
        self.table = table
        super().__init__(
            f"consent required: no active consent for participant "
            f"{participant_id or '<unresolved>'}; refusing to write {table}"
        )


# Tables the gate covers, with how a participant is resolved from an instance.
GATED_TABLES = {
    ParticipantProfile: lambda o: o.participant_id,
    Assignment: lambda o: o.participant_id,
    # Decision and Transition reach a participant through their assignment.
    Decision: lambda o: None,
    Transition: lambda o: None,
    # An export is an administrative act with no owning participant, so it is gated on
    # initiated_by when that names a participant. See _resolve_participant.
    ResearchExport: lambda o: None,
}


def has_active_consent(session: Session, participant_id: str | None) -> bool:
    if not participant_id:
        return False
    row = session.scalar(
        select(Consent).where(
            Consent.participant_id == participant_id,
            Consent.granted_at.is_not(None),
            Consent.withdrawn_at.is_(None),
        )
    )
    return row is not None


def _resolve_participant(session: Session, obj) -> str | None:
    """
    Find the participant a pending object belongs to.

    Uses the identifier already on the instance where possible and falls back to a query only for
    the indirect cases, because during before_flush the related rows may not be persisted yet.
    """
    if isinstance(obj, (ParticipantProfile, Assignment)):
        return obj.participant_id

    if isinstance(obj, Decision):
        assignment = _find_assignment(session, obj.assignment_id)
        return assignment.participant_id if assignment else None

    if isinstance(obj, Transition):
        decision = _find_pending_or_stored(session, Decision, "decision_id", obj.decision_id)
        if decision is None:
            return None
        assignment = _find_assignment(session, decision.assignment_id)
        return assignment.participant_id if assignment else None

    if isinstance(obj, ResearchExport):
        # initiated_by carries a participant id when a participant triggered the export. An
        # administrator's export leaves it unresolved, which the caller must authorise explicitly.
        return obj.initiated_by

    return None


def _find_assignment(session: Session, assignment_id: str | None) -> Assignment | None:
    return _find_pending_or_stored(session, Assignment, "assignment_id", assignment_id)


def _find_pending_or_stored(session: Session, model, pk_name: str, pk_value):
    """Look in session.new first: a row created in this same flush is not queryable yet."""
    if pk_value is None:
        return None
    for pending in session.new:
        if isinstance(pending, model) and getattr(pending, pk_name, None) == pk_value:
            return pending
    return session.get(model, pk_value)


def _pending(session: Session) -> Iterable:
    yield from session.new
    yield from session.dirty


def enforce_consent(session: Session) -> None:
    """Raise ConsentRequired if any pending gated write lacks an active consent."""
    for obj in _pending(session):
        model = type(obj)
        if model not in GATED_TABLES:
            continue
        # An unmodified object caught by session.dirty is not a write.
        if obj in session.dirty and not session.is_modified(obj, include_collections=False):
            continue

        # An administrative export with no participant is allowed only when explicitly marked.
        if isinstance(obj, ResearchExport) and not obj.initiated_by:
            if getattr(obj, "_admin_authorised", False):
                continue
            raise ConsentRequired(None, "research_exports")

        participant_id = _resolve_participant(session, obj)
        if not has_active_consent(session, participant_id):
            raise ConsentRequired(participant_id, model.__tablename__)


_INSTALLED = False


def install() -> None:
    """
    Register the listener once, for every Session.

    Applied to the Session class rather than an instance so it covers sessions created anywhere,
    including in code that predates or ignores this module.
    """
    global _INSTALLED
    if _INSTALLED:
        return

    @event.listens_for(Session, "before_flush")
    def _before_flush(session, flush_context, instances):  # noqa: ANN001
        enforce_consent(session)

    _INSTALLED = True
