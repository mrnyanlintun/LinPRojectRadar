#!/usr/bin/env python3
"""
T1 verification: same-origin static serving and per-user feature flags.

Proves the server-side guarantees through the real ASGI app:

  1. /healthz and /readyz still answer 200 after the static mount, and the SPA is served.
  4. A research account with empty features has all four flags disabled; an operational account
     with empty features has all four enabled.
  5. A disabled feature's action is refused server-side when called directly, and audited.
  6. Portfolio health is refused while the pre-judgment is unlocked, even with health_dialog on.

Guarantees 2, 3 and 7 are proved outside this file — 2 and 7 in the browser (they are about
origins and fetch policy), 3 by the repository search — and are reported in the PR.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_features.py
"""

from __future__ import annotations

import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
from app.features import FEATURE_KEYS  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import Assignment, AuditEvent, Participant  # noqa: E402

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


def get(params: dict) -> dict:
    r = client.get("/exec", params=params)
    assert r.status_code == 200
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


ADMIN = "t1-bootstrap-admin"
PROJECT = "PRJ-T1A"
with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="PM-000", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PROJECT)) is None:
        s.add(Project(legacy_id=PROJECT, doc={"id": PROJECT, "name": "T1 project"}))
    s.commit()
admin_login = post({"action": "researchlogin", "access_token": ADMIN})
admin = admin_login["session_token"]
admin_id = admin_login["participant_id"]

print("=" * 78)
print("GUARANTEE 1: health endpoints survive the static mount; the SPA is served")
print("=" * 78)

r = client.get("/healthz")
check(r.status_code == 200 and r.json().get("status") == "ok",
      "/healthz returns 200 after the static mount", f"HTTP {r.status_code}")
r = client.get("/readyz")
check(r.status_code == 200 and r.json().get("status") == "ready",
      "/readyz returns 200 after the static mount", f"HTTP {r.status_code} {r.text[:120]}")
schema = next((c for c in client.get("/readyz").json()["checks"] if c["name"] == "schema"), {})
# Not pinned to a literal revision id: that would make this check fail at every later migration
# for a reason unrelated to what it's actually verifying (that /readyz agrees the schema is
# current). schema.ok already reports pass/fail against whatever head alembic computes.
check(schema.get("ok") is True, "schema reports itself at head", str(schema))

r = client.get("/")
check(r.status_code == 200 and "<!doctype html>" in r.text[:200].lower(),
      "GET / serves the SPA", f"HTTP {r.status_code}")
check("Opus Gubernatio" in r.text and "<title>Opus Gubernatio" in r.text,
      "served SPA carries the rebranded title")
r = client.get("/assets/js/config.js")
check(r.status_code == 200 and 'window.LIN_API_URL = "/exec"' in r.text,
      "the served config points at the same-origin /exec", f"HTTP {r.status_code}")
# The static routes are exact-path; nothing can fall through to them.
check(client.get("/exec", params={"action": "ping"}).json().get("ok") is True,
      "/exec still dispatches after the mount")
check(client.get("/definitely-not-a-route").status_code == 404,
      "no catch-all static route swallows unknown paths")

print()
print("=" * 78)
print("GUARANTEE 4: defaults fail safe, derived from account_type")
print("=" * 78)


def make(account_type=None):
    body = {"action": "adminparticipantcreate", "session_token": admin}
    if account_type:
        body["account_type"] = account_type
    c = post(body)
    tok = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
    return c, tok


res_p, res_tok = make()
ops_p, ops_tok = make("operational")

r = post({"action": "researchmyfeatures", "session_token": res_tok})
check(r.get("ok") is True and r["account_type"] == "research",
      "research account created with empty features", str(r)[:160])
check(all(r["features"][k] is False for k in FEATURE_KEYS),
      "research + empty features -> all four DISABLED", str(r.get("features")))

r = post({"action": "researchmyfeatures", "session_token": ops_tok})
check(all(r["features"][k] is True for k in FEATURE_KEYS),
      "operational + empty features -> all four ENABLED", str(r.get("features")))

with Session() as s:
    stored = s.execute(
        select(Participant).where(Participant.participant_id == res_p["participant_id"])
    ).scalar_one()
check(stored is not None, "participant row exists")
r = post({"action": "adminfeaturesget", "session_token": admin,
          "participant_id": res_p["participant_id"]})
check(r.get("stored") == {}, "nothing was written to features; the defaults are derived",
      str(r.get("stored")))

