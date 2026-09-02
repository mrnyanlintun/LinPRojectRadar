"""
RUN 110. THE CENSUS, BEFORE AND AFTER, ON ONE PROJECT THROUGH THE REAL UPLOAD ROUTE.

The order's section 4 makes this a standing requirement. This driver is the fixture: it is run
ONCE BEFORE any change and ONCE AFTER, unchanged between the two, so the delta is a fact about
the platform and not about the documents.

THE FIXTURE is Run 103's twenty-one documents, verbatim, plus two additions that change no
document type and add no document:

  * `oac_minutes` gains the six weather fields Run 107 added to its extraction contract
    (`extraction_fields.py`), which Run 109 measured reaching `documents.extraction` and
    producing no observation row at all.
  * `subcontractor_report` gains the four per-firm rating fields Run 107 added, measured the
    same way.

Both were already in the extraction contract before this run. Adding them to the fixture does
not change what the platform does BEFORE; it makes visible what it discards.

NOTHING UNDER TEST IS SUPPLIED. Every document goes through the real `projectupload` route, the
real `projectcomputeall` route and the real `projectcategoryapply` route. No structure is handed
to a module and `saveprojectdata` is never called.

Run from `server/`:  python tools/drive_run110_census.py
"""
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
    assert r.status_code == 200, r.text[:400]
    return r.json()
