#!/usr/bin/env python3
"""
RUN 24. "AN EMPTY PROJECT MUST LOOK EMPTY ON THE SIGNAL FLOW DIAGRAM."

Drives the REAL served Project Detail page in a REAL headless Chromium against a throwaway
SQLite database, on an EMPTY project and on a COMPUTED project, and reads back the shipped
markers for the four items the owner named:

  1. an empty project must read as EMPTY, not as a caption above a full picture;
  2. the registered-but-inactive document marker must be visually distinct from an active one;
  3. the header module count must match the registry;
  4. the obsolete `◀ | ▶` paging control beneath the section navigator must be gone.

IT ASSERTS ON SHIPPED MARKERS, NOT ON PROSE. Visual mass is measured as the number of
*rendered* SVG shapes and *rendered* link paths inside the diagram surface, read from the DOM
with getComputedStyle where a CSS rule could hide something; activity is read from the
`data-active` attribute the implementation writes and from the `lnf-glow-*` filter reference,
the `.lnf-active` class and the `.lnf-flow-*` animation classes. Nothing here re-implements
the production predicate, and nothing asserts the defect's own sentence.

WEBGL IS DISABLED. This driver never needs a composited GL frame; the swiftshader path costs
~61 s per reload here (Run 22 / the post-Run-22 correction measured it) and this one reads DOM
state only.

Run:
    DATABASE_URL=sqlite:///... SESSION_SECRET=... PYTHONIOENCODING=utf-8 \
        python tools/drive_run24_empty_project_diagram.py [--baseline]

`--baseline` records the pre-change reading and does NOT assert the post-change acceptance,
so the same instrument produces the before and the after.
"""
from __future__ import annotations

import csv
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

r16.PORT = 8241
r16.BASE = f"http://127.0.0.1:{r16.PORT}"
r16.ADMIN = "r24-browser-admin"
r16.EMPTY = "PRJ-R24-EMPTY"
r16.FULL = "PRJ-R24-FULL"
r16.ONEDOC = "PRJ-R24-ONEDOC"

EMPTY, FULL, ONEDOC = r16.EMPTY, r16.FULL, r16.ONEDOC
check, fact, post, open_detail, server_state = (
    r16.check, r16.fact, r16.post, r16.open_detail, r16.server_state)

BASELINE = "--baseline" in sys.argv
LABEL = os.environ.get("RUN24_LABEL", "baseline" if BASELINE else "after")

# --------------------------------------------------------------------------- DOM readers

