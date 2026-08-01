#!/usr/bin/env python3
"""
B8 verification: project membership, observer role, and account separation.

Eight guarantees, each proven through the /exec HTTP surface:

  1. A non-member cannot read a project, its documents, or its computed results. Refused, audited.
  2. An observer cannot submit a pre-judgment, reveal, decide, advance, or upload. Each refused
     separately, each audited.
  3. An observer cannot read the recommendation package before the project's PM has locked their
     pre-judgment — and the refusal leaks nothing: the body is grepped for the recommendation
     text, alternatives, detected condition, package_id and hash.
  4. After the PM locks and reveals, an observer reads the same package the PM sees.
  5. Adding a second PM fails at the application AND at the database when the application layer
     is bypassed with raw SQL.
  6. An operational account cannot obtain a consent row, and therefore cannot write to any
     consent-gated table.
  7. An export over a range containing a research and an operational participant, both present
     and active, returns only the research participant's rows.
  8. Revoking a member removes access immediately; the membership row persists with revoked_at.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_membership.py
"""

from __future__ import annotations

import json
import sys
import time

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select, text  # noqa: E402

import app.main as main  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import (  # noqa: E402
    Assignment, AuditEvent, Consent, Participant, ProjectMember, new_ulid,
)

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


def audit_count(event_type: str, **meta) -> int:
    with Session() as s:
        rows = s.scalars(select(AuditEvent).where(AuditEvent.event_type == event_type)).all()
    if not meta:
        return len(rows)
    n = 0
    for r in rows:
        m = r.event_metadata or {}
        if all(m.get(k) == v for k, v in meta.items()):
            n += 1
    return n


# ---------------------------------------------------------------- seed

ADMIN = "b8-bootstrap-admin"
PROJECT = "PRJ-B8A"
# Distinctive markers: if any of these ever appears in a refusal body, the gate leaks.
MARK_ACTION = "ZQMARK-ESCALATE-77"
MARK_COND = "ZQMARK-CONDITION-88"
MARK_ALT = "ZQMARK-ALTERNATIVE-99"

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="PM-000", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    for legacy in (PROJECT, "ST-B8-NEXT"):
        if s.scalar(select(Project).where(Project.legacy_id == legacy)) is None:
            s.add(Project(legacy_id=legacy,
                          doc={"id": legacy, "name": f"B8 {legacy}",
                               "signals": {"evm": {"cpi": 0.9}},
                               "simulationSignals": {"signal_array": []}}))
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]

print("=" * 78)
print("SEED: project, scenario, frozen package, PM + Observer + outsider + operational")
print("=" * 78)

scenario = post({"action": "adminscenariocreate", "session_token": admin,
                 "scenario_version": "b8-v1", "period_count": 1,
                 "evidence_package_id": PROJECT})["scenario_id"]
post({"action": "adminconfigurationcreate", "session_token": admin, "code": "C1",
      "version": "v1", "freeze": True})
post({"action": "adminsequencecreate", "session_token": admin, "order_group": "G8",
      "scenario_set": "SET-B8", "version": "v1", "positions": ["C1"], "freeze": True})
pkg = post({"action": "adminpackagecreate", "session_token": admin, "version": "b8-pkg",
            "provider_id": "frozen-store", "recommended_action": MARK_ACTION,
            "detected_condition": MARK_COND, "alternatives": {"alt1": MARK_ALT},
            "freeze": True})
check(bool(pkg.get("hash")), "package frozen with hash")


def make_participant(**kw):
    c = post(dict({"action": "adminparticipantcreate", "session_token": admin}, **kw))
    tok = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
    return c, tok


def assign(participant_id):
    post({"action": "adminassign", "session_token": admin, "participant_id": participant_id,
          "order_group": "G8", "scenario_set": "SET-B8", "scenario_ids": [scenario]})
    with Session() as s:
        aid = s.scalar(select(Assignment).where(
            Assignment.participant_id == participant_id)).assignment_id
    post({"action": "adminpackageattach", "session_token": admin, "assignment_id": aid,
          "package_id": pkg["package_id"]})
    return aid


pm, pm_tok = make_participant()
obs, obs_tok = make_participant()
out, out_tok = make_participant()          # never a member of PROJECT
ops, ops_tok = make_participant(account_type="operational")

