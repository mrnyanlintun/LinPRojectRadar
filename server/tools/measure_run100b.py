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

def run_project(tag, pct, ev, ac):
    STAMP=str(int(time.time()*1000))+tag
    ADMIN="r100b-"+STAMP; BAC=4_000_000; END="2026-03-31"; PID="PRJ-R100B-"+STAMP
    DOCS=[
     ("contract","contract_value",{"original_contract_sum":BAC,"project_start_date":"2026-01-01","project_end_date":"2027-06-30"}),
     ("tps","time_phased_schedule",{"planned_value_to_date":ev,"planned_percent_complete":pct,
        "data_date":END,"document_date":END}),
     ("pay","pay_application",{"amount_paid_to_date":ac,"completed_to_date":ev,
        "percent_complete_verified":pct,"application_date":END,"document_date":END}),
    ]
    def raw(t): return f"%PDF-1.4 R100B {STAMP} {t}\n".encode()
    set_extractor_override(StubExtractor({hashlib.sha256(raw(t)).hexdigest():(ty,ex) for t,ty,ex in DOCS}))
    with S() as s:
        r=s.scalar(select(Participant).where(Participant.role=="ResearchAdmin"))
        if r is None: s.add(Participant(pseudonymous_code="R100B-A-"+STAMP,role="ResearchAdmin",access_token_hash=hash_access_token(ADMIN)))
        else: r.access_token_hash=hash_access_token(ADMIN)
        if s.scalar(select(Project).where(Project.legacy_id==PID)) is None:
            s.add(Project(legacy_id=PID,doc={"id":PID,"name":"Run100B "+tag,"sector":"construction","signals":{},"events":[]}))
        s.commit()
    admin=post({"action":"researchlogin","access_token":ADMIN})["session_token"]
    c=post({"action":"adminparticipantcreate","session_token":admin,"pseudonymous_code":"R100B-PM-"+STAMP,"role":"Participant","account_type":"operational"})
    PM=post({"action":"researchlogin","access_token":c["access_token"]})["session_token"]
    post({"action":"adminmemberadd","session_token":admin,"id":PID,"participant_id":c["participant_id"],"project_role":"PM"})
    for t,ty,ex in DOCS:
        post({"action":"projectupload","session_token":PM,"id":PID,"period":1,"period_end":END,
              "documents":[{"filename":t+".pdf","mimeType":"application/pdf","dataBase64":b64(raw(t))}]})
    post({"action":"projectcomputeall","session_token":PM,"id":PID})
    ap=post({"action":"projectcategoryapply","session_token":PM,"id":PID,"period":1})
    print(f"--- project {tag}: pct={pct} ev={ev} ac={ac} ---")
    for rd in (ap.get("readings") or []):
        if str(rd.get("category"))=="A1":
            print("   A1 state   :", rd.get("state"))
            print("   A1 status  :", repr(rd.get("status")))
            print("   A1 servedBy:", rd.get("served_by") or rd.get("servedBy"))
            print("   A1 reason  :", str(rd.get("reason") or rd.get("error") or "")[:300])
    return ap

run_project("X", 100.0, 4_000_000, 4_000_000)
run_project("Y", 25.0, 1_000_000, 1_050_000)
