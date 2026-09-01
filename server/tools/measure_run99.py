#!/usr/bin/env python3
"""RUN 99 MEASUREMENT. Server-side only: what the compute route stores, what the portfolio
route serves, for three fixtures built through the REAL routes.

  A  documents uploaded, Process all NOT pressed
  B  documents uploaded, Process all pressed (the owner's two projects)
  C  as B, plus the participant's own `projectcategoryapply` button
  D  as C, but EV = PV = AC = BAC at 100 per cent (the Complete condition)

Nothing under test is supplied. Run from a clean cwd with DATABASE_URL on a throwaway sqlite.
"""
from __future__ import annotations
import base64, hashlib, json, logging, pathlib, sys, time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)

from fastapi.testclient import TestClient            # noqa: E402
from sqlalchemy import select                        # noqa: E402
import app.main as main                              # noqa: E402
from app.documents import set_extractor_override     # noqa: E402
from app.extraction_client import StubExtractor      # noqa: E402
from app.models import Project                       # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import Participant, ComputedResult  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory

def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code} {r.text[:300]}"
    return r.json()

def b64(x): return base64.b64encode(x).decode()

STAMP = str(int(time.time()))
ADMIN = "run99-admin-" + STAMP
BAC = 4_000_000
END = "2026-03-31"

# under-running, healthy figures for A/B/C; the Complete condition for D
FIG = {"ev": 1_000_000, "ac": 1_050_000, "pv": 1_020_000, "ppct": 25.50, "apct": 25.00}
FIGD = {"ev": BAC, "ac": BAC, "pv": BAC, "ppct": 100.0, "apct": 100.0}

IDS = {k: f"PRJ-R99-{k}-{STAMP}" for k in "ABCD"}

def docs_for(pid, f):
    return [
        (f"{pid}-contract", "contract_value",
         {"original_contract_sum": BAC, "project_start_date": "2026-01-01",
          "project_end_date": "2027-06-30"}),
        (f"{pid}-tps", "time_phased_schedule",
         {"planned_value_to_date": f["pv"], "planned_percent_complete": f["ppct"],
          "data_date": END, "document_date": END}),
        (f"{pid}-pay", "pay_application",
         {"amount_paid_to_date": f["ac"], "completed_to_date": f["ev"],
          "percent_complete_verified": f["apct"],
          "application_date": END, "document_date": END}),
    ]

ALL_DOCS = {}
for k in "ABCD":
    ALL_DOCS[k] = docs_for(IDS[k], FIGD if k == "D" else FIG)

def raw(tag): return f"%PDF-1.4 RUN99 {STAMP} {tag}\n".encode()