post({"action": "consentgrant", "session_token": pm_tok, "consent_version": "v1.0"})
post({"action": "consentgrant", "session_token": obs_tok, "consent_version": "v1.0"})
# T4: a_researchprejudgment now requires a completed intake questionnaire. Only the PM needs
# it — the observer's attempt is refused by the PM check, which runs first, so their refusal
# message stays the role message rather than becoming a questionnaire message.
post({"action": "intakesave", "session_token": pm_tok,
      "responses": {"experience_level": "mid", "years_experience": 8}})
assign(pm["participant_id"])
assign(obs["participant_id"])  # the observer has their own assignment on the same scenario

r = post({"action": "adminmemberadd", "session_token": admin, "id": PROJECT,
          "participant_id": pm["participant_id"], "project_role": "PM"})
check(r.get("ok") is True, "PM membership added", str(r)[:160])
r = post({"action": "adminmemberadd", "session_token": admin, "id": PROJECT,
          "participant_id": obs["participant_id"], "project_role": "Observer"})
check(r.get("ok") is True, "Observer membership added", str(r)[:160])

print()
print("=" * 78)
print("GUARANTEE 1: a non-member cannot read the project, documents, or results")
print("=" * 78)

for action in ("researchprojectget", "researchprojectdocs", "researchprojectresults",
               "researchprojectmembers"):
    r = post({"action": action, "session_token": out_tok, "id": PROJECT})
    check(r.get("ok") is False and "not a member" in (r.get("error") or ""),
          f"non-member {action} refused", str(r)[:160])
check(audit_count("project_access_denied", project_id=PROJECT) >= 4,
      "non-member attempts audited",
      str(audit_count("project_access_denied", project_id=PROJECT)))

r = post({"action": "researchmyprojects", "session_token": out_tok})
check(r.get("ok") is True and r.get("projects") == [],
      "researchmyprojects never lists a project the caller is not a member of", str(r)[:160])

print()
print("=" * 78)
print("GUARANTEE 2: an observer cannot pre-judge, reveal, decide, advance, or upload")
print("=" * 78)

denied_before = audit_count("pm_only_action_denied")
r = post({"action": "researchprejudgment", "session_token": obs_tok,
          "pre_action": "monitor", "pre_confidence": 50})
check(r.get("ok") is False and "only the project's PM" in (r.get("error") or ""),
      "observer researchprejudgment refused", str(r)[:160])
r = post({"action": "researchreveal", "session_token": obs_tok})
check(r.get("ok") is False and "only the project's PM" in (r.get("error") or ""),
      "observer researchreveal refused", str(r)[:160])
r = post({"action": "researchdecision", "session_token": obs_tok,
          "final_action": "monitor", "disposition": "accept"})
check(r.get("ok") is False and "only the project's PM" in (r.get("error") or ""),
      "observer researchdecision refused", str(r)[:160])
r = post({"action": "researchadvance", "session_token": obs_tok})
check(r.get("ok") is False and "only the project's PM" in (r.get("error") or ""),
      "observer researchadvance refused", str(r)[:160])
r = post({"action": "save", "session_token": obs_tok, "id": PROJECT,
          "project": {"id": PROJECT, "name": "observer edit"}})
check(r.get("ok") is False and "only the project's PM" in (r.get("error") or ""),
      "observer upload/save refused", str(r)[:160])
check(audit_count("pm_only_action_denied") - denied_before == 5,
      "each observer attempt audited separately (5 events)",
      str(audit_count("pm_only_action_denied") - denied_before))

print()
print("=" * 78)
print("GUARANTEE 3: package unreadable before the PM locks — and the refusal leaks nothing")
print("=" * 78)

r = post({"action": "researchpackageget", "session_token": obs_tok, "id": PROJECT})
check(r.get("ok") is False, "observer package read refused before PM lock", str(r)[:160])
body = json.dumps(r)
for name, needle in (("recommendation text", MARK_ACTION),
                     ("detected condition", MARK_COND),
                     ("alternatives", MARK_ALT),
                     ("package_id", pkg["package_id"]),
                     ("hash", pkg["hash"])):
    check(needle not in body, f"refusal body does not leak the {name}")
