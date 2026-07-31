#!/usr/bin/env python3
"""
T2 verification: two sign-in paths, the consent gate, session resume, and admin management.

Proves the server half of the eight guarantees through the real /exec surface. The browser half
(the sign-in form, the consent screen blocking navigation, sessionStorage vs localStorage, the
admin UI) is proven separately in a live browser and reported in the PR; what is here is
everything that is decidable server-side, which is where every one of these rules is actually
enforced.

Google SSO is exercised by replacing research_identity.verify_google_id_token with a stub. The
real function verifies a signature against Google's live keys, which cannot be scripted without
a real interactive consent screen; the stub substitutes ONLY the "is this token genuinely from
Google" step, leaving the parts T2 actually adds — account lookup, the research-account refusal,
the deactivation check, session minting — running as written.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_auth_session.py
"""

from __future__ import annotations

import json
import sys
import time

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
import app.research_identity as ident  # noqa: E402
from app.research_models import AuditEvent, Participant  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((ok, label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


def audit_rows(event_type: str, **meta) -> list:
    with Session() as s:
        rows = s.scalars(select(AuditEvent).where(AuditEvent.event_type == event_type)).all()
    out = []
    for r in rows:
        m = r.event_metadata or {}
        if all(m.get(k) == v for k, v in meta.items()):
            out.append(m)
    return out


# ---------------------------------------------------------------- bootstrap admin

ADMIN_PW = "t2-bootstrap-admin-password"
with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="PM-000", role="ResearchAdmin",
                          access_token_hash=ident.hash_access_token(ADMIN_PW)))
    else:
        row.access_token_hash = ident.hash_access_token(ADMIN_PW)
        row.is_active = True
    s.commit()

login = post({"action": "researchlogin", "username": "PM-000", "password": ADMIN_PW})
admin = login["session_token"]

print("=" * 78)
print("GUARANTEE 1 (server half): password sign-in; consent gate closed until granted")
print("=" * 78)

created = post({"action": "adminparticipantcreate", "session_token": admin,
                "account_type": "research", "role": "Participant"})
p_code, p_pw = created["pseudonymous_code"], created["password"]
check(created.get("ok") is True and bool(p_pw), "admin created a research user", str(created)[:150])

r = post({"action": "researchlogin", "username": p_code, "password": p_pw})
check(r.get("ok") is True and bool(r.get("session_token")),
      "research participant signs in with username + password", str(r)[:150])
part = r["session_token"]
check(r.get("account_type") == "research", "login reports account_type for routing",
      str(r.get("account_type")))
check((r.get("consent") or {}).get("status") == "none",
      "consent not yet granted -> the frontend routes to the consent screen",
      str(r.get("consent")))

# The gate is real server-side, not merely a screen: a consent-gated write is refused.
gated = post({"action": "adminassign", "session_token": part, "participant_id": "x",
              "order_group": "G", "scenario_set": "S", "scenario_ids": []})
check(gated.get("ok") is False, "a consent-gated action is refused before consent", str(gated)[:150])

print()
print("=" * 78)
print("GUARANTEE 2 (server half): consent granted -> platform; resume without re-consent")
print("=" * 78)

g = post({"action": "consentgrant", "session_token": part, "consent_version": "placeholder-v0"})
check(g.get("ok") is True and bool(g.get("granted_at")), "consent recorded", str(g)[:150])

who = post({"action": "researchwhoami", "session_token": part})
check((who.get("consent") or {}).get("status") == "granted",
      "whoami now reports consent granted -> routed to the platform", str(who.get("consent")))
check(who.get("current_stage") == "evidence",
      "stage is server-derived and returned on resume", str(who.get("current_stage")))

# "Sign out and back in": a NEW login, i.e. a brand-new session token, must not re-prompt.
again = post({"action": "researchlogin", "username": p_code, "password": p_pw})
check(again.get("ok") is True and (again.get("consent") or {}).get("status") == "granted",
      "signing in again returns already-consented -> no second consent prompt",
      str(again.get("consent")))
check(again.get("current_stage") == who.get("current_stage"),
      "same stage on the new session: state resumed, not reset",
      f"{again.get('current_stage')} vs {who.get('current_stage')}")

print()
print("=" * 78)
print("GUARANTEE 3: Google SSO is refused for a research account")
print("=" * 78)

_real_verify = ident.verify_google_id_token
research_email = "participant.person@example.org"
ops_email = "vp.person@example.org"


def _stub(credential):
    # Stands in ONLY for Google's signature check; everything downstream runs as written.
    return {"email": credential, "email_verified": True} if credential else None


