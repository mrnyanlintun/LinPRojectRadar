#!/usr/bin/env python3
"""
RUN 16, WORKSTREAM A7 AND GATE 6. CLEAR-ALL INVALIDATES DERIVED SERVER STATE.

WHAT THIS PROVES AND WHY IT IS NOT ASSERTED IN THE BROWSER. The defect Run 16 found is not a
presentation fault: `resetsignals` cleared the project document and left `computed_results`
untouched, so the SERVER went on answering `projectresults` with a full set of module results,
category statuses and a project status whose inputs no longer existed. That survived a reload
because it was never a browser fact. It is therefore tested here, against the real write handler
and the real read path, through /exec.

WHAT IT DELIBERATELY DOES NOT DO. It does not assert the defect's own sentence, and it does not
assert against a copy of the invalidation logic: every expectation is stated as a property of
what a caller can observe (a live row exists / no live row exists / the superseded row is still
readable by its own id), which is the thing the participant surfaces depend on.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_run16_clear_all_invalidation.py
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.extraction_client import StubExtractor  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import ComputedResult, Participant  # noqa: E402

os.environ.setdefault("SESSION_SECRET", "test-secret-do-not-use-in-prod")
client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory

passed = total = 0
failures: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global passed, total
    total += 1
    if ok:
        passed += 1
    else:
        failures.append(f"{label}" + (f"  [{detail}]" if detail else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


ADMIN_TOKEN = "run16-clearall-admin"
FULL = "PRJ-R16T-FULL"
OTHER = "PRJ-R16T-OTHER"
DATE = "2026-03-31"


def payload_for(project: str) -> bytes:
    return f"%PDF-1.4 RUN16 TEST {project}\n".encode()


def monthly(evm_scale: float) -> dict:
    return {"earned_value": 3_000_000 * evm_scale, "actual_cost": 3_400_000 * evm_scale,
            "planned_value": 3_100_000 * evm_scale, "budget_at_completion": 12_000_000,
            "actual_percent_complete": 25.0, "planned_percent_complete": 26.0,
            "report_date": DATE, "document_date": DATE, "document_risk_score": 0.45}


set_extractor_override(StubExtractor({
    hashlib.sha256(payload_for(FULL)).hexdigest(): ("monthly_report", monthly(1.0)),
    hashlib.sha256(payload_for(OTHER)).hexdigest(): ("monthly_report", monthly(0.9)),
}))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="R16-CLEARALL-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN_TOKEN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN_TOKEN)
    for pid in (FULL, OTHER):
        if s.scalar(select(Project).where(Project.legacy_id == pid)) is None:
            s.add(Project(legacy_id=pid, doc={"id": pid, "name": pid, "signals": {},
                                              "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN_TOKEN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "R16-CLEARALL-PM", "role": "Participant",
                "account_type": "operational"})
pm = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
for pid in (FULL, OTHER):
    post({"action": "adminmemberadd", "session_token": admin, "id": pid,
          "participant_id": created["participant_id"], "project_role": "PM"})
    post({"action": "projectupload", "session_token": pm, "id": pid, "period": 1,
          "period_end": DATE,
          "documents": [{"filename": "M1.pdf", "mimeType": "application/pdf",
                         "dataBase64": base64.b64encode(payload_for(pid)).decode()}]})
    post({"action": "projectcomputeall", "session_token": pm, "id": pid})


def live_rows(pid: str) -> list:
    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == pid))
        return list(s.scalars(select(ComputedResult).where(
            ComputedResult.project_id == proj.id,
            ComputedResult.superseded_by.is_(None))).all())


def all_rows(pid: str) -> list:
    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == pid))
        return list(s.scalars(select(ComputedResult).where(
            ComputedResult.project_id == proj.id)).all())


# ---------------------------------------------------------------- BEFORE
before = post({"action": "projectresults", "session_token": pm, "id": FULL, "period": 1})
check(before.get("ok") is not False and "result" in before,
      "the populated project serves a stored result before the clear-all", str(before)[:120])
before_row = before.get("result") or {}
before_result_id = before_row.get("result_id")
check(bool(before_row.get("module_results")),
      "and that result carries module results", str(len(before_row.get("module_results") or [])))
check(len(live_rows(FULL)) == 1, "exactly one live derived row exists before the clear-all",
      str(len(live_rows(FULL))))
before_total = len(all_rows(FULL))

# ---------------------------------------------------------------- THE CLEAR-ALL
reset = post({"action": "resetsignals", "session_token": pm, "id": FULL})
check(reset.get("ok") is True and reset.get("reset") is True,
      "the supported clear-all workflow reports success", str(reset)[:160])
check(isinstance(reset.get("invalidated_results"), list)
      and len(reset["invalidated_results"]) == 1,
      "and reports exactly the one derived result it invalidated",
      str(reset.get("invalidated_results")))

# ---------------------------------------------------------------- AFTER, ON THE SERVER
check(live_rows(FULL) == [], "no derived result is live for the cleared project",
      str([r.result_id for r in live_rows(FULL)]))
after = post({"action": "projectresults", "session_token": pm, "id": FULL, "period": 1})
check(after.get("ok") is False,
      "and the read path serves no result at all rather than a stale one", str(after)[:160])
check("run projectcompute" in str(after.get("error") or ""),
      "the read path says what to do instead of failing silently", str(after.get("error"))[:120])

# ---------------------------------------------------------------- AUDIT LINEAGE IS RETAINED
check(len(all_rows(FULL)) == before_total,
      "the row is superseded, NOT deleted: the table still holds it",
      f"{len(all_rows(FULL))} vs {before_total}")
by_id = post({"action": "projectresults", "session_token": pm, "id": FULL, "period": 1,
              "result_id": before_result_id})
check("result" in by_id and by_id["result"].get("result_id") == before_result_id,
      "and a decision that referenced that exact result can still resolve it",
      str(by_id)[:140])
check(bool((by_id.get("result") or {}).get("module_results")),
      "with its module results intact, unchanged by the invalidation")

# ---------------------------------------------------------------- THE PROJECT DOCUMENT
# The stored project document itself, re-read from the database after the commit rather than
# through a projection: the event log is what is being checked and no read path is asked to
# vouch for it.
with Session() as s:
    proj = dict(s.scalar(select(Project).where(Project.legacy_id == FULL)).doc or {})
check(proj.get("signals") in ({}, None), "the project's signal blocks are cleared",
      str(proj.get("signals"))[:80])
check(proj.get("signalInputs") in ({}, None), "and its signal inputs are cleared",
      str(proj.get("signalInputs"))[:80])
events = [e for e in (proj.get("events") or []) if (e.get("event") or e.get("type")) == "signals_reset"]
check(len(events) == 1, "the reset is recorded as an event rather than by deleting one",
      str(len(events)))
check(events and events[0].get("invalidated_derived_results") == 1,
      "and that event records how many derived results it invalidated",
      str(events[0] if events else None)[:140])

# ---------------------------------------------------------------- NO CROSS-PROJECT LEAKAGE
check(len(live_rows(OTHER)) == 1,
      "a clear-all on one project leaves another project's live result alone",
      str(len(live_rows(OTHER))))
other = post({"action": "projectresults", "session_token": pm, "id": OTHER, "period": 1})
check("result" in other and bool(other["result"].get("module_results")),
      "and that other project still serves its own stored result")

# ---------------------------------------------------------------- IT IS RECOMPUTABLE AFTERWARDS
post({"action": "projectcomputeall", "session_token": pm, "id": FULL})
again = post({"action": "projectresults", "session_token": pm, "id": FULL, "period": 1})
check("result" in again, "the cleared project can be computed again", str(again)[:120])
check((again.get("result") or {}).get("result_id") != before_result_id,
      "and the recomputation is a NEW row, not the invalidated one revived")
check(len(live_rows(FULL)) == 1, "with exactly one live row again", str(len(live_rows(FULL))))

# ---------------------------------------------------------------- A SECOND CLEAR-ALL IS SAFE
post({"action": "resetsignals", "session_token": pm, "id": FULL})
r2 = post({"action": "resetsignals", "session_token": pm, "id": FULL})
check(r2.get("ok") is True and r2.get("invalidated_results") == [],
      "a clear-all on an already-cleared project succeeds and invalidates nothing",
      str(r2)[:140])

for f in failures:
    print("FAILED:", f)
print(f"RESULT: {passed}/{total} checks passed")
sys.exit(0 if passed == total else 1)
