#!/usr/bin/env python3
"""
RUN 74. DID EXTRACTION STORE ANYTHING?

TST-007 IS NOT IN THIS REPOSITORY and neither are the owner's 27 documents (enumerated; see
the report). This harness therefore REPRODUCES THE SHAPE: 27 REAL reportlab-generated text
PDFs, whose text is verified readable by pdfplumber, uploaded into ONE project at PERIOD 1
through the REAL `projectupload` route, and then counts WHAT IS ACTUALLY STORED in the
`observations` table -- per document, per field.

It answers, by query and not by inference:
  1. how many observations exist for that project and period
  2. which documents they came from
  3. which fields, with their values

and measures the gap between WHAT THE PROMPT ASKED THE MODEL FOR and WHAT REACHED STORAGE.

argv[1] = label   argv[2] = output json
"""
from __future__ import annotations
import base64, hashlib, io, json, logging, os, pathlib, sys, time

LABEL = sys.argv[1] if len(sys.argv) > 1 else "run74"
OUT = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("run74_capture.json")
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)

from reportlab.lib.pagesizes import LETTER            # noqa: E402
from reportlab.pdfgen import canvas as rl_canvas      # noqa: E402
import pdfplumber                                     # noqa: E402
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
PID = f"PRJ-R74-{STAMP}"
ADMIN = f"run74-admin-{STAMP}"
PERIOD_END = "2026-03-31"

def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code} {r.text[:400]}"
    return r.json()

def b64(raw): return base64.b64encode(raw).decode()

# ------------------------------------------------------------- 27 documents, as the owner has
# filename -> doc_type. Named to mirror the owner's D01..D27 set.
DOCSET = [
    ("D01_contract_award.pdf",                  "contract_value"),
    ("D02_pay_application_01.pdf",              "pay_application"),
    ("D03_schedule_of_values.pdf",              "schedule_of_values"),
    ("D04_time_phased_schedule.pdf",            "time_phased_schedule"),
    ("D05_schedule_update.pdf",                 "schedule_update"),
    ("D06_monthly_report.pdf",                  "monthly_report"),
    ("D07_cost_report.pdf",                     "cost_report"),
    ("D08_resource_report.pdf",                 "resource_report"),
    ("D09_rfi_log.pdf",                         "rfi_log"),
    ("D10_rfa_log.pdf",                         "rfa_log"),
    ("D11_submittal_register.pdf",              "submittal_register"),
    ("D12_ncr_log.pdf",                         "ncr_log"),
    ("D13_inspection_report.pdf",               "inspection_report"),
    ("D14_quality_audit_report.pdf",            "quality_audit_report"),
    ("D15_safety_report.pdf",                   "safety_report"),
    ("D16_field_report.pdf",                    "field_report"),
    ("D17_oac_minutes.pdf",                     "oac_minutes"),
    ("D18_procurement_log.pdf",                 "procurement_log"),
    ("D19_lookahead_schedule.pdf",              "lookahead_schedule"),
    ("D20_subcontractor_report.pdf",            "subcontractor_report"),
    ("D21_change_order.pdf",                    "change_order"),
    ("D22_correspondence_notice.pdf",           "correspondence_notice"),
    ("D23_risk_register.pdf",                   "risk_register"),
    ("D24_environmental_compliance_report.pdf", "environmental_report"),
    ("D25_commissioning_report.pdf",            "commissioning_report"),
    ("D26_past_performance_report.pdf",         "past_performance_report"),
    ("D27_historical_project_data.pdf",         "historical_data"),
]

