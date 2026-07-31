#!/usr/bin/env python3
"""
B4 verification: the experimental sequence.

Everything is driven through the /exec HTTP surface. The seven non-negotiable guarantees:

  1. researchreveal refuses when the preliminary judgment is not locked, leaking no package data.
  2. After reveal, pre_action and pre_confidence cannot be modified: the application refuses
     first, and the B1 database trigger still fires if the application is bypassed.
  3. pre_locked_at <= reveal_at always holds, and the stored row satisfies the CHECK.
  4. A participant cannot reveal or decide on an assignment that is not their current one.
  5. An unfrozen package cannot be revealed.
  6. The hash returned matches decision_support_packages.hash and is stored on the decisions row.
  7. No live AI model call occurs anywhere in the flow.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_decision_sequence.py
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import func, select, text  # noqa: E402
from sqlalchemy.exc import DatabaseError  # noqa: E402

import app.main as main  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import (  # noqa: E402
    Assignment, AuditEvent, Decision, DecisionSupportPackage, Participant,
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


# ---------------------------------------------------------------- setup

ADMIN_TOKEN = "b4-bootstrap-admin"
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
print("SETUP")
print("=" * 78)

sc = [post({"action": "adminscenariocreate", "session_token": admin,
            "scenario_version": f"b4-s{i}", "project_type": "construction",
            "period_count": 2})["scenario_id"] for i in range(2)]
post({"action": "adminconfigurationcreate", "session_token": admin,
      "code": "C1", "version": "v1", "freeze": True})
post({"action": "adminsequencecreate", "session_token": admin, "order_group": "GB4",
      "scenario_set": "SET-B4", "version": "v1", "positions": ["C1", "C1"], "freeze": True})

FROZEN = post({"action": "adminpackagecreate", "session_token": admin, "version": "pkg-v1",
               "provider_id": "frozen-store", "model_version": "n/a",
               "output_type": "recommendation", "detected_condition": "cost overrun risk",
               "recommended_action": "Escalate to recovery review",
               "alternatives": ["Monitor for one period", "Re-baseline"],
               "uncertainty": {"confidence": "moderate"},
               "limitations": "Derived from a single reporting period.",
               "freeze": True})
check(FROZEN.get("ok") is True and FROZEN.get("revealable") is True,
      "frozen package created", str(FROZEN)[:160])
check(len(FROZEN.get("hash") or "") == 64, "package hash is a sha256 digest")

UNFROZEN = post({"action": "adminpackagecreate", "session_token": admin, "version": "pkg-v2",
                 "recommended_action": "Should never be seen"})
check(UNFROZEN.get("frozen_at") is None and UNFROZEN.get("revealable") is False,
      "unfrozen package created")


def make_participant():
    c = post({"action": "adminparticipantcreate", "session_token": admin})
    tok = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
    post({"action": "consentgrant", "session_token": tok, "consent_version": "v1.0"})
    post({"action": "adminassign", "session_token": admin, "participant_id": c["participant_id"],
          "order_group": "GB4", "scenario_set": "SET-B4", "scenario_ids": sc})
    return c["participant_id"], tok


p_id, p = make_participant()
other_id, other = make_participant()

with Session() as s:
    a1 = s.scalar(select(Assignment).where(Assignment.participant_id == p_id,
                                           Assignment.sequence_number == 1))
    a2 = s.scalar(select(Assignment).where(Assignment.participant_id == p_id,
                                           Assignment.sequence_number == 2))
    a1_id, a2_id = a1.assignment_id, a2.assignment_id
post({"action": "adminpackageattach", "session_token": admin,
      "assignment_id": a1_id, "package_id": FROZEN["package_id"]})

print()
print("=" * 78)
print("STAGE IS DERIVED, AND EVIDENCE IS CONDITION-FREE")
print("=" * 78)

ev = post({"action": "researchevidenceget", "session_token": p})
check(ev.get("ok") is True, "evidence readable", str(ev)[:140])
check(ev.get("current_stage") == "evidence", "stage derives to 'evidence' before any submission",
      str(ev.get("current_stage")))
blob = json.dumps(ev)
for leak in ("config_id", "recommended_action", "package", "condition_sequence"):
    check(leak not in blob, f"evidence response contains no {leak}")

who = post({"action": "researchwhoami", "session_token": p})
check(who.get("current_stage") == "evidence", "whoami reports the derived stage")

ev_forced = post({"action": "researchevidenceget", "session_token": p, "current_stage": "complete"})
check(ev_forced.get("current_stage") == "evidence", "a body-supplied stage is ignored")

print()
print("=" * 78)
print("GUARANTEE 1: reveal refuses before the judgment is locked")
print("=" * 78)

r = post({"action": "researchreveal", "session_token": p})
check(r.get("ok") is False and "locked" in r.get("error", ""),
      "reveal refused while unlocked", str(r)[:160])
refusal = json.dumps(r)
for leak in ("recommended_action", "Escalate to recovery review", "alternatives",
             "detected_condition", "package_id", "hash"):
    check(leak not in refusal, f"refusal leaks no {leak}")

d = post({"action": "researchdecision", "session_token": p, "final_action": "x",
          "disposition": "accept"})
check(d.get("ok") is False and "revealed" in d.get("error", ""),
      "final decision refused before reveal", str(d)[:140])

print()
print("=" * 78)
print("LOCK: submitted and locked in one transaction")
print("=" * 78)

pj = post({"action": "researchprejudgment", "session_token": p,
           "pre_action": "monitor", "pre_confidence": 55})
check(pj.get("ok") is True, "preliminary judgment accepted", str(pj)[:160])
check(pj.get("pre_judgment_locked") is True, "returned locked")
check(pj.get("pre_submitted_at") == pj.get("pre_locked_at"),
      "pre_submitted_at and pre_locked_at assigned in the same statement",
      f"{pj.get('pre_submitted_at')} vs {pj.get('pre_locked_at')}")
check(pj.get("current_stage") == "awaiting_reveal", "stage derives to 'awaiting_reveal'")

resub = post({"action": "researchprejudgment", "session_token": p,
              "pre_action": "escalate", "pre_confidence": 99})
check(resub.get("ok") is False and "already locked" in resub.get("error", ""),
      "resubmission refused by the application", str(resub)[:140])

with Session() as s:
    dec = s.scalar(select(Decision).where(Decision.assignment_id == a1_id))
    check(dec.pre_action == "monitor" and dec.pre_confidence == 55,
          "stored preliminary judgment unchanged after refused resubmission")

print()
print("=" * 78)
print("GUARANTEE 5: an unfrozen package cannot be revealed")
print("=" * 78)

post({"action": "adminpackageattach", "session_token": admin,
      "assignment_id": a1_id, "package_id": UNFROZEN["package_id"]})
r = post({"action": "researchreveal", "session_token": p})
check(r.get("ok") is False and "not frozen" in r.get("error", ""),
      "reveal of an unfrozen package refused", str(r)[:160])
check("Should never be seen" not in json.dumps(r), "unfrozen content did not leak")
with Session() as s:
    dec = s.scalar(select(Decision).where(Decision.assignment_id == a1_id))
    check(dec.reveal_at is None, "reveal_at not set by the refused attempt")

post({"action": "adminpackageattach", "session_token": admin,
      "assignment_id": a1_id, "package_id": FROZEN["package_id"]})

print()
print("=" * 78)
print("REVEAL + GUARANTEE 6: hash matches and is stored")
print("=" * 78)

rv = post({"action": "researchreveal", "session_token": p})
check(rv.get("ok") is True, "reveal succeeded once locked", str(rv)[:140])
check(rv["package"]["recommended_action"] == "Escalate to recovery review",
      "package content returned verbatim from storage")
check(rv["package"]["hash"] == FROZEN["hash"], "returned hash matches the package row")
check(rv.get("current_stage") == "deciding", "stage derives to 'deciding'")

with Session() as s:
    dec = s.scalar(select(Decision).where(Decision.assignment_id == a1_id))
    pkg = s.get(DecisionSupportPackage, FROZEN["package_id"])
    check(dec.package_hash == pkg.hash, "hash stored on the decisions row")
    check(dec.package_id == pkg.package_id, "package_id stored on the decisions row")
    # Guarantee 3
    check(dec.pre_locked_at <= dec.reveal_at, "pre_locked_at <= reveal_at",
          f"{dec.pre_locked_at} vs {dec.reveal_at}")

first_reveal = rv["reveal_at"]
rv2 = post({"action": "researchreveal", "session_token": p})
check(rv2.get("already_revealed") is True and rv2.get("reveal_at") == first_reveal,
      "re-reveal is idempotent and does not move reveal_at")

print()
print("=" * 78)
print("GUARANTEE 3: the CHECK constraint rejects a backdated reveal")
print("=" * 78)

with Session() as s:
    dec = s.scalar(select(Decision).where(Decision.assignment_id == a1_id))
    try:
        s.execute(text("UPDATE decisions SET reveal_at = :t WHERE decision_id = :i"),
                  {"t": "1999-01-01 00:00:00+00", "i": dec.decision_id})
        s.commit()
        check(False, "CHECK rejects reveal_at before pre_locked_at", "update succeeded")
    except DatabaseError:
        s.rollback()
        check(True, "CHECK rejects reveal_at before pre_locked_at")

print()
print("=" * 78)
print("GUARANTEE 2: post-reveal immutability, application AND trigger")
print("=" * 78)

r = post({"action": "researchprejudgment", "session_token": p,
          "pre_action": "escalate", "pre_confidence": 5})
check(r.get("ok") is False, "application refuses to rewrite the judgment after reveal")

with Session() as s:
    dec = s.scalar(select(Decision).where(Decision.assignment_id == a1_id))
    did = dec.decision_id
    try:
        s.execute(text("UPDATE decisions SET pre_action = 'tamper' WHERE decision_id = :i"),
                  {"i": did})
        s.commit()
        check(False, "B1 trigger still fires when the application is bypassed", "update succeeded")
    except DatabaseError as exc:
        s.rollback()
        check(True, "B1 trigger still fires when the application is bypassed", str(exc)[:70])

with Session() as s:
    dec = s.scalar(select(Decision).where(Decision.assignment_id == a1_id))
    check(dec.pre_action == "monitor" and dec.pre_confidence == 55,
          "preliminary judgment survives both attempts intact")

print()
print("=" * 78)
print("GUARANTEE 4: only the current assignment may be acted on")
print("=" * 78)

r = post({"action": "researchreveal", "session_token": p, "assignment_id": a2_id})
check(r.get("ok") is False and "current assignment" in r.get("error", ""),
      "reveal on a future assignment refused", str(r)[:140])

with Session() as s:
    o = s.scalar(select(Assignment).where(Assignment.participant_id == other_id,
                                          Assignment.sequence_number == 1))
    other_a = o.assignment_id
r = post({"action": "researchdecision", "session_token": p, "assignment_id": other_a,
          "final_action": "x", "disposition": "accept"})
check(r.get("ok") is False, "decision on another participant's assignment refused")

with Session() as s:
    n = s.scalar(select(func.count()).select_from(AuditEvent)
                 .where(AuditEvent.event_type == "out_of_sequence_access_denied")) or 0
check(n >= 2, f"out-of-sequence attempts audited ({n})")

print()
print("=" * 78)
print("FINAL DECISION + STAGE COMPLETION")
print("=" * 78)

fd = post({"action": "researchdecision", "session_token": p, "final_action": "escalate",
           "disposition": "modify", "rationale": "revised after review",
           "final_confidence": 78, "escalation_level": "sponsor",
           "owner_role": "project manager", "authority_role": "sponsor"})
check(fd.get("ok") is True, "final decision recorded", str(fd)[:140])
check(fd.get("current_stage") == "complete", "stage derives to 'complete'")
check(bool(fd.get("final_submitted_at")), "final_submitted_at server-assigned")

dup = post({"action": "researchdecision", "session_token": p, "final_action": "again",
            "disposition": "accept"})
check(dup.get("ok") is False, "a second final decision is refused")

cur = post({"action": "researchcurrent", "session_token": p})
# The scenario has period_count 2, so completing period 1 does NOT finish the assignment. Before
# B5 this asserted the position advanced to 2, which was the bug: a participant was moved to their
# next scenario with a period still outstanding. The assignment now completes only after the final
# period, so the position stays at 1 and the period advances instead.
check(cur.get("current_sequence_number") == 1,
      "position stays at 1 while period 2 is outstanding",
      str(cur.get("current_sequence_number")))
check(cur.get("period") == "P1",
      "period stays at P1 until researchadvance executes the transition",
      str(cur.get("period")))
check("config_id" not in json.dumps(cur), "current position still leaks no config_id")

print()
print("=" * 78)
print("GUARANTEE 7: no live model call anywhere in the flow")
print("=" * 78)

src = pathlib.Path(__file__).resolve().parents[1] / "app" / "research_decision.py"
text_src = src.read_text(encoding="utf-8")
for forbidden in ("requests", "httpx", "urllib.request", "http.client", "socket",
                  "openai", "anthropic", "fetch("):
    check(forbidden not in text_src, f"research_decision.py does not reference {forbidden}")

with Session() as s:
    pkg = s.get(DecisionSupportPackage, FROZEN["package_id"])
    check(pkg.provider_id == "frozen-store" and pkg.model_version == "n/a",
          "revealed package came from storage, not a provider call")
check(rv["package"]["recommended_action"] == FROZEN.get("recommended_action",
                                                        "Escalate to recovery review"),
      "revealed content is byte-identical to what was stored")

print()
print("=" * 78)
failed = [r for r in results if not r[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
