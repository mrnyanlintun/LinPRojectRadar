#!/usr/bin/env python3
"""
RUN 61. THE CALLER STATES ITS QUESTION -- measured on the REAL LOAD PATH.

WHAT MAKES THIS DRIVER DIFFERENT FROM EVERY BROWSER HARNESS SINCE RUN 44, and why it is a new
file rather than an edit to one of them (the existing drivers are the evidence of what earlier
runs measured and are not rewritten):

  1. The project is LOADED FROM THE SERVER. Nothing is constructed in JavaScript.
  2. NO PRE-PRIMING. `LinResults.prime` is NOT called before `render()`. `drive_run44_browser.py`
     lines 250-252 do exactly that, and every harness since copied it. That is the one order in
     which the defect cannot appear, which is why ten runs of browser verification passed
     against a page that was naming a Green module as the driver of a status a Red module set.
  3. THE PROJECT'S CURRENT PERIOD IS NOT 1. A fixture computed only at period 1 cannot show this
     class of defect at all.
  4. The page is driven through `LinDetail.render` on the real load path, so `projectperiods` and
     `projectresults` are issued by the application and observed on the wire.

It also records, by execution, WHICH READER ASKED FOR WHAT. `LinResults.rowFor`,
`rowForPeriod`, `latest`, `rowsForPeriods` and `window.getModuleStatus` are wrapped by an INIT
SCRIPT installed before any application script runs, so no call is missed, and each call records
its own stack. That is the caller table: established by what each caller does with the answer,
not by its name or its comment.

argv[1] = label written into the output
argv[2] = path to write the captured JSON to
"""
from __future__ import annotations
import json, os, pathlib, socket, sys, threading, time, logging

LABEL = sys.argv[1]
OUT = pathlib.Path(sys.argv[2])
ROOT = pathlib.Path(os.environ["OG_ROOT"]).resolve()
sys.path.insert(0, str(ROOT / "server"))
logging.disable(logging.INFO)

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

from fastapi.testclient import TestClient
from sqlalchemy import select
import app.main as main
from app.research_identity import hash_access_token
from app.research_models import Participant
from app.simulation.registry import registry_index, service_index, CORE_VOTING_MODULES

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory

def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"HTTP {r.status_code} {r.text[:300]}"
    return r.json()

PM_TOKEN = "run61-pm-fixed-token"
with Session() as s:
    p = s.scalar(select(Participant).where(Participant.pseudonymous_code == "R60-PM"))
    assert p is not None, "R60-PM participant missing"
    p.access_token_hash = hash_access_token(PM_TOKEN)
    s.commit()
PM = post({"action": "researchlogin", "access_token": PM_TOKEN})["session_token"]

sock = socket.socket(); sock.bind(("127.0.0.1", 0)); PORT = sock.getsockname()[1]; sock.close()
import uvicorn
cfg = uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="critical")
server = uvicorn.Server(cfg)
threading.Thread(target=server.run, daemon=True).start()
for _ in range(200):
    try:
        c = socket.create_connection(("127.0.0.1", PORT), 0.2); c.close(); break
    except OSError:
        time.sleep(0.05)
BASE = f"http://127.0.0.1:{PORT}"

print(f"LABEL:            {LABEL}")
print(f"browser cwd:      {os.getcwd()}")
print(f"repository root:  {ROOT}")
print(f"DATABASE_URL:     {os.environ.get('DATABASE_URL')}")
print(f"registry: {len(registry_index())}  in service: {len(service_index())}  "
      f"core voting: {CORE_VOTING_MODULES}")

from playwright.sync_api import sync_playwright

