#!/usr/bin/env python3
"""
RUN 22 SECTION 10. THE PERIOD-TRANSITION PARTIAL, RESOLVED AGAINST THE ACTUAL DESIGN.

WHAT RUN 21 LEFT PARTIAL AND WHY. Run 21 exercised two complete periods, the cross-assignment
roll, the next assignment's P1, and a server refusal of an invalid `researchadvance`. It did not
exercise a THIRD period inside one assignment, because the fixture it drove did not contain that
structure, and it recorded the gap as fixture shape rather than as an observed defect.

WHAT THE COMMITTED CONFIGURATION ACTUALLY SAYS, CHECKED RATHER THAN ASSUMED. There is no
study-wide period constant anywhere in production. `period_count` is a nullable integer column on
Scenario, supplied per scenario when an operator calls `adminscenariocreate`. The committed
provisioning record, `code_audit/run12_participant_provisioning.csv`, records the frozen project
packages as `period_count=2`. The locked praxis design describes one sequence per scenario ending
at "next-period project state, follow-up decision" -- an opening period and one follow-up -- and
the praxis decision log carries "whether the observation count needs raising via reporting
periods or an eighth project" as an OPEN question for the advisor, not a settled three-period
design.

SO NO THIRD PERIOD IS INVENTED. The owner's instruction is explicit: if an assignment legitimately
contains only two periods, do not invent a third-period requirement. It does, and this file does
not. Raising the period count is an owner and advisor decision recorded in
`code_audit/run22_owner_decisions_remaining.csv`, not an engineering gap.

WHAT THIS FILE DOES INSTEAD, AND WHY IT IS WORTH HAVING. It proves the transition machinery is
not accidentally specific to two. `period_count` is operator-supplied data, so if the advisor
later raises it the instrument must already behave correctly, and "it was never run with three"
would be the wrong answer at that point. A scenario is created with `period_count=3` and driven
P1 -> P2 -> P3, each period through the full locked sequence, and the server is required to refuse
the advance out of P3. This is GENERALISATION EVIDENCE ABOUT THE INSTRUMENT. It is not a claim
about the study protocol, and it changes no protocol, no randomisation and no stage order.
"""

from __future__ import annotations

import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

import app.main as main  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import (  # noqa: E402
    Assignment, Decision, Participant, Transition,
)

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory

