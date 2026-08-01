#!/usr/bin/env python3
"""
B3 verification: assignment, counterbalancing, and blinding.

Everything is driven through the /exec HTTP surface, so what is proven is what a client can see,
not what a function happens to return.

Blinding rules proven:
  1. A Participant cannot fetch another participant's assignments, by any action, including by
     passing another participant_id in the body. Refused and audited.
  2. A Participant cannot fetch an assignment beyond their current sequence_number.
  3. A Participant response never contains config_id or any condition-revealing field.
  4. An unfrozen configuration cannot be assigned.
  5. The B2 consent gate still applies to assignment writes.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_assignment_blinding.py
"""

from __future__ import annotations

import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

import app.main as main  # noqa: E402
from app.research_consent import ConsentRequired  # noqa: E402
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


def audit_count(t: str) -> int:
    with Session() as s:
        return s.scalar(select(func.count()).select_from(AuditEvent)
                        .where(AuditEvent.event_type == t)) or 0


# ---------------------------------------------------------------- setup

ADMIN_TOKEN = "b3-bootstrap-admin"
with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="PM-000", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN_TOKEN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN_TOKEN)
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN_TOKEN})["session_token"]

print("=" * 78)
print("SETUP: scenarios, configurations, sequence")
print("=" * 78)

scenarios = []
for i in range(3):
    r = post({"action": "adminscenariocreate", "session_token": admin,
              "scenario_version": f"v1-s{i}", "project_type": "construction", "period_count": 2})
    scenarios.append(r["scenario_id"])
check(len(scenarios) == 3, "three scenarios created")

# C0 and C1 frozen; C2 deliberately left unfrozen to prove rule 4.
frozen = {}
for code in ("C0", "C1"):
    r = post({"action": "adminconfigurationcreate", "session_token": admin,
              "code": code, "version": "v1", "label": code, "freeze": True})
    frozen[code] = r["config_id"]
    check(r.get("ok") is True and r.get("frozen_at"), f"{code} created and frozen")

r = post({"action": "adminconfigurationcreate", "session_token": admin,
          "code": "C2", "version": "v1", "label": "C2"})
check(r.get("ok") is True and r.get("frozen_at") is None, "C2 created UNFROZEN")

r = post({"action": "adminconfigurationlist", "session_token": admin})
assignable = {c["code"]: c["assignable"] for c in r["configurations"]}
check(assignable == {"C0": True, "C1": True, "C2": False}, "list reports assignability",
      str(assignable))

print()
print("=" * 78)
print("COUNTERBALANCING: sequences are data")
print("=" * 78)

r = post({"action": "adminsequencecreate", "session_token": admin, "order_group": "G1",
          "scenario_set": "SET-A", "version": "v1", "positions": ["C0", "C1", "C0"],
          "freeze": True})
check(r.get("ok") is True, "sequence G1 created and frozen", str(r)[:140])

r = post({"action": "adminsequencecreate", "session_token": admin, "order_group": "G2",
          "scenario_set": "SET-A", "version": "v1", "positions": ["C1", "C0", "C1"],
          "freeze": True})
check(r.get("ok") is True, "sequence G2 created and frozen (different order)")

r = post({"action": "adminsequencecreate", "session_token": admin, "order_group": "G3",
          "scenario_set": "SET-A", "version": "v1", "positions": ["C0", "C2", "C0"],
          "freeze": True})
check(r.get("ok") is True, "sequence G3 created, references the unfrozen C2")

r = post({"action": "adminsequencecreate", "session_token": admin, "order_group": "G4",
          "scenario_set": "SET-A", "version": "v1", "positions": ["C0", "CX"]})
check(r.get("ok") is False and "unknown configuration codes" in r.get("error", ""),
      "sequence with an unknown code refused", str(r)[:140])

r = post({"action": "adminsequencelist", "session_token": admin})
check(len(r["sequences"]) == 9, f"sequence rows stored as data ({len(r['sequences'])} positions)")


def make_participant():
    c = post({"action": "adminparticipantcreate", "session_token": admin})
    login = post({"action": "researchlogin", "access_token": c["access_token"]})
    post({"action": "consentgrant", "session_token": login["session_token"],
          "consent_version": "v1.0", "method": "web"})
    return c["participant_id"], login["session_token"]


p1_id, p1 = make_participant()
p2_id, p2 = make_participant()

print()
print("=" * 78)
print("RULE 4: an unfrozen configuration cannot be assigned")
print("=" * 78)

r = post({"action": "adminassign", "session_token": admin, "participant_id": p1_id,
          "order_group": "G3", "scenario_set": "SET-A", "scenario_ids": scenarios})
check(r.get("ok") is False and "not frozen" in r.get("error", ""),
      "assignment using unfrozen C2 refused", str(r)[:160])
with Session() as s:
    n = s.scalar(select(func.count()).select_from(Assignment)
                 .where(Assignment.participant_id == p1_id)) or 0
check(n == 0, "no partial allocation was written", f"{n} rows")

print()
print("=" * 78)
print("ASSIGNMENT + DETERMINISM")
print("=" * 78)

a1 = post({"action": "adminassign", "session_token": admin, "participant_id": p1_id,
           "order_group": "G1", "scenario_set": "SET-A", "scenario_ids": scenarios})
check(a1.get("ok") is True, "participant 1 assigned under G1", str(a1)[:160])
check(a1.get("condition_sequence") == "C0,C1,C0", "G1 sequence applied",
      str(a1.get("condition_sequence")))