# The observer. Installed as an INIT SCRIPT so it is in place before any application script runs
# and cannot miss an early call. It RECORDS and does not alter: every wrapper returns exactly
# what the wrapped function returned.
OBSERVER = r"""
window.__R61 = { calls: [], primes: [], wired: false };
function __r61_stack() {
  try { throw new Error('x'); } catch (e) {
    return String(e.stack || '').split('\n').slice(2, 7)
      .map(s => s.trim()).filter(s => s && s.indexOf('__r61') === -1).join(' | ');
  }
}
function __r61_wire() {
  if (window.__R61.wired || !window.LinResults) return;
  window.__R61.wired = true;
  var L = window.LinResults;
  ['rowFor', 'rowForPeriod', 'latest', 'rowsForPeriods'].forEach(function (fn) {
    if (typeof L[fn] !== 'function') return;
    var orig = L[fn];
    L[fn] = function (proj) {
      var out = orig.apply(this, arguments);
      var per = null;
      try {
        if (fn === 'rowFor') per = out ? out.period : null;
        else if (fn === 'rowForPeriod') per = out ? out.period : null;
        else if (fn === 'latest') per = out ? out.period : null;
        else if (fn === 'rowsForPeriods') per = (out || []).map(function (r) { return r.period; });
      } catch (e) {}
      window.__R61.calls.push({
        fn: fn,
        asked: fn === 'rowForPeriod' ? arguments[1]
             : (fn === 'rowsForPeriods' ? arguments[1] : null),
        heldPeriod: (proj && proj.storedResult) ? proj.storedResult.period : null,
        got: per, stack: __r61_stack()
      });
      return out;
    };
  });
  var op = L.prime;
  L.prime = function (pid, row) {
    window.__R61.primes.push({ pid: pid, period: row ? row.period : null, stack: __r61_stack() });
    return op.apply(this, arguments);
  };
  if (typeof window.getModuleStatus === 'function') {
    var gm = window.getModuleStatus;
    window.getModuleStatus = function (mc, proj) {
      var out = gm.apply(this, arguments);
      window.__R61.calls.push({
        fn: 'getModuleStatus', mc: mc,
        heldPeriod: (proj && proj.storedResult) ? proj.storedResult.period : null,
        got: out, stack: __r61_stack()
      });
      return out;
    };
  }
}
var __r61_iv = setInterval(function () { __r61_wire(); if (window.__R61.wired) clearInterval(__r61_iv); }, 5);
"""

CAP = {"label": LABEL, "database_url": os.environ.get("DATABASE_URL"),
       "registry": len(registry_index()), "in_service": len(service_index()),
       "projects": {}}

PROJECTS = ["PRJ-R60", "PRJ-R60B"]

OPEN_SECTIONS_JS = r"""() => {
  // The DOM-rendered panels only. The three WebGL surfaces (Signal Web sphere, Project Signal
  // Network, Signal Flow's animated canvas) are NOT opened here: opening all of them at once
  // under swiftshader wedges the page, measured in Run 61, which lost a browser session to it.
  const ids = ['d-ledger','d-ensemble','d-docsignals','d-brief','d-decision','d-signals'];
  const done = [];
  ids.forEach(id => {
    const body = document.getElementById('body-' + id);
    if (!body) return;
    if (body.style.display === 'none' && window.toggleSection) { window.toggleSection(id); done.push(id); }
    else { done.push(id + '(already open)'); }
  });
  return done;
}"""