ident.verify_google_id_token = _stub

post({"action": "adminlinkgoogle", "session_token": admin,
      "participant_id": created["participant_id"], "google_email": research_email})
r = post({"action": "researchssologin", "credential": research_email})
check(r.get("ok") is False and "username and password" in (r.get("error") or ""),
      "SSO refused for a research account, with the correct path explained", str(r)[:180])
check(len(audit_rows("sso_login_denied_research_account")) >= 1, "refusal audited")
check("session_token" not in r, "no session is issued on refusal")

r = post({"action": "researchssologin", "credential": "nobody@example.org"})
check(r.get("ok") is False and "not registered" in (r.get("error") or ""),
      "an unknown Google account is refused, not auto-provisioned", str(r)[:150])

print()
print("=" * 78)
print("GUARANTEE 4: operational user signs in by SSO and is never consent-gated")
print("=" * 78)

ops = post({"action": "adminparticipantcreate", "session_token": admin,
            "account_type": "operational", "role": "Participant",
            "display_name": "Practising VP", "google_email": ops_email})
check(ops.get("ok") is True, "admin created an operational user with a Google link", str(ops)[:150])

r = post({"action": "researchssologin", "credential": ops_email})
check(r.get("ok") is True and bool(r.get("session_token")), "operational SSO sign-in succeeds",
      str(r)[:150])
check(r.get("account_type") == "operational",
      "reports operational -> the frontend skips the consent screen", str(r.get("account_type")))
ops_tok = r["session_token"]

# And the platform will not let an operational account consent even if asked directly.
r = post({"action": "consentgrant", "session_token": ops_tok, "consent_version": "placeholder-v0"})
check(r.get("ok") is False and "operational accounts cannot grant research consent" in (r.get("error") or ""),
      "an operational account cannot grant consent even by direct call", str(r)[:180])

ident.verify_google_id_token = _real_verify

print()
print("=" * 78)
print("GUARANTEE 5: a non-admin cannot reach the admin interface")
print("=" * 78)

before = len(audit_rows("admin_action_denied"))
for action in ("adminparticipantlist", "adminparticipantcreate", "setpassword", "setactive",
               "adminfeaturesget", "adminfeaturesset", "adminlinkgoogle"):
    r = post({"action": action, "session_token": part})
    check(r.get("ok") is False and "ResearchAdmin" in (r.get("error") or ""),
          f"non-admin refused: {action}", str(r)[:130])
denied = len(audit_rows("admin_action_denied")) - before
check(denied == 7, "every refused admin action is audited", str(denied))

print()
print("=" * 78)
print("GUARANTEE 6: the initial password is shown once and never retrievable")
print("=" * 78)

fresh = post({"action": "adminparticipantcreate", "session_token": admin,
              "account_type": "research", "role": "Participant"})
secret = fresh["password"]
check(bool(secret) and fresh.get("access_token") == secret,
      "creation returns the password exactly once", str(fresh)[:120])

listing = post({"action": "adminparticipantlist", "session_token": admin})
blob = json.dumps(listing)
check(secret not in blob, "the password does not appear in the user list")
check("access_token_hash" not in blob, "no password hash is ever exposed")
row = next(p for p in listing["participants"]
           if p["participant_id"] == fresh["participant_id"])
check("password" not in row and "access_token" not in row,
      "no password field on a listed user at all", str(sorted(row))[:200])

got = post({"action": "researchparticipantget", "session_token": admin,
            "participant_id": fresh["participant_id"]})
check(secret not in json.dumps(got), "the password is not retrievable by direct record read")

# Reset issues a NEW one, shown once; the old one stops working.
rs = post({"action": "setpassword", "session_token": admin,
           "participant_id": fresh["participant_id"]})
check(rs.get("ok") is True and bool(rs.get("password")) and rs["password"] != secret,
      "reset issues a new password, shown once", str(rs)[:120])
old = post({"action": "researchlogin", "username": fresh["pseudonymous_code"], "password": secret})
check(old.get("ok") is False, "the previous password no longer works", str(old)[:120])
new = post({"action": "researchlogin", "username": fresh["pseudonymous_code"],
            "password": rs["password"]})
check(new.get("ok") is True, "the new password works", str(new)[:120])

print()
print("=" * 78)
print("GUARANTEE 7: flags take effect; an unset flag shows the account_type default")
print("=" * 78)

f = post({"action": "adminfeaturesget", "session_token": admin,
          "participant_id": fresh["participant_id"]})
check(f.get("stored") == {} and all(v is False for v in f["effective"].values()),
      "research account, nothing set -> all four effective FALSE by default", str(f)[:180])
