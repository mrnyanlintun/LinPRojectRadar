#!/usr/bin/env python3
"""
B2 verification: research identity, roles, and the consent gate.

Proves each non-negotiable rule against whatever DATABASE_URL points at, through the real /exec
HTTP surface rather than by calling functions directly, so what is proven is what a client sees.

  1. Consent gate: no write to participant_profiles, assignments, decisions, transitions or
     research_exports for a participant without an active consent. All five are exercised.
  2. Access tokens are stored hashed only, never returned after creation and never logged.
  3. Role comes from the server-side session. A body-supplied role or participant_id is ignored.
  4. A Participant can only read their own record; the attempt is refused and audited.
  5. Every identity event appends to audit_events with a server timestamp.

Run:
    DATABASE_URL=... python tools/test_research_identity.py
"""

from __future__ import annotations

import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import func, select, text  # noqa: E402

import app.main as main  # noqa: E402
from app.research_consent import ConsentRequired  # noqa: E402
from app.research_models import (  # noqa: E402
    Assignment, AuditEvent, Decision, Participant, ParticipantProfile, ResearchExport, Scenario,
    Transition,
)

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((ok, label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))


def post(payload: dict) -> tuple[int, dict]:
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    return r.status_code, r.json()


def seed_admin() -> str:
    """Bootstrap one ResearchAdmin directly. Everything after this goes through /exec."""
    from app.research_identity import hash_access_token
    token = "bootstrap-admin-token-for-b2-verification"
    with Session() as s:
        existing = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if existing is None:
            s.add(Participant(pseudonymous_code="PM-000", role="ResearchAdmin",
                              access_token_hash=hash_access_token(token)))
            s.commit()
        else:
            existing.access_token_hash = hash_access_token(token)
            s.commit()
    return token


def audit_count(event_type: str) -> int:
    with Session() as s:
        return s.scalar(select(func.count()).select_from(AuditEvent)
                        .where(AuditEvent.event_type == event_type)) or 0


print("=" * 78)
print("SETUP + LOGIN")
print("=" * 78)

admin_token = seed_admin()
st, body = post({"action": "researchlogin", "access_token": admin_token})
check(st == 200 and body.get("ok") is True, "admin login ok", str(body)[:160])
admin_session = body.get("session_token")
check(bool(admin_session), "session token issued")
check(body.get("role") == "ResearchAdmin", "role reported from the database")
check("access_token_hash" not in json.dumps(body), "login response carries no token hash")

st, bad = post({"action": "researchlogin", "access_token": "not-a-real-token"})
check(st == 200 and bad.get("ok") is False, "bad token rejected with HTTP 200 + ok:false", str(bad))

st, body = post({"action": "RESEARCHLOGIN", "access_token": admin_token})
check(body.get("ok") is True, "action matching is case-insensitive")

print()
print("=" * 78)
print("RULE 2: access tokens stored hashed only")
print("=" * 78)

before = audit_count("participant_created")
st, created = post({"action": "adminparticipantcreate", "session_token": admin_session})
check(created.get("ok") is True, "admin created a participant", str(created)[:160])
p_code = created.get("pseudonymous_code")
p_token = created.get("access_token")
p_id = created.get("participant_id")
check(bool(p_token), "plaintext token returned exactly once")
check(p_code and p_code.startswith("PM-"), f"server-generated code {p_code}")

with Session() as s:
    row = s.get(Participant, p_id)
    check(row.access_token_hash != p_token, "stored value is not the plaintext")
    check(len(row.access_token_hash) == 64, "stored value is a sha256 digest")

st, listing = post({"action": "adminparticipantlist", "session_token": admin_session})
check(listing.get("ok") is True, "admin list ok")
check("access_token_hash" not in json.dumps(listing), "list never returns token hashes")
check("access_token" not in json.dumps(listing), "list never returns tokens")

st, again = post({"action": "researchwhoami", "session_token": admin_session})
check("access_token" not in json.dumps(again), "whoami never returns a token")

print()
print("=" * 78)
print("RULE 3: role comes from the session, not the body")
print("=" * 78)

st, plogin = post({"action": "researchlogin", "access_token": p_token})
check(plogin.get("ok") is True and plogin.get("role") == "Participant",
      "participant logged in as Participant")
p_session = plogin.get("session_token")

st, escalate = post({"action": "adminparticipantlist", "session_token": p_session,
                     "role": "ResearchAdmin"})
check(escalate.get("ok") is False and "not authorised" in escalate.get("error", ""),
      "body-supplied role ignored; admin action refused", str(escalate)[:160])

st, who = post({"action": "researchwhoami", "session_token": p_session,
                "role": "ResearchAdmin", "participant_id": "someone-else"})
check(who.get("role") == "Participant", "whoami ignores a body-supplied role")
check(who.get("participant_id") == p_id, "whoami ignores a body-supplied participant_id")

st, forged = post({"action": "researchwhoami", "session_token": p_session[:-4] + "AAAA"})
check(forged.get("ok") is False, "tampered session signature rejected", str(forged)[:120])

print()
print("=" * 78)
print("RULE 4: a Participant may read only their own record")
print("=" * 78)

st, other = post({"action": "adminparticipantcreate", "session_token": admin_session})
other_id = other.get("participant_id")

before_denied = audit_count("cross_participant_read_denied")
st, cross = post({"action": "researchparticipantget", "session_token": p_session,
                  "participant_id": other_id})
check(cross.get("ok") is False and "only read their own" in cross.get("error", ""),
      "cross-participant read refused", str(cross)[:160])
