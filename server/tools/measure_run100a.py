"""RUN 99, fixture E: a FULL document set, through the real routes, to establish whether the
five required categories can be assessed when the documents actually exist."""
import base64, hashlib, json, logging, pathlib, sys, time
HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools"); sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)
from fastapi.testclient import TestClient
from sqlalchemy import select
import app.main as main
from app.documents import set_extractor_override
from app.extraction_client import StubExtractor
from app.models import Project
from app.research_identity import hash_access_token
from app.research_models import Participant, ComputedResult
client = TestClient(main.app, raise_server_exceptions=False); S = main.SessionFactory
def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type":"text/plain"})
    assert r.status_code == 200, r.text[:300]
    return r.json()
def b64(x): return base64.b64encode(x).decode()
STAMP=str(int(time.time())); ADMIN="r100a-"+STAMP; BAC=4_000_000; END="2026-03-31"; PID="PRJ-R100A-"+STAMP
# A healthy project: on budget, on schedule, clean documents.
DOCS = [
 ("contract","contract_value",{"original_contract_sum":BAC,"project_start_date":"2026-01-01","project_end_date":"2027-06-30"}),
 ("tps","time_phased_schedule",{"planned_value_to_date":1_000_000,"planned_percent_complete":25.0,
    "data_date":END,"document_date":END,"total_float":30,"consumed_float":2}),
 ("pay","pay_application",{"amount_paid_to_date":1_000_000,"completed_to_date":1_000_000,
    "percent_complete_verified":25.0,"application_date":END,"document_date":END,
    "original_contingency":400_000,"remaining_contingency":380_000}),
 ("sched","schedule_update",{"activities_planned":200,"activities_constrained":8,"lookahead_weeks":6,
    "data_date":END,"planned_percent_complete":25.0,"planned_value_to_date":1_000_000,
    "total_float":30,"consumed_float":2}),
 ("look","lookahead_schedule",{"activities_planned":200,"activities_constrained":8,"lookahead_weeks":6,
    "constraint_rate":0.04,"lookahead_status_date":END,"lookahead_horizon":6}),
 ("res","resource_report",{"planned_labor_hours":50_000,"actual_labor_hours":49_500,
    "quantity_planned_to_date":1000,"quantity_installed_to_date":995,"quantity_unit":"m3",
    "quantity_source":"survey","resource_plan_version":"v1"}),
 ("cost","cost_report",{"indirect_cost_plan":200_000,"indirect_cost_actual":198_000,
    "material_cost_baseline":800_000,"material_cost_current":805_000,
    "original_contingency":400_000,"remaining_contingency":380_000,
    "overhead_allocation_base":"labour hours","planned_allocation_base_quantity":50_000,
    "actual_allocation_base_quantity":49_500,"overhead_driver_source":"cost ledger","report_date":END}),
 ("rfi","rfi_log",{"rfi_total":40,"rfi_answered":38,"rfi_open":2,"rfi_overdue":0,
    "avg_response_days":6,"oldest_open_days":9,"rfi_period_days":30,"log_date":END}),
 ("rfa","rfa_log",{"rfa_total":30,"rfa_approved":27,"rfa_rejected":1,"rfa_resubmit":2,
    "rfa_open":0,"avg_review_days":8,"log_date":END}),
 ("sub","submittal_register",{"submittals_total":30,"submittals_rejected":1,
    "document_date":END,"document_risk_score":0.15}),
 ("ncr","ncr_log",{"ncr_issued":3,"ncr_closed":3,"ncr_open":0,"ncr_overdue":0,"report_period":"2026-03"}),
 ("safety","safety_report",{"osha_recordable_incidents":0,"total_manhours":50_000,
    "incident_rate":0.0,"report_period":"2026-03"}),
 ("qa","quality_audit_report",{"audit_score":96,"total_findings":4,"critical_findings":0,
    "deficiency_count":4,"audit_date":END}),
 ("env","environmental_report",{"compliance_rate":1.0,"violations":0,"report_date":END,
    "permit_conditions_total":12,"operator_status":"in good standing"}),
 ("subr","subcontractor_report",{"compliance_score":95,"on_time_deliveries":48,
    "scheduled_deliveries":50,"report_period":"2026-03"}),
 ("proc","procurement_log",{"long_lead_items_total":20,"at_risk":1,"delayed":0,
    "on_schedule":19,"report_date":END}),
 ("insp","inspection_report",{"items_inspected":200,"items_passed":198,"items_failed":2,
    "critical_deficiency_count":0,"deficiency_count":2,"document_date":END,"document_risk_score":0.10}),
 ("weather","field_report",{"weather_days_lost":1,"float_remaining":29,"document_date":END,
    "document_risk_score":0.10,"quality_deficiencies_noted":0}),
 ("co","change_order",{"change_order_count":2,"baseline_contract_sum":BAC,
    "revised_contract_sum":BAC,"change_order_date":END}),
 ("oac","oac_minutes",{"document_date":END,"document_risk_score":0.10,
    "outstanding_action_items":2,"safety_incidents_discussed":0,"safety_actions_open":0,
    "quality_issues_discussed":0,"environmental_issues_discussed":0,"weather_days_discussed":1,
    "subcontractor_issues_discussed":0,"subcontractor_disputes":0}),
 ("past","past_performance_report",{"overall_rating":"Very Good","cost_rating":"Very Good",
    "schedule_rating":"Very Good","quality_rating":"Very Good","source":"CPARS"}),
]
def raw(t): return f"%PDF-1.4 R100A {STAMP} {t}\n".encode()
set_extractor_override(StubExtractor({hashlib.sha256(raw(t)).hexdigest():(ty,ex) for t,ty,ex in DOCS}))
with S() as s:
    r=s.scalar(select(Participant).where(Participant.role=="ResearchAdmin"))
    if r is None: s.add(Participant(pseudonymous_code="R100A-A-"+STAMP,role="ResearchAdmin",access_token_hash=hash_access_token(ADMIN)))
    else: r.access_token_hash=hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id==PID)) is None:
        s.add(Project(legacy_id=PID,doc={"id":PID,"name":"Run 100 fixture A","sector":"construction","signals":{},"events":[]}))
    s.commit()