# An explicit set wins over the default, and only for the keys named.
r = post({"action": "adminfeaturesset", "session_token": admin,
          "participant_id": res_p["participant_id"], "features": {"chat": True}})
check(r.get("ok") is True and r["effective"]["chat"] is True,
      "admin enabled chat for the research account", str(r)[:200])
check(all(r["effective"][k] is False for k in FEATURE_KEYS if k != "chat"),
      "the other three keys stay at the restrictive default", str(r.get("effective")))
# This used to be `audit_rows("features_set", changed_by=None) == [] or any(...)`.
# features.py:317 always writes changed_by=caller.participant_id, a real ULID, never None, so
# the left side of the `or` is `[] == []` on every possible run and the right side — the only
# part that reads real content — never executes. It would pass even if features_set were never
# audited at all.
#
# Filtered by changed_by, not participant_id: `audit()` stores participant_id on AuditEvent's
# own COLUMN, so it is never inside event_metadata and audit_rows (which only reads
# event_metadata) can never match it — that trap was caught running this fix, not by inspection.
# changed_by IS passed through **metadata and is real content: every field the audit call writes
# is checked against the values this exact request should have produced.
rows = audit_rows("features_set", changed_by=admin_id)
check(any(m.get("applied") == {"chat": True} and m.get("previous") == {}
          and m.get("now_stored") == {"chat": True} for m in rows),
      "the change is audited with who changed it, the previous state and the new state",
      str(rows))

r = post({"action": "adminfeaturesset", "session_token": admin,
          "participant_id": res_p["participant_id"], "features": {"telepathy": True}})
check(r.get("ok") is False and "unknown feature key" in (r.get("error") or ""),
      "an unrecognised key is refused, not stored", str(r)[:160])
r = post({"action": "adminfeaturesset", "session_token": admin,
          "participant_id": res_p["participant_id"], "features": {"chat": "yes"}})
check(r.get("ok") is False and "true or false" in (r.get("error") or ""),
      "a non-boolean value is refused", str(r)[:160])
r = post({"action": "adminfeaturesset", "session_token": res_tok,
          "participant_id": res_p["participant_id"], "features": {"auditor": True}})
check(r.get("ok") is False and "ResearchAdmin" in (r.get("error") or ""),
      "a non-admin cannot set flags", str(r)[:160])

print()
print("=" * 78)
print("GUARANTEE 5: a disabled feature is refused server-side, bypassing the UI")
print("=" * 78)

# A fresh research account, so all four flags sit at the restrictive default.
g5_p, g5_tok = make()
before = len(audit_rows("feature_denied"))
for action, feature in (("chat", "chat"), ("audit", "auditor"),
                        ("knowledgeget", "knowledge_library"),
                        ("getportfoliohealth", "health_dialog")):
    r = post({"action": action, "session_token": g5_tok})
    # getportfoliohealth is a GET action; posting it proves the gate fires BEFORE dispatch,
    # since an ungated POST would have returned "Unknown POST action" instead.
    check(r.get("ok") is False and "disabled for this account" in (r.get("error") or ""),
          f"{action} refused for the research account ({feature} off)", str(r)[:160])
denied = audit_rows("feature_denied")
check(len(denied) - before == 4, "each refusal is audited", str(len(denied) - before))
check({m.get("feature") for m in denied} >= {"chat", "auditor", "knowledge_library",
                                             "health_dialog"},
      "the audit records which feature was refused",
      str(sorted({m.get('feature') for m in denied})))

# The GET path is gated too, not only POST.
r = get({"action": "getportfoliohealth", "session_token": g5_tok})
check(r.get("ok") is False and "disabled" in (r.get("error") or ""),
      "the GET path is gated as well as POST", str(r)[:160])

# chat is enabled for this account, so the gate lets it through to the dispatcher, which
# reports it as deferred. That is the proof the gate passed rather than silently allowing.
r = post({"action": "chat", "session_token": res_tok, "question": "hello"})
check("not implemented in this build" in (r.get("error") or ""),
      "an ENABLED feature passes the gate and reaches dispatch", str(r)[:160])
r = post({"action": "audit", "session_token": ops_tok})
check("not implemented in this build" in (r.get("error") or ""),
      "operational account passes the auditor gate", str(r)[:160])

print()
print("=" * 78)
print("GUARANTEE 6: portfolio health is refused while the pre-judgment is unlocked")
print("=" * 78)