# A plausible, IN-RANGE value for every field the prompt asks the model for. Nothing invented
# about the platform: the VALUES are fixture data, the FIELD NAMES come from
# `extraction_fields_for` -- i.e. from the prompt's own contract.
VALUES = {
  "original_contract_sum": 4_000_000, "project_start_date": "2026-01-01",
  "project_end_date": "2027-06-30", "federal_acquisition": True,
  "contracting_agency": "General Services Administration",
  "acquisition_designation": "development", "major_acquisition": True,
  "agency_procedure_requires_evms": True, "evms_clause_id": "FAR 52.234-4",
  "award_date": "2026-01-01", "acquisition_id": "GS-P-26-0114",
  "amount_paid_to_date": 1_050_000, "completed_to_date": 1_000_000,
  "percent_complete_verified": 25.0, "application_date": PERIOD_END,
  "original_contingency": 200_000, "remaining_contingency": 90_000,
  "retainage_held": 52_500, "retainage_percent": 5.0,
  "scheduled_value_total": 4_000_000, "period_to_date": 1_000_000,
  "planned_value_to_date": 1_020_000, "planned_percent_complete": 25.5,
  "data_date": PERIOD_END, "baseline_curve_json": [
      {"Period": 0, "Period ending": "2025-12-31", "Planned value this period (USD)": 0,
       "Cumulative planned value (USD)": 0, "Cumulative planned spend (USD)": 0},
      {"Period": 1, "Period ending": PERIOD_END,
       "Planned value this period (USD)": 1_020_000,
       "Cumulative planned value (USD)": 1_020_000,
       "Cumulative planned spend (USD)": 1_000_000}],
  "baseline_version": "PMB Rev 2, reissued 2026-01-15",
  "baseline_approval_source": "Baseline Change Board record BCB-2026-004",
  "milestones_json": [
      {"Milestone": "MS-01", "Description": "Foundations complete",
       "Baseline finish": "2026-06-30", "Current finish": "2026-07-19"},
      {"Milestone": "MS-02", "Description": "Structure topped out",
       "Baseline finish": "2026-09-30", "Current finish": "2026-11-06"}],
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
  "planned_labor_hours": 120_000, "actual_labor_hours": 131_000,
  "planned_equipment_days": 400, "actual_equipment_days": 445,
  "resource_profile_json": [
      {"Period": "2026-03", "Trade": "Electrical",
       "Demand hours": 4000, "Available hours": 3500},
      {"Period": "2026-03", "Trade": "Mechanical",
       "Demand hours": 2000, "Available hours": 2500}],
  "resource_plan_version": "Resource Plan Rev 3",
  "quantity_installed_to_date": 8200, "quantity_planned_to_date": 9000,
  "quantity_unit": "linear metres of conduit",
  "quantity_source": "field quantity survey signed off by the superintendent",
  "rfi_total": 120, "rfi_open": 30, "rfi_answered": 90, "rfi_overdue": 8,
  "avg_response_days": 11, "rfi_period_days": 30, "oldest_open_days": 44,
  "log_date": PERIOD_END,
  "rfa_total": 60, "rfa_approved": 40, "rfa_rejected": 6, "rfa_resubmit": 8,
  "rfa_open": 6, "avg_review_days": 9,
  "submittals_total": 200, "submittals_rejected": 24, "submittals_overdue": 7,
  "ncr_issued": 14, "ncr_closed": 9, "ncr_open": 5, "report_period": PERIOD_END,
  "items_inspected": 300, "items_passed": 280, "items_failed": 20,
  "deficiency_count": 20, "critical_deficiency_count": 2,
  "total_findings": 18, "critical_findings": 3, "audit_score": 82,
  "audit_date": PERIOD_END,
  "osha_recordable_incidents": 2, "total_manhours": 180_000, "incident_rate": 2.2,
  "lost_time_incidents": 1,
  "weather_days_lost": 3, "float_remaining": 12,
  "quality_deficiencies_noted": 4, "safety_observations": 6,
  "environmental_observations": 1, "subcontractor_observations": 2,
  "subcontractor_issues_discussed": 3, "outstanding_action_items": 7,
  "subcontractor_disputes": 1, "safety_incidents_discussed": 2,
  "safety_actions_open": 3, "environmental_issues_discussed": 1,
  "quality_issues_discussed": 4, "weather_days_discussed": 3,
  "long_lead_items_total": 22, "on_schedule": 15, "at_risk": 5, "delayed": 2,
  "activities_planned": 40, "activities_constrained": 6,
  "constraint_rate": 0.15, "lookahead_weeks": 3,
  "scheduled_deliveries": 50, "on_time_deliveries": 44,
  "compliance_score": 88.0,
  "change_order_count": 3, "change_order_value": 145_000,
  "change_order_date": PERIOD_END, "cumulative_change_value": 145_000,
  "modifications_json": [
      {"Modification No": "M-001", "Date issued": "2026-02-10", "Federal": "Yes",
       "Modification type": "Bilateral", "Executed by": "J. Alvarez, Contracting Officer",
       "Authority reference": "Warrant CO-4471, unlimited",
       "Signatories": "J. Alvarez; Northgate Constructors",
       "SF30 applicable": "Yes", "Written instrument": "SF 30 dated 2026-02-10"}],
  "notice_served_by": "Northgate Constructors", "notice_served_on": "GSA",
  "notice_claim": "Extension of time, 14 days, differing site condition",
  "notice_date_served": "2026-03-12",
  "notice_contract_form": "FAR 52.243-4", "notice_kind": "delay",
  "notice_references": "RFI-044; Field Report FR-018",
  "permit_conditions_total": 40, "violations": 2, "compliance_rate": 0.95,
  "overall_rating": "Satisfactory", "schedule_rating": "Satisfactory",
  "cost_rating": "Marginal", "quality_rating": "Very Good",
  "source": "CPARS record for the prior contract",
  "analogous_overrun_pct": 8.5, "analogous_project_type": "federal courthouse fit-out",
  "completion_year": 2023, "similar_project_bac": 3_600_000,
  "similar_project_final_cost": 3_906_000,
  "document_risk_score": 0.4,
  "document_date": PERIOD_END,
}

