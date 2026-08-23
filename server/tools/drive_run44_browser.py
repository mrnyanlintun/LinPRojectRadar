#!/usr/bin/env python3
"""
RUN 44, SECTION 5 ITEMS 7 AND 14. BROWSER VERIFICATION OF THE REPAIRED SURFACES.

Serves the REAL application from the repository root against a throwaway migrated SQLite database
in the session scratchpad, drives the real Chromium headless shell against it, and reads every
claim OUT OF THE RENDERED DOM rather than out of the source.

WHAT IT GUARDS AGAINST FIRST. `preview_start` resolves launch.json from DEng\\Demo and silently
serves a different application; the tell is api.js and boot.js in document.scripts with zero
`.page` sections in the DOM, against the 7 this application has. That is checked before anything
else is measured, and the working directory of the session is printed.

THIS DRIVER CHANGES NOTHING. It serves, renders, observes and records. Production Postgres is
never configured or contacted.

Run:
    DATABASE_URL=sqlite:///<throwaway> SESSION_SECRET=... PYTHONIOENCODING=utf-8 \\
        python tools/drive_run44_browser.py
"""
from __future__ import annotations

import json
import logging
import os
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
PORT = 8412
BASE = f"http://127.0.0.1:{PORT}"

RESULTS: list[tuple[bool, str, str]] = []


def check(ok, label, detail=""):
    RESULTS.append((bool(ok), label, str(detail)))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   [{detail}]" if detail else ""))
    return bool(ok)


PROBE = r"""
() => {
  const out = {};
  out.pageSections = document.querySelectorAll(".page").length;
  out.scripts = Array.from(document.scripts).map(s => s.src.split('/').pop());
  out.demoTell = out.scripts.filter(s => s === 'api.js' || s === 'boot.js');

  // ---- the taxonomy the page actually loaded
  const cats = window.LIN_CATEGORIES || [];
  out.catCount = cats.length;
  out.moduleCount = cats.reduce((n, c) => n + ((c && c.modules) || []).length, 0);
  out.portfolioCats = cats.filter(c => c && c.level === 'portfolio')
                          .map(c => ({ id: c.id, modules: (c.modules || []).length }));

  // ---- SECTION 4.4: the Portfolio Health flyout, rendered by the REAL renderer
  out.flyout = null;
  return out;
}
"""


