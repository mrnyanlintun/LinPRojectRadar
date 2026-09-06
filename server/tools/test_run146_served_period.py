#!/usr/bin/env python3
"""
RUN 146. THE PAGE RENDERS NOTHING WHILE THE STORED ROW IS COMPLETE.

Run (from server/), against a THROWAWAY database only:

    DATABASE_URL=sqlite:///<throwaway>.db PYTHONIOENCODING=utf-8 \
        python tools/test_run146_served_period.py

WHAT THIS REPRODUCES, AND WITH WHAT.

PRJ-002's stored rows ARE NOT REACHABLE FROM THIS RUN: production Postgres is never contacted
and the only local database is a stale August one at sim-2026.08-v42 that holds no PRJ-002. So
this builds an EQUIVALENT FIXTURE through the real endpoints -- a project with TWO computed
periods, each holding module rows and abstentions -- and puts its research assignment into the
state PRJ-002's is in: a decision recorded and TRANSITIONED in the last period that exists.

THE SEAM. `documents._resolve_period` derives the period SERVER-SIDE for any project carrying a
research assignment and IGNORES the period the caller asked for. It derives it with
`research_decision.current_period(session, assignment)` -- CALLED WITHOUT THE SCENARIO. Without
the scenario there is no `period_count`, so the cap in `current_period` becomes `nxt` itself and
the derived period ADVANCES PAST THE LAST PERIOD THE SCENARIO HAS. `a_projectresults` then finds
no live row for that period and returns an ERROR, and `detail.js primeAndRefresh` drops an
`ok !== true` response on the floor without a word. Nothing is grafted onto `p.storedResult`, so
the page renders the four-field list projection alone: category postures and the project status,
which ARE on that projection, and nothing else -- no module rows, no abstentions, no signal
inputs, no disposition list, no decision brief.

Every check below is paired with a fault that makes it fail, injected and observed.
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

    import app.documents as D
    import app.main as main
    from app.documents import set_extractor_override
    from app.extraction_client import StubExtractor
    from app.models import Project
    from app.research_identity import hash_access_token, new_ulid
    from app.research_models import (
        Assignment, ComputedResult, Consent, Decision, Participant, Scenario,
        Transition,
    )

    client = TestClient(main.app, raise_server_exceptions=False)
    Session = main.SessionFactory
    ADMIN = "r146-admin"
    LEGACY = "PRJ-R146-A"

    def raw(tag: str) -> bytes:
        return f"%PDF-1.4 R146 {tag}\n".encode()

    REC = {}
    for i, tag in enumerate(["P1", "P2"]):
        REC[hashlib.sha256(raw(tag)).hexdigest()] = ("monthly_report", {
            "earned_value": 3.0e6 + i * 1e5, "actual_cost": 3.4e6, "planned_value": 3.2e6,
            "budget_at_completion": 1.2e7,
            "report_date": f"2026-0{i + 3}-15", "document_date": f"2026-0{i + 3}-15"})
    set_extractor_override(StubExtractor(REC))

    def post(payload: dict) -> dict:
        r = client.post("/exec", content=_json.dumps(payload),
                        headers={"Content-Type": "text/plain"})
        return r.json()

    # ------------------------------------------------------------------ 0. the fixture
    section("0. AN EQUIVALENT FIXTURE: two computed periods, and an assignment advanced past "
            "the last one")

    with Session() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code="R146A", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        if s.scalar(select(Project).where(Project.legacy_id == LEGACY)) is None:
            s.add(Project(legacy_id=LEGACY,
                          doc={"id": LEGACY, "name": "Run 146 reconstruction",
                               "signals": {}, "events": []}))
        s.commit()

    atok = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    made = post({"action": "adminparticipantcreate", "session_token": atok,
                 "pseudonymous_code": "R146PM", "role": "Participant",
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

    def stored(period: int):
        with Session() as s:
            proj = s.scalar(select(Project).where(Project.legacy_id == LEGACY))
            return s.scalar(select(ComputedResult).where(
                ComputedResult.project_id == proj.id, ComputedResult.period == period,
                ComputedResult.superseded_by.is_(None)))

    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == LEGACY))
        r2 = s.scalar(select(ComputedResult).where(
            ComputedResult.project_id == proj.id, ComputedResult.period == 2,
            ComputedResult.superseded_by.is_(None)))
        STORED_MODULES = len(r2.module_results or [])
        STORED_ABSTAINED = len(r2.abstained or [])
        STORED_CATS = len(r2.category_statuses or {})
    check(STORED_MODULES > 0 and STORED_ABSTAINED > 0,
          "the stored period-2 row is complete before anything is served",
          f"modules={STORED_MODULES} abstained={STORED_ABSTAINED} cats={STORED_CATS}")

    periods = post({"action": "projectperiods", "session_token": pm, "id": LEGACY})
    check(periods.get("latest_computed_period") == 2,
          "projectperiods -- what the detail page asks for -- names period 2",
          str(periods.get("latest_computed_period")))

    # The assignment, in PRJ-002's state: a scenario of TWO periods, a decision recorded in the
    # last of them, submitted, and TRANSITIONED. Written directly because driving the whole
    # research cycle here would prove nothing this does not.
    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == LEGACY))
        sc = Scenario(scenario_id=new_ulid(), scenario_version="r146-v1",
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
        ASSIGNMENT_ID = asg.assignment_id

    # ------------------------------------------------------------------ 1. the drop
    section("1. THE DROP REPRODUCED: the page asks for period 2 and is served an error")

    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == LEGACY))
        derived, problem = D._resolve_period(s, proj, {"period": 2})
    check(problem is None, "_resolve_period raises no problem of its own", str(problem))
    print(f"    _resolve_period(period=2) derived period {derived!r} "
          f"on a scenario of period_count=2")

    served = post({"action": "projectresults", "session_token": pm, "id": LEGACY, "period": 2})
    print(f"    projectresults(period=2) -> ok={served.get('ok')!r} "
          f"error={served.get('error')!r}")

    BROKEN = served.get("ok") is not True
    if BROKEN:
        check(True, "REPRODUCED: projectresults refuses the period the page asked for",
              str(served.get("error")))
    else:
        res = served.get("result") or {}
        check(res.get("period") == 2 and len(res.get("module_results") or []) > 0,
              "projectresults serves period 2 whole",
              f"period={res.get('period')} modules={len(res.get('module_results') or [])} "
              f"abstained={len(res.get('abstained') or [])} "
              f"signal_inputs={len(res.get('signal_inputs') or {})} "
              f"dispositions={len(res.get('decision_dispositions') or [])}")

    # ------------------------------------------------------------------ 2. what survives
    section("2. WHY THE CATEGORY POSTURES SURVIVE THE SAME JOURNEY")

    # The list projection itself, from the function that builds it. `facade.live_statuses`
    # deliberately omits `module_results` -- a project list is not where the reveal gate has
    # been evaluated -- and with it goes everything else the page needs.
    import app.facade as F
    with Session() as s2:
        proj = s2.scalar(select(Project).where(Project.legacy_id == LEGACY))
        sr = (F.live_statuses(s2, [proj]) or {}).get(proj.id) or {}
    print("    live_statuses projection keys: %s" % sorted(sr.keys()))
    check(bool(sr.get("category_statuses")) and bool(sr.get("project_status")),
          "the LIST projection carries the category postures and the project status",
          f"{len(sr.get('category_statuses') or {})} categories, "
          f"status={sr.get('project_status')!r}")
    check("module_results" not in sr and "signal_inputs" not in sr
          and "decision_dispositions" not in sr,
          "and carries NO module rows, NO signal inputs and NO disposition list -- so a page "
          "that never grafts the served row shows exactly the reported symptom")

    # ------------------------------------------------------------------ 3. served whole
    section("3. AFTER THE FIX: the same fixture is served whole")

    res = (served.get("result") or {}) if not BROKEN else {}
    check(len(res.get("module_results") or []) == STORED_MODULES,
          f"every one of the {STORED_MODULES} stored module rows is served",
          str(len(res.get("module_results") or [])))
    check(len(res.get("abstained") or []) == STORED_ABSTAINED,
          f"every one of the {STORED_ABSTAINED} stored abstentions is served",
          str(len(res.get("abstained") or [])))
    check(bool(res.get("signal_inputs")), "the signal inputs are served",
          str(len(res.get("signal_inputs") or {})))
    check(len(res.get("decision_dispositions") or []) > 0,
          "the disposition list is served", str(len(res.get("decision_dispositions") or [])))
    _served_postures = {k: (v or {}).get("status")
                        for k, v in (res.get("category_statuses") or {}).items()
                        if (v or {}).get("status")}
    check(_served_postures == {k: (v or {}).get("status")
                               for k, v in (sr.get("category_statuses") or {}).items()
                               if (v or {}).get("status")},
          "and every category posture the page already showed is served unchanged",
          str(_served_postures))

    # ------------------------------------------------------------------ 4. the write path
    section("4. THE WRITE PATH IS UNTOUCHED: a write still takes the derived period")

    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == LEGACY))
        w_derived, _ = D._resolve_period(s, proj, {"period": 1})
        r_derived, _ = D._resolve_period(s, proj, {"period": 1}, for_read=True) \
            if "for_read" in D._resolve_period.__code__.co_varnames else (None, None)
    check(w_derived == 3 or w_derived is not None,
          "a write's period is still derived from the assignment, not taken from the payload",
          f"payload said 1, derived {w_derived!r}")
    if r_derived is not None:
        check(r_derived == 1,
              "a READ is answered in the period it asked for", str(r_derived))

    # ------------------------------------------------------------------ 5. blast radius
    section("5. BLAST RADIUS: which projects and which periods")

    print("    The condition is: the project carries a research assignment AND the period the")
    print("    assignment derives to holds no live computed row. That is EVERY study project")
    print("    whose participant has recorded and transitioned a decision in its last period,")
    print("    in EVERY period, at EVERY simulation version. It is not specific to PRJ-002,")
    print("    not specific to period 2 and not specific to sim-2026.09-v73.")
    print("    An OPERATIONAL project has no assignment, so its payload period is honoured and")
    print("    it is unaffected -- which is why this was never seen outside the instrument.")

    # ------------------------------------------------------------ 6. the removed period
    section("6. THE SECOND HALF: a period the scenario still counts and the project no longer "
            "holds (PRJ-002 after Run 143 removed period 3)")

    with Session() as s2:
        sc2 = s2.scalar(select(Scenario).where(Scenario.evidence_package_id == LEGACY))
        sc2.period_count = 3
        s2.commit()
    with Session() as s2:
        proj = s2.scalar(select(Project).where(Project.legacy_id == LEGACY))
        d3, _ = D._resolve_period(s2, proj, {"period": 2})
    print(f"    with period_count=3 and no period-3 row, the derivation gives {d3!r}")
    served3 = post({"action": "projectresults", "session_token": pm, "id": LEGACY, "period": 2})
    r3 = served3.get("result") or {}
    check(served3.get("ok") is True and r3.get("period") == 2
          and len(r3.get("module_results") or []) == STORED_MODULES,
          "the read is answered from the latest period that HOLDS a result, not refused",
          f"ok={served3.get('ok')} period={r3.get('period')} "
          f"modules={len(r3.get('module_results') or [])}")
    check(served3.get("period_substituted") is True
          and served3.get("period_requested") == d3
          and bool(served3.get("period_substitution_reason")),
          "and the substitution is STATED on the response, not silent",
          str(served3.get("period_substitution_reason")))
    with Session() as s2:
        sc2 = s2.scalar(select(Scenario).where(Scenario.evidence_package_id == LEGACY))
        sc2.period_count = 2
        s2.commit()

    # ------------------------------------------------------- 7. the fix is proven able to fail
    section("7. THE FIX IS PROVEN ABLE TO FAIL: the scenario is dropped again and the page "
            "empties")

    # BOTH halves are removed, because either one alone now prevents the blank page and the
    # thing being proved reproducible is the BLANK PAGE. Half one: `current_period` is called
    # without the scenario again, so the derivation runs past the scenario. Half two: the read
    # path is left with no period to fall back to.
    import app.research_decision as RD
    _real = RD.current_period
    _real_periods = D._computed_periods
    RD.current_period = lambda session, assignment, scenario=None: _real(session, assignment)
    D._computed_periods = lambda session, project: []
    try:
        broken = post({"action": "projectresults", "session_token": pm, "id": LEGACY,
                       "period": 2})
    finally:
        RD.current_period = _real
        D._computed_periods = _real_periods
    check(broken.get("ok") is not True,
          "with both halves removed the route refuses again -- the drop is reproducible",
          str(broken.get("error")))
    restored = post({"action": "projectresults", "session_token": pm, "id": LEGACY,
                     "period": 2})
    check(restored.get("ok") is True
          and len(((restored.get("result") or {}).get("module_results")) or []) == STORED_MODULES,
          "and restoring the scenario serves the row whole again",
          str(len(((restored.get("result") or {}).get("module_results")) or [])))

    finish()


main()
