"""
RUN 143 PART 2 -- PROOF 12: the exports carry the distinction, and do not double-count.

Runs against a THROWAWAY SQLite file only. Production Postgres is never contacted.

    export DATABASE_URL=sqlite:///<abs path in scratch>
    python -m alembic upgrade head
    PYTHONPATH=. python tools/test_run143p2_export.py
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
from app.models import Project                                        # noqa: E402
from app.research_models import ComputedResult                        # noqa: E402
from app.research_export import (MODULE_RESULT_COLUMNS,               # noqa: E402
                                 build_module_results_rows)

FAILS: list[str] = []


def check(name, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + detail) if detail else ""))
    if not ok:
        FAILS.append(name)


for col in ("carried", "carried_from_period", "carried_from_age", "record_kind"):
    check(f"the flat column {col!r} exists", col in MODULE_RESULT_COLUMNS)

with Session(engine) as s:
    proj = Project(legacy_id="PRJ-CF-EXPORT", doc={"name": "carry export fixture"})
    s.add(proj)
    s.flush()
    # One stored row shaped exactly as compute_project now stores one: the carried reading in
    # `module_results`, and the period's own abstention STILL in `abstained` (rule 6).
    s.add(ComputedResult(
        project_id=proj.id, period=3, computed_at=datetime.datetime(2026, 6, 30),
        simulation_version="sim-2026.09-v71", seed=1, period_cutoff=datetime.date(2026, 6, 30),
        project_status="Amber",
        module_results=[
            {"module_id": "A2.1", "group": "A", "status_color": "Amber",
             "evidence_metric": "Carried from P1: ... P1's own sentence.",
             "carried": True, "carried_from_period": "P1", "carried_from_age": 2,
             "carried_evidence": "P1's own sentence.",
             "carried_reason": "Awaiting the project's activity network."},
            {"module_id": "A2.7", "group": "A", "status_color": "Green",
             "evidence_metric": "this period's own reading"},
        ],
        abstained=[
            {"module_id": "A2.1", "reason": "Awaiting the project's activity network.",
             "abstention_reason_code": "canonical_structure_absent"},
            {"module_id": "A2.8", "reason": "Awaiting a look ahead schedule."},
        ]))
    s.commit()

    rows = build_module_results_rows(s, None, None, None)
    rows = [r for r in rows if r["project"] == "PRJ-CF-EXPORT"]
    print(f"\n{len(rows)} export rows for the fixture:")
    for r in rows:
        print(f"  {r['record_kind']:<32} band={str(r['status_color']):<7} "
              f"carried={str(r['carried']):<2} from={str(r['carried_from_period']):<4} "
              f"age={r['carried_from_age']}  {r['computation'][:44]}")

    kinds = {r["record_kind"] for r in rows}
    carried_rows = [r for r in rows if r["record_kind"] == "carried_reading"]
    check("proof 12: a carried reading is emitted as its own record kind",
          len(carried_rows) == 1, str(kinds))
    if carried_rows:
        c = carried_rows[0]
        check("proof 12: the flat carried column is set", c["carried"] == 1)
        check("proof 12: the flat column NAMES the source period",
              c["carried_from_period"] == "P1", str(c["carried_from_period"]))
        check("proof 12: the age travels in a flat column", c["carried_from_age"] == 2)
        check("proof 12: it still carries its band, because it votes with it",
              c["status_color"] == "Amber")

    cur = [r for r in rows if r["record_kind"] == "reading"]
    check("proof 12: a CURRENT reading is distinguishable in the flat columns",
          len(cur) == 1 and cur[0]["carried"] == "" and cur[0]["carried_from_period"] == "",
          str([(r["carried"], r["record_kind"]) for r in cur]))

    dbl = [r for r in rows if r["record_kind"] == "abstention_superseded_by_carry"]
    check("the double-count row is labelled, not deleted", len(dbl) == 1,
          f"{len(dbl)} rows; reason kept: {bool(dbl and dbl[0]['evidence_metric'])}")
    check("the abstention's own sentence is still in the file",
          bool(dbl and dbl[0]["evidence_metric"]))

    one_per = [r for r in rows if r["record_kind"] in ("reading", "carried_reading")]
    ids = [r["computation"] for r in one_per]
    check("ONE ROW PER MODULE-PERIOD is a filter, not a guess",
          len(ids) == len(set(ids)) == 2, str(ids))

    plain_abst = [r for r in rows if r["record_kind"] == "abstention"]
    check("an abstention that carried nothing keeps the plain kind", len(plain_abst) == 1)

    check("every row carries every declared column",
          all(set(r) == set(MODULE_RESULT_COLUMNS) for r in rows))

print("\n" + ("ALL CHECKS PASSED" if not FAILS else f"{len(FAILS)} FAILED: {FAILS}"))
sys.exit(1 if FAILS else 0)