def extraction_for(doc_type: str) -> dict:
    ex = {}
    for f in (extraction_fields_for(doc_type) or []):
        if f in VALUES:
            ex[f] = VALUES[f]
    ex.setdefault("document_date", PERIOD_END)
    return ex

# ---------------------------------------------------------------- REAL reportlab text PDFs
def make_pdf(filename: str, doc_type: str, ex: dict) -> bytes:
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=LETTER)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(72, 720, filename)
    c.setFont("Helvetica", 9)
    y = 700
    c.drawString(72, y, f"Document type: {doc_type}    Project: RUN74    Period 1 ending {PERIOD_END}")
    y -= 16
    c.drawString(72, y, f"run stamp {STAMP}")
    y -= 20
    for k, v in ex.items():
        s = json.dumps(v) if isinstance(v, (list, dict)) else str(v)
        for chunk in [s[i:i+90] for i in range(0, max(len(s), 1), 90)]:
            c.drawString(72, y, f"{k}: {chunk}")
            y -= 12
            if y < 60:
                c.showPage(); c.setFont("Helvetica", 9); y = 720
    c.showPage(); c.save()
    return buf.getvalue()

BYTES, OVERRIDE, EXPECTED = {}, {}, {}
for fn, dt in DOCSET:
    ex = extraction_for(dt)
    EXPECTED[fn] = ex
    raw = make_pdf(fn, dt, ex)
    BYTES[fn] = raw
    OVERRIDE[hashlib.sha256(raw).hexdigest()] = (dt, ex, 0.95)

# ----- PREMISE CHECK: does the text extract cleanly with pdfplumber, as the owner states?
TEXT_CHECK = {}
for fn, dt in DOCSET:
    with pdfplumber.open(io.BytesIO(BYTES[fn])) as pdf:
        text = "\n".join((p.extract_text() or "") for p in pdf.pages)
    want = [k for k in EXPECTED[fn] if not isinstance(EXPECTED[fn][k], (list, dict))]
    TEXT_CHECK[fn] = {"chars": len(text),
                      "field_names_present_as_text": sum(1 for k in want if k in text),
                      "field_names_requested": len(want)}

