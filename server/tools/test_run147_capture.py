#!/usr/bin/env python3
"""
RUN 147, MEASUREMENT ONE. WHAT THE SERVER ACTUALLY SENDS.

CONSTRUCTED FIXTURE. Production Postgres is never contacted and the only local database
holds no PRJ-002, so every byte captured here comes from a fixture built through the real
endpoints into a throwaway SQLite file: two periods, the second computed and holding module
results and abstentions, a frozen scenario naming the project as its evidence package, and a
research assignment whose decision in the last period is submitted AND transitioned -- the
state PRJ-002's assignment is in.

This script FIXES NOTHING. It captures, verbatim, the two HTTP exchanges the detail page makes
when it opens a project:

    1. POST /exec {action: projectperiods}   -- detail.js currentPeriod()
    2. POST /exec {action: projectresults}   -- detail.js primeAndRefresh()

and prints, for each: the HTTP status, whether the body parses, every top-level key, and for
the results body whether a module array is present, how many entries it holds, how many carry
a band, whether signal_inputs, the disposition list and the category statuses are present.

Run (from server/):
    DATABASE_URL=sqlite:///<throwaway>.db PYTHONIOENCODING=utf-8 \
        python tools/test_run147_capture.py
"""
from __future__ import annotations

import base64
import datetime as _dt
import hashlib
import json as _json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

RESULTS: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    RESULTS.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  [{detail}]" if detail else ""))


def section(title: str) -> None:
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


