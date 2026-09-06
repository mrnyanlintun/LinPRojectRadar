"""RUN 144 RULING 3, PROOF 4: A CARRIED READING SHOWS ITS AGE WITHOUT CLICKING, CONFIRMED BY
OBSERVATION IN A BROWSER AND NOT FROM THE SERVED DATA.

Run with cwd = <worktree>/server:   PYTHONPATH=. python tools/test_run144_ruling3_browser.py

WHY THIS EXISTS. The owner rejected both a derived look-back horizon and a fixed 60-month cap,
and ruled the look-back UNBOUNDED: "the age carries the weight instead". That makes the stated
age the entire safeguard, so it must meet the bar Run 143 set for the carried MARKING itself --
visible with the disclosure CLOSED, at AA contrast, confirmed in a browser. A safeguard a
reviewer has to hover or click to reach is the shape of defect this codebase keeps finding.

WHAT IS ASSERTED, and each is asserted rather than assumed:
  * `<details>` is CLOSED on the measured row. Run 141 established a collapsed element shows
    nothing whatever it contains, so the whole proof rests on this.
  * The age appears in `innerText` -- what the browser actually LAID OUT -- not in an attribute,
    a title or a tooltip. A `title=` would pass a DOM query and fail a reader.
  * It is measured on MORE THAN ONE THEME, because a single theme can hide a colour.
  * NO THRESHOLD. Age 1 and age 40 are rendered and compared: same colour, same font, same
    border, same words apart from the number and its plural. The owner forbade a cap, a warning
    threshold and a colour change past some age, and this is how that stays forbidden.

THE FIXTURE IS CONSTRUCTED and this file says so plainly: two rows byte-identical apart from the
fields `carry_forward.py` writes.
"""
from __future__ import annotations
import http.server, os, socket, sys, threading

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SHOTS = os.environ.get("RUN135_ARTIFACT_SCRATCH") or os.path.join(ROOT, ".artifact_scratch")
SHOTS = os.path.join(SHOTS, "run144r3")
os.makedirs(SHOTS, exist_ok=True)

CAT = "a2"                       # collapsed on arrival; only b3 is open by default
MODULE = "A2.1"
THEMES = ("dark", "light", "newyork")

# THE THEMES THE AA BAR IS ASSERTED ON. The owner asked for "at least two themes"; dark and
# light are the two the app ships as its primary pair and they are asserted.
#
# `newyork` is MEASURED AND REPORTED but not asserted, and the reason is stated rather than
# assumed: it paints a dark page (rgb(13,17,21)) while leaving `--status-nodata-mod-text` at the
# LIGHT default #55606f, so EVERY use of that token on that theme is under AA -- the "No data"
# chip, the abstention reason line, and Run 143's carried note, all of which predate Run 144.
# Ruling 3 did not create it and ruling 3's scope does not include repainting a theme's palette,
# so it is reported as a finding for a ruling rather than silently fixed or silently dropped.
AA_THEMES = ("dark", "light")

CURRENT = {"module_id": MODULE, "category": "A2", "status_color": "Amber",
           "evidence_metric": "The controlling path carries 3 days of float."}


def carried(age: int, period: str) -> dict:
    m = dict(CURRENT)
    m.update({
        "evidence_metric": (f"Carried from {period}: this measure produced no reading from this "
                            f"period's evidence, so its most recent earlier reading is shown "
                            f"and is voting. That reading, from {period}, said: The controlling "
                            f"path carries 3 days of float."),
        "carried": True, "carried_from_period": period, "carried_from_age": age,
        "carried_evidence": "The controlling path carries 3 days of float.",
        "carried_reason": "Awaiting the project's activity network.",
    })
    return m


def row_for(mod, carried_count, oldest):
    return {
        "period": 9,
        "project_status": "Amber",
        "module_results": [mod],
        "abstained": [],
        "category_statuses": {"A2": {"status": "Amber", "state": "computed",
                                     "contributes_to_project_status": True}},
        "project_status_basis": {"carried_count": carried_count, "carried_of_banded": 1,
                                 "carried_oldest_age": oldest},
    }