check(bool(a1.get("sequence_version")), "sequence version recorded")

a2 = post({"action": "adminassign", "session_token": admin, "participant_id": p2_id,
           "order_group": "G2", "scenario_set": "SET-A", "scenario_ids": list(reversed(scenarios))})
check(a2.get("condition_sequence") == "C1,C0,C1", "G2 sequence applied (counterbalanced)")
check([x["scenario_id"] for x in a1["assignments"]] == [x["scenario_id"] for x in a2["assignments"]],
      "scenario order is deterministic regardless of request order")

again = post({"action": "adminassign", "session_token": admin, "participant_id": p1_id,
              "order_group": "G1", "scenario_set": "SET-A", "scenario_ids": scenarios})
check(again.get("ok") is False and "already has assignments" in again.get("error", ""),
      "re-assignment refused rather than silently duplicating")

with Session() as s:
    ev = s.scalar(select(AuditEvent).where(AuditEvent.event_type == "participant_assigned")
                  .order_by(AuditEvent.server_ts))
    meta = ev.event_metadata or {}
check("allocation" in meta and len(meta["allocation"]) == 3,
      "allocation recorded in audit_events for reproducibility")
check(meta.get("sequence_version") is not None, "audit records the sequence version used")

print()
print("=" * 78)
print("RULE 3: participant responses never reveal the condition")
print("=" * 78)

mine = post({"action": "researchmyassignments", "session_token": p1})
blob = json.dumps(mine)
check(mine.get("ok") is True, "participant can read own assignments")
for leak in ("config_id", "config_code", "condition", "package_id", "order_group"):
    check(leak not in blob, f"response contains no {leak}")
if mine["assignments"]:
    check(set(mine["assignments"][0]) == {"sequence_number", "scenario_id", "status"},
          "assignment fields limited to the blind projection",
          str(set(mine["assignments"][0])))

cur = post({"action": "researchcurrent", "session_token": p1})
check("config_id" not in json.dumps(cur), "researchcurrent leaks no config_id")
check(cur.get("current_sequence_number") == 1, "current position is 1",
      str(cur.get("current_sequence_number")))

print()
print("=" * 78)
print("RULE 2: nothing beyond the current sequence_number")
print("=" * 78)

check(len(mine["assignments"]) == 1,
      "only the current assignment is visible, not all three",
      f"{len(mine['assignments'])} visible")
check(mine["assignments"][0]["sequence_number"] == 1, "visible row is position 1")

with Session() as s:
    a = s.scalar(select(Assignment).where(Assignment.participant_id == p1_id,
                                          Assignment.sequence_number == 1))
    a.status = "completed"
    s.commit()

mine2 = post({"action": "researchmyassignments", "session_token": p1})
check(mine2["current_sequence_number"] == 2, "current advances after completion")
check(len(mine2["assignments"]) == 2, "position 2 becomes visible, position 3 does not",
      f"{len(mine2['assignments'])} visible")
check(max(x["sequence_number"] for x in mine2["assignments"]) == 2, "position 3 still hidden")

print()
print("=" * 78)
print("RULE 1: no cross-participant access, by any action")
print("=" * 78)

before = audit_count("cross_participant_assignment_read_denied")

r = post({"action": "researchmyassignments", "session_token": p1, "participant_id": p2_id})
check(r.get("ok") is False and "only read their own" in r.get("error", ""),
      "researchmyassignments refuses another participant_id", str(r)[:140])

r = post({"action": "researchcurrent", "session_token": p1, "participant_id": p2_id})
check(r.get("ok") is False, "researchcurrent refuses another participant_id")

check(audit_count("cross_participant_assignment_read_denied") == before + 2,
      "both refusals appended to audit_events")

r = post({"action": "adminassignmentlist", "session_token": p1})
check(r.get("ok") is False and "not authorized" in r.get("error", ""),
      "participant cannot use the admin listing action")

r = post({"action": "adminassignmentlist", "session_token": p1, "role": "ResearchAdmin"})
check(r.get("ok") is False, "body-supplied role does not grant admin listing")

r = post({"action": "adminassignmentlist", "session_token": admin, "participant_id": p2_id})
check(r.get("ok") is True and all(a["participant_id"] == p2_id for a in r["assignments"]),
      "admin may list any participant's assignments")
check(any("config_id" in a for a in r["assignments"]), "admin view does include config_id")

print()
print("=" * 78)
print("RULE 5: consent gate still applies to assignment writes")
print("=" * 78)

unconsented = post({"action": "adminparticipantcreate", "session_token": admin})
u_id = unconsented["participant_id"]

r = post({"action": "adminassign", "session_token": admin, "participant_id": u_id,
          "order_group": "G1", "scenario_set": "SET-A", "scenario_ids": scenarios})
check(r.get("ok") is False and "consent required" in r.get("error", "").lower(),
      "assignment blocked for a participant without consent", str(r)[:160])

with Session() as s:
    n = s.scalar(select(func.count()).select_from(Assignment)
                 .where(Assignment.participant_id == u_id)) or 0
check(n == 0, "no assignment rows written without consent")

post({"action": "consentwithdraw", "session_token": p2})
r = post({"action": "adminassign", "session_token": admin, "participant_id": p2_id,
          "order_group": "G1", "scenario_set": "SET-A", "scenario_ids": scenarios})
check(r.get("ok") is False, "withdrawal re-closes the gate for assignment", str(r)[:140])

print()
print("=" * 78)
failed = [r for r in results if not r[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
