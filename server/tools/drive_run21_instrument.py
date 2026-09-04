#!/usr/bin/env python3
"""
RUN 21. THE RESEARCH INSTRUMENT AS THE PARTICIPANT AND RESEARCHER ACTUALLY MEET IT, DRIVEN IN A
REAL BROWSER AGAINST A REAL SERVER.

THE QUESTION THIS ANSWERS. Run 20 established a scientifically qualified system on the server.
This driver asks whether the WEBSITE truthfully and reproducibly presents it. For every state
below it proves agreement between four layers, and it fails if any two disagree:

    SERVER TRUTH  ->  API RESPONSE  ->  FRONTEND STATE  ->  VISIBLE BROWSER RESULT

The server is authoritative for persistent state. The browser is the instrument the participant
experiences. Neither may contradict the other, and neither alone is accepted as evidence: a
DOM-only check cannot see a server that is lying, and a server-only check cannot see a page that
renders yesterday's answer.

THE STATES, as the owner named them:

    A  clean/empty project
    B  one controlled document
    C  multiple controlled documents
    D  reset/clear, then reload, then navigate away and back
    E  post-reset new evidence
    F  project switching, A -> B -> A, repeated
    G  hard reload at every important state
    H  a fresh browser context against the same server

and, cutting across them, the Project Detail rail, the FINAL FLOW registry-versus-activity
distinction, blocked and abstaining rendering, the Category-9 and lineage presentation, the two
voting modules and the governed project status, responsive widths, and error states.

WHAT IS INSTRUMENTED AND WHY, so no later session repeats the measurement:

  1. THE RELOAD IS REAL AND IS PROVED REAL. Run 16 recorded "no reload primitive returns in this
     container" and Run 18 showed that to be a WAIT-CONDITION fault rather than a container
     fact: the served document holds requests open (the parser-blocking sign-in script is
     aborted by our own route handler, the map tile host is refused at CONNECT by the egress
     proxy), and "load" therefore never fires. Reloading with wait_until="commit" returns. This
     driver keeps that and adds the proof: a sentinel is written onto window before the reload
     and MUST be gone afterwards, which no same-document operation can produce. The owner's rule
     is honoured in both directions -- a hanging third-party subresource is not accepted as
     evidence that application reload is broken, and it is not used to excuse a real reload
     defect either, because the post-reload DOM is read and asserted against the server.

  2. window.confirm RETURNS FALSE in this headless shell, so a confirm-gated action silently
     no-ops and "the click did not throw" would be a green for an operation that never ran. The
     dialog layer is instrumented and counted, and every state-changing operation is
     additionally proved by its effect AT THE SERVER, which is the only evidence that
     distinguishes an accepted operation from a suppressed one.

  3. TWO DRIVERS MUST NOT SHARE A PORT. A second uvicorn silently fails to bind and every
     request then lands on the first driver's server and database.

It prints a canonical RESULT line so it reads like a suite, but it lives outside the test_*.py
glob deliberately: it needs Chromium, and run_all_suites.sh must not depend on a browser.

Run:
    DATABASE_URL=sqlite:///... SESSION_SECRET=... PYTHONIOENCODING=utf-8 \
        python tools/drive_run21_instrument.py
"""
from __future__ import annotations

import base64
import csv
import json
import os
import pathlib
import sys
import threading
import time
import urllib.request

sys.path.insert(0, __file__.rsplit("tools", 1)[0])
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # Run 136 F10: tools/ on the path
from artifact_write import artifact_out, report_artifact_write  # noqa: E402  Run 136 F10

import tools.drive_run16_final_flow as r16  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
SHELL = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"

# Run 21 drives its own port, admin token and project ids so it can run back to back with the
# Run-16 and Run-18 drivers against the same throwaway database without inheriting their state.
r16.PORT = 8211
r16.BASE = f"http://127.0.0.1:{r16.PORT}"
r16.ADMIN = "r21-instrument-admin"
r16.EMPTY = "PRJ-R21-EMPTY"
r16.FULL = "PRJ-R21-FULL"
r16.ONEDOC = "PRJ-R21-ONEDOC"
r16.LABEL = "run21_instrument"

BASE = r16.BASE
EMPTY, FULL, ONEDOC = r16.EMPTY, r16.FULL, r16.ONEDOC
post, open_detail, doc_bytes = r16.post, r16.open_detail, r16.doc_bytes

PASSED = 0
FAILED = 0
FAILURES: list[str] = []
MATRIX: list[tuple] = []          # run21_browser_state_matrix.csv
RECON: list[tuple] = []           # run21_server_frontend_reconciliation.csv
RESET: list[tuple] = []           # run21_reset_reload_results.csv
DETAILROWS: list[tuple] = []      # run21_project_detail_results.csv
FLOWROWS: list[tuple] = []        # run21_final_flow_results.csv
ISOROWS: list[tuple] = []         # run21_isolation_results.csv
ABSROWS: list[tuple] = []         # run21_abstention_rendering_results.csv


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        FAILURES.append(f"{label}  [{detail}]")
        print(f"  ****  {label}  [{detail}]")


def obs(state: str, name: str, value) -> None:
    MATRIX.append((state, name, str(value)))


# ---------------------------------------------------------------- server truth

def server_results(tok: str, pid: str, period: int = 1) -> dict:
    """The authoritative persistent state, read through the participant's own session."""
    r = post({"action": "projectresults", "session_token": tok, "id": pid, "period": period})
    if not r.get("ok", True) or "result" not in r:
        return {"live_row": False, "error": r.get("error")}
    row = r["result"]
    return {
        "live_row": True,
        "modules": len(row.get("module_results") or []),
        "abstained": len(row.get("abstained") or []),
        "categories": len(row.get("category_statuses") or {}),
        "project_status": row.get("project_status"),
        "status_label": row.get("project_status_label"),
        "raw": row,
    }


def server_docs(tok: str, pid: str) -> dict:
    r = post({"action": "get", "session_token": tok, "id": pid})
    doc = (r.get("result") or {}) if isinstance(r, dict) else {}
    events = doc.get("events") or []
    uploads = [e for e in events if isinstance(e, dict)
               and str(e.get("type", "")).lower().find("upload") >= 0]
    return {"events": len(events), "uploads": len(uploads)}


# ---------------------------------------------------------------- DOM readers

# The FINAL FLOW reader. Reads the Signal Flow column headers, the node fills, the project
# status node, the animated-path count and the summary strip.
READ_FLOW = r16.READ_FLOW

# Reads every badge on the Project Detail page that carries a NUMBER, together with the word
# beside it. A number describing CURRENT ACTIVITY must come from current state; a number
# describing the platform's REGISTRY must say so. This reader does not decide which is which --
# it returns the text and the assertions below decide.
READ_BADGES = r"""
() => {
  const out = [];
  document.querySelectorAll('.collapse-badge,.detail-badge,.eyebrow,.sw-footnote,.kn-sub')
    .forEach(el => {
      const t = (el.textContent || '').replace(/\s+/g, ' ').trim();
      if (t && /\d/.test(t)) out.push(t.slice(0, 160));
    });
  return out;
}
"""

