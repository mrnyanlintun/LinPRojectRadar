#!/usr/bin/env python3
"""
B5 verification: decision-dependent transitions and follow-up decisions.

Driven entirely through /exec, including a full two-period run.

  1. researchadvance refuses before the current decision is complete, writing no transitions row.
  2. A participant cannot advance another's assignment, nor past their current period. Audited.
  3. Period 2's judgment locks before period 2's reveal; the CHECK and the B1 trigger hold on the
     second decisions row too.
  4. Period 1's decisions row is not mutated by anything in period 2.
  5. Replaying the same (participant, scenario, period) selects the identical branch.
  6. Same order_group + same action -> same branch; different action -> different branch.
  7. No live model call anywhere in the flow.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_transitions.py
"""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import func, select, text  # noqa: E402
from sqlalchemy.exc import DatabaseError  # noqa: E402

import app.main as main  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import (  # noqa: E402
    Assignment, AuditEvent, Decision, Participant, Transition,
)
from app.research_transitions import derive_seed, select_branch  # noqa: E402

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


# ---------------------------------------------------------------- setup

ADMIN = "b5-bootstrap-admin"
with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="PM-000", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    # Project states the transitions point at.
    for legacy in ("STATE-P1", "STATE-RECOVERY", "STATE-DRIFT"):
        if s.scalar(select(Project).where(Project.legacy_id == legacy)) is None:
            s.add(Project(legacy_id=legacy, doc={"id": legacy, "name": legacy, "signals": {}}))
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]

print("=" * 78)
print("SETUP: two-period scenario, rules and families as DATA")
print("=" * 78)

scenario = post({"action": "adminscenariocreate", "session_token": admin,
                 "scenario_version": "b5-v1", "project_type": "construction",
                 "period_count": 2, "evidence_package_id": "STATE-P1"})["scenario_id"]
post({"action": "adminconfigurationcreate", "session_token": admin, "code": "C1",
      "version": "v1", "freeze": True})
post({"action": "adminsequencecreate", "session_token": admin, "order_group": "GB5",
      "scenario_set": "SET-B5", "version": "v1", "positions": ["C1"], "freeze": True})
pkg = post({"action": "adminpackagecreate", "session_token": admin, "version": "b5-pkg",
            "provider_id": "frozen-store", "recommended_action": "Escalate",
            "freeze": True})

fam = post({"action": "adminactionfamilycreate", "session_token": admin, "version": "fam-v1",
            "mappings": {"escalate": "escalate", "monitor": "accept",
                         "re-baseline": "modify", "defer": "defer"},
            "freeze": True})
check(fam.get("ok") is True, "action family mapping created as data", str(fam)[:140])

r1 = post({"action": "admintransitionrulecreate", "session_token": admin,
           "scenario_id": scenario, "period": "P1", "action_family": "escalate",
           "version": "rules-v1", "freeze": True,
           "branches": [{"branch_id": "B-RECOVERY", "branch_version": "bv1",
                         "probability": "1.0", "next_state_id": "STATE-RECOVERY"}]})
check(r1.get("ok") is True, "escalate rule created and frozen", str(r1)[:140])

r2 = post({"action": "admintransitionrulecreate", "session_token": admin,
           "scenario_id": scenario, "period": "P1", "action_family": "accept",
           "version": "rules-v1", "freeze": True,
           "branches": [{"branch_id": "B-DRIFT", "branch_version": "bv1",
                         "probability": "1.0", "next_state_id": "STATE-DRIFT"}]})
check(r2.get("ok") is True, "accept rule created and frozen (different next state)")

unfrozen = post({"action": "admintransitionrulecreate", "session_token": admin,
                 "scenario_id": scenario, "period": "P1", "action_family": "defer",
                 "version": "rules-draft",
                 "branches": [{"branch_id": "B-X", "branch_version": "bv1",
                               "probability": "1.0", "next_state_id": "STATE-DRIFT"}]})