check(audit_count("package_read_denied_unlocked", project_id=PROJECT) >= 1,
      "pre-lock package read attempt audited")

print()
print("=" * 78)
print("GUARANTEE 4: after the PM locks and reveals, the observer sees the same package")
print("=" * 78)

post({"action": "researchevidenceget", "session_token": pm_tok})
r = post({"action": "researchprejudgment", "session_token": pm_tok,
          "pre_action": "monitor", "pre_confidence": 60})
check(r.get("ok") is True and r.get("pre_judgment_locked") is True,
      "PM (as project PM) can lock a pre-judgment", str(r)[:200])
pm_reveal = post({"action": "researchreveal", "session_token": pm_tok})
check(pm_reveal.get("ok") is True and pm_reveal.get("package", {}).get(
    "recommended_action") == MARK_ACTION, "PM reveal returns the package", str(pm_reveal)[:160])

obs_read = post({"action": "researchpackageget", "session_token": obs_tok, "id": PROJECT})
check(obs_read.get("ok") is True, "observer can now read the package", str(obs_read)[:200])
check(obs_read.get("package") == pm_reveal.get("package"),
      "observer sees exactly the package the PM sees")
check(audit_count("project_read", action="researchpackageget", project_id=PROJECT) >= 1,
      "observer package read audited")

print()
print("=" * 78)
print("GUARANTEE 5: a second active PM fails — application and raw SQL both")
print("=" * 78)

r = post({"action": "adminmemberadd", "session_token": admin, "id": PROJECT,
          "participant_id": out["participant_id"], "project_role": "PM"})
check(r.get("ok") is False and "already has an active PM" in (r.get("error") or ""),
      "application refuses a second active PM", str(r)[:160])

# Reuse the stored representation of project_id from an existing membership row, so the raw
# INSERT targets exactly the same project value the index sees, on any dialect.
with Session() as s:
    raw_project_id = s.execute(
        text("SELECT project_id FROM project_members LIMIT 1")).scalar_one()
raised = None
try:
    with Session() as s:
        s.execute(
            text("INSERT INTO project_members "
                 "(member_id, project_id, user_key, project_role, added_by) "
                 "VALUES (:m, :p, :u, 'PM', 'raw-sql-bypass')"),
            {"m": new_ulid(), "p": raw_project_id, "u": out["participant_id"]},
        )
        s.commit()
except Exception as exc:  # noqa: BLE001
    raised = exc
check(raised is not None and "unique" in str(raised).lower(),
      "database rejects a second active PM inserted with raw SQL (partial unique index)",
      str(raised)[:200])

print()
print("=" * 78)
print("GUARANTEE 6: an operational account cannot consent, so gated writes fail at source")
print("=" * 78)

r = post({"action": "consentgrant", "session_token": ops_tok, "consent_version": "v1.0"})
check(r.get("ok") is False and "operational" in (r.get("error") or ""),
      "consentgrant refused for the operational account", str(r)[:160])
with Session() as s:
    n = len(s.scalars(select(Consent).where(
        Consent.participant_id == ops["participant_id"])).all())
check(n == 0, "no consent row exists for the operational account", str(n))
check(audit_count("consent_denied_operational",) >= 1, "refusal audited")

r = post({"action": "adminassign", "session_token": admin,
          "participant_id": ops["participant_id"],
          "order_group": "G8", "scenario_set": "SET-B8", "scenario_ids": [scenario]})
check(r.get("ok") is False and "consent required" in (r.get("error") or ""),
      "consent-gated write (assignments) blocked for the operational account", str(r)[:160])

print()
print("=" * 78)
print("GUARANTEE 7: an export returns only the research participant's rows")
print("=" * 78)

# PM (research) completes their decision in the range.
r = post({"action": "researchdecision", "session_token": pm_tok, "final_action": "monitor",
          "disposition": "accept", "final_confidence": 70, "rationale": "b8 research row"})
check(r.get("ok") is True, "research participant completed a decision", str(r)[:160])

