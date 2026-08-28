#!/usr/bin/env python3
"""
RUN 80. THREE DEFECTS, MEASURED BY EXECUTION ON A LOCAL REPRODUCTION.

TST-007 IS NOT IN THIS DATABASE. This builds the SHAPE through the REAL routes: real
reportlab PDFs, the real `projectupload`, the real `projectcomputeall`, and the real
`projectdocumentarchive`. Extraction is the StubExtractor (no ANTHROPIC_API_KEY here), so
the FIELD NAMES come from `extraction_fields_for` -- the prompt's own contract -- and the
values are fixture data.

argv[1] = label   argv[2] = output json
"""
from __future__ import annotations
import base64, hashlib, io, json, logging, os, pathlib, sys, time

LABEL = sys.argv[1] if len(sys.argv) > 1 else "run80"
OUT = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("run80_capture.json")
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
PID = f"PRJ-R80F-{STAMP}"
ADMIN = f"run80-admin-{STAMP}"
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

  # ---- RUN 80. WHAT THE OWNER'S D26 AND D27 STATE, restated on the fixture documents so the
  # chain can be measured end to end. These are the owner's own figures.
  "analogous_project_name": "Cascade Hall Renewal",
  "analogous_adjustment_factor": 1.09,
  "analogous_source": "CPARS past performance record for the Cascade Hall Renewal contract",
  "analogous_comparability_basis": "same building type, same delivery method, same region, "
                                   "completed within three years",
  "analogous_normalization_basis": "adjusted to this project's price level and gross floor area",
  "cost_index_name": "ENR Building Cost Index",
  "cost_index_authority": "Engineering News Record",
  "cost_index_geography": "United States, 20-city average",
  "cost_index_scope": "building construction materials and labour",
  "cost_index_base_period": "2025-12", "cost_index_base_value": 14782,
  "cost_index_observation_period": "2026-03", "cost_index_current_value": 14861,
  "cost_index_vintage": "2026-03 publication",
  "reference_class_inclusion_criteria": "federal building projects between $10M and $50M "
                                        "completed 2019-2025",
  "reference_class_exclusion_criteria": "projects terminated for convenience or default",
  "reference_class_outcome_definition": "final contract value over award value, less one",
  "reference_class_normalization": "constant 2026 dollars",
  "reference_class_vintage": "2026-02 extract",
  "reference_class_governed_percentile": 80,
  "cost_index_cost_exposure": 1_800_000,
  "reference_class_json": [
      {"Project": f"RC-{i:02d}", "Award value": a, "Final value": f}
      for i, (a, f) in enumerate([
          (16900000, 17640000), (12400000, 13020000), (22800000, 25080000),
          (31500000, 32130000), (18200000, 20930000), (14700000, 14700000),
          (26300000, 29455000), (11900000, 12376000), (19400000, 22310000),
          (28100000, 28381000), (15600000, 17472000), (23900000, 24856000),
          (17300000, 19549000), (20500000, 21115000)], start=1)
  ],
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

# THE REGISTER IS A REAL .docx WITH A REAL TABLE. `documents._persist_project_risks` reads the
# risk rows from the DOCUMENT'S OWN BYTES via `risk_register.risk_rows_from_document`, and that
# reader opens only a .docx -- "a PDF is sent to the model as a document block and its tables
# are not available on this side of the boundary at all", in its own words. Run 78's fixture
# printed the register as a PDF, which is why it could not verify A3.6 at all. These five rows
# are the owner's D15: each with a probability and a cost impact and nothing else.
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

def docx_with_table(rows):
    import zipfile
    def cell(t):
        return f'<w:tc><w:p><w:r><w:t xml:space="preserve">{t}</w:t></w:r></w:p></w:tc>'
    body = "".join("<w:tr>" + "".join(cell(c) for c in r) + "</w:tr>" for r in rows)
    xml = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           f'<w:document xmlns:w="{W_NS}"><w:body><w:tbl>{body}</w:tbl></w:body></w:document>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml",
                    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                    '<Default Extension="xml" ContentType="application/xml"/></Types>')
        zf.writestr("word/document.xml", xml)
    return buf.getvalue()

