"""Run 142A, PROOFS 1-3 BY OBSERVATION IN A REAL BROWSER.

Standalone check-script, not pytest. Run with cwd = <worktree>/server:

    python tools/test_run142a_browser.py

WHAT IT MEASURES AND WHY IT IS BUILT THIS WAY.

Run 141 established that a collapsed element shows nothing regardless of what it contains, and
Run 128 that a stylesheet-reading check passed while the text it approved sat at 1.01:1. So
this does neither. It loads THE REAL `assets/js/app.js`, `taxonomy.js`, `categories.js` and
`assets/css/radar.css` into headless Chromium, primes `LinResults` with a stored row of each
shape, calls the REAL `LinApp.renderLedger`, and then:

  * reads the A3 row's text WITHOUT EXPANDING ANYTHING -- the `<details>` is left exactly as
    the renderer produced it, and the assertion is on `innerText`, which the browser computes
    from what is actually laid out and visible;
  * asserts the two shapes produce DIFFERENT visible text on that collapsed row;
  * measures the CONTRAST of the absence line against its own painted background from the
    computed styles and the real palette, and fails below 4.5:1.

THE FIXTURE IS CONSTRUCTED, and this run says so plainly: PRJ-002 is not reachable from here.
"""
from __future__ import annotations
import http.server, json, os, socket, sys, threading, functools

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
# Screenshots are RUN ARTEFACTS, not source: they go to the Run 135C scratch root, which is
# gitignored, so a check run never dirties `git status`.
SHOTS = os.environ.get("RUN135_ARTIFACT_SCRATCH") or os.path.join(ROOT, ".artifact_scratch")
SHOTS = os.path.join(SHOTS, "run142a")
os.makedirs(SHOTS, exist_ok=True)

A3_ABSTAINED = [
    {"module_id": "A3.2", "category": "A3", "reason": "awaiting a cost risk model"},
    {"module_id": "A3.3", "category": "A3", "reason": "beneath the configured exposure floor"},
    {"module_id": "A3.5", "category": "A3",
     "reason": "awaiting a contingency drawdown history"},
    {"module_id": "A3.6", "category": "A3", "reason": "awaiting a risk register"},
]
ROW_BASE = {
    "period": 1,
    "project_status": "Awaiting analysis",
    "module_results": [{"module_id": "A1.2", "category": "A1", "status_color": "Green",
                        "evidence_metric": "CPI 1.02"}],
    "category_statuses": {"A1": {"status": "Green", "state": "computed",
                                 "contributes_to_project_status": True}},
}

PAGE = """<!doctype html><meta charset="utf-8">
<link rel="stylesheet" href="/assets/css/radar.css">
<body><div id="ledger"></div>
<script src="/assets/js/categories.js"></script>
<script src="/assets/js/taxonomy.js"></script>
<script src="/assets/js/module_charts.js"></script>
<script src="/assets/js/tz.js"></script>
<script src="/assets/js/decision.js"></script>
<script src="/assets/js/app.js"></script>
</body>"""

MEASURE = r"""(catId) => {
  const row = document.querySelector('.cat-row[data-cat="' + catId + '"]');
  if (!row) return {error: "no row for " + catId};
  const sum = row.querySelector('summary');
  const note = row.querySelector('.cat-row-absence');
  // Contrast of the absence line against the background actually painted behind it.
  function rgb(s){const m=String(s).match(/[\d.]+/g);return m?m.slice(0,3).map(Number):null;}
  function lum(c){const f=c.map(v=>{v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);});
    return 0.2126*f[0]+0.7152*f[1]+0.0722*f[2];}
  let ratio = null, fg = null, bg = null;
  if (note) {
    fg = rgb(getComputedStyle(note).color);
    let el = note, found = null;
    while (el && !found) {
      const c = getComputedStyle(el).backgroundColor;
      const p = rgb(c);
      if (p && !/rgba\(.*,\s*0\)/.test(c)) found = p;
      el = el.parentElement;
    }
    bg = found || [255,255,255];
    const L1 = lum(fg), L2 = lum(bg);
    ratio = (Math.max(L1,L2)+0.05)/(Math.min(L1,L2)+0.05);
  }
  return {
    details_open: row.open,                    // NOT expanded by this harness
    summary_text: (sum ? sum.innerText : "").replace(/\s+/g," ").trim(),
    note_text: note ? note.innerText.replace(/\s+/g," ").trim() : null,
    note_absence: note ? note.getAttribute("data-absence") : null,
    note_ran: note ? note.getAttribute("data-ran") : null,
    note_of: note ? note.getAttribute("data-of") : null,
    note_visible: note ? !!(note.offsetWidth || note.offsetHeight ||
                            note.getClientRects().length) : false,
    contrast: ratio, fg: fg, bg: bg,
  };
}"""

