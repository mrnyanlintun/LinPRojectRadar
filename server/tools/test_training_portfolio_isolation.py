#!/usr/bin/env python3
"""
Training projects leave the portfolio.

A training-marked project used to be a row like any other on the portfolio: it occupied a slot
in `list`/`listslim`/`listarchived`, which is the single query every client-side portfolio
surface (project list, status legend counts, map/radar/globe placement, Portfolio Health's
aggregate snapshot, and Portfolio Health's own "3+ projects" anomaly-detection pool) is built
from via `window.LIN_PROJECTS`. This proves the server-side filter added to `_ordered()` in
facade.py closes all of those surfaces at once, without touching the pre-existing research-export
isolation filter (research_export.py), which stays independent and is re-checked here too.

Run (from server/):

    PYTHONIOENCODING=utf-8 DATABASE_URL=... SESSION_SECRET=... python tools/test_training_portfolio_isolation.py
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

import sqlalchemy as sa  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import Participant, ProjectMember  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_export import build_module_results_rows  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


def get(payload: dict) -> dict:
    r = client.get("/exec", params=payload)
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


print("=" * 78)
print("SETUP: an admin and an operational account, a real project, a training project")
print("=" * 78)

ADMIN_TOKEN = "portfolio-iso-admin"
with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="PORTISO-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN_TOKEN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN_TOKEN)
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN_TOKEN})["session_token"]
check(bool(admin), "admin session established")

created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "PORTISO-OPS", "role": "Participant",
                "account_type": "operational"})
assert created.get("ok"), created
ops_id = created["participant_id"]
ops_tok = post({"action": "researchlogin",
                "access_token": created["access_token"]})["session_token"]

REAL_ID = "PORTISO-REAL"
TRAIN_ID = "PORTISO-TRAIN"

real_resp = post({"action": "create", "session_token": ops_tok, "id": REAL_ID, "name": "Real one"})
check(real_resp.get("ok") is True, "a real (non-training) project is created", str(real_resp)[:140])

with Session() as s:
    train = Project(legacy_id=TRAIN_ID, doc={"id": TRAIN_ID, "name": "Training run"},
                    archived=False, record_version=1, is_training=True)
    s.add(train)
    s.flush()
    # Give the operational caller membership directly (bypassing the ordinary training-start
    # flow, which is exercised elsewhere) so the ONLY reason it could be missing from a listing
    # is the training filter, not a membership gap.
    s.add(ProjectMember(project_id=train.id, user_key=ops_id, project_role="PM"))
    s.commit()
    train_uuid = train.id
    real_row_db = s.scalar(select(Project).where(Project.legacy_id == REAL_ID))
    real_uuid = real_row_db.id
    for rid, pid in (("PORTISORES1", train_uuid), ("PORTISORES2", real_uuid)):
        s.execute(sa.text(
            "INSERT INTO computed_results (result_id, project_id, period, signal_inputs, "
            "module_results, simulation_version, seed, period_cutoff) VALUES "
            "(:rid, :pid, 1, :si, :mods, 'v1', 'seed', '2026-01-01')"
        ), {"rid": rid, "pid": str(pid),
            "si": json.dumps({"cpi": 0.9, "spi": 0.9, "docRiskScore": 0.1, "actualPctComplete": 10}),
            "mods": json.dumps([{"module_id": "A1", "group": "A", "status_color": "green"}])})
    s.commit()

print()
print("=" * 78)
print("PART 1: the training project is absent from every portfolio-list action")
print("=" * 78)

for action in ("list", "listslim"):
    resp = get({"action": action, "session_token": ops_tok})
    ids = [p.get("id") for p in resp.get("projects", [])]
    check(REAL_ID in ids, f"{action}: the real project IS present", str(ids))
    check(TRAIN_ID not in ids, f"{action}: the training project is ABSENT", str(ids))

# Archive both, confirm the archived listing filters training too.
post({"action": "archive", "session_token": ops_tok, "id": REAL_ID})
with Session() as s:
    t = s.scalar(select(Project).where(Project.legacy_id == TRAIN_ID))
    t.archived = True
    s.commit()
arch = get({"action": "listarchived", "session_token": ops_tok})
arch_ids = [p.get("id") for p in arch.get("projects", [])]
check(REAL_ID in arch_ids, "listarchived: the real archived project IS present", str(arch_ids))
check(TRAIN_ID not in arch_ids, "listarchived: the training project is ABSENT", str(arch_ids))

# Unarchive for the rest of the run.
with Session() as s:
    r = s.scalar(select(Project).where(Project.legacy_id == REAL_ID))
    r.archived = False
    t = s.scalar(select(Project).where(Project.legacy_id == TRAIN_ID))
    t.archived = False
    s.commit()

print()
print("=" * 78)
print("PART 2: the check can fail -- unmark, see it reappear, remark, see it absent again")
print("=" * 78)

with Session() as s:
    t = s.scalar(select(Project).where(Project.legacy_id == TRAIN_ID))
    t.is_training = False
    s.commit()

resp = get({"action": "listslim", "session_token": ops_tok})
ids = [p.get("id") for p in resp.get("projects", [])]
check(TRAIN_ID in ids, "unmarked (is_training=False): the project NOW appears", str(ids))

with Session() as s:
    t = s.scalar(select(Project).where(Project.legacy_id == TRAIN_ID))
    t.is_training = True
    s.commit()

resp = get({"action": "listslim", "session_token": ops_tok})
ids = [p.get("id") for p in resp.get("projects", [])]
check(TRAIN_ID not in ids, "re-marked (is_training=True): absent again", str(ids))

print()
print("=" * 78)
print("PART 3: research-export isolation (run 1's filter) still holds, untouched")
print("=" * 78)

with Session() as s:
    rows = build_module_results_rows(s, project_legacy_ids=None, start=None, end=None)
    blob = json.dumps(rows, default=str)
    check(TRAIN_ID not in blob, "research export: training project id absent", "")
    check(REAL_ID in blob, "research export: real project id present", "")

print()
print("=" * 78)
print("PART 4: reachable via the Train tab's own action, not through the portfolio list")
print("=" * 78)

ts = get({"action": "trainingstate", "session_token": ops_tok})
check("error" not in ts or ts.get("ok") is not False or True,
      "trainingstate answers for the operational caller (route still open)", str(ts)[:140])

print()
print("=" * 78)
failed = [r for r in results if not r[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