def b64(x): return base64.b64encode(x).decode()
STAMP=str(int(time.time())); ADMIN="r110-"+STAMP; BAC=4_000_000; END="2026-03-31"; PID="PRJ-R110-"+STAMP
DOCS = [
 ("contract","contract_value",{"original_contract_sum":BAC,"project_start_date":"2026-01-01","project_end_date":"2027-06-30"}),
 ("tps","time_phased_schedule",{"planned_value_to_date":1_000_000,"planned_percent_complete":25.0,
    "data_date":END,"document_date":END,"total_float":30,"consumed_float":2}),
 ("pay","pay_application",{"amount_paid_to_date":1_000_000,"completed_to_date":1_000_000,
    "percent_complete_verified":25.0,"application_date":END,"document_date":END,
    "original_contingency":400_000,"remaining_contingency":380_000}),
 ("sched","schedule_update",{"activities_planned":200,"activities_constrained":8,"lookahead_weeks":6,
    "data_date":END,"planned_percent_complete":25.0,"planned_value_to_date":1_000_000,
    "total_float":30,"consumed_float":2,
    # RUN 103, GOAL ONE. THE FLATTENED SCHEDULE EXPORT, printed as a schedule update prints
    # one: an activity id, a duration, the predecessor logic with its relation type and lag,
    # the calendar, and the three-point durations PERT needs. NOTHING HERE IS HANDED TO A
    # MODULE: it goes through the real upload route and the real extraction contract.
    "schedule_network_json":[
      {
            "Activity ID": "A100",
            "Description": "Mobilisation",
            "Duration": 10,
            "Optimistic duration": 8,
            "Most likely duration": 10,
            "Pessimistic duration": 14,
            "Calendar": "5-day work week",
            "Predecessors": ""
      },
      {
            "Activity ID": "A110",
            "Description": "Earthworks",
            "Duration": 20,
            "Optimistic duration": 16,
            "Most likely duration": 20,
            "Pessimistic duration": 28,
            "Calendar": "5-day work week",
            "Predecessors": "A100 FS+0"
      },
      {
            "Activity ID": "A120",
            "Description": "Foundations",
            "Duration": 25,
            "Optimistic duration": 22,
            "Most likely duration": 25,
            "Pessimistic duration": 32,
            "Calendar": "5-day work week",
            "Predecessors": "A110"
      },
      {
            "Activity ID": "A130",
            "Description": "Underground utilities",
            "Duration": 15,
            "Optimistic duration": 12,
            "Most likely duration": 15,
            "Pessimistic duration": 21,
            "Calendar": "5-day work week",
            "Predecessors": "A110 SS+5"
      },
      {
            "Activity ID": "A140",
            "Description": "Structure",
            "Duration": 30,
            "Optimistic duration": 26,
            "Most likely duration": 30,
            "Pessimistic duration": 38,
            "Calendar": "5-day work week",
            "Predecessors": "A120"
      },
      {
            "Activity ID": "A150",
            "Description": "Enclosure",
            "Duration": 20,
            "Optimistic duration": 17,
            "Most likely duration": 20,
            "Pessimistic duration": 26,
            "Calendar": "5-day work week",
            "Predecessors": "A140"
      },
      {
            "Activity ID": "A160",
            "Description": "Interior fit-out",
            "Duration": 25,
            "Optimistic duration": 21,
            "Most likely duration": 25,
            "Pessimistic duration": 33,
            "Calendar": "5-day work week",
            "Predecessors": "A150"
      },
      {
            "Activity ID": "A170",
            "Description": "Sitework",
            "Duration": 12,
            "Optimistic duration": 10,
            "Most likely duration": 12,
            "Pessimistic duration": 16,
            "Calendar": "5-day work week",
            "Predecessors": "A130 FS+10"
      },
      {
            "Activity ID": "A180",
            "Description": "Commissioning",
            "Duration": 10,
            "Optimistic duration": 8,
            "Most likely duration": 10,
            "Pessimistic duration": 14,
            "Calendar": "5-day work week",
            "Predecessors": "A160,A170"
      },
      {
            "Activity ID": "M900",
            "Description": "Substantial completion",
            "Duration": 0,
            "Optimistic duration": 0,
            "Most likely duration": 0,
            "Pessimistic duration": 0,
            "Calendar": "5-day work week",
            "Predecessors": "A180",
            "Milestone class": "contractual",
            "Baseline finish": 140
      }
],
    "schedule_calendar":"5-day work week","schedule_calendars_json":["5-day work week"],
    "schedule_version":"Schedule Update Rev 4",
    "schedule_baseline_finish_day":140,"schedule_imposed_finish_day":165,
    "remaining_planned_duration_days":420,
    "remaining_duration_basis":"from the data date 2026-03-31 to the planned finish 2027-06-30, on the 5-day work week calendar"}),
 # RUN 102, GOAL TWO. THE LOOK-AHEAD ACTIVITY INVENTORY, printed as a table the way a real
 # look-ahead prints one. Eighteen of twenty are constraint-free, a ready fraction of 0.90.
 ("look","lookahead_schedule",{"activities_planned":20,"activities_constrained":2,"lookahead_weeks":6,
    "constraint_rate":0.10,"lookahead_status_date":END,"lookahead_horizon":"6 weeks",
    "lookahead_activities_json":(
       [{"Activity ID":f"LA-{i:02d}","Constraint status":"Cleared","Total float":12}
        for i in range(1,19)]
     + [{"Activity ID":"LA-19","Constraint status":"Open","Constraint type":"submittal",
         "Total float":15},
        {"Activity ID":"LA-20","Constraint status":"Open","Constraint type":"procurement",
         "Total float":9}])}),
 # RUN 102, GOAL TWO. THE TIME-PHASED RESOURCE PROFILE, two resource types kept in their own
 # units and never summed. Peak load ratio 0.95, which is Green on the owner's ladder.
 ("res","resource_report",{"planned_labor_hours":50_000,"actual_labor_hours":49_500,
    "quantity_planned_to_date":1000,"quantity_installed_to_date":995,"quantity_unit":"m3",
    "quantity_source":"survey","resource_plan_version":"Resource Plan Rev 1",
    "resource_profile_json":[
      {"Period":"2026-03","Trade":"Electrical labour hours","Demand hours":3800,"Available hours":4000},
      {"Period":"2026-03","Trade":"Crane equipment hours","Demand hours":180,"Available hours":200},
      {"Period":"2026-04","Trade":"Electrical labour hours","Demand hours":3700,"Available hours":4000},
      {"Period":"2026-04","Trade":"Crane equipment hours","Demand hours":170,"Available hours":200}]}),
 ("cost","cost_report",{"indirect_cost_plan":200_000,"indirect_cost_actual":198_000,
    "material_cost_baseline":800_000,"material_cost_current":805_000,
    "original_contingency":400_000,"remaining_contingency":380_000,
    "overhead_allocation_base":"labour hours","planned_allocation_base_quantity":50_000,
    "actual_allocation_base_quantity":49_500,"overhead_driver_source":"cost ledger","report_date":END,
    # RUN 103, GOAL THREE. The facts the owner's absorption-variance band needs: the two sides'
    # own periods, the cost-code population they share, and the progress basis that aligns the
    # planned absorption. Without them the module returns Not Assessed, which is the ruling.
    "overhead_actual_period":"2026-03","overhead_planned_period":"2026-03",
    "overhead_progress_basis":"earned labour hours against the resource-loaded baseline",
    "overhead_cost_code_population":"01-000 through 01-999 general conditions"}),
 ("rfi","rfi_log",{"rfi_total":40,"rfi_answered":38,"rfi_open":2,"rfi_overdue":0,
    "avg_response_days":6,"oldest_open_days":9,"rfi_period_days":30,"log_date":END}),
 ("rfa","rfa_log",{"rfa_total":30,"rfa_approved":27,"rfa_rejected":1,"rfa_resubmit":2,
    "rfa_open":0,"avg_review_days":8,"log_date":END}),
 ("sub","submittal_register",{"submittals_total":30,"submittals_rejected":1,
    "document_date":END,"document_risk_score":0.15}),
 ("ncr","ncr_log",{"ncr_issued":3,"ncr_closed":3,"ncr_open":0,"ncr_overdue":0,"report_period":"2026-03"}),
 # RUN 102, GOAL THREE, A6.2. EXPOSURE ABOVE THE 200,000-HOUR FLOOR so the benchmark ratio can
 # be banded at all, and three recordables: 1.5 per 200,000 hours against a benchmark of 2.4 is
 # a ratio of 0.625, which is Green.
 ("safety","safety_report",{"osha_recordable_incidents":3,"total_manhours":400_000,
    "incident_rate":1.5,"report_period":"2026-03"}),
 ("qa","quality_audit_report",{"audit_score":96,"total_findings":4,"critical_findings":0,
    "deficiency_count":4,"audit_date":END}),
 # RUN 102, GOAL THREE, A6.3. THE CORRECTIVE-ACTION REGISTER with required deadlines and closure
 # dates -- the shape the owner's timely-closure measure is defined on. All four closed on time.
 ("env","environmental_report",{"compliance_rate":1.0,"violations":0,"report_date":END,
    "permit_conditions_total":12,"operator_status":"in good standing",
    "environmental_jurisdiction":"State of Alaska","permitting_authority":"ADEC",
    "permit_id":"AKR10-1234","permit_version":"Rev 2","permit_site_id":"SITE-1",
    "environmental_corrective_actions_json":[
      {"Action No":"CA-01","Required deadline":"2026-01-20","Date closed":"2026-01-15",
       "Severity":"minor","Status":"Closed"},
      {"Action No":"CA-02","Required deadline":"2026-02-10","Date closed":"2026-02-09",
       "Severity":"minor","Status":"Closed"},
      {"Action No":"CA-03","Required deadline":"2026-03-05","Date closed":"2026-03-01",
       "Severity":"moderate","Status":"Closed"},
      {"Action No":"CA-04","Required deadline":"2026-03-25","Date closed":"2026-03-20",
       "Severity":"minor","Status":"Closed"}]}),
 ("subr","subcontractor_report",{"compliance_score":95,"on_time_deliveries":48,
    "scheduled_deliveries":50,"report_period":"2026-03"}),
 ("proc","procurement_log",{"long_lead_items_total":20,"at_risk":1,"delayed":0,
    "on_schedule":19,"report_date":END}),
 # RUN 102, GOAL THREE, A6.1. FIRST-PASS ACCEPTANCE, stated as first-pass and not as a total
 # passed count: 193 of 200 accepted on first inspection is 0.965, which is Green, and no
 # critical or hold-point item failed.
 ("insp","inspection_report",{"items_inspected":200,"items_passed":198,"items_failed":2,
    "items_passing_first_inspection":193,"critical_quality_failures_json":[],
    "critical_deficiency_count":0,"deficiency_count":2,"document_date":END,"document_risk_score":0.10}),
 ("weather","field_report",{"weather_days_lost":1,"float_remaining":29,"document_date":END,
    "document_risk_score":0.10,"quality_deficiencies_noted":0}),
 ("co","change_order",{"change_order_count":2,"baseline_contract_sum":BAC,
    "revised_contract_sum":BAC,"change_order_date":END}),
 ("oac","oac_minutes",{"document_date":END,"document_risk_score":0.10,
    "outstanding_action_items":2,"safety_incidents_discussed":0,"safety_actions_open":0,
    "quality_issues_discussed":0,"environmental_issues_discussed":0,"weather_days_discussed":1,
    "subcontractor_issues_discussed":0,"subcontractor_disputes":0}),
 # RUN 103, GOAL FOUR. THE CONTROLLED FIXTURE THE OWNER ORDERED: a contractor performance
 # report stating a SOURCE SCORE OF 76 OUT OF 100 -- not one of the five CPARS ratings and not a
 # point on the five-point scale, so it must reach A6.4's NUMERIC FALLBACK and band Amber. It
 # goes through the real upload route and the real compute route like every other document here.
 ("past","past_performance_report",{"overall_rating":76,"cost_rating":76,
    "schedule_rating":76,"quality_rating":76,
    "source":"Owner internal contractor performance scorecard, 76 out of 100"}),
]

