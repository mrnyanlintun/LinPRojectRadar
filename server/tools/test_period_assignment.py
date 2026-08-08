#!/usr/bin/env python3
"""
The person states the reporting period, and documents land in the period they stated.

WHAT THIS SUITE EXISTS TO PROTECT. A project holding 84 documents across several reporting
periods computed as ONE period. The cause was not that compute ignored the period: assembly has
always filtered `DocumentUpload.period == period` strictly. It was that nothing ever ASSIGNED a
period. Every client either sent `period: 1` or sent nothing, and `_resolve_period` defaults a
missing period to 1, so a whole project history landed in period one and every cross-period
reader saw a single point.

The checks below hold four things apart:
  - documents stated to different periods land in different periods, and compute finds them;
  - a document dated outside the period it was filed to is FLAGGED and still STORED, never
    moved and never refused;
  - recomputing period one after period four exists is byte-identical, which is the invariant
    this change could most easily have broken because it changes how documents are partitioned;
  - the trend readers compute on four periods and abstain on one, which is the measure of
    whether this defect was what held them back.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_period_assignment.py
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
from app.research_models import (  # noqa: E402
    ComputedResult, DocumentUpload, Participant,
)

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


ADMIN = "pa-admin"
FOUR = "PRJ-PA-FOUR"
ONE = "PRJ-PA-ONE"
FLAG = "PRJ-PA-FLAG"

# Four reporting periods. Every cpi and spi differs, so a series taken from the wrong period
# cannot match by coincidence.
MONTHS = {
    1: ("2026-03-31", 3_000_000, 3_300_000, 3_200_000, 25.0, 27.0),
    2: ("2026-04-30", 4_000_000, 4_400_000, 4_300_000, 33.0, 36.0),
    3: ("2026-05-31", 5_000_000, 5_600_000, 5_400_000, 42.0, 45.0),
    4: ("2026-06-30", 6_000_000, 6_900_000, 6_500_000, 50.0, 54.0),
}


def fields(d, ev, ac, pv, apc, ppc):
    return {"earned_value": ev, "actual_cost": ac, "planned_value": pv,
            "budget_at_completion": 12_000_000, "actual_percent_complete": apc,
            "planned_percent_complete": ppc, "report_date": d, "document_date": d}


def doc(tag: str) -> bytes:
    return f"%PDF-1.4 PERIOD ASSIGN {tag}\n".encode()


REC = {}
for _p, _m in MONTHS.items():
    REC[hashlib.sha256(doc(f"M{_p}")).hexdigest()] = ("monthly_report", fields(*_m))
    REC[hashlib.sha256(doc(f"O{_p}")).hexdigest()] = ("monthly_report", fields(*_m))
# A document whose own date is far outside any period it is likely to be filed to.
REC[hashlib.sha256(doc("LATE")).hexdigest()] = (
    "monthly_report", fields("2026-11-30", 7_000_000, 7_500_000, 7_200_000, 60.0, 62.0))
set_extractor_override(StubExtractor(REC))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="PA-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    for legacy in (FOUR, ONE, FLAG):
        if s.scalar(select(Project).where(Project.legacy_id == legacy)) is None:
            s.add(Project(legacy_id=legacy,
                          doc={"id": legacy, "name": legacy, "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "PA-PM", "role": "Participant",
                "account_type": "operational"})
pm = post({"action": "researchlogin",
           "access_token": created["access_token"]})["session_token"]
for legacy in (FOUR, ONE, FLAG):
    post({"action": "adminmemberadd", "session_token": admin, "id": legacy,
          "participant_id": created["participant_id"], "project_role": "PM"})

try:
    print("=" * 78)
    print("1. Documents stated to different periods land in different periods")
    print("=" * 78)

    for p in (1, 2, 3, 4):
        up = post({"action": "projectupload", "session_token": pm, "id": FOUR,
                   "period": p, "period_end": MONTHS[p][0],
                   "documents": [{"filename": f"M{p}.pdf", "mimeType": "application/pdf",
                                  "dataBase64": b64(doc(f"M{p}"))}]})
        check(up.get("ok") is True and up.get("period") == p,
              f"a document stated to period {p} is filed to period {p}",
              str(up.get("period")))
        check(up.get("period_end") == MONTHS[p][0],
              f"and the stated period ending date is echoed back ({MONTHS[p][0]})",
              str(up.get("period_end")))

    with Session() as s:
        pid = s.scalar(select(Project.id).where(Project.legacy_id == FOUR))
        counts = dict(s.execute(
            select(DocumentUpload.period, func.count())
            .where(DocumentUpload.project_id == pid)
            .group_by(DocumentUpload.period)).all())
    check(counts == {1: 1, 2: 1, 3: 1, 4: 1},
          "the store holds four distinct periods, one document each", str(counts))

    print()
    print("=" * 78)
    print("2. A project with four periods computes four results")
    print("=" * 78)

    allr = post({"action": "projectcomputeall", "session_token": pm, "id": FOUR})
    check(allr.get("ok") is True, "the all-periods control runs", str(allr)[:160])
    check(allr.get("periods") == [1, 2, 3, 4],
          "it discovers four periods, not one", str(allr.get("periods")))
    check(allr.get("computed") == 4,
          "and computes four results", str(allr.get("computed")))

    cutoffs = {}
    for p in (1, 2, 3, 4):
        r = post({"action": "projectresults", "session_token": pm, "id": FOUR,
                  "period": p})["result"]
        cutoffs[p] = r["period_cutoff"]
        check(len(r.get("source_documents") or []) == 1,
              f"period {p} computed from its own single document",
              str(len(r.get("source_documents") or [])))
    check([cutoffs[p] for p in (1, 2, 3, 4)] == [MONTHS[p][0] for p in (1, 2, 3, 4)],
          "each period's cutoff is its OWN evidence date, derived as before and now distinct",
          str(cutoffs))

    print()
    print("=" * 78)
    print("3. The trend readers compute on four periods")
    print("=" * 78)

    r4 = post({"action": "projectresults", "session_token": pm, "id": FOUR,
               "period": 4})["result"]
    si4 = r4["signal_inputs"]
    mods4 = {m.get("method_class") for m in (r4.get("module_results") or [])}
    check(len(si4.get("cpiHistory") or []) == 4,
          "period four is given a four-point cost performance series",
          str(si4.get("cpiHistory")))
    check(len(si4.get("spiHistory") or []) == 4,
          "and a four-point schedule performance series", str(si4.get("spiHistory")))
    check(len(set(si4.get("cpiHistory") or [])) > 1,
          "the series is not flat, so a wrong assembly cannot pass by coincidence",
          str(si4.get("cpiHistory")))
    for mc, name in (("CUSUM", "the control-chart reader"),
                     ("Kalman_Filter", "the smoother"),
                     ("ARIMA_Forecast", "the forecast reader"),
                     ("Regression_To_Mean", "the regression reader")):
        check(mc in mods4, f"{name} computes on four periods")

    print()
    print("=" * 78)
    print("4. THE INVARIANT: recomputing period one after period four exists")
    print("=" * 78)

    # ORDER MATTERS HERE, AND IT IS NOT INCIDENTAL. The portfolio snapshot is cutoff-aligned
    # ACROSS projects: a vector is included for every other project holding a live result at or
    # before this computation's cutoff (the P1 rule from the storage redesign). So a project
    # created later, carrying a result dated at or before this cutoff, legitimately joins this
    # period's portfolio and legitimately changes the stored snapshot. That is the design, not
    # a leak, and it is a DIFFERENT question from the one this check asks.
    #
    # The invariant under test is the period-series one: recomputing an earlier period after
    # LATER PERIODS OF THE SAME PROJECT exist must reproduce it. So the comparison runs here,
    # while the four-period project is the only one with results. Moving it below the
    # single-period and flagging fixtures reintroduces the other projects and makes the check
    # fail for a reason that has nothing to do with period assignment.
    before_p1 = payload_bytes(FOUR, 1)
    before_p2 = payload_bytes(FOUR, 2)
    post({"action": "adminrecompute", "session_token": admin, "id": FOUR, "period": 1,
          "reason": "period-assignment byte-identical check"})
    after_p1 = payload_bytes(FOUR, 1)
    first_diff = next((i for i, (a, b) in enumerate(zip(before_p1, after_p1)) if a != b), "n/a")
    check(after_p1 == before_p1,
          "RECOMPUTING PERIOD ONE WITH PERIODS TWO TO FOUR STORED IS BYTE-IDENTICAL",
          f"first difference at byte {first_diff}")
    check(payload_bytes(FOUR, 2) == before_p2,
          "and period two is untouched by that recompute")

    si1 = post({"action": "projectresults", "session_token": pm, "id": FOUR,
                "period": 1})["result"]["signal_inputs"]
    check(si1.get("cpiHistory") is None,
          "the recomputed period one still has no series: the later periods did not reach it",
          str(si1.get("cpiHistory")))

    print()
    print("=" * 78)
    print("5. The same readers abstain on a one-period project")
    print("=" * 78)

    post({"action": "projectupload", "session_token": pm, "id": ONE, "period": 1,
          "period_end": MONTHS[1][0],
          "documents": [{"filename": "O1.pdf", "mimeType": "application/pdf",
                         "dataBase64": b64(doc("O1"))}]})
    post({"action": "projectcompute", "session_token": pm, "id": ONE, "period": 1})
    r1 = post({"action": "projectresults", "session_token": pm, "id": ONE,
               "period": 1})["result"]
    mods1 = {m.get("method_class") for m in (r1.get("module_results") or [])}
    check(r1["signal_inputs"].get("cpiHistory") is None,
          "one period is given no series at all", str(r1["signal_inputs"].get("cpiHistory")))
    for mc, name in (("CUSUM", "the control-chart reader"),
                     ("Kalman_Filter", "the smoother"),
                     ("ARIMA_Forecast", "the forecast reader"),
                     ("Regression_To_Mean", "the regression reader")):
        check(mc not in mods1,
              f"{name} abstains on one period rather than inventing a series")

    print()
    print("=" * 78)
    print("6. A document dated outside its stated period is flagged AND stored")
    print("=" * 78)

    up = post({"action": "projectupload", "session_token": pm, "id": FLAG,
               "period": 1, "period_end": "2026-03-31",
               "documents": [{"filename": "LATE.pdf", "mimeType": "application/pdf",
                              "dataBase64": b64(doc("LATE"))}]})
    check(up.get("ok") is True, "the upload is NOT refused", str(up)[:160])
    mismatches = up.get("date_mismatches") or []
    check(len(mismatches) == 1, "exactly one document is flagged", str(mismatches))
    check(mismatches and mismatches[0]["filename"] == "LATE.pdf",
          "and it is the one whose date is outside the period", str(mismatches))
    check(mismatches and "2026-11-30" in mismatches[0]["reason"]
          and "2026-03-31" in mismatches[0]["reason"],
          "the reason names both the document's own date and the period's end",
          str(mismatches[0]["reason"]) if mismatches else "")
    check((up.get("summary") or {}).get("date_mismatches") == 1,
          "the summary counts it too", str(up.get("summary")))
    per_file = {f["filename"]: f for f in (up.get("files") or [])}
    check(per_file.get("LATE.pdf", {}).get("period_date_mismatch"),
          "the flag rides on the file's own row, where the outcome is read")
    check(per_file.get("LATE.pdf", {}).get("status") in ("extracted", "matched"),
          "and the document extracted normally",
          str(per_file.get("LATE.pdf", {}).get("status")))

    with Session() as s:
        pid = s.scalar(select(Project.id).where(Project.legacy_id == FLAG))
        rows = s.scalars(select(DocumentUpload).where(
            DocumentUpload.project_id == pid)).all()
    check(len(rows) == 1 and rows[0].period == 1,
          "IT IS STORED, in the period that was stated, not moved to one that fits its date",
          str([(r.period, str(r.period_end)) for r in rows]))
    check(rows and str(rows[0].period_end) == "2026-03-31",
          "with the stated period ending date recorded beside it",
          str(rows[0].period_end) if rows else "")

    # A document INSIDE its period raises nothing, so the flag can distinguish.
    clean = post({"action": "projectupload", "session_token": pm, "id": FLAG,
                  "period": 2, "period_end": "2026-04-30",
                  "documents": [{"filename": "O2.pdf", "mimeType": "application/pdf",
                                 "dataBase64": b64(doc("O2"))}]})
    check(not (clean.get("date_mismatches") or []),
          "a document dated inside its stated period is not flagged",
          str(clean.get("date_mismatches")))

    # And one dated into an EARLIER period is caught by the lower bound.
    early = post({"action": "projectupload", "session_token": pm, "id": FLAG,
                  "period": 3, "period_end": "2026-05-31",
                  "documents": [{"filename": "M1.pdf", "mimeType": "application/pdf",
                                 "dataBase64": b64(doc("M1"))}]})
    em = early.get("date_mismatches") or []
    check(len(em) == 1 and "earlier reporting period" in em[0]["reason"],
          "a document dated in an earlier period is flagged against the lower bound",
          str(em))

    # With no ending date stated there is nothing to measure against, and nothing is claimed.
    quiet = post({"action": "projectupload", "session_token": pm, "id": FLAG,
                  "period": 4,
                  "documents": [{"filename": "M4.pdf", "mimeType": "application/pdf",
                                 "dataBase64": b64(doc("M4"))}]})
    check(not (quiet.get("date_mismatches") or []),
          "with no period ending stated the check says nothing rather than guessing a boundary",
          str(quiet.get("date_mismatches")))
    check(quiet.get("period_end") is None,
          "and the response reports that none was stored", str(quiet.get("period_end")))

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
