"""
RUN 144 RULING 3, PROOF 5 (and the server half of proof 4): THE AGE IS ON EVERY SURFACE.

Runs against a THROWAWAY SQLite file only. Production Postgres is never contacted.

    export DATABASE_URL=sqlite:///<abs path in scratch>
    python -m alembic upgrade head
    PYTHONPATH=. python tools/test_run144_ruling3_surfaces.py

The owner ruled the look-back UNBOUNDED and said so in terms: "the age carries the weight
instead". That makes `carried_from_age` the entire safeguard, so this file checks it is COMPLETE
-- present, correct and stated as a DISTANCE rather than left to be subtracted -- on the server
surfaces. The browser half (the card, the ledger head, contrast, themes, no-threshold) is
`test_run144_ruling3_browser.py`; the two together are the whole of ruling 3's proof.

NO CAP IS ASSERTED HERE AND NONE EXISTS. An age of 600 is exercised deliberately: it must be
carried, exported and printed exactly like an age of 1, with no clamp, no warning and no
different words.
"""
from __future__ import annotations

import datetime
import os
import sys

assert os.environ.get("DATABASE_URL", "").startswith("sqlite:"), \
    "refusing to run against anything but a throwaway SQLite file"

from sqlalchemy.orm import Session                                    # noqa: E402

from app.db import build_engine                                       # noqa: E402
from app.settings import load_settings                                # noqa: E402

engine = build_engine(load_settings())
from app.decision_brief import _limitations                           # noqa: E402
from app.models import Project                                        # noqa: E402
from app.research_models import ComputedResult                        # noqa: E402
from app.research_export import (MODULE_RESULT_COLUMNS,               # noqa: E402
                                 build_module_results_rows)
from app.simulation.carry_forward import CARRIED_KEYS, select_carried  # noqa: E402
from app.simulation.compute import compute_project                    # noqa: E402
from app.simulation.models import SIMULATION_VERSION                  # noqa: E402

FAILS: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + detail) if detail else ""))
    if not ok:
        FAILS.append(name)


# ---------------------------------------------------------- 1. THE AGE IS A DECLARED FIELD
check("`carried_from_age` is one of the keys the carry layer declares it writes",
      "carried_from_age" in CARRIED_KEYS, str(CARRIED_KEYS))
check("proof 5: the export declares a flat `carried_from_age` column",
      "carried_from_age" in MODULE_RESULT_COLUMNS)

# ------------------------------------- 2. THE AGE IS THE DISTANCE, AND IT IS NOT CAPPED
# Eight stored periods of history in which only the OLDEST holds a banded reading for A2.1.
# The distance a reviewer needs is 8, not "P1", and the look-back must reach it with no cap.
oldest = {"period": "P1", "modules": [
    {"module_id": "A2.1", "category": "A2", "status_color": "Amber",
     "evidence_metric": "P1's own sentence."}]}
gap = [{"period": f"P{n}", "modules": []} for n in range(8, 1, -1)]   # P8..P2, newest first
res = compute_project({}, "run144r3", "P9", datetime.date(2026, 6, 30),
                      project_id="PRJ-R144R3", prior_readings=gap + [oldest])
carried_row = next((m for m in res["modules"]
                    if m["module_id"] == "A2.1" and m.get("carried")), None)
check("a reading eight stored periods back still carries -- there is no cap",
      carried_row is not None)
if carried_row:
    check("and the row states the DISTANCE, not just the source period",
          carried_row.get("carried_from_age") == 8,
          f"age {carried_row.get('carried_from_age')}, from "
          f"{carried_row.get('carried_from_period')}")
    check("it names the period as well, so the two together are unambiguous",
          carried_row.get("carried_from_period") == "P1")
check("the caller surfaces the OLDEST age on the project basis",
      res["project_status_basis"].get("carried_oldest_age") == 8,
      str(res["project_status_basis"].get("carried_oldest_age")))

# A deliberately absurd age. The ruling forbids a cap; this is how "no cap" stays testable.
# The prior list is built oldest-last, exactly as the caller orders it: newest first.
FAR_HISTORY = ([{"period": f"P{n}", "modules": []} for n in range(600, 1, -1)]
               + [{"period": "P1", "modules": [
                   {"module_id": "A2.1", "category": "A2", "status_color": "Red",
                    "evidence_metric": "a very old sentence."}]}])
far = select_carried(
    [{"module_id": "A2.1", "abstention_reason_code": "canonical_structure_absent",
      "reason": "nothing this period"}],
    FAR_HISTORY)
far_row = next((r for r in far if r["module_id"] == "A2.1"), None)
check("no cap: a reading 600 stored periods back is still carried",
      far_row is not None)