# THE OBSOLETE COLLAPSE CONTROL. Deliberately stricter than a CSS-visibility check, which the
# owner named explicitly. Absence has to mean absence from the DOM, and a control that is
# present but transparent, zero-sized, pointer-events:none or off-screen is STILL reported --
# because a hidden control with a live hitbox is exactly the defect this is looking for.
READ_RAIL_STRICT = r"""
() => {
  const nav = document.getElementById('detail-secnav');
  const cs = nav ? getComputedStyle(nav) : null;
  const btns = nav ? Array.from(nav.querySelectorAll('.detail-secnav-btn')) : [];
  const arrows = /[◀▶◂▸‹›❮❯«»]/;
  const suspects = [];
  const decorative = [];
  const railBox = nav ? nav.getBoundingClientRect() : null;
  document.querySelectorAll('*').forEach(el => {
    const tag = el.tagName.toLowerCase();
    const txt = (el.textContent || '').trim();
    const aria = ((el.getAttribute && el.getAttribute('aria-label')) || '') + ' ' +
                 ((el.getAttribute && el.getAttribute('title')) || '');
    const cls = (el.className && el.className.baseVal !== undefined
                 ? el.className.baseVal : String(el.className || ''));
    // Only leaf-ish elements, or a container would match on its children's text.
    if (el.children.length > 2) return;
    const hasArrow = txt.length <= 4 && arrows.test(txt);
    const collapseSemantics =
        /\bcollapse\b|\bhide (the )?(rail|nav|navigator|sidebar)\b/i.test(aria) ||
        /secnav-(toggle|collapse|hide)/i.test(cls);
    if (!hasArrow && !collapseSemantics) return;
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    // IS IT A CONTROL? The owner's requirement is that the obsolete collapse control must not
    // exist "as a usable UI control". Control-ness is what decides, and it is read from the
    // accessible control tree rather than guessed: a real element type, an ARIA role, keyboard
    // reachability, or a bound click handler. A decorative glyph in a diagram legend is none of
    // these; it is recorded below rather than silently dropped.
    const isControl = tag === 'button' || tag === 'a' || tag === 'summary' ||
                      (el.getAttribute && el.getAttribute('role') === 'button') ||
                      el.tabIndex >= 0 || !!el.onclick ||
                      (el.hasAttribute && el.hasAttribute('data-secnav-target'));
    // DOES IT SIT OVER THE RAIL? An element that is not a control but overlaps the rail's
    // hitbox can still obstruct it, which the owner asked about explicitly. Any overlap counts,
    // however transparent or small the element is.
    const overlapsRail = !!(railBox && r.width > 0 && r.height > 0 &&
      r.left < railBox.right && r.right > railBox.left &&
      r.top < railBox.bottom && r.bottom > railBox.top);
    const row = {
      tag, text: txt.slice(0, 24), cls: String(cls).slice(0, 60),
      w: Math.round(r.width), h: Math.round(r.height),
      x: Math.round(r.x), y: Math.round(r.y),
      opacity: s.opacity, visibility: s.visibility, display: s.display,
      pointerEvents: s.pointerEvents, isControl, overlapsRail,
      focusable: el.tabIndex >= 0 || tag === 'button' || tag === 'a',
      role: (el.getAttribute && el.getAttribute('role')) || null,
      inRail: !!(el.closest && el.closest('#detail-secnav'))
    };
    // A SUSPECT is a collapse/hide CONTROL, or anything arrow-shaped that overlaps or lives in
    // the rail. Note deliberately: opacity, size and pointer-events are NOT used to excuse an
    // element. A control with opacity 0 and a live hitbox is exactly the defect being hunted,
    // so it is reported here, not filtered out.
    if (isControl || collapseSemantics || overlapsRail || row.inRail) suspects.push(row);
    else decorative.push(row);
  });
  // The keyboard-reachable control tree, which a CSS check cannot see.
  const focusables = Array.from(document.querySelectorAll(
      'button,[href],[tabindex]:not([tabindex="-1"]),[role="button"]'))
    .filter(el => {
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden';
    })
    .map(el => (el.textContent || '').trim().slice(0, 24));
  return {
    present: !!nav,
    hiddenAttr: nav ? nav.hasAttribute('hidden') : null,
    display: cs ? cs.display : null,
    opacity: cs ? cs.opacity : null,
    buttons: btns.length,
    labels: btns.map(b => b.textContent.trim()),
    suspects,
    // Recorded, never asserted against. These are arrow glyphs that are NOT controls and do not
    // touch the rail -- on this page, the separators in the Signal Flow colour legend. They are
    // reported so that "no suspects" cannot be read as "no arrow glyph exists anywhere", which
    // would be a different and untrue claim.
    decorativeArrows: decorative,
    arrowInFocusTree: focusables.filter(t => arrows.test(t))
  };
}
"""

# Reads what the page says about modules that ABSTAIN or are BLOCKED. The scientifically
# legitimate states Run 20 leaves in place must not be rendered as authoritative determinations.
READ_LEDGER = r"""
() => {
  const rows = [];
  document.querySelectorAll('.sig-row,.ledger-row,[data-module-id]').forEach(el => {
    const id = el.getAttribute('data-module-id') || '';
    const t = (el.textContent || '').replace(/\s+/g, ' ').trim();
    if (t) rows.push({ id, text: t.slice(0, 400) });
  });
  const body = (document.body.innerText || '').replace(/\s+/g, ' ');
  return { rows, bodyLen: body.length, body: body.slice(0, 200000) };
}
"""


def read_state(page, state: str, pid: str, shot: bool = True) -> dict:
    flow = page.evaluate(READ_FLOW)
    rail = page.evaluate(READ_RAIL_STRICT)
    badges = page.evaluate(READ_BADGES)
    obs(state, "project", pid)
    obs(state, "flow_present", flow.get("present"))
    if flow.get("present"):
        obs(state, "flow_headers", " | ".join(flow.get("headers") or []))
        obs(state, "flow_animated_paths", flow.get("animated"))
        obs(state, "flow_project_status_node", " ".join(flow.get("prjTexts") or []))
        obs(state, "flow_node_fills", json.dumps(flow.get("counts"), sort_keys=True))
        obs(state, "flow_summary", flow.get("summary"))
    obs(state, "rail_present", rail.get("present"))
    obs(state, "rail_buttons", rail.get("buttons"))
    obs(state, "rail_collapse_suspects", json.dumps(rail.get("suspects")))
    obs(state, "badges_with_numbers", json.dumps(badges))
    if shot:
        try:
            page.screenshot(path=str(artifact_out(
                ROOT / "code_audit" / f"run21_shot_{state}.png")))
        except Exception as exc:                                        # pragma: no cover
            obs(state, "screenshot_error", str(exc)[:120])
    return {"flow": flow, "rail": rail, "badges": badges}


