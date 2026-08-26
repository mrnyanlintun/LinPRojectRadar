#!/usr/bin/env python3
"""
RUN 66. EXTRACT WHAT THE DOCUMENTS STATE, AND COUNT WHAT COMPUTES BEFORE AND AFTER.

The number this run exists to move: how many of the eleven project-level categories carry a
status on a project built through the real routes (`projectupload` then `projectcompute`).

THE FIXTURE STATES THE DOCUMENT TYPES THAT PRODUCE COMPUTING MODULES TODAY (Run 64's
execution result): EVM documents across two periods (A1), a pay application carrying the
contingency pair (A3), an RFI log with its period, a submittal register, and an NCR log
paired with an inspection report (A4), and the quality/safety/environmental reports (A6).

THE VERIFICATION RULE (Run 61) IS FOLLOWED: loaded from the server, nothing pre-primed --
this file never calls LinResults.prime -- the current period is not 1, and the WebGL panels
are opened one at a time.

argv[1] = label   argv[2] = path to write the captured JSON to
"""
from __future__ import annotations
import base64, hashlib, json, logging, os, pathlib, socket, sys, threading, time

LABEL = sys.argv[1] if len(sys.argv) > 1 else "run68"
OUT = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("run68_capture.json")
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402
import app.main as main  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.extraction_client import StubExtractor  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import Participant  # noqa: E402
from app.simulation.registry import registry_index, service_index, CORE_VOTING_MODULES  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory

def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code} {r.text[:300]}"
    return r.json()

def b64(raw): return base64.b64encode(raw).decode()

D = "PRJ-R68"
ADMIN = "run68-admin-token"
BAC = 4_000_000
END = {1: "2026-03-31", 2: "2026-04-30"}
P1 = {"ev": 1_000_000, "ac": 1_050_000, "pv": 1_020_000, "planned_pct": 25.50, "actual_pct": 25.00}
P2 = {"ev": 2_000_000, "ac": 2_100_000, "pv": 1_500_000, "planned_pct": 50.00, "actual_pct": 50.00}

# RUN 68. THE BASELINE DOCUMENT'S OWN TABLE, WHICH IS THE DOCUMENT.
#
# `planned_value_to_date` gave the platform ONE POINT on this curve and three modules are defined
# on the whole of it. The table below is what a cost-loaded baseline prints: one row per period,
# the cumulative value planned to be complete by the end of it, and the cumulative amount planned
# to have been spent by then. The two are DIFFERENT CURVES and both are printed, because value
# earned and money spent are different quantities and A1.9 is defined on the second.
#
# THE ZERO ORIGIN ROW IS NOT DECORATION. `earned_schedule` measures in curve positions and its own
# oracle is "indexed from period 0", so a baseline that prints its origin puts position 2 at the
# end of period 2 and makes the schedule index a true ratio. A baseline printing from period 1
# does not, and `_baseline_structures` omits the elapsed time rather than report an index that is
# wrong by one period. This document prints the origin, as a cost-loaded baseline does.
#
# EVERY FIGURE HERE IS THE DOCUMENT'S. Periods 1 and 2 carry exactly the planned values the same
# documents already state through `planned_value_to_date` (1,020,000 and 1,500,000), so the table
# and the scalar field cannot disagree, and the profile runs out to the 4,000,000 contract sum the
# contract states. A PERIODIC column is printed beside the cumulative one precisely because a real
# baseline prints both, and the reader must be seen to refuse it.
BASELINE_ROWS = [
    {"Period": 0, "Period ending": "2025-12-31",
     "Planned value this period (USD)": 0,
     "Cumulative planned value (USD)": 0,
     "Cumulative planned spend (USD)": 0},
    {"Period": 1, "Period ending": "2026-03-31",
     "Planned value this period (USD)": 1_020_000,
     "Cumulative planned value (USD)": 1_020_000,
     "Cumulative planned spend (USD)": 1_000_000},
    {"Period": 2, "Period ending": "2026-04-30",
     "Planned value this period (USD)": 480_000,
     "Cumulative planned value (USD)": 1_500_000,
     "Cumulative planned spend (USD)": 1_460_000},
    {"Period": 3, "Period ending": "2026-05-31",
     "Planned value this period (USD)": 800_000,
     "Cumulative planned value (USD)": 2_300_000,
     "Cumulative planned spend (USD)": 2_250_000},
    {"Period": 4, "Period ending": "2026-06-30",
     "Planned value this period (USD)": 800_000,
     "Cumulative planned value (USD)": 3_100_000,
     "Cumulative planned spend (USD)": 3_050_000},
    {"Period": 5, "Period ending": "2026-07-31",
     "Planned value this period (USD)": 600_000,
     "Cumulative planned value (USD)": 3_700_000,
     "Cumulative planned spend (USD)": 3_650_000},
    {"Period": 6, "Period ending": "2026-08-31",
     "Planned value this period (USD)": 300_000,
     "Cumulative planned value (USD)": 4_000_000,
     "Cumulative planned spend (USD)": 3_950_000},
]
BASELINE_PROVENANCE = {
    "baseline_version": "PMB Rev 2, reissued 2026-01-15",
    "baseline_approval_source": "Approved by the Project Sponsor and the Contracting Officer, "
                                "Baseline Change Board record BCB-2026-004",
}

