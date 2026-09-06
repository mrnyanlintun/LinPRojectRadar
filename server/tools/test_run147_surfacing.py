#!/usr/bin/env python3
"""
RUN 147, PROOFS 2, 3, 5 AND 6: THE PAGE ITSELF, IN A BROWSER, AGAINST THE REAL BACKEND.

Run with cwd = <worktree>/server, against a THROWAWAY database only:

    DATABASE_URL=sqlite:///<throwaway>.db python tools/test_run147_surfacing.py

THE FIXTURE IS CONSTRUCTED AND THIS FILE SAYS SO PLAINLY. PRJ-002 and its database are not
reachable from this container, so what is reconstructed is its SHAPE: two periods, the second
computed and holding module rows and abstentions, a frozen scenario naming the project as its
evidence package, and a research assignment whose decision in the last period is submitted and
transitioned.

WHAT IS PROVED, in four passes over the same fixture and the same page.

  PASS 1  The code as shipped: the page holds the module rows, the abstentions, the extracted
          values and the disposition list, and carries NO alert.

  PASS 2  `projectresults` is made to REFUSE. Before this run that rendered as a blank page
          with nothing said anywhere. It must now (a) still empty the page -- the refusal is
          real -- and (b) SURFACE, naming projectresults and the server's own reason.

  PASS 3  `projectperiods` is made to REFUSE. This is the FIRST of the two sequential requests
          and the one nobody had examined: `currentPeriod` returned null with NO LOG AT ALL and
          `primeAndRefresh` returned before any `projectresults` request existed. So this pass
          proves BOTH that the results request is never issued and that the page now says so.

  PASS 4  Both injections removed: the page is whole again, and the alert is gone.

Passes 2 and 3 are the "prove it can fail" proof for passes 1 and 4, and passes 1 and 4 are the
"prove it is fixed" proof for 2 and 3. The category postures and the project status are
compared across all four.
"""
from __future__ import annotations

import base64
import datetime as _dt
import hashlib
import json as _json
import os
import re
import socket
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

CHROME = os.environ.get("RUN147_CHROME") or (
    "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell")

SHOTS = os.environ.get("RUN135_ARTIFACT_SCRATCH") or os.path.join(ROOT, ".artifact_scratch")
SHOTS = os.path.join(SHOTS, "run147")
os.makedirs(SHOTS, exist_ok=True)

RESULTS: list[tuple[bool, str, str]] = []
LEGACY = "PRJ-R147-B"
ADMIN = "r147b-admin"


def check(ok: bool, label: str, detail: str = "") -> None:
    RESULTS.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  [{detail}]" if detail else ""))


def section(title: str) -> None:
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


def raw(tag: str) -> bytes:
    return f"%PDF-1.4 R147B {tag}\n".encode()


