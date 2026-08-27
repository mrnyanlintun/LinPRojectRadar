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

LABEL = sys.argv[1] if len(sys.argv) > 1 else "run70-partb"
OUT = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("run70_partb.json")
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

D = "PRJ-R70B"
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

# ------------------------------------------------------------------------------- RUN 70, PART B
# A SECOND PROJECT ON WHICH NO SCHEDULE MODULE COMPUTED. Check 3 refuses a claim about the
# schedule when nothing produced a schedule figure, and that cannot be shown on a project whose
# schedule modules DO compute. This project holds its contract and its pay applications and
# NOTHING ELSE: earned value and actual cost are stated, so a cost index forms; no planned value
# and no schedule update are stated, so no schedule index and no Category A2 module has anything
# to read. Nothing is faked -- these are the same documents, and the project simply has fewer.
DS = D + "-COSTONLY"
COST_ONLY = [
    ("c-contract", 1, "contract_value",
     {"original_contract_sum": BAC, "project_start_date": "2026-01-01",
      "project_end_date": "2027-06-30"}),
] + [(f"c-pay{_p}", _p, "pay_application",
      {"amount_paid_to_date": PERIODS[_p]["ac"], "completed_to_date": PERIODS[_p]["ev"],
       "percent_complete_verified": PERIODS[_p]["actual_pct"],
       "application_date": END[_p], "document_date": END[_p]})
     for _p in range(1, LAST + 1)]


def cost_only_bytes(tag):
    return f"%PDF-1.4 RUN70 {tag}\n".encode()


set_extractor_override(StubExtractor({
    **{hashlib.sha256(doc_bytes(t)).hexdigest(): (ty, ex) for t, _p, ty, ex in DOCS},
    **{hashlib.sha256(cost_only_bytes(t)).hexdigest(): (ty, ex)
       for t, _p, ty, ex in COST_ONLY}}))

with Session() as s:
    if s.scalar(select(Project).where(Project.legacy_id == DS)) is None:
        s.add(Project(legacy_id=DS, doc={"id": DS, "name": "Run 70 cost-only fixture",
                                         "signals": {}, "events": []}))
        s.commit()
post({"action": "adminmemberadd", "session_token": admin, "id": DS,
      "participant_id": created["participant_id"], "project_role": "PM"})
for tag, per, _ty, _ex in COST_ONLY:
    r = post({"action": "projectupload", "session_token": PM, "id": DS, "period": per,
              "period_end": END[per],
              "documents": [{"filename": f"{tag}.pdf", "mimeType": "application/pdf",
                             "dataBase64": b64(cost_only_bytes(tag))}]})
    assert r.get("ok") is True, str(r)[:300]
assert post({"action": "projectcomputeall", "session_token": PM, "id": DS}).get("ok") is True
_sres = post({"action": "projectresults", "session_token": PM, "id": DS,
              "period": post({"action": "projectperiods", "session_token": PM,
                              "id": DS}).get("latest_computed_period")})
_srow = _sres.get("result") or {}
SPARSE = {
    "period": _srow.get("period"),
    "module_ids": sorted(m.get("module_id") for m in (_srow.get("module_results") or [])),
    "cpi": (_srow.get("signal_inputs") or {}).get("cpi"),
    "spi": (_srow.get("signal_inputs") or {}).get("spi"),
    "project_status": _srow.get("project_status"),
}
SPARSE["NO_SCHEDULE_MODULE"] = not any(m.startswith("A2.") for m in SPARSE["module_ids"])
print("COST-ONLY PROJECT:", SPARSE)

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

if os.environ.get("RUN70B_FIXTURE_ONLY"):
    OUT.write_text(json.dumps({"label": LABEL, "fixture": FIX}, indent=2), encoding="utf-8")
    print(f"fixture-only capture written to {OUT}")
    raise SystemExit(0)