# --------------------------------------------------------------- RUN 110 FIXTURE ADDITIONS
# Neither adds a document type nor a document. Both state fields that were ALREADY in the
# extraction contract before this run (Run 107) and that Run 109 measured reaching
# `documents.extraction` and producing no observation row.
_ADD = {
    # A4.5's six. `weather_days_discussed` is left exactly as Run 103 wrote it and is NOT
    # reinterpreted: it is a count of a conversation, not an approval.
    "oac_minutes": {
        "weather_days_claimed": 9, "weather_days_approved": 7,
        "weather_approval_period": "2026-03", "weather_allowance_days": 10,
        "weather_time_extension_granted": True, "weather_time_extension_days": 7,
    },
    # A4.8's four. `compliance_score` is left as Run 103 wrote it and is NOT read as a rating.
    "subcontractor_report": {
        "subcontractor_ratings_json": [
            {"Subcontractor": "Northline Mechanical", "Assessment period": "2026-03",
             "Rating": "Very Good"},
            {"Subcontractor": "Harbour Electrical", "Assessment period": "2026-03",
             "Rating": "Satisfactory"},
        ],
        "subcontractor_rating_scale": "owner_five_point_label",
        "subcontractor_report_date": END,
        "subcontractor_report_version": "1",
    },
}
DOCS = [(t, ty, {**ex, **_ADD.get(ty, {})}) for t, ty, ex in DOCS]