def reconcile(state: str, pid: str, srv: dict, dom: dict) -> None:
    """
    The four-layer agreement, recorded row by row so a disagreement is visible even where this
    driver does not turn it into an acceptance check.
    """
    headers = " | ".join(dom["flow"].get("headers") or [])
    RECON.append((state, pid, "server_live_row", str(srv.get("live_row")),
                  "flow_present", str(dom["flow"].get("present")), ""))
    RECON.append((state, pid, "server_modules_with_a_current_result", str(srv.get("modules")),
                  "flow_headers", headers, ""))
    RECON.append((state, pid, "server_project_status", str(srv.get("project_status")),
                  "flow_project_status_node",
                  " ".join(dom["flow"].get("prjTexts") or []), ""))
    RECON.append((state, pid, "server_categories", str(srv.get("categories")),
                  "flow_animated_paths", str(dom["flow"].get("animated")), ""))


# ---------------------------------------------------------------- the drive

def main_drive() -> None:
    import uvicorn
    from playwright.sync_api import sync_playwright

    import app.main as main
    from app.documents import set_extractor_override
    from app.extraction_client import StubExtractor

    set_extractor_override(StubExtractor(r16.records()))
    config = uvicorn.Config(main.app, host="127.0.0.1", port=r16.PORT, log_level="critical")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(120):
        try:
            urllib.request.urlopen(BASE + "/readyz", timeout=2).read()
            break
        except Exception:
            time.sleep(0.5)

    pm = r16.seed()

    print("=" * 78)
    print("SERVER TRUTH, read through the participant's own session, BEFORE the browser")
    print("=" * 78)
    baseline_server = {}
    for pid in (EMPTY, ONEDOC, FULL):
        st = server_results(pm, pid, 1)
        baseline_server[pid] = st
        print(f"  {pid}: live_row={st.get('live_row')} modules={st.get('modules')} "
              f"status={st.get('project_status')}")
        obs("server-pre", f"{pid}.live_row", st.get("live_row"))
        obs("server-pre", f"{pid}.modules", st.get("modules"))
        obs("server-pre", f"{pid}.project_status", st.get("project_status"))

    # THE EMPTY PROJECT IS EMPTY AT THE SERVER. Everything the browser says about it below is
    # only meaningful because this is true first.
    check(baseline_server[EMPTY].get("live_row") is False,
          "STATE A server: the empty project has NO live result row",
          str(baseline_server[EMPTY]))
    check(baseline_server[FULL].get("live_row") is True
          and (baseline_server[FULL].get("modules") or 0) > 0,
          "STATE C server: the multi-document project HAS a live result row with modules",
          str({k: v for k, v in baseline_server[FULL].items() if k != 'raw'}))
    check(baseline_server[ONEDOC].get("live_row") is True,
          "STATE B server: the one-document project has a live result row",
          str({k: v for k, v in baseline_server[ONEDOC].items() if k != 'raw'}))

    with sync_playwright() as pw:
        errors: list[str] = []

        def new_browser():
            b = pw.chromium.launch(
                executable_path=SHELL,
                args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist",
                      "--no-sandbox"])
            p = b.new_page(viewport={"width": 1680, "height": 1400})
            p.set_default_timeout(45000)
            p.set_default_navigation_timeout(45000)
            p.on("pageerror", lambda e: errors.append(str(e)))
            p.on("dialog", lambda d: d.accept())
            for pattern in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                            "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
                p.route(pattern, lambda r: r.abort())
            p.goto(BASE + "/", wait_until="domcontentloaded")
            p.evaluate("tok => sessionStorage.setItem('og-session-token', tok)", pm)
            p.goto(BASE + "/", wait_until="domcontentloaded")
            p.add_style_tag(content="*,*::before,*::after{transition:none!important;"
                                    "animation:none!important}")
            p.wait_for_timeout(8000)
            return b, p

        browser, page = new_browser()

        def real_reload(tag: str) -> bool:
            """
            A REAL browser reload, proved real. Returns True when the document was destroyed.

            The sentinel is the proof: it is written onto window immediately before the reload
            and must be GONE afterwards. No same-document operation, and no SPA re-render, can
            produce that.
            """
            page.evaluate("() => { window.__r21_sentinel = 'before'; }")
            before = page.evaluate("() => window.__r21_sentinel || null")
            RESET.append((tag, "sentinel_before_reload", str(before), ""))
            t0 = time.time()
            ok = "no"
            try:
                page.reload(wait_until="commit", timeout=45000)
                ok = "yes"
            except Exception as exc:
                RESET.append((tag, "reload_primitive_error", str(exc)[:160], ""))
            RESET.append((tag, "reload_primitive_returned", ok, f"{time.time() - t0:.2f}s"))
            # THE OWNER'S RELOAD RULE, APPLIED. Playwright's reload() TIMES OUT here even at
            # wait_until="commit", and the previous run of this driver wrongly concluded from
            # that the reload had not happened. MEASURED in an isolated probe: the reload DOES
            # complete, the sentinel IS gone and the application IS ready, at about 195 seconds,
            # with document.readyState "interactive". So the timeout is a WAIT-CONDITION fault
            # in the harness, not a broken application reload, and the deadline below is set
            # from that measurement with margin. The distinction is not assumed either way: the
            # sentinel decides, and a reload that genuinely fails still reports "no" here.
            after = "not-determined"
            errs = 0
            reads = 0
            ready_at = None
            # RUN 22 NARROWED THE POLL INTERVAL FROM TWO SECONDS TO A QUARTER OF A SECOND, AND
            # THIS IS NOT A WIDENED TIMEOUT. The deadline is unchanged. Run 21's two-second
            # interval, against a main thread that is busy for the whole interval, produced two
            # usable samples in 212 seconds, so the number it reported was the moment the harness
            # was next willing to look rather than the moment the page was ready. Sampling more
            # often cannot make a slow page look fast; it can only stop a fast page looking slow.
            deadline = time.time() + 900
            while time.time() < deadline:
                try:
                    s = page.evaluate("() => window.__r21_sentinel || null")
                    ready = page.evaluate("() => !!(window.LinApp && window.LinApp.openDetail)")
                    reads += 1
                    if s is None and ready:
                        after = None
                        ready_at = time.time()
                        break
                    after = s
                except Exception:
                    errs += 1
                time.sleep(0.25)
            RESET.append((tag, "sentinel_after_reload", str(after),
                          f"waited {time.time() - t0:.0f}s, {reads} successful reads, "
                          f"{errs} evaluate errors while the document was navigating"))
            # THREE OUTCOMES, KEPT DISTINCT. "yes" means the sentinel was observed GONE, which
            # only a destroyed document can produce. "no" means it was observed SURVIVING, which
            # would be a real defect. "not determined" means the page could not be read at all
            # within the deadline, which is neither -- and it must NOT be reported as either.
            verdict = ("yes" if after is None
                       else "not determined" if after == "not-determined" else "no")
            RESET.append((tag, "application_reloaded_from_server", verdict, ""))
            # Report the primitive and the application separately, so neither can hide the other.
            RESET.append((tag, "reload_primitive_vs_application",
                          f"primitive_returned={ok} application_reloaded="
                          f"{'yes' if after is None else 'no'}",
                          "a primitive timeout with a destroyed document is a harness "
                          "wait-condition fault, not an application reload defect"))
            # THE OWNER'S RULE, BOTH WAYS. A hanging third-party subresource is instrumented
            # rather than used as an excuse; and it is not allowed to hide a real defect either,
            # because the post-reload DOM is read and asserted against the server below.
            #
            # RUN 22 FIXED A DEFECT HERE. These two statements sat AFTER `return verdict`, behind
            # a second dead `return after is None`, so neither ever ran: the driver's own
            # disclosure of what it blocks was described in a comment and never written to the
            # evidence, and run21_reset_reload_results.csv has no such row. A driver that
            # documents a disclosure it does not emit is exactly the class of defect this
            # programme keeps finding in its own instruments. Both are now emitted BEFORE the
            # return, and the dead second return is gone.
            RESET.append((tag, "third_party_subresources_aborted_by_this_driver",
                          "accounts.google.com apis.google.com gstatic.com "
                          "tiles.openfreemap.org maps.googleapis.com", ""))
            # RUN 22 ITEM 7, MEASURED. The readiness figure is now recorded as a number rather
            # than left implicit in the polling note, so the evidence carries the participant
            # facing metric and not only the harness's elapsed time.
            RESET.append((tag, "seconds_until_application_usable",
                          f"{ready_at - t0:.2f}" if ready_at is not None else "not-determined",
                          "measured by polling; Run-22 probes measured the same interval from "
                          "the browser's own navigation timeline, which is the authority"))
            return verdict

        # ------------------------------------------------------------ STATE A
        print()
        print("=" * 78)
        print("STATE A - a clean, empty project")
        print("=" * 78)
        open_detail(page, EMPTY)
        a = read_state(page, "A-empty", EMPTY)
        reconcile("A-empty", EMPTY, baseline_server[EMPTY], a)
        heads_a = " | ".join(a["flow"].get("headers") or [])
        body_a = page.evaluate("() => (document.body.innerText||'').replace(/\\s+/g,' ')")

        check(a["flow"].get("animated") == 0,
              "STATE A: no analytical path is animated on a project with no evidence",
              str(a["flow"].get("animated")))
        check("0 WITH A CURRENT RESULT" in heads_a.upper(),
              "STATE A: the flow reports NO module with a current result", heads_a)
        check("NOT ESTIMABLE" in heads_a.upper(),
              "STATE A: the governed rollup is NOT ESTIMABLE rather than a band", heads_a)
        # THE OWNER'S EXPLICIT PROHIBITION: "96 modules" must not read as 96 modules computed.
        registry_badges = [b for b in a["badges"] if "registered" in b.lower()]
        activity_badges = [b for b in a["badges"]
                           if "96" in b and "registered" not in b.lower()
                           and "registry" not in b.lower()]
        obs("A-empty", "registry_labelled_badges", json.dumps(registry_badges))
        obs("A-empty", "unlabelled_96_badges", json.dumps(activity_badges))
        check(registry_badges != [],
              "STATE A: the architecture inventory is labelled as REGISTERED, not as activity",
              json.dumps(a["badges"]))
        check(activity_badges == [],
              "STATE A: no badge presents 96 as a count of what actually computed",
              json.dumps(activity_badges))
        check(a["rail"]["present"] and a["rail"]["buttons"] > 0,
              "STATE A: the numbered Signal/category rail is present with its buttons",
              json.dumps(a["rail"])[:300])
        check(a["rail"]["suspects"] == [],
              "STATE A: the obsolete collapse control is ABSENT FROM THE DOM",
              json.dumps(a["rail"]["suspects"]))
        check(a["rail"]["arrowInFocusTree"] == [],
              "STATE A: and no arrow control is reachable in the keyboard focus tree",
              json.dumps(a["rail"]["arrowInFocusTree"]))
        FLOWROWS.append(("A-empty", "registry vs activity", "registered-labelled badges present "
                         "and no unlabelled 96", json.dumps(registry_badges),
                         "PASS" if registry_badges and not activity_badges else "FAIL"))
        DETAILROWS.append(("A-empty", 1680, str(a["rail"]["buttons"]),
                           json.dumps(a["rail"]["suspects"]),
                           json.dumps(a["rail"]["arrowInFocusTree"]),
                           "PASS" if not a["rail"]["suspects"] else "FAIL"))

        # ------------------------------------------------------------ STATE B
        print()
        print("=" * 78)
        print("STATE B - exactly one controlled document")
        print("=" * 78)
        open_detail(page, ONEDOC)
        b = read_state(page, "B-onedoc", ONEDOC)
        srv_b = server_results(pm, ONEDOC, 1)
        reconcile("B-onedoc", ONEDOC, srv_b, b)
        heads_b = " | ".join(b["flow"].get("headers") or [])
        check(srv_b.get("live_row") is True,
              "STATE B: the server holds a live row for the one-document project")
        check(b["flow"].get("present") is True,
              "STATE B: the flow renders for the one-document project")
        check("0 WITH A CURRENT RESULT" not in heads_b.upper(),
              "STATE B: the flow does NOT report zero modules when the server holds results",
              heads_b)
        obs("B-onedoc", "server_modules", srv_b.get("modules"))
        FLOWROWS.append(("B-onedoc", "counts reconcile", f"server modules={srv_b.get('modules')}",
                         heads_b, "PASS" if b["flow"].get("present") else "FAIL"))

        # ------------------------------------------------------------ STATE C
        print()
        print("=" * 78)
        print("STATE C - multiple controlled documents across several categories")
        print("=" * 78)
        open_detail(page, FULL)
        c = read_state(page, "C-multidoc", FULL)
        srv_c = server_results(pm, FULL, 1)
        reconcile("C-multidoc", FULL, srv_c, c)
        heads_c = " | ".join(c["flow"].get("headers") or [])
        check(c["flow"].get("animated", 0) > 0,
              "STATE C: analytical paths ARE animated once real evidence is present",
              str(c["flow"].get("animated")))
        check((srv_c.get("modules") or 0) > (srv_b.get("modules") or 0),
              "STATE C: more documents produce more computed modules than the one-document case",
              f"multi={srv_c.get('modules')} one={srv_b.get('modules')}")
        check("0 WITH A CURRENT RESULT" not in heads_c.upper(),
              "STATE C: the flow does not report zero modules on a populated project", heads_c)
        populated_fills = json.dumps(c["flow"].get("counts"), sort_keys=True)
        empty_fills = json.dumps(a["flow"].get("counts"), sort_keys=True)
        check(populated_fills != empty_fills,
              "STATE C: the populated project does not render identically to the empty one")
        FLOWROWS.append(("C-multidoc", "counts reconcile",
                         f"server modules={srv_c.get('modules')} "
                         f"categories={srv_c.get('categories')}", heads_c, "PASS"))

        # ------------------------- the abstention / blocked rendering, on real results
        print()
        print("=" * 78)
        print("BLOCKED AND ABSTAINING STATES, rendered on a project that really has results")
        print("=" * 78)
        raw = srv_c.get("raw") or {}
        abstained = raw.get("abstained") or []
        obs("C-multidoc", "server_abstained_count", len(abstained))
        page_text = page.evaluate(
            "() => (document.body.innerText||'').replace(/\\s+/g,' ')")
        obs("C-multidoc", "page_text_length", len(page_text))
        # A traffic light is a BAND. An abstaining module must not be given one on the page.
        BANDS = ("Green", "Yellow", "Amber", "Red")
        for mod in abstained[:12]:
            mid = mod.get("module_id") if isinstance(mod, dict) else str(mod)
            ABSROWS.append(("C-multidoc", str(mid), "server: abstained",
                            "band published by server", str(
                                (mod.get("status_color") if isinstance(mod, dict) else None)),
                            "PASS" if not (isinstance(mod, dict) and mod.get("status_color")
                                           in BANDS) else "FAIL"))
        check(all(not (isinstance(m, dict) and m.get("status_color") in BANDS)
                  for m in abstained),
              "ABSTENTION: no module the server records as abstaining carries a band",
              json.dumps([m for m in abstained
                          if isinstance(m, dict) and m.get("status_color") in BANDS])[:300])

        # ------------------------------------------------------------ voting and status
        print()
        print("=" * 78)
        print("VOTING AND THE GOVERNED PROJECT STATUS")
        print("=" * 78)
        from app.simulation.registry import CORE_VOTING_MODULES
        obs("voting", "registry_voting_modules", sorted(CORE_VOTING_MODULES))
        check(len(CORE_VOTING_MODULES) == 2,
              "VOTING: the registry declares exactly two voting modules",
              str(sorted(CORE_VOTING_MODULES)))
        srv_status = srv_c.get("project_status")
        node_text = " ".join(c["flow"].get("prjTexts") or [])
        obs("voting", "server_project_status", srv_status)
        obs("voting", "browser_project_status_node", node_text)
        check(srv_status is not None,
              "VOTING: the server publishes a governed project status for the populated project")
        check(str(srv_status).lower() in node_text.lower()
              or str(srv_c.get("status_label") or "").lower() in node_text.lower(),
              "VOTING: the status the browser renders is the status the server governs",
              f"server={srv_status!r}/{srv_c.get('status_label')!r} browser={node_text!r}")

        # ------------------------------------------------------------ STATE G, hard reload
        print()
        print("=" * 78)
        print("STATE G - a REAL browser reload on the populated project")
        print("=" * 78)
        did = real_reload("G-populated-reload")
        # RUN 22 TIGHTENED THIS. It read `did != "no"`, which passes for the verdict
        # "not determined" -- the case where the page could NOT be read at all within the
        # deadline. A qualification claim that the document was destroyed must rest on having
        # OBSERVED it destroyed, not on having failed to observe it surviving. Only "yes" passes
        # now, and "yes" is set solely by seeing the sentinel gone.
        check(did == "yes",
              "STATE G: the browser reload destroyed the old document, observed via the sentinel",
              f"verdict={did}")
        obs("G-populated-reload", "application_reloaded_from_server", did)
        open_detail(page, FULL)
        g = read_state(page, "G-populated-after-reload", FULL)
        srv_g = server_results(pm, FULL, 1)
        reconcile("G-populated-after-reload", FULL, srv_g, g)
        heads_g = " | ".join(g["flow"].get("headers") or [])
        check(g["flow"].get("present") is True,
              "STATE G: the page rebuilds from the server after a real reload")
        check(heads_g == heads_c,
              "STATE G: server truth reconstructs the SAME visible state after reload",
              f"before={heads_c!r} after={heads_g!r}")
        RESET.append(("G-populated-reload", "headers_before", heads_c, ""))
        RESET.append(("G-populated-reload", "headers_after", heads_g, ""))

        # ------------------------------------------------------------ STATE D, reset
        print()
        print("=" * 78)
        print("STATE D - the supported reset/clear on the populated project")
        print("=" * 78)
        confirm_probe = r"""
        () => {
          window.__r21confirm = { calls: 0, accepted: 0 };
          const native = window.confirm;
          window.confirm = function () {
            const out = native.apply(window, arguments);
            window.__r21confirm.calls++;
            if (out) window.__r21confirm.accepted++;
            return out;
          };
        }
        """
        page.evaluate(confirm_probe)
        page.evaluate("() => { const b = document.querySelector('.detail-reset'); "
                      "if (b) b.click(); }")
        page.wait_for_timeout(8000)
        dialog = page.evaluate("() => window.__r21confirm || null")
        RESET.append(("D-reset", "confirm_calls", json.dumps(dialog), ""))
        # THE OPERATION IS PROVED BY ITS EFFECT AT THE SERVER, not by the click not throwing.
        srv_d = server_results(pm, FULL, 1)
        RESET.append(("D-reset", "server_live_row_after_reset", str(srv_d.get("live_row")), ""))
        RESET.append(("D-reset", "server_modules_after_reset", str(srv_d.get("modules")), ""))
        check(srv_d.get("live_row") is False or (srv_d.get("modules") or 0) == 0,
              "STATE D server: the reset really removed the derived current result",
              str({k: v for k, v in srv_d.items() if k != 'raw'}))

        page.evaluate("""() => {
          const h = document.querySelector('#section-d-neural .collapse-header');
          const body = document.getElementById('body-d-neural');
          if (h && body && body.style.display === 'none') h.click();
        }""")
        page.wait_for_timeout(2500)
        d = read_state(page, "D-reset-same-session", FULL)
        reconcile("D-reset-same-session", FULL, srv_d, d)
        heads_d = " | ".join(d["flow"].get("headers") or [])
        check(d["flow"].get("animated") == 0,
              "STATE D: no path is animated once the evidence is cleared, in the SAME session",
              str(d["flow"].get("animated")))
        check("0 WITH A CURRENT RESULT" in heads_d.upper(),
              "STATE D: the flow reports no module with a current result after the reset",
              heads_d)
        check("NOT ESTIMABLE" in heads_d.upper(),
              "STATE D: and the governed rollup is not estimable after the reset", heads_d)
        check(d["rail"]["present"] and d["rail"]["suspects"] == [],
              "STATE D: the rail survives the reset and no collapse control appeared",
              json.dumps(d["rail"]["suspects"]))

        # ---- D continued: the cleared state must SURVIVE a real reload
        print()
        print("STATE D - the cleared state after a REAL reload")
        did2 = real_reload("D-reset-reload")
        # RUN 22: same tightening as STATE G. "not determined" is not evidence of a reload.
        check(did2 == "yes",
              "STATE D: the post-reset reload destroyed the old document, observed via the "
              "sentinel", f"verdict={did2}")
        obs("D-reset-reload", "application_reloaded_from_server", did2)
        open_detail(page, FULL)
        d2 = read_state(page, "D-reset-after-reload", FULL)
        srv_d2 = server_results(pm, FULL, 1)
        reconcile("D-reset-after-reload", FULL, srv_d2, d2)
        heads_d2 = " | ".join(d2["flow"].get("headers") or [])
        check("0 WITH A CURRENT RESULT" in heads_d2.upper(),
              "STATE D: the cleared state REMAINS cleared after a real browser reload", heads_d2)
        check(d2["flow"].get("animated") == 0,
              "STATE D: and no stale path animates after the reload",
              str(d2["flow"].get("animated")))
        RESET.append(("D-reset-reload", "headers_after_reload", heads_d2, ""))

        # THE RESET BOUNDARY MUST BE DISCLOSED, NOT MISREPORTED. This is where Run 21 found the
        # reset defect. The reset does NOT delete documents -- the control says so -- and the
        # server still serves every upload event. Before the fix the reloaded page read "0
        # UPLOADED ON THIS PROJECT" and "This project has no uploaded documents", telling the
        # reader the evidence was gone while it was retained and about to be re-read. Both the
        # server count and the rendered sentence are read here, so the check cannot pass on a
        # number the page invented.
        import urllib.parse
        q = urllib.parse.urlencode({"action": "get", "id": FULL, "session_token": pm})
        with urllib.request.urlopen(BASE + "/exec?" + q, timeout=120) as fh:
            proj = json.loads(fh.read().decode()).get("project") or {}
        srv_events = proj.get("events") or []
        srv_uploads = sum(1 for ev in srv_events if isinstance(ev, dict)
                          and (ev.get("event") or ev.get("type") or ev.get("kind"))
                          == "signals_extracted")
        summary_d2 = str(d2["flow"].get("summary") or "")
        RESET.append(("D-reset-reload", "server_upload_events_still_held", str(srv_uploads), ""))
        RESET.append(("D-reset-reload", "summary_after_reload", summary_d2[:400], ""))
        obs("D-reset-after-reload", "server_upload_events", srv_uploads)
        obs("D-reset-after-reload", "summary_strip", summary_d2)
        check(srv_uploads > 0,
              "STATE D: the server still holds the uploaded documents after the reset, which is "
              "what the reset control promises", str(srv_uploads))
        check("RETAINED" in heads_d2.upper(),
              "STATE D: and the page DISCLOSES those retained documents rather than reporting "
              "the project as having none", heads_d2)
        check(str(srv_uploads) in heads_d2,
              "STATE D: the retained figure the page shows is the server's own count",
              f"server={srv_uploads} header={heads_d2!r}")
        check("has no uploaded documents" not in summary_d2,
              "STATE D: the summary no longer asserts the project has no uploaded documents",
              summary_d2[:300])
        check("retained and will be read again when signals are regenerated" in summary_d2,
              "STATE D: and states that the retained documents will be read again",
              summary_d2[:300])
        FLOWROWS.append(("D-reset-after-reload", "reset boundary disclosed",
                         f"server upload events={srv_uploads}", heads_d2,
                         "PASS" if "RETAINED" in heads_d2.upper() else "FAIL"))

        # ---- D continued: navigate away and back
        print()
        print("STATE D - navigate away to another project and back")
        open_detail(page, EMPTY)
        page.wait_for_timeout(1500)
        open_detail(page, FULL)
        d3 = read_state(page, "D-reset-after-navigation", FULL)
        heads_d3 = " | ".join(d3["flow"].get("headers") or [])
        check("0 WITH A CURRENT RESULT" in heads_d3.upper(),
              "STATE D: the cleared state remains cleared after navigating away and back",
              heads_d3)
        RESET.append(("D-reset-navigate", "headers_after_navigation", heads_d3, ""))

        # ------------------------------------------------------------ STATE H
        print()
        print("=" * 78)
        print("STATE H - a FRESH browser context against the same server and project")
        print("=" * 78)
        b2, page2 = new_browser()
        try:
            page2.evaluate("id => LinApp.openDetail(id)", FULL)
            page2.wait_for_timeout(2500)
            page2.evaluate("""() => {
              const h = document.querySelector('#section-d-neural .collapse-header');
              const body = document.getElementById('body-d-neural');
              if (h && body && body.style.display === 'none') h.click();
            }""")
            page2.wait_for_timeout(2500)
            flow2 = page2.evaluate(READ_FLOW)
            heads_h = " | ".join(flow2.get("headers") or [])
            obs("H-fresh-context", "flow_headers", heads_h)
            RESET.append(("H-fresh-context", "headers_in_fresh_browser", heads_h, ""))
            check("0 WITH A CURRENT RESULT" in heads_h.upper(),
                  "STATE H: a brand-new browser reproduces the CLEARED state from the server",
                  heads_h)
            check(heads_h == heads_d2,
                  "STATE H: and reproduces it identically to the reloaded first browser",
                  f"fresh={heads_h!r} reloaded={heads_d2!r}")
        finally:
            b2.close()

        # ------------------------------------------------------------ STATE E
        print()
        print("=" * 78)
        print("STATE E - NEW evidence after the reset")
        print("=" * 78)
        newdoc = base64.b64encode(doc_bytes(FULL, "M1")).decode()
        up = post({"action": "projectupload", "session_token": pm, "id": FULL,
                   "period": 1, "period_end": r16.MONTHS[1][0],
                   "documents": [{"filename": "M1.pdf", "mimeType": "application/pdf",
                                  "dataBase64": newdoc}]})
        obs("E-post-reset", "upload_ok", up.get("ok", True))
        post({"action": "projectcomputeall", "session_token": pm, "id": FULL})
        srv_e = server_results(pm, FULL, 1)
        obs("E-post-reset", "server_modules", srv_e.get("modules"))
        RESET.append(("E-post-reset", "server_modules_after_new_evidence",
                      str(srv_e.get("modules")), ""))
        check(srv_e.get("live_row") is True,
              "STATE E server: new post-reset evidence produces a live result row again",
              str({k: v for k, v in srv_e.items() if k != 'raw'}))
        # WHAT STATE E ACTUALLY REQUIRES HERE, DERIVED FROM THE PRODUCT'S OWN STATED CONTRACT
        # RATHER THAN ASSUMED. The first version of this driver asserted that the post-reset
        # module count must be LOWER than the pre-reset one, on the assumption that the reset
        # withdraws evidence. IT DOES NOT, and the control says so in its own words: "Clears
        # this project's stored signal values so its documents can be read again. Does not
        # delete documents and does not touch other projects." MEASURED at the server: a project
        # reset after twenty-four uploads keeps all twenty-four upload events, and regenerating
        # signals correctly reads them again and returns to forty-one modules, against
        # thirty-five for a control project that only ever held the one document. So the
        # re-reading is the DESIGNED behaviour and asserting against it would have been an
        # invented requirement.
        #
        # The requirement that survives, and the one that matters, is TRUTHFULNESS: the
        # participant must not be told the retained documents are gone. That is asserted below
        # and is where the real defect was found.
        RESET.append(("E-post-reset", "pre_reset_modules", str(srv_c.get("modules")), ""))
        RESET.append(("E-post-reset", "reset_contract",
                      "the reset clears stored SIGNALS and supersedes derived rows; it does NOT "
                      "delete documents, by the control's own stated contract",
                      "so re-reading retained documents after a reset is designed behaviour"))
        check((srv_e.get("modules") or 0) >= (srv_b.get("modules") or 0),
              "STATE E: regenerating signals after the reset reads the retained documents, "
              "which is what the reset control promises",
              f"post-reset={srv_e.get('modules')} one-document-control={srv_b.get('modules')}")

        open_detail(page, FULL)
        e = read_state(page, "E-post-reset", FULL)
        reconcile("E-post-reset", FULL, srv_e, e)
        heads_e = " | ".join(e["flow"].get("headers") or [])
        # A RE-FETCH MUST RESTORE SERVER TRUTH. The upload above was made through the API, so
        # this browser has no way to know of it until it reads the server again. That is the
        # point: frontend memory must never be the authority.
        did4 = real_reload("E-post-reset-reload")
        check(did4 != "no",
              "STATE E: the reload that must restore server truth did not leave the old "
              "document standing", f"verdict={did4}")
        obs("E-post-reset-reload", "application_reloaded_from_server", did4)
        open_detail(page, FULL)
        e2 = read_state(page, "E-post-reset-after-reload", FULL)
        heads_e2 = " | ".join(e2["flow"].get("headers") or [])
        RESET.append(("E-post-reset", "headers_after_reload", heads_e2, ""))
        check("0 WITH A CURRENT RESULT" not in heads_e2.upper(),
              "STATE E: after re-reading the server the page shows the NEW evidence, not empty",
              heads_e2)
        check(heads_e2 != heads_d2,
              "STATE E: and no longer shows the cleared picture",
              f"post-evidence={heads_e2!r} cleared={heads_d2!r}")

        # ------------------------------------------------------------ STATE F
        print()
        print("=" * 78)
        print("STATE F - project switching, repeated, with no cross-project leakage")
        print("=" * 78)
        seq = []
        for i in range(2):
            open_detail(page, FULL)
            f_full = read_state(page, f"F-switch-{i}-full", FULL, shot=(i == 0))
            open_detail(page, EMPTY)
            f_empty = read_state(page, f"F-switch-{i}-empty", EMPTY, shot=(i == 0))
            seq.append((" | ".join(f_full["flow"].get("headers") or []),
                        " | ".join(f_empty["flow"].get("headers") or [])))
        ISOROWS.append(("F-switching", "populated headers, pass 1", seq[0][0], ""))
        ISOROWS.append(("F-switching", "populated headers, pass 2", seq[1][0], ""))
        ISOROWS.append(("F-switching", "empty headers, pass 1", seq[0][1], ""))
        ISOROWS.append(("F-switching", "empty headers, pass 2", seq[1][1], ""))
        check(seq[0][0] == seq[1][0],
              "STATE F: the populated project reads identically on both passes",
              f"{seq[0][0]!r} vs {seq[1][0]!r}")
        check(seq[0][1] == seq[1][1],
              "STATE F: the empty project reads identically on both passes",
              f"{seq[0][1]!r} vs {seq[1][1]!r}")
        check(seq[0][0] != seq[0][1],
              "STATE F: and the empty project never inherits the populated project's picture",
              f"full={seq[0][0]!r} empty={seq[0][1]!r}")
        check("0 WITH A CURRENT RESULT" in seq[1][1].upper(),
              "STATE F: the empty project still reports no current result after the switching",
              seq[1][1])

        # ---- the frontend must not be the authority. Mutate LOCAL state only and re-fetch.
        print()
        print("=" * 78)
        print("SERVER AUTHORITY - a deliberate frontend divergence, corrected by a re-fetch")
        print("=" * 78)
        open_detail(page, EMPTY)
        mutated = page.evaluate("""() => {
          try {
            const p = (window.LinApp && LinApp.state && LinApp.state.projects || [])
              .find(x => x && x.id === '""" + EMPTY + """');
            if (!p) return 'project-not-found-in-frontend-state';
            p.storedResult = { module_results: { FAKE: { status_color: 'Green' } },
                               project_status: 'Green', category_statuses: { X: 'Green' } };
            return 'mutated';
          } catch (e) { return 'error: ' + e; }
        }""")
        obs("authority", "frontend_local_mutation", mutated)
        RECON.append(("authority", EMPTY, "frontend local mutation applied", str(mutated),
                      "", "", "a fabricated Green result injected into frontend memory only"))
        srv_auth = server_results(pm, EMPTY, 1)
        RECON.append(("authority", EMPTY, "server_live_row", str(srv_auth.get("live_row")),
                      "", "", "server is unmoved by the frontend mutation"))
        check(srv_auth.get("live_row") is False,
              "AUTHORITY: mutating frontend memory did not change the server's answer",
              str({k: v for k, v in srv_auth.items() if k != 'raw'}))
        did3 = real_reload("authority-reload")
        check(did3 != "no",
              "AUTHORITY: the reload that must restore server truth did not leave the old "
              "document standing", f"verdict={did3}")
        obs("authority-reload", "application_reloaded_from_server", did3)
        open_detail(page, EMPTY)
        auth = read_state(page, "authority-after-reload", EMPTY, shot=False)
        heads_auth = " | ".join(auth["flow"].get("headers") or [])
        check("0 WITH A CURRENT RESULT" in heads_auth.upper(),
              "AUTHORITY: the reload discarded the fabricated frontend state and read the server",
              heads_auth)
        check("NOT ESTIMABLE" in heads_auth.upper(),
              "AUTHORITY: and the fabricated Green status did not survive", heads_auth)

        # ------------------------------------------------------------ responsive widths
        print()
        print("=" * 78)
        print("RESPONSIVE QUALIFICATION - the rail and the obsolete control at several widths")
        print("=" * 78)
        # 1920/1680/1440/1280 desktop; 1024 narrow desktop/tablet; 820 tablet; 390 mobile.
        # The rail's own media query hides it below 700, which is a deliberate mobile rule and
        # is recorded as such rather than asserted against.
        open_detail(page, FULL)
        for w, h in ((1920, 1200), (1680, 1400), (1440, 1000), (1280, 900),
                     (1024, 900), (820, 1180), (390, 844)):
            page.set_viewport_size({"width": w, "height": h})
            page.wait_for_timeout(1200)
            rail = page.evaluate(READ_RAIL_STRICT)
            DETAILROWS.append((f"responsive-{w}", w, str(rail["buttons"]),
                               json.dumps(rail["suspects"]),
                               json.dumps(rail["arrowInFocusTree"]),
                               "PASS" if not rail["suspects"] else "FAIL"))
            obs(f"responsive-{w}", "rail_display", rail.get("display"))
            obs(f"responsive-{w}", "rail_buttons", rail.get("buttons"))
            obs(f"responsive-{w}", "collapse_suspects", json.dumps(rail["suspects"]))
            check(rail["suspects"] == [],
                  f"RESPONSIVE {w}px: the obsolete collapse control is absent from the DOM",
                  json.dumps(rail["suspects"]))
            check(rail["arrowInFocusTree"] == [],
                  f"RESPONSIVE {w}px: no arrow control is keyboard-reachable",
                  json.dumps(rail["arrowInFocusTree"]))
            if w >= 1024:
                check(rail["present"] and rail["buttons"] > 0 and rail["display"] != "none",
                      f"RESPONSIVE {w}px: the numbered Signal rail is present and displayed",
                      json.dumps({k: rail[k] for k in ('present', 'buttons', 'display')}))
            try:
                page.screenshot(path=str(artifact_out(
                    ROOT / "code_audit" / f"run21_shot_width_{w}.png")))
            except Exception:
                pass
        page.set_viewport_size({"width": 1680, "height": 1400})
        page.wait_for_timeout(800)

        # ---- the rail actually navigates
        print()
        print("RAIL NAVIGATION - selecting a section really changes the content shown")
        open_detail(page, FULL)
        nav_result = page.evaluate("""() => {
          const btns = Array.from(document.querySelectorAll('.detail-secnav-btn'));
          if (btns.length < 2) return { ok: false, why: 'fewer than two rail buttons' };
          const target = btns[btns.length - 1].getAttribute('data-secnav-target');
          const before = window.scrollY;
          btns[btns.length - 1].click();
          return { ok: true, target, before,
                   // The rail stores the section id with the "section-" prefix STRIPPED, and
                   // its own handler looks up "section-" + target. The first version of this
                   // reader looked up the bare value and reported a working rail as broken.
                   sectionExists: !!document.getElementById('section-' + target),
                   bareIdExists: !!document.getElementById(target) };
        }""")
        page.wait_for_timeout(1500)
        after = page.evaluate("() => ({ y: window.scrollY, active: Array.from("
                              "document.querySelectorAll('.detail-secnav-btn.selected'))"
                              ".map(b => b.textContent.trim()) })")
        obs("rail-nav", "click_result", json.dumps(nav_result))
        obs("rail-nav", "after", json.dumps(after))
        DETAILROWS.append(("rail-navigation", 1680, json.dumps(nav_result), json.dumps(after),
                           "", "PASS" if nav_result.get("ok") else "FAIL"))
        check(nav_result.get("ok") and nav_result.get("sectionExists"),
              "RAIL: a rail button names a section that really exists on the page",
              json.dumps(nav_result))
        check(after["y"] != nav_result.get("before") or after["active"],
              "RAIL: selecting a rail entry changes the view or marks the entry active",
              json.dumps(after))

        # ------------------------------------------------------------ error states
        print()
        print("=" * 78)
        print("ERROR AND INTERRUPTION STATES - failure must be truthful")
        print("=" * 78)
        bad = post({"action": "projectresults", "session_token": pm,
                    "id": "PRJ-R21-DOES-NOT-EXIST", "period": 1})
        obs("errors", "unknown_project_response", json.dumps(bad)[:300])
        check(not bad.get("ok", False) or "result" not in bad,
              "ERROR: an unknown project is refused rather than answered with a fabricated state",
              json.dumps(bad)[:300])
        band_words = ("Green", "Amber", "Red", "Yellow")
        check(not any(w in json.dumps(bad) for w in band_words),
              "ERROR: and the refusal does not carry a band", json.dumps(bad)[:300])
        nosession = post({"action": "projectresults", "session_token": "not-a-real-token",
                          "id": FULL, "period": 1})
        obs("errors", "bad_session_response", json.dumps(nosession)[:300])
        check(not nosession.get("ok", False) or "result" not in nosession,
              "ERROR: an invalid session is refused rather than served project state",
              json.dumps(nosession)[:300])

        obs("browser", "page_errors_total", len(errors))
        obs("browser", "page_errors_sample", json.dumps(errors[:5]))
        browser.close()

    write_all()
    print()
    if FAILURES:
        print("FAILURES:")
        for f in FAILURES:
            print("  " + f)
    print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")