set_extractor_override(StubExtractor({
    hashlib.sha256(raw(t)).hexdigest(): (ty, ex)
    for k in "ABCD" for t, ty, ex in ALL_DOCS[k]}))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="R99-ADMIN-" + STAMP, role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    for k in "ABCD":
        if s.scalar(select(Project).where(Project.legacy_id == IDS[k])) is None:
            s.add(Project(legacy_id=IDS[k],
                          doc={"id": IDS[k], "name": f"Run 99 fixture {k}",
                               "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "R99-PM-" + STAMP, "role": "Participant",
                "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
PM_TOKEN = created["access_token"]
for k in "ABCD":
    post({"action": "adminmemberadd", "session_token": admin, "id": IDS[k],
          "participant_id": created["participant_id"], "project_role": "PM"})
    for tag, _ty, _ex in ALL_DOCS[k]:
        r = post({"action": "projectupload", "session_token": PM, "id": IDS[k], "period": 1,
                  "period_end": END,
                  "documents": [{"filename": tag + ".pdf", "mimeType": "application/pdf",
                                 "dataBase64": b64(raw(tag))}]})
        assert r.get("ok") is True, str(r)[:300]

print("=" * 96)
print("STEP 1  documents uploaded for A B C D; Process all pressed for B C D only")
print("=" * 96)
for k in "BCD":
    r = post({"action": "projectcomputeall", "session_token": PM, "id": IDS[k]})
    print(f"  {k}  projectcomputeall ok={r.get('ok')}  {json.dumps(r)[:240]}")
for k in "CD":
    r = post({"action": "projectcategoryapply", "session_token": PM, "id": IDS[k], "period": 1})
    print(f"  {k}  projectcategoryapply ok={r.get('ok')} readings={len(r.get('readings') or [])} "
          f"servedBy={r.get('servedBy')}")

print()
print("=" * 96)
print("STEP 2  WHAT THE COMPUTE ROUTE STORED  (computed_results row, read direct)")
print("=" * 96)
with Session() as s:
    for k in "ABCD":
        p = s.scalar(select(Project).where(Project.legacy_id == IDS[k]))
        rows = s.scalars(select(ComputedResult).where(
            ComputedResult.project_id == p.id,
            ComputedResult.superseded_by.is_(None))).all()
        if not rows:
            print(f"  {k}  NO computed_results row")
            continue
        for r in rows:
            cs = r.category_statuses or {}
            print(f"  {k}  period={r.period} stored project_status={r.project_status!r} "
                  f"modules={len(r.module_results or [])}")
            print(f"       category_statuses = "
                  + json.dumps({c: (v or {}).get('status') for c, v in cs.items()}))

print()
print("=" * 96)
print("STEP 3  WHAT THE PORTFOLIO ROUTE SERVES  (a_list / a_listslim -> storedResult)")
print("=" * 96)
def get(action, **kw):
    q = "&".join(f"{k}={v}" for k, v in kw.items())
    r = client.get(f"/exec?action={action}&session_token={PM}" + ("&" + q if q else ""))
    return r.json()

for action in ("list", "listslim"):
    out = get(action)
    ps = out.get("projects") or []
    for p in ps:
        if not str(p.get("id", "")).startswith("PRJ-R99-"):
            continue
        sr = p.get("storedResult")
        print(f"  {action:9s} {p['id'][-14:]:14s} doc.status={p.get('status')!r:14s} "
              f"slim={p.get('slim')!r} storedResult.project_status="
              f"{(sr or {}).get('project_status')!r} period={(sr or {}).get('period')!r}")
        if sr and sr.get("category_statuses") is not None:
            print("            cats=" + json.dumps(
                {c: (v or {}).get("status") for c, v in (sr.get("category_statuses") or {}).items()}))

print()
print("=" * 96)
print("STEP 4  WHAT THE DETAIL RESULT ROUTE SERVES  (projectresults -> _result_view)")
print("=" * 96)
for k in "ABCD":
    r = post({"action": "projectresults", "session_token": PM, "id": IDS[k], "period": 1})
    if not r.get("ok"):
        print(f"  {k}  projectresults not ok: {json.dumps(r)[:200]}")
        continue
    res = r.get("result") or {}
    basis = res.get("project_status_basis") or {}
    print(f"  {k}  project_status={res.get('project_status')!r} "
          f"basis.status={basis.get('status')!r} fused_band={basis.get('fused_band')!r} "
          f"official={basis.get('official')!r}")
    print(f"       required_assessed={basis.get('required_assessed')} "
          f"required_missing={basis.get('required_missing')}")
    for d in (basis.get("required_missing_detail") or [])[:6]:
        print(f"         {d['category']}: {d['state']} :: {str(d['missing'])[:110]}")

print()
print("=" * 96)
print("STEP 5  spec_projection readings, per category, for C and D")
print("=" * 96)
from app import spec_projection  # noqa: E402
with Session() as s:
    for k in "ABCD":
        p = s.scalar(select(Project).where(Project.legacy_id == IDS[k]))
        pr = spec_projection.projection(s, p.id, 1)
        print(f"  {k}  called={pr['specification_categories_called']} "
              f"count={pr['specification_reading_count']} status={pr['project_status']!r}")
        for c, v in (pr["category_statuses"] or {}).items():
            print(f"       {c}: status={(v or {}).get('status')!r} "
                  f"state={(v or {}).get('state')!r} reason={str((v or {}).get('reason'))[:90]!r}")

print()
print("TOKENS " + json.dumps({"pm": PM_TOKEN, "ids": IDS}))
