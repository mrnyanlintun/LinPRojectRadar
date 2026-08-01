#!/usr/bin/env python3
"""
T6 — the expert reference lock.

WHAT THIS PROVES

The expert reference is the standard participant decisions are scored against. Its value rests
entirely on having been committed before the expert saw the AI package, so this suite exists to
make that claim falsifiable rather than asserted.

  GUARANTEE 8. No AI package, recommendation, or action-bearing module output reaches an expert
  before their reference is locked. Every pre-lock response is scanned, including the refusal that
  the package endpoint returns — a refusal that named the recommended action would leak exactly
  what it is refusing.

  GUARANTEE 9. After locking, the reference cannot be changed by any route: the API, an ORM
  update, a Core update, or raw driver SQL. All four are refused, and every rejection is audited.

WHY THE DETECTOR IS SELF-TESTED FIRST

`scan_for_leak` is imported from T4's suite rather than rewritten. B7b's leak survived eight
phases because its grep had a clause that could never be false, and the lesson taken from that was
that a leak detector must be proven able to FAIL before it is trusted to pass. This suite proves
it twice over:

  1. Against planted blobs, in the self-test block — the same discipline T4 established.
  2. Against a REAL deliberate leak, end to end. GUARANTEE 8B monkeypatches the live evidence
     handler so it returns the package, runs the identical assertion the real check runs, and
     requires it to fail. Then the patch is removed and the real handler is re-verified clean. A
     check that has never failed is not evidence of anything.

Run:
    DATABASE_URL=sqlite:///./t6.db SESSION_SECRET=... python tools/test_expert_reference_t6.py

Exit code 0 on success, 1 on any failure.
"""

from __future__ import annotations

import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select, text, update  # noqa: E402
from sqlalchemy.exc import DatabaseError  # noqa: E402

import app.main as main  # noqa: E402
import app.research_expert as research_expert  # noqa: E402
from app.research_audit import (  # noqa: E402
    EXPERT_REJECTED_EVENT, is_expert_lock_violation, record_rejected_write,
)
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import (  # noqa: E402
    Assignment, AuditEvent, ExpertReference, Participant,
)

# The detector, imported rather than reimplemented, from the module T4 also imports. One
# definition of what counts as a leak; see tools/leak_detector.py for why that matters.
from tools.leak_detector import (  # noqa: E402
    MARK_ALTERNATIVE, MARK_BOUNDARY, MARK_CONDITION, MARK_LIMITATION, MARK_RECOMMENDATION,
    MARK_UNCERTAINTY, scan_for_leak,
)

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


def audit_count(event_type: str) -> int:
    with Session() as s:
        return len(s.scalars(
            select(AuditEvent).where(AuditEvent.event_type == event_type)).all())


print("=" * 78)
print("T6 — the expert reference lock")
print("=" * 78)

# --------------------------------------------------------------- setup

ADMIN = "t6-admin"
with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="T6-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]

print("\nSETUP: expert scenario, frozen package with planted markers, expert account")

post({"action": "create", "id": "PRJ-T6-EVIDENCE", "name": "T6 Evidence Project"})

scenario = post({"action": "adminscenariocreate", "session_token": admin,
                 "scenario_version": "t6-v1", "project_type": "construction",
                 "period_count": 2, "evidence_package_id": "PRJ-T6-EVIDENCE"})["scenario_id"]

pkg = post({"action": "adminpackagecreate", "session_token": admin, "version": "t6-pkg",
            "provider_id": "frozen-store", "model_version": "t6-model",
            "recommended_action": MARK_RECOMMENDATION,
            "alternatives": {"a": MARK_ALTERNATIVE},
            "detected_condition": MARK_CONDITION,
            "limitations": MARK_LIMITATION,
            "uncertainty": {"u": MARK_UNCERTAINTY},
            "applicability_boundary": MARK_BOUNDARY,
            "freeze": True})
check(pkg.get("ok") is True, "frozen package created with planted markers", str(pkg)[:110])

post({"action": "adminconfigurationcreate", "session_token": admin,
      "code": "C0", "version": "t6", "label": "C0", "freeze": True})
post({"action": "adminsequencecreate", "session_token": admin, "order_group": "GT6",
      "scenario_set": "SET-T6", "version": "t6", "positions": ["C0", "C0"], "freeze": True})


def enrol_expert(code: str):
    c = post({"action": "adminparticipantcreate", "session_token": admin,
              "pseudonymous_code": code, "role": "Expert"})
    tok = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
    post({"action": "consentgrant", "session_token": tok, "consent_version": "t6-v1"})
    post({"action": "adminassign", "session_token": admin, "participant_id": c["participant_id"],
          "order_group": "GT6", "scenario_set": "SET-T6", "scenario_ids": [scenario]})
    with Session() as s:
        a = s.scalar(select(Assignment).where(Assignment.participant_id == c["participant_id"]))
        aid = a.assignment_id
    post({"action": "adminpackageattach", "session_token": admin, "assignment_id": aid,
          "package_id": pkg["package_id"]})
    return c["participant_id"], tok, aid


