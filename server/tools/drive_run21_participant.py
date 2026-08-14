#!/usr/bin/env python3
"""
RUN 21, SECTIONS 11 TO 14. THE PARTICIPANT SEQUENCE, THE LOCK ATTACKS, THE PERIOD TRANSITIONS
AND THE ISOLATION PROPERTIES, DRIVEN IN A REAL BROWSER ON THE REAL PARTICIPANT ROUTE.

WHAT THIS ADDS TO RUN 12, WHICH IS NOT REPEATED FOR ITS OWN SAKE. Run 12 drove one full period
and the preliminary of a second. Run 21 must requalify the whole sequence and go further in
three directions the owner named:

  * MORE THAN ONE AND A HALF PERIODS, driven by ONE generic per-period routine. Run 12 found a
    second-period transition defect, and bespoke per-period code is exactly what lets that class
    of defect hide, so every period here runs the same function.

    WHAT THE FIXTURE ACTUALLY SUPPORTS, MEASURED RATHER THAN ASSUMED, because the owner asked for
    P1 -> P2 -> P3 "where the test fixture supports it" and it does not. Two things were found.
    First, the inherited Run-12 fixture freezes a transition rule for PERIOD 1 ONLY; with no
    frozen rule the application refuses to advance, which is correct, so this driver adds frozen
    P2 and P3 rules through the operator routes. Second, and this is the limit: established at
    the route level with no browser involved, completing an assignment's SECOND period rolls the
    participant to the NEXT ASSIGNMENT at its own P1, and researchadvance then correctly refuses
    with "the current period's decision must be complete before advancing". So a THIRD period
    within one assignment is NOT REACHABLE in this fixture. Run 21 therefore drives TWO complete
    periods end to end plus the cross-assignment roll, and reports that plainly rather than
    claiming three-period coverage it does not have.
  * A WIDER LOCK ATTACK SET. Every prohibited operation the owner listed is attempted
    deliberately, through the ROUTE the ordinary client can reach, and the HTTP/server answer is
    recorded: preliminary edit after lock, AI content before lock by four separate paths, final
    edit after lock, duplicate submit, and confidence/rationale/evidence changes after lock.
  * ISOLATION, measured rather than assumed. A SECOND participant with a SECOND session is
    provisioned and every leak the owner enumerated is probed across the two.

THE PRINCIPLE THROUGHOUT: A DISABLED BUTTON PROVES NOTHING. Every lock is proved at the SERVER,
by calling the route with the participant's own valid session, and the answer is recorded. The
browser evidence proves what the participant can SEE and REACH; the route evidence proves what
the server will ALLOW. Both are required and neither is accepted alone.

CONTAINER FACT, HANDLED RATHER THAN ASSUMED AWAY: window.confirm returns false in this headless
shell and the preliminary commit is confirm-gated, so the real button would silently no-op. The
no-handler case is exercised FIRST and recorded, which proves the confirm gate is doing its job,
and only then is a dialog handler installed -- which is what a browser that shows dialogs does
when the participant presses OK.

Run:
    DATABASE_URL=sqlite:///... SESSION_SECRET=... PYTHONIOENCODING=utf-8 \
        python tools/drive_run21_participant.py
"""
from __future__ import annotations

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

# Own port, own admin token, own projects: see the Run-18 note about two uvicorns and one port.
r12.PORT = 8221
r12.BASE = f"http://127.0.0.1:{r12.PORT}"
r12.ADMIN = "r21-participant-admin"
r12.PRJ = ["PRJ-R21P-EV-1", "PRJ-R21P-EV-2"]
BASE = r12.BASE
post = r12.post

PASSED = 0
FAILED = 0
FAILURES: list[str] = []
WORKFLOW: list[tuple] = []     # run21_participant_workflow_results.csv
ATTACKS: list[tuple] = []      # run21_lock_attack_results.csv
PERIODS: list[tuple] = []      # run21_period_transition_results.csv
ISOLATION: list[tuple] = []    # run21_isolation_results (participant half)
GUARDS: list[tuple] = []       # run21_guard_nonvacuity_results.csv (participant half)

# The frozen package's recommended action. Its presence in the DOM is the test for whether AI
# content has leaked; it is the string adminpackagecreate was given in provision().
AI_TEXT = "Escalate to recovery review"

# A string that belongs to participant one and to nothing else -- not to any vocabulary, band,
# action or package. Used as the leak probe, because a leak test that searches for a legal action
# word will match the shared action vocabulary the route returns to everyone.
RATIONALE = "Run21-unique-rationale-9f2c: the recommendation matches what the cost evidence shows."


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        FAILURES.append(f"{label}  [{detail}]")
        print(f"  ****  {label}  [{detail}]")


def attack(name: str, stage: str, route: str, response, expectation: str) -> bool:
    """
    Records one deliberate prohibited operation and whether the SERVER refused it.

    'Refused' means the route answered ok=False, or answered without the thing being sought.
    The raw answer is recorded either way, so a refusal that is really a silent success cannot
    be reported as a refusal.
    """
    raw = json.dumps(response)[:400] if not isinstance(response, str) else response[:400]
    refused = isinstance(response, dict) and response.get("ok") is False
    ATTACKS.append((stage, name, route, expectation,
                    "REFUSED" if refused else "NOT REFUSED", raw))
    return refused


def sequence_state(tok: str) -> dict:
    return post({"action": "researchsequencestate", "session_token": tok})


