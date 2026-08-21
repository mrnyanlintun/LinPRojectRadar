#!/usr/bin/env python3
"""Out-of-order upload equivalence probe. Drives the REAL /exec routes.

Usage: probe_order.py <order-csv> <out-json>
  order-csv e.g. "1,2,3,4" or "4,1,3,2"
Uploads the SAME documents for the same four periods, only the ORDER differs.
Dumps the complete derived analytical state for every period.
"""
from __future__ import annotations
import base64, hashlib, json, sys

sys.path.insert(0, __file__.rsplit("probe", 1)[0])
sys.path.insert(0, "/home/user/LinPRojectRadar/server")

from fastapi.testclient import TestClient
from sqlalchemy import select

import app.main as main
from app.documents import set_extractor_override
from app.extraction_client import StubExtractor
from app.models import Project
from app.research_identity import hash_access_token
from app.research_models import ComputedResult, Participant, DocumentUpload

ORDER = [int(x) for x in sys.argv[1].split(",")]
OUT = sys.argv[2]

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory

def post(payload):
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code}"
    return r.json()

def b64(raw): return base64.b64encode(raw).decode()

ADMIN = "probe-admin-token"
A = "PRJ-ORDER1"
B = "PRJ-ORDER2"

# Four periods of monthly report evidence. Deliberately identical content per period
# regardless of the upload order used.
PERIOD_FIELDS = {
 1: {"earned_value": 4_000_000, "actual_cost": 4_200_000, "planned_value": 4_100_000,
     "budget_at_completion": 10_000_000, "actual_percent_complete": 40.0,
     "planned_percent_complete": 41.0, "report_date": "2026-03-31", "document_date": "2026-03-31"},
 2: {"earned_value": 5_000_000, "actual_cost": 4_900_000, "planned_value": 5_100_000,
     "budget_at_completion": 10_000_000, "actual_percent_complete": 50.0,
     "planned_percent_complete": 51.0, "report_date": "2026-04-30", "document_date": "2026-04-30"},
 3: {"earned_value": 6_000_000, "actual_cost": 5_600_000, "planned_value": 6_050_000,
     "budget_at_completion": 10_000_000, "actual_percent_complete": 60.0,
     "planned_percent_complete": 61.0, "report_date": "2026-05-31", "document_date": "2026-05-31"},
 4: {"earned_value": 7_000_000, "actual_cost": 7_400_000, "planned_value": 6_900_000,
     "budget_at_completion": 10_000_000, "actual_percent_complete": 70.0,
     "planned_percent_complete": 69.0, "report_date": "2026-06-30", "document_date": "2026-06-30"},
}
PERIOD_END = {1: "2026-03-31", 2: "2026-04-30", 3: "2026-05-31", 4: "2026-06-30"}
OTHER = {"earned_value": 3_000_000, "actual_cost": 3_050_000, "planned_value": 3_020_000,
         "budget_at_completion": 9_000_000, "actual_percent_complete": 33.0,
         "planned_percent_complete": 34.0, "report_date": "2026-03-20",
         "document_date": "2026-03-20"}

def doc_bytes(tag): return f"%PDF-1.4 ORDER PROBE {tag}\n".encode()

RECORDED = {}
for p, f in PERIOD_FIELDS.items():
    RECORDED[hashlib.sha256(doc_bytes(f"P{p}")).hexdigest()] = ("monthly_report", f)
RECORDED[hashlib.sha256(doc_bytes("B1")).hexdigest()] = ("monthly_report", OTHER)
set_extractor_override(StubExtractor(RECORDED))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="PROBE-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    for legacy, name in ((A, "Order A"), (B, "Order B")):
        if s.scalar(select(Project).where(Project.legacy_id == legacy)) is None:
            s.add(Project(legacy_id=legacy, doc={"id": legacy, "name": name, "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "PROBE-PM", "role": "Participant",
                "account_type": "operational"})
pm_id = created["participant_id"]
pm = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
for legacy in (A, B):
    post({"action": "adminmemberadd", "session_token": admin, "id": legacy,
          "participant_id": pm_id, "project_role": "PM"})

post({"action": "projectupload", "session_token": pm, "id": B, "period": 1,
      "period_end": "2026-03-31",
      "documents": [{"filename": "B1.pdf", "mimeType": "application/pdf",
                     "dataBase64": b64(doc_bytes("B1"))}]})
post({"action": "projectcompute", "session_token": pm, "id": B, "period": 1})

# ---- THE ORDER UNDER TEST ----
upload_log = []
for p in ORDER:
    resp = post({"action": "projectupload", "session_token": pm, "id": A, "period": p,
                 "period_end": PERIOD_END[p],
                 "documents": [{"filename": f"P{p}.pdf", "mimeType": "application/pdf",
                                "dataBase64": b64(doc_bytes(f"P{p}"))}]})
    upload_log.append({"requested_period": p, "ok": resp.get("ok"),
                       "assigned_period": resp.get("period"),
                       "err": resp.get("error")})

post({"action": "projectcomputeall", "session_token": pm, "id": A})

# ---- READ BACK THE COMPLETE DERIVED STATE ----
state = {"order": ORDER, "upload_log": upload_log, "periods": {}}
COMPARED = ("period", "signal_inputs", "module_results", "category_statuses", "project_status",
            "simulation_version", "seed", "period_cutoff", "source_documents")
with Session() as s:
    pid = s.scalar(select(Project.id).where(Project.legacy_id == A))
    ups = s.execute(select(DocumentUpload.period, DocumentUpload.document_id,
                           DocumentUpload.period_end)
                    .where(DocumentUpload.project_id == pid)).all()
    state["uploads"] = sorted([[int(p), d, str(e)] for p, d, e in ups])
    for period in (1, 2, 3, 4):
        row = s.scalar(select(ComputedResult).where(
            ComputedResult.project_id == pid, ComputedResult.period == period,
            ComputedResult.superseded_by.is_(None)))
        if row is None:
            state["periods"][period] = None
            continue
        state["periods"][period] = {k: (str(getattr(row, k)) if k == "period_cutoff"
                                        else getattr(row, k)) for k in COMPARED}

state["results_action"] = {p: post({"action": "projectresults", "session_token": pm,
                                    "id": A, "period": p}) for p in (1, 2, 3, 4)}

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(state, fh, sort_keys=True, indent=1, default=str)
print("WROTE", OUT)