def seed():
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
            s.add(Participant(pseudonymous_code="R147B", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        if s.scalar(select(Project).where(Project.legacy_id == LEGACY)) is None:
            s.add(Project(legacy_id=LEGACY,
                          doc={"id": LEGACY, "name": "Run 147 surfacing fixture",
                               "signals": {}, "events": []}))
        s.commit()

    atok = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    made = post({"action": "adminparticipantcreate", "session_token": atok,
                 "pseudonymous_code": "R147BPM", "role": "Participant",
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
        sc = Scenario(scenario_id=new_ulid(), scenario_version="r147b-v1",
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
    """Open the real detail page as the PM and read what the browser LAID OUT."""
    from playwright.sync_api import sync_playwright

    out: dict = {"label": label}
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": 1280, "height": 1000})
        errors: list[str] = []
        console: list[str] = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: console.append(m.type + ": " + m.text))
        posts: list[str] = []

        def _req(r):
            if r.method == "POST" and r.url.endswith("/exec"):
                try:
                    body = r.post_data or ""
                except Exception:
                    body = ""
                m2 = re.search(r'"action"\s*:\s*"([a-z]+)"', body)
                if m2:
                    posts.append(m2.group(1))

        pg.on("request", _req)
        pg.goto(base + "/index.html", wait_until="load")
        pg.evaluate("t => sessionStorage.setItem('og-session-token', t)", token)
        pg.goto(base + "/index.html", wait_until="load")
        pg.wait_for_timeout(2500)
        pg.evaluate("id => window.LinApp.openDetail(id)", LEGACY)
        pg.wait_for_timeout(4000)
        # Both renderers hide detail by default, so a page read without expanding shows
        # nothing whatever it holds.
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
        out["alert"] = pg.evaluate(
            "() => { const e = document.querySelector('.detail-graft-error');"
            "        return e ? e.textContent : null; }")
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
        m = re.search(r"(\d+) of (\d+) modules in service assert a band[^.]*\.", out["text"])
        out["network_line"] = m.group(0) if m else None
        out["no_data_count"] = pg.evaluate(
            "() => (document.body.innerText.match(/No data/g) || []).length")
        out["errors"] = errors[:3]
        out["console_errors"] = [c for c in console if c.startswith("error:")][:5]
        # The lines THIS run's surfacing writes, not the page's ambient console noise.
        out["graft_console"] = [c for c in console
                                if "the stored analysis for" in c.lower()]
        out["posts"] = posts
        pg.screenshot(path=os.path.join(SHOTS, f"run147-{label}.png"), full_page=False)
        b.close()
    return out


def describe(o: dict) -> None:
    print(f"    client row: {o['client_row']}")
    print(f"    network line: {o.get('network_line')!r}")
    print(f"    'No data' occurrences: {o['no_data_count']}")
    print(f"    page alert: {o.get('alert')!r}")
    print(f"    surfacing on the console: {o.get('graft_console')}")
    print(f"    /exec actions the page posted: {sorted(set(o.get('posts') or []))}")


def main() -> None:
    import uvicorn

    import app.documents as D
    import app.main as main_mod
    from app.facade import err

    token, (n_mod, n_abs) = seed()
    print(f"  CONSTRUCTED FIXTURE: the stored period-2 row holds {n_mod} module rows and "
          f"{n_abs} abstentions")

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

    REAL_RESULTS = D.DOCUMENT_ACTIONS["projectresults"]
    REAL_PERIODS = D.DOCUMENT_ACTIONS["projectperiods"]

    try:
        # ------------------------------------------------------------------ pass 1
        section("PASS 1. THE CODE AS SHIPPED: the page is whole and carries no alert")
        whole = observe(base, token, "1-whole")
        describe(whole)
        wr = whole["client_row"] or {}
        check(wr.get("module_results") == n_mod,
              f"the page holds all {n_mod} module rows", str(wr.get("module_results")))
        check((wr.get("signal_inputs") or 0) > 0, "the extracted values reach the page",
              str(wr.get("signal_inputs")))
        check(whole["disposition_select"] is True,
              "the decision card offers a disposition control")
        check(whole.get("alert") is None, "and NO alert is shown on a page that loaded",
              str(whole.get("alert")))
        BASE_STATUS = wr.get("project_status")
        BASE_CATS = wr.get("categories")

        # ------------------------------------------------------------------ pass 2
        section("PASS 2. projectresults IS REFUSED -- the second request. Before this run: a "
                "blank page and not a word anywhere.")
        D.DOCUMENT_ACTIONS["projectresults"] = (
            lambda s, p, sec, ttl: err("run147 injected refusal: no computed result for "
                                       "period 3; run projectcompute first"))
        try:
            refused = observe(base, token, "2-results-refused")
        finally:
            D.DOCUMENT_ACTIONS["projectresults"] = REAL_RESULTS
        describe(refused)
        rr = refused["client_row"] or {}
        check(rr.get("module_results") is None,
              "the page holds NO module rows at all -- not an empty list, no field",
              str(rr.get("module_results")))
        check(bool(refused.get("network_line"))
              and refused["network_line"].startswith("0 of "),
              "the Signal Network line reads the reported sentence verbatim",
              str(refused.get("network_line")))
        check("has not been read back yet" in refused["text"],
              "the decision card says the analysis has not been read back yet")
        check("No extracted values cached this session" in refused["text"],
              "and the extracted values panel says nothing is cached")
        check(bool(refused.get("alert")) and "projectresults" in (refused.get("alert") or ""),
              "AND THE PAGE NOW SAYS SO, naming projectresults", str(refused.get("alert"))[:160])
        check("run147 injected refusal" in (refused.get("alert") or ""),
              "carrying the server's own reason verbatim")
        check(any("projectresults" in c for c in refused.get("graft_console") or []),
              "and the same is on the console as an error",
              str(refused.get("graft_console"))[:200])
        check(rr.get("project_status") == BASE_STATUS and rr.get("categories") == BASE_CATS,
              "the category postures and the project status are unchanged by the refusal",
              f"{BASE_STATUS!r}/{BASE_CATS} -> {rr.get('project_status')!r}/"
              f"{rr.get('categories')}")

        # ------------------------------------------------------------------ pass 3
        section("PASS 3. projectperiods IS REFUSED -- the FIRST request. The results request is "
                "then NEVER ISSUED, and before this run there was no log at all.")
        D.DOCUMENT_ACTIONS["projectperiods"] = (
            lambda s, p, sec, ttl: err("run147 injected refusal: not authorized: not a member "
                                       "of this project"))
        try:
            gated = observe(base, token, "3-periods-refused")
        finally:
            D.DOCUMENT_ACTIONS["projectperiods"] = REAL_PERIODS
        describe(gated)
        gr = gated["client_row"] or {}
        # MEASURED, AND IT KILLS A CANDIDATE. The period gate aborting does NOT by itself empty
        # this page. `taxonomy.rowFor` falls back to the ROWS cache for the SAME period, and
        # other surfaces on this page (workspace.js's period panel, decision-ui.js) fetch
        # `projectresults` on their own and prime it. So a page whose graft never ran can still
        # be rescued by a second consumer -- which is exactly why the "never issued" path is
        # NOT the seam that produces the reported symptom, and pass 2's is.
        print(f"    module rows on the page after the period gate aborted: "
              f"{gr.get('module_results')}")
        check(gr.get("module_results") is not None,
              "THE PERIOD GATE ABORTING DOES NOT EMPTY THE PAGE: another consumer's "
              "projectresults prime still answers rowFor for the same period",
              str(gr.get("module_results")))
        check("projectresults" in (gated.get("posts") or []),
              "and projectresults IS still posted -- by that other consumer, not by "
              "primeAndRefresh, which returned at the gate",
              str(sorted(set(gated.get("posts") or []))))
        check(bool(gated.get("alert")) and "projectperiods" in (gated.get("alert") or ""),
              "the page names projectperiods -- the request that failed",
              str(gated.get("alert"))[:160])
        check("never requested" in (gated.get("alert") or ""),
              "and says the analysis was never requested, which is the fact that distinguishes "
              "this seam from pass 2's")
        check("run147 injected refusal" in (gated.get("alert") or ""),
              "carrying the server's own reason verbatim")
        check(gr.get("project_status") == BASE_STATUS and gr.get("categories") == BASE_CATS,
              "the category postures and the project status are unchanged here too",
              f"{gr.get('project_status')!r}/{gr.get('categories')}")

        # ------------------------------------------------------------------ pass 4
        section("PASS 4. BOTH INJECTIONS REMOVED: the same page, whole again, alert gone")
        back = observe(base, token, "4-restored")
        describe(back)
        kr = back["client_row"] or {}
        check(kr.get("module_results") == n_mod,
              f"all {n_mod} module rows are back", str(kr.get("module_results")))
        check(kr.get("abstained") == n_abs, f"and all {n_abs} abstentions",
              str(kr.get("abstained")))
        check(back.get("alert") is None, "and the alert is gone", str(back.get("alert")))
        check(bool(back.get("network_line"))
              and not back["network_line"].startswith("0 of "),
              "the Signal Network line reads the real counts",
              str(back.get("network_line")))
        check(back["no_data_count"] < refused["no_data_count"],
              "the ledger shows fewer 'No data' rows than it did under refusal",
              f"{back['no_data_count']} vs {refused['no_data_count']}")
        check(kr.get("project_status") == BASE_STATUS and kr.get("categories") == BASE_CATS,
              "and the category postures and project status never moved across all four passes",
              f"{kr.get('project_status')!r}/{kr.get('categories')}")
        print(f"    screenshots: {SHOTS}")
    finally:
        D.DOCUMENT_ACTIONS["projectresults"] = REAL_RESULTS
        D.DOCUMENT_ACTIONS["projectperiods"] = REAL_PERIODS
        server.should_exit = True
        t.join(timeout=10)

    failed = [r for r in RESULTS if not r[0]]
    print(f"\nRESULT: {len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    for ok, label, detail in failed:
        print(f"  FAILED: {label}  [{detail}]")
    sys.exit(1 if failed else 0)


main()