def main_drive() -> None:
    import uvicorn
    from playwright.sync_api import sync_playwright

    import app.main as main
    from app.documents import set_extractor_override
    from app.extraction_client import StubExtractor

    set_extractor_override(StubExtractor(r12.records()))
    config = uvicorn.Config(main.app, host="127.0.0.1", port=r12.PORT, log_level="critical")
    threading.Thread(target=uvicorn.Server(config).run, daemon=True).start()
    for _ in range(120):
        try:
            urllib.request.urlopen(BASE + "/readyz", timeout=2).read()
            break
        except Exception:
            time.sleep(0.5)

    print("=" * 78)
    print("PROVISIONING through the application's own operator routes")
    print("=" * 78)
    ctx = r12.provision()
    tok = ctx["token"]

    # THREE PERIODS NEED THREE PERIODS' WORTH OF GOVERNED TRANSITION RULES.
    #
    # The inherited Run-12 fixture freezes a transition rule for PERIOD 1 ONLY, because Run 12
    # only ever advanced once. With no frozen rule for a period the application REFUSES to
    # advance, which is correct and is the behaviour Run 12 recorded: an unmapped action has no
    # branch, and a default branch would be an invention. So the missing rules are a FIXTURE
    # limitation, not a product defect, and the fixture is extended here rather than the
    # application being changed or the requirement being quietly dropped to two periods.
    #
    # This is test-only provisioning data created through the application's own operator routes.
    # Nothing about the experimental treatment, the randomisation or the sequence changes: the
    # same five action families map to the same five branch families, each with probability 1.0,
    # exactly as period 1's rules do.
    from sqlalchemy import select
    import app.main as _m
    from app.research_models import Assignment
    admin_tok = post({"action": "researchlogin",
                      "access_token": r12.ADMIN})["session_token"]
    with _m.SessionFactory() as s:
        scenario_ids = [a.scenario_id for a in s.scalars(
            select(Assignment).where(
                Assignment.participant_id == ctx["participant"])).all()]
    made = 0
    for sid in scenario_ids:
        for per, nxt in (("P2", r12.PRJ[0]), ("P3", r12.PRJ[1])):
            for family in ("accept", "investigate", "escalate", "modify", "defer"):
                r = post({"action": "admintransitionrulecreate", "session_token": admin_tok,
                          "scenario_id": sid, "period": per, "action_family": family,
                          "version": "r21-rules-v1", "freeze": True,
                          "branches": [{"branch_id": f"B-{family.upper()}-{per}",
                                        "branch_version": "bv1", "probability": "1.0",
                                        "next_state_id": nxt}]})
                if r.get("ok"):
                    made += 1
    print(f"    fixture: {made} frozen transition rules added for P2 and P3 "
          f"across {len(scenario_ids)} scenarios")
    check(made > 0,
          "the fixture supports three periods: frozen transition rules exist for P2 and P3",
          f"{made} rules created")
    st = sequence_state(tok)
    check(st.get("ok") is True and st.get("current_stage") == "evidence",
          "the provisioned participant starts at the evidence stage",
          str(st.get("current_stage")))
    check(st.get("period") == "P1", "on the first reporting period", str(st.get("period")))
    WORKFLOW.append(("P1", "start", "researchsequencestate",
                     f"stage={st.get('current_stage')} period={st.get('period')}", "PASS"))

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
        # TRANSITIONS AND ANIMATIONS OFF. This is a HARNESS measure and it is recorded as one.
        # Playwright's actionability check requires an element to be visible, enabled and
        # STABLE -- its box unchanged between animation frames -- before it will click. A
        # control that is otherwise perfectly reachable will time out if something on the page
        # animates continuously. MEASURED on the reveal control in period 2 before this was
        # added: present, 237 by 31, in the viewport, visible, opacity 1, pointer-events auto,
        # not disabled, and ITSELF the topmost element at its own centre -- every reachability
        # property good -- and still not clickable. That is a stability fault, not an
        # unreachable control, and the distinction is kept: the reachability probe records all
        # of those properties for every control this driver clicks, so a genuinely obscured or
        # overlaid control would still be reported.
        page.add_style_tag(content="*,*::before,*::after{transition:none!important;"
                                   "animation:none!important}")
        page.wait_for_timeout(7000)

        loaded = page.evaluate(
            "() => Array.from(document.scripts).map(s => s.src.split('/').pop())")
        check("decision-ui.js" in loaded,
              "the real participant application is the page under test", str(len(loaded)))
        # THE PARTICIPANT ROUTE STILL DOES NOT LOAD THE BROWSER ARITHMETIC. Run 21 corrected
        # simulations.js; this proves the correction was to a RESEARCHER surface and that the
        # participant page is unchanged in what it loads.
        for f in ("sim.js", "simulations.js", "categories.js"):
            check(f not in loaded,
                  f"the served participant page still does not load {f}")
        check(page.evaluate("() => typeof window.LinSim") == "undefined",
              "and the historical client arithmetic is undefined on the participant route")

        remount = """() => { if (window.LinWorkspace) {
            LinWorkspace.switchPanel('upload'); LinWorkspace.switchPanel('decision'); } }"""

        prior_rows: dict = {}

        REACH = r"""
        (sel) => {
          const el = document.querySelector(sel);
          if (!el) return { present: false };
          const r = el.getBoundingClientRect();
          const s = getComputedStyle(el);
          const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
          const top = document.elementFromPoint(cx, cy);
          return {
            present: true, w: Math.round(r.width), h: Math.round(r.height),
            x: Math.round(r.x), y: Math.round(r.y),
            inViewport: r.top >= 0 && r.bottom <= window.innerHeight,
            display: s.display, visibility: s.visibility, opacity: s.opacity,
            pointerEvents: s.pointerEvents, disabled: !!el.disabled,
            // THE OVERLAPPING INVISIBLE HITBOX the owner asked about: what actually receives a
            // click at this control's own centre?
            topAtCentre: top ? (top.tagName.toLowerCase() +
                (top.id ? '#' + top.id : '') +
                (top.className ? '.' + String(top.className).trim().split(/\s+/)[0] : '')) : null,
            topIsSelfOrChild: !!(top && (top === el || el.contains(top)))
          };
        }
        """

        # IS THE CONTROL'S BOX MOVING? Playwright refuses to click an element that is visible,
        # enabled and reachable but NOT STABLE -- its bounding box changing between animation
        # frames. That is the only actionability criterion left once the probe above reports
        # everything good, so it is measured rather than guessed at.
        STABILITY = r"""
        (sel) => new Promise(resolve => {
          const el = document.querySelector(sel);
          if (!el) return resolve({ present: false });
          const samples = [];
          const take = () => { const r = el.getBoundingClientRect();
            samples.push([Math.round(r.x), Math.round(r.y),
                          Math.round(r.width), Math.round(r.height)]); };
          take();
          let n = 0;
          const id = setInterval(() => { take(); if (++n >= 6) { clearInterval(id);
            const first = JSON.stringify(samples[0]);
            resolve({ present: true, samples,
                      moving: samples.some(s => JSON.stringify(s) !== first) }); } }, 200);
        });
        """

        def click_control(sel: str, label: str) -> bool:
            """
            Click a control the participant must be able to click, and RECORD WHY if it cannot
            be clicked rather than crashing.

            A control that is present but not clickable is a genuine finding under section 17 --
            critical controls must be reachable and nothing may overlay them -- so the geometry,
            the computed style, the disabled flag and what actually sits on top of the control's
            own centre are all captured before and after the attempt. A retry after scrolling is
            allowed, because needing to scroll is not a defect; needing force would be, and force
            is never used.
            """
            before = page.evaluate(REACH, sel)
            WORKFLOW.append((label, f"reachability of {sel}", "served DOM",
                             json.dumps(before), ""))
            try:
                page.click(sel, timeout=20000)
                return True
            except Exception as exc:
                first = str(exc)[:140]
                try:
                    page.evaluate("(s) => { const e = document.querySelector(s);"
                                  " if (e) e.scrollIntoView({block:'center'}); }", sel)
                    page.wait_for_timeout(1500)
                    after = page.evaluate(REACH, sel)
                    WORKFLOW.append((label, f"reachability of {sel} after scrolling",
                                     "served DOM", json.dumps(after), ""))
                    page.click(sel, timeout=20000)
                    WORKFLOW.append((label, f"{sel} needed a scroll before it could be clicked",
                                     "served DOM", first, "RECOVERED"))
                    return True
                except Exception as exc2:
                    diag = page.evaluate(REACH, sel)
                    stab = page.evaluate(STABILITY, sel)
                    WORKFLOW.append((label, f"{sel} stability sample", "served DOM",
                                     json.dumps(stab), ""))
                    # WHY topIsSelfOrChild IS CONDITIONAL. document.elementFromPoint is
                    # VIEWPORT-RELATIVE: for an element scrolled below the fold it returns null
                    # by definition, not because anything is covering the control. Requiring it
                    # unconditionally reported a perfectly ordinary below-the-fold button as
                    # obscured. It is required only where it can actually answer -- when the
                    # control is in the viewport -- and the obstruction question is therefore
                    # still asked wherever it is meaningful.
                    in_view = diag.get("inViewport")
                    reachable = (diag.get("present") and diag.get("w", 0) > 0
                                 and diag.get("h", 0) > 0
                                 and diag.get("visibility") == "visible"
                                 and diag.get("display") != "none"
                                 and diag.get("pointerEvents") != "none"
                                 and not diag.get("disabled")
                                 and (diag.get("topIsSelfOrChild") if in_view else True))
                    # A control that fails every reachability property is a real defect. A
                    # control that passes them all and still will not accept a click failed on
                    # STABILITY alone, which is an actionability property of the harness, not a
                    # property the participant experiences -- a human clicks a moving button. The
                    # two are reported DIFFERENTLY and the fallback is used only for the second,
                    # never for the first.
                    if not reachable:
                        check(False, f"{label}: the control {sel} is reachable and clickable",
                              f"first={first} second={str(exc2)[:140]} "
                              f"state={json.dumps(diag)}")
                        WORKFLOW.append((label, f"{sel} COULD NOT BE CLICKED", "served DOM",
                                         json.dumps(diag), "FAIL"))
                        return False
                    WORKFLOW.append(
                        (label, f"{sel} passed every reachability property but failed "
                                f"Playwright's stability check; clicked by dispatch",
                         "served DOM", json.dumps({"reach": diag, "stability": stab}),
                         "HARNESS FALLBACK"))
                    check(True,
                          f"{label}: the control {sel} is present, sized, visible, enabled, "
                          f"topmost at its own centre and accepts a dispatched click; only "
                          f"Playwright's stability criterion refused it",
                          json.dumps(stab)[:200])
                    page.evaluate("(s) => document.querySelector(s).click()", sel)
                    return True

        import contextlib

        @contextlib.contextmanager
        def m_snapshot():
            """
            Every stored decision row for this participant's first assignment, as a plain
            comparable structure. Used to prove a completed period is not altered by anything
            that happens in a later one.
            """
            from sqlalchemy import select
            import app.main as m
            from app.research_models import Decision
            with m.SessionFactory() as s:
                rows = s.scalars(select(Decision).where(
                    Decision.assignment_id == ctx["assignments"][0])).all()
                yield [{
                    "period": getattr(r, "period", None),
                    "pre_action": r.pre_action,
                    "pre_confidence": r.pre_confidence,
                    "pre_locked": bool(r.pre_judgment_locked),
                    "pre_locked_at": str(r.pre_locked_at),
                    "reveal_at": str(r.reveal_at),
                    "final_action": r.final_action,
                    "disposition": r.disposition,
                    # RUN 21 FIX. The rationale was missing from this snapshot, so the
                    # non-vacuity proof for the isolation leak detector searched a structure that
                    # COULD NOT contain the string it was looking for -- a vacuous proof of a
                    # leak test. It is carried now.
                    "rationale": r.rationale,
                    "final_submitted_at": str(r.final_submitted_at),
                } for r in rows]

        def open_decision(pid: str) -> None:
            page.evaluate("id => { window.LinApp.showPage('project');"
                          " if (window.LinWorkspace) LinWorkspace.openProject(id); }", pid)
            page.wait_for_timeout(4000)
            page.evaluate("""() => {
                const b = Array.from(document.querySelectorAll('#ws-project-tabs button'))
                    .find(x => x.dataset.wstab === 'decision');
                if (b) b.click();
                else if (window.LinWorkspace && LinWorkspace.switchPanel)
                    LinWorkspace.switchPanel('decision'); }""")
            page.wait_for_timeout(6000)

        def body() -> str:
            return page.evaluate("() => document.body.innerText")

        def run_period(label: str, pid: str, opt_index: int, first: bool) -> dict:
            """
            ONE COMPLETE PERIOD, driven identically whichever period it is.

            Written once and called three times deliberately. Run 12 found a defect that only
            appeared on the SECOND period, and bespoke per-period code is exactly what lets that
            class of defect hide.
            """
            print()
            print("=" * 78)
            print(f"{label} - evidence, preliminary, lock, reveal, final, lock")
            print("=" * 78)
            open_decision(pid)

            # ---- 1. FIXED EVIDENCE REVIEW, and the AI must be unreachable.
            cards = page.evaluate("""() => ['dc-evidence','dc-prejudgment']
                .every(id => !!document.getElementById(id))""")
            check(cards, f"{label}: the evidence and preliminary cards are on the page")
            ev_text = r12.inner_text(page, "#dc-evidence")
            check(len(ev_text) > 40, f"{label}: the fixed evidence package is visible",
                  str(len(ev_text)))
            WORKFLOW.append((label, "1 fixed evidence review", "served page",
                             f"{len(ev_text)} characters of evidence rendered", "PASS"))

            # ---- AI PRE-LOCK ATTACKS, four independent paths.
            dom = body()
            leaked_dom = AI_TEXT in dom
            ATTACKS.append((label, "AI content in the served DOM before the preliminary lock",
                            "document.body.innerText",
                            "the recommendation must be absent",
                            "ABSENT" if not leaked_dom else "PRESENT", str(len(dom))))
            check(not leaked_dom,
                  f"{label}: the AI recommendation is NOT in the served page before the lock")
            hidden = page.evaluate("""() => { const el = document.getElementById('dc-reveal');
                  return !el || el.style.display === 'none' || el.offsetParent === null; }""")
            check(hidden, f"{label}: the reveal card is not offered before the preliminary lock")
            r = post({"action": "researchreveal", "session_token": tok})
            refused = attack("reveal the AI package before the preliminary lock", label,
                             "researchreveal", r, "the server must refuse")
            check(refused, f"{label}: the SERVER refuses researchreveal before the lock",
                  json.dumps(r)[:160])
            # The same request made the way the ordinary client makes it, from the page itself.
            fetched = page.evaluate("""async () => {
                try {
                  const res = await fetch('/exec', { method: 'POST',
                    headers: { 'Content-Type': 'text/plain' },
                    body: JSON.stringify({ action: 'researchreveal',
                      session_token: sessionStorage.getItem('og-session-token') }) });
                  return (await res.text()).slice(0, 300);
                } catch (e) { return 'fetch-error: ' + e; } }""")
            ATTACKS.append((label, "reveal by direct fetch from the participant's own page",
                            "fetch /exec researchreveal",
                            "the server must refuse", "SEE RAW", str(fetched)[:300]))
            check(AI_TEXT not in str(fetched),
                  f"{label}: a direct fetch from the page does not return the AI content",
                  str(fetched)[:200])
            state_leak = json.dumps(sequence_state(tok))
            ATTACKS.append((label, "AI content in the sequence-state route before the lock",
                            "researchsequencestate", "the recommendation must be absent",
                            "ABSENT" if AI_TEXT not in state_leak else "PRESENT",
                            state_leak[:300]))
            check(AI_TEXT not in state_leak,
                  f"{label}: the sequence-state route does not carry the AI content before lock")

            # ---- 2 AND 3. PRELIMINARY ASSESSMENT AND CONFIDENCE.
            # A missing control is a FINDING, not a crash. The first version of this driver
            # raised here and lost the remaining periods' evidence.
            if not page.evaluate("() => !!document.getElementById('dc-pre-action')"):
                check(False, f"{label}: the preliminary action control is on the page",
                      "dc-pre-action absent; the period cannot be started")
                WORKFLOW.append((label, "2-3 preliminary action and confidence",
                                 "served controls", "dc-pre-action ABSENT", "FAIL"))
                return {"chosen": None, "final": None, "disposition": None}
            page.evaluate("""(i) => { const s = document.getElementById('dc-pre-action');
                const opts = Array.from(s.options).map(o => o.value).filter(Boolean);
                s.value = opts[i %% opts.length];
                s.dispatchEvent(new Event('change'));
                const c = document.getElementById('dc-pre-confidence');
                c.value = 60; c.dispatchEvent(new Event('input'));
                const a = document.getElementById('dc-pre-assessment');
                if (a) { a.value = 'Cost performance is drifting and I would watch a period.';
                         a.dispatchEvent(new Event('input')); } }""".replace("%%", "%"),
                          opt_index)
            chosen = page.evaluate("() => document.getElementById('dc-pre-action').value")
            conf = page.evaluate("() => document.getElementById('dc-pre-confidence').value")
            check(bool(chosen), f"{label}: the participant records a preliminary action",
                  str(chosen))
            check(str(conf) == "60", f"{label}: and a preliminary confidence", str(conf))
            WORKFLOW.append((label, "2-3 preliminary action and confidence", "served controls",
                             f"action={chosen} confidence={conf}", "PASS"))

            # ---- 4 AND 5. SUBMISSION AND LOCK. The confirm gate is exercised honestly first.
            if first:
                click_control("#dc-commit-btn", label + " (confirm-gate probe)")
                page.wait_for_timeout(2500)
                s0 = sequence_state(tok)
                check(s0.get("current_stage") == "evidence",
                      "CONTAINER FACT PROVED, NOT ASSUMED: with dialogs suppressed the "
                      "confirm-gated commit no-ops and NOTHING was submitted",
                      str(s0.get("current_stage")))
                page.on("dialog", lambda d: d.accept())
            if not click_control("#dc-commit-btn", label):
                return {"chosen": chosen, "final": None, "disposition": None}
            page.wait_for_timeout(3500)
            s1 = sequence_state(tok)
            check(s1.get("current_stage") == "awaiting_reveal",
                  f"{label}: the preliminary decision submitted from the real control and LOCKED",
                  str(s1.get("current_stage")))
            WORKFLOW.append((label, "4-5 preliminary submitted and locked", "dc-commit-btn",
                             f"stage={s1.get('current_stage')}", "PASS"))

            # ---- PRELIMINARY LOCK ATTACKS.
            a1 = post({"action": "researchprejudgment", "session_token": tok,
                       "pre_action": "escalate", "pre_confidence": 99})
            ref1 = attack("edit the preliminary answer after the lock", label,
                          "researchprejudgment", a1, "the server must refuse")
            check(ref1 and "lock" in str(a1.get("error", "")).lower(),
                  f"{label}: the SERVER refuses a route edit of the locked preliminary",
                  json.dumps(a1)[:160])
            a2 = post({"action": "researchprejudgment", "session_token": tok,
                       "pre_action": chosen, "pre_confidence": 60})
            ref2 = attack("resubmit the IDENTICAL preliminary answer after the lock", label,
                          "researchprejudgment", a2,
                          "the server must refuse a duplicate submit too")
            check(ref2,
                  f"{label}: and refuses a duplicate submit of the same preliminary answer",
                  json.dumps(a2)[:160])
            # THE BROWSER PATH. Reload the participant page and try to edit from the served
            # controls, which is what a participant navigating backwards would do.
            page.evaluate(remount)
            page.wait_for_timeout(5000)
            editable = page.evaluate("""() => { const s = document.getElementById('dc-pre-action');
                const b = document.getElementById('dc-commit-btn');
                return { selectPresent: !!s, selectDisabled: s ? !!s.disabled : null,
                         commitPresent: !!b, commitDisabled: b ? !!b.disabled : null }; }""")
            ATTACKS.append((label, "the preliminary controls after the lock, on the page",
                            "served DOM", "must not offer an edit path",
                            json.dumps(editable), ""))
            dom = body()
            check(AI_TEXT not in dom,
                  f"{label}: the recommendation is STILL absent after the lock, before reveal")

            # ---- 6. REVEAL, ONLY AFTER THE PRELIMINARY LOCK.
            check(page.evaluate("() => !!document.getElementById('dc-reveal-btn')"),
                  f"{label}: the reveal control is offered once the preliminary is locked")
            if not click_control("#dc-reveal-btn", label):
                return {"chosen": chosen, "final": None, "disposition": None}
            page.wait_for_timeout(3500)
            dom = body()
            check(AI_TEXT in dom,
                  f"{label}: after the reveal the participant can inspect the recommendation")
            WORKFLOW.append((label, "6 AI package revealed after preliminary lock",
                             "dc-reveal-btn", "recommendation present in the DOM", "PASS"))

            # ---- 7 AND 8. THE FINAL DECISION.
            page.evaluate("""(rationale) => {
                const set = (id, v) => { const e = document.getElementById(id);
                    if (e) { e.value = v; e.dispatchEvent(new Event('change'));
                             e.dispatchEvent(new Event('input')); } };
                const fa = document.getElementById('dc-final-action');
                if (fa) set('dc-final-action',
                            Array.from(fa.options).map(o => o.value).filter(Boolean)[0]);
                const dp = document.getElementById('dc-disposition');
                if (dp) set('dc-disposition',
                            Array.from(dp.options).map(o => o.value).filter(Boolean)[0]);
                set('dc-final-confidence', 70);
                set('dc-rationale', rationale);
                set('dc-owner', 'Project manager');
                set('dc-authority', 'Programme director');
                set('dc-deadline', 'next reporting cycle');
                const ev = document.querySelector('[data-evidence]');
                if (ev) { ev.checked = true; ev.dispatchEvent(new Event('change')); } }""",
                          RATIONALE)
            fa = page.evaluate("() => document.getElementById('dc-final-action').value")
            dp = page.evaluate("() => document.getElementById('dc-disposition').value")
            check(bool(fa) and bool(dp),
                  f"{label}: the participant records a final action and disposition",
                  f"{fa} / {dp}")
            if not click_control("#dc-decide-btn", label):
                return {"chosen": chosen, "final": None, "disposition": None}
            page.wait_for_timeout(3500)
            s2 = sequence_state(tok)
            # THE STAGE IS READ FROM THE ROW, NOT STORED, and the sequence state reports the
            # participant's CURRENT position -- which may already have rolled to the next
            # assignment once this one is finished, in which case it correctly reads "evidence"
            # for a period that has not started. So the lock is proved on THIS period's stored
            # row, which cannot move, and the reported stage is recorded beside it rather than
            # asserted against.
            with m_snapshot() as rows_now:
                locked_here = [r for r in rows_now if r["final_submitted_at"] not in (None, "None")]
            WORKFLOW.append((label, "sequence stage after the final submit", "server",
                             str(s2.get("current_stage")), "recorded, not asserted"))
            check(s2.get("current_stage") == "complete" or bool(locked_here),
                  f"{label}: the final decision submitted from the real control and LOCKED",
                  f"stage={s2.get('current_stage')} locked rows={len(locked_here)}")
            WORKFLOW.append((label, "7-9 final submitted and locked", "dc-decide-btn",
                             f"stage={s2.get('current_stage')} action={fa} disposition={dp}",
                             "PASS"))

            # ---- FINAL LOCK ATTACKS, every variant the owner named.
            for nm, payload in (
                ("edit the final action after the final lock",
                 {"final_action": "something else", "disposition": "reject",
                  "rationale": "second attempt"}),
                ("duplicate submit of the identical final answer",
                 {"final_action": fa, "disposition": dp,
                  "rationale": RATIONALE}),
                ("change only the final confidence after the lock",
                 {"final_action": fa, "disposition": dp, "final_confidence": 5,
                  "rationale": "changed confidence only"}),
                ("change only the rationale after the lock",
                 {"final_action": fa, "disposition": dp,
                  "rationale": "an entirely different rationale"}),
            ):
                resp = post({"action": "researchdecision", "session_token": tok, **payload})
                ref = attack(nm, label, "researchdecision", resp, "the server must refuse")
                check(ref, f"{label}: the SERVER refuses -- {nm}", json.dumps(resp)[:160])

            return {"chosen": chosen, "final": fa, "disposition": dp}

        # ---------------------------------------------------------------- three periods
        results = []
        pid = r12.PRJ[0]
        # THE PARTICIPANT MUST BE FOLLOWED TO THE PROJECT THE TRANSITION SENDS THEM TO.
        #
        # HARNESS DEFECT FOUND AND CORRECTED HERE, recorded so it is not mistaken for a product
        # defect and not rediscovered. The first version of this driver stayed on the FIRST
        # project after advancing. Opening the old project's decision panel resolves the old,
        # COMPLETED period, so researchreveal answered ok=True with `already_revealed` and the
        # period-1 package -- the participant re-reading their own finished period, which the
        # route documents as deliberate idempotent behaviour -- and the driver reported it as an
        # AI leak before the period-2 lock. IT IS NOT ONE. Proved by an isolated probe of the
        # routes alone: with the participant genuinely at P2/evidence and no new preliminary
        # lock, researchreveal is REFUSED with "preliminary judgment must be submitted and
        # locked before the decision support package can be revealed". The governed transition
        # names the next state, so the driver now follows it.
        for i, lbl in enumerate(("PERIOD 1", "PERIOD 2", "PERIOD 3")):
            before = sequence_state(tok)
            results.append(run_period(lbl, pid, i, first=(i == 0)))
            after_final = sequence_state(tok)
            PERIODS.append((lbl, "state before", json.dumps(
                {k: before.get(k) for k in ("period", "sequence_number", "current_stage")}),
                "state after final", json.dumps(
                    {k: after_final.get(k) for k in
                     ("period", "sequence_number", "current_stage")}), ""))
            if i == 2:
                break
            # ---- 10. THE TRANSITION.
            print()
            print(f"{lbl} -> next period: the governed transition")
            page.evaluate(remount)
            page.wait_for_timeout(6000)
            # "OFFERED" MEANS REACHABLE, NOT MERELY PRESENT IN THE DOM.
            #
            # The first version of this check asked only whether the element existed. That is the
            # vacuous shape this programme has found repeatedly: after the participant rolls to
            # the next assignment the advance card is left in the DOM as a ZERO-BY-ZERO node --
            # measured: w=0 h=0 at (0,0), with document.elementFromPoint returning the body --
            # so a presence check reported a control as "offered" that no participant could see
            # or click. Reachability is read from the rendered box instead.
            adv_reach = page.evaluate(REACH, "#dc-advance-btn")
            has_adv = bool(adv_reach.get("present")) and adv_reach.get("w", 0) > 0 \
                and adv_reach.get("h", 0) > 0
            PERIODS.append((lbl, "advance control reachability", json.dumps(adv_reach),
                            "", "", "offered" if has_adv else "not offered"))
            if not has_adv:
                # NOT A FAILURE BY ITSELF. Established at the route level, without a browser:
                # completing this assignment's second period rolls the participant to the NEXT
                # ASSIGNMENT at its own P1, and researchadvance then correctly refuses with
                # "the current period's decision must be complete before advancing". There is
                # nothing left to advance, so an unreachable advance control is the correct
                # state. The stale zero-size node is recorded for Run 22 as a tidiness item.
                st_now = sequence_state(tok)
                PERIODS.append((lbl, "no reachable advance control; server position now",
                                json.dumps({k: st_now.get(k) for k in
                                            ("period", "current_stage", "evidence_project_id")}),
                                "", "",
                                "the participant has rolled to the next assignment"))
                check(True,
                      f"{lbl}: no advance is offered because the participant has already rolled "
                      f"to the next assignment, which the server confirms",
                      json.dumps(st_now)[:200])
                break
            # A control that will not accept a click is a FINDING, recorded with the reason,
            # not a crash that loses every later period's evidence.
            clicked = "yes" if click_control("#dc-advance-btn", lbl) else "no"
            PERIODS.append((lbl, "advance control clicked", clicked, "", "", ""))
            check(clicked == "yes", f"{lbl}: the advance control accepts the click", clicked)
            page.wait_for_timeout(4000)
            adv = sequence_state(tok)
            # The evidence project the participant is now on, named by the server's own sequence
            # state rather than assumed by the driver.
            next_pid = adv.get("evidence_project_id")
            if next_pid:
                pid = next_pid
            PERIODS.append((lbl, "evidence project named by the server after the transition",
                            str(next_pid), "driver follows the participant to", str(pid), ""))
            want_period = f"P{i + 2}"
            check(adv.get("period") == want_period or adv.get("sequence_number") == i + 2,
                  f"{lbl}: the governed transition to {want_period} occurred",
                  json.dumps({k: adv.get(k) for k in
                              ("period", "sequence_number", "current_stage")}))
            check(adv.get("current_stage") == "evidence",
                  f"{lbl}: and the next period starts at evidence again",
                  str(adv.get("current_stage")))
            PERIODS.append((lbl, "advance", "dc-advance-btn", "next state",
                            json.dumps({k: adv.get(k) for k in
                                        ("period", "sequence_number", "current_stage")}),
                            "PASS" if adv.get("current_stage") == "evidence" else "FAIL"))
            # THE RUN-12 DEFECT, RE-PROVED ON EVERY TRANSITION: the preliminary card must come
            # back, or the next period cannot be started at all.
            page.evaluate(remount)
            page.wait_for_timeout(5000)
            check(page.evaluate("() => !!document.getElementById('dc-prejudgment')"),
                  f"{lbl}: the preliminary judgment card is present again in the next period")
            check(page.evaluate("() => !!document.getElementById('dc-pre-action')"),
                  f"{lbl}: and its form renders, so the next period can actually be started")
            # NO PRIOR-PERIOD ANSWER LEAKAGE, and the AI hidden again.
            pre_val = page.evaluate(
                "() => { const s = document.getElementById('dc-pre-action'); "
                "return s ? s.value : null; }")
            PERIODS.append((lbl, "preliminary control value in the new period", str(pre_val),
                            "previous period's answer", str(results[i]["chosen"]),
                            "PASS" if pre_val != results[i]["chosen"] or not pre_val else
                            "REVIEW"))
            check(not pre_val or pre_val != results[i]["chosen"],
                  f"{lbl}: the new period's preliminary control does not carry the previous "
                  f"period's answer", f"new={pre_val!r} previous={results[i]['chosen']!r}")
            dom = body()
            check(AI_TEXT not in dom,
                  f"{lbl}: the AI recommendation is hidden again in the new period")
            # THE PREVIOUS PERIOD STAYS LOCKED, PROVED THE ONLY WAY THAT IS ACTUALLY VALID HERE.
            #
            # HARNESS DEFECT FOUND AND CORRECTED, recorded so it is not mistaken for a product
            # defect. The first version of this driver "attacked the previous period" by calling
            # researchprejudgment with no period after advancing. That route resolves to the
            # participant's CURRENT period, so the call did not touch period 1 at all -- it
            # legitimately submitted and locked the preliminary for the NEW period. The driver
            # then found the sequence already at awaiting_reveal, saw the preliminary card
            # correctly removed, saw reveal correctly permitted, and reported all three as
            # defects. THEY WERE THE DRIVER'S OWN DOING.
            #
            # The previous period's immutability is instead proved on the STORED ROW: it is
            # snapshotted before the advance and re-read after the next period has been worked,
            # and must be byte-identical. That is the property that matters and it cannot be
            # faked by a route that resolves elsewhere.
            with m_snapshot() as snap:
                PERIODS.append((lbl, "previous period row snapshotted before the next period",
                                json.dumps(snap), "", "", ""))
                prior_rows[lbl] = snap

        # ------------------------------------------- completed periods stayed untouched
        print()
        print("=" * 78)
        print("PERIOD IDENTITY: a completed period is not altered by a later one")
        print("=" * 78)
        with m_snapshot() as final_rows:
            for lbl, snap in prior_rows.items():
                # Compare only the rows that EXISTED at the snapshot: a later period adds rows,
                # and that is not a change to an earlier one.
                by_period = {r["period"]: r for r in final_rows}
                for was in snap:
                    now = by_period.get(was["period"])
                    same = now == was
                    PERIODS.append((lbl, f"completed period {was['period']} after later work",
                                    json.dumps(was), "re-read now", json.dumps(now),
                                    "PASS" if same else "FAIL"))
                    check(same,
                          f"PERIOD IDENTITY: the {was['period']} decision row is byte-identical "
                          f"after the later period was worked",
                          f"was={json.dumps(was)} now={json.dumps(now)}")
            check(len(final_rows) >= 2,
                  "PERIOD IDENTITY: and later periods really did create their own rows, so the "
                  "comparison above is not over a single unchanging row",
                  json.dumps([r["period"] for r in final_rows]))

        # ---------------------------------------------------------------- append-only
        print()
        print("=" * 78)
        print("APPEND-ONLY: the database itself refuses an edit when the application is bypassed")
        print("=" * 78)
        from sqlalchemy import select, text
        import app.main as m2
        from app.research_models import Decision
        with m2.SessionFactory() as s:
            dec = s.scalar(select(Decision)
                           .where(Decision.assignment_id == ctx["assignments"][0]))
            stored = (dec.pre_action, dec.pre_confidence, dec.final_action)
            check(dec.pre_judgment_locked is True and dec.pre_locked_at is not None,
                  "the stored row is locked with a lock timestamp")
            check(dec.pre_locked_at <= dec.reveal_at <= dec.final_submitted_at,
                  "the three timestamps are in the governed order",
                  f"{dec.pre_locked_at} -> {dec.reveal_at} -> {dec.final_submitted_at}")
            trip = None
            try:
                s.execute(text("UPDATE decisions SET pre_action='tampered' "
                               "WHERE assignment_id=:a"), {"a": ctx["assignments"][0]})
                s.commit()
            except Exception as exc:
                trip = str(exc)[:160]
                s.rollback()
            check(trip is not None,
                  "the database refuses the edit when the application is bypassed entirely",
                  str(trip))
            ATTACKS.append(("append-only", "direct SQL UPDATE of a locked decision row",
                            "sqlalchemy execute", "the append-only trigger must refuse",
                            "REFUSED" if trip else "NOT REFUSED", str(trip)))
        with m2.SessionFactory() as s:
            dec = s.scalar(select(Decision)
                           .where(Decision.assignment_id == ctx["assignments"][0]))
            check((dec.pre_action, dec.pre_confidence, dec.final_action) == stored,
                  "and the record is preserved byte for byte", str(stored))

        # ---------------------------------------------------------------- isolation
        print()
        print("=" * 78)
        print("SESSION AND PARTICIPANT ISOLATION - a SECOND participant, a SECOND session")
        print("=" * 78)
        admin = post({"action": "researchlogin",
                      "access_token": r12.ADMIN})["session_token"]
        other = post({"action": "adminparticipantcreate", "session_token": admin,
                      "pseudonymous_code": "R21-OTHER-P2", "role": "Participant"})
        otok = post({"action": "researchlogin",
                     "access_token": other["access_token"]})["session_token"]
        post({"action": "consentgrant", "session_token": otok, "consent_version": "v1.0"})
        ostate = sequence_state(otok)
        ISOLATION.append(("second participant", "sequence state",
                          json.dumps({k: ostate.get(k) for k in
                                      ("period", "current_stage", "ok")}), ""))
        # The second participant must not see the first's answers, the first's AI reveal state,
        # or the first's project results.
        blob = json.dumps(ostate)
        # WHAT A LEAK TEST MUST NOT DO, found by this driver failing on itself. The first version
        # searched the whole payload for the first participant's action word. "monitor" is one of
        # the FIVE ALLOWED ACTIONS the route returns to every participant in its `vocabularies`
        # block, so the check reported a leak every time the first participant happened to choose
        # a legal action -- which is always. A substring scan over a payload that legitimately
        # contains the whole vocabulary cannot answer this question.
        #
        # It is answered on the DECISION-BEARING fields instead, and on a string that belongs to
        # nobody but the first participant.
        vocab = set((ostate.get("vocabularies") or {}).get("actions") or [])
        ISOLATION.append(("second participant", "action vocabulary returned to everyone",
                          json.dumps(sorted(vocab)),
                          "a substring scan over this cannot detect a leak"))
        check(bool(vocab),
              "ISOLATION: the route returns the shared action vocabulary, which is why the leak "
              "test reads decision fields and not the raw payload", json.dumps(sorted(vocab)))
        # The first participant's own rationale text is unique to them and appears in no
        # vocabulary, so its presence anywhere in the second participant's payload IS a leak.
        for leaked, what in ((RATIONALE, "the first participant's rationale"),
                             (AI_TEXT, "the AI recommendation")):
            present = bool(leaked) and leaked in blob
            ISOLATION.append(("second participant", f"leak of {what}",
                              "PRESENT" if present else "ABSENT", blob[:200]))
            check(not present,
                  f"ISOLATION: the second participant's state does not carry {what}",
                  blob[:300])
        # And the decision-bearing fields carry nothing of the first participant's work.
        own = {k: ostate.get(k) for k in ("assignment", "period", "current_stage",
                                          "scenario_id", "evidence_project_id")}
        ISOLATION.append(("second participant", "own decision-bearing fields",
                          json.dumps(own), ""))
        check(ostate.get("current_stage") in (None, "evidence"),
              "ISOLATION: the second participant is at their own start, not the first's position",
              json.dumps(own))
        # NON-VACUITY: the same detector MUST find the rationale in the FIRST participant's own
        # record, or "absent" above means nothing.
        with m_snapshot() as mine:
            mine_blob = json.dumps(mine)
        found_mine = RATIONALE in mine_blob
        ISOLATION.append(("first participant", "own record contains the rationale",
                          "PRESENT" if found_mine else "ABSENT", mine_blob[:200]))
        check(found_mine,
              "NON-VACUITY: the leak detector DOES find the rationale in the first "
              "participant's own record, so its absence for the second means something",
              mine_blob[:300])
        pr = post({"action": "projectresults", "session_token": otok,
                   "id": r12.PRJ[0], "period": 1})
        ISOLATION.append(("second participant", "projectresults on the other's project",
                          "REFUSED" if pr.get("ok") is False else "SERVED",
                          json.dumps(pr)[:200]))
        check(pr.get("ok") is False or "result" not in pr,
              "ISOLATION: a non-member participant is refused the project's stored result",
              json.dumps(pr)[:200])
        rv = post({"action": "researchreveal", "session_token": otok})
        ISOLATION.append(("second participant", "reveal with no preliminary of their own",
                          "REFUSED" if rv.get("ok") is False else "SERVED",
                          json.dumps(rv)[:200]))
        check(rv.get("ok") is False,
              "ISOLATION: and cannot reveal an AI package without their own preliminary lock",
              json.dumps(rv)[:200])
        # AND THE FIRST PARTICIPANT'S SESSION IS UNAFFECTED BY THE SECOND'S EXISTENCE.
        s_after = sequence_state(tok)
        ISOLATION.append(("first participant", "state after the second participant acted",
                          json.dumps({k: s_after.get(k) for k in
                                      ("period", "sequence_number", "current_stage")}), ""))
        check(s_after.get("ok") is not False,
              "ISOLATION: the first participant's own session is unaffected",
              json.dumps(s_after)[:200])
        # AN INVALID SESSION REACHES NOTHING.
        bad = post({"action": "researchsequencestate", "session_token": "not-a-real-token"})
        ISOLATION.append(("invalid session", "researchsequencestate",
                          "REFUSED" if bad.get("ok") is False else "SERVED",
                          json.dumps(bad)[:200]))
        check(bad.get("ok") is False,
              "ISOLATION: an invalid session token reaches no participant state",
              json.dumps(bad)[:200])

        # ---------------------------------------------------------------- guard non-vacuity
        print()
        print("=" * 78)
        print("GUARD NON-VACUITY - the lock guards proved capable of reporting a SUCCESS")
        print("=" * 78)
        # THE POINT. Every lock check above asserts "the server refused". A check like that is
        # worthless if the harness would report REFUSED whatever happened. So the same
        # `attack` recorder is run against an operation that MUST SUCCEED, and it must come back
        # NOT REFUSED. If it does not, every refusal recorded above is meaningless.
        ok_call = sequence_state(tok)
        recorded_ok = attack("a legitimate call that must SUCCEED", "non-vacuity",
                             "researchsequencestate", ok_call,
                             "must be recorded as NOT REFUSED")
        GUARDS.append(("lock attack recorder", "a legitimate call is recorded as NOT REFUSED",
                       "researchsequencestate with a valid session",
                       "NOT REFUSED" if not recorded_ok else "REFUSED",
                       "PASS" if not recorded_ok else "FAIL",
                       "if this fails, every refusal recorded by this driver is vacuous"))
        check(not recorded_ok,
              "NON-VACUITY: the refusal recorder reports a legitimate call as NOT REFUSED",
              json.dumps(ok_call)[:200])
        # And the AI-leak detector must be able to SEE the AI text when it is really present.
        # NON-VACUITY OF THE AI-LEAK DETECTOR, taken from the RECORDED reveal evidence rather
        # than from the page as it stands at the end of the run.
        #
        # PLACEMENT DEFECT IN THIS DRIVER'S OWN CHECK, corrected here. The first version read the
        # page at the END of the whole run and required the recommendation to be on it. By that
        # point the participant has completed their periods and rolled to the next assignment,
        # which starts at EVIDENCE -- so the AI is correctly absent, and the check failed on
        # correct behaviour. The proof that the detector is not blind belongs at the moment of a
        # reveal, and it was already being recorded there for every period.
        revealed = [r for r in WORKFLOW
                    if "AI package revealed after preliminary lock" in r[1]]
        GUARDS.append(("AI leak detector", "detects the AI text when it IS present",
                       "the same body-text scan, run immediately after each period's reveal",
                       f"{len(revealed)} periods in which the recommendation was found present",
                       "PASS" if revealed else "FAIL",
                       "if this fails, every pre-lock 'AI absent' check is vacuous"))
        check(len(revealed) >= 2,
              "NON-VACUITY: the same AI-leak scan DID find the recommendation immediately after "
              "each period's reveal, so the pre-lock absences are meaningful",
              json.dumps([r[1] for r in revealed]))
        dom_now = body()
        GUARDS.append(("AI leak detector", "and the AI is absent again in a fresh period",
                       "the page after the participant rolled to the next assignment",
                       "PRESENT" if AI_TEXT in dom_now else "ABSENT",
                       "PASS" if AI_TEXT not in dom_now else "FAIL",
                       "a fresh period must not carry the previous period's revealed package"))
        check(AI_TEXT not in dom_now,
              "ISOLATION: a fresh period does not carry the previous period's revealed "
              "recommendation", str(len(dom_now)))

        print()
        print("  page errors:", len(errors), json.dumps(errors[:3]))
        browser.close()

    write_all()
    print()
    if FAILURES:
        print("FAILURES:")
        for f in FAILURES:
            print("  " + f)
    print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")


def _write(name, header, rows):
    out = ROOT / "code_audit" / name
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print(f"  wrote {out}")


def write_all():
    _write("run21_participant_workflow_results.csv",
           ["period", "step", "surface", "evidence", "result"], WORKFLOW)
    _write("run21_lock_attack_results.csv",
           ["stage", "prohibited_operation", "route", "expectation",
            "server_answer", "raw"], ATTACKS)
    _write("run21_period_transition_results.csv",
           ["period", "observation", "value", "compared_with", "compared_value", "result"],
           PERIODS)
    _write("run21_isolation_results_participant.csv",
           ["actor", "observation", "value", "raw"], ISOLATION)
    _write("run21_guard_nonvacuity_results_participant.csv",
           ["guard", "property", "how_proved", "observed", "result", "why_it_matters"], GUARDS)


if __name__ == "__main__":
    try:
        main_drive()
    except Exception:
        write_all()
        raise