expert_id, expert, expert_aid = enrol_expert("T6-EXPERT-1")
check(bool(expert), "expert enrolled, assigned, and package attached to the assignment")

with Session() as s:
    who = s.get(Participant, expert_id)
    check(who.role == "Expert", "expert account carries the Expert role", str(who.role))

# --------------------------------------------------------------- detector self-test

print("\n[self-test] the detector must FAIL on a planted leak before it is trusted")
check(len(scan_for_leak(json.dumps({"recommended_action": "x"}))) > 0,
      "detector catches a planted package FIELD NAME")
check(len(scan_for_leak(MARK_RECOMMENDATION)) > 0,
      "detector catches a planted package MARKER")
check(len(scan_for_leak("Minimax regret recommends escalate")) > 0,
      "detector catches a planted recommendation PROSE leak")
check(len(scan_for_leak(json.dumps({"period": "P1", "status_color": "Green"}))) == 0,
      "detector passes a genuinely clean blob")

# --------------------------------------------------------------- role gate

print("\nRole gate — the expert actions are for the expert panel only")

pc = post({"action": "adminparticipantcreate", "session_token": admin,
           "pseudonymous_code": "T6-PLAIN"})
plain = post({"action": "researchlogin", "access_token": pc["access_token"]})["session_token"]
post({"action": "consentgrant", "session_token": plain, "consent_version": "t6-v1"})

before = audit_count("expert_action_denied")
r = post({"action": "expertevidenceget", "session_token": plain, "scenario_id": scenario})
check(r.get("ok") is False, "a Participant is refused the expert evidence action", str(r)[:100])
check(audit_count("expert_action_denied") == before + 1, "the refusal is audited")
check(len(scan_for_leak(json.dumps(r))) == 0, "the role refusal leaks nothing", str(r)[:100])

r = post({"action": "expertreferencecommit", "session_token": admin, "scenario_id": scenario,
          "preferred_action": "monitor", "rationale": "x", "required_evidence": "x",
          "escalation_expectation": "x", "confidence": 50})
check(r.get("ok") is False, "even a ResearchAdmin is refused: role is Expert, not seniority")

r = post({"action": "expertevidenceget", "session_token": expert,
          "scenario_id": "01ZZZZZZZZZZZZZZZZZZZZZZZZ"})
check(r.get("ok") is False, "a scenario the expert does not hold is refused", str(r)[:100])

# --------------------------------------------------------------- GUARANTEE 8

print("\nGuarantee 8 — nothing action-bearing reaches the expert before the lock")

pre_lock_bodies: dict[str, dict] = {}

pre_lock_bodies["expertreferencelist"] = post(
    {"action": "expertreferencelist", "session_token": expert})
pre_lock_bodies["expertevidenceget"] = post(
    {"action": "expertevidenceget", "session_token": expert, "scenario_id": scenario,
     "period": "P1"})

before = audit_count("expert_package_denied_before_lock")
refusal = post({"action": "expertpackageview", "session_token": expert,
                "scenario_id": scenario, "period": "P1"})
pre_lock_bodies["expertpackageview (refusal)"] = refusal

check(refusal.get("ok") is False, "the package is refused before the reference is locked")
check("package" not in refusal, "the refusal carries no package key at all — not null, absent",
      str(sorted(refusal.keys())))
check(audit_count("expert_package_denied_before_lock") == before + 1,
      "the pre-lock package refusal is audited")

for name, body in pre_lock_bodies.items():
    findings = scan_for_leak(json.dumps(body))
    check(len(findings) == 0, f"{name} leaks nothing pre-lock", str(findings))

ev = pre_lock_bodies["expertevidenceget"]
check(ev.get("ok") is True, "the expert can read evidence before locking")
check(ev.get("evidence") is not None, "and that evidence is real, so the scan is not vacuous")
check(ev.get("reference_locked") is False, "and the reference reports itself unlocked")

# The whole response surface, not just the fields this suite happens to name.
combined = json.dumps(pre_lock_bodies)
for field in ("recommended_action", "expected_regret", "package_id", "package_hash"):
    check(f'"{field}"' not in combined,
          f"no {field} key anywhere in the pre-lock surface")

# --------------------------------------------------------------- GUARANTEE 8B: real leak

print("\nGuarantee 8B — a DELIBERATE leak is introduced, and the check must catch it")

_real_handler = research_expert.a_expertevidenceget