def finish() -> None:
    failed = [r for r in RESULTS if not r[0]]
    print(f"\nRESULT: {len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    for ok, label, detail in failed:
        print(f"  FAILED: {label}  [{detail}]")
    sys.exit(1 if failed else 0)


def main() -> None:
    from fastapi.testclient import TestClient
    from sqlalchemy import select

    import app.main as main
    from app.documents import set_extractor_override
    from app.extraction_client import StubExtractor
    from app.models import Project
    from app.research_identity import hash_access_token, new_ulid
    from app.research_models import (
        Assignment, ComputedResult, Consent, Decision, Participant, Scenario, Transition,
    )

    client = TestClient(main.app, raise_server_exceptions=False)
    Session = main.SessionFactory
    ADMIN = "r147-admin"
    LEGACY = "PRJ-R147-A"

    def raw(tag: str) -> bytes:
        return f"%PDF-1.4 R147 {tag}\n".encode()

    REC = {}
    for i, tag in enumerate(["P1", "P2"]):
        REC[hashlib.sha256(raw(tag)).hexdigest()] = ("monthly_report", {
            "earned_value": 3.0e6 + i * 1e5, "actual_cost": 3.4e6, "planned_value": 3.2e6,
            "budget_at_completion": 1.2e7,
            "report_date": f"2026-0{i + 3}-15", "document_date": f"2026-0{i + 3}-15"})
    set_extractor_override(StubExtractor(REC))

    def raw_post(payload: dict):
        return client.post("/exec", content=_json.dumps(payload),
                           headers={"Content-Type": "text/plain"})

    def post(payload: dict) -> dict:
        return raw_post(payload).json()

    section("0. THE FIXTURE (CONSTRUCTED -- not the deployment, not PRJ-002)")

    with Session() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code="R147A", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        if s.scalar(select(Project).where(Project.legacy_id == LEGACY)) is None:
            s.add(Project(legacy_id=LEGACY,
                          doc={"id": LEGACY, "name": "Run 147 capture fixture",
                               "signals": {}, "events": []}))
        s.commit()

    atok = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    made = post({"action": "adminparticipantcreate", "session_token": atok,
                 "pseudonymous_code": "R147PM", "role": "Participant",
                 "account_type": "operational"})
    pm = post({"action": "researchlogin",
               "access_token": made["access_token"]})["session_token"]
    post({"action": "adminmemberadd", "session_token": atok, "id": LEGACY,
          "participant_id": made["participant_id"], "project_role": "PM"})
    with Session() as s:
        s.add(Consent(consent_id=new_ulid(), participant_id=made["participant_id"],
                      consent_version="v1.0", method="fixture"))
        s.commit()

    for p, tag in [(1, "P1"), (2, "P2")]:
        post({"action": "projectupload", "session_token": pm, "id": LEGACY,
              "period": p, "period_end": f"2026-0{p + 2}-28",
              "documents": [{"filename": f"{tag}.pdf", "mimeType": "application/pdf",
                             "dataBase64": base64.b64encode(raw(tag)).decode()}]})
        post({"action": "projectcompute", "session_token": pm, "id": LEGACY, "period": p})

    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == LEGACY))
        sc = Scenario(scenario_id=new_ulid(), scenario_version="r147-v1",
                      project_type="construction", period_count=2,
                      evidence_package_id=LEGACY, status="frozen")
        s.add(sc)
        s.commit()
        asg = Assignment(assignment_id=new_ulid(), participant_id=made["participant_id"],
                         scenario_id=sc.scenario_id, sequence_number=1, status="active")
        s.add(asg)
        s.commit()
        dec = Decision(decision_id=new_ulid(), assignment_id=asg.assignment_id, period="P2",
                       final_submitted_at=_dt.datetime(2026, 9, 6, 7, 0,
                                                       tzinfo=_dt.timezone.utc))
        s.add(dec)
        s.commit()
        s.add(Transition(transition_id=new_ulid(), decision_id=dec.decision_id,
                         branch_id="B", branch_version="bv1", probability="1.0",
                         next_state_id=LEGACY))
        s.commit()

    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == LEGACY))
        r2 = s.scalar(select(ComputedResult).where(
            ComputedResult.project_id == proj.id, ComputedResult.period == 2,
            ComputedResult.superseded_by.is_(None)))
        STORED_MODULES = len(r2.module_results or [])
        STORED_ABSTAINED = len(r2.abstained or [])
    check(STORED_MODULES > 0,
          "the stored period-2 row holds module results before anything is served",
          f"modules={STORED_MODULES} abstained={STORED_ABSTAINED}")

    # ---------------------------------------------------------------- capture 1
    section("1. CAPTURE -- POST /exec {action: projectperiods}  (detail.js currentPeriod)")

    r1 = raw_post({"action": "projectperiods", "session_token": pm, "id": LEGACY})
    print(f"    HTTP status: {r1.status_code}")
    parsed1 = True
    try:
        b1 = r1.json()
    except Exception as e:
        b1 = {}
        parsed1 = False
        print(f"    BODY DID NOT PARSE: {e}\n    raw: {r1.text[:400]}")
    if parsed1:
        print(f"    top-level keys: {sorted(b1.keys())}")
        print(f"    ok = {b1.get('ok')!r}")
        print(f"    latest_computed_period = {b1.get('latest_computed_period')!r}")
        print(f"    computed_periods = {b1.get('computed_periods')!r}")
        print(f"    server_derived = {b1.get('server_derived')!r}")
        print(f"    error = {b1.get('error')!r}")
    check(r1.status_code == 200 and b1.get("ok") is True,
          "projectperiods answers ok:true",
          f"status={r1.status_code} ok={b1.get('ok')!r} error={b1.get('error')!r}")
    CLIENT_PERIOD = None
    if b1.get("ok") is True:
        lat = b1.get("latest_computed_period")
        CLIENT_PERIOD = None if lat is None else int(lat)
    check(CLIENT_PERIOD is not None,
          "currentPeriod() would return a period rather than null -- i.e. the results request "
          "is ISSUED AT ALL",
          f"currentPeriod -> {CLIENT_PERIOD!r}")

    # ---------------------------------------------------------------- capture 2
    section("2. CAPTURE -- POST /exec {action: projectresults}  (detail.js primeAndRefresh)")

    if CLIENT_PERIOD is None:
        print("    NOT ISSUED. currentPeriod returned null, so primeAndRefresh returns before "
              "any projectresults request exists. There is no second capture to take.")
        check(False, "a projectresults request is issued", "aborted at the period gate")
        finish()
        return

    r2h = raw_post({"action": "projectresults", "session_token": pm, "id": LEGACY,
                    "period": CLIENT_PERIOD})
    print(f"    HTTP status: {r2h.status_code}")
    try:
        b2 = r2h.json()
    except Exception as e:
        b2 = {}
        print(f"    BODY DID NOT PARSE: {e}\n    raw: {r2h.text[:400]}")
    print(f"    top-level keys: {sorted(b2.keys())}")
    print(f"    ok = {b2.get('ok')!r}   error = {b2.get('error')!r}")
    res = b2.get("result") or {}
    print(f"    result present: {bool(res)}")
    if res:
        print(f"    result keys: {sorted(res.keys())}")
    mods = res.get("module_results")
    print(f"    module_results present: {mods is not None}   is-array: {isinstance(mods, list)}"
          f"   entries: {len(mods) if isinstance(mods, list) else 'n/a'}")
    banded = [m for m in (mods or []) if isinstance(m, dict) and m.get("band")]
    print(f"    entries carrying a band: {len(banded)}")
    print(f"    abstained: {len(res.get('abstained') or [])}")
    si = res.get("signal_inputs")
    print(f"    signal_inputs present: {si is not None}  entries: "
          f"{len(si) if isinstance(si, dict) else 'n/a'}")
    disp = res.get("decision_dispositions")
    print(f"    decision_dispositions present: {disp is not None}  entries: "
          f"{len(disp) if isinstance(disp, list) else 'n/a'}")
    cats = res.get("category_statuses")
    print(f"    category_statuses present: {cats is not None}  entries: "
          f"{len(cats) if isinstance(cats, dict) else 'n/a'}")
    print(f"    period = {res.get('period')!r}  period_substituted = "
          f"{b2.get('period_substituted')!r}  period_requested = {b2.get('period_requested')!r}")

    check(r2h.status_code == 200 and b2.get("ok") is True,
          "projectresults answers ok:true", f"status={r2h.status_code} "
          f"ok={b2.get('ok')!r} error={b2.get('error')!r}")
    check(isinstance(mods, list) and len(mods) == STORED_MODULES,
          f"the response carries all {STORED_MODULES} stored module rows",
          str(len(mods) if isinstance(mods, list) else None))
    check(bool(si), "the response carries the signal inputs", str(len(si or {})))
    check(bool(disp), "the response carries the disposition list", str(len(disp or [])))
    check(bool(cats), "the response carries the category statuses", str(len(cats or {})))

    section("3. THE SPLIT")
    if b2.get("ok") is True and isinstance(mods, list) and mods:
        print("    THE SERVER SENDS IT. Both requests succeed and the results body carries the")
        print("    module array, the signal inputs, the dispositions and the category statuses.")
        print("    On this fixture the loss is therefore NOT upstream of the wire.")
    else:
        print("    THE SERVER DOES NOT SEND IT. The seam is upstream of the wire.")

    finish()


if __name__ == "__main__":
    main()
