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

LABEL = sys.argv[1] if len(sys.argv) > 1 else "run70"
OUT = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("run70_capture.json")
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

D = "PRJ-R70"
ADMIN = "run70-admin-token"
BAC = 4_000_000

# ------------------------------------------------------------------------------------- RUN 70
# EIGHT REPORTING PERIODS OF THE DOCUMENTS THIS PLATFORM ALREADY SUPPORTS.
#
# A1.5 ARIMA CPI Forecast is the only dark module in service whose own refusal names no missing
# DOCUMENT at all. Its words, read off the live run at 3dd890b:
#
#   "The cost performance history is too short for a time series model to be identified from it,
#    so no forecast is reported and no shorter substitute is used."
#
# `canonical_v3.identify_arima` takes `min_history: int = 8`, and `documents._period_history`
# builds `cpiHistory` from the project's own EARLIER live results, one reading per period. So the
# block is the number of periods, not the evidence: eight periods of the SAME pay application and
# time-phased schedule the fixture already uploads carry it. Nothing new is extracted and no field
# is invented. PERIODS 1 AND 2 STATE EXACTLY THE FIGURES THEY STATED AT RUN 69, so every module
# that computed then computes on the same numbers now.
#
# The baseline curve is extended to period 8 because a cost-loaded baseline that stopped at period
# 6 would not cover the status period, and a document may not be made to disagree with itself. The
# profile still runs out to the 4,000,000 the contract states.
END = {1: "2026-03-31", 2: "2026-04-30", 3: "2026-05-31", 4: "2026-06-30",
       5: "2026-07-31", 6: "2026-08-31", 7: "2026-09-30", 8: "2026-10-31"}
LAST = 8

#: period -> (cumulative planned value, cumulative planned spend): the two curves the baseline
#: prints. Periods 0, 1 and 2 are unchanged from Run 69.
CURVE = {0: (0, 0), 1: (1_020_000, 1_000_000), 2: (1_500_000, 1_460_000),
         3: (2_000_000, 1_950_000), 4: (2_500_000, 2_440_000),
         5: (3_000_000, 2_930_000), 6: (3_400_000, 3_330_000),
         7: (3_750_000, 3_680_000), 8: (4_000_000, 3_930_000)}

#: period -> (earned value, actual cost), as the pay application states them. Periods 1 and 2 are
#: unchanged from Run 69.
EVAC = {1: (1_000_000, 1_050_000), 2: (2_000_000, 2_100_000),
        3: (2_150_000, 2_300_000), 4: (2_400_000, 2_620_000),
        5: (2_700_000, 2_980_000), 6: (2_950_000, 3_300_000),
        7: (3_150_000, 3_570_000), 8: (3_300_000, 3_800_000)}

PERIODS = {}
for _p in range(1, LAST + 1):
    _ev, _ac = EVAC[_p]
    _pv = CURVE[_p][0]
    PERIODS[_p] = {"ev": _ev, "ac": _ac, "pv": _pv,
                   "planned_pct": round(_pv / BAC * 100, 2),
                   "actual_pct": round(_ev / BAC * 100, 2)}
P1, P2 = PERIODS[1], PERIODS[2]
PL = PERIODS[LAST]

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
    {"Period": _p,
     "Period ending": (END[_p] if _p else "2025-12-31"),
     "Planned value this period (USD)": CURVE[_p][0] - CURVE[_p - 1][0] if _p else 0,
     "Cumulative planned value (USD)": CURVE[_p][0],
     "Cumulative planned spend (USD)": CURVE[_p][1]}
    for _p in range(0, LAST + 1)
]
BASELINE_PROVENANCE = {
    "baseline_version": "PMB Rev 2, reissued 2026-01-15",
    "baseline_approval_source": "Approved by the Project Sponsor and the Contracting Officer, "
                                "Baseline Change Board record BCB-2026-004",
}

