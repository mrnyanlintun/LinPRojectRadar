#!/usr/bin/env python3
"""
The schedule: parsed, refused where it must be, stored per period, and compared.

WHAT THIS SUITE PROTECTS, in order of how easily each could rot into a lie.

1. A DATE IS PARSED TO THE RIGHT DATE, not merely parsed without error. Every check on the
   parser asserts the resolved calendar date, because "it returned something" is exactly the
   failure mode that would let a wrong-century or a day/month swap through.

2. A DATE THAT CANNOT BE READ REFUSES, and the refusal names the row. `29-May` states no year.
   Resolving it from the document's reporting period or data date is the same class of defect
   the extraction prompt was already fixed for (a value of the right type sitting nearby is not
   a source), so the parser takes no context argument at all and there is nothing to pass one
   to. A row whose current finish refused is a MISSING ROW.

3. AN ACTUAL DATE IS DISTINGUISHABLE FROM A FORECAST ONE. `24-Mar-26 A` carries Primavera P6's
   actual-date marker: the activity finished, and that date will not move. Stripping the marker
   to normalise the date would turn a recorded fact into a prediction.

4. THE SAME ACTIVITY ACROSS TWO PERIODS IS TWO OBSERVATIONS. Not two rows competing to be
   current.

5. RECOMPUTING AN EARLIER PERIOD AFTER A LATER ONE EXISTS IS BYTE-IDENTICAL. Same comparison
   `test_period_series.py` states: the stored row's analytical content serialised with
   `json.dumps(sort_keys=True)` and compared as bytes, with `result_id` and `computed_at`
   excluded BY NAME because a recompute is a new append-only row and is required to have a new
   id, so including them would make the check unpassable for a reason unrelated to period
   alignment.

6. A MILESTONE ABSENT FROM A LATER PERIOD IS NOT MOVEMENT. It is a missing row. Tested twice:
   through the real pipeline, and directly against the module.

THE FIXTURE'S DATES ARE THE ONES A REAL DOCUMENT CARRIED. `29-May`, `14 August 2026` and
`24-Mar-26 A` appeared in one column of one real design activity table
(`REPORT_2026-08-05_extraction-substitution.md` section 1.2 and section 4), together with the
headings `Activity`, `Description`, `Baseline start`, `Baseline finish`, `Complete`,
`Current finish / actual`. The real document is not in this container: this fixture RECONSTRUCTS
those shapes from the recorded findings. That limit is stated in the report and is stated here.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_schedule_milestones.py
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from datetime import date

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.extraction_client import StubExtractor  # noqa: E402
from app.field_registry import NEEDS, unservable_needs  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import (  # noqa: E402
    ComputedResult, Participant, ScheduleActivity,
)
from app.schedule_activities import (  # noqa: E402
    parse_percent_complete, read_activity_table, refusal_lines,
)
from app.schedule_dates import (  # noqa: E402
    ACTUAL, FORECAST, DateRefusal, ScheduleDate, parse_schedule_date,
)
from app.simulation.models_ext import run_milestone_trend  # noqa: E402

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


try:
    print("=" * 78)
    print("1. THE DATE SHAPES A REAL SCHEDULE CARRIED: each parses to the RIGHT date")
    print("=" * 78)

    # Every case asserts the resolved calendar date and the actual/forecast kind. A shape that
    # "parsed" to the wrong day would pass a truthiness check and fail every one of these.
    ACCEPTED = [
        ("24-Mar-26 A", date(2026, 3, 24), ACTUAL,
         "day-month-two-digit-year with P6's ACTUAL marker"),
        ("24-Mar-26", date(2026, 3, 24), FORECAST, "the same date without the marker"),
        ("12-Jan-26", date(2026, 1, 12), FORECAST, "day-month-two-digit-year"),
        ("14 August 2026", date(2026, 8, 14), FORECAST, "day, month spelled out, four-digit year"),
        ("1 March 2026", date(2026, 3, 1), FORECAST, "single-digit day, month spelled out"),
        ("2026-09-30", date(2026, 9, 30), FORECAST, "ISO, the one shape that already parsed"),
        ("24-Mar-2026", date(2026, 3, 24), FORECAST, "day-month-four-digit-year"),
        ("24 Mar 26", date(2026, 3, 24), FORECAST, "space separated, abbreviated month"),
        ("24/Mar/26", date(2026, 3, 24), FORECAST, "slash separated, abbreviated month"),
        ("Mar 24, 2026", date(2026, 3, 24), FORECAST, "month-first with a comma"),
        ("August 14 2026", date(2026, 8, 14), FORECAST, "month-first, spelled out"),
        ("14 Aug 2026 A", date(2026, 8, 14), ACTUAL, "spelled-out shape with the ACTUAL marker"),
        ("30-Sept-26", date(2026, 9, 30), FORECAST, "the four-letter September abbreviation"),
        ("14 August 2026 ", date(2026, 8, 14), FORECAST, "trailing whitespace is not a marker"),
        ("24-Mar-99", date(1999, 3, 24), FORECAST,
         "two-digit year 99 expands to 1999 by the stated window, not to 2099"),
    ]
    for raw, expected, kind, why in ACCEPTED:
        got = parse_schedule_date(raw)
        check(isinstance(got, ScheduleDate) and got.value == expected and got.kind == kind,
              f"{raw!r} -> {expected.isoformat()} ({kind}): {why}",
              repr(got))

    print()
    print("-" * 78)
    print("1b. And every shape this parser REFUSES, with the reason it refuses")
    print("-" * 78)

    REFUSED = [
        ("29-May", "no year",
         "no year stated: a year is NOT taken from the reporting period or the data date"),
        ("02-Apr", "no year", "more of the same no-year shape from the real table"),
        ("17-Jul", "no year", "and another"),
        ("May 29", "no year", "month-first with no year refuses the same way"),
        ("03/04/26", "ambiguous", "all-numeric: 3 April or 4 March is not decidable"),
        ("2026/03/04", "ambiguous",
         "all-numeric even with a four-digit year: the order is still a convention"),
        ("24-Mar-26 X", "marker", "an unrecognised marker is not silently dropped"),
        ("31-Feb-26", "calendar date", "a date that does not exist on the calendar"),
        ("24-Smarch-26", "month name", "an unrecognised month name"),
        ("TBD", "states no date", "a cell that says the date is not known yet"),
        ("N/A", "states no date", "and its siblings"),
        ("next quarter", "unrecognised", "prose is not a date"),
        ("Q3 2026", "unrecognised", "a quarter is not a date"),
    ]
    for raw, fragment, why in REFUSED:
        got = parse_schedule_date(raw)
        check(isinstance(got, DateRefusal) and fragment in got.reason,
              f"{raw!r} REFUSES ({fragment}): {why}", repr(got))

    check(parse_schedule_date("") is None and parse_schedule_date(None) is None
          and parse_schedule_date("   ") is None,
          "an EMPTY cell is None, not a refusal: a column the row did not fill in is not a "
          "value that failed to parse")

    # The strongest statement about year inference is structural, not behavioural.
    import inspect  # noqa: E402
    sig = inspect.signature(parse_schedule_date)
    check(list(sig.parameters) == ["raw"],
          "parse_schedule_date takes ONE argument: there is no context parameter a caller "
          "could use to supply a year the document did not state",
          str(sig))
    check(parse_schedule_date("29-May") != parse_schedule_date("29-May-26"),
          "and the no-year form never resolves to the same thing as a year-bearing one")

    print()
    print("=" * 78)
    print("2. THE TABLE'S OWN HEADINGS, mapped to fields on this side of the boundary")
    print("=" * 78)

    # The real table's headings, verbatim.
    REAL_ROW = {
        "Activity": "D100", "Description": "Concept design",
        "Baseline start": "12-Jan-26", "Baseline finish": "24-Mar-26",
        "Complete": "100%", "Current finish / actual": "24-Mar-26 A",
    }
    rows = read_activity_table([REAL_ROW])
    check(len(rows) == 1, "one table row in, one activity row out", str(rows))
    r = rows[0]
    check(r["activity_key"] == "D100" and r["description"] == "Concept design",
          "`Activity` becomes the identity and `Description` the description", str(r))
    check(r["baseline_start"] == "2026-01-12" and r["baseline_finish"] == "2026-03-24",
          "`Baseline start` and `Baseline finish` parse to the right dates", str(r))
    check(r["current_finish"] == "2026-03-24" and r["current_finish_kind"] == ACTUAL,
          "`Current finish / actual` parses AND is marked actual, not forecast", str(r))
    check(r["percent_complete"] == 100.0, "`Complete` reads 100 from '100%'", str(r))
    check(r["usable_for_trend"] is True and r["unparsed"] == [],
          "and the row is usable with nothing refused", str(r))

    forecast_row = read_activity_table([{**REAL_ROW, "Activity": "D200",
                                         "Current finish / actual": "14 August 2026"}])[0]
    check(forecast_row["current_finish_kind"] == FORECAST
          and r["current_finish_kind"] == ACTUAL,
          "AN ACTUAL DATE IS DISTINGUISHABLE FROM A FORECAST ONE in the stored row itself",
          f"{forecast_row['current_finish_kind']} vs {r['current_finish_kind']}")

    refused_row = read_activity_table([{**REAL_ROW, "Activity": "D400",
                                        "Current finish / actual": "29-May"}])[0]
    check(refused_row["current_finish"] is None
          and refused_row["usable_for_trend"] is False,
          "a row whose current finish will not parse is UNUSABLE for a trend", str(refused_row))
    lines = refusal_lines([refused_row])
    check(len(lines) == 1 and lines[0].startswith("D400:") and "29-May" in lines[0]
          and "no year" in lines[0],
          "and the refusal NAMES THE ROW and gives the reason", str(lines))

    check(read_activity_table([{"Description": "", "Current finish": "2026-01-01"}]) == [],
          "a row with neither identifier nor description is dropped: it has no identity to "
          "match itself by in the next period, and positional matching would compare two "
          "different activities")

    alt = read_activity_table([{"Milestone ID": "M1", "Milestone Description": "Substantial "
                                "completion", "Planned Finish": "01-Feb-27",
                                "Forecast Finish": "15-Mar-27", "% Complete": "60"}])[0]
    check(alt["activity_key"] == "M1" and alt["baseline_finish"] == "2027-02-01"
          and alt["current_finish"] == "2027-03-15" and alt["percent_complete"] == 60.0,
          "a differently headed milestone table maps too, without the module's keys leaking "
          "into the prompt", str(alt))

    check(parse_percent_complete("") is None and parse_percent_complete("TBD") is None
          and parse_percent_complete(None) is None and parse_percent_complete("101") is None,
          "an unreadable or out-of-range percent complete is None, NEVER 0: nothing is "
          "invented for a row that did not carry it")
    check(parse_percent_complete("45.5%") == 45.5 and parse_percent_complete(0) == 0.0,
          "and a stated 0 is kept, because a stated zero is data")

    print()
    print("=" * 78)
    print("3. THE SCHEDULE STORED PER PERIOD, through the real pipeline")
    print("=" * 78)

    ADMIN = "sched-admin-token"
    PRJ = "PRJ-SCHED1"

    def activity(key, desc, bstart, bfinish, complete, current):
        return {"Activity": key, "Description": desc, "Baseline start": bstart,
                "Baseline finish": bfinish, "Complete": complete,
                "Current finish / actual": current}

    # Period 1. The four shapes the real column carried, plus one activity that will vanish.
    P1_TABLE = [
        activity("D100", "Concept design", "12-Jan-26", "24-Mar-26", "100%", "24-Mar-26 A"),
        activity("D200", "Schematic design", "25-Mar-26", "14 August 2026", "45%",
                 "14 August 2026"),
        activity("D300", "Design development", "2026-04-01", "2026-09-30", "10",
                 "2026-09-30"),
        activity("D400", "Permit set", "01-Jun-26", "29-May", "0%", "29-May"),
        activity("D600", "Cost plan", "01-Apr-26", "30-Apr-26", "20%", "30-Apr-26"),
    ]
    # Period 2. D200 slips 14 days, D300 slips 7, D100 is actual and cannot move, D400 still
    # refuses, D600 IS GONE, D700 is new.
    P2_TABLE = [
        activity("D100", "Concept design", "12-Jan-26", "24-Mar-26", "100%", "24-Mar-26 A"),
        activity("D200", "Schematic design", "25-Mar-26", "14 August 2026", "55%",
                 "28 August 2026"),
        activity("D300", "Design development", "2026-04-01", "2026-09-30", "20",
                 "2026-10-07"),
        activity("D400", "Permit set", "01-Jun-26", "29-May", "0%", "29-May"),
        activity("D700", "Tender documents", "01-Sep-26", "30-Nov-26", "0%", "30-Nov-26"),
    ]
    P1_EX = {"data_date": "2026-03-31", "planned_percent_complete": 40.0,
             "activities_planned": 5, "milestones_json": P1_TABLE}
    P2_EX = {"data_date": "2026-04-30", "planned_percent_complete": 50.0,
             "activities_planned": 5, "milestones_json": P2_TABLE}

    def doc_bytes(tag: str) -> bytes:
        return f"%PDF-1.4 SCHEDULE {tag}\n".encode()

    RECORDED = {
        hashlib.sha256(doc_bytes("S1")).hexdigest(): ("schedule_update", P1_EX),
        hashlib.sha256(doc_bytes("S2")).hexdigest(): ("schedule_update", P2_EX),
    }
    set_extractor_override(StubExtractor(RECORDED))

    with Session() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code="SCHED-ADMIN", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        if s.scalar(select(Project).where(Project.legacy_id == PRJ)) is None:
            s.add(Project(legacy_id=PRJ, doc={"id": PRJ, "name": "Schedule One",
                                              "signals": {}, "events": []}))
        s.commit()

    admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    created = post({"action": "adminparticipantcreate", "session_token": admin,
                    "pseudonymous_code": "SCHED-PM", "role": "Participant",
                    "account_type": "operational"})
    pm_id = created["participant_id"]
    pm = post({"action": "researchlogin",
               "access_token": created["access_token"]})["session_token"]
    post({"action": "adminmemberadd", "session_token": admin, "id": PRJ,
          "participant_id": pm_id, "project_role": "PM"})

    def upload_and_compute(period: int, tag: str) -> dict:
        up = post({"action": "projectupload", "session_token": pm, "id": PRJ, "period": period,
                   "documents": [{"filename": f"{tag}.pdf", "mimeType": "application/pdf",
                                  "dataBase64": b64(doc_bytes(tag))}]})
        assert up.get("ok") is True, str(up)[:300]
        post({"action": "projectcompute", "session_token": pm, "id": PRJ, "period": period})
        return post({"action": "projectresults", "session_token": pm,
                     "id": PRJ, "period": period})["result"]

    _COMPARED = ("period", "signal_inputs", "module_results", "category_statuses",
                 "project_status", "portfolio_snapshot", "simulation_version", "seed",
                 "period_cutoff", "source_documents")

    def payload_bytes(period: int) -> bytes:
        with Session() as s:
            pid = s.scalar(select(Project.id).where(Project.legacy_id == PRJ))
            row = s.scalar(select(ComputedResult).where(
                ComputedResult.project_id == pid, ComputedResult.period == period,
                ComputedResult.superseded_by.is_(None)))
            assert row is not None, f"no live result for period {period}"
            out = {k: (str(getattr(row, k)) if k == "period_cutoff" else getattr(row, k))
                   for k in _COMPARED}
            return json.dumps(out, sort_keys=True, default=str).encode()

    r1 = upload_and_compute(1, "S1")
    p1_original = payload_bytes(1)

    with Session() as s:
        pid = s.scalar(select(Project.id).where(Project.legacy_id == PRJ))
        stored1 = {a.activity_key: a for a in s.scalars(select(ScheduleActivity).where(
            ScheduleActivity.project_id == pid, ScheduleActivity.period == 1)).all()}
    check(sorted(stored1) == ["D100", "D200", "D300", "D400", "D600"],
          "all five activity rows are STORED AS DATA, including the one that refused",
          str(sorted(stored1)))
    check(stored1["D100"].current_finish == "2026-03-24"
          and stored1["D100"].current_finish_kind == ACTUAL,
          "the stored row keeps the ACTUAL marker as a fact of its own", str(stored1["D100"]))
    check(stored1["D200"].current_finish == "2026-08-14"
          and stored1["D200"].current_finish_kind == FORECAST,
          "and the forecast beside it is stored as a forecast")
    check(stored1["D400"].current_finish is None
          and stored1["D400"].usable_for_trend is False
          and any("no year" in u["reason"] for u in stored1["D400"].unparsed),
          "the row that refused is stored WITH its reason, not dropped and not guessed",
          str(stored1["D400"].unparsed))
    check(stored1["D100"].percent_complete == 100.0
          and stored1["D300"].percent_complete == 10.0
          and stored1["D100"].baseline_start == "2026-01-12",
          "percent complete and the baseline dates are stored per activity")
    check(stored1["D100"].as_of == date(2026, 3, 31),
          "and the period's own data date is on the row", str(stored1["D100"].as_of))

    r2 = upload_and_compute(2, "S2")
    with Session() as s:
        pid = s.scalar(select(Project.id).where(Project.legacy_id == PRJ))
        d200 = s.scalars(select(ScheduleActivity).where(
            ScheduleActivity.project_id == pid,
            ScheduleActivity.activity_key == "D200")).all()
    check(len(d200) == 2 and sorted(a.period for a in d200) == [1, 2],
          "THE SAME ACTIVITY ACROSS TWO PERIODS IS TWO OBSERVATIONS, one per period",
          str([(a.period, a.current_finish) for a in d200]))
    by_period = {a.period: a for a in d200}
    check(by_period[1].current_finish == "2026-08-14"
          and by_period[2].current_finish == "2026-08-28",
          "and each period keeps its OWN forecast: period 1 is not rewritten by period 2",
          str({p: a.current_finish for p, a in by_period.items()}))
    check(by_period[1].percent_complete == 45.0 and by_period[2].percent_complete == 55.0,
          "percent complete likewise moves per period without overwriting")

    print()
    print("=" * 78)
    print("4. MILESTONE TREND ANALYSIS: abstains on one period, computes on two")
    print("=" * 78)

    check(NEEDS["milestoneHistory"]["servable"] is True
          and "milestoneHistory" not in unservable_needs(),
          "the registry now declares milestoneHistory SERVABLE, having correctly declared it "
          "unservable while the keys were wrong and the dates would not parse")

    si1 = r1["signal_inputs"]
    check(si1.get("milestoneHistory") is None,
          "period 1 is given NO milestone series: one period is not a trend, and the key is "
          "ABSENT rather than a one-element list", str(si1.get("milestoneHistory")))
    mods1 = {m["module_id"] for m in r1["module_results"]}
    check("A2.7" not in mods1,
          "so Milestone Trend Analysis ABSTAINS at period 1")

    si2 = r2["signal_inputs"]
    mh = si2.get("milestoneHistory")
    check(isinstance(mh, list) and len(mh) == 2 and [x["period"] for x in mh] == [1, 2],
          "period 2 is given exactly two snapshots, oldest first",
          str([x.get("period") for x in (mh or [])]))
    check(isinstance(mh, list) and mh[0]["at"] == "2026-03-31" and mh[1]["at"] == "2026-04-30",
          "each snapshot carries its own period's data date")
    check(isinstance(mh, list)
          and sorted(m["name"] for m in mh[0]["milestones"]) == ["D100", "D200", "D300", "D600"]
          and [m["name"] for m in mh[0]["unusable"]] == ["D400"],
          "the unusable row is reported as unusable, not silently missing",
          str(mh[0] if mh else None))
    check(isinstance(mh, list)
          and {m["name"]: m["forecast_kind"] for m in mh[1]["milestones"]}.get("D100") == ACTUAL
          and {m["name"]: m["forecast_kind"]
               for m in mh[1]["milestones"]}.get("D200") == FORECAST,
          "and the actual/forecast distinction survives into what the analytical layer is "
          "served")

    mods2 = {m["module_id"]: m for m in r2["module_results"]}
    a27 = mods2.get("A2.7")
    check(a27 is not None,
          "MILESTONE TREND ANALYSIS COMPUTES at period 2, for the first time on this platform",
          str(sorted(mods2)))
    # D100 actual, unmoved: 0. D200 14 August -> 28 August: +14. D300 30 Sep -> 7 Oct: +7.
    # Mean over the three matched activities is 7.0.
    check((a27 or {}).get("matched_count") == 3,
          "exactly THREE activities matched: D400 refused in both periods, D600 is absent "
          "from period 2 and D700 is absent from period 1",
          str((a27 or {}).get("matched_count")))
    check((a27 or {}).get("worst_milestone") == "D200"
          and (a27 or {}).get("worst_slip_days") == 14,
          "the worst slip is D200's fourteen days, named", str(a27))
    check(abs(((a27 or {}).get("mean_slip_days") or 0) - 7.0) < 1e-9,
          "and the mean slip over the matched activities is 7.0 days",
          str((a27 or {}).get("mean_slip_days")))
    check("D600" not in json.dumps(a27 or {}) and "D700" not in json.dumps(a27 or {}),
          "A MILESTONE ABSENT FROM THE OTHER PERIOD IS NOT REPORTED AS MOVEMENT: neither the "
          "vanished D600 nor the new D700 appears anywhere in the result", str(a27))

    print()
    print("-" * 78)
    print("4b. The same absence property, asserted directly against the module")
    print("-" * 78)

    # Two snapshots, one milestone in both and one only in the earlier. If absence were read as
    # movement, matched_count would be 2 and the vanished milestone could be named the worst.
    direct = run_milestone_trend({"milestoneHistory": [
        {"at": "2026-03-31", "milestones": [{"name": "M1", "forecast": "2026-06-01"},
                                            {"name": "GONE", "forecast": "2026-07-01"}]},
        {"at": "2026-04-30", "milestones": [{"name": "M1", "forecast": "2026-06-11"}]},
    ]}, lambda: 0.5, date(2026, 4, 30))
    check(direct.get("matched_count") == 1 and direct.get("worst_milestone") == "M1",
          "a milestone present in the earlier period and absent from the later one contributes "
          "NOTHING: one match, and the vanished one is not the worst", str(direct))
    check(abs((direct.get("mean_slip_days") or 0) - 10.0) < 1e-9,
          "and the mean is the surviving milestone's own ten-day slip, undiluted by a zero for "
          "the missing row", str(direct.get("mean_slip_days")))
    arriving = run_milestone_trend({"milestoneHistory": [
        {"at": "2026-03-31", "milestones": [{"name": "M1", "forecast": "2026-06-01"}]},
        {"at": "2026-04-30", "milestones": [{"name": "M1", "forecast": "2026-06-11"},
                                            {"name": "NEW", "forecast": "2026-09-01"}]},
    ]}, lambda: 0.5, date(2026, 4, 30))
    check(arriving.get("matched_count") == 1,
          "and a milestone that ARRIVES in the later period is not movement either",
          str(arriving))
    single = run_milestone_trend({"milestoneHistory": [
        {"at": "2026-03-31", "milestones": [{"name": "M1", "forecast": "2026-06-01"}]},
    ]}, lambda: 0.5, date(2026, 3, 31))
    check(single.get("insufficient_data") is True,
          "and one snapshot abstains at the module's own guard", str(single))

    print()
    print("=" * 78)
    print("5. THE ACCEPTANCE CONDITION: an earlier period is byte-identical after a later one")
    print("=" * 78)

    post({"action": "adminrecompute", "session_token": admin, "id": PRJ, "period": 1,
          "reason": "schedule alignment check"})
    p1_recomputed = payload_bytes(1)
    check(p1_recomputed == p1_original,
          "recomputing period 1 with period 2 stored is BYTE-IDENTICAL to the original "
          "period-1 result",
          f"{len(p1_original)} vs {len(p1_recomputed)} bytes; first difference at "
          + str(next((i for i in range(min(len(p1_original), len(p1_recomputed)))
                      if p1_original[i] != p1_recomputed[i]), "n/a")))
    si1b = post({"action": "projectresults", "session_token": pm, "id": PRJ,
                 "period": 1})["result"]["signal_inputs"]
    check(si1b.get("milestoneHistory") is None,
          "the recomputed period 1 still has no milestone series: period 2's schedule did not "
          "reach it", str(si1b.get("milestoneHistory")))
    mods1b = {m["module_id"] for m in post({"action": "projectresults", "session_token": pm,
                                            "id": PRJ, "period": 1})["result"]["module_results"]}
    check("A2.7" not in mods1b,
          "and Milestone Trend Analysis still abstains there, which is what makes the "
          "byte-identical comparison a real constraint rather than a coincidence")

    # Read the assembly at its source, at both periods, against the fully populated project.
    from app.documents import _milestone_history  # noqa: E402
    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == PRJ))
        at1 = _milestone_history(s, proj, 1)
        at2 = _milestone_history(s, proj, 2)
    check([x["period"] for x in at1] == [1],
          "at period 1 the assembly reads period 1 and nothing later", str(at1)[:120])
    check([x["period"] for x in at2] == [1, 2],
          "at period 2 it reads both", str([x["period"] for x in at2]))
    check(sorted(m["name"] for m in at1[0]["milestones"])
          == ["D100", "D200", "D300", "D600"],
          "and period 1's snapshot still names D600, which period 2 dropped: an earlier "
          "period's account of its own schedule is never rewritten",
          str([m["name"] for m in at1[0]["milestones"]]))

    print()
    print("=" * 78)
    print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
    print("=" * 78)
    sys.exit(0 if FAILED == 0 else 1)
except SystemExit:
    raise
except BaseException as exc:  # noqa: BLE001
    # A crash must print a failing RESULT line, never silence.
    import traceback
    traceback.print_exc()
    print(f"RESULT: {PASSED}/{PASSED + FAILED + 1} checks passed (SUITE CRASHED: {exc!r})")
    sys.exit(1)
