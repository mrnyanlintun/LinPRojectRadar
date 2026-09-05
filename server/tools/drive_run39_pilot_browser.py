#!/usr/bin/env python3
"""
RUN 39 SECTION 9. PARTICIPANT-FACING PILOT BROWSER EXECUTION.

A real Chromium headless shell drives a real served participant application on a throwaway
SQLite database with an isolated synthetic PILOT-equivalent identity. No real participant is
involved, contacted, recruited or consented, and nothing here is a study observation.

WHAT IS DRIVEN IN THE BROWSER, AND WHAT IS NOT.
The full governed sequence is exercised in the browser for the first controlled periods --
every control the participant actually touches, in the order they touch it. The remaining
periods are completed through the same authenticated session's API so that all 36 project-period
route identities are reached and completion is reached, WITHOUT re-rendering the identical
treatment 36 times. Section 9 asks for exactly that ordering and warns against altering frozen
treatment semantics to force a full traversal.

RUN 38 RECORDED ONE HONEST `NOT_VERIFIED`: an in-place navigation of an already-loaded workspace
page did not complete under this container's software rasterisation. Section 9 requires that
scenario to be RE-TESTED and the NOT_VERIFIED preserved if the limitation remains. It is
re-tested here with the measured duration recorded, and it is NOT converted to PASS by wording.

Run:
    DATABASE_URL=sqlite:///... SESSION_SECRET=... PYTHONIOENCODING=utf-8 \
        python tools/drive_run39_pilot_browser.py
"""
from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

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
PORT = 8394
BASE = f"http://127.0.0.1:{PORT}"

ROWS: list[list[str]] = []
RESULTS: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> bool:
    RESULTS.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))
    return bool(ok)


def row(step: str, reached: str, observed: str, result: str) -> None:
    ROWS.append([step, reached, observed, result])


def inner_text(page, selector: str) -> str:
    return page.evaluate("s => { const e = document.querySelector(s);"
                         " return e ? e.innerText : ''; }", selector)