DOCS = [
    ("contract", 1, "contract_value",
     {"original_contract_sum": BAC, "project_start_date": "2026-01-01",
      "project_end_date": "2027-06-30"}),
    ("tps1", 1, "time_phased_schedule",
     {"planned_value_to_date": P1["pv"], "planned_percent_complete": P1["planned_pct"],
      "data_date": END[1], "document_date": END[1],
      "baseline_curve_json": BASELINE_ROWS, **BASELINE_PROVENANCE}),
    ("pay1", 1, "pay_application",
     {"amount_paid_to_date": P1["ac"], "completed_to_date": P1["ev"],
      "percent_complete_verified": P1["actual_pct"],
      "application_date": END[1], "document_date": END[1]}),
    ("tps2", 2, "time_phased_schedule",
     {"planned_value_to_date": P2["pv"], "planned_percent_complete": P2["planned_pct"],
      "data_date": END[2], "document_date": END[2],
      "baseline_curve_json": BASELINE_ROWS, **BASELINE_PROVENANCE}),
    # THE CONTINGENCY PAIR RIDES THE PAY APPLICATION, which is the document type that states it.
    ("pay2", 2, "pay_application",
     {"amount_paid_to_date": P2["ac"], "completed_to_date": P2["ev"],
      "percent_complete_verified": P2["actual_pct"],
      "original_contingency": 200_000, "remaining_contingency": 90_000,
      "application_date": END[2], "document_date": END[2]}),
    # RUN 66. THE MILESTONE TABLE THE SCHEDULE UPDATE STATES, ONE PER PERIOD.
    #
    # `milestones_json` is already asked of every `schedule_update` (extraction_fields.py) and
    # already read by `schedule_activities.read_activity_table` into the per-period schedule
    # store, from which `documents._milestone_forecast_history` assembles A2.7's structure. The
    # gap was never the schema: it was that no fixture uploaded a schedule update carrying the
    # table across two periods, so the store held fewer than two snapshots and A2.7 abstained on
    # its own guard. Nothing here is inferred: each row states a committed baseline finish and
    # the finish currently forecast, which is what the document itself carries.
    ("sched1", 1, "schedule_update",
     {"data_date": END[1], "document_date": END[1],
      "planned_percent_complete": P1["planned_pct"],
      "milestones_json": [
          {"Milestone": "MS-01", "Description": "Foundations complete",
           "Baseline finish": "2026-06-30", "Current finish": "2026-07-04"},
          {"Milestone": "MS-02", "Description": "Structure topped out",
           "Baseline finish": "2026-09-30", "Current finish": "2026-10-14"},
          {"Milestone": "MS-03", "Description": "Building watertight",
           "Baseline finish": "2026-12-15", "Current finish": "2026-12-15"},
      ]}),
    ("sched2", 2, "schedule_update",
     {"data_date": END[2], "document_date": END[2],
      "planned_percent_complete": P2["planned_pct"],
      "milestones_json": [
          {"Milestone": "MS-01", "Description": "Foundations complete",
           "Baseline finish": "2026-06-30", "Current finish": "2026-07-08"},
          {"Milestone": "MS-02", "Description": "Structure topped out",
           "Baseline finish": "2026-09-30", "Current finish": "2026-10-28"},
          {"Milestone": "MS-03", "Description": "Building watertight",
           "Baseline finish": "2026-12-15", "Current finish": "2026-12-11"},
      ]}),
    ("risk2", 2, "risk_register", {"document_date": END[2], "document_risk_score": 0.4}),
    ("rfi2", 2, "rfi_log",
     {"rfi_total": 120, "rfi_open": 30, "rfi_answered": 90, "rfi_overdue": 8,
      "avg_response_days": 11, "rfi_period_days": 30, "oldest_open_days": 44,
      "log_date": END[2], "document_date": END[2]}),
    ("sub2", 2, "submittal_register",
     {"submittals_total": 200, "submittals_rejected": 24, "document_date": END[2]}),
    ("ncr2", 2, "ncr_log",
     {"ncr_issued": 14, "ncr_closed": 9, "ncr_open": 5, "report_period": END[2],
      "document_date": END[2]}),
    ("insp2", 2, "inspection_report",
     {"items_inspected": 300, "items_passed": 280, "items_failed": 20,
      "deficiency_count": 20, "critical_deficiency_count": 2, "document_date": END[2]}),
    ("qa2", 2, "quality_audit_report",
     {"total_findings": 18, "critical_findings": 3, "deficiency_count": 18,
      "audit_score": 82, "audit_date": END[2], "document_date": END[2]}),
    ("safe2", 2, "safety_report",
     {"osha_recordable_incidents": 2, "total_manhours": 180_000, "incident_rate": 2.2,
      "report_period": END[2], "document_date": END[2]}),
    ("env2", 2, "environmental_report",
     {"permit_conditions_total": 40, "violations": 2, "compliance_rate": 0.95,
      "report_date": END[2], "document_date": END[2]}),
]