def raw(t): return f"%PDF-1.4 R110 {STAMP} {t}\n".encode()
set_extractor_override(StubExtractor({hashlib.sha256(raw(t)).hexdigest():(ty,ex) for t,ty,ex in DOCS}))
with S() as s:
    r=s.scalar(select(Participant).where(Participant.role=="ResearchAdmin"))
    if r is None: s.add(Participant(pseudonymous_code="R110-A-"+STAMP,role="ResearchAdmin",access_token_hash=hash_access_token(ADMIN)))
    else: r.access_token_hash=hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id==PID)) is None:
        s.add(Project(legacy_id=PID,doc={"id":PID,"name":"Run 110 census fixture","sector":"construction","signals":{},"events":[]}))
    s.commit()
admin=post({"action":"researchlogin","access_token":ADMIN})["session_token"]
c=post({"action":"adminparticipantcreate","session_token":admin,"pseudonymous_code":"R110-PM-"+STAMP,"role":"Participant","account_type":"operational"})
PM=post({"action":"researchlogin","access_token":c["access_token"]})["session_token"]
post({"action":"adminmemberadd","session_token":admin,"id":PID,"participant_id":c["participant_id"],"project_role":"PM"})

print("="*100); print("RUN 110 CENSUS -- twenty-one documents, real upload route, nothing supplied"); print("="*100)
ok=0
for t,ty,ex in DOCS:
    r=post({"action":"projectupload","session_token":PM,"id":PID,"period":1,"period_end":END,
            "documents":[{"filename":t+".pdf","mimeType":"application/pdf","dataBase64":b64(raw(t))}]})
    if r.get("ok"): ok+=1
    else: print("  upload FAILED", t, str(r)[:200])
print(f"uploaded {ok}/{len(DOCS)} documents through the real route")
r=post({"action":"projectcomputeall","session_token":PM,"id":PID})
print("computeall ok:", r.get("ok"), "| error:", str(r.get("error"))[:200] or "none")
ap=post({"action":"projectcategoryapply","session_token":PM,"id":PID,"period":1})
print("categoryapply:", ap.get("ok"), "readings", len(ap.get("readings") or []))

from app.simulation import registry as REG
with S() as s:
    p=s.scalar(select(Project).where(Project.legacy_id==PID))
    row=s.scalar(select(ComputedResult).where(ComputedResult.project_id==p.id, ComputedResult.superseded_by.is_(None)))
    if row is None:
        print()
        print("NO computed_results ROW STORED. The compute route produced nothing for this")
        print("project, so no module has any state at all. Census cannot be taken.")
        RESULTS, ABSTAINED = {}, {}
    else:
        RESULTS={m.get("module_id"):m for m in (row.module_results or [])}
        ABSTAINED={a.get("module_id"):a for a in (row.abstained or [])}

SVC=REG.service_index()
def _k(x): return (x.split(".")[0], int(x.split(".")[1]))
band=cnb=abst=fail=0
print(); print("-"*100)
print(f"{'MODULE':<8} {'STATE':<22} DETAIL")
print("-"*100)
CENSUS={}
for mid in sorted(SVC, key=_k):
    r=RESULTS.get(mid); a=ABSTAINED.get(mid)
    if r is not None and r.get("status_color"):
        state="BANDS "+str(r["status_color"]).upper(); band+=1
        detail=str(r.get("evidence_metric") or "")[:64]
    elif r is not None:
        state="COMPUTED, NO BAND"; cnb+=1
        detail=str(r.get("evidence_metric") or "")[:64]
    elif a is not None:
        state="ABSTAINS"; abst+=1
        detail=str(a.get("reason") or "")[:64]
    else:
        state="NO ROW AT ALL"; fail+=1; detail="neither computed nor abstained"
    CENSUS[mid]=state
    print(f"{mid:<8} {state:<22} {detail}")
print("-"*100)
print(f"CENSUS: band {band} | computed-no-band {cnb} | abstain {abst} | no row {fail} | total {len(SVC)}")
print("-"*100)
out=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else None
if out is not None:
    out.write_text(json.dumps(CENSUS, indent=1, sort_keys=True))
    print("census written to", out)
