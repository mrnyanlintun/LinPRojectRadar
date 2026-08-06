#!/usr/bin/env python3
"""
The cross-period series: assembled from the results already stored, aligned to the period being
computed, and never from a later one.

WHAT THIS SUITE EXISTS TO PROTECT. A series across reporting periods is exactly the shape that
caused P1: a portfolio vector selected by `max(period)` with no alignment to the period being
computed, so a stored period-1 result changed when another project reached period 2. Every check
below is written against that one failure mode. The acceptance condition is stated as a check
rather than as a comment: recomputing period 1 after periods 2, 3 and 4 exist must reproduce the
period-1 result byte for byte.

WHAT IS COMPARED FOR "BYTE-IDENTICAL". The analytical content of the stored row -- signal_inputs,
module_results, category_statuses, project_status, portfolio_snapshot, period_cutoff,
simulation_version and seed -- serialised with `json.dumps(sort_keys=True)` and compared as bytes.
The row's identity and clock columns (result_id, computed_at) are excluded BY NAME and for a
stated reason: a recompute is a new append-only row and is required to have a new id, so
including them would make the check impossible to pass for a reason that has nothing to do with
period alignment. Everything a reader is ever shown is inside the compared payload.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_period_series.py
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.extraction_client import StubExtractor  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import ComputedResult, Participant  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
PASSED = 0
FAILED = 0


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


# The row's analytical content, canonicalised. Identity and clock columns are excluded by name.
_COMPARED = ("period", "signal_inputs", "module_results", "category_statuses", "project_status",
             "portfolio_snapshot", "simulation_version", "seed", "period_cutoff",
             "source_documents")


def payload_bytes(project_legacy_id: str, period: int) -> bytes:
    with Session() as s:
        pid = s.scalar(select(Project.id).where(Project.legacy_id == project_legacy_id))
        row = s.scalar(select(ComputedResult).where(
            ComputedResult.project_id == pid,
            ComputedResult.period == period,
            ComputedResult.superseded_by.is_(None)))
        assert row is not None, f"no live result for {project_legacy_id} period {period}"
        out = {}
        for k in _COMPARED:
            v = getattr(row, k)
            out[k] = str(v) if k == "period_cutoff" else v
        return json.dumps(out, sort_keys=True, default=str).encode()


# --------------------------------------------------------------- fixture

ADMIN = "series-admin-token"
A = "PRJ-SERIESA1"
B = "PRJ-SERIESB1"

# Four periods of a monthly report, EV/AC chosen so cpi and spi differ every period and the
# series is not flat. A flat series would let a broken assembly pass by coincidence.
PERIODS = {
    1: {"earned_value": 4_000_000, "actual_cost": 4_200_000, "planned_value": 4_100_000,
        "budget_at_completion": 10_000_000, "actual_percent_complete": 40.0,
        "planned_percent_complete": 41.0, "report_date": "2026-05-31",
        "document_date": "2026-05-31"},
    2: {"earned_value": 5_000_000, "actual_cost": 4_900_000, "planned_value": 5_100_000,
        "budget_at_completion": 10_000_000, "actual_percent_complete": 50.0,
        "planned_percent_complete": 51.0, "report_date": "2026-06-30",
        "document_date": "2026-06-30"},
    3: {"earned_value": 6_000_000, "actual_cost": 5_600_000, "planned_value": 6_050_000,
        "budget_at_completion": 10_000_000, "actual_percent_complete": 60.0,
        "planned_percent_complete": 61.0, "report_date": "2026-07-31",
        "document_date": "2026-07-31"},
    4: {"earned_value": 6_800_000, "actual_cost": 6_500_000, "planned_value": 7_000_000,
        "budget_at_completion": 10_000_000, "actual_percent_complete": 68.0,
        "planned_percent_complete": 70.0, "report_date": "2026-08-31",
        "document_date": "2026-08-31"},
}
# A second project, so the portfolio has two vectors with signal data and compute_portfolio does
# not stop at its own "portfolio too small" guard before reaching the trajectory block.
OTHER = {"earned_value": 3_000_000, "actual_cost": 3_050_000, "planned_value": 3_020_000,
         "budget_at_completion": 9_000_000, "actual_percent_complete": 33.0,
         "planned_percent_complete": 34.0, "report_date": "2026-05-20",
         "document_date": "2026-05-20"}


def doc_bytes(tag: str) -> bytes:
    return f"%PDF-1.4 PERIOD SERIES {tag}\n".encode()


RECORDED = {hashlib.sha256(doc_bytes(f"A{p}")).hexdigest(): ("monthly_report", f)
            for p, f in PERIODS.items()}
RECORDED[hashlib.sha256(doc_bytes("B1")).hexdigest()] = ("monthly_report", OTHER)
set_extractor_override(StubExtractor(RECORDED))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="SERIES-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    for legacy, name in ((A, "Series A"), (B, "Series B")):
        if s.scalar(select(Project).where(Project.legacy_id == legacy)) is None:
            s.add(Project(legacy_id=legacy, doc={"id": legacy, "name": name, "signals": {},
                                                 "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "SERIES-PM", "role": "Participant",
                "account_type": "operational"})
pm_id = created["participant_id"]
pm = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
for legacy in (A, B):
    post({"action": "adminmemberadd", "session_token": admin, "id": legacy,
          "participant_id": pm_id, "project_role": "PM"})


def upload_and_compute(legacy: str, period: int, tag: str) -> dict:
    up = post({"action": "projectupload", "session_token": pm, "id": legacy, "period": period,
               "documents": [{"filename": f"{tag}.pdf", "mimeType": "application/pdf",
                              "dataBase64": b64(doc_bytes(tag))}]})
    assert up.get("ok") is True, str(up)[:200]
    post({"action": "projectcompute", "session_token": pm, "id": legacy, "period": period})
    return post({"action": "projectresults", "session_token": pm,
                 "id": legacy, "period": period})["result"]


# The second project first, so every period of A is computed against a portfolio of two.
upload_and_compute(B, 1, "B1")

print("=" * 78)
print("1. A single period is not a series: everything that needs one abstains")
print("=" * 78)

r1 = upload_and_compute(A, 1, "A1")
si1 = r1["signal_inputs"]
p1_original = payload_bytes(A, 1)

check(si1.get("cpiHistory") is None and si1.get("spiHistory") is None,
      "period 1 is given NO cpi or spi series: there is no earlier period",
      str(si1.get("cpiHistory")))
mods1 = {m["module_id"] for m in r1["module_results"]}
for mid, name in (("A1.2", "CUSUM"), ("A1.4", "Kalman"), ("A1.5", "ARIMA"),
                  ("A1.10", "Regression to Mean")):
    check(mid not in mods1, f"{name} abstains at period 1 rather than inventing a series")
snap1 = r1.get("portfolio_snapshot") or {}
check("cat8_3_trajectory_classifier" not in (snap1.get("results") or {}),
      "the trajectory classifier abstains at period 1: one snapshot is not a trend",
      str(sorted((snap1.get("results") or {}).keys())))
check(snap1.get("ok") is True and "cat8_1_isolation_forest" in (snap1.get("results") or {}),
      "and the rest of the portfolio snapshot still computed, so the abstention is specific",
      str(snap1)[:120])

print()
print("=" * 78)
print("2. A real three-period series computes, and its figures ARE the stored periods")
print("=" * 78)

r2 = upload_and_compute(A, 2, "A2")
r3 = upload_and_compute(A, 3, "A3")
si2, si3 = r2["signal_inputs"], r3["signal_inputs"]

check(si3.get("cpiHistory") == [si1["cpi"], si2["cpi"], si3["cpi"]],
      "cpiHistory at period 3 is exactly the three stored cpi values, in period order",
      str(si3.get("cpiHistory")))
check(si3.get("spiHistory") == [si1["spi"], si2["spi"], si3["spi"]],
      "spiHistory likewise", str(si3.get("spiHistory")))

mods3 = {m["module_id"]: m for m in r3["module_results"]}
for mid, name in (("A1.2", "CUSUM"), ("A1.4", "Kalman"), ("A1.5", "ARIMA"),
                  ("A1.10", "Regression to Mean")):
    check(mid in mods3, f"{name} computes at period 3 on the project's own stored series")
check(mods3.get("A1.2", {}).get("periods") == 3,
      "CUSUM's control chart is drawn over 3 real observations",
      str(mods3.get("A1.2", {}).get("periods")))

snap3 = (r3.get("portfolio_snapshot") or {}).get("results") or {}
traj = snap3.get("cat8_3_trajectory_classifier")
check(traj is not None,
      "the trajectory classifier COMPUTES at period 3, having abstained on every project ever "
      "computed while `history` was a literal None",
      str(sorted(snap3.keys())))
check(isinstance(traj, dict) and traj.get("periods_analyzed") == 3,
      "over 3 periods", str((traj or {}).get("periods_analyzed")))
# Its figure must be reproducible from the stored periods alone: portfolio.py's own expression
# over the last three stored cpi values. Recomputed here from the STORED rows, not from the
# module's output, so a wrong series cannot satisfy it.
cpis = [si1["cpi"], si2["cpi"], si3["cpi"]]
expected_trend = (cpis[-1] - cpis[0]) / len(cpis)
check(isinstance(traj, dict)
      and abs(traj.get("trend", 0) - round(expected_trend * 1000) / 1000) < 1e-9,
      "and its trend is the stored periods' own cpi movement, recomputed independently here",
      f"module {traj.get('trend') if traj else None} vs stored {expected_trend}")

print()
print("=" * 78)
print("3. THE ACCEPTANCE CONDITION: an earlier period is byte-identical after later periods")
print("=" * 78)

r4 = upload_and_compute(A, 4, "A4")
check(len((r4["signal_inputs"].get("cpiHistory") or [])) == 4,
      "period 4 sees a four-point series", str(r4["signal_inputs"].get("cpiHistory")))

post({"action": "adminrecompute", "session_token": admin, "id": A, "period": 1,
      "reason": "period-series alignment check"})
p1_recomputed = payload_bytes(A, 1)
check(p1_recomputed == p1_original,
      "recomputing period 1 with periods 2, 3 and 4 stored is BYTE-IDENTICAL to the original",
      f"{len(p1_original)} vs {len(p1_recomputed)} bytes; first difference at "
      + str(next((i for i in range(min(len(p1_original), len(p1_recomputed)))
                  if p1_original[i] != p1_recomputed[i]), "n/a")))

si1b = post({"action": "projectresults", "session_token": pm, "id": A,
             "period": 1})["result"]["signal_inputs"]
check(si1b.get("cpiHistory") is None and si1b.get("spiHistory") is None,
      "the recomputed period 1 still has no series: the later periods did not reach it",
      str(si1b.get("cpiHistory")))

post({"action": "adminrecompute", "session_token": admin, "id": A, "period": 2,
      "reason": "period-series alignment check"})
si2b = post({"action": "projectresults", "session_token": pm, "id": A,
             "period": 2})["result"]["signal_inputs"]
check(si2b.get("cpiHistory") == [si1["cpi"], si2["cpi"]],
      "recomputing period 2 with periods 3 and 4 stored gives it a TWO-point series, "
      "not a four-point one", str(si2b.get("cpiHistory")))

print()
print("=" * 78)
print("4. No series is assembled from a later period than the one being computed")
print("=" * 78)

# Read the assembly directly, at every period, against the fully populated four-period project.
# The route-level checks above prove the wiring; this proves the property at its source, for
# every period at once, and is the check the leak fault turns red.
from app.documents import _period_history, _period_snapshots  # noqa: E402

with Session() as s:
    proj = s.scalar(select(Project).where(Project.legacy_id == A))
    stored_cpi = {}
    for r in s.scalars(select(ComputedResult).where(
            ComputedResult.project_id == proj.id,
            ComputedResult.superseded_by.is_(None)).order_by(ComputedResult.period)).all():
        stored_cpi[r.period] = (r.signal_inputs or {}).get("cpi")
    check(sorted(stored_cpi) == [1, 2, 3, 4] and len(set(stored_cpi.values())) == 4,
          "the fixture stores four periods with four DIFFERENT cpi values, so a series taken "
          "from the wrong period cannot match by coincidence", str(stored_cpi))
    for period in (1, 2, 3, 4):
        si = {"cpi": stored_cpi[period], "spi": 1.0}
        snaps = _period_snapshots(s, proj, period, si)
        periods_used = [x["period"] for x in snaps]
        check(periods_used == list(range(1, period + 1)),
              f"period {period}: the snapshot series is periods {list(range(1, period + 1))} "
              f"and nothing later", str(periods_used))
        check(all(x["period"] <= period for x in snaps),
              f"period {period}: no snapshot comes from a later period")
        check(snaps[-1]["period"] == period,
              f"period {period}: the series ENDS at the period being computed")
        hist = _period_history(s, proj, period, si)
        used = hist.get("cpiHistory") or []
        check(used == [stored_cpi[p] for p in range(1, period + 1)][:len(used)]
              and (len(used) == period or period == 1),
              f"period {period}: cpiHistory is the stored values of periods 1..{period}",
              str(used))

print()
print("=" * 78)
print("5. A project whose earlier period was superseded reads the LIVE row, and only live rows")
print("=" * 78)

with Session() as s:
    proj = s.scalar(select(Project).where(Project.legacy_id == A))
    dead = s.scalars(select(ComputedResult).where(
        ComputedResult.project_id == proj.id,
        ComputedResult.superseded_by.is_not(None))).all()
    check(len(dead) >= 2, "the recomputes above left superseded rows in the table, so the "
          "live-only filter has something to exclude", str(len(dead)))
    snaps = _period_snapshots(s, proj, 4, {"cpi": stored_cpi[4], "spi": 1.0})
    check(len(snaps) == 4 and len({x["period"] for x in snaps}) == 4,
          "and a four-period series still has exactly four points, one per period",
          str([x["period"] for x in snaps]))

print()
print("=" * 78)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
print("=" * 78)
sys.exit(0 if FAILED == 0 else 1)