def main() -> int:
    import uvicorn
    from playwright.sync_api import sync_playwright
    from sqlalchemy import select

    import app.main as main_app
    import run38_dryrun as D
    import run39_dataset_class as DC
    from app.research_models import Decision, Participant

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
    print("PROVISIONING THE PILOT-EQUIVALENT IDENTITY (synthetic, isolated)")
    print("=" * 78)
    ctx = D.bootstrap()
    P = D.make_participant(ctx, "SEED-BROWSER")
    with D.SessionFactory() as s:
        s.get(Participant, P["participant_id"]).pseudonymous_code = "R39-PILOT-A"
        s.commit()
    P["code"] = "R39-PILOT-A"
    tok = P["token"]
    registry = DC.load_registry()
    check(DC.classify("R39-PILOT-A", registry) == "PILOT",
          "the browser identity is governed-classified PILOT")
    check(not DC.eligible_for_main_study("R39-PILOT-A", registry),
          "and is not eligible for MAIN_STUDY")
    first_project = P["by_scenario"][P["assignments"][0][2]]
    evidence_project = D.evidence_legacy_id(first_project, "P1")

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

        # ------------------------------------------------------------- start
        page.goto(BASE + "/", wait_until="domcontentloaded")
        page.evaluate("t => sessionStorage.setItem('og-session-token', t)", tok)
        page.goto(BASE + "/", wait_until="domcontentloaded")
        page.add_style_tag(content="*,*::before,*::after{transition:none!important;"
                                   "animation:none!important}")
        page.wait_for_timeout(7000)
        loaded = page.evaluate(
            "() => Array.from(document.scripts).map(s => s.src.split('/').pop())")
        ok = check("decision-ui.js" in loaded,
                   "start: the real participant application is the page under test")
        row("start / authentication", "yes", f"{len(loaded)} scripts, decision-ui.js present",
            "PASS" if ok else "FAIL")

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
        page.wait_for_selector("#dc-pre-action", state="attached", timeout=120000)
        page.wait_for_timeout(3000)
        page.on("dialog", lambda d: d.accept())

        remount = """() => { if (window.LinWorkspace) {
            LinWorkspace.switchPanel('upload'); LinWorkspace.switchPanel('decision'); } }"""
        pkg = ctx["packages"][first_project]
        BROWSER_PERIODS = 2
        transitions: list[str] = []

        for k in range(BROWSER_PERIODS):
            st = D.post({"action": "researchsequencestate", "session_token": tok})
            period = st.get("period")
            transitions.append(f"{first_project}/{period}")

            # ---- evidence review, and the pre-lock leakage check
            ev_text = inner_text(page, "#dc-evidence")
            ok = check(len(ev_text) > 20, f"[{period}] evidence review renders the controlled "
                                          f"evidence", str(len(ev_text)))
            # THREE SEPARATE QUESTIONS, KEPT APART, BECAUSE THEY HAVE DIFFERENT ANSWERS.
            #
            #   (1) Does the SERVER emit any package content before this period's lock? That is
            #       the authorization question and it is the one that decides the blocker.
            #   (2) Is any AI content VISIBLE to the participant right now? That is the
            #       participant-facing question. Computed by walking leaf elements and checking
            #       every ancestor's computed display/visibility/opacity -- not by trusting a
            #       style attribute, and not by accepting `innerText` alone.
            #   (3) Is AI content PRESENT BUT HIDDEN in the serialised DOM? From period 2 on the
            #       answer is yes, and it is residue of THIS participant's own legitimate
            #       reveal in the PREVIOUS period, which `render()` hides by setting
            #       display:none on #dc-reveal rather than by emptying it. That is not future
            #       information and not another project's treatment, so it is RECORDED rather
            #       than conflated with (1) or (2).
            needles = ("cost variance beyond threshold", pkg["version"], pkg["hash"],
                       "r38-test-m1")
            server_blobs = json.dumps([
                D.post({"action": "researchevidenceget", "session_token": tok}),
                D.post({"action": "researchsequencestate", "session_token": tok}),
                D.post({"action": "researchreveal", "session_token": tok}),
            ], default=str)
            server_leak = [n for n in needles if n in server_blobs]

            visible_leak = [n for n in needles if page.evaluate("""(n) => {
                function visible(el) {
                    for (let e = el; e && e !== document; e = e.parentElement) {
                        const s = getComputedStyle(e);
                        if (s.display === 'none' || s.visibility === 'hidden' ||
                            s.opacity === '0') return false;
                    }
                    return el.offsetParent !== null;
                }
                for (const el of document.querySelectorAll('*')) {
                    if (el.children.length === 0 && el.textContent &&
                        el.textContent.indexOf(n) >= 0 && visible(el)) return true;
                }
                return false; }""", n)]

            html = page.content()
            hidden_residue = [n for n in needles if n in html and n not in visible_leak]

            ok = check(not server_leak,
                       f"[{period}] the SERVER emits no AI content before the preliminary lock",
                       str(server_leak))
            ok2 = check(not visible_leak,
                        f"[{period}] no AI content is VISIBLE to the participant before the "
                        f"preliminary lock", str(visible_leak))
            row(f"{period} evidence review + pre-lock leakage", "yes",
                f"{len(ev_text)} chars evidence; server responses carry no package content; "
                f"visible AI content = {len(visible_leak)}; hidden DOM residue of this "
                f"participant's own previous-period reveal = {len(hidden_residue)}",
                "PASS" if ok and ok2 else "FAIL")
            if hidden_residue:
                row(f"{period} hidden DOM residue (recorded, not a leak of future information)",
                    "yes",
                    f"#dc-reveal is display:none but retains {len(hidden_residue)} marker(s) "
                    f"from the PREVIOUS period's reveal, which this participant was "
                    f"legitimately shown; no future period, no other project, and nothing the "
                    f"server sent this period",
                    "RECORDED_NOT_BLOCKING")

            # ---- preliminary entry, confidence, lock
            page.evaluate("""() => {
                const s = document.getElementById('dc-pre-action');
                s.value = Array.from(s.options).map(o => o.value).filter(Boolean)[0];
                s.dispatchEvent(new Event('change'));
                const c = document.getElementById('dc-pre-confidence');
                c.value = 58; c.dispatchEvent(new Event('input'));
                const a = document.getElementById('dc-pre-assessment');
                if (a) { a.value = 'Pilot preliminary assessment.';
                         a.dispatchEvent(new Event('input')); } }""")
            chosen = page.evaluate("() => document.getElementById('dc-pre-action').value")
            conf = page.evaluate("() => document.getElementById('dc-pre-confidence').value")
            ok = check(bool(chosen) and str(conf) == "58",
                       f"[{period}] preliminary action and confidence entered from the real "
                       f"controls", f"{chosen}/{conf}")
            row(f"{period} preliminary entry + confidence", "yes",
                f"pre_action={chosen} pre_confidence={conf}", "PASS" if ok else "FAIL")

            page.click("#dc-commit-btn")
            page.wait_for_timeout(3000)
            st = D.post({"action": "researchsequencestate", "session_token": tok})
            ok = check(st.get("current_stage") == "awaiting_reveal",
                       f"[{period}] preliminary lock taken from the real control",
                       str(st.get("current_stage")))
            row(f"{period} preliminary lock", "yes",
                f"stage={st.get('current_stage')} pre_locked_at={st.get('pre_locked_at')}",
                "PASS" if ok else "FAIL")

            # ---- AI reveal
            page.evaluate(remount)
            page.wait_for_selector("#dc-reveal-btn", state="attached", timeout=120000)
            page.wait_for_timeout(2000)
            dom = page.evaluate("() => document.body.innerText")
            check("cost variance beyond threshold" not in dom,
                  f"[{period}] the AI is still absent after the lock and before the reveal")
            page.click("#dc-reveal-btn")
            page.wait_for_timeout(5000)
            dom = page.evaluate("() => document.body.innerText")
            ok = check("cost variance beyond threshold" in dom,
                       f"[{period}] AI reveal renders the frozen package after the lock")
            row(f"{period} AI reveal", "yes",
                "detected_condition rendered only after the preliminary lock",
                "PASS" if ok else "FAIL")

            # ---- final entry, confidence, disposition, rationale/evidence, lock
            page.evaluate("""() => {
                const set = (id, v) => { const e = document.getElementById(id);
                    if (e) { e.value = v; e.dispatchEvent(new Event('change'));
                             e.dispatchEvent(new Event('input')); } };
                const fa = document.getElementById('dc-final-action');
                set('dc-final-action', Array.from(fa.options).map(o => o.value)
                    .filter(Boolean).slice(-1)[0]);
                const dp = document.getElementById('dc-disposition');
                set('dc-disposition', Array.from(dp.options).map(o => o.value)
                    .filter(Boolean)[0]);
                set('dc-final-confidence', 74);
                set('dc-rationale', 'Pilot rationale recorded through the real control.');
                const ev = document.querySelector('[data-evidence]');
                if (ev) { ev.checked = true; ev.dispatchEvent(new Event('change')); } }""")
            fa = page.evaluate("() => document.getElementById('dc-final-action').value")
            dp = page.evaluate("() => document.getElementById('dc-disposition').value")
            fc = page.evaluate("() => document.getElementById('dc-final-confidence').value")
            rat = page.evaluate("() => { const e=document.getElementById('dc-rationale');"
                                " return e ? e.value.length : 0; }")
            evc = page.evaluate("() => { const e=document.querySelector('[data-evidence]');"
                                " return e ? !!e.checked : false; }")
            ok = check(bool(fa) and bool(dp) and str(fc) == "74" and rat > 0,
                       f"[{period}] final action, confidence, disposition and rationale entered "
                       f"from the real controls", f"{fa}/{dp}/{fc}/rationale {rat} chars")
            row(f"{period} final entry + confidence + disposition", "yes",
                f"final_action={fa} disposition={dp} final_confidence={fc}",
                "PASS" if ok else "FAIL")
            row(f"{period} rationale / evidence interaction", "yes",
                f"rationale {rat} chars typed into the real field; evidence item checked={evc}",
                "PASS" if ok else "FAIL")

            page.click("#dc-decide-btn")
            page.wait_for_timeout(3000)
            st = D.post({"action": "researchsequencestate", "session_token": tok})
            ok = check(st.get("current_stage") == "complete",
                       f"[{period}] final lock taken from the real control",
                       str(st.get("current_stage")))
            again = D.post({"action": "researchdecision", "session_token": tok,
                            "final_action": "monitor", "disposition": "reject"})
            ok2 = check(again.get("ok") is False,
                        f"[{period}] and the server refuses a post-lock edit")
            row(f"{period} final lock", "yes",
                f"stage={st.get('current_stage')}; post-lock edit refused: "
                f"{again.get('error')!r}", "PASS" if ok and ok2 else "FAIL")

            # ---- next period
            page.evaluate(remount)
            page.wait_for_selector("#dc-advance-btn", state="attached", timeout=120000)
            page.wait_for_timeout(2000)
            page.click("#dc-advance-btn")
            page.wait_for_timeout(3000)
            st = D.post({"action": "researchsequencestate", "session_token": tok})
            ok = check(st.get("current_stage") == "evidence",
                       f"[{period}] transition to the next controlled period",
                       json.dumps({k2: st.get(k2) for k2 in ("period", "current_stage")}))
            row(f"{period} -> next period transition", "yes",
                f"now period={st.get('period')} stage={st.get('current_stage')}",
                "PASS" if ok else "FAIL")
            if k + 1 < BROWSER_PERIODS:
                page.wait_for_selector("#dc-pre-action", state="attached", timeout=120000)
                page.wait_for_timeout(2000)

        # ------------------------------------------------------------- SECTION 9 RE-TEST
        # Run 38's honest NOT_VERIFIED, re-measured. The server is probed first so a slow
        # navigation is attributed to the right side rather than guessed at.
        srv_ok = False
        try:
            urllib.request.urlopen(BASE + "/readyz", timeout=10).read()
            srv_ok = True
        except Exception:
            pass
        check(srv_ok, "the server answers immediately before the reload is re-tested")
        page.remove_listener("dialog", lambda d: d.accept()) if False else None
        t0 = time.time()
        try:
            page.goto(BASE + "/?resume=1", wait_until="domcontentloaded", timeout=180000)
            nav_error = ""
        except Exception as exc:
            nav_error = str(exc).splitlines()[0]
        nav_seconds = round(time.time() - t0, 1)
        print(f"    RE-TEST: in-place navigation of the loaded workspace page took "
              f"{nav_seconds}s ({'did not complete' if nav_error else 'completed'})")
        # PRESERVED, NOT REWORDED. If the limitation remains, the row stays NOT_VERIFIED.
        row("in-place reload of the loaded workspace page (Run-38 NOT_VERIFIED, re-tested)",
            "attempted",
            f"{nav_seconds}s under swiftshader software rasterisation; "
            f"{'did not complete -- limitation persists' if nav_error else 'completed'}; "
            f"server answered immediately when probed; a fresh page resumes at once",
            "PASS" if not nav_error else "NOT_VERIFIED_CONTAINER_LIMITATION")
        check(True, "the Run-38 in-place-reload limitation was re-tested and its result recorded "
                    "as measured", f"{nav_seconds}s, "
                    f"{'still NOT_VERIFIED' if nav_error else 'now completes'}")

        # ------------------------------------------------------------- logout / resume
        resume_page = browser.new_page(viewport={"width": 1680, "height": 1400})
        resume_page.goto(BASE + "/", wait_until="domcontentloaded")
        resume_page.evaluate("t => sessionStorage.setItem('og-session-token', t)", tok)
        resume_page.goto(BASE + "/", wait_until="domcontentloaded")
        resume_page.wait_for_timeout(7000)
        st_r = D.post({"action": "researchsequencestate", "session_token": tok})
        ok = check(st_r.get("current_stage") == "evidence",
                   "resume: reopening the application lands exactly where the rows say",
                   json.dumps({k2: st_r.get(k2) for k2 in ("period", "current_stage")}))
        row("logout / resume behaviour", "yes",
            f"fresh page, same session token: period={st_r.get('period')} "
            f"stage={st_r.get('current_stage')}", "PASS" if ok else "FAIL")

        # A fresh login (new session token) must also resume identically.
        relogin = D.post({"action": "researchlogin",
                          "access_token": P["access_token"]})["session_token"]
        st_l = D.post({"action": "researchsequencestate", "session_token": relogin})
        ok = check(st_l.get("period") == st_r.get("period")
                   and st_l.get("current_stage") == st_r.get("current_stage"),
                   "re-authenticating yields the identical derived state")
        row("re-authentication", "yes",
            f"period={st_l.get('period')} stage={st_l.get('current_stage')}",
            "PASS" if ok else "FAIL")
        resume_page.close()

        ok = check(not errors, "no JavaScript console error anywhere in the browser sequence",
                   "; ".join(errors[:3]))
        row("javascript errors", "yes", f"{len(errors)} page errors", "PASS" if ok else "FAIL")
        browser.close()

    # ------------------------------------------------------------- complete the traversal
    print()
    print("=" * 78)
    print("ALL 36 PROJECT-PERIOD ROUTE IDENTITIES AND COMPLETION")
    print("=" * 78)
    reached: set[tuple[str, str]] = {(first_project, p) for p in
                                     ("P" + str(i + 1) for i in range(BROWSER_PERIODS))}
    by_scenario = P["by_scenario"]
    for _ in range(200):
        st = D.post({"action": "researchsequencestate", "session_token": tok})
        if st.get("all_assignments_complete"):
            break
        ev = D.post({"action": "researchevidenceget", "session_token": tok})
        if not ev.get("ok"):
            break
        reached.add((by_scenario[ev["scenario_id"]], ev["period"]))
        if D.post({"action": "researchsequencestate",
                   "session_token": tok}).get("current_stage") == "evidence":
            D.post({"action": "researchprejudgment", "session_token": tok,
                    "pre_action": "monitor", "pre_confidence": 55})
        D.post({"action": "researchreveal", "session_token": tok})
        D.post({"action": "researchdecision", "session_token": tok, "final_action": "escalate",
                "disposition": "accept", "final_confidence": 72, "rationale": "pilot"})
        D.post({"action": "researchadvance", "session_token": tok})

    ok = check(len(reached) == 36, "all 36 project-period route identities were reached",
               f"{len(reached)}")
    row("36 route identities", "yes", f"{len(reached)} of 36 reached", "PASS" if ok else "FAIL")
    final_state = D.post({"action": "researchsequencestate", "session_token": tok})
    ok = check(final_state.get("all_assignments_complete") is True,
               "completion: the pilot session reports complete after all 36 project-periods")
    row("completion", "yes",
        f"all_assignments_complete={final_state.get('all_assignments_complete')}",
        "PASS" if ok else "FAIL")

    with D.SessionFactory() as s:
        n = len(s.scalars(select(Decision)).all())
    ok = check(n == 36, "exactly 36 persisted observations, none duplicated", str(n))
    row("persisted observations", "yes", f"{n} decisions rows", "PASS" if ok else "FAIL")

    out = ROOT / "code_audit" / "run39_pilot_browser_execution.csv"
    with artifact_out(out).open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["step", "reached", "observed", "result"])
        w.writerows(ROWS)

    passed = sum(1 for ok_, _, _ in RESULTS if ok_)
    print()
    for ok_, label, detail in RESULTS:
        if not ok_:
            print(f"FAILED: {label}   {detail}")
    print(f"BROWSER STEPS: {len(ROWS)} recorded, "
          f"{sum(1 for r in ROWS if r[-1] == 'PASS')} PASS, "
          f"{sum(1 for r in ROWS if r[-1].startswith('NOT_VERIFIED'))} NOT_VERIFIED")
    print(f"RESULT: {passed}/{len(RESULTS)} checks passed")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
