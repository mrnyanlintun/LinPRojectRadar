#!/usr/bin/env python3
"""
RUN 146, PROOF 3: THE PAGE ITSELF, IN A BROWSER, AGAINST THE REAL BACKEND.

Run with cwd = <worktree>/server, against a THROWAWAY database only:

    DATABASE_URL=sqlite:///<throwaway>.db SESSION_SECRET=... \
        python tools/test_run146_browser.py

WHY IT IS BUILT THIS WAY. Run 142 and Run 144 both established that a check against the SERVED
PAYLOAD can pass while the page shows nothing, and the fault this run fixes lives in exactly
that gap: `documents.a_projectresults` returned an error and `detail.js primeAndRefresh` dropped
it silently, so the page rendered `facade.live_statuses`'s four-field list projection alone.
Nothing short of loading the real index.html, the real app.js, the real detail.js and the real
taxonomy.js against a real running backend can show that. So this runs uvicorn on a throwaway
database, seeds the fixture through the real endpoints, logs a real participant in, opens the
real project detail page in headless Chromium and reads what the browser LAID OUT.

THE FIXTURE IS CONSTRUCTED and this file says so plainly: PRJ-002 is not reachable from this
container. What is reconstructed is its STATE -- two computed periods and a research assignment
whose derived period runs past the last period that holds a row.

TWO PASSES. The page is measured with the fault INJECTED (the scenario dropped from the
derivation and the read-path fallback removed) and then with the code as shipped. The first pass
must show the blank page; the second must show the module rows, the abstentions, the signal
inputs and the disposition list. A proof that only ever sees the fixed state proves nothing.
"""
from __future__ import annotations

import base64
import datetime as _dt
import hashlib
import json as _json
import os
import socket
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

CHROME = os.environ.get("RUN146_CHROME") or (
    "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell")

RESULTS: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    RESULTS.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  [{detail}]" if detail else ""))


def section(title: str) -> None:
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


LEGACY = "PRJ-R146-B"
ADMIN = "r146b-admin"


def raw(tag: str) -> bytes:
    return f"%PDF-1.4 R146B {tag}\n".encode()


