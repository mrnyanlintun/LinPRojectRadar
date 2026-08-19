#!/usr/bin/env python3
"""
RUN 38, SECTION 24. STUDY-EXECUTION BROWSER QUALIFICATION.

Run 38 does not claim a browser PASS from API tests. This driver launches the real Chromium
headless shell against the real served participant application on a throwaway SQLite database
and walks the complete governed sequence with an isolated TEST_ONLY identity:

  login/authentication -> start session -> evidence review -> preliminary response ->
  preliminary lock -> AI reveal -> final response -> final lock -> next period ->
  reload/resume -> completion

Enough controlled periods are driven IN THE BROWSER to prove every state transition, and then
all 36 route identities are verified reachable mechanically, which is what section 24 asks for
in that order.

CONTAINER FACTS, HANDLED RATHER THAN ASSUMED AWAY: window.confirm returns false in this
headless shell, so the confirm-gated commit is exercised first with no dialog handler (which
proves the gate is real) and then with one. Google SSO and map-tile requests are aborted at the
route level.

THIS DRIVER CHANGES NOTHING. It authenticates, walks, observes and records.

Run:
    DATABASE_URL=sqlite:///... SESSION_SECRET=... PYTHONIOENCODING=utf-8 \
        python tools/drive_run38_browser.py
"""
from __future__ import annotations

import csv
import json
import logging
import pathlib
import sys
import threading
import time
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
logging.disable(logging.INFO)

ROOT = pathlib.Path(__file__).resolve().parents[2]
SHELL = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"
PORT = 8391
BASE = f"http://127.0.0.1:{PORT}"

ROWS: list[list[str]] = []
RESULTS: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> bool:
    RESULTS.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))
    return bool(ok)


def row(surface: str, reached: str, observed: str, result: str) -> None:
    ROWS.append([surface, reached, observed, result])


def inner_text(page, selector: str) -> str:
    return page.evaluate("s => { const e = document.querySelector(s);"
                         " return e ? e.innerText : ''; }", selector)


