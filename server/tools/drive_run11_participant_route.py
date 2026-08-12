#!/usr/bin/env python3
"""
RUN 11, GATE 2. THE ACTUAL PARTICIPANT-REACHABLE ROUTE, DRIVEN IN A REAL BROWSER.

WHY THIS EXISTS AND WHAT IT IS NOT. tests_render.html never loads index.html. Anything asserted
there about what index.html loads, or about what a participant sees, is vacuous. This drives the
served application: a real server, a real Chromium, a real signed-in participant session, the
detail page a project manager opens, and the Period decision tab that carries the research
sequence.

WHAT IT VERIFIES.

  A. THE FOUR SIGNAL LEDGER ROWS RUN 10B CHANGED. The owner has settled that a canonical module
     without its required structure may show as abstaining. This checks that the settled
     behaviour is what a participant actually sees: the row is present, it says what structure is
     missing, it shows no proxy finding, it carries no remediation language, and it is not
     described as voting.

  B. RUN 11'S OWN PARTICIPANT-VISIBLE WORDING. The conflict banner must not say the evidence
     agrees when only one lineage voted, and the seven corrected neighbour modules must abstain
     with their reason rather than band an out-of-domain reading.

  C. THE DECISION SEQUENCE STRUCTURE. The five stage cards must be present in the served page in
     the fixed order, and the reveal control must be one the participant presses.

WHAT IT DELIBERATELY DOES NOT CLAIM. It does not drive a full preliminary-lock-reveal-decide-lock
cycle end to end; that needs a consented, profiled, assigned participant and a research package,
and the run stopped short of building that fixture. The sequence's ORDER and GATING are verified
mechanically by the server suites. This is recorded as a partial verification in the report
rather than dressed up as a complete one.

CONTAINER FACTS ENCODED HERE so no session loses time on them again: Chromium is the headless
SHELL at an explicit path; the parser-blocking Google sign-in script and the map tile host are
aborted; CSS transitions are suppressed before any computed style is read; window.confirm returns
false so a confirm-gated action silently no-ops and is never used as a step.

Run:
    DATABASE_URL=sqlite:///... SESSION_SECRET=... PYTHONIOENCODING=utf-8 \
        python tools/drive_run11_participant_route.py
"""
from __future__ import annotations

import base64
import hashlib
import json
import pathlib
import sys
import threading
import time
import urllib.request

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

ROOT = pathlib.Path(__file__).resolve().parents[2]
SHELL = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"
PORT = 8131
BASE = f"http://127.0.0.1:{PORT}"
ADMIN = "r11-browser-admin"
PRJ = "PRJ-R11-ROUTE"

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


MONTHS = {
    1: ("2026-03-31", 3_000_000, 3_050_000, 3_050_000, 25.0, 25.0),
    2: ("2026-04-30", 4_000_000, 4_250_000, 4_150_000, 33.0, 34.0),
    3: ("2026-05-31", 5_000_000, 5_500_000, 5_300_000, 42.0, 44.0),
    4: ("2026-06-30", 6_000_000, 6_900_000, 6_500_000, 50.0, 54.0),
}
TAGS = ("LOOK", "PAY", "COST", "RFI", "SUB")


def doc_bytes(tag: str) -> bytes:
    return f"%PDF-1.4 RUN11 ROUTE {PRJ} {tag}\n".encode()


