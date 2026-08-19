#!/usr/bin/env python3
"""RUN 41 section 5 - reproduce S2 on the CURRENT (pre-fix) v25 schema.

Builds a genuine final-locked decision through the REAL application routes, then attempts raw
SQL mutation of every substantive final-response field. Captures which mutations SUCCEED.
"""
from __future__ import annotations
import json, os, sys
sys.path.insert(0, __file__.rsplit("tools", 1)[0])
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from sqlalchemy import select, text
import app.main as main
from app.research_models import Decision
import run41_flow as r41_flow

client = TestClient(main.app, raise_server_exceptions=False)
ctx = r41_flow.build(main, client, "S2R")
steps = r41_flow.run_to_final_lock(ctx)
Session = ctx["Session"]

print("=" * 78); print("RUN 41 section 5 - S2 PRE-FIX REPRODUCTION"); print("=" * 78)
print("flow:")
for k, v in steps.items():
    print(f"   {k:12s} ok={v.get('ok')}  stage={v.get('current_stage')}")
did = r41_flow.decision_id(ctx)
with Session() as s:
    d = s.get(Decision, did)
    print(f"\ndecision_id={did}")
    print(f"final_submitted_at (the final lock) = {d.final_submitted_at!r}")
    assert d.final_submitted_at is not None, "PRECONDITION FAILED: decision is not final-locked"
    before = {c: getattr(d, c) for c in
              ["final_action", "disposition", "rationale", "final_confidence",
               "escalation_level", "owner_role", "authority_role", "resource_constraint",
               "evidence_items", "reason_code", "deadline", "residual_risk"]}

MUTATIONS = [
    ("final_action",        "'TAMPERED ACTION'"),
    ("final_confidence",    "1"),
    ("rationale",           "'TAMPERED RATIONALE'"),
    ("disposition",         "'reject'"),
    ("escalation_level",    "'TAMPERED'"),
    ("owner_role",          "'TAMPERED'"),
    ("authority_role",      "'TAMPERED'"),
    ("resource_constraint", "'TAMPERED'"),
    ("evidence_items",      "'[\"TAMPERED\"]'"),
    ("reason_code",         "'TAMPERED'"),
    ("deadline",            "'1999-01-01'"),
    ("residual_risk",       "'TAMPERED'"),
    ("final_submitted_at",  "NULL"),
]
out = {"decision_id": did, "flow_ok": all(v.get("ok") for v in steps.values()), "mutations": {}}
print("\nraw SQL mutation attempts AFTER final lock:")
for col, val in MUTATIONS:
    with Session() as s:
        try:
            s.execute(text(f"UPDATE decisions SET {col} = {val} WHERE decision_id = :d"),
                      {"d": did})
            s.commit()
            with Session() as s2:
                now = getattr(s2.get(Decision, did), col)
            succeeded = True; err = None
        except Exception as e:
            succeeded = False; err = type(e).__name__ + ": " + str(e).split("\n")[0][:110]
            now = None
    out["mutations"][col] = {"raw_sql_mutation_succeeded": succeeded,
                             "value_after": str(now)[:60], "error": err}
    print(f"   {col:22s} succeeded={succeeded}  now={str(now)[:40]!r}"
          + (f"  err={err}" if err else ""))

n_ok = sum(1 for v in out["mutations"].values() if v["raw_sql_mutation_succeeded"])
out["successful_raw_mutations"] = n_ok
out["total_attempted"] = len(MUTATIONS)
print("\n" + "=" * 78)
print(f"S2 PRE-FIX: raw SQL mutations that SUCCEEDED after final lock = {n_ok}/{len(MUTATIONS)}")
print("=" * 78)
json.dump(out, open(sys.argv[1], "w"), indent=2)
