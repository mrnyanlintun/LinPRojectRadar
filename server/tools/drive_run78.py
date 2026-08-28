#!/usr/bin/env python3
"""
RUN 78. THREE DEFECTS, MEASURED BY EXECUTION ON A LOCAL REPRODUCTION.

TST-007 IS NOT IN THIS DATABASE. This builds the SHAPE through the REAL routes: real
reportlab PDFs, the real `projectupload`, the real `projectcomputeall`, and the real
`projectdocumentarchive`. Extraction is the StubExtractor (no ANTHROPIC_API_KEY here), so
the FIELD NAMES come from `extraction_fields_for` -- the prompt's own contract -- and the
values are fixture data.

argv[1] = label   argv[2] = output json
"""
from __future__ import annotations
import base64, hashlib, io, json, logging, os, pathlib, sys, time

LABEL = sys.argv[1] if len(sys.argv) > 1 else "run78"
OUT = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("run78_capture.json")
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)

from reportlab.lib.pagesizes import LETTER            # noqa: E402
from reportlab.pdfgen import canvas as rl_canvas      # noqa: E402
from fastapi.testclient import TestClient             # noqa: E402
from sqlalchemy import select, func                   # noqa: E402
import app.main as main                               # noqa: E402
from app.documents import set_extractor_override      # noqa: E402
from app.extraction_client import StubExtractor       # noqa: E402
from app.extraction_fields import extraction_fields_for  # noqa: E402
from app.models import Project                        # noqa: E402
from app.research_identity import hash_access_token   # noqa: E402
from app.research_models import Participant, Observation, Document, DocumentUpload  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
STAMP = int(time.time())
PID = f"PRJ-R78-{STAMP}"
ADMIN = f"run78-admin-{STAMP}"
PERIOD_END = "2026-03-31"

def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code} {r.text[:400]}"
    return r.json()

def b64(raw): return base64.b64encode(raw).decode()

DOCSET = [
    ("D01_contract_award.pdf",                  "contract_value"),
    ("D02_pay_application.pdf",                 "pay_application"),
    ("D03_schedule_of_values.pdf",              "schedule_of_values"),
    ("D04_time_phased_schedule.pdf",            "time_phased_schedule"),
    ("D06_monthly_report.pdf",                  "monthly_report"),
    ("D08_cost_report.pdf",                     "cost_report"),
    ("D09_rfi_log.pdf",                         "rfi_log"),
    ("D11_submittal_register.pdf",              "submittal_register"),
    ("D12_ncr_log.pdf",                         "ncr_log"),
    ("D14_quality_audit_report.pdf",            "quality_audit_report"),
    ("D15_safety_report.pdf",                   "safety_report"),
    ("D23_risk_register.pdf",                   "risk_register"),
    ("D26_past_performance_report.pdf",         "past_performance_report"),
    ("D27_historical_project_data.pdf",         "historical_data"),
]

VALUES = {
  "original_contract_sum": 4_000_000, "project_start_date": "2026-01-01",
  "project_end_date": "2027-06-30", "federal_acquisition": True,
  "contracting_agency": "General Services Administration",
  "acquisition_designation": "development", "major_acquisition": True,
  "agency_procedure_requires_evms": True, "evms_clause_id": "FAR 52.234-4",
  "award_date": "2026-01-01", "acquisition_id": "GS-P-26-0114",
  "amount_paid_to_date": 1_050_000, "completed_to_date": 1_000_000,
  "percent_complete_verified": 25.0, "application_date": PERIOD_END,
  "original_contingency": 920_000, "remaining_contingency": 892_400,
  "retainage_held": 52_500, "retainage_percent": 5.0,
  "scheduled_value_total": 4_000_000, "period_to_date": 1_000_000,
  "planned_value_to_date": 1_020_000, "planned_percent_complete": 25.5,
  "data_date": PERIOD_END,
  "baseline_version": "PMB Rev 2", "baseline_approval_source": "BCB-2026-004",
  "total_float_days": 12, "critical_path_length_days": 540,
  "earned_value": 1_000_000, "actual_cost": 1_050_000, "planned_value": 1_020_000,
  "actual_percent_complete": 25.0, "budget_at_completion": 4_000_000,
  "report_date": PERIOD_END,
  "indirect_cost_plan": 480_000, "indirect_cost_actual": 561_000,
  "material_cost_baseline": 900_000, "material_cost_current": 940_000,
  "overhead_allocation_base": "direct labour hours",
  "planned_allocation_base_quantity": 120_000,
  "actual_allocation_base_quantity": 131_000,
  "overhead_driver_source": "the overhead schedule printed in this cost report",
  "rfi_total": 120, "rfi_open": 30, "rfi_answered": 90, "rfi_overdue": 8,
  "avg_response_days": 11, "rfi_period_days": 30, "oldest_open_days": 44,
  "log_date": PERIOD_END,
  "submittals_total": 200, "submittals_rejected": 24, "submittals_overdue": 7,
  "ncr_issued": 14, "ncr_closed": 9, "ncr_open": 5, "report_period": PERIOD_END,
  "total_findings": 18, "critical_findings": 3, "audit_score": 82,
  "audit_date": PERIOD_END,
  "osha_recordable_incidents": 2, "total_manhours": 180_000, "incident_rate": 2.2,
  "lost_time_incidents": 1,
  "overall_rating": "Satisfactory", "schedule_rating": "Satisfactory",
  "cost_rating": "Marginal", "quality_rating": "Very Good",
  "source": "CPARS record for the prior contract",
  "analogous_overrun_pct": 9.0, "analogous_project_type": "federal courthouse fit-out",
  "completion_year": 2023, "similar_project_bac": 3_600_000,
  "similar_project_final_cost": 3_906_000,
  "document_risk_score": 0.4, "document_date": PERIOD_END,
}