# ------------------------------------------------------------------ RUN 66: the register table
#
# `documents._persist_project_risks` reads the RISK ROWS FROM THE DOCUMENT'S OWN BYTES
# (`risk_register.risk_rows_from_document`), never from anything a model retyped, and only a
# .docx is openable on this side of the model boundary (`schedule_table` states that limit in
# its own words). So the fixture's register is a real .docx carrying a real table, built here
# with the standard library alone because python-docx is not installed in this environment.
# Every figure in it is stated by the document; nothing downstream supplies or substitutes one.
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def docx_with_table(rows: list[list[str]]) -> bytes:
    import io, zipfile
    def cell(t):
        return (f'<w:tc><w:p><w:r><w:t xml:space="preserve">{t}</w:t></w:r></w:p></w:tc>')
    body = "".join("<w:tr>" + "".join(cell(c) for c in r) + "</w:tr>" for r in rows)
    xml = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           f'<w:document xmlns:w="{W}"><w:body><w:tbl>{body}</w:tbl></w:body></w:document>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml",
                    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                    '<Default Extension="xml" ContentType="application/xml"/></Types>')
        zf.writestr("word/document.xml", xml)
    return buf.getvalue()


REGISTER_ROWS = [
    ["Risk ID", "Risk description", "Probability", "Cost impact (USD)", "Status"],
    ["R-01", "Design growth on the terminal fit-out package", "0.20", "240000", "Open"],
    ["R-02", "Market escalation on structural steel", "0.30", "180000", "Open"],
    ["R-03", "Differing site conditions at the north foundations", "0.15", "320000", "Open"],
    ["R-04", "Late utility diversion approval", "0.25", "120000", "Open"],
]
REGISTER_DOCX = docx_with_table(REGISTER_ROWS)
DOCX_MIME = ("application/vnd.openxmlformats-officedocument"
             ".wordprocessingml.document")

