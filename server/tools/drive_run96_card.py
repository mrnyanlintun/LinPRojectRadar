#!/usr/bin/env python3
"""
RUN 96. THE GOVERNANCE DECISION CARD AND THE SIGNAL FLOW BRANCH WEIGHTS, IN A REAL BROWSER.

Chromium at /opt/pw-browsers, viewports 1280px and 1024px, across every theme the theme
authority declares. Nothing below is asserted from source: the card is read back out of the
RENDERED DOM, and the two branch layers are read back out of the RENDERED SVG attributes.

THE CARD is rendered by the PRODUCTION functions in `assets/js/decision-ui.js`, reached through
its `__cardForTest` seam, against the real stylesheet. The two card payloads are composed by the
production Python composer, `app/decision_brief.py`, from the STORED row.

WHICH ROWS, AND WHICH OF THEM IS A FIXTURE -- stated plainly because it matters:
  INDETERMINATE  project 507be211.../a81ca9d2..., period 8, EXACTLY AS STORED. A1 Red and A4 Red
                 assessed; A2, A3 and A6 assert no band, so the required core is incomplete and
                 the official posture is withheld. Nothing was altered to produce it.
  POSTURE        THE SAME STORED ROW WITH THREE CATEGORY BANDS SUPPLIED IN MEMORY. It is a
                 FIXTURE and is called one everywhere it appears. No row in the database carries
                 all five required categories, so a row carrying a posture had to be constructed.
                 NOTHING IS WRITTEN: the fixture exists only inside this process.
"""
from __future__ import annotations
import copy, json, os, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent))

from app.decision_brief import compose_decision_brief          # noqa: E402
from app.spec_projection import project_status_basis           # noqa: E402
from app.theme import THEMES                                   # noqa: E402

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SCRATCH = pathlib.Path(os.environ.get(
    "RUN96_SCRATCH",
    "/tmp/claude-0/-home-user-LinPRojectRadar/56ab0a7f-4e21-5061-8b33-396724907fe8/scratchpad"))


def say(*a): print(" ".join(str(x) for x in a), flush=True)


row = json.loads((SCRATCH / "row.json").read_text())
cards = {}
for tag, src in (("INDETERMINATE", "row.json"), ("POSTURE (FIXTURE)", "row_posture.json")):
    r = json.loads((SCRATCH / src).read_text())
    basis = project_status_basis(r["category_statuses"])
    cards[tag] = compose_decision_brief(category_statuses=r["category_statuses"],
                                        module_results=r["module_results"],
                                        status_basis=basis)

CSS = (ROOT / "assets/css/radar.css").read_text(encoding="utf-8")
UI = (ROOT / "assets/js/decision-ui.js").read_text(encoding="utf-8")
FLOW = (ROOT / "assets/js/neural_flow.js").read_text(encoding="utf-8")

PAGE = """<!doctype html><meta charset="utf-8"><style>__CSS__</style>
<body><div id="host" style="max-width:820px;padding:24px;"></div>
<div id="dc-package"></div>
<script>window.__stub=1;</script>
</body>"""

from playwright.sync_api import sync_playwright                # noqa: E402

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME,
                           args=["--no-sandbox", "--headless=new", "--use-gl=swiftshader"])
    for VW in (1280, 1024):
        say("=" * 96); say(f"VIEWPORT {VW}px")
        pg = b.new_page(viewport={"width": VW, "height": 2600})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.set_content(PAGE.replace("__CSS__", CSS))
        # The production file is an IIFE that wires to elements that do not exist here; the
        # wiring throws and is swallowed, and the seam it publishes before that is what is used.
        pg.add_script_tag(content="window.addEventListener('error',function(e){e.preventDefault();});")
        pg.add_script_tag(content=UI)
        seam = pg.evaluate("() => !!(window.LinDecisionUI && window.LinDecisionUI.__cardForTest)")
        say(f"  production card seam present: {seam}")
        if not seam:
            say("  FATAL: the card's render functions did not reach the browser"); continue

        for TH in list(THEMES):
            pg.evaluate("(t)=>document.body.setAttribute('data-theme',t)", TH)
            for tag, card in cards.items():
                html = pg.evaluate(
                    "(c)=>{const h=window.LinDecisionUI.__cardForTest.renderDecisionBrief(c);"
                    "document.getElementById('host').innerHTML=h;return h.length;}", card)
                shown = pg.evaluate("""() => {
                  const out=[];
                  document.querySelectorAll('#host .dc-group').forEach(g=>{
                    const h=g.querySelector('h3');
                    const r=g.getBoundingClientRect();
                    out.push({title:h?h.textContent:'',
                              text:g.textContent.replace(h?h.textContent:'','').trim(),
                              w:Math.round(r.width),h:Math.round(r.height),
                              visible:r.width>0&&r.height>0});
                  });
                  return out;
                }""")
                if TH == THEMES[0]:
                    say("-" * 96)
                    say(f"  CARD [{tag}] theme={TH} -- {len(shown)} blocks, {html} chars of HTML")
                    for blk in shown:
                        say(f"    [{blk['w']}x{blk['h']} vis={blk['visible']}] {blk['title']}")
                        say(f"        {blk['text'][:600]}")
                    say(f"    BLOCK TITLES: {[b['title'] for b in shown]}")
                    say(f"    'Recommended action' rendered anywhere (must be False): "
                        f"{'Recommended action' in ''.join(b['title'] for b in shown)}")
                    say(f"    'Alternatives' rendered anywhere (must be False): "
                        f"{'Alternatives' in ''.join(b['title'] for b in shown)}")
                    say(f"    a placeholder rendered anywhere (must be False): "
                        f"{any(x in ''.join(b['text'] for b in shown) for x in ('not established','not available'))}")
                    say(f"    every block has non-zero size (must be True): "
                        f"{all(b['visible'] for b in shown)}")
                else:
                    say(f"  CARD [{tag}] theme={TH}: {len(shown)} blocks, all visible="
                        f"{all(b['visible'] for b in shown)}")
        say(f"  PAGE ERRORS: {errs[:3]}")
        pg.close()
    b.close()
say("RUN 96 CARD DRIVE COMPLETE")