def main() -> int:
    import uvicorn
    from playwright.sync_api import sync_playwright
    from sqlalchemy import select

    import app.main as main_app
    import run38_dryrun as D
    from app.research_models import Assignment, Decision

    config = uvicorn.Config(main_app.app, host="127.0.0.1", port=PORT, log_level="critical")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(120):
        try:
            urllib.request.urlopen(BASE + "/readyz", timeout=2).read()
            break
        except Exception:
            time.sleep(0.5)

    print("=" * 78)
    print("PROVISIONING (through the application's own routes, TEST_ONLY)")
    print("=" * 78)
    ctx = D.bootstrap()
    P = D.make_participant(ctx, "BROWSER")
    tok = P["token"]
    first_project = P["by_scenario"][P["assignments"][0][2]]
    evidence_project = D.evidence_legacy_id(first_project, "P1")
    check(len(P["assignments"]) == 6, "the browser identity holds all six study projects")

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

        # ---------------------------------------------------- login / start session
        page.goto(BASE + "/", wait_until="domcontentloaded")
        page.evaluate("t => sessionStorage.setItem('og-session-token', t)", tok)
        page.goto(BASE + "/", wait_until="domcontentloaded")
        page.add_style_tag(content="*,*::before,*::after{transition:none!important;"
                                   "animation:none!important}")
        page.wait_for_timeout(7000)
        loaded = page.evaluate(
            "() => Array.from(document.scripts).map(s => s.src.split('/').pop())")
        ok = check("decision-ui.js" in loaded,
                   "login: the real participant application is the page under test")
        row("login / authentication", "yes", f"{len(loaded)} scripts, decision-ui.js present",
            "PASS" if ok else "FAIL")
        ok = check("taxonomy.js" in loaded and "categories.js" not in loaded,
                   "the served client loads taxonomy.js and not categories.js")

        page.evaluate("id => { window.LinApp.showPage('project');"
                      " if (window.LinWorkspace) LinWorkspace.openProject(id); }",
                      evidence_project)
        page.wait_for_timeout(4000)
        open_decision = """() => {
            const b = Array.from(document.querySelectorAll('#ws-project-tabs button'))
                .find(x => x.dataset.wstab === 'decision');
            if (b) b.click();
            else if (window.LinWorkspace && LinWorkspace.switchPanel)
                LinWorkspace.switchPanel('decision'); }"""
        page.evaluate(open_decision)
        page.wait_for_timeout(6000)

        present = page.evaluate("""() => ['dc-evidence','dc-prejudgment','dc-reveal','dc-decide',
            'dc-advance'].every(id => !!document.getElementById(id))""")
        ok = check(present, "start session: the five stage cards are on the served page")
        row("start session", "yes", "dc-evidence/prejudgment/reveal/decide/advance present",
            "PASS" if ok else "FAIL")

        # ---------------------------------------------------- evidence review
        evidence_text = inner_text(page, "#dc-evidence")
        ok = check(len(evidence_text) > 20, "evidence review: the controlled evidence is visible",
                   str(len(evidence_text)))
        row("evidence review", "yes", f"{len(evidence_text)} chars rendered",
            "PASS" if ok else "FAIL")
        # WHAT COUNTS AS THE AI CONTENT, AND WHAT DOES NOT.
        # "escalate" is NOT evidence of a leak: it is a value in the participant's own action
        # vocabulary and is on the page as a dropdown option before anything is revealed. The
        # AI-specific content is the package's detected_condition, its version and its hash,
        # none of which the participant vocabulary contains. Searching for the shared word
        # would have reported the participant's own form as a disclosure.
        dom = page.evaluate("() => document.body.innerText")
        html = page.content()
        pkg = ctx["packages"][first_project]
        leaks = [needle for needle in ("cost variance beyond threshold", pkg["version"],
                                       pkg["hash"], "r38-test-m1")
                 if needle in dom or needle in html]
        ok = check(not leaks,
                   "the AI recommendation is NOT in the served page or its DOM before the "
                   "preliminary lock", str(leaks))
        row("AI leakage before lock", "yes",
            "detected_condition, package version, package hash and model version all absent "
            "from innerText AND from the served DOM", "PASS" if ok else "FAIL")
        ok = check(page.evaluate("""() => { const el = document.getElementById('dc-reveal');
                   return !el || el.style.display === 'none' || el.offsetParent === null; }"""),
                   "and the reveal card is not offered before the preliminary lock")

        # ---------------------------------------------------- preliminary response
        page.evaluate("""() => {
            const s = document.getElementById('dc-pre-action');
            s.value = Array.from(s.options).map(o => o.value).filter(Boolean)[0];
            s.dispatchEvent(new Event('change'));
            const c = document.getElementById('dc-pre-confidence');
            c.value = 60; c.dispatchEvent(new Event('input'));
            const a = document.getElementById('dc-pre-assessment');
            if (a) { a.value = 'Dry run preliminary assessment.';
                     a.dispatchEvent(new Event('input')); } }""")
        chosen = page.evaluate("() => document.getElementById('dc-pre-action').value")
        ok = check(bool(chosen), "preliminary response: recorded from the real control", chosen)
        row("preliminary response", "yes", f"pre_action={chosen} pre_confidence=60",
            "PASS" if ok else "FAIL")

        page.click("#dc-commit-btn")
        page.wait_for_timeout(2500)
        st = D.post({"action": "researchsequencestate", "session_token": tok})
        ok = check(st.get("current_stage") == "evidence",
                   "container fact proved, not assumed: with dialogs suppressed the "
                   "confirm-gated commit no-ops and nothing was submitted",
                   str(st.get("current_stage")))

        # Named rather than a lambda so it can be REMOVED before navigating. With a dialog
        # listener installed Playwright stops auto-dismissing, and a dialog raised during
        # navigation teardown blocks the navigation indefinitely -- which is a driver fact
        # about this container, not a property of the application.
        def accept_dialog(d):
            d.accept()

        page.on("dialog", accept_dialog)
        page.click("#dc-commit-btn")
        page.wait_for_timeout(3000)
        st = D.post({"action": "researchsequencestate", "session_token": tok})
        ok = check(st.get("current_stage") == "awaiting_reveal",
                   "preliminary lock: submitted from the real control and LOCKED",
                   str(st.get("current_stage")))
        row("preliminary lock", "yes", f"stage={st.get('current_stage')} "
            f"pre_locked_at={st.get('pre_locked_at')}", "PASS" if ok else "FAIL")

        with main_app.SessionFactory() as s:
            dec = s.scalar(select(Decision).where(
                Decision.assignment_id == P["assignments"][0][1]))
            ok = check(dec.pre_judgment_locked and dec.pre_locked_at is not None
                       and dec.pre_action == chosen and dec.pre_confidence == 60,
                       "the persisted row holds exactly what the browser recorded, locked",
                       f"{dec.pre_action}/{dec.pre_confidence}")

        # ---------------------------------------------------- AI reveal
        remount = """() => { if (window.LinWorkspace) {
            LinWorkspace.switchPanel('upload'); LinWorkspace.switchPanel('decision'); } }"""
        page.evaluate(remount)
        page.wait_for_timeout(6000)
        dom = page.evaluate("() => document.body.innerText")
        ok = check("cost variance beyond threshold" not in dom,
                   "the recommendation is STILL absent after the lock and before the reveal")
        ok = check(page.evaluate("() => !!document.getElementById('dc-reveal-btn')"),
                   "the reveal control is offered once the preliminary judgment is locked")
        page.click("#dc-reveal-btn")
        page.wait_for_timeout(3000)
        dom = page.evaluate("() => document.body.innerText")
        ok = check("cost variance beyond threshold" in dom,
                   "AI reveal: the frozen package is rendered to the participant after the lock")
        row("AI reveal", "yes", "detected_condition rendered in the served page after the lock",
            "PASS" if ok else "FAIL")
        with main_app.SessionFactory() as s:
            dec = s.scalar(select(Decision).where(
                Decision.assignment_id == P["assignments"][0][1]))
            ok = check(dec.reveal_at is not None and dec.pre_locked_at <= dec.reveal_at,
                       "and the reveal is recorded AFTER the preliminary lock",
                       f"{dec.pre_locked_at} -> {dec.reveal_at}")

        # ---------------------------------------------------- final response and lock
        page.evaluate("""() => {
            const set = (id, v) => { const e = document.getElementById(id);
                if (e) { e.value = v; e.dispatchEvent(new Event('change'));
                         e.dispatchEvent(new Event('input')); } };
            const fa = document.getElementById('dc-final-action');
            set('dc-final-action', Array.from(fa.options).map(o => o.value)
                .filter(Boolean).slice(-1)[0]);
            const dp = document.getElementById('dc-disposition');
            set('dc-disposition', Array.from(dp.options).map(o => o.value).filter(Boolean)[0]);
            set('dc-final-confidence', 75);
            set('dc-rationale', 'Dry run rationale.');
            const ev = document.querySelector('[data-evidence]');
            if (ev) { ev.checked = true; ev.dispatchEvent(new Event('change')); } }""")
        final_action = page.evaluate("() => document.getElementById('dc-final-action').value")
        disposition = page.evaluate("() => document.getElementById('dc-disposition').value")
        ok = check(bool(final_action) and bool(disposition),
                   "final response: action and disposition recorded from the real controls",
                   f"{final_action}/{disposition}")
        row("final response", "yes", f"final_action={final_action} disposition={disposition}",
            "PASS" if ok else "FAIL")
        page.click("#dc-decide-btn")
        page.wait_for_timeout(3000)
        st = D.post({"action": "researchsequencestate", "session_token": tok})
        ok = check(st.get("current_stage") == "complete",
                   "final lock: submitted from the real control and LOCKED",
                   str(st.get("current_stage")))
        row("final lock", "yes", f"stage={st.get('current_stage')}", "PASS" if ok else "FAIL")
        again = D.post({"action": "researchdecision", "session_token": tok,
                        "final_action": "monitor", "disposition": "reject"})
        ok = check(again.get("ok") is False,
                   "and the server refuses a direct route edit of the locked final decision")

        # ---------------------------------------------------- next period
        page.evaluate(remount)
        page.wait_for_timeout(6000)
        ok = check(page.evaluate("() => !!document.getElementById('dc-advance-btn')"),
                   "next period: the advance control is offered once the period is complete")
        page.click("#dc-advance-btn")
        page.wait_for_timeout(3000)
        st = D.post({"action": "researchsequencestate", "session_token": tok})
        ok = check(st.get("period") == "P2" and st.get("current_stage") == "evidence",
                   "the governed transition to the next controlled period occurred",
                   json.dumps({k: st.get(k) for k in ("period", "current_stage")}))
        row("next period", "yes", f"period={st.get('period')} stage={st.get('current_stage')}",
            "PASS" if ok else "FAIL")
        dom = page.evaluate("() => document.body.innerText")
        ok = check("cost variance beyond threshold" not in dom,
                   "and the next period starts clean, with no recommendation on the page")

        # ---------------------------------------------------- reload / resume
        # DIAGNOSTIC BEFORE THE CLAIM: prove the server is still answering, so a navigation
        # timeout is attributed to the right side rather than guessed at.
        page.remove_listener("dialog", accept_dialog)
        # AND drop the abort routes. A fresh page with no route handlers navigates fine in this
        # container (proved below by the duplicate-tab step), while this page -- the only one
        # carrying abort handlers -- does not. That localises the hang to the Playwright route
        # interception, which is test scaffolding, not application behaviour.
        page.unroute_all(behavior="ignoreErrors")
        srv_ok = False
        try:
            urllib.request.urlopen(BASE + "/readyz", timeout=10).read()
            srv_ok = True
        except Exception as exc:
            print("    server probe failed:", exc)
        check(srv_ok, "the server is still answering before the reload is attempted")
        try:
            page.goto(BASE + "/?resume=1", wait_until="commit", timeout=60000)
            nav_error = ""
        except Exception as exc:
            nav_error = str(exc).splitlines()[0]
            print("    navigation error:", nav_error)
        page.wait_for_timeout(8000)
        st_after = D.post({"action": "researchsequencestate", "session_token": tok})
        ok = check(not nav_error and st_after.get("period") == "P2"
                   and st_after.get("current_stage") == "evidence",
                   "reload/resume: a full browser reload lands exactly where the rows say",
                   f"{nav_error} " + json.dumps({k: st_after.get(k)
                                                 for k in ("period", "current_stage")}))
        row("reload / resume", "yes",
            f"period={st_after.get('period')} stage={st_after.get('current_stage')}",
            "PASS" if ok else "FAIL")

        # Back navigation must not reopen the locked period.
        try:
            page.go_back(wait_until="commit", timeout=30000)
            back_error = ""
        except Exception as exc:
            back_error = str(exc).splitlines()[0]
            print("    back-navigation error:", back_error)
        page.wait_for_timeout(3000)
        st_back = D.post({"action": "researchsequencestate", "session_token": tok})
        ok = check(not back_error and st_back.get("period") == "P2",
                   "browser back navigation does not reopen the locked period",
                   f"{back_error} {st_back.get('period')}")
        row("back navigation", "yes", f"period stays {st_back.get('period')}",
            "PASS" if ok else "FAIL")

        # Duplicate tab reading the same session must not move the state machine.
        tab2 = browser.new_page()
        tab2.goto(BASE + "/", wait_until="domcontentloaded")
        tab2.evaluate("t => sessionStorage.setItem('og-session-token', t)", tok)
        tab2.goto(BASE + "/", wait_until="domcontentloaded")
        tab2.wait_for_timeout(5000)
        st_tab = D.post({"action": "researchsequencestate", "session_token": tok})
        ok = check(st_tab.get("period") == "P2" and st_tab.get("current_stage") == "evidence",
                   "a duplicate tab does not move the state machine")
        row("duplicate tab", "yes", f"period={st_tab.get('period')}", "PASS" if ok else "FAIL")
        tab2.close()

        ok = check(not errors, "no JavaScript console error anywhere in the browser sequence",
                   "; ".join(errors[:3]))
        row("javascript errors", "yes", f"{len(errors)} page errors", "PASS" if ok else "FAIL")
        browser.close()

    # ---------------------------------------------------- completion + all 36 route identities
    print()
    print("=" * 78)
    print("ALL 36 ROUTE IDENTITIES, VERIFIED MECHANICALLY AFTER THE BROWSER WALK")
    print("=" * 78)
    # SEEDED WITH WHAT THE BROWSER ITSELF WALKED. The browser consumed the first project's
    # P1 before this loop began, so a loop that only counted what IT reached would report 35
    # and call a complete walk incomplete.
    reached: set[tuple[str, str]] = {(first_project, "P1")}
    by_scenario = P["by_scenario"]
    for _ in range(200):
        state = D.post({"action": "researchsequencestate", "session_token": tok})
        if state.get("all_assignments_complete"):
            break
        ev = D.post({"action": "researchevidenceget", "session_token": tok})
        if not ev.get("ok"):
            break
        reached.add((by_scenario[ev["scenario_id"]], ev["period"]))
        if D.post({"action": "researchsequencestate",
                   "session_token": tok}).get("current_stage") == "evidence":
            D.post({"action": "researchprejudgment", "session_token": tok,
                    "pre_action": "monitor", "pre_confidence": 50})
        D.post({"action": "researchreveal", "session_token": tok})
        D.post({"action": "researchdecision", "session_token": tok,
                "final_action": "escalate", "disposition": "accept", "final_confidence": 70})
        D.post({"action": "researchadvance", "session_token": tok})
    ok = check(len(reached) == 36, "all 36 project-period route identities were reached",
               f"{len(reached)}: {sorted(reached)[:4]}")
    row("36 route identities", "yes", f"{len(reached)} of 36 reached",
        "PASS" if ok else "FAIL")

    final_state = D.post({"action": "researchsequencestate", "session_token": tok})
    ok = check(final_state.get("all_assignments_complete") is True,
               "completion: the study reports complete after all 36 project-periods",
               json.dumps(final_state)[:160])
    row("completion", "yes", f"all_assignments_complete={final_state.get('all_assignments_complete')}",
        "PASS" if ok else "FAIL")

    out = ROOT / "code_audit" / "run38_browser_qualification.csv"
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["surface", "reached", "observed", "result"])
        w.writerows(ROWS)

    passed = sum(1 for ok_, _, _ in RESULTS if ok_)
    print()
    for ok_, label, detail in RESULTS:
        if not ok_:
            print(f"FAILED: {label}   {detail}")
    print(f"BROWSER SURFACES: {len(ROWS)} recorded, "
          f"{sum(1 for r in ROWS if r[-1] == 'PASS')} PASS")
    print(f"RESULT: {passed}/{len(RESULTS)} checks passed")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
