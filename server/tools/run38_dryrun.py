#!/usr/bin/env python3
"""
Run 38 dry-run study population builder (TEST_ONLY).

Builds an isolated, fully synthetic participant population that exercises the frozen
research-mode participant route across 6 scenarios x 6 periods = 36 project-periods.

WHY THE PROJECT IDS ARE PREFIXED. research_fixtures/README.md bars the synthetic corpus
(OG-SYNTH-*) from entering an operational or participant database. The controlled stimulus
corpus therefore is NOT bulk-imported here. Instead each study project-period identity is
represented by a TEST_ONLY-prefixed evidence project whose legacy_id embeds the study
project/period it stands for, so the 36 route identities can be exercised and counted without
any synthetic corpus record reaching a participant store.

EVERY record this module writes is TEST_ONLY: participants carry the R38-TESTONLY-*
pseudonymous code prefix, evidence projects carry the TEST-ONLY- legacy_id prefix and a
record_class of TEST_ONLY in their doc. Nothing here is a study observation.

This module MODIFIES NO FROZEN BEHAVIOUR. It only calls the existing /exec actions.
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import Assignment, Participant  # noqa: E402

TEST_ONLY_LABEL = "TEST_ONLY"
CODE_PREFIX = "R38-TESTONLY-"
PROJECT_PREFIX = "TEST-ONLY-"

STUDY_PROJECTS = ("PRJ-AIR", "PRJ-DCT", "PRJ-HSP", "PRJ-HWY", "PRJ-RAL", "PRJ-WTR")
STUDY_PERIODS = ("P01", "P02", "P03", "P04", "P05", "P06")
ROUTE_PERIODS = ("P1", "P2", "P3", "P4", "P5", "P6")

client = TestClient(main.app, raise_server_exceptions=False)
SessionFactory = main.SessionFactory
ADMIN_TOKEN = "r38-readiness-admin"


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload),
                    headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


def evidence_legacy_id(project: str, route_period: str) -> str:
    """The TEST_ONLY evidence project standing for one study project-period."""
    return f"{PROJECT_PREFIX}{project}-{route_period}"


def bootstrap() -> dict:
    """Provision the whole dry-run study. Returns the handles the drivers need."""
    with SessionFactory() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code="R38-ADMIN", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN_TOKEN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN_TOKEN)
        for proj in STUDY_PROJECTS:
            for rp in ROUTE_PERIODS:
                legacy = evidence_legacy_id(proj, rp)
                if s.scalar(select(Project).where(Project.legacy_id == legacy)) is None:
                    s.add(Project(legacy_id=legacy, doc={
                        "id": legacy, "name": f"TEST_ONLY {proj} {rp}",
                        "record_class": TEST_ONLY_LABEL,
                        "stands_for_project": proj, "stands_for_period": rp,
                        "signals": {}, "note": "synthetic dry-run evidence, not a study record",
                    }))
        s.commit()

    admin = post({"action": "researchlogin", "access_token": ADMIN_TOKEN})["session_token"]

    scenarios: dict[str, str] = {}
    for proj in STUDY_PROJECTS:
        r = post({"action": "adminscenariocreate", "session_token": admin,
                  "scenario_version": f"r38-{proj}", "project_type": "construction",
                  "period_count": len(ROUTE_PERIODS),
                  "evidence_package_id": evidence_legacy_id(proj, "P1")})
        assert r.get("scenario_id"), r
        scenarios[proj] = r["scenario_id"]

    post({"action": "adminconfigurationcreate", "session_token": admin,
          "code": "C1", "version": "v1", "freeze": True})
    post({"action": "adminsequencecreate", "session_token": admin, "order_group": "G38",
          "scenario_set": "SET-38", "version": "v1",
          "positions": ["C1"] * len(STUDY_PROJECTS), "freeze": True})

    # One frozen decision-support package per study project. The package is attached per
    # ASSIGNMENT (frozen behaviour): all six periods of a scenario disclose the same package.
    packages: dict[str, dict] = {}
    for proj in STUDY_PROJECTS:
        packages[proj] = post({
            "action": "adminpackagecreate", "session_token": admin,
            "version": f"r38-pkg-{proj}", "recommended_action": "escalate",
            "detected_condition": "cost variance beyond threshold",
            "output_type": "recommendation", "model_version": "r38-test-m1",
            "use_case": "project controls", "alternatives": ["monitor", "investigate"],
            "uncertainty": {"interval": "80%"}, "limitations": "TEST_ONLY synthetic package",
            "applicability_boundary": "dry run only", "freeze": True})
        assert packages[proj].get("frozen_at"), packages[proj]

    # Action taxonomy: every participant action maps to a family, else advance refuses.
    post({"action": "adminactionfamilycreate", "session_token": admin, "version": "r38-v1",
          "mappings": {a: a for a in
                       ("monitor", "investigate", "escalate", "re-baseline", "defer")},
          "freeze": True})

    # Transition rules: P1..P5 for every scenario and every family, each pointing at the
    # NEXT period's TEST_ONLY evidence project. This is what makes all 36 route identities
    # reachable through the participant route rather than merely declared.
    for proj in STUDY_PROJECTS:
        for i in range(len(ROUTE_PERIODS) - 1):
            here, nxt = ROUTE_PERIODS[i], ROUTE_PERIODS[i + 1]
            for fam in ("monitor", "investigate", "escalate", "re-baseline", "defer"):
                post({"action": "admintransitionrulecreate", "session_token": admin,
                      "scenario_id": scenarios[proj], "period": here, "action_family": fam,
                      "version": "r38-v1", "freeze": True,
                      "branches": [{"branch_id": f"{proj}-{here}-{fam}",
                                    "branch_version": "r38-v1", "probability": "1.0",
                                    "next_state_id": evidence_legacy_id(proj, nxt)}]})

    return {"admin": admin, "scenarios": scenarios, "packages": packages}


def make_participant(ctx: dict, tag: str) -> dict:
    """One isolated TEST_ONLY participant, consented, intaked, assigned, packages attached."""
    admin = ctx["admin"]
    c = post({"action": "adminparticipantcreate", "session_token": admin})
    tok = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
    post({"action": "consentgrant", "session_token": tok, "consent_version": "v1.0"})
    post({"action": "intakesave", "session_token": tok,
          "responses": {"experience_level": "mid", "years_experience": 8,
                        "ai_familiarity": "3", "industry": "construction"}})
    # Label the record TEST_ONLY at the only identifier that reaches an export.
    with SessionFactory() as s:
        row = s.get(Participant, c["participant_id"])
        row.pseudonymous_code = f"{CODE_PREFIX}{tag}"
        s.commit()
    r = post({"action": "adminassign", "session_token": admin,
              "participant_id": c["participant_id"], "order_group": "G38",
              "scenario_set": "SET-38",
              "scenario_ids": list(ctx["scenarios"].values())})
    assert r.get("ok"), r

    with SessionFactory() as s:
        rows = s.scalars(select(Assignment)
                         .where(Assignment.participant_id == c["participant_id"])
                         .order_by(Assignment.sequence_number)).all()
        assigns = [(a.sequence_number, a.assignment_id, a.scenario_id) for a in rows]

    by_scenario = {v: k for k, v in ctx["scenarios"].items()}
    for _n, aid, sid in assigns:
        proj = by_scenario[sid]
        post({"action": "adminpackageattach", "session_token": admin, "assignment_id": aid,
              "package_id": ctx["packages"][proj]["package_id"]})

    return {"participant_id": c["participant_id"], "code": f"{CODE_PREFIX}{tag}",
            "access_token": c["access_token"], "token": tok, "assignments": assigns,
            "by_scenario": by_scenario}