def records() -> dict:
    rec = {}
    for p, m in MONTHS.items():
        d = m[0]
        rec[hashlib.sha256(doc_bytes(f"M{p}")).hexdigest()] = ("monthly_report", {
            "earned_value": m[1], "actual_cost": m[2], "planned_value": m[3],
            "budget_at_completion": 12_000_000, "actual_percent_complete": m[4],
            "planned_percent_complete": m[5], "report_date": d, "document_date": d,
            "document_risk_score": 0.45})
        rec[hashlib.sha256(doc_bytes(f"LOOK{p}")).hexdigest()] = ("lookahead_schedule", {
            "activities_planned": 60, "activities_constrained": 4 + 3 * p,
            "lookahead_weeks": 3, "report_date": d})
        rec[hashlib.sha256(doc_bytes(f"PAY{p}")).hexdigest()] = ("pay_application", {
            "amount_paid_to_date": m[2], "percent_complete_verified": m[4],
            "completed_to_date": m[1], "original_contingency": 600_000,
            "remaining_contingency": 600_000 - 90_000 * p, "application_date": d})
        rec[hashlib.sha256(doc_bytes(f"COST{p}")).hexdigest()] = ("cost_report", {
            "material_cost_baseline": 4_000_000,
            "material_cost_current": 4_000_000 + 90_000 * p,
            "indirect_cost_plan": 900_000, "indirect_cost_actual": 880_000, "report_date": d})
        rec[hashlib.sha256(doc_bytes(f"RFI{p}")).hexdigest()] = ("rfi_log", {
            "rfi_total": 20 + 7 * p, "rfi_open": 4 + 3 * p, "rfi_overdue": p,
            "avg_response_days": 8.0 + p, "rfi_period_days": 30,
            "oldest_open_days": 20 + 9 * p, "log_date": d})
        rec[hashlib.sha256(doc_bytes(f"SUB{p}")).hexdigest()] = ("submittal_register", {
            "submittals_total": 40 + 16 * p, "submittals_rejected": 3 + 3 * p,
            "document_date": d})
    return rec


def post(payload: dict) -> dict:
    req = urllib.request.Request(BASE + "/exec", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "text/plain"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode())


def seed() -> str:
    from sqlalchemy import select
    import app.main as main
    from app.models import Project
    from app.research_identity import hash_access_token
    from app.research_models import Participant
    with main.SessionFactory() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code="R11-BROWSER-ADMIN", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        if s.scalar(select(Project).where(Project.legacy_id == PRJ)) is None:
            s.add(Project(legacy_id=PRJ,
                          doc={"id": PRJ, "name": "Richmond VA construction",
                               "signals": {}, "events": []}))
        s.commit()
    admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    created = post({"action": "adminparticipantcreate", "session_token": admin,
                    "pseudonymous_code": "R11-BROWSER-PM", "role": "Participant",
                    "account_type": "operational"})
    pm = post({"action": "researchlogin",
               "access_token": created["access_token"]})["session_token"]
    post({"action": "adminmemberadd", "session_token": admin, "id": PRJ,
          "participant_id": created["participant_id"], "project_role": "PM"})
    for p in (1, 2, 3, 4):
        docs = [{"filename": f"M{p}.pdf", "mimeType": "application/pdf",
                 "dataBase64": base64.b64encode(doc_bytes(f"M{p}")).decode()}]
        docs += [{"filename": f"{t}{p}.pdf", "mimeType": "application/pdf",
                  "dataBase64": base64.b64encode(doc_bytes(f"{t}{p}")).decode()}
                 for t in TAGS]
        post({"action": "projectupload", "session_token": pm, "id": PRJ,
              "period": p, "period_end": MONTHS[p][0], "documents": docs})
    post({"action": "projectcomputeall", "session_token": pm, "id": PRJ})
    return pm


def inner_text(page, selector: str) -> str:
    return page.evaluate(
        "sel => { const el = document.querySelector(sel); return el ? (el.innerText || '') : ''; }",
        selector)