REGISTER_ROWS = [
    ["Risk ID", "Risk description", "Probability", "Cost impact (USD)"],
    ["R-01", "Design growth on the fit-out package", "0.20", "240000"],
    ["R-02", "Market escalation on structural steel", "0.30", "180000"],
    ["R-03", "Differing site conditions at the north foundations", "0.15", "320000"],
    ["R-04", "Late utility diversion approval", "0.25", "120000"],
    ["R-05", "Commissioning delay on the central plant", "0.10", "260000"],
]
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

BYTES, OVERRIDE, EXPECTED, MIMES = {}, {}, {}, {}
for fn, dt in DOCSET:
    ex = extraction_for(dt); EXPECTED[fn] = ex
    if fn == "D23_risk_register.pdf":
        fn = "D23_risk_register.docx"
        raw = docx_with_table(REGISTER_ROWS); MIMES[fn] = DOCX_MIME
    else:
        raw = make_pdf(fn, dt, ex); MIMES[fn] = "application/pdf"
    BYTES[fn] = raw
    OVERRIDE[hashlib.sha256(raw).hexdigest()] = (dt, ex, 0.95)
DOCSET = [(("D23_risk_register.docx" if fn == "D23_risk_register.pdf" else fn), dt)
          for fn, dt in DOCSET]
set_extractor_override(StubExtractor(OVERRIDE))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code=f"R80-ADMIN-{STAMP}", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID)) is None:
        s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 80 reproduction",
                                          "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"R80-PM-{STAMP}", "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PID,
      "participant_id": created["participant_id"], "project_role": "PM"})

UP = post({"action": "projectupload", "session_token": PM, "id": PID, "period": 1,
           "period_end": PERIOD_END,
           "documents": [{"filename": fn, "mimeType": MIMES[fn],
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



# =====================================================================================
# RUN 80, FIX THREE and FIX TWO, MEASURED. This driver's docset above is REPLACED below with
# one that states, on the face of the documents, exactly what the owner's D15, D26 and D27
# state -- five risks with a probability and a cost impact, a named analogue with its award and
# final values and an adjustment factor, a named external index with two levels, and a
# fourteen-project reference class. Nothing here is supplied to a module; every figure is read
# off a document through the real upload route.
# =====================================================================================
print("second pass: the A3 documents")

from app.research_models import ComputedResult                 # noqa: E402
from app.simulation.registry import run_module, service_index   # noqa: E402
import datetime as _dt                                          # noqa: E402

with Session() as s:
    proj = s.scalar(select(Project).where(Project.legacy_id == PID))
    row = s.scalars(select(ComputedResult).where(ComputedResult.project_id == proj.id)
                    .order_by(ComputedResult.period.desc())).first()
    SI = dict(row.signal_inputs or {})

STRUCTS = ("analogEstimate", "externalCostIndex", "referenceClassPopulation",
           "costRiskModel", "originalContingency", "remainingContingency")
print("upload ok=%s compute ok=%s" % (UP.get("ok"), CR.get("ok")))
print("--- per-file unreadable_fields reported to the PM ---")
for f in (UP.get("files") or []):
    if f.get("unreadable_fields"):
        print(" ", f["filename"], "->", f["unreadable_fields"])
print("--- CPARS ratings as stored in signal_inputs ---")
print(" ", {k: SI.get(k) for k in ("overallRating", "scheduleRating",
                                   "costRating", "qualityRating")})
print("--- structures present on signal_inputs ---")
for k in STRUCTS:
    print(f"  {k}: {'PRESENT' if k in SI else 'absent'}")
print("--- the A3 modules on live stored inputs ---")
MODS = {}
for m in sorted(k for k in service_index() if k.startswith("A3")):
    r = run_module(m, SI, lambda: 0.5, _dt.date.fromisoformat(PERIOD_END))
    MODS[m] = r
    print(f"  {m}: insufficient={r.get('insufficient_data')} | {str(r.get('evidence_metric'))[:190]}")
print("--- A6.4 contractor performance on the word ratings ---")
_cp = run_module("A6.4", SI, lambda: 0.5, _dt.date.fromisoformat(PERIOD_END))
print("  ", str(_cp.get("evidence_metric"))[:200])

json.dump({"label": LABEL, "project": PID, "upload": UP, "compute": CR,
           "signal_inputs": SI, "a3": MODS}, OUT.open("w"), indent=2, default=str)
print("capture ->", OUT)
