"""
De-identified export and archive chain (B6).

This turns collected data into an analysable dataset. Two properties matter more than anything
else here.

De-identification is an allowlist, never a denylist. EXPORT_COLUMNS names every field that may
leave the system; a row is assembled by naming each field explicitly, so a column added to a model
later cannot appear in an export by default. A denylist would invert the failure: the day someone
adds an ip_hash column, every export silently starts carrying it, and the leak is discovered after
the data has been shared.

The payload is regenerated on fetch rather than stored. research_exports records the checksum, not
the bytes, so fetching re-derives the payload from the current data and compares. That is a
stronger property than reading back a blob: it detects the underlying rows changing after the
export was taken, which is exactly the drift that would silently invalidate an analysis. It also
means B6 needs no migration.

Free text is included and flagged. rationale is a dependent variable, so it has to be exported,
but participants can type anything into it, including their own name or a colleague's. The export
carries an explicit review flag rather than quietly shipping text nobody has read.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .facade import err
from .research_identity import audit, resolve_caller
from .research_models import (
    Assignment, AuditEvent, Configuration, Decision, DecisionSupportPackage, Participant,
    ResearchExport, Scenario, Transition,
)

# Every field that may leave the system, in export order. Adding a field here is the only way to
# export one. Nothing is derived from a model's column list.
EXPORT_COLUMNS: tuple[str, ...] = (
    # identity: the pseudonymous code and nothing else
    "pseudonymous_code",
    "order_group",
    # design
    "scenario_id",
    "scenario_version",
    "sequence_number",
    "period",
    "config_code",
    # preliminary judgment
    "pre_action",
    "pre_confidence",
    "pre_submitted_at",
    "pre_locked_at",
    # reveal
    "reveal_at",
    "package_id",
    "package_version",
    "package_hash",
    # final decision
    "final_action",
    "disposition",
    "final_confidence",
    "final_submitted_at",
    "escalation_level",
    "owner_role",
    "authority_role",
    "resource_constraint",
    # free text, flagged for review
    "rationale",
    # transition
    "branch_id",
    "branch_version",
    "transition_seed",
    "transition_probability",
    "next_state_id",
    "transition_displayed_at",
    # derived analysis variables
    "judgment_shift_action",
    "confidence_shift",
    "deliberation_seconds",
    "pre_assessment_seconds",
)

# Checked by the tests against the serialised payload. These names must never appear.
FORBIDDEN_FIELDS: tuple[str, ...] = (
    "access_token_hash", "session_ref", "ip_hash", "ip_address", "email", "participant_id",
    "consent_id", "access_token",
)

# Columns whose content is participant-authored and may contain identifiers.
FREE_TEXT_COLUMNS: tuple[str, ...] = ("rationale",)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _seconds_between(later: datetime | None, earlier: datetime | None) -> float | None:
    if later is None or earlier is None:
        return None
    return round((later - earlier).total_seconds(), 3)


def _parse_range(payload: dict) -> tuple[datetime | None, datetime | None, str | None]:
    def one(key: str) -> tuple[datetime | None, str | None]:
        raw = payload.get(key)
        if raw in (None, ""):
            return None, None
        try:
            parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except ValueError:
            return None, f"{key} is not an ISO 8601 timestamp"
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed, None

    start, problem = one("date_from")
    if problem:
        return None, None, problem
    end, problem = one("date_to")
    if problem:
        return None, None, problem
    if start and end and start > end:
        return None, None, "date_from is after date_to"
    return start, end, None


def _assignment_start(session: Session, participant_id: str, scenario_id: str,
                      period: str) -> datetime | None:
    """
    When the participant first saw the evidence for this period.

    Taken from the earliest evidence_viewed audit event rather than from a column, because there
    is no such column: the assignment row records allocation, not when the participant opened it.
    Using the audit trail keeps the derived variable traceable to a recorded event.
    """
    rows = session.scalars(
        select(AuditEvent).where(
            AuditEvent.event_type == "evidence_viewed",
            AuditEvent.participant_id == participant_id,
            AuditEvent.scenario_id == scenario_id,
        ).order_by(AuditEvent.server_ts)
    ).all()
    for row in rows:
        meta = row.event_metadata or {}
        if str(meta.get("period") or "P1") == period:
            return row.server_ts
    return None


def build_rows(session: Session, start: datetime | None, end: datetime | None) -> list[dict[str, Any]]:
    """
    One row per decision: participant x scenario x period. Long format, ready for a mixed-effects
    model with crossed random effects on participant and scenario.

    The range filters on final_submitted_at, so a decision counts as belonging to the window in
    which it was completed. Filtering on pre_submitted_at would split a decision across windows
    when a participant paused between periods.
    """
    query = select(Decision).order_by(Decision.decision_id)
    if start is not None:
        query = query.where(Decision.final_submitted_at >= start)
    if end is not None:
        query = query.where(Decision.final_submitted_at <= end)

    rows: list[dict[str, Any]] = []
    for decision in session.scalars(query).all():
        assignment = session.get(Assignment, decision.assignment_id)
        if assignment is None:
            continue
        participant = session.get(Participant, assignment.participant_id)
        # B8 account separation, UNCONDITIONAL: only research accounts enter an export. This is
        # not a parameter, cannot be overridden by any payload field, and applies to every
        # export ever taken, including refetches of exports created before B8. An operational
        # account's rows never leave the system through this path.
        if participant is None or participant.account_type != "research":
            continue
        scenario = session.get(Scenario, assignment.scenario_id)
        config = session.get(Configuration, assignment.config_id) if assignment.config_id else None
        package = (session.get(DecisionSupportPackage, decision.package_id)
                   if decision.package_id else None)
        transition = session.scalar(
            select(Transition).where(Transition.decision_id == decision.decision_id))

        started = _assignment_start(session, assignment.participant_id,
                                    assignment.scenario_id, decision.period or "P1")

        shift = None
        if decision.final_action is not None and decision.pre_action is not None:
            shift = decision.final_action != decision.pre_action

        confidence_shift = None
        if decision.final_confidence is not None and decision.pre_confidence is not None:
            confidence_shift = decision.final_confidence - decision.pre_confidence

        # Assembled by naming every field. No model introspection, no dict(row), no **kwargs:
        # each of those would let a new column travel outwards without anyone deciding it should.
        row = {
            "pseudonymous_code": participant.pseudonymous_code if participant else None,
            "order_group": participant.order_group if participant else None,
            "scenario_id": assignment.scenario_id,
            "scenario_version": scenario.scenario_version if scenario else None,
            "sequence_number": assignment.sequence_number,
            "period": decision.period,
            # The analyst's view, unlike the participant's: the condition must be present.
            "config_code": config.code if config else None,
            "pre_action": decision.pre_action,
            "pre_confidence": decision.pre_confidence,
            "pre_submitted_at": _iso(decision.pre_submitted_at),
            "pre_locked_at": _iso(decision.pre_locked_at),
            "reveal_at": _iso(decision.reveal_at),
            "package_id": decision.package_id,
            "package_version": package.version if package else None,
            "package_hash": decision.package_hash,
            "final_action": decision.final_action,
            "disposition": decision.disposition,
            "final_confidence": decision.final_confidence,
            "final_submitted_at": _iso(decision.final_submitted_at),
            "escalation_level": decision.escalation_level,
            "owner_role": decision.owner_role,
            "authority_role": decision.authority_role,
            "resource_constraint": decision.resource_constraint,
            "rationale": decision.rationale,
            "branch_id": transition.branch_id if transition else None,
            "branch_version": transition.branch_version if transition else None,
            "transition_seed": transition.seed if transition else None,
            "transition_probability": transition.probability if transition else None,
            "next_state_id": transition.next_state_id if transition else None,
            "transition_displayed_at": _iso(transition.displayed_at) if transition else None,
            "judgment_shift_action": shift,
            "confidence_shift": confidence_shift,
            "deliberation_seconds": _seconds_between(decision.final_submitted_at,
                                                     decision.reveal_at),
            "pre_assessment_seconds": _seconds_between(decision.pre_submitted_at, started),
        }

        # Defensive, and cheap: a row must contain exactly the allowlist. If these ever disagree
        # the export fails rather than shipping an unexpected shape.
        if set(row) != set(EXPORT_COLUMNS):
            raise RuntimeError(
                "export row does not match EXPORT_COLUMNS; "
                f"unexpected={sorted(set(row) - set(EXPORT_COLUMNS))} "
                f"missing={sorted(set(EXPORT_COLUMNS) - set(row))}"
            )
        rows.append({k: row[k] for k in EXPORT_COLUMNS})

    return rows


def serialise(rows: list[dict[str, Any]], fmt: str) -> tuple[bytes, str | None]:
    """Render the payload. The checksum covers exactly these bytes."""
    if fmt == "json":
        body = {
            "columns": list(EXPORT_COLUMNS),
            "free_text_columns": list(FREE_TEXT_COLUMNS),
            "review_required": bool(FREE_TEXT_COLUMNS),
            "review_note": ("Free-text columns are participant-authored and may contain "
                            "identifying content. Review before sharing outside the study team."),
            "row_count": len(rows),
            "rows": rows,
        }
        return json.dumps(body, sort_keys=True, separators=(",", ":"),
                          default=str).encode("utf-8"), None

    if fmt == "csv":
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=list(EXPORT_COLUMNS),
                                lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: ("" if row[k] is None else row[k]) for k in EXPORT_COLUMNS})
        return buffer.getvalue().encode("utf-8"), None

    return b"", f"unsupported format: {fmt}"


def checksum(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _require_admin(session: Session, payload: dict, secret: str, action: str):
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return None, problem
    if not caller.is_admin:
        # Rule 5: refused and audited. An attempt to export is exactly the event a research audit
        # trail should hold, whether or not it succeeded.
        audit(session, "export_action_denied", participant_id=caller.participant_id,
              action=action, role=caller.role)
        session.commit()
        return None, err("not authorised: ResearchAdmin role required")
    return caller, None


def a_adminexportcreate(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = _require_admin(session, payload, secret, "adminexportcreate")
    if problem:
        return problem

    fmt = str(payload.get("format") or "json").strip().lower()
    if fmt not in ("json", "csv"):
        return err("format must be json or csv")

    start, end, problem_text = _parse_range(payload)
    if problem_text:
        return err(problem_text)

    try:
        rows = build_rows(session, start, end)
    except RuntimeError as exc:
        return err(str(exc))

    body, problem_text = serialise(rows, fmt)
    if problem_text:
        return err(problem_text)

    digest = checksum(body)
    date_range = f"{start.isoformat() if start else 'open'}/{end.isoformat() if end else 'open'}"

    row = ResearchExport(
        format=fmt,
        row_count=len(rows),
        checksum=digest,
        destination=str(payload.get("destination") or "inline"),
        date_range=date_range,
        initiated_by=caller.participant_id,
        completed_at=func.now(),
    )
    # An export is an administrative act gated by role, not by participant consent. The consent
    # gate honours this flag rather than resolving initiated_by to a participant who, being an
    # administrator, will never have consented.
    row._admin_authorised = True
    session.add(row)
    audit(session, "export_created", participant_id=caller.participant_id,
          export_format=fmt, row_count=len(rows), checksum=digest, date_range=date_range)
    session.commit()

    session.refresh(row)
    return {
        "ok": True,
        "export_id": row.export_id,
        "format": fmt,
        "row_count": len(rows),
        "checksum": digest,
        "date_range": date_range,
        "destination": row.destination,
        "completed_at": _iso(row.completed_at),
        "review_required": bool(FREE_TEXT_COLUMNS),
        "free_text_columns": list(FREE_TEXT_COLUMNS),
        "columns": list(EXPORT_COLUMNS),
    }


def a_adminexportlist(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = _require_admin(session, payload, secret, "adminexportlist")
    if problem:
        return problem
    rows = session.scalars(select(ResearchExport).order_by(ResearchExport.export_id)).all()
    return {"ok": True, "exports": [
        {"export_id": r.export_id, "format": r.format, "row_count": r.row_count,
         "checksum": r.checksum, "destination": r.destination, "date_range": r.date_range,
         "completed_at": _iso(r.completed_at)}
        for r in rows
    ]}


def a_adminexportfetch(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Re-derive the payload and verify it against the stored checksum.

    A mismatch is reported loudly and the payload is withheld. It means the underlying rows have
    changed since the export was taken, so any analysis quoting that checksum no longer describes
    the data now in the database, and returning it silently would hide exactly that.
    """
    caller, problem = _require_admin(session, payload, secret, "adminexportfetch")
    if problem:
        return problem

    export_id = str(payload.get("export_id") or "").strip()
    if not export_id:
        return err("export_id is required")
    record = session.get(ResearchExport, export_id)
    if record is None:
        return err(f"export not found: {export_id}")

    start, end = None, None
    if record.date_range and "/" in record.date_range:
        left, _, right = record.date_range.partition("/")
        if left != "open":
            start = datetime.fromisoformat(left)
        if right != "open":
            end = datetime.fromisoformat(right)

    try:
        rows = build_rows(session, start, end)
    except RuntimeError as exc:
        return err(str(exc))

    body, problem_text = serialise(rows, record.format or "json")
    if problem_text:
        return err(problem_text)

    digest = checksum(body)
    if digest != record.checksum:
        audit(session, "export_checksum_mismatch", participant_id=caller.participant_id,
              export_id=export_id, stored_checksum=record.checksum, recomputed=digest)
        session.commit()
        return err(
            f"checksum verification failed for export {export_id}: stored {record.checksum}, "
            f"recomputed {digest}. The underlying data has changed since this export was taken; "
            f"the payload is withheld."
        )

    audit(session, "export_fetched", participant_id=caller.participant_id,
          export_id=export_id, checksum=digest, row_count=len(rows))
    session.commit()

    return {
        "ok": True,
        "export_id": export_id,
        "format": record.format,
        "row_count": len(rows),
        "checksum": digest,
        "checksum_verified": True,
        "review_required": bool(FREE_TEXT_COLUMNS),
        "free_text_columns": list(FREE_TEXT_COLUMNS),
        "review_note": ("Free-text columns are participant-authored and may contain identifying "
                        "content. Review before sharing outside the study team."),
        "columns": list(EXPORT_COLUMNS),
        "payload": body.decode("utf-8"),
    }


EXPORT_ACTIONS: dict[str, Callable[[Session, dict, str, int], dict]] = {
    "adminexportcreate": a_adminexportcreate,
    "adminexportlist": a_adminexportlist,
    "adminexportfetch": a_adminexportfetch,
}
