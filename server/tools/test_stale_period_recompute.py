#!/usr/bin/env python3
"""
A period with new documents is recomputed, not skipped: the stale-period recompute.

WHAT THIS SUITE EXISTS TO PROTECT. Before this fix, both `projectcomputeall` and
`projectcompute` checked only whether a live result existed, and skipped any period that had
one -- regardless of whether the period's document set had changed. A PM who uploaded into a
computed period saw the platform report it as done, with the new evidence unreached. The fix
compares the stored result's `source_documents` (the exact set of (document_id, sha256) pairs
the result was built from) against the period's current live document set, and recomputes when
they differ.

FORWARD INVALIDATION. The series readers (`_period_history`, `_period_snapshots`,
`_milestone_history`) take earlier periods' stored results as input. If period 1 is recomputed,
every later period's series has changed and must be recomputed too. This suite verifies that
a recompute of period 1 cascades to every later period.

THE INVARIANT THAT MUST NOT BREAK. A recompute of a period whose documents have NOT changed
must produce a byte-identical result. This suite proves that by recomputing a period with
unchanged documents and asserting the result matches byte for byte.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_stale_period_recompute.py
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


def result_id_for(project_legacy_id: str, period: int) -> str:
    with Session() as s:
        pid = s.scalar(select(Project.id).where(Project.legacy_id == project_legacy_id))
        row = s.scalar(select(ComputedResult).where(
            ComputedResult.project_id == pid,
            ComputedResult.period == period,
            ComputedResult.superseded_by.is_(None)))
        assert row is not None, f"no live result for {project_legacy_id} period {period}"
        return row.result_id


# --------------------------------------------------------------- fixture

ADMIN = "stale-admin-token"
A = "PRJ-STALEA1"
B = "PRJ-STALEB1"

P1_FIELDS = {"earned_value": 4_000_000, "actual_cost": 4_200_000, "planned_value": 4_100_000,
             "budget_at_completion": 10_000_000, "actual_percent_complete": 40.0,
             "planned_percent_complete": 41.0, "report_date": "2026-05-31",
             "document_date": "2026-05-31"}
P2_FIELDS = {"earned_value": 5_000_000, "actual_cost": 4_900_000, "planned_value": 5_100_000,
             "budget_at_completion": 10_000_000, "actual_percent_complete": 50.0,
             "planned_percent_complete": 51.0, "report_date": "2026-06-30",
             "document_date": "2026-06-30"}
P3_FIELDS = {"earned_value": 6_000_000, "actual_cost": 5_600_000, "planned_value": 6_050_000,
             "budget_at_completion": 10_000_000, "actual_percent_complete": 60.0,
             "planned_percent_complete": 61.0, "report_date": "2026-07-31",
             "document_date": "2026-07-31"}
OTHER = {"earned_value": 3_000_000, "actual_cost": 3_050_000, "planned_value": 3_020_000,
         "budget_at_completion": 9_000_000, "actual_percent_complete": 33.0,
         "planned_percent_complete": 34.0, "report_date": "2026-05-20",
         "document_date": "2026-05-20"}

# A new document uploaded AFTER the initial compute, with different EV figures
P1_EXTRA = {"earned_value": 4_100_000, "actual_cost": 4_200_000, "planned_value": 4_100_000,
            "budget_at_completion": 10_000_000, "actual_percent_complete": 41.0,
            "planned_percent_complete": 41.0, "report_date": "2026-05-31",
            "document_date": "2026-05-31"}


def doc_bytes(tag: str) -> bytes:
    return f"%PDF-1.4 STALE RECOMPUTE {tag}\n".encode()


RECORDED = {}
for tag, fields in (("A1", P1_FIELDS), ("A2", P2_FIELDS), ("A3", P3_FIELDS),
                    ("B1", OTHER), ("A1extra", P1_EXTRA)):
    sha = hashlib.sha256(doc_bytes(tag)).hexdigest()
    RECORDED[sha] = ("monthly_report", fields)

set_extractor_override(StubExtractor(RECORDED))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="STALE-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    for legacy, name in ((A, "Stale A"), (B, "Stale B")):
        if s.scalar(select(Project).where(Project.legacy_id == legacy)) is None:
            s.add(Project(legacy_id=legacy, doc={"id": legacy, "name": name, "signals": {},
                                                 "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "STALE-PM", "role": "Participant",
                "account_type": "operational"})
pm_id = created["participant_id"]
pm = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
for legacy in (A, B):
    post({"action": "adminmemberadd", "session_token": admin, "id": legacy,
          "participant_id": pm_id, "project_role": "PM"})

# Second project for portfolio
post({"action": "projectupload", "session_token": pm, "id": B, "period": 1,
      "documents": [{"filename": "B1.pdf", "mimeType": "application/pdf",
                     "dataBase64": b64(doc_bytes("B1"))}]})
post({"action": "projectcompute", "session_token": pm, "id": B, "period": 1})

# Build a three-period project A
for period, tag in ((1, "A1"), (2, "A2"), (3, "A3")):
    post({"action": "projectupload", "session_token": pm, "id": A, "period": period,
          "documents": [{"filename": f"{tag}.pdf", "mimeType": "application/pdf",
                         "dataBase64": b64(doc_bytes(tag))}]})

# Compute all three periods
all_resp = post({"action": "projectcomputeall", "session_token": pm, "id": A})
assert all_resp.get("ok") is True, str(all_resp)[:200]
assert all_resp["computed"] == 3, f"expected 3 computed, got {all_resp['computed']}"

p1_original = payload_bytes(A, 1)
p2_original = payload_bytes(A, 2)
p3_original = payload_bytes(A, 3)
p1_result_id = result_id_for(A, 1)


try:
    # ================================================================
    print("=" * 78)
    print("1. Uploading into a computed period and running the control recomputes that period")
    print("=" * 78)

    post({"action": "projectupload", "session_token": pm, "id": A, "period": 1,
          "documents": [{"filename": "A1extra.pdf", "mimeType": "application/pdf",
                         "dataBase64": b64(doc_bytes("A1extra"))}]})

    resp = post({"action": "projectcomputeall", "session_token": pm, "id": A})
    check(resp.get("ok") is True, "the all-periods control succeeds", str(resp)[:200])

    results_by_period = {r["period"]: r for r in resp["results"]}

    check(results_by_period[1].get("computed") is True,
          "period 1 was RECOMPUTED, not skipped", str(results_by_period.get(1)))
    check(results_by_period[1].get("recomputed") is True,
          "period 1 is marked as a recompute", str(results_by_period.get(1)))
    check(results_by_period[1].get("superseded_result_id") == p1_result_id,
          "the superseded result id is the original",
          f"expected {p1_result_id}, got {results_by_period[1].get('superseded_result_id')}")
    check("added" in (results_by_period[1].get("reason") or "").lower() or
          "document" in (results_by_period[1].get("reason") or "").lower(),
          "the reason names what changed",
          str(results_by_period[1].get("reason")))

    p1_after = payload_bytes(A, 1)
    check(p1_after != p1_original,
          "the result CHANGED: the new document reached the analysis",
          f"same={p1_after == p1_original}")

    r1_new = post({"action": "projectresults", "session_token": pm, "id": A,
                   "period": 1})["result"]
    src_docs = r1_new.get("source_documents") or []
    filenames = sorted(d.get("filename", "") for d in src_docs)
    check("A1extra.pdf" in filenames,
          "the recomputed result includes the new document in source_documents",
          str(filenames))
    check("A1.pdf" in filenames,
          "and still includes the original document",
          str(filenames))

    print()
    print("=" * 78)
    print("2. A period with no new documents is skipped and byte-identical afterwards")
    print("=" * 78)

    p1_now = payload_bytes(A, 1)
    p2_now = payload_bytes(A, 2)
    p3_now = payload_bytes(A, 3)
    p1_rid = result_id_for(A, 1)
    p2_rid = result_id_for(A, 2)
    p3_rid = result_id_for(A, 3)

    resp2 = post({"action": "projectcomputeall", "session_token": pm, "id": A})
    check(resp2.get("ok") is True, "the control succeeds", str(resp2)[:200])
    check(resp2["skipped"] == 3 and resp2["computed"] == 0,
          "all three periods skipped: no documents changed",
          f"computed={resp2.get('computed')}, skipped={resp2.get('skipped')}")
    check(payload_bytes(A, 1) == p1_now, "period 1 is byte-identical after skip")
    check(payload_bytes(A, 2) == p2_now, "period 2 is byte-identical after skip")
    check(payload_bytes(A, 3) == p3_now, "period 3 is byte-identical after skip")
    check(result_id_for(A, 1) == p1_rid, "period 1 result_id unchanged")
    check(result_id_for(A, 2) == p2_rid, "period 2 result_id unchanged")
    check(result_id_for(A, 3) == p3_rid, "period 3 result_id unchanged")

    print()
    print("=" * 78)
    print("3. Recomputing period 1 recomputes every later period (forward invalidation)")
    print("=" * 78)

    check(results_by_period[2].get("computed") is True,
          "period 2 was recomputed (forward invalidation from period 1)",
          str(results_by_period.get(2)))
    check(results_by_period[3].get("computed") is True,
          "period 3 was recomputed (forward invalidation from period 1)",
          str(results_by_period.get(3)))
    check("earlier period" in (results_by_period[2].get("reason") or "").lower(),
          "period 2's reason names earlier-period invalidation",
          str(results_by_period[2].get("reason")))
    check("earlier period" in (results_by_period[3].get("reason") or "").lower(),
          "period 3's reason names earlier-period invalidation",
          str(results_by_period[3].get("reason")))

    print()
    print("=" * 78)
    print("4. The per-period message names what changed rather than only counting")
    print("=" * 78)

    check(resp["computed"] + resp["skipped"] == len(resp["periods"]),
          "every period is accounted for: computed + skipped = total",
          f"computed={resp['computed']}, skipped={resp['skipped']}, periods={len(resp['periods'])}")
    for r in resp["results"]:
        if r.get("recomputed"):
            check(r.get("reason") is not None and len(r["reason"]) > 5,
                  f"period {r['period']}: recomputed with a stated reason",
                  str(r.get("reason")))

    print()
    print("=" * 78)
    print("5. The per-period Workspace button also recomputes a stale period")
    print("=" * 78)

    # Reset: rebuild project A cleanly for a fresh per-period test
    # We'll use a different project to avoid interfering with the forward-invalidation tests above
    C = "PRJ-STALEC1"
    C_FIELDS = {"earned_value": 7_000_000, "actual_cost": 7_100_000, "planned_value": 7_050_000,
                "budget_at_completion": 11_000_000, "actual_percent_complete": 63.0,
                "planned_percent_complete": 64.0, "report_date": "2026-06-15",
                "document_date": "2026-06-15"}
    C_EXTRA = {"earned_value": 7_200_000, "actual_cost": 7_100_000, "planned_value": 7_050_000,
               "budget_at_completion": 11_000_000, "actual_percent_complete": 65.0,
               "planned_percent_complete": 64.0, "report_date": "2026-06-15",
               "document_date": "2026-06-15"}
    for tag, fields in (("C1", C_FIELDS), ("C1extra", C_EXTRA)):
        sha = hashlib.sha256(doc_bytes(tag)).hexdigest()
        RECORDED[sha] = ("monthly_report", fields)
    set_extractor_override(StubExtractor(RECORDED))

    with Session() as s:
        if s.scalar(select(Project).where(Project.legacy_id == C)) is None:
            s.add(Project(legacy_id=C, doc={"id": C, "name": "Stale C", "signals": {},
                                             "events": []}))
        s.commit()
    post({"action": "adminmemberadd", "session_token": admin, "id": C,
          "participant_id": pm_id, "project_role": "PM"})

    post({"action": "projectupload", "session_token": pm, "id": C, "period": 1,
          "documents": [{"filename": "C1.pdf", "mimeType": "application/pdf",
                         "dataBase64": b64(doc_bytes("C1"))}]})
    comp1 = post({"action": "projectcompute", "session_token": pm, "id": C, "period": 1})
    check(comp1.get("ok") is True, "initial compute succeeds", str(comp1)[:200])
    c1_original = payload_bytes(C, 1)

    # Now upload an extra document into the same period
    post({"action": "projectupload", "session_token": pm, "id": C, "period": 1,
          "documents": [{"filename": "C1extra.pdf", "mimeType": "application/pdf",
                         "dataBase64": b64(doc_bytes("C1extra"))}]})

    # The per-period button should recompute
    comp2 = post({"action": "projectcompute", "session_token": pm, "id": C, "period": 1})
    check(comp2.get("ok") is True, "per-period compute succeeds", str(comp2)[:200])
    check(comp2.get("recomputed") is True,
          "the per-period button RECOMPUTED the stale period", str(comp2))
    check("added" in (comp2.get("reason") or "").lower() or
          "document" in (comp2.get("reason") or "").lower(),
          "and it says why", str(comp2.get("reason")))
    c1_after = payload_bytes(C, 1)
    check(c1_after != c1_original,
          "the result CHANGED after the per-period recompute", f"same={c1_after == c1_original}")

    # Run it again with no changes -- should skip
    comp3 = post({"action": "projectcompute", "session_token": pm, "id": C, "period": 1})
    check(comp3.get("ok") is True and comp3.get("recomputed") is not True,
          "running per-period compute again with unchanged docs returns the existing result",
          str(comp3))
    check(comp3.get("note") is not None and "unchanged" in comp3.get("note", "").lower(),
          "and says the documents are unchanged", str(comp3.get("note")))
    check(payload_bytes(C, 1) == c1_after,
          "and the result is byte-identical", f"same={payload_bytes(C, 1) == c1_after}")

    print()
    print("=" * 78)
    print("6. The append-only invariant: superseded rows survive recomputation")
    print("=" * 78)

    with Session() as s:
        pid = s.scalar(select(Project.id).where(Project.legacy_id == A))
        superseded = s.scalars(select(ComputedResult).where(
            ComputedResult.project_id == pid,
            ComputedResult.superseded_by.is_not(None))).all()
        live = s.scalars(select(ComputedResult).where(
            ComputedResult.project_id == pid,
            ComputedResult.superseded_by.is_(None))).all()
        check(len(superseded) >= 3,
              f"at least 3 superseded rows exist from the recomputation cascade ({len(superseded)} found)")
        check(len(live) == 3,
              f"exactly 3 live rows (one per period) after all the recomputation ({len(live)} found)")
        live_periods = sorted(r.period for r in live)
        check(live_periods == [1, 2, 3],
              "live rows cover all three periods", str(live_periods))

    print()
    print("=" * 78)
    print("7. First compute of a period that never had a result still works")
    print("=" * 78)

    # Upload a brand new period 2 for project C (never computed)
    P2C_FIELDS = {"earned_value": 8_000_000, "actual_cost": 8_100_000,
                  "planned_value": 8_050_000, "budget_at_completion": 11_000_000,
                  "actual_percent_complete": 72.0, "planned_percent_complete": 73.0,
                  "report_date": "2026-07-15", "document_date": "2026-07-15"}
    sha = hashlib.sha256(doc_bytes("C2")).hexdigest()
    RECORDED[sha] = ("monthly_report", P2C_FIELDS)
    set_extractor_override(StubExtractor(RECORDED))

    post({"action": "projectupload", "session_token": pm, "id": C, "period": 2,
          "documents": [{"filename": "C2.pdf", "mimeType": "application/pdf",
                         "dataBase64": b64(doc_bytes("C2"))}]})

    all_c = post({"action": "projectcomputeall", "session_token": pm, "id": C})
    check(all_c.get("ok") is True, "all-periods for C succeeds", str(all_c)[:200])
    c_results = {r["period"]: r for r in all_c["results"]}
    check(c_results[1].get("skipped") is True,
          "period 1 of C is skipped (documents unchanged)")
    check(c_results[2].get("computed") is True and c_results[2].get("recomputed") is not True,
          "period 2 of C is computed for the first time (no prior result)",
          str(c_results.get(2)))

    print()
    print("=" * 78)
    print("8. The byte-identical invariant holds: unchanged period's recompute matches")
    print("=" * 78)

    # Take period 2 of C, which was just computed. Recompute via adminrecompute and confirm
    # byte-identical
    c2_before = payload_bytes(C, 2)
    post({"action": "adminrecompute", "session_token": admin, "id": C, "period": 2,
          "reason": "byte-identical invariant check"})
    c2_after = payload_bytes(C, 2)
    check(c2_after == c2_before,
          "recomputing period 2 with unchanged documents is BYTE-IDENTICAL",
          f"{len(c2_before)} vs {len(c2_after)} bytes; first difference at "
          + str(next((i for i in range(min(len(c2_before), len(c2_after)))
                      if c2_before[i] != c2_after[i]), "n/a")))


except Exception as e:
    FAILED += 1
    print(f"  ****  UNCAUGHT EXCEPTION: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 78)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
print("=" * 78)
sys.exit(1 if FAILED else 0)