def main() -> int:
    import uvicorn
    from playwright.sync_api import sync_playwright
    import app.main as main_app

    print(f"browser session cwd: {os.getcwd()}")
    print(f"repository root:     {ROOT}")
    print(f"DATABASE_URL:        {os.environ.get('DATABASE_URL')}")

    config = uvicorn.Config(main_app.app, host="127.0.0.1", port=PORT, log_level="critical")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(120):
        try:
            urllib.request.urlopen(BASE + "/readyz", timeout=2).read()
            break
        except Exception:
            time.sleep(0.5)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=SHELL,
                                     args=["--use-gl=swiftshader", "--no-sandbox"])
        page = browser.new_page(viewport={"width": 1680, "height": 1400})
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        for pattern in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                        "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
            page.route(pattern, lambda r: r.abort())
        page.goto(BASE + "/", wait_until="domcontentloaded")
        page.add_style_tag(content="*,*::before,*::after{transition:none!important;"
                                   "animation:none!important}")
        page.wait_for_timeout(6000)
        page.evaluate("() => { window.confirm = () => false; }")

        print()
        print("=" * 90)
        print("0. THE APPLICATION UNDER TEST IS THE RIGHT ONE")
        print("=" * 90)
        base = page.evaluate(PROBE)
        check(base["pageSections"] == 7,
              "the DOM carries 7 .page sections, which is what this application has",
              base["pageSections"])
        check(not base["demoTell"],
              "and neither api.js nor boot.js is in document.scripts, so DEng\\Demo is not what "
              "is being served", str(base["demoTell"]))

        print()
        print("=" * 90)
        print("1. THE TAXONOMY THE PAGE LOADED")
        print("=" * 90)
        check(base["catCount"] == 12 and base["moduleCount"] == 63,
              "12 categories and 63 modules in service, read from the running page",
              f"{base['catCount']} / {base['moduleCount']}")
        check(base["portfolioCats"] and all(c["modules"] == 0 for c in base["portfolioCats"]),
              "the portfolio-level category is present and carries zero modules",
              json.dumps(base["portfolioCats"]))

        print()
        print("=" * 90)
        print("2. SECTION 4.4 -- THE PORTFOLIO HEALTH FLYOUT, RENDERED BY ITS OWN RENDERER")
        print("=" * 90)
        # deepdive.js is loaded on the deep-dive route, not on the landing page. It is loaded
        # here FROM THE SERVER, so the bytes executed are the bytes the application serves.
        if not page.evaluate("() => !!window.LinDeepDive"):
            page.add_script_tag(url="/assets/js/deepdive.js")
            page.wait_for_timeout(500)
            print("    (deepdive.js loaded from the server on demand: it is not on the landing "
                  "route)")
        check(page.evaluate("() => !!window.LinDeepDive"),
              "the served deepdive.js is loaded and exposes its renderer")
        # RUN 52 FIX. Run 51 DELETED the Portfolio Health flyout and its renderer
        # `LinDeepDive.renderCat8Health` from the served bytes (see
        # test_run44_participant_defect_fixes.py:506-566). The block that stood here called that
        # renderer and would raise `TypeError: window.LinDeepDive.renderCat8Health is not a
        # function` on every run since. This driver is superseded by drive_run51_browser.py; it is
        # KEPT (not deleted) because it is the run-44 audit record, and it is FIXED so it runs. The
        # three checks it made about the flyout's wording cannot be made against a surface that no
        # longer exists, so they are REPLACED -- not deleted -- by the check that actually holds
        # now: the renderer is gone from the served export and the surface is unreachable.
        exports = page.evaluate("() => Object.keys(window.LinDeepDive || {}).sort()")
        print(f"    window.LinDeepDive exports: {exports}")
        check("renderCat8Health" not in exports,
              "SUPERSEDED BY RUN 51: renderCat8Health is gone from the served deepdive.js export, "
              "so the Portfolio Health flyout this section used to render is unreachable",
              str(exports))

        print()
        print("=" * 90)
        print("3. SECTIONS 4.2 AND 4.3 -- THE SIGNALS PANEL, RENDERED BY ITS OWN RENDERER")
        print("=" * 90)
        panel = page.evaluate(r"""
          () => {
            const mk = (si) => {
              const saved = window.LinResults;
              window.LinResults = { rowFor: () => ({ signal_inputs: si }),
                                    hasResult: () => true, clear: () => {} };
              const root = document.createElement('div');
              document.body.appendChild(root);
              try { window.LinSignals.renderSignalsPanel(root, { id: 'PRJ-B', events: [] }); }
              finally { window.LinResults = saved; }
              // The panel body lives inside a collapsed <details>, whose innerText is empty
              // until it is opened. Read the rendered ROWS instead, by their own cells.
              const d = root.querySelector('details'); if (d) d.open = true;
              const rows = Array.from(root.querySelectorAll('tr.ds-row')).map(tr =>
                Array.from(tr.children).map(td => td.textContent.trim()).join(' | '));
              const html = root.innerHTML;
              const text = root.innerText;
              root.remove();
              return { html, text, rows };
            };
            const base = { bac: 5874620, ev: 1046735, ac: 857930, pv: 1085600,
                           cpi: 1.22, spi: 0.964 };
            return {
              absent: mk(Object.assign({}, base, { docRiskScore: null })),
              zero:   mk(Object.assign({}, base, { docRiskScore: 0 })),
              real:   mk(Object.assign({}, base, { docRiskScore: 0.46 }))
            };
          }
        """)
        def prow(name, label):
            return [r for r in panel[name]["rows"] if r.startswith(label)]
        for name in ("absent", "zero", "real"):
            print(f"    docRiskScore {name}:")
            for label in ("Document-risk", "CPI", "SPI"):
                for r in prow(name, label):
                    print(f"      {r}")
        check("computed" in panel["real"]["html"] and "ds-computed" in panel["real"]["html"],
              "CPI and SPI carry the computed mark on the rendered panel")
        check(panel["real"]["html"].count("ds-computed") == 2,
              "exactly two rows are marked computed",
              panel["real"]["html"].count("ds-computed"))
        check("Extracted signal inputs" not in panel["real"]["text"],
              "and the panel heading no longer asserts that every row beneath it was extracted")
        _abs = prow("absent", "Document-risk")
        check(len(_abs) == 1 and "\u2014" in _abs[0] and "0.00" not in _abs[0],
              "an absent document-risk score renders as a dash on the panel, not as 0.00",
              str(_abs))
        # The panel formats with fmtNum, so a genuine zero reads "0" here rather than "0.00" --
        # the Executive Brief's key drivers are where "0.00" appears. What matters on BOTH
        # surfaces is the same: an absence renders as an absence and a zero renders as a value.
        _zero = prow("zero", "Document-risk")
        check(len(_zero) == 1 and "\u2014" not in _zero[0] and "0" in _zero[0]
              and "extracted" in _zero[0],
              "and a genuine stored zero renders as the value 0 with its extracted mark, not as "
              "a dash", str(_zero))
        _cpi = prow("real", "CPI")
        check(len(_cpi) == 1 and "computed" in _cpi[0] and "extracted" not in _cpi[0],
              "the rendered CPI row says computed and does not say extracted", str(_cpi))

        print()
        print("=" * 90)
        print("4. SECTION 4.1 -- THE PROJECT DETAIL PAGE, RENDERED BY ITS OWN RENDERER")
        print("=" * 90)
        prov = page.evaluate(r"""
          () => {
            // THE REAL ROUTE. The stored row is primed through LinResults.prime and carried on
            // the project as storedResult, which is how the loader that fetched it does it --
            // taxonomy.js resolves every status through its own rowFor over exactly that.
            const cat = (window.LIN_CATEGORIES || [])[0];
            const mk = (catStatus, modStatuses) => {
              const row = {
                signal_inputs: { bac: 5874620, cpi: 1.22, spi: 0.964, docRiskScore: null },
                category_statuses: { [cat.num]: { status: catStatus } },
                module_results: (cat.modules || []).map((m, i) => ({
                  module_id: m.num,
                  status_color: modStatuses[i % modStatuses.length],
                  evidence_metric: 'metric ' + m.num
                }))
              };
              // The evidence metric the expandable panel shows comes from the legacy signal
              // array, matched by method_class. Supplied so the panel has something to expand;
              // without it the page correctly renders no "why?" control at all.
              const p = { id: 'PRJ-B44', name: 'Browser Harness', status: catStatus,
                          signalInputs: row.signal_inputs, events: [], history: [],
                          simulationSignals: { signal_array: (cat.modules || []).map(m => (
                            { method_class: m.method_class,
                              evidence_metric: 'metric for ' + m.num })) },
                          storedResult: row };
              window.LIN_PROJECTS = [p];
              window.LinResults.prime('PRJ-B44', row);
              window.LinDetail.render('PRJ-B44');
              const el = document.querySelector('.det-prov .det-prov-line');
              // THE HOPS ARE NOT INSIDE THE SPAN IN THE DOM, and that is the HTML parser, not
              // this run: provenanceLineHtml emits <div class="det-prov-hop"> inside a <p>, and
              // a <div> closes an open <p>, so the browser hoists every hop out to be a sibling
              // of the paragraph. Read them where the parser actually put them. (Recorded as an
              // incidental finding; nothing about it is changed here.)
              const hops = Array.from(document.querySelectorAll('.det-prov-hop'))
                                .map(e => e.textContent).join(' ~ ');
              const rootEl = document.getElementById('detail-root');
              return { line: el ? el.textContent : '', panel: hops,
                       rootLen: rootEl ? rootEl.innerHTML.length : 0,
                       hasProv: !!document.querySelector('.det-prov'),
                       catName: cat.name, catNum: cat.num };
            };
            return {
              amberOverGreens: mk('Amber', ['Green', 'green']),
              amberOverAmber:  mk('Amber', ['Amber'])
            };
          }
        """)
        print("    Amber category over Green modules, rendered line:")
        print(f"      {prov['amberOverGreens']['line']}")
        print("    Amber category over an Amber module, rendered line:")
        print(f"      {prov['amberOverAmber']['line']}")
        first_cat_mods = page.evaluate(
            "() => ((window.LIN_CATEGORIES||[])[0].modules||[]).map(m => m.name)")
        named = [n for n in first_cat_mods if n and n in prov["amberOverGreens"]["line"]]
        check(not named,
              "an Amber category over modules that all read Green names NO module as its driver "
              "on the rendered page", str(named))
        named2 = [n for n in first_cat_mods if n and n in prov["amberOverAmber"]["line"]]
        check(bool(named2),
              "and an Amber category WITH an Amber module still names one, so the guard "
              "suppresses a false attribution and not a true one", str(named2[:2]))
        print("    expandable hops, Amber over Greens:")
        print(f"      {prov['amberOverGreens']['panel']}")
        check("no module in this category reads as adverse" in prov["amberOverGreens"]["panel"],
              "the expandable provenance detail says why instead of going silent",
              prov["amberOverGreens"]["panel"][:160])
        check("CUSUM Anomaly Monitor" in prov["amberOverAmber"]["panel"],
              "and where a module does drive the category, the detail names it as before",
              prov["amberOverAmber"]["panel"][:160])

        print()
        print("=" * 90)
        print("5. PAGE ERRORS")
        print("=" * 90)
        real_errors = [e for e in errors if "CSP" not in e]
        check(not real_errors, "no uncaught page error while rendering every repaired surface",
              str(real_errors[:3]))

        browser.close()

    passed = sum(1 for ok, _, _ in RESULTS if ok)
    print()
    print("=" * 90)
    for ok, label, detail in RESULTS:
        if not ok:
            print(f"FAIL: {label}  [{detail}]")
    print(f"RESULT: {passed}/{len(RESULTS)} checks passed")
    return 1 if passed != len(RESULTS) else 0


if __name__ == "__main__":
    raise SystemExit(main())