PAGE = """<!doctype html><meta charset="utf-8">
<link rel="stylesheet" href="/assets/css/radar.css">
<body data-theme="__THEME__"><div id="ledger"></div>
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
  const sum  = row.querySelector('summary');
  const note = row.querySelector('.cat-row-carried');
  const chip = row.querySelector('.cat-mod-carried');
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
  function style(el){
    if(!el) return null;
    const s = getComputedStyle(el);
    return [s.color, s.backgroundColor, s.fontFamily, s.fontSize, s.fontWeight,
            s.fontStyle, s.borderStyle, s.borderColor, s.textDecorationLine].join("|");
  }
  return {
    details_open: row.open,
    // innerText, not textContent: it is what the browser LAID OUT, so a hidden node cannot
    // pass this measurement.
    summary_text: (sum ? sum.innerText : "").replace(/\s+/g," ").trim(),
    note_text: note ? note.innerText.replace(/\s+/g," ").trim() : null,
    note_visible: vis(note),
    note_contrast: contrast(note),
    note_style: style(note),
    note_oldest_attr: note ? note.getAttribute("data-oldest-age") : null,
    // textContent, NOT innerText: the chip lives INSIDE the closed <details>, so the browser
    // lays out nothing for it and innerText is empty. That emptiness is the point -- it is
    // exactly why the age also has to be on the summary -- and it is asserted below as
    // `chip_laid_out: false`. textContent still reads what the chip WOULD show once opened.
    chip_text: chip ? chip.textContent.replace(/\s+/g," ").trim() : null,
    // What a reader actually GETS from the chip while the disclosure is closed. innerText is
    // the browser's own rendered-text computation, so this is empty for anything the reader
    // cannot read -- a stricter and more honest test than a box measurement, which Chromium
    // still reports for children of a closed <details>.
    chip_rendered: chip ? chip.innerText.replace(/\s+/g," ").trim() : null,
    chip_age_attr: chip ? chip.getAttribute("data-from-age") : null,
    chip_style: style(chip),
    // Overflow guard: the label got longer, so prove the row is not wider than its container.
    row_overflows: row.scrollWidth > row.clientWidth + 1,
    // THE THEME IS MEASURED, NOT ASSUMED. Setting `data-theme` proves nothing if something
    // in the page resets it, and three "themes" that resolve to one palette would make a
    // three-theme claim false. These two are compared across themes below.
    theme_attr: document.body.getAttribute("data-theme"),
    theme_token: getComputedStyle(document.body)
                   .getPropertyValue("--status-nodata-mod-text").trim(),
    page_bg: getComputedStyle(document.body).backgroundColor,
  };
}"""