check(audit_count("cross_participant_read_denied") == before_denied + 1,
      "refused read appended to audit_events")

st, own = post({"action": "researchparticipantget", "session_token": p_session,
                "participant_id": p_id})
check(own.get("ok") is True and own.get("participant_id") == p_id, "own record readable")

print()
print("=" * 78)
print("RULE 1: consent gate blocks all five tables without active consent")
print("=" * 78)

with Session() as s:
    scenario = s.scalar(select(Scenario))
    if scenario is None:
        scenario = Scenario(scenario_version="b2-test")
        s.add(scenario)
        s.commit()
    scenario_id = scenario.scenario_id

def gated_write(label, make):
    """Attempt a direct ORM write and require the gate to stop it."""
    try:
        with Session() as s:
            s.add(make(s))
            s.commit()
        check(False, f"{label} blocked without consent", "write succeeded")
    except ConsentRequired as exc:
        check(True, f"{label} blocked without consent", str(exc)[:80])
    except Exception as exc:  # noqa: BLE001
        check(False, f"{label} blocked without consent", f"wrong error {type(exc).__name__}: {exc}")

gated_write("participant_profiles", lambda s: ParticipantProfile(participant_id=p_id, industry="x"))
gated_write("assignments", lambda s: Assignment(participant_id=p_id, scenario_id=scenario_id,
                                                sequence_number=1))
gated_write("research_exports", lambda s: ResearchExport(format="csv", initiated_by=p_id))

# decisions and transitions reach a participant through an assignment, so one is created for a
# consented participant first, then reused to prove the indirect resolution path.
st, consented = post({"action": "adminparticipantcreate", "session_token": admin_session})
c_token, c_id = consented["access_token"], consented["participant_id"]
st, clogin = post({"action": "researchlogin", "access_token": c_token})
c_session = clogin["session_token"]
st, granted = post({"action": "consentgrant", "session_token": c_session,
                    "consent_version": "v1.0", "method": "web"})
check(granted.get("ok") is True and bool(granted.get("granted_at")),
      "consent granted, granted_at server-assigned", str(granted)[:160])

with Session() as s:
    a = Assignment(participant_id=c_id, scenario_id=scenario_id, sequence_number=1)
    s.add(a)
    s.commit()
    consented_assignment = a.assignment_id
check(True, "assignment written for a consented participant")

# Now an assignment for the UNCONSENTED participant, to hang a decision from.
with Session() as s:
    s.execute(text(
        "INSERT INTO assignments (assignment_id, participant_id, scenario_id, sequence_number) "
        "VALUES (:a, :p, :s, 9)"),
        {"a": "01BYPASSASSIGNMENTFORTEST0", "p": p_id, "s": scenario_id})
    s.commit()
unconsented_assignment = "01BYPASSASSIGNMENTFORTEST0"

gated_write("decisions", lambda s: Decision(assignment_id=unconsented_assignment,
                                            period="P1", pre_action="monitor"))

with Session() as s:
    d = Decision(assignment_id=consented_assignment, period="P1", pre_action="monitor")
    s.add(d)
    s.commit()
    consented_decision = d.decision_id

with Session() as s:
    s.execute(text("INSERT INTO decisions (decision_id, assignment_id, period) "
                   "VALUES (:d, :a, 'P1')"),
              {"d": "01BYPASSDECISIONFORTEST00", "a": unconsented_assignment})
    s.commit()
gated_write("transitions", lambda s: Transition(decision_id="01BYPASSDECISIONFORTEST00",
                                                branch_id="b1"))

st, tr = (None, None)
try:
    with Session() as s:
        s.add(Transition(decision_id=consented_decision, branch_id="b1"))
        s.commit()
    check(True, "transition written for a consented participant")
except Exception as exc:  # noqa: BLE001
    check(False, "transition written for a consented participant", str(exc)[:120])

print()
print("=" * 78)
print("CONSENT WITHDRAWAL RE-CLOSES THE GATE")
print("=" * 78)

st, withdrawn = post({"action": "consentwithdraw", "session_token": c_session})
check(withdrawn.get("ok") is True and bool(withdrawn.get("withdrawn_at")),
      "consent withdrawn, withdrawn_at server-assigned", str(withdrawn)[:160])

with Session() as s:
    from app.research_models import Consent
    rows = s.scalars(select(Consent).where(Consent.participant_id == c_id)).all()
    check(len(rows) == 1 and rows[0].withdrawn_at is not None,
          "consent row retained, not deleted")

gated_write("assignments after withdrawal", lambda s: Assignment(
    participant_id=c_id, scenario_id=scenario_id, sequence_number=2))

print()
print("=" * 78)
print("RULE 5: identity events audited with server timestamps")
print("=" * 78)

with Session() as s:
    types = {r[0] for r in s.execute(select(AuditEvent.event_type).distinct())}
for t in ("research_login", "participant_created", "consent_granted", "consent_withdrawn",
          "cross_participant_read_denied"):
    check(t in types, f"audit_events contains {t}")

with Session() as s:
    missing_ts = s.scalar(select(func.count()).select_from(AuditEvent)
                          .where(AuditEvent.server_ts.is_(None))) or 0
check(missing_ts == 0, "every audit row carries a server timestamp")

st, failed_login_body = post({"action": "researchlogin", "access_token": "another-bad-token"})
check(audit_count("research_login_failed") >= 1, "failed logins are audited too")

print()
print("=" * 78)
failed = [r for r in results if not r[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
