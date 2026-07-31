"""
Research identity: login, session, roles, consent.

Runs on the existing /exec contract. Application errors are HTTP 200 with {"ok":false,"error":...},
actions match case-insensitively, and every timestamp is server-assigned.

Three decisions that shape everything below.

Sessions are stateless and signed, not stored. B2 ships no migration, so there is no sessions
table. A session token is a signed assertion of one thing only, the participant id; the role,
stage and consent state are read from the database on every request. A token therefore cannot
carry a stale or elevated role, and revoking a participant takes effect immediately rather than
when their token expires.

Access tokens are stored as an unsalted SHA-256 of a 256-bit random secret. Unsalted is deliberate
and safe here: the input is high-entropy random, not a human-chosen password, so there is no
dictionary or rainbow-table attack to defend against, and a deterministic hash allows an indexed
lookup instead of scanning every participant row and comparing salted hashes.

Role is never read from the request. A body-supplied role or participant_id is ignored entirely,
not validated, because validating it would imply it is sometimes authoritative.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import re
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .facade import err, now_iso
from .research_consent import ConsentRequired, has_active_consent
from .research_models import AuditEvent, Consent, Participant, new_ulid

log = logging.getLogger("opus-gubernatio-server")

ROLE_ADMIN = "ResearchAdmin"
ROLE_PARTICIPANT = "Participant"
ROLE_EXPERT = "Expert"
ROLE_DEMO = "Demo"

_CODE_RE = re.compile(r"^PM-(\d+)$")


# ---------------------------------------------------------------- audit


def audit(session: Session, event_type: str, *, participant_id: str | None = None,
          scenario_id: str | None = None, **metadata: Any) -> None:
    """
    Append one audit row. server_ts comes from the column default, never from a caller.

    Rule 5: every identity event is audited. Rule 4's rejected cross-participant reads are audited
    here too, which is why this is called before returning the error rather than after.
    """
    session.add(AuditEvent(
        participant_id=participant_id,
        scenario_id=scenario_id,
        event_type=event_type,
        event_metadata=metadata or None,
    ))


# ---------------------------------------------------------------- access tokens


def issue_access_token() -> tuple[str, str]:
    """Return (plaintext, hash). The plaintext is returned to the caller exactly once."""
    plaintext = secrets.token_urlsafe(32)
    return plaintext, hash_access_token(plaintext)


def hash_access_token(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- session tokens


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def mint_session(participant_id: str, secret: str, ttl_seconds: int) -> str:
    """Signed, self-describing, and carrying no authority beyond naming a participant."""
    now = int(time.time())
    payload = {"pid": participant_id, "iat": now, "exp": now + ttl_seconds}
    body = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    sig = _b64(hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest())
    return f"{body}.{sig}"


def read_session(token: str, secret: str) -> tuple[str | None, str | None]:
    """Return (participant_id, error). Signature is checked before the payload is trusted."""
    if not token or "." not in token:
        return None, "missing or malformed session token"
    body, _, sig = token.partition(".")
    expected = _b64(hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest())
    # compare_digest: a timing-safe comparison, so a forged signature cannot be discovered byte by
    # byte from response timing.
    if not hmac.compare_digest(sig, expected):
        return None, "invalid session token"
    try:
        payload = json.loads(_unb64(body))
    except Exception:  # noqa: BLE001
        return None, "invalid session token"
    if int(payload.get("exp", 0)) < int(time.time()):
        return None, "session expired"
    pid = payload.get("pid")
    return (pid, None) if pid else (None, "invalid session token")


# ---------------------------------------------------------------- caller resolution


class Caller:
    """The authenticated caller. Role always comes from the database row, never the request."""

    def __init__(self, participant: Participant) -> None:
        self.participant = participant
        self.participant_id = participant.participant_id
        self.role = participant.role

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN


def resolve_caller(session: Session, payload: dict, secret: str) -> tuple[Caller | None, dict | None]:
    pid, problem = read_session(str(payload.get("session_token") or ""), secret)
    if problem:
        return None, err(problem)
    participant = session.get(Participant, pid)
    if participant is None:
        # A validly signed token for a participant that no longer exists.
        return None, err("session does not correspond to a known participant")
    return Caller(participant), None


def consent_state(session: Session, participant_id: str) -> dict[str, Any]:
    row = session.scalar(
        select(Consent).where(Consent.participant_id == participant_id)
        .order_by(Consent.granted_at.desc())
    )
    if row is None:
        return {"status": "none", "consent_version": None, "granted_at": None, "withdrawn_at": None}
    active = row.withdrawn_at is None and row.granted_at is not None
    return {
        "status": "granted" if active else "withdrawn",
        "consent_version": row.consent_version,
        "granted_at": row.granted_at.isoformat() if row.granted_at else None,
        "withdrawn_at": row.withdrawn_at.isoformat() if row.withdrawn_at else None,
    }


def derived_stage(session: Session, participant_id: str) -> str:
    """
    Current stage, computed from the decisions row.

    participants.current_stage is never read here and is never written from a request. A stored
    stage is a second source of truth that can disagree with the data it describes, and in a
    blinded flow a stage running ahead of the data would itself be a disclosure. Imported locally
    because research_decision imports this module.
    """
    from .research_assignment import current_sequence_number
    from .research_decision import STAGE_EVIDENCE, derive_stage
    from .research_models import Assignment, Decision

    current = current_sequence_number(session, participant_id)
    if current is None:
        return STAGE_EVIDENCE
    assignment = session.scalar(
        select(Assignment).where(Assignment.participant_id == participant_id,
                                 Assignment.sequence_number == current)
    )
    if assignment is None:
        return STAGE_EVIDENCE
    decision = session.scalar(
        select(Decision).where(Decision.assignment_id == assignment.assignment_id)
    )
    return derive_stage(decision)


def _participant_view(session: Session, p: Participant) -> dict[str, Any]:
    """The self-view. Never includes access_token_hash: rule 2."""
    return {
        "participant_id": p.participant_id,
        "pseudonymous_code": p.pseudonymous_code,
        "role": p.role,
        "eligibility_status": p.eligibility_status,
        "current_scenario": p.current_scenario,
        "current_stage": derived_stage(session, p.participant_id),
        "completion_status": p.completion_status,
        "consent": consent_state(session, p.participant_id),
    }


# ---------------------------------------------------------------- actions


def a_researchlogin(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    presented = str(payload.get("access_token") or "").strip()
    if not presented:
        return err("access_token is required")

    token_hash = hash_access_token(presented)
    participant = session.scalar(
        select(Participant).where(Participant.access_token_hash == token_hash)
    )
    if participant is None:
        # Audited without a participant id, since none was identified. The presented token is
        # never recorded, only that an attempt failed.
        audit(session, "research_login_failed", reason="unrecognised access token")
        session.commit()
        return err("access token not recognised")

    audit(session, "research_login", participant_id=participant.participant_id,
          role=participant.role)
    session.commit()

    view = _participant_view(session, participant)
    view["session_token"] = mint_session(participant.participant_id, secret, ttl)
    view["ok"] = True
    return view


def a_researchwhoami(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    view = _participant_view(session, caller.participant)
    view["ok"] = True
    return view


def a_consentgrant(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem

    version = str(payload.get("consent_version") or "").strip()
    if not version:
        return err("consent_version is required")

    if has_active_consent(session, caller.participant_id):
        return err("consent already granted; withdraw it before granting again")

    # Rule 3: the consent is recorded for the session's participant. A participant_id in the body
    # is ignored.
    row = Consent(
        participant_id=caller.participant_id,
        consent_version=version,
        method=payload.get("method"),
        session_ref=payload.get("session_ref"),
    )
    session.add(row)
    audit(session, "consent_granted", participant_id=caller.participant_id,
          consent_version=version, method=payload.get("method"))
    session.commit()

    session.refresh(row)
    if row.granted_at is None:
        return err("consent could not be verified: granted_at was not assigned")
    return {"ok": True, "consent_id": row.consent_id, "consent_version": version,
            "granted_at": row.granted_at.isoformat()}


def a_consentwithdraw(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem

    row = session.scalar(
        select(Consent).where(
            Consent.participant_id == caller.participant_id,
            Consent.withdrawn_at.is_(None),
        ).order_by(Consent.granted_at.desc())
    )
    if row is None:
        return err("no active consent to withdraw")

    # Recorded, never deleted: deleting would destroy the evidence that consent was given.
    row.withdrawn_at = func.now()
    audit(session, "consent_withdrawn", participant_id=caller.participant_id,
          consent_id=row.consent_id)
    session.commit()

    session.refresh(row)
    return {"ok": True, "consent_id": row.consent_id,
            "withdrawn_at": row.withdrawn_at.isoformat() if row.withdrawn_at else None}


def _next_code(session: Session) -> str:
    """PM-001 style, server-generated. Numbering continues past withdrawn or deleted rows."""
    highest = 0
    for (code,) in session.execute(select(Participant.pseudonymous_code)):
        m = _CODE_RE.match(code or "")
        if m:
            highest = max(highest, int(m.group(1)))
    return f"PM-{highest + 1:03d}"


def a_adminparticipantcreate(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    if not caller.is_admin:
        audit(session, "admin_action_denied", participant_id=caller.participant_id,
              action="adminparticipantcreate", role=caller.role)
        session.commit()
        return err("not authorised: ResearchAdmin role required")

    role = str(payload.get("role") or ROLE_PARTICIPANT)
    if role not in (ROLE_ADMIN, ROLE_PARTICIPANT, ROLE_EXPERT, ROLE_DEMO):
        return err(f"unknown role: {role}")

    plaintext, token_hash = issue_access_token()
    code = _next_code(session)
    participant = Participant(
        pseudonymous_code=code,
        role=role,
        access_token_hash=token_hash,
        eligibility_status=payload.get("eligibility_status"),
        scenario_set=payload.get("scenario_set"),
        condition_sequence=payload.get("condition_sequence"),
        order_group=payload.get("order_group"),
        completion_status="not_started",
    )
    session.add(participant)
    session.flush()
    audit(session, "participant_created", participant_id=participant.participant_id,
          created_by=caller.participant_id, role=role, pseudonymous_code=code)
    session.commit()

    return {
        "ok": True,
        "participant_id": participant.participant_id,
        "pseudonymous_code": code,
        "role": role,
        # Returned exactly once. Only its hash is stored, so it cannot be recovered later.
        "access_token": plaintext,
        "access_token_notice": "Shown once. It is stored hashed and cannot be retrieved again.",
    }


def a_adminparticipantlist(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    if not caller.is_admin:
        audit(session, "admin_action_denied", participant_id=caller.participant_id,
              action="adminparticipantlist", role=caller.role)
        session.commit()
        return err("not authorised: ResearchAdmin role required")

    rows = session.scalars(select(Participant).order_by(Participant.pseudonymous_code)).all()
    # No access_token_hash in this projection: rule 2.
    return {"ok": True, "participants": [
        {
            "participant_id": p.participant_id,
            "pseudonymous_code": p.pseudonymous_code,
            "role": p.role,
            "eligibility_status": p.eligibility_status,
            "current_scenario": p.current_scenario,
            "current_stage": derived_stage(session, p.participant_id),
            "completion_status": p.completion_status,
            "consent": consent_state(session, p.participant_id),
        }
        for p in rows
    ]}


def a_researchparticipantget(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Read one participant record.

    Rule 4: a Participant can only ever read their own record. A request for another participant
    is refused in the ok:false shape and the attempt is audited, because an attempt to read another
    participant's data is exactly the event a research audit trail exists to capture.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem

    target_id = str(payload.get("participant_id") or "").strip() or caller.participant_id

    if target_id != caller.participant_id and not caller.is_admin:
        audit(session, "cross_participant_read_denied",
              participant_id=caller.participant_id, target_participant_id=target_id,
              role=caller.role)
        session.commit()
        return err("not authorised: a participant may only read their own record")

    target = session.get(Participant, target_id)
    if target is None:
        return err(f"participant not found: {target_id}")

    view = _participant_view(session, target)
    view["ok"] = True
    return view


IDENTITY_ACTIONS: dict[str, Callable[[Session, dict, str, int], dict]] = {
    "researchlogin": a_researchlogin,
    "researchwhoami": a_researchwhoami,
    "consentgrant": a_consentgrant,
    "consentwithdraw": a_consentwithdraw,
    "adminparticipantcreate": a_adminparticipantcreate,
    "adminparticipantlist": a_adminparticipantlist,
    "researchparticipantget": a_researchparticipantget,
}