DOCS = [
    # RUN 69. WHAT THE CONTRACT STATES ABOUT ITS OWN REGULATORY REGIME. `evms_applicability`
    # reads no performance figure at all and answers from the acquisition, the agency, the
    # agency procedure and the clause, or not at all.
    ("contract", 1, "contract_value",
     {"original_contract_sum": BAC, "project_start_date": "2026-01-01",
      "project_end_date": "2027-06-30",
      "federal_acquisition": True, "contracting_agency": "General Services Administration",
      "acquisition_designation": "development", "major_acquisition": True,
      "agency_procedure_requires_evms": True, "evms_clause_id": "FAR 52.234-4",
      "award_date": "2026-01-01", "acquisition_id": "GS-P-26-0114"}),
    # ONE PAY APPLICATION AND ONE TIME-PHASED SCHEDULE PER PERIOD, which is what a monthly
    # reporting cycle produces. This is the only change Run 70 makes to the evidence: more
    # periods of the same two document types, each stating its own period's figures.
    *[(f"tps{_p}", _p, "time_phased_schedule",
       {"planned_value_to_date": PERIODS[_p]["pv"],
        "planned_percent_complete": PERIODS[_p]["planned_pct"],
        "data_date": END[_p], "document_date": END[_p],
        "baseline_curve_json": BASELINE_ROWS, **BASELINE_PROVENANCE})
      for _p in range(1, LAST + 1)],
    *[(f"pay{_p}", _p, "pay_application",
       {"amount_paid_to_date": PERIODS[_p]["ac"], "completed_to_date": PERIODS[_p]["ev"],
        "percent_complete_verified": PERIODS[_p]["actual_pct"],
        "application_date": END[_p], "document_date": END[_p],
        # THE CONTINGENCY PAIR RIDES THE PAY APPLICATION, which is the document type that
        # states it, and it is stated on the status period's application.
        **({"original_contingency": 200_000, "remaining_contingency": 90_000}
           if _p == LAST else {})})
      for _p in range(1, LAST + 1)],
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
    ("schedL", LAST, "schedule_update",
     {"data_date": END[LAST], "document_date": END[LAST],
      "planned_percent_complete": PL["planned_pct"],
      "milestones_json": [
          {"Milestone": "MS-01", "Description": "Foundations complete",
           "Baseline finish": "2026-06-30", "Current finish": "2026-07-19"},
          {"Milestone": "MS-02", "Description": "Structure topped out",
           "Baseline finish": "2026-09-30", "Current finish": "2026-11-06"},
          {"Milestone": "MS-03", "Description": "Building watertight",
           "Baseline finish": "2026-12-15", "Current finish": "2026-12-09"},
      ]}),
    ("riskL", LAST, "risk_register", {"document_date": END[LAST], "document_risk_score": 0.4}),
    ("rfiL", LAST, "rfi_log",
     {"rfi_total": 120, "rfi_open": 30, "rfi_answered": 90, "rfi_overdue": 8,
      "avg_response_days": 11, "rfi_period_days": 30, "oldest_open_days": 44,
      "log_date": END[LAST], "document_date": END[LAST]}),
    ("subL", LAST, "submittal_register",
     {"submittals_total": 200, "submittals_rejected": 24, "document_date": END[LAST]}),
    ("ncrL", LAST, "ncr_log",
     {"ncr_issued": 14, "ncr_closed": 9, "ncr_open": 5, "report_period": END[LAST],
      "document_date": END[LAST]}),
    ("inspL", LAST, "inspection_report",
     {"items_inspected": 300, "items_passed": 280, "items_failed": 20,
      "deficiency_count": 20, "critical_deficiency_count": 2, "document_date": END[LAST]}),
    ("qaL", LAST, "quality_audit_report",
     {"total_findings": 18, "critical_findings": 3, "deficiency_count": 18,
      "audit_score": 82, "audit_date": END[LAST], "document_date": END[LAST]}),
    ("safeL", LAST, "safety_report",
     {"osha_recordable_incidents": 2, "total_manhours": 180_000, "incident_rate": 2.2,
      "report_period": END[LAST], "document_date": END[LAST]}),
    ("envL", LAST, "environmental_report",
     {"permit_conditions_total": 40, "violations": 2, "compliance_rate": 0.95,
      "report_date": END[LAST], "document_date": END[LAST]}),
    # ---------------------------------------------------------------- RUN 69'S FOUR DOCUMENTS
    #
    # THE RESOURCE REPORT, WHICH IS A HISTOGRAM AND A PRODUCTION RECORD. A2.9 refused four
    # project-total scalars in its own words ("a project-total planned-versus-actual labour ratio
    # is not this index"); what a resource-loaded report PRINTS is the table below, one row per
    # period per trade with the hours demanded and the hours available. A3.3 refused because
    # hours over hours is not productivity: the quantities and the unit below are the output
    # basis it names, printed on the same report beside the hours.
    ("resL", LAST, "resource_report",
     {"planned_labor_hours": 120_000, "actual_labor_hours": 131_000,
      "document_date": END[LAST],
      "resource_plan_version": "Resource Plan Rev 3, issued 2026-04-05",
      "resource_profile_json": [
          {"Period": "2026-03", "Trade": "Electrical",
           "Demand hours": 4000, "Available hours": 3500},
          {"Period": "2026-03", "Trade": "Mechanical",
           "Demand hours": 2000, "Available hours": 2500},
          {"Period": "2026-04", "Trade": "Electrical",
           "Demand hours": 5200, "Available hours": 4000},
          {"Period": "2026-04", "Trade": "Mechanical",
           "Demand hours": 2400, "Available hours": 3000},
      ],
      "quantity_installed_to_date": 8200, "quantity_planned_to_date": 9000,
      "quantity_unit": "linear metres of conduit",
      "quantity_source": "field quantity survey signed off by the superintendent, 2026-04-30"}),
    # THE COST REPORT'S OVERHEAD SCHEDULE. The two indirect figures were already extracted and
    # A3.5 still refused, because "indirect actual over indirect plan with no allocation base is
    # not overhead absorption". The base, and the planned and actual amount of it, are the three
    # facts the schedule prints beside them.
    ("costL", LAST, "cost_report",
     {"indirect_cost_plan": 480_000, "indirect_cost_actual": 561_000,
      "report_date": END[LAST], "document_date": END[LAST],
      "overhead_allocation_base": "direct labour hours",
      "planned_allocation_base_quantity": 120_000,
      "actual_allocation_base_quantity": 131_000,
      "overhead_driver_source": "the overhead schedule printed in this cost report"}),
    # THE CONTRACT MODIFICATION REGISTER. `change_order_count` is a COUNT and B3.5 states there
    # is no count in its result. The register prints who executed each modification and under
    # what authority, which is the question. M-003 deliberately prints a SIGNATURE and NO
    # AUTHORITY, because "signature existence is never authority" is the module's own rule and
    # the fixture must be able to make it fail.
    ("coL", LAST, "change_order",
     {"change_order_date": END[LAST], "document_date": END[LAST],
      "modifications_json": [
          {"Modification No": "M-001", "Date issued": "2026-02-10",
           "Federal": "Yes", "Modification type": "Bilateral",
           "Executed by": "J. Alvarez, Contracting Officer",
           "Authority reference": "Warrant CO-4471, unlimited",
           "Signatories": "J. Alvarez; Northgate Constructors",
           "SF30 applicable": "Yes", "Written instrument": "SF 30 dated 2026-02-10"},
          {"Modification No": "M-002", "Date issued": "2026-03-22",
           "Federal": "Yes", "Modification type": "Unilateral",
           "Executed by": "R. Chen, Contracting Officer",
           "Authority reference": "Warrant CO-2210",
           "Signatories": "R. Chen",
           "SF30 applicable": "Yes", "Written instrument": "SF 30 dated 2026-03-22"},
          {"Modification No": "M-003", "Date issued": "2026-04-18",
           "Federal": "Yes", "Modification type": "Bilateral",
           "Executed by": "T. Okafor, Project Engineer",
           "Authority reference": "",
           "Signatories": "T. Okafor; Northgate Constructors",
           "SF30 applicable": "Yes", "Written instrument": ""},
      ]}),
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
    if tag == "riskL":
        return REGISTER_DOCX
    return f"%PDF-1.4 RUN69 {tag}\n".encode()

set_extractor_override(StubExtractor({
    hashlib.sha256(doc_bytes(t)).hexdigest(): (ty, ex) for t, _p, ty, ex in DOCS}))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="R70-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == D)) is None:
        s.add(Project(legacy_id=D, doc={"id": D, "name": "Run 69 measurement fixture",
                                        "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": f"R70-PM-{int(time.time())}", "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": D,
      "participant_id": created["participant_id"], "project_role": "PM"})
for tag, per, _ty, _ex in DOCS:
    r = post({"action": "projectupload", "session_token": PM, "id": D, "period": per,
              "period_end": END[per],
              "documents": [{"filename": f"{tag}.docx" if tag == "riskL" else f"{tag}.pdf",
                             "mimeType": DOCX_MIME if tag == "riskL" else "application/pdf",
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
FIX["ABSTAINED_REASONS"] = {a.get("module_id"): a.get("reason") for a in _ab}
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

if os.environ.get("RUN70_FIXTURE_ONLY"):
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
  const client = {}, stored = {};
  (window.projectLevelCategories ? projectLevelCategories() : []).forEach(c => {
    let s = null;
    try { s = window.getCategoryStatus ? getCategoryStatus(c.id, p) : null; } catch(e){}
    client[c.id] = s || null;
    const k = c.key || c.id;  // the SERVER's key ('A1'), not the page id ('a1')
    stored[k] = (cs[k] && cs[k].status) || null;
    client[k] = client[c.id];
    if (k !== c.id) delete client[c.id];
  });
  let clientProject = null;
  try { const f = window.getProjectFusion ? getProjectFusion(p) : null;
        clientProject = f ? (f.status || null) : null; } catch(e) {}
  return {
    row_present: !!row,
    row_period: row ? row.period : null,
    row_module_results: row && row.module_results ? row.module_results.length : null,
    row_cats_with_status: Object.keys(cs).filter(k => cs[k] && cs[k].status).length,
    STORED_CATEGORY_STATUS: stored,
    CLIENT_CATEGORY_STATUS: client,
    CATEGORIES_DISAGREEING: Object.keys(stored).filter(k => stored[k] !== client[k]),
    stored_project_status: row ? (row.project_status || null) : null,
    client_project_status: clientProject,
    LIT_ON_PAGE: Object.keys(client).filter(k => client[k]).length,
    LIT_FROM_STORED: Object.keys(stored).filter(k => stored[k]).length,
  };
}"""

# EVERY FIGURE THE DETAIL PAGE PRINTS, harvested from the rendered DOM rather than from a list
# of selectors, so a figure nobody thought to enumerate still appears.
FIGURES_JS = r"""() => {
  const root = document.getElementById('detail-root') || document.body;
  const out = [];
  const walk = (n) => {
    if (n.nodeType === 3) {
      const t = (n.textContent || '').trim();
      if (/[0-9]/.test(t) && t.length < 200) {
        const par = n.parentElement;
        out.push({text: t, cls: par ? (par.className || '') : '',
                  id: par ? (par.id || '') : '',
                  tag: par ? par.tagName : ''});
      }
      return;
    }
    if (n.nodeType !== 1) return;
    if (n.tagName === 'SCRIPT' || n.tagName === 'STYLE') return;
    const st = window.getComputedStyle ? getComputedStyle(n) : null;
    if (st && (st.display === 'none' || st.visibility === 'hidden')) return;
    for (const c of n.childNodes) walk(c);
  };
  walk(root);
  return out;
}"""

# EVERY NON-WEBGL SECTION OPENED, one call, so the figure trace covers what a reader sees after
# opening the page's panels. The WebGL panels are opened separately and one at a time above.
EXPAND_JS = r"""() => {
  const webgl = ['d-projnet', 'd-globe', 'd-neural', 'd-ensemble'];
  const opened = [];
  document.querySelectorAll('[id^="body-"]').forEach((b) => {
    const id = b.id.replace(/^body-/, '');
    if (webgl.indexOf(id) !== -1) return;
    if (b.style.display === 'none' && window.toggleSection) { toggleSection(id); opened.push(id); }
  });
  return opened;
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

    # ------------------------------------------------------------------ SECTION 8, TEST ONE
    # RENDER THE SAME PROJECT TWICE IN ONE PAGE LOAD AND COMPARE. Run 60 established that the
    # first and second render disagreed and the SECOND was correct, which means the first was
    # what a person actually saw. Both renders are harvested from the DOM, not from a model.
    CAP["expanded_1"] = page.evaluate(EXPAND_JS)
    page.wait_for_timeout(6000)
    CAP["figures_render_1"] = page.evaluate(FIGURES_JS)
    page.evaluate("(id) => window.LinDetail && LinDetail.render(id)", D)
    page.wait_for_timeout(12000)
    CAP["expanded_2"] = page.evaluate(EXPAND_JS)
    page.wait_for_timeout(6000)
    CAP["figures_render_2"] = page.evaluate(FIGURES_JS)
    CAP["row_state_render_2"] = page.evaluate(ROW_JS, D)
    a = [f["text"] for f in CAP["figures_render_1"]]
    b = [f["text"] for f in CAP["figures_render_2"]]
    CAP["RENDERS_AGREE"] = a == b
    CAP["RENDER_DIFF"] = [[x, y] for x, y in zip(a, b) if x != y][:60]
    CAP["RENDER_LENGTHS"] = [len(a), len(b)]
    CAP["page_errors"] = errors
    browser.close()

server.should_exit = True
OUT.write_text(json.dumps(CAP, indent=2), encoding="utf-8")
print("=" * 96)
print("BROWSER, ON THE RENDERED DETAIL PAGE:")
for k, v in CAP["after_panels_row_state"].items():
    print(f"  {k:32} {v}")
print(f"  RENDERS_AGREE: {CAP['RENDERS_AGREE']}  lengths {CAP['RENDER_LENGTHS']}")
print(f"  RENDER_DIFF (first 20): {CAP['RENDER_DIFF'][:20]}")
print(f"  projnet_svg_text: {CAP['projnet_svg_text']}")
print(f"page errors: {errors}")
print(f"capture written to {OUT}")