# WHAT "VISUAL MASS" MEANS HERE, MEASURED NOT ESTIMATED. `drawnShapes` and `drawnPaths` count
# only geometry that is actually rendered: an element whose own computed display is none, whose
# computed visibility is hidden, or which sits inside a subtree hidden by either, is not
# counted. That is the property the owner's complaint is about ("renders a dense
# active-looking picture anyway") and it cannot be satisfied by prose.
READ_SURFACE = r"""
() => {
  const c = document.querySelector('.detail-neural-flow');
  if (!c) return { present: false };
  const shown = (el) => {
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
      const cs = getComputedStyle(n);
      if (cs.display === 'none' || cs.visibility === 'hidden') return false;
      if (n === c) break;
    }
    return true;
  };
  const svg = c.querySelector('svg');
  const out = {
    present: true,
    svgPresent: !!svg,
    svgShown: !!svg && shown(svg),
    // The explicit control that reveals the full architecture, and the empty-state panel.
    emptyPanel: !!c.querySelector('.lnf-empty'),
    emptyPanelText: (() => { const e = c.querySelector('.lnf-empty');
      return e ? e.innerText.replace(/\s+/g, ' ').trim() : null; })(),
    revealControl: (() => { const b = c.querySelector('.lnf-reveal');
      return b ? { text: b.innerText.trim(), expanded: b.getAttribute('aria-expanded'),
                   controls: b.getAttribute('aria-controls') } : null; })(),
    summary: (() => { const s = c.querySelector('.lnf-summary');
      return s ? s.innerText.replace(/\s+/g, ' ').trim() : null; })(),
    legend: (() => { const l = c.querySelector('.lnf-legend');
      return l ? l.innerText.replace(/\s+/g, ' ').trim() : null; })(),
  };
  if (!svg) {
    out.drawnShapes = 0; out.drawnPaths = 0; out.headers = []; out.activeNodes = 0;
    out.glowNodes = 0; out.docGlowNodes = 0; out.verdictGlowNodes = 0; out.pulseNodes = 0;
    out.activeCls = 0; out.animated = 0; out.staticPaths = 0; out.brightNodes = 0;
    out.brightList = []; out.docRows = []; out.opacityTiers = {}; out.prjTexts = [];
    return out;
  }
  const nodes = svg.querySelector('#lnf-nodes');
  // SCOPED TO #lnf-nodes. The baseline read counted the two full-panel background rects and
  // the six arrowhead-marker polygons inside <defs> as "bright nodes" at opacity 0.75/1. Those
  // are chrome, not nodes, and a guard that counts them can never go green. Node metrics read
  // the node layer only; `drawnShapes`/`drawnPaths` below are the whole rendered surface,
  // because visual MASS is what item 1 is about.
  const shapes = Array.from(nodes ? nodes.querySelectorAll('circle,rect,polygon') : [])
    .filter(shown);
  const allShapes = Array.from(svg.querySelectorAll('circle,rect,polygon')).filter(shown);
  const paths = Array.from(svg.querySelectorAll('path')).filter(shown);
  const info = shapes.map(el => ({
    fill: (el.getAttribute('fill') || '').toLowerCase(),
    op: parseFloat(el.getAttribute('opacity') || '1'),
    filter: el.getAttribute('filter') || '',
    active: el.getAttribute('data-active'),
    tag: el.tagName.toLowerCase(),
  }));
  const glow = info.filter(n => /lnf-glow-/.test(n.filter));
  out.drawnShapes = allShapes.length;
  out.drawnNodeShapes = shapes.length;
  out.drawnPaths = paths.length;
  out.headers = Array.from(svg.querySelectorAll('text'))
    .filter(t => parseFloat(t.getAttribute('y')) < 34 && t.getAttribute('font-weight') === '700')
    .map(t => t.textContent.trim());
  out.activeNodes = svg.querySelectorAll('[data-active="true"]').length;
  out.glowNodes = glow.length;
  out.docGlowNodes = glow.filter(n => /DocOn/.test(n.filter)).length;
  out.verdictGlowNodes = glow.filter(n => !/DocOn/.test(n.filter)).length;
  out.pulseNodes = nodes ? nodes.querySelectorAll('.lnf-red-pulse').length : 0;
  out.activeCls = svg.querySelectorAll('.lnf-active').length;
  out.animated = svg.querySelectorAll('.lnf-flow-a,.lnf-flow-b,.lnf-flow-c,.lnf-flow-fb').length;
  out.staticPaths = svg.querySelectorAll('.lnf-static').length;
  out.brightNodes = info.filter(n => n.op >= 0.7).length;
  out.brightList = info.filter(n => n.op >= 0.7).map(n => n.tag + ':' + n.fill + ':' + n.op).slice(0, 40);
  const tiers = {};
  info.forEach(n => { const k = n.op.toFixed(2); tiers[k] = (tiers[k] || 0) + 1; });
  out.opacityTiers = tiers;
  const prj = svg.querySelector('#lnf-prj');
  out.prjTexts = prj ? Array.from(prj.querySelectorAll('text')).map(t => t.textContent.trim()) : [];
  // THE DOCUMENT COLUMN, ROW BY ROW, read by pairing each row rect with its own label text.
  // The three deliberately-absent types are identified by their LABEL, not by an index.
  const rows = [];
  if (nodes) {
    Array.from(nodes.querySelectorAll('g[data-kind="document"]')).forEach(g => {
      const sh = g.querySelector('circle,rect,polygon');
      const t = g.querySelector('text');
      if (!sh || !t) return;
      rows.push({ label: t.textContent.trim(), tag: sh.tagName.toLowerCase(),
                  fill: (sh.getAttribute('fill') || '').toLowerCase(),
                  op: parseFloat(sh.getAttribute('opacity') || '1'),
                  filter: sh.getAttribute('filter') || '',
                  active: sh.getAttribute('data-active'),
                  state: sh.getAttribute('data-state') });
    });
  }
  out.docRows = rows;
  return out;
}
"""

