#!/usr/bin/env python3
"""
RUN 26. SITEWIDE COUNTS, SIGNAL FLOW WIRING, AND EMPTY-PROJECT RENDERING.

Drives the REAL served application in a REAL headless Chromium against a throwaway SQLite
database, on an EMPTY project and a COMPUTED project side by side, and reads back:

  1. every user-visible analytical count, as RENDERED TEXT, on the pages that carry one;
  2. the rendered Signal Flow edge inventory, read from the `data-edge-*` attributes the
     renderer writes, and compared against code_audit/signal_flow_authoritative_edges.csv,
     which was extracted from the architecture master and the module registry BEFORE any
     renderer code was read;
  3. the rendered colour of every distinct element type on an EMPTY project, including the
     state behind the "Show the registered architecture" control;
  4. what every derived category renders when its upstream set is empty.

THE ORACLE IS THE AUTHORITATIVE EDGE CSV, NOT THE DIAGRAM. Nothing here re-implements a
production predicate and nothing asserts a shipped sentence verbatim.

WEBGL IS DISABLED: this driver reads DOM state only, and the swiftshader path costs ~61 s per
reload in this container against ~288 ms without it.

Run:
    DATABASE_URL=sqlite:///... SESSION_SECRET=... PYTHONIOENCODING=utf-8 \
        python tools/drive_run26_counts_wiring_empty.py [--baseline]

`--baseline` records the pre-change reading and does not assert the post-change acceptance.
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

# The port is settable so the non-vacuity campaign can run several sandboxed copies of this
# driver without them colliding on one listener.
r16.PORT = int(os.environ.get("RUN26_PORT", "8261"))
r16.BASE = f"http://127.0.0.1:{r16.PORT}"
r16.ADMIN = "r26-browser-admin"
r16.EMPTY = "PRJ-R26-EMPTY"
r16.FULL = "PRJ-R26-FULL"
r16.ONEDOC = "PRJ-R26-ONEDOC"

EMPTY, FULL, ONEDOC = r16.EMPTY, r16.FULL, r16.ONEDOC
check, fact, post, open_detail = r16.check, r16.fact, r16.post, r16.open_detail

BASELINE = "--baseline" in sys.argv
LABEL = os.environ.get("RUN26_LABEL", "baseline" if BASELINE else "after")

AUTH_EDGES = ROOT / "code_audit" / "signal_flow_authoritative_edges.csv"

# The five analytical colours the legend explains, plus the not-relevant marker. Read from the
# page at runtime rather than copied here: see READ_PALETTE.
READ_PALETTE = "() => JSON.parse(JSON.stringify(window.LIN_STATUS_COLORS || {}))"

# THE REGISTRY, AT RUNTIME. Derived from the taxonomy the application actually loaded, not from
# a literal and not from a document. `projectLevelCategories` is the application's own scope
# filter; the counts below are recomputed from its output.
READ_REGISTRY = r"""
() => {
  const all = window.LIN_CATEGORIES || [];
  const proj = window.projectLevelCategories ? window.projectLevelCategories()
             : all.filter(c => !(c && c.level === 'portfolio'));
  const portf = all.filter(c => !proj.includes(c));
  const n = (cs) => cs.reduce((a, c) => a + ((c && c.modules) || []).length, 0);
  const byGroup = {};
  all.forEach(c => { byGroup[c.group] = (byGroup[c.group] || 0) + ((c.modules || []).length); });
  return {
    totalCategories: all.length,
    projectCategories: proj.length,
    portfolioCategories: portf.length,
    totalModules: n(all),
    projectModules: n(proj),
    portfolioModules: n(portf),
    byGroup,
    projectCatNames: proj.map(c => c.name),
    projectCatIds: proj.map(c => c.id),
  };
}
"""

# THE SIGNAL FLOW SURFACE. Colours are read as the RENDERED attribute values on the shipped
# elements, and every element is filtered through a computed-style visibility walk so a hidden
# subtree cannot be counted as rendered.
READ_FLOW = r"""
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
    emptyPanel: !!c.querySelector('.lnf-empty'),
    revealControl: (() => { const b = c.querySelector('.lnf-reveal');
      return b ? { text: b.innerText.trim(), expanded: b.getAttribute('aria-expanded') } : null; })(),
    summary: (() => { const s = c.querySelector('.lnf-summary');
      return s ? s.innerText.replace(/\s+/g, ' ').trim() : null; })(),
    legend: (() => { const l = c.querySelector('.lnf-legend');
      return l ? l.innerText.replace(/\s+/g, ' ').trim() : null; })(),
    legendSwatches: Array.from(c.querySelectorAll('.lnf-legend span[style]'))
      .map(s => ({ text: (s.parentElement && s.parentElement.innerText || '').trim(),
                   bg: getComputedStyle(s).backgroundColor,
                   borderTop: getComputedStyle(s).borderTopColor,
                   hasBorder: getComputedStyle(s).borderTopWidth !== '0px' }))
      .filter(s => s.text),
    svgShown: !!svg && shown(svg),
  };
  if (!svg || !shown(svg)) {
    Object.assign(out, { headers: [], nodes: [], edges: [], animated: 0, glows: 0,
                         activeCls: 0, drawnShapes: 0, drawnPaths: 0, prjTexts: [] });
    return out;
  }
  const nodes = svg.querySelector('#lnf-nodes');
  out.headers = Array.from(svg.querySelectorAll('text'))
    .filter(t => parseFloat(t.getAttribute('y')) < 34 && t.getAttribute('font-weight') === '700')
    .map(t => t.textContent.trim());
  // Every rendered node, by the kind the renderer declares in the DOM.
  out.nodes = Array.from(nodes ? nodes.querySelectorAll('g[data-kind]') : [])
    .filter(shown)
    .map(g => {
      const sh = g.querySelector('circle,rect,polygon');
      const t = g.querySelector('text');
      if (!sh) return null;
      return {
        kind: g.getAttribute('data-kind'),
        name: t ? t.textContent.trim() : '',
        shape: sh.tagName.toLowerCase(),
        fill: (sh.getAttribute('fill') || '').toLowerCase(),
        stroke: (sh.getAttribute('stroke') || 'none').toLowerCase(),
        opacity: parseFloat(sh.getAttribute('opacity') || '1'),
        filter: sh.getAttribute('filter') || '',
        active: sh.getAttribute('data-active') || g.getAttribute('data-active') || '',
        state: sh.getAttribute('data-state') || '',
        status: sh.getAttribute('data-status') || g.getAttribute('data-status') || '',
      };
    }).filter(Boolean);
  // Every rendered edge, read from the attributes the renderer writes. An edge the renderer
  // does not name is still counted, as an unnamed edge, so a missing attribute cannot hide one.
  const paths = Array.from(svg.querySelectorAll('path')).filter(shown);
  out.drawnPaths = paths.length;
  out.drawnShapes = Array.from(svg.querySelectorAll('circle,rect,polygon')).filter(shown).length;
  out.edges = paths.map(p => ({
    type: p.getAttribute('data-edge-type') || '',
    src: p.getAttribute('data-edge-src') || '',
    dst: p.getAttribute('data-edge-dst') || '',
    stroke: (p.getAttribute('stroke') || '').toLowerCase(),
    opacity: parseFloat(p.getAttribute('opacity') || '1'),
    cls: p.getAttribute('class') || '',
  }));
  out.animated = svg.querySelectorAll(
    '.lnf-flow-a,.lnf-flow-b,.lnf-flow-c,.lnf-flow-fb').length;
  out.glows = Array.from(svg.querySelectorAll('[filter]'))
    .filter(e => /lnf-glow-/.test(e.getAttribute('filter') || '')).filter(shown).length;
  out.activeCls = svg.querySelectorAll('.lnf-active').length;
  const prj = svg.querySelector('#lnf-prj');
  out.prjTexts = prj ? Array.from(prj.querySelectorAll('text')).map(t => t.textContent.trim()) : [];
  return out;
}
"""

# USER-VISIBLE COUNTS, AS RENDERED TEXT. Reads innerText off the laid-out page, so a template
# that reads correctly in source and renders wrongly is caught.
READ_PAGE_TEXT = r"""
(sel) => {
  const el = document.querySelector(sel);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  if (!(r.width > 0 && r.height > 0)) return null;
  return el.innerText.replace(/\s+/g, ' ').trim();
}
"""

COUNT_PHRASE = r"""
(txt) => {
  if (!txt) return [];
  const out = [];
  const re = /([^.]*?\b\d{2,3}\b[^.]*?\.)/g;
  let m;
  while ((m = re.exec(txt)) !== null) out.push(m[1].trim());
  return out;
}
"""


def authoritative_edges() -> list[dict]:
    if not AUTH_EDGES.exists():
        return []
    with AUTH_EDGES.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def rendered_edge_set(flow: dict) -> set[tuple[str, str, str]]:
    return {(e["type"], e["src"], e["dst"]) for e in flow.get("edges", [])
            if e.get("type") and e.get("src") and e.get("dst")}


def authoritative_edge_set(rows: list[dict]) -> set[tuple[str, str, str]]:
    """Only the rows the architecture master actually establishes are oracle rows.

    A row whose authority_source records SILENCE is deliberately NOT in the oracle: the report
    carries it as an unresolved mapping instead. Turning a silence into an expected edge is the
    circular step this run exists to avoid.
    """
    out = set()
    for r in rows:
        if (r.get("authority_status") or "").strip().upper() != "ESTABLISHED":
            continue
        out.add((r["edge_type"].strip(), r["upstream_name"].strip(),
                 r["downstream_name"].strip()))
    return out


FACTS_CSV: list[list[str]] = []


def rec(state: str, name: str, value) -> None:
    FACTS_CSV.append([state, name, str(value)])
    fact(state, name, str(value))


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
    auth_rows = authoritative_edges()
    auth = authoritative_edge_set(auth_rows)
    rec("oracle", "authoritative_rows", len(auth_rows))
    rec("oracle", "authoritative_established_edges", len(auth))
    rec("oracle", "authoritative_unresolved_rows",
        sum(1 for r in auth_rows
            if (r.get("authority_status") or "").upper() != "ESTABLISHED"))

    with sync_playwright() as pw:
        errors: list[str] = []
        b = pw.chromium.launch(
            executable_path=r16.SHELL,
            args=["--no-sandbox", "--disable-gpu"])
        page = b.new_page(viewport={"width": 1680, "height": 1500})
        page.set_default_timeout(60000)
        page.set_default_navigation_timeout(60000)
        page.on("pageerror", lambda e: errors.append(str(e)))
        for pattern in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                        "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
            page.route(pattern, lambda r: r.abort())
        page.goto(r16.BASE + "/", wait_until="domcontentloaded")
        page.evaluate("tok => sessionStorage.setItem('og-session-token', tok)", pm)
        page.goto(r16.BASE + "/", wait_until="domcontentloaded")
        page.add_style_tag(content="*,*::before,*::after{transition:none!important;"
                                   "animation:none!important}")
        page.wait_for_timeout(8000)

        # ------------------------------------------------------------------ wrong-app tell
        srcs = page.evaluate(
            "() => Array.from(document.scripts).map(s => (s.src||'').split('/').pop())")
        pages = page.evaluate("() => document.querySelectorAll('.page').length")
        rec("app", "script_names", json.dumps(sorted(x for x in srcs if x)[:40]))
        rec("app", "page_sections", pages)
        check(pages > 0 and "api.js" not in srcs and "boot.js" not in srcs,
              "the served application is this repository's app, not the Demo app",
              f"pages={pages} srcs={srcs[:6]}")

        # ------------------------------------------------------------------ registry at runtime
        reg = page.evaluate(READ_REGISTRY)
        for k, v in reg.items():
            rec("registry", k, json.dumps(v) if isinstance(v, (list, dict)) else v)
        check(reg["totalModules"] == 101, "runtime taxonomy holds 101 registered modules",
              str(reg["totalModules"]))
        check(reg["projectModules"] == 96, "runtime taxonomy holds 96 project modules",
              str(reg["projectModules"]))
        check(reg["portfolioModules"] == 5, "runtime taxonomy holds 5 Portfolio Health modules",
              str(reg["portfolioModules"]))
        check(reg["projectModules"] + reg["portfolioModules"] == reg["totalModules"],
              "the rendered registry satisfies 96 + 5 = 101")
        check(reg["totalCategories"] == 12 and reg["projectCategories"] == 11,
              "12 registered categories, 11 of them project level",
              f"{reg['totalCategories']}/{reg['projectCategories']}")

        palette = page.evaluate(READ_PALETTE)
        rec("palette", "status_colors", json.dumps(palette, sort_keys=True))

        # ------------------------------------------------------------------ explanatory pages
        # THE PAGES ARE `section.page[data-page=...]` AND ARE SHOWN BY REMOVING `hidden`, not by
        # an `active` class. The first attempt at this sweep toggled a class the markup does not
        # use, every page read as NOT PRESENT, and the sweep silently found nothing -- which is
        # the same shape of failure as a template that reads correctly and renders wrongly.
        for name, sel in (("landing", 'section.page[data-page="portfolio"]'),
                          ("handbook-about", 'section.page[data-page="handbook"]'),
                          ("project-detail", 'section.page[data-page="detail"]'),
                          ("project", 'section.page[data-page="project"]'),
                          ("training", 'section.page[data-page="training"]')):
            try:
                page.evaluate("s => { const p = document.querySelector(s);"
                              " if (p) { p.hidden = false; p.style.display = ''; } }", sel)
                page.wait_for_timeout(800)
                txt = page.evaluate(READ_PAGE_TEXT, sel)
            except Exception as exc:            # pragma: no cover - reported, not swallowed
                txt = None
                rec(name, "read_error", str(exc))
            if txt is None:
                rec(name, "rendered", "NOT PRESENT")
                continue
            phrases = page.evaluate(COUNT_PHRASE, txt)
            keep = [p for p in phrases
                    if any(w in p.lower() for w in
                           ("computation", "module", "categor", "method", "analytic",
                            "target", "assessed", "registered", "portfolio"))]
            rec(name, "count_phrases", json.dumps(keep[:12]))

        # THE KNOWLEDGE LIBRARY builds into #knowledge-root lazily. Its count sentences are the
        # ones this run rewrote, so they are read as RENDERED TEXT rather than as source.
        try:
            page.evaluate("""() => {
              const t = document.querySelector('[data-hb-tab="methods"], .hb-tab');
              if (t) t.click();
              if (window.LinKnowledge && LinKnowledge.renderKnowledgePage) LinKnowledge.renderKnowledgePage();
            }""")
            page.wait_for_timeout(2500)
            kn = page.evaluate("() => { const r = document.getElementById('knowledge-root');"
                               " return r ? r.innerText.replace(/\\s+/g,' ').trim() : null; }")
        except Exception as exc:
            kn = None
            rec("knowledge", "read_error", str(exc))
        if kn:
            phrases = page.evaluate(COUNT_PHRASE, kn)
            keep = [p for p in phrases
                    if any(w in p.lower() for w in
                           ("registered module", "analytical server computes", "computation",
                            "portfolio level", "project level"))]
            rec("knowledge", "rendered_chars", len(kn))
            rec("knowledge", "count_phrases", json.dumps(keep[:12]))
            check("101 registered modules" in kn and "96 of the 101" in kn,
                  "KNOWLEDGE: the rendered library states the registry total and both scopes",
                  json.dumps(keep[:4]))
            check("the analytical server computes 100" in kn
                  or "computes 100 of the 101" in kn,
                  "KNOWLEDGE: and states the computed count as a scope of the registry",
                  json.dumps(keep[:4]))
        else:
            rec("knowledge", "rendered", "NOT PRESENT")

        # ------------------------------------------------------------------ EMPTY project
        open_detail(page, EMPTY)
        empty_collapsed = page.evaluate(READ_FLOW)
        rec("empty-collapsed", "empty_panel", empty_collapsed.get("emptyPanel"))
        rec("empty-collapsed", "reveal_control", json.dumps(empty_collapsed.get("revealControl")))
        rec("empty-collapsed", "svg_shown", empty_collapsed.get("svgShown"))
        rec("empty-collapsed", "drawn_shapes", empty_collapsed.get("drawnShapes"))
        rec("empty-collapsed", "drawn_paths", empty_collapsed.get("drawnPaths"))
        check(empty_collapsed.get("emptyPanel") is True,
              "EMPTY: the diagram is replaced by a statement of absence")
        check(empty_collapsed.get("svgShown") is False,
              "EMPTY: no diagram geometry is rendered before the reader asks for it")

        # THE REVEALED ARCHITECTURE. Addition B: its elements must still be neutral.
        page.evaluate("() => { const b = document.querySelector('.lnf-reveal');"
                      " if (b) b.click(); }")
        page.wait_for_timeout(2000)
        empty = page.evaluate(READ_FLOW)
        rec("empty-revealed", "svg_shown", empty.get("svgShown"))
        rec("empty-revealed", "headers", " | ".join(empty.get("headers") or []))
        rec("empty-revealed", "summary", empty.get("summary"))
        rec("empty-revealed", "legend", empty.get("legend"))
        rec("empty-revealed", "project_status_node", " ".join(empty.get("prjTexts") or []))
        rec("empty-revealed", "animated_edges", empty.get("animated"))
        rec("empty-revealed", "glows", empty.get("glows"))
        rec("empty-revealed", "active_class", empty.get("activeCls"))
        rec("empty-revealed", "drawn_shapes", empty.get("drawnShapes"))
        rec("empty-revealed", "drawn_paths", empty.get("drawnPaths"))
        check(empty.get("svgShown") is True,
              "EMPTY: the registered architecture is available behind the explicit control")

        # ---- the empty-project rendered-colour table
        analytical = {str(palette.get(k, "")).lower()
                      for k in ("Green", "Yellow", "Amber", "Red", "Complete", "NotRelevant")
                      if palette.get(k)}
        rows = []
        non_grey_nodes = []
        for n in empty.get("nodes", []):
            allowed = n["fill"] not in analytical
            rows.append([LABEL, "node", n["kind"], n["name"][:40], n["shape"], n["fill"],
                         n["stroke"], n["opacity"], n["filter"], n["state"],
                         "yes" if allowed else "no", "PASS" if allowed else "FAIL"])
            if not allowed:
                non_grey_nodes.append(f"{n['kind']}:{n['name'][:24]}:{n['fill']}")
        non_grey_edges = []
        for e in empty.get("edges", []):
            allowed = e["stroke"] not in analytical
            rows.append([LABEL, "edge", e["type"] or "(unnamed)",
                         (e["src"] + "->" + e["dst"])[:40], "path", e["stroke"], "", e["opacity"],
                         "", e["cls"], "yes" if allowed else "no", "PASS" if allowed else "FAIL"])
            if not allowed:
                non_grey_edges.append(f"{e['type'] or '(unnamed)'}:{e['src']}->{e['dst']}:{e['stroke']}")
        out = artifact_out(ROOT / "code_audit" / f"run26_empty_project_colours_{LABEL}.csv")
        with out.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["label", "element_class", "element_type", "element_name", "shape",
                        "rendered_fill_or_stroke", "rendered_stroke", "rendered_opacity",
                        "filter", "state_or_class", "allowed_on_empty_project", "verdict"])
            w.writerows(rows)
        print(f"        . wrote {out}")

        docs = [n for n in empty.get("nodes", []) if n["kind"] == "document"]
        mods = [n for n in empty.get("nodes", []) if n["kind"] == "module"]
        cats = [n for n in empty.get("nodes", []) if n["kind"] == "category"]
        rec("empty-revealed", "documents_total", len(docs))
        rec("empty-revealed", "modules_total", len(mods))
        rec("empty-revealed", "categories_total", len(cats))
        rec("empty-revealed", "non_grey_nodes", json.dumps(non_grey_nodes[:20]))
        rec("empty-revealed", "non_grey_node_count", len(non_grey_nodes))
        rec("empty-revealed", "non_grey_edges", json.dumps(non_grey_edges[:20]))
        rec("empty-revealed", "non_grey_edge_count", len(non_grey_edges))

        if not BASELINE:
            check(len(non_grey_nodes) == 0,
                  "EMPTY: no node renders an analytical colour, revealed architecture included",
                  json.dumps(non_grey_nodes[:8]))
            check(len(non_grey_edges) == 0,
                  "EMPTY: no edge renders an analytical colour",
                  json.dumps(non_grey_edges[:8]))
            check(empty.get("animated") == 0, "EMPTY: no edge is animated",
                  str(empty.get("animated")))
            check(empty.get("glows") == 0, "EMPTY: no element carries an active glow",
                  str(empty.get("glows")))
            check(empty.get("activeCls") == 0, "EMPTY: nothing is marked active",
                  str(empty.get("activeCls")))
            check(len(docs) > 0 and all(d["state"] != "registered-not-active" for d in docs),
                  "EMPTY: no document row renders the not-relevant marker",
                  json.dumps([d["name"] for d in docs if d["state"] == "registered-not-active"]))

        # ---- legend reconciliation: every rendered colour must be a legend colour
        legend_colours = set()
        for s in empty.get("legendSwatches", []):
            for key in ("bg", "borderTop"):
                v = (s.get(key) or "").strip().lower()
                if v and v not in ("rgba(0, 0, 0, 0)", "transparent"):
                    legend_colours.add(v)
        rec("empty-revealed", "legend_swatch_colours", json.dumps(sorted(legend_colours)))

        # ---- derived categories on an empty upstream set
        # The derived categories, from the ESTABLISHED category-to-category rows only. A SILENT
        # row's downstream is a placeholder, not a category, and including it would make the
        # completeness check below unsatisfiable.
        derived_names = {r["downstream_name"].strip() for r in auth_rows
                         if r["edge_type"].strip() == "CATEGORY -> CATEGORY"
                         and r["authority_status"].strip().upper() == "ESTABLISHED"}

        def bare(name: str) -> str:
            """The category's own name, without the group prefix the rendered label carries.

            The rendered label is "B \u00b7 Signal Synthesis". Matching the inventory's plain
            name against that whole string silently classified EVERY category as not derived,
            so the derived-category table read all PASS for the wrong reason and the NV-E fault
            went red only because the unrelated colour guard fired. That is exactly the failure
            mode the instruction names, and it is fixed here rather than accepted.
            """
            return name.split("\u00b7")[-1].strip()

        derived_rows = []
        for cnode in cats:
            is_derived = bare(cnode["name"]) in derived_names
            coloured = cnode["fill"] in analytical
            derived_rows.append([bare(cnode["name"]), "yes" if is_derived else "no",
                                 cnode["fill"], cnode["opacity"], cnode["status"],
                                 "FAIL" if (is_derived and coloured) else "PASS"])
        out2 = artifact_out(ROOT / "code_audit" / f"run26_derived_categories_empty_{LABEL}.csv")
        with artifact_out(out2).open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["category", "derived", "rendered_fill", "rendered_opacity",
                        "rendered_status", "verdict"])
            w.writerows(derived_rows)
        print(f"        . wrote {out2}")
        n_derived = sum(1 for r in derived_rows if r[1] == "yes")
        rec("empty-revealed", "derived_categories_identified", n_derived)
        check(n_derived == len(derived_names),
              "EMPTY: every derived category the inventory names is found among the rendered "
              "categories, so the derived-category verdict is not vacuous",
              f"{n_derived} of {len(derived_names)}")
        bad_derived = [r[0] for r in derived_rows if r[5] == "FAIL"]
        rec("empty-revealed", "derived_categories_with_status_colour", json.dumps(bad_derived))
        if not BASELINE:
            check(not bad_derived,
                  "EMPTY: no derived category renders a computed-status colour",
                  json.dumps(bad_derived))
            hdr = " | ".join(empty.get("headers") or [])
            check("0 ESTIMABLE NOW" in hdr,
                  "EMPTY: no category reads as estimable", hdr)
            check("NOT ESTIMABLE" in hdr,
                  "EMPTY: the project status reads not estimable", hdr)

        # ------------------------------------------------------------------ edge inventory
        rendered = rendered_edge_set(empty)
        unnamed = [e for e in empty.get("edges", [])
                   if not (e.get("type") and e.get("src") and e.get("dst"))]
        rec("wiring", "rendered_named_edges", len(rendered))
        rec("wiring", "rendered_unnamed_paths", len(unnamed))
        missing = sorted(auth - rendered)
        fabricated = sorted(e for e in rendered - auth
                            if (e[0], e[2], e[1]) not in auth)
        wrong_dir = sorted(e for e in rendered - auth if (e[0], e[2], e[1]) in auth)
        rec("wiring", "missing_edges", json.dumps(missing[:20]))
        rec("wiring", "missing_edge_count", len(missing))
        rec("wiring", "fabricated_edges", json.dumps(fabricated[:20]))
        rec("wiring", "fabricated_edge_count", len(fabricated))
        rec("wiring", "wrong_direction_edges", json.dumps(wrong_dir[:20]))
        rec("wiring", "wrong_direction_edge_count", len(wrong_dir))
        out3 = artifact_out(ROOT / "code_audit" / f"run26_rendered_edges_{LABEL}.csv")
        with artifact_out(out3).open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["edge_type", "upstream", "downstream", "in_authoritative_inventory"])
            for e in sorted(rendered):
                w.writerow([e[0], e[1], e[2], "yes" if e in auth else "no"])
        print(f"        . wrote {out3}")
        if not BASELINE:
            check(len(missing) == 0, "WIRING: every established architectural edge is rendered",
                  json.dumps(missing[:6]))
            check(len(fabricated) == 0, "WIRING: no rendered edge is absent from the inventory",
                  json.dumps(fabricated[:6]))
            check(len(wrong_dir) == 0, "WIRING: no rendered edge runs against the architecture",
                  json.dumps(wrong_dir[:6]))
            check(len(unnamed) == 0, "WIRING: every rendered edge names itself in the DOM",
                  str(len(unnamed)))

        # ------------------------------------------------------------------ COMPUTED project
        open_detail(page, FULL)
        full = page.evaluate(READ_FLOW)
        rec("computed", "svg_shown", full.get("svgShown"))
        rec("computed", "headers", " | ".join(full.get("headers") or []))
        rec("computed", "summary", full.get("summary"))
        rec("computed", "project_status_node", " ".join(full.get("prjTexts") or []))
        rec("computed", "animated_edges", full.get("animated"))
        rec("computed", "glows", full.get("glows"))
        rec("computed", "drawn_shapes", full.get("drawnShapes"))
        rec("computed", "drawn_paths", full.get("drawnPaths"))
        full_hdr = " | ".join(full.get("headers") or [])
        rec("computed", "header_module_count_phrase",
            next((h for h in (full.get("headers") or []) if "MODULE" in h), ""))
        check("96 REGISTERED PROJECT MODULES" in full_hdr,
              "COMPUTED: the Signal Flow header reports the project registry scope",
              full_hdr)
        check("11 REGISTERED CATEGORIES" in full_hdr,
              "COMPUTED: and the project category scope", full_hdr)
        check(full.get("emptyPanel") is False,
              "COMPUTED: a project with evidence shows the diagram directly")

        # Every colour rendered on the computed project must be explained by the legend.
        comp_colours = {n["fill"] for n in full.get("nodes", []) if n["fill"]}
        rec("computed", "rendered_node_fills", json.dumps(sorted(comp_colours)))
        rec("computed", "rendered_edge_count", len(rendered_edge_set(full)))
        comp_missing = sorted(auth - rendered_edge_set(full))
        comp_fab = sorted(e for e in rendered_edge_set(full) - auth
                          if (e[0], e[2], e[1]) not in auth)
        rec("computed", "missing_edge_count", len(comp_missing))
        rec("computed", "fabricated_edge_count", len(comp_fab))
        if not BASELINE:
            check(len(comp_missing) == 0 and len(comp_fab) == 0,
                  "COMPUTED: the same edge inventory holds on a project with evidence",
                  json.dumps((comp_missing[:4], comp_fab[:4])))

        rec("browser", "page_errors", json.dumps(errors[:5]))
        check(not errors, "no uncaught page error during the run", json.dumps(errors[:3]))
        b.close()

    out = artifact_out(ROOT / "code_audit" / f"run26_browser_facts_{LABEL}.csv")
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["state", "observation", "value"])
        w.writerows(FACTS_CSV)
    print(f"\nwrote {out}")
    print(f"\nRESULT: {r16.PASSED}/{r16.PASSED + r16.FAILED} checks passed")


if __name__ == "__main__":
    try:
        main_drive()
    except Exception:
        import traceback
        traceback.print_exc()
        print("\nRESULT: 0/1 checks passed")
        sys.exit(1)
    sys.exit(0 if r16.FAILED == 0 else 1)
