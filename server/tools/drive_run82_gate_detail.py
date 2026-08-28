#!/usr/bin/env python3
"""
RUN 82, PART B. WHAT EACH GATED MODULE ACTUALLY RETURNS, ONCE THE CATEGORY-9 GATE IS OPEN.

Run 80's harness counts gate refusals and buckets everything else as "abstained for another
reason". That bucket is where the answer to the owner's third question lives, and a count cannot
name it. This reads the SIGNAL INPUTS Run 80's harness already stored on its project, re-runs
every gated module in service on them, and prints the WHOLE result row -- state, value,
insufficient_data, abstention code and note -- so "blocked by something else" is a named thing.

It stores nothing and computes nothing new. Run drive_run80_gate.py first.
"""
from __future__ import annotations
import datetime as dt, json, logging, os, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
logging.disable(logging.INFO)

from sqlalchemy import select                                        # noqa: E402
import app.main as main                                              # noqa: E402
from app.models import Project                                       # noqa: E402
from app.research_models import ComputedResult                        # noqa: E402
from app.simulation.registry import run_module, service_index      # noqa: E402
from app.simulation.qualification_boundary import gated_module_ids   # noqa: E402

Session = main.SessionFactory
GATED = sorted(set(gated_module_ids()) & set(service_index()))
print(f"DATABASE_URL={os.environ.get('DATABASE_URL')}")
print(f"gated modules in service: {len(GATED)} -> {GATED}")

with Session() as s:
    proj = s.scalars(select(Project).where(Project.legacy_id.like("PRJ-R80-%"))
                     .order_by(Project.legacy_id.desc())).first()
    assert proj is not None, "run drive_run80_gate.py first"
    cr = s.scalars(select(ComputedResult)
                   .where(ComputedResult.project_id == proj.id, ComputedResult.period == 1)
                   .order_by(ComputedResult.result_id.desc())).first()
    si = dict(cr.signal_inputs or {})
    end = dt.date(2026, 3, 31)

print(f"project={proj.legacy_id} period=1 period_end={end}")
print(f"evidenceQualification present in stored signal_inputs: "
      f"{'evidenceQualification' in si}")
print(f"  value: {json.dumps(si.get('evidenceQualification'), default=str)}")
print("=" * 100)
if isinstance(end, str):
    end = dt.date.fromisoformat(end)
produced = []
for mid in GATED:
    try:
        r = run_module(mid, si, lambda: 0.5, end)
    except Exception as e:                                            # noqa: BLE001
        print(f"{mid:<7} RAISED {type(e).__name__}: {e}")
        continue
    note = str(r.get("evidence_metric") or r.get("note") or r.get("reason") or "")
    ok = (not r.get("insufficient_data")) and r.get("value") is not None
    if ok:
        produced.append(mid)
    print(f"{mid:<7} value={r.get('value')!r:<22} insufficient_data={bool(r.get('insufficient_data'))!s:<6} "
          f"band={r.get('band')!r}")
    print(f"        code={r.get('abstention_reason_code')!r}")
    print(f"        note={note[:300]}")
print("=" * 100)
print(f"gated modules PRODUCING A VALUE with the gate open: {len(produced)}/{len(GATED)} "
      f"-> {produced}")