# =============================================================================================
# RUN 70, PART B. THE THREE CHECKS, PROVED BY INJECTION.
#
# Each injection is a RECOMMENDATION -- the artefact the checks judge -- placed on the project in
# the browser and rendered through the same `setBriefState` path the chat endpoint and the
# scripted fallback both use. A rejected recommendation renders `.eb-rejected`; an accepted one
# renders `.eb-structured` without it.
#
# EACH CHECK IS THEN PINNED TO ITS EXACT SITE. The check's own block is deleted from
# `assets/js/detail.js` on disk, the bytes are re-read to confirm the deletion landed, the page
# is reloaded and the SAME injection is confirmed to render, and the file is restored from a
# COMMITTED reference inside a `finally`. A check that matched a name file-wide, or that some
# other check was really doing the work of, cannot survive this.
# =============================================================================================
import subprocess, shutil  # noqa: E402

DETAIL = ROOT / "assets" / "js" / "detail.js"
# THE SNAPSHOT IS TAKEN FROM THE COMMITTED REFERENCE, NEVER FROM DISK. A previous attempt at
# this campaign was killed between its deletion and its restore, leaving the mutated file on
# disk; a run that snapshotted disk would then have "restored" the mutation and hidden it. HEAD
# is the only thing that cannot be damaged by a half-finished campaign.
SNAPSHOT = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:assets/js/detail.js"],
                          capture_output=True, text=True, check=True).stdout
assert DETAIL.read_text(encoding="utf-8") == SNAPSHOT, (
    "the served detail.js differs from HEAD; commit before running the deletion campaign")

# module-level so the injections and the deletion campaign name the same three sites
CHECK_SITES = {
    "check1": ('      if (!briefHasAny(s.text, BRIEF_CONDITION_WORDS)) return;\n'
               '      const figs = briefFiguresIn(s.text);\n'
               '      if (!figs.length) {'),
    "check2": ('      const allGreen = statedBands.length > 0 '
               '&& statedBands.every((k) => k === "green");'),
    "check3": ('      if (briefHasAny(s.text, BRIEF_SCHEDULE_WORDS) && !ev.scheduleComputed) {'),
}

INJECTIONS = {
    # 1. ASSERTS A CONDITION AND NAMES NO FIGURE. This is the defect verbatim: the sentence the
    #    Executive Brief printed beside three green drivers at 3dd890b.
    "check1": "### Recommendation\n"
              "AMBER · review the cost and schedule trend with the controls lead this cycle.\n"
              "The evidence suggests meaningful risk that may warrant a closer look this cycle.\n"
              "### Signal Pattern\n● AMBER (1 category): A1.\n"
              "### Key Drivers\n- CPI: 0.868\n"
              "### Required Actions\n- Consider a review",
    # 2. THE POSTURE CONTRADICTS ITS DRIVERS. Every driver stated is green; the posture is
    #    adverse; and nothing is named that made it adverse. Every sentence carries a figure, so
    #    check 1 cannot be what rejects this one.
    "check2": "### Recommendation\n"
              "RED · escalate this cycle.\n"
              "The cost performance index is 0.868 and the schedule performance index is 0.825.\n"
              "### Signal Pattern\n● GREEN (3 categories): A1, A4, B1.\n"
              "### Key Drivers\n- CPI: 0.868 (Green)\n- SPI: 0.825 (Green)\n"
              "### Required Actions\n- Consider a review",
    # 3. A SCHEDULE CLAIM WITH NO SCHEDULE MODULE COMPUTED. The figure it names is a stored one,
    #    so check 1 passes it; what fails is that no A2 module produced a value this period.
    "check3": "### Recommendation\n"
              "RED · escalate this cycle.\n"
              "The schedule is behind, and the cost performance index is 0.868.\n"
              "### Signal Pattern\n● RED (1 category): A1.\n"
              "### Key Drivers\n- CPI: 0.868 (Red)\n"
              "### Required Actions\n- Consider a review",
}

# THE REAL RENDER PATH, AND NOTHING TEST-ONLY IS EXPORTED TO REACH IT. The brief is placed on
# the project for the period the stored row holds, and `LinDetail.render` is called: `briefPanel`
# reads the cached brief for that period and hands it to `briefBodyHtml`, which is where the gate
# sits. `refreshBrief` finds the same cached brief for the same period and returns without
# calling the chat endpoint, so the text under test is the text that renders.
SET_JS = r"""(args) => {
  const targets = [];
  try { const c = window.LinStore && LinStore.getCached(args.id); if (c) targets.push(c); } catch (e) {}
  (window.LIN_PROJECTS || []).forEach(x => { if (x.id === args.id && targets.indexOf(x) < 0) targets.push(x); });
  const p = targets[0] || null;
  if (!p) return {error: "no project"};
  const row = (window.LinResults && LinResults.rowFor(p)) || null;
  const period = row ? row.period : null;
  targets.forEach(t => {
    t.executiveBriefRejection = null;
    t.executiveBrief = {text: args.text, generated_at: new Date().toISOString(),
                        period: null, source: "injected"};
  });
  return {period: period, chars: args.text.length, targets: targets.length};
}"""

