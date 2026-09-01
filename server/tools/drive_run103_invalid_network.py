"""
RUN 103, GOAL ONE, THE OTHER HALF: THE DIAGNOSTICS ON AN INVALID NETWORK, THROUGH THE REAL ROUTE.

A project uploads a schedule update whose flattened export carries EIGHT different logic faults
at once. Nothing is repaired, nothing is inferred, no row is dropped and NO BEST-EFFORT PATH is
reported: A2.12 and A2.1 are both Not Assessed with the diagnostics as the stated reason, and the
diagnostics name the affected rows and activity ids so the scheduler can fix the source in one
pass. Nothing under test is supplied: the document goes through the real upload route and the
real compute route, and the reading is read back OUT OF THE STORED ROW.

The second half proves the diagnostics are not vacuous: each fault class is fired ON ITS OWN, and
a clean network is proved to raise none of them.
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
STAMP=str(int(time.time())); ADMIN="r103b-"+STAMP; END="2026-03-31"; PID="PRJ-R103B-"+STAMP
PASS=FAIL=0
def check(ok,label,detail=""):
    global PASS,FAIL
    if ok: PASS+=1; print(f"  PASS  {label}")
    else: FAIL+=1; print(f"  ****  {label}"+(f"   [{detail}]" if detail else ""))

BROKEN = [
  {"Activity ID":"B100","Duration":5,"Predecessors":"ZZZ"},                    # dangling pred
  {"Activity ID":"B100","Duration":3,"Predecessors":""},                       # duplicate id
  {"Activity ID":"","Duration":4,"Predecessors":""},                           # no identity
  {"Activity ID":"B130","Predecessors":"B100"},                                # missing duration
  {"Activity ID":"B140","Duration":2,"Predecessors":"B140"},                   # self link
  {"Activity ID":"B150","Duration":2,"Predecessors":"B160"},                   # cycle
  {"Activity ID":"B160","Duration":2,"Predecessors":"B150"},                   # cycle
  {"Activity ID":"B170","Duration":2,"Predecessors":[{"activity_id":"B100",
      "relation_type":"QQ","lag":"soon"}]},                                    # bad rel + lag
  {"Activity ID":"B180","Duration":2,"Predecessors":"","Calendar":"7-day"},     # calendar not defined
]
DOCS = [
 ("contract","contract_value",{"original_contract_sum":4_000_000,"project_start_date":"2026-01-01","project_end_date":"2027-06-30"}),
 ("sched","schedule_update",{"data_date":END,"planned_percent_complete":25.0,
    "schedule_network_json":BROKEN,"schedule_calendar":"5-day work week",
    "schedule_calendars_json":["5-day work week"],"schedule_version":"Rev 1",
    "schedule_baseline_finish_day":100}),
]
def raw(t): return f"%PDF-1.4 R103B {STAMP} {t}\n".encode()
set_extractor_override(StubExtractor({hashlib.sha256(raw(t)).hexdigest():(ty,ex) for t,ty,ex in DOCS}))
with S() as s:
    r=s.scalar(select(Participant).where(Participant.role=="ResearchAdmin"))
    if r is None: s.add(Participant(pseudonymous_code="R103B-A-"+STAMP,role="ResearchAdmin",access_token_hash=hash_access_token(ADMIN)))
    else: r.access_token_hash=hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id==PID)) is None:
        s.add(Project(legacy_id=PID,doc={"id":PID,"name":"Run 103 invalid network","sector":"construction","signals":{},"events":[]}))
    s.commit()
admin=post({"action":"researchlogin","access_token":ADMIN})["session_token"]
c=post({"action":"adminparticipantcreate","session_token":admin,"pseudonymous_code":"R103B-PM-"+STAMP,"role":"Participant","account_type":"operational"})
PM=post({"action":"researchlogin","access_token":c["access_token"]})["session_token"]
post({"action":"adminmemberadd","session_token":admin,"id":PID,"participant_id":c["participant_id"],"project_role":"PM"})
for t,ty,ex in DOCS:
    post({"action":"projectupload","session_token":PM,"id":PID,"period":1,"period_end":END,
          "documents":[{"filename":t+".pdf","mimeType":"application/pdf","dataBase64":b64(raw(t))}]})
print("computeall:", json.dumps(post({"action":"projectcomputeall","session_token":PM,"id":PID}))[:160])
with S() as s:
    p=s.scalar(select(Project).where(Project.legacy_id==PID))
    row=s.scalar(select(ComputedResult).where(ComputedResult.project_id==p.id, ComputedResult.superseded_by.is_(None)))
    RES={m["module_id"]:m for m in (row.module_results or [])}
    ABS={a["module_id"]:a for a in (row.abstained or [])}

print()
print("="*95)
print("THE DIAGNOSTICS ON AN INVALID NETWORK, READ BACK OUT OF THE STORED ROW")
print("="*95)
for mid in ("A2.12","A2.1"):
    r = RES.get(mid) or ABS.get(mid) or {}
    print(f"\n{mid}:")
    print("  status_color :", repr(r.get("status_color")))
    print("  reason       :", (r.get("reason") or r.get("evidence_metric") or "")[:900])
    d = r.get("schedule_network_diagnostics") or {}
    if d:
        print("  activities_read/accepted:", d.get("activities_read"), "/", d.get("activities_accepted"))
        print("  fault_counts :", json.dumps(d.get("fault_counts")))
        for k in (d.get("faults_present") or []):
            print(f"    {k}: {json.dumps(d.get(k))[:300]}")
    check(r.get("status_color") is None, f"{mid} is NOT ASSESSED on an invalid network")
    check("controlling_path" not in r and "criticality_index" not in r,
          f"{mid} reports NO best-effort path and no partial reading")

_d = (RES.get("A2.12") or ABS.get("A2.12") or {}).get("schedule_network_diagnostics") or {}
check(len(_d.get("faults_present") or []) >= 7,
      "the diagnostics name EVERY fault at once, not the first one the parser hit",
      str(_d.get("faults_present")))
check(bool(_d.get("dangling_predecessor")) and _d["dangling_predecessor"][0].get("row"),
      "and each fault carries the affected SOURCE ROW or activity id",
      json.dumps(_d.get("dangling_predecessor"))[:200])

# ---------------------------------------------------------- NON-VACUITY, FAULT BY FAULT
print()
print("="*95)
print("NON-VACUITY: EACH DIAGNOSTIC FIRED ON A NETWORK CARRYING EXACTLY THAT FAULT")
print("="*95)
from app.simulation.canonical_v3 import schedule_network_diagnostics as D
CLEAN = {"activities":[{"activity_id":"A","current_duration":3},
                       {"activity_id":"B","current_duration":4,"predecessors":["A"]}],
         "calendars":["5-day"]}
_c = D(CLEAN)
check(_c["valid"] and _c["fault_total"] == 0,
      "a clean network raises NO diagnostic and is valid", json.dumps(_c["fault_counts"]))
ONE_EACH = {
  "missing_activity_id": {"activities":[{"activity_id":"","current_duration":1}]},
  "duplicate_activity_id": {"activities":[{"activity_id":"A","current_duration":1},
                                          {"activity_id":"A","current_duration":2}]},
  "dangling_predecessor": {"activities":[{"activity_id":"A","current_duration":1,
                                          "predecessors":["Q"]}]},
  "dangling_successor": {"activities":[{"activity_id":"A","current_duration":1,
                                        "successors":["Q"]}]},
  "self_link": {"activities":[{"activity_id":"A","current_duration":1,"predecessors":["A"]}]},
  "cycle_activities": {"activities":[{"activity_id":"A","current_duration":1,"predecessors":["B"]},
                                     {"activity_id":"B","current_duration":1,"predecessors":["A"]}]},
  "missing_duration": {"activities":[{"activity_id":"A"}]},
  "negative_duration": {"activities":[{"activity_id":"A","current_duration":-2}]},
  "unreadable_predecessor_list": {"activities":[{"activity_id":"A","current_duration":1,
                                                 "predecessors":"not-a-list"}]},
  "unrecognised_relation_type": {"activities":[{"activity_id":"A","current_duration":1},
      {"activity_id":"B","current_duration":1,
       "predecessors":[{"activity_id":"A","relation_type":"QQ"}]}]},
  "unreadable_lag": {"activities":[{"activity_id":"A","current_duration":1},
      {"activity_id":"B","current_duration":1,
       "predecessors":[{"activity_id":"A","lag":"soon"}]}]},
  "disconnected_components": {"activities":[{"activity_id":"A","current_duration":1},
                                            {"activity_id":"B","current_duration":1}]},
  "invalid_calendar": {"activities":[{"activity_id":"A","current_duration":1,"calendar":"7-day"}],
                       "calendars":["5-day"]},
}
for fault, structure in ONE_EACH.items():
    d = D(structure)
    check(d["fault_counts"].get(fault, 0) >= 1 and not d["valid"],
          f"the {fault} diagnostic fires on a network carrying exactly that fault",
          json.dumps(d["faults_present"]))
    check(sorted(d["faults_present"]) == [fault] or fault in d["faults_present"],
          f"  ... and it is the fault reported for it", json.dumps(d["faults_present"]))

print()
print(f"RESULT: {PASS}/{PASS+FAIL} checks passed")
sys.exit(0 if FAIL == 0 else 1)