scenario = post({"action": "adminscenariocreate", "session_token": admin,
                 "scenario_version": "t1-v1", "period_count": 1,
                 "evidence_package_id": PROJECT})["scenario_id"]
post({"action": "adminconfigurationcreate", "session_token": admin, "code": "C1",
      "version": "v1", "freeze": True})
post({"action": "adminsequencecreate", "session_token": admin, "order_group": "GT1",
      "scenario_set": "SET-T1", "version": "v1", "positions": ["C1"], "freeze": True})
pkg = post({"action": "adminpackagecreate", "session_token": admin, "version": "t1-pkg",
            "recommended_action": "Escalate", "freeze": True})

pm_p, pm_tok = make()
post({"action": "consentgrant", "session_token": pm_tok, "consent_version": "v1.0"})
# T4: a_researchprejudgment now requires a completed intake questionnaire.
post({"action": "intakesave", "session_token": pm_tok,
      "responses": {"experience_level": "mid", "years_experience": 8}})
post({"action": "adminassign", "session_token": admin, "participant_id": pm_p["participant_id"],
      "order_group": "GT1", "scenario_set": "SET-T1", "scenario_ids": [scenario]})
with Session() as s:
    aid = s.scalar(select(Assignment).where(
        Assignment.participant_id == pm_p["participant_id"])).assignment_id
post({"action": "adminpackageattach", "session_token": admin, "assignment_id": aid,
      "package_id": pkg["package_id"]})
post({"action": "adminmemberadd", "session_token": admin, "id": PROJECT,
      "participant_id": pm_p["participant_id"], "project_role": "PM"})

# health_dialog explicitly ENABLED, so the only thing that can refuse is the lock condition.
r = post({"action": "adminfeaturesset", "session_token": admin,
          "participant_id": pm_p["participant_id"], "features": {"health_dialog": True}})
check(r["effective"]["health_dialog"] is True, "health_dialog explicitly enabled for the PM",
      str(r.get("effective")))

r = get({"action": "getportfoliohealth", "session_token": pm_tok})
check(r.get("ok") is False and "preliminary judgment" in (r.get("error") or ""),
      "portfolio health refused while the pre-judgment is unlocked", str(r)[:200])
check(len(audit_rows("health_denied_unlocked", project_id=PROJECT)) >= 1,
      "the refusal is audited against the project")
body = json.dumps(r)
check("Escalate" not in body, "the refusal carries no analysis content")

post({"action": "researchevidenceget", "session_token": pm_tok})
locked = post({"action": "researchprejudgment", "session_token": pm_tok,
               "pre_action": "monitor", "pre_confidence": 55})
check(locked.get("pre_judgment_locked") is True, "PM locked the pre-judgment", str(locked)[:160])

r = get({"action": "getportfoliohealth", "session_token": pm_tok})
check(r.get("ok") is True, "portfolio health readable once the pre-judgment is locked",
      str(r)[:200])

# And with the flag off it is refused again, whatever the lock says.
post({"action": "adminfeaturesset", "session_token": admin,
      "participant_id": pm_p["participant_id"], "features": {"health_dialog": False}})
r = get({"action": "getportfoliohealth", "session_token": pm_tok})
check(r.get("ok") is False and "disabled for this account" in (r.get("error") or ""),
      "flag off refuses even after the lock", str(r)[:160])

# A SESSIONLESS read is now REFUSED, and this check used to assert the opposite.
#
# It read "a sessionless facade call is unaffected (pre-existing posture)", which was true and was
# the hole: gate_action deliberately leaves sessionless callers alone because an anonymous caller
# has no flags to apply, so an anonymous GET of getportfoliohealth bypassed the feature gate that
# a signed-in user with the flag OFF is held to. The read guard one layer up now refuses it, so
# the flag can no longer be evaded by presenting no credential at all.
r = get({"action": "getportfoliohealth"})
check(r.get("ok") is False and "session token" in (r.get("error") or ""),
      "a sessionless facade read is refused, so the feature gate cannot be bypassed by "
      "dropping the credential", str(r)[:120])
check("results" not in r, "and the refusal carries no snapshot payload", str(sorted(r)))

# THE CREDENTIAL CARRIER FOR READS. A token in a URL is logged by every intermediary that logs
# URLs, so the header is the mechanism and the query string is a fallback kept only for the one
# caller that cannot set headers (the document-viewer iframe). All three are asserted here, and
# they are written defensively — `.get(...)` rather than indexing — because a broken header
# reader would otherwise make this suite CRASH instead of fail, and a crash prints no RESULT line
# and reads as clean. That failure mode is on the record from the previous two sessions.
_pf_tok = pm_tok
_pf_flag = post({"action": "adminfeaturesset", "session_token": admin,
                 "participant_id": pm_p["participant_id"],
                 "features": {"health_dialog": True}})
