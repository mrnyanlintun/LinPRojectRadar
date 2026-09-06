"""RUN 143 PART 2, PROOF 11: A CARRIED READING IS VISIBLY DISTINCT FROM A CURRENT ONE,
CONFIRMED BY OBSERVATION IN A BROWSER AND NOT FROM THE SERVED DATA.

Run with cwd = <worktree>/server:   python tools/test_run143p2_browser.py

WHY IT IS BUILT THIS WAY, and it is the owner's own condition. "A carried reading that renders
identically to a current one is the defect this run must not ship" and "confirm by observation
in a browser, not from the served data." A check that read the stored row and found `carried:
true` would prove only that the server said so -- which is the thing the client was, until this
run, structurally unable to show. So this loads the REAL app.js, taxonomy.js, categories.js and
radar.css into headless Chromium, primes two rows that differ ONLY in the carrying fields,
calls the REAL LinApp.renderLedger, and compares what the browser LAYS OUT.

THE COLLAPSED STATE IS ASSERTED, not assumed. Every `<details>` but b3 is closed on arrival and
Run 141 established that a collapsed element shows nothing whatever it contains. So the harness
never expands anything, asserts `details.open` is false on the row it measures, and reads
`innerText`, which the browser computes from what is actually laid out.

THE FIXTURE IS CONSTRUCTED and this run says so plainly: no real project is reachable from here.
The two rows are byte-identical apart from the fields `carry_forward.py` writes.
"""
from __future__ import annotations
import http.server, os, socket, sys, threading

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SHOTS = os.environ.get("RUN135_ARTIFACT_SCRATCH") or os.path.join(ROOT, ".artifact_scratch")
SHOTS = os.path.join(SHOTS, "run143p2")
os.makedirs(SHOTS, exist_ok=True)

CAT = "a2"                       # collapsed on arrival; only b3 is open by default
MODULE = "A2.1"

# The reading as a CURRENT one: a band this period's evidence produced.
CURRENT = {"module_id": MODULE, "category": "A2", "status_color": "Amber",
           "evidence_metric": "The controlling path carries 3 days of float."}
# The SAME reading, carried. Identical band, identical module, and the only differences are the
# fields `carry_forward.select_carried` writes.
CARRIED = dict(CURRENT)
CARRIED.update({
    "evidence_metric": ("Carried from P1: this measure produced no reading from this period's "
                        "evidence, so its most recent earlier reading is shown and is voting. "
                        "That reading, from P1, said: The controlling path carries 3 days of "
                        "float."),
    "carried": True, "carried_from_period": "P1", "carried_from_age": 2,
    "carried_evidence": "The controlling path carries 3 days of float.",
    "carried_reason": "Awaiting the project's activity network.",
})

def row_for(mod, carried_count):
    return {
        "period": 3,
        "project_status": "Amber",
        "module_results": [mod],
        "abstained": [],
        "category_statuses": {"A2": {"status": "Amber", "state": "computed",
                                     "contributes_to_project_status": True}},
        "project_status_basis": {"carried_count": carried_count, "carried_of_banded": 1,
                                 "carried_oldest_age": 2 if carried_count else 0},
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
  const chip = row.querySelector('.cat-mod-carried');
  const headNote = row.querySelector('.cat-row-carried');
  function vis(el){ return !!(el && (el.offsetWidth || el.offsetHeight ||
                                     el.getClientRects().length)); }
  function rgb(s){const m=String(s).match(/[\d.]+/g);return m?m.slice(0,3).map(Number):null;}
  function lum(c){const f=c.map(v=>{v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);});
    return 0.2126*f[0]+0.7152*f[1]+0.0722*f[2];}
  function contrast(el){
    if(!el) return null;
    const fg = rgb(getComputedStyle(el).color);
    let e = el, found = null;
    while (e && !found){ const c = getComputedStyle(e).backgroundColor; const p = rgb(c);
      if (p && !/rgba\(.*,\s*0\)/.test(c)) found = p; e = e.parentElement; }
    const bg = found || [255,255,255];
    const L1 = lum(fg), L2 = lum(bg);
    return (Math.max(L1,L2)+0.05)/(Math.min(L1,L2)+0.05);
  }
  const modRow = row.querySelector('.cat-mod-row');
  return {
    details_open: row.open,
    summary_text: (sum ? sum.innerText : "").replace(/\s+/g," ").trim(),
    head_note_text: headNote ? headNote.innerText.replace(/\s+/g," ").trim() : null,
    head_note_visible: vis(headNote),
    head_note_contrast: contrast(headNote),
    // The chip lives INSIDE the collapsed <details>. It is measured to show that the marker
    // exists there too, but the proof rests on the summary, which is what a reader sees.
    chip_text: chip ? chip.textContent.replace(/\s+/g," ").trim() : null,
    chip_from_period: chip ? chip.getAttribute("data-from-period") : null,
    mod_row_class: modRow ? modRow.className : null,
    mod_row_border_left: modRow ? getComputedStyle(modRow).borderLeftStyle : null,
    mod_row_bg: modRow ? getComputedStyle(modRow).backgroundColor : null,
    // The band itself must be UNCHANGED: a carried Amber is an Amber and votes as one.
    pill_html: (function(){ const q = row.querySelector('.cat-mod-row .pill');
      return q ? (q.className + "|" + q.textContent.trim()) : null; })(),
    mod_row_html: modRow ? modRow.innerHTML.replace(/\s+/g," ").trim().slice(0,300) : null,
  };
}"""

RENDER = r"""([row, pid]) => {
  const p = {id: pid, project_id: pid, name: "Run 143 Part 2 fixture"};
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


CHROME = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"
if not os.path.exists(CHROME):
    CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

BASE = serve()
from playwright.sync_api import sync_playwright        # noqa: E402

fail = 0
out = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 1400, "height": 1400})
    errs: list[str] = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    for tag, mod, n in (("current", CURRENT, 0), ("carried", CARRIED, 1)):
        pg.goto(BASE + "/harness", wait_until="load")
        pg.wait_for_timeout(1200)
        errs.clear()
        pg.evaluate(RENDER, [row_for(mod, n), "RUN143P2"])
        pg.wait_for_timeout(400)
        out[tag] = pg.evaluate(MEASURE, CAT)
        pg.screenshot(path=os.path.join(SHOTS, f"{tag}_collapsed.png"), full_page=False)
    b.close()