# THE REAL ONE. Nothing is supplied by the caller: the brief is cleared, and the page's own
# fallback builds it from the stored row when the chat endpoint fails, which it does here.
CLEAR_JS = r"""(id) => {
  const targets = [];
  try { const c = window.LinStore && LinStore.getCached(id); if (c) targets.push(c); } catch (e) {}
  (window.LIN_PROJECTS || []).forEach(x => { if (x.id === id && targets.indexOf(x) < 0) targets.push(x); });
  targets.forEach(t => { t.executiveBrief = null; t.executiveBriefRejection = null; });
  return {cleared: targets.length};
}"""

READ_JS = r"""(id) => {
  let p = null;
  try { p = (window.LinStore && LinStore.getCached(id)) || null; } catch (e) {}
  if (!p) p = (window.LIN_PROJECTS || []).filter(x => x.id === id)[0] || null;
  const root = document.getElementById('detail-root') || document.body;
  const panel = root.querySelector('.eb-panel');
  const body = panel ? panel.querySelector('.eb-body') : null;
  return {
    rejected: !!(body && body.classList.contains('eb-rejected')),
    classes: body ? body.className : null,
    failures: (p && p.executiveBriefRejection && p.executiveBriefRejection.failures) || null,
    rendered_text: body ? body.innerText : null,
    brief_text: (p && p.executiveBrief && p.executiveBrief.text) || null,
    brief_source: (p && p.executiveBrief && p.executiveBrief.source) || null,
  };
}"""


# THE BRIEF ONLY EXISTS WHEN ITS SECTION IS OPEN. `render()` registers `d-brief` as a lazy
# init and `refreshBrief` runs on FIRST EXPAND, never at page load; a driver that read the panel
# without opening it read the loading shimmer and would have called every injection accepted.
OPEN_BRIEF_JS = r"""() => {
  const b = document.getElementById('body-d-brief');
  const wasOpen = !!(b && b.style.display !== 'none');
  if (b && b.style.display === 'none' && window.toggleSection) toggleSection('d-brief');
  return {found: !!b, wasOpen: wasOpen};
}"""


def show(page, text, pid=None):
    """Put `text` on the project (or clear it), drive the page's own render, open the brief."""
    pid = pid or D
    # THE BRIEF IS PLACED BEFORE THE RENDER, AND CARRIES NO PERIOD. `render()` clears `lazyDone`
    # and runs the lazy init of any section the session restored as open, so the brief section
    # re-runs `refreshBrief` on every render; `refreshBrief` then finds this cached brief and
    # renders it without calling the chat endpoint at all. The period is left null deliberately:
    # `briefForPeriod` discards a cached brief whose period disagrees with `briefCurrentPeriod`,
    # which is derived from the snapshot and is not the stored row's period.
    if text is None:
        page.evaluate(CLEAR_JS, pid)
    else:
        page.evaluate(SET_JS, {"id": pid, "text": text})
    page.evaluate("(id) => window.LinDetail && LinDetail.render(id)", pid)
    page.wait_for_timeout(4000)
    opened = page.evaluate(OPEN_BRIEF_JS)
    # The real one has to wait out the chat endpoint's own 15s timeout before the page falls
    # back to the brief it builds itself; an injected one is cached for the period and renders
    # without any call at all.
    page.wait_for_timeout(30000 if text is None else 9000)
    out = page.evaluate(READ_JS, pid)
    out["section_opened"] = opened
    out["project"] = pid
    return out


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

CAP = {"label": LABEL, "fixture": FIX, "sparse": SPARSE,
       "injections": {}, "deletion_campaign": {}}