check(unfrozen.get("ok") is True and unfrozen.get("frozen") is False,
      "unfrozen draft rule created")

listing = post({"action": "admintransitionrulelist", "session_token": admin})
check(any(r["usable"] is False for r in listing["rules"]), "list reports unusable draft rules")


def enrol():
    c = post({"action": "adminparticipantcreate", "session_token": admin})
    tok = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
    post({"action": "consentgrant", "session_token": tok, "consent_version": "v1.0"})
    # T4: a_researchprejudgment now requires a completed intake questionnaire.
    post({"action": "intakesave", "session_token": tok,
          "responses": {"experience_level": "mid", "years_experience": 8}})
    post({"action": "adminassign", "session_token": admin, "participant_id": c["participant_id"],
          "order_group": "GB5", "scenario_set": "SET-B5", "scenario_ids": [scenario]})
    with Session() as s:
        a = s.scalar(select(Assignment).where(Assignment.participant_id == c["participant_id"]))
        aid = a.assignment_id
    post({"action": "adminpackageattach", "session_token": admin,
          "assignment_id": aid, "package_id": pkg["package_id"]})
    return c["participant_id"], tok, aid


p_id, p, a_id = enrol()

print()
print("=" * 78)
print("GUARANTEE 1: advance refuses before the decision is complete")
print("=" * 78)

r = post({"action": "researchadvance", "session_token": p})
check(r.get("ok") is False and "must be complete" in r.get("error", ""),
      "advance refused with no decision at all", str(r)[:140])

ev = post({"action": "researchevidenceget", "session_token": p})
check(ev.get("period") == "P1" and ev.get("current_stage") == "evidence", "period 1, stage evidence")
check(ev["evidence"]["id"] == "STATE-P1", "period 1 evidence is the scenario opening state")

post({"action": "researchprejudgment", "session_token": p, "pre_action": "monitor",
      "pre_confidence": 50})
r = post({"action": "researchadvance", "session_token": p})
check(r.get("ok") is False, "advance refused after pre-judgment only")

post({"action": "researchreveal", "session_token": p})
r = post({"action": "researchadvance", "session_token": p})
check(r.get("ok") is False, "advance refused after reveal but before final decision")

with Session() as s:
    n = s.scalar(select(func.count()).select_from(Transition)) or 0
check(n == 0, "no transitions row written by any refused advance", f"{n} rows")

print()
print("=" * 78)
print("TRANSITION EXECUTES + row is self-contained")
print("=" * 78)

post({"action": "researchdecision", "session_token": p, "final_action": "escalate",
      "disposition": "modify", "final_confidence": 70})
adv = post({"action": "researchadvance", "session_token": p})
check(adv.get("ok") is True, "advance succeeded once the decision was complete", str(adv)[:160])
check(adv.get("branch_id") == "B-RECOVERY", "escalate routed to the recovery branch",
      str(adv.get("branch_id")))
check(adv["state"]["id"] == "STATE-RECOVERY", "next period state returned")
check(adv.get("period") == "P2", "advanced to period 2")

with Session() as s:
    tr = s.scalar(select(Transition))
    for field in ("branch_id", "branch_version", "seed", "probability", "next_state_id",
                  "displayed_at"):
        check(getattr(tr, field) is not None, f"transitions row records {field}")
    check(tr.branch_version == "bv1", "branch_version proves which rule applied")
    stored_seed = tr.seed

print()
print("=" * 78)
print("GUARANTEE 5: replay selects the identical branch")
print("=" * 78)

replay = derive_seed(p_id, scenario, "P1")
check(replay == stored_seed, "seed re-derives from (participant, scenario, period)",
      f"{replay[:16]} vs {stored_seed[:16]}")

again = post({"action": "researchadvance", "session_token": p})
check(again.get("already_advanced") is True and again.get("branch_id") == "B-RECOVERY",
      "re-advance is idempotent and returns the same branch")
