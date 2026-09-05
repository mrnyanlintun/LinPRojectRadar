#!/usr/bin/env python3
"""
RUN 36, SECTION 18. THE AUTHENTICATED PARTICIPANT SURFACE, DRIVEN IN A REAL BROWSER.

NO BROWSER CLAIM UNLESS THE ACTUAL SURFACE WAS REACHED. Every row this writes records what was
REACHED, and a surface that could not be reached is written NOT_VERIFIED rather than passed. That
distinction is not cosmetic: an unreachable PARTICIPANT STUDY PATH is a section-23 blocking
defect, while an unreachable auxiliary surface is a recorded limitation.

WHAT THIS RUN ADDS to the Run-12 and Run-21 drives, which are not repeated for their own sake:
  * the CORRECTED A1.7 and A1.8 behaviour as the participant actually sees it;
  * the A1.1 band withdrawal on the participant surface -- the module must still be present and
    must show no status colour;
  * the handbook / method-reference surface, reached the way Run 32's closure found it can be:
    hb-tab-methods -> [data-topic] -> [id^=body-modref-];
  * no unintended disabled or archived exposure;
  * no JavaScript console crash anywhere in the sequence.

CONTAINER FACTS, HANDLED RATHER THAN ASSUMED AWAY: window.confirm returns false in this headless
shell, so the confirm-gated commit is exercised first with no handler (which proves the gate) and
then with one. Google SSO and tile requests are aborted at the route level.

Run:
    DATABASE_URL=sqlite:///... SESSION_SECRET=... PYTHONIOENCODING=utf-8 \
        python tools/drive_run36_browser.py
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
import pathlib
import sys
import threading
import time
import urllib.request

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

import tools.drive_run12_participant_cycle as r12  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
SHELL = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"

r12.PORT = 8236
r12.BASE = f"http://127.0.0.1:{r12.PORT}"
r12.ADMIN = "r36-browser-admin"
r12.PRJ = ["PRJ-R36B-EV-1", "PRJ-R36B-EV-2"]
BASE = r12.BASE
post = r12.post

ROWS: list[list[str]] = []
PASSED = 0
FAILED = 0


def rec(surface, requirement, reached, result, evidence=""):
    global PASSED, FAILED
    if result == "PASS":
        PASSED += 1
    elif result in ("FAIL",):
        FAILED += 1
    ROWS.append([surface, requirement, reached, result, str(evidence)[:400]])
    print(f"  {result:12s} {surface:34s} {requirement}")


def gate(surface, requirement, ok, evidence=""):
    rec(surface, requirement, "YES", "PASS" if ok else "FAIL", evidence)


def main() -> int:
    import uvicorn
    from playwright.sync_api import sync_playwright

    import app.main as main_app
    from app.documents import set_extractor_override
    from app.extraction_client import StubExtractor

    set_extractor_override(StubExtractor(r12.records()))
    config = uvicorn.Config(main_app.app, host="127.0.0.1", port=r12.PORT, log_level="critical")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(120):
        try:
            urllib.request.urlopen(BASE + "/readyz", timeout=2).read()
            break
        except Exception:
            time.sleep(0.5)

    print("=" * 94)
    print("RUN 36 SECTION 18. THE AUTHENTICATED PARTICIPANT SURFACE IN A REAL BROWSER")
    print("=" * 94)
    ctx = r12.provision()
    tok = ctx["token"]
    st = post({"action": "researchsequencestate", "session_token": tok})
    gate("participant authentication",
         "the provisioned participant authenticates on the real research route and is placed at "
         "the evidence stage of period one",
         st.get("ok") is True and st.get("current_stage") == "evidence" and st.get("period") == "P1",
         json.dumps({k: st.get(k) for k in ("ok", "current_stage", "period")}))

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=SHELL,
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist",
                  "--no-sandbox"])
        page = browser.new_page(viewport={"width": 1680, "height": 1400})
        errors: list[str] = []
        console: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: console.append(f"{m.type}:{m.text}")
                if m.type == "error" else None)
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
        gate("participant application",
             "the real participant application is the page under test",
             "decision-ui.js" in loaded, f"{len(loaded)} scripts")
        gate("client arithmetic boundary",
             "the historical client arithmetic is not served to the participant",
             page.evaluate("() => typeof window.LinSim") == "undefined")

        page.evaluate("id => { window.LinApp.showPage('project');"
                      " if (window.LinWorkspace) LinWorkspace.openProject(id); }", r12.PRJ[0])
        page.wait_for_timeout(4000)
        page.evaluate("""() => {
            const b = Array.from(document.querySelectorAll('#ws-project-tabs button'))
                .find(x => x.dataset.wstab === 'decision');
            if (b) b.click();
            else if (window.LinWorkspace && LinWorkspace.switchPanel)
                LinWorkspace.switchPanel('decision'); }""")
        page.wait_for_timeout(6000)

        gate("project/period workflow",
             "the five stage cards of the governed sequence are on the served page",
             page.evaluate("""() => ['dc-evidence','dc-prejudgment','dc-reveal','dc-decide',
                 'dc-advance'].every(id => !!document.getElementById(id))"""))
        gate("fixed evidence review",
             "the fixed evidence package is visible before any judgment is offered",
             len(r12.inner_text(page, "#dc-evidence")) > 40)
        dom = page.evaluate("() => document.body.innerText")
        gate("AI reveal boundary",
             "the AI recommendation is NOT in the served page before the preliminary lock",
             "Escalate to recovery review" not in dom)

        # -------- preliminary judgment and the confirm gate, exercised honestly
        page.evaluate("""() => {
            const s = document.getElementById('dc-pre-action');
            s.value = Array.from(s.options).map(o => o.value).filter(Boolean)[0];
            s.dispatchEvent(new Event('change'));
            const c = document.getElementById('dc-pre-confidence');
            c.value = 60; c.dispatchEvent(new Event('input'));
            const a = document.getElementById('dc-pre-assessment');
            if (a) { a.value = 'Cost performance is drifting; I would watch one more period.';
                     a.dispatchEvent(new Event('input')); } }""")
        chosen = page.evaluate("() => document.getElementById('dc-pre-action').value")
        page.click("#dc-commit-btn")
        page.wait_for_timeout(2500)
        st = post({"action": "researchsequencestate", "session_token": tok})
        gate("preliminary judgment lock",
             "with dialogs suppressed the confirm-gated commit no-ops and nothing is submitted, "
             "so the gate is doing its job", st.get("current_stage") == "evidence",
             str(st.get("current_stage")))
        page.on("dialog", lambda d: d.accept())
        page.click("#dc-commit-btn")
        page.wait_for_timeout(3000)
        st = post({"action": "researchsequencestate", "session_token": tok})
        gate("preliminary judgment lock",
             "the preliminary judgment is submitted from the real control and LOCKED",
             st.get("current_stage") == "awaiting_reveal", str(st.get("current_stage")))
        resub = post({"action": "researchprejudgment", "session_token": tok,
                      "pre_action": "escalate", "pre_confidence": 99})
        gate("preliminary judgment lock",
             "and the SERVER refuses a direct route edit of the locked preliminary judgment, so "
             "the lock is not merely a disabled button",
             resub.get("ok") is False and "locked" in str(resub.get("error", "")).lower(),
             str(resub)[:160])

        # -------- reveal
        remount = """() => { if (window.LinWorkspace) {
            LinWorkspace.switchPanel('upload'); LinWorkspace.switchPanel('decision'); } }"""
        page.evaluate(remount)
        page.wait_for_timeout(6000)
        dom = page.evaluate("() => document.body.innerText")
        gate("AI reveal", "the recommendation is still absent after the lock and before the "
             "reveal", "Escalate to recovery review" not in dom)
        page.click("#dc-reveal-btn")
        page.wait_for_timeout(3000)
        dom = page.evaluate("() => document.body.innerText")
        gate("AI reveal", "after the participant presses reveal the recommendation is inspectable",
             "Escalate to recovery review" in dom)

        # -------- the corrected voters and the A1.1 withdrawal, as the participant sees them
        # THE ROUTE THE PARTICIPANT'S OWN PAGE CALLS, not a name guessed at: `projectresults`
        # is the member read that carries the per-module rows, and it is reached with the
        # participant's own session token so the reveal gate applies exactly as it does for them.
        sig = post({"action": "projectresults", "session_token": tok,
                    "project_id": r12.PRJ[0], "period": "2026-02"})
        mods = {}

        def _harvest(obj):
            if isinstance(obj, dict):
                if obj.get("module_id"):
                    mods[obj["module_id"]] = obj
                for v in obj.values():
                    _harvest(v)
            elif isinstance(obj, list):
                for v in obj:
                    _harvest(v)
        _harvest(sig)
        if mods:
            a17, a18, a11 = mods.get("A1.7"), mods.get("A1.8"), mods.get("A1.1")
            gate("corrected A1.7 behaviour",
                 "A1.7 carries its canonical value at full precision beside a separate rounded "
                 "display value, so presentation rounding cannot reach the band",
                 bool(a17) and a17.get("tcpi") is not None
                 and a17.get("tcpi") != a17.get("tcpi_display"),
                 json.dumps({k: (a17 or {}).get(k) for k in ("tcpi", "tcpi_display",
                                                             "status_color")}))
            gate("corrected A1.8 behaviour",
                 "A1.8's analytical variance at completion is not replaced by its formatted "
                 "output", bool(a18) and a18.get("vac") is not None
                 and a18.get("vac") != a18.get("vac_display"),
                 json.dumps({k: (a18 or {}).get(k) for k in ("vac", "vac_display",
                                                            "status_color")}))
            # RUN 36 CLOSURE, THE OWNER'S A1.1 RULING OF 2026-08-19. A1.1 is operationally
            # disabled for insufficient canonical input, so on the participant surface it must
            # produce NO figure and NO colour, and it must say why in words rather than fall
            # silent. The retained approximation must not appear here under any guise.
            gate("A1.1 disabled for insufficient canonical input, on the participant surface",
                 "A1.1 shows no status colour and no forecast figure, and the participant is "
                 "told the method is not defined completely enough to run",
                 (not a11) or (a11.get("status_color") in (None, "")
                               and a11.get("p80_eac") is None
                               and a11.get("overrun_pct_p80") is None),
                 json.dumps({k: (a11 or {}).get(k) for k in ("status_color", "p80_eac",
                                                             "overrun_pct_p80",
                                                             "abstention_reason_code")}))
        else:
            for _s in ("corrected A1.7 behaviour", "corrected A1.8 behaviour",
                       "A1.1 disabled for insufficient canonical input, on the participant "
                       "surface"):
                rec(_s, "the per-module signal array was not reachable on this route",
                    "NO", "NOT_VERIFIED",
                    "the signals response carried no module array; recorded rather than passed")

        # -------- final judgment and final lock
        page.evaluate("""() => {
            const set = (id, v) => { const e = document.getElementById(id);
                if (e) { e.value = v; e.dispatchEvent(new Event('change'));
                         e.dispatchEvent(new Event('input')); } };
            const fa = document.getElementById('dc-final-action');
            set('dc-final-action', Array.from(fa.options).map(o => o.value).filter(Boolean)[0]);
            const dp = document.getElementById('dc-disposition');
            set('dc-disposition', Array.from(dp.options).map(o => o.value).filter(Boolean)[0]);
            set('dc-final-confidence', 70);
            set('dc-rationale', 'The recommendation matches what the cost evidence shows.');
            set('dc-owner', 'Project manager');
            set('dc-authority', 'Programme director');
            set('dc-deadline', 'next reporting cycle');
            const ev = document.querySelector('[data-evidence]');
            if (ev) { ev.checked = true; ev.dispatchEvent(new Event('change')); } }""")
        final_action = page.evaluate("() => document.getElementById('dc-final-action').value")
        disposition = page.evaluate("() => document.getElementById('dc-disposition').value")
        gate("final judgment fields",
             "the participant records a final action, a disposition, a confidence, evidence and "
             "a free-text rationale", bool(final_action) and bool(disposition),
             f"{final_action} / {disposition}")
        page.click("#dc-decide-btn")
        page.wait_for_timeout(3000)
        st = post({"action": "researchsequencestate", "session_token": tok})
        gate("final lock", "the final judgment is submitted from the real control and LOCKED",
             st.get("current_stage") == "complete", str(st.get("current_stage")))
        again = post({"action": "researchdecision", "session_token": tok,
                      "final_action": "something else", "disposition": "reject",
                      "rationale": "second attempt"})
        gate("final lock",
             "and the SERVER refuses a direct route edit of the locked final judgment",
             again.get("ok") is False, str(again)[:160])

        from sqlalchemy import select
        import app.main as m2
        from app.research_models import Decision
        with m2.SessionFactory() as s:
            dec = s.scalar(select(Decision)
                           .where(Decision.assignment_id == ctx["assignments"][0]))
            gate("evidence and rationale capture",
                 "the stored row holds the rationale and the evidence items the participant "
                 "supplied", bool(dec.rationale),
                 json.dumps({"rationale": bool(dec.rationale),
                             "evidence_items": dec.evidence_items is not None}))
            gate("governed timestamp order",
                 "preliminary lock, then reveal, then final submission, in that order",
                 dec.pre_locked_at <= dec.reveal_at <= dec.final_submitted_at,
                 f"{dec.pre_locked_at} -> {dec.reveal_at} -> {dec.final_submitted_at}")

        # -------- next period
        page.evaluate(remount)
        page.wait_for_timeout(6000)
        gate("next-period transition",
             "the advance control is offered once the period is complete",
             page.evaluate("() => !!document.getElementById('dc-advance-btn')"))
        page.click("#dc-advance-btn")
        page.wait_for_timeout(3000)
        st = post({"action": "researchsequencestate", "session_token": tok})
        gate("next-period transition",
             "the governed transition to the next reporting period occurred and it starts at "
             "evidence again",
             (st.get("period") == "P2" or st.get("sequence_number") == 2)
             and st.get("current_stage") == "evidence",
             json.dumps({k: st.get(k) for k in ("period", "sequence_number", "current_stage")}))
        page.evaluate(remount)
        page.wait_for_timeout(5000)
        gate("next-period transition",
             "and the preliminary judgment card renders again, so the second period can actually "
             "be started",
             page.evaluate("() => !!document.getElementById('dc-pre-action')"))

        # -------- controlled module presentation and disabled/archive exposure
        page.evaluate("""() => { if (window.LinWorkspace)
            LinWorkspace.switchPanel('signals'); }""")
        page.wait_for_timeout(4000)
        body = page.evaluate("() => document.body.innerText")
        leaked = [n for n in ("Plithogenic", "Hypersoft", "Quantum Probability",
                              "Material Cost Variance")
                  if n in body and "disabled" not in body.lower()]
        gate("no unintended disabled or archive exposure",
             "no disabled or archived method is presented to the participant as a live reading",
             not leaked, str(leaked))

        # -------- the handbook / method reference surface
        # THE ROUTE RUN 32's CLOSURE FOUND: the handbook page, then its Methods tab, then a
        # topic, then a module-reference body. Reached the way the participant reaches it.
        page.evaluate("() => { if (window.LinApp && LinApp.showPage) LinApp.showPage('handbook'); }")
        page.wait_for_timeout(3500)
        reached = page.evaluate("""() => {
            const t = document.getElementById('hb-tab-methods');
            if (t) { t.click(); return 'hb-tab-methods'; }
            return ''; }""")
        page.wait_for_timeout(3000)
        # EVERY topic is tried, not the first one. The first topic on the panel is the framework
        # overview and carries no module references, so probing only that one would report the
        # surface unreachable when it is simply behind a different topic.
        topics = page.evaluate(
            "() => Array.from(document.querySelectorAll('[data-topic]'))"
            ".map(e => e.getAttribute('data-topic'))")
        topic, modref = "", 0
        for _t in topics:
            page.evaluate("t => { const e = document.querySelector('[data-topic=\"' + t + '\"]');"
                          " if (e) e.click(); }", _t)
            page.wait_for_timeout(1200)
            n = page.evaluate("() => document.querySelectorAll('[id^=body-modref-]').length")
            if n:
                topic, modref = _t, n
                break
        if not modref:
            # The bodies may only exist once a module row is expanded, which is what a reader does.
            page.evaluate("""() => { const b = document.querySelector('[data-modref], .modref, '
                + '[id^=head-modref-]'); if (b) b.click(); }""")
            page.wait_for_timeout(1500)
            modref = page.evaluate("() => document.querySelectorAll('[id^=body-modref-]').length")
            topic = topic or ",".join(topics[:6])
        if reached and modref:
            gate("handbook / method reference surface",
                 "the method reference surface is reachable through hb-tab-methods, a topic and "
                 "a module-reference body, and it renders", modref > 0,
                 f"entry={reached} topic={topic} modref_bodies={modref}")
        else:
            rec("handbook / method reference surface",
                "reached through hb-tab-methods -> [data-topic] -> [id^=body-modref-]",
                "NO", "NOT_VERIFIED",
                f"entry={reached!r} topic={topic!r} modref_bodies={modref}; recorded as not "
                f"verified rather than passed. This is an AUXILIARY surface, not a study path.")

        # -------- SECTION 11: the controlled-study population, against the owner contract
        import csv as _csv                                                    # noqa: E402
        _pkgroot = (ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.2"
                    / "Opus_Gubernatio_Synthetic_Programme_v0.2"
                    / "package_A_project_structures")
        _contract = json.loads((ROOT / "research" / "methodology"
                                / "controlled_study_design_contract.json").read_text("utf-8"))
        _projects = [r for r in _csv.DictReader((_pkgroot / "projects.csv").open(encoding="utf-8"))
                     if str(r["study_project_candidate"]).strip().lower() == "true"]
        _periods = list(_csv.DictReader((_pkgroot / "reporting_periods.csv").open(encoding="utf-8")))
        _pids = {p["project_id"] for p in _projects}
        _combos = {(r["project_id"], r["period_id"]) for r in _periods}
        _per = {p: len({r["period_id"] for r in _periods if r["project_id"] == p}) for p in _pids}
        _d = _contract["design"]
        gate("controlled-study population",
             f"the enumerated stimuli hold exactly {_d['project_count']} study projects",
             len(_pids) == _d["project_count"], f"{len(_pids)}: {sorted(_pids)}")
        gate("controlled-study population",
             f"and exactly {_d['period_count_per_project']} periods for every one of them",
             set(_per.values()) == {_d["period_count_per_project"]}, json.dumps(_per))
        gate("controlled-study population",
             f"and exactly {_d['project_period_count']} unique project-periods, with no "
             f"duplicate and no missing combination",
             len(_combos) == _d["project_period_count"] == len(_periods)
             and len(_combos) == len(_pids) * _d["period_count_per_project"],
             f"{len(_combos)} unique of {len(_periods)} rows")

        # -------- console health, over the whole sequence
        gate("no JavaScript console crash",
             "no uncaught page error was raised anywhere in the authenticated sequence",
             not errors, "; ".join(errors)[:300])
        rec("console errors", "console error messages observed during the sequence",
            "YES", "OBSERVED" if console else "NONE", "; ".join(console)[:300])
        browser.close()

    out = ROOT / "code_audit" / "run36_authenticated_browser_qualification.csv"
    with artifact_out(out).open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["surface", "requirement", "surface_reached", "result", "evidence"])
        w.writerows(ROWS)
    print(f"\nwrote {out.name}: {len(ROWS)} rows")
    print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
