#!/usr/bin/env python3
"""
The courses of action are readable on an operational project, and still withheld on the
research path until the preliminary judgment is locked.

WHAT THIS SUITE EXISTS TO PROTECT. The reveal gate was written for the research instrument,
where withholding the scored courses until a participant's preliminary judgment is locked IS
the instrument. It was reached through a `Decision` row, which only exists inside the
protocol, so on an ordinary operational project the predicate was false forever and a project
manager could never see the scored courses on their own project.

The fix branches on `project_under_research_protocol` - does a scenario name this project as
its evidence package - and the two checks that matter most here are the ones that prove the
OTHER two candidate discriminators would have leaked:

  - branching on the presence of a Decision row would release the courses on a research
    project whose PM row was revoked, or before a participant is assigned;
  - branching on the caller's account_type would release them to an operational-account
    OBSERVER on a research project, and the rule is explicitly that the package is withheld
    from every member, observers included, because an observer may be senior to the PM.

Both are asserted below as leaks that must not happen.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_courses_of_action.py
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.extraction_client import StubExtractor  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import Assignment, Participant, ProjectMember  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
PASSED = 0
FAILED = 0


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload),
                    headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


def modules_of(result: dict) -> dict:
    return {m.get("method_class"): m for m in (result.get("module_results") or [])
            if isinstance(m, dict)}


ADMIN = "coa-admin"
OPS = "PRJ-COA-OPS"
RES = "PRJ-COA-RES"
ABST = "PRJ-COA-ABSTAIN"

# cpi 0.84 / spi 0.88 drives the scoring analysis to escalate, and every score differs so a
# wrong one cannot match by coincidence.
FULL = {"earned_value": 4_200_000, "actual_cost": 5_000_000, "planned_value": 4_772_727,
        "budget_at_completion": 12_000_000, "actual_percent_complete": 35.0,
        "planned_percent_complete": 40.0, "report_date": "2026-05-31",
        "document_date": "2026-05-31"}
# No budget at completion, so the scoring analysis fails its own check_inputs and abstains.
# It is then filtered out of module_results before storage, which is the genuine
# "did not compute" state.
NO_BAC = {"earned_value": 4_200_000, "actual_cost": 5_000_000, "planned_value": 4_772_727,
          "actual_percent_complete": 35.0, "planned_percent_complete": 40.0,
          "report_date": "2026-05-31", "document_date": "2026-05-31"}


def doc(tag: str) -> bytes:
    return f"%PDF-1.4 COA {tag}\n".encode()


set_extractor_override(StubExtractor({
    hashlib.sha256(doc("OPS")).hexdigest(): ("monthly_report", FULL),
    hashlib.sha256(doc("RES")).hexdigest(): ("monthly_report", FULL),
    hashlib.sha256(doc("ABST")).hexdigest(): ("monthly_report", NO_BAC),
}))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="COA-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    for legacy in (OPS, RES, ABST):
        if s.scalar(select(Project).where(Project.legacy_id == legacy)) is None:
            s.add(Project(legacy_id=legacy,
                          doc={"id": legacy, "name": legacy, "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]


def make_operational(code: str):
    c = post({"action": "adminparticipantcreate", "session_token": admin,
              "pseudonymous_code": code, "role": "Participant",
              "account_type": "operational"})
    tok = post({"action": "researchlogin",
                "access_token": c["access_token"]})["session_token"]
    return c["participant_id"], tok


ops_id, ops = make_operational("COA-OPS-PM")
for legacy, tag in ((OPS, "OPS"), (ABST, "ABST")):
    post({"action": "adminmemberadd", "session_token": admin, "id": legacy,
          "participant_id": ops_id, "project_role": "PM"})
    post({"action": "projectupload", "session_token": ops, "id": legacy, "period": 1,
          "documents": [{"filename": f"{tag}.pdf", "mimeType": "application/pdf",
                         "dataBase64": b64(doc(tag))}]})
    post({"action": "projectcompute", "session_token": ops, "id": legacy, "period": 1})

try:
    print("=" * 78)
    print("1. An operational project shows its scored courses, with the stored figures")
    print("=" * 78)

    res = post({"action": "projectresults", "session_token": ops, "id": OPS, "period": 1})
    check(res.get("ok") is True, "the operational PM can read the result", str(res)[:160])
    result = res["result"]
    mods = modules_of(result)
    regret = mods.get("Regret_Minimization")

    check(regret is not None,
          "the analysis that scores the courses of action is present in the stored result")
    scores = (regret or {}).get("expected_regret")
    check(isinstance(scores, dict) and len(scores) == 3,
          "and it carries the full scored course set, no longer stripped", str(scores))
    check(scores == {"monitor": 11, "investigate": 5, "escalate": 8},
          "the scores are exactly the stored values", str(scores))
    check((regret or {}).get("recommended_action") == "escalate",
          "the recommended course survives the read",
          str((regret or {}).get("recommended_action")))
    check((regret or {}).get("recommendation_withheld") is None,
          "nothing on the module is marked withheld for an operational project",
          str((regret or {}).get("recommendation_withheld")))
    check("withheld until the preliminary judgment"
          not in str((regret or {}).get("evidence_metric")),
          "and its finding text is the real one, not the withheld placeholder",
          str((regret or {}).get("evidence_metric"))[:90])
    check(result.get("recommendation_withheld") is None,
          "the response does not claim a recommendation was withheld from an operational read",
          str(result.get("recommendation_withheld")))

    print()
    print("=" * 78)
    print("2. A module that genuinely did not compute is still absent, and says nothing")
    print("=" * 78)

    ares = post({"action": "projectresults", "session_token": ops, "id": ABST, "period": 1})
    amods = modules_of(ares["result"])
    check("Regret_Minimization" not in amods,
          "with no budget at completion the scoring analysis abstains and never reaches the row",
          str(sorted(amods)[:5]))
    check(len(amods) > 0,
          "while other modules on the same project did compute, so the absence is specific",
          str(len(amods)))
    check(ares["result"].get("recommendation_withheld") is None,
          "and an abstention is not reported as a withholding")

    print()
    print("=" * 78)
    print("3. The research path is unchanged: withheld before the lock, released after")
    print("=" * 78)

    scenario = post({"action": "adminscenariocreate", "session_token": admin,
                     "scenario_version": "coa-s1", "project_type": "construction",
                     "period_count": 2, "evidence_package_id": RES})["scenario_id"]
    post({"action": "adminconfigurationcreate", "session_token": admin,
          "code": "C1", "version": "v1", "freeze": True})
    post({"action": "adminsequencecreate", "session_token": admin, "order_group": "GCOA",
          "scenario_set": "SET-COA", "version": "v1", "positions": ["C1"], "freeze": True})
    pkg = post({"action": "adminpackagecreate", "session_token": admin, "version": "coa-pkg",
                "provider_id": "frozen-store", "model_version": "n/a",
                "output_type": "recommendation", "detected_condition": "cost overrun risk",
                "recommended_action": "Escalate to recovery review",
                "alternatives": ["Monitor for one period"],
                "limitations": "One period.", "freeze": True})

    rp = post({"action": "adminparticipantcreate", "session_token": admin,
               "pseudonymous_code": "COA-RES-P", "role": "Participant",
               "account_type": "research"})
    rtok = post({"action": "researchlogin",
                 "access_token": rp["access_token"]})["session_token"]
    post({"action": "consentgrant", "session_token": rtok, "consent_version": "v1.0"})
    post({"action": "intakesave", "session_token": rtok,
          "responses": {"experience_level": "mid", "years_experience": 8}})
    post({"action": "adminassign", "session_token": admin,
          "participant_id": rp["participant_id"], "order_group": "GCOA",
          "scenario_set": "SET-COA", "scenario_ids": [scenario]})
    with Session() as s:
        a = s.scalar(select(Assignment).where(
            Assignment.participant_id == rp["participant_id"],
            Assignment.sequence_number == 1))
        assignment_id = a.assignment_id
    post({"action": "adminpackageattach", "session_token": admin,
          "assignment_id": assignment_id, "package_id": pkg["package_id"]})
    post({"action": "adminmemberadd", "session_token": admin, "id": RES,
          "participant_id": rp["participant_id"], "project_role": "PM"})
    post({"action": "projectupload", "session_token": rtok, "id": RES, "period": 1,
          "documents": [{"filename": "RES.pdf", "mimeType": "application/pdf",
                         "dataBase64": b64(doc("RES"))}]})
    post({"action": "projectcompute", "session_token": rtok, "id": RES, "period": 1})

    pre = post({"action": "projectresults", "session_token": rtok, "id": RES, "period": 1})
    pre_regret = modules_of(pre["result"]).get("Regret_Minimization")
    check(pre_regret is not None,
          "before the lock the module is still present, so the ledger can show its status")
    check(pre_regret.get("expected_regret") is None,
          "but the scored course set is withheld", str(pre_regret.get("expected_regret")))
    check(pre_regret.get("recommended_action") is None,
          "and so is the recommended course")
    check(pre_regret.get("recommendation_withheld") is True,
          "marked as withheld, which is what lets the surface say so instead of guessing")
    check(pre["result"].get("recommendation_withheld") is True,
          "and the response says the recommendation itself was withheld")
    blob = json.dumps(pre)
    for leak in ("escalate", "expected_regret"):
        check(leak not in blob, f"the pre-lock response leaks no {leak!r}")

    lock = post({"action": "researchprejudgment", "session_token": rtok,
                 "pre_action": "monitor", "pre_confidence": 55})
    check(lock.get("ok") is True and lock.get("pre_judgment_locked") is True,
          "the preliminary judgment locks", str(lock)[:160])

    postl = post({"action": "projectresults", "session_token": rtok, "id": RES, "period": 1})
    post_regret = modules_of(postl["result"]).get("Regret_Minimization")
    check(post_regret.get("expected_regret") == {"monitor": 11, "investigate": 5,
                                                 "escalate": 8},
          "after the lock the same scored set the operational project shows is released",
          str(post_regret.get("expected_regret")))
    check(post_regret.get("recommended_action") == "escalate",
          "and the recommended course with it")

    print()
    print("=" * 78)
    print("4. The discriminator is the PROJECT, so neither rejected candidate leaks")
    print("=" * 78)

    # 4a. An OPERATIONAL-ACCOUNT observer on the research project. If the gate keyed on the
    # caller's account_type this read would be released, and the rule is that the package is
    # withheld from every member including observers.
    obs_id, obs = make_operational("COA-OPS-OBS")
    post({"action": "adminmemberadd", "session_token": admin, "id": RES,
          "participant_id": obs_id, "project_role": "Observer"})

    scenario2 = post({"action": "adminscenariocreate", "session_token": admin,
                      "scenario_version": "coa-s2", "project_type": "construction",
                      "period_count": 2, "evidence_package_id": ABST})["scenario_id"]
    check(bool(scenario2), "a second scenario exists for the account_type check")

    # Use a research project whose PM has NOT locked: create a fresh one by reusing RES but
    # reading as the observer is enough, because RES is now unlocked-free. Instead assert on a
    # project that is under protocol and unlocked: build one.
    RES2 = "PRJ-COA-RES2"
    with Session() as s:
        if s.scalar(select(Project).where(Project.legacy_id == RES2)) is None:
            s.add(Project(legacy_id=RES2,
                          doc={"id": RES2, "name": RES2, "signals": {}, "events": []}))
        s.commit()
    set_extractor_override(StubExtractor({
        hashlib.sha256(doc("OPS")).hexdigest(): ("monthly_report", FULL),
        hashlib.sha256(doc("RES")).hexdigest(): ("monthly_report", FULL),
        hashlib.sha256(doc("ABST")).hexdigest(): ("monthly_report", NO_BAC),
        hashlib.sha256(doc("RES2")).hexdigest(): ("monthly_report", FULL),
    }))
    scenario3 = post({"action": "adminscenariocreate", "session_token": admin,
                      "scenario_version": "coa-s3", "project_type": "construction",
                      "period_count": 2, "evidence_package_id": RES2})["scenario_id"]
    rp2 = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "COA-RES-P2", "role": "Participant",
                "account_type": "research"})
    rtok2 = post({"action": "researchlogin",
                  "access_token": rp2["access_token"]})["session_token"]
    post({"action": "consentgrant", "session_token": rtok2, "consent_version": "v1.0"})
    post({"action": "intakesave", "session_token": rtok2,
          "responses": {"experience_level": "mid", "years_experience": 8}})
    post({"action": "adminassign", "session_token": admin,
          "participant_id": rp2["participant_id"], "order_group": "GCOA",
          "scenario_set": "SET-COA", "scenario_ids": [scenario3]})
    post({"action": "adminmemberadd", "session_token": admin, "id": RES2,
          "participant_id": rp2["participant_id"], "project_role": "PM"})
    post({"action": "adminmemberadd", "session_token": admin, "id": RES2,
          "participant_id": obs_id, "project_role": "Observer"})
    post({"action": "projectupload", "session_token": rtok2, "id": RES2, "period": 1,
          "documents": [{"filename": "RES2.pdf", "mimeType": "application/pdf",
                         "dataBase64": b64(doc("RES2"))}]})
    post({"action": "projectcompute", "session_token": rtok2, "id": RES2, "period": 1})

    obs_read = post({"action": "projectresults", "session_token": obs, "id": RES2,
                     "period": 1})
    obs_regret = modules_of(obs_read["result"]).get("Regret_Minimization")
    check(obs_read.get("ok") is True, "the operational-account observer can read the project")
    check(obs_regret is not None and obs_regret.get("expected_regret") is None,
          "AN OPERATIONAL ACCOUNT READING A RESEARCH PROJECT IS STILL GATED: the branch is on "
          "the project, not the caller", str(obs_regret))
    check("escalate" not in json.dumps(obs_read),
          "and nothing action-bearing leaks to that observer")

    # 4b. A research project whose PM membership is REVOKED. project_decision_state resolves
    # no decision at all in that state, so a gate keyed on the Decision row would release it.
    with Session() as s:
        pm_row = s.scalar(select(ProjectMember).join(
            Project, Project.id == ProjectMember.project_id).where(
                Project.legacy_id == RES2,
                ProjectMember.user_key == rp2["participant_id"]))
        pm_row.revoked_at = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc)
        s.commit()

    revoked_read = post({"action": "projectresults", "session_token": obs, "id": RES2,
                         "period": 1})
    rev_regret = modules_of(revoked_read["result"]).get("Regret_Minimization")
    check(revoked_read.get("ok") is True,
          "the observer can still read the project after the PM row is revoked")
    check(rev_regret is not None and rev_regret.get("expected_regret") is None,
          "A RESEARCH PROJECT WITH NO RESOLVABLE DECISION IS STILL GATED: the Decision row is "
          "not the discriminator", str(rev_regret))
    check("escalate" not in json.dumps(revoked_read),
          "and nothing action-bearing leaks in that state either")

    print()
    print("=" * 78)
    print("5. The predicate itself, read directly")
    print("=" * 78)

    from app.research_membership import project_under_research_protocol  # noqa: E402
    with Session() as s:
        ops_p = s.scalar(select(Project).where(Project.legacy_id == OPS))
        res_p = s.scalar(select(Project).where(Project.legacy_id == RES))
        check(project_under_research_protocol(s, ops_p) is False,
              "a project no scenario names is not under the research protocol")
        check(project_under_research_protocol(s, res_p) is True,
              "a project a scenario names as its evidence package is")

except Exception as exc:  # noqa: BLE001
    FAILED += 1
    print(f"  ****  UNCAUGHT EXCEPTION: {type(exc).__name__}: {exc}")
    import traceback
    traceback.print_exc()

print()
print("=" * 78)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
print("=" * 78)
sys.exit(1 if FAILED else 0)
