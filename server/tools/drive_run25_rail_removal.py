#!/usr/bin/env python3
"""
RUN 25. "REMOVE THE LEFT RAIL, AND MAKE AN EMPTY PROJECT LOOK EMPTY."

OWNER-DIRECTED CONTRACT CHANGE, 2026-08-14. Earlier owner instructions said the numbered
Signal rail stays, and Runs 16, 23 and 24 built guards asserting its presence. The owner's
2026-08-14 instruction orders the LEFT RAIL REMOVED ENTIRELY: the numbered 1-to-10 list and
any paging control beneath it. This driver asserts the rail is ABSENT, at five viewport
widths, on the REAL served page in a REAL headless Chromium against a throwaway SQLite
database. The reversal is recorded in code_audit/run20_anti_fossilization_register.csv as a
contract change, not a fossilization.

It also re-verifies, with fresh browser evidence, the two things the owner's prompt names
that were ALREADY satisfied on arrival (measured by drive_run24_empty_project_diagram.py at
017c95e, 31/31): the empty-project gate merged at 26597e8 and the 96/11 header count.

WEBGL IS DISABLED: DOM state only (~288ms reload against ~61s with software GL).

Run:
    DATABASE_URL=sqlite:///... SESSION_SECRET=... PYTHONIOENCODING=utf-8 \
        python tools/drive_run25_rail_removal.py
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
import os
import pathlib
import sys
import threading
import time
import urllib.request

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

import tools.drive_run16_final_flow as r16  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]

r16.PORT = 8251
r16.BASE = f"http://127.0.0.1:{r16.PORT}"
r16.ADMIN = "r25-browser-admin"
r16.EMPTY = "PRJ-R25-EMPTY"
r16.FULL = "PRJ-R25-FULL"
r16.ONEDOC = "PRJ-R25-ONEDOC"

EMPTY, FULL = r16.EMPTY, r16.FULL
check, fact, open_detail = r16.check, r16.fact, r16.open_detail

LABEL = os.environ.get("RUN25_LABEL", "after")

# The five widths the owner's acceptance names: two desktop, one laptop, the 700px breakpoint
# boundary the old rail re-laid itself out at, and a phone.
WIDTHS = (1680, 1280, 1024, 700, 390)

# ------------------------------------------------------------------ DOM readers

# THE RAIL, read by every shipped marker the implementation ever used: the element id, the
# class family, and any fixed-position element hugging the left edge that contains three or
# more single-digit numbered buttons (so a re-implementation under a fresh name is still
# caught). Only elements the browser actually lays out count.
READ_RAIL = r"""
() => {
  const byId = document.getElementById('detail-secnav');
  const byCls = document.querySelectorAll('[class*="detail-secnav"]').length;
  const laid = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  // Structural sweep: any laid-out container with >= 3 buttons whose text is a bare 1-2 digit
  // number, fixed- or sticky-positioned. That is the rail's shape whatever it is called.
  const suspects = [];
  document.querySelectorAll('nav,div,aside,ul,ol').forEach(el => {
    if (!laid(el)) return;
    const cs = getComputedStyle(el);
    if (cs.position !== 'fixed' && cs.position !== 'sticky') return;
    const btns = Array.from(el.querySelectorAll('button'))
      .filter(b => /^\d{1,2}$/.test((b.textContent || '').trim()) && laid(b));
    if (btns.length >= 3) suspects.push({ id: el.id || '', cls: String(el.className || '').slice(0, 60),
                                          numbered: btns.length });
  });
  return { byIdPresent: !!byId, byClsCount: byCls, numberedRails: suspects };
}
"""

# THE PAGER, exactly as Run 24 read it: glyph or pager-shaped name, laid out only. The three
# decorative legend arrowheads (&#9656; spans) and CSS list bullets are not controls and are
# not matched.
READ_PAGER = r"""
() => {
  const arrows = /[◀▶◂▸‹›❮❯«»]/;
  const all = Array.from(document.querySelectorAll(
    'button,a,[role="button"],[role="link"],[tabindex],input,select,' +
    '[class*="nav-page"],[class*="secnav-"],[class*="pager"],[id*="pager"]'));
  const hits = all.filter(el => {
    const t = (el.childElementCount === 0 ? (el.textContent || '') : '').trim();
    const a = ((el.getAttribute('aria-label') || '') + ' ' + (el.getAttribute('title') || '')).toLowerCase();
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
                  cls: String(el.className || ''), id: el.id || '' }));
  return { count: hits.length, hits: hits.slice(0, 20) };
}
"""

# The Signal Flow surface, the subset of Run 24's reader this run re-verifies.
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
    svgShown: !!svg && shown(svg),
    emptyPanel: !!c.querySelector('.lnf-empty'),
    reveal: (() => { const b = c.querySelector('.lnf-reveal');
      return b ? { text: b.innerText.trim(), expanded: b.getAttribute('aria-expanded') } : null; })(),
    drawnShapes: 0, drawnPaths: 0, activeNodes: 0, animated: 0, headers: []
  };
  if (svg) {
    out.drawnShapes = Array.from(svg.querySelectorAll('circle,rect,polygon')).filter(shown).length;
    out.drawnPaths = Array.from(svg.querySelectorAll('path')).filter(shown).length;
    out.activeNodes = svg.querySelectorAll('[data-active="true"]').length;
    out.animated = svg.querySelectorAll('.lnf-flow-a,.lnf-flow-b,.lnf-flow-c,.lnf-flow-fb').length;
    out.headers = Array.from(svg.querySelectorAll('text'))
      .filter(t => parseFloat(t.getAttribute('y')) < 34 && t.getAttribute('font-weight') === '700')
      .map(t => t.textContent.trim());
  }
  return out;
}
"""

