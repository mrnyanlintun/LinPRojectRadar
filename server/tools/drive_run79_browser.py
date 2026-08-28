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
import base64, hashlib, io, json, logging, os, pathlib, socket, sys, threading, time

LABEL = sys.argv[1] if len(sys.argv) > 1 else "run79"
OUT = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("run79_capture.json")
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

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
PID = f"PRJ-R79-{STAMP}"
ADMIN = f"run79-admin-{STAMP}"
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
        s.add(Participant(pseudonymous_code=f"R79-ADMIN-{STAMP}", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID)) is None:
        s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 79 reproduction",
                                          "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"R79-PM-{STAMP}", "role": "Participant",
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


def results(period=None):
    pr = post({"action": "projectperiods", "session_token": PM, "id": PID})
    LP = period if period is not None else pr.get("latest_computed_period")
    res = post({"action": "projectresults", "session_token": PM, "id": PID, "period": LP})
    return LP, (res.get("result") or {})

def listrow():
    lst = post({"action": "list", "session_token": PM})
    for p in (lst.get("projects") or lst.get("items") or []):
        if p.get("id") == PID:
            return p
    return {"_missing": True, "_keys": sorted(lst)}


# ------------------------------------------------------------------------------ PART A PROOFS
# A1 is called through the REAL action, exactly as the panel's "Call" button calls it.
LP = post({"action": "projectperiods", "session_token": PM, "id": PID})["latest_computed_period"]
A1 = post({"action": "projectcategoryapply", "session_token": PM, "id": PID,
           "period": LP, "category": "A1"})

# ------------------------------------------------------------------------------------ BROWSER
sock = socket.socket(); sock.bind(("127.0.0.1", 0)); PORT = sock.getsockname()[1]; sock.close()
import uvicorn  # noqa: E402
cfg = uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="critical")
server = uvicorn.Server(cfg)
threading.Thread(target=server.run, daemon=True).start()
for _ in range(200):
    try:
        c = socket.create_connection(("127.0.0.1", PORT), 0.2); c.close(); break
    except OSError:
        time.sleep(0.05)
BASE = f"http://127.0.0.1:{PORT}"
from playwright.sync_api import sync_playwright  # noqa: E402