def _leaky_handler(session, payload, secret, ttl):
    """A deliberately contaminated evidence handler: it attaches the package."""
    body = _real_handler(session, payload, secret, ttl)
    if body.get("ok"):
        body["package"] = {"recommended_action": MARK_RECOMMENDATION}
    return body


research_expert.EXPERT_ACTIONS["expertevidenceget"] = _leaky_handler
leaked = post({"action": "expertevidenceget", "session_token": expert,
               "scenario_id": scenario, "period": "P1"})
leak_findings = scan_for_leak(json.dumps(leaked))
check(len(leak_findings) > 0,
      "the planted leak IS detected by the same check that passed above", str(leak_findings))
check(any("recommended_action" in f for f in leak_findings),
      "and the finding names the leaked field", str(leak_findings))

# Remove the leak and prove the real handler is clean again.
research_expert.EXPERT_ACTIONS["expertevidenceget"] = _real_handler
restored = post({"action": "expertevidenceget", "session_token": expert,
                 "scenario_id": scenario, "period": "P1"})
check(len(scan_for_leak(json.dumps(restored))) == 0,
      "leak removed: the real handler is clean again")
check("package" not in restored, "and carries no package key")

# --------------------------------------------------------------- commit and lock

print("\nThe reference is committed and locked in one statement")

r = post({"action": "expertreferencecommit", "session_token": expert, "scenario_id": scenario,
          "period": "P1", "preferred_action": "escalate",
          "acceptable_alternatives": ["investigate"],
          "unsupported_actions": ["defer"],
          "rationale": "Cost variance is beyond the threshold the sponsor set.",
          "required_evidence": "Monthly report EV/AC, RFI ageing log.",
          "escalation_expectation": "To the programme board within one cycle.",
          "confidence": 80})
check(r.get("ok") is True, "the reference commits", str(r)[:140])
ref = r.get("reference") or {}
reference_id = ref.get("reference_id")
check(bool(ref.get("locked_at")), "locked_at is set by the server in the same statement")
check(ref.get("preferred_action") == "escalate", "the preferred action is stored")
check(audit_count("expert_reference_locked") >= 1, "the lock is audited")

with Session() as s:
    stored = s.get(ExpertReference, reference_id)
    check(stored is not None and stored.locked_at is not None,
          "and the stored row is locked in the database, not only in the response")
    check(stored.period == "P1", "the reference is scoped to the period", str(stored.period))
    check(stored.expert_id == expert_id, "and to the expert who wrote it")

# Validation is enforced, so a reference cannot be committed empty to dodge the lock.
r = post({"action": "expertreferencecommit", "session_token": expert, "scenario_id": scenario,
          "period": "P2", "preferred_action": "not-an-action", "rationale": "x",
          "required_evidence": "x", "escalation_expectation": "x", "confidence": 50})
check(r.get("ok") is False, "an action outside the shared vocabulary is refused", str(r)[:100])

r = post({"action": "expertreferencecommit", "session_token": expert, "scenario_id": scenario,
          "period": "P2", "preferred_action": "monitor",
          "acceptable_alternatives": ["defer"], "unsupported_actions": ["defer"],
          "rationale": "x", "required_evidence": "x", "escalation_expectation": "x",
          "confidence": 50})
check(r.get("ok") is False, "an action cannot be both acceptable and unsupported", str(r)[:100])

# --------------------------------------------------------------- package, post-lock

print("\nOnly after the lock is the package available")

r = post({"action": "expertpackageview", "session_token": expert, "scenario_id": scenario,
          "period": "P1"})
check(r.get("ok") is True, "the package is released once the reference is locked", str(r)[:110])
check(MARK_RECOMMENDATION in json.dumps(r),
      "and it is the real package, so the pre-lock scans were meaningful")
check(audit_count("expert_package_viewed") >= 1, "the package view is audited")

# P2 has no locked reference, so it must still refuse — the lock is per period, not per scenario.
r = post({"action": "expertpackageview", "session_token": expert, "scenario_id": scenario,
          "period": "P2"})
check(r.get("ok") is False, "a period whose reference is NOT locked still refuses the package")
check(len(scan_for_leak(json.dumps(r))) == 0, "and that refusal leaks nothing", str(r)[:100])

print("\nThe realism review is recorded without touching the reference")

r = post({"action": "expertrealismreview", "session_token": expert, "scenario_id": scenario,
          "period": "P1", "plausible": True, "comment": "Reads like a real system output."})
check(r.get("ok") is True, "the realism review is accepted after the lock", str(r)[:110])
with Session() as s:
    stored = s.get(ExpertReference, reference_id)
    check(stored.realism_review is not None, "and stored")
    check(stored.preferred_action == "escalate",
          "while the reference itself is untouched — realism_review is outside the lock")