def seed() -> str:
    """Build the fixture through the real endpoints. Returns the PM's session token."""
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

    REC = {}
    for i, tag in enumerate(["P1", "P2"]):
        REC[hashlib.sha256(raw(tag)).hexdigest()] = ("monthly_report", {
            "earned_value": 3.0e6 + i * 1e5, "actual_cost": 3.4e6, "planned_value": 3.2e6,
            "budget_at_completion": 1.2e7,
            "report_date": f"2026-0{i + 3}-15", "document_date": f"2026-0{i + 3}-15"})
    set_extractor_override(StubExtractor(REC))

    client = TestClient(main.app, raise_server_exceptions=False)
    Session = main.SessionFactory

    def post(payload):
        return client.post("/exec", content=_json.dumps(payload),
                           headers={"Content-Type": "text/plain"}).json()

    with Session() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code="R146B", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        if s.scalar(select(Project).where(Project.legacy_id == LEGACY)) is None:
            s.add(Project(legacy_id=LEGACY,
                          doc={"id": LEGACY, "name": "Run 146 browser reconstruction",
                               "signals": {}, "events": []}))
        s.commit()

    atok = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    made = post({"action": "adminparticipantcreate", "session_token": atok,
                 "pseudonymous_code": "R146BPM", "role": "Participant",
                 "account_type": "operational"})
    pm = post({"action": "researchlogin", "access_token": made["access_token"]})["session_token"]
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
        sc = Scenario(scenario_id=new_ulid(), scenario_version="r146b-v1",
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
        r2 = s.scalar(select(ComputedResult).where(
            ComputedResult.project_id == proj.id, ComputedResult.period == 2,
            ComputedResult.superseded_by.is_(None)))
        counts = (len(r2.module_results or []), len(r2.abstained or []))
    return pm, counts


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def observe(base: str, token: str, label: str) -> dict:
    """Open the real detail page as the PM and read what the browser laid out."""
    from playwright.sync_api import sync_playwright

    out: dict = {"label": label}
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": 1280, "height": 1000})
        errors: list[str] = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(base + "/index.html", wait_until="load")
        pg.evaluate("t => sessionStorage.setItem('og-session-token', t)", token)
        pg.goto(base + "/index.html", wait_until="load")
        pg.wait_for_timeout(2500)
        pg.evaluate("id => window.LinApp.openDetail(id)", LEGACY)
        pg.wait_for_timeout(4000)
        # Expand every collapsible section, then every <details>. Both renderers hide
        # detail by default (Run 141, Run 142), so a page read without this shows nothing
        # whatever it holds.
        pg.evaluate("""() => {
            document.querySelectorAll('[id^="body-"]').forEach(b => {
                if (b.style.display === 'none') {
                    try { window.toggleSection(b.id.slice(5)); } catch (e) {}
                }
            });
        }""")
        pg.wait_for_timeout(3000)
        pg.evaluate("() => document.querySelectorAll('details').forEach(d => { d.open = true; })")
        pg.wait_for_timeout(1500)
        out["text"] = pg.evaluate("() => document.body.innerText")
        out["client_row"] = pg.evaluate("""(id) => {
            const p = (window.LinStore && LinStore.getCached) ? LinStore.getCached(id) : null;
            const r = (p && window.LinResults) ? LinResults.rowFor(p) : null;
            if (!r) return null;
            return {
                period: r.period,
                module_results: Array.isArray(r.module_results) ? r.module_results.length : null,
                abstained: Array.isArray(r.abstained) ? r.abstained.length : null,
                signal_inputs: r.signal_inputs ? Object.keys(r.signal_inputs).length : null,
                dispositions: Array.isArray(r.decision_dispositions)
                    ? r.decision_dispositions.length : null,
                categories: r.category_statuses ? Object.keys(r.category_statuses).length : null,
                project_status: r.project_status || null
            };
        }""", LEGACY)
        out["disposition_select"] = pg.evaluate(
            "() => !!document.querySelector('select.disposition')")
        m = __import__("re").search(
            r"(\d+) of (\d+) modules in service assert a band[^.]*\.", out["text"])
        out["network_line"] = m.group(0) if m else None
        out["no_data_count"] = pg.evaluate(
            "() => (document.body.innerText.match(/No data/g) || []).length")
        out["errors"] = errors[:3]
        out["sections"] = pg.evaluate("""() => Array.from(document.querySelectorAll('[data-section]')).map(e => e.getAttribute('data-section')+':'+(e.className||''))""")
        pg.screenshot(path=os.path.join(SHOTS, f"run146-{label}.png"), full_page=False)
        b.close()
    return out


SHOTS = os.environ.get("RUN135_ARTIFACT_SCRATCH") or os.path.join(ROOT, ".artifact_scratch")
SHOTS = os.path.join(SHOTS, "run146")
os.makedirs(SHOTS, exist_ok=True)


def main() -> None:
    import uvicorn

    import app.documents as D
    import app.main as main_mod
    import app.research_decision as RD

    token, (n_mod, n_abs) = seed()
    print(f"  fixture: the stored period-2 row holds {n_mod} module rows and {n_abs} abstentions")

    port = free_port()
    base = f"http://127.0.0.1:{port}"
    cfg = uvicorn.Config(main_mod.app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(cfg)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.1)

    try:
        # ---------------------------------------------------------------- pass 1: the fault
        section("PASS 1. THE FAULT INJECTED: the scenario dropped from the derivation and the "
                "read-path fallback removed")
        _real_cp, _real_periods = RD.current_period, D._computed_periods
        RD.current_period = lambda s, a, sc=None: _real_cp(s, a)
        D._computed_periods = lambda s, p: []
        try:
            broken = observe(base, token, "broken")
        finally:
            RD.current_period, D._computed_periods = _real_cp, _real_periods

        bt, br = broken["text"], broken["client_row"] or {}
        print(f"    client row: {br}")
        check(br.get("module_results") is None,
              "the page holds NO module rows at all -- not an empty list, no field",
              str(br.get("module_results")))
        check((br.get("categories") or 0) > 0 and bool(br.get("project_status")),
              "while the category postures and the project status ARE on the page",
              f"{br.get('categories')} categories, status={br.get('project_status')!r}")
        check("has not been read back yet" in bt,
              "the decision card says the analysis has not been read back yet")
        check(broken["disposition_select"] is False,
              "there is no disposition control in the DOM")
        check("No extracted values cached this session" in bt
              or "No documents ingested" in bt,
              "and the signal-inputs panel shows no extracted values")
        print(f"    'No data' occurrences on the broken page: {broken['no_data_count']}")
        print(f"    Signal Network line: {broken.get('network_line')!r}")
        check(bool(broken.get("network_line")) and broken["network_line"].startswith("0 of "),
              "the Signal Network line reads 0 of N modules assert a band",
              str(broken.get("network_line")))

        # ---------------------------------------------------------------- pass 2: as shipped
        section("PASS 2. THE CODE AS SHIPPED: the same fixture, the same page")
        fixed = observe(base, token, "fixed")
        ft, fr = fixed["text"], fixed["client_row"] or {}
        print(f"    client row: {fr}")
        check(fr.get("module_results") == n_mod,
              f"the page holds all {n_mod} module rows", str(fr.get("module_results")))
        check(fr.get("abstained") == n_abs,
              f"and all {n_abs} abstentions", str(fr.get("abstained")))
        check((fr.get("signal_inputs") or 0) > 0,
              "the signal inputs reach the page", str(fr.get("signal_inputs")))
        check("No extracted values cached this session" not in ft,
              "so the signal-inputs panel no longer says nothing is cached")
        check(fixed["disposition_select"] is True,
              "the decision card offers a disposition control")
        check((fr.get("dispositions") or 0) > 0,
              "backed by a served disposition list", str(fr.get("dispositions")))
        check("has not been read back yet" not in ft,
              "and no longer says the analysis has not been read back yet")
        check(fixed["no_data_count"] < broken["no_data_count"]
              or broken["no_data_count"] == 0,
              "the ledger shows fewer 'No data' rows than it did with the fault injected",
              f"{fixed['no_data_count']} vs {broken['no_data_count']}")
        check(fr.get("project_status") == br.get("project_status")
              and fr.get("categories") is not None,
              "and the project status is unchanged by the fix",
              f"{br.get('project_status')!r} -> {fr.get('project_status')!r}")
        print(f"    Signal Network line: {fixed.get('network_line')!r}")
        check(bool(fixed.get("network_line"))
              and not fixed["network_line"].startswith("0 of "),
              "the Signal Network line now reads the real counts",
              str(fixed.get("network_line")))
        print(f"    screenshots: {SHOTS}")
    finally:
        server.should_exit = True
        t.join(timeout=10)

    failed = [r for r in RESULTS if not r[0]]
    print(f"\nRESULT: {len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    for ok, label, detail in failed:
        print(f"  FAILED: {label}  [{detail}]")
    sys.exit(1 if failed else 0)


main()