SURFACE_JS = r"""(id) => {
  const q = (s) => document.querySelector(s);
  const t = (s) => { const e = q(s); return e ? (e.innerText || '').trim() : null; };
  const detail = q('[data-page="detail"]') || q('#page-detail') || document.body;
  const all = (detail.innerText || '');
  const p = (window.LIN_PROJECTS || []).filter(x => x.id === id)[0] || null;
  let row = null;
  try { row = (window.LinResults && LinResults.rowFor(p)) || null; } catch (e) {}
  const colors = row && row.module_results
    ? row.module_results.reduce((a, m) => { a[m.module_id] = m.status_color; return a; }, {})
    : null;
  // Which period each surface is showing, established from the row each surface reads.
  const askPeriod = (sel) => {
    const el = q(sel);
    return el ? (el.innerText || '').trim().slice(0, 400) : null;
  };
  return {
    held_row_period: row ? row.period : null,
    stored_projection_period: p && p.storedResult ? p.storedResult.period : null,
    held_module_colors: colors,
    prov_line: t('.det-prov-line'),
    prov_hops: Array.from(document.querySelectorAll('.det-prov-hop')).map(e => (e.innerText||'').trim()),
    prov_host_present: !!q('[data-provenance-host]'),
    surf_signal_flow: askPeriod('.detail-flow, [data-page="detail"] .flow-panel'),
    surf_signal_web: askPeriod('.detail-web'),
    surf_ensemble: askPeriod('.detail-ensemble'),
    surf_projnet: askPeriod('.detail-projnet'),
    surf_ledger: askPeriod('.detail-ledger'),
    surf_brief: askPeriod('.eb-panel'),
    surf_decision: askPeriod('.detail-decision'),
    page_text: all
  };
}"""

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME,
                                 args=["--use-gl=swiftshader", "--no-sandbox", "--headless=new"])
    page = browser.new_page(viewport={"width": 1680, "height": 3000})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    wire = []
    page.on("request", lambda r: wire.append(r.post_data or "") if "/exec" in r.url else None)
    for pattern in ("**accounts.google.com**", "**apis.google.com**", "**gstatic.com**",
                    "**tiles.openfreemap.org**", "**maps.googleapis.com**"):
        page.route(pattern, lambda r: r.abort())
    page.add_init_script(OBSERVER)
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.evaluate("(t) => sessionStorage.setItem('og-session-token', t)", PM)
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.add_style_tag(content="*,*::before,*::after{transition:none!important;animation:none!important}")
    page.wait_for_timeout(8000)

    base = page.evaluate("""() => ({
        pageSections: document.querySelectorAll('.page').length,
        demoTell: Array.from(document.scripts).map(s => s.src.split('/').pop())
                    .filter(s => s === 'api.js' || s === 'boot.js'),
        hasDetail: !!window.LinDetail, observerWired: !!(window.__R61 && window.__R61.wired),
        shapes: {
          rowFor: !!(window.LinResults && window.LinResults.rowFor),
          rowForPeriod: !!(window.LinResults && window.LinResults.rowForPeriod),
          latest: !!(window.LinResults && window.LinResults.latest),
          rowsForPeriods: !!(window.LinResults && window.LinResults.rowsForPeriods)
        }
    })""")
    CAP["app_under_test"] = base
    print(f"  DEng\\Demo tell -> .page sections: {base['pageSections']} (expected 7)   "
          f"api.js/boot.js in document.scripts: {base['demoTell']} (expected [])")
    print(f"  observer wired: {base['observerWired']}   shapes present: {base['shapes']}")

    for LEGACY in PROJECTS:
        page.evaluate("() => window.__R61 && (window.__R61.calls = [], window.__R61.primes = [])")
        # THE PORTFOLIO LOADS FIRST, exactly as it does for a user signing in. This is the step
        # that used to prime a PERIOD 1 row into the shared cache.
        page.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('workspace')")
        page.wait_for_timeout(3000)
        try:
            page.evaluate("() => window.LinWorkspace && LinWorkspace.renderPortfolio && LinWorkspace.renderPortfolio()")
        except Exception:
            pass
        page.wait_for_timeout(2500)
        page.evaluate("() => window.LinApp && LinApp.showPage && LinApp.showPage('portfolio')")
        page.wait_for_timeout(800)
        try:
            page.evaluate("() => window.LinApp && LinApp.buildFallbackList && LinApp.buildFallbackList()")
        except Exception:
            pass
        page.wait_for_timeout(1200)
        primes_before = page.evaluate("() => window.__R61.primes.slice()")

        # ---- FIRST RENDER. No pre-priming by this harness. --------------------------------
        page.evaluate("(id) => window.LinDetail && LinDetail.render(id)", LEGACY)
        page.wait_for_timeout(400)
        first = page.evaluate(SURFACE_JS, LEGACY)
        page.wait_for_timeout(11000)
        settled = page.evaluate(SURFACE_JS, LEGACY)

        # ---- SECTION 4.5. EVERY SURFACE THAT READS MODULE STATUS. ------------------------
        # Each of the eight is a LAZILY-INITIALISED panel: it does not read a stored row at all
        # until its section is opened, which is why a capture taken on a freshly rendered page
        # sees only the provenance line and the brief. Open them all, then attribute every
        # module-status read that follows to the file and line that made it, and record WHICH
        # PERIOD the page held when it did. That is the per-surface answer section 4.5 asks for,
        # established by execution rather than by reading the panel's own caption.
        page.evaluate("() => window.__R61.calls.length = 0")
        opened = page.evaluate(OPEN_SECTIONS_JS)
        page.wait_for_timeout(9000)
        surface_calls = page.evaluate("() => window.__R61.calls.slice(0, 8000)")
        by_file = {}
        for c in surface_calls:
            st = c.get("stack") or ""
            frame = next((f for f in st.split(" | ") if "/assets/js/" in f), st[:60])
            line = frame.split("/assets/js/")[-1].split(")")[0] if "/assets/js/" in frame else "?"
            rec = by_file.setdefault(line, {"held": set(), "got": set(), "n": 0})
            rec["n"] += 1
            rec["held"].add(str(c.get("heldPeriod")))
            rec["got"].add(str(c.get("got"))[:12])
        print(f"      sections opened: {opened}")
        print("      -- SECTION 4.5, per reader: which period the page held, what it returned --")
        for k in sorted(by_file):
            r = by_file[k]
            print(f"         {k:44s} n={r['n']:5d} held={sorted(r['held'])} got={sorted(r['got'])[:6]}")
        SURFACES = {k: {"n": v["n"], "held": sorted(v["held"]), "got": sorted(v["got"])}
                    for k, v in by_file.items()}
        after_open = page.evaluate(SURFACE_JS, LEGACY)

        # ---- SECOND RENDER of the same project, row already primed. -----------------------
        page.evaluate("(id) => window.LinDetail && LinDetail.render(id)", LEGACY)
        page.wait_for_timeout(400)
        second_immediate = page.evaluate(SURFACE_JS, LEGACY)
        page.wait_for_timeout(9000)
        second = page.evaluate(SURFACE_JS, LEGACY)

        # ---- THE DEFECT'S OWN CONDITION, ISOLATED. ---------------------------------------
        # Run 60 measured that the portfolio loader primed the project's PERIOD 1 row into the
        # shared cache before the detail page rendered, and that `rowFor` then handed that row
        # to every reader asking for module statuses while the page held period 4. This stage
        # reproduces exactly that, deliberately and by hand, and asks what the page says.
        #
        # This is NOT the pre-priming the verification rule forbids. The rule forbids priming
        # the row the page is ABOUT to render so that render() finds it already correct. This
        # primes a DIFFERENT period's row -- the adversarial case -- and then renders.
        p1 = post({"action": "projectresults", "id": LEGACY, "period": 1,
                   "session_token": PM})
        page.evaluate("""([id, row]) => {
            window.LinResults.clear();
            window.LinResults.prime(id, row);  // R61-ADVERSARIAL-PRIME
        }""", [LEGACY, p1.get("result")])
        page.evaluate("(id) => window.LinDetail && LinDetail.render(id)", LEGACY)
        page.wait_for_timeout(120)
        p1_render = page.evaluate(SURFACE_JS, LEGACY)
        page.wait_for_timeout(11000)
        p1_settled = page.evaluate(SURFACE_JS, LEGACY)
        print(f"      [P1-PRIMED] period-1 row primed, then render():")
        print(f"        immediate prov line : {p1_render['prov_line']!r}")
        print(f"        immediate held row  : period {p1_render['held_row_period']}  "
              f"colors {p1_render['held_module_colors']}")
        print(f"        settled   prov line : {p1_settled['prov_line']!r}")
        print(f"        settled   held row  : period {p1_settled['held_row_period']}")

        CAP["projects"][LEGACY] = {
            "surfaces_by_reader": SURFACES, "sections_opened": opened,
            "after_open": after_open,
            "p1_primed_render": p1_render, "p1_primed_settled": p1_settled,
            "primes_before_render": primes_before,
            "first_render": first, "settled": settled,
            "second_render_immediate": second_immediate, "second_render": second,
            "calls": page.evaluate("() => window.__R61.calls.slice(0, 4000)"),
            "primes": page.evaluate("() => window.__R61.primes.slice()"),
        }
        print(f"  --- {LEGACY} ---")
        print(f"      primes BEFORE first render : "
              f"{[(x['pid'], x['period']) for x in primes_before]}")
        print(f"      projection period held     : {first['stored_projection_period']}")
        print(f"      FIRST  render prov line    : {first['prov_line']!r}")
        print(f"        held row period          : {first['held_row_period']}   "
              f"colors {first['held_module_colors']}")
        print(f"      SETTLED       prov line    : {settled['prov_line']!r}")
        print(f"        held row period          : {settled['held_row_period']}   "
              f"colors {settled['held_module_colors']}")
        print(f"      SECOND render prov line    : {second['prov_line']!r}")
        print(f"        held row period          : {second['held_row_period']}")
        agree = settled["prov_line"] == second["prov_line"]
        print(f"      FIRST(settled) == SECOND   : {agree}")
        CAP["projects"][LEGACY]["first_equals_second"] = agree

    CAP["pageerrors"] = errors
    CAP["wire"] = [w for w in wire if w]
    browser.close()

OUT.write_text(json.dumps(CAP, indent=1, sort_keys=True, default=str), encoding="utf-8")
print(f"\ncaptured -> {OUT}")
print(f"pageerrors: {len(errors)}")
for e in errors[:8]:
    print("  ", e[:200])
print("DRIVER_OK")