# THE PAGING CONTROL. Searched for by glyph, by accessible name, by class shape and by
# id shape, over the WHOLE document, and only counting elements the browser actually lays out.
READ_PAGER = r"""
() => {
  const arrows = /[◀▶◂▸‹›❮❯«»]/;
  const nav = document.getElementById('detail-secnav');
  // SCOPED TO INTERACTIVE ELEMENTS, plus anything carrying a pager-shaped class or id.
  // The baseline read matched the three decorative arrowheads in the diagram's own legend
  // (the flow-class key renders &#9656;), which are inert <span>s and not controls. A guard
  // that fails on the legend can never go green and would have been the sixteenth vacuous
  // guard in this programme. NV-3 injects a REAL control and proves this still fires.
  const all = Array.from(document.querySelectorAll(
    'button,a,[role="button"],[role="link"],[tabindex],input,select,' +
    '[class*="nav-page"],[class*="secnav-"],[class*="pager"],[id*="pager"]'));
  const hits = all.filter(el => {
    const t = (el.childElementCount === 0 ? (el.textContent || '') : '').trim();
    const a = ((el.getAttribute && (el.getAttribute('aria-label') || '')) + ' ' +
               (el.getAttribute && (el.getAttribute('title') || ''))).toLowerCase();
    const cls = String(el.className && el.className.baseVal !== undefined
                 ? el.className.baseVal : (el.className || '')).toLowerCase();
    const id = String(el.id || '').toLowerCase();
    const glyph = arrows.test(t);
    const named = /\b(prev|next|previous|page)\b/.test(a) ||
                  /nav-page|secnav-(page|toggle|collapse|hide|prev|next)|section-pager/.test(cls + ' ' + id);
    if (!glyph && !named) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  }).map(el => ({ text: (el.textContent || '').trim().slice(0, 24),
                  cls: String(el.className && el.className.baseVal !== undefined
                        ? el.className.baseVal : (el.className || '')),
                  id: el.id || '' }));
  return { count: hits.length, hits: hits.slice(0, 20),
           navPresent: !!nav,
           navButtons: nav ? nav.querySelectorAll('.detail-secnav-btn').length : 0,
           navSelected: nav ? Array.from(nav.querySelectorAll('.detail-secnav-btn'))
             .filter(b => b.getAttribute('aria-current') === 'true')
             .map(b => b.textContent.trim()) : [] };
}
"""

# Every place on the OPEN detail page that states a project-module count. Read separately
# from the registry probe because it must be evaluated with a project actually open: the first
# version of this driver read it at page load, found nothing, and would have reported an empty
# list as agreement had it not been written to require a non-empty one.
READ_BADGES = r"""
() => Array.from(document.querySelectorAll('.collapse-badge'))
        .map(e => e.textContent.trim())
        .filter(t => /\d+\s*registered/i.test(t))
"""

READ_REGISTRY = r"""
() => {
  const all = window.LIN_CATEGORIES || [];
  const proj = all.filter(c => !(c && (c.level === 'portfolio' || c.portfolioLevel)));
  const mods = [];
  proj.forEach(c => (c.modules || []).forEach(m => mods.push(m)));
  return {
    allCats: all.length,
    allModules: all.reduce((n, c) => n + ((c.modules || []).length), 0),
    projCats: proj.length,
    projModules: mods.length,
    // The one value the extraction model SUPPLIES rather than the analytical server
    // computing it, identified by its method class, which is what the server keys on.
    supplied: mods.filter(m => m.method_class === 'Doc_Risk_Cat4').map(m => m.name),
  };
}
"""

FACTS: list[list[str]] = []


def rec(state: str, name: str, value) -> None:
    FACTS.append([state, name, str(value)])
    fact(state, name, str(value))


# --------------------------------------------------------------------------- guards

GUARD_EMPTY = "GUARD_EMPTY_PROJECT_READS_EMPTY"
GUARD_MARKER = "GUARD_INACTIVE_DOC_MARKER_DISTINCT_FROM_ACTIVE"
GUARD_COUNT = "GUARD_HEADER_COUNT_MATCHES_REGISTRY"
GUARD_PAGER = "GUARD_NO_PAGING_CONTROL"