# THE THEME IS SET HERE, AFTER LOAD, AND NOT ON THE <body> TAG. Setting it in the served HTML
# was tried first and it does not survive: the app's own theme bootstrap runs on load and
# rewrites `data-theme` to "plain", so all three "themes" resolved to ONE palette and a
# three-theme claim would have been false. It is set after the bootstrap has run, and the
# resolved token is then MEASURED and compared across themes rather than assumed.
RENDER = r"""([row, pid, theme]) => {
  document.body.setAttribute("data-theme", theme);
  const p = {id: pid, project_id: pid, name: "Run 144 ruling 3 fixture"};
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
                theme = self.path.split("theme=")[-1] if "theme=" in self.path else "dark"
                b = PAGE.replace("__THEME__", theme).encode()
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
FIXTURES = (
    ("current", CURRENT, 0, 0),
    ("age1", carried(1, "P8"), 1, 1),
    ("age8", carried(8, "P1"), 1, 8),
    ("age40", carried(40, "P1"), 1, 40),
)
out: dict[tuple[str, str], dict] = {}
errs: list[str] = []

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 1400, "height": 1400})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    for theme in THEMES:
        for tag, mod, n, oldest in FIXTURES:
            pg.goto(f"{BASE}/harness?theme={theme}", wait_until="load")
            pg.wait_for_timeout(900)
            errs.clear()
            pg.evaluate(RENDER, [row_for(mod, n, oldest), "RUN144R3", theme])
            pg.wait_for_timeout(300)
            out[(theme, tag)] = pg.evaluate(MEASURE, CAT)
            if tag in ("current", "age8"):
                pg.screenshot(path=os.path.join(SHOTS, f"{theme}_{tag}_collapsed.png"))
            if errs:
                print(f"FAIL: renderLedger raised on {theme}/{tag}: {errs}"); fail += 1
    # A NARROW VIEWPORT, because the label got longer and a phone is where a longer label
    # clips. The age must still be laid out and still read at AA on the smallest width the
    # stylesheet targets.
    pgn = b.new_page(viewport={"width": 390, "height": 900})
    pgn.on("pageerror", lambda e: errs.append(str(e)))
    for theme in THEMES:
        pgn.goto(f"{BASE}/harness?theme={theme}", wait_until="load")
        pgn.wait_for_timeout(900)
        errs.clear()
        pgn.evaluate(RENDER, [row_for(carried(40, "P1"), 1, 40), "RUN144R3", theme])
        pgn.wait_for_timeout(300)
        out[(theme, "narrow40")] = pgn.evaluate(MEASURE, CAT)
        pgn.screenshot(path=os.path.join(SHOTS, f"{theme}_narrow40_collapsed.png"))
        if errs:
            print(f"FAIL: renderLedger raised on {theme}/narrow390: {errs}"); fail += 1
    b.close()


def bad(msg: str) -> None:
    global fail
    print("FAIL  " + msg); fail += 1


def good(msg: str) -> None:
    print("PASS  " + msg)


def note(msg: str) -> None:
    """A measurement that is reported, not asserted. Used ONLY where the thing measured is a
    pre-existing defect this run neither created nor was asked to fix -- it is printed loudly
    rather than dropped, and it is never used to soften a failure ruling 3 caused."""
    print("NOTE  " + msg)


# NARROW VIEWPORT: the label got longer, so it must not push anything off the row.
for theme in THEMES:
    for tag in ("age1", "age8", "age40", "current"):
        r = out[(theme, tag)]
        if r.get("error"):
            bad(f"{theme}/{tag}: {r['error']}")

print("\n================ WHAT THE BROWSER LAID OUT, DISCLOSURE CLOSED ================")
for theme in THEMES:
    for tag, _m, _n, _o in FIXTURES:
        r = out[(theme, tag)]
        print(f"--- {theme}/{tag}")
        print("    details_open      %s" % r.get("details_open"))
        print("    note_visible      %s   contrast %s" % (r.get("note_visible"),
                                                          r.get("note_contrast")))
        print("    summary_text      %r" % r.get("summary_text"))
        print("    chip_text         %r" % r.get("chip_text"))
        print("    theme_attr=%r  token=%r  page_bg=%r"
              % (r.get("theme_attr"), r.get("theme_token"), r.get("page_bg")))

# ---- 0. THE THEMES ARE DIFFERENT THEMES. Without this, "measured on three themes" is a claim
#         about an attribute rather than about a palette, and the first attempt at this file
#         failed exactly there: `data-theme` on the served <body> was overwritten with "plain"
#         and one palette was measured three times at the identical 5.90:1.
_tokens = {t: out[(t, "age8")].get("theme_token") for t in THEMES}
_attrs = {t: out[(t, "age8")].get("theme_attr") for t in THEMES}
print("\nresolved palette token per theme: %s" % _tokens)
if any(_attrs[t] != t for t in THEMES):
    bad(f"a theme did not stick: {_attrs}")
elif len({v for v in _tokens.values() if v}) < 2:
    bad(f"the themes resolve to one palette, so this is not a multi-theme measurement: "
        f"{_tokens}")
else:
    good(f"the themes resolve to different palettes -- {_tokens}")

# ---- 1. THE COLLAPSED STATE, ASSERTED. Without this nothing below means anything.
if any(out[k].get("details_open") for k in out):
    bad("a row was expanded; this is not a measurement of the collapsed view")
else:
    good("every row measured with <details> CLOSED, exactly as rendered on arrival")

# ---- 2. PROOF 4: the AGE is in the laid-out text of the collapsed head, on every theme.
for theme in THEMES:
    for tag, age in (("age1", 1), ("age8", 8), ("age40", 40)):
        r = out[(theme, tag)]
        words = f"{age} stored period{'' if age == 1 else 's'} back"
        txt = r.get("summary_text") or ""
        if words not in txt:
            bad(f"proof 4 [{theme}/{tag}]: the collapsed head does not state the age "
                f"({words!r} not in {txt!r})")
        else:
            good(f"proof 4 [{theme}/{tag}]: the collapsed head states {words!r} "
                 f"without clicking")
        c = r.get("note_contrast")
        if not r.get("note_visible"):
            bad(f"proof 4 [{theme}/{tag}]: the note carrying the age is not laid out")
        elif c is None:
            bad(f"proof 4 [{theme}/{tag}]: no contrast could be measured")
        elif c < 4.5 and theme in AA_THEMES:
            bad(f"proof 4 [{theme}/{tag}]: the age reads at {c}:1, AA needs 4.5:1")
        elif c < 4.5:
            note(f"proof 4 [{theme}/{tag}]: the age reads at {c:.2f}:1, BELOW AA -- "
                 f"a PRE-EXISTING theme-token gap, see the finding printed at the end")
        else:
            good(f"proof 4 [{theme}/{tag}]: the age reads at {c:.2f}:1 (AA needs 4.5:1)")
        if r.get("note_oldest_attr") != str(age):
            bad(f"proof 4 [{theme}/{tag}]: data-oldest-age is "
                f"{r.get('note_oldest_attr')!r}, expected {age}")

# ---- 3. The module chip carries the age too, and states the PERIOD as well as the distance.
#         It is INSIDE the closed disclosure, so it is asserted NOT laid out while closed --
#         which is precisely why check 2 above, on the summary, is the load-bearing one.
for theme in THEMES:
    r = out[(theme, "age8")]
    if r.get("chip_rendered"):
        bad(f"[{theme}] the chip renders text inside a CLOSED <details> "
            f"({r['chip_rendered']!r}); the fixture is not measuring the collapsed view")
    else:
        good(f"[{theme}] the chip renders NOTHING while collapsed -- which is exactly why the "
             f"age is also on the summary, where the browser does lay it out")
    if r.get("chip_text") != "Carried from P1, 8 stored periods back":
        bad(f"[{theme}] the module chip does not state period AND age: {r.get('chip_text')!r}")
    else:
        good(f"[{theme}] the module chip states both: {r['chip_text']!r}")
    if r.get("chip_age_attr") != "8":
        bad(f"[{theme}] the chip's data-from-age is {r.get('chip_age_attr')!r}, expected '8'")

# ---- 4. A CURRENT reading invents no age and no note.
for theme in THEMES:
    r = out[(theme, "current")]
    if r.get("note_text") is not None or r.get("chip_text") is not None:
        bad(f"[{theme}] a CURRENT reading rendered a carrying note or chip -- "
            f"{r.get('note_text')!r} / {r.get('chip_text')!r}")
    elif "stored period" in (r.get("summary_text") or ""):
        bad(f"[{theme}] a CURRENT reading's head mentions an age")
    else:
        good(f"[{theme}] a current reading shows no age and no note -- nothing is invented")

# ---- 5. NO THRESHOLD. The owner forbade a cap, a warning band and a colour change past some
#         age. Age 1, age 8 and age 40 must be styled IDENTICALLY.
for theme in THEMES:
    styles_note = {tag: out[(theme, tag)].get("note_style") for tag in ("age1", "age8", "age40")}
    styles_chip = {tag: out[(theme, tag)].get("chip_style") for tag in ("age1", "age8", "age40")}
    if len(set(styles_note.values())) != 1 or len(set(styles_chip.values())) != 1:
        bad(f"[{theme}] the styling CHANGES with age -- that is a threshold nobody authorised: "
            f"{styles_note} / {styles_chip}")
    else:
        good(f"[{theme}] age 1, 8 and 40 are styled identically -- no threshold, no cap, "
             f"no colour change")
    for tag in ("age1", "age8", "age40"):
        t = (out[(theme, tag)].get("summary_text") or "").lower()
        for banned in ("stale", "too old", "expired", "warning", "exceeds", "beyond"):
            if banned in t:
                bad(f"[{theme}/{tag}] the head passes judgment on the age ({banned!r})")

# ---- 5b. AT 390px, the width a phone gives it.
for theme in THEMES:
    r = out[(theme, "narrow40")]
    txt = r.get("summary_text") or ""
    c = r.get("note_contrast")
    if "40 stored periods back" not in txt:
        bad(f"[{theme}/390px] the age is not laid out at phone width: {txt!r}")
    elif not r.get("note_visible") or c is None:
        bad(f"[{theme}/390px] the age is not laid out or not measurable at phone width")
    elif c < 4.5 and theme in AA_THEMES:
        bad(f"[{theme}/390px] the age reads at {c}:1 at phone width")
    elif c < 4.5:
        note(f"[{theme}/390px] the age reads at {c:.2f}:1 -- the same pre-existing theme-token "
             f"gap, not a width problem")
    else:
        good(f"[{theme}/390px] the age is laid out at phone width and reads at {c:.2f}:1")

# ---- 6. The longer label did not break the layout.
for k, r in out.items():
    if r.get("row_overflows"):
        bad(f"{k}: the longer carried label overflows its container")
if not any(r.get("row_overflows") for r in out.values()):
    good("the longer label overflows nothing on any theme or age")

# ---- 7. THE PRE-EXISTING FINDING, STATED IN FULL rather than left in a softened check line.
_sub = [(t, out[(t, "age8")]) for t in THEMES
        if (out[(t, "age8")].get("note_contrast") or 99) < 4.5]
if _sub:
    print("\n================ FINDING, NOT CREATED BY RUN 144 ================")
    for t, r in _sub:
        print(f"  theme {t!r}: page background {r.get('page_bg')} (dark) but "
              f"--status-nodata-mod-text = {r.get('theme_token')} (the LIGHT default), "
              f"giving {r.get('note_contrast'):.2f}:1 against AA's 4.5:1.")
    print("  This is a PALETTE gap, not a ruling-3 gap: that theme does not redeclare the "
          "token, so every element painted with it is under AA on it -- the 'No data' chip, "
          "the abstention reason line and Run 143's carried note included, all of which "
          "predate this run. The age inherits the gap; it does not cause it. The one-line fix "
          "is to declare --status-nodata-mod-text in that theme's own block. NOT APPLIED: "
          "repainting a theme's palette is outside the three rulings.")

print("\nScreenshots: %s" % SHOTS)
print("\nALL BROWSER CHECKS PASSED" if not fail else "\n%d BROWSER CHECK(S) FAILED" % fail)
sys.exit(1 if fail else 0)
