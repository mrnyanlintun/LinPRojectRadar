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

T2 adds a second sign-in path and account lifecycle management, on the same three decisions:

Two credentials, deliberately never converging. A research participant authenticates with the
same opaque access token as before (paired, in the UI, with the pseudonymous code as a familiar
"username" — but the code is checked only AFTER the token already matched, so a wrong code never
narrows the search space; see a_researchlogin). An operational user authenticates with Google
SSO, verified server-side against Google's own signing keys, resolved to a Participant by
google_email. Neither path can produce the other's identity: SSO refuses outright for an account
whose account_type is research, and the password path has no notion of a Google identity at all.

is_active is the one flag that can lock a caller out of everything at once. It is checked in
resolve_caller, the single choke point nearly every authenticated action already passes through,
so deactivating an account does not need to be re-implemented at each endpoint — and cannot be
forgotten at a new one.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
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
    if not participant.is_active:
        # T2: the single choke point. A signature can still be valid after deactivation — the
        # token itself carries no state — so this is the one place that has to check the current
        # row rather than trust the token, exactly like role is never read from the token either.
        return None, err("this account has been deactivated; contact an administrator")
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
    # The current period, not "the" decision: an assignment has one decisions row per period,
    # so querying by assignment alone would be ambiguous once period 2 exists.
    from .research_decision import current_period
    from .research_models import Scenario

    scenario = session.get(Scenario, assignment.scenario_id)
    period = current_period(session, assignment, scenario)
    decision = session.scalar(
        select(Decision).where(Decision.assignment_id == assignment.assignment_id,
                               Decision.period == period)
    )
    return derive_stage(decision)


def _participant_view(session: Session, p: Participant) -> dict[str, Any]:
    """The self-view. Never includes access_token_hash: rule 2."""
    return {
        "participant_id": p.participant_id,
        "pseudonymous_code": p.pseudonymous_code,
        "role": p.role,
        # T2: the frontend routes on this (research -> consent gate; operational -> straight
        # through) rather than inferring it from anything else, so it has to be in the self-view.
        "account_type": p.account_type,
        "is_active": p.is_active,
        # Only meaningful for an operational account; a research participant never has one.
        "display_name": p.display_name,
        "eligibility_status": p.eligibility_status,
        "current_scenario": p.current_scenario,
        "current_stage": derived_stage(session, p.participant_id),
        "completion_status": p.completion_status,
        "consent": consent_state(session, p.participant_id),
    }


# ---------------------------------------------------------------- actions