# The three types the document set's creator confirms are deliberately absent, by the LABEL
# the page actually renders (signals.js DOC_TYPE_LABEL), established by reading the baseline
# DOM rather than assumed: the third one ships as "Test & Commissioning Report".
ABSENT_TYPES = ("Past Performance Report", "Historical Project Data",
                "Test & Commissioning Report")


def guard_empty_reads_empty(s: dict) -> tuple[bool, str]:
    """
    RED when an empty project renders anything that reads as activity, OR when the full
    architecture is drawn without the participant having asked for it.

    Both halves are the owner's acceptance: "the absence is the dominant impression rather
    than a caption above a full picture". A diagram that is merely dim still puts ~96 module
    dots, ~11 category dots and every configured link on screen.
    """
    bad = []
    for k in ("docGlowNodes", "verdictGlowNodes", "pulseNodes", "activeCls", "animated",
              "brightNodes", "activeNodes"):
        if s.get(k):
            bad.append(f"{k}={s[k]}")
    if s.get("drawnShapes"):
        bad.append(f"drawnShapes={s['drawnShapes']}")
    if s.get("drawnPaths"):
        bad.append(f"drawnPaths={s['drawnPaths']}")
    if not s.get("emptyPanel"):
        bad.append("emptyPanel=absent")
    if not s.get("revealControl"):
        bad.append("revealControl=absent")
    return (not bad), ", ".join(bad)


def guard_marker_distinct(s: dict) -> tuple[bool, str]:
    """
    RED when a deliberately-absent document type renders in the same visual state as an
    uploaded one. Compares the SHIPPED attributes of the rows themselves.
    """
    rows = s.get("docRows") or []
    absent = [r for r in rows if r["label"] in ABSENT_TYPES]
    if len(absent) != 3:
        return False, f"expected 3 registered-not-active rows, found {len(absent)}: " + \
                      json.dumps([r['label'] for r in absent])
    live = [r for r in rows if r.get("active") == "true"]
    bad = []
    for r in absent:
        if r.get("active") != "false":
            bad.append(f"{r['label']} data-active={r.get('active')}")
        if "lnf-glow" in (r.get("filter") or ""):
            bad.append(f"{r['label']} carries a glow filter")
        if r["op"] >= 0.7:
            bad.append(f"{r['label']} opacity={r['op']}")
        for l in live:
            if r["fill"] == l["fill"] and abs(r["op"] - l["op"]) < 0.01:
                bad.append(f"{r['label']} is indistinguishable from active {l['label']}")
    return (not bad), ", ".join(bad)


# --------------------------------------------------------------------------- main

def write_facts() -> None:
    out = ROOT / "code_audit" / f"run24_empty_project_diagram_{LABEL}.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["state", "observation", "value"])
        w.writerows(FACTS)
    print(f"\nwrote {out}")