with Session() as s:
    n = s.scalar(select(func.count()).select_from(Transition)) or 0
check(n == 1, "re-advance wrote no second transitions row", f"{n} rows")

print()
print("=" * 78)
print("GUARANTEE 6: same action converges, different action diverges")
print("=" * 78)


def run_period_one(token, action):
    post({"action": "researchevidenceget", "session_token": token})
    post({"action": "researchprejudgment", "session_token": token, "pre_action": "monitor",
          "pre_confidence": 50})
    post({"action": "researchreveal", "session_token": token})
    post({"action": "researchdecision", "session_token": token, "final_action": action,
          "disposition": "accept", "final_confidence": 60})
    return post({"action": "researchadvance", "session_token": token})


q_id, q, _ = enrol()
r_id, r, _ = enrol()
same = run_period_one(q, "escalate")
diff = run_period_one(r, "monitor")

check(same.get("branch_id") == "B-RECOVERY",
      "second participant, same action, same branch", str(same.get("branch_id")))
check(diff.get("branch_id") == "B-DRIFT",
      "third participant, different action, different branch", str(diff.get("branch_id")))
check(same["state"]["id"] != diff["state"]["id"], "the two reach different project states")
check(same["branch_id"] != diff["branch_id"], "branch ids diverge on action family")

unmapped = post({"action": "adminparticipantcreate", "session_token": admin})
u_tok = post({"action": "researchlogin", "access_token": unmapped["access_token"]})["session_token"]
post({"action": "consentgrant", "session_token": u_tok, "consent_version": "v1.0"})
# T4: a_researchprejudgment now requires a completed intake questionnaire.
post({"action": "intakesave", "session_token": u_tok,
      "responses": {"experience_level": "mid", "years_experience": 8}})
post({"action": "adminassign", "session_token": admin,
      "participant_id": unmapped["participant_id"], "order_group": "GB5",
      "scenario_set": "SET-B5", "scenario_ids": [scenario]})
with Session() as s:
    ua = s.scalar(select(Assignment).where(
        Assignment.participant_id == unmapped["participant_id"])).assignment_id
post({"action": "adminpackageattach", "session_token": admin, "assignment_id": ua,
      "package_id": pkg["package_id"]})
post({"action": "researchprejudgment", "session_token": u_tok, "pre_action": "monitor",
      "pre_confidence": 50})
post({"action": "researchreveal", "session_token": u_tok})
post({"action": "researchdecision", "session_token": u_tok,
      "final_action": "invent-a-new-action", "disposition": "accept"})
r = post({"action": "researchadvance", "session_token": u_tok})
check(r.get("ok") is False and "no frozen family mapping" in r.get("error", ""),
      "an unmapped action is an error, not a silent default", str(r)[:160])

print()
print("=" * 78)
print("PERIOD 2 RUNS EXACTLY AS PERIOD 1 (guarantee 3)")
print("=" * 78)

ev2 = post({"action": "researchevidenceget", "session_token": p})
check(ev2.get("period") == "P2", "period 2 evidence")
check(ev2["evidence"]["id"] == "STATE-RECOVERY",
      "period 2 evidence is the state the transition produced", str(ev2["evidence"]["id"]))
check(ev2.get("current_stage") == "evidence", "stage resets to evidence for period 2")

r = post({"action": "researchreveal", "session_token": p})
check(r.get("ok") is False and "locked" in r.get("error", ""),
      "period 2 reveal refused before period 2 judgment is locked")

pj2 = post({"action": "researchprejudgment", "session_token": p, "pre_action": "defer",
            "pre_confidence": 40})
check(pj2.get("ok") is True and pj2.get("period") == "P2", "period 2 judgment locked",
      str(pj2)[:140])
check(pj2.get("pre_submitted_at") == pj2.get("pre_locked_at"),
      "period 2 lock is atomic too")

rv2 = post({"action": "researchreveal", "session_token": p})
check(rv2.get("ok") is True, "period 2 reveal succeeded after locking")