set_extractor_override(StubExtractor(OVERRIDE))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code=f"R74-ADMIN-{STAMP}", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID)) is None:
        s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 74 reproduction",
                                          "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"R74-PM-{STAMP}", "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PID,
      "participant_id": created["participant_id"], "project_role": "PM"})

# ------------------------------------------------------- THE REAL UPLOAD, all 27, period 1
UP = post({"action": "projectupload", "session_token": PM, "id": PID, "period": 1,
           "period_end": PERIOD_END,
           "documents": [{"filename": fn, "mimeType": "application/pdf",
                          "dataBase64": b64(BYTES[fn])} for fn, _ in DOCSET]})

# ---- NON-VACUITY: can the new success message FAIL? A second upload of ONE document that
# extracts cleanly and projects NO observation must be reported as having stored nothing.
VAC_RAW = make_pdf("stores_nothing.pdf", "commissioning_report", {"document_date": PERIOD_END})
OVERRIDE[hashlib.sha256(VAC_RAW).hexdigest()] = (
    "commissioning_report", {"document_date": PERIOD_END}, 0.9)
set_extractor_override(StubExtractor(OVERRIDE))
VAC = post({"action": "projectupload", "session_token": PM, "id": PID, "period": 2,
            "period_end": "2026-04-30",
            "documents": [{"filename": "stores_nothing.pdf", "mimeType": "application/pdf",
                           "dataBase64": b64(VAC_RAW)}]})

CR = post({"action": "projectcomputeall", "session_token": PM, "id": PID})

# ------------------------------------------------------------------ WHAT IS ACTUALLY STORED
with Session() as s:
    proj = s.scalar(select(Project).where(Project.legacy_id == PID))
    n_obs = s.scalar(select(func.count()).select_from(Observation)
                     .where(Observation.project_id == proj.id, Observation.period == 1))
    rows = s.execute(
        select(Document.filename, Observation.field, Observation.value,
               Observation.kind, Observation.source_doc_type)
        .join(Observation, Observation.document_id == Document.document_id)
        .where(Observation.project_id == proj.id, Observation.period == 1)
        .order_by(Document.filename, Observation.field)).all()
    docrows = s.execute(
        select(Document.filename, Document.doc_type, Document.extraction)
        .join(DocumentUpload, DocumentUpload.document_id == Document.document_id)
        .where(DocumentUpload.project_id == proj.id, DocumentUpload.period == 1)).all()

by_doc = {}
for fn, field, value, kind, sdt in rows:
    by_doc.setdefault(fn, []).append({"field": field, "value": value, "kind": kind})

GAP = {}
for fn, dt, ex in docrows:
    stored = {o["field"] for o in by_doc.get(fn, [])}
    GAP[fn] = {"doc_type": dt,
               "fields_the_prompt_asked_for": len(ex or {}),
               "observations_stored": len(stored),
               "extraction_keys": sorted((ex or {}).keys()),
               "stored_fields": sorted(stored)}

pr = post({"action": "projectperiods", "session_token": PM, "id": PID})
LP = pr.get("latest_computed_period")
res = post({"action": "projectresults", "session_token": PM, "id": PID, "period": LP})
ROW = res.get("result") or {}
MR = ROW.get("module_results") or []
CS = ROW.get("category_statuses") or {}
SI = ROW.get("signal_inputs") or {}

docs_with_fields = sum(1 for fn, _ in DOCSET if by_doc.get(fn))

print("=" * 100)
print(f"LABEL {LABEL}   project {PID}   DATABASE_URL={os.environ.get('DATABASE_URL')}")
print("-" * 100)
print("PREMISE CHECK -- reportlab text PDFs read by pdfplumber:")
bad = [f for f, v in TEXT_CHECK.items()
       if v["field_names_present_as_text"] < v["field_names_requested"]]