def a_researchlogin(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    T2 UI note: the sign-in form presents this as "username" (the pseudonymous code) and
    "password" (the access token) side by side, because that is the familiar shape. The backend
    credential is still the token alone — the code adds nothing a lookup on the token hash didn't
    already have — so the code is checked only AFTER a token match, never used to search. A
    request that gets the token right and the code wrong fails with the exact same message as a
    request that gets the token wrong: collapsing them into one path is what keeps "cannot be
    probed" true now that there is a second field to probe.
    """
    presented = str(payload.get("password") or payload.get("access_token") or "").strip()
    if not presented:
        return err("password is required")

    token_hash = hash_access_token(presented)
    participant = session.scalar(
        select(Participant).where(Participant.access_token_hash == token_hash)
    )
    username = str(payload.get("username") or payload.get("pseudonymous_code") or "").strip()
    if participant is None or (username and participant.pseudonymous_code != username):
        # Audited without a participant id, since none was reliably identified. Neither the
        # presented password nor the presented username is ever recorded, only that an attempt
        # failed — recording a rejected username would let the audit log itself become the
        # probing surface it exists to catch.
        audit(session, "research_login_failed", reason="unrecognised credentials")
        session.commit()
        return err("username or password not recognised")

    if not participant.is_active:
        # A distinct message is safe here: it is only reachable once the FULL credential pair
        # already matched, so it discloses nothing to an attacker who does not already hold a
        # valid token.
        audit(session, "research_login_failed", participant_id=participant.participant_id,
              reason="account deactivated")
        session.commit()
        return err("this account has been deactivated; contact an administrator")

    audit(session, "research_login", participant_id=participant.participant_id,
          role=participant.role)
    session.commit()

    view = _participant_view(session, participant)
    view["session_token"] = mint_session(participant.participant_id, secret, ttl)
    view["ok"] = True
    return view


# ---------------------------------------------------------------- Google SSO (operational only)


def verify_google_id_token(credential: str) -> dict[str, Any] | None:
    """
    Verify a Google-issued ID token's signature, issuer and audience server-side, using the
    google-auth library already pinned for the A2 Drive adapter — no new dependency.

    Returns the verified claims, or None for ANY failure (bad signature, wrong audience,
    expired, malformed, no GOOGLE_CLIENT_ID configured, network error reaching Google). The
    caller only ever branches on None vs a dict; it never needs to distinguish why verification
    failed, and folding every failure into one outcome is what keeps a_researchssologin from
    accidentally growing a second, weaker path.

    A bare module-level function, not a method, so a test can replace
    research_identity.verify_google_id_token with a stub before exercising a_researchssologin
    through the real /exec endpoint — the only practical way to prove the SSO ROUTING (account
    lookup, the research-account refusal, the operational success path) without a live Google
    account and a real interactive consent screen, which cannot be scripted.
    """
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
    if not client_id or not credential:
        return None
    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token as google_id_token
    except ImportError:
        return None
    try:
        return google_id_token.verify_oauth2_token(
            credential, google_requests.Request(), client_id
        )
    except Exception:  # noqa: BLE001 — any verification failure is just "not verified"
        return None


def a_researchssologin(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Google SSO, for operational users only.

    Refuses outright for an account whose account_type is research (Guarantee 3): a participant
    who happens to sign in to the browser with a personal Google account elsewhere must not be
    able to reach their research identity that way, because that identity is deliberately
    pseudonymous and SSO always carries a real email.

    No self-registration: an unrecognised Google account is refused, not provisioned. The only
    way an operational account exists is adminparticipantcreate or adminlinkgoogle.
    """
    credential = str(payload.get("credential") or "").strip()
    if not credential:
        return err("credential is required")

    claims = verify_google_id_token(credential)
    email = str((claims or {}).get("email") or "").strip().lower()
    if not claims or not email or claims.get("email_verified") is False:
        audit(session, "sso_login_failed", reason="token could not be verified")
        session.commit()
        return err("Google sign-in could not be verified")

    participant = session.scalar(
        select(Participant).where(func.lower(Participant.google_email) == email)
    )
    if participant is None:
        # Deliberately no email in the audit row: it belongs to whoever tried to sign in, who is
        # by definition not yet a party this system has any record of.
        audit(session, "sso_login_no_account", reason="no participant linked to this Google account")
        session.commit()
        return err("this Google account is not registered on the platform; contact an "
                   "administrator")

    if participant.account_type == "research":
        # Guarantee 3. The explanation names the correct path rather than just refusing, because
        # the likely cause is a participant reaching for the familiar Google button out of habit.
        audit(session, "sso_login_denied_research_account", participant_id=participant.participant_id)
        session.commit()
        return err("research accounts sign in with the username and password supplied by the "
                   "researcher, not Google Sign-In")

    if not participant.is_active:
        audit(session, "sso_login_failed", participant_id=participant.participant_id,
              reason="account deactivated")
        session.commit()
        return err("this account has been deactivated; contact an administrator")

    audit(session, "sso_login", participant_id=participant.participant_id,
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

    # B8 account separation, enforced at source: an operational account can never obtain a
    # consents row, so the B2 consent gate blocks every research write for it. This is
    # structural, not procedural — no username convention is involved.
    if caller.participant.account_type == "operational":
        audit(session, "consent_denied_operational", participant_id=caller.participant_id)
        session.commit()
        return err("operational accounts cannot grant research consent: this account is not "
                   "a research participant")

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

    account_type = str(payload.get("account_type") or "research")
    if account_type not in ("research", "operational"):
        return err("account_type must be 'research' or 'operational'")

    # T2: an admin may supply the initial password/token (so it can be communicated through
    # whatever out-of-band channel the researcher already uses), or leave it to be generated —
    # same shown-once contract either way.
    supplied = str(payload.get("password") or "").strip()
    plaintext, token_hash = (supplied, hash_access_token(supplied)) if supplied \
        else issue_access_token()

    google_email = str(payload.get("google_email") or "").strip().lower() or None
    if google_email and session.scalar(
            select(Participant).where(func.lower(Participant.google_email) == google_email)):
        return err("this Google account is already linked to another participant")

    code = str(payload.get("pseudonymous_code") or "").strip() or _next_code(session)
    if session.scalar(select(Participant).where(Participant.pseudonymous_code == code)):
        return err(f"pseudonymous_code already in use: {code}")

    participant = Participant(
        pseudonymous_code=code,
        role=role,
        account_type=account_type,
        access_token_hash=token_hash,
        # display_name and google_email are meaningful only for an operational account; a
        # research participant's only identifier stays the pseudonymous code regardless of what
        # is passed here, so nothing checks account_type before storing them — the UI is
        # responsible for only offering the field for operational accounts, and nothing reads a
        # research account's display_name anywhere.
        display_name=(str(payload.get("display_name")).strip()
                     if payload.get("display_name") else None),
        google_email=google_email,
        eligibility_status=payload.get("eligibility_status"),
        scenario_set=payload.get("scenario_set"),
        condition_sequence=payload.get("condition_sequence"),
        order_group=payload.get("order_group"),
        completion_status="not_started",
    )
    session.add(participant)
    session.flush()
    audit(session, "participant_created", participant_id=participant.participant_id,
          created_by=caller.participant_id, role=role, pseudonymous_code=code,
          account_type=account_type, google_email_linked=bool(google_email))
    session.commit()

    return {
        "ok": True,
        "participant_id": participant.participant_id,
        "pseudonymous_code": code,
        "role": role,
        "account_type": account_type,
        "display_name": participant.display_name,
        "google_email": google_email,
        # Returned exactly once. Only its hash is stored, so it cannot be recovered later.
        "access_token": plaintext,
        "password": plaintext,  # same value, named for the UI's "password" framing
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

    # Local import: features.py imports audit/resolve_caller from this module at load time, so
    # importing it back at module scope here would be circular. See features.py's own note on
    # the same constraint.
    from .features import effective_features

    rows = session.scalars(select(Participant).order_by(Participant.pseudonymous_code)).all()
    # No access_token_hash in this projection: rule 2.
    return {"ok": True, "participants": [
        {
            "participant_id": p.participant_id,
            "pseudonymous_code": p.pseudonymous_code,
            "role": p.role,
            "account_type": p.account_type,
            "is_active": p.is_active,
            "display_name": p.display_name,
            "google_email": p.google_email,
            "eligibility_status": p.eligibility_status,
            "current_scenario": p.current_scenario,
            "current_stage": derived_stage(session, p.participant_id),
            "completion_status": p.completion_status,
            "consent": consent_state(session, p.participant_id),
            # The effective flags, already resolved against the account_type default — so an
            # admin looking at a research row with nothing configured sees all four as false
            # without having to know the default rule exists.
            "features": effective_features(session, p),
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


def a_adminaccounttypeset(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Change an existing account's type. An admin action, and audited: retyping an account moves
    it across the research/operational boundary, which is exactly the change the audit trail
    must be able to reconstruct.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    if not caller.is_admin:
        audit(session, "admin_action_denied", participant_id=caller.participant_id,
              action="adminaccounttypeset", role=caller.role)
        session.commit()
        return err("not authorised: ResearchAdmin role required")

    target_id = str(payload.get("participant_id") or "").strip()
    account_type = str(payload.get("account_type") or "").strip()
    if not target_id:
        return err("participant_id is required")
    if account_type not in ("research", "operational"):
        return err("account_type must be 'research' or 'operational'")

    target = session.get(Participant, target_id)
    if target is None:
        return err(f"participant not found: {target_id}")

    previous = target.account_type
    target.account_type = account_type
    audit(session, "account_type_changed", participant_id=target_id,
          changed_by=caller.participant_id, from_type=previous, to_type=account_type)
    session.commit()
    return {"ok": True, "participant_id": target_id,
            "account_type": account_type, "previous_account_type": previous}


def _require_admin(session: Session, payload: dict, secret: str, action: str):
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return None, problem
    if not caller.is_admin:
        audit(session, "admin_action_denied", participant_id=caller.participant_id,
              action=action, role=caller.role)
        session.commit()
        return None, err("not authorised: ResearchAdmin role required")
    return caller, None


def a_setpassword(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Admin-only password reset. Shown once, same contract as creation: only the hash is stored,
    so a lost password is reset, never recovered.
    """
    caller, problem = _require_admin(session, payload, secret, "setpassword")
    if problem:
        return problem

    target_id = str(payload.get("participant_id") or "").strip()
    if not target_id:
        return err("participant_id is required")
    target = session.get(Participant, target_id)
    if target is None:
        return err(f"participant not found: {target_id}")

    supplied = str(payload.get("password") or "").strip()
    plaintext = supplied or secrets.token_urlsafe(24)
    target.access_token_hash = hash_access_token(plaintext)
    # Never the plaintext: the audit trail records that a reset happened and by whom, which is
    # what makes a later "who could have known this password" question answerable, without the
    # audit log itself becoming a second place the password is stored.
    audit(session, "password_reset", participant_id=target_id, reset_by=caller.participant_id)
    session.commit()

    return {"ok": True, "participant_id": target_id, "password": plaintext,
            "access_token": plaintext,
            "password_notice": "Shown once. It is stored hashed and cannot be retrieved again."}


def a_setactive(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Activate or deactivate an account. Refuses to deactivate the last active ResearchAdmin —
    surfaced as its own clear message (Part 4), not folded into a generic refusal, because the
    admin needs to know WHY, not just that the click did nothing.
    """
    caller, problem = _require_admin(session, payload, secret, "setactive")
    if problem:
        return problem

    target_id = str(payload.get("participant_id") or "").strip()
    if not target_id:
        return err("participant_id is required")
    target = session.get(Participant, target_id)
    if target is None:
        return err(f"participant not found: {target_id}")

    raw = payload.get("is_active")
    if not isinstance(raw, bool):
        return err("is_active must be true or false")

    if raw is False and target.role == ROLE_ADMIN and target.is_active:
        remaining = session.scalar(
            select(func.count()).select_from(Participant).where(
                Participant.role == ROLE_ADMIN,
                Participant.is_active.is_(True),
                Participant.participant_id != target_id,
            )
        )
        if not remaining:
            audit(session, "deactivate_denied_last_admin", participant_id=target_id,
                  attempted_by=caller.participant_id)
            session.commit()
            return err("cannot deactivate the last active administrator")

    previous = target.is_active
    target.is_active = raw
    audit(session, "account_activated" if raw else "account_deactivated",
          participant_id=target_id, changed_by=caller.participant_id, previous=previous)
    session.commit()
    return {"ok": True, "participant_id": target_id, "is_active": raw}


def a_adminlinkgoogle(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Set or clear the Google account an operational participant signs in with. Also how the
    FIRST admin bootstraps SSO for themselves after this migration lands: sign in with the
    existing access token, then link a Google account to that same admin row — no direct
    database access required.
    """
    caller, problem = _require_admin(session, payload, secret, "adminlinkgoogle")
    if problem:
        return problem

    target_id = str(payload.get("participant_id") or "").strip()
    if not target_id:
        return err("participant_id is required")
    target = session.get(Participant, target_id)
    if target is None:
        return err(f"participant not found: {target_id}")

    email = str(payload.get("google_email") or "").strip().lower() or None
    if email:
        clash = session.scalar(
            select(Participant).where(func.lower(Participant.google_email) == email,
                                      Participant.participant_id != target_id)
        )
        if clash is not None:
            return err("this Google account is already linked to another participant")

    target.google_email = email
    audit(session, "google_email_linked" if email else "google_email_unlinked",
          participant_id=target_id, changed_by=caller.participant_id)
    session.commit()
    return {"ok": True, "participant_id": target_id, "google_email": email}


IDENTITY_ACTIONS: dict[str, Callable[[Session, dict, str, int], dict]] = {
    "researchlogin": a_researchlogin,
    "researchssologin": a_researchssologin,
    "researchwhoami": a_researchwhoami,
    "consentgrant": a_consentgrant,
    "consentwithdraw": a_consentwithdraw,
    "adminparticipantcreate": a_adminparticipantcreate,
    "adminparticipantlist": a_adminparticipantlist,
    "adminaccounttypeset": a_adminaccounttypeset,
    "researchparticipantget": a_researchparticipantget,
    "setpassword": a_setpassword,
    "setactive": a_setactive,
    "adminlinkgoogle": a_adminlinkgoogle,
}