# WHAT THE PAGE SAYS. Read off the RENDERED DOM only -- this harness never primes a row and
# never asks the server a question the page did not ask (Run 61's rule, machine-enforced).
CAPTURE_JS = r"""() => {
  const qa = (s) => Array.from(document.querySelectorAll(s));
  const txt = (e) => e ? (e.textContent || '').replace(/\s+/g,' ').trim() : null;

  // 1. THE ORDERED SECTION IDS, from the DOM, for Part C.
  const sections = qa('#detail-root .collapse-section').map(e => e.id.replace(/^section-/,''));

  // 2. THE CATEGORY PANEL, module by module.
  const panel = {};
  qa('.detail-catspecs .dcat-row').forEach(r => {
    const key = r.getAttribute('data-category');
    const mods = {};
    qa('.dcat-mod', r);
    Array.from(r.querySelectorAll('.dcat-mod')).forEach(m => {
      mods[m.getAttribute('data-module')] = {
        state: m.getAttribute('data-state'),
        value: txt(m.querySelector('.dcat-val')),
        band: txt(m.querySelector('.dcat-band'))
      };
    });
    panel[key] = { state: r.getAttribute('data-state'),
                   status: txt(r.querySelector('.dcat-status')),
                   note: txt(r.querySelector('.dcat-note')),
                   modules: mods };
  });

  // 3. THE SIGNAL LEDGER, as rendered.
  const ledgerRoot = document.querySelector('.detail-ledger');
  const ledger = {
    text: txt(ledgerRoot),
    rows: qa('.detail-ledger [data-module-id], .detail-ledger .cat-mod-row').map(txt),
    numbers: (txt(ledgerRoot)||'').match(/[-$]?\d[\d,]*\.?\d*/g) || []
  };

  // 4. THE PROJECT SIGNAL NETWORK + SIGNAL FLOW, counted by lit node.
  const projnet = {};
  qa('.detail-projnet [data-module-id]').forEach(e => {
    projnet[e.getAttribute('data-module-id')] = e.getAttribute('data-status');
  });
  const flow = {};
  qa('.detail-neural-flow .lnf-nd').forEach(g => {
    const k = g.getAttribute('data-kind') || '?';
    flow[k] = flow[k] || {nodes:0, lit:0};
    flow[k].nodes++;
    if (g.getAttribute('data-active') === 'true') flow[k].lit++;
  });

  // 5. BRIEF, DECISION CARD, HEADER.
  const brief = txt(document.querySelector('#body-d-brief'));
  const decision = txt(document.querySelector('#body-d-decision'));
  const header = {
    text: txt(document.querySelector('#detail-root .detail-head, #detail-root header')),
    statusPills: qa('#detail-root .pill, #detail-root .status-pill').map(txt).slice(0,12)
  };

  // 6. WHAT THE CLIENT'S OWN RESOLVER SAYS -- the row every surface reads.
  const p = (window.LIN_PROJECTS||[]).find(x => x.id === window.__R79_PID) || null;
  const row = (p && window.LinResults) ? window.LinResults.rowFor(p) : null;
  const resolver = {
    project_status: row ? row.project_status : null,
    category_statuses: row ? Object.keys(row.category_statuses||{}) : null,
    module_results: row ? (row.module_results||[]).map(m => [m.module_id, m.display, m.status_color]) : null,
    getCategoryStatus: {},
    storedResult_status: (p && p.storedResult) ? p.storedResult.project_status : null,
    project_doc_status: p ? p.status : null
  };
  // getCategoryStatus takes the taxonomy's lower-case category id, not the key.
  ['a1','a2','a3','a4','a5','a6','b1','b2','b3','b4','c1'].forEach(k => {
    resolver.getCategoryStatus[k] = window.getCategoryStatus ? window.getCategoryStatus(k, p) : 'nofn';
  });
  resolver.getModuleStatus_TCPI = window.getModuleStatus ? window.getModuleStatus('TCPI', p) : null;
  resolver.getModuleStatus_PERT = window.getModuleStatus ? window.getModuleStatus('PERT_Network_Criticality', p) : null;

  // 7. THE PORTFOLIO PAGE: the row for this project, and the Portfolio health card.
  const portfolio = {
    health_card: txt(document.querySelector('#ws-portfolio-list')),
    health_card_exists: !!document.getElementById('ws-portfolio-list'),
    health_heading: qa('.ws-card h3').map(txt).filter(t => /portfolio health/i.test(t||''))
  };
  return { sections, panel, ledger, projnet, flow, brief, decision, header, resolver, portfolio };
}"""

CAP = {}
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME,
                                 args=["--use-gl=swiftshader", "--no-sandbox", "--headless=new"])
    page = browser.new_page(viewport={"width": 1680, "height": 3600})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    for pat in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
        page.route(pat, lambda r: r.abort())
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.wait_for_timeout(9000)
    page.evaluate("(id) => { window.__R79_PID = id; }", PID)
    page.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('portfolio')")
    page.wait_for_timeout(4000)
    try:
        page.evaluate("() => window.LinApp && LinApp.buildFallbackList && LinApp.buildFallbackList()")
    except Exception:
        pass
    page.wait_for_timeout(2000)
    CAP["portfolio_page"] = page.evaluate(CAPTURE_JS)
    page.evaluate("(id) => window.LinDetail && LinDetail.render(id)", PID)
    page.wait_for_timeout(9000)
    # Open every section through the page's OWN toggle, so the lazily-built bodies exist.
    page.evaluate("""() => Array.from(document.querySelectorAll('#detail-root .collapse-section'))
        .forEach(s => { const id = s.id.replace(/^section-/,'');
                        if (!s.classList.contains('open') && window.toggleSection) toggleSection(id); })""")
    page.wait_for_timeout(9000)
    CAP["detail"] = page.evaluate(CAPTURE_JS)
    CAP["page_errors"] = errors
    browser.close()
server.should_exit = True

CAP["label"] = LABEL
CAP["project"] = PID
CAP["period"] = LP
CAP["A1_apply"] = A1
CAP["pm_token"] = PM
json.dump(CAP, OUT.open("w"), indent=2, default=str)
d = CAP["detail"]
print("project", PID, "period", LP)
print("SECTIONS:", d["sections"])
print("PANEL A1:", json.dumps(d["panel"].get("A1")))
print("PANEL A2:", json.dumps(d["panel"].get("A2")))
print("RESOLVER:", json.dumps(d["resolver"]))
print("LEDGER numbers:", d["ledger"]["numbers"][:20])
print("errors:", errors[:3])
print("capture ->", OUT)