print(f"  27 PDFs generated; every requested scalar field name found as selectable text "
      f"in {27 - len(bad)}/27. shortfalls: {bad or 'none'}")
print("-" * 100)
print(f"UPLOAD RESPONSE ok={UP.get('ok')}  summary={UP.get('summary')}")
sts = {}
for f in UP.get("files", []):
    sts[f["status"]] = sts.get(f["status"], 0) + 1
print(f"  per-file statuses: {sts}")
print(f"  files reporting contributes=True: {sum(1 for f in UP.get('files',[]) if f.get('contributes'))}")
print(f"COMPUTE ok={CR.get('ok')}  error={str(CR.get('error'))[:200]}")
print("-" * 100)
print("NON-VACUITY -- one document that extracts and stores nothing, uploaded on its own:")
print(f"  ok={VAC.get('ok')}  summary={VAC.get('summary')}")
print(f"  all_accepted_documents_stored={VAC.get('all_accepted_documents_stored')}")
print(f"  stored_nothing_filenames={VAC.get('stored_nothing_filenames')}")
for f in VAC.get("files", []):
    print(f"    {f['filename']} status={f['status']} contributes={f['contributes']} "
          f"stored={f['stored']} fields_stored={f['fields_stored']}")
    print(f"    note: {f.get('note')}")
print("-" * 100)
print(f"OBSERVATIONS STORED for {PID} period 1: {n_obs}")
print(f"DOCUMENTS SHOWING EXTRACTED FIELDS (>=1 observation): {docs_with_fields} / 27")
print(f"MODULES HOLDING A CURRENT RESULT: {len(MR)} / 63")
print(f"CATEGORIES CARRYING A STATUS: {len([k for k,v in CS.items() if (v or {}).get('status')])} / 11")
print(f"signal_inputs.sources entries: {len((SI.get('sources') or {}))}")
print("-" * 100)
print(f"{'document':44s} {'type':24s} asked stored  DROPPED")
tot_asked = tot_stored = 0
for fn, _ in DOCSET:
    g = GAP.get(fn)
    if not g:
        print(f"{fn:44s} {'-- NO DOCUMENT ROW --'}")
        continue
    d = g["fields_the_prompt_asked_for"] - g["observations_stored"]
    tot_asked += g["fields_the_prompt_asked_for"]; tot_stored += g["observations_stored"]
    print(f"{fn:44s} {str(g['doc_type']):24s} {g['fields_the_prompt_asked_for']:5d} "
          f"{g['observations_stored']:6d}  {d:5d}"
          + ("   <-- STORED NOTHING" if g["observations_stored"] == 0 else ""))
print(f"{'TOTAL':44s} {'':24s} {tot_asked:5d} {tot_stored:6d}  {tot_asked-tot_stored:5d}")
print("=" * 100)

OUT.write_text(json.dumps({
    "label": LABEL, "project": PID, "observations": n_obs,
    "documents_with_fields": docs_with_fields,
    "modules": len(MR),
    "categories": len([k for k, v in CS.items() if (v or {}).get("status")]),
    "upload_summary": UP.get("summary"), "upload_ok": UP.get("ok"),
    "compute_ok": CR.get("ok"),
    "gap": GAP, "by_doc": by_doc, "text_check": TEXT_CHECK,
    "sources_count": len(SI.get("sources") or {}),
}, indent=2, default=str), encoding="utf-8")
print(f"capture -> {OUT}")

# ------------------------------------------------------------------------------- BROWSER
if os.environ.get("RUN74_NO_BROWSER"):
    raise SystemExit(0)
import socket, threading  # noqa: E402
sock = socket.socket(); sock.bind(("127.0.0.1", 0)); PORT = sock.getsockname()[1]; sock.close()
import uvicorn  # noqa: E402
srv = uvicorn.Server(uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="critical"))
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(200):
    try:
        c = socket.create_connection(("127.0.0.1", PORT), 0.2); c.close(); break
    except OSError:
        time.sleep(0.05)
