import json, sys, pathlib
HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools")
sys.path.insert(0, str(HERE.parent))
import logging; logging.disable(logging.INFO)
from fastapi.testclient import TestClient
from sqlalchemy import select
import app.main as main
from app.research_models import ComputedResult, Participant
from app.models import Project
client = TestClient(main.app, raise_server_exceptions=False)
S = main.SessionFactory
def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type":"text/plain"})
    return r.json()
PM = sys.argv[1]
out = post({"action":"list","session_token":PM})
print("list keys:", list(out.keys())[:12], "ok=", out.get("ok"), str(out)[:300])
with S() as s:
    for p in s.scalars(select(Project)).all():
        if not p.legacy_id.startswith("PRJ-R99-"): continue
        r = s.scalar(select(ComputedResult).where(ComputedResult.project_id==p.id,
                                                  ComputedResult.superseded_by.is_(None)))
        if not r: print(p.legacy_id, "no row"); continue
        print("==", p.legacy_id, "modules:", [(m.get("module_id"), m.get("status"), m.get("state")) for m in (r.module_results or [])])
        print("   abstained:", [(a.get("module_id"), str(a.get("reason"))[:70]) for a in (r.abstained or [])][:40])
        print("   unported:", len(r.unported or []), [u.get("module_id") for u in (r.unported or [])][:40])