# --------------------------------------------------------------- GUARANTEE 9

print("\nGuarantee 9 — after locking, the reference cannot be changed by any route")

# Route 1: the API.
before = audit_count("expert_reference_resubmission_denied")
r = post({"action": "expertreferencecommit", "session_token": expert, "scenario_id": scenario,
          "period": "P1", "preferred_action": "monitor", "rationale": "changed my mind",
          "required_evidence": "x", "escalation_expectation": "x", "confidence": 10})
check(r.get("ok") is False, "ROUTE 1 (API): resubmission is refused", str(r)[:110])
check(audit_count("expert_reference_resubmission_denied") == before + 1,
      "and the refusal is audited")
with Session() as s:
    check(s.get(ExpertReference, reference_id).preferred_action == "escalate",
          "and the stored reference is unchanged")

audit_before = audit_count(EXPERT_REJECTED_EVENT)

# Route 2: an ORM update.
rejected = False
with Session() as s:
    try:
        obj = s.get(ExpertReference, reference_id)
        obj.preferred_action = "monitor"
        s.commit()
    except DatabaseError as exc:
        s.rollback()
        rejected = is_expert_lock_violation(exc)
        record_rejected_write(main.engine, reference_id=reference_id,
                              participant_id=expert_id,
                              attempted={"preferred_action": "monitor"}, path="orm",
                              event_type=EXPERT_REJECTED_EVENT)
check(rejected, "ROUTE 2 (ORM update): rejected by the database trigger")

# Route 3: a Core update.
rejected = False
with Session() as s:
    try:
        s.execute(update(ExpertReference)
                  .where(ExpertReference.reference_id == reference_id)
                  .values(confidence=1))
        s.commit()
    except DatabaseError as exc:
        s.rollback()
        rejected = is_expert_lock_violation(exc)
        record_rejected_write(main.engine, reference_id=reference_id,
                              participant_id=expert_id, attempted={"confidence": 1},
                              path="core", event_type=EXPERT_REJECTED_EVENT)
check(rejected, "ROUTE 3 (Core update): rejected by the database trigger")

# Route 4: raw driver SQL — the route that bypasses every layer of the application.
rejected = False
with Session() as s:
    try:
        s.execute(text("UPDATE expert_references SET rationale = :r WHERE reference_id = :i"),
                  {"r": "rewritten", "i": reference_id})
        s.commit()
    except DatabaseError as exc:
        s.rollback()
        rejected = is_expert_lock_violation(exc)
        record_rejected_write(main.engine, reference_id=reference_id,
                              participant_id=expert_id, attempted={"rationale": "rewritten"},
                              path="raw-sql", event_type=EXPERT_REJECTED_EVENT)
check(rejected, "ROUTE 4 (raw SQL): rejected by the database trigger")

# Moving the lock itself is as much a falsification as editing the content.
rejected = False
with Session() as s:
    try:
        s.execute(text("UPDATE expert_references SET locked_at = NULL WHERE reference_id = :i"),
                  {"i": reference_id})
        s.commit()
    except DatabaseError as exc:
        s.rollback()
        rejected = is_expert_lock_violation(exc)
check(rejected, "clearing locked_at to unlock the row is itself rejected")

check(audit_count(EXPERT_REJECTED_EVENT) == audit_before + 3,
      "every rejected write appended a durable audit row",
      f"{audit_count(EXPERT_REJECTED_EVENT)} vs {audit_before} + 3")

with Session() as s:
    final = s.get(ExpertReference, reference_id)
    check(final.preferred_action == "escalate", "final: preferred_action survived every attempt")
    check(final.confidence == 80, "final: confidence survived every attempt")
    check(final.rationale.startswith("Cost variance"), "final: rationale survived every attempt")
    check(final.locked_at is not None, "final: the row is still locked")

# A second INSERT is the trivial way round an UPDATE trigger; the unique index closes it.
duplicated = False
with Session() as s:
    try:
        s.add(ExpertReference(scenario_id=scenario, expert_id=expert_id, period="P1",
                              preferred_action="monitor", confidence=1))
        s.commit()
    except DatabaseError:
        s.rollback()
        duplicated = True
check(duplicated, "a SECOND reference for the same expert, scenario and period is rejected")

# --------------------------------------------------------------- summary

print("\n" + "=" * 78)
passed = sum(1 for ok, _, _ in results if ok)
failed = [(label, detail) for ok, label, detail in results if not ok]
if failed:
    print(f"RESULT: {passed}/{len(results)} checks passed — {len(failed)} FAILED")
    for label, detail in failed:
        print(f"  FAILED: {label}  {detail}")
else:
    print(f"RESULT: {passed}/{len(results)} checks passed")
print("=" * 78)
sys.exit(1 if failed else 0)
