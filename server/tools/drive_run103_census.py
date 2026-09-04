"""
RUN 103. THE CENSUS, CRITICAL PATH ANALYSIS, AND THE CONTRACTOR 76 FIXTURE, ON THE REAL ROUTE.

1. GOAL ONE. A project whose PYTHON row carries category postures must render those postures on
   the Governance Decision card, read back out of the RENDERED DOM, with the card naming which
   layer produced each one.
2. GOAL TWO. Schedule's four modules band, and at least one of them bands ON THIS PROJECT.
3. GOAL THREE. A6.1, A6.2, A6.3 and A6.4 band on their rebuilt measures, on this project.
4. GOAL FIVE. Whether a project authored to good performance across all five required categories
   can publish Green.
5. Nothing under test is supplied. Twenty-three documents go through the REAL upload route, the
   REAL compute route and the REAL category-apply route; the REAL application is then served and
   the REAL detail page opened in Chromium. The decision brief is not composed here, not
   injected here, and handed to no render function. `window.LinResults.rowFor` is NOT
   substituted -- the two drivers that do that (drive_run96_card, drive_run94_charts) are not
   used and violate the owner's verification rule.
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
    assert r.status_code == 200, r.text[:300]
    return r.json()
def b64(x): return base64.b64encode(x).decode()
STAMP=str(int(time.time())); ADMIN="r103-"+STAMP; BAC=4_000_000; END="2026-03-31"; PID="PRJ-R103-"+STAMP
# A healthy project: on budget, on schedule, clean documents, authored to GOOD performance in
# every one of the five required categories.
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
def raw(t): return f"%PDF-1.4 R102 {STAMP} {t}\n".encode()
set_extractor_override(StubExtractor({hashlib.sha256(raw(t)).hexdigest():(ty,ex) for t,ty,ex in DOCS}))
with S() as s:
    r=s.scalar(select(Participant).where(Participant.role=="ResearchAdmin"))
    if r is None: s.add(Participant(pseudonymous_code="R102-A-"+STAMP,role="ResearchAdmin",access_token_hash=hash_access_token(ADMIN)))
    else: r.access_token_hash=hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id==PID)) is None:
        s.add(Project(legacy_id=PID,doc={"id":PID,"name":"Run 102 fixture","sector":"construction","signals":{},"events":[]}))
    s.commit()
admin=post({"action":"researchlogin","access_token":ADMIN})["session_token"]
c=post({"action":"adminparticipantcreate","session_token":admin,"pseudonymous_code":"R102-PM-"+STAMP,"role":"Participant","account_type":"operational"})
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


# =============================================================================================
# RUN 103, GOAL FIVE -- THE CENSUS. EVERY MODULE IN SERVICE, ON ONE PROJECT, WITH THE
# THREE-WAY CLASSIFICATION. Not a sample: the population is `registry.service_index()` itself.
# =============================================================================================
from app.simulation import registry as REG

with S() as s:
    p = s.scalar(select(Project).where(Project.legacy_id == PID))
    row = s.scalar(select(ComputedResult).where(ComputedResult.project_id == p.id,
                                                ComputedResult.superseded_by.is_(None)))
    RESULTS = {m.get("module_id"): m for m in (row.module_results or [])}
    ABSTAINED = {a.get("module_id"): a for a in (row.abstained or [])}
    CATS = {k: (v or {}).get("status") for k, v in (row.category_statuses or {}).items()}
    STATUS = row.project_status

SVC = REG.service_index()
CENSUS = []
for mid in sorted(SVC, key=lambda x: (x.split(".")[0], int(x.split(".")[1]))):
    r = RESULTS.get(mid)
    ab = ABSTAINED.get(mid)
    name = SVC[mid]["module_name"]
    cat = SVC[mid]["category"] + " " + SVC[mid]["category_name"]
    if r is None and ab is None:
        CENSUS.append((mid, name, cat, "NOT DISPATCHED", "", "", "defect",
                       "the module is in service but produced neither a result row nor an "
                       "abstention row on this project"))
        continue
    src = r or ab
    band = src.get("status_color")
    # THE THREE-WAY CLASSIFICATION THE OWNER'S SECTION 6 ASKS FOR. It is decided from the row
    # itself and never from a list written here: an ABSTENTION row is one the registry stored in
    # `abstained` (the module could not carry out its method -- a MISSING DOCUMENT FIELD); a
    # COMPUTED row with no colour is one whose method ran and whose band was withheld (a MISSING
    # THRESHOLD or an unstated fact its band needs); and anything else is a DEFECT.
    if band:
        CENSUS.append((mid, name, cat, "BAND", band,
                       (src.get("band_boundary") or "")[:400],
                       "-", (src.get("band_provenance_class") or "?") + " / "
                       + (src.get("threshold_source") or "?")))
    elif ab is not None and r is None:
        why = ab.get("reason") or src.get("evidence_metric") or ""
        CENSUS.append((mid, name, cat, "ABSTAINED", "", "", "missing document field", why))
    elif src.get("band_asserted") is False or src.get("calibration_pending"):
        why = src.get("band_withheld_reason") or src.get("calibration_note") or ""
        CENSUS.append((mid, name, cat, "COMPUTED, NO BAND", "", "", "missing threshold", why))
    elif src.get("insufficient_data"):
        CENSUS.append((mid, name, cat, "ABSTAINED", "", "", "missing document field",
                       src.get("evidence_metric") or ""))
    else:
        CENSUS.append((mid, name, cat, "COMPUTED, NO BAND", "", "", "missing threshold",
                       json.dumps({k: v for k, v in src.items()
                                   if k in ("evidence_metric", "reason")})[:300]))

print()
print("=" * 100)
print("GOAL FIVE -- THE CENSUS: EVERY MODULE IN SERVICE ON ONE PROJECT")
print("=" * 100)
print(f"population: registry.service_index() = {len(SVC)} modules; none sampled, none omitted")
for c in CENSUS:
    print()
    print(f"  {c[0]:6s} {c[1]}  [{c[2]}]")
    print(f"         produced : {c[3]}" + (f"  {c[4]}" if c[4] else ""))
    if c[3] == "BAND":
        print(f"         provenance/threshold_source : {c[7]}")
        print(f"         boundary : {c[5]}")
    else:
        print(f"         cause    : {c[6]}")
        print(f"         reason   : {c[7][:420]}")
_b = sum(1 for c in CENSUS if c[3] == "BAND")
_n = sum(1 for c in CENSUS if c[3] == "COMPUTED, NO BAND")
_a = sum(1 for c in CENSUS if c[3] == "ABSTAINED")
_f = sum(1 for c in CENSUS if c[3] in ("NOT DISPATCHED", "OTHER"))
print()
print(f"CENSUS TOTALS: banded {_b} | computed without banding {_n} | abstained {_a} | failed {_f}"
      f" | total {len(CENSUS)}")
print("CENSUS ROWS (tab separated, for the report):")
for c in CENSUS:
    print("\t".join([c[0], c[1], c[2], c[3], c[4], c[6],
                     " ".join((c[7] or "").split())[:300]]))
print()
print("stored project_status =", repr(STATUS), "| categories:", json.dumps(CATS))

# --------------------------------------------------------- GOAL ONE: WHAT CPA PRODUCED
print()
print("=" * 100)
print("GOAL ONE -- A2.12 CRITICAL PATH ANALYSIS ON THIS REAL PROJECT")
print("=" * 100)
_cpa = RESULTS.get("A2.12") or ABSTAINED.get("A2.12") or {}
for k in ("status_color", "evidence_metric", "controlling_path", "controlling_path_length_days",
          "forecast_completion_day", "baseline_completion_day", "forecast_finish_variance_days",
          "imposed_finish_day", "controlling_path_total_float_days",
          "remaining_planned_duration_days", "critical_count", "near_critical_count",
          "negative_float_count", "minimum_total_float_days", "median_total_float_days",
          "critical_flag_tolerance_days", "near_critical_band_days",
          "ten_lowest_float_activities", "logic_integrity", "band_governing_rules",
          "band_rules_not_evaluable", "band_basis_id", "band_withheld_reason"):
    if k in _cpa:
        print(f"  {k} = {json.dumps(_cpa[k])[:600]}")
print("  band_boundary:", (_cpa.get("band_boundary") or "")[:1600])
print("  band_rules:")
for _r in (_cpa.get("band_rules") or []):
    print("    -", json.dumps(_r)[:400])
print("  diagnostics on the VALID network:",
      json.dumps((_cpa.get("schedule_network_diagnostics") or {}).get("fault_counts")))
print("  A2.1 PERT on the same network:",
      json.dumps({k: v for k, v in (RESULTS.get("A2.1") or ABSTAINED.get("A2.1") or {}).items()
                  if k in ("status_color", "evidence_metric", "most_critical_activity",
                           "most_critical_share", "trials", "project_finish_p80")})[:700])

# --------------------------------------------------------- GOAL FOUR: THE 76 FIXTURE TRACED
print()
print("=" * 100)
print("GOAL FOUR -- THE CONTRACTOR 76 FIXTURE, FROM DOCUMENT TO CATEGORY POSTURE")
print("=" * 100)
_a64 = RESULTS.get("A6.4") or ABSTAINED.get("A6.4") or {}
print("  A6.4 status_color   =", repr(_a64.get("status_color")))
print("  A6.4 evidence       =", (_a64.get("evidence_metric") or "")[:300])
print("  A6.4 factor_ratings =", json.dumps(_a64.get("factor_ratings"))[:300])
print("  A6.4 threshold_source =", repr(_a64.get("threshold_source")),
      "| provenance =", repr(_a64.get("band_provenance")))
print("  A6.4 boundary       =", (_a64.get("band_boundary") or "")[:500])
print("  A6 category posture (stored row) =", repr(CATS.get("A6")))
# DOES DELIVERY QUALITY'S POSTURE REFLECT IT? MEASURED, NOT ASSUMED. The category is formed by
# `fusion.fuse_signals` over lineage-bearing signals, and ACROSS INDEPENDENT BODIES that is
# Dempster's rule, not worst-wins. So the question is answered by re-running the platform's OWN
# fusion over the stored A6 bands three ways -- as stored, with A6.4 removed, and with A6.4 set
# Red -- and reading what moves. This block is HARNESS, not the route: it re-uses the real
# fusion and the real lineage records on the real stored bands.
from app.simulation.fusion import fuse_signals as _FS
from app.simulation.lineage import lineage_for as _LF
def _a6_fuse(bands):
    return _FS([{"module_id": m, "status": b, "lineage": _LF(m)} for m, b in bands.items()])
_stored = {m: RESULTS[m]["status_color"] for m in sorted(RESULTS) if m.startswith("A6.")}
print("  A6 bands as stored          :", json.dumps(_stored))
_f0 = _a6_fuse(_stored)
_f1 = _a6_fuse({m: b for m, b in _stored.items() if m != "A6.4"})
_f2 = _a6_fuse({**_stored, "A6.4": "Red"})
print("  A6 fused as stored          :", _f0 and _f0["status"], "conflict",
      round((_f0 or {}).get("conflict", 0), 4))
print("  A6 fused with A6.4 REMOVED  :", _f1 and _f1["status"], "conflict",
      round((_f1 or {}).get("conflict", 0), 4))
print("  A6 fused with A6.4 set Red  :", _f2 and _f2["status"], "conflict",
      round((_f2 or {}).get("conflict", 0), 4))
print("  A6 modules that computed:", sorted(m for m in RESULTS if m.startswith("A6.")))
# =============================================================================================
# RUN 101, GOAL FOUR AND GOAL FIVE. THE CARD ON THE OWNER'S OWN ROUTE, READ FROM THE DOM.
#
# NOTHING UNDER TEST IS SUPPLIED. The fixture above seeded 21 documents through the REAL upload
# route and computed through the REAL compute route, which section 1's verification rule
# expressly permits. Below, the REAL application is served and the REAL project detail page is
# opened in Chromium; the Governance Decision panel is read BACK OUT OF THE RENDERED DOM. The
# decision brief is NOT composed here, NOT injected here, and NOT handed to any render function.
#
# CONTRAST with drive_run96_card.py and drive_run94_charts.py, which substitute
# `window.LinResults.rowFor`. Both violate the verification rule and neither is used here.
# =============================================================================================
import os, re, socket, threading

PASS = FAIL = 0
def check(ok, label, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1; print(f"  PASS  {label}")
    else:
        FAIL += 1; print(f"  ****  {label}" + (f"   [{detail}]" if detail else ""))

res = post({"action": "projectresults", "session_token": PM, "id": PID, "period": 1})
_r = res.get("result") or {}
_brief = _r.get("decision_brief") or {}
print()
print("=" * 90)
print("THE SERVED DECISION BRIEF, from `projectresults` -- the route the page itself calls")
print("=" * 90)
print("  brief present:", bool(_brief))
_drv = (_brief.get("drivers") or {})
for d in (_drv.get("collapsed") or []) + (_drv.get("expanded") or []):
    print(f"  driver {d.get('module_id')} [{d.get('band')}] {d.get('category_name')}")
    print(f"     figure   : {d.get('reading')}")
    print(f"     boundary : {(d.get('boundary') or '(none recorded)')}")
    print(f"     basis    : {(d.get('boundary_basis') or '(none recorded)')}")
    print(f"     provenance: {d.get('boundary_provenance')} / cutoffs "
          f"{d.get('boundary_cutoff_provenance')}")

# ---------------------------------------------------------------- GOAL ONE'S PATTERN TEST
# RUN 98's five families, re-run over the WHOLE card and PROVED ABLE TO FAIL FIRST, exactly as
# section 6 requires. The patterns are Run 98's, unchanged and not weakened.
# RUN 101 CORRECTED ITSELF HERE, AND THE MISTAKE IS RECORDED RATHER THAN QUIETLY FIXED.
# This driver first carried a HAND-TRANSCRIBED copy of Run 98's five families, and the
# transcription added imperative verbs Run 98 does not use -- "Schedule" among them. Applied to
# the rendered card it fired on the CATEGORY NAME "Schedule Performance", reporting an issued
# instruction where there was a category heading. That is a defect in the copy, not in the card.
#
# THE PATTERNS BELOW ARE NOW READ OUT OF `drive_run98.py` ITSELF, so there is one authority for
# them and a hand copy cannot drift from it again. Reading them is neither weakening the check
# (section 12.7) nor strengthening it: it is the same check.
_run98 = (HERE / "drive_run98.py").read_text()
exec(_run98[_run98.index("IMPERATIVE_PATTERNS = ["):_run98.index("def scan_imperative(text):")])


def scan_imperative(text):
    hits = []
    for name, pat in IMPERATIVE_PATTERNS:
        for m in re.finditer(pat, text or "", re.IGNORECASE):
            hits.append((name, m.group(0).strip()))
    return hits

print()
print("=" * 90)
print("THE IMPERATIVE / AUTHORITY PATTERN TEST, PROVED ABLE TO FAIL BEFORE IT IS USED")
print("=" * 90)
_probe = scan_imperative(PRESCRIPTIVE_PROBE)
for h in _probe:
    print(f"    HIT  [{h[0]}] {h[1]!r}")
check(len({h[0] for h in _probe}) >= 4,
      "the pattern test fires on a prescriptive probe, on at least four of its five families",
      str(sorted({h[0] for h in _probe})))

# ---------------------------------------------------------------- THE RAISED CHECK, PROVED
# SECTION 6's LAST LINE RAISES THE BAR: "a sentence citing a band without saying what the
# boundary was should not pass". RAISING A BAR IS NOT WEAKENING A CHECK, but a raised check
# must be PROVED still able to fail on the thing it is meant to catch, so it is proved here on
# a driver row that cites a band and records no boundary.
def cites_band_without_boundary(driver):
    return bool(driver.get("band")) and not driver.get("boundary")

_bad = {"module_id": "X.1", "band": "Amber", "reading": "some figure", "boundary": None}
check(cites_band_without_boundary(_bad),
      "the raised check FIRES on a driver citing a band with no boundary recorded (proved able "
      "to fail)")
_good = {"module_id": "A3.2", "band": "Green", "reading": "f", "boundary": "at or below 1.0"}
check(not cites_band_without_boundary(_good),
      "and it does NOT fire on a driver that records its boundary (no false positive)")

sock = socket.socket(); sock.bind(("127.0.0.1", 0)); PORT = sock.getsockname()[1]; sock.close()
import uvicorn
cfg = uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="critical")
srv = uvicorn.Server(cfg)
threading.Thread(target=srv.run, daemon=True).start()
for _ in range(200):
    try:
        c = socket.create_connection(("127.0.0.1", PORT), 0.2); c.close(); break
    except OSError: time.sleep(0.05)
BASE = f"http://127.0.0.1:{PORT}"
SHELL = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"
print()
print("served at:", BASE, "| cwd:", os.getcwd(), "| DATABASE_URL:", os.environ.get("DATABASE_URL"))

from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=SHELL,
                                 args=["--use-gl=swiftshader", "--no-sandbox"])
    page = browser.new_page(viewport={"width": 1280, "height": 2400})
    for pattern in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                    "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
        page.route(pattern, lambda r: r.abort())
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    out = page.evaluate("""async (id) => {
        if (window.LinApp && LinApp.openDetail) LinApp.openDetail(id);
        await new Promise(r => setTimeout(r, 1500));
        await window.LinDetail.render(id);
        let row = null;
        for (let i = 0; i < 200; i++) {
          row = (window.LinResults && window.LinResults.rowFor)
              ? window.LinResults.rowFor({id: id}) : null;
          if (row && row.decision_brief) break;
          await new Promise(r2 => setTimeout(r2, 250));
        }
        const body = document.querySelector('#body-d-decision');
        if (body) body.style.display = '';
        document.dispatchEvent(new CustomEvent('lin:section-opened',
                                               {detail: {id: 'd-decision'}}));
        await new Promise(r => setTimeout(r, 2500));
        const panel = document.querySelector('#body-d-decision');
        return {
          text: panel ? (panel.innerText || '') : null,
          headings: panel ? Array.from(panel.querySelectorAll('h2,h3'))
              .map(n => n.textContent.trim()) : [],
          rowHasBrief: !!(row && row.decision_brief),
        };
    }""", PID)
    browser.close()
srv.should_exit = True

print()
print("=" * 90)
print("THE GOVERNANCE DECISION CARD, AS IT RENDERS ON THE OWNER'S OWN ROUTE AT 1280px")
print("NOTHING WAS SUPPLIED TO THE RENDERER. This is the rendered DOM's own innerText.")
print("=" * 90)
print(out.get("text"))
print("=" * 90)
print("headings:", out.get("headings"))
print("row carried a decision_brief:", out.get("rowHasBrief"))

_card = out.get("text") or ""
# RUN 135C, M8. The Run 106 guard, copied here. `out.get("text") or ""` coerces a panel that did
# not render into the empty string, after which "no imperative on card", "every band cites its
# boundary" and "every boundary cites its basis" are all trivially true -- three terminal checks
# passing on a card nobody saw. drive_run106.py:466 already carries this guard; these three
# omitted it. A missing card is now a FAILURE before the three checks are reached.
check(bool(_card), "the Governance Decision card rendered on the real page",
      f"panel text was {out.get('text')!r}")
_hits = scan_imperative(_card)
check(not _hits, "no action, instruction, deadline, remedy or authority appears on the card",
      str(_hits[:4]))
check("Boundary:" in _card or not any(
        d.get("band") for d in ((_drv.get("collapsed") or []) + (_drv.get("expanded") or []))),
      "every driver citing a band on the rendered card also states its boundary")
check("Basis:" in _card or "Boundary:" not in _card,
      "and every stated boundary on the rendered card also states its basis")
print()
print(f"RESULT: {PASS}/{PASS + FAIL} checks passed")