def extraction_for(doc_type: str) -> dict:
    ex = {}
    for f in (extraction_fields_for(doc_type) or []):
        if f in VALUES:
            ex[f] = VALUES[f]
    ex.setdefault("document_date", PERIOD_END)
    return ex

def make_pdf(filename: str, doc_type: str, ex: dict) -> bytes:
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=LETTER)
    c.setFont("Helvetica-Bold", 13); c.drawString(72, 720, filename)
    c.setFont("Helvetica", 9); y = 700
    c.drawString(72, y, f"Document type: {doc_type}  Period 1 ending {PERIOD_END}"); y -= 16
    c.drawString(72, y, f"run stamp {STAMP}"); y -= 20
    for k, v in ex.items():
        s = json.dumps(v) if isinstance(v, (list, dict)) else str(v)
        for chunk in [s[i:i+90] for i in range(0, max(len(s), 1), 90)]:
            c.drawString(72, y, f"{k}: {chunk}"); y -= 12
            if y < 60:
                c.showPage(); c.setFont("Helvetica", 9); y = 720
    c.showPage(); c.save()
    return buf.getvalue()

BYTES, OVERRIDE, EXPECTED = {}, {}, {}
for fn, dt in DOCSET:
    ex = extraction_for(dt); EXPECTED[fn] = ex
    raw = make_pdf(fn, dt, ex); BYTES[fn] = raw
    OVERRIDE[hashlib.sha256(raw).hexdigest()] = (dt, ex, 0.95)
set_extractor_override(StubExtractor(OVERRIDE))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code=f"R78-ADMIN-{STAMP}", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID)) is None:
        s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 78 reproduction",
                                          "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"R78-PM-{STAMP}", "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PID,
      "participant_id": created["participant_id"], "project_role": "PM"})

UP = post({"action": "projectupload", "session_token": PM, "id": PID, "period": 1,
           "period_end": PERIOD_END,
           "documents": [{"filename": fn, "mimeType": "application/pdf",
                          "dataBase64": b64(BYTES[fn])} for fn, _ in DOCSET]})
CR = post({"action": "projectcomputeall", "session_token": PM, "id": PID})

def snapshot(tag):
    pr = post({"action": "projectperiods", "session_token": PM, "id": PID})
    LP = pr.get("latest_computed_period")
    res = post({"action": "projectresults", "session_token": PM, "id": PID, "period": LP})
    ROW = res.get("result") or {}
    SI = ROW.get("signal_inputs") or {}
    MR = ROW.get("module_results") or []
    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == PID))
        obs = s.execute(
            select(Document.filename, Observation.field, Observation.value,
                   Observation.source_doc_type, Observation.document_id,
                   Observation.withdrawn_at, Observation.withdrawn_by,
                   Observation.withdrawn_by_event_id)
            .join(Observation, Observation.document_id == Document.document_id)
            .where(Observation.project_id == proj.id, Observation.period == 1)).all()
    return {"tag": tag, "period": LP, "si": SI, "modules": MR,
            "obs": [{"file": o[0], "field": o[1], "value": o[2], "sdt": o[3], "doc": o[4],
                     "withdrawn_at": o[5], "withdrawn_by": o[6], "withdrawn_event": o[7]}
                    for o in obs]}

A = snapshot("before_archive")
A["uploadstatus"] = post({"action": "projectuploadstatus", "session_token": PM, "id": PID, "period": 1})

# ---------------------------------------------------------------- ARCHIVE ONE DOCUMENT
ST = post({"action": "projectuploadstatus", "session_token": PM, "id": PID, "period": 1})
docid = None
for d in (ST.get("documents") or []):
    if d.get("filename") == "D02_pay_application.pdf":
        docid = d.get("document_id")
ARCH = post({"action": "projectdocumentarchive", "session_token": PM, "id": PID, "period": 1,
             "document_ids": [docid],
             "confirmation": "Withdraw D02_pay_application.pdf from period 1."})
CR2 = post({"action": "projectcomputeall", "session_token": PM, "id": PID})
B = snapshot("after_archive")
B["uploadstatus"] = post({"action": "projectuploadstatus", "session_token": PM, "id": PID, "period": 1})

json.dump({"label": LABEL, "project": PID, "upload": UP, "compute": CR,
           "archive": ARCH, "recompute": CR2, "archived_document_id": docid,
           "upload_status_before": ST,
           "before": A, "after": B}, OUT.open("w"), indent=2, default=str)
print(f"project {PID}  archived_doc={docid}")
print(f"upload ok={UP.get('ok')} compute ok={CR.get('ok')} archive ok={ARCH.get('ok')} recompute ok={CR2.get('ok')}")
print(f"capture -> {OUT}")