def surface(page, state: str, reveal: bool = False) -> dict:
    """Read the diagram surface, settling until two consecutive reads agree."""
    if reveal:
        page.evaluate("""() => { const b = document.querySelector('.lnf-reveal');
                                 if (b) b.click(); }""")
        page.wait_for_timeout(1500)
    prev = page.evaluate(READ_SURFACE)
    for _ in range(12):
        page.wait_for_timeout(800)
        cur = page.evaluate(READ_SURFACE)
        if json.dumps(cur, sort_keys=True) == json.dumps(prev, sort_keys=True):
            prev = cur
            break
        prev = cur
    for k in ("svgPresent", "svgShown", "emptyPanel", "drawnShapes", "drawnPaths",
              "activeNodes", "docGlowNodes", "verdictGlowNodes", "brightNodes", "pulseNodes",
              "activeCls", "animated", "staticPaths"):
        rec(state, k, prev.get(k))
    rec(state, "headers", " | ".join(prev.get("headers") or []))
    rec(state, "opacity_tiers", json.dumps(prev.get("opacityTiers") or {}, sort_keys=True))
    rec(state, "bright_list", json.dumps(prev.get("brightList") or []))
    rec(state, "empty_panel_text", prev.get("emptyPanelText"))
    rec(state, "reveal_control", json.dumps(prev.get("revealControl")))
    rec(state, "summary", prev.get("summary"))
    rec(state, "legend", prev.get("legend"))
    for r in (prev.get("docRows") or []):
        if r["label"] in ABSENT_TYPES or r.get("active") == "true":
            rec(state, "docrow:" + r["label"], json.dumps(r, sort_keys=True))
    return prev


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
    for pid in (EMPTY, FULL):
        st = server_state(pm, pid, 1)
        for k in ("live_row", "modules", "categories", "project_status"):
            if k in st:
                rec("server:" + pid, k, st[k])

    with sync_playwright() as pw:
        errors: list[str] = []
        b = pw.chromium.launch(executable_path=r16.SHELL,
                               args=["--disable-webgl", "--disable-gpu", "--no-sandbox"])
        page = b.new_page(viewport={"width": 1680, "height": 1400})
        page.set_default_timeout(60000)
        page.set_default_navigation_timeout(60000)
        page.on("pageerror", lambda e: errors.append(str(e)))
        for pattern in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                        "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
            page.route(pattern, lambda r: r.abort())
        page.goto(r16.BASE + "/", wait_until="domcontentloaded")
        page.evaluate("tok => sessionStorage.setItem('og-session-token', tok)", pm)
        page.goto(r16.BASE + "/", wait_until="domcontentloaded")
        page.add_style_tag(content="*,*::before,*::after{transition:none!important}")
        page.wait_for_timeout(8000)

        # ---------------------------------------------------------- the registry itself
        reg = page.evaluate(READ_REGISTRY)
        for k, v in reg.items():
            rec("registry", k, json.dumps(v) if isinstance(v, list) else v)

        # ---------------------------------------------------------- EMPTY, as first shown
        print("\n" + "=" * 78)
        print("STATE A — empty project, exactly as the participant first sees it")
        print("=" * 78)
        open_detail(page, EMPTY)
        a = surface(page, "A-empty-as-shown")
        page.screenshot(path=str(ROOT / "code_audit" / f"run24_{LABEL}_A-empty.png"),
                        full_page=False)
        pager_a = page.evaluate(READ_PAGER)
        rec("A-empty-as-shown", "pager", json.dumps(pager_a, sort_keys=True))

        # ---------------------------------------------------------- EMPTY, revealed
        print("\n" + "=" * 78)
        print("STATE A2 — empty project after the participant asks for the architecture")
        print("=" * 78)
        a2 = surface(page, "A2-empty-revealed", reveal=not BASELINE)
        page.screenshot(path=str(ROOT / "code_audit" / f"run24_{LABEL}_A2-empty-revealed.png"))

        # ---------------------------------------------------------- COMPUTED
        print("\n" + "=" * 78)
        print("STATE C — computed project with documents")
        print("=" * 78)
        open_detail(page, FULL)
        c = surface(page, "C-computed")
        page.screenshot(path=str(ROOT / "code_audit" / f"run24_{LABEL}_C-computed.png"))
        pager_c = page.evaluate(READ_PAGER)
        rec("C-computed", "pager", json.dumps(pager_c, sort_keys=True))

        # ============================================================ ASSERTIONS
        print("\n" + "=" * 78)
        print("ACCEPTANCE")
        print("=" * 78)

        # ITEM 4 — the paging control.
        check(pager_a["count"] == 0 and pager_c["count"] == 0,
              f"{GUARD_PAGER}: no paging or collapse control is rendered on either project",
              json.dumps(pager_a["hits"] + pager_c["hits"]))
        # RUN 25, OWNER-DIRECTED CONTRACT CHANGE, 2026-08-14. This check used to assert the
        # section navigator was still present with its controls. The owner then ordered the
        # rail removed entirely, so the assertion is inverted; the standing browser guard for
        # the new contract is drive_run25_rail_removal.py.
        check(not pager_a["navPresent"] and pager_a["navButtons"] == 0,
              "the section navigator rail is gone, per the owner's 2026-08-14 instruction",
              json.dumps(pager_a))

        # ITEM 3 — the header count against the registry read in the same browser.
        hdr = " | ".join(a2.get("headers") or c.get("headers") or [])
        expect_mod = f"{reg['projModules']} REGISTERED PROJECT MODULES"
        expect_cat = f"{reg['projCats']} REGISTERED CATEGORIES"
        check(expect_mod in hdr and expect_cat in hdr,
              f"{GUARD_COUNT}: the diagram headers carry the registry's own project-level "
              f"figures", f"want '{expect_mod}' and '{expect_cat}' in '{hdr}'")
        check(reg["supplied"] == ["Document Risk Score"],
              "exactly one project-level registry entry is a value the extraction model "
              "supplies rather than the analytical server computing it",
              json.dumps(reg["supplied"]))
        # THE FOUR-COUNTS HAZARD, checked rather than assumed. Every surface on this page that
        # states a project-module count must state the registry's figure, and the whole-taxonomy
        # figure quoted on the Knowledge page must reconcile to it.
        badges = page.evaluate(READ_BADGES)
        rec("registry", "badges_on_detail_page", json.dumps(badges))
        # THREE badges say "N registered" on this page: the Signal Flow section, the Signal
        # Web section (both project modules) and the categories section (project categories).
        # Every one must be a registry figure, and the module figure must actually appear --
        # a check that accepted "all of an empty list" would be the vacuity this programme
        # keeps finding, so a non-empty list carrying the module count is required.
        allowed = {str(reg["projModules"]), str(reg["projCats"])}
        check(len(badges) >= 2
              and all(b.split()[0] in allowed for b in badges)
              and any(b.split()[0] == str(reg["projModules"]) for b in badges),
              "every 'registered' badge on the detail page states a registry figure, and the "
              "project-module figure is among them", json.dumps(badges))
        summ = a2.get("summary") or c.get("summary") or ""
        check(f"{reg['projModules']} registered project modules" in summ
              and f"{reg['projCats']} registered categories" in summ,
              "the diagram's own summary sentence states the same figures as its headers",
              summ[:200])
        check(reg["allModules"] == reg["projModules"] + 5 and reg["allModules"] == 101,
              "the whole-taxonomy figure reconciles: project-level plus Portfolio Health",
              f"all={reg['allModules']} proj={reg['projModules']} cats={reg['allCats']}")

        # ITEM 2 — the registered-but-inactive marker, on the COMPUTED project where an
        # active row exists to compare against.
        ok, det = guard_marker_distinct(c)
        check(ok, f"{GUARD_MARKER}: on a computed project the deliberately-absent document "
                  f"types are visually distinct from the uploaded ones", det)

        # ITEM 1 — the empty project.
        if BASELINE:
            print("  (baseline run: the empty-project acceptance is recorded, not asserted)")
            okb, detb = guard_empty_reads_empty(a)
            print(f"  BASELINE {GUARD_EMPTY} would be: {'GREEN' if okb else 'RED'}  [{detb}]")
        else:
            ok, det = guard_empty_reads_empty(a)
            check(ok, f"{GUARD_EMPTY}: an empty project draws no active marker and no "
                      f"architecture until asked", det)
            check(bool(a.get("emptyPanel")) and not a.get("svgShown"),
                  "the empty project shows a short statement instead of the diagram",
                  f"panel={a.get('emptyPanel')} svgShown={a.get('svgShown')}")
            check((a2.get("drawnShapes") or 0) > 100 and (a2.get("drawnPaths") or 0) > 100,
                  "the full architecture is still available behind the explicit control",
                  f"shapes={a2.get('drawnShapes')} paths={a2.get('drawnPaths')}")
            ok2, det2 = guard_empty_reads_empty(a2)
            check(not ok2 and "drawnShapes=" in det2,
                  "and the guard distinguishes the revealed state from the empty one "
                  "(so it is not simply always green)", det2)
            check((a2.get("activeNodes") or 0) == 0 and (a2.get("animated") or 0) == 0,
                  "even revealed, the empty project's architecture carries no activity",
                  f"active={a2.get('activeNodes')} animated={a2.get('animated')}")
            # The computed project must be the opposite in every respect.
            check((c.get("activeNodes") or 0) > 0 and (c.get("animated") or 0) > 0
                  and not c.get("emptyPanel") and c.get("svgShown"),
                  "the computed project draws the diagram directly and carries activity",
                  f"active={c.get('activeNodes')} animated={c.get('animated')} "
                  f"panel={c.get('emptyPanel')} svgShown={c.get('svgShown')}")

            # ------------------------------------------------ NON-VACUITY MUTATIONS
            print("\n" + "=" * 78)
            print("NON-VACUITY — each guard must be proved capable of failing")
            print("=" * 78)
            open_detail(page, EMPTY)
            base = page.evaluate(READ_SURFACE)
            ok0, _ = guard_empty_reads_empty(base)
            check(ok0, f"NV baseline: {GUARD_EMPTY} is GREEN before any mutation")

            # NV-1: force the empty project's panel to reveal the architecture, with a node
            # made active. The injection is CONFIRMED by re-reading the DOM before judging.
            applied = page.evaluate(r"""() => {
              const b = document.querySelector('.lnf-reveal');
              if (b) b.click();
              return true;
            }""")
            page.wait_for_timeout(1200)
            inj = page.evaluate(r"""() => {
              const svg = document.querySelector('.detail-neural-flow svg');
              if (!svg) return { applied: false, why: 'no svg' };
              const n = svg.querySelector('#lnf-nodes circle');
              if (!n) return { applied: false, why: 'no node' };
              n.setAttribute('filter', 'url(#lnf-glow-Green)');
              n.setAttribute('opacity', '0.88');
              n.setAttribute('data-active', 'true');
              return { applied: svg.querySelectorAll('[data-active="true"]').length > 0 &&
                                /lnf-glow-Green/.test(n.getAttribute('filter') || ''),
                       activeNow: svg.querySelectorAll('[data-active="true"]').length };
            }""")
            check(bool(inj.get("applied")),
                  "NV-1 INJECTION TOOK EFFECT: one empty-project node now carries the shipped "
                  "active markers", json.dumps(inj))
            mut = page.evaluate(READ_SURFACE)
            okm, detm = guard_empty_reads_empty(mut)
            check(not okm and "activeNodes=" in detm and "verdictGlowNodes=" in detm,
                  f"NV-1: {GUARD_EMPTY} goes RED on the injected activity", detm)
            open_detail(page, EMPTY)
            page.wait_for_timeout(1500)
            restored = page.evaluate(READ_SURFACE)
            okr, detr = guard_empty_reads_empty(restored)
            check(okr, f"NV-1 RESTORE: {GUARD_EMPTY} is GREEN again on the rebuilt diagram",
                  detr)

            # NV-2: the marker guard. Force one deliberately-absent row into the active
            # visual state on the COMPUTED project and require the marker guard to fail.
            open_detail(page, FULL)
            page.wait_for_timeout(1500)
            cbase = page.evaluate(READ_SURFACE)
            okc, detc = guard_marker_distinct(cbase)
            check(okc, f"NV-2 baseline: {GUARD_MARKER} is GREEN before the mutation", detc)
            inj2 = page.evaluate(r"""(labels) => {
              const svg = document.querySelector('.detail-neural-flow svg');
              const live = Array.from(svg.querySelectorAll('#lnf-nodes g.lnf-nd'))
                .map(g => ({ g, r: g.querySelector('rect'), t: g.querySelector('text') }))
                .filter(x => x.r && x.t && x.r.getAttribute('data-active') === 'true');
              if (!live.length) return { applied: false, why: 'no active document row to copy' };
              const src = live[0];
              const target = Array.from(svg.querySelectorAll('#lnf-nodes g.lnf-nd'))
                .map(g => ({ g, r: g.querySelector('rect'), t: g.querySelector('text') }))
                .find(x => x.r && x.t && labels.indexOf(x.t.textContent.trim()) >= 0);
              if (!target) return { applied: false, why: 'no absent-type row found' };
              target.r.setAttribute('fill', src.r.getAttribute('fill'));
              target.r.setAttribute('opacity', src.r.getAttribute('opacity'));
              target.r.setAttribute('data-active', 'true');
              if (src.r.getAttribute('filter'))
                target.r.setAttribute('filter', src.r.getAttribute('filter'));
              return { applied: target.r.getAttribute('data-active') === 'true' &&
                                target.r.getAttribute('fill') === src.r.getAttribute('fill') &&
                                Math.abs(parseFloat(target.r.getAttribute('opacity')) -
                                         parseFloat(src.r.getAttribute('opacity'))) < 0.001,
                       copiedFrom: src.t.textContent.trim(),
                       onto: target.t.textContent.trim(),
                       fill: target.r.getAttribute('fill'),
                       opacity: target.r.getAttribute('opacity') };
            }""", list(ABSENT_TYPES))
            check(bool(inj2.get("applied")),
                  "NV-2 INJECTION TOOK EFFECT: a deliberately-absent row now carries an "
                  "uploaded row's exact fill and opacity", json.dumps(inj2))
            cmut = page.evaluate(READ_SURFACE)
            okm2, detm2 = guard_marker_distinct(cmut)
            check(not okm2, f"NV-2: {GUARD_MARKER} goes RED", detm2)
            open_detail(page, FULL)
            page.wait_for_timeout(1500)
            crest = page.evaluate(READ_SURFACE)
            okr2, detr2 = guard_marker_distinct(crest)
            check(okr2, f"NV-2 RESTORE: {GUARD_MARKER} is GREEN again", detr2)

            # NV-3: the pager guard. Insert a real ◀ | ▶ control under the navigator and
            # require the guard to see it.
            inj3 = page.evaluate(r"""() => {
              const nav = document.getElementById('detail-secnav');
              if (!nav || !nav.parentElement) return { applied: false, why: 'no navigator' };
              const d = document.createElement('div');
              d.id = 'nv3-pager';
              d.style.cssText = 'position:fixed;left:8px;top:300px;width:60px;height:20px;';
              d.innerHTML = '<button class="nav-page">◀</button>' +
                            '<button class="nav-page">▶</button>';
              nav.parentElement.appendChild(d);
              const r = d.getBoundingClientRect();
              return { applied: !!document.getElementById('nv3-pager') && r.width > 0 };
            }""")
            check(bool(inj3.get("applied")),
                  "NV-3 INJECTION TOOK EFFECT: a laid-out paging control exists in the DOM",
                  json.dumps(inj3))
            pmut = page.evaluate(READ_PAGER)
            check(pmut["count"] >= 2, f"NV-3: {GUARD_PAGER} goes RED", json.dumps(pmut["hits"]))
            page.evaluate("() => { const d = document.getElementById('nv3-pager'); "
                          "if (d) d.remove(); }")
            prest = page.evaluate(READ_PAGER)
            check(prest["count"] == 0, f"NV-3 RESTORE: {GUARD_PAGER} is GREEN again",
                  json.dumps(prest["hits"]))

            # NV-4: the count guard. Assert it is reading the header, by requiring a
            # deliberately wrong expectation to fail against the same string.
            wrong = f"{reg['projModules'] + 1} REGISTERED PROJECT MODULES"
            check(wrong not in hdr,
                  f"NV-4: {GUARD_COUNT} is discriminating (a figure one higher than the "
                  f"registry does NOT appear in the headers)", f"'{wrong}' in '{hdr}'")
            check(len(hdr) > 0 and "REGISTERED PROJECT MODULES" in hdr,
                  "NV-4: and the header string the count guard reads is really present", hdr)

            # ------------------------------------------------ RE-BASELINE
            print("\n" + "=" * 78)
            print("RE-BASELINE after every fault")
            print("=" * 78)
            open_detail(page, EMPTY)
            page.wait_for_timeout(1500)
            fin_a = page.evaluate(READ_SURFACE)
            oka, deta = guard_empty_reads_empty(fin_a)
            check(oka, f"FINAL: {GUARD_EMPTY} GREEN on the empty project", deta)
            open_detail(page, FULL)
            page.wait_for_timeout(1500)
            fin_c = page.evaluate(READ_SURFACE)
            okcf, detcf = guard_marker_distinct(fin_c)
            check(okcf, f"FINAL: {GUARD_MARKER} GREEN on the computed project", detcf)
            finp = page.evaluate(READ_PAGER)
            check(finp["count"] == 0, f"FINAL: {GUARD_PAGER} GREEN", json.dumps(finp["hits"]))

        check(not errors, "no uncaught page error while driving the diagram",
              json.dumps(errors[:5]))
        b.close()

    write_facts()
    print(f"\nRESULT: {r16.PASSED}/{r16.PASSED + r16.FAILED} checks passed")
    sys.exit(1 if r16.FAILED else 0)


if __name__ == "__main__":
    main_drive()
