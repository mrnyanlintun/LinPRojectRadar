#!/usr/bin/env python3
"""RUN 78 NON-VACUITY. Two checks, each pinned to its exact site and each shown to FAIL when
that site is reverted.

  A. `a_projectuploadstatus`'s baseline/amendments block reads the observation store. Archive
     the contract award; the baseline must stop being reported. Reverting the `withdrawn_at`
     filter must make it come back.
  B. `_period_is_stale`'s Category-9 condition. Strip `evidenceQualification` from a stored
     result and press the same compute control the owner presses; it must recompute and put
     the key back. Reverting the condition must make it skip.
"""
from __future__ import annotations
import base64, hashlib, io, json, logging, sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
logging.disable(logging.WARNING)
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas as rl_canvas
from fastapi.testclient import TestClient
from sqlalchemy import select
import app.main as main
from app.documents import set_extractor_override
from app.extraction_client import StubExtractor
from app.extraction_fields import extraction_fields_for
from app.models import Project
from app.research_identity import hash_access_token
from app.research_models import Participant, ComputedResult
from sqlalchemy.orm.attributes import flag_modified

REVERT = "--revert" in sys.argv
client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
STAMP = int(time.time())
PID = f"PRJ-R78V-{STAMP}"; ADMIN = f"run78v-{STAMP}"; PE = "2026-03-31"
def post(p):
    return client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"}).json()
def b64(r): return base64.b64encode(r).decode()

DOCSET = [("D01_contract_award.pdf","contract_value"),
          ("D02_pay_application.pdf","pay_application"),
          ("D06_monthly_report.pdf","monthly_report")]
VALUES = {"original_contract_sum":4_000_000,"project_start_date":"2026-01-01",
  "project_end_date":"2027-06-30","federal_acquisition":True,
  "contracting_agency":"GSA","acquisition_designation":"development","major_acquisition":True,
  "agency_procedure_requires_evms":True,"evms_clause_id":"FAR 52.234-4",
  "award_date":"2026-01-01","acquisition_id":"GS-P-26-0114",
  "amount_paid_to_date":1_050_000,"completed_to_date":1_000_000,
  "percent_complete_verified":25.0,"application_date":PE,
  "original_contingency":920_000,"remaining_contingency":892_400,
  "earned_value":1_000_000,"actual_cost":1_050_000,"planned_value":1_020_000,
  "actual_percent_complete":25.0,"budget_at_completion":4_000_000,"report_date":PE,
  "document_date":PE}
BYTES,OV={},{}
for fn,dt in DOCSET:
    ex={f:VALUES[f] for f in (extraction_fields_for(dt) or []) if f in VALUES}
    ex.setdefault("document_date",PE)
    buf=io.BytesIO(); c=rl_canvas.Canvas(buf,pagesize=LETTER); c.setFont("Helvetica",9); y=720
    c.drawString(72,y,f"{fn} stamp {STAMP}"); y-=20
    for k,v in ex.items():
        c.drawString(72,y,f"{k}: {v}"); y-=12
    c.showPage(); c.save(); raw=buf.getvalue()
    BYTES[fn]=raw; OV[hashlib.sha256(raw).hexdigest()]=(dt,ex,0.95)
set_extractor_override(StubExtractor(OV))

with Session() as s:
    row=s.scalar(select(Participant).where(Participant.role=="ResearchAdmin"))
    row.access_token_hash=hash_access_token(ADMIN)
    s.add(Project(legacy_id=PID,doc={"id":PID,"name":"Run 78 non-vacuity","signals":{},"events":[]}))
    s.commit()
admin=post({"action":"researchlogin","access_token":ADMIN})["session_token"]
cr=post({"action":"adminparticipantcreate","session_token":admin,
         "pseudonymous_code":f"R78V-PM-{STAMP}","role":"Participant","account_type":"operational"})
PM=post({"action":"researchlogin","access_token":cr["access_token"]})["session_token"]
post({"action":"adminmemberadd","session_token":admin,"id":PID,
      "participant_id":cr["participant_id"],"project_role":"PM"})
post({"action":"projectupload","session_token":PM,"id":PID,"period":1,"period_end":PE,
      "documents":[{"filename":fn,"mimeType":"application/pdf","dataBase64":b64(BYTES[fn])}
                   for fn,_ in DOCSET]})
post({"action":"projectcomputeall","session_token":PM,"id":PID})

# --------------------------------------------------------------- B. the staleness condition
with Session() as s:
    proj=s.scalar(select(Project).where(Project.legacy_id==PID))
    r=s.scalar(select(ComputedResult).where(ComputedResult.project_id==proj.id,
                                            ComputedResult.period==1,
                                            ComputedResult.superseded_by.is_(None)))
    had="evidenceQualification" in (r.signal_inputs or {})
    si=dict(r.signal_inputs or {}); si.pop("evidenceQualification",None)
    r.signal_inputs=si; flag_modified(r,"signal_inputs"); s.commit(); rid=r.result_id
resp=post({"action":"projectcompute","session_token":PM,"id":PID,"period":1})
with Session() as s:
    proj=s.scalar(select(Project).where(Project.legacy_id==PID))
    r=s.scalar(select(ComputedResult).where(ComputedResult.project_id==proj.id,
                                            ComputedResult.period==1,
                                            ComputedResult.superseded_by.is_(None)))
    back="evidenceQualification" in (r.signal_inputs or {})
print(f"CHECK B  key present on first compute: {had}")
print(f"CHECK B  after stripping it, projectcompute recomputed={resp.get('recomputed')} "
      f"note={str(resp.get('note') or resp.get('reason'))[:110]}")
print(f"CHECK B  key restored: {back}")
print(f"CHECK B  {'PASS' if had and resp.get('recomputed') and back else 'FAIL'}")

# --------------------------------------------------------------- A. the baseline reader
st=post({"action":"projectuploadstatus","session_token":PM,"id":PID,"period":1})
before=(st.get("baseline") or {}).get("original")
cid=[d["document_id"] for d in st["documents"] if d["filename"]=="D01_contract_award.pdf"][0]
post({"action":"projectdocumentarchive","session_token":PM,"id":PID,"period":1,
      "document_ids":[cid],"confirmation":"Withdraw the contract award."})
st2=post({"action":"projectuploadstatus","session_token":PM,"id":PID,"period":1})
after=(st2.get("baseline") or {}).get("original")
print(f"CHECK A  baseline BEFORE archive: {before}")
print(f"CHECK A  baseline AFTER  archive: {after}")
print(f"CHECK A  {'PASS' if before and not after else 'FAIL'} "
      f"(expected: reported before, gone after)")
