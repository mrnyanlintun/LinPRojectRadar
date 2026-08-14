#!/usr/bin/env python3
"""
The two period defects INTERACTING: a partitioned project whose evidence later changes.

WHY THIS SUITE EXISTS SEPARATELY FROM THE OTHER TWO. `test_period_assignment.py` proves that a
stated period partitions documents, and `test_stale_period_recompute.py` proves that a period
whose documents changed is recomputed. Neither exercises the two together, and together is where
the byte-identical invariant is actually at risk: partitioning decides WHICH documents a period
holds, staleness compares a stored result's record of its inputs against exactly that set, and
the recompute cascade then rewrites every later period. A fault in the partition shows up as a
wrong staleness verdict, and a fault in the cascade shows up as a period that should have been
left alone being rewritten.

THE SCENARIO, which is the one the brief describes:

    four reporting periods, each stated at upload and each holding its own documents
    -> a further document uploaded into period TWO, which already has a result
    -> the all-periods control run

    period 1  skipped, and BYTE-IDENTICAL afterwards   (its evidence did not change)
    period 2  recomputed, because its own documents changed
    period 3  recomputed, because an earlier period was
    period 4  recomputed, because an earlier period was

The period-1 comparison is the load-bearing one. It is the invariant the period-series work
established, and this is the operation most able to break it.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_period_lifecycle.py
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

import app.main as main  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.extraction_client import StubExtractor  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import ComputedResult, DocumentUpload, Participant  # noqa: E402

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
    r = client.post("/exec", content=json.dumps(payload),
                    headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


_COMPARED = ("period", "signal_inputs", "module_results", "category_statuses", "project_status",
             "portfolio_snapshot", "simulation_version", "seed", "period_cutoff",
             "source_documents")


def payload_bytes(legacy: str, period: int) -> bytes:
    with Session() as s:
        pid = s.scalar(select(Project.id).where(Project.legacy_id == legacy))
        row = s.scalar(select(ComputedResult).where(
            ComputedResult.project_id == pid,
            ComputedResult.period == period,
            ComputedResult.superseded_by.is_(None)))
        assert row is not None, f"no live result for {legacy} period {period}"
        out = {k: (str(getattr(row, k)) if k == "period_cutoff" else getattr(row, k))
               for k in _COMPARED}
        return json.dumps(out, sort_keys=True, default=str).encode()


def result_id(legacy: str, period: int) -> str:
    with Session() as s:
        pid = s.scalar(select(Project.id).where(Project.legacy_id == legacy))
        return s.scalar(select(ComputedResult.result_id).where(
            ComputedResult.project_id == pid,
            ComputedResult.period == period,
            ComputedResult.superseded_by.is_(None)))


ADMIN = "pl-admin"
PRJ = "PRJ-PL-LIFECYCLE"

# Each period's report is dated mid-period and the period ENDS at the month end, which is what
# a monthly report actually looks like. The dates matter here: two same-type documents carrying
# the SAME date resolve by content hash under the equal-date tiebreak, so a revision dated the
# same day as the document it follows may legitimately lose. Dating the later document later is
# how a real revision wins, and it keeps the check about recompute rather than about a hash.
MONTHS = {
    1: ("2026-03-15", "2026-03-31", 3_000_000, 3_300_000, 3_200_000, 25.0, 27.0),
    2: ("2026-04-15", "2026-04-30", 4_000_000, 4_400_000, 4_300_000, 33.0, 36.0),
    3: ("2026-05-15", "2026-05-31", 5_000_000, 5_600_000, 5_400_000, 42.0, 45.0),
    4: ("2026-06-15", "2026-06-30", 6_000_000, 6_900_000, 6_500_000, 50.0, 54.0),
}
# The later document for period two: dated at the period end, so it is inside the period and
# later than the report it follows, and carrying materially worse cost performance so the
# recompute is visible in the stored figures and not only in a message.
P2_EXTRA = ("2026-04-30", 3_400_000, 4_900_000, 4_300_000, 28.0, 36.0)


def fields(d, ev, ac, pv, apc, ppc):
    return {"earned_value": ev, "actual_cost": ac, "planned_value": pv,
            "budget_at_completion": 12_000_000, "actual_percent_complete": apc,
            "planned_percent_complete": ppc, "report_date": d, "document_date": d}


def doc(tag: str) -> bytes:
    return f"%PDF-1.4 PERIOD LIFECYCLE {tag}\n".encode()


REC = {hashlib.sha256(doc(f"M{p}")).hexdigest(): ("monthly_report", fields(m[0], *m[2:]))
       for p, m in MONTHS.items()}
REC[hashlib.sha256(doc("P2X")).hexdigest()] = ("monthly_report", fields(*P2_EXTRA))
set_extractor_override(StubExtractor(REC))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="PL-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PRJ)) is None:
        s.add(Project(legacy_id=PRJ,
                      doc={"id": PRJ, "name": PRJ, "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "PL-PM", "role": "Participant",
                "account_type": "operational"})
pm = post({"action": "researchlogin",
           "access_token": created["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PRJ,
      "participant_id": created["participant_id"], "project_role": "PM"})

try:
    print("=" * 78)
    print("1. Four stated periods, four results, and the series the readers need")
    print("=" * 78)

    for p in (1, 2, 3, 4):
        post({"action": "projectupload", "session_token": pm, "id": PRJ,
              "period": p, "period_end": MONTHS[p][1],
              "documents": [{"filename": f"M{p}.pdf", "mimeType": "application/pdf",
                             "dataBase64": b64(doc(f"M{p}"))}]})
    allr = post({"action": "projectcomputeall", "session_token": pm, "id": PRJ})
    check(allr.get("periods") == [1, 2, 3, 4] and allr.get("computed") == 4,
          "four stated periods compute as four results", str(allr)[:160])

    r4 = post({"action": "projectresults", "session_token": pm, "id": PRJ,
               "period": 4})["result"]
    mods4 = {m.get("method_class") for m in (r4.get("module_results") or [])}
    # RUN 28. Only the control-chart anomaly monitor still computes from the period series
    # alone: its design is frozen and the supplied contract forbids retuning it in this run. The
    # smoother needs a governed state-space record stating where its variances came from, the
    # forecast reader needs a history long enough to identify a model from, and the pooling
    # reader needs a governed reference population of comparable projects; none is in this
    # corpus, so all three abstain truthfully. What this block proves -- that four periods of
    # stored history reach the analytical layer -- is unchanged and is still proved by the
    # monitor, which reads the identical series.
    for mc, name in (("CUSUM", "the control-chart anomaly monitor"),):
        check(mc in mods4, f"{name} computes at period four")
    _mc_ab = {a.get("module_id") for a in (r4.get("abstained") or [])}
    for _mid, _name in (("A1.4", "the schedule-performance smoother"),
                        ("A1.5", "the cost-performance forecast reader"),
                        ("A1.10", "the pooling reader")):
        check(_mid in _mc_ab,
              f"{_name} abstains at period four, on the same four periods of stored history")

    # Captured while the four periods are the ONLY results this project has, and before any
    # other project in this database gains one. The portfolio is cutoff-aligned across
    # projects, so a project created later with a result at or before this cutoff would
    # legitimately change period one's snapshot; that is a different question from the one
    # this suite asks and it must not be allowed to confound the comparison below.
    before = {p: payload_bytes(PRJ, p) for p in (1, 2, 3, 4)}
    ids_before = {p: result_id(PRJ, p) for p in (1, 2, 3, 4)}
    cpi2_before = post({"action": "projectresults", "session_token": pm, "id": PRJ,
                        "period": 2})["result"]["signal_inputs"]["cpi"]

    print()
    print("=" * 78)
    print("2. A further document is uploaded into period TWO, which already has a result")
    print("=" * 78)

    up = post({"action": "projectupload", "session_token": pm, "id": PRJ,
               "period": 2, "period_end": MONTHS[2][1],
               "documents": [{"filename": "P2X.pdf", "mimeType": "application/pdf",
                              "dataBase64": b64(doc("P2X"))}]})
    check(up.get("ok") is True and up.get("period") == 2,
          "it is filed to period two, the period stated", str(up.get("period")))
    check(not (up.get("date_mismatches") or []),
          "and it is not flagged: its own date is inside that period",
          str(up.get("date_mismatches")))

    with Session() as s:
        pid = s.scalar(select(Project.id).where(Project.legacy_id == PRJ))
        counts = dict(s.execute(
            select(DocumentUpload.period, func.count())
            .where(DocumentUpload.project_id == pid)
            .group_by(DocumentUpload.period)).all())
    check(counts == {1: 1, 2: 2, 3: 1, 4: 1},
          "only period two gained a document; the partition held", str(counts))

    print()
    print("=" * 78)
    print("3. The control recomputes from the earliest changed period FORWARD")
    print("=" * 78)

    again = post({"action": "projectcomputeall", "session_token": pm, "id": PRJ})
    check(again.get("ok") is True, "the all-periods control runs", str(again)[:160])
    by_period = {r["period"]: r for r in (again.get("results") or [])}

    check(by_period[1].get("skipped") is True,
          "period one is SKIPPED: its own evidence did not change", str(by_period.get(1)))
    check("unchanged" in (by_period[1].get("note") or "").lower(),
          "and the message says why, in those terms", str(by_period[1].get("note")))

    check(by_period[2].get("recomputed") is True,
          "period two is RECOMPUTED: its own documents changed", str(by_period.get(2)))
    check("document" in (by_period[2].get("reason") or "").lower(),
          "and the reason names what changed rather than counting",
          str(by_period[2].get("reason")))

    for p in (3, 4):
        check(by_period[p].get("recomputed") is True,
              f"period {p} is recomputed: an earlier period was", str(by_period.get(p)))
        check("earlier period" in (by_period[p].get("reason") or "").lower(),
              f"and period {p}'s reason says so", str(by_period[p].get("reason")))

    check(allr.get("periods") == again.get("periods"),
          "the period set is unchanged: recomputing invented no periods",
          str(again.get("periods")))

    print()
    print("=" * 78)
    print("4. THE INVARIANT: the untouched period is byte-identical, the changed one is not")
    print("=" * 78)

    after_p1 = payload_bytes(PRJ, 1)
    first_diff = next((i for i, (a, b) in enumerate(zip(before[1], after_p1)) if a != b), "n/a")
    check(after_p1 == before[1],
          "PERIOD ONE IS BYTE-IDENTICAL after a later period was recomputed",
          f"first difference at byte {first_diff}")
    check(result_id(PRJ, 1) == ids_before[1],
          "and it kept its result_id: it was genuinely left alone, not rewritten identically",
          f"{ids_before[1]} -> {result_id(PRJ, 1)}")

    check(payload_bytes(PRJ, 2) != before[2],
          "period two DID change: the new document reached the analysis")
    cpi2_after = post({"action": "projectresults", "session_token": pm, "id": PRJ,
                       "period": 2})["result"]["signal_inputs"]["cpi"]
    check(cpi2_after != cpi2_before,
          f"its cost performance moved ({cpi2_before} -> {cpi2_after})")
    src2 = sorted(d.get("filename", "") for d in
                  (post({"action": "projectresults", "session_token": pm, "id": PRJ,
                         "period": 2})["result"].get("source_documents") or []))
    check(src2 == ["M2.pdf", "P2X.pdf"],
          "and its result records BOTH of period two's documents", str(src2))

    for p in (3, 4):
        check(result_id(PRJ, p) != ids_before[p],
              f"period {p} was rewritten by the cascade", str(result_id(PRJ, p)))

    print()
    print("=" * 78)
    print("5. Each period still sees only itself and earlier periods")
    print("=" * 78)

    si = {}
    for p in (1, 2, 3, 4):
        si[p] = post({"action": "projectresults", "session_token": pm, "id": PRJ,
                      "period": p})["result"]["signal_inputs"]
    check(si[1].get("cpiHistory") is None,
          "period one has no series", str(si[1].get("cpiHistory")))
    for p in (2, 3, 4):
        check(len(si[p].get("cpiHistory") or []) == p,
              f"period {p} sees exactly {p} points, none from later",
              str(si[p].get("cpiHistory")))
    check(si[4]["cpiHistory"][1] == si[2]["cpi"],
          "and the cascade's series carries period two's NEW figure, not its superseded one",
          f"series {si[4]['cpiHistory']} vs period two cpi {si[2]['cpi']}")

    print()
    print("=" * 78)
    print("6. Running it once more, with nothing changed, touches nothing")
    print("=" * 78)

    settled = {p: payload_bytes(PRJ, p) for p in (1, 2, 3, 4)}
    settled_ids = {p: result_id(PRJ, p) for p in (1, 2, 3, 4)}
    third = post({"action": "projectcomputeall", "session_token": pm, "id": PRJ})
    check(third.get("computed") == 0 and third.get("skipped") == 4,
          "every period is skipped once the evidence has settled",
          f"computed={third.get('computed')} skipped={third.get('skipped')}")
    for p in (1, 2, 3, 4):
        check(payload_bytes(PRJ, p) == settled[p] and result_id(PRJ, p) == settled_ids[p],
              f"period {p} is byte-identical and keeps its result_id")

except Exception as exc:  # noqa: BLE001
    FAILED += 1
    print(f"  ****  UNCAUGHT EXCEPTION: {type(exc).__name__}: {exc}")
    import traceback
    traceback.print_exc()

print()
print("=" * 78)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
print("=" * 78)
sys.exit(1 if FAILED else 0)