check(f.get("defaults_from_account_type") is False,
      "the default itself is reported so the admin can see the rule", str(f.get("defaults_from_account_type")))

fo = post({"action": "adminfeaturesget", "session_token": admin,
           "participant_id": ops["participant_id"]})
check(fo.get("stored") == {} and all(v is True for v in fo["effective"].values()),
      "operational account, nothing set -> all four effective TRUE by default", str(fo)[:180])

st = post({"action": "adminfeaturesset", "session_token": admin,
           "participant_id": fresh["participant_id"], "features": {"chat": True}})
check(st.get("ok") is True and st["effective"]["chat"] is True,
      "admin turned chat on for a research account", str(st)[:150])
check(all(st["effective"][k] is False for k in ("knowledge_library", "health_dialog", "auditor")),
      "the other three stay at the restrictive default", str(st.get("effective")))

# Take effect for THAT user, verified as that user.
me = post({"action": "researchmyfeatures", "session_token": new["session_token"]})
check(me["features"]["chat"] is True and me["features"]["auditor"] is False,
      "the user's own resolved flags reflect the admin's change", str(me.get("features")))
listed = next(p for p in post({"action": "adminparticipantlist", "session_token": admin})["participants"]
              if p["participant_id"] == fresh["participant_id"])
check(listed["features"]["chat"] is True,
      "the admin list shows effective flags inline", str(listed.get("features")))

print()
print("=" * 78)
print("GUARANTEE 8: no idle timeout; an idle session stays valid")
print("=" * 78)

idle_login = post({"action": "researchlogin", "username": p_code, "password": p_pw})
idle_tok = idle_login["session_token"]
first = post({"action": "researchwhoami", "session_token": idle_tok})
check(first.get("ok") is True, "session valid immediately after sign-in")

time.sleep(3)  # real elapsed idle time with zero requests in between
later = post({"action": "researchwhoami", "session_token": idle_tok})
check(later.get("ok") is True,
      "the same token still works after an idle gap with no activity", str(later)[:120])
check(later.get("current_stage") == first.get("current_stage"),
      "and resumes the same server-derived stage", str(later.get("current_stage")))

# The decisive structural point: the token's expiry is fixed at mint time and never shortened
# by inactivity. Nothing in the codebase re-issues or expires it early.
import base64 as _b64mod  # noqa: E402
body_seg = idle_tok.split(".")[0]
claims = json.loads(_b64mod.urlsafe_b64decode(body_seg + "=" * (-len(body_seg) % 4)))
lifetime = claims["exp"] - claims["iat"]
check(lifetime == main.settings.session_ttl_seconds,
      "token lifetime is exactly the configured TTL, set once at mint",
      f"{lifetime}s vs {main.settings.session_ttl_seconds}s")
check("idle" not in json.dumps(claims) and "last_seen" not in json.dumps(claims),
      "the token carries no idle/last-seen field that could expire it early", str(claims))

print()
print("=" * 78)
print("EXTRA: deactivation, and the last-admin protection")
print("=" * 78)

d = post({"action": "setactive", "session_token": admin,
          "participant_id": fresh["participant_id"], "is_active": False})
check(d.get("ok") is True and d.get("is_active") is False, "admin deactivated an account", str(d)[:120])
r = post({"action": "researchlogin", "username": fresh["pseudonymous_code"],
          "password": rs["password"]})
check(r.get("ok") is False and "deactivated" in (r.get("error") or ""),
      "a deactivated account cannot sign in", str(r)[:150])
r = post({"action": "researchwhoami", "session_token": new["session_token"]})
check(r.get("ok") is False and "deactivated" in (r.get("error") or ""),
      "and its EXISTING session stops working immediately", str(r)[:150])

with Session() as s:
    admin_row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin",
                                                   Participant.is_active.is_(True)))
    admin_id = admin_row.participant_id
r = post({"action": "setactive", "session_token": admin,
          "participant_id": admin_id, "is_active": False})
check(r.get("ok") is False and "last active administrator" in (r.get("error") or ""),
      "the last active administrator cannot be deactivated", str(r)[:150])
check(len(audit_rows("deactivate_denied_last_admin")) >= 1, "that refusal is audited")
check(post({"action": "researchwhoami", "session_token": admin}).get("ok") is True,
      "and the admin is still able to work")

print()
print("=" * 78)
passed = sum(1 for ok, _, _ in results if ok)
print(f"RESULT: {passed}/{len(results)} checks passed")
print("=" * 78)
sys.exit(0 if passed == len(results) else 1)