with Session() as s:
    d2 = s.scalar(select(Decision).where(Decision.assignment_id == a_id, Decision.period == "P2"))
    d2_id = d2.decision_id
    check(d2.pre_locked_at <= d2.reveal_at, "period 2 pre_locked_at <= reveal_at")
    try:
        s.execute(text("UPDATE decisions SET pre_action='tamper' WHERE decision_id=:i"),
                  {"i": d2.decision_id})
        s.commit()
        check(False, "B1 trigger fires on the period 2 row", "update succeeded")
    except DatabaseError:
        s.rollback()
        check(True, "B1 trigger fires on the period 2 row")
    try:
        s.execute(text("UPDATE decisions SET reveal_at='1999-01-01 00:00:00+00' "
                       "WHERE decision_id=:i"), {"i": d2.decision_id})
        s.commit()
        check(False, "CHECK holds on the period 2 row", "update succeeded")
    except DatabaseError:
        s.rollback()
        check(True, "CHECK holds on the period 2 row")

print()
print("=" * 78)
print("GUARANTEE 4: period 1's row is untouched by period 2")
print("=" * 78)

with Session() as s:
    d1 = s.scalar(select(Decision).where(Decision.assignment_id == a_id, Decision.period == "P1"))
    check(d1.pre_action == "monitor" and d1.pre_confidence == 50,
          "period 1 preliminary judgment unchanged")
    check(d1.final_action == "escalate" and d1.disposition == "modify",
          "period 1 final decision unchanged")
    check(d1.decision_id != d2_id, "period 1 and 2 are separate rows")

post({"action": "researchdecision", "session_token": p, "final_action": "monitor",
      "disposition": "accept", "final_confidence": 65})
with Session() as s:
    d1b = s.scalar(select(Decision).where(Decision.assignment_id == a_id, Decision.period == "P1"))
    check(d1b.final_action == "escalate", "period 1 still unchanged after period 2 completes")
    a = s.get(Assignment, a_id)
    check(a.status == "completed", "assignment completes only after the final period",
          str(a.status))

end = post({"action": "researchadvance", "session_token": p})
check(end.get("ok") is False and "nothing to advance" in end.get("error", ""),
      "advancing past the final period is refused", str(end)[:140])

print()
print("=" * 78)
print("GUARANTEE 2: no cross-participant or out-of-period advance")
print("=" * 78)

before = 0
with Session() as s:
    before = s.scalar(select(func.count()).select_from(AuditEvent)
                      .where(AuditEvent.event_type == "out_of_sequence_access_denied")) or 0

with Session() as s:
    other_a = s.scalar(select(Assignment).where(Assignment.participant_id == q_id)).assignment_id
r = post({"action": "researchadvance", "session_token": p, "assignment_id": other_a})
check(r.get("ok") is False and "current assignment" in r.get("error", ""),
      "advance on another participant's assignment refused", str(r)[:140])

with Session() as s:
    after = s.scalar(select(func.count()).select_from(AuditEvent)
                     .where(AuditEvent.event_type == "out_of_sequence_access_denied")) or 0
check(after == before + 1, "the refused advance was audited")

with Session() as s:
    n = s.scalar(select(func.count()).select_from(Transition)
                 .where(Transition.decision_id.in_(
                     select(Decision.decision_id).where(Decision.assignment_id == other_a)))) or 0
check(n == 1, "the other participant's transitions are unaffected", f"{n}")

print()
print("=" * 78)
print("GUARANTEE 7: no live model call")
print("=" * 78)

src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "research_transitions.py").read_text(
    encoding="utf-8")
for forbidden in ("requests", "httpx", "urllib.request", "http.client", "socket",
                  "openai", "anthropic", "random.", "fetch("):
    check(forbidden not in src, f"research_transitions.py does not reference {forbidden}")

print()
print("=" * 78)
failed = [x for x in results if not x[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