def doc_bytes(tag):
    if tag == "risk2":
        return REGISTER_DOCX
    return f"%PDF-1.4 RUN68 {tag}\n".encode()

set_extractor_override(StubExtractor({
    hashlib.sha256(doc_bytes(t)).hexdigest(): (ty, ex) for t, _p, ty, ex in DOCS}))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="R68-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == D)) is None:
        s.add(Project(legacy_id=D, doc={"id": D, "name": "Run 68 measurement fixture",
                                        "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"R68-PM-{int(time.time())}", "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": D,
      "participant_id": created["participant_id"], "project_role": "PM"})
for tag, per, _ty, _ex in DOCS:
    r = post({"action": "projectupload", "session_token": PM, "id": D, "period": per,
              "period_end": END[per],
              "documents": [{"filename": f"{tag}.docx" if tag == "risk2" else f"{tag}.pdf",
                             "mimeType": DOCX_MIME if tag == "risk2" else "application/pdf",
                             "dataBase64": b64(doc_bytes(tag))}]})
    assert r.get("ok") is True, str(r)[:300]
assert post({"action": "projectcomputeall", "session_token": PM, "id": D}).get("ok") is True

FIX = {"uploads": len(DOCS)}
per = post({"action": "projectperiods", "session_token": PM, "id": D})
FIX["latest_computed_period"] = per.get("latest_computed_period")
res = post({"action": "projectresults", "session_token": PM, "id": D,
            "period": FIX["latest_computed_period"]})
ROW = res.get("result") or {}
FIX["row_period"] = ROW.get("period")
_mr = ROW.get("module_results") or []
FIX["modules_holding_a_result"] = len(_mr)
FIX["module_ids"] = sorted(m.get("module_id") for m in _mr)
_cs = ROW.get("category_statuses") or {}
FIX["category_statuses"] = {k: (v or {}).get("status") for k, v in _cs.items()}
FIX["category_setter"] = {k: (v or {}).get("status_set_by") for k, v in _cs.items()}
FIX["CATEGORIES_CARRYING_A_STATUS"] = len([k for k, v in _cs.items() if (v or {}).get("status")])
FIX["project_status"] = ROW.get("project_status")
FIX["voting_module_ids"] = ROW.get("voting_module_ids")
FIX["gate_report_count"] = len(ROW.get("signal_qualification") or [])
# RUN 67. The band each computed module asserted, so the sweep for "computes and votes nothing"
# is read off the real path rather than off a module run in isolation.
FIX["no_band"] = sorted(m.get("module_id") for m in _mr if m.get("status_color") is None)
FIX["no_band_declared_calibration_pending"] = sorted(
    m.get("module_id") for m in _mr
    if m.get("status_color") is None and m.get("calibration_pending"))
_ab = ROW.get("abstained") or []
FIX["abstained_count"] = len(_ab)
FIX["still_refused_on_category9"] = sorted(
    a.get("module_id") for a in _ab if "Category-9" in (a.get("evidence_metric") or ""))
FIX["abstention_sentences"] = sorted({(a.get("evidence_metric") or "")[:110] for a in _ab})
FIX["no_band_UNDECLARED"] = sorted(
    m.get("module_id") for m in _mr
    if m.get("status_color") is None and not m.get("calibration_pending"))

print("=" * 96)
print(f"LABEL: {LABEL}")
print(f"repository root:  {ROOT}    DATABASE_URL: {os.environ.get('DATABASE_URL')}")
print(f"registry: {len(registry_index())}  in service: {len(service_index())}  "
      f"core voting: {sorted(CORE_VOTING_MODULES)}")
print("-" * 96)
for k, v in FIX.items():
    print(f"  {k:32} {v}")
print("=" * 96)

if os.environ.get("RUN68_FIXTURE_ONLY"):
    OUT.write_text(json.dumps({"label": LABEL, "fixture": FIX}, indent=2), encoding="utf-8")
    print(f"fixture-only capture written to {OUT}")
    raise SystemExit(0)

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

CAP = {"label": LABEL, "fixture": FIX}

ROW_JS = r"""(id) => {
  const p = (window.LIN_PROJECTS || []).filter(x => x.id === id)[0] || null;
  let row = null;
  try { row = (window.LinResults && LinResults.rowFor(p)) || null; } catch (e) {}
  const cs = (row && row.category_statuses) || {};
  return {
    row_present: !!row,
    row_period: row ? row.period : null,
    row_module_results: row && row.module_results ? row.module_results.length : null,
    row_cats_with_status: Object.keys(cs).filter(k => cs[k] && cs[k].status).length,
    row_cat_statuses: Object.keys(cs).reduce((a,k)=>{a[k]=cs[k]&&cs[k].status;return a;},{}),
    project_level_categories: (window.projectLevelCategories ? projectLevelCategories().length : null),
    cat_status_via_resolver: (function () {
      const o = {};
      (window.projectLevelCategories ? projectLevelCategories() : []).forEach(c => {
        let s = null;
        try { s = window.getCategoryStatus ? getCategoryStatus(c.id, p) : null; } catch(e){}
        o[c.id] = s;
      });
      return o;
    })(),
    LIT_ON_PAGE: (function () {
      let n = 0;
      (window.projectLevelCategories ? projectLevelCategories() : []).forEach(c => {
        let s = null;
        try { s = window.getCategoryStatus ? getCategoryStatus(c.id, p) : null; } catch(e){}
        if (s) n++;
      });
      return n;
    })()
  };
}"""

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME,
                                 args=["--use-gl=swiftshader", "--no-sandbox", "--headless=new"])
    page = browser.new_page(viewport={"width": 1680, "height": 3200})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    for pat in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
        page.route(pat, lambda r: r.abort())
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.add_style_tag(content="*,*::before,*::after{transition:none!important;animation:none!important}")
    page.wait_for_timeout(9000)
    page.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('workspace')")
    page.wait_for_timeout(3000)
    page.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('portfolio')")
    page.wait_for_timeout(1500)
    try:
        page.evaluate("() => window.LinApp && LinApp.buildFallbackList && LinApp.buildFallbackList()")
    except Exception:
        pass
    page.wait_for_timeout(1500)
    page.evaluate("(id) => window.LinDetail && LinDetail.render(id)", D)
    page.wait_for_timeout(12000)
    CAP["row_state"] = page.evaluate(ROW_JS, D)
    # ONE PANEL AT A TIME. The Project Signal Network is where category nodes are countable.
    for sec in ("d-projnet",):
        page.evaluate("""(id) => { const b = document.getElementById('body-' + id);
            if (b && b.style.display === 'none' && window.toggleSection) toggleSection(id); }""", sec)
        page.wait_for_timeout(8000)
    CAP["projnet_svg_text"] = page.evaluate(
        """() => { const r = document.querySelector('.projnet2d-panel');
                   return r ? Array.from(r.querySelectorAll('text'))
                       .map(t => (t.textContent||'').trim()).filter(Boolean) : []; }""")
    CAP["after_panels_row_state"] = page.evaluate(ROW_JS, D)
    CAP["page_errors"] = errors
    browser.close()

server.should_exit = True
OUT.write_text(json.dumps(CAP, indent=2), encoding="utf-8")
print("=" * 96)
print("BROWSER, ON THE RENDERED DETAIL PAGE:")
for k, v in CAP["after_panels_row_state"].items():
    print(f"  {k:32} {v}")
print(f"  projnet_svg_text: {CAP['projnet_svg_text']}")
print(f"page errors: {errors}")
print(f"capture written to {OUT}")