READ_REGISTRY = r"""
() => {
  const all = window.LIN_CATEGORIES || [];
  const proj = all.filter(c => !(c && (c.level === 'portfolio' || c.portfolioLevel)));
  return {
    allModules: all.reduce((n, c) => n + ((c.modules || []).length), 0),
    projCats: proj.length,
    projModules: proj.reduce((n, c) => n + ((c.modules || []).length), 0),
  };
}
"""

FACTS: list[list[str]] = []


def rec(state: str, name: str, value) -> None:
    FACTS.append([state, name, str(value)])
    fact(state, name, str(value))


def rail_guard(r: dict, p: dict) -> tuple[bool, str]:
    """RED when any shipped rail marker, any numbered-rail-shaped element, or any laid-out
    paging control exists on the page."""
    bad = []
    if r.get("byIdPresent"):
        bad.append("id=detail-secnav present")
    if r.get("byClsCount"):
        bad.append(f"detail-secnav classes={r['byClsCount']}")
    if r.get("numberedRails"):
        bad.append("numbered rail: " + json.dumps(r["numberedRails"]))
    if p.get("count"):
        bad.append("pager hits: " + json.dumps(p["hits"]))
    return (not bad), ", ".join(bad)


def write_facts() -> None:
    out = artifact_out(ROOT / "code_audit" / f"run25_rail_removal_{LABEL}.csv")
    with artifact_out(out).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["state", "observation", "value"])
        w.writerows(FACTS)
    print(f"\nwrote {out}")


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

        reg = page.evaluate(READ_REGISTRY)
        for k, v in reg.items():
            rec("registry", k, v)

        # ---------------------------------------------------- 1. THE RAIL IS ABSENT, 5 WIDTHS
        print("=" * 78)
        print("ITEM 1 — the rail is absent at every viewport width, empty AND computed")
        print("=" * 78)
        open_detail(page, EMPTY)
        page.wait_for_timeout(2000)
        for pid in (EMPTY, FULL):
            open_detail(page, pid)
            page.wait_for_timeout(2000)
            for w in WIDTHS:
                page.set_viewport_size({"width": w, "height": 1000})
                page.wait_for_timeout(600)
                r = page.evaluate(READ_RAIL)
                p = page.evaluate(READ_PAGER)
                ok, det = rail_guard(r, p)
                rec(f"{pid}@{w}", "rail_read", json.dumps(r, sort_keys=True))
                rec(f"{pid}@{w}", "pager_read", json.dumps(p, sort_keys=True))
                check(ok, f"RAIL ABSENT on {pid} at {w}px", det)
        page.set_viewport_size({"width": 1680, "height": 1400})
        page.wait_for_timeout(600)

        # The sections the rail used to target must still exist and still open without it.
        open_detail(page, EMPTY)
        page.wait_for_timeout(2000)
        secs = page.evaluate("""() => Array.from(document.querySelectorAll('.collapse-section'))
                                     .map(s => s.id)""")
        check(len(secs) >= 8, "the collapsible sections the rail used to list are all still "
              "on the page", json.dumps(secs))
        toggled = page.evaluate("""() => {
          const sec = document.querySelectorAll('.collapse-section')[2];
          if (!sec) return { ok: false };
          const head = sec.querySelector('.collapse-head,button,[role="button"]');
          const before = sec.classList.contains('open');
          if (head) head.click();
          return { ok: true, before, after: sec.classList.contains('open'), id: sec.id };
        }""")
        check(bool(toggled.get("ok")) and toggled.get("before") != toggled.get("after"),
              "a section still opens from its own header with the rail gone",
              json.dumps(toggled))

        # ---------------------------------------------------- 2. EMPTY LOOKS EMPTY (re-verify)
        print("\n" + "=" * 78)
        print("ITEM 2 — empty project and computed project, side by side (re-verification)")
        print("=" * 78)
        open_detail(page, EMPTY)
        page.wait_for_timeout(2500)
        a = page.evaluate(READ_SURFACE)
        for k in ("emptyPanel", "svgShown", "drawnShapes", "drawnPaths", "activeNodes",
                  "animated"):
            rec("A-empty", k, a.get(k))
        rec("A-empty", "reveal", json.dumps(a.get("reveal")))
        page.screenshot(path=artifact_out(str(ROOT / "code_audit" / f"run25_{LABEL}_empty_1680.png")))
        check(bool(a.get("emptyPanel")) and not a.get("svgShown")
              and a.get("drawnShapes") == 0 and a.get("drawnPaths") == 0
              and a.get("activeNodes") == 0 and a.get("animated") == 0
              and bool(a.get("reveal")),
              "the empty project leads with the statement and the explicit control; no shape, "
              "no path, no activity is rendered", json.dumps(a))
        page.evaluate("""() => { const b = document.querySelector('.lnf-reveal');
                                 if (b) b.click(); }""")
        page.wait_for_timeout(1500)
        a2 = page.evaluate(READ_SURFACE)
        for k in ("svgShown", "drawnShapes", "drawnPaths", "activeNodes", "animated"):
            rec("A2-empty-revealed", k, a2.get(k))
        check(a2.get("svgShown") and (a2.get("drawnShapes") or 0) > 100
              and (a2.get("activeNodes") or 0) == 0 and (a2.get("animated") or 0) == 0,
              "the full architecture is one click away and still carries no activity",
              json.dumps({k: a2.get(k) for k in ("drawnShapes", "drawnPaths", "activeNodes")}))

        open_detail(page, FULL)
        page.wait_for_timeout(2500)
        c = page.evaluate(READ_SURFACE)
        for k in ("emptyPanel", "svgShown", "drawnShapes", "drawnPaths", "activeNodes",
                  "animated"):
            rec("C-computed", k, c.get(k))
        rec("C-computed", "headers", " | ".join(c.get("headers") or []))
        page.screenshot(path=artifact_out(str(ROOT / "code_audit" / f"run25_{LABEL}_computed_1680.png")))
        check(not c.get("emptyPanel") and c.get("svgShown")
              and (c.get("activeNodes") or 0) > 0 and (c.get("animated") or 0) > 0,
              "the computed project draws the diagram directly and carries activity",
              json.dumps({k: c.get(k) for k in ("activeNodes", "animated", "emptyPanel")}))

        # ---------------------------------------------------- 3. THE COUNT (re-verify)
        hdr = " | ".join(c.get("headers") or [])
        check(f"{reg['projModules']} REGISTERED PROJECT MODULES" in hdr
              and f"{reg['projCats']} REGISTERED CATEGORIES" in hdr,
              "the diagram headers carry the registry's own figures at runtime", hdr)
        check(reg["projModules"] == 96 and reg["projCats"] == 11 and reg["allModules"] == 101,
              "and the registry evaluated in this browser holds 96 project modules in 11 "
              "categories, 101 whole-taxonomy", json.dumps(reg))
        check(f"{reg['projModules'] + 1} REGISTERED PROJECT MODULES" not in hdr,
              "count guard is discriminating: one-higher does not appear", hdr)

        # ---------------------------------------------------- NON-VACUITY
        print("\n" + "=" * 78)
        print("NON-VACUITY — each guard proved capable of failing, baseline rechecked after")
        print("=" * 78)
        open_detail(page, EMPTY)
        page.wait_for_timeout(2000)
        r0, p0 = page.evaluate(READ_RAIL), page.evaluate(READ_PAGER)
        ok0, det0 = rail_guard(r0, p0)
        check(ok0, "NV baseline: the rail guard is GREEN before any injection", det0)

        # NV-A: re-insert the removed rail, exactly as detail.js used to build it.
        injA = page.evaluate(r"""() => {
          const nav = document.createElement('nav');
          nav.id = 'detail-secnav';
          nav.className = 'detail-secnav';
          nav.style.cssText = 'position:fixed;left:12px;top:40%;z-index:55;display:flex;'
            + 'flex-direction:column;gap:8px;background:#111;padding:10px 6px;';
          for (let i = 1; i <= 10; i++) {
            const b = document.createElement('button');
            b.className = 'detail-secnav-btn';
            b.textContent = String(i);
            nav.appendChild(b);
          }
          document.body.appendChild(nav);
          const el = document.getElementById('detail-secnav');
          const rct = el.getBoundingClientRect();
          return { applied: !!el && el.querySelectorAll('button').length === 10
                            && rct.width > 0 && rct.height > 0 };
        }""")
        check(bool(injA.get("applied")),
              "NV-A INJECTION TOOK EFFECT: a laid-out 10-button rail with the shipped id and "
              "class exists in the DOM", json.dumps(injA))
        rA, pA = page.evaluate(READ_RAIL), page.evaluate(READ_PAGER)
        okA, detA = rail_guard(rA, pA)
        check(not okA and "detail-secnav" in detA and rA.get("numberedRails"),
              "NV-A: the rail guard goes RED, on the id, the class AND the numbered shape",
              detA)
        page.evaluate("() => document.getElementById('detail-secnav').remove()")
        rAr, pAr = page.evaluate(READ_RAIL), page.evaluate(READ_PAGER)
        okAr, detAr = rail_guard(rAr, pAr)
        check(okAr, "NV-A RESTORE: the rail guard is GREEN again", detAr)

        # NV-B: an anonymous numbered rail under a fresh name (no shipped marker at all).
        injB = page.evaluate(r"""() => {
          const d = document.createElement('div');
          d.id = 'totally-new-nav';
          d.style.cssText = 'position:fixed;left:8px;top:30%;';
          d.innerHTML = Array.from({length: 6}, (_, i) => '<button>' + (i + 1) + '</button>').join('');
          document.body.appendChild(d);
          const r = d.getBoundingClientRect();
          return { applied: r.width > 0 && d.querySelectorAll('button').length === 6 };
        }""")
        check(bool(injB.get("applied")),
              "NV-B INJECTION TOOK EFFECT: an unnamed numbered rail is laid out", json.dumps(injB))
        rB = page.evaluate(READ_RAIL)
        okB, detB = rail_guard(rB, page.evaluate(READ_PAGER))
        check(not okB and rB.get("numberedRails"),
              "NV-B: the structural sweep catches a rail under a fresh name", detB)
        page.evaluate("() => document.getElementById('totally-new-nav').remove()")
        okBr, detBr = rail_guard(page.evaluate(READ_RAIL), page.evaluate(READ_PAGER))
        check(okBr, "NV-B RESTORE: GREEN again", detBr)

        # NV-C: a real paging control.
        injC = page.evaluate(r"""() => {
          const d = document.createElement('div');
          d.id = 'nvc-pager';
          d.style.cssText = 'position:fixed;left:8px;top:300px;width:60px;height:20px;';
          d.innerHTML = '<button class="nav-page">◀</button>'
                      + '<button class="nav-page">▶</button>';
          document.body.appendChild(d);
          return { applied: !!document.getElementById('nvc-pager')
                            && d.getBoundingClientRect().width > 0 };
        }""")
        check(bool(injC.get("applied")),
              "NV-C INJECTION TOOK EFFECT: a laid-out paging control exists", json.dumps(injC))
        pC = page.evaluate(READ_PAGER)
        okC, detC = rail_guard(page.evaluate(READ_RAIL), pC)
        check(not okC and pC["count"] >= 2, "NV-C: the pager guard goes RED", detC)
        page.evaluate("() => document.getElementById('nvc-pager').remove()")
        okCr, detCr = rail_guard(page.evaluate(READ_RAIL), page.evaluate(READ_PAGER))
        check(okCr, "NV-C RESTORE: GREEN again", detCr)

        # NV-D: the empty-project guard, injected activity (Run 24's NV-1, re-proved here).
        page.evaluate("""() => { const b = document.querySelector('.lnf-reveal');
                                 if (b) b.click(); }""")
        page.wait_for_timeout(1200)
        injD = page.evaluate(r"""() => {
          const svg = document.querySelector('.detail-neural-flow svg');
          if (!svg) return { applied: false, why: 'no svg' };
          const n = svg.querySelector('#lnf-nodes circle');
          if (!n) return { applied: false, why: 'no node' };
          n.setAttribute('data-active', 'true');
          n.setAttribute('opacity', '0.88');
          return { applied: svg.querySelectorAll('[data-active="true"]').length > 0 };
        }""")
        check(bool(injD.get("applied")),
              "NV-D INJECTION TOOK EFFECT: an empty-project node carries the active marker",
              json.dumps(injD))
        mutD = page.evaluate(READ_SURFACE)
        check((mutD.get("activeNodes") or 0) > 0,
              "NV-D: the empty-project reader sees the injected activity (so its zeros above "
              "were measurements, not defaults)", json.dumps(mutD.get("activeNodes")))
        open_detail(page, EMPTY)
        page.wait_for_timeout(2000)
        fin = page.evaluate(READ_SURFACE)
        check(bool(fin.get("emptyPanel")) and (fin.get("activeNodes") or 0) == 0
              and fin.get("drawnShapes") == 0,
              "NV-D RESTORE: the rebuilt empty project is empty again", json.dumps(
                  {k: fin.get(k) for k in ("emptyPanel", "activeNodes", "drawnShapes")}))

        # ---------------------------------------------------- FINAL RE-BASELINE
        okF, detF = rail_guard(page.evaluate(READ_RAIL), page.evaluate(READ_PAGER))
        check(okF, "FINAL: the rail guard is GREEN on the empty project", detF)
        open_detail(page, FULL)
        page.wait_for_timeout(2000)
        okF2, detF2 = rail_guard(page.evaluate(READ_RAIL), page.evaluate(READ_PAGER))
        check(okF2, "FINAL: and on the computed project", detF2)
        page.set_viewport_size({"width": 390, "height": 1000})
        page.wait_for_timeout(800)
        page.screenshot(path=artifact_out(str(ROOT / "code_audit" / f"run25_{LABEL}_computed_390.png")))
        okF3, detF3 = rail_guard(page.evaluate(READ_RAIL), page.evaluate(READ_PAGER))
        check(okF3, "FINAL: and at phone width", detF3)

        check(not errors, "no uncaught page error while driving the page",
              json.dumps(errors[:5]))
        b.close()

    write_facts()
    print(f"\nRESULT: {r16.PASSED}/{r16.PASSED + r16.FAILED} checks passed")
    sys.exit(1 if r16.FAILED else 0)


if __name__ == "__main__":
    main_drive()