BASE = f"http://127.0.0.1:{PORT}"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
LABEL = LABEL
PIDS = [PID]

JS = r"""(pid) => {
  const secs = Array.from(document.querySelectorAll('.collapse-section[id^="section-"]'))
    .map(e => e.id.replace(/^section-/, ''));
  const rows = Array.from(document.querySelectorAll('.up-row')).map(tr => ({
    type: (tr.querySelector('.up-type')||{}).textContent,
    file: (tr.querySelector('.up-file')||{}).textContent,
    fields: (tr.querySelector('.up-fields')||{}).textContent,
    status: (tr.querySelector('.up-status')||{}).textContent.trim(),
  }));
  return {
    sections: secs,
    sphere_sections: secs.filter(s => s === 'd-web'),
    sphere_canvas: document.querySelectorAll('.sphere3d-canvas').length,
    sphere_buttons: document.querySelectorAll('.chart3d-btn').length,
    sphere_panels: document.querySelectorAll('.signal-web-panel').length,
    doc_rows: rows.length,
    rows_showing_fields: rows.filter(r => r.fields && r.fields !== 'not recorded').length,
    rows: rows,
  };
}"""

OPEN_ALL = r"""() => {
  let n = 0;
  document.querySelectorAll('.collapse-section[id^="section-"]').forEach(el => {
    const id = el.id.replace(/^section-/, '');
    try { if (!el.classList.contains('open')) { toggleSection(id); n++; } } catch (e) {}
  });
  return n;
}"""

from playwright.sync_api import sync_playwright  # noqa: E402
res = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME,
                           args=["--use-gl=swiftshader", "--no-sandbox", "--headless=new"])
    pg = b.new_page(viewport={"width": 1680, "height": 3200})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    for pat in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
        pg.route(pat, lambda r: r.abort())
    pg.goto(BASE + "/", wait_until="domcontentloaded")
    pg.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
    pg.goto(BASE + "/", wait_until="domcontentloaded")
    pg.add_style_tag(content="*,*::before,*::after{transition:none!important;animation:none!important}")
    pg.wait_for_timeout(9000)
    pg.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('workspace')")
    pg.wait_for_timeout(3000)
    pg.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('portfolio')")
    pg.wait_for_timeout(1500)
    print("loaded_project_ids:", pg.evaluate("() => (window.LIN_PROJECTS||[]).map(p=>p.id)"))
    print("LinDetail?", pg.evaluate("() => !!window.LinDetail"))
    for pid in [PID]:
        pg.evaluate("(id) => window.LinDetail && LinDetail.render(id)", pid)
        pg.wait_for_timeout(12000)
        pg.evaluate(OPEN_ALL)
        pg.wait_for_timeout(9000)
        res[pid] = pg.evaluate(JS, pid)
        print("  collapse-sections in DOM:", pg.evaluate("()=>document.querySelectorAll('.collapse-section').length"),
              " body html len:", pg.evaluate("()=>document.body.innerHTML.length"))
    res["_page_errors"] = errs
    b.close()

print("=" * 96); print("LABEL", LABEL)
for pid in [PID]:
    r = res[pid]
    print(f"--- {pid}")
    print(f"    sections ({len(r['sections'])}): {r['sections']}")
    print(f"    d-web present: {r['sphere_sections']}   .signal-web-panel={r['sphere_panels']} "
          f".sphere3d-canvas={r['sphere_canvas']} .chart3d-btn={r['sphere_buttons']}")
    print(f"    document rows: {r['doc_rows']}   rows showing fields: {r['rows_showing_fields']}")
    for row in r["rows"][:30]:
        print(f"      {str(row['file'])[:42]:44s} {str(row['fields'])[:66]}")
print("page errors:", res["_page_errors"][:5])
print("=" * 96)
pathlib.Path(str(OUT) + ".page.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
print("page capture ->", str(OUT) + ".page.json")