def open_page(pw):
    browser = pw.chromium.launch(executable_path=CHROME,
                                 args=["--use-gl=swiftshader", "--no-sandbox", "--headless=new"])
    page = browser.new_page(viewport={"width": 1680, "height": 3200})
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    for pat in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
        page.route(pat, lambda r: r.abort())
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.wait_for_timeout(9000)
    page.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('workspace')")
    page.wait_for_timeout(2500)
    page.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('portfolio')")
    page.wait_for_timeout(1500)
    page.evaluate("(id) => window.LinDetail && LinDetail.render(id)", D)
    page.wait_for_timeout(10000)
    return browser, page, errs


try:
    with sync_playwright() as pw:
        browser, page, errs = open_page(pw)
        # --------------------------------------------------- the three injections, gate intact
        for name, text in INJECTIONS.items():
            # CHECK 3 IS DRIVEN ON THE COST-ONLY PROJECT, the one with no schedule module.
            CAP["injections"][name] = show(page, text, DS if name == "check3" else D)
        # --------------------------------------------------- the real one
        CAP["real"] = show(page, None)
        CAP["page_errors_phase1"] = errs
        browser.close()

    # ------------------------------------------------ each check pinned to its exact site
    for name, site in CHECK_SITES.items():
        assert site in SNAPSHOT, f"site for {name} not found in the served file"
        # The site is made UNREACHABLE rather than textually removed, so the file stays
        # syntactically valid and the page still loads: what is proved is that this exact
        # block, and no other, is what rejects this exact injection.
        DELETIONS = {
            # CHECK 1 HAS TWO ARMS -- no figure, and a figure the row does not hold -- and they
            # are ONE check. A deletion that removed only the first arm left the second still
            # rejecting the injection, which is exactly the false pin this campaign exists to
            # catch. The whole check is disabled instead, by returning before either arm.
            "check1": ('      if (true) return;\n'
                       '      const figs = briefFiguresIn(s.text);\n'
                       '      if (!figs.length) {'),
            "check2": ('      const allGreen = false '
                       '&& statedBands.every((k) => k === "green");'),
            "check3": ('      if (false && briefHasAny(s.text, BRIEF_SCHEDULE_WORDS) '
                       '&& !ev.scheduleComputed) {'),
        }
        DETAIL.write_text(SNAPSHOT.replace(site, DELETIONS[name]), encoding="utf-8")
        landed = site not in DETAIL.read_text(encoding="utf-8")   # re-read the BYTES from disk
        with sync_playwright() as pw:
            browser, page, errs = open_page(pw)
            out = show(page, INJECTIONS[name], DS if name == "check3" else D)
            browser.close()
        CAP["deletion_campaign"][name] = {
            "deletion_landed_on_disk": landed,
            "still_rejected_with_check_deleted": out.get("rejected"),
            "failures_without_it": out.get("failures"),
            "page_errors": errs,
        }
finally:
    DETAIL.write_text(SNAPSHOT, encoding="utf-8")
    assert DETAIL.read_text(encoding="utf-8") == SNAPSHOT, "restore failed"

# ------------------------------------------------------------------ green again after restore
with sync_playwright() as pw:
    browser, page, errs = open_page(pw)
    CAP["after_restore"] = {n: show(page, t, DS if n == "check3" else D)["rejected"]
                            for n, t in INJECTIONS.items()}
    CAP["after_restore_real"] = show(page, None)
    browser.close()

server.should_exit = True
OUT.write_text(json.dumps(CAP, indent=2), encoding="utf-8")
print("=" * 96)
for n in INJECTIONS:
    i = CAP["injections"][n]
    print(f"INJECTION {n}: rejected={i.get('rejected')}")
    for f in (i.get("failures") or []):
        print(f"    {f['check']} | {f['section']} | {f['reason']}")
        print(f"      sentence: {f['sentence'][:120]}")
    d = CAP["deletion_campaign"].get(n, {})
    print(f"  SITE DELETED: landed={d.get('deletion_landed_on_disk')}  "
          f"still_rejected={d.get('still_rejected_with_check_deleted')}")
    print(f"  AFTER RESTORE: rejected={CAP['after_restore'][n]}")
print("=" * 96)
print("REAL RECOMMENDATION, rejected =", CAP["real"].get("rejected"))
print("-" * 96)
print(CAP["real"].get("brief_text"))
print("-" * 96)
print("AS RENDERED:")
print(CAP["real"].get("rendered_text"))
print("=" * 96)
print("capture written to", OUT)