_passed = 0
_total = 0
_fail: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    global _passed, _total
    _total += 1
    if cond:
        _passed += 1
    else:
        _fail.append(f"{name}" + (f" -- {detail}" if detail else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


ADMIN = "r22-period-admin"
STATES = ("R22-P1", "R22-P2", "R22-P3")

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="PM-R22", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    for legacy in STATES:
        if s.scalar(select(Project).where(Project.legacy_id == legacy)) is None:
            s.add(Project(legacy_id=legacy, doc={"id": legacy, "name": legacy, "signals": {}}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]

# ---------------------------------------------------- 1. the committed design, asserted

# period_count is DATA, not a constant. Pinned as a literal so that a future change turning it
# into a hard-coded two, or a hard-coded three, makes this red.
_two = post({"action": "adminscenariocreate", "session_token": admin,
             "scenario_version": "r22-two", "project_type": "construction",
             "period_count": 2, "evidence_package_id": STATES[0]})
check("a two-period scenario -- the structure the committed provisioning record freezes -- is "
      "accepted", _two.get("scenario_id") is not None, str(_two)[:160])

scenario = post({"action": "adminscenariocreate", "session_token": admin,
                 "scenario_version": "r22-three", "project_type": "construction",
                 "period_count": 3, "evidence_package_id": STATES[0]})["scenario_id"]
check("and a three-period scenario is accepted too, so the period count is operator-supplied "
      "data and not a constant the code assumes to be two", scenario is not None)

# C1 is one of the three configuration codes the server accepts (C0, C1, C2). An invented code
# is refused, which is the instrument enforcing the locked design rather than this suite choosing
# a convenient value.
post({"action": "adminconfigurationcreate", "session_token": admin, "code": "C1",
      "version": "v1", "freeze": True})
post({"action": "adminsequencecreate", "session_token": admin, "order_group": "GR22",
      "scenario_set": "SET-R22", "version": "v1", "positions": ["C1"], "freeze": True})
pkg = post({"action": "adminpackagecreate", "session_token": admin, "version": "r22-pkg",
            "provider_id": "frozen-store", "recommended_action": "Escalate", "freeze": True})
post({"action": "adminactionfamilycreate", "session_token": admin, "version": "r22-fam",
      "mappings": {"escalate": "escalate", "monitor": "accept"}, "freeze": True})

# A rule for EACH period, so the roll is driven by committed data at every step rather than by
# one rule that happens to be reused.
for period, nxt in (("P1", STATES[1]), ("P2", STATES[2])):
    r = post({"action": "admintransitionrulecreate", "session_token": admin,
              "scenario_id": scenario, "period": period, "action_family": "escalate",
              "version": "r22-rules", "freeze": True,
              "branches": [{"branch_id": f"B-{period}", "branch_version": "bv1",
                            "probability": "1.0", "next_state_id": nxt}]})
    check(f"a frozen transition rule exists for {period}", r.get("ok") is True, str(r)[:160])

c = post({"action": "adminparticipantcreate", "session_token": admin})
tok = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
post({"action": "consentgrant", "session_token": tok, "consent_version": "v1.0"})
post({"action": "intakesave", "session_token": tok,
      "responses": {"experience_level": "mid", "years_experience": 8}})
post({"action": "adminassign", "session_token": admin, "participant_id": c["participant_id"],
      "order_group": "GR22", "scenario_set": "SET-R22", "scenario_ids": [scenario]})
with Session() as s:
    a_id = s.scalar(select(Assignment).where(
        Assignment.participant_id == c["participant_id"])).assignment_id
post({"action": "adminpackageattach", "session_token": admin,
      "assignment_id": a_id, "package_id": pkg["package_id"]})

# ---------------------------------------------------- 2. P1 -> P2 -> P3, full locked sequence

# THE LOCKED SEQUENCE IS UNCHANGED AND IS RE-PROVED AT EACH PERIOD, not only at P1:
# evidence -> preliminary -> server lock -> reveal -> final -> server lock.
for n, period in enumerate(("P1", "P2", "P3"), start=1):
    ev = post({"action": "researchevidenceget", "session_token": tok})
    check(f"{period}: the participant is in {period} at the evidence stage",
          ev.get("period") == period and ev.get("current_stage") == "evidence", str(ev)[:180])
    check(f"{period}: the evidence shown is the state this period's rule routed to",
          ev.get("evidence", {}).get("id") == STATES[n - 1],
          f"{ev.get('evidence', {}).get('id')} expected {STATES[n - 1]}")

    early = post({"action": "researchreveal", "session_token": tok})
    check(f"{period}: NO AI BEFORE THE PRELIMINARY LOCK -- reveal is refused at the evidence "
          f"stage", early.get("ok") is False, str(early)[:180])

    post({"action": "researchprejudgment", "session_token": tok,
          "pre_action": "monitor", "pre_confidence": 50})
    mutate = post({"action": "researchprejudgment", "session_token": tok,
                   "pre_action": "escalate", "pre_confidence": 99})
    check(f"{period}: the preliminary judgment is LOCKED server-side and a second submission is "
          f"refused", mutate.get("ok") is False, str(mutate)[:180])

    rv = post({"action": "researchreveal", "session_token": tok})
    check(f"{period}: the package reveals only after the preliminary lock",
          rv.get("ok") is not False, str(rv)[:180])

    post({"action": "researchdecision", "session_token": tok, "final_action": "escalate",
          "disposition": "modify", "final_confidence": 70})
    remut = post({"action": "researchdecision", "session_token": tok,
                  "final_action": "monitor", "disposition": "accept", "final_confidence": 10})
    check(f"{period}: the final judgment is LOCKED and a second submission is refused",
          remut.get("ok") is False, str(remut)[:180])

    adv = post({"action": "researchadvance", "session_token": tok})
    if period == "P3":
        # THE END OF A THREE-PERIOD ASSIGNMENT. The refusal must name the scenario's own count,
        # which proves the server read the DATA rather than a built-in two.
        check("P3: the server REFUSES to advance out of the last period of a three-period "
              "scenario", adv.get("ok") is False, str(adv)[:200])
        check("P3: and the refusal names three periods, proving the limit came from the "
              "scenario's data and not from a constant",
              "3 period" in str(adv.get("error", "")), str(adv.get("error"))[:200])
    else:
        check(f"{period}: the advance succeeds and rolls to the next period",
              adv.get("ok") is True, str(adv)[:200])
        check(f"{period}: the branch that fired is the one this period's frozen rule declares",
              adv.get("branch_id") == f"B-{period}", str(adv.get("branch_id")))

# ---------------------------------------------------- 3. three periods really happened

with Session() as s:
    n_dec = s.scalar(select(func.count()).select_from(Decision).where(
        Decision.assignment_id == a_id)) or 0
    n_tr = s.scalar(select(func.count()).select_from(Transition)) or 0
    periods = sorted(r[0] for r in s.execute(
        select(Decision.period).where(Decision.assignment_id == a_id)).all())

# Pinned as literals. Comparing the count to len(periods) would compare a value with the
# expression that produced it and could never disagree.
check("exactly three decisions rows exist for this assignment, one per period", n_dec == 3,
      str(n_dec))
check("and they are P1, P2 and P3", periods == ["P1", "P2", "P3"], str(periods))
check("exactly two transitions rows exist: P1->P2 and P2->P3, and none out of P3",
      n_tr == 2, str(n_tr))

with Session() as s:
    p1 = s.scalar(select(Decision).where(Decision.assignment_id == a_id,
                                         Decision.period == "P1"))
    check("P1's decisions row was not mutated by anything in P2 or P3: its preliminary action is "
          "still the one submitted in P1", p1.pre_action == "monitor", str(p1.pre_action))
    check("and its final action is still P1's", p1.final_action == "escalate",
          str(p1.final_action))

print("\n".join(f"FAIL: {f}" for f in _fail))
print(f"RESULT: {_passed}/{_total} checks passed")
sys.exit(0 if _passed == _total else 1)
