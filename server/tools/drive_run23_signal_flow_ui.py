#!/usr/bin/env python3
"""
POST-RUN-22 UI CORRECTION. THE SERVED PROJECT DETAIL PAGE, DRIVEN IN A REAL BROWSER.

WHY THIS DRIVER EXISTS ALONGSIDE THE RUN-16/18 ONES. Run 21 reported "FINAL FLOW
qualification: PASS" and Run 22 re-verified it, but the owner reproduced FALSE ACTIVITY on the
Signal Flow of an EMPTY project with their own eyes. The Run-16/18 drivers read the diagram's
headers, its summary sentence, its animated-path count and a histogram of node FILLS. None of
them ever asserted, on the empty project, that no node carries an ACTIVE VISUAL STATE. A
histogram that is merely recorded as a fact cannot fail, and the two checks the empty state did
carry were about the navigation rail. That is the vacuous shape this programme keeps finding.

This driver reads the shipped active-state markers themselves, per node:

  * document nodes  — fill, opacity, and the presence of the `url(#lnf-glow-DocOn)` filter
                      that the implementation uses to make an uploaded document GLOW;
  * module dots     — fill, opacity, glow filter, `lnf-red-pulse`;
  * category nodes  — the same;
  * edges           — the `.lnf-active` marker class and the four `.lnf-flow-*` animation
                      classes the implementation adds only to a live edge.

and it asserts an EMPTY project has zero of every one of them, rather than recording them.

STATES DRIVEN: A empty, B one document, C multi-document, D reset, E hard reload after reset,
F project switch (populated -> empty -> populated), plus the navigation rail at four widths and
a non-vacuity mutation that forces one empty-project node active and requires the named guard
to fail RED.

Run:
    DATABASE_URL=sqlite:///... SESSION_SECRET=... PYTHONIOENCODING=utf-8 \
        python tools/drive_run23_signal_flow_ui.py
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import threading
import time
import urllib.request

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

import tools.drive_run16_final_flow as r16  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]

r16.PORT = 8231
r16.BASE = f"http://127.0.0.1:{r16.PORT}"
r16.ADMIN = "r23-browser-admin"
r16.EMPTY = "PRJ-R23-EMPTY"
r16.FULL = "PRJ-R23-FULL"
r16.ONEDOC = "PRJ-R23-ONEDOC"
r16.LABEL = os.environ.get("RUN23_LABEL", "run23_signal_flow_ui")

EMPTY, FULL, ONEDOC = r16.EMPTY, r16.FULL, r16.ONEDOC
check, fact, post, open_detail, server_state = (
    r16.check, r16.fact, r16.post, r16.open_detail, r16.server_state)

WIDTHS = ((1920, "wide-desktop"), (1440, "normal-desktop"),
          (1024, "tablet"), (760, "narrow"), (390, "mobile"))

# ---------------------------------------------------------------- DOM readers

# THE ACTIVE-STATE READER. Reads the markers the shipped implementation actually uses, not a
# proxy for them. `activeDocs` counts a document node lit by the DocOn glow filter or the
# DocOn fill; `activeMods`/`activeCats` count nodes carrying a verdict glow (the filter is
# added ONLY when the status is not 'None'); `flowClasses` counts the animation classes and
# `activeCls` the explicit `.lnf-active` marker.
READ_ACTIVE = r"""
() => {
  const c = document.querySelector('.detail-neural-flow');
  if (!c) return { present: false };
  const svg = c.querySelector('svg');
  if (!svg) return { present: false };
  const nodes = svg.querySelector('#lnf-nodes');
  const shapes = Array.from(nodes.querySelectorAll('circle,rect,polygon'));
  const info = shapes.map(el => ({
    fill: (el.getAttribute('fill') || '').toLowerCase(),
    op: parseFloat(el.getAttribute('opacity') || '1'),
    filter: el.getAttribute('filter') || '',
    cls: String(el.getAttribute('class') || ''),
    r: el.getAttribute('r') || '',
    tag: el.tagName.toLowerCase(),
  }));
  const glow = info.filter(n => /lnf-glow-/.test(n.filter));
  const docGlow = glow.filter(n => /DocOn/.test(n.filter));
  const verdictGlow = glow.filter(n => !/DocOn/.test(n.filter));
  const headers = Array.from(svg.querySelectorAll('text'))
    .filter(t => parseFloat(t.getAttribute('y')) < 34 && t.getAttribute('font-weight') === '700')
    .map(t => t.textContent.trim());
  const prj = svg.querySelector('#lnf-prj');
  const summary = c.querySelector('.lnf-summary');
  const fills = {};
  info.forEach(n => { if (n.fill && n.fill !== 'none') fills[n.fill] = (fills[n.fill] || 0) + 1; });
  return {
    present: true,
    headers,
    fills,
    glowNodes: glow.length,
    docGlowNodes: docGlow.length,
    verdictGlowNodes: verdictGlow.length,
    pulseNodes: nodes.querySelectorAll('.lnf-red-pulse').length,
    activeCls: svg.querySelectorAll('.lnf-active').length,
    animated: svg.querySelectorAll('.lnf-flow-a,.lnf-flow-b,.lnf-flow-c,.lnf-flow-fb').length,
    staticPaths: svg.querySelectorAll('.lnf-static').length,
    prjTexts: prj ? Array.from(prj.querySelectorAll('text')).map(t => t.textContent.trim()) : [],
    summary: summary ? summary.innerText.replace(/\s+/g, ' ').trim() : null,
    // Bright doc rows: the implementation renders an uploaded document at opacity .88 with a
    // glow. Anything at or above .7 in the doc column is visually lit.
    brightNodes: info.filter(n => n.op >= 0.7).length,
    brightList: info.filter(n => n.op >= 0.7)
      .map(n => n.tag + ':' + n.fill + ':' + n.op).slice(0, 40),
  };
}
"""

# THE NAMED GUARD. One function, used by the empty-state checks AND by the non-vacuity
# mutation, so the mutation proves the very assertion the acceptance relies on.
GUARD_NAME = "GUARD_EMPTY_PROJECT_NO_ACTIVE_MARKER"


def guard_empty_no_active(flow: dict) -> tuple[bool, str]:
    """RED when any Signal Flow node or edge carries an active-state marker."""
    bad = []
    if flow.get("docGlowNodes"):
        bad.append(f"docGlowNodes={flow['docGlowNodes']}")
    if flow.get("verdictGlowNodes"):
        bad.append(f"verdictGlowNodes={flow['verdictGlowNodes']}")
    if flow.get("pulseNodes"):
        bad.append(f"pulseNodes={flow['pulseNodes']}")
    if flow.get("activeCls"):
        bad.append(f"activeCls={flow['activeCls']}")
    if flow.get("animated"):
        bad.append(f"animatedEdges={flow['animated']}")
    if flow.get("brightNodes"):
        bad.append(f"brightNodes={flow['brightNodes']}")
    return (not bad), ", ".join(bad)


READ_RAIL2 = r"""
() => {
  const nav = document.getElementById('detail-secnav');
  const cs = nav ? getComputedStyle(nav) : null;
  const btns = nav ? Array.from(nav.querySelectorAll('.detail-secnav-btn')) : [];
  const arrows = /[◀▶◂▸‹›❮❯«»]/;
  const suspects = Array.from(document.querySelectorAll('button,[role="button"],a'))
    .filter(el => {
      const t = (el.textContent || '').trim();
      const a = ((el.getAttribute('aria-label') || '') + ' ' +
                 (el.getAttribute('title') || '')).toLowerCase();
      const cls = String(el.className && el.className.baseVal !== undefined
                   ? el.className.baseVal : (el.className || '')).toLowerCase();
      return arrows.test(t) || /\bcollapse\b|\bhide (the )?(rail|nav|navigator)\b/.test(a) ||
             /secnav-(toggle|collapse|hide)/.test(cls);
    }).map(el => (el.textContent || '').trim().slice(0, 24));
  // Hit-testing: for each numbered control, is the control itself the element the browser
  // would deliver a click to at its own centre? An invisible overlay fails this.
  const hit = btns.map(b => {
    const r = b.getBoundingClientRect();
    const el = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
    return { label: b.textContent.trim(), w: Math.round(r.width), h: Math.round(r.height),
             top: Math.round(r.top), bottom: Math.round(r.bottom),
             hit: !!el && (el === b || b.contains(el)),
             owner: el ? (el.className && el.className.baseVal !== undefined
                          ? el.className.baseVal : String(el.className || el.tagName)) : null };
  });
  return {
    present: !!nav, hidden: nav ? nav.hasAttribute('hidden') : null,
    display: cs ? cs.display : null, opacity: cs ? cs.opacity : null,
    count: btns.length,
    selected: btns.filter(b => b.getAttribute('aria-current') === 'true').map(b => b.textContent.trim()),
    activeCls: btns.filter(b => b.classList.contains('active')).map(b => b.textContent.trim()),
    labels: btns.map(b => b.getAttribute('aria-label')),
    hit, suspects,
    duplicates: document.querySelectorAll('#detail-secnav, .detail-secnav').length,
    inView: hit.filter(h => h.top >= 0 && h.bottom <= window.innerHeight && h.w > 0).length,
    viewportH: window.innerHeight,
  };
}
"""


def read_flow(page, settle: bool = True) -> dict:
    """
    SUSPECT YOUR OWN INSTRUMENT. The detail page fetches the full stored result AFTER its first
    paint and re-renders the diagram when it lands, so a single evaluate() can capture a
    half-populated frame and report it as the project's state. The first version of this driver
    did exactly that and reported a populated project as reading differently before and after a
    project switch — a driver artefact, not a product defect. This reads until two consecutive
    reads agree, and reports how long that took.
    """
    prev = page.evaluate(READ_ACTIVE)
    if not settle:
        return prev
    for _ in range(12):
        page.wait_for_timeout(1000)
        cur = page.evaluate(READ_ACTIVE)
        if json.dumps(cur, sort_keys=True) == json.dumps(prev, sort_keys=True):
            return cur
        prev = cur
    return prev


def report(page, state: str) -> dict:
    flow = read_flow(page)
    fact(state, "flow_present", str(flow.get("present")))
    if flow.get("present"):
        fact(state, "headers", " | ".join(flow["headers"]))
        fact(state, "doc_glow_nodes", str(flow["docGlowNodes"]))
        fact(state, "verdict_glow_nodes", str(flow["verdictGlowNodes"]))
        fact(state, "bright_nodes", str(flow["brightNodes"]))
        fact(state, "pulse_nodes", str(flow["pulseNodes"]))
        fact(state, "active_class_edges", str(flow["activeCls"]))
        fact(state, "animated_edges", str(flow["animated"]))
        fact(state, "static_edges", str(flow["staticPaths"]))
        fact(state, "node_fills", json.dumps(flow["fills"], sort_keys=True))
        fact(state, "project_status_node", " ".join(flow["prjTexts"]))
        fact(state, "summary_strip", str(flow["summary"]))
        fact(state, "bright_list", json.dumps(flow["brightList"]))
    return flow


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
            urllib.request.urlopen(r16.BASE + "/readyz", timeout=2).read()
            break
        except Exception:
            time.sleep(0.5)

    pm = r16.seed()

    print("=" * 78)
    print("SERVER STATE, through the participant's own session, before the browser")
    print("=" * 78)
    for pid in (EMPTY, FULL, ONEDOC):
        st = server_state(pm, pid, 1)
        for k in ("live_row", "modules", "categories", "project_status"):
            if k in st:
                fact("server:" + pid, k, str(st[k]))

    with sync_playwright() as pw:
        errors: list[str] = []
        b = pw.chromium.launch(executable_path=r16.SHELL,
                               args=["--use-gl=swiftshader", "--enable-webgl",
                                     "--ignore-gpu-blocklist", "--no-sandbox"])
        page = b.new_page(viewport={"width": 1680, "height": 1400})
        page.set_default_timeout(45000)
        page.set_default_navigation_timeout(45000)
        page.on("pageerror", lambda e: errors.append(str(e)))
        for pattern in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                        "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
            page.route(pattern, lambda r: r.abort())
        page.goto(r16.BASE + "/", wait_until="domcontentloaded")
        page.evaluate("tok => sessionStorage.setItem('og-session-token', tok)", pm)
        page.goto(r16.BASE + "/", wait_until="domcontentloaded")
        page.add_style_tag(content="*,*::before,*::after{transition:none!important}")
        page.wait_for_timeout(8000)

        # ---------------------------------------------------------- STATE A: empty
        print("\n" + "=" * 78)
        print("STATE A — brand-new empty project")
        print("=" * 78)
        open_detail(page, EMPTY)
        a = report(page, "A-empty")
        ok, detail = guard_empty_no_active(a)
        check(ok, f"STATE A: {GUARD_NAME} — no Signal Flow node or edge is active", detail)
        page.screenshot(path=str(ROOT / "code_audit" / f"run23_{r16.LABEL}_A-empty.png"))

        # ---------------------------------------------------------- STATE B: one doc
        print("\n" + "=" * 78)
        print("STATE B — exactly one recognised document")
        print("=" * 78)
        open_detail(page, ONEDOC)
        bflow = report(page, "B-onedoc")
        check(bflow.get("docGlowNodes") == 1,
              "STATE B: exactly one document node is lit", str(bflow.get("docGlowNodes")))
        check((bflow.get("verdictGlowNodes") or 0) > 0,
              "STATE B: at least one analytical node carries a current result")
        check((bflow.get("animated") or 0) > 0,
              "STATE B: evidence paths are live")

        # ---------------------------------------------------------- STATE C: multi
        print("\n" + "=" * 78)
        print("STATE C — multiple documents")
        print("=" * 78)
        open_detail(page, FULL)
        cflow = report(page, "C-multi")
        check((cflow.get("docGlowNodes") or 0) > (bflow.get("docGlowNodes") or 0),
              "STATE C: more document nodes are lit than with one document")
        check((cflow.get("verdictGlowNodes") or 0) >= (bflow.get("verdictGlowNodes") or 0),
              "STATE C: analytical activity is at least the one-document case")

        # ---------------------------------------------------------- STATE F: switch
        print("\n" + "=" * 78)
        print("STATE F — project switch: populated -> empty -> populated")
        print("=" * 78)
        open_detail(page, EMPTY)
        f2 = report(page, "F-switch-empty")
        ok, detail = guard_empty_no_active(f2)
        check(ok, f"STATE F: {GUARD_NAME} on the empty project after a switch", detail)
        open_detail(page, FULL)
        f3 = report(page, "F-switch-back-populated")
        # WHAT THIS CHECKS AND WHY IT IS NOT A FILL-HISTOGRAM COMPARISON. The acceptance is
        # that no illumination LEAKS between projects: the populated project must come back
        # with the same evidence lit and the same paths carrying, and the empty one must stay
        # dark. An exact per-status histogram is NOT that property, and asserting it reported a
        # defect that is not one: measured here, two module dots and the rollup move amber ->
        # red across a round trip because the first render reads the period-1 row detail.js
        # primes and a later render reads the list projection, which carries the LATEST period.
        # Both are server rows: this seeded project is Amber at periods 1-3 and Red at period 4
        # (recorded in the report). That is a period-selection artefact in an area this
        # correction was told not to redesign, and it is reported rather than papered over.
        check((f3.get("docGlowNodes") == cflow.get("docGlowNodes")
               and f3.get("animated") == cflow.get("animated")),
              "STATE F: the populated project has the same evidence lit and the same paths "
              "carrying after the round trip",
              f"before docs={cflow.get('docGlowNodes')} edges={cflow.get('animated')} / "
              f"after docs={f3.get('docGlowNodes')} edges={f3.get('animated')}")
        fact("F-switch-back-populated", "fill_histogram_before", json.dumps(cflow.get("fills"), sort_keys=True))
        fact("F-switch-back-populated", "fill_histogram_after", json.dumps(f3.get("fills"), sort_keys=True))

        # ---------------------------------------------------------- STATE D: reset
        print("\n" + "=" * 78)
        print("STATE D — reset (clear-all) on the populated project")
        print("=" * 78)
        open_detail(page, FULL)
        page.evaluate("""() => { const b = document.querySelector('.detail-reset'); if (b) b.click(); }""")
        page.wait_for_timeout(6000)
        page.evaluate("""() => {
          const h = document.querySelector('#section-d-neural .collapse-header');
          const body = document.getElementById('body-d-neural');
          if (h && body && body.style.display === 'none') h.click();
        }""")
        page.wait_for_timeout(2500)
        d = report(page, "D-reset-same-session")
        ok, detail = guard_empty_no_active(d)
        check(ok, f"STATE D: {GUARD_NAME} after the reset", detail)

        # ------------------------------------------------- STATE E: hard reload
        print("\n" + "=" * 78)
        print("STATE E — hard reload after the reset, in a fresh browser with no GL cost")
        print("=" * 78)
        # WHY A SECOND BROWSER RATHER THAN page.goto ON THIS ONE. Run 22 measured where the
        # reload cost lives: the GL pipeline. Under the swiftshader flags this page is launched
        # with, a reload does not return inside three minutes here; with WebGL disabled the
        # instrument is usable in ~288 ms. Measured again in this run: the swiftshader reload
        # exceeded a 180 s navigation budget and was abandoned, so this state is driven in a
        # SECOND browser launched with the Run-22 `webgl_disabled` flags. That is a STRONGER
        # reload than page.reload(): a brand-new browser and a brand-new context share no
        # memory, no cache and no in-page state with the session that performed the reset, so
        # whatever it draws was reconstructed from the server alone. It is proved to be a
        # different browser by the sentinel written on the first page being absent here.
        page.evaluate("() => { window.__r23_sentinel = 'before'; }")
        t_reload = time.time()
        b2 = pw.chromium.launch(executable_path=r16.SHELL,
                                args=["--disable-webgl", "--disable-gpu", "--no-sandbox"])
        page2 = b2.new_page(viewport={"width": 1680, "height": 1400})
        page2.set_default_timeout(60000)
        page2.set_default_navigation_timeout(60000)
        page2.on("pageerror", lambda e: errors.append("reload:" + str(e)))
        for pattern in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                        "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
            page2.route(pattern, lambda r: r.abort())
        page2.goto(r16.BASE + "/", wait_until="domcontentloaded")
        page2.evaluate("tok => sessionStorage.setItem('og-session-token', tok)", pm)
        page2.goto(r16.BASE + "/", wait_until="domcontentloaded")
        page2.add_style_tag(content="*,*::before,*::after{transition:none!important}")
        page2.wait_for_timeout(8000)
        fact("E-reset-reloaded", "reload_seconds", f"{time.time() - t_reload:.1f}")
        gone = page2.evaluate("() => window.__r23_sentinel === undefined")
        check(gone, "STATE E: the page really was rebuilt from the server (the first browser's "
                    "window sentinel is absent)")
        open_detail(page2, FULL)
        e = report(page2, "E-reset-reloaded")
        ok, detail = guard_empty_no_active(e)
        check(ok, f"STATE E: {GUARD_NAME} after a real reload of the reset project", detail)
        # WHAT THE RELOAD MUST RECONSTRUCT. Not byte-identical headers to the same-session
        # read for its own sake, but the same TRUTH: nothing current, nothing estimable, and
        # the retained documents disclosed. The first version of this check demanded string
        # equality and reported a FAILURE for a reloaded page that was MORE truthful than the
        # live one — it said "0 UPLOADED SINCE THE RESET, 24 RETAINED" where the live page said
        # "0 UPLOADED ON THIS PROJECT", because detail.js blanked the event log client-side.
        # That mask is now removed in production, so the two agree; the check states the
        # property and then also requires the agreement, rather than assuming one implies it.
        e_hdr = " | ".join(e.get("headers") or [])
        check("0 WITH A CURRENT RESULT" in e_hdr and "0 ESTIMABLE NOW" in e_hdr
              and "NOT ESTIMABLE" in e_hdr and "24 RETAINED" in e_hdr,
              "STATE E: the reloaded page reconstructs no current activity and discloses the "
              "retained documents", e_hdr)
        check((e.get("headers") or []) == (d.get("headers") or []),
              "STATE E: and the live page after the reset says exactly the same thing",
              f"live={' | '.join(d.get('headers') or [])} / reloaded={e_hdr}")
        page2.screenshot(path=str(ROOT / "code_audit" / f"run23_{r16.LABEL}_E-reloaded.png"))
        b2.close()

        # ------------------------------------------------ NON-VACUITY MUTATION
        print("\n" + "=" * 78)
        print("NON-VACUITY — force one empty-project node active; the guard must go RED")
        print("=" * 78)
        open_detail(page, EMPTY)
        clean = read_flow(page)
        ok_clean, _ = guard_empty_no_active(clean)
        check(ok_clean, f"NON-VACUITY: {GUARD_NAME} is GREEN before the mutation")
        mutated = page.evaluate(r"""() => {
          const svg = document.querySelector('.detail-neural-flow svg');
          const nodes = svg.querySelector('#lnf-nodes');
          const el = nodes.querySelector('circle,rect,polygon');
          el.setAttribute('filter', 'url(#lnf-glow-Green)');
          el.setAttribute('opacity', '0.88');
          return true;
        }""")
        mut = read_flow(page)
        ok_mut, mut_detail = guard_empty_no_active(mut)
        check((not ok_mut) and mutated,
              f"NON-VACUITY: {GUARD_NAME} fails RED on a forced active node", mut_detail)
        fact("non-vacuity", "guard_red_detail", mut_detail)
        page.evaluate("() => { window.LinDetail && null; }")
        open_detail(page, EMPTY)   # re-render restores the honest DOM
        restored = read_flow(page)
        ok_res, res_detail = guard_empty_no_active(restored)
        check(ok_res, f"NON-VACUITY: {GUARD_NAME} is GREEN again after restore", res_detail)

        # ------------------------------------------------ NAVIGATION + RESPONSIVE
        print("\n" + "=" * 78)
        print("NAVIGATION — numbered rail, selection, responsive widths")
        print("=" * 78)
        page.set_viewport_size({"width": 1680, "height": 1400})
        open_detail(page, EMPTY)
        rail = page.evaluate(READ_RAIL2)
        fact("nav", "count", str(rail["count"]))
        fact("nav", "labels", json.dumps(rail["labels"]))
        fact("nav", "opacity", str(rail["opacity"]))
        fact("nav", "duplicates", str(rail["duplicates"]))
        fact("nav", "suspects", json.dumps(rail["suspects"]))
        fact("nav", "hit", json.dumps(rail["hit"]))
        check(rail["count"] >= 10, "NAV: at least 10 numbered controls are present",
              str(rail["count"]))
        check(rail["suspects"] == [], "NAV: no collapse/hide control",
              json.dumps(rail["suspects"]))
        check(all(h["hit"] for h in rail["hit"]),
              "NAV: every numbered control receives its own click (no overlay)",
              json.dumps([h for h in rail["hit"] if not h["hit"]])[:300])

        # click selection
        sel = page.evaluate(r"""() => {
          const btns = Array.from(document.querySelectorAll('.detail-secnav-btn'));
          const b = btns[3];
          b.click();
          const target = b.getAttribute('data-secnav-target');
          return { target };
        }""")
        after_now = page.evaluate(r"""() => {
          const b = Array.from(document.querySelectorAll('.detail-secnav-btn'))[3];
          return { selectedAttr: b.getAttribute('aria-current'),
                   selectedCls: b.classList.contains('selected') };
        }""")
        fact("nav", "immediately_after_click", json.dumps(after_now))
        check(after_now["selectedAttr"] == "true" and after_now["selectedCls"],
              "NAV: the click itself marks its control selected, without waiting on the "
              "scroll-spy", json.dumps(after_now))
        page.wait_for_timeout(2600)
        after = page.evaluate(r"""(target) => {
          const btns = Array.from(document.querySelectorAll('.detail-secnav-btn'));
          const b = btns[3];
          const sec = document.getElementById('section-' + target);
          return {
            selectedAttr: b.getAttribute('aria-current'),
            selectedCls: b.classList.contains('selected'),
            activeCls: b.classList.contains('active'),
            sectionOpen: !!sec && sec.classList.contains('open'),
            selectedCount: document.querySelectorAll('.detail-secnav-btn[aria-current="true"]').length,
          };
        }""", sel["target"])
        fact("nav", "after_click", json.dumps(after))
        check(after["selectedAttr"] == "true",
              "NAV: and it is still the selected control once the smooth scroll has settled",
              json.dumps(after))
        check(after["selectedCount"] == 1,
              "NAV: exactly one control is selected", str(after["selectedCount"]))
        check(after["sectionOpen"],
              "NAV: the clicked control's section is opened/selected")
        # SELECTED must not be ACTIVE: on the empty project, selecting a category must not
        # light anything in the Signal Flow.
        selflow = read_flow(page)
        ok, detail = guard_empty_no_active(selflow)
        check(ok, f"NAV: {GUARD_NAME} still holds while a category is SELECTED", detail)

        for w, name in WIDTHS:
            page.set_viewport_size({"width": w, "height": 1000})
            page.wait_for_timeout(800)
            r = page.evaluate(READ_RAIL2)
            fact("nav-" + name, "count", str(r["count"]))
            fact("nav-" + name, "display", str(r["display"]))
            fact("nav-" + name, "reachable_hits", str(sum(1 for h in r["hit"] if h["hit"])))
            fact("nav-" + name, "suspects", json.dumps(r["suspects"]))
            check(r["count"] >= 10 and r["display"] != "none",
                  f"NAV {name} ({w}px): the numbered rail is present and displayed",
                  f"count={r['count']} display={r['display']}")
            check(all(h["hit"] for h in r["hit"]),
                  f"NAV {name} ({w}px): every control is reachable, nothing overlays it",
                  json.dumps([h for h in r["hit"] if not h["hit"]])[:200])
            page.screenshot(path=str(ROOT / "code_audit" /
                                     f"run23_{r16.LABEL}_nav-{name}.png"))
        page.set_viewport_size({"width": 1680, "height": 1400})

        fact("browser", "page_errors", json.dumps(errors[:5]))
        b.close()

    r16.write_facts()
    print(f"\nRESULT: {r16.PASSED}/{r16.PASSED + r16.FAILED} checks passed")


if __name__ == "__main__":
    try:
        main_drive()
    except Exception:
        r16.write_facts()
        raise