admin=post({"action":"researchlogin","access_token":ADMIN})["session_token"]
c=post({"action":"adminparticipantcreate","session_token":admin,"pseudonymous_code":"R100A-PM-"+STAMP,"role":"Participant","account_type":"operational"})
PM=post({"action":"researchlogin","access_token":c["access_token"]})["session_token"]
post({"action":"adminmemberadd","session_token":admin,"id":PID,"participant_id":c["participant_id"],"project_role":"PM"})
ok=0
for t,ty,ex in DOCS:
    r=post({"action":"projectupload","session_token":PM,"id":PID,"period":1,"period_end":END,
            "documents":[{"filename":t+".pdf","mimeType":"application/pdf","dataBase64":b64(raw(t))}]})
    if r.get("ok"): ok+=1
    else: print("  upload FAILED", t, str(r)[:150])
print(f"uploaded {ok}/{len(DOCS)} documents through the real route")
r=post({"action":"projectcomputeall","session_token":PM,"id":PID})
print("computeall:", json.dumps(r)[:200])
ap=post({"action":"projectcategoryapply","session_token":PM,"id":PID,"period":1})
print("categoryapply:", ap.get("ok"), "readings", len(ap.get("readings") or []), "servedBy", ap.get("servedBy"))
with S() as s:
    p=s.scalar(select(Project).where(Project.legacy_id==PID))
    row=s.scalar(select(ComputedResult).where(ComputedResult.project_id==p.id, ComputedResult.superseded_by.is_(None)))
    print()
    print("PYTHON MODULE LAYER (computed_results row):")
    print("  stored project_status =", repr(row.project_status))
    print("  modules that computed :", sorted(m.get("module_id") for m in (row.module_results or [])))
    print("  category_statuses     :", json.dumps({k:(v or {}).get("status") for k,v in (row.category_statuses or {}).items()}))
    print("  abstained             :", len(row.abstained or []))
res=post({"action":"projectresults","session_token":PM,"id":PID,"period":1})
b=(res.get("result") or {}).get("project_status_basis") or {}
print()
print("SPECIFICATION LAYER (what the portfolio and detail actually serve):")
print("  project_status =", repr((res.get('result') or {}).get('project_status')))
print("  required_assessed", b.get("required_assessed"), " required_missing", b.get("required_missing"))
lst=client.get(f"/exec?action=list&session_token={PM}").json()
for pr in (lst.get("projects") or []):
    if pr["id"]==PID:
        print("  PORTFOLIO ROUTE serves status =", repr(pr.get("status")))

with S() as s:
    p2=s.scalar(select(Project).where(Project.legacy_id==PID))
    row=s.scalar(select(ComputedResult).where(ComputedResult.project_id==p2.id, ComputedResult.superseded_by.is_(None)))
    si=row.signal_inputs or {}
    eq=si.get("evidenceQualification")
    print()
    print("=== evidenceQualification RECORD ===")
    print(json.dumps(eq, indent=2, default=str)[:4000])
    print()
    print("=== A6 MODULE ABSTENTIONS ===")
    for m in (row.abstained or []):
        mid=str(m.get("module_id") or "")
        if mid.startswith("A6"):
            print(" ", mid, "->", json.dumps(m, default=str)[:600])
            print()

with S() as s:
    p3=s.scalar(select(Project).where(Project.legacy_id==PID))
    row=s.scalar(select(ComputedResult).where(ComputedResult.project_id==p3.id, ComputedResult.superseded_by.is_(None)))
    print()
    print("=== BANDS OF COMPUTING MODULES ===")
    for m in (row.module_results or []):
        print("  %-6s status_color=%-8r band_asserted=%-6r calibration_pending=%-6r" % (
            m.get("module_id"), m.get("status_color"), m.get("band_asserted"), m.get("calibration_pending")))
        if m.get("calibration_note"): print("      note:", str(m.get("calibration_note"))[:220])
    print()
    print("=== CATEGORY STATUS OBJECTS ===")
    print(json.dumps(row.category_statuses, indent=2, default=str)[:2500])
