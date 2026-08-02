#!/usr/bin/env python3
"""
T7/T8 guarantees: admin operations (membership, assignment, monitoring, export) and the two
JSON-driven questionnaires — the server-verifiable half.

Run (from server/):

    DATABASE_URL=... SESSION_SECRET=... python tools/test_admin_ops_t7t8.py

Membership (adminmemberadd/revoke/list), assignment (adminassign/adminassignmentlist/
adminscenariocreate/list), and export (adminexportcreate/list/fetch) are B8/B3/B6 actions this
phase did NOT modify — what is proven here is that admin-ops.js's screens are built on the
actual server contract (exact refusal strings, exact field presence/absence) and that two
things genuinely new in this phase behave correctly: operational-account exclusion from export
(not previously covered by B6's own suite) and the two new questionnaire actions.

Guarantees 5, 8 and 10 are UI-rendering concerns (absence of a performance metric in the
rendered DOM, a JSON-definition edit changing the form on reload, absence of a module id in
rendered text) verified directly in a live browser session against a running instance of this
build — see the PR description for that transcript.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient
from sqlalchemy import select

import app.main as main
from app.research_identity import hash_access_token
from app.research_models import AuditEvent, Decision, Participant

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  — {detail}" if detail else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


ADMIN = "t7t8-admin"

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="T7T8-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]


def make_participant(code: str, account_type: str = "research") -> tuple[str, str]:
    created = post({"action": "adminparticipantcreate", "session_token": admin,
                    "pseudonymous_code": code, "role": "Participant",
                    "account_type": account_type})
    assert created.get("ok"), created
    token = post({"action": "researchlogin",
                  "access_token": created["access_token"]})["session_token"]
    return created["participant_id"], token


print("=" * 78)
print("T7/T8 — admin operations and questionnaires")
print("=" * 78)


# ---------------------------------------------------------------- Guarantee 1

print("\nGuarantee 1 — a non-admin cannot reach any admin action; refused and audited")
non_admin_id, non_admin = make_participant("T7T8-NONADMIN")


def audit_count(event_type: str) -> int:
    with Session() as s:
        return len(s.scalars(select(AuditEvent).where(
            AuditEvent.event_type == event_type)).all())


before_admin = audit_count("admin_action_denied")
before_export = audit_count("export_action_denied")
membership_and_assignment = [
    ("adminmemberadd", {"id": "PRJ-X", "participant_id": non_admin_id, "project_role": "PM"}),
    ("adminmemberlist", {"id": "PRJ-X"}),
    ("adminmemberrevoke", {"member_id": "x"}),
    ("adminassign", {"participant_id": non_admin_id, "order_group": "G", "scenario_set": "S",
                     "scenario_ids": ["x"]}),
    ("adminassignmentlist", {}),
    ("adminscenariocreate", {"scenario_version": "v1"}),
]
export_actions = [
    ("adminexportcreate", {}),
    ("adminexportlist", {}),
    ("adminexportfetch", {"export_id": "x"}),
]
for action, extra in membership_and_assignment + export_actions:
    resp = post(dict({"action": action, "session_token": non_admin}, **extra))
    check(resp.get("ok") is False, f"{action} refused for a non-admin", str(resp)[:90])
after_admin = audit_count("admin_action_denied")
after_export = audit_count("export_action_denied")
# research_export.py's own _require_admin audits under a DIFFERENT event_type
# (export_action_denied) than research_membership.py / research_assignment.py's
# (admin_action_denied) — both audited, just two names for the same refusal shape.
check(after_admin >= before_admin + len(membership_and_assignment),
      "membership/assignment refusals audited as admin_action_denied",
      f"{before_admin} -> {after_admin}")
check(after_export >= before_export + len(export_actions),
      "export refusals audited as export_action_denied",
      f"{before_export} -> {after_export}")


# ---------------------------------------------------------------- Guarantee 2

print("\nGuarantee 2 — second active PM refused with a legible message")

# The facade fails closed on writes as of 2026-08-02, and `create` is additionally refused for a
# research account, so the fixture projects below are created by an OPERATIONAL participant.
_WRITER_TOKEN = "t7t8-writer"
_writer = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "T7T8-WRITER", "role": "Participant",
                "account_type": "operational"})
writer = post({"action": "researchlogin",
               "access_token": _writer["access_token"]})["session_token"]
proj_resp = post({"action": "create", "id": "PRJ-T7T8-A", "name": "T7T8 Membership Test",
                  "session_token": writer})
check(proj_resp.get("ok") is True, "test project created", str(proj_resp)[:100])

pm1_id, pm1 = make_participant("T7T8-PM1")
pm2_id, pm2 = make_participant("T7T8-PM2")
obs_id, obs = make_participant("T7T8-OBS")

add1 = post({"action": "adminmemberadd", "session_token": admin, "id": "PRJ-T7T8-A",
            "participant_id": pm1_id, "project_role": "PM"})
check(add1.get("ok") is True, "first PM added")
add2 = post({"action": "adminmemberadd", "session_token": admin, "id": "PRJ-T7T8-A",
            "participant_id": pm2_id, "project_role": "PM"})
check(add2.get("ok") is False, "second PM refused")
check(add2.get("error") == "this project already has an active PM; revoke them first",
      "refusal is the LITERAL B8 message, not a generic error", add2.get("error"))

add_obs = post({"action": "adminmemberadd", "session_token": admin, "id": "PRJ-T7T8-A",
               "participant_id": obs_id, "project_role": "Observer"})
check(add_obs.get("ok") is True, "an observer can be added alongside the PM")


# ---------------------------------------------------------------- Guarantee 3

print("\nGuarantee 3 — a revoked member loses access; the row persists and stays admin-visible")
before_list = post({"action": "adminmemberlist", "session_token": admin, "id": "PRJ-T7T8-A"})
obs_member = next(m for m in before_list["members"] if m["user_key"] == obs_id)
check(obs_member["active"] is True, "observer starts active")

revoke = post({"action": "adminmemberrevoke", "session_token": admin,
              "member_id": obs_member["member_id"]})
check(revoke.get("ok") is True, "revoke accepted")
check(revoke.get("revoked_at") not in (None, ""), "revoke response carries revoked_at")

obs_read = post({"action": "projectresults", "session_token": obs, "id": "PRJ-T7T8-A",
                 "period": 1})
check(obs_read.get("ok") is False, "the revoked observer immediately loses project access",
      str(obs_read)[:90])

after_list = post({"action": "adminmemberlist", "session_token": admin, "id": "PRJ-T7T8-A"})
obs_after = next(m for m in after_list["members"] if m["user_key"] == obs_id)
check(obs_after["active"] is False, "the row is still present, now inactive")
check(obs_after["revoked_at"] not in (None, ""), "revoked_at is set on the row")
check(len(after_list["members"]) == len(before_list["members"]),
      "the row was never deleted — same member count before and after")


# ---------------------------------------------------------------- Guarantee 4

print("\nGuarantee 4 — config_id/condition never in a participant-reachable response")
scenario = post({"action": "adminscenariocreate", "session_token": admin,
                 "scenario_version": "t7t8-v1"})
check(scenario.get("ok") is True, "scenario created")
cfg = post({"action": "adminconfigurationcreate", "session_token": admin,
           "code": "C0", "version": "v1", "label": "T7T8C0", "freeze": True})
check(cfg.get("ok") is True, "configuration created and frozen", str(cfg)[:120])
seq = post({"action": "adminsequencecreate", "session_token": admin, "order_group": "T7T8G",
           "scenario_set": "T7T8SET", "version": "v1", "positions": ["C0"], "freeze": True})
check(seq.get("ok") is True, "sequence created and frozen", str(seq)[:140])
post({"action": "consentgrant", "session_token": pm1, "consent_version": "t7t8-v1"})
assign = post({"action": "adminassign", "session_token": admin, "participant_id": pm1_id,
              "order_group": "T7T8G", "scenario_set": "T7T8SET",
              "scenario_ids": [scenario["scenario_id"]]})
check(assign.get("ok") is True, "assignment created", str(assign)[:120])
check("config_id" in assign["assignments"][0],
      "the ADMIN response (adminassign) legitimately carries config_id")

mine = post({"action": "researchmyassignments", "session_token": pm1})
body = json.dumps(mine)
check(mine.get("ok") is True, "participant can read their own assignments")
check("config_id" not in body, "config_id absent from the participant's own assignment view")
check("package_id" not in body, "package_id absent from the participant's own assignment view")

admin_list = post({"action": "adminassignmentlist", "session_token": admin,
                   "participant_id": pm1_id})
check("config_id" in json.dumps(admin_list),
      "config_id IS present in the admin-only list (not a leak — this route refuses "
      "every non-admin, per Guarantee 1)")


# ---------------------------------------------------------------- Guarantee 6

print("\nGuarantee 6 — export filters account_type='research' unconditionally")
op_id, op_token = make_participant("T7T8-OPERATIONAL", account_type="operational")
res_id, res_token = make_participant("T7T8-RESEARCH", account_type="research")

# An operational account structurally CANNOT grant research consent (B8:
# consent_denied_operational) and Assignment is consent-gated, so an operational participant
# can never reach adminassign through the normal path — which is the point of B8's account
# separation. That means an operational participant's data should never exist to filter in the
# first place. What this guarantee actually needs to prove is DEFENSE IN DEPTH: even if such a
# row existed (a bug elsewhere, a pre-B8 legacy row), the export filter still excludes it. So
# the operational participant's Assignment/Decision rows are seeded with raw SQL, deliberately
# bypassing the ORM before_flush consent gate that would otherwise refuse them — the research
# participant's rows go through the real adminassign path for contrast.
post({"action": "consentgrant", "session_token": res_token, "consent_version": "t7t8-v1"})

scenario2 = post({"action": "adminscenariocreate", "session_token": admin,
                  "scenario_version": "t7t8-export-v1"})
post({"action": "adminconfigurationcreate", "session_token": admin,
     "code": "C0", "version": "v1", "label": "T7T8EXPC0", "freeze": True})
post({"action": "adminsequencecreate", "session_token": admin, "order_group": "T7T8EXPORTG",
     "scenario_set": "T7T8EXPORTSET", "version": "v1", "positions": ["C0"],
     "freeze": True})

a = post({"action": "adminassign", "session_token": admin, "participant_id": res_id,
         "order_group": "T7T8EXPORTG", "scenario_set": "T7T8EXPORTSET",
         "scenario_ids": [scenario2["scenario_id"]]})
assert a.get("ok"), a
with Session() as s:
    from app.research_models import Assignment
    arow = s.scalar(select(Assignment).where(Assignment.participant_id == res_id))
    s.add(Decision(assignment_id=arow.assignment_id, period="P1", pre_action="HOLD",
                   pre_confidence=50, final_action="HOLD", final_confidence=50,
                   final_submitted_at=datetime.now(timezone.utc)))
    s.commit()

with Session() as s:
    from sqlalchemy import text
    op_assignment_id = "01T7T8OPERATIONALASSIGN01"
    now = datetime.now(timezone.utc).isoformat()
    s.execute(text(
        "INSERT INTO assignments (assignment_id, participant_id, scenario_id, sequence_number) "
        "VALUES (:a, :p, :sc, 1)"),
        {"a": op_assignment_id, "p": op_id, "sc": scenario2["scenario_id"]})
    # Raw SQL, not the ORM: Decision is ALSO consent-gated (resolved through its assignment's
    # participant), and an operational account can never hold consent by construction (B8).
    # Bypassing the ORM here is what proves the export filter is real defense in depth rather
    # than something that merely happens to agree with a gate that would refuse this anyway.
    s.execute(text(
        "INSERT INTO decisions (decision_id, assignment_id, period, pre_action, "
        "pre_confidence, final_action, final_confidence, final_submitted_at) "
        "VALUES (:d, :a, 'P1', 'HOLD', 50, 'HOLD', 50, :t)"),
        {"d": "01T7T8OPERATIONALDECISION1", "a": op_assignment_id, "t": now})
    s.commit()

exp = post({"action": "adminexportcreate", "session_token": admin,
           "date_from": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
           "date_to": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
           "format": "json"})
check(exp.get("ok") is True, "export created", str(exp)[:120])
fetched = post({"action": "adminexportfetch", "session_token": admin,
               "export_id": exp["export_id"]})
check(fetched.get("ok") is True, "export fetched and checksum-verified")
payload = json.loads(fetched["payload"])
rows = payload.get("rows", [])
# EXPORT_COLUMNS is an identity allowlist — pseudonymous_code, never participant_id — so the
# row is matched the same way the export itself de-identifies: by pseudonymous code.
op_present = any(r.get("pseudonymous_code") == "T7T8-OPERATIONAL" for r in rows)
res_present = any(r.get("pseudonymous_code") == "T7T8-RESEARCH" for r in rows)
check(op_present is False, "the operational participant's rows are ABSENT from the export")
check(res_present is True, "the research participant's rows ARE present",
      f"rows in range: {len(rows)}")


# ---------------------------------------------------------------- Guarantee 7

print("\nGuarantee 7 — a tampered export fails checksum verification, payload withheld")
with Session() as s:
    from app.research_models import Assignment
    arow = s.scalar(select(Assignment).where(Assignment.participant_id == res_id))
    drow = s.scalar(select(Decision).where(Decision.assignment_id == arow.assignment_id))
    drow.final_action = "TAMPERED-AFTER-EXPORT"
    s.commit()

tampered = post({"action": "adminexportfetch", "session_token": admin,
                 "export_id": exp["export_id"]})
check(tampered.get("ok") is False, "fetch fails after the underlying data changed",
      str(tampered)[:160])
check("checksum verification failed" in (tampered.get("error") or ""),
      "the failure names itself as a checksum verification failure")
check("payload" not in tampered, "no payload key at all on a checksum mismatch")


# ---------------------------------------------------------------- Guarantee 9 (server half)

print("\nGuarantee 9 — intake requires consent; debrief requires completion")
fresh_id, fresh = make_participant("T7T8-FRESH")
no_consent = post({"action": "intakesave", "session_token": fresh,
                   "responses": {"experience_level": "mid"}})
check(no_consent.get("ok") is False, "intake refused before consent", str(no_consent)[:100])

post({"action": "consentgrant", "session_token": fresh, "consent_version": "t7t8-v1"})
status_pre = post({"action": "profilestatus", "session_token": fresh})
check(status_pre.get("ok") is True, "profilestatus reads after consent")
check(status_pre["debrief_eligible"] is False,
      "debrief not eligible before any assignment exists",
      status_pre.get("debrief_eligibility_reason"))

debrief_too_early = post({"action": "debriefsave", "session_token": fresh,
                          "responses": {"expectation_to_agree": "4"}})
check(debrief_too_early.get("ok") is False, "debrief refused before eligibility",
      str(debrief_too_early)[:100])

intake_ok = post({"action": "intakesave", "session_token": fresh,
                  "responses": {"experience_level": "mid", "years_experience": 6,
                                "risk_attitude_general": "5"}})
check(intake_ok.get("ok") is True, "intake accepted once consented", str(intake_ok)[:100])

status_post = post({"action": "profilestatus", "session_token": fresh})
check(status_post["intake_completed"] is True, "profilestatus now reports intake complete")

with Session() as s:
    from app.research_models import ParticipantProfile
    prof = s.scalar(select(ParticipantProfile).where(
        ParticipantProfile.participant_id == fresh_id))
    check(prof is not None and prof.intake_responses.get("experience_level") == "mid",
          "raw intake_responses stored verbatim")
    check(prof is not None and prof.experience_level == "mid",
          "mapped narrow column also populated")
    check(prof is not None and prof.risk_attitude == {"risk_attitude_general": "5"},
          "risk_attitude items collected under the risk_attitude JSONB column")

# make the fresh participant eligible for debrief: one assignment, decision complete
scenario3 = post({"action": "adminscenariocreate", "session_token": admin,
                  "scenario_version": "t7t8-debrief-v1"})
post({"action": "adminconfigurationcreate", "session_token": admin,
     "code": "C0", "version": "v1", "label": "T7T8DBC0", "freeze": True})
post({"action": "adminsequencecreate", "session_token": admin, "order_group": "T7T8DEBRIEFG",
     "scenario_set": "T7T8DEBRIEFSET", "version": "v1", "positions": ["C0"],
     "freeze": True})
debrief_assign = post({"action": "adminassign", "session_token": admin,
                       "participant_id": fresh_id, "order_group": "T7T8DEBRIEFG",
                       "scenario_set": "T7T8DEBRIEFSET",
                       "scenario_ids": [scenario3["scenario_id"]]})
assert debrief_assign.get("ok"), debrief_assign
with Session() as s:
    from app.research_models import Assignment
    arow = s.scalar(select(Assignment).where(Assignment.participant_id == fresh_id))
    s.add(Decision(assignment_id=arow.assignment_id, period="P1", pre_action="HOLD",
                   pre_confidence=50, final_action="HOLD", final_confidence=50,
                   final_submitted_at=datetime.now(timezone.utc)))
    s.commit()

status_eligible = post({"action": "profilestatus", "session_token": fresh})
check(status_eligible["debrief_eligible"] is True,
      "debrief becomes eligible once the assignment's decision is complete")

debrief_ok = post({"action": "debriefsave", "session_token": fresh,
                   "responses": {"expectation_to_agree": "4",
                                "perceived_study_purpose": "testing AI decision support"}})
check(debrief_ok.get("ok") is True, "debrief accepted once eligible", str(debrief_ok)[:100])

status_final = post({"action": "profilestatus", "session_token": fresh})
check(status_final["debrief_completed"] is True, "profilestatus reports debrief complete")


# ---------------------------------------------------------------- definition sanity

print("\nQuestionnaire JSON definitions — structurally valid, marked placeholder")
import pathlib
repo_root = pathlib.Path(__file__).resolve().parents[2]
for name in ("intake.json", "debrief.json"):
    path = repo_root / "assets" / "questionnaires" / name
    check(path.is_file(), f"{name} exists at the expected path", str(path))
    definition = json.loads(path.read_text(encoding="utf-8"))
    check("PLACEHOLDER" in definition.get("note", "").upper(),
          f"{name} carries an explicit placeholder/not-final note")
    check(bool(definition.get("sections")), f"{name} has at least one section")
    types_seen = set()
    for section in definition["sections"]:
        for item in section["items"]:
            types_seen.add(item["type"])
    check({"single-select", "multi-select", "text", "likert", "numeric"} & types_seen,
          f"{name} exercises item types from the required set", str(types_seen))


# ---------------------------------------------------------------- tail

print()
print("=" * 78)
passed = sum(1 for ok, _, _ in results if ok)
for ok, label, detail in results:
    if not ok:
        print(f"  FAILED: {label}  {detail}")
print(f"RESULT: {passed}/{len(results)} checks passed")
print("=" * 78)
sys.exit(0 if passed == len(results) else 1)