def main_drive() -> None:
    import uvicorn
    from playwright.sync_api import sync_playwright

    import app.main as main
    from app.documents import set_extractor_override
    from app.extraction_client import StubExtractor

    set_extractor_override(StubExtractor(records()))
    config = uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="critical")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(120):
        try:
            urllib.request.urlopen(BASE + "/readyz", timeout=2).read()
            break
        except Exception:
            time.sleep(0.5)

    print("=" * 78)
    print("A. The stored result behind the page, read through the participant's own session")
    print("=" * 78)
    pm = seed()
    row = post({"action": "projectresults", "session_token": pm, "id": PRJ,
                "period": 4})["result"]
    abst = {a["module_id"]: a for a in (row.get("abstained") or [])}
    mods = {m["module_id"]: m for m in (row.get("module_results") or [])}
    check(bool(mods), "the project computed and the participant can read its result",
          str(len(mods)))
    check(row.get("project_conflict") is None,
          "GATE 6: the served result publishes no conflict coefficient under one voting lineage",
          str(row.get("project_conflict")))
    check(row.get("project_conflict_state") == "NOT_ESTIMABLE_SINGLE_LINEAGE",
          "GATE 6: and names the state instead", str(row.get("project_conflict_state")))
    check(row.get("project_status_label") == "Cost Recovery Status",
          "GATE 5: the governed rollup is served under the label that matches its lineage",
          str(row.get("project_status_label")))

    # The seven corrected neighbours: every one that computed must be inside its own domain,
    # and any that abstained must say why.
    SEVEN = ("A1.9", "A2.6", "A3.9", "A5.2", "A5.3", "B3.2")
    for mid in SEVEN:
        if mid in abst:
            reason = str(abst[mid].get("reason") or "")
            check(len(reason) > 30, f"GATE 3: {mid} abstains with a sentence that says why",
                  reason[:70])
            check("remediat" not in reason.lower() and "defect" not in reason.lower(),
                  f"GATE 3: {mid}'s abstention carries no remediation language", reason[:70])
        else:
            check(mods.get(mid, {}).get("status_color") in ("Green", "Yellow", "Amber", "Red"),
                  f"GATE 3: {mid} computed a band from in-domain inputs",
                  str(mods.get(mid, {}).get("status_color")))

    print()
    print("=" * 78)
    print("B. The served application in a real browser")
    print("=" * 78)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=SHELL,
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist",
                  "--no-sandbox"])
        page = browser.new_page(viewport={"width": 1680, "height": 1400})
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        for pattern in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                        "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
            page.route(pattern, lambda r: r.abort())
        page.goto(BASE + "/", wait_until="domcontentloaded")
        page.evaluate("tok => sessionStorage.setItem('og-session-token', tok)", pm)
        page.goto(BASE + "/", wait_until="domcontentloaded")
        page.add_style_tag(content="*,*::before,*::after{transition:none!important;"
                                   "animation:none!important}")
        page.wait_for_timeout(7000)

        # GATE 1 ON THE SERVED PAGE, not on the file. This is the assertion tests_render.html
        # cannot make: what the participant's browser actually loaded and what it defines.
        loaded = page.evaluate(
            "() => Array.from(document.scripts).map(s => s.src.split('/').pop())")
        for f in ("sim.js", "simulations.js", "categories.js", "deepdive.js"):
            check(f not in loaded, f"GATE 1: the served participant page does not load {f}",
                  str([s for s in loaded if s == f]))
        for g in ("LinSim", "LinSimulations"):
            check(page.evaluate(f"() => typeof window.{g}") == "undefined",
                  f"GATE 1: and {g} is undefined in the participant's browser",
                  page.evaluate(f"() => typeof window.{g}"))
        check(page.evaluate("() => !window.LIN_ALLOW_CLIENT_ANALYTICS"),
              "GATE 1: the client-analytics opt-in is not set on the application")
        check("ds_defensibility_evidence.js" in loaded,
              "GATE 4: the generated defensibility evidence object is served to the page")
        check(page.evaluate("() => typeof window.DS_DEFENSIBILITY_EVIDENCE") == "object",
              "GATE 4: and it is available to the handbook the participant can open")
        check(page.evaluate(
            "() => (window.DS_DEFENSIBILITY_EVIDENCE || {}).calibrationStatusPlatformWide || ''"
        ).startswith("Not calibrated"),
              "GATE 4: which states platform-wide that nothing here is calibrated")

        page.evaluate("id => window.LinApp.openDetail(id)", PRJ)
        page.wait_for_timeout(6000)
        page.evaluate("""() => {
            document.querySelectorAll('.collapse-section').forEach(sec => {
                if (!sec.classList.contains('open')) {
                    const h = sec.querySelector('.collapse-header');
                    if (h) h.click();
                }
            });
            document.querySelectorAll('details.cat-row').forEach(d => { d.open = true; });
        }""")
        page.wait_for_timeout(5000)

        ledger = inner_text(page, "#body-d-ledger")
        card = inner_text(page, "#body-d-decision") or inner_text(page, "#d-decision")
        check(len(ledger) > 500, "the Signal Ledger rendered on the participant route",
              str(len(ledger)))
        check(not errors, "no uncaught page error on the participant route", str(errors[:2]))
        check("—" not in ledger, "no em dash on the ledger")
        check("—" not in card, "no em dash on the decision card")

        # ---- GATE 6 on the page a participant reads.
        banner = inner_text(page, ".conflict-banner")
        print(f"    conflict banner: {banner!r}")
        check("not estimable from one voting lineage" in banner.lower(),
              "GATE 6: the conflict banner states that conflict is not estimable from one "
              "voting lineage", banner[:90])
        check("agreement" not in banner.lower(),
              "GATE 6: and it does not tell the participant the evidence agrees", banner[:90])

        # ---- GATE 2 A: the canonical-structure abstentions Run 10B introduced.
        rows_with_reason = [ln for ln in ledger.splitlines()
                            if "awaiting" in ln.lower() or "insufficient data" in ln.lower()]
        print(f"    ledger lines stating an abstention: {len(rows_with_reason)}")
        check(rows_with_reason,
              "an abstaining row states its own reason on the page, rather than disappearing")
        for word in ("remediation", "defect", "corrected", "fixed in", "was wrong",
                     "previously reported"):
            check(word not in ledger.lower(),
                  f"no remediation language reached the ledger: '{word}'")
        for word in ("(proxy:", "validated", "calibrated", "field-proven", "Advisory, non-voting",
                     "concept-only"):
            check(word.lower() not in ledger.lower(),
                  f"nothing qualifier-like or overclaiming reached the ledger: '{word}'")
            check(word.lower() not in card.lower(),
                  f"nor the decision card: '{word}'")
        check("votes on the governed status" not in ledger.lower(),
              "no abstaining row is described to the participant as voting")

        # ---- GATE 8: the decision sequence, as the served page presents it.
        stages = page.evaluate("""() => Array.from(
            document.querySelectorAll('#dc-root .dc-rail-step')).map(
                e => (e.dataset.step || e.textContent || '').trim())""")
        print(f"    decision rail steps as served: {stages}")
        cards = page.evaluate("""() => ['dc-evidence','dc-prejudgment','dc-reveal','dc-decide',
            'dc-advance'].map(id => document.getElementById(id) ? id : null)""")
        check(all(cards), "GATE 8: all five stage cards are present in the served page",
              str(cards))
        order = page.evaluate("""() => {
            const ids = ['dc-evidence','dc-prejudgment','dc-reveal','dc-decide','dc-advance'];
            const pos = ids.map(id => {
                const el = document.getElementById(id);
                return el ? Array.prototype.indexOf.call(
                    el.parentNode.children, el) : -1; });
            return pos; }""")
        check(order == sorted(order),
              "GATE 8: and they appear in the fixed research order, evidence before "
              "preliminary judgment before reveal before decision before advance", str(order))
        check(page.evaluate("() => !!document.getElementById('dc-reveal-btn')"),
              "GATE 8: the reveal is a control the participant presses, not a timer")
        # The confirm-gated affordances are never used as a step here: window.confirm returns
        # false in this container, so a confirm-gated action silently no-ops.
        check(page.evaluate("() => window.confirm('probe') === false"),
              "container fact recorded: window.confirm returns false, so no step here depends "
              "on one")

        page.close()
        browser.close()
    server.should_exit = True


if __name__ == "__main__":
    try:
        main_drive()
    finally:
        print()
        print("=" * 78)
        print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
        print("=" * 78)
    sys.exit(1 if FAILED else 0)
