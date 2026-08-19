"""RUN 41 shared fixture: build a real, fully final-locked decision through the REAL app routes.

Nothing here inserts a Decision row directly. Every state transition goes through /exec, so the
state under test is reached by the route the application actually takes.
"""
from __future__ import annotations
import json, sys

def build(main, client, tag: str):
    from sqlalchemy import select
    from app.models import Project
    from app.research_identity import hash_access_token
    from app.research_models import Assignment, Decision, Participant

    Session = main.SessionFactory

    def post(payload):
        r = client.post("/exec", content=json.dumps(payload),
                        headers={"Content-Type": "text/plain"})
        assert r.status_code == 200, f"HTTP {r.status_code}"
        return r.json()

    ADMIN = f"r41-{tag}-admin"
    with Session() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code=f"R41-{tag}", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        for legacy in [f"PRJ-{tag}-EV0", f"PRJ-{tag}-EV1"]:
            if s.scalar(select(Project).where(Project.legacy_id == legacy)) is None:
                s.add(Project(legacy_id=legacy, doc={"id": legacy, "name": legacy, "signals": {}}))
        s.commit()

    admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    sc = [post({"action": "adminscenariocreate", "session_token": admin,
                "scenario_version": f"{tag}-s{i}", "project_type": "construction",
                "period_count": 2, "evidence_package_id": f"PRJ-{tag}-EV{i}"})["scenario_id"]
          for i in range(2)]
    post({"action": "adminconfigurationcreate", "session_token": admin,
          "code": "C1", "version": "v1", "freeze": True})
    post({"action": "adminsequencecreate", "session_token": admin, "order_group": f"G{tag}",
          "scenario_set": f"SET-{tag}", "version": "v1", "positions": ["C1", "C1"], "freeze": True})
    pkg = post({"action": "adminpackagecreate", "session_token": admin, "version": f"{tag}-pkg",
                "provider_id": "frozen-store", "model_version": "n/a",
                "output_type": "recommendation", "detected_condition": "cost overrun risk",
                "recommended_action": "Escalate to recovery review",
                "alternatives": ["Monitor for one period", "Re-baseline"],
                "uncertainty": {"confidence": "moderate"},
                "limitations": "Single period.", "freeze": True})

    c = post({"action": "adminparticipantcreate", "session_token": admin})
    p = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
    post({"action": "consentgrant", "session_token": p, "consent_version": "v1.0"})
    post({"action": "intakesave", "session_token": p,
          "responses": {"experience_level": "mid", "years_experience": 8}})
    post({"action": "adminassign", "session_token": admin, "participant_id": c["participant_id"],
          "order_group": f"G{tag}", "scenario_set": f"SET-{tag}", "scenario_ids": sc})
    with Session() as s:
        a1 = s.scalar(select(Assignment).where(Assignment.participant_id == c["participant_id"],
                                               Assignment.sequence_number == 1))
        a1_id = a1.assignment_id
    post({"action": "adminpackageattach", "session_token": admin,
          "assignment_id": a1_id, "package_id": pkg["package_id"]})

    ctx = {"post": post, "admin": admin, "p": p, "participant_id": c["participant_id"],
           "assignment_id": a1_id, "Session": Session, "package_id": pkg["package_id"]}
    return ctx


FINAL_PAYLOAD = {
    "final_action": "Escalate to recovery review board",
    "disposition": "accept",
    "rationale": "Cost variance exceeds tolerance for two consecutive periods.",
    "final_confidence": 72,
    "escalation_level": "program",
    "owner_role": "Project Manager",
    "authority_role": "Program Director",
    "resource_constraint": "no additional budget available",
    "evidence_items": ["Cost report P01", "Schedule variance chart"],
    "reason_code": "cost_variance",
    "deadline": "2026-09-30",
    "residual_risk": "Recovery may slip if vendor lead time holds.",
}


def run_to_final_lock(ctx):
    """evidence -> preliminary response -> preliminary lock -> reveal -> final response+lock."""
    post = ctx["post"]; p = ctx["p"]
    steps = {}
    steps["evidence"] = post({"action": "researchevidenceget", "session_token": p})
    steps["prejudgment"] = post({"action": "researchprejudgment", "session_token": p,
                                 "pre_action": "Monitor one more period",
                                 "pre_confidence": 55,
                                 "pre_assessment": "Trend is adverse but not yet critical."})
    steps["reveal"] = post({"action": "researchreveal", "session_token": p})
    steps["final"] = post({"action": "researchdecision", "session_token": p, **FINAL_PAYLOAD})
    return steps


def decision_id(ctx):
    from sqlalchemy import select
    from app.research_models import Decision
    with ctx["Session"]() as s:
        d = s.scalar(select(Decision).where(Decision.assignment_id == ctx["assignment_id"]))
        return d.decision_id