# A second participant completes a decision as research, then is retyped operational — both are
# therefore present and active in the range, and the retype is itself an audited admin action.
# They work on a SECOND, unmembered project (pre-B8 style), so the membership guard does not
# apply to them — the export filter alone must exclude their rows.
scenario2 = post({"action": "adminscenariocreate", "session_token": admin,
                  "scenario_version": "b8-v2", "period_count": 1,
                  "evidence_package_id": "ST-B8-NEXT"})["scenario_id"]
ops2, ops2_tok = make_participant()
post({"action": "consentgrant", "session_token": ops2_tok, "consent_version": "v1.0"})
# T4: a_researchprejudgment now requires a completed intake questionnaire.
post({"action": "intakesave", "session_token": ops2_tok,
      "responses": {"experience_level": "mid", "years_experience": 8}})
post({"action": "adminassign", "session_token": admin, "participant_id": ops2["participant_id"],
      "order_group": "G8", "scenario_set": "SET-B8", "scenario_ids": [scenario2]})
with Session() as s:
    aid2 = s.scalar(select(Assignment).where(
        Assignment.participant_id == ops2["participant_id"])).assignment_id
post({"action": "adminpackageattach", "session_token": admin, "assignment_id": aid2,
      "package_id": pkg["package_id"]})
post({"action": "researchevidenceget", "session_token": ops2_tok})
post({"action": "researchprejudgment", "session_token": ops2_tok, "pre_action": "monitor",
      "pre_confidence": 50})
post({"action": "researchreveal", "session_token": ops2_tok})
r = post({"action": "researchdecision", "session_token": ops2_tok, "final_action": "escalate",
          "disposition": "modify", "final_confidence": 65, "rationale": "b8 operational row"})
check(r.get("ok") is True, "second participant completed a decision in the range", str(r)[:160])
r = post({"action": "adminaccounttypeset", "session_token": admin,
          "participant_id": ops2["participant_id"], "account_type": "operational"})
check(r.get("ok") is True and r.get("account_type") == "operational",
      "account retyped operational by audited admin action", str(r)[:160])
check(audit_count("account_type_changed") >= 1, "account type change audited")

exp = post({"action": "adminexportcreate", "session_token": admin, "format": "json"})
check(exp.get("ok") is True, "export created", str(exp)[:160])
fetched = post({"action": "adminexportfetch", "session_token": admin,
                "export_id": exp["export_id"]})
payload = fetched.get("payload") or ""
codes = {row["pseudonymous_code"] for row in json.loads(payload)["rows"]}
check(pm["pseudonymous_code"] in codes,
      "research participant's rows are present", str(codes))
check(ops2["pseudonymous_code"] not in codes,
      "operational participant's rows are absent", str(codes))
check(ops2["pseudonymous_code"] not in payload,
      "operational code appears nowhere in the payload")

print()
print("=" * 78)
print("GUARANTEE 8: revocation removes access immediately; the row persists")
print("=" * 78)

members = post({"action": "adminmemberlist", "session_token": admin, "id": PROJECT})
obs_member = next(m for m in members["members"]
                  if m["user_key"] == obs["participant_id"] and m["active"])
r = post({"action": "adminmemberrevoke", "session_token": admin,
          "member_id": obs_member["member_id"]})
check(r.get("ok") is True and r.get("revoked_at"), "observer membership revoked", str(r)[:160])

r = post({"action": "researchprojectget", "session_token": obs_tok, "id": PROJECT})
check(r.get("ok") is False and "not a member" in (r.get("error") or ""),
      "revoked observer can no longer read the project", str(r)[:160])
r = post({"action": "researchpackageget", "session_token": obs_tok, "id": PROJECT})
check(r.get("ok") is False, "revoked observer can no longer read the package", str(r)[:160])

members = post({"action": "adminmemberlist", "session_token": admin, "id": PROJECT})
row = next(m for m in members["members"] if m["member_id"] == obs_member["member_id"])
check(row["revoked_at"] is not None and row["active"] is False,
      "membership row persists with revoked_at set", str(row)[:200])
with Session() as s:
    check(s.get(ProjectMember, obs_member["member_id"]) is not None,
          "row still present in project_members (never deleted)")

print()
print("=" * 78)
passed = sum(1 for ok, _, _ in results if ok)
print(f"RESULT: {passed}/{len(results)} checks passed")
print("=" * 78)
sys.exit(0 if passed == len(results) else 1)