check(_pf_flag.get("ok") is True,
      "precondition: the reader's health_dialog flag is on, so a refusal below cannot be the "
      "feature gate rather than the credential", str(_pf_flag)[:110])


def _read_health(headers):
    r = client.get("/exec", params={"action": "getportfoliohealth"}, headers=headers)
    assert r.status_code == 200
    return r.json()


check(_read_health({"Authorization": "Bearer " + _pf_tok}).get("ok") is True,
      "a read authenticated by the Authorization: Bearer header succeeds",
      str(_read_health({"Authorization": "Bearer " + _pf_tok}))[:110])
check(_read_health({"X-Session-Token": _pf_tok}).get("ok") is True,
      "and by the X-Session-Token header")
check(get({"action": "getportfoliohealth", "session_token": _pf_tok}).get("ok") is True,
      "and by the query-string fallback, which the iframe viewer still needs")
check(_read_health({"Authorization": "Bearer not-a-real-token"}).get("ok") is False,
      "a Bearer header carrying a bad token is refused, not ignored",
      str(_read_health({"Authorization": "Bearer not-a-real-token"}))[:110])
check(_read_health({"Authorization": _pf_tok}).get("ok") is False,
      "and a token sent WITHOUT the Bearer scheme is not accepted by accident",
      str(_read_health({"Authorization": _pf_tok}))[:110])

print()
print("=" * 78)
print("T6: project creation is refused for a research account, by account_type")
print("=" * 78)

# The researcher creates a participant's project together with its assignment. A participant who
# could create their own would hold a project the decision sequence cannot act on, because the
# sequence is keyed to assignments. This is enforced in gate_action, before dispatch, for the
# same reason the flags above are: hiding the control is not enforcement.

pc_res, pc_res_tok = make()
pc_ops, pc_ops_tok = make("operational")

for action, body in (("projectcreate", {"name": "Research Attempt"}),
                     ("create", {"id": "PRJ-RESEARCH-ATTEMPT", "name": "Research Attempt"})):
    r = post(dict(body, action=action, session_token=pc_res_tok))
    check(r.get("ok") is False and "created by the researcher" in (r.get("error") or ""),
          f"research account refused {action}", str(r)[:160])

# The refusal is audited, so an attempt is visible rather than merely blocked. Two attempts were
# made above, so two rows must exist for this participant specifically — a count over the whole
# table would pass even if the rows belonged to someone else.
with Session() as s:
    denied = s.scalars(select(AuditEvent).where(
        AuditEvent.event_type == "project_creation_denied",
        AuditEvent.participant_id == pc_res["participant_id"])).all()
check(len(denied) == 2, "both refusals are audited against that participant",
      f"{len(denied)} row(s)")

# Operational keeps it: a director running a real project is exactly who creates one.
r = post({"action": "projectcreate", "session_token": pc_ops_tok, "name": "Operational Project"})
check(r.get("ok") is True, "operational account may still create a project", str(r)[:160])

# A SESSIONLESS create is now REFUSED, and this check used to assert the opposite.
#
# It read "a sessionless create is unaffected by the account-type gate", which was true and was
# the defect: guard_project_write returned allow whenever no session token was present, so any
# unauthenticated caller could create — and rename, archive, reset — any project on the deployed
# site. The account-type gate genuinely does leave sessionless callers alone (it has no caller to
# type-check), so the refusal below comes from the write guard, one layer up. Both are correct:
# no session, no write.
r = post({"action": "create", "id": "PRJ-SESSIONLESS-T6", "name": "Sessionless"})
check(r.get("ok") is False and "not authorized" in (r.get("error") or ""),
      "a sessionless create is refused by the write guard", str(r)[:120])
with Session() as s:
    leaked = s.scalar(select(Project).where(Project.legacy_id == "PRJ-SESSIONLESS-T6"))
check(leaked is None, "and no project row was created by the anonymous attempt",
      str(leaked))

print()
print("=" * 78)
passed = sum(1 for ok, _, _ in results if ok)
print(f"RESULT: {passed}/{len(results)} checks passed")
print("=" * 78)
sys.exit(0 if passed == len(results) else 1)
