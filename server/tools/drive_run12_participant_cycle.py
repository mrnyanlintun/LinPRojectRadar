#!/usr/bin/env python3
"""
RUN 12, GATES 4 TO 7. THE WHOLE PARTICIPANT CYCLE, DRIVEN IN A REAL BROWSER ON THE REAL ROUTE.

WHAT THIS IS. Run 11 verified the served participant page but stopped short of driving the
sequence, and said so. This drives it: a real server, a real Chromium, a test-only participant
provisioned through the application's own operator routes, and then evidence, preliminary
judgment, lock, reveal, final decision, lock and advance, every step performed by clicking the
control the participant clicks. Nothing is inserted straight into the decisions table.

WHAT IT PROVES THAT A SERVER SUITE CANNOT. That the controls exist on the served page, that the
reveal control is unreachable before the lock ON THE PAGE, that the page after a lock offers no
way back, and that the AI package text is absent from the served DOM until the reveal. It also
re-checks the same locks SERVER-SIDE by calling the routes directly with the participant's own
session, because a disabled control proves nothing.

TWO CONTAINER FACTS ARE HANDLED EXPLICITLY.

  1. `window.confirm` returns false in this headless shell, and the preliminary commit is
     confirm-gated, so the real button would silently no-op. A Playwright dialog handler that
     ACCEPTS is installed, which is what a browser that shows dialogs does when the participant
     presses OK. This is instrumentation of the dialog, not of the application: the click, the
     handler, the request and the lock are all real. The no-handler case is exercised FIRST and
     recorded, so the confirm gate is proved to be doing its job rather than assumed away.
  2. The Google sign-in script and the map tile host are aborted at the network layer.

Run:
    DATABASE_URL=sqlite:///... SESSION_SECRET=... PYTHONIOENCODING=utf-8 \
        python tools/drive_run12_participant_cycle.py
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
import os as _os_f10  # noqa: E402
sys.path.insert(0, _os_f10.path.dirname(_os_f10.path.abspath(__file__)))  # Run 136 F10
from artifact_write import artifact_out, report_artifact_write  # noqa: E402  Run 136 F10

ROOT = pathlib.Path(__file__).resolve().parents[2]
SHELL = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"
PORT = 8137
BASE = f"http://127.0.0.1:{PORT}"
ADMIN = "r12-cycle-admin"
PRJ = ["PRJ-R12-EV-1", "PRJ-R12-EV-2"]

PASSED = 0
FAILED = 0
EVIDENCE: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))
    EVIDENCE.append(f"{'PASS' if ok else 'FAIL'},{label},{detail}")


MONTHS = {
    1: ("2026-03-31", 3_000_000, 3_050_000, 3_050_000, 25.0, 25.0),
    2: ("2026-04-30", 4_000_000, 4_250_000, 4_150_000, 33.0, 34.0),
}
TAGS = ("LOOK", "PAY", "COST", "RFI", "SUB")


def doc_bytes(prj: str, tag: str) -> bytes:
    return f"%PDF-1.4 RUN12 CYCLE {prj} {tag}\n".encode()


def records() -> dict:
    rec = {}
    for prj in PRJ:
        for p, m in MONTHS.items():
            d = m[0]
            rec[hashlib.sha256(doc_bytes(prj, f"M{p}")).hexdigest()] = ("monthly_report", {
                "earned_value": m[1], "actual_cost": m[2], "planned_value": m[3],
                "budget_at_completion": 12_000_000, "actual_percent_complete": m[4],
                "planned_percent_complete": m[5], "report_date": d, "document_date": d,
                "document_risk_score": 0.45})
            rec[hashlib.sha256(doc_bytes(prj, f"LOOK{p}")).hexdigest()] = (
                "lookahead_schedule", {"activities_planned": 60,
                                       "activities_constrained": 4 + 3 * p,
                                       "lookahead_weeks": 3, "report_date": d})
            rec[hashlib.sha256(doc_bytes(prj, f"PAY{p}")).hexdigest()] = ("pay_application", {
                "amount_paid_to_date": m[2], "percent_complete_verified": m[4],
                "completed_to_date": m[1], "original_contingency": 600_000,
                "remaining_contingency": 600_000 - 90_000 * p, "application_date": d})
            rec[hashlib.sha256(doc_bytes(prj, f"COST{p}")).hexdigest()] = ("cost_report", {
                "material_cost_baseline": 4_000_000,
                "material_cost_current": 4_000_000 + 90_000 * p,
                "indirect_cost_plan": 900_000, "indirect_cost_actual": 880_000,
                "report_date": d})
            rec[hashlib.sha256(doc_bytes(prj, f"RFI{p}")).hexdigest()] = ("rfi_log", {
                "rfi_total": 20 + 7 * p, "rfi_open": 4 + 3 * p, "rfi_overdue": p,
                "avg_response_days": 8.0 + p, "rfi_period_days": 30,
                "oldest_open_days": 20 + 9 * p, "log_date": d})
            rec[hashlib.sha256(doc_bytes(prj, f"SUB{p}")).hexdigest()] = (
                "submittal_register", {"submittals_total": 40 + 16 * p,
                                       "submittals_rejected": 3 + 3 * p, "document_date": d})
    return rec


def post(payload: dict) -> dict:
    req = urllib.request.Request(BASE + "/exec", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "text/plain"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode())


PROVISIONING: list[str] = []


def note(step: str, route: str, detail: str = "") -> None:
    PROVISIONING.append(f"{step} | {route} | {detail}")
    print(f"    provision: {step:<34} via {route} {detail}")


def provision() -> dict:
    """
    GATE 4. Everything the application needs, created the way the application creates it.

    The ONLY direct row writes are the bootstrap research administrator, which has no route
    because a route would need an administrator to call it, and the two empty evidence project
    shells, exactly as the existing decision-sequence suite creates them. Every participant-facing
    piece of state after that is made by an operator or participant route over HTTP.
    """
    from sqlalchemy import select
    import app.main as main
    from app.models import Project
    from app.research_identity import hash_access_token
    from app.research_models import Participant

    with main.SessionFactory() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code="R12-CYCLE-ADMIN", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        for legacy in PRJ:
            if s.scalar(select(Project).where(Project.legacy_id == legacy)) is None:
                s.add(Project(legacy_id=legacy,
                              doc={"id": legacy, "name": "Richmond VA construction",
                                   "signals": {}, "events": []}))
        s.commit()
    note("bootstrap research administrator", "direct row, no route exists",
         "the only account that cannot be made by a route")

    admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    note("administrator session", "researchlogin")

    # An operational account uploads the evidence, so the evidence projects hold real computed
    # results rather than hand-written signals.
    op = post({"action": "adminparticipantcreate", "session_token": admin,
               "pseudonymous_code": "R12-CYCLE-PM", "role": "Participant",
               "account_type": "operational"})
    op_tok = post({"action": "researchlogin",
                   "access_token": op["access_token"]})["session_token"]
    note("operational uploader account", "adminparticipantcreate + researchlogin")
    for legacy in PRJ:
        post({"action": "adminmemberadd", "session_token": admin, "id": legacy,
              "participant_id": op["participant_id"], "project_role": "PM"})
        for p in MONTHS:
            docs = [{"filename": f"M{p}.pdf", "mimeType": "application/pdf",
                     "dataBase64": base64.b64encode(doc_bytes(legacy, f"M{p}")).decode()}]
            docs += [{"filename": f"{t}{p}.pdf", "mimeType": "application/pdf",
                      "dataBase64": base64.b64encode(doc_bytes(legacy, f"{t}{p}")).decode()}
                     for t in TAGS]
            post({"action": "projectupload", "session_token": op_tok, "id": legacy,
                  "period": p, "period_end": MONTHS[p][0], "documents": docs})
        post({"action": "projectcomputeall", "session_token": op_tok, "id": legacy})
    note("evidence uploaded and computed", "projectupload + projectcomputeall",
         f"{len(PRJ)} projects, {len(MONTHS)} periods each")

    scenarios = [post({"action": "adminscenariocreate", "session_token": admin,
                       "scenario_version": f"r12-s{i}", "project_type": "construction",
                       "period_count": len(MONTHS),
                       "evidence_package_id": legacy})["scenario_id"]
                 for i, legacy in enumerate(PRJ)]
    note("frozen project packages (scenarios)", "adminscenariocreate",
         f"period_count={len(MONTHS)}")
    post({"action": "adminconfigurationcreate", "session_token": admin,
          "code": "C1", "version": "v1", "freeze": True})
    post({"action": "adminsequencecreate", "session_token": admin, "order_group": "GR12",
          "scenario_set": "SET-R12", "version": "v1", "positions": ["C1", "C1"], "freeze": True})
    note("configuration and sequence, frozen", "adminconfigurationcreate + adminsequencecreate")

    # The governed transition data. Without a frozen family mapping and a frozen rule the
    # application refuses to advance, which it should: an unmapped action has no branch and a
    # default branch would be an invention. Every participant action is mapped, and each family
    # has a frozen rule for the first period whose next state is the second evidence project.
    fam = post({"action": "adminactionfamilycreate", "session_token": admin,
                "version": "r12-fam-v1", "freeze": True,
                "mappings": {"monitor": "accept", "investigate": "investigate",
                             "escalate": "escalate", "re-baseline": "modify",
                             "defer": "defer"}})
    for family in ("accept", "investigate", "escalate", "modify", "defer"):
        post({"action": "admintransitionrulecreate", "session_token": admin,
              "scenario_id": scenarios[0], "period": "P1", "action_family": family,
              "version": "r12-rules-v1", "freeze": True,
              "branches": [{"branch_id": f"B-{family.upper()}", "branch_version": "bv1",
                            "probability": "1.0", "next_state_id": PRJ[1]}]})
    note("action families and period transition rules, frozen",
         "adminactionfamilycreate + admintransitionrulecreate",
         f"ok={fam.get('ok')}, 5 families")

    pkgs = []
    for i in range(len(PRJ)):
        pkgs.append(post({"action": "adminpackagecreate", "session_token": admin,
                          "version": f"r12-pkg-v{i + 1}", "provider_id": "frozen-store",
                          "model_version": "n/a", "output_type": "recommendation",
                          "detected_condition": "cost overrun risk",
                          "recommended_action": "Escalate to recovery review",
                          "alternatives": ["Monitor for one period", "Re-baseline"],
                          "uncertainty": {"confidence": "moderate"},
                          "limitations": "Derived from a single reporting period.",
                          "freeze": True}))
    note("decision support packages, frozen", "adminpackagecreate",
         f"{len(pkgs)} packages, sha256 hashes")

    created = post({"action": "adminparticipantcreate", "session_token": admin,
                    "pseudonymous_code": "R12-CYCLE-P1", "role": "Participant"})
    tok = post({"action": "researchlogin",
                "access_token": created["access_token"]})["session_token"]
    note("test participant account", "adminparticipantcreate + researchlogin",
         created["participant_id"])
    cg = post({"action": "consentgrant", "session_token": tok, "consent_version": "v1.0"})
    note("consent granted", "consentgrant", f"ok={cg.get('ok')}")
    iq = post({"action": "intakesave", "session_token": tok,
               "responses": {"experience_level": "mid", "years_experience": 8}})
    note("participant profile (intake)", "intakesave", f"ok={iq.get('ok')}")
    # The uploader holds the single PM slot on each evidence project. The participant cannot
    # advance a period or read a stored result without being the project manager, so the
    # handover is performed through the operator routes that exist for it, revocation first
    # because the application refuses a second active PM.
    for legacy in PRJ:
        listed = post({"action": "adminmemberlist", "session_token": admin, "id": legacy})
        for m in (listed.get("members") or []):
            if m.get("project_role") == "PM" and not m.get("revoked_at"):
                post({"action": "adminmemberrevoke", "session_token": admin,
                      "member_id": m.get("member_id")})
    _mem = [post({"action": "adminmemberadd", "session_token": admin, "id": legacy,
                  "participant_id": created["participant_id"], "project_role": "PM"})
            for legacy in PRJ]
    assert all(m.get("ok") for m in _mem), _mem
    note("participant made project manager of the assigned evidence projects",
         "adminmemberadd",
         "required: researchadvance and projectresults both refuse a non-member")
    asg = post({"action": "adminassign", "session_token": admin,
                "participant_id": created["participant_id"], "order_group": "GR12",
                "scenario_set": "SET-R12", "scenario_ids": scenarios})
    note("project and period assignment", "adminassign", f"ok={asg.get('ok')}")

    from app.research_models import Assignment
    with main.SessionFactory() as s:
        assigns = s.scalars(select(Assignment)
                            .where(Assignment.participant_id == created["participant_id"])
                            .order_by(Assignment.sequence_number)).all()
        ids = [a.assignment_id for a in assigns]
    for aid, pkg in zip(ids, pkgs):
        post({"action": "adminpackageattach", "session_token": admin,
              "assignment_id": aid, "package_id": pkg["package_id"]})
    note("packages attached to assignments", "adminpackageattach", str(len(ids)))

    return {"admin": admin, "participant": created["participant_id"], "token": tok,
            "assignments": ids, "packages": pkgs}


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
    print("GATE 4. Provisioning the test participant through the application's own routes")
    print("=" * 78)
    ctx = provision()
    tok = ctx["token"]

    state = post({"action": "researchsequencestate", "session_token": tok})
    check(state.get("ok") is True and state.get("current_stage") == "evidence",
          "GATE 4: the provisioned participant starts at the evidence stage",
          str(state.get("current_stage")))
    check(state.get("period") == "P1", "GATE 4: on the first reporting period",
          str(state.get("period")))

    print()
    print("=" * 78)
    print("GATES 5 TO 7. The cycle, in a real browser on the real participant route")
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
        page.evaluate("t => sessionStorage.setItem('og-session-token', t)", tok)
        page.goto(BASE + "/", wait_until="domcontentloaded")
        page.add_style_tag(content="*,*::before,*::after{transition:none!important;"
                                   "animation:none!important}")
        page.wait_for_timeout(7000)

        loaded = page.evaluate(
            "() => Array.from(document.scripts).map(s => s.src.split('/').pop())")
        check("decision-ui.js" in loaded,
              "the real participant application is the page under test", str(len(loaded)))
        for f in ("sim.js", "simulations.js", "categories.js"):
            check(f not in loaded, f"GATE 8: the served participant page still does not load {f}")
        check(page.evaluate("() => typeof window.LinSim") == "undefined",
              "GATE 8: and the historical client arithmetic is undefined here")

        # The sequence lives in the Period decision tab of the project the participant is
        # assigned. Open the project the way the participant does, then open the sections, which
        # is what mounts the decision card.
        open_sections = """() => {
            const b = Array.from(document.querySelectorAll('#ws-project-tabs button'))
                .find(x => x.dataset.wstab === 'decision');
            if (b) b.click();
            else if (window.LinWorkspace && LinWorkspace.switchPanel)
                LinWorkspace.switchPanel('decision'); }"""
        # The participant reaches the period decision the way the application routes them to
        # it: the project page, then its Period decision tab.
        page.evaluate("id => { window.LinApp.showPage('project');"
                      " if (window.LinWorkspace) LinWorkspace.openProject(id); }", PRJ[0])
        page.wait_for_timeout(4000)
        page.evaluate(open_sections)
        page.wait_for_timeout(6000)
        print("    decision position: "
              + repr(inner_text(page, "#dc-position"))[:160])

        # ---------------------------------------------------------------- the sequence surface
        present = page.evaluate("""() => ['dc-evidence','dc-prejudgment','dc-reveal','dc-decide',
            'dc-advance'].every(id => !!document.getElementById(id))""")
        check(present, "GATE 5: the five stage cards are on the served participant page")

        # STEP 1: evidence visible, recommendation not.
        evidence_text = inner_text(page, "#dc-evidence")
        check(len(evidence_text) > 40, "GATE 5: the fixed evidence package is visible",
              str(len(evidence_text)))
        dom = page.evaluate("() => document.body.innerText")
        check("Escalate to recovery review" not in dom,
              "GATE 5: the AI recommendation is NOT in the served page before the lock")
        check(page.evaluate("""() => { const el = document.getElementById('dc-reveal');
              return !el || el.style.display === 'none' || el.offsetParent === null; }"""),
              "GATE 5: and the reveal card is not offered before the preliminary lock")

        # The confirm gate, exercised honestly: first with NO dialog handler, which is the
        # container's own behaviour, then with one.
        page.evaluate("""() => { const s = document.getElementById('dc-pre-action');
            s.value = Array.from(s.options).map(o => o.value).filter(Boolean)[0];
            s.dispatchEvent(new Event('change'));
            const c = document.getElementById('dc-pre-confidence');
            c.value = 60; c.dispatchEvent(new Event('input'));
            const a = document.getElementById('dc-pre-assessment');
            if (a) { a.value = 'Cost performance is drifting and I would watch one more period.';
                     a.dispatchEvent(new Event('input')); } }""")
        chosen = page.evaluate("() => document.getElementById('dc-pre-action').value")
        conf = page.evaluate("() => document.getElementById('dc-pre-confidence').value")
        check(bool(chosen), "GATE 5: the participant records a preliminary action", str(chosen))
        check(str(conf) == "60", "GATE 5: and a preliminary confidence", str(conf))

        page.click("#dc-commit-btn")
        page.wait_for_timeout(2500)
        st = post({"action": "researchsequencestate", "session_token": tok})
        check(st.get("current_stage") == "evidence",
              "container fact proved, not assumed: with dialogs suppressed the confirm-gated "
              "commit no-ops and NOTHING was submitted", str(st.get("current_stage")))

        page.on("dialog", lambda d: d.accept())
        page.click("#dc-commit-btn")
        page.wait_for_timeout(3000)
        st = post({"action": "researchsequencestate", "session_token": tok})
        check(st.get("current_stage") == "awaiting_reveal",
              "GATE 5: the preliminary decision submitted from the real control and LOCKED",
              str(st.get("current_stage")))

        # ---------------------------------------------------------------- GATE 7, server-side
        resub = post({"action": "researchprejudgment", "session_token": tok,
                      "pre_action": "escalate", "pre_confidence": 99})
        check(resub.get("ok") is False and "locked" in str(resub.get("error", "")).lower(),
              "GATE 7: the SERVER refuses a direct route edit of the locked preliminary "
              "decision", str(resub)[:120])

        from sqlalchemy import select, text
        import app.main as m2
        from app.research_models import Decision
        with m2.SessionFactory() as s:
            dec = s.scalar(select(Decision)
                           .where(Decision.assignment_id == ctx["assignments"][0]))
            stored_pre = (dec.pre_action, dec.pre_confidence)
            check(dec.pre_judgment_locked is True and dec.pre_locked_at is not None,
                  "GATE 7: the stored row is locked with a lock timestamp")
            check(dec.pre_action == chosen and dec.pre_confidence == 60,
                  "GATE 7: and holds exactly what the participant recorded", str(stored_pre))
            check(dec.reveal_at is None, "GATE 7: no reveal has happened yet")
            # The database trigger, tested where the application is bypassed entirely.
            trip = None
            try:
                s.execute(text("UPDATE decisions SET pre_action='tampered' "
                               "WHERE assignment_id=:a"), {"a": ctx["assignments"][0]})
                s.commit()
            except Exception as exc:  # the B1 append-only trigger
                trip = str(exc)[:120]
                s.rollback()
            check(trip is not None,
                  "GATE 7: and the database itself refuses the edit when the application is "
                  "bypassed", str(trip))
        with m2.SessionFactory() as s:
            dec = s.scalar(select(Decision)
                           .where(Decision.assignment_id == ctx["assignments"][0]))
            check((dec.pre_action, dec.pre_confidence) == stored_pre,
                  "GATE 7: the preliminary record is preserved byte for byte")

        # ---------------------------------------------------------------- reveal
        remount = """() => { if (window.LinWorkspace) {
            LinWorkspace.switchPanel('upload'); LinWorkspace.switchPanel('decision'); } }"""
        page.evaluate(remount)
        page.wait_for_timeout(6000)
        dom = page.evaluate("() => document.body.innerText")
        check("Escalate to recovery review" not in dom,
              "GATE 5: the recommendation is STILL absent after the lock and before the reveal")
        check(page.evaluate("() => !!document.getElementById('dc-reveal-btn')"),
              "GATE 5: the reveal control is now offered")
        page.click("#dc-reveal-btn")
        page.wait_for_timeout(3000)
        dom = page.evaluate("() => document.body.innerText")
        check("Escalate to recovery review" in dom,
              "GATE 5: after the reveal the participant can inspect the intended "
              "recommendation")
        with m2.SessionFactory() as s:
            dec = s.scalar(select(Decision)
                           .where(Decision.assignment_id == ctx["assignments"][0]))
            check(dec.reveal_at is not None and dec.pre_locked_at <= dec.reveal_at,
                  "GATE 5 and 7: the reveal is recorded and happened AFTER the preliminary lock",
                  f"{dec.pre_locked_at} -> {dec.reveal_at}")
            check(dec.package_hash == ctx["packages"][0]["hash"],
                  "GATE 7: the revealed package hash is the frozen package's own")

        # ---------------------------------------------------------------- final decision
        page.evaluate("""() => {
            const set = (id, v) => { const e = document.getElementById(id);
                if (e) { e.value = v; e.dispatchEvent(new Event('change'));
                         e.dispatchEvent(new Event('input')); } };
            const fa = document.getElementById('dc-final-action');
            set('dc-final-action', Array.from(fa.options).map(o => o.value)
                .filter(Boolean)[0]);
            const dp = document.getElementById('dc-disposition');
            set('dc-disposition', Array.from(dp.options).map(o => o.value)
                .filter(Boolean)[0]);
            set('dc-final-confidence', 70);
            set('dc-rationale', 'The recommendation matches what the cost evidence shows.');
            set('dc-owner', 'Project manager');
            set('dc-authority', 'Programme director');
            set('dc-deadline', 'next reporting cycle');
            const ev = document.querySelector('[data-evidence]');
            if (ev) { ev.checked = true; ev.dispatchEvent(new Event('change')); } }""")
        final_action = page.evaluate("() => document.getElementById('dc-final-action').value")
        disposition = page.evaluate("() => document.getElementById('dc-disposition').value")
        check(bool(final_action) and bool(disposition),
              "GATE 5: the participant records a final action and a disposition",
              f"{final_action} / {disposition}")
        page.click("#dc-decide-btn")
        page.wait_for_timeout(3000)
        st = post({"action": "researchsequencestate", "session_token": tok})
        check(st.get("current_stage") == "complete",
              "GATE 5: the final decision submitted from the real control and LOCKED",
              str(st.get("current_stage")))

        again = post({"action": "researchdecision", "session_token": tok,
                      "final_action": "something else", "disposition": "reject",
                      "rationale": "second attempt"})
        check(again.get("ok") is False,
              "GATE 7: the SERVER refuses a direct route edit of the locked final decision",
              str(again)[:120])
        with m2.SessionFactory() as s:
            dec = s.scalar(select(Decision)
                           .where(Decision.assignment_id == ctx["assignments"][0]))
            check(dec.final_action == final_action and dec.disposition == disposition,
                  "GATE 7: the final record is preserved and is what the participant recorded",
                  f"{dec.final_action} / {dec.disposition}")
            check(dec.final_submitted_at is not None,
                  "GATE 7: with a final submission timestamp that is the lock")
            check(dec.pre_locked_at <= dec.reveal_at <= dec.final_submitted_at,
                  "GATE 7: the three timestamps are in the governed order")
            check(dec.assignment_id == ctx["assignments"][0],
                  "GATE 7: recorded against the correct assignment and project period")

        # ---------------------------------------------------------------- advance
        remount = """() => { if (window.LinWorkspace) {
            LinWorkspace.switchPanel('upload'); LinWorkspace.switchPanel('decision'); } }"""
        page.evaluate(remount)
        page.wait_for_timeout(6000)
        check(page.evaluate("() => !!document.getElementById('dc-advance-btn')"),
              "GATE 5: the advance control is offered once the period is complete")
        page.click("#dc-advance-btn")
        page.wait_for_timeout(3000)
        print("    advance error on page: "
              + repr(inner_text(page, "#dc-advance-error"))[:200])
        st = post({"action": "researchsequencestate", "session_token": tok})
        check(st.get("period") == "P2" or st.get("sequence_number") == 2,
              "GATE 5: the governed transition to the next reporting period occurred",
              json.dumps({k: st.get(k) for k in ("period", "sequence_number", "current_stage")}))
        check(st.get("current_stage") == "evidence",
              "GATE 5: and the next period starts at evidence again, with no recommendation",
              str(st.get("current_stage")))
        dom = page.evaluate("() => document.body.innerText")

        # The defect this drive found: after the advance the preliminary judgment card had been
        # removed at the first lock and nothing put it back, so the second period could not be
        # started at all. Proved here on the page itself, not on the file.
        page.evaluate(remount)
        page.wait_for_timeout(5000)
        check(page.evaluate("() => !!document.getElementById('dc-prejudgment')"),
              "GATE 5: the preliminary judgment card is present again in the next period")
        check(page.evaluate("() => !!document.getElementById('dc-pre-action')"),
              "GATE 5: and its form renders, so the second period can actually be started")
        page.evaluate("""() => { const s = document.getElementById('dc-pre-action');
            s.value = Array.from(s.options).map(o => o.value).filter(Boolean)[1];
            s.dispatchEvent(new Event('change')); }""")
        page.click("#dc-commit-btn")
        page.wait_for_timeout(3000)
        st2 = post({"action": "researchsequencestate", "session_token": tok})
        check(st2.get("current_stage") == "awaiting_reveal",
              "GATE 5: and the second period's preliminary decision locks the same way",
              str(st2.get("current_stage")))

        # ---------------------------------------------------------------- dispositions
        seq = post({"action": "researchsequencestate", "session_token": tok})
        dispositions = ((seq.get("vocabularies") or {}).get("dispositions")) or []
        check(len(dispositions) >= 5,
              "GATE 5: the instrument offers the governed disposition set", str(dispositions))
        offered = page.evaluate("""() => { const d = document.getElementById('dc-disposition');
            return d ? Array.from(d.options).map(o => o.value).filter(Boolean) : []; }""")
        check(set(offered) <= set(dispositions),
              "GATE 5: and the page offers no disposition the server does not accept",
              str(offered))
        bad = post({"action": "researchdecision", "session_token": tok,
                    "final_action": "monitor", "disposition": "invent-a-disposition",
                    "rationale": "x"})
        check(bad.get("ok") is False,
              "GATE 5: a disposition outside the governed set is refused", str(bad)[:110])

        # ---------------------------------------------------------------- GATE 6, the page
        row = post({"action": "projectresults", "session_token": tok,
                    "id": PRJ[0], "period": 2})
        check(row.get("ok") is not False or row.get("result") is not None,
              "the participant can read the stored result behind the page", str(row)[:90])
        r = (row.get("result") or {})
        if r:
            check(r.get("project_status_label") == "Cost Recovery Status",
                  "GATE 6: the governed status label is served",
                  str(r.get("project_status_label")))
            check(r.get("project_conflict_state") == "NOT_ESTIMABLE_SINGLE_LINEAGE",
                  "GATE 6: the one-lineage conflict semantics are served",
                  str(r.get("project_conflict_state")))
            check(r.get("project_conflict") is None,
                  "GATE 6: and no conflict coefficient is published")
            q = r.get("evidence_qualification") or {}
            check(q.get("revision_resolution_status") == "NOT_ESTIMABLE",
                  "GATE 6: the qualification reaches the served read as NOT_ESTIMABLE",
                  str(q.get("revision_resolution_status")))
            check(q.get("provenance_status") in ("PARTIAL", "NOT_ESTIMABLE"),
                  "GATE 6: provenance is not dressed up as healthy",
                  str(q.get("provenance_status")))
        body = page.evaluate("() => document.body.innerText").lower()
        for word in ("remediation", "defect", "not_estimable_single_lineage", "cat9-qual",
                     "partial", "calibrated"):
            check(word not in body,
                  f"GATE 6: no machine or overclaiming vocabulary reached the participant page: "
                  f"'{word}'")
        vword = page.evaluate("""() => { const t = document.body.innerText;
            const i = t.toLowerCase().indexOf('validated');
            return i < 0 ? '' : t.slice(Math.max(0, i - 90), i + 90); }""")
        print(f"    context around 'validated' on the page: {vword!r}")
        check("—" not in page.evaluate("() => document.body.innerText"),
              "GATE 6: no em dash on the participant page")
        check(not errors, "no uncaught page error across the whole cycle", str(errors[:2]))

        page.close()
        browser.close()
    server.should_exit = True

    out = artifact_out(ROOT / "code_audit" / "run12_participant_cycle_evidence.csv")
    out.write_text("outcome,check,detail\n"
                   + "\n".join(e.replace("\n", " ") for e in EVIDENCE) + "\n",
                   encoding="utf-8")
    prov = artifact_out(ROOT / "code_audit" / "run12_participant_provisioning.csv")
    prov.write_text("step,route,detail\n"
                    + "\n".join(p.replace(" | ", ",") for p in PROVISIONING) + "\n",
                    encoding="utf-8")


if __name__ == "__main__":
    try:
        main_drive()
    finally:
        print()
        print("=" * 78)
        print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
        print("=" * 78)
    sys.exit(1 if FAILED else 0)