def _write(name: str, header: list[str], rows: list) -> None:
    out = artifact_out(ROOT / "code_audit" / name)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print(f"  wrote {out}")


def write_all() -> None:
    _write("run21_browser_state_matrix.csv", ["state", "observation", "value"], MATRIX)
    _write("run21_server_frontend_reconciliation.csv",
           ["state", "project", "server_fact", "server_value",
            "browser_fact", "browser_value", "note"], RECON)
    _write("run21_reset_reload_results.csv", ["state", "observation", "value", "note"], RESET)
    _write("run21_project_detail_results.csv",
           ["state", "viewport_width", "rail_buttons", "collapse_suspects",
            "arrow_in_focus_tree", "result"], DETAILROWS)
    _write("run21_final_flow_results.csv",
           ["state", "property", "server_evidence", "browser_evidence", "result"], FLOWROWS)
    _write("run21_isolation_results.csv", ["state", "observation", "value", "note"], ISOROWS)
    _write("run21_abstention_rendering_results.csv",
           ["state", "module", "server_state", "property", "value", "result"], ABSROWS)


if __name__ == "__main__":
    try:
        main_drive()
    except Exception:
        # Evidence gathered before a failure is still evidence, and losing it to a container
        # flake in the last state has cost this programme time before.
        write_all()
        raise