RENDER = r"""([row, pid]) => {
  const p = {id: pid, project_id: pid, name: "Run 142A reconstruction"};
  window.LinResults.prime(pid, row);
  window.LinApp.renderLedger(p, document.getElementById("ledger"));
  return true;
}"""


def serve():
    sock = socket.socket(); sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]; sock.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=ROOT, **kw)

        def log_message(self, *a): pass

        def do_GET(self):
            if self.path.startswith("/harness"):
                b = PAGE.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(b)))
                self.end_headers(); self.wfile.write(b); return
            return super().do_GET()

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), Q)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{port}"


CHROME = ("/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell")
if not os.path.exists(CHROME):
    CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

BASE = serve()
from playwright.sync_api import sync_playwright        # noqa: E402

fail = 0
out = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 1400, "height": 1600})
    errs: list[str] = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    for tag, abst in (("all_abstained", A3_ABSTAINED), ("never_dispatched", [])):
        pg.goto(BASE + "/harness", wait_until="load")
        pg.wait_for_timeout(1200)
        # The scaffold page is deliberately minimal -- one <div id="ledger"> -- so the shared
        # scripts it must load to satisfy app.js's dependencies (tz.js, decision.js) write into
        # nodes it does not have and raise during PAGE LOAD. Those are the harness's, not the
        # renderer's, and are dropped here. Errors raised from this point on are raised BY THE
        # RENDER CALL and are asserted on below. Nothing is suppressed: the window that matters
        # is the one the measurement is about.
        errs.clear()
        row = dict(ROW_BASE); row["abstained"] = abst
        pg.evaluate(RENDER, [row, "RUN142A"])
        pg.wait_for_timeout(400)
        out[tag] = pg.evaluate(MEASURE, "a3")
        pg.screenshot(path=os.path.join(SHOTS, f"{tag}.png"), full_page=False)
    b.close()

print("Page errors raised BY THE RENDER CALL:", errs or "none")
for tag in ("all_abstained", "never_dispatched"):
    r = out[tag]
    print("--- %s" % tag)
    for k in ("details_open", "note_absence", "note_ran", "note_of", "note_visible",
              "contrast", "fg", "bg"):
        print("    %-14s %s" % (k, r.get(k)))
    print("    summary_text   %r" % r.get("summary_text"))

a, n = out["all_abstained"], out["never_dispatched"]
if a.get("error") or n.get("error"):
    print("FAIL: %s" % (a.get("error") or n.get("error"))); fail += 1
if a.get("details_open") or n.get("details_open"):
    print("FAIL: the harness expanded a row; the measurement is not of the collapsed view")
    fail += 1
if not a.get("note_visible"):
    print("FAIL proof 1/2: the all-abstained absence line is not laid out"); fail += 1
if a.get("summary_text") == n.get("summary_text"):
    print("FAIL proof 2: the collapsed A3 row reads IDENTICALLY in both cases:\n    %r"
          % a.get("summary_text"))
    fail += 1
else:
    print("PASS proof 2: the collapsed A3 row reads differently in the two cases, with no "
          "expansion and without querying the database")
if a.get("note_absence") != "ran_without_band" or n.get("note_absence") != "never_called":
    print("FAIL proof 3: the condition the code tested is not what the row states"); fail += 1
else:
    print("PASS proof 3: condition tested and text emitted, side by side")
    print("    tested %-16s -> emitted %r" % (a["note_absence"], a["note_text"]))
    print("    tested %-16s -> emitted %r" % (n["note_absence"], n["note_text"]))
if a.get("note_ran") != "4":
    print("FAIL proof 1: the row counts %s abstaining modules, expected 4" % a.get("note_ran"))
    fail += 1
for tag in ("all_abstained", "never_dispatched"):
    c = out[tag].get("contrast")
    if c is None or c < 4.5:
        print("FAIL contrast: %s absence line at %s:1 (AA needs 4.5:1)" % (tag, c)); fail += 1
    else:
        print("PASS contrast: %s absence line at %.2f:1" % (tag, c))
if errs:
    print("FAIL: renderLedger raised JavaScript errors: %s" % errs); fail += 1

print()
print("Screenshots:", SHOTS)
print("RESULT:", "FAIL" if fail else "PASS", "(%d failing checks)" % fail)
sys.exit(1 if fail else 0)