if far_row:
    check("no cap: the age is reported as 600, unclamped and unrounded",
          far_row.get("carried_from_age") == 600, str(far_row.get("carried_from_age")))
    check("no cap: its sentence gains no warning, no threshold word and no judgment",
          not any(w in (far_row.get("evidence_metric") or "").lower()
                  for w in ("stale", "too old", "expired", "warning", "exceeds", "beyond")),
          (far_row.get("evidence_metric") or "")[:70])

# ----------------------------------------------------------- 3. PROOF 5: IT IS IN THE EXPORT
with Session(engine) as s:
    proj = Project(legacy_id="PRJ-R144-AGE", doc={"name": "run 144 ruling 3 export fixture"})
    s.add(proj)
    s.flush()
    s.add(ComputedResult(
        project_id=proj.id, period=9, computed_at=datetime.datetime(2026, 6, 30),
        simulation_version=SIMULATION_VERSION, seed=1,
        period_cutoff=datetime.date(2026, 6, 30), project_status="Amber",
        module_results=[
            {"module_id": "A2.1", "group": "A", "status_color": "Amber",
             "method_class": "pert_network_criticality",
             "evidence_metric": "Carried from P1: ... P1's own sentence.",
             "carried": True, "carried_from_period": "P1", "carried_from_age": 8,
             "carried_evidence": "P1's own sentence.",
             "carried_reason": "Awaiting the project's activity network."},
            {"module_id": "A2.7", "group": "A", "status_color": "Amber",
             "method_class": "milestone_trend_analysis",
             "evidence_metric": "this period's own reading"},
            {"module_id": "A3.3", "group": "A", "status_color": "Red",
             "method_class": "cost_risk",
             "evidence_metric": "Carried from P8: ... P8's own sentence.",
             "carried": True, "carried_from_period": "P8", "carried_from_age": 1,
             "carried_evidence": "P8's own sentence.",
             "carried_reason": "Awaiting a governed cost risk record."},
        ],
        abstained=[],
    ))
    s.commit()
    rows = [r for r in build_module_results_rows(s, None, None, None)
            if r.get("project") == "PRJ-R144-AGE"]

carried_rows = [r for r in rows if r.get("carried") == 1]
print(f"\nexported rows: {len(rows)}   carried: {len(carried_rows)}")
for r in carried_rows:
    print(f"    {r['computation']!r:52} carried_from_period={r['carried_from_period']!r} "
          f"carried_from_age={r['carried_from_age']!r}")
check("proof 5: EVERY carried row in the export states its age",
      len(carried_rows) == 2 and all(isinstance(r["carried_from_age"], int)
                                     and r["carried_from_age"] > 0 for r in carried_rows),
      str([r["carried_from_age"] for r in carried_rows]))
check("proof 5: the ages are the stored ones, not recomputed or defaulted",
      sorted(r["carried_from_age"] for r in carried_rows) == [1, 8])
check("proof 5: a CURRENT row's age column is empty, not zero -- nothing is invented",
      all(r["carried_from_age"] == "" for r in rows if r.get("carried") != 1),
      str({r["carried_from_age"] for r in rows if r.get("carried") != 1}))
check("proof 5: the age travels beside the named period, so a reader needs no subtraction",
      all(r["carried_from_period"] for r in carried_rows))
check("proof 5: every declared column is present on every row",
      all(set(r) == set(MODULE_RESULT_COLUMNS) for r in rows))

# ------------------------------------------------- 4. THE DECISION BRIEF STATES THE DISTANCE
MODS = [
    {"module_id": "A2.1", "method_class": "pert_network_criticality",
     "status_color": "Amber", "evidence_metric": "Carried from P1: ...",
     "carried": True, "carried_from_period": "P1", "carried_from_age": 8},
    {"module_id": "A3.3", "method_class": "cost_risk", "status_color": "Red",
     "evidence_metric": "Carried from P8: ...",
     "carried": True, "carried_from_period": "P8", "carried_from_age": 1},
]
lims = _limitations({"carried_count": 2, "carried_of_banded": 2, "carried_oldest_age": 8},
                    {}, MODS)
text = " ".join(lims)
print("\ndecision brief carried limitation:")
for line in lims:
    print("    " + line)
check("the brief states the eight-period distance",
      "8 stored periods back" in text, "not found")
check("the brief's plural agrees at an age of one -- 'stored period', not 'stored periods'",
      "1 stored period back" in text and "1 stored periods back" not in text)
check("the brief attaches no judgment to either age",
      not any(w in text.lower() for w in ("stale", "too old", "expired", "exceeds")),
      "a judgment word is present")

print()
if FAILS:
    print(f"{len(FAILS)} FAILED: {FAILS}")
    sys.exit(1)
print("ALL CHECKS PASSED")