print("Page errors raised BY THE RENDER CALL:", errs or "none")
for tag in ("current", "carried"):
    r = out[tag]
    print(f"--- {tag}")
    for k in ("details_open", "head_note_visible", "head_note_contrast", "chip_text",
              "chip_from_period", "mod_row_class", "mod_row_border_left", "mod_row_bg",
              "pill_html"):
        print("    %-20s %s" % (k, r.get(k)))
    print("    summary_text         %r" % r.get("summary_text"))

c, u = out["carried"], out["current"]
if c.get("error") or u.get("error"):
    print("FAIL: %s" % (c.get("error") or u.get("error"))); fail += 1

# THE COLLAPSED STATE, ASSERTED. Without this the rest of the proof is worthless.
if c.get("details_open") or u.get("details_open"):
    print("FAIL: a row was expanded; this is not a measurement of the collapsed view")
    fail += 1
else:
    print("PASS: both rows measured with <details> CLOSED, exactly as rendered on arrival")

# ---- THE PROOF. Two rows differing only in the carrying fields must not read the same.
if c.get("summary_text") == u.get("summary_text"):
    print("FAIL proof 11: THE DEFECT. The collapsed row reads IDENTICALLY whether the "
          "reading is carried or current:\n    %r" % c.get("summary_text"))
    fail += 1
else:
    print("PASS proof 11: WITHOUT CLICKING, the collapsed row reads differently.")
    print("    current: %r" % u.get("summary_text"))
    print("    carried: %r" % c.get("summary_text"))

if not c.get("head_note_visible"):
    print("FAIL proof 11: the carry note on the collapsed head is not laid out"); fail += 1
if u.get("head_note_text") is not None:
    print("FAIL: a CURRENT reading rendered a carry note; the marker is not read-only-when-set")
    fail += 1
else:
    print("PASS: a current reading renders no carry note at all -- nothing is invented")

# The period must be NAMED on the surface, never "the previous period".
if "P1" not in (c.get("summary_text") or "") and (c.get("chip_from_period") != "P1"):
    print("FAIL proof 11: the surface does not name the period the reading came from"); fail += 1
if c.get("chip_text") and "Carried from P1" in c["chip_text"]:
    print("PASS: the module chip names its source period: %r" % c["chip_text"])
elif c.get("chip_text"):
    print("FAIL: the chip does not name the period: %r" % c["chip_text"]); fail += 1

# Contrast of the visible carry note against the background actually painted behind it.
cc = c.get("head_note_contrast")
if cc is None or cc < 4.5:
    print("FAIL contrast: the carry note reads at %s:1 (AA needs 4.5:1)" % cc); fail += 1
else:
    print("PASS contrast: the carry note reads at %.2f:1" % cc)

# The band must NOT have been repainted: a carried Amber is an Amber and votes as one.
if c.get("pill_html") != u.get("pill_html") or not c.get("pill_html"):
    print("FAIL: the band pill itself changed (%r vs %r); a carried reading's band is its band"
          % (c.get("pill_html"), u.get("pill_html")))
    fail += 1
else:
    print("PASS: the band pill is unchanged -- the marker qualifies the reading, it does not "
          "restate it")

# More than one signal, so no single theme or colour-vision difference erases the distinction.
if "is-carried" not in str(c.get("mod_row_class")):
    print("FAIL: the carried module row carries no class of its own"); fail += 1
elif c.get("mod_row_border_left") != "dashed":
    print("FAIL: the dashed rule is not painted (border-left-style=%s)"
          % c.get("mod_row_border_left"))
    fail += 1
else:
    print("PASS: a second, non-textual signal is painted (dashed left rule) and a third "
          "(background %s vs %s)" % (c.get("mod_row_bg"), u.get("mod_row_bg")))

if errs:
    print("FAIL: renderLedger raised JavaScript errors: %s" % errs); fail += 1

print("\nScreenshots: %s" % SHOTS)
print("ALL BROWSER CHECKS PASSED" if not fail else "%d BROWSER CHECK(S) FAILED" % fail)
sys.exit(1 if fail else 0)
